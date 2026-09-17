# Logging and observability — the guide for squads

Written 12 September 2026. For every squad shipping a service at BFI.

BFI is standardising on Datadog for logs, traces and metrics. Cloud Logging stops being the
place you go to debug. This guide says what to log, what not to log, and which Datadog
feature answers which question.

It is based on measurements from all 152 repos and production telemetry, not on general
advice. Where a rule exists, it is because something in our estate is broken by breaking it.

**Revised 13 September 2026**, after every one of the 73 repositories in this programme was
read line by line and 64 pull requests were raised (16 since closed on SRE's guidance — masking is a deployment setting — and two wrapper pull requests added in their place; the Java one merged on 16 September 2026, the first service one on 15 September). Rules 2, 3 and 5 gained a section each
as a direct result — the Go estate breaks these rules differently from the Java estate, and
the first version of this guide only described the Java half.

---

## Why squads go first

**This work happens before SRE turns on the Datadog features, not after.** That ordering is
deliberate and it is about cost.

Datadog bills on how much we send it. Today production emits **4.5 million log lines a day
and 93.6% of them cannot be parsed** — unparsed request and response bodies, split JSON fragments, repeated errors,
serialised payloads. If SRE switched on better log ingestion against that stream, we would
move the waste from Cloud Logging to Datadog and pay more for it.

Five services produce 64% of all production log lines:

| Service | Lines / 2 days | Share | What it is |
|---|---:|---:|---|
| `confins-prod-ms-lms-ar-be` | 2,640,747 | 29% | **Full HTTP bodies, ~90% of them re-ingested at rollouts** — an SRE collection defect, not a squad item; see [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md) |
| `prod-lora-task` | 1,291,274 | 14% | Routine conditions at `warn` |
| `prod-ms-calculation` | 770,394 | 9% | Axios dumps, one per 4xx |
| `prod-ms-cnv` | 752,562 | 8% | The same error 20,000 times a day |
| `prod-ms-bpm` | 387,332 | 4% | Split JSON fragments, stack frames |

None of it is telemetry anyone reads.

**Corrected 14 September 2026.** The first row used to read "genuinely blank lines". The
lines are full request and response bodies whose JSON has no `message` key, and the two-day
sample that produced 2,640,747 caught a one-hour burst in which the Datadog Agent re-read a
month of dead pods' log files. Real traffic for that service is about 200k indexed entries a
day. The 4.5M-a-day figure above is therefore inflated by roughly 1M on burst days and the
"below 2.5M" target is closer than the table suggests. Detail in [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md).

So there are two numbers the whole company is working towards:

| Metric | Today | Target |
|---|---:|---:|
| Production log lines per day | ~4.5M | **below 2.5M** |
| Share of lines Datadog can parse | 6.4% | **above 80%** |

When those are met, SRE enables log-to-trace correlation, line reassembly and per-service
cost filters — on a stream half the size, so it costs about half as much, permanently.

**Until then, the Datadog features you most want stay off.** Not because SRE is slow, but
because switching them on now would make the bill worse without making debugging better.
Your cleanup is what unlocks them.

---

## Part 1 — The five rules

### Rule 1. One log line, one event, under 16 KB

**This is the most important rule and the least obvious.**

The container runtime splits any stdout line longer than **16 KB** into separate chunks.
Datadog receives them as unrelated log entries. The first chunk may parse; the rest arrive
as meaningless fragments.

We measured this in `prod-ms-bpm`. 86% of its log entries are unparseable, and many are
mid-sentence JSON fragments that look like this in the log explorer:

```
NTB","activityId":"Activity_PD_Model_Check_NTB","processDefinitionId":"NDF2W:129:...","dd.service":"prod-ms-bpm"}
```

That is the tail of a log line whose head went somewhere else. It is not searchable, not
parseable, and you pay to store all of it.

So:

- Never log a request body, response body or serialised domain object.
- Never log a collection. Log its size.
- If you need to know what was in a payload, log the identifiers and fetch the payload from
  the system that owns it.

A log line should be a sentence with fields, not a document.

### Rule 2. Log identifiers, never content

| Log this | Not this |
|---|---|
| `applicationId`, `agreementNo`, `customerId` | name, address, identity number, date of birth |
| `status=400 reason="policy not found"` | the whole error object |
| `messageId`, `routingKey`, `bytes=812` | the message body |
| `rows=1043` | the 1,043 rows |

Two real examples from our own code.

`lms-calculation-service/src/helpers/HttpHelper.ts:27` did this:

```ts
logger.error(`Unexpected error at client response interceptor: ${JSON.stringify(error)}`);
```

`JSON.stringify` on an Axios error serialises the request config. That put a **live
`api-secret` header** and customer `birth_date` into production logs, 12,000 times a day.

`bravo-onboarding-service` logs every inbound request body up to **64 KB** through
`CommonsRequestLoggingFilter`. On the customer onboarding service.

Neither was malicious. Both are one line of well-meaning debugging code that shipped.

**The same rule applies to queue consumers, and that is where the Go estate breaks it.**
`bravo-partnership-service` had 70 call sites across 13 RabbitMQ consumers doing this on
every failure path:

```go
Str("body", string(mqMessage.Body)).
```

That is the whole loan application payload, on the error path, at production volume.
`bravo-employee-service` did it in Java on the *success* path — every inbound and outbound
HC message logged in full, at `info`, about **900,000 times a week**, carrying religion,
marital status, date and place of birth, bank account number and holder name.

Log the message ID, the routing key and the size. If you need the payload to diagnose
something, put it behind `isDebugEnabled()` and mask it first.

**A URL can be a credential.** `backend-dashboard-otrs` logs the Google Chat webhook URL
on every message it sends:

```go
log.Printf("✅ Sent ticket %s %s (%s) to channel %s", ..., webhookURL)
```

Google Chat webhook URLs carry their key and token in the query string. Those entries are
in the log index now, and anyone with log read access can post into those spaces. If you
log a URL, drop the query string:

```go
u, _ := url.Parse(raw); u.RawQuery = ""; u.Fragment = ""; u.User = nil
```

**And a field name is not a safety check.** `bravo-notification-service` had
`tag.Any("private_key", config.Environment.VonagePrivateKey)` at `info`, and
`fmt.Printf("… Private key PEM: %s", pemPrivateKey)` — which bypasses the logger entirely,
so no level could ever have suppressed it. It also attached the bearer token to a logger it
then used to report failed parses, so every malformed token was written out in full.

### Rule 3. Use levels honestly

The test is one question: **would somebody do something about this?**

| Level | Use it when | In production |
|---|---|---|
| `error` | Something failed and a person must look | On, alerts on it |
| `warn` | Something is degraded and may need action | On |
| `info` | A significant business event happened | On, sparingly |
| `debug` | You are diagnosing | **Off** |

`prod-lora-task` emits **3.8 million warnings a week**. In a six-hour sample, 1,067 were
`missing in form submission?` — an optional field being absent. Another 130 were
`unexpected client close`, which is a browser tab closing. Nobody will ever act on either.
They belong at `debug`.

`prod-ms-cnv` emits the same error 4,995 times in six hours. That one *is* a real error —
20,000 employee records a day failing to sync. The level is right; the problem is that
nobody noticed, because it is buried in the same stream as the noise.

**A 4xx is not an error.** This is the single most common level mistake in the estate, and
it hides in one place: the exception handler. `bravo-auth-service` funnels every response
through one function that logged at `error` whatever status code it was handed:

```go
func (e *Error) Write(ctx context.Context, code int, message error, details interface{}) Error {
    ...
    log.ErrorX(ctx, e.Message.Error(), tag.Any("code", code), ...)
```

The result: **16,934 errors and 3 info entries a week**, 98.5% error, on an authentication
service. A wrong OTP was an error. An expired refresh token was an error. Four Java
services had the same shape in their `ControllerAdvice` — `bravo-repeat-order-service`
alone logged 51,843 a week that way, including "Agent not found" and bean-validation
failures.

The rule: **let the status code pick the level.** 5xx is yours; 4xx is the caller's.

```go
logAt := log.ErrorX
if code >= http.StatusBadRequest && code < http.StatusInternalServerError {
    logAt = log.WarnX
}
```

**A "not found" that the code already treats as normal is not an error either.**
`bravo-pbf-service` returned `sql.ErrNoRows` from a lookup straight to its message-handling
wrapper, which logged `sql: no rows in result set` — a message that names no agreement, no
queue and no reason — **40,021 times a week, 97% of everything the service logs.** The very
next function in the same file already treated the same error as the normal case.

Honest levels are what make alerting possible. Dishonest levels are why alerting here does
not work.

### Rule 4. Emit JSON, and let the framework do it

Datadog can only give you fields, faceting and alerting on logs it can parse. Across
production, **only 6.4% of our log lines are parsed** — 573,961 out of 9,029,261 over two
days. The other 93.6% are raw text.

Never write your own log formatting. In particular:

- No `System.out.println` — 98 occurrences in our repos, and they bypass the logging
  framework entirely, so no level, no correlation, no filtering.
- No `printStackTrace()` — 51 occurrences.
- No `console.log` in a Node backend — `bfi-digital-web-api` has 679, all at `info`.
- No ANSI colour codes. `prod-ms-calculation` writes terminal escape sequences into
  Cloud Logging, which is why its errors show up as `info`.

**Java** — add the encoder to `pom.xml` *and* wire it in `logback.xml`. We have 24 repos
with `logstash-logback-encoder` in the POM and only about 10 that actually use it; several
wired it in `logback-test.xml` or `logback-backup.xml`, which never load:

```xml
<appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
</appender>
<root level="INFO"><appender-ref ref="CONSOLE"/></root>
```

**Go** — zerolog with JSON output. `bravo-cnv-service` is the reference implementation in
our estate; copy its logger setup.

**Node** — pino or winston, JSON, level from `LOG_LEVEL`, colour only when attached to a
terminal.

### Rule 5. Never let a config default to DEBUG

Two settings in our stack turn into data leaks when a log level moves:

- `feign.client.config.default.loggerLevel: full` logs full request and response bodies,
  but only when that client's logger is at DEBUG.
- `CommonsRequestLoggingFilter` with `setIncludePayload(true)` logs inbound bodies, but
  only at DEBUG.

Six repos set the first. Twenty-two register the second. Most emit nothing **today** purely
because their loggers sit at INFO. That is not safety, it is luck — one `logging.level` line
added to chase a bug turns on body logging for every upstream call.

Three repos are worse: they default the level to DEBUG and rely on a deployment variable to
turn it off.

```yaml
# bravo-agency-service, bravo-approval-engine-service, bravo-core-proxy-service
CommonsRequestLoggingFilter: ${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:DEBUG}
```

So:

- Set `loggerLevel: basic`, never `full`, on the Feign default.
- Set `setIncludePayload(false)`, or put the filter bean behind `@Profile("local")`.
- Pin log levels explicitly in `application-prod.yaml`. A `root: INFO` does **not** override
  a package-level DEBUG set elsewhere — they are different keys, and this exact mistake is
  live in `bravo-bpm-service` and `bravo-onboarding-service` today.
- If a default must exist, make the safe value the default.

**In Go, masking is a deployment setting — check the manifest, not the code.**
`bfi-go-pkg` provides `logger.JSONScrubberFunc(fields)`, and most Go services call it. The
field list it is given comes from the environment:

```go
HTTPClientRequestBodyJSONMaskedFields []string `env:"HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS" envSeparator:","`
```

SRE sets that list **per service and per environment in `app-deployment`**, in
`values-prod.yaml` — see
[backoffice](https://github.com/bfi-finance/app-deployment/blob/master/backoffice/values-prod.yaml#L218-L221)
for the pattern, and
[lora-gateway](https://github.com/bfi-finance/app-deployment/blob/master/lora-gateway/values-prod.yaml#L122-L123)
for the four variables:

```
HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS
HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS
```

Not every service handles PII — `lora-schema` and `database-catalog` do not — so there is
deliberately no estate-wide default. Your service's list is yours to write, and it needs the
field names *your* payloads use, including nested ones. (An earlier version of this guide
said to put a default in the config struct. SRE corrected that: a struct default is the
wrong layer, and in production it would rarely apply anyway, because the manifest already
sets these variables explicitly — often to `""`.)

What this means for you: **read your `values-prod.yaml` before you read your code.** On
14 September 2026, eight Go services had body logging on in production with every masked
field set to `""`, and eight ran at `LOGGER_LEVEL=debug`. Your service's own file in
`bravo-analysis/docs/logging/` has a table of exactly what production sets, and
[deployment-proposal.md](deployment-proposal.md) has the diff if it needs one.

`lora-gateway-service` was a different problem — the scrubber call itself was commented out:

```go
httpclient.WithRequestBodyLoggingLimit(e.HTTPClientRequestBodyLogLimit),
// httpclient.WithRequestBodyLoggingFunc(),
```

so the masked-fields variable was parsed and then never used, and no deployment setting
could have helped. The comment above it read `// HTTP client request body logger (NON
PRODUCTION ENVIRONMENT ONLY)`. It writes **69,433 bodies a week in production**. That is a
code fix, and it is on the branch.

Three things to check in a Go service:

- In `values-<env>.yaml`: if any `*_BODY_LOGGING` is `true`, every matching
  `*_JSON_MASKED_FIELDS` has a real list — not `""`, not absent.
- In the code: every `With*BodyLoggingFunc` is actually wired to
  `logger.JSONScrubberFunc(<the env field>)`, not commented out and not fed a hardcoded slice.
- `*_BODY_LOGGING_ON_ERROR_ONLY` is `true`. Where it is `false`, every call logs its body,
  not just the failures.

**And one thing the wrapper is fixing for everyone:** until
[bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) ships, `JSONScrubber`
masks a matched field only when its value is a string. A NIK or phone number sent as a JSON
number, or a list of phone numbers, goes through untouched however good your list is.

**Java has one target library now, and a waiting room.** [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) merged on
16 September 2026: `bfi-logging-spring-boot-starter` is the logging library every Java
service moves to. Its fix for the old library ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) was closed the same day, so
`bravo-lib-logging` will not change. Which side you are on depends on your Spring Boot
version.

*One thing first, for Platform, not squads:* the starter is merged but **not yet published**.
`bfi-java-pkg` releases a module only when someone runs the manual *Deploy Package*
workflow for that directory, and it has not run for `logging-core` or `logging-starter`.
Until it does, a `pom.xml` that names the starter will not build. Ask Platform to run it
(core first, then the starter) before you start.

*On Boot 3.3 or newer, or 4.x (19 of the 34 Java repositories):* add `bfi-logging-spring-boot-starter`
0.1.0, delete your `logback*.xml`, and leave request logging off unless your service is
the first layer behind the gateway. You get single-line JSON, an 8 KB message cap, stack
traces capped at 8 KB, framework loggers at WARN, and — if you use Feign — one line per
outbound call with no headers and no bodies unless you set
`bravo.logging.feign.include-body=true` for the client you are debugging. Delete any
hand-written `feign.Logger` and its `Logger.Level.FULL` bean so the starter's takes over.
If you are on `bravo-lib-logging` (eight of the 19), remove it and its filter beans in the
same change. The starter reads `LOG_LEVEL` and `LOG_SENSITIVE_KEYS`; tell SRE when you
migrate, because your manifest currently says `LOGGER_LEVEL` and `SENSITIVE_KEYS`. It was
tried against a throwaway app on Boot 3.3.7 and 4.1.1 and behaves the same on both. One
trap: on Boot 3.2 the starter's format include runs before the property that names it
exists, so the service would start with no appender and log nothing; the starter now refuses
to start in that state and says why. `bravo-insurance-service` is the one repository on 3.2
(3.2.11); move to 3.3 first.

*On Boot 2.7 (14 repositories, seven of them on `bravo-lib-logging`):* nothing shared is
coming. The library reads `SENSITIVE_KEYS`, `REQUEST_BODY_LOGGING` and
`RESPONSE_BODY_LOGGING` from the environment, and the two switches **default to `true`** —
so a service that wires its `RequestLoggingFilter` and sets nothing in its manifest logs
every request and response body at INFO. Its key match is case-sensitive (`Authorization` is
not `authorization`), `FeignClientFilter` masks nothing at all, and there is no body size
cap; the pull request that fixed those was closed in favour of the starter. So: merge your
`fix/logging` pull request, set both switches to `false` and write your `SENSITIVE_KEYS` in
`values-prod.yaml`, and put the Boot 3.3 upgrade on the roadmap — it is the only route to
masked, capped, single-line logs for you.

**One compiler trap worth knowing**, because it will bite whoever fixes this: the shared
config function is `func (e *Env) HTTPClient(logger zerolog.Logger)`. That parameter
shadows the `logger` package inside the function, so `logger.JSONScrubberFunc` compiles
against the parameter and fails. Alias the import.

---

## Part 2 — Which Datadog feature answers which question

Stop opening the log explorer first. It is the right tool for about one question in four.

| Your question | Use | Not logs, because |
|---|---|---|
| Why is this request slow? | **APM → Traces** | Logs have no timing or call tree |
| Which upstream is failing? | **APM → Service Map** | You would be guessing from error text |
| Is this error new, and how often? | **Error Tracking** | It groups 4,995 copies into one issue |
| Is the service healthy? | **APM → Service page** | Request rate, errors, latency in one view |
| Is a pod starved or restarting? | **Infrastructure → Containers** | CPU, memory, OOM kills |
| Which SQL query is slow? | **APM → Database Monitoring** | We have DB spans on ~30 services already |
| What did the user actually see? | **RUM** | 55 RUM apps exist; most squads never open them |
| Did the journey work end to end? | **Synthetics** | We have 8 tests, all DNS/SSL. None tests a loan |
| What exactly happened to loan X? | **Logs**, filtered by an id you logged | This is the one logs are for |

### APM — start here

Traces already exist for **42 production services**, 79 million spans over two days,
including database and queue spans. Most squads do not know this.

`https://us5.datadoghq.com/apm/services`

On a service page you get request rate, error rate, p50/p95/p99 latency, and every upstream
and downstream call, without adding a line of code. If your service is in the traced list,
this is free and you are not using it.

**If your service is not traced, that is the single highest-value thing you can fix.** These
12 services send traces but no logs, and these 41 send logs but no traces — see
[sre-datadog-recommendations.md](sre-datadog-recommendations.md) §3 for the lists.

### Error Tracking — the fix for repeated errors

`https://us5.datadoghq.com/apm/error-tracking`

Error Tracking groups identical errors into one issue with a count, a first-seen date and a
trend. The `prod-ms-cnv` problem — the same error 20,000 times a day — is invisible in a log
stream and obvious in Error Tracking.

Use it instead of writing a log-count monitor. It also gives you assignment and a
resolved/ignored state, so two squads do not chase the same error.

### Database Monitoring

DB spans are already flowing for about 30 services (`prod-ms-bpm-postgresql`,
`prod-ms-agreement-postgresql`, and so on). Before you add a timing log around a
repository call, look there.

### RUM

`https://us5.datadoghq.com/rum/performance`

There are **55 RUM applications** registered. If your front end is one of them, you can see
real user page loads, errors and session replays. Several are registered but not processing
events — check with SRE before assuming yours works.

And note Rule 2 applies to the browser too: `bravo-surveyor-console` has 939 `console.log`
calls in customer validation code. Those cost nothing in Cloud Logging but are readable by
anyone holding the device.

---

## Part 3 — The one thing that is missing

**Our logs are not linked to our traces.**

We checked: `@dd.trace_id` returns **zero logs** across all of production. The trace id
appears as raw text in 17,495 log lines — 0.19% — and is not parsed, so it does nothing.

That means you cannot click from a slow trace to the logs for that request, or from an error
log to the trace that produced it. It is the single feature that would most change how
debugging feels here.

**It is gated on the two numbers at the top of this guide.** The SRE side is about two days
of configuration ([sre-datadog-recommendations.md](sre-datadog-recommendations.md) §4), and
it is deliberately held until log volume is down and logs are parseable — because the same
change applied to today's stream would reassemble every 64 KB request body into a single
large billable event.

Your side of it is small but required, and it is what opens the gate:

1. **Emit JSON** (Rule 4). Correlation cannot work on unparsed text.
2. **Keep lines under 16 KB** (Rule 1). A split line loses its trace id.
3. **Do not invent your own correlation id** when a trace id will do. Several services carry
   a `correlationId` MDC field. Keep it if operations rely on it, but it is not a substitute
   — it does not join to traces, metrics or RUM.

---

## Part 3b — If you are logging bodies because Datadog will not show them

Several squads have said the same thing: *we cannot see the request and response body in
Datadog, so we put it in the log.*

**You were right about the gap.** Datadog's Node.js and Java tracers have no supported
setting that puts an HTTP body on a span. Nothing you could have configured would have given
you this. The full investigation is in [body-visibility.md](body-visibility.md).

Three things you should know before you write the next one.

**Your error dump probably does not contain the response.** If you are doing
`JSON.stringify(error)` on an Axios error, you are getting `message`, `name`, `stack`,
`config`, `code` and `status`. Axios deliberately leaves `response` out of that. The request
body is there. The response body — the half you actually wanted — never was.

**It only fires on failures.** A call that returns HTTP 200 with the wrong number in it
produces nothing. For a calculation or pricing service, that is the failure that matters.

**It ships your credentials.** The dumped config carries request headers. One service is
writing a live API secret into production logs about 1,700 times a day this way.

### What to do instead, today

Put the **identifiers and the decision** on the span, not the payload:

```ts
import tracer from "dd-trace";
tracer.scope().active()?.setTag("loan.agreement_no", agreementNo);
tracer.scope().active()?.setTag("loan.tenor", tenor);
tracer.scope().active()?.setTag("calc.rejected_reason", reason);
```

```java
final Span span = GlobalTracer.get().activeSpan();
if (span != null) span.setTag("loan.agreement_no", agreementNo);
```

That is enough to find the request, group the failures, and reproduce the call. Do not put
whole bodies here: a tag value is silently truncated at 25,000 characters, nothing is
redacted for you, and you pay for every one.

### What is coming, and what it is waiting on

SRE is checking whether we can turn on Datadog's **Live Debugger**. It lets you set a probe
on a line of running production code from the Datadog UI, see the variables in scope at that
line, and remove the probe — no code change, no redeploy, nothing left running.

That is the real replacement for body logging, and it is better than what you have: it is
on-demand rather than always-on, it redacts secrets by default, and it produces data only
while someone is actually debugging.

It is not switched on yet. It needs Remote Configuration enabled, and we do not yet know how
Datadog bills the snapshots. **Nobody is asking you to remove body logging before that
replacement exists.** The one exception is any line that carries a credential or customer
data — that goes now, regardless.

---

## Part 3c — Check that your logs and traces use the same name

This takes one minute and it catches a problem that makes a service look half-dead.

Run both searches in the Datadog **us5** org, with your own service name:

```
# Logs Explorer                 # APM Traces
service:prod-ms-yours env:prod  service:prod-ms-yours env:prod
```

**If one returns plenty and the other returns nothing**, widen the log search:

```
kube_deployment:prod-ms-yours
```

- **Results there** — your logs are arriving under a *different service name*. Datadog has
  built two entities out of one workload, so every dashboard and monitor covers half of it.
  Eight production services are in this state right now.
- **Nothing there either** — your logs are not reaching Datadog at all. Eleven busy Bravo
  services are in this state, including `prod-ms-agreement`, which runs 7.4 million spans a
  week and has never sent a log line.

Either way, the fix is not in your application code. The service name on a log comes from the
Kubernetes deployment name; on a trace it comes from `DD_SERVICE`. Nothing reconciles them.
The fix is the unified tagging labels on the pod template. They belong in
`app-deployment/<service>/values-prod.yaml`, under `deploymentLabels` and `podLabels` —
as of 14 September 2026 exactly one service in the estate has them (`bfi-operation-ui`, in
`bfi-app-deployment`). Today the log side gets its service name from the
`ad.datadoghq.com/<container>.logs` annotation in that same file (105 files carry one), and
the trace side gets it from the tracer's own configuration, because only one manifest sets
`DD_SERVICE`. Two sources, nothing reconciling them — which is the split you are looking at:

```yaml
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-yours"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

**Raise it with Platform rather than opening your own pull request.** 104 of the 152 repos
deploy through the shared `bfi-base-template` workflows, so this is one change for most of
the estate instead of 104 separate ones. Your repo's file in this folder has the exact steps
and your service's measured state.

If your tracer sets the name in code, remove it so `DD_SERVICE` is the only source —
`tracer.init({})` rather than `tracer.init({ service: "..." })` in Node.js, and no
`dd.service` in `JAVA_OPTS` for Spring Boot.

## Part 4 — Checklist for your service

Copy this into your squad's next planning session.

**Stop the bleeding**

- [ ] No `JSON.stringify(error)`, `log.error(msg, e)` on expected failures, or body logging
- [ ] No secrets or customer data in any log line — check your HTTP client error paths first
- [ ] `feign.client.config.default.loggerLevel` is `basic`, not `full`
- [ ] `CommonsRequestLoggingFilter` has `setIncludePayload(false)` or is local-only
- [ ] No `System.out`, `printStackTrace()`, `fmt.Print*`, `log.Print*` or backend
      `console.log` — none of them carry a level
- [ ] Log levels pinned explicitly in `application-prod.yaml`
- [ ] No queue consumer logs `string(msg.Body)` — ID, routing key and size only
- [ ] No log line contains a URL with a query string
- [ ] **Go:** in `values-prod.yaml`, every `*_JSON_MASKED_FIELDS` that matters has a real
      list (not `""`); in the code, every `With*BodyLoggingFunc` is wired to the env field
      and not commented out; `*_BODY_LOGGING_ON_ERROR_ONLY` is `true`; `LOGGER_LEVEL` is
      not `debug`
- [ ] **Java:** `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` are set deliberately in
      `values-prod.yaml` (the library defaults both to `true`), and `SENSITIVE_KEYS` lists
      your fields
- [ ] **Your exception handler picks the level from the status code** — 4xx at warn, 5xx at
      error. This is the one that matters most; check it first

**Make logs usable**

- [ ] JSON encoder wired in the config that actually loads in production
- [ ] Every log line carries a business identifier
- [ ] Levels pass the "would anyone act on this?" test
- [ ] Routine conditions moved to `debug` — including "not found" where the code already
      treats it as the normal case
- [ ] No log statement inside a loop over a collection
- [ ] Every repeating message is a **constant string** — identifiers go in fields, never
      interpolated into the message, or Datadog cannot group it and no query can match it

**Use what is already there**

- [ ] Open your service's APM page and look at p95 latency
- [ ] Open Error Tracking and look at your top three issues
- [ ] Check whether your service traces at all — ask SRE if not
- [ ] Check whether your front end has a working RUM app
- [ ] Run the two searches in Part 3c — do your logs and traces use the same name?
- [ ] If they do not, or if one is empty, read your repo's file in this folder and raise it with Platform
- [ ] Put business identifiers on spans with `setTag`, instead of logging the payload

**Available now, no cost, ask SRE**

- [ ] An Error Tracking view for your service — it works on telemetry already flowing
- [ ] One monitor that watches a business outcome, not CPU

**Available once the gate is met**

- [ ] Log-to-trace correlation
- [ ] Tracing for your service, if it is not traced yet
- [ ] Live Debugger, so you can stop logging bodies altogether — see Part 3b
- [ ] One synthetic test that exercises your squad's critical journey

---

## Part 5 — Where to look

| What | Link |
|---|---|
| APM services | `https://us5.datadoghq.com/apm/services` |
| Error Tracking | `https://us5.datadoghq.com/apm/error-tracking` |
| Log explorer | `https://us5.datadoghq.com/logs` |
| Infrastructure | `https://us5.datadoghq.com/containers` |
| RUM | `https://us5.datadoghq.com/rum/performance` |
| Synthetics | `https://us5.datadoghq.com/synthetics/tests` |
| Monitors | `https://us5.datadoghq.com/monitors/manage` |

Our Datadog site is **us5**. A link starting `app.datadoghq.com` will not resolve to our org.

### Your service probably already has a pull request

Every repository in this programme has a file in `bravo-analysis/docs/logging/` named after
it, and 48 of the 73 have an open pull request on a branch called `fix/logging` (16 more were closed on 14 September 2026 because their only change belonged in `app-deployment`, not in code). The file
names the finding, quotes the production numbers, says what the change does and — just as
importantly — says what it deliberately left alone for you to decide.

Two things to know before you review one:

- **Both the Go and the Java ones are built.** Every Go change has had `go build`, `gofmt`
  and `golangci-lint` run against it locally and the shipped unit tests pass. Every Java
  change was compiled on 14 September 2026 with a JDK and Maven from `mise` (22 of
  22 compile), and 12 of the 12 test suites that were run pass; each file's
  verification note says which. Ten defects have been found between CI, the local toolchain
  and one repository's own test suite; read the CI result, not the diff alone.
- **A red check is probably not yours, but read it rather than assuming.** Across the 44
  pack-two pull requests, 27 jobs are red and 26 of them are dependency CVEs, container-image
  CVEs, a missing Codacy token, a broken Codacy installer script or a SonarQube coverage
  gate — all red before this work. The 27th was real: a Java change that dereferenced a null
  and turned an `AmqpRejectAndDontRequeueException` into a `NullPointerException`, caught by
  the repository's own test. Assuming the cluster was all one cause is exactly the mistake
  made here first; see [README.md](README.md#every-failing-job-checked-one-at-a-time).

Index with every link: [README.md](README.md).

---

## Why this matters beyond tidiness

Logging costs **Rp 636M a month** across three platforms. About a third of the Cloud Logging
share is non-production. Details in [logging-cost.md](logging-cost.md).

But cost is the smaller argument. The larger one is that we are paying for 9 million log
lines a day that we cannot search, cannot correlate to a trace, and cannot alert on — while
a live API secret sat in them and 20,000 employee records a day failed silently.

Following this guide makes the bill smaller. More importantly it makes the next incident
shorter — and it is the thing standing between us and the Datadog features we already pay
for.
