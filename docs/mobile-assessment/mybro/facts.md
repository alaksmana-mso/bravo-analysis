# myBRO (RO Tools) fact sheet

Repo `bfi-finance/bravo-ro-tools-apps`, local checkout at
`/Users/mac-6000202/Documents/BFI_GITHUB/squads/Tele Marketing/bravo-ro-tools-apps`,
master @ `9617214` (19 Oct 2026). Read-only review on 26 Oct 2026. No build was run.
Paths below are relative to the repo root unless they start with `/`.

How to read this sheet:

- Every number comes from a `grep`, `find`, `wc` or `git` command on the checkout, or from the GitHub REST API via `gh api`.
- "not found" means the grep returned zero. It does not prove the thing does not exist.
- "not verified" means I could not check it from the files.
- Secret values are never printed. Secret names and line numbers are.

Orientation documents read first:

- `README.md` (root). Written for the monorepo era. Several claims are stale, see section 16.
- `ro_tools/CLAUDE.md`. Only contains Graphify rules. It points at `ro_tools/graphify-out/`, which does not exist in this checkout.
- `.github/copilot-instructions.md:3` says "4 production applications". This repo holds one. The file is a copy from `bravo-agency-app`.

## 1. Scope

| Item | Value | Evidence |
|---|---|---|
| pubspec name | `rotools` | `ro_tools/pubspec.yaml:1` |
| version line | `3.50.3+1078` | `ro_tools/pubspec.yaml:4` |
| README version claim | `3.39.2+1060` (stale) | `README.md` "Current Version" |
| Android applicationId | `id.co.bfi.ro.rotools`, suffixes `.sit` `.dev` `.uat`, prod none | `ro_tools/android/app/build.gradle:57,68-100` |
| iOS bundle ids | `id.co.bfi.ro.rotools` + `.dev` `.sit` `.uat` (3 configs each) | `grep PRODUCT_BUNDLE_IDENTIFIER ro_tools/ios/Runner.xcodeproj/project.pbxproj` |
| Dart SDK | `>=3.9.0 <4.0.0` | `ro_tools/pubspec.yaml:7` and root `pubspec.yaml:4` |
| Flutter in CI | `3.47.0` everywhere | all build workflows and `.github/actions/setup-codebase/action.yml:22` |
| flutter_riverpod | NOT declared in `ro_tools/pubspec.yaml`. Comes through `core` (`shared_lib/core/pubspec.yaml:15` `^2.1.1`, re-exported at `shared_lib/core/lib/core.dart:3`). Root `pubspec.lock` resolves `2.6.1` | grep |
| hooks_riverpod, riverpod_annotation | not found | grep |
| bloc | not found | grep |
| dio | `^5.4.0` (root lock `5.9.0`) | `ro_tools/pubspec.yaml:18` |
| go_router | `^14.8.0` | `ro_tools/pubspec.yaml:40` |
| auto_route | not found | grep |
| freezed / freezed_annotation | `^4.0.1` / `^3.1.0` | `ro_tools/pubspec.yaml:34,67` |
| firebase_core / analytics / crashlytics / messaging / remote_config | `^4.1.0` / `^12.0.1` / `^5.0.1` / `^16.0.1` / `^6.0.1` | `ro_tools/pubspec.yaml:22-27` |
| datadog_flutter_plugin / datadog_tracking_http_client | `^2.8.0` / `^2.2.0` | `ro_tools/pubspec.yaml:15-16` |
| melos | `^7.1.0` as root dev dep. Config lives in root `pubspec.yaml` under `melos:`. No `melos.yaml` file | root `pubspec.yaml:15,22-170` |
| app lockfile | `ro_tools/pubspec.lock` is git-ignored (`ro_tools/.gitignore` line `pubspec.lock`). Only the root lock (workspace packages) is tracked. App dependency versions are not pinned in git | `git ls-files` |

Code size (`ro_tools/lib`):

| Measure | Value | Command |
|---|---|---|
| Dart files | 1,202 | `find ro_tools/lib -name '*.dart' \| wc -l` |
| Generated files (`*.g.dart`, `*.freezed.dart`) | 448 files, 111,936 lines, all committed | `find` + `git ls-files` (448) |
| l10n generated (`app_localizations*.dart`) | 11,902 lines, committed | `wc -l` |
| Hand-written lines (excl. generated and l10n) | 112,371 | `find ... ! -name '*.g.dart' ! -name '*.freezed.dart' ! -name 'app_localizations*' \| xargs cat \| wc -l` |
| `*.gr.dart`, `*.config.dart` | none (no auto_route, no injectable) | find |

Feature folders (hand-written files / lines):

| Feature | Files | Lines |
|---|---|---|
| app/ (shared app code, data layer, widgets) | 376 | 42,012 |
| loan | 86 | 20,548 |
| activity | 61 | 16,163 |
| spv | 63 | 12,951 |
| ro_database | 22 | 7,449 |
| more_action | 22 | 5,222 |
| contact_detail | 21 | 3,403 |
| search | 12 | 1,762 |
| performance | 13 | 1,423 |
| guidance | 10 | 1,360 |
| notification | 9 | 1,265 |
| new_collateral | 3 | 1,109 |
| upload_file | 7 | 1,067 |
| login | 3 | 1,057 |
| complete_address | 2 | 1,052 |
| sa | 6 | 970 |
| home | 8 | 854 |
| calculation_tse | 2 | 755 |
| account | 4 | 704 |
| submission | 3 | 511 |
| geofencing | 5 | 506 |
| request_detail | 3 | 419 |
| splash | 3 | 336 |
| change_price_list | 2 | 317 |
| file_viewer | 2 | 256 |
| activity_detail | 2 | 199 |
| pbf | 1 | 196 |
| temporary_screens | 1 | 86 |
| asset_detail | 1 | 59 |

Top 8 hand-written files:

| Lines | File |
|---|---|
| 2,635 | `ro_tools/lib/features/loan/proposal/calculator/loan_proposal_calculator_screen.dart` |
| 2,589 | `ro_tools/lib/features/loan/proposal/calculator/loan_proposal_calculator_controller.dart` |
| 2,321 | `ro_tools/lib/features/loan/offering/calculator/loan_offering_calculator_controller.dart` |
| 1,792 | `ro_tools/lib/features/loan/offering/calculator/loan_offering_calculator_screen.dart` |
| 1,785 | `ro_tools/lib/app/widget/notification/notification_card.dart` |
| 1,724 | `ro_tools/lib/features/activity/activity_app_bar.dart` |
| 1,336 | `ro_tools/lib/app/common/exceptions.dart` |
| 1,300 | `ro_tools/lib/features/activity/contact/contact_list_controller.dart` |

Router: `ro_tools/lib/app/navigation/router.dart` (class `AppRouter`, GoRouter) plus
`cre_routes.dart`, `pbf_routes.dart`, `sa_routes.dart`, `spv_routes.dart` in the same folder.
32 `GoRoute(` and 1 `ShellRoute(` across `lib` (grep). Initial location `/splash` (`router.dart:46`).
Navigator key comes from a singleton `NavigationService.instance.navigationKey` (`router.dart:47`).

## 2. Repo layout

Packages (root `pubspec.yaml:6-10` workspace list, `resolution: workspace` in each):

