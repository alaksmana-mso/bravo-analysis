## Summary

Phase 2 of the agency apps roadmap ("Seams with the same behaviour") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 16 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Seams, Same Behaviour".
* **Plan pages:** GENFI plan 03 steps 2 and 4; GENFI plan 11 step 2; GENFI plan 10 steps 1, 2, 4; GENFI plan 13 steps 1–2; GENFI plan 05 step 2; GENFI plan 02 step 6; GENFI plan 01 step 3; GENFI plan 06 step 3; GENFI plan 12 step 2 (and the SQUARE twins).
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 2 is.** Every step puts a new interface ("port") behind code that already works, in a shared package, and wires it in each app's `main.dart`. Agents and staff see and send the same things. The rule for every class B step: the old public call stays, only its body changes, and existing tests keep passing without edits.

**One package, three wirings.** Each shared package (observability, analytics, feature flags, the interceptor chain) is built once and wired three times (`agent_tools`, `are_tracker`, `mybispro`). The app wiring is one row per app, released on each app's own train.

### Five facts that shape Phase 2

**1. Logging is broken in different ways per app.** GENFI's `DatadogLog.e` creates a logger and never writes to it (fixed in Phase 1, 1.G1). SQUARE's `Log.e` logs at debug level under a warning threshold, so nothing reaches Datadog (1.S1). MyShaf has Crashlytics gated off. MY BISPRO does not use `crash_reporting`. `shared_lib/crash_reporting` wraps Crashlytics only (344 lines, 1 unverified test). There is no sanitiser anywhere.

**2. Analytics is small.** GENFI: a wrapper with 5 enum events and 4 call sites, no Datadog fan-out. SQUARE: 27 `logEvent` calls with string names, 8 built at run time, fired from `initState`, with the employee NIK as the Firebase user id (an approved delta in Phase 3). The seam is cheap here; the migration (Phase 5) is small.

**3. Flags are three models and some dart-defines.** GENFI: `ConventFeatureFlag` (20 keys) plus a Sharia model (10 keys) and a static Notifier instance; a raw `getBool` in `main.dart`. SQUARE: a typed `freezed` `RemoteConfig` with 23 fields, hand-mapped in a 140-line repository with no defaults. Six `bool.fromEnvironment` compile-time flags across the apps (`FEATURE_JAILBREAK_DETECTION`, `FEATURE_ENABLE_PROXY`, `FEATURE_FLAG_NEW_*`). No `SwitchFlag` kind, no owner or removal date.

**4. DI is already Riverpod; the gap is ports.** `agent_tools/main.dart` overrides five `HttpClient` variants, `NetworkConfig`, the remote-config Notifier instance and `CrashReporter.instance` (a static replaced at line 32). `are_tracker/main.dart` overrides nine providers (lines 211–238). `shared_data` repositories are concrete classes with a static provider, so nothing below the `HttpClient` can be faked. Static singletons: `CrashReporter.instance`, `NavigationService.instance`, `AliceInspector`.

**5. R8 is on but not explicit, and GENFI has no keep rules.** Flutter's Gradle plugin shrinks release builds by default. `agent_tools` has no `proguard-rules.pro`; SDKs that use reflection (Firebase, Datadog, Alice, ML Kit, Maps, `flutter_inappwebview`) rely on their own bundled rules. Debug builds use the release signing config. A stray `android/app/build.gradle.kts` template sits in `agent_tools`.

Other counts: `http_client.dart` 395 lines, one interceptor (pinning), response-type bug at lines 320–332; 31 workflows, 5,582 lines; raw styling `TextStyle(` 17 and `Colors.` 92 in GENFI, `TextStyle(` 46, `Colors.` 20, `TextButton` 10 in SQUARE; `AGENTS.md`, `.claude/rules` and `CODEOWNERS` absent (`copilot-instructions.md` exists).

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **B** unless marked. "App" = where the change lands.

