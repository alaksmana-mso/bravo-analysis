# Bravo and LORA — quick wins and actions for the next 30 / 60 / 90 days

Compiled 2026-09-18 from every recommendation, quick win and next step written in
`bravo-analysis/docs` and `lora-workspace/docs`. Nothing here is new. Each line points
at the document that says it, so the reasoning can be checked there.

## How to read this

- **One item, one line, one owner.** Where a doc names an owner and an effort, both are kept.
  Where several docs say the same thing, it appears once with every source.
- **Phasing follows the source docs.** Five Bravo docs carry their own Days 0–30 / 31–60 / 61–90
  plans (cost, delivery, observability, people, testing). `workflow-gap.md` and `option-summary.md`
  carry their own 30-day lists. On the LORA side, `production-findings/README.md` orders work as
  "Do first / Then / Structural", `testing.md` and `testing-gates.md` are phased by weeks, and
  `pipelines.md` by Phase 0 (weeks 1–4), Phase 1 (months 2–3), Phase 2 (months 4–6). The logging
  programme is gated on two numbers, not dates.
- **Capacity is the constraint.** The Bravo plans assume about 25 person-days a month from Squad
  S&U and about 10 from Platform/SRE (`bravo-people.md:387`). Section 8 shows the 0–30 day load
  against those numbers. It does not fit. That is the first thing to decide.
- **Sources.** `B:` means `bravo-analysis/docs/`, `L:` means `lora-workspace/docs/production-findings/`
  unless another path is given. `file:line` is the line the item was read from.

---

## 0. This week

These either expire, are a live security exposure, or take under an hour.

### Bravo

| # | Action | Owner | Effort | Source |
|---|---|---|---|---|
| 1 | **Camunda RCE, ten ordered steps.** Rotate `INTERNAL_SERVICE_KEY` first. Then: rotate the credentials in `bravo-e2e-test/cypress.config.js`; pull ingress and APM logs for `POST /engine-rest/deployment/create` over 2026-05-23 to 06-30; confirm whether `/engine-rest/**` is reachable from outside; register a `ProcessEngineAuthenticationFilter`; purge the 61 injected definitions after preserving evidence; rotate everything reachable from the pod; scope lateral movement; close `/camunda/**` `permitAll`; confirm whether this was a sanctioned test, else open an incident. | Bravo + Security | this week | `B:SECURITY-FINDING-camunda-rce.md:109–124`, `B:compare.md:328`, `B:option-summary.md:178` |
| 2 | Fix `HttpHelper.ts` in `lms-calculation-service` and rotate the API secret it prints to production logs. | Contract Collateral | 2 h | `B:logging/README.md:134`, `B:logging/logging-cost.md:572` |
| 3 | Rotate the Google Chat webhooks logged by `bau-prod-ms-otrs-report`. Find someone with write access to that repo. | Platform / Security | 1 d | `B:logging/README.md:143`, `B:logging/sre-datadog-recommendations.md:996` |
| 4 | Delete every `\|\| true` in `OPERATION_PLATFORM.yml`. Then open the Actions tab and check whether the weekly Gherkin cron has fired since 2023. | QA | 1 h + 5 min | `B:bravo-testing.md:568`, `B:compare.md:316` |
| 5 | Give the unowned payload table in `bravo-edoc-service` an owner, a size and a retention policy. | S&U / EM | this sprint | `B:logging/body-visibility.md:403` |
| 6 | `prod-ms-partnership` fails to decrypt a bank account holder name and proceeds in plaintext, 639 times in two days. Needs an owner from Digital Partnership now, not from the logging programme. | Digital Partnership | — | `B:logging/coverage.md:245` |

### LORA

| # | Action | Owner | Effort | Source |
|---|---|---|---|---|
| 7 | **Create the four span/log metrics and the NIK scanner rule.** Spans retain 30 days and cannot be backfilled, so every week of delay is trend lost. Metrics: `cost_bucket` tag; workflow starts and completions; distinct `@WorkflowID` with `@Attempt:>10`; sensitive-data scanner rule for NIK/NPWP. | Platform | S | `L:README.md:159`, `L:monthly-report.md:218–223`, `L:observability.md:474` |
| 8 | Name one owner for the monthly report. Hold the working-day-5 review this month: every red number gets an owner and a ticket. Publish `reports/2026-09.md` by hand on working day 3 of October. | Platform lead | 30 + 90 min | `L:README.md:160`, `L:monthly-report.md:265–268` |
| 9 | Run `temporal workflow count` for `Running`, then again with `StartTime` older than a month. Two commands. Decides whether the never-terminating half is accumulating. | On-call | minutes | `L:cost.md:1368`, `L:reports/2026-08.md:92` |
| 10 | Run `temporal operator namespace describe` and confirm retention is longer than the longest open workflow. | On-call | 5 min | `L:cost.md:1372`, `L:README.md:231` |
| 11 | Un-mute activity-error monitor 17418444: remove the wedged-loan exclusion, give it an owner and a runbook. Triage LPW Success Rate monitor 16306195, which is PagerDuty-routed and sitting in Alert. | Platform / on-call | S | `L:README.md:162`, `L:observability.md:605`, `L:observability.md:750` |
| 12 | Fix the CSP allowlist. One header change. About 17,600 violations a week block `/subscribe/tasks`, `/tasks/query` and `blob:` workers. | LBOFE | S | `L:delivery.md:212`, `L:README.md:153` |

### Both platforms

| # | Action | Owner | Effort | Source |
|---|---|---|---|---|
| 13 | **Set the standing allocation for each platform and name the bus factor.** Every other plan assumes this capacity. It is a meeting. | Leadership | a meeting | `B:bravo-people.md:387`, `B:compare.md:363` |
| 14 | Ask what Coralogix is for. Rp 253.3M a month, flat since February, a third log platform. | Architecture | 1 d | `B:logging/README.md:140`, `B:compare.md:359` |
| 15 | Rotate the credentials in `bravo-e2e-test/cypress.config.js` and move them to environment variables. Listed here again because the LORA docs raise it independently of the RCE. | QA | — | `L:people.md:768`, `B:bravo-testing.md:578` |

---

## 1. Days 0–30

### 1.1 Bravo — engine end-of-support and the platform decision

The one firm recommendation in the option pack: fund Decision A now and do not let it wait for
Decision B (`B:option-summary.md:155`).

