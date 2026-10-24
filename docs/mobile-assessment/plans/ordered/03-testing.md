**Priority 3 of 13.** Phase 1. A coverage gate and controller tests protect every refactor that follows.

## Goal

Business logic is tested on its own, fast. Screens are tested for what the user sees. Every PR must keep coverage on the files it changes above an agreed number. The four main journeys (register, KYC, loan submission, payment) run end to end on real devices before each release.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. GitHub ruleset read through the API on 9 Oct 2026.

### Test inventory

| Package | Test files |
|---|---|
| `digital` | 145 |
| `data/customer` | 33 |
| `shared_lib/core` | 15 |
| **Total** | **193** |

| Kind | Count |
|---|---|
| `testWidgets(` calls | 1,039 |
| `test(` calls | 577 |
| `*_screen_test.dart` files | 85 |
| `*_repository_test.dart` files | 25 |
| `*_use_case_test.dart` files | 13 |
| `*_controller_test.dart` files | 3 (written before the ban) |
| Golden tests (`matchesGoldenFile`) | 0 |
| `integration_test/` folders | 0 |

### The controller-test ban

- `.github/workflows/pr-pipeline.yml`, step "Reject controller_test.dart files" (lines 42–49). It fails any PR that adds or changes a file ending in `_controller_test.dart`. Message: "Controller tests are not allowed. Test the screen instead."
- `AGENTS.md` ("Testing") says the same: test screens only, including the controller.
- Effect: the 72 controllers (for example `submission_controller.dart`, 1,140 lines) can only be tested by pumping a whole screen. Those tests are slow and break when the layout changes.

### Coverage today

- `melos test` (root `pubspec.yaml`) runs `scripts/include_unreached_coverage.sh` first. That script writes a helper test that imports every file in `lib/`, so untested files count as 0%. This is good.
- It then runs `flutter test --coverage` per package, merges with `scripts/combine_coverage.sh`, and strips generated files.
- `pr-pipeline.yml` uploads the result to Codacy (with `continue-on-error: true`) and SonarQube.
- The `master` ruleset requires three checks: `scan-code-coverage`, `Codacy Static Code Analysis` and `Codacy Diff Coverage`.
- **Open question:** "Codacy Diff Coverage" is a required check, so a diff-coverage rule may exist in Codacy. Its threshold is set in the Codacy UI, not in the repo. The parent page says "no threshold". Check the Codacy setting before building a new gate. Note also that if the upload fails, the job still passes.
- Tests run in file order. No random order.

### End-to-end tests

- None in this repo.
- **BFI QA already has a mobile suite** in `bfi-finance/automation-monorepo` (local checkout `lora-workspace/services/automation-monorepo` @ `3ee28dff`, 4 Sep 2026). Folder `packages/mobile-automation/bfi-mobile/`.
- It uses WebdriverIO with Appium, a page-object model and Mocha-style specs. It runs on BFI's own device farm or LambdaTest.
- 15 spec files: loan submission (2W, 4W, guest, draft), home (repeat order, revolving loan, simulation), loan simulation, loan list and detail, notification, account, assets, help (payment methods, contact us).
- Page objects exist for KYC, login and landing. A KYC spec exists since October 2026 (18 specs on 24 Oct 2026), but there is no register spec yet. *Corrected 24 Oct 2026: an earlier version said no KYC spec.* Payment is covered only as the "payment methods" help page.
- `.github/workflows/scheduled-mobile-automation.yml` runs it Mon, Wed and Fri at 17:00 UTC. `upload-app-to-device-farm.yaml` takes the build from Firebase App Distribution.
- `packages/mobile-automation/MIGRATION_PLAN.md` (March 2026) moves older Cucumber tests from `wdio-test-automation` into this package. Several modules are still "pending".
- The suite is not linked to app PRs or to the release flow in `bravo-customer-app`.

## Target (what Jago does, adapted for BFI)

