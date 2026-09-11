# Bravo vs LORA: production findings, side by side, and where the next product should go

**Audience:** CTO office, platform leadership, product leadership
**Question:** Synthesising people, testing, observability, cost and delivery — which platform should BFI prioritise for hosting future business products?

**What this document is.** The five Bravo production-findings documents ([people](bravo-people.md), [testing](bravo-testing.md), [observability](bravo-observability.md), [cost](bravo-cost.md), [delivery](bravo-delivery.md)) each answer one question about Bravo and set it against LORA's equivalent. This document puts all five in one matrix and turns them into a recommendation.

**What this document is not.** It is not the architecture comparison. That is [compare-architecture.md](compare-architecture.md) — the paradigm-level reading of BPMN against GSM+Temporal, including the Bravo team's review of it. That document's verdict stands and is not re-litigated here. This one is about how the two platforms *behave in production and under delivery pressure*, which is a different question and, for a hosting decision, the more decisive one.

**Method.** Everything below is measured, and every row names where. New measurements taken 2026-09-10: Jira (`DF`, `D2W`, `BL`, `BLCS`, **`LN`**), the three Bravo console repositories, Datadog `us5` (APM spans, logs, monitors, Synthetics, CI Visibility, RUM on four Bravo consoles), and GCP billing via the FinOps API for complete-month August 2026. Carried forward: the OTRS ticket export ([ticket-analysis.md](production-findings/ticket-analysis.md)), the 90-day PostgreSQL and Datadog volume split ([workflow-gap.md §8](workflow-gap.md)), and the LORA production-findings pack.

> **Revised 2026-09-11 — and the recommendation in §5 has changed.** Four corrections landed after the previous version, three of which removed a pillar this document's recommendation stood on.
>
> 1. **Team size is not evidence.** Bravo's 7 active engineers against LORA's 22 is the *output of a prior CTO decision to consolidate on LORA*, reversible by the same office. Citing it as a reason to prefer LORA was circular. Removed from the edge column and from the decision drivers ([people §5](bravo-people.md)).
> 2. **"Seven product families" was false as used.** Verified against LORA's own production findings: the prod GKE namespace runs **only** `dp-ndf` workers. The live set is **NDF2W + NDF4W — one family**. Six families are un-deployed, three with no `deploy-prod.yaml` at all. The previous sentence *"already carries 69% of applications across seven product families"* was wrong: that share all runs on the one family.
> 3. **Applications are the wrong unit, and no better unit exists anywhere.** Per CTO office: Bravo ≈**Rp 50.2bn** against LORA DP NDF ≈**Rp 2.4bn**. LORA has 1.45× the applications and roughly **1/21 the business value**. There is **zero** agreement, disbursement, NTF or revenue data in either workspace.
> 4. **The engine end-of-support finding was never surfaced here.** Bravo runs **Camunda 7.23.0 Community Edition** — dead since 14 Oct 2025, no patches ever again — on Spring Boot 3.5.16, out of support since 30 Jun 2026. This was not missing analysis: [option-summary.md](option-summary.md) and [option-1.md](option-1.md) cover it in full. It simply never reached this document. It is now §0.
>
> 5. **Added 2026-09-10 — Bravo's scope in this pack was too narrow, and one row reverses.** Team Bravo objected that the analysis omits the **`LN` project** (Surveyor & Verificator, [board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703)) and the repositories **`bravo-operation-console`, `bravo-surveyor-console`, `bravo-underwriting-console`**. Verified and correct: those three repositories hold **763,861 lines of source and 829 test files**, gate every PR on unit tests, and released three days before this reading; `LN` has issued ~6,600 keys and is **larger than `BLCS`**. Consequences: the delivery-ticket row inverts (Bravo 1.27× LORA, from LORA 1.83×) and is *still* excluded for the same reason as before; the test-file row moves further Bravo's way (**2,286 across four repos**, not 1,457 in one); and Bravo's active-engineer count is **25, not 7**. Nothing in §0 or the value-per-application finding is affected.
>
> 6. **Added 2026-09-10 — DF2W is not in production; it is in UAT.** Team Bravo's second correction. This pack described DF2W as *"fully configured in production with zero applications"*, which reads as *released and unused*. Verified: DF2W is **pre-release** — `INS-6245` seeded branch mapping **for UAT** (2026-09-07), `LN-6479` *"[DF2W] E2E Testing"* is resolved, `TDF-4273` *"DF2W — Golive worker TAC"* closed 2026-09-09, an **LOS penetration test is live** (`ADI-1312` firewall access Done 2026-09-09; `BLCS-4799` sample data Done 2026-09-07), and the go-live epics `D2W-5` and `LN-4573`/`LN-4554` are still open. The *"zero applications"* half was right; *"in production"* was not. [bravo-unified-development-process.md](bravo-unified-development-process.md) had it right all along. This weakens **convergence 8** in [§3](#3-where-they-converge--and-what-that-means-for-the-decision) — see the note there.
>
> **Also resolved 2026-09-10 — the `BLCS`+`LN` double-counting question.** Four tests (project identity, sub-task taxonomy, capability prefixes, cross-project links) show the two projects are split by **squad and domain, not by tier**, and no pair of 80 sampled summaries describes the same change. So the delivery-ticket sum is the supported figure — **Bravo 6,518 against LORA's 5,144** — not the 3,705 floor. The row stays excluded from the edge column for the original reason: ticket volume measures decomposition, and it inverted on a scope fix.
>
> **Net effect: §5 no longer recommends a platform for new products.** It funds the urgent decision and states the three measurements that gate the strategic one.
>
> **A pattern worth naming, since it has now happened three times.** All three scope corrections ran the same way: **Bravo was bounded at `bravo-bpm-service` and LORA at its entire workspace.** That asymmetry produced the missing `bravo-e2e-test` suite, the missing consoles and `LN`, and — inverted — the credit given to LORA for six product families that exist only as code. Every correction that followed moved toward Bravo. **The remaining findings that survive all three corrections are the ones to trust**: the engine end-of-support exposure (§0), orchestration-tier blindness, the cost ratio, and the intervention-rate gap with its one unmapped category.

