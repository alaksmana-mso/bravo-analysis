# Proposal to IT Production: a ticket model that shows the patterns

**For the IT Production and Tech Availability Service team. 6 October 2026.**

**Why this exists.** The CTO asked which area to improve first. Answering took a full export of 873 PRD tickets, 44 post-mortem pages read one by one, and a hand-built classification, because the ticket data cannot answer the question on its own. This proposal changes the ticket model so that the same answer comes out of a Jira dashboard every month, with no manual work.

**What it is based on.** The current PRD field set (read on 6 Oct 2026), the 2026 tickets, and the post-mortems. Companion document: [incident-priorities-2026.md](incident-priorities-2026.md).

---

## 1. What the current tickets cannot tell us

The questions a CTO or a squad lead asks, and whether PRD can answer them today.

| Question | Can PRD answer it today? | Why not |
|---|---|---|
| Which platform area produces the severe incidents? | Partly | Application Name has 30+ values and no grouping. One ticket titled "LMS Core - Max Usage JDBC Connection" is tagged "Agent Tools". 14 tickets carry two applications. |
| What caused them? | No | Root Cause Category is "Functionality Issue" on 260 of 873 tickets. The structured Root Cause field (customfield_10178) is empty on every 2026 ticket. The cause text lives only inside the description, written by a form. |
| Was it caused by a change we made? | No | Only a label, "ImpactDeployment", on 24 tickets. Title search finds 37. The post-mortems show 13 of 44 incidents were change-induced. |
| How was it detected? | No | "Sumber Pelaporan: alert / other" is a line of description text. The "Monitoring" label is on 149 tickets and means roughly the same thing. Neither is a field. |
| How long did it take to detect and to restore service? | No | Only Created and Resolved exist. The SLA fields "Incident - E2E - Time to Response / Dispatching / Resolution" exist in the project and are null on every ticket. |
| Is this a repeat? | No | Link types "Problem/Incident" (is caused by) and "Post-Incident Reviews" exist in the instance and are not used. GW01 went down five times as five unrelated tickets. |
| Which squad owns the fix? | 31% | Squad Fixing is empty on 605 of 873. 371 of those carry the squad as a label instead. |
| Is the vendor working on it? | Partly | The "JIRA ADINS" field is filled on roughly 50 tickets with a helpdesk.ad-ins.com link. Good practice, not yet mandatory. |
| Does a post-mortem exist? | No | No link from a ticket to its Confluence page. At least 11 of 41 P0 tickets have no page. |
| How many contracts or how much money was affected? | No | Business Impact is a paragraph, empty or "-" on 278 tickets. No number field. |

Other signs that the model has drifted:

- Jira **Priority** is "Medium" on 871 of 873 tickets. The real severity is in a custom field called Severity_Prod. Any standard Jira board or filter sorted by priority is meaningless.
- **Impact System** (free text) holds "Database", "PBF(SF)" and "Tidak bisa dilanjut untuk proses" on three consecutive tickets.
- **Related Release Version** holds "2" and "V2.2", which is the version of the intake form, not a release.
- The date in the title differs from the created date on 78 tickets. 30 tickets have no date prefix at all. "20230820" and "20270721" both appear.
- Issue types "Non Bugs" (78), "Alerting" (4) and "Task" (10) never get a Root Cause Category, so 92 tickets fall out of every cause chart.
- The "(R3)" suffix that marks migration tickets is a title convention. It worked for this analysis only because someone typed it 162 times.

None of this is a criticism of the people filling the tickets. The form asks for the right things. It writes them into the description instead of into fields, and the lists it offers do not separate the things we need to count.

---

## 2. Design rules

1. **One ticket is one production incident or defect.** The squad's fix work stays in the squad's own project and is linked. That is already the practice.
2. **Classify with fields, never with labels or title text.** Labels drift. Titles get typed. Fields can be made mandatory and charted.
3. **Five dimensions, each a short closed list.** Where it happened. What kind of ticket it is. How bad it was. Why it happened. How it was found and handled.
4. **Every field feeds one chart.** If no chart in section 6 needs a field, the field goes.
5. **Ask for each fact at the moment it is known.** Where, how bad and how found at creation. Mitigated-at when service is restored. Cause, change-induced, squad and repeat at closure. Nothing is asked twice.

---

## 3. The model

