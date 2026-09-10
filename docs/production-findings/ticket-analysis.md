# Production ticket load, Bravo LOS against LORA — the first symmetric reliability measurement

**Source.** [`Compare_LOS_LORA.xlsx`](Compare_LOS_LORA.xlsx), exported 2026-09-09. Five sheets: a monthly summary, a per-category pivot per platform, and the two raw ticket extracts — **5,677 LOS rows** and **4,184 LORA rows**, each `tanggalrequest` / `aplikasi` / `detail`, covering **2026-01-01 to 2026-09-09**. Companion: [`Trend_Tiket_OTRS_LOS(BPM Bravo).pdf`](Trend_Tiket_OTRS_LOS%28BPM%20Bravo%29.pdf).

**Why this matters to the pack.** Every previous document carried the same caveat: *"We do not have Bravo's manual-intervention rate, incident counts or per-activity failure data."* LORA's ≈0.2% intervention rate was measured; Bravo's was a code-level mechanism with no number attached, so the two platforms could not be compared on reliability. This export closes that gap. It is the **first dataset in the pack that measures the same thing, in the same system, over the same window, for both platforms.**

**One correction to how this was framed.** The spreadsheet does **not** contain a manual-intervention rate. It contains *support-ticket counts by category and month*. A rate needs a denominator, and the denominators come from a different source — the GCP billing export's application counts, which the LORA cost document itself calls "the questionable part of the sheet" ([cost.md](../../../lora-workspace/docs/production-findings/cost.md#the-estate-three-months)). Every rate below is therefore a *verified numerator over an unverified denominator*, and is stated as such. The **counts, trends and per-category breakdowns need no denominator and are the strongest part of this document.**

---

## 1. Read this before any number below: the August taxonomy break

Both queues were re-categorised in August 2026. On LORA it is severe enough to invalidate a naive month-on-month reading.

| Platform | Categories with ≥10 tickets in July and **zero** in Aug + Sep | July volume that vanished | New categories in Aug |
|---|---|---|---|
| LOS / Bravo | `Operation Platform - Other Support` | **53** | `Perubahan Branch Booking` (11), `Kendala Jadwal Survey` (13) |
| LORA | `DBP Surveyor - Lainnya` (113), `DBP Customer - Belum terima dana` (72), `DBP Customer - Lainnya` (49), `DBP Surveyor - Whatsapp chat` (14) | **248** | `Operation - System & Platform Issue` (25), `Funding & Disbursement` (15), `Cancellation Request` (5) |

LORA's headline total falls 460 → 273 between July and August. **The drop is 187; the volume of categories that disappeared is 248.** The entire apparent improvement is accounted for by four ticket streams leaving the queue — three of them the customer-facing and WhatsApp channels, which have no Bravo counterpart at all. Nothing in this export supports the reading "LORA's ticket load halved in August."

**Consequence for this document:** August LORA totals are treated as a floor, not a measurement; Jun–Jul is the clean comparison window; and §3 re-runs the series on a stable-category basis.

---

## 2. Monthly totals as exported

| Month | LOS (Bravo) | LORA | LORA, platform-scope¹ |
|---|---|---|---|
| 2026-01 | 458 | 596 | 454 |
| 2026-02 | 591 | 426 | 336 |
| 2026-03 | 629 | 544 | 420 |
| 2026-04 | 594 | 605 | 501 |
| 2026-05 | 744 | 478 | 352 |
| 2026-06 | 793 | 705 | 556 |
| 2026-07 | 739 | 460 | 325 |
| 2026-08 | 882 | 273 | 273 |
| **Jan–Aug** | **5,430** | **4,087** | **3,217** |
| 2026-09 (to the 9th) | 247 | 97 | 97 |

¹ LORA minus `DBP Customer - *` (666 tickets) and `DBP Surveyor - Whatsapp chat` (204). These are customer-contact channels; Bravo's queue has no equivalent, so leaving them in over-counts LORA by ~21%. Every comparison below uses platform-scope.

**By platform area.** Bravo: Surveyor 4,767 · Operation 507 · Underwriting 282 · Approval 121. LORA: Surveyor 2,233 · Operation 812 · Customer 666 · Underwriting 190 · Internal Tech 163 · User Access 120. **Both systems concentrate ~80% of their ticket load in the surveyor and operations stages** — the same seam, on two different paradigms.

