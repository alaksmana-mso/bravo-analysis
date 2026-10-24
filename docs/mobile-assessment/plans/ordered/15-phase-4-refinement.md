## Summary

This page prepares Phase 4 of the mobile roadmap ("Network chain behind a switch flag") for refinement. It covers all 10 steps: what is true today, what to do, acceptance criteria, who is needed, size, risks, 3 options with a recommendation, and questions for the session.

* **Epic:** not created yet. Suggested title: "[Tech x DK] Mobile App Improvement - Network Chain".
* **Parent:** Mobile roadmap: step by step, section "Phase 4: Network chain behind a switch flag". Plan page: Mobile plan 07: Networking.
* **Facts checked on 24 Oct 2026** against `bfi-finance/bravo-customer-app` `master` @ `56edae4` (23 Oct).

**What Phase 4 is.** The whole HTTP path (auth, token refresh, headers, error mapping, retry) moves out of one 565-line class into small dio interceptors. The new chain sits behind **one** switch flag, `useNewHttpChain`, default old. The facade `HttpClient` picks the chain, so the 117 repository call sites do not change. It is the first class C change in the roadmap, and it touches every logged-in user, which is why it has its own phase.

### Four facts that shape Phase 4

**1. The token-refresh race is real and unguarded.** `http_client.dart` (565 lines, up from 496 when plan 07 was written) refreshes in `_refreshAuthorization` and `_refreshAsGuest` (lines 328–391). There is no `Completer`, lock or queue. Several requests that get a 401 at the same time each start their own refresh. Dio 5.9.1 (what the app uses) ships `QueuedInterceptor` for exactly this. The common fix is a single in-flight refresh that later 401s wait on, with a separate dio instance for the refresh call so it cannot loop.

**2. One dio instance serves everything.** Only test files create a second `Dio()`. `DeviceIntegrityService` gets the client through a setter (`line 50`), which is the cycle plan 07 describes. Interceptors are added at lines 40–46 from `NetworkConfig.interceptors` (dev-mode API history in non-prod).

**3. No request ID yet.** 0 occurrences of `x-request-id` in the data and core packages. The backend standard (set 12–13 Oct 2026) is a gateway-minted `x-bfi-req-id`. So the app should **not** mint its own header name. It should either send nothing and read the gateway's ID back, or send `x-bfi-req-id` only if SRE confirms the gateway accepts a client value. This is class E and needs that answer first (Q1).

**4. Error mapping and the global event.** `apiCallErrorEvent` is a top-level stream (line 14) read in 4 places in the app. `HttpResponseType.plain` and `.stream` exist (lines 521–543). The plan removes the unused types and replaces the global event with a provider.

Other counts: 25 repository files use `HttpClient`, 117 `_httpClient.get/post/put/patch/delete` calls (plan said 114), 46 tests in `http_client_test.dart` (41 when the plan was written), race tests from Phase 1 step 1.15 are a precondition.

## Steps at a glance

Sizes: **XS** = under half a day, **S** = 1–2 days, **M** = 3–5 days. Class **C** = behind `useNewHttpChain`, **E** = backend-coupled, **B** = same behaviour.

| # | Proposed ticket title | Today (23 Oct) | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1 | `feat(network): useNewHttpChain switch flag and facade selector` | No flag | C | Mobile engineer | S | 2.12 | | |
| 4.2 | `feat(network): TokenRefresher with single-flight refresh` | No lock; each 401 refreshes | C | Mobile engineer | M | 1.15 | | |
| 4.3 | `feat(network): authDio and apiDio, remove the integrity setter cycle` | One dio, setter at line 50 | C | Mobile engineer | S | 4.2 | | |
| 4.4 | `feat(network): Header and integrity interceptors` | Headers built in the client | C (+E for the request ID) | Mobile engineer | S | Q1 | | |
| 4.5 | `feat(network): Auth and refresh interceptors` | In `_request` | C | Mobile engineer | M | 4.2, 4.3 | | |
| 4.6 | `feat(network): Error-mapping interceptor, appUpdateRequiredProvider` | `_transformError`, global stream | C | Mobile engineer | S | 4.5 | | |
| 4.7 | `feat(network): Retry interceptor for idempotent GETs` | No retry | C (approved delta) | Mobile engineer | S | 4.6 | | |
| 4.8 | `feat(network): Trace headers (only if the 1.25 spike found gaps)` | Datadog headers only | C + E | Mobile engineer + SRE | S | 1.25 | | |
| 4.9 | Cohort rollout of `useNewHttpChain` 1% → 10% → 50% → 100% | – | C | Feature owner + on-call | 2–4 weeks | 2.23, 2.24 | | |
| 4.10 | `refactor(network): Delete the old request path, shrink HttpClient` | 565 lines | B | Mobile engineer | S | 4.9 | | |

