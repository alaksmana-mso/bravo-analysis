# Why squads cannot see request and response bodies in Datadog

Written 12 September 2026. Evidence is Datadog production over a 7-day window, plus all 152
repos under `squads/` at `master`.

The complaint: *"We cannot see the request and response body in Datadog, for example in
`lms-calculation-service`. That is why we put it in the log."*

**The complaint is correct.** Datadog is not showing them bodies, and nothing they could
have configured would have. They worked around a real gap.

This document is the estate-level view and the list of what SRE should enable. **The
findings for each service live in that service's own file** — what it captures today, what
it does not, and what to do about it. The index is in section 2.

---

## 1. The complaint is true, and it is not about one service

No Datadog tracer, in any language, has a supported setting that puts an HTTP request or
response body on a span. The only payload-shaped thing any of them can attach is headers,
through `DD_TRACE_HEADER_TAGS`, and that is headers only.

This is not a misconfiguration and it is not specific to Node.js. A developer opening a
failed `POST` in Datadog sees that it failed, the route, the status code and the duration.
To debug a calculation result, a scoring decision or a disbursement, that is not enough.

Tracing itself is healthy. `prod-ms-calculation` reported 5,430,270 spans in seven days and
around 100% of its `express.request` spans are retained. The traces are there. The content
is not.

So squads filled the gap themselves — fifteen different ways.

---

## 2. What each service actually does — the index

Every row links to the file that carries the evidence, the code references and the fix.

| Service | Body capture in production | Detail |
|---|---|---|
| `prod-ms-bpm` | **On.** 487,146 request and 471,241 response bodies a week, at INFO, **unmasked** | [bravo-bpm-service.md](bravo-bpm-service.md) |
| `prod-inventory-management` | **On.** Shared-library request logger plus `loggerLevel: full`, both defaulting to on | [bravo-inventory-management-service.md](bravo-inventory-management-service.md) |
| `prod-ms-bfi-insurance-api` | **On, through error paths.** 90,553 entries a week carrying NIK, addresses and bank account numbers | [bfi-insurance-api.md](bfi-insurance-api.md) |
| `prod-ms-calculation` | **On, and only half of it works.** Request body captured, response body never | [lms-calculation-service.md](lms-calculation-service.md) |
| `prod-ms-edoc` | **On, into a database.** A `ConfinsRequestLog` table holds request and response payloads | [bravo-edoc-service.md](bravo-edoc-service.md) |
| `prod-ms-bfi-payment-api` | Off by design — separate prod and non-prod beans | [bfi-payment-api.md](bfi-payment-api.md) |
| `prod-ms-cnv` | Off by design — switches, size limits and 30-field masking | [bravo-cnv-service.md](bravo-cnv-service.md) |
| `prod-ms-user-iam` | Off by design — same transport, correctly disabled | [bravo-user-iam-service.md](bravo-user-iam-service.md) |
| `prod-ms-onboarding` | Off. Carries the best masking list in the estate | [bravo-onboarding-service.md](bravo-onboarding-service.md) |
| `prod-ms-agency` | Dormant. Feign defaults to `FULL`; only the logger level stops it | [bravo-agency-service.md](bravo-agency-service.md) |
| `prod-ms-customer` | Dormant. Five INFO entries in seven days | [bravo-customer-service.md](bravo-customer-service.md) |
| `prod-ms-payment` | Dormant. Heaviest user of the shared logging library | [bravo-payment-service.md](bravo-payment-service.md) |
| `prod-lora-task` | Dormant, at `Debug`. 11 log lines per span is the real problem | [lora-task-service.md](lora-task-service.md) |
| `prod-ms-agreement` | Dormant — **and no logs reach Datadog at all**, against 7.5M spans | [bravo-agreement-service.md](bravo-agreement-service.md) |
| `prod-ms-branch` | Dormant, **two mechanisms registered unconditionally**, no logs arriving | [bravo-branch-service.md](bravo-branch-service.md) |
| `prod-ms-lms-gateway` | Dormant, no logs arriving | [bravo-lms-gateway.md](bravo-lms-gateway.md) |
| `prod-ms-approval-engine` | Dormant, no logs arriving | [bravo-approval-engine-service.md](bravo-approval-engine-service.md) |
| `prod-ms-bravo-core-proxy` | Dormant, no logs arriving | [bravo-core-proxy-service.md](bravo-core-proxy-service.md) |
| `digital-prod-ms-bfi-digital-web-api` | Error objects, not bodies — and outside every `env:prod` view | [bfi-digital-web-api.md](bfi-digital-web-api.md) |
| `bravo-surveyor-console` | Browser. RUM is the answer here, not Live Debugger | [bravo-surveyor-console.md](bravo-surveyor-console.md) |

