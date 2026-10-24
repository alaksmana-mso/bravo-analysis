## Summary

Phase 3 of the SQUARE roadmap ("Approved deltas, one per release"). Child of SQUARE roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, who signs off, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] SQUARE Improvement - Approved Deltas".
* **Plan pages:** SQUARE plan 03 step 3; SQUARE plan 01 steps 4–6; SQUARE plan 04 steps 4–5; SQUARE plan 11 step 3.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 3 is.** Every step changes what staff or third parties see or receive, on purpose, signed off first, shipped alone, watched, with a way back. SQUARE's users are BFI staff on managed devices, so the rollout can be shorter than GENFI's, but the privacy deltas are the same, and one is worse: the employee's national ID number is the Firebase user id.

### Four facts that shape SQUARE Phase 3

**1. The NIK is the analytics user id.** `are_tracker/lib/app/analytics/analytics.dart` line 16: `setUserId(id: profile.agentConfins.nikMarketing)`, plus user properties. Google's Analytics terms do not allow data that identifies a person. Changing the id changes user-level reports, so the dashboard owner must agree.

**2. Consent is a constant.** `DatadogSdk.runApp(_ddSdkConfig, TrackingConsent.granted, ...)` in `are_tracker/lib/main.dart` line 43.

**3. RUM is not processed for SQUARE.** The two SQUARE RUM applications have `rum_event_processing_state: NONE`, so the SDK sends events Datadog drops. Turning processing on costs money (Phase 1 question 4); adding RUM actions (visit report, lead, company submission submitted) is new data and needs sign-off.

**4. One compile-time flag drives a feature.** `FEATURE_FLAG_NON_REGISTERED_MAINTAIN` is a dart-define; `FEATURE_FLAG_NEW_COLLAB_FORM` and `FEATURE_FLAG_NEW_LOAN_CALCULATOR` exist in CI. The jailbreak check is the local `flutter_jailbreak_detection` package behind `FEATURE_JAILBREAK_DETECTION`.

Also: nothing blocks screenshots on OTP, registration, personal and tax information, lead input and detail; `api` secrets and the Keycloak client secret reach the binary through defines (the client secret was also exposed in `debugger.yaml`, rotated in Phase 0).

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. Class **D** = approved delta, **E** = backend-coupled.

| # | Proposed ticket title | Today (24 Oct) | Class | Signs off | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1 | `feat(observability): Sanitiser on every sink; opaque agent id instead of the NIK in Crashlytics and Firebase` | NIK as user id | D | DPO + dashboard owner | Agency engineer | M | 2.1–2.4 | | |
| 3.2 | `feat: ConsentState provider for Datadog and the adapters; PII key denylist` | Consent constant | D | DPO | Agency engineer | S | 2.3–2.4 | | |
| 3.3 | `feat(security): Screen-capture guard on sensitive routes, behind a kill switch` | None | D | Product | Agency engineer | M | 2.7 | | |
| 3.4 | `fix(flags): FEATURE_FLAG_NON_REGISTERED_MAINTAIN to Remote Config; delete the two FEATURE_FLAG_NEW_* defines; jailbreak default on` | Compile-time | D | Squad lead | Agency engineer | S | 2.7 | | |
| 3.5 | Secrets out of the app: review the prod defines; backend relies on none; integrity verdicts enforced for SQUARE | Defines public | E | Security + backend owner | Backend + Agency engineer | M | Q3 | | |
| 3.6 | `feat(analytics): RUM actions for visit report, lead and company submission submitted` (after RUM processing is on) | RUM dropped | D | Product + Datadog owner | Agency engineer | S | Phase 1 Q4 | | |

**Suggested order (one D per SQUARE release).** Release 1: 3.4. Release 2: 3.1 (the NIK change needs the dashboard owner ready). Release 3: 3.2. Release 4: 3.3. Release 5: 3.6 if RUM is on. In parallel: 3.5 monitor-only.

## Definition of ready for every ticket

* Sign-off recorded in the ticket and in an "Approved deltas" table on the Square mobile app assessment page.
* The ticket names its release and confirms no other class C or D change ships in it.
* The rollback is written.
* For 3.1 and 3.2: the golden names file diff is attached; for 3.1 the dashboard owner has a plan for user-level reports.

## Step 3.1: Sanitiser and the opaque agent id

**Today.** See fact 1.

**Tasks.** Sanitiser rules as on the GENFI page (shared package). Replace the NIK user id with `bravoAgentId` or a keyed hash, in Firebase (`setUserId`), Crashlytics and Datadog. Review the user properties (`product_id` is fine; anything that identifies a person goes). Agree the cut-over date with the dashboard owner, because user-level reports change.

**Acceptance criteria.** A test crash and a test event on SIT carry the opaque id and no NIK. Weekly PII query at zero for 2 weeks. The dashboard owner confirms user counts are consistent after the cut-over.

**Who / size.** One Agency engineer. DPO + dashboard owner sign off. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `bravoAgentId` as the id everywhere | One internal id, already used by GENFI's crash reports | User-level reports break at the cut-over |
| B. A keyed hash of the NIK | Stable across systems | A hash of an identifier is still personal data in most readings; needs the key managed |
| C. Keep the NIK | No work | Against Google's terms and BFI's own policy |

