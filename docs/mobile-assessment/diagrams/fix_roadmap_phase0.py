#!/usr/bin/env python3
"""Correct roadmap rows 0.3 and 0.5, the Phase 0 exit gate and the Phase 0 gate in
'Phases at a glance' on page 2853404716. Visible 'Corrected 20 Oct 2026' markers.
Backup: parent/roadmap-storage-v<N>.xml. Aborts if a target string is missing."""
import json, publish

PAGE = "2853404716"
REF = ('<ac:link><ri:page ri:content-title="Mobile roadmap Phase 0: Close the leak – refinement notes" />'
       '<ac:plain-text-link-body><![CDATA[Phase 0 refinement notes]]></ac:plain-text-link-body></ac:link>')
M = "<em>Corrected 20 Oct 2026: "
R = [
 # row 0.3 step
 ('Required reviewers and branch policy (<code>master</code>, <code>release-*</code>, <code>v*</code>) on <code>customer_app_prod</code> and <code>customer_app_prod_test</code>',
  'Deployment branch and tag policy (<code>master</code>, <code>release-*</code>, <code>v*</code>) on <code>customer_app_prod</code> and <code>customer_app_prod_test</code>, plus a push ruleset that limits who can change <code>.github/workflows/**</code>. '
  + M + 'this row used to ask for required reviewers. Our GitHub Team plan does not offer required reviewers on environments in a private repo. The Enterprise question is a separate decision, see ' + REF + '.</em>'),
 # row 0.3 check
 ('<code>GET /environments</code> shows the rule; a test dispatch waits for approval',
  '<code>GET /environments</code> shows a deployment branch policy; a dispatch from a feature branch fails; a PR from a non-listed user that changes a workflow is rejected'),
 # row 0.3 rollback
 ('<p local-id="78b8c36ece98">Remove the rule</p>',
  '<p local-id="78b8c36ece98">Set the policy back to "No restriction"; disable the push ruleset</p>'),
 # row 0.5 step
 ('Remove the <code>trstringer/manual-approval</code> step once 0.3 is live',
  'Keep the <code>trstringer/manual-approval</code> step (2 approvals) and harden it: the person who started the run cannot approve, approvers are teams, a GitHub App token replaces the 2022 <code>GH_PAT</code>. '
  + M + 'this row used to say "remove the step once 0.3 is live". An environment rule needs only 1 approval and is not available on our plan, so removing the step would weaken the gate.</em>'),
 # row 0.5 check
 ('Prod build still stops for approval, now from the environment rule',
  'Prod build still needs 2 approvals; the person who started the run is not offered as an approver'),
 # exit gate
 ('<code>customer_app_prod</code> and <code>customer_app_prod_test</code> need a reviewer. Prod builds cannot start without approval.</p>',
  '<code>customer_app_prod</code> and <code>customer_app_prod_test</code> accept only <code>master</code>, <code>release-*</code> and <code>v*</code>. Only named people can change workflows. Prod builds still need 2 approvals. '
  + M + 'the gate used to say "need a reviewer", which our GitHub plan does not offer.</em> Details per step: ' + REF + '.</p>'),
 # phases at a glance
 ('Secrets rotated, prod environment has reviewers',
  'Secrets rotated, prod environments limited to release refs, prod builds need 2 approvals (<em>corrected 20 Oct 2026</em>)'),
]

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]; v = page["version"]["number"]
    open(f"parent/roadmap-storage-v{v}.xml", "w").write(s)
    for old, new in R:
        if s.count(old) != 1:
            raise SystemExit(f"not found exactly once: {old[:70]}")
        s = s.replace(old, new)
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": v + 1, "message": "Correct Phase 0 rows 0.3 and 0.5 (GitHub Team plan has no environment reviewers)"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"roadmap v{v} -> v{v+1}")

main()
