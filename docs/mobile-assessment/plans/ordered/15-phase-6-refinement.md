## Summary

This page prepares Phase 6 of the mobile roadmap ("Riverpod 3 upgrade on its own") for refinement. It covers the 3 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Riverpod 3".
* **Parent:** Mobile roadmap: step by step, section "Phase 6: Riverpod 3 upgrade on its own". Plan page: Mobile plan 09: State management, step 2.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct), `pubspec.lock`, and the Riverpod 3.0 migration guide.

**What Phase 6 is.** One dependency upgrade that touches every screen, shipped in a release with nothing else. No controller is converted. The 89 `StateNotifier` classes keep compiling through Riverpod's `legacy.dart` import. The point is to pay the runtime-behaviour cost of Riverpod 3 once, in isolation, so the loan pilot (Phase 7) starts on a settled base.

### What Riverpod 3 changes at run time (from the official migration guide)

| Change | What it means for this app | What we do |
| --- | --- | --- |
| **Automatic retry.** Failing providers retry by default | A provider that throws (network down, parse error) now retries on a delay instead of staying in error. Error screens could flicker or appear later | Turn retry **off** globally with the `retry` parameter on `ProviderScope` and in test containers, to keep today's behaviour. Decide per provider later (approved delta) |
| **Out-of-view providers are paused.** Listeners in widgets that are not visible pause | A background tab or a route under the top one stops reacting. There is no global switch; `TickerMode(enabled: true)` keeps a subtree live | Audit screens that rely on background updates (notifications badge, timers, polling). Wrap those with `TickerMode` |
| **Using a `Ref` after dispose throws** `UnmountedRefException` | Any `await` followed by `ref.read` in a disposed provider now crashes instead of silently working | Guard with `ref.mounted` after every `await` in notifiers and flows. The global `appRef` pattern (131 uses) is the main risk |
| **Legacy providers moved** to `legacy.dart` | `StateProvider`, `StateNotifierProvider`, `ChangeNotifierProvider` (98 references) need the import | Export `legacy.dart` from `core.dart` so nothing else changes |
| **All providers filter updates with `==`** | Stream and async providers that emit equal values no longer rebuild listeners | Mostly fine. Check providers that emit the same object on purpose (refresh triggers) |
| **`ProviderObserver` interface changed** to a single `ProviderObserverContext` | `DatadogLogObserver` must be rewritten | One small change, with its test |
| **`Ref` subclasses removed**, **AutoDispose interfaces removed**, **family Notifier types removed** | Affects generated code mostly; the app does not use `riverpod_generator` | Rename where the analyzer complains |
| **Provider failures rethrown as `ProviderException`** (3.4) | `catch (e)` that checks the error type must read `e.exception` | Audit `catch` blocks around `ref.read` and `ref.watch` |

**`valueOrNull`.** Plan 09 says "rename `valueOrNull` (146)". The 3.0 migration guide does not list it as removed and even uses it in a sample. 185 uses today. **Treat the rename as unconfirmed**: run the upgrade on a branch and let the analyzer decide.

Versions today: `flutter_riverpod` 2.6.1 (pubspec says `^2.1.1`), `freezed` 2.5.8, `firebase_core` 3.15.2, `go_router` 17.2.1. `AsyncValue` and `.when(` appear 361 times.

## Steps at a glance

| # | Proposed ticket title | Today (23 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6.1 | `build(deps): Riverpod 3, legacy export, observer, analyzer fixes` | 2.6.1 | B | Mobile engineer | M | Phases 2 and 5 exit gates | | |
| 6.2 | `fix(core): Retry off, TickerMode audit, ref.mounted guards` | Riverpod 2 behaviour | B | Mobile engineer | M | 6.1 | | |
| 6.3 | Release alone with the full parity net and staged rollout | – | B | Release manager + on-call | 1 release | 6.1, 6.2 | | |

**Suggested order.** 6.1 and 6.2 on one branch over 1–2 sprints, merged together right after a release branch is cut, so the upgrade has the full 2-week cycle on SIT and UAT before its prod release. 6.3 is that release.

## Definition of ready

* The release calendar shows the Riverpod release with no other class B, C or D change in it. Feature PRs merged in that window are small and reviewed for Riverpod impact.
* The parity net (goldens, fixtures, e2e, both-paths helper) is green on `master` before the branch merges.
* The kill-switch runbook does not apply (no flag). The rollback is the staged rollout: halt at 5% or 20% and hotfix with the previous version. The ticket says who decides.

## Step 6.1: Upgrade with no conversions

**Today.** `flutter_riverpod` 2.6.1 in `shared_lib/core`. 89 `StateNotifier` classes, 98 legacy provider references, `DatadogLogObserver` implements the 2.x `ProviderObserver`.

