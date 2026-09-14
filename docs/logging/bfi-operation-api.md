# bfi-operation-api — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-ms-bfi-operation-api`  
**Stack:** Java, Spring Boot, Feign, JasperReports  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**No write access.** The GitHub API reports `permissions.push: false` for this repository for the account this work ran under, so no branch could be pushed and no pull request opened.

There is a real finding here and it needs whoever owns the repo:

`src/main/java/id/co/bfi/bfioperationapi/config/RequestLoggingFilterConfig.java` is **correctly profile-gated** — `setIncludePayload(true)` for dev, sit, uat and test; `false` for prod. That part is right, and it is the pattern the rest of the estate should copy.

What is not right: `application-dev.yaml` sets `loggerLevel: FULL` on two Feign clients and `application-local-standalone.yaml` on a third. Those are non-production profiles, so nothing is leaking, but a full Feign log writes request and response bodies in their entirety and there is no masking anywhere in this repository.

`prod-ms-bfi-operation-api` produced **no log entries at all** over the 7 days to 13 September 2026, and no APM spans either. Either it is not running under that name or it is entirely dark. That is worth establishing before anything else.

---


## Which Java wrapper applies here (15 September 2026)

This repository is on Spring Boot 3.3.1, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. Migrating off `bravo-lib-logging` means deleting the `logback*.xml` files and the manual filter beans, and telling SRE that `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.

## Implementation status

**No pull request, and none needed.** No branch was created for this repository.
See the findings above for why.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
