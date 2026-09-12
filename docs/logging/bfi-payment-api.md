# bfi-payment-api — logging fixes

**Squad:** Payment
**Production service:** `prod-ms-bfi-payment-api`
**Stack:** Java, Spring Boot

Nothing in this repo is misconfigured for production. Everything found is in non-production
profiles — which still costs **Rp 56.4M a month** estate-wide, so it is worth a pass.

---

## 1. Non-production profiles carry debug settings

| Setting | File | Value |
|---|---|---|
| `loggerLevel: FULL` ×2 | `application-dev.yaml` | full request/response bodies |
| `loggerLevel: FULL` ×3 | `application-local-standalone.yaml` | full request/response bodies |
| `show-sql: true` ×2 | `application-local-standalone.yaml` | every SQL statement |
| DEBUG/TRACE ×6 | `application-dev.yaml` | |
| DEBUG/TRACE ×4 | `application-local-standalone.yaml` | |

`application-prod.yaml` is clean. `application-local-standalone.yaml` runs on a developer's
machine and costs nothing.

**`application-dev.yaml` is the one that matters.** The dev environment runs in
`bravo-project-nonprod`, which bills Rp 56.4M a month for Cloud Logging — 21% of the whole
logging line. Full Feign bodies plus six debug levels on a payment service is a meaningful
share of that.

### Fix

In `application-dev.yaml`:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
logging:
  level:
    root: INFO
```

Developers who need full bodies in dev can set an environment variable for the afternoon.
It should not be the committed default for a shared environment.

Leave `application-local-standalone.yaml` alone. It never leaves a laptop.

---

## 2. `CommonsRequestLoggingFilter` — dormant in prod

`src/main/java/id/co/bfi/bfipaymentapi/config/RequestLoggingFilterConfig.java` registers
the filter with payload logging and a 10 KB limit. Its logger sits at INFO in production,
so it emits nothing.

One more entry sits in `logback-backup.xml`, which is not loaded.

### Fix

Same as elsewhere: `setIncludePayload(false)`, or `@Profile("local")` on the bean, and pin
the level in `application-prod.yaml`. Payment request bodies carry account and amount data.

---

## 3. 27 `System.out.print` — all in tests

`src/test/java/id/co/bfi/bfipaymentapi/utils/PaymentPointGroupBillingUtilsUserScenarioTest.java`
has all 27.

They do not ship. Worth replacing with assertions on principle — a test that prints instead
of asserting is not testing much — but this is not a logging cost item.

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — dev profile debug and Feign full | Rp 2–5M | medium, part of the non-prod line |
| 2 — dormant payload filter | Rp 0 today | risk removal |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This repo is the one that handles it
correctly, and it should be cited as the pattern when other squads are asked to change.**

| | Seven days, production |
|---|---:|
| Spans | 669,038 |
| Log entries | 70,880 |
| Entries carrying a captured body | 0 |

### Why it is right

`RequestLoggingFilterConfig` declares two beans, not one:

```java
@Bean @Profile("!prod")   // payload and headers included
@Bean @Profile({ "prod" }) // setIncludePayload(false), setIncludeHeaders(false)
```

and `FeignLoggingInterceptor`, which sets `Logger.Level.FULL`, is `@Profile("!prod")`
throughout. Developers get full bodies where they need them and production gets none. That
is the shape every other Java repo in this pack should end up in.

### The consequence, which is the point

Because it is right, this squad has **no body visibility in production at all**. When a
BCA VA or SNAP-BI call misbehaves in prod, there is nothing to look at beyond status and
duration. That is exactly the gap the other squads filled with always-on logging — so this
squad has the strongest claim on the replacement, not the weakest.

### What the replacement is

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. No redeploy, no
always-on logging, nothing left running.

It needs Remote Configuration, and Remote Configuration is failing on this service more than
on any other: **679 failed polls in two days**, `unexpected response code Internal Server
Error 500 ... empty targets meta in director local store`. Thirteen production services
report the same error.

### What to do

1. Nothing to remove. Do not "tidy up" the two-bean arrangement — it is the fix, not a
   leftover.
2. Ask SRE for the Remote Configuration fix. This service is the best pilot candidate:
   highest failure count, cleanest logging, and a real unmet need.
3. Ask SRE for `DD_TRACE_HEADER_TAGS` so correlation ids land on spans. For a payment
   gateway that answers a large share of "which call was this" questions on its own.
4. Where a field is needed on every request rather than during a debugging session, put it
   on the span:

   ```java
   final Span span = GlobalTracer.get().activeSpan();
   if (span != null) {
     span.setTag("payment.partner_ref", partnerReference);
     span.setTag("payment.va_number_masked", maskedVa);
   }
   ```

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bfi-payment-api` | 663,598 spans |
| Logs | `prod-ms-bfi-payment-api` | 70,100 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bfi-payment-api`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bfi-payment-api"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bfi-payment-api
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bfi-payment-api` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bfi-payment-api env:prod

# APM Traces
service:prod-ms-bfi-payment-api env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bfi-payment-api` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Change `loggerLevel: FULL` to `basic` in `application-dev.yaml`
- [ ] Lower the six DEBUG/TRACE entries in `application-dev.yaml` to INFO
- [ ] Leave `application-local-standalone.yaml` as it is
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Replace the 27 `System.out.print` in the scenario test with assertions
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Leave the two-bean `RequestLoggingFilterConfig` alone — it is the pattern, not a leftover
- [ ] Volunteer this service as the Live Debugger pilot: cleanest logging, highest Remote Configuration failure count
- [ ] Ask SRE for `DD_TRACE_HEADER_TAGS` so partner correlation ids land on spans
