## Summary

MyShaf is not a separate code base. It is the **Sharia flavour of the GENFI code** in `agent_tools/` of `bravo-agency-app`. The same Dart files build both apps. 37 `isSharia()` branches in 7 files decide what differs, 26 of them in `router.dart`. Everything on Genfi mobile app assessment applies to MyShaf. This page covers only what is different, and it leads to one decision that should be made before any engineering work on MyShaf.

* **Almost nobody uses it.** Datadog RUM recorded 12 MyShaf sessions in the last 30 days, all Android, all version 1.3.1. GENFI 1.16.0 recorded 238,470 sessions in the same window. The RUM sampling rate for MyShaf is a GitHub variable we could not read, so the true number may be higher, but not by the three orders of magnitude needed to match GENFI.
* **No release for four months.** The last MyShaf tag is `v1.3.1-beta.15-myshaf` (19 Jun 2026). Since then `agent_tools` received 135 commits and the shared packages 52, shipped to GENFI in 75 tags. None of those commits mention Sharia. The next MyShaf build will carry four months of change that nobody has run in the Sharia flavour.
* **CI has never worked for MyShaf.** The SIT pipeline ran 24 times since January 2026 and failed every time. The prod pipeline ran 8 times and failed every time, the last three at the Play Store upload step after the iOS job succeeded. The UAT pipeline has never run. The builds in the stores came from somewhere else, most likely a laptop.
* **No test runs the Sharia flavour.** The flavour is a compile-time `--dart-define=FLAVOUR`. Of 149 test files, none sets a Sharia flavour. The Sharia screens, routes and the device-integrity flow are untested.
* **Prod environments are unprotected (verified).** The GENFI page could not read this. On 26 Oct 2026 the GitHub API shows zero protection rules on `sharia_prod_myshaf` and on the other seven `sharia_*` environments.
* **Telemetry is weaker than GENFI's.** Crashlytics is not wired for the Sharia flavours at Gradle level and is skipped in `main.dart`. Firebase Analytics collection is only enabled when the flavour is convent, so the analytics wrapper sends nothing for MyShaf. Datadog RUM is on. MyShaf is the only flavour with a device-integrity check (Play Integrity / App Attest), behind a one-flag Remote Config model that defaults to on.
* **Decision first.** GENFI's open question 6 ("does MyShaf stay a flavour or become its own app") has a third answer: retire it. With 12 sessions a month, the cost of keeping a second flavour green through the GENFI roadmap is hard to justify. See the Options section.

**How MyShaf relates to GENFI**

## Scope and evidence

