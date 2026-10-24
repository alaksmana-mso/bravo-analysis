## Summary

This page prepares Phase 1 of the mobile roadmap ("Safety net first") for refinement. It covers all 25 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title, same style as Phase 0 (DM-3545): "[Tech x DK] Mobile App Improvement - Safety Net First".
* **Parent:** Mobile roadmap: step by step, section "Phase 1: Safety net first". Phase 0 notes: Mobile roadmap Phase 0: Close the leak – refinement notes.
* **Facts checked on 20 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `97749b2` (19 Oct), its GitHub settings, `automation-monorepo`, and Datadog. Counts use the same `grep` method as the plan pages, so they compare like with like.

**Why Phase 1 matters.** Nothing in this phase changes what customers see. Every step adds a way to *prove* that a later change kept the app the same, to release to a small share of users first, or to stop new debt. Phase 2 onwards depends on it.

### Four facts that shape Phase 1

**1. Debt is growing while we plan.** Same counting method, plan commit `190e1d20` (11 Sep) against `master` today (19 Oct):

| Measure | 11 Sep | 19 Oct | Change |
| --- | --- | --- | --- |
| Feature-to-feature imports | 264 | 334 | +70 |
| `StateNotifier` controllers | 72 | 88 | +16 |
| `navigatorContext` uses | 151 | 166 | +15 |
| `appRef.` uses | 120 | 131 | +11 |
| Test files | 193 | 240 | +47 |

So the ratchet steps (1.19, 1.20) must take their baseline **on the day the check goes live**, not from the plan pages. Every week of delay adds debt that the later phases must remove.

**2. Prod releases ship about every 2 weeks, not every week.** The release branch is cut every week (Monday 17:00 UTC). Successful prod builds: `release-2.25.x` on 15–17 Sep, `release-2.26.x` on 1 Oct, `release-2.27.x` on 13 Oct. So the exit gate "2 release trains" means about **4 weeks**.

**3. Uploads go only to the internal track today.** `build-prod.yml` and `build-prod-test.yml` upload to Play track `internal` and to TestFlight. Moving a build to production happens outside the workflows (Q1). That is where staged rollout (1.3) starts.

**4. Some of the net already exists.** Datadog has a RUM app "BFI Mobile Prod", per-release dashboards (2.5.0, 2.6.0, 2.7.0), and Datadog's built-in "RUM - Mobile App Deployment Tracking". `automation-monorepo` has 18 mobile specs, including a KYC spec. Copilot code review is switched on for PRs. Phase 1 should build on these, not start again.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks, including review. "Owner" is a role. Name a person at the session.

| # | Proposed ticket title | Today (20 Oct) | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1.1 | `chore: Pin one Flutter version for CI and local` | README 3.38.5, CI 3.41.9 | Mobile engineer | S | – | | |
| 1.2 | `ci: Build numbers that only go up` | Set from tag or input | Mobile engineer | S | Q2 | | |
| 1.3 | Staged rollout on Play and phased release on iOS | Internal track only | Release manager | XS (process) | Q1 | | |
| 1.4 | Release health dashboard and stop thresholds | Per-release dashboards, no thresholds | Mobile engineer + SRE | S | – | | |
| 1.5 | Delivery metrics, monthly | No DORA events in Datadog | Squad lead | S | – | | |
| 1.6 | `chore: Track project.pbxproj, delete the backup` | Both tracked, `.gitignore` disagrees | Mobile engineer | XS | – | | |
| 1.7 | `ci: Allow controller tests` + AGENTS.md rule | Ban in `pr-pipeline.yml` | Mobile engineer | XS | – | | |
| 1.8 | `docs: Test pyramid` (merge into 1.7) | No written pyramid | Squad lead | XS | 1.7 | | |
| 1.9 | `test: Random test order` | Fixed order, bundled runs | Mobile engineer | S–M | – | | |
| 1.10 | Coverage gate on changed files | Codacy upload can fail silently | Mobile engineer | S | Q4 | | |
| 1.11 | `test: Analytics golden names file` | None | Mobile engineer | S | – | | |
| 1.12 | `test: Golden screenshots of 5 key screens` | 0 golden tests | Mobile engineer | M | – | | |
| 1.13 | `test: Recorded SIT API fixtures + replay harness` | None | Mobile engineer + QA | M | – | | |
| 1.14 | Connect the e2e suite to release candidates | 18 specs, not triggered by app CI | QA + mobile engineer | L | Q7 | | |
| 1.15 | `test: Token refresh race tests` | 46 tests, no race tests | Mobile engineer | S | – | | |
| 1.16 | `docs: Parity ledger template` | None | QA + squad lead | XS | – | | |
| 1.17 | `chore: One lint set` | `lint` strict + unused `flutter_lints` | Mobile engineer | XS | – | | |
| 1.18 | `ci: Fail PRs with stale generated files` | Bot commits after merge | Mobile engineer | S | – | | |
| 1.19 | `ci: Architecture ratchet` | No checker, 334 feature imports | Mobile engineer | M | – | | |
| 1.20 | `ci: Ratchet legacy state` (same checker) | 88 / 166 / 131 | Mobile engineer | XS | 1.19 | | |
| 1.21 | `chore: CODEOWNERS for guardrail files` | `* @samuel-bfi` only | Squad lead | XS | Phase 0 Q8 | | |
| 1.22 | Review bot rules | Copilot review on, Codacy on | Mobile engineer | S | – | | |
| 1.23 | `docs: OWASP MASVS table` | None | Mobile engineer + security | S | – | | |
| 1.24 | RASP RFP and PoC | Not started | Engineering manager + security | L (calendar) | Budget | | |
| 1.25 | RUM-to-APM linking spike | KrakenD host added 5 Oct | Mobile engineer + SRE | S | – | | |

