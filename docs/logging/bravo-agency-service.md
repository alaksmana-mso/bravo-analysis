# bravo-agency-service — logging fixes

**Squad:** Agency
**Production service:** `prod-ms-agency`
**Stack:** Java, Spring Boot

This repo logs inbound request bodies **by default**. Whether that is happening in
production depends on a deployment environment variable that is not in this repo.

---

## 1. Payload logging defaults to DEBUG

Two halves.

**The filter** — `src/main/java/com/bfi/bravo/config/WebConfig.java`:

```java
filter.setIncludePayload(true);
filter.setMaxPayloadLength(64000);
```

**The level** — `src/main/resources/application.yaml` sets adapter, RestTemplate and CommonsRequestLoggingFilter using a placeholder
with a DEBUG fallback:

```yaml
CommonsRequestLoggingFilter: ${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:DEBUG}
```

`CommonsRequestLoggingFilter` writes at DEBUG. So **unless the deployment sets
`LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER` to something higher, every inbound request
body up to 64000 bytes is written to Cloud Logging.**

### The check

The manifests are not in this repo. One command settles it:

```bash
kubectl -n prod set env deploy/<this-service> --list | grep -i logging
```

If the variable is absent, payload logging is live and this is the repo's main cost and
data-exposure item. If it is set to INFO or WARN, this is dormant and only item 2 matters.

### Fix, either way

A default of DEBUG for a payload-logging filter is the wrong default. Invert it so the
safe state is the one you get when nobody configures anything:

```yaml
CommonsRequestLoggingFilter: ${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:WARN}
```

Better still, set `setIncludePayload(false)` and keep query string, status and duration.
Those answer most debugging questions without putting request bodies in logs.

If the payload is genuinely needed locally, put the `@Bean` behind `@Profile("local")`.

---

## 2. 54 exception logs passing the throwable

Each `log.error(msg, e)` can emit a full stack trace, and multi-line aggregation is off
cluster-wide, so one trace becomes one entry per frame.

Split them: structured warn lines for expected upstream failures, traces only where a
person would need one.

---

## 3. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — payload logging | Rp 2–8M **if live**, Rp 0 if the env var is set | unknown until checked |
| 2 — exception logs | Rp 1–2M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service is one environment variable
away from doing it at scale.**

| | Seven days, production |
|---|---:|
| Spans | 1,169,815 |
| Log entries | 126,432 |
| Entries carrying a captured body | 0 |

### Why nothing is being captured today

`application.yaml:21` sets `loggerLevel: ${FEIGN_LOGGER_LEVEL:FULL}` — Feign is at FULL by
default. What stops the bodies reaching Datadog is `client/logger/FeignSlf4jLogger.java`,
which writes only inside `if (logger.isDebugEnabled())`. Production sits above DEBUG, so the
whole class is a no-op.

That is a single YAML default away from turning 126,432 log entries a week into something
several times larger, with request and response bodies in every entry. Item 1 above covers
the fix; this is why it matters beyond the bill.

`LoggerConfiguration` also registers `bravo-lib-logging`'s `RequestLoggingFilter`
unconditionally — no `@ConditionalOnProperty`, unlike `bravo-onboarding-service` and
`bravo-inventory-management-service`. It is dormant for the same reason, not by design.

### What this repo does mask

`FeignSlf4jLogger.MASKED_FIELD` covers `Authorization`, `api-secret`, `x-api-key`,
`X-ACCESS-TOKEN`, `x-auth-app-id` and `x-auth-app-secret`. Headers only — **bodies are not
masked**. Agency payloads carry agent identity and commission data, so if the level is ever
lowered, that list needs body entries too. `bravo-onboarding-service`'s `maskedField` list
is the one to copy.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. No redeploy,
nothing left running.

Remote Configuration has to work first, and it does not: 452 failed polls in two days,
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store`. Thirteen production services report the same error.

### What to do

1. Pin `FEIGN_LOGGER_LEVEL` to `BASIC` in the production manifest rather than relying on the
   logger level to save you.
2. Add body entries to `MASKED_FIELD` before anyone lowers the level for an investigation.
3. Put agent and agreement identifiers on the span instead of expecting them in a body.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-agency` | 1,155,938 spans |
| Logs | `prod-ms-agency` | 128,406 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-agency`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-agency"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-agency
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-agency` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-agency env:prod

# APM Traces
service:prod-ms-agency env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-agency` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Run the `kubectl set env --list` check above and record the answer
- [ ] Change the YAML default from `:DEBUG` to `:WARN`
- [ ] Set `setIncludePayload(false)` in `WebConfig.java`, or move the bean behind `@Profile("local")`
- [ ] Pin the filter level explicitly in `application-prod.yaml`
- [ ] Review the 54 exception-logging sites
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Pin `FEIGN_LOGGER_LEVEL` to `BASIC` in the production manifest — it defaults to `FULL`
- [ ] Add body entries to `FeignSlf4jLogger.MASKED_FIELD`; today it masks headers only
