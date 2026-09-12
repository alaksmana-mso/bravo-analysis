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
`bravo-inventory-management-service` runs a shared library whose masking behaviour nobody in
this analysis could read, because the source is not in `squads/`.

**A shared library is the leverage point.** `com.bfi.bravo:bravo-lib-logging` provides
`RequestLoggingFilter`, `FeignClientFilter` and `LoggerUtil`, and fifteen repos depend on
it, at four different versions. Its source is not in `squads/`. Whoever owns it can change
body-logging behaviour across the Java estate in one place — the same leverage
`bfi-base-template` gives for deployment manifests.

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
`source:dd_debugger` into a log index you create. Datadog's documentation does not state
whether these count against log ingestion and indexing or are included with APM. Ask the
account team three questions first: does `source:dd_debugger` count against ingested GB and
indexed events; is there a bundled allowance with APM; and does Datadog's "no sampling"
instruction for that index interact with our commitment tier.

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
- **`com.bfi.bravo:bravo-lib-logging`.** Fifteen repos depend on it at four versions. Its
  source is not in `squads/`, so what its `RequestLoggingFilter` and `FeignClientFilter`
  actually capture and mask is unknown. One of those repos runs it in production today.
- **`ConfinsRequestLog` in `bravo-edoc-service`.** Size, retention and read access unknown.
- **The Node.js tracer version actually running.** `lms-calculation-service`'s lockfile says
  5.109.0 and `package.json` says `^5.81.0`. Production spans carry no tracer version tag.
  Below 5.84.0, probes cannot be enabled from the UI.
- **Datadog's billing treatment of `source:dd_debugger`.** Not stated in their documentation
  in either direction. Account team question.
