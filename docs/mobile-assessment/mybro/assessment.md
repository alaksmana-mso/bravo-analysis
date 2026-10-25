## Summary

myBRO (store name "BFI RO Tools", app folder `ro_tools/` in `bfi-finance/bravo-ro-tools-apps`) is the internal app for repeat-order submissions. It is the second largest BFI mobile code base: 112,371 hand-written Dart lines in 754 files, 29 feature folders, 94 controllers. It was split out of the agency monorepo in December 2025 and still carries copies of five of its shared packages. It ships about every nine days and is used: 78,554 Datadog RUM sessions on version 3.50.3 in the last 30 days. This page compares it with the DK Jago app the same way as the GENFI, SQUARE, MyShaf and MY BISPRO pages, and maps its work onto the Agency apps roadmap: shared phases.

* **A workflow prints fields of the Play Store service-account key.** `debug.yml` (added 9 Apr 2026, no PR, still active, 1 run) interpolates `BRAVO_GCP_SA_KEY` into shell six times and prints its `client_email`, `project_id` and `private_key_id` with `jq`. GitHub masks only the whole secret, not these fields. The private key itself is not printed. The same key uploads to Play in `deploy-prod.yml` and is an org secret in 51 repos.
* **UAT was opened for a pentest and never closed.** PR #456 (2 Sep 2026, one approval) made two one-line changes: `FLAG_SECURE` now only in prod, the system proxy now honoured in every non-prod flavour. The TODO says "will be delete soon". SIT builds additionally have no certificate pin and no obfuscation.
* **Checks do not gate merges.** `master` requires 1 approval and no status checks, admins are not enforced, code-owner review is required but there is no `CODEOWNERS` file. The PR pipeline failed on 4 of the last 5 runs, including both runs for the branch that became v3.50.3, the current production tag. All 8 GitHub environments have zero protection rules.
* **The coverage number hides the rules.** `scripts/combine_coverage.dart` excludes every `*_controller.dart`. The 94 controllers hold 27,560 lines and the business logic. 28 of them have a test. No threshold anywhere.
* **The app package has no lint rule set.** `ro_tools/analysis_options.yaml` has no `include:` line, so the root `strict_lint.yaml` reaches only the shared packages. The README's "very_good_analysis" claim is wrong. Read from the files, not verified by running the analyzer.
* **Root detection is half dead.** The Dart side calls a `root_detection` method channel that `MainActivity.kt` never registers, so the KernelSU check always returns false. The jailbreak fork works. No Play Integrity or App Attest. The debug build type is signed with the release keystore.
* **Architecture is the GENFI gap at larger scale.** 95 `StateNotifier` controllers, no domain layer, `*Response` DTOs in 46 screens and 71 controllers, 198 cross-feature imports with 8 two-way cycles, `lib/app` importing `lib/features` in 26 files. Two calculator controllers of 2,589 and 2,321 lines.
* **Observability sends personal data.** Datadog `setUserInfo` sends the login id (likely the NIK), name and email. Firebase Analytics default parameters include `agent_name` on every event. Consent is hard-coded `granted`. `DDService.e` attaches a free-form request map to 159 error calls with no sanitiser.
* **Shared packages have drifted.** `core`, `sso` and `keycloak` are 16 to 42 lines behind the agency copies (interceptor hook, correlation-id capture, web multipart). `ui_theme` and the pinning fork are identical. Nobody owns the sync.
* **iOS cannot be assessed from this repo.** No iOS workflow, no `Info.plist` in git. The store listing has no iOS entry.

**Overall shape today**

## Scope and evidence

