# dsh-TradingAgents — Architecture & Ecosystem Interaction

> A complete map of what this project does, how it plugs into DeepSeek
> Harness, and how it talks to the rest of the DSH plugin family.
> Written 2026-11-23; ground truth is the code (v0.3.1, main @ c278a1e).

## 1. What it is (30 seconds)

A **deterministic multi-agent investment committee** that convenes on any
ticker, debates bull-vs-bear with evidence tags, and outputs an **IC-MEMO**
(the open memo format this repo defines, see `docs/ic-memo/`) with a
disciplined verdict. Every number comes from a **data card** — never from
the LLM's imagination. A **verdict ledger** settles past decisions against
real market outcomes (alpha vs benchmark), creating a self-improving
track record that feeds back into future sessions.

## 2. Committee pipeline (the engine core)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE COMMITTEE SESSION (one ticker)                      │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐   ┌───────┐  │
│  │ ANALYST  │───▶│   BULL   │───▶│   BEAR   │───▶│  RISK   │──▶│   PM  │  │
│  │          │    │          │    │(sees bull│    │(guard-  │   │(verdict│  │
│  │ [A#]     │    │ [B#]     │    │  output) │    │ rails   │   │ + conf│  │
│  │ facts    │    │ cites    │    │ [R#]     │    │ only,   │   │ + size│  │
│  │ from     │    │ [A#]     │    │ rebuts + │    │ never   │   │ _hint │  │
│  │ data card│    │          │    │ independ-│    │ decides)│   │       │  │
│  │          │    │          │    │ ent args │    │ [G#]    │   │       │  │
│  └──────────┘    └────┬─────┘    └──────────┘    └─────────┘   └───────┘  │
│                       │            ▲                                     │
│                       ▼            │ rebuttal (max 3, strongest only)    │
│                  ┌─────────┐       │                                     │
│                  │  BULL   │───────┘                                     │
│                  │ respond │    ┌─────────────────────────────┐           │
│                  └─────────┘    │   GUEST SEATS (optional)    │           │
│                                 │   Buffett · Munger · Lynch  │           │
│                                 │   Wood — critique the       │           │
│                                 │   DEBATE (not the verdict)  │           │
│                                 └─────────────────────────────┘           │
│                                                                             │
│  Output: IC-MEMO (markdown)                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │ yaml head: ticker / as_of / committee / decision / confidence   │      │
│  │             / size_hint / invalidation[]                        │      │
│  │ §1 Analyst brief ([A#] facts)                                    │      │
│  │ §2 Bull-bear debate ([B#] ↔ [R#], with rebuttals)               │      │
│  │ §3 Risk guardrails ([G#] — position caps, triggers, events)     │      │
│  │ §4 PM verdict (cites [G#] that bound it)                        │      │
│  │ Footer: cost + not-investment-advice                             │      │
│  └──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**LLM calls per session**: 4 base (analyst, bull, bear, risk+PM) + 2
(bull rebuttal + PM synthesis) = 6 at rounds=1; each extra debate round
adds 2 (bear cross-exam + bull response). Cost-guard `--max-calls N`
aborts cleanly before the (N+1)-th.

## 3. The data card (the evidence covenant)

```
┌──────────────────────── DATA CARD (JSON) ─────────────────────────┐
│                                                                   │
│  US path (fetch_card.py, zero-key):                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐      │
│  │   CBOE   │  │   SEC    │  │  NASDAQ  │  │    Tencent    │      │
│  │ quote/   │  │ 10-K     │  │ news     │  │  (A-share +   │      │
│  │ K-line/  │  │ 3-stmt   │  │          │  │   fallback)   │      │
│  │ IV30     │  │          │  │          │  │               │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘      │
│       │             │             │               │               │
│       └─────────────┴──────┬──────┴───────────────┘               │
│                            ▼                                       │
│                    OpenBB multi-provider layer                     │
│                    (or Tencent direct for CN)                      │
│                            │                                       │
│                            ▼                                       │
│                  ┌──────────────────┐                              │
│                  │   card.json      │  ← the ONLY thing the        │
│                  │ {quote, bars,    │    committee LLM may cite;   │
│                  │  technicals,     │    "nothing outside the      │
│                  │  statements,     │     data card" is the        │
│                  │  news, _source}  │    product covenant          │
│                  └──────────────────┘                              │
│                                                                     │
│  Historical mode (--date): truncates bars/technicals/52w at the     │
│  date; SEC statements cut by period end (filing lag stated);        │
│  live quote/IV/news withheld (no point-in-time source).             │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. DeepSeek Harness integration (three surfaces)

```
┌───────────────────────── DEEPSEEK HARNESS (the host) ─────────────────────────┐
│                                                                                │
│  ┌─── Profile layer ──────────────────────────────────────────────────────┐   │
│  │                                                                        │   │
│  │   dsh-base (core bundle)                                               │   │
│  │        │                                                               │   │
│  │        ▼  cordis.patch.yml inserts:                                    │   │
│  │   ┌─────────────────────────┐                                          │   │
│  │   │  dsh-tradingagents     │  ← this plugin                            │   │
│  │   │  (lib/index.js)        │                                           │   │
│  │   └───────────┬─────────────┘                                           │   │
│  │               │ apply(ctx) on profile compose                           │   │
│  │               ▼                                                         │   │
│  │   ┌──────────────────────────────────────────────────────────────┐     │   │
│  │   │  ctx.tools.register(defineTool({...}))  × 2 tools            │     │   │
│  │   │                                                                │     │   │
│  │   │  committee_session(ticker, data?, guests?, rounds?,           │     │   │
│  │   │                    portfolio?, date?, lang?)                  │     │   │
│  │   │    → builds card if needed → runs engine → returns IC-MEMO   │     │   │
│  │   │                                                                │     │   │
│  │   │  verdict_settle()                                             │     │   │
│  │   │    → indexes memos → settles due windows (alpha vs benchmark)│     │   │
│  │   └──────────────────────────┬───────────────────────────────────┘     │   │
│  │                             │                                           │   │
│  │  └──────────────────────────┼───────────────────────────────────────────┘   │
│  │                             │                                               │
│  │   SKILL (skills/dsh-tradingagents/SKILL.md)                                │
│  │        — dsh-skill-filesystem discovers it; teaches the agent              │
│  │          when to call the tools and how to read the memo                   │
│  │                                                                             │
│  │   CLI (npm bin: tradingagents)                                              │
│  │        — JS shell → spawns Python engine (works outside DSH too)           │
│  └────────────────────────────────────────────────────────────────────────────┘
│                                                                                │
│  The agent sees the two tools; calling committee_session produces a            │
│  full IC-MEMO inline in the reply. No agentic tool loops — the committee       │
│  itself is the loop, deterministic by design.                                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

## 5. Ecosystem interaction (family bridges)

```
┌──────────────── DSH PLUGIN ECOSYSTEM ────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         ┌────────────┐  │
│  │ dsh-vibe-trading │         │   dsh-WrenAI     │         │  dsh-uigen │  │
│  │  (research tool) │         │  (semantic layer │         │  (ui_compose│  │
│  │                  │         │   over WeKnora)  │         │   + genui   │  │
│  │  Research trail  │         │                  │         │   renderer) │  │
│  │  (research-trail │         │  Future: PM asks │         │             │  │
│  │  /1 JSON)        │         │  "how many times │         │  IC-MEMO →  │  │
│  │       │          │         │  was this KB used│         │  dsh-ui     │  │
│  │       │from_trail│         │  recently?" via  │         │  verdict    │  │
│  │       ▼  .py     │         │  WrenAI's        │         │  card       │  │
│  │  ┌────────────┐  │         │  --check drift   │         │  (inline    │  │
│  │  │ data card  │──┼────────▶│  report          │────────▶│  render)    │  │
│  │  │ (converted)│  │         │                  │         │             │  │
│  │  └────────────┘  │         └──────────────────┘         └────────────┘  │
│  │       │                                                                   │
│  │       ▼                                                                   │
│  │  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  │              dsh-TradingAgents (the committee)                  │    │
│  │  │                                                                  │    │
│  │  │  Input bridges:   from_trail.py (vibe-trading trails)          │    │
│  │  │                    portfolio_committee.py (multi-ticker)        │    │
│  │  │                    fetch_card.py (live zero-key data)           │    │
│  │  │                                                                  │    │
│  │  │  Output bridges:  IC-MEMO (open format, docs/ic-memo/)          │    │
│  │  │                    verdict_card.py (dsh-ui inline)              │    │
│  │  │                    render_html.py (single-file HTML)            │    │
│  │  │                    render_session_svg.py (session card)         │    │
│  │  │                    ledger.py --report (track-record snapshot)   │    │
│  │  │                    validate_memo.py (schema gate)               │    │
│  │  └──────────────────────────────────────────────────────────────────┘    │
│  │              │                              │                            │
│  │              ▼                              ▼                            │
│  │  ┌──────────────────┐         ┌──────────────────────────────┐           │
│  │  │  WeKnora (RAG)   │         │  Family download board       │           │
│  │  (future: memo      │         │  (gap-radar auto-discovers   │           │
│  │  archive as a       │         │   npm packages; star/usage   │           │
│  │  knowledge base)    │         │   tracked)                   │           │
│  │  └──────────────────┘         └──────────────────────────────┘           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 6. The verdict ledger (the self-improvement loop)

```
┌──────────────── VERDICT LEDGER (memos/ledger.json) ────────────────────────┐
│                                                                             │
│   IC-MEMO ──(ledger.py --index)──▶ Ledger entries                          │
│                                       {ticker, date, decision, confidence,  │
│                                        pending: true}                      │
│                                             │                               │
│                        ┌────────────────────┼──────────────────────┐       │
│                        ▼                    ▼                      ▼       │
│                 (window not            (window has           (fetch fails)  │
│                  traded yet)           traded fully)              │         │
│                        │                    │                      │       │
│                   stays pending        settles                 retriable   │
│                        │                    │                      skip    │
│                        │                    ▼                                │
│                        │            ┌──────────────┐                         │
│                        │            │  Settlement  │                         │
│                        │            │  entry = first close AFTER decision   │
│                        │            │  exit  = 5 sessions later            │
│                        │            │  alpha = raw − benchmark             │
│                        │            │  (SPY / SSE Composite)               │
│                        │            │  never scores the live bar           │
│                        │            │  PASS/REVIEW never settle             │
│                        │            └──────┬───────┘                         │
│                        │                   │                                 │
│                        │                   ▼                                 │
│                        │            ┌──────────────┐                         │
│                        │            │  Reflection  │ (one quick LLM call:   │
│                        │            │  2-4 sentences, window boundary       │
│                        │            │  stated)      │                         │
│                        │            └──────┬───────┘                         │
│                        │                   │                                 │
│                        │                   ▼                                 │
│                        │            ┌──────────────┐                         │
│  Next committee ◀──────┼────────────│  [T#] tags   │ (same-ticker outcomes   │
│  session's PM         │            │  re-injected │  + cross-ticker lessons │
│  payload carries      │            │  into PM     │  — only the PM reads    │
│  the track record     │            └──────────────┘  them)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7. Execution model summary

| Surface | Entry point | What it does |
|---|---|---|
| **DSH tool** (primary) | `ctx.tools.register` in `npm/lib/index.js` | `committee_session` + `verdict_settle` — the agent calls them mid-conversation |
| **CLI** (standalone) | `npm bin/tradingagents` | Same engine, no DSH needed (`tradingagents demo`, `card`, `settle`, `report`) |
| **Python direct** | `scripts/tradingagents.py` | The engine itself; all flags |
| **Cron (unattended)** | system crontab 06:30 | `ledger.py --settle` — settles due windows daily |

**Language/runtime**: engine in Python (stdlib-only, zero pip deps);
DSH plugin shell in Node (ESM); the plugin spawns the Python engine as a
child process — same scripts the CLI uses, same memos/cards/ledger paths.

## 8. What the plugin does NOT do (non-goals, nailed down)

No agentic tool loops (the committee IS the loop); no LangGraph or heavy
frameworks (deterministic pipeline is the selling point); no ChatGPT OAuth;
no interactive TUI; no separate Trader role (PM's size_hint covers it);
no risk-layer debate-ification (guardrails audit, they don't decide).
