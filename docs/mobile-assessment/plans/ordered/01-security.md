**Priority 1 of 13.** Phase 0. A workflow can expose prod secrets today, and no GitHub environment is protected. R8 already runs (corrected 14 Oct 2026); making it explicit is a one-line change.

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

*Corrected 14 Oct 2026, after team review. The first version of this page said R8 was off. That was wrong.*

- R8 **is on** for every release build. `digital/android/app/build.gradle` does not set `minifyEnabled`, but the Flutter Gradle plugin sets `isMinifyEnabled = true` on the release build type whenever its `shrink` property is not set to false, and nothing in BFI's workflows or Gradle files sets it. Source: `FlutterPlugin.kt` and `FlutterPluginUtils.shouldShrinkResources` in the Flutter repository.
- Datadog confirms it: Android crashes in production carry `r8-map-id-…` frames, which R8 writes, and the class names are readable because the `mapping.txt` upload in `build-prod.yml` works.
- What is still true: the setting is implicit. A Flutter upgrade, a `--no-shrink` flag, or a copied Gradle block could switch it off without anyone noticing, and nothing in CI would fail. `proguard-rules.pro` (92 lines) keeps MediaPipe, protobuf and Insider; it has never been reviewed against the other SDKs.
- Dart code is obfuscated too (`--obfuscate --split-debug-info`).

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
| R8 on, set explicitly | `app_jago_mobile/android/app/build.gradle` (`minifyEnabled true`, `shrinkResources true` on release types) | BFI already has R8 on through Flutter's default. Set it explicitly in `digital/android/app/build.gradle` so it does not depend on tooling defaults |
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

### Step 1: make R8 explicit and review the keep rules (1 PR)

*Corrected 14 Oct 2026: this step used to say "turn on R8". R8 already runs; the step is now about making that fact visible and safe.*

- In `digital/android/app/build.gradle`, `release`: add `minifyEnabled true` and `shrinkResources true`. This changes nothing in the output today. It stops a tooling default from switching R8 off silently.
- Add a CI step in the prod build that fails if `build/app/outputs/mapping/prodRelease/mapping.txt` is missing (Mobile plan 04: CI/CD, step 5).
- Review `proguard-rules.pro` against every SDK that uses reflection: Vida liveness and idFraudShield (ask Vida), AppsFlyer, Datadog, Mixpanel and session replay, Firebase, `flutter_inappwebview`, `bfi_document_detection`. Most ship their own rules; confirm, do not assume.
- Build a `prod` release and run the smoke list: login, OTP, KYC liveness, document capture, loan submission, payment, push notification, deep link, in-app update. The output should match today's build.

How to check: the release block shows both settings. A prod build with `-Pshrink=false` fails CI because `mapping.txt` is missing. Crashlytics and Datadog still show readable Android stack traces.

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

### Step 7: RASP — free baseline now, then choose a vendor (decision, then 1–2 sprints)

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

#### Option A: free and open-source layer (start now, no vendor needed)

These are worth doing whatever vendor we pick. Together they are a solid baseline. They are not a full RASP: their checks are public, so ready-made bypass scripts exist. Both RootBeer and IOSSecuritySuite say in their own docs that they can be bypassed.

| Tool | What it gives us | Licence and cost | BFI today |
|---|---|---|---|
| Play Integrity API (Android) and App Attest (iOS) | Google or Apple signs a verdict: real app, real device, not tampered. The backend checks the verdict. This is the strongest free layer, because the check happens on the server | Free, platform service | Already sends `x-integrity-id`. Check the backend really rejects bad verdicts on sensitive endpoints |
| R8 / ProGuard | Shrinks and renames Java and Kotlin code | Free, part of the Android build tools | On today through Flutter's default. Step 1 makes it explicit and reviews the keep rules |
| Dart `--obfuscate` | Renames Dart symbols | Free, part of Flutter | Already on |
| RootBeer (Android) | Root checks: su binaries, Magisk, test keys, writable system | Apache 2.0, free | Used inside `flutter_jailbreak_detection` |
| IOSSecuritySuite (iOS) | Jailbreak, debugger, emulator, hooks, file tampering checks | **1.x is BSD 2-Clause (free). 2.x is a paid EULA by headcount: over 1,000 staff needs the "Standard+" plan** | Pinned at 1.9.11 in `Podfile.lock`. Do not upgrade to 2.x without a licence |
| `flutter_jailbreak_detection` | Flutter wrapper around the two above | Open source | BFI already uses a fork (`bfi-flutter-packages` v3.0.0) |
| Talsec freeRASP | Root, jailbreak, Frida and other hooks, tampering, emulator, debugger, Appium, VPN, malware checks, in one Flutter plugin | Free under a fair usage policy. The Flutter wrapper is MIT; the core is a closed binary owned by Talsec | Not used |

**freeRASP needs care.** It is free only up to 100,000 unique devices across the whole organisation. Above that, the app must show "Protected by freeRASP" with its logo, and Talsec may list the app in its marketing. The free tier also sends security telemetry to Talsec. The BFI customer app is likely above 100,000 devices. So freeRASP is fine for a trial in SIT, but for production we would need the paid tier (RASP+), which removes the cap and keeps telemetry in our own systems. The telemetry also needs a data-protection review before any production use.

