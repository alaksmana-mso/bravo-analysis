#!/usr/bin/env python3
"""Add assessment links to 'BFI Mobile apps and web apps list' (2858549294): an 'Assessment'
column on the 'In the stores' table and an 'Assessments' section after the Summary. Idempotent:
re-running replaces the column cells and the section. Only links to pages that exist."""
import re, json, html, sys
import publish
PID = "2858549294"
MAP = {  # store name (first cell) -> assessment page title
 "BFI Mobile - Pinjaman Dana": "BFI Mobile App Assessment", "GENFI": "Genfi mobile app assessment", "My Shaf": "MyShaf mobile app assessment",
 "SQUARE": "Square mobile app assessment", "MY BISPRO": "MY BISPRO mobile app assessment", "myBRO": "myBRO (RO Tools) mobile app assessment",
}
ROADMAPS = ["Mobile roadmap: step by step", "Agency apps roadmap: shared phases", "GENFI roadmap: step by step", "SQUARE roadmap: step by step"]
def exists(t):
    q = __import__("urllib.parse").parse.urlencode({"spaceKey": "EA", "title": t, "limit": 1})
    return bool(publish.req("GET", "/rest/api/content?" + q)["results"])  # exact title, no search-index lag
def link(t): return f'<ac:link><ri:page ri:content-title="{html.escape(t, quote=True)}" /><ac:plain-text-link-body><![CDATA[{t}]]></ac:plain-text-link-body></ac:link>'
p = publish.req("GET", f"/rest/api/content/{PID}?expand=body.storage,version"); s = p["body"]["storage"]["value"]; v = p["version"]["number"]
live = {t for t in list(MAP.values()) + ROADMAPS if exists(t)}
print("pages found:", sorted(live))
# 1. table column
i = s.index("<h3>In the stores</h3>"); j = s.index("</table>", i) + len("</table>")
tbl = s[i:j]
def fix_row(m):
    row = m.group(0)
    cells = re.findall(r"<t[dh][^>]*>.*?</t[dh]>", row, re.S)
    first = html.unescape(re.sub("<[^>]+>", "", cells[0])).strip()
    row = re.sub(r'<t[dh] data-assess="1">.*?</t[dh]>', "", row, flags=re.S)  # drop our earlier cell
    if cells[0].startswith("<th"): cell = '<th data-assess="1"><p>Assessment</p></th>'
    else:
        t = next((MAP[k] for k in MAP if first.startswith(k)), None)
        cell = '<td data-assess="1"><p>' + (link(t) if t in live else ("–" if not t else html.escape(t) + " (not yet)")) + "</p></td>"
    return row.replace("</tr>", cell + "</tr>")
tbl2 = re.sub(r"<tr>.*?</tr>", fix_row, tbl, flags=re.S)
s = s[:i] + tbl2 + s[j:]
# 2. section
sec = '<h2 data-assess="1">Assessments</h2>'
items = [f"<li><p>{link(t)}</p></li>" for t in MAP.values() if t in live]
rm = [f"<li><p>{link(t)}</p></li>" for t in ROADMAPS if t in live]
sec += ("<p>One assessment page per store app, each a child of this page. Every assessment compares the app with the DK Jago app and ends in a roadmap ordered by risk to users.</p><ul>" + "".join(items) + "</ul>"
        "<p>Roadmaps: the BFI customer app has its own. The four agency apps share the phases that touch the monorepo and keep per-app pages for approved deltas, the pilot feature and the remaining features.</p><ul>" + "".join(rm) + "</ul>")
s = re.sub(r'<h2 data-assess="1">Assessments</h2>.*?(?=<h2)', "", s, flags=re.S)  # drop earlier section
k = s.index("<h2>How we built the list</h2>")
s = s[:k] + sec + s[k:]
body = {"id": PID, "type": "page", "title": p["title"], "version": {"number": v + 1, "message": "Assessment links"}, "body": {"storage": {"value": s, "representation": "storage"}}}
if "--dry" in sys.argv: print(len(s)); sys.exit()
publish.req("PUT", f"/rest/api/content/{PID}", json.dumps(body).encode(), {"Content-Type": "application/json"}); print(f"v{v} -> v{v+1}")
