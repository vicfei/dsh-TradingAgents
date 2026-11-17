#!/usr/bin/env python3
"""backtest — run the committee over a (ticker, date) grid, into an isolated ledger (issue #11, R4)

One run yields one decision, which cannot tell whether the system decides well.
This sweeps cells (ticker × as-of date): each cell fetches an as-of card
(--date), runs the committee, and archives into a **run-local memos dir with its
own ledger** — a sweep must never flood the ledger real sessions read back
(the isolation rule; same discipline as upstream). Settlement then grades every
cell whose holding window has traded: raw return + alpha vs benchmark.

Scope: this evaluates decision quality. It is not a portfolio simulator and
must not grow one. One model sampling per cell; text feeds are not archived;
figures are indicative, not repeatable — the report says so.

Usage:
  python3 scripts/backtest.py --tickers AAPL --start 2026-08-01 --end 2026-10-01 --every 14
  python3 scripts/backtest.py ... --report            # also write track-record.md (+ .html)
"""
import argparse, datetime as dt, itertools, json, os, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# What each decision claims will happen; Hold claims no direction, so nothing
# about alpha proves it right or wrong (same scoring discipline as upstream).
_DIRECTION = {"BUY": 1, "OVERWEIGHT": 1, "HOLD": 0, "UNDERWEIGHT": -1, "SELL": -1}


def iter_grid(start, end, every_n_days=1, today=None):
    """Analysis dates from start, never past today; a future date has no outcome."""
    today = today or dt.date.today().isoformat()
    if every_n_days < 1:
        raise ValueError("every_n_days must be >= 1")
    for label, s in (("start", start), ("end", end)):
        try:
            assert dt.date.fromisoformat(s).isoformat() == s
        except (ValueError, AssertionError):
            raise ValueError(f"{label} must be YYYY-MM-DD, got {s!r}")
    if end < start:
        raise ValueError(f"the grid ends before it starts: {end} < {start}")
    dates, cursor = [], dt.date.fromisoformat(start)
    last = min(dt.date.fromisoformat(end), dt.date.fromisoformat(today))
    while cursor <= last:
        dates.append(cursor.isoformat())
        cursor += dt.timedelta(days=every_n_days)
    return dates


def run_cell(ticker, date, run_dir, lang):
    """One (ticker, as-of date) cell: as-of card → committee → archived in the run ledger."""
    env = {**os.environ,
           "TRADINGAGENTS_MEMOS": os.path.join(run_dir, "memos"),
           "TRADINGAGENTS_LEDGER": os.path.join(run_dir, "memos", "ledger.json"),
           "TRADINGAGENTS_LANG": lang}
    card = os.path.join(run_dir, "cards", f"{ticker}-{date}.json")
    os.makedirs(os.path.dirname(card), exist_ok=True)
    fetch = subprocess.run([PY, os.path.join(KIT, "scripts", "fetch_card.py"),
                            "--ticker", ticker, "--date", date, "--out", card,
                            "--lang", lang], env=env, capture_output=True, text=True)
    if not os.path.exists(card):
        return f"card fetch failed: {(fetch.stderr or fetch.stdout)[-160:]}"
    r = subprocess.run([PY, os.path.join(KIT, "scripts", "tradingagents.py"),
                        "--ticker", ticker, "--data", card, "--save", "--lang", lang],
                       env=env, capture_output=True, text=True)
    return None if "IC-MEMO" in r.stdout else f"committee failed: {r.stderr[-160:]}"


def settle_run(run_dir, lang):
    env = {**os.environ,
           "TRADINGAGENTS_MEMOS": os.path.join(run_dir, "memos"),
           "TRADINGAGENTS_LEDGER": os.path.join(run_dir, "memos", "ledger.json"),
           "TRADINGAGENTS_LANG": lang}
    r = subprocess.run([PY, os.path.join(KIT, "scripts", "ledger.py"), "--settle"],
                       env=env, capture_output=True, text=True)
    return r.stdout


