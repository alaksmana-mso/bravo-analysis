# bravo-edoc-service — logging fixes

**Squad:** Operation Post-Go Live
**Production service:** `prod-ms-edoc`
**Stack:** Java, Spring Boot

`loggerLevel: full` is set here on one client and currently emits nothing. The real work
is the exception logging.

---

## 1. `loggerLevel: full` on `ApigeeApiClient` — dormant, but scope it properly

`src/main/resources/application.yaml`:

```yaml
feign:
  client:
    config:
      ApigeeApiClient:
        loggerLevel: full
```

Unlike the other five repos carrying `loggerLevel: full`, this one is **not** on
`feign.client.config.default`. It targets a single client, `ApigeeApiClient`. That is
already the right shape — somebody scoped it deliberately instead of turning it on estate-
wide.

It produces no output today. `application-prod.yaml` sets no logging levels at all, so the
service falls back to `application.yaml`, where `root` is `${LOGGING_LEVEL_ROOT:#{INFO}}` —
INFO unless the deployment says otherwise. Feign writes bodies at DEBUG, so nothing is
emitted.

### Two things to close

1. **The root level is environment-variable driven with no production pin.** If anyone sets
   `LOGGING_LEVEL_ROOT=DEBUG` to chase a bug, Apigee request and response bodies start
   flowing into Cloud Logging, along with everything else at DEBUG across the service. Pin
   it explicitly:

   ```yaml
   # application-prod.yaml
   logging:
     level:
       root: INFO
   ```

2. **Decide whether `ApigeeApiClient` still needs `full`.** If it was added to debug an
   integration that now works, drop it to `basic`. If it is genuinely needed, leave it —
   the blast radius is one client, which is acceptable.

`application-prod.yaml` currently carries no `logging` block. Adding one is the fix for
item 1 and takes a minute.

## 2. 175 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/service/impl/MessageServiceImpl.java` with 17.

Multi-line aggregation is off cluster-wide, so each stack trace becomes one log entry per
frame. A 50-frame trace is 50 entries, each paying its own metadata envelope.

### Fix

Where the failure is expected — an upstream 4xx, a missing record, a validation failure —
log one structured line and drop the throwable:

```java
log.warn("document strategy failed: agreementNo={} step={} reason={}",
         agreementNo, step, e.getMessage());
```

Keep the trace where somebody would genuinely need it to diagnose. Start with the densest
file and work down.

---

## 3. Smaller items

| Item | Count | Note |
|---|---:|---|
| Body logging | 7 | `CommonListener.java` and client classes — log ids, not payloads |
| Payload-logging filter | registered | Limit none; dormant at INFO in prod, same as item 1 |
| DEBUG/TRACE in YAML | a few | Local and standalone profiles only |
| `System.out.print` | a few | All in `src/test/` — harmless |

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — pin the root level in prod | Rp 0 | risk removal only |
| 2 — exception logs | Rp 1–4M | medium |
| 3 — body logging | under Rp 1M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This squad did something different, and
it is the clearest evidence in the pack that the gap is real: they built a database table
for payloads.**

| | Seven days, production |
|---|---:|
| Spans | 385,910 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-edoc` returns no results in Datadog Logs over seven days, under either `service:`
or `kube_deployment:`. The service identity section below covers why.

### The payload store

`config/logger/FeignConfinsLogger.java` is not a logger in the usual sense. On every CONFINS
call, when the Feign level is above `HEADERS`, it:

- builds a `ConfinsRequestLog` row with the path and method,
- puts the request body — or the query string for GETs — into `requestPayload`,
- puts the full response body into `responsePayload`,
- and saves the row through `ConfinsRequestLogRepository`.

The bodies go into Postgres, not into logs. That is why none of this shows up in the numbers
above, and why it has never appeared in a logging cost review.

**It still needs an owner.** That table holds CONFINS request and response payloads for a
document service. Nobody in this analysis could find a retention policy, an access control
statement, or a size for it. It sits outside the logging budget and outside every logging
control we have written.

`config/logger/LoggerConfiguration.java` also registers `bravo-lib-logging`'s
`RequestLoggingFilter` and `FeignClientFilter` unconditionally, the same as
`bravo-branch-service`. Those are dormant only because the level sits above DEBUG.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For the CONFINS
adapter that is a direct replacement for `ConfinsRequestLog` — on demand instead of always
on, and nothing persisted afterwards.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do

1. **Answer three questions about `ConfinsRequestLog` this sprint:** how big is it, how long
   is it kept, and who can read it. If the answer to any of them is "nobody knows", that is
   a finding in its own right.
2. If the table exists for audit rather than debugging, say so explicitly in the repo and
   scope it to the calls that need auditing. If it exists for debugging, it is a Live
   Debugger candidate and can be retired.
3. Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty`, defaulting to false.
4. Scope `loggerLevel: full` to `ApigeeApiClient` properly (item 1 above) — today it is what
   decides whether the payload table is written at all.

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
| Bean validation (`@Valid` on 40 of 68 request bodies), 39 of 41 controllers | 400 `"Some required parameter is not sent"` — **no field list** | ERROR `Exception ` **with the full stack trace**, whose first line carries `rejected value [...]` |
| Bean validation on `DocumentControllerV2` (its own handler) | 400 with `ex.getMessage()` — **the rejected values, echoed** | nothing |
| Business rule: **292 raw `ResponseStatusException` sites** (132 → 400, 84 → 404, 22 → 500), `StateMachineException` 29 (403), `NotFoundException` 8 | Boot's default `/error` body with the reason | **nothing** from any handler |
| `IllegalArgumentException` (33 sites) | 400 under `DocumentControllerV2`, **500** everywhere else | nothing |

