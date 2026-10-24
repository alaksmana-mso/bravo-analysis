**Working page for the RASP vendor selection.** One section per vendor, all scored on the same scorecard. Add findings and screenshots after each call. The decision criteria and the shortlist come from Mobile plan 01: Security, step 7.

## How to use this page

- Every vendor gets the same section layout: what we saw, what was proven on our terms, what was not shown, open asks, data and hosting, commercials.
- "Proven" means one of us drove the test or supplied the input. "Shown" means the vendor ran it on their own app or device. The scorecard counts only "proven".
- Screenshots go under the vendor's section. Do not paste chat transcripts or the presenter's face. Product screens only.
- The scorecard is the same one as plan 01. Fill a cell only with one of: **Pass**, **Fail**, **Shown, not proven**, **Not tested**, **Not supported**.

## Scorecard

Columns are filled in as calls happen. Empty means not yet evaluated.

| Check | Pass mark | Talsec | DoveRunner | Promon | V-Key | Appdome | Guardsquare | Everspin |
|---|---|---|---|---|---|---|---|---|
| Integrates into our GitHub Actions build, Android and iOS | Under 5 working days | Not tested | | | | | | |
| Source changes needed | None or very few | Not tested (SDK, so some) | | | | | | |
| Extra build time | Under 5% | Not tested | | | | | | |
| Frida attach | Detected every time | Shown, not proven | | | | | | |
| Magisk + Zygisk + DenyList | Detected every time | Not tested | | | | | | |
| Root, jailbreak, emulator, KernelSU | Detected every time | Shown, not proven (emulator + test-keys root) | | | | | | |
| Debugger attach, code injection | Detected every time | Shown, not proven | | | | | | |
| Tampered, re-signed build | Rejected | Not tested | | | | | | |
| Server-side attestation our backend can verify | Reliable verdicts | Not tested (AppiCrypt not demoed) | | | | | | |
| Replayed attestation token | Rejected by our backend | Not tested | | | | | | |
| Malware on device (Indonesian banking trojan sample) | Detected | **Pass, with a caveat** (our Hirudo APK, run by Talsec on their demo app, confirmed by email) | | | | | | |
| Overlay, tapjacking, screen recording | Detected or honest "no" | Screen recording yes; overlay not on the list | | | | | | |
| False positives on mid-range Android | Zero critical | Not tested | | | | | | |
| Crashes caused by the RASP | Zero | Not tested | | | | | | |
| App start and transaction speed | No visible change | Not tested | | | | | | |
| Report-only switch without a release | Yes | Shown (per-check reaction in console) | | | | | | |
| Threat dashboard | Working, real time | Shown (Elastic + Client Risk State portal) | | | | | | |
| Telemetry into Datadog | Export exists | Open ask | | | | | | |
| On-prem or in-country option | Available | Shown (Docker images on our Kubernetes) | | | | | | |
| Support response in PoC | Under 4 hours critical | Not tested | | | | | | |

## Talsec

**Call:** 19 October 2026, Google Meet. Talsec presenter: Sergiy Yakymchuk. BFI: Andre Laksmana (left early for another meeting), mobile team members stayed to the end.

### What was shown

- **Per-check reactions.** Each detection has its own reaction, set in their console: Kill, Callback and Kill, Callback, or Ignore. The checks on the list: ADB enabled, Android developer mode, app data migration, application integrity, automation (Appium), bootloader, debugger, emulator or simulator, hooking and runtime manipulation, location spoofing, multi-instance, obfuscation issues, privileged access (root or jailbreak), screen recording, screenshot, secure hardware not available, system VPN, time spoofing. He said there are "hundreds of controls" grouped into these reactions.
- **Telemetry, two ways.** Raw incident documents in Elastic: one `status` and `timeMs` per check, plus device model and manufacturer, SELinux state, IP, city and country. And a **Client Risk State** service: `GET /v1/risk-state/<app>/devices/<device>/risk-state` returns a severity score with the reasons and whether a configured threshold is exceeded. The demo device scored High 300 from seven findings.
- **On-prem option.** The risk-state service and its portal can be delivered as Docker images and run on our Kubernetes, with device state kept in memory and queried by our anti-fraud engine. He positioned this for regulated customers who cannot send data to an external cloud.
- **Malware detection (MTD).** Built with a threat-intelligence partner (name unclear in the captions, a regional company). Two parts: an optional remote app-reputation API that checks every installed app, and a heuristic detector for apps that could steal SMS or misuse the accessibility service. He said they get many reports of banking malware from our region.
- **Demo environment.** Their own demo app (`app.talsec.demo.rasp.*`) on an Android 12 emulator. Nothing was shown on our app or on iOS.

### What was proven on our terms

- **Malware detection works on a real sample, with a caveat.** A BFI mobile team member supplied a sample of the **Hirudo** Android banking malware. Talsec ran it on their demo app and confirmed detection by email the same evening (19 Oct 2026, 18:02 WIB, subject "Talsec App Security follow up data", with a screenshot). We chose the input, so it counts as proven on our terms. But the test ran on Talsec's device and app, not ours, and we did not watch it. The PoC must repeat it on our SIT build in our hands before the row is a clean Pass.

### What was not shown

