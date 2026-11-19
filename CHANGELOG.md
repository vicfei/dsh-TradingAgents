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
