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

## Checklist

- [ ] Review the 108 exception-logging sites, starting with `MasterDataAdapterImpl.java`
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Pin `CommonsRequestLoggingFilter: WARN` in `application-prod.yaml`
- [ ] Replace body logging in `CommonListener.java` with message id and outcome
