#!/usr/bin/env python3
"""fetch_card — 真实行情数据卡取数器（WP1）

产出与 data/demo/DEMO.json 同构的数据卡（议院引擎直接消费）。
证据纪律的数据端落地：每条数据带来源与日期；缺什么就少什么，
不编造、不外推。市场自动识别：纯数字代码 → A股(akshare)，否则美股(yfinance)。

用法：
  python3 scripts/fetch_card.py --ticker NVDA            # 美股 → cards/NVDA.json（默认 OpenBB 富卡）
  python3 scripts/fetch_card.py --ticker 600519          # A股 → cards/600519.json
  python3 scripts/fetch_card.py --ticker NVDA --committee  # 取卡后直接开庭

美股通道（M1）：OpenBB 多 provider 富卡 —— cboe 报价/K线/隐含波动、sec 年报三表、
nasdaq 新闻，全部零 key 且不经雅虎（yfinance 全局限流痛点就此绕开）；各数据块
独立降级，缺什么就少什么。OpenBB 不可用时回落腾讯 Tier2。
"""
import argparse, datetime as dt, json, math, os, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# npm CLI 形态经 TRADINGAGENTS_CARDS 把数据卡落到调用方 cwd（缺省落仓内，开发行为不变）
CARDS = os.environ.get("TRADINGAGENTS_CARDS") or os.path.join(KIT, "cards")

# Card language: English by default (international-first), --lang zh / TRADINGAGENTS_LANG for Chinese
LANG = os.environ.get("TRADINGAGENTS_LANG") or "en"
def tt(en, zh):
    return en if LANG == "en" else zh


def pct(x):
    return f"{x * 100:+.1f}%" if x is not None and not (isinstance(x, float) and math.isnan(x)) else None


def _tech_from_closes(closes, src_label):
    """K 线技术面（纯收盘价序列，腾讯/OpenBB 两通道共用）。"""
    sma60 = sum(closes[-60:]) / 60
    mom20 = closes[-1] / closes[-21] - 1
    vol30 = (sum((closes[i] / closes[i - 1] - 1) ** 2 for i in range(-30, 0)) / 30) ** 0.5 * (252 ** 0.5)
    hi52, lo52 = max(closes[-252:]), min(closes[-252:])
    pos52 = (closes[-1] - lo52) / (hi52 - lo52)
    tech = {
        "trend": tt(f"Price is {'above' if closes[-1] > sma60 else 'below'} the 60-day MA (SMA60={sma60:.2f})",
                    f"现价 {'站稳' if closes[-1] > sma60 else '跌破'} 60 日均线（SMA60={sma60:.2f}）"),
        "momentum": tt(f"20-day momentum {mom20 * 100:+.1f}%", f"20 日动量 {mom20 * 100:+.1f}%"),
        "volatility": tt(f"30-day annualized volatility {vol30:.0%}", f"30 日年化波动 {vol30:.0%}"),
        "range52": tt(f"52-week range {lo52:.2f}–{hi52:.2f}, price at the {pos52:.0%} percentile — Source: {src_label}",
                      f"52 周区间 {lo52:.2f}–{hi52:.2f}，现价处于 {pos52:.0%} 分位 — 来源：{src_label}"),
    }
    return tech


def _billions(x):
    return f"${x / 1e9:,.1f}B" if x is not None else None


