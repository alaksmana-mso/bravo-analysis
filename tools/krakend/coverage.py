#!/usr/bin/env python3
"""Check which observed (method, path) pairs are matched by the generated endpoints.
Reads the generated file plus the hand-written bpm.*.tmpl files next to it.
Input TSV: method<TAB>path<TAB>count, with {p} for any id segment. Prints uncovered rows.
Usage: python3 gen/openapi-to-krakend/coverage.py config/template/bpm._generated.endpoints.tmpl observed.tsv"""
import re, sys
PARAM = re.compile(r"\{[^}/]+\}")
gen = set()
import glob, os
sources = [sys.argv[1]] + [f for f in glob.glob(os.path.join(os.path.dirname(sys.argv[1]), "bpm.*.tmpl")) if "_generated" not in f]
for src in sources:
    for m in re.finditer(r'"endpoint": "([^"]+)",\s*"method": "([A-Z]+)"', open(src).read()):
        gen.add((m.group(2), PARAM.sub("{p}", m.group(1))))
# route-level match: a {p} in the observed path may stand for a static segment that OpenAPI names explicitly
pats = {}
for meth, ep in gen:
    pats.setdefault(meth, []).append(re.compile("^" + re.escape(ep).replace(r"\{p\}", r"[^/]+") + "$"))
total = covered = 0; unc = []
for line in open(sys.argv[2]):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3 or not parts[0]: continue
    meth, path, n = parts[0], parts[1], int(parts[2]); total += n
    probe = path.replace("{p}", "0")
    ok = (meth, path) in gen or any(p.match(probe) for p in pats.get(meth, []))
    if ok: covered += n
    else: unc.append((n, meth, path))
print(f"generated endpoints: {len(gen)}; observed calls: {total:,}; covered: {covered:,} ({100*covered/total:.2f}%)")
for n, meth, path in sorted(unc, reverse=True): print(f"  UNCOVERED {n:>8} {meth} {path}")
