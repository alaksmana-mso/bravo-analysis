#!/usr/bin/env python3
"""Replace the Roadmap section body on the Genfi and Square assessment pages with a short
phase summary and links to the new roadmap pages. Backs up storage first. Aborts if already applied."""
import sys, re, json, html
sys.path.insert(0, "/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams")
import publish
def link(t): return f'<ac:link><ri:page ri:content-title="{html.escape(t, quote=True)}" /><ac:plain-text-link-body><![CDATA[{t}]]></ac:plain-text-link-body></ac:link>'
def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li><p>{i}</p></li>" for i in items) + "</ul>"
def table(head, rows):
    h = "<tr>" + "".join(f"<th><p>{c}</p></th>" for c in head) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td><p>{c}</p></td>" for c in r) + "</tr>" for r in rows)
    return f'<table data-table-width="1800" data-layout="full-width"><tbody>{h}{b}</tbody></table>'
SHARED = link("Agency apps roadmap: shared phases")
JOBS = [("2874998826", "GENFI roadmap: step by step", "GENFI", "calculator and prospect", "prospect", "ds_2"),
        ("2875260970", "SQUARE roadmap: step by step", "SQUARE", "lead and company submission", "lead", "ds_1")]
for pid, roadmap, app, pilot, pkg, ds in JOBS:
    c = publish.req("GET", f"/rest/api/content/{pid}?expand=body.storage,version"); s = c["body"]["storage"]["value"]; v = c["version"]["number"]
    open(f"/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams/parent/{pid}-storage-v{v}.xml", "w").write(s)
    if "Revised 24 Oct 2026: the roadmap" in s: print(pid, "already applied"); continue
    m = re.search(r"(<h2[^>]*>\s*Roadmap\s*</h2>)(.*?)(<h2[^>]*>\s*Open questions\s*</h2>)", s, re.S)
    if not m: raise SystemExit(f"{pid}: Roadmap section not found")
    R = link(roadmap)
    PH = [["0", "Close the leak", "Four leaking workflows gone, secrets rotated, SQUARE upload key reset, prod environments limited to release refs", "A", "shared"],
          ["1", "Safety net first", "One toolchain, checks on every PR, coverage gate, ratchets, dashboards, staged rollout, before any app change", "A", "shared + " + app + " rows"],
          ["2", "Seams, same behaviour", "Observability, analytics, flag and DI ports behind today's calls; interceptor chain built, not wired", "B", "shared"],
          ["3", "Approved deltas", "Privacy and security fixes, one per " + app + " release", "D, E", app],
          ["4", "Network chain", "Six auth decorators become one chain behind useInterceptorClient, one app at a time", "C, E", "shared"],
          ["5", "Move call sites", "Analytics and flag calls move to the ports, per app", "B", "shared"],
          ["6", "Riverpod 3 alone", "One dependency change, three separate releases", "B", "shared"],
          ["7", "Pilot: " + pilot, "Domain layer and Notifiers through the parity loop", "C", app],
          ["8", "Packages", pkg + " as the first feature package; " + ds + " to ds_3", "B", "shared + " + app + " rows"],
          ["9", "Other features", "Same loop for the rest; collab_form last, with the other app", "C, then B", app],
          ["10", "Platform", "RASP (one vendor, three repos), Widgetbook, tokens", "C, D", "shared"]]
    NEW = "".join([
        p(f"<em>Revised 24 Oct 2026: the roadmap is now ordered by risk to users, not by topic, the same way as the BFI customer app's. The earlier 4-phase version (now, quick wins, architecture, platform) is replaced. Every step, with columns for its Jira ticket and PR, is on {R}. Phases shared by all four apps in the monorepo live under {SHARED}.</em>"),
        p("Three rules shape the order:"),
        ul(["<strong>Safety net first.</strong> Tests, staged rollout, health dashboards and the kill switch come before any change to app behaviour.",
            "<strong>One risky change per release, per app.</strong> At most one flagged change or one approved delta per release.",
            "<strong>A fast way back for every risky change.</strong> A switch flag that turns the new path off in minutes, or a halted store rollout."]),
        p("Impact classes: <strong>A</strong> no app change, <strong>B</strong> same behaviour (proven by the parity net), <strong>C</strong> behind a switch flag, <strong>D</strong> approved delta, <strong>E</strong> needs a backend change that keeps old app versions working."),
        table(["Phase", "Name", "What it does", "Classes", "Where"], PH),
        p(f"Each phase is one Jira epic. Each step is one ticket. See {R}."),
    ])
    s = s[:m.start(2)] + NEW + s[m.end(2):]
    body = {"id": pid, "type": "page", "title": c["title"], "version": {"number": v + 1, "message": "Roadmap revised: ordered by user risk, steps on the roadmap page"}, "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{pid}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"{pid} ({app}): v{v} -> v{v+1}")
