**Priority 10 of 13.** Phase 2. Follows from layering and package boundaries.

## Goal

Riverpod stays the DI tool. Each feature package declares its own providers and keeps them private. When a feature needs something from outside, it reads a port: an interface whose provider throws until the app overrides it. All wiring happens in one place in the app, and a test proves every port is wired.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. Counts exclude generated files.

### Providers

- **128** `static final provider` declarations: 94 in `digital`, 31 in `data/customer`, 3 in `shared_lib/core`. This is the convention in `AGENTS.md` ("Provider Definition").
- Every provider is global. Any file can read any provider by importing its class. That is how `loan` reads `auth` internals today (Mobile plan 11: Repo layout).

### The port pattern already exists, 4 times

`digital/lib/main.dart` (`_runApp`, around line 215) builds the root `ProviderScope` with one observer (`DatadogLogObserver`) and 4 overrides:

| Provider | Declared in | Default body |
|---|---|---|
| `NetworkConfig.provider` | `shared_lib/core/lib/src/network/network_config.dart` | throws `UnimplementedError` |
| `DeviceIntegrityService.provider` | `data/customer/lib/src/device_integrity/device_integrity_service.dart` | throws `UnimplementedError` |
| `MixpanelService.provider` | `digital/lib/app/tracker/mixpanel_service.dart` | throws `UnimplementedError` |
| `MixpanelFeatureFlagService.provider` | `digital/lib/app/tracker/mixpanel_feature_flag_service.dart` | throws `UnimplementedError` |

Each error message says "... is not provided in the main function". This is exactly the port pattern this plan builds on. Nothing checks that every such provider is overridden; a missing one fails only at runtime.

### Tests already use overrides

- 42 test files use `overrideWith` or `overrideWithValue`.
- 7 test files build a `ProviderContainer` directly.

### Reach-ins that bypass DI

- The global `appRef` (142 uses) and `navigatorContext` (151 uses). See Mobile plan 09: State management.
- `ProviderScope.containerOf(context)` in 2 design-system components (`app/ui/components/digital_dialog.dart`, `digital_bottom_sheet.dart`) to grab `MixpanelService`.

### Barrels expose everything

- `data/customer/lib/customer.dart` has 115 `export` lines. Importing it gives a file every repository and every API model.
- `shared_lib/core/lib/core.dart` re-exports 12 third-party packages, including `flutter_riverpod` and `go_router`.

## Target (what Jago does, adapted for BFI)

### What Jago does

- Each module has a DI entry point. Example: `module_digital_lending_journey/lib/common/di/di.dart` is an injectable "micro-package" (`@InjectableInit.microPackage`). It lists the modules it needs first.
- The same file marks `PotsRepository` as "provided by app_jago_mobile". The module uses an interface; the app supplies the implementation.
- `app_jago_mobile/lib/common/di/di.dart` pulls in all micro-packages. Rule 5 in `.claude/rules/layer-model.md`: DI composition lives in the app layer only. Modules never register themselves into the app's injector. No single global registry.
- `.claude/rules/ports-and-contracts.md`: a feature gets what it needs as interfaces or callbacks. Exit ports are nullable callbacks: `null` means "this destination does not exist, hide the button".
- Leaf widgets take data and callbacks, not lookups.

### BFI mapping

| Jago | BFI with Riverpod |
|---|---|
| injectable micro-package per module | `lib/src/di/<feature>_providers.dart` per feature package |
| app `includeMicroPackages` | `digital/lib/app/di/app_overrides.dart` (one list of `Override`s) |
| type "provided by app" | port provider that throws, overridden by the app |
| `XxxDependencies` with callbacks | `<Feature>Exits` class with nullable callbacks, behind a port provider |
| constructor injection | `ref.watch` / `ref.read` inside providers and notifiers |

### Three kinds of provider

| Kind | Where | Visible outside the package? |
|---|---|---|
| Internal (notifiers, repository implementations, use cases) | `lib/src/` of the feature | No |
| Port (interface the feature needs from outside) | the `*_api` or `shared_lib` package that owns the interface | Yes, so the app can override it |
| Implementation the app wires into a port | `lib/src/di/` of the providing feature, exported from its barrel | Yes, for the app only |

