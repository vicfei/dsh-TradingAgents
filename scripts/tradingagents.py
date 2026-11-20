#!/usr/bin/env python3
"""dsh-tradingagents v1 — multi-agent investment committee (TradingAgents-style, DSH-native)

Structure inspired by TradingAgents (Tauric Research) and ai-hedge-fund (virattt);
the differentiator: **auditable** — every claim carries an evidence tag, every verdict
names what moved it, output is an IC-MEMO.

Pipeline (6 base calls per session, temperature=0; each guest seat adds one call):
  analyst → bull → bear (sees bull) → bull rebuttal (sees bear)
          → [guest seats: master personas critique the debate] → risk (guardrails only) → PM (verdict)

Guest persona pack cross-linked from the sister repo dsh-ai-hedge-fund (PERSONAS synced;
they critique the full debate rather than blind-estimate — the divergence from that repo).

Usage:
  python3 scripts/tradingagents.py --ticker DEMO                       # offline synthetic smoke
  python3 scripts/tradingagents.py --data my.json --ticker XXX         # bring your own data card
  python3 scripts/tradingagents.py --ticker DEMO --guests all --save   # full guest seats (10 calls)
  ... --lang zh                                                         # Chinese output (English is default)
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time

# Verdict vocabulary (issue #3): five tradeable tiers + PASS (insufficient evidence,
# first-class) + REVIEW (the PM's output could not be read — NOT a verdict, rerun
# required; never recorded as PASS or a tier).
RATINGS = ("BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL")
VERDICTS = RATINGS + ("PASS", "REVIEW")

LANG = os.environ.get("TRADINGAGENTS_LANG") or "en"
def tt(en, zh):
    return en if LANG == "en" else zh

# Cost guard (issue #7): every successful call is counted with its tokens; the
# committee dies cleanly at --max-calls rather than silently overspending.
COST = {"calls": 0, "in": 0, "out": 0}
MAX_CALLS = None


def take_usage(body):
    """Extract (prompt_tokens, completion_tokens) from a provider response, 0-safe."""
    u = (body or {}).get("usage") or {}
    return int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# npm CLI form lands memos in the caller's cwd via TRADINGAGENTS_MEMOS (repo default unchanged)
MEMOS = os.environ.get("TRADINGAGENTS_MEMOS") or os.path.join(KIT, "memos")

# Guest persona pack: definitions synced from the sister repo dsh-ai-hedge-fund
# (scripts/hedge_fund.py PERSONAS) — en/zh discipline pairs.
GUEST_PERSONAS = {
    "warren_buffett": {
        "zh": "沃伦·巴菲特",
        "en": "Warren Buffett",
        "discipline": {
            "en": "Stay inside your circle of competence; look for durable moats (pricing power, switching costs, network effects); value the business on owner earnings; act only when price is well below value (margin of safety); missing out beats being wrong.",
            "zh": "只投能力圈内看得懂的业务；找有持久护城河（定价权/转换成本/网络效应）的好生意；用 Owner Earnings 视角估内在价值；只在价格显著低于价值（安全边际）时出手；宁可错过不可做错。",
        },
        "redflag": {
            "en": "Naturally wary of business models you cannot understand, high-churn industries, and businesses that need perpetual heavy capex.",
            "zh": "对看不懂的商业模式、高换手行业、需要持续巨额资本开支的生意天然警惕。",
        },
    },
    "charlie_munger": {
        "zh": "查理·芒格",
        "en": "Charlie Munger",
        "discipline": {
            "en": "Invert, always invert: first list how this investment dies (competition, technology, leverage, governance) and only after all are excluded talk about returns; cross-check with multiple mental models; buy wonderful companies at fair prices, not fair companies at wonderful prices; avoiding stupidity matters more than finding cleverness.",
            "zh": "反过来想，总是反过来想：先列出这笔投资会如何死掉（竞争/技术/杠杆/治理），全部排除后才谈收益；用多元思维模型交叉检验；以合理价格买卓越公司，而非以便宜价格买平庸公司；避免愚蠢比寻找聪明更重要。",
        },
        "redflag": {
            "en": "Veto outright on poor accounting quality, management that says one thing and does another, and business models too complex to falsify.",
            "zh": "对会计质量差、管理层言行不一、商业模式复杂到无法证伪的公司直接否决。",
        },
    },
    "peter_lynch": {
        "zh": "彼得·林奇",
        "en": "Peter Lynch",
        "discipline": {
            "en": "GARP (growth at a reasonable price): a PEG lens, growth matched against valuation; prefer businesses an ordinary person can understand; look in corners institutions ignore; fundamentals-driven (sustainability of revenue and earnings growth); rotate the fast, accumulate the slow.",
            "zh": "GARP（以合理价格成长）：PEG 视角，成长性与估值匹配；优先能被普通人理解的业务；关注被机构忽视的角落；用基本面驱动（营收/利润增速的可持续性），快轮换慢积累。",
        },
        "redflag": {
            "en": "Wary of grand stories with no validated profit path; wary of slowing growth still priced at high-growth multiples.",
            "zh": "对故事宏大但没有盈利路径验证的公司警惕；对增速放缓但估值仍按高增长给的警觉。",
        },
    },
    "cathie_wood": {
        "zh": "凯瑟琳·伍德",
        "en": "Cathie Wood",
        "discipline": {
            "en": "Focus on disruptive innovation (AI, robotics, genomics, energy storage, blockchain) with exponential growth runways; take a 5-year view of TAM expansion and improving unit economics; tolerate near-term volatility and unprofitability; weigh R&D intensity and flywheel evidence.",
            "zh": "聚焦破坏性创新（AI/机器人/基因/能源存储/区块链）的指数级成长赛道；以 5 年视野看 TAM 扩张与单位经济改善；容忍短期波动与不盈利，看重研发投入强度与飞轮证据。",
        },
        "redflag": {
            "en": "Walk away decisively when growth stalls, innovation spending shrinks, or the thesis is falsified; uninterested in traditional low-growth value names.",
            "zh": "对增长停滞、创新投入收缩、赛道被证伪的标的果断放弃；对传统低增长价值股不感兴趣。",
        },
    },
}

T = {
    "sys": {
        "en": "You play a fixed role in an investment committee. Discipline: use only the given data, never invent numbers; begin every claim with a [B#]/[R#]/[A#]/[G#] tag and cite source tags. Write your entire output in English.",
        "zh": "你在一场投资委员会中扮演固定角色。纪律：只使用给定数据，禁止编造数字；每个主张以 [B#]/[R#]/[A#]/[G#] 标签开头并引用来源标签。全部输出使用中文。",
    },
    "analyst": {
        "en": "You are the analyst: transcribe the data card into a fact list tagged [A#], one entry per fact, nothing added.",
        "zh": "你是分析师：把数据卡转写为带 [A#] 标签的事实清单，一条不漏，不添加。",
    },
    "bull": {
        "en": "You are the bull researcher: build the strongest bullish case; every [B#] must cite [A#].",
        "zh": "你是多方研究员：给出最强看多论证，每条 [B#] 必须引用 [A#]。",
    },
    "bear": {
        "en": "You are the bear researcher: first summarize the bull's points, then rebut each or give independent bear arguments, every item [R#].",
        "zh": "你是空方研究员：先概括多方论点再逐条反驳或给出独立看空论据，每条 [R#]。",
    },
    "rebuttal": {
        "en": "You are the bull researcher: answer only the bear's strongest attacks, at most 3 items, tagged [B#].",
        "zh": "你是多方研究员：只回应空方最强攻击，不超过 3 条 [B#]。",
    },
    "bull_respond": {
        "en": "You are the bull researcher: respond to the bear's latest attack and defend or refine your case, tagged [B#].",
        "zh": "你是多方研究员：回应空方最新攻击，捍卫或修正你的论证，每条 [B#]。",
    },
    "risk": {
        "en": "You are the risk officer: you do not decide; you only set guardrails — position caps, invalidation triggers, events that force a re-review, each tagged [G#].",
        "zh": "你是风控官：不决策，只立护栏——仓位上限、失效触发器、必须重审的事件，每条 [G#]。",
    },
    "risk_guests": {"en": "\n\nGuest-seat summary:\n", "zh": "\n\n客座观点摘要：\n"},
    "pm": {
        "en": 'You are the portfolio manager: output JSON {"decision":"BUY|OVERWEIGHT|HOLD|UNDERWEIGHT|SELL|PASS","confidence":0-100,"size_hint":"..","invalidation":[..],"reasoning":"name which [B#]/[R#]/[G#]/[T#]/guest seats persuaded or constrained you"}. The five tiers: BUY = strong conviction to enter or add; OVERWEIGHT = favorable, gradually increase exposure; HOLD = maintain, no action; UNDERWEIGHT = reduce exposure, take partial profits; SELL = exit or avoid. Conflict between the sides is not itself a reason for HOLD — weigh the cases and commit to the stronger one, sized by how decisively it wins. When the evidence is insufficient to rule, you must PASS — abstaining is a legitimate and honorable output; do not manufacture a direction to look decisive.',
        "zh": '你是组合经理：输出 JSON {"decision":"BUY|OVERWEIGHT|HOLD|UNDERWEIGHT|SELL|PASS","confidence":0-100,"size_hint":"..","invalidation":[..],"reasoning":"点名哪些 [B#]/[R#]/[G#]/[T#]/客座说服或约束了你"}。五档：BUY=强确信建仓或加仓；OVERWEIGHT=偏多逐步加仓；HOLD=维持不动；UNDERWEIGHT=减仓部分止盈；SELL=清仓或回避。多空冲突本身不是 HOLD 的理由——权衡后站更强一方，按胜出幅度定力度。证据不足以裁决时必须 PASS——弃权是合法且体面的输出，不要为显得果断硬造方向。',
    },
    "pm_guests": {
        "en": "\n\nGuest critiques (adopt or rebut them, but name them):\n",
        "zh": "\n\n客座评辩（可采纳可反驳，须点名）：\n",
    },
    "guest": {
        "en": 'You are guest committee member {name}, and you have watched the whole bull-bear debate. Methodology: {discipline} Naturally wary of: {redflag} Judge the debate through your methodology: which side\'s arguments hold up in your framework, which side is being lazy, and one question you would put to each side. Output JSON {{"stance":"BUY|OVERWEIGHT|HOLD|UNDERWEIGHT|SELL|PASS","conviction":0-100,"take":"at most 4 items tagged [P#], each citing [A#]/[B#]/[R#]; the last must start with \'If I were the PM\' and give your action"}}.',
        "zh": '你是客座委员{name}，旁听了整场多空辩论。方法论：{discipline} 天然警惕：{redflag} 用你的方法论评辩：哪方论点在你的框架下站得住、哪方在偷懒，你还想向双方各提一个问题。输出 JSON {{"stance":"BUY|OVERWEIGHT|HOLD|UNDERWEIGHT|SELL|PASS","conviction":0-100,"take":"不超过4条 [P#]，每条引用 [A#]/[B#]/[R#]；末条以\'若我是PM\'开头给处置"}}。',
    },
    "facts": {"en": "Facts:\n", "zh": "事实：\n"},
    "bull_case": {"en": "\n\nBull case:\n", "zh": "\n\n多方论点：\n"},
    "bear_case": {"en": "\n\nBear case:\n", "zh": "\n\n空方攻击：\n"},
    "your_case": {"en": "Your original case:\n", "zh": "你的原论点：\n"},
    "debate_digest": {"en": "\n\nDebate digest:\n", "zh": "\n\n辩论摘要：\n"},
    "bull_rebuttal": {"en": "\n\nBull rebuttal:\n", "zh": "\n\n多方回应：\n"},
    "guardrails": {"en": "\n\nRisk guardrails:\n", "zh": "\n\n风控护栏：\n"},
    "data_card": {"en": "Data card:\n", "zh": "数据卡：\n"},
    "h1_analyst": {"en": "## 1 · Analyst notes", "zh": "## 1 · 分析师纪要"},
    "h1_debate": {"en": "## 2 · Bull-bear debate", "zh": "## 2 · 多空辩论"},
    "h_bull": {"en": "### Bull", "zh": "### 多方"},
    "h_bear": {"en": "### Bear", "zh": "### 空方"},
    "h_rebuttal": {"en": "### Bull rebuttal", "zh": "### 多方回应"},
    "h_guests": {"en": "## 3 · Guest critiques (persona pack dsh-ai-hedge-fund)", "zh": "## 3 · 客座评辩（人格包 dsh-ai-hedge-fund）"},
    "th_guest": {"en": "| Guest | Stance | Conviction |", "zh": "| 客座 | 立场 | 信念 |"},
    "h_risk": {"en": "## {n} · Risk guardrails", "zh": "## {n} · 风控护栏"},
    "h_pm": {"en": "## {n} · Portfolio manager verdict", "zh": "## {n} · 组合经理裁决"},
    "verdict_line": {"en": "- Verdict **{d}** (confidence {c})", "zh": "- 裁决 **{d}**（置信度 {c}）"},
    "review_note": {
        "en": "- **REVIEW**: the PM's output could not be parsed into a decision. This is not a verdict, is not tradeable, and must not be recorded as PASS or a tier — rerun the session (possibly with fresh data) instead.",
        "zh": "- **REVIEW**：组合经理输出无法解析为裁决。这不是判决、不可交易、不得记为 PASS 或任一档位——请重跑本场（必要时换新数据）。",
    },
    "guests_label": {"en": "guests", "zh": "guests"},
    "track_record": {
        "en": "\n\nTrack record — prior settled decisions and lessons (cite them as [T#] where they move you):\n",
        "zh": "\n\n战绩台账——既往已结算判决与教训（若影响你须引用为 [T#]）：\n",
    },
    "footer": {"en": "*{t}s · {n} calls · {ti:,} in / {to:,} out tokens · deepseek-chat · temperature=0 · data={f} · not investment advice*\n★ github.com/vicfei/dsh-TradingAgents",
               "zh": "*耗时 {t}s · {n} 次调用 · {ti:,} 入 / {to:,} 出 token · deepseek-chat · temperature=0 · 数据={f} · 非投资建议*\n★ github.com/vicfei/dsh-TradingAgents"},
}


def llm(role_prompt, user_payload, json_out=False):
    if MAX_CALLS is not None and COST["calls"] >= MAX_CALLS:
        raise SystemExit(f"cost guard: {MAX_CALLS} LLM calls reached (--max-calls); aborting before call #{COST['calls'] + 1}")
    key = subprocess.run(["bash", "-c", 'grep -m1 "^export DEEPSEEK_API_KEY=" ~/.bashrc | cut -d= -f2'],
                         capture_output=True, text=True).stdout.strip().strip('"')
    sysmsg = f"{T['sys'][LANG]}{role_prompt}"
    body = {"model": "deepseek-chat", "temperature": 0,
            "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": user_payload}]}
    if json_out:
        body["response_format"] = {"type": "json_object"}
    r = subprocess.run(["curl", "-s", "-m", "180", "https://api.deepseek.com/chat/completions",
                        "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
                        "-d", json.dumps(body)], capture_output=True, text=True)
    try:
        parsed = json.loads(r.stdout)
        content = parsed["choices"][0]["message"]["content"]
        pin, pout = take_usage(parsed)
        COST["calls"] += 1
        COST["in"] += pin
        COST["out"] += pout
        return content
    except Exception:
        raise SystemExit(f"LLM call failed: {r.stdout[:200]}")


def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip())


def load_portfolio(path):
    """The caller's book, three states strictly distinct (issue #5).

    Provided with a positions list (possibly empty = flat book) vs NOT provided at
    all (the agents know nothing about holdings) — treating "not provided" as flat
    would invent a fact about the caller's account.
    """
    data = json.load(open(path, encoding="utf-8"))
    positions = data.get("positions")
    if not isinstance(positions, list):
        raise SystemExit(tt("--portfolio JSON must carry a positions list "
                            "(empty list = flat book; omit the flag entirely when holdings "
                            "should stay unknown)",
                            "--portfolio 的 JSON 必须含 positions 列表"
                            "（空列表=空仓；不想让议院知道持仓就不要传该参数）"))
    for p in positions:
        q = p.get("quantity")
        if not isinstance(q, (int, float)) or q != q or q in (float("inf"), float("-inf")):
            raise SystemExit(tt(f"non-finite quantity for {p.get('ticker')!r}",
                                f"{p.get('ticker')!r} 的 quantity 非有限数"))
    return {"cash": data.get("cash"), "currency": data.get("currency"), "positions": positions}


def render_portfolio(book, ticker):
    """Holdings block for the PM and risk officer; '' when nothing was provided."""
    if book is None:
        return ""
    ours, others = [], []
    norm = lambda s: str(s).strip().upper().replace(".", "")
    want = norm(ticker)
    for p in book["positions"]:
        (ours if norm(p.get("ticker", "")) == want else others).append(p)
    L = []
    for p in ours:
        px = f", average price {p['average_price']:,.2f}" if p.get("average_price") is not None else ""
        L.append(tt(f"- Current position in {ticker}: {p['quantity']:,.4g} units{px}",
                    f"- 当前持有 {ticker}：{p['quantity']:,.4g} 单位{px}"))
    if not ours:
        L.append(tt(f"- No current position in {ticker}", f"- 当前未持有 {ticker}"))
    if book.get("cash") is not None:
        cur = f" {book['currency']}" if book.get("currency") else ""
        L.append(tt(f"- Cash available: {book['cash']:,.2f}{cur}", f"- 可用现金：{book['cash']:,.2f}{cur}"))
    if others:
        L.append(tt("- Other positions: " + ", ".join(f"{p['ticker']} {p['quantity']:,.4g}" for p in others),
                    "- 其他持仓：" + ", ".join(f"{p['ticker']} {p['quantity']:,.4g}" for p in others)))
    return tt("Portfolio at the analysis date (size_hint must relate to the existing "
              "position — adding vs opening are different acts):\n", 
              "分析日持仓（size_hint 须对照现有仓位——加仓与建仓是两回事）：\n") + "\n".join(L)


def resolve_verdict(pm_text, lang="en"):
    """Parse the PM's output into a verdict (issue #3 dual exit).

    A readable decision (any of the five tiers, PASS) is normalized to upper case.
    Anything unreadable — malformed JSON, a missing decision field, or a decision
    outside the vocabulary — becomes the REVIEW sentinel: not a verdict, not
    tradeable, never silently degraded to PASS or a tier.
    """
    review = {"decision": "REVIEW", "confidence": None, "size_hint": None,
              "invalidation": [], "_unparsed_head": pm_text[:200]}
    try:
        v = parse_json(pm_text)
    except Exception:
        return review
    if not isinstance(v, dict):
        return review
    d = str(v.get("decision", "")).strip().upper()
    if d not in VERDICTS or d == "REVIEW":
        return review
    v["decision"] = d
    return v


def main():
    global LANG, MAX_CALLS
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="DEMO")
    ap.add_argument("--data", default=os.path.join(KIT, "data", "demo", "DEMO.json"))
    ap.add_argument("--guests", default="",
                    help=f"guest personas (comma-separated or all): {','.join(GUEST_PERSONAS)}; default none")
    ap.add_argument("--lang", choices=("en", "zh"), default=os.environ.get("TRADINGAGENTS_LANG") or "en",
                    help="output language (default en)")
    ap.add_argument("--save", action="store_true", help="archive the memo under memos/")
    ap.add_argument("--portfolio", default=None,
                    help="portfolio JSON ({cash?, currency?, positions:[{ticker,quantity,average_price?}]}) — "
                         "empty positions = flat book; omitting the flag leaves holdings unknown")
    ap.add_argument("--max-calls", type=int, default=None,
                    help="cost guard: abort cleanly once this many LLM calls have been made")
    ap.add_argument("--rounds", type=int, default=1,
                    help="debate rounds: each adds one bear cross-exam + one bull response (default 1 keeps the cost profile)")
    ap.add_argument("--html", action="store_true", help="also render a single-file HTML memo (issue #4)")
    args = ap.parse_args()
    if args.ticker != "DEMO" and os.path.abspath(args.data) == os.path.abspath(
            os.path.join(KIT, "data", "demo", "DEMO.json")):
        sys.exit(f"refused honestly -- ticker {args.ticker} with the default DEMO card would "
                 "mislabel synthetic data as a real verdict. Either fetch a real card first "
                 f"(scripts/fetch_card.py --ticker {args.ticker}) and pass --data, "
                 "or use --ticker DEMO for the offline synthetic smoke.")
    LANG = args.lang
    MAX_CALLS = args.max_calls
    t = lambda k, **kw: T[k][LANG].format(**kw) if kw else T[k][LANG]
    p = lambda k: GUEST_PERSONAS[k][LANG] if LANG == "zh" else GUEST_PERSONAS[k]["en"]

    card = json.load(open(args.data))
    try:  # family bridge (S4-A): a dsh-vibe-trading trail converts to a card on the fly
        import from_trail
        if from_trail.is_trail(card):
            card = from_trail.convert(card, args.ticker if args.ticker != "DEMO" else None)
    except ImportError:
        pass
    guests = (list(GUEST_PERSONAS) if args.guests == "all"
              else [g.strip() for g in args.guests.split(",") if g.strip() in GUEST_PERSONAS])
    past_context = ""
    try:  # the track-record loop (issue #2): only the PM reads prior outcomes
        import ledger
        past_context = ledger.context_block(args.ticker)
    except Exception:
        pass
    book = load_portfolio(args.portfolio) if args.portfolio else None  # three-state, issue #5
    holdings = render_portfolio(book, args.ticker)
    t0 = time.time()
    data = json.dumps(card, ensure_ascii=False, indent=1)

    a = llm(t("analyst"), f"{t('data_card')}\n{data}")
    bull_turns = [llm(t("bull"), f"{t('facts')}\n{a}")]      # opening
    bear_turns, last_bull = [], bull_turns[0]
    debate_hist = t("bull_case") + bull_turns[0]
    for i in range(max(1, args.rounds)):                       # --rounds (issue #8); 1 = original shape
        bear_i = llm(t("bear"), f"{t('facts')}\n{a}{debate_hist}")
        bear_turns.append(bear_i)
        debate_hist += t("bear_case") + bear_i
        final = i == args.rounds - 1
        bull_i = llm(t("rebuttal") if final else t("bull_respond"),
                     f"{t('your_case')}\n{last_bull}{t('bear_case')}{bear_i}")
        bull_turns.append(bull_i)
        debate_hist += t("bull_case") + bull_i
        last_bull = bull_i
    join = "\n\n---\n\n"
    bull, bear, reb = join.join(bull_turns[:-1]), join.join(bear_turns), bull_turns[-1]

    guest_memos = {}
    debate_ctx = f"{t('facts')}\n{a}{t('bull_case')}{bull}{t('bear_case')}{bear}{t('bull_rebuttal')}{reb}"
    for pid in guests:
        g = GUEST_PERSONAS[pid]
        prompt = t("guest", name=p(pid), discipline=g["discipline"][LANG], redflag=g["redflag"][LANG])
        out = parse_json(llm(prompt, debate_ctx, json_out=True))
        if isinstance(out.get("take"), list):  # models sometimes return an array — join into paragraphs
            out["take"] = "\n\n".join(str(x) for x in out["take"])
        guest_memos[pid] = out
    guest_digest = "\n".join(
        f"{p(k)}: {v['stance']}@{v['conviction']}" for k, v in guest_memos.items())

    risk = llm(t("risk"),
               f"{t('facts')}\n{a}{t('debate_digest')}\n{bull}\n{bear}"
               + (t("risk_guests") + guest_digest if guest_digest else ""))
    pm = llm(t("pm"),
             f"{t('facts')}\n{a}{t('bull_case')}{bull}{t('bear_case')}{bear}{t('bull_rebuttal')}{reb}"
             + (t("pm_guests") + guest_digest if guest_digest else "")
             + (t("track_record") + past_context if past_context else "")
             + ("\n\n" + holdings + "\n" if holdings else "")
             + t("guardrails") + risk,
             json_out=True)

    verdict = resolve_verdict(pm, LANG)

    review_banner = ("\n" + t("review_note")) if verdict.get("decision") == "REVIEW" else ""

    guest_section = ""
    if guest_memos:
        table = "\n".join(f"| {p(k)} | {v['stance']} | {v['conviction']} |" for k, v in guest_memos.items())
        takes = "\n\n".join(f"### {p(k)}\n{v['take']}" for k, v in guest_memos.items())
        guest_section = f"""{t('h_guests')}
{t('th_guest')}
|---|---|---|
{table}

