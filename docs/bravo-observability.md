# Observability: stuck loans, per-activity failure, and what Bravo can actually see

**Audience:** Production, on-call, Squad LOS, Squad Scoring and Underwriting
**Findings under test:** Can Bravo query "all loans stuck in survey"? Are activity logs thin and untagged? Can Bravo tell which upstream is failing, or only that upstreams are unreliable? Is there proper monitoring? And is the log the only durable substrate?

**Method.** Datadog org `us5`, measured 2026-09-10. APM spans and logs on `env:prod service:prod-ms-bpm` over 7 days (and 2 days where per-activity grouping needed the indexed subset); the full monitor inventory matching `bpm`; the dashboard inventory; and RUM on the four production Bravo LOS consoles. Camunda history semantics and the PostgreSQL schema are from [workflow-gap.md §8–9](workflow-gap.md) and [compare-architecture.md §3.9](compare-architecture.md). **The `bravo-bpm-db` and `bravo-bpm-sharia-db` MCP servers failed to connect during this session**, so every SQL-shaped claim below is marked as *mechanism verified, volume not re-measured today*.

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [Stuck loans at fleet scale](#1-all-loans-stuck-in-survey--answerable-in-sql-invisible-in-telemetry) · **[The orchestration layer emits no spans](#2-the-orchestration-layer-emits-no-spans-at-all)** · [Logs are not thin — they are unjoinable](#3-logs-are-not-thin-they-are-unjoinable) · [Upstream attribution works](#4-upstream-attribution-works--and-this-inverts-the-lora-finding) · [38 monitors, none on the process](#5-38-monitors-none-of-them-on-the-process) · **[The 404 storm nobody is watching](#6-the-404-storm-nobody-is-watching)** |
| **3. What to do** | [The durable-substrate thesis](#7-the-durable-substrate-thesis-inverted) · [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| Bravo can query "all loans stuck in survey" | **True in SQL, false everywhere an on-call engineer looks.** `surveyor_assignment.assignment_status` is a `WHERE` clause and that is a genuine Bravo advantage over LORA. But no dashboard, monitor, SLO or APM view expresses it, the Camunda runtime tables purge at **90 days**, and `Application.lastStage` is `@Transient` — the current stage is not persisted at all. The capability exists; the practice does not. |
| …therefore stuck loans cannot be grouped at fleet scale | **Refuted, by a different route than expected.** Camunda's engine log lines carry `@activityName`, `@activityId` and `@processDefinitionId`, so failures **can** be ranked per BPMN activity today: `One Obligor Check` 5,583 errors in 48 hours, `PD Model Check NTB` 1,394. Nobody was doing it. |
| Activity logs are thin / untagged | **Refuted for the engine, confirmed for everything else — and the real defect is different.** The ~5% of log lines that come from the Camunda job executor are richly tagged, including the **process definition version**. The other ~95% are Spring stack traces with no process context. And **no log line carries the application or lead id**, so you can group failures by activity but you cannot join a failure to a loan. LORA's `@WorkflowID` *is* the loan id; Bravo has no equivalent. |
| We can tell which upstream is failing | **True, and better than LORA.** 25 upstreams resolve cleanly from `okhttp.request` spans by `@peer.hostname`, with status codes. One Feign client per upstream means attribution is structural. LORA puts ~300 proxies behind one route and cannot do this at all without an unreleased PR. |
| Upstream BFI services are unreliable | **Refuted, with the same shape as LORA's finding.** 20,802 outbound errors in 7 days and **not one 5xx in the top 20 rows**. Every attributable upstream failure is a 4xx: `401` from IAM (8,533), `404` from repeat-order (5,070), `400` from scheduling (3,508). These are contract and auth defects, not outages. |
| Bravo has no proper monitoring | **Refuted on count, confirmed on subject.** **38 monitors** match `bpm`. Every one watches a container, a JVM, an HTTP surface or a queue. **Zero watch a process instance, a Camunda incident, the job-executor backlog, or `application_error_tracking`.** Eight are in `Alert` right now; six read `No Data` and cannot fire. |
| Logs are the only durable substrate | **Refuted, and inverted.** Bravo's durable substrate is **PostgreSQL** — 238 entities, `application_status_log` written by a database trigger, reprocess generations chained as rows. Logs are the *least* durable layer here, and Camunda's own runtime history is the one that expires. This is the opposite of LORA, where the document plus Temporal history is durable and the logs last ~7 days. |
| Bravo's front ends are unmonitored | **Refuted — and this is the largest live defect in the document.** All four LOS consoles are RUM-instrumented at `ALL`. The Surveyor Platform emits **1,962,909 errors in 7 days**, of which **748,686 are HTTP 404s**, and the top one hits **54,350 of 79,090 sessions**. No alert can see it, because every success-rate monitor filters on `5*`. |

**The through-line:** Bravo's problem is not that the data is missing. Most of it is there, and in two places it is better than LORA's. The problem is that **every alert Bravo owns is scoped to the container and the 5xx**, so a system that fails by 4xx and by parking a process cannot trigger one.

---

## 1. "All loans stuck in survey" — answerable in SQL, invisible in telemetry

This is the question LORA cannot answer in Temporal at all — zero search attributes, zero query handlers. Bravo can, and the reason is architectural: business state is a relational aggregate, so *"which applications are sitting in surveyor assignment and for how long"* is a `WHERE` clause over `surveyor_assignment.assignment_status` (25 values) joined to `application`.

That advantage is real and this document does not diminish it. Three things bound it.

**The stage is not persisted.** `Application.lastStage` is `@Transient` ([compare-architecture.md §3.2](compare-architecture.md)); the current position in the flow is recovered from Camunda's runtime tables. So the SQL answer is *"stuck in this assignment status"*, not *"stuck at this BPMN step"*, and those differ whenever the step is one the assignment tables do not model.

**Camunda's history purges at 90 days.** `historyTimeToLive: P90D`, history level `full`. `act_hi_actinst` carries roughly 50M rows per 90-day window. After the window, only the trigger-written `application_status_log` can say what happened — which is a status ladder, not a step trace.

**Nobody has written the query down.** There is no dashboard widget, no saved query, no monitor and no SLO in the Datadog org expressing "applications stuck at stage X for more than N hours". The four `LOS Weekly Report Latency` dashboards and `Report Monthly Monitoring - Squad LOS` are per-service latency and success-rate views. The fleet question is answerable by someone who opens a psql session and knows the schema; it is not answerable by whoever is on call at 02:00.

**Grouping stuck loans at fleet scale, by contrast, does work today and nobody was doing it** — see the next two sections. That is the part of this finding that was simply wrong.

---

## 2. The orchestration layer emits no spans at all

Seven operation names cover every span `prod-ms-bpm` produced in 7 days:

| `operation_name` | spans / 7 d | What it is |
|---|---:|---|
| `repository.operation` | 1,412,356 | JPA/Hibernate |
| `spring.handler` | 990,256 | REST controllers |
| `okhttp.request` | 335,731 | outbound calls to upstreams |
| `servlet.request` | 335,010 | inbound HTTP |
| `http.request` | 84,743 | client, other |
| `scheduled.call` | 1,193 | `@Scheduled` / ShedLock jobs |
| `jakarta_rs.request` | 75 | — |

**There is no Camunda span.** No process instance, no service task, no `JavaDelegate`, no job execution. Grouping `spring.handler` by resource confirms it — the top twenty are all controllers (`PartnershipConfigurationController.getByApplicationId`, `SurveyorAssignmentFormTabV2Controller.findByAssignmentId`, …) and not one is an `*Activity` bean.

This is structural, not an oversight of sampling. All 483 service tasks bind via `camunda:delegateExpression` and run inside job-executor threads. Those threads are not started by an HTTP request, so the Java agent has no trace to attach to, and nothing in the codebase opens one. The consequence:

> **The 90% of Bravo's work that is the loan moving through the flow produces no trace.** APM sees the consoles talking to the database and the engine talking to upstreams. It does not see the process.

The contrast with LORA is exact and runs the other way from every other row in this document. LORA's Temporal SDK OTel interceptor emits **one span per activity attempt**, carrying `@temporalWorkflowID` (= the loan id), `resource_name` (= the activity), `@error.type` and the attempt number. That is how LORA found 47 wedged loans in a 7-day window with no code change. Bravo has no equivalent span, and if it had a wedged-process class it could not be found this way.

What Bravo has instead — and it is a genuine substitute for *ranking*, though not for *tracing* — is in the next section.

---

## 3. Logs are not thin. They are unjoinable.

Seven days, `env:prod service:prod-ms-bpm`:

| status | lines / 7 d |
|---|---:|
| `info` | 545,179 |
| **`error`** | **525,181** |
| `warn` | 45,775 |
| **total** | **1,116,135** |

**47% of this service's log volume is ERROR.** That number is not a reliability measurement; it is a formatting artefact, and both halves of that matter. Clustering the error stream gives 124 patterns, and the largest are individual Java stack-trace frames logged as separate lines — `at <pkg>.<class>.<method>(<file>.java:NNN)` ×1,571, `at org.springframework.…` ×874, `at java.base/…` ×66. A single exception produces dozens of ERROR lines. Worse, one Camunda job failure produces **two** lines at **two severities**: `ENGINE-14006 Exception while executing job` at `warn`, then `ENGINE-16004 Exception while closing command context` at `error`, for the same failure.

The consequence is that the error stream cannot be counted, and every log-based monitor built on it inherits that.

**But the engine lines are richly tagged.** The Camunda job executor writes MDC context on its own lines:

```
message: ENGINE-16004 Exception while closing command context: Error while invoking Ali Cloud for PD Model Check Response
status:  error
version: v2.93.53
@activityId:          Activity_PD_Model_Check_NTB
@activityName:        PD Model Check NTB
@processDefinitionId: NDF2W:127:542b74c3-ab85-11f1-ba59-16deca89b476
@processInstanceId:   5b477587-acd4-11f1-be7a-5a673f41da64
```

`@processDefinitionId` carries **the process key and its deployed version** (`NDF2W:127`), which is a genuinely better version dimension than LORA's task-queue proxy. And grouping by `@activityName` produces the per-activity failure table this pack said Bravo did not have — 48 hours, `env:prod`:

| BPMN activity | status | lines / 2 d |
|---|---|---:|
| **One Obligor Check** | error | **5,583** |
| PD Model Check NTB | error | 1,394 |
| KYC Check | warn | 1,377 |
| Publish User Information (Register Keycloak) | error | 789 |
| PD Model Check NTB | warn | 740 |
| Pilot Branch Check | warn | 597 |
| One Obligor | error | 434 |
| Retrive Pefindo Spouse Profile Activity | error | 326 |
| Request Go Live | error | 252 |
| Retrive Pefindo Profile Activity | error | 244 |
| Get Agreement Number | error | 150 |

That is ~4,750 activity-level failures a day, concentrated in one check. It took one query. **The claim "activity logs are thin" is refuted; the claim "nobody is looking" is not.**

### Two real defects the tagging does have

**Only ~5% of lines carry process context.** 17,333 lines in 48 hours match `@processInstanceId:*`, against ~319,000 total. Everything from the REST layer — which is where the consoles, the operator endpoints and every stack trace live — has no process context at all.

**No log line carries the application or lead id.** `@applicationId` was probed and is absent from the engine MDC. So the join is:

| Question | Bravo | LORA |
|---|---|---|
| Which activity fails most? | **yes** — `@activityName` | yes — `@ActivityType` |
| On which process version? | **yes** — `@processDefinitionId` | partly — `@TaskQueue` |
| Which loan is this failure on? | **no** — `@processInstanceId` is a Camunda UUID; resolving it to an application needs a database lookup against `application.process_id`, and only inside the 90-day history window | yes — `@WorkflowID` *is* the application UUID |
| How many times has this attempt been retried? | **no** — no attempt counter on the line | yes — `@Attempt` |

**That missing join is the finding.** Bravo can tell you *One Obligor Check is failing 2,800 times a day*. It cannot tell you *which 400 customers are affected* without leaving Datadog, and it cannot tell you whether those are 2,800 loans failing once or forty loans failing seventy times — the `CARDINALITY(trace_id)` test that separated LORA's fleet problems from its retry loops has no analogue here, because there are no traces on the engine path ([§2](#2-the-orchestration-layer-emits-no-spans-at-all)).

---

## 4. Upstream attribution works — and this inverts the LORA finding

Outbound calls carry `@peer.hostname` per Feign/OkHttp client, one client per upstream. Seven days, `okhttp.request`:

| Upstream | spans / 7 d |
|---|---:|
| `prod-ms-user-iam` | 86,066 |
| `prod-ms-employee` | 64,725 |
| `prod-ms-product` | 31,463 |
| `prod-ms-onboarding` | 29,200 |
| `prod-ms-master` | 27,954 |
| `prod-ms-branch` | 22,784 |
| `prod-ms-agent` | 13,872 |
| `prod-ms-scheduling` | 13,763 |
| `gateway.bfi.co.id` | 13,336 |
| `prod-ms-asset-pricing` | 13,135 |
| …15 more, down to `prod-ms-backoffice` (32) | |

**This is the view LORA does not have.** LORA's gateway routes ~300 inner proxies through one endpoint (`POST /proxy/inner/request-v1`), so 21,128 errors a week report as the same resource, and the fix — [PR 1246](https://github.com/bfi-finance/lora-gateway-service/pull/1246) — is merged but not in any release tag. Bravo gets per-upstream attribution structurally, from having 113 typed Feign clients instead of one generic proxy. Give the point to Bravo.

### The errors are entirely 4xx

| Upstream | status | errors / 7 d | distinct traces |
|---|---:|---:|---:|
| `prod-ms-user-iam` | **401** | **8,533** | 7,964 |
| `prod-ms-repeat-order` | 404 | 5,070 | 3,934 |
| `prod-ms-scheduling` | 400 | 3,508 | 3,081 |
| `prod-ms-agreement` | 400 | 926 | 449 |
| `private.prod.bfi.co.id` | 400 | 671 | 500 |
| `gateway.bfi.co.id` | 422 | 609 | 610 |
| `prod-ms-kyc-proxy` | 400 | 580 | 474 |
| `prod-keycloak-headless` | 404 | 287 | 240 |
| …12 more rows, all 4xx, down to 4 spans | | | |

**Not one 5xx appears in the top twenty** (floor: 4 spans). Roughly 20,800 outbound errors a week, all client-side.

Two things follow, and they are the same two LORA found from the other direction.

**"Upstream BFI services are unreliable" is not what the data says.** It says Bravo asks upstreams for things they will not give it. `401` from the IAM permission endpoint at ~1,200/day is an auth or token-lifetime defect in Bravo, confirmed by the log stream (`FeignException$Unauthorized … [GET] /permission/assigned … "code":"INVALID_KEY"` alongside `TokenExpiredException` ×176). `404` from repeat-order at ~720/day is a lookup for something that does not exist.

**The span:trace ratios say these are fleet-wide, not retry loops.** IAM is 8,533 errors across 7,964 traces — 1.07:1, i.e. every affected request fails once. LORA's equivalent table had rows at 10,442 spans in **2** traces. Bravo's failure mode is *many loans failing once*; LORA's was *two loans failing ten thousand times*. Both are worth fixing and they need completely different fixes: Bravo's is a defect affecting a broad population, LORA's was a retry policy. This is the clearest single illustration in the pack of what "bounded retry" buys and costs.

The only mild loop is `prod-ms-agreement` 400 at 926 errors over 449 traces (2.1:1) and `425` at 49/27.

---

## 5. 38 monitors, none of them on the process

Full inventory of Datadog monitors matching `bpm`:

| Category | Count | Examples |
|---|---:|---|
| Container / pod / JVM resource | 11 | POD & container CPU and memory ×8, `jvm.heap_memory`, `OutOfMemoryError: Metaspace`, faulty-deployment events |
| HTTP surface | 11 | success rate, error rate ×2, p90/average latency, Apdex, throughput anomaly, `Latency Get > 500ms`, `Latency NON Get > 1000ms` |
| RabbitMQ `BlockingQueueConsumer` failed-declare | 6 | one per environment: dev, sit, uat, prod, and three Sharia variants |
| SLO error budget | 3 | 7 d, 30 d, 90 d — all on the same SLO id `8531b563…` |
| Business / upstream log alerts | 5 | Check Pefindo Error, Negativelist (`checkNegativeV2`), `BranchAPIClient` error, CNV success rate, Palav callback |
| Test / scratch | 1 | `TEST- succes rate bpm` |
| **Process-level** | **0** | — |
| **Total** | **38** | |

**Nothing watches a Camunda incident, a stuck process instance, the job-executor backlog, `application_error_tracking` row growth, or a per-activity failure rate** — even though [§3](#3-logs-are-not-thin-they-are-unjoinable) shows the last of those is one query away.

Three pathologies, each with an exact LORA counterpart.

**Eight monitors are in `Alert` right now.** POD CPU and POD Memory for Squad Scoring and Underwriting; both latency monitors; all three SLO error-budget monitors (7/30/90 day); and the scratch `TEST-` monitor. A monitor that has been red long enough to be normal is not a monitor. LORA's [observability.md](../../lora-workspace/docs/production-findings/observability.md) found the same thing — a wedged-loan alert firing continuously into a chat room since January.

**Six monitors read `No Data` and cannot fire.** All four `prod-sharia-bpm` resource monitors (created 2026-05-04, they filter `service:prod-sharia-bpm` while the service is registered as `prod-sharia-bpm-sharia`), plus the CNV success-rate and Palav-callback formula monitors. This is precisely LORA's eight never-evaluated worker monitors, tag mismatch and all.

**The one business monitor filters out the engine's own error class.** The Pefindo monitor reads:

```
logs("service:prod-ms-bpm checkpefindov2 -status:(warn OR info) -\"ENGINE-16004\"")
  .rollup("count").by("service").last("5m") > 1
```

`ENGINE-16004` is Camunda's *"Exception while closing command context"* — the line that carries `@activityName` and the actual failure reason ([§3](#3-logs-are-not-thin-they-are-unjoinable)). It has been excluded, presumably because it was noisy. **The noise was the signal.** LORA's zombie monitor excluded `status must be [EXPIRED, READY_TO_RELEASE_DOCUMENT]` for the same reason and thereby suppressed its own worst failure class. Two teams, two platforms, the same reflex.

**Dashboards.** No dashboard in the org mentions `bpm` or `camunda`. Bravo LOS is covered by nine cloned `LOS Weekly Report Latency` dashboards, `Monitoring (LOS) - success rate production`, and `Report Monthly Monitoring - Squad LOS` — all per-service latency and 5xx. The process view is Camunda Cockpit, which is `permitAll()` at the Spring Security layer ([SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md)) and is not part of any on-call flow recorded here.

---

## 6. The 404 storm nobody is watching

All four production Bravo LOS consoles are RUM-instrumented at `rum_event_processing_state: ALL`. Seven days:

> **Added 2026-09-10 — naming the repositories behind these applications.** The top three rows are `bravo-surveyor-console`, `bravo-operation-console` and `bravo-underwriting-console`, delivered from the **`LN`** Jira project ([board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703)); the fourth is the customer-platform front end. This mapping was missing from the pack, which measured these consoles' *runtime* here while [bravo-testing.md](bravo-testing.md) and [compare-architecture.md](compare-architecture.md) bounded Bravo's *code* at `bravo-bpm-service` — so the same three applications were both measured and uncounted. All three ship `@datadog/browser-rum`, which is what produces the numbers below, and all three run 829 unit tests as a blocking PR gate ([testing §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)). **The finding is unchanged and remains the largest live defect in this document:** the instrumentation was there, the tests gate, and nobody read the errors.

| Console | Sessions | Views | **Errors** | Errors / view |
|---|---:|---:|---:|---:|
| **Surveyor Platform Prod** (`2f3ca103…`) | 79,090 | 953,115 | **1,962,909** | **2.06** |
| Operation Platform Prod (`2ce771bc…`) | 17,135 | 96,707 | 287,646 | 2.97 |
| Underwriting Platform Prod (`acde774e…`) | 15,628 | 205,666 | 124,422 | 0.60 |
| Customer Platform DF (`b75409da…`) | 2,594 | 31,412 | 38,221 | 1.22 |
| **Total** | **114,447** | **1,286,900** | **2,413,198** | **1.88** |

For scale: LORA's back-office front end produces 416,201 errors a week at ≈2.8 per view. Bravo's four consoles produce **5.8× that volume**, at a comparable per-view rate. Neither team was reading RUM.

Top error messages on the Surveyor Platform — the console behind `Surveyor Platform - Release reject`, which is 28.4% of Bravo's entire support-ticket load ([ticket-analysis.md §5.3a](production-findings/ticket-analysis.md)):

| Error | Count / 7 d | Reading |
|---|---:|---|
| **`Request failed with status code 404`** | **748,686** | **38% of all errors on this app — see below** |
| `csp_violation: 'https://surveyor.bfi.co.id/cdn-cgi/rum?' blocked by 'connect-src'` | 35,415 | Cloudflare RUM beacon; cosmetic, but it is drowning the stream |
| `intervention: Ignored attempt to cancel a touchmove event…` | 20,928 | Touch/scroll on tablets — surveyor devices |
| `Request failed with status code 400` | 12,796 | |
| `csp_violation: '…:443/cdn-cgi/rum?' blocked by 'connect-src'` | 10,573 | same beacon on the explicit-port origin |
| `Error getting location: "[GeolocationPositionError]"` | 10,365 | **surveyors cannot get a position** |
| `Unable to get current position` | 10,325 | same defect, second message |
| `Request failed with status code 401` | 7,402 | the browser-side face of the IAM 401s in [§4](#4-upstream-attribution-works--and-this-inverts-the-lora-finding) |
| `Network Error` | 6,828 | |
| `Cannot read properties of null (reading 'filter')` | 6,445 | real null dereference |

### The 404s are four endpoints, and they hit most sessions

| Endpoint | 404s / 7 d | distinct sessions |
|---|---:|---:|
| `/bpm/v1/partnership-configuration/feature-configuration` | **266,767** | **54,350** |
| `/bpm/v2/surveyor-assignment-form-tab/assignment/{id}` | 157,623 | 37,359 |
| `/bpm/v1/application-document-tracking` | 154,097 | 45,916 |
| `/bpm/v1/surveyor-assignment-manual-kyc/scoring/assignment/{id}` | 143,180 | 31,565 |
| `/surveyor/assignment-detail/{id}` | 21,125 | 14,754 |
| `/surveyor/assignment` | 14,565 | 11,287 |

**54,350 of 79,090 surveyor sessions — 69% — get a 404 from `feature-configuration`.** That is not a retry loop and not an edge case; it is the modal experience of using the Surveyor Platform. And the endpoint is the busiest one in the service: `PartnershipConfigurationController.getByApplicationId` is the top `spring.handler` resource at 73,056 spans in 48 hours.

**Why no alert fired.** Every success-rate monitor on `prod-ms-bpm` is written as `http.status_code:5*`:

```
(hits{service:prod-ms-bpm} - hits{service:prod-ms-bpm, http.status_code:5*}) / hits{service:prod-ms-bpm} < 99
```

A 404 is a success by that definition. Bravo's health model is **"not 5xx = healthy"**, which is the same category of assumption as treating a running workflow as a well workflow, and it is wrong in the same way: the system's dominant failure mode is invisible to the thing meant to detect failure.

**What this document cannot say.** Whether these 404s are benign (an optional configuration probed on every page, 404 meaning "no override") or a defect (a lookup that should resolve) is not determinable from telemetry. It has to be read off the controller. But at 266,767 a week across two-thirds of sessions, on the console that generates 28% of Bravo's support tickets, **somebody has to look**, and the geolocation failures on the same console (20,690/week) are the kind of thing that stops a survey being submitted at all.

---

## 7. The durable-substrate thesis, inverted

The thesis offered was *"logs currently serve as the only durable substrate."* For Bravo that is not merely wrong, it is upside down.

| Layer | Bravo | LORA |
|---|---|---|
| Business state | **PostgreSQL, 238 entities, 271 tables, indefinite** | ArangoDB document + Temporal history |
| Status history | **`application_status_log`, written by a database trigger (`log_status`) — durable** | append-only field version chain in the document |
| Prior attempts | **chained `Application` rows via `prevApplication`/`currentIndex` — every reprocess generation is a durable, queryable row** | rewind invalidates fields; the prior generation is reconstructed from Temporal history |
| Step-level trace | Camunda `act_hi_*`, **purged at 90 days** | Temporal event history, 30-day retention on closed workflows |
| Spans | **none for the orchestration layer** | 30 days, one per activity attempt |
| Logs | ~1.1M lines/week, 47% ERROR, no loan id | ~7 days, but carry `@WorkflowID` and `@Attempt` |

**Bravo's durable substrate is the database, and it is the best one either platform has for answering "what happened to this loan".** Every reprocess generation is a row. Nothing has to be replayed. This is the advantage the relational aggregate genuinely delivers, and it is why [compare-architecture.md §3.7](compare-architecture.md) credits Bravo's crude "new row per generation" over LORA's more principled rollback.

The thing that expires is the *step* trace, and it expires from the one place — Camunda's runtime history — where nothing else can reconstruct it, because there are no spans ([§2](#2-the-orchestration-layer-emits-no-spans-at-all)) and the logs have no loan id ([§3](#3-logs-are-not-thin-they-are-unjoinable)). So the accurate statement is:

> **Bravo's business facts are durable and its process facts are not.** At day 91 you can still say what status a loan reached and when. You cannot say which activity failed, how often, or why.

LORA is the mirror image: the loan document and its version chain are durable, but the fleet-level *business* question ("all loans stuck in survey") cannot be asked at all.

---

## Recommended actions

Ordered by value over effort. Items 1 and 2 are the ones that would have caught something.

1. **Look at the `feature-configuration` 404 (S, do this first).** 266,767 a week across 69% of surveyor sessions, on the busiest endpoint in the service, on the console generating 28% of Bravo's tickets. Read the controller, decide whether 404 is the intended "no override" response, and if it is, stop the client treating it as an error. If it is not, this is a live production defect that has been invisible because nothing alerts below 5xx.
2. **Add a 4xx clause to the success-rate monitors (S).** Every `prod-ms-bpm` health monitor is `5*`-only. Add per-resource 4xx rate monitors — at minimum on `401` from IAM (8,533/week), `404` on the four surveyor endpoints, and `400` on scheduling. Bravo does not fail with 5xx; it fails with 4xx.
3. **Build the per-activity failure monitor that already works (S).** `@activityName` grouping is live and untouched. A monitor on `service:prod-ms-bpm status:error @activityName:*` grouped by `@activityName, @processDefinitionId` is a five-minute change and would today read `One Obligor Check` at ~2,800/day. Give it an owner and a runbook entry before creating it — see the LORA lesson below.
4. **Un-exclude `ENGINE-16004` from the Pefindo monitor (S).** It is the line that carries the activity name and the failure reason. If the monitor is too noisy without the exclusion, the correct fix is a threshold or a per-activity group-by, not suppressing the informative half of the signal.
5. **Put the application id into the engine MDC (S–M).** One MDC key on the job-executor path turns Bravo's per-activity ranking into per-loan triage and closes the single biggest gap in [§3](#3-logs-are-not-thin-they-are-unjoinable). `application.process_id` already links the two; the log line just needs the business key on it.
6. **Fix the six `No Data` monitors (S).** Four Sharia resource monitors filter `service:prod-sharia-bpm` against a service registered as `prod-sharia-bpm-sharia`. Retag or delete. Two formula monitors (CNV, Palav) have never evaluated.
7. **Triage the eight monitors in `Alert` (S).** Three SLO error-budget monitors, two latency monitors, two pod-resource monitors and one scratch monitor are all red. Either the thresholds are wrong or the service is degraded; both need an answer, and a permanently red monitor trains people to ignore the channel.
8. **Trace the job executor (M).** A `@WithSpan` on `BaseActivity.execute()`, or the Camunda OpenTelemetry plugin, would give one span per service task with the process key, version, activity and instance — the LORA `RunActivity` equivalent. This is the single change that would make Bravo's orchestration visible in APM at all, and it also delivers per-activity latency, which no metric currently reports.
9. **Write down the stuck-loan SQL (S).** Bravo's real advantage — fleet questions are `WHERE` clauses — is unusable at 02:00 because nobody has saved the query. A notebook with "applications by stage and age", plus a monitor on the count over threshold, converts a capability into an operation.
10. **Read RUM in the weekly review (S).** Four consoles, 2.4M errors a week, instrumented all along, never consulted. Set a per-console error-per-view SLO; today the Surveyor Platform is at 2.06 and nobody could tell if it regressed.

**Do not create these alerts without an owner and a runbook entry.** The evidence in [§5](#5-38-monitors-none-of-them-on-the-process) is that Bravo already has 38 monitors, 8 permanently firing, 6 that cannot fire, and one that had its most useful error class filtered out. Adding a ninth red light to the same chat room reproduces the problem this document is describing.

---

## Plan: 30, 60, 90 days

Ten recommendations plus the runbook precondition, phased against ~10 person-days a month of Platform/SRE time and a slice of Squad S&U.

**Sequencing rule for this document: repair the alert channel before adding anything to it.** This document's own warning is that Bravo already has 38 monitors, 8 permanently in `Alert` and 6 that cannot fire, and that *"adding a ninth red light to the same chat room reproduces the problem this document is describing."* So recommendations 6 and 7 land in the first 30 days and recommendation 2 does not, even though it is the more valuable signal — it arrives in month 2, after the channel is worth alerting into and after the runbook table exists.

The one exception is recommendation 3: it is created in phase 1 **with its runbook entry and owner attached**, because it needs no new plumbing and is the first process-level monitor Bravo will ever have.

**Shared with other documents.** Recommendation 1 is also [bravo-delivery.md](bravo-delivery.md) rec 1 and [bravo-cost.md](bravo-cost.md) rec 5; recommendation 2 is also [bravo-testing.md](bravo-testing.md) rec 3; recommendation 10 pairs with [bravo-delivery.md](bravo-delivery.md) rec 3. Phased identically everywhere — do them once.

### Days 0–30 — one live defect, and a working alert channel

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Investigate the `feature-configuration` 404** — read the controller; establish whether 404 is the intended "no override" response | 1 | S&U | 2 d | A written answer. 266,767/week across 69% of surveyor sessions is explained |
| **Fix it** — resolve the lookup, or stop the client raising 404 as an error | 1 | S&U | 3 d | Surveyor Platform error volume falls measurably in RUM |
| **Triage the eight monitors in `Alert`** — 3 SLO error-budget, 2 latency, 2 pod-resource, 1 scratch (`TEST- succes rate bpm`) | 7 | Platform/SRE | 2 d | Each is fixed, re-thresholded or deleted. **Zero permanently-red monitors** |
| **Fix the six `No Data` monitors** — the four Sharia ones filter `service:prod-sharia-bpm` against a service registered as `prod-sharia-bpm-sharia` | 6 | Platform/SRE | 1 d | All evaluate, or are deleted as duplicates |
| **Un-exclude `ENGINE-16004` from the Pefindo monitor** — it is the line carrying `@activityName` and the failure reason | 4 | Platform/SRE | 0.5 d | The informative half of the signal stops being suppressed. Re-tune with a threshold or a group-by if it is noisy |
| **Build the per-activity failure monitor** — `@activityName` × `@processDefinitionId`, **with owner and runbook entry** | 3 | Platform/SRE | 1 d | `One Obligor Check` at ~2,800/day is a monitored number. Bravo's first process-level alert |
| **Put the application id into the engine MDC** | 5 | S&U | 3 d | An engine log line joins to a loan without a database lookup. This unblocks per-loan triage and makes recs 2 and 8 far more useful |
| **Write down the stuck-loan SQL** as a saved notebook | 9 | S&U | 2 d | "Applications by stage and age" is one click for on-call. Bravo's genuine architectural advantage becomes operable |

### Days 31–60 — see the orchestration, then alert on it

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Trace the job executor** — `@WithSpan` on `BaseActivity.execute()`, or the Camunda OTel plugin | 8 | S&U | 8 d | One span per service task with process key, version, activity and instance. The 90% of Bravo's work that is the process becomes visible in APM, with per-activity latency and a `CARDINALITY(trace_id)` loop test |
| **Alert runbook table** — severity, runbook entry and owner for every signal, retrofitted to the surviving old monitors | precondition | Platform/SRE | 2 d | No alert exists without an owner. This gates the next row |
| **Per-endpoint 4xx monitors** — 404 on the four surveyor endpoints, 401 from IAM, 400 on scheduling | 2 | Platform/SRE | 3 d | Bravo's actual failure mode is alertable for the first time |
| **RUM in the weekly review**, with a per-console error-per-view SLO | 10 | Platform/SRE + EM | 2 d | 2.4M errors a week across four consoles stops being unread. A regression is caught by a number |

### Days 61–90 — consolidate

No new observability work is scheduled. Phase 3 is spent on the deploy-safety and test items in [bravo-testing.md](bravo-testing.md), which consume this document's output: the job-executor spans from recommendation 8 are what make the two end-to-end process tests diagnosable when they fail.

**What to check at day 90:** that the monitors created in phases 1 and 2 have fired, been acted on, and are still un-muted. The failure mode this document describes is not missing tooling — it is a firing alert with no owner. Ninety days is long enough to tell whether that changed.

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| 4xx in the health model | A 404 storm on the busiest endpoint pages someone in five minutes instead of running for months at 266k/week. |
| Per-activity monitor | "One Obligor Check is failing 2,800 times a day" is a number on a dashboard, not a query someone happened to run. |
| Application id in the MDC | On-call goes from a loan number to its activity failures in one Datadog query, the way LORA on-call already can. |
| Job-executor spans | The 90% of Bravo's work that is the process becomes visible in APM, with per-activity latency and a `CARDINALITY(trace_id)` test that separates a broad defect from a loop. |
| Saved stuck-loan query | Bravo's genuine architectural advantage — SQL over relational state — becomes something the on-call rota uses, not something the architecture merely permits. |
| RUM in the weekly review | A surveyor console regression is caught by a number instead of by 315 `Release reject` tickets a month. |
| Monitors triaged | The alert channel means something again, which is the precondition for every other item on this list. |

---

## Related

- [bravo-testing.md](bravo-testing.md) — why nothing catches these before production
- [bravo-delivery.md](bravo-delivery.md) — the console layer these errors come from
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.6, §3.9 — retry policy and the observability comparison in code terms
- [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md) — `Surveyor Platform - Release reject`, 28.4% of ticket load, still unexplained
- [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) — why Cockpit is not a safe on-call surface today
- LORA [observability.md](../../lora-workspace/docs/production-findings/observability.md) — the same investigation on the other platform