| # | Proposed ticket title | Today (24 Oct) | App | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.1 | `feat(observability): shared_lib/observability with AppLogger, sinks, FakeLogger` | `crash_reporting` wraps Crashlytics only | shared | Agency engineer | M | 1.G1, 1.S1 | | |
| 2.2 | `refactor: Wire the observability sinks` (one PR per app; `DatadogLog` and `Log` become shims) | Per-app loggers | GENFI, SQUARE, MY BISPRO | Agency engineer | S each | 2.1 | | |
| 2.3 | `feat(analytics): shared_lib/analytics port, FakeAnalytics, denylist type` | GENFI enum wrapper, SQUARE strings | shared | Agency engineer | S | 1.G2, 1.S2 | | |
| 2.4 | `refactor(analytics): Firebase and Datadog RUM adapters, old calls as shims, router observer` (per app) | No fan-out | GENFI, SQUARE | Agency engineer | S each | 2.3 | | |
| 2.5 | `ci: Ratchet direct analytics, log and SDK calls outside adapters` | No ratchet | shared | Agency engineer | XS | 1.10 | | |
| 2.6 | `feat(flags): shared_lib/feature_flags with FeatureFlag<T>, platforms, FakeFlags, generator` | 3 models | shared | Agency engineer | M | – | | |
| 2.7 | `feat(flags): Catalogues` (GENFI 20 + 10 keys, SQUARE 23 fields) `and SwitchFlag kind` | Hand-mapped | GENFI, SQUARE | Agency engineer | S each | 2.6 | | |
| 2.8 | `refactor(flags): Build today's models from the flag store; old call sites unchanged` | Direct `getBool` | GENFI, SQUARE | Agency engineer | S each | 2.7 | | |
| 2.9 | `refactor(di): Composition root per app, wiring test` | Overrides inline in `main.dart` | GENFI, SQUARE, MY BISPRO | Agency engineer | S each | – | | |
| 2.10 | `refactor(di): Static singletons become providers` | `CrashReporter.instance`, remote-config instance, `AliceInspector`, `NavigationService.instance` | shared + apps | Agency engineer | S | 2.9 | | |
| 2.11 | `feat(network): Interceptor chain in core (not wired yet)` | Six decorators | shared | Agency engineer | M | 1.12 | | |
| 2.12 | `ci: Reusable workflows (checks, build-android, build-ios, distribute) + protect slot` | 31 files, 5,582 lines | shared | Agency engineer + SRE | M | Phase 0 | | |
| 2.13 | `build(android): R8 explicit, keep rules reviewed, fail without mapping.txt, debug signing for debug` | Implicit R8, no keep rules in GENFI | GENFI, SQUARE, MY BISPRO | Agency engineer | S | 1.4 | | |
| 2.14 | `chore: AGENTS.md, .claude/rules, review skill` | `copilot-instructions.md` only | shared | Agency engineer | S | 1.10 | | |
| 2.15 | `ci(design): Raw-styling ratchet (TextStyle, Colors., TextButton)` | 17 / 92 (GENFI), 46 / 20 / 10 (SQUARE) | shared | Agency engineer | XS | 1.10 | | |
| 2.16 | Switch-flag state reported to RUM and Crashlytics; both-paths test helper; cohort dashboard; kill-switch runbook rehearsed | None | shared + apps | Agency engineer + on-call | M | 2.7, 1.14 | | |

**Suggested order.** Sprint 1: 2.9, 2.10, 2.1, 2.6, 2.13. Sprint 2: 2.2, 2.3, 2.4, 2.7, 2.8, 2.5. Sprint 3: 2.11, 2.12, 2.14, 2.15, 2.16. Each app's wiring rows ship in that app's next release.

## Definition of ready for every Phase 2 ticket

* Class B: "existing tests pass unchanged" is an acceptance criterion.
* The ticket names the app or package, and for an app wiring row, the release it rides in.
* No step changes an event name, a flag default, a log destination or a user-facing string. If it must, it moves to Phase 3.

## Step 2.1: Observability package

**Today.** See fact 1. `TrackingConsent.granted` is hard-coded in all three `main.dart` files (consent itself is Phase 3).