> **Three further corrections from the team, 2026-09-11 — landed after the revision above.**
>
> 5. **Bravo's August application count was 118,253, not 76,446.** The old figure came from a partial-month extract: 76,446/118,253 = 0.646, close to the 0.601 cost-completeness factor on the same billing row. Consequences, all recomputed here: **August volume was flat, not −35%** (117,996 → 118,253), so the "unit cost inflates as it drains" reading of August is withdrawn; LORA's share of originations is **59%, not 69%**; Bravo's LOS tier is **≈Rp490–515 per application** (so LORA costs **5–6.5×** more per application, not 4–5×); value per Bravo application is **≈Rp425,000** and the value ratio **≈30×**, not 47×; the Jun–Aug intervention rate is **0.389%** (**3.1×** LORA's, 1 in 257), and **0.134%** excluding `Release reject`. **One thing got stronger:** the corrected count now agrees with Bravo's own engine meter (≈113k) to within 5%, where the two previously differed by 48%.
>
> 6. **`Surveyor Platform - Release reject` is fixed, deployed 2026-09-10.** This is the category carrying 1,542 tickets, 28.4% of Bravo's load and 61% of its intervention rate. Every rate in this document still measures the period *before* the fix. If the category goes to zero, Bravo's rate lands at ≈0.134% — level with LORA's 0.126%. **That is arithmetic on a deployed fix, not a measurement**; a September–October ticket re-export is what would confirm it.
>
> 7. **LORA's engineering spread is structural.** Per the VMP LORA plan, LORA runs as **three sub-teams (LORA 1, 2 and 3)** working different features in parallel, with most tasks executed end to end so members share a baseline understanding of the system. That answers a question this pack left open, and it means the bus-factor finding is **Bravo-specific** rather than platform-neutral.
>
> **And one caveat the first correction creates.** The same billing row that produced a wrong Bravo count also produced LORA's **171,479**, which has *not* been re-verified. If it is partial on the same factor, August originations rose ~61% month over month — the implausibility the LORA cost document originally used to argue the counts were complete. **Getting both application columns from a system, with a stated period and basis, is now the first measurement to fund.**

**Two caveats that qualify every row.** Application counts on both sides come from a billing sheet whose platform totals nothing else corroborates, so every *per-application* figure is a verified numerator over a disputed denominator. And Bravo is being drained into LORA, so it keeps the residual hard cases — a real confound, not controlled for.

---

## 0. Before this decision: Bravo's runtime is out of support

**This document used to open with the matrix. That was wrong**, because there is a more urgent decision sitting in front of it, it already has a firm answer, and it is not contingent on anything below.

| Component | Bravo runs | Support ended |
|---|---|---|
| **Camunda 7 Community Edition** | 7.23.0 | **14 Oct 2025** — line closed, final artifact 7.24.0, repo archived, **no security patches ever again** |
| **Spring Boot 3.5.x (OSS)** | 3.5.16 | **30 Jun 2026** |
| Java 17 (Oracle premier) | 17 | 30 Sep 2026 |
| Camunda 7.23 (Enterprise maintenance) | — **no licence held** — | 13 Oct 2026 |

Verified in the checkout: `pom.xml:26` pins `camunda.spring-boot.version` to 7.23.0; there is no Camunda BOM, no enterprise artifact, no licence file or property, and no Camunda EE repository — only BFI's own Artifact Registry. The `-webapp` and `-rest` starters are both embedded, and `SecurityConfig.java:65` sets `/camunda/**` to `permitAll()`. [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) records **61 injected remote-code-execution process definitions** in that engine, **one confirmed executed**, all still active.

> **An engine with no patch channel and a publicly reachable deployment endpoint is the worst combination on this list, and it is live today.**

**There is a supported destination and it is cheap.** [option-1.md §4](option-1.md) compares the two Apache-2.0 community forks — **Operaton 2.1.4** and **CIB seven 2.2.0**. Both run on Spring Boot 4, keep the `ACT_` schema unchanged, accept the legacy `camunda:` namespace and ship automated migration recipes. Swapping the engine *and* upgrading Spring Boot in one change is **18–33 engineer-days, Rp45–125M, no licence** — against 31–57 engineer-months for a Temporal port or a LORA migration.

**Two decisions, two clocks** ([option-summary.md §2](option-summary.md)):

| | **Decision A — weeks** | **Decision B — months** |
|---|---|---|
| Question | How do we make Bravo safe to run? | What is Bravo's platform for 5–10 years? |
| Answer | **Option 1 Path B — fund it now** | **Open.** §5 states what gates it |
| Contingent on the other? | **No** | No |

**Decision A is unconditional.** Every strategic path leaves Bravo running the retail book for at least 12 months — a Temporal port takes 12–18, a LORA migration 15–24 — and the Spring Boot 4 half of the work is owed under those paths anyway. **Nothing in the rest of this document should delay it.**

---

## 1. The matrix


