## Goal

The HTTP layer is a set of small dio interceptors, each doing one job: headers, auth, token refresh, retry, trace IDs and error mapping. Token refresh is single-flight and proven by tests that fire many requests at once. Repositories keep calling the same `HttpClient` methods, so the 114 call sites do not change.

## Where we are today

Repo: `bravo-customer-app`, `master` @ `190e1d20`. Counts are from `lib/` folders without generated files.

### The client

- `data/customer/lib/src/http_client.dart` is **496** lines. It is one class that does everything.
- **114** HTTP calls in repositories go through it. 27 files in `data/customer/lib` use it. `HttpClient.provider` has 26 references.
- Public methods: `get`, `post`, `patch`, `put`, `delete`. Each takes the same flags: `checkDeviceIntegrity`, `skipAuthCheck`, `allowGuestReauthentication`, `isRestricted`, `timeoutOptions`, `responseType`.
- Flag use: `isRestricted: true` in 5 calls, `allowGuestReauthentication: true` in 7, `skipAuthCheck: true` in 2 (both inside the client, for the guest-authenticate and authorize calls).
- Default headers on every request: `accept`, `api-secret`, `x-app-platform`, `x-app-version`. Per request: `Authorization: Bearer ...` and, when asked, `x-integrity-id` from Play Integrity or App Attest.
- Timeouts: 30 s connect, send and receive. No retry anywhere in the data layer.

### Interceptors today

- `CertificatePinningInterceptor` (local package `http_certificate_pinning`), added when a fingerprint is configured.
- `ApiCallHistoryInterceptor` (`digital/lib/features/dev_mode/api_call_history.dart`), only in non-prod builds. It records status, trace ID and error bodies for the dev menu.
- Datadog RUM tracing is added outside dio, through `HttpOverrides` (`enableHttpTracking` in `main.dart`).

### Auth and refresh (inside the client, not interceptors)

- Before **every** authenticated request, `_clearSessionOnUnauthorized` calls `_refreshAuthorization`. That checks token expiry in `AuthService.refreshToken` (`data/customer/lib/src/auth/auth_service.dart`, 240 lines).
- `AuthService` uses one `Completer` so that callers arriving during a refresh wait for it. This is a single-flight lock, and it works for proactive refresh.
- On a 401 with error code `INVALID_KEY`, the client forces a refresh and retries once.
- **Race:** the forced refresh does not check which token the failed request sent. If several requests fail with the old token, and their 401s arrive after the first refresh has finished, each one starts a new forced refresh. Each refresh issues a new token, which can make the next in-flight request fail too.
- If refresh fails, the client clears the session. It then throws `SessionExpiredException`, or re-authenticates as a guest when `allowGuestReauthentication` is set.
- Restricted sessions (a short-lived token after PIN entry) use a separate token and deadline. A 401 there throws `RestrictedSessionExpiredException`.
- `DeviceIntegrityService` gets the client through a setter (`_deviceIntegrityService.httpClient = this`). The two classes depend on each other.

### Errors

- `_transformError` maps dio errors. Timeouts become `ConnectionTimeoutException`. Bad responses become `HttpStatusCodeException` with `statusCode`, parsed `ErrorResponse`, `x-trace-id` and `endpoint` (`'METHOD path'`). Socket and other errors are rethrown as is.
- `ErrorCode` (`shared_lib/core/lib/src/network/exception/error_code.dart`) has 30 values. `digital/lib` checks `ErrorCode.` 51 times.
- Every error response with a JSON body is also pushed to a global broadcast stream, `apiCallErrorEvent`. Its only consumer shows the "app update required" dialog (`app_screen.dart:70`).
- `toDioResponseType` maps `plain` and `stream` to JSON. No call site uses them, so this is dead code, not a live bug.

### Other dio instances

- `data/customer/lib/src/gcs_client.dart`: uploads to signed storage URLs, with its own error mapping.
- `data/customer/lib/src/common/common_repository.dart`: downloads bytes from a URL.
- Both create a bare `Dio`, which is correct for third-party URLs.

### Tests

- `data/customer/test/http_client_test.dart`: 1,534 lines, 41 tests. `auth_service_test.dart`: 33 tests.
- No test sends two requests at the same time through the refresh path.

## Target (what Jago does, adapted for BFI)

### Jago pattern

