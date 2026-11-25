# S6 plan — A-share parity & the compounding ledger (2026-11-25 → 2026-12-15)

Tracker: issue #50. Supersedes the S6 *preview* in plan-S5.md (TS SDK /
persona-pack move to S7 preview); the S5.1 residue (owner-gated posting) rides
inside S6.2 unchanged.

## Why re-plan — three new facts since the S5 v3 amendment

1. **The ledger has real output.** First settlement landed 2026-11-24:
   NVDA@2026-11-13 (PASS@78) → entry 11-16 @156.14, exit 11-23 @165.05,
   raw +5.7%, **alpha +8.1% vs SPY**, reflection attached. It took an unplanned
   US price-chain rebuild first (#47/#48: all four channels fell the same day;
   sina #4 + eastmoney #5 now cross-verified). Four more windows settle on the
   cron by 11-28 (600519 + NVDA@11-16 on 11-25; AAPL + sh600519 on 11-28).
2. **The CN audit.** The A-share evidence card carries ~60% of the US card:
   `fetch_cn()` (the akshare rich card — fundamentals/industry/news) is written
   but never wired; news enrichment silently skips under cloud-IP throttling
   (the 600519 memo shows `[A7] news: empty`); as-of mode refuses CN — which
   also blocks CN backtest grids despite `backtest.py`'s docstring claiming
   A-share support; no A-share microstructure awareness anywhere (T+1, ±10/20/30%
   limit bands, ST); the CN settle path is single-channel (the US path just
   taught us what single-channel costs); ticker formats differ between entry
   points (`sh600519` parses in the ledger but not in fetch_card).
3. **Market validation.** TradingAgents-CN (33,066★ / 6,875 forks, v3.0) proves
   A-share multi-agent research is a mass pain at scale. Their moat is CN data
   depth (five adapters incl. qmt, consistency checker, sync workers). They have
   **no settlement discipline** — no verdict grading, no track-record loop —
   which confirms our identity rather than threatening it. Their license is
   hybrid (core/app/frontend proprietary): clean-room only; the Apache-licensed
   `tradingagents/` layer may be referenced with attribution.

Standing calibration: **1,967 weekly downloads (family #1) vs 0 stars** —
conversion remains the true bottleneck, but posting is owner-gated; the
engineering window fills with the highest-adoption-value autonomous work,
which is CN parity (the DSH user base is CN-centric; the pain is proven).

## S6.0 · CN parity (2026-11-25 → 12-03) — the A-share card equals the US card

Order by leverage (matches the audit):

1. **CN rich card wiring** — fundamentals (valuation + growth from free
   endpoints), industry classification, and news via EastMoney/Sina direct
   endpoints (2026-11-24 outage archaeology proved both reachable from this
   host; akshare stays an optional convenience, never a hard dependency).
   Every line sourced and dated; the evidence-tag covenant unchanged.
2. **A-share microstructure injection** — when `market == cn`, one prompt
   block enters the risk-officer and PM payloads: T+1 settlement, limit bands
   (±10% main board, ±20% ChiNext/STAR, ±30% BSE, 5% ST), stamp duty on sells,
   suspension risk. Guardrails ([G#]) must respect these constraints.
3. **CN settle channel #2** — sina/eastmoney CN kline endpoints behind tencent
   in `closes_for` (mirror of the US rebuild; the 06:30 DNS flakiness is the
   live failure mode this covers).
4. **as-of CN** — tencent/sina fqkline honor start/end; truncate bars/
   technicals at the date; fundamentals cut by report period. This unblocks
   CN backtest grids and fixes the docstring/behavior mismatch honestly.
5. **Ticker entry unification** — `sh`/`sz` prefixes accepted everywhere
   fetch paths are; BSE (`bj`) either verified live or refused with an explicit
   message (never a silent wrong-market fetch).

## S6.1 · Settlement compounding (2026-11-25 → 12-10, ride the cron)

- Watch the 4 pending windows settle; export a track-record snapshot per
  settle batch (`ledger.py --report` → `docs/track-record/<date>.md`).
- At n ≥ 5 settled: reflection quality review — if lessons read generic,
  tighten the reflect prompt (lessons must cite the memo's own tags).
- Verify one live **[T#] re-injection**: the next real session's PM payload
  must carry the settled lessons block — the loop's full circuit, observed.

## S6.2 · Conversion residue (posting stays owner-gated; drafting is not)

- First-blood post from real settlement data — the draft exists, data slots
  fill from the track-record page; **posting resumes on owner's call**
  (standing deferral 2026-11-22).
- Day-7 channel conversion review 2026-11-29 (gap-radar star board +
  downloads→stars funnel; honest read of how much of the 231/day is real).

## S6.3 · CN evidence expansion (2026-12-03 → 12-10, stretch — cut without guilt)

- **Chip distribution (筹码分布)** computed in-card from daily OHLCV — the one
  CN-native evidence type no US-native tool carries; derived evidence, tagged
  [A#], no new data source required.
- Northbound flow / margin balance only if a free reliable endpoint exists;
   otherwise honest absence (the [A8] pattern).

## S6.4 · Release train

- **0.4.0** = CN parity + settle-channel hardening. Owner real-terminal
  publish (browser auth flow); tarball pack + smoke checklist per the
  six-surface discipline (every face runs before tag).

## Non-goals (reaffirmed + new for S6)

- **No web app.** The 33k★ fork is FastAPI+Vue3+MongoDB+Redis for humans; we
  are agent-native and headless. Their species choice is validated — for them.
- **No new committee roles for CN.** Chip distribution enters as evidence in
  the card, not as a new agent seat; the 6-role pipeline is the auditability
  selling point.
- IC-MEMO ecosystem push stays deferred until adoption evidence (owner ruling
  2026-11-23 — "标准话语权来自采用").
- No code borrowing from TradingAgents-CN's proprietary layers (hybrid
  license); thinking only, and the Apache layer with attribution if ever.
- All standing non-goals from ROADMAP.md (no LangGraph, no agentic loops, no
  TUI, no separate Trader role, no risk-layer debate-ification) unchanged.

## Definition of done for S6

- [ ] CN card carries fundamentals + industry + news with sources; the
      microstructure block is live in risk/PM payloads on `market == cn`
- [ ] CN settle has ≥2 channels; one CN as-of backtest grid ran end to end
      into an isolated ledger
- [ ] ≥5 real settlements in the track record; one live [T#] re-injection
      observed in a real session
- [ ] 0.4.0 on npm

## S7 preview (not committed)

TS SDK + community persona-pack SDK (issue #24 remainder); upstream watch:
Trading-R1's trajectory; revisit `--agentic` only per the standing exception.
