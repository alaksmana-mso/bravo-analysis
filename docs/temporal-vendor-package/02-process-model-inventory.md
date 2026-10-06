# 02. Process model inventory

All counts are from parsing every `.bpmn` and `.dmn` file under `src/main/resources` at tag `v2.94.11`. The parser is a plain XML walk; the counts are element counts, not tag counts. We are happy to send the model files under NDA.

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

Three patterns dominate the models and are worth calling out, because none of them has a direct Temporal equivalent:

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

The `environment.getProperty` pattern reads deployment configuration at decision time. In workflow code it cannot be read directly, because a workflow must be deterministic on replay. The 78 conditions would read the flag through an activity, or through a side-effect, or the flag would be fixed at workflow start. We would like Temporal's recommended pattern, since the same flag can change while an instance is in flight for days.

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

Consequence for Temporal: each user task becomes a wait in workflow code (a signal, an update, or an asynchronously completed activity), and the 48 `complete` and 24 `claim` call sites in our service become calls on the Temporal client. We keep our consoles and our task tables. We want Temporal's view on which wait primitive fits a one-year tail.

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

## 10. How the census maps to Temporal, and where the work is

There is no diagram converter for this move. Every model becomes Java workflow code. The mapping below is our own first reading; we want Temporal to correct it.

| BPMN today | Temporal construct | Our reading of the difficulty |
|---|---|---|
| 53 processes, 4 carrying live volume | about 60 workflow classes on the Java SDK | medium: the two legacy monoliths are 9,494 and 8,464 lines of XML |
| 483 service tasks, 272 delegate classes | activity methods; delegate bodies port near-verbatim, `DelegateExecution` becomes typed arguments and returns | **low, and the largest single block of work** |
| 513 exclusive gateways, 659 JUEL conditions | `if` and `switch` in workflow code | low per item, high in volume; 78 read configuration (see §4) |
| 56 call activities, propagate-all | child workflows, or plain method calls inside the parent | low |
| 96 user tasks | `Workflow.await` on a signal or update, or an async-completed activity | medium: the one-year tail and visibility matter more than the primitive |
| 186 retry cycles, 31 patterns | `RetryOptions` per activity: maximum attempts, backoff, non-retryable types | **low: the policy already exists per activity** |
| 88 `BpmnError` sites, 114 error codes | non-retryable `ApplicationFailure` subtypes caught in the workflow | medium |
| **108 escalation end + 82 escalation boundary events** | no equivalent; becomes typed return values or exceptions from child to parent, designed per process | **high** |
| **146 link throw + 48 link catch events** | no equivalent; a `goto` into shared terminal handlers, becomes structured control flow | **high** |
| 154 embedded sub-processes | inlined blocks or extracted child workflows | medium |
| 12 timers | `Workflow.sleep` or timer-bounded awaits | low |
| 3 DMN tables, 7 rules | plain Java, or evaluated inside an activity | low |
| 260 `asyncAfter` continuations | not needed; every activity is already a durable boundary | none |

**The hard part is concentrated.** Of the 384 escalation and link elements, 212 sit in the legacy monoliths. So do 205 of the 210 error definitions and 147 of the 154 sub-processes. The unified generation is 37 files and 8,540 lines; the legacy files are 30,294 lines, 78% of all BPMN by line.

| Element | Unified | Legacy | Legacy share |
|---|--:|--:|--:|
| BPMN lines | 8,540 | 30,294 | 78% |
| Service tasks | 82 | 401 | 83% |
| Exclusive gateways | 96 | 417 | 81% |
| User tasks | 24 | 72 | 75% |
| Call activities | 38 | 18 | 32% |
| Embedded sub-processes | 7 | 147 | 95% |
| Error definitions | 5 | 205 | 98% |
| Link events | 35 | 159 | 82% |
| Escalation events | 137 | 53 | 28% |
| Retry declarations | 29 | 163 | 85% |

That split is why the sequencing question in [06](06-scope-and-questions.md) matters as much as the element mapping. Porting the unified spine is a bounded job. Porting the two monoliths is where the estimate doubles.