def _num(x):
    """SEC 表列的 None/NaN 统一归 None（np.nan 是 truthy，`or 0` 拦不住）。"""
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def fetch_us_openbb(ticker):
    """M1 富卡：OpenBB 多 provider —— cboe（报价/K线/IV30）、sec（年报三表）、nasdaq（新闻）。

    全零 key、不经雅虎；四块独立降级（K线块为技术面必需，失败则抛错让上层回落腾讯）。
    证据纪律：每条基本面带来源与截至日期，财务一律年报口径并点名报告期。
    """
    from openbb import obb

    providers, fails = {}, []

    # ── 块1 · cboe K 线（必需：技术面 + 52 周） ──
    hist = obb.equity.price.historical(
        ticker, provider="cboe",
        start_date=(dt.date.today() - dt.timedelta(days=400)).isoformat()).to_df()
    if hist.empty:
        raise SystemExit(f"cboe K 线为空：{ticker}")
    providers["historical"] = "cboe"
    closes = [float(x) for x in hist["close"]]
    k_as_of = hist.index[-1].strftime("%Y-%m-%d")
    tech = _tech_from_closes(closes, tt(f"CBOE daily bars (as of {k_as_of})", f"CBOE 日线（截至 {k_as_of}）"))

    fundamentals = []

    # ── 块2 · cboe 报价（现价 + 盘面 + 隐含波动） ──
    quote, q_as_of = None, k_as_of
    try:
        qdf = obb.equity.price.quote(ticker, provider="cboe").to_df()
        quote = qdf.iloc[0].to_dict()
        providers["quote"] = "cboe"
        q_as_of = str(quote.get("last_timestamp"))[:10] or k_as_of
        fundamentals.append(tt(
            f"Last {quote['last_price']:.2f} USD (intraday {quote['change_percent'] * 100:+.2f}%, "
            f"bid {quote.get('bid')} / ask {quote.get('ask')}) — Source: CBOE quote (as of {q_as_of})",
            f"现价 {quote['last_price']:.2f} USD（日内 {quote['change_percent'] * 100:+.2f}%，"
            f"买一 {quote.get('bid')}/卖一 {quote.get('ask')}） — 来源：CBOE 报价（截至 {q_as_of}）"))
        if quote.get("iv30") is not None:
            hv_en = f", 30-day realized {quote['hv30']:.0%}" if quote.get("hv30") is not None else ""
            hv_zh = f"，30 日已实现波动 {quote['hv30']:.0%}" if quote.get("hv30") is not None else ""
            fundamentals.append(tt(
                f"30-day options-implied volatility {quote['iv30']:.0%}{hv_en} — Source: CBOE IV30/HV30 (as of {q_as_of})",
                f"30 日期权隐含波动率 {quote['iv30']:.0%}{hv_zh} — 来源：CBOE IV30/HV30（截至 {q_as_of}）"))
    except Exception as e:
        fails.append(f"quote:{type(e).__name__}")
        fundamentals.append(tt(
            f"Last {closes[-1]:.2f} USD (latest close) — Source: CBOE daily bars (as of {k_as_of})",
            f"现价 {closes[-1]:.2f} USD（最近收盘） — 来源：CBOE 日线（截至 {k_as_of}）"))
    price = round(float(quote["last_price"]), 2) if quote else round(closes[-1], 2)
    as_of = max(q_as_of, k_as_of)

    # ── 块3 · sec 年报三表（财务证据主块） ──
    try:
        inc = obb.equity.fundamental.income(ticker, provider="sec", period="annual", limit=2).to_df()
        bal = obb.equity.fundamental.balance(ticker, provider="sec", period="annual", limit=2).to_df()
        csh = obb.equity.fundamental.cash(ticker, provider="sec", period="annual", limit=2).to_df()
        providers["fundamentals"] = "sec"
        i0 = inc.sort_values("period_ending", ascending=False).iloc[0]
        fy = tt(f"FY{i0['fiscal_year']} (period ending {str(i0['period_ending'])[:10]})",
                f"FY{i0['fiscal_year']}（报告期 {str(i0['period_ending'])[:10]}）")
        src = f"SEC 10-K · {fy}"
        rev, ni = _num(i0.get("total_revenue")), _num(i0.get("net_income"))
        gp, oi = _num(i0.get("total_gross_profit")), _num(i0.get("total_operating_income"))
        if rev:
            line_en, line_zh = f"{fy} revenue {_billions(rev)}", f"{fy} 营收 {_billions(rev)}"
            if len(inc) > 1:
                prev = _num(inc.sort_values("period_ending", ascending=False).iloc[1].get("total_revenue"))
                if prev:
                    yoy = f"{(rev / prev - 1) * 100:+.1f}%"
                    line_en += f" (prior {_billions(prev)}, YoY {yoy})"
                    line_zh += f"（上年 {_billions(prev)}，同比 {yoy}）"
            fundamentals.append(tt(line_en + f" — Source: {src}", line_zh + f" — 来源：{src}"))
        if rev and ni is not None:
            fundamentals.append(tt(
                f"{fy} net income {_billions(ni)} (net margin {ni / rev:.1%}) — Source: {src}",
                f"{fy} 净利润 {_billions(ni)}（净利率 {ni / rev:.1%}） — 来源：{src}"))
        if rev and gp:
            fundamentals.append(tt(
                f"{fy} gross margin {gp / rev:.1%} (gross profit {_billions(gp)}) — Source: {src}",
                f"{fy} 毛利率 {gp / rev:.1%}（毛利 {_billions(gp)}） — 来源：{src}"))
        if rev and oi:
            fundamentals.append(tt(
                f"{fy} operating margin {oi / rev:.1%} (operating income {_billions(oi)}) — Source: {src}",
                f"{fy} 营业利润率 {oi / rev:.1%}（营业利润 {_billions(oi)}） — 来源：{src}"))
        eps = _num(i0.get("diluted_eps"))
        if eps is not None:
            fundamentals.append(tt(
                f"{fy} diluted EPS {eps:.2f} — Source: {src}",
                f"{fy} 摊薄每股收益 {eps:.2f} — 来源：{src}"))
        b0 = bal.sort_values("period_ending", ascending=False).iloc[0]
        cash = (_num(b0.get("cash_and_equivalents")) or 0) + (_num(b0.get("short_term_investments")) or 0)
        debt = (_num(b0.get("long_term_debt")) or 0) + (_num(b0.get("current_portion_of_long_term_debt")) or 0)
        bsrc_en = f"SEC 10-K balance sheet ({str(b0['period_ending'])[:10]})"
        bsrc_zh = f"SEC 10-K 资产负债表（{str(b0['period_ending'])[:10]}）"
        if cash or debt:
            fundamentals.append(tt(
                f"Net cash {_billions(cash - debt)} (cash + ST investments {_billions(cash)} / interest-bearing debt {_billions(debt)}) — Source: {bsrc_en}",
                f"净现金 {_billions(cash - debt)}（现金+短投 {_billions(cash)} / 有息负债 {_billions(debt)}） — 来源：{bsrc_zh}"))
        eq = _num(b0.get("total_common_equity"))
        if eq:
            fundamentals.append(tt(
                f"Common shareholders' equity {_billions(eq)} — Source: {bsrc_en}",
                f"归母股东权益 {_billions(eq)} — 来源：{bsrc_zh}"))
        c0 = csh.sort_values("period_ending", ascending=False).iloc[0]
        ocf, capex = _num(c0.get("net_cash_from_operating_activities")), _num(c0.get("purchase_of_plant_property_and_equipment"))
        csrc = tt("SEC 10-K cash-flow statement", "SEC 10-K 现金流量表")
        if ocf is not None:
            fcf = ocf - abs(capex or 0)
            fundamentals.append(tt(
                f"{fy} operating cash flow {_billions(ocf)}, capex {_billions(abs(capex or 0))} → free cash flow {_billions(fcf)} — Source: {csrc}",
                f"{fy} 经营现金流 {_billions(ocf)}、资本开支 {_billions(abs(capex or 0))} → 自由现金流 {_billions(fcf)} — 来源：{csrc}"))
        bb, dv = _num(c0.get("repurchase_of_common_equity")), _num(c0.get("payment_of_dividends"))
        if bb or dv:
            fundamentals.append(tt(
                f"{fy} shareholder returns: buybacks {_billions(abs(bb or 0))}, dividends {_billions(abs(dv or 0))} — Source: {csrc}",
                f"{fy} 股东回报：回购 {_billions(abs(bb or 0))}、分红 {_billions(abs(dv or 0))} — 来源：{csrc}"))
        shares = _num(i0.get("weighted_ave_diluted_shares_os"))
        if shares and price:
            fundamentals.append(tt(
                f"Market cap ≈ {_billions(shares * price)} (fiscal-year weighted diluted shares × last price) — Source: SEC 10-K shares × CBOE price",
                f"总市值约 {_billions(shares * price)}（按年报加权摊薄股本折算现价） — 来源：SEC 10-K 股本 × CBOE 现价"))
    except Exception as e:
        fails.append(f"sec:{type(e).__name__}")
        print(f"⚠ SEC 财务块失败（{type(e).__name__}），富卡降级为行情+技术面", file=sys.stderr)

    # ── 块4 · nasdaq 新闻 ──
    news = []
    try:
        ndf = obb.news.company(ticker, limit=8).to_df()
        providers["news"] = "nasdaq"
        for _, r in ndf.iterrows():
            syms = str(r.get("symbols") or "")
            if ticker.split(".")[0].upper() not in syms.upper():
                continue
            news.append(f"{r.get('publisher', '?')}：{r.get('title', '')}（{r.get('url', '')}）")
            if len(news) >= 3:
                break
    except Exception as e:
        fails.append(f"news:{type(e).__name__}")

    card = {"ticker": ticker, "as_of": as_of, "price": price,
            "fundamentals": fundamentals + [tech["range52"]], "news": news, "technicals": tech,
            "_source": "openbb:cboe+sec+nasdaq",
            "_providers": {**providers, "fetched_at": dt.datetime.now().isoformat(timespec="seconds")},
            "_note": tt(f"M1 rich card: CBOE quote/K-line/IV + SEC 10-K statements + nasdaq news, zero-key and Yahoo-free; degraded blocks: {', '.join(fails) if fails else 'none'}",
                        f"M1 富卡：CBOE 报价/K线/IV + SEC 年报三表 + nasdaq 新闻，零 key 不经雅虎；降级块：{', '.join(fails) if fails else '无'}")}
    return card


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
    fundamentals = [tt(
        f"Last {price} USD (intraday {chg_pct:+.2f}%) — Source: Tencent US quote (as of {as_of})",
        f"现价 {price} USD（日内 {chg_pct:+.2f}%） — 来源：腾讯美股行情（截至 {as_of}）")]
    if mcap_b > 0 and pe:
        fundamentals.append(tt(
            f"Market cap ≈ ${mcap_b:.1f}B, trailing P/E ≈ {pe:.1f}x — Source: same",
            f"总市值约 ${mcap_b:.1f}B、滚动市盈率约 {pe:.1f} 倍 — 来源：同上"))
    elif mcap_b > 0:
        fundamentals.append(tt(
            f"Market cap ≈ ${mcap_b:.1f}B — Source: same",
            f"总市值约 ${mcap_b:.1f}B — 来源：同上"))
    tech = _tech_from_closes(closes, tt("Tencent adjusted daily bars (320-day window)", "腾讯前复权日线（320 日窗口）"))
    fundamentals.append(tech["range52"])
    return {"ticker": ticker, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": [], "technicals": tech,
            "_source": "tencent-gtimg", "_note": tt(
                "Tier2 CN-direct: real quote + K-line; fundamentals detail and news missing (needs the yfinance path)",
                "Tier2 国内直连：报价+K线真实；财务明细与新闻缺失（需 yfinance 通道）")}


