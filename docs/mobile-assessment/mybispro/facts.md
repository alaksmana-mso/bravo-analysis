# MY BISPRO fact sheet

Source: `bfi-finance/bravo-agency-app`, folder `mybispro/`, master @ `1e50b819` (22 Oct 2026).
Read on 26 Oct 2026. Code and CI files only. No builds, no run logs.
Paths below are relative to the repo root unless they start with `/`.
"Count" lines give the grep used so the number can be reproduced.

Sister pages: GENFI (`agent_tools/`) and SQUARE (`are_tracker/`). Shared packages and shared
workflows are covered there. This sheet only says how MY BISPRO uses them.

---

## 1. Scope

| Item | Value | Evidence |
|---|---|---|
| pubspec name | `mybispro` | `mybispro/pubspec.yaml:1` |
| description | "MyBisPro Mobile App" | `mybispro/pubspec.yaml:2` |
| version line | `1.0.0+1` (placeholder, prod workflow overwrites it) | `mybispro/pubspec.yaml:4`, `.github/workflows/mybispro-promot-prod-pipeline.yml:86-92` |
| Dart SDK | `>=3.9.0 <4.0.0` | `mybispro/pubspec.yaml:7` |
| Flutter constraint | none in pubspec. CI pins Flutter `3.35.0` | all four `mybispro-*` workflows, `.github/actions/setup-codebase/action.yml` |
| Android applicationId | `id.co.bfi.sharia.mybispro` + suffix `.sit` / `.dev` / `.uat` / none | `mybispro/android/app/build.gradle:69,84-108` |
| Android namespace | `id.co.bfi.sharia.mybispro` | `build.gradle:53` |
| minSdk / targetSdk / compileSdk | 29 / 36 / 36, NDK 27.0.12077973 | `build.gradle:54-55,70-71` |
| iOS bundle ids | `id.co.bfi.sharia.mybispro`, `.dev`, `.sit`, `.uat` | `mybispro/ios/Runner.xcodeproj/project.pbxproj:432,520,777,866` and others |
| iOS min platform | 15.0 | `mybispro/ios/Podfile:2` |
| Flavors | sit, dev, uat, prod (Android product flavors + iOS schemes) | `build.gradle:82-108` |

Package versions (from `mybispro/pubspec.lock`):

| Package | Declared | Locked |
|---|---|---|
| flutter_riverpod | not declared (comes through `core`) | 2.6.1 |
| riverpod | transitive | 2.6.1 |
| hooks_riverpod | not used | not in lock |
| riverpod_annotation / riverpod_generator | not used | not in lock |
| bloc / flutter_bloc | not used | not in lock |
| dio | transitive via `core` | 5.9.0 |
| go_router | `^14.8.0` | 14.8.1 |
| freezed | `^2.5.8` | 2.5.8 |
| firebase_core | `^4.1.0` | 4.1.0 |
| firebase_messaging | `^16.0.1` | 16.0.1 |
| firebase_remote_config | `^6.0.1` | 6.0.1 |
| firebase_analytics | not used | not in lock |
| firebase_crashlytics | not used | not in lock |
| datadog_flutter_plugin | `^2.13.1` | 2.13.1 |
| datadog_tracking_http_client | `^2.3.0` | 2.3.0 |
| flutter_secure_storage | transitive via `keycloak` | 8.1.0 |
| flutter_jailbreak_detection | git, SHA `55bba36d` | 0.0.1 |
| http_certificate_pinning | path `shared_lib/http_certificate_pinning` via `core` | 2.0.6 |

Melos: the root `pubspec.yaml` has a `mybispro` category with 9 packages
(`shared_data/agency`, `agent_marketing`, `document`, `keycloak`, `onboarding`, `user_iam`, `sso`,
`shared_lib/core`, `ui_theme`) at `pubspec.yaml:66-75`. Scripts `bootstrap:mybispro`,
`format:mybispro`, `analyze:mybispro`, `test:mybispro`, `generate:mybispro`, `localization:mybispro`
exist (`pubspec.yaml:95,124,152,291` and the generate/localization blocks).

Size (hand-written = not `*.g.dart`, `*.freezed.dart`, `app_localizations*.dart`):

| Measure | Value |
|---|---|
| Dart files under `lib` | 325 (`find lib -name '*.dart' \| wc -l`) |
| Hand-written Dart files | 247 |
| Hand-written lines | 50,880 |
| Generated `*.g.dart` / `*.freezed.dart` files | 76 files, 24,901 lines |
| Generated l10n | 2 files, 7,813 lines (`lib/app/localizations/app_localizations*.dart`) |
| Test Dart lines | 14,038 (`mybispro/test`) |

Feature folders under `lib/features` (hand-written files / lines):

| Feature | Files | Lines |
|---|---|---|
| inputprospect | 29 | 11,601 |
| maintainagent | 27 | 6,818 |
| common | 26 | 5,414 |
| mkyc | 29 | 4,756 |
| prospectlist | 14 | 4,172 |
| agent | 16 | 3,780 |
| editloan | 8 | 3,335 |
| loansimulation | 7 | 1,706 |
| home | 5 | 1,023 |
| claimagent | 5 | 896 |
| ocr | 4 | 714 |
| inbox | 3 | 672 |
| login | 3 | 587 |
| selfie | 4 | 466 |
| survey | 2 | 364 |
| agentlist | 2 | 311 |

Plus `lib/app` (app shell, navigation, 20 shared UI widgets, 24 utils, messaging, remote config,
shared preferences) and `lib/main.dart`.

Top 8 hand-written files:

| Lines | File |
|---|---|
| 1,563 | `lib/features/prospectlist/detail/prospect_detail_screen.dart` |
| 1,338 | `lib/features/inputprospect/idcarddetail/id_card_detail_form_screen.dart` |
| 1,331 | `lib/features/inputprospect/confirmation/input_prospect_confirmation_screen.dart` |
| 1,222 | `lib/features/agent/create_agent_form_screen.dart` |
| 1,165 | `lib/features/editloan/form/edit_loan_form_screen.dart` |
| 1,104 | `lib/features/inputprospect/identity/identity_screen.dart` |
| 975 | `lib/features/inputprospect/loaninfo/loan_info_form_screen.dart` |
| 917 | `lib/features/common/financing_input_form/financing_input_form.dart` |

