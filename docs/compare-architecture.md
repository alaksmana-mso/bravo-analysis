# Bravo LOS (pure BPMN workflow) vs LORA (hybrid GSM + Temporal) — architecture

> **Renamed 2026-09-10.** This file was `compare.md`. It is the **architecture and paradigm** comparison and is unchanged.
> The production-findings synthesis and the platform recommendation now live in **[compare.md](compare.md)**, which draws on
> [bravo-people.md](bravo-people.md), [bravo-testing.md](bravo-testing.md), [bravo-observability.md](bravo-observability.md),
> [bravo-cost.md](bravo-cost.md) and [bravo-delivery.md](bravo-delivery.md).

**Question answered:** the LORA design rationale ([gsm-vs-workflow-approach.md](../../lora-workspace/docs/design-rationale/gsm-vs-workflow-approach.md), [hybrid-approach-gsm-workflow.md](../../lora-workspace/docs/design-rationale/hybrid-approach-gsm-workflow.md)) argued that a data-centric Guard-Stage-Milestone brain on a Temporal execution layer would beat "drawing branching flowchart arrows for every edge case". BFI already runs the same Loan Origination System the other way: `bravo-bpm-service` is a pure workflow-engine implementation on Camunda 7 BPMN. This document reads both codebases and compares what each approach actually produced.

**Method.** Code and configuration verification of `squads/Scoring and Underwriting/bravo-bpm-service` (checkout at `v2.93.43`, last commit 2026-09-07) against the LORA documentation set (`lora-workspace/docs`: design-rationale, assessment, architecture, production-findings, August to September 2026). Every Bravo claim below cites a file. LORA claims cite the LORA docs, which in turn cite LORA code and production data. Counts are `grep`/`find` over the checkout.

**Revision 2026-09-10.** The OTRS ticket export closed the pack's largest measurement gap; §3.14 is new and §3.6, §3.7, §4, §5 and §6 are amended where they said "not measured".

**Revision 2026-09-09.** The Bravo team responded to rows 1–3 of §2. Each response was checked against the code; the rows were revised and §8 records the arguments, the evidence and what changed. Production-share figures come from the 90-day PostgreSQL and Datadog measurements in [workflow-gap.md §8](workflow-gap.md).

**Scope caveats, read first.**

- LORA's production-findings pack measured LORA in production (Temporal Cloud billing, Datadog). For Bravo we have code, git history and the GCP bill as recorded by the LORA cost document. **Superseded in part on 2026-09-10:** the OTRS support-ticket export ([production-findings/ticket-analysis.md](production-findings/ticket-analysis.md)) now gives Bravo's manual-intervention rate, incident counts and per-activity failure data on the same basis as LORA's — the first symmetric reliability measurement in the pack. Its rates rest on the billing sheet's disputed application counts, so they are provisional; its counts and trends are not. Where LORA still has a measured number and Bravo has only a code-level mechanism, the table says so.
- "Bravo" in the LORA cost figures means the whole Bravo estate (Cloud SQL, ~50 upstream services, non-prod projects), not `bravo-bpm-service` alone. On 2026-09-09 the Bravo team objected that this makes the cost comparison unfair because LORA itself calls most of that estate; the objection was checked and upheld, and §3.12 and §8.5 now carry a like-for-like orchestration-tier comparison in which Bravo's tier is the cheaper one.
- Bravo is being drained into LORA (applications fell from ~118k to ~76k per month between July and August 2026), so its unit economics are inflating for reasons unrelated to architecture.

---

## 1. The two systems at a glance

