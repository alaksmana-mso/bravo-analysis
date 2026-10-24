# Mobile plan 01: Repo layout

## Goal

Each big feature (`loan`, `auth`, `rl`, `ro`) lives in its own package with a small public surface. A feature cannot import another feature by accident, because the package does not depend on it. The app (`digital/`) only wires features together.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. Counts exclude `*.g.dart` and `*.freezed.dart`.

### Packages

- Root `pubspec.yaml` is a Dart workspace with 3 members: `digital`, `data/customer`, `shared_lib/core`.
- `digital/lib/features/` holds 23 feature folders and 355 files. `digital/lib/app/` holds 155 more files.
- `data/customer/lib` has 123 files: 26 repository files, the `HttpClient`, and the API models. Its barrel `customer.dart` has 115 `export` lines.
- `shared_lib/core/lib` has 23 files. Its barrel `core.dart` re-exports 12 third-party packages, including `flutter_riverpod`, `go_router` and `freezed_annotation`.

### Feature sizes (files, lines)

| Feature | Files | Lines | StateNotifiers |
|---|---|---|---|
| `loan` | 130 | 25,626 | 21 |
| `auth` | 41 | 9,255 | 6 |
| `rl` | 35 | 6,688 | 8 |
| `ro` | 25 | 7,292 | 5 |
| `bpkb_release` | 20 | 3,512 | 3 |
| `home` | 17 | 2,728 | 4 |
| 17 others | 87 | 14,015 | 22 |

Inside `loan`: `agreement/` 53 files, `submission/` 25, `detail/` 15, `survey/` 14, `submission_list/` 9, `simulation/` 7.

### Cross-feature imports (how hard extraction is)

All imports use `package:digital/...` (0 relative imports), so they are easy to count.

- **264** import lines go from one feature folder into another. They form **60** directed edges between features.
- **14** pairs import each other both ways (cycles). `loan` is in 8 of them: `auth`, `ro`, `rl`, `home`, `payment`, `onboarding`, `bpkb_release`, `domicile_address`.
- What the 264 lines point at: 109 use-case files, 70 screens, 41 widgets or dialogs, 2 controllers, 42 small model or helper files.

| Feature | Imports out to other features | Imports in from other features | Imports in from `app/` |
|---|---|---|---|
| `loan` | 86 | 68 | 27 |
| `auth` | 20 | 84 | 29 |
| `ro` | 35 | 18 | 9 |
| `rl` | 17 | 15 | 16 |

Biggest single edges: `loan → auth` 35 (mostly `auth_use_case.dart`, `auth_flow_use_case.dart`, `kyc_use_case.dart`), `home → loan` 22, `ro → loan` 16, `ro → auth` 16, `loan → select_vehicle` 16.

### Features also lean on the app folder

- 301 of 355 feature files import something from `package:digital/app/`.
- `loan` alone has 853 such import lines, to 93 different app files. By folder: `ui` 258, `theme` 158, `localizations` 81, `util` 53, `common` 52, `widget` 44, `navigation` 38, `dsl` 35, `analytics.dart` 31, `tracker` 29.
- `app/navigation/router.dart` (870 lines, 78 `GoRoute`s) imports every feature. 94 feature files import it back for route-name constants. That is a cycle through the app.

### Leaf features (no edges)

`support` (8 files), `branch_info` and `stnk_management` have 0 imports to or from other features. `select_vehicle` (12 files) has 0 imports out and 18 in, 16 of them from `loan`.

## Target (what Jago does, adapted for BFI)

### What Jago does

- 49 `module_*` packages. 24 are `module_*_journey` feature packages. 25 modules have a `lib/domain/` folder.
- `.claude/rules/layer-model.md` sets four layers: application, features, generic, library. Features must not import other features. The app layer does all DI wiring.
- Shared needs between features go through a thin `*_api` package (entities and interfaces only, no UI). Jago has written this rule but not built one yet: `catalog/README.md` is still a placeholder.
- `MULTI_BANK_ARCHITECTURE_PROPOSAL.md` §7 describes the move as "decouple in place, then extract, then flip". You cut the imports while the code still sits in the old place. Then you move it.