Router: `lib/app/navigation/router.dart` (273 lines). One `GoRouter` at line 69 with
`initialLocation: '/$homeRoute'` (line 70), a `ShellRoute` (line 92) and 9 `GoRoute(` entries
(`grep -c "GoRoute(" router.dart` = 9): home, loanSimulation, inputProspect, surveyor, myShaf,
prospect, maintainReportList, inbox, login (lines 98-179). Most screens are pushed with
`Navigator`/`MaterialPageRoute` rather than declared routes (not counted). `redirect` at line 77.
`DatadogNavigationObserver` at line 90.

## 2. Repo layout

Path dependencies declared in `mybispro/pubspec.yaml`: `agency`, `agent_marketing`, `core`,
`keycloak`, `onboarding`, `ui_theme`, `user_iam` (7). Not declared although listed in the melos
category and in the PR path filter: `shared_data/document`, `shared_data/sso`
(`pubspec.yaml:66-75` vs `mybispro/pubspec.yaml`). No import of `package:document/` or
`package:sso/` in `mybispro/lib` (grep = 0). The category is wider than the real dependency set.
`user_iam` is declared and imported by 1 file.

Not used by MY BISPRO: `shared_features/*`, `shared_lib/crash_reporting`, `shared_lib/places`,
`shared_data/master`, `shared_data/integrity`, `ui_catalog`.

Cross-feature imports: `grep -rhn "import 'package:mybispro/features/" lib/features | wc -l`
= 399 (includes same-feature imports). Relative imports crossing folders: 0 (lint enforces package
imports). `lib/app` imports `lib/features` in 12 places, 9 of them in `router.dart`, the other 3
are `lib/app/utils/agent_list_utils.dart:2`, `lib/app/utils/create_agent_utils.dart:2`,
`lib/app/top_level/top_level_tab_extra.dart:3`.

Top feature-to-feature pairs (different feature only):

| Count | From -> To |
|---|---|
| 25 | inputprospect -> common |
| 9 | loansimulation -> common |
| 9 | inputprospect -> loansimulation |
| 9 | editloan -> common |
| 6 | prospectlist -> common |
| 5 | agent -> common |
| 4 | prospectlist -> inputprospect |
| 4 | common -> loansimulation |
| 4 | agent -> inputprospect |
| 3 | ocr -> inputprospect |
| 3 | maintainagent -> loansimulation |
| 3 | maintainagent -> home |

Two-way import pairs (8): `agent <-> inputprospect`, `agent <-> ocr`, `common <-> loansimulation`,
`editloan <-> prospectlist`, `home <-> maintainagent`, `inputprospect <-> loansimulation`,
`inputprospect <-> ocr`, `mkyc <-> prospectlist`. `common` is not a leaf: it imports
`loansimulation` 4 times.

Import cycle at app level: `main.dart:17` -> `app/app.dart:4` -> `app/app_controller.dart:10` ->
`main.dart`. `AppController` reads the `keycloakConfig` and `networkConfig` constants from
`main.dart` (`app_controller.dart:69,70,83,84`).

## 3. Layering

- No domain layer. Folders named `domain`, `usecase`, `entity`: none under `lib`
  (`find lib -type d -iname domain` etc. = only `lib/features/common/entityselection`, a UI folder).
  One file named `*_use_case.dart`: `lib/app/data/remote_config/remote_config_use_case.dart`
  (a 5-line `StreamProvider`).
- Only `data` folder: `lib/app/data` (remote config, shared preferences).
- Files that read a repository provider directly:
  `grep -rlE "ref\.(read|watch)\([A-Za-z_.]*Repository" lib` = 47 files, 87 call sites.
  Most are controllers that take repositories in their constructor via `ref.watch(...)`.
  Examples: `lib/app/app_controller.dart:27-29`, `lib/app/messaging/messaging_service.dart:33`.
- Screens import `shared_data` packages directly: 49 of 68 `*_screen.dart` files import
  `package:agent_marketing/`, `agency/`, `onboarding/`, `user_iam/` or `keycloak/`
  (`grep -rlE "import 'package:(agent_marketing|agency|onboarding|user_iam|keycloak)/" lib/features | grep _screen.dart | wc -l` = 49).
  Examples: `lib/features/home/home_screen.dart`, `lib/features/inbox/inbox_screen.dart`,
  `lib/features/claimagent/result/claim_agent_result_screen.dart`.
- `*Response` DTO types in screens or controllers: 1 file, and it is a permission type, not an
  API DTO (`lib/features/survey/surveyor_screen.dart:210`, `PermissionRequestResponse`). The
  shared_data models are not named `*Response`, so this grep under-counts DTO leakage. The 49
  screen imports above are the better signal.
- Error-to-UI path: `lib/app/utils/api_error_correlation_id.dart` maps three exception types to a
  correlation id shown on error screens (added 2 Oct 2026, commit `b1e870ad3`, BAE-4018).

## 4. State management

Counts (`grep -rn` over `lib`, generated files excluded):

| Pattern | Count |
|---|---|
| `extends StateNotifier<` | 61 |
| `extends Notifier<` / `AsyncNotifier<` / `AutoDispose*Notifier<` | 0 |
| `StateProvider` | 1 definition (`lib/features/inputprospect/setlocation/set_location_screen.dart:13`, a file-level global) |
| `ChangeNotifier` | 1 (`lib/app/navigation/router.dart:244`, `_StreamListenable` for `refreshListenable`) |
| `static final ...Provider` | 70 (provider as static member on the class) |
| Top-level `final ...Provider` | 1 (`currentLocationStateProvider`) |
| `ConsumerStatefulWidget` | 131 |
| `ConsumerWidget` | 4 |
| `StatefulWidget` (non-Consumer) | 156 |
| `setState(` | 40 |
| `ref.watch(` | 588 |
| `ref.read(` | 130 |
| `ref.listen(` | 56 |
| `ref.watch` on an `onPressed:` line | 4 (`edit_loan_form_screen.dart:354,390`, `financing_input_form.dart:236,272`) |
| Files with `ref.read(` inside a `build` method | 35 (heuristic awk, includes `.notifier` reads in callbacks defined in build) |

Pattern: Riverpod 2 `StateNotifier` + freezed state, provider exposed as
`static final provider = StateNotifierProvider.autoDispose<...>` on the controller class
(`lib/app/app_controller.dart:22-31`). No code generation for providers. `App.build` calls
`ref.read(AppController.provider.notifier).onAppLoaded()` on every build (`lib/app/app.dart:14`),
and `AppScreen.initState` calls it again (`lib/app/app_screen.dart:24-26`).