| Action | Owner | Effort | Source |
|---|---|---|---|
| **Fund Option 1, Path B**: forked engine plus Spring Boot in one change. | Steering / CTO | 18–33 eng-days, Rp 45–125M, no licence | `B:option-summary.md:155`, `B:option-1.md:350`, `B:compare.md:341` |
| Run the schema-log diagnostics in SIT, UAT and PROD independently. Four SQL queries. The one finding that can change the migration plan. | Bravo | hours | `B:option-summary.md:179`, `B:option-1.md:200` |
| Run `SELECT type_, COUNT(*) FROM act_ru_variable GROUP BY type_` before any date is committed. | Bravo | hours | `B:option-1.md:212` |
| Land the six-item pre-decision cleanup: `CollectionUtil` swap, delete `instance-tab-modify.js`, drop `camunda-bpm-mockito`, `hibernate-types-55`, the Jaeger stack, `OldSecurityConfig.java`. | Bravo | 1–2 d | `B:option-summary.md:180`, `B:option-1.md:166–171` |
| Set and publish a Bravo horizon, even provisionally. Selects the bridge variant. | Steering / CTO | a decision | `B:option-summary.md:181` |
| Answer the support-agreement question. If the answer may be yes, open the CIB seven enquiry now. Selects the fork. | Architect + Procurement + Risk | — | `B:option-summary.md:182`, `B:option-1.md:104` |
| Start the LORA gap inventory: every Bravo delegate, status, assignment rule and approval path mapped to a LORA ProcessStep, a new one, or "drop". Useful under every option. | LORA + Bravo | 1–2 eng-months, starts now | `B:option-summary.md:183`, `B:option-3.md:104`, `B:bravo-unified-legacy-to-unified.md:36` |
| Confirm Temporal commitment headroom before the ~March 2027 renewal. | Platform + FinOps | — | `B:option-summary.md:185`, `L:cost.md:1389` |
| Open questions to close: are the six Cockpit capabilities in use (Operations); what deployment window exists (Release management); CIB seven property prefix and webapp path (Engineering spike, hours). | as named | hours each | `B:option-1.md:331–334` |

### 1.2 Bravo — cost (`bravo-cost.md` Days 0–30)

Ordering rule: money that is configuration comes before money that is migration (`B:bravo-cost.md:272`).

| Action | Owner | Effort | Source |
|---|---|---|---|
| **Cut the Cloud Logging bill.** Non-prod exclusion filter and 7-day retention (1 d). Cloud SQL audit and slow-query logs off in non-prod (2 h). VPC flow-log sampling to 10% (1 h). Worth Rp 81–105M a month. | Platform | ~1.5 d | `B:bravo-cost.md:257`, `B:logging/README.md:137`, `B:logging/logging-cost.md:570–571`, `B:compare.md:359` |
| Check the deployment manifests for Feign log levels (1 h). It decides the next two. Then remove `loggerLevel: full` in all six repos (3 d) and drop `CommonsRequestLoggingFilter` payload logging in onboarding and the three default-DEBUG repos (2 d). | S&U + Platform, then each squad | 5 d | `B:logging/logging-cost.md:576–578`, `B:bravo-cost.md:257` |
| Log exceptions as one structured event; enable multi-line stack-trace aggregation cluster-wide. | S&U; Platform | 3 d; 1 d | `B:bravo-cost.md:257`, `B:logging/logging-cost.md:575` |
| Open `bravo-project-nonprod`: a service-level breakdown and a list of what runs and why. 31% of Bravo spend, never examined. Worth up to Rp 573.5M a month. | FinOps + Platform | 2 d | `B:bravo-cost.md:258` |
| Fix the `feature-configuration` 404. 266,767 wasted round trips a week, 69% of surveyor sessions. Named first in three documents. | S&U | 2 d + 3 d | `B:bravo-cost.md:261`, `B:bravo-observability.md:360`, `B:bravo-delivery.md:238` |
| Get the billing owner to define both application counts, with period and basis. The single largest source of error in the pack. | FinOps + billing owner | days | `B:bravo-cost.md:262`, `B:compare.md:60`, `L:cost.md:1377` |
| Publish the LOS tier (`ms-bpm` pods + `prod-postgres-bpm-d2bpm`) as a standing FinOps line. | FinOps | 1 d | `B:bravo-cost.md:263` |
| Stop quoting Rp 1.6B as the migration saving. Correct decks and notes. | EM | 0.5 d | `B:bravo-cost.md:264` |

### 1.3 Bravo — observability (`bravo-observability.md` Days 0–30)

Ordering rule: repair the alert channel before adding anything to it (`B:bravo-observability.md:383`).
Precondition: no new alert without an owner and a runbook entry (`:375`).

| Action | Owner | Effort | Source |
|---|---|---|---|
| Fix the six `No Data` monitors. Four filter on `prod-sharia-bpm` against a service registered as `prod-sharia-bpm-sharia`. | Platform/SRE | 1 d | `B:bravo-observability.md:365` |
| Triage the eight monitors permanently in `Alert`. | Platform/SRE | 2 d | `B:bravo-observability.md:366` |
| Un-exclude `ENGINE-16004` from the Pefindo monitor. | Platform/SRE | 0.5 d | `B:bravo-observability.md:363` |
| Build the per-activity failure monitor grouped by `@activityName` and `@processDefinitionId`. Bravo's first process-level alert. | Platform/SRE | 1 d | `B:bravo-observability.md:362` |
| Put the application id into the engine MDC on the job-executor path. Turns per-activity ranking into per-loan triage. | S&U | 3 d | `B:bravo-observability.md:364` |
| Save the stuck-loan SQL as a notebook ("applications by stage and age") with a threshold monitor. | S&U | 2 d | `B:bravo-observability.md:368` |
| Send CI events to Datadog. Neither platform has pipeline events. | Platform | 2 d | `B:bravo-testing.md:564` |
| Filter the CSP beacon rows (45,988 `cdn-cgi/rum` violations a week). | Platform | 1 d | `B:bravo-delivery.md:241` |
| Instrument Agency Cockpit or retire it. | Platform | 1 d | `B:bravo-delivery.md:246` |

### 1.4 Bravo — testing (`bravo-testing.md` §7, L0 and L1 first)

Re-ordering note from the doc itself: L0 and L1 are the cheapest work and close the most findings.
They come before the item marked highest-value (`B:bravo-testing.md:610`).

| Action | Owner | Effort | Source |
|---|---|---|---|
| **L0 model lint**: parse all 53 BPMN and 3 DMN at build with no Spring context. Catches ENGINE-09004, five bare `PT4M` cycles, four undeployed YAML keys, 56 unpinned `callActivity`, orphan errors. | S&U | 4 d | `B:bravo-testing.md:451` |
| **L1 config-table validation**: selector tables, `productId → key` YAML, per-application jsonb matrix, 1,350 Flyway migrations. | S&U | 3 d | `B:bravo-testing.md:452` |
| `calledElementBinding` investigation, read-only. 56 unpinned call activities, 248,685 NDF2W applications per 90 days. Do not touch in-flight loans this month. | S&U | 5 d | `B:bravo-testing.md:556`, `B:bravo-delivery.md:243` |
| Ship the four mechanical Gherkin rules as CI before any corpus triage starts. About 50 lines over a Gherkin AST. | QA | S | `B:bravo-testing.md:576`, `B:bravo-testing.md:392` |
| Wire the console coverage gates the three consoles already measure; add `-Dsonar.qualitygate.wait=true`. Thresholds sit at 0% / 0% / 1%. "The cheapest quality win in the estate." | FE leads | S | `B:bravo-testing.md:588`, `B:option-1.md:130` |

