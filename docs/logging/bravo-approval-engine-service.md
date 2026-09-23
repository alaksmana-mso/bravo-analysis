# bravo-approval-engine-service — logging fixes

**Squad:** Contract Collateral \& Loan Calculation
**Production service:** `prod-ms-approval-engine`
**Stack:** Java, Spring Boot

This repo logs inbound request bodies **by default**. Whether that is happening in
production depends on a deployment environment variable that is not in this repo.

---

## 1. Payload logging defaults to DEBUG

Two halves.

**The filter** — `src/main/java/com/bfi/bravo/config/WebConfig.java`:

```java
filter.setIncludePayload(true);
filter.setMaxPayloadLength(64000);
```

**The level** — `src/main/resources/application.yaml` sets CommonsRequestLoggingFilter using a placeholder
with a DEBUG fallback:

```yaml
CommonsRequestLoggingFilter: ${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:DEBUG}
```

`CommonsRequestLoggingFilter` writes at DEBUG. So **unless the deployment sets
`LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER` to something higher, every inbound request
body up to 64000 bytes is written to Cloud Logging.**

### The check

The manifests are not in this repo. One command settles it:

```bash
kubectl -n prod set env deploy/<this-service> --list | grep -i logging
```

If the variable is absent, payload logging is live and this is the repo's main cost and
data-exposure item. If it is set to INFO or WARN, this is dormant and only item 2 matters.

### Fix, either way

A default of DEBUG for a payload-logging filter is the wrong default. Invert it so the
safe state is the one you get when nobody configures anything:

```yaml
CommonsRequestLoggingFilter: ${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:WARN}
```

Better still, set `setIncludePayload(false)` and keep query string, status and duration.
Those answer most debugging questions without putting request bodies in logs.

If the payload is genuinely needed locally, put the `@Bean` behind `@Profile("local")`.

---

## 2. 14 exception logs passing the throwable

Each `log.error(msg, e)` can emit a full stack trace, and multi-line aggregation is off
cluster-wide, so one trace becomes one entry per frame.

Split them: structured warn lines for expected upstream failures, traces only where a
person would need one.

---

## 3. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — payload logging | Rp 2–8M **if live**, Rp 0 if the env var is set | unknown until checked |
| 2 — exception logs | Rp 1–2M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **For this service the question does not
arise yet, because nothing it writes reaches Datadog at all.**