Global state / service locators:
- `NavigationService.instance` singleton with a `navigationKey` used as `GoRouter.navigatorKey`
  (`router.dart:76`), used in 4 places.
- `_ref.container.updateOverrides(...)` and `_ref.container.refresh(...)` inside `AppController`
  to swap the auth client at runtime (`app_controller.dart:68-89`). This is a documented Riverpod
  escape hatch, used for the Keycloak token feature flag.
- `MyBisProSharedPreferences.deleteAllData()` calls `SharedPreferences.clear()` (whole store)
  (`lib/app/data/database/mybispro_shared_preferences.dart:24-27`).

## 5. Dependency injection

`lib/main.dart:140-168` (`mainWithConfig`):
1. `FlutterDownloader.initialize()`, `Firebase.initializeApp(FirebaseOptions(...))` from
   dart-defines (no `google-services.json` or `GoogleService-Info.plist` in the repo), then
   `FirebaseMessaging.requestPermission()` at startup (`main.dart:108-125`).
2. `FirebaseRemoteConfig.fetchAndActivate()` under `guardLog` (`main.dart:128-132,145`).
3. Reads `FEATURE_KEYCLOAK_MANAGE_TOKEN` to choose between
   `agent_marketing.AgentMarketingKeycloakHttpClient.provider` and `KeycloakHttpClient.provider`
   (`main.dart:147-152`).
4. `ProviderScope` with observer `DatadogLogProviderObserver` and 4 overrides:
   `HttpClient.authProvider`, `HttpClient.krakendHttpClientProvider` (both -> chosen auth client),
   `KeycloakConfig.provider` (value), `NetworkConfig.provider` (value) (`main.dart:153-167`).
5. `HttpClient.nonAuthKrakendHttpClientProvider` is not overridden, so it falls back to the plain
   client (`shared_lib/core/lib/src/network/http_client.dart:45-48`).

Interfaces / ports: the only abstraction is `core.HttpClient` (concrete class) which both auth
decorators `implements` (`keycloak_http_client.dart:7`, `agent_marketing_keycloak_http_client.dart:7`).
Repositories are concrete classes. No abstract repository or use-case interfaces in `mybispro/lib`.
Tests mock concrete classes with `mocktail` (`test/src/login/login_screen_test.dart:17-33`).

Runtime re-wiring: when the remote flag changes, `AppController._refreshOverrides` logs the user
out of the other Keycloak repository, calls `updateOverrides` and `refresh` on the container
(`app_controller.dart:62-89`).

## 6. Analytics

- No analytics wrapper class. `grep -rniE "analytics|mixpanel|logEvent|trackEvent|addUserAction|setUserInfo|addAttribute" lib` = 0 hits.
- `firebase_analytics` not in pubspec or lock.
- Datadog RUM is configured in `main.dart:72-85` (`DatadogRumConfiguration` with
  `applicationId` and `sessionSamplingRate` from dart-defines, site `us5`,
  `nativeCrashReportEnabled: true`). Views come from `DatadogNavigationObserver` on the
  `GoRouter` (`router.dart:90`). Screens pushed with plain `Navigator` outside `GoRouter` are
  covered by that observer only if they go through the same navigator (not verified).
- Number of explicit event call sites: 0. No custom RUM actions, no user id (`setUserInfo` not
  found), no custom attributes.
- Network tracing: `_ddSdkConfig.enableHttpTracking()` only when `HttpOverrides.current == null`
  and the proxy flag is off (`main.dart:27-29`). `datadog_tracking_http_client` is for
  `dart:io HttpClient`. The app's traffic goes through `dio` (`core.HttpClient`), so whether RUM
  resources are captured for dio calls is not verified from code.

## 7. Logging and crashes

- Crashlytics: not used. `grep -rni crashlytics lib pubspec.yaml` = 0. Yet the prod workflow has a
  step "Upload crashlytics symbols" that calls `mybispro/ios/Pods/FirebaseCrashlytics/upload-symbols`
  with `mybispro/ios/Runner/GoogleService-Info.plist` (`mybispro-promot-prod-pipeline.yml:292-294`).
  Neither path exists in the repo. The last prod run failed on this step (see section 14).
- Datadog SDK: `DatadogSdk.runApp(_ddSdkConfig, TrackingConsent.granted, ...)` when the client
  token is non-empty (`main.dart:26-33`). Tracking consent is hard-coded `granted`. No consent
  screen.
- `DatadogLog` wrapper at `lib/app/utils/datadog_log.dart`. Call sites: `grep -rnE "DatadogLog\.e|guardLog\(" lib` = 108.
  Finding: `DatadogLog.e` only calls `DatadogSdk.instance.logs?.createLogger(DatadogLoggerConfiguration(name: e.toString(), ...))`
  (`datadog_log.dart:8-12`). It creates a logger named after the error string and never calls
  `.error(...)` on it. The stack trace parameter is unused. So the 108 call sites and the
  `DatadogLogProviderObserver` (which reports every `AsyncError` from any provider,
  `datadog_log.dart:26-38`) send no log lines. This is EXTRACTED from code, not verified at
  runtime.
- Custom keys / PII: no `addAttribute`, `addTag`, `setUserInfo` calls. No NIK, phone or email
  sent to Datadog from app code (grep = 0). No PII sanitiser exists either. Error strings used as
  logger names could carry server messages, but since nothing is logged the risk is moot today.
- `debugPrint(` = 3 sites (`messaging_service.dart` and others).
- Swallowed catches (`catch (_)`, empty catch): 0.

## 8. Feature flags

Remote Config (`lib/app/data/remote_config/remote_config_repository.dart`):
- Settings: `fetchTimeout` 1 min, `minimumFetchInterval` 1 h (lines 14-21).
- Flag model `RemoteConfig` (freezed, `remote_config.dart`) with 6 keys read at lines 24-38:
  `FEATURE_KEYCLOAK_MANAGE_TOKEN` (bool), `CONFIG_NEW_AGENT_PERIOD_IN_DAYS`,
  `CONFIG_SCHEDULE_PER_DAY_MIN`, `CONFIG_LAST_MAINTAIN_THRESHOLD_IN_DAYS`,
  `MYBISPRO_APP_VERSION_LATEST`, `MYBISPRO_APP_VERSION_REQUIRED_MIN` (ints). 1 real feature
  flag, 5 config values.
