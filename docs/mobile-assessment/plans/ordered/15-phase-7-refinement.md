## Summary

This page prepares Phase 7 of the mobile roadmap ("Loan pilot through the parity loop") for refinement. It covers all 12 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Loan Pilot".
* **Parent:** Mobile roadmap: step by step, section "Phase 7: Loan pilot through the parity loop". Plan pages: Mobile plan 08: Layering, Mobile plan 09: State management, Mobile plan 10: Dependency injection.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct).

**What Phase 7 is.** The target architecture (domain layer, Notifiers, no globals, ports) is proven on `loan`, the biggest feature, without changing what customers see. New code sits beside old code behind `useNewLoanFlow`. The same tests run on both paths. Then a cohort rollout, a flip, and the old path is deleted. This is the strangler pattern applied inside one app: the new path grows around the old one until the old one can be removed. The known risk of that pattern is keeping both paths forever, which is why the flag has a removal date and the exit gate is "old path deleted".

### Five facts that shape Phase 7

**1. `loan` is bigger than the plan said, and still growing.** 167 files and 31,216 lines today (plan 08: 130 files). By sub-folder: `submission` 51 files / 9,285 lines, `agreement` 56 / 7,652, `detail` 15 / 4,788, `survey` 14 / 3,733, `calculation_card` 5 / 1,521, `submission_list` 9 / 1,327, `simulation` 7 / 1,173, `calculation_field` 3 / 1,005. 30 `StateNotifier` controllers in `loan` (plan 09: 21). Biggest files: `loan_detail_screen.dart` 1,421 lines, `submission_controller.dart` 1,182, `review_submission_screen.dart` 1,142.

**2. There is no domain layer anywhere.** 0 `domain/` folders in the repo. 240 feature files outside `data/` import `package:customer/` (API models); 94 of them in `loan` (plan 08: 214 and the loan share not given).

**3. Globals are everywhere in the flows.** `appRef` and `navigatorContext` counts in the flow files: `esign_use_case` 503 lines (11 / 25), `kyc_use_case` 1,049 (23 / 37), `auth_flow_use_case` 343 (19 / 11), `kyc_spouse_use_case` 375 (7 / 18), `capture_use_case` 152 (14 / 8), `ro_use_case` 304 (9 / 2), `open_agreement_detail_use_case` 99 (3 / 1). `CommonController.provider` is read 63 times across the app.

**4. The pure barrel is cheap.** `shared_lib/core/lib/src` has 21 files, only 2 import Flutter. So `pure.dart` (7.2) is a small change.

**5. Repository ownership is clearer than the plan listed.** By `grep` today: `SurveyRepository` is used only by `loan`; `AssetDocumentRepository` by `loan` and `bpkb_release`; `CommonRepository` and `RlRepository` by `loan` and `rl`; `RoRepository` by `loan` and `ro`; `StaticConfigRepository` by 9 features. Plan 08 named 5 loan-only repositories; only `SurveyRepository` was confirmed by this check (the others live in sub-folders my search did not resolve, so verify before 8.12).

Other counts: `getLoanDetailUseCase` 19 references (plan: 18), `DateUtils.dateOnly` 8 uses in `loan`, `select_vehicle` is imported by `loan` 30 times.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **C** = behind `useNewLoanFlow`, **B** = same behaviour, **A** = no app change.

