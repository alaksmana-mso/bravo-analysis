# Option 3 — Migrate Bravo to LORA

**Companion to** [option-1.md](option-1.md) (version upgrade), [option-2.md](option-2.md) (Temporal) and [option-summary.md](option-summary.md) (comparison and decision framework).

**Status of the wider decision.** No decision has been taken about Bravo's long-term platform, and this document does not assume one. LORA runs in production alongside Bravo today. Whether it becomes BFI's single loan origination system is exactly the question this pack exists to inform.

**Verdict in one line.** This is the only option that ends with one platform instead of two. It is also the only one that asks the organisation to change paradigm as well as runtime. That is where the most-cited objection to it lives, and it is where this document spends its longest section.

---

## 1. Where the two platforms stand today

| | Bravo | LORA |
|---|---|---|
| Applications, Aug 2026 (billing sheet) | 118,253 — **41%** | 171,479 — **59%** |
| Trend Jul → Aug (billing sheet) | 118k → 118k — flat | rising |
| Bravo engine meter, same period | ~120k process starts/month | — |
| Orchestration tier cost | ≈Rp58M/month prod | ≈Rp431M/month all-in |
| Per application | ≈Rp490–515 | ≈Rp2,500–3,200 |
| Product families served | 4 live root workflows | 7 families, 13 repos |
| Paradigm | Imperative BPMN on Camunda | Data-centric GSM planner on Temporal |

Source: [compare.md §3.12](compare-architecture.md), [LORA cost findings](../../lora-workspace/docs/production-findings/cost.md).

**Two caveats on the volume figures. Both come from the LORA cost document itself.** First, the billing sheet's application counts are the least-verified numbers in the pack. An application originated in LORA is plausibly counted a second time in Bravo when it is booked at go-live. Second, Bravo's engine meter reports about 120,000 process starts a month against the sheet's 118,253. So the split is clear in direction and soft in number. It should not be the sole basis for a platform decision. Ask the billing owner to define both columns first.

LORA already runs the NDF product family on the `dp-ndf` document schema, with `ndf4w` and `ndf2w` SKU packages. So Option 3 is not "build an LOS on LORA". It is **close the coverage gap, prove parity, cut the remaining book over, and switch Bravo off.** That is much less risky than a green-field build, and it is the strongest structural argument for this option.

---

## 2. What actually has to move

Counted from the production database, 90 days to 2026-09-09 ([workflow-gap.md §8](workflow-gap.md)):

| Root workflow | Product | Starts (90d) | Share | Migration difficulty |
|---|---|--:|--:|---|
| `NDF2W` | NDF 2-wheel | **248,682** | 73.4% | **Hardest.** The whole 2-wheel retail book, 16 master configs, 185,574 survey tasks averaging 58h open, 49 product-specific delegates with no unified equivalent |
| `NDF4W` | NDF 4-wheel | 59,909 | 17.7% | Hard. 6 master configs, 40 product-specific delegates, 50,650 high-risk survey tasks |
| `NDF4W_RO` | Repeat order | 11,458 | 3.4% | Messiest per unit. RO same-asset, Pallav customer creation, RO-digital operation assignment — the least reusable corners |
| `Unified_Process_Main_Workflow` | **DF4W only** | 18,809 | 5.5% | Easiest. 8-step spine, 36 children, activities already config-gated |
| `NDF4W_Sharia` | Sharia | separate engine | — | Own deployment; must be scoped separately |
| `UNSECURED`, pre-approval, multi-asset | | 0 in 90d | — | Dormant or elsewhere; confirm before scoping |

**The sharp finding from [workflow-gap.md §8.2](workflow-gap.md):** "a single workflow for all products" is false in production. The unified spine carries DF4W plus a 3-application NDF4W pilot. The legacy per-product monoliths carry **about 94% of applications and the entire retail book**. So migrating Bravo to LORA is overwhelmingly a *legacy monolith* migration. Those monoliths are 9,494 and 8,464 lines of BPMN. Their product logic also lives in Java `isNDF4W()` predicates, YAML maps, six-column selector tables and gateway string comparisons.

Beyond the workflows, three Bravo capability blocks need a LORA home:

1. **Human work.** 217,000 lines, 43.6% of the service. The big pieces are `SurveyorAssignmentServiceImpl` (10,419 lines), `OperationAssignmentServiceImpl` (8,177) and `BaseUnderwritingApprovalServiceImpl` (4,604), plus the data-driven approver ladder in `underwriting_job_level_lov_detail`. LORA has counterparts: `lora-task-service` at 89,000 lines, `survey.go` at 5,473 lines and 125 transitions, `underwriting.go` at 3,041 lines and 72 transitions. But nobody has proved coverage parity per product and risk tier.
2. **Operator surfaces** — `ApplicationErrorTracking` console, ~25 retry/reprocess/revive/cancel endpoints, Camunda Cockpit, and `bravo-underwriting-console`.
3. **Durable reprocess generations.** Bravo's `prevApplication` and `currentIndex` chain keeps every attempt as a queryable row. LORA rewinds and re-originates instead, which loses that history ([compare.md §3.7](compare-architecture.md), §6 lesson 3).

---

## 3. The paradigm objection, examined

This is the objection to Option 3 people cite most often. It deserves to be assessed, not dismissed and not simply accepted. Here is the complaint in the LORA team's own words ([Current LORA challenges in Production](../../lora-workspace/docs/production-findings/Current%20LORA%20challenges%20in%20Production.md)):

> "Workflow (imperative) to be translated to (declarative) data readiness as a trigger to run Activity using Golang and LORA SDK. Human tendency is to think in terms of Workflow (e.g: Underwriting will start after Survey) rather than remembering if asset list fields and customer address are filled then start Survey."

> "You can get Java or Golang developers, but they won't be able to immediately read the code and understand. It will take time to understand the concept and go through the coding for SDK or Planner. Modifying SDK and the Planner will take longer time to understand."

LORA's own investigation ([people.md](../../lora-workspace/docs/production-findings/people.md)) tested each of these. Its verdicts are mixed, and the mix is the useful part:

| Claim | LORA's own verdict | What it means for Option 3 |
|---|---|---|
| GSM destroys the business order of the loan process | **Refuted.** GSM *de-indexes* it, it does not delete it. 155 `SetPrecondition` sites encode "when does this stage open?" in business language; the nine `$.status.application` milestones are the process | The order is recoverable, but only through a generated index (status × activity × product) that does not exist yet. Until it does, the objection is true *in practice* even though it is false in principle |
| Go/Java hires cannot onboard | **Overstated, but the entry point is inverted.** 14 onboarding files / ~5,550 lines exist and the tooling works — but there is **no week-1 curriculum and no ADRs**, so hires start at the SDK instead of at a loan moving | A fixable documentation problem, not a property of GSM. But it is unfixed, and it is what people experience |
| Business needs a hand-maintained readiness spreadsheet | **Refuted as necessary.** `depchain-generator` derives it statically — but it is unfinished (no CSV, no edges, LPW-only) and **not run in CI** | The tool that answers the objection exists and is 80% done. Finishing it is small and high-leverage |
| One team must master all LOS domains because `dp-ndf` is shared | **Confirmed as an organizational cost.** One document and one planner leave no seam for a UW/Surveyor team split; the top production incident spans both domains | The one verdict that is *confirmed*, and it is structural rather than educational. It constrains how BFI can organise squads, and Bravo's current split by LOS stage would not survive the move. **Strengthened 2026-09-10 — the seam Bravo would lose is not hypothetical; it is measured. See [§3a](#3a-the-seam-lora-lacks-is-one-bravo-is-actively-running).** |

### 3a. The seam LORA lacks is one Bravo is actively running

**Added 2026-09-10.** The fourth complaint above says a shared document and a shared planner leave no seam along which to split UW and Surveyor teams. We assessed it as *confirmed but abstract* — a constraint on how BFI could organise squads. New evidence makes it concrete. **Bravo's LOS is already organised along exactly that seam, and the split shows up in four independent places:**