This service is silent in Datadog (no log entries in seven days). It also has three advice
classes that disagree with each other: the global one hides the fields from the caller and
prints them to the log; the V2 one does the reverse; the PBF one covers one exception.

### What is already right, and the gaps

Right: `ConfinsRequestLog` — every outbound CONFINS call is stored in the database with path,
method, request payload, response payload and status. That is the "keep the data in the
database" pattern, already built. One correction to this branch: the first commit of #1525 set
`ApigeeApiClient` to `loggerLevel: basic`, and `FeignConfinsLogger` only writes those rows when
the level is above `HEADERS`, so the audit table silently stopped filling. **Restored to `full`
on 23 September** (`77683260`, explained on the pull request); the logger's own output is DEBUG,
so `full` adds nothing to stdout. The gaps:

1. No handler logs a decision, and 292 rule sites bypass the handlers entirely.
2. The reference never returns: the lib's `CorrelationIdFilter` reads `X-Correlation-Id` into
   the MDC and sets no header; no error DTO has an id field.
3. The one logged rejection is a stack trace with the customer's values in it.

### The best practice for this service

1. **One `ErrorAdvice` for the whole service.** Fold the V2 and PBF handlers into it; add
   `ResponseStatusException` and `BusinessException` handlers so the 292 sites return the
   same body shape (`code`, `message`, field list) and write one WARN `request_rejected` line:
   route, status, the document or agreement number from the path, `fields: [{field, rule}]`.
   Drop the stack and the rejected values from the bean-validation line; return the field list
   to the caller instead of "Some required parameter is not sent".
2. **Return the correlation id.** A one-line filter that sets `X-Correlation-Id` on the
   response (the lib filter cannot), and the same value on the error body.
3. **The input is in the database.** Documents, custody, delivery and relocation requests are
   55 entities with `EventStore` and `NotificationOutbox`; CONFINS calls are in
   `ConfinsRequestLog`; the one audit-trail call covers document downloads. Read it there.
4. **Ship the logs to Datadog** (item 2 of this file) so the decision line can be searched.
5. **Keep the lib body loggers behind `enableBfiLogger`**, as the branch does; on `master` they
   ran unconditionally.

### Runbook: a branch asks why a document request was refused

1. Get the reference (once step 2 ships) or the agreement number and time.
2. `service:prod-ms-edoc @event:request_rejected @agreement_number:<n>` once the logs arrive.
3. For the data, the `AssetDocument*` rows; for a CONFINS answer, `confins_request_log`.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-edoc` | 384,176 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-edoc` either — both searches return zero over seven days.

It is not silent. It is producing 384,176 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-edoc`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-edoc"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-edoc
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-edoc` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-edoc env:prod

# APM Traces
service:prod-ms-edoc env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-edoc` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/edoc/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `INFO` |
| `SENSITIVE_KEYS` | not set  ← library default (6 keys) |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | `true` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It wires the library's `RequestLoggingFilter` and `FeignClientFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 2.7.18, so the starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September 2026, Boot 3.3+ only) is out of reach until it upgrades. It stays on `bravo-lib-logging`, whose fix ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) **was closed on 16 September** when the starter merged, so the library keeps unmasked Feign bodies, case-sensitive `SENSITIVE_KEYS` and no body cap: set `REQUEST_BODY_LOGGING=false`, `RESPONSE_BODY_LOGGING=false` and a written `SENSITIVE_KEYS` in `values-prod.yaml`, merge the per-service pull request, and put the Boot 3.3 upgrade on the roadmap — it is the only route to the starter.
---

## Implementation status

**Pull request: [bravo-edoc-service#1525](https://github.com/bfi-finance/bravo-edoc-service/pull/1525)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-edoc-service/tree/fix/logging), head `81903540`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-edoc-service/pull/1525/files) · [Commits](https://github.com/bfi-finance/bravo-edoc-service/pull/1525/commits) · [Compare against master](https://github.com/bfi-finance/bravo-edoc-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 2.7.18. The shared Java logging library every service moves to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)), but it is Boot 3.3+ only (jakarta), so it is out of reach here until the repository upgrades. The fix to the old library that would have bridged that gap, [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123), **was closed the same day** so that one library carries the standard. That leaves **this pull request, plus `REQUEST_BODY_LOGGING=false`, `RESPONSE_BODY_LOGGING=false` and a written `SENSITIVE_KEYS` in `values-prod.yaml`, as the fix for this service** until a Boot 3.3 upgrade, which is the only route to masked, capped, single-line logs for it.

CI on the current head is red only on **`Security Container Scan`, `Static Analysis - SonarQube`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commit:

- fix(logging): gate the shared body loggers and scope Feign logging

Files:

- `src/main/java/com/bfi/bravo/config/logger/LoggerConfiguration.java`
- `src/main/resources/application.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Add a `logging.level.root: INFO` block to `application-prod.yaml`
- [ ] Decide whether `ApigeeApiClient` still needs `loggerLevel: full`, or drop it to `basic`
- [ ] Review the 17 exception logs in `MessageServiceImpl.java`, then the rest of the 175
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Answer three questions about `ConfinsRequestLog`: how big, how long kept, who can read it
- [ ] Say in the repo whether that table exists for audit or for debugging
- [ ] Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty`, defaulting to false
- [ ] One `ErrorAdvice` with `ResponseStatusException` / `BusinessException` handlers and a WARN `request_rejected` line; field list to the caller, no stack, no values
- [ ] Return `X-Correlation-Id` on the response and in the error body
- [ ] Keep `ApigeeApiClient` at `full` — `FeignConfinsLogger` persists to `confins_request_log` only above `HEADERS` (restored on the branch 23 Sep)
