#!/usr/bin/env python3
"""Diagrams for the GENFI and SQUARE plan pages. Each plan page carries 8 mermaid-cloud macros
(01-goal, 02-today, 03-target, 04-plan, 05-done, 06-effort, 07-related, 08-risks) with no
attachments. This script builds each diagram from the page's own text (goal sentences, today
facts, the Jago-vs-ours table, the step list, done-when items, effort lines, related plans,
risk/mitigation pairs), renders them, uploads source + PNG under the macro's filename and
verifies that every macro's revision matches the attachment version.

Usage: agency_plan_diagrams.py [--upload | --verify] [page_id ...]
"""
import os, re, sys, html, json, subprocess, textwrap
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import publish

HOT = 'classDef hot fill:#ffe1e1,stroke:#c00'; GOOD = 'classDef good fill:#e3f5e1,stroke:#2a7'; NOW = 'classDef now fill:#fff4cc,stroke:#b80'
PARENTS = {"GENFI": "2874998826", "SQUARE": "2875260970"}
OUT = os.path.join(D, "agency-plans")

def text_lines(storage):
    s = re.sub(r'<ac:structured-macro[^>]*ac:name="mermaid-cloud".*?</ac:structured-macro>', "", storage, flags=re.S)
    s = re.sub(r"<(pre|ac:plain-text-body)[^>]*>.*?</\1>", "\n[code]\n", s, flags=re.S)
    s = re.sub(r"</(tr|p|li)>", "\n", s); s = re.sub(r"<h2[^>]*>", "\n## ", s); s = re.sub(r"<h3[^>]*>", "\n### ", s); s = re.sub(r"</h\d>", "\n", s)
    s = re.sub(r"<td[^>]*>", "\n| ", s); s = re.sub(r"<th[^>]*>", "\n| ", s); s = re.sub(r"<[^>]+>", " ", s)
    return [re.sub(r"\s+", " ", html.unescape(l)).strip() for l in s.split("\n") if l.strip()]

def sections(lines):
    sec = {}; cur = None
    for l in lines:
        if l.startswith("## "): cur = l[3:].strip(); sec[cur] = []; continue
        if cur: sec[cur].append(l)
    def get(prefix):
        for k, v in sec.items():
            if k.lower().startswith(prefix.lower()): return v
        return []
    return get

def clean(t):
    t = t.replace('"', "'").replace(";", ",").replace("<", "&lt;").replace(">", "&gt;").replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def box(t, width=30, maxchars=110):
    t = clean(t)
    if len(t) > maxchars: t = t[:maxchars - 1].rsplit(" ", 1)[0] + " …"
    return "<br/>".join(textwrap.wrap(t, width)) or "…"

def grid(prefix, labels, cls, width=34, maxchars=130):
    nodes = [f'  {prefix}{i}["{box(t, width, maxchars)}"]:::{cls}' for i, t in enumerate(labels)]
    rows = []
    for r in range(0, len(labels), 2):
        ids = " & ".join(f"{prefix}{i}" for i in range(r, min(r + 2, len(labels))))
        rows.append(f'  subgraph row{prefix}{r}[" "]\n    direction LR\n    {ids}\n  end')
    chain = " ~~~ ".join(f"row{prefix}{r}" for r in range(0, len(labels), 2))
    return "flowchart TD\n" + "\n".join(nodes) + "\n" + "\n".join(rows) + "\n  " + chain

def first_sentences(paras, n=4):
    out = []
    for p in paras:
        if p.startswith("|") or p.startswith("###") or p == "[code]": continue
        for s in re.split(r"(?<=[.!?])\s+", p):
            if len(s) > 15: out.append(s)
            if len(out) >= n: return out
    return out

def items(paras, n=7, skip_tables=True):
    out = []
    for p in paras:
        if p == "[code]" or p.startswith("###"): continue
        if p.startswith("|"):
            if skip_tables: continue
            p = p[2:]
        if p.lower().startswith("revision read") or p.lower().startswith("shared plan."): continue
        if len(p) > 20: out.append(p)
        if len(out) >= n: break
    return out

def pairs_after(paras, left, right, n=6):
    out = []; i = 0
    cell = lambda k: paras[k][2:].strip() if k < len(paras) and paras[k].startswith("| ") else None
    while i < len(paras) and not (cell(i) or "").lower().startswith(left.lower()): i += 1
    if i >= len(paras): return out
    hdr = [cell(i)]; i += 1
    while cell(i) is not None and not hdr[-1].lower().startswith(right.lower()) and len(hdr) < 5: hdr.append(cell(i)); i += 1
    ridx = next((k for k, h in enumerate(hdr) if h.lower().startswith(right.lower())), 1); ncols = max(len(hdr), 2)
    while i + ncols - 1 < len(paras) and all(cell(i + k) is not None for k in range(ncols)):
        l, r = cell(i), cell(i + ridx)
        if len(l) < 12 and len(r) < 20: break  # header of a following table
        out.append((l, r)); i += ncols
        if len(out) >= n: break
    return out

def steps(paras):
    out = []
    for p in paras:
        m = re.match(r"### (Step \d+[^:]*):\s*(.*)", p)
        if m: out.append((m.group(1).replace(" (", "<br/>("), m.group(2)))
    return out

