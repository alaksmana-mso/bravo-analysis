## Summary

This page prepares Phase 10 of the mobile roadmap ("Platform") for refinement. It covers the 6 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Platform". These items can run next to Phase 9 when the release rules hold.
* **Parent:** Mobile roadmap: step by step, section "Phase 10: Platform". Plan pages: Mobile plan 01: Security step 7, Mobile plan 13: Design system steps 6–7, Mobile plan 02 step 11, Mobile plan 04 step 10.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct) and the Flutter, Google and OWASP docs.

**What Phase 10 is.** The items that need a vendor, a budget or a product decision before engineering can start. Each has its own entry gate. None blocks the others.

### Facts that shape Phase 10

* **RASP.** The app pins a local `flutter_jailbreak_detection` package with `IOSSecuritySuite < 2.0` (1.x is BSD-licensed; 2.x needs a paid licence by headcount). No RASP in prod. The RFP (1.24) and the SIT trial (3.11) feed the decision. Google's own view: environmental conditions can make integrity checks fail, so retry with backoff and never hard-block on the first failure.
* **Material 3.** `app_theme.dart` sets `useMaterial3: false`. Flutter made Material 3 the default in 3.16 (November 2023) and says the flag and the Material 2 code "will eventually be removed". No removal version is published. The app is on Flutter 3.41.9.
* **Figma tokens.** No token pipeline. Figma Code Connect has no Flutter support (confirmed on Mobile plan 14). DK's Jago library has a token pipeline and a Widgetbook.
* **iOS signing.** No fastlane directory. Certificates and profiles are base64 environment secrets decoded at build time. Phase 0 recommended Cloud KMS for the Android upload key (2.25); iOS has no equivalent keyless path.
* **AppsFlyer and Datadog RUM actions.** `appsflyer_service.dart` exists; no journey milestone events are sent to AppsFlyer or as RUM actions today.

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days, **L** = 2–3 weeks. Class **D** = approved delta, **C** = flagged, **B** = same behaviour, **A** = no app change.

| # | Proposed ticket title | Entry gate | Class | Owner (role) | Size | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10.1 | RASP in prod, report-only mode; fill the "Protect build" and "Register build" slots | Vendor chosen and contracted (1.24), SIT trial report (3.11) | D | Security + mobile engineer + SRE | L | | |
| 10.2 | RASP enforce mode | 10.1 clean for 2 releases | D | Security + feature owner | S + 2 releases | | |
| 10.3 | Material 3 inside the design-system package | 8.3 done, component goldens in place (8.5) | D (behind a flag per screen group) | Mobile engineer + design | L | | |
| 10.4 | Optional: Figma token pipeline | Design keeps Figma variables current (8.1) | B | Mobile engineer + design | M | | |
| 10.5 | Optional: journey milestones to AppsFlyer and Datadog RUM actions | Product decision on which milestones | D | Product + mobile engineer | S | | |
| 10.6 | Optional: fastlane and match for iOS signing | Only if certificate handling is painful | A | Mobile engineer + SRE | M | | |

## Definition of ready

* The entry gate is met and written in the ticket.
* For 10.1 and 10.2: the PoC scorecard result and the false-positive budget are attached.
* For 10.3: the per-screen-group flag and the golden review process are agreed with design.
* Each ticket names its rollback (report-only, flag off, revert).

## Step 10.1: RASP in prod, report-only first

**Today.** No RASP. The vendor is chosen through the RFP and PoC (Phase 1 step 1.24: Promon, Guardsquare, Appdome, V-Key; Everspin and DoveRunner if local support is a must). The prod workflow has empty "Protect build" and "Register build" steps since 2.18.

**Tasks.** Integrate the vendor's build step (protect before sign, like Jago's `codemix → zipalign → apksigner` order) and build registration. Ship in **report-only mode**: detections are logged to Datadog with device model and OS, nothing is blocked. Watch the report rate for 2 releases. Agree a false-positive budget (for example under 0.1% of sessions on known-good devices).

