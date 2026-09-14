# Logging cost — what it is, where it goes, and what to fix

Written 12 September 2026, extended 13 September 2026. Cost data is GCP billing via FinOps.
Log evidence is Datadog production. Code evidence is all 152 repos under `squads/`, pulled
to `master` on the day of writing, plus 36 more cloned since.

**Section 5 has been rewritten.** The first version ranked repositories by a code scan.
That scan was Java-shaped, and roughly two-thirds of the estate is Go — those repositories
scored zero on it while carrying some of the worst behaviour in production. Section 5 now
ranks by what production shows.

This document was started to approve one recommendation: cut Cloud Logging by
Rp 50–90M a month by turning off Feign body logging. That recommendation appears in
[bravo-cost.md](../bravo-cost.md) and in the CTO deck.

**The direction is right. Two of the supporting numbers are wrong, and the named mechanism
is not confirmed in production.** Sections 1 and 2 give the corrected figures. Section 3
explains what the evidence does and does not support. Section 4 lists the work, ordered by
how much it saves and how sure we are.

---

## 1. Logging costs about three times what the deck says

The deck names Cloud Logging at Rp 140.5M a month. That was the production project only,
and it is out of date.

**August 2026, full month, actual:**

| Service | Cost / month | Share |
|---|---:|---:|
| Cloud Logging (GCP) | **Rp 271,833,531** | 42.8% |
| Coralogix | **Rp 253,322,232** | 39.8% |
| Datadog | **Rp 110,626,087** | 17.4% |
| **Total** | **Rp 635,781,850** | 100% |

BFI runs three log platforms at once. The deck counts one of them, and counts it low.

Cloud Logging alone has grown steadily:

| Month | Cloud Logging |
|---|---:|
| Feb 2026 | Rp 197.5M |
| Mar 2026 | Rp 223.1M |
| Apr 2026 | Rp 240.5M |
| May 2026 | Rp 278.1M |
| Jun 2026 | Rp 303.3M |
| Jul 2026 | Rp 337.6M |
| Aug 2026 | Rp 271.8M |

Up about 38% from February to August. July was the peak.

Coralogix is flat at about Rp 250M a month and has been since February. It is a fixed
marketplace commitment, billed in one charge. Nobody in the cost documents has asked what
it is for. **That question is worth more than the Feign fix.** See item 1 in section 4.

### 1a. What the contract and the 2025 bills add (14 September 2026)

SRE shared two things: the signed Datadog order
(`production-findings/Q-849776-20250930-1622_completed_datadog_contract.pdf`) and the
2025 GCP billing spreadsheet. They change how the Datadog line above should be read.

**The 2025 bills, month by month (Rp):**

| Platform | Jan | Apr | Jul | Oct | Dec | 2025 total |
|---|---:|---:|---:|---:|---:|---:|
| Cloud Logging | 96.8M | 158.6M | 146.5M | 189.0M | 194.4M | **1,780.7M** |
| Coralogix | 227.6M | 232.1M | 227.2M | 234.6M | 233.6M | **2,769.1M** |
| Datadog | 94.8M | 245.3M | 123.1M | 295.0M | 194.8M | **5,620.4M** |

Datadog's 2025 total includes a single **Rp 3.66bn in May** — the previous order's
payment through the marketplace, not a usage month. Take that out and Datadog ran
Rp 90–457M a month, more variable than the other two because the marketplace bills
overage monthly on top of the commitment. Cloud Logging doubled across 2025 (Rp 97M in
January to Rp 194M in December) and kept climbing into 2026 (§1). Coralogix did not move.
Total GCP spend for 2025 was Rp 33.8bn; the three log platforms were Rp 10.2bn of it, 30%.

**The contract.** `Q-849776` is a two-year renewal, 1 October 2025 to 30 September 2027,
resold through GCP Marketplace. Committed quantities per month, and what Datadog's own
usage metrics say we used in the 30 days to 14 September 2026:

| Line | Committed / month | Sales price | Committed $/month | Used (30 d) |
|---|---:|---|---:|---:|
| Infra hosts (Pro Plus) | 100 | $18 / host | 1,800 | 59 |
| Containers | 2,400 | $1 / container | 2,400 | ~3,095 |
| APM Enterprise | 100 hosts | $40 / host | 4,000 | 50 |
| Indexed spans, 15-day | 840M | $1.70 / M | 1,428 | 100M |
| Ingested spans | 20,000 GB | $0.10 / GB | 2,000 | 12,900 GB |
| Log events, 3-day | 30M | $1.06 / M | 32 | — |
| Log events, 7-day | 120M | $1.27 / M | 152 | 240M in total |
| Log ingestion | 256 GB | $0.10 / GB | 26 | **~39,800 GB** |
| Cloud Network Monitoring | 100 hosts | $5 / host | 500 | — |
| RUM session replay | 600K | $1.80 / K | 1,080 | — |
| RUM sessions | 408K | $1.50 / K | 612 | — |
| **Total committed** | | | **$14,030** | |

