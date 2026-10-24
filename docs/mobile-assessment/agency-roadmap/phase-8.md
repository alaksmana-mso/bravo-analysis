## Summary

Phase 8 of the agency apps roadmap ("Packages, move only") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 9 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Packages".
* **Plan pages:** GENFI plan 09: Repo layout steps 3–4; GENFI plan 12: Design system steps 1 and 3; SQUARE plan 10 step 3; SQUARE plan 12 steps 1 and 3; GENFI plan 13 step 4.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 8 is.** Code moves into packages without changing behaviour: the first feature package per app (`prospect` for GENFI, `lead` for SQUARE, after their Phase 7 pilots), the generated-code decision, and the design-system consolidation (four design systems down to one). Every step is class B: tests and golden files must not change, and a "move only" PR is renames plus import rewrites.

### Five facts that shape Phase 8

**1. The monorepo shape is good; the apps are monoliths.** The root `pubspec.yaml` is a Dart workspace of 15 shared packages plus `ui_catalog` and `ui_theme`; melos categories list which shared packages each app uses. But every feature of GENFI (34 folders) and SQUARE (21 folders) lives in one package.

**2. Generated code is as big as hand-written code.** 430,795 generated lines against 439,333 hand-written across the repo. `shared_data` alone: 33,497 hand-written lines, 291,420 generated in 658 files (8.7x), all committed; the largest generated file is 8,238 lines; `agent_marketing` has 124,662 generated lines. This is why the "generated code decision" (8.4) is its own step.

**3. Four design systems.** `ui_theme` in the monorepo (MY BISPRO only) plus `ds_1`, `ds_2`, `ds_3` from the `frontend-mobile-ui` git repo. GENFI imports `ds_2` in 154 files and `ds_3` in 199 (110 files import both) plus a local `ds3` shim. SQUARE uses `ds_1`, the oldest, in 195 files. Adoption is high; the migrations are unfinished.

**4. Cross-feature edges.** GENFI 129 (76 not into `common`); `calculator ↔ prospect` and `convent_registration ↔ account_information` import each other. SQUARE 89 in 79 files; `profile` is imported by 35 files, `maintain` by 12. `collab_form` (124 files, 18,595 lines) is shared by both apps, depends on `agency`, `agent_marketing`, `onboarding` and (undeclared) `core`, branches on `CollabFormAppId` in 26 places, and ships its own routes with untyped `state.extra` casts.

**5. Duplicate class names across packages:** `AgentRepository`, `MasterRepository`, `DocumentRepository`, `AddressRepository`, `BranchRepository`, `MediaRepository`, `CalculationLocalDataSource`. No dependency cycles. No shared package imports an app.

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. All class **B** unless marked.

| # | Proposed ticket title | Today (24 Oct) | App | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1 | `chore: Generated-code decision (gitignore + build in CI, or committed with a freshness check)` | 430,795 generated lines committed | shared | Agency engineer + SRE | M | 1.2 | | |
| 8.2 | `feat(features): Package template, melos scripts, routes hand-off (pilot: a small leaf feature)` | No feature packages | shared | Agency engineer | S | 8.1 | | |
| 8.3 | `feat(features): prospect as a package + prospect_api` | `lib/feature/prospect` | GENFI | Agency engineer | L | GENFI Phase 7 | | |
| 8.4 | `feat(features): lead as a package + lead_api` | `lib/features/lead` | SQUARE | Agency engineer | M | SQUARE Phase 7 | | |
| 8.5 | `refactor(design): Finish ds_2 → ds_3 in GENFI (154 files), delete the ds3 shim` | Two design systems in one app | GENFI | Agency engineer + design | L | 2.15 | | |
| 8.6 | `refactor(design): ds_1 → ds_3 inventory, then migrate SQUARE (195 files), one feature per PR` | Oldest design system | SQUARE | Agency engineer + design | L | 2.15, SQUARE Phase 7 flags | | |
| 8.7 | `refactor(design): MY BISPRO from ui_theme to ds_3; delete ui_theme and ui_catalog` | `ui_theme` for one app | MY BISPRO | Sharia squad | M | 8.6 | | |
| 8.8 | `refactor(data): Rename duplicate repository classes; one KeycloakRepository` | 7 duplicate names | shared | Agency engineer | S | 4.7 | | |
| 8.9 | `refactor(di): Provider declarations out of shared_data (plain Dart data packages)` | `shared_data` depends on Riverpod | shared | Agency engineer | S per package | 8.3 | | |

**Suggested order.** 8.1 and 8.2 during Phase 7. Then 8.3 (GENFI) and 8.4 (SQUARE) as each pilot finishes. 8.5 and 8.6 run with design in parallel. 8.7, 8.8, 8.9 close the phase.

