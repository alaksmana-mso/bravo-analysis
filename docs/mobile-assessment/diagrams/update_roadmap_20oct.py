#!/usr/bin/env python3
"""Roadmap page 2853404716: fold in the 19–20 Oct findings (Codacy, keyless sign-in, stale
baselines, release pace, e2e suite state). Visible 'Updated 20 Oct 2026' markers. Adds row 2.25.
Backup parent/roadmap-storage-v<N>.xml. Aborts if any target string is not found exactly once."""
import json, re, publish

PAGE = "2853404716"
def link(title, text):
    return (f'<ac:link><ri:page ri:content-title="{title}" />'
            f'<ac:plain-text-link-body><![CDATA[{text}]]></ac:plain-text-link-body></ac:link>')
P0 = link("Mobile roadmap Phase 0: Close the leak – refinement notes", "Phase 0 notes")
P1 = link("Mobile roadmap Phase 1: Safety net first – refinement notes", "Phase 1 notes")
U = "<em>Updated 20 Oct 2026: "

R = [
 # 0.2
 ("Rotate <code>BRAVO_GCP_SA_KEY</code> and <code>SSH_PRIVATE_KEY</code>. Do not open the old run's log</p>",
  "Rotate <code>BRAVO_GCP_SA_KEY</code> and <code>SSH_PRIVATE_KEY</code>. Do not open the old run's log. "
  + U + "<code>BRAVO_GCP_SA_KEY</code> is an organization secret used by 51 repos and is the Google Play upload key, so SRE rotates it. Then remove both keys: Google Play through the keyless sign-in BFI already uses in 27 repos (Workload Identity Federation), git dependencies through a read-only GitHub App token. See " + P0 + ".</em></p>"),
 # 0.6
 ("CI check that fails any workflow which echoes <code>secrets.*</code>, in a workflow that is not path-filtered</p>",
  "Codacy scanning of workflow files (Opengrep and Trivy), with the tool list in <code>.codacy/codacy.yaml</code> like other BFI repos. A small grep step only if Codacy misses the trick used in <code>test.yaml</code>. "
  + U + "this row used to propose a new check. Codacy is BFI's standard scanner and is already a required check here, so no new tool.</em></p>"),
 ("A test PR with <code>echo ${{ secrets.X }}</code> fails</p>",
  "A test PR with a copy of the old <code>test.yaml</code> is flagged by Codacy (or by the grep step)</p>"),
 # 0.7
 ("Run CI on PRs that change only <code>.github/**</code> (<code>actionlint</code>, secret-echo check, SHA-pin check)</p>",
  "A small <code>workflow-lint</code> job on every PR, no path filter: <code>actionlint</code> and a SHA-pin check. Pin every action and the <code>bfi-base-template</code> reusable workflow to a commit SHA. "
  + U + "Codacy already runs on workflow-only PRs, so this job adds only what Codacy does not do.</em></p>"),
 # 1.3
 ("Play staged rollout: &quot;Promote&quot; workflow 5% &rarr; 20% &rarr; 50% &rarr; 100%. iOS phased release on</p>",
  "Play staged rollout 5% &rarr; 20% &rarr; 50% &rarr; 100% and iOS phased release, by hand in the consoles with a release checklist. A &quot;Promote&quot; workflow comes with 2.19. "
  + U + "today the workflows upload only to the Play internal track and TestFlight; the move to production is done by hand. Prod releases ship about every 2 weeks.</em></p>"),
 # 1.10
 ("Coverage gate on changed files, start at 70%. Read the Codacy &quot;Diff Coverage&quot; setting first</p>",
  "Coverage gate on changed files, start at 70%, set in Codacy &quot;Diff Coverage&quot; (already a required check). Remove <code>continue-on-error</code> from the coverage upload</p>"),
 # 1.12
 ("Golden screenshots of 5 key screens: home, loan detail, submission review, KYC, payment</p>",
  "Golden screenshots of 5 key screens: home, loan detail, submission review, KYC, payment. Use Alchemist CI-mode goldens (<code>golden_toolkit</code> is discontinued)</p>"),
 # 1.14
 ("Connect the e2e suite in <code>automation-monorepo</code>: register, KYC, loan submission, payment. Add the missing specs and stable <code>Semantics</code> ids</p>",
  "Connect the e2e suite in <code>automation-monorepo</code>: register, KYC, loan submission, payment. Add the missing specs and stable <code>Semantics</code> ids. "
  + U + "the suite has 18 specs and a KYC spec now exists; register and a real payment journey are still missing. Keep Appium in this phase.</em></p>"),
 # 1.19
 ("Architecture ratchet <code>tool/arch_check.dart</code> with today's baseline: <code>feature-import</code> 264, <code>router-import</code> 94, <code>customer-repo-growth</code> 26. Run it in CI</p>",
  "Architecture ratchet <code>tool/arch_check.dart</code> (<code>feature-import</code>, <code>router-import</code>, <code>customer-repo-growth</code>). Take the baseline on the day it merges. Run it in CI. "
  + U + "the baseline numbers from the plan pages are stale. Feature-to-feature imports were 264 on 11 Sep and 334 on 19 Oct. Do this step first in Phase 1. See " + P1 + ".</em></p>"),
 # 1.20
 ("Stop the growth of legacy state: ratchet rules <code>state-notifier</code> 72, <code>app-ref</code> 142, <code>navigator-context</code> 151; <code>AGENTS.md</code> rule for new code</p>",
  "Stop the growth of legacy state: ratchet rules <code>state-notifier</code>, <code>app-ref</code>, <code>navigator-context</code>, baseline on merge day; <code>AGENTS.md</code> rule for new code. "
  + U + "on 19 Oct the counts were 88, 131 and 166, all up since 11 Sep.</em></p>"),
 # 1.22
 ("Review bot with a few helpful rules (large PR, no test change, new dependency, secret echo)</p>",
  "Mechanical review rules in a small <code>github-script</code> job (large PR, no test change, new dependency). "
  + U + "Copilot code review and Codacy already run on every PR, so no new bot.</em></p>"),
 # Phase 1 exit gate
 ("The parity net is green on <code>master</code> for 2 release trains in a row.",
  "The parity net is green on <code>master</code> for 2 prod releases in a row (<em>updated 20 Oct 2026: about 4 weeks at today's pace of one prod release every 2 weeks</em>)."),
]

