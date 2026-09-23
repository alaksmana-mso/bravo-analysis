# bravo-customer-service — logging fixes

**Squad:** Contract Collateral & Loan Calculation (also under Customer Platform)
**Production service:** `prod-ms-customer`
**Stack:** Java, Spring Boot

Customer master data service. Nothing here is live today, but it handles the most sensitive
records in the estate, so the dormant settings deserve closing properly.

---

## 1. 108 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/adapter/masterdata/MasterDataAdapterImpl.java`
with 5, spread fairly evenly elsewhere.

Multi-line aggregation is off cluster-wide, so each trace becomes one entry per frame.

### Fix

Structured warn lines for expected upstream failures. Keep traces only where a person would
need one to diagnose:

```java
log.warn("master data lookup failed: customerId={} field={} reason={}",
         customerId, field, e.getMessage());
```

Do not put the customer name, identity number or address in the message. An id is enough to
trace it.

---

## 2. `CommonsRequestLoggingFilter` with payload logging — dormant

`src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java` registers the filter
with `setIncludePayload(true)` and a 10 KB limit.

It emits nothing today. The filter's logger sits at INFO in the production profile, and
`CommonsRequestLoggingFilter` writes at DEBUG.

**On this service the dormant state matters more than usual.** If it ever turns on, inbound
request bodies to the customer master service go into Cloud Logging — names, identity
numbers, addresses, dates of birth.

### Fix

Set `setIncludePayload(false)`, or move the `@Bean` behind `@Profile("local")`. Then pin
the level so it cannot drift:

```yaml
logging:
  level:
    org.springframework.web.filter.CommonsRequestLoggingFilter: WARN
```

---

## 3. 10 body logs

`src/main/java/com/bfi/bravo/connector/CommonListener.java` has 2, others spread.

A queue listener that logs message bodies logs customer records. Log the message id,
routing key and outcome.

---

## 4. Eight DEBUG/TRACE YAML entries

All in `application-local-standalone.yaml` and `application-local.yaml`. No production
impact.

---

## 5. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — exception logs | Rp 1–3M | medium |
| 2 — dormant payload filter | Rp 0 today | risk removal on the most sensitive service |
| 3 — body logging | under Rp 1M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service's payload filter is dormant,
and what little it does log is almost all errors.**

| | Seven days, production |
|---|---:|
| Spans | 2,017,949 |
| Log entries | 21,371 |
| of which `error` | 20,662 |
| of which `info` | **5** |
| Entries carrying a captured body | 0 |

Five INFO entries in seven days is the proof that
`config/RequestLoggingFilterConfig.java` — `setIncludePayload(true)`,
`setMaxPayloadLength(10000)`, prefix `REQUEST DATA : ` — is producing nothing. It writes at
the filter's own logger level, which sits above DEBUG in production.

It also tells you something else: a service handling two million spans a week that emits
five informational log lines has no operational narrative at all. Everything visible is a
failure.

### What is live

The 10 body logs in service code, covered in item 3 above. Those are the ones to change.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For customer
data that is the right shape — on demand, rate limited, redacted by default, and gone when
you remove the probe. An always-on filter that writes customer records into a system with
broad read access is not.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do

1. Pin the filter level explicitly in `application-prod.yaml`, so it cannot wake up by
   accident.
2. Replace the 10 body logs with identifiers — `cif_id`, `customer_id`, `agreement_no`.
3. Put those same identifiers on the span:

   ```java
   final Span span = GlobalTracer.get().activeSpan();
   if (span != null) {
     span.setTag("customer.cif_id", cifId);
     span.setTag("customer.agreement_no", agreementNo);
   }
   ```

4. Add one INFO line per meaningful business outcome. Five a week is not observability.

---

## Why did validation fail? Answering the customer without logging the payload

