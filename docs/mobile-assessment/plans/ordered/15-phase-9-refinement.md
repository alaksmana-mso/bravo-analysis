## Summary

This page prepares Phase 9 of the mobile roadmap ("Other features through the same loop") for refinement. It covers the 6 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Remaining Features". One sub-epic per feature is also an option (Q5).
* **Parent:** Mobile roadmap: step by step, section "Phase 9: Other features through the same loop". Plan pages: Mobile plan 08 step 11, Mobile plan 09 steps 6–7, Mobile plan 11 steps 9–10, Mobile plan 10 steps 6 and 8.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct).

**What Phase 9 is.** The loop proven on `loan` in Phase 7 (ledger → slices behind a switch flag → both paths green → cohort → flip → delete) and the extraction proven in Phase 8, repeated for `auth`, `rl`, `ro` and the rest. One feature's rollout at a time. Each feature has its own switch flag, ledger and exit gate. By the end, no `StateNotifier`, no `appRef`, no `navigatorContext` outside `app/navigation/`, and `data/customer` is empty.

### The work, measured today

| Feature | Files | Lines | `StateNotifier` controllers | Edges out | Edges in | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `auth` | 40 | 9,283 | 6 | 21 | 100 | `kyc_use_case` 1,049 lines with 23 `appRef` and 37 `navigatorContext`; `auth_flow_use_case` 343 (19 / 11); `kyc_spouse_use_case` 375 (7 / 18); `capture_use_case` 152 (14 / 8) |
| `ro` | 42 | 12,080 | 8 | 63 | 21 | Most outgoing edges of any feature (plan said 35). `ro_use_case` 304 lines (9 / 2) |
| `rl` | 34 | 6,765 | 8 | 18 | 17 | Balanced; shares `RlRepository` and `CommonRepository` with `loan` |
| `home` | 22 | 4,104 | 5 | 55 | 2 | Reads everything; a consumer of `*_api` packages, not a package itself at first |
| Remaining | – | – | 36 | – | – | `select_vehicle` 6 (moved in 8.10), `bpkb_release` 3, `app/` 3, `support` 2 (moved in 8.7), `splash` 2, `onboarding` 2, `domicile_address` 2, and 12 features with 1 each |

Total `StateNotifier` controllers today: 89 (30 in `loan`, done in Phase 7). `appRef.` 131 uses, `navigatorContext` 166 uses (Phase 7 removes the `loan` and service share). `CommonController` is read 63 times and goes last.

Repository ownership by `grep` today: `auth` owns `AccountRepository`, `RateLimitRepository`, `UserVerificationRepository`; `rl` owns `BankAccountRepository`; shared: `AuthRepository` (`account`, `auth`, `pin`), `RlRepository` and `CommonRepository` (`loan`, `rl`), `RoRepository` (`loan`, `ro`), `StaticConfigRepository` (9 features).

## Steps at a glance

Sizes in sprints. Class **C** = behind the feature's switch flag, then **B** for the extraction.

| # | Proposed ticket title | Today (23 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9.1 | `auth` through the loop: ledger, `useNewKycFlow`, split KYC flows, domain, Notifiers, cohort, flip, delete, then extract | 40 files, 6 controllers, 100 edges in | C, then B | Feature owner + 2 engineers | 5–6 sprints | 7.12, 8.9 | | |
| 9.2 | `rl` through the loop | 34 files, 8 controllers | C, then B | Feature owner + 1 engineer | 3 sprints | 9.1 past 50% | | |
| 9.3 | `ro` through the loop | 42 files, 8 controllers, 63 edges out | C, then B | Feature owner + 1–2 engineers | 4 sprints | 9.2 past 50% | | |
| 9.4 | Remaining features: 36 controllers, by size; `CommonController` last | 12 features with 1 controller, 6 with 2–3 | C or B by size | Mobile engineers | 3–4 sprints | 9.3 | | |
| 9.5 | `refactor(core): Remove the legacy Riverpod layer and the global appRef` | `legacy.dart` export, `late WidgetRef appRef` | B | Mobile engineer | S | 9.4 | | |
| 9.6 | `refactor(data): Shared service ports, shrink barrels, empty data/customer` | 26 repository files, 119 exports | B | Mobile engineer | 2 sprints | 9.1–9.3 | | |

**Suggested order.** `auth` first (it blocks the most), `rl`, `ro`, then the small ones. Start a feature's rollout only when the previous one is past 50%, so two cohort checks do not overlap on one journey. About 4 quarters in total at one feature at a time, less with two feature teams.

## Definition of ready for every Phase 9 ticket

