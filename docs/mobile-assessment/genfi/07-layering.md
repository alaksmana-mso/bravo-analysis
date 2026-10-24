Priority 7 of 13. Phase 2. No domain layer anywhere in GENFI. Controllers call `shared_data` repositories directly and API models reach the screens. Starts the main refactor, with `prospect` and `calculator` first.

## Goal

Every feature has three layers: data, domain and presentation. Business rules live in a pure-Dart domain layer that is unit-tested on its own. Screens and notifiers never see API models, so an API change stops at the data layer. `shared_data` repositories sit behind ports owned by the domain.

## Where we are today

Revision read: `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026). Counts exclude generated files and the localisation files. GENFI is `agent_tools/`; its features live in `lib/feature/` (singular).

* **No feature has the target shape.** 0 `domain/` folders and 0 `*_use_case.dart` files in `agent_tools/lib`. SQUARE has one feature in the right shape (`lead/cancellation_review` with `data/`, `domain/`, `presentation/`); GENFI has nothing to copy from inside its own app, so it copies that SQUARE folder.
* **Size.** 484 hand-written Dart files, 103,578 lines, 34 feature folders, 96 `StateNotifier` controllers. `prospect` is 89 files, 31,169 lines and 20 controllers, about 30% of the app. Then `common` 47 files / 7,146 lines / 13 controllers (a grab-bag that 23 `prospect` files and 14 `calculator` files import), `calculator` 8 / 6,665 / 1, `prospect_pbf` 15 / 5,818 / 6, `convent_registration` 9 / 4,548 / 3.
* **The six largest files are all in `prospect` and `calculator`:** `prospect/loan_info/loan_info_screen.dart` 2,429 lines, `calculator/calculator_controller.dart` 2,290, `prospect/collateral/collateral_screen.dart` 2,160, `calculator/result/calculation_result_screen.dart` 2,038, `prospect/loan_info/loan_info_screen_controller.dart` 1,901, `calculator/calculator_screen.dart` 1,862. Loan-calculation rules (tenor, instalment, down payment, admin fee) sit inside `calculator_controller.dart` and the two prospect controllers.
* **API models reach the UI.** 239 files outside a `data/` folder import a `shared_data` package (`agency`, `agent_marketing`, `onboarding`, `master`, `user_iam`, `document`). By feature: `prospect` 64, `common` 33, `prospect_pbf` 14, `target_performance` 9, `products` 7, `convent_registration` 7, `convent_lounge` 7, `account_information` 7, `registration` 5, `personal_information` 5.
* **Repositories are read straight from screens and controllers.** In `prospect` and `calculator` alone: `AgentRepository` 55 references, `OnboardingAgentRepository` 19, `BranchRepository` 11, `VehicleRepository` 9, `CalculationRepository` 9, `LeadRepository` 7, `ApplicationsRepository` 6, `ProductRepository` 5.
* **129 cross-feature imports** (the same number the Lint plan counts). Top edges: `prospect → common` 23, `calculator → common` 14, `calculator → prospect` 8, `prospect_pbf → common` 6, `prospect → calculator` 5, `convent_registration → account_information` 5.
* **Globals are fewer than in BFI.** No `appRef` and no `navigatorContext`. `NavigationService.instance` is read 4 times. `DateTime.now()` appears 78 times, which matters for date rules in the domain (use a clock port).
* `shared_data` already maps most network DTOs to models (`agent_marketing` 77 mapper files, `onboarding` 46, `agency` 23). The models are `freezed` with defaults. The ports can wrap the existing repositories.
* `shared_data/agency` imports `flutter/material` in 3 repositories (for `DateTimeRange`) and one model; about 30 models import `flutter/foundation`. `core` (`shared_lib/core/lib/src`, 15 files) re-exports `flutter_riverpod`; only 1 file imports Flutter, so a pure barrel is cheap.
* `collab_form` (18,595 lines) is shared by GENFI and SQUARE, branches on `CollabFormAppId` in 13 places, and holds its own `StateNotifier`s and routes.

## Target (what Jago does, adapted for GENFI)

| Jago pattern | Our adaptation |
| --- | --- |
| presentation → domain ← data; domain is pure Dart with `entities/`, `repositories/` (abstract) and `usecases/` | Same three folders inside each feature, in place first (`feature/<name>/domain`, `data`, `presentation`), then as a package (GENFI plan 09: Repo layout). |
| Features talk through thin `*_api` packages | `prospect_api`, `calculator_api`, `common` split into small `*_api` readers: entities and read-only providers only. The checker stops direct imports. |
| The "ponytail rule": no use-case class for a plain pass-through | Same. Flag logic in the wrong layer, not missing ceremony. |
| Old misplaced logic is a ratchet | `dto-in-presentation` and `feature-boundary` baselines only go down (GENFI plan 06: Lint and guardrails). |

| Layer | Holds | May import | Must not import |
| --- | --- | --- | --- |
| `domain/` | entities, repository interfaces, use cases, rules | `dart:*`, `freezed_annotation`, `collection`, `package:core/pure.dart`, `*_api` packages | Flutter, Riverpod, `package:core/core.dart`, `shared_data`, `data/`, `presentation/` |
| `data/` | mappers, repository implementations (wrapping `shared_data`) | `domain/`, `shared_data`, `shared_lib/core` | `presentation/` |
| `presentation/` | notifiers, screens, widgets, flows | `domain/`, design system, Riverpod | `data/`, `shared_data` DTOs |
| `di/` | provider declarations | all three layers | nothing else |

Sketch, calculator:

```dart
// domain/repositories/calculation_repository.dart
abstract interface class CalculationPort {
  Future<Quote> quote(QuoteRequest request);
}
// domain/usecases/compute_installment.dart (pure, tested with no binding)
Installment computeInstallment(Quote quote, Tenor tenor, DownPayment dp) { ... }
// data/calculation_port_impl.dart (wraps shared_data; maps DTO -> entity)
final class CalculationPortImpl implements CalculationPort {
  CalculationPortImpl(this._remote);
  final CalculationRepository _remote; // from shared_data
  @override Future<Quote> quote(QuoteRequest r) async => (await _remote.calculate(r.toDto())).toDomain();
}
```

Do not copy: Jago's 28 domain files that still import Flutter (our domain-purity rule is strict from day one), `module_common` as a catch-all (GENFI's `common` folder is already that, and it is split, not moved), and bloc.

## Plan

### Step 1: rules, checker and a pure core barrel (1–2 PRs, shared with SQUARE)

* Add `.claude/rules/layer-model.md` and `feature-layers.md`. Add `domain-purity` (strict) and `dto-in-presentation` (ratchet, baseline 239 for GENFI on merge day) to `tool/arch_check.dart` (GENFI plan 06).
* Add `shared_lib/core/lib/pure.dart` that exports only Flutter-free files. Fix the 4 `shared_data` files that import `flutter/material` (`DateTimeRange` → a pure range type).
* How to check: a branch adding a Flutter import to a domain file fails CI. `pure.dart` compiles without Flutter.

### Step 2: parity ledger and switch flag for `prospect` and `calculator` (1–2 PRs)

* `docs/parity/genfi-prospect.md` and `genfi-calculator.md`: one row per behaviour, with its old-path test, e2e spec and analytics events (GENFI plan 04: Testing, step 4). Write missing old-path tests now, against today's output. The calculator rules get **characterisation tests first**: feed today's `calculator_controller.dart` a table of inputs and record the outputs as the expected values.
* Add the switch flags `useNewProspectFlow` and `useNewCalculatorFlow` to the flag catalogue (GENFI plan 10): owner, removal date, default = old path.
* How to check: the feature owner signs off both ledgers; every row has an old-path test; the calculator table has at least one row per product and tenor the business uses.

### Step 3: first vertical slice, calculator (2–3 PRs)

* `calculator` is small in files (8) but holds the densest rules (6,665 lines, one 2,290-line controller). Add `domain/` and `data/` inside `lib/feature/calculator/`. Entities `Quote`, `Tenor`, `DownPayment`, `Installment`; `CalculationPort`; a mapper; an implementation wrapping `CalculationRepository`.
* Move the calculation rules into pure use cases with the characterisation table as their tests. A new notifier and screen path read the port; the old controller stays. `useNewCalculatorFlow` picks which runs. Parity net on both paths (golden of the result screen, fixture replay).
* How to check: new-path files do not import `shared_data` DTOs. Every rule in the table gives the same answer on both paths. Ledger rows for the calculator are green on both paths.

### Step 4: `prospect` slices (6–9 PRs)

* One sub-folder per PR: `loan_info`, `collateral`, `input`, `detail`, `list`, `confirmation`, `reserve_lead`, then the convent and PBF variants. Pull the rules out of `loan_info_screen_controller.dart` (1,901 lines) and `loan_info_screen.dart` (2,429) into domain use cases. Copy the SQUARE `cancellation_review` folder shape.
* `prospect` reads `calculator` 5 times and `common` 23 times: route those reads through `calculator_api` and small `common` readers, so the new path has 0 cross-feature imports.
* Old and new rules must give the same result for the same input: test both with the same fixtures.
* How to check: each moved rule has a test that needs no widget binding and passes on both paths. `dto-in-presentation` for `prospect` drops with every PR.

### Step 5: cohort check, flip, delete (2–4 weeks rollout + 1–2 PRs per flag)

* `useNewCalculatorFlow` first, then `useNewProspectFlow`: 1% → 10% → 50% → 100% watching crash-free sessions, error rate and the prospect-input and reserve-lead funnels. After two releases at 100%, delete the old controllers, screens and the flag.
* Start `prospect`'s rollout only when the calculator is past 50%.
* How to check: no reference to either flag remains; `dto-in-presentation` for `calculator` and `prospect` is 0.

### Step 6: repeat per feature, then `collab_form`

* Order for GENFI: `prospect_pbf` and `calculator_pbf` (same rules, PBF products), `convent_registration`, `target_performance`, `account_information`, `personal_information`, then the rest. Split `common` into `*_api` readers as its importers move; do not move it as one block. `collab_form` last, together with SQUARE.
* Start a new feature's rollout only when the previous one is past 50%.
* How to check: every feature has a signed-off ledger with all rows done.

### Parity check

* The parity net from GENFI plan 04 step 4 (goldens, fixtures, fakes, ledger) runs on both paths for every slice.
* The calculator characterisation table is the oracle for every rule move. A different answer is a bug, not a delta, unless product signs it off.
* Analytics events stay the same on both paths (golden names file, GENFI plan 11).

## Done when

* `domain-purity` is 0 and strict in CI. `dto-in-presentation` is 0 for `calculator` and `prospect` and never rises elsewhere.
* Every `domain/` file runs its tests without a Flutter binding.
* The six largest files are gone or under 500 lines, with their rules in domain tests.
* `shared_data` has no Flutter UI imports; `core` has a pure barrel.
* Every migrated feature passed its cohort check and its old path is deleted.

## Effort and owner

* Size: L. 6–8 sprints for `calculator` and `prospect`, then 2–3 sprints per further feature, plus 2–4 weeks of staged rollout each. Runs in parallel with GENFI plan 09: Repo layout.
* Owner: GENFI squad; the `shared_data` changes with the Agency squad; step 1 once for GENFI and SQUARE.

## Depends on / related plans

* GENFI plan 09: Repo layout (package shape, order of features).
* GENFI plan 08: State management (notifiers call use cases).
* GENFI plan 13: Dependency injection (ports and providers live in `di/`).
* GENFI plan 05: Networking (repositories keep the same `HttpClient`).
* GENFI plan 04: Testing (parity net and domain tests).
* GENFI plan 06: Lint and guardrails (runs the rules).
* SQUARE plan 08: Layering (the `cancellation_review` shape to copy; step 1 is shared).

## Risks

| Risk | Mitigation |
| --- | --- |
| Mappers add boilerplate for no gain | Ponytail rule: a thin entity is fine; map only what screens use |
| Moving a calculation rule changes a quote | Characterisation table first, one row per product and tenor; a changed answer blocks the PR |
| `common` becomes a second `module_common` | Split it into `*_api` readers as importers move; never move it as one package |
| `collab_form` is shared by two apps with different rules | Inject policies per app instead of `CollabFormAppId` branches; migrate it last |
| Teams keep using DTOs in new screens | `dto-in-presentation` ratchet fails the PR |
| Two cohort checks overlap on one journey | One feature rollout at a time past 50% |
