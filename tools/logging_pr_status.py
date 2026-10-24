#!/usr/bin/env python3
"""Refresh the Status column of the two pull-request tables in docs/logging/history.md
(moved there from README.md on 7 October 2026; README.md is still scanned in case a table returns).

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

# Why a pull request was closed, where the closing comment says so (repo, number) -> text
CLOSE_NOTES = {
    ("bravo-partnership-service", 2367): "superseded by the squad's own [#2386](https://github.com/bfi-finance/bravo-partnership-service/pull/2386)",
    ("lora-task-service", 1363): "dropped: the change relied on debug logging in production",
    ("bravo-user-iam-service", 521): "replaced by the one-flag fix #525",
    ("app-deployment", 14252): "the services trace with OpenTelemetry, which ignores DD_TRACE_HEADER_TAGS; replaced by the span attribute in bfi-go-pkg#185",
    ("app-deployment", 14329): "replaced by a stack of 8 batch PRs, [#14466](https://github.com/bfi-finance/app-deployment/pull/14466) to [#14473](https://github.com/bfi-finance/app-deployment/pull/14473) (merge bottom first, about 15 minutes apart)",
    ("bfi-app-deployment", 4115): "replaced by a stack of 4, [bfi-app-deployment#4151](https://github.com/bfi-finance/bfi-app-deployment/pull/4151) to [#4154](https://github.com/bfi-finance/bfi-app-deployment/pull/4154)",
}

# A cell the tool itself could have written. Anything else is hand-written detail, and is kept
# as long as the pull request is still in the same state (merged / closed / open). 21 October 2026.
TOOL_CELL = re.compile(r"^(\*\*merged \d+ \w+\*\*(, .*)?|closed \d+ \w+(, .*)?|open(, \*\*approved\*\*)? — .*)$")
def state_class(cell):
    return "merged" if cell.startswith("**merged") else "closed" if cell.startswith("closed") else "open"

# Merged pull requests that were later reverted, (repo, number) -> text
REVERT_NOTES = {
    ("bravo-bpm-service", 10463): "reverted the same day in #10578: not finished in review and testing",
    ("bravo-bpm-service", 10571): "reverted the same day in #10578: not finished in review and testing",
}

def status_text(pr, cutoff_day):
    d = lambda s: datetime.date.fromisoformat(s[:10]).strftime("%-d %b") if s else "?"
    if pr["state"] == "merged":
        note = REVERT_NOTES.get((pr["repo"].split("/")[-1], pr["number"]))
        return f"**merged {d(pr['merged_at'])}**" + (f", {note}" if note else "")
    if pr["state"] == "closed":
        note = CLOSE_NOTES.get((pr["repo"].split("/")[-1], pr["number"]))
        return f"closed {d(pr['closed_at'])}" + (f", {note}" if note else "")
    head = "open, **approved**" if pr.get("approvals") else "open"
    if pr["pending"]:
        return head + " — CI running"
    if not pr["failing"]:
        return head + " — CI green"
    return head + " — red only on " + ", ".join(gate_names(pr["failing"]))

def main():
    status_path = sys.argv[1]
    date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else datetime.date.today().strftime("%-d %b")
    data = json.load(open(status_path))
    by_key = {(p["repo"].split("/")[-1], p["number"]): p for p in data["prs"]}
    for name in ("history.md", "README.md"):
        refresh(pathlib.Path(__file__).resolve().parent.parent / "docs/logging" / name, by_key, date)

def refresh(readme, by_key, date):
    lines = readme.read_text().splitlines(keepends=True)
    row_rx = re.compile(r"^\| \[(?P<repo>[^\]]+)\]\([^)]+\) \|(?P<mid>.*?)\[#(?P<num>\d+)\]\(https://github\.com/bfi-finance/[^/]+/pull/\d+\)(?P<rest>.*)\|\s*$")
    changed = 0; missing = []; kept = []
    for i, line in enumerate(lines):
        if line.startswith(("| Repo | Pull request | Status", "| Repository | Production service | Pull request | What it changes | Status",
                            "| Service | Squad | Pull request | What it fixes | Status", "| Repository | Pull request | What it does | Status",
                            "| Repository | Base branch | Pull request | Why | Reviewers | Status")):
            lines[i] = re.sub(r"Status \([^)]*\)", f"Status ({date})", line); continue
        m = row_rx.match(line)
        if not m: continue
        pr = by_key.get((m.group("repo"), int(m.group("num"))))
        if not pr:
            missing.append(f"{m.group('repo')}#{m.group('num')}"); continue
        cells = [c for c in line.rstrip("\n").strip().strip("|").split(" | ")]
        new_cell = status_text(pr, date); old_cell = cells[-1].strip()
        if not TOOL_CELL.match(old_cell) and state_class(old_cell) == state_class(new_cell):
            kept.append(f"{m.group('repo')}#{m.group('num')}"); continue  # hand-written cell, same state: keep it
        cells[-1] = new_cell
        new = "| " + " | ".join(c.strip() for c in cells) + " |\n"
        if new != line: lines[i] = new; changed += 1
    readme.write_text("".join(lines))
    print(f"{readme.name}: {changed} rows changed; header date -> ({date}); not in status file: {missing or 'none'}; hand-written cells kept: {kept or 'none'}")

if __name__ == "__main__":
    main()
