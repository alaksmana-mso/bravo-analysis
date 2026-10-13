# bravo-lms-ops-service — logging findings and fixes

**Squad:** Operation Post-Go Live  
**Production service:** `prod-ms-lms-ops`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** 464,045 info, 67,867 error, 255 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

RequestLoggingFilterConfig built the filter with setIncludePayload(true) and a
10 KB cap. AbstractRequestLoggingFilter.shouldLog() returns
logger.isDebugEnabled(), and application-prod.yaml sets root: INFO with
nothing overriding the filter, so this never fired in production. It was still
a full request body one level change away from the log stream, and raising the
level is exactly what someone does when they are debugging an incident.
Payload capture is now off and the cap drops to 2 KB.

Not addressed here, and needing this squad. prod-bravo-lms-ops writes 67,867
error entries a week. The largest pattern, 1,264 of them, is a log line whose
entire message is the single word:

    Exception

That is not something a logging pass can repair from the outside — it needs
whoever wrote the call site to say what happened. The second largest, 446 a
week, is "Error decrypting bbn customer data", which looks like the same class
of problem as the decrypt failure on prod-ms-partnership and deserves an owner
rather than a level change.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/lms-ops/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `SENSITIVE_KEYS` | `password,secret,authorization,api-secret,nik,Set-Cookie` |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | `false` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It wires the library's `RequestLoggingFilter` and `FeignClientFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 2.7.18, so the starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September 2026, Boot 3.3+ only) is out of reach until it upgrades. It stays on `bravo-lib-logging`, whose fix ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) **was closed on 16 September** when the starter merged, so the library keeps unmasked Feign bodies, case-sensitive `SENSITIVE_KEYS` and no body cap: set `REQUEST_BODY_LOGGING=false`, `RESPONSE_BODY_LOGGING=false` and a written `SENSITIVE_KEYS` in `values-prod.yaml`, merge the per-service pull request, and put the Boot 3.3 upgrade on the roadmap — it is the only route to the starter.
---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service is on Spring Boot 2.7.18, so it cannot take the starter (Boot 3.3 or later). What it gets: nothing from the libraries for now. `bravo-lib-logging` is deprecated (decided 13 October); only core and the starter are developed further, so [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) and #132 leave it untouched. Until this service moves to Boot 3 and the starter it keeps `X-Correlation-Id` and a UUID of its own, and a Go service on an older wrapper replaces that id.

What is left for the squad and SRE:

- **Deployment (SRE):** add `DD_TRACE_HEADER_TAGS: "x-bfi-req-id:request_id"` to the service's app-deployment values; the Datadog Java agent tags spans from the header with no code change, and this works on Boot 2.7 as it does on Boot 3.
- **Forwarding:** until the move to the starter, Feign calls (47 files) need the service's own `RequestInterceptor` that copies the correlation id from the MDC into the `x-bfi-req-id` header, or a hop into another service starts a new id.
- **Error bodies:** add the correlation id from the MDC to the service's error type, so a caller can quote it.

## Implementation status

**Pull request: [bravo-lms-ops-service#1856](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-lms-ops-service/tree/fix/logging), head `af3f466a`, branched from `master` at `057f3826`.

[Files changed](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856/files) · [Commits](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856/commits) · [Compare against master](https://github.com/bfi-finance/bravo-lms-ops-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 2.7.18. The shared Java logging library every service moves to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)), but it is Boot 3.3+ only (jakarta), so it is out of reach here until the repository upgrades. The fix to the old library that would have bridged that gap, [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123), **was closed the same day** so that one library carries the standard. That leaves **this pull request, plus `REQUEST_BODY_LOGGING=false`, `RESPONSE_BODY_LOGGING=false` and a written `SENSITIVE_KEYS` in `values-prod.yaml`, as the fix for this service** until a Boot 3.3 upgrade, which is the only route to masked, capped, single-line logs for it.

CI on the current head is red only on **`Security Container Scan`, `Static Analysis - SonarQube`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 1 Codacy thread(s); 1 fixed in `c2eb2732` (refactor(logging): drop the payload cap the disabled payload never used). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): close the request payload trap

Files:

- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Run CI on the pull request — see the verification note above for what was and was not checked locally
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