- No Frida attach. He described the reaction but did not run it. The demo document shows `hooks: OK`.
- No Magisk with Zygisk and DenyList. The root finding shown was the easy case: emulator with test keys and a rooting package installed.
- No tampered and re-signed build.
- AppiCrypt, their server-side attestation, was not demonstrated at all.
- Nothing on iOS.
- Nothing on our app, so none of the integration questions were tested: R8, the IOSSecuritySuite we already ship, Vida liveness, Mixpanel session replay, Datadog RUM, size and start time.

### Things to pay attention to

- **Score logic.** The portal says a finding clears only when the device's retained history holds only OK results. One false positive keeps a device at High until the history ages out. Ask the retention window and whether we can clear a finding by hand.
- **Telemetry is personal data.** Each incident carries IP, city, country, device model and a device identifier. On their SaaS this needs a data-processing agreement and data-protection-officer review before production. On-prem avoids the transfer.
- **SDK model.** Talsec compiles into the app. A wrapper (Promon, Appdome, Everspin) protects the finished binary. An SDK's checks are visible to anyone who decompiles the app. Ask what stops the detection code from being patched out.
- **Overlay and tapjacking** are not on the reaction list we saw. Screen recording and screenshot are. Accessibility appears as a check in the Elastic document. Ask directly.

### Open asks sent to Talsec

1. A PoC on our SIT build, scored on the scorecard above, with a BFI engineer holding the phone and the Frida laptop. The five tests not shown: Frida attach, Magisk with DenyList, a tampered re-signed build, a replayed AppiCrypt token, a normal user on a mid-range Xiaomi or Oppo.
2. In writing: the iOS check list side by side with Android; whether overlay and tapjacking are detected; the risk-state retention window and whether a finding can be cleared by hand; how telemetry reaches Datadog.
3. The on-prem option priced separately, with the Docker images and the resources they need.
4. Confirmation that a reaction change in the console reaches the app without a store release.

### Data and hosting

- SaaS: telemetry to Talsec-hosted Elastic and portal. Location of the hosting not stated. Ask.
- On-prem: risk-state service and portal as Docker images on our Kubernetes.
- RASP+ (the paid tier) sends no telemetry to Talsec, per their published terms. freeRASP does, and is capped at 100,000 devices per organisation, so freeRASP is for a SIT trial only.

### Commercials

- Not discussed on the call. Ask for a 3-year price at today's user count and at double, with SaaS and on-prem as separate lines.
- Vendor materials sent after the call: a default offer and sales slides (links in the 19 Oct email). Treat them as the starting point for the quote, not the quote.

### Screenshots

Product screens from the call. Captions and the presenter are not included.

## DoveRunner (formerly AppSealing)

**Call:** not yet held.

Known before the call: wraps the built app (obfuscation, encryption, RASP). Used by Kredivo in Indonesia. Flutter support to confirm. Licence model to ask.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## Promon SHIELD

**Call:** booked for 28 October 2026, 15:00 WIB. Promon contacts: Sai Kwan Lau, Eric Iswara. Promon confirmed by email (16 Oct) that SHIELD integrates with a Flutter app. We asked for a Flutter mobile RASP demo, not a slide deck.

Known before the call: post-build protection added in the pipeline. RASP-first, common in banking, rich telemetry and callback APIs for a fraud engine, app attestation (Verify) and analytics (Insight). Lighter on code obfuscation. Licensed by active users.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## V-Key

**Call:** not yet held.

Known before the call: SDK with a software "virtual secure element" (V-OS) that isolates keys and sensitive code. Strongest on device binding and in-app identity (smart token, biometrics, MFA). Blocks screen sharing, checks accessibility and side-loaded apps. Flat yearly subscription. Flutter support to confirm.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## Appdome

**Call:** not yet held.

Known before the call: no-code, the built app goes in through an API in CI/CD and a protected app comes out in 2 to 10 minutes. Soft exits instead of crashes. Detections can be forwarded as headers to our backend. A certificate of protections per build. Flat yearly fee per app.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## Guardsquare (DexGuard and iXGuard)

**Call:** not yet held.

Known before the call: build-time hardening through a Gradle plugin and the Xcode toolchain, polymorphic protection per build, ThreatCast monitoring. Strongest on obfuscation. Licensed by downloads in three tiers; server-side attestation needs the top tier.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## Everspin (Eversafe and CodeMix)

**Call:** not yet held.

Known before the call: wraps the built app and registers each build for forgery checks. What Jago's prod pipeline uses. Supplies financial institutions in Indonesia. Licence model to ask.

### What was shown

### What was proven on our terms

### What was not shown

### Things to pay attention to

### Open asks

### Data and hosting

### Commercials

### Screenshots

## Decision log

| Date | Decision or finding | By |
|---|---|---|
| 11 Oct 2026 | Free layer first (R8 explicit, root check fail-safe, backend enforces Play Integrity and App Attest). freeRASP for a SIT trial only. RFP to Promon, Guardsquare, Appdome, V-Key; Everspin and DoveRunner if local support is a must. | Andre |
| 19 Oct 2026 | Talsec call. Detection list, per-check reactions, Elastic telemetry, on-prem risk-state shown. Frida, DenyList, tamper, AppiCrypt, iOS and our app not tested. PoC requested. | Andre, mobile team |
| 19 Oct 2026 | Talsec confirmed by email that the Hirudo malware sample supplied by BFI is detected by their anti-malware SDK, tested on their demo app. | Talsec, BFI mobile team |
| 28 Oct 2026 | Promon demo booked, 15:00 WIB. Flutter RASP demo requested. | Andre |
