# Where to improve first: what the 2026 production tickets and post-mortems say

**Prepared for the CTO. 6 October 2026.**

**Sources.**

- Jira project PRD (IT Production, board 116). All 873 tickets created 1 Jan to 6 Oct 2026, pulled on 6 Oct 2026 with the structured fields the production team fills in: Application Name, Severity, Root Cause Category, Squad Fixing, Impact Area, Business Impact, Root Cause. Counts for 2025 were pulled for comparison only.
- Confluence space ITPROD, folder PostMortem_2026. All 44 pages, read in full.

**Method.** Tickets are counted as the team recorded them. Each post-mortem was then read and placed into one improvement area by its stated root cause. The area placement is my judgment; the counts, dates, durations and quotes are taken from the pages. Where a page contradicts itself, the appendix says so.

---

## The answer in one page

**The order to work in:**

| # | Area | Why it is in this position |
|---|------|---------------------------|
| 1 | **CONFINS R3 migration and month-end batch stability** | 301 of 873 tickets and 201 of the 374 P0/P1 tickets this year. Volume tripled in August when the R1-to-R3 contract migration started and has not come down. 24 EOD/EOM batch failures, four of them P0. The 8 Sep P0 still has no root cause. 31 tickets open. |
| 2 | **Change and release control** | The largest controllable cause in the post-mortems: 13 of 44 incidents were started by a change we made. It is also the mechanism behind priority 1. The three incidents with the largest money impact this year all trace to a release or data change that reached production untested. |
| 3 | **Platform single points of failure and database capacity** | 16 of 44 post-mortems and 11 of the P0 ones. One on-prem gateway (GW01) went down five times. The Agreement database connection pool was exhausted four times. Each event hit 9 to 19 services at once. Three of the gateway incidents still have no root cause. |
| 4 | **Money-affecting defects that nobody is watching for** | 0% interest contracts ran for four weeks. Split-funding paid the whole amount to the supplier on 26 contracts. 1,918 contracts were under-billed for late charges. 2,850 payments sat unposted. All found by users, none by monitoring. |
| 5 | **The data pipeline that feeds Collection** | Collection started late at least seven mornings this year because Airflow, Kafka CDC or the DB2DB inbound failed. The data team finds it in a chat group, not an alert. |
| 6 | **Third-party dependencies** | Pefindo, Dukcapil, VIDA, Telkom, Grahacom. Eleven tickets and five post-mortems. Detection is fine. There is no fallback and contract or link expiries are not tracked. |
| 0 | **Incident learning discipline (foundation for all of the above)** | 4 of 44 post-mortems have a real why-chain. 8 have no action item. 45 of 84 action items have an owner, 9 are marked done. At least 11 of the 41 P0 tickets have no post-mortem page. 605 of 873 tickets have no squad. The structured Root Cause field is empty on all 873; the cause lives only in the description text. |

**Why this order.** Priority 1 is where the pain is right now and where the next migration wave will add more. Priority 2 is the control that stops priority 1 from repeating and is the top cause we can fix ourselves. Priority 3 has the widest blast radius per event and the most unresolved root causes. Priorities 4 to 6 are real but smaller or less controllable. Priority 0 is cheap and without it the other five cannot be measured.

---

## 1. The numbers

### 1.1 Volume and severity

| Period | Tickets | P0 | P1 | P0+P1 share |
|---|---|---|---|---|
| 2025 full year | 1,260 | 301 P0+P1 | | 24% |
| 2026 Jan to 6 Oct | 873 | 41 | 333 | 43% |

2026 already has more P0/P1 tickets than the whole of 2025, with a quarter of the year left.

| Month 2026 | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct (6 days) |
|---|---|---|---|---|---|---|---|---|---|---|
| All tickets | 95 | 113 | 64 | 68 | 43 | 68 | 88 | **139** | **166** | 29 |
| CONFINS R3 | 15 | 28 | 28 | 25 | 10 | 16 | 26 | **66** | **67** | 20 |
| LMS System | 7 | 9 | 2 | 6 | 3 | 6 | 12 | 18 | **32** | 4 |

