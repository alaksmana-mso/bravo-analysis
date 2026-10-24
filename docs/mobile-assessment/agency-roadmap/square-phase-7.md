## Summary

Phase 7 of the SQUARE roadmap ("Pilot: lead and company submission through the parity loop"). Child of SQUARE roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] SQUARE Improvement - Pilot: lead and company submission".
* **Plan pages:** SQUARE plan 08: Layering steps 1–5, SQUARE plan 09: State management step 3, SQUARE plan 13 step 3, SQUARE plan 11 step 4.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 7 is.** The target architecture is proven on SQUARE's two largest features without changing what field staff see. SQUARE has one advantage GENFI lacks: `lib/features/lead/cancellation_review/` already has the target shape (`data/`, `domain/`, `presentation/`). The pilot copies that shape across `lead` and `company_submission` behind `useNewLeadFlow`, runs the same tests on both paths, rolls out to internal users, flips, and deletes the old path.

### Five facts that shape SQUARE Phase 7

**1. The two features are 29,929 lines.** `lead`: 82 files, 20,692 lines, sub-folders `cancellation_review` (target shape), `change_phone`, `domicile_area`, `leads_submission`, `leads_tracker`, `loan_calculator`, plus `lead_table.dart`, `lead_util.dart`, `loan_limit.dart`. `company_submission`: 37 files, 9,237 lines. SQUARE has 82 `StateNotifier` controllers in total.

**2. The rules sit in three files.** `company_submission_prospect_step.dart` (1,195 lines), `collateral_asset_info_controller.dart` (804), `no_deal_recalculation_controller.dart`. 19 `*_use_case.dart` files are mostly Riverpod providers wrapping a repository call; rules such as `isWorkLocationInCompanySubmissionPiloting` sit in those provider functions.

**3. API models reach the UI.** 41 screen files and 57 controller files import the `agency` package; 66 lines use `*Response` DTOs; screens read repositories directly (`loan_screen.dart:737`, `collateral_asset_info_screen.dart:52–53`).

**4. 89 cross-feature imports in 79 files;** `profile` is imported by 35 files, `maintain` by 12. `shared_data` already maps most DTOs to models (`agent_marketing` 77 mapper files, `onboarding` 46, `agency` 23), so the ports can wrap the existing repositories.

**5. Keycloak and managed devices.** SQUARE signs in through Keycloak; the new path must drive the same auth calls. Users are staff on managed devices, so rollout stages can be 20% → 100% and a forced update is possible.

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **C** = behind `useNewLeadFlow`, **B** = same behaviour, **A** = no app change.

| # | Proposed ticket title | Today (24 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1 | `chore: Layer rules, domain-purity (strict), dto-in-presentation (ratchet); pure core barrel` (shared with GENFI) | No rules | A | Agency engineer | S | Phase 1 step 1.10 | | |
| 7.2 | `docs(square): Ledgers for lead and company_submission; flag useNewLeadFlow` | 1.S3, 1.S4 done | A | QA + feature owner | M | Phase 2 step 2.7 | | |
| 7.3 | `feat(lead): Slice 1, lead detail and leads tracker list on the new path (cancellation_review shape)` | Old controllers | C | Agency engineer | M | 7.1, 7.2, Phase 6 | | |
| 7.4 | `feat(company_submission): Move the rules (prospect step, collateral, no-deal recalculation) into domain use cases; new notifiers beside the old` (3–5 PRs) | 3 rule files | C | 2 Agency engineers | L | 7.3 | | |
| 7.5 | Cohort rollout `useNewLeadFlow` 20% → 50% → 100% | – | C | Flag owner + on-call | 2–4 weeks | 7.3, 7.4, 2.16 | | |
| 7.6 | `refactor: Flip and delete the old controllers, use cases and the flag` | – | B | Agency engineer | M | 7.5 | | |

**Suggested order.** Sprint 1: 7.1 (if GENFI has not done it), 7.2. Sprint 2: 7.3. Sprints 3–5: 7.4. Then 7.5, then 7.6. About two months.

## Definition of ready for every ticket

* The ledger rows the ticket turns green are listed.
* Class C tickets name the goldens, fixtures and e2e specs that must pass with the flag off and on.
* The new path imports nothing from `shared_data` outside `data/`.
* No old-path file is edited, except to add a test.

## Step 7.1: Rules, checker rules, pure barrel

Same as GENFI Phase 7 step 7.1 and shared with it: one PR for the monorepo. SQUARE baseline for `dto-in-presentation` on merge day (41 screen + 57 controller files today).

**Acceptance criteria.** A Flutter import in a domain file fails CI. `pure.dart` compiles without Flutter. `cancellation_review/domain` passes `domain-purity` (it should already).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Once for both apps | One source of truth | Needs the two squads to agree the wording |
| B. SQUARE's own rules | Fast | Two rule sets in one repo |
| C. Review only | No code | 98 files with DTOs in the UI show how review did |

**Recommended: A.**

## Step 7.2: Ledgers and the flag

**Today.** Controller tests for `lead` and `company_submission` (1.S3) and the parity net (1.S4) exist. 19 `*_use_case.dart` providers hold rules that need characterisation.