## Definition of ready for every Phase 8 ticket

* The ticket says "move only" and lists the folders that move. Any behaviour change is a separate ticket.
* Golden screenshots and the golden names file are listed as acceptance criteria and must be unchanged.
* The import-rewrite script is committed with the PR.
* All three apps build for every flavour in CI before merge.

## Step 8.1: Generated-code decision

**Today.** See fact 2. `build_runner` output is committed; PR diffs carry thousands of generated lines.

**Tasks.** Decide once for the monorepo: (a) `.gitignore` `*.g.dart` and `*.freezed.dart`, run `build_runner` in `checks.yml` with a cache keyed on `pubspec.lock` and model sources; or (b) keep committing with a "generated files are fresh" check that fails stale PRs. Either way, split the largest generated files by moving the `freezed` models they come from.

**Acceptance criteria.** (a): PR diffs contain no generated files; CI time within today's plus 3 minutes. (b): a stale generated file fails the PR.

**Who / size.** One Agency engineer + SRE for CI time. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ignore and build in CI with a cache | Clean diffs, smaller clone | Every developer runs `build_runner` locally; CI time |
| B. Commit with a freshness check (as the BFI app does) | No local step; reviewable | 430k lines stay in git |
| C. Leave as is | No work | 8.7x generated code with no check |

**Recommended: B first** (one PR, matches the BFI app), **A if CI time allows** after the cache is measured. The team's preference decides (question 1).

## Step 8.2: Package template and a leaf pilot

**Today.** No feature packages; routes composed in each app's router.

**Tasks.** A package template: `pubspec.yaml` with `resolution: workspace`, a barrel that exports routes, exits, port types and provider declarations only, `lib/src/di/`, `test/helpers/overrides.dart`. Melos scripts per package. Pilot with a leaf feature with no edges (candidates: GENFI `splash` or `media`; SQUARE `brochure` or `user_guide`, confirm with the edge list).

**Acceptance criteria.** All flavours build. The moved tests run in CI. The template is written down for 8.3 and 8.4.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Leaf feature first, template as the deliverable | Zero-edge proof of the mechanics | Proves little about edges |
| B. `prospect` or `lead` first | Biggest win | Highest risk; needs Phase 7 first anyway |
| C. No pilot | Fast | The first real move hits every problem at once |

**Recommended: A.**

## Step 8.3: `prospect` as a package

**Today.** `lib/feature/prospect`: 89 files, 31,169 lines, 20 controllers; after GENFI Phase 7 the old path is gone. Imported by `calculator` (8) and `convent_lounge`; imports `common` (23) and `calculator` (5).

**Tasks.** Move to `features/agent_tools/prospect` with the template. `prospect_api` for the entities other features import. The app shell wires providers and `prospect_routes.dart`. The remaining `common` reads go through small `*_api` readers (GENFI Phase 7 did most).

**Acceptance criteria.** The package compiles and tests on its own with `melos exec`; the app imports it as a package; `feature-boundary` for `prospect` in and out is 0; goldens unchanged.

**Who / size.** One Agency engineer. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One move PR after the pilot, with `prospect_api` | Clean cut | Large rename diff |
| B. Move before Phase 7 finishes | Earlier package | Two paths move; double work |
| C. Keep in the app | None | Squads keep colliding in one package |

**Recommended: A.**

## Step 8.4: `lead` as a package

**Today.** `lib/features/lead`: 82 files, 20,692 lines, `cancellation_review` already in the target shape. Imported by many features (`profile` is the most imported SQUARE feature at 35 files; `lead` edges to confirm).

**Tasks.** Same as 8.3 with `lead_api`.

**Acceptance criteria.** Same as 8.3 for `lead`.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. After SQUARE Phase 7 | Pure move | Waits |
| B. Now | Earlier | Moves the old path too |
| C. `profile` first (most imported) | Breaks the biggest edge cluster | `profile` is small; `profile_api` can come without the move |

**Recommended: A**, with a `profile_api` reader extracted in SQUARE Phase 9.

## Step 8.5: Finish `ds_2` → `ds_3` in GENFI

**Today.** `ds_2` in 154 files, `ds_3` in 199, 110 files import both, a local `ds3` shim.

**Tasks.** List the `ds_2` widgets still used; map each to its `ds_3` equivalent; migrate per feature; delete the shim and the `ds_2` dependency. Goldens regenerated in the same PR with design's sign-off where pixels change.

**Acceptance criteria.** `pubspec` has no `bfi_design_system_2`; 0 files import it; key-screen goldens signed off.

**Who / size.** One Agency engineer + design. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Per feature, goldens regenerated with sign-off | Reviewable visual diffs | Weeks of design review |
| B. One big replace | Fast | Every golden fails at once |
| C. Keep both | None | Two design systems forever |

