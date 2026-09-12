# Datadog configuration — recommendations for SRE

Written 12 September 2026. Audience: SRE and Platform.

BFI is standardising on Datadog for logs, traces and metrics. This document is a
configuration audit of what is in Datadog today, across every environment, and what to
change.

Everything here was measured on 11–12 September 2026 against our **us5** org, plus a scan of
all 152 repos under `squads/`.

**The headline:** the expensive parts of Datadog are already deployed and working. APM
covers 42 production services with 79 million spans over two days, including database and
queue spans. What is missing is mostly configuration — and three defects that make parts of
the current setup silently useless.

---

## 0. Read this before enabling anything

**Sequencing is deliberate. Squad log cleanup comes first. SRE enablement comes second.**

Datadog bills on ingested bytes and indexed events. Most of the enablement in this document
would increase that. Our production log stream is currently **4.5 million entries a day, of
which 93.6% are unparsed** and a large share is measurable waste — blank lines, repeated
errors, serialised payloads.

If we enable ingestion improvements against today's stream, we do not fix the problem. We
move it from Cloud Logging at Rp 271.8M a month to Datadog at Datadog prices, on top of the
Rp 110.6M we already spend there.

The specific trap is §3's partial-line reassembly. It works by rejoining log lines that the
container runtime split at 16 KB. That is the right fix — but applied to today's stream it
would rejoin `bravo-onboarding-service`'s 64 KB request bodies and
`lms-calculation-service`'s Axios dumps into **single large billable events**. We would be
paying Datadog to carefully reassemble the exact content that should never have been logged.

So the order is:

| Phase | What | Effect on Datadog cost | Gate to exit |
|---|---|---|---|
| **1** | Cloud Logging savings + defect fixes | **None** — no Datadog change | Nothing to gate |
| **2** | Squads cut log volume ([squads-guide.md](squads-guide.md)) | **Reduces** | Prod log entries below 2.5M/day and parsed share above 80% |
| **3** | SRE ingestion and correlation enablement | Increases, but from a smaller base | Ingest measured, per-service filters in place |
| **4** | Paid add-on products | Increases per product | Enable one at a time, measure each |

Phase 1 saves **Rp 81–105M a month** and touches nothing in Datadog. Start there today.
Phase 3 waits for the gate, not for a date.

### What the gate is worth

Five services produce 64% of all production log entries, and most of that volume is waste:

| Service | Entries / 2 days | Share | What it is |
|---|---:|---:|---|
| `confins-prod-ms-lms-ar-be` | 2,640,747 | 29% | **Genuinely blank log lines** |
| `prod-lora-task` | 1,291,274 | 14% | Routine conditions logged at `warn` |
| `prod-ms-calculation` | 770,394 | 9% | Axios config dumps, one per 4xx |
| `prod-ms-cnv` | 752,562 | 8% | The same error 20,000 times a day |
| `prod-ms-bpm` | 387,332 | 4% | Split JSON fragments, stack frames |
| **Top five** | **5,842,309** | **64%** | |

None of that is telemetry anyone reads. Removing it roughly halves the stream before we ask
Datadog to ingest it properly — so every per-GB item in Phase 3 costs about half as much,
permanently.

**That is the whole argument for this ordering.** The cleanup is not a prerequisite because
it is tidy. It is a prerequisite because it changes the price of everything after it.

---

## 1. What is configured today

### Environment coverage

| Environment | Logs, 2 days | APM spans, 2 days |
|---|---:|---:|
| `prod` | 9,029,261 | 79,251,410 |
| `prod-sharia` | 41,518 | 831,429 |
| `digital-prod` | 1,191 | 678,028 |
| `production` | 0 | 100,230 |
| `none` | 0 | 76,840 |
| `sit` | 0 | 13,291 |
| `uat` | 0 | 1,904 |
| `test` | 0 | 462 |

Three problems visible in that table.

1. **No non-production logs reach Datadog at all.** dev, SIT and UAT log only to Cloud
   Logging, where they cost **Rp 93.1M a month**. Engineers debugging a SIT failure cannot
   use the tool we are standardising on. Fixing this is Phase 3, not Phase 1 — see §8.
2. **`prod` and `production` are both in use.** They are separate environments to Datadog.
   Any query, monitor or dashboard scoped to `env:prod` silently excludes the 100,230 spans
   tagged `production`.
3. **76,840 spans are tagged `env:none`** — unified tagging is not set on those services.

### Instrumentation, from the repos

| Signal | Repos | Note |
|---|---:|---|
| `dd-java-agent` attached in Dockerfile | 26 | Works |
| `dd-trace-go` in `go.mod` | 35 | Works |
| OpenTelemetry in `go.mod` | 54 | **Second tracing stack, see §7** |
| `logstash-logback-encoder` in `pom.xml` | 24 | Only ~10 wired into a loading config |
| `DD_ENV` / `DD_SERVICE` set in repo | **0** | Set in deployment manifests only |
| `DD_LOGS_INJECTION` set in repo | **0** | See §3 |
| `DD_PROFILING_ENABLED` | **0** | Not enabled anywhere |
| `DD_DBM_PROPAGATION_MODE` | **0** | Not enabled anywhere |
| `DD_RUNTIME_METRICS_ENABLED` | **0** | Not enabled anywhere |