| **Item** | **myBRO** | **Jago (reference)** |
| --- | --- | --- |
| Repository | [bfi-finance/bravo-ro-tools-apps](https://github.com/bfi-finance/bravo-ro-tools-apps), app `ro_tools/`, packages `shared_lib/core`, `shared_lib/http_certificate_pinning`, `shared_data/sso`, `shared_data/keycloak`, `ui_theme` | DK GitLab digital\_banking\_app + prod-pipelines/jago-mobile |
| Revision read | master @ 9617214 (19 Oct 2026); 342 commits since the first push on 24 Dec 2025 | Local working copy, Oct 2026 |
| Store | `id.co.bfi.ro.rotools`, Android only; pubspec `3.50.3+1078`; last tag `v3.50.3-rotools` (1 Oct 2026); 10 tags in 90 days | n/a |
| Audience | Internal staff: repeat-order (RO), CRE, SA, SPV and PBF roles | Retail banking customers |
| Stack | Flutter 3.47.0 in CI, Dart >=3.9, Riverpod 2.6 (StateNotifier, via `core`), dio 5.9, go\_router 14.8, freezed 4.0, firebase\_core 4.1, analytics 12, crashlytics 5, remote\_config 6, messaging 16, datadog\_flutter\_plugin 2.8, syncfusion charts 29 | Flutter 3.38.8, Dart 3.10, bloc, injectable + Kiwi |
| Size | 754 hand-written Dart files, 112,371 lines; 448 generated files, 111,936 lines, committed; 11,902 lines of l10n; 29 feature folders, 103 screens, 94 controllers, 27 repositories | About 5,288 test files alone |
| Usage | Datadog RUM "RO Tools-Prod": 78,554 sessions on 3.50.3 in the last 30 days, 13,871 on 3.50.2, 7,751 on 3.49.2 | n/a |
| GitHub environments | `dev_ro_tools`, `sit_ro_tools`, `uat_ro_tools`, `prod_ro_tools`, plus `dev`, `sit`, `uat`, `prod`, `copilot`. All with 0 protection rules (API, 26 Oct 2026) | Separate prod pipeline repo |
| Assessed on | 26 Oct 2026 | 9 Oct 2026 |

All findings come from reading source and CI files at the revision above, a `diff -rq` against the agency monorepo copies, the GitHub REST API (environments, branch protection, rulesets, workflow runs, no logs) and Datadog RUM. Nothing was built or run. The fact sheet with the command behind every number is in `bravo-analysis/docs/mobile-assessment/mybro/facts.md`.

## Side-by-side comparison

Effort: S = up to 1 sprint, M = 2–4 sprints, L = more than a quarter. "Shared pattern" means the same finding exists in the agency monorepo and the fix should be the same code, but it needs its own PR in this repo.

| **Area** | **Jago** | **myBRO today** | **Gap** | **Effort** |
| --- | --- | --- | --- | --- |
| Repo layout | Melos workspace, feature and shared packages, thin `*_api` contracts. | Melos workspace (config in the root pubspec): one app plus five packages copied from the agency monorepo. `lib/app` holds 42,012 lines of data layer, widgets and utilities and imports `lib/features` in 26 files. 198 cross-feature imports over 66 pairs, 8 two-way. `core`, `sso`, `keycloak` have drifted from the agency copies. | Pick one source for the shared packages (a published package or a git subtree) before any refactor touches them twice. Feature packages later. | S (sync) / L (packages) |
| Layering | data → domain ← presentation. Domain is pure Dart. | `app/data/<area>/repository + model` and `features/<f>/screen + controller`. No domain folder. Repositories are reached only from controllers (good), but `*Response` DTOs reach 46 screens and 71 controllers. The rules sit in the two calculator controllers (2,589 and 2,321 lines) and `contact_list_controller` (1,300). | Domain for the loan proposal and offering calculations first. Mappers at the repository edge. | L |
| State management | bloc with rules. | Riverpod 2.6 legacy: 95 `StateNotifier`, 0 `Notifier`, 145 `ConsumerStatefulWidget`, 300 `ref.listen`. Provider as `static final` on the class. `NavigationService` singleton for the navigator key. Two provider observers (Datadog, Crashlytics). | Keep Riverpod. Riverpod 3, then Notifier, the same sequence as the agency apps. | M |
| Dependency injection | injectable + get\_it, wiring in the app layer. | `ProviderScope` with 6 overrides in `main.dart`. The auth client (`SsoHttpClient` or `KeycloakHttpClient`) is chosen by the Remote Config value `roFfSsoLogin`, read through `AppController`, default Keycloak until the fetch returns. No interfaces beyond `core.HttpClient`. | Ports. Make the auth choice a build-time or start-up decision, not a watched provider. | M (with layering) |
| Analytics wrapper | `AnalyticsPlatform` interface, fan-out, typed events. | `AnalyticsServices` wrapper over Firebase Analytics, 24 named events (mixed English and Indonesian, e.g. `user_click_lanjutkan`), 27 call sites, user id and `user_role` property, `FirebaseAnalyticsObserver` and `DatadogNavigationObserver` on the shell route. Default parameters carry the whole user json including `agent_name`. A clamp sanitiser (25 params, 100 chars), no PII redaction. | Closest to the target of the five apps. Add the Datadog fan-out, typed parameters, and drop `agent_name` from default params. | S |
| Logging and crashes | Monitoring fans out to Crashlytics and Datadog. PII sanitiser. | Crashlytics in every flavour, no custom keys, `recordFlutterError` wired. `runZonedGuarded` errors go to Datadog only. `DDService.e` creates a logger per call and sends error, stack, `path` and a `request` map (159 call sites). Provider errors go to both. `setUserInfo` sends id, name and email. Consent hard-coded `granted`. No sanitiser. | Works, unlike the agency apps' `DatadogLog.e`. Needs the PII cleaner and a consent setting. | S |
| Feature flags | Typed catalogue behind one interface. | `RoRemoteConfigValue`, 38 typed keys with defaults, live updates, a mapper from one Remote Config string. Plus 22 compile-time `FEATURE_FLAG_*` dart-defines, 3 of which no workflow passes. Fallback mapping bug when the fetch fails: `roFfNotification` and `roFfAllowNewVersionOfTaxStatus` both read `featureFlagActivityContact` (`app_controller.dart:236,242`). | Good shape. Fix the fallback bug, retire the compile-time flags into the catalogue. | S |
| Networking | dio adapter behind a client interface, typed exceptions. | `core.HttpClient` (dio, 30 s timeouts, pin interceptor when a fingerprint is set). Two auth decorators that refresh before every call and clear the session on 401. No retry, no request-id header, Krakend providers unused. `datadog_tracking_http_client` traces first-party hosts. System proxy honoured outside prod. | Same chain as the agency apps, from the same `core` once it is one package again. | M |
| Security | Everspin RASP, CodeMix, build registration, device fingerprint, screen-capture guard, pinning. | Prod: pinned, R8 and `shrinkResources` on with a `proguard-rules.pro`, `--obfuscate`, `FLAG_SECURE` on Android, emulator block, mock-location rejection, jailbreak fork. SIT: no pin, no obfuscation, proxy, screenshots. UAT: pinned but proxy and screenshots since PR #456. KernelSU channel dead. No Play Integrity. `allowBackup` not set (Android default true). Debug build type signed with the release keystore. | Close UAT again, pin and obfuscate SIT, wire or delete the KernelSU check, set `allowBackup` false, add Play Integrity with the other repos. RASP vendor with the other three. | S (fixes) / M (RASP) |
| Design system | Tokens from Figma, Widgetbook. | `ui_theme` in 316 files, identical to the agency copy. Raw `Colors.` on 39 lines. | Clean. Keep it in sync with the agency copy. | S |
| Testing | 5,288 test files, coverage gate on changed files, Appium end-to-end. | 441 test files, 1,949 `testWidgets`, 1,751 `test(`, 100 screen tests, 28 controller tests, 0 goldens, no `integration_test`. Coverage excludes every controller, the request and response models, navigation and the services. No threshold, no randomisation. `--concurrency=1`. | Put the controllers back in the coverage number. Characterisation tests for the two calculators before any refactor. | M |
| Lint and guardrails | custom\_lint, Danger, generated-files check, `.claude/rules`. | Root `strict_lint.yaml` with 6 rules ignored. `ro_tools/analysis_options.yaml` has no `include:`, so the app has no rule set. `flutter analyze --fatal-infos --fatal-warnings`, format, pubghost, Codacy. No `custom_lint`, no import-boundary check. `copilot-instructions.md` still describes the 4-app monorepo. | Add the include line (expect many findings, baseline them). Architecture ratchets. | S |
| CI/CD | See the next section. | 12 workflows. Prod works. PR checks do not gate. Android only. | See the next section. | M |

**Target shape**

## CI/CD compared step by step

| **Step** | **Jago prod pipeline** | **myBRO** | **Gap** |
| --- | --- | --- | --- |
| Trigger | Version tag, trigger branches, or manual. | Tag `**-rotools` for SIT, dispatch with `tag` for UAT and prod, push to master on `ro_tools/**` for trunk. `build-train-sit.yml` (331 scheduled runs until 29 Jul 2026) has its approval job set to `if: false` and no schedule today. | Delete or repair the build train. |
| Run history (API, 26 Oct 2026) | n/a | Prod 31 runs, last 1 Oct 2026, success. SIT 68 runs, last 1 Oct, success. Trunk 104, success. PR pipeline 213 runs, 4 of the last 5 failed. UAT 5 runs, last 8 Apr 2026. | Prod and SIT work. The PR check is red and not required. |
| Branch protection | Separate repo for prod. | `master`: 1 approving review, no required status checks, `enforce_admins` false, `require_code_owner_reviews` true with no `CODEOWNERS`, push restricted to `bfibravo-bot`, no rulesets. | Require the PR pipeline. Add `CODEOWNERS` or turn the flag off. |
| Toolchain | One pinned version. | Flutter 3.47.0 in every file (newer than the agency monorepo's 3.35.0). Java 17. SDK 35 in SIT and UAT, 36 in prod. NDK 26, 28 and 29 across workflows and Gradle. | One toolchain file. |
| Version and build number | From the tag, CI counter. | From the pubspec `version:` line, bumped by hand in feature PRs (`3.50.2+1077` → `3.50.3+1078`). `standard-version` writes the changelog and tag as `bfibravo-bot`. | CI counter so the build number cannot go backwards. |
| Config | `env.dart` per environment. | 36 to 39 dart-defines per build from environment variables and secrets. 22 of them are feature flags. `KEYCLOAK_REDIRECT_URL` is a secret in SIT and a variable in UAT and prod. | Move flags into the catalogue, defines into one config step. |
| Build | `flutter build appbundle`, fastlane. | Prod builds an APK and an AAB in two jobs, `--release --obfuscate --split-debug-info`. SIT, UAT and trunk build `--release` only, no obfuscation. No iOS job. | Obfuscate every build. Decide whether iOS exists. |
| Code protection | CodeMix, registration. | R8 and `shrinkResources` on, `proguard-rules.pro` present (14 lines). No RASP. | Same vendor decision as the other repos. |
| Approval | Separate repo with its own access. | `trstringer/manual-approval@v1`, 2 of 9, `GH_PAT`. `prod_ro_tools` has 0 rules. | Limit the environment to release refs, keep the step. |
| Signing | Keystore only in the prod repo. | `ANDROID_KEYSTORE_BASE64` and props decoded from secrets. No keystore artifact. | Acceptable once the environment is limited. |
| Distribution | Play internal, TestFlight. | Prod: Play `internal` with `BRAVO_GCP_SA_KEY` (service-account JSON). SIT and UAT: Firebase App Distribution group `ro-tools` through keyless WIF (`BFI_DEVSECOPS_WIF_PROVIDER`), the pattern the agency monorepo should copy. | Move the Play upload to WIF too, then delete the JSON key. |
| Post-build | Eversafe registration. | Dart symbols kept 90 days as an artifact. No Datadog or Crashlytics symbol upload step. | Upload symbols to Datadog and Crashlytics so stack traces are readable. |
| PR checks | Lint, format, generated files, tests, coverage on changed files, Danger. | Format, analyze, pubghost, tests with coverage, lcov comment, Codacy upload. No path filter (the filter workflow exists and has 0 runs). No threshold. No randomisation. No generated-files check. Not required to merge. | Make it required. Gate on changed-file coverage with the controllers included. |
| Secrets handling | n/a | `debug.yml` prints fields of `BRAVO_GCP_SA_KEY`. Secrets interpolated into `run:` in 5 workflows (line numbers in the fact sheet). `permissions:` only in 4 of 12 files. Two actions pinned by SHA, the rest by tag, the Graphify reusable workflow by branch. | Delete `debug.yml`, rotate the key, `env:` for secrets, pin by SHA. |

**Pipeline state**

## Security items

Shared with the other mobile repos (`BRAVO_GCP_SA_KEY` as an org secret in 51 repos, prod builds without environment rules, RASP missing): see Agency phase 0: Close the leak and Mobile plan 01: Security. Specific to myBRO:

1. **`debug.yml`** (job `debug-playstore`): delete it from master and rotate `BRAVO_GCP_SA_KEY`. The printed `client_email`, `project_id` and `private_key_id` are not the private key, but they identify the key, the workflow is still dispatchable by anyone with write access, and the same key is the Play upload credential. Checked through run metadata only, no log opened.
2. **PR #456** opened UAT to proxies and screen recording for a pentest on 2 Sep 2026 with a "delete soon" TODO. Revert the two lines, or make the pentest build a separate flavour that is never distributed to the `ro-tools` group.
3. **SIT builds have no pin and no obfuscation**, and honour the system proxy. Testers run a build that any intercepting proxy can read. Pass `SHA_256_FINGERPRINT` and `--obfuscate` in `deploy-sit.yml` and `trunk-pipeline.yml`.
4. **No required status checks and admins not enforced on `master`.** v3.50.3 shipped from a branch whose PR checks failed twice.
5. **Eight environments with zero protection rules.** Limit `prod_ro_tools` to release refs (Team plan: no required reviewers on private repos).
6. **KernelSU check is dead code.** `splash_controller.dart:77-86` calls `MethodChannel('root_detection')`, `MainActivity.kt` registers only `env-value`, `file_picker_channel` and `file_utils`. Wire it or delete the Kotlin class, which runs `ps` through `Runtime.exec`.
7. **Personal data in telemetry.** Datadog `setUserInfo(id: username, name, email)`, analytics default parameter `agent_name`, `DDService.e` request maps. Decide what is allowed, then add the sanitiser the agency apps also need.
8. **`allowBackup` not set** (default true on Android). Set it to false like MY BISPRO does.
9. **Debug build type signed with the release keystore** (`build.gradle:107-110`).
10. **`flutter_driver` imported by `main.dart`** behind a dart-define. Keep it out of release builds by construction, not by flag.
11. **`requestLegacyExternalStorage` true** and `READ/WRITE_EXTERNAL_STORAGE` on targetSdk 36. Review before the next Play policy deadline.

**Security posture per build flavour**

## What else to work on

### 1. Put the controllers back into the coverage number

`scripts/combine_coverage.dart` removes `*_controller.dart`, `*_request.dart`, `*_response.dart`, navigation, notification data, the face-detection, messaging and Datadog services from `lcov.info` before it is reported. The number that reaches the PR comment and Codacy therefore describes screens and widgets only. The PR template asks for 80 percent and nothing checks it. Remove the controller exclusion, accept the drop, and gate on changed files from there.

**What the coverage number covers**

### 2. Sync or own the shared packages

| **Package** | **Against the agency copy (1e50b819)** |
| --- | --- |
| `shared_lib/http_certificate_pinning` | Identical |
| `ui_theme` | Identical code, pubspec differs |
| `shared_lib/core` | Agency has `addInterceptor`, `x-correlation-id` capture, web multipart, two more test files; `exceptions.dart` differs by 20 lines |
| `shared_data/sso` | 17 lines behind in the client, 16 in the repository |
| `shared_data/keycloak` | 17 lines behind in the client |

The agency monorepo still has the `archived/ro_tools` branch. Every shared fix on the agency roadmap (the network chain, the request id, the logging fix) will have to be applied here by hand until one copy is the source. Options: publish `core`, `sso`, `keycloak`, `ui_theme` and the pinning fork as versioned packages from the agency repo (GitHub App token for private pub, as the agency phase 1 page proposes), or move myBRO back into the monorepo. Recommended: publish, because the two repos have different release cadences and owners.

### 3. Split the largest files

| **File** | **Lines** |
| --- | --- |
| `features/loan/proposal/calculator/loan_proposal_calculator_screen.dart` | 2,635 |
| `features/loan/proposal/calculator/loan_proposal_calculator_controller.dart` | 2,589 |
| `features/loan/offering/calculator/loan_offering_calculator_controller.dart` | 2,321 |
| `features/loan/offering/calculator/loan_offering_calculator_screen.dart` | 1,792 |
| `app/widget/notification/notification_card.dart` | 1,785 |
| `features/activity/activity_app_bar.dart` | 1,724 |
| `app/common/exceptions.dart` | 1,336 |
| `features/activity/contact/contact_list_controller.dart` | 1,300 |

The two calculators are the pilot for Phase 7. They have the most rules, the fewest tests relative to size, and two near-copies of each other (proposal and offering).

### 4. Other items

* Three compile-time flags are read but never passed by any workflow, so they compile to false: `FEATURE_FLAG_ALLOW_NEW_VERSION_OF_TAX_STATUS`, `FEATURE_FLAG_MULTI_ASSET_2W`, `FEATURE_FLAG_MULTI_ASSET_4W`.
* Fallback mapping bug in `app_controller.dart:236,242` when the Remote Config fetch fails.
* `ro_tools/pubspec.lock` is git-ignored, so app dependency versions are not pinned in git. Only the workspace packages are locked.
* `geolocator` is declared `^9` and overridden to `^11`. `network_image_mock` is a production dependency. `flutter_html` and `flutter_pdfview` are on beta pins. `syncfusion_flutter_charts` has no `registerLicense` call in `lib`.
* `flutter_riverpod` and `stack_trace` are imported but not declared by the app.
* PBF routes and a `temporary_screens` folder are kept as placeholders with "DO NOT DELETE, WAITING FOR INTEGRATION" TODOs. Five copies of a "handle reAssign" TODO in `notification_card.dart`.
* README is stale: version 3.39.2, "very_good_analysis", "SonarQube", iOS 12. `copilot-instructions.md`, `.github/agents` and the env mapper action still describe the 4-app monorepo. `ro_tools/CLAUDE.md` is Graphify boilerplate pointing at a folder that does not exist.
* Product naming: the launcher icon says "myBRO", the Android label says "BFI RO Tools", the RUM app says "RO Tools-Prod".

## Plans and roadmap

myBRO lives in its own repository, so the shared phase pages cannot carry its tickets. The pattern is the same, because the shared packages and the workflow files were copied from the monorepo. Each myBRO step below names the agency phase it mirrors, so the two repos can do the same work in the same order and one squad can review both. Steps that mirror a shared step should reuse that step's design, not redo it.

Impact classes as on GENFI roadmap: step by step: **A** no app change, **B** same behaviour, **C** behind a switch flag, **D** approved delta, **E** backend-coupled.

| **#** | **Step** | **Class** | **Mirrors** | **Depends on** | **Jira ticket** | **PR** |
| --- | --- | --- | --- | --- | --- | --- |
| R.0.1 | Delete `debug.yml`. Rotate `BRAVO_GCP_SA_KEY` (org-wide, coordinate with Agency phase 0). | A | Agency phase 0 | – | | |
| R.0.2 | Limit `prod_ro_tools` to release refs. Require the PR pipeline on `master`, enforce for admins, add `CODEOWNERS` or turn the flag off. | A | Agency phase 0 | – | | |
| R.0.3 | Revert PR #456 (UAT proxy and screen record), or move the pentest build to a separate undistributed flavour. | D | – | – | | |
| R.1.1 | Pass `SHA_256_FINGERPRINT` and `--obfuscate` in SIT and trunk builds. `env:` for secrets, `permissions:` in every workflow, actions pinned by SHA. | A | Agency phase 1 | R.0.2 | | |
| R.1.2 | Add `include:` to `ro_tools/analysis_options.yaml`, baseline the findings, ratchet down. Remove the controller exclusion from `combine_coverage.dart`, gate on changed files. | A | Agency phase 1 | – | | |
| R.1.3 | Characterisation tests for `loan_proposal_calculator_controller` and `loan_offering_calculator_controller` against today's output. | A | Agency phase 1 (parity net) | – | | |
| R.1.4 | Play upload through WIF instead of the JSON key. Symbols to Datadog and Crashlytics after each prod build. Build number from a CI counter. | A | Agency phase 1 | R.0.1 | | |
| R.1.5 | One source for `core`, `sso`, `keycloak`, `ui_theme`, pinning fork: publish from the agency repo and consume here. | B | Agency phase 1 (toolchain) and phase 8 | – | | |
| R.2.1 | Monitoring port with a PII sanitiser in front of `DDService.e`, Crashlytics and `setUserInfo`. Analytics port over `AnalyticsServices`. Flag port over `RoRemoteConfigValue`, compile-time flags folded in, fallback bug fixed. | B | Agency phase 2 | R.1.3 | | |
| R.3.1 | Approved deltas, one per release: `allowBackup` false, debug build off the release key, drop `agent_name` from default analytics params, real consent setting, wire or delete the KernelSU check, `flutter_driver` out of release. | D | GENFI phase 3 | R.2.1 | | |
| R.4.1 | Network chain behind `useInterceptorClient`: `SsoHttpClient` and `KeycloakHttpClient` become the shared chain with refresh, retry and request id. Auth choice at start-up, not a watched provider. | C, E | Agency phase 4 | R.1.5 | | |
| R.6.1 | Riverpod 3 upgrade alone, one release. | B | Agency phase 6 | R.1.3 | | |
| R.7.1 | Pilot: the loan proposal calculator through the parity loop (ledger, `useNewProposalCalculator`, domain for the calculation rules shared with the offering calculator, Notifiers, cohort by branch, flip, delete). | C | GENFI phase 7 | R.6.1 | | |
| R.8.1 | `loan` as the first feature package, move only. | B | Agency phase 8 | R.7.1 | | |
| R.9.1 | Other features through the same loop: `activity`, `spv`, `ro_database`, `more_action`, then class B conversions. Break the 8 two-way pairs and the `lib/app` → `lib/features` imports on the way. | C, then B | GENFI phase 9 | R.8.1 | | |
| R.10.1 | RASP vendor (one decision for the four repos), Play Integrity, Widgetbook for `ui_theme`. | C, D | Agency phase 10 | – | | |

Suggested epics: "[Tech x DK] myBRO Improvement - Close the leak", "- Safety net", "- Seams and deltas", "- Network chain", "- Pilot: loan calculators", "- Remaining features", "- Platform". One epic per phase, one ticket per step, as on the other roadmaps.

**Where myBRO's work sits**

## Open questions

| **#** | **Question** | **Who answers** |
| --- | --- | --- |
| Q1 | Was `BRAVO_GCP_SA_KEY` rotated after `debug.yml` ran on 9 Apr 2026? Who added the workflow and why? | Platform, Tele Marketing tech lead |
| Q2 | Is the UAT pentest finished? Can PR #456 be reverted now? | Security, Tele Marketing squad |
| Q3 | Why is the PR pipeline red on 4 of 5 runs, and why is it not required on `master`? | Tele Marketing tech lead |
| Q4 | Is iOS built anywhere? There is no workflow and no `Info.plist` in git. The store has no iOS listing. | Tele Marketing squad |
| Q5 | Which copy of `core`, `sso` and `keycloak` is the source of truth, this repo or the agency monorepo? | Agency and Tele Marketing tech leads |
| Q6 | Was excluding every controller from coverage a decision? | Tele Marketing squad |
| Q7 | Is the Datadog `setUserInfo` id the NIK? Is name and email in RUM allowed under the PII rules for the us5 account? | Security, Observability |
| Q8 | Is the Syncfusion charts licence registered outside `lib`? | Tele Marketing squad |
| Q9 | Is the build train (`build-train-sit.yml`) retired? | Tele Marketing squad |

Facts checked on 26 Oct 2026 against `bravo-ro-tools-apps` `master` @ `9617214`, `bravo-agency-app` `master` @ `1e50b819` for the package diff, the GitHub REST API and Datadog RUM (us5). Full fact sheet: `bravo-analysis/docs/mobile-assessment/mybro/facts.md`.