**Recommended: A.**

## Step 8.6: `ds_1` → `ds_3` for SQUARE

**Today.** `ds_1` in 195 files; raw styling in 46 `TextStyle(`, 20 `Colors.`, 10 `TextButton(` sites.

**Tasks.** An inventory table (`BfiText` → `ds_3` typography, `BfiColors` → tokens) with an owner per widget; where `ds_3` lacks a widget SQUARE needs, add it to `ds_3`, not the app. Migrate one feature per PR, behind the same switch flags as the Layering rollouts where screens are rebuilt; goldens regenerated in the same PR.

**Acceptance criteria.** SQUARE `pubspec` has no `bfi_design_system_1`; the inventory table is complete.

**Who / size.** One Agency engineer + design. L (3–4 sprints).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Inventory, then per feature with the Layering flags | Rebuilt screens get the new system once | Long |
| B. Migrate styling only, screens untouched | Smaller | Screens are rebuilt again in Phase 9 |
| C. Keep `ds_1` | None | The oldest system stays in a live app |

**Recommended: A.**

## Step 8.7: MY BISPRO to `ds_3`

**Today.** `ui_theme` (monorepo) serves MY BISPRO only; `ui_catalog` has 1 test.

**Tasks.** Move MY BISPRO to `ds_3`; delete `ui_theme` and `ui_catalog` from the workspace.

**Acceptance criteria.** `ui_theme` and `ui_catalog` gone; MY BISPRO goldens signed off.

**Who / size.** Sharia squad + one Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Move and delete | One design system | Sharia squad time |
| B. Keep `ui_theme` for MY BISPRO | No work | Four systems become three, not one |
| C. Fold `ui_theme` into `ds_3` | Preserves MY BISPRO's look | Two looks in one package |

**Recommended: A.**

## Step 8.8: Duplicate repository names

**Today.** See fact 5. The duplicate `KeycloakRepository` is deleted in Phase 4 (4.7).

**Tasks.** Rename the duplicates with a package prefix or merge them where they are the same thing (`BranchRepository`, `AddressRepository`).

**Acceptance criteria.** No two packages export the same class name. All apps build.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rename now | Imports stop needing `as` prefixes | Touches call sites |
| B. Merge duplicates into `master_data` | Fewer classes | A behaviour question per pair |
| C. Leave | None | `import ... as` everywhere |

**Recommended: A**, B where the pair is the same API.

## Step 8.9: `shared_data` without Riverpod

**Today.** `core` re-exports `flutter_riverpod`; `shared_data` packages depend on Riverpod only for provider declarations.

**Tasks.** Move provider declarations into the feature `di/` or a small `shared_data/*/di` file, one package per PR. Stop re-exporting Riverpod from `core`.

**Acceptance criteria.** `shared_data/agency` `pubspec` has no `flutter_riverpod`. All apps build.

**Who / size.** One Agency engineer. S per package.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Per package, later | Data packages become plain Dart | 9 PRs |
| B. Keep Riverpod in data packages | No work | Data packages pull in a UI framework |
| C. One PR for all | Fast | Large diff |

**Recommended: A.**

## Exit gate for Phase 8

* `prospect` and `lead` are packages with no feature dependency; the leaf pilot too.
* The generated-code decision is in force in CI.
* `ds_2`, `ds_1`, `ui_theme` and `ui_catalog` are gone; one design system.
* No duplicate class names across packages; `shared_data` packages do not depend on Riverpod.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Generated code: ignore and build in CI, or commit with a freshness check? | Agency squad + SRE | |
| Q2 | Which leaf feature per app is the package pilot? | Agency squad | |
| Q3 | Design capacity for `ds_2` → `ds_3` and `ds_1` → `ds_3` reviews in the same quarter? | Design lead | |
| Q4 | Does the Sharia squad own the MY BISPRO move (8.7)? | Sharia squad lead | |
| Q5 | Epic: one for the monorepo with per-app sub-tickets? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Workspace | root `pubspec.yaml` `workspace:` (15 packages + `ui_catalog`, `ui_theme`) |
| Generated vs hand-written | 430,795 vs 439,333 lines; plan 09 "today" |
| Design systems | plan 09 and plan 12 "today"; `grep` of `ds_` imports |
| Edges | import graph per app (GENFI 129, SQUARE 89); plan 09 |
| `collab_form` | 124 files, 18,595 lines; `CollabFormAppId` 26 references |

## Sources for the recommendations

* BFI Phase 8 refinement notes (move-only rules, Widgetbook, package template).
* Widgetbook, [Widgetbook in a monorepo](https://docs.widgetbook.io/guides/monorepo).
* GENFI plan 09 and SQUARE plan 10 (repo layout), GENFI plan 12 and SQUARE plan 12 (design systems).
