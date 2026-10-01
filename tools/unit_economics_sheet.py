"""Build the private "BFI Unit economics" Google Sheet (Bravo vs LORA).

Inputs (all gathered read-only beforehand):
  --gcp      FinOps pull JSON (finops_pull.py output): tier components + project/service totals
  --sre      SRE invoice workbook "GCP Billing - 2026" exported as .xlsx
  --bravo    Bravo application counts CSV (team query 2, UTC months)
  --lora     LORA counts CSV from lora_arango_counts.py (ArangoDB partnership-ndf-v2.doc_pending)

Writes to exactly one spreadsheet (SHEET_ID). The Inputs tab is written only
when it is empty, so amounts typed there survive a monthly re-run.

Auth: Application Default Credentials with the spreadsheets scope, i.e.
  gcloud auth application-default login \
    --scopes=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/cloud-platform
"""

import argparse
import csv
import json

import google.auth
import openpyxl
from googleapiclient.discovery import build

SHEET_ID = "1Kk2N0s20QnNHRMjQPeZ8bh5tYjgKc0qrxHU4B-P_8z0"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
PROJ_MONTHS = [f"2026-{m:02d}" for m in range(9, 13)] + [f"2027-{m:02d}" for m in range(1, 13)]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August"]

# Cross-check only: Temporal Usage "Workflows" actions / 2 (one LPW + one LTW per loan) should equal
# the ArangoDB LPW workflow count. LORA counts themselves come from ArangoDB (--lora).
LORA_WORKFLOW_ACTIONS = {"2026-04": 212251, "2026-05": 212655, "2026-06": 219022,
                         "2026-07": 224498, "2026-08": 271452}

# Measured 25 Sep 2026 (30 days, Datadog us5): share of usage from Bravo + LORA (prod-bravo-cluster / env:prod).
DATADOG_SHARE = {"logs ingested (prod-bravo-cluster index)": 38917240703091 / 40018585646645,
                 "APM spans ingested (env prod + prod-sharia)": (13290938696344 + 17737453994) / 15545550967445,
                 "containers running (prod-bravo-cluster)": 2248.75 / (2248.75 + 1059.19 + 36)}
# GitHub org bfi-finance, non-archived repos pushed in the 180 days to 25 Sep 2026.
DEV_TOOLS = {"bravo": 120, "lora": 25, "other": 42}
# Rewinds (Temporal reset = new run of the same LPW, same document), from lora-workspace/docs/production-findings/billing.
REWINDS = {"2026-01": 152, "2026-02": 98, "2026-03": 141, "2026-04": 69, "2026-05": 52, "2026-06": 118, "2026-07": 41,
           "2026-08": 33}
# Single days, 28 Sep 2026: LPW starts in ArangoDB (version.created_at) vs Temporal `workflow count` (dp-ndf queues).
DAILY_CHECK = [("2026-08-28", 4811, 4816), ("2026-09-01", 5012, 5015), ("2026-09-05", 4347, 4347),
               ("2026-09-10", 4886, 4886), ("2026-09-15", 4935, 4936), ("2026-09-20", 4341, 4341),
               ("2026-09-24", 4403, 4417)]
# August 2026 verified applications, grouped by customer NIK + product (ArangoDB, 28 Sep 2026).
AUG_ATTEMPTS = [("applied once", 79402), ("2 times", 12592), ("3 times", 3565), ("4 times", 1467), ("5+ times", 1854)]
AUG_EARLIER_STATUS = [("rejected", 21145), ("canceled", 13718), ("expired", 1240), ("disbursed", 15)]

TABS = ["CTO view", "Summary", "Shared breakdown", "Costs", "Applications", "Re-processing", "Allocation keys", "Inputs",
        "Vendors per call", "Projection", "Budget 2027", "Backtest", "Checks", "Read me"]

# Inputs: tool, bucket, key, amount, incl VAT, basis, period, source/budget id, note
INPUTS = [
    ["Temporal Cloud", "lora_tier", "none", 1679950003, "N", "contract (GCP Marketplace credit, Mar 2026)", "Mar 26 - Feb 27",
     "GCP invoice Mar 2026; IT budget ITOP0228", "IT budget shows Rp1,871,810,630 paid incl. VAT = same contract"],
    ["ArangoDB licence", "lora_tier", "none", 784772000, "N", "contract (Bravo & Lora Billing sheet)", "2026",
     "Bravo & Lora Billing sheet", "Budget 715,000,000; renewal quote 1,392,765,840. Old-sheet figure chosen 25 Sep"],
    ["Clickhouse", "lora_tier", "none", 68950980, "Y", "budget 2026", "2026", "IT budget 2026", "LORA-owned (confirmed 25 Sep)"],
    ["Metered.ca", "lora_tier", "none", 135864000, "Y", "budget 2026", "2026", "IT budget 2026", "LORA-owned (confirmed 25 Sep)"],
    ["Codacy", "shared", "dev_tools", 1089551250, "Y", "paid", "19 May 26 - 18 May 27", "BROP0005, KPO/PO/26/05/04016",
     "130 seats + 40 prorated; budget line 'Sonarqube/Codacy' 903,971,250"],
    ["Snyk", "shared", "dev_tools", 1170000000, "Y", "budget 2026", "22 Nov 26 - 21 Nov 27", "BROP0004", "'via GCP' but not on the GCP bill"],
    ["GitHub (340 seats, 184 Copilot)", "shared", "dev_tools", 1499808000, "Y", "budget 2026", "18 Oct 26 - 17 Oct 27", "BROP0006",
     "Rp530,392,243 paid so far"],
    ["Atlassian (Jira, Confluence)", "shared", "dev_tools", 1852000000, "Y", "budget 2026", "2026", "IT budget 2026", ""],
    ["Postman", "shared", "dev_tools", 233376000, "Y", "budget 2026", "2026", "IT budget 2026", ""],
    ["Cypress", "shared", "dev_tools", 15077130, "Y", "budget 2026", "2026", "IT budget 2026", ""],
    ["LambdaTest", "shared", "dev_tools", 82877691, "Y", "budget 2026", "2026", "IT budget 2026", ""],
    ["PagerDuty", "shared", "dev_tools", 297480000, "Y", "budget 2026", "2026", "IT budget 2026", ""],
    ["Apigee", "shared", "gcp_spend", 929600000, "Y", "budget 2026", "2026", "IT budget 2026", "Renewal invoice 26-27: 1,000,350,870"],
    ["SonarQube server", "shared", "dev_tools", None, "Y", "MISSING", "", "", "Fill in if SonarQube still runs next to Codacy"],
]
DATADOG_Y2 = ["Datadog Year 2 commitment (projection floor only)", 3176907912, "Y", "budget 2026 (contract Q-849776 Y2)",
              "from Oct 2026"]

VENDORS = [
    ["izi.credit", "credit scoring", "bpm", "Bravo"],
    ["Tongdun", "fraud scoring", "bpm", "Bravo"],
    ["advance.ai", "KYC / scoring", "bpm, kyc-proxy, external-services, onboarding, agent-marketing", "Shared"],
    ["Monnai", "KYC / scoring", "kyc-proxy", "Shared"],
    ["Pefindo", "credit bureau", "kyc-proxy", "Shared"],
    ["ASLI RI", "identity check", "kyc-proxy, external-services", "Shared"],
    ["VIDA", "e-signature / identity", "kyc-proxy, external-services", "Shared"],
    ["Privy", "e-signature", "kyc-proxy, external-services", "Shared"],
    ["Vonage (Nexmo)", "SMS / OTP / WhatsApp", "notification, notification-v2, external-services, call-gateway", "Shared"],
    ["text2tell", "SMS", "notification, notification-v2, external-services", "Shared"],
    ["smsblast", "SMS", "notification, notification-v2, external-services", "Shared"],
    ["yellow.ai", "chatbot / WhatsApp", "bpm, notification, onboarding, edoc, external-services", "Shared"],
    ["GoPay", "payments", "gold-service, kyc-proxy", "Shared"],
    ["Midtrans", "payments", "gold-service", "Other (not loan origination)"],
    ["DOKU", "payments", "bfi-payment-api", "Other (not loan origination)"],
]


def _m(*vals):
    """Monthly amounts from January 2026 on; None = no invoice yet."""
    return {f"2026-{i + 1:02d}": v for i, v in enumerate(vals) if v is not None}


# Per-call vendor invoices 2026, from Finance (read 29 Sep 2026). Amounts as invoiced.
#   SMS: "Tracking Invoice vendor SMS.xlsx" (Drive 1Vbi8QsJDIp29TsgOUlYGuM4Q4-oLZWQl). Vonage detail is ex-tax per API
#        key; Vonage July 2026 is still waiting for approval. ADA / Brahmayasa do not state the tax basis.
#   Yellow.ai: "Rekapitulasi Penggunaan Yellow Ai" (Drive 1ng0hmhJ3ERpLfBxDVZpIF1DFiqWYb-33S_pQzJk57mw), incl. VAT,
#        one tab per business unit, Jan-Jun 2026 so far.
# Columns: vendor, line, Bravo share, LORA share, VAT basis, source, amounts. Shares "sms" use Allocation keys B7/B8.
VENDOR_INVOICES = [
    ["Vonage", "WhatsApp, key 4ace03fe (WA - LORA, Digital Partnership)", 0, 1, "excl. VAT", "SMS file, Vonage detail",
     _m(45628935.10, 42919597.11, 53603820.01 + 104263 + 32979.64, 64144949.18 + 179449 + 59630.30,
        68534904.40 + 185956 + 54353.32, 88398763.56 + 324635 + 77016.76, 91120589.16 + 303417 + 69719.70)],
    ["Vonage", "OTP SMS, key af5e4fe8 (all BFI)", "sms", "sms", "excl. VAT", "SMS file, Vonage detail",
     _m(297762.73 + 50104327.19, 224205.44 + 45699763.08, 40304.09 + 45515113.99, 13204.85 + 50118165.21,
        28452.25 + 47208815.19, 10271.09 + 50058469.75, 20281.06 + 46765871.91)],
    ["Vonage", "Other SMS, key 8807cf48 (all BFI)", "sms", "sms", "excl. VAT", "SMS file, Vonage detail",
     _m(249 + 83.92 + 4208862.95, 530 + 224.79 + 3814814.20, 5215677.11, 162 + 75.93 + 3632992.44,
        15 + 4195950.75, 4748007.36, 5003607.05)],
    ["Vonage", "Notification Service, key b3ab55a7 (many apps)", "sms", "sms", "excl. VAT", "SMS file, Vonage detail",
     _m(1981459.97, 677617.31, 290890.11 + 571 + 390.63, 619467.15 + 12061.63, 504874.40, 781294.84 + 28, 887430.98)],
    ["ADA (Axiata)", "SMS (all BFI)", "sms", "sms", "incl. VAT (assumed)", "SMS file, ADA invoices",
     _m(26068330.02, 25111705.38, 26916125.82, 31566339.84, 26874026.85, 28026035.91, 40417889.43)],
    ["Brahmayasa / Nadyne", "SMS (all BFI)", "sms", "sms", "incl. VAT (assumed)", "SMS file, Brahmayasa invoices",
     _m(263253 + 10360984, 224692 + 9370947, 1726155 + 9692403, 3861479 + 9264582, 977361 + 9607910,
        801070 + 9847282, 972482 + 4354419)],
    ["Yellow.ai", "WhatsApp, Bravo tab: platform, utility and authentication", 1, 0, "incl. VAT", "Yellow.ai file, Bravo tab",
     _m(193382934.6 - 40894774.96, 190288527.2 - 39414639.51, 179396035.2 - 35045290.38, 210469135.3 - 43958950.29,
        212185024.3 - 43350271.4, 223449046.4 - 47210823.96)],
    ["Yellow.ai", "WhatsApp, Bravo tab: marketing conversations (flag: may not be origination)", 1, 0, "incl. VAT",
     "Yellow.ai file, Bravo tab", _m(40894774.96, 39414639.51, 35045290.38, 43958950.29, 43350271.4, 47210823.96)],
    ["Yellow.ai", "WhatsApp, Sharia tab", 1, 0, "incl. VAT", "Yellow.ai file, Sharia tab",
     _m(157727.96, 0.09, 0.09, 32716.39, 19488.92, 43552.74)],
    ["Yellow.ai", "WhatsApp, Digital Partnership tab (LORA's business unit)", 0, 1, "incl. VAT",
     "Yellow.ai file, Digital Partnership tab", _m(13787154.96, 11801028.8, 26811373.23, 9297474.55, 8963151.43, 8639584.72)],
    ["Vonage", "WhatsApp Tele RO, keys 00b4bd6a / 5b5cfb9f (telemarketing): EXCLUDED", 0, 0, "excl. VAT",
     "SMS file, Vonage detail",
     _m(341379 + 110713.72 + 99997650.18, 40432 + 12120.47 + 101555055.47, 47766 + 18808.12 + 93990100.36,
        366 + 103987145.17, 1126 + 935.11 + 96168415.37, 142 + 24.98 + 103889781.01, 66 + 117293367.59)],
    ["Yellow.ai", "WhatsApp, other business units (Tele RO, Collection, Customer Care, Buspro, HC, Teledigital, ITVM): EXCLUDED",
     0, 0, "incl. VAT", "Yellow.ai file, other tabs",
     _m(537461078.47, 544186464.59, 570851928.23, 529301689.14, 545616789.36, 524417070.89)],
]
# EKYC / credit bureau: "Summary Invoice+Details E-KYC.xlsx" (user's copy, Drive 11aeLZLs29U04KUHbLl-0DE4-Dz9S9ifA,
# read 29 Sep 2026), amounts after tax. Finance lists the users as "NDF4W, NDF2W, Agency, Sharia, Partnership, KYC Proxy".
# All calls go through prod-ms-kyc-proxy. LORA share = vendor calls whose trace includes a LORA service (Datadog APM,
# 14 days to 29 Sep 2026). No trace includes Bravo's BPM or intake services, so Bravo = 0; the rest (BFI mobile app
# customer-bff, rule engine, assistance, untraced) is left unattributed. Calls, not Rupiah: products are priced differently.
EKYC_LORA_SHARE = {"Advance AI": 20241 / 39647, "VIDA": (17946 + 1396) / (37559 + 2593),
                   "CBI": 47710 / 58954, "Pefindo": 32556 / 40574}
