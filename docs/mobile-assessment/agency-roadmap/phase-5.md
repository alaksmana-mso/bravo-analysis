## Summary

Phase 5 of the agency apps roadmap ("Move call sites, per app") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 8 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Move Call Sites".
* **Plan pages:** GENFI plan 11 steps 3 and 5, GENFI plan 10 step 2; SQUARE plan 04 steps 3 and 5, SQUARE plan 11 step 2; GENFI plan 03 step 4 (shim removal).
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 5 is.** Phase 2 put the analytics, flag and logging ports behind the old calls. Phase 5 drains the old calls, one feature per PR, then deletes the shims and the old models. Every PR is class B. It can run next to Phases 3 and 4.

### Three facts that shape Phase 5

**1. The analytics migration is small.** GENFI: 5 enum events, 4 call sites. SQUARE: 27 `logEvent` calls, 8 names built at run time, in features `lead`, `recruitment`, `maintain`, `performance` and others. Against the BFI app's 204 calls, this is a week of work, not a quarter.

**2. The flag migration is the bigger part.** GENFI: 20 `ConventFeatureFlag` keys + 10 Sharia keys read through the old models, plus a raw `getBool` in `main.dart`. SQUARE: 23 fields read through `RemoteConfig`. Keys stay the same, so the Remote Config console needs no change.

**3. Logging shims are cheap to remove.** `DatadogLog`, `Log` and `CrashReporter` became shims in Phase 2; the direct-call ratchet (2.5) counts what is left.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. All class **B** unless marked.

| # | Proposed ticket title | Today (24 Oct) | App | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5.1 | `refactor(analytics): Typed events for the 5 GENFI events, replace the 4 call sites` | Enum + 4 sites | GENFI | Agency engineer | S | 2.4 | | |
| 5.2 | `refactor(analytics): <feature>_events.dart and the 27 SQUARE call sites, one feature per PR` | 27 sites, 8 run-time names | SQUARE | Agency engineer | M | 2.4 | | |
| 5.3 | `refactor(flags): GENFI call sites to the catalogue (30 keys); delete the old models and the static instance` | Old models | GENFI, MyShaf | Agency engineer | M | 2.8 | | |
| 5.4 | `refactor(flags): SQUARE call sites to the catalogue (23 fields); delete remote_config_repository mapping` | Hand-mapped | SQUARE | Agency engineer | S | 2.8 | | |
| 5.5 | `chore: Delete the analytics and logging shims; strict ratchet` | Shims | shared + apps | Agency engineer | XS | 5.1–5.2 | | |
| 5.6 | `docs(analytics): Generated event catalogue, CODEOWNERS for product analytics` | None | shared | Agency engineer + product analytics | S | 5.5 | | |
| 5.7 | `ci(flags): Quarterly expired-flags report; docs/flags.md per app` | None | shared | Agency engineer | S | 2.7 | | |
| 5.8 | `feat(analytics): MyShaf events and MY BISPRO coverage` | MyShaf shares GENFI's wrapper | MyShaf, MY BISPRO | Agency engineer + product | S | 5.1 | | |

**Suggested order.** Week 1: 5.1, 5.7. Weeks 2–3: 5.2 (small features first, `lead` last), 5.4. Week 4: 5.3, 5.5, 5.6, 5.8.

## Definition of ready for every Phase 5 ticket

* The ticket names the feature and the exact count it will move (from the ratchet baseline).
* The golden names file diff must be empty; the ticket says so.
* The ratchet baseline file is lowered in the same PR.
* For 5.3 and 5.4: the catalogue entry exists (2.7) before the call site moves.

## Step 5.1: GENFI analytics call sites

**Today.** `ConventAnalyticsService` with 5 enum events and 4 call sites; the `proudct` key typo is an approved delta (GENFI Phase 3).

**Tasks.** Typed events with typed parameters for the 5 values. Replace the 4 call sites. Model screen views through the router observer (2.4).

**Acceptance criteria.** Golden names unchanged (except the Phase 3 delta). Baseline 0 for GENFI. Firebase DebugView on dev shows the same names.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Hand migration in one PR | 4 sites; trivial | None |
| B. Codemod | Overkill | – |
| C. Leave the enum wrapper as the port | No work | Two patterns across apps |

**Recommended: A.**

## Step 5.2: SQUARE analytics call sites

**Today.** 27 `logEvent` calls with string names, 8 built at run time, fired from `initState`; `setUserId` with the NIK (fixed in SQUARE Phase 3).

**Tasks.** `<feature>_events.dart` per feature. One feature per PR, small first: `performance`, `maintain`, `recruitment`, then `lead`. Run-time names become an event with an enum field that builds the same string.

**Acceptance criteria per PR.** Golden names unchanged. Baseline goes down by the feature's count. Widget tests use `FakeAnalytics`.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One feature per PR, small first | Reviewable; parity per PR | About 6 PRs |
| B. One PR for all 27 | Fast | Run-time names hide in the noise |
| C. Codemod | Script to write for 27 sites | Not worth it |

**Recommended: A.**

## Step 5.3: GENFI flag call sites

