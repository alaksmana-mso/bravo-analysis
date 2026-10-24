## Summary

Phase 3 of the GENFI roadmap ("Approved deltas, one per release"). Child of GENFI roadmap: step by step. It covers the 6 steps: what is true today, what to do, acceptance criteria, who signs off, owner and size, 3 options with a recommendation, questions. MyShaf is the same binary (Sharia flavour), so every delta ships to both.

* **Epic:** not created yet. Suggested: "[Tech x DK] GENFI Improvement - Approved Deltas".
* **Plan pages:** GENFI plan 03 step 3; GENFI plan 01 steps 4–6; GENFI plan 11 steps 3–4; GENFI plan 10 step 3.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 3 is.** Every step here changes what agents or third parties see or receive, on purpose. Each is signed off before it ships, goes out alone in its GENFI release, is watched on the release health dashboard, and has a way back. The rules are the same as BFI Phase 3: one delta per release, sign-off before code, monitor-only first for anything the backend enforces.

### Four facts that shape GENFI Phase 3

**1. Personal data in crash keys.** The Crashlytics user id is `bravoAgentId` (good), but the custom keys include `nik_marketing`, the agent's national ID number, next to `marketing_id`, `marketing_spv_id`, `product_ids`, `is_admin_agent_session`, `app_flavor`. Remote-config values are printed to the console on web.

**2. Consent is a constant.** `DatadogSdk.runApp(_ddSdkConfig, TrackingConsent.granted, ...)` in `agent_tools/lib/main.dart` line 49 (and the same in SQUARE and MY BISPRO).

**3. Twenty-one dart-defines go into the prod binary.** `agent_tools_prod_release.yaml` passes 21 values per platform. Anything in a dart-define is public once the app is installed. `DEVICE_INTEGRITY_URL` is passed to SIT, UAT and MyShaf but **not to GENFI prod**, so the Play Integrity and App Attest check runs for MyShaf only. `shared_data/integrity` has 0 tests.

**4. Compile-time feature flags.** `FEATURE_JAILBREAK_DETECTION` and `FEATURE_ENABLE_PROXY` are `bool.fromEnvironment` values, so a missing CI variable silently turns the jailbreak check off or the proxy on. `FEATURE_FLAG_NEW_*` defines exist in CI. Six `bool.fromEnvironment` reads across the apps.

Also: the `proudct` event key typo in the GENFI analytics wrapper (dashboards query the misspelt key today); nothing blocks screenshots on OTP, registration (KTP OCR, selfie), personal and tax information, prospect input and detail.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. Class **D** = approved delta, **E** = backend-coupled.

| # | Proposed ticket title | Today (24 Oct) | Class | Signs off | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1 | `feat(observability): Sanitiser on every sink; drop nik_marketing from the crash keys; no remote-config print on web` | NIK in crash keys | D | DPO | Agency engineer | M | Phase 2 step 2.1–2.2 | | |
| 3.2 | `feat: ConsentState provider for Datadog and the adapters; PII key denylist` | Consent constant | D | DPO | Agency engineer | S | 2.3–2.4 | | |
| 3.3 | `fix(analytics): proudct → product` | Misspelt key | D | Dashboard owner | Agency engineer | XS | 1.G2 | | |
| 3.4 | `feat(security): Screen-capture guard on sensitive routes, behind a kill switch` | None | D | Product | Agency engineer | M | 2.7 (flag kind) | | |
| 3.5 | `fix(flags): Jailbreak detection default on, proxy default off; delete FEATURE_FLAG_NEW_* from CI` | Defaults off | D | Squad lead | Agency engineer | XS | – | | |
| 3.6 | Secrets out of the app: review the 21 prod defines; backend relies on none; `DEVICE_INTEGRITY_URL` and the integrity check for GENFI prod | Integrity check MyShaf only | E | Security + backend owner | Backend + Agency engineer | M | Q4 | | |

