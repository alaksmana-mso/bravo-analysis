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
