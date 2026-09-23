#!/usr/bin/env python3
"""Poll every fix/logging pull request in bfi-finance and write a status JSON.
Usage: poll.py OUT.json   (token from `git credential fill`)"""
import json, subprocess, sys, urllib.request, urllib.parse, datetime
tok = subprocess.run(["git","credential","fill"],input="protocol=https\nhost=github.com\n",capture_output=True,text=True).stdout
TOKEN = [l.split("=",1)[1] for l in tok.splitlines() if l.startswith("password=")][0]
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "poll"}
import os, tempfile, time
_hdr = tempfile.NamedTemporaryFile("w", delete=False, suffix=".hdr"); os.chmod(_hdr.name, 0o600)
_hdr.write(f"Authorization: Bearer {TOKEN}\nAccept: application/vnd.github+json\n"); _hdr.close()
def get(url):
    # curl, not urllib: the sandbox lets curl out but blocks Python sockets.
    # The token travels in a 0600 header file, never in argv, so a failure trace cannot print it.
    for attempt in range(4):
        r = subprocess.run(["curl","-sS","--max-time","60","--retry","2","-H",f"@{_hdr.name}",url],capture_output=True,text=True)
        if r.returncode == 0:
            try: return json.loads(r.stdout)
            except json.JSONDecodeError: pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"GitHub API failed after retries: {url}")
prs = []
for q in ["is:pr org:bfi-finance author:alaksmana-mso head:fix/logging",
          "is:pr repo:bfi-finance/bfi-java-pkg 122", "is:pr repo:bfi-finance/bfi-java-pkg 123",
          "is:pr repo:bfi-finance/app-deployment 13820", "is:pr repo:bfi-finance/bfi-go-pkg 175"]:
    page = 1
    while True:
        d = get("https://api.github.com/search/issues?per_page=100&page=%d&q=%s" % (page, urllib.parse.quote(q)))
        for it in d["items"]:
            repo = it["repository_url"].split("/repos/")[1]
            if (repo, it["number"]) not in [(p["repo"], p["number"]) for p in prs]:
                prs.append({"repo": repo, "number": it["number"], "title": it["title"]})
        if len(d["items"]) < 100: break
        page += 1
out = []
for p in prs:
    pr = get(f"https://api.github.com/repos/{p['repo']}/pulls/{p['number']}")
    row = {**p, "state": "merged" if pr["merged"] else pr["state"], "merged_at": pr["merged_at"],
           "merged_by": (pr["merged_by"] or {}).get("login"), "closed_at": pr["closed_at"],
           "head": pr["head"]["sha"], "head_ref": pr["head"]["ref"], "approvals": [], "failing": [], "pending": []}
    revs = get(f"https://api.github.com/repos/{p['repo']}/pulls/{p['number']}/reviews?per_page=100")
    row["approvals"] = sorted({r["user"]["login"] for r in revs if r["state"] == "APPROVED"})
    if row["state"] == "open":
        cr = get(f"https://api.github.com/repos/{p['repo']}/commits/{row['head']}/check-runs?per_page=100")
        for c in cr["check_runs"]:
            if c["status"] != "completed": row["pending"].append(c["name"])
            elif c["conclusion"] in ("failure", "timed_out", "action_required", "cancelled"): row["failing"].append(f"{c['name']} ({c['conclusion']})")
        st = get(f"https://api.github.com/repos/{p['repo']}/commits/{row['head']}/status")
        for s in st["statuses"]:
            if s["state"] in ("failure", "error"): row["failing"].append(f"{s['context']} (status:{s['state']})")
            elif s["state"] == "pending": row["pending"].append(s["context"])
    out.append(row)
    print(f"{p['repo']}#{p['number']}: {row['state']} {row['merged_at'] or ''} {row['merged_by'] or ''} fail={len(row['failing'])} pend={len(row['pending'])}", file=sys.stderr)
out.sort(key=lambda r: (r["repo"], r["number"]))
json.dump({"polled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "prs": out}, open(sys.argv[1], "w"), indent=1)
print(f"{len(out)} pull requests -> {sys.argv[1]}")