| | **Bravo LOS** (`bravo-bpm-service`) | **LORA** (`lora-workspace/services/*`) |
|---|---|---|
| Orchestration paradigm | Process-centric BPMN 2.0 on embedded Camunda 7.23 | Data-centric GSM planner (`GSMBELExecutor`) on Temporal Cloud |
| Language / runtime | Java 17, Spring Boot 3.5.16, one monolithic service | Go, 13 repos across 7 product families, shared `lora-process-sdk` |
| State store | PostgreSQL (Cloud SQL) via JPA: 238 `@Entity`, 271 tables, 1,350 Flyway migrations | One JSON document per loan in ArangoDB (`dp-ndf-v0_24_0`; 777 leaf fields by the LORA assessment's count, ≈1,200 properties when nested object nodes are counted), held in Temporal workflow memory |
| Process model artefacts | 53 production BPMN files (largest `ndf4w.bpmn` 9,494 lines, `ndf2w.bpmn` 8,464), 3 DMN, used only by the pre-MVP unsecured flow, one unreferenced | No flowchart. 172 registered ProcessSteps with ReadSet/WriteSet, 155 `SetPrecondition` guards, 3 hard precursors |
| Automated step implementations | 225 classes implementing `JavaDelegate` directly, 276 including subclasses of the abstract bases, all in `activity/` (31,677 LOC, 6.4% of code) | 172 activity constructors + 301 schema-validated gateway proxies |
| Human-task code | ~217k LOC (43.6% of code): `SurveyorAssignmentServiceImpl` 10,419 lines, `OperationAssignmentServiceImpl` 8,177, `BaseUnderwritingApprovalServiceImpl` 4,604 | ~12k LOC of hand-written FSMs: `survey.go` 5,473 lines / 125 transitions, `bpkb_review.go` 3,421 / 79, `underwriting.go` 3,041 / 72; 77 form builders |
| Total size | 497,970 LOC main Java, 5,070 files; 1,457 test files (plus 595 `.feature` files in the separate `bravo-e2e-test` repo, frozen 2023) | ~617k LOC Go across the workspace (gateway 164k, task-service 89k, task-ndf 78k, ndf 53k, sdk 24.5k) |
| External integrations | 113 `@FeignClient` interfaces, 2 RabbitMQ brokers, 14 listeners, 7 publishers | 301 proxies behind one gateway route, 25 RabbitMQ subscribers, NATS |
| Age and churn | First commit 2022-01-26; 39,668 commits; 94 authors all-time, 23 active in 2026; 5,479 release tags | Production since 2026; 8 concurrent worker versions (`v0-16` to `v0-22`) |
| Volume (Aug 2026, per LORA cost doc) | 76,446 applications (31%) | 171,479 applications (69%) |
| Orchestration-tier cost (Aug 2026, FinOps API) | `ms-bpm` pods + its Cloud SQL: **≈Rp58M/month prod** (≈Rp70M with SIT/UAT pods); ≈Rp510–760 per application. The ≈Rp1.65B "Bravo estate" figure is mostly the shared data plane LORA also calls | **≈Rp431M/month all-in** (GKE Rp187M, Temporal Rp140M, ArangoDB licence Rp65M + GKE Rp39M); ≈Rp2,500–3,200 per application |

---

## 2. The design rationale's claims, checked against Bravo

The LORA rationale made five arguments against the workflow approach. Bravo is the concrete workflow approach it was arguing against, so each can be tested.

| # | Rationale claim | What Bravo shows | Verdict |
|---|---|---|---|
| 1 | Flowcharts need "branching arrows for every edge case"; complexity explodes | **Observed:** `ndf4w.bpmn` alone has 111 service tasks, 21 user tasks, 137 exclusive gateways, 48 sub-processes and 70 error definitions in one 9,494-line file, and product routing sits inside gateway conditions as string-compared variables plus Spring property lookups (`environment.getProperty('setting.feature.config.featDF2W') == 'true' && applicationWorkflowSelectorType == "OPTION_DF2W"`). **Mitigated:** the 2024 unified rewrite applies the standard spine-plus-children remedy (an 8-step spine, 36 children) and is 3.4× smaller with 7× fewer flag lookups. **Not removed:** decision density is unchanged at ≈0.7 business gateways and ≈1.3–1.4 conditions per service task in both generations, escalation plumbing rose to 1.67 definitions per service task, and the spine carries 5.5% of production volume (DF4W only) while the monoliths carry ≈94% and were edited more often in 2026. Detail in §8.1 | **Observed in Bravo; a consequence of modelling practice, not a law of the paradigm.** The mitigation exists and is unproven at scale |
| 2 | Loan events are parallel and out-of-order; process-centric models handle this badly | Bravo's flows are almost entirely sequential: 14 `parallelGateway` and 4 `inclusiveGateway` across 53 files, 0 in `unified-main-workflow.bpmn`; 0 message events, 0 signal events, 0 event-based gateways, 0 event sub-processes, 0 non-interrupting boundary events. Camunda supports every one of these, so their absence is a modelling choice. An external event cannot be injected into a waiting process; it is reflected by a REST call that sets a variable or completes a task. Detail in §8.2 | **Confirmed as observed.** Fork/join parallelism is a modelling choice Bravo could adopt; unplanned, data-driven order is a paradigm difference |
| 3 | In workflow tools the data "lives in scattered process variables outside the diagram" | Not how Bravo did it. Camunda holds only routing flags (255 variable keys in `WorkflowConstants.java`, all decision booleans, scores and one `applicationId`). Business data is a relational aggregate of 238 JPA entities with `Application` as root, which gives SQL fleet queries and independent evolution of sub-entities. What *is* scattered is **lifecycle state**: 30 `ApplicationStatus` values plus ~105 other status enums, `OperationAssignment` with 7 parallel status fields, `SurveyorAssignment` 8+, 197 `setStatus` sites in 73 files, an `Application` root that is a Lombok `@Data` class with no transition method, and no persisted "current stage" (`lastStage` is `@Transient`; stage is recovered from Camunda, whose history is purged after 90 days). Detail in §8.3 | **Partly refuted, redirected.** The relational aggregate is legitimate; the weakness is an aggregate root that does not own its lifecycle |
| 4 | Temporal gives retries, durable waits and event loops "natively"; workflow engines need plumbing | Bravo built a lot of plumbing: 186 `failedJobRetryTimeCycle` declarations with 30 distinct values, a custom last-attempt degrade framework (`OutboundAutoErrorHandlerEngineServiceImpl`, 62 call sites, 50 `customErrorHandle` implementations), a DB-backed retry counter (`RetryLog`), a transactional outbox (`event_store`), an inbox for out-of-order messages (`event_retry`), a work/wait/dead queue triple per binding, 15 ShedLock schedulers, and ~25 manual retry/reprocess/revive/cancel endpoints. | **Confirmed on plumbing volume.** But see §3.6: Bravo's retries are *bounded* and degrade gracefully, which is precisely the retry *policy* LORA never wrote |
| 5 | Saga compensation for failed disbursement is the execution layer's job | Bravo has 0 `compensateEventDefinition`, 0 `bpmn:transaction`, 0 terminate events. Failed go-live is handled by a 5-minute sweeper (`OperationAssignmentScheduler.checkFailedGoLiveDigiSign`) that re-requests and asks CONFINS to republish. LORA has document-field rollback only | **Neither system built it.** The rationale was right that it is needed and wrong that either execution layer would supply it for free |

The one claim the rationale did not make, and should have: **human tasks re-create flowchart complexity regardless of paradigm.** Bravo spends 44% of its code on human work; LORA's assessment found ~12k lines of hand-written FSMs "inside the declarative outer shell". Both are the same phenomenon. See §4.

---

## 3. Dimension-by-dimension comparison

### 3.1 Process model and orchestration

**Bravo.** There is no single process; there are three generations of top-level processes deployed side by side.

| Generation | Root process key(s) | Started from |
|---|---|---|
| Unified (current) | `Unified_Process_Main_Workflow`; plus two further roots, `Unified_Process_Operation_Workflow` (started by a `JavaDelegate` inside the main workflow, not a `callActivity`) and `Unified_Process_Scoring_2` (started programmatically from Java) | `POST /v2.1/application` → `ApplicationV2P1ServiceImpl.java:441,641` |
| Legacy per product | `NDF4W`, `NDF2W`, `NDF4W_Sharia`, `NDF4W_RO`, `UNSECURED`, `OPERATION`, `Sharia_NDF4W_Operation_Process` | `/v1` and `/v2/application` via the YAML map `productId → key` (`application.yaml:1364`) with an RO override in Java (`ApplicationServiceImpl.java:752-762`) |
| Standalone | `preApprovalScoring`, `multiAssetSurveyScoring`, `unsecured-pre-mvp` | Dedicated services |

The unified master (`unified-main-workflow.bpmn`, 903 lines) composes the lifecycle as eight `callActivity` steps in a fixed order, each a sub-process file that calls further sub-processes:

```
Unified_Process_Main_Workflow
├─ Workflow_Check            → Duplicate Check, Marketing ID, Branch Lead & Survey, Pilot Branch,
│                              Follow-Up Assignment, Dedupe Customer, Anti-Fraud, KYC
├─ Workflow_Initial_Scoring  → Personal Data Prerequisite (→ Pefindo), KYC ×2, RAC (→ Pefindo), PD Model
├─ Update_Application
├─ Workflow_Survey           → Surveyor Resolution, Surveyor Assignment, Scoring Assignment,
│                              Negotiation Assignment, Survey Returned
├─ Create_CIF
├─ Document_Submission
├─ Workflow_Underwriting     → Underwriting CA, Approval Engine, Underwriting BM, Underwriting Regular (→ BM)
└─ Escalation_Decision
   then a service task starts Unified_Process_Operation_Workflow
      → Branch Data Enrichment, HO Data Enrichment, HO Request Go Live, Go Live, Pending Take Over
```

Chaining is `callActivity` (56) plus BPMN **escalation** as the child-to-parent return channel (190 escalation event definitions) plus BPMN **link** events as intra-process "goto" to shared terminal handlers (194). Every `callActivity` passes `<camunda:in variables="all"/>`; 49 of 56 also declare `<camunda:out variables="all"/>`, and the seven that do not include all five call activities in `unified-workflow-survey.bpmn` plus Create CIF and Document Submission in the main workflow, so child results such as `surveyResult` and `negotiationStatus` never propagate upward through the mapping. None of the 56 sets `camunda:calledElementBinding`, so each child resolves to the **latest deployed version** at call time (see §3.11). The legacy files (`ndf4w.bpmn`, `ndf2w.bpmn`, `unsecured.bpmn`) use BPMN **errors** instead of escalations (210 error definitions, e.g. `Customer Profile - HighRisk` ×15, `Customer Profile - Rejected` ×12), and `ndf2w.bpmn` bridges into the unified underwriting sub-process, so a legacy instance can end up running unified code.

In production the two generations are not equals. Over the 90 days to 2026-09-09 the unified spine started 18,806 applications, all DF4W, against about 321,000 on the legacy monoliths (NDF2W 248,685, NDF4W and RO 71,995); the spine is 5.5% of volume, flat week over week, and DF2W is fully configured with zero applications ([workflow-gap.md §8](workflow-gap.md)). Every comparison of "Bravo's BPMN" with LORA in this document is therefore mostly a comparison with the monoliths, because that is what carries the book.

Service tasks bind to Spring beans exclusively via `camunda:delegateExpression` (483 bindings, 274 distinct bean names, 276 `JavaDelegate` classes all under `com.bfi.bravo.activity`); there are 0 `camunda:class`, 0 `camunda:expression`, 0 external-task workers, 0 execution or task listeners. All 483 service tasks execute inside the engine's job-executor threads, which are left at the Spring Boot starter defaults (core pool 3). The 3 DMN files are reachable only from the pre-MVP unsecured flow; one is referenced by nothing.

**LORA.** No master process. `GSMBELExecutor.Workflow` runs a Temporal `Selector` loop; on every document change `Planner.Next()` recomputes which of the 172 ProcessSteps have their ReadSet available, WriteSet writable and precondition true, and schedules them as parallel Temporal activities. There are zero imperative `ExecuteActivity` chains and only 3 hard precursors. Order is emergent from data dependencies.

**Assessment.** Bravo's order is explicit and readable by a business analyst in Camunda Modeler; LORA's order is implicit and, per LORA's own production findings, "hard to map back" for people who think in workflow terms (a spreadsheet is being built to visualise the readiness matrix). Bravo pays for legibility with 53 files whose gateways encode product, feature-flag and risk-type branching as strings; LORA pays for decoupling with a readiness matrix that lives in 154 Go files.

### 3.2 Where the loan lives (the "artefact")

| | Bravo | LORA |
|---|---|---|
| The record | `Application` JPA entity (444 lines) with `@OneToOne` to `Lead`, `Customer`, `Loan`, `Calculation`, `Asset`, `Referral`, `Simulation`, plus `newLoan`/`newAsset`/`newCalculation` shadow copies; jsonb `additionalInformation` | One `dp-ndf` JSON document per product family, 777 leaf fields (≈1,200 properties including object nodes), addressed by JSON path |
| Link to the engine | `application.process_id` UUID → Camunda process instance (65 migrations reference `process_id`) | Workflow ID = document ID; the document *is* workflow state |
| Where the engine keeps state | Camunda `ACT_RU_*` tables in the same PostgreSQL; history at `full` level, `historyTimeToLive: P90D` | Temporal event history (never `ContinueAsNew`) + ArangoDB checkpoints every 2 minutes while dirty |
| Audit trail | 31 history/audit tables; `application_status_log` written by a PostgreSQL trigger (`log_status`), generic jsonb-diff shadow tables via `history_update()` trigger; Camunda history purged after 90 days | Append-only field version chain in the document; Temporal history; NATS event stream |
| Idempotency | `@Version` optimistic locking on every `BaseEntity`; read-then-check duplicate guards with **no unique index on `application(lead_id)`**; `businessKey` not used on the main process | NATS KV idempotency for proxy calls; `mutable: false` write-once fields; `StoreInitialDocRevision` PK conflict is one of the wedge causes |

**Assessment.** LORA realised the GSM "one artefact" idea fully and it is the part of the design the assessment rated highest. Bravo has an aggregate root but the lifecycle is smeared across the entity, several assignment tables and the engine's runtime tables; after 90 days only the trigger-written status log can tell you what happened.

### 3.3 Milestones and status enforcement

| | Bravo | LORA |
|---|---|---|
| Status vocabulary | 30 `ApplicationStatus` values (`CAS`, `FOLLOW_UP`, `SUBMITTED`, `SURVEY_ASSIGNED`, `CA_ASSIGNED`, `BM_DONE`, `READY_FOR_GO_LIVE`, `GO_LIVE`, `DISBURSED`, `REPROCESS`, …) plus `UnderwritingStatus` (19), surveyor `AssignmentStatus` (25), operation `AssignmentStatus` (16), `CasConstants.AssignmentStatus`, `RiskType` (8) | 9 `$.status.application` values (`new → pre_qualified → pre_approved → approved → live → disbursed`, plus `rejected`, `expired`, `canceled`), 17 declared transitions; separate nested survey FSM |
| Who writes it | 197 `setStatus(` sites in 73 files; 53 write `Application.status` directly, including from an HTTP controller (`SalestraxController.java:74`). The target status is a **string literal in BPMN** (`<camunda:inputParameter name="statusToBeSet">Approved</camunda:inputParameter>`, 18 files) applied unconditionally by `SetApplicationStatusActivity` and its 3 product-specific copies | Activities write the field; 155 preconditions enforce ordering by convention |
| Central transition validator | A working graph state machine exists (`service/statemachine/AbstractSM.java`, Guava `ImmutableGraph`) but has **one** subclass, for `UnsecuredBooking`; and its `updateStateIgnoreException` swallows the violation | `AsStateValidator()` rejects unknown enum values only; the declared FSM table is not checked on write |
| Observed illegal transitions | Not measured | None observed in production |

**Assessment.** Both systems declare a lifecycle and neither enforces it at write time. LORA's is smaller (9 states) and lives on one field; Bravo's is larger and lives on at least four entities at once. This is the GSM leg the LORA assessment called "weakest", and Bravo shows the pure-workflow approach does not fix it either: the BPMN diagram *looks* like the transition graph, but 53 of the write sites bypass it.

### 3.4 Guards and the cost of adding a step

**Bravo.** Adding an automated check means: a new `JavaDelegate` in `activity/`, a new `serviceTask` plus a "Checkpoint" gateway in the right BPMN file, a `failedJobRetryTimeCycle` choice, usually a new `WorkflowConstants` key and a gateway condition, and, for the unified flow, a row in the `WorkflowSelectorActivity` configuration tables so the per-application on/off map (`ApplicationWorkflowConfig.workflowConfig` jsonb, `{"CI": {"PilotBranchCheckActivity": [true,false]}}`) knows about it. In-flight instances keep the old parent definition but pick up the latest child (§3.11).

The unified rewrite did add one genuinely data-driven element. `BaseActivity.execute()` (`activity/BaseActivity.java:79-129`) is a **skip gate**: before running, every unified activity looks up the per-application jsonb matrix in `ApplicationWorkflowConfig` (`{"CI": {"PilotBranchCheckActivity": [true,false]}, "SUO": {"SurveyActivity": [true,false]}}`) and runs only if its own flag is true for the current repetition index; the matrix is resolved from the six-column selector tables at start and re-resolved mid-flight for the "SUO" phase. So Bravo already has a boolean-per-activity guard layer sitting on top of the flowchart. It differs from LORA's guards in two ways: it can only *skip* a step the diagram already contains, never introduce or reorder one, and the flags are static per application rather than computed from data readiness. Versions of this matrix are shipped as SQL data migrations (`V2_0_2024040*__insert-*-workflow-config.sql`, `V2_0_202409101208__update-is-active-workflow-master-config.sql`, …).

**LORA.** A new Constructor with ReadSet/WriteSet and optional `SetPrecondition`; register it; the planner slots it in. No orchestration edit. The assessment verified this with 172 activities and 3 precursors. The production cost is the flip side: a new shared-planner activity hits every matching in-flight loan unless gated by `$.experiments.*`.

**Assessment.** This is the clearest LORA win and the reason the assessment says "do not revert to BPMN for scoring/checks". Bravo's `activity/` package being only 6.4% of the codebase suggests the automated pipeline was never the expensive part in either system.

### 3.5 Human tasks

This is where the two systems look most alike underneath.

| | Bravo | LORA |
|---|---|---|
| Wait mechanism | Camunda `userTask` used as an **anonymous latch**: 96 user tasks; the legacy files set `camunda:assignee="#{surveyAssignee}"` (21 sites) but every `unified-*` file has 0 `camunda:assignee`, 0 `candidateGroups`, 0 `formKey`, 0 timers. Outcomes are routed by a gateway on a `camunda:formData` field (`${surveyResult == "SUCCESS"}`). Completion is `taskService.complete(taskId, vars)` (48 sites) after a REST call has already mutated a domain table; 0 message correlation | 30-day async activity on the document workflow + a second `TaskWorkflow` per loan; completion via `CompleteActivity(token)`; 6-hour keepalive timer loop |
| Who does the work | Postgres tables: `surveyor_assignment`, `operation_assignment`, `underwriting_approval_approver`; eligibility from `surveyor_coverage`, `surveyor_level`, `underwriting_job_level_lov(_detail)`; roles from Keycloak enforced by a bespoke `@Authorize` AOP aspect (979 sites, 0 `@PreAuthorize`) | `lora-task-service` (89k LOC) stores FormDefinitions in ArangoDB; task managers per type (survey, review, mKYC, e-sign) |
| Assignment algorithm | Static coverage map + supervisor-tree walk with a visited set and `get(0)` (`SurveyorAssignmentAutoReassignScheduleServiceImpl.java:678-729`); no load balancing; CA is human-picked from a branch+product downline query | Assignment rules inside `setsurveydatabyassignmentrule`; reassignment as FSM transitions |
| Approval chain | Data-driven ladder: `underwriting_job_level_lov_detail` rows by `global_level` (CAFH 200 → AMB 300 → CCU 400 → GMB 600) snapshotted onto approver rows; renaming a role (BLCS-4683, NMH→GMB) touched one YAML line, one SQL `UPDATE`, zero Java. But the chain *rules* live in `BaseUnderwritingApprovalServiceImpl` (4,604 lines) behind feature flags (`featFinalApproverRoleOnReject`, `featSingleApproverRejectedRole`, …), see BLCS-4719 | `underwriting.go` 3,041 lines / 72 transitions; `AddTransition` tables + `pickTransition` switches |
| SLA / escalation timing | Not in BPMN. `@Scheduled` + ShedLock jobs with working-hours arithmetic (`0 0 8-17 * * 1-6`, Asia/Jakarta, 120-minute reassign interval) | Timers inside the task workflow (the 22–26% of Temporal Actions) |
| Code footprint | ~217k LOC, 44% of the service | ~12k LOC FSMs + 77 form builders + task-service |
| UI contract | `bravo-underwriting-console` (React) calls domain verbs (`PATCH /v1/underwritings/{id}/approval/bm-decision`, `PUT …/approver-decision`); the UI never sees a Camunda task id | Backoffice renders `FormDefinition` via templ; task inbox with `limit`; 416k RUM errors/week measured |

**Assessment.** Bravo did not use Camunda's task list, identity or timer features for human work; it built a CRUD application beside the engine and used user tasks as gates. LORA did not use `Workflow.await`; it built a second workflow and hand-written FSMs. In both, the orchestration paradigm turned out to be nearly irrelevant to the human-task layer, and that layer is the dominant maintenance cost. The LORA assessment's recommendation ("extract form routing into declarative config") applies to Bravo's 10k-line service classes just as well.

One Bravo-specific hazard: `SurveyorAssignmentServiceImpl.java:2547` completes a task by comparing against the modeller-generated literal `"Activity_0hqjmnn"`; renaming the element in the diagram silently breaks physical-document submission.

### 3.6 Failure handling, retry and compensation

This is where the comparison inverts the rationale's expectation.

| | Bravo | LORA |
|---|---|---|
| Retry policy | Per-task `failedJobRetryTimeCycle`, 186 declarations, 30 distinct values (`R5/PT1M` ×39, `R0/PT0M` ×39, `R3/PT1M` ×14, up to `R5/PT15M,PT30M,PT1H,PT3H,PT12H`); Camunda default 3 tries elsewhere. `R0/PT0M` on checkpoint gateways is deliberate: fail fast into an incident and park | One central `makeActivityOption`: `MaximumAttempts: 0` (unbounded), `MaximumInterval: 60s`, `NonRetryableErrorTypes: nil`. Backoff decays for ~63 s then polls flat forever |
| Terminal-error classification | Yes, two ways: `BpmnError`/`BpmnException` for business outcomes (routed to boundary events), and `OutboundAutoErrorHandlerEngineServiceImpl` which on the **last attempt** persists an error row and calls a per-activity `customErrorHandle` (50 implementations) that typically degrades, e.g. `AntiFraudEngineActivity` sets `WORKFLOW_ANTI_FRAUD_RESULT = BYPASS` | None. Zero `NewNonRetryableApplicationError` in `services/`. ~50,000 4xx/week retried as if transient; 4xx outnumber 5xx 111:1 |
| Dead letter | Camunda incident + `ApplicationErrorTracking` table with an operator console (`/v1/application-error-tracking`: assign-surveyor, assign-branch, cancel, send-salestrax → `setVariable` + `setJobRetries(…,1)`); `unified-pending-take-over` parks on a user task; RabbitMQ `.dead` queues with 7-day TTL | Undesigned: 1,269 force-cancel Jira tickets Jan–Aug 2026, ops cancels and re-originates from event 1 |
| Measured consequence | **≈0.44% of applications need a person to unstick them** (Jun–Aug 2026; 1,334 stuck-application tickets over 301,164 applications), **2,514 Jan–Aug**; no zombie-loan class, but 3.5× LORA's rate — and the figure excludes silent recoveries through the operator console, which raise no ticket (§3.14) | 47 loans wedged per 7-day window, 19 still burning daily, one at attempt 1,890; ~1,630 human interventions Jan–Aug; ≈0.2% of applications; 20–25 permanent wedges/month |
| Alerting | Slack (6 channels) + Google Chat, gated to last retry only (`CamundaErrorNotificationServiceImpl.java:35-39`) | Datadog monitor on >10 attempts exists but has the noisiest wedged-loan error excluded |
| Circuit breaking | None. 113 Feign clients, one with a `Retryer`, global `readTimeout` 300 s, default job-executor pool of 3 | None at activity level; gateway shares one route for ~300 upstreams |
| Compensation for external side effects | None. Create CIF has no pre-check for an existing `cifId` inside the activity, so a timeout-but-succeeded CONFINS call can create a second CIF; go-live failure is re-synced by a 5-minute sweeper | None. `golive_update_agreement` and `ro_update_cif` are among the wedged activities: external operations that could neither complete nor be reversed |
| Messaging reliability | `event_store` outbox (swept every minute, but only 2 of 7 publishers), `event_retry` inbox for messages that arrive before the application reaches the matching state, retry with `x-retries-count ≤ 5` held in an in-JVM scheduler (lost on pod restart); several listeners swallow exceptions with `log.error` only | 25 RMQ subscribers completing activities or pushing updates |

**Assessment.** The rationale said Temporal "handles backoff retries" and treated that as closing the topic. Bravo shows what a retry *policy* looks like when the engine forces you to write one: bounded attempts, fail-fast checkpoints, business-vs-transient error separation, graceful degrade, an operator queue. It is inconsistent (30 retry vocabularies, `PT4M` with no repeat count in 5 places, `retryFailedJob` uses `singleResult()` and grants one retry) and it is plumbing the rationale wanted to avoid, but it does not produce zombie loans. LORA's uncapped default is simpler and is the single largest source of its ops load. The LORA pack's own conclusion, "Temporal removes retry plumbing; it does not remove the need for a retry policy", is exactly the Bravo lesson.

The degrade-on-last-attempt pattern is double-edged: bypassing anti-fraud after three failures keeps the pipeline moving but is a credit-policy decision made by an exception handler.

### 3.7 Rework, rollback and reprocess

| | Bravo | LORA |
|---|---|---|
| Model | Return loops are modelled explicitly in BPMN (`unified-survey-returned.bpmn`, `unified-underwriting-ca.bpmn` return paths, statuses `UW_RETURNED`/`BM_RETURNED`). Full reprocess creates a **new `Application` row** chained via `prevApplication` and `currentIndex`, capped by `reprocessMaxLimit`; scoring and UW data are scoped per generation (~40 `currentIndex` reads) | Planner rollback: identify downstream readers of a changed field, revert their writes on the version chain, re-schedule, fast-forward unchanged inputs. Activities with irreversible effects opt out via `SetRetainDataOnRollback()` |
| Engine involvement | `ProcessInstanceModification` used live in one place, and only to force-terminate to hardcoded event ids (`"Event_1hx9v4v"`, `"Event_0z554j6"`, `"Event_0r02gct"`) inside a swallowing `catch`; 4 of 7 uses are commented out. Reprocess otherwise resets JPA fields and sets statuses backwards (`UnderwritingReprocessServiceImpl.java:42-88`) | Native to the planner |
| Production cost | **413 `Rescoring / Reproses` tickets Jan–Aug 2026** (OTRS), peaking at 91 in March; a further 145 `Reassign Application` and 128 `Request Take Application` (§3.14) | 287 rewind incidents at the survey/task-master seam ("event 15"); rewind and force-cancel tickets ≈705 rows |

**Assessment.** LORA's rollback is more principled for computed fields (the assessment's "milestone invalidation" praise stands). Bravo's "new row per generation" is crude but has a virtue LORA lacks: every generation is a durable, queryable record, and nothing has to replay Temporal history to reconstruct it.

