# npm 0.1.0 发布指引（owner 手动，2FA OTP）

包已就绪：`npm/` 目录，`npm pack` 实测干净（13 文件 43KB，无 pycache），临时 prefix
安装冒烟通过（demo 开庭 + card 取数 + 纪要/卡片落调用方 cwd）。

## 步骤

```bash
cd ~/dsh-tradingagents/npm
npm publish --registry https://registry.npmjs.org/   # 必须官方源（腾讯镜像只读）；OTP 按提示输入
```

- `prepack` 钩子自动从仓内同步 scripts/ templates/ data/demo/ LICENSE——**永远取当前
  工作树最新**，无需手工拷贝。
- 发布后验证：`npm view dsh-tradingagents version` → 0.1.0；然后
  `npm i -g dsh-tradingagents && tradingagents demo --save` 全新环境冒烟。

## 结构（weknora-ops 已验证的分发车模式）

| 件 | 作用 |
|---|---|
| `bin/tradingagents` | JS 壳 spawn 包内 Python 引擎（dsh-laya sidecar 先例） |
| `skills/dsh-tradingagents/SKILL.md` | DSH 技能，由 dsh-skill-filesystem 从 ~/.dsh/skills/ 发现 |
| `cordis.patch.yml` | 空 patch `[]`——`dsh.bundle.patch` 身份标记，不含 cordis 插件模块 |
| `scripts/*.py` + `data/demo/` | 引擎与离线 DEMO 数据卡 |

用户装技能：`ln -s "$(npm root -g)/dsh-tradingagents/skills/dsh-tradingagents" ~/.dsh/skills/dsh-tradingagents`

## 版本策略

0.0.1=占位锁名（已发）→ **0.1.0=首个真插件包**（引擎 v1：富数据卡 + 客座席位）。
后续 0.1.x 修 bug、0.2.0 加 cordis typed-tools 完整插件模块（ROADMAP M1 剩余项）。
