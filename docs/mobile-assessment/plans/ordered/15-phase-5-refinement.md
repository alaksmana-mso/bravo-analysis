## Summary

This page prepares Phase 5 of the mobile roadmap ("Move call sites, feature by feature") for refinement. It covers all 8 steps: what is true today, what to do, acceptance criteria, who is needed, size, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Move Call Sites".
* **Parent:** Mobile roadmap: step by step, section "Phase 5: Move call sites, feature by feature". Plan pages: Mobile plan 02: Analytics wrapper, Mobile plan 12: Feature flags, Mobile plan 05: Logging and crashes.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct).

**What Phase 5 is.** Phase 2 put the new analytics, flag and monitoring ports *behind* the old calls. Phase 5 drains the old calls, one feature per PR, then deletes the shims. Every PR is class B: the golden names file, flag defaults and log destinations do not change. This phase can run next to Phases 3 and 4, because its PRs change no behaviour.

### Three facts that shape Phase 5

**1. The work is concentrated in two features.** Firebase `logEvent` calls per feature today: `loan` 71, `auth` 56, `ro` 13, `home` 12, `support` 11, `account` 10, `onboarding` 7, `payment` 4, `select_vehicle` 3, and 2 or fewer in `promo`, `pin`, `notification`, `domicile_address`, `payment_method`. Remote Config reads per feature: `loan` 29, `auth` 18, `home` 8, `pin` 5, `dev_mode` 3, and 2 or fewer in `ro`, `rl`, `bpkb_release`, `bank`, `domicile_address`, `account`. So `loan` and `auth` are about 60% of the work. Start small to prove the pattern, as plan 02 says, then do the two big ones.

**2. There are three Mixpanel experiments, not two.** `experiment_repository.dart` defines `bfi-mobile-home-page-force-register-exp`, `bfi-mobile-home-revamp-exp` and `bfi-mobile-kyc-revamp-exp`. Plan 12 counted two. Each one must keep its `experiment-exposure` event.

**3. The dead flags are referenced 6 times, in the model and mapping only.** `featureFlagSurveyor` and `featureFlagLov` appear in `remote_config.dart` and its repository, never in a feature. Removing them is safe once the catalogue test (2.11) agrees.

Also: 19 log call sites with raw error text were fixed in Phase 3 (3.2). What remains for 5.x is moving the 61 `DatadogLog` static calls to the port when a file is touched, not a separate migration (the static facade stays until Phase 8).

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. All class **B** unless marked.

| # | Proposed ticket title | Today (23 Oct) | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1 | `refactor(analytics): Move Firebase calls to the port`, one sub-ticket per feature (14) | 196 calls in features, 8 in `app/` | Mobile engineers (2 in parallel) | M per big feature, XS–S per small one | 2.2, 2.3, 1.11 | | |
| 5.2 | `refactor(flags): Move Remote Config reads to flagProvider`, one sub-ticket per feature (11) | 86 references outside the flag folder | Mobile engineer | S per feature | 2.13 | | |
| 5.3 | `refactor(flags): Three Mixpanel experiments into the catalogue` | 3 keys in `experiment_repository.dart` | Mobile engineer | S | 2.10 | | |
| 5.4 | `chore(analytics): Delete the shims, strict CI count` | Shims exist after 2.2 | Mobile engineer | XS | 5.1 done | | |
| 5.5 | `chore(flags): Delete RemoteConfig and its generated code` | 2,486 + 376 generated lines | Mobile engineer | S | 5.2, 5.3 | | |
| 5.6 | `docs(analytics): Generated event catalogue + CODEOWNERS` | None | Mobile engineer + product analytics | S | 5.4 | | |
| 5.7 | `ci(flags): Flag lifecycle check and docs/flags.md` | None | Mobile engineer | S | 2.12 | | |
| 5.8 | `chore(flags): Remove dead and fully-on flags`, one PR per flag | 2 dead flags; others unknown | Mobile engineer + flag owners | XS per flag | 5.5, Q2 | | |

**Suggested order.** Week 1: 5.1 for `payment_method`, `promo`, `pin`, `notification`, `domicile_address` (prove the pattern, 1 PR each), 5.7. Weeks 2–3: 5.1 `account`, `support`, `onboarding`, `payment`, `select_vehicle`, `home`, `ro`; 5.2 small features; 5.3. Weeks 4–6: 5.1 `auth` then `loan`; 5.2 `auth` then `loan`. Then 5.4, 5.5, 5.6, 5.8.

## Definition of ready for every Phase 5 ticket

