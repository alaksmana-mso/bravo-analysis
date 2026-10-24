## Summary

Phase 7 of the GENFI roadmap ("Pilot: calculator and prospect through the parity loop"). Child of GENFI roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] GENFI Improvement - Pilot: calculator and prospect".
* **Plan pages:** GENFI plan 07: Layering steps 1–5, GENFI plan 08: State management step 3, GENFI plan 13 step 3, GENFI plan 10 step 4.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 7 is.** The target architecture (domain layer, Notifiers, ports) is proven on GENFI's two largest features without changing what agents see. New code sits beside old code behind `useNewCalculatorFlow` and `useNewProspectFlow`. The same tests run on both paths. Then a cohort rollout, a flip, and the old path is deleted. It is the strangler pattern inside one app; the discipline is finishing, which is why the flags have removal dates and the exit gate is "old path deleted".

### Five facts that shape GENFI Phase 7

**1. The two features are 37,834 lines.** `prospect`: 89 files, 31,169 lines, 20 controllers, 14 sub-folders (`loan_info`, `collateral`, `input`, `detail`, `list`, `confirmation`, `reserve_lead`, `convent_*`, `pbf_*`). `calculator`: 8 files, 6,665 lines, 1 controller of 2,290 lines. Together 36% of GENFI.

**2. The rules live in three files.** `calculator_controller.dart` 2,290 lines, `loan_info_screen_controller.dart` 1,901, and the screens themselves: `loan_info_screen.dart` 2,429, `collateral_screen.dart` 2,160, `calculation_result_screen.dart` 2,038, `calculator_screen.dart` 1,862. Loan calculation (tenor, instalment, down payment, admin fee) is the densest logic in the app and a wrong answer is a wrong quote to a customer.

**3. No domain anywhere.** 0 `domain/` folders, 0 use-case files. 239 files outside `data/` import `shared_data` DTOs; `prospect` 64 of them. `prospect` and `calculator` read `AgentRepository` 55 times, `OnboardingAgentRepository` 19, `BranchRepository` 11, `VehicleRepository` 9, `CalculationRepository` 9 directly.

**4. The edges to cut.** `prospect → common` 23, `calculator → common` 14, `calculator → prospect` 8, `prospect → calculator` 5. `common` (47 files, 7,146 lines, 13 controllers) is GENFI's `module_common`: split it into `*_api` readers as importers move, never move it as a block.

**5. Fewer globals than BFI, but dates are a trap.** No `appRef`, no `navigatorContext`; `NavigationService.instance` 4 reads; `DateTime.now()` 78 uses. Domain rules about tenor and due dates need a clock port, or the characterisation tests will drift with the calendar.

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **C** = behind a switch flag, **B** = same behaviour, **A** = no app change.

| # | Proposed ticket title | Today (24 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.1 | `chore: Layer rules, domain-purity (strict) and dto-in-presentation (ratchet 239); pure core barrel` | No rules | A | Agency engineer | S | Phase 1 step 1.10 | | |
| 7.2 | `docs(genfi): Ledgers for calculator and prospect; characterisation table; flags useNewCalculatorFlow and useNewProspectFlow` | 1.G3, 1.G4 done | A | QA + feature owner | M | Phase 2 step 2.7 | | |
| 7.3 | `feat(calculator): Domain (Quote, Tenor, DownPayment, Installment), CalculationPort, rules as pure use cases, new notifier beside the old controller` | 2,290-line controller | C | Agency engineer | L | 7.1, 7.2, Phase 6 | | |
| 7.4 | `feat(prospect): Slices loan_info, collateral, input, detail, list, confirmation, reserve_lead, then convent and PBF variants` (one sub-ticket each) | 14 sub-folders | C | 2 Agency engineers | L (6–9 PRs) | 7.3 | | |
| 7.5 | Cohort rollout: `useNewCalculatorFlow` 10% → 50% → 100%; `useNewProspectFlow` when the calculator is past 50% | – | C | Flag owner + on-call | 4–6 weeks | 7.3, 7.4, 2.16 | | |
| 7.6 | `refactor: Flip and delete both old paths and flags` | – | B | Agency engineer | M | 7.5 | | |

**Suggested order.** Sprint 1: 7.1, 7.2. Sprints 2–3: 7.3. Sprints 4–7: 7.4 (two engineers, one sub-folder each). Then 7.5 over 4–6 weeks, then 7.6. About one quarter.

