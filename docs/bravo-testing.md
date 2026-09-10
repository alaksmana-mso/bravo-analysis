# Testing: what CI covers, and why nothing says "this change hits NDF2W"

**Audience:** Engineering, QA, release managers on Squad LOS and Squad Scoring and Underwriting
**Findings under test:** Business logic cannot be unit-tested effectively. Tests and CI cannot say whether a change affects NDF4W underwriting or NDF2W. Validation is applied only after the service is already serving traffic. "Still running" is treated as "healthy". And the role of a nightly end-to-end run in proving the contract.

**Method.** Test inventory and build configuration from the `bravo-bpm-service` checkout at `v2.93.43` (`src/test/java`, `pom.xml`, `makefile`), as recorded in [compare-architecture.md §3.10](compare-architecture.md). Production evidence measured live in Datadog `us5` on 2026-09-10: BPMN parse warnings on `env:prod service:prod-ms-bpm`, the Synthetics inventory, the CI Visibility inventory, and the RUM and monitor findings carried over from [bravo-observability.md](bravo-observability.md). Production volume shares are from [workflow-gap.md §8](workflow-gap.md).

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [Inventory](#1-inventory-1457-test-files-4-of-which-run-a-process) · **[Where the business logic actually is](#2-where-the-business-logic-actually-is--and-why-mockito-cannot-reach-it)** · **[NDF4W vs NDF2W](#3-no-test-can-say-this-change-hits-ndf2w--and-one-bridge-makes-it-worse)** · [Validation happens in production](#4-validation-happens-in-production-38198-times-a-week) · [The health assumption](#5-not-5xx--healthy) · [The nightly run that does not exist](#6-the-nightly-e2e-that-does-not-exist) |
| **3. What to do** | [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| Business logic cannot be unit-tested effectively | **True, and for a sharper reason than in LORA.** 776 of 1,457 test files are pure Mockito, and Mockito can reach Java. But Bravo's routing logic is not Java: it is `conditionExpression` strings inside 53 BPMN XML files, a six-column database selector, and a per-application jsonb on/off matrix. **Those three are data, not code, and no unit test in the repository executes any of them.** |
| Tests and CI cannot distinguish an NDF4W-underwriting change from an NDF2W one | **True, and materially worse than the LORA equivalent.** Product identity is expressed in five places at once. And `ndf2w.bpmn` bridges into the *unified* underwriting sub-process, so a change to unified underwriting reaches NDF2W — **248,685 applications over 90 days** — with nothing in the build saying so. |
| Validation is applied only after the service is serving traffic | **Confirmed, and measurable.** All 53 BPMN and 3 DMN files are auto-deployed and parsed at Spring Boot startup. The engine emitted **38,198 `ENGINE-09004` model-parse warnings in production in 7 days**, naming real modelling defects in real files. There is no parse or lint gate before that. |
| "Still running" is treated as "healthy" | **Confirmed in a Bravo-specific form: "not 5xx" is treated as healthy.** Every success-rate monitor filters `http.status_code:5*`. A 404 storm of 748,686 a week across 69% of surveyor sessions is, by that definition, a healthy service. |
| A nightly end-to-end run proves the contract | **There is no such run.** The org has **8 Synthetics tests, all DNS and SSL health checks**, and **zero CI pipeline events for any repository**. Nothing exercises a Bravo loan journey on a schedule. LORA's nightly partner-E2E is mostly red — but it exists, asserts a terminal condition, and can therefore be fixed. |
| The 1,457-file suite is a safety net for the orchestration | **No. Four test files deploy and run a Camunda process**, one of them against a production BPMN. There is no test of retry exhaustion, incident creation, escalation across a `callActivity`, or the forced-termination path. |
| Coverage is gated | **No gate exists.** `pom.xml` configures JaCoCo `report` and no `check`; there is no threshold. The `makefile` passes `-Dspring-boot.run.profiles`, which surefire ignores, so the profile the tests believe they are running under is not the one they get. |

**The through-line:** Bravo's suite tests the Java it can reach and does not touch the XML, the configuration tables or the engine, which is where the loan's behaviour is decided. The result is a build that can be green for a change that alters the routing of 94% of production volume.

---

## 1. Inventory: 1,457 test files, 4 of which run a process

| | Count |
|---|---:|
| Test files, `src/test/java` | 1,457 |
| Pure Mockito unit tests | 776 |
| Tests that **deploy and execute a Camunda process** | **4** (one against a production BPMN, `unified-anti-fraud-engine.bpmn`) |
| H2 "parse tests" asserting BPMN structure | a handful |
| End-to-end walks from application start to go-live | **0** |
| Tests of retry exhaustion, incident creation, cross-`callActivity` escalation, forced termination | **0** |
| Coverage threshold | **none** — JaCoCo `report` only, no `check` goal |
| Test tooling present in `pom.xml` and effectively unused | `camunda-bpm-assert`, `camunda-bpm-process-test-coverage`, `camunda-bpm-mockito` |

The suite is large, well-maintained and conventional. Nothing in it is bad. The problem is what it is pointed at: **0.27% of the test files exercise the orchestration engine**, and the engine is what decides what happens to a loan.

The three Camunda testing libraries in the pom are the tell. Somebody knew this was the right way to test a BPMN system, added the dependencies, and the practice never took hold — the same shape as LORA's `lora-super-test`, which has 150 scenario tests and no CI runner.

**A structural difference worth noting in Bravo's favour:** LORA has 608 test files across 13 repositories with four repos at zero and `lora-process-sdk` carrying no `.github/workflows/` at all. Bravo has one repository, one build, and everything in it runs. Bravo's problem is coverage of the right thing; LORA's is that some repositories are not covered at all. Bravo's is the better problem to have.

---

## 2. Where the business logic actually is — and why Mockito cannot reach it

"Business logic cannot be unit-tested" is the complaint. In LORA it was graded *overstated*, because LORA's rules live in Go preconditions that `PreConditionIsMet(nil, data)` can execute directly — 97 test files already do. In Bravo the complaint holds, and the reason is that a large part of the decision surface is **not in Java at all**.

| Where a routing decision lives | Form | Can a unit test execute it? |
|---|---|---|
| BPMN gateway conditions — 137 exclusive gateways in `ndf4w.bpmn` alone; ≈1.3 `conditionExpression` per service task in both generations | JUEL strings inside XML, e.g. `environment.getProperty('setting.feature.config.featDF2W') == 'true' && applicationWorkflowSelectorType == "OPTION_DF2W"` | **No.** Only by deploying the process and running it — 4 test files do this |
| Which activities run for this application | `WorkflowProductConfig(productId, type, customerType, userType, businessType, riskType)` → `WorkflowMasterConfig` → per-application jsonb matrix `{"CI": {"PilotBranchCheckActivity": [true,false]}}` | **No.** It is rows in PostgreSQL, shipped as Flyway data migrations |
| The skip gate itself | `BaseActivity.execute()` reads the matrix and runs or no-ops | Yes in principle; the *matrix content* is still data |
| Which BPMN process starts for a product | YAML map `productId → key` in `application.yaml:1364`, with a Java override for RO | Partly — and the map contains four keys that are **not deployed processes** ([compare-architecture.md Appendix C](compare-architecture.md)) |
| Approval chain rules | `BaseUnderwritingApprovalServiceImpl`, 4,604 lines, behind feature flags (`featFinalApproverRoleOnReject`, `featSingleApproverRejectedRole`, …) | Yes — this part is genuinely Java and genuinely testable |
| Terminal vs transient error, and the degrade decision | 50 `customErrorHandle` implementations invoked on the **last** retry, e.g. anti-fraud degrades to `BYPASS` | Yes for the handler; **no** for "does the engine actually reach the last attempt", which needs the engine |

So the accurate statement is not *"business logic cannot be tested"* but:

> **Bravo's Java is testable and largely tested. Bravo's decisions are in XML, YAML and database rows, and none of those is executed by any test in the build.**

That has a specific, expensive consequence. The `customErrorHandle` framework contains at least one credit-policy decision — bypassing anti-fraud after three failed attempts keeps the pipeline moving. Whether that path is ever reached depends on `failedJobRetryTimeCycle`, which is a string attribute on a BPMN element (186 declarations, 30 distinct values, including 5 `PT4M` cycles with no repeat count, which do not do what their author intended). **No test asserts that any activity's retry policy is what the modeller meant**, and the one that degrades anti-fraud is the one where being wrong is a credit-risk event rather than an outage.

---

## 3. No test can say "this change hits NDF2W" — and one bridge makes it worse

This is the finding with the largest production exposure, and it is the same complaint LORA graded **True** for itself. Bravo's version is worse for two independent reasons.

### Reason one: product identity is in five places

| Mechanism | Where |
|---|---|
| Numeric literals | `Application.isNDF4W() { return productId == 1L; }` — 18 such predicates |
| YAML process-key map | `application.yaml:1364`, plus an RO override in `ApplicationServiceImpl.java:752-762` |
| Six-column DB selector | `WorkflowProductConfig` → `WorkflowMasterConfig` → per-application jsonb matrix |
| Java factories | 31 of them |
| Gateway string expressions | inside all 53 BPMN files |

A change to any one of these can alter the behaviour of one product, several, or all. Adding DF2W Sharia (product 15) touched **all five**, behind per-product feature flags. There is no artefact in the build — no test name, no tag, no coverage report dimension — that maps a diff to the set of products it affects. A reviewer's only tool is knowing all five mechanisms.

LORA's answer to the same problem is structural rather than tested: product families have separate document schemas, separate workers and separate task queues, so a change to `…/ndf2w` cannot reach NDF4W by construction. LORA still cannot tell you *which* product a shared-planner change affects — that is its True verdict — but it has fewer ways to get it wrong.

### Reason two: the legacy-to-unified bridge

`ndf2w.bpmn` calls into the **unified underwriting sub-process**. And no `callActivity` in the codebase sets `camunda:calledElementBinding`, so every child resolves to the **latest deployed version at call time**.

Put those two facts together with the production volume split:

| Generation | Applications, 90 days to 2026-09-09 | Share |
|---|---:|---:|
| Legacy monoliths — NDF2W | 248,685 | ~73% |
| Legacy monoliths — NDF4W + RO | 71,995 | ~21% |
| **Unified spine** — DF4W only | **18,806** | **5.5%** |
| DF2W — fully configured | **0** | 0% |

> **A change to `unified-underwriting-*.bpmn` — the "new", 5.5%-of-volume generation — is picked up by in-flight NDF2W loans at their next call activity. That is 73% of BFI's origination volume, reached through a file whose name says it belongs to the other generation, with no migration plan, no version pin and no test.**

The four Camunda-executing test files do not cover this path. Neither does anything else. This is the most consequential untested edge in either platform and it is invisible in the diff.

---

## 4. Validation happens in production, 38,198 times a week

The LORA complaint was that validation is "only JSON Schema, applied after the worker is already serving traffic". Bravo has no schema registry at all, so the equivalent question is: *when is a process model checked?*

**At pod startup, in production.** Spring Boot auto-deploys every BPMN and DMN resource on the classpath — there is no `deployment-resource-pattern` narrowing it — and the engine parses and versions each changed definition as it boots. That parse is the validation.

It is not silent. Measured on `env:prod service:prod-ms-bpm`, 7 days:

| Deployed version | `ENGINE-09004` parse warnings |
|---|---:|
| `v2.92.45` | 24,513 |
| `v2.93.53` | 13,685 |
| **Total** | **38,198** |

A representative line, captured live:

```
status:  warn
version: v2.93.53
message: ENGINE-09004 Warnings during parsing:
  * Exclusive Gateway 'Gateway_X_KYC_Verified' has outgoing sequence flow
    'Flow_Condition_KYC_Verified' without condition which is not the default flow.
    We assume it to be the default flow, but it is bad modeling practice,
    better set the default flow in your gateway.
  | resource unified-kyc-check.bpmn
@activityName: KYC Check
@processDefinitionId: 544e3ea0-ab85-11f1-ba59-16deca89b476
```

Read that carefully. The engine is telling the team, in production, that a gateway on the **KYC path** has an unconditional outgoing flow that Camunda is *guessing* is the default. That is a routing decision being resolved by an engine assumption rather than by the model. The warning names the file. It has been repeating for at least two deployed versions.

**Three things follow.**

1. **The model is validated after deployment, not before it.** Every one of these warnings is available at build time — `camunda-bpm-assert` and a parse test would surface them in seconds — and none of them is a build failure today.
2. **The count is a boot-frequency artefact, and that is also informative.** 38,198 warnings in a week across two versions means pods are restarting often and re-parsing all 53 files each time. The *distinct* warning set is small; the volume tells you about pod churn.
3. **Nothing consumes them.** No monitor matches `ENGINE-09004`. The warnings land in the same log stream as the 525,181 error lines a week ([bravo-observability.md §3](bravo-observability.md)) and are invisible.

The honest comparison: LORA's `docFieldCheck` panics the **worker at startup** if a schema path is missing, which is late but is at least fatal and per-deployment. Bravo's equivalent check emits a warning, assumes a default, and serves traffic.

---

## 5. "Not 5xx" = healthy

The assumption named in the finding — *"still running" is treated as "healthy"* — is LORA's failure mode: about half of LORA's loans never reach a terminal status while producing zero errors and zero failed attempts, and every signal reads healthy.

Bravo does not have that failure class. Its BPMN checkpoints fail fast into an incident and park ([compare-architecture.md §3.6](compare-architecture.md)), so a wedged Bravo loan becomes a visible ticket rather than an invisible running workflow. That is a real advantage and it is why Bravo's stuck-application rate is *measurable* at ≈0.44% while LORA's silent half went unnoticed for months.

**Bravo's version of the same mistake is one layer up.** Every health signal it owns is defined as the absence of a 5xx:

```
(hits{service:prod-ms-bpm} - hits{service:prod-ms-bpm, http.status_code:5*})
  / hits{service:prod-ms-bpm} < 99
```

So:

| Reality | What the health model reports |
|---|---|
| 748,686 HTTP 404s a week on the Surveyor Platform, 266,767 of them from one endpoint hitting **54,350 of 79,090 sessions** | healthy |
| 8,533 `401 Unauthorized` from the IAM permission endpoint, ~1,200/day, 1.07 errors per trace — a broad auth defect | healthy |
| 20,802 outbound errors a week, **none of them 5xx** | healthy |
| ~4,750 activity-level engine failures a day, `One Obligor Check` at 5,583 in 48 hours | healthy — nothing reads `@activityName` |
| Eight monitors permanently in `Alert`; six that cannot fire | — |

Evidence and queries in [bravo-observability.md](bravo-observability.md) §4–6.

**Stated as a testing finding:** Bravo's release gate is *it deployed and it is not returning 500*. That is the same category of statement as *the workflow is still Running*, and it is wrong for the same reason — it defines health as the absence of the one failure mode the system does not have.

---

## 6. The nightly E2E that does not exist

The role a nightly end-to-end run plays for LORA is to prove the Digital Partnership contract: 11 partner journeys through DP → LORA, with a terminal assertion (the agreement number comes back on DP tracking status). LORA's own [testing.md](../../lora-workspace/docs/production-findings/testing.md) grades that run harshly — 59 of 83 web cases have never passed in 31 nightly runs, and the API run fails the same 199 cases every night — but the run exists, asserts, and is fixable.

**Bravo has no equivalent, and this was checked three ways.**

| Surface | What is there |
|---|---|
| Datadog **Synthetics** | **8 tests in the entire org**: 4 DNS checks (`bfi.co.id`, `bfidigital.id`, and the two Bravo microservice domains) and 4 SSL certificate checks (`microservices.prod.bravo.bfi.co.id`, the Sharia equivalent, `e-self.bfi.co.id`, `sso.bfi.co.id`). **Zero browser tests. Zero multi-step API tests. Nothing that creates an application.** |
| Datadog **CI Visibility** | **Zero pipeline events for any repository** in 30 days — Bravo or LORA. No build, test or deploy telemetry reaches this org at all. |
| Repository | 4 test files execute a Camunda process; no start-to-go-live walk exists ([§1](#1-inventory-1457-test-files-4-of-which-run-a-process)) |

So the continuous evidence that a Bravo loan can still be originated end to end is: **the production ticket queue.** `Surveyor Platform - Release reject` at 315 tickets in August, growing 4.8× since January, is the regression detector.

That is the finding. It is not that Bravo's nightly run is red — it is that the question "can a loan still get from submission to go-live on NDF2W this morning?" has no automated answer, and the eight Synthetics checks confirm only that DNS resolves and the certificate is valid.

**One caveat in Bravo's favour.** Bravo's volume is its own smoke test: 76,446 applications in August means a total break in the main path is visible within minutes through the ticket queue and the latency monitors. That works for outages. It does not work for the failure Bravo actually has — a slow, product-specific, 4xx-shaped degradation that grows 82% over eight months while volume falls.

---

## Recommended actions

Ordered by what would have caught something. Items 1–3 are days of work each.

1. **Pin `calledElementBinding` on every `callActivity`, or write the one test that proves the bridge (S–M, highest value).** 56 call activities, none version-pinned, and `ndf2w.bpmn` calls into unified underwriting. Either pin the binding so a unified edit cannot reach 73% of volume mid-flight, or add a Camunda process test that starts an NDF2W instance and asserts which underwriting definition version it enters. Today neither exists.
2. **Fail the build on `ENGINE-09004` (S).** The warnings are already produced; they are simply produced in the wrong place. A parse test over all 53 BPMN files with `camunda-bpm-assert` — the dependency is already in the pom — turns 38,198 production warnings a week into a red build. Start by fixing the KYC gateway the engine is currently guessing about.
3. **Add a 4xx clause to the release health gate (S).** "Not 5xx" is not health. At minimum, per-resource 404 and 401 rates on the four surveyor endpoints and the IAM permission call. See [bravo-observability.md](bravo-observability.md) recommendation 2.
4. **Build one end-to-end process test per generation (M).** Two tests: an NDF2W instance and a unified DF4W instance, each walked from start to go-live with upstreams stubbed, asserting the terminal status and the set of activities executed. `camunda-bpm-assert` and `camunda-bpm-mockito` are already dependencies. Two tests would cover the paradigm's entire happy path, which is currently covered by none.
5. **Test the retry and degrade policies (M).** Assert that `failedJobRetryTimeCycle` is a valid `Rn/PTn` on every service task — the 5 bare `PT4M` cycles are a latent defect — and add a test that drives an activity to last-attempt and asserts which `customErrorHandle` fires. The anti-fraud `BYPASS` path is a credit-policy decision reached by an exception handler and nothing verifies when.
6. **Make the product blast radius visible in the diff (M).** Tag every test with the products it covers and emit, per PR, the set of `productId`s reachable from the changed BPMN files, config rows and factories. A reviewer should not have to know five discrimination mechanisms to know whether a change reaches NDF2W.
7. **Turn on a coverage gate, and correct the `makefile` (S).** JaCoCo `check` with a floor at the current level, ratcheting. Fix `-Dspring-boot.run.profiles`, which surefire ignores — the tests are not running under the profile the build claims.
8. **Add one Synthetics multi-step API test for the origination journey (S–M).** Not a replacement for a process test; a canary. Today the only continuous evidence that Bravo works is a support-ticket queue.
9. **Send CI events to Datadog (S).** Zero pipeline events exist for either platform, so no one can answer "is the build getting slower, flakier, redder". This is a configuration change and it benefits both teams.

---

## Plan: 30, 60, 90 days

Nine recommendations, phased against ~25 person-days a month of Squad S&U time (the allocation set by [bravo-people.md](bravo-people.md) recommendation 4).

**Sequencing rule for this document: investigate before touching anything that reaches in-flight loans.** Recommendation 1 is the highest-value item here and the most dangerous to rush — unpinned `callActivity` binding affects **248,685 NDF2W applications per 90 days**. It is therefore read-only in month 1, a decision in month 2, and a change in month 3. Nothing else in this plan alters in-flight behaviour at all.

**Shared with other documents.** Recommendation 1 is also [bravo-delivery.md](bravo-delivery.md) rec 6, and recommendation 3 is also [bravo-observability.md](bravo-observability.md) rec 2. Both are phased identically in all documents — do them once.

### Days 0–30 — look, and start reporting

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **`calledElementBinding` investigation — read-only.** Enumerate all 56 `callActivity` elements; map which children an NDF2W instance reaches; quantify the exposure of the `ndf2w.bpmn` → unified-underwriting bridge | 1 | S&U | 5 d | A written exposure note. **No code change this phase** |
| **Send CI pipeline events to Datadog** | 9 | Platform | 2 d | Zero pipeline events becomes a build-health number, for both platforms |

### Days 31–60 — put the gates in

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Fail the build on `ENGINE-09004`.** A parse test over all 53 BPMN files with `camunda-bpm-assert` — already in the pom — and fix the KYC gateway whose default flow the engine is currently guessing | 2 | S&U | 4 d | 38,198 production parse warnings a week become a red build |
| **Add the 4xx clause to the release health gate.** Per-resource 404 and 401 rates, at minimum on the four surveyor endpoints and the IAM permission call | 3 | Platform/SRE | 3 d | "Not 5xx = healthy" is retired. A release that 404s two-thirds of sessions fails the gate |
| **Coverage gate + `makefile` fix.** JaCoCo `check` at the current floor, ratcheting; correct `-Dspring-boot.run.profiles`, which surefire ignores | 7 | S&U | 2 d | Coverage cannot fall, and tests run under the profile the build claims |
| **Synthetics multi-step API test for origination** — a canary, not a replacement for a process test | 8 | QA | 3 d | Something other than the support-ticket queue notices that origination broke |
| **`calledElementBinding` decision** — pin, or accept in-flight child migration deliberately, with a migration plan | 1 | S&U + EM | 2 d | A recorded decision. Implementation next phase |

### Days 61–90 — prove the journey, then make the change

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Two end-to-end process tests** — one NDF2W instance, one unified DF4W, start to go-live with upstreams stubbed, asserting terminal status and the executed activity set | 4 | S&U + QA | 10 d | "Can a loan still get from submission to go-live?" is answered every build, per generation. This is also the harness the next two items need |
| **Implement the binding decision** — pin `calledElementBinding` on all 56 call activities, with the migration plan agreed in phase 2 | 1 | S&U | 10 d | A unified sub-process redeploy can no longer silently change the path of in-flight NDF2W loans |
| **Retry-policy validation (part 1).** Assert every `failedJobRetryTimeCycle` is a valid `Rn/PTn` — the five bare `PT4M` cycles are a latent defect | 5 | S&U | 4 d | No service task carries a retry policy that does not do what its author intended |

### Deferred, with triggers

| Deferred | Rec | Why | Trigger |
|---|---|---|---|
| **Degrade-path tests (part 2)** — drive an activity to last attempt, assert which `customErrorHandle` fires; the anti-fraud `BYPASS` is a credit-policy decision reached by an exception handler | 5 | Needs the process-test harness built above | After the E2E process tests land |
| **Product blast radius in the diff** — tag tests by product; emit reachable `productId`s per PR | 6 | 8 days, and much cheaper once job-executor tracing ([bravo-observability.md](bravo-observability.md) rec 8) and the flag registry ([bravo-delivery.md](bravo-delivery.md) rec 5) exist | Q2 week 1 |

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| `calledElementBinding` pinned | A change to unified underwriting cannot silently alter the path of 248,685 in-flight NDF2W applications. Migration becomes a decision instead of a side effect. |
| `ENGINE-09004` fails the build | The KYC gateway that Camunda is currently guessing the default flow for is fixed in a PR, not discovered in a log stream nobody reads. |
| 4xx in the health gate | A release that starts 404-ing on two-thirds of surveyor sessions is caught at deploy, not by a rising ticket category. |
| Two end-to-end process tests | "Can a loan still get from submission to go-live?" has an automated answer for both generations, every build. |
| Retry and degrade tested | Nobody discovers by incident that anti-fraud has been bypassing after three failures, or that five retry cycles never repeat. |
| Product blast radius in the diff | A reviewer sees "this PR reaches NDF2W, NDF4W and RO" on the PR itself, and the five discrimination mechanisms stop being tribal knowledge. |
| CI events flowing | Build health becomes a number for both platforms instead of an impression. |

---

## Related

- [bravo-observability.md](bravo-observability.md) — the production signals these gates would consume
- [bravo-delivery.md](bravo-delivery.md) — what shipping a change into Bravo costs once it passes
- [bravo-people.md](bravo-people.md) §6 — why a Bravo change is fewer artefacts than a LORA one, and what that buys
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.10, §3.11 — the test inventory and in-flight versioning in code terms
- [workflow-gap.md](workflow-gap.md) §8 — the 5.5% / 94% volume split between the two generations
- LORA [testing.md](../../lora-workspace/docs/production-findings/testing.md) — the same questions asked of the other platform
