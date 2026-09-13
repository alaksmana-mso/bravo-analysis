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

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* What was checked: brace and paren balance on every touched file, line lengths against the prettier-java `printWidth` of 120, and imports placed in sorted order. That is not a build — please treat the CI result as the first real check.

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

- fix(logging): log rejected requests at warn, and close the payload trap

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`
- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

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
