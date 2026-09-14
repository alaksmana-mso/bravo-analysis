# Why only twenty repos, and what the rest look like

Written 13 September 2026, revised the same day after the second pack was
implemented. Answers a fair question: the first pack covered twenty
repositories. That was a cut by billable impact, **not** a clean/dirty split.
The other services were not clean.

All 53 have now been worked through. This file records what the estate contains,
what the second pack found, and three places where the first version of this
document was wrong.

---

## 1. Corrections to the first version of this file

**Four repositories were mapped to the wrong production service.** The first
version matched Datadog service names to repository names by similarity. Datadog
carries the answer directly, in the `git.repository_url` tag:

| I said | Datadog says |
|---|---|
| `bravo-calculation-service` runs as `prod-ms-calculation` | `prod-ms-calculation` is built from **`lms-calculation-service`** — already covered in the first pack |
| `bravo-customer-app-loan-service` runs as `prod-ms-kyc-proxy` | `prod-ms-kyc-proxy` is built from **`bravo-kyc-proxy`** |
| `bravo-samsat-region-resolver` runs as `prod-ms-rule-engine` | `prod-ms-rule-engine` is built from **`bfi-rule-engine-service`** |
| `notification-service` runs as `prod-ms-notification` | `prod-ms-notification` is built from **`bravo-notification-service`** |

**`prod-ms-krakend-gateway` is not a levelling mistake.** The first version of
this file said of the gateway: "Nothing is wrong; it is a request log wearing the
wrong level." That was wrong on both counts.

The `server-observer` plugin maps status codes to levels deliberately and
correctly — 5xx to error, 4xx to warn, 2xx to info — and production runs at
`LOGGER_LEVEL=WARNING`, which is why there is no info. The 942,909 warn entries a
week are **942,909 real 4xx responses**:

| Route | Status | Per week |
|---|---:|---:|
| `/collection/notification/whatsapp` | 400 | **415,388** |
| `/collection/notification/email` | 500 | 67,369 |
| `/gopay-kendaraan-payment-collection/inquiry` | 422 | 23,750 |
| `/collection/document/survey` | 500 | 17,600 |
| `/eline/lms-ops/v1/eline/feedback` | 400 | 11,295 |
| `/autodebit-bri/payment/callback/v1/Api/Inquiry` | 404 | 6,507 |

A WhatsApp notification endpoint rejecting 415,388 requests a week, and a bank
autodebit callback hitting a route that does not exist 6,507 times a week, are
integration defects. **The logging is reporting them accurately.** Silencing the
gateway would remove the only evidence. The gateway pull request therefore
changes masking defaults only, and the volume stays until someone fixes the
callers.

**"Production-active" was too generous.** The 70/53 split came from that same
name-similarity join. Of the services in it, several produce no telemetry at all
— see section 4.

---

## 2. What the estate actually contains

| | Count |
|---|---:|
| Repository checkouts under `squads/` before this work | 152 (121 unique — six repos are checked out twice) |
| Repositories in the `bfi-finance` GitHub org | 267 (19 archived) |
| Production services with telemetry in Datadog, 7 days | 122 application services |
| Repositories that identify themselves in production logs via `git.repository_url` | **39** |
| Production services with **no repository we can see** | 52 |

### The 52 with no source

These run in production and nothing in `bfi-finance` corresponds to them. Most
are the **CONFINS / AdIns vendor estate** and the **BFI Treasury** family:

- CONFINS: `prod-ms-lms-ar-be`, `prod-ms-fou-foundation-be`, `prod-ms-los-be`,
  `prod-ms-lms-amendment-be`, `prod-ms-lms-payment-be`, `prod-ms-lms-cashbank-be`,
  `prod-ms-lms-ar-maintenance-be`, `prod-ms-lms-government-rgltn-be`,
  `prod-ms-lms-recon-be`, `prod-ms-lms-recovery-be`, `prod-ms-mou-cwr-be`,
  `prod-ms-ce-integration-be`, `prod-ms-fincal-be`, `prod-ms-pcms-accounting-be`,
  `prod-ms-ams-asset-be`, `prod-ms-ams-storage-and-selling-be`, the nine
  `confins-prod-ms-ce-batch-worker-*` jobs and `confins-prod-ms-ce-camunda-external-task-client`.