* The feature's ledger exists and is signed before the first slice (same as 7.3).
* The feature's switch flag is in the catalogue with owner and removal date.
* The Phase 7 write-up ("how we did loan") is linked, and the ticket says what is different for this feature.
* The extraction sub-ticket is "move only" with goldens unchanged (same as Phase 8).

## Step 9.1: `auth`

**Today.** 40 files, 9,283 lines, 6 controllers. The KYC flows hold the most globals in the app: `kyc_use_case` 1,049 lines (23 `appRef`, 37 `navigatorContext`), `auth_flow_use_case` 343 (19 / 11), `kyc_spouse_use_case` 375 (7 / 18), `capture_use_case` 152 (14 / 8). 100 edges in from other features; after 8.9 most go through `auth_api`.

**Tasks.** Ledger (`docs/parity/auth.md`) from the register, login, OTP, PIN and KYC journeys. `useNewKycFlow` flag. Split `kyc_use_case` and `kyc_spouse_use_case` into domain use cases plus flow classes (as 7.9 did for e-sign). Convert the 6 controllers. Cohort 1% → 10% → 50% → 100% watching register and KYC completion funnels. Flip and delete. Then extract to `features/auth`, with `auth_api` implementations moving in.

**Acceptance criteria.** Same as 7.3 to 7.12 for `auth`: ledger green on both paths, e2e register and KYC specs pass flag off and on, cohort thresholds met, old path deleted, `dto-in-presentation`, `state-notifier`, `app-ref` for `auth` all 0, then `features/auth/pubspec.yaml` lists no feature package.

**Who / size.** Feature owner + 2 engineers. 5–6 sprints.

**Risks.** KYC uses vendor SDKs (Vida liveness, document detection). The new flow must drive the same SDK calls in the same order. Record each SDK call in the fixtures (1.13) and compare.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same loop as `loan`, KYC flows first | The hardest globals go first while the team is fresh from Phase 7 | KYC is the most sensitive journey; cohort stages need an extra day each |
| B. Convert controllers first, flows later | Early wins | The flows are where the risk is; converting around them changes little |
| C. Two flags (`useNewKycFlow`, `useNewAuthFlow`) | Finer rollback | Two cohorts on overlapping journeys (login leads into KYC) |

**Recommended: A**, with C only if the ledger shows login and KYC never share a screen.

## Step 9.2: `rl`

**Today.** 34 files, 6,765 lines, 8 controllers, 18 edges out, 17 in. Shares `RlRepository` and `CommonRepository` with `loan`.

**Tasks.** Same loop. `useNewRlFlow`. The shared repositories stay with `loan` (the owner); `rl` reads through a small `loan_api` reader or its own copy of the calls (decide in the ledger).

**Acceptance criteria.** Same pattern. Revolving-loan e2e (home-revolving-loan spec) passes both paths.

**Who / size.** Feature owner + 1 engineer. 3 sprints.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same loop, shared repositories through `loan_api` | Consistent | `loan_api` grows by two readers |
| B. Duplicate the shared calls into `rl` | No cross-package dependency | Two copies of the same API client |
| C. Skip the flag for `rl` (smaller feature) | Faster | A revolving-loan bug reaches every RL customer at once |

**Recommended: A.**

## Step 9.3: `ro`

**Today.** 42 files, 12,080 lines, 8 controllers, **63 edges out** (into `loan` 29, `auth` 27), 21 in. `ro_use_case` 304 lines (9 / 2).

**Tasks.** Same loop. `useNewRoFlow`. The 63 outgoing edges go through `loan_api`, `auth_api` and exit ports before extraction.

**Acceptance criteria.** Same pattern. Repeat-order e2e (home-repeat-order spec) passes both paths. `ro` edges out reach 0 before the move.

**Who / size.** Feature owner + 1–2 engineers. 4 sprints.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Decouple edges first, then the loop | The package move at the end is a pure move | A sprint of port work before visible progress |
| B. Loop first, edges during extraction | Earlier cohort | 63 edges rewritten in the move PR; not "move only" |
| C. Merge `ro` into `loan` as a sub-feature | Fewer packages | `ro` is a different journey with its own owner; it hides the edges rather than cutting them |

**Recommended: A.**

## Step 9.4: Remaining features

**Today.** 36 controllers outside `loan`, `auth`, `rl`, `ro`: `select_vehicle` 6 (already a package after 8.10), `bpkb_release` 3, `app/` 3, `support` 2 (package after 8.7), `splash` 2, `onboarding` 2, `domicile_address` 2, and 12 features with 1 each (`search_city`, `promo`, `pin`, `payment_method`, `payment`, `notification`, `lov`, `document`, `dev_mode`, `branch_info`, `bank`, `account`). `CommonController` (in `app/`) is read 63 times.

