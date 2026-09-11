# People: is Bravo actually faster to build in?


> **Corrected 2026-09-11, from the team.** Three changes, and the first moves every per-application figure below.
>
> 1. **Bravo's August application count is 118,253, not 76,446.** The old number came from a partial-month extract. 76,446/118,253 = 0.646, against a 0.601 cost-completeness factor on the same row. So August volume was **flat**, not −35%. Every rate derived from it has been recomputed here. The corrected count now agrees with Bravo's engine meter (≈113k) to within 5%. The two used to differ by 48%.
> 2. **`Surveyor Platform - Release reject` was fixed and deployed 2026-09-10.** Everything measured here predates the fix.
> 3. **LORA runs as three sub-teams (LORA 1, 2, 3)** with end-to-end task execution, per the VMP LORA plan — so the bus-factor risk is Bravo-specific.
>
> **Open:** LORA's **171,479** comes from the same billing row and has not been re-verified.

**Audience:** Engineering managers, tech leads, the CTO office deciding where the next product family lands
**Claim under test:** *"Developing in Lora is hard, but developing in Bravo is faster and easier because the team now knows what to do."*

**Method.** We read Jira at `bfifinance.atlassian.net` on 2026-09-10.

The claim points at three boards:

- **DF4W** — [board 2099](https://bfifinance.atlassian.net/jira/software/c/projects/DF/boards/2099/timeline), project `DF`
- **DF2W** — [board 2877](https://bfifinance.atlassian.net/jira/software/c/projects/D2W/boards/2877/timeline), project `D2W`
- **Digital Partnership NDF2W/NDF4W** — [board 683](https://bfifinance.atlassian.net/jira/software/c/projects/BL/boards/683/timeline), project `BL`

We enumerated all three. **We then added a fourth Bravo project on 2026-09-10: `LN`, Surveyor & Verificator, [board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703).** Team Bravo pointed out that it was missing. It is larger than `BLCS`, and it changes the throughput finding in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive).

Two of the original three turn out to contain no development work at all, which changes the question — see [§1](#1-the-two-boards-the-claim-cites-contain-no-development-work).

Volumes come from issue-key deltas at month boundaries (§3, with its stated error direction). Cycle times and team shape come from four 50-issue samples, pulled at two independent points in the year (§4, §5).

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
> `LN` is a live scrum board. It has issued about **6,600 keys since September 2024**. Its issues are assigned, resolved, and closing on the day we read it — `LN-6626` was created at 14:35 and resolved at 17:43 on 2026-09-10. Its summaries are console work: `[Surveyor]`, `[Operation]`, `[FE][TechDebt] Surveyor Route Validation based on Role`. **It is larger than `BLCS`**, which has 4,811 keys, and which this document had treated as the whole of Bravo LOS delivery.
>
> Three consequences, and the first is the one that matters:
>
> 1. **[§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) said "LORA carries 1.8× the ticket volume". That does not survive.** On the corrected scope, Bravo created **6,518** issues from January to August 2026, against LORA's **5,144**. That is Bravo at **1.27×**. We ran four tests for double-counting — project identity, sub-task taxonomy, capability prefixes, cross-project links — and all four show the two projects are **complementary, not duplicative**. So the sum is the supported figure. On the July–August trend, Bravo is at **1.81× LORA**.
> 2. **[§1](#1-the-two-boards-the-claim-cites-contain-no-development-work) ended by saying "the comparison the claim wants has to be made somewhere else."** That was correct, and the somewhere else already existed. `LN` is it. The finding that `DF`/`D2W` are intake backlogs still stands — but the inference that Bravo therefore had one delivery project does not.
> 3. **[§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)'s "7 distinct assignees" covered `BLCS` only.** Sampling `LN` the same way gives **10 more**. And the union of git authors across Bravo's four LOS repositories over the last 12 months is **25 humans, not 7**. The section's conclusion still stands: headcount is a prior CTO decision, not platform evidence. But the number itself was far too low.
>
> **What does not change.** Cycle time ([§4](#4-cycle-time-no-durable-advantage-either-way)) is still a wash. The ergonomics finding in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) still holds: five repositories per LORA change, against two Bravo lanes. `LN` does narrow that gap a little, because it shows Bravo's own front-end work is tracked in a *second* project. And DF2W still has zero applications.

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

**The through-line.** The claim asks about *ergonomics*, and people defend it with *velocity*. **Velocity cannot settle it.** The ticket-count metric reversed direction the moment we added a missing project. That is the clearest possible evidence it was never measuring what it was being asked to measure.

On ergonomics the claim is right. And nobody had measured the size of the effect until now: **five repositories per change, against two lanes.**

---

## 1. The two boards the claim cites contain no development work

Both DF boards were enumerated in full.

| Project | Board | Issues | Types | Status | Assignees | Resolved | First → last created |
|---|---|---|---|---|---|---|---|
| `DF` (DF4W) | 2099, kanban | **24** | 23 `Epic`, 1 `Task` | 24 of 24 `TODO` | **0 assigned** | **0** | 2025-12-12 → 2026-09-09 |
| `D2W` (DF2W) | 2877, kanban | **22** (36 keys issued; 14 deleted or moved) | 22 `Epic` | 22 of 22 `To Do` | **0 assigned** | **0** | 2026-06-02 → 2026-08-28 |
| `BL` (LORA DP) | 683 | **10,138 keys** | Story, Sub-task, Task, Bug, Story Bug | mixed | assigned | thousands | 2024-11-21 → 2026-09-10 |

Every `DF` issue is titled `#EPIC …`, and labelled either by quarter or with `R3#Confins`. Twelve of the 24 were created inside four minutes on 2025-12-12. That is a backlog-loading session, not a sprint. `D2W`'s first sixteen were created inside seventeen minutes on 2026-06-02. Nine months after the first DF epic was written, **not one has been assigned to anyone or moved out of To Do.**

This is not a criticism of the boards. A product intake backlog is a legitimate artefact, and both of these are well formed. It is a statement about what you can conclude from them. **A timeline view of these boards shows product intent, not delivery. It cannot be compared with `BL`'s timeline at all.** Any side-by-side that puts board 2099 next to board 683 is comparing an epic backlog with a ticket stream.

The comparison the claim wants has to be made somewhere else.

> **And it already existed.** When this section was written, it pointed to `BLCS` as that somewhere else. In fact there were **two**: `BLCS` and `LN`. [§2](#2-where-bravos-development-work-actually-lives-blcs-and-ln) now covers both. The conclusion about `DF` and `D2W` is unchanged. They are intake backlogs, and nothing on them can be timed.

---

## 2. Where Bravo's development work actually lives: `BLCS` **and `LN`**

Bravo LOS engineering is tracked in project **`BLCS`**. That is where the tickets cited elsewhere in this pack come from: `BLCS-4683`, the NMH-to-GMB role rename, and `BLCS-4719`, the approver-chain flags. Both appear in [compare-architecture.md §3.5](compare-architecture.md). Recent titles confirm the scope: *"#CapabilityTrue [4W Scoring] Adjustment Regular RAC 4W"*, *"[BE] Prepare Query Change GMB to NMH"*, *"[DF2W UW] Sync Surveyor Status Underwriting Return"*.

| | `BLCS` (Bravo LOS) | `LN` (Bravo Surveyor & Verificator) | `BL` (LORA DP) |
|---|---|---|---|
| Board | — | **703, `LS board`, scrum** | 683 |
| First issue | `BLCS-985`, 2023-12-19 | `LN-76`, 2024-09-09 | `BL-3`, 2024-11-21 |
| Latest issue at read time | `BLCS-4811`, 2026-09-09 | **`LN-6626`, 2026-09-10** — created 14:35, resolved 17:43 | `BL-10138`, 2026-09-10 |
| Issue types in use | Epic, Story, Story Bug, Task, Sub-task, Bug | Epic, Story, Task, Sub-task | Epic, Story, Story Bug, Task, Sub-task, Bug |
| Sub-task naming convention | `[BE]` · `[FE]` · `[QA]` · `[DF2W UW]` | `[Surveyor]` · `[Operation]` · `[FE]` · `[FE][TechDebt]` · `[Master]` | `[LSS]` · `[LGS]` · `[LPW]` · `[LTW]` · `[LTS]` · `[LBOFE]` · `[QA]` · `[PR]` |
| Delivers into | `bravo-bpm-service` | `bravo-surveyor-console`, `bravo-operation-console`, `bravo-underwriting-console` | 13 LORA repos |

**`LN` is the console-tier delivery project**, and it is the larger of Bravo's two: about 6,600 keys against `BLCS`'s 4,811. It tracks the three operator consoles measured in [bravo-testing.md §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change): 763,861 lines of source, 829 test files, and releases three days before this reading.

So together with `BLCS`, **Bravo LOS runs two delivery projects against LORA's one.** That is the mirror image of the repository asymmetry in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means). It is also a warning against reading either project on its own.

The taxonomies match, and that is what makes the comparison possible. Both projects run the same PMO template: a Story with `[BE]`, `[FE]` and `[QA]`-style sub-tasks, `Story Bug` for defects found inside a story, and `Task` for standalone work.

So counting a `BLCS` ticket against a `BL` ticket is like against like at the *process* level. It is **not** like against like at the *change* level. [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) is where that matters.

**DF2W work appears in both delivery projects.** In `BLCS`: `BLCS-4391` *"[DF2W UW] Code Review - BM Return"*, `BLCS-4420` *"[DF2W Scoring] Penyesuaian sumber Data Downpayment"*, and `BLCS-4426`. In `LN`: `LN-6479` *"[DF2W] E2E Testing"*, `LN-4533` *"[DF2W] [O] Application Tracking Regular Risk"*, and `LN-4513` *"[DF2W] [S] History Assignment Regular Risk"*.

So two squads are actively building and testing DF2W. It is simply not tracked on the DF2W intake board. And it has not yet taken a production application.

> **DF2W's actual status, verified 2026-09-10.** Earlier versions of this pack described DF2W as *"fully configured in production"*. That reads as *released and unused*. It is neither. It is **in pre-release testing**, and the Jira trail is clear:
> - `INS-6245` *"[Tech Debt] Seeding Branch Mapping DF2W **for UAT**"* — Done 2026-09-07
> - `LN-6479` *"#CapabilityTrue **[DF2W] E2E Testing**"* — resolved
> - `TDF-4273` *"DF2W — **Golive worker TAC**"* — Done 2026-09-09
> - `ADI-1312` *"Open Rule Firewall access VPN Sibertahan **untuk Pentest LOS**"* — **Done 2026-09-09**, and `BLCS-4799` *"[QA] Support Sample Data Pentest"* — Done 2026-09-07
> - Still open: `D2W-5` *"#EPIC DF2W Operation Process (**Pre Go-Live**)"*, `LN-4573`/`LN-4554` *"[DF2W] [O] **Testing Till Go Live** Low/Medium Risk"*
>
> So *"zero applications"* is correct, and *"in production"* was not. **This pack already had it right in one place.** [bravo-unified-development-process.md](bravo-unified-development-process.md) says DF2W is *"not yet in production"* and *"pre-production"*. Four other places had it wrong.
>
> One qualifier: the penetration test is scoped to **LOS**, not specifically to DF2W. So read it as the platform's release gate rather than DF2W's alone.

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

**This is a reversal, not a revision.** The previous version of this table showed LORA at **1.83×** Bravo over the same eight months, with its lead narrowing from 3.2× to 1.5×. With `LN` counted, Bravo is **ahead overall and pulling away**: level in the spring, and 1.81× LORA by midsummer.

`LN` is not a minor addition. It created **3,705** issues in eight months, against `BLCS`'s 2,813. So the project this document had treated as all of Bravo LOS delivery was the smaller of Bravo's two.

**Caveat, stated plainly, and there are now two.**

**One: key deltas are an upper bound** on issues created, because deleted and moved issues consume keys too. `D2W` shows how real that is — 14 of its 36 keys have no issue behind them. The bound applies to all three projects, and there is no reason to think the deletion rate differs systematically. But no figure here is exact.

**Two: does summing `BLCS` and `LN` double-count the same change? We tested this on 2026-09-10. The answer is no.**

Here is the worry. If one piece of work were tracked as a `BLCS` story for the back end *and* an `LN` story for the console, adding the projects would count it twice. That would matter, because `BL` needs no summing — it bundles every tier into one project, using `[LSS]`, `[LGS]`, `[LPW]`, `[LTS]` and `[LBOFE]` sub-tasks.

We ran four tests. All four point the same way:

| Test | Result |
|---|---|
| **Project identity** | `BLCS` is **"Team Scoring & Underwriting"**, `LN` is **"Team Surveyor & Verificator"** — the split is by **squad and domain, not by tier** |
| **Sub-task taxonomy** | `LN` sub-tasks are **`[BE]` 18, `[FE]` 15, `[QA]` 7** in a 40-issue sample. `LN` is full-stack, so it is not the front-end half of a `BLCS` story |
| **Capability-area prefixes** | Disjoint. `BLCS`: `[4W Scoring]` `[2W Scoring]` `[All Scoring]` `[DF2W Scoring]` `[DF2WSH Scoring]` `[UW 4W]` `[DF2W UW]`. `LN`: `[DF2W] [O]` `[DF2W] [S]` `[NDF2W]` `[NDF4W]` `[DF4W]` `[NDF]` — where `[O]`/`[S]` are the Operation and Surveyor consoles |
| **Cross-project issue links** | **Zero** across the sampled issues. The only links found were `LN`→`LN` |

**The same product appears in both projects, but never the same capability.** DF2W is the clearest case. In `BLCS`: `BLCS-4481` *"[DF2W UW] Penyesuaian UI untuk Product Category"* and `BLCS-4420` *"[DF2W Scoring] Penyesuaian sumber Data Downpayment"*. In `LN`: `LN-4533` *"[DF2W] [O] Application Tracking Regular Risk"* and `LN-4513` *"[DF2W] [S] History Assignment Regular Risk"*. **No pair among 80 sampled summaries describes the same change.**

The two squads even run the same sprint train and test separately. `BLCS-4808` and `BLCS-4809` are *"[QA] Regression Test Sprint 18"*; `LN-6599`, `LN-6600` and `LN-6602` are *"[QA] Regression Testing - Sprint 18"*. That is the one real inflation. **Per-sprint regression and code-review tickets get written twice**, once per squad, where a single-project team writes them once. It is a handful of tickets per sprint, not a doubling.

| Treatment of Bravo's two projects | Bravo Jan–Aug | vs LORA 5,144 | Status |
|---|---:|---|---|
| `BLCS` only — the previous version of this section | 2,813 | LORA **1.83×** | **wrong** — one of two projects |
| Perfectly duplicative: take the larger alone | 3,705 | LORA 1.39× | **excluded by the four tests above** |
| Fully independent: sum them | **6,518** | **Bravo 1.27×** | **the supported figure** |

So the range collapses to its top end: **Bravo at about 6,518 against LORA's 5,144, or Bravo 1.27×.**

Two things could still pull it down. One is a cross-domain ticket type: `BLCS-4405` *"[DF2W UW] Sync Surveyor Status Underwriting Return"* touches both domains and could plausibly have an `LN` counterpart. The other is the duplicated per-sprint QA overhead. Both push the true figure slightly below 6,518. Neither comes close to 3,705.

**What this does not mean.** The original caution now cuts in Bravo's favour, which is exactly why we should keep applying it.

It does not mean Bravo ships 1.27× the product change. [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) shows LORA breaks one change into more tickets than Bravo does. We used that argument to discount LORA's apparent lead. We must now use it to discount Bravo's. Ticket count measures *decomposition* at least as much as *output*.

**So the correct conclusion is not "Bravo is 1.27× faster". It is that ticket volume cannot settle this question in either direction, and this document should stop being cited as though it had.**

Two findings here do survive scope changes: cycle time ([§4](#4-cycle-time-no-durable-advantage-either-way)), which is a wash, and artefacts per change ([§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means)), which is Bravo's genuine edge.

---

## 4. Cycle time: no durable advantage either way

We measured created date to `resolutiondate`, in calendar days, for every resolved issue created in a matched window. That is two windows and **six** samples, 50 issues each, taken six months apart so we are not reading a single sprint.

> **`LN` added 2026-09-10.** The first version of this section sampled `BLCS` and `BL` only. We added `LN` to [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) and [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property), but not here. That left Bravo's larger delivery project out of the one measurement this document calls durable. It is now measured by the same method. **The finding does not change. It gets stronger.**

| Sample | Window | n | Median | Mean | P90-ish tail |
|---|---|---:|---:|---:|---|
| Bravo `BLCS` | 2026-06-01 → 06-08 | 50 | **9 d** | 22.3 d | 60–98 d (9 issues) |
| Bravo `LN` | 2026-06-01 → 06-02 | 50 | **68 d** | 63.4 d | 40–101 d (**45 issues**) |
| LORA `BL` | 2026-06-02 → 06-03 | 50 | **2 d** | 18.5 d | 43–90 d (13 issues) |
| Bravo `BLCS` | 2026-08-11 → 08-18 | 50 | **2 d** | 3.9 d | 10–15 d (8 issues) |
| Bravo `LN` | 2026-08-11 → 08-18 | 50 | **1 d** | 2.4 d | 8–10 d (9 issues) |
| LORA `BL` | 2026-08-11 → 08-12 | 50 | **2 d** | 5.3 d | 14–29 d (9 issues) |

**`LN`'s June figure is not a cycle time.** The reason is the same artefact this document has now found three times. 45 of those 50 issues were created in a **37-minute window on 2026-06-01, between 21:19 and 21:56**. That is a backlog-loading session — the `[DF2W] [O]` and `[S]` capability stories.

So their created-to-resolved interval measures how long the **DF2W programme took to build**. It does not measure how long a ticket takes to turn around. The five issues in that sample that were created organically the next day have a median of **0 days**.

We already found the same mechanism on the `DF` and `D2W` intake boards in [§1](#1-the-two-boards-the-claim-cites-contain-no-development-work), where twelve issues were created inside four minutes. Reading 2 below finds it again on `BLCS`.

**And it points at something real.** *Both* Bravo delivery projects loaded a DF2W backlog on 2026-06-01. That is the DF2W programme kickoff, visible in two projects at once. It is corroborating evidence for the domain split established in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive). It is not evidence of a difference in delivery speed.

Three readings.

1. **The medians converge at 1–2 days and stay there.** In August all three projects look the same in the middle of the distribution: `LN` at 1 day, `BLCS` at 2, `BL` at 2. And `LN`, Bravo's larger project, has both the lowest median and the lowest mean of the three. So whatever difficulty LORA imposes, it does not show up in how long a typical ticket takes to close. Adding Bravo's missing project does not open a gap in Bravo's favour either.
2. **June's gap runs the *wrong way* for the claim.** Bravo's June median is 9 days against LORA's 2. The cause is visible in the data, and it is not architectural. Nine `BLCS` Stories created on 2026-06-01 all resolved together, on 2026-07-17, 07-31 and 08-14. They were closed in release batches, not when the work finished. `resolutiondate` on a batch-closed Story measures release cadence, not engineering effort.
3. **Both platforms have the same two-humped shape:** a mass of sub-tasks closing in under 3 days, and a tail of Stories that close on release. That is one delivery process running on two platforms, which is what §2 predicted.

**Limits.** Each sample covers one to six working days. So it is a snapshot of two release cadences, not a distribution over the year.

The sample windows differ in calendar length, because the projects create tickets at different rates and 50 issues therefore cover different spans. `BL` creates about 1.8× the tickets of `BLCS`, and `LN` creates more than either.

**The June `LN` sample is a backlog load, and should not be read as a cadence at all.** The August windows are the comparable ones. Both samples exclude unresolved issues, which truncates the tail equally on both sides.

---

## 5. Team shape is a prior decision, not a platform property

The measurement first, because it is real and it is quoted elsewhere in this pack. Distinct assignees across the four 50-issue samples above (100 issues per platform, two separate months):

| | Bravo `BLCS` | Bravo `LN` | LORA `BL` |
|---|---:|---:|---:|
| Distinct assignees, 100 sampled issues | **7** | **10** | **22** |
| June sample | 6 | — | 19 |
| August sample | 7 | 8 | 13 |
| Unassigned resolved issues in sample | 1 | 0 | 3 |

> **Corrected 2026-09-10.** The `LN` column is new. We sampled `LN` by the same method: 100 resolved issues, being the most recent 50 plus the 50 resolved in August 2026. That gives **10 distinct assignees**, and none of them appear in the `BLCS` samples.
>
> So the two projects together put **at least 17** people on Bravo LOS delivery. And the union of git authors across Bravo's four LOS repositories over the last 12 months is **25 humans** — 44 identities, of which 19 are bots or service accounts. **The "7" covered one of Bravo's two delivery projects.**
>
> This does not revive the argument the section withdraws. It makes the withdrawal easier. The figure used against Bravo was not just circular. It was also **too low by a factor of three or more.**

> **Correction, 2026-09-11 — and it withdraws an argument this document used to make.**
> Earlier versions of this section read *"Seven engineers is the whole Bravo LOS delivery capacity"*. They treated that as **the strongest argument against putting new product families on Bravo.** That inference is withdrawn.
>
> **Bravo's headcount is the output of an earlier CTO decision to consolidate engineering onto LORA.** It is not a property of Bravo, of BPMN, or of Camunda. The same office that would decide where a new product family goes also sets the allocation, and can reverse it. Citing the consequence of a decision as evidence about that decision is circular. This document was doing exactly that.

**What follows from the correction.**

**Neither number describes a platform.** Bravo has 7 because capacity was moved to LORA. LORA has 22 for the same reason. Move the capacity back and both numbers move. **Team size is an input to the platform decision, not evidence for it.** It has been removed from the edge column in [compare.md §1](compare.md) and from the decision drivers in [compare.md §4](compare.md).

**The throughput comparison in [§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive) has been overtaken twice, and the conclusion is the same both times.**

It originally explained LORA's 1.83× ticket volume as *decomposition*: five repositories per change against one. Headcount was a second explanation for the same gap. It pointed the same way, and ticket counts alone cannot separate the two.

Since then, the 1.83× has turned out to be an artefact of the missing `LN` project. On the corrected scope, Bravo is at 1.27× LORA.

**The instruction is unchanged, and it now applies in Bravo's favour. No per-team velocity claim built on ticket counts should be used as a platform measurement, in either direction.** [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means) survives intact, because it counts artefacts per change rather than tickets per team.

**One thing survives. And as of 2026-09-11 it is specific to Bravo, not neutral across platforms.**

In both samples, almost every `Story`-type issue is assigned to a single account, while the sub-tasks spread across the rest. That is 9 of 9 long-lived Stories in June, and 9 of 11 in August. So whoever holds the shape of a Bravo change today is a **bus factor of one**, on a service carrying about 94% of origination. That is a live operational risk, and it needs an owner **whatever is decided about new products**. In the same samples, LORA's Stories are spread across a dozen accounts.

> **Answered 2026-09-11: LORA's spread is structural, not accidental.** The Bravo/LORA team and the VMP LORA plan both say LORA is organised as **three sub-teams, LORA 1, 2 and 3**. They work different features in parallel. And because most tasks are executed end to end, members share a baseline understanding of the whole system.
>
> That answers the question this paragraph used to leave open: would LORA's wider spread survive a re-staffing? It is a deliberate team design, so it should.
>
> **What that does and does not change.** It does **not** fix Bravo's bus factor. Bravo's Story layer still runs through one account, on the service carrying about 94% of origination.
>
> What it changes is the comparison. We used to call this finding platform-neutral. On the evidence now available it is **not**. Concentration is a Bravo-specific risk, and LORA has a structural answer to it that Bravo does not.
>
> Note the basis. This is a team statement about how LORA is organised. It is not something this pack measured, the way it measured the assignee counts.

**One row gains weight from this correction: the hiring pool.** If capacity is going to be added to either platform, the question becomes *which platform can BFI actually hire for?*

Java 17, Spring Boot and Camunda are a commodity skill set. Go plus a bespoke GSM planner plus Temporal is not. LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) puts it plainly: *"you can get Java or Golang developers, but they won't be able to immediately read the code."*

**This is the one staffing-related fact a CTO cannot reverse, because it is a property of the labour market rather than of an allocation decision. And it favours Bravo.** See [§7](#7-the-onboarding-curve), which bounds it: the advantage is front-loaded, and largely spent by week three.

**How this bears on the claim under test.** "The team now knows what to do" is still confounded. But the confound is tenure, not size. Bravo's assignees have been on this codebase for up to four years. LORA's include this year's joiners, closing tickets at the same median. Knowing what to do is a property of *people and their tenure*, and people can be moved. It is not a property of either platform.

---

## 6. The shape of one change — this is what "easier" actually means

This is the finding that survives every caveat above, and it is the one the claim is really about.

Take one ordinary change: bumping an upstream integration to v2. In LORA it appears in Jira as **six tickets across five repositories**. All six were created within two minutes on 2026-08-11, and all six went to one engineer:

```
BL-9528  [LSS]    add one-obligor-summary-check-v2 schema
BL-9529  [LGS]    add one-obligor-summary-check-v2 handler
BL-9530  [LPW]    migrate get-obligor-summary to v2
BL-9531  [LTS]    register v2 proxy in authorization
BL-9532  [LBOFE]  migrate auto-exposure component to v2
BL-9533  [PR]     Review: one-obligor-summary-check-v2 proxy refactor
```

That is the Schema-First order: `LSS → LGS → LPW/LTW → LTS → LBOFE`. LORA's own [service-dependencies](../../lora-workspace/docs/architecture/service-dependencies.md) rule mandates it, and here it is rendered as one ticket per step. Nobody added this as overhead. It is the architecture made visible in the tracker. The same pattern repeats throughout the `BL` sample — `BL-9506`, `BL-9507` and `BL-9508` split one fee calculation across `[LSS]`, `[LTW]` and `[LBOFE]`.

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
| Repositories touched by one integration change | **1** (`bravo-bpm-service`), or **2** when a console is involved | **5** (LSS, LGS, LPW, LTS, LBOFE) |
| Deploys to land it | 1–2 | up to 5, in a mandated order |
| Jira projects the change appears in | **1** (`BLCS`), or **2** when it crosses the underwriting/surveyor boundary | 1 (`BL`) |
| Jira artefacts | 1–3 | 5–6 |
| Backward-compatibility obligation | none in-process | additive-only, because 8 worker versions run concurrently |
| Cost when the change is wrong | one revert | a version-ordered unwind |

> **Corrected 2026-09-10: the count is 1–2, not 1.** Bravo LOS is four repositories and two Jira projects ([§2](#2-where-bravos-development-work-actually-lives-blcs-and-ln)). So a change that touches a console lands in a console repository too. And a change that crosses the underwriting/surveyor boundary appears in both `BLCS` and `LN` — `BLCS-4405` *"[DF2W UW] Sync Surveyor Status Underwriting Return"* is exactly that.
>
> **The finding survives comfortably.** Two repositories and two projects is still not five repositories in a mandated order, with an additive-only compatibility obligation across eight concurrent worker versions. But the honest figure is 1–2. The earlier flat "1" came from bounding Bravo at `bravo-bpm-service`.

**This is the entire defensible content of "developing in Bravo is faster and easier", and it is worth taking seriously.** A monolith with a relational aggregate really is fewer moving parts per change than thirteen repositories with a schema-first ordering rule.

It also explains §3 without appealing to productivity at all. LORA's per-change ticket count is about 2–5× Bravo's. Divide decomposition out, and the two teams may well be shipping at similar rates with very different bookkeeping.

**This argument has become more important since `LN` was added, not less.** Raw ticket volume now favours Bravo 1.27×. And the same correction that discounted LORA's old 1.83× lead discounts Bravo's new one.

The counter-argument is just as concrete, and it belongs in the same table. The five-repository tax buys three things: product isolation at the data layer, schema-validated contracts, and the ability to add an automated step with no orchestration edit at all — 172 activities against 3 hard precursors ([compare-architecture.md §3.4](compare-architecture.md)). Bravo's one-repository change buys speed. It pays for that with one job executor, one deployment, and a BPMN edit that ships for every product at once.

**Neither is free. The claim is right that Bravo's per-change cost is lower. It is silent on what that cost buys.**

---

## 7. The onboarding curve

| | Bravo | LORA |
|---|---|---|
| Hiring pool | Java 17 / Spring Boot / Camunda 7 — commodity | Go + a bespoke GSM planner + Temporal — "you can get Java or Golang developers, but they won't be able to immediately read the code" |
| Written onboarding | none found in this analysis pack | `docs/onboarding/` — 14 files, ~5,550 lines, with working hands-on tooling |
| Week-1 curriculum | not established | **also not established** — LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) grades this *"overstated, but the entry point is inverted"* |
| What a hire must actually read | 498k LOC main Java; product identity in 5 places; 197 `setStatus` sites in 73 files; a 10,419-line surveyor assignment service. **A console hire instead reads 208–307k LOC of React/TypeScript in one of three repositories** — a smaller and much more conventional surface, which is a real part of Bravo's onboarding story that this section had missed | ~617k LOC Go across 13 repos; 172 activity constructors; 155 preconditions with no generated index |
| Concepts with no analogue elsewhere | BPMN escalation as a return channel; a per-application jsonb activity on/off matrix; five-place product discrimination | ReadSet/WriteSet planning; determinism constraints; schema-versioned task queues |

The commodity-skills advantage is real, and it is front-loaded. It gets a new hire to their first compile faster. It does not help with the parts of Bravo that are actually hard. On this pack's evidence, those parts are large: an aggregate root with no behaviour, a lifecycle spread across four status vocabularies, and orchestration that 1,453 of 1,457 test files never touch.

**Neither platform has a week-1 curriculum. That is the finding both teams share**, and it is cheaper to fix than either architecture.

---

## 8. What the claim gets right, and what it does not

| Half of the claim | Status |
|---|---|
| "Developing in Lora is hard" | **Partly true, and specifically true.** Five repositories, a mandated ordering rule, additive-only schema changes, and eight concurrent worker versions. Measured in [§6](#6-the-shape-of-one-change--this-is-what-easier-actually-means). |
| "Developing in Bravo is faster" | **Not supported — but no longer contradicted either.** The ticket-volume measure reversed when the missing `LN` project was added (Bravo 1.27×, from LORA 1.83×), which retires it as evidence in either direction. What is left is identical August median cycle time and a slower June median. **No *reliable* throughput measure in this document favours either platform.** |
| "…and easier" | **Supported.** One repository, one deploy, no cross-service ordering. This is the real effect and it is worth about 3–5 artefacts per change. |
| "…because the team now knows what to do" | **Not established, and confounded by tenure.** Bravo's assignees have been on this codebase for up to four years; LORA's include this year's joiners closing tickets at the same median. **Knowing what to do is a property of people and their tenure, and people can be reallocated** — so it is not a property of either platform ([§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)). |

**A fifth thing the claim does not say, and should.** It cites two products, DF4W and DF2W. Those are the two smallest things Bravo runs, and one of them is not running at all. DF4W is the only product on the unified spine, at 5.5% of started applications over 90 days. DF2W is fully configured and has taken **zero** applications.

If those are the reference implementations for "Bravo is easier", then nobody has tested that easiness at volume. Volume lives on the monoliths, where about 94% of the book actually runs, and where 2026 saw more commits than the spine did.

---

## Recommended actions

1. **Stop citing boards 2099 and 2877 as delivery evidence. Small effort.** They are product intake backlogs, with zero assigned and zero resolved issues. Pick one of two fixes. Either wire the DF and D2W epics to their `BLCS` **and `LN`** children, so the timeline reflects delivery. Or state explicitly that Bravo delivery is tracked in **`BLCS` and `LN`**, and compare against both. Reading only one of the two is the error this document made until 2026-09-10 ([§3](#3-throughput-on-the-corrected-scope-the-lora-lead-does-not-survive)).
2. **Measure changes, not tickets. Small to medium effort. And this recommendation just proved itself.** The ticket ratio flipped from LORA 1.83× to Bravo 1.27× when we added one Jira project, with no line of code changing. A metric that swings that far on a scope correction is not measuring delivery. The remaining ratio and the five-repository decomposition still point opposite ways, and they cancel.

    So agree one unit — merged pull requests per product change, or Story-level lead time — and publish it for both platforms. Until then, neither team's velocity claim can be checked.
3. **Fix the LORA per-change tax directly. Medium effort.** This is the true part of the complaint. The five sub-tasks in `BL-9528` through `BL-9532` are mechanical and ordered. A generator that scaffolds the schema, handler, activity migration, authorization entry and front-end call from one spec turns six tickets into one, plus review. LORA's own [people.md](../../lora-workspace/docs/production-findings/people.md) already designs this as "Tier 0 — deterministic, a script not a prompt". Nobody has built it.
4. **Set the standing allocation for each platform, and name the bus factor. Small effort, and urgent.** These are two separate things, and only the second is a risk finding.

    **The allocation** is an input. The other four documents' 30/60/90 plans are sized against it — they assume about 25 person-days a month of Squad S&U time. That number needs an owner, not an inference.

    **The bus factor** is the live risk. The Story layer runs through one account, on the service carrying about 94% of origination. Re-staffing alone does not fix knowledge concentration. This risk is **specific to Bravo**: LORA's three sub-teams and end-to-end task execution are a structural answer to it (§5, updated 2026-09-11).

    **The allocation is not an argument about which platform should host new products** ([§5](#5-team-shape-is-a-prior-decision-not-a-platform-property)).
5. **Write the week-1 curriculum for both platforms. Small effort each.** Neither platform has one. LORA has the raw material — about 5,550 lines of onboarding docs — and the wrong entry point. Bravo has commodity skills and no map of a 498,000-line monolith.
6. **Re-ask the question once DF2W has volume. Medium effort.** DF2W is the cleanest available test of "building a new product on Bravo is easy". Its configuration is seeded. It has zero applications. It is **in UAT with a penetration test running**, and its go-live epics are still open. Its actual delivery cost — from the first `BLCS` ticket to the first production application — is the number this debate needs and does not have.

---

## Plan: 30, 60, 90 days

Six recommendations, phased. **Almost none of this is Bravo engineering time.** It is engineering management, PMO, and for one item the LORA squad.

That matters. The other four documents' plans are sized against a share of Squad S&U's time. Whatever that share turns out to be, a plan that spends it on measurement rather than product has to justify itself. This one spends about half a day of it. **The allocation itself is a decision, not a finding** — see [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property).

**The rule for ordering this work.** The allocation decision comes first, because it sets the capacity every other document's plan assumes. It is an *input*, not a finding — see the correction in [§5](#5-team-shape-is-a-prior-decision-not-a-platform-property).

### Days 0–30 — settle what is being measured, and who is doing it

| Item | Rec | Owner | Effort | Done when |
|---|---|---|---|---|
| **Set the standing allocation, and name the bus factor.** Decide what share of engineering time each platform gets for remediation work, and record that the Story layer runs through one account on the service carrying ~94% of origination | 4 | Leadership | a meeting, **day 1** | A recorded decision, including what percentage of Squad S&U time is available for the other four documents' plans. **Not a platform-choice input** |
| **Board hygiene.** Wire DF/D2W epics to their `BLCS` and `LN` children, or state in the board description that Bravo delivery is tracked in **`BLCS` and `LN`** — DF2W work runs through both | 1 | PMO | 1 d | Boards 2099 and 2877 can no longer be read as a delivery timeline, and nobody repeats the mistake this pack made of reading only one of the two delivery projects |
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
| Allocation set and bus factor named | The other four documents' plans are sized against a real number instead of an inferred one, and knowledge concentration on the Story layer has an owner. The allocation is not quoted as a reason to prefer a platform; the concentration risk is Bravo-specific. |
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