def fetch_us_via_relay(ticker):
    """Tier1 via 新加坡中继：在 SG 节点跑同脚本的 yfinance 全量路径，拉回数据卡。"""
    import subprocess as sp
    key = os.path.expanduser("~/.ssh/id_ed25519_gwpull")
    host = "ubuntu@43.134.172.70"
    sp.run(["scp", "-i", key, "-o", "ConnectTimeout=10", "-q",
            os.path.join(KIT, "scripts", "fetch_card.py"), f"{host}:/tmp/fetch_card.py"], check=True)
    r = sp.run(["ssh", "-i", key, "-o", "ConnectTimeout=10", host,
                f"python3 /tmp/fetch_card.py --ticker {ticker} --market us --tier yfinance --out /tmp/card_{ticker}.json"],
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
    def add(text_en, text_zh, src):
        fundamentals.append(tt(f"{text_en} — Source: {src} (as of {as_of})",
                               f"{text_zh} — 来源：{src}（截至 {as_of}）"))
    if info.get("marketCap"):
        add(f"Market cap ${info['marketCap'] / 1e9:.0f}B", f"总市值 ${info['marketCap'] / 1e9:.0f}B", "yfinance/marketCap")
    if info.get("revenueGrowth") is not None:
        add(f"Revenue YoY {pct(info['revenueGrowth'])}", f"营收同比 {pct(info['revenueGrowth'])}", "yfinance/revenueGrowth")
    if info.get("grossMargins") is not None:
        add(f"Gross margin {pct(info['grossMargins']).replace('+', '')}", f"毛利率 {pct(info['grossMargins']).replace('+', '')}", "yfinance/grossMargins")
    if info.get("operatingMargins") is not None:
        add(f"Operating margin {pct(info['operatingMargins']).replace('+', '')}", f"营业利润率 {pct(info['operatingMargins']).replace('+', '')}", "yfinance/operatingMargins")
    if info.get("returnOnEquity") is not None:
        add(f"ROE {pct(info['returnOnEquity']).replace('+', '')}", f"ROE {pct(info['returnOnEquity']).replace('+', '')}", "yfinance/returnOnEquity")
    if info.get("freeCashflow"):
        add(f"Free cash flow ${info['freeCashflow'] / 1e9:.1f}B", f"自由现金流 ${info['freeCashflow'] / 1e9:.1f}B", "yfinance/freeCashflow")
    if info.get("totalCash") and info.get("totalDebt"):
        add(f"Net cash ${(info['totalCash'] - info['totalDebt']) / 1e9:.1f}B"
            f" (cash {info['totalCash'] / 1e9:.1f}B / interest-bearing debt {info['totalDebt'] / 1e9:.1f}B)",
            f"净现金 ${(info['totalCash'] - info['totalDebt']) / 1e9:.1f}B"
            f"（现金 {info['totalCash'] / 1e9:.1f}B / 有息负债 {info['totalDebt'] / 1e9:.1f}B）", "yfinance/totalCash,debt")
    if info.get("trailingPE"):
        add(f"Trailing P/E {info['trailingPE']:.1f}x", f"滚动市盈率 {info['trailingPE']:.1f} 倍", "yfinance/trailingPE")

    news = []
    try:
        for n in (t.news or [])[:3]:
            ts = dt.datetime.fromtimestamp(n.get("providerPublishTime", 0)).strftime("%Y-%m-%d")
            news.append(f"{ts} {n.get('publisher', '?')}: {n.get('title', '')}")
    except Exception:
        pass

    close = hist["Close"]
    tech = _tech_from_closes([float(x) for x in close],
                             tt(f"yfinance daily bars (as of {as_of})", f"yfinance 日线（截至 {as_of}）"))
    return {"ticker": ticker, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": news, "technicals": tech,
            "_source": "yfinance", "_note": tt(
                "Real data; news headlines only (summaries need a licensed source)",
                "真实数据；新闻仅标题（摘要需另行授权源）")}


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
    fundamentals = [tt(
        f"Last {price} CNY (intraday {chg_pct:+.2f}%) — Source: Tencent A-share quote (as of {as_of})",
        f"现价 {price} CNY（日内 {chg_pct:+.2f}%） — 来源：腾讯 A 股行情（截至 {as_of}）")]
    if mcap_yi:
        line_zh = f"总市值约 {mcap_yi:.0f} 亿元"
        line_en = f"Market cap ≈ CNY {mcap_yi:.1f}B"
        if pe:
            line_zh += f"、市盈率(TTM)约 {pe:.1f} 倍"
            line_en += f", PE(TTM) ≈ {pe:.1f}x"
        if pb:
            line_zh += f"、市净率约 {pb:.1f} 倍"
            line_en += f", PB ≈ {pb:.1f}x"
        fundamentals.append(tt(line_en + " — Source: same", line_zh + " — 来源：同上"))
    tech = _tech_from_closes(closes, tt("Tencent adjusted daily bars (320-day window)", "腾讯前复权日线（320 日窗口）"))
    fundamentals.append(tech["range52"])
    return {"ticker": code, "as_of": as_of, "price": price,
            "fundamentals": fundamentals, "news": [], "technicals": tech,
            "_source": "tencent-gtimg", "_note": tt(
                "A-share Tencent channel: real quote + K-line; fundamentals detail and news missing (auto-skipped when the EastMoney channel is throttled)",
                "A 股腾讯通道：报价+K线真实；财务明细与新闻缺失（东财通道限流时自动略过）")}


def fetch_cn(code):
    import akshare as ak
    spot = ak.stock_individual_info_em(symbol=code)
    d = {r["item"]: r["value"] for _, r in spot.iterrows()}
    hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=(dt.date.today() - dt.timedelta(days=400)).strftime("%Y%m%d"), adjust="qfq")
    price = round(float(hist["收盘"].iloc[-1]), 2)
    as_of = hist["日期"].iloc[-1]
    fundamentals = [
        tt(f"Market cap ≈ CNY {int(d.get('总市值', 0)) / 1e8:.1f}B — Source: EastMoney profile (as of {as_of})",
           f"总市值 {int(d.get('总市值', 0)) / 1e8:.0f} 亿 — 来源：东财个股资料（截至 {as_of}）"),
        tt(f"PE(TTM) {d.get('市盈率(TTM)', '?')}x — Source: same",
           f"市盈率(TTM) {d.get('市盈率(TTM)', '?')} 倍 — 来源：同上"),
        tt(f"Industry {d.get('行业', '?')} — Source: same",
           f"行业 {d.get('行业', '?')} — 来源：同上"),
    ]
    try:
        fin = ak.stock_financial_abstract(symbol=code)
        latest = fin.iloc[:, :3]
        fundamentals.append(tt(
            f"Recent financial abstract (latest period {latest.columns[-1] if len(latest.columns) > 1 else '?'}): revenue/net income in the data-card sidecar — Source: EastMoney financial abstract",
            f"近期财务摘要（最近报告期 {latest.columns[-1] if len(latest.columns) > 1 else '?'}）：营收/净利见数据卡 sidecar — 来源：东财财务摘要"))
    except Exception:
        pass
    news = []
    try:
        for _, r in ak.stock_news_em(symbol=code).head(3).iterrows():
            news.append(tt(f"{str(r['发布时间'])[:10]} EastMoney: {r['新闻标题']}",
                           f"{str(r['发布时间'])[:10]} 东财：{r['新闻标题']}"))
    except Exception:
        pass
    close = hist["收盘"]
    tech = _tech_from_closes([float(x) for x in close],
                             tt(f"EastMoney adjusted daily bars (as of {as_of})", f"东财日线（截至 {as_of}）"))
    return {"ticker": code, "as_of": str(as_of), "price": price,
            "fundamentals": fundamentals, "news": news, "technicals": tech,
            "_source": "akshare(东财)", "_note": tt(
                "Real data; financial-abstract fields follow EastMoney's own conventions",
                "真实数据；财务摘要字段随东财口径")}


