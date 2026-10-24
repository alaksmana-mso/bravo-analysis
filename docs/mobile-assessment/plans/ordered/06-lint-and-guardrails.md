**Priority 6 of 13.** Phase 1. The ratchet checker must exist before the architecture work starts, so new debt stops growing.

## Goal

The architecture rules are checked by tools, not only by reviewers. A PR that adds a feature-to-feature import, a Flutter import in domain code, or a vendor SDK import outside its adapter fails CI. Reviewers and AI tools read the same written rules.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`.

### Lint

- Root `analysis_options.yaml` includes `package:lint/strict.yaml` (`lint: ^2.1.0` in the root `pubspec.yaml`).
- It excludes `*.g.dart`, `*.freezed.dart`, `*.mapper.dart`. It turns off `unnecessary_parenthesis` and `avoid_redundant_argument_values`, and adds `prefer_single_quotes` and `sort_constructors_first`.
- The three packages (`digital`, `data/customer`, `shared_lib/core`) have no own `analysis_options.yaml`. They use the root file.
- `flutter_lints: ^2.0.0` is still a dev dependency of `digital` and `shared_lib/core`. No `analysis_options.yaml` includes it. It is unused.
- No `custom_lint` and no custom rules.

### CI checks

- `pr-pipeline.yml`: PR title format, closes `feat` PRs into release branches, melos bootstrap check, `melos run analyze` (which runs `dart format --set-exit-if-changed` and `flutter analyze`), tests, Codacy and Sonar upload.
- `on-merge-master.yml`: runs `melos generate` and `melos format`, then **commits any diff back** as `bfibravo-bot`. So stale generated files are fixed after merge, not blocked before it.
- `pr-pipeline.yml` and `on-merge-master.yml` skip PRs that only touch `.github/**`. Workflow changes get no checks.
- No review bot. Codacy gets AI review instructions from `.codacy/instructions/review.md`.

### Architecture today (baseline for a ratchet)

Counted with a script over `digital/lib/features/` (23 features), generated files excluded:

| Check | Count |
|---|---|
| Imports from one feature into another | 264 |
| Files with at least one such import | 106 |
| Distinct feature-to-feature pairs | 60 |
| Biggest pairs | `loan → auth` 35, `home → loan` 22, `loan → select_vehicle` 16, `ro → auth` 16, `ro → loan` 16 |
| Vendor SDK imports (Firebase Analytics, Mixpanel, AppsFlyer, Insider, Remote Config, Datadog) inside `features/` | 0 (they sit in 6 files under `app/`) |
| `package:flutter` imports in `data/customer/lib` | 0 |

There is no `domain/` folder yet, so "domain has no Flutter imports" cannot be checked until the Layering plan starts.

### AI rules

- `AGENTS.md` (194 lines) covers commands, API naming, UI and design-system rules, controller structure, use cases, data layer, logging, testing.
- `sync-ai-rules.yml` copies `AGENTS.md` to `CLAUDE.md`, `.github/copilot-instructions.md` and `.codacy/instructions/review.md` on every push to `master` or `release-*`.
- No `.claude/rules/` and no skills.

## Target (what Jago does, adapted for BFI)

| Jago pattern | Path | Note |
|---|---|---|
| Shared lint package | `module_linter/lib/global_lint.yaml` (116 lines), `flutter_lint.yaml` | Every module includes it. Turns on `custom_lint` and `strict-raw-types` |
| Custom lint rules | `module_linter/lib/rules/` | Only 3 rules: `avoid_media_query_of`, `avoid_image_network`, `avoid_svg_picture_network`. None of them check architecture |
| Danger bot | `danger/Dangerfile`, `danger-bot` job in `.gitlab-ci.yml` | 3 lines. One rule: label MRs that change Hive table files |
| Generated-files check | `verify-generated-files` job in `.gitlab-ci.yml` | Rebuilds generated code on the MR and fails on any diff |
| Package rule | `scripts/package-centralization-checks.sh` (240 lines) | Only `library/*` wrappers may depend on pub.dev packages |
| Written rules | `.claude/rules/` (14 files): `layer-model.md`, `journey-clean-architecture.md`, `ports-and-contracts.md`, `ratchet.md`, … | Read by AI tools and humans |
| Review skill | `.claude/skills/mr-review/` | Reviews a diff against those rules |
| Ratchet policy | `.claude/rules/ratchet.md` | "Review the diff, not the codebase." Old violations are allowed; new ones are not |

Important: Jago's architecture rules are still checked **by review, not by tooling** (stated on the parent page). Its Danger file and custom rules are thin. BFI can do better on this one point with a simple script.

How it maps to BFI:

- Lint package: keep `lint/strict`. Add `custom_lint` only if a rule needs the AST. A grep-based script is enough for import rules.
- Ratchet: start from the 264 cross-feature imports above. CI fails only if a PR adds a new one.
- Review bot: a GitHub Action (Danger JS, or a small `actions/github-script` step) instead of Ruby Danger on GitLab.

**Do not copy:** Jago's Hive-label Danger rule (BFI has no Hive). The `library/*` wrapper-per-package rule (110 wrappers is too heavy for BFI). Jago's rule texts word for word; write BFI's own.

## Plan

### Step 1: clean up lint setup (1 small PR)

- Remove `flutter_lints` from `digital/pubspec.yaml` and `shared_lib/core/pubspec.yaml`.
- Keep the root `analysis_options.yaml`. Add `strict-raw-types: true`, `strict-casts: true` and `strict-inference: true` if the error count is small; otherwise list them as a later step.
- Check: `melos run analyze` passes.

### Step 2: fail PRs on stale generated files (1 PR)

- Add a step to `pr-pipeline.yml`: run `melos generate` and `melos l10n`, then fail if `git status --porcelain` is not empty.
- Keep the bot commit in `on-merge-master.yml` for one month as a safety net. Then remove it.

### Step 3: architecture dependency check (1–2 PRs)

Add `scripts/check-architecture.dart` (or `.sh`). Run it in `pr-pipeline.yml` after analyze.

| Rule | How it is checked | Regime |
|---|---|---|
| No feature imports another feature | `features/<a>/**` must not import `package:digital/features/<b>/` | Ratchet: baseline file with today's 264 imports; new ones fail |
| Domain has no Flutter or data imports | `**/domain/**` must not import `package:flutter/`, `package:dio/`, `package:customer/` | Strict (new folders start clean) |
| Vendor SDKs only in adapters | `firebase_analytics`, `mixpanel_flutter`, `appsflyer_sdk`, `flutter_insider`, `datadog_flutter_plugin`, `firebase_remote_config` only under `app/analytics/`, `app/logging/`, `app/flags/` (or the adapter folders the other plans create) | Strict (0 today in features) |
| Design-system package does not import the app | `shared_lib/design_system/**` must not import `package:digital/` | Strict |
| `data/customer` has no Flutter UI imports | No `package:flutter/material.dart` in `data/customer/lib` | Strict (0 today) |

```dart
// scripts/check_architecture.dart (sketch)
final featureImport = RegExp(r"^import 'package:digital/features/([a-z_0-9]+)/");
for (final file in dartFilesUnder('digital/lib/features')) {
  final owner = file.path.split('/')[3];
  for (final line in file.readAsLinesSync()) {
    final m = featureImport.firstMatch(line);
    if (m != null && m[1] != owner && !baseline.contains('$owner->${m[1]}:${file.path}')) {
      violations.add('${file.path}: imports feature ${m[1]}');
    }
  }
}
```

- Store the baseline in `scripts/architecture-baseline.txt`. A PR that removes a violation also removes its line. The count can only go down.
- Once features become packages (Repo layout plan), the package graph enforces most of this. Keep the script for domain and SDK rules.
- Check: a test PR that adds `import 'package:digital/features/payment/...'` in `features/home/` fails.

### Step 4: a review bot (1 PR)

Use a GitHub Action (Danger JS or `actions/github-script`). Start with a few rules that help, not nag:

- Warn when a PR changes more than 600 lines outside generated files.
- Warn when `lib/` changes but no test file changes.
- Warn when `pubspec.yaml` adds a dependency, and ask for a reason.
- Fail when a workflow file prints `secrets.*` (see Security plan).
- Label PRs that touch `.github/workflows/` so SRE reviews them.

Also make sure workflow-only PRs run at least this bot and the secret check. Today they skip every check.

### Step 5: AI rules and the review skill (1–2 PRs)

- Add `.claude/rules/` with BFI's own short files: `layer-model.md`, `riverpod-conventions.md` (Notifier, no global `appRef`), `analytics.md`, `ratchet.md`, `testing.md`.
- Keep `AGENTS.md` as the entry point. Link to the rule files from it, so `sync-ai-rules.yml` still covers Copilot and Codacy.
- Add `.claude/skills/mr-review/SKILL.md`: review the diff only, check each rule, report new violations with file and line, ignore old ones.
- Check: run the skill on 3 recent merged PRs. It should find real issues and few false alarms.

### Step 6: protect the guardrails (1 PR)

- Add a `CODEOWNERS` entry so changes to `.github/`, `scripts/check-architecture*`, `analysis_options.yaml` and `.claude/` need a lead's review.

### Parity check

- This plan changes no app behaviour. It adds the CI rules that keep old and new paths apart until flip and delete.
- Rule `switch-path-isolation` (strict) in `scripts/check-architecture.dart`: new-path code may not import old-path code, and old-path code may not import new-path code. Only the switch point, the one place that reads the switch flag, may import both.
- Agree one way to mark the two paths (for example a folder per path) with Mobile plan 08: Layering, before the first switch flag ships.
- Rule `switch-flag-expiry`: every switch flag in the flag catalogue (Mobile plan 12: Feature flags) has an owner and a removal date. Every old path is tagged with the same date. CI fails when a flag or its old path is still in the code after that date.
- Step 1 lint changes (strict casts and inference) must not change behaviour. `melos test` and the parity net stay green.
- Approved deltas: none.

## Done when

- `flutter_lints` is gone from every `pubspec.yaml`.
- CI fails a PR with stale generated files, before merge.
- CI fails a PR that adds a new feature-to-feature import. The baseline count goes down every month (264 at the start).
- CI fails a PR that imports Flutter or dio in a `domain/` folder.
- CI fails a PR that imports a vendor analytics or logging SDK outside its adapter folder.
- Workflow-only PRs run the secret check and the review bot.
- `.claude/rules/` and an `mr-review` skill exist and are linked from `AGENTS.md`.
- CI fails a PR where new-path code imports old-path code, or the other way round.
- CI fails when a switch flag or its old path is still in the code after its removal date.

## Effort and owner

- **S** from the parent table. About 1–2 sprints.
- Owner: Customer Mobile Apps squad tech lead. SRE reviews workflow changes.

## Depends on / related plans

- Mobile plan 11: Repo layout (package boundaries replace part of the import check).
- Mobile plan 08: Layering (the domain rules need `domain/` folders).
- Mobile plan 02: Analytics wrapper, Mobile plan 05: Logging and crashes, Mobile plan 12: Feature flags (they define the adapter folders).
- Mobile plan 01: Security (workflow secret check).
- Mobile plan 03: Testing (test rules in `AGENTS.md`).
- Mobile plan 04: CI/CD (where the new jobs run).

## Risks

| Risk | Mitigation |
|---|---|
| The import check blocks work on a busy sprint | Ratchet only; old violations never fail |
| Baseline file becomes a dumping ground | Only a lead can add lines (CODEOWNERS); report the count monthly |
| Review bot is noisy and gets ignored | Start with warnings; turn a rule into a failure only after a month with few false alarms |
| AI rules drift from what CI checks | Each rule file names the CI check that enforces it, or says "review only" |
| Stricter analyzer flags flood the build | Turn them on one at a time; fix per package |
