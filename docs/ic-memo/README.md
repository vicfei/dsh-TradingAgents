# IC-MEMO — the committee's memo format (internal schema)

> **Position (owner ruling 2026-11-23)**: this is the **internal format
> documentation of dsh-TradingAgents** — the single source of truth for
> what the committee emits and what validators enforce. The standalone
> spec-repo play (ic-memo as an ecosystem standard with multi-language
> SDKs) is **deferred until adoption evidence exists**: the right to set
> a standard comes from adoption, not from writing one. The former
> vicfei/ic-memo repo is archived; its spec site remains readable at
> <https://vicfei.github.io/ic-memo/>.

- **SPEC v0.2**: [SPEC.md](SPEC.md) — extracted from production memos
  (2026-11-16 → 11-22), not invented.
- **Examples**: the live memos themselves —
  [memos/NVDA-2026-11-13.md](../../memos/NVDA-2026-11-13.md) (PASS @78,
  abstention with full reasoning), [memos/sh600519-2026-11-19.md](../../memos/sh600519-2026-11-19.md)
  (OVERWEIGHT — first directed call), [memos/DEMO-2026-11-16-guests.md](../../memos/DEMO-2026-11-16-guests.md)
  (synthetic, marked).
- **Validator scope** (planned, in-repo CI): parse the yaml head, check
  the closed verdict vocabulary (normalize casing; out-of-vocabulary →
  REVIEW), validate tag uniqueness/citation integrity. No external-SDK
  ambitions until the product earns gravity.

- **Validator (shipped 2026-11-23)**: `scripts/validate_memo.py` — runs on
  the real archive in CI (`--all`); parses the yaml head, enforces the
  closed verdict vocabulary, checks role-tag presence and the footer
  contract. First run validated all 7 archived memos GREEN.