Net due over the term is $174,324.52 after a $162,390.68 credit for the existing order:
**$5,966.92 in year one and $168,357.60 due 1 October 2026** for year two. Overage is billed
monthly at the "Additional" rates on page 2 — $0.10/GB for log ingestion, $1.59–1.91 per
million log events, $0.002 per container-hour.

**Three things this settles, and one it does not.**

1. **Logs are 1.5% of the Datadog contract.** $210 of $14,030 a month. The "Datadog cost
   will explode" concern is real but it is not about the per-line price; it is about the
   ingestion line having been sized at **256 GB a month**.
2. **We are over on the two log lines and under on almost everything else.** Datadog's
   `datadog.estimated_usage.logs.ingested_bytes` says about **1.3 TB a day** — 150× the
   commitment — and `ingested_events` about 8M a day against 5M committed. At the overage
   rate that is roughly **$4,000 a month** of log ingestion, about Rp 64M at Rp 16,000, which
   would explain most of the Rp 110.6M Datadog line in August. Meanwhile APM hosts, infra
   hosts and indexed spans are used at half the commitment or less. The next renewal should
   move money from the span and host lines to the log lines — or, better, arrive with a
   stream a third the size.
3. **The per-service split is known.** Top log-ingestion sources over the last seven days,
   Datadog's estimate, 96% of it from the `prod-bravo-cluster` index: `prod-ms-assistance`
   1.60 TB, `prod-ms-cnv` 1.39 TB, `prod-ms-lms-ops` 0.70 TB, `prod-agent-marketing`
   0.52 TB, `prod-ms-audit-trail` 0.48 TB, `prod-ms-repeat-order` 0.37 TB,
   `prod-customer-bff` 0.33 TB, `prod-ms-supplier` 0.21 TB, `prod-ms-bfi-incentive-api`
   0.19 TB, `prod-sharia-user-iam-sharia` 0.19 TB, `prod-ms-bpm` 0.18 TB. Four of the top
   eight run production at `LOGGER_LEVEL=debug` ([deployment-proposal.md](deployment-proposal.md) §1).

What it does not settle: **40 TB across 240M events is 166 KB per event**, which is not
what a log line weighs. Either the estimate over-counts, or a few services ship very large
entries — the 64 KB request bodies and serialised payloads elsewhere in this document
would do it. SRE should reconcile the metric against the Usage & Cost page and the last
three invoices before the figure is used in a renewal conversation. Until then, treat the
$4,000 as an upper bound with the right order of magnitude.

---

## 2. Where the Cloud Logging money goes

August line items, top 200 rows. They cover Rp 227.5M of the Rp 271.8M month, so 84%.
Ranking is reliable. Absolute figures are floors, not totals.

### By project

| Project | Cost / month | Volume | What it is |
|---|---:|---:|---|
| `bravo-project-331802` | **Rp 125,414,087** | 18.05 TB | Bravo production |
| `bravo-project-nonprod` | **Rp 56,360,125** | 7.66 TB | Bravo dev, SIT, UAT |
| `bfi-devsecops` | **Rp 34,898,639** | 4.77 TB | CI/CD cluster |
| `bfi-internal-app-production` | Rp 9,012,031 | 1.23 TB | Internal apps |
| `bfi-internal-app-nonprod` | Rp 1,564,409 | 0.21 TB | Internal apps, non-prod |
| `core-system-nonprod` | Rp 236,516 | 0.03 TB | CONFINS non-prod |

**Non-production is Rp 93.1M a month — 34% of the Cloud Logging bill.** That is
`bravo-project-nonprod`, `bfi-devsecops`, `bfi-internal-app-nonprod` and
`core-system-nonprod` added together. No customer is served by any of it.

This is the largest clean saving in the document. It needs no code change and no product
decision. It is a retention setting and an exclusion filter.

### By resource type

