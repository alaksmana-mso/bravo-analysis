#!/usr/bin/env python3
"""Turn plain-text page titles into Confluence page links (ac:link by content-title) on the
agency roadmap pages. Skips text inside existing links and a page's own title. Idempotent."""
import sys, re, json, html
sys.path.insert(0, "/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams")
import publish
PAGES = {  # title -> id (pages to edit AND titles to link)
 "Agency apps roadmap: shared phases": "2874966307", "GENFI roadmap: step by step": "2875555894", "SQUARE roadmap: step by step": "2874966327",
 "Agency phase 0: Close the leak": "2875064598", "Agency phase 1: Safety net first": "2875523184", "Agency phase 2: Seams with the same behaviour": "2875261121",
 "Agency phase 4: Network chain behind a switch flag": "2875359525", "Agency phase 5: Move call sites, per app": "2875555921",
 "Agency phase 6: Riverpod 3 upgrade on its own": "2875555941", "Agency phase 8: Packages, move only": "2875359553", "Agency phase 10: Platform": "2875392361",
 "GENFI phase 3: Approved deltas": "2875392385", "GENFI phase 7: Pilot, calculator and prospect": "2874900880", "GENFI phase 9: Other features": "2875359575",
 "SQUARE phase 3: Approved deltas": "2874900902", "SQUARE phase 7: Pilot, lead and company submission": "2874900926", "SQUARE phase 9: Other features": "2875359597",
}
EXTRA = ["Genfi mobile app assessment", "Square mobile app assessment", "Mobile roadmap: step by step", "BFI Mobile App Assessment",
         "Mobile plan 01a: RASP vendor comparison", "Mobile plan 01: Security"]
plans = json.load(open("/private/tmp/claude-503/-Users-mac-6000202-Documents-BFI-GITHUB/84fae0bf-c66b-4f2a-8ff3-898e9839bfc6/scratchpad/square/plans/index.json"))
EXTRA += list(plans.keys()) + ["GENFI plan 07: Layering", "SQUARE plan 05: Testing", "SQUARE plan 06: Networking", "SQUARE plan 07: Lint and guardrails", "SQUARE plan 13: Dependency injection"]
TITLES = sorted(set(list(PAGES.keys()) + EXTRA), key=len, reverse=True)
def link(t): return f'<ac:link><ri:page ri:content-title="{html.escape(t, quote=True)}" /><ac:plain-text-link-body><![CDATA[{t}]]></ac:plain-text-link-body></ac:link>'
def process(s, own):
    out = []; depth = 0; n = 0
    for part in re.split(r'(<[^>]+>|<!\[CDATA\[.*?\]\]>)', s, flags=re.S):
        if part.startswith("<"):
            if part.startswith("<ac:link"): depth += 1
            elif part.startswith("</ac:link"): depth -= 1
            out.append(part); continue
        if depth or not part.strip(): out.append(part); continue
        txt = html.unescape(part)
        for t in TITLES:
            if t == own or t not in txt: continue
            # keep the escaped form for non-link text
            pieces = txt.split(t); txt = None
            seg = []
            for i, p in enumerate(pieces):
                seg.append(p)
                if i < len(pieces) - 1: seg.append("\x00" + t + "\x00"); n += 1
            txt = "".join(seg)
        # re-escape text, then swap placeholders for links
        esc = html.escape(txt, quote=False)
        esc = re.sub(r'\x00(.*?)\x00', lambda m: link(m.group(1)), esc)
        out.append(esc)
    return "".join(out), n
for title, pid in PAGES.items():
    p = publish.req("GET", f"/rest/api/content/{pid}?expand=body.storage,version"); s = p["body"]["storage"]["value"]; v = p["version"]["number"]
    s2, n = process(s, title)
    if n == 0: print(f"{title}: nothing to link"); continue
    body = {"id": pid, "type": "page", "title": title, "version": {"number": v + 1, "minorEdit": True, "message": "Link page titles"}, "body": {"storage": {"value": s2, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{pid}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"{title}: v{v}->v{v+1}, {n} links")
