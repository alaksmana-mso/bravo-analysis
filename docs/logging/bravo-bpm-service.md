# bravo-bpm-service — logging fixes

**Squad:** Scoring and Underwriting (also checked out under Survey and Verification)
**Production service:** `prod-ms-bpm`
**Stack:** Java, Spring Boot, Camunda 7

This repo carries the largest logging configuration risk in the estate — and, measured on
14 September 2026, the largest log volume of any Bravo production service. The manifest has
been read: *item 1*'s standard Feign logger is **not** what runs. `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG=true`
replaces it with the hand-written logger below, so item 1 costs nothing on its own and
everything through item 2's logger.

That logger is writing full request and response bodies into production at INFO, about
86,600 times a day — 89% of the service's log bytes, about 22 GB a day. See
[Request and response bodies in Datadog](#request-and-response-bodies-in-datadog).

---

## 1. Feign full-body logging — settled by the manifest

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

### What the manifest says

`app-deployment/bpm/values-prod.yaml` (read 14 September 2026) sets `LOGGING_LEVEL_ROOT=INFO`
and nothing for `com.bfi.bravo.adapter` — so the DEBUG level does survive, exactly as the
code reading said. It also sets `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG=true`, which is
why that DEBUG level produces nothing: `FeignLoggingConfiguration` registers
`CustomFeignLogger` as the Feign logger bean, replacing the standard `Slf4jLogger`. The
standard logger is never called. `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL=basic` is set too,
and is inert — the code hard-codes `Logger.Level.FULL` and every client sets `full` by name.

### What production says

Across two days, all production services: `status:debug` 0, `END HTTP` 0. Both checks look
for the *standard* Feign logger, and the manifest explains why they find nothing. This repo
has two other body-logging paths that match neither check, and **both write at INFO**:

- `CustomFeignLogger` — outbound Feign request and response bodies. On in production.
- `CustomRequestLoggingFilter` — inbound request bodies. It extends
  `CommonsRequestLoggingFilter` but overrides `shouldLog()` to `logger.isInfoEnabled()`
  and `afterRequest()` to `logger.info()`, so unlike every other Commons filter in this
  pack the DEBUG gate does not hold it back. No `REQUEST DATA :` entries appear in
  production, so something is stopping it — but the configuration says it should be
  writing, and that gap is not explained by the logger level. That finding is in
[Request and response bodies in Datadog](#request-and-response-bodies-in-datadog), and it is
the bigger of the two.

### What it measures to

`prod-ms-bpm`, 24 hours to the afternoon of 14 September 2026:

| | Count |
|---|---:|
| Entries carrying `ResponseBody=` | 84,028 |
| Entries carrying `RequestBody=` only | 2,602 |
| Of those 86,630, cut at Datadog's 76,800-byte message limit | 86,623 |
| Indexed message bytes, body entries | 6.65 GB |
| Indexed message bytes, everything else | 0.82 GB |
| Ingested bytes, whole service, per day (Datadog's usage metric, 7-day mean) | ~25 GB |

Almost every body entry is longer than Datadog will index, so the payloads are bigger than
the indexed figure shows. About 22 GB a day of bodies is 660 GB a month: at contract rates
roughly $70 a month of Datadog ingestion and under $5 of indexed events, and roughly
**Rp 5–8M a month** in Cloud Logging at $0.50/GiB. That is the figure for this repo — not
the Rp 0–40M range this file carried before the manifest was read, and not the Rp 50–90M in
the original deck. The value of fixing it is data protection first and cost second: these
are unmasked PEFINDO, SLIK, Dukcapil and CONFINS payloads at INFO.

The sharia deployment (`values-prod-sharia.yaml`, Datadog service `prod-sharia-bpm-sharia`)
runs the same logger at version 2 with **header logging on, including `Authorization`**
(`ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER_AUTH=true`). It wrote ten lines in the
last 24 hours, so the volume is nothing — but a bearer token in a log index is a finding
regardless of count. [deployment-proposal.md](deployment-proposal.md) §5 has the two-line
change.

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
| 1 — Feign body logging, via `CustomFeignLogger` | **Rp 5–8M** | high — measured: ~22 GB a day, 89% of the service's log bytes |
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

One thing is set correctly in the main deployment: header logging is off. Exactly one entry
in seven days carries `Headers=`, and the manifest confirms
`ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER=false`. Keep it that way — and fix the
sharia deployment, which sets both the header flag and `…SHOW_HEADER_AUTH` to `true`, so
there the `Authorization` header is written (§1).

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
2. **Adopt `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September 2026) as soon as Platform publishes it** — the *Deploy Package* workflow is manual and has not run for the new modules yet. This repo is on
   Boot 3.5.16 and uses no shared logging library, so it can take the starter directly: the
   JSON output it already has through its own `logback.xml` keeps working, every message is capped at 8 KB (the
   Feign lines are 76 KB+ today), and the starter's own Feign logger — one line per call, no
   headers, bodies only when you ask — replaces `CustomFeignLogger` once the bean is deleted.
   Until then the masking and size cap in #10463 stand.
3. Ask SRE for the Remote Configuration fix first. It is item 5a in
   [sre-datadog-recommendations.md](sre-datadog-recommendations.md).
4. Meanwhile, cut the volume without losing the capability — **this is what
   [#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463) does**: a size
   limit and a masking step in `CustomFeignLogger`, full logging off by default. Scope it
   to the clients you actually debug instead of `default`, and take the masked-field list
   from `bravo-onboarding-service`'s `FeignSlf4jLogger` — the most complete one in the
   estate.
5. Put the identifiers on the span, so a failed call is findable without the body at all:

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

## Why did validation fail? Answering the customer without logging the payload

The Scoring and Underwriting reviewer asked on [#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463/changes/BASE..f234da81be5dcd45e2d106eeae04a6e9c5c0ad89#diff-267c70ab9bcb25d7dbfde1922e70479c1a3faa40175d392dc662585f137d3f24),
against `RequestLoggingFilterConfig`, whether there is still a way to know what the user sent.
The reason behind the question: when a request fails validation and the customer asks why,
today the engineer only finds out by reading the payload in the log. That is a real need, and
it deserves a real answer. The payload log is the wrong tool for it. This section says what to
use instead. It is written from the code on `fix/logging` and from seven days of production
logs, 16 to 23 September 2026.

### What happens today when a request is rejected

| How the request fails | What the caller gets back | What the log says | Lines, 7 days |
|---|---|---|---:|
| Bean validation (`@Valid` sits on 609 of the 690 request bodies) | 400, `errors: ["field : message"]` | one ERROR line from `ErrorHandlerController`. Spring fills it with the field, the constraint and the rejected value | 1,745 |
| A path or query parameter of the wrong type | 400 | one ERROR line naming the parameter and the value. The `undefined` bug in §5 is most of these | 3,393 |
| Body that does not parse | 400 | one ERROR line | 117 |
| A business rule thrown as `BravoCommonException` (258 places in the code) | 400 with a code, a sub-code and `details[].fields` | **nothing.** `handleBravoCommonException` has no log statement | 0, by design |
| A business rule thrown as `BusinessErrorException` (334 places: "Application list not found", "Workflow still on progress", the alternative-offer limit, and so on) | **500 Internal Server Error** with the rule text as the message | ERROR with a full stack trace, as if the service had crashed | inside the 7,047 `Exception = ` lines from the same handler class |

Every one of those lines already carries two identifiers. `correlationId` comes from
`CorrelationIdFilter`: the `x-request-id` header if the caller sent one, otherwise a fresh
UUID. `trace_id` comes from the Datadog tracer. Both are attributes on the line, because
production logs go through the `LogstashEncoder` in `logback.xml`. So the log side is better
than it looks. Two things are missing, and they are why the payload gets read:

1. **The correlation id never goes back to the caller.** `CorrelationIdFilter` puts it in the
   MDC and the request context, and sets no response header. The console cannot show it, so
   customer service cannot quote it, so the engineer has nothing to search for except a
   customer name and a time window. The payload is the only thing in the log that contains
   something the customer can be matched on. That is the whole reason it feels necessary.
   The starter in `bfi-java-pkg` has the same gap in its own `CorrelationIdFilter`; it reads
   the header and never writes it back.
2. **Business-rule rejections are either silent or logged as faults.** The
   `BravoCommonException` path leaves no line at all. The `BusinessErrorException` path
   returns a 500 and a stack trace for what is a decision, not a failure.

### The best practice for this service

The rule is short: **log the decision, return the reference, keep the data in the database.**
The payload is the input. The customer's question is about the outcome. Record the outcome
where it happens, once, and make it findable.

**1. Log one decision line per rejected request, from the handler, not from 592 throw sites.**
`ErrorHandlerController` sees every rejection, so it is the one place to write the line. One
WARN, no stack trace, structured:

```json
{
  "level": "WARN",
  "event": "request_rejected",
  "http": { "route": "/v2/surveyor-assignment/{id}/asset", "status_code": 400 },
  "application_id": "APP-…",
  "error_code": "INVALID_ARGUMENT",
  "fields": [ { "field": "vehicleOwnershipNumber", "rule": "Pattern", "rejected": "…" } ],
  "correlationId": "…", "dd.trace_id": "…"
}
```

- Field name and rule always. The rejected value only when the field is not in the masked
  list from `FeignBodySanitizer`; a NIK or a phone number that failed a pattern check is still
  a NIK or a phone number.
- Add the missing statement to `handleBravoCommonException`, with the code, the sub-code and
  the `fields` it already builds for the response.
- Put `application_id` on the line whenever the route has one. A small interceptor that
  copies the `{applicationId}` path variable into the MDC does it for every controller at
  once.

With that line in place, "why was application X rejected on Tuesday" is one search:
`service:prod-ms-bpm @event:request_rejected @application_id:X`.

**2. Return the reference.** One line in `CorrelationIdFilter`:
`response.setHeader("x-request-id", requestCorrelationId)`. Then put the same value in
`BaseErrorResponse` and in the error branch of `BravoCommonResponse`, so the console can show
"Reference: …" in its error message. The path from the customer to the answer becomes:
customer service asks for the reference, the engineer searches `@correlationId:<reference>`,
reads the decision line, and opens the linked trace if the rejection came from an upstream
call. Two minutes, no payload, and the same reference works across every service the request
touched if the console forwards the header.

**3. Stop treating rule outcomes as faults.** `BusinessErrorException` is a rejected input or
a state the rule does not allow, so return a 4xx (422 fits, 400 is acceptable) and log at WARN
without the trace. The six 400 handlers that call `log.error` today (bean validation, type mismatch, bind, unreadable body, missing parameter, invalid format) should be WARN too. A
rejected request is the service working. This also removes a share of the stack traces in §2
and §4.

**4. When the input itself is needed, it is in the database, not in the log.** Camunda's
history level is FULL in production (`act_ge_property.historyLevel = 3`, the Spring Boot
starter default; nothing in the configuration lowers it), and history is kept for 90 days
(`historyTimeToLive: P90D`). Every process variable value, and every change to it, is in
`act_hi_varinst` and `act_hi_detail`, by process instance id or business key. The application
entities are in the service's own tables. That is where "what did the user input" lives, and
it is behind database access control. A log line is readable by everyone with Datadog access
and is copied into Cloud Logging. That difference is the reason the payload does not belong
in the log.

**5. For the rest, a payload window that is scoped and masked, never the default.**
#10463 makes the inbound payload a per-environment switch (`REQUEST_LOGGING_INCLUDE_PAYLOAD`,
off). Two refinements make the switch safe to use when a squad does need it:

- capture the body only when the response status is 4xx. `CustomRequestLoggingFilter` can
  read the response inside `afterRequest` through `ServletRequestAttributes.getResponse()`,
  so "every request, raw" becomes "rejected requests only";
- run the captured body through `FeignBodySanitizer` and the same cap before it is written.

The same two refinements are worth asking for in the starter's `RequestLoggingFilter`
(`request-logging.include-payload` is all-or-nothing there too). They are not in #10463; they
are the next step if the squad wants the window at all.

**6. Live Debugger stays the durable answer for a one-off look at a live request** once SRE
fixes Remote Configuration; see *What to do* above.

### What not to do

- Do not log the raw body of every request at INFO. That was the `master` default
  (`setIncludePayload(true)`), and the outbound equivalent is the 86,600 body lines a day
  measured in §1. Scoring requests carry NIK, phone numbers and income.
- Do not log the rejected value of a masked field. The field name and the rule are enough
  to answer the customer.
- Do not add a log line at each `throw`. The handler already sees them all; one line there
  is complete and consistent.
- Do not answer "we cannot see the payload" with `loggerLevel: full` or a DEBUG level on
  `com.bfi.bravo.adapter`. That is the one-variable route to a credit-bureau dump.

### Runbook: a customer asks why their application was rejected

1. Get the reference from the console error (once step 2 ships) or the application id and
   the time from customer service.
2. Datadog, us5: `service:prod-ms-bpm @correlationId:<reference>`, or
   `service:prod-ms-bpm @event:request_rejected @application_id:<id>`.
3. Read the decision line: route, code, field, rule. For a bean-validation rejection today,
   the existing `Method arguments not valid exception` line already names the field, the
   constraint and the value.
4. If the rejection came from an upstream call, open the trace by `trace_id`: the Feign span
   shows which service said no and with which status.
5. If the value itself matters and the field is masked, read it from `act_hi_varinst` or the
   application table by process instance id. Do not switch on payload logging for this.

### Where this sits against #10463

Nothing in #10463 has to change. Steps 1 to 3 are two small commits: a log statement and a
status change in `ErrorHandlerController`, and one `setHeader` line plus a field on the two
error responses. They can ride on #10463 if the squad wants them there, or go in a follow-up
owned by the squad; either way they are the answer to the reviewer's question, and the
payload switch is the fallback, not the plan.

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

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
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

## In the production deployment

Read from `app-deployment/bpm/values-prod-sharia.yaml`, `app-deployment/bpm/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG` | `true` *(values-prod-sharia.yaml)* |
| `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER` | `true` *(values-prod-sharia.yaml)* |
| `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER_AUTH` | `true` *(values-prod-sharia.yaml)* |
| `FEIGN_CUSTOM_LOG_VERSION` | `2` *(values-prod-sharia.yaml)* |
| `FEIGN_CUSTOM_LOG_VERSION` | `3` *(values-prod.yaml)* |
| `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL` | `basic` *(values-prod.yaml)* |
| `LOGGING_LEVEL_ROOT` | `INFO` *(values-prod.yaml)* |
| `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG` | `true` *(values-prod.yaml)* |
| `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG_SHOW_HEADER` | `false` *(values-prod.yaml)* |

This is a Java service that does **not** depend on `bravo-lib-logging`. The variables above are the ones that matter: `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG=true` swaps Feign's standard logger for `CustomFeignLogger`, which writes every request and response body at **INFO**, unmasked and uncapped; `FEIGN_CUSTOM_LOG_VERSION=3` is the variant that puts request body, response body, status and elapsed time in one entry; header logging is off in the main deployment and **on** in the sharia one (`values-prod-sharia.yaml`, version 2, with `…SHOW_HEADER_AUTH=true` — so the `Authorization` header is written as well). `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL=basic` is inert: the code hard-codes a `Logger.Level.FULL` bean and every named client sets `loggerLevel: full` explicitly. `LOGGING_LEVEL_ROOT=INFO` duplicates `application-prod.yaml`; nothing overrides `com.bfi.bravo.adapter`, which stays at DEBUG — but the custom logger does not use that package's logger, so the DEBUG level produces nothing. See §1 for what this measures to in Datadog. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** Spring Boot 3.5.16, no shared logging library: this is the first service that should adopt `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September, publish pending) — see §1 and *What to do* above. Every setting the squad asked for on #10463 (a sanitize flag, the body cap, payload logging for the inbound filter, all in `application.yaml` with an environment variable behind each) has a direct equivalent in the starter's `bravo.logging.*` properties, so nothing configured now is lost in the move.
---

## Implementation status

**Pull request: [bravo-bpm-service#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-bpm-service/tree/fix/logging), head `c47f1cb504`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-bpm-service/pull/10463/files) · [Commits](https://github.com/bfi-finance/bravo-bpm-service/pull/10463/commits) · [Compare against master](https://github.com/bfi-finance/bravo-bpm-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.16. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON (which this repo already emits through its own `logback.xml`), an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

The squad's review of 16 September (four comments) is answered in the thread and in a fourth commit — see the pull request.

CI re-runs on the new head; on the previous one only SonarQube and the container scan were red, both gates that were red before this branch.

| | |
|---|---|
| Commits | 4 |
| Files changed | 7 |

Commits:

- fix(logging): stop the inbound request filter capturing payloads
- fix(logging): mask and truncate Feign bodies, drop full Feign logging by default
- style: satisfy spotless (prettier-java) in CustomFeignLogger
- fix(logging): make the Feign sanitizer JSON-aware and put every switch in application.yaml (17 September, after the squad's review)

Files:

- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`
- `src/main/java/com/bfi/bravo/config/feign/CustomFeignLogger.java`
- `src/main/java/com/bfi/bravo/config/feign/FeignBodySanitizer.java`
- `src/main/java/com/bfi/bravo/config/feign/FeignCustomLogConfig.java`
- `src/main/resources/application-prod.yaml`
- `src/main/resources/application.yaml`
- `src/test/java/com/bfi/bravo/config/feign/FeignBodySanitizerTest.java`

**The squad reviewed it on 16 September 2026** (four comments from the Scoring and Underwriting reviewer), and every one was about control rather than direction:

| Asked | Answer, and what changed in `c47f1cb504` |
|---|---|
| Can the body cap be set from `application.yaml`? | It could already (`setting.feign-custom-log-config.max-body-length`, env `FEIGN_CUSTOM_LOG_MAX_BODY_LENGTH`); the reviewer was reading the Java, not the YAML hunk. A `sanitize` switch (`FEIGN_CUSTOM_LOG_SANITIZE`, default on) now sits beside it, and `masked-fields` stays overridable there |
| Is there a way to still see what the user sent? | Yes, three: the inbound payload switch is now a property (`setting.request-logging.include-payload`, env `REQUEST_LOGGING_INCLUDE_PAYLOAD`, default off — it logs the raw body, hence off in prod); the process variables in the BPM database; and, durably, Live Debugger once Remote Configuration works, or the starter's masked `RequestLoggingFilter` when this service adopts it. **On 23 September the reviewer explained the need behind the question** (a customer asks why validation failed, and only the payload log says); the answer is in [Why did validation fail?](#why-did-validation-fail-answering-the-customer-without-logging-the-payload): log the decision, return the reference, read the input from the database |
| Add a flag to enable the sanitizer | Added, as above. Masking is also JSON-aware now: a body that parses is walked as a tree and any listed key is masked whatever its value — nested object, array, number — which also closes Codacy's "nested values leak" comment; non-JSON bodies get one alternation pass instead of one per key |
| If `loggerLevel` is `basic`, is the payload gone — so what are the sanitizer and the 2048 cap for? | Two loggers. `loggerLevel` drives Feign's built-in logger, which only writes at DEBUG and so writes nothing in production at `full` *or* `basic`; the change removes the one-env-var route to a payload dump. The bodies in production come from `CustomFeignLogger`, switched on by the manifest and writing at INFO regardless — 86,630 body entries a day. That is where the sanitizer and the cap apply, and bodies keep being logged there, masked and bounded |

Seven unit tests cover the sanitizer (`FeignBodySanitizerTest`): scalar types, nested objects and arrays, case-insensitive keys, the text fallback, truncation, the off switch. Compiled and run on 17 September; Spotless clean on every changed file. The full 18,306-test suite was not re-run for this commit — CI does that.

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 18306 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
- [ ] Log one structured WARN decision line per rejected request in `ErrorHandlerController`; add the missing statement to `handleBravoCommonException`
- [ ] Return `x-request-id` in the response and put it on the two error response types, so the console can show a reference
- [ ] Return a 4xx and log at WARN without a trace for `BusinessErrorException`; downgrade the six 400 handlers from `log.error` to `log.warn`
- [ ] If the payload window is ever used, capture only on 4xx and run the body through `FeignBodySanitizer` first
