# DSH 插件 npm 包规范（逆向 jevcore-dsh@0.2.1，2026-11-16 实测）

npm 是 DSH 插件官方分发通道（`dsh plugin --profile <name> add <pkg>` 装的就是 npm 包）；
marketplace 自动索引 npm 上的 dsh 生态包（连仅含 README 的占位包都收——dsh-trading@0.0.1 即占位）。

## 包结构模板（jevcore-dsh 实测）

```
dsh-tradingagents/
  package.json          # 关键字段见下
  cordis.patch.yml      # 组件注册（profile dump 同款格式：- id/name/config）
  lib/                  # TS 编译产物（ESM），main/exports 指 lib/index.js
  skills/               # 插件可捆绑 skills（随包分发）
```

```json
{
  "name": "dsh-tradingagents",
  "version": "0.1.0",
  "type": "module",
  "main": "./lib/index.js",
  "exports": { ".": { "types": "./lib/index.d.ts", "default": "./lib/index.js" } },
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } },
  "engines": { "node": ">=20" },
  "peerDependencies": {
    "@deepseek-ai/cordis": "^4.0.2",
    "@deepseek-ai/dsh-tools": ">=0.1.2-rc.1 <0.2.0 || >=0.1.5-alpha.1 <0.2.0"
  },
  "files": ["lib", "skills", "cordis.patch.yml", "README.md", "LICENSE"]
}
```

## 要点
- `"dsh": {"bundle": {"patch": ...}}` 是插件身份标记；cordis.patch.yml 注册服务/工具/门
- Python 引擎的插件化路径：JS 插件 spawn Python 脚本（dsh-laya 先例：JS 插件 + 本地
  Python sidecar），或引擎 TS 重写（6 调用编排，1-2 天）
- 发布走官方 registry（腾讯镜像只读）；CN 网络不稳时经 SSH 中继发布（SG 节点可用）
- 版本策略：0.0.1 立即占位（防抢注，npm 囤名有前科）→ 0.1.0 WP3 真插件

## 0.1.0 落地实录（2026-11-17，本仓 npm/ 目录）

采用 **weknora-ops 已验证的分发车模式**（dsh-weknora-ops@0.2.1 结构逆向）：

- `cordis.patch.yml` = 空 patch `[]` + 说明注释——**不含 cordis 插件模块就不能走完整
  patch 注册**（强行走会在 import 期失败）；`dsh.bundle.patch` 字段保留作插件身份标记
- 实际分发面三件：`bin/tradingagents`（JS 壳 spawn 包内 Python 引擎）+
  `skills/dsh-tradingagents/SKILL.md`（由 @deepseek-ai/dsh-skill-filesystem 从
  `~/.dsh/skills/` 或 `<project>/.dsh/skills/` 发现，用户符号链接注册）+ 包内
  `scripts/ data/demo/ templates/`
- `prepack` 钩子（build.mjs）从仓内同步引擎资产——npm/ 不提交生成物，publish 永远取
  最新；打包后须清扫 `__pycache__`（files 白名单目录下的 .pyc 会进包）
- 环境出口约定：`TRADINGAGENTS_MEMOS` / `TRADINGAGENTS_CARDS`——引擎工件落调用方 cwd
  而非（可能只读的）全局包目录
- 完整 typed-tools cordis 插件模块（`dsh plugin add` 后自动注册工具面）留 0.2.0
