#!/usr/bin/env python3
"""render_session_svg — a real-data session map for an IC-MEMO (showcase + product)

Parses an archived committee memo (guest table, yaml verdict, per-section tag
counts, provenance footer) and renders an SVG: the role pipeline with how much
evidence each stage produced, the guest seats with stance colors and conviction
bars, and the PM verdict banner. Deterministic; English labels. The footer's
token segment is optional (pre-cost-guard memos carry calls only).
"""
import argparse, re, sys

C = {"bg": "#0d1117", "panel": "#161b22", "fg": "#c9d1d9", "dim": "#8b949e",
     "accent": "#f2cc60", "line": "#30363d",
     "BUY": "#3fb950", "OVERWEIGHT": "#56d364", "HOLD": "#e3b341",
     "UNDERWEIGHT": "#e3b341", "SELL": "#f85149", "PASS": "#a5d6ff", "REVIEW": "#f85149"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse(memo):
    def g(pat, default=""):
        m = re.search(pat, memo, re.M)
        return m.group(1) if m else default
    d = {"ticker": g(r"^ticker: (.+)$"), "decision": g(r"^decision: (.+)$"),
         "confidence": g(r"^confidence: (\d+)"), "as_of": g(r"^as_of: (.+)$")}
    d["guests"] = [(m[0], m[1], m[2]) for m in re.findall(r"^\| ([A-Z][^|]+?) \| (\w+) \| (\d+) \|", memo, re.M)
                   if m[0] != "Guest"]
    foot = re.search(r"\*(\d+)s · (\d+) calls(?: · ([\d,]+) in / ([\d,]+) out tokens)?(.*)\*", memo)
    d["footer"] = tuple((x or "") for x in (foot.groups() if foot else ("?", "?", None, None, "")))
    # Line walker: only the known template headers switch sections — LLM memos
    # contain stray '# ...'/'## ...' lines mid-body, and find()-based splitting
    # shatters on them; stray lines stay in the current section.
    switchers = (("### Bull rebuttal", "bull"), ("## 3", "guests"), ("Guest critiques", "guests"),
                 ("## 4", "risk"), ("Risk guardrails", "risk"),
                 ("## 5", "pm"), ("Portfolio manager verdict", "pm"),
                 ("### Bull", "bull"), ("### Bear", "bear"), ("## 1", "analyst"))
    d["tags"] = {}
    cur = None
    for line in memo.splitlines():
        for head, key in switchers:
            if line.startswith(head):
                cur = key
                break
        else:
            if cur:
                bucket = d["tags"].setdefault(cur, {})
                for t in "ABRGP":
                    n = len(re.findall(rf"\[{t}\d", line))
                    if n:
                        bucket[t] = bucket.get(t, 0) + n
    return d


def render(d, title):
    W, H = 960, 560
    tok = f" · {esc(d['footer'][2])} in / {esc(d['footer'][3])} out tokens" if d["footer"][2] else ""
    s, calls = d["footer"][0], d["footer"][1]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Menlo,Consolas,monospace">',
         f'<defs><marker id="a" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">'
         f'<path d="M0,0 L7,3 L0,6 z" fill="{C["dim"]}"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>',
         f'<text x="24" y="34" font-size="17" fill="{C["fg"]}" font-weight="bold">{esc(title)}</text>',
         f'<text x="{W-24}" y="34" font-size="12" fill="{C["dim"]}" text-anchor="end">one real session · parsed from the archived IC-MEMO</text>']
    roles = [("analyst", "A"), ("bull", "B"), ("bear", "R"), ("risk", "G"), ("PM", "")]
    x, y, bw, bh, gap = 24, 64, 158, 64, 22
    for i, (role, tag) in enumerate(roles):
        cnt = d["tags"].get(role if role != "PM" else "pm", {})
        badge = " · ".join(f"[{k}]×{v}" for k, v in sorted(cnt.items())) or ("final" if role == "PM" else "")
        o.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="{C["panel"]}" stroke="{C["line"]}"/>')
        o.append(f'<text x="{x+bw/2}" y="{y+26}" font-size="14" fill="{C["accent"]}" text-anchor="middle">{esc(role.upper())}</text>')
        o.append(f'<text x="{x+bw/2}" y="{y+46}" font-size="10" fill="{C["dim"]}" text-anchor="middle">{esc(badge)}</text>')
        if i < len(roles) - 1:
            o.append(f'<line x1="{x+bw}" y1="{y+bh/2}" x2="{x+bw+gap}" y2="{y+bh/2}" stroke="{C["dim"]}" stroke-width="1.4" marker-end="url(#a)"/>')
        x += bw + gap
    gx, gy = 24, 172
    gh = 40 + 34 * max(len(d["guests"]), 1)
    o.append(f'<rect x="{gx}" y="{gy}" width="470" height="{gh}" rx="10" fill="{C["panel"]}" stroke="{C["line"]}"/>')
    o.append(f'<text x="{gx+16}" y="{gy+26}" font-size="12" fill="{C["accent"]}">GUEST SEATS — critiquing the debate</text>')
    for i, (name, stance, conv) in enumerate(d["guests"]):
        yy = gy + 48 + i * 34
        col = C.get(stance, C["fg"])
        o.append(f'<rect x="{gx+16}" y="{yy-12}" width="86" height="20" rx="5" fill="{col}" opacity="0.18"/>')
        o.append(f'<text x="{gx+59}" y="{yy+2}" font-size="11" fill="{col}" text-anchor="middle">{esc(stance)}</text>')
        o.append(f'<rect x="{gx+112}" y="{yy-10}" width="{int(conv)*1.7}" height="10" rx="3" fill="{col}" opacity="0.55"/>')
        nx = min(gx + 112 + int(conv) * 1.7 + 6, gx + 470 - 176)  # keep the row inside the panel
        o.append(f'<text x="{int(nx)}" y="{yy}" font-size="11" fill="{C["fg"]}">{esc(name)} @{conv}</text>')
    vx, vy, vw = 520, 172, 416
    o.append(f'<rect x="{vx}" y="{vy}" width="{vw}" height="{gh}" rx="10" fill="{C["panel"]}" stroke="{C.get(d["decision"], C["line"])}" stroke-width="1.6"/>')
    o.append(f'<text x="{vx+18}" y="{vy+28}" font-size="12" fill="{C["accent"]}">PORTFOLIO MANAGER VERDICT</text>')
    o.append(f'<text x="{vx+18}" y="{vy+62}" font-size="26" fill="{C.get(d["decision"], C["fg"])}" font-weight="bold">{esc(d["decision"])} <tspan font-size="15" fill="{C["dim"]}">@ {esc(d["confidence"])} confidence</tspan></text>')
    o.append(f'<text x="{vx+18}" y="{vy+92}" font-size="11" fill="{C["dim"]}">the guest split itself is evidence the call</text>')
    o.append(f'<text x="{vx+18}" y="{vy+108}" font-size="11" fill="{C["dim"]}">cannot be made on this data — PASS, with reasons</text>')
    o.append(f'<text x="{vx+18}" y="{vy+134}" font-size="11" fill="{C["dim"]}">invalidation triggers in the memo define what reopens it</text>')
    o.append(f'<line x1="24" y1="{H-46}" x2="{W-24}" y2="{H-46}" stroke="{C["line"]}"/>')
    o.append(f'<text x="24" y="{H-24}" font-size="11" fill="{C["dim"]}">provenance: {esc(s)}s · {esc(calls)} calls{tok} · deepseek-chat · temperature=0 · as of {esc(d["as_of"])}</text>')
    o.append(f'<text x="{W-24}" y="{H-24}" font-size="11" fill="{C["dim"]}" text-anchor="end">not investment advice</text>')
    o.append("</svg>")
    return "".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("memo")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    d = parse(open(args.memo, encoding="utf-8").read())
    if not d["decision"]:
        sys.exit("not an IC-MEMO (no decision yaml)")
    out = args.out or args.memo.rsplit(".", 1)[0] + ".session.svg"
    open(out, "w", encoding="utf-8").write(render(d, f"IC-MEMO · {d['ticker']} · committee session map"))
    print(f"session svg -> {out}")


if __name__ == "__main__":
    main()
