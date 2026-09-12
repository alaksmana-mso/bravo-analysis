# bravo-branch-service — logging fixes

**Squad:** Internal Service
**Production service:** `prod-ms-branch`
**Stack:** Java, Spring Boot

Moderate findings. The logs-inside-loops item is the one worth attention, because branch
and survey group data is processed in batches.

---

## 1. Six logs inside loops

| File | Count |
|---|---:|
| `src/main/java/com/bfi/bravo/service/impl/BravoBranchTransactionalServiceImpl.java` | 1 |
| `src/main/java/com/bfi/bravo/service/impl/SurveyGroupTransactionalServiceImpl.java` | 1 |

Branch and survey group syncs run over the full branch list. One log line per branch means
the output scales with the estate, and it grows every time BFI opens a branch.

### Fix

Log once before the loop with the count, once after with the outcome, and inside only on
failure:

```java
log.info("branch upsert starting: count={}", branches.size());
// loop, log failures only
log.info("branch upsert done: ok={} failed={}", ok, failed);
```

---

## 2. 66 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/service/impl/BranchUpsertServiceImpl.java` with 4.

Combined with item 1, a failing branch sync produces a stack trace per branch. With
multi-line aggregation off cluster-wide, each trace is one entry per frame.

That combination is how a routine upstream outage turns into a large log bill for an hour.

### Fix

Structured warn lines for expected failures. Traces only where diagnosis needs one.

---

## 3. `CommonsRequestLoggingFilter` — dormant

`src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java` registers it with
payload logging on. The logger sits at INFO in production, so it emits nothing.

Set `setIncludePayload(false)` or move the bean behind `@Profile("local")`, and pin the
level in `application-prod.yaml`.

---

## 4. Smaller items

| Item | Count | Note |
|---|---:|---|
| DEBUG/TRACE in YAML | 8 | `application-unit-test.yaml` and local profiles — no production impact |
| `System.out.print` | 2 | `src/test/` only |

---

## 5. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — logs in loops | Rp 1–3M | medium, spikes during syncs |
| 2 — exception logs | Rp 1–2M | medium |
| 3 — dormant payload filter | Rp 0 today | risk removal |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This repo has two body-capture
mechanisms registered at once, and no logs reaching Datadog to show it.**

| | Seven days, production |
|---|---:|
| Spans | 3,078,091 |
| Log entries | **0** |
| Entries carrying a captured body | 0 |

`prod-ms-branch` returns no results in Datadog Logs over seven days, under either `service:`
or `kube_deployment:`. The service identity section below covers why.

### Two mechanisms, both unconditional

- `config/RequestLoggingFilterConfig.java` — `CommonsRequestLoggingFilter` with
  `setIncludePayload(true)` and `setMaxPayloadLength(LoggingConstants.MAX_PAYLOAD_LENGTH)`,
  prefix `REQUEST DATA : `.
- `config/LoggerConfiguration.java` — registers `bravo-lib-logging`'s `RequestLoggingFilter`
  **and** `FeignClientFilter` as `@Primary`, with no `@ConditionalOnProperty`.

Compare `bravo-onboarding-service` and `bravo-inventory-management-service`, which put the
same shared-library beans behind `setting.features.enableBfiLogger`. This repo does not.
Both mechanisms are dormant only because the logger level sits above DEBUG — not by design.

**This is the sequencing risk on this service.** Fixing log collection turns on two payload
loggers at the same moment, on a service already doing 3 million spans a week, with logs
inside branch-sync loops (item 1 above) on top.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe.

Remote Configuration has to work first, and it is failing across the Java estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store` on thirteen production services.

### What to do, in this order

1. Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty` the way
   `bravo-onboarding-service` does, and default it to false.
2. Pin the `CommonsRequestLoggingFilter` level explicitly in `application-prod.yaml`.
3. Fix the loop logging (item 1).
4. Only then fix log collection, after the exclusion filters exist.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-branch` | 3,054,484 spans |
| Logs | — | **0 entries** |

**This service sends no logs to Datadog at all.** Not under this name, and not under
`kube_deployment:prod-ms-branch` either — both searches return zero over seven days.

It is not silent. It is producing 3,054,484 spans, so the workload is busy and the Agent
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
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-branch`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-branch"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-branch
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-branch` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-branch env:prod

# APM Traces
service:prod-ms-branch env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-branch` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Move loop logging out of the loop in `BravoBranchTransactionalServiceImpl`
- [ ] Same in `SurveyGroupTransactionalServiceImpl`
- [ ] Review the exception logs in `BranchUpsertServiceImpl.java`
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Confirm with Platform why this service sends no logs to Datadog
- [ ] Check the container writes logs to stdout, not to a file
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Enable log collection **after** the non-production exclusion filters exist
- [ ] Put the `bravo-lib-logging` beans behind `@ConditionalOnProperty`, defaulting to false
- [ ] Pin the `CommonsRequestLoggingFilter` level in `application-prod.yaml` before log collection is fixed