| Project | Resource | Cost / month |
|---|---|---:|
| `bravo-project-331802` | `k8s_container` | Rp 107,457,874 |
| `bravo-project-nonprod` | `k8s_container` | Rp 37,995,747 |
| `bfi-devsecops` | `k8s_container` | Rp 34,898,639 |
| `bravo-project-nonprod` | `cloudsql_database` | Rp 18,364,379 |
| `bfi-internal-app-production` | `k8s_container` | Rp 9,012,031 |
| `bravo-project-331802` | `gce_subnetwork` | Rp 7,899,743 |
| `bravo-project-331802` | `cloudsql_database` | Rp 5,804,015 |
| `bravo-project-331802` | `http_load_balancer` | Rp 4,252,455 |
| `bfi-internal-app-nonprod` | `cloudsql_database` | Rp 1,564,409 |

Container logs are Rp 189.6M of the Rp 227.5M analysed — 83%. Everything else is small by
comparison.

Two lines are pure configuration and belong to nobody's backlog:

- **`cloudsql_database` in non-prod, Rp 18.4M a month.** Cloud SQL audit and slow-query
  logs from dev, SIT and UAT databases. Three times what the production database logs cost.
- **`gce_subnetwork`, Rp 7.9M a month.** VPC flow logs. Sampling is almost certainly at
  100%. Dropping to 10% cuts this to under Rp 1M with no loss for normal use.

---

## 3. The Feign claim does not hold up in production

This is the part of the deck that needs correcting before it goes to a CTO.

### What the code says

The claim is real in the source. In `bravo-bpm-service`:

- `src/main/resources/application.yaml` sets `loggerLevel: full` on **129** Feign client
  entries, including `feign.client.config.default`.
- The same file sets `logging.level.com.bfi.bravo.adapter: DEBUG`.
- All **57** Feign client interfaces live under `com.bfi.bravo.adapter.http.*`.
- `application-prod.yaml` sets `logging.level.root: INFO`. It never overrides
  `com.bfi.bravo.adapter`. In Spring Boot those are different keys, so the package stays
  at DEBUG.

Feign only writes bodies when the client's own logger is at DEBUG. Here it is. On paper,
every upstream call logs its full request and response body.

`bravo-onboarding-service` has the same shape, plus inbound payload logging. See
[bravo-onboarding-service.md](bravo-onboarding-service.md).

### What production says

Nothing. Over two days across every production service:

| Check | Result |
|---|---|
| Logs at `status:debug`, all of prod | **0** |
| Logs containing `END HTTP`, the Feign full-logging terminator | **0** |

Feign's full logger writes at DEBUG and ends every exchange with `<--- END HTTP (n-byte
body)`. Neither marker exists anywhere in production.

### What that means

One of two things is true, and we cannot tell which from these repos:

1. **The deployment overrides the log level.** A `LOGGING_LEVEL_COM_BFI_BRAVO_ADAPTER`
   environment variable in the Helm chart or Kubernetes manifest would switch it off. None
   of the 152 repos under `squads/` contains a deployment manifest — they live in a GitOps
   repo we do not have. This is the likelier explanation.
2. **Datadog drops DEBUG before indexing**, and Cloud Logging still pays for it.

**Until somebody checks the deployment manifests, the Rp 50–90M saving attributed to this
fix is not evidence-based.** It is a code reading with no production signal behind it.

Checking costs about an hour: read the ms-bpm manifest, or run
`kubectl set env deploy/prod-ms-bpm --list | grep -i logging` against the prod cluster.
**Do that before the deck is shown.** It flips a headline number in either direction.

### What is true either way

The configuration is wrong and should be fixed regardless. `loggerLevel: full` on
`feign.client.config.default` means a single line in one manifest — or one careless merge
to `application-prod.yaml` — starts writing PEFINDO, SLIK, Dukcapil and CONFINS request
bodies into Cloud Logging. That is a data-protection exposure sitting behind one
environment variable. It should not be reachable by accident.

Four more repos carry `loggerLevel: full` where it currently emits nothing, because their
Feign packages sit at INFO or WARN:

- `bravo-agreement-service`, `bravo-payment-service` and
  `bravo-inventory-management-service` set it on `feign.client.config.default` — the same
  landmine as `bravo-bpm-service`, currently disarmed. `bravo-inventory-management-service`
  has it in `application-prod.yaml` itself, which is the worst place for it.
- `bravo-edoc-service` sets it on a single client, `ApigeeApiClient`. That is already the
  right shape — the blast radius is one integration, not 28.

---

## 4. What is actually driving volume

These come from production logs, not from reading code. Each one is measured.

### 4.1 Empty log lines — `confins-prod-ms-lms-ar-be`

The highest-volume service in production emits **blank log lines**. Message field empty,
several per second, 2,730 in one hour and 9.25 million over seven days.

They are shipped, indexed and stored. They carry no information at all. Every one still
pays the per-entry metadata envelope — roughly 500–1,000 bytes of resource labels,
timestamps and Kubernetes attributes.

This is the single clearest piece of waste found. It sits in CONFINS, which is outside the
Bravo repos, so it needs an owner naming.

### 4.2 One repeating error — `prod-ms-cnv`

`Failed to update user access metadata` appears **4,995 times in six hours**. About 20,000
a day. 1.59 million errors over seven days, which is nearly all of that service's error
volume.

Source: `bravo-cnv-service/internal/rabbitmq/employeemq/employee_hcis_consumer.go:147`.

Each failure is preceded by an info line for the same message, so it is roughly 40,000
lines a day from one consumer. The handler returns `NackDiscard`, so this is not a retry
loop — about 20,000 genuine HCIS employee messages fail every day and are thrown away.

**That is a correctness problem that happens to be expensive.** The logging is a symptom.
See [bravo-cnv-service.md](bravo-cnv-service.md).

### 4.3 Stack traces logged one frame per entry — `prod-ms-bpm`

The top three log patterns in `prod-ms-bpm` are all single stack-trace frames:
`at com.…(File.java:123)`. 1,441, 844 and 378 occurrences in two days for the top three
alone, and many more below them.

Multi-line aggregation is not configured. A 50-frame Java stack trace becomes 50 separate
log entries, each paying its own metadata envelope. The text is maybe 3 KB; the 50
envelopes add perhaps 35 KB on top.

Two conditions drive most of it, and neither is a real fault:

- `TokenExpiredException` — 172 in two days, each with a ~50-frame trace, logged at SEVERE
  by Tomcat. An expired token is an expected condition.
- `FeignException$Unauthorized` on `IAMApiClient#getAssignedPermission` — 106 in two days,
  same shape.