def diagrams(title, lines):
    get = sections(lines); d = {}
    app = "GENFI" if title.startswith("GENFI") else "SQUARE"
    goal = first_sentences(get("Goal"), 4)
    d["01-goal"] = "flowchart LR\n" + "\n".join(f'  g{i}["{box(s, 28, 120)}"]:::good' for i, s in enumerate(goal)) + "\n  " + " --> ".join(f"g{i}" for i in range(len(goal))) + f"\n  {GOOD}"
    today = items(get("Where we are today"), 7)
    d["02-today"] = grid("t", today, "hot") + f"\n  {HOT}"
    pr = pairs_after(get("Target"), "Jago pattern", "Our adaptation", 6)
    if not pr: pr = [(s, "") for s in first_sentences(get("Target"), 4)]
    rows = []
    for i, (l, r) in enumerate(pr):
        rows.append(f'  j{i}["{box(l, 28, 100)}"]:::now')
        if r: rows.append(f'  b{i}["{box(r, 28, 110)}"]:::good'); rows.append(f"  j{i} -->|adapt| b{i}")
    d["03-target"] = "flowchart LR\n  subgraph jg[\"Jago (reference)\"]\n    direction TB\n" + "\n".join(f"    j{i}" for i in range(len(pr))) + f"\n  end\n  subgraph bf[\"{app} target\"]\n    direction TB\n" + "\n".join(f"    b{i}" for i in range(len(pr)) if pr[i][1]) + "\n  end\n" + "\n".join(rows) + f"\n  {NOW}\n  {GOOD}"
    st = steps(get("Plan"))
    d["04-plan"] = "flowchart TD\n" + "\n".join(f'  s{i}["{box(a, 26, 60)}<br/>{box(b, 30, 90)}"]:::now' for i, (a, b) in enumerate(st)) + "\n  " + " --> ".join(f"s{i}" for i in range(len(st))) + f"\n  {NOW}"
    done = items(get("Done when"), 7)
    d["05-done"] = grid("d", done, "good") + f"\n  {GOOD}"
    eff = items(get("Effort and owner"), 6)
    d["06-effort"] = "flowchart LR\n" + "\n".join(f'  e{i}["{box(s, 30, 120)}"]:::now' for i, s in enumerate(eff)) + "\n  " + " ~~~ ".join(f"e{i}" for i in range(len(eff))) + f"\n  {NOW}"
    rel = items(get("Depends on"), 7)
    d["07-related"] = f'flowchart LR\n  me["{box(title, 26, 60)}"]:::good\n' + "\n".join(f'  r{i}["{box(s, 28, 100)}"]\n  me --> r{i}' for i, s in enumerate(rel)) + f"\n  {GOOD}"
    rk = pairs_after(get("Risks"), "Risk", "Mitigation", 6)
    d["08-risks"] = "flowchart LR\n" + "\n".join(f'  k{i}["{box(l, 28, 100)}"]:::hot\n  m{i}["{box(r, 28, 110)}"]:::good\n  k{i} -->|mitigate| m{i}' for i, (l, r) in enumerate(rk)) + f"\n  {HOT}\n  {GOOD}"
    return d

def render(path_mmd, path_png):
    r = subprocess.run(["mise", "x", "node@22", "--", "npx", "-y", "@mermaid-js/mermaid-cli", "-p", os.path.join(D, "puppeteer.json"), "-b", "white", "-s", "2", "-i", path_mmd, "-o", path_png], capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(path_png), r.stderr[-200:]

def main():
    mode = "render"; args = [a for a in sys.argv[1:]]
    if "--upload" in args: mode = "upload"; args.remove("--upload")
    if "--verify" in args: mode = "verify"; args.remove("--verify")
    pages = []
    for name, pid in PARENTS.items():
        for p in publish.req("GET", f"/rest/api/content/{pid}/child/page?limit=50")["results"]:
            if not args or p["id"] in args: pages.append((p["id"], p["title"]))
    report = []
    for pid, title in sorted(pages, key=lambda x: x[1]):
        page = publish.req("GET", f"/rest/api/content/{pid}?expand=body.storage"); s = page["body"]["storage"]["value"]
        macros = re.findall(r'<ac:parameter ac:name="filename">([^<]+)</ac:parameter><ac:parameter ac:name="revision">(\d+)', s)
        if not macros: report.append(f"{title}: no macros, skipped"); continue
        atts = {x["title"]: x["version"]["number"] for x in publish.req("GET", f"/rest/api/content/{pid}/child/attachment?limit=200&expand=version")["results"]}
        if mode == "verify":
            bad = [(f, r) for f, r in macros if atts.get(f) != int(r) or f + ".png" not in atts]
            report.append(f"{title}: {len(macros)} macros, {len(atts)} attachments, mismatches {bad}"); continue
        out = os.path.join(OUT, re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")); os.makedirs(out, exist_ok=True)
        d = diagrams(title, text_lines(s)); fails = []
        for stem, _rev in macros:
            if stem not in d: fails.append((stem, "no generator")); continue
            mmd = os.path.join(out, stem + ".mmd"); png = os.path.join(out, stem + ".png")
            open(mmd, "w").write(d[stem].strip() + "\n")
            ok, err = render(mmd, png)
            if not ok: fails.append((stem, err)); continue
            if mode == "upload":
                if stem in atts: fails.append((stem, f"attachment exists v{atts[stem]}; not re-uploading")); continue
                v = publish.upload(pid, stem, open(mmd, "rb").read(), "text/plain"); publish.upload(pid, stem + ".png", open(png, "rb").read(), "image/png")
                if v != int(_rev): fails.append((stem, f"uploaded v{v}, macro expects {_rev}"))
        report.append(f"{title}: {len(macros)} macros, {mode}, problems {fails}")
    print("\n".join(report))

if __name__ == "__main__": main()
