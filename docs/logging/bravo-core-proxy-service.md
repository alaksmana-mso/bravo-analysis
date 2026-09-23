# bravo-core-proxy-service — logging fixes

**Squad:** Contract Collateral \& Loan Calculation
**Production service:** `prod-ms-bravo-core-proxy`
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

## 2. 26 exception logs passing the throwable

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
| Spans | 758,447 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-bravo-core-proxy` returns no results in Datadog Logs over seven days, under either
`service:` or `kube_deployment:`. The service identity section below covers why and what to
do about it.

For a proxy this is the worst place to be. Three quarters of a million spans a week say what
was called and how long it took, and nothing says what was proxied.

### What exists in the code

`client/FeignSlf4jLogger.java` captures request and response bodies at Feign level FULL,
gated on `logger.isDebugEnabled()`, with `MASKED_FIELD` covering the auth headers only.
Production sits above DEBUG, so it is a no-op today.

Sequencing matters here: if log collection is fixed while the payload filter default is
still `DEBUG` (item 1 above), the first thing to arrive in Datadog will be proxied bodies.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For a proxy
that is a good fit — one probe on the forward method answers most questions.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Fix the payload filter default (item 1) **before** log collection is fixed.
2. Fix log collection, after the exclusion filters exist.
3. Add `DD_TRACE_HEADER_TAGS` so correlation ids land on spans. For a proxy this is worth
   more than for most services: it lets a caller's request id follow the hop.

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
| Bean validation (`@Valid` on 24 of 171 request bodies — 14%) | 400 with `field: message` errors | **nothing** |
| Wrong parameter type | 400, the cause message echoes the rejected value | nothing |
| Business rule (`PaymentException` 9 sites, `IdempotencyException`, `AgreementException`, `MaintenanceException`, `NewCoreClientException`) | the exception's own status; downstream errors passed through | **nothing** |
| `UnsupportedOperationException` (12 sites), `NotImplementedException` (3), anything unexpected | **500 with the exception message** | **nothing** |

`ControllerAdvice` has no logger at all: not one `log.` statement in 330 lines. This service
sends 746,000 spans a week and **zero log entries** to Datadog. A rejected request leaves no
record anywhere except the response the caller received.

### The two gaps

1. **The reference never goes back to the caller.** `CorrelationIdFilter` reads
   `X-Correlation-Id`, generates a UUID, puts it in the MDC, propagates it into executors and
   AMQP headers — and sets no response header. `BaseResponse` has no trace field. The console
   pattern prints only `%X{correlationId}`; `dd.trace_id` is in the MDC and never printed.
2. **Nothing is recorded, and there is nowhere to look.** This is a proxy: it stores mapping
   tables and an outbox, not the proxied request. Only 4 entities exist. So unlike the other
   services, "read it from the database" is not available here; the record of the request is
   in the core system downstream and in the trace.

### The best practice for this service

1. **One WARN decision line per rejection, from `ControllerAdvice`.** Give the class a logger
   and add one statement to `handleBusinessException`, `handleMethodArgumentNotValid`,
   `handleNewCoreClientException` and the catch-all: event `request_rejected`, route, status,
   the error code, the agreement or payment id from the path, the field and rule for bean
   validation, and the downstream status for a passed-through core error. No stack trace for a
   rule; keep one for the catch-all, which today returns 500 silently.
2. **Return the reference.** One `setHeader` line in `CorrelationIdFilter`, plus a field on
   `BaseResponse`. Because this service already forwards the id into AMQP headers, the same
   reference then follows the request into the consumers.
3. **The trace is the record here.** For a proxy the Datadog trace is where the request and the
   downstream answer meet: the outbound span carries the core system's status and URL. Print
   `dd.trace_id` (the pattern has room, or use a JSON encoder) so the decision line opens the
   trace. For the body itself, Live Debugger on the client method once Remote Configuration
   works, or the downstream system's own record.
4. **Fix the 500s that are really 4xx.** Twelve `UnsupportedOperationException` sites and three
   `NotImplementedException` sites reach the catch-all as 500 with no line. Map them to 501 or
   400 with a code, and log them.
5. **Keep the payload switch off.** `LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER=WARN` and
   `FEIGN_LOGGER_LEVEL=BASIC` on the branch close both routes (`master` had `DEBUG` with a 64 KB
   payload and Feign `FULL` with the `com.bfi.bravo.client` logger at DEBUG in prod). If a
   window is ever needed, capture on 4xx only and through a masker.

### Runbook: a customer asks why a core transaction was rejected

1. Get the reference (once step 2 ships) or the agreement number and the time.
2. Datadog APM: `service:prod-ms-bravo-core-proxy` traces for that time window, filter by the
   resource; the outbound span shows the core system's status. Once step 1 ships, start from the
   decision line instead: `@event:request_rejected @agreement_number:<n>`.
3. For the data, ask the downstream core system by its own reference; this service does not hold it.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bravo-core-proxy` | 745,851 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-bravo-core-proxy` either — both searches return zero over seven days.

It is not silent. It is producing 745,851 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bravo-core-proxy`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bravo-core-proxy"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bravo-core-proxy
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bravo-core-proxy` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bravo-core-proxy env:prod

# APM Traces
service:prod-ms-bravo-core-proxy env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bravo-core-proxy` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/core-proxy/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_ROOT` | `INFO` |
| `LOGGING_LEVEL_COM_BFI_BRAVO` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE_SQL` | `info` |
| `LOGGING_LEVEL_ORG_HIBERNATE_TYPE_DESCRIPTOR_SQL` | `info` |
| `LOGGING_LEVEL_ORG_SPRINGFRAMEWORK_WEB_CLIENT_RESTTEMPLATE` | `INFO` |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bravo-core-proxy-service#418](https://github.com/bfi-finance/bravo-core-proxy-service/pull/418)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-core-proxy-service/tree/fix/logging), head `dc71bed`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-core-proxy-service/pull/418/files) · [Commits](https://github.com/bfi-finance/bravo-core-proxy-service/pull/418/commits) · [Compare against master](https://github.com/bfi-finance/bravo-core-proxy-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.15. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is red only on **`SonarQube Code Analysis`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 2 Codacy thread(s); 2 fixed in `ce65d53` (fix(logging): mask the same fields in Feign requests and responses, at any depth). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 3 |

Commit:

- fix(logging): safe defaults for Feign level and inbound payload logging

Files:

- `src/main/java/com/bfi/bravo/client/FeignSlf4jLogger.java`
- `src/main/java/com/bfi/bravo/config/WebConfig.java`
- `src/main/resources/application.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 826 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Run the `kubectl set env --list` check above and record the answer
- [ ] Change the YAML default from `:DEBUG` to `:WARN`
- [ ] Set `setIncludePayload(false)` in `WebConfig.java`, or move the bean behind `@Profile("local")`
- [ ] Pin the filter level explicitly in `application-prod.yaml`
- [ ] Review the 26 exception-logging sites
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Fix the payload filter default **before** log collection is fixed, not after
- [ ] Ask SRE for `DD_TRACE_HEADER_TAGS` — for a proxy this carries the caller's request id across the hop
- [ ] Give `ControllerAdvice` a logger and one structured WARN decision line per rejected request; keep the stack trace for the catch-all only
- [ ] Return `X-Correlation-Id` in the response and put it on `BaseResponse`
- [ ] Print `dd.trace_id` in the log output so a rejection opens its trace
- [ ] Map `UnsupportedOperationException` / `NotImplementedException` to a 4xx/501 with a code instead of a silent 500
