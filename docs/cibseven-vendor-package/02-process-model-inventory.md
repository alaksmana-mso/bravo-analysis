# 02. Process model inventory

All counts are from parsing every `.bpmn` and `.dmn` file under `src/main/resources` at tag `v2.94.11`. The parser is a plain XML walk; the counts are element counts, not tag counts. We are happy to send the model files under NDA, and to run any compatibility tooling you recommend against them.

## 1. Files and processes

| | Count |
|---|---|
| BPMN files | 53 |
| Executable processes (one per file) | 53 |
| Processes with `camunda:historyTimeToLive` set (all to 90 days) | 52 |
| Processes carrying a `camunda:versionTag` | 27 |
| DMN files / decisions / decision tables | 3 / 3 / 3 |
| Distinct process definition keys ever deployed to production | 90 (37 are retired keys no longer in the repository) |
| Process definition versions in production (all keys) | 3,750; the most-revised key has 141 versions |

The 53 processes split into two generations:

- **Legacy, per-product monoliths** (14 files): `ndf4w`, `ndf2w`, `ndf4w-ro`, `ndf4w-sharia`, `unsecured`, `pre-approval-scoring` and their operation/surveyor companions. These are large flat models. `ndf2w.bpmn` and `ndf4w.bpmn` are each several hundred elements.
- **Unified generation** (34 files): one spine, `unified-main-workflow.bpmn` (`Unified_Process_Main_Workflow`), which uses call activities to reach 32 child processes, one per domain step (KYC check, PEFINDO credit check, PD model, surveyor assignment, survey, underwriting BM, underwriting CA, operation, go-live and so on). This generation is where all new products are being built.
- Plus 5 shared helpers (`operation`, `schedule-selection`, `long-survey-scoring`, `multiasset-survey-scoring`, `ndf4w-scoring-1`).

## 2. Element census

| Element | Count | Notes |
|---|---:|---|
| Sequence flows | 2,214 | 659 carry a condition expression |
| Exclusive gateways | 513 | 99 declare a default flow |
| Parallel gateways | 14 | |
| Inclusive gateways | 4 | fork and join both present |
| Event-based gateways | 0 | |
| **Service tasks** | **483** | every one uses `camunda:delegateExpression`; 274 distinct Spring beans |
| **User tasks** | **96** | across 26 files; see §5 |
| Call activities | 56 | see §6 |
| Embedded sub-processes | 154 | used as scopes for error and escalation boundary events |
| Business rule tasks | 2 | `camunda:decisionRef`, binding `latest`, `mapDecisionResult=singleEntry` |
| Abstract (untyped) tasks | 5 | placeholders, no behaviour |
| Script tasks | 0 | |
| Send / receive tasks | 0 | |
| Manual tasks | 0 | |
| Multi-instance activities | 0 | |
| Transaction sub-processes, compensation | 0 | |

## 3. Events

| Event | Count |
|---|---:|
| Start events, none | 207 |
| End events, none | 225 |
| **End events, escalation** | **108** |
| **End events, error** | **104** |
| **Boundary events, error** (all interrupting) | **106** |
| **Boundary events, escalation** (all interrupting) | **82** |
| Boundary events, timer | 8 |
| Intermediate catch, timer | 4 |
| **Intermediate throw, link** | **146** |
| **Intermediate catch, link** | **48** |
| Message events | 0 (4 `bpmn:message` definitions exist but nothing references them) |
| Signal events | 0 |
| Conditional, compensation, terminate, cancel events | 0 |
| Distinct `bpmn:error` definitions | 114 |
| Distinct `bpmn:escalation` definitions | 97 |

Three patterns dominate the models. They are standard Camunda 7 semantics, and they are the behaviours a fork has to reproduce exactly:

1. **Error end event → error boundary event on the enclosing sub-process.** This is how a delegate that throws `BpmnError` (88 throw sites in Java) routes an application to a rejection or a manual-review path. 104 error end events, 106 error boundary events, 114 error codes.
2. **Escalation end event → escalation boundary event.** Used the same way for non-error outcomes, for example "send back to surveyor". 108 escalation ends, 82 escalation boundaries, 97 escalation codes.
3. **Link events** to keep large flat diagrams readable: 146 throw and 48 catch link events.

Timers are few and short: 12 fixed durations between 5 seconds and 60 minutes, and 1 duration expression.

## 4. Expressions

Every expression in the models is **JUEL** (`${...}` or `#{...}`). There is no FEEL and no scripting.

| Where | Count | What they do |
|---|---:|---|
| Sequence-flow conditions | 659 | compare process variables; 109 call a Java method |
| … of which call `environment.getProperty(...)` | 78 | read a **Spring `Environment` bean** inside the expression, to switch flow on a feature flag from configuration |
| … of which call `execution.hasVariable(...)` | 68 | guard against a missing variable before comparing it |
| … of which call a custom Spring bean method | 3 | `isRO2WSoaId(...)`, `validateROTele(...)` |
| `camunda:inputParameter` | 130 | mostly string literals such as a status to set; 4 are `camunda:list`; 2 are expressions |
| `camunda:outputParameter` | 109 | mostly literals mapped to a result variable |
| `camunda:assignee` on user tasks | 21 | all the same expression, `#{surveyAssignee}` |
| Timer duration expression | 1 | `${scheduleSelectionWaitDuration}` |
| Call activity `calledElement` expressions | 0 | all static keys |

Representative conditions, verbatim:

```
${execution.hasVariable('bureauRacResult') && bureauRacResult == 'NOT_PASS'}
${environment.getProperty('setting.ndf2w.feat2WRegular') == "true" && isRegular == true}
${creditModelPersonaOverlay == "LOW" || (environment.getProperty('setting.feature.config.featHighRiskJourney') == 'true' && creditModelPersonaOverlay == "HIGH")}
```

