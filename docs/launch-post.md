# 发布帖文案 v1（R1 渠道弹药——owner 过目后方可外发）

> 标题模板沿用既定策略：带 TradingAgents 关键词吃上游搜索流量；中英双版；结尾统一
> 短链与 badge。发布渠道：X / V2EX（分享创造）/ 即刻 / 掘金 / Discord（rea、jevcore
> 社区跨界）。**发帖是外部动作，须 owner 手动执行或明确授权。**

---

## EN（X + Discord）

**TradingAgents, now native in DeepSeek Harness — and it knows how to abstain.**

A multi-agent investment committee that runs in your terminal:

- analyst → bull → bear → risk → PM, every claim evidence-tagged `[A#][B#][R#][G#]`
- **PASS is a first-class verdict** — insufficient evidence means no call, with reasons
- 4 guest seats: Buffett / Munger / Lynch / Wood critique the debate itself (they split — see demo)
- zero-key real data: CBOE quote/K-line/options-IV + SEC 10-K + nasdaq news (Yahoo-free)
- 6–10 model calls per session (~40s), auditable IC-MEMO output

```bash
npm i -g dsh-tradingagents
tradingagents demo --guests all --save
```

Not affiliated with Tauric Research — structure inspired, discipline rebuilt for auditability.
Not investment advice. ⭐ github.com/vicfei/dsh-TradingAgents

---

## CN（V2EX 分享创造 / 即刻 / 掘金）

**TradingAgents 有 DSH 原生版了——一个会弃权的 AI 投研议院**

楼上各位聊多智能体投研，我们把它做成了 DeepSeek Harness 插件：

- 6 角色议院：分析师 → 多方 → 空方 → 风控（只立护栏禁止决策）→ PM 裁决
- **每个主张带证据标签，裁决必须点名是哪条论据说服了它**——可审计是产品灵魂
- **PASS 弃权是一等公民**：证据不足就拒绝表态，这是特性不是失败
- 客座席位：巴菲特/芒格/林奇/伍德用各家方法论点评多空辩论（实测会分裂：
  巴菲特 PASS@72 vs 伍德 HOLD@55，风控官为分歧专门立护栏条款）
- 数据零 key：CBOE 报价/K线/**期权隐含波动** + SEC 10-K 三表 + nasdaq 新闻，
  完全绕开被限流的雅虎；A 股走腾讯通道
- 一场 6-10 次调用约 40 秒，离线 DEMO 零 Key 零网络可跑全程

```bash
npm i -g dsh-tradingagents
tradingagents demo --guests all --save
```

结构致敬 Tauric Research 的 TradingAgents 与 virattt 的 ai-hedge-fund，非官方、
无隶属；纪律为可审计性重写。不是投资建议。求星：github.com/vicfei/dsh-TradingAgents

---

## 渠道执行清单（外发前逐项）

- [ ] X（EN 版 + demo.png）
- [ ] V2EX /go/create 分享创造节点（CN 版）
- [ ] 即刻「AI 探索站」话题（CN 版）
- [ ] 掘金（CN 版 + 首屏图）
- [ ] Discord：rea 官方社区 #showcase、jevcore 社区（EN 版，遵守各社区自我推广规则）
- [ ] dsh-plugin marketplace 提交（渠道定位待查——见 ROADMAP R1 备注）
- [ ] awesome-dsh 系 PR（仓定位待查）
- [ ] Trendshift 徽章申请（通常需基础星标量，滞后执行）

> 备注：marketplace/awesome-dsh 的确切提交入口本窗口尚未查实——外发前 owner 确认
> 或授权我调研（GitHub API 可用）。