| # | Proposed ticket title | Today (23 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1 | `chore: Layer rules, domain-purity and dto-in-presentation checker rules, review skill` | No rules, no `domain/` | A | Mobile engineer | S | 1.19 | | |
| 7.2 | `feat(core): pure.dart barrel` | 2 of 21 core files import Flutter | B | Mobile engineer | XS | – | | |
| 7.3 | `docs(loan): Parity ledger, missing old-path tests, useNewLoanFlow flag` | No ledger | A | QA + feature owner | M | 1.16, 2.12 | | |
| 7.4 | `feat(app): UiFeedback port replaces CommonController reads in flows` | 63 reads | B | Mobile engineer | S | 2.15 | | |
| 7.5 | `refactor(app): Remove appRef from services and widgets` | 131 `appRef.` uses in total | B | Mobile engineer | M | 6.3 | | |
| 7.6 | `feat(loan): Slice 1, loan detail on the new path` | `detail` 15 files / 4,788 lines | C | Mobile engineer | M | 7.1–7.4 | | |
| 7.7 | `feat(loan): Slice 2, agreement rules into domain` | `agreement` 56 / 7,652 | C | Mobile engineer | L | 7.6 | | |
| 7.8 | `feat(loan): Slices 3–6, submission, survey, simulation, submission list` (one sub-ticket each) | 51 + 14 + 7 + 9 files | C | 2 mobile engineers | L (4–6 PRs) | 7.7 | | |
| 7.9 | `refactor(loan): Split esign flow, remove globals from loan flows` | `esign_use_case` 503 lines, 36 global reads | C | Mobile engineer | M | 7.8 | | |
| 7.10 | `feat(loan): LoanExits exit port` | Direct pushes to payment, ro, rl, bpkb, onboarding | C | Mobile engineer | S | 7.6 | | |
| 7.11 | Cohort rollout of `useNewLoanFlow` 1% → 10% → 50% → 100% | – | C | Feature owner + on-call | 2–4 weeks | 7.6–7.10, 2.23 | | |
| 7.12 | `refactor(loan): Flip and delete the old loan path` | – | B | Mobile engineer | M | 7.11 | | |

**Suggested order.** Sprint 1: 7.1, 7.2, 7.3, 7.4. Sprint 2: 7.5, 7.6. Sprints 3–4: 7.7, 7.10. Sprints 5–7: 7.8 (two engineers, one sub-folder each). Sprint 8: 7.9. Then 7.11 for 2–4 weeks, then 7.12. About one quarter in total.

## Definition of ready for every Phase 7 ticket

* The ledger rows the ticket will turn green are listed (from 7.3).
* For class C tickets: the ticket names the goldens, fixtures and e2e specs that must pass with the flag off and on.
* The new path imports nothing from `package:customer/` outside `data/` (checker rule from 7.1 is strict for new files).
* No old-path file is edited, except to add a test. If an old file must change, the ticket says why.

## Step 7.1: Layer rules and checker rules

**Today.** No written layer rules beyond `AGENTS.md`. No `domain/` folder. 240 files import API models into screens and controllers.

**Tasks.** `.claude/rules/layer-model.md` and `feature-layers.md` in BFI's words. Update the "Layered Architecture", "UseCases" and "Data Layer" sections of `AGENTS.md`. Two checker rules: `domain-purity` (strict: a file under `domain/` that imports Flutter, Riverpod, `core.dart`, `package:customer/`, `data/` or `presentation/` fails; count today 0) and `dto-in-presentation` (ratchet, baseline on merge day, about 240). Add `.claude/skills/mr-review/SKILL.md` that checks a diff against the rules.

**Acceptance criteria.** A branch that adds `import 'package:flutter/material.dart'` to a domain file fails. The review skill finds real issues on 3 recent merged PRs with few false alarms.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules in `.claude/rules` + the Phase 1 checker + a review skill | One source of truth for humans, CI and AI tools | Rules must be short to be read |
| B. An analyzer plugin (`import_rules`) for the strict rule, checker for the ratchet | IDE feedback for domain purity | Two tools; the plugin needs Dart 3.10+, which the app has |
| C. Review only | No code | 240 violations show how review alone did |

**Recommended: A**, B as a bonus for the strict rule if it runs clean.

## Step 7.2: Pure barrel in core

**Today.** `shared_lib/core/lib/src`: 21 files, 2 import Flutter (`constants/product.dart` through the full barrel, `extension/datetime_extension.dart` through `material.dart`).

**Tasks.** `shared_lib/core/lib/pure.dart` exports only Flutter-free files. Fix the 2 imports. Export `Product`, `ProductCategory` and the date extensions from `pure.dart`.

**Acceptance criteria.** A script confirms no file reachable from `pure.dart` imports Flutter. Existing tests pass unchanged.

**Who / size.** One mobile engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `pure.dart` barrel in `core` | Smallest change | `core` still has Flutter code; fine until Phase 8 |
| B. New package `shared_lib/pure` | Package boundary enforces purity | More files to move now |
| C. Domain imports `core.dart` and we accept Flutter in domain | No work | Breaks `domain-purity`; domain tests would need a widget binding |

**Recommended: A now, B in Phase 8** when `core` is split.

