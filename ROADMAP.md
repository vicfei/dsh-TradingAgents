# ROADMAP — dsh-tradingagents (replanned 2026-11-17)

North star: **top-20 DSH plugin within 30 days (≈150–300★), aiming for 1000★**
(reference: dsh-code 1001★ community #1; dsh-trading 42★; jevcore 105★).

**Window assessment (2026-11-17):** the upstream Tauric repo has entered a polishing
phase (0.7.1 is all fixes; Trading-R1 in early access splits their focus) — the window
for claiming the DSH-native slot is open. Diagnosis: **the M0.5 launch battle was never
executed** (engineering jumped M0 → M1) while the north star is stars and distribution
ran at zero. Replanning principle: **distribution first, then the moat, then ecosystem.**
Work is tracked in GitHub issues/milestones (R1–R4); development proceeds by
issue → branch → PR.

## Shipped baseline (history)

- **M0 engine** (2026-11-16): 6-role committee + evidence tags + PASS-first verdicts +
  IC-MEMO v0.1 + offline DEMO (PASS@55)
- **WP1 data** (2026-11-16): fetch_card 3-tier ladder (yfinance → Tencent → SG relay)
- **M1 main line** (2026-11-17): OpenBB rich cards (CBOE quote/K-line/IV30 + SEC 10-K +
  nasdaq news, zero-key, Yahoo-free; NVDA PASS@72); four-master guest seats (DEMO split
  verdict); npm 0.1.0 distribution-vehicle bundle; CI green badge
- **Reverse-engineering archive:** `docs/upstream-architecture.md`,
  `docs/upstream-features.md` — the basis of this replan
- **English-first conversion** (2026-11-17, owner directive, issue #1): engine
  output/memos/cards default to English (`--lang zh` fallback); README/SKILL/ROADMAP/
  templates in English; demo assets regenerated from an English run

## R1 · Launch battle (this week, 11-17 → 11-21) — turn engineering into stars

> The one blocker was owner action and is done: npm publish (OTP manual,
> guide `docs/PUBLISH-0.1.0.md`).

- [x] **npm 0.1.0 published** (owner OTP 2026-11-17) → registry latest=0.1.0; fresh
      `npm i -g` → `tradingagents demo` 31s full committee smoke
- [x] npm 0.1.1 (English engine) and **0.1.2** (R2: verdict ledger + six-value
      vocabulary) published same day; 0.1.2 fresh-install smoke caught the
      settle-in-fresh-cwd crash, fixed in PR #15 (rides in 0.1.3)
- [x] Demo assets (2026-11-17): assets/demo.png terminal card (real 0.1.0 run data;
      visually accepted) on the README first screen + assets/demo.cast replayable;
      asciinema.org anonymous uploads are dead (302 login), animated version needs an
      owner account — English version shipped with #1
- [x] README comparison table: "Model calls dozens (tool loops × debates)" +
      "zero-key Yahoo-free market data" rows
- [x] Marketplace entry verified (2026-11-17): the real gate is
      awesome-dsh-plugin/awesome-dsh-plugin (24.9k★, one-file submission under
      data/plugins/) → dsh-market (12.7k★) auto-aggregates; submission drafted
      (docs/marketplace-submission/, monorepo subpackage format); **`dsh plugin add
      dsh-tradingagents` install verified** (0.2.2-rc.1, 803ms) — external PR awaits
      owner gate
- [x] Launch post copy v1 (docs/launch-post.md EN+CN + channel checklist) — external
      posting gated on owner review
- [ ] Channel checklist execution: awesome-dsh PR (awaiting owner) → X / V2EX / Juejin /
      Jike posts (copy awaiting owner) / Discord; Trendshift badge (needs baseline stars)
- [ ] Star dashboard: the gap-radar family download board auto-discovers 0.1.0 (no
      action needed) + daily star log; channel-conversion review on day 7
- [ ] super-agent listing: bundle form is ready; listing inside @vicfei/dsh-super-agent
      is the sibling window's asset — owner/that window executes

## R2 · Track-record loop (11-22 → 11-28) — the committee learns its own scorecard

> Formerly M3, pulled forward. The upstream's deepest moat; borrow the thinking, not the
> code (Apache-2.0 clean-room). Our edge: the CBOE channel never gets Yahoo-throttled,
> and IC-MEMO is already the verdict archive format. Issues #2 #3.

- [x] Verdict ledger (2026-11-17): `scripts/ledger.py` — `[date|ticker|decision|confidence|pending]`
      over IC-MEMO archives (append-only + idempotent per ticker+day; --save auto-appends;
      synthetic DEMO entries recorded but never settled)
- [x] Settlement (2026-11-17): entry at the first close after the decision date, exit
      `holding` sessions later (default 5, env `TRADINGAGENTS_HOLDING_DAYS`), raw return +
      **alpha vs benchmark** asof-both-ends (US→SPY via CBOE, A-share→000001.SS via
      Tencent fqkline); never scores the live bar; unresolved windows stay pending;
      resolution_date recorded. Live-verified both markets (NVDA -2.87% vs SPY, 600519
      +2.46% vs SSE on backdated test entries; math unit-tested in CI)
- [x] Reflection (2026-11-17): one quick-LLM call, 2-4 sentences, window boundary stated
- [x] Re-injection (2026-11-17): PM payload carries same-ticker outcomes + cross-ticker
      lessons ([T#] citations) — only the PM reads them
- [x] `tradingagents settle` subcommand (2026-11-17): indexes memos then settles due
      entries (npm CLI; engine: `python3 scripts/ledger.py --settle`)
- [x] Verdict dual exit + five tiers (2026-11-17, PR #14): BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/
      SELL + PASS (first-class) + REVIEW sentinel — `resolve_verdict()` normalizes casing,
      rejects out-of-vocabulary or missing decisions to REVIEW (not a verdict, never
      silently PASS/Hold); memo renders a REVIEW banner; ledger records REVIEW entries
      but never settles or scores them; resolve_verdict unit-tested in CI; live run on
      the six-value vocabulary verified
- [ ] Content ammunition: first critical review post ("the committee's first track
      record") — settlement data is exclusive material

## R3 · Input & rendering (11-29 → 12-05) — visible quality

- [x] IC-MEMO single-page HTML render (2026-11-17, PR #17): `--html` / scripts/render_html.py —
      static single file, sidebar TOC, yaml block, tables, mobile/print CSS, zero external
      assets; renderer structure unit-tested in CI. Along the way it exposed and fixed two
      English-first leaks: the engine prompt now enforces output language, and the bundled
      DEMO data card was translated (synthetic numbers unchanged)
- [ ] `--portfolio` three-state input: held / flat / not-provided strictly distinct
      (issue #5)
- [ ] `--date` historical as-of mode: SEC filed-as-of semantics via the sec provider —
      precondition for the backtest grid (issue #6)
- [ ] Cost guard: llm() parses usage, memo footer reports calls/tokens, `--max-calls`
      hard cap (issue #7)
- [ ] `--rounds N` configurable debate rounds (default 1 keeps the cost profile)
      (issue #8)

## R4 · Ecosystem & portfolio committee (12-06 → 12-15) — the two wings of scale

- [ ] **Portfolio committee** (the original M2 headline, upstream has nothing like it):
      multi-ticker allocation debate + portfolio risk constraints (correlation/drawdown);
      IC-MEMO portfolio variant (issue #9)
- [ ] cordis typed-tools plugin module (0.2.0): real `dsh plugin add` registration,
      committee exposed as typed tools (issue #10)
- [ ] Backtest grid: iter_grid/run/summarize over (ticker, date) cells into an isolated
      ledger; public win-rate/alpha-bucket page — "self-proving credibility" made
      literal, and evergreen content (issue #11)
- [ ] IC-MEMO standalone spec repo + multi-language SDK (Python/TS) + community
      persona-pack SDK

## Explicit non-goals (nailed down at replan)

- No LangGraph/heavy-framework migration (the deterministic CLI is the selling point);
  no agentic tool loops (they dilute the "no numbers outside the data card" covenant —
  if ever done, as an opt-in `--agentic` mode whose data citations still become cards);
  no interactive TUI (DSH is headless by nature); no ChatGPT OAuth (the key is already
  there); no separate Trader role (the PM's size_hint covers it); no risk-layer
  debate-ification (the risk officer "sets guardrails and never decides" is the
  auditability selling point); no checkpoint resume (a 6-10-call pipeline is too short
  until proven otherwise)

## Discipline (non-negotiables)

- Evidence tags and the PASS verdict are the product's soul; no feature dilutes them;
- Real-data mode forbids model-invented numbers (nothing outside the data card);
  synthetic mode must be conspicuously marked;
- Ledger/settlement point-in-time discipline: entry at the first close after the
  decision date, never score the live bar, unresolved windows stay pending, resolved
  entries carry resolution_date;
- Backtests and sweeps always use an isolated ledger, never polluting the context live
  runs read back;
- A not-investment-advice footer on every IC-MEMO.

## Star strategy (unchanged, executed in R1)

1. **Name as traffic**: keep the full TradingAgents name for upstream search overflow;
   README credit + Not affiliated
2. **Keyword matrix**: topics tradingagents/ai-hedge-fund/deepseek-harness/dsh/
   multi-agent-trading/investment-committee/bull-bear/quant; bilingual description
3. **Comparison table opener**: a searcher sees the position in 10 seconds (the rea play)
4. **Zero-friction demo**: offline DEMO, zero keys, zero network, ~40s to a full
   IC-MEMO; PASS abstention + persona splits are the spread hooks
5. **Open-format positioning**: IC-MEMO as a standalone spec (the VIDEO.md play)
6. **Track record as content**: from R2 on, every settlement batch is exclusive
   publishing material
