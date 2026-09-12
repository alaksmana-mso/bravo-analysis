# bravo-lms-gateway — logging fixes

**Squad:** Contract Collateral & Loan Calculation (also under Payment, Tele Marketing)
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

## Checklist

- [ ] Consolidate the 117 exception logs in `PaymentAdapterImpl.java` behind one handler
- [ ] Convert the survivors to structured warn lines without traces
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Pin `CommonsRequestLoggingFilter: WARN` in `application-prod.yaml`