**Tasks.** `shared_lib/observability` with `AppLogger`, `LogSink`, `LogEvent`, `ObservabilityUser`, `FakeLogger`, and a sanitiser type (rules land in Phase 3). Move `shared_lib/crash_reporting` in as the Crashlytics sink; add a Datadog logs sink. Keep `CrashReporter` as a thin shim for one release. Pure Dart apart from the adapters.

**Acceptance criteria.** 100% unit coverage of the fan-out; `melos analyze` passes; no app changed yet.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One shared package, two sinks, shims | One logger for four apps | `crash_reporting`'s one test must be rewritten |
| B. Per-app loggers improved in place | No package | Three copies of the same fix |
| C. Datadog SDK directly everywhere | No port | Opposite of the goal |

**Recommended: A.**

## Step 2.2: Wire the sinks per app

**Today.** `agent_tools/lib/app/utils/datadog_log.dart`, `are_tracker/lib/app/crash_reporter.dart`, `mybispro/lib/app/utils/datadog_log.dart`.

**Tasks.** Each `main.dart` registers the sinks; `DatadogLog` and `Log` become shims; the provider observer uses `AppLogger`. MyShaf: enable Crashlytics or record why not (1.G1). MY BISPRO: first time it gets crash reporting (an approved delta for that app, note it).

**Acceptance criteria.** `grep DatadogSdk.instance.logs` outside the package returns 0. Datadog log volume per app within ±10% of the week before (GENFI, after 1.G1 made logging work).

**Who / size.** One Agency engineer. S per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One PR per app, shims kept one release | Each app's release is watched on its own | Three PRs |
| B. One PR for all three | Fewer PRs | Three apps' behaviour in one review |
| C. GENFI only, others later | Smallest | SQUARE and MY BISPRO stay without a sanitiser path |

**Recommended: A.**

## Step 2.3: Analytics port

**Today.** See fact 2. Golden names files exist after Phase 1 (1.G2, 1.S2).

**Tasks.** `shared_lib/analytics` with the port, event base class, context, `FakeAnalytics`, the PII denylist type. Pure Dart, unit-tested.

**Acceptance criteria.** No Flutter or vendor import. 100% unit-tested.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One shared port for the agency apps, same shape as the BFI app's | One pattern across BFI | Keep the two packages in step by convention |
| B. Reuse the BFI app's package as a git dependency | One package | Cross-repo dependency on a package that is still changing |
| C. Per-app wrappers | No shared code | SQUARE and GENFI diverge again |

**Recommended: A**, with B revisited once both packages are stable.

## Step 2.4: Adapters per app

**Today.** GENFI: `ConventAnalyticsService`; SQUARE: `analytics.dart` with `logEvent`.

**Tasks.** `FirebaseAdapter` and `DatadogRumAdapter` in each app's `lib/app/analytics/adapters/`. Move the service logic into the Firebase adapter; keep the old call as a shim. One router observer sends `screen()` to all adapters and to crash breadcrumbs.

**Acceptance criteria.** Golden names file unchanged. Firebase DebugView on dev shows the same names for a 10-minute smoke run. (Datadog RUM actions are new data and wait for Phase 3 sign-off; the adapter can exist without sending.)

**Who / size.** One Agency engineer. S per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Shims first, adapters behind them | Zero call-site diff; parity easy | Two ways to call analytics until Phase 5 |
| B. Adapters plus a mass replace | One PR | Hard to prove parity, especially SQUARE's 8 run-time names |
| C. Only new code uses the port | Smallest | The old path never shrinks |

**Recommended: A.**

## Step 2.5: Ratchet direct calls

**Today.** No rule.

**Tasks.** Rules in `tool/arch_check.dart`: `analytics-direct-call`, `log-direct-call` (`DatadogSdk.instance.logs`, `FirebaseCrashlytics.instance` outside adapters), `sdk-outside-adapters`. Baseline on merge day.

**Acceptance criteria.** A new direct call fails CI.