---

## 3. The trend, on a stable-category basis

Restricting both series to categories that carry at least one ticket in Jan–Mar **and** at least one in August removes the taxonomy break from both sides. 37 Bravo categories, 19 LORA categories survive the filter.

| Month | Bravo, stable | LORA, stable |
|---|---|---|
| 2026-01 | 413 | 312 |
| 2026-02 | 555 | 226 |
| 2026-03 | 584 | 300 |
| 2026-04 | 538 | 408 |
| 2026-05 | 688 | 229 |
| 2026-06 | 705 | 354 |
| 2026-07 | 644 | 179 |
| 2026-08 | 751 | 206 |
| **Jan→Aug** | **×1.82** | **×0.66** |
| **Jan–Aug total** | **4,878** | **2,214** |

**This is the finding.** Bravo's ticket load rose 82% over eight months **while its application volume fell** (117,996 in July to 76,446 in August, and being actively drained into LORA). LORA's fell by a third while its volume rose. Per unit of work, the divergence is wider than the raw counts show.

The pack has an explanation ready for the Bravo direction and should be sceptical of it: a shrinking platform gets the *residual* population — the products and branches migrated last, the edge cases LORA does not yet cover. That is a real confound and it is not controlled for here. But it cuts both ways: it is also consistent with a system whose ops burden is not falling as its load falls, which is what a fixed-flowchart architecture under continuing product change would look like.

---

## 4. Manual-intervention rate — both platforms, same method

### 4.1 Defining the numerator

LORA's published ≈0.2% comes from Jira force-cancel (1,269) plus rewind (705 rows ≈ 360 incidents) = **≈1,630 interventions Jan–Aug** ([reliability.md](../../../lora-workspace/docs/production-findings/reliability.md#the-number-that-actually-matters-manual-intervention-rate)). To match it, this document selects the OTRS categories that mean *an application stopped and a person had to move it* — not questions, logins, config or master-data requests. Membership is listed in [Appendix A](#appendix-a-stuck-application-category-membership) so the classification can be argued with.

**The classification validates itself on LORA.** OTRS gives **1,453 stuck-application tickets Jan–Aug**; Jira gives **≈1,630**. Two independent ticketing sources, two independent category schemes, within 11% of each other. That is strong enough to apply the same filter to Bravo.

| | Bravo | LORA |
|---|---|---|
| Stuck-application tickets, Jan–Aug | **2,514** | **1,453** |
| Independent cross-check | — | ≈1,630 (Jira force-cancel + rewind) |

### 4.2 Applying the denominator

