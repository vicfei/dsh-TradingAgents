#!/usr/bin/env node
// dsh-tradingagents CLI —— JS 壳 spawn 包内 Python 引擎（dsh-laya sidecar 先例）
//
//   tradingagents demo [--guests all] [--save]      # 离线合成数据开庭
//   tradingagents card --ticker NVDA [--committee]  # 取真数据卡（OpenBB 富卡）可直开庭
//   tradingagents --ticker X --data card.json ...   # 引擎参数全透传
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argv = process.argv.slice(2);
const [cmd, ...rest] = argv;

let script, pass;
if (cmd === "card") {
  script = "fetch_card.py";
  pass = rest;
} else if (cmd === "settle") {
  script = "ledger.py";        // track-record loop: index memos, settle due entries
  pass = ["--index", "--settle", ...rest];
} else if (cmd === "demo") {
  script = "tradingagents.py";
  pass = ["--ticker", "DEMO", ...rest];
} else {
  script = "tradingagents.py";
  pass = argv;
}

// 纪要/数据卡落调用方 cwd（引擎识别的环境出口；缺省会落包目录，不可写且难找回）
const env = {
  ...process.env,
  TRADINGAGENTS_MEMOS: path.join(process.cwd(), "memos"),
  TRADINGAGENTS_CARDS: path.join(process.cwd(), "cards"),
  TRADINGAGENTS_LEDGER: path.join(process.cwd(), "memos", "ledger.json"),
};

const r = spawnSync("python3", [path.join(root, "scripts", script), ...pass], {
  stdio: "inherit",
  env,
});
process.exit(r.status ?? 1);
