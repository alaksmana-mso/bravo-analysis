**Priority 13 of 13.** Phase 3. Adoption of the shared components is already high, so this is polish.

## Goal

BFI's UI components and theme live in their own package. Each component can be seen and tried in Widgetbook without running the app. Colours, type and spacing come from named tokens, and later can be generated from Figma.

## Where we are today

Revision read: `bravo-customer-app` `master` @ `190e1d20`. Counts are from `grep` over `digital/lib/`, without generated files.

### What exists

| Item | Path | Size |
|---|---|---|
| Theme | `digital/lib/app/theme/` (6 files) | 1,569 lines |
| Colours | `theme/digital_colors.dart` | 44 `static const` colours, hard-coded hex |
| Typography | `theme/digital_text.dart` | 305 lines |
| Icons | `theme/hero_icon.dart`, `hero_icons.dart` | HeroIcons font |
| Material theme | `theme/app_theme.dart` | `useMaterial3: false` |
| Core components | `digital/lib/app/ui/components/` | 16 files |
| More components | `digital/lib/app/widget/components/` | 11 files (checkbox, chip, search bar, tooltip, …) |
| Loose UI helpers | `digital/lib/app/ui/` | scaffold, snackbar, shimmer, empty and loading states |
| Auto-tracking | `digital/lib/app/tracker/tracker_component_mixin.dart` | Used by `DigitalButton`, `DigitalTextField`, `DigitalSearchBar` |

There are 32 `Digital*` classes across `app/ui`, `app/widget` and `app/theme`.

### How well it is used

| Check | Count |
|---|---|
| Lines using `DigitalButton` | 250 (246 constructor calls) |
| Raw `ElevatedButton` / `TextButton` / `OutlinedButton` / `FilledButton` outside components | 0 |
| Lines using `DigitalColors.` | 1,040 |
| Raw `Color(0x…)` outside `app/theme/` | 49 |
| Lines using `DigitalText.` | 792 |
| `TextStyle(` outside `app/theme/` | 108 |

Note: the parent page quotes 454 `DigitalButton` uses, 795 `DigitalColors` and 39 raw colours. The counts above use a different grep (lines in `lib/` only, generated files excluded). The message is the same: the components are used well.

Rules exist in `AGENTS.md` ("Design System & Custom Components"): always `DigitalText`, use `DigitalScaffold`, `showDigitalDialog` and so on. But `AGENTS.md` also says "If not, use `Color(0xFF...)` directly", which invites raw colours.

### What blocks a separate package

- Components import app code: `app/analytics.dart`, `app/common/app_screen.dart`, localisation (`ui_text.dart`), intent launchers. 10 files in `app/ui` and `app/widget` import analytics or tracker code.
- `widget/components/bank_account_form.dart` imports a feature screen (`features/bank/select_bank/select_bank_screen.dart`). That is a feature form, not a design-system component.
- Tests: 8 component test files in `digital/test/app/ui/components/`. No golden tests (0 uses of `matchesGoldenFile`).
- No Widgetbook. No catalogue a designer can open.
- No token pipeline. Colours are typed by hand from Figma.

## Target (what Jago does, adapted for BFI)

| Jago pattern | Path | What it does |
|---|---|---|
| Design-system package | `module_design_library/` (98 Dart files, 40 tests) | Components under `lib/widgets/` (buttons, inputs, chips, modals, nudges, stepper …), tokens under `lib/design_tokens/` |
| Token source | `module_design_library/design_tokens_source.json` | Figma variables export, the single source of truth |
| Token generator | `module_design_library/generate_tokens.py` (878 lines) + `diff_tokens.py` | Writes one `.gen.dart` per Figma collection into `lib/design_tokens/generated/` (8 files). Fails if a brand is missing |
| Token docs | `module_design_library/TOKEN_ARCHITECTURE.md` | Explains how to read a token in a component |
| Widgetbook | `app_widget_book/` (63 Dart files) | A small app that shows every component with knobs. Published to GitLab Pages by the `pages` job in `.gitlab-ci.yml` |
| Token inspector | `library/token_inspector/` | In Widgetbook, hover a widget to see which tokens it uses |
| AI skills | `.claude/skills/add-component`, `update-design-tokens`, `add-token-inspection`, `add-brand` | Step-by-step guides for adding a component or applying a new Figma export |

How it maps to BFI:

- Package: `shared_lib/design_system/` (name to agree), added to the melos workspace. It depends only on Flutter and small pub packages. The app depends on it.
- Analytics: components do not call analytics directly. They take an optional `onTrack` callback, or the app injects a tracker through an `InheritedWidget`. The `TrackerComponentMixin` idea stays, but the Mixpanel link moves to the app.
- Riverpod: the package does not need Riverpod. Theme comes from `ThemeExtension` or an `InheritedWidget`, like Jago's `DesignThemeProvider`.
- Widgetbook: `shared_lib/design_system/widgetbook/` or `apps/widgetbook/`. Published as a static web build.

**Do not copy:** Jago's multi-brand and theme-mode matrix (BFI ships one brand). The token inspector, until a designer asks for it. The Figma token pipeline, until BFI's Figma file uses variables consistently. Jago's token values or brand names.

## Plan

### Step 1: agree the scope (no code, 1 week)

