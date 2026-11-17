#!/usr/bin/env python3
"""ledger — the verdict track-record layer (issue #2, R2)

The IC-MEMO archive is already the verdict store; this module makes it *compound*:

  append   --save already appends every archived memo as a pending ledger entry
             ([ticker|date|decision|confidence|pending], idempotent per ticker+date)
  settle   once the holding window (default 5 trading days) has fully traded:
             entry at the FIRST close after the decision date, exit at the close
             `holding` sessions later, raw return + alpha vs the market benchmark
             (US->SPY via CBOE, A-share->000001.SS via Tencent). Never scores a
             bar that is still trading; unresolved windows stay pending. One quick
             LLM call turns the outcome into a 2-4 sentence lesson (window boundary
             stated). Point-in-time discipline per ROADMAP.
  context  renders the PM's track-record block: same-ticker prior outcomes +
           recent cross-ticker lessons (only the PM ever reads this)

Ledger file: env TRADINGAGENTS_LEDGER, else <repo>/memos/ledger.json (local artifact).
Synthetic DEMO entries are recorded but never settled.

Usage:
  python3 scripts/ledger.py --index            # rebuild from memos/*.md
  python3 scripts/ledger.py --settle           # settle due pending entries
  python3 scripts/ledger.py --context NVDA     # print the PM track-record block
"""
import argparse, datetime as dt, json, os, re, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.environ.get("TRADINGAGENTS_LEDGER") or os.path.join(KIT, "memos", "ledger.json")
MEMOS = os.environ.get("TRADINGAGENTS_MEMOS") or os.path.join(KIT, "memos")
LANG = os.environ.get("TRADINGAGENTS_LANG") or "en"
HOLDING_DAYS = int(os.environ.get("TRADINGAGENTS_HOLDING_DAYS") or "5")

BENCHMARKS = {"us": "SPY", "cn": "000001.SS"}  # A-share benchmark = SSE Composite


def tt(en, zh):
    return en if LANG == "en" else zh


# ── ledger store ────────────────────────────────────────────────────────────

def load():
    return json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"entries": []}


def save(ledger):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(ledger, open(LEDGER, "w"), ensure_ascii=False, indent=1)


def memo_head(path):
    """Pull the yaml-head facts out of an archived IC-MEMO."""
    head = open(path, encoding="utf-8").read().split("```yaml", 1)
    if len(head) < 2:
        return None
    y = head[1].split("```", 1)[0]
    g = lambda k: (re.search(rf"^{k}:\s*(.+)$", y, re.M) or [None, None])[1]
    if not (g("ticker") and g("decision")):
        return None
    return {"ticker": g("ticker").strip(), "date": (g("as_of") or "?").strip(),
            "decision": g("decision").strip(), "confidence": g("confidence"),
            "committee": (g("committee") or "?").strip(), "memo": os.path.basename(path)}


def index(rebuild=False):
    """(Re)index archived memos into pending entries; idempotent per (ticker, date)."""
    ledger = {"entries": []} if rebuild else load()
    known = {(e["ticker"], e["date"]) for e in ledger["entries"]}
    for p in sorted(os.listdir(MEMOS)):
        if not p.endswith(".md") or p == "ledger.json":
            continue
        h = memo_head(os.path.join(MEMOS, p))
        if not h or (h["ticker"], h["date"]) in known:
            continue
        h.update({"pending": True, "synthetic": h["ticker"] == "DEMO",
                  "review": h["decision"].upper() == "REVIEW",  # not a verdict — kept on record, never settled
                  "added_at": dt.datetime.now().isoformat(timespec="seconds")})
        ledger["entries"].append(h)
        known.add((h["ticker"], h["date"]))
    save(ledger)
    return ledger


# ── price fetchers (lazy imports; stdlib-only at module level) ─────────────

def _closes_openbb(symbol, start, end):
    from openbb import obb
    df = obb.equity.price.historical(symbol, provider="cboe", start_date=start, end_date=end).to_df()
    return {str(i)[:10]: float(c) for i, c in zip(df.index, df["close"])}


