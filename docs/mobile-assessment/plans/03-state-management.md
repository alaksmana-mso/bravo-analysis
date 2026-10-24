# Mobile plan 03: State management

## Goal

All screen state uses Riverpod 3 `Notifier` and `AsyncNotifier`. No code reaches providers or the navigator through a global. Notifiers hold screen state and call use cases. They never navigate, never touch `BuildContext`, and can be unit-tested on their own.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. Counts exclude generated files.

### Versions and the written rule

- `flutter_riverpod` 2.6.1 and `state_notifier` 0.15.2 (from `pubspec.lock`). Riverpod comes in through `shared_lib/core`, whose barrel re-exports `flutter_riverpod`.
- `AGENTS.md` tells authors to use `StateNotifierProvider` with `autoDispose` for every controller. New code follows the legacy API on purpose today.
- No `@riverpod` annotations, no `riverpod_generator`, no `riverpod_lint`.

### Controllers and providers

| Item | Count |
|---|---|
| Classes that extend `StateNotifier` | 72 (21 in `loan`, 8 `rl`, 6 `auth`, 5 `ro`, 3 in `app/`) |
| `StateNotifierProvider` declarations | 78: 7 plain, 41 `.autoDispose`, 30 `.autoDispose.family` |
| Controllers with a `freezed` UI state | 71 |
| Controllers that keep a `Ref` in a `_ref` field | 58 |
| `if (!mounted)` checks | 86 |
| `state =` assignments in controller files | 490 |
| `FutureProvider` / `StreamProvider` / `StateProvider` | 45 / 4 / 3 |
| `.valueOrNull` reads | 146 |
| `Notifier` or `AsyncNotifier` classes | 0 |

Controllers take their dependencies in the constructor and start loading there. Example: `SubmissionController` (`loan/submission/submission_controller.dart`) takes 9 constructor arguments, including `CommonController` and its own `Ref`, and calls `_onScreenLoaded()` from the constructor.

### The global `appRef`

`digital/lib/app/common/app_screen.dart` line 26 declares `late WidgetRef appRef;`. `AppScreen.initState` sets it. Any code can then read any provider without being given a `Ref`. The comment says "Must not be used for listen & watch".

There are **142** uses in **31** files. By place:

| Where | Uses |
|---|---|
| Use-case and flow functions (14 files; top: `kyc_use_case.dart` 20, `auth_flow_use_case.dart` 16, `capture_use_case.dart` 14, `esign_use_case.dart` 11) | 101 |
| App services (`ipv_service.dart` 11, `push_notification_util.dart` 7, `go_router_extension.dart` 3, others) | 24 |
| Widgets and screens (11 files, 4 of them in `app/ui`, `app/widget` and `app/dsl`) | 15 |
| Declaration and assignment | 2 |

By purpose:

| What `appRef` is used for | Uses | Replacement |
|---|---|---|
| Read a repository or device service (`AppPreferences` 9, `UserVerificationRepository` 6, `FileService` 6, `ipvServiceProvider` 3, 11 others) | 42 | Take the `Ref` from the caller, or inject the dependency |
| Show global loading or errors (`CommonController.provider.notifier`) | 23 | Loading in notifier state; `UiFeedback` port for flows (Mobile plan 04) |
| Invalidate or refresh cached data (`getLoanDetailUseCase`, `getAgreementDetailUseCase`, `getRoStatusUseCase`, …) | 19 | `ref.invalidate` from the caller's `Ref` |
| Read remote config or flags (`getRemoteConfigUseCase` 16, `isHomeRevampEnabledUseCase` 2) | 18 | Feature-flag port (Mobile plan 07) |
| Analytics (`Analytics` 8, `MixpanelService` 7, `TrackerJourneyManager` 2) | 17 | Analytics port (Mobile plan 05) |
| Await shared async data (`getUserAccessTypeUseCase` 5, `getAccountStatusUseCase` 3, `getRoSelectedAgreementUseCase` 3, …) | 15 | `ref.read(x.future)` from the caller's `Ref`, or `SessionReader` (Mobile plan 01) |
| Passed on as a `ref:` argument | 3 | Pass the real `Ref` |
| A `listenManual` subscription (`esign_use_case.dart`), against the file's own comment | 1 | Listen from the caller's `Ref` |
| A widget reading its own controller | 2 | Use the widget's own `ref` |
| Declaration and assignment | 2 | Delete |

### The global `navigatorContext`

`app/navigation/router.dart` line 95 defines `BuildContext get navigatorContext`. It has **151** uses in **25** files: 21 in features and 4 in `app/`. 13 of the 25 are use-case files and 2 are controllers. It lets non-UI code push screens and show dialogs. It is the same problem as `appRef`, for navigation.

