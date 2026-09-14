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

---

## Implementation status

**Pull request: [bravo-agent-service#1632](https://github.com/bfi-finance/bravo-agent-service/pull/1632)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-agent-service/tree/fix/logging), head `45e487d6`, branched from `master` at `5c2b4a18`.

[Files changed](https://github.com/bfi-finance/bravo-agent-service/pull/1632/files) · [Commits](https://github.com/bfi-finance/bravo-agent-service/pull/1632/commits) · [Compare against master](https://github.com/bfi-finance/bravo-agent-service/compare/master...fix/logging)

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