January to July averaged 77 tickets a month, below the 2025 average of 105. August and September doubled that. The whole increase is CONFINS R3 and LMS, and almost all of it carries the "(R3)" migration tag: 2 such tickets in June, 7 in July, 65 in August, 78 in September.

### 1.2 Where the severe tickets are

| Application | Tickets | P0+P1 | Share of all P0+P1 |
|---|---|---|---|
| CONFINS R3 | 301 | 201 | 54% |
| LMS System | 99 | 26 | 7% |
| LORA | 65 | 17 | 5% |
| CONFINS R1 | 49 | 12 | 3% |
| MyBRO, Surveyor Platform, CMS Juristech | 19, 18, 14 | 10 each | 8% together |
| Apigee (gateway), Payment Point, Customer Platform | 8, 23, 18 | 8 each | 6% together |

For comparison, CONFINS R3 had 54 tickets in the whole of 2025.

### 1.3 What the team says caused them

| Root Cause Category (as filled in) | Tickets |
|---|---|
| Functionality Issue | 260 |
| Data Issues | 165 |
| Not filled in | 92 |
| Application Issue | 73 |
| Missing or incorrect requirements (technical, functional, UI) | 85 |
| Missed on Development | 60 |
| Known Issues/Bugs | 54 |
| Infrastructure, Database, Network, Configuration | 51 |
| External Systems Issues | 4 |

Read together: about 530 tickets, six in ten, are software defects or requirement gaps. Infrastructure is 6% of tickets. The post-mortems tell the opposite story, because the big outages are infrastructure and change events while the ticket volume is application defects. Both are true and they need different fixes.

### 1.4 Recurring families in the tickets

| Family (matched on ticket title) | Tickets | P0 | P1 |
|---|---|---|---|
| EOD / EOM batch failures (CONFINS R3, one R1) | 24 | 4 | 14 |
| Change, deployment or migration induced | 37 | 6 | 19 |
| Airflow / ETL / DB2DB / BOD delays | 18 | 1 | 12 |
| Connection pool, JDBC, DB CPU, locking | 15 | 4 | 7 |
| Pefindo / Dukcapil / VIDA / SLIK | 11 | 4 | 1 |
| Autorekon | 10 | 1 | 5 |
| Network / ISP / WLC | 9 | 5 | 0 |
| Gateway GW01 / GW02 / Apigee | 6 | 2 | 3 |

### 1.5 Resolution and backlog

| Severity | Median days to resolve | 90th percentile | Resolved |
|---|---|---|---|
| P0 | 3 | 25 | 40 of 41 |
| P1 | 7 | 39 | 313 of 333 |
| P2 | 11 | 55 | 370 of 440 |

95 tickets are open on 6 Oct: 90 in "Escalation to Squad", 5 in "[BU] Todo". 20 open P1 and 1 open P0 (5 Oct, CONFINS R3 Autorekon). 17 have been open more than 60 days, the oldest since 12 Feb. 31 open tickets are CONFINS R3 and 20 are LMS System.

### 1.6 The 44 post-mortems by improvement area

| Area | Post-mortems | P0 | Repeats the page admits | Root cause missing or "suspected" | Found by users, not monitoring |
|---|---|---|---|---|---|
| Change and release control | 13 | 4 | 1 | 0 | 3 |
| Platform SPOF and capacity | 16 | 11 | 2 | 4 | 1 |
| CONFINS R3 batch and vendor defects | 2 | 2 | 0 | 1 | 0 |
| Money-affecting logic defects | 2 | 0 | 0 | 0 | 2 |
| Data pipeline to Collection | 6 | 1 | 1 | 2 | 0 |
| Third-party dependencies | 5 | 4 | 0 | 0 | 1 |

