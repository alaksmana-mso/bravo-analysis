## Summary

Phase 1 of the agency apps roadmap ("Safety net first") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step; the app-specific rows (golden names, parity nets, e2e journeys, release dashboards) are on those roadmap pages. This page covers the 16 shared steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Safety Net First".
* **Plan pages:** GENFI plan 02: CI/CD steps 1, 2, 4, 5, 7; GENFI plan 04: Testing steps 1–3; GENFI plan 06: Lint and guardrails steps 1–2; GENFI plan 09: Repo layout steps 1–2; GENFI plan 05: Networking step 1; GENFI plan 03 step 5 (and the SQUARE twins).
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**Why Phase 1 matters.** Nothing here changes what agents or staff see. Every step adds a way to prove a later change kept the app the same, to release to a few users first, or to stop new debt. The BFI roadmap learned one lesson worth repeating: take every ratchet baseline **on the day the check merges**, not from the plan pages, because the numbers move every week.

### Four facts that shape Phase 1

**1. The toolchain is copied 37 times.** `subosito/flutter-action@v2` with `flutter-version: 3.35.0` appears in 37 places. Java is 17 adopt in most workflows, 17 temurin in one, 11 in three, absent in one. Android SDK setup uses two different actions with platforms 36, 35 and 33. Xcode is `latest-stable`, `16.4` or unset; runners are `macos-26`, `macos-15`, `macos-latest`. `melos-action@v2` in deploy workflows, `@v3` in the setup action. No `.fvmrc`, `mise.toml` or `.tool-versions`.

**2. The release pipeline has silent gaps.** The operator types the version; `fjogeleit/yaml-update-action@main` writes it; non-prod builds are always `+1`. `tag-release-pipeline.yml` picks the app by `contains("are")`, so a tag containing "share" would build ARE tracker. When `is_firebase_distribution` is true, nothing is distributed for Android (no step). The iOS dSYM upload reads a path the archive is not written to. `GEN_AI_WEBSOCKET_URL` and `DEVICE_INTEGRITY_URL` reach SIT, UAT and MyShaf but not GENFI prod.

**3. Tests run, but nothing gates.** Coverage is whole-package, posted with `continue-on-error: true`, no minimum. `--fail-fast` hides every failure after the first. No random order. `sso`, `integrity`, `http_certificate_pinning` and `onboarding_collab_form` have 0 tests; `core` has 4 and none covers the HTTP client. `ui_catalog`, `shared_lib/crash_reporting` and `myshaf` match no `paths-filter` key, so their tests never run on PRs.

**4. Three lint sets, no rules, dead weight.** Root `strict_lint.yaml` (1,176 lines, 154 rules on, 48 commented out), `very_good_analysis` in the shared packages, `flutter_lints` in `agent_tools`. `pubghost` allows dead code and dead intl. No dependency-rule tool: 129 (GENFI) and 89 (SQUARE) cross-feature imports, 3 repositories and a model in `shared_data/agency` import `flutter/material`, `collab_form` imports `core` without declaring it, `are_tracker` imports `dio` and `equatable` undeclared. Dead: `shared_data/document`, `shared_features/onboarding_collab_form`. `graphify-out/` (48,755 nodes) is committed build output. Generated code is 430,795 lines against 439,333 hand-written.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. All class **A**.