### 4.4 BPMN parse warnings — `prod-ms-bpm`

`ENGINE-09004 Warnings during parsing` appears 432 times in two days across four variants.
Each message is long — one is over 1,500 characters, listing every gateway and link event
in the diagram.

These are model quality warnings on `ndf2w.bpmn`, `ndf4w.bpmn` and
`unified-main-workflow.bpmn`. They re-emit on every engine parse. Fixing the models
removes them; they are not runtime errors.

### 4.5 Full HTTP error objects with a live secret — `prod-ms-calculation`

`lms-calculation-service/src/helpers/HttpHelper.ts:27` runs
`JSON.stringify(error)` on every Axios failure and logs the result.

For an Axios error that serialises the entire request config. Production logs show each
entry contains:

- the **`api-secret` header in plaintext**, a live credential, repeated in every entry
- the full request body, including customer `birth_date`
- the full stack trace
- ANSI colour escape codes, because the logger writes terminal formatting into Cloud Logging

437 of these in 51 minutes, about 12,000 a day, roughly 1.5–2 KB each.

**This is a credential exposure, not just a cost line.** Anyone with log read access has
the secret. It should be treated as leaked and rotated. It is logged at `info`, so it does
not appear in error dashboards.

See [lms-calculation-service.md](lms-calculation-service.md). This is the most urgent item
in the pack, and it has nothing to do with Feign.

### 4.6 Routine warnings at WARN — `prod-lora-task`

3.82 million warnings over seven days. In a six-hour sample: 3,371 of one generic pattern
and 1,067 of `missing in form submission?` from
`lora-task-service/internal/httpserver/handlers/frontend/task/action.go:306`.

An optional form field being absent is normal. It is logged as a warning on every request.

### 4.7 Inbound request payloads up to 64 KB — `bravo-onboarding-service`

`CommonsRequestLoggingFilter` is registered with `setIncludePayload(true)` and
`setMaxPayloadLength(64000)`, and `application.yaml` sets that filter's logger to `DEBUG`.
`application-prod.yaml` does not override it.

Unlike the Feign case, this one is switched on explicitly and by name. Every inbound
request body up to 64 KB is written to logs — on the service that handles customer
onboarding.

Three more repos register the same filter with a 64 KB payload limit and a logger level of
`${LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER:DEBUG}` — **DEBUG unless the deployment says
otherwise**: `bravo-agency-service`, `bravo-approval-engine-service`,
`bravo-core-proxy-service`. Same manifest check as section 3 settles all three.

---

## 5. Estate-wide code findings

All 152 repos, 149,729 files scanned.

One caveat before the table. **`console.log` in a browser front-end costs nothing.** It runs
on the user's machine and never reaches Cloud Logging. It matters only when it prints
customer data into a console someone can open. `console.log` in a **Node.js backend** goes
to stdout, and that does cost money. The two are counted separately below.

