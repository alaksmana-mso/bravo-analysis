#!/usr/bin/env python3
"""Replace the ASCII code-block diagrams on the parent page with mermaid-cloud macros.

The Nth `code` macro on the page (document order) is replaced by parent/pNN.mmd.
Safety: each code block's text must still equal parent/pNN.txt (taken from v7), so a
concurrent edit aborts the run instead of replacing the wrong block.
Also removes the earlier test macro "00-summary".
"""
import os, re, json
import publish

PAGE = "2831057205"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parent")

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]
    blocks = list(re.finditer(r'<ac:structured-macro[^>]*ac:name="code".*?</ac:structured-macro>', s, flags=re.S))
    index = json.load(open(os.path.join(D, "ascii-index.json")))
    if len(blocks) != len(index):
        raise SystemExit(f"expected {len(index)} code blocks, found {len(blocks)}; page changed, stop")
    for i, b in enumerate(blocks, 1):
        body = re.search(r'<!\[CDATA\[(.*?)\]\]>', b.group(0), flags=re.S).group(1)
        if body != open(os.path.join(D, f"p{i:02d}.txt")).read():
            raise SystemExit(f"code block {i} differs from backup; stop")
    repl = {}
    for i in range(1, len(blocks) + 1):
        stem = f"p{i:02d}"
        rev = publish.upload(PAGE, stem, open(os.path.join(D, stem + ".mmd"), "rb").read(), "text/plain")
        publish.upload(PAGE, stem + ".png", open(os.path.join(D, stem + ".png"), "rb").read(), "image/png")
        repl[i] = publish.macro(stem, rev)
        print(f"uploaded {stem} rev {rev}")
    out, last = [], 0
    for i, b in enumerate(blocks, 1):
        out.append(s[last:b.start()]); out.append(repl[i]); last = b.end()
    out.append(s[last:])
    s = "".join(out)
    s = re.sub(r'<ac:structured-macro[^>]*ac:name="mermaid-cloud"[^>]*>(?:(?!</ac:structured-macro>).)*?'
               r'ac:name="filename">00-summary<.*?</ac:structured-macro>', "", s, flags=re.S)
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1,
                        "message": "Replace ASCII diagrams with Mermaid"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(),
                {"Content-Type": "application/json"})
    left = s.count('ac:name="code"')
    print(f"page {PAGE} -> v{page['version']['number'] + 1}; code blocks left: {left}")

if __name__ == "__main__":
    main()
