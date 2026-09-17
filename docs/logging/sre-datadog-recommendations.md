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
which 93.6% are unparsed** and a large share is measurable waste — unparsed bodies, repeated
errors, serialised payloads.

If we enable ingestion improvements against today's stream, we do not fix the problem. We
move it from Cloud Logging at Rp 271.8M a month to Datadog at Datadog prices, on top of the
Rp 110.6M we already spend there.

**What "Datadog prices" means, now that the contract is in hand (14 September 2026).** The
signed order `Q-849776` runs 1 October 2025 to 30 September 2027. Its committed quantities,
per month, against what Datadog's own `datadog.estimated_usage.*` metrics say we used in
the 30 days to 14 September:

| Line | Committed / month | Used, last 30 days | Overage rate |
|---|---:|---:|---|
| Infra hosts (Pro Plus) | 100 | 59 | $0.035 / host-hour |
| Containers | 2,400 | ~3,095 | $0.002 / container-hour |
| APM Enterprise hosts | 100 | 50 | $0.08 / host-hour |
| Indexed spans | 840M | 100M | $2.55 / M |
| Ingested spans | 20,000 GB | 12,900 GB | $0.10 / GB |
| **Log events indexed** (3-day + 7-day) | **150M** | **240M** | $1.59–1.91 / M |
| **Log ingestion** | **256 GB** | **~39,800 GB** | **$0.10 / GB** |
| Cloud Network Monitoring | 100 hosts | — | $0.012 / host-hour |
| RUM sessions + replay | 408K + 600K | — | $2.20–2.60 / K |

Two things follow. **Logs are 1.5% of what was bought** — $210 of the $14,030 committed a
month — and the log ingestion line was sized at 256 GB a month for an estate that Datadog
says is sending it about **1.3 TB a day**. If that metric is right, log ingestion overage is
roughly **$4,000 a month** (about Rp 64M at Rp 16,000), which would make it the largest
single overage on the account and most of the Rp 110.6M. The event line is also over
(240M against 150M) but that costs about $170 a month. The contract is meanwhile
*under*-used on APM hosts, infra hosts and indexed spans by half or more.

The metric needs one check before anyone acts on it: 40 TB across 240M events is 166 KB an
event, which is not what a log line weighs. Either the estimate over-counts, or a small
number of services are shipping very large entries (the 64 KB request bodies and serialised
payloads in this document would do it). **SRE should reconcile it against the Usage & Cost
page and the last three marketplace invoices before the next renewal conversation.**
Either way the shape of the argument is unchanged: the cheap way to stay inside this
contract is to send fewer, smaller lines, which is Phase 2.

The 2025 billing sheet SRE shared says the same thing from the other side. Datadog cost
Rp 5.62bn in 2025 through the GCP marketplace — Rp 3.66bn of it in May, the prior order's
payment — and Rp 90–457M a month otherwise, against Cloud Logging at Rp 1.78bn for the year
(Rp 97M in January rising to Rp 194M in December) and Coralogix flat at Rp 2.77bn. Year 2 of
the current order is a single $168,357.60 payment due 1 October 2026.

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
| `confins-prod-ms-lms-ar-be` | 2,640,747 | 29% | **Full HTTP bodies, ~90% re-ingested at rollouts** — see [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md) (corrected 14 Sep) |
| `prod-lora-task` | 1,291,274 | 14% | Routine conditions logged at `warn` |
| `prod-ms-calculation` | 770,394 | 9% | Axios config dumps, one per 4xx |
| `prod-ms-cnv` | 752,562 | 8% | The same error 20,000 times a day |
| `prod-ms-bpm` | 387,332 | 4% | Split JSON fragments, stack frames |
| **Top five** | **5,842,309** | **64%** | |

None of that is telemetry anyone reads. Removing it roughly halves the stream before we ask
Datadog to ingest it properly — so every per-GB item in Phase 3 costs about half as much,
permanently.