## Target (what Jago does, adapted for BFI)

### What Jago does

- `.claude/rules/bloc-conventions.md`: a bloc holds orchestration and screen state. Business rules go to domain use cases. Blocs have no `BuildContext`, no widgets and no navigation. They emit states or effects, and the widget navigates.
- "Widgets don't decide": no business branching in `build()`, no use-case or repository calls from widgets.
- `.claude/rules/ports-and-contracts.md` has three tiers of navigation. Inside a feature, the feature owns its routes. Across features, a port. The app shell owns the full route graph.
- New and changed state holders get a test.

### BFI mapping (Riverpod, not bloc)

| Jago | BFI |
|---|---|
| bloc / cubit | `Notifier<UiState>` or `AsyncNotifier<T>` |
| state + effect | `freezed` UI state + today's `Event<T>` wrapper (`app/event.dart`) |
| widget navigates on effect | screen uses `ref.listen` on the event, then navigates |
| bloc test | `ProviderContainer` test with port overrides (Mobile plan 11) |

### Which Notifier type

| Today | Target |
|---|---|
| `StateNotifier<XUiState>` with several `AsyncValue` fields (most of the 72) | `Notifier<XUiState>`. Keep the `freezed` state as it is. |
| A screen that only loads one thing | `AsyncNotifier<T>` |
| `.family` (30) | `NotifierProvider.autoDispose.family`, with the argument passed to the class constructor (Riverpod 3 style) |
| Constructor dependencies | `ref.watch` in `build()` for things that should reset state; `ref.read` inside methods for services |
| `_ref` field (58) | the built-in `ref` |
| `if (!mounted)` (86) | `if (!ref.mounted)` (new in Riverpod 3) |
| Work started in the constructor | Started from `build()` |

### Sketch

```dart
class SubmissionNotifier extends Notifier<SubmissionUiState> {
  SubmissionNotifier(this.extra);
  final SubmissionScreenExtra extra;

  static final provider = NotifierProvider.autoDispose
      .family<SubmissionNotifier, SubmissionUiState, SubmissionScreenExtra>(
    SubmissionNotifier.new,
  );

  @override
  SubmissionUiState build() {
    Future.microtask(_load);
    return const SubmissionUiState();
  }

  Future<void> submit() async {
    state = state.copyWith(isSubmitting: true);
    final result = await ref.read(submitLoanProvider).call(state.form);
    if (!ref.mounted) return;
    state = state.copyWith(isSubmitting: false, doneEvent: Event(result.id));
  }
}
```

The screen listens to `doneEvent` and navigates. The notifier never does.

### Riverpod 3: upgrade first, then convert

Riverpod 3.0 came out in September 2025. Changes that matter here (confirm each against the official migration guide during the spike):

- `StateNotifier`, `StateNotifierProvider` and `StateProvider` move to `package:flutter_riverpod/legacy.dart`. They still work.
- The `AutoDispose*` and `Family*` notifier classes merge into one `Notifier`.
- `Ref.mounted` is added. Riverpod 2 `Notifier` has no `mounted`, which matters for BFI's 86 checks.
- Failed providers retry on their own by default.
- `valueOrNull` is gone; `value` takes its place.
- `ProviderObserver` methods change shape. This touches `DatadogLogObserver` (Mobile plan 06).

So: upgrade first, with the legacy import, then convert. Converting on 2.6 would mean writing `AutoDisposeFamilyNotifier` classes now and rewriting them after the upgrade.

### `riverpod_generator`: not now

- Hand-written `NotifierProvider` is one line and keeps the `static final provider` habit.
- The generator ties BFI to newer analyzer versions. That likely forces the `freezed` 2.5 → 3 upgrade at the same time.
- It adds up to 72 more generated files during a large migration.
- Revisit after the `freezed` 3 upgrade. It can then be allowed per package.
- `riverpod_lint` is useful either way. Add it through Mobile plan 12 if it fits the analyzer version.

### What NOT to copy from Jago

- bloc itself (decision already made).
- Jago's event-bus seam between journeys. BFI uses ports and exit callbacks (Mobile plan 04).

## Plan

### Step 1: stop the growth (1 PR)

- Update `AGENTS.md`: new controllers are `Notifier` or `AsyncNotifier`. No new `appRef`, no new `navigatorContext`, no `BuildContext` in notifiers.
- Add three ratchet rules to `tool/arch_check.dart` (Mobile plan 01): `state-notifier` (72), `app-ref` (142), `navigator-context` (151).
- Check: a branch that adds `appRef.read(` fails.

### Step 2: Riverpod 3 upgrade, no conversions (1–2 PRs)