**Acceptance criteria.** The protected build passes the full parity net (goldens, fixtures, e2e) and the Phase 2 smoke list. Report rate by device model is on a dashboard. No increase in crash rate or startup time beyond the agreed threshold (vendor SDKs add startup cost; measure p75 cold start before and after).

**Who / size.** Security + one mobile engineer + SRE for the pipeline. L.

**Risks.** A false positive blocks a real customer from their loan. That is why enforce mode is a separate step. Vendor SDKs can also break R8 keep rules and increase app size; measure both.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Commercial RASP from the PoC winner, report-only first | Real anti-tamper, vendor support, fraud telemetry | Licence cost; per-user pricing grows with the base (ask for a flat quote) |
| B. Free layer only (R8 explicit, root check fail-safe, backend verdict enforcement) and freeRASP paid tier later | Low cost | Public checks are bypassable; freeRASP free tier is capped at 100k devices and sends telemetry to the vendor |
| C. Enforce from day one | Faster "protection" | Blocks customers on false positives; no baseline to compare against |

**Recommended: A.** B's items happen anyway in Phases 2 and 3.

## Step 10.2: RASP enforce mode

**Today.** After 10.1: 2 releases of report-only data.

**Tasks.** Turn on blocking for the agreed detections (rooted or jailbroken device, debugger, repackaged app, hooking framework), one detection class at a time, behind a remote switch so it can go back to report-only in minutes. Customer support gets a script for "the app says my device is not safe".

**Acceptance criteria.** Cohort dashboard green for each detection class. Support tickets about blocked devices reviewed weekly for the first month. A remote switch returns to report-only within one journey start.

**Who / size.** Security + feature owner. S of code, 2 releases of watching.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One detection class at a time, remote switch per class | Each false-positive source is found on its own | Several weeks |
| B. All classes at once | Fast | A single bad rule blocks many customers and nobody knows which rule |
| C. Enforce only on high-value journeys (loan submission, payment), report elsewhere | Protects what matters, fewer blocked sessions | More complex policy to explain and test |

**Recommended: A, moving to C's policy if support load is high.**

## Step 10.3: Material 3 inside the design-system package

**Today.** `useMaterial3: false`. Flutter's default is Material 3 since 3.16; Material 2 "will eventually be removed", no date given. Component goldens exist after 8.5.

**Tasks.** Flip `useMaterial3` inside `shared_lib/design_system` only. Fix every golden diff component by component with design's sign-off (colours, shapes, text styles, `NavigationBar` and other replaced widgets). Roll out behind a switch flag per screen group so a visual regression can be turned back.

**Acceptance criteria.** Golden diffs reviewed and signed by design for every component. Key-screen goldens (1.12) updated with sign-off. Cohort check shows no change in task completion on the switched screens.

**Who / size.** One mobile engineer + design. L.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Flip inside the package, fix goldens, flag per screen group | Controlled, reviewable, reversible | Weeks of design review |
| B. Flip in the app in one release | Fast | Every screen changes at once; the goldens all fail; no way back per screen |
| C. Stay on Material 2 until Flutter forces it | No work now | A forced migration later, on Flutter's schedule, with no goldens to catch the diffs |

**Recommended: A**, scheduled after 8.5 and before Flutter removes the flag (watch the breaking-changes page each quarter).

## Step 10.4: Optional, Figma token pipeline

**Today.** No pipeline. Figma Code Connect does not support Flutter. DK's Jago library generates tokens from a Figma export.

**Tasks.** Export Figma variables as JSON (DTCG format) into the package (`tokens/source.json`). A small generator writes `lib/tokens/*.g.dart`. CI checks the generated files match the JSON. A short skill file explains the steps.