| # | Proposed ticket title | Today (24 Oct) | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | `chore: One toolchain in mise.toml (Flutter 3.35.0, Java 17, melos)` | 37 copies, mixed Java and SDKs | Agency engineer | M | – | | |
| 1.2 | `ci: Checks on every PR through map-changes-context; random test order` | Dart-only triggers; 3 packages never tested | Agency engineer | S | 1.1 | | |
| 1.3 | `ci: Build number from CI, version from the tag, explicit tag-to-app map` | Typed version, `contains("are")` | Agency engineer | S | Q2 | | |
| 1.4 | `ci: Fix dead paths and symbol uploads; fail without mapping.txt or dSYM` | No Android Firebase step; wrong dSYM path | Agency engineer | S | – | | |
| 1.5 | `chore: Tidy the repo side (graphify-out, disabled workflows)` | 5 disabled workflows, committed build output | Agency engineer | XS | 0.6 | | |
| 1.6 | `ci: Coverage gate on changed files (70%)` | No threshold | Agency engineer | S | – | | |
| 1.7 | `test: Fix the harness (random order, no fail-fast, placeholders, matrix)` | `--fail-fast`, 2 placeholder tests | Agency engineer | S | 1.2 | | |
| 1.8 | `test: Shared packages with no tests (core, sso, keycloak, integrity, pinning)` | 4 packages at 0 | Agency engineer | M | – | | |
| 1.9 | `chore: One lint set` | 3 lint sets | Agency engineer | S | – | | |
| 1.10 | `ci: Architecture ratchet (feature-boundary, flutter-in-shared_data, undeclared deps)` | No checker; 129 / 89 imports | Agency engineer | M | – | | |
| 1.11 | `chore: Delete the dead packages, declare the undeclared imports` | 2 dead packages | Agency engineer | XS | 1.10 | | |
| 1.12 | `test: Characterise the six auth decorators` | 0 tests on refresh behaviour | Agency engineer | S | – | | |
| 1.13 | `chore: CODEOWNERS for .github, tool, analysis_options, .claude` | No `CODEOWNERS` | Squad lead | XS | – | | |
| 1.14 | Release health dashboard per app and stop thresholds (GENFI, SQUARE, MY BISPRO RUM apps) | Per-release dashboards unknown; SQUARE RUM not processed | Agency engineer + SRE | S | Q4 | | |
| 1.15 | Staged rollout on Play and phased release on iOS, by hand with a checklist, for every app | Not used | Release manager | XS (process) | – | | |
| 1.16 | One Datadog monitor per app on error rate and crash-free sessions; name the Datadog owner | None | Squad lead + SRE | S | 1.14 | | |

**Suggested order.** Week 1: 1.10 and 1.11 (stop the growth), 1.9, 1.13, 1.1. Week 2: 1.2, 1.7, 1.6, 1.12. Weeks 3–4: 1.3, 1.4, 1.5, 1.8, 1.14, 1.15, 1.16. App-specific rows (on the roadmap pages) run in parallel.

## Definition of ready for every Phase 1 ticket

* The ticket links to this page and to the epic, and names the app or package it touches.
* For any change to the build (1.1, 1.3, 1.4): the ticket says how we prove the APK and IPA did not change (size, `flutter --version` in the log, SIT smoke).
* For any new CI check: non-blocking for 1 week, then required, with the date in the ticket.
* Ratchet baselines are taken from `master` on merge day and committed with the check.

## Step 1.1: One toolchain

**Today.** See fact 1. A `chore/flutter-3.47.2-upgrade` branch exists.

**Tasks.** `mise.toml` at the root with `flutter = "3.35.0"` (the version CI uses today, so the binaries do not change), `java = "temurin-17"`, `melos`. Replace every `subosito/flutter-action`, `setup-java` and `setup-android` block with `jdx/mise-action` plus one `setup-android` version. Pin Xcode and the macOS runner label once. Point the README at `mise.toml`. Delete the stale upgrade branches once the upgrade PR exists.

**Acceptance criteria.** `grep flutter-version .github` returns 0. Every build log prints 3.35.0 and Java 17. SIT APK size within ±1%. A local `mise install` matches CI.

**Who / size.** One Agency engineer. M (31 workflow files).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `mise.toml` + `jdx/mise-action` | One file for Flutter, Java and melos; BFI repos already use mise | Developers who use FVM must switch or keep `.fvmrc` in step |
| B. `.fvmrc` + `subosito/flutter-action` `flutter-version-file` | Flutter-native | Java and melos still need their own setup blocks |
| C. Pin in `pubspec.yaml` `environment: flutter: 3.35.0` | No new file | Does not cover Java, SDK or melos |