### 3.8 Multi-product handling

| | Bravo | LORA |
|---|---|---|
| Products | NDF4W(1), NDF2W(2), DF4W(4), DF2W(11), NDF4W Sharia(10), DF2W Sharia(15), unsecured(9), pre-approval(3), plus RO and company variants | 7 product families, 7 root document schemas, 13 repos (`partnership-ndf`, `disburse-ssf`, `mou-heto-machinery`, …) |
| Discrimination mechanism | Five at once: numeric literals in `Application` (`isNDF4W() { return productId == 1L; }`, 18 predicates), YAML `productId → BPMN key` map, a 6-column DB selector (`WorkflowProductConfig(productId, type, customerType, userType, businessType, riskType)` → `WorkflowMasterConfig` → per-application jsonb on/off map), 31 Java factories, and string-typed gateway expressions in BPMN. Adding DF2W Sharia (product 15) touched all five behind per-product feature flags | Queue and workflow type derived from schema name; SKU logic in `…/ndf4w` / `…/ndf2w` packages; `$.experiments.*` for flags |
| Isolation cost | One service, one deployment, one job executor for every product; a BPMN change ships for all | 56 duplicated activity packages, 3 SDK versions, 4 zero-test repos; 6 of 7 families have no production APM presence |

**Assessment.** Bravo's per-product legacy BPMNs (`ndf4w.bpmn`, `ndf2w.bpmn`, `ndf4w-sharia.bpmn`, `ndf4w-ro.bpmn`) are the "flowchart explosion" the rationale predicted, and the unified rewrite replaced it with configuration tables plus gateway string-matching. LORA isolated products at the data layer at the price of fleet divergence. Neither is clean; LORA's problem is engineering consistency, Bravo's is that product identity is a magic number in five places.