def validate(card):
    for k in ("ticker", "as_of", "price", "fundamentals", "technicals"):
        assert card.get(k), tt(f"data card missing field: {k}", f"数据卡缺字段: {k}")
    assert len(card["fundamentals"]) >= 3, tt(
        "fewer than 3 fundamentals — not enough to convene the committee",
        "基本面数据不足 3 条，不足以开庭")


def main():
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--out", default=None, help="数据卡输出路径（缺省 cards/<ticker>.json）")
    ap.add_argument("--market", choices=("auto", "us", "cn"), default="auto")
    ap.add_argument("--committee", action="store_true", help="取卡后直接运行议院")
    ap.add_argument("--via-relay", action="store_true", help="经 SSH 中继跑 yfinance 全量（国内网络用）")
    ap.add_argument("--tier", choices=("auto", "openbb", "tencent", "yfinance"), default="auto",
                    help="auto=OpenBB 富卡失败转腾讯；openbb=强制富卡；tencent=腾讯 Tier2；yfinance=直连雅虎（需干净网络）")
    ap.add_argument("--lang", choices=("en", "zh"), default=LANG,
                    help="card language (default en)")
    args = ap.parse_args()
    LANG = args.lang
    market = args.market
    if market == "auto":
        market = "cn" if args.ticker.isdigit() else "us"
    if market == "cn":
        card = fetch_cn_tencent(args.ticker)
        try:  # 东财增强（财务摘要/新闻），被限流时静默跳过
            import akshare as ak
            ndf = ak.stock_news_em(symbol=args.ticker).head(3)
            card["news"] = [tt(f"{str(d)[:10]} EastMoney: {h}", f"{str(d)[:10]} 东财：{h}")
                            for d, h in zip(ndf["发布时间"].tolist(), ndf["新闻标题"].tolist())]
            card["_note"] += tt("; news via EastMoney", "；新闻经东财增强")
        except Exception as e:
            print(f"⚠ EastMoney enrichment skipped ({type(e).__name__})", file=sys.stderr)
    elif args.via_relay:
        card = fetch_us_via_relay(args.ticker)
    elif args.tier == "tencent":
        card = fetch_us_tencent(args.ticker)
    elif args.tier == "yfinance":
        card = fetch_us(args.ticker)
    elif args.tier == "openbb":
        card = fetch_us_openbb(args.ticker)
    else:  # auto：OpenBB 富卡优先，整体失败回落腾讯 Tier2
        try:
            card = fetch_us_openbb(args.ticker)
        except (Exception, SystemExit) as e:
            print(f"⚠ OpenBB 富卡失败（{type(e).__name__ if not isinstance(e, SystemExit) else e}），降级腾讯 Tier2", file=sys.stderr)
            card = fetch_us_tencent(args.ticker)
    validate(card)
    if args.out:
        out = args.out
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    else:
        os.makedirs(CARDS, exist_ok=True)
        out = os.path.join(CARDS, f"{args.ticker}.json")
    json.dump(card, open(out, "w"), ensure_ascii=False, indent=1)
    print(tt(f"card → {out} · {len(card['fundamentals'])} fundamentals · {len(card['news'])} news · as of {card['as_of']}",
             f"card → {out} · {len(card['fundamentals'])} 条基本面 · {len(card['news'])} 条新闻 · 截至 {card['as_of']}"))
    if args.committee:
        subprocess.run([sys.executable, os.path.join(KIT, "scripts", "tradingagents.py"),
                        "--ticker", args.ticker, "--data", out, "--save"])


if __name__ == "__main__":
    main()