| Package | Path | Hand-written lines / files | Tests |
|---|---|---|---|
| rotools (app) | `ro_tools/` | 112,371 / 754 | 441 test files |
| core | `shared_lib/core` | 729 / 15 | 1 |
| http_certificate_pinning | `shared_lib/http_certificate_pinning` (vendored copy of `diefferson/http_certificate_pinning` 2.0.6, see its `pubspec.yaml:3-4`) | 284 / 5 | 0 |
| sso | `shared_data/sso` | 549 / 6 | 0 |
| keycloak | `shared_data/keycloak` | 799 / 11 | 1 |
| ui_theme | `ui_theme` | 4,468 / 41 | 13 |

Path deps from the app: `core`, `keycloak`, `sso`, `ui_theme` (`ro_tools/pubspec.yaml:12,47,59,63`).
`core` depends on `http_certificate_pinning` by path (`shared_lib/core/pubspec.yaml:17`).
`sso` and `keycloak` depend on `core` by path.

Copies of the agency monorepo packages. Compared with
`/Users/mac-6000202/Documents/BFI_GITHUB/squads/Agency/bravo-agency-app` (master @ `1e50b8191`, 22 Oct 2026)
using `diff -rq` excluding build output, generated files and lockfiles:

| Package | Verdict | Detail |
|---|---|---|
| `shared_lib/http_certificate_pinning` | same | 25 files each, 0 differ |
| `ui_theme` | same code, pubspec differs | 171 vs 172 files (agency has a stray `.DS_Store`), only `pubspec.yaml` differs (4 lines) |
| `shared_lib/core` | drifted, agency moved ahead | agency 23 files, RO 19. Agency adds `lib/src/ui/reference_id_block.dart`, `test/src/network/exceptions_test.dart`, `test/src/network/http_client_test.dart`. `http_client.dart` 42 changed lines (agency has `addInterceptor`, `XFile` multipart for web, `x-correlation-id` capture). `exceptions.dart` 20 lines (agency 47 vs RO 29). `core.dart` exports one more file. `pubspec.yaml` 9 lines |
| `shared_data/sso` | drifted | `sso_http_client.dart` 17 lines (agency has `addInterceptor`), `sso_repository.dart` 16 lines, `analysis_options.yaml`, `pubspec.yaml` |
| `shared_data/keycloak` | drifted | `keycloak_http_client.dart` 17 lines, `analysis_options.yaml`, `pubspec.yaml` |

The agency monorepo still has `remotes/origin/archived/ro_tools` and `remotes/origin/rotools-rodatabase` branches (`git branch -a` in that repo).

Cross-feature imports (imports of `package:rotools/features/<other>/` from inside `lib/features/<feature>/`):

- 198 import lines across 66 directed pairs.
- Top pairs: loan -> more_action 19, activity -> spv 11, ro_database -> search 8, more_action -> upload_file 8, activity -> search 8, ro_database -> spv 7, loan -> geofencing 7, contact_detail -> more_action 6, contact_detail -> geofencing 6, activity -> loan 6, activity -> geofencing 6, contact_detail -> loan 5.
- Two-way pairs (8): activity <-> contact_detail, activity <-> loan, activity <-> notification, activity <-> spv, contact_detail <-> loan, contact_detail <-> spv, loan <-> more_action, ro_database <-> spv.
- Inverted layering: 26 files under `lib/app/` import `lib/features/` (activity 17, geofencing 11, spv 10, contact_detail 5, ro_database 4). 335 feature files import `lib/app/`.

What lives in `shared_lib/core` (`shared_lib/core/lib/core.dart:1-18`): re-exports of `clock`, `collection`, `flutter_riverpod`. Set and string extensions. Models `PagedList`, `PagedListWithTotal`, `Paginated`, `Pair`. Network: `HttpClient` (Dio wrapper), `NetworkConfig`, exceptions, RFC3339 and dynamic-to-string converters, `tryParseDateTime`. `secureStorageProvider`. `AppPreferencesDataSource` (shared_preferences).

## 3. Layering

- Domain layer: no folder named `domain`, `usecase`, `use_case` or `entit*` under `ro_tools/lib` (`find -type d -iname`). Not found.
- Structure is `app/data/<area>/{<area>_repository.dart, model/*.dart}` plus `features/<feature>/{*_screen.dart, *_controller.dart, widgets}`. Counts: 29 `model` dirs, 27 `*_repository.dart`, 94 `*_controller.dart`, 103 `*_screen.dart`.
- Files that call repository providers directly (`ref.read|watch(<X>Repository.provider`): 86. Of those, 0 are `*_screen.dart`, widget or bottom-sheet files. Repositories are reached from controllers and providers only.
- Screens and controllers that use `*Response` DTO types: 46 screens, 71 controllers (grep `[A-Za-z]Response\b`). Examples:
  - `ro_tools/lib/features/change_price_list/change_price_list_screen.dart:18` `final AgreementCollateralResponse asset;`
  - `ro_tools/lib/features/account/account_screen.dart:75` `Widget _content({GetUserAgentResponse? profile})`
  - `ro_tools/lib/features/performance/performance_screen.dart:69` `const SummaryPlanActivityResponse()`
  - `ro_tools/lib/features/change_price_list/change_price_list_controller.dart:39,45` builds `GetAssetResponse` by hand.
- Mappers: 7 files match `*mapper*`. `lib/app/mapper/` holds `custom_error_mapper`, `enum_mapper`, `error_data_mapper`, `form_to_map`, `remote_config_mapper`.
- Where business rules live: in `StateNotifier` controllers that consume DTOs directly. Three biggest:
  1. `loan/proposal/calculator/loan_proposal_calculator_controller.dart` 2,589 lines
  2. `loan/offering/calculator/loan_offering_calculator_controller.dart` 2,321 lines
  3. `activity/contact/contact_list_controller.dart` 1,300 lines
  (next: `activity/prospect/prospect_list_controller.dart` 1,193, `ro_database/filter/ro_database_filter_controller.dart` 1,069). All 94 controllers total 27,560 lines.

## 4. State management

Greps over hand-written `ro_tools/lib` files:

| Pattern | Count |
|---|---|
| `extends StateNotifier<` | 95 |
| `StateNotifierProvider` | 95 |
| `extends Notifier<`, `extends AsyncNotifier<`, `extends AutoDisposeNotifier<` | 0 |
| `StateProvider` | 0 |
| `ChangeNotifier` | 0 |
| `FutureProvider` | 6 |
| `StreamProvider` | 0 |
| `Provider<` | 8 |
| `static final .*Provider` (single line) | 42 (many providers wrap to the next line, so the true count of `static final provider =` is higher) |
| `ConsumerWidget` | 38 |
| `ConsumerStatefulWidget` | 145 |
| `HookConsumerWidget` | 0 |
| `ref.listen` | 300 |
| `ref.read(` | 648 |
| `ref.watch(` | 1,214 |
| `appRef` | 0 |
| `navigatorKey` | 1 (`router.dart:47`), `GlobalKey<NavigatorState>` 2 (`NavigationService` singleton) |
| `ref.watch(` within 3 lines after `onPressed:`/`onTap:`/`onChanged:` | 2 (heuristic) |
| `ref.read(` within 25 lines after `Widget build(BuildContext context` | 22 (heuristic, includes legitimate reads in callbacks) |

Riverpod 2 legacy style throughout: `StateNotifier` + freezed state, providers as `static final provider` on the class.
No code generation for providers. Provider observers: `ErrorLogProviderObserver` (Datadog) and `RiverpodCrashlyticsObserver` (`ro_tools/lib/main.dart:255`).
A `NavigationService` singleton exposes the navigator key (`lib/app/navigation/navigation_service.dart`).

