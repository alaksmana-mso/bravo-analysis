# Bravo LOS (pure BPMN workflow) vs LORA (hybrid GSM + Temporal)

**Question answered:** the LORA design rationale ([gsm-vs-workflow-approach.md](../../lora-workspace/docs/design-rationale/gsm-vs-workflow-approach.md), [hybrid-approach-gsm-workflow.md](../../lora-workspace/docs/design-rationale/hybrid-approach-gsm-workflow.md)) argued that a data-centric Guard-Stage-Milestone brain on a Temporal execution layer would beat "drawing branching flowchart arrows for every edge case". BFI already runs the same Loan Origination System the other way: `bravo-bpm-service` is a pure workflow-engine implementation on Camunda 7 BPMN. This document reads both codebases and compares what each approach actually produced.

**Method.** Code and configuration verification of `squads/Scoring and Underwriting/bravo-bpm-service` (checkout at `v2.93.43`, last commit 2026-09-07) against the LORA documentation set (`lora-workspace/docs`: design-rationale, assessment, architecture, production-findings, August to September 2026). Every Bravo claim below cites a file. LORA claims cite the LORA docs, which in turn cite LORA code and production data. Counts are `grep`/`find` over the checkout.

**Scope caveats, read first.**

- LORA's production-findings pack measured LORA in production (Temporal Cloud billing, Datadog). For Bravo we have code, git history and the GCP bill as recorded by the LORA cost document. We do **not** have Bravo's manual-intervention rate, incident counts or per-activity failure data. Where LORA has a measured number and Bravo has only a code-level mechanism, the table says so.
- "Bravo" in the LORA cost figures means the whole Bravo estate (Cloud SQL, ~50 upstream services, non-prod projects), not `bravo-bpm-service` alone.
- Bravo is being drained into LORA (applications fell from ~118k to ~76k per month between July and August 2026), so its unit economics are inflating for reasons unrelated to architecture.

---

## 1. The two systems at a glance

| | **Bravo LOS** (`bravo-bpm-service`) | **LORA** (`lora-workspace/services/*`) |
|---|---|---|
| Orchestration paradigm | Process-centric BPMN 2.0 on embedded Camunda 7.23 | Data-centric GSM planner (`GSMBELExecutor`) on Temporal Cloud |
| Language / runtime | Java 17, Spring Boot 3.5.16, one monolithic service | Go, 13 repos across 7 product families, shared `lora-process-sdk` |
| State store | PostgreSQL (Cloud SQL) via JPA: 238 `@Entity`, 271 tables, 1,350 Flyway migrations | One JSON document per loan in ArangoDB (`dp-ndf-v0_24_0`, 777 fields), held in Temporal workflow memory |
| Process model artefacts | 53 production BPMN files (largest `ndf4w.bpmn` 9,494 lines, `ndf2w.bpmn` 8,464), 3 DMN, used only by the pre-MVP unsecured flow, one unreferenced | No flowchart. 172 registered ProcessSteps with ReadSet/WriteSet, 155 `SetPrecondition` guards, 3 hard precursors |
| Automated step implementations | 225 classes implementing `JavaDelegate` directly, 276 including subclasses of the abstract bases, all in `activity/` (31,677 LOC, 6.4% of code) | 172 activity constructors + 301 schema-validated gateway proxies |
| Human-task code | ~217k LOC (43.6% of code): `SurveyorAssignmentServiceImpl` 10,419 lines, `OperationAssignmentServiceImpl` 8,177, `BaseUnderwritingApprovalServiceImpl` 4,604 | ~12k LOC of hand-written FSMs: `survey.go` 5,473 lines / 125 transitions, `bpkb_review.go` 3,421 / 79, `underwriting.go` 3,041 / 72; 77 form builders |
| Total size | 497,970 LOC main Java, 5,070 files; 1,457 test files | ~617k LOC Go across the workspace (gateway 164k, task-service 89k, task-ndf 78k, ndf 53k, sdk 24.5k) |
| External integrations | 113 `@FeignClient` interfaces, 2 RabbitMQ brokers, 14 listeners, 7 publishers | 301 proxies behind one gateway route, 25 RabbitMQ subscribers, NATS |
| Age and churn | First commit 2022-01-26; 39,668 commits; 94 authors all-time, 23 active in 2026; 5,479 release tags | Production since 2026; 8 concurrent worker versions (`v0-16` to `v0-22`) |
| Volume (Aug 2026, per LORA cost doc) | 76,446 applications (31%) | 171,479 applications (69%) |
| Platform cost (Aug 2026, per LORA cost doc) | ≈Rp1,625–1,677M/month whole estate; ≈Rp21,256–21,900 per application (inflating as volume drains) | ≈Rp402–437M/month all-in incl. Temporal and ArangoDB contracts; ≈Rp1,150–1,350 per application on GCP, ≈Rp2,347–2,546 all-in |

