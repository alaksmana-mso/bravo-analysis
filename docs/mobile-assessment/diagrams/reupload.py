#!/usr/bin/env python3
"""Re-upload changed diagrams to a page and bump their mermaid-cloud macro revisions in place.

Usage: reupload.py <page_id> <dir> <stem> [<stem> ...]
For each stem: uploads <dir>/<stem>.mmd (as attachment "<stem>") and <dir>/<stem>.png as new
versions, then rewrites the macro's "revision" parameter so the add-on renders the new source.
Does not touch any other content. Aborts if a stem's macro is not found exactly once.
"""
import os, re, sys, json
import publish

def main(page_id, d, stems):
    page = publish.req("GET", f"/rest/api/content/{page_id}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]
    for stem in stems:
        pat = re.compile(r'(<ac:parameter ac:name="filename">' + re.escape(stem) + r'</ac:parameter><ac:parameter ac:name="revision">)(\d+)(</ac:parameter>)')
        if len(pat.findall(s)) != 1:
            raise SystemExit(f"{stem}: macro found {len(pat.findall(s))} times; stop")
        rev = publish.upload(page_id, stem, open(os.path.join(d, stem + ".mmd"), "rb").read(), "text/plain")
        publish.upload(page_id, stem + ".png", open(os.path.join(d, stem + ".png"), "rb").read(), "image/png")
        s = pat.sub(lambda m: f"{m.group(1)}{rev}{m.group(3)}", s)
        print(f"{stem}: revision -> {rev}")
    body = {"id": page_id, "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1, "message": f"Update diagrams: {', '.join(stems)}"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{page_id}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"page {page_id} -> v{page['version']['number'] + 1}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
