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

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This repo built the best-designed
workaround in the Java estate, and then left it switched off.**

| | Seven days, production |
|---|---:|
| Spans | 5,291,885 |
| Log entries | 316,369 |
| Entries carrying a captured body | 8 |
| INFO entries | 47 |

### Two mechanisms, both dormant

- `WebConfig.java:62` and `:78` — `CommonsRequestLoggingFilter` with
  `setMaxPayloadLength(64000)`. This is item 1 above. It writes at the filter's own logger
  level, which sits above DEBUG in production, so nothing is emitted.
- `adapter/logger/FeignSlf4jLogger.java` — request and response bodies at Feign level FULL,
  gated on `logger.isDebugEnabled()`, truncated at
  `feign.client.config.default.max-chars-before-truncation: 5000`, and passed through
  `JsonMasker` first. `setting.features.enableBfiLogger` is `false` in
  `feature-properties.yml`, so the shared `bravo-lib-logging` filters are off as well.

47 INFO entries in seven days is the proof that none of this is running.

### The masking list is the asset here

`FeignSlf4jLogger.maskedField` covers, on both request and response:

- headers — `Authorization`, `api-secret`, `api-key`, `x-api-key`, `X-ACCESS-TOKEN`,
  `x-auth-app-id`, `x-auth-app-secret`, `client_secret`
- identity — `NIK`, `identity_number`, `id_number`, `idNumber`, `npwp_number`,
  `phone_number`, `email`
- credentials — `password`, `surveyor_password`, `username`, `accessKey`, `access_token`,
  `refresh_token`
- customer names — `customer.full_name`, `customer.spouse_name`,
  `customer.spouse_identity_number`

**No other repo in the pack masks this thoroughly.** When `bravo-bpm-service` is asked to
add masking to `CustomFeignLogger`, this is the list to copy.

### The 64 KB limit is the outlier

Every other `CommonsRequestLoggingFilter` in the estate uses 10,000 characters. This one
uses 64,000 — more than six times as much. Log lines over 16 KB are split by the container
runtime, so a 64 KB payload arrives in Datadog as four unparseable fragments. If the filter
is ever enabled, lower it to 10,000 first.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe.

Remote Configuration has to work first, and it does not: 207 failed polls in two days,
`empty targets meta in director local store`. Thirteen production services report it.

### What to do

1. Lower `setMaxPayloadLength` to 10,000 in both places, or move the bean behind
   `@Profile("local")`.
2. Leave `FeignSlf4jLogger` in place. It is correct and it is off. Do not delete it —
   it is the reference implementation for the rest of the estate.
3. Offer the `maskedField` list to the `bravo-lib-logging` maintainers and to the
   `bravo-bpm-service` squad.
4. Put onboarding identifiers on the span — `application_id`, `prospect_id`, the step name —
   so a stuck onboarding is findable without a payload.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-onboarding` | 5,244,564 spans |
| Logs | `prod-ms-onboarding` | 314,902 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-onboarding`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-onboarding"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-onboarding
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-onboarding` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-onboarding env:prod

# APM Traces
service:prod-ms-onboarding env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-onboarding` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Remove the `CommonsRequestLoggingFilter: DEBUG` entry from `application.yaml`
- [ ] Pin `CommonsRequestLoggingFilter`, `adapter` and `utils` levels in `application-prod.yaml`
- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Replace the payload filter with a method/path/status/duration filter if tracing is wanted
- [ ] Remove body logging from `AgentRegistrationImpl.java`
- [ ] Review the 18 exception logs in `EventProcessor.java`
- [ ] Leave the Hibernate `BasicBinder: TRACE` block commented out
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Lower `setMaxPayloadLength` from 64,000 to 10,000 in both `WebConfig.java` sites
- [ ] Keep `FeignSlf4jLogger` — it is the reference masking implementation for the estate
- [ ] Offer the `maskedField` list to the `bravo-lib-logging` maintainers and the bpm squad
