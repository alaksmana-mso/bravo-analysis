## Goal

Every log line and crash report goes through one BFI `Monitoring` interface. A PII cleaner runs before anything leaves the device. Each error carries the backend trace ID, so support can jump from a crash or a log line to the matching backend trace.

## Where we are today

Repo: `bravo-customer-app`, `master` @ `190e1d20`. Counts are from `lib/` folders only, without generated files.

### DatadogLog

- `shared_lib/core/lib/src/utils/datadog_log.dart` (195 lines). A static class with `error`, `warn` and `debug`. There is no `info` level.
- **38** direct calls in **19** files: 32 `error`, 6 `warn`, 0 `debug`.
- **35 of the 38** put the raw error text into the message (`'...: $error'` or `error.toString()`).
- `guardLog(...)` wraps a future and logs any failure. It has **131** call sites.
- `DatadogLogObserver` (same file) is a Riverpod `ProviderObserver`. It logs every provider that ends in an error, using `error.toString()`.
- Level rule (`_shouldLogAsError`): HTTP 5xx is `error`. HTTP 4xx, timeouts, socket errors and session expiry are `warn`.
- The parent page says "90 uses". That count includes test files. In `lib/` there are 59 mentions.

### Crashlytics

- Wired only in `digital/lib/main.dart` (`_initializeCrashlytics`).
- `DatadogLog.errorReporter` is set there. `error` becomes a non-fatal `recordError`. `warn` becomes a Crashlytics breadcrumb (`crashlytics.log`).
- `FlutterError.onError` and `PlatformDispatcher.instance.onError` are chained to Crashlytics. Platform errors are recorded as fatal.
- Collection is always on. Custom keys: `flavor`, `app_version`.
- Before each report it sets `trace_id`, `session_id` and `endpoint` as **global** custom keys. Two errors close together can overwrite each other's keys.
- No user ID is set in Crashlytics or in Datadog.

### Trace IDs

- `data/customer/lib/src/http_client.dart:421` reads `x-trace-id` from error responses and stores it in `HttpStatusCodeException`.
- `DatadogLog.error` receives `traceId` and `endpoint`, but only passes them to Crashlytics. The Datadog log line itself does not carry them (`_logger?.error(message, errorMessage: ..., errorStackTrace: ...)`).
- `support_identifier.dart` shows the trace ID, or else the Datadog session ID, to the user in `DigitalDialog`, so support can look it up.
- Datadog RUM HTTP tracking is on (`enableHttpTracking`, `datadog_tracking_http_client`). First-party hosts are the API host and the KrakenD host. Trace sampling comes from the `DATADOG_TRACE_SAMPLE_RATE` dart-define.
- HTTP tracking is skipped when an HTTP proxy override is active (`main.dart:39`), so proxy-enabled test builds send no RUM resources.

### PII risk

- Nothing cleans messages, errors or attributes before they leave the device.
- `HttpStatusCodeException.toString()` prints only the status code, which is safe.
- Other errors are not safe. A `FormatException` from JSON parsing includes part of the source text, which can be a response body with customer data. `DatadogLogObserver` and most `DatadogLog` calls send that text as is.

## Target (what Jago does, adapted for BFI)

### Jago pattern

