#!/usr/bin/env python3
"""Add an 'Impact and benefits' h2 to the parent page, right after 'Plans (in priority order)'.

Storage-level edit (keeps the layouts and the 42 mermaid macros). Aborts if the page
changed since parent/storage-v11.xml or if the section already exists.
"""
import os, re, json
import publish

PAGE = "2831057205"
D = os.path.dirname(os.path.abspath(__file__))

def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li><p>{i}</p></li>" for i in items) + "</ul>"
def table(head, rows):
    h = "<tr>" + "".join(f"<th><p>{c}</p></th>" for c in head) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td><p>{c}</p></td>" for c in r) + "</tr>" for r in rows)
    return f'<table data-table-width="1800" data-layout="full-width"><tbody>{h}{b}</tbody></table>'

ROWS = [
    ["01", "Security",
     "A workflow on <code>master</code> and 4 release branches can print prod secrets. No GitHub environment has a protection rule. R8 is off, so Android code ships unshrunk and readable. Nothing stops screenshots of KYC or PIN screens.",
     "Prod secrets cannot be printed or used without an approver. Android code is shrunk and renamed, so crash reports become readable and the app is harder to copy. Sensitive screens are blank in screenshots. The backend stops trusting a secret anyone can pull out of the APK.",
     "Removes a live key-leak path and an audit finding waiting to happen. Smaller APK. Fewer fraud and account-takeover cases from tampered apps once RASP is in.",
     "Audit, fraud, every user"],
    ["02", "Analytics wrapper",
     "187 Firebase calls in 81 files with 148 event names typed as strings. A second, separate Mixpanel path. The customer's full home address goes to Firebase; income and loan amount go to Mixpanel. Datadog consent is hard-coded to granted.",
     "One interface, typed events, one catalogue. Personal data is blocked before it leaves the device. Consent is real. Dashboards keep the same event names.",
     "Closes a personal-data exposure to two third parties. New events take minutes, not a hunt through 80 files. Swapping or adding a vendor touches 1 file. Product analytics can review every event in one place.",
     "Data protection, product analytics, marketing"],
    ["03", "Testing",
     "Controller tests are rejected by CI. Logic can only be tested through whole screens. No coverage threshold we can see. No end-to-end run before a release.",
     "Logic is tested on its own, fast. Coverage on changed files is a hard gate (start 70%). Register, KYC, loan submission and payment run on real devices for every release candidate. The parity net lets us refactor with proof.",
     "Fewer regressions reach customers. PRs get faster, because unit tests replace slow screen tests. Every later plan can change code without guessing.",
     "Squad, QA, release manager"],
    ["04", "CI/CD",
     "README says Flutter 3.38.5, CI uses 3.41.9. Build numbers come from a tag. 13 workflows, 2,943 lines, 279 of them repeated <code>--dart-define</code> flags. One workflow builds prod-signed apps with no approval. Workflow-only PRs skip CI.",
     "One Flutter version in one file. Build numbers always go up. Prod builds need an approver. Workflows under 1,500 lines. Staged rollout on Play with a crash check between stages. A monthly report on how fast and how safely we ship.",
     "Fewer broken builds from version drift. Faster, safer releases. A bad release reaches 10% of users, not 100%. Delivery metrics we can show management.",
     "Squad, SRE, management"],
    ["05", "Logging and crashes",
     "35 of 38 Datadog error calls put raw error text in the message. No PII cleaner. Trace ID reaches Crashlytics but not Datadog logs, so support cannot jump from a crash to the backend trace.",
     "One monitoring interface. A PII cleaner runs before anything leaves the device, proven by a unit test and a weekly zero-hit query. Every error carries the backend trace ID.",
     "Support finds the cause of a customer problem in minutes instead of hours. Personal data stops landing in Datadog and Crashlytics. Crash rates can be split by old and new path during rollouts.",
     "Support, SRE, data protection"],
    ["06", "Lint and guardrails",
     "Rules exist only in <code>AGENTS.md</code> and reviewers' heads. 264 feature-to-feature imports today, and nothing stops the 265th.",
     "A checker in CI fails any PR that adds new debt: feature-to-feature imports, Flutter in domain code, vendor SDKs outside adapters, overdue switch flags. The baseline only goes down.",
     "The architecture work cannot be undone by the next sprint. Reviews are shorter, because the tool catches the mechanical part. AI tools and new joiners read the same written rules.",
     "Squad, tech lead, new joiners"],
    ["07", "Networking",
     "One 496-line HTTP client. Token refresh has a real race: several late 401s can each start a new refresh. No request ID on requests.",
     "Small interceptors, each with one job. Single-flight refresh, proven by 7 race tests. Every request carries a request ID and keeps the server trace ID. The 114 repository call sites do not change.",
     "Fewer random logouts and failed requests under load. Backend and mobile logs line up on one ID. A bug in auth or retry is found in a 40-line file, not a 500-line one.",
     "Every user, support, backend team"],
    ["08", "Layering",
     "No domain layer. 214 of 355 feature files import API models straight into screens and controllers. Business rules sit in 1,000-line screens and a 970-line KYC use case.",
     "Every feature has data, domain and presentation. Rules live in pure Dart with their own unit tests. An API change stops at the data layer. <code>loan</code> first, then <code>auth</code>, <code>rl</code>, <code>ro</code>.",
     "A backend field change no longer breaks screens. Rules like tenor, due dates and KYC skips are tested in milliseconds without a widget. New features in <code>loan</code> get faster to build and safer to change.",
     "Squad, product, backend team"],
    ["09", "State management",
     "72 controllers on the legacy <code>StateNotifier</code> API. A global <code>appRef</code> used in 142 places and a global <code>navigatorContext</code> in 151, so code can reach anything from anywhere.",
     "Riverpod 3 <code>Notifier</code> everywhere. No globals. Notifiers hold state, call use cases, never navigate, and have unit tests.",
     "Riverpod stays supported (the legacy API is on its way out). Bugs are reproducible in a unit test instead of only on a phone. Memory leaks from stale global reads go away.",
     "Squad"],
    ["10", "Dependency injection",
     "4 ports overridden inline in <code>main.dart</code>. 128 providers with no boundary; any feature can read any other.",
     "Each feature declares its own providers and reads outside things only through ports. All wiring in one place. A CI test proves every port is wired.",
     "A missing wiring is caught in CI, not at app start on a customer's phone. Tests swap real services for fakes in one line. Same mechanism carries the switch flags for safe rollouts.",
     "Squad, QA"],
    ["11", "Repo layout",
     "All 23 features in one package. 60 feature pairs import each other, 14 of them in both directions. <code>router.dart</code> (870 lines) imports every feature.",
     "<code>loan</code>, <code>auth</code>, <code>rl</code>, <code>ro</code> are their own packages with a small public surface. A feature cannot import another by accident, because the package does not depend on it.",
     "Two squads can work on two features without stepping on each other. Builds and tests can run per package. A feature can be reused in another BFI app later.",
     "Squad leads, future apps"],
    ["12", "Feature flags",
     "One 44-field Remote Config model (2,443 generated lines), read in 44 files. Mixpanel flags on a separate path. 2 flags nobody reads. No owner or removal date on any flag.",
     "A typed catalogue: key, safe default, owner, removal date. One port over Remote Config and Mixpanel. CI fails when a flag is overdue. Switch flags for safe rollouts live here.",
     "Flags stop piling up. A flag change rebuilds only the widgets that read it. Rollouts and kill switches become a routine, not a one-off.",
     "Product, squad"],
    ["13", "Design system",
     "32 <code>Digital*</code> components inside the app package, no Widgetbook, 49 raw colour literals. Adoption is already high, so this is the smallest gap.",
     "Components and theme in their own package, every component visible in Widgetbook, colours and spacing as named tokens, optional Figma sync.",
     "Designers and engineers check a component without running the app. UI drift between screens drops. Golden tests catch an unintended visual change.",
     "Design, squad"],
]