### 3.9 Observability and operability

| | Bravo | LORA |
|---|---|---|
| Engine UI | Camunda Cockpit/Tasklist/Admin at `/camunda/**`, `permitAll()` at the Spring Security layer (engine authorization + Keycloak is the only gate) | Temporal UI (flooded), custom "Oh My LORA" diff inspector |
| "Which loans are stuck at survey?" | SQL over `surveyor_assignment.assignment_status` or Cockpit incident list; `ApplicationErrorTracking` table | Not a Temporal Visibility query (0 search attributes); works via Datadog APM spans by activity name and error type |
| Metrics | Micrometer/Prometheus on, but 0 custom process metrics (9 `@Timed` on outbound clients); no metric for incidents, stuck processes or per-activity duration | OTel spans per activity attempt with workflow id; 5 dashboards, 12+ monitors; bookkeeping is 63.5% of activity executions so business signal is diluted |
| Tracing | Jaeger dependency present, `NoopTracer` unless `JAEGER_ENABLE_TRACE=true`; Feign `loggerLevel: full` globally (PEFINDO/SLIK/Dukcapil/CONFINS bodies in JSON logs) | ~195k spans/day carrying a customer NIK in clear text (adjacent service) |
| Upstream attribution | Per Feign client, so attributable | ~300 proxies behind one gateway route; 21k 500s/week unattributable |
| Logs cost | Cloud Logging for the Bravo estate ≈Rp201M/month (more than LORA's whole GKE line) | Datadog |

**Assessment.** Bravo can answer fleet questions with SQL because state is relational; LORA needs APM. Bravo has essentially no process-level metrics and logs full request bodies; LORA has metrics but narrates its own bookkeeping. Both leak PII into telemetry in different ways.

### 3.10 Testing

| | Bravo | LORA |
|---|---|---|
| Inventory, service repo | 1,457 test files; 776 pure Mockito; **4** deploy and run a Camunda process (one against a production BPMN, `unified-anti-fraud-engine.bpmn`); a handful of H2 "parse tests" assert BPMN structure | 608 `_test.go`; 100 of 161 activity packages tested |
| Journey suite, separate repo | **`bravo-e2e-test`** (two squad clones): **595** Cypress/Cucumber `.feature` files, 28,268 steps, 600 commits by 46 authors; 349 files on `surveyor-platform`, 11 on `ndf2w`. 4 CI workflows; only `OPERATION_PLATFORM.yml` is scheduled (`cron 00 23 * * MON`) and **every step ends `\|\| true`, so it cannot fail**; covers 10 of 595 files. **Frozen 2023-11-21.** 82% of `Then`/`And` steps carry no assertion verb | `lora-super-test`: 150 scenario tests, mock interceptor, derived expectations, **a CI workflow with nowhere to run yet**; the partner nightly is red for 5 weeks |
| Can a test fail an upstream on demand? | **No** — `bravo-mock-service` (Mockoon) is static and shared, so 50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths are unexercised | **Yes** — per-run mock interceptor; a spec steers one answer with a 2-line delta |
| What is untested | No end-to-end walk from start to go-live; no test of retry exhaustion, incident creation, escalation across `callActivity`, or the expiry modification path | Product policy is not a merge gate; error-classification and unbounded-retry gates proposed |
| Coverage gate | None in `pom.xml` (JaCoCo `report` only, no `check`); Sonar server config only; `makefile` passes `-Dspring-boot.run.profiles` which surefire ignores | Test floor per repo proposed; 4 repos at zero |

**Assessment.** Both suites are large and both leave the orchestration layer itself untested. Bravo's Camunda test tooling (`camunda-bpm-assert`, process-test-coverage, `camunda-bpm-mockito`) is all in the pom and almost unused. The LORA testing complaint ("business logic cannot be tested, only schema at runtime") was assessed as overstated; the Bravo equivalent would be "the BPMN is the logic and nobody tests the BPMN".

**Amended 2026-09-11 — the closest structural parallel in this document.** Both organisations made a large, deliberate investment in journey testing and both ended with an artefact that gates nothing. Bravo wrote **595 Gherkin features across 46 authors** and stopped in November 2023, leaving its one scheduled workflow written so it could not report a failure. LORA wrote `lora-super-test` — a better-engineered harness, with a mock interceptor, derived expectations and a stub-drift check — and has **a CI workflow file with no runner to execute it**. The paradigms differ; this outcome does not, and neither team knew the other had reached it. Both corpora are recoverable assets rather than sunk costs: Bravo's 349 surveyor features describe the journeys behind 28.4% of its ticket load, and LORA's harness needs a machine, not a rewrite.

**One asymmetry that does follow from the architecture.** Bravo's boundary is 113 typed `@FeignClient` interfaces; LORA's is one gateway envelope naming a JSON schema. So Bravo gets stub-drift detection from `javac` where LORA needs a bespoke `check:stubs` script against a live registry — cheaper for Bravo. But LORA can make any upstream fail per test run and **Bravo cannot make one fail at all**, which is why Bravo's degrade paths, including the anti-fraud `BYPASS` credit decision, have never been executed by a test. A nine-layer remediation ladder for Bravo is worked out in [bravo-testing.md §7](bravo-testing.md).

### 3.11 Versioning and deployment of in-flight instances

| | Bravo | LORA |
|---|---|---|
| Mechanism | Spring Boot auto-deploys all 53 BPMN + 3 DMN at boot (no `deployment-resource-pattern`); Camunda versions each changed definition; an in-flight **parent** finishes on its old version, but because no `callActivity` sets `calledElementBinding`, every **child** it calls next resolves to the latest deployed version. That is the de-facto migration mechanism: redeploying a sub-process changes behaviour for running loans at their next call. 0 `ProcessInstanceMigration`. `camunda:versionTag` unmaintained (`0.0.1` ×23, absent ×26). Behavioural versioning lives in data instead: `WorkflowMasterConfig.workflowConfigVersion` + the per-application on/off matrix (§3.4), toggled by `featRefactorWorkflow` | Schema-versioned task queues (`dp-ndf-vX_Y_Z`); one worker deployment per schema version; 8 versions live at once (`v0-16` … `v0-22`), 5 of them idle but holding 82 cores / 154 GB |
| Risk | Structural edits to a parent are only safe for new instances, while edits to a child hit in-flight loans immediately with no migration plan; hardcoded activity ids used for forced termination (`"Event_1hx9v4v"`, …) break for instances on versions that lack them, and the failure is swallowed | Deterministic-replay constraints; old versions cannot retire until abandoned loans terminate |

**Assessment.** Both defer the hard problem. Bravo gets Camunda's built-in definition versioning free of infrastructure cost; LORA pays for version coexistence in pods.

### 3.12 Cost and scale

Numbers from the LORA cost document (GCP billing export + FinOps API, August 2026) and from a like-for-like pull of the Bravo orchestration tier made on 2026-09-09 after the Bravo team's objection (§8.5). All figures are GCP net cost in IDR for the complete month of August 2026.

**Like-for-like: orchestration tier against orchestration tier.**

| | Bravo LOS tier | LORA tier |
|---|---|---|
| What is in the tier | `ms-bpm` pods (Camunda + all human-task services) and its Cloud SQL instance `prod-postgres-bpm-d2bpm` | LPW/LTW workers, gateway, task service, schema service (GKE `squad:lora`), Temporal Cloud contract, ArangoDB licence and GKE |
| Monthly cost, prod | **≈Rp58M** (pods Rp5.3M + Cloud SQL Rp52.7M) | **≈Rp431M** (GKE Rp187.2M + Temporal Rp140.0M + ArangoDB licence Rp65.4M + ArangoDB GKE Rp38.9M; roughly half of task-service and ArangoDB GKE is SIT/UAT) |
| Non-prod copies | pods Rp12.1M; SIT/UAT/Sharia databases not pulled | inside the figures above |
| Applications, Aug 2026 | 76,446 (billing sheet) to ≈113k (engine meter: 338,858 process starts in 90 days) | 171,479 (billing sheet) to ≈135k (Temporal meter) |
| **Per application** | **≈Rp510–760** | **≈Rp2,500–3,200** |
| Not attributable to either | Memorystore Redis (Rp51M), in-cluster RabbitMQ, Keycloak, Cloud Logging (Rp140.5M prod), console hosting, and the ~26 `ms-*` data-plane services with ~50 Cloud SQL instances that **both** platforms call | same |

**The estate view the LORA cost document started from**, kept for reference: the two Bravo GCP projects bill ≈Rp1.87B/month, of which LORA's labels are ≈Rp226M and the remainder ≈Rp1.65B; Cloud SQL is Rp584M, Cloud Logging Rp201M, `bravo-project-nonprod` Rp573M. That remainder is not "Bravo LOS"; it is the shared BFI data plane plus non-prod, and LORA's 300 gateway proxies depend on it (§8.5).

**Assessment.** On the only fair basis, LORA's orchestration tier costs about 7× Bravo's in absolute terms and 4–5× per application. The reasons are not the paradigm: a fixed Temporal commitment, a fixed ArangoDB licence, 44 pods requesting 448 GB at 15.5% utilisation, and eight worker versions of which five are idle. Three of those four are **time-locked rather than merely wasteful**, which bounds how fast the gap can close: about **31% of LORA's node cost sits on a `Commitment v1: N2 Cpu in Jakarta for 3 Year` SKU**, so right-sizing requests releases the on-demand slice immediately and the committed slice only when that commitment is re-planned; the Temporal commitment was bought through the GCP Marketplace in **March 2026**, so it is renegotiable at **~March 2027** and not before; and the five idle worker versions cannot be retired at all while **~half of all loans never reach a terminal state** (a licence-plate reservation renews itself, so the workflow never ends and keeps its version pinned). The idle fleet is therefore a reliability defect presenting as a cost line. Bravo's tier is one deployment and one database, and that database alone costs more than LORA's ArangoDB compute. The migration still pays, because LORA's marginal cost per application is near zero and the Bravo LOS tier (≈Rp58–100M/month plus a second platform to staff) goes away, but the earlier claim that retiring Bravo saves ≈Rp1.6B/month is withdrawn: the data plane stays because LORA needs it. Two Bravo-specific costs remain worth noting: Camunda `full` history and 90-day retention on Cloud SQL are part of that Rp52.7M, and `ms-bpm` logs full request bodies into a Cloud Logging line that is not attributable but is large.

### 3.13 People and cognition

| | Bravo | LORA |
|---|---|---|
| Learning curve | Java/Spring/Camunda are commodity skills; BPMN is readable by analysts. The hard part is the 236k-LOC `service/` package and 5-place product logic | "You can get Java or Golang developers, but they won't be able to immediately read the code" (LORA production challenges). Custom SDK and planner; data-readiness thinking is unnatural |
| Team shape | 94 authors over 4.5 years, 20–23 active per year, one repo; squads split by LOS stage (Scoring and Underwriting owns this repo) | One document and one planner leave no seam for a UW/Surveyor team split; proposed fix is end-to-end teams per product family |
| Business legibility | The BPMN diagram is the business flow, but the truth is also in `WorkflowSelectorActivity` tables, feature flags and 197 `setStatus` sites | 9-status ladder is legible; the 155 preconditions that decide *when* are not, without a generated index |

---

### 3.14 Production ticket load and manual-intervention rate

*Added 2026-09-10 from the OTRS export `Compare_LOS_LORA.xlsx` (5,677 LOS + 4,184 LORA tickets, 2026-01-01 to 2026-09-09). Full derivation, category membership and caveats: [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md).*

This is the first dataset in the pack that measures the same thing, in the same system, over the same window, for both platforms. Two warnings carry into every row below. **August was a re-categorisation month on both queues** — LORA lost four ticket streams worth 248/month, which is more than its entire July→August decline, so its August total is a floor rather than a measurement. And **the rates divide a verified numerator by the billing sheet's disputed application counts**; the counts and trends need no denominator and are the firmer half.

| | Bravo (LOS) | LORA |
|---|---|---|
| Tickets Jan–Aug 2026 | 5,430 | 4,087 (3,217 excluding the customer/WhatsApp channels Bravo has no equivalent of) |
| Trend Jan→Aug, stable categories only | **×1.82 — rising while application volume fell** (118k→76k) | ×0.66 |
| Stuck-application tickets Jan–Aug | **2,514** | **1,453** — against ≈1,630 from Jira force-cancel + rewind, an independent cross-check within 11% |
| **Manual-intervention rate, Jun–Aug** | **≈0.443%** — 1 application in 225 | **≈0.126%** — 1 in 790 (published figure 0.18–0.22%) |
| Zero-intervention completion | ≈99.56% | ≈99.87% |
| Top single category | `Surveyor Platform - Release reject` — **1,542 tickets, 28.4% of all Bravo tickets**, grown 4.8× (65→315) and still climbing after normalising for volume (2.36→4.12 per 1,000) | `DBP Surveyor - Lainnya` ("other"), 809 (19.8%); largest *named* failure is `Kendala Assignment Tidak Muncul`, 347 (8.5%) |
| Load shape | Secular growth, no spikes | Single-month spikes that recover — a defect shipped and fixed |
| Concentration | 60 categories, top 5 = 53.9% | 42 categories, top 5 = 55.2% |

**Assessment.** Bravo's rate is about 3.5× LORA's, and the errors that are easiest to identify all push the same way: the billing sheet plausibly counts LORA-originated applications again in Bravo at go-live, which inflates Bravo's denominator; and Bravo's operator console lets staff unstick an application without ever raising a ticket, so its numerator is undercounted too. The one confound that flatters LORA is real — a platform being drained keeps the residual hard cases — and it is not controlled for.

**This does not overturn §3.6 or §5; it completes them.** Bravo has bounded, classified failure and no zombie-loan class, *and* it puts three and a half times as many applications in front of a human. Those are consistent: fail-fast checkpoints convert an invisible wedge into a visible ticket, which is a better operational posture and is exactly what a ticket queue counts. LORA's defect class is loans nobody sees; Bravo's is loans everybody sees, more often.

**And it turns on one unexplained category.** `Release reject` is 1,542 of Bravo's 2,514 stuck-application tickets. Remove it and Bravo's rate falls to 0.152%, level with LORA's 0.126%. No code path of that name has been mapped to a BPMN element or endpoint — `bravo-analysis` holds documents, not source. **Whether Bravo's intervention rate is 3.5× LORA's or level with it is currently a single open question**, and answering it is days of work for whoever owns the Surveyor Platform.

---

## 4. Where the two systems converge

Read side by side, the paradigms differ less than the rationale expected. The same five problems appear in both, in different clothes.

1. **Human-task complexity is paradigm-independent.** Bravo: 44% of code, three service classes over 4,600 lines each. LORA: ~12k lines of FSM inside the declarative shell. Neither engine's native task model was used.
2. **The lifecycle FSM is declared but not enforced.** Bravo has a state-machine class used once; LORA has an FSM table validated for enum membership only.
3. **No saga compensation.** Both rely on sweepers, re-sync and humans for failed external commits (CIF, agreement, go-live).
4. **Operations absorb the design gaps as tickets.** Bravo: `ApplicationErrorTracking` console, ~25 retry/reprocess/revive endpoints, Cockpit, and **2,514 stuck-application tickets Jan–Aug 2026**. LORA: 1,269 force-cancels, 705 rewinds, **1,453 stuck-application tickets over the same window**. Bravo designed its queue; LORA's emerged; both are the same order of magnitude and both are growing out of the human-task layer, not the engine (§3.14).
5. **The orchestration layer is untested in both — and both built a journey suite that no longer gates anything.** 4 of 1,457 Bravo tests run a process; LORA's nightly is red and its product-policy tests are not a gate. Beyond that, Bravo's 595-file Cypress corpus has been frozen since 2023-11-21 with its one scheduled workflow unable to fail, and LORA's `lora-super-test` has a CI workflow with nowhere to run ([§3.10](#310-testing)).
6. **The surveyor-assignment seam is the top ops complaint on both, in the same words.** 1,182 Bravo tickets (21.8% of load) and 1,021 LORA tickets (25.0%) are "assignment does not appear / cannot reassign / cannot take / cannot cancel". A BPMN flowchart and a GSM planner each modelled assignment around a hand-written service layer — `SurveyorAssignmentServiceImpl` at 10,419 lines, `survey.go` at 5,473 — and inherited that layer's failure modes at nearly the same rate. This is convergence #1 measured on both sides rather than inferred from code size (§3.14).
7. **Bravo drifted toward LORA on its own.** The 2024 unified rewrite replaced per-product flowcharts with one superset flowchart plus a per-application boolean matrix that decides which activities run (§3.4). That matrix is a static, hand-configured cousin of LORA's computed guards. The team arrived at "the data decides whether a step runs" without leaving BPMN; what it could not get from BPMN was "the data decides *when*", which is the part LORA's planner adds.

---

## 5. What each approach did better

**Bravo (pure workflow) did better at:**

- **Bounded, classified failure.** Fail-fast checkpoints, business errors as BPMN errors, transient errors retried a finite number of times, degrade on last attempt, alert on last attempt, park in an operator console. Inconsistent, but no zombie loans by construction. **This is a claim about the *shape* of failure, not its frequency** — Bravo's measured manual-intervention rate is ≈3.5× LORA's (§3.14). Bounded failure means the wedge is visible and recoverable, not that it is rare.
- **A designed dead-letter path.** `ApplicationErrorTracking` plus `setVariable` + `setJobRetries` is the "visible failure" LORA's reliability document asks for.
- **Fleet queries.** Relational state means "all loans stuck at survey" is a `WHERE` clause.
- **Durable reprocess generations.** `prevApplication`/`currentIndex` keeps every attempt as a row.
- **Commodity skills and readable order.** The happy path is eight boxes in one file.
- **Cheap version coexistence.** Camunda versions definitions; no extra pods.
- **Orchestration-tier cost.** ≈Rp58M/month for pods plus database against LORA's ≈Rp431M all-in, ≈Rp510–760 per application against ≈Rp2,500–3,200 (§3.12, §8.5).

**LORA (hybrid GSM + Temporal) did better at:**

- **Adding automated steps.** 172 activities, 3 precursors, no orchestration edits. The clearest validated win.
- **One artefact.** The whole loan in one schema-validated document with a version chain; 777 leaf fields with generated constants.
- **Parallelism for free.** ReadSet/WriteSet locking runs independent checks concurrently; Bravo has 5 parallel gateways in 53 files.
- **Principled rework for computed fields.** Rollback by dependency, not by resetting columns.
- **Product isolation at the data layer.** Separate documents and queues; Bravo has one job executor for everything.
- **Marginal cost.** Near-zero cost per additional application once the fixed footprint is paid; volume moved from Bravo to LORA adds almost nothing to LORA's bill. (The earlier bullet claiming ≈Rp2,300 vs ≈Rp21,900 per application is withdrawn; like-for-like, Bravo's orchestration tier is the cheaper one, §3.12.)
- **Observability of the automated pipeline.** Spans per activity attempt; Bravo has no process metrics.
- **Measured intervention rate.** ≈0.126% of applications need a person, against Bravo's ≈0.443% — 1 in 790 against 1 in 225 — and LORA's ticket load fell a third over eight months while Bravo's rose 82% (§3.14). Both figures rest on disputed application counts, and Bravo's excludes silent operator-console recoveries; the gap also turns entirely on one unexplained Bravo category.