VENDOR_INVOICES += [
    ["Advance AI", "EKYC: OCR KTP, ID forgery, liveness (via kyc-proxy)", 0, EKYC_LORA_SHARE["Advance AI"], "incl. VAT",
     "EKYC file, AAI tab", _m(65511090, 61781157, 61460478, 71341254, 73583010, 73918674, 82898352, 67592673)],
    ["VIDA", "EKYC: digital certificate, liveness, demog check (via kyc-proxy)", 0, EKYC_LORA_SHARE["VIDA"], "incl. VAT",
     "EKYC file, VIDA tab", _m(257477598, 246833808, 245954244, 296933769, 247331421, 326152188, 346352579, 359876763)],
    ["CBI (Credit Bureau Indonesia)", "Credit bureau report (via kyc-proxy); new in 2026", 0, EKYC_LORA_SHARE["CBI"],
     "incl. VAT", "EKYC file, CBI tab",
     _m(4497720, 44000400, 123241080, 162916920, 355065690, 535387410, 566189910, 604208520)],
    ["Pefindo Biro Kredit", "Credit bureau IdScore / IdReport (via kyc-proxy); Jan-Feb awaited from Risk, Aug not billed",
     0, EKYC_LORA_SHARE["Pefindo"], "incl. VAT", "EKYC file, Pefindo tab",
     _m(None, None, 981094812, 1043863647, 760312704, 384688815, 162900825)],
]
VENDOR_MONTHS = [f"2026-{m:02d}" for m in range(1, 9)]
# Bravo / LORA share of all-BFI SMS sends. Datadog APM, 30 days to 29 Sep 2026, prod-ms-notification send traces
# (/v2/sms/send, /v2/message/send, /v1/notification/send, gRPC SendWrapper): 1,981 of 28,512 include prod-ms-bpm or
# Sharia BPM; none include a LORA service (LORA's WhatsApp runs on its own Vonage key and calls Vonage directly).
SMS_SHARE = {"bravo": 1981 / 28512, "lora": 0.0}

# Budget 2027 step changes: item -> (2027 per year excl. VAT as a formula of D = current, month it starts).
STEP_2027 = {
    "Temporal Cloud": ("=D{r}", 3, "Contract renews Mar 2027; same price assumed until a quote arrives"),
    "ArangoDB licence": (1392765840, 1, "Renewal quote 1,392,765,840 (current 784,772,000)"),
    "Apigee": ("=1000350870/1.11", 1, "Renewal invoice 26-27: 1,000,350,870 incl. VAT"),
    "GitHub (340 seats, 184 Copilot)": ("=D{r}*(1+$B$2)", 10, "Renews 18 Oct; uplift % in B2"),
    "Snyk": ("=D{r}*(1+$B$2)", 11, "Renews 22 Nov; uplift % in B2"),
    "Codacy": ("=D{r}*(1+$B$2)", 5, "Renews 19 May; uplift % in B2"),
}
# USD/IDR. 2027: Finance's estimate (Tommy, 29 Sep 2026; the real rate depends on the payment date). 2026: the rate in
# the IT budget ("Kurs IDR16.000"). Temporal's USD 100,000 was paid as Rp1,679,950,003.
FX = {"2027": 18000, "2026": 16000}
USD_PRICED = {"Temporal Cloud", "Clickhouse", "Metered.ca", "Codacy", "Snyk",
              "GitHub (340 seats, 184 Copilot)", "Atlassian (Jira, Confluence)", "Postman", "Cypress", "LambdaTest",
              "PagerDuty"}  # ArangoDB and Apigee have Rupiah quotes for the renewal already
USD_RATE_PAID = {"Temporal Cloud": "=1679950003/100000"}


def col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def load(args):
    gcp = json.load(open(args.gcp))
    fin = {}
    for r in gcp:
        fin[(r["month"], r["env"], r["bucket"], r["component"])] = r["amount"] or 0.0
    wb = openpyxl.load_workbook(args.sre, data_only=True)
    proj, serv = {}, {}
    for row in wb["Projects"].iter_rows(min_row=2, max_col=9, values_only=True):
        if row[0]:
            proj[row[0]] = {f"2026-{i + 1:02d}": float(row[i + 1] or 0) for i in range(8)}
    for row in wb["Services"].iter_rows(min_row=2, min_col=6, max_col=14, values_only=True):
        if row[0] and row[0] != "Services":
            serv[row[0]] = {f"2026-{i + 1:02d}": float(row[i + 1] or 0) for i in range(8)}
    bravo = {r["month"]: r for r in csv.DictReader(open(args.bravo))}
    lora = {r["month"]: {k: int(v) for k, v in r.items() if k != "month"} for r in csv.DictReader(open(args.lora))}
    return fin, proj, serv, bravo, lora


def build_costs(fin, proj, serv):
    """Rows: month, env, bucket, component, group, amount_before_share, key, share(f), amount(f), source, kind."""
    rows = []

    def add(m, env, bucket, comp, group, amt, key, src, kind):
        rows.append([m, env, bucket, comp, group, amt, key, None, None, src, kind])

    inputs_row = {r[0]: i + 2 for i, r in enumerate(INPUTS)}
    for m in MONTHS:
        f = lambda env, b, c: fin.get((m, env, b, c), 0.0)
        # prod tiers
        bpm_gke, bpm_sql, bpm_sh = f("prod", "bravo_tier", "ms-bpm GKE"), f("prod", "bravo_tier", "BPM Cloud SQL"), f("prod", "bravo_tier", "BPM Sharia Cloud SQL")
        lora_gke, arango = f("prod", "lora_tier", "squad=lora GKE"), f("prod", "lora_tier", "ArangoDB GKE")
        add(m, "prod", "bravo_tier", "ms-bpm GKE (k8s-label/app=ms-bpm)", "GCP", bpm_gke, "none", "FinOps", "usage")
        add(m, "prod", "bravo_tier", "BPM Cloud SQL (prod-postgres-bpm-d2bpm)", "GCP", bpm_sql, "none", "FinOps", "usage")
        add(m, "prod", "bravo_tier", "BPM Sharia Cloud SQL", "GCP", bpm_sh, "none", "FinOps", "usage")
        add(m, "prod", "lora_tier", "LORA GKE (k8s-label/squad=lora)", "GCP", lora_gke, "none", "FinOps", "usage")
        add(m, "prod", "lora_tier", "ArangoDB GKE (k8s-label/app=arangodb)", "GCP", arango, "none", "FinOps", "usage")
        # shared GCP in bravo-project-prod, by service, tiers removed, reconciled to the invoice
        services = {k[3]: v for k, v in fin.items() if k[0] == m and k[1] == "prod" and k[2] == "project_service"}
        services["Compute Engine"] = services.get("Compute Engine", 0) - bpm_gke - lora_gke - arango
        services["Cloud SQL"] = services.get("Cloud SQL", 0) - bpm_sql - bpm_sh
        for s, v in sorted(services.items(), key=lambda x: -x[1]):
            if abs(v) >= 1_000_000:
                add(m, "prod", "shared", f"GCP {s}", f"GCP {s}", v, "none", "FinOps (tiers removed)", "usage")
        small = sum(v for v in services.values() if abs(v) < 1_000_000)
        add(m, "prod", "shared", "GCP other services (< Rp1M each)", "GCP other", small, "none", "FinOps", "usage")
        invoice = proj["bravo-project-prod"][m]
        finops_total = fin.get((m, "prod", "project_total", "bravo-project-331802"), 0.0)
        add(m, "prod", "shared", "Invoice vs FinOps difference", "GCP other", invoice - finops_total, "none",
            "SRE invoice sheet minus FinOps", "usage")
        # company-wide tools on the GCP bill
        add(m, "prod", "shared", "Datadog (GCP Marketplace, usage-billed)", "Datadog", proj["Use of datadog-public endpoint"][m],
            "datadog", "SRE invoice sheet", "datadog")
        add(m, "prod", "shared", "Coralogix (SOC-owned)", "Coralogix", serv["Coralogix"][m], "gcp_spend", "SRE invoice sheet", "usage")
        other = proj["[Charges not specific to a project]"][m] - serv["Coralogix"][m] - serv["Temporal Cloud (Credits)"][m]
        add(m, "prod", "shared", "Other unattributed Marketplace (SCC, Mailgun, MongoDB, Looker Studio, ...)", "Other Marketplace",
            other, "gcp_spend", "SRE invoice sheet (Temporal credit removed)", "usage")
        # licences from Inputs (monthly, ex-VAT)
        for r in INPUTS:
            row = inputs_row[r[0]]
            add(m, "prod", r[1], r[0], "LORA licences" if r[1] == "lora_tier" else "Dev & platform licences",
                f"=Inputs!I{row}", r[2], "Inputs tab (IT budget 2026)", "fixed")
        # non-prod, shown apart
        np_bravo = f("nonprod", "bravo_tier", "ms-bpm GKE") + sum(v for k, v in fin.items() if k[0] == m and k[1] == "nonprod" and k[2] == "bravo_tier" and "Cloud SQL" in k[3])
        np_lora = f("nonprod", "lora_tier", "squad=lora GKE") + f("nonprod", "lora_tier", "ArangoDB GKE")
        np_total = proj["bravo-project-nonprod"][m]
        add(m, "nonprod", "nonprod_bravo", "Bravo BPM (ms-bpm + BPM Cloud SQL, SIT/UAT)", "Non-prod", np_bravo, "none", "FinOps", "usage")
        add(m, "nonprod", "nonprod_lora", "LORA (squad=lora + ArangoDB, SIT/UAT)", "Non-prod", np_lora, "none", "FinOps", "usage")
        add(m, "nonprod", "nonprod_shared", "Rest of bravo-project-nonprod", "Non-prod", np_total - np_bravo - np_lora, "none",
            "SRE invoice sheet minus tiers", "usage")
    for i, r in enumerate(rows, start=2):
        r[7] = (f'=IF(G{i}="none",1,IF(G{i}="datadog",\'Allocation keys\'!$B$2,IF(G{i}="dev_tools",\'Allocation keys\'!$B$3,'
                f'IFERROR(VLOOKUP(A{i},\'Allocation keys\'!$A$12:$G$30,7,FALSE),0))))')
        r[8] = f"=F{i}*H{i}"
    return rows


