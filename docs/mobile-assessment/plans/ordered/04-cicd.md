**Priority 4 of 13.** Phase 1. One Flutter version and protected prod builds are cheap and unblock the CI gates the other plans add.

## Goal

One Flutter version, set in one file. Build numbers always go up without a human typing them. Prod builds need approval through the GitHub environment, are protected (R8 set explicitly now, RASP later), and roll out to users in stages. The workflows are short enough to read, and we can see how fast and how safely we ship.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. GitHub settings read through the API on 9 Oct 2026 (metadata only).

### Workflows

13 workflow files in `.github/workflows/`, 2,943 lines in total, plus one composite action (`internals/install_flutter/action.yml`).

| Workflow | Lines | Trigger | What it does |
|---|---|---|---|
| `build-prod.yml` | 449 | Manual | Approval step, Android AAB to Play **internal** track, iOS IPA to TestFlight, symbols to Crashlytics and Datadog |
| `build-sit-uat.yml` | 463 | `v*` tag push, or manual | SIT or UAT build to Firebase App Distribution |
| `create-release-tag.yml` | 457 | Manual | `standard-version` tag and changelog |
| `build-prod-test.yml` | 409 | Manual | Prod-like build in `customer_app_prod_test` |
| `build-prod-artifact.yml` | 312 | Manual | Prod-signed APK and IPA as run artifacts, no approval |
| `merge-release-to-master.yml` | 204 | Push to `release-*` | Merges release back to `master` |
| `on-merge-master.yml` | 194 | Push to `master`, `release-*` | Regenerate and format (bot commit), tests, Sonar, dev build |
| `pr-pipeline.yml` | 130 | Pull request | Title, bootstrap, analyze, tests, coverage upload |
| `create-release-branch.yml` | 126 | Cron Monday 17:00 UTC | Cuts the release branch (week 2 of the sprint) |
| `optimize-assets.yml` | 78 | Push with SVG or PNG | Compresses assets |
| `sync-ai-rules.yml` | 53 | Push of `AGENTS.md` | Copies AI rules |
| `build-merged-changelog.yml` | 50 | Push of changelogs | Merges changelog |
| `test.yaml` | 18 | Manual | "Reveal Secret". Must be deleted (see Security plan) |

5 workflows run on a self-hosted runner (`<repo>-runner`): `on-merge-master`, `merge-release-to-master`, `sync-ai-rules`, `optimize-assets`, `build-merged-changelog`.

### Facts that matter for this plan

- **Flutter version in three places.** `README.md` says 3.38.5. `internals/install_flutter/action.yml` clones 3.41.9 (used by 5 workflows). `build-prod-artifact.yml` uses `kefasjw/flutter-action@v2` with `'3.41.9'` typed twice. No `mise.toml`, `.fvmrc` or `.tool-versions`.
- **Build numbers.** `digital/pubspec.yaml` is fixed at `2.0.0+1`. SIT and UAT always build `<version>+1`. Prod uses a version typed into the `version` input. Nothing guarantees the number goes up.
- **Duplicated config.** About 30 `--dart-define` values are repeated in 5 workflows and for both platforms: 279 `dart-define` lines in total.
- **Approval.** `build-prod.yml` uses `trstringer/manual-approval@v1` (2 approvers) as a job step. The `customer_app_prod` environment itself has **no protection rules** and no branch policy. So `build-prod-artifact.yml` and `test.yaml` reach prod secrets with no approval.
- **Unpinned actions.** `fjogeleit/yaml-update-action@main` is used 8 times (a moving branch). `actions/download-artifact@v2` (2) and `actions/checkout@v2` (1) are old majors. The repo allows all actions and does not require SHA pinning.
- **Path filters.** `pr-pipeline.yml` and `on-merge-master.yml` ignore `.github/**`, so workflow changes run no checks.
- **Release candidates.** Local tags show 21 versions with `-rc` tags in 2026. The median version needed 11 release candidates; the most needed 23. That is a rough sign of how much rework happens late.

## Target (what Jago does, adapted for BFI)

