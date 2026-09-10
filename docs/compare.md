# Bravo vs LORA: production findings, side by side, and where the next product should go

**Audience:** CTO office, platform leadership, product leadership
**Question:** Synthesising people, testing, observability, cost and delivery — which platform should BFI prioritise for hosting future business products?

**What this document is.** The five Bravo production-findings documents ([people](bravo-people.md), [testing](bravo-testing.md), [observability](bravo-observability.md), [cost](bravo-cost.md), [delivery](bravo-delivery.md)) each answer one question about Bravo and set it against LORA's equivalent. This document puts all five in one matrix and turns them into a recommendation.

**What this document is not.** It is not the architecture comparison. That is [compare-architecture.md](compare-architecture.md) — the paradigm-level reading of BPMN against GSM+Temporal, including the Bravo team's review of it. That document's verdict stands and is not re-litigated here. This one is about how the two platforms *behave in production and under delivery pressure*, which is a different question and, for a hosting decision, the more decisive one.

**Method.** Everything below is measured, and every row names where. New measurements taken 2026-09-10: Jira (`DF`, `D2W`, `BL`, `BLCS`), Datadog `us5` (APM spans, logs, monitors, Synthetics, CI Visibility, RUM on four Bravo consoles), and GCP billing via the FinOps API for complete-month August 2026. Carried forward: the OTRS ticket export ([ticket-analysis.md](production-findings/ticket-analysis.md)), the 90-day PostgreSQL and Datadog volume split ([workflow-gap.md §8](workflow-gap.md)), and the LORA production-findings pack.

> **Revised 2026-09-11.** Three findings landed after the first version: Bravo's journey suite **exists and was abandoned** rather than never built ([testing §6](bravo-testing.md)); Bravo **cannot make an upstream fail on demand**, so its retry and degrade policy is entirely unverified ([testing §7.4](bravo-testing.md)); and the two test layers that would catch the most in Bravo **run in milliseconds** ([testing §7.2](bravo-testing.md)). The first two change rows in §1 and a recommendation in §5. **The recommendation in §5 stands.**

**Two caveats that qualify every row.** Application counts on both sides come from a billing sheet whose platform totals nothing else corroborates, so every *per-application* figure is a verified numerator over a disputed denominator. And Bravo is being drained into LORA, so it keeps the residual hard cases — a real confound, not controlled for.

---

## 1. The matrix

