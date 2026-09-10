#!/usr/bin/env python3
"""Measure each slide's natural height at print-page width, via headless Chrome --dump-dom.

The deck's print rules live in one @media print block. To measure them on-screen we
re-emit that block's contents scoped under html[data-printsim], strip @page, and pin
the viewport to the print page's CSS pixel box (330mm x 186mm at 96dpi).
"""
import json, pathlib, re, subprocess, sys, tempfile

D = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE_W, PAGE_H = 330 / 25.4 * 96, 186 / 25.4 * 96      # 1247.24 x 703.18 px

def printsim(css):
    """Extract the @media print block and rescope it for on-screen simulation."""
    i = css.index("@media print{")
    depth, j = 0, i + len("@media print")
    while True:
        if css[j] == "{": depth += 1
        elif css[j] == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    block = css[i + len("@media print{"):j]
    block = re.sub(r"@page\{[^}]*\}", "", block)
    out = []
    for rule in re.findall(r"([^{}]+)\{([^{}]*)\}", block):
        sels, body = rule
        sels = ",".join("html[data-printsim] " + s.strip() for s in sels.split(",") if s.strip())
        out.append(f"{sels}{{{body}}}")
    return "\n".join(out)

def measure(slug):
    frag = (D / f"{slug}.html").read_text()
    head, main = frag.split("\n<main", 1)
    css = (D / "_deck.css").read_text()
    doc = f"""<!doctype html>
<html lang="en" data-theme="light" data-printsim>
<head><meta charset="utf-8">
<style>:root{{color-scheme:light}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}</style>
{head}
<style>
html[data-printsim] body{{width:{PAGE_W}px}}
{printsim(css)}
</style>
</head><body>
<main{main}
<script>
window.addEventListener('load', function(){{
  setTimeout(function(){{
    var out = [].map.call(document.querySelectorAll('.slide'), function(s){{
      return Math.round(s.getBoundingClientRect().height);
    }});
    document.title = 'M:' + JSON.stringify(out);
  }}, 1200);
}});
</script>
</body></html>"""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "m.html"
    tmp.write_text(doc)
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                        f"--window-size={int(PAGE_W)},{int(PAGE_H)}",
                        "--virtual-time-budget=15000", "--dump-dom", tmp.as_uri()],
                       capture_output=True, text=True, timeout=180)
    m = re.search(r"<title>M:(\[[^<]*\])</title>", r.stdout)
    if not m:
        print(f"  {slug}: measurement failed"); return None
    return json.loads(m.group(1))

if __name__ == "__main__":
    result = {}
    for slug in sys.argv[1:]:
        h = measure(slug)
        if h is None: continue
        result[slug] = h
        over = [(i + 1, v, round(PAGE_H / v, 3)) for i, v in enumerate(h) if v > PAGE_H]
        print(f"{slug}: {len(h)} slides, {len(over)} over {PAGE_H:.0f}px")
        for i, v, k in over:
            print(f"    slide {i:2d}  {v:5d}px  needs zoom {k}")
    (D / "heights.json").write_text(json.dumps(result, indent=1))
