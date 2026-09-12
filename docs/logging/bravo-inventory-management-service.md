# bravo-inventory-management-service — logging fixes

**Squad:** Asset Management
**Production service:** `prod-inventory-management`
**Stack:** Java, Spring Boot

This is the only repo in the estate with `loggerLevel: full` written directly into
`application-prod.yaml`. It happens to be harmless today. It is one line from not being.

---

## 1. `loggerLevel: full` in the production profile

`src/main/resources/application-prod.yaml`, lines 1–7:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: full
        connectTimeout: 30000
        readTimeout: 30000

logging:
  level:
    root: WARN
```

18 Feign client interfaces are covered by that `default`.

**It emits nothing.** Feign writes bodies at DEBUG, and `root: WARN` puts every logger two
levels above that. No package-specific override raises them.

So the current cost is zero. But this configuration says "log every upstream request and
response body in production" and is relying on a separate setting, in the same file, to
contradict it. Anyone who later adds a package-level debug entry to chase a bug turns on
full body logging for 18 clients without realising.

Of the six repos carrying `loggerLevel: full`, this is the one most likely to surprise
someone, because the other five at least keep it out of the production profile.

### Fix

Delete the `loggerLevel: full` line. Keep the timeouts:

```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 30000
        readTimeout: 30000
```

Two minutes of work. No behaviour change.

---

## 2. Five DEBUG entries in the SIT profile

`src/main/resources/application-sit.yaml` carries five DEBUG/TRACE levels and a
`loggerLevel: full`, plus a payload-logging filter entry.

SIT runs in `bravo-project-nonprod`, which costs **Rp 56.4M a month** in Cloud Logging. Non-
production debug settings are not free — they are a third of the logging bill estate-wide.

### Fix

Lower SIT to INFO. If a developer needs debug in SIT, they can set it for an afternoon and
put it back. It should not be the committed default.

---

## 3. Smaller items

| Item | Count | Note |
|---|---:|---|
| Payload-logging filter entries | 3 | In `application-sit.yaml`, `application-local.yaml` and one more — not prod |
| `show-sql: true` | 1 | `application-local.yaml` only — fine |
| Exception logs with throwable | 5 | `AgreementServiceImpl.java` (2) and others — low |

This repo is in good shape apart from item 1. Five exception-logging sites is the lowest
count of any Java service reviewed.

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — remove `loggerLevel: full` from prod | Rp 0 today | removes a risk, not a cost |
| 2 — lower SIT debug levels | Rp 1–3M | medium |

---

## Checklist

- [ ] Delete `loggerLevel: full` from `application-prod.yaml`
- [ ] Lower the five DEBUG/TRACE entries in `application-sit.yaml` to INFO
- [ ] Remove `loggerLevel: full` from `application-sit.yaml`