CONFINS R3 has only two post-mortems against 301 tickets and 24 batch failures. Most of its P0s have no page.

---

## 2. Priority 1: CONFINS R3 migration and month-end batch stability

**What the evidence says.**

- 301 tickets, 191 P1 and 10 P0. 105 are about journals, GL, COA or posting. 53 about payment and allocation. 52 about agreement and go-live. 22 about EOD or EOM.
- The jump in August is the R1-to-R3 contract migration. The ticket "Impact Area" field was introduced in August and already shows 27 tickets tagged "Issue Migrasi" and 23 "Issue Workflow". The migrated-contract defects are concrete: double allocation, reversal errors, PSAK values wrong, journals not formed, payment columns dropped, pocket retention not migrated.
- The month-end and daily batch has failed 24 times this year. Four were P0: 1 Mar, 30 Mar, 14 Jul (right after the Phase 2 deployment), 8 Sep. The 8 Sep page says, as of 1 Oct, "the root cause investigation is still in progress by the ADINS Team". Five follow-up actions on that page have no owner, date or ticket. The two newest tickets (3 and 4 Oct) report EOD running slower than before.
- 147 tickets name "Adins - Confins r3" as the fixing squad. The Symptom field on 110 tickets across the project is "-" or empty, and much of that is in this bucket. Resolution for CONFINS R3 tickets runs at a median of 9 days, 90th percentile 46 days.
- Autorekon broke 10 times since June, ending in the P0 of 5 Oct.

**What to improve first.**

1. Gate the next migration wave on a reconciliation pack, not on a go/no-go meeting: journal totals, allocation totals and asset status compared R1 vs R3 for the migrated contracts before the wave is declared done. The August defects are exactly the kind this would catch.
2. Make the batch observable: one dashboard per EOD/EOM step with duration and retry count, and an alert when retries start, not when they are exhausted. Today the 8 Sep failure was noticed when the auto-retry limit was reached.
3. Put a root-cause SLA into the AdIns engagement for P0 and P1, with the clock visible on the ticket. Two of the three CONFINS R3 P0 post-mortems have the vendor's analysis as an attached PDF or "still in progress".
4. Pre-production configuration parity. The 14 Jul EOD P0 was an appsettings mismatch between UAT and production. The page itself asks for "comparing tools untuk memastikan appsetting".

**Measure.** CONFINS R3 P0+P1 tickets per month (201 so far, 94 of them in Aug to Oct), EOD/EOM failures per month (currently 2 to 3), open CONFINS R3 tickets older than 30 days.

---

## 3. Priority 2: change and release control

**What the evidence says.** Thirteen post-mortems start with a change we made. The same pattern repeats with different names:

| Date | What changed | What it broke | Why it got through |
|---|---|---|---|
| 6 Jan (found 29 Jan) | MyBRO/MySIS custom-pricing flag reused for life insurance | Contracts booked at 0% interest for four weeks | Whole squad unaware the flag disables all pricing validation; no revenue check after release |
| 6 Feb | GKE upgrade with Istio reinstall | TLS 1.2/1.3 mismatch to CNV, bureau calls down 6.5 h | GKE auto-upgrade had been off since Sep 2025; no maintenance window; not tested |
| 18 Feb | Encryption key moved to Google KMS | Krakend token validation, eKYC face capture down ~11 h | Dependency impact not assessed; fix waited for PICs until morning |
| 9 Mar | Postgres 13 to 16 upgrade on Agent DB | Agent platform down 6 h, data restored from backup | No query regression test, no rollback path; CPU alert during the upgrade ignored |
| 31 Mar | EOD/EOM CronJob schedule edited | EOM ran at the old time, 17 payments affected | Merged without ArgoCD sync; EOD and EOM share one CronJob |
| 10 Apr | Hibernate 6.6.0.CR1 to 6.6.42 | GOTO payment inserts failed | Core library upgraded without impact analysis |
| 13 May | Unified Platform released big-bang to all branches | Go-live ratio dropped, leads stuck; rollback left mixed data | UAT on mock data; Krakend route not deployed; IAM misconfigured; no pilot |
| 13 to 14 Jul | Phase 2 deployment | EOD R3 P0 and split-funding AP regression (26 contracts, money sent to the wrong party) | UAT did not cover the second core system |
| 20 to 28 Jul | Debezium CDC rolled to production | core-proxy DB died, late charges not billed on 1,918 contracts | DB had gone down twice in UAT on 20 and 28 Jun; rolled out anyway |
| 3 Aug | Cloud Armor rule added after a SOAR alert | Payment Point and H2H blocked 3 h | Security team not in the change loop; nobody checked which IP the rule matched |
| 7 Sep | Sangfor host migration | DB link listener not restarted, tele-collection late | No post-reboot checklist |
| 29 Sep | Manual mapping row added in production under a support ticket | GET agreement returned 500, LMS Core and e-Doc down 37 min | No uniqueness constraint, no validation before the data change |
| 2 Oct | Cherry-pick to release branch | RAL print and inventory status down 2 h | A fix commit was missed; no diff check on the release branch |

