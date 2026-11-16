---
name: dsh-tradingagents
description: Multi-agent investment committee (TradingAgents-style) for DeepSeek Harness — analyst/bull/bear/risk/PM debate with evidence tags, PASS as first-class verdict, IC-MEMO auditable output. Runs offline demo or with real data cards.
---

Use this skill when asked to research a ticker, debate an investment idea, or
produce an investment committee memo. The committee is a deterministic script —
you orchestrate, it decides.

## Run

```bash
python3 $KIT/scripts/tradingagents.py --ticker DEMO                    # offline synthetic smoke
python3 $KIT/scripts/tradingagents.py --data <card.json> --ticker XXX  # real/curated data card
```

## Data discipline (the covenant)

- The committee only sees the data card. **You must not let it invent numbers**:
  build the card from real sources (yfinance/akshare/manual), every item dated.
- Synthetic runs must keep the `_note` marker and DEMO ticker — never present
  synthetic output as real analysis.
- If data is insufficient for a card, say so and don't run — garbage in, confident
  garbage out.

## Verdicts

- `PASS` is a valid, respectable outcome (evidence insufficient). Do not rerun
  the committee hoping for a different verdict — reruns require NEW data
  (invalidation triggers in the memo define what counts).
- Report the verdict verbatim with its named influences; archive the memo
  (`--save`), never edit an archived memo.

## Output

Every session emits an IC-MEMO (`templates/IC-MEMO.md` format). When the person
asks follow-ups, quote tag IDs ([A#]/[B#]/[R#]/[G#]) — the memo is the single
source of truth.

*Not investment advice.*
