## Goal

Screens and controllers send analytics through one BFI interface, using typed events from one catalogue. Firebase, Mixpanel, Insider, AppsFlyer and Datadog RUM become adapters behind that interface. Every event name that dashboards use today stays exactly the same.

## Where we are today

Repo: `bravo-customer-app`, `master` @ `190e1d20`. Counts are from `grep` over `digital/lib` without generated files.

### Firebase path

- `digital/lib/app/analytics.dart` (144 lines) wraps `FirebaseAnalytics.instance`. It is the only file that touches the Firebase SDK.
- **187** `.logEvent(` calls in **81** files (80 outside `analytics.dart`).
- **148** distinct event names written as string literals: 140 fixed names and 8 built at runtime (for example `'click_via_${contact.type.name}'`).
- 84 files read `Analytics.provider`.
- Biggest users by file count: `features/loan` 31, `features/auth` 16, `features/home` 7. The other 26 files are spread over 15 folders.
- `logEvent` turns every parameter into a string and adds `product_name` from a hard-coded `switch` over `Product`.
- `analytics.dart` adds its own router listener and sends `logScreenView` for every route.

### Mixpanel and Insider path

- `digital/lib/app/tracker/mixpanel_service.dart` (400 lines). It tracks events, screen views, identity, super properties, campaign attribution and session replay.
- `EventTracker` (`tracker/event_tracker.dart`) is a typed event: `name`, `TrackerAction`, `TrackerComponent`, `properties`. Mixpanel name = `name-action` (kebab case).
- `TrackerJourney` enum has **34** journeys (8 submission, 12 login, 14 KYC). `TrackerJourneyManager` keeps a stack and adds `journey` to each event.
- Automatic tracking: `TrackerComponentMixin` is used by `DigitalButton`, `DigitalTextField` and `DigitalSearchBar`. It builds the event name from the label text. `DigitalBottomSheet` and `DigitalDialog` call `track` directly.
- **29** direct `MixpanelService.provider).track(` calls. 33 files import `mixpanel_service.dart`.
- Every Mixpanel event is copied to Insider (`insider_service.dart`, 166 lines) with a snake_case name.
- `DigitalSearchBar` sends the same interaction to Mixpanel and Firebase by hand, with two naming rules.

### Other platforms

- AppsFlyer (`appsflyer/appsflyer_service.dart`, 244 lines): attribution, deep links and customer user ID. It sends no in-app events today.
- Datadog RUM: views come from the router observer. Only **1** custom action in the app (`ktp_capture_screen.dart`).
- Datadog starts with `TrackingConsent.granted` hard-coded in `digital/lib/main.dart:42`. There is no consent state anywhere in the app.

### Personal data found in events

- `home_loan_simulation.dart:368` sends `'customer_address': domicile?.asCompleteFormat` with the `apply_loan` event to Firebase. Firebase terms do not allow personal data in event parameters.
- 4 fields set `requireTrackValue: true`. They send the typed value to Mixpanel: loan amount, monthly income, marital status and loan purpose.
- Insider receives name and phone number on login (`insider_service.dart`, `identify`). Mixpanel receives the display name as a user property.

## Target (what Jago does, adapted for BFI)

### Jago pattern

- `module_common/lib/analytics/analytics_platform.dart` (25 lines): an abstract `AnalyticsPlatform` with `sendEvent`, `setCustomerId` and `setUserProperty`.
- `analytics_platforms.dart` (138 lines): a fan-out. It merges common properties into each event, then calls every registered platform.
- `platforms/`: three adapters (Firebase, Datadog, CleverTap). Each is about 30 lines.
- Events are classes (`AnalyticsEventV2`). 62 files subclass it. Names live as constants in 62 files under `journeyconstants/` (including its `partner/` subfolder).
- `AnalyticsProperties` (`analytics_property.dart`) drops any value that is not a string, number or bool.
- Widgets call `context.sendAnalytics(event)` (`analytics_context_ext.dart`). An event bus hands it to `bloc/analytics_bloc.dart`, which calls a use case. Widgets never import an SDK.
- Debug-only events go only to platforms that accept them (`allowDebuggingPurpose`).

### BFI shape (Riverpod, no bloc)

- A new pure-Dart package `shared_lib/analytics`. It holds the port, the event base class, the context and the event catalogue. It has no SDK dependency, so future feature packages can depend on it (see Mobile plan 01: Repo layout).
- Adapters live in `digital/lib/app/analytics/adapters/`, one file per vendor. Only these files import vendor SDKs.
- One Riverpod provider builds the fan-out from an explicit list of adapters. Tests override it with a fake that records events.
- Screens and controllers call `ref.read(analyticsProvider).track(SomeEvent(...))`. No event bus is needed: a provider call is already decoupled.

