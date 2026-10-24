## Summary

Phase 9 of the GENFI roadmap ("Other features through the same loop"). Child of GENFI roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] GENFI Improvement - Remaining Features". One sub-epic per feature group is an option.
* **Plan pages:** GENFI plan 07 step 6, GENFI plan 08 steps 3–4, GENFI plan 09 step 5, GENFI plan 13 step 4.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 9 is.** The loop proven on `calculator` and `prospect` (Phase 7) and the extraction proven on `prospect` (Phase 8), repeated for the rest of GENFI. One feature's rollout at a time. `common` is split into `*_api` readers as its importers move, never moved as a block. `collab_form` goes last, together with SQUARE. By the end: no `StateNotifier`, no `shared_data` DTO in the UI, every feature a package.

### The work, measured today

| Feature group | Files | Lines | Controllers | Why this order |
| --- | --- | --- | --- | --- |
| `prospect_pbf` + `calculator_pbf` + `asset_selector_pbf` | 15 + 3 + 3 | 5,818 + 2,369 + 789 | 6 + 1 + 1 | Same rules as the convent calculator and prospect; the domain from Phase 7 serves them |
| `convent_registration` + `convent_take_selfie` + `convent_idcard_ocr` + `convent_camera*` | 9 + 1 + 2 + 3 | 4,548 + 97 + 157 + 592 | 3 + 0 + 1 + 1 | Registration journey (KTP OCR, selfie): sensitive, has e2e |
| `target_performance` | 12 | 2,636 | 2 | Imports `shared_data` in 9 files |
| `account_information` + `personal_information` + `tax_information` | 9 + 7 + 6 | 1,662 + 3,359 + 1,396 | 3 + 2 + 2 | `convent_registration ↔ account_information` import each other (5 edges) |
| `convent_lounge`, `convent_bonus`, `agency_news`, `products`, `chat`, `notification` | 11, 5, 11, 9, 11, 7 | 2,181, 1,704, 1,776, 1,887, 1,211, 1,122 | 1, 2, 5, 1, 1, 1 | Mid-size, few edges |
| `common` | 47 | 7,146 | 13 | Split into readers as importers move (23 from `prospect`, 14 from `calculator`, 6 from `prospect_pbf`) |
| Small: `maintain_activity`, `onboarding`, `registration`, `admin_agent`, `manage_admin`, `profile`, `consent_sign`, `home`, `auth`, `ocr`, `splash`, `media` | – | – | 1–3 each | Class B conversions with screen tests, flags only on sign-in and money paths |
| `collab_form` (shared) | 124 | 18,595 | – | Last, with SQUARE; policies per app instead of `CollabFormAppId` branches (26 references) |

Totals: GENFI 96 `StateNotifier` controllers (21 in `calculator` and `prospect`, done in Phase 7), 239 DTO-import files, 129 cross-feature imports.

## Steps at a glance

Class **C** = behind the feature's switch flag, then **B** for the extraction.

| # | Proposed ticket title | Today (24 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1 | PBF features through the loop on the Phase 7 domain, then extract | 21 files, 8 controllers | C, then B | Feature owner + 1 engineer | 2 sprints | Phase 7, Phase 8 step 8.3 | | |
| 9.2 | Registration journey (`convent_registration` and the capture features) through the loop, then extract | 15 files, 5 controllers | C, then B | Feature owner + 1–2 engineers | 3 sprints | 9.1 past 50% | | |
| 9.3 | `target_performance`, `account_information`, `personal_information`, `tax_information` through the loop; `account_api` to break the cycle | 34 files, 9 controllers | C, then B | 1 engineer | 3 sprints | 9.2 past 50% | | |
| 9.4 | Mid-size and small features: class B conversions with screen tests; flags only on `auth`, `onboarding`, `consent_sign` | about 50 controllers | B or C by path | Agency engineers | 4 sprints | 9.3 | | |
| 9.5 | `refactor(core): Remove the legacy Riverpod export; shared_data without Riverpod` | `legacy.dart` export | B | 1 engineer | S + 1 sprint | 9.4 | | |
| 9.6 | `collab_form` split by screen with injected policies, with SQUARE | 124 files | C, then B | Both squads | 3–4 sprints | SQUARE Phase 9 | | |

**Suggested order.** As listed; start a feature's rollout only when the previous one is past 50%. About 3–4 quarters at one feature group at a time.

## Definition of ready for every ticket

* The feature's ledger is signed before the first slice (same as 7.2).
* The feature's switch flag is in the catalogue with owner and removal date, where a flag applies.
* The Phase 7 write-up is linked and the ticket says what differs for this feature.
* The extraction sub-ticket is "move only" with goldens unchanged.

## Step 9.1: PBF features

**Today.** `prospect_pbf`, `calculator_pbf`, `asset_selector_pbf` repeat the convent flow for PBF products with their own controllers.

**Tasks.** Ledger; `useNewPbfFlow`; the PBF screens read the Phase 7 domain (`CalculationPort`, prospect use cases) with PBF product policies injected; new notifiers; cohort 10% → 50% → 100%; flip and delete; extract into the `prospect` and `calculator` packages or a `pbf` package (question 1).

