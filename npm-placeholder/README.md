# dsh-tradingagents

> TradingAgents, natively on DeepSeek Harness — a multi-agent investment committee
> that debates in your terminal: analyst → bull → bear → risk guardrails →
> portfolio manager. Every claim carries an evidence tag, every verdict names
> what moved it, and **abstention (PASS) is a first-class decision**.
>
> Inspired by TauricResearch/TradingAgents & virattt/ai-hedge-fund (not affiliated).

**Status: name reserved — first release in development.**

Engine and docs: https://github.com/vicfei/dsh-TradingAgents

- 6-role committee pipeline, ~30s per session on your existing DSH model key
- Real-data adapters: US & A-share, zero API keys, CN-cloud friendly
- Output: [IC-MEMO](https://github.com/vicfei/dsh-TradingAgents/blob/main/templates/IC-MEMO.md) — an open, auditable investment-committee memo format
- Not investment advice.


---

**发布记录**：2026-11-16 手动 `npm publish`（网页认证流）成功。注意：npm 新版分阶段发布会在版本列表留下一个 `0.0.0-stage` 内部占位工件（描述 "Temporary package placeholder for staged publishing"），非抢注，`latest` 正常指向 0.0.1。
