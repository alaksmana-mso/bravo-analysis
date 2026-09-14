# bravo-collateral-service — logging findings and fixes

**Squad:** Contract Collateral & Loan Calculation  
**Production service:** `prod-ms-collateral`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** no log entries under this name over the 7-day window

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

Two changes, both logging only.

1. ErrorAdvice logged five 400-producing handlers at error:
   handleMethodArgumentNotValid, handleBadRequest, handleParseError,
   handleHttpMessageNotReadable and the bad-request fallback. Each is the
   caller being told no, not a fault in this service, so each moves to warn.
   handleBusinessException was already at info and is left alone.

2. RequestLoggingFilterConfig built the filter with setIncludePayload(true).
   AbstractRequestLoggingFilter.shouldLog() returns logger.isDebugEnabled(),
   and application-prod.yaml sets root: INFO with nothing overriding the
   filter, so this never fired in production — prod-ms-collateral emits no
   logs at all over a 7-day window. It was still a full request body one level
   change away from the log stream, and raising the level is exactly what
   someone does when they are debugging an incident. Payload capture is now
   off and the cap drops to 2 KB.

Worth a separate look, and not touched here: application-prod.yaml carries a
hardcoded microservice.confinsoauth key and secret pair in the committed prod
profile. The value looks like a placeholder, but if it is live it does not
belong in the repository.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/collateral/values-prod-sharia.yaml`, `app-deployment/collateral/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_COM_BFI_BRAVO_UTIL` | `ERROR` *(values-prod.yaml)* |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (15 September 2026).** This repository is on Spring Boot 2.7.18, so the new starter ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), Boot 3.x only) is not available to it until it upgrades. It stays on its own filters and Feign loggers, with the per-file fixes above; the shared-library fixes in [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) do not apply to it because it does not use `bravo-lib-logging`.
---

## Implementation status

**Pull request: [bravo-collateral-service#420](https://github.com/bfi-finance/bravo-collateral-service/pull/420)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-collateral-service/tree/fix/logging), head `d3c8242`, branched from `master` at `795c6b9`.

[Files changed](https://github.com/bfi-finance/bravo-collateral-service/pull/420/files) · [Commits](https://github.com/bfi-finance/bravo-collateral-service/pull/420/commits) · [Compare against master](https://github.com/bfi-finance/bravo-collateral-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): log rejected requests at warn, and close the payload trap

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 1530 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