| Where | Team Scoring & Underwriting | Team Surveyor & Verificator |
|---|---|---|
| Jira project | **`BLCS`** — 4,811 keys | **`LN`** — ~6,600 keys, [board 703](https://bfifinance.atlassian.net/jira/software/c/projects/LN/boards/703) |
| Capability areas | `[4W Scoring]` `[2W Scoring]` `[All Scoring]` `[DF2W Scoring]` `[UW 4W]` `[DF2W UW]` | `[DF2W] [O]` `[DF2W] [S]` `[NDF2W]` `[NDF4W]` `[NDF]` |
| Console repositories | `bravo-underwriting-console` (249k LOC) | `bravo-surveyor-console` (307k LOC), `bravo-operation-console` (208k LOC) |
| Sprint testing | `BLCS-4808/4809` "Regression Test Sprint 18" | `LN-6599/6600/6602` "Regression Testing - Sprint 18" |

Cross-project issue links between them: **zero**. Assignee overlap in the sampled issues: **zero**. So: two squads, one sprint train, no shared scope, separate front ends. Each is full-stack inside its own domain — `LN` sub-tasks split `[BE]` 18, `[FE]` 15, `[QA]` 7. Delivery figures are in [bravo-people.md §3–§5](bravo-people.md).

**What this does to the option.** It turns "Bravo's split by LOS stage would not survive the move" from a prediction into a **priced loss**. Two squads ship independently today, against separate repositories and separate boards. Option 3 would merge them into a shared-document model whose own investigation says there is no seam to split them back.

That is not a reason to reject the option. LORA's [people.md](../../lora-workspace/docs/production-findings/people.md) proposes end-to-end teams per product family as the replacement organisation, and that is a coherent answer. But it is a real cost. Unlike the other three complaints it is **structural and cannot be remediated**. So state it plainly as *"merge two working squads and re-cut them by product family"*, not as *"a constraint on how BFI can organise"*.

**One caution, so this is not read as one-sided.** Bravo's seam is not free either. [compare-architecture.md §3.14](compare-architecture.md) shows that the surveyor-assignment boundary is the top operations complaint on **both** platforms, at nearly the same rate: 21.8% of Bravo's tickets and 25.0% of LORA's. And `BLCS-4405`, *"[DF2W UW] Sync Surveyor Status Underwriting Return"*, is exactly the kind of ticket a seam creates. Its whole purpose is keeping two sides of a boundary consistent. So Bravo's seam lets two squads ship independently, and Bravo pays for it in cross-boundary synchronisation.

**The honest reading.** Three of the four complaints are about missing artefacts: a generated readiness index, a week-1 curriculum, and ADRs. Weeks of work fixes those. Changing paradigm does not come into it. The fourth complaint, team ownership, is a genuine property of a shared-document design and does not go away. So the paradigm objection is **real but mostly fixable**, and fixing it is cheap next to the migration. Price it into Option 3 explicitly — the effort table below does — rather than treating it as either a blocker or a grumble.

**Do not lose the counter-consideration.** [compare.md §3.4](compare-architecture.md) rates GSM's central claim as validated. In LORA, adding an automated check means writing a new Constructor with a ReadSet, a WriteSet and a precondition. There is no orchestration edit. That was verified at 172 activities with only 3 hard precursors. In Bravo the same change touches a `JavaDelegate`, a BPMN file, a gateway, a retry choice, a `WorkflowConstants` key and a configuration table.

That capability is what Option 3 buys, and the paradigm objection is its price. Whether the trade is worth making is a judgement about which cost the organisation would rather carry. That judgement belongs to the CTO, not to this document.

---

## 4. Effort

This is the lowest-confidence estimate in the pack. Nobody has measured LORA's per-product coverage gap against Bravo. So treat the first workstream as the one that makes every other number here real.

| Workstream | Detail | Eng-months |
|---|---|---|
| **Gap inventory, per product and risk tier** | The method already written down for the legacy→unified migration ([bravo-unified-legacy-to-unified.md §3](bravo-unified-legacy-to-unified.md)) applied across the LORA boundary: every Bravo delegate, status, assignment rule and approval path mapped to an existing LORA ProcessStep, a required new one, or "drop". **Do this before committing to any of the numbers below.** | 1–2 |
| **Close product coverage in LORA** | NDF2W (16 configs), NDF4W (6 configs), RO variants, Sharia. New ProcessSteps with ReadSet/WriteSet/preconditions; document schema extensions | **10–20** |
| **Human-task parity** | Surveyor assignment and coverage/level eligibility, operation assignment, the underwriting approval ladder and its feature-flagged chain rules, document submission. The largest single block and the one with the least reuse | **6–12** |
| **Paradigm-cost remediation** (§3) | Finish `depchain-generator` and run it in CI to produce the status × activity × product index per product family; a week-1 curriculum and ADRs; resolve the team-ownership seam. Small, and it de-risks everything downstream | **1–2** |
| **LORA reliability remediation — a hard prerequisite** | See §6. Bounded retries and a terminal-error class, the `SetTermination` defect (about **half of all loans never reach a terminal state**), an operator surface for wedged loans, per-family APM (6 of 7 families have no production APM presence), and a green nightly | **4–8** |
| **Parallel run, parity diffing, tier-by-tier cutover, drain** | Same pattern as §4 of the legacy→unified plan, at higher stakes: NDF2W alone is 248,682 instances per quarter. Includes a terminal sweep for the parked-instance tail (§8) | **6–10** |
| **Bravo decommission** | Retire `ms-bpm` and `prod-postgres-bpm-d2bpm`, the SIT/UAT/Sharia copies, the console, and the dead `setting.workflow.map` entries. Resolve data retention: Camunda history is purged at 90 days but the relational record is the system of record for booked loans | 2–3 |
| **Total** | | **30–57** |

**Elapsed:** 15–24 months. **Indicative one-off** at an assumed Rp30–50M per engineer-month: **Rp900M – Rp2.85B**.

**One important qualification on that total.** Some of this work overlaps with LORA's existing product roadmap and reliability backlog. It would be done whether or not Bravo migrates. So the *incremental* cost of a migration decision is lower than the table's total. Nobody has quantified by how much. That should happen before the number goes into a business case. The gap inventory is the workstream that produces the figure.

---

## 5. Sequence

```mermaid
flowchart TB
  classDef s fill:#DDEBF1,stroke:#1F6F8B,color:#12252D
  classDef g fill:#F6E3C5,stroke:#B07D2B,color:#3A2A0A
  B0["BRIDGE: Bravo must run safely throughout<br/>see option-1.md"]:::g --> S1
  S1["1. Gap inventory<br/>Bravo capability → LORA ProcessStep"]:::s --> S2["2. Paradigm + reliability remediation<br/>readiness index, bounded retries, termination, wedge console"]:::s
  S2 --> S3["3. Close coverage: DF4W first (18.8k/90d)<br/>then NDF4W_RO (11.5k)"]:::s
  S3 --> S4["4. Shadow run and diff outcomes<br/>decisions, statuses, assignments, documents"]:::s
  S4 --> S5["5. NDF4W (60k/90d) by risk tier"]:::s
  S5 --> S6["6. NDF2W (248.7k/90d) LAST, by tier"]:::s
  S6 --> S7["7. Sharia (separate engine)"]:::s
  S7 --> S8["8. Drain in-flight Camunda instances<br/>plus a terminal sweep for the parked tail"]:::s
  S8 --> S9["9. Decommission ms-bpm + its Cloud SQL"]:::s
```

Two ordering rules, both from evidence already in this repository:

- **Lowest volume and highest existing coverage first.** DF4W is already on the unified spine with config-gated activities. RO is small enough to absorb a mistake. NDF2W is 73% of the book, so it must go last.
- **Reliability and legibility before volume.** Moving the retail book onto LORA before step 2 completes would multiply a measured defect rate by roughly 3×. It would also do that while the people operating it still lack the readiness index.

**This sequence is also its own off-ramp.** Steps 1 to 4 are inventory, remediation, DF4W coverage and a shadow run. They cost about 12–20 engineer-months. They answer one question to a *decision-grade* standard: does LORA actually absorb a Bravo product cleanly? They answer it on 5.5% of volume, without committing the retail book. If the answer is no, the work still leaves LORA measurably better and Bravo untouched.

---

## 6. The reliability prerequisite

LORA's own production findings are the strongest argument for sequencing Option 3 carefully. They come from the LORA team's measurements.

| Finding | Measured | Consequence for a retail-book cutover |
|---|---|---|
| **About half of all loans never reach a terminal state** | `SetTermination` requires terminal status **and** plate released **and** BPKB state; a licence-plate reservation renews itself, so the workflow never ends | Workflow versions can never be retired; 5 idle worker versions hold 82 cores / 154 GB. At 3× volume this compounds |
| Uncapped retries, no terminal-error class | `MaximumAttempts: 0`, zero `NewNonRetryableApplicationError`; ~50,000 4xx/week retried as transient; 4xx outnumber 5xx 111:1 | 47 loans wedged per 7-day window, one at attempt 1,890; **20–25 permanent wedges/month** at 171k applications |
| Undesigned dead-letter path | 1,269 force-cancel and ~705 rewind tickets Jan–Aug 2026; ops re-originates from event 1 | Bravo's operators today have `ApplicationErrorTracking` plus `setJobRetries`. They would be moving to a *worse* operator surface — though **not to a busier one**: measured on the same OTRS queue over the same months, Bravo generates 2,514 stuck-application tickets to LORA's 1,453, at ≈0.39% of applications against ≈0.13% ([ticket-analysis.md](production-findings/ticket-analysis.md)) |
| No per-family observability | 6 of 7 product families have no production APM presence; Temporal has **0 search attributes** | "Which loans are stuck at survey?" is a SQL `WHERE` clause on Bravo today. It is not answerable on LORA without APM |
| Testing | Nightly red for 5 weeks; `lora-super-test` has no CI runner; 4 repos at zero tests; product policy is not a merge gate | Parity for 16 NDF2W risk-tier configurations cannot be proven by a suite that does not run |

**One counterweight, added 2026-09-10.** Every row above is a LORA defect, so the table reads as a list of reasons to hesitate. The OTRS export supplies the comparison that was missing.

On the only symmetric measurement in the pack, **LORA is the more reliable platform per application today.** About 99.87% of its applications complete with no support ticket, against Bravo's ≈99.56%. Over eight months LORA's ticket load fell by a third while Bravo's rose 82% against falling volume ([ticket-analysis.md](production-findings/ticket-analysis.md)).

Three things qualify that. Both figures rest on the billing sheet's disputed application counts. Bravo's excludes silent operator-console recoveries. And the gap turns on one unexplained Bravo category. So this corrects the framing. It is not a licence to skip the gates below. The reliability prerequisite is about *specific defect classes that would compound at 3× volume*. It is not a claim that LORA is the shakier system.

None of these is an argument against Option 3 in principle. They are all arguments for one thing: make "green nightly, bounded retries, terminal statuses, wedge console, readiness index" the entry gate to each cutover wave. Read the current defect rate as a statement about LORA's *maturity*, not about GSM or Temporal. Bravo's equivalents took four years to reach their current state (§7 of [compare.md](compare-architecture.md)).

---

## 7. Cost after the migration

| Line | Change |
|---|---|
| `ms-bpm` pods + `prod-postgres-bpm-d2bpm` | **−≈Rp58M/month** prod; **−≈Rp70–100M/month** including SIT/UAT and Sharia copies |
| LORA marginal cost of Bravo's volume | **≈zero.** LORA went +23% Temporal-metered volume for +3% spend Jun→Aug; it pays for provisioned capacity, not work done |
| Second platform's staffing and on-call | Retires. Not in any GCP line, and plausibly the largest saving |
| Cloud Logging on the Bravo estate | Partially retires. `ms-bpm` logs full Feign request bodies (`loggerLevel: full`) into a Rp140.5M/month prod logging line |

**What does not retire. This correction matters.** [compare.md §3.12](compare-architecture.md) withdrew the earlier claim that retiring Bravo saves about Rp1.6B a month. Most of the Bravo estate is the shared BFI data plane, and **LORA's 301 gateway proxies call it too**. That includes Cloud SQL at Rp584M, the roughly 26 `ms-*` data-plane services with about 50 Cloud SQL instances, Memorystore and Keycloak. All of it stays. Only the LOS tier retires.

**And on a like-for-like tier, LORA is the more expensive platform today**: ≈Rp2,500–3,200 per application against Bravo's ≈Rp490–515. So unit cost does not justify Option 3. Its financial case is *not running two loan origination systems*, plus LORA's near-zero marginal cost as volume grows. That case gets much stronger if LORA does its own right-sizing. Retiring the five idle worker versions alone is worth ≈Rp63M a month, which is more than the entire Bravo LOS tier.

---

## 8. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Bravo must stay running and secure throughout** | **Medium** *(was High)* | 15–24 months on an unpatched engine with a proven RCE path is not survivable on its own — but since the fork correction, [option-1.md](option-1.md) closes the *unpatched-engine* half for **18–33 engineer-days** with no licence, landing Bravo on a supported engine and Spring Boot for the duration. **The other half is not closed by any option here:** the RCE was reached with a valid credential, so rotating `INTERNAL_SERVICE_KEY`, moving to per-caller secrets and registering a `ProcessEngineAuthenticationFilter` are separate work that every option needs ([SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md)). Days, not months — but do not assume the fork carries it. This risk is now cheaply mitigated rather than structural |
| **Camunda cannot be retired by waiting** | Medium–High | **96 `userTask` elements across 26 of the 53 BPMN files** mean in-flight instances park on human action indefinitely ([Camunda 7 Exit Plan](production-findings/Camunda%207%20Exit%20Plan.pdf)). A residue will never complete on its own, so the final decommission needs an explicit force-complete/cancel sweep, and the two-platform period lasts until that sweep runs |
| Coverage gap is unmeasured | High | The gap inventory is the first workstream and gates the rest of the estimate |
| Moving 94% of the book onto a platform with a measured wedge rate | High | §6 remediation as an entry gate per wave |
| Silent parity failure | High | The config-skip trap: an unconfigured activity no-ops rather than failing. Shadow-run diffing on decisions, statuses, assignments and documents; a "fail loud on missing config" guard |
| **Paradigm adoption cost across the organisation** | Medium–High | §3. Mostly remediable with a generated readiness index, a week-1 curriculum and ADRs — but unremediated today, and the team-ownership seam is structural |
| NDF2W volume shock | High | Last, by risk tier, with the legacy path kept warm for rollback |
| Loss of relational fleet queries and reprocess generations | Medium | Decide deliberately what replaces them — [compare.md §6](compare-architecture.md) lesson 3 |
| Sharia runs in its own engine | Medium | Scope separately; it was not in the 90-day sample |
| Single-vendor concentration | Low–Medium | All BFI origination would depend on Temporal Cloud and ArangoDB contracts |

---

## 9. When Option 3 is the right answer

It is the right answer under two conditions. First, BFI intends to run **one** loan origination system. Second, BFI judges that the capability GSM buys is worth its price. That capability is adding an automated step without editing an orchestration model, validated in production at 172 activities. Its price is the adoption cost in §3 and the maturity gap in §6.

The honest qualifications, stated so they are not discovered later:

- It does **not** answer the end-of-support finding by itself. Fifteen to twenty-four months of Bravo runtime still has to be made safe. That is now cheap, though: [option-1.md](option-1.md) Path B lands a supported engine and Spring Boot in 18–33 engineer-days with no licence. So the bridge is a small line item, not a strategic constraint.
- It should **not** start with the retail book. It should start with a gap inventory, the paradigm remediation and the reliability work, and prove itself on DF4W.
- Its cost case is "stop running two platforms", not "LORA is cheaper per loan". On a like-for-like tier it is not, today.
- The paradigm objection is real. It is mostly fixable, and fixing it is cheap. But nobody has done it. A migration decision that assumes it away will meet it at full strength during cutover.

---

## Sources

- [Current LORA challenges in Production](../../lora-workspace/docs/production-findings/Current%20LORA%20challenges%20in%20Production.md) — the paradigm and training complaints, verbatim
- [people.md](../../lora-workspace/docs/production-findings/people.md) — LORA's own verdicts on those complaints
- [workflow-gap.md §8](workflow-gap.md) — production volumes by root definition and product, per-product configuration, human-task queues
- [compare.md](compare-architecture.md) — like-for-like cost tiers, capability comparison, what each platform did better
- [bravo-unified-legacy-to-unified.md](bravo-unified-legacy-to-unified.md) — the migration method and its risks, at a smaller scale
- [LORA production findings](../../lora-workspace/docs/production-findings/) — reliability, cost, testing, delivery
- `squads/Scoring and Underwriting/bravo-bpm-service` at `2d5d856` — code counts