The `environment.getProperty` pattern reads a **Spring bean** from inside a gateway condition. It works because the engine is embedded and resolves Spring beans in expressions. It appears in 78 conditions. We need it to keep working unchanged, and we want CIB seven to confirm that no default expression restriction, now or planned, blocks bean method calls in BPMN conditions.

## 5. User tasks

| | Count |
|---|---:|
| User tasks | 96, in 26 of the 53 files |
| With `camunda:formKey` or `formRef` | 0 |
| With embedded `camunda:formData` fields | fields total 89 (generated-form fields; not rendered by any client of ours) |
| With `camunda:assignee` | 21 (expression `#{surveyAssignee}`) |
| With candidate users / groups, due date, priority | 0 |
| Task listeners | 0 |

The user tasks are **wait states, not forms**. Our own consoles show the work and call a domain endpoint on `ms-bpm`; the service then finds the task by process instance and task definition key and completes it through `TaskService`. Assignment is set from a variable or by our code, and claim/complete is driven by our API. No Camunda form technology is used and Tasklist is not the operator's tool.

Consequence for a fork: none expected. Our service completes tasks through `TaskService`, which CIB seven keeps. We do not need its forms or its task-list web client.

## 6. Call activities

| | Count |
|---|---:|
| Call activities | 56 |
| `calledElementBinding` | all `latest` (56) |
| `camunda:in variables="all"` | 56 |
| `camunda:out variables="all"` | 49 |
| Business-key propagation, local scope, `sourceExpression`, tenant id, variable-mapping delegate | 0 |

Every call activity passes every variable in and every variable out. The unified spine is built entirely this way: one parent, 32 children, all variables shared.

## 7. Job configuration and transaction boundaries

| Attribute | Count |
|---|---:|
| `camunda:asyncAfter="true"` | 260 |
| `camunda:asyncBefore="true"` | 9 |
| `camunda:exclusive="false"` | 7 |
| `camunda:failedJobRetryTimeCycle` | 186 declarations, 31 distinct patterns |
| `camunda:jobPriority` | 0 |

The most common retry patterns are `R5/PT1M` (39) and `R0/PT0M` (39, meaning fail immediately and raise an incident), then `R3/PT1M` (14), `R3/PT3M` (7), `R5/PT5S` (8) and a long tail of custom back-off lists such as `R6/PT15S,PT30S,PT1M,PT1M,PT3M,PT5M`. The asynchronous continuations are placed deliberately after external calls so that a failed call becomes a retryable job with an incident rather than a rolled-back transaction.

## 8. DMN

| | Value |
|---|---|
| Namespace | DMN 1.3 (`https://www.omg.org/spec/DMN/20191111/MODEL/`) |
| Decisions | 3: `pefindo-dmn`, `pefindo-izidata-dmn`, `ekyc` |
| Decision tables | 3, all hit policy **FIRST** |
| Rules | 7 in total |
| Input expressions | 41, all with the default expression language (Camunda 7 default, JUEL for input expressions) |
| Literal expressions, required-decision links, DRDs | none |

The DMN footprint is small. The decision tables are evaluated from the 2 business rule tasks; there is no direct `DecisionService` call from Java.

## 9. Extension elements not used

For completeness: no `camunda:executionListener`, no `camunda:taskListener`, no `camunda:script`, no `camunda:connector`, no `camunda:field` injection, no `camunda:properties`, no `camunda:formKey`, no external-task topics (`camunda:type="external"`), no tenant ids, no candidate groups. This is a simpler surface than the file count suggests.

## 10. What the model census means for a move to CIB seven

The models should not change. They use the `camunda:` extension namespace, which we understand CIB seven accepts as-is. No element above is outside standard Camunda 7.

So the question is not conversion. It is **behavioural equality**. The elements we most need to behave exactly as they do on Camunda 7.23 are, in order of risk to us:

1. **Job execution and retries:** 260 `asyncAfter`, 9 `asyncBefore`, 186 retry cycles with custom back-off lists, incident creation on exhaustion.
2. **Error and escalation propagation** across embedded sub-processes and call activities: 104 + 106 error elements, 108 + 82 escalation elements.
3. **JUEL resolution:** 659 conditions, including Spring bean calls and `execution.hasVariable`.
4. **Call activities** with `latest` binding and all-variable propagation, while new definition versions are deployed under running parents.
5. **Inclusive gateway joins** (4) and **link events** (194).

We would like CIB seven to tell us where its engine differs from Camunda 7.23 in any of these, and what is fixed in CIB seven that was broken in 7.23.

## 11. The Sharia release line, in brief

The Sharia deployment runs an older branch on Camunda 7.17 (see [01](01-system-overview.md)). Its model set is a subset of the main line's and uses the same patterns. Counted the same way at release `v2.53.108`:

| | Sharia line | Main line |
|---|---:|---:|
| BPMN files / processes | 39 | 53 |
| Service tasks (all `delegateExpression`) | 385 | 483 |
| Distinct delegate beans | 213 | 274 |
| User tasks | 71 | 96 |
| Call activities | 31 | 56 |
| Exclusive / parallel gateways | 382 / 14 | 513 / 14 |
| Conditions (of which `environment.getProperty`) | 519 (52) | 659 (78) |
| Error end / error boundary events | 93 / 95 | 104 / 106 |
| Escalation end / escalation boundary events | 74 / 50 | 108 / 82 |
| Link throw / catch events | 106 / 36 | 146 / 48 |
| `asyncAfter` / retry-cycle declarations | 196 / 150 | 260 / 186 |
| DMN files | 3 | 3 |

No script tasks, listeners or multi-instance on either line.