Jago's prod pipeline lives in a separate repo (`prod-pipelines/jago-mobile`). The app repo `.gitlab-ci.yml` (704 lines) runs checks, tags the build, and triggers it (`mobile-prod`, `mobile-nonprod` jobs). The prod flow is described in `jago_mobile_cicd.md`.

| Step | Jago | BFI today | BFI target |
|---|---|---|---|
| Trigger | Tag, `master` or `release/*`; a `versioning-mobile` job tags first | Manual dispatch with tag + version | Manual dispatch on a tag, approval through the environment |
| Toolchain | `mise.toml` pins Flutter with a checksum; CI images and the trigger branch also name the version | 3 places, 2 different versions | One `mise.toml`; CI reads it |
| Version and build number | `X.Y.Z+W` tag; `W` comes from a CI variable bumped on every build | Typed by hand (prod) or `+1` (SIT/UAT) | `W` from a counter that only goes up |
| Config | `dart tools/env.dart` writes config; Firebase files injected | About 30 `--dart-define` from secrets, 4 flavors | Same values, kept in one place (`--dart-define-from-file` written by one script) |
| Build | Unsigned AAB; iOS through fastlane with match | Signed AAB; iOS through `xcodebuild` | Keep Android; fastlane + match for iOS is optional |
| Code protection | CodeMix on the unsigned AAB, then `zipalign`, then `apksigner` | None; R8 on through Flutter's default, not set explicitly (*corrected 14 Oct 2026*) | R8 explicit and checked; RASP step after vendor choice |
| Signing | Keystore only in the prod pipeline repo | Base64 secrets in `customer_app_prod` | Same, but only reachable after environment approval |
| Distribution | Play internal (script), TestFlight (fastlane), optional GCS copy for test automation | Play internal, TestFlight, Firebase App Distribution | Add staged rollout on Play production |
| Post-build | Eversafe build registration | Symbols to Crashlytics and Datadog | Add RASP registration later |
| PR checks | Lint + custom rules, format, generated files, package rules, random-order tests, changed-file coverage, Danger | Title, bootstrap, analyze, tests, Codacy/Sonar | See Testing and Lint plans |

**Do not copy:** the separate prod-pipeline repository (environment protection gives most of the benefit for less upkeep). Jago's habit of naming the Flutter version in several places (CI image tags, trigger branch name, `mise.toml`). Jago's single build for all environments; BFI's four flavors are better.

## Plan

Each step is one or two PRs. The app keeps shipping through every step.

### Step 1: protect prod first (with Security plan step 0)

- Delete `test.yaml`.
- Add required reviewers and a branch policy (`master`, `release-*`, `v*` tags) to `customer_app_prod` and `customer_app_prod_test`.
- Move `build-prod-artifact.yml` behind the same environment approval, or delete it if `build-prod-test.yml` covers its use.
- Once the environment has reviewers, remove the `trstringer/manual-approval` step. The environment rule replaces it and is enforced by GitHub.

### Step 2: one Flutter version (1 PR)

- Add `mise.toml` at the repo root with `flutter = "3.41.9"`.
- Change `internals/install_flutter/action.yml` to read the version from `mise.toml` (or use `jdx/mise-action`).
- Replace `kefasjw/flutter-action` in `build-prod-artifact.yml` with the internal action.
- Fix `README.md` (version, missing `melos.yaml`, old `release-2.0.0` branch).
- Check: `grep -rn '3\.[0-9][0-9]\.[0-9]' .github README.md` finds no Flutter version.

### Step 3: build numbers that only go up (1 PR)

- Build number = `github.run_number` of the build workflow plus a fixed offset above the highest number already on Play and App Store Connect. Or keep a repository variable and bump it in the build job.
- Use the same rule for SIT, UAT and prod, so a tester's device can always install the next build.
- Remove the free-text `version` input. Read the version name from the tag.
- Check: two builds of the same tag get different, increasing numbers.

### Step 4: reusable workflows (2–3 PRs)

