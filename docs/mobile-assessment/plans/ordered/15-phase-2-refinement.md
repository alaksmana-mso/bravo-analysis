## Summary

This page prepares Phase 2 of the mobile roadmap ("Seams with the same behaviour") for refinement. It covers all 25 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title, same style as Phase 0 (DM-3545): "[Tech x DK] Mobile App Improvement - Seams, Same Behaviour".
* **Parent:** Mobile roadmap: step by step, section "Phase 2: Seams with the same behaviour". Earlier notes: Mobile roadmap Phase 0: Close the leak – refinement notes and Mobile roadmap Phase 1: Safety net first – refinement notes.
* **Facts checked on 20 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `97749b2` (19 Oct), the Datadog, Firebase and GitHub docs, and `bfi-base-template`.

**What Phase 2 is.** Every step puts a new interface ("port") *behind* code that already works, or adds machinery for later rollouts. Customers see and send exactly the same things. The parity net from Phase 1 proves it. After this phase, the risky changes in Phases 3 to 9 can hide behind switch flags.

**The rule for every class B step on this page:** the old public call stays. Only its body changes. Tests that exist today keep passing without edits. If a test must change, the step is not class B and needs a flag or a sign-off.

### Five facts that shape Phase 2

**1. The seams are smaller than the plan pages say, in a good way.** Plan 10 counted 4 ports overridden in `main.dart`. Today `main.dart` overrides 2 (`DeviceIntegrityService`, `NetworkConfig`), and 4 library files throw `UnimplementedError` as a "wire me" signal (`device_integrity_service.dart`, `product_config.dart`, `product.dart`, `network_config.dart`). The composition root (2.15) starts from these 4.

**2. Datadog already has what 2.8 and 2.23 need.** The Datadog Flutter plugin (BFI uses `^3.5.0`) has built-in **Feature Flag Tracking**: one call, `DatadogSdk.instance.rum?.addFeatureFlagEvaluation(key, value)`, and the RUM UI can then split sessions, errors and crashes by flag value. So "tag every session with the switch-flag state" needs no custom attribute scheme. Crashlytics needs its own custom key (limit: 64 keys, 1,024 characters each).

**3. Remote Config is already real-time.** `remote_config_repository.dart` listens to `onConfigUpdated` and activates at once. Firebase's own guidance: real-time updates bypass the fetch interval, and activating at once "should be avoided for sensitive UIs". This is exactly why the `SwitchFlag` rule (2.12) says: read the value at the start of a journey, not in the middle.

**4. R8 and symbol uploads already work.** `build-prod.yml` uploads Flutter symbols to Crashlytics and runs `datadog-ci flutter-symbols upload` with `--android-mapping-location .../mapping.txt`. So `mapping.txt` exists on every prod build today. Step 2.17 only makes the setting explicit and adds a fail-if-missing check. `proguard-rules.pro` has 92 lines (25 `keep` rules, for MediaPipe, protobuf and Insider).

**5. The shared CI template has no Flutter pipeline.** `bfi-base-template` has reusable `pr-pipeline` and `deploy` workflows for Java, JS, Go, Node, Python, .NET and PHP, but none for Flutter. The 4 build workflows here total 2,990 lines with 259 `--dart-define` lines. Step 2.19 can either stay in-repo or add a Flutter template for other BFI Flutter apps (`bravo-agency-app`, RO Tools, SQUARE).

Counts refreshed on 19 Oct: 204 `logEvent` calls in 87 files (plan 02 said 187 in 81); 61 `DatadogLog` call sites (plan 05 said 59); 86 `RemoteConfig` references outside its folder; `remote_config.freezed.dart` 2,486 lines + `remote_config.g.dart` 376 lines; 91 field annotations in `remote_config.dart`.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks, including review. Class: **A** no app change, **B** same behaviour.