- Bump `flutter_riverpod` in `shared_lib/core/pubspec.yaml`. Add `export 'package:flutter_riverpod/legacy.dart';` to `core.dart`, so all 72 controllers compile unchanged.
- Rename `valueOrNull` (146). Update `DatadogLogObserver`.
- Turn automatic retry off in `main.dart` and in test containers, to keep today's behaviour. Decide per provider later.
- Check: `melos test` passes. Manual smoke on SIT for login, KYC, loan apply, payment. Datadog shows no new provider errors after release.

### Step 3: remove `appRef` from app services and widgets (2 PRs)

- Services (24 uses): `ipv_service.dart`, `push_notification_util.dart`, `go_router_extension.dart`, `tracker_journey_manager.dart`, `deep_link_handler.dart`. Make each a provider that gets `Ref`. For navigation, read the `GoRouter` instance from a provider instead of `navigatorContext`.
- Widgets (15 uses): use the widget's own `ref`. The `Digital*` components get callbacks instead (Mobile plan 05 and Mobile plan 10).
- Check: `app-ref` count drops by 39.

### Step 4: remove `appRef` and `navigatorContext` from flows (4–6 PRs)

- Flow functions take `BuildContext` and `WidgetRef` (or `Ref`) from the calling widget. They check `context.mounted` after each `await`.
- Order: `esign_use_case.dart` and `open_agreement_detail_use_case.dart` (`loan`), then `ro_use_case.dart`, then the `auth` flows (`kyc_use_case.dart`, `auth_flow_use_case.dart`, `capture_use_case.dart`, `kyc_spouse_use_case.dart`).
- Do this together with the flow split in Mobile plan 02, step 6.
- Check: `app-ref` reaches 0. `navigator-context` is 0 outside `app/navigation/`.

### Step 5: convert `loan`'s 21 controllers (3–5 PRs)

- One sub-folder per PR: `detail/`, `agreement/`, `submission/`, `survey/`, `simulation/`, `submission_list/`.
- Rename `XController` to `XNotifier`. Keep the `freezed` state.
- Replace injected `CommonController` with an `isLoading` field and the screen's own overlay.
- Add a notifier test per class (needs Mobile plan 11 to lift the controller-test ban).
- Check: `state-notifier` for `loan` is 0. Each converted notifier has a test.

### Step 6: convert the rest, feature by feature

- `rl` (8), `auth` (6), `ro` (5), then the 29 smaller ones and the 3 in `app/`.
- `CommonController` itself goes last, after its 23 global reads are gone.

### Step 7: remove the legacy layer (1 PR)

- Delete the `legacy.dart` export and `late WidgetRef appRef`.
- Check: the app compiles without them.

## Done when

- 0 classes extend `StateNotifier`. `core.dart` does not export `legacy.dart`.
- 0 uses of `appRef`. The declaration in `app_screen.dart` is deleted.
- 0 uses of `navigatorContext` outside `app/navigation/`.
- 0 notifier files import `package:flutter/material.dart` or `router.dart`.
- Every notifier in `loan`, `auth`, `rl` and `ro` has a unit test.
- `AGENTS.md` shows `Notifier` as the standard.

## Effort and owner

- Size: **M** (from the parent table).
- Rough time: 1 sprint for steps 1–2, 2–3 sprints for steps 3–5. Step 6 rides along with feature work over the following quarter.
- Owner: Customer Mobile Apps squad.

## Depends on / related plans

- Mobile plan 01: Repo layout (the checker; features cannot move while they use `appRef`).
- Mobile plan 02: Layering (rules leave notifiers and flows for the domain).
- Mobile plan 04: Dependency injection (`UiFeedback` and other ports replace global reads).
- Mobile plan 05: Analytics wrapper (17 analytics reads through `appRef`).
- Mobile plan 06: Logging and crashes (`DatadogLogObserver` after the upgrade).
- Mobile plan 07: Feature flags (18 remote-config reads through `appRef`).
- Mobile plan 11: Testing (notifier tests, removing the ban).

## Risks

| Risk | Mitigation |
|---|---|
| Riverpod 3 changes behaviour quietly (retry, paused listeners, `==` filtering) | Retry off at first. Full test run. SIT smoke on the four main journeys before release. |
| Moving work from constructor to `build()` changes load timing | Convert with a test that checks the first state and the first API call. |
| Flows lose access to dialogs when the widget is gone | Check `context.mounted` after every `await`. Tests cover the back-button case. |
| Long tail of small features never gets converted | The ratchet only goes down. Report the counts every sprint. |
| `riverpod_lint` or Riverpod 3 conflicts with current analyzer pins | Upgrade in its own PR. Pin versions in one place. |