Naming: port and repository providers are top-level (`kycLauncherProvider`), because `domain/` has no Riverpod (Mobile plan 08: Layering). Notifiers keep `static final provider`, as today. This matches `analyticsProvider` in Mobile plan 02: Analytics wrapper.

### Sketch

```dart
// features/auth_api/lib/src/kyc_launcher.dart  (no Flutter, no Riverpod)
abstract interface class KycLauncher {
  Future<KycOutcome> start(KycRequest request);
}

// features/auth_api/lib/src/providers.dart
final kycLauncherProvider = Provider<KycLauncher>(
  (ref) => throw UnimplementedError(
    'kycLauncherProvider: wire it in digital/lib/app/di/app_overrides.dart',
  ),
);

// features/loan/lib/src/loan_exits.dart
class LoanExits {
  const LoanExits({this.openPayment, this.openRepeatOrder});
  final void Function(String agreementId)? openPayment;     // null = hide
  final void Function(String agreementId)? openRepeatOrder; // null = hide
}

// digital/lib/app/di/app_overrides.dart
List<Override> appOverrides(AppBootstrap boot) => [
  NetworkConfig.provider.overrideWith((ref) => boot.networkConfig),
  kycLauncherProvider.overrideWith((ref) => ref.watch(authKycLauncherProvider)),
  loanExitsProvider.overrideWith((ref) => LoanExits(
        openPayment: (id) => ref.read(AppRouter.provider).router
            .pushNamed(PaymentRoutes.detail, extra: id),
      )),
];
```

`KycLauncher` has no `BuildContext`. The implementation in `auth` navigates with the `GoRouter` instance, whose `push` returns a `Future` with the result.

### Rules

- Override providers only in the root `ProviderScope` and in tests. No nested scopes with overrides. This avoids Riverpod's scoped-provider `dependencies` lists.
- A feature never imports another feature's providers. It reads a port.
- Leaf widgets never call `ProviderScope.containerOf`. They take a callback.
- Every port provider is listed in `allPorts` in `digital/lib/app/di/ports.dart`. A wiring test reads each one.
- Do not add `get_it`, `injectable` or `kiwi`.

### What NOT to copy from Jago

- Two DI systems at once (Jago runs old Kiwi and new injectable side by side).
- injectable code generation. Riverpod already does DI and BFI already knows it.
- `ignoreUnregisteredTypes`: it hides a missing registration until runtime. BFI's wiring test catches it in CI instead.
- Multi-bank slots in the dependencies object. Add a callback only when a real second destination exists.

## Plan

### Step 1: composition root and wiring test (1 PR)

- Create `digital/lib/app/di/app_overrides.dart` and `ports.dart`. Move the 4 overrides out of `main.dart` without changing them. `main.dart` calls `appOverrides(...)`.
- Change the 4 error messages to point at `app_overrides.dart`.
- Add `test/app/di/wiring_test.dart`: build a `ProviderContainer` with `appOverrides` (SDK objects faked) and read every provider in `allPorts`. None may throw.
- Add a checker rule (Mobile plan 06): every provider whose body throws `UnimplementedError` must appear in `allPorts`.
- Check: the app runs the same on SIT. The wiring test fails if one override is removed.

### Step 2: write the rules (1 PR)

- Add `.claude/rules/ports-and-di.md` and update "Dependency Injection" and "Provider Definition" in `AGENTS.md`.
- Add a ratchet rule `container-lookup` to `tool/arch_check.dart`: `ProviderScope.containerOf` outside `digital/lib/app/` (baseline 2).
- Make sure Dart's `implementation_imports` lint is on, so no package imports another package's `src/`.

### Step 3: `UiFeedback` port (1–2 PRs, with Mobile plan 09)

- Interface: `showLoading(bool)`, `showError(UiText)`, `showSnackBar(UiText)`. The app implements it with today's `CommonController`.
- Flows switch from `appRef.read(CommonController.provider.notifier)` (23 uses) to `ref.read(uiFeedbackProvider)`.
- Check: 0 reads of `CommonController` outside `digital/lib/app/`.

### Step 4: `auth_api` ports (2–3 PRs, with Mobile plan 11 step 5)

- `SessionReader` (logged-in state, user access type), `LoginLauncher`, `KycLauncher`.
- Implementations stay in `digital/lib/features/auth` for now. The app wires them.
- Switch `loan` first: 11 imports of `auth_use_case.dart`, 7 of `auth_flow_use_case.dart`, 4 of `kyc_use_case.dart`.
- Check: those import counts reach 0 in `loan`. Wiring test lists the 3 new ports.