Datadog API keys are correctly referenced from GitHub Actions secrets
(`${{secrets.BRAVO_DD_API_KEY}}`). **No committed keys were found.** That part is clean.

### Other products

| Product | State |
|---|---|
| RUM | 55 applications registered; at least 11 have `rum_event_processing_state: NONE`; `product_analytics_retention_state: NONE` on all |
| Synthetics | **8 tests, all DNS or SSL checks.** No API tests, no browser journeys |
| Error Tracking | In use by at least one monitor; no evidence of squad adoption |
| SLOs | At least one ("Master Services 90 day"), currently in `Warn` |
| Database Monitoring | DB spans present for ~30 services, but `DD_DBM_PROPAGATION_MODE` is not set anywhere, so this is APM client-side spans, not DBM |

---

# Phase 1 — Do now. Saves money, changes no Datadog cost.

## 2. Cut the Cloud Logging bill and fix the defects

Nothing in this section adds a byte to Datadog.

### 2.1 Non-production Cloud Logging — Rp 81–105M a month

| Action | Saving / month | Effort |
|---|---:|---|
| Exclusion filters + 7-day retention on `bravo-project-nonprod`, `bfi-devsecops`, `bfi-internal-app-nonprod`, `core-system-nonprod` | Rp 60–80M | 1 d |
| Turn off Cloud SQL audit and slow-query logs in non-prod | Rp 15–18M | 2 h |
| VPC flow log sampling to 10% | Rp 6–7M | 1 h |

Non-prod is **Rp 93.1M a month, 34% of the Cloud Logging bill**, on environments that serve
no customer. The Cloud SQL line in non-prod alone is three times what production's database
logs cost.

This is the largest confirmed saving in the entire analysis and it depends on nothing else.

### 2.2 Fix the monitors — a large family cannot fire

**Effort: 1–2 days. Cost: zero. This is a live alerting gap.**

**Defect A — monitors targeting environments that send no logs.** A family of at least 20
log monitors named `Error Queue Failed Declare Spring Boot For Apps <service>`, created
September 2023, target `dev-ms-*`, `sit-ms-*` and `uat-ms-*`:

```
logs("@logger.name:org.springframework.amqp.rabbit.listener.BlockingQueueConsumer
      status:warn failed service:dev-ms-employee").index("*").rollup("count").last("15m") > 10
```

No non-production logs reach Datadog. These can never fire. All report status `OK`.

**Defect B — production monitors querying service names that do not exist.** Worse, because
these are production. The monitor named `... For Apps prod-sharia-bpm-sharia` queries:

```
service:prod-sharia-sharia-bpm-sharia
```

Note the doubled `sharia-sharia`. The actual sharia services, verified:

```
prod-sharia-user-iam-sharia, prod-sharia-customer-sharia,
prod-sharia-agent-marketing-sharia, prod-sharia-agency-sharia
```

`prod-sharia-sharia-bpm-sharia` does not exist. The same doubling appears in the payment,
onboarding and agent-marketing monitors across prod, UAT and SIT.

**These monitors show `OK` because nothing matches, not because nothing is wrong.** A queue
declaration failure on sharia BPM today would alert nobody.

**Defect C — production alerts routed to test channels.** Live production monitors notify
`@googlechat-test` (LORA container OOM) and `@webhook-testwebhook` (LORA success rate,
repeat-order success rate, BFI Mobile log errors).

**Defect D — almost all monitors watch infrastructure.** The set is dominated by CPU, memory
and OOM alerts at a 94% threshold. There is **no monitor that watches a loan through the
system** — not submission rate, not approval throughput, not disbursement success, not stage
dwell time. This is why `prod-ms-cnv` failed 20,000 employee syncs a day unnoticed.

**What to do:**

1. Delete the dev/SIT/UAT monitor family.
2. Fix the doubled `sharia-sharia` names, or rebuild from the verified service list.
3. Replace `@googlechat-test` and `@webhook-testwebhook` with real squad channels.
4. Audit every monitor in `OK` with no data. An `OK` that has never evaluated true looks
   identical to a healthy one.
5. Ask each squad for one business monitor. Error Tracking alerts are the cheapest start and
   add no ingest cost — they derive from telemetry already flowing.

### 2.3 Pin the tracer version

**Effort: 1 hour. Cost: zero.**

23 Dockerfiles contain:

```dockerfile
wget -O dd-java-agent.jar 'https://github.com/DataDog/dd-trace-java/releases/latest/download/dd-java-agent.jar'
```

**`releases/latest`.** Every image build picks up whatever the newest tracer is. Two builds
of the same commit can ship different tracers, and a breaking tracer change arrives silently
on whichever service rebuilds first.

```dockerfile
ARG DD_TRACER_VERSION=1.42.2
RUN wget -O dd-java-agent.jar \
  "https://repo1.maven.org/maven2/com/datadoghq/dd-java-agent/${DD_TRACER_VERSION}/dd-java-agent-${DD_TRACER_VERSION}.jar"
```

