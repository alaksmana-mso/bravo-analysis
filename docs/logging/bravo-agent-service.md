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

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* What was checked: brace and paren balance on every touched file, line lengths against the prettier-java `printWidth` of 120, and imports placed in sorted order. That is not a build — please treat the CI result as the first real check.

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

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/adapter/advice/ErrorAdvice.java`

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
