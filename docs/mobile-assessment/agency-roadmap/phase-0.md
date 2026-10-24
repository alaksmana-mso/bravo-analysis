## Summary

Phase 0 of the agency apps roadmap ("Close the leak") for the whole `bravo-agency-app` monorepo: GENFI, MyShaf, SQUARE and MY BISPRO. It is linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers all 7 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title, same style as the BFI one (DM-3545): "[Tech x DK] Agency Apps Improvement - Close The Leak". One epic for the monorepo.
* **Plan pages:** GENFI plan 01: Security step 0–2, GENFI plan 02: CI/CD step 3 (and their SQUARE twins).
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026) and the GitHub Actions API. No run log was opened, no secret value was read.

**Why this phase is bigger than BFI's.** The BFI customer app had one leaky workflow that never ran. The agency monorepo has **four**, two of which run on every tag push, and one of them uploads the SQUARE signing keystore and its password file as a downloadable artifact. Everything in this phase is class A: it changes GitHub, CI and secrets, never the app.

### Five facts that shape Phase 0

**1. Four workflows print or export secrets.**

| Workflow | What it does | Runs |
| --- | --- | --- |
| `test.yaml` "Reveal Secret" | Echoes `SSH_PRIVATE_KEY` and `KNOWN_HOSTS` through `sed 's/./& /g'`, which defeats log masking. Added 26 Nov 2025 by a direct commit, no PR | 0 (disabled by hand) |
| `debugger.yaml` | 52 secret echoes in 4 jobs, piped through `sed` and `base64`: keystores, `BRAVO_GCP_SA_KEY`, `GOOGLE_SERVICES_JSON`, `KEYCLOAK_CLIENT_SECRET`, `SSH_PRIVATE_KEY` and more. Added 9 Feb 2026, no PR. Uses the four `*_ro_tools` environments | 0, still active |
| `agent-tools-convent-deploy-tag-cd-pipeline.yml` lines 94–95 | Step "Reveal secret" echoes `FIREBASE_API_KEY` with the same trick, on every `*-agent-tools-convent` tag | 162, latest 22 Oct 2026 |
| `are-tracker-deploy-tag-cd-pipeline.yml` lines 84–91 | Decodes `KEYSTORE_BASE64` and `KEYSTORE_PROPS_BASE64` to files and uploads them as artifact `android-keystore-files`, 1-day retention, downloadable by anyone with repo read | 156, latest 21 Oct 2026 |

**2. The SQUARE upload key has left the runner 156 times.** A signing key that was downloadable must be treated as lost. If Play App Signing is on for SQUARE, the key is only the *upload* key and Google can reset it (question 2). If it is not on, the fix is a new app signing key through Play's key upgrade flow, which is slower.

**3. Prod approval is a workflow step, not an environment rule.** `trstringer/manual-approval` asks 2 of 8 or 9 named people, authenticated with `GH_PAT`. `agent_tools_prod_release_build.yaml` and `are-tracker-prod-deployment-build.yml` build prod-signed APK and IPA with **no approval at all**. The org is on the GitHub Team plan, so required reviewers on environments are not available for a private repo (the BFI Phase 0 page has the detail). Branch and tag rules on environments are available.

**4. PR checks run only when `*.dart` files change.** A PR that only adds a workflow gets no checks. Secrets are interpolated straight into `run:` commands (for example `GOOGLE_SERVICES_JSON`) and dispatch inputs are used unquoted in shell.

**5. Some of the work is already ticketed for the BFI app.** `BRAVO_GCP_SA_KEY` is an organization secret used by 51 repos; its rotation is DM-3591 (Bimo, SRE). `SSH_PRIVATE_KEY` here is this repo's own environment secret, separate from the customer app's. Codacy is BFI's standard scanner and already runs on this repo's PRs (confirm the workflow-file patterns, question 4).

Also: 31 workflow files, 5,582 lines, 5 disabled. `SHA_256_FINGERPRINT` is passed in 25 places but not to the convent SIT pipeline, so SIT builds ship without certificate pinning. The pinning fork `shared_lib/http_certificate_pinning` forwards the `Authorization` header to native code and has a `print` at line 42.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. All class **A** unless marked.