- `module_common/lib/monitoring/monitoring.dart` (63 lines): a `Monitoring` class that fans out to a list of `MonitoringPlatform`s. It keeps only platforms that say they are enabled.
- `monitoring/platform/monitoring_platform.dart`: the interface. Methods: `setup`, `identify`, `reportError`, `reportFlutterError`, `forwardLog(level, message, error, stackTrace, attributes)`.
- Two platforms: `crashlytics_platform.dart` and `datadog_platform.dart`, each under 40 lines.
- `module_common/lib/observability/jago_observability_sanitizer.dart` (98 lines). It flattens nested attributes, then redacts the message, the error and every string attribute.
- The redaction patterns live in `module_common/lib/datadog/datadog_utils.dart`. There is a fixed list (phone, KTP, NPWP, address, mother's maiden name, PIN button, bank name) plus extra patterns loaded from Remote Config.
- The sanitizer has its own tests (`module_common/test/observability/`).

### BFI shape

- A `Monitoring` port in `shared_lib/core` (pure Dart). `DatadogLog` stays as the static entry point for now, but its body calls the port. This keeps all 38 call sites and 131 `guardLog` sites working.
- Two adapters: `DatadogMonitoringAdapter` and `CrashlyticsMonitoringAdapter`. Both run every event through one `PiiSanitizer` first.
- The sanitizer is BFI's own. Write the patterns from BFI's data: NIK (16 digits), phone (`+62` / `08`), email, NPWP, bank account numbers, address fields, plus the field names that appear in BFI JSON. Do not copy Jago's regexes.
- Trace ID and endpoint travel as per-event attributes, never as global keys.

```dart
// shared_lib/core/lib/src/monitoring/monitoring.dart
enum LogLevel { debug, info, warn, error }

class LogEvent {
  const LogEvent(this.level, this.message,
      {this.error, this.stackTrace, this.traceId, this.endpoint,
       this.attributes = const {}});
  final LogLevel level; final String message;
  final Object? error; final StackTrace? stackTrace;
  final String? traceId; final String? endpoint;
  final Map<String, Object?> attributes;
}

abstract interface class MonitoringAdapter {
  bool get isEnabled;
  void log(LogEvent event);                 // already sanitised
  void recordError(Object error, StackTrace? st, {required bool fatal,
      Map<String, Object?> attributes});
  void identify(String pseudonymousId);
}

abstract interface class PiiSanitizer {
  LogEvent clean(LogEvent event);           // message, error text, attributes
}
```

### Log levels (one meaning each)

| Level | Use for | Sent to |
|---|---|---|
| debug | Developer detail | Device console only |
| info | Business milestones (loan submitted, KYC done) | Datadog logs |
| warn | Expected failures (4xx, timeout, no network, session expired) | Datadog logs + Crashlytics breadcrumb |
| error | Unexpected failures (5xx, parse errors, bugs) | Datadog logs + Crashlytics non-fatal |

### What not to copy from Jago

- A separate "observability component" behind a feature flag next to the old path. BFI has one path today; keep one.
- Remote-config redaction patterns as the only defence. They help, but the fixed list must work on its own and be unit-tested.
- Jago's regex list itself. Its data shapes are not BFI's.

## Plan

1. **Sanitiser with tests (1 PR).** Add `PiiSanitizer` in `shared_lib/core/lib/src/monitoring/`. Cover NIK, phone, email, NPWP, account numbers, and JSON keys such as `name`, `address`, `mother_name`, `phone`, `nik`. Add a test file with real-shaped (fake) samples, including a `FormatException` that holds a JSON body. Check: tests pass; coverage of the sanitiser is 100%.
2. **Monitoring port behind DatadogLog (1 PR).** Add `Monitoring`, `MonitoringAdapter` and the two adapters. Change the body of `DatadogLog.error/warn/debug` to build a `LogEvent` and call `Monitoring`. Keep the public signatures. Add `DatadogLog.info`. Check: the existing `datadog_log_test.dart` still passes; a new test shows a phone number in a message arrives redacted at both adapters.
3. **Trace ID on every log line (same or next PR).** Send `trace_id` and `endpoint` as Datadog log attributes. Stop setting them as global Crashlytics keys; pass them in the `recordError` call instead (`information:` list or a per-call key set). Check: in Datadog Logs, filter `@trace_id:*` and see values on HTTP errors.
4. **Move crash hooks out of main.dart (1 PR).** Move `FlutterError.onError`, `PlatformDispatcher.onError` and the Crashlytics setup into `CrashlyticsMonitoringAdapter.setup()`. `main.dart` calls one `Monitoring.setup()`. Check: a debug-menu "test crash" button still shows up in Crashlytics for the dev flavor.
5. **Pseudonymous user ID (1 PR).** Call `identify(customerId)` on login and clear it on logout, for both Crashlytics and Datadog (`setUserInfo` with ID only, no name or phone). Agree with the data protection officer first. Check: a crash in dev shows the customer ID and nothing else about the user.
6. **Clean the call sites (1–2 PRs).** Replace `'...: $error'` messages with a fixed message plus `error:` as a field, so the sanitiser sees the error separately. Start with the 35 known sites. Check: `grep` finds 0 `DatadogLog.(error|warn)(` calls with `$error`, `$e` or `toString()` in the message.
7. **Check RUM-to-APM linking (1 spike, no code if it works).** Take one prod RUM session with a failed request. Confirm the RUM resource links to an APM trace, and that the `x-trace-id` response header matches that APM trace ID. Check whether KrakenD and Istio pass the tracing headers through. Record the answer on this page.
8. **Fix linking gaps if step 7 finds any (1 PR each).** Options: add W3C `tracecontext` header types next to Datadog headers in `DatadogConfiguration.firstPartyHostsWithTracingHeaders`; ask SRE to forward headers at the gateway; ask backend owners to return the Datadog trace ID in `x-trace-id`.
9. **Remote log threshold and sampling (1 PR).** Set the Datadog logger's remote threshold to `info` in prod and `debug` in dev. Keep RUM sampling in dart-defines, but write the agreed prod values on this page.
10. **Ratchet against new direct calls (1 PR).** Add to the CI script from Mobile plan 05: Analytics wrapper. Count imports of `firebase_crashlytics` and `DatadogSdk.instance.logs` outside the adapters. Fail if the count goes up.

## Done when

- A unit test proves that NIK, phone, email and a JSON body with `name` and `address` are redacted before any adapter receives them.
- 0 imports of `firebase_crashlytics` outside `CrashlyticsMonitoringAdapter`.
- 0 `DatadogLog.error/warn` calls with raw error text inside the message string.
- Every HTTP error log in Datadog has `@trace_id` and `@endpoint` attributes.
- Crashlytics no longer uses global custom keys for `trace_id`, `session_id` or `endpoint`.
- Step 7 is written up: either "RUM resources link to APM traces" or a list of fixes with owners.
- A weekly Datadog Logs query for the PII patterns over mobile logs returns 0 hits.

## Effort and owner

- Size: **S** (from the parent table).
- About 1–1.5 sprints. Steps 1–4 fit in one sprint. Step 7 needs a few hours with Datadog access.
- Owner: Customer Mobile Apps squad. SRE helps with step 7 and step 8 (gateway headers). The data protection officer approves step 5.

## Depends on / related plans

- Mobile plan 05: Analytics wrapper (shares the PII denylist and the CI ratchet script).
- Mobile plan 08: Networking (the trace-header interceptor and the typed errors that carry `traceId`).
- Mobile plan 09: Security (PII handling rules and data protection sign-off).
- Mobile plan 03: State management (`DatadogLogObserver` keeps working after the move to `Notifier`).
- Mobile plan 11: Testing (sanitiser tests and crash-hook tests).

## Risks

| Risk | Mitigation |
|---|---|
| Sanitiser misses a new data shape | Unit tests per pattern; weekly Datadog query for PII patterns; add patterns as found |
| Sanitiser over-redacts and hides the real error | Keep error type, endpoint and trace ID unredacted; test with real error samples |
| Regex cost on every log line slows the app | Run only on warn and error; benchmark in a unit test with a 10 KB body |
| Moving crash hooks loses early startup crashes | Call `Monitoring.setup()` at the same point as today, before `runApp` |
| Adding a user ID raises privacy concerns | ID only, no name or phone; sign-off before merge |
| Trace IDs do not match APM | Step 7 checks first; step 8 lists fixes per owner |