* The ticket names the feature and the exact count it will move (from the ratchet baseline).
* The golden names file (1.11) diff must be empty; the ticket says so.
* The ratchet baseline file is lowered in the same PR.
* For 5.2: the catalogue entry exists (2.11) before the call site moves.

## Step 5.1: Move Firebase calls to the port, one feature per PR

**Today.** 204 `logEvent(` calls in 87 files (196 in features, 8 in `app/`). 148 names as strings, 8 built at run time (plan 02). `Analytics.logEvent` is a shim since 2.2.

**Tasks.** Per feature: add `<feature>_events.dart` to the catalogue, replace each call with a typed event, model the run-time names as an event with an enum field that builds the same string. Order: small features first, then `home`, `ro`, `auth`, `loan`.

**Acceptance criteria per PR.** Golden names file unchanged. Firebase DebugView on the dev flavor shows the same names for the feature's main screens. Ratchet baseline goes down by the feature's count. Widget tests use `FakeAnalytics`.

**Who / size.** Two engineers can work in parallel on different features. M for `loan` and `auth`, S for `home`, `ro`, `support`, `account`, XS for the rest.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Hand migration, one feature per PR, small first | Reviewable. Each PR proves parity on its own | About 20 PRs |
| B. A codemod script that rewrites all 204 calls, one PR | Fast | One 87-file PR; run-time names need hand work anyway; a bad rewrite hides in the noise |
| C. Codemod per feature, hand-check the result, one PR per feature | Fast and reviewable | Script to write; worth it only if the call shapes are regular (check on `pin` first) |

**Recommended: A for the first 5 features, then decide on C** once the shapes are known.

## Step 5.2: Move Remote Config reads to `flagProvider`

**Today.** 86 references to `getRemoteConfigUseCase` or `RemoteConfig` outside the flag folder. The bridge (2.13) keeps them working.

**Tasks.** Per feature: replace `getRemoteConfigUseCase.select(...)` with `ref.watch(flagProvider(<Feature>Flags.<key>))`. Order: `pin`, `bank`, `bpkb_release`, `rl`, `ro`, `account`, `domicile_address`, `dev_mode`, `home`, `auth`, `loan`.

**Acceptance criteria per PR.** The widget tests that read a flag pass through the new read with the same result (both-paths helper where a switch flag is involved). Ratchet count of `getRemoteConfigUseCase` goes down.

**Who / size.** One mobile engineer. S per feature.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One feature per PR, catalogue entry first | Same rhythm as 5.1 | 11 PRs |
| B. Keep the bridge forever, only new code uses flags | No migration | `RemoteConfig` (2,800 generated lines) never dies |
| C. Big-bang replace | One PR | 86 sites across 11 features in one review |

**Recommended: A.**

## Step 5.3: Three Mixpanel experiments into the catalogue

**Today.** Three experiment keys in `experiment_repository.dart`, read through `mixpanel_feature_flag_service.dart`. Two `appRef` reads in `go_router_extension.dart` touch them (plan 12).

**Tasks.** Define each as `BoolFlag(source: FlagSource.mixpanel)` in the catalogue. Remove the private keys from the repository. Replace the `appRef` reads with a passed-in ref (coordinate with Phase 7 step 7.5).

**Acceptance criteria.** One `experiment-exposure` event per key per session in Mixpanel, same as today (golden names file covers the event name; a SIT session check covers the count).

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Mixpanel source behind the flag port | One flag API for product | Exposure events must be fired by the source, not forgotten |
| B. Leave experiments on their own path | No work | Two flag systems forever |
| C. Move experiments to Firebase A/B Testing | One vendor | Product uses Mixpanel funnels; a vendor change is a product decision, not Phase 5 |

**Recommended: A.**

## Step 5.4: Delete the analytics shims

**Today.** `Analytics.logEvent`, `MixpanelService.track`, `analytics.dart` are shims since 2.2.

**Tasks.** When the ratchet reaches 0: delete the shims and `analytics.dart`. Make the CI rule strict (any direct SDK call fails).

**Acceptance criteria.** Baseline 0. `grep` for `FirebaseAnalytics.instance.logEvent` outside the adapters returns 0.

**Who / size.** One mobile engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete when baseline is 0 | Clean | Waits for the last feature |
| B. Delete early, break the last callers on purpose | Forces the pace | Breaks `master` for whoever is mid-migration |
| C. Keep the shims as "convenience" | None | The ratchet never reaches 0 |

**Recommended: A.**

## Step 5.5: Delete `RemoteConfig` and its generated code