The same question the Scoring and Underwriting reviewer asked on `bravo-bpm-service#10463` applies
here: when a request is rejected and the customer asks why, the engineer reads the payload in the
log because nothing else says. The estate-level answer is in
[bravo-bpm-service.md](bravo-bpm-service.md#why-did-validation-fail-answering-the-customer-without-logging-the-payload):
**log the decision, return the reference, keep the data in the database.** This section is what
that means for this service, read from the code on `fix/logging` and seven days of production
logs on 23 September 2026.

### What happens today when a request is rejected

| How the request fails | Caller gets | Log says |
|---|---|---|
| Bean validation (`@Valid` on 10 of 25 request bodies) | 400, one attribute per field with `rejectedValue: message` | one ERROR line `Error bad request: {body}` from `ErrorAdvice` (line 305) — **customer field values at ERROR**, no stack trace |
| Unreadable body | 400 `Invalid format: …` (contains the value) | nothing |
| Business rule via `BusinessException` (`CustomerMaintenanceException` 19 sites, `CustomerException` 15, seven `Invalid*Exception` classes 14, and four smaller) | the exception's own status, `error_code`, `message` | **nothing** — `handleBusinessException` has no log statement |
| `ValidationException` (parse failure of the emergency-relation input), 3 `CustomerMaintenanceException` sites | **500** | nothing |
| Downstream `FeignException` | **400** with Feign's message (downstream URL and body excerpt) | ERROR line `Error handleFeignException` |
| Anything else | 500 with the exception message | nothing |

Production over seven days: 24,779 error lines, 319 warn, 16 info. The error stream is
dominated by `Failed get customers from confins: Data is not exist!` and `400 BAD_REQUEST
"Cannot find … with code …"`, and 111 lines with an empty message. None of them is a business
rule decision, because those are not logged.

### What is already right, and the gaps

Right: `CorrelationIdFilter` **writes `x-request-id` back** on every response. Right: a JSON
`LogstashEncoder` is configured — but only on a file appender to `/tmp/log`, while stdout keeps
the plain-text pattern, so Datadog sees the pattern. The gaps:

1. Rule rejections are silent, and the one class of rejection that is logged carries the
   customer's rejected values (name, phone, address fragments) at ERROR.
2. The reference is not in the error body.
3. A rule outcome can be a 500 (`ValidationException` by constructor, three
   `CustomerMaintenanceException` sites), and a downstream failure is reported as the caller's
   fault (400).

### The best practice for this service

1. **One WARN decision line per rejection, from `ErrorAdvice`.** Add it to
   `handleBusinessException`, `handleHttpMessageNotReadable` and the catch-all; keep it to
   route, status, `error_code`, the CIF id or maintenance request id from the path, and field
   plus rule for bean validation. **Remove `getRejectedValue()` from the bean-validation
   message** in both the response and the log: this service's fields are identity data.
2. **Put `x-request-id` in the error body.** The header is already there; add the field to
   `ErrorResponse`.
3. **Send JSON to stdout.** Move the `LogstashEncoder` from the `/tmp/log` file appender to the
   console appender, and `dd.trace_id` comes along with the MDC; the decision line then links
   to the trace, which already shows the CONFINS call that said "Data is not exist".
4. **Fix the statuses.** `ValidationException` and the three 500 maintenance sites become 4xx;
   `FeignException` becomes 502 (or the downstream status), not 400.
5. **The input is in the database.** A CIF is `Cif` with `CifAddress`, `CifCompany`,
   `CifEmergency`, `CifDocument` and the rest; a maintenance request is
   `CustomerMaintenance` / `CustomerMaintenanceDetail` / `CustomerMaintenanceEvent`; every
   edit publishes a `CustomerLog` row through the `@CustomerHistoryAudit` aspect. Read it there.
6. **Leave the payload filter off.** `REQUEST DATA :` is off on the branch; `master` had it on
   with a 10 KB cap and a DEBUG logger in `logback.xml`. If a window is ever needed, 4xx only,
   masked.

### Runbook: a customer asks why their data change was rejected

1. Get the `x-request-id` from the console (already returned) or the CIF id and the time.
2. `CustomerMaintenanceEvent` for that request shows the outcome and actor; `CustomerLog` shows
   what changed.
3. Once step 1 ships: `service:prod-ms-customer @event:request_rejected @cif_id:<id>`, or
   `@correlationId:<reference>`.
4. If the rejection came from CONFINS, open the trace: the outbound span carries its status.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-customer` | 1,990,622 spans |
| Logs | `prod-ms-customer` | 21,287 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-customer`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-customer"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-customer
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-customer` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-customer env:prod

# APM Traces
service:prod-ms-customer env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-customer` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/customer/values-prod-sharia.yaml`, `app-deployment/customer/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL` | `full` *(values-prod-sharia.yaml)* |
| `LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS` | `DEBUG` *(values-prod-sharia.yaml)* |
| `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL` | `full` *(values-prod.yaml)* |
| `LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS` | `DEBUG` *(values-prod.yaml)* |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bravo-customer-service#621](https://github.com/bfi-finance/bravo-customer-service/pull/621)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-customer-service/tree/fix/logging), head `ddfe4af9`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-customer-service/pull/621/files) · [Commits](https://github.com/bfi-finance/bravo-customer-service/pull/621/commits) · [Compare against master](https://github.com/bfi-finance/bravo-customer-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.15. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is **fully green**.

**Codacy review, answered 18 September 2026.** 3 Codacy thread(s); 3 fixed in `942d5edb` (docs(logging): say what the request filter actually writes; drop the unused payload cap). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commit:

- fix(logging): stop the request-logging filter capturing customer payloads

Files:

- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`
- `src/main/resources/application-prod.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Review the 108 exception-logging sites, starting with `MasterDataAdapterImpl.java`
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Pin `CommonsRequestLoggingFilter: WARN` in `application-prod.yaml`
- [ ] Replace body logging in `CommonListener.java` with message id and outcome
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml`
- [ ] Add one INFO line per business outcome — five INFO entries a week is not observability
- [ ] Log one structured WARN decision line per rejected request in `ErrorAdvice`; add it to `handleBusinessException` and the catch-all
- [ ] Remove `getRejectedValue()` from the bean-validation response and log line
- [ ] Add `x-request-id` to `ErrorResponse` (already a response header)
- [ ] Move the `LogstashEncoder` from the `/tmp/log` file appender to the console appender
- [ ] Return 4xx for `ValidationException` and the 500 maintenance sites; 502 for downstream `FeignException`
