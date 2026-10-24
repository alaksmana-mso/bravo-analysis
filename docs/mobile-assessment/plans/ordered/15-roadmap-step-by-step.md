## Summary

This page replaces the Roadmap on the parent page (BFI Mobile App Assessment). It lists every step of Mobile plans 01 to 13 in the order we will do them. Each step has a row for its Jira ticket and its pull request (PR).

**Why the order changed.** The old roadmap grouped work by topic: quick wins, architecture, platform. The new one groups work by **risk to customers**. The customer app has many users. It ships every week. Old app versions stay on phones for months. So each step must reach customers in a way that cannot break the app, and that we can undo quickly.

**Three rules shape the order:**

1. **Build the safety net first.** Tests, release tooling, dashboards and the kill switch come before any change to app behaviour (Phases 0 and 1).
2. **Change one risky thing per release.** A release carries at most one flagged change or one approved delta. If something goes wrong, we know which change caused it.
3. **Every risky change has a fast way back.** A switch flag that turns the new path off in minutes, or a halted store rollout.

**How to use this page.**

* Each phase is one **Jira epic**. Put the epic key next to "Jira epic" under the phase heading.
* Each row is one **Jira ticket**. Put the ticket key in the "Jira ticket" column.
* Put the PR link (or links) in the "PR" column when the PR is opened.
* "Plan ref" points to the plan page and step, for example "01 §0" = Mobile plan 01: Security, step 0. The details of each step stay on that plan page.
* A phase starts only when the previous phase's exit gate is met. Rows inside a phase can run in parallel unless the row says otherwise.

Facts come from `bravo-customer-app` `master` @ `190e1d20` and the 13 plan pages, as of 18 Oct 2026.

## How each step stays safe

### Impact classes

Every step has one class. The class tells you how the step can affect customers and how to undo it.

| Class | What it means | How we undo it | Example |
| --- | --- | --- | --- |
| **A. No app change** | GitHub settings, CI, docs, dashboards or tests only. The app that customers install does not change. | Revert the PR or the setting. | Delete `test.yaml`, coverage gate |
| **B. Same behaviour** | App code moves, but customers see and send exactly the same things. The parity net proves it. | Halt the store rollout and ship a hotfix. | Analytics port behind today's calls |
| **C. Flagged change** | A new path sits next to the old one behind a switch flag. Default = old path. The flag rolls out 1% → 10% → 50% → 100%. | Turn the switch flag off. Open apps pick it up at the next journey start. | New network chain, loan domain layer |
| **D. Approved delta** | Behaviour is meant to change. Product or the data protection officer signs it off first. Where possible, it has its own kill-switch flag. | Turn the kill switch off, or halt the rollout and hotfix. | Home address removed from `apply_loan` |
| **E. Backend-coupled** | The backend must change too. It must keep working for old app versions until the minimum supported version is raised. | Backend goes back to monitor-only. | `API_SECRET` no longer trusted alone |

### Release rules for every step

1. **One risky change per release.** A release carries at most one class C or class D change. Class A and B changes can ride along.
2. **Two dials, one at a time.** The Play staged rollout and a switch-flag rollout are separate dials. Move only one of them in the same week.
3. **Staged store rollout.** Play: 5% → 20% → 50% → 100%. iOS: App Store phased release. Before each step up, check the release health dashboard.
4. **Stop rules.** Halt or flip back when the new version or the new path is worse than the old one by more than the agreed thresholds. Starting proposal (Mobile plan 04, step 8): crash-free sessions more than 0.2 points lower, error rate more than 10% higher, p75 screen load more than 10% slower, funnel conversion more than 2 points lower.
5. **Backend changes go monitor-only first.** A class E step logs what it would block, without blocking. It enforces only after the oldest supported app version can handle it.
6. **The parity net must be green before a release.** Unit and widget tests, golden screenshots, recorded API fixtures, the analytics golden names file, and the e2e journeys in `automation-monorepo`.
7. **Old app versions are not affected by switch flags.** A flag only exists in builds that contain the new path. Old builds keep their old code. This is why class C is safe for the long tail of old versions.

## Phases at a glance

| Phase | Goal | Classes | Exit gate | Jira epic |
| --- | --- | --- | --- | --- |
| 0. Close the leak | No prod secret can be printed or used without approval | A | Secrets rotated, prod environments limited to release refs, prod builds need 2 approvals (*corrected 20 Oct 2026*) | |
| 1. Safety net first | Tests, release tooling and guardrails before any app change | A | Parity net green on 2 release trains; staged rollout used on 1 real release | |
| 2. Seams, same behaviour | Ports and flags in place, customers see no change | B | One release at 100% with golden files unchanged and no health regression | |
| 3. Approved deltas | Privacy and security fixes, one per release | D, E | Each delta signed off and stable at 100% for 1 release | |
| 4. Network chain | Interceptors and the refresh-race fix behind a switch flag | C, E | Old network path deleted after 2 releases at 100% | |
| 5. Move call sites | Analytics, flags and logs use the new ports everywhere | B | All ratchet baselines for direct calls at 0; shims deleted | |
| 6. Riverpod 3 alone | Dependency upgrade in a release with nothing else | B | 1 release at 100% with no new provider errors | |
| 7. Loan pilot | Domain layer and Notifiers for `loan` through the parity loop | C | Old loan path deleted after 2 releases at 100% | |
| 8. Packages | Design system and `loan` move into packages, move only | B | `loan` is its own package; tests and goldens unchanged | |
| 9. Other features | Same loop for `auth`, `rl`, `ro` and the rest | C | Every feature's old path deleted | |
| 10. Platform | RASP, Material 3 and optional extras | C, D | Per item | |