| Dimension | **Bravo LOS** | **LORA** | Edge | Source |
|---|---|---|---|---|
| **PEOPLE** | | | | |
| Active engineers on the platform (sampled) | **7** distinct assignees across 100 sampled tickets; the Story layer held by **one** account | **22** distinct assignees across 100 sampled tickets | **LORA** | [people §5](bravo-people.md) |
| Delivery tickets, Jan–Aug 2026 | ≈2,813 (`BLCS`) | ≈5,144 (`BL`) | LORA (1.83×) | [people §3](bravo-people.md) |
| Median ticket cycle time, Aug 2026 | **2 days** | **2 days** | tie | [people §4](bravo-people.md) |
| Repositories touched per integration change | **1** | **5**, in a mandated order | **Bravo** | [people §6](bravo-people.md) |
| Hiring pool | Java/Spring/Camunda — commodity | Go + bespoke GSM planner + Temporal | **Bravo** | [people §7](bravo-people.md) |
| Week-1 curriculum | none | none | tie (both bad) | [people §7](bravo-people.md) |
| **TESTING** | | | | |
| Test files | 1,457 in one repo, all running | 608 across 13 repos; 4 repos at zero, SDK has no CI workflow | Bravo | [testing §1](bravo-testing.md) |
| Tests that execute the orchestration | **4** of 1,457 (0.27%) | planner scheduling untested; 16 planner tests, all rollback | tie (both absent) | [testing §1](bravo-testing.md) |
| Can CI say "this change hits NDF2W"? | **No** — product identity in 5 places, and `ndf2w.bpmn` bridges into unified underwriting (73% of volume) | **No** — but product families are isolated by schema, worker and queue | LORA | [testing §3](bravo-testing.md) |
| Where the model is validated | **production, at pod boot** — 38,198 parse warnings/week, non-fatal | worker startup — fatal panic on a missing path | LORA | [testing §4](bravo-testing.md) |
| Coverage gate | none (JaCoCo `report`, no `check`) | none; floor proposed | tie | [testing §1](bravo-testing.md) |
| Automated journey test | **exists and was abandoned.** 595 Cypress/Cucumber features in `bravo-e2e-test`, 349 on the Surveyor Platform; 4 CI workflows, 1 scheduled weekly — **every step ends `\|\| true`, so it cannot fail**; frozen 2023-11-21. Plus 8 org Synthetics, all DNS/SSL, and zero CI events | nightly partner-E2E exists, asserts a terminal condition, **mostly red** | **LORA** | [testing §6](bravo-testing.md) |
| Assertion quality of the journey suite | **82%** of 25,805 `Then`/`And` steps contain no assertion verb; 70% of files named `Positive TestCase` | asserts a terminal condition per journey | **LORA** | [testing §6](bravo-testing.md) |
| Can a test make an upstream fail on demand? | **no.** `bravo-mock-service` is static and shared, so **50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths are unexercised** | **yes** — a spec steers one answer with a 2-line delta | **LORA** | [testing §7.4](bravo-testing.md) |
| Cost of closing the test gap | **L0 + L1 are days and run in seconds**; 6 of 9 layers absent but the two highest-value run in **milliseconds** | CI runner exists but has nowhere to run; SIT access unresolved | **Bravo** | [testing §7.2](bravo-testing.md) |
| Health assumption | **"not 5xx = healthy"** | "still Running = healthy" | tie (both wrong) | [testing §5](bravo-testing.md) |
| **OBSERVABILITY** | | | | |
| Spans on the orchestration layer | **zero** — 7 operation names, none Camunda | **one span per activity attempt**, carrying the loan id | **LORA** | [obs §2](bravo-observability.md) |
| Per-activity failure ranking | **yes** — `@activityName` on engine logs; `One Obligor Check` 5,583/48h | yes — `@ActivityType` + `@Attempt` | tie | [obs §3](bravo-observability.md) |
| Join a failure to a loan | **no** — no application id on any log line | **yes** — `@WorkflowID` *is* the application UUID | **LORA** | [obs §3](bravo-observability.md) |
| "All loans stuck in survey?" | **yes, in SQL** — relational state | **no** — zero Temporal search attributes | **Bravo** | [obs §1](bravo-observability.md) |
| Which upstream is failing? | **yes, structurally** — 25 hosts from Feign/OkHttp spans | **no** — ~300 proxies on one route; fix merged, undeployed | **Bravo** | [obs §4](bravo-observability.md) |
| Upstream error profile | 20,802/week, **zero 5xx in the top 20**; 1.07 errors per trace — broad defects | ~65,500 4xx + 1,155 5xx/week; **93% from 24 workflows** — retry loops | different failures | [obs §4](bravo-observability.md) |
| Monitors | 38 — **zero process-level**; 8 permanently `Alert`, 6 `No Data` | 47+ — including a wedged-loan alert firing since January; 8 never evaluated | tie (both broken the same way) | [obs §5](bravo-observability.md) |
| Durable substrate | **PostgreSQL** — status log by DB trigger, reprocess generations as rows; step trace purges at **90 days** | document + version chain + Temporal history; logs ~7 days, spans 30 | **Bravo** for business facts | [obs §7](bravo-observability.md) |
| **COST** (August 2026, GCP net, IDR) | | | | |
| Orchestration tier, production | **≈Rp 58M** (`ms-bpm` pods + its Cloud SQL) | ≈Rp 431M all-in | **Bravo (7×)** | [cost §3](bravo-cost.md) |
| Per application | **≈Rp 510–760** | ≈Rp 2,500–3,200 | **Bravo (4–5×)** | [cost §3](bravo-cost.md) |
| Whole GCP footprint | Rp 1,887M (50.9% of BFI's entire GCP bill — mostly the shared data plane **LORA also calls**) | ≈Rp 431M | not comparable | [cost §2](bravo-cost.md) |
| Marginal cost per extra application | pods + database — small but non-zero | **≈zero**: +23% volume for +3% spend | **LORA** | [cost §4](bravo-cost.md) |
| Direction of unit cost | **worsening** — fixed cost, volume −35% in one month | improving | **LORA** | [cost §4](bravo-cost.md) |
| Largest addressable line | **Cloud Logging Rp 140.5M/month** — 2.4× the orchestration tier, and it is configuration | Temporal Actions programme, Rp 7.2M | — | [cost §5–6](bravo-cost.md) |
| **DELIVERY** | | | | |
| Feature flags | **five mechanisms**, no registry; gateway flags need a restart; per-application jsonb activity matrix is genuinely good | `$.experiments.*` per-loan stamps + schema-versioned workers | tie | [delivery §1](bravo-delivery.md) |
| In-flight deploy safety | **no `calledElementBinding`** — a unified sub-process redeploy reaches in-flight NDF2W loans at their next call | schema-versioned queues; old loans stay on old workers | **LORA** | [delivery §1](bravo-delivery.md) |
| Custom UI on a page | easy — plain React on domain REST verbs | three layers (templ → customElement → HTMX); JsForm is the fix | **Bravo** | [delivery §2](bravo-delivery.md) |
| Front-end surface | **≥15 browser applications** | 2 | **LORA** | [delivery §2](bravo-delivery.md) |
| Pagination | **solved** — `SurveyorAssignmentFormTabV2Controller` + 9 sub-resource endpoints, the busiest read path in the service | not needed — one task, one form | both correct for their object | [delivery §3](bravo-delivery.md) |
| Master data → dropdowns | **yes, live** — role rename was 1 YAML line + 1 SQL `UPDATE` + zero Java | startup cache, values copied onto the loan; no ad-hoc SQL | **Bravo** on speed, **LORA** on consistency | [delivery §4](bravo-delivery.md) |
| Front-end errors, 7 days | **2,413,198** across 4 consoles (1.88/view); **748,686 are 404s**, one endpoint on **69% of sessions** | 416,201 (2.8/view) on the back office | **LORA** (5.8× less) | [delivery §5](bravo-delivery.md) |
| **RELIABILITY** (carried from [ticket-analysis.md](production-findings/ticket-analysis.md)) | | | | |
| Manual-intervention rate, Jun–Aug | **≈0.443%** — 1 in 225 | **≈0.126%** — 1 in 790 | **LORA (3.5×)** — but see §4 | |
| Ticket trend, Jan→Aug (stable categories) | **×1.82 while volume fell 35%** | ×0.66 while volume rose | **LORA** | |
| Failure shape | bounded, classified, parked in an operator console — **no zombie class** | uncapped retry; ~half of loans never terminate | **Bravo** on shape | |
| **VOLUME** | | | | |
| Applications, Aug 2026 | 76,446 (31%) | 171,479 (69%) | — | |
| Products on the modern generation | **DF4W only — 5.5% of Bravo volume. DF2W: fully configured, zero applications** | 7 product families, 13 repos | **LORA** | [workflow-gap §8](workflow-gap.md) |

---

## 2. What each platform is genuinely better at

**Bravo is better at:**

- **Running cheaply.** ≈Rp58M against ≈Rp431M, ≈Rp510–760 per application against ≈Rp2,500–3,200. One deployment, one database.
- **The cost of one change.** One repository, one deploy, no cross-service ordering rule. The five-repo LORA tax is real and measurable.
- **Fleet questions about business state.** Relational state means "all loans stuck at survey" is a `WHERE` clause. LORA cannot express this at all.
- **Upstream attribution.** 113 typed Feign clients give per-upstream, per-status attribution for free. LORA's 300-proxies-one-route design cannot.
- **Durable business history.** Every reprocess generation is a queryable row. Nothing has to be replayed.
- **Bounded, classified failure.** Fail-fast checkpoints, business errors as BPMN errors, degrade on last attempt, an operator console. No zombie loans by construction.
- **Configuration-driven change on reference data.** A staged approval-role rename was one YAML line and one SQL `UPDATE`.
- **A cheaper test boundary.** 113 typed Feign interfaces mean stub drift is caught by `javac`. LORA needs a `check:stubs` script against a live schema registry to get the same guarantee ([testing §7.1](bravo-testing.md)).
- **Commodity skills at hiring.**

**LORA is better at:**

- **Adding automated steps.** 172 activities against 3 hard precursors, no orchestration edit. The clearest validated architectural win.
- **Seeing what the orchestrator is doing.** One span per activity attempt, carrying the loan id. Bravo emits **zero** spans for its entire orchestration layer.
- **Joining a failure to a customer.** `@WorkflowID` is the application UUID. Bravo cannot do this from telemetry at all.
- **Not needing a person.** ≈0.126% intervention rate against ≈0.443%, and falling while Bravo's rises.
- **Marginal cost.** Near zero per additional application. Bravo's is small but real, and its unit cost is inflating as it drains.
- **Product isolation.** Separate schemas, workers and queues. Bravo has one job executor for every product and product identity in five places.
- **In-flight deploy safety.** Schema-versioned queues against Bravo's unpinned child processes.
- **Team breadth.** 22 active contributors against 7, with LORA's Stories distributed and Bravo's held by one account.
- **A journey test that runs and asserts.** LORA's nightly is mostly red and that is bad. **Bravo's is worse in a more specific way:** 595 feature files exist, one workflow is scheduled, and every step in it ends `|| true` — so it reports success whether the loan journey worked or not, on 10 of 595 files, and has been frozen since 2023-11-21. A red test can be fixed. **A permanently green one actively misleads**, and 82% of the corpus's `Then` steps assert nothing even if it ran.
- **A verified failure policy.** LORA's retry behaviour is bad *and measured*. Bravo's is well-designed and **unverified** — nothing in Bravo can make an upstream fail, so the degrade paths this document recommends porting have never been executed by a test.

---

## 3. Where they converge — and what that means for the decision

Seven things are the same on both platforms, and they matter because **anything that is the same on both cannot be a reason to choose either.**

1. **Human-task complexity is paradigm-independent.** Bravo spends 44% of its code on human work; LORA has ~12k lines of hand-written FSMs inside a declarative shell. Neither engine's native task model was used.
2. **The orchestration layer is untested in both.** 4 of 1,457 Bravo tests execute a process; LORA's planner scheduling is untested and its nightly is red.
3. **Both built a journey suite and left it unable to run.** Bravo: 595 Cypress features, 46 authors, four workflows, frozen 2023-11-21, and the one scheduled workflow written so it cannot fail. LORA: `lora-super-test`, 150 scenario tests, **a CI workflow file that has nowhere to run yet**. Two teams, two platforms, the same outcome — a large deliberate investment in journey testing that no longer gates anything. This is the closest structural parallel in the pack and neither team knew the other had it.
4. **The lifecycle FSM is declared and not enforced in both.** Bravo has a state-machine class used once; LORA validates enum membership only.
5. **Neither has saga compensation.** Both rely on sweepers, re-sync and humans for failed external commits.
6. **Both mistake the absence of one failure mode for health.** "Not 5xx" and "still Running" are the same error. Both teams also filtered their most informative error class out of their one business monitor — Bravo excluded `ENGINE-16004`, LORA excluded the go-live agreement message.
7. **Surveyor assignment is the top ops complaint on both, in the same words, at nearly the same rate** — 1,182 Bravo tickets (21.8%) and 1,021 LORA tickets (25.0%). A BPMN flowchart and a GSM planner each modelled assignment around a hand-written service layer and inherited its failure modes.

**Both teams also had rich instrumentation they were not reading.** LORA's two RUM applications had been on all along and were never consulted. All four Bravo LOS consoles are instrumented at `ALL` and produce 2.4M errors a week that nobody had opened. This is not an architecture finding; it is the same operational gap on both sides, and it is the cheapest thing on either backlog.

---

## 4. The four numbers that actually decide it

Strip out everything that converges and everything that is a wash. Four measurements carry the decision, and one of them points at Bravo.

**1. Bravo's orchestration is 4–5× cheaper per application — and the gap closes on its own.** ≈Rp510–760 against ≈Rp2,500–3,200. This is the strongest fact on Bravo's side and it should not be minimised. Two things bound it. The gap is caused by LORA's fixed contracts and over-provisioning — a 3-year CPU commitment, a Temporal commitment renegotiable at ~March 2027, 448 GB of requests at 15.5% utilisation, five idle worker versions — not by the paradigm. And Bravo's advantage erodes automatically: fixed cost over volume falling 35% in a month means ≈Rp1,450 per application at 40k/month without either team doing anything. Meanwhile **Cloud Logging alone (Rp140.5M/month) is 2.4× the entire tier the migration would retire**, and it is a configuration fix.

**2. Bravo needs a person 3.5× more often, and the trend is diverging.** ≈0.443% against ≈0.126%; ×1.82 against ×0.66 over eight months, with Bravo's volume falling and LORA's rising. **The honest qualifier is large**: the gap turns entirely on one category, `Surveyor Platform - Release reject` — 1,542 tickets, 28.4% of Bravo's load, growing 4.8×, and **still unmapped to any code path**. Remove it and Bravo's rate is 0.152% against LORA's 0.126% — level. Two other errors push the other way (Bravo's denominator is probably inflated; its operator console lets staff unstick applications without a ticket), so the 3.5× is more likely a floor than a ceiling. But it is one category away from being a wash, and mapping that category is days of work nobody has done.