| Jago pattern | Path | BFI adaptation |
|---|---|---|
| About 5,288 test files across modules | `module_*/test/`, `app_*_mobile/test/` | Grow unit tests for use cases and notifiers first |
| Random test order | `very_good test` in `scripts/ci-module-test-coverage.sh` and `.gitlab-ci.yml` | `flutter test --test-randomize-ordering-seed random` |
| Coverage gate on changed files | `coverage` job in `.gitlab-ci.yml`; `scripts/calculate-min-coverage.sh`, `scripts/coverage-result.sh` | Same idea as a GitHub step |
| End-to-end on real devices | `app_jago_mobile/e2e_mobile/` (WebdriverIO, Appium, Cucumber, BrowserStack; 243 `.feature` files) | Use BFI's existing `automation-monorepo` mobile package |

How Jago's coverage gate works, in short:

1. For each module the MR touches, list the changed files with `git diff` against the merge base.
2. Remove generated and mock files from `lcov.info`.
3. Keep only the changed files with `lcov --extract`.
4. Take the **lowest** line coverage across modules.
5. Fail if it is not above the threshold (a CI variable).

Riverpod mapping: test a `Notifier` with a `ProviderContainer` and overrides. No widget pump needed.

```dart
test('submit shows error when repository fails', () async {
  final container = ProviderContainer(overrides: [
    loanRepositoryProvider.overrideWithValue(FakeLoanRepository.failing()),
  ]);
  addTearDown(container.dispose);

  await container.read(submissionProvider.notifier).submit();

  expect(container.read(submissionProvider).hasError, isTrue);
});
```

**Do not copy:** a second e2e framework. BFI QA already chose WebdriverIO + Appium; Jago's Cucumber layer and BrowserStack config are not needed. Do not copy Jago's "fail when equal to threshold" quirk (`-le` in `coverage-result.sh`); fail only when below.

## Plan

### Step 1: lift the controller-test ban (1 PR)

- Remove lines 42–49 from `.github/workflows/pr-pipeline.yml`.
- Update `AGENTS.md` "Testing": test use cases and notifiers with unit tests; keep a small number of screen tests for user flows.
- Check: a PR with a new `*_controller_test.dart` passes CI.

### Step 2: write down the test pyramid (1 PR, docs)

| Layer | What to test | Tool | Target share |
|---|---|---|---|
| Unit | Use cases, mappers, notifiers, validators | `test`, `ProviderContainer`, `mocktail` | Most tests |
| Repository | JSON to model, error mapping | `test` with a fake `HttpClient` | One per repository (exists today) |
| Widget | One screen state per test, key interactions | `testWidgets` | Fewer, focused |
| Golden (optional) | Design-system components | `matchesGoldenFile` | Core components only |
| End to end | 4 main journeys | `automation-monorepo` mobile suite | Few, slow, before release |

Put this table in `AGENTS.md` so AI tools follow it too.

### Step 3: random test order (1 PR)

- In the root `pubspec.yaml` melos `test` script, add `--test-randomize-ordering-seed random`.
- Fix the tests that fail. They share state and would fail randomly later anyway.

### Step 4: coverage gate on changed files (1–2 PRs)

