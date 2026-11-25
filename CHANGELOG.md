## 0.4.0 (2026-11-25) — A-share parity

The theme: **the A-share card now equals the US card** (S6 replan #50, driven by the CN audit + the TradingAgents-CN market validation). Plus the ledger's first compounding evidence.

- **CN rich card (#54/#55)**: F10 financial abstract (revenue/NP + YoY, ROE, margins, EPS/BPS — report period named), SW + CSRC industry classification, and top-3 news — eastmoney-family free endpoints, each block degrading alone with a named skip (the audit caught the old path silently shipping `news: empty`). Ticker grammar unified: bare codes and `sh/sz/bj`-prefixed forms everywhere (#54).
- **A-share microstructure in the committee (#56/#57)**: T+1 (session-ahead guardrails, no intraday stop), limit bands (±10/20/30%, ST 5%, limit-down exit traps), stamp duty — injected into risk + PM payloads as venue facts, never as data-card evidence; memo yaml carries the `market_rules` audit key.
- **as-of CN (#58/#59)**: bars/technicals truncated at the date; live quote/PE/PB/mcap/news withheld; F10 fundamentals gated by **statutory disclosure deadlines** (CSRC schedule — period-end filtering alone leaked the Q3 report into an Oct-15 card). CN backtest grids unblocked end to end (live: one cell → HOLD@58 → +1.1% alpha vs SSE).
- **Chip distribution — 筹码分布 (#60/#61)**: the CN-native evidence type, computed in-card from OHLCV (60-session memory half-life; volume-profile approximation, assumption stated on the card). CI-tested math. Live session: the bull/bear fight cited the 92.6% profit ratio and the SMA60≈avg-cost confluence.
- **CN settle channel #2 (#52/#53)**: tencent → eastmoney-cn (push2his qfq, dual-hop) — the US rebuild pattern extended to A-shares.
- **US price chain rebuild (#47/#48, hotfixed 2026-11-24)**: sina #4 + eastmoney #5 after all four US channels fell the same day — the outage that landed the first real settlement: **NVDA@2026-11-13, +8.1% alpha vs SPY**; track-record snapshots live (`docs/track-record/`).
- **Report copy fix (#49)**: PASS settles (only REVIEW entries don't) — the discipline header now says what the code does.

**S6.1 live evidence** (rides this release): the 2026-11-25 real session on 600519 → OVERWEIGHT@62 — the PM's size decision visibly changed by the [T2]/[T3] lesson ("high-confidence PASS with 0% size forfeited upside" → starter position instead), guardrails rewritten session-ahead because of T+1. The committee is learning from its own scorecard.


- **US price channel rebuild (#47)**: all three US tiers fell at once on 2026-11-24 (cboe 403 region-throttle, yahoo 429, SG-relay yfinance rate-limited by Yahoo itself; tencent-usfqkline still returns boundary garbage only). Added **sina** as US fallback #4 — CN-native, no key, full history one-shot; 2026-11-23 closes cross-verified identical against eastmoney qfq (NVDA/AAPL/SPY). Added **eastmoney** (push2his, direct + SG-relay hop) as #5 — qfq semantics, but its CDN blackholes bursty IPs, so it stays a low-volume last resort.

## 0.3.1 (2026-11-23)

- **settle integrity (S5.0, PR #42)**: starvation guard (boundary-bar garbage from degraded US channels raises a retriable skip instead of silently starving), SG-relay third US tier, truthful settle reporting (settled / retriable fetch failures / windows-not-fully-traded — "nothing due" only when nothing is pending). Live before/after: `nothing due` → `3 starved · 2 windows not fully traded · 6/6 pending preserved`.
- **IC-MEMO internal schema (PR #43)**: `scripts/validate_memo.py` — yaml head, closed verdict vocabulary, role tags, footer contract; CI gates the real archive (7/7 GREEN). The spec lives at docs/ic-memo/ (folded back from the cancelled standalone repo, 2026-11-23).
- **dsh-ui verdict card (PR #44)**: `scripts/verdict_card.py` — a memo's inline projection (stat + top [G#] quotes + not-investment-advice) as a ```dsh-ui block; CI lints cards through dsh-uigen compose() (genui 0.16.0 whitelist).
- **track-record snapshot (PR #45)**: `tradingagents report` / `scripts/ledger.py --report` — one-command docs/track-record/<date>.md the moment the first real settlement lands.

# Changelog

## 0.3.0 (2026-11-20) — ledger integrity + the family bridge

- **Ledger-integrity guard** (#36): `--ticker` ≠ DEMO with the default DEMO
  card now refuses with the exact fix paths — a bare ticker can never again
  mislabel synthetic data as a real verdict (caught live during settlement-day
  execution; the polluted entry was removed on discovery). CI unit check.
- **The family bridge** (#37, S4-A): dsh-vibe-trading research trails
  (schema research-trail/1) convert to committee cards on the fly — the
  trail's deterministic computed layer is covenant-safe evidence; its
  findings ride as a research note conspicuously marked "PRIOR LLM
  INTERPRETATION — context only, never data". Live E2E: a real trail →
  OVERWEIGHT@58 with OOS segments cited and empty statistics dismissed.
- Session map SVG on the homepage, README embed fixes, typed-tools memo
  render fix (#27–#31, previously shipped in 0.2.2 hotfix line — consolidated
  release notes here).

## 0.2.2 — bin syntax repair line
## 0.2.0 — typed tools (committee_session / verdict_settle)
## 0.1.x — launch line (English engine, verdict ledger, settle loop)
