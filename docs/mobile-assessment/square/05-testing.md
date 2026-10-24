Priority 5 of 13. Phase 1. Controller tests exist and are allowed, and the trunk pipeline runs them with coverage, but nothing fails a PR when coverage drops, and no journey is tested end to end.

## Goal

A coverage gate on changed files blocks PRs. Domain and notifier logic is unit-tested without a widget binding. The main SQUARE journeys run end to end on real devices before each release. The parity net is in place before the architecture refactors (SQUARE plan 08: Layering) start.

## Where we are today

Revision read: `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026). Counts from `are_tracker/test` and the shared packages in its melos category (`shared_data/agency`, `agent_marketing`, `keycloak`, `master`, `onboarding`, `user_iam`, `sso`, `shared_features/collab_form`, `onboarding_collab_form`, `shared_lib/core`, `crash_reporting`, `places`).

* **135 test files** in `are_tracker/test`: 854 `testWidgets` and 394 `test` calls. 71 screen tests, 7 controller tests, 0 use-case tests. `mocktail` in 94 files, `mockito` in 0. `test/src/auth/widget_test.dart` is a 14-line placeholder.
* **Shared packages:** `agent_marketing` 28 test files, `agency` 19, `onboarding` 7, `core` 4 (none covers `HttpClient` request building or error mapping), `collab_form` 4 (one is an empty placeholder), `crash_reporting` 1, `keycloak` 1, `master` 1, `user_iam` 1, `places` 1, `sso` 0, `onboarding_collab_form` 0, `integrity` 0, `http_certificate_pinning` 0. `ui_theme` 13, `ui_catalog` 1.
* **No golden tests** (0 `matchesGoldenFile`), no `integration_test` folder in any app, and no end-to-end suite for SQUARE. The org's `automation-monorepo` has a mobile suite only for the BFI customer app (`bfi-mobile`); nothing for `are_tracker`.
* **CI:** `pr-check-test-coverage.yml` runs on PRs that touch `are_tracker/**/*.dart` or any shared package, through `workflow-test-coverage-check.yml`: `melos bootstrap:are_tracker`, then `melos test:are_tracker`, which runs `include_unreached_coverage.dart` (a dummy test that imports every lib file so untested files count as 0%), `flutter test --coverage --no-pub --reporter failures-only --fail-fast` per category package, then `combine_coverage.dart`. The report step (`kefasjw/lcov-pull-request-report`) has `continue-on-error: true` and sets no minimum. The trunk pipeline (`are-tracker-trunk-pipeline.yml`) runs the same on `master` with `continue-on-error: false`, but still with no threshold. **There is no threshold anywhere.**
* Coverage is for the whole package and its category packages, not for changed files. No test randomisation. `--fail-fast` hides every failure after the first. `--reporter failures-only` hides passing counts.
* Nothing bans controller tests (unlike `bravo-customer-app`), which is good. 7 controller tests exist against 82 controllers, so most controller logic is tested only through 71 whole-screen tests.
* SQUARE is 377 hand-written Dart files and 75,106 lines in `are_tracker/lib`, in 21 feature folders (`lead`, `company_submission`, `kpi_incentive`, `branch_activity`, `recruitment`, `report`, `maintain`, `master_data`, `account`, `auth`, `home` and others).

## Target (what Jago does, adapted for SQUARE)

| Jago pattern | Our adaptation |
| --- | --- |
| Coverage gate on changed files per module (`coverage-result.sh`) | A coverage-diff step in `workflow-test-coverage-check.yml`: lcov for the app and its category packages, filtered to files changed in the PR, fail below 70% (start value). Ratchet: never lower the number. Shared with GENFI (same workflow, same script). |
| Tests run in random order | `--test-randomize-ordering-seed=random` in `melos test:*`. Fix order-dependent tests as they appear. |
| About 5,288 test files; domain tested without Flutter | Pure-Dart tests for domain and notifiers as SQUARE plan 08: Layering adds them, starting with `lead` and `company_submission`. Screen tests stay. |
| Appium + Cucumber on BrowserStack | Reuse the org's `automation-monorepo` mobile suite (WebdriverIO + Appium). Journeys for SQUARE: SSO login, lead input, company submission, cancellation review, KPI and incentive view. Run on SIT builds nightly and on release candidates. |

**Parity net** (needed by every refactor plan): golden screenshots of the main screens, recorded API fixtures replayed through a fake `HttpClient`, widget tests that run with a switch flag off and on, and the analytics golden names file (SQUARE plan 04: Analytics wrapper). See the BFI Mobile App Assessment page, section "Keeping features identical", for the ledger template.

## Plan

### Step 1: coverage gate on changed files (1 PR, shared with GENFI)

* Add `scripts/coverage_diff.dart`: reads `combined_coverage/lcov.info`, filters to files in `git diff --name-only origin/master`, prints per-file and total coverage, exits 1 below the threshold in `scripts/coverage_threshold.txt` (70).
* Run it in `workflow-test-coverage-check.yml` after `combine_coverage.dart`, for every application in the matrix. Remove `continue-on-error` from the report step.
* Exclude generated files (`*.g.dart`, `*.freezed.dart`, `*.pb*.dart`), localizations and test helpers.
* How to check: a PR that adds an untested 50-line file to a SQUARE controller fails with the per-file table in the job log.

### Step 2: fix the harness (1 PR, shared with GENFI)

* Add `--test-randomize-ordering-seed=random` to every `melos test:*` script. Drop `--fail-fast` in CI so the full failure list shows. Keep `--reporter failures-only` only if the log stays readable.
* Delete the 14-line `are_tracker/test/src/auth/widget_test.dart` placeholder and the `collab_form` placeholder; replace them with real tests or nothing.
* Add `shared_lib/crash_reporting`, `ui_catalog` and `myshaf` to the CI matrix so their tests run.
* How to check: two consecutive CI runs use different seeds and both pass.

### Step 3: test the shared packages that have none (2–3 PRs, shared with GENFI)

* `core`: `HttpClient` request building, error mapping (`HttpStatusCodeException` with `correlationId`, timeouts), response types (the `stream` and `plain` mapping bug from SQUARE plan 06: Networking).
* `sso` and `keycloak`: token refresh, expiry, the double-refresh race (expect it to fail, then fix in SQUARE plan 06: Networking). SQUARE signs in through Keycloak, so these two packages matter more for SQUARE than for GENFI.
* `integrity`: nonce and verify calls with a mocked `HttpClient`. `http_certificate_pinning`: interceptor behaviour with a fake channel.
* How to check: no package in the `are_tracker` category list has 0 test files.

### Step 4: controller tests for the biggest controllers (1–2 PRs)

* 7 controller tests exist against 82 controllers. Add direct tests for the `lead` and `company_submission` controllers first, since SQUARE plan 08 refactors those features first. Write the tests against today's behaviour, so they become the old-path tests in the parity ledger.
* Use `ProviderContainer` with the repository providers overridden by fakes, no widget pumping.
* How to check: every controller in `lead` and `company_submission` has a test file, and the tests pass on `master` before any refactor starts.

### Step 5: parity net before the refactors (2 PRs)

* Golden screenshot tests for the top screens of `lead` and `company_submission`, plus `home`. Use Alchemist CI-mode goldens (fixed test font, Linux CI only), so pictures match across machines.
* Recorded SIT fixtures for their API calls under `test/fixtures/`, scrubbed of personal data (names, NIK, phone numbers). A `FakeHttpClient` that replays fixtures. A `FakeAnalytics` and `FakeLogger` from SQUARE plans 04 and 03.
* The parity ledger template at `docs/parity/README.md` (shared with GENFI), and the first ledger, `docs/parity/square-lead.md`.
* How to check: the ledger for `lead` has an old-path test for every row.

### Step 6: end-to-end journeys (3–4 sprints, with QA)

* Add a `square` package next to `bfi-mobile` in `automation-monorepo/packages/mobile-automation`. SIT builds from `are-tracker-deploy-tag-cd-pipeline.yml` are uploaded to the device cloud. Specs: SSO login, lead input, company submission, cancellation review, KPI and incentive view.
* Add stable `Semantics` identifiers to the screens the specs touch, so refactors do not break selectors. Today the suite for BFI selects mostly by visible text; do not repeat that.
* Nightly on SIT; required on release candidates.
* How to check: a release candidate build has a green e2e run attached to its tag.

### Step 7: grow domain and notifier tests with the refactors (ongoing)

* Every domain use case lands with unit tests (SQUARE plan 08: Layering). Every Notifier lands with a test that uses the fake repositories (SQUARE plan 09: State management).
* Raise the coverage threshold by 5 points per quarter while the gate stays green.
* How to check: the threshold file shows a higher number than at step 1 and CI is green.

### Parity check

* Steps 1–3 change no app code. Steps 4–5 add tests only. Nothing in this plan changes what agents see.
* The parity net built here is used by SQUARE plans 06, 08 and 09: every old-path test written in step 4 must pass unchanged on the new path, or the difference is an approved delta in the ledger.

## Done when

* PRs fail when coverage on changed files drops below the threshold; the threshold only goes up.
* Tests run in random order and the whole failure list is visible.
* No shared package in the `are_tracker` category has 0 tests; `HttpClient`, `sso` and `keycloak` are tested.
* Every `lead` and `company_submission` controller has a direct test.
* The parity net (goldens, fixtures, fakes, ledger) exists for `lead`.
* The e2e journeys run nightly on SIT and gate release candidates.

## Effort and owner

* Steps 1–2: S, days. Owner: Agency squad (one change for GENFI and SQUARE).
* Step 3: S, 1 sprint. Owner: whoever owns `shared_data` (Agency squad with Sharia).
* Step 4: S, 1 sprint. Owner: SQUARE engineers.
* Step 5: S–M, 1–2 sprints, before SQUARE plan 08 starts.
* Step 6: M, 3–4 sprints with QA automation. Owner: QA lead with the squad.

## Depends on / related plans

* SQUARE plan 02: CI/CD (the checks job runs the gate and random order; shared).
* SQUARE plan 06: Networking (characterisation tests first; the refresh race).
* SQUARE plan 08: Layering (domain tests; parity ledger per feature).
* SQUARE plan 09: State management (notifier tests).
* SQUARE plan 04: Analytics wrapper (golden names file).
* SQUARE plan 07: Lint and guardrails (ratchet on the threshold).
* GENFI plan 04: Testing (steps 1–3 are the same work; do it once).

## Risks

| Risk | Mitigation |
| --- | --- |
| A 70% gate blocks urgent fixes in untested legacy files | Gate on changed lines, not whole files, for the first quarter; allow a labelled override with a reviewer |
| Random order exposes many order-dependent tests at once | Introduce with a fixed seed first, fix in batches, then switch to random |
| E2E suite is flaky on real devices | Retry once; quarantine list reviewed weekly; never skip silently |
| Golden tests break on every `ui_theme` bump | Scope goldens to layout, not pixels, for shared components; regenerate in the theme PR |
| Keycloak SSO makes e2e login hard to automate | A SIT test realm with a long-lived test user; never a prod account |
