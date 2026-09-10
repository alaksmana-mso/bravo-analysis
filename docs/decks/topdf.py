#!/usr/bin/env python3
"""Wrap an Artifact deck fragment in a full HTML document and render it to PDF via headless Chrome."""
import pathlib, subprocess, sys, tempfile, os

D = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# The Artifact runtime wraps a fragment in this skeleton; reproduce it so the
# local render matches the published page.
HEAD_RESET = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{color-scheme:light}
body{margin:0;font:14px system-ui,-apple-system,sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
</style>"""

def render(slug):
    frag = (D / f"{slug}.html").read_text()
    doc = f"<!doctype html>\n<html lang=\"en\" data-theme=\"light\">\n<head>\n{HEAD_RESET}\n{frag.split(chr(10)+'<main')[0]}\n</head>\n<body>\n<main{frag.split(chr(10)+'<main',1)[1]}\n</body>\n</html>\n"
    tmp = pathlib.Path(tempfile.mkdtemp()) / f"{slug}.print.html"
    tmp.write_text(doc)
    out = D / "pdf" / f"{slug}.pdf"
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           # the window size sets the viewport width that print media queries see;
           # left at Chrome's 800x600 default, the layout collapses to its narrow form
           "--window-size=1247,703",
           "--no-pdf-header-footer", "--virtual-time-budget=20000",
           "--run-all-compositor-stages-before-draw",
           f"--print-to-pdf={out}", tmp.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not out.exists():
        print(f"  FAILED {slug}\n{r.stderr[-1500:]}"); return None
    return out

if __name__ == "__main__":
    for slug in sys.argv[1:]:
        p = render(slug)
        if p: print(f"  {p.name:34s} {p.stat().st_size/1024:8.0f} KB")
