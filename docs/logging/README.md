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
- **Service pull requests: 7 merged, 44 open, 16 closed** on SRE's guidance. The Payment squad merged `bfi-payment-api#1650` on 7 October, and `bravo-edoc-service#1525` merged on 6 October. Squad reviewers were requested on 36 open pull requests on 7 October. None of the open ones fails CI because of this work. The red checks are gates that were already red before this work. Every pull request and its status is in the [table below](#per-service-pages-and-pull-requests).
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

## Per-service pages and pull requests

Every service in the programme has its own page with its findings and what its squad should do. The table lists each service's pull request and its status on 7 October. Squads come from the squad-to-repository sheet; a star marks a repository that is not in the sheet, where the squad is inferred from the squad's system list. Pull request counts for services: 7 merged, 44 open, 16 closed.

| Service | Squad | Pull request | What it fixes | Status (7 Oct) |
|---|---|---|---|---|
| [backend-dashboard-otrs](backend-dashboard-otrs.md) | — | none | No write access | no pull request |
| [bfi-connect](bfi-connect.md) | — | [#788](https://github.com/bfi-finance/bfi-connect/pull/788) | stop logging customer phone numbers on every duplicate-check miss | open — red only on Prettier |
| [bfi-digital-web-api](bfi-digital-web-api.md) | Digital Web | [#711](https://github.com/bfi-finance/bfi-digital-web-api/pull/711) | 679 `console.log` in a Node backend — billable | open — red only on SNYK / image CVEs |
| [bfi-incentive-api](bfi-incentive-api.md) | Agency | [#1698](https://github.com/bfi-finance/bfi-incentive-api/pull/1698) | give the consumer failure a stable message | open — red only on SNYK / image CVEs |
| [bfi-insurance-api](bfi-insurance-api.md) | Insurance | [#3298](https://github.com/bfi-finance/bfi-insurance-api/pull/3298) | 624 exception logs, broker body logging, logs in loops | open — red only on SNYK / image CVEs, SonarQube |
| [bfi-operation-api](bfi-operation-api.md) | — | none | No write access | no pull request |
| [bfi-payment-api](bfi-payment-api.md) | Payment | [#1650](https://github.com/bfi-finance/bfi-payment-api/pull/1650) | Dev profile debug levels and Feign full | **merged 7 Oct** |
| [bfi-rule-engine-service](bfi-rule-engine-service.md) | Digital Partnership | [#67](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67) | mask outbound HTTP bodies before they reach the log stream | **merged 17 Sep** |
| [bravo-agency-service](bravo-agency-service.md) | Agency | [#1141](https://github.com/bfi-finance/bravo-agency-service/pull/1141) | Payload filter defaulting to DEBUG | **merged 18 Sep** |
| [bravo-agency-service](bravo-agency-service.md) | Agency | [#1173](https://github.com/bfi-finance/bravo-agency-service/pull/1173) | stop the SIT message loop: reject without requeue when the application does not exist | open — CI green |
| [bravo-agent-marketing-service](bravo-agent-marketing-service.md) | Agency | [#829](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/829) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-agent-service](bravo-agent-service.md) | Agency | [#1632](https://github.com/bfi-finance/bravo-agent-service/pull/1632) | log rejected requests at warn, not error | open — red only on SonarQube |
| [bravo-agreement-service](bravo-agreement-service.md) | Contract Collateral | [#2604](https://github.com/bfi-finance/bravo-agreement-service/pull/2604) | 209 exception logs, dormant `loggerLevel: full` | open — CI green |
| [bravo-approval-engine-service](bravo-approval-engine-service.md) | Contract Collateral | [#166](https://github.com/bfi-finance/bravo-approval-engine-service/pull/166) | Payload filter defaulting to DEBUG | open — red only on SNYK / image CVEs |
| [bravo-asset-pricing-service](bravo-asset-pricing-service.md) | Internal Service | none | Nothing to change — and no telemetry in production at all | no pull request |
| [bravo-assistance-service](bravo-assistance-service.md) | Customer Platform | [#200](https://github.com/bfi-finance/bravo-assistance-service/pull/200) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-audit-trail-service](bravo-audit-trail-service.md) | Internal Service | [#36](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36) | mask outbound bodies, and say what the error was | open — red only on Codacy coverage |
| [bravo-auth-service](bravo-auth-service.md) | Internal Service | [#258](https://github.com/bfi-finance/bravo-auth-service/pull/258) | pick the log level from the status code | open — CI green |
| [bravo-backoffice-service](bravo-backoffice-service.md) | Direct Marketing | [#2781](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-bpm-service](bravo-bpm-service.md) | Scoring and Underwriting | [#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463) | 384 `loggerLevel: full`, stack frames, ENGINE-09004 | open — red only on SNYK / image CVEs, SonarQube |
| [bravo-bpm-service](bravo-bpm-service.md) | Scoring and Underwriting | [#10571](https://github.com/bfi-finance/bravo-bpm-service/pull/10571) | adopt the Java logging starter 0.1.1 (draft) | open — red only on SNYK / image CVEs, SonarQube |
| [bravo-branch-service](bravo-branch-service.md) | Internal Service | [#506](https://github.com/bfi-finance/bravo-branch-service/pull/506) | Logs inside branch-sync loops | open — red only on SonarQube |
| [bravo-calculation-service](bravo-calculation-service.md) | — | none | Mis-mapped by me | no pull request |
| [bravo-cnv-service](bravo-cnv-service.md) | Internal Service | [#726](https://github.com/bfi-finance/bravo-cnv-service/pull/726) | 20k failed HCIS messages/day, logged twice each | open — CI green |
| [bravo-collateral-service](bravo-collateral-service.md) | Contract Collateral | [#420](https://github.com/bfi-finance/bravo-collateral-service/pull/420) | log rejected requests at warn, and close the payload trap | open — red only on SonarQube |
| [bravo-core-proxy-service](bravo-core-proxy-service.md) | Contract Collateral | [#418](https://github.com/bfi-finance/bravo-core-proxy-service/pull/418) | Payload filter defaulting to DEBUG | open — red only on SonarQube |
| [bravo-customer-app-loan-service](bravo-customer-app-loan-service.md) | — | none | Mis-mapped by me | no pull request |
| [bravo-customer-bff-service](bravo-customer-bff-service.md) | Customer Mobile Apps | [#1216](https://github.com/bfi-finance/bravo-customer-bff-service/pull/1216) | give the masked-field lists a default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-customer-service](bravo-customer-service.md) | Contract Collateral | [#621](https://github.com/bfi-finance/bravo-customer-service/pull/621) | 108 exception logs, dormant payload filter | open — CI green |
| [bravo-database-catalog](bravo-database-catalog.md) | — | [#41](https://github.com/bfi-finance/bravo-database-catalog/pull/41) | mask request and response bodies by default | open — CI green |
| [bravo-document-service](bravo-document-service.md) | Operation Post-Go Live | none | Nothing to change — and no telemetry in production at all | no pull request |
| [bravo-edoc-service](bravo-edoc-service.md) | Operation Post-Go Live | [#1525](https://github.com/bfi-finance/bravo-edoc-service/pull/1525) | 175 exception logs, dormant `loggerLevel: full` | **merged 6 Oct** |
| [bravo-employee-service](bravo-employee-service.md) | Internal Service | [#172](https://github.com/bfi-finance/bravo-employee-service/pull/172) | stop writing whole HR records to the log stream | open — red only on Codacy coverage |
| [bravo-gen-ai](bravo-gen-ai.md) | Internal Service | [#359](https://github.com/bfi-finance/bravo-gen-ai/pull/359) | give the masked-field lists a default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-insurance-service](bravo-insurance-service.md) | Insurance | [#820](https://github.com/bfi-finance/bravo-insurance-service/pull/820) | log rejected requests at warn, not error | **merged 24 Sep** |
| [bravo-integrity-service](bravo-integrity-service.md) | Internal Service | [#29](https://github.com/bfi-finance/bravo-integrity-service/pull/29) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-inventory-management-service](bravo-inventory-management-service.md) | Asset Management | [#399](https://github.com/bfi-finance/bravo-inventory-management-service/pull/399) | `loggerLevel: full` in `application-prod.yaml` | **merged 15 Sep** |
| [bravo-inventory-management-service](bravo-inventory-management-service.md) | Asset Management | [#409](https://github.com/bfi-finance/bravo-inventory-management-service/pull/409) | turn the correlation id filter back on | open — CI green |
| [bravo-inventory-management-system](bravo-inventory-management-system.md) | Asset Management | [#232](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232) | stop putting the request body and Authorization header in RUM errors | open — red only on SNYK / image CVEs |
| [bravo-journal-service](bravo-journal-service.md) | Contract Collateral | [#297](https://github.com/bfi-finance/bravo-journal-service/pull/297) | log rejected requests at warn, and close the payload trap | open — red only on SNYK / image CVEs, SonarQube |
| [bravo-krakend-gateway](bravo-krakend-gateway.md) | — | [#387](https://github.com/bfi-finance/bravo-krakend-gateway/pull/387) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-krakend-internal](bravo-krakend-internal.md) | — | [#58](https://github.com/bfi-finance/bravo-krakend-internal/pull/58) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-kyc-proxy](bravo-kyc-proxy.md) | Internal Service | [#726](https://github.com/bfi-finance/bravo-kyc-proxy/pull/726) | give the masked-field lists a default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-kyc-sign-service](bravo-kyc-sign-service.md) | Internal Service* | [#118](https://github.com/bfi-finance/bravo-kyc-sign-service/pull/118) | mask request and response bodies by default | open — red only on Codacy coverage |
| [bravo-lms-gateway](bravo-lms-gateway.md) | Contract Collateral | [#2519](https://github.com/bfi-finance/bravo-lms-gateway/pull/2519) | 117 exception logs in one adapter | open — red only on SonarQube |
| [bravo-lms-ops-service](bravo-lms-ops-service.md) | Operation Post-Go Live | [#1856](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856) | close the request payload trap | open — red only on SNYK / image CVEs, SonarQube |
| [bravo-master-service](bravo-master-service.md) | Internal Service | none | Nothing to change — and no telemetry in production at all | no pull request |
| [bravo-notification-service](bravo-notification-service.md) | Internal Service | [#446](https://github.com/bfi-finance/bravo-notification-service/pull/446) | stop logging signing keys, private keys and bearer tokens | open — red only on SonarQube |
| [bravo-onboarding-service](bravo-onboarding-service.md) | Customer Platform | [#6328](https://github.com/bfi-finance/bravo-onboarding-service/pull/6328) | 64 KB inbound payload logging, live in prod | open, **approved** — red only on Codacy coverage, SNYK / image CVEs |
| [bravo-partnership-provisioning-service](bravo-partnership-provisioning-service.md) | LORA Core | [#94](https://github.com/bfi-finance/bravo-partnership-provisioning-service/pull/94) | mask request and response bodies by default | open — red only on Codacy coverage, SNYK / image CVEs |
| [bravo-partnership-service](bravo-partnership-service.md) | Digital Partnership | [#2367](https://github.com/bfi-finance/bravo-partnership-service/pull/2367) | stop copying MQ and HTTP payloads into the log stream | open — red only on SNYK / image CVEs, SonarQube |
| [bravo-payment-service](bravo-payment-service.md) | Payment | [#2661](https://github.com/bfi-finance/bravo-payment-service/pull/2661) | Dormant `loggerLevel: full` | open — red only on SonarQube |
| [bravo-pbf-service](bravo-pbf-service.md) | PBF (SF)* | [#125](https://github.com/bfi-finance/bravo-pbf-service/pull/125) | stop reporting "agreement not held here" as an error | open — red only on SonarQube |
| [bravo-product-service](bravo-product-service.md) | Contract Collateral | [#665](https://github.com/bfi-finance/bravo-product-service/pull/665) | log rejected requests at warn, not error | open — red only on Codacy coverage |
| [bravo-repeat-order-service](bravo-repeat-order-service.md) | Tele Marketing | [#3503](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503) | log rejected requests at warn, not error | open — red only on SNYK / image CVEs |
| [bravo-robot-controller](bravo-robot-controller.md) | Internal Service | [#84](https://github.com/bfi-finance/bravo-robot-controller/pull/84) | give the masked-field lists a default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-robot-scrape](bravo-robot-scrape.md) | Internal Service | [#114](https://github.com/bfi-finance/bravo-robot-scrape/pull/114) | report DMS upload failures as errors, not as stdout text | open — CI green |
| [bravo-samsat-region-resolver](bravo-samsat-region-resolver.md) | — | none | Mis-mapped by me | no pull request |
| [bravo-scheduling-service](bravo-scheduling-service.md) | Internal Service | [#300](https://github.com/bfi-finance/bravo-scheduling-service/pull/300) | mask outbound HTTP bodies before they reach the log stream | open — CI green |
| [bravo-supplier-service](bravo-supplier-service.md) | Supplier Platform | [#181](https://github.com/bfi-finance/bravo-supplier-service/pull/181) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [bravo-surveyor-console](bravo-surveyor-console.md) | Survey and Verification | [#3976](https://github.com/bfi-finance/bravo-surveyor-console/pull/3976) | 939 browser `console.log` — exposure, **no cost** | open — CI green |
| [bravo-user-iam-service](bravo-user-iam-service.md) | Internal Service | [#521](https://github.com/bfi-finance/bravo-user-iam-service/pull/521) | BAU deployment split across three Datadog names, 51 logs against 1.9M spans | open — CI green |
| [collection-consumer-service](collection-consumer-service.md) | Asset Management | [#143](https://github.com/bfi-finance/collection-consumer-service/pull/143) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [dms-data-admin-service](dms-data-admin-service.md) | — | none | Nothing to change — the prod profile is an empty file, and is right by accident | no pull request |
| [doc-renderer-service](doc-renderer-service.md) | Internal Service | [#31](https://github.com/bfi-finance/doc-renderer-service/pull/31) | mask request and response bodies by default | open — red only on Codacy coverage |
| [document-hub-service](document-hub-service.md) | Digital Partnership | [#92](https://github.com/bfi-finance/document-hub-service/pull/92) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [gold-service](gold-service.md) | LORA New Product | [#190](https://github.com/bfi-finance/gold-service/pull/190) | mask request and response bodies by default | open — CI green |
| [lms-calculation-service](lms-calculation-service.md) | Contract Collateral | [#647](https://github.com/bfi-finance/lms-calculation-service/pull/647) | **Live API secret in logs**, PII, 12k entries/day | **merged 18 Sep** |
| [lora-cdc-foxx-service](lora-cdc-foxx-service.md) | — | [#3](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3) | move the Datadog credentials and tags out of source | open — CI green |
| [lora-gateway-service](lora-gateway-service.md) | LORA Core | [#1263](https://github.com/bfi-finance/lora-gateway-service/pull/1263) | actually mask outbound bodies, and log them on failure only | open — red only on SNYK / image CVEs |
| [lora-partnership-ndf](lora-partnership-ndf.md) | LORA Core | [#1493](https://github.com/bfi-finance/lora-partnership-ndf/pull/1493) | mask request and response bodies by default | open — red only on Codacy coverage |
| [lora-partnership-task-ndf](lora-partnership-task-ndf.md) | LORA Core | [#2126](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126) | mask request and response bodies by default | open — red only on Codacy coverage, SNYK / image CVEs |
| [lora-schema-service](lora-schema-service.md) | LORA Core | [#1496](https://github.com/bfi-finance/lora-schema-service/pull/1496) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [lora-task-service](lora-task-service.md) | LORA Core | [#1363](https://github.com/bfi-finance/lora-task-service/pull/1363) | 3.8M warnings in 7 days, nearly all routine | open — red only on Codacy coverage |
| [notification-service](notification-service.md) | Internal Service | [#122](https://github.com/bfi-finance/notification-service/pull/122) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |
| [portfolio-management-service](portfolio-management-service.md) | LORA New Product | [#122](https://github.com/bfi-finance/portfolio-management-service/pull/122) | mask request and response bodies by default (closed: masking is a deployment setting, not a code default) | closed 14 Sep |

**Shared libraries and platform**

| Repository | Pull request | What it does | Status (7 Oct) |
|---|---|---|---|
| [app-deployment](https://github.com/bfi-finance/app-deployment) | [#13820](https://github.com/bfi-finance/app-deployment/pull/13820) | production log levels and mask lists for 20 services | **merged 7 Oct** |
| [app-deployment](https://github.com/bfi-finance/app-deployment) | [#14251](https://github.com/bfi-finance/app-deployment/pull/14251) | SIT and UAT logging baseline, 29 files | open — CI green |
| [app-deployment](https://github.com/bfi-finance/app-deployment) | [#14252](https://github.com/bfi-finance/app-deployment/pull/14252) | tag traces with the request id (draft) | open — CI green |
| [bfi-go-pkg](https://github.com/bfi-finance/bfi-go-pkg) | [#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) | Go wrapper: mask every value type, bounded payload helper | open, **approved** — CI green |
| [bfi-go-pkg](https://github.com/bfi-finance/bfi-go-pkg) | [#185](https://github.com/bfi-finance/bfi-go-pkg/pull/185) | Go wrapper: request id in error details, validation fields on the access line | open — CI green |
| [bfi-java-pkg](https://github.com/bfi-finance/bfi-java-pkg) | [#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) | new Java logging starter | **merged 16 Sep** |
| [bfi-java-pkg](https://github.com/bfi-finance/bfi-java-pkg) | [#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) | old Java library: mask Feign bodies (closed in favour of the starter) | closed 16 Sep |
| [bfi-java-pkg](https://github.com/bfi-finance/bfi-java-pkg) | [#128](https://github.com/bfi-finance/bfi-java-pkg/pull/128) | starter 0.1.1: stop dropping request logs after 6 lines | **merged 7 Oct** |
| [bfi-java-pkg](https://github.com/bfi-finance/bfi-java-pkg) | [#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) | return the correlation id on the response | open — red only on SNYK / image CVEs |
| [bravo-terraform](https://github.com/bfi-finance/bravo-terraform) | [#366](https://github.com/bfi-finance/bravo-terraform/pull/366) | create the queue monitors in production only | open — red only on SNYK / image CVEs |
| [bravo-terraform](https://github.com/bfi-finance/bravo-terraform) | [#367](https://github.com/bfi-finance/bravo-terraform/pull/367) | exclusion filters for non-production Cloud Logging | open — red only on SNYK / image CVEs |
