**Priority 8 of 13.** Phase 2. Starts the main refactor, with loan first.

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
- bloc. State holders in BFI are Riverpod `Notifier`s (Mobile plan 09).

### BFI layer contracts

| Layer | Holds | May import | Must not import |
|---|---|---|---|
| `domain/` | entities, repository interfaces, use cases, business rules | `dart:*`, `freezed_annotation`, `meta`, `collection`, `package:core/pure.dart`, `*_api` packages | Flutter, Riverpod, `package:core/core.dart`, `package:customer/`, `data/`, `presentation/` |
| `data/` | DTOs, mappers, repository implementations | `domain/`, `shared_lib/network`, `package:customer/` (during migration) | `presentation/` |
| `presentation/` | notifiers, screens, widgets, flows | `domain/`, `shared_lib/design_system`, Riverpod | `data/`, `package:customer/` |
| `di/` | provider declarations | all three layers | nothing else |

Domain has no Riverpod. Providers for domain types live in `di/` (Mobile plan 10).

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
- Add two rules to `tool/arch_check.dart` (Mobile plan 11: Repo layout):
- `domain-purity` is strict: any file under `domain/` that imports Flutter, Riverpod, `package:core/core.dart`, `package:customer/`, `data/` or `presentation/` fails. Today the count is 0.
- `dto-in-presentation` is a ratchet: feature files outside `data/` that import `package:customer/`. Baseline 214.
- Check: a branch that adds `import 'package:flutter/material.dart'` to a domain file fails.

### Step 2: a pure barrel in core (1 PR)

- Add `shared_lib/core/lib/pure.dart`. It exports only files with no Flutter import. Today that is the string, iterable and set extensions.
- Two small fixes widen it. `constants/product.dart` imports the full `core.dart` barrel; point it at what it needs. `extension/datetime_extension.dart` imports `package:flutter/material.dart`; replace that use with a pure helper.
- Then export `Product`, `ProductCategory` and the date extensions from `pure.dart` too.
- Check: a script confirms none of the files reachable from `pure.dart` import Flutter.

This plan is the main user of "Keeping features identical" on the parent page. Each feature goes through the same loop: fill the parity ledger from today's behaviour, build the new path beside the old one, put a switch flag in front, get the parity net green on both paths, run the cohort check, then flip and delete. For `loan` that is steps 3–9. **Extracting a feature is not done until its old path is deleted.**

### Step 3: loan parity ledger and switch flag, before any code moves (1–2 PRs)

- Copy the parity ledger template (Mobile plan 03: Testing, step 11) to `docs/parity/loan.md`.
- Fill it from today's behaviour: loan detail, agreement tabs and overdue rules, submission, survey, simulation, submission list, esign. One row per behaviour: old-path test, e2e spec (`loan-detail`, `loan-list`, `loan-simulation`, the 4 submission specs), analytics events from the golden names file (Mobile plan 02: Analytics wrapper).
- Where a row has no old-path test, write one now, against today's output. This is the "write the domain test against today's output first" rule from the risk table.
- List the approved deltas that touch `loan`, for example PII removed from `apply_loan` and income or amount bucketing. Each needs sign-off from product or the data protection officer.
- Add the switch flag `useNewLoanFlow` to the flag catalogue (Mobile plan 12: Feature flags): owner, removal date, default = old path.
- Check: the feature owner signs off the ledger. Every row has an old-path test.

### Step 4: first vertical slice, loan detail (1–2 PRs)

- Add `domain/` and `data/` folders inside `digital/lib/features/loan/` (decouple in place; the package move comes later).
- Add `LoanApplicationStatus`, `LoanApplicationRepository`, the mapper and `LoanApplicationRepositoryImpl` (wraps `LoanOnboardingRepository`).
- Add a new loan detail path that reads the new interface. The old `getLoanDetailUseCase` (18 references) stays as it is. `useNewLoanFlow` picks which one runs.
- The parity net runs on both paths: golden screenshot of loan detail, fixture replay, widget tests with the flag off and on.
- Check: new-path `loan/detail/` screens and notifiers do not import `package:customer/`. Mapper has unit tests. The ledger rows for loan detail have a green new-path test.

### Step 5: agreement slice (2–3 PRs)

- `agreement/` is the biggest sub-folder (53 files).
- Move the tab rule from `agreement_mapper.dart` into `domain/usecases/split_agreements_by_tab.dart`, working on an `Agreement` entity.
- Move the overdue rules from `agreement_status_extension.dart` into domain. Replace `DateUtils.dateOnly` with a pure helper.
- The old mapper and extension stay until step 9. Both old and new rules must give the same tabs and the same overdue labels for the same input.
- Check: both rules have plain unit tests that need no widget binding. The same test inputs give the same output on both paths.

