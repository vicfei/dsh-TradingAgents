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
