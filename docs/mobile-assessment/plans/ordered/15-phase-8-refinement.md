## Summary

This page prepares Phase 8 of the mobile roadmap ("Packages, move only") for refinement. It covers all 12 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Packages".
* **Parent:** Mobile roadmap: step by step, section "Phase 8: Packages, move only". Plan pages: Mobile plan 11: Repo layout, Mobile plan 13: Design system, Mobile plan 10: Dependency injection, Mobile plan 14 (designer guide).
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct) and the Widgetbook and Melos docs.

**What Phase 8 is.** Code moves into packages without changing behaviour: first the shared packages every feature needs (design system, localisation, forms), then `loan`. Every step is class B: tests and golden files must not change. The rule for a "move only" PR is simple: the diff is renames plus import rewrites, and `git diff --stat -M` shows mostly moves.

### Five facts that shape Phase 8

**1. The workspace has 3 packages and the app imports its own `app/` folder everywhere.** `pubspec.yaml` workspace: `digital`, `data/customer`, `shared_lib/core`. 314 feature files import `package:digital/app/` for `ui`, `theme`, `localizations` or `dsl`. 40 files under `app/ui` and `app/theme` import `package:digital/` back (analytics, localisation). That cycle is what 8.2 cuts.

**2. The design system is used, but not clean.** 29 `Digital*` classes (plan 13: 32). 96 raw `Color(0x…)` literals outside `app/theme` (plan: 49, so it doubled) and 82 raw `TextStyle(` in features. `useMaterial3: false` in `app_theme.dart`. No Widgetbook.

**3. The feature graph is denser than the plan said.** 64 feature pairs import each other (plan 11: 60), 16 in both directions (plan: 14). Top edges: `loan→auth` 40, `loan→select_vehicle` 30, `ro→loan` 29, `home→loan` 29, `ro→auth` 27. Edges into `auth`: 100 (plan: 84). `router.dart` is 963 lines (plan: 870) and 116 feature files import it (plan: 94).

**4. Two pilots are ready.** `support` has 0 edges in and 0 out. `select_vehicle` has 1 edge out and 21 in (plan said 0 out, 16 in; the one out needs a look). Both can move with little risk.

**5. `data/customer` is one big barrel.** 26 repository files, 119 exports in `customer.dart` (plan: 115). Repositories used by one feature today: `SurveyRepository` (loan), `AccountRepository`, `RateLimitRepository`, `UserVerificationRepository` (auth), `BankAccountRepository` (rl), `PaymentRepository` (payment), `NotificationRepository`, `FaqRepository` (support), `CustomerProfileRepository` (account), `CustomerAttributionRepository` (lov). `StaticConfigRepository` is used by 9 features and is the first shared-data candidate.

Widgetbook's own docs describe two monorepo shapes: one Widgetbook app that catalogues every package, or one per package. Melos handles both.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. All class **B** unless marked.

