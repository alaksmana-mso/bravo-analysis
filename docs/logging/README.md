# Logging analysis

Written 12 September 2026. Second pass 13 September 2026.

Cost data is GCP billing through FinOps. Log evidence is Datadog production. Code evidence
is all 152 repos under `squads/`, pulled to `master` on the day of writing — 149,729 files
scanned — plus 36 more cloned since.

**73 repositories analysed. On 17 September 2026: 1 service pull request merged, 47 open, 16 closed on SRE's guidance; the Java wrapper ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)) is merged, the Go wrapper ([bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175)) is open, the Boot 2.7 bridge ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) is closed; the manifest pull request ([app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820)) carries two SRE approvals; 80 files in this folder.** The code half
of the programme is written; what is left on it is review, merge, and one publish step.

## What changed on 15–17 September

- **The Java wrapper merged.** [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122) landed on `master` on 16 September
  (`dfeb6ac`): `bfi-logging-core` and `bfi-logging-spring-boot-starter` 0.1.0, with the
  five gaps this programme found fixed on the branch before merge. **It is not published.**
  `bfi-java-pkg` releases a module only through a manual *Deploy Package* workflow, which
  last ran on 30 January 2026 and has not run for the new modules. Until Platform runs it
  (core, then starter) no service can add the dependency. That is now the first Java item
  in the table below.
- **Java is one layer again.** [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123), our fix to `bravo-lib-logging` for the 14
  Boot 2.7 repositories, was closed on 16 September so that one library carries the
  standard. Those 14 repositories keep their per-service pull requests and manifest
  switches, and need a Boot 3.3 upgrade to reach the starter; the 19 on Boot 3.3+ (one on
  4.1.1, checked) adopt it once published; `bravo-insurance-service` leaves 3.2.11 first.
- **The first service pull request merged**: `bravo-inventory-management-service#399`, by
  its squad, on 15 September.
- **SRE approved the manifest change.** [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) has two approvals (15 September) and
  one condition: each impacted service's SA confirms first, because the change restarts
  19 services. That confirmation is the user's next step, not ours.
- **The bpm squad reviewed `bravo-bpm-service#10463`** on 16 September — four comments, all
  about control: a flag for the sanitizer, the cap in `application.yaml`, whether inbound
  payloads can still be seen, and what `loggerLevel: basic` leaves. Answered on the pull
  request and in the code on 17 September ([bravo-bpm-service.md](bravo-bpm-service.md)).
- **CI re-read on 17 September**: of 47 open service pull requests, 11 are fully green and
  36 fail only on gates that were red before this work. Two `lora-*` branches were
  refreshed from `master` to clear a pre-existing test failure and a cancelled job.
- **Codacy's review of every open pull request was answered on 18 September.** 91 threads on
  38 pull requests: 63 fixed in a commit on the branch (each thread names it), 14 pointed at
  code that had already been reverted or fixed on 14 September, 14 declined with the reason in
  the thread. Three were real defects this pass would otherwise have shipped: an out-of-scope
  variable in `bfi-digital-web-api`, a reserved `message` key in `bravo-robot-scrape`'s
  logging call that would have raised at runtime, and validation *values* logged by
  `bravo-journal-service`. One Codacy suggestion was tried and backed out because the squad's
  own test pins the behaviour (`bravo-pbf-service`). `bravo-audit-trail-service` still carried
  a default masked-field list the 14 September revert had missed; it is gone now. Every thread
  is replied to and resolved; each per-service file records the round under *Implementation
  status*.

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
- **The Feign mechanism the deck names is real, on, and worth about a tenth of what was
  claimed.** `bpm`'s manifest turns on a hand-written Feign logger that writes bodies at
  INFO — which is why no DEBUG line or `END HTTP` marker ever appeared. It is 89% of the
  service's log bytes, about 22 GB a day; at contract and Cloud Logging rates that is
  roughly Rp 5–8M a month, not Rp 50–90M.
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
- **Go masking is a deployment setting, and in production it is often set to nothing.**
  Eight services log bodies with every `*_JSON_MASKED_FIELDS` set to `""` in
  `values-prod.yaml`; eight run at `LOGGER_LEVEL=debug`; in one repository the scrubber
  call is commented out entirely, under a comment claiming the code is non-production
  only. The wrapper itself never masked a number or a list.