**Today.** `remote_config.dart` (177 lines), `.freezed.dart` (2,486), `.g.dart` (376), repository (245), converters.

**Tasks.** When `getRemoteConfigUseCase` references reach 0: delete the model, the generated files, the hand-written mapping, and the bridge from 2.13.

**Acceptance criteria.** No `RemoteConfig` type in `digital/lib`. `melos generate` produces no new files for it. App builds for all 4 flavors.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete in one PR when references are 0 | Clean | One larger diff (mostly generated code) |
| B. Keep the model as a read-only view over the store | Familiar type stays | 2,800 generated lines stay for no reason |
| C. Delete field by field | Many small PRs | Generated files change every time |

**Recommended: A.**

## Step 5.6: Generated event catalogue and `CODEOWNERS`

**Today.** No catalogue. Product analytics has no place to review events.

**Tasks.** A script turns the event classes into `docs/analytics/event-catalogue.md` (name, sinks, parameters, owning feature, owner). CI regenerates it and fails if it is stale. `CODEOWNERS`: product analytics reviews PRs that touch `*_events.dart`.

**Acceptance criteria.** Catalogue generated in CI. A PR that adds an event asks product analytics for review.

**Who / size.** One mobile engineer + product analytics. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Markdown in the repo, generated, code-owned | Changes with the code | Product reads GitHub |
| B. Export to a sheet or Confluence page on each release | Product-friendly | One more sync job |
| C. Both | Everyone happy | Two artefacts |

**Recommended: A**, and B only if product asks.

## Step 5.7: Flag lifecycle check and `docs/flags.md`

**Today.** `SwitchFlag` has a removal-date test since 2.12. Release flags have no owner or date.

**Tasks.** A unit test fails when any release flag is past its `removeBy` date (2-week grace), printing owner and key. Generate `docs/flags.md` from the catalogue.

**Acceptance criteria.** An overdue release flag fails CI. `docs/flags.md` lists every flag with owner and date.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Unit test + generated doc | Enforced, visible | Owners must set dates (Q2) |
| B. Warning only | Never blocks | Flags pile up again |
| C. A flag-management vendor with lifecycle features | Built in | New vendor; not needed for 44–91 flags |

**Recommended: A.**

## Step 5.8: Remove dead and fully-on flags

**Today.** `featureFlagSurveyor` and `featureFlagLov` are never read in a feature. The rest: unknown until owners answer.

**Tasks.** One PR per flag: delete the flag and the dead branch. The owner confirms in the ticket that the value is fully on in prod. Delete the console key one release later.

**Acceptance criteria.** Owner confirmation in each ticket. Flag count in `docs/flags.md` goes down. No behaviour change (the dead branch was never taken).

**Who / size.** One mobile engineer + flag owners. XS per flag.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One PR per flag, owner confirms | Safe, traceable | Slow if owners are slow |
| B. Remove all "fully on" flags in one PR | Fast | One wrong assumption removes a live branch |
| C. Leave them | No work | 91 fields stay forever |

**Recommended: A.**

## Exit gate for Phase 5

* Direct-call ratchets for analytics, flags and monitoring at 0.
* Shims and `RemoteConfig` deleted.
* Event catalogue and `docs/flags.md` generated in CI; both code-owned.
* Golden names file unchanged through the whole phase, except the Phase 3 approved deltas.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Can two engineers work Phase 5 in parallel with Phases 3 and 4? | Squad lead | |
| Q2 | Who owns each Remote Config flag, and which are fully on in prod? | Product + mobile squad | |
| Q3 | Does product analytics agree to be code owner of `*_events.dart`? | Product analytics lead | |
| Q4 | Are the 3 Mixpanel experiments still running, or can any be closed first? | Product | |
| Q5 | Epic for Phase 5: one epic with sub-tickets per feature? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Calls per feature | `grep -rn "logEvent("` per `digital/lib/features/<f>`, generated files excluded |
| Flag reads per feature | `grep -rn "getRemoteConfigUseCase\|RemoteConfig\b"` per feature |
| Experiments | `digital/lib/app/experiment/experiment_repository.dart` lines 6–8 |
| Dead flags | 6 references, all in `digital/lib/app/remote_config/` |
| Generated sizes | `wc -l` on `remote_config.freezed.dart`, `remote_config.g.dart` |

## Sources for the recommendations

* Mobile plan 02: Analytics wrapper, steps 8–10. Mobile plan 12: Feature flags, steps 5–9.
* Firebase, [Remote Config loading strategies](https://firebase.google.com/docs/remote-config/loading): defaults and activation.
