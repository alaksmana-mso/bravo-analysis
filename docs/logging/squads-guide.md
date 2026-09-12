# Logging and observability — the guide for squads

Written 12 September 2026. For every squad shipping a service at BFI.

BFI is standardising on Datadog for logs, traces and metrics. Cloud Logging stops being the
place you go to debug. This guide says what to log, what not to log, and which Datadog
feature answers which question.

It is based on measurements from all 152 repos and two days of production telemetry, not on
general advice. Where a rule exists, it is because something in our estate is broken by
breaking it.

---

## Why squads go first

**This work happens before SRE turns on the Datadog features, not after.** That ordering is
deliberate and it is about cost.

Datadog bills on how much we send it. Today production emits **4.5 million log lines a day
and 93.6% of them cannot be parsed** — blank lines, split JSON fragments, repeated errors,
serialised payloads. If SRE switched on better log ingestion against that stream, we would
move the waste from Cloud Logging to Datadog and pay more for it.

Five services produce 64% of all production log lines:

| Service | Lines / 2 days | Share | What it is |
|---|---:|---:|---|
| `confins-prod-ms-lms-ar-be` | 2,640,747 | 29% | **Genuinely blank lines** |
| `prod-lora-task` | 1,291,274 | 14% | Routine conditions at `warn` |
| `prod-ms-calculation` | 770,394 | 9% | Axios dumps, one per 4xx |
| `prod-ms-cnv` | 752,562 | 8% | The same error 20,000 times a day |
| `prod-ms-bpm` | 387,332 | 4% | Split JSON fragments, stack frames |

None of it is telemetry anyone reads.

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
The fix is the unified tagging labels on the pod template, in the GitOps repo:

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
- [ ] No `System.out`, `printStackTrace()`, or backend `console.log`
- [ ] Log levels pinned explicitly in `application-prod.yaml`

**Make logs usable**

- [ ] JSON encoder wired in the config that actually loads in production
- [ ] Every log line carries a business identifier
- [ ] Levels pass the "would anyone act on this?" test
- [ ] Routine conditions moved to `debug`
- [ ] No log statement inside a loop over a collection

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
