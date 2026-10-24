## Summary

This page replaces the Roadmap on the Square mobile app assessment page. It lists every step of SQUARE plans 01 to 13 in the order we will do them, with a row for each step's Jira ticket and pull request (PR). It follows the BFI customer app's roadmap (Mobile roadmap: step by step), so the three squads use one method.

**Why the order changed.** The assessment's roadmap grouped work by topic. This one groups work by **risk to the field staff who use SQUARE**. SQUARE is an internal app, so a bad release is cheaper to roll back than for GENFI or the BFI app, but the same loop applies: safety net first, one risky change per release, a fast way back.

**One repo, four apps.** SQUARE (`are_tracker/`), GENFI (`agent_tools/`, with MyShaf as its Sharia flavour) and MY BISPRO (`mybispro/`) share one monorepo, one CI setup and 15 shared packages. Most steps are done **once** and live on shared phase pages under Agency apps roadmap: shared phases, linked from this page and from GENFI roadmap: step by step. Only the phases that differ per app (3, 7, 9) have SQUARE-specific pages under this one.

**Three rules shape the order** (same as BFI):

1. **Build the safety net first.** Tests, release tooling, dashboards and the kill switch come before any change to app behaviour (Phases 0 and 1).
2. **Change one risky thing per release, per app.** A SQUARE release carries at most one flagged change or one approved delta.
3. **Every risky change has a fast way back.** A switch flag, or a halted store rollout.

**How to use this page.** Each phase is one Jira epic (shared phases: one epic for the monorepo; per-app phases: one epic per app). Each row is one ticket. "Plan ref" points to the plan page and step, for example "01 §0" = SQUARE plan 01: Security, step 0. "App" says what the row touches: `shared`, `SQUARE`, `GENFI`, `MyShaf`, `MY BISPRO`.

