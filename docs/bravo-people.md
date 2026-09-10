# People: is Bravo actually faster to build in?

**Audience:** Engineering managers, tech leads, the CTO office deciding where the next product family lands
**Claim under test:** *"Developing in Lora is hard, but developing in Bravo is faster and easier because the team now knows what to do."*

**Method.** Jira, `bfifinance.atlassian.net`, read 2026-09-10. The claim points at three boards: **DF4W** ([board 2099](https://bfifinance.atlassian.net/jira/software/c/projects/DF/boards/2099/timeline), project `DF`), **DF2W** ([board 2877](https://bfifinance.atlassian.net/jira/software/c/projects/D2W/boards/2877/timeline), project `D2W`) and **Digital Partnership NDF2W/NDF4W** ([board 683](https://bfifinance.atlassian.net/jira/software/c/projects/BL/boards/683/timeline), project `BL`). All three were enumerated. **A fourth Bravo project, `LN` — Surveyor & Verificator, [board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703) — was added on 2026-09-10 after Team Bravo pointed out it was missing; it is larger than `BLCS` and it changes the throughput finding in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive).** Two of the three turn out not to contain development work at all, which changes the question — see [§1](#1-the-two-boards-the-claim-cites-contain-no-development-work). Volumes are derived from issue-key deltas at month boundaries (§3, with its stated error direction); cycle times and team shape are from four 50-issue samples pulled at two independent points in the year (§4, §5).

**On this page:** the problem → what we found → what to do.

| | |
|---|---|
| **1. The problem** | [Verdicts](#verdicts) |
| **2. What we found** | [The cited boards are empty](#1-the-two-boards-the-claim-cites-contain-no-development-work) · [Where Bravo work lives](#2-where-bravos-development-work-actually-lives-blcs-and-ln) · [Throughput](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) · [Cycle time](#4-cycle-time-no-durable-advantage-either-way) · [Team shape is a prior decision](#5-team-shape-is-a-prior-decision-not-a-platform-property) · **[The shape of one change](#6-the-shape-of-one-change--this-is-what-easier-actually-means)** · [Onboarding](#7-the-onboarding-curve) |
| **3. What to do** | [What the claim gets right](#8-what-the-claim-gets-right-and-what-it-does-not) · [Recommended actions](#recommended-actions) · [Plan: 30/60/90](#plan-30-60-90-days) · [What changes when this is done](#what-changes-when-this-is-done) |


---

> **Correction, 2026-09-10 — Bravo's delivery scope in this document was incomplete, and the headline throughput finding reverses.**
> Team Bravo objected that this pack omits the **`LN` project (Surveyor & Verificator, [board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703))** and the three console repositories that project delivers into — `bravo-operation-console`, `bravo-surveyor-console`, `bravo-underwriting-console`. **Verified, and the objection is right.**
>
> `LN` is a live scrum board with **~6,600 keys issued since September 2024**, assigned, resolved, and closing tickets the day this was read (`LN-6626` was created at 14:35 and resolved at 17:43 on 2026-09-10). Its summaries are console work: `[Surveyor]`, `[Operation]`, `[FE][TechDebt] Surveyor Route Validation based on Role`. **It is larger than `BLCS`** (4,811 keys), which this document had treated as the whole of Bravo LOS delivery.
>
> Three consequences, and the first is the one that matters:
>
> 1. **[§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) said "LORA carries 1.8× the ticket volume". That does not survive.** On the corrected scope Bravo created **6,518** issues Jan–Aug 2026 against LORA's **5,144** — Bravo **1.27×**. Four tests for double-counting (project identity, sub-task taxonomy, capability prefixes, cross-project links) all show the two projects are **complementary, not duplicative**, so the sum is the supported figure; the Jul–Aug trend has Bravo at **1.81× LORA**.
> 2. **[§1](#1-the-two-boards-the-claim-cites-contain-no-development-work) ended by saying "the comparison the claim wants has to be made somewhere else."** That was correct, and the somewhere else already existed. `LN` is it. The finding that `DF`/`D2W` are intake backlogs still stands — but the inference that Bravo therefore had one delivery project does not.
> 3. **[§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)'s "7 distinct assignees" was `BLCS`-only.** Sampling `LN` the same way gives **10 more**, and the union of git authors across Bravo's four LOS repositories in the last 12 months is **25 humans, not 7**. The section's conclusion — that headcount is a prior CTO decision and not platform evidence — is unaffected, but the number itself was too low.
>
> **What does not change.** Cycle time ([§4](#4-cycle-time-no-durable-advantage-either-way)) is still a wash. The ergonomics finding in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) — five repositories per LORA change against two Bravo lanes — still holds, though `LN` shows Bravo's own front-end work is tracked in a *second* project, which narrows that gap somewhat. And DF2W still has zero applications.

---

## Verdicts

| Claim | Verdict |
|-------|---------|
| The DF4W and DF2W boards show Bravo development moving faster | **Unfalsifiable as posed — *those* boards contain no development, though Bravo has two that do.** `DF` holds 24 issues, 23 of them Epics; `D2W` holds 22 issues, all Epics. Every one is unassigned, none is resolved, and no child stories are tracked there. These are product intake backlogs, not delivery boards, and nothing on them can be timed. **Bravo's delivery is tracked in `BLCS` and `LN` ([§2](#2-where-bravos-development-work-actually-lives-blcs-and-ln)); the claim points at the wrong boards, not at an absence of work.** |
| Bravo development is faster | **Not settled by throughput in either direction; not supported on cycle time.** Bravo's two delivery projects (`BLCS` + `LN`) created ≈**6,518** issues Jan–Aug 2026 against LORA's (`BL`) ≈**5,144** — Bravo 1.27×, and 1.81× in Jul–Aug. **This reverses the earlier finding of a 1.83× LORA lead, which had counted only `BLCS`.** But ticket volume measures decomposition as much as output, so it does not support the claim either — it retires the metric ([§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive)). Median created→resolved time in matched August samples is **1–2 days across all three projects** (`LN` 1 d, `BLCS` 2 d, `BL` 2 d); in the June samples LORA looks faster, but both Bravo windows there are contaminated by DF2W backlog loading ([§4](#4-cycle-time-no-durable-advantage-either-way)). |
| …because the team now knows what to do | **Confounded by tenure, and the team-size half is withdrawn.** The Bravo team is the team that has worked on Bravo since 2022 (94 all-time authors, 20–23 active per year); the LORA team is largely different people. So this is a statement about tenure on a four-year-old codebase, not about the platform being easier to learn. **And team *size* is not evidence at all** — it is the output of a prior CTO decision to consolidate on LORA, reversible by the same office. The figure once quoted here as Bravo's 7 against LORA's 22 was also **`BLCS`-only**: with `LN` counted it is at least 17 by Jira sample and **25 by git authorship across Bravo's four LOS repositories** ([§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)). |
| Developing in Bravo is *easier* | **Supported, narrowly and importantly.** One change is fewer artefacts. A Bravo ticket decomposes into `[BE]`/`[FE]`/`[QA]`; the equivalent LORA ticket decomposes into `[LSS]`/`[LGS]`/`[LPW]`/`[LTS]`/`[LBOFE]` — five repositories, five sub-tasks, five deploys, for one proxy version bump ([§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means)). That is a real, measurable ergonomics gap and it is the defensible core of the claim. |
| Bravo has a shallower onboarding curve | **Supported on skills, unsupported on codebase.** Java/Spring/Camunda are commodity; Go + a bespoke GSM planner is not. But the thing a new Bravo hire must actually read is a 498k-LOC monolith with product identity in five places and 197 `setStatus` sites. The commodity-skill advantage is real at hiring and largely spent by week three. |
| DF2W is a live Bravo product delivering faster than LORA | **Refuted — and the reason is that DF2W is not live at all.** *Corrected 2026-09-10:* DF2W is **pre-release, in UAT with an LOS penetration test running**, not a released product sitting idle. Its configuration is seeded in the production database and it has started **zero applications** in 90 days ([workflow-gap.md §8](workflow-gap.md)); its go-live epics are still `To Do`. DF4W — the only product on the unified spine — carries **5.5%** of Bravo's volume. The two products the claim points to are, between them, the smallest thing Bravo runs. |

**The through-line:** the claim is asking about *ergonomics* and being defended with *velocity*. **Velocity cannot settle it** — the ticket-count metric reversed direction the moment a missing project was added, which is the clearest possible evidence that it was never measuring what it was being asked to measure. On ergonomics the claim is right, and nobody had measured the size of the effect until now: **five repositories per change against two lanes.**

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

> **And it already existed.** When this section was written it pointed to `BLCS` as that somewhere else. There were **two** — `BLCS` and `LN` — and [§2](#2-where-bravos-development-work-actually-lives-blcs-and-ln) now covers both. The conclusion about `DF` and `D2W` stands unchanged: they are intake backlogs and nothing on them can be timed.

---

## 2. Where Bravo's development work actually lives: `BLCS` **and `LN`**

Bravo LOS engineering is tracked in project **`BLCS`**, which is where the tickets cited elsewhere in this pack come from (`BLCS-4683`, the NMH→GMB role rename; `BLCS-4719`, the approver-chain flags — both in [compare-architecture.md §3.5](compare-architecture.md)). Recent titles confirm the scope: *"#CapabilityTrue [4W Scoring] Adjustment Regular RAC 4W"*, *"[BE] Prepare Query Change GMB to NMH"*, *"[DF2W UW] Sync Surveyor Status Underwriting Return"*.

| | `BLCS` (Bravo LOS) | `LN` (Bravo Surveyor & Verificator) | `BL` (LORA DP) |
|---|---|---|---|
| Board | — | **703, `LS board`, scrum** | 683 |
| First issue | `BLCS-985`, 2023-12-19 | `LN-76`, 2024-09-09 | `BL-3`, 2024-11-21 |
| Latest issue at read time | `BLCS-4811`, 2026-09-09 | **`LN-6626`, 2026-09-10** — created 14:35, resolved 17:43 | `BL-10138`, 2026-09-10 |
| Issue types in use | Epic, Story, Story Bug, Task, Sub-task, Bug | Epic, Story, Task, Sub-task | Epic, Story, Story Bug, Task, Sub-task, Bug |
| Sub-task naming convention | `[BE]` · `[FE]` · `[QA]` · `[DF2W UW]` | `[Surveyor]` · `[Operation]` · `[FE]` · `[FE][TechDebt]` · `[Master]` | `[LSS]` · `[LGS]` · `[LPW]` · `[LTW]` · `[LTS]` · `[LBOFE]` · `[QA]` · `[PR]` |
| Delivers into | `bravo-bpm-service` | `bravo-surveyor-console`, `bravo-operation-console`, `bravo-underwriting-console` | 13 LORA repos |

**`LN` is the console-tier delivery project**, and it is the larger of Bravo's two: ~6,600 keys against `BLCS`'s 4,811. It tracks the three operator consoles measured in [bravo-testing.md §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change) — 763,861 lines of source, 829 test files, releases three days before this reading. Together with `BLCS` it means **Bravo LOS runs two delivery projects against LORA's one**, which is the mirror image of the repository asymmetry in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) and a caution about reading either project alone.

The taxonomies match, which is what makes the comparison possible: both projects run the same PMO template — a Story with `[BE]`/`[FE]`/`[QA]`-style sub-tasks, `Story Bug` for defects found inside a story, `Task` for standalone work. Counting a `BLCS` ticket against a `BL` ticket is therefore counting like against like at the *process* level. It is **not** counting like against like at the *change* level, and [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) is where that matters.

**DF2W work appears in both delivery projects** — `BLCS-4391` *"[DF2W UW] Code Review - BM Return"*, `BLCS-4420` *"[DF2W Scoring] Penyesuaian sumber Data Downpayment"*, `BLCS-4426`; and `LN-6479` *"[DF2W] E2E Testing"*, `LN-4533` *"[DF2W] [O] Application Tracking Regular Risk"*, `LN-4513` *"[DF2W] [S] History Assignment Regular Risk"*. So DF2W is being actively built and tested across two squads; it is just not tracked on the DF2W intake board, and it has not yet taken a production application.

> **DF2W's actual status, verified 2026-09-10.** Earlier versions of this pack described DF2W as *"fully configured in production"*, which reads as *released and unused*. It is neither. It is **in pre-release testing**, and the Jira trail is unambiguous:
> - `INS-6245` *"[Tech Debt] Seeding Branch Mapping DF2W **for UAT**"* — Done 2026-09-07
> - `LN-6479` *"#CapabilityTrue **[DF2W] E2E Testing**"* — resolved
> - `TDF-4273` *"DF2W — **Golive worker TAC**"* — Done 2026-09-09
> - `ADI-1312` *"Open Rule Firewall access VPN Sibertahan **untuk Pentest LOS**"* — **Done 2026-09-09**, and `BLCS-4799` *"[QA] Support Sample Data Pentest"* — Done 2026-09-07
> - Still open: `D2W-5` *"#EPIC DF2W Operation Process (**Pre Go-Live**)"*, `LN-4573`/`LN-4554` *"[DF2W] [O] **Testing Till Go Live** Low/Medium Risk"*
>
> So *"zero applications"* is correct and *"in production"* was not. **This pack already had it right in one place** — [bravo-unified-development-process.md](bravo-unified-development-process.md) says DF2W is *"not yet in production"* and *"pre-production"* — and wrong in four others. The penetration test is scoped to **LOS**, not specifically to DF2W, so read it as the platform's release gate rather than DF2W's alone.

---

## 3. Throughput: on the corrected scope, the LORA lead does not survive

Jira issue keys are allocated monotonically per project, so the key of the first issue created after a month boundary bounds the number created before it. Boundaries were read directly.

| Boundary | `BLCS` key | `LN` key | `BL` key |
|---|---|---|---|
| 2026-01-01 | `BLCS-1939` | `LN-2843` | `BL-4795` |
| 2026-03-01 | `BLCS-2322` | — | `BL-6002` |
| 2026-05-01 | `BLCS-3229` | `LN-4066` | `BL-7552` |
| 2026-06-01 | `BLCS-3580` | — | `BL-8073` |
| 2026-07-01 | `BLCS-3921` | `LN-5048` | `BL-8652` |
| 2026-08-01 | `BLCS-4289` | — | `BL-9256` |
| 2026-09-01 | `BLCS-4752` | `LN-6548` | `BL-9939` |

`LN` was read at four boundaries rather than seven, so its windows are pooled two months at a time and `BLCS`/`BL` are pooled to match.

| Window | Bravo `BLCS` | Bravo `LN` | **Bravo total** | LORA (`BL`) | **Bravo ÷ LORA** |
|---|---:|---:|---:|---:|---:|
| Jan–Apr | 1,290 | 1,223 | **2,513** | 2,757 | 0.91× |
| May–Jun | 692 | 982 | **1,674** | 1,100 | **1.52×** |
| Jul–Aug | 831 | 1,500 | **2,331** | 1,287 | **1.81×** |
| **Jan–Aug** | **2,813** | **3,705** | **6,518** | **5,144** | **1.27×** |

**This is a reversal, not a revision.** The previous version of this table showed LORA at **1.83×** Bravo over the same eight months and described its lead as narrowing from 3.2× to 1.5×. With `LN` counted, Bravo is **ahead overall and pulling away** — level in the spring, 1.81× LORA by midsummer. `LN` is not a minor addition: it created **3,705** issues in eight months against `BLCS`'s 2,813, so the project this document had been treating as all of Bravo LOS delivery was the smaller of Bravo's two.

**Caveat, stated plainly, and there are now two.**

**One — key deltas are an upper bound** on issues created, because deleted and moved issues consume keys. `D2W` shows how real that is: 14 of 36 keys have no issue behind them. The bound applies to all three projects and there is no reason to think the deletion rate differs systematically, but no figure here is exact.

**Two — does summing `BLCS` and `LN` double-count the same change? Tested 2026-09-10: no.** If one piece of work were tracked as a `BLCS` story for the back end *and* an `LN` story for the console, adding the projects would count it twice — and that would matter, because `BL` needs no summing (it bundles every tier into one project via `[LSS]`/`[LGS]`/`[LPW]`/`[LTS]`/`[LBOFE]` sub-tasks). Four tests, all pointing the same way:

| Test | Result |
|---|---|
| **Project identity** | `BLCS` is **"Team Scoring & Underwriting"**, `LN` is **"Team Surveyor & Verificator"** — the split is by **squad and domain, not by tier** |
| **Sub-task taxonomy** | `LN` sub-tasks are **`[BE]` 18, `[FE]` 15, `[QA]` 7** in a 40-issue sample. `LN` is full-stack, so it is not the front-end half of a `BLCS` story |
| **Capability-area prefixes** | Disjoint. `BLCS`: `[4W Scoring]` `[2W Scoring]` `[All Scoring]` `[DF2W Scoring]` `[DF2WSH Scoring]` `[UW 4W]` `[DF2W UW]`. `LN`: `[DF2W] [O]` `[DF2W] [S]` `[NDF2W]` `[NDF4W]` `[DF4W]` `[NDF]` — where `[O]`/`[S]` are the Operation and Surveyor consoles |
| **Cross-project issue links** | **Zero** across the sampled issues. The only links found were `LN`→`LN` |

**The same product appears in both projects, but never the same capability.** DF2W is the clearest case: `BLCS-4481` *"[DF2W UW] Penyesuaian UI untuk Product Category"*, `BLCS-4420` *"[DF2W Scoring] Penyesuaian sumber Data Downpayment"* against `LN-4533` *"[DF2W] [O] Application Tracking Regular Risk"*, `LN-4513` *"[DF2W] [S] History Assignment Regular Risk"*. **No pair in 80 sampled summaries describes the same change.**

The two squads even run the same sprint train and test separately — `BLCS-4808/4809` *"[QA] Regression Test Sprint 18"* alongside `LN-6599/6600/6602` *"[QA] Regression Testing - Sprint 18"*. That is the one real inflation: **per-sprint regression and code-review tickets are written twice**, once per squad, where a single-project team writes them once. It is a handful of tickets per sprint, not a doubling.

| Treatment of Bravo's two projects | Bravo Jan–Aug | vs LORA 5,144 | Status |
|---|---:|---|---|
| `BLCS` only — the previous version of this section | 2,813 | LORA **1.83×** | **wrong** — one of two projects |
| Perfectly duplicative: take the larger alone | 3,705 | LORA 1.39× | **excluded by the four tests above** |
| Fully independent: sum them | **6,518** | **Bravo 1.27×** | **the supported figure** |

So the range collapses to its top end: **Bravo ≈6,518 against LORA's 5,144, Bravo 1.27×.** The residual risk is one cross-domain ticket type — `BLCS-4405` *"[DF2W UW] Sync Surveyor Status Underwriting Return"* touches both domains and could plausibly have an `LN` counterpart — plus the duplicated per-sprint QA overhead. Both push the true figure slightly below 6,518 and neither comes close to 3,705.

**What this does not mean — and the original caution now cuts in Bravo's favour, which is a reason to keep applying it.** It does not mean Bravo ships 1.27× the product change. [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) shows LORA decomposes one change into more tickets than Bravo does; that argument was used to discount LORA's apparent lead and it must now be used to discount Bravo's. Ticket count is a measure of *decomposition* at least as much as of *output*. **The correct conclusion is not "Bravo is 1.27× faster" — it is that ticket volume cannot settle this question in either direction, and this document should stop being cited as though it had.** The two findings here that do survive scope changes are cycle time ([§4](#4-cycle-time-no-durable-advantage-either-way), a wash) and artefacts per change ([§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means), Bravo's genuine edge).

---

## 4. Cycle time: no durable advantage either way

Created → `resolutiondate`, in calendar days, for every resolved issue created in a matched window. Two windows, **six** samples, `n = 50` each, taken six months apart to avoid reading a single sprint.

> **`LN` added 2026-09-10.** The first version of this section sampled `BLCS` and `BL` only — `LN` was added to [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) and [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property) but not here, which left Bravo's larger delivery project out of the one measurement this document calls durable. Now measured by the same method. **The finding does not change; it gets stronger.**

| Sample | Window | n | Median | Mean | P90-ish tail |
|---|---|---:|---:|---:|---|
| Bravo `BLCS` | 2026-06-01 → 06-08 | 50 | **9 d** | 22.3 d | 60–98 d (9 issues) |
| Bravo `LN` | 2026-06-01 → 06-02 | 50 | **68 d** | 63.4 d | 40–101 d (**45 issues**) |
| LORA `BL` | 2026-06-02 → 06-03 | 50 | **2 d** | 18.5 d | 43–90 d (13 issues) |
| Bravo `BLCS` | 2026-08-11 → 08-18 | 50 | **2 d** | 3.9 d | 10–15 d (8 issues) |
| Bravo `LN` | 2026-08-11 → 08-18 | 50 | **1 d** | 2.4 d | 8–10 d (9 issues) |
| LORA `BL` | 2026-08-11 → 08-12 | 50 | **2 d** | 5.3 d | 14–29 d (9 issues) |

**`LN`'s June figure is not a cycle time, and the reason is the same artefact this document has now found three times.** 45 of those 50 issues were created in a **37-minute window on 2026-06-01, 21:19–21:56** — a backlog-loading session, the `[DF2W] [O]`/`[S]` capability stories. Their created→resolved interval measures how long the **DF2W programme took to build**, not how long a ticket takes to turn around. The five issues in that sample that were created organically the next day have a median of **0 days**. The same mechanism was already identified on the `DF`/`D2W` intake boards in [§1](#1-the-two-boards-the-claim-cites-contain-no-development-work) (twelve issues created inside four minutes) and in reading 2 below on `BLCS`.

**And it points at something real:** *both* Bravo delivery projects loaded a DF2W backlog on 2026-06-01. That is the DF2W programme kickoff, visible in two projects at once — which is corroborating evidence for the domain split established in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive), not for a difference in delivery speed.

Three readings.

1. **The medians converge at 1–2 days and stay there.** In August all three projects are indistinguishable on the middle of the distribution — `LN` 1 d, `BLCS` 2 d, `BL` 2 d — and `LN`, Bravo's larger project, has both the lowest median and the lowest mean of the three. Whatever difficulty LORA imposes, it does not show up in how long a typical ticket takes to close; and adding Bravo's missing project does not open a gap in Bravo's favour either.
2. **June's gap runs the *wrong way* for the claim.** Bravo's June median is 9 days against LORA's 2. The cause is visible in the data and is not architectural: nine `BLCS` Stories created on 2026-06-01 all resolved together on 2026-07-17, 07-31 and 08-14 — they were closed in release batches, not when the work finished. `resolutiondate` on a batch-closed Story measures release cadence, not engineering effort.
3. **Both platforms have the same bimodal shape** — a mass of sub-3-day sub-tasks and a tail of Stories that close on release. That is one delivery process running on two platforms, which is what §2 predicted.

**Limits.** Each sample covers one to six working days, so it is a snapshot of two release cadences, not a distribution over the year. Sample windows differ in calendar length because the projects create tickets at different rates and 50 issues therefore span different spans — `BL` creates ~1.8× the tickets of `BLCS`, and `LN` more than either. **The June `LN` sample is a backlog load and should not be read as a cadence at all**; the August windows are the comparable ones. Both samples exclude unresolved issues, which truncates the tail on both sides equally.

---

## 5. Team shape is a prior decision, not a platform property

The measurement first, because it is real and it is quoted elsewhere in this pack. Distinct assignees across the four 50-issue samples above (100 issues per platform, two separate months):

| | Bravo `BLCS` | Bravo `LN` | LORA `BL` |
|---|---:|---:|---:|
| Distinct assignees, 100 sampled issues | **7** | **10** | **22** |
| June sample | 6 | — | 19 |
| August sample | 7 | 8 | 13 |
| Unassigned resolved issues in sample | 1 | 0 | 3 |

> **Corrected 2026-09-10.** The `LN` column is new. Sampling `LN` by the same method — 100 resolved issues, most recent 50 plus the 50 resolved in August 2026 — gives **10 distinct assignees**, none of whom appear in the `BLCS` samples. The two projects together put **at least 17** people on Bravo LOS delivery, and the union of git authors across Bravo's four LOS repositories over the last 12 months is **25 humans** (44 identities, 19 of them bots or service accounts). **The "7" was one of Bravo's two delivery projects.**
>
> This does not resurrect the argument the section withdraws — it makes the withdrawal easier. The figure that was being used against Bravo was not only circular; it was also **too low by a factor of three or more.**

> **Correction, 2026-09-11 — and it withdraws an argument this document used to make.**
> Earlier versions of this section read *"Seven engineers is the whole Bravo LOS delivery capacity"* and treated it as **the strongest argument against placing new product families on Bravo.** That inference is withdrawn.
>
> **Bravo's headcount is the output of a previous CTO decision to consolidate engineering onto LORA.** It is not a property of Bravo, of BPMN, or of Camunda. The same office that would decide where a new product family goes sets the allocation, and can reverse it. Citing the consequence of a decision as evidence about the decision is circular, and this document was doing exactly that.

**What follows from the correction.**

**Neither number describes a platform.** Bravo has 7 because capacity was moved to LORA; LORA has 22 for the same reason. If capacity moved back, both numbers move. **Team size is an input to the platform decision, not evidence for it**, and it has been removed from the edge column in [compare.md §1](compare.md) and from the decision drivers in [compare.md §4](compare.md).

**The throughput comparison in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) has been overtaken twice, and the conclusion is the same both times.** It originally explained LORA's 1.83× ticket volume as *decomposition* — five repositories per change against one — and headcount was a second explanation for the same gap, pointing the same way, inseparable from ticket counts alone. The 1.83× has since been shown to be an artefact of missing `LN`, and on the corrected scope Bravo is at 1.27× LORA. **The instruction is unchanged and now applies in Bravo's favour: no per-team velocity claim built on ticket counts — in either direction — should be used as a platform measurement.** [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) survives intact, because it counts artefacts per change rather than tickets per team.

**One thing survives, and it is platform-neutral.** In both samples essentially every `Story`-type issue is assigned to a single account while sub-tasks distribute across the rest — 9 of 9 long-lived Stories in June, 9 of 11 in August. Whoever holds the shape of a Bravo change today is a **bus factor of one**, on a service carrying ~94% of origination. That is a live operational risk needing an owner **whatever is decided about new products**, and it is not an argument for or against either platform. LORA's Stories are spread across a dozen accounts in the same samples; whether that survives a re-staffing is unknown.

**And one row gains weight from this correction: the hiring pool.** If capacity is to be added to either platform, the question becomes *which platform can BFI actually hire for?* Java 17 / Spring Boot / Camunda is a commodity skill set. Go plus a bespoke GSM planner plus Temporal is not — LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) puts it as *"you can get Java or Golang developers, but they won't be able to immediately read the code."* **This is the one staffing-adjacent fact that is not CTO-reversible, because it is a property of the labour market rather than of an allocation decision — and it favours Bravo.** See [§7](#7-the-onboarding-curve), where it is bounded: the advantage is front-loaded and largely spent by week three.

**How this bears on the claim under test.** "The team now knows what to do" is still confounded, but by tenure rather than by size: Bravo's assignees have been on this codebase for up to four years, and LORA's include this year's joiners closing tickets at the same median. Knowing what to do is a property of *people and their tenure*, and people can be moved. It is not a property of either platform.

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

**This is the entire defensible content of "developing in Bravo is faster and easier", and it is worth taking seriously.** A monolith with a relational aggregate really is fewer moving parts per change than thirteen repositories with a schema-first ordering rule. It also explains §3 without any appeal to productivity: LORA's per-change ticket count is ~2–5× Bravo's, so once decomposition is divided out the two teams may well be shipping at similar rates with very different bookkeeping. **This argument has become more important, not less, since `LN` was added** — raw ticket volume now favours Bravo 1.27×, and the same correction that discounted LORA's old 1.83× lead discounts Bravo's new one.

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
| "Developing in Bravo is faster" | **Not supported — but no longer contradicted either.** The ticket-volume measure reversed when the missing `LN` project was added (Bravo 1.27×, from LORA 1.83×), which retires it as evidence in either direction. What is left is identical August median cycle time and a slower June median. **No *reliable* throughput measure in this document favours either platform.** |
| "…and easier" | **Supported.** One repository, one deploy, no cross-service ordering. This is the real effect and it is worth about 3–5 artefacts per change. |
| "…because the team now knows what to do" | **Not established, and confounded by tenure.** Bravo's assignees have been on this codebase for up to four years; LORA's include this year's joiners closing tickets at the same median. **Knowing what to do is a property of people and their tenure, and people can be reallocated** — so it is not a property of either platform ([§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)). |

**A fifth thing the claim does not say, and should.** The two products it cites — DF4W and DF2W — are the two smallest things Bravo runs, and one of them is not running at all. DF4W is the only product on the unified spine, 5.5% of started applications over 90 days. DF2W is fully configured and has taken **zero** applications. If those are the reference implementations for "Bravo is easier", then the easiness has not yet been tested at volume, on the monoliths, where ~94% of the book actually runs and where 2026 saw more commits than the spine did.

---

## Recommended actions

1. **Stop citing boards 2099 and 2877 as delivery evidence (S).** They are product intake backlogs with zero assigned and zero resolved issues. Either wire DF/D2W epics to their `BLCS` children so the timeline reflects delivery, or state explicitly that Bravo delivery is tracked in `BLCS` and compare there.
2. **Measure changes, not tickets (S–M) — and this recommendation just proved itself.** The ticket ratio inverted from LORA 1.83× to Bravo 1.27× on the addition of one Jira project, without a line of code changing. A metric that swings that far on a scope correction is not measuring delivery. The remaining ratio and the 5-repo decomposition still point opposite ways and cancel. Agree one unit — merged PRs per product change, or Story-level lead time — and publish it for both platforms. Until then neither team's velocity claim is checkable.
3. **Fix the LORA per-change tax directly, since it is the true part of the complaint (M).** The five sub-tasks in `BL-9528..9532` are mechanical and ordered. A generator that scaffolds the schema, handler, activity migration, authorization entry and FE call from one spec turns six tickets into one plus review. LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) already designs this as "Tier 0 — deterministic, a script not a prompt"; it is not built.
4. **Set the standing allocation for each platform, and name the bus factor (S, urgent).** Two separate things, and only the second is a risk finding. **The allocation** is an input the other four documents' 30/60/90 plans are sized against — they assume ~25 person-days a month of Squad S&U time, and that number needs an owner rather than an inference. **The bus factor** is the live risk: the Story layer runs through one account on the service carrying ~94% of origination, and re-staffing does not fix knowledge concentration by itself. **Neither is an argument about which platform should host new products** ([§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)).
5. **Write the week-1 curriculum for both (S each).** Neither platform has one. LORA has the raw material (~5,550 lines of onboarding docs) and the wrong entry point; Bravo has commodity skills and no map of a 498k-LOC monolith.
6. **Re-ask the question when DF2W has volume (M).** DF2W is the cleanest available test of "building a new product on Bravo is easy": configuration seeded, zero applications, **in UAT with a pen test running**, go-live epics still open. Its actual delivery cost — from first `BLCS` ticket to first production application — is the number this debate needs and does not have.

---

## Plan: 30, 60, 90 days

Six recommendations, phased. **Almost none of this is Bravo engineering time** — it is engineering management, PMO and, for one item, the LORA squad. That matters because the other four documents' plans are sized against a share of Squad S&U's time, and whatever that share turns out to be, a plan spending it on measurement rather than product has to justify itself. This one spends about half a day of it. **The allocation itself is a decision, not a finding** — see [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property).

**Sequencing rule for this document:** the allocation decision comes first, because it sets the capacity every other document's plan assumes. It is an *input*, not a finding — see the correction in [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property).

### Days 0–30 — settle what is being measured, and who is doing it

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Set the standing allocation, and name the bus factor.** Decide what share of engineering time each platform gets for remediation work, and record that the Story layer runs through one account on the service carrying ~94% of origination | 4 | Leadership | a meeting, **day 1** | A recorded decision, including what percentage of Squad S&U time is available for the other four documents' plans. **Not a platform-choice input** |
| **Board hygiene.** Wire DF/D2W epics to their `BLCS` children, or state in the board description that Bravo delivery is tracked in `BLCS` | 1 | PMO | 1 d | Boards 2099 and 2877 can no longer be read as a delivery timeline |
| **Spike the LORA scaffolding generator** — schema + handler + activity + authorization + FE call from one spec | 3 | LORA squad | 5 d spike | A prototype generates the `BL-9528..9532` shape. Full build lands in phase 3 |

### Days 31–60 — agree the unit of comparison

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Measure changes, not tickets.** Agree one unit — merged PRs per product change, or Story-level lead time — and publish it for both platforms | 2 | EM + LORA squad | 3 d | "Bravo shipped 40 product changes last month, LORA 44" is a sentence someone can check. Ticket ratios — 1.83× when it favoured LORA, 1.27× when it favoured Bravo — stop being quoted as velocity |

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
| Re-ask the "is Bravo easier" question with real DF2W data | 6 | DF2W has **zero** applications today and is still in UAT and pen test. There is nothing to measure yet | When DF2W takes production volume — the clock started above |

---

## What changes when this is done

| Recommendation | Example when done |
|---|---|
| Delivery tracked where delivery happens | A DF4W epic on board 2099 shows its `BLCS` children and a real start date. The timeline stops reading as nine months of inactivity. |
| One agreed unit of change | "Bravo shipped 40 product changes last month, LORA shipped 44" is a sentence someone can check, instead of two ticket counts that measure different things. |
| Scaffolding for the five-repo change | `BL-9528..9532` becomes one ticket and a generated PR set. The strongest argument for Bravo loses most of its force, on the merits. |
| Allocation set and bus factor named | The other four documents' plans are sized against a real number instead of an inferred one, and knowledge concentration on the Story layer has an owner. Neither is quoted as a reason to prefer a platform. |
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
