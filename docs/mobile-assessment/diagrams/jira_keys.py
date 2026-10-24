#!/usr/bin/env python3
"""Replace plain 'DM-NNNN' text with Jira issue macros on a Confluence page (storage level),
and optionally fill empty 'Jira ticket' cells of roadmap rows: usage
  jira_keys.py <page_id>                      # macro-ify plain keys in the body
  jira_keys.py <page_id> 0.1=DM-3593 0.2=...   # also set roadmap row cells (7th td) by row number
Backs up to parent/<page_id>-storage-v<N>.xml."""
import re, sys, json, html, publish
SERVER_ID = "e11399a0-5e7f-3912-9253-fe5136baa0af"
def macro(key):
    return ('<ac:structured-macro ac:name="jira" ac:schema-version="1">'
            f'<ac:parameter ac:name="key">{key}</ac:parameter>'
            f'<ac:parameter ac:name="serverId">{SERVER_ID}</ac:parameter>'
            '<ac:parameter ac:name="server">System Jira</ac:parameter></ac:structured-macro>')
def main(page, assigns):
    p = publish.req("GET", f"/rest/api/content/{page}?expand=body.storage,version")
    s = p["body"]["storage"]["value"]; v = p["version"]["number"]
    import os; open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "parent", f"{page}-storage-v{v}.xml"), "w").write(s)
    # 1) plain keys in text nodes (not already inside a macro parameter)
    def sub(m):
        return macro(m.group(1))
    s2 = re.sub(r'(?<![>"\w-])(DM-\d{4})(?![\w-])(?![^<]*</ac:parameter>)', sub, s)
    n_text = len(re.findall(r'(?<![>"\w-])DM-\d{4}(?![\w-])(?![^<]*</ac:parameter>)', s))
    s = s2
    # 2) roadmap rows: set the Jira ticket cell (7th <td>) for given row numbers
    n_rows = 0
    for a in assigns:
        row, keys = a.split("="); keys = keys.split("+")
        m = re.search(r'<tr[^>]*>\s*<td[^>]*>\s*<p[^>]*>' + re.escape(row) + r'</p>\s*</td>.*?</tr>', s, re.S)
        if not m: raise SystemExit(f"row {row} not found")
        tr = m.group(0); tds = list(re.finditer(r'<td[^>]*>.*?</td>', tr, re.S))
        if len(tds) < 8: raise SystemExit(f"row {row} has {len(tds)} cells")
        cell = tds[6]; macros = " ".join(macro(k) for k in keys)
        if re.search(r'<p[^>]*/>', cell.group(0)):
            inner = re.sub(r'<p([^>]*)/>', lambda mm: f'<p{mm.group(1)}>' + macros + '</p>', cell.group(0), count=1)
        elif re.search(r'<p[^>]*>', cell.group(0)):
            inner = re.sub(r'<p([^>]*)>.*?</p>', lambda mm: f'<p{mm.group(1)}>' + macros + '</p>', cell.group(0), count=1, flags=re.S)
        else:
            inner = cell.group(0).replace('</td>', '<p>' + macros + '</p></td>')
        if inner == cell.group(0): raise SystemExit(f"row {row}: cell unchanged")
        tr2 = tr[:cell.start()] + inner + tr[cell.end():]
        s = s.replace(tr, tr2); n_rows += 1
    body = {"id": page, "type": "page", "title": p["title"],
            "version": {"number": v + 1, "message": "Jira ticket keys as issue macros"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{page}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"{page}: v{v} -> v{v+1}; {n_text} plain keys macro-ified, {n_rows} rows set")
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
