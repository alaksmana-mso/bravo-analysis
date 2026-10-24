## Summary

We want the BFI customer app (`bravo-customer-app`) to follow the DK Jago app (`digital_banking_app`). This page compares the two. It lists the gaps and suggests an order of work.

- **CI/CD and basic security are closer to Jago than expected.** BFI already obfuscates release builds and pins certificates. It checks for rooted devices, uses Play Integrity and App Attest, uploads to Play and TestFlight, and has a manual approval gate for prod.
- **Architecture is the biggest gap.** BFI has no domain layer and no module boundaries. Screens and controllers use API models (DTOs) directly. Jago has a pure-Dart domain layer, feature modules, and written layer rules.
- **Analytics needs one wrapper.** BFI sends events two ways: 187 Firebase `logEvent` calls with 148 hard-coded event names, mostly in screens, and a separate typed Mixpanel tracker. Jago has one analytics interface that fans out to every platform, with typed events. This is the best quick win.
- **Testing has no safety net.** BFI's PR pipeline rejects controller tests. No coverage threshold is enforced. There are no end-to-end tests. Jago gates coverage on changed files and runs Appium end-to-end tests.
- **App protection is missing.** Jago wraps every prod build with Everspin (anti-tamper and code protection) and registers each build. BFI has nothing like this, and Android code shrinking (R8) is probably off.
- **One urgent security item:** a GitHub workflow in the repo is built to print prod secrets in readable form. See the Security items section below.

**Decision already made:** keep Riverpod. Copy Jago's layers, ports and analytics wrapper, not its bloc library.

## Scope and evidence

| Item | BFI | Jago (reference) |
|---|---|---|
| Repository | `bfi-finance/bravo-customer-app` | DK GitLab `digital_banking_app` + `prod-pipelines/jago-mobile` |
| Revision read | `master` @ `190e1d20` (11 Sep 2026) | Local working copy, Oct 2026 |
| Stack | Flutter 3.41.9 in CI, Dart 3.10, Riverpod 2.6, dio, go_router | Flutter 3.38.8, Dart 3.10, bloc, injectable + Kiwi |
| Assessed on | 9 Oct 2026 | 9 Oct 2026 |

All findings come from reading source code and CI files. Nothing was run. Counts are from `grep` over `lib/` folders, without generated files.

**Jago is a reference, not a perfect target.** It has its own debt:

- It runs two DI systems at the same time (old Kiwi, new injectable).
- Its shared `module_common` package is too big, and new logic there is now forbidden.
- Its architecture rules are checked by code review, not by tooling.

Copy the target shape, not the debt.

## Side-by-side comparison

Effort: **S** = up to 1 sprint, **M** = 2–4 sprints, **L** = more than a quarter.