| # | Proposed ticket title | Today (23 Oct) | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8.1 | Design-system scope and token names agreed with design (no code) | 29 `Digital*` classes, no token list | Design lead + squad lead | S (1 week calendar) | – | | |
| 8.2 | `refactor(ui): Cut component dependencies on the app` | 40 files in `app/ui` + `app/theme` import `package:digital/` | Mobile engineer | M | 2.4 | | |
| 8.3 | `feat(design-system): Create the package, move theme then components` (one PR per folder) | In `digital/lib/app/` | Mobile engineer | L | 8.1, 8.2 | | |
| 8.4 | `feat(design-system): Widgetbook, built in CI, published internally` | None | Mobile engineer | M | 8.3 | | |
| 8.5 | `ci(design-system): Ratchet raw colours and text styles, component goldens` | 96 raw colours, 82 raw text styles | Mobile engineer | S | 8.3, 1.19 | | |
| 8.6 | `refactor: Move localizations and dsl to shared_lib` | In `app/localizations`, `app/dsl` | Mobile engineer | M | 8.3 | | |
| 8.7 | `feat(features): Pilot package feature_support` | 0 edges | Mobile engineer | S | 8.6 | | |
| 8.8 | `refactor(navigation): Routes per feature, exit ports for cross-feature pushes` (3–4 PRs) | `router.dart` 963 lines, 116 importers | Mobile engineer | L | 7.10 | | |
| 8.9 | `feat(auth_api): SessionReader, LoginLauncher, KycLauncher ports; switch loan first` | 100 edges into auth, 40 from loan | Mobile engineer | M | 8.8 | | |
| 8.10 | `feat(features): Extract select_vehicle` | 21 edges in, 1 out | Mobile engineer | S | 8.7 | | |
| 8.11 | `refactor(loan): Decouple the remaining loan edges (loan_api for home)` | `home→loan` 29, `loan→ro` 10, `loan→payment` 9 | Mobile engineer | M | 8.9, 8.10 | | |
| 8.12 | `feat(features): Extract loan with its providers, helpers and loan-only repositories` | 167 files | Mobile engineer | M | 8.11 | | |

**Suggested order.** 8.1 starts during Phase 7. Sprint 1: 8.2, 8.5 (ratchet first, so raw colours stop growing). Sprints 2–3: 8.3, 8.6. Sprint 4: 8.4, 8.7, 8.10. Sprints 5–6: 8.8, 8.9. Sprint 7: 8.11, 8.12.

## Definition of ready for every Phase 8 ticket

* The ticket says "move only" and lists the folders that move. Any behaviour change is a separate ticket.
* Golden screenshots and the golden names file are listed as acceptance criteria and must be unchanged.
* The import-rewrite script is committed with the PR, so the move can be replayed if a release branch needs it.
* All 4 flavors build in CI before merge.

## Step 8.1: Design-system scope and token names