**Tasks.** Bump to `^3.x` in `shared_lib/core/pubspec.yaml`. Add `export 'package:flutter_riverpod/legacy.dart';` to `core.dart`. Rewrite `DatadogLogObserver` for `ProviderObserverContext`. Fix whatever the analyzer flags (`Ref` subclasses, AutoDispose names, family notifiers, `ProviderException`). Rename `valueOrNull` only if the analyzer says so.

**Acceptance criteria.** `melos run analyze` and `melos test` pass. Zero controllers converted (ratchet `state-notifier` count unchanged). `DatadogLogObserver` test passes.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Upgrade only, legacy export, no conversions | Smallest change per release. Conversions come feature by feature in Phase 7 | The legacy import stays until Phase 9 |
| B. Upgrade and convert the 30 `loan` controllers in the same release | Less total work | Two risks in one release; against the "one risky change" rule |
| C. Stay on Riverpod 2 until the end of the roadmap | No work now | The legacy API ages; Riverpod 2 gets fewer fixes; every later phase builds on an API that is on its way out |

**Recommended: A.**

## Step 6.2: Keep today's behaviour

**Today.** Providers do not retry, out-of-view listeners keep running, a stale `Ref` works silently.

**Tasks.** `retry: (count, error) => null` on the root `ProviderScope` and in the test container helper. Audit screens that rely on background updates and wrap them in `TickerMode(enabled: true)` where needed. Add `if (!ref.mounted) return;` after awaits in notifiers and flows that outlive a screen. Audit `catch` blocks around provider reads for `ProviderException`.

**Acceptance criteria.** A test shows a failing provider does not retry. A list of screens checked for background updates is in the ticket, with the ones wrapped. No new `UnmountedRefException` in Datadog after one day on SIT with the dev team using the app.

**Who / size.** One mobile engineer. M (the audit is the work).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Retry off globally, targeted `TickerMode`, mounted guards | Today's behaviour kept; each difference is a conscious later decision | The audit needs care; the global `appRef` makes stale refs likely |
| B. Accept Riverpod 3 defaults (retry on, pause on) | Less code | Two behaviour changes for every screen at once, untested against our flows |
| C. Retry off, ignore pausing | Half the audit | A background badge or timer stops silently |

**Recommended: A.**

## Step 6.3: Release alone

**Today.** Prod releases ship about every 2 weeks through the staged rollout (Phase 1).

**Tasks.** Manual SIT smoke on login, KYC, loan apply, payment, notifications. Play 5% → 20% → 50% → 100% with the release health dashboard. Watch Datadog for new provider errors and `UnmountedRefException`. iOS phased release.

**Acceptance criteria.** 1 release at 100% with crash-free sessions and error rate within thresholds, and no new provider error signature in Datadog Error Tracking.

**Who / size.** Release manager + mobile on-call. One release cycle.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own release, staged, watched | Clean attribution if something breaks | One release slot used for an invisible change |
| B. Ride along with a feature release | No slot used | A problem cannot be attributed; against the release rules |
| C. Internal testers first for one week, then staged | Extra safety | One more week; worth it if 6.2's audit found many hot spots |

**Recommended: A**, with C if the audit found more than a handful of `TickerMode` or mounted changes.

## Exit gate for Phase 6

* 1 release at 100% with no new provider errors and no health regression.
* `state-notifier` ratchet unchanged (no conversions slipped in).
* Retry is off and documented. The `TickerMode` list is on Mobile plan 09.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which release slot takes the Riverpod upgrade, and can the squad hold other risky merges for that cycle? | Release manager + squad lead | |
| Q2 | Which screens rely on background updates (badges, timers, polling)? | Mobile squad | |
| Q3 | Do we want `riverpod_lint` on in the same PR to catch misuse early? | Squad lead | |
| Q4 | Epic for Phase 6: one epic with 3 tickets, or one ticket? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Versions | `pubspec.lock`: flutter_riverpod 2.6.1, freezed 2.5.8, firebase_core 3.15.2, go_router 17.2.1 |
| Legacy usage | `grep`: 98 legacy provider references, 89 `extends StateNotifier<`, 185 `valueOrNull`, 361 `AsyncValue` or `.when(` |
| Observer | `shared_lib/core/lib/src/utils/datadog_log.dart` line 154 `DatadogLogObserver extends ProviderObserver` |
| Breaking changes | Riverpod 3.0 migration guide (list above) |

## Sources for the recommendations

* Riverpod, [Migrating from 2.0 to 3.0](https://riverpod.dev/docs/3.0_migration): automatic retry and the `retry` parameter, out-of-view pausing and `TickerMode`, `UnmountedRefException` and `ref.mounted`, `legacy.dart`, `==` filtering, `ProviderObserverContext`, removed `Ref` subclasses, `ProviderException`.
* Riverpod, [What's new in 3.0](https://riverpod.dev/docs/whats_new).
* Mobile plan 09: State management, section "Riverpod 3: upgrade first, then convert".