def grids(fin, proj, serv, bravo, lora):
    g = {}
    costs = build_costs(fin, proj, serv)
    g["Costs"] = [["Month", "Env", "Bucket", "Component", "Group", "Amount before share (Rp)", "Allocation key",
                   "Bravo+LORA share", "Amount (Rp)", "Source", "Kind"]] + costs

    # Applications
    # Applications: A month | B-E Bravo | F-K LORA from ArangoDB | L Temporal check | M rewinds
    app = [["Month", "Bravo conventional", "Bravo Sharia", "Bravo total", "Bravo first-time (conv.)",
            "LORA applications (verified submissions)", "LORA NDF2W", "LORA NDF4W", "LORA LPW workflows",
            "LORA never verified", "LORA repeat applications (same NIK + product in month)",
            "Temporal Workflows / 2 (check)", "LORA rewinds (log)", "Bravo unique loans (NIK + product)",
            "LORA unique loans (NIK + product)"]]
    for m in sorted(set(bravo) | set(lora)):
        r = len(app) + 1
        b, lo = bravo.get(m), lora.get(m)
        row = [m] + ([int(b["conventional"]), int(b["sharia"]), f"=B{r}+C{r}", int(b["conventional_first_time"])] if b else ["", "", "", ""])
        row += ([lo["applications"], lo["ndf2w"], lo["ndf4w"], lo["lpw_workflows"], lo["never_verified"], lo["reoriginated_est"]]
                if lo else ["", "", "", "", "", ""])
        row += [round(LORA_WORKFLOW_ACTIONS[m] / 2) if m in LORA_WORKFLOW_ACTIONS else "", REWINDS.get(m, "")]
        row += [int(b["unique_nik_product"]) + int(b["sharia_unique_nik_product"]) if b else "",
                f"=F{r}-K{r}" if lo else ""]
        app.append(row)
    g["Applications"] = app
    arow = {x[0]: i + 2 for i, x in enumerate(app[1:])}

    # Re-processing
    rp = [["Month", "LPW workflows", "Verified applications", "Never verified", "Repeat applications (same customer + product)",
           "Unique customer + product", "LPW workflows per unique customer", "Repeat share of applications", "Rewinds (extra runs)",
           "Bravo total", "Bravo re-created (prev_application_id)", "Bravo re-created share", "Bravo unique loans",
           "Bravo repeats (rows - unique)", "Bravo repeat share of rows", "Bravo re-processing cost (Rp)",
           "LORA re-processing cost (Rp)"]]
    for m in sorted(lora):
        r, a = len(rp) + 1, arow[m]
        rp.append([m, f"=Applications!I{a}", f"=Applications!F{a}", f"=Applications!J{a}", f"=Applications!K{a}",
                   f"=C{r}-E{r}", f'=IF(F{r}=0,"",B{r}/F{r})', f'=IF(C{r}=0,"",E{r}/C{r})', f"=Applications!M{a}",
                   f'=IF(Applications!D{a}="","",Applications!D{a})', f'=IF(Applications!B{a}="","",Applications!B{a}-Applications!E{a})',
                   f'=IF(Applications!B{a}="","",K{r}/Applications!B{a})',
                   f'=IF(Applications!N{a}="","",Applications!N{a})', f'=IF(M{r}="","",J{r}-M{r})', f'=IF(M{r}="","",N{r}/J{r})',
                   f'=IFERROR(VLOOKUP($A{r},Summary!$A:$R,15,FALSE),"")', f'=IFERROR(VLOOKUP($A{r},Summary!$A:$R,17,FALSE),"")'])
    rp.append([])
    rp.append(["August 2026: how often the same customer + product applied"])
    for k, v in AUG_ATTEMPTS:
        rp.append([k, v])
    rp.append([])
    rp.append(["August 2026: status of the earlier attempt, when a customer applied again"])
    for k, v in AUG_EARLIER_STATUS:
        rp.append([k, v])
    rp.append([])
    rp.append(["Notes: 'repeat' counts every extra verified submission by the same NIK + product in the month (mostly re-applying "
               "after a rejection or a cancellation, including IT Production force-cancel re-originations). Rewinds re-run the same "
               "workflow and add no application. Bravo's re-created count is conventional BPM only."])
    g["Re-processing"] = rp

    # Allocation keys
    dd = sum(DATADOG_SHARE.values()) / len(DATADOG_SHARE)
    dev = (DEV_TOOLS["bravo"] + DEV_TOOLS["lora"]) / sum(DEV_TOOLS.values())
    ak = [["Key", "Share", "How it was measured"],
          ["datadog", dd, "Average of the three measures below (edit if you prefer another weighting)"],
          ["dev_tools", dev, f"GitHub bfi-finance repos active in 180 days: Bravo {DEV_TOOLS['bravo']} + LORA {DEV_TOOLS['lora']} of {sum(DEV_TOOLS.values())}"]]
    for k, v in DATADOG_SHARE.items():
        ak.append([f"  datadog: {k}", v, "Datadog us5, 30 days to 25 Sep 2026"])
    ak.append(["sms_bravo", SMS_SHARE["bravo"], "Bravo share of all-BFI SMS sends: prod-ms-notification send traces that include "
               "prod-ms-bpm or Sharia BPM, 1,981 of 28,512 (Datadog APM, 30 days to 29 Sep 2026). Per-call vendors only"])
    ak.append(["sms_lora", SMS_SHARE["lora"], "LORA share of all-BFI SMS sends: no send trace includes a LORA service "
               "(LORA's WhatsApp is on its own Vonage key, billed directly)"])
    while len(ak) < 10:
        ak.append([])
    ak.append(["Monthly keys", "", "", "", "", "", ""])
    ak.append(["Month", "Bravo apps", "LORA LPW workflows", "Bravo share of Shared", "LORA share of Shared",
               "Bravo projects GCP (prod+nonprod)", "gcp_spend share"])
    exclude = {"[Charges not specific to a project]", "Use of datadog-public endpoint", "Source"}
    for m in MONTHS:
        r = len(ak) + 1
        ar = arow[m]
        bravo_gcp = proj["bravo-project-prod"][m] + proj["bravo-project-nonprod"][m]
        all_proj = sum(v[m] for k, v in proj.items() if k not in exclude)
        ak.append([m, f"=Applications!D{ar}", f"=Applications!I{ar}", f'=IF(C{r}="","",B{r}/(B{r}+C{r}))',
                   f'=IF(D{r}="","",1-D{r})', bravo_gcp, bravo_gcp / all_proj])
    g["Allocation keys"] = ak

    # Inputs
    inp = [["Tool", "Bucket", "Allocation key", "Amount per year (Rp)", "Includes VAT? (Y/N)", "Per year excl. VAT",
            "Basis", "Period", "Per month excl. VAT", "Source", "Note"]]
    for r in INPUTS:
        i = len(inp) + 1
        inp.append([r[0], r[1], r[2], r[3], r[4], f'=IF(D{i}="","",IF(E{i}="Y",D{i}/1.11,D{i}))', r[5], r[6],
                    f'=IF(F{i}="",0,F{i}/12)', r[7], r[8]])
    inp.append([])
    i = len(inp) + 1
    inp.append([DATADOG_Y2[0], "shared", "datadog", DATADOG_Y2[1], DATADOG_Y2[2], f'=IF(E{i}="Y",D{i}/1.11,D{i})',
                DATADOG_Y2[3], DATADOG_Y2[4], f"=F{i}/12", "IT budget 2026", "Used only as the Projection floor"])
    g["Inputs"] = inp
    datadog_floor_cell = f"Inputs!I{i}"

    # Vendors per call: A-F description + shares | G-N invoiced Jan-Aug 2026 | O-V excl. VAT; totals rows below
    vm = VENDOR_MONTHS
    v = [["Vendor", "Line", "Bravo share", "LORA share", "VAT basis", "Source"] + [f"{m} invoiced" for m in vm]
         + [f"{m} excl. VAT" for m in vm]]
    for x in VENDOR_INVOICES:
        r = len(v) + 1
        share = lambda s, cell: f"='Allocation keys'!{cell}" if s == "sms" else s
        row = [x[0], x[1], share(x[2], "$B$7"), share(x[3], "$B$8"), x[4], x[5]] + [x[6].get(m, "") for m in vm]
        row += [f'=IF({col(7 + j)}{r}="","",{col(7 + j)}{r}/IF(LEFT($E{r},4)="incl",1.11,1))' for j in range(len(vm))]
        v.append(row)
    v_last = len(v)
    v.append([])
    vtot = {}
    for name, sc in [("Bravo", "C"), ("LORA", "D")]:
        r = len(v) + 1
        vtot[name] = r
        v.append([f"{name}: per-call vendors attributed (excl. VAT)", "Blank = an included invoice is still missing", "", "", "", ""]
                 + [""] * len(vm)
                 + [f'=IF(SUMPRODUCT(({col(7 + j)}$2:{col(7 + j)}${v_last}="")*(${sc}$2:${sc}${v_last}>0))>0,"",'
                    f'SUMPRODUCT({col(15 + j)}$2:{col(15 + j)}${v_last},${sc}$2:${sc}${v_last}))' for j in range(len(vm))])
    v.append(["Shared by both, not attributed (EKYC calls outside LORA traces), excl. VAT", "", "", "", "", ""] + [""] * len(vm)
              + [f'=SUMPRODUCT({col(15 + j)}$2:{col(15 + j)}${v_last},--($C$2:$C${v_last}+$D$2:$D${v_last}>0),'
                 f'1-$C$2:$C${v_last}-$D$2:$D${v_last})' for j in range(len(vm))])
    r = len(v) + 1
    v.append(["Excluded (not loan origination), excl. VAT, for reference", "", "", "", "", ""] + [""] * len(vm)
              + [f'=SUMPRODUCT({col(15 + j)}$2:{col(15 + j)}${v_last},--($C$2:$C${v_last}+$D$2:$D${v_last}=0))'
                 for j in range(len(vm))])
    v.append([])
    v.append(["Vendor catalogue (who calls what, prod manifests)", "Category", "Called by", "Platform"])
    for x in VENDORS:
        v.append(x)
    v.append([])
    v.append(["EKYC shares (LORA column, editable): share of each vendor's calls made inside a LORA trace (Datadog, 14 days "
              "to 29 Sep 2026). No call traces back to Bravo's BPM, so Bravo is 0; the remaining calls (BFI mobile app, "
              "rule engine, assistance) are not attributed to either platform."])
    v.append(["Pefindo falls from Rp1.04bn (Apr) to Rp0.16bn (Jul) while CBI rises from Rp4.5M (Jan) to Rp0.60bn (Aug): "
              "the credit-bureau work is moving from Pefindo to CBI. Look at the two together."])
    g["Vendors per call"] = v
    vcol = {m: col(15 + j) for j, m in enumerate(vm)}

    # Summary
    # Summary: A month | B-D cost | E-G load | H-J Shared split (by load) | K-L unique loans | M-N COST PER LOAN |
    #          O-R re-processing | S-T per submission | U-V tier-only per loan | W non-prod | X vendors | Y-Z cost of unique loans
    #          AA-AE company | AF-AJ per-call vendors and cost per loan incl. vendors
    s = [["Month", "Bravo orchestration", "LORA orchestration", "Shared", "Bravo applications (rows)",
          "LORA verified submissions", "LORA LPW workflows", "Bravo share of Shared (rows vs LPW)", "Bravo part of Shared",
          "LORA part of Shared", "Bravo unique loans (NIK + product)", "LORA unique loans (NIK + product)",
          "Bravo cost per loan", "LORA cost per loan", "Bravo re-processing cost", "Bravo re-processing % of cost",
          "LORA re-processing cost", "LORA re-processing % of cost", "Bravo cost per application row",
          "LORA cost per verified submission", "Bravo tier-only per loan", "LORA tier-only per loan",
          "Non-prod (shown apart)", "Per-call vendors, Bravo + LORA (Vendors tab)", "Bravo cost of unique loans",
          "LORA cost of unique loans", "Company total cost (Bravo + LORA + Shared)", "Company unique loans",
          "Company cost per loan", "Company re-processing cost", "Company re-processing % of cost",
          "Bravo per-call vendors (excl. VAT)", "LORA per-call vendors (excl. VAT)", "Bravo cost per loan incl. per-call vendors",
          "LORA cost per loan incl. per-call vendors", "Company cost per loan incl. per-call vendors"]]
    for m in MONTHS:
        r = len(s) + 1
        ar = arow[m]
        sm = lambda b: f'SUMIFS(Costs!$I:$I,Costs!$A:$A,$A{r},Costs!$C:$C,"{b}")'
        s.append([m, "=" + sm("bravo_tier"), "=" + sm("lora_tier"), "=" + sm("shared"),
                  f"=Applications!D{ar}", f"=Applications!F{ar}", f"=Applications!I{ar}",
                  f"=E{r}/(E{r}+G{r})", f"=D{r}*H{r}", f"=D{r}-I{r}",
                  f"=Applications!N{ar}", f"=Applications!O{ar}",
                  f"=(B{r}+I{r})/K{r}", f"=(C{r}+J{r})/L{r}",
                  f"=(B{r}+I{r})*(1-K{r}/E{r})", f"=1-K{r}/E{r}", f"=(C{r}+J{r})*(1-L{r}/G{r})", f"=1-L{r}/G{r}",
                  f"=(B{r}+I{r})/E{r}", f"=(C{r}+J{r})/F{r}", f"=B{r}/K{r}", f"=C{r}/L{r}",
                  f'={sm("nonprod_bravo")}+{sm("nonprod_lora")}+{sm("nonprod_shared")}',
                  f'=IF(OR(AF{r}="",AG{r}=""),"",AF{r}+AG{r})',
                  f"=B{r}+I{r}-O{r}", f"=C{r}+J{r}-Q{r}",
                  f"=B{r}+C{r}+D{r}", f"=K{r}+L{r}", f"=AA{r}/AB{r}", f"=O{r}+Q{r}", f"=AD{r}/AA{r}",
                  f"='Vendors per call'!{vcol[m]}{vtot['Bravo']}", f"='Vendors per call'!{vcol[m]}{vtot['LORA']}",
                  f'=IF(AF{r}="","",(B{r}+I{r}+AF{r})/K{r})', f'=IF(AG{r}="","",(C{r}+J{r}+AG{r})/L{r})',
                  f'=IF(OR(AF{r}="",AG{r}=""),"",(AA{r}+AF{r}+AG{r})/AB{r})'])
    g["Summary"] = s

    # Shared breakdown
    groups = []
    for r in costs:
        if r[2] == "shared" and r[4] not in groups:
            groups.append(r[4])
    sb = [["Group"] + MONTHS]
    for gname in groups:
        r = len(sb) + 1
        sb.append([gname] + [f'=SUMIFS(Costs!$I:$I,Costs!$A:$A,{col(j + 2)}$1,Costs!$C:$C,"shared",Costs!$E:$E,$A{r})'
                             for j in range(len(MONTHS))])
    r = len(sb) + 1
    sb.append(["Total Shared"] + [f"=SUM({col(j + 2)}2:{col(j + 2)}{r - 1})" for j in range(len(MONTHS))])
    g["Shared breakdown"] = sb

    # Projection: A-C | D-I cost series | J Bravo rows | K LORA LPW | L-M unique loans | N share | O-P totals |
    #             Q-R cost per loan | S-T re-processing cost
    n_act = len(MONTHS)
    p = [["Month", "t", "Type", "Bravo tier", "LORA tier usage", "LORA fixed (licences)", "Shared usage (GCP, Coralogix, other)",
          "Shared Datadog", "Shared fixed (licences)", "Bravo applications (rows)", "LORA LPW workflows",
          "Bravo unique loans", "LORA unique loans", "Bravo share of Shared", "Bravo total cost", "LORA total cost",
          "Bravo cost per loan", "LORA cost per loan", "Bravo re-processing cost", "LORA re-processing cost",
          "Company total cost", "Company unique loans", "Company cost per loan", "Total processing load (rows + LPW)"]]
    prow = {}
    for t, m in enumerate(MONTHS + PROJ_MONTHS, start=1):
        r = len(p) + 1
        if m in MONTHS:
            cs = lambda b, k: f'SUMIFS(Costs!$I:$I,Costs!$A:$A,$A{r},Costs!$C:$C,"{b}",Costs!$K:$K,"{k}")'
            row = [m, t, "Actual", f'={cs("bravo_tier","usage")}', f'={cs("lora_tier","usage")}', f'={cs("lora_tier","fixed")}',
                   f'={cs("shared","usage")}', f'={cs("shared","datadog")}', f'={cs("shared","fixed")}',
                   f"=Summary!E{t + 1}", f"=Summary!G{t + 1}", f"=Summary!K{t + 1}", f"=Summary!L{t + 1}"]
        else:
            fc = lambda c: f"=MAX(0,FORECAST($B{r},{c}$2:{c}${n_act + 1},$B$2:$B${n_act + 1}))"
            dd_floor = f"'Allocation keys'!$B$2*{datadog_floor_cell}" if m >= "2026-10" else "0"
            row = [m, t, "Projected", fc("D"), fc("E"), f"=F{n_act + 1}", fc("G"),
                   f"=MAX({dd_floor},FORECAST($B{r},H$2:H${n_act + 1},$B$2:$B${n_act + 1}))", f"=I{n_act + 1}",
                   fc("J"), fc("K"), fc("L"), fc("M")]
        row += [f"=J{r}/(J{r}+K{r})", f"=D{r}+(G{r}+H{r}+I{r})*N{r}", f"=E{r}+F{r}+(G{r}+H{r}+I{r})*(1-N{r})",
                f"=O{r}/L{r}", f"=P{r}/M{r}", f"=O{r}*(1-L{r}/J{r})", f"=P{r}*(1-M{r}/K{r})",
                f"=O{r}+P{r}", f"=L{r}+M{r}", f"=U{r}/V{r}", f"=J{r}+K{r}"]
        p.append(row)
        prow[m] = r
    last = len(p)
    p.append([])
    p.append(["Year totals", "", "", "Bravo total cost", "LORA total cost", "Shared (all)", "Bravo unique loans",
              "LORA unique loans", "Bravo cost per loan", "LORA cost per loan", "Bravo re-processing cost",
              "LORA re-processing cost", "Company total cost", "Company unique loans", "Company cost per loan"])
    p_year = {}
    for yr, lo, hi in [("2026 (Feb-Dec: actual + projected)", 2, 12), ("2027 (projected)", 13, last)]:
        r = len(p) + 1
        p.append([yr, "", "", f"=SUM(O{lo}:O{hi})", f"=SUM(P{lo}:P{hi})", f"=SUM(G{lo}:I{hi})", f"=SUM(L{lo}:L{hi})",
                  f"=SUM(M{lo}:M{hi})", f"=D{r}/G{r}", f"=E{r}/H{r}", f"=SUM(S{lo}:S{hi})", f"=SUM(T{lo}:T{hi})",
                  f"=D{r}+E{r}", f"=G{r}+H{r}", f"=M{r}/N{r}"])
        p_year[yr[:4]] = r
    p.append(["Note: January 2026 is not included (no FinOps cost data). Shared is split by processing load "
              "(Bravo rows vs LORA LPW); cost per loan divides by unique customer + product."])
    g["Projection"] = p

    # Checks
    ck = [["Check", "Month", "Expected", "Actual", "Difference", "Pass?"]]
    for m in MONTHS:
        r = len(ck) + 1
        ck.append(["bravo-project-prod: FinOps total vs SRE invoice", m, proj["bravo-project-prod"][m],
                   fin.get((m, "prod", "project_total", "bravo-project-331802"), 0.0), f"=D{r}/C{r}-1", f'=IF(ABS(E{r})<0.015,"PASS","CHECK")'])
    for m in MONTHS:
        r = len(ck) + 1
        ck.append(["bravo-project-nonprod: FinOps total vs SRE invoice", m, proj["bravo-project-nonprod"][m],
                   fin.get((m, "nonprod", "project_total", "bravo-project-nonprod"), 0.0), f"=D{r}/C{r}-1", f'=IF(ABS(E{r})<0.015,"PASS","CHECK")'])
    for i, m in enumerate(MONTHS, start=2):
        r = len(ck) + 1
        ck.append(["Shared split adds up (Bravo part + LORA part = Shared)", m, f"=Summary!D{i}",
                   f"=Summary!I{i}+Summary!J{i}", f"=D{r}-C{r}", f'=IF(ABS(E{r})<1,"PASS","CHECK")'])
    for i, m in enumerate(MONTHS, start=2):
        r = len(ck) + 1
        ck.append(["Prod buckets add up to invoice (tiers + Shared GCP part = bravo-project-prod)", m, proj["bravo-project-prod"][m],
                   f'=SUMIFS(Costs!$F:$F,Costs!$A:$A,B{r},Costs!$E:$E,"GCP*")', f"=D{r}/C{r}-1", f'=IF(ABS(E{r})<0.001,"PASS","CHECK")'])
    for m in sorted(LORA_WORKFLOW_ACTIONS):
        r, a = len(ck) + 1, arow[m]
        ck.append(["LORA LPW workflows (ArangoDB) vs Temporal Workflows / 2", m, f"=Applications!L{a}", f"=Applications!I{a}",
                   f"=D{r}/C{r}-1", f'=IF(ABS(E{r})<0.03,"PASS","CHECK")'])
    for d, arango, temporal in DAILY_CHECK:
        r = len(ck) + 1
        ck.append(["LORA LPW starts on one day: ArangoDB vs Temporal workflow count", d, temporal, arango,
                   f"=D{r}/C{r}-1", f'=IF(ABS(E{r})<0.01,"PASS","CHECK")'])
    for m in sorted(lora):
        r, a = len(ck) + 1, arow[m]
        ck.append(["LORA applications <= LPW workflows", m, f"=Applications!I{a}", f"=Applications!F{a}",
                   f"=D{r}-C{r}", f'=IF(D{r}<=C{r},"PASS","CHECK")'])
    for m in sorted(lora):
        r, a = len(ck) + 1, arow[m]
        ck.append(["LORA unique loans <= verified submissions", m, f"=Applications!F{a}", f"=Applications!O{a}",
                   f"=D{r}-C{r}", f'=IF(D{r}<=C{r},"PASS","CHECK")'])
    for m in MONTHS:
        r, a = len(ck) + 1, arow[m]
        ck.append(["Bravo unique loans <= application rows", m, f"=Applications!D{a}", f"=Applications!N{a}",
                   f"=D{r}-C{r}", f'=IF(D{r}<=C{r},"PASS","CHECK")'])
    for i, m in enumerate(MONTHS, start=2):
        r = len(ck) + 1
        ck.append(["Cost of unique loans + re-processing = platform total (Bravo + LORA)", m,
                   f"=Summary!B{i}+Summary!I{i}+Summary!C{i}+Summary!J{i}",
                   f"=Summary!Y{i}+Summary!O{i}+Summary!Z{i}+Summary!Q{i}", f"=D{r}-C{r}", f'=IF(ABS(E{r})<1,"PASS","CHECK")'])
    for m, n in [("2026-06", 106722), ("2026-07", 117996)]:
        r = len(ck) + 1
        ck.append(["Bravo rows = Bravo team's reported count", m, n, f"=Applications!B{arow[m]}", f"=D{r}-C{r}",
                   f'=IF(E{r}=0,"PASS","CHECK")'])
    r = len(ck) + 1
    ck.append(["Bravo Aug 2026 = Bravo team's reported count", "2026-08", 118253, f"=Applications!B{arow['2026-08']}",
               f"=D{r}-C{r}", f'=IF(E{r}=0,"PASS","CHECK")'])
    for i, m in enumerate(MONTHS, start=2):
        r = len(ck) + 1
        ck.append(["Company total = Bravo orch. + Bravo part + LORA orch. + LORA part", m, f"=Summary!AA{i}",
                   f"=Summary!B{i}+Summary!I{i}+Summary!C{i}+Summary!J{i}", f"=D{r}-C{r}", f'=IF(ABS(E{r})<1,"PASS","CHECK")'])
    g["Checks"] = ck

    bud = budget_grid(g, prow, p_year, datadog_floor_cell)
    bt = backtest_grid(g, bud)
    top = shared_top_groups(costs, groups)
    g["CTO view"], g["_charts"] = cto_grid(bud, bt, top, groups, prow)
    g["Read me"] = [[x] for x in README]
    return g