**Other pub.dev RASP plugins** (for example `advanced_root_detection`, `enhanced_jailbreak_root_detection`, `flutter_secure_app`) are early versions (0.0.x for some) with small teams. Do not use them in a regulated lending app without a code review and an owner.

#### Option B: commercial RASP and app shielding (shortlist for quotes)

All of these say they support Flutter apps. "Confirm" means we did not find it stated clearly, so ask in the RFP.

| Vendor and product | How it works | Licence model | Notes |
|---|---|---|---|
| Promon SHIELD | Added after the build, in the pipeline | By active users | RASP-first, common in banking. Rich telemetry and callback APIs to feed a backend fraud engine. Also offers app attestation (Verify) and analytics (Insight). Lighter on code obfuscation |
| Guardsquare DexGuard (Android) and iXGuard (iOS) | Build-time: a Gradle plugin and the Xcode toolchain inject the protection | By app downloads, in 3 tiers (Core, Control, Command). Server-side attestation needs Command | Strongest on obfuscation. A different (polymorphic) protection layer for every build. ThreatCast for monitoring. Flutter support stated by the vendor |
| Appdome | No-code: the built app goes in through an API in CI/CD (about 2–10 minutes), a protected app comes out. We sign it ourselves | Flat yearly fee per app (Android + iOS), unlimited users | Soft exits and local-language warnings instead of crashing the app. Can forward detections as headers to our backend or WAF. A certificate of the protections per build, useful for audit |
| V-Key (V-OS) | SDK with a software "virtual secure element" that isolates keys and sensitive code | Flat yearly subscription (details on request) | Strongest on device binding and identity (smart token, biometrics, MFA). Also blocks screen sharing and checks accessibility and side-loaded apps. Confirm Flutter |
| Everspin Eversafe + CodeMix | Wraps the built app; build registration for forgery checks | Ask | What Jago's prod pipeline uses. Supplies financial institutions in Indonesia |
| DoveRunner (formerly AppSealing, INKA Entworks) | Seals the built app: obfuscation, encryption, RASP | Ask | Used by Kredivo in Indonesia. Confirm Flutter |
| Talsec RASP+ (paid freeRASP) | Same plugin as freeRASP, no device cap, own telemetry, plus AppiCrypt for API checks | Ask | Easiest move from a freeRASP trial |
| Licel DexProtector | Build-time protection with RASP | Ask | Flutter page on the vendor site |
| Build38 | Flutter plugin using Dart FFI | Ask | Dedicated Flutter product |
| Zimperium (zShield / MAPS) | Obfuscation, anti-tamper, RASP | Ask | Cross-platform frameworks stated. Confirm Flutter |
| LIAPP (Lockin Company) | Obfuscation, anti-tamper, root and VM checks | Ask | iOS only on the Enterprise plan. Confirm Flutter |

**Licence model matters for BFI.** Pricing by active users or downloads grows with our customer base. A flat fee per app stays the same as we grow. Ask every vendor for a 3-year cost at today's users and at 2× today's users.

#### Proof-of-concept scorecard

Every shortlisted vendor runs the same PoC on our prod-like build. A vendor passes only if it meets all of these.

| Phase | Check | Pass mark |
|---|---|---|
| 1. Integration | Added to our GitHub Actions build for Android and iOS | Done in under 5 working days |
| 1. Integration | Source code changes needed | None or very few |
| 1. Integration | Extra build time | Under 5% longer pipeline |
| 2. Detection | Hooking: Frida, Magisk | Detected, every time, in real time |
| 2. Detection | Environment: root, jailbreak, emulator, KernelSU | Detected, every time |
| 2. Detection | Debugger attach and code injection | Detected, every time |
| 2. Detection | Server-side attestation | Reliable verdicts our backend can check |
| 3. Users | Real users blocked by mistake | Zero critical false positives |
| 3. Users | Crashes caused by the RASP | Zero |
| 3. Users | App start and transaction speed | No change users can notice |
| Support | Threat dashboard | Working, readable, real-time |
| Support | Response during the PoC | Under 4 hours for critical issues |

Add our own red team (or the pentest vendor) to try to bypass each candidate during the PoC.

#### Recommendation

1. Now, free: make R8 explicit (step 1), make the root check fail safe (step 2), and make the backend enforce the Play Integrity and App Attest verdicts on sensitive endpoints (step 3). Keep IOSSecuritySuite below 2.0, or budget for its licence.
2. Trial: run freeRASP in report-only mode on SIT builds for 2 sprints. Use it to measure false positives on our users' kinds of devices. Do not ship it to prod on the free tier.
3. RFP and PoC: ask Promon, Guardsquare, Appdome and V-Key for quotes and a PoC, scored with the scorecard above. Add Everspin and DoveRunner if a local Indonesian support team is a must-have. Add Talsec RASP+ if the trial went well.
4. Pick by fit: Promon if fraud telemetry into our backend matters most; Guardsquare if protecting the code itself matters most; Appdome if speed and a flat cost matter most; V-Key if device binding and in-app identity (tokens, MFA) matter most.