## 5. Dependency injection

`ro_tools/lib/main.dart:233-258` builds `ProviderScope(overrides: [...])`:

| Override | Line | What it injects |
|---|---|---|
| `AppConfig.provider.overrideWithValue(_appConfig(deviceInfo))` | 237 | 22 compile-time feature flags + device info |
| `HttpClient.authProvider.overrideWith(...)` | 238-249 | watches `AppController.provider` -> `roRemoteConfigValue.roFfSsoLogin`. True -> `SsoHttpClient.provider`, false -> `KeycloakHttpClient.provider` |
| `SsoConfig.provider.overrideWithValue(_ssoConfig)` | 250 | client id, login/token/logout URLs from dart-define, redirect `com.rotools.app://auth/callback` (line 77) |
| `KeycloakConfig.provider.overrideWithValue(_keycloakConfig)` | 251 | client id, client secret, realm, login URL from dart-define |
| `NetworkConfig.provider.overrideWithValue(_networkConfig)` | 252 | scheme, host, port, SHA-256 fingerprint list |
| `secureStorageProvider.overrideWithValue(_secureStorage)` | 253 | `FlutterSecureStorage` with `encryptedSharedPreferences: true, resetOnError: true` (lines 107-112) |

Interfaces and ports: `HttpClient` is a concrete class (`shared_lib/core/lib/src/network/http_client.dart:8`).
`SsoHttpClient implements HttpClient` and `KeycloakHttpClient implements HttpClient` use the Dart implicit interface.
`HttpClient.authProvider` throws `UnimplementedError` until overridden (`http_client.dart:34-36`), same for `NetworkConfig.provider` (`network_config.dart:12-16`).
`HttpClient.krakendHttpClientProvider` and `nonAuthKrakendHttpClientProvider` exist in core (`http_client.dart:38-46`) but are not referenced in `ro_tools/lib` (grep 0).
No abstract repository ports. Repositories are concrete classes with a `static final provider`.
The auth client choice depends on a Remote Config value that is only known after `AppController` fetches it. Before that the default `roFfSsoLogin` is `false` (`ro_remote_config_value.dart:33`), so Keycloak is used.

## 6. Analytics

- Wrapper: `AnalyticsServices` (`ro_tools/lib/app/analytics/analytics_services.dart`), Firebase Analytics only. Mixpanel not found.
- `logEvent` call sites outside the wrapper: 27 (grep `logEvent(`).
- Event names: 24 constants in `ro_tools/lib/app/data/analytics/log_event_name.dart` with a uniqueness guard. Names are mixed English and Indonesian, e.g. `user_click_login`, `user_login_successfully`, `user_click_RO_Database`, `user_click_customer_card`, `user_click_lanjutkan`, `user_click_buat_penawaran`, `user_click_ajukan_pembiayaan`, `user_click_phone_number_customer`, `trigger_on_debounce_triggered`.
- User id: `setUserId(id: userData.userId)` and user property `user_role` (`analytics_services.dart:22-25`). Default event parameters are the whole `UserData` json: `agent_id`, `agent_name`, `bravo_agent_id`, `user_id`, `user_role` (`analytics_services.dart:45-51`, model at `base_analytics_model.dart:79-87`). `agent_name` is a person name sent on every event.
- Parameter sanitiser `_AnalyticsSanitizer` (`base_analytics_model.dart:34-77`) caps 25 params, key 40 chars, value 100 chars. It does not redact PII.
- Navigation observers: `FirebaseAnalyticsObserver` (`analytics_services.dart:15-18`) and `DatadogNavigationObserver` (`router.dart:38-43`) both attached to the `ShellRoute` (`router.dart:50`). Route name falls back to `'unnamed'`.
- Datadog RUM: `DatadogConfiguration` in `main.dart:84-98`. `applicationId` from dart-define `DATADOG_APP_ID`, `clientToken` from `DATADOG_CLIENT_TOKEN`, `site: DatadogSite.us5`, `env` and `flavor` from `FLAVOUR`, `firstPartyHosts: [API_HOST]`, `nativeCrashReportEnabled: true`. SDK only starts when the token is non-empty (`main.dart:51`). HTTP tracking enabled at `main.dart:222`.
- Datadog user info: `DDService.setUserInfo(id: state.username, email: agentData.email, name: agentData.name, extraInfo: {'role': ...})` (`ro_tools/lib/features/login/login_controller.dart:204-209`). `username` is the login identifier (the login screen logs an event named `user_click_NIK_field`, `log_event_name.dart:14`, so the username is likely the NIK). Not verified that `state.username` equals the NIK.

## 7. Logging and crashes

- Crashlytics init: `Firebase.initializeApp` with options from dart-define (`main.dart:184-193`), then `FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError` (`main.dart:212`). No condition, no `setCrashlyticsCollectionEnabled` (grep 0). Runs in every flavour.
- Firebase options use `ANDROID_FIREBASE_APP_ID`, `ANDROID_FIREBASE_API_KEY`, `ANDROID_FIREBASE_SENDER_ID` for both platforms. There is no iOS-specific option set.
- `runZonedGuarded` error handler sends only to Datadog (`DDService.e`), not to Crashlytics (`main.dart:58`).
- `RiverpodCrashlyticsObserver.onError` records every provider error as non-fatal (`crashlytics_service.dart:27-37`).
- Custom keys: `setCustomKey`, `setUserIdentifier` not found. Crashlytics has no user id or nik/phone/email keys.
- Datadog logs: `DDService.e` (`ro_tools/lib/app/dd_service.dart:36-50`) creates a new logger per call with `remoteLogThreshold: LogLevel.warning` and sends `error`, `StackTrace`, plus attributes `path` and `request` (a `Map<String, dynamic>`). 159 call sites. Whether request bodies with PII reach Datadog depends on each caller. Not verified per call site.
- `ErrorLogProviderObserver.didUpdateProvider` forwards every `AsyncValue` error to Datadog (`dd_service.dart:66-80`).
- Tracking consent: `TrackingConsent.granted` hard-coded (`main.dart:52`). No consent screen found.
- PII sanitiser for logs: not found. Only the analytics param clamp exists.
- `print`/`debugPrint`: 2 `debugPrint` in `lib/app/messaging/messaging_service.dart:77,124` (error text only), 1 `print` in `shared_lib/http_certificate_pinning/lib/src/http_certificate_pinning.dart:42` (method-channel args). `LogInterceptor`, `PrettyDioLogger`, `Alice`, `requestBody: true` not found. No request or response bodies are printed.
- `log(` from `dart:developer` is used in `app_controller.dart` for the Remote Config stream error.

## 8. Feature flags

Remote Config:

- `RemoteConfigRepository` (`ro_tools/lib/app/data/remote_config/remote_config_repository.dart`). Settings: `fetchTimeout` 1 min, `minimumFetchInterval` 1 h in release and 5 min in debug (lines 16-23). `forceFetchAndActivate` drops the interval to zero (lines 35-53). Live updates via `onConfigUpdated` (lines 56-66).
- Flag model: `RoRemoteConfigValue` in `ro_tools/lib/app/data/remote_config/data/ro_remote_config_value.dart`, 38 fields with `@Default` (grep `-c "@Default"`). Mostly `roFf*` booleans plus `roMaxMultipleAsset` int. Two fields carry explicit `@JsonKey(name: 'RO_FF_MULTI_ASSET_4W' / '2W')` (lines 34-35).
- Read path: `getAll()` -> `remoteConfigMapper(value.asString())` -> `RoRemoteConfigValue.fromJson` (lines 68-74, mapper in `lib/app/mapper/remote_config_mapper.dart`).
- Raw `getBool`/`getString`/`getInt` on `FirebaseRemoteConfig`: not found. (The `context.getString` hits are l10n.)
- 202 reads of `roFf*`/`roRemoteConfigValue.` across `lib` vs 20 reads of `featureFlag*` from `AppConfig` outside main/app_config.

