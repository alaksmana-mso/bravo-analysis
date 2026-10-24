## Summary

This page prepares Phase 3 of the mobile roadmap ("Approved deltas, one per release") for refinement. It covers all 11 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title, same style as Phase 0 (DM-3545): "[Tech x DK] Mobile App Improvement - Approved Deltas".
* **Parent:** Mobile roadmap: step by step, section "Phase 3: Approved deltas, one per release". Earlier notes: Phase 0, Phase 1 and Phase 2 refinement pages under the same parent.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct), the plugin versions in `pubspec.lock`, and the Google, Apple, Datadog and OWASP docs.

**What Phase 3 is.** Every step here changes what customers or third parties see or receive. That is on purpose. Each change is signed off before it ships, goes out alone in its release, is watched on the release health dashboard, and has a way back. These are the "approved deltas" from the parent page's parity rules: they are listed, signed off, and left out of the parity check.

**Three rules for this phase.**

1. **One delta per release.** If two ship together and something breaks, we cannot tell which one did it.
2. **Sign-off before code.** The data protection officer (DPO) signs privacy deltas. Product signs behaviour deltas. The ticket is not ready until the sign-off is in it.
3. **Monitor first for anything the backend enforces.** Class E steps log what they would block for 2 weeks before they block.

### Five facts that shape Phase 3

**1. The personal-data leak in analytics is still live.** `home_loan_simulation.dart` line 369 sends `customer_address` (the full domicile address) in the `apply_loan` Firebase event. `requireTrackValue` appears 27 times in the app (plan 02 counted 4 fields). Google's Analytics terms forbid uploading data that lets Google identify a person. So step 3.4 is a compliance fix, not only a privacy nicety.

**2. Raw error text in logs is smaller than the plan said, but the risk is the same.** 55 `DatadogLog.error` or `warn` call sites exist outside tests. 19 of them put `$e`, `$error` or `.toString()` into the message (plan 05 said 35 of 38; the counting method differs). Any of these can carry a server response body with a name or an ID number. Datadog's Flutter plugin has a log `eventMapper` hook that can change or drop a log before it leaves the device. That is the natural place for the sanitiser (3.1).

**3. The root check is off by default in code.** `app_config.dart` line 20: `bool.fromEnvironment('IS_DEVICE_ROOT_CHECKER_ENABLED')` with no `defaultValue`, so the default is `false`. Prod turns it on through a GitHub variable in `build-prod.yml`. If that variable disappears, the check goes silent (3.7).

**4. Nothing blocks screenshots today.** No `FLAG_SECURE`, no secure-layer trick, no screen-capture plugin in the app (3.8). The common plugins all use the same two tricks, and the iOS one relies on UIKit internals that Apple can change. One plugin's own docs say iPhone Mirroring on iOS 26.5.2 still shows the protected surface.

**5. Datadog tracking consent is a constant.** `main.dart` line 31: `DatadogSdk.runApp(_ddSdkConfig, TrackingConsent.granted, _runApp)`. The real consent value comes with step 3.3.

Counts refreshed on 23 Oct: 9 uses of documents or temporary directories in `file_service.dart` and friends, 0 backup-exclusion attributes, 6 references to `loanSubmissionDrafts` or `lastRepaymentPaymentDetails`, no WebView navigation allow-list found by `grep`, `api-secret` header set in `http_client.dart` line 32.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days, including review. Class: **D** approved delta, **E** backend-coupled, **A** no app change.