**Acceptance criteria.** Generated tokens match the JSON in CI. One brand, light mode. Component goldens unchanged after the first generation (tokens equal today's values).

**Who / size.** One mobile engineer + design. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own generator from a DTCG JSON export | Small, no vendor | Design must keep Figma variables current (8.1 question) |
| B. Tokens Studio or Style Dictionary pipeline | Standard tooling, multi-platform | More setup; Style Dictionary needs a Dart transform |
| C. No pipeline; tokens maintained by hand in Dart | No work | Drift between Figma and code |

**Recommended: A if design commits to Figma variables; otherwise C with a quarterly review.** Only start if 8.1 confirmed the commitment.

## Step 10.5: Optional, journey milestones to AppsFlyer and Datadog RUM

**Today.** No milestone events to AppsFlyer; no RUM custom actions for journeys. The analytics port (Phase 2) makes adding a sink a one-line change per event.

**Tasks.** Product picks the milestones (for example `loan_submitted`, `kyc_completed`). Add the AppsFlyer and Datadog RUM sinks to those event classes. Approved delta (new data to a third party): DPO sign-off on the parameters.

**Acceptance criteria.** The chosen events appear in AppsFlyer and as RUM actions. Golden names file shows only the added sinks, no renamed events.

**Who / size.** Product + one mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. A handful of milestones, sinks added on the event class | Cheap with the port in place | Needs the product list and DPO sign-off |
| B. Mirror every event to AppsFlyer | Simple rule | Cost per event and more data to a third party |
| C. Do nothing | No work | Marketing attribution stays coarse |

**Recommended: A.**

## Step 10.6: Optional, fastlane and match for iOS signing

**Today.** `apple-actions/import-codesign-certs` and `xcodebuild`. Certificates and profiles as base64 secrets. No fastlane.

**Tasks.** Only if certificate handling is painful (expiry incidents, manual profile updates). `fastlane match` keeps certificates in an encrypted store; all builds use the same ones. Otherwise keep today's setup and rotate on a schedule.

**Acceptance criteria.** iOS build signs with the same certificates; TestFlight upload unchanged; the base64 secrets are removed from the environments.

**Who / size.** One mobile engineer + SRE. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `fastlane match` with an encrypted GCS bucket | Shared certificates, rotation in one place | One more tool on the macOS runner |
| B. Keep `import-codesign-certs`, add an expiry monitor | Minimal | Manual renewal stays |
| C. Xcode Cloud for iOS builds | Apple-managed signing | A second CI system for one platform |

**Recommended: B now, A only if an expiry incident happens** or certificates must be shared with another BFI iOS app.

## Exit gate for Phase 10

* Per item: 10.1 report-only for 2 releases with the false-positive rate inside budget; 10.2 enforce on with support tickets reviewed; 10.3 Material 3 on for all screen groups with design sign-off; 10.4–10.6 done or recorded as "not now" with a reason and a review date.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which RASP vendor won the PoC, and what is the false-positive budget? | Security + engineering manager | |
| Q2 | Which detections are enforced first, and what does support tell a blocked customer? | Security + support lead | |
| Q3 | Does design commit to keeping Figma variables current (for 10.4)? | Design lead | |
| Q4 | Which journey milestones does marketing need in AppsFlyer (10.5)? | Product + marketing | |
| Q5 | Has iOS certificate handling caused an incident in the last year (10.6)? | Release manager | |
| Q6 | Epic for Phase 10: one epic, or one per item since they have different owners? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| RASP today | `digital/pubspec.yaml` lines 48–52; `digital/ios/Podfile.lock` line 184 (`IOSSecuritySuite < 2.0.0`) |
| Material 3 | `digital/lib/app/theme/app_theme.dart` line 9 |
| No fastlane | `ls digital/ios` |
| AppsFlyer | `digital/lib/app/appsflyer/appsflyer_service.dart` |

## Sources for the recommendations

* Flutter, [Material 3 is the default](https://docs.flutter.dev/release/breaking-changes/material-3-default) and [Migrate to Material 3](https://docs.flutter.dev/release/breaking-changes/material-3-migration): flag is temporary, Material 2 will eventually be removed, no date.
* Android, [Play Integrity overview](https://developer.android.com/google/play/integrity/overview): environmental failures, retry with backoff. OWASP, [MASTG-KNOW-0035](https://mas.owasp.org/MASTG/knowledge/android/MASVS-RESILIENCE/MASTG-KNOW-0035/).
* Mobile plan 01: Security, step 7 (vendor list, PoC scorecard, licence models, freeRASP limits). Mobile plan 14 (DTCG tokens, Figma variables, Code Connect has no Flutter support).