Across the tickets, 37 carry the "ImpactDeployment" label or say "after deploy", "migrasi" or "upgrade" in the title: 6 P0, 19 P1.

**What to improve first.**

1. One rule for every production change, including infrastructure, data fixes and security rules: a written impact list, a rollback that has been tried, and a named person watching the success-rate dashboards for the first hour. Three pages in this set end with exactly that lesson ("pastikan semua fitur masih berjalan normal", "monitor post-deployment results", "periodic post-fix monitoring of APM").
2. No release to all branches at once for customer-facing platforms. The 13 May page asks for "release di specific cabang (piloting, jangan bigbang)".
3. UAT and production environments must match in configuration, and UAT must use real integrations where the production dependency is the thing being changed. Two P0s this year were environment drift.
4. A failed test in UAT blocks the rollout. The late-charge incident would not have happened.

**Measure.** Change-induced P0+P1 per month (currently about 3). Share of releases with a recorded rollback test and a post-release watch.

---

## 4. Priority 3: platform single points of failure and database capacity

**What the evidence says.**

- The on-prem gateway `gw.bfi.co.id` (GW01/GW02, Edge Micro behind nginx) went down or degraded on 9 Mar (NIC on host 118), 1 Apr (NIC on VM 114), 21 Apr, 14 May, 18 May, 24 Aug (GW01) and 4 Sep (host 120 I/O error during Sangfor migration, GW02 and NOTIFDB on the same host). Each time 9 to 19 services returned 5xx until someone failed over by hand, 30 to 36 minutes later. The 21 Apr, 14 May and 18 May pages have no root cause. The 24 Aug page offers a "suspected" DNS priority difference between GW01 and GW02. The 14 May page says it recurred; the 18 May page is the third in four weeks.
- The Agreement database is the second single point. Its connection pool was exhausted on 8 Jan (JDBC over 2,500), 1 Apr (over 2,500 again), 24 Aug (as a symptom of the gateway), 22 Sep (Collateral Hikari pool at its 300 limit while a DBA reindex job ran during live traffic). It was locked on 7 Mar by a cron CDC job during business hours. More than ten services depend on it. The recorded fixes are "raise the pool", "add a cron to scale pods in the evening" and "migrate the cron to Airflow".
- Other capacity events of the same shape: lms-ar-be with a maximum of 2 replicas crashing on OOM (15 Jan), the notification DB (19 Jan) taking login down because auth depends on it, a bulk WhatsApp blast saturating the repeat-order DB with no throttle and no kill switch (25 Feb), the anti-fraud DB above 90% CPU with no check on it (7 Apr), the CDB SQL Server hanging while a 10 GB backup ran (12 Feb, root cause still "investigation").
- In the tickets: 15 connection-pool, CPU or locking tickets, 4 of them P0, and the CMS collection DB alone shows "High CPU Collect DB1" on 26 Jan and again on 1 Oct.