| # | Proposed ticket title | Today (23 Oct) | Class | Signs off | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3.1 | `feat(core): PiiSanitizer before logs and crashes leave the device` | No sanitiser | D | DPO | Mobile engineer | M | 2.5 | | |
| 3.2 | `refactor(core): Fixed log messages, error as a field` | 19 of 55 sites put raw error text in the message | D | Squad lead | Mobile engineer | S | 3.1 | | |
| 3.3 | `feat(analytics): Consent state and PII key denylist` | Consent hard-coded granted | D | DPO | Mobile engineer | S | 2.2 | | |
| 3.4 | `fix(analytics): Remove customer_address from apply_loan, bucket income and amount` | Full address sent to Firebase | D | DPO + dashboard owner | Mobile engineer + product analytics | S | 3.3, 1.11 | | |
| 3.5 | `feat(core): Pseudonymous user ID in Crashlytics and Datadog` | No user ID set | D | DPO | Mobile engineer | S | 2.5 | | |
| 3.6 | `chore(core): Remote log threshold info in prod` | No threshold set | D (volume only) | SRE | Mobile engineer | XS | 2.5 | | |
| 3.7 | `fix(security): Root check on by default, CI asserts prod flags` | Code default false, prod var true | D | Squad lead | Mobile engineer | XS | – | | |
| 3.8 | `feat(security): Screen-capture guard on sensitive screens` | Nothing blocks screenshots | D | Product | Mobile engineer | M | 2.12 (kill switch) | | |
| 3.9 | `fix(security): Secure storage review` | Images in documents dir, no backup exclusion | D | Product + DPO | Mobile engineer | M | 1.14 (e2e) | | |
| 3.10 | Backend: stop trusting `api-secret` alone, enforce integrity verdicts | Header sent on every request | E | Security + BFF owner | BFF team + mobile | M | Phase 1 Q (min. version) | | |
| 3.11 | freeRASP trial in SIT, report-only | Not started | A (SIT only) | Security | Mobile engineer | S | – | | |

**Suggested order (one D per release).** Release 1: 3.7 (smallest, pure safety). Release 2: 3.1 + 3.2 together (one delta: "logs are sanitised"). Release 3: 3.3. Release 4: 3.4. Release 5: 3.5 + 3.6. Release 6: 3.8 behind its kill switch. Release 7: 3.9. In parallel, no release needed: 3.10 (backend, monitor-only), 3.11 (SIT only). At today's pace of one prod release every 2 weeks, that is about 14 weeks. Pairs can merge if the DPO signs them as one change.

## Definition of ready for every Phase 3 ticket

* The ticket links to this page and to the Phase 3 epic.
* The sign-off is recorded in the ticket (who, date), and the row is added to the "Approved deltas" table on the parent assessment page.
* The ticket names its release and confirms no other class C or D change ships in it.
* The rollback is written: kill switch, remote config value, or halt and hotfix.
* For 3.3, 3.4 and 3.5: the golden names file (1.11) diff is attached and reviewed by product analytics.

## Step 3.1: `PiiSanitizer` before logs and crashes leave the device

**Today.** No sanitiser. `DatadogLog` (61 sites) forwards to Datadog and Crashlytics. 19 call sites put the raw error text in the message. Datadog's `datadog_flutter_plugin` 3.5.0 has `DatadogLoggingConfiguration.eventMapper` ("modify or drop specific LogEvents before they are sent"). The RUM configuration has event mappers too (confirm names in 3.5.0). Datadog's own privacy page says PII in unstructured text can only be removed afterwards by a deletion request.

**Tasks.** Add `PiiSanitizer` in `shared_lib/core/lib/src/monitoring/`. Cover NIK (16 digits), phone numbers, email, NPWP, account numbers, and JSON keys such as `name`, `address`, `mother_name`, `phone`, `nik`. Wire it in the `Monitoring` port (2.5) so both adapters use it, and register it as the Datadog log `eventMapper` as a second net. Test with real-shaped fake samples, including a `FormatException` that carries a JSON body.

**Acceptance criteria.** Sanitiser unit tests 100% covered. A phone number in a message reaches Datadog and Crashlytics redacted (SIT test). A weekly Datadog query for NIK and phone patterns in mobile logs returns zero hits for 2 weeks. Existing `datadog_log_test.dart` passes with the redaction added.

**Who / size.** One mobile engineer. DPO signs off. M.

**Risks.** Over-matching hides useful detail (for example a 16-digit order number). Keep an allow-list of known safe keys and log a sanitiser hit counter so we can see how often it fires.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own sanitiser in the `Monitoring` port, plus the Datadog `eventMapper` as a second net | One rule set for both sinks. The mapper catches logs that bypass the port | Regexes to maintain |
| B. Datadog Sensitive Data Scanner on the server side only | No app code | Data has already left the device. Does not cover Crashlytics. Extra Datadog product |
| C. Only fix the 19 call sites (3.2), no sanitiser | Smallest | The next `$error` goes straight through |