**Corrected 14 September 2026.** The first row is not a squad item and not a vendor item.
The entries are request and response bodies with no `message` key, and the two-day count
includes a one-hour burst in which a newly scheduled pod re-read sixteen log files left on
its node by dead pods, with application timestamps from August. The same happens across the
CONFINS family (`foundation-be`, `ce-camunda-external-task-client`, `lms-amendment-be`, the
`ce-batch-worker-*` jobs). It is a Datadog Agent file-tailing configuration on the
`core-system-prod` cluster, and it is SRE's to fix — §3 below and [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md).

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
| `confins-prod-ms-lms-ar-be` | **SRE** — collection defect; the traffic is Contract Collateral's core-proxy | Stop shared-path file tailing, purge stale files, index exclusion meanwhile | [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md) |
| `prod-lora-task` | LORA Core | Routine warnings to debug | [lora-task-service.md](lora-task-service.md) |
| `prod-ms-calculation` | Contract Collateral | Stop `JSON.stringify(error)` — **also a leaked secret** | [lms-calculation-service.md](lms-calculation-service.md) |
| `prod-ms-cnv` | Internal Service | Fix the HCIS sync failure | [bravo-cnv-service.md](bravo-cnv-service.md) |
| `prod-ms-bpm` | Scoring and Underwriting | Feign config, stack traces, ENGINE-09004 | [bravo-bpm-service.md](bravo-bpm-service.md) |

**Corrected 14 September 2026.** This paragraph used to say the service "has no identified
owner" and that naming one was the SRE action. The owner question is moot for the volume:
about 90% of it is the Datadog Agent re-reading dead pods' files from a shared `/var/log` on
every rollout, and pods on one node indexing each other's lines. That is SRE's configuration
on `prod-core-system-cluster`. The image is built in BFI's own `bfi-devsecops` registry; the
vendor is AdIns; the bodies themselves are a data-handling question for whoever owns the
CONFINS contract. Evidence and the fix in [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md).

### 3a. Phase 2 is written and raised — four things now belong to SRE

As of 13 September 2026 the code half of Phase 2 exists: **73 repositories analysed, 64
pull requests open**, each with a file in this folder naming the finding, the branch and
the change. Squads have to review and merge them. Four things that came out of it are
SRE's, not theirs.

**1. Shared-workflow gates account for 26 of the 27 red jobs, and none of them is a code
problem.** Every failing job across the 44 pack-two pull requests was fetched and read
individually — 27 red jobs across 19 repositories:

| Cause | Jobs |
|---|---:|
| Dependency CVEs (SNYK) and base-image CVEs (Trivy — `musl`, `zlib`) | 17 |
| `CodacyCoverageReporter` has no API token | 5 |
| SonarQube quality gate on new-code coverage | 1 |
| Codacy CLI installer itself broken — `codacy-cli.sh: line 65: fatal: command not found` | 1 |
| `goconst` finding that predates the branch | 1 |
| Prettier violations that predate the branch | 1 |
| A real test failure in the change (fixed) | 1 |

The Codacy token error reads:

```
error [CodacyCoverageReporter] Invalid configuration: Either a project or account
API token must be provided or available in an environment variable
```

**An earlier version of this section said that error explained 23 of the pull requests.**
It was checked on three repositories and generalised; reading all 27 logs brings it down to
five. The correction matters in both directions — it is a smaller job than described, and
one of the pull requests it was said to excuse actually had a defect in it.

Three separate Platform items fall out of this:

- **The Codacy project token is absent** for these runs on at least five repositories.
- **The Codacy CLI installer is broken** on `bravo-employee-service` — the job dies inside
  `codacy-cli.sh`, before any analysis runs, so no token would help.
- **The SonarQube new-code baseline is wrong somewhere.** `bravo-insurance-service`'s quality
  gate reports **9,855 "new lines"** against a limit of 2,000 for a pull request that changes
  **+10/−4 lines in one file**. Any squad opening a small pull request against that project
  will fail the gate on somebody else's code.

Until these are fixed, every squad reviewing one of these pull requests sees a red check and
has to be told which red to ignore — and being told to ignore red is exactly how a real
failure gets missed. **Fix the gates, or the merge rate for Phase 2 will be whatever each
squad's patience allows.**

**2. Six production services emit no telemetry at all.** No logs, no APM spans, over a full
7-day window: `prod-ms-asset-pricing`, `prod-ms-document`, `prod-ms-master`,
`prod-ms-collateral`, `prod-ms-journal`, `prod-ms-data-admin`. Add
`prod-ms-krakend-internal`, `prod-ms-kyc-sign`, `prod-doc-renderer` and
`prod-ms-document-hub` to the same list.

