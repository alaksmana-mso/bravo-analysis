# bravo-agent-service — logging findings and fixes

**Squad:** Agency  
**Production service:** `prod-ms-agent`  
**Stack:** Java, Spring Boot, bravo-lib-logging  
**Production volume:** 86,579 info, 32,911 error, 222 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

prod-ms-agent writes 32,911 error entries a week against 86,579 info.
ErrorAdvice logs at error in eleven places, and six of them only ever produce
an HTTP 400:

  MethodArgumentNotValidException, MethodArgumentTypeMismatchException,
  ConstraintViolationException, DataIntegrityViolationException,
  PropertyReferenceException, MissingServletRequestParameterException

All six are the caller sending something this service correctly refused. They
move to warn. Two of the messages also said only "Exception occurred" or
"Error occurred" with no indication of which handler wrote them; they now name
the exception they handle.

Deliberately unchanged and still at error:

- handleSQLExceptionError. It answers 400, but an SQLException is this
  service's fault whatever status the caller sees.
- handleBusinessExceptionError and handleResponseError, whose status varies.
- handleException, the 500 catch-all.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/agent/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `INFO` |
| `SENSITIVE_KEYS` | not set  ← library default (6 keys) |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | not set  ← library default `true` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It wires the library's `RequestLoggingFilter` and `FeignClientFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It was not published when this was written; **Platform published it on 23 September 2026** (*Deploy Package* runs for `bfi-logging-core` 0.1.0 and then `bfi-logging-spring-boot-starter` 0.1.0), so the dependency can be added now — no service had done so by 6 October. Migrating off `bravo-lib-logging` means deleting the `logback*.xml` files and the manual filter beans, and telling SRE that the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service is on Spring Boot 3.5.15, so its path is the logging starter, `bfi-logging-spring-boot-starter` 0.1.3 or later. With [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) the starter's filter reads `x-bfi-req-id` (the gateway's header) first and `X-Correlation-Id` as a fallback, mints an id in the gateway's xid format when none arrives, and returns it on the response. With [#132](https://github.com/bfi-finance/bfi-java-pkg/pull/132) every Feign call forwards it (this repository has Feign in 4 files), and one `request_rejected` line names the fields that failed validation, never the values. **None of this applies until the service adopts the starter**; no service has it on its main branch yet.

What is left for the squad and SRE:

- **Deployment (SRE):** add `DD_TRACE_HEADER_TAGS: "x-bfi-req-id:request_id"` to the service's app-deployment values. The Datadog Java agent then tags spans with the same name the Go wrapper uses, so one trace search finds every service of a request.
- **Header name:** the service handles `X-Correlation-Id` in its own code (1 file). Switch those places to `x-bfi-req-id`; the starter keeps reading the old header as a fallback, so the switch can be gradual.
- **RestTemplate / WebClient calls** are not forwarded by the starter. Add the service's own interceptor that copies `CorrelationId.current()` into the `x-bfi-req-id` header.
- **Error bodies:** the service has its own error type; add `CorrelationId.current()` (bfi-logging-core) to it in the exception handler, so a caller can quote the id without reading headers.

## Implementation status

**Pull request: [bravo-agent-service#1632](https://github.com/bfi-finance/bravo-agent-service/pull/1632)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-agent-service/tree/fix/logging), head `45e487d6`, branched from `master` at `5c2b4a18`.

[Files changed](https://github.com/bfi-finance/bravo-agent-service/pull/1632/files) · [Commits](https://github.com/bfi-finance/bravo-agent-service/pull/1632/commits) · [Compare against master](https://github.com/bfi-finance/bravo-agent-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.15. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It was not published when this was written; **Platform published it on 23 September 2026** (*Deploy Package* runs for `bfi-logging-core` 0.1.0 and then `bfi-logging-spring-boot-starter` 0.1.0), so the dependency can be added now — no service had done so by 6 October. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `bravo-lib-logging`, its filter beans and `logback*.xml` in the same change; the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`).

CI on the current head is **fully green**.

**Codacy review, answered 18 September 2026.** 1 Codacy thread(s); 1 fixed in `b2435677` (refactor(advice): type the PropertyReferenceException handler). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/adapter/advice/ErrorAdvice.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 2181 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