---

## 6. Lessons across the boundary

For LORA, from Bravo:

1. **Write the retry policy Bravo was forced to write.** Bounded attempts or `ScheduleToCloseTimeout`, a terminal-error class for 4xx, and an explicit parked state with an operator surface. Bravo's `R0/PT0M` checkpoint idiom is the same idea as "convert an invisible wedge into a visible failure".
2. **Keep the degrade decision out of the exception handler.** Bravo's `customErrorHandle` bypassing anti-fraud after three failures is a credit decision hidden in error handling. If LORA adds terminal errors, decide explicitly whether a terminal error means "reject", "park" or "skip".
3. **Persist generations.** LORA's rewind-then-re-originate practice loses the history that Bravo keeps in chained `Application` rows.
4. **Measure the same KPI on both — done, and it is now the pack's sharpest comparison.** ≈99.87% zero-intervention for LORA against ≈99.56% for Bravo (§3.14). The remaining work is on the Bravo side and is worth days: `application_error_tracking` rows, reprocess and revive endpoint hits and Cockpit incident history would capture the interventions that never became tickets, giving Bravo the same two-source cross-check LORA already has.

For Bravo (or any future BPMN work), from LORA:

1. **One artefact, one status field.** Bravo's four overlapping status vocabularies are the real "scattered state" problem. A single lifecycle field with a write-time transition validator would be cheaper than the BPMN it duplicates.
2. **Stop encoding product and flags in gateway expressions.** LORA's schema-derived queues show product identity can be structural rather than a string compared in XML.
3. **Test the orchestration.** Bravo has `camunda-bpm-assert` and process-test-coverage in the pom and uses them in four files.
4. **Retire `full` history or shorten it.** Every variable write on 483 service tasks lands in `ACT_HI_DETAIL` on Cloud SQL, the single largest Bravo bill line.

