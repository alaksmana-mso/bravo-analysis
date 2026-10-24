## Summary

This page prepares Phase 0 of the mobile roadmap ("Close the leak") for refinement on **Wednesday 21 Oct 2026**. It covers every Phase 0 step: what is true today, what to do, acceptance criteria, who is needed, size, risks, and the questions to answer in the session.

* **Epic:** DM-3545 "[Tech x DK] Mobile App Improvement - Close The Leak" (owner Samuel Christian Putra). No tickets under it yet.
* **Parent:** Mobile roadmap: step by step, section "Phase 0: Close the leak".
* **Groomed on Wednesday 21 Oct 2026.** The team created 5 tickets under DM-3545: DM-3590 (SSH key rotation, Bimo), DM-3591 (`BRAVO_GCP_SA_KEY` rotation with SRE, Bimo), DM-3592 (deployment branch and tag rules, Samuel), DM-3593 (remove Reveal Secret and `build-prod-artifact`, Samuel), DM-3594 (CI check for printed secrets, Andre). The keys are in the table below. *Note 24 Oct: the page version published on 21 Oct had reverted the 20 Oct Codacy and key-location sections, most likely an older editor draft. They are restored here with the ticket keys added.*
* **Revised on 20 Oct 2026 (later), after team input.** Steps 0.6 and 0.7 now use **Codacy**, BFI's standard scanner, instead of a new tool. A new section "Where should keys live?" answers the Cloud KMS question. Step 0.2b now builds on the keyless Google sign-in that 27 BFI repos already use.
* **Options and recommendations added on 20 Oct 2026.** Each step now has 3 options, a recommendation, and the best-practice source behind it. Sources are listed at the end.
* **Facts checked on 19 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `4fb4175`, its GitHub settings, and the GitHub docs. Secret values were never read. Only secret names, dates and locations were listed.

**Three facts change the plan.** Please read these before the session.

1. **GitHub Team plan cannot add required reviewers to environments in a private repo.** The org is on the Team plan and the repo is private. GitHub's docs say required reviewers and wait timers are "only available for public repositories" on Free, Pro and Team. So step 0.3 cannot be done as written. Branch and tag rules on environments *are* available on Team. See step 0.3 for the proposed split.
2. **Step 0.5 should not happen while we are on Team.** The `trstringer/manual-approval` step is the only approval gate today, and it needs **2** approvals. An environment rule (if we ever get it) needs only **1**. Keep the step.
3. **`BRAVO_GCP_SA_KEY` is an organization secret, shared by many repos.** It is not only a mobile secret. A code search finds it in workflows of 51 repos in `bfi-finance` (backend services, LORA services, web apps). In this repo it is the key that uploads the app to **Google Play**. Rotating it touches every one of those repos at once.

**Two more facts found on 20 Oct 2026:**

* The repo's default `GITHUB_TOKEN` permission is **write**, and "Allow GitHub Actions to create and approve pull requests" is **on**. 4 workflows (`build-prod`, `build-prod-test`, `build-prod-artifact`, `create-release-tag`) have no `permissions:` block, so they get the write token. GitHub's advice is read-only by default.
* The approval step and 7 other workflows use `GH_PAT`, an **organization secret last updated 15 Feb 2022**. A personal access token that has not changed for more than 4 years is a long-lived credential with unknown scope.

**Good news since the roadmap was written:** someone disabled the "Reveal Secret" workflow in the Actions UI on **16 Oct 2026**. It can no longer be dispatched. The file is still on `master` and all 4 release branches.

## Steps at a glance

Proposed ticket titles follow the repo's PR title rule: `type: [DM-xxxx] Sentence`. Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, including review.

| # | Proposed ticket title | Status on 19 Oct | Owner (role) | Size | Blocked by | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1 | `ci: Remove Reveal Secret workflow` (master + 4 release branches) | Disabled 16 Oct. File still on 5 branches | Samuel | XS | – | DM-3593 | |
| 0.2a | Rotate `SSH_PRIVATE_KEY` and `KNOWN_HOSTS` check | Not started | Bimo + key owner | S | Who owns the key (question Q2) | DM-3590 | |
| 0.2b | Rotate `BRAVO_GCP_SA_KEY` (org secret) | Not started | Bimo (SRE) | S–M | SRE agreement (Q3) | DM-3591 | |
| 0.3a | Deployment branch and tag rules on `customer_app_prod` and `customer_app_prod_test`, push ruleset on `.github/workflows/**`, read-only default token | Not started | Samuel | S | – | DM-3592 | |
| 0.3b | Decide: required reviewers on prod environments (needs GitHub Enterprise, or another control) | Not possible on Team | Engineering manager + SRE | Decision | Licence decision (Q1) | | |
| 0.4 | `ci: Put build-prod-artifact behind the approval gate` or delete it | Decided: delete (in DM-3593) | Samuel | XS–S | – | DM-3593 | |
| 0.5 | ~~Remove `trstringer/manual-approval`~~ **Keep it and harden it**: no self-approval, team approvers, GitHub App token instead of `GH_PAT` | Not started | Mobile squad + org admin (GitHub App) | S | – | | |
| 0.6 | `ci: Codacy scanning for workflow files` (tool list in `.codacy/codacy.yaml`; grep step only if Codacy misses the `test.yaml` trick) | Ticket created as "Add CI check to fail workflows printing secrets" | Andre + Codacy admin | S | Q15 | DM-3594 | |
| 0.7 | `ci: workflow-lint job + pin actions to commit SHAs` | Codacy runs on workflow-only PRs; no `actionlint`; 42 action lines on tags | Mobile squad | S | – | | |