**Suggested order.** Week 1: 1.19 and 1.20 (stop the growth), 1.7 + 1.8, 1.17, 1.6, 1.1. Week 2: 1.3, 1.4, 1.11, 1.15, 1.18, 1.21. Weeks 3–4: 1.9, 1.10, 1.12, 1.13, 1.2, 1.22, 1.25. In parallel, run by others: 1.14 (QA), 1.24 (procurement), 1.5, 1.23, 1.16.

## Definition of ready for every Phase 1 ticket

* The ticket links to this page and to the Phase 1 epic.
* The owner is a named person.
* Acceptance criteria are copied from the step below.
* For any change that touches the build (1.1, 1.2, 1.6, 1.17): the ticket says how we prove the APK and IPA did not change (size, `flutter --version` in the log, a smoke run on SIT).
* For any new CI check: it starts as non-blocking for 1 week, then becomes required. The ticket names the date.

## 1a. Release tooling

### Step 1.1: One Flutter version in one file

**Today.** `README.md` says Flutter 3.38.5. `internals/install_flutter/action.yml` clones Flutter **3.41.9**. `build-prod-artifact.yml` sets `flutter-version: '3.41.9'` again with a different action. There is no `.fvmrc`, `mise.toml` or `.tool-versions`.

**Tasks.** Add one version file. Make the internal install action and `build-prod-artifact.yml` read it. Fix the README. Keep **3.41.9**, the version CI uses today, so the built app does not change.

**Acceptance criteria.** `grep` finds no Flutter version number in `.github/` or `README.md`. Every build log prints 3.41.9. The next SIT APK has the same size (±1%) as the one before.

**Who / size.** One mobile engineer. S.

**Risks.** A developer on another version gets a clear error instead of a silent difference. That is the goal. Tell the squad first.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `mise.toml` with `flutter = "3.41.9"` | One tool for Flutter, Java, Node. BFI already uses `mise` in other repos | CI needs a mise step. Not every Flutter developer uses mise |
| B. `.fvmrc` (FVM). CI reads it, for example with `subosito/flutter-action` `flutter-version-file: .fvmrc` | FVM is common in Flutter teams. The action's README supports `.fvmrc` and `pubspec.yaml` directly | One more tool on laptops |
| C. Exact pin in `pubspec.yaml` `environment: flutter: 3.41.9`, read by CI | No new file or tool. `pub get` itself refuses another version | An exact pin in `pubspec.yaml` is unusual. Upgrades touch every package's lock |

**Recommended: B.** It is the Flutter-native way, and CI can read it without a script. If the squad already uses mise daily, A is just as good. The point is one file, not the tool.

### Step 1.2: Build numbers that only go up

**Today.** The build workflows write the version into `digital/pubspec.yaml` with `fjogeleit/yaml-update-action`, from the tag or the free-text `version` input. A human can type a build number that is lower than the last one, or reuse one.

**Tasks.** Build number = a counter that only goes up. Remove the free-text `version` input. Read the version name from the tag.

**Acceptance criteria.** Two builds of the same tag get different, increasing build numbers. Play internal track and TestFlight accept both.

**Who / size.** One mobile engineer. S.

**Risks.** The first number must be above the highest number already on Play and App Store Connect for each app id (Q2). Play's upper limit for a version code is 2,100,000,000.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `github.run_number` of the build workflow + a fixed offset | Simple, no state to keep | Counters differ per workflow. Fine only if each flavor has its own app id |
| B. A repository variable that the build job bumps | One counter for all workflows | Needs a token that can write variables. Two parallel builds can race |
| C. Compute from the version (`major*10000 + minor*100 + patch`) | Readable | Breaks on release candidates and hotfixes with the same version |