Prefer Maven Central over GitHub releases — it is the supported channel and does not depend
on GitHub availability at build time.

### 2.4 Fix tagging and service identity

**Effort: 3 days. Cost: zero — this renames, it does not add volume.**

**Eight services have different names in logs and traces.** This is a bigger family than
the two named in the first version of this document — a full seven-day sweep found the rest.

| Logs | Traces | Owner |
|---|---|---|
| `confins-prod-ms-lms-ar-be` | `prod-ms-lms-ar-be` | CONFINS / AdIns |
| `confins-prod-ms-foundation-be` | `prod-ms-fou-foundation-be` | CONFINS / AdIns |
| `confins-prod-ms-ce-integration-be` | `prod-ms-ce-integration-be` | CONFINS / AdIns |
| `confins-prod-ms-los-be` | `prod-ms-los-be` | CONFINS / AdIns |
| `confins-prod-ms-mou-cwr-be` | `prod-ms-mou-cwr-be` | CONFINS / AdIns |
| `confins-prod-ms-lms-amendment-be` | `prod-ms-lms-amendment-be` | CONFINS / AdIns |
| `confins-prod-ms-lms-recovery-be` | `prod-ms-lms-recovery-be` | CONFINS / AdIns |
| `bau-prod-ms-user-iam` | `prod-ms-bau-user-iam` | Internal Service — [repo file](bravo-user-iam-service.md) |

Datadog treats each of these as two services. Logs and traces can never join, no service page
shows both, and every monitor covers half the picture. `confins-prod-ms-lms-ar-be` is also
our highest-volume logger.

Seven of the eight are CONFINS services from the vendor, running in the separate
`core-system-prod` GCP project. They have no repository under `squads/`, so the fix goes to
the vendor or to whoever owns that cluster's Helm charts. The eighth is ours.

**This mismatch also produced a wrong finding in the first version of §5.**
`prod-ms-lms-ar-be` and `prod-ms-fou-foundation-be` were listed there as services that trace
but send no logs. They do send logs — under their `confins-` names. Two of the twelve
"silent" services were never silent. The corrected coverage numbers are in §5.

### Why it happens

The service name on a **log** comes from the Kubernetes container and deployment name, or
from an Agent annotation. The service name on a **trace** comes from `DD_SERVICE`, or from
whatever the tracer was initialised with in code. Nothing reconciles them.

You can see the collision on the log events themselves. A single `confins-prod-ms-lms-ar-be`
entry carries **two `service` tags**:

```
service:confins-prod-ms-lms-ar-be     <- from the container and deployment name
service:prod-ms-lms-ar-be             <- from the kube_app_instance label
```

Datadog resolves one of them and discards the other.

**What to do:**

1. **Stop setting the name in two places.** Put the unified tagging labels on the pod
   template. The Agent then applies one identity to logs, traces, metrics and profiles
   together:

   ```yaml
   # deployment.yaml -> spec.template.metadata.labels
   tags.datadoghq.com/env: "prod"
   tags.datadoghq.com/service: "prod-ms-lms-ar-be"
   tags.datadoghq.com/version: "v3.1.12"
   ```

2. **Source the environment variables from those labels**, so the two can never drift again:

   ```yaml
   env:
     - name: DD_ENV
       valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
     - name: DD_SERVICE
       valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
     - name: DD_VERSION
       valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
   ```

   These labels already exist on some workloads — we found them on
   `sit-finance-shareholders` — so the pattern is established, just not applied everywhere.

3. **Keep the trace name, not the log name.** In every one of the eight, the trace name is
   the one that follows the `prod-ms-*` convention and carries far more history. Renaming the
   logs to match orphans nothing.

4. **Do it once, in the shared template.** 104 of the 152 repos deploy through
   `bfi-finance/bfi-base-template`, and 65 of those go through its `*-deploy-prod.yaml`
   workflows. One change there reaches most of the estate. The CONFINS services do not use
   it and need a separate conversation with the vendor.

5. **Retire `env:production` and `env:digital-prod`.** Pick `prod` and migrate. `env` should
   be a small closed set — `prod`, `uat`, `sit`, `dev` — with the product in the service
   name. `bfi-digital-web-api` currently reports under `env:digital-prod`, which excludes
   2.08M spans a week from every estate-wide `env:prod` view.

6. **Tell each squad to run the two-search check** in their repo file before you start, so
   the list is confirmed rather than assumed.

Do this in Phase 1 because it costs nothing and because Phase 3's per-service exclusion
filters need correct service names to work.

---

### 2.5 Answer the squads on request and response bodies

**Effort: 1 hour for the header tags, then however long the Remote Configuration fix takes.
Cost: none for this step.**

Squads have told us they cannot see request and response bodies in Datadog, and that this is
why they log them by hand — `lms-calculation-service` is the named example. **They are
right.** The estate-level view and the service-by-service index are in
[body-visibility.md](body-visibility.md); the findings themselves live in each service's own
file, under a section called *Request and response bodies in Datadog*.