**Recommended: A**, because Java and SDK drift are half of the problem here.

## Step 1.2: Checks on every PR

**Today.** `pr-check-*` trigger on `*.dart` under listed folders only. `workflow-map-changes-context.yml` builds the app matrix. `ui_catalog`, `shared_lib/crash_reporting` and `myshaf` have no key.

**Tasks.** Remove the `*.dart` path filters; let `map-changes-context` decide the app matrices; always run `workflow-lint` (Phase 0), a `pubspec` check and a Gradle and iOS config lint. Add the three missing keys. (Random order is step 1.7.)

**Acceptance criteria.** A PR that changes only `pubspec.lock` runs the checks. A Dart change in `ui_catalog` runs its tests.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Context map decides the matrix; a small always-on job for everything else | Fast for Dart-only PRs, nothing skipped | Two trigger paths to keep in step |
| B. Run every app's full matrix on every PR | Simple | Three apps' tests on a README change |
| C. Keep Dart-only triggers, add a separate workflow for non-Dart files | Minimal diff | Two workflows that must agree on what "everything" means |

**Recommended: A.**

## Step 1.3: Build number and version from CI

**Today.** See fact 2.

**Tasks.** Build number = `github.run_number` + an offset above today's highest number per app (question 2). Version from the tag (`v1.17.0-rc.1-agent-tools-convent` → `1.17.0`). Remove the free-text version input. A suffix table (`-genfi`, `-myshaf`, `-square`, `-mybispro`) replaces `contains()`.

**Acceptance criteria.** Two consecutive prod builds of one app have increasing build numbers with nobody typing them. A tag named `v1.0.0-share-test` builds nothing.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `run_number` + offset per app, suffix table | Simple, no state | Offsets must be set once per app from the stores |
| B. A repository variable per app bumped by the build | One counter per app | Needs a write token; parallel builds can race |
| C. Keep typed versions, only fix the tag matcher | Smallest | Human-typed numbers can go backwards |

**Recommended: A.**

## Step 1.4: Dead paths and symbol uploads

**Today.** No Android Firebase App Distribution step when the flag says so; iOS dSYM path does not match the archive path; two URLs missing from GENFI prod; nothing fails when `mapping.txt` or the dSYM folder is missing; the Datadog symbol upload has no `--version`.

**Tasks.** Add the Android Firebase step. Fix the dSYM path. Pass the two URLs to GENFI prod. Add `--version` to the Datadog upload. Fail the prod build when `mapping.txt` or the dSYM folder is missing.

**Acceptance criteria.** A prod build shows readable stack traces in Crashlytics and Datadog for the same version, on both platforms. A build with `-Pshrink=false` fails on the missing mapping file.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Fix all five in one PR | Readable crashes on the next release | One PR across two prod workflows |
| B. Fix only the fail-if-missing checks | Smaller | The dSYM path stays wrong, so iOS crashes stay unreadable |
| C. Wait for the reusable workflows (Phase 2) | One rewrite | Months of unreadable iOS crashes |

**Recommended: A.**

## Step 1.5: Tidy the repo side

**Today.** 5 disabled workflows; `graphify-out/` committed and refreshed weekly by a workflow with `contents: write`; the `*_ro_tools` environments (Phase 0 step 0.6).

**Tasks.** Decide where `graphify-out/` lives (artifact or Pages site, not source). Delete the 5 disabled workflows.

**Acceptance criteria.** `git ls-files .github/workflows` lists only live workflows. No weekly bot commit of build output.

**Who / size.** One Agency engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Graphify output as a build artifact, delete disabled workflows | Clean history, smaller clone | The Graphify bundle must be fetched, not read from the tree |
| B. Keep committing, delete only the workflows | Smaller change | A weekly write-token commit of 48,755 nodes stays |
| C. Leave everything | None | Dead workflows confuse the next reader |

