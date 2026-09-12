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

## Checklist

- [ ] Review the 23 exception logs in `BillingServiceImpl.java`, then the rest of the 624
- [ ] Replace body logging in `RabbitmqPublisher.java` with routing key, id and size
- [ ] Move loop logging out of the loop in `InsurancePaymentCommandService` and `SppaCommandService`
- [ ] Replace all 14 `printStackTrace()` in `src/main/java` with logger calls
- [ ] Replace all 10 `System.out.print` in `src/main/java` with logger calls
- [ ] Check `application-sit.yaml` and `application-uat.yaml` for debug levels