| Area | Jago | BFI today | Gap | Effort |
|---|---|---|---|---|
| Repo layout | Melos workspace. 4 apps, 49 `module_*` packages (features + shared), 110 `library/*` wrappers around pub.dev packages. | Melos workspace with 3 packages: `digital` (the app, 23 features), `data/customer` (API + models), `shared_lib/core`. | Every feature lives in one package. Nothing stops one feature from importing another. | L |
| Layering | `data → domain ← presentation` in every feature. Domain is pure Dart. Features talk through thin `*_api` contract packages. Rules are written down in `.claude/rules/layer-model.md` and `journey-clean-architecture.md`. | Screen → controller (`StateNotifier`) → sometimes a use case → repository → `HttpClient`. No `domain/` folder anywhere. Repositories return API models straight to the UI. | API changes reach the screens directly. Business rules sit in controllers and screens. | L |
| State management | bloc, with rules: no `BuildContext` or navigation inside blocs. | Riverpod 2.6 with the old `StateNotifier` API. 72 controllers. A global `appRef` is used in 142 places. | Keep Riverpod. Move to `Notifier` / `AsyncNotifier`. Remove the global `appRef`. | M |
| Dependency injection | injectable + get_it. Each module exposes a micro-package. Wiring happens only in the app layer. | Riverpod providers (128 `static final provider`). Environment objects are injected with `ProviderScope.overrides` in `main.dart`. | Riverpod is fine as DI. The gap is module boundaries: each feature package should expose its providers, and the app should wire them. | M (comes with layering) |
| Analytics wrapper | `AnalyticsPlatform` interface. One fan-out sends each event to Datadog, Firebase and CleverTap. Events are typed classes (`AnalyticsEventV2`), with name constants in about 55 files. Widgets fire an event; a bloc dispatches it. | Two separate paths. **Firebase:** 187 `logEvent` calls in 81 files, 148 event names as plain strings, almost all in screens. **Mixpanel:** a typed `EventTracker`, plus automatic tracking in the `Digital*` components. AppsFlyer and Insider have their own services. | No single interface. No event catalogue. Adding or replacing a platform means touching 80+ files. | S–M |
| Logging and crashes | `Monitoring` fans out to Crashlytics and Datadog. PII is cleaned by `jago_observability_sanitizer.dart`. | `DatadogLog` (59 mentions in app code; *corrected 9 Oct: the earlier "90 uses" counted test files*) forwards errors to Crashlytics with trace and session IDs. Flutter and platform errors are caught. | Good. Add a PII cleaner before logs leave the device. | S |
| Feature flags | Typed flag catalogue (`BoolFeatureFlag`, `IntFeatureFlag`, …) behind one `FeatureFlagPlatform` interface. Providers: Firebase Remote Config, Split.io, GrowthBook. | One very wide `RemoteConfig` model (its generated file is 2,443 lines), plus Mixpanel flags for experiments. | No typed catalogue, and no single interface across Remote Config and Mixpanel. | M |
| Networking | dio adapter behind a client interface. 17 typed exception classes mapped to error messages. Not interceptor-based yet (their own TODO). | One dio wrapper (`http_client.dart`, 496 lines). Token refresh and the 401 retry live inside the client, not in an interceptor. Errors are mapped to typed exceptions with `x-trace-id`. | Move auth, refresh and retry into dio interceptors. Split the client by concern. | S |
| Security | Everspin Eversafe anti-tamper (Android and iOS), CodeMix code protection on every prod build, each build registered for forgery checks, TrustDecision device fingerprint, screen-capture guard, certificate pinning. | Certificate pinning, root/jailbreak check (behind a flag), Play Integrity / App Attest (`x-integrity-id` header), Dart `--obfuscate`. **No `minifyEnabled`** on the Android release build, so R8 is probably not running. `API_SECRET` is built into the app. | No anti-tamper (RASP) or code protection. R8 likely off. | S (R8) / M (RASP, needs vendor) |
| Design system | `module_design_library`: tokens generated from a Figma export, brand and theme switching, Widgetbook published to GitLab Pages. | In-app `Digital*` classes (32, across `app/ui`, `app/widget` and `app/theme`) and theme in `digital/lib/app/`. Used well: 250 lines use `DigitalButton` vs 0 raw Material buttons, 1,040 lines use `DigitalColors` vs 49 raw colours. *Corrected 9 Oct: earlier counts (16 / 454 / 795 / 39) were wrong; the conclusion is the same.* | No separate package. No token pipeline from Figma. No Widgetbook. | M |
| Testing | About 5,288 test files. Coverage gate on **changed files** per module. End-to-end tests with Appium + Cucumber on BrowserStack. | 193 test files, 1,039 widget tests, mostly whole screens. **The PR pipeline rejects `*_controller_test.dart` files.** Coverage is uploaded to Codacy and Sonar. *Corrected 9 Oct:* `master` requires a "Codacy Diff Coverage" check, so a threshold may exist in Codacy settings (not visible in the repo). No integration or end-to-end tests in this repo; a separate mobile suite exists in `automation-monorepo` (WebdriverIO + Appium, 18 specs on 24 Oct 2026, including a KYC spec; still no register spec and no real payment journey). *Corrected 24 Oct 2026: an earlier version said 15 specs and no KYC spec.* | Logic can't be tested on its own. Unclear whether anything blocks a coverage drop. Nothing tests full journeys. | M |
| Lint and guardrails | `custom_lint` rules, Danger bot, checks for generated files and package use, `.claude/rules` (14 files) and skills, including an `mr-review` skill. | `lint/strict`, `dart format` check, generated-code check on merge, `AGENTS.md`. | No architecture checks. No review bot. | S |
| CI/CD | See the next section. | GitHub Actions, 13 workflows. | See the next section. | M |