**Suggested order.** Sprint 1: 4.1, 4.2, 4.3. Sprint 2: 4.4, 4.5, 4.6. Sprint 3: 4.7, 4.8, both-paths tests green, release with the flag off. Then 4.9 over 2–4 weeks. Then 4.10 after 2 releases at 100%.

## Definition of ready for every Phase 4 ticket

* The ticket links to this page and to the Phase 4 epic.
* Each class C ticket states which existing tests run on both paths and which of the 1.15 race tests target the new path.
* Contract replay (fixtures from 1.13) is listed as an acceptance criterion for every interceptor ticket.
* No ticket changes a repository call site. If one must, it is a separate class B ticket.

## Step 4.1: Switch flag and facade selector

**Today.** No flag. `HttpClient._request` does everything.

**Tasks.** Add `useNewHttpChain` to the flag catalogue (owner, removal date, default old, real-time). `HttpClient` reads the flag once per request and routes to the old code or the new chain. Add `x-bfi-chain: new` only on SIT and UAT builds so QA can see which path served a request in the dev-mode API history.

**Acceptance criteria.** With the flag off, all 46 existing tests pass unchanged. With the flag on and no interceptors yet, the chain falls back to old behaviour (no-op), so both paths are identical on day one.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One flag for the whole chain, read per request | One kill switch, one cohort to watch | All-or-nothing: a bug in retry turns off the refresh fix too |
| B. One flag per interceptor | Fine-grained | 6 flags, 6 cohorts, mixed states nobody has tested |
| C. No flag, ship the chain in one release | Simplest code | A refresh bug logs out every user at once; the parent page's rules forbid it |

**Recommended: A.**

## Step 4.2: `TokenRefresher` with single-flight refresh

**Today.** `_refreshAuthorization` (line 358) and `_refreshAsGuest` (line 391) run per caller. The 1.15 race tests show 5 parallel 401s cause 5 refreshes.

**Tasks.** Extract `TokenRefresher`: one in-flight refresh at a time (a shared `Future`), a timeout (10 s), a terminal rule (a 401 from the refresh endpoint ends the session), and a one-retry guard on the original request. The old path keeps calling the old code.

**Acceptance criteria.** The 1.15 tests show exactly 1 refresh for 5 parallel 401s and for 5 parallel expired-token requests on the new path. A refresh that itself returns 401 fails all waiters with the original error and clears the session once.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Own `TokenRefresher` with a shared future, used by a `QueuedInterceptor` (4.5) | Exact behaviour we need, 40 lines, fully tested | We maintain it |
| B. A pub.dev package (`dio_single_flight`, `dio_bearer`, `dio_auto_pilot`) | Ready-made | Small packages, each with its own session model; guest re-authentication is BFI-specific |
| C. Serialise all requests through one queue | Removes the race | Every request waits on every other; latency for the whole app |

**Recommended: A.**

## Step 4.3: Two dio instances

**Today.** One instance. `DeviceIntegrityService` receives the client through a setter, so the client and the integrity service depend on each other.

**Tasks.** `authDio` (no auth interceptor; used for guest-authenticate, authorize, refresh) and `apiDio` (full chain) in `data/customer/lib/src/network/dio_provider.dart`. Give `DeviceIntegrityService` `apiDio` through its provider and delete the setter.

**Acceptance criteria.** Login, guest start and PIN flows pass on SIT with the flag on. The setter is gone. Wiring test (2.15) lists both dio providers.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Two instances, refresh on `authDio` | Standard pattern: the refresh call can never loop through the auth interceptor | Two base configurations to keep in step (share a builder) |
| B. One instance, skip-auth flag on refresh requests | One config | Easy to forget the flag; the loop risk stays |
| C. Three instances (auth, api, upload) | Upload gets its own timeouts | More than needed now; add later if uploads need it |

**Recommended: A.**

## Step 4.4: Header and integrity interceptors, and the request ID question

**Today.** Base headers (`api-secret`, version, platform) and `x-integrity-id` are built inside the client. No request ID. Backend standard: gateway-minted `x-bfi-req-id`, span tag `request_id`.

**Tasks.** Interceptor 2 adds base headers. Interceptor 3 adds `x-integrity-id`. For the request ID: **ask SRE first (Q1)**. If the gateway accepts a client-supplied `x-bfi-req-id`, send one (UUID per request) and log it with the response. If not, read the gateway's `x-bfi-req-id` from the response and log that. Never invent a different header name.

**Acceptance criteria.** Contract replay: identical requests on both paths, except the approved request-ID header. A dev-menu API history entry shows all headers. One request can be found in the backend logs by its ID (confirm with SRE).

