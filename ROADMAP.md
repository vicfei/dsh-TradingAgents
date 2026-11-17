# ROADMAP — dsh-tradingagents（2026-11-17 重排版）

北极星指标：**30 天内进入 DSH 插件 top-20（≈150–300★），冲击 1000★**
（对照组：dsh-code 1001★ 为社区第一；dsh-trading 42★；jevcore 105★）。

**窗口判断（2026-11-17）**：上游 Tauric 本体进入打磨期（0.7.1 全是修固，README 顶部
挂 Trading-R1 early access 分流研发重心）——借势卡位 DSH 生态的时间窗开着。诊断：
**M0.5 发布战役整体未执行**（工程从 M0 直跳 M1），北极星是星标而分发动作为零——
重排第一原则：**先分发，再护城河，后生态**。

## 已交付基线（历史存档）

- **M0 引擎**（2026-11-16）：6 角色议院 + 证据标签 + PASS 一等裁决 + IC-MEMO v0.1 +
  离线 DEMO（PASS@55）
- **WP1 数据**（2026-11-16）：fetch_card 三级降级（yfinance→腾讯→SG 中继）
- **M1 主线四连**（2026-11-17，6fe8bea/5eab620/6a42b95）：OpenBB 富数据卡（cboe
  报价/K线/IV30 + sec 10-K + nasdaq 新闻，零 key 不经雅虎；NVDA PASS@72）；四大师
  客座评辩（DEMO 分裂判决 PASS@72 vs HOLD@55）；npm 0.1.0 分发车 bundle 就绪（pack
  干净+安装冒烟过）；CI 绿 badge 上首屏
- 逆向档案：`docs/upstream-architecture.md`（架构解剖+借鉴清单）、
  `docs/upstream-features.md`（功能面+差距表）——重排的依据

## R1 · 发布战役（本周，11-17 → 11-21）——把工程变成星标

> 阻塞点唯一且是 owner 动作：npm publish（OTP 手动，指引 `docs/PUBLISH-0.1.0.md`）。

- [x] **npm 0.1.0 发布**（owner OTP 2026-11-17）→ 官方源验证 latest=0.1.0；全新
      `npm i -g` → `tradingagents demo` 31s 完整开庭冒烟通过
- [x] 演示资产（2026-11-17）：assets/demo.png 终端卡（0.1.0 真跑数据：四客座分裂
      PASS@72/72/62 vs HOLD@55，视觉验收过）首屏嵌入 + assets/demo.cast 可回放；
      asciinema.org 匿名上传已终结（302 登录），动图版待 owner 账号
- [x] README 对比表：加"Model calls dozens (tool loops × debates)"与"市场数据零 key
      Yahoo-free"两行
- [x] marketplace 入口查实（2026-11-17）：真入口=awesome-dsh-plugin/awesome-dsh-plugin
      （24.9k★，data/plugins/ 一文件投稿制）→ dsh-market（12.7k★）目录自动聚合；
      投稿件已备（docs/marketplace-submission/，monorepo 子包格式）；**`dsh plugin add
      dsh-tradingagents` 实证可装**（0.2.2-rc.1，803ms）——外发 PR 待 owner 确认
- [x] 发布帖文案 v1（docs/launch-post.md 中英双版 + 渠道执行清单）——外发须 owner 过目
- [ ] 渠道清单逐项（入口已查实、投稿件已备，见上）：awesome-dsh PR（待 owner 确认）→ X/V2EX/即刻/掘金（文案待 owner 过目）/ Discord；Trendshift
      徽章 / X + V2EX + 即刻 + 掘金双语帖（标题带 TradingAgents 关键词）/ Discord
      （rea/jevcore 社区跨界）——发布帖文案先给 owner 过目
- [ ] 星标看板：接入 gap-radar 家族下载看板 + 每日星标记录，第 7 天复盘渠道转化
- [ ] super-agent 挂靠：包形态已就绪，找 owner/兄弟窗口把 dsh-tradingagents 列进
      @vicfei/dsh-super-agent 的可装清单（620 周下载主件通道）

## R2 · 战绩闭环（11-22 → 11-28）——议院学会记账，自证可信

> 原 M3 提前。上游最深的护城河件，抄思路不抄代码（Apache-2.0 净室）；我们的优势是
> cboe 数据不怕雅虎限流、IC-MEMO 天然就是判决存档格式。

- [ ] 判决台账：IC-MEMO 存档加 `[date|ticker|decision|confidence|pending]` 索引
      （append-only + 幂等，同标的同日一条）