## Step 7.3: Loan parity ledger, missing tests, switch flag

**Today.** No ledger. e2e specs that cover loan: `loan-detail`, `loan-list`, `agreement-list`, `loan-simulation`, 4 submission specs. Golden names file from Phase 1.

**Tasks.** Copy the ledger template to `docs/parity/loan.md`. One row per behaviour: loan detail, agreement tabs and overdue rules, submission, survey, simulation, submission list, e-sign. Where a row has no old-path test, write one now against today's output. List the approved deltas that touch `loan` (from Phase 3). Add `useNewLoanFlow` to the catalogue: owner, removal date, default old, real-time, read at journey start.

**Acceptance criteria.** Feature owner signs the ledger. Every row has an old-path test. The flag exists and the both-paths helper (2.20) can switch it.

**Who / size.** QA + feature owner + one engineer for the missing tests. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ledger first, tests against today's output, then code | The rule from the plan: write the test before the move | Feels slow; it is the thing that makes the rest safe |
| B. Ledger written as slices land | Faster start | Rows get written to match the new code, not today's behaviour |
| C. e2e only, no ledger | Less paperwork | No per-behaviour trace; the flip decision has no evidence table |

**Recommended: A.**

## Step 7.4: `UiFeedback` port

**Today.** 63 reads of `CommonController.provider` (loading overlay, error dialogs, snack bars), many through `appRef`.

**Tasks.** Interface `UiFeedback` (`showLoading`, `showError`, `showSnackBar`). The app implements it with today's `CommonController`. Flows read `ref.read(uiFeedbackProvider)` instead of the global.

**Acceptance criteria.** 0 reads of `CommonController` outside `digital/lib/app/`. Existing screen tests pass unchanged. Golden screenshots unchanged.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One port, implemented by the existing controller | Zero visible change, removes 63 global reads | The controller still exists until Phase 9 |
| B. Each screen owns its overlay now | End state in one step | Touches every screen; not class B |
| C. Keep `CommonController` reads | No work | The global stays in every flow |

**Recommended: A.**

## Step 7.5: Remove `appRef` from services and widgets

**Today.** 131 `appRef.` uses across the app (plan 09 said 142; 120 on 11 Sep, so it grew and then moved). Services: `ipv_service.dart`, `push_notification_util.dart`, `go_router_extension.dart`, `tracker_journey_manager.dart`, `deep_link_handler.dart`. Widgets use it in about 15 places.

**Tasks.** Each service becomes a provider that gets `Ref`. Navigation reads the `GoRouter` from a provider instead of `navigatorContext`. Widgets use their own `ref`. The `Digital*` components get callbacks (done in 2.4).

**Acceptance criteria.** `app-ref` ratchet drops by the services-and-widgets share (about 39 per the plan; measure on the day). Parity net green. No `UnmountedRefException` on SIT (Riverpod 3 is live after Phase 6).

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Services to providers, widgets to their own `ref`, flows later (7.9) | Mechanical, class B, testable | The flows still hold most uses |
| B. Everything at once, including flows | One sweep | Flows need the domain split (7.9) to do it right |
| C. Keep `appRef`, add `ref.mounted` guards only | Smaller | Riverpod 3 made stale refs throw; the global stays the main source |

**Recommended: A.**

## Step 7.6: Slice 1, loan detail

**Today.** `loan/detail`: 15 files, 4,788 lines; `loan_detail_screen.dart` alone is 1,421 lines. `getLoanDetailUseCase` has 19 references. Screens read API models directly.

**Tasks.** Add `domain/` and `data/` folders inside `digital/lib/features/loan/`. `LoanApplicationStatus`, `LoanApplicationRepository`, a mapper, `LoanApplicationRepositoryImpl` wrapping `LoanOnboardingRepository`. A new detail path that reads the interface, beside the old one. `useNewLoanFlow` picks the path at journey start.

**Acceptance criteria.** New-path `loan/detail/` screens and notifiers import nothing from `package:customer/`. Mapper unit tests. Golden screenshot of loan detail identical on both paths. Fixture replay identical. Ledger rows for loan detail green on both paths.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Vertical slice: entity, repository interface, mapper, one screen, behind the flag | Proves the whole shape end to end on the smallest sub-folder | Two detail screens exist for a while |
| B. Build the full loan domain first, then switch screens | Clean layering | Months before anything is proven; big-bang risk |
| C. Map API models to domain inside the old screen | Smallest diff | No new path; nothing to compare in a cohort |