---

## 2. The design rationale's claims, checked against Bravo

The LORA rationale made five arguments against the workflow approach. Bravo is the concrete workflow approach it was arguing against, so each can be tested.

| # | Rationale claim | What Bravo shows | Verdict |
|---|---|---|---|
| 1 | Flowcharts need "branching arrows for every edge case"; complexity explodes | `ndf4w.bpmn` alone: 111 service tasks, 21 user tasks, 137 exclusive gateways, 48 sub-processes, 70 error definitions, in one 9,494-line file. The 2024 "unified" rewrite split it into 36 `unified-*.bpmn` files chained by 56 `callActivity` elements, but the count of decision points did not fall: 122 gateways are literally named "Checkpoint", and 240 exclusive gateways carry `asyncAfter` as transaction boundaries. Product routing is re-expressed inside gateway expressions as string-compared variables plus Spring property lookups (`environment.getProperty('setting.feature.config.featDF2W') == 'true' && applicationWorkflowSelectorType == "OPTION_DF2W"`) | **Confirmed** |
| 2 | Loan events are parallel and out-of-order; process-centric models handle this badly | Bravo's flows are almost entirely sequential: 4 `parallelGateway` in `ndf4w.bpmn`, 1 in `ndf2w.bpmn`, 0 in `unified-main-workflow.bpmn`. There are 0 message events, 0 signal events, 0 event-based gateways and 0 non-interrupting boundary events across all 53 files. An external event cannot be injected into a waiting process; it can only be reflected by a REST call that sets a variable or completes a task | **Confirmed** |
| 3 | In workflow tools the data "lives in scattered process variables outside the diagram" | Not how Bravo did it. Camunda holds only routing flags: 255 variable keys in `WorkflowConstants.java`, all decision booleans, scores and one `applicationId`. Business data is in 238 JPA entities with `Application` as aggregate root. What *is* scattered is **status**: 30 `ApplicationStatus` values plus ~105 other status enums, `OperationAssignment` carrying 7 parallel status fields, `SurveyorAssignment` 8+. The "current stage" is not persisted at all (`Application.lastStage` is `@Transient`); it is recovered by querying Camunda's active activity ids, and Camunda history is purged after 90 days | **Partly refuted, redirected.** The weakness is not scattered data but scattered *lifecycle state* with no single artefact |
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

Service tasks bind to Spring beans exclusively via `camunda:delegateExpression` (483 bindings, 274 distinct bean names, 276 `JavaDelegate` classes all under `com.bfi.bravo.activity`); there are 0 `camunda:class`, 0 `camunda:expression`, 0 external-task workers, 0 execution or task listeners. All 483 service tasks execute inside the engine's job-executor threads, which are left at the Spring Boot starter defaults (core pool 3). The 3 DMN files are reachable only from the pre-MVP unsecured flow; one is referenced by nothing.

**LORA.** No master process. `GSMBELExecutor.Workflow` runs a Temporal `Selector` loop; on every document change `Planner.Next()` recomputes which of the 172 ProcessSteps have their ReadSet available, WriteSet writable and precondition true, and schedules them as parallel Temporal activities. There are zero imperative `ExecuteActivity` chains and only 3 hard precursors. Order is emergent from data dependencies.