### BFI target layout

```text
bravo-customer-app/
  digital/                 app shell: main, router composition, overrides, top level
  features/
    loan/                  package feature_loan
    auth/                  package feature_auth
    auth_api/              package feature_auth_api (ports other features need)
    rl/  ro/  select_vehicle/  support/ ...
  shared_lib/
    core/                  plumbing (exists)
    design_system/         Mobile plan 10
    analytics/             Mobile plan 05
    network/               Mobile plan 08 (HttpClient moves out of data/customer)
    master_data/           address, branch, vehicle, bank, static config
    l10n/                  ui_text and app_id.arb
  data/customer/           legacy, frozen, shrinks to nothing
  tool/arch_check.dart     ratchet checker + baseline
```

Inside one feature package:

```text
features/loan/
  lib/feature_loan.dart        public barrel (small)
  lib/src/domain/              see Mobile plan 02: Layering
  lib/src/data/
  lib/src/presentation/
  lib/src/routes/loan_routes.dart
  lib/src/di/loan_providers.dart
  test/
```

### Rules

- A feature package depends on `shared_lib/*` and on `*_api` packages. Never on another feature package. Never on `digital`.
- The barrel exports only: the route list builder, route argument types, the feature's exit-port type, and the providers the app must override. Screens are not exported.
- A `*_api` package is created only when a second feature needs the data. It holds entities and abstract interfaces only.
- Route names belong to the feature. `router.dart` stops holding every constant. The app builds the route table from each feature's `xxxRoutes()`.
- Navigation to another feature goes through an exit port (a callback the app fills in). See Mobile plan 04: Dependency injection.
- New shared logic does not go into a catch-all package. Each `shared_lib` package has one job.

### What NOT to copy from Jago

- The 4 apps and multi-bank layers (`catalog/`, bank packages). BFI ships one brand.
- 110 `library/*` wrapper packages around pub.dev packages. That is too much overhead for one squad.
- `module_common`, Jago's god package. Jago now forbids new logic in it. BFI should not create one.
- Rules that are only checked by reviewers. Jago's layer model is "review-enforced". BFI should check it with a script from day one.

## Plan

### Step 1: write the rules and the ratchet checker (1 PR)

- Add `tool/arch_check.dart`. It scans imports and counts violations per rule and per file. It compares to `tool/arch_baseline.json`. It fails if any count goes up. It asks you to lower the baseline when a count goes down.
- Rules from this plan: `feature-import` (264 today), `router-import` (94 files), `customer-repo-growth` (26 repository files in `data/customer`).
- Mobile plans 02, 03 and 04 add their rules to the same file.
- Add the rules to `AGENTS.md` and a new `.claude/rules/layer-model.md` (BFI version).
- Check: run it on `master`; it passes. Add one import from `rl` into `ro` on a branch; it fails.
- CI wiring belongs to Mobile plan 12: Lint and guardrails.

### Step 2: shared packages that every feature needs (with Mobile plan 10)

- Mobile plan 10: Design system moves `app/ui`, `app/theme` and the generic parts of `app/widget` into `shared_lib/design_system`. This removes up to 460 of `loan`'s 853 app imports.
- Move `app/localizations` (`ui_text.dart`, ARB) into `shared_lib/l10n`.
- Move `app/dsl` (8 files, used by `loan`, `rl`, `ro`, `auth`, `account`) into `shared_lib/dsl_form`.
- These are file moves plus an import rewrite script. No behaviour change.
- Check: `grep -r "package:digital/app/(ui|theme|localizations|dsl)" digital/lib/features` returns 0.

### Step 3: pilot with `support` (1–2 PRs)

- `support` has 0 feature edges. Move it to `features/support/` as `feature_support`.
- Add `supportRoutes()` and wire it in `router.dart`.
- This proves the package template, workspace entry, `melos` scripts, tests in CI and the route hand-off.
- Check: app builds for all 4 flavors. `melos test` runs the moved tests.

### Step 4: own the routes per feature, still inside `digital` (3–4 PRs)