The short version: no Datadog tracer, in any language, has a supported setting that puts an
HTTP body on a span, so no amount of configuration would have given them this. Fifteen squads
built their own version instead, and the two that have it switched on in production are the
two with no masking:

- `prod-ms-bpm` writes **487,146 request bodies and 471,241 response bodies a week**, at
  INFO, unmasked and untruncated — 44% of that service's entire log volume.
- `prod-inventory-management` runs a shared-library request logger plus `loggerLevel: full`,
  both defaulting to on, and writes six log lines per span recorded.

Two more that do not show up in logging numbers at all: `bravo-edoc-service` persists CONFINS
request and response payloads into a **database table** with no known owner or retention, and
`bfi-insurance-api` puts whole disbursement and customer payloads — bank accounts, NIK,
addresses — into dead-letter error messages, 90,553 times a week.

We are about to ask squads to remove body logging. **Do not make that ask without naming the
replacement in the same sentence**, or it will be resisted, correctly.

Two things to do in Phase 1, both free:

**a. Turn on header tags.** One environment variable, no code change:

```yaml
DD_TRACE_HEADER_TAGS: "x-request-id,x-correlation-id,x-b3-traceid,content-type,content-length"
```

Incoming headers land as `http.request.headers.*`, outgoing as `http.response.headers.*`.
This is not bodies. It is the correlation identifiers that let a developer tie a trace to a
record elsewhere, plus payload size. Never add `authorization`, `api-secret`, `cookie` or
`set-cookie`.

**b. Fix Remote Configuration. It is failing right now.** This was written up as a
30-minute check. It has since been measured, and the answer is worse than unverified:
thirteen production Java services are polling for Remote Configuration and getting an error
back.

```
[dd-remote-config] WARN datadog.remoteconfig.ConfigurationPoller - Failed to retrieve
remote configuration: unexpected response code Internal Server Error 500
rpc error: code = Unknown desc = empty targets meta in director local store
```

Roughly **91,000 failed polls in seven days**, led by `prod-ms-bfi-payment-api` (679 in two
days), `prod-ms-bfi-insurance-api` (579), `prod-ms-employee` (509), `prod-ms-insurance`
(497) and `prod-ms-payment` (477). `prod-ms-bpm` and `prod-inventory-management` — the two
services with body logging switched on — are both on the list.

`empty targets meta in director local store` means the Agent has no Remote Configuration
state to serve. In practice it is one of three things, and all three are ours to check:

1. Remote Configuration is not enabled on the Datadog org.
2. The API key the Agents use does not carry the Remote Configuration capability.
3. Remote Configuration is switched off in the Agent, or the Agent is below 7.49.0.

Until this is fixed, **nothing can be enabled from the Datadog UI** — not Live Debugger, not
remote tracer configuration, not remote sampling rates. It is also writing a steady stream
of billable error logs on thirteen services for no benefit.

Nothing in the org uses Live Debugger today: a 30-day search for `source:dd_debugger`
returns zero results. That is a consequence of this, not a separate fact.

**Do not enable Live Debugger yet.** It is a Phase 4 item because we do not know how Datadog
bills it — see §6a. Phase 1's job is to find out whether we *can*, and to tell the squads the
answer.

---

# Phase 2 — Squads cut log volume

This is [squads-guide.md](squads-guide.md). SRE's job here is to hold the gate and measure,
not to write code.

## 3. What SRE needs from Phase 2 before opening Phase 3

Two numbers, tracked weekly:

| Metric | Today | Gate to open Phase 3 |
|---|---:|---:|
| Production log entries per day | ~4.5M | **below 2.5M** |
| Share carrying `@logger.name` (parsed) | 6.4% | **above 80%** |

Query for the first:

```
SELECT DATE_TRUNC('day', timestamp) AS d, count(*) FROM logs GROUP BY DATE_TRUNC('day', timestamp)
-- filter: env:prod
```

Query for the second: the same count with filter `env:prod @logger.name:*`, over the total.

### Why these two gates and not a date

**The volume gate** protects the per-GB cost of everything in Phase 4. Halving the stream
halves the recurring price of ingestion, indexing and retention.

**The parsed-share gate** is the one people will want to skip, and it matters more. Datadog
exclusion filters, retention filters and index routing all work on **parsed attributes**.
While 93.6% of logs are raw text, a filter can only match message substrings — which is
fragile, and will silently drop things we wanted to keep. Configuring cost controls on an
unparsed stream is how you get a bill that does not fall and an incident where the evidence
was filtered out.

So: squads make logs parseable, then SRE can control cost precisely. Not before.

### The five services to chase first

Phase 2 is 64% done when these five are fixed. SRE should track them by name:

| Service | Owner | Fix | Doc |
|---|---|---|---|
| `confins-prod-ms-lms-ar-be` | **needs an owner** | Stop emitting blank lines | [logging-cost.md](logging-cost.md) §4.1 |
| `prod-lora-task` | LORA Core | Routine warnings to debug | [lora-task-service.md](lora-task-service.md) |
| `prod-ms-calculation` | Contract Collateral | Stop `JSON.stringify(error)` — **also a leaked secret** | [lms-calculation-service.md](lms-calculation-service.md) |
| `prod-ms-cnv` | Internal Service | Fix the HCIS sync failure | [bravo-cnv-service.md](bravo-cnv-service.md) |
| `prod-ms-bpm` | Scoring and Underwriting | Feign config, stack traces, ENGINE-09004 | [bravo-bpm-service.md](bravo-bpm-service.md) |