| # | Proposed ticket title | Today (24 Oct) | App | Owner (role) | Size | Blocked by | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1 | `ci: Remove the four secret-leaking workflows and steps` | All four present on `master` | shared | Agency squad | XS | – | | |
| 0.2 | Rotate the exposed secrets; reset the SQUARE upload key | Not started | shared, SQUARE | SRE (Bimo) + Agency squad + release manager | M | Q2, DM-3591 | | |
| 0.3 | Branch and tag rules on the prod environments; push ruleset on workflows; fold the `_build` workflows behind the approval | 0 protection rules (confirm) | shared | Repo admin | S | – | | |
| 0.4 | `ci: Codacy workflow scanning + workflow-lint on every PR` | PR checks skip non-Dart changes | shared | Agency squad + Codacy admin | S | Q4 | | |
| 0.5 | `ci: SHA_256_FINGERPRINT in every build` + `fix(pinning): no Authorization to native, no print` | SIT builds unpinned; fork leaks header | shared | Agency squad | S | – | | |
| 0.6 | Retire the `*_ro_tools` environments and their secrets | 4 environments for an app that moved repos | shared | Repo admin + RO Tools squad | XS | RO Tools confirms | | |
| 0.7 | `ci: Least-privilege permissions, pin yaml-update-action@main, secrets to env:` | Default token write, one action on `@main` | shared | Agency squad | S | – | | |

**Suggested order.** Day 1: 0.1 (disable in the UI first, then the PR). Days 1–3: 0.2 with SRE. Week 1: 0.3, 0.6. Week 2: 0.4, 0.5, 0.7.

## Definition of ready for every Phase 0 ticket

* The ticket links to this page and to the epic.
* The owner is named, not only the team.
* Acceptance criteria are copied from the step below.
* For secret rotation: the person who can create the new value and the person who can update the GitHub secret are both named and available on the same day.
* Nobody opens the logs of the 162 convent runs or the 156 ARE tracker runs to "check". The API metadata is enough.

## Step 0.1: Remove the four secret-leaking workflows and steps

**Today.** See fact 1. `test.yaml` is disabled by hand; `debugger.yaml` is active; the convent and ARE tracker pipelines run on every tag.

**Tasks.** Disable `debugger.yaml` and the two tag pipelines in the Actions UI first. One PR: delete `test.yaml` and `debugger.yaml`; delete the "Reveal secret" step (convent lines 94–95); delete the keystore upload step (ARE tracker lines 84–95, keep the decode step that the build needs). Check every release branch and tag workflow for copies.

**Acceptance criteria.** The Actions API no longer lists "Reveal Secret" or "debugger". `grep -E "echo.*secrets\."` and `grep upload-artifact` next to `keystore` return nothing. The next convent and ARE tracker tag builds pass.

**Who / size.** One Agency engineer. XS. Two reviewers.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete all four in one PR, after disabling in the UI | Closes every path in a day | One PR touches four workflows; reviewers must read all four |
| B. One PR per workflow | Smaller reviews | Four days of partial exposure |
| C. Delete the two dead workflows, keep the pipelines and only remove the steps "when touched" | Less change | The convent and ARE tracker pipelines run on every tag; they are the live leaks |

**Recommended: A.**

## Step 0.2: Rotate the exposed secrets; reset the SQUARE upload key

**Today.** Exposed to anyone who could read a run log or download an artifact: `FIREBASE_API_KEY` (SIT), `SSH_PRIVATE_KEY`, `BRAVO_GCP_SA_KEY` (org secret, DM-3591), `KEYCLOAK_CLIENT_SECRET`, `GOOGLE_SERVICES_JSON`, both Android keystores and their password files. The SQUARE keystore was a downloadable artifact 156 times.

**Tasks.** With SRE: rotate `SSH_PRIVATE_KEY` and `KNOWN_HOSTS` in every environment of this repo; `KEYCLOAK_CLIENT_SECRET` in Keycloak and in every environment; `FIREBASE_API_KEY` (SIT project; restrict the key in Google Cloud Console too); `BRAVO_GCP_SA_KEY` through DM-3591. For SQUARE: if Play App Signing is on, request an upload-key reset in Play Console and create a new upload keystore; if not, run Play's app signing key upgrade. Rotate the GENFI keystore passwords too (they were in `debugger.yaml`). Store the new keystore files only as environment secrets and never as artifacts.

**Acceptance criteria.** Every listed secret shows today's date in GitHub. Old Keycloak client secret rejected. Old Firebase key disabled. SQUARE's next internal-track upload is signed with the new upload key and Play accepts it. The old keystores are deleted from every laptop that had them (ask).

**Who / size.** SRE + Agency squad + release manager (Play Console). M, mostly calendar time.

**Risks and rollback.** A wrong Keycloak secret breaks SQUARE and GENFI sign-in in SIT and prod at once: rotate SIT first, then prod on a quiet day, with a tester ready. A wrong upload key is rejected by Play, not installed by anyone: safe.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rotate everything on a schedule, keystore reset through Play App Signing | Closes the exposure; the upload key becomes replaceable in future too | Needs Play Console admin and SRE on the same days |
| B. Rotate only the secrets that were printed in runs that succeeded | Less work | The ARE tracker artifact was downloadable regardless of log success; the keystore must be reset either way |
| C. Rotate, and move the Play upload to keyless sign-in (Workload Identity Federation) in the same change | Removes `BRAVO_GCP_SA_KEY` from this repo for good | Bigger change; do it in Phase 2 after the BFI app proves the pattern |

