# bravo-repeat-order-service — logging findings and fixes

**Squad:** Tele Marketing  
**Production service:** `prod-ms-repeat-order`  
**Stack:** Java, Spring Boot, Feign, RabbitMQ  
**Production volume:** 244,564 info, 51,843 error, 36,237 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-repeat-order` writes **51,843 error entries a week** (plus 244,564 info and 36,237 warn). Measured in Datadog over the 7 days to 13 September 2026.

The dominant error pattern is this service's own `ControllerAdvice` reporting 4xx responses:

| Pattern | Entries/week |
|---|---:|
| `Error handleBusinessException: …ErrorResponse(…)` | 344 + 211 + 82 + 49 + 26 + 24 + 20 + 18 (many code variants) |
| `[GenericCalculatorServiceImpl][getSimulationTypeInfo] error 400 BAD_REQUEST "…contract status: EXPIRED is not allowed"` | 209 |
| `Error handleMethodArgumentNotValid: …code=B0000, message=Bad Request…` | 119 |

Sampled messages include `Agent not found: null`, `Found duplicate license from Branch ID …`, `Minimum required installment payment not met. Required: 5, Paid: 0`, and bean-validation failures.

**Every one of those is a rule rejecting a request.** The caller sent something the service correctly refused. Reporting them at `error` means `error` no longer distinguishes anything — which is the actual cost here, more than the volume.

## What this PR changes

In `ErrorAdvice`:

| Handler | Before | After |
|---|---|---|
| `handleMethodArgumentNotValid` | error | **warn** |
| `handleResourceConflictException` | error | **warn** |
| `handleBadRequest` | error | **warn** |
| `handleMethodArgumentTypeMismatch` | error | **warn** |
| `handleBusinessException` | error | **warn for 4xx, error kept for 5xx** |
| `handleFeignException` | error | **error — unchanged** |
| `handleRuntimeException` | error | **error — unchanged** |

`BusinessException extends ResponseStatusException`, so the status is already on the exception:

```java
if (e.getStatusCode().is5xxServerError()) {
  log.error(...);
} else {
  log.warn(String.format("Rejected request, handleBusinessException: %s ", body));
}
```

The message prefix changes from `Error handle…` to `Rejected request, handle…` so the line reads as what it is.

**`handleFeignException` deliberately stays at error.** A Feign failure means a downstream call failed, even though this service answers 400 to its own caller. That is worth waking someone.

## Also: a 64 KB payload trap

`WebConfig` built the request-logging filter with `setIncludePayload(true)` and `setMaxPayloadLength(64000)`.

`AbstractRequestLoggingFilter.shouldLog()` returns `logger.isDebugEnabled()`, and no production profile sets `CommonsRequestLoggingFilter` to DEBUG — so **this is dormant today**. I checked `application-prod.yaml`: `root: INFO`, nothing overriding the filter.

But it is a 64 KB request body one level change away from the log stream, and raising the level is exactly what someone does when they are debugging an incident. Payload capture is now off and the cap is 2 KB.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/repeat-order/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_ROOT` | `INFO` |
| `FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL` | `basic` |
| `LOGGING_LEVEL_ORG_HIBERNATE_SQL` | `WARN` |
| `LOGGING_LEVEL_ORG_HIBERNATE_TYPE_DECRIPTOR_SQL` | `WARN` |
| `LOGGING_LEVEL_COM_BFI_BRAVO_ADAPTER_HTTP_FEIGN` | `INFO` |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.3.2, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It was not published when this was written; **Platform published it on 23 September 2026** (*Deploy Package* runs for `bfi-logging-core` 0.1.0 and then `bfi-logging-spring-boot-starter` 0.1.0), so the dependency can be added now — no service had done so by 6 October. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service is on Spring Boot 3.3.2, so its path is the logging starter, `bfi-logging-spring-boot-starter` 0.1.3 or later. With [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) the starter's filter reads `x-bfi-req-id` (the gateway's header) first and `X-Correlation-Id` as a fallback, mints an id in the gateway's xid format when none arrives, and returns it on the response. With [#132](https://github.com/bfi-finance/bfi-java-pkg/pull/132) every Feign call forwards it (this repository has Feign in 71 files), and one `request_rejected` line names the fields that failed validation, never the values. **None of this applies until the service adopts the starter**; no service has it on its main branch yet.

What is left for the squad and SRE:

- **Deployment (SRE):** add `DD_TRACE_HEADER_TAGS: "x-bfi-req-id:request_id"` to the service's app-deployment values. The Datadog Java agent then tags spans with the same name the Go wrapper uses, so one trace search finds every service of a request.
- **Header name:** the service handles `X-Correlation-Id` in its own code (1 file). Switch those places to `x-bfi-req-id`; the starter keeps reading the old header as a fallback, so the switch can be gradual.
- **RestTemplate / WebClient calls** are not forwarded by the starter. Add the service's own interceptor that copies `CorrelationId.current()` into the `x-bfi-req-id` header.
- **Error bodies:** the service has its own error type; add `CorrelationId.current()` (bfi-logging-core) to it in the exception handler, so a caller can quote the id without reading headers.

## Implementation status

**Pull request: [bravo-repeat-order-service#3503](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-repeat-order-service/tree/fix/logging), head `3c9a0da3c`, branched from `master` at `8f0c4d338`.

[Files changed](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503/files) · [Commits](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503/commits) · [Compare against master](https://github.com/bfi-finance/bravo-repeat-order-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.3.2. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It was not published when this was written; **Platform published it on 23 September 2026** (*Deploy Package* runs for `bfi-logging-core` 0.1.0 and then `bfi-logging-spring-boot-starter` 0.1.0), so the dependency can be added now — no service had done so by 6 October. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

CI on the current head is red only on **`Security Container Scan`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 6 Codacy thread(s); 6 fixed in `96e379f22` (fix(logging): keep the trace on the 5xx branch; placeholders). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/WebConfig.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 5559 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