**Recommended: A**, if each flavor has its own app id (confirm in Q2). Otherwise B.

### Step 1.3: Staged rollout on Play and phased release on iOS

**Today.** Workflows upload to Play `internal` and to TestFlight. The move to production is done by hand outside CI (Q1). We found no sign of staged rollout or phased release.

**Tasks.** For each prod release, roll out in stages: Play 5% → 20% → 50% → 100%. iOS: turn on "Phased Release for Automatic Updates". Check the release health dashboard (1.4) before each step up.

**Acceptance criteria.** One real release goes through all stages, with the dashboard checked and the result written in the release notes.

**Who / size.** Release manager, with someone who has Play Console and App Store Connect release rights. XS as a process change.

**Important limits.** On Play, halting a rollout stops new installs. Users who already updated keep that version, and we fix forward with a higher build number. On iOS, phased release goes 1%, 2%, 5%, 10%, 20%, 50%, 100% over 7 days for automatic updates, can be paused for up to 30 days in total, and anyone can still update by hand from the App Store.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Do it by hand in Play Console and App Store Connect, with a release checklist | No code. Starts with the next release | Depends on people following the checklist |
| B. A "Promote" workflow that calls the Play API with `userFraction` (the Play API supports start, increase, halt and resume) | Repeatable, logged | Needs the Play publisher credential in a workflow, which Phase 0 is still fixing |
| C. Option B plus an automatic halt when a Datadog monitor fires | Fastest reaction | Most moving parts. An automatic halt on a noisy signal can stop a good release |

**Recommended: A now, B in Phase 2** (with the reusable workflows, step 2.19, and after the Play credential is fixed in Phase 0).

### Step 1.4: Release health dashboard and stop thresholds

**Today.** Datadog RUM app "BFI Mobile Prod" exists. There are dashboards per old release (2.5.0, 2.6.0, 2.7.0), "Report Monthly Monitoring (Customer Mobile Apps Squad)", and the built-in "RUM - Mobile App Deployment Tracking". No dashboard holds agreed stop thresholds.

**Tasks.** One dashboard that compares the new version with the previous one: crash-free sessions, error rate, p75 screen load, ANR rate. Agree stop thresholds with product and SRE. Add monitors that alert the mobile on-call.

**Acceptance criteria.** The dashboard shows the last 2 versions side by side. Thresholds are written on the dashboard and on this page. A test monitor notifies the right channel.

**Who / size.** Mobile engineer + SRE. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Use Datadog's built-in "Mobile App Deployment Tracking" filtered to "BFI Mobile Prod" | Ready today | No thresholds, no BFI-specific funnels |
| B. A BFI dashboard built from A, plus monitors with thresholds. Use Google Play's own "bad behaviour" limits as the hard ceiling (user-perceived crash rate 1.09%, ANR rate 0.47%), and "worse than the previous version" as the stop rule | One place, agreed numbers, alerts | Thresholds need agreement. Data must be sampled enough per version |
| C. Firebase Crashlytics velocity alerts and release monitoring only | Already in the app | Separate from Datadog, no funnel or load time |

**Recommended: B, with Crashlytics velocity alerts switched on as a backup.** Above Play's limits, Play may show the app less in the store, so they are a real business ceiling.

### Step 1.5: Delivery metrics, monthly

**Today.** Datadog has no DORA deployment events (checked 90 days). Prod build runs since 1 Jul: 18 (9 success, 7 failure, 2 cancelled).

**Tasks.** Measure each month: release frequency, lead time from merge to prod, failed releases (hotfix needed), time to restore.

**Acceptance criteria.** The first monthly report exists, with the method written down.

**Who / size.** Squad lead. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. A small script over the GitHub API (workflow runs, tags, PR merge times) into a sheet | Cheap. No licence | We maintain the script |
| B. Datadog DORA Metrics: send a deployment event from `build-prod.yml` | Next to the other dashboards | May need a Datadog product we do not use yet. Check cost |
| C. Count by hand from the release notes | No work to set up | Not repeatable |

**Recommended: A.** Revisit B if the org adopts Datadog DORA for backend services.

### Step 1.6: Track `project.pbxproj`, delete the backup

**Today.** `digital/ios/Runner.xcodeproj/project.pbxproj` and `project.pbxproj.backup` are both tracked. `.gitignore` line 60 says `*.xcodeproj/project.pbxproj`, which does not match reality.