| # | Proposed ticket title | Today (20 Oct) | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1 | `feat(analytics): Port package shared_lib/analytics` | `Analytics` class + separate Mixpanel/Insider/AppsFlyer services | Mobile engineer | S | – | | |
| 2.2 | `refactor(analytics): Adapters and fan-out behind the old calls` | 204 direct calls in 87 files | Mobile engineer | M | 2.1, 1.11 | | |
| 2.3 | `ci: Ratchet direct analytics calls` | No ratchet | Mobile engineer | XS | 1.19 | | |
| 2.4 | `refactor(ui): Digital* components track through the port` | 9 UI files import `EventTracker` / Mixpanel | Mobile engineer | S | 2.2 | | |
| 2.5 | `refactor(core): Monitoring port behind DatadogLog` | Static class, `error/warn/debug`, no `info` | Mobile engineer | S | – | | |
| 2.6 | `feat(core): trace_id and endpoint as log attributes` | Set as global Crashlytics keys today | Mobile engineer | S | 2.5 | | |
| 2.7 | `refactor(app): Crash hooks into the Crashlytics adapter` | In `main.dart` | Mobile engineer | XS | 2.5 | | |
| 2.8 | `feat(core): Report switch-flag values to RUM and Crashlytics` | 5 attribute/key calls today, none for flags | Mobile engineer | S | 2.5, 2.12 | | |
| 2.9 | `ci: Ratchet direct Crashlytics/Datadog calls` | 2 direct SDK calls outside `DatadogLog` | Mobile engineer | XS | 1.19 | | |
| 2.10 | `feat(flags): Flag port, Firebase and Mixpanel sources` | Firebase fetch logic in one repository, Mixpanel flags separate | Mobile engineer | M | – | | |
| 2.11 | `feat(flags): Catalogue of the Remote Config keys` | 91 fields in one model | Mobile engineer + product | S | 2.10 | | |
| 2.12 | `feat(flags): SwitchFlag kind with owner and removal date` | None | Mobile engineer | S | 2.10 | | |
| 2.13 | `refactor(flags): Build RemoteConfig from the flag store` | 86 references outside the folder | Mobile engineer | S | 2.11 | | |
| 2.14 | `feat(dev-mode): Flag override screen` | `dev_mode_screen.dart` exists (1,038 lines) | Mobile engineer | S | 2.10 | | |
| 2.15 | `refactor(app): Composition root and wiring test` | 2 overrides in `main.dart`, 4 `UnimplementedError` ports | Mobile engineer | S | – | | |
| 2.16 | `chore: DI rules and container-lookup ratchet` | 2 `ProviderScope.containerOf` uses | Mobile engineer | XS | 1.19 | | |
| 2.17 | `build(android): Make R8 explicit, fail without mapping.txt` | R8 on by default, mapping uploaded to Datadog | Mobile engineer | S | – | | |
| 2.18 | `ci: Protect-build and register-build slots` | None | Mobile engineer | XS | 2.19 | | |
| 2.19 | `ci: Reusable build workflows and one dart-define file` | 4 workflows, 2,990 lines, 259 define lines | Mobile engineer + SRE | M | Phase 0 done | | |
| 2.20 | `test: Run a widget test on both paths` | `flutter_test_config.dart` exists | Mobile engineer | S | 2.12 | | |
| 2.21 | `build: Force a switch flag in SIT/UAT builds` | None | Mobile engineer + QA | S | 2.12, 1.14 | | |
| 2.22 | e2e twice per release candidate | Suite not yet triggered from app CI | QA + mobile engineer | S | 1.14, 2.21 | | |
| 2.23 | Cohort dashboard by flag value | Release dashboards exist, no flag split | Mobile engineer + SRE | S | 2.8, 1.4 | | |
| 2.24 | `docs: Kill-switch runbook` + SIT rehearsal | None | Squad lead + on-call | S | 2.12, 2.23 | | |
| 2.25 | Android signing with a key in Cloud KMS (proof of concept) | Keystore as a base64 secret | SRE + mobile engineer | M | Phase 0 Q14 | | |

**Suggested order.** Sprint 1: 2.15, 2.16, 2.5, 2.7, 2.10, 2.17 (small, independent). Sprint 2: 2.1, 2.2, 2.3, 2.11, 2.12, 2.13, 2.6. Sprint 3: 2.4, 2.8, 2.9, 2.14, 2.20, 2.21, 2.19. Sprint 4: 2.18, 2.22, 2.23, 2.24, then the release that closes the gate. 2.25 runs on the side with SRE.

**Release plan.** Phase 2 code can ship in normal releases as it lands (class B rides along). The exit gate needs one release that holds all of it at 100% with no regression.

## Definition of ready for every Phase 2 ticket

* The ticket links to this page and to the Phase 2 epic.
* The owner is a named person.
* Acceptance criteria are copied from the step below. For class B: "existing tests pass unchanged" is always one of them.
* The ticket names the parity-net checks it relies on: golden names file (1.11), golden screenshots (1.12), fixtures (1.13), e2e (1.14).
* No step on this page changes an event name, a flag default, a log destination or a user-facing string. If it must, the ticket moves to Phase 3 as an approved delta.

## 2a. Analytics seam

### Step 2.1: Analytics port package

**Today.** `digital/lib/app/analytics.dart` holds an `Analytics` class exposed as a Riverpod provider, wrapping Firebase. Mixpanel is a separate typed `EventTracker` + `MixpanelService` + `TrackerJourneyManager`. `AppsflyerService` and `InsiderService` are separate again. 204 `logEvent(` calls in 87 files. No package holds a vendor-free interface.

**Tasks.** Create `shared_lib/analytics` with `Analytics`, `AnalyticsAdapter`, `AnalyticsEvent`, `AnalyticsContext`, `AnalyticsUser` and a `FakeAnalytics`. Pure Dart, no Flutter or vendor import.