Reuse existing fields wherever one exists. New fields are marked.

### 3.1 Where

| Field | Type | Values | Mandatory | Jira implementation |
|---|---|---|---|---|
| **Platform Area** | single select | 1 CONFINS R3 (AdIns core) · 2 CONFINS R1 (legacy core) · 3 LMS, Payment and Insurance (Bravo) · 4 Origination Bravo (BPM, Agreement, Collateral, Loan Calc, Agency, Surveyor, Onboarding) · 5 Origination LORA · 6 Customer and partner channels (Customer Platform, BFI Mobile, Digital Partnership, Salesforce/PBF, MyBRO/MySIS) · 7 Collection (CMS, Centerix, Juris) · 8 Data platform (DWH, Airflow, Kafka CDC, Autorekon feeds) · 9 Identity and gateway (Keycloak, Apigee, GW01/02, Krakend) · 10 Infrastructure and network (hosts, DB servers, ISP, branch network) · 11 Third-party service (Pefindo, Dukcapil, VIDA, banks, telco) · 12 Corporate applications | At creation | **Use Jira Components.** They are project-level, chart natively, and a component lead can be the default assignee. Today PRD has zero components. |
| Application Name | single select | Existing list, pruned and deduplicated. One value per ticket: the application where the defect is. | At creation | Existing customfield_10979, changed from multi-select to single. The 14 two-value tickets move the second value into Affected services. |
| Affected services | labels-style multi | prod-ms-* and platform names that showed impact | At creation for Incidents | Existing customfield_10086, unused today. Pre-filled from the Datadog alert when the ticket is auto-created. |
| Impact System | free text | retire | | customfield_10082 hidden. Its content is covered by the two fields above. |

### 3.2 What kind

| Issue type | Meaning | Replaces |
|---|---|---|
| **Incident** | Service degraded or down, or a batch at risk, for a period of time | Bug (when it was an outage), Alerting |
| **Defect** | Wrong behaviour or wrong data with no outage. Found by a user, a reconciliation or a report | Bug (when it was not an outage), Non Bugs |
| **Service request** | Data fix, manual job, restart, access change | Task, part of Non Bugs |
| **Problem** | A recurring cause that owns two or more Incidents or Defects. Closed only when the cause is removed | New. Examples that exist today: GW01 outages, Agreement DB pool exhaustion, EOD R3 failures, CMS inbound delays |
| Alert | Auto-created from monitoring. Converts to Incident when confirmed, or closes as "No impact" | Alerting, kept for automation |

Incidents and Defects link to their Problem with the existing link type "is caused by". That single rule is what makes the repeat view in section 6 possible.

### 3.3 How bad

| Field | Type | Values | Mandatory | Jira implementation |
|---|---|---|---|---|
| Severity | single select | P0 Critical · P1 High · P2 Medium · P3 Low, with the written criteria below | At creation, re-checked at closure | Existing customfield_10655 Severity_Prod. Add an automation that copies it into Jira Priority so boards and standard filters work. |
| **Business impact type** | multi select | Transactions failed · Money mis-posted or mis-calculated · Customer-facing outage · Internal users blocked · Reporting or regulatory · Data quality only · None | At closure | New |
| **Contracts or transactions affected** | number | | At closure for P0, P1 and any money impact | New. Replaces guessing from paragraphs. |
| **Amount affected (IDR)** | number | | When Business impact type includes money | New |
| Business Impact | paragraph | narrative | Optional | Existing customfield_10457 |

Severity criteria to publish with the field, so that P1 means the same thing in January and September:

| Severity | Criteria |
|---|---|
| P0 | A core flow is down for all users (origination, payment, disbursement, collection start, EOD/EOM), or money is leaving or being booked wrongly right now |
| P1 | A major function is down for a region or a channel, a batch is late past its window, or a defect affects more than 100 contracts |
| P2 | A function is impaired but a workaround exists, or a defect affects fewer than 100 contracts |
| P3 | Cosmetic, single user, or no business effect |

### 3.4 Why

