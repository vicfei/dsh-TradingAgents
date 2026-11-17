---
name: dsh-tradingagents
description: Multi-agent investment committee (TradingAgents-style) — analyst/bull/bear/risk/PM debate with optional Buffett/Munger/Lynch/Wood guest seats, evidence tags, PASS as a first-class verdict, auditable IC-MEMO output. Deterministic CLI, zero-key real-data cards via OpenBB (CBOE/SEC/nasdaq).
---

Use this skill when asked to research a ticker, debate an investment idea, or
produce an investment committee memo. The committee is a deterministic CLI —
you orchestrate, it decides. `tradingagents` must be on PATH
(`npm i -g dsh-tradingagents`).

## Run

```bash
tradingagents demo --save                     # offline synthetic smoke (DEMO marker kept)
tradingagents demo --guests all --save        # + 4 master-persona guest seats critiquing the debate
tradingagents card --ticker NVDA --committee  # zero-key rich card (CBOE quote/K-line/IV + SEC 10-K + nasdaq news) → full committee
tradingagents card --ticker 600519 --committee  # A-share card (Tencent channel)
tradingagents --ticker X --data card.json --save  # pre-built data card
```

Requires `python3` (stdlib only for the committee; `pip install --user openbb`
enables the rich card — falls back to Tencent channels without it).
Memos land in `./memos/`, cards in `./cards/` (relative to where you invoke).

## Data discipline (the covenant)

- The committee only sees the data card. **You must not let it invent numbers**:
  build the card from real sources, every item carries its source and date.
- Synthetic runs must keep the DEMO ticker — never present synthetic output as
  real analysis.
- If data is insufficient for a card, say so and don't run — garbage in,
  confident garbage out.

## Verdicts

- `PASS` is a valid, respectable outcome (evidence insufficient). Do not rerun
  the committee hoping for a different verdict — reruns require NEW data
  (invalidation triggers in the memo define what counts).
- Report the verdict verbatim with its named influences; archive the memo
  (`--save`), never edit an archived memo.

## Output

Every session emits an IC-MEMO (format spec bundled at `templates/IC-MEMO.md`).
When the person asks follow-ups, quote tag IDs ([A#]/[B#]/[R#]/[G#]/[P#]) —
the memo is the single source of truth.

*Not investment advice.*
