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
