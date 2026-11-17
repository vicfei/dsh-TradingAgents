# dsh-tradingagents — TradingAgents 的 DeepSeek Harness 原生版

**一个在你终端里开庭的多智能体投研议院——每个主张带证据标签，每次裁决可审计。**

[![npm](https://img.shields.io/npm/v/dsh-tradingagents)](https://www.npmjs.com/package/dsh-tradingagents) [![License: MIT](https://img.shields.io/badge/license-MIT-3da639)](LICENSE)

> 结构致敬 [Tauric Research 的 TradingAgents](https://github.com/TauricResearch/TradingAgents) 与
> [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)——重构为 DeepSeek Harness
> 原生体验。非官方、无隶属。[English README](README.md)

## 一句话定位

6 角色议院（分析师 → 多方 → 空方 → 回应 → 风控只立护栏 → 组合经理裁决）：
每个主张带 `[A#][B#][R#][G#]` 证据标签，裁决必须点名动因，**PASS 弃权是一等公民**
（证据不足就拒绝表态），输出可审计的 [IC-MEMO](templates/IC-MEMO.md) 开放格式。
客座席位：巴菲特/芒格/林奇/伍德用各家方法论点评多空辩论（会真实分裂）。

## 快速开始（零额外 key）

```bash
npm i -g dsh-tradingagents
tradingagents demo --guests all --save          # 离线合成数据开庭，约 40 秒
tradingagents card --ticker NVDA --committee    # 零 key 真数据 → 完整议院
```

或源码运行：`python3 scripts/tradingagents.py --ticker DEMO --guests all --save`

- 输出默认英文（面向国际），`--lang zh` 切换中文（环境变量 `TRADINGAGENTS_LANG`）
- 真数据多级通道且不经雅虎：OpenBB 富卡（CBOE 报价/K线/期权隐含波动 + SEC 10-K
  三表 + nasdaq 新闻，全零 key）→ 腾讯通道回落（国内直连可用）→ `--via-relay` 中继
- 一场 6-10 次调用约 31-55 秒；每条数据带来源与截至日期

## 纪律

- 数据卡外无数字：议院只看数据卡，禁止模型编数；合成运行保留 DEMO 标记
- 已存档纪要不可编辑；重开须有新证据（纪要里的 invalidation 定义了什么算新证据）

**不是投资建议。**

详见英文 [README](README.md)（对比表/管线图/格式说明）与 [ROADMAP](ROADMAP.md)。