**Recommended: A.**

## Step 1.6: Coverage gate on changed files

**Today.** `melos test:<app>` runs `include_unreached_coverage.dart`, `flutter test --coverage --fail-fast`, `combine_coverage.dart`; the report has `continue-on-error: true` and no minimum.

**Tasks.** `scripts/coverage_diff.dart`: reads `combined_coverage/lcov.info`, filters to files in `git diff --name-only origin/master`, prints per-file and total coverage, exits 1 below `scripts/coverage_threshold.txt` (70). Run it in `workflow-test-coverage-check.yml` after `combine_coverage.dart`; remove `continue-on-error`. Exclude generated files, localisations and test helpers.

**Acceptance criteria.** A PR that adds an untested 50-line file to a controller fails with the per-file table in the log. A PR that changes only generated files passes.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own `coverage_diff.dart` over lcov | Works for all three apps and the shared packages in one script | We maintain it |
| B. Codacy "Diff Coverage" as on the BFI app | Uses what BFI pays for | Codacy must see each app's lcov; the matrix posts one combined file per app today |
| C. Whole-package threshold | Simplest | Blocks every PR until legacy files are covered |

**Recommended: A**, and B later if Codacy coverage per app is easy to wire.

## Step 1.7: Fix the harness

**Today.** `--fail-fast` and `--reporter failures-only`; no random order; two placeholder tests; three packages outside the CI matrix.

**Tasks.** `--test-randomize-ordering-seed=random`; drop `--fail-fast` in CI; delete the placeholders or replace them with real tests; add `shared_lib/crash_reporting`, `ui_catalog` and `myshaf` to the matrix.

**Acceptance criteria.** Two consecutive CI runs use different seeds and both pass; the failure list shows every failure.

**Who / size.** One Agency engineer. S to M if many order-dependent tests appear.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Random order non-blocking for a week, then required | Finds coupling without blocking PRs | A week with two test runs |
| B. Random order required at once | Fast | Can block every PR until flaky tests are fixed |
| C. Fixed seed forever | Deterministic | Hides order coupling |

**Recommended: A.**

## Step 1.8: Shared packages with no tests

**Today.** `sso` 0, `integrity` 0, `http_certificate_pinning` 0, `onboarding_collab_form` 0 (dead, delete in 1.11), `keycloak` 1, `core` 4 (none for `HttpClient`).

**Tasks.** `core`: request building, error mapping (`HttpStatusCodeException` with `correlationId`, timeouts), the response-type bug (`stream` and `plain` both map to `json`). `sso` and `keycloak`: token refresh, expiry, the double-refresh race (expected to fail; fixed in Phase 4). `integrity`: nonce and verify with a mocked client. Pinning: interceptor behaviour with a fake channel.

**Acceptance criteria.** No package in any app's melos category has 0 test files. The double-refresh test exists and is marked as a known failure.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Characterisation tests against today's behaviour | Gives Phase 4 its oracle | Tests encode bugs on purpose; mark them |
| B. Tests written to the target behaviour | Cleaner | They fail until Phase 4; nothing protects the old path |
| C. Skip, rely on app-level tests | No work | The refresh race stays invisible |

**Recommended: A.**

## Step 1.9: One lint set

**Today.** See fact 4.

**Tasks.** One `analysis_options.yaml` at the root that every package includes; pick `very_good_analysis` (already the shared-package choice) and port the few `strict_lint` rules the team wants. Stop ignoring `depend_on_referenced_packages` and `use_build_context_synchronously`. Add `http_certificate_pinning` to analysis.

**Acceptance criteria.** `melos analyze` passes with one set. Rule count and the ignored-rule list are in the ticket.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `very_good_analysis` everywhere, a short root override | The shared packages already use it; maintained | `agent_tools` gains warnings to fix |
| B. Keep `strict_lint.yaml` as the one set | No dependency | 1,176 hand-copied lines to maintain |
| C. Leave three sets | None | Rules differ by folder |