`confins-prod-ms-lms-ar-be` has no identified owner and is the single largest contributor at
29%. **Naming that owner is an SRE action, this week.**

---

# Phase 3 — Ingestion and correlation, once the gate is met

Each item here increases Datadog ingest. Each is worth it on a clean stream and wasteful on
a dirty one.

## 4. Log-to-trace correlation — the highest-value change

**Effort: 1–2 days. Cost: small increase on a clean stream, large on today's.**

### The finding

| Check | Result |
|---|---|
| Logs with `@dd.trace_id` across all of prod, 2 days | **0** |
| Logs containing the raw text `dd.trace_id` | 17,495 (0.19%) |
| Prod logs carrying `@logger.name` (parsed at all) | 573,961 of 9,029,261 = **6.4%** |

Nobody can click from a trace to its logs, or from an error log to its trace. We own the
feature and get none of it.

The tracer *is* injecting context — sampled lines contain `"dd.service":"prod-ms-bpm"`,
`"dd.env":"prod"`, `"dd.version":"v2.93.56"`. So `DD_LOGS_INJECTION` is on for at least some
services. The trace id is not landing as a parsed attribute.

### Root cause: log lines are split at 16 KB

This is the important discovery, and it explains the 93.6% unparsed rate.

The container runtime splits any stdout line over **16 KB** into separate chunks. Datadog
ingests them as unrelated entries. In `prod-ms-bpm`, 86% of entries carry no `@logger.name`,
and sampling them returns mid-sentence JSON fragments:

```
NTB","activityId":"Activity_PD_Model_Check_NTB","processDefinitionId":"NDF2W:129:...","dd.service":"prod-ms-bpm","dd.env":"prod","dd.version":"v2.93.56"}
```

That is the tail of one JSON log line. Its head — including the opening brace, the message
and the trace id — arrived as a separate entry. Neither is valid JSON, so neither parses,
so no attributes are extracted from either.

Large log lines are not just expensive. **They are actively destroying the log pipeline.**

### Why this waits for the gate

Partial-line reassembly fixes the symptom by rejoining the fragments. On today's stream that
means Datadog would faithfully rebuild `bravo-onboarding-service`'s 64 KB request bodies and
`lms-calculation-service`'s Axios dumps into **single large billable events** — and index
them.

We would be paying Datadog to reassemble the content that should never have been logged, at
a higher unit price than Cloud Logging charged to mangle it.

**Reassembly is the right fix applied after the payloads are gone, and a cost multiplier
applied before.**

### What to enable, after the gate

**a. Partial-line reassembly in the agent.** In the Helm values:

```yaml
datadog:
  logs:
    enabled: true
    containerCollectAll: true
  env:
    - name: DD_LOGS_CONFIG_AUTO_MULTI_LINE_DETECTION
      value: "true"
```

Note: do **not** raise `DD_LOGS_CONFIG_MAX_MESSAGE_SIZE_BYTES` at the same time. Leave the
default cap in place as a backstop. If a service is still producing lines large enough to
hit it, that is a Phase 2 failure for that service, and the cap is what tells you.

**b. Confirm `DD_LOGS_INJECTION=true` on every service**, set once in namespace defaults
rather than per deployment. This adds three small fields per line — negligible on a clean
stream.

**c. Check the log pipeline has a Trace Id remapper.** In
`Logs → Configuration → Pipelines`, the standard Java/Go pipelines should include a
**Trace Id Remapper** mapping `dd.trace_id` to the reserved attribute. Without it, JSON logs
with a flat `dd.trace_id` key still will not correlate.

**d. Set log exclusion filters per service, at the same time.** This is the cost control, and
it only works now that logs are parsed. Index `error` and `warn` in full; sample `info` at
10–20%; exclude `debug` entirely. Configure it in the same change as reassembly so ingest
never rises unguarded.

## 5. Close the trace and log coverage gap

**Effort: 5 days. Cost: increases span volume — see the note on KrakenD.**

Re-measured over a full seven days, and corrected. The first version of this document
used a two-day window and an incomplete APM service list.

| | Count |
|---|---:|
| Service names sending logs | 78 |
| Service names sending traces | 101 |
| Sending both, as Datadog sees them today | 52 |
| Sending both, after the eight name mismatches in §2.4 are fixed | **59** |
| Tracing but sending no logs | **42** |
| Logging but sending no traces | **18** |

Trace counts exclude the datastore child services the tracer generates automatically
(`*-postgres`, `*-redis`, `*-rabbitmq`, `*-http-client`), which are not separately deployed
workloads.

**The Bravo services that trace but send no logs are the ones to start with.** All of these
return zero log entries over seven days — not under their service name, and not under
`kube_deployment:` either:

| Service | Spans, 7 days | Repo file |
|---|---:|---|
| `prod-ms-agreement` | 7,424,485 | [bravo-agreement-service.md](bravo-agreement-service.md) |
| `prod-ms-document` | 5,831,475 | — |
| `prod-ms-branch` | 3,054,484 | [bravo-branch-service.md](bravo-branch-service.md) |
| `prod-ms-agent` | 3,013,188 | — |
| `prod-ms-master` | 2,639,121 | — |
| `prod-ms-asset-pricing` | 1,776,285 | — |
| `prod-ms-collateral` | 1,354,151 | — |
| `prod-ms-bravo-core-proxy` | 745,851 | [bravo-core-proxy-service.md](bravo-core-proxy-service.md) |
| `prod-ms-edoc` | 384,176 | [bravo-edoc-service.md](bravo-edoc-service.md) |
| `prod-ms-lms-gateway` | 292,481 | [bravo-lms-gateway.md](bravo-lms-gateway.md) |
| `prod-ms-approval-engine` | 27,699 | [bravo-approval-engine-service.md](bravo-approval-engine-service.md) |

`prod-ms-agreement` runs 7.4 million spans a week and has never sent a log line to Datadog.
If it fails at 02:00 there is a duration and a status code, and nothing else.

These are not quiet services. They are busy services whose logs stop at Cloud Logging and
Coralogix. That is also why the Cloud Logging bill and the Datadog bill do not describe the
same estate.

**Services that log but send no traces**, highest volume first:

- `prod-ms-krakend-gateway` — 1,293,001 entries, no traces. This is the **API gateway**;
  every request enters through it, so it is the highest-value place to have tracing and the
  most expensive. See the cost note below.
- `prod-lora-task` — 3,858,350 entries, 337,750 spans. Traced, but barely: this one is a
  coverage problem rather than an absence. See [lora-task-service.md](lora-task-service.md).
- The ten `confins-prod-ms-ce-batch-worker-*` jobs, `prod-robot-scrape`,
  `prod-ms-gold-service`, `prod-ms-backoffice-worker`, `prod-lora-cdc-foxx-service`,
  `prod-ares`, `prod-army`, `prod-pcms`, `bau-prod-ms-otrs-report`.

Enable log collection on the silent services **after** §2.1's exclusion filters exist, so
their volume lands inside a filter rather than outside one. Each affected repo file now
carries the check and the steps.

### Cost note, and how to control it

Tracing a gateway produces a span for **every request**. KrakenD is our highest-traffic
entry point, so this is the one item here with a genuinely large cost tail.

Do it anyway, but with sampling set from the start:

```yaml
DD_TRACE_SAMPLE_RATE: "0.1"          # 10% of traces retained
DD_TRACE_RATE_LIMIT: "100"           # spans/sec ceiling per instance
```

Then raise the rate on the specific endpoints that matter using trace retention filters,
rather than tracing everything at 100% and filtering after you have paid to ingest it.

Enable log collection on the 12 silent services **after** §4d's exclusion filters exist, so
their volume lands inside a filter rather than outside one.

---

# Phase 4 — Paid add-ons, one at a time

Each of these is a separately metered product. Enable one, measure a full week of billing,
then decide on the next. Do not batch them.

## 6. Products we already license but have switched off

| Setting | What it gives | Cost model | Recommendation |
|---|---|---|---|
| `DD_RUNTIME_METRICS_ENABLED=true` | JVM heap, GC, thread counts per service, correlated to traces | Custom metrics — watch the count | **First.** We already alert on `jvm.heap_memory` for ms-bpm; this makes it estate-wide. Enable on Java services only |
| `DD_DBM_PROPAGATION_MODE=full` | Links a slow trace to the actual SQL plan | Priced per database host | **Second, on the top 10 DB-heavy services only.** Not estate-wide |
| `DD_PROFILING_ENABLED=true` | Continuous CPU and allocation profiles | Priced per host | **Third, on `prod-ms-bpm` alone** to start. It is our heaviest JVM and has a standing heap alert |
| Error Tracking | Grouped, deduplicated, assignable errors | **Derived from existing telemetry** | **Actually do this in Phase 1** — no new ingest, and it would have caught `prod-ms-cnv` on day one |

Error Tracking is the exception in this table: it costs no additional ingest because it works
on errors already flowing. Move it forward.

## 6a. Live Debugger — the replacement for body logging

**Effort: 1 day once Remote Configuration works. Cost: unknown — confirm first.**

**Blocked today.** Remote Configuration is failing across thirteen production services
(§2.5b). Live Debugger cannot be switched on until that is fixed, so treat §2.5b as the
prerequisite for this whole section.

This is the feature that makes body logging unnecessary. A developer sets a probe on a line
of running production code from the Datadog UI, captures the variables in scope, and removes
it. No code change, no redeploy, nothing left running afterwards. On-demand beats always-on
for both cost and data protection.

It sits in Phase 4 for one reason: **we do not know what it costs.** Snapshots are delivered
as log events tagged `source:dd_debugger`, into a log index you create yourself. Datadog's
documentation does not state, in either direction, whether those count against log ingestion
and indexing or are included with APM. The mechanism says they are ordinary logs.

