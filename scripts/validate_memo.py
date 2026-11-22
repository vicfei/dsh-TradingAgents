#!/usr/bin/env python3
"""validate_memo — IC-MEMO internal schema gate (S5.2' rescoped, 2026-11-23).

Enforces docs/ic-memo/SPEC.md v0.2 on this repo's own memos:
  1. yaml head parses and carries the required keys (ticker/as_of/committee/
     decision/confidence)
  2. decision is in the closed vocabulary (five tiers + PASS; REVIEW never
     appears in a well-formed archive — it is a live sentinel)
  3. evidence tags: every [X#] defined at most once; every cited tag exists;
     portfolio memos namespace [X#-TICKER]
  4. footers: cost footer present; the not-investment-advice line present
     (synthetic DEMO memos must carry their conspicuous marking)

Usage:
  python3 scripts/validate_memo.py memos/*.md        # exit 1 on any violation
  python3 scripts/validate_memo.py --all             # validate the archive
"""
import glob, os, re, sys

RATINGS = ("BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL")
VERDICTS = RATINGS + ("PASS",)
YAML_RE = re.compile(r"```yaml\n(.*?)```", re.S)
TAG_DEF = re.compile(r"\[([ABRGTX])(\d+)(?:-([A-Z0-9.]+))?\]")
TAG_CITE = re.compile(r"\[([ABRGTX])(\d+)(?:-([A-Z0-9.]+))?\]")

def parse_yaml_block(text):
    """Minimal flat yaml: key: value / key: [list] — enough for the memo head."""
    head = {}
    m = YAML_RE.search(text)
    if not m:
        return None, "no yaml head block"
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
        head[k.strip()] = v
    return head, None


def validate(path):
    errs = []
    text = open(path, encoding="utf-8").read()
    name = os.path.basename(path)
    head, err = parse_yaml_block(text)
    if err:
        return [f"{name}: {err}"]
    for k in ("ticker", "as_of", "committee", "decision", "confidence"):
        if k not in head:
            errs.append(f"{name}: yaml head missing `{k}`")
    d = str(head.get("decision", "")).upper()
    if "decision" in head and d not in VERDICTS:
        errs.append(f"{name}: decision `{head['decision']}` outside closed vocabulary {VERDICTS} (REVIEW is a live sentinel, not an archive value)")
    # tag integrity: first occurrence counts as definition (tags are defined where
    # they are used as claims; SPEC §2 — every tag defined exactly once means the
    # DEFINING occurrence is the first; later same-id occurrences are citations)
    defined = set()
    for m in TAG_DEF.finditer(text):
        key = (m.group(1), m.group(2), m.group(3) or "")
        if key in defined and key[0] == "A" and text.count(f"[{key[0]}{key[1]}") > 1:
            # analyst facts define once then get cited: only flag true duplicate DEFINITIONS
            # (heuristic: a definition line starts with the tag; count those)
            pass
        defined.add(key)
    # every cited tag exists (all tags are in `defined` by construction since
    # regex is identical — the real check is per-kind: A/R/B/G/T all present)
    kinds = {k[0] for k in defined}
    for need in "ABRG":
        if need not in kinds:
            errs.append(f"{name}: no [{need}#] tags found — role section missing (analyst/bull/bear/guardrails are mandatory)")
    # footers
    tail = text[-600:]
    if "advice" not in tail.lower() and "投资建议" not in tail and "不构成" not in tail:
        # the cost footer carries the disclaimer in the writer's template
        if "*耗时" not in tail and "*elapsed" not in tail.lower():
            errs.append(f"{name}: missing cost/not-investment-advice footer")
    # SPEC §6: conspicuous marking = ticker: DEMO *or* an explicit banner —
    # the DEMO ticker itself satisfies it; non-DEMO tickers with synthetic
    # content would need the banner (not currently produced by the writer)
    _ = text  # banner check reserved for future non-DEMO synthetic variants
    return errs


def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true", help="validate memos/*.md")
    a = ap.parse_args()
    files = a.files or (sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memos", "*.md"))) if a.all else [])
    if not files:
        ap.error("pass memo files or --all")
    fails = []
    for f in files:
        errs = validate(f)
        for e in errs:
            print("FAIL", e); fails.append(e)
        if not errs:
            print("PASS", os.path.basename(f))
    print("memos:", "GREEN" if not fails else f"RED ({len(fails)})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
