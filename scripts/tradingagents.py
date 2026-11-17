#!/usr/bin/env python3
"""dsh-tradingagents v1 — 多智能体投研议院（TradingAgents-style，DSH 原生）编排器

结构致敬 TradingAgents（Tauric Research）与 ai-hedge-fund（virattt），
差异点：**可审计**——每个主张带证据标签，裁决必须点名动因，输出 IC-MEMO。

管线（6 次基础调用/场，temperature=0；--guests 每位客座 +1 次）：
  analyst → bull → bear(见多方) → bull 回应(见空方)
          → [客座席位：大师人格用各自方法论评辩] → risk(只立护栏) → PM(裁决)

客座人格包跨接自姊妹仓 dsh-ai-hedge-fund（PERSONAS 定义同步，评辩而非盲估——
与那边"互不可见独立估值"的差异点：这里人格看完整多空辩论后表态）。

用法：
  python3 scripts/tradingagents.py --ticker DEMO                 # 离线合成数据冒烟
  python3 scripts/tradingagents.py --data my.json --ticker XXX   # 自备数据卡
  python3 scripts/tradingagents.py --ticker DEMO --guests all --save   # 全客座开庭（10 次调用）
"""
import argparse, json, os, re, subprocess, sys, time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMOS = os.path.join(KIT, "memos")

# 客座人格包：定义同步自姊妹仓 dsh-ai-hedge-fund scripts/hedge_fund.py 的 PERSONAS
GUEST_PERSONAS = {
    "warren_buffett": {
        "zh": "沃伦·巴菲特",
        "discipline": "只投能力圈内看得懂的业务；找有持久护城河（定价权/转换成本/网络效应）的好生意；用 Owner Earnings 视角估内在价值；只在价格显著低于价值（安全边际）时出手；宁可错过不可做错。",
        "redflag": "对看不懂的商业模式、高换手行业、需要持续巨额资本开支的生意天然警惕。",
    },
    "charlie_munger": {
        "zh": "查理·芒格",
        "discipline": "反过来想，总是反过来想：先列出这笔投资会如何死掉（竞争/技术/杠杆/治理），全部排除后才谈收益；用多元思维模型交叉检验；以合理价格买卓越公司，而非以便宜价格买平庸公司；避免愚蠢比寻找聪明更重要。",
        "redflag": "对会计质量差、管理层言行不一、商业模式复杂到无法证伪的公司直接否决。",
    },
    "peter_lynch": {
        "zh": "彼得·林奇",
        "discipline": "GARP（以合理价格成长）：PEG 视角，成长性与估值匹配；优先能被普通人理解的业务；关注被机构忽视的角落；用基本面驱动（营收/利润增速的可持续性），快轮换慢积累。",
        "redflag": "对故事宏大但没有盈利路径验证的公司警惕；对增速放缓但估值仍按高增长给的警觉。",
    },
    "cathie_wood": {
        "zh": "凯瑟琳·伍德",
        "discipline": "聚焦破坏性创新（AI/机器人/基因/能源存储/区块链）的指数级成长赛道；以 5 年视野看 TAM 扩张与单位经济改善；容忍短期波动与不盈利，看重研发投入强度与飞轮证据。",
        "redflag": "对增长停滞、创新投入收缩、赛道被证伪的标的果断放弃；对传统低增长价值股不感兴趣。",
    },
}


