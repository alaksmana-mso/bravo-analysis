## Summary

Phase 6 of the agency apps roadmap ("Riverpod 3 upgrade on its own") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 4 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Riverpod 3".
* **Plan pages:** GENFI plan 08: State management steps 1–2 (and SQUARE plan 09).
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 6 is.** One shared dependency upgrade (`shared_lib/core` re-exports `flutter_riverpod`), shipped as **three separate app releases** with nothing else in them. No controller is converted; the legacy `StateNotifier` API keeps compiling through Riverpod's `legacy.dart`. The point is to pay the runtime-behaviour cost of Riverpod 3 once per app, in isolation, so the pilots (Phase 7) start on a settled base.

### Numbers per app

| App | `StateNotifier` classes | `valueOrNull` uses | `static final provider` |
| --- | --- | --- | --- |
| GENFI (`agent_tools`) | 96 | 180 | 104 |
| SQUARE (`are_tracker`) | 82 | 158 | 103 |
| MY BISPRO (`mybispro`) | 61 | 46 | 70 |

`flutter_riverpod` is 2.6.1 (locked). The agency apps have **no global `appRef`** (better than the BFI app), but they do `ref.watch` inside callbacks and keep business rules inside controllers (plan 08). `shared_data` packages depend on Riverpod only for provider declarations.

### What Riverpod 3 changes at run time

From the official migration guide; the full table is on the BFI Phase 6 refinement notes.

| Change | What it means here | What we do |
| --- | --- | --- |
| Automatic retry of failing providers | Error screens could flicker or appear later | `retry: (count, error) => null` on each root `ProviderScope` and in the test container helper |
| Out-of-view providers pause | Background tabs, timers and polling stop; no global switch | Audit per app; wrap with `TickerMode(enabled: true)` where needed |
| Using a `Ref` after dispose throws `UnmountedRefException` | `ref.watch` inside callbacks is the main risk here | `ref.mounted` guards after awaits; the Event wrapper and `guardLog` template (step 6.2) make this the default |
| Legacy providers moved to `legacy.dart` | 239 `StateNotifier` classes across the apps | Export `legacy.dart` from `core.dart` |
| All providers filter with `==` | Stream providers that emit equal values stop rebuilding | Check refresh triggers |
| `ProviderObserver` interface changed | `ErrorLoggingProviderObserver` must be rewritten | One small change with a test |
| `Ref` subclasses and AutoDispose types removed; `ProviderException` | Analyzer-driven renames; `catch` blocks that check error types | Fix what the analyzer flags |

`valueOrNull`: plan 08 says "rename"; the migration guide does not list it as removed. Treat as unconfirmed; let the analyzer decide.

## Steps at a glance

| # | Proposed ticket title | Today (24 Oct) | App | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1 | `build(deps): Riverpod 3 in core, legacy export, observer, analyzer fixes` | 2.6.1 | shared | B | Agency engineer | M | Phases 2 and 5 gates | | |
| 6.2 | `feat(core): Event wrapper, guardLog and the Notifier state template; retry off; TickerMode audit; mounted guards` | None | shared + apps | B | Agency engineer | M | 6.1 | | |
| 6.3 | Release GENFI alone, staged, watched | – | GENFI, MyShaf | B | Release manager + on-call | 1 release | 6.2 | | |
| 6.4 | Release SQUARE alone, then MY BISPRO alone | – | SQUARE, MY BISPRO | B | Release manager + on-call | 2 releases | 6.3 | | |

**Suggested order.** 6.1 and 6.2 on one branch over 1–2 sprints, merged right after the release branches are cut. Then one app release per cycle, GENFI first (largest), SQUARE, MY BISPRO.

## Definition of ready

* Each app's release calendar shows the Riverpod release with no other class B, C or D change in it.
* The parity net (goldens, fixtures, e2e, both-paths helper) is green on `master` for that app before its release.
* The rollback is the staged rollout: halt at the first stage and hotfix with the previous version. The ticket names who decides.

## Step 6.1: Upgrade with no conversions

**Today.** `flutter_riverpod` 2.6.1 through `core`. 239 `StateNotifier` classes across the apps. `ErrorLoggingProviderObserver` implements the 2.x observer.