Application counts per month exist for Jun, Jul and Aug only ([cost.md](../../../lora-workspace/docs/production-findings/cost.md#the-estate-three-months)). LORA's June count in that sheet (2,789) is broken by ~40× and is replaced with the Temporal meter's ~110k, per the cost document's own correction.

| Month | Bravo apps | Bravo stuck | rate | LORA apps | LORA stuck | rate |
|---|---|---|---|---|---|---|
| Jun | 106,722 | 389 | 0.364% | ~110,000 | 266 | 0.242% |
| Jul | 117,996 | 411 | 0.348% | 119,527 | 103 | 0.086% |
| Aug | 76,446 | 534 | **0.699%** | 171,479 | 137 | 0.080%† |
| **Jun–Aug** | **301,164** | **1,334** | **0.443%** | **401,006** | **506** | **0.126%** |

† LORA's August rate is understated — the taxonomy break (§1) removed streams worth ~248 tickets/month from the queue.

| | Bravo | LORA |
|---|---|---|
| **Applications completing with zero support ticket** | **≈99.2%** (all tickets), **≈99.56%** (stuck only) | **≈99.6%** / **≈99.87%** |
| **Roughly one in…** | **1 in 225** needs a person to unstick it | **1 in 790** |
| All-ticket rate per 1,000 applications | 8.02 | 3.59 |
| Stuck-application rate per 1,000 | 4.43 | 1.26 |

**Bravo's manual-intervention rate is ≈0.44%, about 3.5× LORA's ≈0.13%.** LORA's OTRS-derived figure sits just under its own published 0.18–0.22%, which is the expected direction: OTRS sees tickets, Jira's force-cancel/rewind counts see the two specific recovery paths, and the overlap is partial.

### 4.3 Four reasons to hold this number loosely

1. **The denominators are the weakest link.** The billing sheet's platform totals go 109.5k → 237.5k → 247.9k in two months, which nothing else supports; the likeliest reading is that a LORA-originated application is counted again in Bravo when it books at go-live. If that is right, **Bravo's denominator is inflated and its true rate is higher than 0.44%**, not lower.
2. **A ticket is not an intervention, in either direction.** Bravo's operator console (`/v1/application-error-tracking`: assign-surveyor, assign-branch, cancel, send-salestrax) and its ~25 retry/reprocess/revive endpoints let an operator unstick an application **without raising a ticket at all**. Every silent recovery is a Bravo intervention this measurement cannot see. LORA has the mirror problem in reverse: force-cancel-then-re-originate is disruptive enough that it reliably produces a ticket.
3. **Three months is a short window** and the monthly rates are volatile (LORA 0.24% → 0.09% → 0.08%; Bravo 0.36% → 0.35% → 0.70%).
4. **The residual-population confound in §3 applies here too.**

**Net direction of the error.** Points 1 and 2 both push the same way — they understate Bravo. Point 4 is the only one that flatters LORA. The 3.5× gap is more likely a floor than a ceiling, but it should be re-derived once the billing owner defines both application columns.

---

## 5. Per-activity failure data

### 5.1 Bravo — top 12 categories, Jan–Aug

| Total | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Category |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **1,542** | 65 | 126 | 136 | 154 | 186 | 252 | 308 | 315 | **Surveyor Platform - Release reject** |
| 413 | 32 | 55 | 91 | 29 | 86 | 56 | 34 | 30 | Assignment Detail FU - Rescoring / Reproses |
| 370 | 57 | 60 | 61 | 40 | 47 | 35 | 31 | 39 | Surveyor Platform - Question |
| 310 | 22 | 33 | 31 | 29 | 60 | 58 | 41 | 36 | Surveyor Platform - Assignment Detail |
| 291 | 38 | 35 | 43 | 40 | 29 | 53 | 53 | 0 | Operation Platform - Other Support ‡ |
| 274 | 23 | 32 | 34 | 28 | 61 | 41 | 20 | 35 | Surveyor Platform - Scoring Process |
| 210 | 35 | 25 | 31 | 21 | 15 | 29 | 28 | 26 | Surveyor Platform - Login |
| 170 | 19 | 19 | 31 | 19 | 29 | 19 | 19 | 15 | Surveyor Platform - Submit |
| 170 | 11 | 21 | 8 | 52 | 31 | 18 | 18 | 11 | Surveyor Platform - MKYC |
| **145** | 3 | 9 | 3 | 9 | 19 | 21 | 20 | **61** | **Assignment Detail FU - Reassign Application** |
| 130 | 0 | 52 | 22 | 13 | 8 | 22 | 7 | 6 | Surveyor Platform - SG SSG 0 |
| **128** | 3 | 4 | 9 | 14 | 13 | 19 | 26 | **40** | **Assignment Detail FU - Request Take Application** |

‡ retired in the August re-categorisation. 60 distinct categories; top 5 = 53.9% of volume.

### 5.2 LORA — top 12 categories, Jan–Aug

| Total | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Category |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 809 | 136 | 106 | 110 | 77 | 109 | 158 | 113 | 0 | DBP Surveyor - Lainnya ‡ |
| 415 | 108 | 61 | 60 | 35 | 14 | 52 | 58 | 27 | DBP Operation - Lainnya |
| 369 | 78 | 37 | 42 | 31 | 75 | 57 | 49 | 0 | DBP Customer - Lainnya ‡ |
| **347** | 39 | 30 | 34 | 31 | 44 | **124** | 26 | 19 | **DBP Surveyor - Kendala Assignment Tidak Muncul** |
| **314** | 9 | 4 | 18 | **144** | 59 | 52 | 13 | 15 | **DBP Surveyor - Kendala / Gagal Reassign** |
| 297 | 24 | 22 | 43 | 50 | 39 | 47 | 72 | 0 | DBP Customer - Belum terima dana ‡ |
| 242 | 50 | 35 | 30 | 26 | 13 | 21 | 9 | 58 | DBP Surveyor - Kendala Proses Aplikasi |
| **233** | 64 | 34 | 28 | 61 | 5 | 14 | 15 | 12 | **DBP Operation - Assignment tidak muncul** |
| 204 | 40 | 31 | 39 | 23 | 12 | 45 | 14 | 0 | DBP Surveyor - Whatsapp chat ‡ |
| 155 | 0 | 6 | 23 | 27 | 34 | 28 | 26 | 11 | DBP Internal Tech - System & Technical Config |
| 117 | 10 | 15 | 32 | 36 | 15 | 2 | 3 | 4 | DBP User Access - Management User & Akses Login |
| 69 | 11 | 6 | 29 | 12 | 5 | 1 | 1 | 4 | DBP Surveyor - Kendala Batalkan Assignment |

‡ vanished in the August re-categorisation (§1). 42 distinct categories; top 5 = 55.2% of volume.

### 5.3 Three things the two tables say together

**(a) `Surveyor Platform - Release reject` is Bravo's dominant single failure, and it is accelerating.** 1,542 tickets — **28.4% of Bravo's entire Jan–Aug load**, more than the next three categories combined. It grew **4.8× (65 → 315)** while application volume fell, and normalised against the months where volume is known it still climbs: **2.36 → 2.61 → 4.12 per 1,000 applications** (Jun/Jul/Aug). Nothing else in either platform's data behaves like this.

This is the highest-value open item the export produces, and the analysis pack **cannot currently resolve it**: `bravo-analysis` holds documents only, and no code path named "release reject" has been mapped to a BPMN element or a service endpoint. Whoever owns the Surveyor Platform should be asked what user action raises this category and which activity it corresponds to. Until then it is a large, growing, unexplained failure concentration — and if it maps to a workflow step, it is the strongest per-activity evidence in the pack about either platform.

**(b) The surveyor-assignment seam is the top intervention driver on both platforms.** This is a convergence finding, and it belongs alongside the five already in [compare.md §4](../compare.md#4-where-the-two-systems-converge).

| | Bravo | LORA |
|---|---|---|
| Assignment-seam tickets, Jan–Aug | **1,182** (21.8% of load) | **1,021** (25.0% of load) |
| Categories | Reassign Application, Request Take Application, Cancel Application, Rescoring/Reproses, Assignment Detail, "assignment tidak muncul" ×3 | Gagal Reassign, Assignment Tidak Muncul ×3, Batalkan Assignment, Assignment Workflow Failed, Pembagian Assignment, Reassignment PIC |
| Failure vocabulary | assignment does not appear · cannot reassign · cannot take · cannot cancel | assignment does not appear · cannot reassign · cannot cancel · workflow failed |

**A BPMN flowchart and a GSM planner produce the same ops complaint, in the same words, at the same rate.** Neither paradigm solved surveyor assignment; each modelled it around a hand-written service layer (`SurveyorAssignmentServiceImpl`, 10,419 lines; `survey.go`, 5,473 lines / 125 transitions) and inherited that layer's failure modes. This is the sixth and cleanest instance of the "human-task complexity is paradigm-independent" convergence, and it is the first one measured on both sides rather than inferred from code size.

**(c) LORA's spikes are single-cause and recover; Bravo's growth is secular.** LORA's two largest categories are dominated by one bad month each — `Gagal Reassign` 144 in April against a 4–59 baseline, `Assignment Tidak Muncul` 124 in June against 26–44 — the signature of a defect shipped and then fixed. Bravo's top category has no spike; it has a slope. Incident-shaped load and debt-shaped load are different operational problems, and the mitigation for one does not work on the other.

---

## 6. What this changes in the analysis pack

| Claim as it stood | Status now |
|---|---|
| "We do not have Bravo's manual-intervention rate, incident counts or per-activity failure data" ([compare.md](../compare.md) scope caveats) | **Withdrawn.** All three now exist for Jan–Sep 2026. |
| §3.6 *Measured consequence* — Bravo: "Not measured" | **Replaced.** ≈0.44% Jun–Aug, 2,514 stuck-application tickets Jan–Aug. |
| §3.7 *Production cost* — Bravo: "Not measured" | **Replaced.** 413 rescoring/reprocess tickets Jan–Aug, against LORA's 705 rewind rows. |
| §5 "Bravo did better at bounded, classified failure… no zombie loans by construction" | **Qualified, not withdrawn.** Both halves of the pack's picture survive: Bravo has no zombie-loan class, *and* it generates 3.5× LORA's rate of applications needing a human. Bounded failure is not the same as infrequent failure — it converts an invisible wedge into a visible ticket. That is a better operational posture and it is what the ticket queue is counting. |
| §6.4 "Measure the same KPI on both… before anyone claims either platform is more reliable" | **Done, with the denominator caveat of §4.3.** The recommendation to compute Bravo's rate from `application_error_tracking` and endpoint hits still stands — it would capture the silent interventions OTRS misses (§4.3 point 2). |
| [option-summary.md](../option-summary.md) open question 3, "What is Bravo's manual-intervention rate?" | **Answered, provisionally.** No longer blocks the options comparison. |
| Option 3's case ("retire Bravo") | **Strengthened on reliability, unchanged on cost.** Bravo's tier is still the cheaper one per application (§3.12); it now also carries the higher intervention rate. |

**What it does not change.** Nothing here is an architecture measurement. Ticket load reflects product maturity, migration state, branch training, category hygiene and support-desk routing at least as much as it reflects BPMN versus GSM. The residual-population confound (§3) is real and uncontrolled. **This is the reliability comparison the pack was missing; it is not a verdict on the paradigm.**

---

## 7. What would firm this up

| | Effort | Why |
|---|---|---|
| Get the billing owner to define `Bravo total app` and `Lora total app` | Days | Every rate in §4 is a verified numerator over an unverified denominator. This is the single largest source of error. |
| Map `Surveyor Platform - Release reject` to a BPMN element or endpoint | Days | 28.4% of Bravo's ticket load, growing 4.8×, currently unexplained (§5.3a). |
| Count `application_error_tracking` rows and reprocess/revive endpoint hits | Days | Captures the Bravo interventions that never became tickets (§4.3 point 2) and gives a second, independent Bravo numerator — the same cross-check LORA already has. |
| Ask the service desk what changed in August | Hours | Whether the vanished LORA categories were re-routed, merged or genuinely closed determines if §3's divergence is real. |
| Re-export with resolution time and reopen count | Days | Ticket *count* weights a password reset the same as a wedged loan. Time-to-resolve would separate them. |
| Extend the window back to 2025 | Days | Eight months cannot distinguish a trend from a migration artefact. |

---

## Appendix A: stuck-application category membership

Selected as "an application stopped and a person had to move it". Excluded: questions, logins, user access, master/reference data, config requests, form-field defects, scoring-result queries, and all customer-contact channels.

**Bravo (15 categories, 2,514 tickets Jan–Aug):** `Surveyor Platform -` Release reject · Release Cancel · Assignment Detail FU - Rescoring / Reproses · Assignment Detail FU - Reassign Application · Assignment Detail FU - Request Take Application · Assignment Detail FU - Cancel Application · Assignment tidak muncul · Aplikasi tidak turun ke Surveyor · Perubahan Branch Booking; `Underwriting Platform -` Assignment tidak muncul; `Approval Platform -` Assignment tidak muncul · Ketidaksesuaian Staging Approval; `Operation Platform -` Aplikasi Tidak Bisa Lanjut · Aplikasi Gagal Return · Agreement Status Not Sync.

**LORA (23 categories, 1,453 tickets Jan–Aug):** `DBP Surveyor -` Kendala / Gagal Reassign · Kendala Assignment Tidak Muncul · Kendala Proses Aplikasi · Assignment Workflow Failed · Kendala Batalkan Assignment · Gagal melakukan revisi · Gagal approve revisi · Kendala Pembagian Assignment; `DBP Operation -` Assignment tidak muncul · Cancellation Request · Gagal kirim revisi · Data tidak berhasil kirim ke ops 2; `DBP Underwriting -` Assignment tidak muncul · Rewind · Return · Tidak masuk staging approval · Tidak berhasil lanjut · Tidak berhasil approve · Tidak berhasil revisi · Tidak berhasil reject · Salah staging · Perpindahan Proses · Perubahan/Reassignment PIC.

**Sensitivity.** The `Release reject` category alone is 1,542 of Bravo's 2,514. Excluding it entirely drops Bravo's Jun–Aug rate from 0.443% to **0.152%** — level with LORA's 0.126%. **Whether Bravo's intervention rate is 3.5× LORA's or level with it turns on one category whose meaning nobody in this pack has yet established.** That is why §7 ranks mapping it second.
