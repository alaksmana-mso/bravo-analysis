# bravo-payment-service — logging fixes

**Squad:** Payment
**Production service:** `prod-ms-payment`
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

## 2. 8 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/util/AuthUtil.java` with 5.

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
| Body logging | 0 | `CommonListener.java` and client classes — log ids, not payloads |
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
span. Squads work around that by logging bodies. **This service does not, and the filter
that could is dormant.**

| | Seven days, production |
|---|---:|
| Spans | 304,460 |
| Log entries | 25,845 |
| of which `info` | 725 |
| Entries carrying a captured body | 0 |

`config/RequestLoggingFilterConfig.java` builds a `CommonsRequestLoggingFilter` with
`setIncludePayload(true)` and `setMaxPayloadLength(10000)`, prefix `REQUEST DATA : `. It
writes at the filter's own logger level, above DEBUG in production. Searching all of
production for `REQUEST DATA :` returns zero results, and 725 INFO entries in seven days
confirms it.

### The shared-library exposure

429 files in this repo import `com.bfi.logger.utils.LoggerUtil` from
`com.bfi.bravo:bravo-lib-logging` — **the heaviest use of that library anywhere in the
estate**. `LoggerUtil` is a wrapper, not a body logger, so it is not producing payloads
today. But it means any behaviour change in that library lands here first and hardest.

Fifteen repos depend on `bravo-lib-logging` and its source is not in `squads/`. That is a
gap worth closing regardless of this work.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For payment
flows that is the right shape: on demand, redacted by default, and gone afterwards.

Remote Configuration has to work first, and it is failing here: 477 failed polls in two
days, `unexpected response code Internal Server Error 500 ... empty targets meta in director
local store`. Thirteen production services report the same error.

### What to do

1. Pin the filter level explicitly in `application-prod.yaml` so it cannot wake up by
   accident.
2. Remove the dormant `loggerLevel: full` (item 1 above) — with 429 `LoggerUtil` call sites,
   this repo is the last place you want full Feign logging to switch on unnoticed.
3. Put payment identifiers on the span — `payment_id`, `agreement_no`, `voucher_no` — rather
   than expecting a body.
4. Ask who owns `bravo-lib-logging`, and where its source is.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-payment` | 301,375 spans |
| Logs | `prod-ms-payment` | 25,795 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-payment`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-payment"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-payment
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-payment` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-payment env:prod

# APM Traces
service:prod-ms-payment env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-payment` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Pin the Feign client package level explicitly in `application-prod.yaml`
- [ ] Review the 5 exception logs in `AuthUtil.java`, then the rest of the 8
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml`
- [ ] Ask who owns `com.bfi.bravo:bravo-lib-logging` and where its source lives