**Recommended: A.**

## Step 1.10: Architecture ratchet

**Today.** No checker. 129 (GENFI) and 89 (SQUARE) cross-feature imports; `shared_data/agency` imports `flutter/material`; undeclared imports.

**Tasks.** `tool/arch_check.dart` with a baseline file: `feature-boundary` (features import only `lib/app`, shared packages and `*_api`), `flutter-in-shared_data`, `undeclared-import`. Baseline on merge day. Run in CI. Later rules (`domain-purity`, `dto-in-presentation`, `state-notifier`) are added by the Layering and State plans.

**Acceptance criteria.** Passes on `master`; a branch with a new `calculator → prospect` import fails.

**Who / size.** One Agency engineer. M. Copy the BFI checker if it exists by then (BFI Phase 1 step 1.19).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own Dart script with a baseline, shared with the BFI app | Ratchet semantics; one tool across BFI repos | We maintain it |
| B. `import_rules` analyzer plugin | IDE feedback | No baseline: 218 failures on day one |
| C. `custom_lint` rule (plan 06 step 4) | IDE feedback | Analyzer version pinning pain; keep for later |

**Recommended: A now, C later.**

## Step 1.11: Delete the dead weight, declare the undeclared

**Today.** `shared_data/document` (duplicates `agency/src/document`), `shared_features/onboarding_collab_form` (no app imports it); `collab_form` → `core` undeclared; `are_tracker` → `dio`, `equatable` undeclared.

**Tasks.** Delete the two packages. Declare the imports. Run `pubghost` without the allow flags.

**Acceptance criteria.** `pubghost` and `arch_check` report nothing. All three apps build.

**Who / size.** One Agency engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete and declare now | Smaller workspace | None |
| B. Mark deprecated, delete next quarter | Softer | Dead code stays in every bootstrap |
| C. Leave | None | Confuses the Layering work |

**Recommended: A.**

## Step 1.12: Characterise the six auth decorators

**Today.** Six near-identical auth clients (1,508 lines) on top of one `HttpClient`: only one retries after a refresh, two can refresh twice at once, one refreshes before every request. No tests.

**Tasks.** Tests with a fake Dio for each decorator: header names and schemes, when refresh happens, what happens on 401, what happens when two requests hit an expired token at once. Expect the double-refresh test to fail for the Keycloak clients. Test only, no production code.

**Acceptance criteria.** Every decorator has a behaviour test; the plan's comparison table is reproduced by tests.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Fake Dio, deterministic `Completer`s | Fast, exact | Timing needs care |
| B. Local mock server | Closer to real | Slower |
| C. No tests | No work | Phase 4 has no oracle |

**Recommended: A.**

## Step 1.13: `CODEOWNERS`

**Today.** None.

**Tasks.** Owners for `.github/`, `tool/`, `scripts/`, `analysis_options.yaml`, `.claude/`: a team, not one person. "Require review from Code Owners" in the ruleset.

**Acceptance criteria.** A PR touching `.github/` asks the team and cannot merge without it.

**Who / size.** Squad lead + repo admin. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Guardrail files only, enforced | Small, clear | Feature code unowned for now |
| B. Owners per app folder too | Right reviewers everywhere | Needs the squad mapping |
| C. Advisory only | No blocking | Not enforced |

**Recommended: A**, B when features become packages.

## Step 1.14: Release health dashboards and stop thresholds

**Today.** Datadog RUM apps: "Agent Tools GENFI App" (processed), "SQUARE (ARE Tracker)" (not processed), "MyShaf" (processed). No agreed thresholds.

**Tasks.** One dashboard per app comparing the new version with the previous: crash-free sessions, error rate, p75 screen load, ANR. Agree stop thresholds with product and SRE. Decide RUM processing for SQUARE (cost).

**Acceptance criteria.** Each dashboard shows the last 2 versions side by side. Thresholds written on the dashboard. SQUARE RUM decision recorded.