### Three things that index makes obvious

**The squads did the engineering.** `bravo-onboarding-service` masks NIK, email, password,
spouse name and access tokens on both directions. `bravo-cnv-service` has per-direction
switches, 32 KB limits and a thirty-field scrubber. `bfi-payment-api` splits prod and
non-prod into separate beans. These are not careless teams. They built what Datadog did not
give them.

**The two that are switched on are the two with the least protection.**
`bravo-bpm-service`'s `CustomFeignLogger` has no masking and no size limit at all.
`bravo-inventory-management-service` runs a shared library whose masking behaviour, when
this was first written, nobody in this analysis could read.

**A shared library is the leverage point — and it has now been read.** `com.bfi.bravo:bravo-lib-logging`
is the `logger` module of [`bfi-finance/bfi-java-pkg`](https://github.com/bfi-finance/bfi-java-pkg);
**eighteen** repositories depend on it, at versions 1.2.7, 2.0.3 and 2.1.4 against a library
at 1.3.10. What it does, read on 14 September 2026: `REQUEST_BODY_LOGGING` and
`RESPONSE_BODY_LOGGING` **default to `true`**, so a service that wires its
`RequestLoggingFilter` and sets nothing logs every request and response body at INFO;
`SENSITIVE_KEYS` defaults to six names and is matched **exactly and case-sensitively**, so
`Authorization` is not `authorization`; **`FeignClientFilter` logs both Feign bodies
unmasked** and ignores both switches; there is no body size cap; and `CustomAppender` copies
every Hibernate SQL statement into the MDC, where it rides along on the next log line.
[bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) fixed the masking,
the case and the size cap in one place — and **was closed on 16 September 2026**, the day
#122 merged, so that the estate has one Java logging library to maintain rather than two.
`bravo-lib-logging` therefore keeps the defaults above. For the seven Boot 2.7 repositories
on it the fix is the per-service pull request plus the two switches in `values-prod.yaml`
(as the Go services do), until they move to Boot 3.3 and the starter (§2a).

### 2a. The new Java starter — bfi-java-pkg#122, read 15 September 2026, merged 16 September

A colleague opened [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) on 14 September: `bfi-logging-core` (a Logback/logstash JSON
encoder with volume controls) and `bfi-logging-spring-boot-starter` (Spring Boot 3.3+/4.x
auto-configuration). Read in full. **Merged to `master` on 16 September 2026** (`dfeb6ac`,
24 commits, 67 files) as version 0.1.0 of both modules. It is now the one Java logging
library this programme points at: `bravo-lib-logging` stays as it is, and its fix (#123)
was closed the same day.

**Merged is not published.** The repository releases a module only when someone runs the
manual *Deploy Package* workflow for that module's directory; it last ran on 30 January 2026
and has not run for `logging-core` or `logging-starter`. Until Platform runs it twice (core
first, then the starter), no service can add the dependency — a build would fail to resolve
it. That single step is now the gate on every Java item in this programme.

**What it gets right, and why it matters here:**

- **A message cap at the encoder** — `TruncatingMessageJsonProvider`, 8,192 characters, plus
  stack traces capped at 8,192 characters and 20 frames. This is the only wrapper-level
  change that shortens `prod-ms-bpm`'s Feign lines (99.99% of 86,600 a day hit Datadog's
  76,800-byte limit): bpm is on Boot 3.5.16 and does not use `bravo-lib-logging`, so #123
  cannot reach it. It also keeps Java lines under the 16 KB split that leaves 93.6% of
  production logs unparseable.
- **Single-line JSON** with `level`, `timestamp`, `service`, `version`, `env`, and
  `trace_id`/`span_id` normalised from `dd.trace_id` (the MDC passthrough keeps `dd.trace_id`
  too, so Datadog's own correlation still works). bpm logs a plain-text pattern today.
- **Request logging off by default**, payload off by default, 2 KB payload cap — the opposite
  of the lib's `true`/`true`.
- Async appender that drops rather than blocks, duplicate-message filter, framework loggers at
  WARN, `LOG_LEVEL` with an INFO default. Tests on every class.

**What it left out, and what we added on 15 September** (four commits on the PR branch,
`mvn verify` green, 58 + 39 tests):

| Gap as opened | Fix pushed |
|---|---|
| No outbound (Feign) handling at all — the estate's largest body source is a Feign logger | `BravoFeignLogger`: one INFO line per call (client, method, URL, status, `duration_ms`), **never headers**, bodies opt-in (`bravo.logging.feign.include-body`, default `false`), masked and capped; backs off if the service has its own `feign.Logger` bean |
| The PII regex never ran over the `message` field — a body logged as a plain string was capped but not masked | `maskPii` on the message provider, default on, `LOG_MASK_MESSAGE_PII` to turn off |
| `request_body` was regex-masked only — the key deny-list never saw a body's fields | `MaskingValueUtil.maskJson`: parse JSON, mask every field by key whatever its type, regex fallback |
| Both READMEs linked a guideline at `../docs` that is not in the repository | Plain text; new properties documented |
| Spring Boot 3 only — and, as found on the second review, **Boot 3.3 or newer**: on Boot 3.2 (Logback 1.4) the format include runs before the Spring property that names it exists, and the service starts with no appender and logs nothing | Not fixable for 2.7 (jakarta). 14 of 34 Java repositories are on Boot 2.7; #123 was to be their bridge and was closed on 16 September, so they stay on their current code and manifest switches until they upgrade to Boot 3.3. For 3.2 the fifth commit adds a startup check that fails the boot with the reason instead of running silent; `bravo-insurance-service` (3.2.11) must move to 3.3 first |

**Second review, 15 September afternoon.** The author rebased the branch onto master and
added eight commits: the PR pipeline now builds and scans the two new modules; a `.codacy.yml`
excludes test sources from Codacy; the starter's parent moved from Boot 3.3.7 to 3.5.16;
Logback 1.5.36, logstash-logback-encoder 8.1 and Jackson 2.22.2 are pinned; and a
`logging-starter/.snyk` file ignores seven Spring Framework advisories until 15 March 2027.
Every check is green: 61 + 42 tests, Codacy 0 issues, both SNYK scans clean. Two things to
know about that green:

- The seven ignores are honest. Each advisory's only fix is Spring Framework 7.0.9, because
  Spring Framework 6.2 and Boot 3.5 left open-source support on 30 June 2026. Every Spring
  CVE from now on lands in this file until the library moves to Boot 4, so the expiry date is
  the real control. Boot 4.0 itself leaves open-source support on 31 December 2026.
- The Jackson and Logback pins live in the modules' own build, so they make the library's scan
  clean; a consuming service still gets the versions its own Boot BOM manages.

We then built a throwaway consumer against three Boot lines. On 3.3.7 and 4.1.1 the starter
works as shipped: one JSON line per event, the 16-digit identifier redacted, `correlation_id`
carried into handler logs. On 3.2.11 the app started, served requests and **wrote nothing**:
Logback 1.4 evaluates the format include before the Spring property exists, only a Logback
status warning records it, and the same app passes once Logback is pinned to 1.5.18. One
production repository, `bravo-insurance-service`, is on 3.2.11. The fifth commit on the branch
adds a startup check (`bravo.logging.startup-check.enabled`, default on, previously a documented
property bound to nothing) that fails the boot with the reason, and the README now says Boot
3.3 or newer.

**What it does not do, and will not:** capture outbound bodies for debugging. That is still
Live Debugger's job (§5), once Remote Configuration works.

---

## 3. Three defects that make all of this worse

These apply estate-wide and they are the reason the complaint feels bigger than "no bodies".

### Most logs are not JSON

93.6% of production log volume is not parseable by Datadog. Services that build a JSON
formatter then override it on the transport — `lms-calculation-service` is the clearest
example — send Datadog a string, not fields. There is nothing to filter on and nothing to
facet.

### Severity is thrown away

Where the level is rendered *inside* the message, Datadog never sees it as a level. Over
seven days `prod-ms-calculation` sent 2,397,823 log entries and **1,325** carry
`status:error`. A developer filtering that service for errors misses almost all of them.

### There is no link from a log to its trace

> Across **all of production**, a search for logs carrying `@dd.trace_id` returns **zero
> results**.

Not one service in the estate can pivot from a log line to its trace, or from a trace to its
logs.

It is closer than it looks. **21 services already emit `dd.trace_id` inside their log
text** — 48,690 entries in seven days, led by `prod-ms-assistance` at 42,442 and
`prod-inventory-management` at 5,819. The tracer's log injection is working. Datadog is not
parsing it, because the field sits inside a text message rather than in a JSON attribute.

That makes correlation a pipeline and formatting problem, not an instrumentation problem —
which is a much shorter job than it appeared.

---

## 4. What is not the answer

**App and API Protection.** It can attach request bodies to spans, but only when a security
rule fires, truncated, redacted, and gated on a policy the squad does not control. Response
bodies are never collected. It is enabled today on exactly one non-production .NET service.
It is not a debugging tool and should not be sold as one.

**Raising the log message size cap.** That turns today's payload dumps into larger billable
Datadog events. It is the opposite of the fix.

**Asking squads to log bodies "properly".** Any always-on body logging puts customer data
into a system with broad read access and pays per gigabyte for data nobody reads. The goal
is to make body logging unnecessary, not tidier.

---

## 5. What SRE should enable

Five items. Item 5.0 is new, and it blocks the one that matters most.

### 5.0 Fix Remote Configuration — it is failing right now

This was listed as "unverified, check first" in the first version of this document. It has
now been measured, and the answer is worse than unverified.

Thirteen production Java services are polling for Remote Configuration and **failing**:

```
[dd-remote-config] WARN datadog.remoteconfig.ConfigurationPoller - Failed to retrieve
remote configuration: unexpected response code Internal Server Error 500
rpc error: code = Unknown desc = empty targets meta in director local store
```

Roughly 91,000 failed polls in seven days. The worst offenders:

| Service | Failed polls, 2 days |
|---|---:|
| `prod-ms-bfi-payment-api` | 679 |
| `prod-ms-bfi-insurance-api` | 579 |
| `prod-ms-employee` | 509 |
| `prod-ms-insurance` | 497 |
| `prod-ms-payment` | 477 |
| `prod-ms-lms-ops` | 475 |
| `prod-ms-agency` | 452 |
| `prod-inventory-management` | 302 |
| `prod-ms-onboarding` | 207 |
| `prod-ms-bpm` | 191 |

`empty targets meta in director local store` means the Agent has no Remote Configuration
state to serve. In practice that is one of three things: Remote Configuration is not enabled
on the Datadog org, the Agent's API key does not carry the Remote Configuration capability,
or the Agent has it switched off.

**Live Debugger cannot be enabled until this is fixed.** Neither can remote tracer
configuration or any other UI-driven change. It is also generating a small stream of billable
error logs on thirteen services for no benefit.

This is now the first item, ahead of everything else in this section.

### 5.1 Log-to-trace correlation

The highest-value change in this document and the cheapest. A developer who can go from a
trace to that request's logs in one click recovers most of what they are missing — more than
body capture gives them.

```yaml
DD_LOGS_INJECTION: "true"
DD_ENV: prod
DD_SERVICE: <service>
DD_VERSION: <image tag>
```

SRE's side is the environment variables and confirming the Trace Id Remapper is on the
pipeline. The squad side is emitting JSON so the injected fields survive. Full detail in
[sre-datadog-recommendations.md §4](sre-datadog-recommendations.md).

Start with `prod-inventory-management`. It already writes `dd.trace_id` into 5,819 log
entries a week; it needs the format and the pipeline, not the instrumentation.

**Datadog cost: none.** Same events, with extra fields.

### 5.2 Header tags — one variable, today

```yaml
DD_TRACE_HEADER_TAGS: "x-request-id,x-correlation-id,x-b3-traceid,content-type,content-length"
```

Incoming headers land on spans as `http.request.headers.*`, outgoing as
`http.response.headers.*`. This does not give bodies. It gives the correlation identifiers
that tie a Datadog trace to a record in another system, plus the payload size — which
answers a surprising share of "what was sent" questions on its own.

Never add `authorization`, `api-secret`, `cookie` or `set-cookie` to this list.

**Datadog cost: negligible.**

### 5.3 Live Debugger — the replacement for body logging

A probe set on a line of running production code from the Datadog UI, capturing the
variables in scope, then removed. No code change, no redeploy, nothing left running.

That is strictly better than logging bodies: on demand rather than always on, rate limited,
secrets redacted by default, and producing data only while someone is debugging.

**Prerequisites:**

| Requirement | Status |
|---|---|
| Remote Configuration working end to end | **failing — see 5.0** |
| Datadog Agent 7.49.0 or later | check per cluster |
| Agent log collection on, or `DD_APM_DEBUGGER_LOGS_ENABLED_OVERRIDE=true` | on for most clusters |
| `DD_DYNAMIC_INSTRUMENTATION_ENABLED=true` on the service | not set anywhere |
| RBAC roles `live_debugger_read` / `live_debugger_write` | not granted |

A 30-day search for `source:dd_debugger` returns zero results. Nothing in the org uses it.

**What each stack actually gets — tell squads this up front, or the pilot will look like a
failure:**

| Stack | Services | What is available |
|---|---|---|
| Java | 14 of the 20 documented services | **Method probes** — name a method, get its arguments and return value. The strongest option, and it covers the two services with body logging switched on. |
| Node.js | `lms-calculation-service`, `bfi-digital-web-api` | **Line probes only.** Pick a line, get the variables in scope at that line. No method probes, no return-value capture. |
| Go on OpenTelemetry | `bravo-cnv-service`, `lora-task-service`, `bravo-user-iam-service` | **Nothing.** See 5.5. |
| Browser | `bravo-surveyor-console` | **Nothing.** RUM is the answer instead. |

Four limits that apply to every probe:

1. **Node.js is line probes only** (see the table above).
2. **Do not probe a line where you must walk in through `req`.** Default capture depth is 3
   levels and 20 fields per object; an Express `req` blows past both, and an object with
   more than 500 properties disables snapshotting for that probe.
3. **Strings truncate at 255 characters by default**, collections at 100 elements. Raise per
   probe, deliberately.
4. **Snapshot probes are limited to one capture per second**, with a ceiling of 25 per second
   across a process. A debugging tool, not a sampler.

Secrets are redacted by default — the built-in list covers `secret`, `apisecret`,
`password`, `token`, `authorization`, `cookie`, `ssn` and around sixty more. Add
BFI-specific names — `nik`, `no_ktp`, `norek` — with
`DD_DYNAMIC_INSTRUMENTATION_REDACTED_IDENTIFIERS`. Note that
`DD_DYNAMIC_INSTRUMENTATION_REDACTED_TYPES` is documented by Datadog but is **not
implemented in the Node.js tracer**; do not rely on it.

**Cost: confirm before enabling.** Snapshots are delivered as log events tagged
`source:dd_debugger` into a log index you create. Our contract (order `Q-849776`, read on
14 September 2026) has no Live Debugger line, so if they bill as ordinary logs they land on
the two lines we are already over: ingestion at **$0.10/GB** and indexed events at
**$1.59–1.91 per million** in overage. Datadog's documentation does not state whether they
count there or are included with APM. Two questions remain for the account team: does
`source:dd_debugger` count against ingested GB and indexed events, and does Datadog's "no
sampling" instruction for that index interact with our commitment tier.

### 5.4 Manual span tags — the targeted fallback

Where a squad needs a specific field on every request rather than during a debugging
session, put it on the span:

```java
final Span span = GlobalTracer.get().activeSpan();
if (span != null) { span.setTag("loan.tenor", tenor); }
```

Right for *identifiers and decisions*. Wrong for whole bodies: a tag value is truncated at
25,000 characters silently, there is no redaction, and every tag is billed as part of the
span.

### 5.5 Three services cannot have Live Debugger at all

`bravo-cnv-service`, `lora-task-service` and `bravo-user-iam-service` are instrumented with
**OpenTelemetry**, not the Datadog tracer. `go.opentelemetry.io/otel` and the `otelhttp` /
`otelgrpc` contrib packages are their direct dependencies; `github.com/DataDog/dd-trace-go/v2`
appears only as an indirect dependency pulled in by Agent packages.

dd-trace-go does subscribe to Datadog's `LIVE_DEBUGGING` remote-config product at the
versions in use — but only when you instrument with it. Under OpenTelemetry there is no
probe mechanism.

Between them those three services account for **13.2 million spans a week**, including the
single busiest service in the estate. Whatever SRE enables for the Java estate does not reach
them. That is a real cost of the split tracing stack, and it belongs in the decision recorded
in [sre-datadog-recommendations.md §7](sre-datadog-recommendations.md).

`bravo-surveyor-console` is a browser application and has no server-side tracer at all. Its
answer is RUM, and it is one setting away from working — see its own file.

---

## 6. The trade to put to the squads

Squads are being asked to remove body logging. They should get something back in the same
breath, and the sequencing should be explicit:

| SRE delivers | Squad removes |
|---|---|
| Remote Configuration that works | Nothing yet — this is the unblocker |
| Log-to-trace correlation | Timestamp-grepping as a debugging method |
| Header tags with correlation IDs | Logging request metadata by hand |
| Live Debugger, with a named owner per squad | Always-on body logging |

**Do not ask for the removal before the replacement exists.** The squads are logging bodies
because they had no alternative. Taking that away first will be resisted — correctly.

Two exceptions, both of which go now on their own schedule:

- The credential leak in `lms-calculation-service`. That is a security fix, not part of this
  programme.
- The unowned payload table in `bravo-edoc-service`. Nobody is asking for it to be deleted —
  it needs an owner, a size and a retention policy, this sprint.

---

## 7. What could not be checked

- **Why Remote Configuration returns `empty targets meta`.** The failure is measured; the
  cause is one of three things and needs an SRE with access to the org settings and the
  Agent configuration. This is now the first item in section 5.
- ~~**`com.bfi.bravo:bravo-lib-logging`.** Fifteen repos depend on it at four versions. Its
  source is not in `squads/`, so what its `RequestLoggingFilter` and `FeignClientFilter`
  actually capture and mask is unknown.~~ **Resolved 14 September 2026** — the source is
  `bfi-finance/bfi-java-pkg`; eighteen repos depend on it; both filters capture bodies by
  default and `FeignClientFilter` masks nothing. See above. The library-level fix
  ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) was closed on
  16 September; the target for every Java service is the starter merged in
  [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) (§2a), reached
  by Boot 3.3+ services once it is published and by Boot 2.7 services after they upgrade.
- **`ConfinsRequestLog` in `bravo-edoc-service`.** Size, retention and read access unknown.
- **The Node.js tracer version actually running.** `lms-calculation-service`'s lockfile says
  5.109.0 and `package.json` says `^5.81.0`. Production spans carry no tracer version tag.
  Below 5.84.0, probes cannot be enabled from the UI.
- **Datadog's billing treatment of `source:dd_debugger`.** Not stated in their documentation
  in either direction, and not a line in our contract. Account team question; the rates it
  would fall under if it bills as logs are in §5.3 above.