- Create `.github/workflows/_build-android.yml` and `_build-ios.yml` as `workflow_call` workflows. Inputs: flavor, tag, distribution target.
- Write the `--dart-define` list once: a script `scripts/write-dart-defines.sh` writes `dart_defines.json` from the environment, and the build uses `--dart-define-from-file`.
- Make `build-prod.yml`, `build-sit-uat.yml`, `build-prod-test.yml` and `on-merge-master.yml` call them.
- Pin every third-party action to a commit SHA. Replace `fjogeleit/yaml-update-action@main`. Upgrade `download-artifact` and `checkout` to current majors. Add Dependabot for `github-actions`.
- Check: total workflow lines drop from 2,943 to under 1,500. A SIT build gives the same APK size as before.

### Step 5: make R8 explicit and leave a slot for protection (1 PR)

- R8 already runs through Flutter's default (*corrected 14 Oct 2026*). Mobile plan 01: Security, step 1 sets it explicitly in `build.gradle`. The build workflow checks that `mapping.txt` exists and fails if not, so a tooling change cannot switch R8 off silently.
- Add an empty, clearly named job step "Protect build" between build and sign. When the RASP vendor is chosen, it runs the vendor tool there, then aligns and signs, like Jago's `codemix → zipalign → apksigner` order.
- Add a "Register build" step after upload, for the vendor's build registration.

### Step 6: staged rollout on Play (1 PR)

- Keep the upload to `internal`. Add a manual "Promote" workflow that moves the same version code to `production` with `userFraction: 0.05`, then 0.2, 0.5, 1.0.
- Before each increase, check the Crashlytics crash-free rate and Datadog errors for the new version.
- On iOS, use App Store phased release (set in App Store Connect or with fastlane).
- The Play rollout and a switch-flag rollout are two separate dials. Change only one at a time, so the cohort check (step 8) can tell which one caused a change.

Steps 7–9 run the release side of "Keeping features identical" on the parent page.

### Step 7: run the e2e suite twice on each release candidate (1–2 PRs, with QA)

- For each release candidate, build two SIT apps from the same commit. They differ only in the forced switch-flag value: all switch flags off, and all switch flags on. The reusable build workflow (step 4) takes this as an input. Prod builds ignore it.
- Upload both to Firebase App Distribution and trigger the `automation-monorepo` mobile suite once per build (Mobile plan 03: Testing, step 10).
- Both runs must be green. Link both results in the release notes. Start as a release checklist item, then make it a hard gate for `build-prod.yml`.
- When no switch flag exists, run the suite once.
- Check: a release candidate where the new path breaks a journey shows one green and one red run, and `build-prod.yml` does not start.

### Step 8: cohort dashboard with thresholds (1 PR + a dashboard)

- Mobile plan 05: Logging and crashes tags each RUM session and Crashlytics report with the switch-flag state. The dashboard splits every number by that tag.
- Datadog RUM: crash-free sessions, error rate and screen load time, memory use, old path against new path, for the same app version.
- Firebase or Mixpanel: the funnel of the switched journey (for example loan submission start to submit), old path against new path.
- Proposed starting thresholds, to agree with product and SRE: crash-free sessions on the new path no more than 0.2 points below the old path; error rate no more than 10% higher; p75 screen load no more than 10% slower; funnel conversion no more than 2 points lower. Compare only when each path has enough sessions to be meaningful.
- Each flag step (1% → 10% → 50% → 100%) waits for one full day of data and a green dashboard.
- Check: the dashboard shows both cohorts for a test flag in SIT, and a breached threshold turns its widget red.

### Step 9: kill-switch runbook (1 PR, docs)

- Write `docs/runbooks/kill-switch.md`. The switch flag is the kill switch: setting it back to the old path turns the new path off for everyone.
- Who flips it: the feature owner named in the flag catalogue, or the mobile on-call if the owner cannot be reached. One person flips, a second person checks the console value.
- When to flip: any threshold in step 8 is breached, or a P1 incident points at the new path. Do not wait for a root cause.
- How fast: target 15 minutes from the alert to the flag change. Switch flags are real-time flags (Mobile plan 12: Feature flags), so open apps get the change without a restart and use it at the next journey start.
- After a flip: pause the Play rollout if the new build is also suspected, write a short incident note, and record it in the feature's parity ledger.
- Rehearse the runbook once in SIT for each new switch flag before it reaches 1% in prod.
- Check: one rehearsal is recorded with its time from alert to flip.