**What to improve first.**

1. Find the GW01 root cause and remove the manual failover. Two gateways with a health-checked automatic switch, and the DNS configuration made identical. Until then every unrelated incident on that host becomes a company-wide outage.
2. Give the Agreement database a capacity owner. Separate batch and CDC traffic from online traffic, set a per-service connection budget, and alert on pool usage at 70%, not when it is full. Raising the limit after each incident has been tried four times.
3. Retire the "max replica 2" and "single pod" deployments on the critical path. The 15 Jan page already asks for a resource and utilisation report per deployment.

**Measure.** Gateway incidents per quarter (currently 2 to 3), minutes to fail over (currently 30 plus), Agreement DB pool incidents (currently 1 to 2 per quarter).

---

## 5. Priority 4: money-affecting defects with no business monitoring

**What the evidence says.** The incidents that cost money were not outages. Systems were green.

| Incident | Found after | Found by | Impact as recorded |
|---|---|---|---|
| 0% interest in MyBRO/MySIS | 23 days (6 Jan to 29 Jan report, 2 Feb fix) | A user | "huge monitory cost"; the page still says "X agreements, Y IDR" |
| Split-funding AP not split | Same day, after disbursement | A user | 26 contracts, 19 already paid in full to the supplier |
| Late charge missing in payment info | 2 days | A user | 1,918 contracts could underpay |
| Payment Point not posting to CONFINS | Hours | A user | 2,850 payments in a dead-letter queue, no alert on the queue |
| Autorekon double / not running | Days | Finance | 10 tickets since June, P0 on 5 Oct |

The 0% interest page gives the honest reason: "reliability of detection: Zero. System monitoring saw no error." Its action item, "set up alert for critical revenue related data before application goes live", has no owner and no status.

**What to improve first.** Five daily reconciliation checks with an owner in Finance or Operations: interest rate distribution on new contracts, funding split totals vs agreement, late-charge billed vs due, payments received vs posted, autorekon matched vs unmatched. These are queries, not projects. Each one would have caught one of the incidents above on day one.

**Measure.** Days from first wrong transaction to detection (currently 2 to 23). Number of contracts touched by a money defect per quarter.

---

## 6. Priority 5: the data pipeline that feeds Collection

**What the evidence says.** Collection (CMS, New Centerix, tele and field) cannot start until the DB2DB inbound from the warehouse finishes. That chain broke on 4 Jan (Airflow stopped on one null name), 22 Feb (Airflow deadlock, P0), 7 May (ORG master changed in CMS without telling the data team), 25 Jul, 15 Aug (Kafka node-pool expansion during the R3 migration, 7 hours before SRE was asked), 5 Sep (Kafka connector to CONFINS R3 dropped its slot), 11 Sep (a text value in a numeric column stopped the whole EOD). Eighteen tickets in this family, 12 of them P1.

Every one of these was found by the data team in a WhatsApp group at 00:52, 01:45 or 04:19. None was a monitoring alert. Two of the pages record their duration as "57 minutes" and "13 minutes" while their own timelines show 4 and 1.5 hours.

**What to improve first.** A freshness check on the inbound tables with an alert to the on-call person, a DW EOD checkpoint before 02:00, and a rule that Airflow skips a bad row and reports it instead of stopping the DAG. The 5 Sep page's own action for SRE reads "No action from SRE", which is the gap.

**Measure.** Mornings per month Collection starts late (currently 1 to 3).

---

## 7. Priority 6: third-party dependencies

**What the evidence says.** Pefindo failed three times (12 Feb, 14 Feb, 1 Apr), Dukcapil link suspended by the ISP over a contract date (31 Mar), VIDA degraded twice, Telkom national outages took 159 branch, gerai and POS devices offline (22 Jan) with single-link sites unable to recover, Grahacom trunk down for tele-collection (27 Jul). Eleven tickets, 4 P0.

