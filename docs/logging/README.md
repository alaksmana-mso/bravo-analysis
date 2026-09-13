# Logging analysis

Written 12 September 2026. Second pass 13 September 2026.

Cost data is GCP billing through FinOps. Log evidence is Datadog production. Code evidence
is all 152 repos under `squads/`, pulled to `master` on the day of writing — 149,729 files
scanned — plus 36 more cloned since.

**73 repositories analysed, 64 pull requests open, 79 files in this folder.** The code half
of the programme is written; what is left on it is review and merge.

## Start here

**[logging-cost.md](logging-cost.md)** — what logging costs, where the money goes, what the
evidence supports, and the ordered work list.

**For the CTO:** [bravo-logging-deck.html](../decks/bravo-logging-deck.html) —
13 slides, also rendered to [PDF](../decks/pdf/bravo-logging-deck.pdf). The correction is on
slides 3–5, what the second pass found on 8–9, the plan on 11–13.

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
- **Eleven busy Bravo services send no logs to Datadog at all**, including
  `prod-ms-agreement` at 7.4 million spans a week. Another **eight are split across two
  service names**, so logs and traces can never join.
- **Two services are logging full request and response bodies into production**, unmasked.
  `prod-ms-bpm` alone writes 487,146 of them a week — 44% of its log volume.
- **Remote Configuration is failing on thirteen production services**, roughly 91,000 failed
  polls a week. Nothing can be enabled from the Datadog UI until that is fixed.

Added by the second pass:

- **Working Google Chat webhook credentials are in the Datadog log index now.** The key and
  token are in the URL query string, and the URL is logged on every message sent.
- **Whole HR records at `info`, about 900,000 times a week** — religion, marital status,
  date and place of birth, bank account number and holder name.
- **The Go estate's masking is wired up and empty.** Twenty-two repositories hand the
  scrubber a field list that defaults to nothing; in one the scrubber call is commented out
  entirely, under a comment claiming the code is non-production only.
- **Six production services emit no logs and no traces at all.** Not quiet — invisible.
- One CI job, failing for a missing Codacy token, **red-flags 23 of the 64 pull requests**
  for a reason unrelated to their content.

## Moving to Datadog

BFI is standardising on Datadog for logs, traces and metrics. Two documents cover that:

- **[squads-guide.md](squads-guide.md)** — what to log and what not to, which Datadog
  feature answers which question, and where to find it. For every squad.
- **[sre-datadog-recommendations.md](sre-datadog-recommendations.md)** — a configuration
  audit of our Datadog org across all environments, and what SRE should change.
- **[body-visibility.md](body-visibility.md)** — squads say they cannot see request and
  response bodies in Datadog, so they log them instead. They are right. This is the
  estate-level view, the service-by-service index, and what SRE should enable. The findings
  for each service live in that service's own file.

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
| 7 | **Fix Remote Configuration** — failing on 13 services, ~91k failed polls a week | SRE | 1 d | none |
| 8 | Turn on `DD_TRACE_HEADER_TAGS` for correlation IDs | SRE | 1 h | none |
| 9 | **Rotate the Google Chat webhooks** logged by `bau-prod-ms-otrs-report` | Platform / security | 1 d | none |
| 10 | **Fix the Codacy token in the shared CI workflow** — it blocks 23 of the 64 pull requests | Platform | 1 h | none |

None of these increases Datadog spend. Items 1 and 2 are an afternoon between them, and
item 2 decides whether several of the per-repo files below are worth anything. Item 9 is a
live credential exposure; item 10 is an hour that unblocks six weeks of squad work.

## Coverage — all 53 remaining repositories are now done

**[coverage.md](coverage.md)** has the estate map and the results of the second pack.
Headline numbers: 122 production services, **52 with no source we can see**, and
`confins-prod-ms-lms-ar-be` alone at 29% of all production log volume. Getting an owner for
the CONFINS and Treasury families is still a bigger lever than every pull request here put
together.

**coverage.md also corrects three things this README said before.** The most important:

> The single worst offender in the whole estate is not in the first twenty:
> `prod-ms-krakend-gateway` … because the API gateway emits its access log at warn level.