Facts come from `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026) and the 13 SQUARE plan pages.

## How each step stays safe

The impact classes and release rules are the same as on the BFI roadmap (Mobile roadmap: step by step, section "How each step stays safe"):

| Class | What it means | How we undo it |
| --- | --- | --- |
| **A. No app change** | GitHub, CI, docs, dashboards or tests only | Revert the PR or the setting |
| **B. Same behaviour** | Code moves; staff see and send the same things. The parity net proves it | Halt the store rollout and hotfix |
| **C. Flagged change** | New path beside the old one behind a switch flag, default old, rolled out 1% → 10% → 50% → 100% | Flag off |
| **D. Approved delta** | Behaviour is meant to change; signed off first | Kill switch, or halt and hotfix |
| **E. Backend-coupled** | The backend must keep working for old app versions | Backend back to monitor-only |

Two SQUARE-specific points:

* **Internal users, managed devices.** Rollout stages can be shorter (10% → 50% → 100% is enough for most class C steps) and a forced update is possible through MDM (open question 3).
* **Keycloak sign-in.** SQUARE uses `KeycloakAuthStrategy`; the network chain (Phase 4) and e2e login (Phase 1) need a SIT test realm.

## Phases at a glance

| Phase | Goal | Where | Classes | Exit gate | Jira epic |
| --- | --- | --- | --- | --- | --- |
| 0. Close the leak | No workflow prints or uploads a secret; prod builds need an approver | Agency phase 0: Close the leak (shared) | A | Leaky workflows gone, 6 secrets rotated, SQUARE upload key reset, prod environments limited to release refs | |
| 1. Safety net first | Tests, release tooling and guardrails before any app change | Agency phase 1: Safety net first (shared) + SQUARE rows | A | Parity net green on 2 SQUARE releases; staged rollout used once; ratchets live | |
| 2. Seams, same behaviour | Observability, analytics, flag and DI ports behind today's calls | Agency phase 2: Seams with the same behaviour (shared) | B | One SQUARE release at 100% with golden files unchanged | |
| 3. Approved deltas | Privacy and security fixes, one per SQUARE release | SQUARE phase 3: Approved deltas (this page's child) | D, E | Each delta signed off and stable at 100% for 1 release | |
| 4. Network chain | Six auth decorators become one interceptor chain behind `useInterceptorClient` | Agency phase 4: Network chain behind a switch flag (shared) | C, E | Old decorators deleted after 2 releases at 100% per app | |
| 5. Move call sites | Analytics and flag calls move to the ports | Agency phase 5: Move call sites, per app (shared) | B | Direct-call ratchets at 0 for SQUARE | |
| 6. Riverpod 3 alone | Dependency upgrade in a release with nothing else | Agency phase 6: Riverpod 3 upgrade on its own (shared) | B | 1 SQUARE release at 100% with no new provider errors | |
| 7. Pilot: lead and company submission | Domain layer and Notifiers for the two largest features through the parity loop | SQUARE phase 7: Pilot, lead and company submission (this page's child) | C | Old `lead` and `company_submission` paths deleted after 2 releases at 100% | |
| 8. Packages | `lead` as the first feature package; design system `ds_1` → `ds_3` | Agency phase 8: Packages, move only (shared) + SQUARE rows | B | `lead` is its own package; `ds_1` gone | |
| 9. Other features | Same loop for `maintain`, `recruitment`, `profile` and the rest; `collab_form` last | SQUARE phase 9: Other features (this page's child) | C, then B | Every SQUARE feature's old path deleted; `StateNotifier` 0 | |
| 10. Platform | RASP (one vendor, three repos), tokens, Widgetbook | Agency phase 10: Platform (shared) | C, D | Per item | |

Phases 0 and 1 can overlap. From Phase 2 on, a phase starts only when the previous exit gate is met for SQUARE. GENFI and MY BISPRO run the same shared phases on their own release trains.

## Phase 0: Close the leak (shared)

Steps are on Agency phase 0: Close the leak. SQUARE-relevant facts: `are-tracker-deploy-tag-cd-pipeline.yml` decodes the signing keystore and its password file and **uploads them as a workflow artifact** (lines 84–91, 156 runs); `test.yaml` and `debugger.yaml` echo secrets; the SQUARE prod build runs in `agency_prod_are_tracker` with no protection rule (confirm, question 1).

| # | Step | Plan ref | App | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 0.1 | Disable, then delete `test.yaml`, `debugger.yaml`, the "Reveal secret" step in the convent pipeline and the keystore upload in the ARE tracker pipeline | 01 §0 | shared | A | | |
| 0.2 | Rotate `FIREBASE_API_KEY` (SIT), `SSH_PRIVATE_KEY`, `BRAVO_GCP_SA_KEY`, `KEYCLOAK_CLIENT_SECRET`, the prod keystore passwords; **reset the SQUARE upload key through Play App Signing** (the keystore left the runner 156 times) | 01 §0 | shared, SQUARE | A | | |
| 0.3 | Deployment branch and tag rules on `agency_prod_are_tracker`, `agency_prod_agent_tools` and the MY BISPRO prod environment; push ruleset on `.github/workflows/**`; keep the 2-approval step | 01 §0, 02 §3 | shared | A | | |
| 0.4 | Codacy scanning of workflow files, plus a `workflow-lint` job (`actionlint`, artifact-path check for `*.jks`, `*.p12`, `*.mobileprovision`, SHA pins) on every PR with no path filter | 01 §1 | shared | A | | |
| 0.5 | Pass `SHA_256_FINGERPRINT` to every build that leaves a runner (ARE tracker SIT/UAT included); fix the pinning fork | 01 §2 | shared | A (CI) + B (pinning fork) | | |

## Phase 1: Safety net first (shared + SQUARE rows)

Shared steps are on Agency phase 1: Safety net first. SQUARE-only rows:

| # | Step | Plan ref | App | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 1.S1 | Make `Log.e` work: create the logger once at startup and call `.error()` instead of `.debug()`; ask the Datadog owner to turn RUM event processing on for the two SQUARE RUM applications, or remove the RUM SDK until it is paid for | 03 §1, 04 §5 | SQUARE | B (telemetry only) | | |
| 1.S2 | Analytics golden names file: 27 call sites, 8 names built at run time, screen-view names | 04 §1 | SQUARE | A | | |
| 1.S3 | Direct controller tests for `lead` and `company_submission` (7 controller tests exist against 82 controllers) | 05 §4 | SQUARE | A | | |
| 1.S4 | Parity net for `lead` and `company_submission`: goldens of the top screens and home, recorded scrubbed fixtures, `FakeHttpClient`, ledger template and `docs/parity/square-lead.md` | 05 §5 | SQUARE | A | | |
| 1.S5 | e2e journeys in `automation-monorepo` (`square` package): SSO login, lead input, company submission, cancellation review, KPI and incentive view; stable `Semantics` ids; SIT Keycloak test user | 05 §6 | SQUARE | A | | |
| 1.S6 | Play staged rollout and iOS phased release for SQUARE, by hand with a checklist; release health dashboard for the SQUARE RUM app with stop thresholds | from the BFI roadmap 1.3–1.4 | SQUARE | A | | |
| 1.S7 | One Datadog monitor on error rate and crash-free sessions, routed to the squad channel | 03 §5 | SQUARE | A | | |

## Phase 2: Seams with the same behaviour (shared)

Steps are on Agency phase 2: Seams with the same behaviour. SQUARE wiring rows there: `are_tracker/lib/main.dart` registers the observability sinks (03 §4), the analytics adapters with `Analytics.logEvent` as a shim (04 §2), the composition root that replaces the nine inline overrides (13 §1) and the catalogue of the 23 Remote Config fields (11 §2).

## Phase 3: Approved deltas (SQUARE)

Steps are on SQUARE phase 3: Approved deltas. Summary:

| # | Step | Plan ref | Class | Signs off | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 3.1 | Sanitiser before every sink; opaque agent id instead of the NIK for Crashlytics and Firebase user ids | 03 §3, 04 §4 | D | DPO + dashboard owner | | |
| 3.2 | `ConsentState` provider for Datadog and the adapters; PII key denylist | 01 §6, 04 §4 | D | DPO | | |
| 3.3 | Screen-capture guard on OTP, registration (KTP OCR, selfie), personal and tax information, lead input and detail, behind a kill switch | 01 §5 | D | Product | | |
| 3.4 | Compile-time feature flags become code defaults or Remote Config: `FEATURE_FLAG_NON_REGISTERED_MAINTAIN` to Remote Config; delete `FEATURE_FLAG_NEW_COLLAB_FORM` and `FEATURE_FLAG_NEW_LOAN_CALCULATOR` from CI | 11 §3 | D | Squad lead | | |
| 3.5 | Secrets out of the app: review the prod dart-defines; the backend stops relying on any of them; Play Integrity and App Attest verdicts enforced for SQUARE | 01 §4 | E | Security + backend | | |
| 3.6 | RUM actions for visit report submitted, lead submitted, company submission submitted (once RUM processing is on) | 04 §5 | D (new data to Datadog) | Product | | |

## Phase 4: Network chain behind a switch flag (shared)

Steps are on Agency phase 4: Network chain behind a switch flag. GENFI goes first; SQUARE follows with `KeycloakAuthStrategy` behind `useInterceptorClient` (06 §3), then the Krakend variant folds into one client (06 §4), then the cohort rollout (06 §5). SQUARE signs in through Keycloak, so the double-refresh race in the `sso` and `keycloak` packages is SQUARE's main risk.

## Phase 5: Move call sites, per app (shared)

Steps are on Agency phase 5: Move call sites, per app. SQUARE rows there: `<feature>_events.dart` per feature (`lead`, `recruitment`, `maintain`, `performance`, …) and the 27 call sites, one feature per PR (04 §3); the 23 Remote Config fields read through the catalogue and the hand-written mapping deleted (11 §2).

## Phase 6: Riverpod 3 upgrade on its own (shared)

Steps are on Agency phase 6: Riverpod 3 upgrade on its own. One shared PR; **three releases**, one per app. SQUARE numbers: 82 `StateNotifier` classes, 158 `valueOrNull` uses, 103 `static final provider`.

## Phase 7: Pilot, lead and company submission (SQUARE)

Steps are on SQUARE phase 7: Pilot, lead and company submission. Summary:

| # | Step | Plan ref | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- |
| 7.1 | Layer rules, `domain-purity` (strict) and `dto-in-presentation` (ratchet) in the checker; pure core barrel (shared with GENFI) | 08 §1 | A | | |
| 7.2 | Ledgers for `lead` and `company_submission`; flag `useNewLeadFlow` | 08 §2, 11 §4 | A | | |
| 7.3 | Slice 1: lead detail and leads tracker list on the new path, copying the `cancellation_review` shape | 08 §3 | C | | |
| 7.4 | Move the rules: `company_submission_prospect_step.dart` (1,195 lines), `collateral_asset_info_controller.dart` (804), `no_deal_recalculation_controller.dart` into domain use cases | 08 §4, 09 §3 | C | | |
| 7.5 | Cohort rollout 1% → 10% → 50% → 100% watching crash-free sessions, error rate and the lead funnel | 08 §5 | C | | |
| 7.6 | Flip and delete the old controllers, use cases and the flag | 08 §5 | B | | |

## Phase 8: Packages, move only (shared + SQUARE rows)

Steps are on Agency phase 8: Packages, move only. SQUARE rows there: `lead` as the first feature package (10 §3), the `ds_1` → `ds_3` inventory and migration in the 195 files, one feature per PR behind the same switch flags as the Layering rollouts (12 §1, §3).

## Phase 9: Other features (SQUARE)

Steps are on SQUARE phase 9: Other features. Order: `maintain` (visit report), `recruitment`, `profile` (imported by 35 files), then the rest; `collab_form` last, together with GENFI (08 §6, 09 §3–4, 10 §5, 13 §4).

## Phase 10: Platform (shared)

Steps are on Agency phase 10: Platform. SQUARE note: the RASP proof of concept also runs on a SQUARE build; one vendor, one contract, three repos (01 §7).

## Rollout and rollback

Same as the BFI roadmap: the flag owner decides each step up; the mobile on-call can flip back without asking; target 15 minutes from alert to flag change; halt the Play rollout and pause the iOS phased release if the build is suspected; every flip gets a ledger note. SQUARE-specific: managed devices allow a forced update, so the minimum supported version can move faster than for GENFI (open question 3).

## Mapping to the plan pages

| Plan | Steps | Phases |
| --- | --- | --- |
| 01 Security | §0 → 0.1–0.3; §1 → 0.4; §2 → 0.5; §3 → 2 (shared); §4 → 3.5; §5 → 3.3; §6 → 3.1–3.2; §7 → 10 | 0, 2, 3, 10 |
| 02 CI/CD | §1, §2, §4, §5, §7 → 1 (shared); §3 → 0.3; §6 → 2 (shared) | 0, 1, 2 |
| 03 Logging and crashes | §1 → 1.S1; §2, §4 → 2 (shared); §3 → 3.1; §5 → 1.S7 | 1, 2, 3 |
| 04 Analytics wrapper | §1 → 1.S2; §2 → 2 (shared); §3 → 5; §4 → 3.1–3.2; §5 → 1.S1, 3.6 | 1, 2, 3, 5 |
| 05 Testing | §1–3 → 1 (shared); §4 → 1.S3; §5 → 1.S4; §6 → 1.S5; §7 → 7, 9 | 1, 7, 9 |
| 06 Networking | §1 → 1 (shared); §2 → 2 (shared); §3–6 → 4 (shared) | 1, 2, 4 |
| 07 Lint and guardrails | §1–2 → 1 (shared); §3 → 2 (shared); §4 → 10 | 1, 2, 10 |
| 08 Layering | §1 → 7.1; §2 → 7.2; §3–5 → 7.3–7.6; §6 → 9 | 7, 9 |
| 09 State management | §1–2 → 6 (shared); §3 → 7.4, 9; §4 → 9 | 6, 7, 9 |
| 10 Repo layout | §1–2 → 1 (shared); §3 → 8 (SQUARE row); §4 → 8 (shared); §5 → 9 | 1, 8, 9 |
| 11 Feature flags | §1 → 2 (shared); §2 → 2, 5; §3 → 3.4; §4 → 7.2 | 2, 3, 5, 7 |
| 12 Design system | §1, §3 → 8 (SQUARE rows); §2 → 2 (shared); §4 → 10 | 2, 8, 10 |
| 13 Dependency injection | §1–2 → 2 (shared); §3 → 7.4, 9; §4 → 9 | 2, 7, 9 |

## Open questions

1. **Who owns the SQUARE roadmap and each epic?** The Agency squad with a named tech lead for SQUARE.
2. **Stop thresholds** for the SQUARE release health dashboard, and the RUM processing cost decision (RUM is not processed for SQUARE today).
3. **Forced update through MDM:** can SQUARE set a minimum version, and who decides?
4. **Go or no-go at each rollout stage:** feature owner alone, or with QA?
5. **SIT Keycloak test realm and user** for e2e login.
6. **Datadog owner for the agency apps** (03 §5).