### 1.5 Bravo — workflow shape (`workflow-gap.md` §12, 0–30 days)

| Action | Exit criterion | Source |
|---|---|---|
| Publish the effective per-product flow. One diagram per product, in the repo, regenerated on build. | Every live product has a current owner-readable diagram. | `B:workflow-gap.md:342`, `:143` |
| Freeze new hidden variation: a PR check that fails a new `application.isXxx()` in `activity/unified/**` and a new config-gated class without a doc entry. | The `isXxx()` count can only go down from 19. | `B:workflow-gap.md:343` |
| One-page ADR: product-owned spines + shared domain children + fork on structure only. Stakeholder sign-off. | ADR merged. | `B:workflow-gap.md:345` |
| Delete dead `setting.workflow.map` keys (`PREAPPROVAL`, `DF4W`, `DF2W`, `DF2W_Sharia`) and `Process_NDF4W_Scoring_1_Mock_Ro`. | Map keys map 1:1 to deployed processes. | `B:workflow-gap.md:346`, `B:compare-architecture.md:643–644` |

### 1.6 Bravo — reliability measurement (`production-findings/ticket-analysis.md`)

| Action | Owner | Effort | Source |
|---|---|---|---|
| Re-export Sep–Oct tickets and confirm `Surveyor Platform - Release reject` has gone to zero after the 2026-09-10 fix. Decides whether Bravo's intervention rate is 3.1× LORA's or level. | Squad LN | hours | `B:production-findings/ticket-analysis.md:248`, `B:compare.md:270` |
| Count `application_error_tracking` rows and reprocess/revive endpoint hits. A second, independent numerator. | Bravo | days | `B:production-findings/ticket-analysis.md:249`, `B:compare-architecture.md:437` |
| Ask the service desk what changed in August. Four LORA ticket streams vanished. | Service desk | hours | `B:production-findings/ticket-analysis.md:250` |
| **Get the agreement, NTF and disbursement split by platform out of a system.** Gating measurement #1 for Decision B. Applications are the wrong unit by about 30×. | CTO office / billing owner | days | `B:compare.md:269`, `B:compare.md:346`, `L:reports/2026-08.md:97` |

### 1.7 Bravo — people (`bravo-people.md` Days 0–30)

| Action | Owner | Effort | Source |
|---|---|---|---|
| Stop citing boards 2099 and 2877 as delivery evidence. Wire the epics to their `BLCS` and `LN` children or say so. | PMO | 1 d | `B:bravo-people.md:382` |
| Spike the LORA per-change generator: schema, handler, activity migration, authorization entry and front-end call from one spec. | LORA squad | 5 d | `B:bravo-people.md:386`, `B:compare.md:361` |

### 1.8 LORA — cost and reliability, "Do first" (`README.md` Act 3)

All items are small and low replay risk unless marked.

| Action | Owner | Effort | Source |
|---|---|---|---|
| Raise retry `MaximumInterval` from 60 s to 5–15 min at the four call sites. About 6× fewer retry Actions, no latency cost. **Done in code, 25 Sep 2026:** 15 min in the 7 process workers (BL-9767); prod with LPW v0-25; task workers still 60 s. | LPW | S | `L:README.md:143`, `L:reliability.md:192`, `assessment/engineering.md:255` |
| Add a default `ScheduleToCloseTimeout` so uncapped retry becomes a visible failure. | SDK | S | `L:README.md:144`, `L:reliability.md:193` |
| Clear the wedged loans in Appendix A. Fix the `StoreInitialDocRevision*` PK conflict and the `ro_update_cif` path. About 450k wasted Actions a month and 19 customers waiting. | LPW | S | `L:README.md:145`, `L:reliability.md:236` |
| Unwedge the 24 loop workflows behind 93% of upstream errors: 19 `golive_update_agreement`, 2 `calculate_pre_scoring_ndf4w`, 1 `dochub_create_document`. | On-call | S | `L:observability.md:741`, `L:observability-upstreams.md:230` |
| Classify terminal errors centrally at the proxy/HTTP client layer and list that one type in `NonRetryableErrorTypes`. One or two places, not 134 activities. About 50,000 non-retryable 4xx a week are retried forever. | SDK / LGS | S | `L:reliability.md:235`, `L:observability-upstreams.md:239` |
| Map `agreementservice.ErrBadRequest` to a 400 business error. Removes about 75% of gateway 500s. Stop retrying 4xx in LTW `CallLGSRescheduleAPI`. Include `Details[0].Code` in `APIError.Error()`. | LGS / LTW / SDK | S each | `L:observability.md:742–744` |
| Raise idle `DefaultSleepDuration` and skip the 6 h keepalive when nothing is pending. Drop the task-master's second 6 h timer. | LPW / LTW | S | `L:README.md:148`, `L:cost.md:1263` |
| Alert on more than 10 failed attempts per workflow. P99 is 1, so false positives are nil. | On-call | S | `L:README.md:146` |
| **Deploy PR 1246** (proxy schema on gateway spans) with the next LGS tag, and run the 7-step deploy-day checklist: create the `@proxy.schema` and `@proxy.kind` facets, add per-endpoint 5xx monitors with owner and runbook. | LGS releaser | S | `L:observability.md:740`, `L:observability.md:337` |
| Alert on 5xx per upstream endpoint, never on the aggregate. Hand the three upstream bugs (income model on `customer_income = 0`, ms-customer `HikariPool`, ms-agreement timeout-as-400) to their owners. | On-call → upstream teams | S | `L:observability.md:745` |
| Retag or delete the eight No-Data worker resource monitors. | Platform | S | `L:observability.md:751` |
| Weekly completion-rate widget and an open-non-terminal > 20 days count. The never-terminating half has no failed attempts and no signal today. | On-call → Product | S | `L:observability.md:736` |
| Adopt zero-human-intervention rate as the reported KPI instead of the Actions bar. | Platform lead | S | `L:README.md:158`, `L:reliability.md:238` |
| Test the re-origination hypothesis: does force-cancel + restart reuse an Arango `_key` and cause the PK zombies? | LPW | S | `L:reliability.md:237` |
| Re-cut the upstream table by host × path group × status with `CARDINALITY(trace_id)`. No code change. | Platform | today | `L:observability-upstreams.md:228` |

### 1.9 LORA — testing and merge gates (`testing.md` §13 0–30 days, `testing-gates.md` weeks 1–4)

Everything else in the testing plan assumes a suite that can go green (`L:testing.md:738`).