**That was wrong.** The gateway's `server-observer` plugin maps 5xx to error, 4xx to warn
and 2xx to info, deliberately and correctly, and production runs at `LOGGER_LEVEL=WARNING`.
The 942,909 warn entries a week are **942,909 real 4xx responses** — 415,388 of them a
single WhatsApp notification endpoint returning 400, and 6,507 a bank autodebit callback
hitting a route that does not exist. The logging is reporting integration defects
accurately. Silencing it would remove the only evidence.

## Implementation — pack one, twenty pull requests

Every recommendation that is a code or configuration change has been implemented on a
branch called **`fix/logging`** in each of the twenty repositories, branched from `master`,
pushed, and raised as a pull request. All twenty are **open and unmerged**.

**Corrected 14 September 2026.** This paragraph said the machine had no Node, Go, JDK or
Maven toolchain. **Go and Node are in fact installed via `mise`** — a bare `which go` is what
produced the wrong conclusion, and the claim went into ~50 documents and 64 pull requests
before it was caught.

Every Go change in this programme has since been compiled, formatted and linted locally.
**Java genuinely cannot be built here**: there is no Maven and `/usr/bin/java` is the macOS
stub with no runtime, so the Java pull requests were reviewed by reading only. CI on each
pull request is still the authority.

| Repo | Pull request |
|---|---|
| [bfi-digital-web-api](bfi-digital-web-api.md) | [#711](https://github.com/bfi-finance/bfi-digital-web-api/pull/711) |
| [bfi-insurance-api](bfi-insurance-api.md) | [#3298](https://github.com/bfi-finance/bfi-insurance-api/pull/3298) |
| [bfi-payment-api](bfi-payment-api.md) | [#1650](https://github.com/bfi-finance/bfi-payment-api/pull/1650) |
| [bravo-agency-service](bravo-agency-service.md) | [#1141](https://github.com/bfi-finance/bravo-agency-service/pull/1141) |
| [bravo-agreement-service](bravo-agreement-service.md) | [#2604](https://github.com/bfi-finance/bravo-agreement-service/pull/2604) |
| [bravo-approval-engine-service](bravo-approval-engine-service.md) | [#166](https://github.com/bfi-finance/bravo-approval-engine-service/pull/166) |
| [bravo-bpm-service](bravo-bpm-service.md) | [#10463](https://github.com/bfi-finance/bravo-bpm-service/pull/10463) |
| [bravo-branch-service](bravo-branch-service.md) | [#506](https://github.com/bfi-finance/bravo-branch-service/pull/506) |
| [bravo-cnv-service](bravo-cnv-service.md) | [#726](https://github.com/bfi-finance/bravo-cnv-service/pull/726) |
| [bravo-core-proxy-service](bravo-core-proxy-service.md) | [#418](https://github.com/bfi-finance/bravo-core-proxy-service/pull/418) |
| [bravo-customer-service](bravo-customer-service.md) | [#621](https://github.com/bfi-finance/bravo-customer-service/pull/621) |
| [bravo-edoc-service](bravo-edoc-service.md) | [#1525](https://github.com/bfi-finance/bravo-edoc-service/pull/1525) |
| [bravo-inventory-management-service](bravo-inventory-management-service.md) | [#399](https://github.com/bfi-finance/bravo-inventory-management-service/pull/399) |
| [bravo-lms-gateway](bravo-lms-gateway.md) | [#2519](https://github.com/bfi-finance/bravo-lms-gateway/pull/2519) |
| [bravo-onboarding-service](bravo-onboarding-service.md) | [#6328](https://github.com/bfi-finance/bravo-onboarding-service/pull/6328) |
| [bravo-payment-service](bravo-payment-service.md) | [#2661](https://github.com/bfi-finance/bravo-payment-service/pull/2661) |
| [bravo-surveyor-console](bravo-surveyor-console.md) | [#3976](https://github.com/bfi-finance/bravo-surveyor-console/pull/3976) |
| [bravo-user-iam-service](bravo-user-iam-service.md) | [#521](https://github.com/bfi-finance/bravo-user-iam-service/pull/521) |
| [lms-calculation-service](lms-calculation-service.md) | [#647](https://github.com/bfi-finance/lms-calculation-service/pull/647) |
| [lora-task-service](lora-task-service.md) | [#1363](https://github.com/bfi-finance/lora-task-service/pull/1363) |

Each per-repo file carries an *Implementation status* section with the branch link, the
commits, the files touched and a compare view.

What could **not** be implemented in a repository, because it lives in the GitOps deployment
manifests: the unified `tags.datadoghq.com/*` tagging, `DD_ENV` for `bfi-digital-web-api`,
the `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG` and `FEIGN_CUSTOM_LOG_VERSION` values on
`prod-ms-bpm`, the `SERVICE_LOG_DIR` value on `bau-prod-ms-user-iam`, and every
`LOGGING_LEVEL_*` override. Those remain Platform work.

Two findings surfaced only while writing the code, and are now in the relevant files:

- **`lms-calculation-service`** registers its Axios interceptor in the constructor on the
  shared default instance, so one failed call is logged once per `HttpHelper` ever
  constructed. That multiplies the volume, the cost and the credential exposure by an
  unknown factor.
- **`bravo-user-iam-service`** pipes the service through `tee`, so the container's exit
  status is `tee`'s. A crash has been reported to Kubernetes as a clean exit.

## Implementation — pack two, forty-four pull requests

The 53 repositories in [coverage.md](coverage.md) have now been worked through on the same
pipeline: a `fix/logging` branch from `master`, the change, a push, a pull request, and the
findings written into the per-service file below.

Forty-four are open. Nine have no pull request — two because there is no write access to the
repository, four because nothing needed changing, and three because I had mapped them to the
wrong production service and they are not production-active at all.

**The Go half has now been built; the Java half has not.** `go build ./...` passes on all 35
Go repositories in the programme, `gofmt` is clean on every changed file, and
`golangci-lint` runs clean against each repository's own config — except three whose
`.golangci.yml` will not load with golangci-lint 2.11.4 (`backend-dashboard-otrs`,
`bravo-integrity-service`, `bravo-cnv-service`), which therefore have no local lint result.
The two test suites shipped with this work — `pkg/logbody` in `bravo-partnership-service`
and `helper.RedactURL` in `backend-dashboard-otrs` — pass.

That found four defects reading had missed, on top of the five CI caught. See
[What CI said about pack two](#what-ci-said-about-pack-two).

Java is still read-only here, so those pull requests remain unbuilt. Treat CI as the
authority for them.

| Repository | Production service | Pull request | What it changes |
|---|---|---|---|
| [bfi-connect](bfi-connect.md) | `prod-ms-bfi-connect` | [#788](https://github.com/bfi-finance/bfi-connect/pull/788) | stop logging customer phone numbers on every duplicate-check miss |
| [bfi-incentive-api](bfi-incentive-api.md) | `prod-ms-bfi-incentive-api` | [#1698](https://github.com/bfi-finance/bfi-incentive-api/pull/1698) | give the consumer failure a stable message |
| [bfi-rule-engine-service](bfi-rule-engine-service.md) | `prod-ms-rule-engine` | [#67](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67) | mask outbound HTTP bodies before they reach the log stream |
| [bravo-agent-marketing-service](bravo-agent-marketing-service.md) | `prod-agent-marketing` | [#829](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/829) | mask request and response bodies by default |
| [bravo-agent-service](bravo-agent-service.md) | `prod-ms-agent` | [#1632](https://github.com/bfi-finance/bravo-agent-service/pull/1632) | log rejected requests at warn, not error |
| [bravo-assistance-service](bravo-assistance-service.md) | `prod-ms-assistance` | [#200](https://github.com/bfi-finance/bravo-assistance-service/pull/200) | mask request and response bodies by default |
| [bravo-audit-trail-service](bravo-audit-trail-service.md) | `prod-ms-audit-trail` | [#36](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36) | mask outbound bodies, and say what the error was |
| [bravo-auth-service](bravo-auth-service.md) | `prod-ms-auth` | [#258](https://github.com/bfi-finance/bravo-auth-service/pull/258) | pick the log level from the status code |
| [bravo-backoffice-service](bravo-backoffice-service.md) | `prod-ms-backoffice` | [#2781](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781) | mask request and response bodies by default |
| [bravo-collateral-service](bravo-collateral-service.md) | `prod-ms-collateral` | [#420](https://github.com/bfi-finance/bravo-collateral-service/pull/420) | log rejected requests at warn, and close the payload trap |
| [bravo-customer-bff-service](bravo-customer-bff-service.md) | `prod-customer-bff` | [#1216](https://github.com/bfi-finance/bravo-customer-bff-service/pull/1216) | give the masked-field lists a default |
| [bravo-database-catalog](bravo-database-catalog.md) | `prod-database-catalog` | [#41](https://github.com/bfi-finance/bravo-database-catalog/pull/41) | mask request and response bodies by default |
| [bravo-employee-service](bravo-employee-service.md) | `prod-ms-employee` | [#172](https://github.com/bfi-finance/bravo-employee-service/pull/172) | stop writing whole HR records to the log stream |
| [bravo-gen-ai](bravo-gen-ai.md) | `prod-ms-gen-ai` | [#359](https://github.com/bfi-finance/bravo-gen-ai/pull/359) | give the masked-field lists a default |
| [bravo-insurance-service](bravo-insurance-service.md) | `prod-ms-insurance` | [#820](https://github.com/bfi-finance/bravo-insurance-service/pull/820) | log rejected requests at warn, not error |
| [bravo-integrity-service](bravo-integrity-service.md) | `prod-ms-integrity` | [#29](https://github.com/bfi-finance/bravo-integrity-service/pull/29) | mask request and response bodies by default |
| [bravo-inventory-management-system](bravo-inventory-management-system.md) | `bravo-inventory-management-system` | [#232](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232) | stop putting the request body and Authorization header in RUM errors |
| [bravo-journal-service](bravo-journal-service.md) | `prod-ms-journal` | [#297](https://github.com/bfi-finance/bravo-journal-service/pull/297) | log rejected requests at warn, and close the payload trap |
| [bravo-krakend-gateway](bravo-krakend-gateway.md) | `prod-ms-krakend-gateway` | [#387](https://github.com/bfi-finance/bravo-krakend-gateway/pull/387) | mask request and response bodies by default |
| [bravo-krakend-internal](bravo-krakend-internal.md) | `prod-ms-krakend-internal` | [#58](https://github.com/bfi-finance/bravo-krakend-internal/pull/58) | mask request and response bodies by default |
| [bravo-kyc-proxy](bravo-kyc-proxy.md) | `prod-ms-kyc-proxy` | [#726](https://github.com/bfi-finance/bravo-kyc-proxy/pull/726) | give the masked-field lists a default |
| [bravo-kyc-sign-service](bravo-kyc-sign-service.md) | `prod-ms-kyc-sign` | [#118](https://github.com/bfi-finance/bravo-kyc-sign-service/pull/118) | mask request and response bodies by default |
| [bravo-lms-ops-service](bravo-lms-ops-service.md) | `prod-ms-lms-ops` | [#1856](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856) | close the request payload trap |
| [bravo-notification-service](bravo-notification-service.md) | `prod-ms-notification` | [#446](https://github.com/bfi-finance/bravo-notification-service/pull/446) | stop logging signing keys, private keys and bearer tokens |
| [bravo-partnership-provisioning-service](bravo-partnership-provisioning-service.md) | `prod-ms-partnership-provisioning` | [#94](https://github.com/bfi-finance/bravo-partnership-provisioning-service/pull/94) | mask request and response bodies by default |
| [bravo-partnership-service](bravo-partnership-service.md) | `prod-ms-partnership` | [#2367](https://github.com/bfi-finance/bravo-partnership-service/pull/2367) | stop copying MQ and HTTP payloads into the log stream |
| [bravo-pbf-service](bravo-pbf-service.md) | `prod-ms-pbf` | [#125](https://github.com/bfi-finance/bravo-pbf-service/pull/125) | stop reporting "agreement not held here" as an error |
| [bravo-product-service](bravo-product-service.md) | `prod-ms-product` | [#665](https://github.com/bfi-finance/bravo-product-service/pull/665) | log rejected requests at warn, not error |
| [bravo-repeat-order-service](bravo-repeat-order-service.md) | `prod-ms-repeat-order` | [#3503](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503) | log rejected requests at warn, not error |
| [bravo-robot-controller](bravo-robot-controller.md) | `prod-ms-robot-controller` | [#84](https://github.com/bfi-finance/bravo-robot-controller/pull/84) | give the masked-field lists a default |
| [bravo-robot-scrape](bravo-robot-scrape.md) | `prod-robot-scrape` | [#114](https://github.com/bfi-finance/bravo-robot-scrape/pull/114) | report DMS upload failures as errors, not as stdout text |
| [bravo-scheduling-service](bravo-scheduling-service.md) | `prod-ms-scheduling` | [#300](https://github.com/bfi-finance/bravo-scheduling-service/pull/300) | mask outbound HTTP bodies before they reach the log stream |
| [bravo-supplier-service](bravo-supplier-service.md) | `prod-ms-supplier` | [#181](https://github.com/bfi-finance/bravo-supplier-service/pull/181) | mask request and response bodies by default |
| [collection-consumer-service](collection-consumer-service.md) | `prod-ms-collection-consumer` | [#143](https://github.com/bfi-finance/collection-consumer-service/pull/143) | mask request and response bodies by default |
| [doc-renderer-service](doc-renderer-service.md) | `prod-doc-renderer` | [#31](https://github.com/bfi-finance/doc-renderer-service/pull/31) | mask request and response bodies by default |
| [document-hub-service](document-hub-service.md) | `prod-ms-document-hub` | [#92](https://github.com/bfi-finance/document-hub-service/pull/92) | mask request and response bodies by default |
| [gold-service](gold-service.md) | `prod-ms-gold-service` | [#190](https://github.com/bfi-finance/gold-service/pull/190) | mask request and response bodies by default |
| [lora-cdc-foxx-service](lora-cdc-foxx-service.md) | `prod-lora-cdc-foxx-service` | [#3](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3) | move the Datadog credentials and tags out of source |
| [lora-gateway-service](lora-gateway-service.md) | `prod-lora-gateway` | [#1263](https://github.com/bfi-finance/lora-gateway-service/pull/1263) | actually mask outbound bodies, and log them on failure only |
| [lora-partnership-ndf](lora-partnership-ndf.md) | `prod-lora-partnership-ndf` | [#1493](https://github.com/bfi-finance/lora-partnership-ndf/pull/1493) | mask request and response bodies by default |
| [lora-partnership-task-ndf](lora-partnership-task-ndf.md) | `prod-lora-partnership-task-ndf` | [#2126](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126) | mask request and response bodies by default |
| [lora-schema-service](lora-schema-service.md) | `prod-lora-schema` | [#1496](https://github.com/bfi-finance/lora-schema-service/pull/1496) | mask request and response bodies by default |
| [notification-service](notification-service.md) | `prod-ms-notification` | [#122](https://github.com/bfi-finance/notification-service/pull/122) | mask request and response bodies by default |
| [portfolio-management-service](portfolio-management-service.md) | `prod-portfolio-management-service` | [#122](https://github.com/bfi-finance/portfolio-management-service/pull/122) | mask request and response bodies by default |

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

## What CI said about pack two

CI is the only build these changes have had, and it did its job. **Five defects in my own
code**, all found within the hour and all fixed:

| Repository | What CI caught | Cause |
|---|---|---|
| 7 Go repos | `"…/logger" imported and not used` and `logger.JSONScrubberFunc undefined (type zerolog.Logger has no field…)` | `func (e *Env) HTTPClient(logger zerolog.Logger)` — the parameter shadows the package inside that function. Import aliased to `bfilogger` |
| 4 of those again | `undefined: logger` | `Env.Logger()` in the same file also calls `logger.Config` and `logger.New`. The alias has to be applied to those too |
| `gold-service` | `internal/config/http.go:15:1: File is not properly formatted (gofmt)` | Since Go 1.19 gofmt reformats doc comments; a `//nolint:` directive needs a blank `//` line separating it from the prose |
| `bravo-auth-service` | `"fmt" imported and not used` | Removing `fmt.Print(e)` took the last real use. My own grep for remaining uses matched the word inside the comment I had just written |
| `bravo-notification-service` | found before pushing | A comment block was missing its `//` on the second line. Brace-balance checks pass happily on a syntax error like that |

**What is failing that is not mine.** The largest cluster — the jobs named
`Static Analysis - SonarQube` across the shared `call-workflow-passing-data` workflow —
fails at the Codacy coverage step, not on code:

```
error [CodacyCoverageReporter] Invalid configuration: Either a project or account
API token must be provided or available in an environment variable
```

Confirmed identical on `bravo-supplier-service`, `bravo-pbf-service` and
`bravo-journal-service`, whose changes are a struct-tag default, a log level and a log
level respectively. The `Security Container Scan`, `SNYK` and `Codacy Diff Coverage` gates
are the same kind of thing — pre-existing repository gates, not defects introduced here.

Two more that are not code: `bfi-connect`'s Prettier check fails on twenty-five files, all
of them under `src/test/`, none of them touched by this branch; and
`bravo-customer-bff-service` enforces a PR title convention that the original title did not
meet (the PR has been retitled).

### And then the toolchain turned out to be here

On 14 September the "no Go toolchain" premise was found to be wrong — `mise` had Go 1.26.7,
`gofmt` and `golangci-lint` 2.11.4 all along. Running them found **four more defects that
reading had missed**, every one of them mine:

| Found by | Repository | Defect |
|---|---|---|
| `gofmt` | `bravo-audit-trail-service` | comment alignment on the struct tag — the exact file flagged as "most likely to need a formatter pass" |
| `golangci-lint` | `bfi-rule-engine-service`, `bravo-scheduling-service` | `gochecknoglobals` on the masked-field list |
| `golangci-lint` | `bravo-partnership-service` | `gochecknoglobals` on two lookup tables in `pkg/logbody` |
| `golangci-lint` | `bravo-customer-bff-service` | `tagalign` on the two struct tags this work lengthened |

All fixed and pushed. **It also corrected a wrong call made here.** The claim above that the
`Static Analysis - SonarQube` cluster is all a missing Codacy token was drawn from three
repositories and generalised. On `bfi-rule-engine-service` that job actually failed earlier,
at `make lint`, on the `gochecknoglobals` above — CI had been reporting a real defect for a
day and it was explained away.

**Where the 44 stand after those fixes**, at the time of writing:

| | Count |
|---|---:|
| Fully green | 17 |
| Failing only on scanner or coverage gates (SonarQube/Codacy token, SNYK, container scan) | 23 |
| Still running | 3 |
| `bfi-connect`, on the pre-existing Prettier failure in `src/test/` | 1 |

**No compile or lint failure from this work remains open.**

**Read this as the argument for building before merging, not against it.** Every one of the
five defects was invisible to reading and to the brace, paren, import-order and line-length
checks that were the only tools available here.

## Per-repo recommendations

Ordered by billable impact. **This table is the first twenty only** — the other 53 are in
the pack-two table above, each with its own file and pull request, and ranked by production
volume in [logging-cost.md](logging-cost.md) §5.

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

Every file also carries two standard sections, the same shape everywhere, so a squad can
check their own service in a minute:

- **Request and response bodies in Datadog** — what that service captures today, what it
  cannot capture, which Datadog feature replaces it, and what to do. In
  [lms-calculation-service.md](lms-calculation-service.md) the detail sits in item 4a and the
  section summarises it.
- **Service identity in Datadog** — measured log and trace volume over seven days, whether
  the log name and the trace name agree, and the exact steps to fix it if they do not.

## Telemetry coverage, production, seven days

| | Count |
|---|---:|
| Service names sending logs | 78 |
| Service names sending traces | 101 |
| Sending both, as Datadog sees them today | 52 |
| Sending both, once the eight name mismatches are fixed | **59** |
| Tracing but sending no logs | **42** |
| Logging but sending no traces | **18** |

This corrects an earlier figure of "30 of 71 send both, two services have different names".
That came from a two-day window and an incomplete APM service list. The direction was right;
the counts were low, and two of the twelve services listed there as silent were not silent —
they were logging under a different name.

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
