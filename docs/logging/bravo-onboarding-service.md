# bravo-onboarding-service — logging fixes

**Squad:** Customer Platform
**Production service:** `prod-ms-onboarding`
**Stack:** Java, Spring Boot

This is the one repo where payload logging is switched on **explicitly, by name, in the
production profile** — and the one where the deployment manifest switches it back off.
`app-deployment/onboarding/values-prod.yaml` sets
`LOGGING_LEVEL_ORG_SPRINGFRAMEWORK_WEB_FILTER_COMMONSREQUESTLOGGINGFILTER=OFF` (read
14 September 2026), so item 1 below writes nothing in production today. An earlier version
of this file said nothing here depended on a manifest; that was wrong. The code fix still
stands, because one environment-variable edit turns 64 KB request bodies back on.

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
different keys — but the manifest does what the profile does not: it sets the Commons
filter's logger to `OFF`, leaves `utils` and `adapter` at DEBUG, and pins five more
packages (`adapter.http.oauth`, `aspect`, the RabbitMQ publisher and consumer) at DEBUG
explicitly. Datadog indexed five INFO lines from this service in the last 24 hours and no
request payload.

Result, as the code stands: every inbound request body, up to 64 KB, would be written to
Cloud Logging — on the onboarding service, so names, identity numbers, addresses and
document data. Today the manifest's `OFF` is the only thing preventing it.

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

The manifest does **not** switch this one off: nothing in `onboarding/values-prod.yaml`
overrides `id.co.bfi.bravo.adapter`, and the clients are built with
`new FeignSlf4jLogger(<Client>.class)` under that package. Yet Datadog indexes none of it —
no `--->`/`<---` markers, no body text, five INFO lines in 24 hours. Either the logback
configuration that `LOGGER_LEVEL=INFO` drives wins over Spring's per-package level, or a
Datadog index exclusion filter drops it; the one-minute check is Datadog's
`Logs → Configuration → Indexes` page. Either way, fixing item 1's YAML removes the DEBUG
level on `id.co.bfi.bravo.adapter` as well and closes this one for good.

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
| 1 — 64 KB inbound payloads | Rp 0 today — the manifest sets the filter `OFF` | high that it costs nothing now; the fix removes the switch that would turn it back on |
| 2 — Feign bodies | Rp 0 today — nothing indexed | medium; manifest does not override, Datadog shows none |
| 3 — body logs in services | Rp 1–2M | medium |
| 4 — exception logs | Rp 1–2M | medium |

Item 1 is still the change that matters — not for what it saves this month, but because it
is customer data behind one environment variable — and it is a three-line change.

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

### Three mechanisms, and the picture is not what it first looked like

`WebConfig` declares **two** request filters, selected by
`setting.features.loggingFilterV2`, and `feature-properties.yml` sets that to **true**:

- `requestLoggingFilter` — a plain `CommonsRequestLoggingFilter`, payload on, 64,000
  characters, **no masking**. Active only when the flag is `false`, so it is the inactive
  fallback.
- `applicationRequestLoggingFilter` — `ApplicationRequestLoggingFilter`, which overrides
  `getMessagePayload` to run the body through `JsonMasker` before it is logged. **This is
  the one that is wired**, and it is a good piece of work.

And `application.yaml:14` sets `CommonsRequestLoggingFilter: DEBUG` — hardcoded, not a
placeholder, with no override in `application-prod.yaml`. The override is in the
deployment: `values-prod.yaml` sets that logger to `OFF`. An earlier version of this file
said Datadog was dropping the DEBUG lines and Cloud Logging still paying for them; the
manifest says they are never written. That claim is withdrawn.

The third mechanism, `adapter/logger/FeignSlf4jLogger.java`, does bodies at Feign level
FULL gated on `logger.isDebugEnabled()`, truncated at 5,000 characters, masked.
`setting.features.enableBfiLogger` is `false`, so the shared `bravo-lib-logging` filters
are off.

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

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
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

## In the production deployment

Read from `app-deployment/onboarding/values-prod-sharia.yaml`, `app-deployment/onboarding/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `INFO` |
| `SENSITIVE_KEYS` | `password,token,secret,key,authorization,api-secret,api-ke…` (31 fields) |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | `false` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It wires the library's `RequestLoggingFilter` and `FeignClientFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.

**Proposed change to this file:** section §4 of [deployment-proposal.md](deployment-proposal.md) — raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on 14 September 2026 (branch `fix/logging`), awaiting SRE review.


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Migrating off `bravo-lib-logging` means deleting the `logback*.xml` files and the manual filter beans, and telling SRE that the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bravo-onboarding-service#6328](https://github.com/bfi-finance/bravo-onboarding-service/pull/6328)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-onboarding-service/tree/fix/logging), head `f3bb118aa`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-onboarding-service/pull/6328/files) · [Commits](https://github.com/bfi-finance/bravo-onboarding-service/pull/6328/commits) · [Compare against master](https://github.com/bfi-finance/bravo-onboarding-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.15. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `bravo-lib-logging`, its filter beans and `logback*.xml` in the same change; the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`).

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is red only on **`Codacy Diff Coverage`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 3 Codacy thread(s); 2 fixed in `d67fa4daa` (fix(logging): give the V2 request filter its own level switch; drop the unused payload cap); 1 declined with the reason in the thread. Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commit:

- fix(logging): cut the 64 KB payload cap and stop the unmasked filter capturing bodies

Files:

- `src/main/java/id/co/bfi/bravo/config/WebConfig.java`
- `src/main/resources/application.yaml`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