**Acceptance criteria.** `melos run analyze` passes. The package has no Flutter or vendor dependency. 100% unit-tested. Nothing in `digital` uses it yet.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own small port in `shared_lib/analytics`, as plan 02 sketches | Fits Riverpod, typed events, our naming rules. No vendor lock | We maintain it |
| B. A customer-data-platform SDK (for example Segment) as the single sink, vendors wired server-side | One SDK, vendors swapped in a console | New cost and vendor. Events leave through a third party. Insider and AppsFlyer have device-side features that need their own SDKs |
| C. Keep Firebase as the "hub" and forward from there | No new code | Firebase cannot fan out to Mixpanel, Insider or AppsFlyer on-device |

**Recommended: A.**

### Step 2.2: Adapters and fan-out behind the old calls

**Today.** Logic for Firebase, Mixpanel and Insider lives in three services with different shapes. Firebase names are strings at the call site.

**Tasks.** Add `FirebaseAdapter`, `MixpanelAdapter`, `InsiderAdapter`, `AppsFlyerAdapter`, `DatadogRumAdapter` in `digital/lib/app/analytics/adapters/`. Move logic without changing it. Keep `Analytics.logEvent` and `MixpanelService.track` as thin shims that call the port.

**Acceptance criteria.** Golden names file (1.11) unchanged. Adapter tests assert the exact name and parameters sent to a mocked SDK, one per naming rule. Existing tests pass unchanged. Firebase DebugView on a dev build shows the same event names for a 10-minute smoke run.

**Who / size.** One mobile engineer. M. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Shims first, adapters behind them, call sites untouched | Zero call-site diff in this phase. Easy to prove parity | Two ways to call analytics until Phase 5 |
| B. Adapters plus a mass find-and-replace of all 204 calls in one PR | Done in one go | 87-file PR, hard to review, hard to prove parity |
| C. Adapters, and only new code uses the port | Smallest | The old path never shrinks |

**Recommended: A.** The ratchet (2.3) stops the old path from growing, and Phase 5 drains it.

### Step 2.3: Ratchet direct analytics calls

**Today.** No check. Direct calls grew from 187 to 204 since 11 Sep.

**Tasks.** Add rules `analytics-direct-call` (Firebase `logEvent`, `MixpanelService.track`) to the Phase 1 checker (`tool/arch_check.dart`, step 1.19). Baseline on merge day.

**Acceptance criteria.** A PR that adds a new `logEvent(` outside the adapters fails.

**Who / size.** One mobile engineer. XS. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules in the existing checker | One tool, one baseline file | None |
| B. A separate script as plan 02 sketched | Independent | Two checkers to maintain |
| C. Code review only | No code | It grew by 17 calls in 5 weeks with review only |

**Recommended: A.**

### Step 2.4: `Digital*` components track through the port

**Today.** 9 files under `digital/lib/app/ui` and `app/widget` import `EventTracker` or the Mixpanel session-replay package. `DigitalButton` takes an `EventTracker Function()? eventTracker` callback.

**Tasks.** Components call `analytics.track` through the port (or an `onTrack` callback, see plan 13 step 2). Keep the `eventTracker` parameter as a shim until Phase 8.

**Acceptance criteria.** Golden names file unchanged. Widget tests use `FakeAnalytics`. Mixpanel session replay still records in a SIT smoke run.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Components read the port from `ref` (they are already in a Riverpod tree) | Small diff | Components depend on Riverpod |
| B. Components get an `onTrack` callback, the screen wires it | Components stay pure, ready for the design-system package (Phase 8) | Every call site passes a callback |
| C. A `ComponentTracker` interface injected once at app start | One wiring point | A global |

**Recommended: B.** It is the shape the design-system package needs anyway.

## 2b. Monitoring seam

### Step 2.5: Monitoring port behind `DatadogLog`

**Today.** `shared_lib/core/lib/src/utils/datadog_log.dart` is a static class with `error`, `warn`, `debug` (no `info`), a `DatadogLogger` and a `DatadogErrorReporter` set from the app, and a `DatadogLogObserver` for Riverpod. 61 call sites. 2 direct SDK calls outside it. `datadog_flutter_plugin ^3.5.0` supports global log attributes (since 2.4.0).

**Tasks.** Add `Monitoring`, `MonitoringAdapter`, a Datadog adapter and a Crashlytics adapter. `DatadogLog.error/warn/debug` build a `LogEvent` and call `Monitoring`. Keep the static signatures. Add `DatadogLog.info`.

**Acceptance criteria.** `datadog_log_test.dart` passes unchanged. A new test shows one log reaches both adapters. No change in log volume on SIT over one day (Datadog log count per hour within ±10%).

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Port inside `shared_lib/core`, static facade kept | Smallest diff, no import changes | `core` still depends on the Datadog SDK |
| B. New package `shared_lib/monitoring`, `core` re-exports the facade | Clean package boundary now | More files to move; same behaviour |
| C. Replace `DatadogLog` with the Datadog SDK directly everywhere | No port | Opposite of the goal |

**Recommended: A now, B when `core` is split in Phase 8.**

### Step 2.6: `trace_id` and endpoint as log attributes

