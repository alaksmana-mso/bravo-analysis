## Summary

Phase 10 of the agency apps roadmap ("Platform") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 5 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Platform". These items can run next to Phase 9 when the release rules hold.
* **Plan pages:** GENFI plan 01: Security step 7; GENFI plan 12: Design system step 4; GENFI plan 06: Lint and guardrails step 4; GENFI plan 03 step 5 (ownership); and the SQUARE twins.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 10 is.** The items that need a vendor, a budget or another squad: RASP, the shared Widgetbook and token pipeline in `frontend-mobile-ui`, and promoting the architecture checker to a lint. Each has its own entry gate.

### Facts that shape Phase 10

* **RASP.** `agent_tools` and `are_tracker` pin a local `flutter_jailbreak_detection` package with `IOSSecuritySuite < 2.0`; `agent_tools` also uses `device_integrity` (the BFI fork) and `shared_data/integrity` (0 tests). No RASP. The BFI app runs the vendor RFP and PoC (BFI Phase 1 step 1.24, Mobile plan 01a: RASP vendor comparison). Plan 01 step 7 says: **one vendor, one contract, three repos**; run the PoC on a prod-like GENFI build (the largest app) and a SQUARE build.
* **Design system.** After Phase 8, every app is on `ds_3` from `frontend-mobile-ui`. `ds_3` has no Widgetbook and no token pipeline. The BFI app's design-system work (BFI Phase 8 and Phase 10) is a separate package in a separate repo; the open decision "build our own or adopt DK's Jago library" (BFI assessment, open question 5) applies here too.
* **Lint.** The architecture checker from Phase 1 is a script with a baseline; plan 06 step 4 promotes the stable rules to `custom_lint` for IDE feedback once the baselines are near 0.
* **Material 3.** `ds_3` is the design system's concern; check its `useMaterial3` setting with the `frontend-mobile-ui` owners (question 3). Flutter made Material 3 the default in 3.16 and will remove Material 2 eventually.

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **D** = approved delta, **C** = flagged, **B** = same behaviour, **A** = no app change.

| # | Proposed ticket title | Entry gate | App | Class | Owner (role) | Size | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10.1 | RASP in prod, report-only mode first; fill the protect-and-register slot | Vendor chosen through the BFI PoC; SIT report-only trial on GENFI and SQUARE | GENFI, SQUARE, MY BISPRO | D | Security + Agency engineer + SRE | L | | |
| 10.2 | RASP enforce mode, one detection class at a time | 10.1 clean for 2 releases per app | all | D | Security + flag owner | S + 2 releases | | |
| 10.3 | Widgetbook for `ds_3` in `frontend-mobile-ui`, published on GitHub Pages per tag | Phase 8 done (one design system) | shared (`frontend-mobile-ui`) | A | Design-system owner + Agency engineer | M | | |
| 10.4 | Optional: Figma variables → `ds_3` tokens | Design keeps Figma variables current | shared | B | Design + Agency engineer | M | | |
| 10.5 | Promote stable checker rules to `custom_lint` | Baselines near 0 | shared | A | Agency engineer | M | | |

## Definition of ready

* The entry gate is met and written in the ticket.
* For 10.1 and 10.2: the PoC scorecard result and a false-positive budget per app are attached.
* Each ticket names its rollback (report-only, flag off, revert).

## Step 10.1: RASP in prod, report-only first

**Today.** No RASP in any agency app. The BFI PoC picks the vendor; the agency apps join the same contract. The prod workflows have an empty protect-and-register slot since Phase 2 (2.12).

**Tasks.** Integrate the vendor's build step (protect before sign) and build registration in the reusable workflows, so all three apps get it from one change. Ship in **report-only mode**: detections logged to Datadog with device model and OS, nothing blocked. Watch the report rate for 2 releases per app. A false-positive budget per app (GENFI's agents use a wider range of devices than SQUARE's managed fleet).

**Acceptance criteria.** The protected builds pass the parity net and the Phase 2 smoke lists. Report rate by device model on a dashboard per app. No crash-rate or cold-start regression beyond thresholds. App size change recorded.

**Who / size.** Security + one Agency engineer + SRE. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same vendor as the BFI app, report-only first, one reusable-workflow change for three apps | One contract, one integration, three apps | Waits for the BFI PoC |
| B. Free layer only (R8 explicit, root check default on, backend verdict checks) | No cost | Public checks are bypassable |
| C. Enforce from day one | Faster "protection" | Blocks agents on false positives; GENFI's device range makes this likely |

**Recommended: A.** B's items are already in Phases 2 and 3.

## Step 10.2: Enforce mode

