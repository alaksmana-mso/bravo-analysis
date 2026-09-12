# bravo-core-proxy-service — logging fixes

**Squad:** Contract Collateral \& Loan Calculation
**Production service:** `prod-ms-bravo-core-proxy`
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

**The level** — `src/main/resources/application.yaml` sets CommonsRequestLoggingFilter using a placeholder
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

## 2. 26 exception logs passing the throwable

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
span. Squads work around that by logging bodies. **For this service the question does not
arise yet, because nothing it writes reaches Datadog at all.**

| | Seven days, production |
|---|---:|
| Spans | 758,447 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-bravo-core-proxy` returns no results in Datadog Logs over seven days, under either
`service:` or `kube_deployment:`. The service identity section below covers why and what to
do about it.

For a proxy this is the worst place to be. Three quarters of a million spans a week say what
was called and how long it took, and nothing says what was proxied.

### What exists in the code

`client/FeignSlf4jLogger.java` captures request and response bodies at Feign level FULL,
gated on `logger.isDebugEnabled()`, with `MASKED_FIELD` covering the auth headers only.
Production sits above DEBUG, so it is a no-op today.

Sequencing matters here: if log collection is fixed while the payload filter default is
still `DEBUG` (item 1 above), the first thing to arrive in Datadog will be proxied bodies.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. For a proxy
that is a good fit — one probe on the forward method answers most questions.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Fix the payload filter default (item 1) **before** log collection is fixed.
2. Fix log collection, after the exclusion filters exist.
3. Add `DD_TRACE_HEADER_TAGS` so correlation ids land on spans. For a proxy this is worth
   more than for most services: it lets a caller's request id follow the hop.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bravo-core-proxy` | 745,851 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-bravo-core-proxy` either — both searches return zero over seven days.

It is not silent. It is producing 745,851 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bravo-core-proxy`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bravo-core-proxy"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bravo-core-proxy
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bravo-core-proxy` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bravo-core-proxy env:prod

# APM Traces
service:prod-ms-bravo-core-proxy env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bravo-core-proxy` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Run the `kubectl set env --list` check above and record the answer
- [ ] Change the YAML default from `:DEBUG` to `:WARN`
- [ ] Set `setIncludePayload(false)` in `WebConfig.java`, or move the bean behind `@Profile("local")`
- [ ] Pin the filter level explicitly in `application-prod.yaml`
- [ ] Review the 26 exception-logging sites
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Fix the payload filter default **before** log collection is fixed, not after
- [ ] Ask SRE for `DD_TRACE_HEADER_TAGS` — for a proxy this carries the caller's request id across the hop