**Today.** 29 `Digital*` classes across `app/ui`, `app/widget`, `app/theme`. Some are feature-specific (`bank_account_form`, `bfi_banner`, `loan_amount_field_badge`). No token names agreed with design. The open decision from the parent page (build our own, or adopt DK's Jago library) is still open (Q1).

**Tasks.** With design: which classes are real design-system components, which stay in the app. Token names for colour, text, spacing, radius, starting from `DigitalColors` and `DigitalText`. Record the build-or-adopt decision.

**Acceptance criteria.** A signed-off list of components and tokens on Mobile plan 13. The build-or-adopt decision recorded on the parent page.

**Who / size.** Design lead + squad lead. S, one week of calendar time.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Build our own package from today's `Digital*` set | Full control, own look, adoption already high | We maintain it |
| B. Adopt DK's Jago library and join the shared design community | Faster start, Widgetbook and token pipeline exist | Dependency on DK's roadmap and look; a management decision |
| C. Own package now, designed so B stays possible (same token names as DTCG) | Keeps the door open | Slightly more design work up front |

**Recommended: C**, unless management picks B outright (Q1).

## Step 8.2: Cut component dependencies on the app

**Today.** 40 files in `app/ui` and `app/theme` import `package:digital/` (analytics, localisation strings, feature types). After 2.4 the tracking goes through a callback.

**Tasks.** Localised strings passed in as parameters instead of read from `ui_text.dart`. Feature-specific forms moved to their features (`bank_account_form.dart` to `features/bank/`). Any remaining feature type replaced by a plain parameter.

**Acceptance criteria.** `grep "package:digital/" digital/lib/app/ui digital/lib/app/theme` returns 0. Golden screenshots unchanged. Golden names unchanged.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Parameters and callbacks | Components become pure widgets | Call sites pass a few more arguments |
| B. An abstract "app services" interface the components read from an inherited widget | Fewer call-site changes | A hidden dependency; harder to use in Widgetbook |
| C. Leave the imports, move anyway with a dependency on `digital` | Fast | A package that depends on the app is not a package |

**Recommended: A.**

## Step 8.3: Create the package and move the code

**Today.** Theme in `app/theme`, components in `app/ui/components`, generic widgets in `app/widget/components`.

**Tasks.** `shared_lib/design_system` with `resolution: workspace`. Move `app/theme` first, then `app/ui/components`, then the generic widgets, one PR each. Leave a re-export file in the app for one release, then rewrite imports (script) and delete it. Move the 8 component tests with the code.

**Acceptance criteria.** `melos test` passes. No `Digital*` class defined outside the package. Golden screenshots unchanged. APK size within ±1%.

**Who / size.** One mobile engineer. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One package, one folder per PR, re-export for one release | Reviewable; nothing breaks mid-way | Three or four PRs |
| B. One PR for everything | Done at once | Hundreds of import changes in one review |
| C. Two packages (`design_tokens` pure Dart, `design_system` widgets) | Tokens usable by domain code and by a Figma pipeline | One more package; worth it if 8.1 chooses a token pipeline |

**Recommended: A, with C's split if 8.1 picks a token pipeline** (step 10.4).

## Step 8.4: Widgetbook

**Today.** None. Widgetbook docs: single workspace app that catalogues all packages, or one per package.

**Tasks.** A Widgetbook app with one use case per component and knobs for main states. Built as Flutter web in CI on every PR that touches the package. Published from `master` to an internal site (GitHub Pages on a private repo, or a GCS bucket behind IAP).

**Acceptance criteria.** A designer opens the link and sees every component. The build runs in CI and fails on a broken use case.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One Widgetbook app in the workspace, cataloguing `design_system` only | Simple | Feature widgets are not in it (fine; they are not design-system) |
| B. One Widgetbook per package | Flexible | More apps to keep building |
| C. Widgetbook Cloud (hosted, review workflow) | Visual review on PRs | Cost; check before Phase 8 |

**Recommended: A**, with C evaluated by design if they want PR-level visual review.

## Step 8.5: Ratchet raw colours and text styles, component goldens

**Today.** 96 raw `Color(0x…)` outside `app/theme` (up from 49), 82 raw `TextStyle(` in features. `AGENTS.md` has a line about `Color(0xFF...)` that needs fixing.

**Tasks.** Checker rules `raw-color` and `raw-text-style` with a baseline on merge day. New rule in `AGENTS.md`: add a token, do not add a literal. Goldens for button, text field, dialog, bottom sheet (Alchemist CI mode, Linux CI only).

**Acceptance criteria.** A PR that adds a new raw colour fails. Component goldens pass 10 runs in a row.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Ratchet in the existing checker + component goldens | Stops the growth now (it doubled since September) | Old literals stay until touched |
| B. A lint rule (custom_lint) that forbids `Color(` outside the package | IDE feedback | No baseline; 96 errors on day one |
| C. Fix all 96 now | Clean | A design pass on 96 sites; not "move only" |

**Recommended: A**, and the fixes land as screens are touched in Phases 7 and 9.

## Step 8.6: Move localisation and forms to `shared_lib`

**Today.** `app/localizations` (`ui_text.dart`, ARB) and `app/dsl` (3 entries) are imported by features through `package:digital/app/`. Together with `ui` and `theme`, 314 feature files import `app/`.

**Tasks.** `shared_lib/l10n` and `shared_lib/dsl_form`. File moves plus an import-rewrite script.

**Acceptance criteria.** No feature imports `package:digital/app/` for `ui`, `theme`, `localizations` or `dsl`. `melos l10n` still generates. Golden screenshots unchanged.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Two small packages | Clear ownership | Two more workspace entries |
| B. Fold both into `design_system` | Fewer packages | Localisation is not design; the package grows |
| C. Fold into `core` | No new package | `core` becomes the "everything" package, which is Jago's `module_common` debt |

**Recommended: A.**

## Step 8.7: Pilot package `feature_support`

**Today.** `support`: 0 edges in, 0 out, 11 analytics calls (moved in Phase 5), 2 controllers.

**Tasks.** Move to `features/support/` as `feature_support`. `supportRoutes()` wired in `router.dart`. Proves the package template, workspace entry, Melos scripts, tests in CI, route hand-off.

**Acceptance criteria.** All 4 flavors build. `melos test` runs the moved tests. The package template is written down for the next extraction.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `support` first | Zero edges; the template is the deliverable | A small feature proves less about edges |
| B. `select_vehicle` first | Tests the "many importers" case | 21 importers to rewrite on the first try |
| C. `loan` first | Biggest win | Highest risk; it needs 8.8–8.11 anyway |

**Recommended: A, then 8.10 (`select_vehicle`).**

## Step 8.8: Routes per feature, exit ports

**Today.** `router.dart` 963 lines, imported by 116 feature files. Cross-feature pushes are direct.

**Tasks.** One `<feature>_routes.dart` per feature folder, route-name constants inside the feature. `router.dart` only composes lists. Cross-feature pushes go through exit ports (the `LoanExits` pattern from 7.10, one per feature).

**Acceptance criteria.** `router-import` ratchet from 116 to 0. `router.dart` under 150 lines. Deep links and push-notification routes tested on SIT.

**Who / size.** One mobile engineer. L (3–4 PRs).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Route lists per feature, composed in the app; exits as ports | go_router stays the single router; features own their routes | Each feature needs its exit interface |
| B. A navigation package that wraps go_router and features call by name | One API, no go_router in features | Stringly-typed names; the wrapper grows |
| C. Nested routers per feature | Full isolation | Deep links and back-stack behaviour get hard |

**Recommended: A.**

## Step 8.9: `auth_api` ports

**Today.** 100 edges into `auth`; `loan` alone imports `auth` 40 times. Callers mostly want: is the user logged in and at which level, make the user log in, run KYC and return the result.

**Tasks.** `features/auth_api` with `SessionReader`, `LoginLauncher`, `KycLauncher`. Implementations stay in `digital/lib/features/auth` for now. The app wires them (2.15). Switch `loan` first, then the others.

**Acceptance criteria.** `loan` imports of `auth` use cases reach 0. Wiring test lists the 3 ports. Edges into `auth` go down with each PR.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. A thin `*_api` package with 3 interfaces | Jago's pattern; breaks the biggest edge cluster | Interfaces must stay small or they become `auth` again |
| B. Move `auth` to a package first and let features depend on it | Simpler mentally | `auth` depends on `loan` back (bidirectional edges), so it does not resolve |
| C. Merge `auth` into `core` | No new package | `core` becomes the everything package |

**Recommended: A.**

## Step 8.10: Extract `select_vehicle`

**Today.** 21 edges in (mostly `loan`), 1 edge out (check which), 6 controllers.

**Tasks.** Resolve the one outgoing edge (parameter or exit port). Move to `features/select_vehicle`. Rewrite 21 imports.

**Acceptance criteria.** All 4 flavors build. Vehicle selection journey passes on SIT.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Extract after the one edge is resolved | Clean package | One small refactor first |
| B. Extract with the edge, depend on the other feature | Fast | A feature package depending on a feature; the checker should refuse |
| C. Leave inside `digital` | No work | `loan` cannot leave without it |

**Recommended: A.**

## Step 8.11: Decouple the remaining `loan` edges

**Today.** `home→loan` 29, `ro→loan` 29, `loan→ro` 10, `loan→payment` 9, `onboarding→loan` 8, `rl→loan` 7, `notification→loan` 6.

**Tasks.** A small `loan_api` (loan summary entity + reader) for `home`, `onboarding`, `notification`, `rl`, `ro`. `loan→ro`, `loan→payment`, `loan→rl` through `LoanExits` (7.10).

**Acceptance criteria.** `feature-import` for `loan`, in and out, is 0. `loan` imports nothing from `digital/app/` except through `shared_lib`.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `loan_api` for readers, exits for pushes | Same pattern as `auth_api` | Two more small packages |
| B. Let `home` depend on the `loan` package | Simple | `home` then pulls all of `loan` into its build; `ro→loan→ro` cycle stays |
| C. Move the shared pieces into `core` | No api package | `core` grows |

**Recommended: A.**

## Step 8.12: Extract `loan`

**Today.** 167 files. After Phase 7 the old path is gone, so this is a move of the new code.

**Tasks.** Move to `features/loan`. `lib/src/di/loan_providers.dart`, a barrel that exports routes, exits, port types and the implementation providers only. `test/helpers/overrides.dart` with fakes. Move the loan-only repositories into the package's `data/` (verify the list: `SurveyRepository` confirmed, the plan's other four to check). Rewrite imports.

