# Mobile plan 09: Security

## Goal

No workflow can expose prod secrets. Every prod build is shrunk, obfuscated and protected against tampering. Sensitive screens cannot be captured. The backend trusts device integrity and user auth, never a value baked into the app.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20` (11 Sep 2026). GitHub settings were read through the API on 9 Oct 2026 (metadata only). No run logs were opened. No secret values were read.

### Urgent: the "Reveal Secret" workflow

| Fact | Evidence |
|---|---|
| `.github/workflows/test.yaml` ("Reveal Secret") is still on `master` | GitHub API, `master` @ `a1a63916`, 9 Oct 2026. Workflow state: `active` |
| It is also on all 4 release branches | `release-2.24.x`, `release-2.25.x`, `release-2.26.x`, `release-2.27.x` |
| It echoes `BRAVO_GCP_SA_KEY`, `KNOWN_HOSTS`, `SSH_PRIVATE_KEY` with a space between every character | 18-line file. The spaces defeat GitHub's log masking |
| It runs in the `customer_app_prod` environment | `environment: customer_app_prod` |
| `customer_app_prod` has **no protection rules** and no branch policy | `GET /environments`: `protection_rules: []` for all 6 environments |
| The GitHub API lists no pull request for commit `70ed19f3` | It may have been pushed directly. Worth checking the ruleset bypass list |

### Other workflows that reach prod secrets without approval

- `build-prod.yml` has a `trstringer/manual-approval` step (2 approvals). But it is a step, not an environment rule. The approval job itself already runs inside `customer_app_prod`.
- `build-prod-artifact.yml` runs in `customer_app_prod` with no approval at all. It builds a prod-signed APK and IPA and uploads them as run artifacts.
- `pr-pipeline.yml` and `on-merge-master.yml` ignore changes under `.github/**`. So a PR that only adds a workflow gets no CI checks.

### Android code shrinking (R8)

- `digital/android/app/build.gradle`, `release` build type (line 185): sets `proguardFiles`, but not `minifyEnabled` or `shrinkResources`. Android Gradle Plugin 8.12.1 defaults both to off. So R8 does not run.
- `proguard-rules.pro` has 92 lines. It keeps MediaPipe, protobuf and Insider classes. It has no rules for Vida, AppsFlyer, Datadog, Mixpanel or Firebase. Most of these ship their own rules inside the library, but Vida must be checked with the vendor.
- `build-prod.yml` uploads `build/app/outputs/mapping/prodRelease/mapping.txt` to Datadog, and Crashlytics has `mappingFileUploadEnabled true`. That file only exists when R8 runs. So both uploads have nothing to send today.
- Dart code is obfuscated (`--obfuscate --split-debug-info`). Java and Kotlin code is not.

### Secrets and flags built into the app

- `digital/lib/app/app_config.dart:33` reads `API_SECRET` from `--dart-define`. `data/customer/lib/src/http_client.dart:35` sends it as the `api-secret` header on every request. Anyone can pull it out of the APK.
- The root/jailbreak check is behind `IS_DEVICE_ROOT_CHECKER_ENABLED` (`app_config.dart:19`). It uses `bool.fromEnvironment`, so the **code default is off**. The prod GitHub variable is `true` today, so prod is protected. If that variable is ever missing, the check silently turns off.
- The check itself fails closed: `app_controller.dart:263` treats an error as "jailbroken". It runs once, at app start.
- `IS_HTTP_PROXYING_ALLOWED` is `false` for prod and `true` for SIT. Same risk: the code default decides what happens if the variable is missing (here the default is safe).

### What is already good

- Certificate pinning: `http_client.dart:44` (`allowedSHAFingerprints`).
- Device integrity: `x-integrity-id` header from `bfi-flutter-device-integrity` v1.2.1 (Play Integrity / App Attest).
- Storage: all 26 keys in `AppPreferencesKey` go through `FlutterSecureStorage` (`shared_lib/core/lib/src/shared_preferences/app_preferences.dart`). Android uses `encryptedSharedPreferences: true`. iOS uses `first_unlock` keychain access. No `SharedPreferences`, Hive or SQLite elsewhere.
- `android:allowBackup="false"` in `AndroidManifest.xml`.

### Gaps

- **No screen-capture guard.** No `FLAG_SECURE` and no iOS capture handling anywhere in `digital/`.
- **Files in the documents folder are plain files.** `FileService.saveImageToFile` writes images to `getApplicationDocumentsDirectory()`. It is called from `camera_service.dart`, `image_picker_service.dart`, the loan draft loader and asset verification. Some of these are KYC or vehicle photos.
- **No RASP** (runtime self-protection: anti-tamper, anti-hook, anti-debug).
- **`project.pbxproj` is tracked** although `.gitignore:59` excludes it. `project.pbxproj.backup` is tracked too.
- **WebView with JavaScript** in `features/loan/survey/online_survey/online_survey_screen.dart`. Needs a URL allowlist check.

## Target (what Jago does, adapted for BFI)

| Jago pattern | Path | BFI adaptation |
|---|---|---|
| R8 on, with resource shrinking | `app_jago_mobile/android/app/build.gradle` (`minifyEnabled true`, `shrinkResources true` on release types) | Same, in `digital/android/app/build.gradle` |
| Code protection after build | `app_jago_mobile/tools/everspin/android/scripts/run_android_codemix.sh` | A protection step in `build-prod.yml`, once a vendor is chosen |
| Build registration for forgery checks | `tools/everspin/android/scripts/upload_android_eversafe.sh` | Post-build step, same vendor |
| Screen-capture guard by route | `app_jago_mobile/lib/common/security/screen_capture/` (guard, policy, route list, navigator observer; 502 lines) | A `go_router` observer plus a route allowlist. Behind a Remote Config flag |
| Prod signing in a separate repo | `prod-pipelines/jago-mobile` | Not needed. Protect the GitHub environment instead |

How Jago's screen guard works, in short: a navigator observer tracks which routes are on screen. A policy checks each route against a list of protected routes (PIN entry, password, card details and so on). A method channel turns the native capture block on or off. A remote flag can switch the whole thing off.

**Do not copy:** Jago's vendor configuration, keys, app IDs or certificates. Do not copy the separate prod-pipeline repository; it adds a second repo to maintain.

## Plan

### Step 0 (urgent, this week): remove "Reveal Secret" and lock prod

Owner: SRE with the squad lead. One PR per branch, plus settings changes.

1. Delete `.github/workflows/test.yaml` from `master` and from `release-2.24.x`, `release-2.25.x`, `release-2.26.x`, `release-2.27.x`. Disable the workflow in the Actions UI first, so it cannot run while PRs wait.
2. Rotate `BRAVO_GCP_SA_KEY` and `SSH_PRIVATE_KEY`. Do it even though the one run (31 Dec 2025) failed before any step started. Anyone who could dispatch the workflow could have read them.
3. Add required reviewers to the `customer_app_prod` environment. Also add a deployment branch rule: only `master`, `release-*` and `v*` tags. Do the same for `customer_app_prod_test`.
4. Add a CI check that fails any workflow which echoes `secrets.*`. See the sketch below.
5. Do **not** open the old run's logs to "check". The API metadata is enough.

```bash
# .github/scripts/check-workflow-secrets.sh (sketch)
# Fails if any run: line echoes or prints a secrets.* expression.
if grep -nE '(echo|printf|cat).*\$\{\{ *secrets\.' .github/workflows/*.y*ml; then
  echo "::error::Workflows must not print secrets"; exit 1
fi
```

Run this check from a small workflow that is **not** path-filtered, so PRs that touch only `.github/**` also get it.

How to check: the Actions API no longer lists "Reveal Secret". `GET /environments` shows a `required_reviewers` rule on `customer_app_prod`. A test PR that adds `echo ${{ secrets.X }}` fails.

### Step 1: turn on R8 (1 PR, 1 sprint)

- In `digital/android/app/build.gradle`, `release`: add `minifyEnabled true` and `shrinkResources true`.
- Add keep rules only where a library needs them. Check each SDK's docs: Vida liveness and idFraudShield (ask Vida), Insider (rules exist), AppsFlyer, Datadog, Mixpanel and session replay, Firebase, MediaPipe (rules exist), `flutter_inappwebview`, `bfi_document_detection`.
- Build a `prod` release locally and on SIT. Run the smoke list: login, OTP, KYC liveness, document capture, loan submission, payment, push notification, deep link, in-app update.
- Confirm `mapping.txt` now exists, and that Crashlytics and Datadog show readable Android stack traces.

How to check: `apkanalyzer` shows renamed classes. APK size drops. No new crash types in the first week on the Play internal track.

### Step 2: make the security flags fail safe (1 small PR)

- Change `isDeviceRootCheckerEnabled` to `bool.fromEnvironment('IS_DEVICE_ROOT_CHECKER_ENABLED', defaultValue: true)`.
- Add a CI step in prod workflows that fails if `IS_DEVICE_ROOT_CHECKER_ENABLED` is not `true` or `IS_HTTP_PROXYING_ALLOWED` is not `false`.
- Re-run the root check when the app returns to the foreground, not only at start.

### Step 3: treat `API_SECRET` as public (backend + app, 1–2 sprints)

- Write down that `api-secret` is not a security control. It only tags traffic as "from our app".
- Backend (Customer BFF owners): make sure every sensitive endpoint checks the user token and the `x-integrity-id` verdict. No endpoint may accept `api-secret` alone.
- Rotate the value once the backend no longer depends on it. Later, remove it.

### Step 4: screen-capture guard (1–2 PRs)

- Add `digital/lib/app/security/screen_capture/`: a `go_router` observer, a list of protected route names, and a method channel.
- Android: set `FLAG_SECURE` on the activity window while a protected route is on top.
- iOS: hide content when `UIScreen.capturedDidChange` fires, and show a blur on app-switcher snapshots.
- Start with: PIN entry and reset, OTP, KTP and selfie capture, KYC review, agreement and e-sign, bank account form, payment details.
- Put it behind a Remote Config flag so it can be turned off if a device misbehaves.

### Step 5: secure storage review (1 PR)

- List what `FileService` writes and how long it stays. Delete KYC and vehicle images after upload.
- Write those files to the app cache or a temporary folder, not the documents folder. Exclude them from iCloud backup.
- Review `loanSubmissionDrafts` and `lastRepaymentPaymentDetails`. Keep only what the screen needs.
- Check WebView: allow only BFI domains in `online_survey_screen.dart`.

### Step 6: clean up `project.pbxproj` (1 PR)

- Decide: `project.pbxproj` is the source of truth (Xcode projects need it). Remove the `.gitignore:59` line so the rule matches reality.
- Delete `project.pbxproj.backup`.

### Step 7: choose a RASP vendor (decision, then 1–2 sprints)

Use these criteria. Prices need real quotes; none are given here.

| Criterion | Why it matters |
|---|---|
| Works with Flutter release builds on Android (AAB) and iOS | Some tools only handle native apps |
| Protects after the build, without changing source code | Keeps the app code clean |
| Anti-tamper, anti-hook (Frida), anti-debug, root/jailbreak, emulator detection | Core RASP features |
| Server-side verdict or build registration | Lets the backend reject forged apps, like Jago's Eversafe registration |
| Runs in GitHub Actions on Linux and macOS runners | Fits our pipeline |
| Effect on app size and start time | Measured on our app, not the vendor's demo |
| Support in Indonesia, OJK and BI audit evidence | Needed for regulator reviews |
| Licence model (per app, per install, per year) | Budget fit |

Candidates to ask for quotes: Everspin Eversafe and CodeMix (what Jago uses), Promon SHIELD, Guardsquare DexGuard and iXGuard, Appdome, Talsec freeRASP (free tier) or its paid tier. Then the protection step goes into the CI/CD plan.

### Step 8: OWASP MASVS mapping (living table)

MASVS is the OWASP list of mobile security requirements. Keep this table in the repo and update it each quarter.

| MASVS group | BFI today | Action in this plan |
|---|---|---|
| STORAGE | Secure storage for keys; plain image files in documents folder | Step 5 |
| CRYPTO | Platform keystore and keychain via `flutter_secure_storage` | None now |
| AUTH | PIN, OTP, tokens; `API_SECRET` in app | Step 3 |
| NETWORK | TLS + certificate pinning | Check pin rotation process |
| PLATFORM | WebView with JS; no screen-capture guard | Steps 4, 5 |
| CODE | Dart obfuscated; R8 off | Step 1 |
| RESILIENCE | Root check, Play Integrity, App Attest; no RASP | Steps 2, 7 |
| PRIVACY | Mixpanel session replay, several trackers | Review masking with the analytics plan |

## Done when

- `test.yaml` is gone from `master` and every `release-*` branch. The Actions API lists no "Reveal Secret" workflow.
- `customer_app_prod` and `customer_app_prod_test` have required reviewers and a branch policy.
- A PR that echoes `secrets.*` in a workflow fails CI, even if it only touches `.github/**`.
- `BRAVO_GCP_SA_KEY` and `SSH_PRIVATE_KEY` have new values (SRE confirms; values never shared).
- The prod AAB is built with R8. `mapping.txt` is uploaded to Crashlytics and Datadog.
- A prod build with `IS_DEVICE_ROOT_CHECKER_ENABLED` unset still runs the root check.
- No sensitive endpoint accepts a request with only `api-secret`.
- Protected routes show a black screen in screenshots and screen recordings on Android and iOS.
- A RASP vendor decision is recorded.

## Effort and owner

- Step 0: **S**, days, not sprints. Owner: SRE (secrets, environments), squad lead (PRs).
- R8, flags, storage, pbxproj, screen guard: **S**, about 2 sprints in total. Owner: Customer Mobile Apps squad.
- `API_SECRET`: **S** on the app, backend effort depends on the BFF team.
- RASP: **M** (2–4 sprints after the vendor is chosen). Owner: Security with the squad. Budget owner: IT management.

## Depends on / related plans

- Mobile plan 13: CI/CD (protection step slot, environment protection, workflow checks).
- Mobile plan 12: Lint and guardrails (workflow secret check as a CI rule).
- Mobile plan 11: Testing (smoke list for the R8 build; e2e on protected builds).
- Mobile plan 05: Analytics wrapper (session replay masking for PRIVACY).
- Mobile plan 06: Logging and crashes (readable Android traces after R8).

## Risks

| Risk | Mitigation |
|---|---|
| R8 strips a class used by reflection; a crash appears only in release | Smoke list on a prod-like build; roll out on Play internal track first |
| Rotating `SSH_PRIVATE_KEY` breaks git dependency fetches in CI | Update every workflow secret and deploy key in the same change window |
| Required reviewers slow down urgent hotfixes | Name at least 3 reviewers across SRE and release engineering |
| Screen guard blocks legitimate support screenshots | Limit to the route list; flag to switch off |
| RASP flags real users on custom ROMs | Start in report-only mode; watch false-positive rate before blocking |
| Backend still relies on `api-secret` somewhere unknown | Search BFF code and gateway config before rotating it |
