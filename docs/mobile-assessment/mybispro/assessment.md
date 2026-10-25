## Summary

MY BISPRO (`mybispro/` in `bravo-agency-app`) is the smallest of the four agency apps: 50,880 hand-written Dart lines in 247 files, 16 feature folders, for Sharia credit-marketing staff. It shares the monorepo, the CI setup and seven shared packages with GENFI, SQUARE and MyShaf. The shared findings on Genfi mobile app assessment and Square mobile app assessment apply here. This page lists what MY BISPRO adds, compared with the DK Jago app in the same way.

* **Every pipeline is red.** The last five runs of the trunk, SIT and prod workflows all failed. The prod pipeline last ran on 19 Jun 2026 and failed on the Datadog symbol upload before the Play upload step. The UAT workflow has never run. No tag since `v1.8.0-rc.4-mybispro` (19 Jun 2026). One commit touched `mybispro/` in the last 90 days.
* **Errors go nowhere.** `DatadogLog.e` creates a Datadog logger named after the error and never writes to it. 108 call sites and the Riverpod provider observer send nothing. There is no Crashlytics, no analytics event, no user id. Datadog RUM is configured in code, but no RUM application exists for MY BISPRO and no session was recorded in the last 30 days. The app is unmonitored.
* **A config name mismatch keeps root detection always on.** CI passes `FEATURE_ENABLE_JAILBREAK_DETECTION`, the code reads `FEATURE_JAILBREAK_DETECTION` with default `true`. It cannot be switched off from CI.
* **Certificate pinning only in prod.** DEV, SIT and UAT builds do not receive `SHA_256_FINGERPRINT`. The debug build type signs with the release keystore.
* **Prod environment has no protection rule (verified).** All four `sharia_*_mybispro` environments return zero rules from the API. The only gate is the manual-approval action, 2 of 9 named people.
* **Architecture is the same gap as GENFI, smaller.** No domain layer. 49 of 68 screens import `shared_data` packages directly. 61 `StateNotifier` controllers, 70 `static final` providers. Eight two-way feature import pairs, `common` imports `loansimulation`, and `main.dart` → `app.dart` → `app_controller.dart` → `main.dart` is an import cycle.
* **Tests are widget tests only.** 57 files, 223 `testWidgets`, 0 `test(`, 0 controller tests, 0 goldens, no coverage threshold. Controllers are mocked in the widget tests, so the rules in them are untested.
* **A placeholder reaches production.** The credit-analyst note in the edit-loan form is the l10n string `dummyCreditAnalystNote`.
* **Decision already made for the monorepo:** keep Riverpod, copy Jago's layers, ports and wrapper, not its bloc library.

**Overall shape today**

## Scope and evidence

