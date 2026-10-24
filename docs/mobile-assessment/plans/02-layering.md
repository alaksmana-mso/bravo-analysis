# Mobile plan 02: Layering

## Goal

Every feature has three layers: `data`, `domain` and `presentation`. Business rules live in a pure-Dart domain layer that is unit-tested on its own. Screens and notifiers never see API models (DTOs), so an API change stops at the data layer.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. Counts exclude generated files.

### The flow is written down, but it skips a domain

- `AGENTS.md` (copied to `CLAUDE.md`) sets the flow: Screen → Controller → UseCase (optional) → Repository → HttpClient.
- There is no `domain/` folder anywhere in the repo.
- Repositories live in `data/customer/lib/src/<area>/`. Each returns API models straight to the caller. Example: `LoanOnboardingRepository.getLoanApplicationStatusV2` returns `LoanTrackingStatusResponse`.
- API models follow protobuf names exactly (rule in `AGENTS.md`), for example `CustomerOTPInfo`. They are `freezed` + `json_serializable` classes.

### API models reach the UI

- 214 of 355 feature files import `package:customer/` (the API model package).
- 48 of 95 `*_screen.dart` files import it.
- 65 of 72 controllers (`StateNotifier`) import it.
- In `loan`: 83 of 130 files, including 44 screens, widgets, tabs and dialogs.

### Use cases are mixed with UI work

There are 38 `*use_case*.dart` files. `AGENTS.md` describes two kinds: "Type A" shared data (a `FutureProvider`) and "Type B" flows (functions that run a whole journey).

| Check on the 38 use-case files | Files |
|---|---|
| Is a `FutureProvider` or `StreamProvider` (Type A) | 23 |
| Imports `package:customer/` | 32 |
| Imports a `*_screen.dart` file | 16 |
| Imports Flutter (`package:flutter/...`) | 13 |
| Imports `router.dart` or `go_router` | 13 |
| Uses the global `appRef` | 14 |

Largest: `auth/kyc/kyc_use_case.dart` 970 lines, `loan/detail/esign/esign_use_case.dart` 503, `loan/submission/load_submission_draft_use_case.dart` 433, `auth/kyc/kyc_spouse_use_case.dart` 375, `auth/auth_flow_use_case.dart` 330.

`startKycFlowUseCase` in `kyc_use_case.dart` is a good example. It reads providers through `appRef`, pushes screens through the global `navigatorContext`, shows dialogs, and holds KYC rules, all in one function.

### Business rules sit in UI folders

- `loan/agreement/agreement_mapper.dart` decides which agreements show in the "active" and "paid-off" tabs. It works on the API model `GetListAgreementsData`.
- `loan/agreement/agreement_status_extension.dart` holds the overdue rules (warning at 7 days, "long overdue" after 30). It imports `package:flutter/material.dart` only to use `DateUtils`.
- `submission_controller.dart` (1,140 lines) mixes form state, calculation calls, remote-config checks and submission rules.

### A pure-Dart import is hard today

`shared_lib/core/lib/core.dart` re-exports `flutter_riverpod`, `go_router` and 10 other packages. Any file that imports `package:core/core.dart` pulls in Flutter.

## Target (what Jago does, adapted for BFI)

### What Jago does

- `.claude/rules/journey-clean-architecture.md`: `presentation → domain ← data`. Both arrows point at domain.
- `domain/` has `entities/`, `repositories/` (abstract) and `usecases/`. It must compile and test without Flutter.
- `data/` has DTOs, mappers, datasources and repository implementations.
- `presentation/` has state holders, screens and widgets. It never imports `data/`.
- The "ponytail rule": do not demand a use-case class for a plain pass-through. Flag logic in the wrong layer, not missing ceremony.
- New code is strict. Old misplaced logic is a ratchet: only growth is flagged.
- Example module: `module_digital_lending_journey/lib/` has `data/`, `domain/`, `presentation/` and `common/di/`.

### What NOT to copy from Jago

- Jago's own debt: 28 of its 1,112 `domain/` files still import Flutter. BFI's checker makes domain purity strict from the first file.
- Jago's `module_common`. Shared domain logic in BFI goes to a named package (`shared_lib/master_data`), not a catch-all.
- bloc. State holders in BFI are Riverpod `Notifier`s (Mobile plan 03).

### BFI layer contracts