**Today.** On HTTP errors the client reads `x-trace-id` and sets it as a global Crashlytics key. Datadog logs do not carry it as an attribute.

**Tasks.** Send `trace_id` and `endpoint` as Datadog log attributes on the log call. Pass them to Crashlytics per `recordError` call instead of as global keys.

**Acceptance criteria.** In Datadog Logs, `@trace_id:*` shows values on HTTP errors from a SIT build. Crashlytics shows the trace ID on a test non-fatal. Existing tests pass unchanged.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Per-call attributes through the port | Precise, no stale global state | Needs the port (2.5) |
| B. Global logger attribute updated on every response | One line | A stale ID from the last request can land on an unrelated log |
| C. Rely on RUM-to-APM linking only (Phase 1 spike) | No app code | Only works for RUM resources, not for logs |

**Recommended: A.**

### Step 2.7: Crash hooks into the Crashlytics adapter

**Today.** `FlutterError.onError`, `PlatformDispatcher.onError` and the Crashlytics setup sit in `main.dart`.

**Tasks.** Move them into `CrashlyticsMonitoringAdapter.setup()`. `main.dart` calls `Monitoring.setup()`.

**Acceptance criteria.** The dev-menu "test crash" shows in Crashlytics for the dev flavor. Existing tests pass unchanged.

**Who / size.** One mobile engineer. XS. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Move as is, no behaviour change | Pure move | None |
| B. Move and add a Datadog RUM error forward at the same time | One PR | Changes what Datadog receives: not class B |
| C. Leave in `main.dart` | No work | `main.dart` stays the place everything leaks into |

**Recommended: A.**

### Step 2.8: Report switch-flag values to RUM and Crashlytics

**Today.** 5 `addAttribute` / `setCustomKey` calls in the app, none for flags. The Datadog plugin has Feature Flag Tracking: `addFeatureFlagEvaluation(key, value)` on the RUM instance (plugin ≥ 1.3.2; BFI is on ^3.5.0). Datadog does not allow `.`, `:`, `-` and some other characters in flag names.

**Tasks.** When a switch flag is read at journey start, call `addFeatureFlagEvaluation` and set a Crashlytics custom key (`flag_<name>`). Do it through the `Monitoring` port so adapters own the SDK calls.

**Acceptance criteria.** In Datadog RUM "Feature Flags", a SIT test flag shows sessions by value. A Crashlytics test crash on SIT shows `flag_<name>`. Flag names in the catalogue (2.11) use only letters, digits and underscores.

**Who / size.** One mobile engineer. S. Class B (adds attributes, changes no behaviour).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Datadog Feature Flag Tracking + one Crashlytics key per switch flag | Built-in UI splits errors and crashes by flag value. No custom attribute scheme | Crashlytics key limit 64 (fine for a handful of switch flags) |
| B. A custom RUM global attribute `flags=…` as plan 05 sketched | Works on older plugins | Reinvents what the SDK has. Harder to query |
| C. Only Firebase user properties | Already there | Not visible in Datadog, where the health dashboard lives |

**Recommended: A.**

### Step 2.9: Ratchet direct Crashlytics and Datadog calls

**Today.** 2 direct SDK calls outside `DatadogLog`.

**Tasks.** Rule `monitoring-direct-call` in the Phase 1 checker: imports of `firebase_crashlytics` and `DatadogSdk.instance.logs` outside the adapters.

**Acceptance criteria.** A new direct call fails CI.

**Who / size.** One mobile engineer. XS. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rule in the existing checker | One tool | None |
| B. `analysis_options.yaml` banned-import lint (plugin) | IDE feedback | Needs a plugin and a baseline |
| C. Review only | No code | Not enforced |

**Recommended: A.**

## 2c. Feature-flag seam

### Step 2.10: Flag port, Firebase and Mixpanel sources

**Today.** `remote_config_repository.dart` (245 lines): `fetchTimeout` 30 s, `minimumFetchInterval` 1 h (0 when `IS_REMOTE_CONFIG_BYPASS_ENABLED`), first fetch with a 5 s timeout, then `onConfigUpdated` → `activate()` → new value. Mixpanel flags live in `mixpanel_feature_flag_service.dart` and `experiment_repository.dart`. `firebase_remote_config ^5.1.5`.

**Tasks.** Add `Flag`, `BoolFlag`, `IntFlag`, `StringFlag`, `JsonFlag`, `FlagStore`, `FirebaseFlagSource`, `MixpanelFlagSource`, `FakeFlagStore`. Wrap today's fetch logic unchanged.

**Acceptance criteria.** Unit tests: bad JSON or wrong type returns the default. The 5 s first-fetch timeout and 1 h interval are the same values, asserted in a test. Existing tests pass unchanged.