## CI/CD compared step by step

Jago's prod pipeline lives in a **separate repository** (`prod-pipelines/jago-mobile`). The app repo only runs checks and triggers it.

| Step | Jago prod pipeline | BFI (`build-prod.yml` and others) | Gap |
|---|---|---|---|
| Trigger | Version tag, trigger branches, or manual on `master`. | Manual dispatch with a `manual-approval` gate. Weekly cron cuts the release branch. `standard-version` creates tags. | OK. |
| Toolchain | Flutter version pinned in one place (mise, CI image). | README says Flutter 3.38.5. CI uses 3.41.9. | Pin one version in one file (`mise.toml` or `.fvmrc`) and use it in CI and locally. |
| Version and build number | `X.Y.Z+W` from the tag. Build number from a CI counter. | `pubspec.yaml` fixed at `2.0.0+1`. CI overwrites it from the tag or an input. | OK, but use a CI counter for the build number so it always goes up. |
| Config | `dart tools/env.dart` writes config per environment. Firebase files are injected. | About 30 `--dart-define` values from GitHub secrets. Four flavors: dev, sit, uat, prod. | OK. Flavors are better than Jago's single build. |
| Build | `flutter build appbundle`, unsigned. iOS through fastlane. | `flutter build appbundle` / `ipa` with `--obfuscate --split-debug-info`. iOS through `xcodebuild`. | Consider fastlane + match for iOS signing. |
| Code protection | CodeMix on the unsigned bundle, then `zipalign`, then `apksigner`. | None. R8 probably off. | **Add R8 now. Choose a RASP vendor.** |
| Signing | Prod keystore only in the prod pipeline repo. | Keystore and certificates as base64 GitHub secrets, decoded at build time. | Acceptable. Restrict who can run prod workflows (see security items). |
| Distribution | Play internal track (script). TestFlight through fastlane. Optional GCS copy for test automation. | Play internal track (`r0adkll/upload-google-play`). TestFlight (`apple-actions/upload-testflight-build`). Firebase App Distribution for dev, SIT and UAT. | OK. |
| Post-build | Eversafe build registration (forgery tracking). | Upload debug symbols to Crashlytics and Datadog. | Add registration once a RASP vendor is chosen. |
| PR checks | Lint (+ custom rules), format, generated files, package rules, tests with random order, coverage on changed files, Danger. | Conventional PR title, block `feat` into release branches, Melos bootstrap check, analyze, tests, Codacy/Sonar upload. | Add a coverage gate on changed files. Remove the controller-test ban. |

## What else to work on

These go beyond the four areas we started with.

### 1. Upgrade old dependencies

- Riverpod 2.6 (`StateNotifier` is the legacy API) and freezed 2.5 (version 3 is current).
- Firebase is one major version behind (`firebase_core` 3.15, analytics 11.6, crashlytics 4.3, messaging 15.2).
- `flutter_markdown` 0.6 is discontinued.
- `lottie` 2.7 and `geolocator` 11.1 are several major versions behind.
- Forked git dependencies (`bfi-flutter-packages`, `bfi-flutter-device-integrity`, image-validation SDK) are pinned by tag or SHA. Each needs an owner and an upgrade path.
- `flutter_meta_sdk` is in `pubspec.yaml` but no Dart code imports it.

### 2. Split the largest files

The top five are all in the loan, onboarding and KYC flows.

| File | Lines |
|---|---|
| `loan/detail/loan_detail_screen.dart` | 1,315 |
| `loan/submission/submission_controller.dart` | 1,140 |
| `loan/submission/review/review_submission_screen.dart` | 1,139 |
| `onboarding/product/product_screen.dart` | 1,004 |
| `auth/kyc/kyc_use_case.dart` | 970 |