**Three questions for the account team before this is switched on in production:**

1. Does `source:dd_debugger` count against ingested GB and indexed events?
2. Is there any bundled allowance with our APM subscription?
3. Datadog's guidance is to create that index with no sampling. How does that interact with
   our commitment tier?

Volume is small by nature — one capture per second per probe, live only for the length of a
debugging session. But small is not free, and we do not have the rates.

**When it is approved, roll it out as a time-boxed pilot on one service**, with a named owner
per squad holding `live_debugger_write`. Set
`DD_DYNAMIC_INSTRUMENTATION_ENABLED=true` on that service only, add BFI-specific identifiers
to `DD_DYNAMIC_INSTRUMENTATION_REDACTED_IDENTIFIERS` (`nik`, `no_ktp`, `norek` — `secret`,
`password`, `token` and about sixty others are redacted by default), and trade it explicitly
against removing the body logging in that service.

The four limits that will otherwise make the pilot look like a failure — Node.js supports
line probes only, capture depth and field count are tight, strings truncate at 255
characters, and snapshots are rate limited to one per second — are set out in
[body-visibility.md §5.3](body-visibility.md). Read that before briefing any squad.

**Three services cannot have this at all.** `bravo-cnv-service`, `lora-task-service` and
`bravo-user-iam-service` instrument with OpenTelemetry, not the Datadog tracer, and under
OTel there is no probe mechanism. Between them that is **13.2 million spans a week**,
including the busiest service in the estate. `bravo-surveyor-console` is a browser
application and has no server-side tracer either; its answer is RUM. Say so before briefing
those squads, not after. See §7.

**Best pilot candidate: `bfi-payment-api`.** It captures nothing in production by design, so
it has the clearest unmet need and nothing to unwind; it is Java, so it gets method probes;
and it has the highest Remote Configuration failure count in the estate, so fixing §2.5b is
verifiable there first.

## 7. Pick one tracing stack

**Effort: a decision, then 1–2 sprints.**

| Stack | Repos |
|---|---:|
| OpenTelemetry in `go.mod` | 54 |
| `dd-trace-go` in `go.mod` | 35 |
| `dd-java-agent` in Dockerfile | 26 |

The Go estate carries both OpenTelemetry and the Datadog tracer. Datadog ingests OTLP, so
this can work — but instrumentation, context propagation and sampling behave differently
between the two, and a trace crossing from an OTel service to a dd-trace service can break
at the boundary. That is a plausible contributor to the 76,840 spans tagged `env:none`.

There is also a cost angle: two tracers on one service can produce duplicate spans, which we
pay for twice.

**There is a third cost, and it is new.** Datadog's Live Debugger only works through the
Datadog tracer. `bravo-cnv-service`, `lora-task-service` and `bravo-user-iam-service` all
have `go.opentelemetry.io/otel` as a direct dependency and `github.com/DataDog/dd-trace-go/v2`
only as an indirect one, so none of them can ever be given a probe. That is **13.2 million
spans a week**, including `prod-ms-cnv`, the busiest service in the estate.

**Recommendation:** standardise on OpenTelemetry SDK with OTLP export to the Datadog agent
for Go, keep `dd-java-agent` for Java, and remove `dd-trace-go` where OTel is already
present. Whichever way it goes, it needs to be one decision rather than 54.

**But make the decision with the Live Debugger consequence stated.** Choosing OTel for Go
means accepting that a third of the estate's span volume is permanently outside the
on-demand debugging story we are about to sell to the Java squads. That may still be the
right call — it is a portability argument against a tooling argument — but it should be
chosen, not discovered later.

## 8. Non-production telemetry in Datadog

**This is the item most likely to blow the budget, so it comes last.**

Today dev, SIT and UAT log only to Cloud Logging at Rp 93.1M a month. Sending that stream to
Datadog as-is would add a volume comparable to production.

Do not do that. Instead, once Phases 1–3 are done:

1. Send **SIT and UAT only** — not dev.
2. **Errors and warnings only**, via an agent-side exclusion filter, not a Datadog index
   filter. Filtering at the agent means we never pay to ingest the rest.
3. **3-day retention**, separate index from production.
4. Size it against the Phase 1 Cloud Logging reduction before switching on, and review after
   one full billing week.

SIT and UAT already send traces (13,291 and 1,904 spans), so the tagging is partly in place.

### Why bother at all

Because "we use Datadog" is not true for engineers if it only holds in production. A
developer debugging a SIT failure today has to go to Cloud Logging, which is the tool we are
moving away from. But this is a convenience improvement with a real recurring cost, and it
should be bought deliberately after the savings are banked — not bundled into the migration.

## 9. RUM and synthetics

**RUM — tidy first, expand later.** 55 applications are registered:

- At least 11 have `rum_event_processing_state: NONE` — registered but collecting nothing.
  **Delete them rather than finishing them**, unless a squad asks. Finishing them adds
  session cost.
- Test, SIT and UAT apps sit alongside production with no convention: `RO Tools-SIT`,
  `RO Tools-UAT`, `RO Tools-Prod`, `Surveyor Platform Test`, `test-ms-bfi-incentive-ui`,
  `sit-notary-ui`.