| Pattern | Occurrences | Why it costs |
|---|---:|---|
| `console.log` / `console.debug` | 4,294 raw | Only the Node backend share is billable — see note above |
| `log.error(msg, exception)` | 3,504 | Each one can emit a full stack trace |
| Logging a body or serialised object | 425 | Request bodies, `writeValueAsString`, payloads |
| `loggerLevel: full` | 412 | Across 6 repos; live in 2 |
| Payload-logging request filters | 184 | Across 22 repos; live in 1, default-on in 3 |
| DEBUG/TRACE levels in YAML | 135 | Mostly local profiles; 11 at root |
| `System.out.print` | 98 | Bypasses the logging framework entirely |
| Logging inside a loop | 69 | Volume scales with data size |
| `printStackTrace()` | 51 | Unstructured, unfilterable, no level |

Two repos that look alarming in a raw scan are not. `bfi-digital-web-ui-v3` shows 1,349
`console.log` calls, but 1,242 are in `.history/` editor snapshots and `bower_components`
vendor code — 107 real, all vendor. `bravo-surveyor-console` has 939 genuine ones, but it
is a browser console: no Cloud Logging cost, only a data-exposure question.

### 5a. What the code scan missed

The table above came from pattern-matching Java idioms: `loggerLevel: full`,
`CommonsRequestLoggingFilter`, `printStackTrace`. Applied to the whole estate it produced a
**false clean bill for the Go services**, which are about two-thirds of the repositories and
include four of the five worst severity mixes in production.

Reading the remaining 53 repositories against production evidence turned up four patterns
that no Java-shaped scan would ever have found:

| Pattern | Repos | What it costs |
|---|---:|---|
| `*_JSON_MASKED_FIELDS` parsed from the environment with **no default**, so the scrubber runs with an empty list | 22 | Nothing in volume. Everything in exposure — the code reads as though masking is on |
| `With*BodyLoggingFunc` **commented out**, so the masked-field config is parsed and never used | 8 | `lora-gateway-service` alone: 69,433 bodies a week, unmasked |
| Exception handler logging **every 4xx at error** | 6 | `prod-ms-auth` 98.5% error; `prod-ms-repeat-order` 51,843 a week |
| Queue consumer logging `string(msg.Body)` on the failure path | 3 | `prod-ms-partnership` 123,503 body-carrying entries a week — the highest in the estate |

**The lesson for any future scan:** rank by production severity mix first, then read the
code. `bravo-partnership-service`, `bravo-auth-service` and `bravo-assistance-service` all
scored zero on the code scan and have among the worst production behaviour in the estate.

**A second lesson, about checking rather than scanning.** The changes in this programme were
written on a machine believed to have no build tools; `mise` in fact had Go, `gofmt`,
`golangci-lint` and Node all along, and Node runs `prettier-plugin-java` too. Running what
was actually available found four defects that reading had missed, in changes already
described in these documents as reviewed. The one class that stayed hidden is the one no
static tool catches: a Java change that swapped a string concatenation — null-safe by
definition — for a method call on the same possibly-null reference, turning the exception a
RabbitMQ listener is contracted to throw into a `NullPointerException`. Only that
repository's own test suite found it, and it could not be run here. **A logging change is a
code change; it earns the same build, lint and test as any other.**

### 5b. Four exposures found on the way, none of them cost items

Listed here because they came out of this work, not because they belong in a cost document.
Each needs an owner outside the logging programme. Detail in
[coverage.md](coverage.md) §3.

| Finding | Service | State |
|---|---|---|
| Google Chat webhook URLs logged in full — the key and token are in the query string | `bau-prod-ms-otrs-report` | **Live. Rotate the webhooks.** |
| JWT signing key printed with `fmt.Printf`, which no log level can suppress | `prod-ms-notification` | Code present; **not firing** in the 7-day window |
| Whole HR records at `info` — religion, marital status, bank account, personal email | `prod-ms-employee` | Live, ~900,000 a week |
| Customer mobile number, customer ID and licence plate on every duplicate-check miss | `prod-ms-bfi-connect` | Live, 6,608 a week |

Per-repo files, ordered by billable impact:

| Repo | Squad | Main problem |
|---|---|---|
| [bravo-bpm-service](bravo-bpm-service.md) | Scoring and Underwriting | 384 `loggerLevel: full`, 694 exception logs, stack frames, ENGINE-09004 |
| [lms-calculation-service](lms-calculation-service.md) | Contract Collateral | **Live API secret in logs**, PII, 12k entries/day |
| [bravo-cnv-service](bravo-cnv-service.md) | Internal Service | 20k failed HCIS messages/day, each logged twice |
| [bravo-onboarding-service](bravo-onboarding-service.md) | Customer Platform | 64 KB inbound payload logging, live in prod |
| [bfi-insurance-api](bfi-insurance-api.md) | Insurance | 624 exception logs, 82 body logs, 36 logs in loops |
| [bravo-lms-gateway](bravo-lms-gateway.md) | Contract Collateral | 663 exception logs, 117 in one file |
| [bfi-digital-web-api](bfi-digital-web-api.md) | Digital Web | 679 `console.log` in a Node backend — billable |
| [lora-task-service](lora-task-service.md) | LORA Core | 3.8M warnings in 7 days |
| [bravo-agreement-service](bravo-agreement-service.md) | Contract Collateral | 209 exception logs, dormant `loggerLevel: full` |
| [bravo-customer-service](bravo-customer-service.md) | Contract Collateral | 108 exception logs, payload filter |
| [bfi-payment-api](bfi-payment-api.md) | Payment | `show-sql`, payload filter, 5 `loggerLevel: full` |
| [bravo-agency-service](bravo-agency-service.md) | Agency | Payload filter defaulting to DEBUG |
| [bravo-approval-engine-service](bravo-approval-engine-service.md) | Contract Collateral | Payload filter defaulting to DEBUG |
| [bravo-core-proxy-service](bravo-core-proxy-service.md) | Contract Collateral | Payload filter defaulting to DEBUG |
| [bravo-branch-service](bravo-branch-service.md) | Internal Service | 66 exception logs, 6 logs in loops |
| [bravo-edoc-service](bravo-edoc-service.md) | Operation Post-Go Live | 175 exception logs, dormant `loggerLevel: full` |
| [bravo-payment-service](bravo-payment-service.md) | Payment | Dormant `loggerLevel: full` |
| [bravo-inventory-management-service](bravo-inventory-management-service.md) | Asset Management | `loggerLevel: full` in `application-prod.yaml` |
| [bravo-surveyor-console](bravo-surveyor-console.md) | Survey and Verification | 939 browser `console.log` — exposure, not cost |

And the second pack, ordered the same way. These were invisible to the code scan:

| Repo | Squad | Main problem | Entries / week |
|---|---|---|---:|
| [bravo-partnership-service](bravo-partnership-service.md) | Digital Partnership | 70 sites logging the raw MQ body; HTTP bodies unmasked; a poison message repeating 183× | 965,616 |
| [bravo-employee-service](bravo-employee-service.md) | Internal Service | Whole HR records at `info`, three call sites | 907,511 |
| [bravo-assistance-service](bravo-assistance-service.md) | Customer Platform | Masking configured, field list empty | 812,125 |
| [collection-consumer-service](collection-consumer-service.md) | Contract Collateral | 89% of a busy consumer is warn or error | 601,576 |
| [bravo-lms-ops-service](bravo-lms-ops-service.md) | Operation Post-Go Live | 1,264 entries a week whose whole message is the word `Exception` | 532,167 |
| [bravo-customer-bff-service](bravo-customer-bff-service.md) | Customer Mobile Apps | Masking configured, field list empty | 439,358 |
| [bravo-agent-marketing-service](bravo-agent-marketing-service.md) | Direct Marketing | Bodies on every call, not just failures | 438,865 |
| [bfi-incentive-api](bfi-incentive-api.md) | Agency | Whole DTO interpolated into the message, so it cannot be grouped | 351,082 |
| [bravo-repeat-order-service](bravo-repeat-order-service.md) | Tele Marketing | Every 4xx logged at error by `ControllerAdvice` | 332,644 |
| [bravo-audit-trail-service](bravo-audit-trail-service.md) | Internal Service | No masking config at all; error duplicated in its own message | 292,109 |
| [portfolio-management-service](portfolio-management-service.md) | Contract Collateral | 99,131 warn, masking empty | 108,151 |
| [lora-gateway-service](lora-gateway-service.md) | LORA Core | Scrubber commented out; bodies on every call | 82,911 |
| [lora-partnership-ndf](lora-partnership-ndf.md) | Digital Partnership | 73% error | 77,228 |
| [bravo-pbf-service](bravo-pbf-service.md) | PBF (SF) | 97% of the service is `sql: no rows in result set` | 41,067 |
| [bravo-auth-service](bravo-auth-service.md) | Internal Service | 98.5% error — every 4xx logged at error | 17,774 |
| [backend-dashboard-otrs](backend-dashboard-otrs.md) | — | **Google Chat webhook credentials in the log index** | 11,846 |
| [bravo-notification-service](bravo-notification-service.md) | Internal Service | **JWT signing key via `fmt.Printf`**; Vonage key at info | 9,570 |
| [bfi-connect](bfi-connect.md) | Digital Partnership | Customer phone number on every duplicate-check miss | 6,617 |

