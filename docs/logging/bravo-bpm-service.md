# bravo-bpm-service — logging fixes

**Squad:** Scoring and Underwriting (also checked out under Survey and Verification)
**Production service:** `prod-ms-bpm`
**Stack:** Java, Spring Boot, Camunda 7

This repo carries the largest logging configuration risk in the estate. Whether *item 1* is
currently costing money is **unconfirmed** — that still needs a manifest check.

What is confirmed is separate and larger: a second, hand-written Feign logger is writing
full request and response bodies into production at INFO, 487,146 times a week. See
[Request and response bodies in Datadog](#request-and-response-bodies-in-datadog).

---

## 1. Feign full-body logging — check the manifest before doing anything else

### What the code says

`src/main/resources/application.yaml`:

- **129** entries set `loggerLevel: full`, including `feign.client.config.default`
- the same file sets:

```yaml
logging:
  level:
    com:
      bfi:
        bravo:
          adapter: DEBUG
```

- all **57** Feign client interfaces live under `com.bfi.bravo.adapter.http.*`

`src/main/resources/application-prod.yaml`:

```yaml
logging:
  level:
    root: INFO
    org:
      hibernate: WARN
```

It sets `root`. It does **not** set `com.bfi.bravo.adapter`. Those are different keys in
Spring Boot, so the DEBUG level survives into production.

Feign writes bodies when the client's logger is at DEBUG. On this reading, every upstream
call — PEFINDO, SLIK, Dukcapil, CONFINS, Ali Cloud — logs its complete request and response
body.

### What production says

Nothing matching. Across two days, all production services:

| Check | Result |
|---|---|
| `status:debug` | 0 |
| `END HTTP` (Feign's full-logging terminator) | 0 |

**That does not mean bodies are absent.** Both checks look for the *standard* Feign logger,
which is gated on DEBUG and terminates each response with `END HTTP`. This repo also has
`CustomFeignLogger`, which writes bodies through `log.info` and matches neither check.
It is on in production. That finding is in
[Request and response bodies in Datadog](#request-and-response-bodies-in-datadog), and it is
the bigger of the two.

### So do this first

Somebody needs to read the deployment manifest, which is not in this repo:

```bash
kubectl -n prod set env deploy/prod-ms-bpm --list | grep -i 'logging\|FEIGN'
```

Grep for `FEIGN` as well as `LOGGING`. The same command answers the second question:
whether `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG` is `true` and what
`FEIGN_CUSTOM_LOG_VERSION` is set to. Production behaviour says `true` and `3`; confirm it
from the manifest in the same hour.

If it shows `LOGGING_LEVEL_COM_BFI_BRAVO_ADAPTER=INFO` or similar, the body logging is
already off and there is **no cost saving here at all**. If it shows nothing, the logs are
being written and Datadog is dropping them before indexing — in which case Cloud Logging is
paying for all of it.

**One hour of work decides whether this repo is worth Rp 0 or Rp 40M a month.** Do not
quote a saving until it is done.

### Fix the configuration either way

Regardless of the answer, this is wrong:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: full
```

A default of `full` means one environment variable — or one merge into
`application-prod.yaml` — starts writing customer credit-bureau payloads into Cloud
Logging. That should not be one line away.

Change the default to `basic`, which logs method, URL, status and timing:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
```

Then set `full` on individual clients only where somebody can say why, and only for
non-production profiles.

Also pin the level explicitly in `application-prod.yaml` so it cannot drift:

```yaml
logging:
  level:
    root: INFO
    com.bfi.bravo.adapter: INFO
```

---

## 2. Stack traces, one log entry per frame

The three highest-volume log patterns in this service are all single stack frames:

| Pattern | Count, 2 days |
|---|---:|
| `at <pkg>.<class>.<method>(File.java:NN)` | 1,441 |
| `at org.springframework.…` | 844 |
| `at <pkg>.…` (deeper nesting) | 378 |

Multi-line aggregation is not configured anywhere in the cluster. A 50-frame Java trace
becomes 50 log entries. The text is about 3 KB; the 50 metadata envelopes add roughly 35 KB
on top of it.

Two of these are not faults at all:

- **`TokenExpiredException`** — 172 in two days, each with a ~50-frame trace, logged at
  SEVERE by Tomcat's `StandardWrapperValve`. An expired token is a normal condition. It
  should be a 401 and one line.
- **`FeignException$Unauthorized` on `IAMApiClient#getAssignedPermission`** — 106 in two
  days, same shape.

### Fix

1. Catch `TokenExpiredException` in `InternalAuthenticationFilter` (`doFilterInternal`,
   line 52) and return 401 without letting it reach Tomcat. One warn line with the token
   subject, no trace.
2. Same for the `IAMApiClient` 401 path.
3. Ask Platform to enable multi-line log aggregation cluster-wide. That is one Fluent Bit
   setting and it helps every Java service at once — it belongs in the platform work, not
   this backlog.

---

## 3. ENGINE-09004 BPMN parse warnings

432 occurrences in two days across four variants. Each message is long — one exceeds 1,500
characters listing every gateway and link event in the diagram.

Affected models:

- `ndf2w.bpmn` — exclusive gateways with an unconditional outgoing flow that is not marked
  as the default
- `ndf4w.bpmn` — link events whose catch and throw names do not match
- `unified-main-workflow.bpmn` — five mismatched link event names

These are model quality warnings. They re-emit every time the engine parses the definition.
None is a runtime error.

### Fix

In the BPMN files:

- set the default flow explicitly on each exclusive gateway the warning names
- make each link event's name match its link definition name

This is diagram editing, not code. It also removes a recurring warning that makes real
`ENGINE-*` problems harder to spot. `ENGINE-14006 Exception while executing job` — 41 in
two days — is a real one currently buried in the noise.

---

## 4. 694 exception logs passing the throwable

694 occurrences of `log.error(msg, exception)` across the repo. Highest concentration:

- `src/main/java/com/bfi/bravo/activity/multiasset/CalculateIncomePerMonthV2Activity.java` — 15

Each one can emit a full trace. Most do not need to: if the error is handled and the flow
continues, the trace adds nothing a message and a correlation id would not.

### Fix

Use the trace where the error is genuinely unexpected. Where it is an expected upstream
failure, log one structured line:

```java
log.warn("PD model check failed, falling back: loanId={} status={} reason={}",
         loanId, status, ex.getMessage());
```

Two error messages worth attention on their own, both currently logged with full traces:

- `Error while invoking Ali Cloud for PD Model Check Response` — 35 in two days, plus 31
  `ENGINE-16004 Exception while closing command context` for the same cause
- `Error when processing scheduling appointment event : 404 NOT_FOUND "Lead does NOT exist!"`
  — 169 in two days. A missing lead is a data condition, not an exception.

---

## 5. Smaller items

| Item | Count | Note |
|---|---:|---|
| Logging a serialised body | 46 | `RecalculateLoanStructureLTVOnly2WServiceImpl.java` has 6 |
| `printStackTrace()` | 26 | All in `src/test/` — harmless, but replace with assertions |
| `console.log` | 28 | Camunda Cockpit webjars, vendor code — leave alone |
| `CommonsRequestLoggingFilter` | registered | `setIncludePayload(true)`, 10 KB limit, but its logger sits at INFO in prod, so it is dormant. Remove the bean or leave it — it is not currently emitting |

Two recurring errors point at a caller bug rather than a logging problem:

- `Method parameter 'id': … Invalid UUID string: undefined` — 91 in two days
- `Method parameter '…': … For input string: "undefined"` — 82 in two days

A front-end is sending the literal string `undefined`. Fixing the caller removes 173 error
logs every two days and a real defect. Worth a ticket to whichever console owns it.

---

## 6. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — Feign body logging | **Rp 0 to 40M** | unknown until the manifest is read |
| 2 — stack trace handling | Rp 8–15M | medium; most of it is the cluster-wide setting |
| 3 — ENGINE-09004 | Rp 2–5M | high |
| 4 — exception logs | Rp 3–6M | medium |
| 5 — `undefined` parameter bug | under Rp 1M | high |

---

## Request and response bodies in Datadog

Squads across BFI say they cannot see request and response bodies in Datadog. They are
right: no Datadog tracer, in any language, has a supported setting that puts an HTTP body on
a span. **This service is the one that did something about it, and it is the most expensive
way to have done it.**

| | Seven days, production |
|---|---:|
| Spans | 3,191,886 |
| Log entries | 1,109,474 |
| Entries carrying a captured request body | 487,146 |
| Entries carrying a captured response body | 471,241 |

Forty-four per cent of this service's log volume is captured HTTP bodies.

### What is producing them

`src/main/java/com/bfi/bravo/config/feign/CustomFeignLogger.java` is a hand-written Feign
logger. It reads the request body, reads the response body, rebuffers the response so the
call still works, and writes both to `log.info`.

`FeignLoggingConfiguration` only creates the bean when
`setting.feign-custom-log-config.active` is true, and `application.yaml` defaults that to
`false` through `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG`. **Production has it switched on.**

The format says which variant. This service emits 547,490 INFO entries in seven days, and
about 487,000 of them carry `RequestBody=`, `Status=`, `ElapsedTime=` and `BodyLength=` in
the *same* entry. Only `logAndRebufferResponseV3` builds one entry that way, so
`FEIGN_CUSTOM_LOG_VERSION=3` as well.

One thing is set correctly: header logging is off. Exactly one entry in seven days carries
`Headers=`, so `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER` is false and no
`Authorization` value is being written. Keep it that way.

### What is wrong with it

- **No masking.** Every other hand-written Feign logger in the estate runs bodies through a
  masker first. `bravo-approval-engine-service` masks the auth headers.
  `bravo-onboarding-service` masks NIK, email, password, spouse name and access tokens.
  `CustomFeignLogger` masks nothing at all. Whatever is in the body goes to Datadog and to
  Cloud Logging in full.
- **No size limit.** There is no truncation anywhere in the class. Scoring payloads are
  large, and log lines over 16 KB are split by the container runtime — which is part of why
  this service's logs are hard to read at all.
- **Always on.** It fires on every Feign call, successful or not. Almost none of those
  487,000 entries is ever read by anyone.

### What you get back if you turn it off

This service is Java, and that matters. The Java tracer supports **method probes** in
Datadog's Live Debugger: name a method, get its arguments and its return value, captured
from the running pod, with no redeploy and nothing left behind. That is a much closer match
to what `CustomFeignLogger` does than anything the Node.js services can have.

The catch is that Live Debugger needs Remote Configuration, and **Remote Configuration is
failing on this service today**:

```
[dd-remote-config] WARN datadog.remoteconfig.ConfigurationPoller - Failed to retrieve
remote configuration: unexpected response code Internal Server Error 500 ... empty targets
meta in director local store
```

191 of those in two days. Thirteen production services report the same error. Nothing can be
switched on from the Datadog UI until SRE fixes it.

### What to do

1. **Do not switch `CustomFeignLogger` off yet.** It is the only place response bodies exist
   in this estate today. Removing it before the replacement works takes away real debugging
   ability, and that will be resisted — correctly.
2. Ask SRE for the Remote Configuration fix first. It is item 5a in
   [sre-datadog-recommendations.md](sre-datadog-recommendations.md).
3. Meanwhile, cut the volume without losing the capability. Add a size limit and a masking
   step to `CustomFeignLogger`, and scope it to the clients you actually debug instead of
   `default`. Copy the masked-field list from `bravo-onboarding-service`'s
   `FeignSlf4jLogger` — it is the most complete one in the estate.
4. Put the identifiers on the span, so a failed call is findable without the body at all:

   ```java
   final Span span = GlobalTracer.get().activeSpan();
   if (span != null) {
     span.setTag("bpm.application_id", applicationId);
     span.setTag("bpm.process_instance_id", processInstanceId);
     span.setTag("http.downstream_status", response.status());
   }
   ```

5. Once Live Debugger works, set a method probe on the client method, capture one example,
   remove the probe, and delete `CustomFeignLogger`.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bpm` | 3,177,971 spans |
| Logs | `prod-ms-bpm` | 1,113,282 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bpm`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bpm"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bpm
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bpm` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bpm env:prod

# APM Traces
service:prod-ms-bpm env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bpm` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] **Read the prod deployment manifest for `LOGGING_LEVEL_*` overrides** — do this first
- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Pin `com.bfi.bravo.adapter: INFO` in `application-prod.yaml`
- [ ] Handle `TokenExpiredException` in `InternalAuthenticationFilter` without a trace
- [ ] Handle the `IAMApiClient` 401 path the same way
- [ ] Ask Platform for cluster-wide multi-line aggregation
- [ ] Set default flows on the gateways named in `ndf2w.bpmn`
- [ ] Match link event names in `ndf4w.bpmn` and `unified-main-workflow.bpmn`
- [ ] Review the 694 `log.error(msg, ex)` sites, starting with the Ali Cloud path
- [ ] Raise a ticket for the front-end sending `undefined` as a path parameter
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Do **not** remove `CustomFeignLogger` until Live Debugger works — it is the only response-body capture in the estate
- [ ] Add a size limit and a masking step to `CustomFeignLogger`; copy the field list from `bravo-onboarding-service`
- [ ] Scope the custom Feign logger to the clients you debug, not `default`
- [ ] Chase SRE on the Remote Configuration failure — 191 failed polls in two days blocks Live Debugger
