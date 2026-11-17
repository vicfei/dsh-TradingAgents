#!/usr/bin/env python3
"""portfolio committee — the multi-ticker allocation debate (issue #9, R4)

The single-ticker committee decides *a* ticker; this one decides *a portfolio*:
one analyst pass per ticker (facts only, [A#]), then one allocation debate —

  bull (allocation case, weights must cite [A#]) → bear (challenges, [R#])
  → bull response → risk (portfolio guardrails only, [G#]) → PM

The PM outputs an allocation JSON: decision ∈ DEPLOY | HOLD | PASS (REVIEW when
unreadable — same sentinel semantics as the single-ticker committee), per-ticker
weights summing to ≤ 100 with the remainder as explicit cash. Guardrails: a
single name may not exceed 40% unless the PM explicitly overrules with reasons
(overruling a guardrail must be named, not silent).

Calls: N analysts + 5. Cost guard and evidence discipline identical to the base
committee (shared llm()/COST from tradingagents.py).

Usage:
  python3 scripts/portfolio_committee.py --tickers NVDA,AAPL,MSFT            # cards from cards/
  python3 scripts/portfolio_committee.py --tickers ... --refetch             # fetch cards first
  python3 scripts/portfolio_committee.py --tickers ... --save --html
"""
import argparse, json, os, subprocess, sys, time

import tradingagents as TA
from tradingagents import COST, T, llm, tt

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.environ.get("TRADINGAGENTS_CARDS") or os.path.join(KIT, "cards")
MEMOS = TA.MEMOS

PORTFOLIO_VERDICTS = ("DEPLOY", "HOLD", "PASS", "REVIEW")

PT = {
    "analyst_each": {"en": "You are the analyst covering {t} within a portfolio review: transcribe its data card into [A#{i}] facts (tags carry the ticker suffix, e.g. [A1-NVDA]) — one entry per fact, nothing added.",
                     "zh": "你是组合评审中负责 {t} 的分析师：把它的数据卡转写为 [A#{i}] 事实（标签带标的后缀，如 [A1-NVDA]）——一条不漏，不添加。"},
    "bull": {"en": "You are the allocation bull: propose target weights across the given tickers (and cash) that maximize expected risk-adjusted return. Every weight decision must cite facts [A#-*]; tag your points [B#]. State the weights explicitly.",
             "zh": "你是配置多方：在给定标的（与现金）间提出目标权重以最大化预期风险调整收益。每个权重决定必须引用 [A#-*] 事实；论点 [B#]。明确写出权重。"},
    "bear": {"en": "You are the allocation bear: challenge each proposed weight — concentration, correlation, crowding, downside asymmetry — every point [R#] citing [A#-*] or attacking [B#].",
             "zh": "你是配置空方：逐项挑战提议权重——集中度/相关性/拥挤度/下行不对称——每条 [R#] 引用 [A#-*] 或攻击 [B#]。"},
    "bull_respond": {"en": "You are the allocation bull: respond to the bear's strongest challenges, adjusting weights where the attack lands, [B#].",
                     "zh": "你是配置多方：回应空方最强质疑，被击中处调整权重，[B#]。"},
    "risk": {"en": "You are the portfolio risk officer: you do not decide; set portfolio guardrails only — max single-name weight, concentration limits, a qualitative correlation caveat (state plainly that no correlation data is in evidence), drawdown/invalidation triggers — each [G#].",
             "zh": "你是组合风控官：不决策，只立组合护栏——单一名目权重上限、集中度限制、相关性定性警示（明示证据中没有相关性数据）、回撤/失效触发器——每条 [G#]。"},
    "pm": {"en": 'You are the portfolio manager: output JSON {"decision":"DEPLOY|HOLD|PASS","confidence":0-100,"weights":{"TICKER":percent},...,"cash_pct":percent,"reasoning":"name which [A#]/[B#]/[R#]/[G#] moved each weight; overruling any guardrail must be explicit","invalidation":[..]}. Weights + cash_pct must sum to 100; no single name above 40 unless you explicitly overrule [G#] with reasons. When the evidence is insufficient to allocate, PASS.',
           "zh": '你是组合经理：输出 JSON {"decision":"DEPLOY|HOLD|PASS","confidence":0-100,"weights":{"标的":百分比,...},"cash_pct":百分比,"reasoning":"点名哪些 [A#]/[B#]/[R#]/[G#] 决定了各权重；推翻任何护栏必须明说","invalidation":[..]}。权重+现金合计 100；单一名目超 40 必须明示推翻哪条 [G#] 及理由。证据不足以配置时 PASS。'},
    "h1": {"en": "# IC-MEMO · PORTFOLIO · {d}", "zh": "# IC-MEMO · 组合 · {d}"},
    "s_analysts": {"en": "## 1 · Analyst notes ({t})", "zh": "## 1 · 分析师纪要（{t}）"},
    "s_debate": {"en": "## 2 · Allocation debate", "zh": "## 2 · 配置辩论"},
    "s_risk": {"en": "## 3 · Portfolio guardrails", "zh": "## 3 · 组合护栏"},
    "s_pm": {"en": "## 4 · Portfolio manager allocation", "zh": "## 4 · 组合经理配置"},
    "verdict_line": {"en": "- Verdict **{d}** (confidence {c}) · weights {w} · cash {cash}%",
                     "zh": "- 裁决 **{d}**（置信度 {c}）· 权重 {w} · 现金 {cash}%"},
    "footer": {"en": "*{t}s · {n} calls · {ti:,} in / {to:,} out tokens · deepseek-chat · temperature=0 · portfolio committee v1 · not investment advice*",
               "zh": "*耗时 {t}s · {n} 次调用 · {ti:,} 入 / {to:,} 出 token · deepseek-chat · temperature=0 · 组合议院 v1 · 非投资建议*"},
}


