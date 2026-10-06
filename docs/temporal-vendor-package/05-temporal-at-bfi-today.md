# 05. Temporal at BFI today

Temporal is not new to BFI. This section sets out what already runs, so that the assessment starts from our real operating experience rather than from a greenfield assumption. Figures are from our Temporal Cloud namespaces on 2026-09-23 and from the repositories on 2026-10-02.

## 1. The account

- **Temporal Cloud**, region `ap-southeast-1`, bought through the Google Cloud Marketplace in March 2026 as a prepaid annual commitment.
- Namespaces in use: `lora-prod`, `lora-sit`, and `agreement-sit` (the Java pilot below). Authentication is by API key per namespace.
- Observability: Datadog, with the Temporal SDK metrics and a tracing interceptor in the Go services.

## 2. LORA: a second loan origination platform, in Go, in production on Temporal for about a year

LORA is BFI's other loan-origination platform. It is built in Go on a custom in-house workflow SDK (`lora-process-sdk`) over the Temporal Go SDK, and it runs a data-driven process model rather than BPMN. It is relevant here because it is the same company, the same kind of workload, and the same Temporal account.

| Measure | Value |
|---|---|
| Go services on the Temporal Go SDK | 8, on SDK versions 1.34 to 1.48 |
| Namespace `lora-prod`, Running workflow executions | about 49,000 (23,000 loan-process workflows, 26,000 task-master workflows) |
| Starts per day on the current version | about 5,000; completions about 3,000 |
| Peak Running per version at a version handover | about 22,000 |
| Completed-duration profile | 53% over 24 h, 42% over 7 days, 9% over 14 days |
| Versioning model | one task queue per deployed version (`dp-ndf-v0_NN_0`); old versions drain over about three weeks |

LORA's loans are long-running in the same way Bravo's are: they park on a survey or a document for days, with no pending workflow task and no timer, and they complete slowly.

## 3. What a year of LORA taught us, and what it means for this assessment

These are our own findings, from our own namespaces. They are the practical questions we will bring to the first call.

1. **Worker memory is the sticky cache.** Worker pods ramped to a plateau equal to the default 10,000-entry sticky cache times about 0.75 MB per workflow, and one worker type was OOM-killed repeatedly. We now size workers as `0.75 MB × cache size + 0.3 GB + 25%` and set the cache per deployment. For Bravo, with 1.1 million open engine instances today, cache sizing and the "parked workflows do not enter the cache" behaviour decide the worker fleet. We want Temporal's guidance on this for a Java worker holding long-lived, mostly idle workflows.
2. **Retry policy defaults cost real money and real noise.** LORA ran with a 60-second maximum retry interval on activities, so a dependency outage produced thousands of retries an hour. We have since raised the ceiling to 15 minutes by configuration. Bravo already has 186 explicit retry policies in its models; we want to carry that discipline over, not rediscover it.
3. **Search attributes have to be designed up front.** LORA defined none. "Which loans are stuck at survey?" is not answerable from Temporal Visibility there and has to be answered from the application database. Bravo's operations staff ask that question daily in Cockpit. For Bravo we would define search attributes for application id, product, risk tier, current step and assignee before porting the first workflow.
4. **Version retirement needs a loop.** With one task queue per version, old versions hold orphaned child workflows that ops terminated at the parent and never at the child, which blocks retiring the version. We now have a runbook and a cleanup. Bravo has 56 call activities; the parent-child cancellation rules need deciding at design time.
5. **Observability coverage of long-lived workflows is partial.** A completion span is missing for 30 to 70% of long-running loans, which made a cohort analysis wrong until we checked Temporal's own status counts. For Bravo we would want workflow-state metrics from Temporal, not inferred from traces.

None of these is a complaint about the product. They are operating lessons, and they are the reason this package asks specific questions in [06](06-scope-and-questions.md) rather than general ones.

## 4. The Java pilot: Temporal inside a Bravo service

A sibling Bravo service, `bravo-agreement-service` (Java, Spring Boot 2.7), has a pilot on the **Temporal Java SDK through `temporal-spring-boot-starter` 1.39**. It is in review and has run against an in-memory test server and the `agreement-sit` namespace.

What it established, and what carries over to `ms-bpm`:

- One workflow type per loan product, generated from a template, with a product router. Thirteen products in the master; the same product list drives `ms-bpm`.
- Synchronous HTTP semantics preserved with **update-with-start**: the caller gets a 201 with the result while the workflow continues.
- A **steps facade**: the existing service methods are exposed through one interface, and activities are a thin adapter over it, so the pre-Temporal and Temporal code paths run the same business code. This is the pattern we would use for the 272 delegates in `ms-bpm`.
- Business rejections are **non-retryable `ApplicationFailure`** carrying a typed detail object, mapped back to the exact HTTP error body the consoles already expect. Transient failures stay retryable.
- A 30-day `Workflow.await` for a document-signing wait, replacing a RabbitMQ retry ladder.
- Worker in-process with the API pods, activated only when a Temporal target is configured, so the service runs with Temporal dark by default.
- Dependency facts: the starter compiled against Spring Boot 2.7.18 and is stated to support Boot 2, 3 and 4; it needed gRPC 1.76 and protobuf 3.25, which had to be pinned ahead of the Google libraries BOM. `ms-bpm` is on Spring Boot 3.5 and will move to 4; we need the same facts confirmed for that line.

So the team has a working Java pattern for request-scoped workflows. What it has not yet done is a workflow that lives for days with human waits in the middle, at a hundred thousand starts a month. That is the gap this assessment should close.