**Suggested order (one D per GENFI release).** Release 1: 3.5. Release 2: 3.1. Release 3: 3.2 + 3.3 (one sign-off: "analytics and crash data cleaned"). Release 4: 3.4 behind its kill switch. In parallel, monitor-only: 3.6. About 8–10 weeks at one GENFI release every 2 weeks (confirm the GENFI cadence, question 1).

## Definition of ready for every ticket

* The sign-off is recorded in the ticket (who, date), and the row is added to an "Approved deltas" table on the Genfi mobile app assessment page.
* The ticket names its release and confirms no other class C or D change ships in it.
* The rollback is written: kill switch, remote value, or halt and hotfix.
* For 3.1–3.3: the golden names file diff is attached and reviewed.

## Step 3.1: Sanitiser and the crash keys

**Today.** See fact 1. The observability package and sinks exist after Phase 2; the sanitiser type is a placeholder.

**Tasks.** Sanitiser rules: denied keys dropped (`nik`, `nik_marketing`, `phone`, `email`, `address`, `name`, `income`), NIK, phone and email patterns masked in messages and stack frames. Drop `nik_marketing` from the Crashlytics keys. Remove the remote-config print on web. Register the sanitiser as the Datadog log `eventMapper` as a second net.

**Acceptance criteria.** Sanitiser 100% unit-tested. A test crash on SIT shows `bravoAgentId` and no NIK. A weekly Datadog query for NIK and phone patterns in GENFI logs returns zero for 2 weeks.

**Who / size.** One Agency engineer. DPO signs off. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Sanitiser in the port plus the Datadog mapper; drop the key | One rule set for both sinks; catches logs that bypass the port | Regexes to maintain |
| B. Drop `nik_marketing` only | Smallest | The next `$error` with a response body goes through |
| C. Server-side scrubbing only | No app code | Data has left the device; Crashlytics not covered |

**Recommended: A.**

## Step 3.2: Consent and the PII denylist

**Today.** See fact 2. No consent UI exists; the default stays granted so nothing visible changes yet.

**Tasks.** `ConsentState` provider (default granted) feeds `DatadogSdk.runApp` and the sinks and adapters. Denylist in the analytics fan-out, matched on whole words. Debug asserts; release drops the key and logs through the sanitised path.

**Acceptance criteria.** A unit test sends a denied key and sees it dropped. Golden names unchanged. Datadog receives the consent value from the provider.

**Who / size.** One Agency engineer. DPO signs off. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Provider + denylist, default granted | Closes the leak class; no visible change until a consent UI exists | Consent UX is a product decision (question 2) |
| B. Remove known bad parameters at call sites | Small | The next one sails through |
| C. Full consent flow now | Complete | Product and legal work for a later delta |

**Recommended: A.**

## Step 3.3: `proudct` → `product`

**Today.** The wrapper sends the misspelt key; dashboards query it.

**Tasks.** Rename the key. The dashboard owner updates the report in the same week. Record it as an approved delta in the golden names file.

**Acceptance criteria.** Firebase DebugView shows `product`; the dashboard shows the same numbers the week after.

**Who / size.** One Agency engineer + dashboard owner. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Rename, update the dashboard | Clean | A one-week discontinuity in the report |
| B. Send both keys for a quarter | No discontinuity | Double parameters |
| C. Leave | No work | A typo in the catalogue forever |

**Recommended: A.**

## Step 3.4: Screen-capture guard

**Today.** Nothing in the app. The common approach: `FLAG_SECURE` on Android per route; a secure-layer trick on iOS that relies on UIKit internals (BFI Phase 3 step 3.8 lists the caveats).

**Tasks.** `lib/app/security/screen_capture/`: a `go_router` observer, a list of protected route names, a method channel. Routes: OTP, registration (KTP OCR, selfie), personal information, tax information, prospect input and detail. Behind a Remote Config kill switch.

**Acceptance criteria.** e2e journeys pass (QA accepts black screenshots on protected screens). Screenshots blank on Android and iOS test devices. Kill switch off restores screenshots at the next journey start.

