#!/usr/bin/env python3
"""Family bridge (S4-A): dsh-vibe-trading research trail → committee data card

A vibe-trading trail (schema research-trail/1) carries a deterministic
computed layer over real market data — exactly what the committee's covenant
allows as evidence ("nothing outside the data card"). This converter reshapes
a trail into the committee card format:

- stats/backtests → `technicals` (numbers stay the computed layer's own)
- source metadata → `_source` (provenance rides)
- the trail's findings → `research_note`, **conspicuously marked as prior LLM
  interpretation — context, not data** (the committee may read it, but cites
  numbers only from the computed fields)

Usage:
  python3 scripts/from_trail.py --trail trail.json [--symbol sh600519] [--out card.json]
  # or implicitly: tradingagents.py --data trail.json --ticker sh600519  (auto-detected)
"""
import argparse, json, sys

TRAIL_SCHEMA = "research-trail/1"


def is_trail(obj):
    return isinstance(obj, dict) and obj.get("schema") == TRAIL_SCHEMA


def _val(v):
    """pass numbers through; render unavailable-dicts as null+reason"""
    if isinstance(v, dict) and "unavailable" in v:
        return None
    return v


def convert(trail, symbol=None):
    stats = trail.get("stats", {})
    if not stats:
        sys.exit("refused honestly — the trail carries no stats block")
    sym = symbol or next(iter(stats))
    if sym not in stats:
        sys.exit(f"refused honestly — symbol {sym} not in the trail (has: {', '.join(list(stats)[:6])})")
    st = stats[sym]
    bt = (trail.get("backtests") or {}).get(sym, {})
    meta = (trail.get("datasets") or {}).get(sym, {})
    tech = {k: _val(st.get(k)) for k in
            ("last", "ret20", "ret60", "vol30", "dd_from_120d_peak", "vol_z20",
             "rsi14", "macd_hist", "above_sma60")}
    tech["above_sma60"] = _val(st.get("above_sma60"))
    if bt:
        tech["sma_cross_backtest"] = {
            "trades": bt.get("trades"), "sum_strategy": bt.get("sum_strategy"),
            "train": bt.get("train"), "holdout": bt.get("holdout"),
            "oos_note": bt.get("oos_note")}
    unavailable = {k: v["unavailable"] for k, v in
                   {k: st.get(k) for k in tech if isinstance(st.get(k), dict)}.items()
                   if isinstance(v, dict) and "unavailable" in v}
    card = {
        "ticker": sym,
        "as_of": (meta.get("date_range") or ["?"])[-1],
        "price": _val(st.get("last")),
        "technicals": tech,
        "fundamentals": {"note": "not carried by a vibe-trading trail — fundamentals "
                                 "require fetch_card.py (OpenBB rich card)"},
        "news": [],
        "research_note": {
            "origin": "dsh-vibe-trading research trail (family bridge S4-A)",
            "question": trail.get("question", ""),
            "status": "PRIOR LLM INTERPRETATION — context only, never data; "
                      "numbers must be cited from the technicals block above",
            "findings": trail.get("findings", ""),
            "plan": (trail.get("plan") or {}).get("plan", "")},
        "unavailable_fields": unavailable,
        "_source": {
            "origin": "dsh-vibe-trading research trail",
            "schema": TRAIL_SCHEMA,
            "data_source": meta.get("source", "?"),
            "adjustment": meta.get("adjustment", "?"),
            "date_range": meta.get("date_range", ["?", "?"]),
            "bars": meta.get("bars"),
            "coverage_gaps": meta.get("coverage_gaps", []),
            "board": trail.get("board", ""),
        },
    }
    return card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trail", required=True)
    ap.add_argument("--symbol")
    ap.add_argument("--out")
    args = ap.parse_args()
    trail = json.load(open(args.trail))
    if not is_trail(trail):
        sys.exit(f"refused honestly — not a research-trail/1 document (schema={trail.get('schema')!r})")
    card = convert(trail, args.symbol)
    if args.out:
        json.dump(card, open(args.out, "w"), ensure_ascii=False, indent=1)
        print(f"→ {args.out}", file=sys.stderr)
    else:
        print(json.dumps(card, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