### Step 6: submission, survey, simulation, submission list (4–6 PRs)

- One sub-folder per PR. Pull rules out of `submission_controller.dart` into use cases as you touch it. The new notifier lives beside the old controller; `useNewLoanFlow` picks which one the screen uses.
- Notifier tests need the controller-test ban removed (Mobile plan 03: Testing).
- The 4 submission e2e specs run with the flag forced off and forced on.
- Check: no new-path file in `loan` imports `package:customer/`. The `loan` count of `dto-in-presentation` reaches 0 only when the old path is deleted (step 9).

### Step 7: split the Type B flows (2–4 PRs)

- `esign_use_case.dart` (503 lines) first, because it is inside `loan`. Then `kyc_use_case.dart` (970) and `kyc_spouse_use_case.dart` (375) in `auth`.
- Each becomes domain use cases plus one flow class. The `appRef` and `navigatorContext` uses go away in the same PR (Mobile plan 09).
- `esign` is inside `loan` and uses `useNewLoanFlow`. The KYC flows are in `auth`; they get their own switch flag (`useNewKycFlow`) and their own ledger, and go through the same loop.
- Check: no file under `presentation/flows/` reads a global. Domain rules have tests.

### Step 8: cohort check for loan (2–4 weeks of rollout)

- Turn `useNewLoanFlow` on in stages: 1% → 10% → 50% → 100%. Do not change the Play staged rollout at the same time.
- At each stage, compare old-path and new-path users on the cohort dashboard (Mobile plan 04: CI/CD): crash-free sessions, error rate, screen load time, and the loan submission funnel.
- Move to the next stage only when every threshold is green. If one breaks, flip the flag back (kill-switch runbook), fix, and start that stage again.
- Check: each stage has a note in the ledger with its date and dashboard result.

### Step 9: flip and delete the old loan path (1–2 PRs)

- After 2 releases at 100% with no regression, delete the old loan code: the old controllers, use cases, mappers and the screens only the old path uses.
- Delete `useNewLoanFlow` from the catalogue and the old-path tests. Delete the Remote Config key one release later.
- Set every ledger row to "done".
- Check: no reference to `useNewLoanFlow` is left. `dto-in-presentation` for `loan` is 0. Only now is the `loan` extraction done.

### Step 10: decide the future of `data/customer` (rides on each extraction)

- **Transport** (`http_client.dart`, `gcs_client.dart`, `device_service.dart`, `device_integrity/`) moves to `shared_lib/network` (Mobile plan 07: Networking).
- **Feature-owned repositories** move into the feature's `data/`. Today 13 repositories are used by one feature only. For `loan` that is 5: `LoanAgreementRepository`, `LoanCalculatorRepository`, `LoanOnboardingDocumentRepository`, `AdditionalDocumentsRepository`, `SurveyRepository`.
- **Shared reference data** moves to `shared_lib/master_data` with its own domain and data layers. Candidates: `StaticConfigRepository` (used by 10 features), `AddressRepository`, `BranchRepository`, `VehicleRepository`, `BankRepository`, `CustomerAttributionRepository` (LOV).
- **Repositories shared by two features** (`LoanOnboardingRepository` by `loan` and `ro`, `RlRepository` by `loan` and `rl`) stay with the owner. The other feature uses a `*_api` interface.
- Ratchet: no new repository file in `data/customer` (`customer-repo-growth`, baseline 26).

### Step 11: repeat for `auth`, `rl`, `ro`

- Same order: one slice per PR, rules first, then screens off DTOs.
- Same loop for each feature: ledger first (step 3), new path beside the old one behind its own switch flag, parity net green on both paths, cohort check (step 8), flip and delete (step 9).
- Start a new feature's rollout only when the previous one is past 50%, so two cohort checks do not overlap on the same journey.

### Worked example: agreement list and submission entry

The team's page "BFI Mobile Use Cases" asks how the Jago architecture helps with two real cases: the shared agreement list (a Type A use case) and entering loan submission (a Type B flow). Short answer:

- **Jago helps with where code lives and who may call whom.** Rules go in a pure-Dart domain. Flows never touch the UI from inside a use case. Features do not import each other.
- **Jago does not solve caching, refresh or time.** That part is about state, and Riverpod's reactive graph already does it better than Jago's event bus. We keep Riverpod and add one refresh rule.

Facts below are from `bravo-customer-app` `master` (`190e1d20`).

