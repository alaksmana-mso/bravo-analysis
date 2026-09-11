# Testing: what CI covers, and why nothing says "this change hits NDF2W"

**Audience:** Engineering, QA, release managers on Squad LOS and Squad Scoring and Underwriting
**Findings under test.** Business logic cannot be unit-tested effectively. Tests and CI cannot say whether a change affects NDF4W underwriting or NDF2W. Validation only happens after the service is already serving traffic. "Still running" is treated as "healthy". And finally, the role a nightly end-to-end run plays in proving the contract.

**Method.** The test inventory and build configuration come from **four** Bravo LOS repositories:

- `bravo-bpm-service` at `v2.93.43` — `src/test/java`, `pom.xml`, `makefile`, as recorded in [compare-architecture.md §3.10](compare-architecture.md)
- `bravo-e2e-test` — see [§6](#6-the-journey-suite-bravo-built-and-stopped-running)
- the three operator consoles `bravo-surveyor-console` `v2.83.12`, `bravo-operation-console` `v2.80.18` and `bravo-underwriting-console` `v1.63.13`, measured 2026-09-10 — `src/`, `package.json`, `makefile`, `vite.config.ts`, `.github/workflows/`, `sonar-project.properties`

Production evidence was measured live in Datadog `us5` on 2026-09-10: BPMN parse warnings on `env:prod service:prod-ms-bpm`, the Synthetics inventory, and the CI Visibility inventory. The RUM and monitor findings carry over from [bravo-observability.md](bravo-observability.md). Production volume shares come from [workflow-gap.md §8](workflow-gap.md).

> **Correction, 2026-09-11.** The first version of this document concluded that no Bravo journey suite existed. It had checked three surfaces: Datadog Synthetics, Datadog CI Visibility, and `bravo-bpm-service` itself. **It did not check sibling repositories, and there is one.** `squads/<squad>/bravo-e2e-test` holds 595 Cypress/Cucumber `.feature` files and four CI workflows.
>
> [§6](#6-the-journey-suite-bravo-built-and-stopped-running) is rewritten around what is actually there. The conclusion moved in an unexpected direction: the corrected finding is *worse* for Bravo than the original, not better.

> **Amended 2026-09-10.** We have now measured the `bravo-e2e-test` corpus for *content*, not just existence. That covered keyword distribution, assertion density split by API and UI tier, scenario length, outline parameterisation, step-vocabulary size, widget coupling and orphaned glue.
>
> Two things changed. First, the blanket claim "the suite does not assert" is **too harsh**. Its 130 API feature files assert on 87% of their `Then` steps. So the skill is present, and the defect is confined to the 465 UI files.
>
> Second, the triage in [recommendation 12](#recommended-actions) needs a **style gate in front of it** ([§6.1](#61-if-the-349-surveyor-files-are-being-re-pointed-fix-the-style-first)). Re-pointing these files without one just reproduces the defect. The style argument, and the product/QA ritual that produces files like this, live in [people.md](../../lora-workspace/docs/production-findings/people.md#writing-gherkin-for-the-bfi-loan-business).

> **Correction, 2026-09-10 — the scope of "Bravo" in this document was too narrow, for the second time.**
> Team Bravo pointed out that the Bravo LOS estate includes three operator-console repositories — **`bravo-operation-console`, `bravo-surveyor-console` and `bravo-underwriting-console`** — plus a Jira project, **`LN`, Surveyor & Verificator ([board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703))**. This pack had counted none of them.
>
> We verified it. The three repositories hold **763,861 lines of source, and 829 test files totalling 188,389 lines of test code**. They released within three days of this measurement. And **their pull-request pipelines run unit tests as a blocking job.** This is the objection in its strongest form, and it is correct.
>
> Two claims below were wrong as a result. *"Bravo has one repository, one build"* ([§1](#1-inventory-2286-test-files-across-four-repositories-4-of-which-run-a-process)) was false. And the headline test-file count understated Bravo by 57%. The real figure is **2,286 test files across four repositories, not 1,457 in one.**
>
> The correction is not all good for Bravo. Coverage in all three consoles is **measured and not enforced**. The thresholds sit at 0% for surveyor and operation, and 1% for underwriting. And `jest-coverage-thresholds-bumper` is declared and never invoked — the same shape as `camunda-bpm-mockito`.
>
> None of this reaches the orchestration tier. The BPMN routing logic still has no test that executes it. See [§1.1](#11-the-console-tier-what-actually-gates-a-bravo-front-end-change).
>
> **The pack contradicted itself about this.** [bravo-observability.md §7](bravo-observability.md) and [bravo-delivery.md](bravo-delivery.md) both measure "the four production Bravo LOS consoles" in RUM, at 2.4 million errors a week. So those consoles were visible in the runtime analysis and missing from the code and test analysis. The same three repositories were being measured in production and left out of the inventory.

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [Inventory](#1-inventory-2286-test-files-across-four-repositories-4-of-which-run-a-process) · **[The console tier](#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)** · **[Where the business logic actually is](#2-where-the-business-logic-actually-is--and-why-mockito-cannot-reach-it)** · **[NDF4W vs NDF2W](#3-no-test-can-say-this-change-hits-ndf2w--and-one-bridge-makes-it-worse)** · [Validation happens in production](#4-validation-happens-in-production-38198-times-a-week) · [The health assumption](#5-not-5xx--healthy) · **[The journey suite Bravo stopped running](#6-the-journey-suite-bravo-built-and-stopped-running)** · **[fix the Gherkin style first](#61-if-the-349-surveyor-files-are-being-re-pointed-fix-the-style-first)** |
| **3. The strategy** | **[Layers L0–L8](#7-a-test-strategy-for-bravo--layers-l0l8)** · [Where the boundary is](#71-where-bravos-test-boundary-is) · [The nine layers](#72-the-nine-layers) · [Regression T1–T12](#73-the-regression-suite-t1t12) · [Negative N0–N12](#74-the-negative-suite-n0n12) · [The budget](#75-the-budget-400-cases-must-not-mean-400-process-runs) |
| **4. What to do** | [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| Business logic cannot be unit-tested effectively | **True, and for a sharper reason than in LORA.** 776 of 1,457 test files are pure Mockito, and Mockito can reach Java. But Bravo's routing logic is not Java: it is `conditionExpression` strings inside 53 BPMN XML files, a six-column database selector, and a per-application jsonb on/off matrix. **Those three are data, not code, and no unit test in the repository executes any of them.** |
| Tests and CI cannot distinguish an NDF4W-underwriting change from an NDF2W one | **True, and materially worse than the LORA equivalent.** Product identity is expressed in five places at once. And `ndf2w.bpmn` bridges into the *unified* underwriting sub-process, so a change to unified underwriting reaches NDF2W — **248,685 applications over 90 days** — with nothing in the build saying so. |
| Validation is applied only after the service is serving traffic | **Confirmed, and measurable.** All 53 BPMN and 3 DMN files are auto-deployed and parsed at Spring Boot startup. The engine emitted **38,198 `ENGINE-09004` model-parse warnings in production in 7 days**, naming real modelling defects in real files. There is no parse or lint gate before that. |
| "Still running" is treated as "healthy" | **Confirmed in a Bravo-specific form: "not 5xx" is treated as healthy.** Every success-rate monitor filters `http.status_code:5*`. A 404 storm of 748,686 a week across 69% of surveyor sessions is, by that definition, a healthy service. |
| A nightly end-to-end run proves the contract | **Corrected 2026-09-11 — one exists, and it cannot fail.** Bravo has a **595-file Cypress/Cucumber suite** in a sibling repo (`bravo-e2e-test`) and four GitHub Actions workflows, one scheduled weekly. But every step in the scheduled workflow ends `\|\| true`, so **the run can never go red**; it covers **10 of 595** files; and the repo has been frozen since **2023-11-21**. LORA's nightly is mostly red, which is bad. Bravo's is permanently green by construction, which is worse. **And even if it ran: 57% of the `Then` steps in its 465 UI feature files are pure clicking and typing** — though its 130 API feature files assert on 87% of theirs, so the skill exists and the defect is confined to the UI tier ([§6](#6-the-journey-suite-bravo-built-and-stopped-running)). |
| The 1,457-file suite is a safety net for the orchestration | **No. Four test files deploy and run a Camunda process**, one of them against a production BPMN. There is no test of retry exhaustion, incident creation, escalation across a `callActivity`, or the forced-termination path. |
| Coverage is gated | **No gate exists.** `pom.xml` configures JaCoCo `report` and no `check`; there is no threshold. The `makefile` passes `-Dspring-boot.run.profiles`, which surefire ignores, so the profile the tests believe they are running under is not the one they get. |

**The through-line.** Bravo's suite tests the Java it can reach. It does not touch the XML, the configuration tables or the engine. Those are where the loan's behaviour is decided. The result is a build that can be green for a change that alters the routing of 94% of production volume.

---

## 1. Inventory: 2,286 test files across four repositories, 4 of which run a process

| | Count |
|---|---:|
| Test files, `bravo-bpm-service` `src/test/java` | 1,457 |
| Pure Mockito unit tests | 776 |
| Tests that **deploy and execute a Camunda process** | **4** (one against a production BPMN, `unified-anti-fraud-engine.bpmn`) |
| H2 "parse tests" asserting BPMN structure | a handful |
| End-to-end walks from start to go-live, **in this repo** | **0** |
| Tests of retry exhaustion, incident creation, cross-`callActivity` escalation, forced termination | **0** |
| Coverage threshold | **none** — JaCoCo `report` only, no `check` goal |
| Test tooling in `pom.xml`, by actual use | `camunda-bpm-assert` 13.0.0 — **used in 7 test files**; `camunda-bpm-process-test-coverage-junit5` — imported in 4; **`camunda-bpm-mockito` 5.15.0 — declared and never imported once: a dead dependency** |
| *In the sibling repo* `bravo-e2e-test`: Cypress/Cucumber `.feature` files | **595** (28,268 steps) — frozen 2023-11-21, see [§6](#6-the-journey-suite-bravo-built-and-stopped-running) |
| Test files, three operator consoles (Vitest + Testing Library) | **829** — surveyor 286, underwriting 441, operation 102 |
| Lines of test code in those consoles | **188,389** against 763,861 lines of source |
| Console coverage **enforced** | **none** — thresholds are 0% (surveyor, operation) and 1% (underwriting); `jest-coverage-thresholds-bumper` declared and never invoked |
| Console unit tests **blocking a PR** | **yes, all three** — `unit-test` / `static-analysis` runs `make unit-test-and-report`, no `\|\| true`, and `compile_code` `needs:` it ([§1.1](#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)) |
| *In the sibling repo* `bravo-e2e-test`: Cypress/Cucumber `.feature` files | **595** (28,268 steps) — frozen 2023-11-21, see [§6](#6-the-journey-suite-bravo-built-and-stopped-running) |
| **Bravo LOS total** | **2,286 test files across four repositories** |

The suite is large, well maintained and conventional. Nothing in it is bad. The problem is where it is pointed. **0.27% of the test files exercise the orchestration engine**, and the engine is what decides what happens to a loan.

The three Camunda testing libraries in the pom are the tell, and the detail sharpens it. `camunda-bpm-assert` is genuinely used, in 7 files. `camunda-bpm-mockito` was added and **never imported once**. So somebody knew this was the right way to test a BPMN system and added the dependencies. The practice never took hold. That is the same shape as LORA's `lora-super-test`, which has 150 scenario tests and no CI runner.

**A structural difference in Bravo's favour. Restated, because the first version of it was false.**

It used to read: *"Bravo has one repository, one build, and everything in it runs."* In fact Bravo has **four** repositories in the LOS spine, and one of them, `bravo-e2e-test`, is frozen.

What survives is the comparison of totals and coverage gaps. **Bravo has 2,286 test files across four repositories, against LORA's 608 across 13.** LORA has four repositories with zero tests, and `lora-process-sdk` has no `.github/workflows/` at all. Every Bravo repository that is not frozen runs its tests on every pull request.

So Bravo's problem is covering the right thing. LORA's problem is that some repositories are not covered at all. Bravo's is still the better problem to have, and the corrected numbers widen the gap rather than narrowing it.

**The qualifier that keeps this honest.** 829 of those 2,286 files are console component tests. And none of the 2,286 executes a BPMN routing decision. So volume moved in Bravo's favour. [§2](#2-where-the-business-logic-actually-is--and-why-mockito-cannot-reach-it) and [§3](#3-no-test-can-say-this-change-hits-ndf2w--and-one-bridge-makes-it-worse) are untouched by it.


---

## 1.1 The console tier: what actually gates a Bravo front-end change

The three operator consoles are where the surveyor, operation and underwriting staff do their work. They are the same three applications that emit **2.37 million of the 2.41 million RUM errors a week** in [bravo-observability.md §7](bravo-observability.md). They are not small, and they are not dormant.

| | `bravo-surveyor-console` | `bravo-operation-console` | `bravo-underwriting-console` |
|---|---:|---:|---:|
| Version at read time | `v2.83.12` | `v2.80.18` | `v1.63.13` |
| Source files / LOC | 1,812 / 306,670 | 1,506 / 207,825 | 1,748 / 249,366 |
| Test files / test LOC | 286 / 63,810 | 102 / 21,885 | **441 / 102,694** |
| Storybook stories | 20 | 0 | 33 |
| CI workflows | 9 | 9 | 10 |
| Commits, last 12 months | 1,636 | 1,205 | 1,493 |
| Distinct human authors, last 12 months | 20 | 17 | 8 |
| First commit | 2021-12-22 | 2022-01-25 | 2022-07-15 |
| Last commit | 2026-09-08 | 2026-09-08 | 2026-09-07 |

**The pull-request pipeline is a real gate. It is the strongest testing artefact in the Bravo estate.** In all three repositories, `pr-pipeline.yaml` or `pull-request-pipeline.yml` runs `lint-code` → `unit-test` (or `static-analysis`) → `compile_code`. The test job executes `make unit-test-and-report`, which is `yarn test:coverage`. And `compile_code` declares `needs: [unit-test, …]`. There is **no `|| true` and no `continue-on-error`** anywhere in the 28 workflow files. So a failing unit test blocks the merge.

That is worth saying plainly. This document is otherwise hard on Bravo's CI. And it is the exact opposite of the `OPERATION_PLATFORM.yml` cron in [§6](#6-the-journey-suite-bravo-built-and-stopped-running), where every step ends `|| true` so the job cannot fail. **Both patterns exist in the same estate.** The consoles got the discipline. The journey suite did not.

**Three qualifiers, all verified, and they matter.**

1. **Coverage is measured, not enforced.** In the surveyor and operation consoles, `vite.config.ts` sets `thresholds: {statements: 0, branches: 0, functions: 0, lines: 0}`. In underwriting, `vitest.pipeline.config.ts` sets all four to `1` — one percent. Coverage is computed, written to `coverage/lcov.info` and shipped to SonarQube. No number can fail the build. So the gate proves that *the tests that exist still pass*. It does not stop coverage falling.
2. **`jest-coverage-thresholds-bumper` is a dead dependency.** It is declared in `bravo-underwriting-console/package.json`, and it appears in no script, no `makefile` target and no workflow. Its whole purpose is to ratchet thresholds upward as coverage improves. Somebody intended enforcement, and it never landed. **That is the same shape as `camunda-bpm-mockito` in [§1](#1-inventory-2286-test-files-across-four-repositories-4-of-which-run-a-process): declared, never imported.** Two independent teams, two dead quality dependencies, one cause.
3. **SonarQube scans but does not block.** Every `sonar-scanner` call omits `-Dsonar.qualitygate.wait=true`. So the scan publishes and the job carries on, whatever the gate says. Snyk *does* block, at `--severity-threshold=high`.

**What this tier does not do.** These are component and hook tests against `happy-dom`, with `axios-mock-adapter` at the HTTP boundary. They assert that a React tree renders and behaves, given a mocked response.

**None of them crosses into `ms-bpm`. None executes a BPMN gateway, a DMN table or a product-matrix flag.** Those are the three places [§2](#2-where-the-business-logic-actually-is--and-why-mockito-cannot-reach-it) shows Bravo's routing decisions actually live.

So the console suites answer "does the UI work" well. They say nothing about "does this change hit NDF2W", which is this document's question. They leave the [L0–L8 strategy](#7-a-test-strategy-for-bravo--layers-l0l8) unchanged. But **L7, the console contract layer, should be re-scoped.** It assumed a console tier with no test infrastructure to build on. There is 188,389 lines of it.
---

## 2. Where the business logic actually is — and why Mockito cannot reach it

The complaint is "business logic cannot be unit-tested". For LORA we graded it *overstated*, because LORA's rules live in Go preconditions that `PreConditionIsMet(nil, data)` can execute directly, and 97 test files already do. For Bravo the complaint holds. The reason is that a large part of the decision surface is **not in Java at all**.

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

That has a specific and expensive consequence. The `customErrorHandle` framework contains at least one credit-policy decision: bypassing anti-fraud after three failed attempts keeps the pipeline moving.

Whether that path is ever reached depends on `failedJobRetryTimeCycle`. That is a string attribute on a BPMN element. There are 186 declarations with 30 distinct values, including 5 `PT4M` cycles with no repeat count, which do not do what their author intended.

**No test asserts that any activity's retry policy is what the modeller meant.** And the one that degrades anti-fraud is the one where being wrong is a credit-risk event, not an outage.

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

A change to any one of these can alter the behaviour of one product, several products, or all of them. Adding DF2W Sharia, product 15, touched **all five**, behind per-product feature flags.

Nothing in the build maps a diff to the set of products it affects. There is no test name, no tag and no coverage-report dimension that does it. A reviewer's only tool is knowing all five mechanisms.

LORA's answer to the same problem is structural rather than tested. Product families have separate document schemas, separate workers and separate task queues. So a change to `…/ndf2w` cannot reach NDF4W by construction. LORA still cannot tell you *which* product a shared-planner change affects — that is its True verdict. But it has fewer ways to get this wrong.

### Reason two: the legacy-to-unified bridge

`ndf2w.bpmn` calls into the **unified underwriting sub-process**. And no `callActivity` in the codebase sets `camunda:calledElementBinding`. So every child resolves to the **latest deployed version, at call time**.

Put those two facts together with the production volume split:

| Generation | Applications, 90 days to 2026-09-09 | Share |
|---|---:|---:|
| Legacy monoliths — NDF2W | 248,685 | ~73% |
| Legacy monoliths — NDF4W + RO | 71,995 | ~21% |
| **Unified spine** — DF4W only | **18,806** | **5.5%** |
| DF2W — configured, **in UAT / pen test, not released** | **0** | 0% |

> **A change to `unified-underwriting-*.bpmn` — the "new", 5.5%-of-volume generation — is picked up by in-flight NDF2W loans at their next call activity. That is 73% of BFI's origination volume, reached through a file whose name says it belongs to the other generation, with no migration plan, no version pin and no test.**

The four Camunda-executing test files do not cover this path. Neither does anything else. This is the most consequential untested edge in either platform and it is invisible in the diff.

---

## 4. Validation happens in production, 38,198 times a week

The LORA complaint was that validation is "only JSON Schema, applied after the worker is already serving traffic". Bravo has no schema registry at all. So the equivalent question is this: when does anything check a process model?

**At pod startup, in production.** Spring Boot auto-deploys every BPMN and DMN resource on the classpath. No `deployment-resource-pattern` narrows it. The engine then parses and versions each changed definition as it boots. That parse is the validation.

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

Read that carefully. In production, the engine is telling the team that a gateway on the **KYC path** has an unconditional outgoing flow, and that Camunda is *guessing* it is the default. So an engine assumption is resolving a routing decision, not the model. The warning names the file. And it has been repeating for at least two deployed versions.

**Three things follow.**

1. **The model is validated after deployment, not before.** Every one of these warnings is available at build time. `camunda-bpm-assert` plus a parse test would surface them in seconds. None of them fails a build today.
2. **The count is an artefact of how often pods boot, and that is informative too.** 38,198 warnings in a week across two versions means pods restart often, and re-parse all 53 files each time. The *distinct* warning set is small. The volume tells you about pod churn.
3. **Nothing reads them.** No monitor matches `ENGINE-09004`. The warnings land in the same log stream as the 525,181 error lines a week ([bravo-observability.md §3](bravo-observability.md)), where they are invisible.

The honest comparison. LORA's `docFieldCheck` panics the **worker at startup** if a schema path is missing. That is late, but it is at least fatal, and it happens per deployment. Bravo's equivalent check emits a warning, assumes a default, and serves traffic.

---

## 5. "Not 5xx" = healthy

The finding names an assumption: *"still running" is treated as "healthy"*. That is LORA's failure mode. About half of LORA's loans never reach a terminal status. They produce zero errors and zero failed attempts, and every signal reads healthy.

Bravo does not have that failure class. Its BPMN checkpoints fail fast into an incident and park ([compare-architecture.md §3.6](compare-architecture.md)). So a wedged Bravo loan becomes a visible ticket, not an invisible running workflow. That is a real advantage. It is why Bravo's stuck-application rate is *measurable*, at about 0.39%, while LORA's silent half went unnoticed for months.

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

**Stated as a testing finding.** Bravo's release gate is *it deployed, and it is not returning 500*. That is the same kind of statement as *the workflow is still Running*. And it is wrong for the same reason. It defines health as the absence of the one failure mode the system does not have.

---

## 6. The journey suite Bravo built, and stopped running

For LORA, a nightly end-to-end run proves the Digital Partnership contract. It runs 11 partner journeys through DP into LORA, with a terminal assertion: the agreement number comes back on DP tracking status.

LORA's own [testing.md](../../lora-workspace/docs/production-findings/testing.md) grades that run harshly. 59 of 83 web cases have never passed in 31 nightly runs, and the API run fails the same 199 cases every night. But the run exists, it asserts, and it can be fixed.

**Bravo's equivalent exists too.** It is not in `bravo-bpm-service`, which is why the first version of this document missed it. It sits in a sibling repository, checked out twice under different squads:

| | `squads/<squad>/bravo-e2e-test` |
|---|---|
| Harness | Cypress + `@badeball/cypress-cucumber-preprocessor` |
| Feature files | **595** |
| Gherkin steps (`Given`/`When`/`Then`/`And`/`But`) | **28,268** |
| History | 600 commits, 46 authors, 334 in 2022 and 266 in 2023 |
| **Last commit** | **2023-11-21** |
| CI workflows | 4 — `OPERATION_PLATFORM.yml`, `LOS_E2E.yml`, `NDF4W_E2E.yml`, `LMS_E2E.yml` |
| Scenario tags | `@BLOS-T3424`, `@B4WH-T808` — the **same Zephyr scheme** as LORA's `@BL-T<n>` |

**And it is pointed at exactly the right place.** Feature files by area:

| Area | Files | |
|---|---:|---|
| **`surveyor-platform`** | **349** | the console behind `Surveyor Platform - Release reject` — 28.4% of Bravo's ticket load — and the 404 storm in [§5](#5-not-5xx--healthy) |
| `agency` | 114 | |
| `operation-platform` | 55 | |
| `repeat-order` | 39 | |
| `lms` | 22 | |
| `ndf2w` | 11 | 73% of production volume |
| `ndf4w` | 3 | |
| `unsecured` | 2 | |

So the finding is not that nobody built a journey suite. **Somebody built 595 of them. They aimed 349 at Bravo's worst-performing console and wired four CI workflows. Then three things happened.**

**One: only one workflow is scheduled, and it cannot fail.** `OPERATION_PLATFORM.yml` runs weekly, on `cron: "00 23 * * MON"`. The other three are `workflow_dispatch` only, so they are manual and never automatic. And every step of the scheduled one is written like this:

```yaml
on:
  schedule:
    - cron: "00 23 * * MON"          # weekly, not nightly
# …
      - run: |
          npx cypress run --browser electron --record --key ${{ secrets.… }} \
            --spec cypress/e2e/feature/operation-platform/BLOS-T3424.feature || true
          # …nine more specs, every one of them ending in  || true
```

`|| true` swallows the exit code. **So the workflow reports success whether the loan journey worked or not.** And it covers **10 of the 595** files.

This is the same defect as [§5](#5-not-5xx--healthy), one layer further out. Bravo's release gate treats "not 5xx" as healthy. Bravo's CI gate treats "the runner finished" as healthy.

**Two: the UI half of the suite does not assert. The API half does.** *(Re-measured 2026-09-10, with a wider verb list and a hand-read sample of each bucket. On the wider list, the earlier "82% carry no assertion verb" figure comes out at **80%**. Splitting it by tier is what makes it actionable.)*

| `Then` steps | Count | Assertion-shaped | Pure UI action |
|---|---:|---:|---:|
| **API feature files** (130 files) | 223 | **194 — 87%** | 11 — 5% |
| **UI feature files** (465 files) | 12,918 | 3,474 — **27%** | 7,407 — **57%** |
| All | 13,141 | 3,668 — 28% | 7,418 — 56% |

*(873 steps carry both kinds of word — mostly `Then Click Button < Visible` — and 1,182 neither.)*

**This is the more useful form of the finding, and part of it favours Bravo.**

Where the assertion was obvious — a status code and a response body — BFI's QA wrote it. `Then the response status should be 200`. `Then Verify the API status code is 500`. **They know how to do this.**

It broke in the UI tier, where there was no obvious thing to assert. There the keyword became a sequencing word: `Then Input username with text "…"`, `Then Click on button "#kc-login"`, `Then Continue to personal information`. A `Then` that types into a field detects a crash and nothing else.

And **463 of the 595 files, or 78%, are named by test polarity** rather than by business capability. The names are `Positive TestCase` 366 times, `Positive Test Case` 48, `Negative TestCase` 38, `Negative Case` 8 and `Positive Case` 2. Across all 595 files there are only **101 distinct `Feature:` names.**

The `Feature:` line is where a reader learns what the system does. This corpus's file list is not a table of contents of the loan business.

**The rest of the corpus's shape, measured.** These properties decide whether the 349 surveyor files can be re-pointed cheaply. They are also the argument for writing a style guide *before* the triage, not after it:

| Property | Measured | Why it matters for the triage |
|---|---:|---|
| `Scenario` · `Scenario Outline` · `Examples` · `Background` · `Rule` | 15 · **1,068** · 394 · 71 · **0** | `Scenario Outline` is the default keyword by copy-paste, not by need |
| Outlines with **no** `Examples` block | **675 of 1,068 (63%)** | Parameterised in name only |
| `Examples` blocks with exactly one data row | **332 of 394 (84%)** | Of the outlines that are parameterised, most vary nothing. **1,007 of 1,068 outlines carry no data variation at all** |
| Steps per scenario | median **3**, mean **26**, p90 **85**, **max 319**; 245 over 30, 144 over 60, **97 over 100** | Bimodal: small API checks and journey scripts. A 319-step scenario cannot fail for one reason, so a red run localises nothing |
| Distinct step phrasings (parameters normalised) | **2,438**, of which **1,229 (50%) used exactly once** | A domain language of ~2,400 words for one product line, half of it single-use |
| Step definitions | **1,691** in **206** files, 1,679 distinct | The glue is 1:1 with the prose, so the prose is code with worse tooling. Every re-pointed file drags its own bespoke steps along |
| Steps naming a UI widget (button, field, dropdown, page, modal…) | **7,042 (25%)** | A button rename invalidates the specification of a lending rule |
| Explicit `wait` steps | **618** (`User can wait <n> seconds` alone: **538**) | Timing is in the specification. This is the flake budget, written down |
| Indonesian UI labels inside English step text | **1,349 steps** (`Click on button Selanjutnya` ×523) | The sentence is a locator, not a specification; it cannot be reused across products |
| Orphaned glue | `underwriting/` holds **3 step-definition files and zero feature files** | Glue outliving its specification |

Two details are worth more than the totals.

First, the three most-used phrasings in the whole corpus are `User Click on Search Button` at 710 uses, `User click "<p>" button` at 624, and `User can wait <n> seconds` at 538. The second is a lower-cased duplicate of `click on "<p>" button`, which appears 304 times. So one intent has at least three spellings.

Second, there is a branch on the remote named **`B4WH-5851-qa-split-object-and-action`**. QA diagnosed the page-object and step-mixing problem themselves, and the fix never landed. That is [§5](#5-not-5xx--healthy) again, in a third place: **nothing broke when the file was wrong.**

**Three: it has been frozen for nearly three years, and the schedule has almost certainly lapsed.** The last commit was 2023-11-21. GitHub disables scheduled workflows after 60 days of repository inactivity, so the weekly cron is very likely not firing. **Zero CI pipeline events for any repository in 30 days** ([the Datadog check](#verdicts)) is consistent with that.

*This document cannot confirm it from a local checkout. Somebody needs to open the Actions tab.* That is a five-minute task, and it is the first item in the plan.

| Surface | What is there |
|---|---|
| Datadog **Synthetics** | **8 tests in the entire org**: 4 DNS checks and 4 SSL certificate checks. **Zero browser tests. Zero multi-step API tests. Nothing that creates an application.** |
| Datadog **CI Visibility** | **Zero pipeline events for any repository** in 30 days — Bravo or LORA. No build, test or deploy telemetry reaches this org at all. |
| `bravo-bpm-service` | 4 test files execute a Camunda process; no start-to-go-live walk ([§1](#1-inventory-2286-test-files-across-four-repositories-4-of-which-run-a-process)) |
| **`bravo-e2e-test`** | **595 feature files, 4 workflows, 1 weekly schedule that cannot fail, frozen 2023-11-21** |

**What this changes, and it does not favour Bravo.** The original finding was an absence, and absences are cheap to excuse — nobody got round to it.

The corrected finding is an **abandonment**. The investment was made at scale, by 46 people. Then it was allowed to decay, while the console it covers became the largest single source of production tickets. Worse, the one part still nominally running was written so it could not report a failure.

**An absent test cannot mislead anyone. A permanently green one can.** For as long as that workflow was firing, it was evidence of nothing while looking like evidence of something.

**So the continuous evidence that a Bravo loan can still be originated end to end is still the production ticket queue.** `Surveyor Platform - Release reject` ran at 315 tickets in August and has grown 4.8× since January. That is the regression detector.

**One caveat in Bravo's favour, and one asset.**

Bravo's volume is its own smoke test. At 118,253 applications in August, a total break in the main path is visible within minutes. That works for outages. It does not work for the failure Bravo actually has: a slow, product-specific, 4xx-shaped degradation that grows 82% over eight months while volume falls.

And the 595 files are a genuine **asset**, not just a reproach. 349 of them describe the surveyor journeys that [§7.3](#73-the-regression-suite-t1t12) wants regression cases for. They are Gherkin, so QA and product can read them. The L8 canary in [§7.2](#72-the-nine-layers) does not need writing from scratch. It needs **triaging, re-pointing, and an exit code that means something.**

### 6.1 If the 349 surveyor files are being re-pointed, fix the style first

The triage in [§7.3](#73-the-regression-suite-t1t12) and [recommendation 12](#recommended-actions) both assume the 595 files are an asset to re-aim, not rewrite. That holds. But re-pointing a file that names buttons, waits five seconds and ends every `Then` with a click just gives you a re-pointed file with the same defect.

So here are **eight rules. Each one answers a number measured above**, and the first three can be checked mechanically:

| # | Rule | Measured violation |
|---|---|---:|
| 1 | **A `Then` may not contain an action verb.** `Then` asserts; `When` acts | 7,418 steps |
| 2 | **A business-rule scenario may not name a UI widget** — no button, field, dropdown, page. Widgets belong to the small journey tier only | 7,042 steps |
| 3 | **No `wait` in a step.** Time appears only as an SLA or an expiry rule | 618 steps |
| 4 | **`Scenario Outline` only when `Examples` has ≥ 2 rows that change the outcome** | 1,007 of 1,068 |
| 5 | **`Feature:` names a business capability**, never a test polarity or a platform | 463 of 595 |
| 6 | **One scenario, one rule.** If the name needs "and", split it | 97 scenarios over 100 steps |
| 7 | **Step text is English; Indonesian only inside quoted values** | 1,349 steps |
| 8 | **A capped, reviewed step vocabulary** — one list per repo, with the `When` list closed. A new `When` needs a reviewer, because a new trigger is a new claim about the system | 2,438 phrasings, half single-use |

Rules 1 to 4 are roughly **50 lines over a Gherkin AST**. They would have failed most of this corpus on the day it was written. They are worth more than the triage itself: without them the triage is a one-off, and with them the corpus cannot decay the same way twice.

**Two tiers, and the ratio is the structural fix.** The corpus collapsed rule specification and UI journey into one artefact. That is how a scenario reaches 319 steps.

Separate them. Write **many** small rule scenarios that assert a state, a status or a rejection reason — those belong at [L3–L5](#72-the-nine-layers). Write **single digits** of full UI journeys per product, at L7–L8.

Bravo's own API features are already the first tier done correctly. That is the model to copy, and it is in the same repository.

**Keep one thing unchanged: the tags.** Every scenario carries a Zephyr key — `@BLOS-T3424`, `@B4WH-T808`, `@BR2W-T178` — under a `@ProjectKey-<KEY>` feature tag. That is the same scheme LORA's harnesses enforce as `@BL-T<n>`. It is the join from a requirement to an execution, and it is the one practice in this corpus that needs no correction.

The full style argument, together with the LORA-side collaboration ritual that produces these files in the first place, is in [people.md → Writing Gherkin for the BFI loan business](../../lora-workspace/docs/production-findings/people.md#writing-gherkin-for-the-bfi-loan-business).

---

## 7. A test strategy for Bravo — layers L0–L8

Sections 1 to 6 are a diagnosis. This section is the architecture.

The diagnosis on its own has a failure mode. Nine recommendations with no ladder to hang them on become nine tickets, each argued separately.

LORA's [lora-super-test](../../lora-workspace/docs/production-findings/testing/lora-super-test.html) does have a ladder: five `_`-prefixed layers (`_whitebox`, `_canary`, `_contract`, `_widgets`, `_utility`), a four-row cost budget, and a Zephyr tag per case. It also has its own account of *why*: full-SIT end-to-end tests "tested their uptime, not our code".

Bravo has no equivalent structure at all. What follows is the Bravo version. It is derived from Bravo's own decision surface, not copied from LORA's.

**Two design rules, both taken from LORA and both still true here.**

1. **Test only what you control; own the answers at the boundary.** LORA's boundary is one gateway envelope. Bravo's is different, and §7.1 works out where it actually sits.
2. **A change must fail in the cheapest layer that can see it.** LORA states this as a rule of thumb. For Bravo it is the whole point. Bravo's expensive layer, a Camunda process test, is the *only* layer that exists for orchestration today. And it exists four times.

### 7.1 Where Bravo's test boundary is

| | LORA | Bravo |
|---|---|---|
| Upstream call shape | one envelope, `POST /proxy/inner/request-v1`, naming its schema | **113 typed `@FeignClient` interfaces**, one per upstream |
| Interception point | one mock matching on `api_data_schema` answers as ~300 upstreams | 113 stub sets — **wider**, but each is a typed Java interface |
| Stub drift caught by | `check:stubs` against the live LSS schema registry | **the compiler.** Bravo has no schema registry ([§4](#4-validation-happens-in-production-38198-times-a-week)) — but a stub built from the Feign DTO *cannot* drift without failing the build |
| Fail-on-demand today | per-run, a spec steers one answer with a 2-line delta | **not possible.** `bravo-mock-service` (Mockoon, `*.mock.bravo.bfi.co.id`) is static and shared — the same weakness LORA names when it explains why it built its own |

**The finding in that table is in the last two rows, and they run in opposite directions.**

Bravo's boundary is wider than LORA's, and it needs no schema registry to stay honest. `javac` checks its 113 typed interfaces, where LORA's 300 JSON envelopes need a bespoke `check:stubs` script. That is a real advantage, and Bravo got it for free.

But Bravo has **no way to make an upstream fail on demand**. §7.3 lists what that costs.

### 7.2 The nine layers

Ordered by cost. Each row states what only that layer can catch — a layer that catches nothing a cheaper one sees does not belong on the ladder.

| Layer | What it owns | What **only** it can catch | Cost | Today |
|---|---|---|---|---|
| **L0** · model lint | All 53 BPMN + 3 DMN parsed at build, no Spring context | `ENGINE-09004` (38,198/wk in production); the **5 bare `PT4M`** retry cycles among 186 declarations; the **4 YAML process keys that are not deployed processes**; the **56 `callActivity` with no `calledElementBinding`**; orphans among 70 error definitions and 190 escalations | **seconds** | **none** |
| **L1** · config-table validation | The six-column selector, the `productId → key` YAML map, the per-application jsonb matrix, 1,350 Flyway migrations | Every `productId` resolves to a deployed process; every activity named in a jsonb matrix exists among the **274 distinct bean names**; no `WorkflowMasterConfig` row points at nothing | **seconds** | **none** |
| **L2** · Java unit | The 776 Mockito tests that exist. `BaseUnderwritingApprovalServiceImpl` (4,604 lines), the 50 `customErrorHandle` bodies | Ordinary Java defects. **This layer is fine** — it is the one Bravo already has | ms | **776 files** |
| **L3** · gateway-expression eval | Every `conditionExpression` string, evaluated through `ExpressionManager` against a variable map — **no process started** | Which branch a given variable set takes, across **137 exclusive gateways in `ndf4w.bpmn` alone** and ≈1.3 conditions per service task. **This is the layer that turns Bravo's routing from data back into code** | **ms** | **none** |
| **L4** · delegate contract | Each of the **276 `JavaDelegate`** classes against stubbed Feign clients | What an activity writes to process variables; which `customErrorHandle` fires on last attempt — including the anti-fraud `BYPASS` credit decision | **ms** | partial, inside L2 |
| **L5** · process fragment | One sub-process deployed and driven with `camunda-bpm-assert` — unified underwriting alone, unified KYC alone | Retry exhaustion, incident creation, escalation across one boundary, the forced-termination path | **~1 s** | **4 files** |
| **L6** · product-matrix journey | One process test per generation × product, start → go-live, upstreams stubbed | **"Does this change reach NDF2W?"** — the question [§3](#3-no-test-can-say-this-change-hits-ndf2w--and-one-bridge-makes-it-worse) says nothing answers. And the `ndf2w.bpmn` → unified-underwriting bridge | **~10 s** | **none** |
| **L7** · console contract + widget | Snapshot the response shape of the **9+ `FormTab` sub-resources** each console pane depends on; one live test per shared component. **Build this inside the consoles' existing Vitest suites — 829 files and a blocking PR gate already exist ([§1.1](#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)); this layer is an addition, not a new harness** | A console change that 404s a pane; the shape drift behind `Cannot read properties of null` (6,445/wk) | **~2 s** | **829 console test files, Vitest + Testing Library + `axios-mock-adapter`, gating every PR** |
| **L8** · production canary | A Synthetics multi-step API test that creates a real application; the per-console RUM error-per-view SLO | That origination works *right now*, on real infrastructure, with real upstreams | **minutes, scheduled** | **8 DNS/SSL checks** |

**Six of the nine layers do not exist.** L2 is healthy, and L5 exists four times.

The two layers that would have caught the most are **L0 and L3**, and both run in milliseconds. They are also the two Bravo has never built. Between them they cover every finding in [§2](#2-where-the-business-logic-actually-is--and-why-mockito-cannot-reach-it). The XML, the YAML and the config rows that Mockito cannot reach are all reachable *without the engine*.

**The routing rule, as a table.** When something breaks, this is the layer that should have caught it.

| Symptom | Cheapest layer that can see it |
|---|---|
| A gateway has no default flow | **L0** |
| A retry cycle does not repeat | **L0** |
| A new product has no deployed process | **L1** |
| A jsonb matrix names an activity that no longer exists | **L1** |
| An approval-ladder rule is wrong | **L2** |
| **A change reroutes one product and not another** | **L3** |
| An activity writes the wrong variable | **L4** |
| An upstream failure does not create an incident | **L5** |
| **A unified edit changes an in-flight NDF2W path** | **L6** |
| A console pane 404s | **L7** |
| Origination is broken in production | **L8** |

Read that column against the "Today" column above: **eight of eleven symptoms have no layer at all**, and the two marked in bold are the two with the largest production exposure in this document.

### 7.3 The regression suite, T1–T12

A regression test exists because something happened. Every case below is anchored to evidence in this pack, and the layer column says where it belongs — not one of them needs a browser.

| # | Regression | Because | Layer |
|---|---|---|---|
| **T1** | `Gateway_X_KYC_Verified` has an explicit default flow | The engine is **guessing** it in production, on the KYC path, across two deployed versions | L0 |
| **T2** | An NDF2W instance enters a **pinned** underwriting definition version | `ndf2w.bpmn` bridges into unified underwriting; 56 call activities are unpinned; **248,685 applications / 90 d** | L6 |
| **T3** | Every `failedJobRetryTimeCycle` is a valid `Rn/PTn` | 186 declarations, 30 distinct values, **5 bare `PT4M`** that do not repeat | L0 |
| **T4** | Anti-fraud degrades to `BYPASS` **only** on the last attempt | A credit-policy decision reached by an exception handler, verified by nothing | L4 + L5 |
| **T5** | `feature-configuration` returns its documented status | 266,767 404s/wk across **69% of surveyor sessions**, on the busiest handler in the service | L7 |
| **T6** | Every key in the `productId → process` map is a deployed process | The map contains **four that are not** | L1 |
| **T7** | The approval ladder resolves after a role rename | `BLCS-4683` renamed NMH→GMB; `BLCS-4811` is reversing it | L1 + L2 |
| **T8** | The IAM token is refreshed before `/permission/assigned` | **8,533 `401`s/wk at 1.07 per trace** — a broad auth defect, not a retry loop | L4 |
| **T9** | Adding a product touches all five discrimination mechanisms **consistently** | Product 15 (DF2W Sharia) touched all five, behind flags, untested | L1 + L3 |
| **T10** | Position capture succeeds, or degrades explicitly | ~20,700 geolocation failures/wk on a field-staff console | L7 |
| **T11** | The `FormTab` v2 pane set matches its snapshot | 9+ sub-resources; **four are the top sources of the 404 storm** | L7 |
| **T12** | Every monitor's `service:` tag matches a registered service | Four Sharia monitors filter `prod-sharia-bpm` against `prod-sharia-bpm-sharia` and **cannot fire** | L0 (lint the monitor definitions) |

### 7.4 The negative suite, N0–N12

**This is the largest single gap. It is also the one thing on the ladder Bravo cannot build without new infrastructure.** LORA can make any upstream fail, per run, with a two-line delta. Bravo cannot make an upstream fail at all. `bravo-mock-service` is static and shared, so *"ask anti-fraud to reject"* is not something a Bravo test can do. That is why 50 `customErrorHandle` implementations, 70 error definitions and 190 escalations go entirely unexercised.

| # | Force this | Assert | Layer |
|---|---|---|---|
| **N0** | Upstream returns 5xx | retries per `failedJobRetryTimeCycle`, then an incident is created and the loan parks | L5 |
| **N1** | Upstream returns `401` | the token is refreshed and the call retried — not counted as a terminal failure | L4 |
| **N2** | Upstream returns `404` | treated as "absent", not as an error — the live repeat-order case, 5,070/wk | L4 |
| **N3** | Upstream returns `400` | a contract violation is terminal and named, not retried 186 times | L4 |
| **N4** | Upstream never answers | the **300 s global `readTimeout`** is not the effective timeout for a job-executor thread | L4 |
| **N5** | Retries exhaust | the correct one of **50** `customErrorHandle` implementations fires | L4 + L5 |
| **N6** | Anti-fraud fails 3× | degrade to `BYPASS` — and **it is recorded as a credit decision**, not a log line | L5 |
| **N7** | Upstream returns a well-formed payload with a wrong-typed field | rejected at the client, not written to the aggregate | L4 |
| **N8** | The jsonb matrix disables a **mandatory** activity | the process refuses to start, rather than skipping a required check | L1 + L5 |
| **N9** | A child sub-process throws | escalation reaches the parent through one of the 190 escalation paths | L5 |
| **N10** | A loan is force-terminated mid-flight | status and `application_status_log` are consistent; no orphan job | L5 |
| **N11** | The same application starts twice | idempotent — one process instance, `RetryLog` unambiguous | L4 |
| **N12** | Two approvers decide concurrently | one wins; the ladder does not skip a tier | L2 |

**N0 through N12 need one piece of infrastructure**, and it is the same piece LORA built: a **per-run stub layer in front of the 113 Feign clients**, where a test steers one answer and everything else comes from a shared baseline. Bravo's version is cheaper than LORA's, for the reason in §7.1. The stubs are generated from typed interfaces. So there is no schema registry to keep in sync, and no `check:stubs` script to write.

### 7.5 The budget: 400 cases must not mean 400 process runs

LORA's arithmetic applies unchanged. 400 cases at a 2-minute walk each is 13 hours. And a suite nobody can run in a sprint is a suite nobody runs. Here are the same 400 cases spread down the ladder:

| Layer band | Cases | Each | When | Wall clock |
|---|---:|---:|---|---:|
| L0 + L1 — lint and config | ~60 | ~20 ms | **every build** | **~2 s** |
| L2 + L3 + L4 — Java, expressions, delegates | ~1,100 | ~5 ms | every build | ~15 s |
| L5 — process fragments | ~60 | ~1 s | every build | ~1 min |
| L6 — product-matrix journeys | **5** | ~10 s | every merge | ~1 min |
| L7 — console contracts | ~40 | ~2 s | every merge | ~1.5 min |
| L8 — canary | 1 | ~3 min | hourly | — |
| | | | **per-merge total** | **≈4 min** |

Five L6 journeys covers the whole product matrix: NDF2W, NDF4W, RO, unified DF4W and DF2W. **Five tests would cover the paradigm's happy path across 100% of production volume.** Today, zero tests cover it. They are also the *expensive* layer, deliberately kept to five, because L0 to L4 catch everything that does not need the engine.

### 7.6 Three rules that keep it from rotting

Taken from LORA's review criteria, which reject exactly three things in a spec diff. Bravo's equivalents:

1. **No hand-written expectation lists.** LORA derives its 24-stage activity plan from real traces, because hand-written lists "were proven wrong twice". Bravo's equivalent is the activity set per product: **derive it from `act_hi_actinst`. Never type it.** This depends on the job-executor spans in [bravo-observability.md](bravo-observability.md) recommendation 8. Without them, a derived Bravo expectation has no source.
2. **No selectors or field paths in a test.** Bravo's version of this rule: no `productId == 1L` literal in a test. A test asks the config layer which product it is. That way a test cannot become the sixth discrimination mechanism.
3. **No stub copied into a case.** Name a baseline bundle, state only the delta. This is what makes N0–N12 two lines each instead of a fixture per case.

**And one rule that is Bravo's alone:** never auto-record a snapshot. LORA states the reason precisely. If the first passing run records the baseline, "that day's form — bugs included — would silently become the truth". For Bravo the trap is larger. L0 would otherwise record 38,198 parse warnings a week as the approved state of the models.

---

## Recommended actions

Ordered by what would have caught something. Items 1–3 are days of work each.

1. **Pin `calledElementBinding` on every `callActivity`, or write the one test that proves the bridge. Small to medium effort, highest value.** There are 56 call activities and none is version-pinned, and `ndf2w.bpmn` calls into unified underwriting. So do one of two things. Pin the binding, so a unified edit cannot reach 73% of volume mid-flight. Or add a Camunda process test that starts an NDF2W instance and asserts which underwriting definition version it enters. Today neither exists.
2. **Fail the build on `ENGINE-09004`. Small effort.** The warnings are already produced. They are just produced in the wrong place. A parse test over all 53 BPMN files with `camunda-bpm-assert` — the dependency is already in the pom — turns 38,198 production warnings a week into a red build. Start by fixing the KYC gateway the engine is currently guessing about.
3. **Add a 4xx clause to the release health gate. Small effort.** "Not 5xx" is not health. At minimum, add per-resource 404 and 401 rates on the four surveyor endpoints and the IAM permission call. See [bravo-observability.md](bravo-observability.md) recommendation 2.
4. **Build one end-to-end process test per generation. Medium effort.** That is two tests: an NDF2W instance and a unified DF4W instance. Walk each from start to go-live with upstreams stubbed, and assert the terminal status and the set of activities executed. `camunda-bpm-assert` and `camunda-bpm-mockito` are already dependencies. Two tests would cover the paradigm's entire happy path. No test covers it today.
5. **Test the retry and degrade policies. Medium effort.** Assert that `failedJobRetryTimeCycle` is a valid `Rn/PTn` on every service task — the 5 bare `PT4M` cycles are a latent defect. Then add a test that drives an activity to its last attempt and asserts which `customErrorHandle` fires. The anti-fraud `BYPASS` path is a credit-policy decision reached through an exception handler, and nothing verifies when it fires.
6. **Make the product blast radius visible in the diff. Medium effort.** Tag every test with the products it covers. Then emit, for each pull request, the set of `productId`s reachable from the changed BPMN files, config rows and factories. A reviewer should not have to know five discrimination mechanisms to know whether a change reaches NDF2W.
7. **Turn on a coverage gate in `ms-bpm`, and fix the `makefile`. Small effort.** Use JaCoCo `check`, with a floor at the current level, ratcheting upward. And fix `-Dspring-boot.run.profiles`, which surefire ignores. The tests are not running under the profile the build claims.
8. **Add one Synthetics multi-step API test for the origination journey. Small to medium effort.** This is a canary, not a replacement for a process test. Today the only continuous evidence that Bravo works is a support-ticket queue. **And it need not be written from scratch.** 349 of the 595 `bravo-e2e-test` feature files already describe the surveyor journeys ([§6](#6-the-journey-suite-bravo-built-and-stopped-running)).
9. **Send CI events to Datadog. Small effort.** Neither platform has any pipeline events, so nobody can answer whether the build is getting slower, flakier or redder. This is a configuration change, and it benefits both teams.
10. **Build the per-run stub layer in front of the 113 Feign clients. Medium effort, and it unblocks N0 through N12.** Today no Bravo test can make an upstream fail. So 50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths go unexercised. `bravo-mock-service`, which is Mockoon, does not solve this: it is static and shared. That is exactly why LORA built its own interceptor instead of using it. Bravo's version is the cheaper one to build, because stubs generate from typed Feign interfaces. There is no schema registry to sync and no `check:stubs` script to write ([§7.1](#71-where-bravos-test-boundary-is)).
11. **Derive expectations. Never type them. Small effort, and it is a policy rather than a task.** LORA derives its activity plan from real traces, because hand-written lists were proven wrong twice. Bravo's equivalent is the per-product activity set, derived from `act_hi_actinst`. That needs the job-executor spans in [bravo-observability.md](bravo-observability.md) recommendation 8 first. Until those land, an L6 journey's expected activity set has no trustworthy source. This is the one dependency this document has on another.

12. **Delete every `|| true` from `OPERATION_PLATFORM.yml`, then decide what happens to the corpus. Small effort to fix, medium to triage. Do the fix today.**

    The one scheduled Bravo end-to-end workflow cannot report a failure. Deleting `|| true` is a trivial edit on each line, and it turns a decorative run into a real one.

    Then answer the question this document cannot answer from a checkout: **open the Actions tab and find out whether the weekly cron has fired since 2023.**

    After that, the 595 files are a triage job, not a rewrite. 349 of them cover the console generating 28.4% of Bravo's tickets. They already carry Zephyr tags. And the 57% of UI `Then` steps that only click need an assertion added. So re-point them at L7 and L8 rather than starting again. But **land the four mechanical style rules in [§6.1](#61-if-the-349-surveyor-files-are-being-re-pointed-fix-the-style-first) first**, or the triage will produce re-pointed files with the same defect.

13. **Ship the four mechanical Gherkin rules as CI before the triage starts. Small effort.** The rules are: no action verb in a `Then`; no UI widget in a rule scenario; no `wait`; and no `Scenario Outline` with fewer than two `Examples` rows. That is about 50 lines over a Gherkin AST. They fail most of the existing corpus on contact, which is the point. Without them the triage in item 12 is a one-off, and the corpus already decayed this way once ([§6.1](#61-if-the-349-surveyor-files-are-being-re-pointed-fix-the-style-first)).

14. **Rotate the credentials committed in `bravo-e2e-test/cypress.config.js`. Small effort, and it is a security task rather than a testing one.** We found this while measuring the corpus. The file carries a Jira user API token for `qa@bfi.co.id`, a Zephyr Scale API key, an LMS username and password in plaintext, an agreement `apiSecret`, and a lead token. The repository has 46 contributors and two squad checkouts.

    The JWTs decode to 2024 expiries. **The plaintext LMS credentials carry no expiry at all.** So rotate them, move them to repository secrets, and assume the full history is exposed. The values sit in 600 commits of git history, not just the working tree. None of this depends on whether the suite is ever revived.

    > **Escalated 2026-09-10. This is no longer hygiene. It is a candidate root cause.**
    >
    > The production Camunda engine contains **61 injected remote-code-execution process definitions, and one of them ran**. We corrected the vector on 2026-09-10: the deploy path `/engine-rest/**` **requires a credential**. So whoever did it held a valid Keycloak token, or the shared internal service secret ([SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md)).
    >
    > **A repository with 46 contributors, two checkouts and plaintext service secrets in 600 commits of history is the most plausible source anyone has identified.** This is not established — no ticket or log ties this file to those deployments. But it moves the item from *"rotate on principle"* to **the second action in an active security incident**. And the intrusion window, 2026-05-23 to 06-30, sits inside the period these credentials were exposed.

15. **Enforce the coverage the three consoles already measure, and wire up the bumper that is already installed. Small effort.** All three compute coverage on every pull request and ship it to SonarQube. All three set the failing threshold to 0% or 1%, so it cannot fail.

    Read the current lcov figure for each repository, set the threshold just below it, and let `jest-coverage-thresholds-bumper` ratchet it up. That package is **already a dependency in `bravo-underwriting-console`, and invoked nowhere.**

    This is the cheapest quality win in the estate. The tests, the runner, the coverage report and the blocking job all exist. One number in three config files is the difference between measuring and enforcing. Add `-Dsonar.qualitygate.wait=true` in the same change, so the Sonar gate stops being advisory.

### Where each recommendation lands on the ladder

| Rec | Layer | Note |
|---|---|---|
| 2 — fail the build on `ENGINE-09004` | **L0** | Also delivers T1, T3, T12 in the same test harness |
| 7 — coverage gate, `makefile` fix | **L2** | Gates the layer that is already healthy |
| 6 — product blast radius in the diff | **L1 + L3** | Falls out of L1 and L3 almost for free once they exist — the reachable `productId` set *is* the L3 evaluation |
| 5 — retry and degrade policies | **L0** (validity) **+ L4/L5** (behaviour) | Part 1 is L0 and costs 4 days; part 2 needs L5 *and* rec 10 |
| 1 — pin `calledElementBinding` | **L0** (detect) **→ L6** (prove) | L0 finds all 56 in seconds; only L6 proves the fix |
| 4 — end-to-end process test per generation | **L6** | Five journeys, not two — the full product matrix |
| 3 — 4xx in the health gate | **L7** | With T5, T10, T11 |
| 8 — Synthetics origination canary | **L8** | — |
| 9 — CI events to Datadog | — | Infrastructure for all of it: today no layer's runtime is measurable |
| **10 — per-run stub layer** | **enables L4, L5** | The whole of N0–N12 |
| **11 — derive, don't type** | **policy for L6** | Blocked on observability rec 8 |

**The ordering this implies differs from the list above, and it is better.** Recommendation 2 is written as "fail the build on `ENGINE-09004`". But the harness it needs *is* L0. And once L0 exists, it also delivers T1, T3, T12 and the detection half of recommendation 1, in the same few days. **L0 and L1 are the cheapest work in this document, and they close the largest number of findings.** They should come first, ahead of the item currently marked highest-value.

---

## Plan: 30, 60, 90 days

Eleven recommendations, phased against about 25 person-days a month of Squad S&U time. That allocation is set by [bravo-people.md](bravo-people.md) recommendation 4.

**The phases are the ladder in [§7.2](#72-the-nine-layers), built cheapest first:** L0 and L1 in month 1, L3 and L4 in month 2, L5 and L6 in month 3. That ordering is not a preference. L6 is the only layer that can prove the `calledElementBinding` fix, and L0 is the only layer that can find all 56 call sites in seconds.

**The rule for ordering this work: investigate before touching anything that reaches in-flight loans.** Recommendation 1 is the highest-value item here, and the most dangerous to rush. Unpinned `callActivity` binding affects **248,685 NDF2W applications per 90 days**. So it is read-only in month 1, a decision in month 2, and a change in month 3. Nothing else in this plan alters in-flight behaviour at all.

**Shared with other documents.** Recommendation 1 is also recommendation 6 in [bravo-delivery.md](bravo-delivery.md). Recommendation 3 is also recommendation 2 in [bravo-observability.md](bravo-observability.md). Both are phased the same way in every document, so do them once.

### Days 0–30 — look, and start reporting

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **`calledElementBinding` investigation — read-only.** Enumerate all 56 `callActivity` elements; map which children an NDF2W instance reaches; quantify the exposure of the `ndf2w.bpmn` → unified-underwriting bridge | 1 | S&U | 5 d | A written exposure note. **No code change this phase** |
| **Send CI pipeline events to Datadog** | 9 | Platform | 2 d | Zero pipeline events becomes a build-health number, for both platforms |
| **Open the Actions tab on `bravo-e2e-test`** and record whether the weekly cron has fired since 2023-11-21. This document cannot answer that from a local checkout | 12 | QA | **5 min** | The status of Bravo's only scheduled journey run stops being an inference |
| **Delete every `\|\| true` from `OPERATION_PLATFORM.yml`** | 12 | QA | **1 h** | Bravo's one scheduled E2E run can report a failure. Until this lands the run is evidence of nothing while looking like evidence of something |
| **Build L0 — model lint.** All 53 BPMN + 3 DMN parsed at build with `camunda-bpm-assert`, already in the pom. Delivers rec 2, plus **T1** (the KYC gateway the engine is guessing), **T3** (the 5 bare `PT4M` cycles), **T12** (monitor tag mismatch) and the *detection* half of rec 1 (all 56 unpinned call activities) | 2, 5, 1 | S&U | 4 d | 38,198 production parse warnings a week become a red build that runs in **seconds**. The cheapest layer in the document, and the one that closes the most findings |
| **Build L1 — config-table validation.** Every `productId` resolves to a deployed process; every activity in a jsonb matrix exists among the 274 bean names; no orphan `WorkflowMasterConfig` rows | 6 | S&U | 3 d | The **four YAML keys that are not deployed processes** fail the build. **T6**, **T7** and **T9** land here |

### Days 31–60 — put the gates in

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Fail the build on `ENGINE-09004`.** A parse test over all 53 BPMN files with `camunda-bpm-assert` — already in the pom — and fix the KYC gateway whose default flow the engine is currently guessing | 2 | S&U | 4 d | 38,198 production parse warnings a week become a red build |
| **Add the 4xx clause to the release health gate.** Per-resource 404 and 401 rates, at minimum on the four surveyor endpoints and the IAM permission call | 3 | Platform/SRE | 3 d | "Not 5xx = healthy" is retired. A release that 404s two-thirds of sessions fails the gate |
| **Coverage gate + `makefile` fix.** JaCoCo `check` at the current floor, ratcheting; correct `-Dspring-boot.run.profiles`, which surefire ignores | 7 | S&U | 2 d | Coverage cannot fall, and tests run under the profile the build claims |
| **Synthetics multi-step API test for origination** — a canary, not a replacement for a process test | 8 | QA | 3 d | Something other than the support-ticket queue notices that origination broke |
| **`calledElementBinding` decision** — pin, or accept in-flight child migration deliberately, with a migration plan | 1 | S&U + EM | 2 d | A recorded decision. Implementation next phase |
| **Build L3 — gateway-expression evaluation.** Every `conditionExpression` evaluated through `ExpressionManager` against a variable map, no process started | 6 | S&U | 5 d | **Bravo's routing stops being data and becomes code.** 137 exclusive gateways in `ndf4w.bpmn` alone are testable in milliseconds. This plus L1 *is* rec 6 — the reachable `productId` set falls out of it |
| **Build the per-run stub layer** in front of the 113 Feign clients — generated from the typed interfaces, one baseline bundle plus a per-test delta | 10 | S&U | 6 d | An upstream can be made to fail on demand for the first time. **Unblocks all of N0–N12** |

### Days 61–90 — prove the journey, then make the change

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Build L5 + L6 — the five product-matrix journeys.** NDF2W, NDF4W, RO, unified DF4W, DF2W, each start to go-live with upstreams stubbed on the phase-2 stub layer, asserting terminal status and the executed activity set. Expectations **derived** from `act_hi_actinst`, never typed | 4, 11 | S&U + QA | 12 d | "Can a loan still get from submission to go-live?" is answered every build, **for 100% of production volume** instead of 0%. **T2** lands here, and this is the harness the next two items need |
| **Implement the binding decision** — pin `calledElementBinding` on all 56 call activities, with the migration plan agreed in phase 2 | 1 | S&U | 10 d | A unified sub-process redeploy can no longer silently change the path of in-flight NDF2W loans |
| **Retry-policy validation (part 1).** Assert every `failedJobRetryTimeCycle` is a valid `Rn/PTn` — the five bare `PT4M` cycles are a latent defect | 5 | S&U | 4 d | No service task carries a retry policy that does not do what its author intended |

### Deferred, with triggers

| Deferred | Rec | Why | Trigger |
|---|---|---|---|
| **The negative suite, N0–N12** — force each upstream failure mode and assert the degrade decision; the anti-fraud `BYPASS` (**N6**) is a credit-policy decision reached by an exception handler | 5, 10 | Needs both the phase-2 stub layer and the phase-3 L5 harness. Roughly 2 days per case once both exist | After the L6 journeys land |
| **Triage the 595 `bravo-e2e-test` features** — land the four mechanical style rules ([§6.1](#61-if-the-349-surveyor-files-are-being-re-pointed-fix-the-style-first)), re-point the 349 surveyor files at L7/L8, add assertions to the 57% of UI `Then` steps that only act, retire the rest | 12 | A triage job, not a rewrite: the files carry Zephyr tags and describe the right journeys. Cheaper once L7 exists to receive them — and worthless without the style rules, which is ~50 lines of CI | After L7 lands |
| **L7 — console contracts.** Snapshot the 9+ `FormTab` sub-resource response shapes; one live test per shared component. **T5**, **T10**, **T11** | 3 | The 4xx health gate in phase 2 detects these; L7 is what *prevents* them. Depends on the console inventory in [bravo-delivery.md](bravo-delivery.md) rec 7 | After that inventory |
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
| **L0 + L1 exist** | A gateway with no default flow, a retry cycle that never repeats, a product with no deployed process, and a jsonb matrix naming a deleted activity all fail the build **in seconds** — instead of in a production log stream nobody reads. |
| **L3 exists** | "Which products does this diff reroute?" is answered by evaluating the gateway conditions, not by a reviewer who happens to know all five discrimination mechanisms. |
| **The stub layer exists** | A test can say *"this run's anti-fraud rejects"*. 50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths stop being unexercised. |
| **The frozen corpus is triaged** | 349 surveyor feature files that describe the journeys behind 28.4% of Bravo's tickets either assert something and run, or are retired on purpose — instead of sitting in a repo nobody has opened since 2023. |
| **The ladder has a routing rule** | A form change fails in L7 in two seconds, not in a 10-second journey three layers from the cause — and the per-merge suite still finishes in about four minutes. |

---

## Related

- [bravo-observability.md](bravo-observability.md) — the production signals these gates would consume
- [bravo-delivery.md](bravo-delivery.md) — what shipping a change into Bravo costs once it passes
- [bravo-people.md](bravo-people.md) §6 — why a Bravo change is fewer artefacts than a LORA one, and what that buys
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.10, §3.11 — the test inventory and in-flight versioning in code terms
- [workflow-gap.md](workflow-gap.md) §8 — the 5.5% / 94% volume split between the two generations
- LORA [testing.md](../../lora-workspace/docs/production-findings/testing.md) — the same questions asked of the other platform
- LORA [people.md § Writing Gherkin for the BFI loan business](../../lora-workspace/docs/production-findings/people.md#writing-gherkin-for-the-bfi-loan-business) — **the style guide and the product/QA ritual derived from this corpus.** It covers the ten rules, the two tiers, the capped step vocabulary, and the CI gates that stop a `.feature` file decaying the way these 595 did
- LORA [lora-super-test](../../lora-workspace/docs/production-findings/testing/lora-super-test.html) — **the strategy [§7](#7-a-test-strategy-for-bravo--layers-l0l8) is derived from**: five `_`-prefixed layers, the mock interceptor, derived expectations, and the test-volume budget