| Layer | Holds | May import | Must not import |
|---|---|---|---|
| `domain/` | entities, repository interfaces, use cases, business rules | `dart:*`, `freezed_annotation`, `meta`, `collection`, `package:core/pure.dart`, `*_api` packages | Flutter, Riverpod, `package:core/core.dart`, `package:customer/`, `data/`, `presentation/` |
| `data/` | DTOs, mappers, repository implementations | `domain/`, `shared_lib/network`, `package:customer/` (during migration) | `presentation/` |
| `presentation/` | notifiers, screens, widgets, flows | `domain/`, `shared_lib/design_system`, Riverpod | `data/`, `package:customer/` |
| `di/` | provider declarations | all three layers | nothing else |

Domain has no Riverpod. Providers for domain types live in `di/` (Mobile plan 04).

### Where new code goes

| New code | Home |
|---|---|
| Business rule or validation | `domain/usecases/` or a method on the entity |
| API call | `data/` repository implementation, behind a `domain/repositories/` interface |
| DTO → entity mapping | `data/mappers/`, as a `toDomain()` extension on the DTO |
| Shared data across screens (today's Type A) | a provider in `presentation/` that calls a use case |
| Multi-screen journey (today's Type B) | a flow class in `presentation/flows/` plus domain use cases for its rules |
| Display format (dates, money text, colours) | `presentation/` |

### What a Type B use case becomes

`startKycFlowUseCase` splits in two:

- **Domain:** pure rules such as "can this user skip KYC", "is the cached KTP still valid", "should we call the vendor again". Each is a small use case with a unit test.
- **Presentation flow:** a `KycFlow` class. It gets a `BuildContext` (or the router) and a `Ref` from its caller. It pushes screens, shows dialogs and calls the domain use cases. No globals.

### Sketch: loan detail after the change

```dart
// features/loan/lib/src/domain/entities/loan_application_status.dart
@freezed
class LoanApplicationStatus with _$LoanApplicationStatus {
  const factory LoanApplicationStatus({
    required String groupId,
    required LoanStage stage,
    DateTime? surveyDate,
  }) = _LoanApplicationStatus;
}

// features/loan/lib/src/domain/repositories/loan_application_repository.dart
abstract interface class LoanApplicationRepository {
  Future<LoanApplicationStatus> statusByGroupId(String groupId);
}

// features/loan/lib/src/data/mappers/loan_tracking_mapper.dart
extension LoanTrackingStatusResponseX on LoanTrackingStatusResponse {
  LoanApplicationStatus toDomain() => LoanApplicationStatus(/* ... */);
}
```

## Plan

### Step 1: rules and checker (1 PR)

- Add `.claude/rules/layer-model.md` and `.claude/rules/feature-layers.md` (BFI versions, in our own words). Update the "Layered Architecture", "UseCases" and "Data Layer" sections of `AGENTS.md`. The `sync-ai-rules` workflow keeps `CLAUDE.md` in step.
- Add two rules to `tool/arch_check.dart` (Mobile plan 01: Repo layout):
- `domain-purity` is strict: any file under `domain/` that imports Flutter, Riverpod, `package:core/core.dart`, `package:customer/`, `data/` or `presentation/` fails. Today the count is 0.
- `dto-in-presentation` is a ratchet: feature files outside `data/` that import `package:customer/`. Baseline 214.
- Check: a branch that adds `import 'package:flutter/material.dart'` to a domain file fails.

### Step 2: a pure barrel in core (1 PR)

- Add `shared_lib/core/lib/pure.dart`. It exports only files with no Flutter import. Today that is the string, iterable and set extensions.
- Two small fixes widen it. `constants/product.dart` imports the full `core.dart` barrel; point it at what it needs. `extension/datetime_extension.dart` imports `package:flutter/material.dart`; replace that use with a pure helper.
- Then export `Product`, `ProductCategory` and the date extensions from `pure.dart` too.
- Check: a script confirms none of the files reachable from `pure.dart` import Flutter.

### Step 3: first vertical slice, loan detail (1–2 PRs)

- Add `domain/` and `data/` folders inside `digital/lib/features/loan/` (decouple in place; the package move comes later).
- Add `LoanApplicationStatus`, `LoanApplicationRepository`, the mapper and `LoanApplicationRepositoryImpl` (wraps `LoanOnboardingRepository`).
- Point `getLoanDetailUseCase` (18 references) at the new interface. Screens keep working.
- Check: `loan/detail/` screens and notifiers no longer import `package:customer/`. Mapper has unit tests.

### Step 4: agreement slice (2–3 PRs)

- `agreement/` is the biggest sub-folder (53 files).
- Move the tab rule from `agreement_mapper.dart` into `domain/usecases/split_agreements_by_tab.dart`, working on an `Agreement` entity.
- Move the overdue rules from `agreement_status_extension.dart` into domain. Replace `DateUtils.dateOnly` with a pure helper.
- Check: both rules have plain unit tests that need no widget binding.

### Step 5: submission, survey, simulation, submission list (4–6 PRs)

- One sub-folder per PR. Pull rules out of `submission_controller.dart` into use cases as you touch it.
- Notifier tests need the controller-test ban removed (Mobile plan 11: Testing).
- Check: `dto-in-presentation` for `loan` reaches 0.

### Step 6: split the Type B flows (2–4 PRs)

- `esign_use_case.dart` (503 lines) first, because it is inside `loan`. Then `kyc_use_case.dart` (970) and `kyc_spouse_use_case.dart` (375) in `auth`.
- Each becomes domain use cases plus one flow class. The `appRef` and `navigatorContext` uses go away in the same PR (Mobile plan 03).
- Check: no file under `presentation/flows/` reads a global. Domain rules have tests.

### Step 7: decide the future of `data/customer` (rides on each extraction)

- **Transport** (`http_client.dart`, `gcs_client.dart`, `device_service.dart`, `device_integrity/`) moves to `shared_lib/network` (Mobile plan 08: Networking).
- **Feature-owned repositories** move into the feature's `data/`. Today 13 repositories are used by one feature only. For `loan` that is 5: `LoanAgreementRepository`, `LoanCalculatorRepository`, `LoanOnboardingDocumentRepository`, `AdditionalDocumentsRepository`, `SurveyRepository`.
- **Shared reference data** moves to `shared_lib/master_data` with its own domain and data layers. Candidates: `StaticConfigRepository` (used by 10 features), `AddressRepository`, `BranchRepository`, `VehicleRepository`, `BankRepository`, `CustomerAttributionRepository` (LOV).
- **Repositories shared by two features** (`LoanOnboardingRepository` by `loan` and `ro`, `RlRepository` by `loan` and `rl`) stay with the owner. The other feature uses a `*_api` interface.
- Ratchet: no new repository file in `data/customer` (`customer-repo-growth`, baseline 26).

### Step 8: repeat for `auth`, `rl`, `ro`

- Same order: one slice per PR, rules first, then screens off DTOs.

## Done when

- `domain-purity` count is 0 and the rule is strict in CI.
- `dto-in-presentation` is 0 for `loan`, `auth`, `rl` and `ro`. The total is below 214 and never rises.
- Every `domain/` file in those four features runs its tests without a Flutter binding.
- `esign_use_case.dart`, `kyc_use_case.dart` and `kyc_spouse_use_case.dart` are gone. Their rules have domain tests.
- `data/customer` holds no feature-owned repository for those four features.
- `AGENTS.md` describes Screen → Notifier → UseCase → Repository interface ← Repository impl.

## Effort and owner

- Size: **L** (from the parent table).
- Rough time: 6–8 sprints for `loan` and the KYC flows, then 2–3 sprints per further feature. It runs in parallel with Mobile plan 01.
- Owner: Customer Mobile Apps squad.

## Depends on / related plans

- Mobile plan 01: Repo layout (package shape, checker, order of features).
- Mobile plan 03: State management (notifiers call use cases; flows lose globals).
- Mobile plan 04: Dependency injection (providers for interfaces live in `di/`).
- Mobile plan 08: Networking (`shared_lib/network` takes the transport).
- Mobile plan 11: Testing (unit tests for domain and notifiers).
- Mobile plan 12: Lint and guardrails (runs the rules in CI).

## Risks

| Risk | Mitigation |
|---|---|
| Mappers add boilerplate for no gain | Follow the ponytail rule: a thin entity is fine. Map only what screens use. |
| Moving a rule changes behaviour | Write the domain test against today's output first, then move the code. |
| Protobuf names leak into entities | Entities use plain business names. Only DTOs follow protobuf names. |
| Teams keep using DTOs in new screens | `dto-in-presentation` ratchet fails the PR. |
| `master_data` grows into a god package | It holds reference data only. Anything else needs a tech-lead review. |