**Who / size.** One Agency engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rules in the existing checker | One tool | None |
| B. Separate scripts | Independent | More to maintain |
| C. Review only | No code | Not enforced |

**Recommended: A.**

## Step 2.6: Feature-flag package

**Today.** See fact 3.

**Tasks.** `shared_lib/feature_flags` with `FeatureFlag<T>`, `FeatureFlagPlatform`, `RemoteConfigPlatform`, `FakeFlags`, and a generator that builds `setDefaults` and the key map from the catalogue. Wrap today's Firebase fetch logic unchanged.

**Acceptance criteria.** Unit tests cover defaults, type mismatches and unknown keys. No app changed yet.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own typed port with a generator | Fits three apps; generated key map stops typos | We maintain it |
| B. Same as the BFI app's `shared_lib/flags` as a git dependency | One package | Cross-repo coupling |
| C. A flag vendor | Richer targeting | New cost in a "same behaviour" phase |

**Recommended: A.**

## Step 2.7: Catalogues and the `SwitchFlag` kind

**Today.** GENFI 20 + 10 keys, a static Notifier instance, a raw `getBool` in `main.dart`; SQUARE 23 fields, hand-mapped, no defaults.

**Tasks.** One catalogue per app, flavour-scoped where needed; every flag gets an owner, a description and a removal date; tunables marked as config. `SwitchFlag`: owner and `removeBy` required, default old path, real-time, read at journey start; CI fails on an overdue one. Keep today's keys so Remote Config needs no change.

**Acceptance criteria.** A test compares each catalogue with today's model and defaults. A `SwitchFlag` without `removeBy` fails CI.

**Who / size.** One Agency engineer. S per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Hand-written catalogues, generator keeps the key map honest | Readable, typo-proof | One-time typing |
| B. Generate catalogues from the console export | Exact keys | Owners and dates still need editing |
| C. Keep the models, add owners as comments | No new structure | No typed flags, no switch flags |

**Recommended: A.**

## Step 2.8: Bridge today's models

**Today.** Call sites read `ConventFeatureFlag`, the Sharia model and SQUARE's `RemoteConfig` directly.

**Tasks.** Build each model from the flag store. Replace the static Notifier instance with the provider. Old call sites keep working until Phase 5.

**Acceptance criteria.** Existing remote-config tests pass unchanged. Widget tests that read a flag give the same result through both reads.

**Who / size.** One Agency engineer. S per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Bridge now, delete the models in Phase 5 | No call-site change | Two reads of one key for a while |
| B. Delete the models now | Done in one go | Big PR, not class B |
| C. New flags only in the store | Smallest | Two sources of truth with no end |

**Recommended: A.**

## Step 2.9: Composition root per app and wiring test

**Today.** See fact 4.

**Tasks.** `lib/app/di/app_overrides.dart` per app with one function per concern (network, analytics, logging, flags); `main.dart` calls it. `test/helpers/test_overrides.dart`. A wiring test builds a `ProviderContainer` with the overrides and reads every port.

**Acceptance criteria.** `main.dart` under 100 lines. The wiring test fails if one override is removed. SIT smoke unchanged.

**Who / size.** One Agency engineer. S per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One override list per app, one test | Riverpod's own mechanism | Lists to keep in step, which the test enforces |
| B. `riverpod_generator` | Less boilerplate later | Big migration here |
| C. A second DI container | Mirrors Jago | Jago's own debt |

**Recommended: A.**

## Step 2.10: Static singletons become providers

**Today.** `CrashReporter.instance`, the remote-config Notifier instance (GENFI), `AliceInspector`, `NavigationService.instance` (SQUARE 5, GENFI 4).

**Tasks.** Each becomes a provider in the root. Alice moves to `dev_dependencies` behind a compile-time flag (plan 05 step 6).

**Acceptance criteria.** `grep ".instance ="` in `lib` returns 0. Release builds do not contain Alice.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Providers now | Every dependency fakeable | Some call sites change signature |
| B. Keep statics, wrap in providers that return them | Smaller | Still a global behind the provider |
| C. Leave | None | Tests cannot fake them |