| **Item** | **MY BISPRO** | **Jago (reference)** |
| --- | --- | --- |
| Repository | [bfi-finance/bravo-agency-app](https://github.com/bfi-finance/bravo-agency-app), folder `mybispro` | DK GitLab digital\_banking\_app + prod-pipelines/jago-mobile |
| Revision read | master @ 1e50b819 (22 Oct 2026) | Local working copy, Oct 2026 |
| Store | `id.co.bfi.sharia.mybispro`; iOS id6469687433 v1.8.0 (19 Jun 2026); Android present. Last tag `v1.8.0-rc.4-mybispro` (19 Jun 2026), 418 tags in total | n/a |
| Audience | Sharia credit-marketing staff (BFI employees with the CMS role, per the README) | Retail banking customers |
| Stack | Flutter 3.35.0 in CI, Dart >=3.9, Riverpod 2.6 (StateNotifier, via `core`), dio 5.9, go\_router 14.8, freezed 2.5, firebase\_core 4.1, firebase\_remote\_config 6.0, firebase\_messaging 16.0, datadog\_flutter\_plugin 2.13 | Flutter 3.38.8, Dart 3.10, bloc, injectable + Kiwi |
| Size | 247 hand-written Dart files, 50,880 lines; 76 generated files, 24,901 lines; 7,813 lines of generated l10n; 16 feature folders; 68 screens | About 5,288 test files alone |
| Shared packages used | `agency`, `agent_marketing`, `core`, `keycloak`, `onboarding`, `ui_theme`, `user_iam` | 49 module packages |
| Datadog RUM | Configured in `main.dart` from dart-defines. No RUM application named for MY BISPRO exists in Datadog (us5), and no session was found in the last 30 days | n/a |
| GitHub environments | `sharia_dev_mybispro`, `sharia_sit_mybispro`, `sharia_uat_mybispro`, `sharia_prod_mybispro`, all with 0 protection rules (API, 26 Oct 2026) | Separate prod pipeline repo |
| Assessed on | 26 Oct 2026 | 9 Oct 2026 |

All findings come from reading source and CI files at the revision above, the GitHub REST API (environments, workflow runs, job and step conclusions, no logs) and Datadog RUM. Nothing was built or run. Counts come from grep over `mybispro/lib` without generated files. The full fact sheet with the grep for every number is in `bravo-analysis/docs/mobile-assessment/mybispro/facts.md`.

## Side-by-side comparison

Effort: S = up to 1 sprint, M = 2–4 sprints, L = more than a quarter. Rows marked (shared) are the same finding as on the GENFI and SQUARE pages and get fixed once for the monorepo.

| **Area** | **Jago** | **MY BISPRO today** | **Gap** | **Effort** |
| --- | --- | --- | --- | --- |
| Repo layout | Melos workspace, feature and shared packages, thin `*_api` contracts. | One package with 16 feature folders under `lib/features`. 399 package imports between features, 8 two-way pairs (`agent ↔ inputprospect`, `common ↔ loansimulation`, `mkyc ↔ prospectlist` and five more). `common` is not a leaf. `lib/app` imports features in 12 places. (shared) The melos `mybispro` category and the PR path filter list `shared_data/document` and `sso`, which the app does not depend on. | Feature boundaries exist only by folder. Fix the category and filter now (S); feature packages come with the shared repo-layout plan. | S now, L with the shared plan |
| Layering | data → domain ← presentation. Domain is pure Dart. | Screen → controller (StateNotifier) → shared\_data repository → HttpClient. No `domain` folder anywhere. 47 files read a repository provider directly (87 call sites). 49 of 68 screens import a `shared_data` package. The shared\_data models are already mapped from the network DTOs, which is a good base. | Rules sit in controllers and 1,200-line screens. | L |
| State management | bloc with rules. | Riverpod 2.6 StateNotifier: 61 controllers, 70 `static final` providers, 1 global `StateProvider`, `NavigationService.instance` singleton. `ref.watch` on `onPressed` lines: 4. `AppController.onAppLoaded()` is called from `App.build` on every build and again from `AppScreen.initState`. | Keep Riverpod. Move to Notifier. Remove the double `onAppLoaded`. | M |
| Dependency injection | injectable + get\_it, wiring only in the app layer. | `ProviderScope` with 4 overrides in `main.dart`. The auth client is chosen at start-up by the Remote Config flag `FEATURE_KEYCLOAK_MANAGE_TOKEN` and swapped at runtime with `container.updateOverrides` when the flag changes, after logging the user out of the other Keycloak repository. No interfaces: repositories are concrete, the only abstraction is `core.HttpClient`. | Riverpod is fine as DI. Ports are missing. The runtime swap is an escape hatch that should go when the network chain lands. | M (with layering) |
| Analytics wrapper | `AnalyticsPlatform` interface, fan-out to Datadog, Firebase, CleverTap, typed events. | None. No `firebase_analytics`, no event call, no user id, no custom RUM action. Views would come from the `DatadogNavigationObserver` on the `GoRouter`, but most screens are pushed with plain `Navigator`, so view coverage is unknown. | Decide what MY BISPRO should measure. Then the shared analytics port. | S (after the decision) |
| Logging and crashes | Monitoring fans out to Crashlytics and Datadog. PII sanitiser. | `DatadogLog.e` calls `createLogger(name: e.toString())` and never `.error()`. 108 call sites and the provider observer report nothing. No Crashlytics. Datadog RUM native crash reporting is on, but no RUM application exists. Consent hard-coded `granted`. No PII sanitiser. | Fix `DatadogLog.e` once in `core` (same bug on GENFI and SQUARE), create the RUM application, decide on Crashlytics. | S |
| Feature flags | Typed catalogue behind one interface. | `RemoteConfig` freezed model with 6 keys: 1 flag (`FEATURE_KEYCLOAK_MANAGE_TOKEN`) and 5 numbers (agent period, schedule, maintain threshold, latest and minimum app version for the update prompt). Live updates through `onConfigUpdated`. One raw `getBool` in `main.dart`. 21 compile-time dart-defines, one of them misnamed in CI. | Small and clean. Join the shared catalogue; fix the CI name. | S |
| Networking | dio adapter behind a client interface, typed exceptions. | `core.HttpClient` (dio, 30 s timeouts) behind one of two Keycloak decorators. Both refresh before every call and clear the session on 401. No retry interceptor, no request id header, no dio tracing for RUM. `retry` is used only for the FCM token. Login is a Keycloak webview. (shared) The two decorators are two of the six near-identical auth clients. | Same chain as the other apps. | M (shared) |
| Security | Everspin RASP, CodeMix, build registration, device fingerprint, screen-capture guard, pinning. | Pinning only when `SHA_256_FINGERPRINT` is passed, only prod passes it. Root detection on, cannot be turned off from CI (name mismatch). No Play Integrity. `--obfuscate --split-debug-info` in CI, no explicit `minifyEnabled`, no `proguard-rules.pro`. `allowBackup` false, no cleartext. Debug build type signed with the release keystore. `FEATURE_ENABLE_PROXY` reaches prod from a variable. No screen-capture guard. Tokens in secure storage. A WhatsApp link carries the customer's mobile number. | Pin everywhere, fix the flag name, keep debug off the release key, drop the prod proxy switch. RASP with the other repos. | S / M (RASP) |
| Design system | Tokens from Figma, Widgetbook. | `ui_theme` only (119 files). `BfiColors` 731 uses, raw colours 47 sites. No `ds_*` git package. | The cleanest of the four apps. Keep it that way through the shared design-system plan. | S |
| Testing | 5,288 test files, coverage gate on changed files, Appium end-to-end. | 57 widget test files, 223 `testWidgets`, 0 `test(`, 0 controller tests, 0 goldens, no integration tests. Controllers mocked with `mocktail`. Template `widget_test.dart` with an empty `main()`. Coverage computed, never gated. No randomisation. | Controller tests for the three rule-heavy features first. Coverage gate on changed files. | M |
| Lint and guardrails | custom\_lint, Danger, generated-files check, `.claude/rules`. | (shared) Root `strict_lint.yaml` with 6 rules downgraded to ignore, including `depend_on_referenced_packages`. `very_good_analysis` is a dev dependency but not the rule set. `flutter analyze --fatal-infos --fatal-warnings`, format check, pubghost. No `custom_lint`, no architecture rule, no generated-files check. | One lint set, architecture ratchets. | S (shared) |
| CI/CD | See the next section. | 4 workflows, 773 lines, none with `permissions:`, all red. | See the next section. | M |

**Target shape**

## CI/CD compared step by step

| **Step** | **Jago prod pipeline** | **MY BISPRO** | **Gap** |
| --- | --- | --- | --- |
| Trigger | Version tag or manual on master. | Trunk: push to master on `mybispro/**` only, so a shared-package change does not rebuild it. SIT: tag `**-mybispro`. UAT and prod: manual dispatch (`tag`, `version`, `is_adhoc`). | Trigger the trunk build on shared-package changes too. |
| Run history (API, 26 Oct 2026) | n/a | Trunk 11 runs, last 2 Oct 2026, failed at "Setup Android SDK". SIT 19 runs, last 19 Jun, failed at App Distribution (Android) and "Build iOS SIT". UAT 0 runs. Prod 14 runs, last 19 Jun, Android failed at "Upload android symbol to datadog" before the Play step, iOS failed at "Upload crashlytics symbols" after TestFlight. Last five of each: all failed. | **No green run on record.** Store builds come from somewhere else. |
| Toolchain | One pinned version. | Flutter 3.35.0 in all four files. Trunk uses Java 11 and Android SDK 33 against `compileSdk` 36. Prod installs NDK 28 while Gradle asks for 27. Xcode `latest-stable`, not pinned. | One toolchain file. Fix the trunk SDK (the step that fails). |
| Version and build number | From the tag, CI counter. | pubspec `1.0.0+1`. Prod writes the operator's `version` input with `yaml-update-action@main`. DEV, SIT and UAT builds ship as `1.0.0+1`. | CI counter. |
| Config | `env.dart` per environment. | 12 defines in trunk (no Firebase, so DEV starts Firebase with empty options), 21 in SIT, 22 in UAT and prod. `FEATURE_ENABLE_JAILBREAK_DETECTION` is passed, `FEATURE_JAILBREAK_DETECTION` is read. | Fix the name. Give DEV its Firebase config or drop Firebase from DEV on purpose. |
| Build | `flutter build appbundle`, fastlane for iOS. | APK or AAB `--obfuscate --split-debug-info --release`; iOS through `xcodebuild` with team, profile and signing identity on the command line. | Consider fastlane + match. |
| Code protection | CodeMix, registration. | No explicit R8 setting, no `proguard-rules.pro`. The prod job uploads `mapping.txt`, which suggests shrinking is on by default (not verified). | Make R8 explicit, add the rules file. |
| Approval | Separate repo. | `trstringer/manual-approval@v1`, 2 of 9, `GH_PAT`. Environment has 0 rules. | Protect `sharia_prod_mybispro`. |
| Signing | Keystore only in the prod repo. | Keystore, properties, p12, profile and ExportOptions decoded from base64 secrets into the workspace. No keystore artifact upload (better than SQUARE). | Acceptable once the environment is protected. |
| Distribution | Play internal, TestFlight. | SIT and UAT: Firebase App Distribution group `sharia-mybispro`. Prod: Play `internal` with `BRAVO_GCP_SA_KEY`, TestFlight with App Store Connect API key. Ad-hoc builds a profile APK and IPA as 1-day artifacts. | Same as GENFI. |
| Post-build | Eversafe registration. | Datadog symbols (`datadog-ci`, unpinned npm install). Then a Crashlytics `upload-symbols` step for `Pods/FirebaseCrashlytics` and a `GoogleService-Info.plist` that do not exist in the repo. On Android the symbol upload runs before the Play upload, so a symbol failure blocks the release. | Delete the Crashlytics step. Move the Play upload before the symbol upload, or make symbols `continue-on-error`. |
| PR checks | Lint, format, generated files, tests, coverage on changed files, Danger. | (shared) Format, analyze, pubghost, tests, coverage comment with `continue-on-error`. Runs only on `*.dart` changes. No threshold, no randomisation, no generated-files check. | Same as the shared CI plan. |
| Pinned actions | n/a | 17 third-party actions, all by tag, `yaml-update-action@main` by branch, `checkout@v1` in trunk. No `permissions:` block anywhere. Secrets interpolated into `run:` on 30+ lines. | Pin by SHA, least-privilege token, `env:` for secrets. |

**Pipeline state**

## What else to work on

### 1. The dead logging path

`lib/app/utils/datadog_log.dart` is the same file as in GENFI and SQUARE. `DatadogLog.e(e, st)` builds a `DatadogLoggerConfiguration(name: e.toString())`, calls `createLogger`, and returns. The stack trace is unused. `guardLog` wraps 108 calls with it, and `DatadogLogProviderObserver` reports every `AsyncError` from every provider through it. Nothing reaches Datadog Logs. Because MY BISPRO has no Crashlytics either, a handled error in this app is invisible. The fix is one method in `core`, shared by all four apps, and a RUM application for MY BISPRO so the SDK has somewhere to send.

**Where a handled error goes today**

### 2. Config and build mistakes that cost nothing to fix

* `FEATURE_ENABLE_JAILBREAK_DETECTION` (CI) vs `FEATURE_JAILBREAK_DETECTION` (code). Root detection is always on. Either is fine, but the define is dead.
* `google-services` Gradle plugin declared in `settings.gradle`, never applied. Firebase runs from dart-defines only. Delete the declaration or the confusion stays.
* `gradle.properties` suppresses "unsupported compileSdk 35" while compileSdk is 36.
* `appAuthRedirectScheme` placeholders per flavour, but `flutter_appauth` is not a dependency.
* `test/src/widget_test.dart` is the Flutter template with an empty `main()`.
* The trunk DEV build builds an APK and throws it away. Either distribute it or stop building it.

### 3. Split the largest files

| **File** | **Lines** |
| --- | --- |
| `features/prospectlist/detail/prospect_detail_screen.dart` | 1,563 |
| `features/inputprospect/idcarddetail/id_card_detail_form_screen.dart` | 1,338 |
| `features/inputprospect/confirmation/input_prospect_confirmation_screen.dart` | 1,331 |
| `features/agent/create_agent_form_screen.dart` | 1,222 |
| `features/editloan/form/edit_loan_form_screen.dart` | 1,165 |
| `features/inputprospect/identity/identity_screen.dart` | 1,104 |

`inputprospect` is 11,601 lines in 29 files, a quarter of the app. It is the pilot feature for Phase 7. The router declares 9 routes. Most screens are pushed with `Navigator`, so typed routes per feature come with the layering work.

### 4. Other items

* `dummyCreditAnalystNote` ("dummy credit analyst note") is set as the credit-analyst note by `edit_loan_form_controller.dart:55` and shown by the form. Check what the backend receives.
* `create_agent_model.dart` carries a TODO "remove this when create agent API is ready". `upload_image_field.dart:182` has "hit upload service" with the upload not wired. Check whether these screens are live.
* `FirebaseMessaging.requestPermission()` runs in `main` before any UI, so iOS asks for push permission on first launch with no context.
* `MyBisProSharedPreferences.deleteAllData()` clears the whole `SharedPreferences` store.
* Older majors: `share_plus` 7, `mime` 1.0, `freezed` 2.5, `geolocator` 13, `go_router` 14, Riverpod 2.6. The git dependency `flutter_jailbreak_detection` is pinned by SHA to `bfi-flutter-packages`.
* The GitHub API lists an active workflow `mybispro-pr-pipeline.yml` whose file no longer exists on master. Some run history sits under renamed files.
* The MyShaf route inside this app (`myShafRoute`) is a screen, not the MyShaf app.

## Security items

Shared with the monorepo (secret-printing workflows, keystore artifact, `BRAVO_GCP_SA_KEY` in 51 repos, prod builds without environment rules): see Genfi mobile app assessment and Agency phase 0: Close the leak. Specific to MY BISPRO:

1. `sharia_prod_mybispro` has no protection rule (verified 26 Oct 2026). Required reviewers are not available on the Team plan for private repos, so limit the environment to release refs and keep the approval step, as the shared Phase 0 page says.
2. DEV, SIT and UAT builds are unpinned. Only the prod workflow passes `SHA_256_FINGERPRINT`.
3. The debug build type uses the release signing config (`build.gradle:122-128`). A debug build from any laptop with the keystore is a release-signed binary.
4. `FEATURE_ENABLE_PROXY` enters prod builds from a repository variable. When on, it also switches off Datadog HTTP tracking.
5. Secrets interpolated into `run:` lines in all four workflows (trunk 81-88, SIT 57-70 and 137-164, UAT the same, prod 103-117 and 226-254). `CLIENT_SECRET` for Keycloak is among them and is compiled into the binary as a dart-define.
6. No `permissions:` block in any workflow, so every job runs with the default token.
7. Root detection cannot be switched off (name mismatch). This is safe but means a false positive on a staff device blocks the user until a code change.
8. The Keycloak login is an in-app webview (`keycloak` depends on `webview_flutter`), not the system browser. Inferred from the dependency, not traced further.

## Plans and roadmap

MY BISPRO does not get thirteen plan pages of its own. It is small, and most of the work is shared. The split:

* **Shared, done once for the monorepo:** security, CI/CD, networking, lint, repo layout, design system, dependency injection, Riverpod 3. Under Agency apps roadmap: shared phases, MY BISPRO is a row in every phase table.
* **MY BISPRO rows in the GENFI plan pages** where the finding is identical: GENFI plan 03: Logging and crashes (the `DatadogLog.e` fix is one change in `core`), GENFI plan 10: Feature flags (one catalogue), GENFI plan 12: Design system.
* **MY BISPRO only:** the per-app phases below. They follow the same impact classes as GENFI roadmap: step by step (**A** no app change, **B** same behaviour, **C** behind a switch flag, **D** approved delta, **E** backend-coupled).

| **#** | **Step** | **Class** | **Phase** | **Depends on** | **Jira ticket** | **PR** |
| --- | --- | --- | --- | --- | --- | --- |
| P.1 | Repair the trunk build (Java 17, SDK 36) and the SIT and prod pipelines so one run is green. Delete the Crashlytics symbol step. Move the Play upload before the Datadog symbol upload. | A | 0 | – | | |
| P.2 | Limit `sharia_prod_mybispro` to release refs. Pin actions by SHA, add `permissions:`, move secrets to `env:`. | A | 0 | Agency phase 0 | | |
| P.3 | Fix the melos category and PR path filter (drop `document`, `sso`), trigger trunk on shared-package changes. | A | 1 | – | | |
| P.4 | Create the MY BISPRO RUM application and pass its id. Fix `DatadogLog.e` in `core`. | A (Datadog) / B (code) | 1 and 2 | GENFI plan 03 step 1 | | |
| P.5 | Controller tests for `inputprospect`, `editloan` and `maintainagent` against today's behaviour. Coverage gate on changed files. | A | 1 | Agency phase 1 | | |
| P.6 | Approved deltas, one per release: remove `dummyCreditAnalystNote`, fix the jailbreak define name, pin SIT and UAT, debug build off the release key, drop the prod proxy variable, move the push-permission prompt behind a screen. | D | 3 | Phase 1 gate | | |
| P.7 | Network chain behind `useInterceptorClient`: the two Keycloak decorators become the shared chain. Remove the runtime `updateOverrides` swap. | C, E | 4 | Agency phase 4 | | |
| P.8 | Pilot: `inputprospect` through the parity loop (ledger, flag `useNewInputProspectFlow`, domain for the prospect and financing rules, Notifiers, cohort 20% → 100%, flip, delete). | C | 7 | Phase 6 | | |
| P.9 | Other features through the same loop: `maintainagent`, `editloan`, `agent`, `mkyc`, then class B conversions for the rest. Break the 8 two-way pairs and the `main.dart` cycle on the way. | C, then B | 9 | P.8 | | |

Suggested epic names: "[Tech x DK] MY BISPRO Improvement - Approved deltas", "- Pilot: input prospect", "- Remaining features". The shared phases use the epics on the shared pages.

**Where MY BISPRO's work sits**

## Open questions

| **#** | **Question** | **Who answers** |
| --- | --- | --- |
| Q1 | How are MY BISPRO builds reaching Play and TestFlight when no recorded run is green? Who builds them, from which machine, with which keystore? | Agency tech lead |
| Q2 | How many staff use MY BISPRO? There is no RUM application and no analytics, so this page has no number. | Sharia business |
| Q3 | Who owns the app? The README says Sharia. The last release was in June. Is the app still being developed? | Engineering manager |
| Q4 | What are the prod values of `FEATURE_ENABLE_PROXY` and `DATADOG_SAMPLING_RATE`? | Environment owner |
| Q5 | Is the `dummyCreditAnalystNote` text stored on the backend for real loans? | Sharia product |
| Q6 | Is root detection meant to be always on for staff devices, or should the CI switch work? | Security |
| Q7 | Does Datadog RUM record dio resources at all for this app, given only `dart:io` tracking is enabled? | Observability |

Facts checked on 26 Oct 2026 against `bravo-agency-app` `master` @ `1e50b819`, the GitHub REST API and Datadog RUM (us5). Full fact sheet with commands: `bravo-analysis/docs/mobile-assessment/mybispro/facts.md`.