Detection works here. What is missing is a fallback (queue and retry the bureau call instead of failing the application), a second link at the single-link sites, and an owner for contract and link expiry dates. The Dukcapil page's action was to create a WhatsApp group with the ISP.

**Measure.** Minutes of bureau unavailability per month and the share of those minutes in which applications still progressed.

---

## 8. Priority 0: incident learning discipline

This is the foundation. It is cheap, and without it the five areas above cannot be tracked.

**Post-mortems.** 44 pages this year. 4 contain a why-chain deeper than one line. 8 have no action item at all. Of 84 action items, 45 have an owner, 9 are marked done, and most of the rest sit in the template placeholder ("@ owner", "incomplete"). 4 pages have no root cause (three GW01 outages and the CDB hang). Several pages carry template text ("Duplicate/copy this template", "Kindly update the unfilled field", "e.g., 39 minutes"). Three pages state a duration that contradicts their own timeline. Two squads use their own RCA format with no severity, duration or ticket link. The one complete example in the set, the 28 Jul late-charge page, shows the team can do it: six-step why-chain, dated timeline, seven owned actions, six closed.

**Coverage.** 41 P0 tickets, 44 post-mortem pages, but they do not line up. At least 11 P0 tickets have no page: LORA failed go-live (27 Jan), CONFINS R3 expired-before-effective date (30 Jan), prepaid settlement (12 Mar), ready-to-golive stuck (25 Mar), two Digital Partnership P0s (16 and 17 Apr), S1 scoring stuck (23 May), Autorekon (5 Oct), and others.

**Tickets.** 605 of 873 have no Squad Fixing. 92 have no Root Cause Category, and "Functionality Issue" is used 260 times as a catch-all. The structured Root Cause field is empty on every 2026 ticket; the cause is typed into the description by the intake form, so it cannot be filtered or charted. The Impact Area field was only introduced in August. Resolution is recorded, but not time to detect or time to mitigate. The companion document [prd-ticket-model-proposal.md](prd-ticket-model-proposal.md) proposes the fix.

**What to improve first.**

1. Every P0 and every P1 longer than an hour gets a post-mortem within five working days, in one template, with at least one owned action with a date. A fortnightly 30-minute review of open actions, chaired by one person.
2. Replace "Functionality Issue" with a small fixed list that maps to the six areas above, and make Squad Fixing mandatory at triage.
3. Record detected-at and mitigated-at on the ticket. Those two timestamps are the only way to show whether priorities 3 to 6 are improving.

---

## 9. Caveats

- Ticket categories and severities are as the production team recorded them. Some application tags are wrong on the face of it (a ticket titled "LMS Core - Max Usage JDBC Connection" is tagged "Agent Tools"). The top-line shares would not change if those were fixed.
- 2025 figures are counts only. The field set was different and I did not read 2025 tickets.
- The assignment of post-mortems to areas is mine. Where a page has two causes I placed it by the one that started the chain and noted the second (for example the late-charge incident is a change-control failure whose impact is financial).
- Durations are taken as written. Where a page's timeline disagrees, the longer figure is probably right.
- The post-mortem folder is the only Confluence source read. Squads may keep RCAs elsewhere; those would raise the coverage figure in section 8.
- Nothing here measures what did not become a ticket.

## Appendix: data files

- [`incident-priorities-2026-data/prd-tickets-2026.json`](incident-priorities-2026-data/prd-tickets-2026.json): the 873 PRD tickets with the fields used here (key, summary, status, severity, application, squad, root cause category and text, impact area, business impact, created and resolved dates).
- [`incident-priorities-2026-data/postmortems-2026.json`](incident-priorities-2026-data/postmortems-2026.json): one record per post-mortem page (44) with page ID and URL, date, priority, duration, affected services, root cause as written, contributing factors, detection, action items with owner and status, and quality notes.

Every page in the PostMortem_2026 folder dated 4 Jan to 2 Oct 2026 was read.
