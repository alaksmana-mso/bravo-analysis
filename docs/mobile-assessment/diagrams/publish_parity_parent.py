#!/usr/bin/env python3
"""Add the 'Keeping features identical' section to the parent page (storage-level edit).

- Summary: one bullet after the urgent security bullet.
- Plans table: a 'Parity role' column.
- New h2 section before 'Roadmap', with 2 mermaid-cloud diagrams (parity/q01, q02).
Aborts if the page has changed since parent/storage-v8.xml, or if the edit would drop any existing macro.
"""
import os, re, json
import publish

PAGE = "2831057205"
D = os.path.dirname(os.path.abspath(__file__))

ROLES = {
    "01": "R8 build passes the same smoke and e2e tests; security changes are approved deltas",
    "02": "Golden event-names file = analytics parity oracle for every later plan",
    "03": "Builds the parity net: golden screenshots, API fixtures, tests on both paths, e2e journeys",
    "04": "Runs the parity net twice per release candidate; staged rollout, cohort dashboard, kill switch",
    "05": "Tags crashes and sessions with the flag state so cohorts can be compared",
    "06": "Old and new path may not import each other; every switch flag has a removal date",
    "07": "Contract replay: same recorded traffic through old client and new interceptors",
    "08": "Main user of the loop, loan first: ledger, flag, both paths green, flip and delete",
    "09": "Same screen tests pass on the old controller and the new Notifier",
    "10": "Wiring test resolves both paths while a switch flag exists",
    "11": "Move-only extraction: tests and golden files unchanged",
    "12": "Owns switch flags: owner, removal date, clean-up after the flip",
    "13": "Golden screenshots of every Digital* component before and after the move",
}

def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li><p>{i}</p></li>" for i in items) + "</ul>"
def ol(items): return '<ol start="1">' + "".join(f"<li><p>{i}</p></li>" for i in items) + "</ol>"
def table(head, rows):
    h = "<tr>" + "".join(f"<th><p>{c}</p></th>" for c in head) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td><p>{c}</p></td>" for c in r) + "</tr>" for r in rows)
    return f'<table data-table-width="1800" data-layout="full-width"><tbody>{h}{b}</tbody></table>'

