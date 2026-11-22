#!/usr/bin/env python3
"""verdict_card — IC-MEMO → dsh-ui summary card (2026-11-23).

Renders the verdict head (ticker, decision, confidence, top guardrails)
as a ```dsh-ui fenced block — the compact inline projection of a full
IC-MEMO for DeepSeek Harness replies (renders via dsh-genui when the
host has it; plain markdown fence otherwise).

Discipline (docs/ic-memo SPEC §2/§6): numbers only from the memo itself;
synthetic DEMO memos keep their marking ON the card; every card carries
the not-investment-advice line.

Usage:
  python3 scripts/verdict_card.py memos/NVDA-2026-11-13.md
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_memo import parse_yaml_block, YAML_RE  # reuse the schema layer

RATINGS = ("BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL")

TONE = {"BUY": "success", "OVERWEIGHT": "success", "HOLD": "info",
        "UNDERWEIGHT": "warning", "SELL": "danger", "PASS": "muted"}


def guardrail_quotes(text, limit=3):
    """First sentence of each [G#] guardrail, capped — the tags the PM cites."""
    out = []
    for m in re.finditer(r"\[G(\d+)\][ \t]*([^\n]{10,})", text):
        snippet = re.split(r"[。;；.—]| — ", m.group(2).strip())[0]
        out.append(f"[G{m.group(1)}] {snippet[:80]}")
        if len(out) >= limit:
            break
    return out


def card(path):
    text = open(path, encoding="utf-8").read()
    head, err = parse_yaml_block(text)
    if err:
        sys.exit(f"validate first: {err}")
    ticker = str(head.get("ticker", "?"))
    decision = str(head.get("decision", "?")).upper()
    conf = head.get("confidence", "?")
    synthetic = ticker.upper() == "DEMO"
    items = [
        {"type": "stat", "label": f"{ticker} · {decision}" + (" · SYNTHETIC" if synthetic else ""),
         "value": f"conf {conf}", "delta": str(head.get("as_of", ""))},
    ]
    for q in guardrail_quotes(text):
        items.append({"type": "text", "size": "muted", "content": q})
    items.append({"type": "text", "size": "caption",
                  "content": "not investment advice — full reasoning in the IC-MEMO"})
    node = {"type": "card", "title": f"IC-MEMO · {ticker} · {head.get('as_of', '')}",
            "items": items}
    if synthetic:
        node["tone"] = "muted"
    return "```dsh-ui\n" + __import__("json").dumps(node, ensure_ascii=False, indent=2) + "\n```"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(card(sys.argv[1]))
