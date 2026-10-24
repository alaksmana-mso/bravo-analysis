## Goal

Every runtime flag is a typed entry in one catalogue, with a key, a safe default, an owner and a removal date. Code reads flags through one port, whether the value comes from Firebase Remote Config or Mixpanel. Old flags get removed on a schedule, not by accident.

## Where we are today

Repo: `bravo-customer-app`, `master` @ `190e1d20`. Counts are from `digital/lib` without generated files unless stated.

### Firebase Remote Config

- `digital/lib/app/remote_config/remote_config.dart` (174 lines): one freezed class, `RemoteConfig`, with **44** fields. Its generated file `remote_config.freezed.dart` is **2,443** lines, plus 371 lines in `remote_config.g.dart`.
- 32 of the 44 fields are on/off feature flags (`featureFlag*` or `feature*`). The rest are settings: durations, delays, image-check thresholds (`IpvConfig`), soft-update version, session-replay sampling.
- 6 fields are per-product maps (`ProductBasedFeatureFlag`), parsed by `product_ff_converter.dart`.
- `remote_config_repository.dart` (239 lines) maps **44** `BFI_MOBILE_*` keys by hand. Each key name and its fallback are written out once per field.
- Defaults live in `@Default(...)` annotations. The repository falls back to `RemoteConfig.defaultValue()`.
- The `IS_IPV_BYPASS_ENABLED` dart-define forces 7 image-check and liveness flags off in test builds.
- Fetch: first fetch with a 5 s timeout, a second fetch, then real-time updates (`onConfigUpdated`) for every key. Minimum fetch interval is 1 hour.
- `getRemoteConfigUseCase` (a `StreamProvider`) has **65** references in **44** files. Read styles are mixed: `.select(...latestValueOrNull?.x == true)`, `.valueOrNull ?? RemoteConfig.defaultValue()`, `.selectAsync(...)`, `.future`.
- 2 flags are parsed but never read in `lib/`: `featureFlagSurveyor` and `featureFlagLov`. Only tests use them.

### Mixpanel flags (experiments)

- `digital/lib/app/tracker/mixpanel_feature_flag_service.dart` (56 lines) wraps Mixpanel's flag API. Lookup is network-only; prefetch is off.
- `digital/lib/app/experiment/experiment_repository.dart` (91 lines) holds 2 experiments as private string keys: force-register and home revamp. A value of `treatment` means "on".
- It tracks one `experiment-exposure` event per key per session, and falls back to the default after a 10 s timeout.
- The home-revamp result is read in 7 places, 2 of them through the global `appRef` in `go_router_extension.dart`.

### Build-time switches (not runtime flags)

- `digital/lib/app/app_config.dart` has 5 `IS_*` dart-defines: `IS_DEVICE_ROOT_CHECKER_ENABLED`, `IS_HTTP_PROXYING_ALLOWED`, `IS_IPV_BYPASS_ENABLED`, `IS_REMOTE_CONFIG_BYPASS_ENABLED`, `IS_FAKE_CAMERA_ENABLED`.
- The prod workflow sets only `IS_DEVICE_ROOT_CHECKER_ENABLED`. The SIT/UAT workflow sets 4 of them.
- These change per build, not per user. They are correct as build switches and should stay that way.

### Gaps

- No single list of flags with owners or dates.
- Two flag systems with two APIs and no shared interface.
- Any key change emits a whole new `RemoteConfig`. Screens that do not use `.select` rebuild for unrelated flags.
- Adding one flag touches 3 files plus code generation.

## Target (what Jago does, adapted for BFI)

### Jago pattern

- `module_configuration/lib/common/feature_flags/base_feature_flag.dart`: a flag object with `key`, `initialValue`, `isRealtime` and a value notifier. It also records which platform supplied the value.
- Typed subclasses: `bool_feature_flag.dart`, `int_feature_flag.dart`, `string_feature_flag.dart`, `json_remote_config.dart`, `json_class_remote_config.dart` (JSON mapped to a class).
- `feature_flag_platform.dart`: one interface for every vendor (`getBool`, `getString`, `getNumber`, `getJsonString`, `hasFlag`, `fetchAndActivate`, `onConfigUpdated`).
- Four implementations in `module_common/lib/feature_flags/providers/`: Firebase, Split.io, GrowthBook, and a default.
- `module_common/lib/feature_flags/platforms/feature_flag_platforms.dart` asks platforms in a fixed priority order. The first one that has the key wins. Only flags marked `isRealtime` refresh on a live config update.
- The catalogue is `feature_flags.dart` (1,703 lines, about 256 entries), plus per-team files in `epics/`. Keys carry a team prefix and often a date, for example a `dl_` prefix and a `_20240925` suffix.