**Recommended: A.** Do 3.2 in the same release so the sanitiser sees the error as a field, not inside a sentence.

## Step 3.2: Fixed log messages, error as a field

**Today.** 19 sites build the message from the error (`'...: $error'`, `$e`, `.toString()`).

**Tasks.** Replace with a fixed message and `error:` as a separate field. Add a checker rule (`log-raw-error`, baseline 19, must only go down).

**Acceptance criteria.** `grep` finds 0 `DatadogLog.(error|warn)(` calls with `$error`, `$e` or `toString()` in the message. Log messages in Datadog become stable strings, so the "Found Errors" dashboard groups them.

**Who / size.** One mobile engineer. S. Log text is not in the parity net, so this is a delta by definition, but a harmless one.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Fix the 19 sites now, ratchet the rest | Done in one PR. Future sites blocked | 19 messages change in dashboards |
| B. Fix only when touched | No dedicated work | The leak path stays open for months |
| C. Rewrite all 55 sites to a new log API | Clean | Not needed; the port (2.5) already gives the shape |

**Recommended: A.**

## Step 3.3: Consent state and PII key denylist

**Today.** `TrackingConsent.granted` is hard-coded in `main.dart`. No denylist in the analytics path. The analytics port and adapters exist after Phase 2 (2.1–2.4).

**Tasks.** Add a `ConsentState` provider (default: granted, matching today, so no behaviour change at first). Adapters check it. Pass the real value to Datadog instead of the constant. Add a key denylist in the fan-out, matched on whole words (`address`, `phone`, `nik`, `email`, `customer_name`, `income`), so `product_name` passes. Debug builds assert, release builds drop the key and log a warning through the sanitised monitoring path.

**Acceptance criteria.** A unit test sends a denied key and sees it dropped. Golden names file unchanged (names stay, only the denied parameters go). Datadog receives the consent value from the provider.

**Who / size.** One mobile engineer. DPO signs off the denylist. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Denylist in the fan-out + consent provider, default granted | Closes the leak class, not one event. No visible change until a consent UI exists | A consent screen is a product decision (Q2) |
| B. Only remove known bad parameters at their call sites | Small | The next PII parameter sails through |
| C. Full consent flow (screen, storage, per-vendor opt-out) now | Complete | Product and legal work; belongs to a later delta once Q2 is answered |

**Recommended: A now, C when product decides on consent UX.**

## Step 3.4: Remove `customer_address` from `apply_loan`, bucket income and amount

**Today.** `home_loan_simulation.dart:369` sends `'customer_address': domicile?.asCompleteFormat` to Firebase in `apply_loan`. Loan amount, income, marital status and loan purpose go to Mixpanel through `requireTrackValue` (27 occurrences). Google Analytics terms do not allow data that identifies a person.

**Tasks.** Replace the address with city only, or remove it. Bucket income and amount (for example 5 bands) if the dashboard owner needs them. Review every `requireTrackValue` field with the DPO.

**Acceptance criteria.** Golden names file diff shows only the agreed parameter changes. Firebase DebugView on dev shows `apply_loan` without the address. The dashboard owner confirms their report still works.

**Who / size.** One mobile engineer + product analytics. DPO and dashboard owner sign off. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. City only + banded amount and income | Keeps the dashboards useful. Removes direct identifiers | Bands must be agreed with analytics |
| B. Remove all four parameters | Simplest and safest | Marketing loses funnel detail |
| C. Keep, hash the address | Looks private | A hash of an address is still personal data in most readings. Not a fix |

**Recommended: A.**

## Step 3.5: Pseudonymous user ID

**Today.** No `identify` or `setUserInfo` call in the monitoring path. Support cannot find a customer's crash.

**Tasks.** Call `identify(customerId)` on login and clear on logout, for Crashlytics and Datadog (`setUserInfo` with ID only, no name, no phone). Through the `Monitoring` port.

