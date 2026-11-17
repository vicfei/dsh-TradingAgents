# IC-MEMO v0.1 — Investment Committee Memo (an open format)

> IC-MEMO is the auditable output format for multi-agent investment decisions:
> every claim carries an evidence tag, every verdict records what moved it,
> and third parties can re-audit the reasoning. Spec repo and more language
> implementations: see docs/. (中文说明见 README.zh-CN.md)

```yaml
ticker: <symbol>
as_of: <data date>
committee: tradingagents/<version>
decision: BUY | HOLD | SELL | PASS      # PASS = evidence insufficient, decline to rule
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