def load_cards(tickers, refetch, lang):
    cards = {}
    for t in tickers:
        path = os.path.join(CARDS, f"{t}.json")
        if refetch or not os.path.exists(path):
            r = subprocess.run([sys.executable, os.path.join(KIT, "scripts", "fetch_card.py"),
                                "--ticker", t, "--lang", lang], capture_output=True, text=True)
            if not os.path.exists(path):
                raise SystemExit(f"card fetch failed for {t}: {r.stdout[-200:]} {r.stderr[-200:]}")
        cards[t] = json.load(open(path))
    return cards


def resolve_allocation(pm_text, allowed=PORTFOLIO_VERDICTS):
    """Same sentinel semantics as tradingagents.resolve_verdict, portfolio vocabulary."""
    try:
        v = TA.parse_json(pm_text)
    except Exception:
        v = None
    if not isinstance(v, dict) or str(v.get("decision", "")).strip().upper() not in allowed[:-1]:
        return {"decision": "REVIEW", "confidence": None, "weights": {}, "cash_pct": None,
                "reasoning": tt("The PM's output could not be parsed into an allocation; not a verdict — rerun.",
                                "组合经理输出无法解析为配置；非判决——请重跑。"), "invalidation": [],
                "_unparsed_head": pm_text[:200]}
    v["decision"] = str(v["decision"]).strip().upper()
    v.setdefault("weights", {})
    v.setdefault("cash_pct", 0)
    # models sometimes put a literal Cash key inside weights — normalize it into
    # cash_pct (dedupe), then check the sum; a wrong total is flagged, never silently rescaled
    cash_in_weights = {k: w for k, w in v["weights"].items() if str(k).strip().lower() == "cash"}
    for k in cash_in_weights:
        v["weights"].pop(k)
    if cash_in_weights:
        v["cash_pct"] = max(v["cash_pct"] or 0, *cash_in_weights.values())
    total = sum(w for w in v["weights"].values() if isinstance(w, (int, float))) + (v["cash_pct"] or 0)
    if abs(total - 100) > 1.0 and v["decision"] != "PASS":
        v["_weight_warning"] = tt(f"weights + cash sum to {total:.0f}%, not 100% — flagged, not silently normalized",
                                  f"权重+现金合计 {total:.0f}%，非 100%——标记而不静默归一")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True, help="comma-separated, e.g. NVDA,AAPL,MSFT")
    ap.add_argument("--refetch", action="store_true", help="fetch fresh cards first")
    ap.add_argument("--lang", choices=("en", "zh"), default=TA.LANG)
    ap.add_argument("--max-calls", type=int, default=None)
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--html", action="store_true")
    args = ap.parse_args()
    TA.LANG = args.lang
    if args.max_calls:
        TA.MAX_CALLS = args.max_calls
    t = lambda k, **kw: PT[k][args.lang].format(**kw) if kw else PT[k][args.lang]

    tickers = [x.strip().upper() for x in args.tickers.split(",") if x.strip()]
    if len(tickers) < 2:
        raise SystemExit("portfolio committee needs at least 2 tickers")
    cards = load_cards(tickers, args.refetch, args.lang)
    t0 = time.time()

    facts, sections = {}, []
    for t_ in tickers:
        facts[t_] = llm(t("analyst_each", t=t_, i="1"), f"{tt('Data card:', '数据卡：')}\n{json.dumps(cards[t_], ensure_ascii=False, indent=1)}")
        sections.append(f"{t('s_analysts', t=t_)}\n{facts[t_]}")
    all_facts = "\n\n".join(f"[{k}]\n{v}" for k, v in facts.items())

    bull = llm(t("bull"), f"{tt('Facts per ticker:', '各标的事实：')}\n{all_facts}")
    bear = llm(t("bear"), f"{tt('Facts per ticker:', '各标的事实：')}\n{all_facts}\n\n{tt('Bull allocation:', '多方配置：')}\n{bull}")
    reb = llm(t("bull_respond"), f"{tt('Your allocation:', '你的配置：')}\n{bull}\n\n{tt('Bear attack:', '空方攻击：')}\n{bear}")
    risk = llm(t("risk"), f"{tt('Facts per ticker:', '各标的事实：')}\n{all_facts}\n\n{tt('Debate digest:', '辩论摘要：')}\n{bull}\n{bear}")
    pm = llm(t("pm"),
             f"{tt('Facts per ticker:', '各标的事实：')}\n{all_facts}\n\n{tt('Bull:', '多方：')}\n{bull}\n{tt('Bear:', '空方：')}\n{bear}\n{tt('Bull response:', '多方回应：')}\n{reb}\n\n{tt('Guardrails:', '护栏：')}\n{risk}",
             json_out=True)
    alloc = resolve_allocation(pm)
    w = ", ".join(f"{k} {v}%" for k, v in alloc.get("weights", {}).items()) or "—"

    memo = f"""{t('h1', d=cards[tickers[0]].get('as_of', '?'))}

```yaml
committee: tradingagents/portfolio-v1
tickers: [{', '.join(tickers)}]
decision: {alloc.get('decision')}
confidence: {alloc.get('confidence')}
weights: {json.dumps(alloc.get('weights', {}), ensure_ascii=False)}
cash_pct: {alloc.get('cash_pct')}
invalidation: {json.dumps(alloc.get('invalidation', []), ensure_ascii=False)}
```

{chr(10).join(sections)}

{t('s_debate')}
### {tt('Bull', '多方')}
{bull}

### {tt('Bear', '空方')}
{bear}

### {tt('Bull response', '多方回应')}
{reb}

{t('s_risk')}
{risk}

{t('s_pm')}
{t('verdict_line', d=alloc.get('decision'), c=alloc.get('confidence') if alloc.get('confidence') is not None else '?', w=w, cash=alloc.get('cash_pct'))}
- {alloc.get('reasoning')}
{alloc.get('_weight_warning', '')}

---
{t('footer', t=int(time.time()-t0), n=COST['calls'], ti=COST['in'], to=COST['out'])}
"""
    print(memo)
    if args.save:
        os.makedirs(MEMOS, exist_ok=True)
        path = os.path.join(MEMOS, f"PORTFOLIO-{cards[tickers[0]].get('as_of', 'x')}.md")
        open(path, "w", encoding="utf-8").write(memo)
        print(f"→ {path}", file=sys.stderr)
        if args.html:
            import render_html
            hp = os.path.splitext(path)[0] + ".html"
            open(hp, "w", encoding="utf-8").write(render_html.render(memo))
            print(f"→ {hp}", file=sys.stderr)


if __name__ == "__main__":
    main()