Phases 0 and 1 can overlap. From Phase 2 on, a phase starts only when the previous exit gate is met. Phases 9 and 10 can run at the same time if the release rules hold.

## Phase 0: Close the leak

**Jira epic:** *(add)*

**Goal.** No one can print or use prod secrets without an approver. Nothing in the app changes.

**Entry gate.** None. Start now.

**Exit gate.** `test.yaml` gone from every branch. Both secrets rotated. `customer_app_prod` and `customer_app_prod_test` accept only `master`, `release-*` and `v*`. Only named people can change workflows. Prod builds still need 2 approvals. *Corrected 20 Oct 2026: the gate used to say "need a reviewer", which our GitHub plan does not offer.* Details per step: Phase 0 refinement notes.

| # | Step | Plan ref | Class | Check before done | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1 | Disable "Reveal Secret" in the Actions UI, then delete `test.yaml` on `master` and `release-2.24.x` to `release-2.27.x` | 01 §0.1, 04 §1 | A | Actions API no longer lists the workflow | Not needed | | |
| 0.2 | Rotate `BRAVO_GCP_SA_KEY` and `SSH_PRIVATE_KEY`. Do not open the old run's log. *Updated 20 Oct 2026: `BRAVO_GCP_SA_KEY` is an organization secret used by 51 repos and is the Google Play upload key, so SRE rotates it. Then remove both keys: Google Play through the keyless sign-in BFI already uses in 27 repos (Workload Identity Federation), git dependencies through a read-only GitHub App token. See Phase 0 notes.* | 01 §0.2 | A | Old key disabled in GCP; old SSH key removed; next build passes with the new values | Keep the old key disabled; fix the new one | | |
| 0.3 | Deployment branch and tag policy (`master`, `release-*`, `v*`) on `customer_app_prod` and `customer_app_prod_test`, plus a push ruleset that limits who can change `.github/workflows/**`. *Corrected 20 Oct 2026: this row used to ask for required reviewers. Our GitHub Team plan does not offer required reviewers on environments in a private repo. The Enterprise question is a separate decision, see Phase 0 refinement notes.* | 01 §0.3, 04 §1 | A | `GET /environments` shows a deployment branch policy; a dispatch from a feature branch fails; a PR from a non-listed user that changes a workflow is rejected | Set the policy back to "No restriction"; disable the push ruleset | | |
| 0.4 | Put `build-prod-artifact.yml` behind the same approval, or delete it if `build-prod-test.yml` covers it | 04 §1 | A | A dispatch waits for approval | Revert PR | | |
| 0.5 | Keep the `trstringer/manual-approval` step (2 approvals) and harden it: the person who started the run cannot approve, approvers are teams, a GitHub App token replaces the 2022 `GH_PAT`. *Corrected 20 Oct 2026: this row used to say "remove the step once 0.3 is live". An environment rule needs only 1 approval and is not available on our plan, so removing the step would weaken the gate.* | 04 §1 | A | Prod build still needs 2 approvals; the person who started the run is not offered as an approver | Revert PR | | |
| 0.6 | Codacy scanning of workflow files (Opengrep and Trivy), with the tool list in `.codacy/codacy.yaml` like other BFI repos. A small grep step only if Codacy misses the trick used in `test.yaml`. *Updated 20 Oct 2026: this row used to propose a new check. Codacy is BFI's standard scanner and is already a required check here, so no new tool.* | 01 §0.4, 04 §11 | A | A test PR with a copy of the old `test.yaml` is flagged by Codacy (or by the grep step) | Revert PR | | |
| 0.7 | A small `workflow-lint` job on every PR, no path filter: `actionlint` and a SHA-pin check. Pin every action and the `bfi-base-template` reusable workflow to a commit SHA. *Updated 20 Oct 2026: Codacy already runs on workflow-only PRs, so this job adds only what Codacy does not do.* | 04 §11 | A | A workflow-only PR shows the checks | Revert PR | | |

## Phase 1: Safety net first

**Jira epic:** *(add)*

**Goal.** Before any change to app behaviour, we can (a) prove a change kept behaviour the same, (b) release to a small share of users first, (c) see when a release is worse, and (d) stop new debt from growing.

**Entry gate.** Phase 0 rows 0.1 to 0.3 done.