`router.dart` holds every route in 870 lines. Split it per feature, the same way Jago has one `*_routes.dart` per journey.

### 3. Other items

- **Fix the README.** It points to a `melos.yaml` that doesn't exist and to the old `release-2.0.0` branch.
- **Add end-to-end tests** for the main journeys (register, KYC, loan submission, payment). Jago uses Appium + Cucumber on BrowserStack.
- **Translations.** Only Indonesian exists (`app_id.arb`), and there is no sync tool. Jago syncs its copy with Ditto. This is low priority unless an English version is planned.
- **AI rules and skills.** Copy Jago's approach: `.claude/rules` for the layer rules, and an `mr-review` skill that checks a diff against those rules. BFI already has `AGENTS.md` and a `sync-ai-rules` workflow to build on.

## Security items

### 1. A workflow can print prod secrets in readable form (urgent)

- **File:** `.github/workflows/test.yaml`, named "Reveal Secret".
- **Added:** commit `70ed19f3`, 31 Dec 2025. It is still on `master`, and (*added 9 Oct*) also on all four release branches `release-2.24.x` to `release-2.27.x`. The GitHub API shows no pull request for that commit.
- **What it does:** it runs on manual dispatch, inside the `customer_app_prod` environment. It echoes three secrets: `BRAVO_GCP_SA_KEY`, `KNOWN_HOSTS` and `SSH_PRIVATE_KEY`. Each one is piped through `sed 's/./& /g'`, which puts a space between every character.
- **Why that matters:** GitHub hides a secret in logs only when the exact value appears. With spaces added, the value no longer matches, so the full GCP service-account key and SSH private key would show in the job log. Anyone who can read the run logs could read them.
- **History:** the workflow has run once, on 31 Dec 2025. That run failed before any step started (the job shows no steps), so the secrets were most likely not printed. This was checked through the GitHub API; the log itself was not opened.

**Actions:**

1. Delete `test.yaml` from `master` and every release branch.
2. Rotate `BRAVO_GCP_SA_KEY` and `SSH_PRIVATE_KEY` anyway. They were exposed to anyone who could run the workflow, and that is the safe default.
3. Add required reviewers to the `customer_app_prod` environment (*added 9 Oct: today none of the 6 environments has any protection rule*), so no workflow can use prod secrets without approval.
4. Add a CI check that fails any workflow which echoes `secrets.*`.

### 2. Other items

- **Prod builds without approval** (*added 9 Oct*). `build-prod-artifact.yml` builds a prod-signed APK and IPA inside `customer_app_prod` with no approval. The approval in `build-prod.yml` is a job step, not an environment rule. PRs that only change `.github/**` skip CI.
- **Personal data in analytics** (*added 9 Oct*). The `apply_loan` event sends the full home address (`customer_address`) to Firebase (`home_loan_simulation.dart:368`). Loan amount, monthly income, marital status and loan purpose go to Mixpanel. Datadog tracking consent is hard-coded to granted (`main.dart:42`). Handled first in Mobile plan 02.
- **Root check default** (*added 9 Oct*). The check is on in prod through a GitHub variable, but the code default is off. If the variable goes missing, the check silently stops.

- **R8 probably off.** The Android `release` build type sets `proguardFiles` but not `minifyEnabled true`. Without it, R8 does not shrink or obfuscate Java and Kotlin code. Turn it on and test the release build.
- **`API_SECRET` is built into the app** and sent on every request. Treat it as public, because anyone can pull it out of the app. Do not let the backend rely on it for security.
- **`project.pbxproj` is tracked** even though `.gitignore` excludes it. A `project.pbxproj.backup` copy is also tracked. Decide which one is the source of truth and delete the backup.
- **No anti-tamper (RASP).** Jago uses Everspin Eversafe. For a lending app that handles KYC, this is worth a vendor decision.

## Plans (in priority order)

Each row of the comparison table has its own plan page, as a child of this page. The number is the priority.