- `BFI PAS! (Inactive)` is named inactive but flagged `is_active: true`.
- `product_analytics_retention_state: NONE` on every app. Leave it off — it is a separate
  charge and nobody has asked for it.
- **`Synthetic Tests Default Application` was created by a personal Gmail address**
  (`lili.pertiwi93@gmail.com`). **Check whether that account still has org access.** That is
  an access review item for Phase 1, not a cost item.

Adopt one convention — `<product>-<env>` — and delete the dead applications. Tidying reduces
cost; expanding RUM increases it and can wait.

**Synthetics — 8 tests, all DNS or SSL.** Nothing tests whether a customer can submit a loan
application.

Synthetics are priced per test run, so cost scales with test count times frequency. Add
sparingly and deliberately:

1. **One API test per critical path** — application submit, document upload, disbursement
   trigger. Run every 5 minutes.
2. **One multistep API test** covering a full application through to approval. Run every
   15–30 minutes, not every minute.
3. **One browser test per customer-facing front end.** These are the expensive kind — one
   per product, hourly.

This is directly relevant to the finding that the Gherkin end-to-end suite is frozen and
cannot fail ([bravo-testing.md](../bravo-testing.md)). Synthetics give the production-facing
half of that coverage continuously, rather than in a weekly cron.

---

## 10. Ordered plan

| # | Phase | Action | Effort | Datadog cost | Saving / month |
|---|---|---|---|---|---:|
| 1 | 1 | Non-prod Cloud Logging filters and retention (§2.1) | 2 d | none | **Rp 81–105M** |
| 2 | 1 | Fix dead and misrouted monitors (§2.2) | 2 d | none | — |
| 3 | 1 | Pin the tracer version (§2.3) | 1 h | none | — |
| 4 | 1 | Unified tags, service-name mismatches, retire `env:production` (§2.4) | 3 d | none | — |
| 5 | 1 | Error Tracking rollout to squads (§6) | 2 d | none | — |
| 5a | 1 | Header tags on, and **fix Remote Configuration — failing on 13 services** (§2.5) | 1 d | none | — |
| 6 | 1 | Name an owner for `confins-prod-ms-lms-ar-be` (§3) | 1 d | none | — |
| 7 | 1 | RUM tidy-up and the Gmail access review (§9) | 2 d | reduces | — |
| 8 | 2 | **Squads cut log volume** — hold the gate, track weekly (§3) | 4–6 wks | reduces | feeds every item below |
| 9 | 3 | Reassembly + logs injection + trace remapper + per-service exclusion filters (§4) | 2 d | small, gated | — |
| 10 | 3 | Trace KrakenD then `prod-lora-task`, with sampling from day one (§5) | 3 d | moderate | — |
| 11 | 3 | Log collection on the silent traced services, `prod-ms-agreement` first (§5) | 3 d | moderate | — |
| 12 | 4 | Live Debugger pilot on `bfi-payment-api`, once billing is confirmed (§6a) | 1 d | **unknown — confirm** | — |
| 13 | 4 | Runtime metrics, then DBM on 10 services, then profiling on ms-bpm (§6) | 3 d | per product | — |
| 14 | 4 | Pick one tracing stack; remove duplicate tracers (§7) | decision | reduces | — |
| 15 | 4 | Real synthetic tests, added sparingly (§9) | 3 d | per run | — |
| 16 | 4 | SIT and UAT logs into Datadog, errors only, 3-day retention (§8) | 3 d | **largest increase** | — |

Phase 1 is about two weeks of work, banks the full **Rp 81–105M a month**, closes a live
alerting gap and adds no Datadog cost. Phase 2 is the squads' work and the gate. Nothing in
Phase 3 or 4 should start before the gate is met.

---

## What could not be checked

Stated plainly so nobody treats this audit as complete.

- **The Datadog agent configuration itself.** The Helm values and DaemonSet live in a GitOps
  repo we do not have. Everything in §4 is inferred from log content and needs confirming
  against the actual agent config.
- **Log indexes, exclusion filters and retention already in place.** Not exposed through the
  tooling available here. Check `Logs → Configuration → Indexes` before adding more — it is
  possible some filtering already exists and explains part of the 93.6% unparsed rate.
- **Our actual Datadog contract and unit rates.** The cost direction in this document is
  qualitative. Before Phase 3, get the per-GB ingest, per-million-events index and per-host
  add-on rates from the account team, and model the gate against real numbers. August
  Datadog spend was Rp 110.6M, which is the baseline to protect.
- **Whether DEBUG logs are dropped by Datadog or never emitted.** Zero `status:debug` entries
  exist across production. This is the open question from [logging-cost.md](logging-cost.md)
  §3, and it decides whether the Feign body-logging fix is worth Rp 0 or Rp 40M a month.
  Reading the ms-bpm deployment manifest settles it.
- **Monitor totals.** We confirmed the defect patterns in §2.2 by sampling roughly 45
  monitors. We did not enumerate every monitor in the org, so treat the counts as floors.