| Week | Action | Owner | Source |
|---|---|---|---|
| 1 | Add a PR pipeline to `lora-process-sdk` (`go vet`, `go test -race`). Nothing runs tests on the SDK every worker imports. Prerequisite for every framework gate. | SDK owners | `L:testing-gates.md:42`, `L:pipelines.md:271` |
| 1 | Gate C2 SDK change (reject `MaximumAttempts: 0` with no `ScheduleToCloseTimeout`). Gate C6 terminality, layer 1, skipped-with-ticket. | SDK | `L:testing-gates.md:12`, `:16` |
| 1–2 | Pin one `lora-process-sdk` minor fleet-wide. Set a test floor on the four zero-test product repos. | Platform | `L:README.md:150`, `L:testing-gates.md:63` |
| 2–4 | Gate C1 error-classification lint (required week 4). C2 required week 3. C5 depchain registration (week 3). C4 schema backward-compat diff (week 4). | SDK / Platform | `L:testing-gates.md:11–15`, `:621–623` |
| 0–30 | **Get the monorepo nightly green or quarantined and name its owner.** Treat as an S2 incident. Stop CI rewriting Zephyr case status. File CI cycles into a named folder. Point `zephyr-config.js` at the `Integration` tree. | QA | `L:README.md:172`, `L:testing.md:373–378` |
| 0–30 | Provision the `lora-super-test` CI runner. Clone it into `services/` and register it in `services.manifest.json`. It is the missing L3/L4 layer. | Dev | `L:README.md:173`, `L:testing.md:535` |
| 0–30 | Tag the 16 untagged monorepo specs. Remove the `updateAssignee` DB write. Fix the RO_CONDITIONAL mixed hosts. Confirm the PNG fixture data is synthetic. Add a browser-console assertion to both UI harnesses. | QA | `L:testing.md:177–199`, `:738` |
| 0–30 | Product tag on tests (`t.Run("product=NDF4W", …)`) so `go test -run NDF4W` is a real first check. | Dev | `L:README.md:149`, `L:testing.md:468` |

### 1.10 LORA — pipelines Phase 0 (`pipelines.md`, weeks 1–4, no other team needed)

Platform and the LORA team own all of Phase 0 (`L:pipelines.md:357`). Fourteen items, all mechanical:

- P0.1 PR pipeline on `lora-process-sdk` and `lora-tools`. P0.2 Uncomment the LTS Snyk job; add container scans to LGS, LSS, LTS.
- P0.3 `environment: prod` approval and cosign on `lora-tools`. P0.4 Top-level `permissions: contents: read` everywhere.
- P0.5 Move `github.event.inputs.*` out of `run:` into `env:`. P0.6 Pin actions to full SHA; bump `checkout`, `github-script`, `setup-go`.
- P0.7 `timeout-minutes` and deploy `concurrency` on every workflow. P0.8 SIT trigger on `v*` tags only, reachable from `master` or `release*`.
- P0.9 `gitleaks` PR job in every repo; confirm org secret scanning and push protection. P0.10 `dependabot.yml` everywhere, weekly, grouped.
- P0.11 Fix `DEVSEVCOPS_PROJECT`, unify the Vault key, one approver team. P0.12 Replace `docker.sock` scans with scans on a saved tarball.
- P0.13 Pin `node-version`; bump LBOFE Snyk image. P0.14 Write `docs/onboarding/rollback-runbook.md`.
- **Open one DevSecOps ticket per Phase 1 dependency now** (tag shared actions, GitHub App, WIF service accounts, prod image repo split, admission policy). `L:pipelines.md:358`

Sources: `L:pipelines.md:271–284`.

### 1.11 LORA — front end and delivery (`delivery.md`)

| Action | Owner | Effort | Source |
|---|---|---|---|
| Fix the duplicate script injection (`localTZAbbrev` already declared, 8,067 a week). | LBOFE | S | `L:delivery.md:213` |
| Guard custom elements on `customElements.whenDefined`. About 34,900 null dereferences a week. | LBOFE | S–M | `L:delivery.md:214` |
| Filter `ResizeObserver` noise (18% of FE errors). Then set a front-end error-rate SLO. Today: 2.8 errors per view. | LBOFE + Platform | S | `L:delivery.md:215` |
| Read RUM in the weekly review. The Customer FE has never been examined. | Platform | weekly | `L:delivery.md:216`, `L:README.md:234` |
| Document the flag story: `$.experiments.*` on the loan plus schema-versioned workers. Gate new planner activities on an experiment field. Do not wait for a flag service. | LPW | S–M | `L:delivery.md:208`, `assessment/executive.md:112` |

### 1.12 LORA — people and process (`people.md`, decisions of 2026-09-08)

| Action | Owner | Effort | Source |
|---|---|---|---|
| Ship the FSM diagram export and the depchain matrix first. Both small. Nothing to diff against until they exist. | Dev | S | `L:people.md:1081`, `:1298` |
| Confluence pilot, in order: one spec (survey eligibility) on the fixed template, walked with Product; sync job + parser + gate 1; the `.feature` file with scenario IDs; the generated as-built section on the same page. Only then a second spec. | Product + Eng + QA | a few days | `L:people.md:526–529`, `:1311` |
| Retag the three `.feature` files from `LORA-E2E-###` to `@BL-T<n>` before writing a fourth. Decide what consumes the file before the fourth exists. | QA | S | `L:people.md:1315`, `:740` |
| Gherkin style guide plus gates B4 and B5 (B2 only if a reviewer is staffed), shipped with the first file. | QA + Eng | S | `L:people.md:1314`, `:767` |
| Definition of Ready: no estimate until *on failure*, *on rework* and *on abandonment* have values and every path resolves. Example Mapping, 30 minutes, inside intake. | Product + Eng + QA | 60–90 min per process | `L:people.md:502`, `:706` |
| Create `docs/adr/` and record the GSM-vs-flowchart and spine decisions. | Eng | S | `L:people.md:1300`, `L:README.md:152` |
| Write the rule now, before the tests exist: a guard test may not be weakened without product sign-off. | EM | — | `L:people.md:1234` |

### 1.13 Estate logging programme — Phase 1, "do these first" (`logging/README.md`, `logging/sre-datadog-recommendations.md` §10)

Sequencing gate: squad cleanup first, SRE enablement second. Enablement waits for production log lines
below 2.5M a day (today ~4.5M) and parsed share above 80% (today 6.4%) (`B:logging/README.md:103`).
Error Tracking is the exception and goes on now (`:127`).