**3. Bravo cannot see its own orchestration, and its proof that a loan can still be originated has been switched off.** Zero spans on the engine path. No application id on any log line. Zero process-level monitors among 38. Zero CI pipeline telemetry. **And the journey suite is the sharpest version of this:** Bravo built 595 Cypress features with 46 authors, aimed 349 of them at the Surveyor Platform, wired four CI workflows — then froze the repo in November 2023 and left the one scheduled workflow written so that every step ends `|| true` and it cannot report a failure. The continuous evidence that Bravo works is the support-ticket queue. **Two things follow, and they pull in opposite directions.** A platform in this state should not receive new product families, because each one adds surface that nothing watches. But the remediation is *cheaper than this document originally implied*: the two test layers that would catch the most in Bravo run in **milliseconds** and are days of work ([testing §7.2](bravo-testing.md)), and 349 usable journey descriptions already exist. **Bravo's testability gap is a decision nobody has made, not a mountain nobody can climb.**

**4. The claim that Bravo is easier rests on the two smallest things Bravo runs.** DF4W is the only product on the unified spine, 5.5% of Bravo's volume. DF2W is fully configured and has started **zero** applications in 90 days; its board is 22 unassigned epics. ~94% of Bravo's book runs on the legacy monoliths, which were edited *more* often in 2026 than the spine. The ergonomic advantage in [people §6](bravo-people.md) is real — one repository against five — but it has not been demonstrated at volume on the generation that carries the business.