- Split `router.dart` into one `xxx_routes.dart` per feature folder. Route-name constants move into the feature.
- Calls that push another feature's route switch to an exit port.
- Check: `router-import` count drops from 94 to 0. `router.dart` only composes lists.

### Step 5: `auth_api` first, before moving `auth` (2–3 PRs)

- `auth` has 84 imports coming in from other features. Most callers want three things: "is the user logged in and at which access level", "make the user log in", "run KYC and give me the result".
- Create `features/auth_api` with `SessionReader`, `LoginLauncher` and `KycLauncher` interfaces. The code stays in `digital/lib/features/auth`. The app wires it (Mobile plan 04).
- Switch callers feature by feature. Start with `loan` (35 imports).
- Check: `feature-import` edges into `auth` drop from 84 toward 0.

### Step 6: extract `select_vehicle` (1 PR)

- It has 0 imports out. `loan` needs it (16 imports). Move it first, so `loan` can depend on a package.

### Step 7: decouple `loan` in place (4–6 PRs)

- Do Mobile plan 02 (domain layer) and Mobile plan 03 (Notifier, no `appRef`) for `loan` while it still sits in `digital`.
- Cut the remaining `loan` edges: `home → loan` (22) through a small `loan_api` (loan summary entity + reader), `loan → payment`, `loan → ro`, `loan → rl` through exit ports.
- Check: `feature-import` count for `loan` (in and out) is 0. `loan` imports nothing from `digital/app/` except through `shared_lib`.

### Step 8: extract `loan` (1–2 PRs)

- Move the folder to `features/loan`. Rewrite imports. Wire providers and routes in the app.
- Check: `features/loan/pubspec.yaml` lists no feature package. All 4 flavors build. Smoke test on SIT: apply, detail, agreement, survey.

### Step 9: repeat for `auth`, `rl`, `ro`

- Same order each time: decouple in place, then extract. Expect `ro` to be harder than its size suggests: 35 imports out.

### Step 10: empty `data/customer`

- Each extraction takes the repositories that only that feature uses. For `loan` that is `LoanAgreementRepository`, `LoanCalculatorRepository`, `LoanOnboardingDocumentRepository`, `AdditionalDocumentsRepository`, `SurveyRepository`.
- See Mobile plan 02: Layering for where shared repositories go.

## Done when

- `features/loan`, `features/auth`, `features/rl`, `features/ro` exist as workspace packages. None lists another feature in its `pubspec.yaml`.
- `feature-import` count for those four is 0. The total across the app is lower than 264 and never rises.
- 0 feature files import `app/navigation/router.dart`.
- `tool/arch_check.dart` runs on every PR (Mobile plan 12).
- `data/customer` has fewer than 26 repository files, and no new one was added since the baseline.

## Effort and owner

- Size: **L** (from the parent table).
- Rough time: 10–12 sprints for steps 1–9, alongside feature work. Steps 1–3 fit in the first 2 sprints.
- Owner: Customer Mobile Apps squad, with one named tech lead for the layout.

## Depends on / related plans

- Mobile plan 02: Layering (what goes inside each package).
- Mobile plan 03: State management (removing `appRef` before a feature can move).
- Mobile plan 04: Dependency injection (ports, exit ports, app wiring).
- Mobile plan 10: Design system (blocks every extraction).
- Mobile plan 05: Analytics wrapper (`shared_lib/analytics`).
- Mobile plan 08: Networking (`shared_lib/network`).
- Mobile plan 12: Lint and guardrails (runs the checker in CI).

## Risks

| Risk | Mitigation |
|---|---|
| Moving files breaks open PRs | Move one feature at a time. Announce the move a sprint ahead. Use a script to rewrite imports. |
| `loan` extraction stalls on its 8 cycles | Decouple in place first. Measure edges per sprint. Extract only at 0. |
| A new `shared_lib` package becomes a god module | One job per package. Review any new file in `shared_lib` that imports more than one other `shared_lib` package. |
| Build time grows with more packages | Workspace resolution keeps one lockfile. Track CI time per PR. |
| Team keeps adding edges while we cut them | The ratchet fails the PR. New code follows the rule from day one. |