- `module_http/lib/network/http/http_client.dart` (825 lines) is also one big client. It has its own TODO to move to interceptors. So BFI should not copy its structure.
- What is worth copying is the **split by concern**, in three clients.
- `public_http_client.dart` serves calls without a session.
- `auth_http_client.dart` serves login and token calls.
- `digital_bank_client.dart` serves authenticated calls. It owns the auth and journey headers.
- `module_http/lib/exceptions/` has 18 exception classes in 18 files, under two bases (`ServerException`, `AppException`). They cover bad request, unauthorized, forbidden, not found, conflict, rate limit, server error, upgrade required, parsing and network failures. `utils/mapping_error_code.dart` maps them to messages.
- Every request carries a request ID header and a journey ID header (`network/journey/journey_id_utils.dart`), so backend logs can group calls by user journey.

### BFI shape

- Keep the `HttpClient` facade and its method signatures. Each flag becomes an entry in `Options.extra`, read by the matching interceptor.
- Two dio instances, built in one provider file.
- `authDio` has base headers, pinning and error mapping. It is used only for guest-authenticate and authorize. It has no auth or refresh interceptors, so a refresh can never call itself.
- `apiDio` serves everything else, with the full chain below.
- A `TokenRefresher` class owns the single-flight lock. It replaces the refresh logic split between `HttpClient` and `AuthService`.

| Order | Interceptor | Job |
|---|---|---|
| 1 | `CertificatePinningInterceptor` | Unchanged |
| 2 | `BaseHeadersInterceptor` | `accept`, `api-secret`, `x-app-platform`, `x-app-version`, new `x-request-id` (UUID per request) |
| 3 | `DeviceIntegrityInterceptor` | Adds `x-integrity-id` when `extra['checkDeviceIntegrity']` is true |
| 4 | `AuthInterceptor` | Proactive expiry check via `TokenRefresher`, then adds the normal or restricted bearer token; stores the token used in `extra` |
| 5 | `RefreshInterceptor` | On 401 `INVALID_KEY`: if the stored token differs from the current one, retry at once; else refresh once (single flight) and retry once |
| 6 | `RetryInterceptor` | Only GET and only connection errors or 502/503/504. Max 2 retries, backoff with jitter. Never retries POST, PATCH, PUT or DELETE |
| 7 | `ErrorMappingInterceptor` | Turns `DioException` into the typed exceptions; reads `x-trace-id`; reports "app update required" to a provider instead of a global stream |
| 8 | `ApiCallHistoryInterceptor` | Non-prod only, unchanged |

```dart
// data/customer/lib/src/network/token_refresher.dart
class TokenRefresher {
  TokenRefresher(this._auth, this._authApi);
  final AuthService _auth;
  final AuthApi _authApi;          // uses authDio
  Future<String>? _inFlight;

  /// Returns a fresh token. Concurrent callers share one refresh.
  Future<String> refresh({required String staleToken}) {
    return _inFlight ??= _doRefresh(staleToken)
        .whenComplete(() => _inFlight = null);
  }

  Future<String> _doRefresh(String staleToken) async {
    final current = await _auth.getAuthorizationToken();
    if (current.isNotEmpty && current != staleToken) return current; // already refreshed
    await _auth.refreshToken(authenticateGuest: _authApi.guest,
        authorize: _authApi.authorize, force: true);
    return _auth.getAuthorizationToken();
  }
}
```

### What not to copy from Jago

- The 825-line client and headers stored as mutable state on the client object. Use per-request interceptors.
- A long list of exception classes up front. Start from what BFI screens actually branch on: timeout, no network, session expired, restricted session expired, update required, and `HttpStatusCodeException` with `ErrorCode`. Add more only when a screen needs them.
- Do not adopt the journey ID header until the backend logs it. Ask the backend owners first.

## Plan