**Acceptance criteria.** A dev crash shows the customer ID and nothing else about the user. Logout clears it (test).

**Who / size.** One mobile engineer. DPO signs off. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Internal customer ID only | Support can search by ID. No direct identifier leaves the device | Still a pseudonymous identifier; needs DPO sign-off and a retention note |
| B. A per-install random ID, mapped to the customer in our backend | Stronger separation | Support needs a lookup tool |
| C. No user ID | Nothing to sign off | Support stays blind; the parent page lists this as a benefit we want |

**Recommended: A**, with B noted as the stricter fallback if the DPO asks for it.

## Step 3.6: Remote log threshold in prod

**Today.** No remote threshold set on the Datadog logger. Session and trace sampling come from GitHub variables (`DATADOG_SESSION_SAMPLING_RATE`, `DATADOG_TRACE_SAMPLING_RATE`).

**Tasks.** Set the Datadog remote log threshold to `info` in prod and `debug` in dev. Write the agreed prod sampling values on Mobile plan 05.

**Acceptance criteria.** Datadog log volume for the app drops by the debug share and stays within the agreed range for 1 week. No error or warn log is lost (count before and after).

**Who / size.** One mobile engineer. SRE agrees the numbers. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Threshold `info` in prod through the adapter | One line, reversible by hotfix | Debug logs from prod are gone (they should be) |
| B. Threshold driven by a remote flag | Can raise to `debug` for an incident | One more flag; a flag read at startup only |
| C. Leave as is | No work | Pays for debug logs from every customer |

**Recommended: A**, and B later if on-call asks for it.

## Step 3.7: Root check on by default, CI asserts prod flags

**Today.** `IS_DEVICE_ROOT_CHECKER_ENABLED` and `IS_HTTP_PROXYING_ALLOWED` are read with `bool.fromEnvironment` and no `defaultValue`, so both default to `false`. Prod passes `IS_DEVICE_ROOT_CHECKER_ENABLED` from a GitHub variable. The root check runs at start only.

**Tasks.** `defaultValue: true` for the root check. A CI step in the prod workflow fails if `IS_DEVICE_ROOT_CHECKER_ENABLED` is not `true` or `IS_HTTP_PROXYING_ALLOWED` is not `false`. Re-run the root check when the app returns to the foreground.

**Acceptance criteria.** The prod value is unchanged (already on), so customers see nothing new. A SIT build on a rooted test device shows the block on resume. The CI check fails when the variable is removed in a test run.

**Who / size.** One mobile engineer. Squad lead signs off. XS.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Default true + CI assert + resume check | Fail-safe, no change for real users | A rooted tester's device gets blocked in SIT unless the flag is set |
| B. Default true only | Smallest | A missing variable still passes silently in CI |
| C. Move the decision to a remote flag | Can turn off for a bad device model | A failed fetch must still mean "on", so the default matters anyway |

**Recommended: A.**

## Step 3.8: Screen-capture guard on sensitive screens

**Today.** Nothing in the app. Android: `FLAG_SECURE` on the activity window blanks screenshots and the recents thumbnail. iOS: no public API; plugins put the Flutter view inside a secure text field's layer, which relies on UIKit internals. Known gaps: external cameras, and iPhone Mirroring on iOS 26.5.2 per one plugin's docs.

**Tasks.** A `go_router` observer with a list of protected routes and a method channel. Android sets and clears `FLAG_SECURE` as protected routes enter and leave. iOS applies the secure-layer approach and blurs the app-switcher snapshot. Routes: PIN entry and reset, OTP, KTP and selfie capture, KYC review, agreement and e-sign, bank account form, payment details. Behind a Remote Config kill switch (default on in prod after the cohort check).

**Acceptance criteria.** e2e journeys pass (Appium screenshots of protected screens will be black on Android; QA accepts that or captures through the test harness). Screenshots on those screens are blank on Android and iOS test devices. Kill switch off restores screenshots within one journey start.