### BFI shape (Riverpod)

- A small `flags` folder in `shared_lib/core` (or its own package once Mobile plan 01: Repo layout lands). It holds the flag types and the port.
- One catalogue file per feature: `digital/lib/features/<feature>/<feature>_flags.dart`. Each entry has key, default, owner, ticket and removal date.
- One `FlagSource` port. Two adapters: `FirebaseFlagSource` and `MixpanelFlagSource`. Each flag names its source, so there is no guessing by priority.
- A Riverpod `Provider.family` returns the current value for one flag. Widgets rebuild only when that flag changes.

```dart
// shared_lib/core/lib/src/flags/flag.dart
enum FlagSource { remoteConfig, mixpanel }

sealed class Flag<T> {
  const Flag({required this.key, required this.defaultValue,
      required this.owner, required this.removeBy,
      this.source = FlagSource.remoteConfig, this.realtime = false});
  final String key; final T defaultValue; final FlagSource source;
  final String owner; final DateTime? removeBy;   // null = permanent setting
  final bool realtime;
}
final class BoolFlag extends Flag<bool> {
  const BoolFlag({required super.key, required super.defaultValue,
      required super.owner, required super.removeBy,
      super.source, super.realtime});
}
// IntFlag, StringFlag and JsonFlag<T> (with a fromJson mapper) look the same.

abstract interface class FlagStore {         // the port
  T read<T>(Flag<T> flag);                    // never throws, falls back to default
  Stream<T> watch<T>(Flag<T> flag);
}

final flagProvider = StreamProvider.family<Object?, Flag<Object?>>(
    (ref, flag) => ref.watch(flagStoreProvider).watch(flag));
```

```dart
// digital/lib/features/home/home_flags.dart
abstract final class HomeFlags {
  static const inbox = BoolFlag(key: 'BFI_MOBILE_FEATURE_FLAG_INBOX',
      defaultValue: true, owner: 'customer-mobile', removeBy: null);
  static const homeRevamp = BoolFlag(key: 'bfi-mobile-home-revamp-exp',
      defaultValue: false, source: FlagSource.mixpanel,
      owner: 'growth', removeBy: /* date agreed with product */ null);
}
```

### Rules

- **Keep every existing key string.** Remote Config and Mixpanel consoles must not change during the move.
- **Defaults are the safe state.** If the network fails, the app must behave as it did before the feature existed, unless the flag is a kill switch.
- **Release flags have a removal date.** Settings (durations, thresholds) are marked permanent and do not need one.
- **Experiments track exposure.** The `MixpanelFlagSource` keeps today's one-exposure-per-session event, sent through Mobile plan 05: Analytics wrapper.
- **Security switches stay build-time.** Root check, proxying, fake camera and image-check bypass stay as dart-defines. Do not make them remotely switchable.

### What not to copy from Jago

- Flags as static mutable globals. Use `const` definitions plus a Riverpod store, so tests can override values.
- One 1,700-line catalogue file. Use one small file per feature.
- Three vendors with a priority order. BFI has two sources; each flag names its own.
- Date suffixes inside new key names are fine, but do not rename existing keys to add them.

## Plan

