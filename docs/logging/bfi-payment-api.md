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

## Checklist

- [ ] Change `loggerLevel: FULL` to `basic` in `application-dev.yaml`
- [ ] Lower the six DEBUG/TRACE entries in `application-dev.yaml` to INFO
- [ ] Leave `application-local-standalone.yaml` as it is
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Replace the 27 `System.out.print` in the scenario test with assertions
