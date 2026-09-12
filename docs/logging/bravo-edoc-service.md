# bravo-edoc-service — logging fixes

**Squad:** Operation Post-Go Live
**Stack:** Java, Spring Boot

`loggerLevel: full` is set here on one client and currently emits nothing. The real work
is the exception logging.

---

## 1. `loggerLevel: full` on `ApigeeApiClient` — dormant, but scope it properly

`src/main/resources/application.yaml`:

```yaml
feign:
  client:
    config:
      ApigeeApiClient:
        loggerLevel: full
```

Unlike the other five repos carrying `loggerLevel: full`, this one is **not** on
`feign.client.config.default`. It targets a single client, `ApigeeApiClient`. That is
already the right shape — somebody scoped it deliberately instead of turning it on estate-
wide.

It produces no output today. `application-prod.yaml` sets no logging levels at all, so the
service falls back to `application.yaml`, where `root` is `${LOGGING_LEVEL_ROOT:#{INFO}}` —
INFO unless the deployment says otherwise. Feign writes bodies at DEBUG, so nothing is
emitted.

### Two things to close

1. **The root level is environment-variable driven with no production pin.** If anyone sets
   `LOGGING_LEVEL_ROOT=DEBUG` to chase a bug, Apigee request and response bodies start
   flowing into Cloud Logging, along with everything else at DEBUG across the service. Pin
   it explicitly:

   ```yaml
   # application-prod.yaml
   logging:
     level:
       root: INFO
   ```

2. **Decide whether `ApigeeApiClient` still needs `full`.** If it was added to debug an
   integration that now works, drop it to `basic`. If it is genuinely needed, leave it —
   the blast radius is one client, which is acceptable.

`application-prod.yaml` currently carries no `logging` block. Adding one is the fix for
item 1 and takes a minute.

## 2. 175 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/service/impl/MessageServiceImpl.java` with 17.

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
| Body logging | 7 | `CommonListener.java` and client classes — log ids, not payloads |
| Payload-logging filter | registered | Limit none; dormant at INFO in prod, same as item 1 |
| DEBUG/TRACE in YAML | a few | Local and standalone profiles only |
| `System.out.print` | a few | All in `src/test/` — harmless |

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — pin the root level in prod | Rp 0 | risk removal only |
| 2 — exception logs | Rp 1–4M | medium |
| 3 — body logging | under Rp 1M | medium |

---

## Checklist

- [ ] Add a `logging.level.root: INFO` block to `application-prod.yaml`
- [ ] Decide whether `ApigeeApiClient` still needs `loggerLevel: full`, or drop it to `basic`
- [ ] Review the 17 exception logs in `MessageServiceImpl.java`, then the rest of the 175
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