**Tasks.** By size. Features with 1 controller and no journey of their own convert as class B with screen tests (no flag). `pin`, `payment`, `onboarding` get a flag because they sit on money or sign-in paths. `CommonController` goes last, after 7.4's port has removed every direct read.

**Acceptance criteria.** `state-notifier` ratchet reaches 0. Each converted notifier has a test. Payment and PIN journeys pass both paths.

**Who / size.** Mobile engineers between other work. 3–4 sprints.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flag only where money or sign-in is involved; class B elsewhere | Proportionate | Judgement call per feature; write the rule down |
| B. Flag everything | Uniform | 18 flags, 18 cohorts for one-screen features |
| C. Flag nothing | Fast | A PIN screen regression reaches everyone |

**Recommended: A.** Rule: a switch flag when the feature is on a journey in the parity net (register, KYC, loan submission, payment, PIN).

## Step 9.5: Remove the legacy Riverpod layer

**Today.** `legacy.dart` exported from `core.dart` since 6.1. `late WidgetRef appRef` still declared.

**Tasks.** Delete the export and the global. Delete `navigatorContext` outside `app/navigation/`.

**Acceptance criteria.** The app compiles. `app-ref` and `navigator-context` ratchets at 0; the rules become strict (any use fails).

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete when the ratchets hit 0 | Clean | Waits for the last feature |
| B. Delete early and fix the stragglers in the same PR | Forces the end | Risky if stragglers sit in a flow under rollout |
| C. Keep the export "for compatibility" | None | The legacy API stays available to new code |

**Recommended: A.**

## Step 9.6: Shared service ports, barrels, empty `data/customer`

**Today.** 26 repository files, 119 exports in `customer.dart`. Device services used by flows (`FileService`, `CameraService`, `ImagePickerService`, `VidaLivenessService`, IPV) have no ports. `core.dart` re-exports `go_router`.

**Tasks.** Each extraction takes its own repositories (9.1–9.3). Shared reference data (`StaticConfigRepository` used by 9 features, address, branch, vehicle, bank, LOV) moves to `shared_lib/master_data` with its own domain and data layers. Transport (`http_client`, `gcs_client`, device integrity) moves to `shared_lib/network` (Phase 4 made it small). Device services become ports when the first package needs them. Drop exports from `customer.dart` as files leave; stop re-exporting `go_router` from `core.dart`.

**Acceptance criteria.** `customer-repo-growth` ratchet reaches 0. `customer.dart` deleted or empty. `core.dart` exports no router. Each `shared_lib/*` package has a barrel that exports ports and providers only.

**Who / size.** One mobile engineer, riding on each extraction. 2 sprints of dedicated work at the end.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Repositories move with their feature; shared data to `master_data`; transport to `network` | Each package owns its data | Three destinations to keep straight; write the map in the ticket |
| B. Keep `data/customer` as a "data" package forever | No moves | Every feature depends on everything; the package boundary is fiction |
| C. One repository per package, no shared `master_data` | Simple rule | 9 features would copy the static-config client |

**Recommended: A.**

## Exit gate for Phase 9

* Every feature's old path deleted. All switch flags removed. Every feature with a journey in the parity net has its ledger signed and closed.
* `state-notifier`, `app-ref`, `navigator-context` (outside `app/navigation/`), `dto-in-presentation`, `feature-import`, `router-import` all 0 and strict.
* `data/customer` empty. `legacy.dart` export gone.
* The written loop template has been used four times without changes, or the changes are folded back into it.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Can `auth` get 2 engineers for 5–6 sprints? | Engineering manager | |
| Q2 | Do the Vida and document-detection SDK calls appear in the recorded fixtures, so the new KYC flow can be compared call by call? | Mobile squad + QA | |
| Q3 | Which small features count as "on a money or sign-in path" and get a flag? | Product + squad lead | |
| Q4 | Who owns `shared_lib/master_data` and `shared_lib/network` once they exist? | Squad lead | |
| Q5 | One epic for Phase 9, or one epic per feature (`auth`, `rl`, `ro`, rest)? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Feature sizes | `git ls-files` + `wc -l` per feature, generated files excluded |
| Controllers per feature | `grep -rl "extends StateNotifier<"` per folder |
| Edges | import graph of `package:digital/features/<x>/` across features |
| Globals in flows | `grep -c appRef` and `navigatorContext` per flow file |
| Repositories | `grep` of each `*Repository` class across `digital/lib/features` |

## Sources for the recommendations

* Phase 7 refinement notes (the loop), Phase 8 refinement notes (move-only extraction).
* Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html): the discipline is finishing, not starting.
* Mobile plan 08 step 11, Mobile plan 09 steps 6–7, Mobile plan 11 steps 9–10, Mobile plan 10 steps 6 and 8.