**Exit gate.** The parity net is green on `master` for 2 prod releases in a row (*updated 20 Oct 2026: about 4 weeks at today's pace of one prod release every 2 weeks*). One real release went out through the Play staged rollout and iOS phased release, checked on the release health dashboard. The architecture ratchet runs on every PR.

### 1a. Release tooling

| # | Step | Plan ref | Class | Check before done | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | Pin Flutter in `mise.toml` to **3.41.9, the version CI uses today**, so the built app does not change. Use it in CI. Fix the README | 04 §2 | A | `grep` finds no other Flutter version in `.github` or README; APK size same as last release | Revert PR | | |
| 1.2 | Build numbers that only go up (run number + offset). Same rule for SIT, UAT and prod | 04 §3 | A | Two builds of the same tag get increasing numbers; Play and App Store Connect accept them | Revert PR | | |
| 1.3 | Play staged rollout 5% → 20% → 50% → 100% and iOS phased release, by hand in the consoles with a release checklist. A "Promote" workflow comes with 2.19. *Updated 20 Oct 2026: today the workflows upload only to the Play internal track and TestFlight; the move to production is done by hand. Prod releases ship about every 2 weeks.* | 04 §6 | A | One release promoted through all stages | Halt rollout in Play Console | | |
| 1.4 | Release health dashboard per app version: crash-free sessions, error rate, p75 screen load (Datadog RUM, Crashlytics). Agree the stop thresholds with product and SRE | 04 §8 (first half) | A | Dashboard shows the last 2 versions side by side | Not needed | | |
| 1.5 | DORA-style delivery metrics, monthly | 04 §12 | A | First monthly report produced | Not needed | | |
| 1.6 | `project.pbxproj`: make it the tracked source of truth, delete the `.backup` copy | 01 §6 | A | iOS builds for all 4 flavors give the same IPA as before | Revert PR | | |

### 1b. Test net

| # | Step | Plan ref | Class | Check before done | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.7 | Lift the controller-test ban in `pr-pipeline.yml`; update `AGENTS.md` | 03 §1 | A | A PR with a new `*_controller_test.dart` passes | Revert PR | | |
| 1.8 | Write down the test pyramid in `AGENTS.md` | 03 §2 | A | Reviewed by the squad lead | Revert PR | | |
| 1.9 | Random test order in `melos test`; fix tests that share state | 03 §3 | A | 5 runs in a row pass with random seeds | Revert PR | | |
| 1.10 | Coverage gate on changed files, start at 70%, set in Codacy "Diff Coverage" (already a required check). Remove `continue-on-error` from the coverage upload | 03 §4 | A | A PR that adds an untested use case fails | Lower the threshold or revert | | |
| 1.11 | Analytics golden names file: every Firebase name, Mixpanel name and journey code | 02 §1 | A | File has 148 Firebase names and 34 journey codes | Revert PR | | |
| 1.12 | Golden screenshots of 5 key screens: home, loan detail, submission review, KYC, payment. Use Alchemist CI-mode goldens (`golden_toolkit` is discontinued) | 03 §7 | A | Changing one colour on a key screen fails the test | Revert PR | | |
| 1.13 | Recorded SIT API fixtures for 4 journeys, personal data scrubbed, plus a replay harness | 03 §8 | A | Scrub check passes; a renamed request field fails the replay test | Revert PR | | |
| 1.14 | Connect the e2e suite in `automation-monorepo`: register, KYC, loan submission, payment. Add the missing specs and stable `Semantics` ids. *Updated 20 Oct 2026: the suite has 18 specs and a KYC spec now exists; register and a real payment journey are still missing. Keep Appium in this phase.* | 03 §6 | A (B for the `Semantics` ids) | Each release candidate has an e2e result linked in its release notes | Revert PR | | |
| 1.15 | Network race tests, no production code: 5 parallel requests with an expired token, 5 parallel 401s | 07 §1 | A | Proactive case shows 1 refresh; the 401 case documents today's bug | Revert PR | | |
| 1.16 | Parity ledger template `docs/parity/_template.md` and guide | 03 §11 | A | Template reviewed by QA and the squad lead | Revert PR | | |

### 1c. Guardrails

| # | Step | Plan ref | Class | Check before done | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.17 | Lint clean-up: one lint set, stricter analyzer options if the error count is small | 06 §1 | A | `melos run analyze` passes | Revert PR | | |
| 1.18 | Fail PRs on stale generated files (`melos generate`, `melos l10n`, then `git status`) | 06 §2 | A | A PR with a stale `.g.dart` fails | Revert PR | | |
| 1.19 | Architecture ratchet `tool/arch_check.dart` (`feature-import`, `router-import`, `customer-repo-growth`). Take the baseline on the day it merges. Run it in CI. *Updated 20 Oct 2026: the baseline numbers from the plan pages are stale. Feature-to-feature imports were 264 on 11 Sep and 334 on 19 Oct. Do this step first in Phase 1. See Phase 1 notes.* | 11 §1, 06 §3 | A | Passes on `master`; a branch with a new `rl → ro` import fails | Revert PR | | |
| 1.20 | Stop the growth of legacy state: ratchet rules `state-notifier`, `app-ref`, `navigator-context`, baseline on merge day; `AGENTS.md` rule for new code. *Updated 20 Oct 2026: on 19 Oct the counts were 88, 131 and 166, all up since 11 Sep.* | 09 §1 | A | A branch that adds `appRef.read(` fails | Revert PR | | |
| 1.21 | `CODEOWNERS` for `.github/`, the checker, `analysis_options.yaml`, `.claude/` | 06 §6 | A | A PR touching `.github/` asks for a lead | Revert PR | | |
| 1.22 | Mechanical review rules in a small `github-script` job (large PR, no test change, new dependency). *Updated 20 Oct 2026: Copilot code review and Codacy already run on every PR, so no new bot.* | 06 §4 | A | Bot comments on 3 test PRs as expected | Disable the workflow | | |

### 1d. Security groundwork (no app change)

| # | Step | Plan ref | Class | Check before done | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.23 | OWASP MASVS table in the repo, reviewed each quarter | 01 §8 | A | Table committed and reviewed | Not needed | | |
| 1.24 | RASP: start the RFP and PoC with Promon, Guardsquare, Appdome, V-Key (Everspin, DoveRunner if local support is a must). No app change yet | 01 §7 (RFP) | A | Quotes and PoC dates received | Not needed | | |
| 1.25 | RUM-to-APM linking spike: does a RUM resource link to its APM trace through KrakenD and Istio? Record the answer | 05 §7 | A | Answer written on plan 05 | Not needed | | |

## Phase 2: Seams with the same behaviour

**Jira epic:** *(add)*

**Goal.** Add the ports, the flag catalogue and the switch-flag machinery. Customers see and send exactly the same things. After this phase, every later change can go behind a switch flag.

**Entry gate.** Phase 1 exit gate met.

**Exit gate.** One release at 100% that contains all Phase 2 code, with the analytics golden names file, the golden screenshots and the e2e journeys unchanged, and no health regression. The kill-switch runbook has been rehearsed once in SIT.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1 | Analytics port package `shared_lib/analytics` with `FakeAnalytics`, pure Dart | 02 §2 | B | Package has no Flutter or vendor import; 100% unit-tested | Revert PR | | |
| 2.2 | Analytics adapters and fan-out. Old `Analytics.logEvent` and `MixpanelService.track` stay as thin shims | 02 §3 | B | Adapter tests assert exact names and parameters; golden names file unchanged | Halt rollout, hotfix | | |
| 2.3 | CI ratchet against new direct analytics calls | 02 §4 | A | Baseline stored; a new direct call fails | Revert PR | | |
| 2.4 | `Digital*` components send tracking through `analytics.track` | 02 §7 | B | Golden names file unchanged; widget tests use `FakeAnalytics` | Halt rollout, hotfix | | |
| 2.5 | Monitoring port behind `DatadogLog`, same public signatures; add `DatadogLog.info` | 05 §2 | B | `datadog_log_test.dart` still passes | Halt rollout, hotfix | | |
| 2.6 | Trace ID and endpoint as Datadog log attributes; per-call keys in Crashlytics | 05 §3 | B | `@trace_id:*` shows values on HTTP errors in SIT | Halt rollout, hotfix | | |
| 2.7 | Move crash hooks from `main.dart` into the Crashlytics adapter | 05 §4 | B | Debug-menu test crash appears in Crashlytics (dev flavor) | Halt rollout, hotfix | | |
| 2.8 | Tag every RUM session and Crashlytics report with the state of each switch flag | 05 parity | B | Tag visible in SIT sessions | Halt rollout, hotfix | | |
| 2.9 | Monitoring ratchet against new direct Crashlytics or Datadog log calls | 05 §10 | A | A new direct call fails CI | Revert PR | | |
| 2.10 | Flag port, adapters and `FakeFlagStore`. Wrap today's fetch logic unchanged | 12 §1 | B | Parse-error tests return the default | Halt rollout, hotfix | | |
| 2.11 | Catalogue of the 44 Remote Config keys with today's defaults | 12 §2 | B | Test compares keys and defaults with today's mapping | Revert PR | | |
| 2.12 | `SwitchFlag` kind: owner and removal date required, default = old path, real-time | 12 §3 | B | A switch flag without a removal date fails CI | Revert PR | | |
| 2.13 | Bridge: build `RemoteConfig` from the flag store; old call sites keep working | 12 §4 | B | `remote_config_repository_test.dart` passes unchanged | Halt rollout, hotfix | | |
| 2.14 | Debug flag-override screen in dev and SIT flavors only | 12 §10 | A (not in prod) | Prod build has no override screen | Revert PR | | |
| 2.15 | Composition root `app_overrides.dart` and wiring test | 10 §1 | B | Wiring test fails if one override is removed; SIT runs the same | Halt rollout, hotfix | | |
| 2.16 | DI rules, `container-lookup` ratchet, `implementation_imports` lint | 10 §2 | A | Ratchet passes on `master` | Revert PR | | |
| 2.17 | Make R8 explicit (`minifyEnabled`, `shrinkResources`), fail the prod build without `mapping.txt`, review keep rules. R8 already runs, so the output should match | 01 §1, 04 §5 | B | Smoke list on a prod-like build: login, OTP, KYC liveness, document capture, loan submission, payment, push, deep link, in-app update; readable stack traces in Crashlytics and Datadog | Halt rollout, hotfix | | |
| 2.18 | Empty "Protect build" and "Register build" slots in the prod workflow | 04 §5 | A | Prod build passes with the empty steps | Revert PR | | |
| 2.19 | Reusable build workflows, one `--dart-define` file, actions pinned to SHAs | 04 §4 | A | Workflow lines under 1,500; SIT APK size same as before | Revert PR | | |
| 2.20 | Widget-test helper that runs the same test on both paths | 03 §9 | A | A test that fails only on the new path shows one green and one red | Revert PR | | |
| 2.21 | Force a switch flag in SIT and UAT builds with a `--dart-define` (prod ignores it); e2e specs tag the flag value | 03 §10 | A (not in prod) | The 4 journeys pass with the flag forced off and on | Revert PR | | |
| 2.22 | e2e suite runs twice per release candidate (all switch flags off, all on) | 04 §7 | A | Both runs linked in release notes | Make it a checklist item again | | |
| 2.23 | Cohort dashboard: split health and funnels by switch-flag state, thresholds in red | 04 §8 (second half) | A | A test flag in SIT shows both cohorts | Not needed | | |
| 2.24 | Kill-switch runbook; rehearse once in SIT | 04 §9 | A | Rehearsal recorded with the time from alert to flip | Not needed | | |
| 2.25 | Sign the Android bundle with the upload key held in Cloud KMS (HSM) through its PKCS#11 library and `jarsigner`, after a proof of concept. CI signs in keyless and never holds the key. *Added 20 Oct 2026 from the key-location review in Phase 0 notes.* | Phase 0 notes, key table | A | The signed bundle verifies with `apksigner verify`; Play accepts it on the internal track; the keystore file is gone from the environment secrets | Put the keystore secret back | | |

## Phase 3: Approved deltas, one per release

**Jira epic:** *(add)*

**Goal.** Fix the privacy and security items that are meant to change behaviour. Each one is signed off, shipped alone in its release, and watched on the dashboard.

**Entry gate.** Phase 2 exit gate met. Each delta is listed in the "Approved deltas" table on the parent page with its sign-off.

**Exit gate.** Every delta in this phase is at 100% for 1 release with no regression. Class E steps are in monitor-only mode at least.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1 | `PiiSanitizer` before anything leaves the device (Datadog, Crashlytics). Data protection officer signs off | 05 §1 | D | Sanitiser 100% unit-tested; a phone number in a message arrives redacted | Halt rollout, hotfix | | |
| 3.2 | Clean the 35 log call sites: fixed message plus the error as a field | 05 §6 | D (log text only) | `grep` finds no `$error` in error messages | Halt rollout, hotfix | | |
| 3.3 | Consent and PII key denylist in the analytics fan-out; pass the real consent to Datadog | 02 §5 | D | Unit test drops a denied key; `product_name` still passes | Kill-switch flag on the denylist | | |
| 3.4 | Remove `customer_address` from `apply_loan` (or city only); bucket income and amount. Dashboard owner and data protection officer sign off | 02 §6 | D | Golden names file shows only the agreed change; dashboard owner confirms | Halt rollout, hotfix | | |
| 3.5 | Pseudonymous user ID (customer ID only) in Crashlytics and Datadog | 05 §5 | D | A dev crash shows the customer ID and nothing else | Halt rollout, hotfix | | |
| 3.6 | Remote log threshold `info` in prod, sampling values written down | 05 §9 | D (log volume only) | Datadog log volume within the agreed range after 1 day | Halt rollout, hotfix | | |
| 3.7 | Security flags fail safe: root check default on, CI check on prod variables. Re-check root on resume | 01 §2 | D | Root check value in prod is unchanged (already on); resume check tested on a rooted SIT device | Halt rollout, hotfix | | |
| 3.8 | Screen-capture guard on PIN, OTP, KTP and selfie, KYC review, e-sign, bank form, payment, behind a Remote Config kill switch | 01 §4 | D | e2e journeys pass; screenshots on those screens are blank on Android and iOS | Kill switch off | | |
| 3.9 | Secure storage: delete KYC and vehicle images after upload, keep them out of backups, WebView domain allow-list. Check draft resume still works | 01 §5 | D | KYC and document capture journeys pass; loan draft resume passes | Halt rollout, hotfix | | |
| 3.10 | `API_SECRET` treated as public: backend checks user token and integrity verdict on every sensitive endpoint. Monitor-only first, enforce after the minimum supported version | 01 §3 | E | Backend logs show 0 would-be blocks from current app versions for 2 weeks | Backend back to monitor-only | | |
| 3.11 | RASP free trial: freeRASP in report-only mode on SIT builds for 2 sprints to measure false positives. Not in prod | 01 §7 (trial) | A (SIT only) | False-positive report written | Remove from SIT build | | |

## Phase 4: Network chain behind a switch flag

**Jira epic:** *(add)*

**Goal.** Move auth, refresh, headers, errors and retry into dio interceptors and fix the token-refresh race. The whole new chain sits behind one switch flag, `useNewHttpChain`, so the 114 repository call sites do not change.

**Entry gate.** Phase 3 exit gate met. Recorded fixtures (1.13) and race tests (1.15) exist.

**Exit gate.** `useNewHttpChain` at 100% for 2 releases with no regression in HTTP error rate, session-expired count or screen load. Old request code and the flag deleted.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1 | Add switch flag `useNewHttpChain` to the catalogue (owner, removal date, default old). The facade picks the path | 07 parity | C | Flag off = today's behaviour on all tests | Flag off | | |
| 4.2 | Extract `TokenRefresher` (new path) | 07 §2 | C | 5 parallel 401s cause exactly 1 refresh; the 41 old tests pass | Flag off | | |
| 4.3 | Two dio instances (`authDio`, `apiDio`); remove the `DeviceIntegrityService` setter cycle | 07 §3 | C | Login, guest start and PIN flows pass on SIT with the flag on | Flag off | | |
| 4.4 | Headers and integrity interceptors. Add `x-request-id` only after SRE confirms the gateway and backends accept it | 07 §4 | C + E | Contract replay: same requests on both paths, except the approved new header | Flag off | | |
| 4.5 | Auth and refresh interceptors | 07 §5 | C | Refresh and restricted-session tests pass against the interceptors | Flag off | | |
| 4.6 | Error-mapping interceptor; `appUpdateRequiredProvider` replaces the global event | 07 §6 | C | Widget test: "app update required" dialog still shows | Flag off | | |
| 4.7 | Retry interceptor for idempotent GETs only | 07 §7 | C (approved delta) | GET retried twice on 503; POST never retried | Flag off | | |
| 4.8 | Trace headers in the Datadog first-party host config, only if the 1.25 spike found gaps | 05 §8, 07 §8 | C + E | A RUM resource links to its APM trace | Flag off | | |
| 4.9 | Cohort rollout of `useNewHttpChain`: 1% → 10% → 50% → 100%, one day of data per stage | 07 parity, 04 §8 | C | Cohort dashboard green at each stage | Flag off (runbook) | | |
| 4.10 | Flip and delete: remove old request code and the flag; shrink `HttpClient` under 150 lines | 07 §9 | B | 2 releases at 100% with no regression | Halt rollout, hotfix | | |

## Phase 5: Move call sites, feature by feature

**Jira epic:** *(add)*

**Goal.** Move every analytics, flag and log call to the new ports, one feature per PR. Then delete the old shims. Customers see no change.

**Entry gate.** Phase 2 exit gate met. This phase can run next to Phases 3 and 4, because its PRs are class B.

**Exit gate.** All direct-call baselines at 0. Shims and `RemoteConfig` deleted. Catalogues published.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1 | Migrate Firebase analytics calls, one feature per PR: `account`, `payment_method`, `promo`, `pin`, then `home`, `auth`, `loan` (one sub-ticket per feature) | 02 §8 | B | Golden names file unchanged; Firebase DebugView shows the same names; baseline goes down | Halt rollout, hotfix | | |
| 5.2 | Move Remote Config call sites to `flagProvider`, one feature per PR: `home`, `loan`, `auth`, `pin`, `rl`, `ro` | 12 §5 | B | Widget tests give the same result with old and new reads | Halt rollout, hotfix | | |
| 5.3 | Move the two Mixpanel experiments into the catalogue | 12 §6 | B | One `experiment-exposure` event per key per session, same as today | Halt rollout, hotfix | | |
| 5.4 | Delete the analytics shims and make the CI count strict | 02 §9 | B | Baseline 0 | Revert PR | | |
| 5.5 | Delete `RemoteConfig` and its generated code | 12 §7 | B | No `RemoteConfig` type left in `digital/lib` | Revert PR | | |
| 5.6 | Publish the analytics event catalogue; product analytics owns it in `CODEOWNERS` | 02 §10 | A | `event-catalogue.md` generated in CI | Revert PR | | |
| 5.7 | Flag lifecycle check in CI and `docs/flags.md` | 12 §9 | A | An overdue release flag fails CI | Revert PR | | |
| 5.8 | First flag clean-up: remove `featureFlagSurveyor`, `featureFlagLov` and every flag the owner confirms is fully on (one PR per flag) | 12 §8 | B | Owner confirms the prod value in the ticket | Halt rollout, hotfix | | |

## Phase 6: Riverpod 3 upgrade on its own

**Jira epic:** *(add)*

**Goal.** Move to Riverpod 3 without converting any controller. This is a dependency upgrade that touches every screen, so it ships in a release with no other class B, C or D change.

**Entry gate.** Phases 2 and 5 exit gates met.

**Exit gate.** 1 release at 100% with no new provider errors in Datadog and no health regression.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1 | Bump `flutter_riverpod` to 3; export `legacy.dart` so the 72 controllers compile unchanged; rename `valueOrNull`; update `DatadogLogObserver` | 09 §2 | B | `melos test` passes; full parity net green | Halt rollout, hotfix to the previous version | | |
| 6.2 | Turn automatic retry off in `main.dart` and test containers, to keep today's behaviour | 09 §2 | B | Tests for failing providers show no retry | Halt rollout, hotfix | | |
| 6.3 | Release alone: Play 5% → 100% with the health dashboard; manual SIT smoke for login, KYC, loan apply, payment | 09 §2 | B | No new provider errors after each stage | Halt rollout | | |

## Phase 7: Loan pilot through the parity loop

**Jira epic:** *(add)*

**Goal.** Prove the target architecture on `loan`, the biggest feature, without changing what customers see. Domain layer, Notifiers and no globals, all behind `useNewLoanFlow`.

**Entry gate.** Phases 4 and 6 exit gates met (the network chain and Riverpod 3 are settled, so cohort data is clean).

**Exit gate.** `useNewLoanFlow` at 100% for 2 releases with no regression. Old loan path, old tests and the flag deleted. `dto-in-presentation` for `loan` is 0.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1 | Layer rules in `.claude/rules/` and `AGENTS.md`; `domain-purity` (strict) and `dto-in-presentation` (ratchet 214) in the checker; AI review skill | 08 §1, 06 §5 | A | A domain file that imports Flutter fails | Revert PR | | |
| 7.2 | Pure barrel `shared_lib/core/lib/pure.dart` | 08 §2 | B | Script confirms no Flutter import is reachable from `pure.dart` | Halt rollout, hotfix | | |
| 7.3 | Loan parity ledger from today's behaviour; write missing old-path tests; add `useNewLoanFlow` | 08 §3 | A | Feature owner signs off; every row has an old-path test | Revert PR | | |
| 7.4 | `UiFeedback` port replaces reads of `CommonController` in flows | 10 §3 | B | 0 reads of `CommonController` outside `digital/lib/app/` | Halt rollout, hotfix | | |
| 7.5 | Remove `appRef` from app services and widgets (39 uses) | 09 §3 | B | `app-ref` count drops by 39; parity net green | Halt rollout, hotfix | | |
| 7.6 | Slice 1, loan detail: domain types, mapper, repository; new path behind `useNewLoanFlow` | 08 §4 | C | Golden, fixture replay and widget tests green on both paths | Flag off | | |
| 7.7 | Slice 2, agreement: tab and overdue rules into domain; old and new give the same output | 08 §5 | C | Same inputs, same outputs on both paths | Flag off | | |
| 7.8 | Slices 3 to 6: submission, survey, simulation, submission list (one sub-ticket each); new notifiers beside old controllers | 08 §6, 09 §5, 03 §5 | C | 4 submission e2e specs pass with the flag forced off and on | Flag off | | |
| 7.9 | Split `esign` flow; remove `appRef` and `navigatorContext` from loan flows | 08 §7, 09 §4 | C | No file under `presentation/flows/` reads a global | Flag off | | |
| 7.10 | `LoanExits` exit port: payment, `ro`, RL, BPKB, onboarding | 10 §5 | C | `loan` has 0 imports of other features' screens | Flag off | | |
| 7.11 | Cohort rollout of `useNewLoanFlow`: 1% → 10% → 50% → 100%. Do not move the Play dial in the same week | 08 §8 | C | Each stage noted in the ledger with its dashboard result | Flag off (runbook) | | |
| 7.12 | Flip and delete the old loan path, tests and flag. Remote Config key deleted one release later | 08 §9 | B | No reference to `useNewLoanFlow`; `dto-in-presentation` for `loan` = 0 | Halt rollout, hotfix | | |

## Phase 8: Packages, move only

**Jira epic:** *(add)*

**Goal.** Move code into packages without changing behaviour: first the shared packages every feature needs (design system, l10n, forms), then `loan`. Tests and golden files must not change.

**Entry gate.** Phase 7 exit gate met. Design system scope agreed with design (8.1 can start earlier).

**Exit gate.** `features/loan` is its own package with no feature dependency. All 4 flavors build. Golden screenshots unchanged.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1 | Agree design-system scope and token names with design | 13 §1 | A | Signed-off list of components and tokens | Not needed | | |
| 8.2 | Cut component dependencies on the app (callbacks for tracking, strings as parameters) | 13 §2 | B | `grep "package:digital/"` in components returns 0; golden names unchanged | Halt rollout, hotfix | | |
| 8.3 | Create `shared_lib/design_system` and move theme, then components (one folder per PR, re-export for one release) | 13 §3 | B | Golden screenshots unchanged; `melos test` passes | Halt rollout, hotfix | | |
| 8.4 | Widgetbook, built on every PR that touches the package, published internally | 13 §4 | A | A designer opens the link and sees every component | Revert PR | | |
| 8.5 | Guard design rules: ratchet on new raw `Color(0x…)` and `TextStyle(`; component goldens | 13 §5, 03 §12 | A | A PR with a new raw colour fails | Revert PR | | |
| 8.6 | Move `app/localizations` and `app/dsl` to `shared_lib` | 11 §2 | B | No feature imports `package:digital/app/` for `ui`, `theme`, `localizations` or `dsl` | Halt rollout, hotfix | | |
| 8.7 | Pilot package: `support` | 11 §3 | B | All 4 flavors build; moved tests run in CI | Halt rollout, hotfix | | |
| 8.8 | Routes per feature, still inside `digital`; cross-feature pushes through exit ports | 11 §4 | B | `router-import` = 0; deep links tested on SIT | Halt rollout, hotfix | | |
| 8.9 | `auth_api` ports (`SessionReader`, `LoginLauncher`, `KycLauncher`); switch `loan` callers first | 11 §5, 10 §4 | B | `loan` imports of `auth` use cases = 0 | Halt rollout, hotfix | | |
| 8.10 | Extract `select_vehicle` | 11 §6 | B | All 4 flavors build | Halt rollout, hotfix | | |
| 8.11 | Decouple the remaining `loan` edges (`home → loan` through `loan_api`) | 11 §7 | B | `feature-import` for `loan` in and out = 0 | Halt rollout, hotfix | | |
| 8.12 | Extract `loan` with its own providers, test helpers and loan-only repositories | 11 §8, 10 §7, 08 §10 | B | SIT smoke: apply, detail, agreement, survey; goldens unchanged | Halt rollout, hotfix | | |

## Phase 9: Other features through the same loop

**Jira epic:** *(add)*

**Goal.** Repeat Phases 7 and 8 for `auth`, `rl`, `ro` and the rest. One feature at a time, each with its own ledger and switch flag (for example `useNewKycFlow`).

**Entry gate.** Phase 8 exit gate met.

**Exit gate.** Every feature's old path deleted. `app-ref` and `state-notifier` at 0. `data/customer` empty.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1 | `auth`: ledger, `useNewKycFlow`, split KYC flows, domain layer, Notifiers, cohort, flip and delete, then extract | 08 §7, §11; 09 §4, §6; 11 §9 | C, then B | Same checks as 7.3 to 7.12 and 8.12 | Flag off | | |
| 9.2 | `rl`: same loop | 08 §11, 09 §6, 11 §9 | C, then B | Same checks | Flag off | | |
| 9.3 | `ro`: same loop (expect it harder: 35 imports out) | 08 §11, 09 §6, 11 §9 | C, then B | Same checks | Flag off | | |
| 9.4 | Remaining features (29 smaller controllers, 3 in `app/`), `CommonController` last | 09 §6 | C or B by size | Same checks | Flag off or hotfix | | |
| 9.5 | Remove the legacy Riverpod layer (`legacy.dart`, global `appRef`) | 09 §7 | B | App compiles without them | Halt rollout, hotfix | | |
| 9.6 | Shared service ports and smaller barrels; empty `data/customer` | 10 §6, §8; 11 §10 | B | `customer-repo-growth` baseline only goes down to 0 | Halt rollout, hotfix | | |

Start a new feature's rollout only when the previous one is past 50%, so two cohort checks never overlap on the same journey.

## Phase 10: Platform

**Jira epic:** *(add)*

**Goal.** The larger platform items that need a vendor or a product decision.

**Entry gate.** Vendor or product decision made for each item. Can run next to Phase 9 if the release rules hold.

**Exit gate.** Per item.

| # | Step | Plan ref | Class | Check before release | Rollback | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10.1 | RASP in prod, **report-only mode first**. A false positive would block a real customer, so watch the report rate for 2 releases before you enforce. Fill the "Protect build" and "Register build" slots | 01 §7, 04 §5 | D | False-positive rate within the PoC limit in report-only mode | Report-only via remote config, or halt rollout | | |
| 10.2 | RASP enforce mode, after 10.1 is clean | 01 §7 | D | Cohort dashboard green; support tickets about blocked devices reviewed | Back to report-only | | |
| 10.3 | Material 3, inside the design-system package, with goldens in place first | 13 §7 | D | Golden diffs reviewed and signed off by design | Halt rollout, hotfix | | |
| 10.4 | Optional: Figma token pipeline | 13 §6 | B | Generated tokens match the JSON | Revert PR | | |
| 10.5 | Optional: journey milestones to AppsFlyer and Datadog RUM | 02 §11 | D | Product decision recorded | Remove the sink | | |
| 10.6 | Optional: fastlane and match for iOS signing | 04 §10 | A | iOS build signs with the same certificates | Revert PR | | |

## Rollout and rollback

Every class C or D step goes through the same loop.

* **Who decides.** The feature owner named in the flag catalogue decides each step up. The mobile on-call can flip back without asking.
* **Time to flip back.** Target 15 minutes from alert to flag change (Mobile plan 04, step 9). Switch flags are real-time, so open apps use the old path at the next journey start.
* **Store rollout.** If a new build is suspected, halt the Play rollout and pause the iOS phased release. Ship a hotfix through the normal release branch.
* **Old app versions.** Users who do not update keep the old code. Backend changes (class E) must keep working for them until the minimum supported version is raised. The app already shows an "app update required" dialog for one backend error code (Mobile plan 07, step 6). Raising the minimum version is a product decision.
* **Record it.** Every flip or halt gets a short note in the feature's parity ledger.

## Mapping to the plan pages

Every numbered step of Mobile plans 01 to 13 has a row above. This table shows where each plan's steps landed.

| Plan | Steps | Phases |
| --- | --- | --- |
| 01 Security | §0 → 0.1–0.6; §1 → 2.17; §2 → 3.7; §3 → 3.10; §4 → 3.8; §5 → 3.9; §6 → 1.6; §7 → 1.24, 3.11, 10.1, 10.2; §8 → 1.23 | 0, 1, 2, 3, 10 |
| 02 Analytics wrapper | §1 → 1.11; §2–4 → 2.1–2.3; §5–6 → 3.3–3.4; §7 → 2.4; §8–10 → 5.1, 5.4, 5.6; §11 → 10.5 | 1, 2, 3, 5, 10 |
| 03 Testing | §1–4 → 1.7–1.10; §5 → 7.8; §6–8 → 1.14, 1.12, 1.13; §9–10 → 2.20–2.21; §11 → 1.16; §12 → 8.5 | 1, 2, 7, 8 |
| 04 CI/CD | §1 → 0.3–0.5; §2–3 → 1.1–1.2; §4 → 2.19; §5 → 2.17–2.18; §6 → 1.3; §7 → 2.22; §8 → 1.4, 2.23; §9 → 2.24; §10 → 10.6; §11 → 0.6–0.7; §12 → 1.5 | 0, 1, 2, 10 |
| 05 Logging and crashes | §1 → 3.1; §2–4 → 2.5–2.7; §5 → 3.5; §6 → 3.2; §7 → 1.25; §8 → 4.8; §9 → 3.6; §10 → 2.9; flag tag → 2.8 | 1, 2, 3, 4 |
| 06 Lint and guardrails | §1–2 → 1.17–1.18; §3 → 1.19; §4 → 1.22; §5 → 7.1; §6 → 1.21 | 1, 7 |
| 07 Networking | §1 → 1.15; §2–7 → 4.2–4.7; §8 → 4.8; §9 → 4.10 | 1, 4 |
| 08 Layering | §1–2 → 7.1–7.2; §3 → 7.3; §4–9 → 7.6–7.12; §10 → 8.12, 9.6; §11 → 9.1–9.3 | 7, 8, 9 |
| 09 State management | §1 → 1.20; §2 → 6.1–6.3; §3 → 7.5; §4 → 7.9, 9.1; §5 → 7.8; §6 → 9.1–9.4; §7 → 9.5 | 1, 6, 7, 9 |
| 10 Dependency injection | §1–2 → 2.15–2.16; §3 → 7.4; §4 → 8.9; §5 → 7.10; §6 → 9.6; §7 → 8.12; §8 → 9.6 | 2, 7, 8, 9 |
| 11 Repo layout | §1 → 1.19; §2 → 8.6; §3–8 → 8.7–8.12; §9 → 9.1–9.3; §10 → 9.6 | 1, 8, 9 |
| 12 Feature flags | §1–4 → 2.10–2.13; §5–7 → 5.2, 5.3, 5.5; §8 → 5.8; §9 → 5.7; §10 → 2.14 | 2, 5 |
| 13 Design system | §1–5 → 8.1–8.5; §6 → 10.4; §7 → 10.3 | 8, 10 |

**What moved compared with the old roadmap.**

* Coverage gate, one Flutter version and the analytics golden file moved **earlier**, into Phase 1, because they cost customers nothing and protect everything after them.
* The analytics wrapper is split. The seams ship first with no change (Phase 2). The personal-data fixes ship later, one per release (Phase 3). Call sites move last (Phase 5).
* dio interceptors moved **out of** the architecture phase into their own phase behind one switch flag (Phase 4). The refresh race touches every logged-in user.
* The Riverpod 3 upgrade has its own phase (Phase 6), because it touches every screen.
* The design-system package moved from "platform" to Phase 8, because the `loan` package needs it.
* The e2e suite moved from "platform" to Phase 1. It is part of the safety net.
* RASP is split: RFP now (Phase 1), SIT trial in Phase 3, prod in report-only mode first (Phase 10).

## Open questions

1. **Owner.** Who owns the roadmap and each epic? The Customer Mobile Apps squad with a named tech lead is the suggestion (parent page, question 1).
2. **Stop thresholds.** Product and SRE agree the numbers in "Release rules" before Phase 1 ends.
3. **Minimum supported app version.** Who decides when to raise it, and how often? Class E steps (3.10, 4.4, 4.8) need an answer.
4. **Go or no-go at each rollout stage.** Is it the feature owner alone, or the feature owner plus QA?
5. **Coverage threshold.** 70% on changed files to start (parent page, question 3).
6. **RASP vendor and budget** (parent page, question 2).
7. **Design system: build our own or adopt DK's library** (parent page, question 5). Phase 8 assumes we build our own.