**Recommended: A.**

## Step 2.11: Interceptor chain in core, not wired

**Today.** `http_client.dart` 395 lines; the only interceptor is pinning; the response-type bug; six decorators outside.

**Tasks.** `AuthStrategy`, `TokenStore` and six interceptors (headers, auth, single-flight refresh, retry, trace id, error mapping) in `shared_lib/core`, with tests (1.12 is the oracle). Fix the response-type bug. Pinning interceptor stops forwarding `Authorization` (done in 0.5) and pins the download host too. **Not wired into any app** in this phase; Phase 4 does that behind `useInterceptorClient`.

**Acceptance criteria.** Core tests cover request building, single-flight refresh, 401 retry, error mapping and pinning. No app behaviour changes (nothing is wired).

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Build and test the chain now, wire in Phase 4 | The risky wiring is separate from the build | Dead code for a sprint |
| B. Build and wire in one go | Faster | Two risks in one release |
| C. Fix the decorators in place | No chain | Six copies to fix |

**Recommended: A.**

## Step 2.12: Reusable workflows

**Today.** 31 workflows, 5,582 lines; `bfi-base-template` has no Flutter pipeline.

**Tasks.** `checks.yml`, `build-android.yml`, `build-ios.yml`, `distribute.yml` as `workflow_call` with inputs app, flavour, environment, forced switch flags. Per-app workflows become 20-line callers. The protect-and-register slot (no-op). Consider moving them to `bfi-base-template` later, for the BFI app too.

**Acceptance criteria.** Workflow file count below 15. SIT APK sizes unchanged. One toolchain change touches one file.

**Who / size.** One Agency engineer, SRE reviews. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Reusable workflows in this repo | Owned by the squad; fast | The BFI app copies it by hand |
| B. A Flutter pipeline in `bfi-base-template` from the start | One place for all Flutter apps | Slower; template changes need SRE review; pin by SHA |
| C. Keep 31 files, dedupe only the defines | Small | 5,582 lines stay |

**Recommended: A now, B once stable** (two releases), together with the BFI app.

## Step 2.13: R8 explicit, keep rules, debug signing

**Today.** See fact 5.

**Tasks.** `minifyEnabled true`, `shrinkResources true` in each app's release block. `proguard-rules.pro` for `agent_tools` reviewed against Firebase, Datadog, Alice, ML Kit, Maps, `flutter_inappwebview`. Fail the prod build without `mapping.txt` (1.4). Debug builds get the debug signing config. Delete the stray `build.gradle.kts`.

**Acceptance criteria.** Smoke list on a prod-like build per app: login, OTP, registration with OCR and selfie, prospect input, calculator, reserve lead (GENFI); SSO login, lead input, company submission (SQUARE). Readable stack traces. APK size within ±1%.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Explicit settings + reviewed keep rules + fail-if-missing | Today's behaviour made visible and safe | Keep-rule review needs each SDK's docs |
| B. Option A plus `-printusage` per release | Catches a stripped SDK class | Noisy |
| C. Turn R8 off | No stripping risk | Bigger APK, readable code |

**Recommended: A**, with B's report kept for the first 3 releases.

## Step 2.14: AI rules and review skill

**Today.** `.github/copilot-instructions.md` exists; no `AGENTS.md`, `.claude/rules`, or review skill. Copilot code review is on.

**Tasks.** `AGENTS.md` as the entry point; `.claude/rules/` with `layer-model.md`, `riverpod-conventions.md`, `analytics.md`, `ratchet.md`, `testing.md`; a `mr-review` skill that checks a diff against the rules; a sync workflow like the BFI app's.

**Acceptance criteria.** The skill finds real issues on 3 recent merged PRs with few false alarms. `copilot-instructions.md` is generated from `AGENTS.md`.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same files and sync as the BFI app | One convention across BFI | Rules must be short to be read |
| B. `copilot-instructions.md` only | Already there | Claude and Codex users miss it |
| C. None | No work | Rules stay in heads |

**Recommended: A.**