- Live updates: `stream` listens to `onConfigUpdated` and re-activates (lines 41-49).
  `getRemoteConfigUseCase` is a `StreamProvider.autoDispose` (`remote_config_use_case.dart:4`).
- Raw calls outside the repository: `FirebaseRemoteConfig.instance.getBool('FEATURE_KEYCLOAK_MANAGE_TOKEN')`
  in `main.dart:147-149`. No other raw `getBool/getString` on Remote Config in `lib`.
- Force / soft update is driven by the two version keys vs `PackageInfo.buildNumber`
  (`app_controller.dart:91-104`).

Compile-time dart-defines read in `lib` (21 names, `grep -rhoE "fromEnvironment"`):
`API_SCHEME`, `API_HOST`, `API_PORT`, `SHA_256_FINGERPRINT`, `CLIENT_ID`, `CLIENT_SECRET`,
`REALM_ID`, `KEYCLOAK_LOGIN_URL`, `DATADOG_CLIENT_TOKEN`, `DATADOG_APP_ID`,
`DATADOG_SAMPLING_RATE`, `FLAVOUR` (x2), `FIREBASE_APP_ID`, `FIREBASE_API_KEY`,
`FIREBASE_SENDER_ID`, `FIREBASE_PROJECT_ID`, `FIREBASE_ANDROID_CLIENT_ID`,
`FIREBASE_IOS_CLIENT_ID`, `SURVEYOR_PLATFORM_URL`, `FEATURE_ENABLE_PROXY`,
`FEATURE_JAILBREAK_DETECTION` (default `true`, `app_controller.dart:114-117`).
`MAPS_API_KEY` is read by Gradle, not Dart (`build.gradle:36-43,75`).

Name mismatch: every workflow passes `--dart-define=FEATURE_ENABLE_JAILBREAK_DETECTION=${{vars.FEATURE_JAILBREAK_DETECTION}}`
(`mybispro-deploy-tag-cd-pipeline.yml:73,153`, `mybispro-uat-promote-tag-pipeline.yml:78`,
`mybispro-promot-prod-pipeline.yml:120,243`). Code reads `FEATURE_JAILBREAK_DETECTION`. The
define is ignored and the default `true` always applies. Root detection cannot be turned off from
CI today. (The trunk DEV build does not pass it at all.)

## 9. Networking

- Base client: `core.HttpClient` wrapping `dio` 5.9.0, timeouts connect/send/receive 30 s,
  `Accept: application/json` (`shared_lib/core/lib/src/network/http_client.dart:10-21`).
  Per-call `TimeoutOptions` override possible.
- Auth decorators (both `implements HttpClient`, chosen at startup by `FEATURE_KEYCLOAK_MANAGE_TOKEN`):
  - `keycloak.KeycloakHttpClient` (`shared_data/keycloak/lib/src/keycloak_http_client.dart`):
    before every call it awaits `_keycloakRepository.refreshToken()` (line 34 and 6 more),
    adds the bearer header, and on HTTP 401 clears the session and throws
    `SessionExpiredException` (lines 161-175). Token endpoint is Keycloak direct:
    `/keycloak/realms/{realm}/protocol/openid-connect/token` (`data/network/keycloak_network_data_source.dart:20`).
  - `agent_marketing.AgentMarketingKeycloakHttpClient` (`shared_data/agent_marketing/lib/src/keycloak/agent_marketing_keycloak_http_client.dart`,
    237 lines): same shape, but refresh goes through the backend
    `/agent-marketing/v1/keycloak/refresh_token` (`keycloak/data/network/keycloak_network_data_source.dart:20`).
  - Refresh logic (`keycloak_repository.dart:54-68` in both): if refresh token expired ->
    clear session + `SessionExpiredException`. Else if access token expired -> refresh. Expiry is
    computed from local clock + `expires_in` (lines 94-103).
- Retry: no HTTP-level retry interceptor. Package `retry` is used in 2 places for FCM token
  fetch and device-token registration, 4 attempts, 10 s factor, no jitter
  (`lib/app/messaging/messaging_service.dart:124-145`).
- Client variants in `main.dart`: `authProvider` and `krakendHttpClientProvider` both point to
  the chosen Keycloak client. `nonAuthKrakendHttpClientProvider` and `HttpClient.provider` stay
  unauthenticated.
- Debug inspector: no `alice`, `chucker_flutter` or similar in pubspec or lock.
- Outgoing trace / request id header: none set by app code. `grep -rn "x-request-id|x-bfi-req-id|correlation" shared_lib/core/lib/src/network` = 0.
  The app only reads a correlation id from error responses (`api_error_correlation_id.dart`).
  Datadog RUM tracing headers for dio: not configured (no `DatadogInterceptor` / `dio` tracing
  found, grep `datadog` in core network = 0).
- Proxy: `FEATURE_ENABLE_PROXY` installs `HttpOverrides.global = HttpProxy` from system proxy
  settings (`main.dart:97-101`). When on, Datadog HTTP tracking is skipped (`main.dart:27`).
  All environments including prod pass this define from `vars.FEATURE_ENABLE_PROXY`
  (`mybispro-promot-prod-pipeline.yml:119`). The prod value is a repo variable, not visible in
  code. Not verified.
- Keycloak login: `KeycloakLoginClient` (`login_screen.dart:110`), the `keycloak` package depends
  on `webview_flutter ^4.2.2` (`shared_data/keycloak/pubspec.yaml:18`). Login happens in an
  in-app webview, not a system browser (INFERRED from the dependency, not traced further).

## 10. Security

