# bravo-agreement-service — logging fixes

**Squad:** Contract Collateral \& Loan Calculation
**Production service:** `prod-ms-agreement`
**Stack:** Java, Spring Boot

`loggerLevel: full` is set here and currently emits nothing. The real work is the
exception logging.

---

## 1. `loggerLevel: full` — dormant, but remove it

`src/main/resources/application.yaml` sets `feign.client.config.default.loggerLevel: full`.

It produces no output. The Feign client packages sit at INFO in the production profile, and
Feign only writes bodies at DEBUG. Verified by resolving the effective level for every
Feign client interface in this repo against `application.yaml` plus
`application-prod.yaml`.

So there is no saving here. There is a risk: a default of `full` means one
`logging.level` line, or one environment variable, starts writing upstream request and
response bodies into Cloud Logging.

### Fix

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
```

`basic` logs method, URL, status and timing. That covers most debugging and carries no
payload. Set `full` per client, in non-production profiles, where somebody can say why.

---

## 2. 209 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/service/document/impl/LoanApplicationDocumentStrategyServiceImpl.java` with 22.

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
| Body logging | 19 | `CommonListener.java` and client classes — log ids, not payloads |
| Payload-logging filter | registered | Limit 10000; dormant at INFO in prod, same as item 1 |
| DEBUG/TRACE in YAML | a few | Local and standalone profiles only |
| `System.out.print` | a few | All in `src/test/` — harmless |

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — `loggerLevel: full` | Rp 0 | risk removal only |
| 2 — exception logs | Rp 1–4M | medium |
| 3 — body logging | under Rp 1M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service has the second-largest trace
volume in the estate and sends no logs at all, so neither route works today.**

| | Seven days, production |
|---|---:|
| Spans | 7,504,233 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-agreement` returns no results in Datadog Logs over seven days, under either
`service:` or `kube_deployment:`. The service identity section below covers why.

### What exists in the code

`config/RequestLoggingFilterConfig.java` builds a `CommonsRequestLoggingFilter` with
`setIncludePayload(true)` and `setMaxPayloadLength(10000)`, prefix `Incoming Request: `, and
`beforeRequest` deliberately suppressed to avoid duplicate lines. It writes at the filter's
own logger level, which sits above DEBUG in production. Searching all of production for
`Incoming Request:` returns zero results, which confirms it.

### Two files that look like body logging and are not

Do not "clean these up" as part of this work:

- `config/CachedBodyFilter.java` wraps the request so the body can be read more than once.
  It logs nothing.
- `config/web/ResponseWrapperFilter.java` builds the `BaseResponse` envelope for
  `MouMaintenanceController` and `SpecialOrderSelectionController`. It reads the response
  body to re-shape it, not to record it.

Both are load-bearing. Removing either breaks behaviour.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For a service
with 7.5 million spans a week and no logs, this is the shortest path to being able to debug
anything at all.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Fix log collection, after the exclusion filters exist, so 7.5 million spans' worth of
   service finally has logs to go with them.
2. Keep `setIncludePayload(false)` in mind when you do — pin the filter level explicitly in
   `application-prod.yaml` so fixing collection does not also switch on payload capture.
3. Then ask for Live Debugger, and put agreement identifiers on the span in the meantime.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-agreement` | 7,424,485 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-agreement` either — both searches return zero over seven days.

It is not silent. It is producing 7,424,485 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-agreement`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-agreement"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-agreement
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-agreement` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-agreement env:prod

# APM Traces
service:prod-ms-agreement env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-agreement` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Pin the Feign client package level explicitly in `application-prod.yaml`
- [ ] Review the 22 exception logs in `LoanApplicationDocumentStrategyServiceImpl.java`, then the rest of the 209
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml` before log collection is fixed
- [ ] Leave `CachedBodyFilter` and `ResponseWrapperFilter` alone — they are not logging code