**Recommended: A.**

## Step 3.2: Consent and the PII denylist

Same as GENFI Phase 3 step 3.2: `ConsentState` provider (default granted) for `DatadogSdk.runApp`, the sinks and adapters; a whole-word denylist in the fan-out.

**Acceptance criteria.** Denied key dropped in a unit test; golden names unchanged; consent value reaches Datadog from the provider.

**Who / size.** One Agency engineer. DPO. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Provider + denylist, default granted | Closes the class; no visible change | Consent UX is a product decision |
| B. Call-site fixes only | Small | The next parameter sails through |
| C. Full consent flow now | Complete | Later delta |

**Recommended: A.**

## Step 3.3: Screen-capture guard

**Tasks.** Same implementation as GENFI (shared method channel). Routes: OTP, registration (KTP OCR, selfie), personal and tax information, lead input and detail. Kill switch.

**Acceptance criteria.** e2e passes; screenshots blank on test devices; kill switch works within a journey start.

**Who / size.** One Agency engineer. Product signs off. M (S if GENFI's lands first).

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Shared method channel, per route, kill switch | One implementation for three apps | UIKit dependency on iOS |
| B. A pub.dev plugin | Ready-made | Small maintainers |
| C. Android only | Solid API | iOS screens stay capturable |

**Recommended: A.**

## Step 3.4: Compile-time flags

**Today.** See fact 4.

**Tasks.** `FEATURE_FLAG_NON_REGISTERED_MAINTAIN` becomes a Remote Config flag in the catalogue with today's value as default. Delete `FEATURE_FLAG_NEW_COLLAB_FORM` and `FEATURE_FLAG_NEW_LOAN_CALCULATOR` from CI (confirm they are fully on, question 2). Jailbreak detection default on with a kill switch.

**Acceptance criteria.** Prod values unchanged on day one. No `--dart-define` starts with `FEATURE_`. Rooted SIT device shows the block.

**Who / size.** One Agency engineer. Squad lead signs off. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Remote Config for the live flag, delete the dead ones, defaults in code | Fail-safe, one flag system | A failed fetch must land on today's value: set the default accordingly |
| B. Defaults only | Smallest | Dead defines stay |
| C. Keep | No work | A missing variable changes behaviour silently |

**Recommended: A.**

## Step 3.5: Secrets out of the app, integrity for SQUARE

**Tasks.** Review the SQUARE prod defines; document that they are public. Backend: sensitive endpoints check the user token (Keycloak) and the integrity verdict; monitor-only 2 weeks, then enforce. SQUARE's managed devices allow a forced update, so the minimum version can move faster than GENFI's.

**Acceptance criteria.** 0 would-be blocks from current versions for 2 weeks; enforcement on; a pentest cannot call a sensitive endpoint with a define alone.

**Who / size.** Backend owner + security + one Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Monitor-only, then enforce, with a forced update | Safe and faster than GENFI | MDM policy must exist (question 3) |
| B. Enforce at once | Fast | Blocks staff on old versions |
| C. Keep | No change | Defines are not a control |

**Recommended: A.**

## Step 3.6: RUM actions

**Today.** See fact 3.

**Tasks.** Once RUM processing is on: add RUM actions for visit report submitted, lead submitted, company submission submitted, through the analytics port's Datadog adapter. DPO signs the parameters.

**Acceptance criteria.** Actions visible in Datadog RUM for a SIT build; golden names file shows only added sinks.

**Who / size.** One Agency engineer. Product + Datadog owner sign off. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Three milestone actions through the adapter | Cheap with the port; funnels in Datadog | Needs RUM processing paid for |
| B. Mirror every event to RUM | Simple rule | Cost per event |
| C. No RUM for SQUARE | No cost | Crashlytics-only visibility |

**Recommended: A if Phase 1 Q4 says yes; otherwise C with Crashlytics as the floor.**

## Exit gate

* Every delta at 100% for 1 SQUARE release with no regression; each in the "Approved deltas" table with its sign-off.
* No NIK in any sink; weekly PII query at zero for 2 weeks.
* 3.5 at least in monitor-only with the 2-week log reviewed.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who owns the SQUARE Firebase dashboards, and when can the user id change? | Product analytics | |
| Q2 | Are `FEATURE_FLAG_NEW_COLLAB_FORM` and `FEATURE_FLAG_NEW_LOAN_CALCULATOR` fully on in prod? | Agency squad | |
| Q3 | Can SQUARE force a minimum version through MDM, and who decides? | IT + squad lead | |
| Q4 | Will RUM processing be turned on for SQUARE? | Datadog owner | |
| Q5 | Who is the DPO contact? | Engineering manager | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| NIK as user id | `are_tracker/lib/app/analytics/analytics.dart` lines 16–21 |
| Consent | `are_tracker/lib/main.dart` line 43 |
| RUM processing | Datadog RUM application list |
| Compile-time flags | SQUARE plan 11 step 3; `grep bool.fromEnvironment` |

## Sources for the recommendations

* BFI Phase 3 refinement notes; GENFI phase 3 page (shared implementation).
* Google, [Analytics Terms of Service](https://www.google.com/analytics/terms/).
* Android, [Play Integrity verdicts](https://developer.android.com/google/play/integrity/verdict).
