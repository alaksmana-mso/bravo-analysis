#!/usr/bin/env python3
"""Refresh the Status column of the two pull-request tables in docs/logging/README.md.

Usage:  tools/logging_pr_status.py STATUS.json [--date "23 Sep"]

STATUS.json is what tools/poll_fix_logging_prs.py writes: {"polled_at": ..., "prs": [
  {"repo": "bfi-finance/<repo>", "number": N, "state": "open|merged|closed",
   "merged_at": ..., "merged_by": ..., "closed_at": ..., "failing": [job names], "pending": [...]}]}

Only the last column of the two tables (pack one: "| Repo | Pull request | Status (...)",
pack two: "| Repository | Production service | Pull request | What it changes | Status (...)")
is rewritten, plus the "(dd Mon)" in both header cells. Everything else in the README is left alone.
"""
import json, re, sys, pathlib, datetime

GATES = [  # job-name fragment -> how the README names the gate
    (re.compile(r"sonar", re.I), "SonarQube"),
    (re.compile(r"snyk|trivy|container|image|vulnerab|security", re.I), "SNYK / image CVEs"),
    (re.compile(r"codacy.*cover|coverage", re.I), "Codacy coverage"),
    (re.compile(r"codacy", re.I), "Codacy step"),
    (re.compile(r"prettier|format|lint", re.I), "Prettier"),
    (re.compile(r"test", re.I), "unit-test job"),
]
ORDER = ["Codacy coverage", "Codacy step", "Prettier", "SNYK / image CVEs", "SonarQube", "unit-test job"]

def gate_names(failing):
    names = set()
    for f in failing:
        for rx, name in GATES:
            if rx.search(f):
                names.add(name); break
        else:
            names.add(f.split(" (")[0])
    return sorted(names, key=lambda n: (ORDER.index(n) if n in ORDER else 99, n))

def status_text(pr, cutoff_day):
    d = lambda s: datetime.date.fromisoformat(s[:10]).strftime("%-d %b") if s else "?"
    if pr["state"] == "merged":
        return f"**merged {d(pr['merged_at'])}** by the squad"
    if pr["state"] == "closed":
        return f"closed {d(pr['closed_at'])}"
    if pr["pending"]:
        return "open — CI running"
    if not pr["failing"]:
        return "open — CI green"
    return "open — red only on " + ", ".join(gate_names(pr["failing"]))

def main():
    status_path = sys.argv[1]
    date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else datetime.date.today().strftime("%-d %b")
    data = json.load(open(status_path))
    by_key = {(p["repo"].split("/")[-1], p["number"]): p for p in data["prs"]}
    readme = pathlib.Path(__file__).resolve().parent.parent / "docs/logging/README.md"
    lines = readme.read_text().splitlines(keepends=True)
    row_rx = re.compile(r"^\| \[(?P<repo>[^\]]+)\]\([^)]+\.md\) \|(?P<mid>.*)\[#(?P<num>\d+)\]\(https://github\.com/bfi-finance/[^/]+/pull/\d+\)(?P<rest>.*)\|\s*$")
    changed = 0; missing = []
    for i, line in enumerate(lines):
        if line.startswith("| Repo | Pull request | Status") or line.startswith("| Repository | Production service | Pull request | What it changes | Status"):
            lines[i] = re.sub(r"Status \([^)]*\)", f"Status ({date})", line); continue
        m = row_rx.match(line)
        if not m: continue
        pr = by_key.get((m.group("repo"), int(m.group("num"))))
        if not pr:
            missing.append(f"{m.group('repo')}#{m.group('num')}"); continue
        cells = [c for c in line.rstrip("\n").strip().strip("|").split(" | ")]
        cells[-1] = status_text(pr, date)
        new = "| " + " | ".join(c.strip() for c in cells) + " |\n"
        if new != line: lines[i] = new; changed += 1
    readme.write_text("".join(lines))
    print(f"{changed} rows changed; header date -> ({date}); not in status file: {missing or 'none'}")

if __name__ == "__main__":
    main()