**Acceptance criteria.** Same checks as Phase 7; the characterisation table gains PBF rows; the three features' old paths deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Reuse the Phase 7 domain with product policies | No second domain for the same rules | PBF differences must be real policies, not branches |
| B. Own PBF domain | Independent | Duplicated rules |
| C. Leave PBF on the old path | Less work | Two code paths for one calculation forever |

**Recommended: A.**

## Step 9.2: Registration journey

**Today.** `convent_registration` (9 files, 4,548 lines, 3 controllers) plus the capture features (selfie, ID-card OCR, camera). Sensitive (KTP, selfie). It imports `account_information` (5) and `tax_information` (3).

**Tasks.** Ledger from the register e2e; `useNewRegistrationFlow`; vendor SDK calls (ML Kit OCR, camera) recorded in the fixtures and compared call by call; domain for the registration rules; new notifiers; cohort with an extra day per stage; flip, delete, extract as `registration` with the capture features inside.

**Acceptance criteria.** Register e2e passes flag off and on; SDK calls identical in replay; old path deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One flag for the whole registration journey | One cohort for one journey | A larger slice |
| B. A flag per capture step | Finer | Mixed states inside one journey |
| C. Skip the flag (registration is one-time per agent) | Faster | A registration bug blocks every new agent |

**Recommended: A.**

## Step 9.3: Performance and information features

**Today.** `target_performance` imports `shared_data` in 9 files; `convent_registration ↔ account_information` is a two-way edge.

**Tasks.** `account_api` (read-only account entity) to break the cycle; ledgers; flags only where the journey touches money or identity (tax information: yes; target performance: class B with screen tests); domain, notifiers, cohort where flagged; extract.

**Acceptance criteria.** No two-way edges remain; counts 0 for the four features.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `account_api` first, then the loop per feature | Breaks the cycle before moving code | One more small package |
| B. Merge `account_information` and `personal_information` | Fewer packages | Two journeys in one |
| C. Loop without breaking the cycle | Faster | The packages cannot be extracted |

**Recommended: A.**

## Step 9.4: Mid-size and small features

**Today.** About 50 controllers across 18 features with 1–5 controllers each.

**Tasks.** Class B conversion (Notifier + screen tests, no flag) for features off the sign-in and money paths. Flags for `auth`, `onboarding`, `consent_sign`, `chat` (if it carries agent-customer messages). `common` readers extracted as each importer moves.

**Acceptance criteria.** `state-notifier` ratchet reaches 0; each notifier has a test; `common` has no importers left and is deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flag only on sign-in and money paths, class B elsewhere | Proportionate | A judgement per feature; write the rule down |
| B. Flag everything | Uniform | 18 flags for one-screen features |
| C. Flag nothing | Fast | An auth regression reaches every agent |

**Recommended: A.**

## Step 9.5: Remove the legacy layer

**Tasks.** Delete the `legacy.dart` export from `core`; move provider declarations out of `shared_data` (plan 13 step 4); stop re-exporting Riverpod from `core`.

**Acceptance criteria.** The apps compile; `state-notifier` strict; `shared_data/*` have no `flutter_riverpod` dependency.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete when ratchets hit 0 | Clean | Waits for the last feature |
| B. Delete early, fix stragglers | Forces the end | Risky mid-rollout |
| C. Keep | None | Legacy API stays available |

**Recommended: A.**

## Step 9.6: `collab_form`

**Today.** 124 files, 18,595 lines, branches on `CollabFormAppId` in 26 places, own routes with untyped `state.extra` casts, depends on `core` undeclared.

**Tasks.** With SQUARE: split by screen into `features/shared/collab_form`; inject per-app policies instead of the `CollabFormAppId` branches; typed route arguments; the loop with one flag per app.

**Acceptance criteria.** 0 `CollabFormAppId` branches; typed routes; both apps' e2e pass; old path deleted.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Last, split by screen, policies injected | Both apps' rules are explicit | Needs both squads |
| B. Fork per app | No coordination | Two copies of 18,595 lines |
| C. Leave | None | A shared monolith with app branches |

**Recommended: A.**

## Exit gate

* Every GENFI feature's old path deleted; all switch flags removed; every ledger closed.
* `state-notifier`, `dto-in-presentation`, `feature-boundary` all 0 and strict; `common` deleted; `collab_form` split.
* `legacy.dart` export gone; `shared_data` plain Dart.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Do the PBF features become a `pbf` package or join `prospect` and `calculator`? | Agency squad | |
| Q2 | Which small features sit on money or sign-in paths and get a flag? | Product + squad lead | |
| Q3 | Who owns `collab_form` across the two squads? | Both tech leads | |
| Q4 | One epic, or one per feature group? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Feature sizes and controllers | `git ls-files` + `wc -l` + `grep -rl "extends StateNotifier<"` per `agent_tools/lib/feature/*/` |
| Edges | import graph (129 total; two-way pairs listed) |
| `collab_form` | 124 files, 18,595 lines; `CollabFormAppId` 26 references |

## Sources for the recommendations

* GENFI phase 7 page (the loop), Agency phase 8 page (move-only extraction).
* GENFI plan 07 step 6, plan 08 steps 3–4, plan 09 step 5, plan 13 step 4.
