## Summary

Phase 4 of the agency apps roadmap ("Network chain behind a switch flag") for the whole `bravo-agency-app` monorepo. Linked from GENFI roadmap: step by step and SQUARE roadmap: step by step. It covers the 8 steps: what is true today, what to do, acceptance criteria, owner and size, 3 options with a recommendation, questions.

* **Epic:** not created yet. Suggested: "[Tech x DK] Agency Apps Improvement - Network Chain".
* **Plan pages:** GENFI plan 05: Networking steps 3–6 (and SQUARE plan 06). Step 1 (characterisation tests) is Phase 1 step 1.12; step 2 (the chain in `core`) is Phase 2 step 2.11.
* **Facts checked on 24 Oct 2026** against `bravo-agency-app` `master` @ `1e50b819`.

**What Phase 4 is.** The six auth decorators (1,508 lines) are replaced by one interceptor chain in `shared_lib/core`, built and tested in Phase 2. Each app switches to it behind **one** switch flag, `useInterceptorClient`, default old, one app at a time: GENFI first (the largest app and the simplest auth, OTP), then SQUARE (Keycloak), then MY BISPRO. Repositories keep calling `HttpClient`; nothing above the client changes.

### Four facts that shape Phase 4

**1. Six decorators, three behaviours on 401.**

| Class | Package | Lines | On 401 |
| --- | --- | --- | --- |
| `OtpHttpClient` | `agent_marketing` | 264 | refresh once, retry once (single-flight guard) |
| `AgentMarketingKeycloakHttpClient` | `agent_marketing` | 237 | `SessionExpiredException` |
| `OnBoardingHttpClient` | `onboarding` | 246 | `SessionExpiredException` |
| `SquareHttpClient` | `agency` | 288 | `SessionExpiredException`; refreshes **before every request** |
| `SsoHttpClient` | `sso` | – | can refresh twice at once |
| `KeycloakHttpClient` | `keycloak` | – | can refresh twice at once |

Only one retries after a refresh. Two can start two refreshes at the same time. `SquareHttpClient` refreshes before every request, which is a hidden load on Keycloak.

**2. GENFI wires five client variants in `main.dart`:** default, auth, Krakend, chat gateway, non-auth Krakend. The chat client uses `Bearer`; the OTP client uses `AuthBearer`. SQUARE wires three (default, auth, Krakend) plus `KeycloakConfig` and `SsoConfig`.

**3. The core client is small and has one bug.** `http_client.dart` is 395 lines, 30-second timeouts, typed exceptions with `correlationId` read from error responses, no trace id sent. `HttpResponseType.stream` and `.plain` both map to `ResponseType.json` (fixed in Phase 2). The only interceptor is pinning.

**4. There is a duplicate `KeycloakRepository`** across packages, and `package:http` and `dio` are used directly in places outside `HttpClient`. Alice (an HTTP inspector) ships in release builds.

The backend standard for request ids is a gateway-minted `x-bfi-req-id` (set 12–13 Oct 2026 for the BFI estate). The agency apps go through Krakend for some calls and straight to services for others (question 1).

## Steps at a glance

Sizes: **S** = 1–2 days, **M** = 3–5 days. Class **C** = behind `useInterceptorClient`, **E** = backend-coupled, **B** = same behaviour.

| # | Proposed ticket title | Today (24 Oct) | App | Class | Owner (role) | Size | Depends on | Jira ticket | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.1 | `feat(network): useInterceptorClient switch flag and facade selector` | No flag | shared | C | Agency engineer | S | 2.7, 2.11 | | |
| 4.2 | `feat(network): OtpAuthStrategy; wire GENFI behind the flag` | `OtpHttpClient` | GENFI | C | Agency engineer | M | 4.1 | | |
| 4.3 | `feat(network): Fold the Krakend, chat-gateway and non-auth variants into header options` | 5 variants | GENFI | C | Agency engineer | S | 4.2, Q2 | | |
| 4.4 | Cohort rollout of `useInterceptorClient` for GENFI, 10% → 50% → 100% | – | GENFI | C | Flag owner + on-call | 2–4 weeks | 4.3, 2.16 | | |
| 4.5 | `refactor(network): Delete the GENFI decorators` | – | GENFI | B | Agency engineer | S | 4.4 | | |
| 4.6 | `feat(network): KeycloakAuthStrategy; wire SQUARE behind the flag; cohort; delete` | `SquareHttpClient`, `KeycloakHttpClient`, `SsoHttpClient` | SQUARE | C then B | Agency engineer | M + 2–4 weeks | 4.5 | | |
| 4.7 | Same for MY BISPRO; then delete all six classes and the duplicate `KeycloakRepository` | – | MY BISPRO, shared | C then B | Agency engineer | S + 2 weeks | 4.6 | | |
| 4.8 | `chore(network): Alice to dev_dependencies; replace direct http and dio uses; trace id header` | Alice in release builds | shared | B + E | Agency engineer | S | 4.7, Q1 | | |