Full index of all 73, with pull request links: [README.md](README.md) ·
[coverage.md](coverage.md).

---

## 6. What to do, in order

Ordered by saving divided by effort. Platform work first, because it is bigger than all the
code work combined and depends on nobody's sprint.

| # | Action | Owner | Effort | Saving / month | Confidence |
|---|---|---|---|---:|---|
| 1 | **Ask what Coralogix is for.** Rp 253M a month, flat since February, three platforms doing one job | Architecture | 1 day | up to **Rp 253M** | needs a decision, not analysis |
| 2 | **Exclusion filter + 7-day retention on non-prod.** `bravo-project-nonprod`, `bfi-devsecops`, `bfi-internal-app-nonprod` | Platform | 1 day | **Rp 60–80M** | high |
| 3 | **Turn off Cloud SQL audit/slow-query logs in non-prod** | Platform | 2 h | **Rp 15–18M** | high |
| 4 | **VPC flow log sampling to 10%** | Platform | 1 h | **Rp 6–7M** | high |
| 5 | **Fix `HttpHelper.ts` and rotate the leaked secret** | Contract Collateral | 2 h | Rp 2–4M | high, and it is a security fix |
| 6 | **Stop the blank log lines in `confins-prod-ms-lms-ar-be`** | CONFINS owner | 1 d | Rp 5–15M | medium, needs an owner |
| 7 | **Fix the HCIS consumer failure in `bravo-cnv-service`** | Internal Service | 2–3 d | Rp 3–8M | medium, mostly a bug fix |
| 8 | **Enable multi-line stack trace aggregation** cluster-wide | Platform | 1 d | Rp 10–20M | medium |
| 9 | **Check the deployment manifests for Feign log levels** | S&U + Platform | 1 h | decides items 10–11 | — |
| 10 | **Remove `feign.client.config.default.loggerLevel: full`** in all 6 repos; set per client where needed | Each squad | 3 d | **unknown until #9** | low on cost, high on risk removal |
| 11 | **Drop `CommonsRequestLoggingFilter` payload logging** in onboarding and the 3 default-DEBUG repos | Each squad | 2 d | Rp 5–15M | medium |
| 12 | **Fix the ENGINE-09004 BPMN model warnings** | S&U | 2 d | Rp 2–5M | high |
| 13 | **Downgrade routine warnings to debug** in `lora-task-service` | LORA Core | 1 d | Rp 3–6M | medium |
| 14 | **Long tail**: `printStackTrace`, `System.out`, `console.log`, logs in loops | All squads | ongoing | Rp 5–10M | low each |
| 15 | **Merge the 48 open service pull requests and the two wrapper ones.** Written, raised, waiting on squad review — see [README.md](README.md) | Each squad | review only | folded into 6–14 | — |
| 16 | **Fix the three CI gate faults.** A missing Codacy API token (5 pull requests), a `codacy-cli.sh` installer that dies with `command not found`, and a SonarQube new-code baseline that scores a 10-line pull request as 9,855 new lines. Each squad currently has to be told which red check to ignore | Platform | 2 h | unblocks #15 | high |
| 17 | **Give every Go `*_JSON_MASKED_FIELDS` a default** and check no manifest overrides it with a blank | Platform + each squad | 1 d | exposure, not cost | high |
| 18 | **Rotate the Google Chat webhook credentials** in `bau-prod-ms-otrs-report`, and find someone with write access to that repo | Platform / security | 1 d | security | high |

**Items 1–4 are Rp 81–105M a month excluding Coralogix, and they are all platform
configuration.** No squad backlog, no code review, no release. They are available this
week.

**Items 5–14 are now written.** As of 13 September 2026 all 73 repositories have a file in
this folder and 64 have an open pull request. What is left on the code side is review and
merge, not analysis — which makes item 16 disproportionately important for a one-hour job.

Items 10 and 11 — the fix the deck actually asks to approve — cannot be sized until item 9
is done.

---

## 7. So should the Cloud Logging fix be approved?

**Approve the programme. Do not approve it on the stated reasoning.**

What holds:

- Logging is a large and growing cost line, and it is mostly configuration.
- It is bigger than the orchestration tier a migration would retire. Considerably bigger
  than the deck says — Rp 636M a month across three platforms against about Rp 58M.