## Definition of ready for every ticket

* The ledger rows the ticket turns green are listed.
* Class C tickets name the goldens, fixtures, e2e specs and characterisation rows that must pass with the flag off and on.
* The new path imports nothing from `shared_data` outside `data/` (strict for new files).
* No old-path file is edited, except to add a test.

## Step 7.1: Rules, checker rules, pure barrel

**Today.** No written layer rules; `shared_lib/core/lib/src` has 15 files, 1 imports Flutter; 4 `shared_data` files import `flutter/material` (for `DateTimeRange`).

**Tasks.** `.claude/rules/layer-model.md` and `feature-layers.md` (shared with SQUARE). `domain-purity` strict and `dto-in-presentation` ratchet (baseline 239 for GENFI on merge day) in `tool/arch_check.dart`. `shared_lib/core/lib/pure.dart`; replace `DateTimeRange` with a pure range type in `shared_data`.

**Acceptance criteria.** A domain file that imports Flutter fails CI. `pure.dart` compiles without Flutter. `shared_data` has no `flutter/material` import.

**Who / size.** One Agency engineer. S. Shared with SQUARE Phase 7 step 7.1: do it once.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules + checker + pure barrel, once for both apps | One source of truth | Rules must stay short |
| B. `import_rules` plugin for the strict rule | IDE feedback | Needs Dart 3.10+ across the workspace |
| C. Review only | No code | 239 violations show how review did |

**Recommended: A**, B as a bonus later (Phase 10 step 10.5).

## Step 7.2: Ledgers, characterisation table, flags

**Today.** The parity net (1.G3) and the characterisation table (1.G4) exist from Phase 1; the `SwitchFlag` kind exists (2.7).

**Tasks.** `docs/parity/genfi-calculator.md` and `genfi-prospect.md`: one row per behaviour with its old-path test, e2e spec and analytics events. Where a row has no test, write one against today's output. The calculator table: one row per product and tenor the business uses, inputs → today's outputs, as the oracle for every rule move. Flags with owner, removal date, default old, read at journey start.

**Acceptance criteria.** Feature owner signs both ledgers; every row has an old-path test; the table covers every product and tenor in prod (product confirms, question 1).

**Who / size.** QA + feature owner + one engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ledger and table first, then code | The test exists before the move | Feels slow; it is what makes the move safe |
| B. Ledger as slices land | Faster start | Rows match the new code, not today's behaviour |
| C. e2e only | Less paperwork | No per-rule trace for the quote logic |

**Recommended: A.**

## Step 7.3: Slice 1, calculator

**Today.** See facts 2 and 3.

**Tasks.** `domain/` and `data/` inside `lib/feature/calculator/`: entities, `CalculationPort`, a mapper, an implementation wrapping `CalculationRepository`. Rules as pure use cases with the characterisation table as tests; a clock port for date rules. A new `Notifier` (Riverpod 3 template from Phase 6) and a new result screen path beside the old controller. `useNewCalculatorFlow` picks the path at journey start. Parity net on both paths: golden of the result screen, fixture replay, widget tests twice.

**Acceptance criteria.** New-path files import no `shared_data` DTO. Every table row gives the same answer on both paths. Ledger rows green on both paths. `calculator_controller.dart` is untouched.

**Who / size.** One Agency engineer. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Calculator first: small in files, densest rules, cheapest tests | Proves the whole shape on the riskiest logic with the best oracle | Two result screens exist for a while |
| B. Prospect first: biggest feature | Bigger win | 89 files before anything is proven |
| C. Map DTOs inside the old controller | Smallest diff | No new path, nothing to compare in a cohort |

**Recommended: A.**

## Step 7.4: Prospect slices

**Today.** 14 sub-folders; the rules in `loan_info_screen_controller.dart` (1,901) and `loan_info_screen.dart` (2,429); reads of `calculator` (5) and `common` (23).

**Tasks.** One sub-folder per sub-ticket: `loan_info`, `collateral`, `input`, `detail`, `list`, `confirmation`, `reserve_lead`, then `convent_detail`, `convent_list`, `convent_status_detail`, `convent_resend_link`, `pbf_detail`, `pbf_list`. Rules into domain use cases; reads of `calculator` through `calculator_api`, of `common` through small readers. New notifiers beside old controllers; `useNewProspectFlow` picks the path. Copy the SQUARE `cancellation_review` folder shape.