**Suggested order.** Sprint 1: 4.1, 4.2, 4.3. Then 4.4 (calendar). Sprint 3: 4.5, 4.6 build. Then 4.6 rollout. Sprint 5: 4.7, 4.8.

## Definition of ready for every Phase 4 ticket

* The characterisation tests (1.12) are listed as the oracle: they must pass against the new chain with the flag on, except the double-refresh test, which must now pass instead of fail.
* Contract replay with the recorded fixtures (Phase 1 parity net rows) is an acceptance criterion for every wiring ticket.
* No repository call site changes. If one must, it is a separate class B ticket.

## Step 4.1: Switch flag and facade selector

**Today.** No flag. The chain exists in `core` (2.11) but nothing uses it.

**Tasks.** `useInterceptorClient` in each app's catalogue (owner, removal date, default old, real-time). `HttpClient` reads it once per request and routes to the decorator (old) or the chain (new). SIT and UAT builds add an `x-bfi-chain: new` header so QA can see which path served a request.

**Acceptance criteria.** Flag off: every existing test passes unchanged. Flag on with no strategy wired yet: the chain falls back to old behaviour.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One flag per app for the whole chain | One kill switch, one cohort per app | All-or-nothing per app |
| B. One flag per interceptor | Fine-grained | Mixed states nobody tested |
| C. No flag | Simplest | A refresh bug logs out every agent at once |

**Recommended: A.**

## Step 4.2: `OtpAuthStrategy`, GENFI first

**Today.** `OtpHttpClient` (264 lines) is the only decorator that refreshes once and retries once.

**Tasks.** Implement `OtpAuthStrategy` from the existing repository code. Wire it in `agent_tools/lib/main.dart` behind the flag; the decorator stays as the old path. Run the 1.12 tests against the chain.

**Acceptance criteria.** With the flag on, the OTP tests pass; 5 parallel 401s cause exactly 1 refresh; the SIT smoke list (login, OTP, prospect input, calculator, reserve lead) passes on both paths; contract replay identical.

**Who / size.** One Agency engineer. M.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. GENFI first: largest user base, simplest auth | Proves the chain where the auth is easiest and the cohort is biggest | GENFI agents update slowly; the old path stays in the field longer |
| B. SQUARE first: internal users, managed devices | Safer rollout | Keycloak is the harder strategy; the race lives there |
| C. All three at once | Fast | Three cohorts, three auth schemes, one flag each: too much at once |

**Recommended: A**, as plan 05 says.

## Step 4.3: Fold the client variants

**Today.** Five `HttpClient` overrides in GENFI's `main.dart`. The chat gateway uses `Bearer`; OTP uses `AuthBearer`.

**Tasks.** Header options on one client instead of five variants. Standardise on `Bearer` once the backend accepts it; keep `AuthBearer` in the strategy until then (question 2).

**Acceptance criteria.** `main.dart` overrides one `HttpClient` provider. Contract replay shows identical headers per host on both paths.

**Who / size.** One Agency engineer. S. Class C, plus E if the header scheme changes.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One client, per-host header options | One wiring, one chain | The chat gateway's `Bearer` scheme must be confirmed |
| B. Keep five variants on the new chain | Smaller | Five providers to keep in step |
| C. Two clients (auth, non-auth), as the BFI app does | Standard: the refresh call cannot loop through the auth interceptor | Still needs per-host header options for Krakend and chat |

**Recommended: C's two-instance split inside A**: one `authDio` for the refresh call, one `apiDio` with per-host options.

## Step 4.4: Cohort rollout for GENFI

**Today.** Cohort dashboards and the kill-switch runbook exist after Phase 2 (2.16).

**Tasks.** 10% → 50% → 100%, one day of data per stage, no Play dial moved in the same week. Watch: HTTP error rate, session-expired count, refresh calls per session, p75 screen load, by flag value.

**Acceptance criteria.** Each stage noted in the ledger. Session-expired count on the new path at or below the old. No flip, or flip and fix recorded.

**Who / size.** Flag owner + on-call. 2–4 weeks.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Three stages, a day each minimum | Plan 05's loop | 2–4 weeks |
| B. 1% → 10% → 50% → 100% as the BFI app | Finer | GENFI's user count makes 1% a small sample |
| C. Internal testers then 100% | Fast | Testers do not have agents' devices and networks |

**Recommended: A.**

## Step 4.5: Delete the GENFI decorators

**Tasks.** After 2 releases at 100%: delete `OtpHttpClient`, the GENFI-only variants and the old-path tests. Keep the flag until SQUARE and MY BISPRO are done (one catalogue entry, three apps), then delete it in 4.7.

**Acceptance criteria.** `grep "implements HttpClient"` in `agent_marketing` returns 0.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Delete per app as each finishes | Debt goes down early | The shared flag outlives GENFI's rollout |
| B. Delete all six at the end | One PR | GENFI's dead code stays for months |
| C. Keep as fallback | None | Two paths forever |

**Recommended: A.**

## Step 4.6: SQUARE: `KeycloakAuthStrategy`