**Assessment.** Bravo's order is explicit and readable by a business analyst in Camunda Modeler; LORA's order is implicit and, per LORA's own production findings, "hard to map back" for people who think in workflow terms (a spreadsheet is being built to visualise the readiness matrix). Bravo pays for legibility with 53 files whose gateways encode product, feature-flag and risk-type branching as strings; LORA pays for decoupling with a readiness matrix that lives in 154 Go files.

### 3.2 Where the loan lives (the "artefact")

| | Bravo | LORA |
|---|---|---|
| The record | `Application` JPA entity (444 lines) with `@OneToOne` to `Lead`, `Customer`, `Loan`, `Calculation`, `Asset`, `Referral`, `Simulation`, plus `newLoan`/`newAsset`/`newCalculation` shadow copies; jsonb `additionalInformation` | One `dp-ndf` JSON document, 777 schema-defined fields, addressed by JSON path |
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
| Measured consequence | **Not measured.** Bravo's equivalent of the LORA number would be `ApplicationErrorTracking` rows + reprocess/revive endpoint hits + Cockpit interventions; none of this is exported as a metric | 47 loans wedged per 7-day window, 19 still burning daily, one at attempt 1,890; ~1,630 human interventions Jan–Aug; ≈0.2% of applications; 20–25 permanent wedges/month |
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
| Production cost | Not measured | 287 rewind incidents at the survey/task-master seam ("event 15"); rewind and force-cancel tickets ≈705 rows |

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
| Inventory | 1,457 test files; 776 pure Mockito; **4** deploy and run a Camunda process (one against a production BPMN, `unified-anti-fraud-engine.bpmn`); a handful of H2 "parse tests" assert BPMN structure | 608 `_test.go`; 100 of 161 activity packages tested; `lora-super-test` 150 scenario tests with no CI runner; nightly red for 5 weeks |
| What is untested | No end-to-end walk from start to go-live; no test of retry exhaustion, incident creation, escalation across `callActivity`, or the expiry modification path | Product policy is not a merge gate; error-classification and unbounded-retry gates proposed |
| Coverage gate | None in `pom.xml` (JaCoCo `report` only, no `check`); Sonar server config only; `makefile` passes `-Dspring-boot.run.profiles` which surefire ignores | Test floor per repo proposed; 4 repos at zero |

**Assessment.** Both suites are large and both leave the orchestration layer itself untested. Bravo's Camunda test tooling (`camunda-bpm-assert`, process-test-coverage, `camunda-bpm-mockito`) is all in the pom and almost unused. The LORA testing complaint ("business logic cannot be tested, only schema at runtime") was assessed as overstated; the Bravo equivalent would be "the BPMN is the logic and nobody tests the BPMN".

### 3.11 Versioning and deployment of in-flight instances

| | Bravo | LORA |
|---|---|---|
| Mechanism | Spring Boot auto-deploys all 53 BPMN + 3 DMN at boot (no `deployment-resource-pattern`); Camunda versions each changed definition; an in-flight **parent** finishes on its old version, but because no `callActivity` sets `calledElementBinding`, every **child** it calls next resolves to the latest deployed version. That is the de-facto migration mechanism: redeploying a sub-process changes behaviour for running loans at their next call. 0 `ProcessInstanceMigration`. `camunda:versionTag` unmaintained (`0.0.1` ×23, absent ×26). Behavioural versioning lives in data instead: `WorkflowMasterConfig.workflowConfigVersion` + the per-application on/off matrix (§3.4), toggled by `featRefactorWorkflow` | Schema-versioned task queues (`dp-ndf-vX_Y_Z`); one worker deployment per schema version; 8 versions live at once (`v0-16` … `v0-22`), 5 of them idle but holding 82 cores / 154 GB |
| Risk | Structural edits to a parent are only safe for new instances, while edits to a child hit in-flight loans immediately with no migration plan; hardcoded activity ids used for forced termination (`"Event_1hx9v4v"`, …) break for instances on versions that lack them, and the failure is swallowed | Deterministic-replay constraints; old versions cannot retire until abandoned loans terminate |

**Assessment.** Both defer the hard problem. Bravo gets Camunda's built-in definition versioning free of infrastructure cost; LORA pays for version coexistence in pods.

### 3.12 Cost and scale

