# Brief: add parity (keeping features identical) to each plan

Decision (agreed with the user): no second app. We improve the one BFI app in place. For risky changes the old
and new code live side by side in the same app, behind a per-feature switch flag. The same tests run on both
paths. Then a staged rollout compares the two user groups (cohorts). Then we flip to the new path and delete
the old one. A feature has parity only when its old path is deleted.

The parent page defines this once, in a section called "Keeping features identical". Plans refer to it by that
name. Terms to use, exactly:
- "switch flag": a Remote Config flag per feature that picks old or new path (e.g. `useNewLoanFlow`), with an owner and a removal date. Plus a dev-mode toggle for QA.
- "parity net": the tests that must pass on BOTH paths: golden screenshots of key screens, recorded SIT API fixtures (contract replay), widget tests run with the flag off and on, the analytics golden names file (plan 02 step 1), end-to-end journeys in automation-monorepo (`packages/mobile-automation/bfi-mobile`, 15 specs today) run with the flag off and on.
- "parity ledger": one table per feature: behaviour | old-path test | new-path test | e2e spec | analytics events | status | approved delta. Feature owner signs off.
- "approved delta": a change that is meant to differ (PII removed from `apply_loan`, income/amount bucketing, screen-capture block, R8, root-check default on, real Datadog consent). Listed, signed off by product or the data protection officer, excluded from the parity check.
- "cohort check": during rollout (flag 1% → 10% → 50% → 100%, plus Play staged rollout) compare old vs new users in Datadog RUM (crash-free sessions, error rate, screen load time) and Firebase/Mixpanel funnels. Agreed thresholds. The switch flag is the kill switch.
- "flip and delete": after 2 releases at 100% with no regression, delete the old path and the switch flag.

What to add to each plan (do not add or rename any `## ` heading — the 8 h2 headings must stay exactly as they are):
1. A block `### Parity check` at the END of the `## Plan` section (just before `## Done when`). 3–8 flat bullets: what in this plan could change behaviour, how the parity net proves it did not, which items are approved deltas. Refer to other plans by "Mobile plan NN: Title".
2. 1–3 bullets added to `## Done when` about parity.
3. ONLY for the plans marked "new steps" below: add real numbered steps inside `## Plan` (renumber later steps if needed, and fix any "step N" references elsewhere in the same file), and redraw that plan's diagram `diagrams/NN/04-plan.mmd` to include them (same style rules as diagrams/_DIAGRAM_BRIEF.md), then render it:
   cd /Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams && mise x node@22 -- npx -y @mermaid-js/mermaid-cli -p puppeteer.json -b white -s 2 -i NN/04-plan.mmd -o NN/04-plan.png
   and LOOK at the PNG. If the 05-done diagram no longer matches the Done when list, update and render it too.

Per plan:
- 01 Security: R8 build must pass the same smoke list and e2e as a non-R8 build; screen-capture block, root-check default on, Datadog consent = approved deltas. Block only.
- 02 Analytics wrapper: the golden names file is the analytics parity oracle that every later plan reuses; on each switched feature the same events fire on both paths. Block only.
- 03 Testing: NEW STEPS. This plan BUILDS the parity net: golden screenshots for key screens (loan detail, submission review, KYC, home, payment), recorded SIT API fixtures + a replay harness, a helper that runs a widget test twice (flag off/on), e2e journeys register/KYC/loan submission/payment added to automation-monorepo and able to run against a build with the flag forced on or off, a parity ledger template. Check automation-monorepo (read-only) for how specs locate elements; if they rely on text or accessibility ids, say the new path must keep the same Keys/Semantics ids.
- 04 CI/CD: NEW STEPS. Release candidates run the e2e suite twice (flag off, flag on); Play staged rollout; a cohort dashboard (Datadog RUM + Firebase/Mixpanel funnel) with thresholds; a kill-switch runbook (who flips the flag, how fast).
- 05 Logging and crashes: tag RUM sessions/Crashlytics with the switch-flag state so the cohort check can split by path; the sanitiser is an approved delta. Block only.
- 06 Lint and guardrails: rules: the new path may not import the old path and vice versa; every switch flag and old path has a removal date checked in CI. Block only.
- 07 Networking: contract replay: recorded fixtures through the old HttpClient and the new interceptor chain must give identical requests and mapped results; ship the new chain behind a switch flag. Block only, plus 1 Done-when bullet.
- 08 Layering: NEW STEPS. The main user of the loop: per feature (loan first): fill the parity ledger from today's behaviour, build the new path beside the old, switch flag, parity net green on both, cohort check, flip and delete. Make it explicit that extraction of a feature is not "done" until the old path is deleted.
- 09 State management: the same screen tests must pass on the StateNotifier version and the Notifier version before the swap; where a controller has no screen test, add one first. Block only.
- 10 Dependency injection: the wiring test resolves both paths while a switch flag exists; overrides per path in tests. Block only.
- 11 Repo layout: extraction is move-only: no behaviour change in the same PR; tests and golden files unchanged and green before and after. Block only.
- 12 Feature flags: NEW STEP. This plan owns switch flags as a flag kind in the catalogue: owner, removal date, default = old path, cleanup after flip; CI fails when a switch flag is past its removal date.
- 13 Design system: golden screenshots of every Digital* component before and after the package move. Block only.

Style: plain English, short sentences, flat lists only (no nested bullets), no secret values. Keep the
"**Priority N of 13.**" first line unchanged. Edit only the plan files and diagrams named in your task.