**Recommended: A now, C in Phase 2.**

## Step 0.3: Branch and tag rules, push ruleset, one prod workflow per app

**Today.** Prod environments (`agency_prod_agent_tools`, `agency_prod_are_tracker`, the MY BISPRO one) have no protection rule that we could read (question 1). The `_build` workflows produce prod-signed binaries with no approval. The approval step needs 2 of 8–9 people and runs on `GH_PAT`.

**Tasks.** On each prod environment: deployment branches and tags = `master`, `release-*`, `v*`. A push ruleset "Restrict file paths" on `.github/workflows/**` with a short bypass list. Merge `agent_tools_prod_release_build.yaml` and `are-tracker-prod-deployment-build.yml` into the main prod workflows behind an "artifacts only" input, so every prod-signed build passes the approval. Keep the 2-approval step (an environment rule would allow 1, and is not available on the Team plan). Replace `GH_PAT` in the approval step with a GitHub App token and set `exclude-workflow-initiator-as-approver: true`.

**Acceptance criteria.** A dispatch of a prod workflow from a feature branch fails at the environment check. No workflow builds a prod-signed binary outside the approval. A PR from a non-listed user that changes a workflow is rejected.

**Who / size.** Repo admin + one Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Branch and tag policy + push ruleset + fold the `_build` workflows + harden the approval step | Everything the Team plan allows, in one ticket | More settings to own; the bypass list must stay short |
| B. Branch and tag policy only | Smallest | The `_build` workflows still skip approval |
| C. GitHub Enterprise for required reviewers, or a separate prod-pipeline repo | Enforced by GitHub | A management decision, tracked on the BFI Phase 0 page (Q1 there); do not wait for it |

**Recommended: A.**

## Step 0.4: Codacy workflow scanning and a `workflow-lint` job on every PR

**Today.** `pr-check-code-analysis.yml` and `pr-check-test-coverage.yml` trigger only on `*.dart` paths. Codacy runs on the repo (confirm the GitHub Actions patterns are on, question 4). Secrets are interpolated into `run:` and dispatch inputs are unquoted.

**Tasks.** Codacy: make sure Opengrep and Trivy are on for GitHub Actions files; add `.codacy/codacy.yaml` with the tool list, like other BFI repos. A small `workflow-lint.yml` with no path filter: `actionlint`; fail if any `upload-artifact` path matches `*.jks`, `*.keystore`, `*.properties`, `*.p12`, `*.mobileprovision`; fail if a `run:` line prints a `secrets.*` expression (only if Codacy does not already); SHA-pin check. Move secret interpolation out of `run:` into `env:`; quote dispatch inputs.

**Acceptance criteria.** A test PR that re-adds the keystore upload step fails. A test PR with a copy of `debugger.yaml` is flagged. A workflow-only PR shows the check and cannot merge while it fails (required in the ruleset after 1 week).

**Who / size.** One Agency engineer + Codacy admin. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Codacy for the security patterns + a tiny `workflow-lint` for `actionlint`, artifact paths and SHA pins | BFI's standard scanner, one small job for what it does not do | Pattern switches are UI-only in Codacy |
| B. Our own grep script only (as plan 01 step 1 wrote) | No dependency on Codacy settings | Easy to bypass; duplicates Codacy |
| C. Codacy only | No new workflow | No `actionlint`, no artifact-path rule, which is this repo's actual leak |

**Recommended: A.**

## Step 0.5: Certificate pinning in every build, fix the pinning fork

**Today.** `SHA_256_FINGERPRINT` is passed in 25 places but not to the convent SIT pipeline or every ARE tracker and MyShaf SIT job. `CertificatePinningInterceptor` is added only when the define is non-empty, so an unpinned build silently works. The fork `shared_lib/http_certificate_pinning` forwards the `Authorization` header to native code and prints at line 42; it is excluded from analysis.

**Tasks.** Pass the define in every build job that leaves a runner. CI assertion that it is non-empty. In the fork: stop forwarding `Authorization` to native code, remove the `print`, add the package to analysis, add a test.

**Acceptance criteria.** `grep SHA_256_FINGERPRINT` counts one per build job. A build with an empty define fails CI. The fork's test passes and the header no longer appears in the native call.

