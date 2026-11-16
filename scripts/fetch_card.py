#!/usr/bin/env python3
"""fetch_card — 真实行情数据卡取数器（WP1）

产出与 data/demo/DEMO.json 同构的数据卡（议院引擎直接消费）。
证据纪律的数据端落地：每条数据带来源与日期；缺什么就少什么，
不编造、不外推。市场自动识别：纯数字代码 → A股(akshare)，否则美股(yfinance)。

用法：
  python3 scripts/fetch_card.py --ticker NVDA            # 美股 → cards/NVDA.json
  python3 scripts/fetch_card.py --ticker 600519          # A股 → cards/600519.json
  python3 scripts/fetch_card.py --ticker NVDA --committee  # 取卡后直接开庭
"""
import argparse, datetime as dt, json, math, os, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(KIT, "cards")


def pct(x):
    return f"{x * 100:+.1f}%" if x is not None and not (isinstance(x, float) and math.isnan(x)) else None


def fetch_us_tencent(ticker):
    """Tier2（国内直连）：腾讯美股报价 + K 线技术面，基本面精简但真实。"""
    import re as _re, urllib.request
    def get(url):
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read()
    q = get(f"https://qt.gtimg.cn/q=us{ticker}").decode("gbk", "ignore")
    f = q.split("~")
    def to_f(i):
        try:
            v = float(f[i])
            return v if v == v else None
        except (ValueError, IndexError):
            return None
    if not _re.match(r"[\d.]+$", (f[3] if len(f) > 3 else "") or ""):
        raise SystemExit(f"腾讯报价解析失败: {q[:80]}")
    price = to_f(3)
    chg_pct = to_f(32) or 0.0
    pe, mcap_b = to_f(39), (to_f(44) or 0) / 100  # 44=总市值（亿美元）
    as_of = f[30][:10]
    k = json.loads(get(f"https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?param=us{ticker}.OQ,day,,,320,qfq").decode())
    days = k["data"][f"us{ticker}.OQ"]["qfqday"]
    closes = [float(d[2]) for d in days]
    sma60 = sum(closes[-60:]) / 60
    mom20 = closes[-1] / closes[-21] - 1
    vol30 = (sum((closes[i] / closes[i - 1] - 1) ** 2 for i in range(-30, 0)) / 30) ** 0.5 * (252 ** 0.5)
    hi52, lo52 = max(closes[-252:]), min(closes[-252:])
    pos52 = (closes[-1] - lo52) / (hi52 - lo52)
    fundamentals = [f"现价 {price} USD（日内 {chg_pct:+.2f}%） — 来源：腾讯美股行情（截至 {as_of}）"]
    if mcap_b > 0 and pe:
        fundamentals.append(f"总市值约 ${mcap_b:.1f}B、滚动市盈率约 {pe:.1f} 倍 — 来源：同上")
    elif mcap_b > 0:
        fundamentals.append(f"总市值约 ${mcap_b:.1f}B — 来源：同上")
    fundamentals.append(f"52 周区间 {lo52:.2f}–{hi52:.2f}，现价处于 {pos52:.0%} 分位 — 来源：腾讯前复权日线（320 日窗口）")
    tech = {
        "trend": f"现价 {'站稳' if closes[-1] > sma60 else '跌破'} 60 日均线（SMA60={sma60:.2f}）",
        "momentum": f"20 日动量 {mom20 * 100:+.1f}%",
        "volatility": f"30 日年化波动 {vol30:.0%}",
    }
    return {"ticker": ticker, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": [], "technicals": tech,
            "_source": "tencent-gtimg", "_note": "Tier2 国内直连：报价+K线真实；财务明细与新闻缺失（需 yfinance 通道）"}


