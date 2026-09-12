# bravo-payment-service — logging fixes

**Squad:** Payment
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

## Checklist

- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Pin the Feign client package level explicitly in `application-prod.yaml`
- [ ] Review the 5 exception logs in `AuthUtil.java`, then the rest of the 8
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