Vendor calls, findings and the filled-in scorecard live on the child page **Mobile plan 01a: RASP vendor comparison**, one section per vendor.

Then the protection step goes into the CI/CD plan.

### Step 8: OWASP MASVS mapping (living table)

MASVS is the OWASP list of mobile security requirements. Keep this table in the repo and update it each quarter.

| MASVS group | BFI today | Action in this plan |
|---|---|---|
| STORAGE | Secure storage for keys; plain image files in documents folder | Step 5 |
| CRYPTO | Platform keystore and keychain via `flutter_secure_storage` | None now |
| AUTH | PIN, OTP, tokens; `API_SECRET` in app | Step 3 |
| NETWORK | TLS + certificate pinning | Check pin rotation process |
| PLATFORM | WebView with JS; no screen-capture guard | Steps 4, 5 |
| CODE | Dart obfuscated; R8 on by default, not set explicitly | Step 1 |
| RESILIENCE | Root check, Play Integrity, App Attest; no RASP | Steps 2, 7 |
| PRIVACY | Mixpanel session replay, several trackers | Review masking with the analytics plan |

### Parity check

- See "Keeping features identical" on the parent page for the switch flag, parity net, parity ledger and approved deltas.
- R8 already runs on every release build, so the risk that it strips a class an SDK reaches by reflection is live today. Step 1 reviews the keep rules; a change there could break a journey without a compile error.
- R8 parity: after step 1, the build with the explicit settings and reviewed keep rules must pass the same smoke list and the same e2e journeys in automation-monorepo (`packages/mobile-automation/bfi-mobile`) as today's build.
- The analytics golden names file (Mobile plan 02: Analytics wrapper, step 1) must show the same events on both builds.
- Step 5 changes where KYC and vehicle images are stored. The KYC and document capture journeys in the parity net must pass before and after.
- Approved deltas (meant to differ, signed off, excluded from the parity check): the screen-capture block (step 4), the root check on by default (step 2), and real Datadog consent instead of a constant.
- The screen-capture Remote Config flag (step 4) is a kill switch, not a switch flag. There is no old path to keep.

## Done when

- `test.yaml` is gone from `master` and every `release-*` branch. The Actions API lists no "Reveal Secret" workflow.
- `customer_app_prod` and `customer_app_prod_test` have required reviewers and a branch policy.
- A PR that echoes `secrets.*` in a workflow fails CI, even if it only touches `.github/**`.
- `BRAVO_GCP_SA_KEY` and `SSH_PRIVATE_KEY` have new values (SRE confirms; values never shared).
- `minifyEnabled` and `shrinkResources` are set explicitly in `build.gradle`, and the prod build fails when `mapping.txt` is missing. Crashlytics and Datadog keep receiving it (they do today).
- A prod build with `IS_DEVICE_ROOT_CHECKER_ENABLED` unset still runs the root check.
- No sensitive endpoint accepts a request with only `api-secret`.
- Protected routes show a black screen in screenshots and screen recordings on Android and iOS.
- A RASP vendor decision is recorded.
- The build with explicit R8 settings and reviewed keep rules passes the same smoke list and the same e2e journeys as today's build.
- The screen-capture block, the root-check default and Datadog consent are listed as approved deltas in the parity ledger and signed off.

## Effort and owner

- Step 0: **S**, days, not sprints. Owner: SRE (secrets, environments), squad lead (PRs).
- R8 (explicit setting, keep-rule review), flags, storage, pbxproj, screen guard: **S**, about 2 sprints in total. Owner: Customer Mobile Apps squad.
- `API_SECRET`: **S** on the app, backend effort depends on the BFF team.
- RASP: **M** (2–4 sprints after the vendor is chosen). Owner: Security with the squad. Budget owner: IT management.

## Depends on / related plans

- Mobile plan 04: CI/CD (protection step slot, environment protection, workflow checks).
- Mobile plan 06: Lint and guardrails (workflow secret check as a CI rule).
- Mobile plan 03: Testing (smoke list for the R8 build; e2e on protected builds).
- Mobile plan 02: Analytics wrapper (session replay masking for PRIVACY).
- Mobile plan 05: Logging and crashes (Android traces are already readable; the `mapping.txt` upload must keep working).

## Risks

| Risk | Mitigation |
|---|---|
| A keep-rule change lets R8 strip a class used by reflection; the crash appears only in release | Smoke list on a prod-like build; roll out on Play internal track first |
| Rotating `SSH_PRIVATE_KEY` breaks git dependency fetches in CI | Update every workflow secret and deploy key in the same change window |
| Required reviewers slow down urgent hotfixes | Name at least 3 reviewers across SRE and release engineering |
| Screen guard blocks legitimate support screenshots | Limit to the route list; flag to switch off |
| RASP flags real users on custom ROMs | Start in report-only mode; watch false-positive rate before blocking |
| Backend still relies on `api-secret` somewhere unknown | Search BFF code and gateway config before rotating it |