{takes}

"""

    memo = f"""# IC-MEMO · {args.ticker} · {card.get('as_of', '?')}

```yaml
ticker: {args.ticker}
as_of: {card.get('as_of', '?')}
committee: tradingagents/v1{'(' + t('guests_label') + ': ' + ', '.join(p(k) for k in guest_memos) + ')' if guest_memos else ''}
decision: {verdict.get('decision')}
confidence: {verdict.get('confidence')}
size_hint: {verdict.get('size_hint')}
invalidation: {json.dumps(verdict.get('invalidation', []), ensure_ascii=False)}
portfolio: {('flat' if not book['positions'] else f"{len(book['positions'])} position(s)") if book is not None else 'unknown'}
```

{t('h1_analyst')}
{a}

{t('h1_debate')}
{t('h_bull')}
{bull}

{t('h_bear')}
{bear}

{t('h_rebuttal')}
{reb}

{guest_section}{t('h_risk', n=4 if guest_memos else 3)}
{risk}

{t('h_pm', n=5 if guest_memos else 4)}
{t('verdict_line', d=verdict.get('decision'), c=verdict.get('confidence') if verdict.get('confidence') is not None else '?')}
- {verdict.get('reasoning')}{review_banner}

---
{t('footer', t=int(time.time()-t0), n=COST["calls"], ti=COST["in"], to=COST["out"], f=os.path.basename(args.data))}
"""
    print(memo)
    if args.save:
        os.makedirs(MEMOS, exist_ok=True)
        suffix = "-guests" if guest_memos else ""
        path = os.path.join(MEMOS, f"{args.ticker}-{card.get('as_of', 'x')}{suffix}.md")
        open(path, "w").write(memo)
        print(f"→ {path}", file=sys.stderr)
        try:  # archive → pending ledger entry (idempotent per ticker+date)
            import ledger
            ledger.index()
        except Exception:
            pass
    if args.html:
        try:
            import render_html
            html_path = os.path.splitext(path if args.save else os.path.join(MEMOS, f"{args.ticker}-{card.get('as_of', 'x')}{'-guests' if guest_memos else ''}.md"))[0] + ".html"
            os.makedirs(os.path.dirname(html_path), exist_ok=True)
            open(html_path, "w", encoding="utf-8").write(render_html.render(memo))
            print(f"→ {html_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠ html render failed: {type(e).__name__}", file=sys.stderr)


if __name__ == "__main__":
    main()
