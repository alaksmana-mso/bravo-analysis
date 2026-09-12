# bravo-onboarding-service — logging fixes

**Squad:** Customer Platform
**Production service:** `prod-ms-onboarding`
**Stack:** Java, Spring Boot

This is the one repo where payload logging is switched on **explicitly, by name, and
confirmed active in the production profile**. Unlike the Feign case in
[bravo-bpm-service](bravo-bpm-service.md), nothing here depends on a deployment manifest.

It is also the service that handles customer onboarding, so the bodies being logged are
customer records.

---

## 1. Inbound request bodies up to 64 KB are logged

Two halves, both in this repo.

**The filter** — `src/main/java/id/co/bfi/bravo/config/ApplicationRequestLoggingFilter.java`
and `WebConfig.java` register `CommonsRequestLoggingFilter` with:

- `setIncludePayload(true)`
- `setMaxPayloadLength(64000)`

**The level** — `src/main/resources/application.yaml`:

```yaml
logging:
  level:
    org:
      springframework:
        web:
          filter:
            CommonsRequestLoggingFilter: DEBUG
    id:
      co:
        bfi:
          bravo:
            utils: DEBUG
            adapter: DEBUG
```

`src/main/resources/application-prod.yaml` sets `root: INFO`, `hibernate: WARN` and
`security: INFO`. It overrides **none** of the three DEBUG entries above. They are
different keys, so all three stay at DEBUG in production.

Result: every inbound request body, up to 64 KB, is written to Cloud Logging. On the
onboarding service. That means names, identity numbers, addresses and document data.

### Fix

Delete the `CommonsRequestLoggingFilter` entry from `application.yaml`. If anyone wants it
for local debugging, put it in `application-local.yaml` where it belongs.

Then pin the levels in `application-prod.yaml` so this cannot come back:

```yaml
logging:
  level:
    root: INFO
    org.springframework.web.filter.CommonsRequestLoggingFilter: WARN
    id.co.bfi.bravo.adapter: INFO
    id.co.bfi.bravo.utils: INFO
```

If request tracing is genuinely needed in production, log the method, path, status and
duration. Not the body. A filter that does that is about fifteen lines and carries no
customer data.

---

## 2. Feign full-body logging on top

`application.yaml` also sets:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: full
        max-chars-before-truncation: 5000
```

All **17** Feign client interfaces sit under `id.co.bfi.bravo.adapter.http.*`, which the
block in item 1 puts at DEBUG. So outbound bodies are logged too, truncated at 5,000
characters.

The clients include `keycloak`, `ocr`, `duplicatecheck`, `dms` and `hardrac` — identity
documents, OCR results and duplicate-check payloads.

The same production caveat from [bravo-bpm-service](bravo-bpm-service.md) applies: no
`END HTTP` markers and no `status:debug` entries appear anywhere in production. So this may
be suppressed by a deployment environment variable.

**But item 1 is not affected by that caveat**, because `CommonsRequestLoggingFilter` is
named explicitly in the YAML. Fixing item 1 fixes the DEBUG level on
`id.co.bfi.bravo.adapter` at the same time, which closes this one too.

### Fix

Change the default to `basic` while you are in the file:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
```

---

## 3. 49 body logs in service code

Highest concentration:

- `src/main/java/id/co/bfi/bravo/services/impl/AgentRegistrationImpl.java` — 10

Agent registration payloads carry personal data. Log the agent id and the outcome.

---

## 4. 96 exception logs passing the throwable

Highest concentration:

- `src/main/java/id/co/bfi/bravo/services/consumer/EventProcessor.java` — 18

A consumer that logs a full trace per failed message produces a lot of output when an
upstream is down. Log one structured line with the message id and the reason; keep the
trace for genuinely unexpected failures.

---

## 5. Smaller items

| Item | Count | Note |
|---|---:|---|
| Logging inside a loop | 7 | `validator/v4/helper/CorporateValidationHelper.java` and others — volume scales with document count |
| `printStackTrace()` | 4 | All in `src/test/` — harmless |
| DEBUG/TRACE in YAML | 9 | Local and standalone profiles only, apart from the prod-active ones in item 1 |

`application.yaml` also has a commented-out Hibernate SQL and `BasicBinder: TRACE` block.
Leave it commented. `BasicBinder: TRACE` logs every bound SQL parameter, which on this
service would mean every identity number passing through JPA.

---

## 6. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — 64 KB inbound payloads | Rp 5–12M | high, and it removes customer data from logs |
| 2 — Feign bodies | Rp 0–5M | unknown, same manifest question as bpm-service |
| 3 — body logs in services | Rp 1–2M | medium |
| 4 — exception logs | Rp 1–2M | medium |

Item 1 is the one that matters, and it is a three-line change.

---

## Checklist

- [ ] Remove the `CommonsRequestLoggingFilter: DEBUG` entry from `application.yaml`
- [ ] Pin `CommonsRequestLoggingFilter`, `adapter` and `utils` levels in `application-prod.yaml`
- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Replace the payload filter with a method/path/status/duration filter if tracing is wanted
- [ ] Remove body logging from `AgentRegistrationImpl.java`
- [ ] Review the 18 exception logs in `EventProcessor.java`
- [ ] Leave the Hibernate `BasicBinder: TRACE` block commented out
