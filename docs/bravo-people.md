# People: is Bravo actually faster to build in?

**Audience:** Engineering managers, tech leads, the CTO office deciding where the next product family lands
**Claim under test:** *"Developing in Lora is hard, but developing in Bravo is faster and easier because the team now knows what to do."*

**Method.** Jira, `bfifinance.atlassian.net`, read 2026-09-10. The claim points at three boards: **DF4W** ([board 2099](https://bfifinance.atlassian.net/jira/software/c/projects/DF/boards/2099/timeline), project `DF`), **DF2W** ([board 2877](https://bfifinance.atlassian.net/jira/software/c/projects/D2W/boards/2877/timeline), project `D2W`) and **Digital Partnership NDF2W/NDF4W** ([board 683](https://bfifinance.atlassian.net/jira/software/c/projects/BL/boards/683/timeline), project `BL`). All three were enumerated. Two of the three turn out not to contain development work at all, which changes the question — see [§1](#1-the-two-boards-the-claim-cites-contain-no-development-work). Volumes are derived from issue-key deltas at month boundaries (§3, with its stated error direction); cycle times and team shape are from four 50-issue samples pulled at two independent points in the year (§4, §5).

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [The cited boards are empty](#1-the-two-boards-the-claim-cites-contain-no-development-work) · [Where Bravo work lives](#2-where-bravos-development-work-actually-lives-blcs) · [Throughput](#3-throughput-lora-carries-18-the-ticket-volume) · [Cycle time](#4-cycle-time-no-durable-advantage-either-way) · [Team shape](#5-team-shape-7-people-against-22) · **[The shape of one change](#6-the-shape-of-one-change--this-is-what-easier-actually-means)** · [Onboarding](#7-the-onboarding-curve) |
| **3. What to do** | [What the claim gets right](#8-what-the-claim-gets-right-and-what-it-does-not) · [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| The DF4W and DF2W boards show Bravo development moving faster | **Unfalsifiable as posed — the boards contain no development.** `DF` holds 24 issues, 23 of them Epics; `D2W` holds 22 issues, all Epics. Every one is unassigned, none is resolved, and no child stories are tracked there. These are product intake backlogs, not delivery boards. Nothing on them can be timed. |
| Bravo development is faster | **Not supported on throughput; not supported on cycle time.** Bravo's real delivery project (`BLCS`) created ≈2,813 issues Jan–Aug 2026 against LORA's (`BL`) ≈5,144. Median created→resolved time in matched August samples is **2 days on both**. In the June samples LORA was *faster* (median 2 d vs 9 d). |
| …because the team now knows what to do | **Confounded, and probably backwards.** The Bravo team is the team that has worked on Bravo since 2022 (94 all-time authors, 20–23 active per year). The LORA team is largely different people. "The team knows what to do" is a statement about tenure on a four-year-old codebase, not about the platform being easier to learn. |
| Developing in Bravo is *easier* | **Supported, narrowly and importantly.** One change is fewer artefacts. A Bravo ticket decomposes into `[BE]`/`[FE]`/`[QA]`; the equivalent LORA ticket decomposes into `[LSS]`/`[LGS]`/`[LPW]`/`[LTS]`/`[LBOFE]` — five repositories, five sub-tasks, five deploys, for one proxy version bump ([§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means)). That is a real, measurable ergonomics gap and it is the defensible core of the claim. |
| Bravo has a shallower onboarding curve | **Supported on skills, unsupported on codebase.** Java/Spring/Camunda are commodity; Go + a bespoke GSM planner is not. But the thing a new Bravo hire must actually read is a 498k-LOC monolith with product identity in five places and 197 `setStatus` sites. The commodity-skill advantage is real at hiring and largely spent by week three. |
| DF2W is a live Bravo product delivering faster than LORA | **Refuted.** DF2W is **fully configured in production and has started zero applications** in 90 days ([workflow-gap.md §8](workflow-gap.md)); its board is 22 unstarted epics. DF4W — the only product on the unified spine — carries **5.5%** of Bravo's volume. The two products the claim points to are, between them, the smallest thing Bravo runs. |

**The through-line:** the claim is asking about *ergonomics* and being defended with *velocity*. On velocity the data does not support it. On ergonomics it is right, and nobody had measured the size of the effect until now: **five repositories per change against two lanes.**

---

## 1. The two boards the claim cites contain no development work

Both DF boards were enumerated in full.

| Project | Board | Issues | Types | Status | Assignees | Resolved | First → last created |
|---|---|---|---|---|---|---|---|
| `DF` (DF4W) | 2099, kanban | **24** | 23 `Epic`, 1 `Task` | 24 of 24 `TODO` | **0 assigned** | **0** | 2025-12-12 → 2026-09-09 |
| `D2W` (DF2W) | 2877, kanban | **22** (36 keys issued; 14 deleted or moved) | 22 `Epic` | 22 of 22 `To Do` | **0 assigned** | **0** | 2026-06-02 → 2026-08-28 |
| `BL` (LORA DP) | 683 | **10,138 keys** | Story, Sub-task, Task, Bug, Story Bug | mixed | assigned | thousands | 2024-11-21 → 2026-09-10 |

Every `DF` issue is titled `#EPIC …` and labelled by quarter or by `R3#Confins`. Twelve of the 24 were created inside four minutes on 2025-12-12 — a backlog-loading session, not a sprint. `D2W`'s first sixteen were created inside seventeen minutes on 2026-06-02. Nine months after the first DF epic was written, **not one has been assigned to anyone or moved out of To Do.**

This is not a criticism of the boards; a product intake backlog is a legitimate artefact and both are well-formed ones. It is a statement about what can be concluded from them: **a timeline view of these boards shows product intent, not delivery, and cannot be compared with `BL`'s timeline at all.** Any side-by-side that puts board 2099 next to board 683 is comparing an epic backlog with a ticket stream.

The comparison the claim wants has to be made somewhere else.

---

## 2. Where Bravo's development work actually lives: `BLCS`

Bravo LOS engineering is tracked in project **`BLCS`**, which is where the tickets cited elsewhere in this pack come from (`BLCS-4683`, the NMH→GMB role rename; `BLCS-4719`, the approver-chain flags — both in [compare-architecture.md §3.5](compare-architecture.md)). Recent titles confirm the scope: *"#CapabilityTrue [4W Scoring] Adjustment Regular RAC 4W"*, *"[BE] Prepare Query Change GMB to NMH"*, *"[DF2W UW] Sync Surveyor Status Underwriting Return"*.

| | `BLCS` (Bravo LOS) | `BL` (LORA DP) |
|---|---|---|
| First issue | `BLCS-985`, 2023-12-19 | `BL-3`, 2024-11-21 |
| Latest issue at read time | `BLCS-4811`, 2026-09-09 | `BL-10138`, 2026-09-10 |
| Issue types in use | Epic, Story, Story Bug, Task, Sub-task, Bug | Epic, Story, Story Bug, Task, Sub-task, Bug |
| Sub-task naming convention | `[BE]` · `[FE]` · `[QA]` · `[DF2W UW]` | `[LSS]` · `[LGS]` · `[LPW]` · `[LTW]` · `[LTS]` · `[LBOFE]` · `[QA]` · `[PR]` |

The taxonomies match, which is what makes the comparison possible: both projects run the same PMO template — a Story with `[BE]`/`[FE]`/`[QA]`-style sub-tasks, `Story Bug` for defects found inside a story, `Task` for standalone work. Counting a `BLCS` ticket against a `BL` ticket is therefore counting like against like at the *process* level. It is **not** counting like against like at the *change* level, and [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) is where that matters.

**DF2W work does appear in `BLCS`** — `BLCS-4391` *"[DF2W UW] Code Review - BM Return"*, `BLCS-4405`, `BLCS-4420`, `BLCS-4426`. So DF2W is being built; it is just not being tracked on the DF2W board, and it has not yet taken a single production application.

---

## 3. Throughput: LORA carries 1.8× the ticket volume

Jira issue keys are allocated monotonically per project, so the key of the first issue created after a month boundary bounds the number created before it. Boundaries were read directly.

| Boundary | `BLCS` key | `BL` key |
|---|---|---|
| 2026-01-01 | `BLCS-1939` | `BL-4795` |
| 2026-03-01 | `BLCS-2322` | `BL-6002` |
| 2026-05-01 | `BLCS-3229` | `BL-7552` |
| 2026-06-01 | `BLCS-3580` | `BL-8073` |
| 2026-07-01 | `BLCS-3921` | `BL-8652` |
| 2026-08-01 | `BLCS-4289` | `BL-9256` |
| 2026-09-01 | `BLCS-4752` | `BL-9939` |

| Window | Bravo (`BLCS`) | LORA (`BL`) | LORA ÷ Bravo |
|---|---:|---:|---:|
| Jan–Feb | 383 | 1,207 | 3.2× |
| Mar–Apr | 907 | 1,550 | 1.7× |
| May | 351 | 521 | 1.5× |
| Jun | 341 | 579 | 1.7× |
| Jul | 368 | 604 | 1.6× |
| Aug | 463 | 683 | 1.5× |
| **Jan–Aug** | **2,813** | **5,144** | **1.83×** |

**Caveat, stated plainly.** Key deltas are an **upper bound** on issues created, because deleted and moved issues consume keys. `D2W` shows how real that is — 14 of 36 keys have no issue behind them. The bound applies to both projects and there is no reason to think the deletion rate differs systematically, but neither figure is exact. The *trend* — both projects rising, LORA's lead narrowing from 3.2× to 1.5× — is robust to the error; the absolute ratio is not.

**What this does not mean.** It does not mean LORA ships 1.8× the product change. [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) shows LORA decomposes one change into more tickets than Bravo does, and by roughly this factor. Ticket count is a measure of *decomposition* at least as much as of *output*, which is precisely why the raw board comparison the claim invites is not a velocity measurement.

---

## 4. Cycle time: no durable advantage either way

Created → `resolutiondate`, in calendar days, for every resolved issue created in a matched window. Two windows, four samples, `n = 50` each, taken six months apart to avoid reading a single sprint.

| Sample | Window | n | Median | Mean | P90-ish tail |
|---|---|---:|---:|---:|---|
| Bravo `BLCS` | 2026-06-01 → 06-08 | 50 | **9 d** | 22.3 d | 60–98 d (9 issues) |
| LORA `BL` | 2026-06-02 → 06-03 | 50 | **2 d** | 18.5 d | 43–90 d (13 issues) |
| Bravo `BLCS` | 2026-08-11 → 08-18 | 50 | **2 d** | 3.9 d | 10–15 d (8 issues) |
| LORA `BL` | 2026-08-11 → 08-12 | 50 | **2 d** | 5.3 d | 14–29 d (9 issues) |

Three readings.

1. **The medians converge at 2 days and stay there.** In August the two platforms are indistinguishable on the middle of the distribution. Whatever difficulty LORA imposes, it does not show up in how long a typical ticket takes to close.
2. **June's gap runs the *wrong way* for the claim.** Bravo's June median is 9 days against LORA's 2. The cause is visible in the data and is not architectural: nine `BLCS` Stories created on 2026-06-01 all resolved together on 2026-07-17, 07-31 and 08-14 — they were closed in release batches, not when the work finished. `resolutiondate` on a batch-closed Story measures release cadence, not engineering effort.
3. **Both platforms have the same bimodal shape** — a mass of sub-3-day sub-tasks and a tail of Stories that close on release. That is one delivery process running on two platforms, which is what §2 predicted.

**Limits.** Each sample covers one to six working days, so it is a snapshot of two release cadences, not a distribution over the year. Sample windows differ in calendar length because `BL` creates ~1.8× the tickets and 50 issues therefore span fewer days. Both samples exclude unresolved issues, which truncates the tail on both sides equally.

---

## 5. Team shape: 7 people against 22

Distinct assignees across the four 50-issue samples above (100 issues per platform, two separate months):

| | Bravo `BLCS` | LORA `BL` |
|---|---:|---:|
| Distinct assignees, 100 sampled issues | **7** | **22** |
| June sample | 6 | 19 |
| August sample | 7 | 13 |
| Unassigned resolved issues in sample | 1 | 3 |

Two structural observations, stated without naming individuals.

**Bravo's Story layer has one owner.** In both samples, essentially every `Story`-type issue is assigned to a single account, while `Sub-task`s distribute across the remaining six. The one account holds 9 of 9 long-lived Stories in the June sample and 9 of 11 in August. Whether that account is a product owner, a lead or a de-facto integrator, the effect is the same: **the person who holds the shape of a Bravo change is a bus factor of one.** LORA's Stories are spread across a dozen accounts in the same samples.

**Seven engineers is the whole Bravo LOS delivery capacity.** Cross-checked against the codebase: `bravo-bpm-service` has 94 all-time authors but **23 active in 2026** across the whole service, of which the Scoring-and-Underwriting squad owns this repo. Seven active assignees on a 498k-LOC monolith carrying ~94% of BFI's origination volume is a thin shoulder, and it is the strongest argument in this document *against* moving new product families onto Bravo — not because Bravo is slow, but because there is nobody spare.

**How this bears on the claim.** "The team now knows what to do" is doing a lot of work here. It is true, and it is true of seven people. LORA's 22 assignees include people who joined this year and are shipping at the same median cycle time. That is evidence the LORA learning curve is climbable, not evidence it is absent.

---

## 6. The shape of one change — this is what "easier" actually means

This is the finding that survives every caveat above, and it is the one the claim is really about.

Take a single, ordinary change: bumping an upstream integration to v2. In LORA it appears in Jira as **six tickets across five repositories**, all created within two minutes on 2026-08-11 and all assigned to one engineer:

```
BL-9528  [LSS]    add one-obligor-summary-check-v2 schema
BL-9529  [LGS]    add one-obligor-summary-check-v2 handler
BL-9530  [LPW]    migrate get-obligor-summary to v2
BL-9531  [LTS]    register v2 proxy in authorization
BL-9532  [LBOFE]  migrate auto-exposure component to v2
BL-9533  [PR]     Review: one-obligor-summary-check-v2 proxy refactor
```

That is the Schema-First order — `LSS → LGS → LPW/LTW → LTS → LBOFE` — mandated by LORA's own [service-dependencies](../../lora-workspace/docs/architecture/service-dependencies.md) rule, rendered as a ticket each. It is not overhead someone added; it is the architecture made visible in the tracker. The same pattern repeats throughout the `BL` sample: `BL-9506/9507/9508` split one fee calculation across `[LSS]`, `[LTW]` and `[LBOFE]`.

The equivalent Bravo change is **one sub-task**:

```
BLCS-4433  [4W Scoring] BE Implementation - Adjustment NST Rate – RO Rate Standard Override Indicator
```

or, when the front end is involved, **two lanes plus QA**:

```
BLCS-4388  [FE] Development - DF2W section & field visibility on Ringkasan Data & Dokumen
BLCS-4389  [FE] Manual Testing - Verify DF2W reduced view + 4W no-regression
BLCS-4390  [FE] Deploy - Deploy to SIT
```

| | Bravo | LORA |
|---|---|---|
| Repositories touched by one integration change | **1** (`bravo-bpm-service`) | **5** (LSS, LGS, LPW, LTS, LBOFE) |
| Deploys to land it | 1 | up to 5, in a mandated order |
| Jira artefacts | 1–3 | 5–6 |
| Backward-compatibility obligation | none in-process | additive-only, because 8 worker versions run concurrently |
| Cost when the change is wrong | one revert | a version-ordered unwind |

**This is the entire defensible content of "developing in Bravo is faster and easier", and it is worth taking seriously.** A monolith with a relational aggregate really is fewer moving parts per change than thirteen repositories with a schema-first ordering rule. It also explains §3 without any appeal to productivity: LORA's ticket count is ~1.8× Bravo's and LORA's per-change ticket count is ~2–5× Bravo's, so on a per-*change* basis the two teams may well be shipping at similar rates with very different bookkeeping.

The counter-argument is equally concrete and belongs in the same table: the five-repo tax buys product isolation at the data layer, schema-validated contracts, and the ability to add an automated step with no orchestration edit at all — 172 activities against 3 hard precursors ([compare-architecture.md §3.4](compare-architecture.md)). Bravo's one-repo change buys speed and pays with one job executor, one deployment, and a BPMN edit that ships for every product at once.

**Neither is free. The claim is right that Bravo's per-change cost is lower. It is silent on what that cost buys.**

---

## 7. The onboarding curve

| | Bravo | LORA |
|---|---|---|
| Hiring pool | Java 17 / Spring Boot / Camunda 7 — commodity | Go + a bespoke GSM planner + Temporal — "you can get Java or Golang developers, but they won't be able to immediately read the code" |
| Written onboarding | none found in this analysis pack | `docs/onboarding/` — 14 files, ~5,550 lines, with working hands-on tooling |
| Week-1 curriculum | not established | **also not established** — LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) grades this *"overstated, but the entry point is inverted"* |
| What a hire must actually read | 498k LOC main Java; product identity in 5 places; 197 `setStatus` sites in 73 files; a 10,419-line surveyor assignment service | ~617k LOC Go across 13 repos; 172 activity constructors; 155 preconditions with no generated index |
| Concepts with no analogue elsewhere | BPMN escalation as a return channel; a per-application jsonb activity on/off matrix; five-place product discrimination | ReadSet/WriteSet planning; determinism constraints; schema-versioned task queues |

The commodity-skills advantage is real and it is front-loaded. It gets a hire to their first compile faster. It does not help with the parts of Bravo that are actually hard, and by the evidence of this pack those are large: an aggregate root with no behaviour, a lifecycle smeared across four status vocabularies, and orchestration that is untested by 1,453 of 1,457 test files.

**Neither platform has a week-1 curriculum. That is the finding both teams share**, and it is cheaper to fix than either architecture.

---

## 8. What the claim gets right, and what it does not

| Half of the claim | Status |
|---|---|
| "Developing in Lora is hard" | **Partly true, and specifically true.** Five repositories, a mandated ordering rule, additive-only schema changes, and eight concurrent worker versions. Measured in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means). |
| "Developing in Bravo is faster" | **Not supported.** Fewer tickets (1.83×), identical August median cycle time, slower June median. No throughput measure in this document favours Bravo. |
| "…and easier" | **Supported.** One repository, one deploy, no cross-service ordering. This is the real effect and it is worth about 3–5 artefacts per change. |
| "…because the team now knows what to do" | **Not established, and confounded by tenure.** Bravo's seven active assignees have been on this codebase for up to four years. LORA's twenty-two include this year's joiners closing tickets at the same median. Knowing what to do is a property of the people, and the seven do not scale. |

**A fifth thing the claim does not say, and should.** The two products it cites — DF4W and DF2W — are the two smallest things Bravo runs. DF4W is the only product on the unified spine, 5.5% of started applications over 90 days. DF2W is fully configured and has taken **zero** applications. If those are the reference implementations for "Bravo is easier", then the easiness has not yet been tested at volume, on the monoliths, where ~94% of the book actually runs and where 2026 saw more commits than the spine did.

---

## Recommended actions

1. **Stop citing boards 2099 and 2877 as delivery evidence (S).** They are product intake backlogs with zero assigned and zero resolved issues. Either wire DF/D2W epics to their `BLCS` children so the timeline reflects delivery, or state explicitly that Bravo delivery is tracked in `BLCS` and compare there.
2. **Measure changes, not tickets (S–M).** The 1.83× ticket ratio and the 5-repo decomposition point the same direction and cancel. Agree one unit — merged PRs per product change, or Story-level lead time — and publish it for both platforms. Until then neither team's velocity claim is checkable.
3. **Fix the LORA per-change tax directly, since it is the true part of the complaint (M).** The five sub-tasks in `BL-9528..9532` are mechanical and ordered. A generator that scaffolds the schema, handler, activity migration, authorization entry and FE call from one spec turns six tickets into one plus review. LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) already designs this as "Tier 0 — deterministic, a script not a prompt"; it is not built.
4. **Name Bravo's bus factor (S, urgent).** Seven active assignees, with the Story layer held by one account, on the service carrying ~94% of origination. Before any new product family is placed on Bravo, that number has to be a staffing decision someone has made on purpose.
5. **Write the week-1 curriculum for both (S each).** Neither platform has one. LORA has the raw material (~5,550 lines of onboarding docs) and the wrong entry point; Bravo has commodity skills and no map of a 498k-LOC monolith.
6. **Re-ask the question when DF2W has volume (M).** DF2W is the cleanest available test of "building a new product on Bravo is easy": fully configured, zero applications, 22 unstarted epics. Its actual delivery cost — from first `BLCS` ticket to first production application — is the number this debate needs and does not have.

---

## Plan: 30, 60, 90 days

Six recommendations, phased. **Almost none of this is Bravo engineering time** — it is engineering management, PMO and, for one item, the LORA squad. That matters, because [§5](#5-team-shape-7-people-against-22) is the constraint on everything else in this pack: seven active assignees carry ~94% of origination, so any plan spending their days on measurement rather than product has to justify itself. This one spends about half a day of theirs.

**Sequencing rule for this document:** the staffing decision comes first, because it sets the capacity every other document's plan assumes.

### Days 0–30 — settle what is being measured, and who is doing it

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Name the bus factor.** Seven active assignees, Story layer on one account, on the service carrying ~94% of origination. Decide the staffing and the standing allocation for remediation work | 4 | Leadership | a meeting, **day 1** | A recorded decision, including what percentage of Squad S&U time is available for the other four documents' plans |
| **Board hygiene.** Wire DF/D2W epics to their `BLCS` children, or state in the board description that Bravo delivery is tracked in `BLCS` | 1 | PMO | 1 d | Boards 2099 and 2877 can no longer be read as a delivery timeline |
| **Spike the LORA scaffolding generator** — schema + handler + activity + authorization + FE call from one spec | 3 | LORA squad | 5 d spike | A prototype generates the `BL-9528..9532` shape. Full build lands in phase 3 |

### Days 31–60 — agree the unit of comparison

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Measure changes, not tickets.** Agree one unit — merged PRs per product change, or Story-level lead time — and publish it for both platforms | 2 | EM + LORA squad | 3 d | "Bravo shipped 40 product changes last month, LORA 44" is a sentence someone can check. The 1.83× ticket ratio stops being quoted as velocity |

### Days 61–90 — remove the tax, and fix onboarding

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Ship the scaffolding generator** | 3 | LORA squad | 15 d | `BL-9528..9532` becomes one ticket and a generated PR set. The strongest argument for Bravo is answered on the merits, not rebutted |
| **Week-1 curriculum, Bravo** — a map of a 498k-LOC monolith and its five product-discrimination mechanisms | 5 | EM + S&U | 3 d | A new hire reaches a moving loan in week 1, not `SurveyorAssignmentServiceImpl` |
| **Week-1 curriculum, LORA** — invert the entry point from the SDK to a loan moving | 5 | LORA EM | 3 d | A Go hire reaches a moving loan in week 1, not the planner |
| **Start the DF2W clock** — instrument first-`BLCS`-ticket to first-production-application | 6 | PMO | 1 d | The measurement is armed. It reports when DF2W takes production volume |

### Deferred, with a trigger

| Deferred | Rec | Why | Trigger |
|---|---|---|---|
| Re-ask the "is Bravo easier" question with real DF2W data | 6 | DF2W has **zero** applications today and 22 unstarted epics. There is nothing to measure yet | When DF2W takes production volume — the clock started above |

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| Delivery tracked where delivery happens | A DF4W epic on board 2099 shows its `BLCS` children and a real start date. The timeline stops reading as nine months of inactivity. |
| One agreed unit of change | "Bravo shipped 40 product changes last month, LORA shipped 44" is a sentence someone can check, instead of two ticket counts that measure different things. |
| Scaffolding for the five-repo change | `BL-9528..9532` becomes one ticket and a generated PR set. The strongest argument for Bravo loses most of its force, on the merits. |
| Bus factor named | Placing a new product family on Bravo is a decision that includes "and we will hire three more engineers", or it is a decision not taken. |
| Week-1 curriculum | A Go hire reaches a moving loan in week 1 instead of the SDK; a Java hire reaches a moving loan instead of `SurveyorAssignmentServiceImpl`. |
| DF2W measured end to end | The claim gets a real number attached to it, on the product it was made about. |

---

## Related

- [bravo-delivery.md](bravo-delivery.md) — what shipping into Bravo costs at the UI and configuration layer
- [bravo-testing.md](bravo-testing.md) — why "it compiles and deploys" is the only gate a Bravo change passes
- [compare.md](compare.md) — the synthesis and the platform recommendation
- [compare-architecture.md](compare-architecture.md) §3.13, §8.1 — team shape and the unified-rewrite argument
- [workflow-gap.md](workflow-gap.md) §8 — DF4W at 5.5% of volume, DF2W at zero
- LORA [people.md](../../lora-workspace/docs/production-findings/people.md) — the GSM-vs-workflow onboarding problem from the other side