**Who / size.** One mobile engineer. M. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own typed port over Firebase and Mixpanel, as plan 12 sketches | Fits what we have. No new vendor | We maintain it |
| B. Adopt an OpenFeature-style interface with providers | Standard shape, vendor-neutral | Dart support is thin; still our own providers |
| C. Replace Firebase Remote Config with a flag vendor (LaunchDarkly, GrowthBook, …) | Richer targeting and audit | New cost and migration in a "same behaviour" phase |

**Recommended: A.** Keep the port shape close to OpenFeature names so C stays possible later.

### Step 2.11: Catalogue of the Remote Config keys

**Today.** One `RemoteConfig` model with 91 field annotations (plan 12 said 44 keys; several fields are nested objects). Generated code: 2,486 + 376 lines. 86 references outside the folder.

**Tasks.** One `Flag` per existing key in per-feature files, with today's defaults. A test compares the catalogue against the keys and defaults in `remote_config_repository.dart`.

**Acceptance criteria.** The catalogue test passes. The count of keys is written in the ticket. No call site changes.

**Who / size.** One mobile engineer, product confirms owners. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Hand-written catalogue, test keeps it honest | Readable, reviewable | One-time typing |
| B. Generate the catalogue from the Remote Config console export | Exact | Console export has no owner or feature; still needs editing |
| C. Keep the wide model, add owners as comments | No new structure | Does not give typed flags |

**Recommended: A**, with B's export as the starting list.

### Step 2.12: `SwitchFlag` kind

**Today.** None. Remote Config real-time updates bypass the fetch interval and activate at once. Firebase advises against activating mid-screen for sensitive UI.

**Tasks.** `SwitchFlag` = `BoolFlag` with required `owner` and `removeBy`, default = old path, `realtime: true`, read at journey start only. A test fails on an overdue `removeBy` with no grace period. SIT and UAT builds can force a value with a `--dart-define` (2.21). Prod ignores it.

**Acceptance criteria.** A `SwitchFlag` with no `removeBy`, or a past one, fails CI. A unit test shows a flip mid-journey does not change the running journey.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flag read once per journey, held in the journey's state | Predictable. Matches Firebase guidance | A flip reaches a user at their next journey start, not at once |
| B. Flag watched live, screens rebuild on change | Instant kill switch | A user mid-KYC can land on the other path. Hard to test |
| C. Flag read once per app start | Simplest | A kill switch waits for a restart |

**Recommended: A.**

### Step 2.13: Build `RemoteConfig` from the flag store

**Today.** `RemoteConfigRepository` reads `FirebaseRemoteConfig` directly.

**Tasks.** Build the `RemoteConfig` model from the `FlagStore`. Old call sites keep working.

**Acceptance criteria.** `remote_config_repository_test.dart` passes with the same expectations. Widget tests that read a flag give the same result through both reads.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Bridge, keep the model until Phase 5 deletes it | No call-site change now | Two reads of the same key exist for a while |
| B. Delete the model now and move all 86 references | Done in one go | Large PR, not class B |
| C. Leave the model on Firebase, new flags only in the store | Smallest | Two sources of truth with no end date |

**Recommended: A.**

### Step 2.14: Flag override screen in dev and SIT

**Today.** `dev_mode_screen.dart` (1,038 lines) exists for non-prod builds, with API history and tools.

**Tasks.** A section in dev mode that lists every flag from the catalogue with a local override. Switch flags first. Not compiled into prod.