| **Item** | **MyShaf** | **GENFI (same code)** |
| --- | --- | --- |
| Repository | [bfi-finance/bravo-agency-app](https://github.com/bfi-finance/bravo-agency-app), folder `agent_tools`, flavours `sit_sharia`, `uat_sharia`, `prod_sharia` | Same folder, flavours `dev`, `sit`, `uat`, `prod` |
| Revision read | master @ 1e50b819 (22 Oct 2026) | Same |
| Store | `id.co.bfi.sharia.myshaf`; iOS id6479341998 v1.3.1 (19 Jun 2026); Android present. Last tag `v1.3.1-beta.15-myshaf` (19 Jun 2026) | `id.co.bfi.agenttools`; v1.16.0 (18 Sep 2026); last tag 22 Oct 2026 |
| Audience | Sharia partners and agents | Business agents (Agen Bisnis) |
| Datadog RUM | Application `MyShaf` (9a3558ab…), Flutter, active, event processing ALL | Agent Tools GENFI App |
| GitHub environments | `sharia_dev_myshaf`, `sharia_sit_myshaf`, `sharia_uat_myshaf`, `sharia_prod_myshaf`. All four have 0 protection rules (API, 26 Oct 2026) | `agency_*_agent_tools` |
| Pipelines | `myshaf-deploy-tag-cd-pipeline.yml` (SIT, tag push), `myshaf-uat-promote-tag-pipeline.yml` (UAT, dispatch), `myshaf-prod-deployment.yml` (prod, dispatch) | `agent-tools-convent-*`, `agent_tools_prod_release*.yaml` |
| Owner (README) | "owner: Agency, Sharia" | Agency |
| Assessed on | 26 Oct 2026 | 24 Oct 2026 |

All findings come from reading source and CI files at the revision above, the GitHub REST API (environments, workflow run lists, job conclusions) and Datadog RUM aggregates. Nothing was built or run. No workflow log was opened.

## How MyShaf is built from GENFI's code

`AppFlavor` has eight values. `getAppFlavor()` reads the `FLAVOUR` dart-define once at compile time and `isSharia()` is true for the three `*_sharia` values. Android `productFlavors` and iOS schemes exist per flavour. The Firebase and Crashlytics Gradle plugins are applied only to the four convent flavours (`build.gradle:133-139`).

What the Sharia flavour changes:

| **Area** | **Convent (GENFI)** | **Sharia (MyShaf)** | **Where** |
| --- | --- | --- | --- |
| Entry route | `/conventSplashScreen`, then registration and the convent onboarding | `/home`, redirect to `/onboarding` (OTP login) when logged out | `router.dart:205-227` |
| Top-level tabs | `ConventTopLevelScreen` with `ConventProfileScreen` | Older `TopLevelScreen` with `HomeScreen` and `ProfileScreen` | `router.dart:490-530, 1477, 1529` |
| Onboarding | `convent_onboarding_screen.dart` | `onboarding_screen.dart` with a device-integrity step | `feature/onboarding/` |
| Device integrity | Not run | Play Integrity / App Attest nonce flow, on unless `FEATURE_INTEGRITY_CHECK` Remote Config says off | `onboarding_screen_controller.dart:79-86`, `sharia_remote_config.dart` |
| Prospect flow | Convent prospect, PBF variants | Sharia prospect variants: reserve lead, confirmation, detail by group code, Sharia product list and footnotes | `feature/prospect/*`, 26 router branches |
| Crash reporting | Crashlytics on (release) | Off: no Gradle plugin, and `main.dart:129` skips the Crashlytics handlers and the FCM permission request | `main.dart:129-166`, `build.gradle:133` |
| Analytics | `ConventAnalyticsService` with collection enabled on app load | Same wrapper is wired, but `setCollectionEnabled()` is only called when `isConvent` (`app_controller.dart:14-20`). Nothing is sent | `app_controller.dart` |
| Datadog RUM | On | On, own application id, via `DATADOG_APP_ID` secret | `main.dart:44-78` |
| Feature flags | `ConventFeatureFlag`, 20 keys | `ShariaRemoteConfig`, 1 key | `app/common/sharia_feature_flag/` |
| Package id | `id.co.bfi.agenttools[.flavour]` | `id.co.bfi.sharia.myshaf[.flavour]` | `main.dart:168-178` |
| Localisation | One `app_id.arb` with Sharia strings mixed in (`shariaProducts`, `reservationSucceedSharia`) | Same file | `app/localizations/` |

The shared packages carry Sharia only as data: product codes, role names and application statuses in `agent_marketing`, `agency`, `keycloak` and `user_iam`. No shared package branches on the flavour.

The last commit that touched Sharia-only code was 16 Sep 2026 (`#5635`, admin management), as a side effect of a GENFI feature. The last commit made for MyShaf was 19 Jun 2026 (`fix myshaf app icon`, `#5518`).

## Usage

Datadog RUM sessions, last 30 days (26 Sep to 26 Oct 2026):

| **App** | **Version** | **Sessions** |
| --- | --- | --- |
| MyShaf | 1.3.1 (Android) | 12 |
| Agent Tools GENFI App | 1.16.0 | 238,470 |
| RO Tools-Prod (myBRO) | 3.50.3 | 78,554 |

No iOS session was recorded for MyShaf. The sampling rate is set per environment by the `DATADOG_SAMPLING_RATE` variable and could not be read. Product analytics retention for the MyShaf RUM application is NONE, so there is no longer history to check. The number of registered Sharia agents was not available to this assessment (open question 1).

## Side-by-side comparison

The GENFI comparison table applies row by row. This table lists only where MyShaf differs or where a shared finding hits MyShaf harder. Effort: S = up to 1 sprint, M = 2–4 sprints.

| **Area** | **Same as GENFI?** | **MyShaf difference** | **Effort** |
| --- | --- | --- | --- |
| Repo layout, layering, state management, DI, design system, lint | Yes | None. Every refactor on the GENFI roadmap changes MyShaf's binary too, with no test running the Sharia paths. | Comes with GENFI |
| Analytics wrapper | Partly | Wrapper wired, collection never enabled. Either enable it (one line) or remove the dead wiring. The GENFI page's "MyShaf coverage" gap is this. | S |
| Logging and crashes | Partly | No crash reporting at all except Datadog error tracking. `CrashReporter` is a no-op for this flavour by design. Decide whether MyShaf gets Crashlytics (needs the Gradle plugin for the Sharia flavours and the `google-services.json` that the prod workflow already decodes) or Datadog only. | S |
| Feature flags | Different | Two Remote Config models in one app: 20 convent keys and 1 Sharia key. GENFI plan 10 step "one catalogue for GENFI and MyShaf" covers it. | S (in plan 10) |
| Networking | Yes | Same `OtpHttpClient`. Different `API_HOST` per environment variable only. | None |
| Security | Partly | Device integrity runs only here. SIT builds have no `SHA_256_FINGERPRINT`, so testers run unpinned builds (UAT and prod pass it). `FEATURE_ENABLE_PROXY` reaches prod from a variable. Prod environment has no protection rule. | S |
| Testing | Worse | 0 of 149 test files set a Sharia flavour. `getAppFlavor()` is a top-level function that reads a const, so tests cannot inject it. Make the flavour a provider or pass `isSharia` down, then run the suite twice in CI. | M |
| CI/CD | Worse | See the next section: every recorded run failed. | S to repair, M to make reliable |

**Today vs target**

## CI/CD compared step by step

| **Step** | **GENFI** | **MyShaf** | **Gap** |
| --- | --- | --- | --- |
| Trigger | Tag `*-agent-tools-convent` (SIT), dispatch (UAT, prod) | SIT: push of tags matching the MyShaf pattern. UAT and prod: manual dispatch with `tag`, `version`, `is_adhoc` inputs (`myshaf-prod-deployment.yml:3-15`) | Same shape |
| Run history (API, 26 Oct 2026) | SIT 162 runs, 49 of the last 50 green | SIT 24 runs, 0 green (Jan to Jun 2026). UAT 0 runs. Prod 8 runs, 0 green, actor the same engineer each time | **The pipeline has never produced a MyShaf release.** |
| Where prod fails | n/a | Last three runs (18 and 19 Jun 2026): approval green, iOS build green, Android fails at "Upload to PlayStore" (`r0adkll/upload-google-play@v1`, line 151). One run also failed in "Build iOS App". | Find out how 1.3.1 reached Play. If by hand, the signed AAB left the pipeline through the 1-day artifact. |
| Where SIT fails | n/a | Last run (19 Jun): "Build Android SIT" and "Build iOS SIT" both fail | Fix or disable. A permanently red pipeline trains people to ignore CI. |
| Toolchain | Flutter 3.35.0, Java 17, SDK 36 | Same values, copied into these three files too (part of the 37 copies) | One pinned version, shared |
| Approval | `trstringer/manual-approval`, 2 of 8 | Same action, 2 of 9 named people, `GH_PAT`. Environment itself has 0 rules. | Protect the environment, then the step is a second gate not the only one |
| Signing | Base64 keystore and certificates from secrets | Same secret names, decoded in `run:` (lines 77-91, 176-222) | Same as GENFI plan 01 |
| Config | 21 dart-defines | 20 dart-defines in prod. SIT omits `SHA_256_FINGERPRINT` (unpinned). `DEVICE_INTEGRITY_URL` passed in all three. | Pass the fingerprint to SIT |
| Secrets in `run:` | Several | `${{secrets.*}}` interpolated straight into the build command, lines 104-126 and 235-257 | Pass through `env:` |
| Distribution | Play internal, TestFlight | Play internal track (`BRAVO_GCP_SA_KEY`, service-account JSON), TestFlight. Ad-hoc path builds a `profile` APK and IPA and uploads them as 1-day artifacts, no store. SIT: Firebase App Distribution group `sharia-myshaf` | Same as GENFI, plus the Play upload is the step that breaks |
| Post-build | Datadog symbols, Crashlytics symbols | Datadog symbols for `id.co.bfi.sharia.myshaf`. Then `upload-symbols` to Crashlytics for a flavour that has no Crashlytics. | Remove the dead step or wire Crashlytics |
| Pinned actions | By tag; `yaml-update-action@main` | Same, plus `actions/checkout@v1` and `@v2` in the SIT file | Pin by SHA |

**Pipeline state**

## Release drift

MyShaf's store binary was built in June from the code of June. GENFI's code kept moving in the same files.

| **Measure** | **Value** |
| --- | --- |
| Commits to `agent_tools` since `v1.3.1-beta.15-myshaf` | 135 |
| Commits to `shared_data`, `shared_lib`, `shared_features` since then | 52 |
| Of those, mentioning Sharia or MyShaf | 0 |
| Tags since 19 Jun 2026 | convent 75, aretracker 72, mybispro 1, myshaf 1 |
| Test files that set a Sharia flavour | 0 of 149 |

The risk is not that MyShaf is broken today. The store binary is frozen. The risk is the next release: four months of GENFI changes in shared screens (`feature/prospect`, `feature/common`, the router) reach Sharia users through a pipeline that has never been green, with no test and no cohort rollout for this flavour.

**Drift since June**

## Security items

Shared with GENFI and SQUARE (secret-printing workflows, keystore artifact, `BRAVO_GCP_SA_KEY` in 51 repos): see Genfi mobile app assessment and Agency phase 0: Close the leak. Specific to MyShaf:

1. `sharia_prod_myshaf` has no protection rule (verified). The manual-approval step is the only gate, and `agent_tools_prod_release_build.yaml` shows how a `_build` variant can bypass such a step.
2. SIT builds are unpinned (`SHA_256_FINGERPRINT` not passed). Testers never exercise pinning before UAT.
3. `FEATURE_ENABLE_PROXY` and `FEATURE_JAILBREAK_DETECTION` enter prod from GitHub variables. A changed variable changes the security posture of a prod build without a code review.
4. Secrets interpolated into `run:` commands in all three MyShaf workflows.
5. The device-integrity check defaults to on but is a Remote Config flag (`FEATURE_INTEGRITY_CHECK`). Anyone with Remote Config access can turn it off for every user. Decide whether that is intended.
6. The signed prod AAB and IPA are uploaded as workflow artifacts for 1 day. That is how a release can be published by hand when the upload step fails, and it is also an exfiltration path.

## Options

Three options for what MyShaf becomes. Pick one before planning engineering work.

| **Option** | **What it means** | **Strengths** | **Weaknesses** |
| --- | --- | --- | --- |
| A. Retire MyShaf, move Sharia agents into GENFI | Sharia products become a product line inside GENFI (the shared packages already model them as data). Store listing closed after a migration window. | Removes a flavour nobody tests, a second store presence, three pipelines and 37 branches. The GENFI roadmap then has one app to keep green. | Needs a product and Sharia-business decision, user migration, and a check of any regulatory reason for a separate Sharia app. |
| B. Keep the flavour, make it a first-class release train | MyShaf ships on every GENFI release train. CI repaired, Sharia flavour in the parity net, cohort rollout per flavour, Crashlytics and analytics decided. | No user migration. The code stays one. | Every GENFI step on the roadmap gets a MyShaf row. Doubles the test matrix for 12 sessions a month. |
| C. Freeze it | No new releases. Store listing stays. Fix only security items that affect the frozen binary (none found in the binary itself). | Cheapest now. | The binary ages against backend and OS changes. A forced release later carries all the drift at once. |

**Recommended: A**, subject to the product check in open question 2. If the answer is that Sharia agents must have a separate app, then B, and the first step is to repair CI and add the flavour to the parity net before any other change reaches MyShaf.

Until the decision: do not release MyShaf from the current master. If a release is unavoidable, build from `v1.3.1-beta.15-myshaf` plus cherry-picked fixes.

**Options**

## Plans and roadmap

MyShaf has no plan pages of its own. The GENFI plan pages carry MyShaf where the code is shared, and the shared phase pages under Agency apps roadmap: shared phases carry the monorepo work (secrets, CI, seams, network chain, Riverpod 3, packages, platform). The steps below are the MyShaf-only work, in the same format as GENFI roadmap: step by step, so they can be added to the relevant epic as tickets.

Impact classes: **A** no app change, **B** same behaviour, **C** behind a switch flag, **D** approved delta.

| **#** | **Step** | **Class** | **Phase** | **Depends on** | **Jira ticket** | **PR** |
| --- | --- | --- | --- | --- | --- | --- |
| M.1 | Decide option A, B or C (product, Sharia business, Agency tech lead). Record it on this page. | – | 0 | – | | |
| M.2 | Protect `sharia_prod_myshaf` and `sharia_prod_mybispro`: limit to release refs, required reviewers where the plan allows. Part of Agency phase 0 step on prod environments. | A | 0 | – | | |
| M.3 | Fix or disable the MyShaf SIT pipeline. If option C, disable all three workflows and say so in the file. | A | 0 | M.1 | | |
| M.4 | Pass `SHA_256_FINGERPRINT` to the SIT build. Move `FEATURE_ENABLE_PROXY` and `FEATURE_JAILBREAK_DETECTION` out of prod variables into code defaults per flavour. | A (CI) / D (prod build) | 1 | M.3 | | |
| M.5 | Make the flavour injectable: `getAppFlavor()` behind a provider or an `isSharia` parameter, then run the test suite with the Sharia flavour in `pr-check-test-coverage.yml`. | B | 1 | Agency phase 1 (checks on every PR) | | |
| M.6 | Decide crash reporting and analytics for MyShaf: wire Crashlytics for the Sharia flavours or delete the dead Crashlytics symbol step and the analytics wiring. | B | 2 | M.1 (only if B) | | |
| M.7 | Merge `ShariaRemoteConfig` into the one flag catalogue (GENFI plan 10). | B | 2 | GENFI plan 10 step 1 | | |
| M.8 | First release after the decision: from a parity-net-green master, Play staged rollout 20% → 100%, with a MyShaf row on the cohort dashboard. | C | 3 | M.3, M.5 | | |
| M.9 | If option A: migration plan for Sharia agents into GENFI, store listing sunset, remove the three `*_sharia` flavours, 37 branches and 3 workflows. | D | 9 | M.1 = A | | |

## Open questions

| **#** | **Question** | **Who answers** |
| --- | --- | --- |
| Q1 | How many active Sharia agents use MyShaf? RUM says 12 sessions a month. Is there a backend number (logins to the Sharia agent API)? | Sharia business, Agency squad |
| Q2 | Is there a regulatory or brand reason for a separate Sharia app, or can Sharia products live inside GENFI? | Sharia business, Legal |
| Q3 | How was 1.3.1 published to Play when every prod run failed at the upload step? Who holds the Play upload rights for `id.co.bfi.sharia.myshaf`? | Agency tech lead |
| Q4 | What is `DATADOG_SAMPLING_RATE` for `sharia_prod_myshaf`? | Whoever owns the environment variables |
| Q5 | Is the device-integrity check meant to be switchable from Remote Config? | Security |
| Q6 | Who owns MyShaf today? The README says "Agency, Sharia". The last release was run by one engineer. | Engineering manager |

Facts checked on 26 Oct 2026 against `bravo-agency-app` `master` @ `1e50b819`, the GitHub REST API and Datadog RUM (us5). Sources: `agent_tools/lib/main.dart`, `agent_tools/lib/app/utils/flavor_utils.dart`, `agent_tools/lib/app/navigation/router.dart`, `agent_tools/android/app/build.gradle`, the three `myshaf-*` workflows, `README.md`.