1. **Race tests first (1 PR, no production code).** Add tests to `http_client_test.dart` that fire 5 requests at once with an expired token, and 5 requests that all get 401 `INVALID_KEY`. Count refresh calls with a fake. Mark the 401 case as a known failure today. Check: the proactive case shows 1 refresh; the 401 case shows the current behaviour.
2. **Extract `TokenRefresher` (1 PR).** Move the refresh and stale-token check into `TokenRefresher`. `HttpClient` calls it. Check: the step 1 tests now show exactly 1 refresh for 5 concurrent 401s. All 41 existing tests still pass.
3. **Two dio instances (1 PR).** Build `authDio` and `apiDio` in `data/customer/lib/src/network/dio_provider.dart`. Guest-authenticate and authorize use `authDio`. Remove the `httpClient` setter cycle in `DeviceIntegrityService` by giving it `apiDio` through its provider. Check: login, guest start and PIN flows pass on the SIT flavor.
4. **Headers and integrity interceptors (1 PR).** Move base headers and `x-integrity-id` into interceptors 2 and 3. Add `x-request-id`. Check: a dev-menu API history entry shows all headers; backend logs show the request ID (confirm with SRE).
5. **Auth and refresh interceptors (1 PR).** Move `_authorizationToken`, `_clearSessionOnUnauthorized` and `_restrictedRequest` into interceptors 4 and 5. `HttpClient._request` shrinks to building `Options` and calling `apiDio`. Check: all refresh and restricted-session tests pass, now against the interceptors.
6. **Error mapping interceptor (1 PR).** Move `_transformError` into interceptor 7. Replace the global `apiCallErrorEvent` with an `appUpdateRequiredProvider` that `app_controller.dart` listens to. Remove the unused `plain` and `stream` response types. Check: the "app update required" dialog still appears for that error code (widget test).
7. **Retry interceptor (1 PR).** Add retry for idempotent GETs only. Log each retry at `info` through Mobile plan 06: Logging and crashes. Check: unit tests show a GET is retried twice on 503 and a POST is never retried.
8. **Trace headers (1 PR, after the spike in Mobile plan 06: Logging and crashes).** If the spike finds gaps, add tracing header types in the Datadog first-party host config. Do not hand-write Datadog headers in an interceptor. Check: a RUM resource in Datadog links to its APM trace.
9. **Shrink the facade (1 PR).** `HttpClient` keeps only `get/post/patch/put/delete`. Target: under 150 lines. Check: `wc -l` and the CI job.

### Refresh race tests (must exist before step 5 merges)

- 5 concurrent requests, token expired before sending: exactly 1 refresh, 5 successes.
- 5 concurrent requests, all get 401 `INVALID_KEY`: exactly 1 refresh, each request retried once.
- A late 401 that carries the old token after a refresh finished: no new refresh, retried with the current token.
- Refresh fails with `INVALID_KEY`: session cleared once, all 5 callers get `SessionExpiredException`.
- Same with `allowGuestReauthentication`: one guest login, all callers retried.
- Restricted request with expired restricted token: `RestrictedSessionExpiredException`, normal token untouched.
- Refresh in flight while the user logs out: no token is saved after logout.

## Done when

- `http_client.dart` is under 150 lines. No auth, refresh or error logic is left in it.
- Each interceptor has its own test file. The 7 race tests above pass in CI.
- `authDio` has no auth or refresh interceptor (checked by a unit test on the interceptor list).
- No POST, PATCH, PUT or DELETE is ever retried (unit test).
- `apiCallErrorEvent` and the `httpClient` setter on `DeviceIntegrityService` are gone.
- Every request carries `x-request-id`. Every `HttpStatusCodeException` carries `traceId` when the server sent one.
- The 114 repository call sites are unchanged, apart from imports.

## Effort and owner

- Size: **S** (from the parent table). The race tests and refresh change carry most of the risk.
- About 1–2 sprints. Steps 1–3 in sprint 1, steps 4–9 in sprint 2.
- Owner: Customer Mobile Apps squad. SRE confirms that `x-request-id` reaches backend logs (step 4).

## Depends on / related plans

- Mobile plan 02: Layering (repositories map API models to domain types on top of this client).
- Mobile plan 04: Dependency injection (dio instances and interceptors as providers).
- Mobile plan 06: Logging and crashes (trace IDs, retry logs, RUM-to-APM spike).
- Mobile plan 09: Security (pinning, `api-secret`, integrity headers).
- Mobile plan 11: Testing (race tests and interceptor tests).

## Risks

| Risk | Mitigation |
|---|---|
| Refresh change logs users out by mistake | Race tests first (step 1); release behind a Remote Config kill switch that falls back to the old path for one release |
| Interceptor order bug sends a request without a token | Unit test asserts the interceptor order; SIT smoke test of login, KYC and loan submit |
| Retry repeats a payment or submission | Retry only GET; tested in step 7 |
| `x-request-id` rejected by the gateway or WAF | Check with SRE on SIT before prod |
| Pinning behaves differently on `authDio` | Both instances get the same pinning interceptor; tested on a prod-like build |
| Datadog tracing stops after moving clients | Tracing stays in `HttpOverrides`, not in dio; check RUM resources after each step |