**Tasks.** Remove the `.gitignore` line. Delete the `.backup` file.

**Acceptance criteria.** iOS builds for all 4 flavors give the same IPA as before. `git status` is clean after opening the project in Xcode.

**Who / size.** One mobile engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Track `project.pbxproj`, fix `.gitignore`, delete the backup | Matches how Flutter projects work | None |
| B. Generate the Xcode project with XcodeGen or Tuist | No merge conflicts in `pbxproj` | Big change for little gain in one app |
| C. Only delete the backup | Smallest | The confusing `.gitignore` line stays |

**Recommended: A.**

## 1b. Test net

### Step 1.7: Allow controller tests

**Today.** `pr-pipeline.yml` step "Reject controller_test.dart files" fails any PR that adds `*_controller_test.dart`. `AGENTS.md` line 191 says "Test screens only (including the controller)". `CLAUDE.md` and `.github/copilot-instructions.md` are copies of `AGENTS.md` (194 lines each), kept in step by `sync-ai-rules.yml`.

**Tasks.** Remove the step. Change the rule in `AGENTS.md`: test controllers and use cases with unit tests (Riverpod `ProviderContainer`), keep a few screen tests for user flows.

**Acceptance criteria.** A PR with a new `*_controller_test.dart` passes. `CLAUDE.md` and `copilot-instructions.md` show the new rule after the sync.

**Who / size.** One mobile engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Remove the ban and change the rule | Unblocks fast logic tests | Old habit needs a short team note |
| B. Option A, plus a rule: controller tests use `ProviderContainer`, no widget pumping | Keeps tests fast and consistent | One more rule to review |
| C. Keep the ban, allow only use-case tests | Smallest change | Controllers hold most logic today, so they stay untested |

**Recommended: B.**

### Step 1.8: Write down the test pyramid

**Today.** No written pyramid. `AGENTS.md` has a short "Testing" section.

**Tasks.** A table in `AGENTS.md`: unit (domain, use cases, controllers), widget (screens, a few), golden (key screens), e2e (4 journeys). What goes where, and how fast each should be.

**Acceptance criteria.** Reviewed by the squad lead and QA. Synced to `CLAUDE.md` and `copilot-instructions.md`.

**Who / size.** Squad lead. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same PR as 1.7, table in `AGENTS.md` | One change, one review. AI tools read it too | `AGENTS.md` grows |
| B. A separate `docs/testing.md` linked from `AGENTS.md` and the PR template | Room for examples | Easier to forget |
| C. No document, rely on review | No work | Rules stay in people's heads |

**Recommended: A.** Merge 1.8 into the 1.7 ticket.

### Step 1.9: Random test order