**Acceptance criteria.** A prod build contains no override code (check with a `const bool.fromEnvironment` guard and a grep of the release build's assets is not possible for Dart, so assert through a prod-flavor widget test that the section is absent). QA can flip a switch flag on a SIT build without a console change.

**Who / size.** One mobile engineer. S. Class A (non-prod only).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Inside the existing dev-mode screen | One place QA already knows | The screen grows past 1,000 lines; split it into tabs |
| B. A separate hidden route | Small | One more hidden entry point |
| C. Only `--dart-define` forcing (2.21), no screen | No UI code | QA cannot flip at run time |

**Recommended: A**, as a new tab.

## 2d. Dependency-injection seam

### Step 2.15: Composition root and wiring test

**Today.** `main.dart` overrides 2 providers inside `ProviderScope` (`DeviceIntegrityService`, `NetworkConfig`). 4 library files throw `UnimplementedError` when not wired (`device_integrity_service.dart`, `product_config.dart` ×3, `product.dart`, `network_config.dart`). `flutter_riverpod ^2.1.1` in `core`.

**Tasks.** `digital/lib/app/di/app_overrides.dart` and `ports.dart`. Move the overrides without changing them. `test/app/di/wiring_test.dart` reads every provider in `allPorts` from a container built with `appOverrides` and fakes for SDK objects.

**Acceptance criteria.** The wiring test fails if one override is removed. SIT smoke run unchanged. Existing tests pass unchanged.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One `appOverrides()` list, one `allPorts` list, one test | Riverpod's own override mechanism (`overrideWith`). Nothing new | Lists to keep in step, which the test enforces |
| B. `riverpod_generator` with generated providers | Less boilerplate later | Big migration in a "same behaviour" phase. Plan 09 says not now |
| C. A separate DI container (get_it, injectable) | Mirrors Jago | Two DI systems, which is Jago's own debt |

**Recommended: A.**

### Step 2.16: DI rules and `container-lookup` ratchet

**Today.** 2 `ProviderScope.containerOf` uses. No written rule.

**Tasks.** `.claude/rules/ports-and-di.md`, `AGENTS.md` section. Rule `container-lookup` in the checker (baseline 2). Confirm Dart's `implementation_imports` lint is on.

**Acceptance criteria.** The ratchet passes on `master`. A new `containerOf` outside `digital/lib/app/` fails.

**Who / size.** One mobile engineer. XS. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules in `AGENTS.md` + checker rule | Enforced and readable by AI tools | None |
| B. `riverpod_lint` package | Riverpod-specific lints in the IDE | Covers Riverpod misuse, not our port rules |
| C. Review only | No code | Not enforced |

**Recommended: A, and add B as a bonus** if it runs clean on `master`.

## 2e. Build and CI seam

### Step 2.17: Make R8 explicit, fail without `mapping.txt`

**Today.** `build.gradle` release block sets `proguardFiles` but not `minifyEnabled` or `shrinkResources`. R8 runs through Flutter's default. `build-prod.yml` already uploads `mapping.txt` to Datadog and Flutter symbols to Crashlytics. `proguard-rules.pro`: 92 lines, 25 `keep` rules (MediaPipe, protobuf, Insider).

**Tasks.** Add `minifyEnabled true` and `shrinkResources true`. CI step fails if `mapping.txt` is missing. Review keep rules against every SDK that uses reflection (Vida, AppsFlyer, Datadog, Mixpanel + session replay, Firebase, `flutter_inappwebview`, `bfi_document_detection`).

**Acceptance criteria.** Smoke list on a prod-like build: login, OTP, KYC liveness, document capture, loan submission, payment, push, deep link, in-app update. Readable stack traces in Crashlytics and Datadog. APK size within ±1% of the previous release.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Explicit settings + fail-if-missing + keep-rule review | Makes today's behaviour visible and safe | Keep-rule review needs each SDK's docs |
| B. Option A plus `-printusage` and a diff of removed classes per release | Catches an SDK class that R8 stripped | Noisy output to read |
| C. Turn R8 off to "be safe" | No stripping risk | Bigger APK, readable code for attackers. Opposite of plan 01 |

**Recommended: A**, with B's usage report kept as a build artifact for the first 3 releases.

### Step 2.18: Protect-build and register-build slots

**Today.** None. Order today: build → sign → upload.

**Tasks.** Empty named steps "Protect build" (between build and sign) and "Register build" (after upload) in the prod workflow, ready for the RASP vendor (Phase 10).

**Acceptance criteria.** Prod build passes with the empty steps. The steps are in the reusable workflow (2.19), not copied.

**Who / size.** One mobile engineer. XS. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Named no-op steps in the reusable workflow | Vendor drops in later with one change | Two empty steps look odd |
| B. Add them when the vendor is chosen | No work now | The build order (protect before sign) is easy to get wrong under time pressure |
| C. A `workflow_call` hook input for a vendor workflow | Flexible | Over-design for now |

**Recommended: A.**

### Step 2.19: Reusable build workflows and one `--dart-define` file

**Today.** 4 build workflows, 2,990 lines in total, 259 `--dart-define` lines. No `--dart-define-from-file`. `bfi-base-template` has reusable pipelines for 7 stacks but not Flutter. Other BFI Flutter apps: `bravo-agency-app`, RO Tools, SQUARE. GitHub: `workflow_call` jobs must declare their own `environment:`; secrets pass only to the directly called workflow; `secrets: inherit` works inside one org.

**Tasks.** `_build-android.yml` and `_build-ios.yml` as `workflow_call`. Inputs: flavor, tag, distribution, forced switch flags (2.21). `scripts/write-dart-defines.sh` writes `dart_defines.json`; build uses `--dart-define-from-file`. Pin every action to a SHA. Dependabot for `github-actions`.

**Acceptance criteria.** Workflow lines under 1,500. SIT APK size and `flutter --version` in the log unchanged. All 4 flavors build. Secrets never written to a committed file.

**Who / size.** One mobile engineer, SRE reviews. M. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Reusable workflows inside this repo | Fast, owned by the squad | Other Flutter apps copy it by hand |
| B. A `flutter-pr-pipeline` and `flutter-build` in `bfi-base-template`, used by this repo and the other Flutter apps | One place, SRE-owned like the other stacks. Codacy and container scan wiring come for free | Slower: template changes need SRE review. Pin to a commit SHA, never `@master` |
| C. Keep 4 workflows, only move the defines to a file | Small | 2,990 lines stay |

**Recommended: A now, then B** once the shape is stable (two releases). Write A so the files can move to the template unchanged.

### Step 2.25: Android signing with a key in Cloud KMS (proof of concept)

**Today.** `ANDROID_KEYSTORE_BASE64` and its properties are environment secrets, decoded to a file at build time. BFI runs Cloud KMS with an HSM key (`bravo-terraform` `product/kms`). Whether Play App Signing is on is Phase 0 question Q14.

**Tasks.** Proof of concept: import or create the upload key in Cloud KMS (HSM), sign the `.aab` with `jarsigner` through the Cloud KMS PKCS#11 library, CI signs in keyless (WIF). Then switch the prod workflow and delete the keystore secrets.

**Acceptance criteria.** `apksigner verify` passes. Play accepts the bundle on the internal track. The keystore secret is gone from both prod environments. Rollback written down.

**Who / size.** SRE + one mobile engineer. M, after the PoC.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Upload key in Cloud KMS, sign through PKCS#11 | The private key never leaves KMS. Signing is logged in Cloud Audit Logs | JDK PKCS#11 setup on the runner; proof of concept first |
| B. Keep the keystore secret, add Play App Signing if not on (Q14) | Google holds the app signing key; a leaked upload key can be reset | The upload key still sits in CI as a file |
| C. Keystore in Secret Manager or Vault instead of GitHub | Central store, access logs | Still a file that CI reads back |

**Recommended: A, with B's Play App Signing confirmed first.** If the PoC fails, B is the floor.

## 2f. Parity machinery

### Step 2.20: Run a widget test on both paths

**Today.** `digital/test/flutter_test_config.dart` exists (an isolated test binding). No both-paths helper.

**Tasks.** `testWidgetsBothPaths(description, flag: …, body)` runs the body twice, flag off and on, through `FakeFlagStore`. Test names carry `[old]` / `[new]`.

**Acceptance criteria.** A test that fails only on the new path shows one green and one red result.

**Who / size.** One mobile engineer. S. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One helper next to `flutter_test_config.dart`, overrides the flag store | Simple, reads well | Doubles the run time of the tests that use it |
| B. A `group` per path with shared setup | No helper | Boilerplate in every test |
| C. Run the whole suite twice in CI with the flag forced | No test changes | Doubles all test time, including tests with no flag |

**Recommended: A.**

### Step 2.21: Force a switch flag in SIT and UAT builds

**Today.** None. Prod reads only Remote Config.

**Tasks.** A `--dart-define=FORCE_FLAGS=…` read at start-up in non-prod flavors only. e2e specs tag the flag value in their report. The reusable workflow (2.19) takes it as an input.

**Acceptance criteria.** The 4 journeys pass on a SIT build with the flag forced off and on a SIT build with it forced on. A prod build ignores the define (test: the prod flavor's `AppConfig` has no such field).

**Who / size.** One mobile engineer + QA. S. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Build-time define, non-prod only | Deterministic per build. Prod cannot be affected | Two SIT builds per release candidate |
| B. Remote Config conditions per tester | No build change | Flaky in e2e; prod and SIT share the console |
| C. Deep link that sets the override | One build serves both | A hidden entry point; must be stripped from prod |

**Recommended: A.**

### Step 2.22: e2e twice per release candidate

**Today.** The suite is not yet triggered from app CI (Phase 1 step 1.14 does that).

**Tasks.** For each release candidate, build two SIT apps from the same commit: all switch flags off, all on. Trigger the `automation-monorepo` suite once per build. Both results linked in the release notes. One run when no switch flag exists.

**Acceptance criteria.** A candidate where the new path breaks a journey shows one green and one red run, and `build-prod.yml` does not start. Starts as a checklist item, becomes a gate after 2 releases.

**Who / size.** QA + one mobile engineer. S. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Two builds, two runs, hard gate later | Clear evidence per path | Doubles device time per candidate |
| B. One build, specs flip the flag through the override screen | One build | Specs become stateful; a crash leaves the flag set |
| C. Run only the new path | Half the time | No proof the old path still works |

**Recommended: A.**

### Step 2.23: Cohort dashboard by flag value

**Today.** Release dashboards exist in Datadog (per version). No split by flag. With 2.8, RUM Feature Flag Tracking gives the split for free.

**Tasks.** A dashboard: crash-free sessions, error rate, p75 screen load, memory, by flag value for the same app version. Funnel of the switched journey in Firebase or Mixpanel, by flag value. Thresholds from Phase 1 (1.4), widgets turn red.

**Acceptance criteria.** A test flag on SIT shows both cohorts. A breached threshold turns its widget red. Thresholds are written on the dashboard.

**Who / size.** One mobile engineer + SRE. S. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Datadog Feature Flag Tracking views + the release dashboard with a flag template variable | Built-in, no custom facets | Funnels still live in Firebase or Mixpanel |
| B. Custom facets on a RUM attribute | Works without Feature Flag Tracking | More setup, same result |
| C. Firebase A/B Testing as the only view | Has funnels | Not where SRE and on-call look |

**Recommended: A**, with the funnel view linked from the dashboard.

### Step 2.24: Kill-switch runbook and SIT rehearsal

**Today.** None.

**Tasks.** `docs/runbooks/kill-switch.md`: who flips (flag owner, or mobile on-call), when (threshold breached or P1 pointing at the new path), how fast (15 minutes from alert to flag change), what after (pause Play rollout if the build is suspected, incident note, ledger entry). Rehearse once in SIT per new switch flag.

**Acceptance criteria.** One rehearsal recorded with the time from alert to flip. The on-call rota names who can flip.

**Who / size.** Squad lead + on-call. S. Class A.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Runbook in the repo + rehearsal | Next to the flags; rehearsed, not only written | Needs console rights for on-call |
| B. Runbook as a Confluence page only | Visible to product | Drifts from the code |
| C. Automatic flip from a Datadog monitor | Fastest | A noisy monitor can flip a good release; keep humans in the loop first |

**Recommended: A.** Revisit C after 3 clean rollouts.

## Exit gate for Phase 2

* One prod release that contains all Phase 2 code reached 100% through the staged rollout with no regression on the release health dashboard.
* Golden names file, golden screenshots, fixtures and the e2e journeys unchanged across that release.
* The kill-switch runbook was rehearsed once in SIT with a test switch flag.
* The ratchets from 2.3, 2.9 and 2.16 run in CI with their baselines recorded.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who owns the analytics event catalogue on the product side (for 2.11 and later 5.6)? | Product analytics | |
| Q2 | How many Remote Config keys are live in the console today, and who owns each? | Product + mobile squad | |
| Q3 | Is the Datadog plan's RUM Feature Flag Tracking enabled for the BFI Mobile Prod app, or does it need a setting? | SRE | |
| Q4 | Do Vida, `bfi_document_detection` and the image-validation SDK ship their own R8 keep rules? | Mobile squad (ask vendors) | |
| Q5 | Should the Flutter reusable workflows live in `bfi-base-template` from the start (2.19 option B)? | SRE | |
| Q6 | Who can rehearse the kill switch in SIT, and does the on-call have Remote Config console rights? | Squad lead | |
| Q7 | Is Play App Signing on (Phase 0 Q14)? Decides the shape of 2.25 | Release manager | |
| Q8 | Epic for Phase 2: one epic with 25 tickets, or one per seam (2a–2f)? | Samuel | |

## Evidence

| Fact | How it was checked (20 Oct 2026) |
| --- | --- |
| Overrides and ports | `digital/lib/main.dart` `ProviderScope.overrides`; `grep UnimplementedError` in `lib/` |
| `DatadogLog` shape | `shared_lib/core/lib/src/utils/datadog_log.dart`; 61 call sites by `grep` |
| Analytics shape | `digital/lib/app/analytics.dart`, `app/tracker/*`, `app/insider`, `app/appsflyer`; 204 `logEvent(` in 87 files |
| Remote Config | `digital/lib/app/remote_config/remote_config_repository.dart` lines 14–34 and 200–215; `wc -l` on the generated files |
| R8 and symbols | `digital/android/app/build.gradle` release block; `proguard-rules.pro`; `build-prod.yml` lines 172–214 |
| Workflow size | `cat .github/workflows/*.y*ml \| wc -l` = 2,990; `--dart-define` lines per workflow |
| SDK versions | `digital/pubspec.yaml`, `shared_lib/core/pubspec.yaml` |
| Base template stacks | `bfi-finance/bfi-base-template/.github/workflows` listing |

## Sources for the recommendations

* Datadog, [Feature Flag Tracking setup (Flutter)](https://docs.datadoghq.com/real_user_monitoring/feature_flag_tracking/setup/?tab=flutter): `addFeatureFlagEvaluation(key, value)`, plugin ≥ 1.3.2, unsupported characters in flag names.
* Datadog, [Flutter advanced configuration](https://docs.datadoghq.com/real_user_monitoring/mobile_and_tv_monitoring/flutter/advanced_configuration): RUM `addAttribute`, global attributes for logs.
* Firebase, [Remote Config loading strategies](https://firebase.google.com/docs/remote-config/loading) and [Flutter get started](https://firebase.google.com/docs/remote-config/flutter/get-started): real-time updates bypass the fetch interval; avoid activating at once on sensitive UI; 12 h default interval.
* Firebase, [Crashlytics custom keys (Flutter)](https://firebase.google.com/docs/crashlytics/flutter/customize-crash-reports): 64 keys, 1,024 characters.
* Riverpod, [Provider overrides](https://riverpod.dev/docs/concepts2/overrides) and [Testing](https://riverpod.dev/docs/essentials/testing): `overrideWith`, one container per test.
* GitHub, [Reusing workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows): secrets reach only the directly called workflow, `secrets: inherit` in one org, `environment` in the called job.
* GitHub, [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): pin to a commit SHA, treat reusable workflows like third-party actions.
* Google Cloud, [Cloud KMS PKCS #11 library](https://docs.cloud.google.com/kms/docs/reference/pkcs11-library).
