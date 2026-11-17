/**
 * dsh-tradingagents host plugin (0.2.0, issue #10): the committee as typed tools.
 *
 * Registers two agent tools on `ctx.tools` once the profile composes:
 *   committee_session — convene the multi-agent investment committee on a ticker
 *   verdict_settle    — index archived memos and settle due verdicts (alpha vs benchmark)
 *
 * The tools spawn the bundled Python engine (same scripts the CLI uses); artifacts
 * (memos, cards, ledger) land under the calling process's cwd, exactly like the CLI.
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineTool } from "@deepseek-ai/dsh-tools";

export const name = "tradingagents";
export const inject = ["tools"];

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PY = "python3";

function run(script, args, timeoutMs = 600_000) {
  const env = {
    ...process.env,
    TRADINGAGENTS_MEMOS: path.join(process.cwd(), "memos"),
    TRADINGAGENTS_CARDS: path.join(process.cwd(), "cards"),
    TRADINGAGENTS_LEDGER: path.join(process.cwd(), "memos", "ledger.json"),
  };
  const r = spawnSync(PY, [path.join(ROOT, "scripts", script), ...args],
                      { encoding: "utf8", timeout: timeoutMs, env, maxBuffer: 16 * 1024 * 1024 });
  if (r.error) throw new Error(`${script}: ${r.error.message}`);
  if (r.status !== 0) throw new Error(`${script} exited ${r.status}: ${(r.stderr || "").slice(-400)}`);
  return (r.stdout || "").trim();
}

const LANG = {
  type: "string", enum: ["en", "zh"],
  description: "Output language (default en).",
};

export async function apply(ctx) {
  ctx.tools.register(defineTool({
    name: "committee_session",
    description:
      "Convene the multi-agent investment committee (analyst → bull/bear debate → risk guardrails " +
      "→ portfolio manager) on a ticker and return the full IC-MEMO with its evidence-tagged verdict " +
      "(BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL, PASS when evidence is insufficient). " +
      "Uses a zero-key data card (CBOE/SEC/nasdaq via OpenBB; Tencent fallback) unless a card file is given. " +
      "Takes ~30-90s. Not investment advice.",
    parameters: {
      ticker: { type: "string", required: true, description: "Ticker symbol, e.g. NVDA or 600519." },
      data: { type: "string", description: "Existing data-card JSON path; omit to build one from live zero-key sources." },
      guests: { type: "string", description: "Guest personas comma-separated or 'all' (warren_buffett, charlie_munger, peter_lynch, cathie_wood)." },
      rounds: { type: "number", description: "Debate rounds (default 1; each extra round adds a bear cross-exam + bull response)." },
      portfolio: { type: "string", description: "Portfolio JSON path — holdings-aware verdict (three-state discipline)." },
      date: { type: "string", description: "As-of historical date YYYY-MM-DD (US rich-card path only)." },
      lang: LANG,
    },
    output: {
      schema: { type: "object", additionalProperties: false,
                properties: { memo: { type: "string", required: true } } },
      render: (_args, value) => [{
        type: "text",
        text: (value.memo.split("\n").find(l => l.startsWith("decision:"))
              || "committee session complete — see the memo for the evidence-tagged verdict"),
      }],
    },
    execute(args) {
      let data = args.data;
      if (!data) {
        const card = path.join(process.cwd(), "cards", `${args.ticker}.json`);
        if (!existsSync(card)) {
          run("fetch_card.py", ["--ticker", args.ticker, ...(args.date ? ["--date", args.date] : []),
                                ...(args.lang ? ["--lang", args.lang] : [])]);
        }
        data = card;
      }
      const extra = [
        ...(args.guests ? ["--guests", args.guests] : []),
        ...(args.rounds ? ["--rounds", String(args.rounds)] : []),
        ...(args.portfolio ? ["--portfolio", args.portfolio] : []),
        ...(args.lang ? ["--lang", args.lang] : []),
        "--save",
      ];
      return { memo: run("tradingagents.py", ["--ticker", args.ticker, "--data", data, ...extra]) };
    },
  }));

  ctx.tools.register(defineTool({
    name: "verdict_settle",
    description:
      "Settle the committee's due verdicts: index archived IC-MEMOs into the verdict ledger and, for " +
      "every decision whose 5-trading-day holding window has traded, record raw return + alpha vs its " +
      "benchmark (SPY / SSE Composite) plus a short reflection. Run this periodically; the next " +
      "committee session reads the lessons.",
    parameters: {},
    output: {
      schema: { type: "object", additionalProperties: false,
                properties: { result: { type: "string", required: true } } },
      render: (_args, value) => [{ type: "text", text: value.result.split("\n").slice(-3).join("\n") }],
    },
    execute() {
      const out = run("ledger.py", ["--index", "--settle"]);
      return { result: out || "nothing due for settlement" };
    },
  }));
}