| Dimension | **Bravo LOS** | **LORA** | Edge | Source |
|---|---|---|---|---|
| **PEOPLE** | | | | |
| Active engineers on the platform (sampled) | 7 distinct assignees across 100 sampled tickets; Story layer held by **one** account | 22 distinct assignees across 100 sampled tickets | **excluded** — a prior CTO decision, not a platform property | [people §5](bravo-people.md) |
| Delivery tickets, Jan–Aug 2026 | ≈**6,518** (`BLCS` 2,813 + `LN` 3,705) | ≈5,144 (`BL`) | **excluded** — confounded by decomposition *and* headcount, and it **inverted** (was LORA 1.83×, is Bravo 1.27×) when a missing Bravo project was added | [people §3, §5](bravo-people.md) |
| Median ticket cycle time, Aug 2026 | **2 days** | **2 days** | tie | [people §4](bravo-people.md) |
| Repositories touched per integration change | **1**, or 2 where a console is involved | **5**, in a mandated order | **Bravo** | [people §6](bravo-people.md) |
| Hiring pool | Java/Spring/Camunda — commodity | Go + bespoke GSM planner + Temporal | **Bravo** | [people §7](bravo-people.md) |
| Week-1 curriculum | none | none | tie (both bad) | [people §7](bravo-people.md) |
| **TESTING** | | | | |
| Test files | **2,286 across 4 repos** — 1,457 in `ms-bpm`, 829 in the three consoles; every non-frozen repo runs them on each PR | 608 across 13 repos; 4 repos at zero, SDK has no CI workflow | Bravo | [testing §1](bravo-testing.md) |
| Unit tests **blocking a merge** | **yes** — `ms-bpm` and all three consoles; no `\|\| true` in 28 console workflows | yes, where a workflow exists | tie | [testing §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change) |
| Coverage **enforced** (not merely measured) | **no** — JaCoCo `report` without `check`; console thresholds at 0% and 1%; `jest-coverage-thresholds-bumper` installed and never invoked | no | **tie — the same defect on both** | [testing §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change) |
| Tests that execute the orchestration | **4** of 1,457 (0.27%) | planner scheduling untested; 16 planner tests, all rollback | tie (both absent) | [testing §1](bravo-testing.md) |
| Can CI say "this change hits NDF2W"? | **No** — product identity in 5 places, and `ndf2w.bpmn` bridges into unified underwriting (73% of volume) | **No** — but product families are isolated by schema, worker and queue | LORA | [testing §3](bravo-testing.md) |
| Where the model is validated | **production, at pod boot** — 38,198 parse warnings/week, non-fatal | worker startup — fatal panic on a missing path | LORA | [testing §4](bravo-testing.md) |
| Coverage gate | none (JaCoCo `report`, no `check`) | none; floor proposed | tie | [testing §1](bravo-testing.md) |
| Automated journey test | **exists and was abandoned.** 595 Cypress/Cucumber features in `bravo-e2e-test`, 349 on the Surveyor Platform; 4 CI workflows, 1 scheduled weekly — **every step ends `\|\| true`, so it cannot fail**; frozen 2023-11-21. Plus 8 org Synthetics, all DNS/SSL, and zero CI events | nightly partner-E2E exists, asserts a terminal condition, **mostly red** | **LORA** | [testing §6](bravo-testing.md) |
| Assertion quality of the journey suite | **Split by tier.** Its **130 API** feature files assert on **87%** of their `Then` steps — competent Gherkin. Its **465 UI** files assert on **27%**, and **57% of their `Then` steps are pure clicking and typing**. 78% of files named by test polarity; 1,007 of 1,068 `Scenario Outline`s vary nothing | asserts a terminal condition per journey | **LORA**, narrowly — Bravo's API tier is the better-written Gherkin in the estate | [testing §6](bravo-testing.md) |
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
| Per application | **≈Rp 490–515** | ≈Rp 2,500–3,200 | **Bravo (5–6.5×)** | [cost §3](bravo-cost.md) |
| Whole GCP footprint | Rp 1,887M (50.9% of BFI's entire GCP bill — mostly the shared data plane **LORA also calls**) | ≈Rp 431M | not comparable | [cost §2](bravo-cost.md) |
| Marginal cost per extra application | pods + database — small but non-zero | **≈zero**: +23% volume for +3% spend | **LORA** | [cost §4](bravo-cost.md) |
| Direction of unit cost | **flat in August** — fixed cost, volume flat (117,996 → 118,253) | improving | **LORA** | [cost §4](bravo-cost.md) |
| Largest addressable line | **Cloud Logging Rp 140.5M/month** — 2.4× the orchestration tier, and it is configuration | Temporal Actions programme, Rp 7.2M | — | [cost §5–6](bravo-cost.md) |
| **DELIVERY** | | | | |
| Feature flags | **five mechanisms**, no registry; gateway flags need a restart; per-application jsonb activity matrix is genuinely good | `$.experiments.*` per-loan stamps + schema-versioned workers | tie | [delivery §1](bravo-delivery.md) |
| In-flight deploy safety | **no `calledElementBinding`** — a unified sub-process redeploy reaches in-flight NDF2W loans at their next call | schema-versioned queues; old loans stay on old workers | **LORA** | [delivery §1](bravo-delivery.md) |
| Custom UI on a page | easy — plain React on domain REST verbs | three layers (templ → customElement → HTMX); JsForm is the fix | **Bravo** | [delivery §2](bravo-delivery.md) |
| Front-end surface | **≥15 browser applications**; the 3 LOS consoles alone are **763,861 LOC / 829 tests** | 2 | **LORA** | [delivery §2](bravo-delivery.md) |
| Shared UI component library kept in sync | **no** — one design system, **three different versions** across the three LOS consoles (`3.0.138` / `3.0.155` / `^3.0.158`), plus **React 17 vs 18**, Vite 4 vs 7, ESLint vs Biome, Node 18 vs 20 | one back office, one toolchain | **LORA** | [delivery §2](bravo-delivery.md#2-custom-front-end-easy-per-page-hard-per-system) |
| Pagination | **solved** — `SurveyorAssignmentFormTabV2Controller` + 9 sub-resource endpoints, the busiest read path in the service | not needed — one task, one form | both correct for their object | [delivery §3](bravo-delivery.md) |
| Master data → dropdowns | **yes, live** — role rename was 1 YAML line + 1 SQL `UPDATE` + zero Java | startup cache, values copied onto the loan; no ad-hoc SQL | **Bravo** on speed, **LORA** on consistency | [delivery §4](bravo-delivery.md) |
| Front-end errors, 7 days | **2,413,198** across 4 consoles (1.88/view); **748,686 are 404s**, one endpoint on **69% of sessions** | 416,201 (2.8/view) on the back office | **LORA** (5.8× less) | [delivery §5](bravo-delivery.md) |
| **RELIABILITY** (carried from [ticket-analysis.md](production-findings/ticket-analysis.md)) | | | | |
| Manual-intervention rate, Jun–Aug | **≈0.389%** — 1 in 257 | **≈0.126%** — 1 in 790 | **LORA (3.1×)** — but see §4 | |
| Ticket trend, Jan→Aug (stable categories) | **×1.82 on flat volume** | ×0.66 while volume rose | **LORA** | |
| Failure shape | bounded, classified, parked in an operator console — **no zombie class** | uncapped retry; ~half of loans never terminate | **Bravo** on shape | |
| **VOLUME & BUSINESS VALUE** | | | | |
| Applications, Aug 2026 | 118,253 (41%) | 171,479 (59%) | LORA on count | billing sheet |
| **Business value** | **≈Rp 50.2bn** | **≈Rp 2.4bn** (DP NDF) | **Bravo (≈21×)** | per CTO office, 2026-09-11 — *period and basis to confirm* |
| **Value per application** | **≈Rp 425,000** | **≈Rp 14,000** | **Bravo (≈30×)** | derived from the two rows above |
| Agreement / disbursement / NTF data | **none** | **none** | — | **the largest measurement gap in the pack** |
| Product families **live in production** | 4 — NDF2W, NDF4W, NDF4W-RO, DF4W. Plus `NDF4W_Sharia` and `UNSECURED` configured at zero volume | **1** — NDF (NDF2W 90.2%, NDF4W 9.8%), via the partnership door | **Bravo** | [workflow-gap §8](workflow-gap.md) · LORA cost.md, testing.md |
| Product families **built, not yet live** | **DF2W — in UAT, LOS pen test running, go-live epics open** (config seeded, zero starts). Plus `NDF4W_Sharia`, `UNSECURED` and `DF2W_Sharia` configured at zero | **6 of 7** — SSF ×2, HETO ×3, revolving loan; awaiting a CTO decision. Three have **no `deploy-prod.yaml`**; three more name a schema version that does not exist | **Bravo** — one family in flight to a release against six awaiting a decision, three of which cannot deploy at all | LORA people.md, pipelines.md · Jira `INS-6245`, `LN-6479`, `TDF-4273`, `D2W-5` |
| Products on the *modern* generation | DF4W only — 5.5% of Bravo's own volume | all of it, but that is one family | — | [workflow-gap §8](workflow-gap.md) |
| **PLATFORM LIFECYCLE** | | | | |
| Workflow engine support | **Camunda 7.23.0 CE — dead 14 Oct 2025, no patches ever again**, no licence held | Temporal Cloud, contracted; renegotiable ~Mar 2027 | **LORA** | [§0](#0-before-this-decision-bravos-runtime-is-out-of-support) |
| Application framework support | **Spring Boot 3.5.16 — out of support 30 Jun 2026** | Go, current | **LORA** | [option-summary §1](option-summary.md) |
| Cost to reach a supported runtime | **18–33 engineer-days, Rp45–125M, no licence** (Operaton 2.1.4 or CIB seven 2.2.0) | n/a — already supported | — | [option-1 §4](option-1.md) |
| Engine coupling, if it ever had to move | shallow on public API — 483 `delegateExpression`, 272 delegates, but only **4 internal `engine.impl` imports across 3 files**, **zero** `HistoryService` use, and `ACT_` tables touched by 2 Flyway DDL migrations only | n/a | — | verified in checkout |

---

## 2. What each platform is genuinely better at

**Bravo is better at:**

- **Running cheaply.** ≈Rp58M against ≈Rp431M, ≈Rp490–515 per application against ≈Rp2,500–3,200. One deployment, one database.
- **The cost of one change.** One repository, one deploy, no cross-service ordering rule. The five-repo LORA tax is real and measurable.
- **Fleet questions about business state.** Relational state means "all loans stuck at survey" is a `WHERE` clause. LORA cannot express this at all.
- **Upstream attribution.** 113 typed Feign clients give per-upstream, per-status attribution for free. LORA's 300-proxies-one-route design cannot.
- **Durable business history.** Every reprocess generation is a queryable row. Nothing has to be replayed.
- **Bounded, classified failure.** Fail-fast checkpoints, business errors as BPMN errors, degrade on last attempt, an operator console. No zombie loans by construction.
- **Configuration-driven change on reference data.** A staged approval-role rename was one YAML line and one SQL `UPDATE`.
- **A cheaper test boundary.** 113 typed Feign interfaces mean stub drift is caught by `javac`. LORA needs a `check:stubs` script against a live schema registry to get the same guarantee ([testing §7.1](bravo-testing.md)).
- **Carrying the business.** ≈Rp 50.2bn against ≈Rp 2.4bn, and **four product families live in production against LORA's one.** Whatever is decided about new products, Bravo is where the book and the money are.
- **Commodity skills at hiring** — and this now matters more, because it is the one staffing-adjacent fact a CTO cannot reverse by reallocating people. Java/Spring/Camunda is a commodity hire; Go plus a bespoke GSM planner is not.

**LORA is better at:**

- **A supported runtime.** Go and Temporal Cloud against Camunda 7 CE, dead since October 2025, and Spring Boot 3.5.16, dead since June 2026 ([§0](#0-before-this-decision-bravos-runtime-is-out-of-support)). Fixable on Bravo in 18–33 engineer-days, but not fixed today.
- **Adding automated steps.** 172 activities against 3 hard precursors, no orchestration edit. The clearest validated architectural win.
- **Seeing what the orchestrator is doing.** One span per activity attempt, carrying the loan id. Bravo emits **zero** spans for its entire orchestration layer.
- **Joining a failure to a customer.** `@WorkflowID` is the application UUID. Bravo cannot do this from telemetry at all.
- **Not needing a person.** ≈0.126% intervention rate against ≈0.389%, and falling while Bravo's rises.
- **Marginal cost.** Near zero per additional application. Bravo's is small but real, and its unit cost is inflating as it drains.
- **Product isolation.** Separate schemas, workers and queues. Bravo has one job executor for every product and product identity in five places. **Proven on one family only** — the isolation is structural in the design, but six of seven families have never been deployed, so it has not been exercised across families in production.
- **In-flight deploy safety.** Schema-versioned queues against Bravo's unpinned child processes.
- **A journey test that runs and asserts.** LORA's nightly is mostly red and that is bad. **Bravo's is worse in a more specific way:** 595 feature files exist, one workflow is scheduled, and every step in it ends `|| true` — so it reports success whether the loan journey worked or not, on 10 of 595 files, and has been frozen since 2023-11-21. A red test can be fixed. **A permanently green one actively misleads** — and if it ran, 57% of the `Then` steps in the 465 UI feature files it covers are pure clicking and typing. One qualifier in Bravo's favour, added 2026-09-10: the corpus's **130 API feature files assert on 87% of their `Then` steps**, so the skill is present and the defect is confined to the UI tier ([testing §6](bravo-testing.md)).
- **A verified failure policy.** LORA's retry behaviour is bad *and measured*. Bravo's is well-designed and **unverified** — nothing in Bravo can make an upstream fail, so the degrade paths this document recommends porting have never been executed by a test.

---

## 3. Where they converge — and what that means for the decision

Eight things are the same on both platforms, and they matter because **anything that is the same on both cannot be a reason to choose either.**

1. **Human-task complexity is paradigm-independent.** Bravo spends 44% of its code on human work; LORA has ~12k lines of hand-written FSMs inside a declarative shell. Neither engine's native task model was used.
2. **The orchestration layer is untested in both.** 4 of 1,457 Bravo tests execute a process; LORA's planner scheduling is untested and its nightly is red.
3. **Both built a journey suite and left it unable to run.** Bravo: 595 Cypress features, 46 authors, four workflows, frozen 2023-11-21, and the one scheduled workflow written so it cannot fail. LORA: `lora-super-test`, 150 scenario tests, **a CI workflow file that has nowhere to run yet**. Two teams, two platforms, the same outcome — a large deliberate investment in journey testing that no longer gates anything. This is the closest structural parallel in the pack and neither team knew the other had it.
4. **The lifecycle FSM is declared and not enforced in both.** Bravo has a state-machine class used once; LORA validates enum membership only.
5. **Neither has saga compensation.** Both rely on sweepers, re-sync and humans for failed external commits.
6. **Both mistake the absence of one failure mode for health.** "Not 5xx" and "still Running" are the same error. Both teams also filtered their most informative error class out of their one business monitor — Bravo excluded `ENGINE-16004`, LORA excluded the go-live agreement message.
7. **Both platforms have product families built and not yet live — and this pack applied the criticism to only one of them. *Amended 2026-09-10: this is no longer a symmetric convergence.*** The double standard was real and its correction stands: earlier versions counted LORA's six un-deployed families as "7 product families" in its favour while counting Bravo's DF2W against it. But the two situations are **not the same state**, and saying so was itself an error in the opposite direction.

    **Bravo's DF2W is in flight to a release.** Verified 2026-09-10: UAT branch mapping seeded (`INS-6245`, 2026-09-07), `[DF2W] E2E Testing` resolved (`LN-6479`), go-live worker TAC closed (`TDF-4273`, 2026-09-09), an **LOS penetration test running** (`ADI-1312`, `BLCS-4799`), and pre-go-live epics open and being worked (`D2W-5`, `LN-4573`, `LN-4554`). It is a product in pre-release testing, which is the normal state of an unlaunched product.

    **LORA's six are awaiting a decision.** Per the CTO office they are *pending a decision to turn on or not*; three have **no `deploy-prod.yaml` at all** and three name a schema version that does not exist. None is in UAT.

    **So the honest reading:** both platforms have built families that have never taken an application, and neither team should be criticised for that alone — but **one has a dated release path and five to six do not.** On this row the edge is Bravo's. What survives as a genuine convergence is the narrower point: *neither platform's un-launched families tell you anything about how easy that platform is to build on, and both packs had been using them as if they did.*
8. **Surveyor assignment is the top ops complaint on both, in the same words, at nearly the same rate** — 1,182 Bravo tickets (21.8%) and 1,021 LORA tickets (25.0%). A BPMN flowchart and a GSM planner each modelled assignment around a hand-written service layer and inherited its failure modes.

**Both teams also had rich instrumentation they were not reading.** LORA's two RUM applications had been on all along and were never consulted. All four Bravo LOS consoles are instrumented at `ALL` and produce 2.4M errors a week that nobody had opened. This is not an architecture finding; it is the same operational gap on both sides, and it is the cheapest thing on either backlog.

---

## 4. The three measurements that actually decide it

Strip out everything that converges, everything that is a wash, and everything that is a prior decision rather than a platform property. **Three measurements carry the decision. Two point at Bravo.**

**1. Bravo's orchestration is 5–6.5× cheaper per application — and the gap closes on its own.** ≈Rp490–515 against ≈Rp2,500–3,200. This is the strongest fact on Bravo's side and it should not be minimised. Two things bound it. The gap is caused by LORA's fixed contracts and over-provisioning — a 3-year CPU commitment, a Temporal commitment renegotiable at ~March 2027, 448 GB of requests at 15.5% utilisation, five idle worker versions — not by the paradigm. And Bravo's advantage erodes automatically: fixed cost over volume that falls as the migration proceeds means ≈Rp1,450 per application at 40k/month without either team doing anything. Meanwhile **Cloud Logging alone (Rp140.5M/month) is 2.4× the entire tier the migration would retire**, and it is a configuration fix.

**2. Bravo needs a person 3.1× more often, and the trend is diverging.** ≈0.389% against ≈0.126%; ×1.82 against ×0.66 over eight months, with Bravo's volume falling and LORA's rising. **The honest qualifier is large**: the gap turns entirely on one category, `Surveyor Platform - Release reject` — 1,542 tickets, 28.4% of Bravo's load, growing 4.8×, and **still unmapped to any code path**. Remove it and Bravo's rate is 0.134% against LORA's 0.126% — level. Two other errors push the other way (Bravo's denominator is probably inflated; its operator console lets staff unstick applications without a ticket), so the 3.1× is more likely a floor than a ceiling. But it is one category away from being a wash, and mapping that category is days of work nobody has done.

**3. Bravo cannot see its own orchestration, and its proof that a loan can still be originated has been switched off.** Zero spans on the engine path. No application id on any log line. Zero process-level monitors among 38. Zero CI pipeline telemetry. **And the journey suite is the sharpest version of this:** Bravo built 595 Cypress features with 46 authors, aimed 349 of them at the Surveyor Platform, wired four CI workflows — then froze the repo in November 2023 and left the one scheduled workflow written so that every step ends `|| true` and it cannot report a failure. The continuous evidence that Bravo works is the support-ticket queue. **But the remediation is cheap and this cuts against the argument**: the two test layers that would catch the most run in **milliseconds** and are ~7 days of work ([testing §7.2](bravo-testing.md)), and 349 usable journey descriptions already exist. **This is a decision nobody has made, not a mountain nobody can climb** — which makes it a reason to fund remediation, and a weak reason to move products.

**What used to be driver 4 is withdrawn.** It read *"the claim that Bravo is easier rests on the two smallest things Bravo runs"* — DF4W at 5.5% and DF2W at zero. That is still true of the *unified spine*, and [§1](#1-the-matrix) keeps the row. But it cannot carry decision weight while **LORA's entire production estate is one product family** and six of its seven are in the same unlaunched state DF2W is in. Symmetrically applied, the observation cancels.

**And what used to be the capacity half of driver 3 is withdrawn** for the reason in [people §5](bravo-people.md): headcount is the output of a prior CTO decision, not a property of a platform.

## 5. Strategic recommendation

> ### Decision A — fund now: get Bravo onto a supported engine and Spring Boot. 18–33 engineer-days, no licence.
> ### Decision B — where the next product family goes: **open**, and gated on three measurements that have never been taken.

**Why this document no longer picks a platform for new products.** The previous version recommended prioritising LORA. That recommendation rested on five pillars and **three of them have failed**:

| Pillar | Status |
|---|---|
| LORA has 22 engineers against Bravo's 7 | **Withdrawn.** The output of a prior CTO decision, reversible by the same office |
| LORA carries 69% of applications across seven product families | **False.** One family is live; that share all runs on it; six are un-deployed |
| LORA is where the business is | **Inverted.** Bravo ≈Rp 50.2bn against ≈Rp 2.4bn — **≈30× the value per application** |
| Bravo cannot see or test its own orchestration | **Stands** — but remediation is days-to-weeks, not quarters |
| LORA has near-zero marginal cost and structural product isolation | **Stands**, though the isolation is proven on one family |

**What survives is genuinely balanced.** LORA has near-zero marginal cost, product isolation and in-flight deploy safety by construction, one span per activity attempt carrying the loan id, and a journey test that asserts. Bravo has the cheaper tier by 5–6.5×, one or two repositories per change against five, a console tier of 829 tests gating every front-end merge, the business and the money, four live product families against one, fleet SQL queries, per-upstream attribution, durable reprocess generations, bounded classified failure, and the commodity hiring pool. **Neither list wins on the evidence available, and the evidence that would decide it does not exist yet.**

**Three measurements gate Decision B.** All are weeks or less, and none has been taken:

1. **The agreement / NTF / disbursement split by platform.** Every rate in this pack divides by an application count from a billing sheet that nothing corroborates, whose LORA column swings 0.03×–1.27× against the Temporal meter, and which probably double-counts a LORA loan in Bravo at go-live. The CTO office's Rp 50.2bn / Rp 2.4bn figures say applications are the wrong unit by a factor of ~47 — **that needs to come from a system, with a stated period and basis.**
2. **`Surveyor Platform - Release reject` mapped to a code path — now **hours**, not days.** 28.4% of Bravo's ticket load, growing 4.8×. **Narrowed 2026-09-10** to six named candidates by opening the console repositories the pack had never held: four `release-assignment` handlers in `OperationAssignmentController` plus `voidAssignment`/`reprocess`, and `cancel-reject-notes` routes in `bravo-surveyor-console`; owning squad `LN`. Remove the category and Bravo's intervention rate is 0.134% against LORA's 0.126% — level. Days of work.
3. **LORA's per-family production readiness.** Six of seven families are un-deployed and nothing records whether that is a business decision, a readiness gap, or drift. If the intent is that LORA hosts the next family, the question is what it actually costs to launch one there — and three of the six do not have a production deploy workflow.

**One instruction that does not wait for any of them.** Bravo carries the majority of the book and the majority of the money. **Whatever is decided about new products, Bravo must be resourced and treated as a strategically important platform**, not as a system being wound down. Its runtime is out of support today, its orchestration is unobservable, and its journey tests do not run — and it will be originating the majority of BFI's business value throughout whatever migration is or is not chosen.

**Two qualifications that survive unchanged.**

1. **This is not an architecture verdict.** [compare-architecture.md §7](compare-architecture.md) concludes the paradigm decided the shape of ~6% of Bravo's codebase and ~10% of LORA's — the automated pipeline — and decided it in LORA's favour, while the other ~90% looks structurally similar and differs by engineering discipline. Nothing here overturns that, and nothing here rests on it.
2. **Nothing here justifies rushing the remaining migration.** Bravo runs 118,253 applications a month, has bounded failure, and is the cheapest orchestration tier of the three options. The migration should finish because running two platforms costs two teams — not because Bravo is failing.

### Port these four things from Bravo into LORA

The comparison produces a shopping list, and it is not one-directional.

| From Bravo | Why | LORA's gap |
|---|---|---|
| **A retry policy** — bounded attempts, fail-fast checkpoints, business-vs-transient classification, degrade-on-last-attempt, an operator queue | Bravo has no zombie-loan class *because the engine forced it to write one* | `MaximumAttempts: 0`, `NonRetryableErrorTypes: nil`, ~60,000 non-retryable 4xx/week retried as transient |
| **A designed dead-letter path** — `ApplicationErrorTracking` plus an operator console | Failure becomes visible and recoverable by someone other than an engineer | 1,269 force-cancels Jan–Aug; ops re-originates from event 1 |
| **Durable generations** — `prevApplication` / `currentIndex`, every attempt a row | Answers "what happened on day 120" without replay | rewind loses the prior generation |
| **Per-upstream attribution by construction** | "Which BFI service is degrading" is one query | 21k undifferentiated 500s/week; the fix is merged and undeployed |

And keep the degrade decision out of the exception handler: Bravo's `customErrorHandle` bypassing anti-fraud after three failures is a credit-policy decision hidden in error handling. If LORA adds terminal errors, decide explicitly whether terminal means *reject*, *park* or *skip*.

> **Port the design, not the assurance.** Every row above is a *design* Bravo got right, and the evidence for each is behavioural — Bravo has no zombie-loan class in production. But [testing §7.4](bravo-testing.md) establishes that **no Bravo test can make an upstream fail**, because `bravo-mock-service` is static and shared. Bravo's **50 `customErrorHandle` implementations, 70 error definitions and 190 escalation paths have never been executed by a test**. LORA should copy the shape and **write the negative tests Bravo never had** — its mock interceptor can already fail any upstream on demand.

---

## 6. What would settle Decision B

The three gating measurements are in [§5](#5-strategic-recommendation). This table says what each *outcome* would mean, so the decision is decidable rather than arguable.

| Finding | Effect |
|---|---|
| **The agreement/NTF split comes from a system** and confirms Bravo carries ~21× the value | **Decision B tilts to Bravo** for anything revenue-bearing, and LORA's application-share argument disappears entirely. Gating measurement #1 |
| The split shows LORA's applications convert at a comparable rate after all | Restores LORA's volume argument and tilts Decision B back. Same measurement, opposite outcome — which is why it must be taken rather than assumed |
| **`Surveyor Platform - Release reject` maps to a defect that is then fixed** — six candidate endpoints named 2026-09-10, so this is now hours of instrumentation | Bravo's intervention rate falls to ≈0.134%, level with LORA's, and LORA's clearest remaining reliability edge disappears. **Days of work.** Gating measurement #2 |
| **Launching one un-deployed LORA family is costed** — three have no `deploy-prod.yaml` | Prices the actual thing being proposed: hosting a *new* family on LORA. Gating measurement #3 |
| **The billing owner defines the application counts** and Bravo's denominator is confirmed inflated | Bravo's true intervention rate rises and its per-application cost rises. Strengthens the recommendation. |
| Bravo is re-staffed | **No longer a falsifier** — headcount was withdrawn as evidence ([people §5](bravo-people.md)). It is an input the CTO sets, not a finding that moves. |
| Bravo instruments the job executor, adds journey tests and 4xx health gates | Removes the observability half of decision point 3. All three are in [bravo-observability.md](bravo-observability.md) and [bravo-testing.md](bravo-testing.md) recommendations and are weeks, not quarters. **Cheaper than first stated:** layers L0 and L1 run in seconds and are ~7 days of work between them, and 349 existing feature files cover the journeys. |
| **`bravo-e2e-test`'s weekly cron turns out to still be firing** | Then Bravo has had a green-by-construction journey signal running for three years on 10 of 595 files. Strengthens decision point 3 rather than weakening it — a misleading signal is worse than none. Checking is **five minutes in the Actions tab.** |
| Bravo's negative suite (N0–N12) is built and the degrade paths pass | Confirms the four items in §5 are safe to port, and closes the largest verification gap on Bravo's side. Needs the per-run stub layer first ([testing §7.4](bravo-testing.md)). |
| LORA's never-terminating half and uncapped retry go unfixed for another two quarters | Weakens the recommendation on its own terms — LORA's reliability edge is partly an artefact of failures nobody can see. |
| DF2W ships on Bravo and its end-to-end delivery cost is measured | The first real test of "building a new product on Bravo is easy". Currently in **UAT with an LOS pen test running**, zero applications, go-live epics open — so the clock is running and the answer is close. **Now paired with the LORA equivalent** — the cost of launching one un-deployed LORA family, which is gating measurement #3 |
| **Decision A is funded and lands** | Removes the runtime-support and RCE exposure from Decision B entirely, so B can be taken on architecture and economics alone. 18–33 engineer-days. **This is the one thing on this page that should not wait for evidence.** |

---

## 7. What to do next

**Decision A first — items 1–2 are unconditional under every strategic path.** Then the three measurements that gate Decision B. Then work that is worth doing whichever way B goes.

1. **Fix the Camunda RCE (this week) — and note the vector was corrected 2026-09-10.** The deploy path is `/engine-rest/**`, which already requires a credential; the injected definitions therefore came from **a held Keycloak token or the shared `INTERNAL_SERVICE_KEY`**, not from an open door. So: **rotate `INTERNAL_SERVICE_KEY` first** (it grants `ROLE_SYSTEM_SERVICE` and full engine rights, making it RCE-equivalent), rotate the plaintext secrets committed in `bravo-e2e-test/cypress.config.js`, pull access logs for `POST /engine-rest/deployment/create` across 2026-05-23 → 06-30 to identify the caller, register a `ProcessEngineAuthenticationFilter` so the engine's own authorization actually applies, purge the 61 injected definitions, remove `permitAll()` on `/camunda/**` as hardening, and check for lateral movement using the pod's service account and datasource credentials. Live, confirmed code execution in production, on an engine with no patch channel. Required under every option.
2. **Fund Option 1 Path B (18–33 engineer-days, Rp45–125M, no licence).** Swap Camunda 7.23.0 CE for Operaton 2.1.4 or CIB seven 2.2.0 *and* upgrade Spring Boot to 4.0.x in one change. Answer the fork question first — is a contractual support agreement required, and purchasable for a BFI entity? Yes → CIB seven, no → Operaton. Run the `ACT_GE_SCHEMA_LOG` diagnostics in every environment before setting a cutover date; that is hours of work and it is the one finding that can change the plan.
3. **Get the agreement / NTF / disbursement split by platform from a system (days).** Gating measurement #1. The Rp 50.2bn / Rp 2.4bn figures are a CTO-office estimate; the decision needs them with a stated period and basis, alongside the `Bravo total app` / `Lora total app` definitions.
4. **~~Map `Surveyor Platform - Release reject` to a code path~~ — fixed and deployed 2026-09-10. Re-export September–October tickets and confirm the category has gone to zero (hours).** Instrument the four `release-assignment` handlers in `OperationAssignmentController`, `voidAssignment`, `reprocess` and the surveyor console's `cancel-reject-notes` routes, then join to the OTRS dates. **Note the queue is named *Surveyor* Platform while every endpoint is `OPERATION_*` — that mismatch may be why it was never found.** 28.4% of Bravo's ticket load, growing 4.8×. It decides whether Bravo's intervention rate is 3.1× LORA's or level with it. **Fixed and deployed 2026-09-10** per the Bravo team, so the answer should arrive in the next ticket export rather than from code archaeology.
5. **Define `Bravo total app` and `Lora total app` with the billing owner (days).** Every per-application number in this pack — cost, intervention rate, zero-intervention completion — is provisional until this exists.
6. **Read the `feature-configuration` 404 (hours to look, days to fix).** 266,767 a week on the busiest handler in `ms-bpm`, reaching 69% of surveyor sessions, invisible to every monitor. Live defect or benign probe — either way it should not be unknown.
7. **Delete every `|| true` from `OPERATION_PLATFORM.yml`, and open the Actions tab (one hour, plus five minutes).** Bravo's only scheduled journey run cannot report a failure. Fixing that is a two-character deletion per line. Finding out whether it has fired since 2023 is a five-minute look that this pack could not do from a checkout — and the answer decides whether Bravo has had *no* journey signal or a *false* one.
8. **Cut Bravo's Cloud Logging bill (weeks, Rp50–90M/month).** Larger than the saving from retiring the Bravo LOS tier entirely, available now, configuration only, and it also removes upstream request bodies containing customer data from Cloud Logging.
9. **Give both platforms a 4xx-aware health gate and a front-end error budget (weeks).** Both currently define health as the absence of the one failure mode they do not have.
10. **Build LORA's schema-first scaffolding generator (weeks).** Turns `BL-9528..9532` — five repositories, six tickets — into one ticket and a generated PR set. It removes the strongest argument for Bravo, on the merits.
11. **Write LORA's retry policy and dead-letter path (weeks).** Port the four items in §5 — the design, not the assurance: write the negative tests Bravo never had. This is the largest single reliability item on LORA's list and Bravo already shows what the answer looks like.
12. **Set each platform's standing allocation, and name the bus factor (a meeting).** The allocation is an input the other four documents' plans are sized against; the bus factor — the Story layer running through one account — is a live operational risk, and it is **Bravo-specific**: LORA runs three sub-teams with end-to-end task execution, which is a structural answer to the same risk (bravo-people.md §5, updated 2026-09-11). **The allocation is not evidence about where new products should go; the concentration risk now mildly favours LORA.**
13. **Instrument Bravo's job executor and add two end-to-end process tests (weeks).** Bravo runs 118,253 applications a month and the majority of BFI's business value, for years to come. It should be observable and testable while it does.

---

## Related

- **[compare-architecture.md](compare-architecture.md)** — the paradigm comparison (BPMN vs GSM+Temporal), the Bravo team's review, and the code-level evidence index
- [bravo-people.md](bravo-people.md) · [bravo-testing.md](bravo-testing.md) · [bravo-observability.md](bravo-observability.md) · [bravo-cost.md](bravo-cost.md) · [bravo-delivery.md](bravo-delivery.md) — the five findings this synthesises
- [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md) — the symmetric reliability measurement
- [workflow-gap.md](workflow-gap.md) — the production volume split between Bravo's two generations
- **[option-summary.md](option-summary.md)** — **read this alongside §0.** Bravo's end-of-support position and the three responses to it, with the Decision A / Decision B split this document now adopts · [option-1.md](option-1.md) the fork comparison · [option-2.md](option-2.md) Temporal · [option-3.md](option-3.md) LORA migration
- [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) — an unrelated critical finding that is independent of this decision and should not wait for it
- LORA production findings: [people](../../lora-workspace/docs/production-findings/people.md) · [testing](../../lora-workspace/docs/production-findings/testing.md) · [observability](../../lora-workspace/docs/production-findings/observability.md) · [cost](../../lora-workspace/docs/production-findings/cost.md) · [delivery](../../lora-workspace/docs/production-findings/delivery.md) · [reliability](../../lora-workspace/docs/production-findings/reliability.md)