M27 = [f"2027-{m:02d}" for m in range(1, 13)]
INPUTS_NAMES = {r[0] for r in INPUTS}


def budget_grid(g, prow, p_year, datadog_floor_cell):
    """Budget 2027: assumptions, fixed contracts with step changes, fitted variable rates, scenario volumes,
    monthly budget per scenario and yearly totals. Returns the row numbers other tabs need."""
    n_act = len(MONTHS)
    b = []

    def put(row):
        b.append(row)
        return len(b)

    put(["Budget 2027 (prod, excl. VAT). Yellow cells are inputs; everything else is a formula.", "Value", "Note"])
    a = {}
    a["uplift"] = put(["Renewal uplift % (GitHub, Snyk, Codacy at renewal)", 0, "0% = same price"])
    a["gcp_pct"] = put(["GCP price change %", 0, "Applied to all GCP usage from the month below"])
    a["gcp_from"] = put(["GCP price change from month (1-12)", 1, ""])
    a["low"] = put(["Low scenario = base x", 0.8, ""])
    a["high"] = put(["High scenario = base x", 1.2, ""])
    a["dd"] = put(["Datadog Year 2 floor per month (Bravo+LORA share)", f"='Allocation keys'!$B$2*{datadog_floor_cell}",
                   "Contract Q-849776 Year 2; usage above it is billed"])
    a["ratio_b"] = put(["Bravo load per loan (rows / unique loans, last 3 months)",
                        f"=SUM(Summary!E{n_act - 1}:E{n_act + 1})/SUM(Summary!K{n_act - 1}:K{n_act + 1})",
                        "Lower it to model fewer repeat applications"])
    a["ratio_l"] = put(["LORA load per loan (LPW workflows / unique loans, last 3 months)",
                        f"=SUM(Summary!G{n_act - 1}:G{n_act + 1})/SUM(Summary!L{n_act - 1}:L{n_act + 1})",
                        "Lower it to model fewer repeat submissions"])
    a["fx27"] = put(["USD/IDR rate for 2027 (Finance estimate)", FX["2027"],
                     "Finance (Tommy, 29 Sep 2026): actual rate depends on the payment date; Rp18,000 for estimates"])
    a["fx26"] = put(["USD/IDR rate behind the current amounts", FX["2026"],
                     "IT budget 2026 uses 'Kurs IDR16.000'; Temporal was paid at 16,800 (own cell in block A)"])
    a["gcp_fx"] = put(["Apply the new rate to GCP and Datadog usage too? (Y/N)", "Y",
                       "Y if GCP / Marketplace is billed in USD and converted; N if priced in Rupiah"])
    fxr = f"IF($B${a['gcp_fx']}=\"Y\",$B${a['fx27']}/$B${a['fx26']},1)"
    assert a["uplift"] == 2  # STEP_2027 formulas use $B$2
    put([])

    # A. Fixed contracts
    put(["A. Fixed contracts (licences and prepaid contracts)"])
    hdr = ["Item", "Bucket", "Bravo+LORA share", "Current per year (excl. VAT)", "2027 per year (excl. VAT)",
           "Changes from month (2027)", "Full company per year 2027 (memo, for the IT budget)", "Source / note"] + M27 + [
           "Priced in USD? (Y/N)", "USD/IDR rate behind the current amount", "Exchange-rate factor on the new amount"]
    put(hdr)
    first = len(b) + 1
    inputs_row = {r[0]: i + 2 for i, r in enumerate(INPUTS)}
    for x in INPUTS:
        r = len(b) + 1
        key = {"none": "1", "dev_tools": "'Allocation keys'!$B$3",
               "gcp_spend": f"'Allocation keys'!$G${12 + n_act}"}[x[2]]
        new, frm, note = STEP_2027.get(x[0], ("=D{r}", 1, "Flat"))
        new = new.format(r=r) if isinstance(new, str) else new
        row = [x[0], x[1], "=" + key, f"=N(Inputs!F{inputs_row[x[0]]})", new, frm, f"=E{r}*W{r}", note]
        row += [f"=IF({k}>=$F{r},$E{r}*$W{r},$D{r})/12*$C{r}" for k in range(1, 13)]
        row += ["Y" if x[0] in USD_PRICED else "N", USD_RATE_PAID.get(x[0], f"=$B${a['fx26']}"),
                f'=IF(U{r}="Y",$B${a["fx27"]}/V{r},1)']
        put(row)
    last = len(b)
    sub = {}
    for bucket in ["bravo_tier", "lora_tier", "shared"]:
        sub[bucket] = put([f"Fixed contracts per month: {bucket}", "", "", "", "", "", "", ""]
                          + [f'=SUMIF($B${first}:$B${last},"{bucket}",{col(9 + k)}${first}:{col(9 + k)}${last})' for k in range(12)])
    put([])

    # B. Variable rates
    put(["B. Usage costs: fixed part + cost per extra unit of load, fitted on the actual months (Projection tab)"])
    put(["Bucket", "Cost series (Projection)", "Driver (Projection)", "Fixed part per month (fit)", "Cost per extra unit (fit)",
         "R squared", "Your fixed part (optional)", "Your cost per unit (optional)", "Fixed part used", "Cost per unit used"])
    fit = {}
    for name, y, x in [("Bravo tier (GCP)", "D", "J"), ("LORA tier usage (GCP)", "E", "K"),
                       ("Shared usage (GCP, Coralogix, other)", "G", "X"), ("Shared Datadog", "H", "X")]:
        r = len(b) + 1
        Y, X = f"Projection!{y}2:{y}{n_act + 1}", f"Projection!{x}2:{x}{n_act + 1}"
        put([name, y, x, f"=MAX(0,AVERAGE({Y})-MAX(0,SLOPE({Y},{X}))*AVERAGE({X}))", f"=(AVERAGE({Y})-D{r})/AVERAGE({X})",
             f"=RSQ({Y},{X})", None, None, f'=IF(G{r}="",D{r},G{r})', f'=IF(H{r}="",E{r},H{r})'])
        fit[name.split(" (")[0]] = r
    fb, fl, fs, fd = fit["Bravo tier"], fit["LORA tier usage"], fit["Shared usage"], fit["Shared Datadog"]
    put(["Drivers: J = Bravo application rows, K = LORA LPW workflows, X = both. Datadog uses the larger of the fit and the "
         "Year 2 floor. Fits keep the line through the average month and never go below zero."])
    put([])

    # C. Scenario volumes
    put(["C. Expected unique loans per month (type yours over the defaults)"])
    put(["Month", "Base: Bravo loans", "Base: LORA loans", "Low: Bravo loans", "Low: LORA loans", "High: Bravo loans",
         "High: LORA loans"])
    vol = {}
    for m in M27:
        r = len(b) + 1
        vol[m] = r
        put([m, f"=ROUND(Projection!L{prow[m]},0)", f"=ROUND(Projection!M{prow[m]},0)", f"=ROUND(B{r}*$B${a['low']},0)",
             f"=ROUND(C{r}*$B${a['low']},0)", f"=ROUND(B{r}*$B${a['high']},0)", f"=ROUND(C{r}*$B${a['high']},0)"])
    put(["Base defaults = the Projection trend of unique loans. Loans = unique customer + product per month."])
    put([])

    # D. Monthly budget per scenario
    blocks = {}
    for scen, cb, cl in [("Low", "D", "E"), ("Base", "B", "C"), ("High", "F", "G")]:
        put([f"D. Monthly budget: {scen} scenario"])
        put(["Month", "Bravo loans", "LORA loans", "Bravo load", "LORA load", "Bravo share of Shared", "GCP price x exchange-rate factor",
             "Bravo orchestration", "LORA orchestration", "Shared", "Company total", "Bravo part of Shared", "LORA part of Shared",
             "Bravo total", "LORA total", "Bravo cost per loan", "LORA cost per loan", "Company cost per loan", "Fixed", "Variable"])
        r0 = len(b) + 1
        for k, m in enumerate(M27):
            r, c = len(b) + 1, col(9 + k)
            put([m, f"={cb}{vol[m]}", f"={cl}{vol[m]}", f"=B{r}*$B${a['ratio_b']}", f"=C{r}*$B${a['ratio_l']}",
                 f"=IF(D{r}+E{r}=0,0.5,D{r}/(D{r}+E{r}))", f"=IF({k + 1}>=$B${a['gcp_from']},1+$B${a['gcp_pct']},1)*{fxr}",
                 f"=($I${fb}+$J${fb}*D{r})*G{r}+{c}${sub['bravo_tier']}",
                 f"=($I${fl}+$J${fl}*E{r})*G{r}+{c}${sub['lora_tier']}",
                 f"=($I${fs}+$J${fs}*(D{r}+E{r}))*G{r}+MAX($B${a['dd']}*{fxr},($I${fd}+$J${fd}*(D{r}+E{r}))*{fxr})+{c}${sub['shared']}",
                 f"=H{r}+I{r}+J{r}", f"=J{r}*F{r}", f"=J{r}-L{r}", f"=H{r}+L{r}", f"=I{r}+M{r}",
                 f'=IF(B{r}=0,"",N{r}/B{r})', f'=IF(C{r}=0,"",O{r}/C{r})', f'=IF(B{r}+C{r}=0,"",K{r}/(B{r}+C{r}))',
                 f"={c}${sub['bravo_tier']}+{c}${sub['lora_tier']}+{c}${sub['shared']}+($I${fb}+$I${fl}+$I${fs})*G{r}"
                 f"+MAX($B${a['dd']},$I${fd})*{fxr}",
                 f"=K{r}-S{r}"])
        blocks[scen] = (r0, len(b))
        put([])

    # E. Yearly totals
    put(["E. Budget 2027: yearly totals"])
    put(["Scenario", "Bravo orchestration", "LORA orchestration", "Shared", "Company total", "Bravo total (incl. part of Shared)",
         "LORA total (incl. part of Shared)", "Fixed", "Variable", "Bravo loans", "LORA loans", "Company cost per loan"])
    year = {}
    for scen in ["Low", "Base", "High"]:
        r0, r1 = blocks[scen]
        r = len(b) + 1
        year[scen] = r
        S = lambda c: f"=SUM({c}{r0}:{c}{r1})"
        put([scen, S("H"), S("I"), S("J"), S("K"), S("N"), S("O"), S("S"), S("T"), S("B"), S("C"), f"=E{r}/(J{r}+K{r})"])
    r = len(b) + 1
    put(["Projection tab 2027 (straight-line trend, no step changes)", "", "", "", f"=Projection!M{p_year['2027']}"])
    put(["Base scenario vs Projection tab", "", "", "", f"=E{year['Base']}/E{r}-1"])
    put([])
    put(["How to read it: fixed contracts + the fixed part of usage is most of the budget; the volume you type in only "
         "moves the variable part. Budget the fixed part and the known step changes first."])
    g["Budget 2027"] = b
    return {"a": a, "blocks": blocks, "year": year, "sub": sub, "first": first, "last": last, "vs_proj": r + 1}