NEW_ROW = ('<tr><td><p>2.25</p></td>'
  '<td><p>Sign the Android bundle with the upload key held in Cloud KMS (HSM) through its PKCS#11 library and <code>jarsigner</code>, after a proof of concept. CI signs in keyless and never holds the key. <em>Added 20 Oct 2026 from the key-location review in ' + P0 + '.</em></p></td>'
  '<td><p>Phase 0 notes, key table</p></td><td><p>A</p></td>'
  '<td><p>The signed bundle verifies with <code>apksigner verify</code>; Play accepts it on the internal track; the keystore file is gone from the environment secrets</p></td>'
  '<td><p>Put the keystore secret back</p></td><td><p /></td><td><p /></td></tr>')

def main():
    page = publish.req("GET", f"/rest/api/content/{PAGE}?expand=body.storage,version")
    s = page["body"]["storage"]["value"]; v = page["version"]["number"]
    open(f"parent/roadmap-storage-v{v}.xml", "w").write(s)
    if "2.25</p>" in s:
        raise SystemExit("already applied")
    for old, new in R:
        if s.count(old) != 1:
            raise SystemExit(f"not found exactly once ({s.count(old)}): {old[:70]}")
        s = s.replace(old, new)
    m = re.search(r"<tr[^>]*>(?:(?!</tr>).)*?>2\.24</p>.*?</tr>", s, re.S)
    if not m: raise SystemExit("row 2.24 not found")
    s = s[:m.end()] + NEW_ROW + s[m.end():]
    body = {"id": PAGE, "type": "page", "title": page["title"],
            "version": {"number": v + 1, "message": "Fold in 19-20 Oct findings: Codacy, keyless sign-in, stale baselines, release pace, e2e state; add 2.25"},
            "body": {"storage": {"value": s, "representation": "storage"}}}
    publish.req("PUT", f"/rest/api/content/{PAGE}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(f"roadmap v{v} -> v{v+1}")

main()