## Step 2.15: Raw-styling ratchet

**Today.** GENFI `TextStyle(` 17, `Colors.` 92; SQUARE `TextStyle(` 46, `Colors.` 20, `TextButton(` 10. Four design systems in play (`ui_theme`, `ds_1`, `ds_2`, `ds_3`).

**Tasks.** Rule `no-raw-style` with baselines per app in the checker. Migrate as screens are touched.

**Acceptance criteria.** Baselines only go down. A PR with a new raw colour fails.

**Who / size.** One Agency engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ratchet in the checker | Stops growth now | Old literals stay until touched |
| B. A lint rule | IDE feedback | No baseline |
| C. Fix all now | Clean | A design pass across two apps |

**Recommended: A.**

## Step 2.16: Parity machinery

**Today.** None. The Datadog Flutter plugin has Feature Flag Tracking (`addFeatureFlagEvaluation`).

**Tasks.** Report each switch flag's value to RUM and as a Crashlytics key through the observability port. A `testWidgetsBothPaths` helper. A `--dart-define=FORCE_FLAGS` read in non-prod flavours only. Cohort dashboard by flag value per app. Kill-switch runbook rehearsed once in SIT per app.

**Acceptance criteria.** A test flag in SIT shows both cohorts on the dashboard. A test that fails only on the new path shows one green and one red. The rehearsal is recorded with its time from alert to flip.

**Who / size.** One Agency engineer + on-call. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Datadog Feature Flag Tracking + Crashlytics key + helper + runbook | Built-in UI splits errors by flag value | SQUARE needs RUM processing (Phase 1 Q4) |
| B. Custom RUM attribute | Works without the feature | Reinvents the SDK |
| C. Firebase user properties only | Already there | Not where SRE looks |

**Recommended: A.**

## Exit gate for Phase 2

* One release per app that holds all Phase 2 wiring reached 100% with no regression and golden files unchanged.
* The shared packages (observability, analytics, feature flags, interceptor chain) exist with tests; the chain is not yet wired.
* Each app has a composition root and a wiring test; no static singletons.
* R8 explicit with reviewed keep rules in every app; the kill-switch runbook rehearsed once per app.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who owns each shared package (`observability`, `analytics`, `feature_flags`, `core` chain)? | Agency tech lead | |
| Q2 | MyShaf: enable Crashlytics, or record why not? | Sharia squad | |
| Q3 | MY BISPRO: does it get the full wiring in Phase 2, or only logging? | Sharia squad | |
| Q4 | Do the vendor SDKs in `agent_tools` ship their own R8 keep rules? (ML Kit, Maps, Alice) | Agency squad | |
| Q5 | Move the reusable Flutter workflows to `bfi-base-template` now or later? | SRE | |
| Q6 | Epic: one for the monorepo, with sub-tickets per app for the wiring rows? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Logging per app | plan 03 "today" (GENFI and SQUARE); `grep TrackingConsent` in the three `main.dart` files |
| Analytics counts | `grep -c "logEvent("`: SQUARE 27, GENFI 6 (4 call sites + wrapper) |
| Flags | plan 10 and 11 "today"; `grep -c bool.fromEnvironment` = 6 |
| DI | `are_tracker/lib/main.dart` lines 211–238; plan 13 "today" |
| R8 and keep rules | plan 01 step 3; `agent_tools/android/app` has no `proguard-rules.pro` |
| Raw styling | plan 12 step 2 baselines |

## Sources for the recommendations

* BFI Phase 2 refinement notes (same seams, sources and tools).
* Datadog, [Feature Flag Tracking setup (Flutter)](https://docs.datadoghq.com/real_user_monitoring/feature_flag_tracking/setup/?tab=flutter); [`DatadogLoggingConfiguration.eventMapper`](https://pub.dev/documentation/datadog_flutter_plugin/latest/datadog_flutter_plugin/DatadogLoggingConfiguration-class.html).
* Riverpod, [Provider overrides](https://riverpod.dev/docs/concepts2/overrides).
* GitHub, [Reusing workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).
