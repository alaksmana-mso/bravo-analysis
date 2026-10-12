# bravo-asset-pricing-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-asset-pricing`  
**Stack:** Java, Spring Boot, Feign, bravo-lib-logging  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**No change was needed.** I looked and found nothing in this repository that a logging pass should alter.

- `application-prod.yaml` sets `root: INFO`, `hibernate: WARN`, `RestTemplate: INFO`.
- `application.yaml` takes its levels from `LOGGING_LEVEL_COM_BFI_BRAVO` and `LOGGING_LEVEL_ROOT`, both defaulting to `INFO`.
- The seven `loggerLevel: full` entries are all in `application-dev`, `-sit`, `-uat` and `-local`. Production does not use those profiles.
- No `CommonsRequestLoggingFilter` bean with `setIncludePayload(true)`.

`prod-ms-asset-pricing` produced **no log entries and no APM spans** over the 7 days to 13 September 2026. A service that cannot be observed at all is a bigger problem than any of the logging defects in this programme, and it is not one this pull request pack can fix.

---


## Which Java wrapper applies here (17 September 2026)

This repository is on Spring Boot 2.7.18, so the starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), merged 16 September 2026, Boot 3.3+ only) is out of reach until it upgrades. It stays on `bravo-lib-logging`, whose fix ([bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123)) **was closed on 16 September** when the starter merged, so the library keeps unmasked Feign bodies, case-sensitive `SENSITIVE_KEYS` and no body cap: set `REQUEST_BODY_LOGGING=false`, `RESPONSE_BODY_LOGGING=false` and a written `SENSITIVE_KEYS` in `values-prod.yaml`, and put the Boot 3.3 upgrade on the roadmap — it is the only route to the starter.

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service is on Spring Boot 2.7.18, so it cannot take the starter (Boot 3.3 or later). What it gets: `bravo-lib-logging`'s filter reads `x-bfi-req-id` first, then `X-Correlation-Id`, from the next release of the `logger` module after [bfi-java-pkg#129](https://github.com/bfi-finance/bfi-java-pkg/pull/129) merges; it still mints a UUID when no id arrives, which a Go service on an older wrapper replaces. The Feign forwarding and the rejected-request line in #132 are starter-only.

What is left for the squad and SRE:

- **Deployment (SRE):** add `DD_TRACE_HEADER_TAGS: "x-bfi-req-id:request_id"` to the service's app-deployment values; the Datadog Java agent tags spans from the header with no code change, and this works on Boot 2.7 as it does on Boot 3.
- **Forwarding:** Feign calls (6 files) need the service's own `RequestInterceptor` that copies the library's correlation id from the MDC into the `x-bfi-req-id` header. Until then a hop into another service starts a new id.
- **Error bodies:** add the correlation id from the MDC to the service's error type, so a caller can quote it.

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