def llm(role_prompt, user_payload, json_out=False):
    key = subprocess.run(["bash", "-c", 'grep -m1 "^export DEEPSEEK_API_KEY=" ~/.bashrc | cut -d= -f2'],
                         capture_output=True, text=True).stdout.strip().strip('"')
    sysmsg = f"你在一场投资委员会中扮演固定角色。纪律：只使用给定数据，禁止编造数字；每个主张以 [B#]/[R#]/[A#]/[G#] 标签开头并引用来源标签。{role_prompt}"
    body = {"model": "deepseek-chat", "temperature": 0,
            "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": user_payload}]}
    if json_out:
        body["response_format"] = {"type": "json_object"}
    r = subprocess.run(["curl", "-s", "-m", "180", "https://api.deepseek.com/chat/completions",
                        "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
                        "-d", json.dumps(body)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)["choices"][0]["message"]["content"]
    except Exception:
        raise SystemExit(f"LLM 调用失败: {r.stdout[:200]}")


def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="DEMO")
    ap.add_argument("--data", default=os.path.join(KIT, "data", "demo", "DEMO.json"))
    ap.add_argument("--guests", default="",
                    help=f"客座人格（逗号分隔或 all）：{','.join(GUEST_PERSONAS)}；缺省无客座")
    ap.add_argument("--save", action="store_true", help="把会议纪要存 memos/")
    args = ap.parse_args()
    card = json.load(open(args.data))
    guests = (list(GUEST_PERSONAS) if args.guests == "all"
              else [g.strip() for g in args.guests.split(",") if g.strip() in GUEST_PERSONAS])
    t0 = time.time()
    data = json.dumps(card, ensure_ascii=False, indent=1)

    a = llm("你是分析师：把数据卡转写为带 [A#] 标签的事实清单，一条不漏，不添加。",
            f"数据卡：\n{data}")
    bull = llm("你是多方研究员：给出最强看多论证，每条 [B#] 必须引用 [A#]。",
               f"事实：\n{a}")
    bear = llm("你是空方研究员：先概括多方论点再逐条反驳或给出独立看空论据，每条 [R#]。",
               f"事实：\n{a}\n\n多方论点：\n{bull}")
    reb = llm("你是多方研究员：只回应空方最强攻击，不超过 3 条 [B#]。",
              f"你的原论点：\n{bull}\n\n空方攻击：\n{bear}")

    guest_memos = {}
    debate_ctx = f"事实：\n{a}\n\n多方：\n{bull}\n空方：\n{bear}\n多方回应：\n{reb}"
    for pid in guests:
        p = GUEST_PERSONAS[pid]
        g = parse_json(llm(
            f"你是客座委员{p['zh']}，旁听了整场多空辩论。方法论：{p['discipline']} 天然警惕：{p['redflag']} "
            f"用你的方法论评辩：哪方论点在你的框架下站得住、哪方在偷懒，你还想向双方各提一个问题。"
            f"输出 JSON {{\"stance\":\"BUY|HOLD|SELL|PASS\",\"conviction\":0-100,"
            f"\"take\":\"不超过4条 [P#]，每条引用 [A#]/[B#]/[R#]；末条以'若我是PM'开头给处置\"}}。",
            debate_ctx, json_out=True))
        if isinstance(g.get("take"), list):  # 模型偶返回数组——并成段落
            g["take"] = "\n\n".join(str(x) for x in g["take"])
        guest_memos[pid] = g
    guest_digest = "\n".join(
        f"{GUEST_PERSONAS[k]['zh']}: {v['stance']}@{v['conviction']}" for k, v in guest_memos.items())

    risk = llm("你是风控官：不决策，只立护栏——仓位上限、失效触发器、必须重审的事件，每条 [G#]。",
               f"事实：\n{a}\n\n辩论摘要：\n{bull}\n{bear}" +
               (f"\n\n客座观点摘要：\n{guest_digest}" if guest_digest else ""))
    pm = llm("你是组合经理：输出 JSON {{\"decision\":\"BUY|HOLD|SELL|PASS\",\"confidence\":0-100,"
             "\"size_hint\":\"..\",\"invalidation\":[..],\"reasoning\":\"点名哪些 [B#]/[R#]/[G#]/客座说服或约束了你\"}}。"
             "证据不足以裁决时必须 PASS——弃权是合法且体面的输出。",
             f"事实：\n{a}\n\n多方：\n{bull}\n空方：\n{bear}\n多方回应：\n{reb}"
             + (f"\n\n客座评辩（可采纳可反驳，须点名）：\n{guest_digest}" if guest_digest else "")
             + f"\n风控护栏：\n{risk}",
             json_out=True)

    verdict = parse_json(pm)

    guest_section = ""
    if guest_memos:
        table = "\n".join(
            f"| {GUEST_PERSONAS[k]['zh']} | {v['stance']} | {v['conviction']} |" for k, v in guest_memos.items())
        takes = "\n\n".join(
            f"### {GUEST_PERSONAS[k]['zh']}\n{v['take']}" for k, v in guest_memos.items())
        guest_section = f"""## 3 · 客座评辩（人格包 dsh-ai-hedge-fund）
| 客座 | 立场 | 信念 |
|---|---|---|
{table}

{takes}

"""

    memo = f"""# IC-MEMO · {args.ticker} · {card.get('as_of', '?')}

```yaml
ticker: {args.ticker}
as_of: {card.get('as_of', '?')}
committee: tradingagents/v1{'（guests: ' + ', '.join(GUEST_PERSONAS[k]['zh'] for k in guest_memos) + '）' if guest_memos else ''}
decision: {verdict.get('decision')}
confidence: {verdict.get('confidence')}
size_hint: {verdict.get('size_hint')}
invalidation: {json.dumps(verdict.get('invalidation', []), ensure_ascii=False)}
```

## 1 · 分析师纪要
{a}

## 2 · 多空辩论
### 多方
{bull}

### 空方
{bear}

### 多方回应
{reb}

{guest_section}## {4 if guest_memos else 3} · 风控护栏
{risk}

## {5 if guest_memos else 4} · 组合经理裁决
- 裁决 **{verdict.get('decision')}**（置信度 {verdict.get('confidence')}）
- {verdict.get('reasoning')}

---
*耗时 {time.time()-t0:.0f}s · {len(guests) + 6} 次调用 · deepseek-chat · temperature=0 · 数据={os.path.basename(args.data)} · 非投资建议*
"""
    print(memo)
    if args.save:
        os.makedirs(MEMOS, exist_ok=True)
        suffix = "-guests" if guest_memos else ""
        path = os.path.join(MEMOS, f"{args.ticker}-{card.get('as_of', 'x')}{suffix}.md")
        open(path, "w").write(memo)
        print(f"→ {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