**Acceptance criteria.** `features/loan/pubspec.yaml` lists no feature package. All 4 flavors build. SIT smoke: apply, detail, agreement, survey. Goldens unchanged. The barrel exports no screen or notifier.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One move PR after 8.11, repositories included | Clean cut | A large rename diff |
| B. Move code first, repositories later | Smaller first PR | `loan` depends on `data/customer` for one more cycle |
| C. Move before Phase 7 finishes | Earlier package | Two paths move; double the work |

**Recommended: A.**

## Exit gate for Phase 8

* `features/loan` is its own package with no feature dependency. `support` and `select_vehicle` too.
* `design_system`, `l10n` and `dsl_form` packages exist; Widgetbook is published.
* Golden screenshots and the golden names file unchanged across the phase.
* `router-import` 0, `raw-color` and `raw-text-style` ratchets live.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Build our own design-system package, or adopt DK's Jago library? (parent page open question 5) | Management + design | |
| Q2 | Where does the internal Widgetbook site live (GitHub Pages private, GCS + IAP)? | SRE | |
| Q3 | Do we want Widgetbook Cloud for PR visual review? | Design lead | |
| Q4 | Which repositories are truly loan-only? (verify the plan's list of 5) | Mobile squad | |
| Q5 | Who owns `auth_api` once `auth` moves in Phase 9? | Squad lead | |
| Q6 | Epic for Phase 8: one epic with 12 tickets? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Workspace | root `pubspec.yaml` `workspace:` (3 entries) |
| `app/` imports from features | `grep -rl` for `package:digital/app/` followed by `ui`, `theme`, `localizations` or `dsl`: 314 files |
| Components importing the app | `grep -rl "package:digital/"` in `app/ui`, `app/theme`: 40 |
| Design-system counts | 29 `class Digital`, 96 `Color(0x` outside theme, 82 `TextStyle(` in features, `useMaterial3: false` |
| Feature graph | import edges: 64 pairs, 16 bidirectional; top edges listed above; 100 into `auth` |
| Router | `digital/lib/app/navigation/router.dart` 963 lines; 116 importers |
| Pilots | `support` 0 in / 0 out; `select_vehicle` 21 in / 1 out |
| Repositories | 26 files, 119 exports; single-feature users by `grep` |

## Sources for the recommendations

* Widgetbook, [Widgetbook in a monorepo](https://docs.widgetbook.io/guides/monorepo): one app for all packages, or one per package.
* Melos monorepo layering: [Flutter monorepo: scale shared code](https://kitemetric.com/blogs/flutter-monorepo-scale-shared-code-efficiently) (feature packages depend down, never up), [freeCodeCamp: monorepos in Flutter](https://www.freecodecamp.org/news/how-to-use-monorepos-in-flutter/).
* Mobile plan 11: Repo layout (target layout, rules), Mobile plan 13: Design system, Mobile plan 14: designer guide (tokens, DTCG, Figma variables).
