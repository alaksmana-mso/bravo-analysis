#!/usr/bin/env python3
"""Emit a print-only, per-deck block that zooms any slide taller than the page box."""
import json, pathlib
D = pathlib.Path(__file__).parent
PX        = 96 / 25.4                       # px per mm at print resolution
SLIDE_H   = 183 * PX                        # printed slide box (186mm page - 3mm slack)
PAD_V     = (11 + 8) * PX                   # print padding, top + bottom
AVAIL     = SLIDE_H - PAD_V                 # room for .inner
MEAS_PAD  = (13 + 9) * PX                   # padding in force when heights were measured
FLOOR     = 0.62                            # below this, readability loses to pagination

def block(slug, heights):
    """Zoom .inner (not .slide) so the slide still fills its page while the content fits."""
    rules, worst = [], 1.0
    for i, h in enumerate(heights, start=1):
        inner = h - MEAS_PAD                 # natural content height
        if inner > AVAIL:
            k = max(FLOOR, round(AVAIL / inner, 3))
            if k >= 0.995: continue      # within rounding: leave it unscaled
            worst = min(worst, k)
            rules.append(f"  .deck > section:nth-child({i}) > .inner{{zoom:{k}}}")
    if not rules:
        return f"/* print-fit {slug}: every slide fits the page box unscaled */\n"
    return ("@media print{\n"
            f"  /* print-fit {slug}: {len(rules)} of {len(heights)} slides scaled to fit "
            f"{AVAIL:.0f}px of content; smallest {worst} */\n"
            + "\n".join(rules) + "\n}\n")

if __name__ == "__main__":
    hs = json.loads((D / "heights.json").read_text())
    for slug, heights in hs.items():
        (D / f"_fit-{slug}.css").write_text(block(slug, heights))
        n = block(slug, heights).count("nth-child")
        print(f"  {slug:32s} {n} slide(s) scaled")