**Who / size.** One Agency engineer. S. The fork change is class B (same behaviour for a pinned build).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Define everywhere + assertion + fork fix | Closes a leak and a silent gap | SIT builds with a wrong fingerprint now fail instead of silently unpinning: that is the point |
| B. Define everywhere, fork later | Smaller | The header keeps reaching native code |
| C. Replace the fork with a maintained pinning package | No fork to own | A dependency change in Phase 0; do it in Phase 4 with the interceptor chain |

**Recommended: A.**

## Step 0.6: Retire the `*_ro_tools` environments

**Today.** `dev_ro_tools`, `sit_ro_tools`, `uat_ro_tools`, `prod_ro_tools` belong to RO Tools (myBRO), which moved to `bravo-ro-tools-apps`. `debugger.yaml` used them. Their secrets may still be live.

**Tasks.** RO Tools confirms nothing uses them. Delete the environments and their secrets. Rotate any secret that also exists in the new repo.

**Acceptance criteria.** `GET /environments` lists no `*_ro_tools`. RO Tools builds still pass in their repo.

**Who / size.** Repo admin + RO Tools squad. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete after RO Tools confirms | Clean | Waits on another squad |
| B. Delete now | Fast | Breaks RO Tools if anything still points here |
| C. Leave them | None | Live secrets in environments nobody owns |

**Recommended: A.**

## Step 0.7: Least-privilege permissions, pinned actions, secrets in `env:`

**Today.** Not every workflow has a `permissions:` block (the default token is write). `fjogeleit/yaml-update-action@main` is on a moving branch. `update-graphify.yaml` runs `bfi-base-template@master` with `secrets: inherit` and `contents: write`.

**Tasks.** `permissions: contents: read` at the top of every workflow, more only per job. Pin every action to a commit SHA, including `yaml-update-action` and the `bfi-base-template` reusable workflow. Dependabot for `github-actions`. Secrets through `env:` only.

**Acceptance criteria.** `actionlint` and the SHA-pin check pass on `master`. No `@main` or `@master` reference remains. The default workflow permission is read-only in the repo settings.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. All of it in one PR with Dependabot | GitHub's own guidance | Dependabot PRs to review weekly |
| B. Pin third-party actions only | Smaller | GitHub-owned actions on tags can still move |
| C. Later, with the reusable workflows (Phase 2) | One rewrite | The `@main` action and the write token stay for months |

**Recommended: A.**

## Exit gate for Phase 0

* The four leaking workflows and steps are gone. No workflow uploads a signing file.
* Every exposed secret is rotated; the SQUARE upload key is reset.
* Prod environments accept only `master`, `release-*` and `v*`; no prod-signed build skips the 2-approval step.
* Every PR, including workflow-only PRs, runs Codacy and `workflow-lint`.
* Every build that leaves a runner is pinned.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | What protection rules do the three prod environments have today? (Could not be read from this session) | Repo admin | |
| Q2 | Is Play App Signing on for SQUARE (`are_tracker`) and GENFI? Decides whether the keystore reset is an upload-key reset or a key upgrade | Release manager | |
| Q3 | Who holds the SSH key and the Keycloak client, and who can rotate them the same day? | SRE + Agency squad | |
| Q4 | Are Codacy's GitHub Actions patterns on for this repo, and who is the Codacy admin? | Squad lead | |
| Q5 | Does RO Tools still use anything in this repo? | RO Tools lead | |
| Q6 | Epic: one for the monorepo, owned by whom? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Four leaking workflows | `grep -lE "echo.*secrets\."` on `.github/workflows` at `1e50b819`; run counts from the GitHub Actions API (plan 01) |
| Keystore artifact | `are-tracker-deploy-tag-cd-pipeline.yml` lines 84–91 |
| Approval step, `_build` workflows, Dart-only PR checks | plan 01 and plan 02 "today" sections; `pr-check-*.yml` `paths:` |
| Pinning gaps | `grep -c SHA_256_FINGERPRINT .github/workflows` = 25; convent SIT pipeline has none |
| Team plan, no environment reviewers | BFI Phase 0 refinement notes (same org) |
| `BRAVO_GCP_SA_KEY` ticket | DM-3591 under DM-3545 |

## Sources for the recommendations

* BFI Phase 0 refinement notes (Codacy, GitHub Team plan limits, key-location table, keyless Google sign-in).
* GitHub, [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use): pin to a commit SHA, least-privilege token, `CODEOWNERS` on workflows, secrets in `env:`.
* GitHub, [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments): branch and tag policies on Team; required reviewers only for public repos on Team.
* Google Play, [Play App Signing](https://support.google.com/googleplay/android-developer/answer/9842756): upload-key reset.
* [trstringer/manual-approval](https://github.com/trstringer/manual-approval): `exclude-workflow-initiator-as-approver`, App token.
