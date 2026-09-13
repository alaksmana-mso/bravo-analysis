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

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* Line lengths were checked against the prettier-java `printWidth` of 120 and brace balance verified by script. That is not a build.

---

## Implementation status

**Pull request: [bravo-repeat-order-service#3503](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-repeat-order-service/tree/fix/logging), head `3c9a0da3c`, branched from `master` at `8f0c4d338`.

[Files changed](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503/files) · [Commits](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3503/commits) · [Compare against master](https://github.com/bfi-finance/bravo-repeat-order-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/WebConfig.java`

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/WebConfig.java`

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---

## Checklist

- [ ] Run CI on the pull request — nothing here was compiled or tested
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
