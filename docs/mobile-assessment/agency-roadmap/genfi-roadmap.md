## Summary

This page replaces the Roadmap on the Genfi mobile app assessment page. It lists every step of GENFI plans 01 to 13 in the order we will do them, with a row for each step's Jira ticket and pull request (PR). It follows the BFI customer app's roadmap (Mobile roadmap: step by step), so the three squads use one method.

**Why the order changed.** The assessment's roadmap grouped work by topic: now, quick wins, architecture, platform. This one groups work by **risk to the agents who use the app**. GENFI ships to external agents who do not update on a schedule, so each step must reach them in a way that cannot break the app, and that we can undo quickly.

**One repo, four apps.** GENFI (`agent_tools/`, with MyShaf as its Sharia flavour), SQUARE (`are_tracker/`) and MY BISPRO (`mybispro/`) share one monorepo, one CI setup and 15 shared packages. So most steps are done **once**. Those steps live on shared phase pages under Agency apps roadmap: shared phases, linked from this page and from SQUARE roadmap: step by step. Only the phases that differ per app (3, 7, 9) have GENFI-specific pages under this one.

**Three rules shape the order** (same as BFI):

1. **Build the safety net first.** Tests, release tooling, dashboards and the kill switch come before any change to app behaviour (Phases 0 and 1).
2. **Change one risky thing per release, per app.** A GENFI release carries at most one flagged change or one approved delta.
3. **Every risky change has a fast way back.** A switch flag, or a halted store rollout.

**How to use this page.** Each phase is one Jira epic (shared phases: one epic for the monorepo; per-app phases: one epic per app). Each row is one ticket. "Plan ref" points to the plan page and step, for example "01 §0" = GENFI plan 01: Security, step 0. "App" says what the row touches: `shared` (monorepo, CI or a shared package), `GENFI`, `MyShaf`, `SQUARE`, `MY BISPRO`.