- First, read the Codacy "Diff Coverage" setting. If it already has a threshold, decide whether to keep Codacy or replace it.
- Add `scripts/coverage-changed-files.sh`. It lists changed `lib/**/*.dart` files per package (excluding `.g.dart`, `.freezed.dart`, `.mapper.dart`), extracts them from `combined_coverage/lcov.info`, and prints line coverage.
- Add a step after "Run test with coverage" in `pr-pipeline.yml`. Fail if coverage on changed files is below the threshold.
- Start at 70% (the parent page's suggestion). Raise it by 5 points each quarter, up to 80%.
- Remove `continue-on-error: true` from the Codacy upload, or stop requiring the Codacy check. A required check should not pass on a failed upload.
- Check: a test PR that adds an untested use case fails.

### Step 5: unit tests for the biggest logic files (ongoing, with Layering)

- Start with `loan/submission/submission_controller.dart` (1,140 lines) and `auth/kyc/kyc_use_case.dart` (970 lines).
- Write tests while moving logic into domain use cases. Do not write tests for code that is about to move.

### Step 6: connect the existing e2e suite (2–3 sprints, with QA)

- Agree with QA (owners of `automation-monorepo`) on four journeys: register, KYC, loan submission, payment.
- Fill the gaps: add a register spec (page objects exist) and review the KYC spec that was added in October 2026. Add a real payment journey, not only the help page.
- Add stable `Semantics` identifiers (through `AttributeId`) to the screens these journeys use, so selectors do not break on layout or text changes. Flutter `Key`s do not help here: Appium cannot see them (see step 10).
- Trigger the suite from `build-sit-uat.yml` after the Firebase App Distribution upload (a `workflow_dispatch` or `repository_dispatch` call into `automation-monorepo`).
- Make a green run on the release candidate a condition for `build-prod.yml` (a release checklist item first, a hard gate later).
- Check: each release candidate has an e2e result linked in the release notes.

Steps 7–11 build the parity net described in "Keeping features identical" on the parent page. Later plans use it every time they put a new path beside an old one.

### Step 7: golden screenshots of key screens (1–2 PRs)

- Add golden tests (`matchesGoldenFile`) for 5 key screens: home, loan detail, submission review, KYC, payment.
- Pump each screen with fake providers and fixed data, so the picture does not depend on the network or the clock.
- Load the real fonts and run goldens only on the Linux CI image, so pictures match across machines.
- Each golden runs on both paths while a switch flag exists. The same golden file must match both, unless the ledger lists an approved delta.
- Check: changing one colour or one label on a key screen fails the golden test.

### Step 8: recorded SIT API fixtures and a replay harness (1–2 PRs)

- Record real SIT responses for the 4 journeys (register, KYC, loan submission, payment) as JSON files under `test/fixtures/sit/`.
- Scrub personal data before the files are committed: names, NIK, phone numbers, addresses, account numbers. A script checks the files and fails on a match.
- Add a replay harness: a fake `HttpClient` that serves the recorded responses and records every outgoing request.
- A replay test compares two things on both paths: the requests sent (method, path, body) and the mapped result the screen gets.
- Mobile plan 07: Networking uses this harness to compare the old `HttpClient` with the new interceptor chain.
- Check: a replay test fails when a request body field is renamed.

### Step 9: run a widget test on both paths (1 PR)

- Add a test helper, for example `testWidgetsBothPaths(description, flag: LoanFlags.useNewLoanFlow, body)`. It runs the same test body twice: once with the switch flag off and once with it on.
- It overrides the flag through the test flag store (Mobile plan 12: Feature flags). Until that store exists, it overrides the provider that reads the flag.
- The test name shows the path (`[old]` or `[new]`), so a failure says which path broke.
- Check: a test that passes on the old path and fails on the new path shows one green and one red result.

### Step 10: e2e journeys with the switch flag forced off or on (1–2 sprints, with QA)

- Today the specs find elements by what Appium can see, not by Flutter `Key`s. All selectors sit in the page objects in `bfi-mobile/pom/` (`automation-monorepo` @ `3ee28dff`). About 250 are XPath on visible text (`@content-desc` on Android, `@name` or `@label` on iOS), 163 of them through the helper `ComponentPage.elementByDesc`. 17 more use accessibility ids, which are also visible text. Only 6 use `@resource-id`.
- In the app, `@resource-id` comes from `Semantics(identifier:)`. The only place that sets it is `AttributeId` (`digital/lib/app/ui/attribute_id.dart`), used by `DigitalButton`, `DigitalTextField` and 6 other files (loan and home screens, the top-level screen). Its value is built from the analytics event name. So renaming an event (Mobile plan 02: Analytics wrapper) also renames an e2e id.
- The app has 249 `Key('...')` widgets and 597 `find.byKey` calls in tests. Appium does not see these Keys; only widget tests use them.
- Rule: a new path keeps the same visible text, the same `Semantics` identifiers and the same `Key`s as the old path on every screen in the 4 journeys. If a text must change, it is an approved delta and the spec changes in the same release.
- Add a way to force a switch flag in SIT and UAT builds only: a `--dart-define` read at start-up. Prod builds ignore it. The dev-mode toggle (Mobile plan 12: Feature flags) does the same by hand for QA.
- Add the register spec and the payment journey from step 6, and check the KYC spec. Each spec tags the flag value in its report, so a failed run says which path broke.
- Check: the 4 journeys pass on a SIT build with the flag forced off and on a SIT build with it forced on.

### Step 11: parity ledger template (1 PR, docs)

- Add `docs/parity/_template.md` with one table: behaviour | old-path test | new-path test | e2e spec | analytics events | status | approved delta.
- Add a short guide: fill the ledger from today's behaviour before writing the new path; the feature owner signs it off; each approved delta needs product or data protection officer sign-off.
- Mobile plan 08: Layering fills the first ledger, for `loan`.

### Step 12 (optional): golden tests for components

- After the design-system package exists, add goldens for 4–6 core components.
- Run them only on the Linux CI image.

### Parity check

- This plan builds the parity net. It changes almost no app behaviour itself.
- Lifting the controller-test ban, random order and the coverage gate change only CI. The app does not change.
- Adding `Semantics` identifiers for e2e (step 6) changes the accessibility tree, but an identifier is not read aloud by TalkBack or VoiceOver. Do not add or change `Semantics` labels for e2e, because users hear those.
- The net covers the 4 journeys and 5 key screens. A feature outside them needs its own old-path tests first (see Mobile plan 08: Layering).
- The net has no approved deltas of its own. Each feature's ledger lists its approved deltas, and the net skips only those rows.
- The net checks analytics through the golden names file from Mobile plan 02: Analytics wrapper.

## Done when

- `pr-pipeline.yml` has no controller-test ban.
- At least one unit test file exists for every notifier changed in the last quarter.
- Tests run in random order in CI.
- CI fails a PR whose changed files have line coverage below the agreed threshold (start: 70%).
- The coverage check cannot pass when the coverage upload fails.
- Register, KYC, loan submission and payment journeys run on real devices against SIT for each release candidate.
- Median PR test time does not grow (unit tests replace slow screen tests).
- The parity net exists: golden screenshots of the 5 key screens, SIT fixtures with a replay harness, the both-paths widget-test helper, and the parity ledger template.
- The 4 e2e journeys pass on a SIT build with a switch flag forced off and on one with it forced on.
- The rule "a new path keeps the same visible text, `Semantics` identifiers and `Key`s" is written in `AGENTS.md`.

## Effort and owner

- **M** from the parent table. About 3 sprints for steps 1–4, then ongoing. Steps 7–11 add about 2 sprints.
- Owner: Customer Mobile Apps squad for steps 1–5, 7–9, 11 and 12.
- Steps 6 and 10: QA (automation-monorepo owners) with the squad. SRE for the cross-repo trigger.

## Depends on / related plans

- Mobile plan 08: Layering (domain use cases are what unit tests target).
- Mobile plan 09: State management (`Notifier` tests with `ProviderContainer`).
- Mobile plan 13: Design system (golden tests).
- Mobile plan 06: Lint and guardrails (test rules in `AGENTS.md` and the review skill).
- Mobile plan 04: CI/CD (gate placement, e2e trigger after SIT build).
- Mobile plan 01: Security (smoke tests after the keep-rule review).

## Risks

| Risk | Mitigation |
|---|---|
| Coverage gate blocks urgent fixes | Allow a `skip-coverage` label that needs a lead's approval; review its use monthly |
| Teams write low-value tests to hit the number | Gate only changed files; reviewers check test quality; keep the threshold moderate |
| Random order exposes many flaky tests at once | Fix in one sprint; quarantine with `skip` plus a ticket, never delete |
| E2E tests are slow and flaky on the device farm | Keep to 4 journeys; retry once; track flake rate |
| Two QA suites drift (old Cucumber and new Mocha) | Finish the migration in `MIGRATION_PLAN.md` before adding new journeys |
| Codacy and the new gate disagree | Pick one source of truth after step 4 |
