# Logging analysis

## Problem statement

BFI pays too much for its logs, and the logs still do not do their job.

- **We pay too much.** Logging costs about Rp 636M a month across three platforms: Cloud Logging, Coralogix and Datadog. In September the non-production environments spent more on Cloud Logging (Rp 157.5M) than production did (Rp 147.6M), and they serve no customer. Every production service line is also stored twice, because two log collectors run side by side. Our Datadog contract covers 256 GB of log ingestion a month. We send about 1.3 TB a day, so almost all of it is billed as overage.
- **The logs are hard to use.** 93.6% of production log lines cannot be parsed, because the container runtime splits any line over 16 KB. Eleven busy services send no logs to Datadog, and six send neither logs nor traces. Eight services log under two different names, so their logs and traces never join. Some monitors watch service names that do not exist, so they can never fire.
- **Sensitive data is in the logs.** One service wrote a live API secret into production logs for weeks. Working Google Chat webhook credentials, whole HR records and unmasked request and response bodies sit in the Datadog log index.
- **Why it keeps happening.** Squads cannot see request and response bodies in Datadog, so they log full bodies at `info` to answer customer questions. The shared logging libraries make body logging easy and masking weak. Each service sets its own log level and mask list in its deployment settings, and many are left at `debug` or with an empty mask list.