def _closes_tencent(symbol, start, end):
    import urllib.request
    sym = symbol if not symbol.isdigit() else ("sh" if symbol.startswith(("6", "5")) else "sz") + symbol
    sym = {"000001.SS": "sh000001", "399001.SZ": "sz399001"}.get(symbol, sym)  # index aliases
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{start},{end},320,qfq"
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read()
    data = json.loads(raw)["data"][sym]
    days = data.get("qfqday") or data.get("day") or data.get("kline") or []
    return {d[0][:10].replace("/", "-"): float(d[2]) for d in days}


def closes_for(ticker, start, end):
    market = "cn" if ticker.isdigit() else "us"
    sym = ticker if market == "us" else ticker
    try:
        return _closes_openbb(sym, start, end), market
    except Exception:
        return _closes_tencent(sym, start, end), market


def settle_return(stock, bench, decision_date, holding=HOLDING_DAYS, today=None):
    """Pure settlement math. Entry = first close STRICTLY after the decision date;
    exit = `holding` sessions later. Returns None while the window has not fully
    traded (exit bar missing, or exit bar is today's live session)."""
    today = today or dt.date.today().isoformat()
    sessions = sorted(d for d in stock if d > decision_date)
    if len(sessions) <= holding:
        return None
    entry_d, exit_d = sessions[0], sessions[holding]
    if exit_d >= today:  # today's bar may still be trading — never score it
        return None
    entry, exit_ = stock[entry_d], stock[exit_d]
    b_sorted = sorted(bench)
    if b_sorted[-1] < exit_d:  # benchmark must have traded through the exit
        return None
    b_entry = bench[max(d for d in b_sorted if d <= entry_d)]   # asof(entry)
    b_exit = bench[min(d for d in b_sorted if d >= exit_d)]     # first close at/after exit
    raw = exit_ / entry - 1
    alpha = raw - (b_exit / b_entry - 1)
    return {"raw_return": round(raw, 4), "alpha": round(alpha, 4),
            "entry_date": entry_d, "exit_date": exit_d, "resolution_date": exit_d}


# ── reflection (one quick-LLM call per settled entry) ───────────────────────

def _key():
    return subprocess.run(["bash", "-c", 'grep -m1 "^export DEEPSEEK_API_KEY=" ~/.bashrc | cut -d= -f2'],
                          capture_output=True, text=True).stdout.strip().strip('"')