1. **Port and adapters (1 PR).** Add `Flag`, `BoolFlag`, `IntFlag`, `StringFlag`, `JsonFlag`, `FlagStore`, `FirebaseFlagSource` and `MixpanelFlagSource`. Wrap the current Firebase fetch logic (5 s first fetch, real-time listener) unchanged. Add a `FakeFlagStore` for tests. Check: unit tests for parse errors (bad JSON, wrong type) return the default.
2. **Catalogue the 44 keys (1 PR).** Write one `Flag` per existing key in per-feature files, with today's defaults. Do not change call sites yet. Add a test that compares the catalogue against the keys in `remote_config_repository.dart`, so nothing is missed. Check: 44 entries; the test passes.
3. **Bridge (1 PR).** Build `RemoteConfig` from the `FlagStore` instead of reading `FirebaseRemoteConfig` directly. Old call sites keep working. Check: `remote_config_repository_test.dart` passes with the same expectations.
4. **Move call sites, one feature per PR.** Replace `getRemoteConfigUseCase.select(...)` with `ref.watch(flagProvider(HomeFlags.inbox))` in that feature. Start with `home`, then `loan`, `auth`, `pin`, `rl`, `ro`. Check: the reference count of `getRemoteConfigUseCase` goes down in the CI baseline (same ratchet script as Mobile plan 05: Analytics wrapper).
5. **Move the two experiments (1 PR).** Define them as `BoolFlag(source: FlagSource.mixpanel)`. Remove the private keys from `experiment_repository.dart`. Replace the 2 `appRef` reads in `go_router_extension.dart` with a ref passed in (see Mobile plan 03: State management). Check: one `experiment-exposure` event per key per session in Mixpanel, same as today.
6. **Delete `RemoteConfig` (1 PR).** When the reference count reaches 0, delete `remote_config.dart`, its 2,814 generated lines, and the hand-written mapping. Check: no `RemoteConfig` type left in `digital/lib`.
7. **First cleanup (1 PR per flag).** Remove `featureFlagSurveyor` and `featureFlagLov` (never read in `lib/`). For every other release flag, ask the owner if it is fully on in prod. If yes, remove the flag and the dead branch. Delete the key in the Remote Config console one release later.
8. **Lifecycle check in CI (1 PR).** A unit test fails when a release flag is past its `removeBy` date. It prints the owner and the key. Allow a 2-week grace period. Add a `docs/flags.md` generated from the catalogue (key, type, default, source, owner, remove by).
9. **Debug override screen (1 PR, optional).** In dev and SIT flavors, list every flag from the catalogue with a switch that overrides it locally. This replaces ad-hoc `IS_REMOTE_CONFIG_BYPASS_ENABLED` testing for most cases.

### Flag lifecycle

| Stage | Who | What happens |
|---|---|---|
| Add | Feature developer | Entry in `<feature>_flags.dart` with default, owner, ticket, `removeBy` (release flags: at most 3 months) |
| Roll out | Product + squad | Value changed in the Remote Config or Mixpanel console |
| Fully on | Owner | Ticket raised to remove the flag |
| Remove | Feature developer | Code branch and catalogue entry deleted; console key deleted one release later |
| Overdue | CI | Test fails after `removeBy` + 2 weeks |

## Done when

- 0 references to `FirebaseRemoteConfig` or `MixpanelFeatureFlagService` outside the two flag adapters.
- 0 references to `getRemoteConfigUseCase` and the `RemoteConfig` class in `digital/lib`.
- Every flag key used in code is in the catalogue. A test fails if a key string appears outside a `*_flags.dart` file.
- Every release flag has an owner and a `removeBy` date. The overdue test runs in the PR pipeline.
- `featureFlagSurveyor` and `featureFlagLov` are gone.
- A widget that reads one flag does not rebuild when another flag changes (widget test).

## Effort and owner

- Size: **M** (from the parent table).
- About 2–3 sprints. Steps 1–3 in one sprint. Steps 4–6 over 1–2 sprints next to feature work. Cleanup (step 7) continues after.
- Owner: Customer Mobile Apps squad. Each flag's owner (a squad or a product manager) is named in the catalogue.

## Depends on / related plans

- Mobile plan 01: Repo layout (where the flags package lives).
- Mobile plan 03: State management (removing `appRef` reads of experiments).
- Mobile plan 04: Dependency injection (flag store provider and test overrides).
- Mobile plan 05: Analytics wrapper (experiment exposure events, shared CI ratchet script).
- Mobile plan 09: Security (security switches stay build-time).
- Mobile plan 12: Lint and guardrails (lint rule against raw key strings).

## Risks

| Risk | Mitigation |
|---|---|
| A key is mistyped during the move and a feature silently uses its default | Step 2 test compares catalogue keys with the old mapping; keys are copied, not retyped |
| A default changes by accident | Step 2 copies defaults from `@Default`; a test checks each default against `RemoteConfig.defaultValue()` before deletion |
| Removing a flag that is not fully on in prod | Owner confirms in the ticket; console value checked before the PR |
| Real-time updates flip a flag mid-journey | Only flags marked `realtime` update live; others apply on next app start |
| The overdue test blocks unrelated PRs | 2-week grace; owner can extend `removeBy` once with a reason in the PR |
| Mixpanel lookup is slow (network-only) | Keep the 10 s timeout and default; consider prefetch in a later PR |