Either they are not running under those names, or they are running and nobody can see them.
A service nobody can observe is a worse problem than a noisy one, and no amount of squad
cleanup will surface it — this needs someone to check the deployments.

**3. Three services log but produce no APM spans at all**: `prod-ms-product`,
`prod-ms-kyc-proxy`, `prod-ms-rule-engine`. They are running untraced. That is a smaller
version of the same problem and belongs in §5's coverage work.

**5. The deployment manifests are where most of the remaining logging settings live — and
eight production services run at `debug`.** SRE gave access to `app-deployment` and
`bfi-app-deployment` on 14 September 2026 (`confins-app-deployment` was not reachable).
Every `values-prod.yaml` for the 65 repositories in this programme has been read; what each
one sets is in that service's file under *In the production deployment*, and the changes are
written out as diffs in [deployment-proposal.md](deployment-proposal.md) and raised as
[app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on `fix/logging` — **not merged**.
The five findings that matter:

- **`LOGGER_LEVEL=debug` in production** on `audit-trail`, `gen-ai`,
  `partnership-provisioning`, `robot-controller`, `supplier`, `doc-renderer`,
  `gold-service` and `portfolio-management-service`; `POSTGRES_LOG_LEVEL=debug` on the
  last two; `LOG_LEVEL=DEBUG` on `robot-scrape`. Between them the eight Go services put
  0.9 TB into Datadog in the last seven days. One line each.
- **Body logging on with every masked-field list set to `""`** on `lora-gateway`,
  `doc-renderer`, `partnership-provisioning` (HTTP) and `integrity`, `pbf` (gRPC). SRE's
  reading is that `lora-schema` and `database-catalog`, which are in the same state, carry
  no PII. The proposal gives the five a list — backoffice's, the closest thing to an agreed
  BFI list — for the squads to trim.
- **Every body, not only failures**, on `doc-renderer`, `portfolio-management-service` and
  `database-catalog` (`HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY=false`).
- **`bpm` runs a hand-written Feign body logger at INFO.** `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG=true`
  in `bpm/values-prod.yaml` replaces Feign's DEBUG logger with `CustomFeignLogger`, which
  writes every request and response body unmasked and uncapped — 89% of the service's log
  bytes, about 22 GB a day, the largest single log producer in Bravo. The sharia deployment
  additionally logs headers *including `Authorization`* (`…SHOW_HEADER_AUTH=true`), though it
  wrote ten lines in the last day. The code fix is
  [bravo-bpm-service#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463);
  the manifest switch is the fallback — [deployment-proposal.md](deployment-proposal.md) §5.
- **Java defaults.** `bravo-lib-logging` defaults `REQUEST_BODY_LOGGING` and
  `RESPONSE_BODY_LOGGING` to `true`. Of 18 repositories on it, four set `SENSITIVE_KEYS` in
  production and four turn response bodies off; the rest log both bodies of every request at
  INFO because nobody set the switch. `bravo-onboarding-service` — 64 KB request bodies —
  is the one the proposal touches. **From 16 September Java is one layer again:** `bfi-logging-spring-boot-starter`
  ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged that day — 8 KB message
  cap, request logging off, Feign bodies opt-in and never headers) is the library every Java
  service moves to. The 19 repositories on Boot 3.3 or newer can take it as soon as Platform
  publishes it (the *Deploy Package* workflow is manual and has not run for the new modules);
  `bravo-insurance-service` leaves 3.2.11 first. The 14 Boot 2.7 repositories cannot take it,
  and the library-level fix for `bravo-lib-logging` ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123))
  was closed with #122's merge, so for them the per-service pull request and the manifest
  switches are the fix until they upgrade. Manifest trap for SRE: the starter
  reads `LOG_LEVEL` and `LOG_SENSITIVE_KEYS`, not `LOGGER_LEVEL` and `SENSITIVE_KEYS`.

Two side findings from the same read: `bravo-scheduling-service` and
`bfi-rule-engine-service` read their HTTP client timeouts from `HTTPCLIENT_*` while
production sets `HTTP_CLIENT_*`, so those timeouts have never been applied; and both
`notification-service` and `bravo-notification-service` map to the same
`app-deployment/notification` directory, which the per-service files now say.

