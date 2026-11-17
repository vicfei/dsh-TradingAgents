---
name: dsh-tradingagents
description: Multi-agent investment committee (TradingAgents-style) for DeepSeek Harness — analyst/bull/bear/risk/PM debate with evidence tags, PASS as a first-class verdict, IC-MEMO auditable output. Runs offline demo or with real data cards. English-first, --lang zh for Chinese.
---

Use this skill when asked to research a ticker, debate an investment idea, or
produce an investment committee memo. The committee is a deterministic script —
you orchestrate, it decides.

## Run

```bash
python3 $KIT/scripts/tradingagents.py --ticker DEMO                    # offline synthetic smoke
python3 $KIT/scripts/tradingagents.py --ticker DEMO --guests all --save  # + 4 guest seats
python3 $KIT/scripts/fetch_card.py --ticker NVDA --committee           # real data → full committee
python3 $KIT/scripts/ledger.py --settle                                # settle due verdicts (alpha vs benchmark)
python3 $KIT/scripts/render_html.py memos/<memo>.md                    # single-file HTML memo
python3 $KIT/scripts/tradingagents.py --ticker X --data c.json --portfolio book.json  # holdings-aware verdict
python3 $KIT/scripts/fetch_card.py --ticker NVDA --date 2025-06-15             # as-of historical card (SEC cut by period end)
```

## Track record (issue #2 loop)

Every `--save` archives a memo and appends a pending verdict-ledger entry. After the
5-trading-day holding window trades out, `--settle` resolves it: entry at the first
close after the decision date, raw return + alpha vs benchmark (SPY / SSE Composite),
one short reflection — and the next session's PM reads those lessons before ruling.

Output language: English by default, `--lang zh` for Chinese (env `TRADINGAGENTS_LANG`).

## Data discipline (the covenant)

- The committee only sees the data card. **You must not let it invent numbers**:
  build the card from real sources, every item dated.
- Synthetic runs must keep the `_note` marker and DEMO ticker — never present
  synthetic output as real analysis.
- If data is insufficient for a card, say so and don't run — garbage in,
  confident garbage out.

## Verdicts

- Five tradeable tiers: BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL.
- `PASS` is a valid, respectable outcome (evidence insufficient). Do not rerun
  the committee hoping for a different verdict — reruns require NEW data
  (invalidation triggers in the memo define what counts).
- `REVIEW` is a different exit: the PM's output could not be parsed into a
  decision. It is not a verdict and is never traded or recorded as PASS —
  rerun the session.
- Report the verdict verbatim with its named influences; archive the memo
  (`--save`), never edit an archived memo.

## Output

Every session emits an IC-MEMO (`templates/IC-MEMO.md` format). When the person
asks follow-ups, quote tag IDs ([A#]/[B#]/[R#]/[G#]/[P#]) — the memo is the single
source of truth.

*Not investment advice.*
