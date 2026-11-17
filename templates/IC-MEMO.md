# IC-MEMO v0.1 — Investment Committee Memo (an open format)

> IC-MEMO is the auditable output format for multi-agent investment decisions:
> every claim carries an evidence tag, every verdict records what moved it,
> and third parties can re-audit the reasoning. Spec repo and more language
> implementations: see docs/. (中文说明见 README.zh-CN.md)

```yaml
ticker: <symbol>
as_of: <data date>
committee: tradingagents/<version>
decision: BUY | OVERWEIGHT | HOLD | UNDERWEIGHT | SELL | PASS | REVIEW
# five tradeable tiers; PASS = evidence insufficient, decline to rule (first-class);
# REVIEW = output unreadable — not a verdict, not tradeable, rerun required
confidence: <0-100>
size_hint: <position sizing hint, %>
invalidation: [ <falsifiable re-review triggers> ]
```

## 1 · Analyst notes (fact layer)
- [A#] <fact> — Source: <data item / date>
(transcribe the input data only; no outside information)

## 2 · Bull-bear debate (argument layer)
### Bull
- [B#] <thesis, citing [A#]>
### Bear
- [R#] <rebuttal / independent bear case, citing [A#] or attacking [B#]>
### Bull rebuttal
- [B#] <response to [R#]>

## 3 · Guest critiques (optional; persona layer)
| Guest | Stance | Conviction |
|---|---|---|
- [P#] <persona-methodology critique, citing [A#]/[B#]/[R#]; last item: "If I were the PM…"

## 4 · Risk guardrails (constraint layer)
- The risk officer only sets constraints, never decides: drawdown/position/correlation caps, invalidation triggers
- [G#] <constraint or trigger>

## 5 · Portfolio manager verdict (decision layer)
- Verdict and confidence; **must name which [B#]/[R#]/[G#]/[P#] moved or persuaded it**
- Unresolved dissent that conflicts with the verdict stays on record (never deleted; only marked not-adopted, with reasons)

## 6 · Provenance
- Model / version / temperature / elapsed time / cost; full round transcripts in the sidecar

---
## Portfolio variant (v1)

`committee: tradingagents/portfolio-v1` replaces the single-ticker head:

```yaml
tickers: [ <list> ]
decision: DEPLOY | HOLD | PASS | REVIEW   # PASS = evidence insufficient to allocate
weights: { <ticker>: <percent> }
cash_pct: <percent>                       # weights + cash_pct must sum to 100
```

Section 2 is the **allocation debate** (bull proposes weights citing [A#-TICKER],
bear challenges them); section 3 carries portfolio guardrails ([G#]: single-name
cap, concentration, a stated-plainly correlation caveat when no correlation data
is in evidence, drawdown triggers). The PM must name the tags that moved each
weight, and overruling a guardrail must be explicit — a weights+cash total that
isn't 100% is flagged on the memo, never silently rescaled.