- **Six production services emit no logs and no traces at all.** Not quiet — invisible.
- Three broken CI gates — a missing Codacy token, a broken Codacy installer and a SonarQube
  new-code baseline — **red-flag pull requests for reasons unrelated to their content**.

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
93.6% unparsed, 64% of it from five services emitting unparsed bodies and repeated errors —
would move the waste from Cloud Logging to Datadog and cost more. Clean first, then enable
on a stream half the size.

**The contract puts a number on that (added 14 September 2026).** SRE shared the signed
Datadog order (`Q-849776`, 1 October 2025 to 30 September 2027) and the 2025 GCP billing
sheet. Logs are a small line in a large contract: the committed log lines are **150M
indexed events a month at 3- and 7-day retention and 256 GB of ingestion a month**, worth
$210 of the $14,030 committed each month. Datadog's own usage metric says we are sending it
**about 240M events and 40 TB a month** — the events 1.6× the commitment, the bytes
**150×**, billed as overage at $0.10/GB. The gate is not there because Datadog logging is
expensive per line; it is there because the ingestion commitment was sized for a clean
stream and we are shipping a dirty one at 150 times that size. Detail and the reconciliation
SRE still needs to do are in [logging-cost.md](logging-cost.md) §1a.

The one exception is Error Tracking, which derives from telemetry already flowing and adds
no ingest. Turn that on now.

## Do these first

| # | Action | Owner | Effort | Datadog cost |
|---|---|---|---|---|
| 1 | Fix `HttpHelper.ts` and rotate the leaked secret | Contract Collateral | 2 h | none |
| 2a | **Publish the merged [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), then adopt it in `bravo-bpm-service` first.** Merged 16 September; nothing can depend on it until Platform runs the manual *Deploy Package* workflow for `logging-core` and then `logging-starter`. bpm is Boot 3.5.16 with no shared logging library today, and the 76 KB Feign lines that make it the largest log producer in Bravo | Platform + S&U | review + 1 d | reduces |
| 2 | **Merge [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820)** — approved by SRE on 15 September, waiting on each service's SA to confirm the rollout restart; nine production services off `debug`, five given a masked-field list, three to failure-only bodies, onboarding's request bodies off, `bpm`'s sharia header logging (with `Authorization`) off, two Java packages off `DEBUG`. 20 `values-prod*.yaml` files, one variable each; the reasoning is [deployment-proposal.md](deployment-proposal.md) | SRE + owning squads | review only | reduces |
| 3 | Exclusion filter and 7-day retention on non-prod projects | Platform | 1 d | none |
| 4 | Fix the monitors that query service names that do not exist | SRE | 2 d | none |
| 5 | **Fix CONFINS log re-ingestion** — the Datadog Agent re-reads dead pods' files from a shared `/var/log` on every rollout; ~90% of that service's volume, about a third of all indexed prod log events ([confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md), corrected 14 Sep) | SRE | 1 d | **reduces** |
| 6 | Ask what Coralogix is for | Architecture | 1 d | none |
| 7 | **Fix Remote Configuration** — failing on 13 services, ~91k failed polls a week | SRE | 1 d | none |
| 8 | Turn on `DD_TRACE_HEADER_TAGS` for correlation IDs | SRE | 1 h | none |
| 9 | **Rotate the Google Chat webhooks** logged by `bau-prod-ms-otrs-report` | Platform / security | 1 d | none |
| 10 | **Fix the three CI gate faults** — missing Codacy token, broken `codacy-cli.sh`, wrong SonarQube new-code baseline | Platform | 2 h | none |

None of these increases Datadog spend. Item 2 replaces what used to read "check the prod
deployment manifests": SRE gave access to them on 14 September 2026, they have been read
for every service in this programme, what they say is in each per-service file under
**In the production deployment**, and the changes they need are raised as one pull request
on `fix/logging` — not merged.
Item 9 is a live credential exposure; item 10 is an hour that unblocks six weeks of squad
work.

## Coverage — all 53 remaining repositories are now done

**[coverage.md](coverage.md)** has the estate map and the results of the second pack.
Headline numbers: 122 production services, **52 with no source we can see**, and
`confins-prod-ms-lms-ar-be` alone at 29% of all production log volume.