| Action | Owner | Effort | Source |
|---|---|---|---|
| **Publish bfi-java-pkg#122** by running the manual Deploy Package workflow for `logging-core` then `logging-starter`. Adopt it in `bravo-bpm-service` first. Nothing can depend on the starter until it is published. | Platform + S&U | review + 1 d | `B:logging/README.md:135`, `B:logging/logging-cost.md:583` |
| **Merge app-deployment#13820**: nine services off `debug`, five masked-field lists, three to failure-only bodies, onboarding bodies off, `bpm` sharia header logging off. Each service's SA confirms the restart. | SRE + squads | review | `B:logging/README.md:136` |
| Merge the 47 open service PRs and the Go wrapper PR. Set every Go `*_JSON_MASKED_FIELDS` per service in `app-deployment`. Run CI on each PR before merging; ten defects were invisible to reading. | each squad; SRE | review; 2 h | `B:logging/logging-cost.md:582`, `:585`, `:493` |
| Fix CONFINS log re-ingestion: the Agent re-reads dead pods' files from a shared `/var/log` on every rollout. About a third of all indexed prod events. | SRE | 1 d | `B:logging/README.md:139`, `B:logging/confins-prod-ms-lms-ar-be-findings.md:221` |
| Fix the monitors that query service names that do not exist (20+ report `OK` and can never fire). | SRE | 2 d | `B:logging/README.md:138` |
| Fix Remote Configuration on 13 services (~91k failed polls a week). Nothing can be enabled from the Datadog UI until then. | SRE | 1 d | `B:logging/README.md:141`, `B:logging/body-visibility.md:220` |
| Turn on `DD_TRACE_HEADER_TAGS` for correlation IDs. Never add `authorization`, `api-secret`, `cookie`. | SRE | 1 h | `B:logging/README.md:142`, `B:logging/body-visibility.md:281` |
| Fix the three CI gate faults: Codacy token, `codacy-cli.sh`, SonarQube new-code baseline. "An hour that unblocks six weeks of squad work." | Platform | 2 h | `B:logging/README.md:144` |
| Pin the tracer version. Unified tags and the eight service-name splits; retire `env:production`. Source-code integration on Java services. | SRE | 1 h; 3 d; 2 d | `B:logging/sre-datadog-recommendations.md:989–998` |
| Find out why six production services emit no logs and no spans at all. | SRE | 2 d | `B:logging/sre-datadog-recommendations.md:997`, `B:logging/coverage.md:161` |
| Reconcile the ~1.3 TB/day ingestion estimate against Usage & Cost and the invoices before the next renewal conversation. The commitment is 256 GB a month. | SRE + FinOps | 2 h | `B:logging/sre-datadog-recommendations.md:1000` |
| Turn on Error Tracking now. RUM tidy-up and the Gmail access review. | SRE | 2 d; 2 d | `B:logging/README.md:127`, `B:logging/sre-datadog-recommendations.md:994` |
| Fix the HCIS consumer failure in `bravo-cnv-service` (20k failed messages a day, logged twice). Fix the ENGINE-09004 model warnings. Downgrade routine warnings in `lora-task-service`. | Internal Service; S&U; LORA Core | 2–3 d; 2 d; 1 d | `B:logging/logging-cost.md:574`, `:579`, `:580` |
| Every squad: the "stop the bleeding" checklist, starting with the exception handler picking level from status code (4xx warn, 5xx error). | each squad | next planning session | `B:logging/squads-guide.md:579` |

---

## 2. Days 31–60

### 2.1 Bravo

| Area | Action | Owner | Effort | Source |
|---|---|---|---|---|
| Observability | Add a 4xx clause to the success-rate monitors: `401` from IAM, `404` on the four surveyor endpoints, `400` on scheduling. "Bravo does not fail with 5xx. It fails with 4xx." | Platform/SRE | 3 d | `B:bravo-observability.md:361`, `B:bravo-testing.md:558`, `B:compare.md:360` |
| Observability | **Trace the job executor**: `@WithSpan` on `BaseActivity.execute()` or the Camunda OpenTelemetry plugin. The one change that makes orchestration visible in APM. | S&U | 8 d | `B:bravo-observability.md:367`, `B:compare.md:368` |
| Observability | Read RUM in the weekly review; set a per-console error-per-view SLO. Retrofit an alert runbook table to surviving monitors. | Platform/SRE + EM | 2 d + 2 d | `B:bravo-observability.md:369`, `:375`, `B:bravo-delivery.md:240` |
| Security | Add the two engine-integrity monitors: new `act_re_deployment` rows outside the naming convention; process starts outside the known key set. Either would have fired on 2026-05-23. | Platform/SRE + Security | 1 d | `B:bravo-observability.md:371`, `L:observability.md:505` |
| Cost | Check whether failed geolocation attempts are billed (Rp 64M Maps spend against 20,690 failures a week). Establish the failure cause. | FinOps + LN; S&U | 2 d; 5 d | `B:bravo-cost.md:259`, `B:bravo-delivery.md:239` |
| Cost | Decide the Camunda history question explicitly with Compliance: shorten the TTL or stop calling it a cost problem. Implementation deferred. | S&U + Compliance | 2 d | `B:bravo-cost.md:260`, `B:option-summary.md:186` |
| Cost | `bravo-project-nonprod` reduction plan from the Days 0–30 breakdown. | FinOps + Platform | 3 d | `B:bravo-cost.md:258` |
| Testing | Fail the build on ENGINE-09004 via a parse test over all 53 BPMN. Start with the KYC gateway the engine is guessing about. | S&U | 4 d | `B:bravo-testing.md:557` |
| Testing | JaCoCo `check` gate in `ms-bpm` at the current floor, ratcheting. Fix the `makefile` profile flag surefire ignores. | S&U | 2 d | `B:bravo-testing.md:562` |
| Testing | One Synthetics multi-step API test for the origination journey (L8). | QA | 3 d | `B:bravo-testing.md:563`, `:459` |
| Testing | Per-run stub layer in front of the 113 Feign clients. Unblocks N0–N12. | S&U | 6 d | `B:bravo-testing.md:565`, `:522` |
| Testing | L3 gateway-expression evaluation through `ExpressionManager`. 137 gateways in `ndf4w.bpmn` alone. | S&U | 5 d | `B:bravo-testing.md:454` |
| Delivery | `calledElementBinding` decision: pin, or accept in-flight child migration deliberately. | S&U + EM | 2 d | `B:bravo-delivery.md:243` |
| Delivery | Feature-flag registry. Start by listing the 78 gateway lookups, Java flags and selector tables. | S&U | 4 d | `B:bravo-delivery.md:242` |
| People | Measure changes, not tickets: one unit (merged PRs per product change, or Story lead time) for both platforms. | EM + LORA squad | 3 d | `B:bravo-people.md:383` |
| Workflow | Build `spine_df4w`; route new DF4W volume behind a flag. Delete the three DF4W `applicationWorkflowSelectorType` gateways and the DF4W arms of `isXxx()`. Convert KYC/RAC config no-ops to explicit model choices. Per-product diagram diffed in CI; contract tests per domain child. | S&U | — | `B:workflow-gap.md:352–355` |
| Option 1 | Restore a PROD clone and rehearse the full cutover: engine starts with no unexpected DDL, in-flight resume, user tasks claimable, Cockpit plugins load, timers fire. Non-negotiable before a date. | Bravo | 2–3 d | `B:option-1.md:216`, `B:option-summary.md:162` |
| Option 1 | Run the three console suites against a staging instance on the forked engine. Turn console coverage thresholds on first. | Bravo + FE | — | `B:option-1.md:126`, `:130` |