def section():
    return "".join([
        "<h2>Impact and benefits</h2>",
        p("What each plan changes for BFI, in plain terms. \"Today\" is from <code>bravo-customer-app</code> <code>master</code> "
          "(<code>190e1d20</code>). \"Benefit\" is what the business and the team get once the plan's \"Done when\" checks pass."),
        table(["#", "Plan", "Today (the problem)", "After (what changes)", "Benefit", "Who feels it"], ROWS),
        "<h3>What you get, by audience</h3>",
        ul([
            "<strong>Customers:</strong> fewer random logouts and failed requests (07), fewer regressions in each release (03, 04), "
            "a bad release stopped at 10% of users instead of 100% (04), and an app that is harder to tamper with (01).",
            "<strong>Compliance and audit:</strong> the secret-leak path closed and prod builds behind an approver (01, 04), personal data "
            "blocked from analytics and logs with a weekly proof (02, 05), real consent (02), an OWASP MASVS table kept per quarter (01).",
            "<strong>Support and SRE:</strong> one ID from a customer complaint to a crash to the backend trace (05, 07), readable Android "
            "stack traces after R8 (01), crash and error rates split by rollout group (04, 05).",
            "<strong>Product:</strong> new events reviewed in one catalogue (02), flags with owners and removal dates (12), rollouts and "
            "kill switches as a routine (04, 12), delivery metrics every month (04).",
            "<strong>Engineering:</strong> rules tested in milliseconds without a widget (08, 09), a CI checker that stops new debt (06), "
            "features in their own packages so squads do not collide (11), a Widgetbook for the UI kit (13).",
        ]),
        "<h3>Benefits that arrive first</h3>",
        p("Plans 01 to 06 are small and pay back in the first one or two sprints each. Plans 07 to 11 are the architecture work; "
          "their benefit grows feature by feature, starting with <code>loan</code>. Plans 12 and 13 are useful but nothing else waits on them."),
    ])

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]
    if s != open(os.path.join(D, "parent", "storage-v11.xml")).read():
        raise SystemExit("parent page changed since backup; stop")
    if "Impact and benefits" in s:
        raise SystemExit("section already present; stop")
    before = len(re.findall(r'ac:name="mermaid-cloud"', s))
    anchor = re.search(r"<h2[^>]*>Keeping features identical</h2>", s)
    if not anchor: raise SystemExit("anchor heading not found")
    s = s[:anchor.start()] + section() + s[anchor.start():]
    after = len(re.findall(r'ac:name="mermaid-cloud"', s))
    if after != before: raise SystemExit(f"macro count changed {before} -> {after}; stop")
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1, "message": "Add 'Impact and benefits' per plan"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"page {PAGE} -> v{page['version']['number'] + 1}; mermaid {after}; rows {len(ROWS)}")

if __name__ == "__main__":
    main()
