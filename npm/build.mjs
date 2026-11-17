// prepack：从仓内同步引擎与资产进包（npm/ 下不提交生成物，防漂移——publish 永远取最新）
import { cpSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");

for (const d of ["scripts", "templates", "data"]) {
  rmSync(path.join(here, d), { recursive: true, force: true });
}
cpSync(path.join(repo, "scripts"), path.join(here, "scripts"), { recursive: true });
cpSync(path.join(repo, "templates"), path.join(here, "templates"), { recursive: true });
mkdirSync(path.join(here, "data"), { recursive: true });
cpSync(path.join(repo, "data", "demo"), path.join(here, "data", "demo"), { recursive: true });
cpSync(path.join(repo, "LICENSE"), path.join(here, "LICENSE"));
rmSync(path.join(here, "scripts", "__pycache__"), { recursive: true, force: true });
console.log("staged scripts/ templates/ data/demo/ LICENSE from repo root");