def reflect(entry, memo_text):
    prompt = tt(
        "You are a trading analyst reviewing your own past decision now that the outcome is known.\n"
        f"The outcome covers {entry.get('holding_days', HOLDING_DAYS)} trading days from the first close after the decision date, which may be shorter than the horizon the decision was written for.\n"
        "Write exactly 2-4 sentences of plain prose (no bullets, no headers, no markdown).\n\n"
        "Cover in order:\n"
        f"1. What the {entry.get('holding_days', HOLDING_DAYS)}-day alpha shows about the directional call (cite the figure), and say so plainly if the window is too short to judge the thesis.\n"
        "2. Which part of the investment thesis this window supports or undercuts.\n"
        "3. One concrete lesson to apply to the next similar analysis.\n\n"
        "Be specific and terse. Your output will be stored verbatim in a verdict ledger and re-read by future committees, so every word must earn its place.",
        "你是交易分析师，正在复盘自己过去的决策——结果已知。\n"
        f"结果覆盖自决策日次一收盘起 {entry.get('holding_days', HOLDING_DAYS)} 个交易日，可能短于决策本意的持有周期。\n"
        "写恰好 2-4 句平实散文（不要列表/标题/markdown）：1) 这 {0} 日 alpha 对方向判断说明了什么（引用数字）；窗口太短不足以检验论点就直说。2) 这个窗口支持或削弱了论点的哪一部分。3) 一条用于下次同类分析的具体教训。".format(entry.get('holding_days', HOLDING_DAYS)))
    body = {"model": "deepseek-chat", "temperature": 0, "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": tt(
            f"Raw return over {entry.get('holding_days', HOLDING_DAYS)} trading days: {entry['raw_return']:+.1%}\n"
            f"Alpha vs {entry['benchmark']}: {entry['alpha']:+.1%}\n\nOriginal decision ({entry['decision']}@{entry['confidence']}):\n{memo_text[:2000]}",
            f"{entry.get('holding_days', HOLDING_DAYS)} 个交易日 raw return：{entry['raw_return']:+.1%}\n"
            f"相对 {entry['benchmark']} 的 alpha：{entry['alpha']:+.1%}\n\n原判决（{entry['decision']}@{entry['confidence']}）：\n{memo_text[:2000]}")}]}
    r = subprocess.run(["curl", "-s", "-m", "180", "https://api.deepseek.com/chat/completions",
                        "-H", f"Authorization: Bearer {_key()}", "-H", "Content-Type: application/json",
                        "-d", json.dumps(body)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except Exception:
        return tt("(reflection unavailable this pass)", "（本轮反思不可得）")


# ── settle / context ────────────────────────────────────────────────────────

def settle(only=None):
    ledger = load()
    settled, skipped = [], []
    for e in ledger["entries"]:
        if not e.get("pending") or e.get("synthetic") or e.get("review"):
            continue
        if only and e["ticker"] != only:
            continue
        d = e["date"]
        if not re.match(r"\d{4}-\d{2}-\d{2}", d):
            skipped.append((e["ticker"], d, "unparseable date"))
            continue
        start = (dt.date.fromisoformat(d) - dt.timedelta(days=10)).isoformat()
        end = (dt.date.fromisoformat(d) + dt.timedelta(days=round((HOLDING_DAYS + 1) * 7 / 5) + 10)).isoformat()
        try:
            stock, market = closes_for(e["ticker"], start, end)
            bench, _ = closes_for(BENCHMARKS[market], start, end)
            res = settle_return(stock, bench, d)
        except Exception as exc:
            skipped.append((e["ticker"], d, f"{type(exc).__name__}: {str(exc)[:60]}"))
            continue
        if res is None:
            continue  # window not fully traded yet — retry next pass
        e.update(res)
        e.update({"benchmark": BENCHMARKS[market], "holding_days": HOLDING_DAYS, "pending": False})
        try:
            memo_text = open(os.path.join(MEMOS, e["memo"]), encoding="utf-8").read()
            e["reflection"] = reflect(e, memo_text)
        except Exception:
            e["reflection"] = tt("(reflection unavailable this pass)", "（本轮反思不可得）")
        settled.append((e["ticker"], d, f"{e['alpha']:+.1%}"))
    save(ledger)
    return settled, skipped


def context_block(ticker, limit=5):
    """The PM's track-record payload: same-ticker outcomes first, then cross-ticker lessons."""
    entries = [e for e in load()["entries"]
               if not e.get("pending") and not e.get("synthetic") and not e.get("review")]
    if not entries:
        return ""
    same = [e for e in entries if e["ticker"] == ticker][-limit:]
    others = [e for e in entries if e["ticker"] != ticker][-limit:]
    def line(e):
        return (f"[{e['date']} | {e['ticker']} | {e['decision']}@{e['confidence']}] "
                f"over {e['holding_days']}d: raw {e['raw_return']:+.1%}, alpha {e['alpha']:+.1%} "
                f"vs {e['benchmark']} (resolved {e['resolution_date']}) — lesson: {e.get('reflection', '')}")
    parts = []
    if same:
        parts.append(tt("Prior outcomes on this ticker:\n", "本标的既往判决：\n") + "\n".join(line(e) for e in same))
    if others:
        parts.append(tt("Recent lessons from other tickers:\n", "其他标的近期教训：\n") + "\n".join(line(e) for e in others))
    return "\n\n".join(parts)


def main():
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", action="store_true", help="(re)index memos/*.md into pending entries")
    ap.add_argument("--settle", action="store_true", help="settle due pending entries (prices + reflection)")
    ap.add_argument("--context", help="print the PM track-record block for a ticker")
    ap.add_argument("--lang", choices=("en", "zh"), default=LANG)
    args = ap.parse_args()
    LANG = args.lang
    if args.index:
        n = len(index(rebuild=True)["entries"])
        print(tt(f"ledger indexed: {n} entries → {LEDGER}", f"台账重建：{n} 条 → {LEDGER}"))
    if args.settle:
        settled, skipped = settle()
        for t, d, a in settled:
            print(tt(f"settled {t} {d}: alpha {a}", f"已结算 {t} {d}: alpha {a}"))
        for t, d, r in skipped:
            print(tt(f"skipped {t} {d}: {r}", f"跳过 {t} {d}: {r}"), file=sys.stderr)
        if not settled:
            print(tt("nothing due for settlement", "没有到期待结算条目"))
    if args.context:
        print(context_block(args.context))


if __name__ == "__main__":
    main()