- [ ] 结算器：持有窗（默认 5 交易日，可配）走完 → 决策日次一收盘入场 → raw return +
      **alpha vs 基准**（映射表：US→SPY、A 股→000001.SS/399001.SZ；数据走 cboe 通道）
      → 台账 pending→resolved（带 resolution_date 时点纪律）
- [ ] 反思器：1 次 quick 调用写 2-4 句教训（窗口边界明示："为数月写的论点不被一周
      证伪"），台账回写
- [ ] 回注：下场开庭时 PM 载荷带"同标的既往判决+跨标的教训"（只有 PM 读）
- [ ] `tradingagents settle` 独立子命令（定时结算，对应上游 settle_all_pending）
- [ ] 裁决双出口：JSON 解析失败 → REVIEW（不可交易须重跑）≠ PASS（证据不足弃权）；
      评级加档 Overweight/Underweight（五档语义，PASS 保留）
- [ ] 内容弹药：第一批评判性复盘帖（"议院的第一笔战绩"）——结算数据是独占素材

## R3 · 输入与呈现（11-29 → 12-05）——给用户看得到的质感

- [ ] IC-MEMO 单页 HTML 渲染（`--html`）：纯静态单文件+侧栏目录，可分享传播
      （对应 M2 Web 决策卡的轻量先行版；上游 complete_report.html 思路）
- [ ] `--portfolio` 三态入参：持仓/空仓/未提供严格分开（"未提供"绝不渲染成"空仓"），
      PM 与风控载荷加持仓块
- [ ] `--date` 历史模式：as-of 取卡（SEC 按申报时点口径正是我们 sec provider 能力）
      ——回测网格的前置
- [ ] 成本护栏（M1 余项）：llm() 解析 usage 累计，memo 页脚报调用数/token，
      `--max-calls` 硬顶
- [ ] `--rounds N` 多空辩论轮数可配（默认 1 维持成本面）
- [ ] （可选）卡瘦身 flag：`--no-news` 等，长市况下控 token

## R4 · 生态与组合议院（12-06 → 12-15）——规模化的两翼

- [ ] **组合议院**（原 M2 头牌，上游没有的真差异件）：多标的仓位分配辩论 +
      风控组合约束（相关性/回撤）；IC-MEMO 组合版格式
- [ ] cordis typed-tools 完整插件模块（0.2.0）：`dsh plugin add dsh-tradingagents`
      真注册，委员会作为 typed tools 暴露（plugin-spec.md 留的 0.2.0 位）
- [ ] 回测网格：`iter_grid/run/summarize` 三件套（独立 memo log 防污染、Hold 不计
      命中、明写"指示性非可复现"——纪律照抄上游）
- [ ] 战绩页（公开）：议院历史胜率/alpha 分桶页面——"自证可信"的落地形态，也是
      常青内容资产
- [ ] IC-MEMO 独立 spec 仓 + 多语言 SDK（Python/TS）+ 社区人格包 SDK（原 M3）

## 明确不做（重排时一并钉死）

- LangGraph/重框架迁移（确定性 CLI 是卖点）；agentic 工具循环（稀释"数据卡外无
  数字"红线；若做须 `--agentic` 可选且数据引用仍成卡）；交互式 TUI（DSH 场景天然
  无头）；ChatGPT OAuth（key 已就位）；Trader 独立角色（PM 的 size_hint 已覆盖）；
  风险层辩论化（风控官"只立护栏禁止决策"是可审计卖点）；checkpoint resume（管线
  6-10 调用太短，等真有需求再说）

## 纪律（不可让步项）

- 证据标签与 PASS 裁决是产品灵魂，任何功能不得稀释；
- 真实数据模式禁止模型编数（数据卡外无数字），合成模式必须显著标注；
- 台账/结算时点纪律：入场=决策日次一收盘、不评当日活价、窗口未走完保持 pending、
  resolved 回写带 resolution_date；
- 回测与扫盘一律独立台账，永不污染真实运行回读的上下文；
- 不是投资建议的声明在每份 IC-MEMO 页脚。

## 星标策略（不变，R1 执行）

1. **名字即流量**：TradingAgents 全名保留吃上游搜索溢流；README credit + Not affiliated
2. **关键词矩阵**：topics tradingagents/ai-hedge-fund/deepseek-harness/dsh/
   multi-agent-trading/investment-committee/bull-bear/quant；描述双语
3. **对比表开场**：搜索者 10 秒看清定位（rea 打法）
4. **零摩擦演示**：离线 DEMO 零 Key 零网络 40 秒完整 IC-MEMO；PASS 弃权+人格分裂是
   传播钩子
5. **开放格式卡位**：IC-MEMO 独立 spec（VIDEO.md 打法）
6. **战绩即内容**：R2 起每批结算数据都是独占发布素材