**Who / size.** One mobile engineer. S. The request-ID part is class E.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Read the gateway's `x-bfi-req-id` from the response, log it on errors and in RUM | No backend change. Follows the standard | The ID exists only after the response; a request that never returns has no ID |
| B. Send a client `x-bfi-req-id` if the gateway honours it | One ID from tap to database | Needs gateway confirmation; a spoofable client value must be treated as a hint, not a key |
| C. Send our own `x-request-id` as plan 07 wrote | Simple | Two ID schemes in the estate. Against the 13 Oct standard |

**Recommended: A now**, B if SRE confirms the gateway passes a client value through.

## Step 4.5: Auth and refresh interceptors

**Today.** `_authorizationToken`, `_clearSessionOnUnauthorized`, `_restrictedRequest` live in `_request`.

**Tasks.** Interceptor 4 attaches the token. Interceptor 5 is a `QueuedInterceptor` that, on 401 `INVALID_KEY`, calls `TokenRefresher` and retries once; on a refresh failure it clears the session once. `_request` shrinks to building `Options` and calling `apiDio`.

**Acceptance criteria.** All refresh and restricted-session tests pass against the interceptors (flag on). Both-paths test helper (2.20) runs the auth tests twice. Contract replay identical.

**Who / size.** One mobile engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `QueuedInterceptor` + `TokenRefresher` | Dio's own queuing stops concurrent handlers from racing; the refresher stops concurrent refreshes | Two mechanisms; document why both exist |
| B. `InterceptorsWrapper` with manual locking | Familiar | The pattern most tutorials copy, and the one that fires 5 refreshes under load |
| C. Refresh proactively on a timer before expiry, no 401 handling | Fewer 401s | A 401 still happens (revoked token, clock skew); it must be handled |

**Recommended: A**, with proactive refresh kept as it is today.

## Step 4.6: Error-mapping interceptor and `appUpdateRequiredProvider`

**Today.** `_transformError` maps errors to typed exceptions with `x-trace-id`. `apiCallErrorEvent` is a global stream used in 4 places (the "app update required" dialog among them). `plain` and `stream` response types exist.

**Tasks.** Interceptor 7 maps errors. Replace the global stream with `appUpdateRequiredProvider` that `app_controller.dart` listens to. Remove the unused `plain` and `stream` types (approved delta: dead code).

**Acceptance criteria.** Widget test: the "app update required" dialog still appears for that error code on both paths. Typed exceptions and `x-trace-id` identical in contract replay.

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Interceptor + provider, old stream kept as a shim until 4.10 | No call-site change now | Two signals for one event until the delete |
| B. Interceptor, and move the 4 listeners now | Clean | 4 app files change in a network ticket; still small |
| C. Keep the global stream | No work | A global the DI plan (Phase 2) wants gone |

**Recommended: B** (the 4 listeners are small and the provider is the end state).

## Step 4.7: Retry interceptor for idempotent GETs

**Today.** No retry.

**Tasks.** Retry GET only, on 502, 503, 504 and connection errors, 2 attempts with backoff, never on POST, PUT, PATCH, DELETE. Log each retry at `info` through the `Monitoring` port.

**Acceptance criteria.** Unit tests: a GET is retried twice on 503, a POST is never retried, a GET with a body is not retried. Approved delta recorded (retries change what the backend sees).

**Who / size.** One mobile engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. GET-only retry, 2 attempts, backoff, through our interceptor | Safe by construction | Some GETs are heavy (document downloads); allow an opt-out option |
| B. `dio_smart_retry` package | Ready-made, configurable | Retries by status by default; must be restricted to GET |
| C. No retry | No duplicate risk | Users keep seeing transient 503s as errors |

**Recommended: A.**

## Step 4.8: Trace headers, only if the 1.25 spike found gaps

**Today.** `firstPartyHosts` sends Datadog-format headers to the API host and the KrakenD host. The SDK also supports W3C `tracecontext` and B3 through `firstPartyHostsWithTracingHeaders`. Whether RUM resources link to APM traces through KrakenD and Istio is the Phase 1 spike (1.25).

**Tasks.** If the spike found gaps: add `TracingHeaderType.tracecontext` next to `datadog` for both hosts in the Datadog configuration. Do not hand-write tracing headers in an interceptor. If SRE needs the gateway to forward headers, that is their ticket.

**Acceptance criteria.** A RUM resource in Datadog links to its APM trace for both hosts. Contract replay ignores tracing headers (approved).