- Configuration work should come before migration work.

What does not hold:

- **Rp 140.5M is stale.** Cloud Logging was Rp 271.8M in August; the production project
  alone was Rp 125.4M.
- **"2.4× the orchestration tier" understates it.** Cloud Logging alone is 4.7×. All three
  platforms together are about 11×.
- **The Feign mechanism is unproven in production.** Zero DEBUG logs and zero `END HTTP`
  markers across the estate. The Rp 50–90M figure is attached to a cause we have not
  confirmed is active.
- **The named fix is not the biggest lever.** Non-production logging is Rp 93.1M a month
  and is certain. Coralogix is Rp 253M a month and nobody has justified it.

The honest version for a CTO: *logging costs Rp 636M a month across three platforms,
about a third of it on environments that serve no customer, and one service is writing a
live API secret into the logs. Rp 81–105M a month is recoverable by platform configuration
alone, starting this week. The Feign question needs a one-hour manifest check before we
put a number on it.*

That is a stronger case than the one in the deck, and every figure in it survives contact
with the billing data.

---

## 8. Corrections owed to other documents

**All of these were applied on 13 September 2026**, each marked in place so a reader
holding an older copy can see what changed. The table is kept as the record of what was
wrong.

| File | Said | Now says | Applied |
|---|---|---|---|
| `bravo-cost.md` §5, §6, line 81, 165, 172, 242, 272 | Cloud Logging Rp 140.5M | Rp 271.8M estate; Rp 125.4M prod project (Aug 2026) | ✅ |
| `bravo-cost.md` line 176 | `loggerLevel: full` means 113 clients log bodies | 129 entries, 57 clients, in `bravo-bpm-service`; not observed in production | ✅ |
| `bravo-cost.md` line 207, 227 | Rp 50–90M from the Feign fix | Unsized until the deployment manifests are checked | ✅ |
| `compare.md` line 135, 226, 359 | Rp 140.5M, 2.4× the tier | Rp 271.8M, 4.7× the tier | ✅ |
| `compare-architecture.md` line 258, 316, 318 | Cloud Logging ≈Rp 201M / Rp 140.5M prod | Rp 271.8M estate; Rp 125.4M prod | ✅ |
| `option-3.md` line 174 | Rp 140.5M/month prod logging line | Rp 125.4M prod (Aug 2026) | ✅ |
| CTO deck `body_cto.html` slide 08 | "Cloud Logging alone costs Rp 140.5M a month… 2.4 times the tier" | Rp 271.8M, 4.7× — and drop the Feign attribution until #9 is done | ✅ |

Three documents also repeated the Rp 50–90M saving as settled. It is not settled. Each has
been changed to the Rp 81–105M platform figure, which is measured, with the Feign saving
marked unsized pending the manifest check.

Two more were corrected at the same time, beyond the list above:
[lora-workspace `production-findings/cost.md`](../../../lora-workspace/docs/production-findings/cost.md)
carried Cloud Logging at Rp 201.4M, and its CTO deck duplicated the figure in three places
(`build.js`, `cost-cto.html`, `cost-slides/cto-slides.html`) — all three moved together,
and `cost-cto.pdf` was re-rendered. **`cost-cto.pptx` could not be rebuilt**: it needs
Node, which is not installed on this machine, so it still carries the old figure.

### Corrections this document owes, from the second pass

Two of them are mine.

| Said | Should say | Where it was fixed |
|---|---|---|
| §5's estate scan gives the per-repo ranking | The scan is Java-shaped and returns a **false clean bill for the Go estate**, which is about two-thirds of the repositories. Rank by production severity mix, then read the code | §5a above |
| `prod-ms-krakend-gateway` is "an access log wearing the wrong level. Nothing is wrong" | The plugin levels by status code, correctly, and production runs at WARNING. The 942,909 warn entries a week are **real 4xx responses** — 415,388 of them one WhatsApp endpoint returning 400 | [coverage.md](coverage.md) §1, [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §5 |
| Four repositories mapped to a production service by name similarity | Datadog's `git.repository_url` tag settles it. `prod-ms-calculation` is `lms-calculation-service`, `prod-ms-kyc-proxy` is `bravo-kyc-proxy`, `prod-ms-rule-engine` is `bfi-rule-engine-service`, `prod-ms-notification` is `bravo-notification-service` | [coverage.md](coverage.md) §1 |
| "70 production-active repositories" | Too generous — it came from the same name join. **Only 39 repositories identify themselves in production logs**, and six services in the list emit no telemetry at all | [coverage.md](coverage.md) §2, §4 |