| Control | State | Evidence |
|---|---|---|
| Certificate pinning | `CertificatePinningInterceptor` added only when `SHA_256_FINGERPRINT` is non-empty. Only the prod workflow passes it. DEV, SIT and UAT builds are unpinned. | `core/.../http_client.dart:24-29`, `mybispro-promot-prod-pipeline.yml:103,226`. Not in `mybispro-deploy-tag-cd-pipeline.yml` or `mybispro-uat-promote-tag-pipeline.yml` |
| Pinning plugin | vendored fork `shared_lib/http_certificate_pinning` 2.0.6 (path dep of `core`) | `shared_lib/core/pubspec.yaml:18-19` |
| Root / jailbreak | `flutter_jailbreak_detection` (BFI git fork, pinned SHA). On rooted device `isDeviceRooted = true` and the app stops loading. Cannot be disabled from CI (name mismatch, section 8). | `app_controller.dart:38-45,114-117` |
| Play Integrity / App Attest | none. `device_integrity`, `shared_data/integrity` not depended on | grep = 0 |
| R8 / minify / shrinkResources | not set in `build.gradle`. Flutter's Gradle plugin default applies (not verified here). `--obfuscate --split-debug-info` on every CI build | `build.gradle` has no `minifyEnabled`, workflows lines 89-90, 74-75, 79-80, 121-122, 244-245 |
| proguard-rules.pro | none (`find android -name "proguard*"` = 0) | |
| allowBackup | `false`, `fullBackupContent="false"` | `AndroidManifest.xml:24-25` |
| usesCleartextTraffic | not set (default false on API 28+) | grep = 0 |
| network_security_config | none | `res/xml` has only `provider_paths.xml` |
| iOS ATS | no `NSAppTransportSecurity` key, so default ATS | `Info.plist` grep = 0 |
| Debug signing | `debug` build type uses the **release** keystore (`signingConfig signingConfigs.release`) | `build.gradle:122-128` |
| Keystore in repo | no. `keystore.properties`, `*.jks` git-ignored. CI writes them from base64 secrets | `android/.gitignore`, root `.gitignore:12-13`, workflow "Create the Keystore" steps |
| Proxy switch | `FEATURE_ENABLE_PROXY` dart-define (see section 9) | `main.dart:88,22-24` |
| Screen capture guard | none (`FLAG_SECURE`, `screen_protector` grep = 0) | |
| Secure storage | tokens in `flutter_secure_storage` via `keycloak` package, keys `kc_atk`, `kc_rtk`, `kc_atetk`, `kc_rtetk`, `kc_hsebek`, `mkt` | `shared_data/keycloak/lib/src/data/local/keycloak_local_data_source.dart:6-11` |
| Plain `SharedPreferences` | FCM token and last report reminder date | `mybispro_shared_preferences.dart:11-12` |
| Biometrics | none (`local_auth` grep = 0) | |
| WebView | `flutter_inappwebview` 6.1.5, 1 `InAppWebView(` for the surveyor platform URL | `lib/features/survey/surveyor_screen.dart:33` |
| Deep links / app links | none. No `CFBundleURLTypes`, no `intent-filter` with `VIEW`+scheme, no `app_links` | `Info.plist`, `AndroidManifest.xml` |
| Custom URL scheme | `appAuthRedirectScheme` placeholder per flavor, but `flutter_appauth` is not a dependency. Unused placeholder. | `build.gradle:76,87,93,99,105` |
| Permissions (Android) | INTERNET, CAMERA, COARSE+FINE LOCATION, READ/WRITE EXTERNAL STORAGE, RECEIVE_BOOT_COMPLETED. `READ_MEDIA_*` removed with `tools:node="remove"` | `AndroidManifest.xml:5-15` |
| Permissions (iOS) | camera, location (3 keys), photo library, `UIBackgroundModes` | `Info.plist:43-56` |
| Maps key | `MAPS_API_KEY` injected into manifest meta-data at build time | `build.gradle:75`, `AndroidManifest.xml:69-71` |

Hard-coded URLs in `lib` (names only, `grep -rnoE "https?://"`): Google Play and App Store
listing URLs (`url_launcher.dart:103-104`), Google/Apple Maps search URLs (`url_launcher.dart:39,58,70`),
Google Authenticator store links (`login_guide_screen.dart:179-180`), WhatsApp `wa.me` links with
the customer's mobile number (`prospect_detail_screen.dart:1455`, `prospect_list_screen.dart:643`),
and a Flutter issue link in a comment. No API hosts, no keys, no secrets hard-coded
(`grep -rniE "api_?key|secret"` only hits dart-define reads and the remote flag name).

## 11. Design system

| Import | Files |
|---|---|
| `package:ui_theme/` | 119 |
| `package:ds_1/`, `bfi_design_system_2`, `bfi_design_system_3`, `ui_catalog` | 0 |

Colors: `BfiColors.` tokens = 731 uses. Raw `Colors.` = 30 lines. Raw `Color(0x...)` = 17.
Raw `TextStyle(` = 0. The app is on `ui_theme` only, with a small raw-colour tail (47 sites).

## 12. Testing

- Test files: 57 `*_test.dart` under `mybispro/test/src` (61 Dart files, 14,038 lines).
- `testWidgets(` = 223. `test(` = 0. `group(` = 0.
- Every test file is a screen, dialog, picker or bottom-sheet widget test. Controller / notifier
  unit tests: 0 (`find test -name '*controller*_test.dart'` = 0). Controllers are replaced with
  mocks in widget tests (`login_screen_test.dart:17-33,87`), so controller logic is largely
  untested at unit level. 47 test files reference a `Controller`.
- Golden tests: 0 (`matchesGoldenFile` grep = 0). `integration_test/`: none.
- Mocks: `mocktail` in 51 files. No generated mocks.
- `test/src/widget_test.dart` is the Flutter template with an empty `main()` (lines 1-8).
- `test/src/dummy/get_application_response_data.dart` holds fixture data.
- Coverage: `melos test:mybispro` = `include_unreached_coverage.dart` (adds unreached files),
  `flutter test --coverage --no-pub --reporter failures-only --fail-fast`, then
  `combine_coverage.dart` which removes `**/*.g.dart` and `**/*.freezed.dart`
  (`pubspec.yaml:291-301`, `scripts/combine_coverage.dart:3-5`).
- No coverage threshold anywhere (`grep -rn "min_coverage|threshold" .github scripts` = 0).
  The PR comment comes from `kefasjw/lcov-pull-request-report@v1` with `continue-on-error: true`
  (`workflow-test-coverage-check.yml:74-80`).
- No `--test-randomize-ordering-seed`. `--fail-fast` is on.

## 13. Lint and guardrails

- Single root `analysis_options.yaml` (`include: strict_lint.yaml`, a vendored copy of the `lint`
  package rules). `mybispro/analysis_options.yaml` does not exist, so the root file applies.
- `very_good_analysis ^10.0.0` is a root dev dependency (`pubspec.yaml:30`) but is **not** the
  included rule set.