---

## 5. Strategic recommendation

> ### Prioritise **LORA** for future business products. Do not start a new product family on Bravo. Do not accelerate the migration of what is already running there.

**The case, in one paragraph.** Bravo is cheaper to run and cheaper to change, and both of those are real. But BFI is not choosing a platform to run for one quarter; it is choosing where to put products that must be operated, observed, tested and staffed for years. On those axes Bravo is measurably behind and moving the wrong way: seven active engineers with the Story layer on one account, zero telemetry on the orchestration layer, a journey suite that was built by 46 people and then frozen with its one scheduled run unable to fail, a health model that missed a 748,686-per-week 404 storm on two-thirds of surveyor sessions, an intervention rate 3.5× LORA's, and an ops load rising 82% while its volume falls 35%. LORA has the opposite profile on every one of those, already carries 69% of applications across seven product families, and has a marginal cost near zero — so the next product costs it almost nothing to host. Bravo's cost advantage is the strongest counter-argument and it shrinks on its own as volume drains, while the single largest cost lever on either platform (Rp140.5M/month of Cloud Logging) is a Bravo configuration fix that has nothing to do with the decision.

**Three qualifications, stated plainly, because they are the parts most likely to be right and inconvenient.**

1. **This is not primarily an architecture verdict.** [compare-architecture.md §7](compare-architecture.md) concludes that the paradigm decided the shape of ~6–10% of each codebase and decided it in LORA's favour, while the other ~90% looks structurally similar. Nothing here overturns that. The recommendation rests on **capacity, observability and testability** — engineering discipline and staffing, not GSM versus BPMN. A well-staffed, well-instrumented Bravo would be a reasonable place to build. It does not exist today.
2. **LORA must fix four things or it will re-earn the criticism.** The five-repo per-change tax ([people §6](bravo-people.md)) is the true half of "Bravo is easier" and is addressable with a generator. Uncapped retry and the ~half of loans that never terminate are LORA's equivalent of Bravo's `Release reject` — a large, known, unfixed defect class. The gateway's 300-proxies-one-route blindness is a solved problem sitting in an undeployed PR. And LORA's orchestration cost is 4–5× Bravo's for reasons that are provisioning, not physics.
3. **Nothing here justifies rushing the remaining migration.** Bravo runs 76,446 applications a month, has bounded failure, and is the cheaper tier. The migration should finish because running two platforms costs two teams, not because Bravo is failing. Its ticket trend is a reason to invest in the Surveyor Platform, not to hurry.