---

## 7. Verdict on the rationale

The rationale's central claim, that GSM and Temporal are complementary layers and that a data-centric model beats a flowchart for the automated pipeline, is **supported** by the comparison: Bravo's flowcharts did explode, are sequential, and mix product routing into XML; LORA's planner adds steps without orchestration edits. The Bravo team's review (§8) establishes that the first two findings are consequences of how Bravo was modelled rather than laws of BPMN, and that the standard remedies exist. It does not change the finding, because the remedies are respectively 5.5% deployed, not started, and not enforced, and a paradigm is fairly judged by what teams build with it under delivery pressure.

Two of its assumptions are **not supported**. It assumed the execution layer would make retries and long waits a solved problem; Bravo shows a workflow engine that forces you to write a retry policy ends up with a better one than an engine that lets you skip it. And it did not anticipate that human-task complexity would return in either paradigm, which is where both systems spend most of their code.

The honest summary is that the paradigm choice decided the shape of roughly 6% (Bravo) to 10% (LORA) of the codebase, the automated pipeline, and decided it in LORA's favour. The remaining 90% (human tasks, integrations, status handling, operations) looks structurally similar in both, and the differences there come from engineering discipline, not from GSM versus BPMN.

---

## 8. Bravo team responses, reviewed (2026-09-09)

The Bravo team replied to rows 1–3 of §2. Each response was checked against the code; the rows were revised where the check supported the response. This section records the argument, the evidence, what changed, and what still stands.

### 8.1 "Flowchart explosion is an anti-pattern, not a paradigm flaw; keep the spine thin and delegate to modular children"

**The argument is correct as a statement about BPMN.** Nothing in the paradigm requires a 9,494-line file, and spine-plus-children is the standard mitigation. It is also not hypothetical for Bravo: the 2024 unified rewrite *is* this mitigation, an eight-step spine with 36 child processes.

**What the code says about whether it worked:**

| Metric | Legacy monoliths (13 files) | Unified spine + children (37 files) |
|---|---|---|
| Lines of BPMN | 29,111 | 8,536 |
| Service tasks | 380 | 82 |
| Exclusive gateways with more than one outgoing flow (business decisions) | 259 | 58 |
| Business decision gateways per service task | 0.68 | 0.71 |
| `conditionExpression` per service task | 1.41 | 1.33 |
| Escalation event definitions per service task | 0.13 | 1.67 |
| Feature-flag lookups inside gateway expressions (`environment.getProperty`) | 68 | 10 |
| Production share of started applications, 90 days to 2026-09-09 | ≈94% (NDF2W, NDF4W, RO, Sharia) | 5.5% (DF4W only; DF2W configured, zero volume) |
| Commits touching the files in 2026 | 57 | 39 |