Suggested order: 0.1 and 0.3a first (smallest, biggest effect), then 0.6 and 0.7, then 0.2a, 0.4, then 0.2b with SRE. 0.3b is a decision, not code.

## Recommendations at a glance

| # | Recommended option | In one line |
| --- | --- | --- |
| 0.1 | C: delete on all 5 branches + audit-log check | Remove it everywhere and record who ran, changed or disabled it |
| 0.2a | A now, then C | Rotate the SSH key this week. Then replace it with a short-lived, read-only GitHub App token |
| 0.2b | C, with A done by SRE | Give Google Play its own keyless account, using the Workload Identity Federation setup BFI already runs for 27 repos. SRE rotates the shared key |
| 0.3 | B now, C as a recorded decision | Branch and tag rules, push ruleset on workflows, code owners, read-only token. Enterprise is a management call |
| 0.4 | A if unused, else B now and C in Phase 2 | Fewer workflows that can reach prod secrets |
| 0.5 | B | Keep the 2-approval step, block self-approval, swap the 2022 token for an App token |
| 0.6 | A | Turn on Codacy's GitHub Actions scanning (Opengrep + Trivy) for this repo, like other BFI repos. Keep a small grep step only for what Codacy does not catch |
| 0.7 | C | Codacy already runs on workflow-only PRs. Add a tiny `workflow-lint` job for `actionlint` and the grep step, and pin every action and reusable workflow to a commit SHA |

## Definition of ready for every Phase 0 ticket

* The ticket links to this page and to the epic DM-3545.
* The owner is named, not only the team.
* Acceptance criteria are copied from the step below.
* For secret rotation: the person who can create the new key and the person who can update the GitHub secret are both named and available on the same day.
* Nobody opens the log of run `20612762797` (the one "Reveal Secret" run). The API metadata is enough.

## Step 0.1: Remove the "Reveal Secret" workflow

**Why.** The file `.github/workflows/test.yaml` prints three secrets with a space between each character, so GitHub's log masking does not hide them. Disabling it in the UI is reversible by anyone with admin rights. Deleting it is the real fix.

**Today (19 Oct).**

* Workflow state: `disabled_manually`, changed on 16 Oct 2026 14:09 WIB.
* File present on `master`, `release-2.24.x`, `release-2.25.x`, `release-2.26.x`, `release-2.27.x` (same blob on all 5).
* It has run once: run `20612762797`, 31 Dec 2025, conclusion `failure`, before any step started.
* `master` and `release*` are protected by the ruleset "Protected Branch": PR required, 2 approvals, squash only, Codacy checks required. Admins can bypass.

**Tasks.**

1. One PR per branch that deletes `test.yaml` (5 PRs). Title: `ci: [DM-xxxx] Remove Reveal Secret workflow`.
2. Keep the workflow disabled until all 5 PRs are merged.
3. Do not cherry-pick anything else into release branches in the same PR.

**Acceptance criteria.**

* `GET /repos/bfi-finance/bravo-customer-app/contents/.github/workflows/test.yaml?ref=<branch>` returns 404 for all 5 branches.
* The Actions workflow list no longer shows "Reveal Secret" (GitHub drops it once the file is gone from the default branch).

**Who.** One mobile engineer. Two reviewers per PR (ruleset).

**Risks.** None to the app. PRs that only touch `.github/**` skip "CI On Pull Request" today (see 0.7), but Codacy still reports, so the PRs can merge.

**Questions.**

* Q4: Who disabled the workflow on 16 Oct? Record it in the ticket for the audit trail.

### Options and recommendation (0.1)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete the file on all 5 branches (5 PRs). Keep the workflow disabled until all are merged | Closes it for good. GitHub's guidance is to remove what is no longer needed | 5 small PRs, 2 reviews each |
| B. Delete on `master` only. Leave release branches until they retire | 1 PR | The file stays on release branches for months. Anyone who re-enables the workflow can dispatch it from those refs |
| C. Option A, plus an audit-log check: an org owner lists every dispatch of this workflow and every enable or disable event, and records who disabled it on 16 Oct | Gives audit and the security team evidence, not only a fix | Needs an org owner for 30 minutes |

**Recommended: C.** The deletion is cheap. The audit-log record answers the first question an auditor will ask: was it ever used?

## Step 0.2a: Rotate `SSH_PRIVATE_KEY` (and `KNOWN_HOSTS`)

**Why.** "Reveal Secret" was built to print this key. The one run failed before it started, so the key was most likely not printed. But anyone who could dispatch the workflow could have read it. Rotation is the safe default.

**Today (19 Oct).**

* What it does: CI uses it with `shimataro/ssh-key-action` to pull private git dependencies: `bfi-flutter-packages` (5 references), `bfi-flutter-device-integrity`, `bravo-image-validation-mobile-sdk`, `bfi-protobuf`.
* Where it is stored: **5 separate environment secrets**, not one repo secret.

| Environment | `SSH_PRIVATE_KEY` last updated | `KNOWN_HOSTS` last updated |
| --- | --- | --- |
| `customer_app_dev` | 2 May 2024 | 2 May 2024 |
| `customer_app_sit` | 2 May 2024 | 2 May 2024 |
| `customer_app_uat` | 2 May 2024 | 2 May 2024 |
| `customer_app_prod` | 2 May 2024 | 2 May 2024 |
| `customer_app_prod_test` | 31 Dec 2025 | 31 Dec 2025 |