### Port these four things from Bravo into LORA

The comparison produces a shopping list, and it is not one-directional.

| From Bravo | Why | LORA's gap |
|---|---|---|
| **A retry policy** — bounded attempts, fail-fast checkpoints, business-vs-transient classification, degrade-on-last-attempt, an operator queue | Bravo has no zombie-loan class *because the engine forced it to write one* | `MaximumAttempts: 0`, `NonRetryableErrorTypes: nil`, ~60,000 non-retryable 4xx/week retried as transient |
| **A designed dead-letter path** — `ApplicationErrorTracking` plus an operator console | Failure becomes visible and recoverable by someone other than an engineer | 1,269 force-cancels Jan–Aug; ops re-originates from event 1 |
| **Durable generations** — `prevApplication` / `currentIndex`, every attempt a row | Answers "what happened on day 120" without replay | rewind loses the prior generation |
| **Per-upstream attribution by construction** | "Which BFI service is degrading" is one query | 21k undifferentiated 500s/week; the fix is merged and undeployed |

And keep the degrade decision out of the exception handler: Bravo's `customErrorHandle` bypassing anti-fraud after three failures is a credit-policy decision hidden in error handling. If LORA adds terminal errors, decide explicitly whether terminal means *reject*, *park* or *skip*.

> **Port the design, not the assurance — this qualification is new and it matters.** Every row above is a *design* Bravo got right, and the evidence for each is that Bravo has no zombie-loan class in production. That evidence is real but it is **behavioural, not verified**: [testing §7.4](bravo-testing.md) establishes that **no Bravo test can make an upstream fail**, because `bravo-mock-service` is static and shared. So Bravo's **50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths have never been executed by a test** — including the anti-fraud `BYPASS`, which is a credit-policy decision reached by an exception handler. LORA should copy the shape of these four things and **write the negative tests Bravo never had** ([testing §7.4](bravo-testing.md), N0–N12) rather than inheriting the assumption that they work. LORA is better placed to do this than Bravo is: its mock interceptor can already fail any upstream on demand.