### Step 10 (optional): fastlane + match for iOS

- Only if certificate handling is painful today. match keeps certificates in an encrypted git repo or bucket, and all builds use the same ones.
- Otherwise keep `apple-actions/import-codesign-certs` and `xcodebuild`.

### Step 11: run checks on workflow changes (1 PR)

- Remove `.github/**` from the `paths-ignore` of `pr-pipeline.yml`, or add a small `workflow-lint.yml` that always runs: `actionlint`, the secret-echo check, and the SHA-pin check.

### Step 12: measure delivery (DORA-style, 1 PR + a dashboard)

DORA metrics are four standard measures of software delivery.

| Metric | How to measure for BFI |
|---|---|
| Deployment frequency | Number of `build-prod.yml` runs that reach Play production per month (Actions API) |
| Lead time for changes | Time from PR merge to the prod build that contains it (tag dates + PR merge dates) |
| Change failure rate | Share of releases that needed a hotfix tag or a rollback; also release candidates per version (median 11 today) |
| Time to restore | Time from a P1 incident on the app to the fixed build on Play |

- Write a small script that pulls these from the GitHub API each month. Show them on the Datadog CI dashboard or a sheet.

### Parity check

- The reusable workflows (step 4) could change what goes into the app. Compare the `--dart-define` key list and the APK size of a SIT build before and after; they must match.
- The new build-number rule (step 3) changes only the version code. The app itself does not change.
- R8 already runs today, so it is not a delta. After step 5 the build must pass the same smoke list and e2e journeys as today's build.
- The e2e suite runs on both paths for each release candidate (step 7), so a broken new path cannot reach `build-prod.yml` unnoticed.
- In prod, the cohort check (step 8) compares old-path and new-path users. The kill-switch runbook (step 9) says who turns the new path off and how fast.
- This plan has no approved deltas of its own.

## Done when

- `customer_app_prod` has required reviewers; no workflow can use prod secrets without approval.
- The Flutter version appears only in `mise.toml`.
- Every build has a higher build number than the one before, with no manual input.
- Workflow files total under 1,500 lines; `--dart-define` values are listed once.
- Every third-party action is pinned to a SHA.
- `minifyEnabled` is explicit, the prod build fails if `mapping.txt` is missing, and the pipeline has a named protection step.
- Play production releases roll out in stages, with a crash-rate check between stages.
- PRs that change workflows run `actionlint` and the secret check.
- A monthly report shows the four delivery metrics.
- Each release candidate with a switch flag has two green e2e runs (flags forced off and forced on), linked in the release notes.
- A cohort dashboard compares old-path and new-path users against agreed thresholds.
- The kill-switch runbook names who flips a switch flag and how fast, and it has been rehearsed once in SIT.

## Effort and owner

- **M** from the parent table. About 3–4 sprints, spread out.
- Owner: Customer Mobile Apps squad for workflows. SRE / release engineering for environments, runners and Play/App Store access.
- Steps 7–9: the squad with QA (two e2e runs), SRE (cohort dashboard and on-call) and product (thresholds). About 1 more sprint.

## Depends on / related plans

- Mobile plan 01: Security (step 0, R8, RASP vendor).
- Mobile plan 03: Testing (coverage gate, e2e trigger after the SIT build).
- Mobile plan 06: Lint and guardrails (workflow checks, review bot).
- Mobile plan 13: Design system (Widgetbook build and publish job).
- Mobile plan 05: Logging and crashes (crash-free rate used for rollout decisions).

## Risks

| Risk | Mitigation |
|---|---|
| Reusable workflows break a release build | Move SIT first; run old and new side by side for one release |
| New build-number scheme collides with numbers already on the stores | Read the highest number from Play and App Store Connect first; set the offset above it |
| Environment reviewers become a bottleneck | At least 3 reviewers; document a hotfix path |
| Self-hosted runner is a single point of failure | Monitor it; fall back to GitHub-hosted runners for critical jobs |
| Staged rollout slows urgent fixes | Allow a direct 100% promotion with two approvals |
| SHA pinning makes updates tedious | Dependabot opens update PRs |
