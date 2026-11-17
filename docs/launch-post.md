# Launch kit v2（2026-11-17 · facts frozen at npm 0.1.2 · awesome PR #16227 已开）

> Owner posts these with their own accounts; copy below is paste-ready per channel.
> Links: repo https://github.com/vicfei/dsh-TradingAgents · npm https://www.npmjs.com/package/dsh-tradingagents
> Image: repo `assets/demo.png` (English terminal card, real run: Buffett/Munger PASS@72 · Lynch HOLD@55 · Wood BUY@62 · PM PASS@72)
> Facts to keep accurate: 6-10 calls/session (~35-56s) · zero-key data (CBOE quote/K-line/options-IV + SEC 10-K + nasdaq news) · five tiers + PASS + REVIEW · track-record ledger settles alpha vs SPY/SSE Composite · English-first, --lang zh.

---

## X / Twitter

**Post 1 (≤280 chars, attach demo.png):**

TradingAgents, natively on DeepSeek Harness — a multi-agent investment committee that
abstains when evidence is thin, and shows its receipts.

- every claim evidence-tagged; PASS is a first-class verdict
- Buffett/Munger/Lynch/Wood guest seats that actually disagree
- zero-key data: CBOE/SEC/nasdaq, no Yahoo

npm i -g dsh-tradingagents

**Thread continuation (posts 2-4):**

2/ The demo above is a real run: guest seats split three ways (PASS/PASS vs HOLD vs
BUY), the risk officer logs the split as a guardrail, and the PM rules PASS naming it.
Deterministic CLI — 6 calls for the base committee, one per guest seat.

3/ Every archived verdict becomes a ledger entry. After the 5-trading-day window
trades out, it settles: entry at the next close, raw return + alpha vs SPY (or SSE
Composite for A-shares), plus a short reflection. The next session's PM reads those
lessons before ruling. The committee has a scorecard.

4/ Five tradeable tiers (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL), PASS for insufficient
evidence, and REVIEW when output can't be parsed — never silently a Hold.
Inspired by TauricResearch/TradingAgents & virattt/ai-hedge-fund, not affiliated.
★ github.com/vicfei/dsh-TradingAgents

---

## V2EX（分享创造节点）

**标题**：TradingAgents 有 DeepSeek Harness 原生版了——一个会弃权、有战绩的 AI 投研议院

**正文**：docs/launch-post.md 旧 CN 版基础上更新三点——①评级五档+PASS/REVIEW 双出口（读不出的判决绝不静默当 Hold）②战绩台账：每份判决 5 个交易日后按相对 SPY/上证的 alpha 结算并写反思，下次开庭 PM 会读教训 ③全仓英文优先（面向国际），`--lang zh` 可切中文。安装：`npm i -g dsh-tradingagents`；离线 DEMO 零 key 零网络 40 秒出完整 IC-MEMO。附 demo.png。结构致敬 Tauric 与 virattt，非官方无隶属；不是投资建议。求星。

---

## 即刻（AI 探索站话题）

短版 200 字：把 TradingAgents 做成了 DSH 插件：多空辩论议院，每个主张带证据标签，证据不足就 PASS 弃权；巴菲特/芒格/林奇/伍德客座评辩会真分裂（实测 PASS/PASS/HOLD/BUY）；判决 5 个交易日后自动按相对基准的 alpha 结算并写反思——议院有自己的战绩单。`npm i -g dsh-tradingagents`，离线 demo 零 key。附图。不是投资建议。

---

## 掘金

标题：TradingAgents, now native in DeepSeek Harness — a committee that abstains with receipts
（或中文标题：会弃权的 AI 投研议院：把 TradingAgents 搬进 DeepSeek Harness）
正文 = X thread 1-4 合并 + Quick start 代码块 + demo.png + 对比表截图/引用 README 表格。

---

## Discord（rea #showcase / jevcore 社区）

EN，遵守各社区自我推广规则（先看置顶）。用 X Post 1 + 一句 "Track-record loop: every
verdict settles against its benchmark after 5 trading days — the committee reads its
own lessons." + repo 链接。

---

## 执行清单

- [x] awesome-dsh-plugin PR **#16227** 已提交（等审）
- [ ] X 主贴+线程（demo.png）
- [ ] V2EX 分享创造
- [ ] 即刻 AI 探索站
- [ ] 掘金
- [ ] Discord：rea / jevcore
- [ ] （滞后）Trendshift 徽章——需基础星标量；0ms-marketplace 系备选仓（0xsline 1.4k★ 等）在主渠道过审后再投

> 渠道转化第 7 天复盘（R1 项）：以 npm 周下载 + repo 星标为口径。