**Today.** `SquareHttpClient` refreshes before every request; `KeycloakHttpClient` and `SsoHttpClient` can refresh twice at once. SQUARE signs in through Keycloak with PKCE (plan 06 target).

**Tasks.** `KeycloakAuthStrategy` (also used by MY BISPRO): refresh on 401 or on expiry, single-flight, PKCE kept. Wire in `are_tracker/lib/main.dart` behind the flag. Cohort 20% → 100% (internal users). Delete the three Keycloak decorators after 2 releases.

**Acceptance criteria.** The double-refresh test now passes. Keycloak refresh calls per session drop (the pre-request refresh is gone); record the before and after. SSO login e2e passes on both paths.

**Who / size.** One Agency engineer. M + rollout.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. One Keycloak strategy shared by SQUARE and MY BISPRO | One fix for the race | MY BISPRO's config must match |
| B. Keep `SquareHttpClient`'s refresh-before-every-request behaviour | No behaviour change | Keeps the Keycloak load; the plan calls it a bug |
| C. Move SQUARE to OTP auth like GENFI | One strategy for all | A product and security change, not a refactor |

**Recommended: A.** The removed pre-request refresh is an approved delta: Keycloak sees fewer calls; sign it off with the IAM owner.

## Step 4.7: MY BISPRO, then delete everything old

**Tasks.** Wire MY BISPRO behind the flag with the Keycloak strategy; 20% → 100%; delete all six decorator classes, the duplicate `KeycloakRepository` and the flag.

**Acceptance criteria.** `grep "implements HttpClient"` in `shared_data` returns 0. One `KeycloakRepository`. The flag is gone from every catalogue.

**Who / size.** One Agency engineer. S + 2 weeks.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Same loop, then delete | Consistent | Waits for the third rollout |
| B. Skip the flag for MY BISPRO (internal, small) | Faster | A refresh bug blocks Sharia staff |
| C. Leave MY BISPRO on the old decorators | Less work | Six classes stay for one app |

**Recommended: A.**

## Step 4.8: Tidy, and the trace id

**Today.** Alice ships in release builds; `package:http` and `dio` are used directly outside `HttpClient`; no trace id is sent; `correlationId` is read from error responses only.

**Tasks.** Alice to `dev_dependencies` behind a compile-time flag. Replace direct `http` and `dio` uses with `HttpClient`. Trace id: read the gateway's `x-bfi-req-id` from responses and log it; send a client id only if SRE confirms the gateway honours it (question 1). Never invent a new header name.

**Acceptance criteria.** Release builds do not contain Alice. `pubghost` shows no undeclared imports. Error logs carry the gateway request id.

**Who / size.** One Agency engineer. S.

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| A. Read the gateway id, log it; Alice out of release | Follows the BFI standard; smaller binary | A request that never returns has no id |
| B. Send a client-minted `x-bfi-req-id` | One id from tap to database | Only if the gateway passes it through; direct-to-service calls bypass the gateway |
| C. Keep Alice in release "for support" | Convenient | An HTTP inspector in a prod lending app |

**Recommended: A**, B where SRE confirms.

## Exit gate for Phase 4

* `useInterceptorClient` at 100% for 2 releases in every app, then deleted.
* All six decorators and the duplicate `KeycloakRepository` deleted.
* Exactly 1 refresh per burst of parallel 401s in every app, proven by tests and by the refresh-calls-per-session metric.
* Alice out of release builds.

## Questions for the session

| # | Question | Who answers | Answer |
| --- | --- | --- | --- |
| Q1 | Which agency calls go through Krakend and which go direct? Does Krakend accept a client `x-bfi-req-id`? | SRE | |
| Q2 | Can the chat gateway and the OTP backend both accept `Bearer`? | Backend owners | |
| Q3 | Who owns Keycloak for the agency apps, and can we measure refresh calls per session before and after? | IAM owner | |
| Q4 | Who is the flag owner for `useInterceptorClient` per app? | Agency tech lead | |
| Q5 | Epic: one for the monorepo, with sub-tickets per app? | Agency tech lead | |

## Evidence

| Fact | How it was checked (24 Oct 2026) |
| --- | --- |
| Six decorators | plan 05 "today" table |
| Client variants | `agent_tools/lib/main.dart` (five overrides), `are_tracker/lib/main.dart` lines 211–238 |
| Core client | `shared_lib/core/lib/src/network/http_client.dart`, 395 lines |
| Request-id standard | Request-id chain decision, 12–13 Oct 2026 |

## Sources for the recommendations

* BFI Phase 4 refinement notes (single-flight refresh, two dio instances, `QueuedInterceptor`, request-id rules).
* [Your Dio interceptor is swallowing 401s](https://blog.devgenius.io/your-dio-interceptor-is-swallowing-401s-heres-the-race-condition-10ae0e93e728); [dio_bearer docs](https://pub-web-s1.flutter-io.cn/documentation/dio_bearer/0.0.2).
* GENFI plan 05: Networking (decorator table, strategies, interceptor order).
