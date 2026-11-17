# 上游 TradingAgents 架构解剖（TauricResearch/TradingAgents，Apache-2.0，2026-11-17 浅克隆实测）

> 源码级逆向（~100 个 py 文件，graph/agents/memory/backtest/dataflows/llm_clients/cli）。
> 结论先行：**他们是"agentic 自由度 + 学习闭环"，我们是"证据纪律 + 确定性管线"**——
> 两条路线在分析师层和记忆层正面分叉，在裁决诚实性上殊途同归（他们的 REVIEW 哨兵 ≈
> 我们 PASS 的远亲）。最值得抄的一件：记忆结算闭环（pending → alpha 结算 → 反思 →
> 回注），那正是我们 ROADMAP M3"议院历史胜率"的引擎，且抄思路不抄代码（Apache-2.0
> 本可抄代码，但保持零代码关系的净室姿态更稳）。

## 1 · 执行管线（LangGraph 状态图，setup.py）

```
START ──┬─► [4 分析师并行：market / social / news / fundamentals]  ──┐
        │     每位=私有子图：LLM + 13 个 @tool 工具循环              │ 汇合
        └─► [Memory Log 节点（并行）：结算到期旧决策 + 取教训]  ──────┘
                     ▼
        Bull ↔ Bear 研究员辩论（count 上限，交替应答）
                     ▼
        Research Manager（deep 档 LLM）→ 五档评级 + 投资计划
                     ▼
        Trader（quick 档）→ 交易提案（看组合持仓上下文）
                     ▼
        风险三方辩论：Aggressive → Conservative → Neutral（固定轮换，count 上限）
                     ▼
        Portfolio Manager（deep 档）→ 终裁 + final_rating ──► END
```

- **分析师是 agentic 工具使用者**：私有消息史（互不可见、不写同 key），工具循环上限
  `max_tool_rounds=20`，超限注入 WRAP_UP 强制收报告（防 #1420 递归爆栈）——工程上
  是"每位分析师一个子图"的隔离设计
- **辩论终止=确定性计数**：多空 `2×max_debate_rounds` 交替；风险三方 `3×rounds` 固定
  轮换 Agg→Con→Neu。没有裁判，纯轮数截断
- **双档 LLM 分工**：quick（分析师/辩手/交易员/反思器）、deep（两位经理）——每档可
  各配 provider/endpoint（`quick_think_provider`…）

## 2 · 记忆闭环（招牌件，memory/ 三件套）

```
propagate() 存决策 → [date | ticker | rating | pending] 追加进 append-only md
      （HTML 注释硬分隔符 + 文件锁 + 幂等卫队：同 ticker 同日期只记一条）
下次运行时 Memory Log 节点（与分析师并行）：
  settle_all_pending → 每条到期 pending：
    持有窗（默认 5 个交易日）已走完 → 取「决策日次一收盘」入场、窗口末日收盘出场
    raw return + alpha vs 基准（后缀映射表：.SS→000001.SS / .SZ→399001.SS / .T→^N225 / 默认 SPY）
    → Reflector（quick LLM）写 2-4 句教训（明示窗口长度边界："为几个月写的论点不被一周证伪"）
    → 回写 log（pending→resolved，附 resolution_date=结果可知的时点）
  → get_past_context()（同 ticker 决策 + 跨标的教训）只注入 PM
```

- 时点纪律贯穿：入场=决策日**次一收盘**（当天读得到盘后新闻 #1518）；不评当日活价；
  未来窗未走完=保持 pending 下轮再试（#1169）
- 回测扫网格用**独立 log**（`memory_log_path` 指到 run 目录）——"扫盘灌进真实运行回读的
  上下文等于污染"（backtest.py 的第一设计原则）
- 记忆旋转：`memory_log_max_entries` 只裁 resolved，pending 永不裁

## 3 · 回测层（backtest.py，236 行，克制得罕见）

- (ticker, date) 网格逐格跑完整管线，断点续跑（格子去重）；单格失败不终止扫盘
- 评分=按评级分桶：方向命中（`_DIRECTION` 期望 × alpha 符号）+ 平均 alpha；Hold 无方向
  不计命中；REVIEW 不计分（"没有方向的判决既不算对也不算错"）
- **明写边界**："这是决策质量评估器，不是组合模拟器，也永远不许长成"（不发明成交价/
  现金账本）；"每格一次采样、文本源不存档，数字是指示性的而非可复现的"

## 4 · 裁决与评级（rating.py，哲学与我们最近的一件）

- 五档：Buy / Overweight / Hold / Underweight / Sell
- **REVIEW 哨兵**：确定性正则解析不出评级时输出 REVIEW（不可交易、须人工/重跑），绝不
  静默降级成 Hold（#1170："被记成 Hold 的东西会被下次运行当作做过的判断引用"）
- PM 提示词反和稀泥条款："冲突本身不是 Hold 的理由——权衡后更强的那方就是你的工作；
  只在证据真的均衡或太薄时 Hold，不要为了显得果断而硬造方向"——与我们 PM 的 PASS
  纪律同构，但他们没有"弃权"档，Hold 兼任了我们的 PASS+HOLD 两个语义
