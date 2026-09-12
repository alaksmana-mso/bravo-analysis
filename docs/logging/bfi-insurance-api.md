# bfi-insurance-api — logging fixes

**Squad:** Insurance (also checked out under Tele Marketing)
**Production service:** `prod-ms-bfi-insurance-api`
**Stack:** Java, Spring Boot

Production shows 451,528 warnings and 338,565 errors over seven days. This repo has the
second-highest weighted logging risk in the estate, and unlike `bravo-bpm-service` none of
it depends on a deployment manifest — it is all in the code.

---

## 1. 624 exception logs passing the throwable

The highest count in any repo. Concentrated in:

| File | Count |
|---|---:|
| `src/main/java/id/co/bfi/insurance/service/billing/impl/BillingServiceImpl.java` | 23 |

Every `log.error("...", e)` can emit a full stack trace, and with multi-line aggregation
off cluster-wide, each trace becomes one log entry per frame.

### Fix

Split them. Where the failure is expected — an upstream 4xx, a validation failure, a
missing record — log one structured line:

```java
log.warn("billing lookup failed: policyNo={} status={} reason={}",
         policyNo, status, e.getMessage());
```

Keep the throwable only where the failure is genuinely unexpected and somebody would need
the trace to diagnose it. That is a small minority of 624.

Start with `BillingServiceImpl` — it is the densest file and billing runs on a schedule, so
its logging multiplies.

---

## 2. 82 body logs, including the message broker

| File | Count |
|---|---:|
| `src/main/java/id/co/bfi/insurance/broker/publisher/RabbitmqPublisher.java` | 7 |

A publisher that logs every message body logs every insurance payload that crosses the
broker — policy holder details, claim data, premium calculations.

### Fix

Log the routing key, message id and size. Not the body:

```java
log.info("published: exchange={} routingKey={} messageId={} bytes={}",
         exchange, routingKey, messageId, payload.length());
```

If somebody needs the body to debug, they can get it from the broker.

---

## 3. 36 logs inside loops

| File | Count |
|---|---:|
| `src/main/java/id/co/bfi/insurance/command/service/payment/InsurancePaymentCommandService.java` | 2 |
| `src/main/java/id/co/bfi/insurance/command/service/sppa/SppaCommandService.java` | 2 |

Volume scales with the size of the input. A batch of 10,000 payments produces 10,000 log
lines from one operation, and nobody reads them.

### Fix

Log once before the loop with the count, once after with the outcome. Log inside the loop
only on failure, and consider capping that too:

```java
log.info("processing {} payments for batch {}", payments.size(), batchId);
// ... loop, log only failures ...
log.info("batch {} done: ok={} failed={}", batchId, ok, failed);
```

---

## 4. 14 `printStackTrace()` and 10 `System.out.print`

| File | Item | Count |
|---|---|---:|
| `src/main/java/id/co/bfi/insurance/command/action/excel/ExcelGenerateCommandAction.java` | `printStackTrace` | 4 |
| `src/main/java/id/co/bfi/insurance/util/XlsxReportUtil.java` | `System.out` | 2 |
| `src/main/java/id/co/bfi/insurance/command/service/claim/header/ClaimHeaderCommandService.java` | `System.out` | 2 |

These are worse than they look. Both bypass the logging framework: no level, no correlation
id, no structure. They cannot be filtered, excluded or routed. An exclusion filter written
later will not catch them.

These are in `src/main/java`, not tests, so they run in production.

### Fix

Replace every one with a logger call. This is mechanical and worth doing in a single pass.

---

## 5. Non-production profiles

`loggerLevel: full` appears in `src/main/resources/application-unit-test.yaml`. That is
harmless — unit tests do not ship.

Four DEBUG/TRACE entries sit in local and unit-test profiles. Also fine.

But note that non-production Cloud Logging costs Rp 56.4M a month across the estate. If
this service runs in SIT or UAT with debug levels on, it contributes. Check
`application-sit.yaml` and `application-uat.yaml` when you do the pass in item 4.

---

## 6. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — exception logs | Rp 4–8M | medium |
| 2 — broker body logging | Rp 2–4M | medium, and it removes policy data from logs |
| 3 — logs in loops | Rp 1–3M | medium |
| 4 — `printStackTrace` / `System.out` | under Rp 1M | high, but they block future filtering |