- Excludes: `shared_lib/http_certificate_pinning`, `**/app_localizations*.dart`, `**.g.dart`,
  `**.freezed.dart` (`analysis_options.yaml:4-8`).
- Downgraded to ignore: `depend_on_referenced_packages`, `deprecated_member_use`,
  `use_late_for_private_fields_and_variables`, `invalid_annotation_target`,
  `use_build_context_synchronously`, `avoid_classes_with_only_static_members`
  (`analysis_options.yaml:9-15`). `strict-casts: true` (`strict_lint.yaml:9`).
- No `custom_lint`, no `riverpod_lint`.
- CI: `melos analyze:mybispro` = `flutter analyze --fatal-infos --fatal-warnings --no-pub`
  on the category and on `mybispro/` (`pubspec.yaml:152-155`), `melos format:mybispro` with
  `--set-exit-if-changed` (`pubspec.yaml:124-127`), and `pubghost -d / -c / -t` dead-dependency,
  dead-code and dead-translation checks (`workflow-code-analysis-check.yml:104-138`, each gated
  by inputs, allowed to fail by `allow_*` inputs). `pubghost.ignore_dependencies` lists 4 build
  packages (`mybispro/pubspec.yaml:83-88`).
- No check that generated files are up to date (no `build_runner` + `git diff` step found).

## 14. CI/CD

Workflows that start with `mybispro-` (4 files, 773 lines). None has a `permissions:` block.
Flutter `3.35.0` everywhere. No workflow sets the Android `versionCode`/`versionName` for DEV,
SIT or UAT builds. Those builds carry pubspec `1.0.0+1`.

### 14.1 `mybispro-trunk-pipeline.yml` (91 lines) - "Trunk CD Pipeline to DEV"

- Trigger: push to `master`, paths `mybispro/**`, excluding changelogs and workflows (lines 2-10).
  Shared package changes do **not** trigger it.
- Job `build-and-deploy`, `ubuntu-latest`, environment `sharia_dev_mybispro`.
- Java **11** (`setup-java@v3`, line 22, the other three use 17). Android SDK **33** via
  `amyu/setup-android@v2` (line 63) while `compileSdk` is 36.
- Steps: ssh key (`shimataro/ssh-key-action@v2`), `bluefireteam/melos-action@v2`, LCOV, then
  `melos bootstrap:shared_code`, `bootstrap:mybispro`, `test:shared_code`, `test:mybispro`
  (lines 50-55), keystore from `ANDROID_KEYSTORE_BASE64` + `ANDROID_KEYSTORE_PROPS_BASE64`
  (lines 65-72), `flutter build apk --flavor dev ... --obfuscate --split-debug-info --release`
  with 12 `--dart-define` (lines 74-91).
- Firebase dart-defines are **not** passed, so the DEV build calls `Firebase.initializeApp` with
  empty options. No distribution step, no artifact upload. The job builds and discards the APK.
- Secrets interpolated directly in `run:`: lines 81, 82, 85, 86, 88.
- `actions/checkout@v1` (line 17).

### 14.2 `mybispro-deploy-tag-cd-pipeline.yml` (194 lines) - "deploy tags to SIT & UAT"

- Trigger: push of tags `**-mybispro` (lines 6-7). Despite the name, every job uses environment
  `sharia_sit_mybispro` and flavor `sit`. UAT is a separate dispatch workflow.
- Jobs: `build-and-distribute-android` (ubuntu, Java 17), `build-ios` (`macos-latest`),
  `distribute-ios` (needs build-ios).
- Android: keystore from secrets (lines 41-48), `flutter build apk --flavor sit` with 21
  `--dart-define` incl. Firebase, `--obfuscate --split-debug-info --release` (lines 50-76),
  Firebase App Distribution group `sharia-mybispro` via `wzieba/Firebase-Distribution-Github-Action@v1`
  with `debug: true` (lines 78-85), `upload-artifact@v4` of the APK, 1 day (lines 87-92).
- iOS: `apple-actions/import-codesign-certs@v1` (p12 from `IOS_CERTIFICATES_BASE64` /
  `IOS_CERTIFICATES_SECRET`), provisioning profile and `ExportOptions.plist` written from base64
  secrets with `echo ... | base64 --decode` (lines 106-120), `flutter build ios --flavor sit`
  (lines 130-156), `xcodebuild ... archive` with `DEVELOPMENT_TEAM`, `PROVISIONING_PROFILE`,
  `CODE_SIGN_IDENTITY` from secrets on the command line (line 164), export, upload `mybispro.ipa`
  artifact (1 day), then App Distribution in `distribute-ios` (lines 188-194).
- No Xcode version pin (runner default). No symbol upload to Datadog in this workflow.
- Secrets interpolated directly in `run:`: lines 57, 58, 61, 62, 64-70, 137, 138, 141, 142,
  144-150, 164.
- `actions/checkout@v2`.

### 14.3 `mybispro-uat-promote-tag-pipeline.yml` (194 lines)

- Trigger: `workflow_dispatch` with input `tag` (lines 3-8). `branches: [release*]` under
  `workflow_dispatch` has no effect in Actions.
- Same three jobs as 14.2 with environment `sharia_uat_mybispro`, flavor `uat`, Java 17,
  App Distribution group `sharia-mybispro` (lines 189-194). 22 `--dart-define` per build.
- Secrets in `run:`: same pattern as 14.2 (lines 61-75, 141-155, 165).
- GitHub API: **0 runs ever** for this file (section 14.6). UAT builds have never gone through it
  under this file name.

### 14.4 `mybispro-promot-prod-pipeline.yml` (294 lines)

- Trigger: `workflow_dispatch` inputs `tag`, `version`, `is_adhoc` (bool) (lines 3-15).
- Job `approval-prod`: `trstringer/manual-approval@v1`, `minimum-approvals: 2`, 9 named
  approvers (simukti, subhanbfi, hendry-bfi, okky-bfi, ariesatya, ahmadwahyudi-bfi, fika24,
  irawanse0372, Michaelchristian1991), token `GH_PAT` (lines 18-27). This is an issue-based
  approval, not a GitHub environment protection rule.