**Acceptance criteria.** No new-path file in `prospect` imports a `shared_data` DTO or another feature directly. The prospect input and reserve-lead e2e specs pass flag off and on. Each sub-folder's ledger rows green. `dto-in-presentation` for `prospect` drops with every PR.

**Who / size.** Two Agency engineers in parallel. L (6–9 PRs).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One sub-folder per sub-ticket, two engineers | Parallel, reviewable | Shared widgets between sub-folders need coordination |
| B. All of `prospect` in one ticket | Simple tracking | 89 files, one reviewer: no |
| C. Skip the convent and PBF variants | Less work | Prospect is not done until its old path is gone; the variants share the rules |

**Recommended: A.**

## Step 7.5: Cohort rollout

**Today.** Cohort dashboards and the runbook exist (2.16). GENFI's release health dashboard (1.G6).

**Tasks.** `useNewCalculatorFlow`: 10% → 50% → 100%, one day of data per stage, no Play dial moved in the same week. Watch: crash-free sessions, error rate, p75 screen load, and the calculator funnel (open → result → reserve lead). `useNewProspectFlow` starts when the calculator is past 50%; watch the prospect-input and reserve-lead funnels.

**Acceptance criteria.** Each stage noted in the ledgers. Funnel conversion on the new path within 2 points of the old. No flip, or flip and fix recorded.

**Who / size.** Flag owner + on-call. 4–6 weeks.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Three stages per flag, calculator first | Clean attribution | 4–6 weeks |
| B. One combined flag | Fewer dials | A calculator bug and a prospect bug look the same |
| C. Internal agents only, then 100% | Fast | Staff do not quote like agents do |

**Recommended: A.**

## Step 7.6: Flip and delete

**Tasks.** After 2 GENFI releases at 100% per flag: delete `calculator_controller.dart`, the old prospect controllers, old-only screens, both flags and the old-path tests. Delete the Remote Config keys one release later. Ledgers set to done.

**Acceptance criteria.** No reference to either flag. `dto-in-presentation` for `calculator` and `prospect` is 0. `state-notifier` for both is 0. The six largest files are gone or under 500 lines.

**Who / size.** One Agency engineer. M (large deletion).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete per flag after its gate | Clean | Two deletion PRs |
| B. Delete per sub-folder | Smaller PRs | Flags linger; mixed state |
| C. Keep the old path "one more quarter" | None | The strangler never finishes; the removal date fails CI anyway |

**Recommended: A.**

## Exit gate

* Both flags at 100% for 2 releases with no regression on health or the funnels, then deleted.
* Old paths deleted; `dto-in-presentation`, `state-notifier` and the feature-boundary counts for `calculator` and `prospect` are 0.
* Ledgers complete and signed. The loop is written up for GENFI Phase 9.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which products and tenors must the characterisation table cover? | Product (GENFI) | |
| Q2 | Who is the GENFI feature owner who signs the ledgers and owns the two flags? | Agency tech lead | |
| Q3 | Can two engineers be dedicated to 7.4 for 4 sprints? | Engineering manager | |
| Q4 | Are the calculator e2e and reserve-lead e2e specs done (1.G5)? | QA lead | |
| Q5 | Does the PBF calculator share the rules with the convent calculator, so one domain serves both? | Agency squad | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Feature sizes and controllers | `git ls-files` + `wc -l` per `agent_tools/lib/feature/*/`, generated files excluded |
| Biggest files | `wc -l` over `agent_tools/lib`, localisation files excluded |
| DTO imports | `grep -rl` of the `shared_data` package imports outside `data/`: 239, `prospect` 64 |
| Repository reads | `grep -o "[A-Z]\w+Repository"` in `prospect` and `calculator` |
| Edges | import graph: `prospect → common` 23, `calculator → common` 14, `calculator → prospect` 8, `prospect → calculator` 5 |
| Globals | `appRef` 0, `navigatorContext` 0, `NavigationService.instance` 4, `DateTime.now()` 78 |

## Sources for the recommendations

* GENFI plan 07: Layering (the BFI layer contracts adapted, the calculator sketch).
* BFI Phase 7 refinement notes (the loan loop this page copies).
* Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html).
