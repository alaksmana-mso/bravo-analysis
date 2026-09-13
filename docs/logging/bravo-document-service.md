# bravo-document-service — logging findings and fixes

**Squad:** Operation Post-Go Live  
**Production service:** `prod-ms-document`  
**Stack:** Java, Spring Boot, bravo-lib-logging  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**No change was needed.** `application-prod.yaml` sets `root: INFO` and `RestTemplate: INFO`; the `DEBUG` entries are confined to `application-local` and `application-local-standalone`. There is no payload-capturing filter and no `loggerLevel: full`.

`prod-ms-document` produced **no log entries and no APM spans** over the 7 days to 13 September 2026.

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