| Field | Type | Values | Mandatory | Jira implementation |
|---|---|---|---|---|
| **Cause category** | single select | 1 Code defect (logic) · 2 Requirement or design gap · 3 Data or master-data issue · 4 Configuration or environment drift · 5 Change or deployment regression · 6 Capacity or resource exhaustion (pool, CPU, memory, disk) · 7 Infrastructure or network hardware · 8 Batch, scheduling or orchestration · 9 Third-party or vendor service · 10 Security control · 11 Not yet known | At closure. "Not yet known" blocks Done for P0 and P1 | Existing customfield_10225 with a new option list. Old options retired: Functionality Issue, Application Issue, Known Issues/Bugs, Missed on Development, Missed Error Handling, the three "Missing/Incorrect Requirements" variants, Invalid Issues. |
| **Change-induced?** | yes / no | | At closure | New. Yes when the trigger was a deployment, a migration wave, an infrastructure change, a configuration change or a manual data change. |
| **Change reference** | text or link | Release tag, change request, migration wave name | When Change-induced = yes | Repurpose customfield_10516 Related Release Version, which is misused today |
| **Escaped from** | single select | Requirements · Development · QA or UAT · Vendor delivery · Migration · Operations | At closure for Defects and for change-induced Incidents | New. Replaces "Missed on Development" with a value that names the gate that let it through. |
| Root Cause | paragraph | one paragraph, the cause and not the fix | At closure for P0 and P1 | Existing customfield_10178. Empty on every 2026 ticket because the form writes into the description. Point the form at the field. |
| Workaround | paragraph | | When a temporary solution exists | Existing customfield_10179, unused |
| Repeat of | issue link | "is caused by" → Problem, or "relates to" → earlier Incident | Asked at closure: "Have we seen this before?" | Existing link types. Rule: the second occurrence of the same cause creates a Problem ticket. |

Each Cause category maps to exactly one improvement area in the priorities report: 1 and 2 to delivery quality, 3 to data, 4 and 5 to change control, 6 and 7 to platform capacity and resilience, 8 to batch, 9 to third parties, 10 to security. That is what turns a ticket count into a priority list.

### 3.5 How it was found and handled

| Field | Type | Values | Mandatory | Jira implementation |
|---|---|---|---|---|
| **Detection source** | single select | Monitoring alert · Business reconciliation or report · User or branch report · Vendor or partner told us · Internal team noticed · Post-deployment check | At creation | New. Replaces the description line "Sumber Pelaporan" and the "Monitoring" label. |
| **Started at** | date-time | When the impact began, from the alert or the best estimate | At creation for Incidents | New |
| **Detected at** | date-time | When we knew | At creation | New. Defaults to Created. |
| **Mitigated at** | date-time | Service restored or workaround in place | On entering the Mitigated status | New, stamped by automation |
| Resolved | date-time | Permanent fix in production | On Done | Existing |
| Squad Fixing | multi select | Existing list | On entering "Escalation to Squad" | Existing customfield_11044, made mandatory on the transition |
| Vendor ticket | URL | | When Squad Fixing is an AdIns squad or Cause category is Third-party | Existing customfield_11473 JIRA ADINS, generalised |
| Fix ticket | issue link | the squad project issue | On entering "Escalation to Squad" | Existing "relates to" |
| **Post-mortem page** | URL | Confluence page | For every P0, and every P1 longer than 60 minutes, within 5 working days | New, or the existing "Post-Incident Reviews" link type if the review is a Jira issue |

From these four timestamps the dashboard derives time to detect, time to mitigate and time to resolve. Today only the last one exists.

---

## 4. Workflow

Today: Backlog → In Progress Task Production → Escalation to Squad → PAT → Done, plus "[BU] Todo". There is no state that says "service is back" and no state that says "we know why".

Proposed:

| Status | Meaning | Gate to leave it |
|---|---|---|
| New | Created by a person or an alert | Platform Area, Application, Severity, Detection source set |
| Triage | L1 confirming impact and scope | Affected services set; Alert converted to Incident or closed |
| Mitigating | Service still impaired | |
| Mitigated | Service restored or workaround in place; cause not yet known | Mitigated at stamped automatically |
| Root cause analysis | | Cause category not "Not yet known"; Root Cause filled for P0/P1 |
| Fix in progress | With the squad or vendor | Squad Fixing and Fix ticket or Vendor ticket set |
| Fix in verification | Today's PAT | |
| Done | | Change-induced answered; repeat question answered; Business impact type set; post-mortem link present for P0 and long P1 |
| Closed, no action | Resolution "Not an issue" or "Duplicate" | Replaces the "Invalid Issues" cause category |

