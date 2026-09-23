#!/usr/bin/env python3
"""Turn docs/logging/README.md into the markdown body of the Confluence page
"2026-09 Logging" (page 2774335489, space Technology Development).

The Confluence page is the README with three changes: the H1 is dropped (Confluence shows the
title), a "Built from" line points at the source file, and every relative link is rewritten to
the child page that md2conf created for that file. Links to files with no child page fall back
to the GitHub blob URL.

Usage:  tools/readme_to_confluence.py > /tmp/page.md
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = "https://bfifinance.atlassian.net/wiki/spaces/EA/pages/"
GITHUB = "https://github.com/alaksmana-mso/bravo-analysis/blob/fix/logging/docs/"

# child pages of 2774335489, listed on 23 September 2026 (title -> id); per-service pages are
# titled "<repo> — logging ..." so they are matched on the repo name before the dash.
NAMED = {
    "logging-cost.md": "2755821705", "sre-datadog-recommendations.md": "2755657932",
    "squads-guide.md": "2755723449", "body-visibility.md": "2755461582", "coverage.md": "2755658136",
    "deployment-proposal.md": "2773450891", "confins-prod-ms-lms-ar-be-findings.md": "2774728705",
}
SERVICE_PAGES = {
    "bravo-core-proxy-service": "2755756199", "bravo-agreement-service": "2755821675", "bravo-agency-service": "2755821690",
    "bravo-kyc-sign-service": "2755657872", "bravo-pbf-service": "2755756214", "bravo-payment-service": "2755559714",
    "bravo-inventory-management-service": "2755756229", "bravo-employee-service": "2755166708", "bfi-rule-engine-service": "2755657887",
    "bfi-insurance-api": "2755657902", "bravo-bpm-service": "2755788998", "bravo-branch-service": "2755657917",
    "bravo-notification-service": "2755690684", "bfi-connect": "2755789013", "backend-dashboard-otrs": "2755166760",
    "bravo-lms-gateway": "2755756256", "bravo-auth-service": "2755166775", "bravo-asset-pricing-service": "2755166790",
    "bravo-customer-service": "2755821736", "lora-gateway-service": "2755559777", "bravo-krakend-internal": "2755657947",
    "dms-data-admin-service": "2755690699", "bravo-customer-app-loan-service": "2755461550", "bravo-database-catalog": "2755723491",
    "lora-schema-service": "2755166805", "bravo-samsat-region-resolver": "2755526965", "bravo-integrity-service": "2755756287",
    "doc-renderer-service": "2755690714", "bravo-scheduling-service": "2755166837", "bravo-assistance-service": "2755756302",
    "bravo-repeat-order-service": "2755756317", "bravo-audit-trail-service": "2755723522", "bravo-insurance-service": "2755723537",
    "bfi-operation-api": "2755756332", "bravo-inventory-management-system": "2755166886", "bravo-onboarding-service": "2755166901",
    "bravo-gen-ai": "2755821751", "bfi-digital-web-api": "2755461597", "document-hub-service": "2755723570",
    "bravo-product-service": "2755559904", "bravo-cnv-service": "2755789028", "bravo-partnership-provisioning-service": "2755789043",
    "collection-consumer-service": "2755658073", "lora-task-service": "2755690780", "bfi-payment-api": "2755461629",
    "lms-calculation-service": "2755789077", "bravo-edoc-service": "2755821801", "lora-cdc-foxx-service": "2755527025",
    "bravo-partnership-service": "2755166916", "bravo-approval-engine-service": "2755789092", "bravo-backoffice-service": "2755723585",
    "bravo-surveyor-console": "2755658121", "bravo-calculation-service": "2755756382", "portfolio-management-service": "2755690812",
    "bravo-customer-bff-service": "2755527040", "bravo-robot-scrape": "2755461661", "bravo-robot-controller": "2755690844",
    "bravo-master-service": "2755166944", "bravo-user-iam-service": "2755690859", "gold-service": "2755723600",
    "bfi-incentive-api": "2755690874", "bravo-journal-service": "2755559919", "bravo-krakend-gateway": "2755723632",
    "notification-service": "2755723664", "lora-partnership-task-ndf": "2755166995", "lora-partnership-ndf": "2755461694",
    "bravo-collateral-service": "2755789153", "bravo-document-service": "2755723698", "bravo-agent-service": "2755167010",
    "bravo-lms-ops-service": "2755461745", "bravo-supplier-service": "2755167025", "bravo-agent-marketing-service": "2755461778",
    "bravo-kyc-proxy": "2755690889",
}
unresolved = []

def target(href):
    path, _, frag = href.partition("#")
    if path == "":  # same-page anchor: Confluence anchors differ; keep the text, drop the link
        return None
    name = path.split("/")[-1]
    if name in NAMED: return WIKI + NAMED[name]
    stem = name[:-3] if name.endswith(".md") else name
    if stem in SERVICE_PAGES: return WIKI + SERVICE_PAGES[stem]
    unresolved.append(href)
    return GITHUB + ("logging/" + path if not path.startswith("../") else path[3:])

def rewrite(md):
    def sub(m):
        text, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://", "mailto:")): return m.group(0)
        t = target(href)
        return text if t is None else f"[{text}]({t})"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", sub, md)

def main():
    src = (ROOT / "docs/logging/README.md").read_text()
    lines = src.splitlines(keepends=True)
    if lines and lines[0].startswith("# "): lines = lines[1:]
    body = rewrite("".join(lines))
    header = ("###### Built from [bravo-analysis/docs/logging/README.md](" + GITHUB + "logging/README.md), "
              "refreshed by tools/readme_to_confluence.py\n\n")
    sys.stdout.write(header + body.lstrip("\n"))
    if unresolved: print("unresolved (sent to GitHub):", sorted(set(unresolved)), file=sys.stderr)

if __name__ == "__main__":
    main()