Facts come from `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026) and the 13 GENFI plan pages.

## How each step stays safe

The impact classes and release rules are the same as on the BFI roadmap (Mobile roadmap: step by step, section "How each step stays safe"). In short:

| Class | What it means | How we undo it |
| --- | --- | --- |
| **A. No app change** | GitHub, CI, docs, dashboards or tests only | Revert the PR or the setting |
| **B. Same behaviour** | Code moves; agents see and send the same things. The parity net proves it | Halt the store rollout and hotfix |
| **C. Flagged change** | New path beside the old one behind a switch flag, default old, rolled out 1% → 10% → 50% → 100% | Flag off |
| **D. Approved delta** | Behaviour is meant to change; signed off first | Kill switch, or halt and hotfix |
| **E. Backend-coupled** | The backend must keep working for old app versions | Backend back to monitor-only |

Two GENFI-specific points:

* **Agents update slowly.** GENFI has no forced-update dialog today. Class E steps must assume months of old versions in the field (open question 3).
* **Three apps, one dependency change.** A shared-package change ships in three separate releases (GENFI, SQUARE, MY BISPRO). Each app's release is watched on its own.

## Phases at a glance

| Phase | Goal | Where | Classes | Exit gate | Jira epic |
| --- | --- | --- | --- | --- | --- |
| 0. Close the leak | No workflow prints or uploads a secret; prod builds need an approver | Agency phase 0: Close the leak (shared) | A | Leaky workflows gone, 6 secrets rotated, SQUARE upload key reset, prod environments limited to release refs | |
| 1. Safety net first | Tests, release tooling and guardrails before any app change | Agency phase 1: Safety net first (shared) + GENFI rows | A | Parity net green on 2 GENFI releases; staged rollout used once; ratchets live | |
| 2. Seams, same behaviour | Observability, analytics, flag and DI ports behind today's calls | Agency phase 2: Seams with the same behaviour (shared) | B | One GENFI release at 100% with golden files unchanged | |
| 3. Approved deltas | Privacy and security fixes, one per GENFI release | GENFI phase 3: Approved deltas (this page's child) | D, E | Each delta signed off and stable at 100% for 1 release | |
| 4. Network chain | Six auth decorators become one interceptor chain behind `useInterceptorClient` | Agency phase 4: Network chain behind a switch flag (shared) | C, E | Old decorators deleted after 2 releases at 100% per app | |
| 5. Move call sites | Analytics and flag calls move to the ports | Agency phase 5: Move call sites, per app (shared) | B | Direct-call ratchets at 0 for GENFI | |
| 6. Riverpod 3 alone | Dependency upgrade in a release with nothing else | Agency phase 6: Riverpod 3 upgrade on its own (shared) | B | 1 GENFI release at 100% with no new provider errors | |
| 7. Pilot: calculator and prospect | Domain layer and Notifiers for the two largest features through the parity loop | GENFI phase 7: Pilot, calculator and prospect (this page's child) | C | Old calculator and prospect paths deleted after 2 releases at 100% | |
| 8. Packages | `prospect` as the first feature package; design system to `ds_3` | Agency phase 8: Packages, move only (shared) + GENFI rows | B | `prospect` is its own package; `ds_2` gone | |
| 9. Other features | Same loop for `prospect_pbf`, `convent_registration`, `target_performance` and the rest; `collab_form` last | GENFI phase 9: Other features (this page's child) | C, then B | Every GENFI feature's old path deleted; `StateNotifier` 0 | |
| 10. Platform | RASP (one vendor, three repos), tokens, Widgetbook | Agency phase 10: Platform (shared) | C, D | Per item | |

Phases 0 and 1 can overlap. From Phase 2 on, a phase starts only when the previous exit gate is met for GENFI. SQUARE and MY BISPRO run the same shared phases on their own release trains.

## Phase 0: Close the leak (shared)

Steps are on Agency phase 0: Close the leak. GENFI-relevant facts: `agent-tools-convent-deploy-tag-cd-pipeline.yml` prints `FIREBASE_API_KEY` on every GENFI tag push (162 runs); `test.yaml` and `debugger.yaml` echo secrets; prod builds for `agent_tools` run in `agency_prod_agent_tools` with no protection rule (confirm, question 1).

| # | Step | Plan ref | App | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 0.1 | Disable, then delete `test.yaml`, `debugger.yaml`, the "Reveal secret" step in the convent pipeline and the keystore upload in the ARE tracker pipeline | 01 §0 | shared | A | | |
| 0.2 | Rotate `FIREBASE_API_KEY` (SIT), `SSH_PRIVATE_KEY`, `BRAVO_GCP_SA_KEY`, `KEYCLOAK_CLIENT_SECRET`, the prod keystore passwords; reset the SQUARE upload key through Play App Signing | 01 §0 | shared | A | | |
| 0.3 | Deployment branch and tag rules on `agency_prod_agent_tools`, `agency_prod_are_tracker` and the MY BISPRO prod environment; push ruleset on `.github/workflows/**`; keep the 2-approval step | 01 §0, 02 §3 | shared | A | | |
| 0.4 | Codacy scanning of workflow files, plus a `workflow-lint` job (`actionlint`, artifact-path check for `*.jks`, `*.p12`, `*.mobileprovision`, SHA pins) on every PR with no path filter | 01 §1 | shared | A | | |
| 0.5 | Pass `SHA_256_FINGERPRINT` to every build that leaves a runner; fix the pinning fork (no `Authorization` header to native code, remove the `print`) | 01 §2 | shared | A (CI) + B (pinning fork) | | |

## Phase 1: Safety net first (shared + GENFI rows)

Shared steps (toolchain, checks on every PR, build numbers, symbol uploads, coverage gate, harness, shared-package tests, lint set, architecture ratchet, dead weight) are on Agency phase 1: Safety net first. GENFI-only rows:

| # | Step | Plan ref | App | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 1.G1 | Make `DatadogLog.e` work: one logger at startup, error level with stack trace, then Crashlytics. Enable Crashlytics for the Sharia flavour or record why not | 03 §1 | GENFI, MyShaf | B (telemetry only) | | |
| 1.G2 | Analytics golden names file: the 5 enum events and screen-view names | 11 §1 | GENFI | A | | |
| 1.G3 | Parity net for `calculator` and `prospect`: goldens of the top screens, recorded fixtures, `FakeHttpClient`, ledger template | 04 §4 | GENFI | A | | |
| 1.G4 | Characterisation table for the calculator rules (inputs → today's outputs), the oracle for Phase 7 | 07 §2 | GENFI | A | | |
| 1.G5 | e2e journeys for GENFI in `automation-monorepo`: register, prospect input, calculator, reserve lead; stable `Semantics` ids | 04 §5 | GENFI | A | | |
| 1.G6 | Play staged rollout and iOS phased release for GENFI, by hand with a checklist; release health dashboard for the GENFI RUM app with stop thresholds | from the BFI roadmap 1.3–1.4 | GENFI | A | | |
| 1.G7 | One Datadog monitor per app on error rate and crash-free sessions, routed to the squad channel; name the Datadog owner | 03 §5 | GENFI, MyShaf | A | | |

## Phase 2: Seams with the same behaviour (shared)

Steps are on Agency phase 2: Seams with the same behaviour. GENFI wiring rows there: `agent_tools/lib/main.dart` registers the observability sinks (03 §4), the analytics adapters (11 §2), the composition root (13 §1) and the flag catalogue (10 §2).

## Phase 3: Approved deltas (GENFI)

Steps are on GENFI phase 3: Approved deltas. Summary:

| # | Step | Plan ref | Class | Signs off | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- |
| 3.1 | Sanitiser before every sink; drop `nik_marketing` from the Crashlytics keys | 03 §3, 01 §6 | D | DPO | | |
| 3.2 | `ConsentState` provider for Datadog and the adapters; PII key denylist | 01 §6, 11 §4 | D | DPO | | |
| 3.3 | Fix the `proudct` event key | 11 §3 | D | Dashboard owner | | |
| 3.4 | Screen-capture guard on OTP, registration (KTP OCR, selfie), personal and tax information, prospect input and detail, behind a kill switch | 01 §5 | D | Product | | |
| 3.5 | Compile-time feature flags become code defaults: jailbreak detection on, proxy off; delete `FEATURE_FLAG_NEW_*` from CI | 10 §3 | D | Squad lead | | |
| 3.6 | Secrets out of the app: review the 21 prod dart-defines; backend stops relying on any of them; `DEVICE_INTEGRITY_URL` for GENFI prod, integrity check for GENFI not only MyShaf | 01 §4 | E | Security + backend | | |

## Phase 4: Network chain behind a switch flag (shared)

Steps are on Agency phase 4: Network chain behind a switch flag. GENFI is the **first app** behind `useInterceptorClient` (05 §3: `OtpAuthStrategy` from the existing repository code, wired in `agent_tools/lib/main.dart`), then the Krakend, chat-gateway and non-auth variants fold into one client (05 §4), then the cohort rollout (05 §5).

## Phase 5: Move call sites, per app (shared)

Steps are on Agency phase 5: Move call sites, per app. GENFI rows there: typed events for the 5 enum values and the 4 call sites (11 §3), the GENFI catalogue of 20 + 10 Remote Config keys (10 §2), MyShaf events and RUM (11 §5).

## Phase 6: Riverpod 3 upgrade on its own (shared)

Steps are on Agency phase 6: Riverpod 3 upgrade on its own. One shared PR; **three releases**, one per app. GENFI numbers: 96 `StateNotifier` classes, 180 `valueOrNull` uses, 104 `static final provider`.

## Phase 7: Pilot, calculator and prospect (GENFI)

Steps are on GENFI phase 7: Pilot, calculator and prospect. Summary:

| # | Step | Plan ref | Class | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- |
| 7.1 | Layer rules, `domain-purity` (strict) and `dto-in-presentation` (ratchet, 239) in the checker; pure core barrel | 07 §1 | A | | |
| 7.2 | Ledgers for `calculator` and `prospect`; flags `useNewCalculatorFlow`, `useNewProspectFlow` | 07 §2, 10 §4 | A | | |
| 7.3 | Slice 1: `calculator` domain (`Quote`, `Tenor`, `DownPayment`, `Installment`), rules as pure use cases, new notifier beside the old controller | 07 §3, 08 §3 | C | | |
| 7.4 | `prospect` slices: `loan_info`, `collateral`, `input`, `detail`, `list`, `confirmation`, `reserve_lead`, then convent and PBF variants; reads of `calculator` and `common` through `*_api` readers | 07 §4, 13 §3 | C | | |
| 7.5 | Cohort rollout: calculator first, prospect when calculator is past 50% | 07 §5 | C | | |
| 7.6 | Flip and delete both old paths and flags | 07 §5 | B | | |

## Phase 8: Packages, move only (shared + GENFI rows)

Steps are on Agency phase 8: Packages, move only. GENFI rows there: `prospect` as the first feature package with `prospect_api` (09 §3), finish `ds_2` → `ds_3` in the 154 files (12 §1).

## Phase 9: Other features (GENFI)

Steps are on GENFI phase 9: Other features. Order: `prospect_pbf` and `calculator_pbf`, `convent_registration`, `target_performance`, `account_information`, `personal_information`, then the rest; split `common` into `*_api` readers as importers move; `collab_form` last, together with SQUARE (07 §6, 08 §3–4, 09 §5, 13 §4).

## Phase 10: Platform (shared)

Steps are on Agency phase 10: Platform. GENFI note: the RASP proof of concept runs on a prod-like GENFI build, the largest app, and reuses the BFI vendor shortlist (01 §7).

## Rollout and rollback

Same as the BFI roadmap: the flag owner decides each step up; the mobile on-call can flip back without asking; target 15 minutes from alert to flag change; halt the Play rollout and pause the iOS phased release if the build is suspected; every flip gets a ledger note. GENFI-specific: agents who do not update keep old code, so class E steps keep working for old versions until a minimum version is set (open question 3).

## Mapping to the plan pages

| Plan | Steps | Phases |
| --- | --- | --- |
| 01 Security | §0 → 0.1–0.3; §1 → 0.4; §2 → 0.5; §3 → 2 (shared); §4 → 3.6; §5 → 3.4; §6 → 3.1–3.2; §7 → 10 | 0, 2, 3, 10 |
| 02 CI/CD | §1, §2, §4, §5, §7 → 1 (shared); §3 → 0.3; §6 → 2 (shared) | 0, 1, 2 |
| 03 Logging and crashes | §1 → 1.G1; §2, §4 → 2 (shared); §3 → 3.1; §5 → 1.G7 | 1, 2, 3 |
| 04 Testing | §1–3 → 1 (shared); §4 → 1.G3; §5 → 1.G5; §6 → 7, 9 | 1, 7, 9 |
| 05 Networking | §1 → 1 (shared); §2 → 2 (shared); §3–6 → 4 (shared) | 1, 2, 4 |
| 06 Lint and guardrails | §1–2 → 1 (shared); §3 → 2 (shared); §4 → 10 | 1, 2, 10 |
| 07 Layering | §1 → 7.1; §2 → 1.G4, 7.2; §3–5 → 7.3–7.6; §6 → 9 | 1, 7, 9 |
| 08 State management | §1–2 → 6 (shared); §3 → 7.3–7.4, 9; §4 → 9 | 6, 7, 9 |
| 09 Repo layout | §1–2 → 1 (shared); §3 → 8 (GENFI row); §4 → 8 (shared); §5 → 9 | 1, 8, 9 |
| 10 Feature flags | §1 → 2 (shared); §2 → 2, 5; §3 → 3.5; §4 → 7.2 | 2, 3, 5, 7 |
| 11 Analytics wrapper | §1 → 1.G2; §2 → 2 (shared); §3 → 3.3, 5; §4 → 3.2; §5 → 5 | 1, 2, 3, 5 |
| 12 Design system | §1 → 8 (GENFI row); §2 → 2 (shared); §3 → 8 (shared); §4 → 10 | 2, 8, 10 |
| 13 Dependency injection | §1–2 → 2 (shared); §3 → 7.4, 9; §4 → 9 | 2, 7, 9 |

## Open questions

1. **Who owns the GENFI roadmap and each epic?** The Agency squad with a named tech lead.
2. **Stop thresholds** for the GENFI release health dashboard (crash-free, error rate, load time, prospect and reserve-lead funnels).
3. **Minimum supported app version for agents.** There is no forced-update dialog. Class E steps (3.6, 4) need a policy.
4. **Go or no-go at each rollout stage:** feature owner alone, or with QA?
5. **MyShaf:** does it get its own release health dashboard and cohort, or ride with GENFI? (Same binary, different flavour.)
6. **Datadog owner for the agency apps** (03 §5), and the RUM processing cost decision.
