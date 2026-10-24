#!/usr/bin/env python3
"""Replace the body of the parent page's 'Roadmap' h2 with a short phase summary and a
link to the child page 'Mobile roadmap: step by step'. Also mention the child page in the
'Also under this page' paragraph.

Storage-level edit (keeps every other section and its mermaid macros). Backs up the
current storage to parent/storage-v<N>.xml. Aborts if the Roadmap marker already exists.
"""
import os, re, json, html
import publish

PAGE = "2831057205"
CHILD = "2853404716"
CHILD_TITLE = "Mobile roadmap: step by step"
D = os.path.dirname(os.path.abspath(__file__))

def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li><p>{i}</p></li>" for i in items) + "</ul>"
def table(head, rows):
    h = "<tr>" + "".join(f"<th><p>{c}</p></th>" for c in head) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td><p>{c}</p></td>" for c in r) + "</tr>" for r in rows)
    return f'<table data-table-width="1800" data-layout="full-width"><tbody>{h}{b}</tbody></table>'
LINK = (f'<ac:link><ri:page ri:content-title="{html.escape(CHILD_TITLE)}" />'
        f'<ac:plain-text-link-body><![CDATA[{CHILD_TITLE}]]></ac:plain-text-link-body></ac:link>')

PHASES = [
    ["0", "Close the leak", "Remove the secrets workflow, rotate secrets, protect prod", "A"],
    ["1", "Safety net first", "Tests, golden files, e2e, staged rollout, health dashboard, ratchet, before any app change", "A"],
    ["2", "Seams, same behaviour", "Analytics, monitoring and flag ports; switch flags; R8 explicit. Customers see no change", "B"],
    ["3", "Approved deltas", "Privacy and security fixes, one per release, each signed off", "D, E"],
    ["4", "Network chain", "dio interceptors and the refresh-race fix behind one switch flag", "C, E"],
    ["5", "Move call sites", "Analytics, flag and log calls move to the ports, feature by feature", "B"],
    ["6", "Riverpod 3 alone", "Dependency upgrade in a release with nothing else", "B"],
    ["7", "Loan pilot", "Domain layer and Notifiers for <code>loan</code> through the parity loop", "C"],
    ["8", "Packages", "Design system, then <code>loan</code>, move only", "B"],
    ["9", "Other features", "Same loop for <code>auth</code>, <code>rl</code>, <code>ro</code> and the rest", "C, then B"],
    ["10", "Platform", "RASP (report-only first), Material 3, optional extras", "C, D"],
]

NEW = "".join([
    p("<em>Revised 18 Oct 2026: the roadmap is now ordered by risk to customers, not by topic. "
      "The earlier 4-phase version (now, quick wins, architecture, platform) is replaced. "
      f"Every step, with columns for its Jira ticket and PR, is on the child page {LINK}.</em>"),
    p("Three rules shape the order:"),
    ul(["<strong>Safety net first.</strong> Tests, staged rollout, health dashboards and the kill switch come before any change to app behaviour.",
        "<strong>One risky change per release.</strong> At most one flagged change or one approved delta per release, so a problem points to one cause.",
        "<strong>A fast way back for every risky change.</strong> A switch flag that turns the new path off in minutes, or a halted store rollout."]),
    p("Impact classes: <strong>A</strong> no app change, <strong>B</strong> same behaviour (proven by the parity net), "
      "<strong>C</strong> behind a switch flag, <strong>D</strong> approved delta, <strong>E</strong> needs a backend change that keeps old app versions working."),
    table(["Phase", "Name", "What it does", "Classes"], PHASES),
    p(f"Each phase is one Jira epic. Each step is one ticket. See {LINK}."),
])

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]; v = page["version"]["number"]
    if "Revised 18 Oct 2026: the roadmap" in s:
        raise SystemExit("already applied")
    os.makedirs(os.path.join(D, "parent"), exist_ok=True)
    open(os.path.join(D, "parent", f"storage-v{v}.xml"), "w").write(s)
    m = re.search(r"(<h2[^>]*>\s*Roadmap\s*</h2>)(.*?)(<h2[^>]*>\s*Open questions\s*</h2>)", s, re.S)
    if not m:
        raise SystemExit("Roadmap section not found")
    s = s[:m.start(2)] + NEW + s[m.end(2):]
    old = "It explains tokens, components and Widgetbook in plain words, with a reading list, and supports Mobile plan 13."
    if s.count(old) != 1:
        raise SystemExit("'Also under this page' sentence not found exactly once")
    s = s.replace(old, old + f" And {LINK}: the roadmap as one row per step, phase by phase, with Jira and PR columns.")
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": v + 1, "message": "Roadmap revised: ordered by customer risk, steps on child page"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"parent v{v} -> v{v + 1}; backup parent/storage-v{v}.xml")

if __name__ == "__main__":
    main()