**Today.** `ConventFeatureFlag` (20 keys), the Sharia model (10 keys), a static Notifier instance, a raw `getBool` in `main.dart`.

**Tasks.** Replace reads with `ref.watch(flagProvider(...))`, one feature per PR. Replace the raw `getBool`. Delete the models, the static instance and the bridge from 2.8.

**Acceptance criteria.** `grep getBool( / getString(` outside the platform returns 0. Flavour-scoped flags resolve the same values for GENFI and MyShaf as today (test).

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One feature per PR, then delete the models | Same rhythm as analytics | Several PRs |
| B. Keep the models as views over the store | Familiar types stay | Two reads per key forever |
| C. Big-bang | One PR | 30 keys across many files in one review |

**Recommended: A.**

## Step 5.4: SQUARE flag call sites

**Today.** `RemoteConfig` with 23 fields, hand-mapped in a 140-line repository with no defaults.

**Tasks.** Replace reads with the catalogue; delete the hand-written mapping and the model. Declared defaults come from the catalogue.

**Acceptance criteria.** `remote_config_repository_test.dart` expectations hold through the new reads, then the file is deleted with the mapping. No `RemoteConfig` type left in `are_tracker/lib`.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One feature per PR, then delete | Clean | Several PRs |
| B. Keep the model | None | 140 lines of mapping stay |
| C. Big-bang | One PR | Larger review |

**Recommended: A.**

## Step 5.5: Delete the shims, strict ratchet

**Tasks.** When the analytics and logging baselines reach 0 per app: delete `Analytics.logEvent`, `ConventAnalyticsService`, `DatadogLog`, `Log`, `CrashReporter` shims. Make the CI rules strict.

**Acceptance criteria.** Baselines 0; any direct SDK call fails CI.

**Who / size.** One Agency engineer. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete when 0 | Clean | Waits for the last feature |
| B. Delete early, break callers | Forces the pace | Breaks `master` |
| C. Keep | None | Ratchet never reaches 0 |

**Recommended: A.**

## Step 5.6: Event catalogue and `CODEOWNERS`

**Tasks.** A script turns the event classes of all apps into `docs/analytics/event-catalogue.md` (name, app, sinks, parameters, owner). CI regenerates it. `CODEOWNERS`: product analytics reviews `*_events.dart`.

**Acceptance criteria.** Catalogue generated in CI; a PR that adds an event asks product analytics.

**Who / size.** One Agency engineer + product analytics. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Markdown in the repo, generated, code-owned | Changes with the code | Product reads GitHub |
| B. Export to Confluence per release | Product-friendly | One more sync job |
| C. Both | Everyone happy | Two artefacts |

**Recommended: A.**

## Step 5.7: Expired-flags report

**Tasks.** A unit test fails when a release flag is past its `removeBy` date (2-week grace); a quarterly report lists flags past their date; `docs/flags.md` per app generated from the catalogue.

**Acceptance criteria.** An overdue flag fails CI; the report runs and lists 0 expired flags.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Test + report + generated doc | Enforced, visible | Owners must set dates |
| B. Warning only | Never blocks | Flags pile up |
| C. A flag vendor | Built in | Not needed for 53 flags |

**Recommended: A.**

## Step 5.8: MyShaf and MY BISPRO events

**Today.** MyShaf uses GENFI's wrapper (same folder); MY BISPRO has no analytics wrapper.

**Tasks.** Decide which events MyShaf shares with GENFI (flavour-scoped). Wire the port in MY BISPRO with its own small catalogue.

**Acceptance criteria.** Datadog RUM shows sessions and actions for a MyShaf SIT build. MY BISPRO sends through the port only.

**Who / size.** One Agency engineer + product. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flavour-scoped events in one catalogue for GENFI and MyShaf; a small MY BISPRO catalogue | One pattern | Product must decide the MyShaf set |
| B. Separate catalogues per flavour | Clear | Duplicated events |
| C. Skip MY BISPRO | Less work | One app outside the port |

**Recommended: A.**

## Exit gate for Phase 5

* Direct-call ratchets for analytics, flags and logging at 0 in every app; shims and old flag models deleted.
* Event catalogue and `docs/flags.md` generated in CI; both code-owned.
* Golden names files unchanged through the phase, except the Phase 3 approved deltas.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who owns each GENFI and SQUARE Remote Config flag, and which are fully on in prod? | Product + Agency squad | |
| Q2 | Does product analytics agree to be code owner of `*_events.dart` for the agency apps? | Product analytics lead | |
| Q3 | Which events does MyShaf share with GENFI? | Product (Sharia) | |
| Q4 | Epic: one with sub-tickets per app? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Call-site counts | `grep -c "logEvent("`: SQUARE 27, GENFI 6 (4 call sites + wrapper) |
| Flag models | plan 10 and 11 "today" sections |
| Run-time names | SQUARE plan 04 step 1 (8) |

## Sources for the recommendations

* BFI Phase 5 refinement notes.
* GENFI plan 11 and SQUARE plan 04 (analytics), GENFI plan 10 and SQUARE plan 11 (flags).
