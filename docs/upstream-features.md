<!-- Internal working notes (Chinese) — kept for development reference; user-facing docs are English-first per issue #1 -->
# 上游 TradingAgents 功能面清单（TauricResearch，2026-11-17 浅克隆实测，接续 upstream-architecture.md）

> 架构解剖见 `upstream-architecture.md`（怎么搭的）；本文回答"能用它做什么"。
> 版本 0.7.1（2026-10-27），20+ 测试文件，Keep-a-Changelog + 语义化版本。
> README 顶部另挂 Trading-R1 early access（他们的下一代 RL 推理产品——多线布局信号）。

## A · 入口形态（五种）

1. **交互式 TUI**：`tradingagents` 起 问答题式配置（标的/日期/LLM/深度/分析师子集），
   上次的答案回填为默认（回车即确认）；运行中实时滚动各 agent 产出
2. **无头模式**：per-run 步骤用 flag 答完（`--ticker --date --analysts --save --no-show
   --checkpoint --portfolio --no-html`），其余用 `TRADINGAGENTS_*` 环境变量；缺答案
   在开跑前停下并**点名该设哪个 flag**（CI/定时任务友好）
3. **Python API**：`TradingAgentsGraph().propagate()` + `save_reports()`
4. **Docker**：compose + 数据卷（结果/记忆/缓存）；`--profile ollama` 本地模型一键起；
   `.env.enterprise` 走 Azure
5. **OAuth 子命令**：`tradingagents login chatgpt`——用 ChatGPT Plus/Pro **订阅**代替
   API key（localhost 回调，`logout` 可撤销）

## B · 标的与市场覆盖

- 雅虎覆盖的全市场：后缀Ticker——US / `.HK` / `.T` / `.L` / `.NS` `.BO` / `.TO` /
  `.AX` / **A 股 `.SS` `.SZ`（茅台=600519.SS）** / 加密 `BTC-USD`
- 标的身份解析：别名归一（`XAUUSD→GC=F`）；加密资产改提示词框架（"当作资产而非公司，
  别找财报"）
- alpha 基准按交易所后缀自动映射（20+ 市场，A 股→上证/深证成指）

## C · 模型接入（业界最宽面，15+ provider）

OpenAI / Google / Anthropic / xAI / **DeepSeek** / Qwen（国际+国内双端点）/ GLM（Zhipu
国际+BigModel 国内）/ MiniMax（全球+国内）/ OpenRouter / Mistral / Kimi / Groq /
NVIDIA NIM / Azure（企业）/ Bedrock（extra）/ **Ollama（本地）** / openai_compatible
（vLLM/LM Studio/llama.cpp 任意兼容端点）。

- **双档分治可跨厂**：quick 档（分析师/辩手/交易员）与 deep 档（两位经理）各配
  provider+模型+端点——"经理跑 Claude、其余跑 OpenAI"
- 每厂思考档位参数（reasoning_effort / thinking_level / effort）、max_tokens 上限、
  重试预算（治 429）

## D · 数据功能（时点纪律是灵魂）

- 13 个分析师工具 × 8 vendor，按类配 vendor 链（`fundamental_data: sec_edgar,yfinance`）
- **SEC EDGAR「按申报时点」财报**：历史日期的运行读到的是**当天所见版本**——后来重述
  的数字仍读首次申报值（Apple 2008 总资产例：期间运行读 $39.6B 而非重述后 $36.2B）；
  零 key；2009 起；Q4 不推导（申报人只在年报里给）
- 雅虎财报按"覆盖期"而非"发布日"记——历史运行被告知** withheld**（无法证明当时公开了
  什么）而非硬塞现值；内幕交易同理（按事件日非申报日）
- 社交面：Reddit + StockTwits，可选 **Jev 筛查**（TYPESAFE_API_KEY）——离题帖剔除，
  按多头/空头/中立/不明计数开路
- 宏观：FRED（免费 key）；**预测市场：Polymarket 零 key**（事件概率入证据）；全球新闻
  查询词可配（`global_news_queries`）
- 一切数据 as-of trade_date（未来日期直接拒绝）

## E · 运行体验

