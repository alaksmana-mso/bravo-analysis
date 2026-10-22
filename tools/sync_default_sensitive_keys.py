#!/usr/bin/env python3
"""Put DEFAULT_LOG_SENSITIVE_KEYS into every application's env in the Helm values files.

The organization-level GitHub variable DEFAULT_LOG_SENSITIVE_KEYS is the source of the baseline
deny-list that bfi-go-pkg and bfi-java-pkg mask in logged bodies and query strings. Pods cannot see a
GitHub variable, only Helm values, so this script copies the variable's value into each service's
values-<env>.yaml. Run it again whenever the variable changes; it replaces an existing entry.

Layouts handled (text-level edits, the file's own formatting is kept):
  - `extraEnv: |` string block, at any indent (microservices-http.extraEnv, bfi `image:`-keyed charts)
  - `globalEnv: |` string block (LORA Temporal worker charts)
Files with neither block are skipped and listed (infra charts: clamav, kafka, secrets, sqlproxy, UIs, ...).
Apps in NO_LOGGING_LIBRARY_APPS are BFI apps that use neither library: skipped when adding, and
`--remove --only <apps>` takes the entry out of their files.
Apps in SKIP_APPS are third-party or vendor software that never reads the variable. They are left exactly
as they are: an env change only restarts them, and Keycloak runs as one replica (20 Oct 2026, UAT).

Usage:
  sync_default_sensitive_keys.py --value-file keys.txt --repo sre/app-deployment --repo sre/bfi-app-deployment --dry-run
  sync_default_sensitive_keys.py --from-gh --repo sre/app-deployment --env prod
  sync_default_sensitive_keys.py --value-file keys.txt --repo sre/app-deployment --values-file values-prod.yaml --only branch,master
  --env nonprod | prod | all (default all): which values-*.yaml to touch, for staged PRs.
  --from-gh needs a gh token with admin:org (gh variable get DEFAULT_LOG_SENSITIVE_KEYS --org bfi-finance).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

VAR = "DEFAULT_LOG_SENSITIVE_KEYS"
# Third-party or vendor apps: they do not use bfi-go-pkg or bfi-java-pkg, so the variable is useless to them
# and adding it only forces a restart. Never touched, in either direction.
SKIP_APPS = {
    "keycloak",                                     # Keycloak, single replica: a restart stops all logins
    "krakend-gateway", "krakend-gateway-internal",  # KrakenD API gateways
    "airflow",                                      # Apache Airflow
    "filebrowser",                                  # File Browser (StrategyOne)
    "strategyone-batch-ws", "strategyone-lab", "strategyone-modelmgr",
    "strategyone-tus", "strategyone-wsd", "strategyone-wsp",  # vendor StrategyOne
}
# BFI apps whose code uses neither bfi-go-pkg nor a BFI Java logging library (bfi-logging-* or
# bravo-lib-logging), so they never read the variable. Verified 22 Oct 2026 from go.mod / pom.xml on each
# repo's default branch, or, where the repo is not visible, from Datadog span language and manifest env
# names. Re-check an app when it adopts one of the libraries, then remove it here. Skipped when adding;
# `--remove --only <apps>` takes the entry out of their files.
NO_LOGGING_LIBRARY_APPS = {
    # app-deployment, Java on plain logback
    "agreement", "approval-engine", "bpm", "collateral", "core-proxy", "customer", "dominic", "employee",
    "insurance", "journal", "lms-gateway", "master", "product", "repeat-order", "bfi-connect",
    # app-deployment, other languages
    "calculation", "ai-platform", "robot-scrape",
    # bfi-app-deployment: .NET
    "bfi-incentive-net-api", "bfi-payment-net-api", "bfi-syariah-net-api", "bfi-otrs-api", "bfi-otrs-ui",
    # bfi-app-deployment: web front ends
    "bfi-formio-ui", "bfi-omni-middleware-ui", "bfi-panel-dashboard-ui", "bfi-operation-ui", "ms-new-otrs-ui",
    "bfi-website-cms", "bfi-corporate-website",
    # bfi-app-deployment: PHP, Python, Java without a logging library
    "ares", "iad-ams", "pcms", "ms-score-branch-ui", "army", "pmotools", "pmotools2",
    "bfi-jira-data-migration-api", "bfi-insurance-api",
}


class HelmLoader(yaml.SafeLoader):
    """SafeLoader that accepts the custom tags some values files use (e.g. `!string`) as plain values."""


def _any_tag(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


HelmLoader.add_multi_constructor("!", _any_tag)
HelmLoader.add_multi_constructor("tag:", _any_tag)


def load(text: str):
    return yaml.load(text, Loader=HelmLoader)  # noqa: S506 - SafeLoader subclass
BLOCK_RE = re.compile(r"^(?P<indent>\s*)(?P<key>extraEnv|globalEnv):\s*\|\s*$")
ITEM_RE = re.compile(r"^(?P<indent>\s*)- name:\s*(?P<name>\S+)\s*$")


def read_value(args: argparse.Namespace) -> str:
    if args.value:
        raw = args.value
    elif args.value_file:
        raw = Path(args.value_file).read_text()
    elif args.from_gh:
        raw = subprocess.check_output(
            ["gh", "variable", "get", VAR, "--org", "bfi-finance"], text=True
        )
    else:
        sys.exit("give --value, --value-file or --from-gh")
    keys = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]
    if not keys:
        sys.exit("the value is empty")
    return ",".join(keys)


def env_matches(path: Path, which: str) -> bool:
    name = path.name
    if not (name.startswith("values-") and name.endswith(".yaml")):
        return False
    is_prod = name.startswith("values-prod")
    return which == "all" or (which == "prod") == is_prod


def find_block(lines: list[str]) -> tuple[int, int, str, str] | None:
    """Return (header_index, end_index_exclusive, item_indent, key) of the first env block."""
    for i, line in enumerate(lines):
        m = BLOCK_RE.match(line)
        if not m:
            continue
        header_indent = len(m.group("indent"))
        end = i + 1
        item_indent = None
        while end < len(lines):
            cur = lines[end]
            if cur.strip() == "":
                end += 1
                continue
            if len(cur) - len(cur.lstrip(" ")) <= header_indent:
                break
            if item_indent is None:
                im = ITEM_RE.match(cur)
                item_indent = im.group("indent") if im else " " * (header_indent + 2)
            end += 1
        # trailing blank lines belong to the next section, not the block
        while end > i + 1 and lines[end - 1].strip() == "":
            end -= 1
        return i, end, item_indent or " " * (header_indent + 2), m.group("key")
    return None


def upsert(lines: list[str], value: str) -> tuple[list[str], str]:
    """Insert or replace the VAR item in the first env block. Returns (new_lines, action)."""
    found = find_block(lines)
    if found is None:
        return lines, "skipped: no extraEnv/globalEnv block"
    start, end, ind, key = found
    entry = [f'{ind}- name: {VAR}\n', f'{ind}  value: "{value}"\n']
    for j in range(start + 1, end):
        im = ITEM_RE.match(lines[j])
        if im and im.group("name") == VAR:
            # replace the item's value line (the line after the name, or insert one)
            if j + 1 < end and lines[j + 1].lstrip().startswith("value:"):
                if lines[j + 1] == entry[1]:
                    return lines, f"unchanged ({key})"
                return lines[: j + 1] + [entry[1]] + lines[j + 2 :], f"updated ({key})"
            return lines[: j + 1] + [entry[1]] + lines[j + 1 :], f"updated ({key})"
    return lines[:end] + entry + lines[end:], f"added ({key})"


def remove(lines: list[str]) -> tuple[list[str], str]:
    """Delete the VAR item (its name line and value line) from the first env block. Returns (new_lines, action)."""
    found = find_block(lines)
    if found is None:
        return lines, "skipped: no extraEnv/globalEnv block"
    start, end, _, key = found
    for j in range(start + 1, end):
        im = ITEM_RE.match(lines[j])
        if im and im.group("name") == VAR:
            stop = j + 2 if j + 1 < end and lines[j + 1].lstrip().startswith("value:") else j + 1
            return lines[:j] + lines[stop:], f"removed ({key})"
    return lines, f"absent ({key})"


def block_items(lines: list[str]) -> list:
    """Parse the first env block's own text (dedented) as a YAML list, independent of the rest of the file."""
    found = find_block(lines)
    if found is None:
        return []
    start, end, _, _ = found
    # Some live files carry trailing tabs inside the block; Helm's parser tolerates them, PyYAML does not.
    # They are stripped for this check only, never rewritten in the file.
    body = [l.rstrip("\t ") + "\n" if l.strip() else l for l in lines[start + 1 : end]]
    indent = min(len(l) - len(l.lstrip(" ")) for l in body if l.strip())
    return load("".join(l[indent:] if l.strip() else l for l in body)) or []