def backtest_grid(g, bud):
    """Backtest: predict each known month from the months before it, compare with the actual company cost."""
    n = len(MONTHS) + 1  # last Summary row
    bt = [["Month", "Actual company cost", "Company unique loans", "Predicted: cost per loan x loans (last month)",
           "Predicted: cost per loan x loans (average so far)", "Predicted: fixed + variable fit", "Predicted: last month's cost (flat)",
           "Error: cost per loan (last month)", "Error: cost per loan (average)", "Error: fixed + variable", "Error: flat"]]
    first_pred = None
    for i, m in enumerate(MONTHS):
        s = i + 2
        r = len(bt) + 1
        row = [m, f"=Summary!AA{s}", f"=Summary!AB{s}"]
        if i >= 3:
            first_pred = first_pred or r
            A, L = f"Summary!AA2:AA{s - 1}", f"Summary!AB2:AB{s - 1}"
            row += [f"=Summary!AA{s - 1}/Summary!AB{s - 1}*C{r}", f"=SUMPRODUCT({A}/{L})/{s - 2}*C{r}",
                    f"=INTERCEPT({A},{L})+MAX(0,SLOPE({A},{L}))*C{r}", f"=Summary!AA{s - 1}",
                    f"=D{r}/B{r}-1", f"=E{r}/B{r}-1", f"=F{r}/B{r}-1", f"=G{r}/B{r}-1"]
        bt.append(row)
    lr = len(bt)
    r = len(bt) + 1
    bt.append(["Average size of the error", "", "", "", "", "", ""]
              + [f"=SUMPRODUCT(ABS({c}{first_pred}:{c}{lr}))/COUNT({c}{first_pred}:{c}{lr})" for c in "HIJK"])
    mean_row = r
    bt.append(["Each month is predicted only from the months before it (at least 3), using the month's REAL loans. "
               "That is the best case: a real budget also has to guess the loans."])
    bt.append([])
    bt.append(["Block test: fit on the first N months, predict the rest"])
    rn = len(bt) + 1
    bt.append(["N (months used to fit)", 3])
    T = f"COUNT(Summary!$AA$2:$AA${n})"
    tr_c, tr_l = f"OFFSET(Summary!$AA$2,0,0,$B${rn},1)", f"OFFSET(Summary!$AB$2,0,0,$B${rn},1)"
    te_c = f"OFFSET(Summary!$AA$2,$B${rn},0,{T}-$B${rn},1)"
    te_l = f"OFFSET(Summary!$AB$2,$B${rn},0,{T}-$B${rn},1)"
    r = len(bt) + 1
    bt.append(["Actual cost of the predicted months", f"=SUM({te_c})"])
    bt.append(["Cost per loan x loans", f"=SUM({tr_c})/SUM({tr_l})*SUM({te_l})", f"=B{r + 1}/B{r}-1"])
    bt.append(["Fixed + variable fit", f"=({T}-$B${rn})*INTERCEPT({tr_c},{tr_l})+SLOPE({tr_c},{tr_l})*SUM({te_l})", f"=B{r + 2}/B{r}-1"])
    bt.append(["Last fitted month's cost, flat", f"=INDEX(Summary!$AA$2:$AA${n},$B${rn})*({T}-$B${rn})", f"=B{r + 3}/B{r}-1"])
    block = (r, r + 3)
    cpl = cpl_one_year(bt, bud, n)
    bt.append([])
    for line in [
        "WHAT IT MEANS",
        "Cost per loan x expected loans over-predicts when volume grows: from Feb to Aug 2026 loans rose 32% but cost only 9%,",
        "  because about three quarters of the cost is fixed. A wrong volume guess also passes almost 1-to-1 into the budget.",
        "No method here can see contract step changes (ArangoDB renewal, Datadog Year 2, Temporal renewal): add them on top.",
        "Use cost per loan as the efficiency KPI. Budget with 'Budget 2027': fixed contracts + fixed part of usage + a small",
        "  cost per extra unit x expected load. Re-run this test every month; the fit needs about 6 months to be reliable."]:
        bt.append([line])
    g["Backtest"] = bt
    return {"first": 2, "last": lr, "mean": mean_row, "block": block, "n_cell": rn, "cpl": cpl}


def cpl_one_year(bt, bud, n):
    """If the budget is cost per loan x expected loans: error by horizon (2026 history) and over 2027 (vs Budget 2027)."""
    k = len(MONTHS)
    bt.append([])
    bt.append(["IF THE BUDGET IS COST PER LOAN x EXPECTED LOANS: HOW BIG IS THE ERROR?"])
    bt.append(["1. By how far ahead you predict (2026): month i's cost per loan x a later month's real loans, vs that month's "
               "actual cost. Helper grid, rows = starting month, columns = months ahead."])
    bt.append(["Starting month"] + [f"{h} ahead" for h in range(1, k)])
    g0 = len(bt) + 1
    for i, m in enumerate(MONTHS):
        si = i + 2
        bt.append([m] + [f"=Summary!AA{si}/Summary!AB{si}*Summary!AB{si + h}/Summary!AA{si + h}-1" if i + h < k else ""
                         for h in range(1, k)])
    g1 = len(bt)
    bt.append([])
    bt.append(["Months ahead", "Average error", "Smallest", "Largest"])
    h0 = len(bt) + 1
    for h in range(1, k):
        c = col(1 + h)
        rng = f"{c}{g0}:{c}{g1}"
        bt.append([h, f"=AVERAGE({rng})", f"=MIN({rng})", f"=MAX({rng})"])
    h1 = len(bt)
    bt.append([])
    bt.append(["2. Over a year: 2027 budget as cost per loan x the scenario's loans, vs the Budget 2027 model "
               "(fixed contracts, step changes, exchange rate)"])
    rates = [("Latest month's cost per loan", f"=Summary!AA{n}/Summary!AB{n}"),
             ("Last 3 months' cost per loan", f"=SUM(Summary!AA{n - 2}:AA{n})/SUM(Summary!AB{n - 2}:AB{n})"),
             ("All months' cost per loan", f"=SUM(Summary!AA2:AA{n})/SUM(Summary!AB2:AB{n})")]
    yr = bud["year"]
    bt.append(["Cost per loan used", "Rp per loan", "Low", "Base", "High"])
    bt.append(["Budget 2027 model (the reference)", "", *[f"='Budget 2027'!E{yr[sc]}" for sc in ("Low", "Base", "High")]])
    ref = len(bt)
    bt.append(["2027 loans in the scenario", "", *[f"='Budget 2027'!J{yr[sc]}+'Budget 2027'!K{yr[sc]}" for sc in ("Low", "Base", "High")]])
    loans = len(bt)
    y0 = len(bt) + 1
    for lbl, f in rates:
        r = len(bt) + 1
        bt.append([f"Error: {lbl}", f] + [f"=$B{r}*{c}${loans}/{c}${ref}-1" for c in "CDE"])
    y1 = len(bt)
    bt.append([])
    bt.append(["3. Why the base case can look right: two errors that cancel (company fit on the actual months)"])
    rf = len(bt) + 1
    bt.append(["Fixed part per month (fit)", f"=INTERCEPT(Summary!AA2:AA{n},Summary!AB2:AB{n})"])
    bt.append(["Cost per extra loan (fit)", f"=SLOPE(Summary!AA2:AA{n},Summary!AB2:AB{n})"])
    bt.append(["2027 cost from 2026's cost pattern only (base loans)", f"=12*B{rf}+B{rf + 1}*D{loans}"])
    bt.append(["Volume effect: cost per loan x loans over-budgets by", f"=B{y0}*D{loans}/B{rf + 2}-1"])
    bt.append(["Missing cost: contract changes + exchange rate not in 2026's pattern", f"=D{ref}/B{rf + 2}-1"])
    bt.append([])
    bt.append(["4. If the loans guess is wrong (budget set on base loans, latest month's cost per loan)"])
    bt.append(["Actual loans vs plan", "Error of the cost-per-loan budget"])
    for x in (-0.3, -0.2, -0.1, 0, 0.1, 0.2):
        bt.append([x, f"=B{y0}*D{loans}/(12*$B${rf}+$B${rf + 1}*D{loans}*(1+A{len(bt) + 1}))-1"])
    return {"h0": h0, "h1": h1, "y0": y0, "y1": y1}