**Tasks.** Bump in `shared_lib/core/pubspec.yaml`; `export 'package:flutter_riverpod/legacy.dart';` from `core.dart`; rewrite the observer for `ProviderObserverContext`; fix analyzer findings; rename `valueOrNull` only if the analyzer says so.

**Acceptance criteria.** `melos analyze` and `melos test:*` pass for all three apps. `state-notifier` ratchet unchanged. Observer test passes.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Upgrade only, legacy export, no conversions | Smallest change per release | The legacy import stays until Phase 9 |
| B. Upgrade and convert the pilot features in the same release | Less total work | Two risks in one release |
| C. Stay on Riverpod 2 | No work now | Every later phase builds on an API that is on its way out |

**Recommended: A.**

## Step 6.2: Keep today's behaviour, and the state template

**Today.** Providers do not retry; out-of-view listeners keep running; stale refs work silently. Plan 08 step 2 asks for an `Event` wrapper, a `guardLog` helper and a Notifier state template that every migrated notifier will use.

**Tasks.** `retry` off on each root `ProviderScope` and in the test helper. Audit screens that rely on background updates (notifications, chat, timers) per app and wrap them. `ref.mounted` guards after awaits in flows. `Event` wrapper + `guardLog` + the state template in `core` (used from Phase 7 on; nothing converted yet).

**Acceptance criteria.** A test shows a failing provider does not retry. The `TickerMode` list per app is in the ticket. No new `UnmountedRefException` on SIT after one day of dev use per app.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Retry off, targeted `TickerMode`, mounted guards, template ready | Today's behaviour kept; later differences are conscious | The audit is the work |
| B. Accept Riverpod 3 defaults | Less code | Two behaviour changes on every screen at once |
| C. Retry off only | Half the audit | A background timer stops silently |

**Recommended: A.**

## Step 6.3: GENFI release alone

**Tasks.** Manual SIT smoke (login, OTP, registration, prospect input, calculator, reserve lead, chat, notifications). Play 5% → 20% → 50% → 100% with the release health dashboard; watch Datadog Error Tracking for new provider signatures and `UnmountedRefException`. iOS phased release. MyShaf is the same binary: watch its dashboard too.

**Acceptance criteria.** 1 GENFI release at 100% within thresholds and with no new provider error signature.

**Who / size.** Release manager + on-call. One release cycle.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own release, staged, watched | Clean attribution | One release slot for an invisible change |
| B. Ride along with a feature release | No slot used | Cannot attribute a problem |
| C. Internal testers for a week first | Extra safety | One more week; worth it if 6.2 found many hot spots |

**Recommended: A**, C if the audit found more than a handful of changes.

## Step 6.4: SQUARE, then MY BISPRO

**Tasks.** Same as 6.3 per app. SQUARE: 20% → 100% (internal). MY BISPRO: 20% → 100%.

**Acceptance criteria.** 1 release per app at 100% with no new provider errors.

**Who / size.** Release manager + on-call. Two cycles.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One app per cycle | Each watched alone | Three cycles |
| B. SQUARE and MY BISPRO together | One cycle | Two apps' errors mixed on the dashboard |
| C. All three at once | Fastest | Against the one-risky-change rule |

**Recommended: A.**

## Exit gate for Phase 6

* 1 release per app at 100% with no new provider errors and no health regression.
* `state-notifier` ratchet unchanged. Retry off and documented. The `TickerMode` lists on the plan pages.
* The `Event` wrapper, `guardLog` and the state template exist in `core` with tests.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which release slots take the three Riverpod releases? | Release manager + squad lead | |
| Q2 | Which screens rely on background updates per app (chat, notifications, timers)? | Agency squad | |
| Q3 | `riverpod_lint` on in the same PR? | Squad lead | |
| Q4 | Epic: one, with one ticket per app release? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Counts per app | `grep` for `extends StateNotifier<`, `valueOrNull`, `static final provider` per `lib`, generated files excluded |
| Version | `pubspec.lock`: flutter_riverpod 2.6.1 |
| Breaking changes | Riverpod 3.0 migration guide |

## Sources for the recommendations

* Riverpod, [Migrating from 2.0 to 3.0](https://riverpod.dev/docs/3.0_migration); [What's new in 3.0](https://riverpod.dev/docs/whats_new).
* BFI Phase 6 refinement notes (full change table).
* GENFI plan 08 and SQUARE plan 09, section "Riverpod 3 upgrade".