Numbers from the LORA cost document (GCP billing export + FinOps API, August 2026), reproduced with its caveats.

| | Bravo estate | LORA |
|---|---|---|
| Applications, Aug 2026 | 76,446 | 171,479 |
| Monthly platform cost | ≈Rp1,677M (Cloud SQL alone Rp584M; Cloud Logging Rp201M; `bravo-project-nonprod` Rp573M) | ≈Rp402M all-in (GKE Rp163–197M + Temporal ≈Rp140M/12-month contract + ArangoDB) |
| Per application | ≈Rp21,900 (was Rp13,889 in July; inflating as volume drains) | ≈Rp2,347 all-in; ≈Rp1,150–1,350 GCP only |
| Cost shape | Fixed; flat while volume fell 35% | Fixed; 43× volume increase for 3% less spend Jun→Jul; 44 pods request 448 GB and use 15.5% |
| Engine-specific cost | Camunda `full` history in PostgreSQL, `P90D` retention, nightly one-hour cleanup window | Temporal ≈$0.051/loan; mean 126 Actions/loan, P95 191; 63.5% of activity executions are notify + checkpoint |

**Assessment.** The unit-cost gap is real but is mostly Cloud SQL, logging and a non-prod project, not the BPMN engine. The LORA cost document itself says the Temporal Actions programme is worth ~Rp7M/month against ~Rp1,625M/month for retiring Bravo, so the architecture comparison should not be read as a cost argument. What the comparison does support: a relational, full-history, single-database LOS at this volume is expensive to keep, and Camunda's `ACT_HI_*` growth on Cloud SQL is part of that bill.

### 3.13 People and cognition

| | Bravo | LORA |
|---|---|---|
| Learning curve | Java/Spring/Camunda are commodity skills; BPMN is readable by analysts. The hard part is the 236k-LOC `service/` package and 5-place product logic | "You can get Java or Golang developers, but they won't be able to immediately read the code" (LORA production challenges). Custom SDK and planner; data-readiness thinking is unnatural |
| Team shape | 94 authors over 4.5 years, 20–23 active per year, one repo; squads split by LOS stage (Scoring and Underwriting owns this repo) | One document and one planner leave no seam for a UW/Surveyor team split; proposed fix is end-to-end teams per product family |
| Business legibility | The BPMN diagram is the business flow, but the truth is also in `WorkflowSelectorActivity` tables, feature flags and 197 `setStatus` sites | 9-status ladder is legible; the 155 preconditions that decide *when* are not, without a generated index |

---

## 4. Where the two systems converge

Read side by side, the paradigms differ less than the rationale expected. The same five problems appear in both, in different clothes.

1. **Human-task complexity is paradigm-independent.** Bravo: 44% of code, three service classes over 4,600 lines each. LORA: ~12k lines of FSM inside the declarative shell. Neither engine's native task model was used.
2. **The lifecycle FSM is declared but not enforced.** Bravo has a state-machine class used once; LORA has an FSM table validated for enum membership only.
3. **No saga compensation.** Both rely on sweepers, re-sync and humans for failed external commits (CIF, agreement, go-live).
4. **Operations absorb the design gaps as tickets.** Bravo: `ApplicationErrorTracking` console, ~25 retry/reprocess/revive endpoints, Cockpit. LORA: 1,269 force-cancels, 705 rewinds. Bravo designed its queue; LORA's emerged.
5. **The orchestration layer is untested in both.** 4 of 1,457 Bravo tests run a process; LORA's nightly is red and its product-policy tests are not a gate.
6. **Bravo drifted toward LORA on its own.** The 2024 unified rewrite replaced per-product flowcharts with one superset flowchart plus a per-application boolean matrix that decides which activities run (§3.4). That matrix is a static, hand-configured cousin of LORA's computed guards. The team arrived at "the data decides whether a step runs" without leaving BPMN; what it could not get from BPMN was "the data decides *when*", which is the part LORA's planner adds.

---

## 5. What each approach did better

**Bravo (pure workflow) did better at:**