def shared_top_groups(costs, groups, k=6):
    score = {x: 0.0 for x in groups}
    lic = sum(r[3] / (1.11 if r[4] == "Y" else 1) / 12 for r in INPUTS if r[1] == "shared" and r[3]) * 0.78
    for r in costs:
        if r[2] == "shared":
            score[r[4]] += r[5] if isinstance(r[5], (int, float)) else lic / len(groups)
    return sorted(groups, key=lambda x: -score[x])[:k]


def cto_grid(bud, bt, top, groups, prow):
    """CTO view: charts on the left, their data (formulas) from column AA."""
    OFF = 26
    rows = [["CTO view: Bravo + LORA unit economics. Charts read the tables from column AA to the right."]]
    charts = []
    n = len(MONTHS) + 1
    mean, (ra, rc, rf, rl) = bt["mean"], (bt["block"][0], bt["block"][0] + 1, bt["block"][0] + 2, bt["block"][0] + 3)
    yb, yl, yh = bud["year"]["Base"], bud["year"]["Low"], bud["year"]["High"]
    bn = lambda cell: f'TEXT({cell}/1000000000,"0.0")'
    rows += [
        [],
        ["HOW TO PREDICT NEXT YEAR'S BUDGET"],
        ["Recommendation: budget = fixed contracts + known contract step changes + fixed part of usage + a small cost per "
         "extra loan (the 'Budget 2027' tab). Use cost per loan to track efficiency, not to build the budget."],
        ["Method", "Average error, one month ahead", '="Block test: fit first "&Backtest!B' + str(bt["n_cell"])
         + '&" months, predict the rest"', "What it means"],
        ["Cost per loan x expected loans (last month's rate)", f"=Backtest!H{mean}", f"=Backtest!C{rc}",
         "Over-predicts when volume grows, because most cost is fixed"],
        ["Cost per loan x expected loans (average rate so far)", f"=Backtest!I{mean}", "",
         "Worst of the simple methods: old, higher rates drag it up"],
        ["Fixed + variable fit (the Budget 2027 method)", f"=Backtest!J{mean}", f"=Backtest!C{rf}",
         "Poor with 3 months of data, 2-4% once it had 5+; improves every month"],
        ["Last month's cost, unchanged", f"=Backtest!K{mean}", f"=Backtest!C{rl}",
         "Good one month ahead, but blind to growth and to contract changes"],
        [f'="Why: from {MONTHS[0]} to {MONTHS[-1]} loans rose "&TEXT(Summary!AB{n}/Summary!AB2-1,"0%")&" but cost only "'
         f'&TEXT(Summary!AA{n}/Summary!AA2-1,"0%")&". Most of the cost is fixed, so cost per loan falls as volume grows."'],
        ["Every backtest uses the month's REAL loans. A real budget also has to guess the loans, and with cost per loan x loans "
         "that guess passes almost 1-to-1 into the budget."],
        ["No method can see contract step changes (ArangoDB renewal, Datadog Year 2 minimum, Temporal renewal). "
         "Budget 2027 adds them on top."],
        ["=\"Budget 2027 (base): Rp\"&" + bn(f"'Budget 2027'!E{yb}") + "&\"bn for the year; low Rp\"&"
         + bn(f"'Budget 2027'!E{yl}") + "&\"bn, high Rp\"&" + bn(f"'Budget 2027'!E{yh}")
         + "&\"bn. Fixed part Rp\"&" + f"TEXT('Budget 2027'!H{yb}/12000000000,\"0.00\")" + "&\"bn a month.\""],
        [f"=\"Exchange rate: USD/IDR \"&TEXT('Budget 2027'!B{bud['a']['fx27']},\"#,##0\")&\" for 2027 (Finance estimate; the real rate "
         f"depends on the payment date), against \"&TEXT('Budget 2027'!B{bud['a']['fx26']},\"#,##0\")&\" behind the 2026 amounts.\""],
        ["=\"If the CTO budgets with cost per loan x loans: the 2027 error runs from \"&TEXT(MIN(Backtest!C" + str(bt["cpl"]["y0"])
         + ":E" + str(bt["cpl"]["y1"]) + "),\"+0%;-0%\")&\" to \"&TEXT(MAX(Backtest!C" + str(bt["cpl"]["y0"]) + ":E"
         + str(bt["cpl"]["y1"]) + "),\"+0%;-0%\")&\" (3 rates x 3 scenarios), and the error grows by about \"&TEXT(SLOPE(Backtest!B"
         + str(bt["cpl"]["h0"]) + ":B" + str(bt["cpl"]["h1"]) + ",Backtest!A" + str(bt["cpl"]["h0"]) + ":A" + str(bt["cpl"]["h1"])
         + ")*100,\"0.0\")&\" points per month ahead.\""],
        ["These figures are live formulas: re-run monthly. The Backtest tab extends as months are added."],
        [],
    ]
    txt_rows = len(rows)

    def put(vals):
        rows.append([None] * OFF + vals)
        return len(rows)

    def block(hdr, lines):
        h = put(hdr)
        for ln in lines:
            put(ln)
        return h, len(rows)

    C = lambda i: OFF + 1 + i  # 1-based column of the i-th value in a block
    h1, l1 = block(["Month", "Bravo orchestration", "Bravo part of Shared", "LORA orchestration", "LORA part of Shared",
                    "Company cost per loan", "Bravo cost per loan", "LORA cost per loan", "Company cost of unique loans",
                    "Company re-processing cost", "Company cost per loan incl. per-call vendors"],
                   [[m, f"=Summary!B{i}", f"=Summary!I{i}", f"=Summary!C{i}", f"=Summary!J{i}", f"=Summary!AC{i}",
                     f"=Summary!M{i}", f"=Summary!N{i}", f"=Summary!AA{i}-Summary!AD{i}", f"=Summary!AD{i}",
                     f'=IF(Summary!AJ{i}="",NA(),Summary!AJ{i})']
                    for i, m in enumerate(MONTHS, start=2)])
    put([])
    h2, l2 = block([f"{MONTHS[-1]} (latest month)", "Rp"],
                   [[lbl, f"=Summary!{c}{n}"] for lbl, c in [("Bravo orchestration", "B"), ("Bravo part of Shared", "I"),
                                                              ("LORA orchestration", "C"), ("LORA part of Shared", "J")]])
    put([])
    sb_row = {x: i + 2 for i, x in enumerate(groups)}
    sb_total = len(groups) + 2
    h3, l3 = block(["Month"] + top + ["Other Shared"],
                   [[m] + [f"='Shared breakdown'!{col(j + 2)}{sb_row[x]}" for x in top]
                    + [f"='Shared breakdown'!{col(j + 2)}{sb_total}-" + "-".join(f"'Shared breakdown'!{col(j + 2)}{sb_row[x]}" for x in top)]
                    for j, m in enumerate(MONTHS)])
    put([])
    h4, l4 = block(["Month", "Company cost per loan (actual, then projected)"],
                   [[m, f"=Projection!W{prow[m]}"] for m in MONTHS + PROJ_MONTHS])
    put([])
    bl = bud["blocks"]
    h5, l5 = block(["Month", "Low", "Base", "High"],
                   [[m, f"='Budget 2027'!K{bl['Low'][0] + k}", f"='Budget 2027'!K{bl['Base'][0] + k}",
                     f"='Budget 2027'!K{bl['High'][0] + k}"] for k, m in enumerate(M27)])
    put([])
    h6, l6 = block(["Scenario", "Bravo orchestration", "LORA orchestration", "Shared"],
                   [[s, f"='Budget 2027'!B{bud['year'][s]}", f"='Budget 2027'!C{bud['year'][s]}", f"='Budget 2027'!D{bud['year'][s]}"]
                    for s in ["Low", "Base", "High"]])
    put([])
    h7, l7 = block(["Month", "Fixed", "Variable"],
                   [[m, f"='Budget 2027'!S{bl['Base'][0] + k}", f"='Budget 2027'!T{bl['Base'][0] + k}"] for k, m in enumerate(M27)])
    put([])
    h8, l8 = block(["Month", "Actual", "Cost per loan x loans (last month)", "Cost per loan x loans (average)",
                    "Fixed + variable fit", "Last month, flat"],
                   [[f"=Backtest!A{r}", f"=Backtest!B{r}"] + [f'=IF(Backtest!{c}{r}="",NA(),Backtest!{c}{r})' for c in "DEFG"]
                    for r in range(bt["first"] + 3, bt["last"] + 1)])
    put([])
    h9, l9 = block(["Months ahead", "Average error", "Smallest", "Largest"],
                   [[f"=Backtest!A{r}", f"=Backtest!B{r}", f"=Backtest!C{r}", f"=Backtest!D{r}"]
                    for r in range(bt["cpl"]["h0"], bt["cpl"]["h1"] + 1)])

    spec = [  # title, type, stacked, header row, last row, series (block-relative, 1 = first value column)
        ("1. Company cost per month: who uses it", "bar", True, h1, l1, [1, 2, 3, 4]),
        (f"2. Where the money went, {MONTHS[-1]}", "pie", False, h2, l2, [1]),
        ("3. Cost per loan: company, Bravo, LORA", "line", False, h1, l1, [5, 6, 7]),
        ("4. Shared cost: the biggest items", "bar", True, h3, l3, list(range(1, len(top) + 2))),
        ("5. Company cost: unique loans vs re-processing", "bar", True, h1, l1, [8, 9]),
        ("6. Company cost per loan: actual, then projected to Dec 2027", "line", False, h4, l4, [1]),
        ("7. Budget 2027: company monthly total, low / base / high", "line", False, h5, l5, [1, 2, 3]),
        ("8. Budget 2027: yearly Bravo / LORA / Shared per scenario", "bar", True, h6, l6, [1, 2, 3]),
        ("9. Budget 2027 base: fixed vs variable", "bar", True, h7, l7, [1, 2]),
        ("10. Backtest: actual company cost vs four ways to predict it", "line", False, h8, l8, [1, 2, 3, 4, 5]),
        ("11. Company cost per loan, with and without per-call vendors", "line", False, h1, l1, [5, 10]),
        ("12. Cost per loan x loans: error by months ahead", "bar", False, h9, l9, [1, 2, 3]),
    ]
    for i, (title, typ, stacked, h, l, series) in enumerate(spec):
        charts.append({"title": title, "type": typ, "stacked": stacked, "tab": "CTO view", "hdr": h, "last": l,
                       "cat": C(0), "series": [C(s) for s in series], "anchor": (txt_rows + 1 + (i // 2) * 20, 0 if i % 2 == 0 else 6)})
    return rows, charts


README = [
    "BFI Unit economics - Bravo vs LORA (private). Built 25 Sep 2026, LORA counts from ArangoDB since 28 Sep 2026.",
    "",
    "WHAT IT SHOWS",
    "Monthly platform cost per loan, Feb-Aug 2026, with a projection to Dec 2027.",
    "ONE LOAN = one unique customer (NIK) + product in the month, on both platforms. Repeat submissions,",
    "  reprocess chains, re-originations, unverified starts and rewinds are NOT extra loans: their cost is",
    "  shown as 're-processing cost' and is carried by the unique loans.",
    "Bravo orchestration = ms-bpm pods + BPM Cloud SQL (conventional + Sharia), prod.",
    "LORA orchestration = GKE squad=lora + ArangoDB GKE (prod) + Temporal + ArangoDB licence + Clickhouse + Metered.ca.",
    "Shared = everything else both platforms use: the rest of bravo-project-prod, plus the Bravo+LORA share of Datadog,",
    "  Coralogix, other unattributed Marketplace charges, and dev/platform licences.",
    "Shared is split by processing load: Bravo % = Bravo apps / (Bravo apps + LORA LPW workflows).",
    "Cost per loan = (orchestration + that platform's part of Shared) / its unique loans.",
    "Re-processing cost = platform cost x (1 - unique loans / processing load) (load: Bravo rows, LORA LPW workflows).",
    "Cost per application row / per verified submission are kept next to it for comparison.",
    "Non-prod (bravo-project-nonprod) is shown apart and is NOT in cost per application.",
    "Per-call vendors (SMS, WhatsApp, EKYC, credit bureaus) are on their own tab and NOT in the headline. Summary AF-AJ adds",
    "  them as a second figure: cost per loan incl. per-call vendors, only for months with every included invoice.",
    "",
    "COMPANY FIGURES (Summary AA-AE)",
    "Company = Bravo + LORA estate: Bravo orchestration + LORA orchestration + Shared (= both parts of Shared).",
    "Company cost per loan = company total / (Bravo unique loans + LORA unique loans). A customer applying for the same",
    "  product on both platforms in one month counts once on each; this is expected to be rare and is not de-duplicated.",
    "",
    "PER-CALL VENDORS (Vendors per call)",
    "Finance's invoice files (Drive): 'Tracking Invoice vendor SMS.xlsx' and 'Rekapitulasi Penggunaan Yellow Ai'.",
    "LORA direct: Vonage WhatsApp key 4ace03fe and the Yellow.ai Digital Partnership tab. Bravo direct: Yellow.ai Bravo and",
    "  Sharia tabs (the Bravo tab's marketing conversations are a separate, flagged row). All-BFI SMS (Vonage OTP/regular/",
    "  notification keys, ADA, Brahmayasa) is split with sms_bravo / sms_lora on 'Allocation keys' (Datadog send traces).",
    "Excluded: Tele RO WhatsApp (Vonage and Yellow.ai) and the other Yellow.ai business units (Collection, Customer Care, ...).",
    "ADA and Brahmayasa do not state their tax basis; treated as incl. VAT.",
    "EKYC and credit bureaus (Advance AI, VIDA, CBI, Pefindo; Finance's 'Summary Invoice+Details E-KYC'): LORA gets its",
    "  measured share of calls; Bravo 0 (no call traces back to BPM); the rest is not attributed. Pefindo Jan-Feb awaited.",
    "",
    "BUDGET 2027 (Budget 2027 tab)",
    "A: fixed contracts with the known step changes (ArangoDB quote, Temporal renewal, Apigee renewal, GitHub/Snyk/Codacy",
    "  renewal months with an uplift %). B: usage costs fitted on the actual months as fixed part + cost per extra unit",
    "  of load (override cells if a fit looks wrong). C: expected unique loans per month for low / base / high (type over",
    "  the defaults). Load per loan turns loans into processing load; lowering it models fewer repeat applications.",
    "D: monthly budget per scenario. E: yearly totals, and a comparison with the straight-line Projection tab.",
    "Exchange rate: USD-priced contracts are re-priced at the 2027 USD/IDR rate (Finance: Rp18,000 for estimates) from",
    "  their renewal month; GCP and Datadog usage too while the Y/N switch is Y. 2026 amounts are taken at Rp16,000",
    "  (IT budget) except Temporal (USD 100,000 paid as Rp1,679,950,003). Rupiah quotes (ArangoDB, Apigee) are not re-priced.",
    "",
    "BACKTEST (Backtest tab)",
    "The block 'If the budget is cost per loan x expected loans' shows the error by months ahead (2026 history), the 2027",
    "  error for 3 rates x 3 scenarios against Budget 2027, the two errors that cancel in the base case, and a loans-miss table.",
    "Predicts each known month from the months before it and compares with the actual company cost, for four methods:",
    "  cost per loan x loans (last month / average), fixed + variable fit, and last month flat. Plus a block test.",
    "",
    "APPLICATION COUNTS (UTC calendar months)",
    "Bravo: Bravo team's query 2 on public.application (deleted=false), conventional + Sharia BPM, read-only.",
    "  SELECT DATE_TRUNC('month', created_at)::DATE, COUNT(id) FROM application WHERE deleted=false GROUP BY 1",
    "LORA: prod ArangoDB, database partnership-ndf-v2, collection doc_pending (one document per LPW workflow;",
    "  _key = workflow ID = application UUID; documents are never deleted). Read-only user, via aql.sh.",
    "  LORA applications = documents with data.submission_date set, by month of submission_date (verified submissions).",
    "  LORA LPW workflows = all documents, by month of version.created_at. LTW (the task-worker pair) is not counted.",
    "  LORA unique loans = distinct customer NIK + product among the month's verified submissions.",
    "Bravo unique loans: distinct customer.identity_number (NIK) + loan.product_id, joined from public.application",
    "  (application.customer_id is not a person: BPM copies the customer row for every application and reprocess).",
    "  Cross-check: Temporal Usage 'Workflows' actions / 2 (Apr-Aug) and Temporal workflow count on single days.",
    "  These replace the earlier Temporal-based LORA numbers. LORA history starts 26 Aug 2025.",
    "",
    "COST SOURCES",
    "GCP tiers: FinOps API (bfi-finops-dashboard), net of credits, labels k8s-label/app, k8s-label/squad, crossplane-name.",
    "Project and service totals: SRE sheet 'GCP Billing - 2026' (invoice view). FinOps vs invoice gap is kept as a row.",
    "Licences: CTO's 'List Budget Infomation Technology 2026.xlsx' (Drive 1b2wTxsUtgYZHH8gWJlk7iC6W0RkUqfLc) - paid amount where shown, else budget; VAT removed (/1.11); /12.",
    "Temporal: contract Rp1,679,950,003 / 12. The one-off March credit line on the GCP bill is excluded.",
    "Datadog: actual monthly GCP line (usage-billed). From Oct 2026 the Year 2 commitment is the projection floor.",
    "",
    "ALLOCATION KEYS (edit on 'Allocation keys')",
    "datadog: average of logs (97%), APM spans (86%), containers (67%) belonging to Bravo+LORA.",
    "dev_tools: Bravo+LORA share of active GitHub repos (78%).",
    "gcp_spend: Bravo projects' share of the project-attributed GCP bill, per month.",
    "",
    "CAVEATS",
    "January 2026 is left out: FinOps has almost no line items for it.",
    "Licence amounts are budgets unless marked 'paid'; each is applied to every month (renewals assumed continuous).",
    "Projections are straight lines over Feb-Aug 2026 (7 months); treat them as a guide, not a forecast.",
    "Unique loans are counted per month: a customer who applies again next month counts once in each month.",
    "Loans are not the value unit; the value split between platforms is still unconfirmed.",
    "Never quote the withdrawn 'LORA Rp1,350 vs Bravo Rp21,256' or '227x' figures.",
    "",
    "EDITING",
    "Yellow cells on 'Inputs', 'Allocation keys' (B2:B3) and 'Vendors per call' (column E) are yours to edit.",
    "A monthly re-run rewrites every tab except 'Inputs'.",
]

RP = {"type": "NUMBER", "pattern": "#,##0"}
PCT = {"type": "PERCENT", "pattern": "0.0%"}
X2 = {"type": "NUMBER", "pattern": "0.00"}


def push(g):
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets()
    meta = svc.get(spreadsheetId=SHEET_ID).execute()
    have = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    reqs = []
    if "Summary" not in have and "Sheet1" in have:
        reqs.append({"updateSheetProperties": {"properties": {"sheetId": have["Sheet1"], "title": "Summary"}, "fields": "title"}})
        have["Summary"] = have.pop("Sheet1")
    for t in TABS:
        if t not in have:
            reqs.append({"addSheet": {"properties": {"title": t}}})
    if reqs:
        svc.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
    meta = svc.get(spreadsheetId=SHEET_ID, fields="sheets(properties,charts(chartId))").execute()
    sid = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    charts = [c["chartId"] for s in meta["sheets"] for c in s.get("charts", [])]

    inputs_existing = svc.values().get(spreadsheetId=SHEET_ID, range="Inputs!A1:A3").execute().get("values")
    data = []
    for t in TABS:
        if t == "Inputs" and inputs_existing:
            continue
        svc.values().clear(spreadsheetId=SHEET_ID, range=f"'{t}'").execute()
        data.append({"range": f"'{t}'!A1", "values": [[("" if c is None else c) for c in row] for row in g[t]]})
    svc.values().batchUpdate(spreadsheetId=SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": data}).execute()

    reqs = [{"deleteEmbeddedObject": {"objectId": c}} for c in charts]

    def fmt(tab, r0, r1, c0, c1, nf):
        reqs.append({"repeatCell": {"range": {"sheetId": sid[tab], "startRowIndex": r0, "endRowIndex": r1,
                                              "startColumnIndex": c0, "endColumnIndex": c1},
                                    "cell": {"userEnteredFormat": {"numberFormat": nf}}, "fields": "userEnteredFormat.numberFormat"}})

    def fill(tab, r0, r1, c0, c1, rgb=(1, 0.95, 0.6)):
        reqs.append({"repeatCell": {"range": {"sheetId": sid[tab], "startRowIndex": r0, "endRowIndex": r1,
                                              "startColumnIndex": c0, "endColumnIndex": c1},
                                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": rgb[0], "green": rgb[1], "blue": rgb[2]}}},
                                    "fields": "userEnteredFormat.backgroundColor"}})

    for t in TABS:
        if t in ("Read me", "CTO view"):
            continue
        reqs.append({"updateSheetProperties": {"properties": {"sheetId": sid[t], "gridProperties": {"frozenRowCount": 1}},
                                               "fields": "gridProperties.frozenRowCount"}})
        reqs.append({"repeatCell": {"range": {"sheetId": sid[t], "startRowIndex": 0, "endRowIndex": 1},
                                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "wrapStrategy": "WRAP"}},
                                    "fields": "userEnteredFormat.textFormat.bold,userEnteredFormat.wrapStrategy"}})
    n = len(MONTHS) + 1
    fmt("Summary", 1, n, 1, 7, RP); fmt("Summary", 1, n, 7, 8, PCT); fmt("Summary", 1, n, 8, 15, RP)
    fmt("Summary", 1, n, 15, 16, PCT); fmt("Summary", 1, n, 16, 17, RP); fmt("Summary", 1, n, 17, 18, PCT)
    fmt("Summary", 1, n, 18, 30, RP); fmt("Summary", 1, n, 30, 31, PCT); fmt("Summary", 1, n, 31, 36, RP)
    for t in ("CTO view", "Budget 2027", "Backtest"):
        fmt(t, 1, len(g[t]), 1, 40, RP)
    nr = len(g["Re-processing"])
    fmt("Re-processing", 1, nr, 1, 6, RP); fmt("Re-processing", 1, nr, 6, 7, X2); fmt("Re-processing", 1, nr, 7, 8, PCT)
    fmt("Re-processing", 1, nr, 8, 11, RP); fmt("Re-processing", 1, nr, 11, 12, PCT)
    fmt("Re-processing", 1, nr, 12, 14, RP); fmt("Re-processing", 1, nr, 14, 15, PCT); fmt("Re-processing", 1, nr, 15, 17, RP)
    fmt("Costs", 1, len(g["Costs"]), 5, 6, RP); fmt("Costs", 1, len(g["Costs"]), 7, 8, PCT); fmt("Costs", 1, len(g["Costs"]), 8, 9, RP)
    fmt("Shared breakdown", 1, len(g["Shared breakdown"]), 1, n, RP)
    fmt("Applications", 1, len(g["Applications"]), 1, 15, RP)
    fmt("Allocation keys", 1, 10, 1, 2, PCT); fmt("Allocation keys", 12, 30, 1, 3, RP); fmt("Allocation keys", 12, 30, 3, 5, PCT)
    fmt("Allocation keys", 12, 30, 5, 6, RP); fmt("Allocation keys", 12, 30, 6, 7, PCT)
    fmt("Inputs", 1, len(g["Inputs"]), 3, 4, RP); fmt("Inputs", 1, len(g["Inputs"]), 5, 6, RP); fmt("Inputs", 1, len(g["Inputs"]), 8, 9, RP)
    fmt("Vendors per call", 1, len(g["Vendors per call"]), 6, 22, RP)
    fmt("Projection", 1, len(g["Projection"]), 3, 13, RP); fmt("Projection", 1, len(g["Projection"]), 13, 14, PCT)
    fmt("Projection", 1, len(g["Projection"]), 14, 20, RP)
    fmt("Checks", 1, len(g["Checks"]), 2, 4, RP); fmt("Checks", 1, len(g["Checks"]), 4, 5, {"type": "NUMBER", "pattern": "0.00%"})
    if not inputs_existing:
        fill("Inputs", 1, len(INPUTS) + 1, 3, 5)
        miss = [i for i, r in enumerate(INPUTS, start=1) if r[3] is None]
        for i in miss:
            fill("Inputs", i, i + 1, 0, 11, (1, 0.8, 0.8))
    fill("Allocation keys", 1, 3, 1, 2)
    fill("Allocation keys", 6, 8, 1, 2)
    for t, w in [("Summary", 150), ("Costs", 120), ("Inputs", 150), ("Checks", 150), ("Projection", 120), ("Read me", 900)]:
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid[t], "dimension": "COLUMNS", "startIndex": 0, "endIndex": 20},
                                                   "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    def src(tab, c, r0, r1):
        return {"sourceRange": {"sources": [{"sheetId": sid[tab], "startRowIndex": r0, "endRowIndex": r1,
                                             "startColumnIndex": c, "endColumnIndex": c + 1}]}}

    def chart(title, tab, anchor_row, anchor_col, ctype, dom_col, series_cols, r1, stacked=False, anchor_tab=None):
        spec = {"title": title, "basicChart": {
            "chartType": ctype, "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
            "stackedType": "STACKED" if stacked else "NOT_STACKED",
            "domains": [{"domain": src(tab, dom_col, 0, r1)}],
            "series": [{"series": src(tab, c, 0, r1), "targetAxis": "LEFT_AXIS"} for c in series_cols]}}
        reqs.append({"addChart": {"chart": {"spec": spec, "position": {"overlayPosition": {
            "anchorCell": {"sheetId": sid[anchor_tab or tab], "rowIndex": anchor_row, "columnIndex": anchor_col},
            "widthPixels": 720, "heightPixels": 360}}}}})

    chart("Cost per loan (unique customer + product)", "Summary", n + 2, 0, "LINE", 0, [12, 13, 28], n)
    chart("Bravo: cost of unique loans + re-processing cost", "Summary", n + 42, 0, "COLUMN", 0, [24, 14], n, stacked=True)
    chart("LORA: cost of unique loans + re-processing cost", "Summary", n + 42, 6, "COLUMN", 0, [25, 16], n, stacked=True)
    chart("Bravo: orchestration + part of Shared", "Summary", n + 2, 6, "COLUMN", 0, [1, 8], n, stacked=True)
    chart("LORA: orchestration + part of Shared", "Summary", n + 22, 6, "COLUMN", 0, [2, 9], n, stacked=True)
    chart("Cost per loan: actual Feb-Aug 2026, projected to Dec 2027", "Projection", 2, 25, "LINE", 0, [16, 17, 22],
          len(MONTHS) + len(PROJ_MONTHS) + 1)
    for ch in g["_charts"]:
        h, l = ch["hdr"] - 1, ch["last"]
        if ch["type"] == "pie":
            spec = {"title": ch["title"], "pieChart": {"legendPosition": "RIGHT_LEGEND",
                                                     "domain": src(ch["tab"], ch["cat"] - 1, h + 1, l),
                                                     "series": src(ch["tab"], ch["series"][0] - 1, h + 1, l)}}
            reqs.append({"addChart": {"chart": {"spec": spec, "position": {"overlayPosition": {
                "anchorCell": {"sheetId": sid[ch["tab"]], "rowIndex": ch["anchor"][0] - 1, "columnIndex": ch["anchor"][1]},
                "widthPixels": 600, "heightPixels": 360}}}}})
            continue
        spec = {"title": ch["title"], "basicChart": {
            "chartType": "COLUMN" if ch["type"] == "bar" else "LINE", "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
            "stackedType": "STACKED" if ch["stacked"] else "NOT_STACKED",
            "domains": [{"domain": src(ch["tab"], ch["cat"] - 1, h, l)}],
            "series": [{"series": src(ch["tab"], c - 1, h, l), "targetAxis": "LEFT_AXIS"} for c in ch["series"]]}}
        reqs.append({"addChart": {"chart": {"spec": spec, "position": {"overlayPosition": {
            "anchorCell": {"sheetId": sid[ch["tab"]], "rowIndex": ch["anchor"][0] - 1, "columnIndex": ch["anchor"][1]},
            "widthPixels": 600, "heightPixels": 360}}}}})
    svc.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
    print("written:", ", ".join(TABS), "| Inputs preserved" if inputs_existing else "")


def write_xlsx(g, path):
    """Fallback when the Sheets API is blocked: same tabs, formulas, formats and charts as an .xlsx for
    File > Import > Replace spreadsheet (keeps the sheet ID)."""
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    yellow, red = PatternFill("solid", fgColor="FFF299"), PatternFill("solid", fgColor="FFCCCC")
    for t in TABS:
        ws = wb.create_sheet(t)
        for row in g[t]:
            ws.append([("" if c is None else c) for c in row])
        if t not in ("Read me", "CTO view"):
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.font = Font(bold=True)
                c.alignment = Alignment(wrap_text=True, vertical="top")
        for c in range(1, 20):
            ws.column_dimensions[col(c)].width = 110 if t == "Read me" and c == 1 else (40 if c in (1, 4) else 18)
    n = len(MONTHS) + 1
    def nf(t, r0, r1, c0, c1, f):
        for row in wb[t].iter_rows(min_row=r0, max_row=r1, min_col=c0, max_col=c1):
            for c in row:
                c.number_format = f
    R, P = "#,##0", "0.0%"
    nf("Summary", 2, n, 2, 7, R); nf("Summary", 2, n, 8, 8, P); nf("Summary", 2, n, 9, 15, R)
    nf("Summary", 2, n, 16, 16, P); nf("Summary", 2, n, 17, 17, R); nf("Summary", 2, n, 18, 18, P); nf("Summary", 2, n, 19, 30, R)
    nf("Summary", 2, n, 31, 31, P); nf("Summary", 2, n, 32, 36, R)
    nr = len(g["Re-processing"])
    nf("Re-processing", 2, nr, 2, 6, R); nf("Re-processing", 2, nr, 7, 7, "0.00"); nf("Re-processing", 2, nr, 8, 8, P)
    nf("Re-processing", 2, nr, 9, 11, R); nf("Re-processing", 2, nr, 12, 12, P)
    nf("Re-processing", 2, nr, 13, 14, R); nf("Re-processing", 2, nr, 15, 15, P); nf("Re-processing", 2, nr, 16, 17, R)
    nc = len(g["Costs"]); nf("Costs", 2, nc, 6, 6, R); nf("Costs", 2, nc, 8, 8, P); nf("Costs", 2, nc, 9, 9, R)
    nf("Shared breakdown", 2, len(g["Shared breakdown"]), 2, n, R)
    nf("Applications", 2, len(g["Applications"]), 2, 15, R)
    nf("Allocation keys", 2, 10, 2, 2, P); nf("Allocation keys", 13, 30, 2, 3, R); nf("Allocation keys", 13, 30, 4, 5, P)
    nf("Allocation keys", 13, 30, 6, 6, R); nf("Allocation keys", 13, 30, 7, 7, P)
    ni = len(g["Inputs"]); nf("Inputs", 2, ni, 4, 4, R); nf("Inputs", 2, ni, 6, 6, R); nf("Inputs", 2, ni, 9, 9, R)
    nf("Vendors per call", 2, len(VENDOR_INVOICES) + 1, 3, 4, P); nf("Vendors per call", 2, len(VENDOR_INVOICES) + 5, 7, 22, R)
    nf("Allocation keys", 7, 8, 2, 2, "0.0%")
    nf("CTO view", 2, len(g["CTO view"]), 28, 40, R)
    for row in wb["CTO view"].iter_rows(min_row=2):
        if isinstance(row[26].value, str) and row[26].value.startswith("=Backtest!A"):
            for c in row[27:30]:
                c.number_format = P
    nf("Budget 2027", 2, len(g["Budget 2027"]), 2, 20, R); nf("Budget 2027", 2, 3, 2, 2, P)
    nf("Budget 2027", 5, 6, 2, 2, "0.00"); nf("Budget 2027", 8, 9, 2, 2, "0.00")
    bw = wb["Budget 2027"]
    for row in bw.iter_rows(min_row=10):
        lbl = str(row[0].value or "")
        if lbl in INPUTS_NAMES:
            row[2].number_format = P
            row[5].number_format = "0"
    for row in bw.iter_rows(min_row=10):
        if row[1].value in ("D", "E", "G", "H"):
            row[5].number_format = "0.00"; row[4].number_format = "#,##0.0000"; row[7].number_format = "#,##0.0000"
            row[9].number_format = "#,##0.0000"
        if isinstance(row[5].value, str) and row[5].value.startswith("=IF(D"):
            row[5].number_format = P; row[6].number_format = "0.00"
    nf("Backtest", 2, len(g["Backtest"]), 2, 7, R); nf("Backtest", 2, len(g["Backtest"]), 8, 11, P)
    for row in wb["Backtest"].iter_rows(min_row=len(MONTHS) + 3):
        for c in row:
            if isinstance(c.value, str) and (c.value.endswith("-1") or c.value.startswith(("=AVERAGE", "=MIN(", "=MAX("))):
                c.number_format = P
            if isinstance(c.value, float) and c.column == 1 and -1 < c.value < 1:
                c.number_format = "+0%;-0%;0%"
        if row[2].value and str(row[2].value).startswith("=B"):
            row[2].number_format = P
    npj = len(g["Projection"]); nf("Projection", 2, npj, 4, 13, R); nf("Projection", 2, npj, 14, 14, P); nf("Projection", 2, npj, 15, 20, R)
    nf("Checks", 2, len(g["Checks"]), 3, 4, R); nf("Checks", 2, len(g["Checks"]), 5, 5, "0.00%")
    for i, r in enumerate(INPUTS, start=2):
        for c in (4, 5):
            wb["Inputs"].cell(i, c).fill = yellow
        if r[3] is None:
            for c in range(1, 12):
                wb["Inputs"].cell(i, c).fill = red
    for r in (2, 3):
        wb["Allocation keys"].cell(r, 2).fill = yellow
    for r in (7, 8):
        wb["Allocation keys"].cell(r, 2).fill = yellow
    for r in range(2, len(VENDOR_INVOICES) + 2):
        for c in range(7, 15):
            wb["Vendors per call"].cell(r, c).fill = yellow
        if VENDOR_INVOICES[r - 2][0] in ("Advance AI", "VIDA", "CBI (Credit Bureau Indonesia)", "Pefindo Biro Kredit"):
            for c in (3, 4):
                wb["Vendors per call"].cell(r, c).fill = yellow
    for row in bw.iter_rows():
        v0 = row[0].value
        if row[0].row in range(2, 13):
            row[1].fill = yellow
        elif str(v0 or "") in INPUTS_NAMES:
            row[4].fill = yellow; row[5].fill = yellow; row[20].fill = yellow; row[21].fill = yellow
            row[21].number_format = "#,##0.0"; row[22].number_format = "0.000"
        elif row[1].value in ("D", "E", "G", "H"):
            row[6].fill = yellow; row[7].fill = yellow
        elif str(v0 or "") in M27 and isinstance(row[1].value, str) and "Projection!" in row[1].value:
            for c in range(1, 7):
                row[c].fill = yellow
    bt = wb["Backtest"]
    for row in bt.iter_rows():
        if row[0].value == "N (months used to fit)":
            row[1].fill = yellow
    cv = wb["CTO view"]
    for c, w in zip("ABCDE", (58, 22, 30, 60, 18)):
        cv.column_dimensions[c].width = w
    for row in cv.iter_rows(min_row=1, max_row=20, max_col=4):
        if isinstance(row[1].value, str) and row[1].value.startswith("=Backtest!"):
            row[1].number_format = row[2].number_format = "0.0%"
        if row[0].value in ("HOW TO PREDICT NEXT YEAR'S BUDGET", "Method"):
            for c in row:
                c.font = Font(bold=True)
    cv["A1"].font = Font(bold=True, size=13)
    s = wb["Summary"]
    def add(ws, chart, cols, rows, anchor, title, stacked=False):
        chart.title, chart.height, chart.width = title, 9, 18
        for c in cols:
            chart.add_data(Reference(ws, min_col=c, min_row=1, max_row=rows), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=rows))
        if stacked:
            chart.grouping, chart.overlap = "stacked", 100
        ws.add_chart(chart, anchor)
    add(s, LineChart(), [13, 14, 29], n, f"A{n + 3}", "Cost per loan (unique customer + product)")
    add(s, BarChart(), [25, 15], n, f"A{n + 41}", "Bravo: cost of unique loans + re-processing cost", stacked=True)
    add(s, BarChart(), [26, 17], n, f"H{n + 41}", "LORA: cost of unique loans + re-processing cost", stacked=True)
    add(s, BarChart(), [2, 9], n, f"H{n + 3}", "Bravo: orchestration + part of Shared", stacked=True)
    add(s, BarChart(), [3, 10], n, f"H{n + 22}", "LORA: orchestration + part of Shared", stacked=True)
    pj = wb["Projection"]
    add(pj, LineChart(), [17, 18, 23], len(MONTHS) + len(PROJ_MONTHS) + 1, "Z2",
        "Cost per loan: actual Feb-Aug 2026, projected to Dec 2027")
    for ch in g["_charts"]:
        ws = wb[ch["tab"]]
        c = {"bar": BarChart, "line": LineChart, "pie": PieChart}[ch["type"]]()
        c.title, c.height, c.width = ch["title"], 9, 16
        for sc in ch["series"]:
            c.add_data(Reference(ws, min_col=sc, min_row=ch["hdr"], max_row=ch["last"]), titles_from_data=True)
        c.set_categories(Reference(ws, min_col=ch["cat"], min_row=ch["hdr"] + 1, max_row=ch["last"]))
        if ch["stacked"]:
            c.grouping, c.overlap = "stacked", 100
        ws.add_chart(c, f"{col(ch['anchor'][1] + 1)}{ch['anchor'][0]}")
    wb.save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gcp", required=True)
    ap.add_argument("--sre", required=True)
    ap.add_argument("--bravo", required=True)
    ap.add_argument("--lora", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print grid sizes, do not write")
    ap.add_argument("--xlsx", help="write an .xlsx for File > Import > Replace spreadsheet instead of using the Sheets API")
    a = ap.parse_args()
    g = grids(*load(a))
    if a.dry_run:
        for t in TABS:
            print(t, len(g[t]), "rows")
        return
    if a.xlsx:
        write_xlsx(g, a.xlsx)
        return
    push(g)


if __name__ == "__main__":
    main()