**Recommended: A.**

## Step 7.7: Slice 2, agreement rules into domain

**Today.** `agreement`: 56 files, 7,652 lines. Tab split in `agreement_mapper.dart`, overdue rules in `agreement_status_extension.dart`, 8 uses of `DateUtils.dateOnly` (a Flutter helper) in `loan`.

**Tasks.** `domain/usecases/split_agreements_by_tab.dart` on an `Agreement` entity. Overdue rules into domain with a pure date helper. Old mapper and extension stay until 7.12. Both rules must give identical tabs and labels for the same input.

**Acceptance criteria.** Plain unit tests with no widget binding for both rules. A property test feeds the same inputs to old and new and compares. Agreement list golden identical on both paths.

**Who / size.** One mobile engineer. L (2–3 PRs).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules first (pure functions with tests), then the screen | The riskiest logic gets the cheapest tests | Screen work waits a sprint |
| B. Screen first, rules later | Visible progress | Rules stay in the mapper; the cohort compares pixels, not logic |
| C. Both at once | One PR | Too big to review |

**Recommended: A.**

## Step 7.8: Slices 3–6, submission, survey, simulation, submission list

**Today.** `submission` 51 files / 9,285 lines, `submission_controller.dart` 1,182 lines; `survey` 14 / 3,733; `simulation` 7 / 1,173; `submission_list` 9 / 1,327. 4 submission e2e specs exist.

**Tasks.** One sub-folder per sub-ticket. Pull rules out of `submission_controller.dart` into use cases. New notifiers live beside old controllers. The 4 submission e2e specs run with the flag forced off and on. Notifier tests (controller-test ban lifted in 1.7).

**Acceptance criteria.** No new-path file in `loan` imports `package:customer/`. The 4 submission specs pass on both paths. Each sub-folder's ledger rows green.

**Who / size.** Two mobile engineers in parallel. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One sub-folder per sub-ticket, two engineers | Parallel, reviewable | Shared code between submission and survey needs coordination |
| B. All four in one ticket | Simple tracking | 81 files, one reviewer, one PR; no |
| C. Skip `simulation` and `submission_list` (small) | Less work | Loan is not done until its old path is gone; small folders are cheap |

**Recommended: A.**

## Step 7.9: Split the e-sign flow, remove globals from loan flows

**Today.** `esign_use_case.dart` 503 lines, 11 `appRef` and 25 `navigatorContext` reads. `open_agreement_detail_use_case.dart` 99 lines (3 / 1).

**Tasks.** `esign` becomes domain use cases plus one flow class that takes `BuildContext` and `WidgetRef` from the caller and checks `context.mounted` after each `await`. Same for `open_agreement_detail`. Behind `useNewLoanFlow`. The KYC flows in `auth` are Phase 9 (`useNewKycFlow`).

**Acceptance criteria.** No file under `loan/presentation/flows/` reads a global. Domain rules have tests. E-sign journey passes on both paths (QA, e2e if a spec exists, else a manual SIT script in the ledger).

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flow class with context and ref passed in, domain use cases underneath | Testable rules, no globals | Callers change signature (9 callers for submission entry per the plan) |
| B. Keep the flow, only swap `appRef` for a passed `ref` | Smaller | The 503-line flow stays a flow |
| C. Move e-sign into a separate feature package now | Clean boundary | Package work belongs to Phase 8 |

**Recommended: A.**

## Step 7.10: `LoanExits` exit port

**Today.** `loan` pushes routes of other features directly: payment, `ro`, `rl`, BPKB release, onboarding. `loan` imports `auth` 40 times, `select_vehicle` 30 times, `ro` 10, `payment` 9.

**Tasks.** `LoanExits` interface with one callback per exit. The app fills each with a `GoRouter` push. New-path screens use the port; old path unchanged.

**Acceptance criteria.** New-path `loan` files have 0 imports of other features' screens. Deep links into and out of loan work on SIT (both paths).

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Exit port per feature, app wires it | Standard "ports and adapters"; enables the package move in Phase 8 | One more interface per feature |
| B. A global navigation service | One API | A global again |
| C. Keep direct route pushes | No work | `loan` cannot become a package |