- 研究深度选择（quick/deep → 辩论轮数）；分析师团队子集（market/news/social/
  fundamentals 任选）；历史分析日期（time-travel）
- 实时进度 + **成本统计回调**（LLM 调用数/工具调用数/token in/out 全程计数）
- 输出语言可配（内部辩论保持英文，产出翻译）
- 官方更新与公告通道（每日至多一次、后台、可关）

## F · 输出

- **报告树**：每角色一个 md（market/sentiment/news/fundamentals/bull/bear/manager/
  trader/aggressive/conservative/neutral/decision）+ 汇总 complete_report.md
- **complete_report.html**：单页 HTML 带目录侧栏（浏览器/手机/打印三态可读）
- 保存时可自动开浏览器

## G · 持久化与运维

- 记忆日志常开（`~/.tradingagents/memory/trading_memory.md`），路径可覆盖，条数上限
  旋转（pending 永不裁）
- `ta.settle_all_pending()` 独立结算入口（定时任务用）
- **Checkpoint resume**：`--checkpoint` opt-in，按节点存 SQLite（每标的一个库），
  成功自动清、`--clear-checkpoints` 重置
- 组合 JSON：`--portfolio my_book.json`（三态纪律见架构篇）
- 回测三件套：`iter_grid / run_backtest / summarize`

## H · 与我仓的功能差距表（我仓缺 → 借鉴优先级）

| 功能 | 上游 | 我仓现状 | 借鉴判定 |
|---|---|---|---|
| 历史日期回看（as-of） | 全链路时点纪律+SEC 按申报版 | 数据卡带 as_of 但只有"今天" | **高**：`--date` 历史模式是回测/胜率页的前置；SEC EDGAR 时点口径正是我们 sec provider 能力 |
| 成本统计 | 调用/token 全程计数 | 无（M1 余项"成本护栏"） | **高**：正好是成本护栏的实现参照（llm() 返回时累计 usage） |
| 单页 HTML 报告 | complete_report.html 带目录 | 无（M2 Web 决策卡） | **高**：IC-MEMO 渲染先行版——纯静态单文件，无框架依赖 |
| 组合 JSON 入参 | --portfolio 三态 | 无 | **中**：PM 的 size_hint 变成对着真持仓说话 |
| 分析师子集 | --analysts 任选 | 卡内容固定 | 低（我们卡即四分析师合一，可加 --no-news 之类瘦身flag） |
| 独立结算命令 | settle_all_pending | 无（M3） | **高**（与记忆闭环同件，M3 一起做） |
| 断点续跑 | SQLite checkpoint | 无 | 低（管线 6-10 调用，短） |
| OAuth 订阅登录 | ChatGPT Plus/Pro | 不适用 | 不抄（DSH 场景 key 已就位） |
| 交互式 TUI | 问答题 CLI | 无头 CLI（DSH 场景天然无头） | 不抄 |
| 更新公告通道 | 每日检查 | 无 | 不抄（生态位置不同） |
| 报告树分角色文件 | 12 个 md | 单 IC-MEMO | 不抄（单文件可审计是我们的格式主张；可加可选 sidecar） |

## I · 对我仓 M2/M3 的功能补强清单（合并两篇分析）

1. **M3 记忆结算闭环**（架构篇已列）+ 独立结算子命令 + 历史日期模式——三件同源，
   一起动工：`--date` 取历史卡 → 开庭 → 存档 → settle → 反思 → 回注
2. **成本护栏**（M1 余项）：抄 stats 思路——llm() 解析 usage 累计，卡/memo 页脚报
   调用数与 token，`--max-calls` 硬顶
3. **IC-MEMO HTML 渲染**（M2 提前的轻量件）：单文件静态页+侧栏目录，无框架
4. **`--portfolio` 三态入参**：PM/风控载荷加持仓块（未提供≠空仓）
5. 五档评级加档 + REVIEW/PASS 双出口（架构篇已列，功能上即"评级词汇表"一件）

---
*分析基线同 architecture 篇：2026-11-17 SG 中继浅克隆。功能判断以源码与 README 实测
为准，README 截图（CLI 界面）未逐帧验证。*