Fallback bug: when the fetch fails, `AppController._getAllRoConfigs` builds the model from compile-time flags
(`ro_tools/lib/app/app_controller.dart:215-245`). Two fields are mis-mapped:
`roFfNotification: _appConfig.featureFlagActivityContact` (line 236) and
`roFfAllowNewVersionOfTaxStatus: _appConfig.featureFlagActivityContact` (line 242).

Compile-time dart-defines (43 distinct names, perl multi-line scan of `fromEnvironment(` across all packages):

- Infra: `API_SCHEME`, `API_HOST`, `API_PORT`, `FLAVOUR`, `SHA_256_FINGERPRINT`, `CLIENT_ID`, `CLIENT_SECRET`, `REALM_ID`, `KEYCLOAK_LOGIN_URL`, `KEYCLOAK_REDIRECT_URL`, `CLIENT_ID_SSO`, `SSO_LOGIN_URL`, `SSO_TOKEN_URL`, `SSO_LOGOUT_URL`, `DATADOG_CLIENT_TOKEN`, `DATADOG_APP_ID`, `ANDROID_FIREBASE_APP_ID`, `ANDROID_FIREBASE_API_KEY`, `ANDROID_FIREBASE_SENDER_ID`, `FIREBASE_PROJECT_ID`, `FLUTTER_DRIVER_ENABLED`.
- Flags (22): `FEATURE_FLAG_ACTIVITY_CONTACT`, `_ACTIVITY_PROSPECT`, `_ACTIVITY_FUNDING`, `_DATA_SECURITY`, `_LOAN_FUNDING_REDUCTION`, `_LOAN_OFFERING_FUNDING_REDUCTION`, `_ALLOW_MOCK_LOCATION`, `_SPV`, `_NOTIFICATION`, `_LOCK_REQUEST`, `_MULTI_ASSET`, `_ADD_ASSET`, `_PREVENT_EMULATOR`, `_EOM_CONTINUE_LOCK`, `_INSTALLMENT_TYPE`, `_ADD_COLLATERAL_2W`, `_KEYCLOAK_FORM_LOGIN`, `_CONVERT_RO_REGULAR_OFFERING`, `_ALLOW_NEW_VERSION_OF_TAX_STATUS`, `_SSO_LOGIN`, `_MULTI_ASSET_4W`, `_MULTI_ASSET_2W`.
- Three flags are read in code but never passed by any workflow, so they compile to `false`: `FEATURE_FLAG_ALLOW_NEW_VERSION_OF_TAX_STATUS`, `FEATURE_FLAG_MULTI_ASSET_2W`, `FEATURE_FLAG_MULTI_ASSET_4W` (grep over `.github/workflows`).
- `FEATURE_FLAG_PREVENT_EMULATOR` and `FEATURE_FLAG_SSO_LOGIN` are read at top level in `main.dart:62-66`.

## 9. Networking

- `HttpClient` (`shared_lib/core/lib/src/network/http_client.dart`): Dio, base URL from `NetworkConfig` (`Uri(scheme, host, port)`, lines 10-14), `connectTimeout`/`sendTimeout`/`receiveTimeout` 30 s each (lines 15-17), `Accept: application/json`. `CertificatePinningInterceptor` added only when `sha256Fingerprint` is non-empty (lines 22-28). Methods get/post/postV2/patch/put/delete/download. `_transformError` maps Dio timeouts to `ConnectionTimeoutException` and bad status to `HttpStatusCodeException` (lines 217-252).
- Auth decorators:
  - `SsoHttpClient` (`shared_data/sso/lib/src/sso_http_client.dart`): before every call `getValidAccessToken()` (`sso_repository.dart:36-67`): returns cached token if not expired (JWT exp), else refreshes with the refresh token, on any refresh exception clears the session and throws `SessionExpiredException`. A 401 on the real call clears the session and throws `SessionExpiredException` (`sso_http_client.dart:184-198`). No retry of the failed request.
  - `KeycloakHttpClient` (`shared_data/keycloak/lib/src/keycloak_http_client.dart`): before every call `refreshToken()` (`keycloak_repository.dart:54-68`): if the refresh token is past its stored expiry -> clear session + throw, else if the access token is past its stored expiry -> call refresh endpoint. 401 -> clear session + `SessionExpiredException` (`keycloak_http_client.dart:185-199`). No retry.
  - Expiry for Keycloak is computed from server-returned lifetimes and the device clock (`keycloak_repository.dart:94-103`).
- Retry interceptor: not found (`RetryInterceptor`, `maxRetries`).
- Client variants: `HttpClient.provider` (no auth), `HttpClient.authProvider` (switched SSO/Keycloak, see section 5), Krakend providers unused.
- Alice or other debug inspector: not found.
- Trace or request id header (`x-request-id`, `x-bfi-req-id`, `traceparent`, `x-correlation-id`): not found in RO. The agency copy of `http_client.dart` reads `x-correlation-id` from error responses. RO does not.
- Datadog `datadog_tracking_http_client` wraps `dart:io` HTTP with `firstPartyHosts = [API_HOST]` (`main.dart:88,222`), which adds Datadog trace headers to first-party calls. Not verified at runtime.
- Base URL per env: GitHub Environment `vars.API_SCHEME/API_HOST/API_PORT` passed as dart-defines in each deploy workflow. No URL is hard-coded in `lib` apart from store links, `wa.me`, Google Maps search and the WhatsApp App Store link.
- Proxy: `HttpProxy.createHttpProxy()` sets `HttpOverrides.global` (`main.dart:102-105`), called when `_flavour != 'prod'` (`main.dart:216-219`). This makes the Dart HTTP stack honour the device system proxy.

## 10. Security