- 结构化输出（Pydantic）+ 自由文本降级 + 从文本确定性回读评级（"论文里引用的评级
  不能反过来顶替判决"）

## 5 · 数据与工程面

- **dataflows**：8 vendor（yahoo/alpha_vantage/sec_edgar/fred/reddit/stocktwits/
  polymarket…），按类配置 vendor 链（`"fundamental_data": "sec_edgar,yfinance"` 顺序
  降级，不静默路由到没选的源）；缓存目录；date_window 历史时点隔离
- **llm_clients**：openai/anthropic/google/azure/bedrock/chatgpt-auth 六客户端 + 工厂
  分档；重试预算与 max_tokens 上限可配（治 429 与失控输出）
- **checkpointer**：LangGraph 断点续跑（config `checkpoint_enabled`），组合指纹防陈旧
  resume
- **组合上下文三态**（portfolio.py）：持仓/空仓/未提供严格区分——"把没提供当成空仓
  等于编造账户事实"；券商中立（通用单位+货币标签）
- 全仓注释带 issue 编号（#1088/#1170/#1251/#1420…）——122.9k★ 的实战打磨痕迹，
  每条防御都有一次真实事故背书

## 6 · 对照我仓（dsh-tradingagents）

| 面 | 上游 | 我仓 | 判词 |
|---|---|---|---|
| 分析师数据 | 模型自己调 13 工具（agentic） | 预取数据卡（evidence-first） | **哲学分叉点**：他们查得自由，我们查得可审计；纪律红线"数据卡外无数字"不因对比动摇 |
| 证据纪律 | 自然语言报告，无标签 | [A#/B#/R#/G#/P#] 全链路引用+PM 必须点名动因 | 我仓核心差异点，保持 |
| 弃权/哨兵 | REVIEW（解析失败）+反和稀泥 Hold | PASS 一等裁决（证据不足） | 可借鉴：把"输出不可解析"与"证据不足"分成两个出口 |
| 评级粒度 | 五档 | 四值 BUY/HOLD/SELL/PASS | 可选加 Overweight/Underweight 档，PASS 保留 |
| 记忆闭环 | 产品化（pending→alpha→反思→回注） | 无（M3 规划） | **最高优先借鉴**——IC-MEMO 天然就是判决存档，补结算/反思/回注即成胜率页引擎 |
| 回测 | 网格+独立 log+诚实披露 | 无（M3 规划） | 抄思路：独立 log 防污染、Hold 不计命中、明写不可复现 |
| 风险层 | 三方辩论（激进/保守/中立） | 风控官只立护栏禁止决策 | 设计分歧：他们让风险**辩**，我们让风险**禁**——护栏不变裁决属性是我们的可审计卖点，不抄辩论化 |
| 客座人格 | 无 | 四大师评辩 | 我仓独有 |
| 数据源 | yahoo 为主+sec_edgar/fred | OpenBB（cboe IV30+sec+nasdaq 零 key）+腾讯 | 我仓更强且不怕雅虎限流；cboe 隐含波动他们没有 |
| 框架 | LangGraph 重框架 | 确定性 CLI（stdlib） | 我仓轻量是卖点（DSH 终端 30-40s 一场）；不引入 LangGraph |
| 成本 | 每场几十次调用（工具循环+多轮辩论） | 6-10 次 | 我仓优势，写进对比表 |
| 断点续跑 | checkpointer | 无 | 管线短优先级低，不急 |

## 7 · 借鉴清单（排入 M2/M3，抄思路不抄代码）

1. **M3 提前动工的记忆结算闭环**（价值最高）：IC-MEMO 存档加 `[date|ticker|decision|pending]`
   索引 → 持有窗走完用 cboe 日线结算 alpha（基准：A股 000001.SS/399001.SZ、美股 SPY，
   后缀映射表照抄思路）→ 反思器 2-4 句教训 → 下场开庭注入 PM。议院从此有战绩，
   "自证可信"从口号变数据
2. **REVIEW/PASS 双出口**：裁决 JSON 解析失败→REVIEW（不可交易须重跑）≠ PASS（证据
   不足弃权）——防解析事故被记忆层记成判断
3. **评级加档**：BUY/HOLD/SELL/PASS → 可选 +OVERWEIGHT/UNDERWEIGHT（五档语义更贴近
   研报习惯，PASS 语义不动）
4. **组合上下文三态**：`--portfolio` 入参（持仓/空仓/未提供严格分开，"未提供"绝不
   渲染成"无持仓"）
5. **辩论轮数可配**：`--rounds N`（多空各 N 轮应答，默认 1 维持成本面）
6. **回测网格纪律**（M3）：独立 memo log 防污染、Hold 不计命中、REVIEW 不计分、
   明写"指示性非可复现"
7. 不抄：agentic 工具循环（稀释数据卡纪律；如做，作 `--agentic` 可选模式且数据引用
   仍须成卡）、LangGraph、Trader 独立角色（PM 的 size_hint 已覆盖）

---
*分析基线：浅克隆 2026-11-17（SG 中继取回）；"他们 122.9k★"是家族调研档数字。本文入
仓 docs/，供 M2/M3 施工时对照。*
