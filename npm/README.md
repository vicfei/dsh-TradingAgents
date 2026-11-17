# dsh-tradingagents

**TradingAgents, natively on DeepSeek Harness** — a multi-agent investment
committee as a deterministic CLI: analyst → bull → bear → rebuttal → (guest
seats) → risk → PM, every claim evidence-tagged, `PASS` a first-class verdict,
output an auditable [IC-MEMO](https://github.com/vicfei/dsh-TradingAgents).

```bash
npm i -g dsh-tradingagents
tradingagents demo --guests all --save          # offline smoke, 10 calls, ~40s
tradingagents card --ticker NVDA --committee    # zero-key real data → committee
```

- Committee needs only `python3` (stdlib) + a `DEEPSEEK_API_KEY` in `~/.bashrc`.
- Rich data card (`card`): CBOE quote/K-line/options-IV + SEC 10-K statements +
  nasdaq news via [OpenBB](https://openbb.co) — zero API keys, Yahoo-free.
  Optional: `pip install --user openbb`; without it the CLI falls back to
  Tencent channels (CN-cloud friendly).
- Register the DSH skill: `ln -s "$(npm root -g)/dsh-tradingagents/skills/dsh-tradingagents" ~/.dsh/skills/dsh-tradingagents`

Structure inspired by TradingAgents (Tauric Research) and ai-hedge-fund
(virattt). Not affiliated with either. **Not investment advice.**

Full docs: [github.com/vicfei/dsh-TradingAgents](https://github.com/vicfei/dsh-TradingAgents)