| Problem on the team's page | BFI today | Does Jago help? | What we do |
|---|---|---|---|
| Agreement list mapping and the "due in 5 days or less" rule | Mapper in `loan/agreement/agreement_mapper.dart`. The due rule (`remainingDaysToNextInstallment`) uses `DateUtils` from `flutter/material`. `agreement_use_case.dart` also holds `addFundsUseCase`, which uses `navigatorContext` and `appRef`, so the file imports the router and UI code | Yes | Move the mapping, sort and due rule into `domain/` as pure Dart (step 5). They become plain unit tests with a fake clock |
| Type B flow does UI work (`LoadSubmissionDraftUseCase`) | 433 lines. `call()` takes a `BuildContext`, shows a dialog widget defined in the same file, and drives the global loading overlay through `CommonController` | Yes | Jago's rule: logic never takes a `BuildContext`, never builds widgets, never navigates. Split into a domain decision plus a presentation flow (step 7) |
| Other features reading the agreement list | `home` (use case, controller, home card), `bpkb_release` and the app shell import `loan/agreement` directly: 6 edges into `loan`. `home` reaches into 5 features | Partly | Jago's target is a thin `*_api` package plus exit callbacks. Jago has not built one yet, so we would be first. We add `agreement_api`: entities and read-only providers, nothing else |
| Entering submission from many places | 9 callers (promo, notification, calculator, draft card, deep link, product screen, loan detail ×2, submission status card) import `loan/submission/enter_submission.dart` | Yes | Jago's exit-port idea: callers get an `onStartSubmission` callback that the app shell wires. They stop importing `loan` |
| Refresh is scattered | 14 `invalidate` calls on the list (6) and the detail family (8), in more than 10 files. The push handler invalidates through `appRef` | The idea only | Jago sends named refresh events on its event bus. We keep Riverpod and give refresh one owner (below) |
| Cache never expires, "now" freezes, backend changes do not notify | The list and due providers stay alive, so the "now" they used stays until something invalidates them. A day passing changes nothing | No | Jago has the same gap (most of its code calls `DateTime.now()` directly). BFI already uses `clock.now()`, which is better. We add a refresh-on-resume and date-change rule (below) |

One note: `ensureSubmissionCanProceed`, named on the team's page, is not on `master`. It is probably on a branch. The target below keeps its job (the guard).

#### Type A target: the agreement list

- **Domain (pure Dart, inside `loan` for now):** an `Agreement` entity; an `AgreementRepository` interface; `MapAgreementList` (drop null status, paid-off parent and active-children rows, sort by `goliveDate`); `DueBills` (first 5 live entries, payable not zero, 5 days or less, earliest first). Both take a `Clock`. A pure `dateOnly` helper replaces `DateUtils`.
- **Data:** the repository implementation calls the same endpoint (`GET` for the standard list, `POST` with the NIK and agreement-number proof for registered users) and maps DTOs to entities.
- **Presentation:** the providers keep their names and their reactive graph: `getAgreementListUseCase`, `getDueBillAgreementsUseCase`, `getDefaultLoanScreenTabUseCase`, `getHomeMissionsUseCase`. They just call the domain use cases instead of holding the rules. The four controllers that listen to the list do not change.
- **Other features:** `home`, `bpkb_release` and the app shell import `agreement_api` (the entity plus the read-only providers). They no longer import `loan/agreement` internals. The checker (step 1) stops new edges.

#### The refresh rule

- One owner, `AgreementRefresh`, with named methods. It replaces the 14 scattered `invalidate` calls.

| Method | Replaces today's |
|---|---|
| `afterSubmission()` | `invalidateLoan()` in the submission controller |
| `afterPayment(agreementNumber)` | the push handler (payment notification to amortization). It runs through a provider, not `appRef` |
| `afterRegisteredLink()` | the registered-agreement connection |
| `retry()` | the retry handlers in the agreement tabs, bill list, home card and BPKB release |

- Each method decides what to invalidate: the list, one detail, or both. Callers only say what happened. This is the Riverpod version of Jago's named refresh events.
- Two new triggers fix the frozen "now". First: when the app comes back to the foreground after a set time, call `retry()` (the time is to agree with product). Second: when the calendar date changes, invalidate the due providers so the bill badge, reminder and home mission recompute.
- This is still not real-time from the backend. If the team later needs that, a `StreamProvider` fed by push or polling can sit under the same owner.

#### Type B target: entering submission

```dart
// domain (pure Dart): decide, do not show anything
sealed class SubmissionEntry {}
class Blocked extends SubmissionEntry { Blocked(this.reason); final BlockReason reason; }
class ChooseDraft extends SubmissionEntry { ChooseDraft(this.draft); final SubmissionDraft draft; }
class Proceed extends SubmissionEntry { Proceed(this.start); final SubmissionStart start; }

abstract interface class StartSubmission {
  Future<SubmissionEntry> call(Product product, {SubmissionDraft? draft});
}
```