**Who / size.** Agency engineer + SRE. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Datadog's built-in mobile deployment-tracking dashboard, cloned per app, plus monitors | Ready today | SQUARE needs RUM processing on, or Crashlytics-only for SQUARE |
| B. Crashlytics velocity alerts only | Already there | No load time or funnels |
| C. Both | Backup for SQUARE | Two places |

**Recommended: C**: A where RUM is processed, B as the floor for SQUARE until the cost decision.

## Step 1.15: Staged rollout and phased release

**Today.** Prod workflows upload to the stores; no staged rollout is known to be used.

**Tasks.** Play 5% → 20% → 50% → 100% and iOS phased release for GENFI; SQUARE and MY BISPRO are internal and can use 20% → 100%. A release checklist per app.

**Acceptance criteria.** One real release per app goes through the stages with the dashboard checked.

**Who / size.** Release manager. XS as a process.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. By hand with a checklist | Starts with the next release | Depends on people |
| B. A "Promote" workflow on the Play API | Repeatable | Needs the Play credential, which Phase 0 is still fixing |
| C. Automatic halt from a monitor | Fastest | Noisy monitors can halt good releases |

**Recommended: A now, B in Phase 2.**

## Step 1.16: Monitors and ownership

**Today.** None. No named Datadog owner for the agency apps.

**Tasks.** One monitor per app on error rate and crash-free sessions, routed to the squad channel. Name the owner.

**Acceptance criteria.** A forced crash in SIT triggers the monitor. The owner is on the dashboard.

**Who / size.** Squad lead + SRE. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Datadog monitors per app | Next to the dashboards | SQUARE needs RUM or logs processed |
| B. Crashlytics alerts only | Free | No error-rate signal |
| C. None | None | Rollouts cannot be watched |

**Recommended: A.**

## Exit gate for Phase 1

* One toolchain file; every build log shows the same versions.
* Coverage gate, random order, architecture ratchet and `workflow-lint` run on every PR and are required.
* No shared package at 0 tests. The decorator tests exist.
* Each app has a release health dashboard with thresholds and has shipped one release through a staged rollout.
* The app-specific rows on the GENFI and SQUARE roadmap pages are done (golden names, parity net, e2e).

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which version tool does the squad use locally (FVM, mise, none)? | Agency squad | |
| Q2 | Highest build number per app on Play and App Store Connect (for the offsets)? | Release manager | |
| Q3 | Is 70% on changed files the agreed start? | Squad lead + QA | |
| Q4 | Will RUM processing be turned on for SQUARE, and who pays? | Datadog owner + squad lead | |
| Q5 | Who owns the Datadog setup for the agency apps? | Engineering manager | |
| Q6 | Can the BFI app's `arch_check.dart` be shared as a package, or copied? | Both squads | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| 37 copies of the Flutter version | `grep -rhoE "flutter-version:..." .github` |
| Workflows | 31 files, 5,582 lines |
| Test counts per package | `git ls-files` per package, counting `_test.dart` files, at `1e50b819` |
| CI test commands | root `pubspec.yaml` `melos` scripts `test:*`; `workflow-test-coverage-check.yml` |
| Lint sets, imports, dead packages | plan 06 and plan 09 "today" sections |
| Generated vs hand-written | 430,795 vs 439,333 lines |
| RUM apps | Datadog RUM application list (SQUARE `rum_event_processing_state: NONE`) |

## Sources for the recommendations

* BFI Phase 1 refinement notes (same steps, sources and tools).
* [subosito/flutter-action](https://github.com/subosito/flutter-action), [jdx/mise-action](https://github.com/jdx/mise-action).
* Google Play, [Android vitals thresholds](https://developer.android.com/google/play/vitals); Apple, [phased release](https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases).
* [import_rules](https://pub.dev/packages/import_rules), [very_good_analysis](https://pub.dev/packages/very_good_analysis).
