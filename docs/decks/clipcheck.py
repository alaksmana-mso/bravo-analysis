#!/usr/bin/env python3
"""Detect print clipping empirically: compare each slide's text against its PDF page.

The height model in measure.py/fit.py proved unreliable (the printed content box is
larger than 183mm minus padding, and `zoom` on .inner does not survive Chrome's print
path). This checks the only thing that matters: did the words reach the page.
"""
import re, subprocess, sys, pathlib, html as H
D = pathlib.Path(__file__).parent

def slide_texts(slug):
    t = (D / f"{slug}.html").read_text()
    main = t[t.index("<main"):t.index("</main>")]
    out = []
    for m in re.finditer(r'<section class="slide[^"]*"[^>]*>(.*?)</section>', main, re.S):
        body = m.group(1)
        body = re.sub(r'<(script|style)\b.*?</\1>', ' ', body, flags=re.S)
        # .cue / .rail / .hud are display:none in print — not clipping when absent
        body = re.sub(r'<(\w+) class="cue"[^>]*>.*?</\1>', ' ', body, flags=re.S)
        body = re.sub(r'<[^>]+>', ' ', body)
        txt = H.unescape(body)
        out.append(re.sub(r'\s+', ' ', txt).strip())
    return out

def page_text(slug, pg):
    r = subprocess.run(["pdftotext", "-f", str(pg), "-l", str(pg),
                        str(D / "pdf" / f"{slug}.pdf"), "-"],
                       capture_output=True, text=True)
    return re.sub(r'\s+', ' ', r.stdout)

def toks(s):
    """Distinctive words only. Table and multi-column text comes back from pdftotext in
    a different order than the DOM, so position-based matching is useless; set coverage
    is not."""
    # pdftotext drops hyphens inside words ("engineer-days" -> "engineerdays"), so
    # compare hyphen-free forms.
    return {w.replace("-", "").replace("'", "")
            for w in re.findall(r"[A-Za-z][A-Za-z'-]{5,}", s.lower())}

def check(slug, floor=0.97):
    slides = slide_texts(slug)
    bad = []
    for i, txt in enumerate(slides, start=1):
        want = toks(txt)
        if len(want) < 8:
            continue
        got = toks(page_text(slug, i))
        missing = want - got
        cov = 1 - len(missing) / len(want)
        if cov < floor:
            bad.append((i, len(want), sorted(missing)[:8], cov))
    return bad

if __name__ == "__main__":
    total = 0
    for slug in sys.argv[1:]:
        bad = check(slug)
        total += len(bad)
        if not bad:
            print(f"{slug:32s} OK  ({len(slide_texts(slug))} slides, no words lost)")
        for i, n, miss, cov in bad:
            print(f"{slug:32s} p{i:<3d} {100*cov:5.1f}% of {n} words  missing e.g. {miss}")
    print("---- slides losing words:", total)