### 2.2 LORA

| Area | Action | Owner | Effort | Source |
|---|---|---|---|---|
| Cost | **Coalesce NATS notifies.** `PublishActivityStart`/`End` are 57% of activity Actions. Checkpoint deltas; stop dumping `history.cache` every persist. Mean loan 118.8 → ~45 Actions. Replay risk Medium. | LPW / SDK | M | `L:README.md:170`, `L:cost.md:1236`, `assessment/architecture.md:158` |
| Cost | Reuse the planner-loop timer when its deadline has not moved. About 4.7M Actions a month. | LPW | S–M | `L:cost.md:1237` |
| Cost | **Make every loan terminate.** Cap the renewal, not the window: write `min(cap, max(document, NATS KV))`, apply the cap where `lead_expiration` reads, replace the two `+1 year` sentinels with a suspension flag. Product decides the cap (anything over 30 days is safe). Stage the backlog; do not let one sweep terminate 18,000 workflows. | LPW + Product | M | `L:cost.md:1240`, `:943–953` |
| Observability | Upsert Temporal search attributes: `ApplicationStatus`, `BlockedActivity`, `BlockedSince`, `FailingUpstream`, `ProductId`. | LPW | M | `L:README.md:171`, `L:observability.md:731` |
| Observability | Call `PublishActivityFailed` / `PublishWorkflowError` (dead code today). Add a `SetQueryHandler`. Inject `dd.trace_id` into logs via `ConvertID()`. | LPW / SDK | S each | `L:observability.md:732–739` |
| Observability | Track fleet P95 Actions per loan (191 today) as a regression SLO. Two saved DDSQL notebooks (completion cohort, Actions per loan). Extend the monthly dashboard with Tier 0/1 widgets. | Platform | S; S; M | `L:observability.md:737`, `L:monthly-report.md:230–231` |
| Testing | NDF4W profile and stub bundles in super-test. Port the top 10 `lora-trigger` scripts with `@BL-T` tags. T0/T1/T2 wired to the depchain impact map. Build N9, N1, N4 first, in super-test not SIT. In-repo `plannertest`. | Dev / QA | — | `L:testing.md:739`, `:641–643`, `:470` |
| Gates | Weeks 5–6: gate C6 terminality layer 2. `replay-check` at deploy, report-only for two UAT deploys. | SDK / Platform | M | `L:testing-gates.md:13`, `:16`, `L:README.md:175` |
| Testing | Depchain PR-impact comment: emit `activities_by_product.json`; CI says "impacts NDF4W". Close the depchain generator (CSV, eagerness, precursors, `depended_by`, run in CI on drift). | Dev | M; S–M | `L:README.md:174`, `L:people.md:1298` |
| Pipelines | Phase 1 begins (months 2–3), repo by repo starting with the SDK and the three HTTP services: converge on `bfi-base-template` at a semver tag; SBOM + provenance; GitHub App replaces `GH_PAT` (272 references); WIF everywhere; GitOps via PR for UAT and PROD; promotion gate in `deploy-prod`; frontend build-once; the three LORA gates as template steps; pre-commit. | Platform + DevSecOps | M each | `L:pipelines.md:292–302`, `:360` |
| People | Archetype 2 Phase 1: build the net (merge gates, planner harness, coverage floor on changed packages). Phase 2: each domain owner writes their guard pack in pairs, product signs off scenarios. | EM + domain owners | — | `L:people.md:1252–1255` |
| Architecture | Central status transition validator, shadow mode first. Low effort, closes the main GSM safety gap. | SDK | low | `assessment/architecture.md:150`, `assessment/executive.md:118` |

### 2.3 Estate logging — Phase 2 and the body-visibility sequence

- Squads cut log volume over 4–6 weeks; SRE holds the gate and tracks weekly. `B:logging/sre-datadog-recommendations.md:1002`
- SRE delivers in order: Remote Config → log-to-trace correlation (start with `prod-inventory-management`) → header tags → Live Debugger. Only then are squads asked to remove always-on body logging. "Do not ask for the removal before the replacement exists." `B:logging/body-visibility.md:259`, `:393`
- Squads put identifiers and the decision on the span, not the payload. Available today. `B:logging/squads-guide.md:491`

---

## 3. Days 61–90

### 3.1 Bravo

| Area | Action | Owner | Effort | Source |
|---|---|---|---|---|
| Cost | No new cost work. Verify: September and October Cloud Logging against the August baseline; the LOS tier view across three months; per-application cost on agreed denominators. "A saving not measured on a subsequent invoice is a plan." | FinOps | — | `B:bravo-cost.md:296` |
| Observability | Day-90 check: have the phase 1 and 2 monitors fired, did somebody act, are they still un-muted. | Platform/SRE | — | `B:bravo-observability.md:418` |
| Testing | L5 process-fragment tests and L6 product-matrix journeys: five journeys cover the whole matrix, about 4 minutes per merge. | S&U + QA | 12 d | `B:bravo-testing.md:559`, `:456–457`, `:538` |
| Testing | Retry and degrade tests, part 1: every `failedJobRetryTimeCycle` is a valid `Rn/PTn`. | S&U | 4 d | `B:bravo-testing.md:560` |
| Testing | Policy: derive expectations from `act_hi_actinst`, never type them. Depends on the job-executor spans from Days 31–60. | S&U + QA | policy | `B:bravo-testing.md:566` |
| Delivery | `calledElementBinding` implementation, per the Days 31–60 decision. | S&U | 10 d | `B:bravo-testing.md:556` |
| Delivery | Inventory the 15+ consoles; name an owner for shared components. | EM + FE leads | 3 d | `B:bravo-delivery.md:244` |
| People | Week-1 curriculum for both platforms. A Bravo hire should reach a moving loan in week 1. | EM + S&U; LORA EM | 3 d each | `B:bravo-people.md:394`, `L:people.md:1297` |
| People | Arm the DF2W clock: first `BLCS` ticket to first production application. | PMO | 1 d | `B:bravo-people.md:395` |
| Workflow | Stand up `spine_ndf2w` (248k loans a quarter). Strangler cutover to at least 25% of new NDF2W starts at error and latency parity. Collapse the worst 2W/4W duplicate delegates. Write the dated decommission plan for `NDF4W`, `NDF4W_RO` and Sharia; DF2W launches on `spine_df2w`. Report the five programme metrics monthly. | S&U + Product | — | `B:workflow-gap.md:361–366` |
| Option 1 | If Decision A is funded and the rehearsal passed: quiesce the job executor during the swap, back up before the schema-log reconciliation, promote SIT → soak → UAT → soak → PROD with the diagnostics run per environment. Do not rename `CAMUNDA_HISTORY_*`. | Bravo + Release mgmt | 18–33 eng-days total | `B:option-1.md:274–307` |

