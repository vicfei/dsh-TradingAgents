# S5 plan — first blood & the format play (2026-11-22 → 2026-12-06)

> Status snapshot taken 2026-11-22 (repo main @ 993dd86). Builds on the
> S-tracks (S1 #32 / S3 #34 / S4 #35); R1-R4 remain fully shipped. Absolute
> dates throughout (discipline: clock-source).

## Where we actually stand (2026-11-22)

- **Distribution**: npm 0.3.0 live; **weekly downloads 1,594 = family #1**
  (gap-radar board). Upstream **awesome-dsh-plugin PR #16227 MERGED** —
  the repo is in the 24.9k★ catalog. Star conversion still unmeasured
  (star dashboard open).
- **Loop**: daily settle cron live (06:30) — but **bleeding**: all 6
  ledger entries pending; settle log shows DNS-failure skips
  (2026-11-20: NVDA/AAPL/sh600519 skipped on name-resolution failure)
  followed by "nothing due for settlement" ever since. Manual run today
  reproduces it: 6/6 pending, nothing due → **skip entries are not being
  retried and/or due-window detection is off** (PR #40 fixed prefixed-ticker
  routing; this is the layer beneath it).
- **First real track record**: the ledger's first directed call
  (sh600519 OVERWEIGHT 2026-11-19, the 0.2.1 live-session verdict) plus
  NVDA×2 PASS / 600519 PASS / AAPL HOLD are ALL waiting on the settle bug.
- **S-tracks**: S4-a (family bridge: vibe-trading trails → committee)
  shipped in 0.3.0; S1 (#32) blocked by the settle bug; S3 (#34) owner-gated,
  content depends on S1's data; #35's option A is done, C is mostly done
  (cron) modulo the repair.

## S5.0 · Settle integrity repair (2026-11-22 → 11-24) — stop the bleeding first

1. **Bug**: reproduce why due entries report "nothing due" — audit the
   skip path in `scripts/ledger.py --settle` (a DNS-skipped entry must
   remain pending-eligible forever, never age out of the due window; the
   06:30 cron hits pre-network DNS gaps — retry discipline, not skip).
2. **Fix + tests**: hermetic unit tests for due-window computation and
   skip-retry semantics (fixture clock, fixture network failure); CI gate.
3. **Cron hardening**: settle retries transient URLError with backoff
   in-run (×3); cron line keeps the pending-retry contract documented.
4. **Unblock**: settle all 6 entries on a working network window (manual
   run after fix); sh600519 exercises the PR #40 prefixed-ticker routing
   for real; synthetic DEMO settles marked, never mixed.
5. **Output**: first real track-record snapshot (memo + html) → the S3
   content base. Closes #32.

## S5.1 · Content & conversion (2026-11-24 → 11-28, owner-gated where marked)

- Draft post #1 from real settlement data ("the committee's first track
  record" — exclusive material; use the S3 kit, EN first + zh mirror).
- Star dashboard goes live (gap-radar board already counts downloads;
  add daily star snapshot + day-7 channel-conversion review, 2026-11-29).
- Owner actions: post via S3 channel checklist; Trendshift badge once
  baseline stars exist.

## S5.2 · R5 = IC-MEMO open format (#35 pick = B, #24) — 2026-11-26 → 12-06

Decision rationale recorded on #35: A shipped (S4-a), C is absorbed by
S5.0 (cron + repair = standing feature), B is the ecosystem big-rock —
and it is now **de-risked by family precedent**:

- **The play is proven**: format-anything's FORMAT.md (2026-11-22) executed
  exactly this spec-repo pattern — independent spec doc, versioned, verdict
  scale, machine blocks; IC-MEMO gets the same shape (v0.2 spec: yaml
  header, evidence tags [A#]/[G#]/[T#], verdict vocabulary, footers).
- **The render surface is live**: dsh-uigen 0.1.0 + genui render inline
  components in DSH replies; an IC-MEMO → dsh-ui projection makes every
  memo readable inside the host that already carries the committee (the
  two repos' ROADMAPs both reserved this interface).
- Scope (one repo, issue→PR): `ic-memo` spec repo (SPEC.md + examples +
  this repo's renderer adopted as reference implementation) → Python SDK
  (emit/parse/validate; the committee itself is the first consumer) →
  TS SDK + persona-pack SDK deferred to v0.2 of the spec repo.

## S5.3 · Family-synergy quick wins (ride along, 2026-11-26 → 12-06)

- `ui_compose`-validated dsh-ui card for the IC-MEMO summary block
  (committee verdict + confidence + top evidence tags, rendered inline by
  dsh-genui) — demo in this repo's README once the SDK lands.
- Backtest grid output → optional genui table/chart projection (same tool).

## Non-goals & discipline

Unchanged from ROADMAP (no LangGraph / no agentic loops / point-in-time
settlement / isolated sweep ledgers / not-investment-advice footer on
every memo). New items inherit: evidence tags and PASS are the soul; the
track record publishes ONLY settled, resolution-dated entries.

---

# S5 execution plan v2 (written 2026-11-22 22:52 CST)

> What changed since the morning plan: S5.0 shipped (PR #42) — the settle
> unblock is on autopilot; the uigen×genui render loop closed live (S5.3's
> render surface is proven); the FORMAT.md spec-site pattern shipped
> (S5.2's play has a family template). New fact that reshapes priorities:
> **npm weekly 1,736 (family #1, growing) but stars = 0** — the conversion
> gap is now the top lever, and content is the star machine.

## Immediate · Settlement watch (2026-11-23 → 11-28, low-touch)

The 06:30 cron settles on autopilot. On the first REAL settle landing
(600519 due 2026-11-24; sh600519 due 2026-11-27; US entries on the first
healthy channel day):

1. run `scripts/backtest.py --report`-style snapshot export (or a small
   `ledger.py --report` addition) → `docs/track-record/2026-11.md`;
2. close #32 with the settled numbers;
3. cut the S5.1 post draft from the real data (see below).

## S5.1 · Content & conversion (drafting can start 2026-11-23; data slots fill at settlement)

**The star machine — three pieces, gated only on data + owner posting:**

- **Post #1 — "the committee's first track record"** (EN first + zh
  mirror, the S3 kit): the narrative is honesty — PASS abstentions
  included, alpha vs benchmark, the settle loop's point-in-time
  discipline; exclusive material nobody else has.
- **Post #2 — "what 1,700 weekly installs and zero stars taught us"**
  (or fold into #1): the README comparison table + demo.cast replay are
  the hooks; target channels per the S3 checklist (X/V2EX/Juejin/Jike —
  owner accounts).
- **Star dashboard**: gap-radar gains a daily star snapshot column
  (script + the day-7 channel-conversion review lands 2026-11-29 — two
  days after the awesome catalog entry went live with real downloads).

## S5.2 · IC-MEMO open format — `ic-memo` repo (2026-11-26 → 12-06, now fully de-risked)

Family-proven template: format-anything's FORMAT.md (spec doc → gh-pages
single-page site → SDK follows). Concrete breakdown:

1. **PR1 spec**: `vicfei/ic-memo` — SPEC v0.2 extracted from what the
   committee already emits (yaml header, five-value verdict vocabulary +
   PASS + REVIEW sentinel, evidence tags [A#]/[G#]/[T#], portfolio
   variant, not-investment-advice footer, cost footer) + 3 example memos
   (real NVDA/AAPL/sh600519 from this repo's memos/) + gh-pages site.
2. **PR2 Python SDK**: `ic_memo` — emit/parse/validate; the committee
   (this repo) adopts it as first consumer (its memo writer swaps to the
   SDK; round-trip tests in CI); ledger interop (index any IC-MEMO
   directory into pending entries).
3. **PR3 = old S5.3 (genui card)**: `ic_memo.render.dsh_ui()` — verdict +
   confidence + top evidence tags as a ui_compose-linted ```dsh-ui
   summary card (the uigen×genui loop is live-proven; demo in README).
4. Release train: this repo's 0.3.1 (the settle fix rides to npm — owner
   real-terminal publish) and ic-memo 0.1.0 (SDK).

## S6 preview (beyond 12-06 — not committed yet)

TS SDK + community persona-pack SDK (issue #24 remainder); upstream
watch: Trading-R1's early-access trajectory and whether Tauric's polish
phase opens the DSH-native slot further; possible `--agentic` opt-in
per the standing non-goal exception.

## Definition of done for S5

- [ ] first real settlement landed + #32 closed + track-record exported
- [ ] two posts out (owner-gated) + star dashboard live + day-7 review done
- [ ] ic-memo repo: SPEC + site + Python SDK adopted in-repo + genui card
- [ ] 0.3.1 on npm (settle fix live for users)

---

# S5 amendment v3 (owner ruling, 2026-11-23)

**"标准的话语权来自采用"** — the ic-memo standalone spec-repo play is
**cancelled and folded back**: the spec now lives at
[docs/ic-memo/](ic-memo/) as the committee's internal format documentation
(the former vicfei/ic-memo repo is archived; the npm name stays squatted).
S5.2 is rescoped:

- WAS: ic-memo repo + Python SDK + multi-language ecosystem play.
- NOW: **in-repo schema discipline** — a memo validator (parse + verdict
  vocabulary + tag integrity) as a CI gate on this repo's own memos; the
  open-format/ecosystem push is deferred **until adoption evidence exists**
  (stars/community uptake — the S5.1 content track is the path that earns
  the voice; posting was deferred 2026-11-22 and resumes on owner's call).
- The dsh-ui verdict card (old S5.3) remains valid in-repo work (rendering
  our own memos inline via dsh-uigen) — it is product surface, not
  standard-setting.