| Control | State | Evidence |
|---|---|---|
| Certificate pinning | On when `SHA_256_FINGERPRINT` dart-define is non-empty. Comma-separated list supported (`network_config.dart:24-31`). Passed in prod (`deploy-prod.yml:96,209`) and UAT (`deploy-uat.yaml:73`). NOT passed in SIT (`deploy-sit.yml`, `trunk-pipeline.yml` 0 hits) -> SIT builds have no pinning | grep |
| Root / jailbreak | `flutter_jailbreak_detection` from the BFI fork (git ref `55bba36`, `ro_tools/pubspec.yaml:28-32`). Checked in `splash_controller.dart:92-97`; detection shows a block state | code |
| KernelSU check | DEAD. Dart calls `MethodChannel('root_detection').invokeMethod('checkKernelSU')` (`splash_controller.dart:77-86`) and returns `false` on any error. `MainActivity.kt` registers channels `env-value`, `file_picker_channel`, `file_utils` only. The Kotlin `RootDetection` class (`MainActivity.kt:18-64`) is never instantiated. So `isKernelSU` is always `false` | code |
| Play Integrity / App Attest / Firebase App Check | not found | grep `integrity|AppAttest|DeviceCheck|AppCheck` |
| Emulator block | `FEATURE_FLAG_PREVENT_EMULATOR` -> Android `isPhysicalDevice` check, app exits with `SystemNavigator.pop()` otherwise (`main.dart:200-208,233,257`). iOS always treated as real | code |
| Mock location | `position.isMocked` rejected unless `roFfAllowMockLocation` (`geo_controller.dart:109`, `contact_action_controller.dart:66`) | code |
| R8 minify / shrink | `minifyEnabled true`, `shrinkResources true` on release (`build.gradle:112-115`). `proguard-rules.pro` present (14 lines, keeps `io.flutter.**`) | file |
| Dart obfuscation | `--obfuscate --split-debug-info=./debug-info` only in `deploy-prod.yml:131,244`. SIT and UAT builds are `--release` without obfuscation | workflows |
| `allowBackup` | not set in `AndroidManifest.xml` -> Android default (true) | file |
| `usesCleartextTraffic` | not set -> default false for targetSdk 36 | file |
| `network_security_config` | not found | find |
| `requestLegacyExternalStorage` | `true` (`AndroidManifest.xml:16`) | file |
| Debug signing | `debug` build type uses `signingConfigs.release` (`build.gradle:107-110`). Debug builds are signed with the release keystore when `keystore.properties` exists | file |
| Keystore source | Secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PROPS_BASE64` decoded in CI. No keystore in git (`git ls-files` grep `.jks|keystore` empty) | workflows |
| Screen-capture guard | Android only: `window.addFlags(FLAG_SECURE)` when flavour == `prod` (`MainActivity.kt:72-78`). iOS: nothing in `AppDelegate.swift`. Dart-side guard not found | code |
| Proxy switch (PR #456) | see below | git |
| Secure storage keys (names) | Keycloak: `kc_atk`, `kc_rtk`, `kc_atetk`, `kc_rtetk`, `kc_hsebek`, `mkt` (`keycloak_local_data_source.dart:6-11`). SSO: `sso_atk`, `sso_rtk`, `sso_atetk`, `sso_rtetk`, `sso_hsebek`, `sso_itk`, `mkt` (`sso_local_data_source.dart:6-12`). App prefs (10 keys, `app_preferences_key.dart:4-13`) include `user_login` (cached `GetUserAgentResponse` profile) and `analyticsUserData`, both read via `secureGetFromJson` | code |
| Biometrics | not found (`local_auth`, `biometric`) | grep |
| WebView | `webview_flutter` in `shared_data/keycloak/lib/src/keycloak_webview_client.dart` for the Keycloak form login | code |
| Deep links | AppAuth redirect `com.rotools.app://auth/callback` (`main.dart:77`, `AndroidManifest.xml:60-74` `RedirectUriReceiverActivity`). `appAuthRedirectScheme` placeholder per flavour (`build.gradle:72-99`). `uni_links`/`app_links` not found | code |
| Hard-coded URLs/keys in lib | URLs: Play Store, Apple App Store (WhatsApp), `wa.me`, Google Maps search, a Spring docs link in a comment. Keys/tokens/passwords literal: not found (regex over `lib`) | grep |
| iOS `Info.plist` | NOT in git (`git ls-files` finds only `Flutter/AppFrameworkInfo.plist`). ATS, URL schemes and usage strings cannot be verified. No workflow builds iOS | git |
| iOS deployment target | Podfile `platform :ios, '15.0'`; pbxproj `IPHONEOS_DEPLOYMENT_TARGET = 11.0` (12 occurrences); README says 12.0 | files |
| Android SDK | `compileSdk 36`, `targetSdk 36`, `minSdk 29`, NDK `29.0.14206865` (`build.gradle:36-38,58-60`) | file |

PR #456 "Open access screen record and proxy for uat" (commit `3049a97`, 2 Sep 2026, author Reza Nandika, 1 approval by `setiantodenis-bfi`, merged 2 Sep 2026). Diff is 2 lines:

- `MainActivity.kt:75`: `if (flavour == "prod" || flavour == "uat")` -> `if (flavour == "prod")`. `FLAG_SECURE` (blocks screenshots and screen recording) is now set only in prod builds. UAT, SIT and dev builds can be screenshotted and recorded.
- `main.dart:217`: `if (_flavour != 'prod' && _flavour != 'uat')` -> `if (_flavour != 'prod')`. The system proxy is now applied in UAT as well as SIT and dev. A tester (or attacker) can route UAT traffic through an intercepting proxy. In UAT the pin (`SHA_256_FINGERPRINT` is passed) still applies, so interception also needs the pin bypassed. In SIT there is no pin.
- Both lines carry a TODO "Env UAT will be delete soon, for Pentest purpose" (`MainActivity.kt:74`, `main.dart:216`). The change is 8 weeks old and still in master.

## 11. Design system

- `package:ui_theme` imported in 316 files under `ro_tools/lib`.
- `bfi_design_system`, `ds_1`, `bfi_design_system_2`, `bfi_design_system_3`: 0 files. `google_fonts` imported directly: 0 (it is a dep of `ui_theme`).
- Raw `Colors.` uses: 39 lines in 26 files. `Color(0x` literals: 7.
- `ui_theme` is 4,468 hand-written lines in 41 files with 13 test files.

## 12. Testing

| Measure | Value | Command |
|---|---|---|
| Test files `ro_tools/test` | 441 (`111,629` lines) | find `*_test.dart` |
| Test files in shared packages | 15 (core 1, keycloak 1, ui_theme 13, sso 0, pinning 0) | find |
| `testWidgets(` | 1,949 | grep |
| `test(` | 1,751 | grep |
| `*controller_test.dart` | 28 (vs 94 controllers) | find |
| `*screen_test.dart` | 100 (vs 103 screens) | find |
| Goldens | 0 png, 0 `matchesGoldenFile` | find/grep |
| `integration_test/` | does not exist | ls |
| Mocks | 99 `extends Mock` classes (mocktail) | grep |
| Coverage tool | `scripts/combine_coverage.dart` + `scripts/include_unreached_coverage.dart`, lcov | files |
| Coverage exclusions | `*_controller.dart`, `**/*_request.dart`, `**/*_response.dart`, `*/app/navigation/*.dart`, notification data and models, `face_detection_service`, `messaging_service`, `dd_service`, `file_handler/*` (`scripts/combine_coverage.dart:3-17`). All 94 controllers (27,560 lines, where the business rules live) are excluded from the coverage number | file |
| Coverage threshold | none in scripts or workflows (grep `threshold|min`). PR template asks for "at least 80%" (`.github/pull_request_template.md`) but nothing enforces it | grep |
| CI test command | `melos test:ro_tools` -> `flutter test --coverage --no-pub --reporter failures-only --fail-fast --concurrency=1` (root `pubspec.yaml:160-170`) | file |
| Randomisation | `--test-randomize-ordering-seed` not found | grep |
| Reporting | lcov PR comment via `kefasjw/lcov-pull-request-report@v1` and upload to Codacy (`workflow-test-coverage-check.yml:83-98,136-141`, `trunk-pipeline.yml:58-63`) | files |

## 13. Lint and guardrails

