# PR body（提交 awesome-dsh-plugin 用——owner 确认后执行）

**Adds vicfei/dsh-TradingAgents — multi-agent investment committee (workflow)**

One file added: `data/plugins/vicfei__dsh-TradingAgents--npm.yml` (monorepo subpackage
format — the installable package lives in the repo's `npm/` directory and on npm as
`dsh-tradingagents`).

- Install (verified on dsh 0.2.2-rc.1, 803ms): `dsh plugin add dsh-tradingagents`
  (npm 0.1.0, declares `dsh.bundle` + `cordis.patch.yml`)
- Distribution vehicle: a skill (`skills/dsh-tradingagents/SKILL.md`, symlink into
  `~/.dsh/skills/`) + a `tradingagents` CLI that spawns the bundled Python engine
- Real working code: 6-role committee engine, 4 guest personas, OpenBB zero-key data
  cards, CI-green, archived sample memos — not a placeholder
- Repo created 2026-11-16 (meets the 1-day bar), MIT, structure credited to
  TauricResearch/TradingAgents & virattt/ai-hedge-fund with explicit non-affiliation

PR 执行命令（owner 跑）：

```bash
# 1) fork 一次（浏览器或 gh）
# 2) 从 fork 提交：
cd /tmp && git clone --depth 1 git@ssh.github.com:vicfei/awesome-dsh-plugin.git && cd awesome-dsh-plugin
git checkout -b add-dsh-tradingagents
cp ~/dsh-tradingagents/docs/marketplace-submission/vicfei__dsh-TradingAgents--npm.yml data/plugins/
git add data/plugins/vicfei__dsh-TradingAgents--npm.yml
git commit -m "Add vicfei/dsh-TradingAgents (multi-agent investment committee)"
git push -f origin add-dsh-tradingagents
# 3) 开 PR：base awesome-dsh-plugin/awesome-dsh-plugin ← vicfei:add-dsh-tradingagents，body 用上文
```

> 备选渠道（同一投稿件可复用）：0xsline/awesome-deepseek-harness（1.4k★）、
> polang233/dsh-plugin-index（256★）、bradeGithub/DSH-Plugins-Marketplace（206★）——
> 待 awesome-dsh-plugin 主渠道过审后再逐个补，避免同日多仓自我推广观感。