```dart
// shared_lib/analytics/lib/src/analytics_event.dart
enum Sink { firebase, mixpanel, insider, appsFlyer, datadogRum }

abstract class AnalyticsEvent {
  const AnalyticsEvent();
  String get name;                       // legacy name, never renamed
  Map<String, Object?> get params => const {};
  Set<Sink> get sinks;                   // where this event goes today
}

// shared_lib/analytics/lib/src/analytics.dart
abstract interface class Analytics {
  void track(AnalyticsEvent event);
  void screen(String routeName);
  Future<void> identify(AnalyticsUser user);
  Future<void> setUserProperties(Map<String, Object?> props);
  Future<void> reset();                  // on logout
  AnalyticsContext get context;          // product, journey, form name
}

abstract interface class AnalyticsAdapter {
  Sink get sink;
  Future<void> track(AnalyticsEvent event, AnalyticsContext ctx);
  Future<void> screen(String routeName, {String? previous});
  Future<void> identify(AnalyticsUser user);
  Future<void> setUserProperties(Map<String, Object?> props);
  Future<void> reset();
}
```

```dart
// shared_lib/analytics/lib/src/events/loan_events.dart
final class ApplyLoanEvent extends AnalyticsEvent {
  const ApplyLoanEvent({this.assetInfo, this.assetYear, this.tenure});
  final String? assetInfo;
  final int? assetYear;
  final int? tenure;
  @override String get name => 'apply_loan';      // same as today
  @override Set<Sink> get sinks => const {Sink.firebase};
  @override Map<String, Object?> get params =>
      {'asset_info': assetInfo, 'asset_year': assetYear, 'tenure': tenure};
}
```

### Key design rules

- **Routing keeps today's behaviour.** A Firebase event today goes only to Firebase. A Mixpanel event goes to Mixpanel and Insider. Each event class declares its `sinks`, so the migration does not add new event volume to any vendor. Mixpanel bills per event, so this matters.
- **Naming stays per adapter.** The Mixpanel adapter keeps `name-action`. The Insider adapter keeps snake_case. The Firebase adapter keeps the current `product_name` mapping. That logic moves out of `analytics.dart` and `mixpanel_service.dart` unchanged.
- **One context.** `AnalyticsContext` holds `currentProduct`, the journey stack and `formName`. Today these live in two places (`Analytics.currentProduct` and `MixpanelService.currentProduct`). `AnalyticsProductMixin`, `FormStepperAwareMixin` and `TrackerJourneyManager` write to the context instead.
- **One router listener** sends `screen()` to all adapters. Today `analytics.dart` and `mixpanel_service.dart` each add one.
- **Auto-tracking stays.** `EventTracker` becomes an `AnalyticsEvent` subclass with `sinks = {mixpanel, insider}`. `TrackerComponentMixin` keeps building names from labels. The `Digital*` components call `analytics.track` instead of `MixpanelService.track`.

### What not to copy from Jago

- Platforms that register themselves in a static set from their constructor. Use an explicit list in a provider instead, so tests and flavors control it.
- Filtering platforms by `runtimeType.toString()`. With `--obfuscate` (which BFI uses) type names are scrambled. Use the `Sink` enum.
- An event bus plus a bloc just to forward events. Riverpod does not need it.
- A god package. The analytics package holds analytics only, not general utilities.

## Plan

1. **Freeze the names (1 PR).** Add `scripts/analytics/extract_event_names.sh`. It writes every Firebase name, Mixpanel event name and `TrackerJourney` code to `docs/analytics/event-names.golden.txt`. Commit the file. Check: the file has 148 Firebase names and 34 journey codes.
2. **Port package (1 PR).** Create `shared_lib/analytics` with `Analytics`, `AnalyticsAdapter`, `AnalyticsEvent`, `AnalyticsContext`, `AnalyticsUser` and a `FakeAnalytics` for tests. Pure Dart, 100% unit-tested. Check: `melos run analyze` passes; the package has no Flutter or vendor imports.
3. **Adapters and fan-out (1–2 PRs).** Add `FirebaseAdapter`, `MixpanelAdapter`, `InsiderAdapter`, `AppsFlyerAdapter` and `DatadogRumAdapter` in `digital/lib/app/analytics/adapters/`. Move logic out of `analytics.dart`, `mixpanel_service.dart` and `insider_service.dart` without changing it. Keep `Analytics.logEvent` and `MixpanelService.track` as thin shims that call the new provider. Check: adapter tests assert the exact name and parameters sent to a mocked SDK for one sample event per naming rule.
4. **CI ratchet (1 PR).** Add `scripts/analytics/check_direct_calls.sh` to `pr-pipeline.yml`. See "Done when" for the rules. Store the starting counts in `scripts/analytics/baseline.txt`. The job fails if any count goes up. Each migration PR lowers the baseline.
5. **Consent and PII guard (1 PR).** Add a `ConsentState` provider (default: granted, matching today). Adapters check it before sending. Pass the real value to Datadog instead of the hard-coded `TrackingConsent.granted`. Add a key denylist in the fan-out, matched on whole key words (`address`, `phone`, `nik`, `email`, `customer_name`, `income`), so `product_name` still passes. In debug it asserts. In release it drops the key and logs a warning. Check: a unit test sends a denied key and sees it dropped.
6. **Fix the known PII (1 PR, needs sign-off).** Remove `customer_address` from `apply_loan`, or replace it with city only. Agree with the dashboard owner first; this is the only planned change to an event. Review the 4 `requireTrackValue` fields with the data protection officer; bucket income and amount if they must stay.
7. **Move the components (1 PR).** `DigitalButton`, `DigitalTextField`, `DigitalSearchBar`, `DigitalBottomSheet` and `DigitalDialog` call `analytics.track`. This alone moves all automatic Mixpanel tracking. Check: golden names unchanged; widget tests use `FakeAnalytics`.
8. **Migrate Firebase calls, one feature per PR.** Order: small features first to prove the pattern (`account`, `payment_method`, `promo`, `pin`), then `home`, `auth`, `loan` last. For each feature add `<feature>_events.dart` to the catalogue and replace calls. Model the 8 runtime-built names as an event with an enum field that builds the same string. Check per PR: the golden file is unchanged; Firebase DebugView on the dev flavor shows the same names; the baseline goes down.
9. **Delete the shims (1 PR).** When the baseline for direct calls reaches 0, remove `Analytics.logEvent`, `MixpanelService.track` and `analytics.dart`. Make the CI counts strict (any match fails).
10. **Publish the catalogue (1 PR).** A script turns the event classes into `docs/analytics/event-catalogue.md`: name, sinks, parameters, owning feature, owner. Product analytics reviews new events in PRs that touch the catalogue (CODEOWNERS).
11. **Optional, later.** Send chosen journey milestones (for example `loan_submitted`) to AppsFlyer as conversion events and to Datadog RUM as actions. This is a product decision, done by adding a sink to the event class.

