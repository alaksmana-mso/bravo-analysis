# Delivery: flags, consoles, pagination, master data

**Audience:** Platform, front-end engineers, product engineers shipping DF and NDF work on Bravo
**Structure:** the four delivery questions LORA's [delivery.md](../../lora-workspace/docs/production-findings/delivery.md) asks — can you choose what deploys, is custom UI hard, is pagination solved, can master data feed dropdowns — asked of Bravo, plus what production says about the front ends.

**Method.** Code and configuration facts from the `bravo-bpm-service` checkout at `v2.93.43`, as recorded in [compare-architecture.md](compare-architecture.md), **plus the three operator-console repositories `bravo-surveyor-console` `v2.83.12`, `bravo-operation-console` `v2.80.18` and `bravo-underwriting-console` `v1.63.13`, added 2026-09-10** — 763,861 LOC, 829 test files, 28 CI workflows, delivered from the `LN` Jira project ([board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703)) and released within three days of this reading. This document previously discussed those consoles only through their production telemetry; the repositories they come from were not counted anywhere in the pack ([testing §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)). Production evidence measured live in Datadog `us5` on 2026-09-10: RUM on the four instrumented Bravo LOS consoles (7 days), `spring.handler` span resources on `env:prod service:prod-ms-bpm`, and the RUM application inventory for the whole org. Deployed versions read from production log tags.

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [Feature flags](#1-feature-flags-five-mechanisms-no-registry-and-a-restart) · [Custom front end](#2-custom-front-end-easy-per-page-hard-per-system) · **[Pagination](#3-pagination-bravo-built-it-it-is-called-formtab-and-it-is-the-busiest-read-path)** · [Master data](#4-master-data-bravo-has-the-feature-lora-declined-to-build) · **[What production says about the front ends](#5-what-production-actually-says-about-the-front-ends)** |
| **3. What to do** | [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Question | Verdict |
|---|---|
| **Can you pick what deploys?** | **Yes — five different ways, which is the problem.** Bravo has no LaunchDarkly either, but it has Spring property flags read *inside BPMN gateway strings* (78 lookups), a six-column database selector, a per-application jsonb activity on/off matrix, Camunda definition versioning, and 31 Java factories. There is no registry, no owner and no expiry. Toggling a gateway flag needs a configuration change and a restart, because it is `environment.getProperty` evaluated at gateway time. |
| **Is a custom front end on a page hard?** | **No — and that is the trade.** Every Bravo console is an ordinary React app calling domain REST verbs; the UI never sees a Camunda task id. One page is easy. But there are **at least fifteen** separate browser applications in the Bravo orbit, and a change to a shared concept ships in as many of them as touch it. LORA has one back-office front end and a three-layer widget seam. Bravo traded a hard seam for a wide surface. **Measured 2026-09-10:** 763,861 LOC and 829 tests across three consoles, sharing a design system that has drifted to **three different versions** with React 17 on two and React 18 on the third ([§2](#2-custom-front-end-easy-per-page-hard-per-system)). |
| **Is pagination solved?** | **Yes, and LORA's account of the problem is confirmed from Bravo's own telemetry.** Bravo built exactly the paging LORA describes: a controller literally named `SurveyorAssignmentFormTabV2Controller`, plus **nine** per-assignment sub-resource endpoints. Together they are the busiest read path in the service. LORA is right not to rebuild it — and Bravo is right that it needed it, because Bravo's surveyor really does open one application, not one task. |
| **Can master data feed dropdowns?** | **Yes — Bravo has the capability LORA deliberately declined.** LOV tables and three master-data services back the dropdowns directly, which is why renaming an approval role (`BLCS-4683`, NMH→GMB) took one YAML line, one SQL `UPDATE` and zero Java. The cost is the one LORA designed around: values are read live, so a mid-flight master-data edit can change what a form offers after a decision has been taken on the old list. |
| **Are the front ends healthy?** | **No, and nobody was looking.** Four instrumented consoles produce **2,413,198 errors in 7 days** — 5.8× LORA's back office. **748,686 of them are 404s on the Surveyor Platform**, one endpoint reaching **69% of all sessions**. No monitor can see it because every health check filters on `5*`. |

**The through-line:** every delivery mechanism Bravo needs exists and most of them work. What is missing is a boundary — no flag registry, no console inventory, no front-end error budget — so the delivery surface grows and nothing tells anyone it has.

---

## 1. Feature flags: five mechanisms, no registry, and a restart

LORA's complaint was "no feature flag; cannot pick what deploys", graded *partially true* — no LaunchDarkly, but `$.experiments.*` per-loan stamps and concurrent schema-versioned workers exist.

Bravo's answer is the opposite failure. It has **five** ways to pick what runs, and they are not coordinated.

| Mechanism | Granularity | To change it you… | Applies to in-flight loans? |
|---|---|---|---|
| **Spring property flags inside BPMN gateway conditions** — `environment.getProperty('setting.feature.config.featDF2W') == 'true'`; **68 lookups in the legacy monoliths, 10 in the unified spine** | environment-wide | change configuration and **restart**, or refresh config | yes, at the next gateway evaluation |
| **Java service flags** — `featRefactorWorkflow`, `featFinalApproverRoleOnReject`, `featSingleApproverRejectedRole` (`BaseUnderwritingApprovalServiceImpl`, 4,604 lines) | environment-wide | same | yes |
| **Six-column selector tables** — `WorkflowProductConfig(productId, type, customerType, userType, businessType, riskType)` → `WorkflowMasterConfig` | per product / customer / risk combination | a Flyway **data migration** (`V2_0_2024040*__insert-*-workflow-config.sql`) | at resolution time |
| **Per-application jsonb activity matrix** — `ApplicationWorkflowConfig.workflowConfig`, e.g. `{"CI": {"PilotBranchCheckActivity": [true,false]}}`, read by `BaseActivity.execute()` before every unified activity | **per application, per activity** | resolved at start, re-resolved mid-flight for the "SUO" phase | fixed per application at start |
| **Camunda definition versioning** | per process definition | deploy | parent stays on its version; **children resolve to latest at call time** |

**What is genuinely good here.** The jsonb matrix is a real per-application guard layer sitting on top of the flowchart — the closest thing in either platform to LORA's `$.experiments.*`, and it arrived independently. It is the "Bravo drifted toward LORA on its own" finding in [compare-architecture.md §4](compare-architecture.md). It can only *skip* a step the diagram already contains, never introduce or reorder one, and it is static per application rather than computed from data readiness — but it is the right idea.

**Three problems, in order of cost.**

1. **A flag inside a BPMN gateway string is not a release toggle.** `environment.getProperty(...) == 'true'` is read from Spring configuration inside the engine. Flipping it is a configuration deploy, not a switch, and it applies to the whole environment at once. That is a *slower* release control than a code change gated behind a property, because the property is now also in XML.
2. **There is no registry and no expiry.** 78 gateway lookups plus an unbounded set of Java flags plus the selector tables, with no list of which are live, which product each belongs to, or which can be removed. `featRefactorWorkflow` gates the entire unified-versus-legacy behaviour and has been in place since 2024.
3. **The five mechanisms interact and nothing checks the interaction.** Adding DF2W Sharia (product 15) touched all five. There is no test that executes any of them ([bravo-testing.md §2](bravo-testing.md)).

**Bravo's real deploy risk is not flags, it is child-process binding.** No `callActivity` sets `camunda:calledElementBinding`, so redeploying a sub-process changes behaviour for running loans at their next call — including NDF2W loans entering unified underwriting. That is 73% of production volume with no migration plan. It is covered in [bravo-testing.md §3](bravo-testing.md) and it is the single most important "what deploys to whom" question on this platform.

---

## 2. Custom front end: easy per page, hard per system

LORA's complaint was that a custom widget is three layers — templ emits a custom tag, SolidJS registers the `customElement`, HTMX carries the value back — and that field-by-field templ cannot see sibling fields. Production bore it out: a script injected twice (8,067×/week) and hydration-order null dereferences (~34,900×/week).

**Bravo has none of that seam.** Each console is a plain React application talking to REST endpoints that speak domain verbs — `PATCH /v1/underwritings/{id}/approval/bm-decision`, `PUT …/approver-decision`. The UI never sees a Camunda task id or a form definition. Adding a field, a control or a whole page is ordinary front-end work.

**The cost is on the other axis: how many front ends there are.** The RUM inventory for the org lists, in the Bravo/LOS orbit:

| Console | Instrumented |
|---|---|
| Surveyor Platform (Prod + Test) | ALL |
| Operation Platform (Prod + Test) | ALL |
| Underwriting Platform (Prod + Test) | ALL |
| Backoffice Web App | ALL |
| Supplier Web App | ALL |
| Customer Platform 4W · 2W · Sharia · **DF** · unified | ALL |
| Agency Cockpit | NONE |
| `prod-bravo-e-line-ui`, `prod-notary-ui`, `prod-bravo-lms-fe`, `prod-bravo-lms-fund-fe`, `Prod LMS Core FE`, `prod-bfi-dashboard-digital-fe`, `prod-bravo-edoc-download`, `PROD-DMS-FE`, `EGC Platform`, agent and RO tooling | mixed |

That is **at least fifteen browser applications** where LORA has two (back office and customer). Every shared concept — an approval banner, an asset-category field, a status label — is implemented and maintained once per console that shows it. The `BLCS` ticket stream shows the consequence directly: `BLCS-4397` *"Shared summary section config for both surfaces"* and `BLCS-4398` *"Verify section matrix across 5 flows on both surfaces"* are one story spending its effort on keeping two consoles consistent.

**The coordination tax, now measured rather than asserted (added 2026-09-10).** The three LOS consoles were checked out for the first time: **763,861 lines of source across 5,066 files, 829 test files, 4,334 commits in the last 12 months.** They share a design system, `@bfi-finance/frontend-ui` — and it has drifted, along with the platforms underneath it:

| | `bravo-surveyor-console` | `bravo-operation-console` | `bravo-underwriting-console` |
|---|---|---|---|
| `@bfi-finance/frontend-ui` | `3.0.155` pinned | **`3.0.138`** pinned — 17 releases behind | `^3.0.158` range |
| React | `^17.0.2` | **`^18.2.0`** | `^17.0.2` |
| MUI `@mui/material` | `^5.4.4` | `^5.3.1` | `^5.16.7` |
| `@testing-library/react` | `^12.1.2` | **`^14.0.0`** | `^12.1.2` |
| Vite | `7.3.6` | `7.3.6` | **`4.5.0`** |
| Linter | ESLint | **Biome** | ESLint |
| CI Node | 20 | 20 | **18** |
| Owning squad | `LN` | `LN` | `BLCS` |

**Three consoles, three versions of the shared component library, two major versions of React, two major versions of Vite, two linters and two Node versions.** This is the coordination tax made concrete, and it is worse than "implemented once per console": a shared design system *exists*, so the cost was recognised and paid for — and then the consoles diverged anyway. The React 17/18 split is the one to watch, because `@bfi-finance/frontend-ui` must now satisfy both, or one console is using it in a configuration it was not built for.

**It also has a practical consequence elsewhere in the pack.** [option-1.md §4a](option-1.md#4a-the-consoles-are-insulated-from-this-change) proposes running the three console suites as a boundary regression net for an engine cutover. That remains the cheapest net available — but it is **three toolchains, not one**: two React majors, two Vite majors, two Node versions. Budget for that, and expect the underwriting console (Vite 4, Node 18) to be the one that needs attention first.

**The honest scoring.** Per page, Bravo is clearly easier and LORA's JsForm work is an attempt to reach where Bravo already is. Per system, Bravo pays a coordination tax LORA does not have, and it pays it in exactly the place where its production error volume is concentrated ([§5](#5-what-production-actually-says-about-the-front-ends)). The drift table above is the tax's invoice.

---

## 3. Pagination: Bravo built it, it is called `FormTab`, and it is the busiest read path

LORA's delivery document says complaint 8 is **misstated**, on this reasoning: *"In Bravo the surveyor saw all fields from all tasks on one giant form. They needed pagination by logical group. In LORA the surveyor opens one task and sees only that task's fields."*

**That account is correct, and it can now be verified from Bravo's own production telemetry rather than from memory.** Grouping `spring.handler` spans by resource, 48 hours:

| Controller | spans / 2 d | What it is |
|---|---:|---|
| `PartnershipConfigurationController.getByApplicationId` | 73,056 | per-application configuration (and the 404 storm — [§5](#5-what-production-actually-says-about-the-front-ends)) |
| **`SurveyorAssignmentFormTabV2Controller.findByAssignmentId`** | **33,673** | **the paged form itself, v2** |
| `ApplicationDocumentTrackingController.get` | 32,820 | documents pane |
| `SurveyorAssignmentManualKycController.scoring` | 30,591 | KYC pane |
| `SurveyorAssignmentController.exposeSurveyData` | 8,535 | survey payload |
| `SurveyorAssignmentCompanyDataController.findByAssignmentId` | 7,526 | company pane |
| `SurveyorAssignmentCompanyLegalityDocumentController.findByAssignmentId` | 7,476 | legality pane |
| `SurveyorAssignmentCapitalDetailController.findByAssignmentId` | 6,413 | capital pane |
| `LongSurveyController.findAllByApplicationId` / `findByAssignmentId` | 5,077 / 4,903 | long-survey panes |

Plus three more per-assignment sub-resources visible in the 404 table: `surveyor-assignment-other-business`, `surveyor-assignment-asset-validation-two-wheeler`, `surveyor-assignment-request`.

**A controller named `FormTabV2` is a pagination mechanism that has already been through one major version.** Nine or more sub-resource endpoints per assignment is "pagination by logical group" implemented as one endpoint per group. It works, it is heavily used, and it is the dominant read path in `ms-bpm`.

Three things follow.

**LORA's recommendation stands and is now better evidenced.** Nobody should rebuild Bravo-style whole-application paging in LORA, because LORA's surveyor genuinely opens one task. The two systems present different objects.

**Bravo's design is not a workaround; it is a consequence of the object it presents.** A Bravo surveyor opens an *assignment*, which spans the whole application. Paging it is the only sane thing to do. Calling this a defect misreads it.

**But it has a real cost that LORA does not pay:** opening one assignment issues roughly ten HTTP requests, each a controller, each a set of JPA `repository.operation` spans against `prod-postgres-bpm-d2bpm` — which is 34.7% of Bravo's production Cloud SQL bill ([bravo-cost.md §5](bravo-cost.md)). And **four of those ten endpoints are the top four sources of the 404 storm** ([§5](#5-what-production-actually-says-about-the-front-ends)), so the paging surface is also the failure surface.

---

## 4. Master data: Bravo has the feature LORA declined to build

LORA's complaint 9 was "master data tables cannot feed dropdowns", graded *overstated; the design is intentional*: LORA loads BFI DMS into a process-global cache at worker startup, copies values onto the loan document at write time, and deliberately does not support ad-hoc SQL from a form — so codes and labels stay consistent for the life of the loan.

**Bravo does the thing LORA refused to do, and it is a genuine delivery advantage.**

| | Bravo | LORA |
|---|---|---|
| Where dropdown options come from | LOV tables in the same database (`underwriting_job_level_lov`, `underwriting_job_level_lov_detail`, `surveyor_coverage`, `surveyor_level`) plus live calls to master-data services | process-global cache loaded at worker start from BFI DMS; JSON Schema `enum`/`lov`; widget APIs |
| Master-data traffic, 7 days | `prod-ms-product` 31,463 · `prod-ms-master` 27,954 · `prod-ms-branch` 22,784 · `prod-ms-employee` 64,725 | ~620k LORA calls/week to `prod-ms-master` alone, via the gateway |
| Adding a new lookup | insert rows; the form reads them | LGS inner proxy + schema `lov` (+ optional cache key) — a multi-repo change |
| Renaming a role across the approval ladder | **one YAML line, one SQL `UPDATE`, zero Java** (`BLCS-4683`, NMH→GMB) | a schema change and a redeploy |
| Consistency for the life of the loan | **not guaranteed** — options are read live | guaranteed by copying values onto the document at write |

**The `BLCS-4683` case is the strongest single argument for Bravo's approach in this pack.** Renaming an approval role across a staged ladder — the kind of change that ordinarily ripples through code — was a configuration edit, because the ladder is `underwriting_job_level_lov_detail` rows ordered by `global_level` (CAFH 200 → AMB 300 → CCU 400 → GMB 600) snapshotted onto approver rows. That is data-driven delivery working exactly as intended.

**And the cost is exactly the one LORA designed around.** Because options are read live, a master-data edit changes what a form offers immediately, including for applications already in flight and already decided on the old list. Bravo mitigates this partially — the approver ladder is *snapshotted onto approver rows* at assignment — but that is one path, done deliberately, not a platform property. LORA's guarantee is structural: the values are on the loan document, so a mid-flight DMS change cannot alter what the surveyor already confirmed.

There is a live illustration of the risk in the ticket stream. `BLCS-4683` renamed NMH→GMB in September 2026; `BLCS-4811`, three days before this document, is *"[BE] Prepare Query Change GMB to NMH"* — the rename is being reversed. A configuration change that is cheap to make is also cheap to make twice, and each edit lands on whatever applications are in flight at that moment. **Nothing in Bravo records which applications were decided under which version of the ladder**, because the master-data tables have no temporal dimension and Camunda's history purges at 90 days.

**Neither design is wrong.** Bravo optimised for change velocity on slowly-changing reference data and got it. LORA optimised for per-loan immutability and pays a multi-repo change for every new lookup. The right answer differs per lookup, and neither platform lets you choose per lookup.

---

## 5. What production actually says about the front ends

Sections 1–4 are code and configuration reading. They did not have to be. **All four production Bravo LOS consoles are RUM-instrumented at `rum_event_processing_state: ALL`**, and — as with LORA's back office — nobody had looked.

Seven days:

| Console | Sessions | Views | Actions | **Errors** | Errors/view |
|---|---:|---:|---:|---:|---:|
| **Surveyor Platform Prod** | 79,090 | 953,115 | 3,739,210 | **1,962,909** | **2.06** |
| Operation Platform Prod | 17,135 | 96,707 | 2,516,533 | 287,646 | **2.97** |
| Underwriting Platform Prod | 15,628 | 205,666 | 1,964,283 | 124,422 | 0.60 |
| Customer Platform DF | 2,594 | 31,412 | 87,473 | 38,221 | 1.22 |
| **Total** | **114,447** | **1,286,900** | **8,307,499** | **2,413,198** | **1.88** |

For scale: LORA's back office produces 416,201 errors a week at ≈2.8 per view over 24,172 sessions. **Bravo's LOS consoles produce 5.8× the error volume at a comparable per-view rate.** Both teams had the instrumentation and neither was reading it.

Top errors on the Surveyor Platform — the console behind `Surveyor Platform - Release reject`, 28.4% of Bravo's entire support-ticket load:

| Error | Count / 7 d | Reading |
|---|---:|---|
| **`Request failed with status code 404`** | **748,686** | **38% of this app's errors. Four endpoints, below** |
| `csp_violation: 'https://surveyor.bfi.co.id/cdn-cgi/rum?' blocked by 'connect-src'` | 35,415 | Cloudflare RUM beacon — cosmetic, but it is the second-largest row |
| `intervention: Ignored attempt to cancel a touchmove event…` | 20,928 | tablet touch/scroll — surveyor devices |
| `Request failed with status code 400` | 12,796 | |
| `csp_violation: '…:443/cdn-cgi/rum?' blocked by 'connect-src'` | 10,573 | same beacon, explicit-port origin |
| **`Error getting location: "[GeolocationPositionError]"`** | **10,365** | **surveyors cannot get a position** |
| **`Unable to get current position`** | **10,325** | same defect, second message |
| `Request failed with status code 401` | 7,402 | the browser face of 8,533 IAM 401s ([bravo-observability.md §4](bravo-observability.md)) |
| `Network Error` | 6,828 | |
| `Cannot read properties of null (reading 'filter')` | 6,445 | real null dereference |

### Three findings that change this document

**A. The 404s are the paging surface from [§3](#3-pagination-bravo-built-it-it-is-called-formtab-and-it-is-the-busiest-read-path).**

| Endpoint | 404s / 7 d | distinct sessions |
|---|---:|---:|
| `/bpm/v1/partnership-configuration/feature-configuration` | **266,767** | **54,350 of 79,090 — 69%** |
| `/bpm/v2/surveyor-assignment-form-tab/assignment/{id}` | 157,623 | 37,359 |
| `/bpm/v1/application-document-tracking` | 154,097 | 45,916 |
| `/bpm/v1/surveyor-assignment-manual-kyc/scoring/assignment/{id}` | 143,180 | 31,565 |
| `/surveyor/assignment-detail/{id}` | 21,125 | 14,754 |
| `/surveyor/assignment` | 14,565 | 11,287 |

Three of the top four are the assignment sub-resource endpoints — the `FormTab` paging model. The first is the busiest handler in the entire service. **Two-thirds of all surveyor sessions receive a 404 from it.** Whether that is benign (an optional configuration probe where 404 means "no override") or a defect is a question for the controller, not for telemetry — but at this volume, on this console, it has to be asked. It is section 3's mechanism and section 5's largest error, and nobody had connected them because nobody had opened either view.

**B. Geolocation fails ~20,700 times a week on a platform spending Rp64.0M/month on Maps APIs.** `GeolocationPositionError` and `Unable to get current position` are the same defect reported twice. Surveyors are field staff whose submissions depend on position capture. Separately, [bravo-cost.md §5](bravo-cost.md) finds Geocoding, Places and Maps billing **Rp63,979,414 in August** in the Bravo production project. This document does not claim the two are causally linked — a browser geolocation failure and a server-side Maps call are different layers — but they are the same feature, in the same console, and neither has been examined.

**C. No alert can see any of this.** Every `prod-ms-bpm` health monitor is written as `(hits − hits{http.status_code:5*}) / hits < 99`. A 404 is a success by that definition, and none of the 38 monitors touches RUM at all ([bravo-observability.md §5](bravo-observability.md)). This is the delivery-side face of the same finding: Bravo can ship a console change that 404s two-thirds of sessions and every signal it owns stays green.

**Caveats.** RUM sessions are sampled and the counts include benign browser noise — the two CSP rows (45,988 combined) are a third-party beacon and are cosmetic, and `utc_offset is deprecated` (5,950) is a library warning. Treat the 404 rows, the geolocation rows and the null dereference as the actionable ones. Window is 7 days to 2026-09-10.

### How to reproduce

```
# Datadog RUM, Surveyor Platform Prod
@application.id:2f3ca103-2053-4601-8e2a-5de3aee713bb @type:error
  → group by @error.message

# the 404 endpoints
@application.id:2f3ca103-2053-4601-8e2a-5de3aee713bb @type:resource @resource.status_code:404
  → group by @resource.url_path_group, count(*) and cardinality(@session.id)
```

---

## Recommended actions

1. **Read the `feature-configuration` 404 (S, do this first).** 266,767 a week, 69% of surveyor sessions, on the busiest handler in the service. Decide whether 404 is the intended "no override" response — and if it is, stop the client raising it as an error, because it is currently drowning that console's error stream. If it is not, this is a live production defect that has been invisible for as long as anyone has data for.
2. **Fix the geolocation failures, and check them against the Maps bill (S–M).** ~20,700 failures a week on a field-staff console. Establish the cause (permissions, HTTPS context, device, timeout) and whether the retries are billed against the Rp64.0M/month Maps line.
3. **Set a front-end error budget per console (S).** Today the Surveyor Platform runs at 2.06 errors per view and Operation at 2.97, and no number would move if either doubled. One SLO per console, reviewed weekly, is the cheapest thing on this list.
4. **Filter the CSP beacon rows (S).** 45,988 `cdn-cgi/rum` violations a week are cosmetic and are the second- and fifth-largest rows on the Surveyor Platform. Either allow the origin in `connect-src` or stop loading the beacon; right now they hide real errors.
5. **Build a feature-flag registry (S–M).** 78 gateway lookups plus the Java flags plus the selector tables, with no list of what is live, what it gates, who owns it, or when it can be removed. Start by listing them; the removal candidates will be obvious.
6. **Pin `calledElementBinding`, or accept in-flight child migration deliberately (S–M).** This is the real "choose what deploys" question on Bravo and it is currently answered by default. Cross-referenced in [bravo-testing.md](bravo-testing.md) recommendation 1.
7. **Inventory the consoles and name a shared component owner (M).** At least fifteen browser applications, with stories already spending their effort on "both surfaces". Either a shared component library with an owner, or an explicit decision that each console diverges.
8. **Give slowly-changing reference data a version, or a snapshot (M).** The NMH→GMB rename and its in-progress reversal show a configuration lever cheap enough to pull twice. Applications decided under the old ladder are not distinguishable from those decided under the new one after 90 days. Either version the LOV tables or snapshot the values onto the application, as the approver rows already do.
9. **Instrument Agency Cockpit, or retire it (S).** It is the one LOS-adjacent console with `rum_event_processing_state: NONE`.

---

## Plan: 30, 60, 90 days

Nine recommendations, phased against ~25 person-days a month of Squad S&U time and a slice of Platform/SRE.

**Sequencing rule for this document: fix what users hit before rebuilding what engineers dislike.** The 404 storm reaches 69% of surveyor sessions on the console that generates 28.4% of Bravo's support tickets; the console inventory and the shared-component question are structurally important and hurt nobody today. So the live defects go first and the architecture of the delivery surface goes last.

**Shared with other documents.** Recommendation 1 is also [bravo-observability.md](bravo-observability.md) rec 1 and [bravo-cost.md](bravo-cost.md) rec 5; recommendation 2 pairs with [bravo-cost.md](bravo-cost.md) rec 3; recommendation 3 pairs with [bravo-observability.md](bravo-observability.md) rec 10; recommendation 6 is [bravo-testing.md](bravo-testing.md) rec 1. Phased identically everywhere — do them once.

### Days 0–30 — the live defects and the cheap noise

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Read the `feature-configuration` 404** — is 404 the intended "no override" response, or a defect? | 1 | S&U | 2 d | A written answer for the endpoint hitting 54,350 of 79,090 sessions |
| **Act on the answer** — resolve the lookup, or stop the client raising it as an error | 1 | S&U | 3 d | The Surveyor Platform's error stream drops by roughly a third, and whatever the 404 was hiding becomes visible |
| **Filter or allowlist the CSP beacon** — 45,988 `cdn-cgi/rum` violations a week | 4 | Platform | 1 d | The 2nd and 5th largest error rows on the Surveyor Platform disappear. Real errors stop being buried |
| **Instrument Agency Cockpit, or retire it** | 9 | Platform | 1 d | No LOS-adjacent console is left at `rum_event_processing_state: NONE` |
| **`calledElementBinding` investigation — read-only** *(shared; see [bravo-testing.md](bravo-testing.md))* | 6 | S&U | 5 d | The real "choose what deploys" question has a written exposure note. No code change |

### Days 31–60 — budgets, the field defect, and the flag inventory

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Fix the geolocation failures** — ~20,700 a week on a field-staff console; establish cause (permissions, HTTPS context, device, timeout) | 2 | S&U | 5 d | Surveyors stop failing position capture. Cause documented and cross-checked against the Rp64.0M/month Maps line |
| **Set a front-end error budget per console** — one SLO each, reviewed weekly | 3 | Platform/SRE + EM | 2 d | Today Surveyor runs at 2.06 errors/view and Operation at 2.97 and nothing would move if either doubled. A console regression is caught by a number instead of by 315 `Release reject` tickets a month |
| **Build the feature-flag registry** — 78 gateway lookups plus the Java flags plus the selector tables: what is live, what it gates, who owns it, when it expires | 5 | S&U | 4 d | Somebody can answer "what is `featRefactorWorkflow` gating and can we delete it" without reading 53 BPMN files. Removal candidates become obvious |
| **`calledElementBinding` decision** *(shared)* | 6 | S&U + EM | 2 d | A recorded decision with a migration plan |

### Days 61–90 — the delivery surface itself

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Implement the binding decision** *(shared; effort carried in [bravo-testing.md](bravo-testing.md))* | 6 | S&U | — | Redeploying a unified sub-process stops silently changing the path of in-flight NDF2W loans |
| **Inventory the consoles and name a shared-component owner** — at least fifteen browser applications, with stories already spending their effort on "both surfaces" | 7 | EM + FE leads | 3 d | Either a shared component library with an owner, or an explicit, recorded decision that consoles diverge |

### Deferred, with triggers

| Deferred | Rec | Why | Trigger |
|---|---|---|---|
| **Shared component library** (beyond the inventory) | 7 | An organisational decision with a budget, not an engineering task | After the phase-3 inventory |
| **Version or snapshot slowly-changing reference data** — the NMH→GMB rename and its in-progress reversal | 8 | 10 days, and the design depends on the Camunda history decision in [bravo-cost.md](bravo-cost.md) rec 4, because both concern what is knowable after day 91 | After that decision lands |

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| `feature-configuration` 404 resolved | The Surveyor Platform's error stream drops by roughly a third, and whatever the 404 was hiding becomes visible. |
| Geolocation fixed | Field surveyors stop failing position capture ~20,700 times a week, and the Maps line gets an explanation. |
| Front-end error budgets | A console regression is caught by a number instead of by 315 `Release reject` tickets a month. |
| Flag registry | Somebody can answer "what is `featRefactorWorkflow` gating and can we delete it" without reading 53 BPMN files. |
| `calledElementBinding` decided | Redeploying a unified sub-process stops silently changing the path of in-flight NDF2W loans. |
| Console ownership | "Shared summary section config for both surfaces" is a component change, not a story. |
| Reference data versioned | The question "which ladder was this application approved under" has an answer at day 120. |

---

## Related

- [bravo-observability.md](bravo-observability.md) §5, §6 — the monitors that cannot see any of this, and the 404 endpoint table
- [bravo-testing.md](bravo-testing.md) §3, §4 — child-process binding, and where model validation actually happens
- [bravo-cost.md](bravo-cost.md) §5 — the Maps and Cloud Logging lines behind two of these findings
- [bravo-people.md](bravo-people.md) §6 — why a Bravo change is fewer artefacts than a LORA one
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.4, §3.8, §3.11 — the guard layer, product discrimination and versioning in code terms
- LORA [delivery.md](../../lora-workspace/docs/production-findings/delivery.md) — the four questions asked of the other platform