| # | Plan | Why this position |
|---|---|---|
| 01 | [Mobile plan 01: Security](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831712582) | Secrets workflow, unprotected prod environment, R8 |
| 02 | [Mobile plan 02: Analytics wrapper](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831057216) | Personal data in events today; one interface for all SDKs |
| 03 | [Mobile plan 03: Testing](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831614206) | Coverage gate and controller tests protect every refactor |
| 04 | [Mobile plan 04: CI/CD](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831057239) | One Flutter version, protected prod builds |
| 05 | [Mobile plan 05: Logging and crashes](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831614229) | PII cleaner for logs and crash reports |
| 06 | [Mobile plan 06: Lint and guardrails](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831778004) | Ratchet checker before the architecture work |
| 07 | [Mobile plan 07: Networking](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831483095) | Interceptors; fixes a token-refresh race |
| 08 | [Mobile plan 08: Layering](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831057259) | Domain layer, loan first |
| 09 | [Mobile plan 09: State management](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831778025) | Riverpod 3, then Notifier; remove global appRef |
| 10 | [Mobile plan 10: Dependency injection](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831483118) | Ports and one composition root on Riverpod |
| 11 | [Mobile plan 11: Repo layout](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2832269523) | Feature packages after layering is proven |
| 12 | [Mobile plan 12: Feature flags](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2831745435) | Typed flag catalogue |
| 13 | [Mobile plan 13: Design system](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2832924690) | Package + Widgetbook; adoption already high |

## Roadmap

The phases are in order. Each has an outcome, not a date.

### Phase 0: now

- Remove the "Reveal Secret" workflow and rotate the secrets.
- Protect the `customer_app_prod` environment.

### Phase 1: quick wins (about 1 sprint each)

| Work | Outcome |
|---|---|
| Analytics interface + event catalogue | One `AnalyticsPlatform`-style interface. Firebase, Mixpanel, AppsFlyer, Insider and Datadog become implementations. Events are typed. Screens call one method. The 187 string-literal calls are moved over feature by feature. |
| Turn on R8 | `minifyEnabled true` on release, with keep rules tested on a prod-like build. |
| Coverage gate on changed files | PRs fail if coverage on the changed files drops below an agreed number (copy Jago's `coverage-result.sh` idea). |
| One Flutter version | Pinned in one file and used by CI and developers. README fixed. |
| PII cleaner for logs | Logs are cleaned before `DatadogLog` and Crashlytics send them. |

### Phase 2: architecture (start with `loan`, the biggest feature at 130 files)

| Work | Outcome |
|---|---|
| Domain layer for `loan` | Pure-Dart entities and use cases. Repositories map API models to domain types. Screens never see API models. |
| Allow controller tests | Remove the ban. Test controllers and use cases directly. Keep the screen tests. |
| Move to `Notifier` / `AsyncNotifier` | Replace `StateNotifier` feature by feature. Remove the global `appRef`. |
| Split `loan` into its own package | `features/loan` becomes a package with a small public API. The app wires its providers. |
| Typed feature-flag catalogue | One interface over Remote Config and Mixpanel flags. |
| dio interceptors | Auth, refresh and retry move out of `HttpClient`. |

Repeat the domain-and-package step for `auth`, `rl`, `ro` and the rest once `loan` works.

### Phase 3: platform

| Work | Outcome |
|---|---|
| RASP / code protection | Vendor chosen (Everspin, or another). A protection step in the prod pipeline. Each build registered. |
| Design-system package | `Digital*` components and theme move to their own package, with Widgetbook. A Figma token pipeline is optional. |
| End-to-end suite | Main journeys covered on real devices. |
| Architecture checks in CI | A dependency-rule check (no feature-to-feature imports, domain has no Flutter imports), plus an `mr-review` skill. |

## Open questions

1. **Who owns this plan?** The Customer Mobile Apps squad, with a named tech lead.
2. **RASP vendor and budget.** Does BFI want Everspin (same as Jago), or a different vendor? This needs a quote.
3. **Coverage threshold.** What number for changed files? A suggested start is 70%, raised over time.
4. **Separate prod pipeline repo?** Jago keeps prod signing and distribution in a separate repo. That gives a smaller blast radius, but it is more to maintain. BFI could get most of the benefit by protecting the GitHub environment instead.