### 3.2 LORA

| Area | Action | Owner | Effort | Source |
|---|---|---|---|---|
| Cost | **Retire the five idle worker versions** (`v0-16`–`v0-20`: 82 cores, 154 GB). About Rp 63M a month, more than the whole Bravo LOS tier. Blocked only on abandoned loans terminating (Days 31–60). | Platform | S–M | `L:README.md:168`, `L:cost.md:1258`, `B:option-3.md:178` |
| Cost | Put a date on Bravo LOS decommissioning and right-size the LORA tier (≈Rp 431M all-in, about 7× the tier it replaces). Renegotiate the Temporal commitment against ~52% fewer Actions. | Org / Finance | — | `L:README.md:169`, `L:cost.md:382` |
| Reliability | Fix the survey and ESIGN partial-completion races that drive rewinds and force-cancel. Replay risk Medium. | LTW | M | `L:README.md:180`, `L:cost.md:1266` |
| Testing | Super-test parallel runs. Full T3 nightly = super-test + monorepo `@BL`. NFR gates on P95 Actions per loan and the FE error budget. One coverage grid across the three harnesses. T4 fleet pack. Traceability report: which BL requirement is untested. | Dev / QA | — | `L:testing.md:740` |
| Gates | `replay-check` becomes blocking after two clean UAT deploys. Make each check required once green for two weeks. Pin the six other family repos to the same SDK minor so gates 1 and 2 protect them. | Platform | — | `L:testing-gates.md:13`, `:625–627` |
| Reporting | Scheduled job writes `reports/YYYY-MM.md` pre-filled from Datadog and GCP as a draft PR. GCP billing as a scheduled BigQuery view. Jira rewind and force-cancel counts into Datadog. | Platform | M; S; S–M | `L:monthly-report.md:239–240`, `L:observability.md:755` |
| People | Archetype 2 Phase 3: name the platform team (SDK, planner, gateway, schema). Phase 4: pilot one product family end-to-end with a defined overlap. | Leadership | — | `L:people.md:1256–1257` |
| Architecture | Shared activity library for the 56 duplicated packages, so a Pefindo fix lands once. Structural; decide deliberately. | Platform team | M | `L:README.md:187`, `assessment/executive.md:111` |
| Delivery | `intake-to-skeleton` generator, LPW first. Do not promise LTW until three LPW activities have merged from it. | Eng | S–M | `L:people.md:1310`, `:892` |

### 3.3 Estate logging — Phase 3, then Phase 4 (only once the gate is met)

Phase 3 (2.5M lines/day and 80% parsed): reassembly, logs injection, trace remapper and per-service
exclusion filters (2 d); trace KrakenD then `prod-lora-task` with sampling from day one (3 d);
log collection on the silent traced services, `prod-ms-agreement` first (3 d).
`B:logging/sre-datadog-recommendations.md:1003–1005`

Phase 4: Live Debugger pilot on `bfi-payment-api` once billing is confirmed (1 d); runtime metrics,
then DBM on 10 services, then profiling on `ms-bpm` (3 d); pick one tracing stack and remove the
duplicates (a decision); real synthetic tests, sparingly (3 d); SIT and UAT logs, errors only,
3-day retention, last (3 d). `B:logging/sre-datadog-recommendations.md:1006–1010`

---

## 4. Decisions that gate the plan

| Decision | Who | By | Why it gates | Source |
|---|---|---|---|---|
| Standing allocation per platform; bus factor named | Leadership | day 1 | Every other plan assumes the capacity | `B:bravo-people.md:387` |
| Fund Option 1 Path B (Decision A) | Steering / CTO | weeks | Engine and framework are out of support today | `B:option-summary.md:155` |
| Bravo horizon, even provisional | Steering / CTO | 30 d | Selects the bridge variant; main input to Decision B | `B:option-summary.md:181` |
| Is a support contract required for the engine? | Architect + Procurement + Risk | 30 d | Selects the fork (CIB seven vs Operaton) | `B:option-summary.md:182` |
| Camunda history TTL | S&U + Compliance | 60 d | Data-retention change, not engineering | `B:bravo-cost.md:260` |
| `calledElementBinding`: pin or accept in-flight migration | S&U + EM | 60 d | Answered by default today for 248k loans a quarter | `B:bravo-delivery.md:243` |
| Product-owned spines ADR | Product owners | 30 d | Gates the whole workflow-gap programme | `B:workflow-gap.md:345` |
| Abandonment cap per loan (the `on abandonment` cell) | Product | 60 d | Gates loan termination and worker retirement | `L:cost.md:947` |
| Which 4xx are terminal; `DefaultScheduleToCloseTimeout` value | SDK + Product | week 2 | Gates C1 and C2 (defaults exist if nobody decides) | `L:testing-gates.md:656–657` |
| Replay credentials and egress for gate C3 | Platform + Security | week 4 | Gate 3 cannot run without it | `L:testing-gates.md:658` |
| Renewer/expirer fix for gate C6 | Product | 60 d | Test stays skipped-with-ticket until taken | `L:testing-gates.md:661` |
| Régime A or C for the process source of truth | Eng leadership | 90 d | A half-maintained spec is worse than none | `L:people.md:1309` |
| One tracing stack (OpenTelemetry vs Datadog tracer) | SRE | Phase 4 | 13.2M spans a week can never have Live Debugger | `B:logging/sre-datadog-recommendations.md:1008` |
| Approve the logging programme, but not on its stated reasoning (Rp 140.5M is stale) | CTO | now | Named fix is not the biggest lever | `B:logging/logging-cost.md:603` |

---

## 5. Deferred past 90 days, with the trigger that starts them