### Step 5: exit ports per feature (with Mobile plan 11 step 4)

- `LoanExits` first: payment, repeat order (`ro`), RL, BPKB release, onboarding.
- The app fills each callback with a `GoRouter` push.
- Check: `loan` has 0 imports of other features' screens.

### Step 6: shared service ports

- Analytics (Mobile plan 02), feature flags (Mobile plan 12) and network (Mobile plan 07) each expose one port provider in their `shared_lib` package.
- Device services used by flows (`FileService`, `CameraService`, `ImagePickerService`, `VidaLivenessService`, the IPV service) become ports when the first feature package needs them.

### Step 7: per-package providers on extraction

- Each extracted package gets `lib/src/di/<feature>_providers.dart`. Its barrel exports routes, exits, port types and the implementation providers the app wires. Nothing else.
- Test helpers: `test/helpers/overrides.dart` per package with fakes for each port.
- Check: the barrel exports no `*_screen.dart` and no notifier.

### Step 8: shrink the big barrels

- As repositories leave `data/customer`, drop them from `customer.dart` (115 exports today).
- Stop re-exporting `go_router` from `core.dart` once only `digital` and presentation code use it.

### Parity check

- Moving overrides (step 1) and adding ports (steps 3 to 6) should not change behaviour. The app must run the same on SIT.
- While a switch flag exists, both paths must be wired. The wiring test (step 1) builds the container twice, with the flag forced to old and to new, and reads every provider in `allPorts`. None may throw on either path.
- The switch point is a provider in `digital/lib/app/di/` that reads the switch flag and returns the old or new implementation. Features never read the flag themselves.
- Tests override ports per path. `test/helpers/overrides.dart` gives one fake set for the old path and one for the new path, so the same widget test runs with the flag off and on.
- `UiFeedback` (step 3) must show the same loading, error and snack bar as `CommonController`. Golden screenshots of the key screens prove it.
- Approved deltas: none. This plan moves wiring only.

## Done when

- `main.dart` has no inline overrides. It calls `appOverrides(...)`.
- The wiring test runs in CI and covers every provider that throws `UnimplementedError`.
- 0 `ProviderScope.containerOf` outside `digital/lib/app/`.
- `loan`, `auth`, `rl` and `ro` read other features only through ports listed in `allPorts`.
- No extracted package's barrel exports a screen or a notifier.
- `pubspec.lock` contains no `get_it`, `injectable` or `kiwi`.
- While a switch flag exists, the wiring test resolves every port on both the old and the new path.
- When a switch flag is deleted, its old-path wiring and per-path test overrides go in the same PR.

## Effort and owner

- Size: **M** (comes with layering, from the parent table).
- Rough time: 2 sprints for steps 1–4. Steps 5–8 ride on each feature extraction.
- Owner: Customer Mobile Apps squad.

## Depends on / related plans

- Mobile plan 11: Repo layout (packages that need ports; order of extraction).
- Mobile plan 08: Layering (domain interfaces that ports implement).
- Mobile plan 09: State management (removing `appRef`; `UiFeedback`).
- Mobile plan 02: Analytics wrapper (`analyticsProvider`).
- Mobile plan 12: Feature flags (flag port).
- Mobile plan 07: Networking (`NetworkConfig` and the HTTP client as ports).
- Mobile plan 03: Testing (fakes for ports, wiring test).
- Mobile plan 06: Lint and guardrails (checker rules in CI).

## Risks

| Risk | Mitigation |
|---|---|
| A port is not wired and the app crashes at start | Wiring test in CI. Checker forces every throwing provider into `allPorts`. |
| Too many tiny ports | Create a port only when a second package needs it. One port per capability, not per method. |
| Overrides that watch other providers rebuild too often | Use `ref.watch` only on stable providers. Cover with the wiring test and a SIT smoke. |
| Nested `ProviderScope` overrides sneak in | Review rule plus a checker rule for `ProviderScope(` with `overrides:` outside `main.dart` and tests. |
| Exit callbacks hide a button by mistake (`null`) | A widget test per exit: wired shows the button, `null` hides it. |