**Today.** `melos test` uses `scripts/test_bundling.sh` (added in PR #1433, 22 Sep). It bundles each package's tests into one `flutter test` run to save time. Tests in one bundle share one process, so hidden shared state between test files is now more likely. No random order.

**Tasks.** Add `--test-randomize-ordering-seed random` to the bundled and unbundled runs. Print the seed in the log. Fix the tests that fail.

**Acceptance criteria.** 5 runs in a row pass with different seeds. A failing seed can be replayed locally.

**Who / size.** One mobile engineer. S to M, depending on how many tests fail.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Turn on random order in the PR pipeline at once | Finds coupling now | Can block every PR until the flaky tests are fixed |
| B. Run random order nightly first (non-blocking), fix what fails, then turn it on in PRs | No PR blocked while fixing | Two weeks before it protects PRs |
| C. Turn off bundling for a random-order job | Each file isolated | Loses the speed gain from #1433 |

**Recommended: B, then A.**

### Step 1.10: Coverage gate on changed files

**Today.** `melos test` writes `combined_coverage/lcov.info` without generated files. The Codacy upload has `continue-on-error: true`. The ruleset requires "Codacy Diff Coverage". Whether Codacy enforces a threshold is set in Codacy, not in the repo (Q4).

**Tasks.** One enforced gate: coverage on changed lines or files ≥ 70% to start, raised by 5 points a quarter up to 80%. Remove `continue-on-error` so a failed upload is visible.

**Acceptance criteria.** A PR that adds an untested use case fails. A PR that changes only generated files or tests is not blocked.

**Who / size.** One mobile engineer, plus whoever has Codacy admin. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Set the threshold in Codacy "Diff Coverage" (already required) and remove `continue-on-error` | Uses what we pay for. No new script | Depends on Codacy access and its rules |
| B. Own script over `lcov.info` and `git diff` in CI | Vendor-independent, visible in the repo | We maintain it |
| C. Both | Two views | Two gates that can disagree |

**Recommended: A.** Use B only if Codacy cannot express "changed lines ≥ N%".

### Step 1.11: Analytics golden names file

**Today.** 204 `logEvent(` calls in `digital/lib` (same method: 201 on 11 Sep). No file lists the event names.

**Tasks.** A script writes every Firebase event name, Mixpanel event name and `TrackerJourney` code to `docs/analytics/event-names.golden.txt`. CI fails if the list changes without the file changing.

**Acceptance criteria.** The file is committed. Renaming one event in a test PR fails CI.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `grep`-based extraction script | Cheap, fast | Misses names built at run time (plan 02 counts 8) |
| B. Extraction with the Dart analyzer | Resolves constants | More work |
| C. Record events at run time with a fake analytics in widget tests | Catches run-time names | Needs the port from Phase 2 |

**Recommended: A now**, with the 8 run-time names listed by hand. C comes with Phase 2.

### Step 1.12: Golden screenshots of 5 key screens

**Today.** 0 golden tests in the repo. `golden_toolkit`, the old common helper, is discontinued on pub.dev.

**Tasks.** Golden tests for home, loan detail, submission review, KYC, payment. Fake providers and fixed data, fixed clock, fixed fonts. Run only on the Linux CI image.

**Acceptance criteria.** Changing one colour or label on a key screen fails the test. Goldens pass 10 runs in a row on CI.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flutter's own `matchesGoldenFile` with our own font loading | No dependency | Font and platform differences make goldens flaky across machines |
| B. Alchemist (by Very Good Ventures). Its CI mode renders text in a fixed test font, so pictures match across platforms. Readable platform goldens stay local | Built for this problem. Maintained | One dev dependency |
| C. A hosted visual-testing service | Review UI, history | Cost. Screens leave our network |

**Recommended: B.**

### Step 1.13: Recorded SIT API fixtures and a replay harness

**Today.** No fixtures. The app already has a dev-mode `ApiCallHistoryInterceptor` (`digital/lib/features/dev_mode/api_call_history.dart`) that records requests, responses and `x-trace-id` in non-prod builds.

**Tasks.** Record SIT responses for register, KYC, loan submission and payment. Scrub personal data with a script that fails on NIK, phone, name, address or account-number patterns. A fake `HttpClient` replays them and records outgoing requests.

**Acceptance criteria.** The scrub check passes on every fixture. A replay test fails when a request field is renamed.

**Who / size.** Mobile engineer + QA (test accounts). M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Export from the existing dev-mode API history on a SIT build, then scrub | Reuses what exists. Real traffic | Manual export at first |
| B. Record through a proxy (for example mitmproxy) on SIT | Captures everything | Proxy setup, certificate pinning gets in the way |
| C. Contract tests with the backend teams | Catches backend changes too | Needs backend teams. Longer |

**Recommended: A.** Consider C later with the BFF team.

### Step 1.14: Connect the e2e suite to release candidates

**Today.** `automation-monorepo` `packages/mobile-automation/bfi-mobile` has 18 specs (WebdriverIO + Appium), last changed 15 Oct. It includes login, KYC, loan detail, loan list, simulation, 4 submission specs. No register spec. "Payment" is only the help page. The app sets `Semantics(identifier:)` in only 4 places, so most selectors use visible Indonesian text.

**Tasks.** Agree 4 journeys with QA: register, KYC, loan submission, payment. Add the missing specs. Add stable `Semantics` identifiers on the screens of those journeys. Trigger the suite from `build-sit-uat.yml` after the Firebase App Distribution upload. Link the result in release notes.

**Acceptance criteria.** Each release candidate has a linked e2e result. The 4 journeys pass on SIT.

**Who / size.** QA (owns the suite) + one mobile engineer. L (2–3 weeks), mostly QA.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Keep the Appium suite, fill the gaps, trigger it from app CI | QA already owns it. No tool change during Phase 1 | Appium sees Flutter through accessibility only, so selectors need `Semantics` identifiers |
| B. Patrol (Flutter-native e2e, lives in the app repo, reaches OS dialogs) | Uses Flutter finders. Developers can run it | New tool. Some teams report CI reliability problems |
| C. Maestro (YAML flows) | Quick to write | Another tool. Same accessibility limits as Appium |

**Recommended: A.** Do not change e2e tools in the phase that is meant to build the safety net. Revisit B in Phase 8.

### Step 1.15: Token refresh race tests

**Today.** `data/customer/test/http_client_test.dart` has 46 tests (41 when plan 07 was written). None fire parallel requests with an expired token.

**Tasks.** Tests only, no production code: 5 parallel requests with an expired token; 5 parallel requests that all get 401 `INVALID_KEY`. Count refresh calls with a fake.

**Acceptance criteria.** The proactive case shows 1 refresh. The 401 case is marked as a known failure and documents today's bug.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Unit tests with a fake refresh call and `Completer`s to control the order | Fast, exact | Needs care to make timing deterministic |
| B. A local mock HTTP server in the test | Closer to real | Slower, more setup |
| C. No tests, watch prod logout rates | No work | Proves nothing before Phase 4 |

**Recommended: A.**

### Step 1.16: Parity ledger template

**Today.** None.

**Tasks.** `docs/parity/_template.md` with one table: behaviour | old-path test | new-path test | e2e spec | analytics events | status | approved delta. A short guide on who signs off.

**Acceptance criteria.** Reviewed by QA and the squad lead.

**Who / size.** QA + squad lead. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Markdown in the repo | Changes with the code, reviewed in PRs | Less visible to product |
| B. A Confluence page template | Visible to product and audit | Drifts from the code |
| C. A Jira checklist per feature | Tracked with the work | Hard to read as a whole |

**Recommended: A**, with a link from the feature's Confluence page.

## 1c. Guardrails

### Step 1.17: One lint set

**Today.** `analysis_options.yaml` includes `package:lint/strict.yaml` (`lint: ^2.1.0` in the root). `flutter_lints: ^2.0.0` is still in `digital/pubspec.yaml` and `shared_lib/core/pubspec.yaml`, but nothing includes it.

**Tasks.** Remove `flutter_lints`. Measure how many errors `strict-casts`, `strict-inference` and `strict-raw-types` would add. Turn on only the ones with a small count.

**Acceptance criteria.** `melos run analyze` passes. The counts are written in the ticket.

**Who / size.** One mobile engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Keep `lint/strict`, remove `flutter_lints`, add strict modes if cheap | Smallest change | None |
| B. Switch to `very_good_analysis` | Popular, strict | Many new warnings at once |
| C. Leave as is | No work | Confusing for new joiners |

**Recommended: A.**

### Step 1.18: Fail PRs with stale generated files

**Today.** After merge, `on-merge-master.yml` runs `melos generate`, and if files changed, a bot commits "chore: update generated files [skip ci]" and pushes straight to `master` or the release branch. That push skips review.

**Tasks.** A PR step: run `melos generate` and `melos l10n`, then fail if `git status --porcelain` is not empty. Keep the bot for 1 month as a safety net, then remove it.

**Acceptance criteria.** A PR with a stale `.g.dart` fails. After 1 month the bot step is gone.

**Who / size.** One mobile engineer. S (generation adds minutes to the PR job).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. PR check, then remove the bot after 1 month | Catches it before merge. Ends unreviewed pushes | Slower PR job |
| B. Stop committing generated files. Generate in every build | No stale files ever | Slower builds and IDE setup. Big change |
| C. A local pre-commit hook plus the PR check | Fast feedback for developers | Hooks are optional on laptops |

**Recommended: A.** Add C as an optional helper.

### Step 1.19: Architecture ratchet

**Today.** No checker. 334 feature-to-feature imports today, 264 on 11 Sep.

**Tasks.** `tool/arch_check.dart`: count violations per rule and per file, compare with `tool/arch_baseline.json`, fail if any count goes up, ask to lower the baseline when it goes down. Rules: `feature-import`, `router-import`, `customer-repo-growth`. Run it in `pr-pipeline.yml` after analyze. **Take the baseline on the day it merges.**

**Acceptance criteria.** Passes on `master`. A branch that adds an `rl → ro` import fails.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Our own Dart script with a baseline file | Ratchet built in: old debt allowed, new debt blocked | We maintain it |
| B. `import_rules`, a native Dart analyzer plugin with YAML rules (needs Dart 3.10+) | Errors show in the IDE | No baseline, so every one of the 334 old imports would fail at once |
| C. `dart_boundaries` (custom_lint plugin) | Rich rules | Same baseline problem. custom_lint is the older plugin route and needs exact analyzer version pins |

**Recommended: A now.** Use B for new packages from Phase 8, where the debt starts at 0.

### Step 1.20: Ratchet legacy state

**Today.** `StateNotifier` 88, `navigatorContext` 166, `appRef.` 131. All grew since 11 Sep.

**Tasks.** Add rules `state-notifier`, `app-ref`, `navigator-context` to the 1.19 checker. Add the rule for new code to `AGENTS.md`.

**Acceptance criteria.** A branch that adds `appRef.read(` fails.

**Who / size.** One mobile engineer. XS (on top of 1.19).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same checker as 1.19 | One tool, one baseline | None |
| B. A lint rule in an analyzer plugin | IDE feedback | Same baseline problem as 1.19 B |
| C. Review only, written rule in `AGENTS.md` | No code | It grew by 15–16 in 5 weeks with review only |

**Recommended: A.**

### Step 1.21: `CODEOWNERS` for guardrail files

**Today.** `CODEOWNERS` has one line: `* @samuel-bfi`. The ruleset needs 2 approvals but not code-owner review.

**Tasks.** Owners for `.github/`, `scripts/`, `tool/`, `analysis_options.yaml`, `AGENTS.md`, `.claude/`: a team (for example mobile leads + SRE for `.github/`), not one person. Turn on "Require review from Code Owners" in the ruleset.

**Acceptance criteria.** A PR that touches `.github/` asks for the right team, and cannot merge without it.

**Who / size.** Squad lead + repo admin. XS. Same as Phase 0 question Q8. Do it once, in whichever phase is first.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Owners only for guardrail files | Small, clear | Feature code still has one owner |
| B. Option A plus owners per feature folder, from the squad mapping | Right reviewers everywhere | Needs an up-to-date team mapping |
| C. Option A plus "require code owner review" in the ruleset | Enforced, not advisory | A missing owner blocks merges |

**Recommended: A + C.** B later, when features become packages (Phase 8).

### Step 1.22: Review bot rules

**Today.** Copilot code review runs on PRs (GitHub's dynamic workflow). `.github/copilot-instructions.md` is synced from `AGENTS.md`. Codacy static analysis is a required check.

**Tasks.** Add the few mechanical checks a bot does better than people: warn on more than 600 changed lines outside generated files; warn when `lib/` changes but no test changes; ask for a reason when `pubspec.yaml` adds a dependency; label PRs that touch `.github/workflows/`.

**Acceptance criteria.** The bot comments as expected on 3 test PRs. No comment on a normal small PR.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Danger JS with those rules | Purpose-built, flexible | One more tool |
| B. A small `actions/github-script` workflow for the mechanical checks. Keep Copilot review for the rest, guided by `copilot-instructions.md` | No new tool. Uses what is on | Script lives in YAML |
| C. Only Copilot review with better instructions | No code | AI review is not reliable for exact counts |

**Recommended: B.**

## 1d. Security groundwork

### Step 1.23: OWASP MASVS table

**Today.** None.

**Tasks.** A table in the repo with the MASVS v2 control groups (STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE, PRIVACY). For each control: status, evidence, owner, next action. Review each quarter.

**Acceptance criteria.** Committed and reviewed by security.

**Who / size.** Mobile engineer + security. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Markdown table in the repo | Next to the code, reviewed in PRs | Security team may prefer their own tool |
| B. The OWASP MAS checklist spreadsheet | Standard format | Drifts from the code |
| C. Ask the next pentest vendor to fill it | Independent | Only as fresh as the last pentest |

**Recommended: A**, and give it to the next pentest as input.

### Step 1.24: RASP RFP and PoC

**Today.** Not started. Details and vendor list: Mobile plan 01: Security, step 7.

**Tasks.** Send the RFP to Promon, Guardsquare, Appdome and V-Key (add Everspin and DoveRunner if local support is a must). Ask for a 3-year cost at today's users and at 2×. Book PoC dates. No app change in Phase 1.

**Acceptance criteria.** Quotes and PoC dates received. The PoC scorecard is agreed.

**Who / size.** Engineering manager + security + procurement. L in calendar time, little engineering time.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. RFP and PoC with 4 vendors, one scorecard | Fair comparison | Takes weeks |
| B. Free baseline only (R8, root check, backend verdict checks) | No cost | Not a full RASP. Public checks can be bypassed |
| C. Ask DK which vendor terms they could share | Faster start | Ties us to DK's choice and timing |

**Recommended: A**, while the free baseline items continue in Phases 2 and 3.

### Step 1.25: RUM-to-APM linking spike

**Today.** `digital/lib/main.dart` sets `firstPartyHosts` to the API host and, since 5 Oct (DM-3337), the KrakenD host. With `firstPartyHosts`, the Datadog Flutter SDK sends Datadog-format tracing headers only. The SDK also supports W3C `tracecontext` and B3 through `firstPartyHostsWithTracingHeaders`. Errors read `x-trace-id` from responses.

**Tasks.** No code. Take 10 prod RUM sessions with a failed request. Check whether each RUM resource links to an APM trace, and whether `x-trace-id` matches that trace. Check both hosts. Write the answer on Mobile plan 05.

**Acceptance criteria.** A short written answer: linked or not, per host, with 2 example links.

**Who / size.** Mobile engineer + SRE. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. The spike as planned, no code | Answers the question with no app change | None |
| B. Add `tracecontext` next to the Datadog headers now | Works through gateways that drop `x-datadog-*` | An app change in Phase 1. The gateway must accept the headers |
| C. Rely only on `x-trace-id` from the server | No work | Does not link RUM to traces |

**Recommended: A.** If gaps are found, the fix is roadmap step 4.8, behind the network switch flag.

## Exit gate for Phase 1

* The parity net is green on `master` for 2 prod releases in a row (about 4 weeks at today's pace).
* One real release went out through Play staged rollout and iOS phased release, checked against the release health dashboard.
* The architecture ratchet (1.19 + 1.20) runs on every PR, and its baseline has not gone up.
* Every new check that was non-blocking for its first week is now required.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | How is a build moved from Play internal to production today, and who does it? | Release manager | |
| Q2 | Does each flavor have its own app id? What is the highest build number on Play and App Store Connect per app id? | Mobile squad | |
| Q3 | Who agrees the stop thresholds (crash-free, errors, load time, funnel)? | Product + SRE | |
| Q4 | Who has Codacy admin, and does "Diff Coverage" already have a threshold? | Squad lead | |
| Q5 | Which Flutter version tool does the squad use today: FVM, mise, or none? | Mobile squad | |
| Q6 | Is 70% on changed code the agreed start? | Squad lead + QA | |
| Q7 | Can QA own the 4 journeys and the trigger from `build-sit-uat.yml`? Which test accounts can we use on SIT? | QA lead | |
| Q8 | Who owns the RASP RFP and its budget? | Engineering manager | |
| Q9 | Who is the mobile on-call that the release monitors notify? | Squad lead | |
| Q10 | Epic for Phase 1: who creates it, and is one epic with 25 tickets right, or one epic with 4 sub-groups (1a–1d)? | Samuel | |

## Evidence

| Fact | How it was checked (20 Oct 2026) |
| --- | --- |
| Counts on 11 Sep vs 19 Oct | Same `grep` method on `190e1d20` and `97749b2`, generated files excluded |
| Flutter versions | `README.md`, `internals/install_flutter/action.yml`, `build-prod-artifact.yml` |
| Release pace | GitHub API runs of `build-prod.yml` since 1 Jul; `create-release-branch.yml` cron |
| Tracks | `track: internal` in `build-prod.yml` and `build-prod-test.yml` |
| Datadog | RUM application list ("BFI Mobile Prod"), dashboard search, DORA event search (none in 90 days) |
| e2e suite | `automation-monorepo` tree, `packages/mobile-automation/bfi-mobile/tests/**` (18 specs), last commit 15 Oct |
| Test bundling | `scripts/test_bundling.sh`, PR #1433 |
| Generated-files bot | `on-merge-master.yml` step "Verify generated files are up to date" |
| Tracing headers | `digital/lib/main.dart` `DatadogConfiguration` |

## Sources for the recommendations

* Google Play, [Android vitals](https://developer.android.com/google/play/vitals): bad-behaviour thresholds (1.09% user-perceived crash rate, 0.47% ANR rate).
* Google Play Developer API, [APKs and Tracks](https://developers.google.com/android-publisher/tracks): staged release with `userFraction`, increase, halt and resume.
* Apple, [Release a version update in phases](https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases): 7-day schedule, pause up to 30 days, manual updates still possible.
* [subosito/flutter-action](https://github.com/subosito/flutter-action): `flutter-version-file` accepts `pubspec.yaml` or `.fvmrc`.
* [Alchemist](https://pub.dev/packages/alchemist) and [golden_toolkit (discontinued)](https://pub.dev/packages/golden_toolkit): CI-mode goldens that avoid font differences on Linux.
* Patrol, Maestro, Appium comparison: [itsallwidgets forum thread](https://forum.itsallwidgets.com/t/e2e-testing-tools-patrol-vs-maestro-vs-appium-what-do-you-use/4034) and [devicelab.dev](https://devicelab.dev/blog/flutter-testing-maestro-patrol-appium). Opinion sources, read with care.
* [import_rules](https://pub.dev/packages/import_rules) and [dart_boundaries](https://pub.dev/packages/dart_boundaries): import-boundary lint options.
* OWASP, [MASVS](https://mas.owasp.org/MASVS/): 8 control groups, no verification levels since v2.0.
* Datadog, [Flutter advanced configuration](https://docs.datadoghq.com/real_user_monitoring/application_monitoring/flutter/advanced_configuration/): `firstPartyHostsWithTracingHeaders` and `TracingHeaderType` (`datadog`, `b3`, `b3multi`, `tracecontext`).