- Job `build-android` (needs approval), runner `ubuntu-22-8core`, Java 17,
  `android-actions/setup-android@v3` + `sdkmanager` installs `platforms;android-36`,
  `build-tools;36.0.0`, `ndk;28.0.12433566` (lines 52-62) while `build.gradle` asks for NDK
  27.0.12077973. Version set by `fjogeleit/yaml-update-action@main` writing `inputs.version` into
  `mybispro/pubspec.yaml` `version` (lines 86-92, action pinned to a **branch**).
  `flutter build appbundle` (or `apk` when ad-hoc) `--flavor prod` with 22 `--dart-define`
  incl. `SHA_256_FINGERPRINT`, `--obfuscate --split-debug-info --release` (lines 94-123).
  Artifact upload (1 day). `npm install -g @datadog/datadog-ci` unpinned (line 133).
  `datadog-ci flutter-symbols upload --service-name id.co.bfi.sharia.mybispro` with Dart symbols
  and `mapping.txt` (lines 135-146). Play upload `r0adkll/upload-google-play@v1`, track
  `internal`, service account `BRAVO_GCP_SA_KEY` (lines 148-156), skipped when ad-hoc.
- Job `build-ios` (needs approval), runner `macos-26`, `maxim-lobanov/setup-xcode@v1` with
  `latest-stable` (not pinned), certs / profile / ExportOptions from secrets (ad-hoc variants
  chosen by `is_adhoc`), version via yaml-update-action, `flutter build ios --flavor prod`
  `--release` or `--profile` when ad-hoc (lines 218-246), archive, export, artifact,
  `apple-actions/upload-testflight-build@v1` with App Store Connect API key secrets (lines
  267-274), datadog-ci symbols with dSYMs (lines 279-290), then the Crashlytics step that
  references files not in the repo (lines 292-294).
- Secrets in `run:`: lines 103-105, 108, 109, 111-117, 226-228, 231, 232, 234-240, 254.
- Order problem: on Android, the Play upload step comes **after** the Datadog symbol upload.
  The last prod run failed at "Upload android symbol to datadog", so the Play step never ran.
  On iOS, TestFlight upload comes before the Datadog and Crashlytics steps, so the iOS build was
  uploaded before the job turned red.

### 14.5 Third-party actions (tag-pinned, none by SHA)

`actions/checkout@v1/@v2/@v4`, `actions/setup-java@v3`, `subosito/flutter-action@v2`,
`shimataro/ssh-key-action@v2`, `bluefireteam/melos-action@v2`, `hrishikesh-kadam/setup-lcov@v1`,
`amyu/setup-android@v2`, `android-actions/setup-android@v3`, `wzieba/Firebase-Distribution-Github-Action@v1`,
`actions/upload-artifact@v4`, `actions/download-artifact@v4`, `apple-actions/import-codesign-certs@v1`,
`apple-actions/upload-testflight-build@v1`, `trstringer/manual-approval@v1`,
`fjogeleit/yaml-update-action@main` (branch), `maxim-lobanov/setup-xcode@v1`,
`r0adkll/upload-google-play@v1`.

Secret handling: keystore, keystore properties, provisioning profile and ExportOptions are
written to disk with `echo $VAR | base64 -d` from `env:` vars (acceptable), but the keystore
is also written into the workspace at `mybispro/android/keystore.jks`. No `upload-artifact` of
keystores or certificates. No `sed` of secrets. The whole `flutter build` line including
`CLIENT_SECRET`, Datadog and Firebase keys is a `run:` interpolation (GitHub masks known secret
values in logs, but the expansion happens in the shell script).

### 14.6 GitHub API (read-only, 26 Oct 2026)

| Workflow | Total runs | Last run | Conclusion | Failed step (job metadata) |
|---|---|---|---|---|
| mybispro-trunk-pipeline.yml | 11 | 2026-10-02 (push master) | failure | `Setup Android SDK` |
| mybispro-deploy-tag-cd-pipeline.yml | 19 | 2026-06-19 (tag v1.8.0-rc.4-mybispro) | failure | Android: `Upload Artifact to BRAVO Firebase App Distribution`. iOS: `Build iOS SIT` |
| mybispro-uat-promote-tag-pipeline.yml | 0 | never | - | - |
| mybispro-promot-prod-pipeline.yml | 14 | 2026-06-19 (dispatch) | failure | Android: `Upload android symbol to datadog`. iOS: `Upload crashlytics symbols`. Approval: success |

The last 5 runs of trunk, deploy-tag and prod are all `failure` (dates: trunk 2026-10-02,
09-22, 06-09, 04-21 x2. deploy-tag 06-19, 06-18 x2, 04-21 x2. prod 06-19, 04-21 x2, 04-14 x2).
Step names come from the jobs API, not from logs. Why each step failed is not known.

Run totals look low for 801 commits. The API also lists an active workflow
`mybispro-pr-pipeline.yml` ("MyBisPro CI PR") whose file no longer exists on master, so some
history sits under deleted or renamed files. Not investigated further.

Environments containing `mybispro`: `sharia_dev_mybispro`, `sharia_sit_mybispro`,
`sharia_uat_mybispro`, `sharia_prod_mybispro`. All four return `protection_rules: []` and
`deployment_branch_policy: null`. No required reviewers, no wait timer, no branch policy on the
prod environment. The only prod gate is the `manual-approval` action.

Tags: 418 tags match `*mybispro*`. Latest three: `v1.8.0-rc.4-mybispro` (2026-06-19),
`v1.8.0-rc.3-mybispro` (2026-06-18), `v1.8.0-rc.2-mybispro` (2026-06-18). `mybispro/CHANGELOG.md`
top entry is `1.8.0-rc.4-mybispro` (2026-06-19). No tag since June 2026. Last commit touching
`mybispro/` is `b1e870ad3` on 2026-10-02 (1 commit in the last 90 days, 801 in total since
2023-02-20).

### 14.7 PR checks that apply to mybispro

- `pr-check-code-analysis.yml` and `pr-check-test-coverage.yml` trigger on paths incl.
  `mybispro/**/*.dart` (line 12 in both), call `workflow-map-changes-context.yml`
  (`dorny/paths-filter@v3`) whose `mybispro` filter is `mybispro/**` plus `shared_data/agency`,
  `agent_marketing`, `document`, `keycloak`, `onboarding`, `user_iam`, `sso`, `shared_lib/core`,
  `shared_lib/http_certificate_pinning`, `ui_theme` (`workflow-map-changes-context.yml:58-69`),
  then run `workflow-code-analysis-check.yml` (format, analyze, pubghost) and
  `workflow-test-coverage-check.yml` (`melos test:mybispro`, lcov PR comment) per matched app.
  `pr-merge.yml` runs the coverage workflow again on merge.