def fetch_us_via_relay(ticker):
    """Tier1 via 新加坡中继：在 SG 节点跑同脚本的 yfinance 全量路径，拉回数据卡。"""
    import subprocess as sp
    key = os.path.expanduser("~/.ssh/id_ed25519_gwpull")
    host = "ubuntu@43.134.172.70"
    sp.run(["scp", "-i", key, "-o", "ConnectTimeout=10", "-q",
            os.path.join(KIT, "scripts", "fetch_card.py"), f"{host}:/tmp/fetch_card.py"], check=True)
    r = sp.run(["ssh", "-i", key, "-o", "ConnectTimeout=10", host,
                f"python3 /tmp/fetch_card.py --ticker {ticker} --market us --out /tmp/card_{ticker}.json"],
               capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise SystemExit(f"中继取数失败: {r.stdout[-200:]} {r.stderr[-200:]}")
    sp.run(["scp", "-i", key, "-o", "ConnectTimeout=10", "-q",
            f"{host}:/tmp/card_{ticker}.json", "/tmp/"], check=True)
    card = json.load(open(f"/tmp/card_{ticker}.json"))
    card["_note"] = "真实数据（经中继走 yfinance 全量）"
    return card


def fetch_us(ticker):
    import yfinance as yf
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info or {}
    except Exception as e:
        print(f"⚠ info 拉取降级: {e}", file=sys.stderr)
    hist = t.history(period="1y")
    if hist.empty:
        raise SystemExit(f"无行情数据：{ticker}")
    price = round(float(hist["Close"].iloc[-1]), 2)
    as_of = hist.index[-1].strftime("%Y-%m-%d")

    f, fundamentals = [], []
    def add(text, src):
        fundamentals.append(f"{text} — 来源：{src}（截至 {as_of}）")
    if info.get("marketCap"):
        add(f"总市值 ${info['marketCap'] / 1e9:.0f}B", "yfinance/marketCap")
    if info.get("revenueGrowth") is not None:
        add(f"营收同比 {pct(info['revenueGrowth'])}", "yfinance/revenueGrowth")
    if info.get("grossMargins") is not None:
        add(f"毛利率 {pct(info['grossMargins']).replace('+', '')}", "yfinance/grossMargins")
    if info.get("operatingMargins") is not None:
        add(f"营业利润率 {pct(info['operatingMargins']).replace('+', '')}", "yfinance/operatingMargins")
    if info.get("returnOnEquity") is not None:
        add(f"ROE {pct(info['returnOnEquity']).replace('+', '')}", "yfinance/returnOnEquity")
    if info.get("freeCashflow"):
        add(f"自由现金流 ${info['freeCashflow'] / 1e9:.1f}B", "yfinance/freeCashflow")
    if info.get("totalCash") and info.get("totalDebt"):
        add(f"净现金 ${(info['totalCash'] - info['totalDebt']) / 1e9:.1f}B"
            f"（现金 {info['totalCash'] / 1e9:.1f}B / 有息负债 {info['totalDebt'] / 1e9:.1f}B）", "yfinance/totalCash,debt")
    if info.get("trailingPE"):
        add(f"滚动市盈率 {info['trailingPE']:.1f} 倍", "yfinance/trailingPE")

    news = []
    try:
        for n in (t.news or [])[:3]:
            ts = dt.datetime.fromtimestamp(n.get("providerPublishTime", 0)).strftime("%Y-%m-%d")
            news.append(f"{ts} {n.get('publisher', '?')}：{n.get('title', '')}")
    except Exception:
        pass

    close = hist["Close"]
    sma60 = close.rolling(60).mean().iloc[-1]
    mom20 = close.iloc[-1] / close.iloc[-21] - 1
    vol30 = float(hist["Close"].pct_change().tail(30).std() * math.sqrt(252))
    tech = {
        "trend": f"现价 {'站稳' if close.iloc[-1] > sma60 else '跌破'} 60 日均线（SMA60={sma60:.2f}）",
        "momentum": f"20 日动量 {pct(mom20)}",
        "volatility": f"30 日年化波动 {vol30:.0%}",
    }
    return {"ticker": ticker, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": news, "technicals": tech,
            "_source": "yfinance", "_note": "真实数据；新闻仅标题（摘要需另行授权源）"}


def fetch_cn_tencent(code):
    """A 股腾讯通道（国内直连首选；东财/akshare 易对云 IP 限流）。"""
    import re as _re, urllib.request
    sym = ("sh" if code.startswith(("6", "5")) else ("bj" if code.startswith(("4", "8")) else "sz")) + code
    def get(url):
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read()
    q = get(f"https://qt.gtimg.cn/q={sym}").decode("gbk", "ignore")
    f = q.split("~")
    def to_f(i):
        try:
            v = float(f[i]); return v if v == v else None
        except (ValueError, IndexError):
            return None
    if not _re.match(r"[\d.]+$", (f[3] if len(f) > 3 else "") or ""):
        raise SystemExit(f"腾讯 A 股报价解析失败: {q[:80]}")
    price = to_f(3)
    chg_pct = to_f(32) or 0.0
    pe, mcap_yi, pb = to_f(39), to_f(44), to_f(46)
    ts = f[30] or ""
    as_of = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else "?"
    k = json.loads(get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,320,qfq").decode())
    days = k["data"][sym]["qfqday"] or k["data"][sym].get("day")
    closes = [float(d[2]) for d in days]
    sma60 = sum(closes[-60:]) / 60
    mom20 = closes[-1] / closes[-21] - 1
    vol30 = (sum((closes[i] / closes[i - 1] - 1) ** 2 for i in range(-30, 0)) / 30) ** 0.5 * (252 ** 0.5)
    hi52, lo52 = max(closes[-252:]), min(closes[-252:])
    pos52 = (closes[-1] - lo52) / (hi52 - lo52)
    fundamentals = [f"现价 {price} CNY（日内 {chg_pct:+.2f}%） — 来源：腾讯 A 股行情（截至 {as_of}）"]
    if mcap_yi:
        line = f"总市值约 {mcap_yi:.0f} 亿元"
        if pe: line += f"、市盈率(TTM)约 {pe:.1f} 倍"
        if pb: line += f"、市净率约 {pb:.1f} 倍"
        fundamentals.append(line + " — 来源：同上")
    fundamentals.append(f"52 周区间 {lo52:.2f}–{hi52:.2f}，现价处于 {pos52:.0%} 分位 — 来源：腾讯前复权日线（320 日窗口）")
    tech = {
        "trend": f"现价 {'站稳' if closes[-1] > sma60 else '跌破'} 60 日均线（SMA60={sma60:.2f}）",
        "momentum": f"20 日动量 {mom20 * 100:+.1f}%",
        "volatility": f"30 日年化波动 {vol30:.0%}",
    }
    return {"ticker": code, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": [], "technicals": tech,
            "_source": "tencent-gtimg", "_note": "A 股腾讯通道：报价+K线真实；财务明细与新闻缺失（东财通道限流时自动略过）"}


def fetch_cn(code):
    import akshare as ak
    spot = ak.stock_individual_info_em(symbol=code)
    d = {r["item"]: r["value"] for _, r in spot.iterrows()}
    hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=(dt.date.today() - dt.timedelta(days=400)).strftime("%Y%m%d"), adjust="qfq")
    price = round(float(hist["收盘"].iloc[-1]), 2)
    as_of = hist["日期"].iloc[-1]
    fundamentals = [
        f"总市值 {int(d.get('总市值', 0)) / 1e8:.0f} 亿 — 来源：东财个股资料（截至 {as_of}）",
        f"市盈率(TTM) {d.get('市盈率(TTM)', '?')} 倍 — 来源：同上",
        f"行业 {d.get('行业', '?')} — 来源：同上",
    ]
    try:
        fin = ak.stock_financial_abstract(symbol=code)
        latest = fin.iloc[:, :3]
        fundamentals.append(f"近期财务摘要（最近报告期 {latest.columns[-1] if len(latest.columns) > 1 else '?'}）：营收/净利见数据卡 sidecar — 来源：东财财务摘要")
    except Exception:
        pass
    news = []
    try:
        for _, r in ak.stock_news_em(symbol=code).head(3).iterrows():
            news.append(f"{str(r['发布时间'])[:10]} 东财：{r['新闻标题']}")
    except Exception:
        pass
    close = hist["收盘"]
    sma60 = close.rolling(60).mean().iloc[-1]
    mom20 = close.iloc[-1] / close.iloc[-21] - 1
    vol30 = float(hist["收盘"].pct_change().tail(30).std() * math.sqrt(252))
    tech = {
        "trend": f"现价 {'站稳' if close.iloc[-1] > sma60 else '跌破'} 60 日均线（SMA60={sma60:.2f}）",
        "momentum": f"20 日动量 {mom20 * 100:+.1f}%",
        "volatility": f"30 日年化波动 {vol30:.0%}",
    }
    return {"ticker": code, "as_of": str(as_of), "price": price,
            "fundamentals": fundamentals, "news": news, "technicals": tech,
            "_source": "akshare(东财)", "_note": "真实数据；财务摘要字段随东财口径"}


def validate(card):
    for k in ("ticker", "as_of", "price", "fundamentals", "technicals"):
        assert card.get(k), f"数据卡缺字段: {k}"
    assert len(card["fundamentals"]) >= 3, "基本面数据不足 3 条，不足以开庭"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--out", default=None, help="数据卡输出路径（缺省 cards/<ticker>.json）")
    ap.add_argument("--market", choices=("auto", "us", "cn"), default="auto")
    ap.add_argument("--committee", action="store_true", help="取卡后直接运行议院")
    ap.add_argument("--via-relay", action="store_true", help="经 SSH 中继跑 yfinance 全量（国内网络用）")
    ap.add_argument("--tier", choices=("auto", "tencent"), default="auto", help="auto=直连yfinance失败转腾讯；tencent=强制Tier2")
    args = ap.parse_args()
    market = args.market
    if market == "auto":
        market = "cn" if args.ticker.isdigit() else "us"
    if market == "cn":
        card = fetch_cn_tencent(args.ticker)
        try:  # 东财增强（财务摘要/新闻），被限流时静默跳过
            import akshare as ak
            ndf = ak.stock_news_em(symbol=args.ticker).head(3)
            card["news"] = [f"{str(d)[:10]} 东财：{h}" for d, h in zip(ndf["发布时间"].tolist(), ndf["新闻标题"].tolist())]
            card["_note"] += "；新闻经东财增强"
        except Exception as e:
            print(f"⚠ 东财增强跳过（{type(e).__name__}）", file=sys.stderr)
    elif args.via_relay:
        card = fetch_us_via_relay(args.ticker)
    elif args.tier == "tencent":
        card = fetch_us_tencent(args.ticker)
    else:
        try:
            card = fetch_us(args.ticker)
        except Exception as e:
            print(f"⚠ yfinance 直连失败（{type(e).__name__}），降级腾讯 Tier2", file=sys.stderr)
            card = fetch_us_tencent(args.ticker)
    validate(card)
    if args.out:
        out = args.out
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    else:
        os.makedirs(CARDS, exist_ok=True)
        out = os.path.join(CARDS, f"{args.ticker}.json")
    json.dump(card, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"card → {out} · {len(card['fundamentals'])} 条基本面 · {len(card['news'])} 条新闻 · 截至 {card['as_of']}")
    if args.committee:
        subprocess.run([sys.executable, os.path.join(KIT, "scripts", "tradingagents.py"),
                        "--ticker", args.ticker, "--data", out, "--save"])


if __name__ == "__main__":
    main()