**What this programme does about it.** Send less, mask what we keep, and give squads a supported way to see the data they need. Only then turn on more Datadog features, because Datadog bills on what we send. The ordered work is in [Do these first](#do-these-first).

## Where things stand on 7 October 2026

- **One of thirteen steps is done.** Three are partly done or unclear, and nine show no progress. The table below has the status of each.
- **The production manifest change is live.** [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) merged on 7 October and rolled out within minutes. It takes nine services off `debug` and gives five of them a mask list. Its effect on volume can be measured from 8 October.
- **Two security items are still open.** The Google Chat webhook keys are still being logged, between 250 and 950 lines on most days. The leaked API secret no longer reaches the logs, but nobody has confirmed it was rotated.
- **Every open step has an SRE ticket and, where a change can fix it, a pull request.** Tickets [SRE-1821](https://bfifinance.atlassian.net/browse/SRE-1821) to [SRE-1832](https://bfifinance.atlassian.net/browse/SRE-1832) carry the label `logging-programme`.
- **Service pull requests: 5 merged, 43 open, 16 closed** on SRE's guidance. Squad reviewers were requested on 36 of the open ones on 7 October. None of the open ones fails CI because of this work. The red checks are gates that were already red before this work.
- **The Java logging starter is published** (version 0.1.1, 7 October). No service uses it on its main branch yet. `bravo-bpm-service` should be first.

## Do these first

| # | Action | Owner | Status (7 Oct) | PR and ticket |
|---|---|---|---|---|
| 1 | Fix the leaked API secret in `lms-calculation-service`, and rotate it | Contract Collateral | **Partly done.** The code fix is live since 1 October, and no log line has carried the secret since. Rotation is not confirmed. | [lms-calculation-service#647](https://github.com/bfi-finance/lms-calculation-service/pull/647) (merged); [SRE-1822](https://bfifinance.atlassian.net/browse/SRE-1822) |
| 2 | Merge the production manifest change: log levels and mask lists for 20 services | SRE + squads | **Done.** Merged and rolled out on 7 October. | [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) |
| 2a | Adopt the Java logging starter, `bravo-bpm-service` first | Platform + Scoring and Underwriting | **Partly done.** Published, version 0.1.1. No service uses it on its main branch. | [bravo-bpm-service#10571](https://github.com/bfi-finance/bravo-bpm-service/pull/10571) (draft); [SRE-1832](https://bfifinance.atlassian.net/browse/SRE-1832) |
| 3 | Non-production: lower Argo CD's log level, stop the SIT agency–onboarding message loop, add exclusion filters | Platform + Agency | **Not done.** Argo CD still writes about 355 GB a day. The SIT loop ran again on 3 and 6 October. There are still no exclusion filters. | [bravo-terraform#367](https://github.com/bfi-finance/bravo-terraform/pull/367); [bravo-agency-service#1173](https://github.com/bfi-finance/bravo-agency-service/pull/1173); [SRE-1823](https://bfifinance.atlassian.net/browse/SRE-1823) |
| 4 | Remove the monitors that watch service names that do not exist | SRE | **Not done.** All 74 are still in place and can never fire. | [bravo-terraform#366](https://github.com/bfi-finance/bravo-terraform/pull/366); [SRE-1824](https://bfifinance.atlassian.net/browse/SRE-1824) |
| 5 | Fix CONFINS log re-ingestion | SRE | **Unclear.** The re-reading looks stopped, but volume is 2.7 to 7.3 million entries a day, against about 200,000 in September. | No PR; [SRE-1825](https://bfifinance.atlassian.net/browse/SRE-1825) |
| 6 | Decide what Coralogix is for | Architecture | **No progress.** No page or ticket answers it. | No PR; [SRE-1826](https://bfifinance.atlassian.net/browse/SRE-1826) |
| 7 | Fix Datadog Remote Configuration on 13 services | SRE | **Not done.** 108,000 failed polls in seven days. | No PR; [SRE-1827](https://bfifinance.atlassian.net/browse/SRE-1827) |
| 8 | Tag traces with the correlation id (`DD_TRACE_HEADER_TAGS`) | SRE | **Not done.** No production manifest sets it. | [app-deployment#14252](https://github.com/bfi-finance/app-deployment/pull/14252) (draft); [SRE-1828](https://bfifinance.atlassian.net/browse/SRE-1828) |
| 9 | Stop logging the Google Chat webhook keys in `bau-prod-ms-otrs-report`, then rotate them | Platform / security | **Not done.** 954 lines carried the keys on 6 October. | No PR, no write access; [SRE-1821](https://bfifinance.atlassian.net/browse/SRE-1821) |
| 10 | Fix the three CI gate faults: Codacy token, Codacy installer, SonarQube baseline | Platform | **Not done.** A shallow clone is ruled out as the SonarQube cause. The baseline is the next suspect. | No PR; [SRE-1829](https://bfifinance.atlassian.net/browse/SRE-1829) |
| 11 | Return the request id to the caller and log one line per rejected request, in the shared libraries | Platform, then squads | **Not done.** Neither Java filter returns the id yet. | [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129); [bfi-go-pkg#185](https://github.com/bfi-finance/bfi-go-pkg/pull/185); [SRE-1830](https://bfifinance.atlassian.net/browse/SRE-1830) |
| 12 | Apply the SIT and UAT logging baseline to 29 manifest files | SRE | **Not done.** The 29 files are unchanged. | [app-deployment#14251](https://github.com/bfi-finance/app-deployment/pull/14251); [SRE-1831](https://bfifinance.atlassian.net/browse/SRE-1831) |

None of these steps increases Datadog spend. Take the two security items, 9 and 1, first. The evidence behind each status is on [the history page](history.md#do-these-first--full-evidence).

## Moving to Datadog

BFI is standardising on Datadog for logs, traces and metrics. Clean up first, then turn on more Datadog features. Datadog bills on what we send it, so turning features on against today's stream would move the waste from Cloud Logging to Datadog and cost more.

SRE turns features on when both numbers below reach their gate:

| Metric | Today | Gate |
|---|---:|---:|
| Production log lines per day | ~4.5M | **below 2.5M** |
| Share Datadog can parse | 6.4% | **above 80%** |

The one exception is Error Tracking. It uses telemetry that already flows and adds no ingestion, so turn it on now.

Our Datadog contract commits 256 GB of log ingestion a month. We send about 40 TB a month, 150 times that, and the excess is billed as overage. The detail is in [logging-cost.md](logging-cost.md) §1a.

## Documents

| Document | What it is for |
|---|---|
| [logging-cost.md](logging-cost.md) | What logging costs, where the money goes, and the ordered work list |
| [bravo-logging-deck.html](../decks/bravo-logging-deck.html) ([PDF](../decks/pdf/bravo-logging-deck.pdf)) | The CTO deck, 13 slides |
| [squads-guide.md](squads-guide.md) | For every squad: what to log, what not to log, and which Datadog feature answers which question |
| [sre-datadog-recommendations.md](sre-datadog-recommendations.md) | For SRE: an audit of our Datadog setup and what to change |
| [body-visibility.md](body-visibility.md) | Why squads log request and response bodies, and what replaces that |
| [nonprod-logging.md](nonprod-logging.md) | SIT and UAT: what they cost and the logging baseline |
| [deployment-proposal.md](deployment-proposal.md) | The production manifest changes and the reasoning behind them |
| [coverage.md](coverage.md) | The estate map: 122 production services, 52 with no source we can see |
| [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md) | The CONFINS log re-ingestion finding |
| [history.md](history.md) | Full evidence, weekly changes, every pull request with its status, and CI results |

## Per-service pages

Every service in the programme has its own page with its findings, its pull request and what its squad should do. The first twenty, ordered by billable impact, are below. The other 53 are in the pack-two table on [the history page](history.md#implementation--pack-two-forty-four-pull-requests).

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
| [bravo-user-iam-service](bravo-user-iam-service.md) | Internal Service | BAU deployment split across three Datadog names, 51 logs against 1.9M spans |