- With design, list which of the 32 `Digital*` classes are real design-system components. Mark feature-specific ones (`bank_account_form`, `bfi_banner`, `loan_amount_field_badge`) to stay in the app.
- Agree token names for colour, text, spacing, radius. Start from what `DigitalColors` and `DigitalText` already use.

### Step 2: cut the app dependencies (1–2 PRs)

- Replace direct analytics calls in components with an `onTrack` callback or an injected `ComponentTracker` interface.
- Pass localised strings in as parameters instead of reading `ui_text.dart`.
- Move `bank_account_form.dart` to `features/bank/`.
- Check: `grep "package:digital/" digital/lib/app/ui/components digital/lib/app/theme` returns 0 lines.

### Step 3: create the package and move code (2–3 PRs, one folder at a time)

- Create `shared_lib/design_system/` with `pubspec.yaml` (`resolution: workspace`).
- Move `app/theme/` first. Then `app/ui/components/`. Then the generic parts of `app/widget/components/`.
- Leave a re-export file in the app for one release, so feature code keeps compiling. Then update imports and delete the re-export.
- Move the 8 component tests along with the code.
- Check: `melos test` passes. The app has no `Digital*` class definitions left outside the package.

### Step 4: add Widgetbook (1–2 PRs)

- Add a Widgetbook app with one use case per component and knobs for main states (enabled, disabled, loading, error).
- Build it in CI as a Flutter web build on every PR that touches the package.
- Publish it from `master` to an internal static site (GitHub Pages on a private repo, or a GCS bucket behind IAP).
- Check: a designer can open the link and see every component.

### Step 5: guard the rules (1 PR)

- Fix the `AGENTS.md` line about `Color(0xFF...)`. New rule: add a token instead.
- Add a lint or a CI grep that fails a PR which adds a new `Color(0x…)` or `TextStyle(` outside the package (ratchet: old ones are allowed until touched).
- Add golden tests for the top components (button, text field, dialog, bottom sheet). Run them on Linux CI only, to keep pixels stable.

### Step 6 (optional): Figma token pipeline

Only start this if design keeps Figma variables up to date.

- Export Figma variables as JSON into the package (`tokens/source.json`).
- Write a small generator (Dart or Python) that writes `lib/tokens/*.g.dart`. Keep it simple: one brand, light mode only.
- Add a CI check that the generated files match the JSON.
- Add a short skill file (`.claude/skills/update-design-tokens/SKILL.md`) that explains the steps. Write it in our own words.

### Step 7 (optional): Material 3

`app_theme.dart` sets `useMaterial3: false`. Flutter's Material 2 support is shrinking. Plan the switch inside the package, with golden tests in place first.

### Parity check

- Cutting the app dependencies (step 2) and moving components into `shared_lib/design_system` (step 3) must not change a pixel or an event.
- Before step 2, add golden screenshots of every `Digital*` component that moves, in its main states (enabled, disabled, loading, error). Run them on Linux CI.
- The same golden files must pass before and after the package move. A changed pixel fails the PR.
- Step 2 replaces direct analytics calls with `onTrack` or `ComponentTracker`. Automatic Mixpanel tracking runs through these components, so the analytics golden names file (Mobile plan 02: Analytics wrapper) must stay unchanged.
- Passing localised strings in as parameters must show the same text. The golden screenshots catch a wrong string.
- Approved deltas: none in the move. Material 3 (step 7) is a visual change. It needs its own approved delta from design and new golden files.

## Done when

- `shared_lib/design_system/` exists and the app depends on it.
- 0 `Digital*` component classes are defined in `digital/lib/`.
- 0 imports from the design-system package into `package:digital/`.
- Widgetbook is published from `master` and shows every component.
- CI fails a PR that adds a new raw `Color(0x…)` in `digital/lib/` outside the package.
- Golden tests cover at least 4 core components.
- (Optional) Token files are generated from the Figma JSON, and CI checks they are in sync.
- Golden screenshots of every moved `Digital*` component are identical before and after the package move.
- The analytics golden names file is unchanged by steps 2 and 3.

## Effort and owner

- **M** from the parent table. About 3 sprints for steps 1–5, run next to feature work.
- Step 6 (tokens) is another 1–2 sprints, only if design is ready.
- Owner: Customer Mobile Apps squad, with one named designer as co-owner.

## Depends on / related plans

- Mobile plan 11: Repo layout (where the new package sits in the workspace).
- Mobile plan 02: Analytics wrapper (the `ComponentTracker` interface should use the same analytics interface).
- Mobile plan 03: Testing (golden tests, component tests).
- Mobile plan 06: Lint and guardrails (raw colour and import rules).
- Mobile plan 04: CI/CD (Widgetbook build and publish job).

## Risks

| Risk | Mitigation |
|---|---|
| Moving code breaks many imports at once | Re-export file for one release; move one folder per PR |
| Auto-tracking events change names after the refactor | Snapshot the Mixpanel event names in a test before and after |
| Widgetbook rots because nobody updates it | `add-component` skill and PR checklist: new component means new use case |
| Golden tests are flaky across machines | Run them only in CI on one Linux image; update with a script |
| Figma variables are incomplete, so generated tokens are wrong | Keep the pipeline optional; design signs off each export |
| Widgetbook site leaks unreleased UI | Host it behind company login, not public Pages |
