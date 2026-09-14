# bravo-journal-service — logging findings and fixes

**Squad:** Contract Collateral & Loan Calculation  
**Production service:** `prod-ms-journal`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

1. ErrorAdvice logged four handlers at error. handleParseError,
   handleHttpMessageNotReadable and the bad-request fallback only ever produce
   a 400, so they move to warn. handleBusinessException decides by status: 5xx
   stays at error, 4xx moves to warn.

2. RequestLoggingFilterConfig built the filter with setIncludePayload(true)
   and a 10 KB cap. AbstractRequestLoggingFilter.shouldLog() returns
   logger.isDebugEnabled(), and application-prod.yaml sets root: INFO with
   nothing overriding the filter, so this never fired in production. It was
   still a full request body one level change away from the log stream, and
   raising the level is exactly what someone does when they are debugging an
   incident. Payload capture is now off and the cap drops to 2 KB.

prod-ms-journal produced no log entries at all over the 7 days to 13 September
2026. That is its own problem and not one this PR can fix.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/journal/values-prod-sharia.yaml`, `app-deployment/journal/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Logging variables | none set — the service's own `application*.yaml` decides |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (15 September 2026).** This repository is on Spring Boot 2.7.18, so the new starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), Boot 3.x only) is not available to it until it upgrades. It stays on its own filters and Feign loggers, with the per-file fixes above; the shared-library fixes in [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) do not apply to it because it does not use `bravo-lib-logging`.
---

## Implementation status

**Pull request: [bravo-journal-service#297](https://github.com/bfi-finance/bravo-journal-service/pull/297)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-journal-service/tree/fix/logging), head `2d70fa3`, branched from `master` at `55de33b`.

[Files changed](https://github.com/bfi-finance/bravo-journal-service/pull/297/files) · [Commits](https://github.com/bfi-finance/bravo-journal-service/pull/297/commits) · [Compare against master](https://github.com/bfi-finance/bravo-journal-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): log rejected requests at warn, and close the payload trap

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 934 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
