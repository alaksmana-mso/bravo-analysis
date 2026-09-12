# Logging analysis

Written 12 September 2026.

Cost data is GCP billing through FinOps. Log evidence is Datadog production. Code evidence
is all 152 repos under `squads/`, pulled to `master` on the day of writing — 149,729 files
scanned.

## Start here

**[logging-cost.md](logging-cost.md)** — what logging costs, where the money goes, what the
evidence supports, and the ordered work list.

**For the CTO:** [bravo-logging-deck.html](../decks/bravo-logging-deck.html) —
11 slides, also rendered to [PDF](../decks/pdf/bravo-logging-deck.pdf). The correction is on
slides 3–5, the plan on 9–11.

The short version:

- Logging costs **Rp 636M a month** across three platforms, not the Rp 140.5M in the CTO
  deck. Cloud Logging is Rp 271.8M, Coralogix Rp 253.3M, Datadog Rp 110.6M.
- **A third of the Cloud Logging bill is non-production.** Rp 93.1M a month on environments
  that serve no customer.
- **The Feign mechanism the deck names is not confirmed in production.** Zero DEBUG logs
  and zero `END HTTP` markers estate-wide. A one-hour manifest check settles it.
- **Rp 81–105M a month is recoverable by platform configuration alone**, with no code
  change and no squad backlog.
- One service is writing a **live API secret** into production logs.
- **Log lines over 16 KB are split by the container runtime**, which is why 93.6% of
  production logs are unparseable — and why big payload logging corrupts the pipeline as
  well as costing money.
- A family of Datadog monitors **queries service names that do not exist**, so they report
  `OK` and can never fire.

## Moving to Datadog

BFI is standardising on Datadog for logs, traces and metrics. Two documents cover that:

- **[squads-guide.md](squads-guide.md)** — what to log and what not to, which Datadog
  feature answers which question, and where to find it. For every squad.
- **[sre-datadog-recommendations.md](sre-datadog-recommendations.md)** — a configuration
  audit of our Datadog org across all environments, and what SRE should change.

**The sequencing matters, and it is about cost.** Squad log cleanup comes first; SRE
enablement comes second, gated on two numbers:

| Metric | Today | Gate |
|---|---:|---:|
| Production log lines per day | ~4.5M | **below 2.5M** |
| Share Datadog can parse | 6.4% | **above 80%** |

Datadog bills on what we send it. Enabling better log ingestion against today's stream —
93.6% unparsed, 64% of it from five services emitting blank lines and repeated errors —
would move the waste from Cloud Logging to Datadog and cost more. Clean first, then enable
on a stream half the size.

The one exception is Error Tracking, which derives from telemetry already flowing and adds
no ingest. Turn that on now.

## Do these first

| # | Action | Owner | Effort | Datadog cost |
|---|---|---|---|---|
| 1 | Fix `HttpHelper.ts` and rotate the leaked secret | Contract Collateral | 2 h | none |
| 2 | Check prod deployment manifests for `LOGGING_LEVEL_*` overrides | Platform | 1 h | none |
| 3 | Exclusion filter and 7-day retention on non-prod projects | Platform | 1 d | none |
| 4 | Fix the monitors that query service names that do not exist | SRE | 2 d | none |
| 5 | Name an owner for `confins-prod-ms-lms-ar-be` — 29% of all log volume | SRE | 1 d | none |
| 6 | Ask what Coralogix is for | Architecture | 1 d | none |

None of these increases Datadog spend. Items 1 and 2 are an afternoon between them, and
item 2 decides whether several of the per-repo files below are worth anything.

## Per-repo recommendations

Ordered by billable impact.

| Repo | Squad | Main problem |
|---|---|---|
| [bravo-bpm-service](bravo-bpm-service.md) | Scoring and Underwriting | 384 `loggerLevel: full`, stack frames, ENGINE-09004 |
| [lms-calculation-service](lms-calculation-service.md) | Contract Collateral | **Live API secret in logs**, PII, 12k entries/day |
| [bravo-cnv-service](bravo-cnv-service.md) | Internal Service | 20k failed HCIS messages/day, logged twice each |
| [bravo-onboarding-service](bravo-onboarding-service.md) | Customer Platform | 64 KB inbound payload logging, live in prod |
| [bfi-insurance-api](bfi-insurance-api.md) | Insurance | 624 exception logs, broker body logging, logs in loops |
| [bravo-lms-gateway](bravo-lms-gateway.md) | Contract Collateral | 117 exception logs in one adapter |
| [bfi-digital-web-api](bfi-digital-web-api.md) | Digital Web | 679 `console.log` in a Node backend — billable |
| [lora-task-service](lora-task-service.md) | LORA Core | 3.8M warnings in 7 days, nearly all routine |
| [bravo-agency-service](bravo-agency-service.md) | Agency | Payload filter defaulting to DEBUG |
| [bravo-approval-engine-service](bravo-approval-engine-service.md) | Contract Collateral | Payload filter defaulting to DEBUG |
| [bravo-core-proxy-service](bravo-core-proxy-service.md) | Contract Collateral | Payload filter defaulting to DEBUG |
| [bravo-agreement-service](bravo-agreement-service.md) | Contract Collateral | 209 exception logs, dormant `loggerLevel: full` |
| [bravo-customer-service](bravo-customer-service.md) | Contract Collateral | 108 exception logs, dormant payload filter |
| [bravo-edoc-service](bravo-edoc-service.md) | Operation Post-Go Live | 175 exception logs, dormant `loggerLevel: full` |
| [bravo-branch-service](bravo-branch-service.md) | Internal Service | Logs inside branch-sync loops |
| [bfi-payment-api](bfi-payment-api.md) | Payment | Dev profile debug levels and Feign full |
| [bravo-payment-service](bravo-payment-service.md) | Payment | Dormant `loggerLevel: full` |
| [bravo-inventory-management-service](bravo-inventory-management-service.md) | Asset Management | `loggerLevel: full` in `application-prod.yaml` |
| [bravo-surveyor-console](bravo-surveyor-console.md) | Survey and Verification | 939 browser `console.log` — exposure, **no cost** |

## How to read these

Each per-repo file separates three things, because they get confused in the existing cost
documents:

- **Live** — confirmed emitting in production, or set explicitly in the production profile.
- **Dormant** — the setting exists but produces no output today, usually because the
  logger sits above DEBUG. No saving, but a risk worth closing.
- **Unknown** — depends on a deployment manifest that is not in these repos. Flagged, never
  costed.

Savings are ranges with a stated confidence. Where the evidence does not support a number,
the file says so rather than guessing.

## Three things this analysis could not check

- **Deployment manifests.** None of the 152 repos under `squads/` contains one. They live
  in a GitOps repo we do not have. This blocks a firm answer on Feign and on three payload
  filters.
- **Datadog's own filtering.** Datadog shows zero DEBUG logs estate-wide. That could mean
  DEBUG is not emitted, or that Datadog drops it before indexing while Cloud Logging still
  pays. Reading the manifests distinguishes the two.
- **Our Datadog contract rates.** The cost direction in the Datadog documents is
  qualitative. Before any enablement, get the per-GB ingest, per-million-events index and
  per-host add-on rates from the account team. August Datadog spend was Rp 110.6M, which is
  the baseline to protect.