**Who / size.** One mobile engineer + SRE. S. Class C + E.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. `tracecontext` + `datadog` header types in the SDK config | SDK does the sampling and formatting | A gateway that strips unknown headers still breaks it; SRE check needed |
| B. Hand-written headers in an interceptor | Full control | Duplicates the SDK, easy to get sampling wrong |
| C. Do nothing, rely on `x-trace-id` from responses | No work | Only errors carry it; no RUM-to-APM link |

**Recommended: A**, only if 1.25 says so.

## Step 4.9: Cohort rollout of `useNewHttpChain`

**Today.** The cohort dashboard (2.23) and kill-switch runbook (2.24) exist after Phase 2.

**Tasks.** Rehearse the kill switch in SIT. Roll out 1% → 10% → 50% → 100%, one day of data per stage, no Play rollout dial moved in the same week. Watch: HTTP error rate, session-expired count (logouts), p75 screen load, refresh calls per session, by flag value.

**Acceptance criteria.** Each stage noted in the ledger with its dashboard result. Logouts per session on the new path are at or below the old path. No stage flipped back, or the flip and fix are recorded.

**Who / size.** Feature owner + mobile on-call. 2–4 weeks of calendar time.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Four stages, one day each minimum, human go or no-go | Matches the parent page's loop | 2–4 weeks |
| B. Two stages (10%, 100%) | Faster | 10% to 100% is a big jump for a change that touches every request |
| C. Internal testers only, then 100% | Fast | Testers do not have the long tail of devices and networks |

**Recommended: A.**

## Step 4.10: Delete the old path, shrink `HttpClient`

**Today.** 565 lines.

**Tasks.** After 2 releases at 100% with no regression: delete the old request code, the flag, and the old-path tests. `HttpClient` keeps `get`, `post`, `put`, `patch`, `delete` and the response mapping only. Target under 150 lines. Delete the Remote Config key one release later.

**Acceptance criteria.** `wc -l` under 150. No reference to `useNewHttpChain`. All 25 repository files unchanged. CI job asserts the line count.

**Who / size.** One mobile engineer. S. Class B.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete in one PR after the gate | Clean end state | One larger PR to review |
| B. Delete piece by piece over several PRs | Small reviews | The flag lingers; the catalogue test (2.12) would flag an overdue removal date anyway |
| C. Keep the old path "just in case" | None | Two code paths forever; the parent page says a feature has parity only when the old path is gone |

**Recommended: A.**

## Exit gate for Phase 4

* `useNewHttpChain` at 100% for 2 releases with no regression in HTTP error rate, logouts per session or screen load.
* Old request code and the flag deleted. `HttpClient` under 150 lines.
* Exactly 1 refresh per burst of parallel 401s, proven by the race tests and by the refresh-calls-per-session metric in prod.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Does KrakenD accept a client-supplied `x-bfi-req-id`, or does it always mint its own? | SRE | |
| Q2 | Which endpoints are safe to retry on GET, and are any GETs too heavy to retry (documents)? | BFF team | |
| Q3 | What is the acceptable "logouts per session" threshold for the cohort check? | Product + squad lead | |
| Q4 | Did the 1.25 spike find a RUM-to-APM gap? Which host? | Mobile engineer + SRE | |
| Q5 | Who is the feature owner of `useNewHttpChain` (named in the flag catalogue)? | Squad lead | |
| Q6 | Epic for Phase 4: one epic with 10 tickets? | Samuel | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Client size and refresh code | `data/customer/lib/src/http_client.dart`: 565 lines; `_refreshAuthorization` line 358, `_refreshAsGuest` line 391; no `Completer` |
| Interceptors and setter | lines 40–46; `device_integrity_service.dart` line 50 |
| Request ID | `grep -ri x-request-id data shared_lib`: 0 |
| Global error stream | `http_client.dart` line 14; 4 uses in `digital/lib` |
| Call sites and tests | 25 repository files, 117 calls, 46 tests |
| dio version | `pubspec.lock`: dio 5.9.1 |
| Backend request-ID standard | Request-id chain decision, 12–13 Oct 2026 (`x-bfi-req-id`, gateway-minted) |

## Sources for the recommendations

* Dio `QueuedInterceptor` and the refresh race: [Your Dio interceptor is swallowing 401s](https://blog.devgenius.io/your-dio-interceptor-is-swallowing-401s-heres-the-race-condition-10ae0e93e728), [dio_bearer docs](https://pub-web-s1.flutter-io.cn/documentation/dio_bearer/0.0.2) (separate refresh client, terminal 401), [dio_single_flight](https://pub.dev/packages/dio_single_flight).
* Datadog, [Flutter advanced configuration](https://docs.datadoghq.com/real_user_monitoring/application_monitoring/flutter/advanced_configuration/): `firstPartyHostsWithTracingHeaders`, `TracingHeaderType`.
* Mobile plan 07: Networking (BFI shape, interceptor order, race tests).