Three readings follow. Modularisation cut the absolute size by 3.4× and the flag lookups by 7×, which is a real gain. It did not cut the *density* of branching: a unified service task still sits next to 0.7 business decisions and 1.3 conditions, the same as in the monolith, so the edge cases were partitioned, not removed. And it added a new kind of plumbing: the escalation return channel costs 1.67 escalation definitions per service task, 13× the legacy rate, plus the seven missing `camunda:out` mappings in Appendix C, a defect that can only exist once there are child processes to map from.

The larger point is operational. The mitigation has been in the codebase for two years and carries 5.5% of production volume, one product. The monoliths were changed more often in 2026 than the spine. The Bravo team's remedy is right and is being applied; the evidence that it scales to the whole book does not exist yet, and the present state is two generations running in parallel: two flowcharts, two error idioms, and a bridge from `ndf2w.bpmn` into unified underwriting.

**What changed in the document.** §2 row 1 now reads "observed in Bravo; a consequence of modelling practice, not a law of the paradigm; the mitigation exists and is unproven at scale". The earlier wording "the count of decision points did not fall" is replaced by the density figures above, and the 122 gateways named "Checkpoint" are no longer counted as decision points: 102 of them have a single outgoing flow and are transaction boundaries, not branches.

**What still stands.** "Constraining the spine to high-level orchestration" moves complexity down into children; it does not say where product and risk-type variation goes. In Bravo it went into the six-column selector tables, the per-activity on/off matrix and gateway strings (§3.4, §3.8). LORA's answer is a separate document and worker per product family. Both are legitimate; neither is "the flowchart stays simple".

### 8.2 "Camunda fully supports parallel execution; unlocking it is a product and engineering collaboration problem"

**The argument is correct about the engine.** Camunda 7 has parallel and inclusive gateways, message and signal events, event sub-processes and non-interrupting boundary events, all of which express concurrency and out-of-order arrival. Bravo's 14 parallel gateways and 4 inclusive gateways are a modelling choice, not an engine limit. The unified surveyor assignment already runs two human tasks concurrently through an inclusive gateway (`unified-surveyor-assignment.bpmn`), and the KYC, Pefindo, anti-fraud and dedupe checks in `unified-workflow-check.bpmn` are data-independent and could be forked today.

**Where the argument stops short.** The rationale's claim was not about fork/join parallelism but about *unplanned* order: data arriving whenever it arrives, and work starting whenever its inputs exist. BPMN can model that, but every interleaving has to be drawn: a message event or event sub-process per external signal, a non-interrupting boundary per "this may arrive while that is running". Bravo has zero of each, which is the plain reason the flows are sequential: nobody wanted to draw it. GSM does not draw it; the planner derives it from ReadSet/WriteSet. That is a paradigm difference. The "Speaking Engineer" method the Bravo team cites (LORA `people.md`, steps 1 to 8: classify every arrow as a data dependency, a human decision or an external event) is exactly the exercise that produces a readiness matrix rather than a wider flowchart, so adopting it would pull Bravo's modelling toward LORA's, not merely add gateways.

Two engine caveats apply to Bravo specifically if parallelism is adopted. Parallel branches become concurrent jobs on a job executor left at the starter default of three threads (§3.6). And none of the 14 existing parallel gateways carries `asyncBefore` on the join, the usual Camunda 7 guard against optimistic-locking failures when concurrent branches converge. Both would need fixing first.

Fairness to Bravo: LORA's parallelism benefit is asserted in its design and assessment, not measured. No LORA production document reports a latency or throughput gain from concurrent activities. The comparison is "Bravo does not model it" against "LORA gets it structurally", not "LORA measured a win".

**What changed in the document.** §2 row 2 now distinguishes the two claims: fork/join is a modelling choice Bravo could adopt; data-driven order is a paradigm difference.

### 8.3 "Relational DDD aggregate versus one document is a philosophy difference, not scattered data"

**The argument is correct as far as it goes**, and §2 row 3 already said the rationale's "scattered process variables" criticism does not describe Bravo. The relational aggregate has concrete advantages recorded in §3.9 and §5: fleet questions are SQL, sub-entities evolve independently (1,350 migrations), and there is no schema-version fleet to retire. The field count the Bravo team quotes for LORA is fair: `dp-ndf-v0_23_0` has 1,196 properties when nested object nodes are counted and about 910 leaf fields; the LORA assessment's "777 fields" counts leaves in v0_24_0 by a stricter rule. Whichever count is used, it is one large schema *per product family*, seven families in 13 repos, not one form for everything, so "forces all data into one giant form" overstates the LORA side as well.

**Where the argument turns against itself.** In Domain-Driven Design the aggregate root exists to enforce invariants: state changes go through it, and it refuses illegal ones. Bravo's `Application` is a Lombok `@Data` entity with generated setters, no hand-written behaviour and no transition method (`entity/Application.java:45-52`, zero domain methods). The lifecycle invariants live in BPMN string literals and 197 `setStatus` call sites across 73 files, including an HTTP controller (§3.3). A graph state machine exists in the codebase and is wired to one peripheral entity. That is the pattern the DDD literature calls an anemic domain model, and it is the actual finding behind "scattered": not that data is in 238 tables, but that the loan's lifecycle has no owner. Describing the model as DDD raises the bar the code is measured against rather than lowering it.

The document model does not automatically fix this either. LORA's status field is validated for enum membership only (§3.3). The difference is that LORA has one field to put a validator on; Bravo has four status vocabularies on four entities.

**What changed in the document.** §2 row 3 keeps the "partly refuted" verdict, now credits the relational aggregate explicitly, and names the anemic-aggregate point as the residual criticism. §1 and §3.2 give the field count as a range with both counting rules.

### 8.4 "LORA is just orchestration; comparing its cost with the whole Bravo estate is unfair"

**The argument is upheld, with one factual correction.** The LORA cost document compared LORA's all-in platform bill (≈Rp431M) with the "Bravo remainder" of the two GCP projects (≈Rp1.65B) and concluded LORA was 13–16× cheaper per application and that retiring Bravo was worth ≈Rp1.6B/month. Checking what LORA calls shows why that is not like-for-like: `lora-gateway-service` has 40 client packages behind ~300 proxy handlers, 26 of them Bravo platform services (agreement, master data, branch, customer/CIF, product, calculation, asset pricing, collateral, document, e-doc, document hub, doc renderer, agent, scheduling, notification, backoffice, partnership, insurance, KYC proxy, KYC sign, CNV, integration, rule engine, portfolio management, payment), plus the same Apigee scoring chain `bravo-bpm-service` uses with byte-identical paths (StrategyOne, one-obligor, AliCloud models, anti-fraud, BFI Connect). Production spans confirm it: `prod-ms-master` alone takes 620k LORA calls a week. The Bravo estate is mostly a shared data plane, and it does not retire when the Bravo LOS does.

**The factual correction.** LORA does not call `ms-bpm`, and it does not call any Bravo surveyor, operation, underwriting or approval service: zero references to `bpm` in any LORA repo, `ms-bpm` absent from the production upstream table, and the surveyor, operation and CA hosts appear only in BPM's own CORS allow-list. Those functions live inside `ms-bpm` and its consoles, and LORA re-implements them in `lora-partnership-task-ndf`, `lora-task-service` and `lora-backoffice-fe`. So the examples in the objection are wrong, and the principle is right.

**The like-for-like number.** Pulling only Bravo's orchestration tier from the FinOps API for August 2026: `ms-bpm` pods Rp5.3M in prod (Rp12.1M more in SIT/UAT) and the `prod-postgres-bpm-d2bpm` Cloud SQL instance Rp52.7M, so ≈Rp58M prod against LORA's ≈Rp431M all-in. Per application, ≈Rp510–760 against ≈Rp2,500–3,200. LORA's orchestration costs roughly 7× more in absolute terms and 4–5× more per application, for reasons the LORA documents already list: fixed Temporal and ArangoDB contracts, 15.5% utilisation of 448 GB of requests, and five idle worker versions.

**What changed in the documents.** LORA's `cost.md` gained a section "Orchestration against orchestration", its verdict table and recommendations were amended, the production-findings README rows were rewritten, and §1, §3.12 and §5 of this document now carry the tier-level figures. The 227× "retire Bravo" lever is re-sized to 8–14× (≈Rp58–100M/month). The slide decks derived from `cost.md` (CTO, developer and holistic-health decks) were regenerated with the tier-level figures the same day.

**What still stands.** LORA's cost is flat with volume, so finishing the migration still costs nothing at the margin and removes one platform. Temporal is still ≈5 cents per loan. And the comparison says nothing about the paradigm: the gap is provisioning and contracts, not GSM versus BPMN.

**How much of the gap is actually reachable, and when.** "A right-sized LORA could close it substantially" is true but slower than it sounds, and the levers are smaller than the one they are being compared against:

| Lever | Worth | Available |
|---|---|---|
| Retire the Bravo **LOS** tier | ≈Rp58M/month prod, ≈Rp70–100M with non-prod | when the migration finishes |
| Retire the five idle worker versions | share of 448 GB at 15.5% utilisation | **blocked** until abandoned loans terminate |
| Right-size pod requests | the on-demand 69% of node cost | now; the committed 31% only at CUD re-plan |
| Re-size the Temporal commitment | commit is ~52% larger than needed | **~March 2027** renewal |
| The whole Temporal Actions programme | **≈Rp7.2M/month** (~1.7% of LORA's bill) | now |

So the single largest cost action available to either team is still finishing the migration — but it is **8–14×** the Temporal work, not 227×, and LORA's own tier does not become cheaper than Bravo's by doing it. The Actions programme is worth doing for the renewal negotiation, not for this month's invoice.

### 8.5 Net effect on the verdict

None of the four responses moves the §7 conclusion on architecture, and two of them sharpen it. The fourth reverses a cost claim that was never part of the architectural verdict but was being quoted alongside it: on a like-for-like tier, Bravo's orchestration is the cheaper one today. The "flowchart explosion" and "sequential" findings are true of Bravo and are consequences of how Bravo was modelled, not laws of BPMN; the Bravo team's own remedies (thin spine, parallel gateways, an aggregate that owns its invariants) are the right ones and are, respectively, 5.5% deployed, not started, and not enforced. The pure-workflow approach *could* have avoided most of what §2 rows 1 and 2 describe, and did not. That is itself evidence about how the two paradigms behave under real delivery pressure, which is the only condition under which either will ever run.

---

## Appendix A. Bravo evidence index

| Topic | File(s) |
|---|---|
| Master process and call graph | `src/main/resources/bpmn/unified-main-workflow.bpmn`; `calledElement` targets across `src/main/resources/bpmn/*.bpmn` |
| Process roots and entry points | `controller/v2/ApplicationV2P1Controller.java:23-39`; `service/impl/v2/ApplicationV2P1ServiceImpl.java:441,641`; `activity/unified/operation/CreateOperationWorkflowUnifiedActivity.java:119`; `service/df2w/impl/Scoring2DF2WServiceImpl.java:192` |
| Delegate binding and skip gate | `activity/BaseActivity.java:26,47-129`; `activity/unified/GetApplicationWorkflowConfigUnifiedActivity.java:33-44` |
| Human-task completion helpers | `service/impl/CamundaServiceImpl.java:119-185` (`passUserTask`, `completeUserTask`, `completeUserTaskByRootProcessId`) |
| Product → process key | `src/main/resources/application.yaml:1364`; `service/impl/ApplicationServiceImpl.java:752-762`; `utils/ApplicationUtil.java:269-299` |
| Unified selector tables | `entity/workflow/WorkflowProductConfig.java`, `WorkflowMasterConfig.java`, `entity/ApplicationWorkflowConfig.java`; `service/impl/workflow/ApplicationWorkflowConfigMapServiceImpl.java:64-294` |
| Status enums and writes | `constant/ApplicationConstants.java:76-125`; `activity/SetApplicationStatusActivity.java:164-174,444`; `controller/SalestraxController.java:74` |
| Unused state machine | `service/statemachine/AbstractSM.java`; `service/unsecured/impl/StateMachine.java` |
| Aggregate root without behaviour | `entity/Application.java:45-52` (`@Data`, `@Builder`, no domain methods); `entity/common/BaseEntity.java:18-23` |
| Parallelism constructs | 14 `parallelGateway` (e.g. `ndf4w.bpmn` "Assigned Surveyor Created Task" forks, `unified-underwriting-ca.bpmn` `Gateway_P_*`), 4 `inclusiveGateway` (`unified-surveyor-assignment.bpmn`, `unified-survey-returned.bpmn`); no `asyncBefore` on any join |
| Unified vs legacy metrics (§8.1) | counts over `unified-*.bpmn` (37 files) vs the 13 legacy files; production share from `workflow-gap.md` §8.1–8.2 |
| Stage recovery | `entity/Application.java:59-60,265-266`; `service/impl/CamundaServiceImpl.java:479-491` |
| Human tasks and roles | `constant/ActivityIdConstants.java:36-81`; `annotation/AuthorizeAspect.java:37-76`; `service/impl/SurveyorAssignmentServiceImpl.java:2528-2559`; `service/impl/underwriting/BaseUnderwritingApprovalServiceImpl.java:3102-3189` |
| Approval ladder | `service/impl/underwriting/UnderwritingApprovalApproverServiceImpl.java:898-1042`; `db/migration/V2_0_202609031000__update-underwriting-job-level-lov-nmh-to-gmb.sql` |
| Surveyor SLA | `scheduler/SurveyorAssignmentScheduler.java`; `service/impl/surveyorassignment/SurveyorAssignmentAutoReassignScheduleServiceImpl.java:678-729`; `application.yaml:3213-3223` |
| Retry framework | `service/impl/OutboundAutoErrorHandlerEngineServiceImpl.java`; `service/impl/RetryLogServiceImpl.java`; `config/FailingOnLastRetryAspect.java`; `service/impl/CamundaErrorNotificationServiceImpl.java:27-39`; `service/impl/CamundaServiceImpl.java:333-339` |
| Operator console | `controller/application/ApplicationErrorTrackingController.java`; `service/impl/application/ApplicationErrorTrackingServiceImpl.java:136-231`; `controller/general/GeneralController.java:85-126` |
| Messaging | `config/rabbitmq/RabbitAdminConfig.java:46-156`; `connector/CommonListenerWithExchange.java:27-66`; `connector/CommonPublisherWithExchange.java:42-118`; `service/impl/application/ApplicationStatusUpdateServiceImpl.java:104-212` |
| Termination and expiry | `service/impl/LeadReserveServiceImpl.java:508-720`; `scheduler/ApplicationScheduler.java`; `scheduler/LeadReserveScheduler.java` |
| Engine config | `application.yaml:621-630`; `config/SecurityConfig.java:63-67`; `config/KeycloakIdentityProviderConfig.java` |
| Tests | `src/test/java/com/bfi/bravo/functional/*`; `pom.xml:855-890`; `makefile:10-33` |
| Audit | `db/migration/V1_0_202208051538__create-function-history.sql`; `V2_0_202401031042__create-application-status-log-table.sql`; `V1_0_59`/`V1_0_100`/`V2_0_202305181939` event-store migrations |

## Appendix A2. Bravo production sources

- `docs/production-findings/Compare_LOS_LORA.xlsx` — OTRS support tickets, both platforms, 2026-01-01 to 2026-09-09 (5,677 LOS + 4,184 LORA rows). Analysed in [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md).
- `docs/production-findings/Trend_Tiket_OTRS_LOS(BPM Bravo).pdf`
- 90-day `ms-bpm` PostgreSQL and Datadog measurements, per [workflow-gap.md §8](workflow-gap.md)

## Appendix B. LORA sources used

- `docs/design-rationale/README.md`, `gsm-vs-workflow-approach.md`, `hybrid-approach-gsm-workflow.md`
- `docs/assessment/README.md`, `architecture.md`, `engineering.md`
- `docs/architecture/guard-stage-milestone-foundations.md`, `application-status-lifecycle.md`, `temporal-workflows.md`, `overview.md`
- `docs/production-findings/README.md`, `reliability.md`, `cost.md`, `Current LORA challenges in Production.md`

## Appendix C. Bravo defects noticed in passing

Not the subject of this comparison, but found while reading and worth a ticket each.

| Finding | Evidence |
|---|---|
| Seven `callActivity` elements have `<camunda:in variables="all"/>` but no `<camunda:out>`, so child outputs never map back to the parent | `unified-workflow-survey.bpmn:7,14,80,87,138`; `unified-main-workflow.bpmn:229,238` |
| `setting.workflow.map` maps products 3, 4, 11 and 15 to `PREAPPROVAL`, `DF4W`, `DF2W`, `DF2W_Sharia`, none of which is a deployed process key; `startProcessInstanceByKey` on those values from `/v1` or `/v2` throws | `application.yaml:1364` |
| Deployed but unreachable: `Process_NDF4W_Scoring_1_Mock_Ro` and DMN `pefindo-dmn` | `ndf4w-scoring-1-mock-ro.bpmn`; `dmn/pre-mvp-unsecured-pefindo.dmn` |
| `unified-survey-returned.bpmn` is the only process without `camunda:historyTimeToLive` | the file's `<bpmn:process>` element |
| `AuthorizeAspect` parses `permissions` but only checks `roles`; an annotation with permissions and no roles authorizes unconditionally | `annotation/AuthorizeAspect.java:45-75` |
| Task completion by modeller-generated literal `"Activity_0hqjmnn"` instead of an `ActivityIdConstants` key | `service/impl/SurveyorAssignmentServiceImpl.java:2547` |
| `retryFailedJob` uses `singleResult()` and grants one retry; throws if an instance has two open incidents | `service/impl/CamundaServiceImpl.java:333-339` |
| No unique index on `application(lead_id)` behind a read-then-check duplicate guard that is retried by the engine | `service/impl/ApplicationServiceImpl.java:1521-1536` |
| Create CIF does not check for an existing `cifId` before calling CONFINS; a timeout-then-success can create a second CIF | `activity/unified/survey/CreateCIFUnifiedActivity.java:67-100` |
| RabbitMQ retry waits are held in an in-JVM scheduler after the message is acked; a pod restart during the 1-hour wait loses the retry | `connector/CommonListenerWithExchange.java:45-66`; `application.yaml:1845` |
| Several listeners swallow exceptions with `log.error(e.getMessage())` and no requeue | `connector/agreement/AgreementGoLiveResultListener.java:37-39`; `connector/confins/ConfinsStatusListener.java:70-74` |
| `PT4M` retry cycles with no `Rn` repeat prefix | `ndf2w.bpmn:1711,2208`; `ndf4w.bpmn:1735`; `ndf4w-scoring-1.bpmn:200`; `unified-pefindo-check.bpmn:22` |
| Job executor left at starter defaults (pool 3) under 260 `asyncAfter` checkpoints and 5-minute Feign read timeouts | absence of `camunda.bpm.job-execution.*` in all `application*.yaml`; `application.yaml:353-359` |
| Camunda web app `permitAll()` at the Spring Security layer; Feign `loggerLevel: full` globally | `config/SecurityConfig.java:65-66`; `application.yaml:359` |
| `makefile` passes `-Dspring-boot.run.profiles`, which surefire ignores; no JaCoCo `check` goal | `makefile:10-33`; `pom.xml:871-890` |