* Used by 6 workflows: `pr-pipeline`, `on-merge-master`, `build-sit-uat`, `build-prod`, `build-prod-test`, `build-prod-artifact`.
* **Whose key is it?** Not known. `bravo-image-validation-mobile-sdk` has no deploy keys. One deploy key cannot be attached to several repos. So the key is most likely a personal or machine-user SSH key (inferred, not confirmed). If it is a personal key, it can do anything that person can do on GitHub, including write access.
* `KNOWN_HOSTS` is not a secret value in itself (it holds GitHub's public host keys). It does not need rotation, but check it matches GitHub's current published keys.

**Tasks.**

1. Find the account that holds the public key (Q2). An org admin can check the SSH keys of a machine user. Or ask the person who set it up in May 2024.
2. Create a new key pair. Preferred target: a **read-only deploy key per dependency repo** (4 keys), or one machine user with read-only access to only those 4 repos. Do not use a personal account.
3. Update `SSH_PRIVATE_KEY` in all 5 environments on the same day.
4. Run one SIT build and one PR pipeline to prove dependencies still resolve.
5. Delete the old public key from the account that holds it.

**Acceptance criteria.**

* All 5 environment secrets show today's date.
* The old public key is gone from GitHub (confirmed by the key owner or an org admin).
* A PR pipeline run and a `build-sit-uat` run pass after the change.
* The ticket records which account or deploy keys now hold the new key.

**Who.** A mobile engineer (repo admin, to update env secrets) and the key owner or an org admin (to remove the old key).

**Risks and rollback.** If the new key is wrong, every build fails at "flutter pub get" for git dependencies. Rollback: keep the old key active until step 4 passes, then delete it. Do the change outside the Monday release-branch cut.

**Questions.**

* Q2: Whose account holds the current key? Personal, machine user, or deploy key?
* Q5: Move to per-repo deploy keys now, or keep one machine user? Deploy keys mean 4 secrets to manage, but no account can reach other repos.

### Options and recommendation (0.2a)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rotate in place: new key pair on the same account, update the 5 environment secrets, delete the old public key | Fastest (1 day). Closes the exposure | Keeps an account we cannot name, which may be personal and may have write access |
| B. Read-only deploy key per dependency repo (4 keys) | Each key reads one repo only. No person's account involved | 4 long-lived keys to rotate. CI needs per-repo key mapping (one SSH key per host alias) |
| C. GitHub App token: a small internal GitHub App on the 4 repos with Contents read-only. CI gets a token with `actions/create-github-app-token` (`repositories:` the 4 repos, `permission-contents: read`). Git rewrites `git@github.com:` URLs to HTTPS with the token | No long-lived SSH key. The token lives 1 hour and is revoked at the end of the job. Read-only and limited to 4 repos. GitHub recommends short-lived, well-scoped tokens | Needs an org owner to create the App. The App private key is still a secret, but it can only make read tokens for those 4 repos. Touches 6 workflows |

**Recommended: A this week, then C.** Rotation is the urgent part, because the key was exposed to anyone who could dispatch the workflow. C removes the long-lived key. Make C a separate ticket in this epic. If time is short, move it to early Phase 1.

## Step 0.2b: Rotate `BRAVO_GCP_SA_KEY`

**Why.** "Reveal Secret" was built to print it too. In this repo it is the service-account key that uploads the prod app to **Google Play** (`r0adkll/upload-google-play`, package `id.co.bfi.customer`, track `internal`), in `build-prod.yml` and `build-prod-test.yml`.

**Today (19 Oct).**

* It is an **organization secret**, last updated **9 Apr 2026**. It is not stored in this repo or in its environments.
* A GitHub code search for `secrets.BRAVO_GCP_SA_KEY` finds 51 repos in `bfi-finance`. Examples: `bravo-user-iam-service`, `bravo-agency-service`, `bravo-calculation-service`, `bfi-operation-api`, `lora-cdc-bridge-service`, `lora-ndf-4w`. The search count can include old or archived repos.
* Because it is one org secret, updating it updates every repo at once. That makes the swap easy, and a bad key breaks all of them at once.
* The same key both deploys backend services to GCP (inferred from the other repos) and publishes the customer app to Google Play. One leaked key can do both.
* **BFI already uses keyless Google sign-in (Workload Identity Federation, WIF) in production CI.** 27 repos use the org secret `BFI_DEVSECOPS_WIF_PROVIDER`. For example, `bravo-dms-fe` `deploy-prod.yaml` signs in with `google-github-actions/auth`, `id-token: write`, and the service account `bfi-devsecops-wif@bfi-devsecops.iam.gserviceaccount.com`. There is also `BFI_BRAVONONPROD_WIF_PROVIDER` (June 2026) for non-prod. So option C below reuses a pattern SRE already runs. It is not a new platform.

**Tasks.**

1. With SRE: find the service account behind the key and its GCP project. List its roles and its Google Play Console permissions.
2. Create a new key for the same service account. Update the org secret. Run one build in a backend repo and one `build-prod-test` (Firebase distribution, not Play) to prove it works. Then disable and delete the old key in GCP.
3. Raise a follow-up (not Phase 0): a **separate** service account for Google Play publishing, used only by this repo, and later WIF instead of a key.

**Acceptance criteria.**

* In GCP, the service account shows only the new key. The old key is disabled, then deleted.
* The org secret shows today's date.
* One backend deploy pipeline and one mobile pipeline that uses the key pass after the swap.
* A follow-up ticket exists for "separate Play publisher account".

**Who.** SRE (GCP IAM owner) and a GitHub org admin. The mobile squad only verifies the mobile pipeline.

**Risks and rollback.** Highest-risk step in Phase 0, because it can break deploys of many backend services. Rollback: re-enable the old key in GCP within its deletion grace period, and put the old value back in the org secret. Plan it on a quiet day, with SRE watching, not on a release day.

**Questions.**

* Q3: Does SRE agree to rotate an org-wide key for a mobile finding? Who signs it off?
* Q6: Which GCP project and service account is it? Does it really hold Google Play permissions plus GCP deploy roles?
* Q7: Do we split the Play publisher account now (in Phase 0) or as a follow-up?

### Options and recommendation (0.2b)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. SRE rotates the shared key: new key, update the org secret, test, disable the old key, delete it later | One change fixes all 51 repos | The same key still deploys backends and publishes the app. Still a long-lived key in 51 repos |
| B. Split, with a key: a new service account only for Google Play publishing, its key stored only in `customer_app_prod` and `customer_app_prod_test`. Remove Play access from the shared account. SRE also does A | The mobile app no longer depends on an org-wide key. A leak of one key no longer gives both powers | Still a long-lived key |
| C. Split, with no key: a new Play publisher service account that CI reaches through Workload Identity Federation (`google-github-actions/auth`, job needs `id-token: write`). `r0adkll/upload-google-play` takes `serviceAccountJson: ${{ steps.auth.outputs.credentials_file_path }}`, which its README documents. Trust limited to repo `bfi-finance/bravo-customer-app` on release refs. SRE also does A | No key exists, so none can leak. Google's advice is to avoid user-managed keys and use a dedicated service account per application | The existing WIF provider (`BFI_DEVSECOPS_WIF_PROVIDER`) needs a binding for this repo and a new Play-only service account. The new account must be invited in Play Console. Test on the internal track first |

**Recommended: C for the mobile app, plus A by SRE.** The shared key must be rotated anyway, because it was exposed. Moving Google Play to its own keyless account removes the mobile app from the 51-repo blast radius. If the WIF binding takes too long, use B as a stepping stone. Later, outside Phase 0: the Google org policy "Disable service account key creation", with exceptions, as Google recommends.

## Where should keys live? (the Cloud KMS question)

**Short answer: use Cloud KMS for keys that *sign* something, and use no key at all where Google or GitHub offer keyless sign-in.** Cloud KMS keeps a private key inside Google (optionally in an HSM) and does the signing for you. The key never leaves. It is not a place to park a downloaded service-account JSON or an SSH private key for CI to read back. For stored secret values, the matching Google product is Secret Manager, and BFI also runs HashiCorp Vault.

**What BFI already has.**

* **Cloud KMS** in production use: `bravo-terraform` `product/kms` defines an HSM-protected key, `bfi-go-pkg` `cryptox` and `bfi-java-pkg` `data-encryption` use KMS for data encryption, and `bravo-customer-bff-service` has a KMS data-key sync script.
* **HashiCorp Vault** in project `bfi-devsecops`, auto-unsealed with the KMS key `vault-keyring/vault-key`. `app-deployment` uses it for application runtime secrets. We found no GitHub workflow that reads CI secrets from Vault today.
* **Keyless Google sign-in for CI** (WIF): `BFI_DEVSECOPS_WIF_PROVIDER`, used by 27 repos, including prod deploys.

**Per credential in this repo:**

| Credential | What it does | Best home | Why |
| --- | --- | --- | --- |
| `BRAVO_GCP_SA_KEY` | Uploads the app to Google Play (and, in other repos, deploys to GCP) | **No key.** WIF with a Play-only service account (0.2b option C) | A key in KMS or Secret Manager is still a long-lived key that CI must read. With WIF, CI gets a token that lasts about an hour and only for this repo. Google's advice is to avoid service-account keys |
| `SSH_PRIVATE_KEY` | Reads 4 private git dependencies | **No key.** GitHub App token, read-only, 1 hour (0.2a option C) | GitHub cannot check a signature made in KMS during `git clone` without extra tooling. A short-lived App token removes the key instead of hiding it |
| `ANDROID_KEYSTORE_BASE64` + `ANDROID_KEYSTORE_PROPS_BASE64` | Signs the Android bundle before upload | **Cloud KMS (HSM)** is a good fit, as a later step | Signing is what KMS is for. Cloud KMS has a PKCS#11 library, and Java's `jarsigner` (used for `.aab` files) can sign through PKCS#11. CI signs in with WIF, asks KMS to sign, and never holds the private key. If Play App Signing is on (Q14), this key is only the *upload* key, so a leak can be fixed by asking Google to reset it. Proof of concept needed |
| `IOS_CERTIFICATES_BASE64` + `IOS_CERTIFICATES_SECRET`, provisioning profiles | Signs the iOS app | Keep in GitHub environment secrets for now, or in an encrypted store such as fastlane match | Apple's `codesign` reads keys from the macOS keychain. Signing through Cloud KMS is not a common path on macOS runners |
| `APPSTORE_API_PRIVATE_KEY` | Uploads to TestFlight | Environment secret, scoped to `customer_app_prod` | Apple offers no keyless sign-in from GitHub. Rotate on a schedule |
| `GH_PAT` | Approval step and 7 other workflows | **No token.** GitHub App token (0.5) | A personal token from 2022 should not sit in the prod path |
| Values built into the app (`API_SECRET`, `VIDA_*`, `DATADOG_CLIENT_TOKEN`, …) | Go into the binary as `--dart-define` | Environment secrets are fine | Anyone can pull these out of the app, so a vault does not protect them. Plan 01 step 3 (`API_SECRET` as public) is the real fix |

**Recommended for Phase 0:** WIF for Google Play and a GitHub App token for git dependencies. Both remove the key instead of moving it. **Cloud KMS for the Android upload key** is worth a follow-up ticket (proposed for Phase 2, next to step 2.17 "make R8 explicit"), after a proof of concept. Secret Manager or Vault for CI secrets adds little while the secrets still live in GitHub environments that only release refs can use (0.3).

## Step 0.3a: Branch and tag rules on the prod environments (possible today)

**Why.** Today any branch can run a workflow that uses `customer_app_prod`. That is how "Reveal Secret" could reach prod secrets. A deployment branch and tag policy limits prod secrets to protected refs. This is available on the Team plan.

**Today (19 Oct).**

* All 6 environments have **0 protection rules** and **no** deployment branch policy.
* `customer_app_prod` is used by `build-prod.yml` (4 jobs) and `build-prod-artifact.yml` (2 jobs).
* `customer_app_prod_test` is used by `build-prod-test.yml` (3 jobs). This "test only" workflow also **uploads to Google Play** with the org key. So it needs the same rule.
* Admins can bypass environment rules (`can_admins_bypass: true`).
* Recent tags look like `v2.28.0-rc10`. There is also a stray tag `vnull` (probably from a failed tag run).

**Tasks.**

1. On `customer_app_prod` and `customer_app_prod_test`, set "Deployment branches and tags" to **Selected**: branches `master` and `release-*`, tags `v*`.
2. Check how `build-prod.yml` is started today. It is `workflow_dispatch` with a `tag` input. Confirm the release manager runs it from `master` or a `release-*` branch, not from a feature branch.
3. Optional, same ticket: a tag ruleset so only release engineering can create `v*` tags. Otherwise anyone with write access can create a `v*` tag and use it to reach prod secrets.
4. Delete the stray `vnull` tag (after checking nothing points at it).

**Acceptance criteria.**

* `GET /repos/.../environments/customer_app_prod` shows a `deployment_branch_policy`. Same for `customer_app_prod_test`.
* A test dispatch of `build-prod-test.yml` from a feature branch fails at the environment check.
* The next real prod release from a release branch still works.

**Who.** Repo admin (Samuel or another admin) and the release manager.

**Risks and rollback.** If the release process runs from a branch that is not in the list, the prod build is blocked. Rollback: set the policy back to "No restriction" (one click). Agree the branch list with the release manager first.

**A real case to settle first (found 20 Oct).** On 15 Sep 2026, `build-prod.yml` was dispatched twice from the branch `ci/test-build-prod-android-sdk-2.25.x` (one failure, one cancelled). That branch would not match `master`, `release-*` or `v*`. So either (a) such test runs move to `build-prod-test.yml` on `customer_app_prod_test` with the same rule, or (b) the rule allows a named pattern such as `ci/test-build-prod-*`, which weakens it. Recommendation: (a). Ask the release manager who ran those builds and why (Q16).

## Step 0.3b: Required reviewers on prod environments (decision)

**Why.** Branch rules (0.3a) stop feature branches. They do not stop someone with admin or bypass rights, or a workflow merged into `master` or a release branch. Required reviewers would add a human approval before any job sees prod secrets.

**Today.** Not available. Org plan: **Team**. Repo: **private**. GitHub's docs: required reviewers and wait timers are "only available for public repositories" on Free, Pro and Team plans.

**Options.** See "Options and recommendation (0.3)" below. It covers 0.3a and 0.3b together.

**Questions.**

* Q1: Who decides between A, B and C, and by when?
* Q8: Can we move `CODEOWNERS` for `.github/` and "require code owner review" into Phase 0? Today `CODEOWNERS` has one owner for everything (`* @samuel-bfi`) and the ruleset does not require code-owner review.

### Options and recommendation (0.3)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Environment branch and tag policy on the 2 prod environments (`master`, `release-*`, `v*`), plus a tag ruleset so only release engineering can create `v*` tags | Available on our plan. A feature branch can no longer reach prod secrets | Does not stop a bad workflow that is merged into `master` or a release branch |
| B. Option A, plus: a **push ruleset** "Restrict file paths" on `.github/workflows/**` with a short bypass list (release engineering, SRE). `CODEOWNERS` for `.github/` and "Require review from Code Owners" in the ruleset. Default `GITHUB_TOKEN` set to read-only, and "Allow GitHub Actions to create and approve pull requests" turned off. Ruleset admin bypass changed from "always" to "pull requests only" | Only named people can change workflows, and the right people review them. A workflow cannot approve its own PR. GitHub's changelog (Sep 2024) says push rules are available on Team for private repos | More settings to own. The bypass list must stay small. The 4 workflows without a `permissions:` block need one first, so the read-only default does not break them |
| C. GitHub Enterprise (required reviewers on environments, prevent self-review, no admin bypass), or a separate prod-pipeline repo | Strongest. Enforced by GitHub, not by workflow code | Licence cost for the whole org, or a second repo to maintain. A management decision |

**Recommended: B now, and C recorded as a decision with an owner and a date.** B closes most of the gap at no licence cost. Confirm in Settings → Rules that "New push ruleset" is offered before the ticket is sized. If it is not, fall back to A plus `CODEOWNERS`.

## Step 0.4: `build-prod-artifact.yml` behind the approval gate, or delete it

**Why.** It builds a prod-signed APK and IPA inside `customer_app_prod` with no approval. Signed prod binaries can leave CI as artifacts.

**Today (19 Oct).**

* 314 lines. Header says it builds artifacts only and must not deploy to Firebase, Play or the App Store.
* Uses `customer_app_prod` in 2 jobs, no approval step. Uploads with `actions/upload-artifact@v4` (default retention, so the signed files stay downloadable for days).
* `build-prod-test.yml` covers a similar need but also uploads to Play and Firebase.

**Tasks.**

1. Ask the squad who uses it and why (Q9).
2. If nobody needs it: delete it (one PR on `master`, cherry-pick to release branches if present).
3. If it is needed: add the same `approval-prod` job as `build-prod.yml` (2 approvals) as a `needs:` dependency of both build jobs. Set `retention-days: 1` on the uploads, like `build-prod.yml`.

**Acceptance criteria.**

* Either the file is gone, or a dispatch stops at the approval job and artifacts expire after 1 day.

**Who.** One mobile engineer. Release manager to confirm usage.

**Risks.** None to the app. Someone who relies on it for QA must switch to `build-prod-test.yml`.

### Options and recommendation (0.4)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete it | One less workflow that can sign prod builds | Anyone who uses it moves to `build-prod-test.yml` |
| B. Keep it, add the 2-approval job as a `needs:` dependency, `retention-days: 1` on uploads, `permissions: contents: read` | Keeps the use case, closes the gap | One more prod-signing workflow to maintain |
| C. Fold it into `build-prod.yml` as a "distribution: none" choice | One prod workflow, one gate to protect. Matches roadmap step 2.19 (reusable workflows) | Bigger change, 2–3 days |

**Recommended: A if nobody uses it (Q9). Otherwise B now and C in Phase 2.** Best practice is to keep as few paths to prod secrets as possible.

## Step 0.5: Keep and harden `trstringer/manual-approval` (corrected)

**Original idea.** Once environment reviewers exist, the environment rule replaces the workflow step.

**Why we propose to keep it.**

* Environment reviewers are not available on our plan (see 0.3b).
* Today the step needs **2** approvals from `tribe-bravo-sre`, `release-engineering`, `samuel-bfi`, `subhanbfi`. An environment rule needs only **1** of up to 6 reviewers. Removing the step would weaken the gate even with Enterprise, unless we accept 1 approver.

**Proposed ticket action.** Create one work ticket for the hardening (option B below). Record in DM-3545 that the step stays. Revisit only if GitHub Enterprise (option C in 0.3) is chosen.

### Options and recommendation (0.5)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Keep the step as it is | No work | Approvers mix people and teams. The token is the 2022 `GH_PAT`. The person who starts the run can approve it |
| B. Harden it: `exclude-workflow-initiator-as-approver: true`, approvers as teams only, and a GitHub App token instead of `GH_PAT`. The action's README says team approvers need a GitHub App token with read access to org members and write access to issues | No self-approval. No long-lived personal token in the prod path | App tokens live 1 hour, so the approval window must stay under 60 minutes, or the job fails |
| C. Replace it with environment required reviewers (needs GitHub Enterprise) | Enforced by GitHub | Only 1 approval. Licence cost |

**Recommended: B.** In Phase 0, only the approval step moves to an App token. `GH_PAT` is used by 7 other workflows here, and maybe by other repos. Replacing it everywhere is a separate ticket (Q11).

## Step 0.6: Scan workflow files for printed secrets (Codacy)

**Why.** Stops the next "Reveal Secret" at review time. This is a main control while we stay on the Team plan.

**Today (20 Oct).**

* No such check in this repo. `.github/scripts/` has only `build-merged-changelog.py`.
* **Codacy is BFI's standard scanner.** "Codacy Static Code Analysis" and "Codacy Diff Coverage" are required checks on `master` and `release*` here. The shared `bfi-base-template` pipelines (`java-pr-pipeline.yaml`, `js-pr-pipeline.yaml`) default to `scanning-tool: codacy` and `container-scanning-tool: codacy` (Codacy CLI v2 container scan).
* **Other repos keep their Codacy tool list in the repo.** 33 repos have a `.codacy.yml` (mostly `exclude_paths`, for example `bravo-agency-app`, also a Flutter app). Several have `.codacy/codacy.yaml` with a tool list, for example `bravo-agent-service`: `lizard`, `opengrep`, `pmd`, `trivy`. This repo has only `.codacy/instructions/review.md`, so its tool setup lives in the Codacy UI.
* **Codacy can scan GitHub Actions files.** Codacy's supported-tools page lists GitHub Actions with static analysis by **Opengrep** and secret detection by **Opengrep** and **Trivy**. Codacy moved from Semgrep to Opengrep in February 2026.
* **Pattern on/off switches are UI-only.** `bravo-backoffice-web-ui` `.codacy/pattern-cleanup-checklist.md` notes that `.codacy.yaml` supports only paths, engines and languages, so individual patterns are toggled in the Codacy UI by a repo admin.

**Tasks.**

1. In Codacy (repo admin): make sure Opengrep and Trivy are on for this repo, including the GitHub Actions patterns. Add `.codacy/codacy.yaml` with the tool list, like `bravo-agent-service`, so the setup is visible in the repo.
2. Test: a test PR with a copy of the old `test.yaml`. Record which Codacy patterns fire.
3. Only if Codacy does not flag the "print a secret with spaces" trick: add `.github/scripts/check-workflow-secrets.sh`. It fails when a `run:` line both prints (`echo`, `printf`, `cat`, `tee`, `>>`) and uses `${{ secrets.` Also flag `sed`/`tr`/`rev`/`base64` applied to a secret, which is how masking was defeated in `test.yaml`.
4. Run that script from a small workflow `workflow-lint.yml` that triggers on every PR with **no** `paths-ignore` (see 0.7). Remove the `test.yaml` copy after the test.

**Acceptance criteria.**

* A PR that adds `echo ${{ secrets.X }}` fails the check.
* A PR that adds `echo "${{ secrets.X }}" | sed 's/./& /g'` fails the check.
* Current workflows on `master` pass (no false alarm).

**Who.** One mobile engineer, plus a Codacy repo admin for the pattern settings. SRE reviews the pattern list.

**Risks.** A grep check can be bypassed by a determined insider. It catches mistakes and makes intent visible in review. That is why 0.3b and `CODEOWNERS` matter too.

### Options and recommendation (0.6)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. **Codacy** with Opengrep and Trivy on for GitHub Actions files, tool list in `.codacy/codacy.yaml`. Plus a small grep step only for the pattern Codacy misses, if any | BFI's standard tool, already a required check, already runs on every PR including workflow-only ones. Findings show in the same place as other code issues. No new vendor | Pattern switches are UI-only. Generic rules may not catch the "spaces between characters" trick, so test with the old `test.yaml` |
| B. Codacy plus a custom Opengrep rule for printing secrets | Everything in one tool | We did not find in Codacy's docs whether it accepts custom Opengrep rules. Ask the Codacy admin or Codacy support |
| C. Codacy plus `zizmor` (open-source GitHub Actions analyser) in a `workflow-lint` job | `zizmor` has Actions-specific audits (`template-injection`, `excessive-permissions`, `unpinned-uses`, `unredacted-secrets`, `artipacked`) | A second scanner next to Codacy. Findings in two places |

**Recommended: A.** Codacy is the standard across BFI repos and is already enforced here. Add the grep step only if the `test.yaml` test shows a gap. Consider B if Codacy supports custom rules. Keep C as an option for later, not Phase 0.

## Step 0.7: Run checks on PRs that change only `.github/**`

**Why.** `pr-pipeline.yml` has `paths-ignore: ".github/**"`. A PR that only changes workflows runs none of our own checks. That is how a workflow like `test.yaml` can arrive without any automated check.

**Today (19 Oct).**

* Codacy is a GitHub App, not a workflow, so it already reports on workflow-only PRs. PRs #1493 and #1502 changed only `.github/` and merged with the required Codacy checks.
* Third-party actions are pinned to commit SHAs since PR #1450 (DM-2600, 7 Oct 2026). Good.
* GitHub-owned actions are still on tags (`actions/checkout@v4`, `@v2`, `setup-java@v3`, `download-artifact@v2`). 42 lines.
* `update-graphify.yaml` (new on 15 Oct) calls a reusable workflow from another repo at `@master`: `bfi-finance/bfi-base-template/.github/workflows/update-graphify.yaml@master`. Whatever lands on that branch runs here.

**Tasks.**

1. New `workflow-lint.yml`, triggered on `pull_request` with no path filter: `actionlint`, the 0.6 grep step if needed, and a SHA-pin check (allow `actions/*` on tags for now, or pin them too, decide in Q10). Security scanning stays in Codacy.
2. Pin the `bfi-base-template` reusable workflow to a commit SHA, or accept `@master` and give that repo's `.github/` the same protection.

**Acceptance criteria.**

* A PR that changes only a workflow file shows the `workflow-lint` check and cannot merge while it fails (add it to the ruleset's required checks).
* `actionlint` passes on `master`, or the known findings are listed in the ticket.

**Who.** One mobile engineer. SRE for the ruleset change.

**Risks.** Making the check required blocks merges if it is flaky. Start as non-required for one week, then make it required.

### Options and recommendation (0.7)

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rely on Codacy only (it already runs on workflow-only PRs) | No new workflow | No `actionlint` (YAML and expression errors), no SHA-pin check, no grep step |
| B. Codacy plus a tiny `workflow-lint.yml`: no path filter, `permissions: contents: read`, no secrets. Runs `actionlint`, the SHA-pin check and the 0.6 grep step if needed. Required after 1 week | Fast and safe. Covers what Codacy does not | One more small workflow |
| C. Option B, plus pin everything to commit SHAs: the 42 GitHub-owned action lines still on tags, and the cross-repo reusable workflow `bfi-base-template/...@master`. Dependabot for `github-actions` keeps the pins fresh | GitHub's guidance: pin to a full commit SHA, and treat reusable workflows like third-party actions | Dependabot PRs to review each week. The `bfi-base-template` pin must be bumped on purpose when the template changes |

**Recommended: C.** Codacy does the security scanning. The small job adds the checks Codacy does not do. The pins stop a moved tag, or a change on another repo's `master`, from running here.

## Exit gate for Phase 0 (proposed update)

The roadmap's exit gate assumed required reviewers. Proposed wording for the session:

* `test.yaml` is gone from every branch.
* `SSH_PRIVATE_KEY` rotated in all 5 environments, old key removed. `BRAVO_GCP_SA_KEY` rotated with SRE, old key deleted.
* `customer_app_prod` and `customer_app_prod_test` accept only `master`, `release-*` and `v*`. Only named people can change `.github/workflows/**`. The default `GITHUB_TOKEN` is read-only.
* Every PR, including workflow-only PRs, runs the secret-echo check.
* Prod builds keep the 2-approval step, with no self-approval. A decision on Enterprise or a separate prod repo is recorded in DM-3545.

## Questions for Wednesday

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Stay on Team with option 0.3-B, or go for Enterprise or a separate prod repo (option 0.3-C)? Who decides, by when? | Engineering manager, SRE | |
| Q2 | Whose account holds the current `SSH_PRIVATE_KEY`? | Mobile squad, org admin | |
| Q3 | Does SRE agree to rotate the org-wide `BRAVO_GCP_SA_KEY` now? Who signs off? | SRE lead | |
| Q4 | Who disabled "Reveal Secret" on 16 Oct? | Repo admins | |
| Q5 | Per-repo deploy keys or one read-only machine user for the git dependencies? | Mobile squad, SRE | |
| Q6 | Which service account and GCP project is behind `BRAVO_GCP_SA_KEY`, and what roles does it hold? | SRE | |
| Q7 | Split a separate Google Play publisher account now, or as a follow-up? | SRE, release manager | |
| Q8 | Add `CODEOWNERS` for `.github/` and "require code owner review" in Phase 0? | Squad lead | |
| Q9 | Does anyone use `build-prod-artifact.yml`? | Release manager, QA | |
| Q10 | Pin GitHub-owned actions (`actions/*`) to SHAs too, or keep tags? (Recommendation: pin) | Mobile squad | |
| Q11 | Whose token is `GH_PAT` (Feb 2022), what scopes does it have, and which other repos use it? | GitHub org admin | |
| Q12 | Who checks the 4 workflows without a `permissions:` block before the default token becomes read-only? | Mobile squad | |
| Q13 | Can SRE bind this repo to the existing `BFI_DEVSECOPS_WIF_PROVIDER` for a new Play-only service account? | SRE | |
| Q14 | Is Play App Signing on for `id.co.bfi.customer`? (If yes, the keystore in CI is only the upload key.) | Release manager | |
| Q15 | Who is the Codacy admin for this repo, and does Codacy accept custom Opengrep rules? | Squad lead | |
| Q16 | Who dispatched `build-prod.yml` from `ci/test-build-prod-android-sdk-2.25.x` on 15 Sep, and can those test runs use `build-prod-test.yml` instead? | Release manager | |

## Evidence

| Fact | How it was checked (19 Oct 2026) |
| --- | --- |
| Workflow disabled 16 Oct | GitHub API `actions/workflows`: state `disabled_manually`, `updated_at` 2026-10-16T14:09 |
| `test.yaml` on 5 branches | GitHub API `contents/.github/workflows/test.yaml?ref=…`, same blob `b20e044f` |
| One run only | GitHub API `actions/workflows/test.yaml/runs`: total 1, run `20612762797`, failure. Log not opened |
| No environment protection | GitHub API `environments`: 0 protection rules, no branch policy, admins can bypass |
| Team plan, private repo | GitHub API `orgs/bfi-finance` plan `team`; repo visibility `private`; GitHub docs "Deployments and environments" |
| Environment rule needs 1 approval | GitHub docs: up to 6 reviewers, only one needs to approve |
| Secret locations and dates | GitHub API secret listings (names and dates only, no values) |
| 51 repos use `BRAVO_GCP_SA_KEY` | GitHub code search `secrets.BRAVO_GCP_SA_KEY` in org `bfi-finance` |
| Ruleset | GitHub API `rulesets/11766362`: `~DEFAULT_BRANCH` and `release*`, PR with 2 approvals, Codacy checks, admin bypass |
| Workflow contents | Sparse clone of `.github/` at `master` @ `4fb4175` |
| Prod build from a test branch | GitHub API runs of `build-prod.yml`: `head_branch` `ci/test-build-prod-android-sdk-2.25.x`, 15 Sep 2026 |
| Default token write, Actions can approve PRs | GitHub API `actions/permissions/workflow` (20 Oct 2026) |
| Codacy is the BFI standard | `bfi-base-template` `java-pr-pipeline.yaml` and `js-pr-pipeline.yaml` (`scanning-tool` default `codacy`); `.codacy.yml` in 33 repos; `.codacy/codacy.yaml` in `bravo-agent-service` |
| Keyless Google sign-in in prod | GitHub code search: `BFI_DEVSECOPS_WIF_PROVIDER` in 27 repos; `bravo-dms-fe` `deploy-prod.yaml` |
| Cloud KMS and Vault | `bravo-terraform` `product/kms/main.tf` (HSM key); `bfi-terraform-selfservice` `devsecops/iam/vault` (Vault unsealed by KMS key `vault-keyring/vault-key`) |
| App signing secrets | Secret names in `customer_app_prod` (names only, no values) |
| `GH_PAT` is an org secret from 15 Feb 2022 | GitHub API organization-secrets listing for the repo (name and date only) |

## Sources for the recommendations

* GitHub, [Secure use reference for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use): pin to a full commit SHA, `CODEOWNERS` on `.github/workflows`, least-privilege `GITHUB_TOKEN`, OIDC instead of long-lived secrets, never use structured data as a secret, same care for reusable workflows.
* GitHub, [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments): required reviewers only for public repos on Free, Pro and Team; up to 6 reviewers, 1 approval needed; prevent self-review; admin bypass.
* GitHub, [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) and [changelog: push rules generally available (Sep 2024)](https://github.blog/changelog/2024-09-10-push-rules-are-now-generally-available-and-updates-to-custom-properties/): "Restrict file paths", for example `.github/workflows/**/*`.
* GitHub, [actions/create-github-app-token](https://github.com/actions/create-github-app-token): `owner`, `repositories`, `permission-*` inputs; tokens expire after 1 hour and are revoked at the end of the job.
* Google Cloud, [Best practices for managing service account keys](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys): avoid user-managed keys, one service account per application, disable before delete, org policy to block key creation.
* [r0adkll/upload-google-play](https://github.com/r0adkll/upload-google-play): `serviceAccountJson` takes the credentials file from `google-github-actions/auth` (Workload Identity Federation).
* [trstringer/manual-approval](https://github.com/trstringer/manual-approval): `exclude-workflow-initiator-as-approver`, team approvers need a GitHub App token, 60-minute limit with App tokens.
* Codacy, [Supported languages and tools](https://docs.codacy.com/getting-started/supported-languages-and-tools): GitHub Actions covered by Opengrep (static analysis) and Opengrep + Trivy (secret detection).
* Google Cloud, [Cloud KMS PKCS #11 library](https://docs.cloud.google.com/kms/docs/reference/pkcs11-library): lets tools that speak PKCS#11, such as Java's `jarsigner`, sign with a key held in KMS.
* [zizmor audits](https://docs.zizmor.sh/audits/): `template-injection`, `excessive-permissions`, `unpinned-uses` (SHA pins for all actions by default), `overprovisioned-secrets`, `unredacted-secrets`, `artipacked`.