- `.github/actions/map-deployment-env` maps `mybispro_{dev,sit,uat,prod}` to the four
  `sharia_*_mybispro` environments (lines 42-45).
- Coverage threshold: none. Test randomisation: none. Generated-files check: none.
- Shared workflows `tag-release-pipeline.yml` (changelog + tag, `mybispro` branch at lines
  64-67), `debugger.yaml`, `test.yaml`: covered on the sister pages.

## 15. Dependencies

- Git dependency: `flutter_jailbreak_detection` from `git@github.com:bfi-finance/bfi-flutter-packages.git`,
  ref `55bba36de6e68e86d5e02c76865deb25286daa2a`, path `packages/flutter_jailbreak_detection`,
  version 0.0.1 (`mybispro/pubspec.yaml:30-34`). SSH URL, hence the `ssh-key-action` step in CI.
- Vendored plugin: `shared_lib/http_certificate_pinning` 2.0.6 (fork of
  `diefferson/http_certificate_pinning`), reached through `core` (`shared_lib/core/pubspec.yaml:18-19`).
  `pubspec.lock:965-971` marks it `direct overridden`.
- `dependency_overrides`: none in `mybispro/pubspec.yaml` or root. One in
  `shared_data/agent_marketing/pubspec.yaml:27-28` (`frontend_server_client: ^4.0.0`, "fix for
  melos generate"). No `pubspec_overrides.yaml` files.
- Older majors still in use (locked): `share_plus` 7.2.2, `mime` 1.0.6, `intl` 0.20.2,
  `freezed` 2.5.8 (3.x exists), `go_router` 14.8.1, `geolocator` 13.0.4, `flutter_riverpod` 2.6.1
  (3.x exists), `visibility_detector` 0.4.0+2, `http_proxy` 1.2.3. Discontinued status on pub.dev
  not verified from this machine.
- Firebase 4.x/16.x/6.x line is current (Sept 2026 majors).
- Packages imported but not declared: 0 (`grep import 'package:X/'` vs pubspec, after allowing
  `flutter` and `mybispro`). Riverpod, dio and freezed_annotation reach the app through
  `core`'s exports, which the lint `depend_on_referenced_packages` would flag but it is set to
  ignore (`analysis_options.yaml:10`).
- `google-services` Gradle plugin is declared in `android/settings.gradle:23` but never applied in
  `app/build.gradle`. Firebase is configured purely from dart-defines.
- `gradle.properties` has `android.suppressUnsupportedCompileSdk=35` while compileSdk is 36
  (stale). AGP 8.7.0, Kotlin 2.1.0, Gradle 8.10.2, `-Xmx6g`.

## 16. Other

- TODO/FIXME/HACK in `lib`: 5. Notable: `lib/features/agent/model/create_agent_model.dart:1`
  "remove this when create agent API is ready", `lib/features/agent/model/npwp_verification_result_model.dart:1`
  "Need to be revisit when implementing data", `lib/features/maintainagent/reportform/upload_image_field.dart:182`
  "hit upload service" (upload not wired). The other 2 are minor.
- Dummy data: l10n key `dummyCreditAnalystNote` ("dummy credit analyst note") is set as the
  credit-analyst note by `lib/features/editloan/form/edit_loan_form_controller.dart:55` and shown
  by `edit_loan_form_screen.dart:931`. A placeholder text reaches a production form.
  `create_agent_model.dart` is a placeholder model per its TODO. Test fixtures in
  `test/src/dummy/`.
- README: root `README.md:16` says "`mybispro`, a MyBisPro flutter application for BFI Employee
  with CMS role, owner: Sharia" and lists the folder at line 39. No `mybispro/README.md`. The
  root README does not describe the mybispro pipelines or flavors.
- Translations: one ARB, `lib/app/localizations/app_id.arb` (Indonesian, 882 keys), template
  `app_id.arb`, `nullable-getter: false` (`l10n.yaml`). Single locale. Generated files are
  committed in `lib/app/localizations/`.
- Platforms: `android/` and `ios/` only. No `web/`, `macos/`, `linux/`, `windows/`.
- MyShaf: tags `*-myshaf` and `myshaf-*` workflows exist in the same repo, but those workflows
  build `agent_tools/` (`myshaf-deploy-tag-cd-pipeline.yml:58-62`), not `mybispro/`. The
  `myShafRoute` inside mybispro (`router.dart:135`) is a screen, not the MyShaf app.
- `FirebaseMessaging.requestPermission()` is called in `main` before any UI
  (`main.dart:124`), so the iOS push permission prompt appears at first launch.
- Branding: namespace and bundle id use `sharia`, the app label is "MyBisPro" (`build.gradle:77`).
- Google Maps Android renderer forced to `latest` with `useAndroidViewSurface = true`
  (`main.dart:36-40`).

## 17. Open questions

1. Why every recent run of all three active mybispro workflows failed (trunk: Android SDK setup.
   deploy-tag: App Distribution and iOS build. prod: symbol uploads). Needs the run logs, which
   this sheet did not open.
2. Whether any MY BISPRO build reached Play `internal` or TestFlight since June 2026. The API
   shows no successful prod run in the last 5. Store consoles were not checked.
3. Where UAT builds come from, given `mybispro-uat-promote-tag-pipeline.yml` has 0 runs.
4. The real values of `vars.FEATURE_ENABLE_PROXY` and `vars.DATADOG_SAMPLING_RATE` per
   environment (repo variables, not in code).
5. Whether Flutter's Gradle plugin default enables R8 for this `build.gradle` (no explicit
   `minifyEnabled`). The prod workflow expects `mapping.txt`, which suggests yes.
6. Whether Datadog RUM records dio resources at all, since only `dart:io` tracking is enabled
   and no dio interceptor was found.
7. Whether `DatadogLog.e` creating loggers without logging is known to the squad (108 call
   sites, plus the provider observer).
8. Whether the `FEATURE_ENABLE_JAILBREAK_DETECTION` vs `FEATURE_JAILBREAK_DETECTION` mismatch is
   intentional (detection always on).
9. History under the deleted `mybispro-pr-pipeline.yml` and any renamed workflow files.
10. pub.dev discontinued status of `dotted_line`, `dotted_border`, `custom_refresh_indicator`,
    `flutter_downloader`, `http_proxy` (not checked from this machine).