**Tasks.** `docs/parity/square-lead.md` and `square-company-submission.md`: one row per behaviour (lead list and tracker, lead detail, submission steps, collateral info, no-deal recalculation, cancellation review) with old-path test, e2e spec and analytics events. Write missing old-path tests against today's output, including a table for the recalculation and collateral rules. `useNewLeadFlow` in the catalogue: owner, removal date, default old, read at journey start.

**Acceptance criteria.** Feature owner signs both ledgers; every row has an old-path test.

**Who / size.** QA + feature owner + one engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ledger first, tests against today's output | The move has an oracle | Feels slow |
| B. Ledger as slices land | Faster start | Rows match the new code |
| C. e2e only | Less paperwork | No per-rule trace |

**Recommended: A.**

## Step 7.3: Slice 1, lead detail and leads tracker list

**Today.** `cancellation_review` has the shape to copy; `leads_tracker` and the detail screens read `AreApplicationRepository` directly.

**Tasks.** `domain/` and `data/` at `lib/features/lead/` level: `Lead` entity, `LeadRepository` interface, mapper, `LeadRepositoryImpl` wrapping the `shared_data` repository. A new notifier (Riverpod 3 template) and screen path for lead detail and the tracker list; the old controller stays. `useNewLeadFlow` picks the path. Parity net on both paths.

**Acceptance criteria.** New-path files import no `shared_data` DTO. Mapper unit tests. Goldens of lead detail and tracker identical on both paths. Ledger rows green on both paths.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Lead detail and tracker first, copying `cancellation_review` | The shape exists in the same folder; smallest vertical slice | Two detail paths for a while |
| B. `company_submission` first (the rules) | Riskiest logic first | No shape to copy inside that feature yet |
| C. Map DTOs inside the old controller | Smallest diff | No new path to compare |

**Recommended: A.**

## Step 7.4: Move the rules in `company_submission`

**Today.** See fact 2.

**Tasks.** Pull the collateral, prospect-step and recalculation rules out of `company_submission_prospect_step.dart`, `collateral_asset_info_controller.dart` and `no_deal_recalculation_controller.dart` into domain use cases with plain unit tests. Old and new rules must give the same result for the same input (the 7.2 table). New notifiers beside the old controllers, behind the same flag (`company_submission` is entered from `lead`, so one flag covers the journey; confirm, question 2). `isWorkLocationInCompanySubmissionPiloting` and friends move out of the provider functions.

**Acceptance criteria.** Each moved rule has a test that needs no widget binding and passes on both paths. Company submission e2e passes flag off and on. `dto-in-presentation` for the feature drops with every PR.

**Who / size.** Two Agency engineers. L (3–5 PRs).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules first as pure functions, then the screens | The riskiest logic gets the cheapest tests | Screen work waits a sprint |
| B. Screens first | Visible progress | Rules stay in controllers; the cohort compares pixels, not logic |
| C. Both at once | One PR | Too big to review |

**Recommended: A.**

## Step 7.5: Cohort rollout

**Tasks.** `useNewLeadFlow` 20% → 50% → 100% (internal users), one day of data per stage. Watch crash-free sessions, error rate, p75 screen load and the lead and company-submission funnels. Keycloak refresh calls per session must not rise.

**Acceptance criteria.** Each stage noted in the ledgers; funnels within 2 points; no flip, or flip and fix recorded.

**Who / size.** Flag owner + on-call. 2–4 weeks.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Three stages | Enough for an internal app | 2–4 weeks |
| B. 1% → 10% → 50% → 100% | Finer | Too fine for SQUARE's user count |
| C. 100% at once with a forced update | Fastest | No cohort comparison |

**Recommended: A.**

## Step 7.6: Flip and delete

**Tasks.** After 2 SQUARE releases at 100%: delete the old controllers, the rule-holding provider functions, old-only screens, the flag and old-path tests. Remote Config key one release later.

**Acceptance criteria.** No reference to `useNewLeadFlow`. `dto-in-presentation` and `state-notifier` for `lead` and `company_submission` are 0. The three rule files are gone or under 500 lines.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One deletion PR after the gate | Clean | Large diff |
| B. Per sub-folder | Smaller PRs | Flag lingers |
| C. Keep the old path | None | The removal date fails CI anyway |

**Recommended: A.**

## Exit gate

* `useNewLeadFlow` at 100% for 2 releases with no regression, then deleted.
* Old paths deleted; `dto-in-presentation`, `state-notifier` and feature-boundary counts for `lead` and `company_submission` are 0.
* Ledgers complete and signed; the loop written up for SQUARE Phase 9.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who is the SQUARE feature owner who signs the ledgers and owns `useNewLeadFlow`? | Agency tech lead | |
| Q2 | Is company submission always entered from lead, so one flag covers both? | Agency squad | |
| Q3 | Can two engineers be dedicated to 7.4 for 3 sprints? | Engineering manager | |
| Q4 | Are the lead and company-submission e2e specs done (1.S5)? | QA lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Feature sizes | `git ls-files` + `wc -l` per `are_tracker/lib/features/{lead,company_submission}` |
| Target shape | `are_tracker/lib/features/lead/cancellation_review/{data,domain,presentation}` |
| Rules, DTOs, edges | SQUARE plan 08 "today" |
| Controllers | `grep -rl "extends StateNotifier<"` in `are_tracker/lib`: 82 |

## Sources for the recommendations

* SQUARE plan 08: Layering (layer contracts, sketch, order).
* BFI Phase 7 refinement notes (the loop).
* Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html).