- **Domain:** `StartSubmission` runs the guard checks and the draft lookup and returns a decision: blocked (with a reason), choose a draft, or proceed. It has no `BuildContext`, dialog or navigation, and gets plain unit tests.
- **Presentation:** a `SubmissionEntryFlow` in `loan/presentation/flows/`. It shows the loading overlay, the blocking or error UI, and the draft-choice dialog. It starts journey tracking only after "proceed", then navigates. It gets its `BuildContext` and `Ref` from the caller; no globals.
- **Callers:** the 9 entry points stop importing `loan/submission`. Each gets an `onStartSubmission(product, draft, journey)` callback, wired once by the app shell. This is Jago's exit-port idea in Riverpod form.
- Tracking still finishes on submission success or when the route returns, as today.

#### Parity for this example

- Agreement list: the new domain rules must give the same rows, order, due list, badge, reminder and home mission as today for the same recorded API fixtures and the same fake date. These are rows in `docs/parity/loan.md`.
- Submission entry: the 9 entry points must give the same guard result, dialog, tracking events and screen, on both paths. The 4 submission e2e specs run with `useNewLoanFlow` off and on.
- Screens keep the same text and `Semantics` identifiers, so the e2e selectors still work (Mobile plan 03: Testing, step 10).

### Parity check

- Every step from 4 to 7 changes code that users run: loan detail, agreement tabs, overdue labels, submission, esign, KYC. Each could change behaviour.
- The parity ledger (step 3) lists today's behaviour first. Each row has an old-path test, a new-path test, an e2e spec and its analytics events.
- The parity net runs on both paths: golden screenshots, fixture replay, widget tests with the flag off and on, the 4 journeys in `automation-monorepo` with the flag forced off and on, and the golden names file.
- New-path screens keep the same visible text, `Semantics` identifiers and `Key`s, so e2e specs and widget tests work unchanged (Mobile plan 03: Testing, step 10).
- Approved deltas for `loan`: PII removed from `apply_loan`, income and amount bucketing. They are listed in the ledger and skipped by the parity check.
- The cohort check (step 8) proves it in prod. Flip and delete (step 9) ends it. A feature is not extracted while its old path or switch flag still exists.

## Done when

- `domain-purity` count is 0 and the rule is strict in CI.
- `dto-in-presentation` is 0 for `loan`, `auth`, `rl` and `ro`. The total is below 214 and never rises.
- Every `domain/` file in those four features runs its tests without a Flutter binding.
- `esign_use_case.dart`, `kyc_use_case.dart` and `kyc_spouse_use_case.dart` are gone. Their rules have domain tests.
- `data/customer` holds no feature-owned repository for those four features.
- `AGENTS.md` describes Screen → Notifier → UseCase → Repository interface ← Repository impl.
- `loan`, `auth`, `rl` and `ro` each have a parity ledger signed off by the feature owner, with every row "done".
- Each switch flag used for these features passed the cohort check at every stage, and its old path and flag are deleted. Extraction of a feature is not done before that.

## Effort and owner

- Size: **L** (from the parent table).
- Rough time: 6–8 sprints for `loan` and the KYC flows, then 2–3 sprints per further feature. Add 2–4 weeks of staged rollout per feature, plus 2 releases at 100% before the old path is deleted. It runs in parallel with Mobile plan 11.
- Owner: Customer Mobile Apps squad.

## Depends on / related plans

- Mobile plan 11: Repo layout (package shape, checker, order of features).
- Mobile plan 09: State management (notifiers call use cases; flows lose globals).
- Mobile plan 10: Dependency injection (providers for interfaces live in `di/`).
- Mobile plan 07: Networking (`shared_lib/network` takes the transport).
- Mobile plan 03: Testing (unit tests for domain and notifiers).
- Mobile plan 06: Lint and guardrails (runs the rules in CI).

## Risks

| Risk | Mitigation |
|---|---|
| Mappers add boilerplate for no gain | Follow the ponytail rule: a thin entity is fine. Map only what screens use. |
| Moving a rule changes behaviour | Write the domain test against today's output first, then move the code. |
| Protobuf names leak into entities | Entities use plain business names. Only DTOs follow protobuf names. |
| Teams keep using DTOs in new screens | `dto-in-presentation` ratchet fails the PR. |
| `master_data` grows into a god package | It holds reference data only. Anything else needs a tech-lead review. |