About Rp 7–16M a month. The largest single code-level saving outside `bravo-bpm-service`.

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service does log bodies in
production — but not through the filter that was written for it, and the payloads carry
customer identity data.**

| | Seven days, production |
|---|---:|
| Spans | 305,978 |
| Log entries | 799,198 |
| Entries containing a serialised payload | 90,553 |

### The filter built for this is not the one producing bodies

`src/main/java/id/co/bfi/insurance/config/HttpJsonLoggingFilter.java` captures the inbound
request body as a structured field, truncated at
`constant.insurance.log-http-request-response-payload-max-size` (default 10,000), at INFO,
and only when a correlation id is already in the MDC.

In production it produces almost nothing. Zero log entries in seven days start with
`Request `, which is the message this filter writes, and the service emits only 12,928 INFO
entries out of 799,198. It is dead weight as configured.

Note also what it does *not* do: it reads `ContentCachingRequestWrapper`, so it captures the
**request** only. There is no response-body capture anywhere in this repo.

### What is actually writing payloads

Two error paths, both at scale:

- The RabbitMQ consumer dead-letter handler. `Exception(won't retry, direct to dead queue)
  while executing idempotencyKey ..., consumer: notify-disbursement-status, payload {...}` —
  and that payload carries `account_no_to`, `account_name_to`, `bank_name_to`,
  `amount_paid` and the agreement number. 377 of one variant alone in two days.
- The life-insurance customer update. `life insurance - Update customer data failed -
  customer data not found, payload : {...}` — that payload carries a 16-digit `id_number`
  (NIK), four full addresses, `birth_date` and `mobile_phone`. 92 in two days.

Neither is masked. Neither needs the whole payload to be diagnosable.

### What you get back

This service is Java, so Datadog's Live Debugger can set a **method probe**: name a method,
get its arguments and its return value from the running pod, no redeploy. That covers the
"what did the consumer actually receive" question far better than a dead-letter log line.

It needs Remote Configuration, and Remote Configuration is failing here — 579 failed polls
in two days, `empty targets meta in director local store`. Thirteen production services
report the same error. SRE has to fix that before anything can be switched on.

### What to do

1. Replace the payload in the dead-letter error with identifiers: idempotency key,
   `reference_id`, `agreement_number`, `branch_id`, and the exception message. The payload
   itself is already in the dead-letter queue, which is where it belongs.
2. Same for the life-insurance path: log `guid`, `cif_id` and `confins_customer_id`, not the
   customer record.
3. Decide what `HttpJsonLoggingFilter` is for. Today it costs a `ContentCachingRequestWrapper`
   on every request and emits almost nothing. Either scope it deliberately or remove it. If
   it is kept, give it field masking — it has none.
4. Put the identifiers on the span so the call is findable without a body:

   ```java
   final Span span = GlobalTracer.get().activeSpan();
   if (span != null) {
     span.setTag("insurance.agreement_no", agreementNo);
     span.setTag("insurance.reference_id", referenceId);
   }
   ```

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bfi-insurance-api` | 306,785 spans |
| Logs | `prod-ms-bfi-insurance-api` | 802,536 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bfi-insurance-api`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bfi-insurance-api"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bfi-insurance-api
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bfi-insurance-api` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bfi-insurance-api env:prod

# APM Traces
service:prod-ms-bfi-insurance-api env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bfi-insurance-api` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Review the 23 exception logs in `BillingServiceImpl.java`, then the rest of the 624
- [ ] Replace body logging in `RabbitmqPublisher.java` with routing key, id and size
- [ ] Move loop logging out of the loop in `InsurancePaymentCommandService` and `SppaCommandService`
- [ ] Replace all 14 `printStackTrace()` in `src/main/java` with logger calls
- [ ] Replace all 10 `System.out.print` in `src/main/java` with logger calls
- [ ] Check `application-sit.yaml` and `application-uat.yaml` for debug levels
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Replace the dead-letter payload dump with idempotency key, reference id and agreement number
- [ ] Replace the life-insurance customer payload with `guid`, `cif_id` and `confins_customer_id`
- [ ] Decide whether `HttpJsonLoggingFilter` is meant to be live; if kept, give it field masking
- [ ] Chase SRE on the Remote Configuration failure — 579 failed polls in two days
