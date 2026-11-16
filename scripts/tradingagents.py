#!/usr/bin/env python3
"""dsh-tradingagents v0 — 多智能体投研议院（TradingAgents-style，DSH 原生）编排器

结构致敬 TradingAgents（Tauric Research）与 ai-hedge-fund（virattt），
差异点：**可审计**——每个主张带证据标签，裁决必须点名动因，输出 IC-MEMO。

管线（6 次 DeepSeek 调用/场，temperature=0）：
  analyst → bull → bear(见多方) → bull 回应(见空方) → risk(只立护栏) → PM(裁决)

用法：
  python3 scripts/tradingagents.py --ticker DEMO                 # 离线合成数据冒烟
  python3 scripts/tradingagents.py --data my.json --ticker XXX   # 自备数据卡
"""
import argparse, json, os, subprocess, sys, time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMOS = os.path.join(KIT, "memos")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="DEMO")
    ap.add_argument("--data", default=os.path.join(KIT, "data", "demo", "DEMO.json"))
    ap.add_argument("--save", action="store_true", help="把会议纪要存 memos/")
    args = ap.parse_args()
    card = json.load(open(args.data))
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
    risk = llm("你是风控官：不决策，只立护栏——仓位上限、失效触发器、必须重审的事件，每条 [G#]。",
               f"事实：\n{a}\n\n辩论摘要：\n{bull}\n{bear}")
    pm = llm("你是组合经理：输出 JSON {{\"decision\":\"BUY|HOLD|SELL|PASS\",\"confidence\":0-100,"
             "\"size_hint\":\"..\",\"invalidation\":[..],\"reasoning\":\"点名哪些 [B#]/[R#]/[G#] 说服或约束了你\"}}。"
             "证据不足以裁决时必须 PASS——弃权是合法且体面的输出。",
             f"事实：\n{a}\n\n多方：\n{bull}\n空方：\n{bear}\n多方回应：\n{reb}\n风控护栏：\n{risk}",
             json_out=True)

    try:
        verdict = json.loads(pm)
    except json.JSONDecodeError:
        import re
        verdict = json.loads(re.sub(r"^```(json)?|```$", "", pm.strip(), flags=re.M).strip())

    memo = f"""# IC-MEMO · {args.ticker} · {card.get('as_of', '?')}

```yaml
ticker: {args.ticker}
as_of: {card.get('as_of', '?')}
committee: tradingagents/v0
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

## 3 · 风控护栏
{risk}

## 4 · 组合经理裁决
- 裁决 **{verdict.get('decision')}**（置信度 {verdict.get('confidence')}）
- {verdict.get('reasoning')}

---
*耗时 {time.time()-t0:.0f}s · deepseek-chat · temperature=0 · 数据={os.path.basename(args.data)}*
"""
    print(memo)
    if args.save:
        os.makedirs(MEMOS, exist_ok=True)
        path = os.path.join(MEMOS, f"{args.ticker}-{card.get('as_of', 'x')}.md")
        open(path, "w").write(memo)
        print(f"→ {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