| | Seven days, production |
|---|---:|
| Spans | 26,775 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-approval-engine` returns no results in Datadog Logs over seven days, under either
`service:` or `kube_deployment:`. The service identity section below covers why and what to
do about it.

### What exists in the code

`client/logger/FeignSlf4jLogger.java` captures request and response bodies at Feign level
FULL, gated on `logger.isDebugEnabled()`, with `MASKED_FIELD` covering `Authorization`,
`api-secret`, `x-api-key`, `X-ACCESS-TOKEN`, `x-auth-app-id` and `x-auth-app-secret` —
headers only, not bodies. Production sits above DEBUG, so it is a no-op today.

This matters for sequencing. If log collection is fixed while the payload filter default is
still `DEBUG` (item 1 above), the first thing to arrive in Datadog will be bodies.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Fix the payload filter default (item 1) **before** log collection is fixed, not after.
2. Fix log collection, after the exclusion filters exist, so the new volume lands inside a
   filter rather than on the bill.
3. Then ask for Live Debugger. There is no point asking for body capture on a service whose
   ordinary logs are invisible.

---

## Why did validation fail? Answering the customer without logging the payload

The same question the Scoring and Underwriting reviewer asked on `bravo-bpm-service#10463` applies
here: when a request is rejected and the customer asks why, the engineer reads the payload in the
log because nothing else says. The estate-level answer is in
[bravo-bpm-service.md](bravo-bpm-service.md#why-did-validation-fail-answering-the-customer-without-logging-the-payload):
**log the decision, return the reference, keep the data in the database.** This section is what
that means for this service, read from the code on `fix/logging` on 23 September 2026.

### What happens today when a request is rejected

| How the request fails | Caller gets | Log says |
|---|---|---|
| Bean validation (`@Valid` on 16 of 17 request bodies) | 400, code `B0000`, one attribute per field with `field: message`, no rejected value | one ERROR line `Error bad request: {body}` from `ControllerAdvice` (line 248), no stack trace |
| Wrong parameter type | 400, message echoes the rejected value | nothing |
| Constraint violation, missing parameter, unreadable body | 400 | nothing |
| Business rule via `ApprovalException` (22 throw sites: 13 map to 400, 5 to 401, 3 to 404, 1 to 409) | the exception's own status, body with `code`, `message`, `path` | **nothing** — `handleBusinessException` has no log statement |
| Anything else (`IllegalStateException` and friends) | **500 with the exception message** | **nothing**, not even the stack trace |

And none of it reaches Datadog anyway: this service sends spans but **zero log entries** (see
*Service identity in Datadog* below). Today "read the log" means the pod's stdout in Cloud
Logging, in a plain-text pattern that carries `correlationId` and nothing else structured.

### The two gaps

1. **The reference never goes back to the caller.** `CorrelationIdFilter` reads
   `X-Correlation-Id`, generates a UUID when absent and puts it in the MDC, but sets no response
   header. Neither `ErrorResponse` nor `BaseResponse` has a trace or correlation field. The
   Datadog `dd.trace_id` exists in the MDC at runtime (the agent is in the image) and is never
   printed, because the console pattern prints only `%X{correlationId}`.
2. **Rule outcomes are silent.** An approval request rejected by a rule produces a response and
   no line. The only rejection that is logged is bean validation.

### The best practice for this service

1. **One WARN decision line per rejection, from `ControllerAdvice`.** Add it to
   `handleBusinessException` and the catch-all: event `request_rejected`, route, status, the
   `code` already in the body, the request id and approver ids from the path, and for bean
   validation the field and rule (the `attributes` list already built). No stack trace for a
   rule; keep it for the catch-all, which today hides real faults behind a silent 500.
2. **Return the reference.** One line in `CorrelationIdFilter`: `response.setHeader("X-Correlation-Id", id)`,
   and the same value as a field on `ErrorResponse`. Then the console can show it and support can quote it.
3. **Print the trace id.** Switch the console appender to the `LogstashEncoder` that is already
   on the classpath (`logstash-logback-encoder` 7.4 is declared and unused), or add
   `%X{dd.trace_id}` to the pattern. Either way the decision line links to the trace, which is
   the only telemetry this service ships today.
4. **The input is already in the database.** An approval request is a `Request` /
   `RequestDetail` row with `Approval` and `ApprovalEvent` history, JPA-audited with created-by
   and modified-by. "What did they send" is a query by request id, behind database access
   control, not a log line readable by everyone with Datadog access.
5. **Keep the payload switch off.** `LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER` is `WARN` on the
   branch (it was `DEBUG` with a 64 KB payload on `master`). If a window is ever needed, capture
   on 4xx only and through a masker. One more thing the code reading found: `com.bfi.bravo.client`
   is at DEBUG in `application.yaml` and not overridden in `application-prod.yaml`, so on
   `master` the Feign body logger's gate was open — `FEIGN_LOGGER_LEVEL=BASIC` on the branch is
   what closes it. Do not reopen it to answer a customer question.

### Runbook: a customer asks why an approval request was rejected

1. Get the reference (once step 2 ships) or the approval request id and the time.
2. Read the `Request` and `ApprovalEvent` rows for that id: the status, the actor and the
   timestamp of the rejection are there today.
3. Once step 1 ships: `service:prod-ms-approval-engine @event:request_rejected @request_id:<id>`,
   or `@correlationId:<reference>`. Until the service ships logs to Datadog, the same search
   runs in Cloud Logging.
4. If the rejection came from a downstream call, open the trace by `trace_id`.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-approval-engine` | 27,699 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-approval-engine` either — both searches return zero over seven days.

It is not silent. It is producing 27,699 spans, so the workload is busy and the Agent
can reach Datadog. The logs are going to Cloud Logging and Coralogix and stopping there.

The practical effect: when this service fails at 02:00, there is a trace showing *that* it
failed and nothing showing *why*. The on-call engineer has a duration and a status code.

### What to do

1. **Confirm the Agent is collecting this pod's logs.** In the GitOps values file, check for
   the log collection annotation on the pod template, or that the Agent's
   `containerCollectAll` covers this namespace.
2. **Make sure the container writes to stdout**, not to a file inside the container. A
   Logback `FileAppender` or a pm2 `log_file` produces logs the Agent never sees.
3. **Do not enable collection until the non-production exclusion filters exist**
   ([sre-datadog-recommendations.md §2.1](sre-datadog-recommendations.md)). Turning this on
   first adds volume outside a filter and moves cost rather than saving it.
4. **Apply the unified tagging block below at the same time**, so the logs arrive already
   carrying the same service name as the traces.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-approval-engine`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-approval-engine"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-approval-engine
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-approval-engine` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-approval-engine env:prod

# APM Traces
service:prod-ms-approval-engine env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-approval-engine` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/approval-engine/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_ROOT` | `INFO` |
| `LOGGING_LEVEL_COM_BFI_BRAVO` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE_SQL` | `info` |
| `LOGGING_LEVEL_ORG_HIBERNATE_TYPE_DESCRIPTOR_SQL` | `info` |
| `LOGGING_LEVEL_ORG_SPRINGFRAMEWORK_WEB_CLIENT_RESTTEMPLATE` | `INFO` |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.16, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bravo-approval-engine-service#166](https://github.com/bfi-finance/bravo-approval-engine-service/pull/166)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-approval-engine-service/tree/fix/logging), head `aefbb29`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-approval-engine-service/pull/166/files) · [Commits](https://github.com/bfi-finance/bravo-approval-engine-service/pull/166/commits) · [Compare against master](https://github.com/bfi-finance/bravo-approval-engine-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.16. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is red only on **`Security Scan - SNYK`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 3 Codacy thread(s); 3 fixed in `dd120ee` (fix(logging): mask the same fields in Feign requests and responses, at any depth). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 3 |

Commit:

- fix(logging): safe defaults for Feign level and inbound payload logging

Files:

- `src/main/java/com/bfi/bravo/client/logger/FeignSlf4jLogger.java`
- `src/main/java/com/bfi/bravo/config/WebConfig.java`
- `src/main/resources/application.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 388 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Run the `kubectl set env --list` check above and record the answer
- [ ] Change the YAML default from `:DEBUG` to `:WARN`
- [ ] Set `setIncludePayload(false)` in `WebConfig.java`, or move the bean behind `@Profile("local")`
- [ ] Pin the filter level explicitly in `application-prod.yaml`
- [ ] Review the 14 exception-logging sites
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Fix the payload filter default **before** log collection is fixed, not after
- [ ] Do not ask for Live Debugger until this service's ordinary logs are visible
- [ ] Log one structured WARN decision line per rejected request in `ControllerAdvice`; add it to `handleBusinessException` and the catch-all
- [ ] Return `X-Correlation-Id` in the response and put it on `ErrorResponse`
- [ ] Print `dd.trace_id` (switch the console appender to the declared `LogstashEncoder`, or add it to the pattern)
- [ ] Keep `LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER=WARN` and `FEIGN_LOGGER_LEVEL=BASIC`; answer "what did they send" from `Request` / `RequestDetail`