def check(path: Path, lines: list[str], expected: int = 1) -> str:
    """Return a note saying how much of the file could be checked.

    Best case the whole file parses. Failing that, the env block alone is parsed. Failing that too (tabs
    inside the block, Helm syntax), the VAR item is counted textually, which is enough since the script
    only ever appends two well-formed lines.
    """
    try:
        items = block_items(lines)
        names = [item.get("name") for item in items if isinstance(item, dict)]
        note = ""
    except yaml.YAMLError:
        found = find_block(lines)
        start, end = found[0], found[1]
        names = [ITEM_RE.match(l.rstrip("\t \n") + "\n").group("name")
                 for l in lines[start + 1 : end] if ITEM_RE.match(l.rstrip("\t \n") + "\n")]
        note = "(env block is not strict YAML, tabs; item counted textually)"
    if names.count(VAR) != expected:
        raise ValueError(f"{path}: expected {expected} {VAR} in the env block, found {names.count(VAR)}")
    if note:
        return note
    try:
        load("".join(lines))
        return ""
    except yaml.YAMLError:
        return "(file has non-YAML syntax; only the env block was checked)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", required=True, help="deployment repo path, repeatable")
    ap.add_argument("--env", choices=["all", "prod", "nonprod"], default="all")
    ap.add_argument("--value")
    ap.add_argument("--value-file")
    ap.add_argument("--from-gh", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma-separated app folders to touch; others are left alone (for staged batches)")
    ap.add_argument("--values-file", help="touch only values files with exactly this name, e.g. values-prod-sharia.yaml")
    ap.add_argument("--remove", action="store_true", help="take the entry out instead of adding it (needs --only)")
    args = ap.parse_args()
    if args.remove and not args.only:
        sys.exit("--remove needs --only <apps>, so it never strips the whole estate by accident")
    value = None if args.remove else read_value(args)
    only = {a.strip() for a in args.only.split(",") if a.strip()} if args.only else None

    counts: dict[str, int] = {}
    for repo in args.repo:
        root = Path(repo)
        for chart in sorted(root.glob("*/Chart.yaml")):
            if only is not None and chart.parent.name not in only:
                continue
            if chart.parent.name in SKIP_APPS:
                counts["skipped-app"] = counts.get("skipped-app", 0) + 1
                print(f"  {'skipped: third-party app (SKIP_APPS)':<38} {chart.parent.relative_to(root.parent)}")
                continue
            if chart.parent.name in NO_LOGGING_LIBRARY_APPS and not args.remove:
                counts["skipped-no-library"] = counts.get("skipped-no-library", 0) + 1
                print(f"  {'skipped: no logging library':<38} {chart.parent.relative_to(root.parent)}")
                continue
            for path in sorted(chart.parent.glob("values-*.yaml")):
                if not env_matches(path, args.env) or (args.values_file and path.name != args.values_file):
                    continue
                lines = path.read_text().splitlines(keepends=True)
                new_lines, action = remove(lines) if args.remove else upsert(lines, value)
                counts[action.split(" ")[0]] = counts.get(action.split(" ")[0], 0) + 1
                rel = path.relative_to(root.parent)
                if action.startswith("skipped"):
                    print(f"  {action:<38} {rel}")
                    continue
                if new_lines != lines:
                    note = check(path, new_lines, expected=0 if args.remove else 1)
                    if not args.dry_run:
                        path.write_text("".join(new_lines))
                    print(f"  {action:<38} {rel} {note}")
    print("summary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())), "(dry run)" if args.dry_run else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
