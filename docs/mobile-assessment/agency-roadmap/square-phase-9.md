## Summary

Phase 9 of the SQUARE roadmap ("Other features through the same loop"). Child of SQUARE roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] SQUARE Improvement - Remaining Features".
* **Plan pages:** SQUARE plan 08 step 6, SQUARE plan 09 steps 3–4, SQUARE plan 10 step 5, SQUARE plan 13 step 4, SQUARE plan 12 step 3.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 9 is.** The loop proven on `lead` and `company_submission` (Phase 7) and the extraction proven on `lead` (Phase 8), repeated for the rest of SQUARE in the plan's order: `maintain` (visit report), `recruitment`, `profile` (the most imported feature), then the rest. The `ds_1` → `ds_3` migration (Phase 8 step 8.6) rides on the same switch flags where screens are rebuilt. `collab_form` goes last, together with GENFI.

### The work, measured today

SQUARE has 21 feature folders, 82 `StateNotifier` controllers (those in `lead` and `company_submission` are done in Phase 7), 89 cross-feature imports in 79 files, and `ds_1` in 195 files.

| Feature group | Why this order | Notes |
| --- | --- | --- |
| `maintain` (visit report) | Imported by 12 files; a daily field journey with its own e2e (visit report submitted is a RUM action in Phase 3) | Flag: `useNewMaintainFlow` |
| `recruitment` | A money and identity path (candidate data) | Flag |
| `profile` | Imported by 35 files: the biggest edge cluster | `profile_api` first (read-only profile entity), then the loop; class B if no journey of its own |
| `kpi_incentive`, `agent_performance`, `performance`, `report`, `branch_activity` | Read-mostly dashboards | Class B conversions with screen tests and goldens |
| `auth`, `account`, `master_data`, `select_product`, `upload_image`, `notification`, `brochure`, `user_guide`, `home`, `main`, `splash` | Small or infrastructure | Flag only on `auth` (Keycloak sign-in) and `upload_image` (documents); class B elsewhere |
| `collab_form` (shared) | Last, with GENFI | Policies per app instead of `CollabFormAppId` branches |

## Steps at a glance

Class **C** = behind the feature's switch flag, then **B** for the extraction.

| # | Proposed ticket title | Today (24 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1 | `maintain` through the loop (ledger, flag, domain, notifiers, cohort, flip, delete), `ds_3` on the rebuilt screens, then extract | Old controllers, `ds_1` | C, then B | Feature owner + 1 engineer | 3 sprints | Phase 7, Phase 8 steps 8.4 and 8.6 | | |
| 9.2 | `recruitment` through the loop, then extract | – | C, then B | 1 engineer | 2–3 sprints | 9.1 past 50% | | |
| 9.3 | `profile_api`, then `profile` through the loop (class B if no own journey), then extract | Imported by 35 files | B or C | 1 engineer | 2 sprints | 9.2 | | |
| 9.4 | Dashboard and small features: class B conversions; flags on `auth` and `upload_image` | about 40 controllers | B or C by path | Agency engineers | 4 sprints | 9.3 | | |
| 9.5 | `refactor(core): Remove the legacy Riverpod export; shared_data without Riverpod` (shared with GENFI) | `legacy.dart` export | B | 1 engineer | S + 1 sprint | 9.4, GENFI 9.5 | | |
| 9.6 | `collab_form` split by screen with injected policies, with GENFI | 124 files | C, then B | Both squads | 3–4 sprints | GENFI Phase 9 | | |

**Suggested order.** As listed; one rollout at a time past 50%. About 3 quarters.

## Definition of ready for every ticket

* The feature's ledger is signed before the first slice.
* The switch flag is in the catalogue with owner and removal date, where a flag applies.
* The Phase 7 write-up is linked; the ticket says what differs.
* The extraction sub-ticket is "move only"; goldens unchanged except where `ds_3` replaced `ds_1` under the same flag and design signed the diff.

## Step 9.1: `maintain`

**Tasks.** Ledger from the visit-report journey (e2e from 1.S5); `useNewMaintainFlow`; domain for the visit-report rules; new notifiers; the rebuilt screens use `ds_3` (Phase 8 step 8.6) so the golden diff is signed by design once; cohort 20% → 50% → 100%; flip, delete, extract.