**Bravo**
- Camunda history implementation — after the Compliance decision. `B:bravo-cost.md:310`
- `bravo-project-nonprod` execution — after the reduction plan. `B:bravo-cost.md:311`
- Version or snapshot slowly-changing reference data (10 d) — after the history decision. `B:bravo-delivery.md:245`
- Product blast radius in the diff (8 d) — Q2 week 1. `B:bravo-testing.md:561`
- N0–N12 negative suite (about 2 d per case) — after the L6 journeys and the stub layer. `B:bravo-testing.md:508`
- L7 console contract tests, then the 595-feature Gherkin triage — after the console inventory. `B:bravo-testing.md:458`, `:660`
- Shared component library — an organisational decision with a budget. `B:bravo-delivery.md:288`
- Re-ask "is a new product on Bravo easy?" — once DF2W has production volume. `B:bravo-people.md:395`
- Appendix C code tickets (17 items: `AuthorizeAspect` permissions bypass, duplicate CIF on timeout, RabbitMQ retry lost on restart, no unique index on `application(lead_id)`, and so on). Worth a ticket each; not phased. `B:compare-architecture.md:642–656`
- Option 2 and Option 3 workstreams — after Decision B: Temporal search attributes and error taxonomy (2–3 eng-months), Cockpit replacement (2–4), DF4W-on-Temporal as the experiment with an exit (8–14), LORA product coverage (10–20), human-task parity (6–12), LORA reliability remediation as the entry gate to each cutover wave (4–8). `B:option-2.md:150–166`, `B:option-3.md:105–110`, `:163`
- Out of scope for the 90-day workflow programme: rewriting survey/underwriting domain logic; migrating the Sharia deployment; any change to the LORA or Temporal track. `B:workflow-gap.md:374`

**LORA**
- `ContinueAsNew` with carry-over snapshot — structural, high replay risk, decide deliberately. `L:README.md:191`
- Third-party feature-flag service — only if stamping through DP proves too slow. `L:delivery.md:50`
- Pipelines Phase 2 (months 4–6): admission control (audit SIT → enforce UAT → PROD), DAST on SIT, Helm/IaC scanning, OpenSSF Scorecard, CI Visibility and DORA, ephemeral runners, SLSA Build L3. `L:pipelines.md:310–316`
- Archetype 2 Phase 5: remaining families, instrumentation first. `L:people.md:1258`
- Human-task abstraction: extract form routing into declarative config, even partially. The largest ongoing cost, ~12,000 lines of hand-written FSMs. `assessment/architecture.md:148`
- Compensation design — only if scope expands to fund movement. `assessment/architecture.md:154`
- Queue management: `QueueAssigned` handler, queue fields, monitoring. `domain/queue-management.md:554`, `:758`

---

## 6. Explicitly do not do

- Do not treat "raise concurrent workflows" as a Temporal bill fix. It buys pod RAM, not fewer Actions. `L:README.md:195`
- Do not start an OpenMetrics scrape just to name the Activity bar. `L:README.md:205`
- Do not make diff-inspector the fleet dashboard. `L:README.md:204`
- Do not dissolve a domain team before its guard test pack exists. `L:README.md:197`
- Do not build Bravo-style application-wide pagination. Do not invent a fourth UI path. `L:delivery.md:210`, `L:README.md:181`
- Do not merge the product families back onto `dp-ndf`. `architecture/product-family-workers.md:67`
- Do not spend SDK work on sticky-cache RAM. `L:cost.md:1247`
- Do not create a Bravo alert without an owner and a runbook entry. `B:bravo-observability.md:375`
- Do not rename `CAMUNDA_HISTORY_*` as part of the engine migration. `B:option-1.md:307`
- Do not quote Rp 1.6B as the migration saving. `B:bravo-cost.md:264`
- Do not enable Datadog log ingestion before the volume and parse gates are met. `B:logging/README.md:103`
- Do not ask squads to remove body logging before the replacement exists. `B:logging/body-visibility.md:393`
- Do not use App and API Protection as a debugging tool, and do not raise the log message size cap. `B:logging/body-visibility.md:200`
- Do not treat the allocation decision as evidence about where new products should go. `B:compare.md:363`
- Do not cite "seven product families" as a production property; six are not deployed. `assessment/executive.md:94`
- Do not repeat the withdrawn claim that Bravo's Camunda is publicly exposed. `L:bravo-cross-check.md:131`

---

## 7. Where the same item appears on both sides

These are one piece of work, not two.

| Item | Bravo source | LORA source |
|---|---|---|
| Agreement / NTF / disbursement split by platform, from a system | `B:compare.md:269` | `L:reports/2026-08.md:97` |
| Both application counts defined by the billing owner | `B:bravo-cost.md:262` | `L:cost.md:1377` |
| Engine-integrity monitors on unexpected deployments and unknown process keys | `B:bravo-observability.md:371` | `L:observability.md:505`, `:748` |
| Rotate `cypress.config.js` credentials | `B:bravo-testing.md:578` | `L:people.md:768` |
| 4xx-aware health gate and a front-end error budget on both platforms | `B:compare.md:360` | `L:delivery.md:215` |
| Week-1 curriculum for both platforms | `B:bravo-people.md:394` | `L:people.md:1297` |
| Mechanical Gherkin rules as CI, about 50 lines | `B:bravo-testing.md:576` | `L:people.md:1314` |
| Retry policy and dead-letter path: LORA ports Bravo's design, then writes the negative tests Bravo never had | `B:compare.md:288–295` | `L:reliability.md:235`, `assessment/architecture.md:160` |
| Temporal commitment headroom before the March 2027 renewal | `B:option-summary.md:185` | `L:cost.md:1389` |
| Idle LORA worker versions worth ≈Rp 63M a month | `B:option-3.md:178` | `L:README.md:168` |

---

## 8. Capacity check for Days 0–30

Person-days named in the source docs for the first 30 days, summed by owner, against the standing
assumption in `bravo-people.md:387`.

| Owner | Named work in Days 0–30 | Assumed capacity | Verdict |
|---|---|---|---|
| Squad S&U (Bravo) | `feature-configuration` 404 (5), MDC (3), stuck-loan SQL (2), L0 (4), L1 (3), `calledElementBinding` read-only (5), pre-decision cleanup (2), Feign and exception logging (6), ENGINE-09004 (2) | ~25 pd/month | **~32 pd. Over by a week.** Drop or defer the `calledElementBinding` investigation or the exception-logging change to Days 31–60. |
| Platform/SRE (estate) | Bravo monitors and CSP and Cockpit (8.5), logging Phase 1 SRE items (~17), Cloud Logging cuts (1.5), CI events (2) | ~10 pd/month | **~29 pd. Nearly 3× over.** The logging Phase 1 list alone exceeds the month. Either Platform is given more people for 30 days, or the Bravo observability repairs wait. The docs rank the credential rotations, CONFINS re-ingestion and Remote Config first. |
| LORA squad (LPW/LTW/SDK/LGS) | All "do first" items are marked S; gates C1/C2/C5/C6 layer 1; PR 1246 deploy; Phase 0 pipelines (14 mechanical items); generator spike (5) | not stated in any doc | Not sized anywhere. The first thing the allocation meeting should produce. |
| QA (both) | Monorepo nightly incident; super-test runner; tag/fix specs; Gherkin gates; cypress rotation; `\|\| true` removal | not stated | Not sized. |
| FinOps / billing owner | Both application counts (days), NTF split (days), nonprod breakdown (2), LOS tier line (1), Coralogix (1) | not stated | Roughly two weeks of one person. |

The Option 1 engineering (18–33 eng-days) is on top of all of this and is not in the S&U number.