- Root `analysis_options.yaml` includes `strict_lint.yaml` (a vendored copy of the `lint` package rule set, header at `strict_lint.yaml:1-5`, 159 rule lines). It is not `very_good_analysis`, although README says so and `very_good_analysis ^10.0.0` is a root dev dep (root `pubspec.yaml:16`).
- Root options ignore: `depend_on_referenced_packages`, `deprecated_member_use`, `use_late_for_private_fields_and_variables`, `invalid_annotation_target`, `use_build_context_synchronously`, `avoid_classes_with_only_static_members` (`analysis_options.yaml:16-22`). Rules turned off: `unnecessary_parenthesis`, `avoid_redundant_argument_values`, `use_build_context_synchronously`.
- `ro_tools/analysis_options.yaml` (12 lines) has NO `include:` line. It only sets two ignores and excludes. Because the analyzer uses the nearest options file, the app package is analysed with the default analyzer and no lint rule set. This is read from the file. It was not verified by running `flutter analyze`.
- `strict-casts: true` is set in `strict_lint.yaml:9-10`, which only reaches the shared packages.
- Excludes: generated files, `app_localizations*`, `shared_lib/http_certificate_pinning`, platform folders.
- `custom_lint`: 0. Architecture or import-boundary checks: none found.
- CI runs `melos format:ro_tools` (set-exit-if-changed) and `melos analyze:ro_tools` = `flutter analyze --fatal-infos --fatal-warnings --no-pub` (root `pubspec.yaml:68-76`), plus `pubghost -d/-c/-t` for dead deps, dead code and dead translations (`workflow-code-analysis-check.yml:114-136`). `pubghost` ignore list in `ro_tools/pubspec.yaml:94-100`.

## 14. CI/CD

Common facts: Flutter `3.47.0`, Java `17.0` (adopt), Android SDK `35` (SIT/UAT via `amyu/setup-android@v2`) or `platforms;android-36`, `build-tools;36.0.0`, NDK `26.1.10909125` and `28.0.12433566` (prod). No Xcode, no iOS job anywhere. Version and build number come from the pubspec `version:` line; no `--build-name`/`--build-number` in any workflow (grep 0). Version bumps are manual commits (last four bumps by Reza Nandika in feature/fix PRs, e.g. `c5558ce` 3.50.2+1077 -> 3.50.3+1078). No `.versionrc` or `package.json`, so `standard-version` in the tag workflow writes `CHANGELOG.md` and the tag only.

| Workflow | Trigger | Jobs | Environment | Runner | Build / distribution | Notes |
|---|---|---|---|---|---|---|
| `build-train-sit.yml` | `workflow_dispatch` | `approval-build-train` (`if: false`), `get-build-info`, `trigger-build` -> `tag-release-pipeline.yml` | `sit_ro_tools` | ubuntu-latest | computes next `x.y.z-sprintN-rotools` tag | approval job disabled at line 8, so the job chain never runs from dispatch. API shows 331 runs, last 29 Jul 2026 `failure`, event `schedule` (no `schedule:` in the current file) |
| `debug.yml` | `workflow_dispatch` | `debug-playstore` | none | ubuntu-latest | none | see secret printing below |
| `deploy-prod.yml` | `workflow_dispatch` input `tag` | `approval-prod`, `deployment-prod` (apk), `deployment-prod-aab` (aab + Play) | `prod_ro_tools` | `ubuntu-22-8core` | `flutter build apk/appbundle --flavor prod --release --obfuscate --split-debug-info` with 39 `--dart-define`; `r0adkll/upload-google-play@v1` track `internal`, package `id.co.bfi.ro.rotools` (lines 260-267) | approval `trstringer/manual-approval@v1`, 9 approvers listed, `minimum-approvals: 2` (line 19). Dart symbols kept 90 days (line 253-258). No Crashlytics or Datadog symbol upload step |
| `deploy-sit.yml` | push of tags `**-rotools` | `deployment-sit` | `sit_ro_tools` | `ubuntu-22-8core` | `flutter build apk --flavor sit --release`, 36 `--dart-define`, no pin, no obfuscation; WIF auth `google-github-actions/auth@v2` -> `firebase appdistribution:distribute` group `ro-tools`, project `bravo-project-nonprod` (lines 107-128) | `permissions: contents read, id-token write` (15-17) |
| `deploy-uat.yaml` | `workflow_dispatch` input `tag` | `deployment-uat` | `uat_ro_tools` | `ubuntu-22-8core` | `flutter build apk --flavor uat --release`, 38 `--dart-define` incl. pin; Firebase App Distribution group `ro-tools`, same nonprod project | `permissions` present (17-19). Does not create `google-services.json` |
| `pr-pipeline.yml` | `pull_request` opened/synchronize/reopened | calls `workflow-code-analysis-check.yml` and `workflow-test-coverage-check.yml` (`secrets: inherit`) | via mapper -> `sit_ro_tools` | ubuntu-latest | format, analyze, pubghost, tests + coverage, Codacy | no path filter on the trigger. `workflow-map-changes-context.yml` has the path filters but has 0 runs |
| `tag-release-pipeline.yml` | `workflow_call`, `workflow_dispatch` | `tag_release_and_changelog` | none | ubuntu-latest | `npx standard-version --commit-all [--release-as TAG]`, `git push --follow-tags` as `bfibravo-bot` with `GH_PAT` | pushes directly to master (the bot is the only account allowed to push) |
| `trunk-pipeline.yml` | push to `master` with paths `ro_tools/**` (excludes changelogs and workflows), `workflow_dispatch` | `scan-code-coverage` | `dev_ro_tools` | ubuntu-latest | tests + Codacy, then `flutter build apk --flavor sit --release` (no pin, no obfuscation). The APK is not uploaded anywhere | runs on `ubuntu-latest` and first frees disk (lines 23-30) |
| `update-graphify.yaml` | cron `17 6 * * 6` Asia/Jakarta, dispatch | reusable `bfi-finance/bfi-base-template/.github/workflows/update-graphify.yaml@master` | none | `<repo>-runner` self-hosted label | commits graph output | `permissions: contents: write`. 2 runs, last 23 Oct `cancelled` |
| `workflow-code-analysis-check.yml` | `workflow_dispatch`, `workflow_call` | `format_and_analyze`, `dead_code_checks` | none | ubuntu-latest | `melos format/analyze`, `pubghost -d -c -t` | SSH key action pinned by SHA here |
| `workflow-map-changes-context.yml` | `workflow_call` | `changes` (`dorny/paths-filter@v3`) | none | ubuntu-latest | path filter for `ro_tools/**` and the 5 shared packages | `permissions` present. 0 runs. Not called by any workflow |
| `workflow-test-coverage-check.yml` | `workflow_dispatch`, `workflow_call` | `generate-coverage`, `setup-environment`, `codacy_analysis` | mapped `<env>_ro_tools` | ubuntu-latest | `melos test:<app>`, lcov PR comment, artifact `coverage-report-ro_tools` (1 day), Codacy upload | `GITHUB_TOKEN: ${{ secrets.GH_PAT }}` at job level (line 59). Input `sonar_scans` only gates the artifact; there is no Sonar step |

`--dart-define` counts: deploy-prod 39 per build (two builds), deploy-uat 38, deploy-sit 36, trunk 36.

Signing: secret names `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PROPS_BASE64` (env vars, decoded with `base64 -di`), `GOOGLE_SERVICES_JSON` (decoded inline). Play upload: `BRAVO_GCP_SA_KEY` as `serviceAccountJsonPlainText`. Firebase distribution: WIF `BFI_DEVSECOPS_WIF_PROVIDER` + service account `bfi-devsecops-wif@bfi-devsecops.iam.gserviceaccount.com`. Git access: `SSH_PRIVATE_KEY`, `KNOWN_HOSTS`. Others: `GH_PAT`, `CODACY_PROJECT_TOKEN`, `KEYCLOAK_CLIENT_SECRET`, `SHA_256_FINGERPRINT`, `DATADOG_CLIENT_TOKEN`, `DATADOG_APP_ID`, `ANDROID_FIREBASE_APP_ID`, `ANDROID_FIREBASE_API_KEY`, `ANDROID_FIREBASE_SENDER_ID`, `FIREBASE_PROJECT_ID`, `KEYCLOAK_REDIRECT_URL` (secret in SIT/trunk, var in UAT/prod).