**Who / size.** One Agency engineer. Product signs off. M. Share the method-channel code with the BFI app if it lands first.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own method channel, per route, kill switch | We control the iOS trick; one implementation for three apps | We own the workaround when UIKit changes |
| B. A pub.dev plugin | Ready-made | Small maintainers; same UIKit dependency |
| C. Android only | Solid API | iOS KYC screens stay capturable |

**Recommended: A**, reusing the BFI app's implementation.

## Step 3.5: Compile-time flags become code defaults

**Today.** See fact 4.

**Tasks.** `FEATURE_JAILBREAK_DETECTION` → default on in code, with a Remote Config kill switch; `FEATURE_ENABLE_PROXY` → default off, dev flavours only. Delete `FEATURE_FLAG_NEW_*` from CI. CI asserts no `--dart-define` starts with `FEATURE_`.

**Acceptance criteria.** Prod values unchanged (jailbreak check already on in prod, confirm question 3). A SIT build on a rooted device shows the block. CI fails on a `FEATURE_` define.

**Who / size.** One Agency engineer. Squad lead signs off. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Defaults in code + kill switch + CI assert | Fail-safe | A rooted tester's device is blocked in SIT unless the switch is off |
| B. Defaults only | Smallest | A stray define still works |
| C. Keep compile-time flags | No work | A missing variable silently disables security |

**Recommended: A.**

## Step 3.6: Secrets out of the app, integrity check for GENFI

**Today.** See fact 3. Google's guidance: verify integrity tokens on the server, bind them to the request, check timestamps and nonces.

**Tasks.** Review the 21 defines: which are secrets the backend relies on? Document that any define is public. With the backend owners: sensitive endpoints check the user token and the integrity verdict; **monitor-only for 2 weeks**, then enforce for app versions at or above the minimum. Pass `DEVICE_INTEGRITY_URL` to GENFI prod. Tests for `shared_data/integrity`.

**Acceptance criteria.** Backend logs show 0 would-be blocks from current GENFI versions for 2 weeks. Enforcement on for new versions. `integrity` has tests. A pentest cannot call a sensitive endpoint with a define value alone.

**Who / size.** Backend owner + security + one Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Monitor-only, then enforce per app version | Safe for agents on old versions | Weeks of calendar time |
| B. Enforce at once | Fast | Blocks agents on old versions and on devices where Play Integrity fails |
| C. Keep relying on defines | No backend change | A value anyone can extract is not a control |

**Recommended: A.**

## Exit gate

* Every delta at 100% for 1 GENFI release with no regression; each in the "Approved deltas" table with its sign-off.
* Weekly PII query on GENFI logs at zero for 2 weeks.
* 3.6 at least in monitor-only with the 2-week log reviewed.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | What is the GENFI prod release cadence? | Release manager | |
| Q2 | Does BFI want a consent screen for agents? | Product + legal | |
| Q3 | Is the jailbreak check on in GENFI prod today (CI variable value)? | Agency squad | |
| Q4 | Which backend owns the agent endpoints, and what is the minimum supported GENFI version? | Backend lead + product | |
| Q5 | Who is the DPO contact for the agency apps? | Engineering manager | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Crash keys | GENFI plan 03 "today" |
| Consent | `agent_tools/lib/main.dart` line 49 |
| Dart-defines and integrity URL | GENFI plan 02 "today"; plan 01 step 4 |
| Compile-time flags | `grep -c bool.fromEnvironment` = 6; plan 10 step 3 |

## Sources for the recommendations

* BFI Phase 3 refinement notes (sanitiser, consent, screen capture, Play Integrity).
* Android, [Play Integrity verdicts](https://developer.android.com/google/play/integrity/verdict).
* Datadog, [`DatadogLoggingConfiguration.eventMapper`](https://pub.dev/documentation/datadog_flutter_plugin/latest/datadog_flutter_plugin/DatadogLoggingConfiguration-class.html).
