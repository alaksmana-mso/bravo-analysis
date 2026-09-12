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

These files live in the GitOps repo, not here. This repo deploys through
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

## Checklist

- [ ] Review the 108 exception-logging sites, starting with `MasterDataAdapterImpl.java`
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Pin `CommonsRequestLoggingFilter: WARN` in `application-prod.yaml`
- [ ] Replace body logging in `CommonListener.java` with message id and outcome
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml`
- [ ] Add one INFO line per business outcome — five INFO entries a week is not observability