def section(m1, m2):
    return "".join([
        "<h2>Keeping features identical</h2>",
        m1,
        p("We do <strong>not</strong> build a second app. We improve the one BFI app in place. "
          "For each risky change, the old and the new code live side by side in the same app, behind a switch flag. "
          "The same tests run on both paths. Then we roll out slowly, compare the two groups of users, flip, "
          "and delete the old path. Each plan below applies this in its own <strong>Parity check</strong> block."),
        "<h3>Why not a second app</h3>",
        ul([
            "<strong>Users would have to move.</strong> A second app needs a new bundle id. Users reinstall, and their "
            "secure storage (tokens, PIN state) does not move. Or it replaces the current app in one big-bang cut-over.",
            "<strong>Parity drifts from day one.</strong> The current app ships every week (Monday release branch). "
            "A parallel app has to chase every change for months.",
            "<strong>Too big to rewrite safely.</strong> 23 features, 78 routes, 264 cross-feature imports.",
            "<strong>Jago did not do it either.</strong> Its rule is a ratchet plus \"extract and flip\" inside one app. "
            "Its second app shell is for a second bank, not for parity.",
            "<strong>Second apps we do want:</strong> internal ones only, never in the stores: Widgetbook for the "
            "design system, and a sandbox app per feature package.",
        ]),
        "<h3>The loop for each feature</h3>",
        m2,
        ol([
            "<strong>Freeze.</strong> Write the parity ledger for the feature. Make sure the parity net passes on the old path.",
            "<strong>Build beside.</strong> The new path is added next to the old one. The old code is not changed.",
            "<strong>Switch flag.</strong> One Remote Config flag per feature (for example <code>useNewLoanFlow</code>), "
            "default = old path, with an owner and a removal date. QA also gets a dev-mode toggle.",
            "<strong>Same tests, both paths.</strong> The parity net must pass with the flag off and on: golden screenshots, "
            "recorded SIT API fixtures, widget tests run twice, the analytics golden names file, and the e2e journeys "
            "in <code>automation-monorepo</code>.",
            "<strong>Cohort check.</strong> Roll the flag out 1% → 10% → 50% → 100%, with Play staged rollout. Compare old and "
            "new users in Datadog RUM (crash-free sessions, errors, load time) and in Firebase/Mixpanel funnels. "
            "If a threshold breaks, flip the flag back.",
            "<strong>Flip and delete.</strong> After 2 releases at 100% with no regression, delete the old path and the flag. "
            "A feature has parity only when its old path is gone.",
        ]),
        "<h3>Parity ledger (one per feature)</h3>",
        p("The feature owner signs it off. Example row:"),
        table(["Behaviour", "Old-path test", "New-path test", "E2E spec", "Analytics events", "Status", "Approved delta"],
              [["Loan submission review shows tenor, amount and fees", "review_submission_screen_test", "same test, flag on",
                "loan submission journey", "apply_loan (same name)", "both green", "address removed from apply_loan"]]),
        "<h3>Approved deltas</h3>",
        p("Some changes are meant to differ. Each one is listed, signed off, and left out of the parity check."),
        table(["Change", "Why", "Signs off"], [
            ["Home address removed from <code>apply_loan</code>; income and amount bucketed", "Personal data in analytics", "Product + data protection officer"],
            ["Screen-capture block on sensitive screens", "Security (Mobile plan 01)", "Product"],
            ["R8 on; root check on by default", "Security (Mobile plan 01)", "Squad lead"],
            ["Real tracking consent for Datadog", "Privacy (Mobile plan 02, 05)", "Data protection officer"],
        ]),
        "<h3>Where each plan fits</h3>",
        p("The <strong>Parity role</strong> column in the Plans table above shows what each plan adds. "
          "In short: plan 03 builds the parity net, plan 04 runs it on every release candidate, "
          "plan 12 owns the switch flags, and plan 08 is the main user of the loop."),
    ])

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]
    if s != open(os.path.join(D, "parent", "storage-v8.xml")).read():
        raise SystemExit("parent page changed since backup; stop")
    before = len(re.findall(r'ac:name="mermaid-cloud"', s))
    if "Keeping features identical" in s:
        raise SystemExit("section already present; stop")
    # diagrams
    macros = []
    for stem in ("q01", "q02"):
        rev = publish.upload(PAGE, stem, open(os.path.join(D, "parity", stem + ".mmd"), "rb").read(), "text/plain")
        publish.upload(PAGE, stem + ".png", open(os.path.join(D, "parity", stem + ".png"), "rb").read(), "image/png")
        macros.append(publish.macro(stem, rev))
    # 1. summary bullet
    anchor = re.search(r'See the Security items section below\.</p></li>', s)
    if not anchor: raise SystemExit("summary anchor not found")
    s = s[:anchor.end()] + ('<li><p><strong>No second app.</strong> Features stay identical through one loop: old and new path '
                            'behind a switch flag, same tests on both, slow rollout, then delete the old path. '
                            'See Keeping features identical below.</p></li>') + s[anchor.end():]
    # 2. plans table column
    start = s.find(">Plans (in priority order)<"); end = s.find("</table>", start)
    t = s[start:end]
    t, hn = re.subn(r"(<th[^>]*><p[^>]*>Why this position</p></th>)(</tr>)", r"\1<th><p>Parity role</p></th>\2", t, count=1)
    if hn != 1: raise SystemExit("plans table header not found")
    def addcell(mo):
        num = re.search(r"<td[^>]*><p[^>]*>(\d\d)</p></td>", mo.group(0)).group(1)
        return mo.group(0)[:-5] + f"<td><p>{ROLES[num]}</p></td></tr>"
    t, n = re.subn(r"<tr[^>]*><td[^>]*><p[^>]*>\d\d</p></td>.*?</tr>", addcell, t, flags=re.S)
    if n != 13: raise SystemExit(f"plans table rows found: {n}")
    s = s[:start] + t + s[end:]
    # 3. new section before Roadmap
    rm = re.search(r"<h2[^>]*>Roadmap</h2>", s)
    s = s[:rm.start()] + section(*macros) + s[rm.start():]
    after = len(re.findall(r'ac:name="mermaid-cloud"', s))
    if after != before + 2: raise SystemExit(f"macro count {before} -> {after}; stop")
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1, "message": "Add 'Keeping features identical' + parity role per plan"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"page {PAGE} -> v{page['version']['number'] + 1}; mermaid {before} -> {after}")

if __name__ == "__main__":
    main()