### CI check sketch (step 4)

```bash
# scripts/analytics/check_direct_calls.sh (ratchet: fail if a count goes up)
count() { grep -rE "$1" digital/lib --include='*.dart' \
  --exclude='*.g.dart' --exclude='*.freezed.dart' \
  | grep -v 'lib/app/analytics/adapters/' | wc -l | tr -d ' '; }
check() { now=$(count "$2"); max=$(grep "^$1=" scripts/analytics/baseline.txt | cut -d= -f2)
  [ "$now" -le "$max" ] || { echo "$1: $now > baseline $max"; exit 1; }; }
check firebase_log_event '\.logEvent\('
check mixpanel_track     'MixpanelService\.provider\)\.track\('
check sdk_imports        "import 'package:(firebase_analytics|mixpanel_flutter|flutter_insider|appsflyer_sdk)/"
```

## Done when

- 0 imports of `firebase_analytics`, `mixpanel_flutter`, `flutter_insider` or `appsflyer_sdk` outside `digital/lib/app/analytics/adapters/` and `main.dart`.
- 0 calls to `.logEvent(` or `MixpanelService.provider).track(` in `digital/lib`.
- 0 string literals passed as event names outside `shared_lib/analytics/lib/src/events/`.
- `event-names.golden.txt` is unchanged from step 1, except for changes approved in step 6.
- The CI job fails a PR that adds a direct SDK call or raises any baseline count.
- A unit test proves a denied parameter key never reaches an adapter.
- Datadog receives the real consent state, not a constant.
- Daily event counts in Firebase and Mixpanel for the top 20 events stay within normal range for 2 weeks after each feature moves.

## Effort and owner

- Size: **S–M** (from the parent table).
- About 3 sprints: sprint 1 for steps 1–5, sprints 2–3 for steps 6–10 in parallel with feature work.
- Owner: Customer Mobile Apps squad. Product analytics owns the catalogue review. The data protection officer signs off step 6.

## Depends on / related plans

- Mobile plan 01: Repo layout (where `shared_lib/analytics` sits).
- Mobile plan 03: State management (removing `appRef` from the `Digital*` components).
- Mobile plan 04: Dependency injection (provider wiring and overrides).
- Mobile plan 06: Logging and crashes (shares the PII denylist and sanitiser).
- Mobile plan 07: Feature flags (Mixpanel experiment exposure events move into the catalogue).
- Mobile plan 10: Design system (the `Digital*` components that auto-track).
- Mobile plan 12: Lint and guardrails (turns the grep ratchet into a lint rule).

## Risks

| Risk | Mitigation |
|---|---|
| A renamed event breaks a dashboard or funnel | Golden names file checked in CI; DebugView check per PR; count watch for 2 weeks |
| Migration doubles events during the switch | Shims forward to the new provider, so old and new paths never both send |
| Fan-out sends Firebase events to Mixpanel and raises cost | Each event declares `sinks`; default keeps today's routing |
| Label-based auto names change when copy changes | Already true today; catalogue lists auto names so copy edits are visible in review |
| Removing PII changes reports people rely on | Step 6 needs dashboard owner sign-off before merge |
| Consent wiring blocks events by mistake | Default stays "granted" until the consent screen exists; tests cover both states |