- Treasury: `prod-ms-bfi-treasury-batching-api`, `-disbursement-api`,
  `-bank-facility-api`, `-gateway-api`, `-backoffice-api`, `-notification-api`,
  `-time-deposit-api`.
- Others: `prod-ms-bfi-task-allocation` (1.25M spans a week), `prod-ms-bfi-agency-api`,
  `prod-ms-bfi-otrs-api`, `prod-ms-ams`, `prod-iad-ams`, `prod-bau-prod-ms-sampling-ams`,
  `prod-ms-findigital-scorebranch`, `prod-ms-findigital-onegate`,
  `prod-ms-bfi-payment-net-api`, `prod-ms-bfi-syariah-net-api`, `prod-ms-consumer-bfi`,
  `prod-ares`, `prod-army`.

`confins-prod-ms-lms-ar-be` alone is **29% of all production log volume**.

**Corrected 14 September 2026.** That share is a collection artefact, not application
output. The entries are request and response bodies with no `message` key, and about 90% of
the volume is the Datadog Agent re-reading dead pods' log files from a shared `/var/log` on
the `core-system-prod` nodes whenever a rollout schedules a new pod. Files outnumber pods
across the whole CONFINS family. SRE can fix it without source access — [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md). Getting source
access, or an owner, for this group still matters for the body logging and for the other 51
services without source.

---

## 3. What the second pack found

Six things that were not visible from the first twenty.

**Whole HR records at info, roughly 900,000 times a week.**
`bravo-employee-service` logged every inbound and outbound RabbitMQ message in
full — religion, marital status, date and place of birth, bank account number and
holder name, personal email and mobile number. See
[bravo-employee-service.md](bravo-employee-service.md).

**A JWT signing key printed to stdout.** `bravo-notification-service` had
`fmt.Printf("… Private key PEM: %s", pemPrivateKey)`. `fmt.Printf` bypasses the
logger, so no level could suppress it. It is not firing in production today —
that path is not being exercised — but the code is there. The same file logged
the Vonage private key at info and every failed bearer token at warn. See
[bravo-notification-service.md](bravo-notification-service.md).

**Working Google Chat webhook credentials in the log index.**
`backend-dashboard-otrs` logs the full webhook URL, and those URLs carry their
key and token in the query string. **Rotate them.** There is no write access to
that repository, so the fix sits on a local branch. See
[backend-dashboard-otrs.md](backend-dashboard-otrs.md).

**An authentication service where 98.5% of entries are errors.**
`prod-ms-auth` writes 16,934 errors and 3 info a week, because `Error.Write`
logged at error whatever status code it was handed. A wrong OTP was an error.
See [bravo-auth-service.md](bravo-auth-service.md).