---

## 6. What would change this recommendation

Stated in advance, so the conclusion is falsifiable.

| Finding | Effect |
|---|---|
| **`Surveyor Platform - Release reject` maps to a defect that is then fixed** | Bravo's intervention rate falls to ≈0.152%, level with LORA's. Decision point 2 disappears and the recommendation weakens materially. **This is the single highest-value open item in the pack and it is days of work.** |
| **The billing owner defines the application counts** and Bravo's denominator is confirmed inflated | Bravo's true intervention rate rises and its per-application cost rises. Strengthens the recommendation. |
| Bravo is staffed to 15–20 engineers with a named shared-component owner | Removes decision point 3's capacity half. Would need to be sustained, not announced. |
| Bravo instruments the job executor, adds journey tests and 4xx health gates | Removes the observability half of decision point 3. All three are in [bravo-observability.md](bravo-observability.md) and [bravo-testing.md](bravo-testing.md) recommendations and are weeks, not quarters. **Cheaper than first stated:** layers L0 and L1 run in seconds and are ~7 days of work between them, and 349 existing feature files cover the journeys. |
| **`bravo-e2e-test`'s weekly cron turns out to still be firing** | Then Bravo has had a green-by-construction journey signal running for three years on 10 of 595 files. Strengthens decision point 3 rather than weakening it — a misleading signal is worse than none. Checking is **five minutes in the Actions tab.** |
| Bravo's negative suite (N0–N12) is built and the degrade paths pass | Confirms the four items in §5 are safe to port, and closes the largest verification gap on Bravo's side. Needs the per-run stub layer first ([testing §7.4](bravo-testing.md)). |
| LORA's never-terminating half and uncapped retry go unfixed for another two quarters | Weakens the recommendation on its own terms — LORA's reliability edge is partly an artefact of failures nobody can see. |
| DF2W ships on Bravo and its end-to-end delivery cost is measured | The first real test of "building a new product on Bravo is easy". Currently: 22 unstarted epics, zero applications. |

