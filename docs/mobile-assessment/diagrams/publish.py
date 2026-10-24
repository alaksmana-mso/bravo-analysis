#!/usr/bin/env python3
"""Publish Mermaid diagrams to a Confluence page as mermaid-cloud macros.

Usage: publish.py <page_id> <diagram_dir>

<diagram_dir>/manifest.json: [{"file": "01-goal.mmd", "heading": "Goal"}, ...]
For each entry: uploads the .mmd source as attachment "<stem>" (text/plain) and
"<stem>.png" (rendered next to it), then inserts a mermaid-cloud macro right after
the <h2> whose text equals "heading". Re-running replaces our earlier macros.
Credentials come from ~/.config/mcp-atlassian/.env (never printed).
"""
import json, os, re, sys, html, base64, urllib.request, uuid

def env():
    vals = {}
    for line in open(os.path.expanduser("~/.config/mcp-atlassian/.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            vals[k] = v.strip().strip('"').strip("'")
    return vals

E = env()
BASE = E["CONFLUENCE_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(f'{E["CONFLUENCE_USERNAME"]}:{E["CONFLUENCE_API_TOKEN"]}'.encode()).decode()

def req(method, path, body=None, headers=None):
    h = {"Authorization": AUTH, "Accept": "application/json"}
    h.update(headers or {})
    r = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read()[:400]!r}")

def upload(page_id, name, data, ctype):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    res = req("PUT", f"/rest/api/content/{page_id}/child/attachment?expand=version", body,
              {"X-Atlassian-Token": "nocheck", "Content-Type": f"multipart/form-data; boundary={b}"})
    return res["results"][0]["version"]["number"]

def macro(stem, rev):
    return ('<ac:structured-macro ac:name="mermaid-cloud" ac:schema-version="1" data-layout="default">'
            f'<ac:parameter ac:name="filename">{html.escape(stem)}</ac:parameter>'
            f'<ac:parameter ac:name="revision">{rev}</ac:parameter></ac:structured-macro>')

def text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()

def main(page_id, d):
    manifest = json.load(open(os.path.join(d, "manifest.json")))
    macros = {}
    for m in manifest:
        stem = os.path.splitext(m["file"])[0]
        src = open(os.path.join(d, m["file"]), "rb").read()
        png = open(os.path.join(d, stem + ".png"), "rb").read()
        rev = upload(page_id, stem, src, "text/plain")
        upload(page_id, stem + ".png", png, "image/png")
        macros.setdefault(m["heading"], []).append(macro(stem, rev))
        print(f"uploaded {stem} rev {rev}")
    page = req("GET", f"/rest/api/content/{page_id}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]
    stems = {os.path.splitext(m["file"])[0] for m in manifest}
    # drop our earlier macros (re-run safe)
    def keep(mo):
        f = re.search(r'ac:name="filename">([^<]*)<', mo.group(0))
        return "" if f and html.unescape(f.group(1)) in stems else mo.group(0)
    s = re.sub(r'<ac:structured-macro[^>]*ac:name="mermaid-cloud".*?</ac:structured-macro>', keep, s, flags=re.S)
    missing = set(macros)
    def ins(mo):
        t = text_of(mo.group(0))
        if t in macros:
            missing.discard(t)
            return mo.group(0) + "".join(macros[t])
        return mo.group(0)
    s = re.sub(r"<h([234])[^>]*>.*?</h\1>", ins, s, flags=re.S)
    if missing:
        raise SystemExit(f"headings not found: {sorted(missing)}")
    body = {"id": page_id, "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1, "message": "Add Mermaid diagrams"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    req("PUT", f"/rest/api/content/{page_id}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"page {page_id} -> v{page['version']['number'] + 1}, {sum(len(v) for v in macros.values())} diagrams")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