**Go masking is a deployment setting, and in production it is often set to
nothing.** `bfi-go-pkg` provides `JSONScrubberFunc`; the field list it masks comes
from `*_JSON_MASKED_FIELDS` environment variables that SRE sets per service and per
environment in `app-deployment` — not, as an earlier version of this paragraph had
it, from a default in each service's code. Reading every `values-prod.yaml` on
14 September 2026: **eight Go services log bodies in production with every
masked-field variable set to `""`** (`lora-gateway`, `doc-renderer`,
`partnership-provisioning`, `lora-schema`, `database-catalog` over HTTP;
`integrity`, `pbf`, `supplier` over gRPC). SRE's view is that `lora-schema` and
`database-catalog` carry no PII, which leaves five where a list is needed; the
the diffs are in [deployment-proposal.md](deployment-proposal.md), raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820).
Separately, in three repositories the code never called the scrubber at all —
`lora-gateway-service` had the call commented out under a comment claiming the
code was non-production only, while writing 69,433 bodies a week in production —
so a deployment setting would have done nothing; those three pull requests wire
it (`lora-gateway-service`, `bravo-kyc-sign-service`, `bravo-database-catalog`).
The sixteen pull requests that only added a code default were closed on SRE's
guidance; see [README.md](README.md#implementation--pack-two-forty-four-pull-requests).

**Eight Go services run production at `LOGGER_LEVEL=debug`.** `audit-trail`,
`gen-ai`, `partnership-provisioning`, `robot-controller`, `supplier`,
`doc-renderer`, `gold-service`, `portfolio-management-service` — and the last
two also at `POSTGRES_LOG_LEVEL=debug`. `bravo-robot-scrape` runs at `DEBUG`
too. No code change fixes that; one line each in `values-prod.yaml` does
([deployment-proposal.md](deployment-proposal.md) §1).

**Customer phone numbers on every duplicate-check miss.** `bfi-connect` writes
6,608 warn entries a week carrying a mobile number, customer ID and licence
plate, for a "Data Not Found" response the code already treats as normal.

---

## 4. Services that emit nothing at all

Six of the 53 produce **no log entries and no APM spans** in a 7-day window:
`prod-ms-asset-pricing`, `prod-ms-document`, `prod-ms-master`,
`prod-ms-collateral`, `prod-ms-journal`, `prod-ms-data-admin`. Several others —
`prod-ms-krakend-internal`, `prod-ms-kyc-sign`, `prod-doc-renderer`,
`prod-ms-document-hub` — are the same.

A service nobody can observe is a worse problem than a noisy one, and this
programme cannot fix it from the code side. It belongs with SRE alongside the
Remote Configuration failure.

Separately: `prod-ms-product`, `prod-ms-kyc-proxy` and `prod-ms-rule-engine`
produce logs but **no APM spans at all**. They are running untraced.

---

## 5. Status — the 53

**44 pull requests open.** Nine repositories have none, for the reasons given.

| Repository | Production service | Pull request | What it changes |
|---|---|---|---|
| [bfi-connect](bfi-connect.md) | `prod-ms-bfi-connect` | [#788](https://github.com/bfi-finance/bfi-connect/pull/788) | stop logging customer phone numbers on every duplicate-check miss |
| [bfi-incentive-api](bfi-incentive-api.md) | `prod-ms-bfi-incentive-api` | [#1698](https://github.com/bfi-finance/bfi-incentive-api/pull/1698) | give the consumer failure a stable message |
| [bfi-rule-engine-service](bfi-rule-engine-service.md) | `prod-ms-rule-engine` | [#67](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67) | mask outbound HTTP bodies before they reach the log stream |
| [bravo-agent-marketing-service](bravo-agent-marketing-service.md) | `prod-agent-marketing` | [#829](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/829) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-agent-service](bravo-agent-service.md) | `prod-ms-agent` | [#1632](https://github.com/bfi-finance/bravo-agent-service/pull/1632) | log rejected requests at warn, not error |
| [bravo-assistance-service](bravo-assistance-service.md) | `prod-ms-assistance` | [#200](https://github.com/bfi-finance/bravo-assistance-service/pull/200) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-audit-trail-service](bravo-audit-trail-service.md) | `prod-ms-audit-trail` | [#36](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36) | mask outbound bodies, and say what the error was |
| [bravo-auth-service](bravo-auth-service.md) | `prod-ms-auth` | [#258](https://github.com/bfi-finance/bravo-auth-service/pull/258) | pick the log level from the status code |
| [bravo-backoffice-service](bravo-backoffice-service.md) | `prod-ms-backoffice` | [#2781](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-collateral-service](bravo-collateral-service.md) | `prod-ms-collateral` | [#420](https://github.com/bfi-finance/bravo-collateral-service/pull/420) | log rejected requests at warn, and close the payload trap |
| [bravo-customer-bff-service](bravo-customer-bff-service.md) | `prod-customer-bff` | [#1216](https://github.com/bfi-finance/bravo-customer-bff-service/pull/1216) | ~~give the masked-field lists a default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-database-catalog](bravo-database-catalog.md) | `prod-database-catalog` | [#41](https://github.com/bfi-finance/bravo-database-catalog/pull/41) | mask request and response bodies by default |
| [bravo-employee-service](bravo-employee-service.md) | `prod-ms-employee` | [#172](https://github.com/bfi-finance/bravo-employee-service/pull/172) | stop writing whole HR records to the log stream |
| [bravo-gen-ai](bravo-gen-ai.md) | `prod-ms-gen-ai` | [#359](https://github.com/bfi-finance/bravo-gen-ai/pull/359) | ~~give the masked-field lists a default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-insurance-service](bravo-insurance-service.md) | `prod-ms-insurance` | [#820](https://github.com/bfi-finance/bravo-insurance-service/pull/820) | log rejected requests at warn, not error |
| [bravo-integrity-service](bravo-integrity-service.md) | `prod-ms-integrity` | [#29](https://github.com/bfi-finance/bravo-integrity-service/pull/29) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-inventory-management-system](bravo-inventory-management-system.md) | `bravo-inventory-management-system` | [#232](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232) | stop putting the request body and Authorization header in RUM errors |
| [bravo-journal-service](bravo-journal-service.md) | `prod-ms-journal` | [#297](https://github.com/bfi-finance/bravo-journal-service/pull/297) | log rejected requests at warn, and close the payload trap |
| [bravo-krakend-gateway](bravo-krakend-gateway.md) | `prod-ms-krakend-gateway` | [#387](https://github.com/bfi-finance/bravo-krakend-gateway/pull/387) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-krakend-internal](bravo-krakend-internal.md) | `prod-ms-krakend-internal` | [#58](https://github.com/bfi-finance/bravo-krakend-internal/pull/58) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-kyc-proxy](bravo-kyc-proxy.md) | `prod-ms-kyc-proxy` | [#726](https://github.com/bfi-finance/bravo-kyc-proxy/pull/726) | ~~give the masked-field lists a default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-kyc-sign-service](bravo-kyc-sign-service.md) | `prod-ms-kyc-sign` | [#118](https://github.com/bfi-finance/bravo-kyc-sign-service/pull/118) | mask request and response bodies by default |
| [bravo-lms-ops-service](bravo-lms-ops-service.md) | `prod-ms-lms-ops` | [#1856](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856) | close the request payload trap |
| [bravo-notification-service](bravo-notification-service.md) | `prod-ms-notification` | [#446](https://github.com/bfi-finance/bravo-notification-service/pull/446) | stop logging signing keys, private keys and bearer tokens |
| [bravo-partnership-provisioning-service](bravo-partnership-provisioning-service.md) | `prod-ms-partnership-provisioning` | [#94](https://github.com/bfi-finance/bravo-partnership-provisioning-service/pull/94) | mask request and response bodies by default |
| [bravo-partnership-service](bravo-partnership-service.md) | `prod-ms-partnership` | [#2367](https://github.com/bfi-finance/bravo-partnership-service/pull/2367) | stop copying MQ and HTTP payloads into the log stream |
| [bravo-pbf-service](bravo-pbf-service.md) | `prod-ms-pbf` | [#125](https://github.com/bfi-finance/bravo-pbf-service/pull/125) | stop reporting "agreement not held here" as an error |
| [bravo-product-service](bravo-product-service.md) | `prod-ms-product` | [#665](https://github.com/bfi-finance/bravo-product-service/pull/665) | log rejected requests at warn, not error |
| [bravo-repeat-order-service](bravo-repeat-order-service.md) | `prod-ms-repeat-order` | [#3503](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503) | log rejected requests at warn, not error |
| [bravo-robot-controller](bravo-robot-controller.md) | `prod-ms-robot-controller` | [#84](https://github.com/bfi-finance/bravo-robot-controller/pull/84) | ~~give the masked-field lists a default~~ **closed 14 Sep — deployment setting, not a code default** |
| [bravo-robot-scrape](bravo-robot-scrape.md) | `prod-robot-scrape` | [#114](https://github.com/bfi-finance/bravo-robot-scrape/pull/114) | report DMS upload failures as errors, not as stdout text |
| [bravo-scheduling-service](bravo-scheduling-service.md) | `prod-ms-scheduling` | [#300](https://github.com/bfi-finance/bravo-scheduling-service/pull/300) | mask outbound HTTP bodies before they reach the log stream |
| [bravo-supplier-service](bravo-supplier-service.md) | `prod-ms-supplier` | [#181](https://github.com/bfi-finance/bravo-supplier-service/pull/181) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [collection-consumer-service](collection-consumer-service.md) | `prod-ms-collection-consumer` | [#143](https://github.com/bfi-finance/collection-consumer-service/pull/143) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [doc-renderer-service](doc-renderer-service.md) | `prod-doc-renderer` | [#31](https://github.com/bfi-finance/doc-renderer-service/pull/31) | mask request and response bodies by default |
| [document-hub-service](document-hub-service.md) | `prod-ms-document-hub` | [#92](https://github.com/bfi-finance/document-hub-service/pull/92) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [gold-service](gold-service.md) | `prod-ms-gold-service` | [#190](https://github.com/bfi-finance/gold-service/pull/190) | mask request and response bodies by default |
| [lora-cdc-foxx-service](lora-cdc-foxx-service.md) | `prod-lora-cdc-foxx-service` | [#3](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3) | move the Datadog credentials and tags out of source |
| [lora-gateway-service](lora-gateway-service.md) | `prod-lora-gateway` | [#1263](https://github.com/bfi-finance/lora-gateway-service/pull/1263) | actually mask outbound bodies, and log them on failure only |
| [lora-partnership-ndf](lora-partnership-ndf.md) | `prod-lora-partnership-ndf` | [#1493](https://github.com/bfi-finance/lora-partnership-ndf/pull/1493) | mask request and response bodies by default |
| [lora-partnership-task-ndf](lora-partnership-task-ndf.md) | `prod-lora-partnership-task-ndf` | [#2126](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126) | mask request and response bodies by default |
| [lora-schema-service](lora-schema-service.md) | `prod-lora-schema` | [#1496](https://github.com/bfi-finance/lora-schema-service/pull/1496) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [notification-service](notification-service.md) | `prod-ms-notification` | [#122](https://github.com/bfi-finance/notification-service/pull/122) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |
| [portfolio-management-service](portfolio-management-service.md) | `prod-portfolio-management-service` | [#122](https://github.com/bfi-finance/portfolio-management-service/pull/122) | ~~mask request and response bodies by default~~ **closed 14 Sep — deployment setting, not a code default** |

**No pull request — 9 repositories.**

| Repository | Production service | Why |
|---|---|---|
| [backend-dashboard-otrs](backend-dashboard-otrs.md) | `bau-prod-ms-otrs-report` | **No write access.** Branch exists locally. The credential exposure it fixes needs action now, not later |
| [bfi-operation-api](bfi-operation-api.md) | `prod-ms-bfi-operation-api` | **No write access.** Finding recorded in the file |
| [bravo-asset-pricing-service](bravo-asset-pricing-service.md) | `prod-ms-asset-pricing` | Nothing to change — and no telemetry in production at all |
| [bravo-calculation-service](bravo-calculation-service.md) | `prod-ms-calculation` | Mis-mapped by me. `prod-ms-calculation` is built from `lms-calculation-service` |
| [bravo-customer-app-loan-service](bravo-customer-app-loan-service.md) | `prod-ms-kyc-proxy` | Mis-mapped by me. `prod-ms-kyc-proxy` is built from `bravo-kyc-proxy` |
| [bravo-document-service](bravo-document-service.md) | `prod-ms-document` | Nothing to change — and no telemetry in production at all |
| [bravo-master-service](bravo-master-service.md) | `prod-ms-master` | Nothing to change — and no telemetry in production at all |
| [bravo-samsat-region-resolver](bravo-samsat-region-resolver.md) | `prod-ms-rule-engine` | Mis-mapped by me. `prod-ms-rule-engine` is built from `bfi-rule-engine-service` |
| [dms-data-admin-service](dms-data-admin-service.md) | `prod-ms-data-admin` | Nothing to change — the prod profile is an empty file, and is right by accident |

---

## 6. One security-shaped finding carried forward

`prod-ms-partnership` logs this 639 times in two days, at `warn`:

```
failed to decrypt bank_account_name_to, assuming plaintext
```

The service attempts to decrypt a bank account holder's name, fails, and
proceeds with the value as plaintext. That is not a logging defect — the logging
is how it surfaced. It needs an owner from the Digital Partnership squad and
should not wait for the logging programme. The pull request on that repository
deliberately leaves the line exactly as it is, because it is the only signal
that this is happening.