**Corrected 14 September 2026.** That 29% is mostly not the service's own output. About 90%
of it is the Datadog Agent re-reading a month of dead pods' log files at every rollout, on a
shared `/var/log` path, and the entries are full HTTP bodies, not blank lines. It is an SRE
collection fix, not an ownership problem — [confins-prod-ms-lms-ar-be-findings.md](confins-prod-ms-lms-ar-be-findings.md). Getting an owner for the CONFINS and Treasury
families still matters for the body logging itself and for the 52 services without source.

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
**And Java can be compiled here too — the third correction of this claim.** `/usr/bin/java`
is the macOS stub, but `mise x java@temurin-17 maven@3.9` installs a JDK and Maven in two
minutes, and the GCP artifact-registry wagon in the poms picks up the machine's gcloud
credentials, so the private `bravo-lib-logging` resolves. On 14 September 2026 every Java
repository with a `.java` change on its branch was compiled: **22 of 22 compile**.
Unit tests were run on 12 of them: 12 pass (bfi-connect (0 tests), bfi-insurance-api (4391 tests), bravo-agent-service (2181 tests), bravo-approval-engine-service (388 tests), bravo-bpm-service (18306 tests), bravo-collateral-service (1530 tests), bravo-core-proxy-service (826 tests), bravo-employee-service (176 tests), bravo-insurance-service (947 tests), bravo-journal-service (934 tests), bravo-product-service (330 tests), bravo-repeat-order-service (5559 tests)).
The wrapper pull requests are built too: `bfi-go-pkg#175` (`go test`, lint clean),
`bfi-java-pkg#123` (`mvn verify`, 74 tests, 0 failures — closed 16 September) and
`bfi-java-pkg#122` (`mvn verify`, 61 + 42 tests, 0 failures — merged 16 September). CI on
each pull request is still the authority, but "not compiled" is no longer true of anything
in this programme.

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

Forty-four were opened. Nine have no pull request — two because there is no write access to
the repository, four because nothing needed changing, and three because I had mapped them to
the wrong production service and they are not production-active at all.

### Sixteen of the forty-four were closed on 14 September 2026, on SRE's guidance

SRE reviewed the approach and set two things straight, both of which change what belongs in
a per-service pull request:

1. **Masked fields are a deployment setting, not a code default.** The Go wrapper already
   reads `HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS`, `HTTP_SERVER_RESPONSE_…`,
   `HTTP_CLIENT_REQUEST_…` and `HTTP_CLIENT_RESPONSE_…` from the environment; SRE sets them
   per service and per environment in `app-deployment` (`values-prod.yaml`), because not
   every service handles PII and each one needs its own field list and nested paths.
   [backoffice's](https://github.com/bfi-finance/app-deployment/blob/master/backoffice/values-prod.yaml#L218-L221)
   is the pattern. Giving every service the same default list in its config struct was the
   wrong layer — and, it turns out, would have done nothing in production for most of them,
   because the manifests already set those variables explicitly (often to `""`), and an
   explicit value beats a struct default every time.
2. **Fix it once in the wrapper, not once per service.** Both shared libraries had a real
   masking gap that no per-service change could close:
   [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) — `JSONScrubber`
   masked strings only, so a NIK, phone number or salary sent as a JSON number went through
   (open); and in `bravo-lib-logging` `FeignClientFilter` logged every Feign request and
   response body **unmasked**, the sensitive-key match was case-sensitive (so
   `Authorization` slipped past `authorization`), and nothing capped body size. Our fix for
   that, [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123), was
   closed on 16 September in favour of the new starter — see the note after this list.

**Java now has one target library.** On 14 September a colleague opened [bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122): two new
modules, `bfi-logging-core` and `bfi-logging-spring-boot-starter`, for Spring Boot 3.3 and newer
(on 3.2 the service would start and log nothing; the starter fails fast there — §2a of body-visibility.md).
They are the schema-and-volume layer this programme was missing — single-line JSON with
`level`, `service`, `trace_id`; an 8 KB message cap and stack-trace cap that keep Java lines
under the 16 KB container-runtime split; request logging off by default; async, dedupe,
framework loggers at WARN. They did not touch outbound bodies or run the PII regex over the
message, so on 15 September we pushed five commits onto that branch: a Feign logger that
writes one line per call and never a header (bodies opt-in, masked, capped), the PII pass on
every `message`, JSON parsing of captured bodies so the key deny-list reaches their fields,
the READMEs, and the Boot 3.2 startup check. **It merged on 16 September**, and #123 — the
matching fix to the old library — was closed the same day so that the estate maintains one
library. The rule from here: **every Java service moves to the starter. The 19 on Boot 3.3+
(20 with `bravo-insurance-service`, once it leaves 3.2.11) can do so as soon as Platform
publishes it; the 14 on Boot 2.7 keep their per-service fixes and manifest switches, and
their route to masked, capped, single-line logs is a Boot 3.3 upgrade.** Publishing is a
manual *Deploy Package* run that has not happened yet. Full assessment in [body-visibility.md](body-visibility.md) §2a.

So: the commit that added a struct default was reverted on every branch that had one.
**Sixteen branches were left identical to their base and their pull requests closed**, each
with a comment saying why. **Nine were kept**, because they also carry the code the
deployment setting depends on — the scrubber actually wired to the field list the
environment provides — or a log-level fix. Two (`bravo-scheduling-service`,
`bfi-rule-engine-service`) had a hardcoded field list in `main.go`; that is replaced by the
standard environment variables, which `app-deployment` does not yet set for them.

What every service's production manifest actually says, and the diffs SRE and the squads
need to apply, are in **[deployment-proposal.md](deployment-proposal.md)** and in each
per-service file under *In the production deployment*. Those diffs were **not** applied by
this work — a change to a production manifest is SRE's call.

**Both halves have now been built.** `go build ./...` passes on all 35
Go repositories in the programme, `gofmt` is clean on every changed file, and
`golangci-lint` runs clean against each repository's own config — except three whose
`.golangci.yml` will not load with golangci-lint 2.11.4 (`backend-dashboard-otrs`,
`bravo-integrity-service`, `bravo-cnv-service`), which therefore have no local lint result.
The two test suites shipped with this work — `pkg/logbody` in `bravo-partnership-service`
and `helper.RedactURL` in `backend-dashboard-otrs` — pass.

That found four defects reading had missed, on top of the five CI caught. See
[What CI said about pack two](#what-ci-said-about-pack-two).

The Java pull requests were compiled on 14 September 2026 once a JDK turned out to be a
`mise x` away (22 of 22 compile; 12 of the 12 test suites run pass — see
each file's verification note). Treat CI as the authority for them still.

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

## What CI said about pack two

CI is the only build these changes have had, and it did its job. **Five defects in my own
code** were caught here, all fixed. Four more were found afterwards by tools that turned out
to be installed on this machine, and one more by a test suite — see below.

| Repository | What CI caught | Cause |
|---|---|---|
| 7 Go repos | `"…/logger" imported and not used` and `logger.JSONScrubberFunc undefined (type zerolog.Logger has no field…)` | `func (e *Env) HTTPClient(logger zerolog.Logger)` — the parameter shadows the package inside that function. Import aliased to `bfilogger` |
| 4 of those again | `undefined: logger` | `Env.Logger()` in the same file also calls `logger.Config` and `logger.New`. The alias has to be applied to those too |
| `gold-service` | `internal/config/http.go:15:1: File is not properly formatted (gofmt)` | Since Go 1.19 gofmt reformats doc comments; a `//nolint:` directive needs a blank `//` line separating it from the prose |
| `bravo-auth-service` | `"fmt" imported and not used` | Removing `fmt.Print(e)` took the last real use. My own grep for remaining uses matched the word inside the comment I had just written |
| `bravo-notification-service` | found before pushing | A comment block was missing its `//` on the second line. Brace-balance checks pass happily on a syntax error like that |

### And then the toolchain turned out to be here

On 14 September the "no Go toolchain" premise was found to be wrong — `mise` had Go 1.26.7,
`gofmt` and `golangci-lint` 2.11.4 all along, and Node too. Running them found **four more
defects that reading had missed**, every one of them mine:

| Found by | Repository | Defect |
|---|---|---|
| `gofmt` | `bravo-audit-trail-service` | comment alignment on the struct tag — the exact file flagged as "most likely to need a formatter pass" |
| `golangci-lint` | `bfi-rule-engine-service`, `bravo-scheduling-service` | `gochecknoglobals` on the masked-field list |
| `golangci-lint` | `bravo-partnership-service` | `gochecknoglobals` on two lookup tables in `pkg/logbody` |
| `golangci-lint` | `bravo-customer-bff-service` | `tagalign` on the two struct tags this work lengthened |

All fixed and pushed.

Node also turned out to run **`prettier-plugin-java`**, so the Java estate is not as
unverifiable as these documents claimed. Every Java file this programme changed now parses
and is format-checked against each repository's pinned `prettier-java` settings. Java still
cannot be *compiled* or unit-tested here — `/usr/bin/java` is the macOS stub — but "checked
brace balance by hand" was never the best available.

### Every failing job, checked one at a time

An earlier version of this section said the `Static Analysis - SonarQube` cluster was all a
missing Codacy token. **That was drawn from three repositories and generalised to twenty**,
and it was wrong: on `bfi-rule-engine-service` the job died earlier, at `make lint`, on the
`gochecknoglobals` above. CI had been reporting a real defect for a day and it was explained
away.

So every failing job was then fetched and read individually. **27 failing jobs across 19
repositories:**

| Cause | Jobs | Mine? |
|---|---:|---|
| Dependency and container CVE gates — SNYK on the dependency tree, Trivy on the base image (`musl`, `zlib` and friends) | 17 | No |
| Codacy coverage reporter has no API token | 5 | No |
| SonarQube quality gate — `bravo-insurance-service`, 83.8% coverage on new code and "9855 new lines" against a 2000 limit, for a pull request of **+10/−4 in one file** | 1 | No |
| Codacy CLI installer broken — `bravo-employee-service`, `codacy-cli.sh: line 65: fatal: command not found` | 1 | No |
| `golangci-lint` — `bravo-gen-ai`, `goconst` in `internal/store/pg/session_store.go` | 1 | No |
| Prettier — `bfi-connect`, 180 files under `src/main/java` | 1 | No |
| **Maven test failure — `bfi-incentive-api`** | **1** | **Yes** |

One caveat on that table: **a single job can fail at more than one step**, so counting one
cause per job is already a simplification. `bfi-incentive-api`'s `Static Analysis - SonarQube`
job is the example — Maven's tests failed *and* the Codacy step then failed for want of a
token. The question that matters is not which step failed last but whether any step failed
on code written here, and after reading all 27 logs the answer is: one did.

The CVE gates have a structural answer as well as a read one: **not one of the 65 branches
in this programme touches a `pom.xml`, `go.mod`, `go.sum`, `package.json` or `Dockerfile`.**
A dependency or base-image CVE cannot have been introduced by a change that adds no
dependency and rebuilds no image.

The two that needed the most work to rule out:

- **`bravo-gen-ai`.** A `golangci-lint` failure looks like mine by default, and the first
  sweep marked it so. It is not. The `goconst` pair is in `session_store.go` and
  `session_store_test.go`, both byte-identical to `master`; this branch changes two lines of
  `internal/config/config.go`, a different package, and `goconst` counts per package. It
  does not reproduce locally because `goconst` reports at whichever occurrence it reaches
  first, and macOS and Linux walk the directory in different orders — on macOS it lands on
  the test file, which this repository's config excludes from reporting.
- **`bfi-connect`.** The earlier claim here, "twenty-five files, all under `src/test/`, none
  touched by this branch", was wrong three times over: it is **180** files, they are under
  **`src/main/java`**, and the file this branch touches **is one of them**. It is still not
  this branch's doing — running `prettier-java` over the file before and after the edit
  produces the identical set of twenty violation hunks, all import ordering. The job was red
  on `master`.

**One real defect was mine, and only a test could have found it.** `bfi-incentive-api`
replaced an interpolated DTO with `agreementStatusUpdate.getAgreementNumber()`. That
variable is initialised to `null` and is still null when the failure was the deserialisation
itself — so the call threw a `NullPointerException` from inside the catch block, in place of
the `AmqpRejectAndDontRequeueException` the RabbitMQ listener is contracted to throw. That
changes what the broker does with the message: a behaviour regression, not a red mark.
`AgreementStatusUpdateDailyConsumerTest.test_Receive_WhenException` caught it, because its
first parameter case is a null response. Fixed in `2a738ed6` and pushed.

It is worth being precise about why this one got through when the Go defects did not: a Go
compiler was sitting on the machine unused, and — as was found a day later — so was a
JDK, one `mise x` away. This change could have been tested before pushing and was only
read. Reading does not catch a null dereference.

### Where the 47 open service pull requests stand on 17 September

Re-polled on 17 September 2026, every red job classified by name:

| | Count |
|---|---:|
| Fully green | 11 |
| Failing **only** on gates that were red before this work — SNYK and container-image CVEs (22 jobs), SonarQube new-code gates (18), Codacy coverage upload without its token (10), `bfi-connect`'s pre-existing Prettier drift (1) | 36 |
| Failing on anything written here | **0** |

Two of the 36 were red on a *unit-test* job and were looked at one by one. `lora-task-service`
failed on `TestGetUserProfilePartnershipOnly` in a package this branch does not touch; `master`
fixed that test on 16 September, so the branch was refreshed from `master` on 17 September and
the package passes locally. `lora-partnership-ndf`'s test job was **cancelled**, not failed;
that branch was refreshed the same way to re-run it. Merged: `bravo-inventory-management-service#399`,
15 September, by its squad.

### Where the 44 pack-two pull requests stood before SRE's review

*(Counts below are as of the CI read on 14 September, before 16 of the 44 were closed — see above. Of the 28 still open, none fails on anything written here.)*

Re-polled after the fixes above (last poll: evening of 14 September, after the
`bfi-insurance-api` test fix on `878035cc4`), with every failing job's log read:

| | Count |
|---|---:|
| Fully green | 28 |
| Failing **only** on dependency, container, coverage or quality gates that were red before this work (SonarQube, SNYK, Trivy container scan, and `bfi-connect`'s pre-existing Prettier drift) | 15 |
| Closed before the poll (`bravo-assistance-service`) | 1 |
| Failing on anything written here | **0** |
| Still running | 0 |

`bfi-insurance-api` and `bravo-scheduling-service` are now fully green; `bfi-incentive-api`
fails only on SonarQube and the container scan.

`bfi-incentive-api` is the one to check if you want to see the fix land: **1806 tests run,
0 failures, `BUILD SUCCESS`** on head `2a738ed6`. That job is still red, but now only at the
Codacy coverage step, for want of the same API token that stops it in five other
repositories.

**No compile, lint, format or test failure from this work is still open** — and this time
that sentence rests on reading all 27 logs rather than on three of them.

**Read this as the argument for building before merging, not against it.** Ten defects in
this work were invisible to reading: five caught by CI, four by the Go tools that were here
all along, and one by a test suite that could not be run here at all.

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

## Three things this analysis could not check — and what they said once checked

All three were opened up on 14 September 2026, when SRE gave access to `app-deployment` and
`bfi-app-deployment`, the signed Datadog order and the 2025 billing sheet.

- **Deployment manifests.** Read for every service in this programme; what each one sets is
  in its file under *In the production deployment*, and the changes they need are diffs in
  [deployment-proposal.md](deployment-proposal.md). **On Feign:** `bpm/values-prod.yaml` sets
  `ENABLE_FEATURE_CONFIG_FEIGN_CUSTOM_LOG=true` and `FEIGN_CUSTOM_LOG_VERSION=3`, which swaps
  Feign's DEBUG logger for a hand-written one that writes every request and response body at
  INFO. That is why the estate has zero DEBUG lines and zero `END HTTP` markers while bodies
  were being logged the whole time. Measured in Datadog over 24 hours: 86,630 body entries,
  6.65 GB of the service's 7.47 GB of indexed message bytes, 99.99% of them cut at the
  76,800-byte message limit; ingestion-side the service takes about 25 GB a day — the whole
  contract's monthly log-ingestion commitment every ten days. **On the three payload
  filters:** `onboarding` sets its Commons filter to `OFF` (so the 64 KB request-body
  logging its code enables is off in production), `agency` sets it to `INFO`,
  `approval-engine` and `core-proxy` set nothing — and send no logs to Datadog at all. The
  one manifest repo still unread is `confins-app-deployment`: the URL returns 404 to the
  token used here, so the CONFINS services stay outside this analysis.
- **Datadog's own filtering.** Narrowed, not closed. No manifest hides DEBUG for the services
  above, and Datadog still indexes zero `status:debug` lines in seven days. One manifest
  does put a Java package at DEBUG in production (`customer`'s CONFINS client) and nothing
  from it is indexed either. What remains is Datadog's own `Logs → Configuration → Indexes`
  page — a one-minute check for someone with the admin role. The ingestion-to-indexed
  ratio, about 3× for `prod-ms-bpm` and about 40× for `prod-ms-assistance`, has the shape
  of a per-service exclusion filter.
- **Our Datadog contract rates.** In hand: order `Q-849776`, 1 October 2025 to 30 September
  2027, $14,030 a month committed, of which log ingestion is 256 GB a month at $0.10/GB and
  log events 150M a month at $1.06–1.27 per million; overage $0.10/GB and $1.59–1.91 per
  million. Datadog's own usage metric says about 1.3 TB a day ingested — 150× the
  commitment. The 2025 billing sheet puts Datadog at Rp 5.62bn for the year (Rp 3.66bn of
  it a prior-order payment in May) against Cloud Logging Rp 1.78bn and Coralogix Rp 2.77bn.
  The detail is in [logging-cost.md](logging-cost.md) §1a and
  [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §0. August Datadog spend,
  Rp 110.6M, remains the monthly baseline to protect.
