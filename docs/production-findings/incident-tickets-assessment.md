**Source:** Jira project PRD (board 116), every ticket created 1 Jan – 28 Oct 2026 (1,014 tickets, 301 days, 215 working days). The war-room Google Chat space *war-room-production-issue* is a bot feed of the same PRD tickets, so it adds no extra tickets. Pulled 29 Oct 2026. The ticket-level result is attached as `prd-2026-classified.csv`.

**Earlier analysis:** [Incident priorities 2026](https://bfifinance.atlassian.net/wiki/pages/viewpage.action?pageId=2822799414) (6 Oct 2026, 873 tickets). This page extends it to 28 Oct and adds the systemic/glitch split.

## 1. Summary

- On average, PRD gets **3.4 tickets per calendar day** (4.7 per working day). Most are P1 and P2.
- **P4 and P5 do not exist.** The Severity field (Severity_Prod) has only four values: P0, P1, P2, P3.
- The rate is going up. In the last 30 days it was **6.5 tickets per day**, almost double the year average.
- **65% of tickets are systemic.** The same failure comes back, or the cause is a defect in code or requirements. The systemic share went from 57% in January to 75% in October.
- The biggest group is **systemic + dev process (QA)**: 443 tickets, 1.5 per day. Most of them are Confins R3 journal, prepaid/allocation and payment defects.
- P0 tickets are different. Most P0s are **infrastructure glitches** (network, connection pool, server down): 16 of 44.

## 2. Average tickets per day, by severity

Period: 1 Jan – 28 Oct 2026. Today (29 Oct) is not counted because the day is not complete.

| Severity | Tickets | Per calendar day | Per working day | Last 30 days, per day |
|---|---:|---:|---:|---:|
| P0 – Critical | 44 | 0.15 | 0.20 | 0.13 |
| P1 – High | 387 | 1.29 | 1.80 | 2.37 |
| P2 – Medium | 524 | 1.74 | 2.44 | 4.00 |
| P3 – Low | 59 | 0.20 | 0.27 | 0.00 |
| P4 | 0 | 0 | 0 | 0 |
| P5 | 0 | 0 | 0 | 0 |
| **Total** | **1,014** | **3.37** | **4.72** | **6.50** |

How to read it:

- One P0 every **7 days** on average. One P1 almost every working day, often two.
- 61 tickets (6%) were raised on Saturday or Sunday. 72 days had no ticket.
- The busiest days had 14–15 tickets (26 Aug, 30 Sep, 6 Oct, 21 Oct).

### 2.1 Per month

| Month | Tickets | Per day | P0/day | P1/day | P2/day | P3/day |
|---|---:|---:|---:|---:|---:|---:|
| Jan | 95 | 3.06 | 0.29 | 1.06 | 1.06 | 0.65 |
| Feb | 113 | 4.04 | 0.36 | 1.21 | 1.89 | 0.57 |
| Mar | 64 | 2.06 | 0.23 | 0.90 | 0.81 | 0.13 |
| Apr | 68 | 2.27 | 0.23 | 1.00 | 0.90 | 0.13 |
| May | 43 | 1.39 | 0.10 | 0.58 | 0.61 | 0.10 |
| Jun | 68 | 2.27 | 0.00 | 0.70 | 1.50 | 0.07 |
| Jul | 88 | 2.84 | 0.03 | 1.00 | 1.61 | 0.19 |
| Aug | 139 | 4.48 | 0.06 | 2.00 | 2.39 | 0.03 |
| Sep | 166 | 5.53 | 0.03 | 2.23 | 3.17 | 0.10 |
| Oct (1–28) | 170 | 6.07 | 0.14 | 2.25 | 3.68 | 0.00 |

Two things changed in the second half of the year:

1. **Volume tripled from May to October.** The rise starts in August, with the R1 → R3 contract migration. 266 tickets carry the "(R3)" tag in the summary.
2. **The severity mix changed.** P0 fell from 0.3 per day (Jan–Feb) to almost zero (Jun–Sep). P3 almost disappeared after June. This looks like a change in how severity is chosen, not only a change in real impact. Compare months with care.

## 3. Systemic or glitch

### 3.1 Definitions

- **Systemic:** the cause is in the system or the way of working. The ticket comes back until someone changes code, requirements, release steps, data flows or capacity. A fix of one record does not stop it.
- **Glitch:** an isolated event. It does not repeat, or it was transient (network blip, one restart, one bad input). One retry, restart or data correction closes it.

Subgroups (the cause that let the ticket happen):

- **Infra:** network, server, database capacity, connection pool, CPU/memory, gateway, certificates, vendor platform availability.
- **Dev process (QA):** a defect that testing should have caught. Wrong logic, missed error handling, missing or wrong requirements, known bugs.
- **Release process:** the problem came with a change in production. Deployment, upgrade, configuration not promoted, R1 → R3 migration cutover.
- **Data problem:** wrong, missing, duplicate or out-of-sync data, where the data itself needs a fix.

### 3.2 Result

| Group | Subgroup | Tickets | Share | Per day | P0 | P1 | P2 | P3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **Systemic** | Dev process (QA) | 443 | 43.7% | 1.47 | 11 | 211 | 196 | 25 |
| | Release process | 85 | 8.4% | 0.28 | 3 | 40 | 40 | 2 |
| | Data problem | 88 | 8.7% | 0.29 | 2 | 31 | 50 | 5 |
| | Infra | 43 | 4.2% | 0.14 | 6 | 17 | 17 | 3 |
| | **Systemic total** | **659** | **65.0%** | **2.19** | **22** | **299** | **303** | **35** |
| **Glitch** | Dev process (QA) | 157 | 15.5% | 0.52 | 4 | 33 | 106 | 14 |
| | Release process | 25 | 2.5% | 0.08 | 1 | 10 | 14 | 0 |
| | Data problem | 100 | 9.9% | 0.33 | 1 | 25 | 66 | 8 |
| | Infra | 61 | 6.0% | 0.20 | 16 | 20 | 25 | 0 |
| | Not a defect (invalid) | 12 | 1.2% | 0.04 | 0 | 0 | 10 | 2 |
| | **Glitch total** | **355** | **35.0%** | **1.18** | **22** | **88** | **221** | **24** |
| **All** | | **1,014** | **100%** | **3.37** | **44** | **387** | **524** | **59** |

Systemic share per month: Jan 57%, Feb 58%, Mar 75%, Apr 53%, May 60%, Jun 62%, Jul 58%, **Aug 71%, Sep 66%, Oct 75%**.

### 3.3 What is inside each group

**Systemic – dev process (QA), 443 tickets.** This is the main problem. The same failure modes repeat every month:

| Application | Failure mode | Tickets (systemic) |
|---|---|---:|
| Confins R3 | Journal not formed or wrong (AMGD, NAR, PRV, ETM, RESTRUCTURE, PLC…) | 115 (all subgroups) |
| Confins R3 | Prepaid, allocation, pocket, waive, ERT, settlement | 48 |
| Confins R3 | Camunda / workflow stuck | 46 |
| Confins R3 | Payment receive, posting, reversal | 46 |
| LMS System | Payment receive, posting, reversal | 37 |
| Confins R3 | Status out of sync between CMS, LMS and R3 | 27 |
| Payment Point | Transaction not posted / double allocated | 23 |

Examples: PRD-6660 *LORA – Cannot Golive* (P1), PRD-6849 *Journal not balance RESTRUCTURE* (7 near-identical tickets), PRD-6700 *Gagal prepaid settlement* (5 tickets). The war-room feed for 28–29 Oct shows the same pattern: 11 of 16 new tickets (PRD-7767 to PRD-7782) are Confins R3, and 8 of them are prepaid, ERT, journal or WO-payment logic.

**Systemic – release process, 85 tickets.** Problems that came with a change. Examples: PRD-7203 *EOD R3 Error (after deploy Phase 2)* (P0), PRD-7674 *Redis version carried in a deployment*, PRD-7405 *PP BCA double allocate – impact of deployment*, PRD-7350 *Duplicate data after R3 migration*, PRD-7692 *Camunda not accessible after Redis upgrade*. 220 of the 266 "(R3)" tickets are systemic.

**Systemic – data problem, 88 tickets.** Repeated data fixes for the same flows: Camunda instances that need manual push (15), journals that need manual data (12), prepaid/allocation corrections (8), CMS–LMS status sync (8).

**Systemic – infra, 43 tickets.** Repeated capacity limits: PRD-6741 *High CPU Collect DB1*, PRD-7746 *EOD Error Out of Shared Memory* (P0), PRD-7690 *Golive R3 failed – Redis BusinessDt* (P0), WebCore server restarts (Confins R1, 3 tickets), CMS Juristech DB2DB inbound delay (5).

**Glitch – infra, 61 tickets.** These carry most of the P0s (16). Examples: PRD-6678 *WLC network* (P0), PRD-6679 *LMS Core max JDBC connection* (P0), PRD-7669 *ISP backbone issue* (P0), PRD-6789 *Gerai dan Pos down*. Each one was short, but several look alike (network and connection pool). If they repeat, they move to systemic.

**Glitch – dev process (QA), 157 tickets.** One-off defects with no repeat this year. Many are LORA (18), LMS (11) and Confins R3 (11). Example: PRD-6675 *LORA failed upload image of STNK* (P0).

**Glitch – data problem, 100 tickets.** One-off data corrections. Example: PRD-6672 *MyBRO DWH ETL stuck*, PRD-6998 *Inventory date NULL*.

**Glitch – release process, 25 tickets.** One-off change problems. Example: PRD-6793 *CNV – GKE update impact* (P0).

## 4. What this means

1. **Most tickets are not bad luck.** Two of three tickets come back until the cause is fixed. Closing a ticket with a data patch does not reduce the rate.
2. **Confins R3 alone is 338 of the 659 systemic tickets (51%).** Its journal, prepaid/allocation, Camunda and payment flows need defect fixes and regression tests, not more manual support.
3. **Testing is the weakest control.** Dev process (QA) is 59% of all tickets (600 of 1,014). The same failure modes reach production again and again.
4. **Release control matters for the worst incidents.** Release-process tickets are only 11%, but they include P0 EOD failures and the R3 migration side effects.
5. **P0 is mostly infrastructure.** 22 of 44 P0s are infra (16 glitch + 6 systemic). Network and database capacity are the P0 risk.

## 5. Suggested next steps

1. **Problem tickets for the top 7 systemic failure modes** in section 3.3. One owner each, a root-cause fix and a regression test. Link the PRD tickets to the problem ticket (the Jira "Problem/Incident" link type exists but is not used).
2. **Make the PRD form record the cause.** The Root Cause field (cf 10178) is empty on every 2026 ticket. The cause is only free text in the description, and many say "masih dicari tau". Add a required "Systemic / Glitch" field and a required "Cause subgroup" field at close.
3. **Link each PRD ticket to the release that caused it** (if any). Without this link, release-process tickets are undercounted (see section 6).
4. **Fix the severity scale.** Remove P4/P5 from any guideline, or add them to the field. Write down what P0–P3 mean, because the mix changed a lot after June.
5. **Track this page monthly:** tickets per day per severity and the systemic share. Target: systemic share below 50%.

## 6. Method and limits

- **Data:** Jira REST search `project = PRD AND created >= "2026-01-01"`, 1,019 tickets on 29 Oct 2026, 1,014 up to 28 Oct. Severity is the field *Severity_Prod* (cf 10655), not *Priority* (Priority is "Medium" on almost every ticket).
- **Classification is rule-based**, not a manual review of every ticket. Inputs: Root Cause Category (cf 10225), Impact Area (cf 12031), the summary, and the "Root Cause" text in the description.
  - *Systemic* if any of: ≥3 near-identical summaries in the same application; ≥5 tickets with the same failure mode in the same application; a defect category (Missed on Development, Missed Error Handling, Missing/Incorrect Requirements, Known Issues/Bugs); Impact Area "Issue Migrasi"; or root-cause text that names logic, calculation or many records.
  - *Glitch* otherwise, or if the category is "Invalid Issues", or if the root cause says retry, restart, intermittent or user input.
  - *Subgroup* in this order: infra (infra/network/database category or infra words such as high CPU, down, connection pool, network) → release (Issue Migrasi, Configuration Issue, or deploy/upgrade/cutover/migration words) → data (Data Issues category) → dev process (all defect and functionality categories, and the rest).
- **Accuracy:** a hand check of 36 random tickets agreed with the rules on about 31 (≈85%). Treat each cell as ±15%. The totals and the direction are reliable. Single tickets may be in the wrong cell. Check the CSV before quoting one ticket.
- **Release process is probably undercounted.** Tickets only say "after deploy" when the reporter knows. No PRD ticket is linked to a release or change record.
- **"Recurring" is measured inside 2026 only.** A failure mode that also happened in 2025 but only once in 2026 counts as a glitch.