**Who / size.** One mobile engineer. Product signs off (support may get "my screenshot is black" tickets). M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own method channel: `FLAG_SECURE` on Android, secure-layer on iOS, per route | Small, no dependency, we control the iOS trick | We own the iOS workaround when Apple changes UIKit |
| B. A pub.dev plugin (`screen_security` 1.1.x, `screen_guard`, `screenshot_defender`) | Ready-made | Small maintainers, low adoption, same UIKit dependency. One ships in a regulated app only after code review |
| C. Android only, iOS later | Half the work, solid API | iOS KYC screens stay capturable |

**Recommended: A**, reading option B's source for the iOS approach. Keep the kill switch for one full release.

## Step 3.9: Secure storage review

**Today.** `file_service.dart` writes to app directories (9 directory calls across the app). No iOS backup exclusion found. `loanSubmissionDrafts` and `lastRepaymentPaymentDetails` persist (6 references). `flutter_secure_storage` 9.2.4. No WebView navigation allow-list found.

**Tasks.** List what `FileService` writes and for how long. Delete KYC and vehicle images after upload. Write them to the cache or a temp folder, excluded from iCloud backup. Keep only what the draft screen needs in `loanSubmissionDrafts` and `lastRepaymentPaymentDetails`. Restrict the online-survey WebView to BFI domains. Check the Keychain accessibility setting for secure storage (`first_unlock_this_device` for tokens).

**Acceptance criteria.** KYC and document-capture journeys pass before and after (parity net). Loan draft resume passes. A file listing after a KYC run shows no KTP or selfie image left. WebView refuses a non-BFI URL in a widget test.

**Who / size.** One mobile engineer. Product and DPO sign off (draft retention is a product choice). M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete after upload, cache directory, backup excluded, Keychain accessibility set, WebView allow-list | Closes the storage findings in one delta | Draft behaviour may change for a user who left mid-KYC; needs a product call |
| B. Encrypt images at rest with a key in secure storage | Keeps files | Complexity, and the files still sit on the device |
| C. Only move to the cache directory | Small | The OS may keep them for a long time; no backup exclusion |

**Recommended: A.**

## Step 3.10: Stop trusting `api-secret` alone, enforce integrity verdicts (backend)

**Today.** The app sends `api-secret` on every request (`http_client.dart:32`) and `x-integrity-id` from Play Integrity or App Attest. Anyone can pull `api-secret` out of the APK. Google's guidance: verify the integrity token on the server, compare `requestDetails` with the original request, bind the token to the request (`requestHash`), check the timestamp and track nonces against replay, and do not cache classic verdicts.

**Tasks.** With the Customer BFF owners: write down that `api-secret` is a traffic tag, not a control. Every sensitive endpoint checks the user token and the integrity verdict. **Monitor-only for 2 weeks** (log would-be blocks by app version), then enforce for app versions at or above the minimum supported version. Later rotate `api-secret`, then remove it.

**Acceptance criteria.** Backend logs show 0 would-be blocks from current app versions for 2 weeks. Enforcement is on for new versions. Old versions keep working until the minimum version is raised. A pentest cannot call a sensitive endpoint with `api-secret` alone.

**Who / size.** BFF team (owner), security, mobile squad verifies. M, mostly backend.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Monitor-only, then enforce per app version | Safe for the long tail of old installs | Takes 3–4 weeks of calendar time |
| B. Enforce at once | Fast | Breaks old app versions and any device where Play Integrity fails (unstable network, overloaded device). Google itself recommends retry with backoff |
| C. Keep `api-secret`, rotate it monthly | No backend change | A secret anyone can extract is not a control, however often it rotates |

**Recommended: A.**

## Step 3.11: freeRASP trial in SIT, report-only

**Today.** The app pins `flutter_jailbreak_detection` (a local package) with `IOSSecuritySuite < 2.0`. No RASP. The free tier of freeRASP is capped at 100,000 devices and sends telemetry to Talsec, so it is for SIT only.

**Tasks.** Add freeRASP to SIT builds in report-only mode for 2 sprints. Count false positives by device model. Write a short report on Mobile plan 01.

**Acceptance criteria.** Report written, with the false-positive rate and the device models that triggered. Nothing shipped to prod.