`secrets.*` interpolated directly into `run:` blocks (shell injection surface and log exposure risk):

| File | Lines |
|---|---|
| `debug.yml` | 16, 25, 31, 35, 39, 51 (`BRAVO_GCP_SA_KEY`) |
| `deploy-prod.yml` | 80, 96-97, 102-107 (apk job) and 193, 209-210, 215-220 (aab job) |
| `deploy-sit.yml` | 56, 72-73, 77-82 |
| `deploy-uat.yaml` | 73-74, 79-84 |
| `trunk-pipeline.yml` | 87-88, 92-97 |
| `tag-release-pipeline.yml` | none in `run:` (`GH_PAT` only in `with:`) |

`echo` of secrets: `echo ${{ secrets.GOOGLE_SERVICES_JSON }} | base64 -di > file` (`deploy-prod.yml:80,193`, `deploy-sit.yml:56`). The value goes to a pipe, not to the log. No `sed 's/./& /g'` pattern found in this repo (grep 0).

`debug.yml` in detail (job `debug-playstore`, 1 run, 9 Apr 2026, actor `kevinmya`, `success`). Added by commit `106073d` on 2026-04-09 by Kevin Arief, message "Add debug workflow for PlayStore service account", no PR number. It handles one secret, `BRAVO_GCP_SA_KEY`, and prints these sub-fields of it to the job log with `jq -r`:

- `.client_email` (line 31)
- `.project_id` (line 35)
- `.private_key_id` (line 51)

The whole JSON secret is interpolated into shell single quotes six times (lines 16, 25, 31, 35, 39, 51). GitHub masks the full secret string, but the extracted sub-fields are different strings and are not masked. `.private_key` itself is read into a shell variable (line 39) and only tested, not printed. The workflow is still `active`.

Third-party actions, pinning:

- SHA-pinned: `shimataro/ssh-key-action@87a8f067...` (only in the two `workflow-*check.yml` files), `codacy/codacy-coverage-reporter-action@89d6c85c...`.
- Tag-pinned (mutable): `actions/checkout@v1/@v2/@v4/@v6`, `actions/setup-java@v3`, `actions/setup-node@v4`, `actions/upload-artifact@v4/@v5`, `actions/download-artifact@v5`, `subosito/flutter-action@v2`, `bluefireteam/melos-action@v2/@v3`, `amyu/setup-android@v2`, `android-actions/setup-android@v3`, `shimataro/ssh-key-action@v2` (deploy and trunk files), `google-github-actions/auth@v2`, `trstringer/manual-approval@v1`, `r0adkll/upload-google-play@v1`, `kefasjw/lcov-pull-request-report@v1`, `hrishikesh-kadam/setup-lcov@v1`, `dorny/paths-filter@v3`.
- Reusable workflow from another repo: `bfi-finance/bfi-base-template/.github/workflows/update-graphify.yaml@master` (branch ref, not SHA).

`permissions:` present only in `deploy-sit.yml`, `deploy-uat.yaml`, `workflow-map-changes-context.yml`, `update-graphify.yaml`. Absent in the other 8 files (default token permissions apply).

`upload-artifact` of keystore or certificates: none. Artifacts are the apk, aab, Dart symbols and `lcov.info`.

PR check path filters: none on `pr-pipeline.yml`. Coverage threshold: none. Randomisation: none. Generated-files check: none (`build_runner` is not run in CI, generated files are committed and trusted).

GitHub API facts (`gh api`, read-only, 26 Oct 2026):

| Workflow | State | Runs | Last run | Conclusion | Actor / event |
|---|---|---|---|---|---|
| build-train-sit.yml | active | 331 | 2026-07-29 | failure | pandu-malik / schedule |
| debug.yml | active | 1 | 2026-04-09 | success | kevinmya / workflow_dispatch |
| deploy-prod.yml | active | 31 | 2026-10-01 | success | rezanandika10 / workflow_dispatch |
| deploy-sit.yml | active | 68 | 2026-10-01 | success | bfibravo-bot / push |
| deploy-uat.yaml | active | 5 | 2026-04-08 | success | rezanandika10 / workflow_dispatch |
| pr-pipeline.yml | active | 213 | 2026-10-19 | failure | debam-bfi / pull_request |
| tag-release-pipeline.yml | active | 61 | 2026-10-01 | success | rezanandika10 / workflow_dispatch |
| trunk-pipeline.yml | active | 104 | 2026-10-01 | success | rezanandika10 / push |
| update-graphify.yaml | active | 2 | 2026-10-23 | cancelled | debam-bfi / schedule |
| workflow-code-analysis-check.yml | active | 4 | 2026-07-30 | failure | rezanandika10 / push |
| workflow-map-changes-context.yml | active | 0 | - | - | - |
| workflow-test-coverage-check.yml | active | 6 | 2026-07-30 | failure | rezanandika10 / push |

Also listed by the API: three dynamic Copilot workflows (`copilot-pull-request-reviewer`, `copilot-swe-agent`).

Last five `pr-pipeline.yml` runs: 4 failures and 1 success. The two runs on `fix/update-pic-screen` (1 Oct 2026) both failed, and that branch became v3.50.3, the current production tag.

Environments: `copilot`, `dev_ro_tools`, `prod`, `prod_ro_tools`, `sit`, `sit_ro_tools`, `uat`, `uat_ro_tools`. All eight have `protection_rules = 0` and no deployment branch policy. The only production gate is the `trstringer/manual-approval` issue step inside `deploy-prod.yml`.

Rulesets: `[]`. Branch protection on `master`: required approving reviews 1, `require_code_owner_reviews: true` but no `CODEOWNERS` file exists in the repo (find), `dismiss_stale_reviews: false`, `require_last_push_approval: false`, required status checks: none (`required_status_checks` null), `enforce_admins: false`, `required_linear_history: false`, `allow_force_pushes: false`, `allow_deletions: false`, `required_conversation_resolution: true`. Push restricted to user `bfibravo-bot`. Bypass PR allowance: `bfibravo-bot`. Collaborators endpoint returned 100 (first page, so at least 100 users or teams expanded).

Tags: 73 total. Last three: `v3.50.3-rotools` (2026-10-01), `v3.50.2-rotools` (2026-09-23), `v3.50.1-rotools` (2026-09-17). Tags matching `*-rotools*` in the last 90 days (since 28 Jul 2026): 10, roughly one every 9 days. Repo history: 342 commits, first commit `2f1b1d5` 2025-12-24 "init push ro tools".

## 15. Dependencies