---

## 7. What to do next

Ordered by value, not by platform. Items 1–4 are hours or days of work and two of them could change the conclusion above.

1. **Map `Surveyor Platform - Release reject` to a code path (days).** 28.4% of Bravo's ticket load, growing 4.8×, unexplained. It decides whether Bravo's intervention rate is 3.5× LORA's or level with it.
2. **Define `Bravo total app` and `Lora total app` with the billing owner (days).** Every per-application number in this pack — cost, intervention rate, zero-intervention completion — is provisional until this exists.
3. **Read the `feature-configuration` 404 (hours to look, days to fix).** 266,767 a week on the busiest handler in `ms-bpm`, reaching 69% of surveyor sessions, invisible to every monitor. Live defect or benign probe — either way it should not be unknown.
4. **Delete every `|| true` from `OPERATION_PLATFORM.yml`, and open the Actions tab (one hour, plus five minutes).** Bravo's only scheduled journey run cannot report a failure. Fixing that is a two-character deletion per line. Finding out whether it has fired since 2023 is a five-minute look that this pack could not do from a checkout — and the answer decides whether Bravo has had *no* journey signal or a *false* one.
5. **Cut Bravo's Cloud Logging bill (weeks, Rp50–90M/month).** Larger than the saving from retiring the Bravo LOS tier entirely, available now, configuration only, and it also removes upstream request bodies containing customer data from Cloud Logging.
6. **Give both platforms a 4xx-aware health gate and a front-end error budget (weeks).** Both currently define health as the absence of the one failure mode they do not have.
7. **Build LORA's schema-first scaffolding generator (weeks).** Turns `BL-9528..9532` — five repositories, six tickets — into one ticket and a generated PR set. It removes the strongest argument for Bravo, on the merits.
8. **Write LORA's retry policy and dead-letter path (weeks).** Port the four items in §5 — the design, not the assurance: write the negative tests Bravo never had. This is the largest single reliability item on LORA's list and Bravo already shows what the answer looks like.
9. **Name Bravo's staffing decision (a meeting).** Seven active engineers on the service carrying ~94% of origination, with the Story layer on one account. Whatever is decided about new products, that number needs an owner.
10. **Instrument Bravo's job executor and add two end-to-end process tests (weeks).** Even under this recommendation, Bravo runs 76,446 applications a month for years to come. It should be observable and testable while it does.

---

## Related

- **[compare-architecture.md](compare-architecture.md)** — the paradigm comparison (BPMN vs GSM+Temporal), the Bravo team's review, and the code-level evidence index
- [bravo-people.md](bravo-people.md) · [bravo-testing.md](bravo-testing.md) · [bravo-observability.md](bravo-observability.md) · [bravo-cost.md](bravo-cost.md) · [bravo-delivery.md](bravo-delivery.md) — the five findings this synthesises
- [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md) — the symmetric reliability measurement
- [workflow-gap.md](workflow-gap.md) — the production volume split between Bravo's two generations
- [option-summary.md](option-summary.md), [option-1.md](option-1.md), [option-2.md](option-2.md), [option-3.md](option-3.md) — the migration options this recommendation feeds
- [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) — an unrelated critical finding that is independent of this decision and should not wait for it
- LORA production findings: [people](../../lora-workspace/docs/production-findings/people.md) · [testing](../../lora-workspace/docs/production-findings/testing.md) · [observability](../../lora-workspace/docs/production-findings/observability.md) · [cost](../../lora-workspace/docs/production-findings/cost.md) · [delivery](../../lora-workspace/docs/production-findings/delivery.md) · [reliability](../../lora-workspace/docs/production-findings/reliability.md)
