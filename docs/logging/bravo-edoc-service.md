# bravo-edoc-service — logging fixes

**Squad:** Operation Post-Go Live
**Production service:** `prod-ms-edoc`
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

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This squad did something different, and
it is the clearest evidence in the pack that the gap is real: they built a database table
for payloads.**

| | Seven days, production |
|---|---:|
| Spans | 385,910 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-edoc` returns no results in Datadog Logs over seven days, under either `service:`
or `kube_deployment:`. The service identity section below covers why.

### The payload store

`config/logger/FeignConfinsLogger.java` is not a logger in the usual sense. On every CONFINS
call, when the Feign level is above `HEADERS`, it:

- builds a `ConfinsRequestLog` row with the path and method,
- puts the request body — or the query string for GETs — into `requestPayload`,
- puts the full response body into `responsePayload`,
- and saves the row through `ConfinsRequestLogRepository`.

The bodies go into Postgres, not into logs. That is why none of this shows up in the numbers
above, and why it has never appeared in a logging cost review.

**It still needs an owner.** That table holds CONFINS request and response payloads for a
document service. Nobody in this analysis could find a retention policy, an access control
statement, or a size for it. It sits outside the logging budget and outside every logging
control we have written.

`config/logger/LoggerConfiguration.java` also registers `bravo-lib-logging`'s
`RequestLoggingFilter` and `FeignClientFilter` unconditionally, the same as
`bravo-branch-service`. Those are dormant only because the level sits above DEBUG.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For the CONFINS
adapter that is a direct replacement for `ConfinsRequestLog` — on demand instead of always
on, and nothing persisted afterwards.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do

1. **Answer three questions about `ConfinsRequestLog` this sprint:** how big is it, how long
   is it kept, and who can read it. If the answer to any of them is "nobody knows", that is
   a finding in its own right.
2. If the table exists for audit rather than debugging, say so explicitly in the repo and
   scope it to the calls that need auditing. If it exists for debugging, it is a Live
   Debugger candidate and can be retired.
3. Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty`, defaulting to false.
4. Scope `loggerLevel: full` to `ApigeeApiClient` properly (item 1 above) — today it is what
   decides whether the payload table is written at all.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-edoc` | 384,176 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-edoc` either — both searches return zero over seven days.

It is not silent. It is producing 384,176 spans, so the workload is busy and the Agent
can reach Datadog. The logs are going to Cloud Logging and Coralogix and stopping there.

The practical effect: when this service fails at 02:00, there is a trace showing *that* it
failed and nothing showing *why*. The on-call engineer has a duration and a status code.

### What to do

1. **Confirm the Agent is collecting this pod's logs.** In the GitOps values file, check for
   the log collection annotation on the pod template, or that the Agent's
   `containerCollectAll` covers this namespace.
2. **Make sure the container writes to stdout**, not to a file inside the container. A
   Logback `FileAppender` or a pm2 `log_file` produces logs the Agent never sees.
3. **Do not enable collection until the non-production exclusion filters exist**
   ([sre-datadog-recommendations.md §2.1](sre-datadog-recommendations.md)). Turning this on
   first adds volume outside a filter and moves cost rather than saving it.
4. **Apply the unified tagging block below at the same time**, so the logs arrive already
   carrying the same service name as the traces.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-edoc`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-edoc"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-edoc
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-edoc` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-edoc env:prod

# APM Traces
service:prod-ms-edoc env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-edoc` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Add a `logging.level.root: INFO` block to `application-prod.yaml`
- [ ] Decide whether `ApigeeApiClient` still needs `loggerLevel: full`, or drop it to `basic`
- [ ] Review the 17 exception logs in `MessageServiceImpl.java`, then the rest of the 175
- [ ] Replace body logging with identifier logging
- [ ] Confirm the payload-logging filter stays dormant, or remove the bean
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Answer three questions about `ConfinsRequestLog`: how big, how long kept, who can read it
- [ ] Say in the repo whether that table exists for audit or for debugging
- [ ] Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty`, defaulting to false
