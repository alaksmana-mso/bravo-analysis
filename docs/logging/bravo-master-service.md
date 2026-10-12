# bravo-master-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-master`  
**Stack:** Java, Spring Boot  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**No change was needed.** `application.yaml` takes its levels from `LOGGING_LEVEL_COM_BFI_BRAVO` and `LOGGING_LEVEL_ROOT`, both defaulting to `INFO`, and `application-prod.yaml` pins `root: INFO`. The `root: DEBUG` entries are in `application-local` and `application-unit-test`.

`ApiExceptionHandler` logs at error in exactly one place — `handleServerError`, which returns a 500. That is correct: unlike the ErrorAdvice classes in the sibling repositories, it does not log its 4xx handlers at all.

`prod-ms-master` produced **no log entries and no APM spans** over the 7 days to 13 September 2026.

---


## Which Java wrapper applies here (17 September 2026)

This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It was not published when this was written; **Platform published it on 23 September 2026** (*Deploy Package* runs for `bfi-logging-core` 0.1.0 and then `bfi-logging-spring-boot-starter` 0.1.0), so the dependency can be added now — no service had done so by 6 October. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service is on Spring Boot 3.5.15, so its path is the logging starter, `bfi-logging-spring-boot-starter` 0.1.3 or later. With [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) the starter's filter reads `x-bfi-req-id` (the gateway's header) first and `X-Correlation-Id` as a fallback, mints an id in the gateway's xid format when none arrives, and returns it on the response. With [#132](https://github.com/bfi-finance/bfi-java-pkg/pull/132) every Feign call forwards it (this repository has Feign in 3 files), and one `request_rejected` line names the fields that failed validation, never the values. **None of this applies until the service adopts the starter**; no service has it on its main branch yet.

What is left for the squad and SRE:

- **Deployment (SRE):** add `DD_TRACE_HEADER_TAGS: "x-bfi-req-id:request_id"` to the service's app-deployment values. The Datadog Java agent then tags spans with the same name the Go wrapper uses, so one trace search finds every service of a request.
- **Header name:** the service handles `X-Correlation-Id` in its own code (1 file). Switch those places to `x-bfi-req-id`; the starter keeps reading the old header as a fallback, so the switch can be gradual.
- **RestTemplate / WebClient calls** are not forwarded by the starter. Add the service's own interceptor that copies `CorrelationId.current()` into the `x-bfi-req-id` header.
- **Error bodies:** the service has its own error type; add `CorrelationId.current()` (bfi-logging-core) to it in the exception handler, so a caller can quote the id without reading headers.

## Implementation status

**No pull request, and none needed.** No branch was created for this repository.
See the findings above for why.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Establish why this service emits no telemetry in production, or retire the name
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