**Recommended: A.**

## Step 7.11: Cohort rollout of `useNewLoanFlow`

**Today.** Cohort dashboard (2.23) and runbook (2.24) exist. The network chain (Phase 4) is settled, so cohort data is clean.

**Tasks.** Rehearse the kill switch in SIT. 1% → 10% → 50% → 100%, one day of data per stage. Compare: crash-free sessions, error rate, p75 screen load, the loan submission funnel (start to submit), by flag value. Do not move the Play dial in the same week.

**Acceptance criteria.** Each stage noted in the ledger with its dashboard result. Funnel conversion on the new path within 2 points of the old (threshold from 1.4). No flip, or flip and fix recorded.

**Who / size.** Feature owner + on-call. 2–4 weeks.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Four stages with funnel and health checks | The plan's loop | 2–4 weeks |
| B. Roll out per sub-folder flag | Finer control | Mixed states (new detail, old submission) nobody tested |
| C. Internal cohort only, then 100% | Fast | Staff do not apply for loans like customers do |

**Recommended: A.**

## Step 7.12: Flip and delete the old loan path

**Today.** –

**Tasks.** After 2 releases at 100% with no regression: delete old controllers, use cases, mappers and old-only screens. Delete `useNewLoanFlow` from the catalogue and the old-path tests. Delete the Remote Config key one release later. Set every ledger row to "done".

**Acceptance criteria.** No reference to `useNewLoanFlow`. `dto-in-presentation` for `loan` is 0. `state-notifier` for `loan` is 0. `app-ref` in `loan` is 0. Lines in `loan` go down (record the number).

**Who / size.** One mobile engineer. M (large diff, mostly deletions).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete in one PR after the gate | Clean | A large deletion PR; reviewers check the ledger, not every line |
| B. Delete per sub-folder | Smaller PRs | The flag lingers; mixed state again |
| C. Keep the old path for "one more quarter" | None | The strangler never finishes; the flag's removal date fails CI anyway |

**Recommended: A.**

## Exit gate for Phase 7

* `useNewLoanFlow` at 100% for 2 releases with no regression on health or the loan funnel.
* Old loan path, old tests and the flag deleted. `dto-in-presentation`, `state-notifier` and `app-ref` for `loan` all 0.
* The ledger is complete and signed. The pattern (ledger → slice → both paths → cohort → flip → delete) is written up as the template for Phase 9.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who is the `loan` feature owner who signs the ledger and owns `useNewLoanFlow`? | Squad lead | |
| Q2 | Can two engineers be dedicated to 7.8 for 3 sprints? | Engineering manager | |
| Q3 | Is there an e-sign e2e spec, or do we need a manual SIT script for 7.9? | QA lead | |
| Q4 | Which loan behaviours changed in Phase 3 (approved deltas) that the ledger must list? | Product | |
| Q5 | Do we start Phase 8's design-system scope talk (8.1) during Phase 7, so 8.3 is ready when loan is done? | Design lead | |
| Q6 | Epic for Phase 7: one epic with 12 tickets, sub-tickets under 7.8? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Loan size by sub-folder | `git ls-files` + `wc -l` per `digital/lib/features/loan/*/`, generated files excluded |
| DTO imports | `grep -rl "package:customer/"` in features outside `data/`: 240 files, 94 in loan |
| Globals in flows | `grep -c appRef` and `navigatorContext` per flow file |
| `CommonController` reads | `grep -rn "CommonController.provider"`: 63 |
| Core purity | 21 files in `shared_lib/core/lib/src`, 2 import `package:flutter/` |
| Repository use | `grep` of each `*Repository` class name across `digital/lib/features` |

## Sources for the recommendations

* Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html) and Microsoft, [Strangler fig pattern](https://learn.microsoft.com/azure/architecture/patterns/strangler-fig): grow the new path beside the old, retire the old, and the discipline risk of running both forever.
* Riverpod, [Testing](https://riverpod.dev/docs/essentials/testing) and [overrides](https://riverpod.dev/docs/concepts2/overrides): one container per test, override at the repository level.
* Mobile plan 08: Layering (BFI layer contracts, worked example for agreement list and submission entry), Mobile plan 09 steps 3–5, Mobile plan 10 steps 3 and 5.