**Acceptance criteria.** Same checks as Phase 7 for `maintain`; `ds_1` imports in `maintain` reach 0; visit-report RUM action unchanged.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Loop with the design-system swap on the same flag | One rebuild, one cohort | Two kinds of change under one flag: the ledger must separate "same behaviour" rows from "approved visual delta" rows |
| B. Loop first, `ds_3` later | Cleaner separation | Screens rebuilt twice |
| C. `ds_3` only, no loop | Faster visual win | Rules stay in controllers |

**Recommended: A**, as SQUARE plan 12 step 3 says.

## Step 9.2: `recruitment`

**Tasks.** Same loop with `useNewRecruitmentFlow`; candidate data handling reviewed with the DPO (personal data); extract.

**Acceptance criteria.** Same checks; old path deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same loop | Consistent | – |
| B. Class B only | Faster | Candidate-data regressions reach every recruiter at once |
| C. Later | – | Blocks nothing, but the longest-lived legacy code |

**Recommended: A.**

## Step 9.3: `profile_api`, then `profile`

**Today.** `profile` is imported by 35 files.

**Tasks.** `profile_api` with a read-only profile entity and provider; switch the 35 importers to it (class B, small PRs); then `profile` itself through the loop, class B if it has no journey of its own (question 1); extract.

**Acceptance criteria.** 0 direct imports of `profile`; `profile` is a package.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `profile_api` first | Breaks the biggest edge cluster before moving code | One more small package |
| B. Move `profile` and let features depend on the package | Simple | 35 features pull all of `profile` |
| C. Merge `profile` into `core` | No api package | `core` becomes the everything package |

**Recommended: A.**

## Step 9.4: Dashboards and small features

**Tasks.** Class B conversion for read-mostly features with goldens and screen tests; flags on `auth` (Keycloak sign-in) and `upload_image`.

**Acceptance criteria.** `state-notifier` ratchet reaches 0; each notifier has a test.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flag only on sign-in and document paths | Proportionate | Judgement per feature; write the rule down |
| B. Flag everything | Uniform | Many flags for dashboards |
| C. Flag nothing | Fast | A sign-in regression blocks every field user |

**Recommended: A.**

## Step 9.5: Remove the legacy layer

Shared with GENFI Phase 9 step 9.5: delete the `legacy.dart` export, move provider declarations out of `shared_data`, stop re-exporting Riverpod from `core`. Done once both apps are at 0.

**Acceptance criteria.** Apps compile; `state-notifier` strict; `shared_data` plain Dart.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete when both apps are at 0 | Clean | Waits for the slower app |
| B. Per-app legacy export | SQUARE can finish first | Two `core` configurations |
| C. Keep | None | Legacy API stays |

**Recommended: A.**

## Step 9.6: `collab_form`

Same as GENFI Phase 9 step 9.6, done together: split by screen, policies per app, typed routes, one flag per app.

**Acceptance criteria.** 0 `CollabFormAppId` branches; both apps' e2e pass; old path deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Together, last | Both apps' rules explicit | Needs both squads |
| B. Fork per app | No coordination | Two copies |
| C. Leave | None | Shared monolith with app branches |

**Recommended: A.**

## Exit gate

* Every SQUARE feature's old path deleted; all switch flags removed; every ledger closed.
* `state-notifier`, `dto-in-presentation`, `feature-boundary` all 0 and strict; `ds_1` gone; `collab_form` split.
* `legacy.dart` export gone; `shared_data` plain Dart.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Does `profile` have a journey of its own that needs a flag, or is it read-mostly? | Agency squad | |
| Q2 | Which small features sit on sign-in or document paths? | Product + squad lead | |
| Q3 | Design capacity to sign the `ds_3` golden diffs per feature as they are rebuilt? | Design lead | |
| Q4 | One epic, or one per feature group? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Features and controllers | `ls are_tracker/lib/features`; `grep -rl "extends StateNotifier<"`: 82 |
| Edges | SQUARE plan 08 "today" (89 imports; `profile` 35, `maintain` 12) |
| `ds_1` | SQUARE plan 12 "today" (195 files) |

## Sources for the recommendations

* SQUARE phase 7 page (the loop), Agency phase 8 page (move-only extraction, `ds_1` → `ds_3`).
* SQUARE plan 08 step 6, plan 09 steps 3–4, plan 10 step 5, plan 12 step 3, plan 13 step 4.