**Tasks.** Blocking for one detection class at a time (rooted or jailbroken device, debugger, repackaged app, hooking), behind a remote switch per class. SQUARE first (managed devices, fewest surprises), then GENFI, then MY BISPRO. Support script for "the app says my device is not safe".

**Acceptance criteria.** Cohort dashboard green per class per app. Support tickets reviewed weekly for the first month. The switch returns to report-only within one journey start.

**Who / size.** Security + flag owner. S of code, 2 releases of watching per app.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One class at a time, SQUARE first | Each false-positive source found alone; the safest app first | Several weeks |
| B. All classes at once | Fast | A bad rule blocks many agents and nobody knows which |
| C. Enforce only on money journeys (reserve lead, company submission), report elsewhere | Protects what matters | A more complex policy to test |

**Recommended: A, moving to C's policy if support load is high.**

## Step 10.3: Widgetbook for `ds_3`

**Today.** No Widgetbook. `ds_3` lives in `frontend-mobile-ui`, which is not this monorepo.

**Tasks.** A Widgetbook app in `frontend-mobile-ui` with one use case per `ds_3` component and knobs for main states; built in CI on every PR that touches the package; published on GitHub Pages per tag.

**Acceptance criteria.** Designers and developers open the same URL to see every `ds_3` component.

**Who / size.** The `frontend-mobile-ui` owner + one Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Widgetbook in `frontend-mobile-ui` | Where the components live | Another repo's CI to set up |
| B. Widgetbook in the agency monorepo pointing at `ds_3` | Agency squad owns it | Duplicated when the BFI app wants one too |
| C. Adopt DK's Jago library and its Widgetbook | Exists today | A management decision (BFI assessment, open question 5) |

**Recommended: A**, unless C is chosen for BFI as a whole.

## Step 10.4: Optional, Figma tokens

**Tasks.** Export Figma variables (DTCG JSON) into `ds_3`; a small generator writes the token files; CI checks they match. Only if design commits to keeping Figma variables current.

**Acceptance criteria.** Generated tokens match the JSON in CI; component goldens unchanged after the first generation.

**Who / size.** Design + one Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own generator from a DTCG export | Small, no vendor | Design must keep Figma current |
| B. Tokens Studio or Style Dictionary | Standard tooling | More setup |
| C. Hand-maintained tokens | No work | Drift |

**Recommended: A if design commits; otherwise C with a quarterly review.**

## Step 10.5: Promote checker rules to `custom_lint`

**Today.** `tool/arch_check.dart` with baselines (Phase 1 step 1.10 and the Layering and State rules).

**Tasks.** For rules whose baseline is 0 (`domain-purity`, `flutter-in-shared_data`, `undeclared-import`): a `custom_lint` rule so the IDE shows the violation. Keep the script for ratchet rules with a non-zero baseline.

**Acceptance criteria.** The IDE flags a Flutter import in a domain file before CI does. CI and the lint agree.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `custom_lint` for zero-baseline rules only | IDE feedback where it is clean | Analyzer version pinning |
| B. `import_rules` analyzer plugin | First-party plugin route | Needs Dart 3.10+ across the workspace |
| C. Script only | No pinning pain | No IDE feedback |

**Recommended: A**, or B if the workspace is on Dart 3.10+ by then.

## Exit gate for Phase 10

* Per item: 10.1 report-only for 2 releases per app within budget; 10.2 enforce on with support reviewed; 10.3 Widgetbook published; 10.4 and 10.5 done or recorded as "not now" with a reason and a review date.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Does the BFI RASP contract cover three repos, and what is the false-positive budget for GENFI's device range? | Security + engineering manager | |
| Q2 | Who owns `frontend-mobile-ui` and its CI? | Design-system owner | |
| Q3 | What is `ds_3`'s Material 3 setting, and who plans the Material 2 removal? | `frontend-mobile-ui` owner | |
| Q4 | Does design commit to Figma variables for `ds_3`? | Design lead | |
| Q5 | Epic: one, or one per item since owners differ? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| RASP today | `agent_tools/pubspec.yaml` lines 40–74, `are_tracker/pubspec.yaml` lines 47–51 |
| Design systems | plan 12 "today" (GENFI and SQUARE) |
| Checker | Phase 1 step 1.10 |

## Sources for the recommendations

* GENFI plan 01: Security step 7; Mobile plan 01a: RASP vendor comparison; BFI Phase 10 refinement notes.
* Flutter, [Material 3 is the default](https://docs.flutter.dev/release/breaking-changes/material-3-default).
* Widgetbook, [Widgetbook in a monorepo](https://docs.widgetbook.io/guides/monorepo).