Defects and Service requests skip Mitigating and Mitigated. Problems have their own short workflow: Open → Cause confirmed → Fix planned → Fix deployed → Closed, and they stay open across months.

Automation rules worth setting up on day one:

- Datadog alert creates an Alert with Detection source = Monitoring alert, Started at = alert time, Affected services from the alert tags.
- Entering Mitigated stamps Mitigated at. Entering Done refuses if the closure gates are not met.
- Five working days after a P0 reaches Mitigated with no Post-mortem page, the ticket is flagged and the Tech Availability lead is mentioned.
- Second Incident linked "relates to" an earlier one with the same Cause category and Application prompts for a Problem.

---

## 5. Naming, labels and clean-up

**Summary line.** `YYYYMMDD - <Application> - <symptom in six to ten words>`. The date is the incident start, not the ticket creation. No suffixes. The "(R3)" suffix becomes a label in the programme family below, and Change-induced = yes with Change reference = the wave name.

**Labels** are for programmes and campaigns only, where a ticket needs to be found across projects: `r3-migration`, `df2w-release`, `pentest-2026`. Never for squad, cause, source or severity. Those are fields.

**Clean-up of 2026 data**, so the first monthly review has a baseline:

| Today | Becomes | How |
|---|---|---|
| Squad labels on 371 tickets with empty Squad Fixing | Squad Fixing | Bulk edit by label |
| "Monitoring" label (149) | Detection source = Monitoring alert | Bulk edit |
| "ImpactDeployment" label (24) and the 37 title matches | Change-induced = yes | Bulk edit, then review |
| "(R3)" suffix (162) | label `r3-migration`, Change-induced = yes, Change reference = wave | Bulk edit by title |
| Root Cause Category old values | new Cause category | Mapping table, then a two-day review of the 374 P0 and P1 tickets using the data file in `incident-priorities-2026-data/` |
| 41 P0 tickets | Post-mortem page link | From the PostMortem_2026 folder; the gaps become the first action list |

---

## 6. The monthly review pack

Each view is one Jira filter or dashboard gadget. The JQL is written against today's field IDs where the field already exists.

| # | View | What it answers | JQL or gadget |
|---|---|---|---|
| 1 | Volume by Platform Area by month | Where is the load going | Two-dimensional filter statistics: component × created month |
| 2 | P0 and P1 by Platform Area | Where is the severe pain | `project = PRD AND cf[10655] in ("CRITICAL (P0)","HIGH (P1)") AND created >= startOfMonth(-1)` grouped by component |
| 3 | Cause category by Platform Area | What to fix in each area | Two-dimensional: component × cf[10225] |
| 4 | Change-induced share | Is change control working | `"Change-induced?" = Yes` as a share of Incidents, trend by month |
| 5 | Detection source and time to detect | Is monitoring catching things before users do | Pie on Detection source; average of Detected at minus Started at |
| 6 | Time to mitigate by severity | Are we restoring faster | Average of Mitigated at minus Started at, grouped by cf[10655] |
| 7 | Repeats | Which causes keep coming back | `issuetype = Problem AND status != Closed` with linked-issue counts, sorted by count |
| 8 | Open past 30 days by squad | What is stuck | `project = PRD AND statusCategory != Done AND created <= -30d` grouped by cf[11044] |
| 9 | Post-mortem coverage | Are we learning | `cf[10655] = "CRITICAL (P0)" AND "Post-mortem page" is EMPTY AND status = Done` should be zero |
| 10 | Vendor queue | Is AdIns inside its SLA | `cf[11473] is not EMPTY AND statusCategory != Done` with age |
| 11 | Money impact this month | What did defects cost | Sum of Amount affected where Business impact type includes money |
| 12 | Migration wave scorecard | Should the next wave go | Tickets with label `r3-migration` by wave, by severity, by Cause category |

Views 1 to 3 and 7 are the priorities report. Views 4 to 6 are the three measures that report proposed for its top three areas. With this model the report is a dashboard, refreshed on the first working day of each month, and the discussion moves from "what happened" to "what are we doing about it".

---

## 7. Rollout