**6. Service-to-repository mapping should come from Datadog, not from name similarity.**
Four repositories in the original coverage list were mapped to the wrong service. The
`git.repository_url` tag settles it in one query:

```
SELECT "git.repository_url", count(*) FROM logs WHERE "git.repository_url" IS NOT NULL
GROUP BY "git.repository_url" ORDER BY count(*) DESC
-- filter: env:prod
```

**Only 39 repositories answer it.** Every Go service carries the tag; almost no Java service
does. Getting source-code integration onto the Java services is cheap, and it makes every
future question of the form "which repo is this service?" answerable without guessing.

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

For Java there is now a wrapper-level answer: `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September, awaiting its first publish)
caps every message at 8 KB and every stack trace at 8 KB / 20 frames at the encoder, so a
service that adopts it cannot emit a line the runtime has to split. The reassembly work
below is still needed for Go, Node.js and the Java services that have not moved yet.

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

  **Do not treat its volume as noise.** An earlier draft of the coverage document called
  this an access log at the wrong level. That was wrong. The `server-observer` plugin maps
  5xx to error, 4xx to warn and 2xx to info deliberately, and production runs at
  `LOGGER_LEVEL=WARNING`, which is why there is no info. Every one of the 942,909 warn
  entries a week is a **real 4xx response**: 415,388 of them a single WhatsApp notification
  endpoint returning 400, 67,369 an email endpoint returning 500, and 6,507 a bank autodebit
  callback hitting a route that does not exist. The gateway is the only thing in the estate
  reporting those. Tracing it will make them easier to act on; filtering them would destroy
  the evidence.
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

It sits in Phase 4 for one reason: **we do not know how it is billed.** Snapshots are
delivered as log events tagged `source:dd_debugger`, into a log index you create yourself.
Datadog's documentation does not state, in either direction, whether those count against log
ingestion and indexing or are included with APM. The mechanism says they are ordinary logs —
and our contract (`Q-849776`, §0) has no Live Debugger line, so ordinary logs would land on
the two lines we are already over: ingestion at $0.10/GB and indexed events at $1.59–1.91 per
million in overage.

**Two questions for the account team before this is switched on in production:**

1. Does `source:dd_debugger` count against ingested GB and indexed events, or is there a
   bundled allowance with APM Enterprise?
2. Datadog's guidance is to create that index with no sampling. How does that interact with
   our commitment tier?

Volume is small by nature — one capture per second per probe, live only for the length of a
debugging session. At the overage rates above a pilot would cost dollars, not thousands; the
question is only whether it is billed at all.

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
| 6 | 1 | **Fix CONFINS log re-ingestion** — stop shared-path file tailing, purge stale `*.json` on the core-system nodes, index exclusion meanwhile (§3, [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md)) | 1 d | **reduces** — about a third of indexed prod log events | most of the log-event overage |
| 7 | 1 | RUM tidy-up and the Gmail access review (§9) | 2 d | reduces | — |
| 7a | 1 | **Fix the three CI gate faults** — the missing Codacy project token (5 pull requests), the broken `codacy-cli.sh` installer on `bravo-employee-service`, and the SonarQube new-code baseline that scores a 10-line pull request as 9,855 new lines on `bravo-insurance-service` (§3a) | 2 h | none | unblocks Phase 2 |
| 7b | 1 | **Rotate the Google Chat webhook credentials** logged by `bau-prod-ms-otrs-report`, and find an owner with write access to that repo (§3a, [backend-dashboard-otrs.md](backend-dashboard-otrs.md)) | 1 d | none | security |
| 7c | 1 | Establish why six production services emit no logs and no spans at all (§3a) | 2 d | none | — |
| 7d | 1 | Datadog source-code integration on the Java services, so `git.repository_url` answers "which repo is this?" (§3a) | 2 d | none | — |
| 7e | 1 | **Apply [deployment-proposal.md](deployment-proposal.md)** — nine services off `debug`, five given a masked-field list, three to failure-only bodies, onboarding's request bodies off (§3a item 5) | 2 h | reduces | volume and exposure |
| 7f | 1 | **Reconcile Datadog's log-ingestion estimate (≈1.3 TB/day) against the Usage & Cost page and the invoices** — if it is right, log ingestion is ~150× the 256 GB/month commitment and about $4,000/month in overage (§0) | 2 h | none | sizes the next renewal |
| 7g | 2 | **Publish the merged Java starter and merge the Go wrapper fix.** [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) merged on 16 September but nothing can depend on it until the manual *Deploy Package* workflow is run for `logging-core` and then `logging-starter` (last run 30 January 2026). [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) (mask non-string values) is still open. [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123), the `bravo-lib-logging` fix, was closed on 16 September — the 14 Boot 2.7 repositories keep their per-service fixes and manifest switches until they upgrade | 1 h + 1 d | none | closes the masking gap for every Java service on Boot 3.3+, and the Go one |
| 8 | 2 | **Squads cut log volume** — hold the gate, track weekly (§3). 47 pull requests are open and waiting on squad review, one is merged (§3a) | 4–6 wks | reduces | feeds every item below |
| 9 | 3 | Reassembly + logs injection + trace remapper + per-service exclusion filters (§4) | 2 d | small, gated | — |
| 10 | 3 | Trace KrakenD then `prod-lora-task`, with sampling from day one (§5) | 3 d | moderate | — |
| 11 | 3 | Log collection on the silent traced services, `prod-ms-agreement` first (§5) | 3 d | moderate | — |
| 12 | 4 | Live Debugger pilot on `bfi-payment-api`, once billing is confirmed (§6a) | 1 d | **unknown — confirm** | — |
| 13 | 4 | Runtime metrics, then DBM on 10 services, then profiling on ms-bpm (§6) | 3 d | per product | — |
| 14 | 4 | Pick one tracing stack; remove duplicate tracers (§7) | decision | reduces | — |
| 15 | 4 | Real synthetic tests, added sparingly (§9) | 3 d | per run | — |
| 16 | 4 | SIT and UAT logs into Datadog, errors only, 3-day retention (§8) | 3 d | **largest increase** | — |

Phase 1 is about two weeks of work, banks the full **Rp 81–105M a month**, closes a live
alerting gap and adds no Datadog cost. Phase 2 is the squads' work and the gate — the code
for it is written and raised, so what is left is review and merge, not analysis. Nothing in
Phase 3 or 4 should start before the gate is met.

**Items 7a and 7b did not exist when this plan was first written.** They came out of
implementing Phase 2 and both are SRE's. 7b is a live credential exposure and should not
queue behind the rest of Phase 1.

---

## What could not be checked — and what has been since

Stated plainly so nobody treats this audit as complete. Two of the four were closed on
14 September 2026, when SRE opened the deployment repos, the contract and the billing sheet;
two are narrower than they were but still open.

- **The Datadog agent configuration itself.** Still open. `app-deployment` and
  `bfi-app-deployment` hold the application charts — a per-container
  `ad.datadoghq.com/<name>.logs` annotation in 105 production values files, unified-tag
  labels in exactly one — but not the agent's own Helm values or DaemonSet. Everything in §4
  about the agent is still inferred from log content; whoever owns the agent chart needs to
  confirm it. (`confins-app-deployment` returns 404 to the token used here.)
- **Log indexes, exclusion filters and retention already in place.** Still open, and more
  pointed than before: Datadog's own ingestion metric and its indexed bytes disagree by about
  3× for `prod-ms-bpm` and about 40× for `prod-ms-assistance`. That is the shape of a
  per-service exclusion filter. Check `Logs → Configuration → Indexes` before adding more.
- **Our actual Datadog contract and unit rates.** Closed. §0 has the order, the unit rates
  and the usage against them; the gate in §3 is modelled against those numbers.
- **Whether DEBUG logs are dropped by Datadog or never emitted.** Closed for the service it
  was asked about: `bpm/values-prod.yaml` turns on a custom Feign logger that writes at INFO,
  so no DEBUG line was ever emitted there — the bodies are in Datadog at INFO, 89% of the
  service's log bytes, worth about Rp 5–8M a month rather than Rp 0–40M
  ([logging-cost.md](logging-cost.md) §3). Estate-wide there are still zero `status:debug`
  entries in seven days, and one manifest does put a Java package at DEBUG in production
  (`customer`, its CONFINS client) with nothing indexed from it — which folds into the
  exclusion-filter check above.
- **Monitor totals.** We confirmed the defect patterns in §2.2 by sampling roughly 45
  monitors. We did not enumerate every monitor in the org, so treat the counts as floors.
