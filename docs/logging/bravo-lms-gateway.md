# bravo-lms-gateway — logging fixes

**Squad:** Contract Collateral & Loan Calculation (also under Payment, Tele Marketing)
**Production service:** `prod-ms-lms-gateway`
**Stack:** Java, Spring Boot

663 exception logs, and 117 of them are in one file. That concentration is the finding.

---

## 1. 117 exception logs in `PaymentAdapterImpl.java`

`src/main/java/com/bfi/bravo/adapter/payment/PaymentAdapterImpl.java`

117 `log.error(msg, exception)` calls in a single adapter. The repo total is 663, so this
one file is 18% of it.

An adapter with 117 error-logging sites is usually one of two things: a lot of copy-paste,
or a class doing too much. Either way, every upstream payment failure emits a full stack
trace, and payment adapters fail often — upstream timeouts, 4xx from the core, retries.

### Fix

1. Handle the failures once, not 117 times. A single `@ExceptionHandler` or a wrapper
   method around the upstream calls replaces most of these sites.
2. Whatever remains should log structured fields, not traces:

   ```java
   log.warn("payment call failed: op={} agreementNo={} status={} reason={}",
            op, agreementNo, status, e.getMessage());
   ```

3. Keep the trace for the genuinely unexpected paths only.

This is the single densest logging site found in the estate. It is worth a focused half-day.

---

## 2. `CommonsRequestLoggingFilter` with payload logging — currently dormant

`src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

```java
@Bean
public CommonsRequestLoggingFilter logFilter() {
  CommonsRequestLoggingFilter filter = new CommonsRequestLoggingFilter();
  filter.setIncludeQueryString(true);
  filter.setIncludePayload(true);
  filter.setMaxPayloadLength(10000);
  filter.setIncludeHeaders(false);
  filter.setAfterMessagePrefix("REQUEST DATA : ");
  return filter;
}
```

Payload logging is on, capped at 10 KB. **It emits nothing today**, because the filter's
logger sits at INFO in the production profile and `CommonsRequestLoggingFilter` writes at
DEBUG.

So this is not costing money. It is a landmine: one `logging.level` line in
`application-prod.yaml`, or one environment variable, and this gateway starts writing every
inbound request body into Cloud Logging. It is a gateway, so that is every request in the
LMS path.

### Fix

Either delete the bean, or keep it and set `setIncludePayload(false)`. If somebody wants it
for local work, move the whole `@Bean` behind `@Profile("local")`.

Also pin the level explicitly in `application-prod.yaml` so it cannot drift:

```yaml
logging:
  level:
    org.springframework.web.filter.CommonsRequestLoggingFilter: WARN
```

---

## 3. Three `loggerLevel: full` entries — non-production only

All three are in `src/main/resources/application-local-standalone.yaml`. They do not ship.

Leave them, or change them to `basic` if you want consistency. No cost impact.

---

## 4. Nine DEBUG/TRACE YAML entries

All in local and standalone profiles. No production impact.

---

## 5. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — `PaymentAdapterImpl` exception logs | Rp 3–7M | medium |
| 2 — dormant payload filter | Rp 0 today | it removes a risk, not a cost |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This gateway does neither: no bodies, and
no logs at all.**

| | Seven days, production |
|---|---:|
| Spans | 291,205 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-lms-gateway` returns no results in Datadog Logs over seven days, under either
`service:` or `kube_deployment:`. The service identity section below covers why.

That is the worst combination for a gateway. The 117 exception logs in `PaymentAdapterImpl`
(item 1 above) are being written and nobody can read them.

### What exists in the code

`config/RequestLoggingFilterConfig.java` builds a `CommonsRequestLoggingFilter` with
`setIncludePayload(true)` and `setMaxPayloadLength(10000)`, prefix `REQUEST DATA : `. It
writes at the filter's own logger level, above DEBUG in production, so it is dormant.
Searching all of production for `REQUEST DATA :` returns zero results.

Sequencing matters: fixing log collection while the payload filter default is still `DEBUG`
would deliver payment payloads to Datadog as the first thing that arrives.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Pin the filter level explicitly in `application-prod.yaml` **before** log collection is
   fixed.
2. Fix log collection, after the exclusion filters exist.
3. Reduce the 117 exception logs first (item 1), or fixing collection will deliver 117
   stack traces per failure into a paid index.
4. Add `DD_TRACE_HEADER_TAGS` so correlation ids cross the gateway hop on the span.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-lms-gateway` | 292,481 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-lms-gateway` either — both searches return zero over seven days.

It is not silent. It is producing 292,481 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-lms-gateway`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-lms-gateway"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-lms-gateway
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-lms-gateway` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-lms-gateway env:prod

# APM Traces
service:prod-ms-lms-gateway env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-lms-gateway` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/lms-gateway/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Logging variables | none set — the service's own `application*.yaml` decides |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (15 September 2026).** This repository is on Spring Boot 2.7.18, so the new starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), Boot 3.x only) is not available to it until it upgrades. It stays on its own filters and Feign loggers, with the per-file fixes above; the shared-library fixes in [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) do not apply to it because it does not use `bravo-lib-logging`.
---

## Implementation status

**Pull request: [bravo-lms-gateway#2519](https://github.com/bfi-finance/bravo-lms-gateway/pull/2519)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-lms-gateway/tree/fix/logging), head `e0380966e`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-lms-gateway/pull/2519/files) · [Commits](https://github.com/bfi-finance/bravo-lms-gateway/pull/2519/commits) · [Compare against master](https://github.com/bfi-finance/bravo-lms-gateway/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commit:

- fix(logging): stop the request-logging filter capturing payment payloads

Files:

- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`
- `src/main/resources/application-prod.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Consolidate the 117 exception logs in `PaymentAdapterImpl.java` behind one handler
- [ ] Convert the survivors to structured warn lines without traces
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Pin `CommonsRequestLoggingFilter: WARN` in `application-prod.yaml`
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml` before log collection is fixed
- [ ] Reduce the 117 exception logs first, or fixing collection delivers 117 stack traces per failure