| When | What | Who |
|---|---|---|
| Week 1 | Agree the three lists: Platform Areas, Cause categories, Severity criteria. One hour with the squad leads and AdIns. Freeze them for a quarter. | IT Production lead |
| Week 1 to 2 | Create components, new fields, new issue types, new option list on Root Cause Category. Point the intake form (version 2.2) at the fields instead of the description. | Jira admin with IT Production |
| Week 2 | Automation rules from section 4. Dashboard with the twelve views. | Jira admin |
| Week 3 | Train L1 and the monitoring team on the new creation gates. Switch the Datadog alert integration to the Alert issue type. | Tech Availability Service lead |
| Week 3 to 4 | Back-fill the 2026 P0 and P1 tickets per section 5. | IT Production, two people, two days |
| Month 2 | First monthly review on the dashboard. Retire the old labels and the Impact System field. | IT Production lead with the CTO |
| Quarterly | Fifteen-minute review of the option lists. Add a value only if it would appear in at least five tickets a quarter. | IT Production lead |

Ownership of the taxonomy sits with IT Production. Squads propose; IT Production decides. That keeps the lists short.

---

## 8. What not to do

- Do not add more paragraph fields. Three exist and two are empty.
- Do not create per-squad or per-application custom fields. The squad list and the application list are values, not fields.
- Do not keep "Functionality Issue". It is the answer when nobody wants to choose.
- Do not let labels carry anything that a chart depends on.
- Do not make the full set mandatory at creation. The person opening a ticket at 02:00 knows where and how bad, not why. Ask why at closure.
- Do not run the taxonomy change and the workflow change on different days. Tickets created in between will be in neither model.

---

## Appendix A. Field reference, current state

| Field | ID | Used in 2026 | Proposed |
|---|---|---|---|
| Application Name | customfield_10979 | 872 of 873 | Keep, single-select |
| Severity_Prod | customfield_10655 | 873 | Keep, mirror to Priority |
| Root Cause Category | customfield_10225 | 781 | Keep field, replace options |
| Squad Fixing | customfield_11044 | 268 | Keep, mandatory on escalation |
| Impact Area | customfield_12031 | 261 (since August) | Fold into Cause category and Change-induced |
| Product | customfield_11926 | 467 | Keep |
| Business Impact | customfield_10457 | 595 | Keep as narrative |
| Symptom | customfield_10479 | most | Keep |
| Impact System | customfield_10082 | most, inconsistent | Retire |
| Nomor OTRS | customfield_10458 | 353 | Keep |
| Related Release Version | customfield_10516 | misused | Repurpose as Change reference |
| JIRA ADINS | customfield_11473 | about 50 | Keep as Vendor ticket, mandatory for AdIns squads |
| Root Cause | customfield_10178 | 0 | Use it |
| Workaround | customfield_10179 | 0 | Use it |
| Affected services | customfield_10086 | 0 | Use it |
| Major incident, Incident manager, Responders | 10181, 11996, 10180 | 0 | Use Major incident = P0 flag or remove |
| Incident E2E and Vendor SLA fields | 10335, 10337, 10338, 10339, 10340, 10172 | 0 | Remove, replaced by the four timestamps |
| Components | | 0 | Platform Area |
| Link types Problem/Incident, Post-Incident Reviews | | 0 | Repeat and post-mortem links |

## Appendix B. Mapping old Root Cause Category to the new Cause category

| Old value (2026 count) | New value |
|---|---|
| Functionality Issue (260) | Code defect, unless the ticket text says otherwise; review the P0 and P1 ones by hand |
| Data Issues (165) | Data or master-data issue |
| Application Issue (73) | Code defect or Capacity, by ticket |
| Missing/Incorrect Requirements Technical (69), Functional (8), plain (6), UI Design (2) | Requirement or design gap |
| Missed on Development (60), Missed Error Handling on Development (13) | Code defect, Escaped from = Development |
| Known Issues/Bugs (54) | Code defect, linked to a Problem |
| Infrastructure Issues (33), Network Issue (4) | Infrastructure or network hardware, or Capacity, by ticket |
| Database Issue (7) | Capacity or Data, by ticket |
| Configuration Issue (7) | Configuration or environment drift |
| External Systems Issues (4) | Third-party or vendor service |
| Issue by Security and Non Functionality (3) | Security control or Capacity |
| Access Management Issue (1) | Configuration or environment drift |
| Invalid Issues (12) | Resolution "Not an issue", no cause |
| Empty (92) | Review; most are Non Bugs and Alerting |