- **Bounded, classified failure.** Fail-fast checkpoints, business errors as BPMN errors, transient errors retried a finite number of times, degrade on last attempt, alert on last attempt, park in an operator console. Inconsistent, but no zombie loans by construction.
- **A designed dead-letter path.** `ApplicationErrorTracking` plus `setVariable` + `setJobRetries` is the "visible failure" LORA's reliability document asks for.
- **Fleet queries.** Relational state means "all loans stuck at survey" is a `WHERE` clause.
- **Durable reprocess generations.** `prevApplication`/`currentIndex` keeps every attempt as a row.
- **Commodity skills and readable order.** The happy path is eight boxes in one file.
- **Cheap version coexistence.** Camunda versions definitions; no extra pods.

**LORA (hybrid GSM + Temporal) did better at:**

- **Adding automated steps.** 172 activities, 3 precursors, no orchestration edits. The clearest validated win.
- **One artefact.** The whole loan in one schema-validated document with a version chain; 777 fields with generated constants.
- **Parallelism for free.** ReadSet/WriteSet locking runs independent checks concurrently; Bravo has 5 parallel gateways in 53 files.
- **Principled rework for computed fields.** Rollback by dependency, not by resetting columns.
- **Product isolation at the data layer.** Separate documents and queues; Bravo has one job executor for everything.
- **Unit economics.** ≈Rp2,300 vs ≈Rp21,900 per application, with the caveat that most of the gap is Cloud SQL and logging, not the engine.
- **Observability of the automated pipeline.** Spans per activity attempt; Bravo has no process metrics.

---

## 6. Lessons across the boundary

For LORA, from Bravo:

1. **Write the retry policy Bravo was forced to write.** Bounded attempts or `ScheduleToCloseTimeout`, a terminal-error class for 4xx, and an explicit parked state with an operator surface. Bravo's `R0/PT0M` checkpoint idiom is the same idea as "convert an invisible wedge into a visible failure".
2. **Keep the degrade decision out of the exception handler.** Bravo's `customErrorHandle` bypassing anti-fraud after three failures is a credit decision hidden in error handling. If LORA adds terminal errors, decide explicitly whether a terminal error means "reject", "park" or "skip".
3. **Persist generations.** LORA's rewind-then-re-originate practice loses the history that Bravo keeps in chained `Application` rows.
4. **Measure the same KPI on both.** The LORA pack proposes "percentage of applications completing with zero human intervention" and computes ≈99.8% for LORA. Bravo's equivalent is derivable from `application_error_tracking`, reprocess and revive endpoint calls and Cockpit incident history, and should be computed before anyone claims either platform is more reliable.

For Bravo (or any future BPMN work), from LORA:

1. **One artefact, one status field.** Bravo's four overlapping status vocabularies are the real "scattered state" problem. A single lifecycle field with a write-time transition validator would be cheaper than the BPMN it duplicates.
2. **Stop encoding product and flags in gateway expressions.** LORA's schema-derived queues show product identity can be structural rather than a string compared in XML.
3. **Test the orchestration.** Bravo has `camunda-bpm-assert` and process-test-coverage in the pom and uses them in four files.
4. **Retire `full` history or shorten it.** Every variable write on 483 service tasks lands in `ACT_HI_DETAIL` on Cloud SQL, the single largest Bravo bill line.

---

## 7. Verdict on the rationale

The rationale's central claim, that GSM and Temporal are complementary layers and that a data-centric model beats a flowchart for the automated pipeline, is **supported** by the comparison: Bravo's flowcharts did explode, are sequential, and mix product routing into XML; LORA's planner adds steps without orchestration edits.

Two of its assumptions are **not supported**. It assumed the execution layer would make retries and long waits a solved problem; Bravo shows a workflow engine that forces you to write a retry policy ends up with a better one than an engine that lets you skip it. And it did not anticipate that human-task complexity would return in either paradigm, which is where both systems spend most of their code.

The honest summary is that the paradigm choice decided the shape of roughly 6% (Bravo) to 10% (LORA) of the codebase, the automated pipeline, and decided it in LORA's favour. The remaining 90% (human tasks, integrations, status handling, operations) looks structurally similar in both, and the differences there come from engineering discipline, not from GSM versus BPMN.

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