- Git dependency: `flutter_jailbreak_detection` from `git@github.com:bfi-finance/bfi-flutter-packages.git` ref `55bba36de6e68e86d5e02c76865deb25286daa2a`, path `packages/flutter_jailbreak_detection` (`ro_tools/pubspec.yaml:28-32`). SSH URL, hence the `SSH_PRIVATE_KEY` step in every workflow.
- `dependency_overrides`: `archive: ^3.6.1`, `geolocator: ^11.0.0` (`ro_tools/pubspec.yaml:65-67`). `geolocator` is declared `^9.0.2` at line 39 and then overridden to 11. The declaration is misleading.
- Pre-release pins: `flutter_html: 3.0.0-beta.2`, `flutter_pdfview: 1.4.2-beta.1`.
- Old majors (version judgement from memory, latest versions not verified): `flutter_secure_storage ^8.0.0` (root lock 8.1.0), `share_plus ^7.1.0`, `http_proxy ^1.2.3`, `intl ^0.20.2`, `geolocator ^9`.
- Commercial: `syncfusion_flutter_charts ^29.1.38`. `SyncfusionLicense.registerLicense` not found in `lib`. Licence state not verified.
- Test helper in production deps: `network_image_mock ^2.1.1` sits under `dependencies` (`ro_tools/pubspec.yaml:50`). It is imported 0 times in `lib` and 1 time in `test`.
- `flutter_driver` (dev dep) is imported by the production entry point `ro_tools/lib/main.dart:13` and enabled behind `const bool.fromEnvironment('FLUTTER_DRIVER_ENABLED')` in debug/profile (`main.dart:38-42`).
- Imported but not declared in `ro_tools/pubspec.yaml`: `flutter_riverpod` (`lib/app/crashlytics/crashlytics_service.dart:4`) and `stack_trace` (`lib/main.dart:23`). Both resolve transitively. `depend_on_referenced_packages` is ignored in root options, and the app package has no lint set at all.
- `pubghost` ignore list: `json_annotation`, `build_runner`, `flutter_launcher_icons`, `freezed`, `json_serializable` (`ro_tools/pubspec.yaml:94-100`).
- `shared_lib/http_certificate_pinning` is a vendored fork at 2.0.6 with `flutter_lints ^1.0.0` in its dev deps. Upstream status not verified.
- Locked versions from the root `pubspec.lock` (workspace packages only): `flutter_riverpod 2.6.1`, `dio 5.9.0`, `freezed 4.0.1`, `flutter_secure_storage 8.1.0`, `webview_flutter 4.13.0`, `flutter_appauth 7.0.1`, `google_fonts 6.3.3`, `http 1.6.0`. App-only packages (go_router, firebase_*, datadog_*, syncfusion, geolocator, share_plus, flutter_html, http_proxy) are not in any tracked lockfile.

## 16. Other

- TODO/FIXME/HACK: 31 lines in hand-written code (excluding the vendored pinning package). Notable:
  1. `ro_tools/lib/main.dart:216` `//TODO(reza): Env UAT will be delete soon, for testing purpose` (the proxy switch, see PR #456).
  2. `ro_tools/android/.../MainActivity.kt:74` `//TODO: (reza) Env UAT will be delete soon, for Pentest purpose` (the FLAG_SECURE switch).
  3. `ro_tools/lib/app/widget/notification/notification_card.dart:456,469,481,529,545` `TODO(agung) : Handle reAssign & changePriority button` (five copies).
  4. `ro_tools/lib/app/file_handler/file_handler.dart:38,67` `TODO: handle permission request for IOS`.
  5. `ro_tools/lib/app/navigation/pbf_routes.dart:32,57,101` and `pbf_top_level_screen.dart:29,127` `TODO(Reza): DO NOT DELETED! WAITING FOR INTEGRATION` (PBF routes kept as placeholders; there is also a `features/temporary_screens` folder).
- Dummy data: `dummy|lorem|fakeData|mockData` in `lib`: not found (the 52 regex hits were `isNullOrEmpty` helpers).
- README accuracy: version stale (3.39.2+1060 vs 3.50.3+1078). "Very Good Analysis strict linting" is wrong (strict_lint.yaml at root, no lint set in the app package). "SonarQube (see sonar-project.properties)" is wrong: the file is git-ignored and CI uses Codacy. "Minimum iOS version: 12.0" disagrees with Podfile 15.0 and pbxproj 11.0. `./run_coverage.sh` is git-ignored and absent. "State Management: Controllers" hides that it is Riverpod 2 StateNotifier. The README calls CRE "Credit Risk Executive", not verified.
- `ro_tools/CLAUDE.md` and `ro_tools/.claude/` are Graphify boilerplate. `graphify-out/` is git-ignored and absent.
- `.github/copilot-instructions.md` and the `.github/agents`, `.github/prompts` folders describe the 4-app agency monorepo (`agent_tools`, `are_tracker`, `ro_tools`, `mybispro`). The env mapper action still lists those apps (`actions/map-development-env/action.yml:5`).
- Translations: Indonesian only. `ro_tools/lib/app/localizations/app_id.arb` has 1,268 keys. No English arb. `l10n.yaml` template is `app_id.arb`.
- Product name: "myBRO" appears only in the launcher icon asset name (`ro_tools/pubspec.yaml:81`), `ro_images.dart` and a few l10n strings. The Android label is "BFI RO Tools" with `[SIT]`, `[DEV]`, `[UAT]` prefixes (`build.gradle:72-99`).
- Firebase App Distribution group `ro-tools` is shared by SIT and UAT builds in the same nonprod project.
- The `.specify/` folder (spec-kit) exists at the root with templates and scripts.
- `KEYCLOAK_REDIRECT_URL` is a secret in SIT and trunk but a variable in UAT and prod.
- `RootDetection` Kotlin class runs `ps` through `Runtime.exec` (`MainActivity.kt:33`) but is dead code (section 10).
- Android `debug` build type is signed with the release keystore (`build.gradle:107-110`).

## 17. Open questions

1. Is the UAT proxy and screen-record opening from PR #456 (2 Sep 2026) still needed, and who owns removing it? The TODO says "will be delete soon".
2. Was the `BRAVO_GCP_SA_KEY` service account key rotated after `debug.yml` printed its `client_email`, `project_id` and `private_key_id` on 9 Apr 2026? Should the workflow be deleted?
3. Why does `pr-pipeline.yml` fail on 4 of the last 5 runs, and why are there no required status checks on `master`? v3.50.3 shipped from a branch whose PR checks failed.
4. `require_code_owner_reviews` is on but there is no `CODEOWNERS` file. Is that intended?
5. The KernelSU check is dead (no `root_detection` method channel registered). Was it ever wired, or did it break in the split from the monorepo?
6. The coverage script excludes every `*_controller.dart`. Was that a conscious decision? Controllers hold the business rules (27,560 lines).
7. `ro_tools/analysis_options.yaml` has no `include:`. Is the app really analysed without lint rules in CI, or does `melos analyze:ro_tools` pick up the root file in some way I did not verify?
8. `iOS`: no `Info.plist` in git and no iOS workflow. Is iOS built at all, and where?
9. Three compile-time flags are never passed by any workflow (`FEATURE_FLAG_ALLOW_NEW_VERSION_OF_TAX_STATUS`, `_MULTI_ASSET_2W`, `_MULTI_ASSET_4W`). Are they meant to come from Remote Config only, and is the mis-mapped fallback at `app_controller.dart:236,242` known?
10. Which copy of `shared_lib/core`, `sso`, `keycloak` is the source of truth now? Agency has moved ahead (interceptor hook, correlation id, web multipart) and RO has not pulled those changes.
11. Does the Datadog `setUserInfo` call send the NIK as `id` plus name and email? Is that in line with the PII rules for the Datadog account (site us5)?
12. Is the `syncfusion_flutter_charts` licence registered somewhere outside `lib`, or does the app show the licence banner?
13. `build-train-sit.yml` has 331 runs by schedule but no `schedule:` trigger today and an approval job set to `if: false`. Is the build-train process retired?
