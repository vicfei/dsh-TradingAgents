# ROADMAP — dsh-tradingagents

北极星指标：**30 天内进入 DSH 插件 top-20（≈150–300★），冲击 1000★**
（对照组：dsh-code 1001★ 为社区第一；dsh-trading 42★；jevcore 105★）。

## 星标策略（引流设计，与命名一体）

1. **名字即流量**（owner 定调）：`TradingAgents` 全名保留——Tauric 仓的搜索流量直接
   溢流（"tradingagents deepseek/harness/中文"全吃）；npm `dsh-tradingagents` 已验可注册。
   合规姿势：README 首屏 credit + "Not affiliated"，"X for Y" 是 OSS 惯例（rea-video 先例）。
2. **关键词矩阵**：repo topics = tradingagents, ai-hedge-fund, deepseek-harness, dsh,
   multi-agent-trading, investment-committee, bull-bear, quant；描述双语含中文词（43% 生态
   是中文用户）。
3. **对比表开场**：README 第一屏就是三方对照表——搜索者 10 秒内看清定位（rea 打法）。
4. **零摩擦演示**：离线合成 DEMO（零 Key 零网络）31 秒出完整 IC-MEMO；GIF/asciinema
   首屏。PASS 弃权裁决是传播钩子（"会弃权的 AI 议院"）。
5. **开放格式卡位**：IC-MEMO 独立 spec（VIDEO.md 打法）——别的交易插件若采纳格式，
   名字永远跟着我们。
6. **渠道清单**（M0.5 执行）：dsh-plugin marketplace 提交 / awesome-dsh 系 PR /
   Trendshift 徽章 / X + V2EX + 即刻 + 掘金双语帖（标题带 TradingAgents 关键词）/
   Discord（rea/jevcore 社区跨界发帖）。

## 里程碑

### M0 · 引擎冒烟 ✅（2026-11-16）
6 角色管线（analyst→bull→bear→bull 回应→risk→PM）+ 证据标签纪律 + PASS 一等裁决
+ IC-MEMO v0.1 模板 + 离线 DEMO 数据。冒烟产出 `memos/DEMO-2026-11-16.md`
（PASS@55，PM 逐条点名动因）。

### M0.5 · 发布包（本周）
- [ ] README 双语打磨 + 首屏 asciinema/GIF（终端跑一场 DEMO 全程）
- [ ] **公开仓上线 + marketplace 提交 + 渠道清单逐项执行**
- [ ] 发布帖文案（中英双版，标题模板："TradingAgents, now native in DeepSeek Harness"）
- [ ] 星标看板：每日记录，第 7 天复盘渠道转化

### M1 · 真数据 + 插件化（第 2-3 周）
- [x] 数据适配器：yfinance（美股零 Key）/ akshare（A 股零 Key），数据卡 Schema 固化（WP1，2026-11-16）
- [x] 富数据卡（2026-11-17）：OpenBB 多 provider —— CBOE 报价/K线/IV30 + SEC 10-K 三表 +
      nasdaq 新闻，全零 Key 且不经雅虎（yfinance 全局限流痛点绕开）；四块独立降级、
      NaN 哨兵防泄漏；NVDA 开庭 PASS@72（IV30/HV30 与证据错配稽核入裁决）、AAPL 全绿
- [x] 人格包跨接（2026-11-17）：ai-hedge-fund 四大师（巴菲特/芒格/林奇/伍德）作客座席位，
      `--guests` 评辩而非盲估（差异点：看完整多空辩论后用各家方法论裁决式点评）；
      DEMO 全客座实测 10 调用 39s——人格真实分裂（PASS@72 vs HOLD@55），风控官为分歧
      立 [G8] 条款，PM 点名客座分裂入裁决；PERSONAS 定义内嵌并标注同步来源（bundle 自包含）
- [ ] npm 0.1.0 skill bundle（按 docs/plugin-spec.md jevcore-dsh 模板）：
      `dsh plugin add dsh-tradingagents` 一行装，委员会作为 typed tools 暴露
- [ ] super-agent 分发接入（@vicfei/dsh-super-agent 可装形态）
- [ ] 成本护栏：每场上限（调用数/token 预算），headless CI 冒烟入 README badge

### M2 · 人格包 + 组合议院（第 4-6 周）
- [ ] persona packs（ai-hedge-fund 式：巴菲特/芒格/林奇…客座席位，可配置）
- [ ] 多标的组合议院（跨标的仓位分配辩论）+ 风控组合约束（相关性/回撤）
- [ ] Web UI 决策卡（IC-MEMO 渲染 + 辩论时间轴）

### M3 · 标准与生态（第 2 月起）
- [ ] IC-MEMO 独立 spec 仓 + 多语言实现（Python/TS SDK）+ 社区角色包 SDK
- [ ] 回测轨迹：IC-MEMO 存档 → 事后命中率统计（议院的历史胜率页面——自证可信）

## 纪律（不可让步项）

- 证据标签与 PASS 裁决是产品灵魂，任何功能不得稀释；
- 真实数据模式禁止模型编数（数据卡外无数字），合成模式必须显著标注；
- 不是投资建议的声明在每份 IC-MEMO 页脚。