def summarize(ledger_path):
    """Grade settled decisions by verdict bucket; PASS/REVIEW are counted, not scored."""
    entries = json.load(open(ledger_path))["entries"] if os.path.exists(ledger_path) else []
    resolved = [e for e in entries if not e.get("pending") and not e.get("synthetic")
                and not e.get("review") and isinstance(e.get("alpha"), (int, float))]
    buckets = {}
    for e in resolved:
        b = buckets.setdefault(e["decision"], {"n": 0, "hits": 0, "directed": 0, "alpha_sum": 0.0})
        b["n"] += 1
        b["alpha_sum"] += e["alpha"]
        d = _DIRECTION.get(e["decision"], 0)
        if d:
            b["directed"] += 1
            b["hits"] += (e["alpha"] * d) > 0
    pending = sum(1 for e in entries if e.get("pending") and not e.get("synthetic") and not e.get("review"))
    unscored = sum(1 for e in entries if e.get("review"))
    passed = sum(1 for e in entries if e.get("decision") == "PASS")
    return {"buckets": {k: {"n": v["n"],
                            "hit_rate": round(v["hits"] / v["directed"], 3) if v["directed"] else None,
                            "mean_alpha": round(v["alpha_sum"] / v["n"], 4)}
                        for k, v in buckets.items()},
            "resolved": len(resolved), "pending": pending, "pass": passed, "review": unscored}


def render_report(run_dir, s, lang, every):
    lines = [f"# Track record — dsh-tradingagents (backtest run {os.path.basename(run_dir)})",
             "",
             f"Grid: every {every} day(s); holding window 5 trading sessions; entry at the first close after each decision date; alpha vs SPY (US) / SSE Composite (A-shares).",
             "",
             "| Decision | n | direction hit-rate | mean alpha |",
             "|---|---|---|---|"]
    for d in ("BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL"):
        b = s["buckets"].get(d)
        if b:
            hit = f"{b['hit_rate']:.0%}" if b["hit_rate"] is not None else "no direction claimed"
            lines.append(f"| {d} | {b['n']} | {hit} | {b['mean_alpha']:+.1%} |")
    lines += ["", f"Resolved {s['resolved']} · PASS {s['pass']} (no direction, not scored) · "
              f"REVIEW {s['review']} (unreadable, not scored) · pending {s['pending']}.",
              "", "> One model sampling per cell; text feeds are not archived. These figures "
              "are indicative, not repeatable. Not investment advice."]
    md = os.path.join(run_dir, "track-record.md")
    open(md, "w", encoding="utf-8").write("\n".join(lines))
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True, help="comma-separated")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--every", type=int, default=7)
    ap.add_argument("--lang", choices=("en", "zh"), default=os.environ.get("TRADINGAGENTS_LANG") or "en")
    ap.add_argument("--report", action="store_true", help="write track-record.md (+ .html)")
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    dates = iter_grid(args.start, args.end, args.every)
    run_dir = os.path.join(os.getcwd(), "backtest", dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)
    print(f"run dir: {run_dir} · {len(tickers)} ticker(s) × {len(dates)} date(s) = {len(tickers)*len(dates)} cells")

    failures = []
    for i, (t_, d_) in enumerate(itertools.product(tickers, dates), 1):
        print(f"[{i}/{len(tickers)*len(dates)}] {t_} @ {d_} ...", flush=True)
        err = run_cell(t_, d_, run_dir, args.lang)
        if err:
            failures.append((t_, d_, err))
            print(f"  ✗ {err}", file=sys.stderr)
    print(settle_run(run_dir, args.lang).strip() or "settle: nothing due")

    s = summarize(os.path.join(run_dir, "memos", "ledger.json"))
    print(json.dumps(s, indent=1))
    for t_, d_, err in failures:
        print(f"FAILED {t_} {d_}: {err}", file=sys.stderr)
    if args.report:
        md = render_report(run_dir, s, args.lang, args.every)
        print(f"report → {md}")
        try:
            sys.path.insert(0, os.path.join(KIT, "scripts"))
            import render_html
            hp = md[:-3] + ".html"
            open(hp, "w", encoding="utf-8").write(render_html.render(open(md).read()))
            print(f"report → {hp}")
        except Exception as e:
            print(f"⚠ html report skipped ({type(e).__name__})", file=sys.stderr)


if __name__ == "__main__":
    main()