**Who / size.** One mobile engineer. Security reads the report. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. freeRASP report-only on SIT, 2 sprints | Real data for the vendor decision (Phase 10) | SIT devices are not customer devices; the false-positive rate is indicative only |
| B. Skip the trial, go straight to the vendor PoC | Saves 2 sprints | The PoC scorecard has no baseline to compare against |
| C. Trial on a 1% prod cohort | Real devices | Free tier telemetry to a third party from prod: needs DPO sign-off and the paid tier. Not for Phase 3 |

**Recommended: A.**

## Exit gate for Phase 3

* Every delta on this page is at 100% for 1 release with no regression on the release health dashboard.
* Each delta has its row in the "Approved deltas" table on the parent page, with the sign-off.
* The weekly PII query on mobile logs returns zero hits for 2 weeks in a row.
* 3.10 is at least in monitor-only mode with the 2-week log reviewed.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Who is the DPO contact for sign-offs on 3.1, 3.3, 3.4, 3.5, 3.9? | Engineering manager | |
| Q2 | Does BFI want a user-facing tracking consent screen? If yes, when? | Product + legal | |
| Q3 | Who owns the `apply_loan` dashboard, and which bands for income and amount keep it useful? | Product analytics | |
| Q4 | Which screens are "sensitive" for the capture guard? Does customer support accept black screenshots on those screens? | Product + support | |
| Q5 | How long may a loan draft keep personal data on the device? | Product + DPO | |
| Q6 | Who owns the Customer BFF change for 3.10, and what is the minimum supported app version policy? | BFF lead + product | |
| Q7 | Can QA's Appium runs tolerate black screenshots on protected screens, or do we need a SIT-only bypass? | QA lead | |
| Q8 | Epic for Phase 3: one epic with 11 tickets? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Address in `apply_loan` | `digital/lib/features/home/loan_simulation/home_loan_simulation.dart` lines 364–369 |
| Raw error in log messages | `grep` for `DatadogLog.(error or warn)(` with `$e`, `$error`, `toString()`: 19 of 55 non-test sites |
| Root check default | `digital/lib/app/app_config.dart` lines 20–22; `build-prod.yml` lines 144 and 330 |
| No screen-capture code | `grep` for `FLAG_SECURE`, `setSecure`, `capturedDidChange` in `digital/`: 0 |
| Consent constant | `digital/lib/main.dart` line 31 |
| Storage | `digital/lib/app/file_service.dart`; 0 hits for `isExcludedFromBackup`; 6 refs to drafts and payment details |
| `api-secret` | `data/customer/lib/src/http_client.dart` line 32 |
| Datadog log mapper | `datadog_flutter_plugin` API docs, `DatadogLoggingConfiguration.eventMapper` |

## Sources for the recommendations

* Google, [Analytics Terms of Service](https://www.google.com/analytics/terms/): no data that lets Google identify a person (Firebase's own analytics policy page now points here).
* Datadog, [`DatadogLoggingConfiguration`](https://pub.dev/documentation/datadog_flutter_plugin/latest/datadog_flutter_plugin/DatadogLoggingConfiguration-class.html): `eventMapper` to change or drop logs before send. Datadog, [RUM data security](https://docs.datadoghq.com/data_security/real_user_monitoring/): PII in free text can only be removed by a deletion request.
* Android, [Play Integrity verdicts](https://developer.android.com/google/play/integrity/verdict) and [standard requests](https://developer.android.com/google/play/integrity/standard): verify on the server, `requestHash`, nonce and timestamp against replay, do not cache classic verdicts. OWASP, [MASTG-KNOW-0035](https://mas.owasp.org/MASTG/knowledge/android/MASVS-RESILIENCE/MASTG-KNOW-0035/).
* Screen capture: [screen_security](https://pub.dev/documentation/screen_security/1.1.0/) (caveats on UIKit internals and iPhone Mirroring), [screen_guard](https://pub.dev/packages/screen_guard), [screenshot_defender](https://pub.dev/packages/screenshot_defender).
* [flutter_secure_storage](https://pub.dev/documentation/flutter_secure_storage/latest/): iOS Keychain `accessibility` options.
* Talsec freeRASP limits: Mobile plan 01: Security, step 7.
