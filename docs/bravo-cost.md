# Cost: what Bravo LOS actually bills, and where the levers are

**Audience:** Platform, finance, the CTO office sizing the migration
**Questions:** What does Bravo cost on a like-for-like basis with LORA? What drives it? Which levers are real, how much are they worth, and when are they available?

**Method.** GCP billing read live through the FinOps dashboard API ([`bfi-finops-dashboard`](https://github.com/bfi-finance/bfi-finops-dashboard) MCP server) on 2026-09-10 for the **complete month of August 2026**: per-project totals, the `bravo-project-331802` service breakdown, and Cloud SQL line items filtered to the BPM instance. Application counts and the LORA tier figures are carried from [LORA cost.md](../../lora-workspace/docs/production-findings/cost.md) and [compare-architecture.md §3.12, §8.4](compare-architecture.md); the engine-meter application count is from [workflow-gap.md §8](workflow-gap.md). All figures are GCP **net cost in IDR**.

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [What Bravo bills](#1-what-bravo-bills-and-what-that-means) · [August 2026, measured](#2-august-2026-measured) · **[The orchestration tier](#3-the-orchestration-tier-rp58m)** · [Unit cost and its direction](#4-unit-cost-and-the-direction-it-is-moving) · **[Cost drivers ranked](#5-cost-drivers-ranked--and-three-that-are-defects)** |
| **3. What to do** | [What the levers are worth](#6-what-the-levers-are-worth) · [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| Bravo is expensive | **Not as an orchestration tier — it is the cheaper one.** `ms-bpm` pods plus its Cloud SQL instance is **≈Rp58M/month in production** against LORA's **≈Rp431M all-in**: roughly **7× cheaper in absolute terms and 4–5× cheaper per application**. This document does not overturn that; it confirms it with an independent pull. |
| Retiring Bravo saves ≈Rp1.6B/month | **Withdrawn, and this document re-confirms the withdrawal.** The Bravo GCP projects bill **Rp1.874B** in August, but the remainder beyond the LOS tier is the shared BFI data plane — ~26 `ms-*` services that **LORA itself calls**. The LOS lever is **≈Rp58M prod, ≈Rp70–100M with non-prod: 8–14×** the entire Temporal Actions programme, not 227×. |
| Bravo's cost is dominated by the workflow engine | **No. The engine tier is 4.5% of its own production project.** Cloud SQL (Rp450.7M) and Compute Engine (Rp394.4M) are 65% of `bravo-project-331802`, and neither is mostly BPM. |
| Bravo's unit economics are improving as it drains | **Refuted.** Volume fell 35% (117,996 → 76,446 applications) between July and August while ticket load **rose 82%** over eight months. Fixed platform cost over falling volume means the cost per application is inflating, for reasons unrelated to architecture. |
| The cost work worth doing is on the engine | **Refuted, and three larger levers are named here.** Cloud Logging at **Rp140.5M/month** — 2.4× the whole orchestration tier — sits behind a globally enabled `loggerLevel: full` and an error stream that is 47% stack-trace frames. The Maps API stack is **Rp64.0M/month**. Non-production is **Rp573.5M**, 31% of all Bravo spend. |
| Bravo's cost is a reason to keep it | **Partly, and it is the strongest argument on Bravo's side of the ledger.** But the tier that would retire is small (≈Rp58M) and the platform it would retire *to* costs more per application today. The cost case for migration is that LORA's marginal cost is near zero and one platform goes away — not that Bravo is expensive. |

**The through-line:** Bravo's LOS orchestration is genuinely cheap, and almost none of Bravo's bill is orchestration. The money is in a database, a log pipeline and a non-production estate, and two of those three are misconfiguration rather than workload.

---

## 1. What Bravo bills, and what that means

Bravo has no metered orchestration invoice. There is no Actions counter, no per-workflow storage line, nothing analogous to Temporal Cloud. Camunda 7 is an **embedded library** inside a Spring Boot service, so every cost it creates lands somewhere else on the GCP bill:

| Where the engine's cost shows up | Line | Notes |
|---|---|---|
| Process state, history, and all 238 business entities | **Cloud SQL** — `prod-postgres-bpm-d2bpm` | History level `full`, `historyTimeToLive: P90D`. `act_hi_actinst` carries ~50M rows per 90-day window |
| Job-executor threads running all 483 service tasks | **Compute Engine** — `ms-bpm` pods on `prod-bravo-cluster` | Job executor left at the Spring Boot starter default (core pool 3) |
| Every log line the engine and its controllers emit | **Cloud Logging** | 1,116,135 lines/week from `prod-ms-bpm` alone |
| Outbound calls to 25 upstreams | those services' own bills | |

**The comparison this makes possible, and the trap in it.** Because the engine is embedded, "the cost of Bravo's orchestration" is not separable from "the cost of Bravo's human-task application" — they are the same deployment. `ms-bpm` contains the BPMN engine *and* the ~217k LOC of surveyor, operation, underwriting and approval services (44% of the codebase). So the ≈Rp58M tier below is **orchestration plus all human-task handling**, which is the correct like-for-like against LORA's ≈Rp431M (workers + gateway + task service + schema service + Temporal + ArangoDB). Both sides include the human-task layer. That is what makes the ratio meaningful.

---

## 2. August 2026, measured

Per-project, complete month, read 2026-09-10:

| Project | August 2026 |
|---|---:|
| `bravo-project-331802` (Bravo production) | **Rp 1,300,270,632** |
| `bravo-project-nonprod` | **Rp 573,504,402** |
| `bravo-project-shared-services` | Rp 13,568,891 |
| `bravo-project-collection` | Rp 181,361 |
| **Bravo total** | **Rp 1,887,525,286** |
| *BFI GCP estate, all 34 projects* | *Rp 3,708,544,980* |

**Bravo is 50.9% of BFI's entire GCP bill.** That number is arresting and it is the one most likely to be misread, so state it precisely: it is the bill for the platform that hosts most of BFI's origination *and* the ~26 shared `ms-*` data-plane services that both platforms depend on. It is not the price of the workflow engine.

Service breakdown of the production project:

| Service | August 2026 | Share |
|---|---:|---:|
| Cloud SQL | Rp 450,659,997 | 34.7% |
| Compute Engine | Rp 394,392,920 | 30.3% |
| **Cloud Logging** | **Rp 140,536,563** | **10.8%** |
| Cloud Storage | Rp 86,484,875 | 6.7% |
| Networking | Rp 51,860,732 | 4.0% |
| Cloud Memorystore for Redis | Rp 51,023,861 | 3.9% |
| Vertex AI | Rp 50,370,386 | 3.9% |
| **Geocoding API** | **Rp 30,780,541** | **2.4%** |
| Places API | Rp 16,296,928 | 1.3% |
| Maps API | Rp 8,748,514 | 0.7% |
| Places API (New) | Rp 8,153,431 | 0.6% |
| Cloud Vision API | Rp 3,371,788 | 0.3% |
| Gemini API | Rp 2,615,141 | 0.2% |
| Cloud Run | Rp 2,341,507 | 0.2% |
| Kubernetes Engine (control plane) | Rp 1,344,487 | 0.1% |
| 10 smaller lines | Rp 1,288,860 | 0.1% |
| **Total** | **Rp 1,300,270,632** | |

Two groupings worth naming because neither appears as a line:

- **Google Maps platform — Rp 63,979,414/month** (Geocoding + Places + Maps + Places New). Larger than the entire LOS orchestration tier.
- **AI and OCR — Rp 56,357,315/month** (Vertex AI + Vision + Gemini).

---

## 3. The orchestration tier: ≈Rp58M

| Component | August 2026, prod | Source |
|---|---:|---|
| `prod-postgres-bpm-d2bpm` — vCPU + RAM | **Rp 40,930,777** | measured today, 30 daily line items |
| `prod-postgres-bpm-d2bpm` — storage, backup and remaining SKUs | ≈ Rp 11,800,000 | balance to the previously measured instance total |
| **Cloud SQL instance, total** | **≈ Rp 52,700,000** | [compare-architecture.md §8.4](compare-architecture.md), corroborated |
| `ms-bpm` pods, production | ≈ Rp 5,300,000 | [compare-architecture.md §8.4](compare-architecture.md) |
| **Production LOS tier** | **≈ Rp 58,000,000** | |
| `ms-bpm` pods, SIT + UAT | ≈ Rp 12,100,000 | |
| **With non-prod pods** | **≈ Rp 70,100,000** | SIT/UAT/Sharia *databases* not separately pulled; true figure is higher |

**The corroboration matters.** The Rp52.7M instance figure was previously derived once; an independent line-item pull today puts vCPU + RAM alone at **Rp40.93M across 30 days**, which is consistent and rules out an order-of-magnitude error. The BPM instance is **11.7% of the production project's Cloud SQL bill** — it is a significant database, but it is one of many (`prod-postgres-onboarding-d2onb`, `prod-postgres-asset-pricing-d2apc`, `prod-postgres-repeat-order-d2rod`, `prod-postgres-document-d2doc` and the Sharia variants all appear in the same sample).

**The tier is 4.5% of its own production project and 3.1% of Bravo's total GCP spend.** Whatever else is true, the workflow engine is not where Bravo's money goes.

### Against LORA, like for like

| | Bravo LOS tier | LORA tier |
|---|---|---|
| What is in it | `ms-bpm` pods (Camunda + all human-task services) + `prod-postgres-bpm-d2bpm` | LPW/LTW workers, gateway, task service, schema service, Temporal Cloud contract, ArangoDB licence + GKE |
| Monthly, production | **≈ Rp 58M** | **≈ Rp 431M** |
| Applications, Aug 2026 | 76,446 (billing sheet) to ≈113k (engine meter: 338,858 process starts / 90 d) | 171,479 (billing sheet) to ≈135k (Temporal meter) |
| **Per application** | **≈ Rp 510–760** | **≈ Rp 2,500–3,200** |
| Cost shape | ~variable with pods, ~fixed on the database | ~86% fixed: contracts and over-provisioned capacity |

**LORA's orchestration costs ≈7× more in absolute terms and 4–5× more per application.** The reasons are not the paradigm — a fixed Temporal commitment bought in March 2026, a fixed ArangoDB licence, 44 pods requesting 448 GB at 15.5% utilisation, and eight worker versions of which five are idle. Bravo's tier is one deployment and one database.

**The denominators are the weakest part of both columns**, exactly as [ticket-analysis.md §4.3](production-findings/ticket-analysis.md) warns: the billing sheet's platform totals go 109.5k → 237.5k → 247.9k in two months, which nothing else supports, and the likeliest reading is that a LORA-originated application is counted again in Bravo when it books at go-live. If that is right, **Bravo's denominator is inflated and its true per-application cost is higher than Rp510–760** — but not by enough to close a 4–5× gap.

---

## 4. Unit cost, and the direction it is moving

| | Jun 2026 | Jul 2026 | Aug 2026 | Direction |
|---|---:|---:|---:|---|
| Bravo applications | 106,722 | 117,996 | **76,446** | **−35% in one month** |
| Bravo support tickets (stable categories) | 705 | 644 | 751 | **+82% since January** |
| Bravo stuck-application rate | 0.364% | 0.348% | **0.699%** | worsening |
| LOS tier cost | ~flat — one deployment, one database | | | flat |

**Bravo's platform cost is essentially fixed and its volume is falling by design.** Cost per application therefore rises for every application migrated away, with no engineering cause. Meanwhile the *ops* cost per application is rising faster: the stuck-application rate doubled between July and August on a shrinking book.

The pack's standing explanation applies and should be held loosely: a draining platform keeps the residual hard cases — the products, branches and edge cases migrated last. That is a real confound and it is not controlled for. It is also consistent with a fixed-flowchart architecture under continuing product change, which is what [ticket-analysis.md §3](production-findings/ticket-analysis.md) argues.

**What this means for a decision.** Bravo's per-application cost advantage is real today and is eroding on its own. It is not a floor to plan against: at 40k applications a month the same ≈Rp58M is ≈Rp1,450 each, and the gap to LORA halves without either team doing anything.

**LORA's direction is the opposite and this is the load-bearing fact for the migration case:** LORA's cost is ~86% fixed, so it absorbed **+23% Temporal-metered volume for +3% spend** between June and August. Its marginal cost per additional application is near zero. Bravo's is not zero — it is pods and database — but it is small.

---

## 5. Cost drivers ranked — and three that are defects

| # | Driver | Monthly | Nature |
|---|---|---:|---|
| 1 | Cloud SQL, whole production project | Rp 450.7M | workload; the BPM instance is Rp52.7M of it |
| 2 | Compute Engine, whole production project | Rp 394.4M | workload |
| 3 | **Cloud Logging** | **Rp 140.5M** | **substantially defect — see below** |
| 4 | Cloud Storage | Rp 86.5M | workload |
| 5 | **Non-production estate** (`bravo-project-nonprod`) | **Rp 573.5M** | **31% of all Bravo spend — governance** |
| 6 | **Google Maps platform** | **Rp 64.0M** | **workload, but see the geolocation defect** |
| 7 | Redis (Memorystore) | Rp 51.0M | workload; also the NIK-keyed cache flagged for PII |
| 8 | Vertex AI + Vision + Gemini | Rp 56.4M | workload |

### Defect 1 — Cloud Logging at Rp140.5M is 2.4× the orchestration tier

`prod-ms-bpm` alone emits **1,116,135 log lines a week**, of which **525,181 (47%) are ERROR**. Two configuration choices explain most of that, and both are recorded in the code:

- **`loggerLevel: full` is set globally on Feign** ([compare-architecture.md Appendix C](compare-architecture.md)), so every one of the 113 clients logs complete request and response bodies. That is PEFINDO, SLIK, Dukcapil and CONFINS payloads going into Cloud Logging as JSON — a cost line and a data-protection exposure in the same breath.
- **Stack traces are logged one frame per line.** The top error "patterns" in the log stream are literally `at org.springframework.…` (874/week) and `at java.base/…`. One exception becomes dozens of billable lines. And one Camunda job failure produces **two** lines at **two severities** (`ENGINE-14006` at `warn`, `ENGINE-16004` at `error`).

Add **38,198 `ENGINE-09004` BPMN parse warnings a week** ([bravo-testing.md §4](bravo-testing.md)) — pods re-parsing all 53 model files on every boot.

**This is the largest single addressable line in Bravo's bill, it is larger than the thing the migration would retire, and the fix is configuration.** Even a conservative 40% reduction is ≈Rp56M/month — the whole LOS orchestration tier, recovered without migrating anything.

### Defect 2 — Rp64.0M of Maps against 20,690 geolocation failures a week

The Geocoding, Places and Maps APIs are surveyor-platform costs: a field surveyor's device resolving addresses and capturing position. **The console is `bravo-surveyor-console` (`@react-google-maps/api`, 307k LOC, delivered by squad `LN` — repository identified 2026-09-10, [bravo-testing.md §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)), so there is now a named repository and squad to take this defect to.** Meanwhile RUM on the Surveyor Platform records `Error getting location: "[GeolocationPositionError]"` **10,365 times** and `Unable to get current position` **10,325 times** in seven days ([bravo-observability.md §6](bravo-observability.md)).

These two facts have not been connected before and this document does not claim the connection is causal — a browser geolocation failure and a Maps API call are different layers. But **Rp64M/month is being spent on location services on a console where location capture fails ~20,700 times a week**, and nobody has checked whether the failed attempts are also billed attempts. That is a day of work with a real number attached.

### Defect 3 — non-production is 31% of Bravo's spend

`bravo-project-nonprod` bills **Rp573.5M/month**, against Rp1,300.3M in production — a **0.44 non-prod-to-prod ratio**. For comparison, roughly half of LORA's task-service and ArangoDB GKE lines are SIT/UAT, but LORA's non-prod is inside a much smaller total. Nothing in this analysis establishes what is running in `bravo-project-nonprod` or whether it should be. At this size it is the second-largest lever available and it has never been examined.

### The 404 storm has a cost tail

`/bpm/v1/partnership-configuration/feature-configuration` returns 404 **266,767 times a week** and `PartnershipConfigurationController.getByApplicationId` is the **single busiest handler in the service** (73,056 spans in 48 hours). Every one of those is a servlet request, a JPA `repository.operation` against `prod-postgres-bpm-d2bpm`, and at least one log line. It is a small slice of a large database bill — but it is a slice being spent to produce an error, on two-thirds of surveyor sessions.

---

## 6. What the levers are worth

| Lever | Worth / month | Available | Confidence |
|---|---:|---|---|
| **Cut Cloud Logging** — disable global Feign body logging, log exceptions as one event, stop re-parsing warnings | **Rp 50–90M** | now | high — configuration only |
| **Review `bravo-project-nonprod`** | unknown, up to **Rp 573.5M** | now | low — never examined |
| **Audit the Maps spend against failed geolocation** | up to **Rp 64.0M** | now | low — needs a day of work first |
| Shorten Camunda history TTL from 90 d, or drop history level from `full` | part of Rp 52.7M | now, with a data-retention decision | medium — it is the audit trail after `application_status_log` |
| Fix the `feature-configuration` 404 | small, but removes 266,767 wasted DB round trips/week | now | high |
| **Retire the Bravo LOS tier** (the migration) | **Rp 58M prod, Rp 70–100M with non-prod** | when the migration finishes | high |
| *For scale:* the entire LORA Temporal Actions programme | *Rp 7.2M* | now | high |

Two conclusions follow, and they are uncomfortable together.

**The migration is still the single largest structural lever (8–14× the Temporal Actions programme), and it is not the largest lever available this quarter.** Cloud Logging is bigger, available now, and does not depend on anything. A team that fixed logging configuration alone would save more in September than retiring the entire Bravo LOS tier will save when the migration completes.

**And retiring Bravo does not make LORA's tier cheaper.** LORA's ≈Rp431M is 86% fixed, and three of its four cost levers are time-locked: ~31% of node cost sits on a 3-year N2 CPU commitment; the Temporal commitment is renegotiable at **~March 2027**; and the five idle worker versions cannot retire while ~half of LORA's loans never reach a terminal state — a reliability defect presenting as a cost line. The migration's cost case is *one platform instead of two, at near-zero marginal cost per application*, not *the cheaper platform wins*.

---

## Recommended actions

1. **Cut the Cloud Logging bill (S, do this first — Rp50–90M/month).** Turn off Feign `loggerLevel: full` globally and enable it per-client only where needed; this also removes upstream request bodies containing customer data from Cloud Logging. Log exceptions as a single structured event rather than one line per stack frame. Stop `ENGINE-09004` recurring by fixing the models ([bravo-testing.md](bravo-testing.md) recommendation 2). This is the largest, fastest, lowest-risk saving in the document.
2. **Open `bravo-project-nonprod` (S to look, unknown to fix — up to Rp573.5M/month).** 31% of Bravo's spend has never been examined in this pack. Produce a service-level breakdown and a list of what is running and why. Even a 20% reduction outbids the migration lever.
3. **Check whether failed geolocation attempts are billed (S — up to Rp64.0M/month).** Rp64M of Maps APIs on a console with 20,690 geolocation failures a week. Establish whether the two are related before deciding anything. **Owner identified 2026-09-10:** the call sites are in `bravo-surveyor-console` (`@react-google-maps/api`), squad **`LN` — Team Surveyor & Verificator**; the repository has 286 PR-gating tests to add a regression to once the behaviour is fixed.
4. **Decide the Camunda history question explicitly (S–M).** History level `full` with `P90D` on Cloud SQL is a real cost and, after day 91, the only remaining record of what happened to a loan is the trigger-written `application_status_log`. Either shorten the TTL and accept that, or keep it and stop calling it a cost problem — but make it a decision rather than a default.
5. **Fix the `feature-configuration` 404 (S).** 266,767 wasted round trips a week through the busiest handler in the service. Small money, real load, and it is a live defect regardless ([bravo-observability.md](bravo-observability.md) recommendation 1).
6. **Get the billing owner to define the application counts (Days — this is the single largest source of error in the whole pack).** Every per-application figure here and in [ticket-analysis.md](production-findings/ticket-analysis.md) is a verified numerator over a disputed denominator. The `Bravo total app` and `Lora total app` columns need definitions, specifically on whether a LORA-originated application is counted again in Bravo at go-live.
7. **Publish the LOS tier as a standing line (S).** ≈Rp58M is the number that matters for the migration decision, and it currently has to be reassembled by hand from line items each time. A saved FinOps view of `ms-bpm` pods plus `prod-postgres-bpm-d2bpm` makes the migration's value trackable month to month.
8. **Do not quote Rp1.6B as the migration saving (S, documentation).** The Bravo estate is Rp1.887B and most of it is the shared data plane LORA depends on and which does not retire. The figure is **Rp58M prod, Rp70–100M with non-prod**. That claim was already withdrawn once; it should not come back.

---

## Plan: 30, 60, 90 days

Eight recommendations, phased. Most of this is FinOps and Platform time, not Squad S&U engineering — which matters, because the largest saving here is configuration, not migration.

**Sequencing rule for this document: money that is configuration comes before money that is migration.** Cloud Logging at **Rp140.5M/month is 2.4× the entire ≈Rp58M tier the migration would retire**, and it is a config change available now. It starts in week 1. The migration lever is not in this plan at all — it lands when the migration finishes, and nothing here accelerates it.

**Shared with other documents.** Recommendation 5 is also [bravo-observability.md](bravo-observability.md) rec 1 and [bravo-delivery.md](bravo-delivery.md) rec 1; recommendation 3 pairs with [bravo-delivery.md](bravo-delivery.md) rec 2. Phased identically — do them once.

### Days 0–30 — start the largest saving, and fix the denominators

| Item | Rec | Owner | Effort | Worth / done when |
|---|---|---|---|---|
| **Turn off global Feign `loggerLevel: full`**; re-enable per client only where genuinely needed | 1 | S&U + Platform | 3 d | **Largest single saving in the pack.** Upstream request bodies stop entering Cloud Logging — a cost line and a data-protection exposure closed together. Drop visible on the September bill |
| **Get the billing owner to define `Bravo total app` and `Lora total app`** — specifically whether a LORA-originated application is recounted in Bravo at go-live | 6 | FinOps + billing owner | 2 d | **The single largest source of error in the whole pack.** Every per-application figure — cost, intervention rate, zero-intervention completion — stops being provisional |
| **Fix the `feature-configuration` 404** | 5 | S&U | 2 d (fix; investigation is in the observability plan) | 266,767 wasted round trips a week removed from the busiest handler and its database |
| **Publish the LOS tier as a standing FinOps view** — `ms-bpm` pods + `prod-postgres-bpm-d2bpm` | 7 | FinOps | 1 d | ≈Rp58M becomes a tracked chart. The migration's value is trackable month to month instead of reassembled by hand |
| **First look at `bravo-project-nonprod`** — service-level breakdown of Rp573.5M/month | 2 | FinOps + Platform | 2 d | 31% of Bravo's spend stops being unexamined. Sets up the phase-2 plan |
| **Correct the Rp1.6B figure** wherever it survives in slides, decks and briefing notes | 8 | EM | 0.5 d | Nobody plans against a saving withdrawn in September 2026. The figure is Rp58M prod, Rp70–100M with non-prod |

### Days 31–60 — finish the logging cut, answer the open questions

| Item | Rec | Owner | Effort | Worth / done when |
|---|---|---|---|---|
| **Log exceptions as one structured event**, not one line per stack frame; stop `ENGINE-09004` recurring by fixing the models | 1 | S&U | 3 d | Completes the **Rp50–90M/month** saving. ERROR share falls from 47% and the log stream becomes countable |
| **`bravo-project-nonprod` reduction plan** | 2 | FinOps + Platform | 3 d | A decommissioning plan, or a written rationale for Rp573.5M/month. Execution in Q2 |
| **Audit Maps spend against failed geolocation** — Rp64.0M/month against ~20,700 browser geolocation failures a week on the same console (`bravo-surveyor-console`) | 3 | FinOps + squad `LN` | 2 d | Either a defect is fixed and money returns, or the spend is justified and stops being an open question |
| **Decide the Camunda history question** — level `full` with `P90D` on Cloud SQL, against what the trigger-written `application_status_log` retains after day 91 | 4 | S&U + Compliance | 2 d | A recorded decision rather than a default. Implementation in Q2 |

### Days 61–90 — verify the savings landed

No new cost work is scheduled. Phase 3 is verification, because a saving that is not measured on a subsequent invoice is a plan, not a saving.

| Check | Against |
|---|---|
| September and October Cloud Logging against the August baseline of Rp140.5M | Recommendations 1 — target Rp50–90M/month reduction |
| The LOS tier standing view across three months | Recommendation 7 — confirm ≈Rp58M and its trend as volume drains |
| Per-application cost recomputed on the agreed denominators | Recommendation 6 — the first non-provisional unit cost in the pack |

### Deferred, with triggers

| Deferred | Rec | Why | Trigger |
|---|---|---|---|
| Camunda history implementation | 4 | A data-retention change needing compliance sign-off, not an engineering task | After the phase-2 decision |
| `bravo-project-nonprod` execution | 2 | Phase 2 produces the plan; execution depends on what it finds | After the phase-2 plan |

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| Logging configuration fixed | Rp50–90M/month recovered — more than the migration lever — and PEFINDO/SLIK/Dukcapil/CONFINS request bodies stop landing in Cloud Logging. |
| Non-prod examined | The second-largest number in Bravo's bill has an owner and a rationale, or a decommissioning plan. |
| Maps spend explained | Either a defect is fixed and Rp-tens-of-millions come back, or the spend is justified and stops being an open question. |
| History decision made | "What happened to this loan on day 120" has a documented answer instead of an accidental one. |
| Application counts defined | Every rate in this pack — cost per application, intervention rate, zero-intervention completion — stops being provisional. |
| LOS tier tracked | The migration's financial value is a chart, not an argument. |
| Rp1.6B retired from the vocabulary | Nobody plans against a saving that was withdrawn in September 2026. |

---

## Related

- [bravo-delivery.md](bravo-delivery.md) — the console and configuration layer these costs sit under
- [bravo-observability.md](bravo-observability.md) §3, §6 — the log volume and the 404 storm behind two of the levers
- [bravo-testing.md](bravo-testing.md) §4 — the 38,198 parse warnings a week
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.12, §8.4 — the like-for-like derivation and the Bravo team's objection that produced it
- [production-findings/ticket-analysis.md](production-findings/ticket-analysis.md) §4.3 — why the denominators are the weakest link
- LORA [cost.md](../../lora-workspace/docs/production-findings/cost.md) — the same analysis on the other platform
