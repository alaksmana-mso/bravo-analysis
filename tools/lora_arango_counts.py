"""Monthly LORA counts from prod ArangoDB (partnership-ndf-v2.doc_pending), read-only.

One document per LPW workflow (_key = workflow ID = application UUID). Two full-collection
queries (no indexes exist), grouped by UTC calendar month:
  lpw_workflows     documents by month of version.created_at (LPW start)
  never_verified    of those, documents with no data.submission_date
  applications      documents by month of data.submission_date (verified submission)
  ndf2w / ndf4w     applications by loan_structure.product_id (2 / 1)
  reoriginated_est  applications minus distinct NIK+product in the month

Runs through ~/.config/mcp-arangodb/aql.sh (credentials stay in lora.env; ARANGO_DB must be
partnership-ndf-v2). Output: CSV at the path given.
"""

import csv
import json
import subprocess
import sys

AQL = "/Users/mac-6000202/.config/mcp-arangodb/aql.sh"

Q_LPW = """
FOR d IN doc_pending
  FILTER d.version.created_at >= @from AND d.version.created_at < @to
  COLLECT m = SUBSTRING(d.version.created_at, 0, 7)
  AGGREGATE lpw = COUNT(1), never_verified = SUM(d.data.submission_date == null ? 1 : 0)
  RETURN { m, lpw, never_verified }
"""

Q_APPS = """
FOR d IN doc_pending
  FILTER d.data.submission_date >= @from AND d.data.submission_date < @to
  COLLECT m = SUBSTRING(d.data.submission_date, 0, 7)
  AGGREGATE apps = COUNT(1),
            ndf2w = SUM(d.data.loan_structure.product_id == 2 ? 1 : 0),
            ndf4w = SUM(d.data.loan_structure.product_id == 1 ? 1 : 0),
            uniq = COUNT_DISTINCT(CONCAT(d.data.customer.ktp.nik, "|", d.data.loan_structure.product_id))
  RETURN { m, apps, ndf2w, ndf4w, reoriginated_est: apps - uniq }
"""


def run(query, bind):
    out = subprocess.run([AQL, query, json.dumps(bind)], capture_output=True, text=True, timeout=900)
    if out.returncode != 0:
        raise SystemExit(f"aql.sh failed ({out.returncode}): {out.stdout[:300]} {out.stderr[:300]}")
    body = json.loads(out.stdout)
    if body.get("error") or body.get("hasMore"):
        raise SystemExit(f"query error or truncated: {str(body)[:300]}")
    return body["result"]


def main(path, start="2025-08-01T00:00:00Z", end="2026-10-01T00:00:00Z"):
    bind = {"from": start, "to": end}
    rows = {}
    for r in run(Q_LPW, bind):
        rows.setdefault(r["m"], {}).update(lpw_workflows=r["lpw"], never_verified=r["never_verified"])
    for r in run(Q_APPS, bind):
        rows.setdefault(r["m"], {}).update(applications=r["apps"], ndf2w=r["ndf2w"], ndf4w=r["ndf4w"],
                                           reoriginated_est=r["reoriginated_est"])
    cols = ["month", "lpw_workflows", "never_verified", "applications", "ndf2w", "ndf4w", "reoriginated_est"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for m in sorted(rows):
            w.writerow([m] + [rows[m].get(c, 0) for c in cols[1:]])
    print(open(path).read())


if __name__ == "__main__":
    main(sys.argv[1])
