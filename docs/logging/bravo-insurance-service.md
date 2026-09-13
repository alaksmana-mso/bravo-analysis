# bravo-insurance-service — logging findings and fixes

**Squad:** Insurance  
**Production service:** `prod-ms-insurance`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** 10,145 error, 78 warn, no info at all

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

prod-ms-insurance writes 10,145 error entries a week against 78 warn and no
info at all. Error is doing every job in this service, which means it
distinguishes nothing.

ErrorAdvice moves four handlers off error:

- handleParseError, handleHttpMessageNotReadable and the bad-request fallback
  only ever produce a 400. They are now warn.
- handleBusinessException decides by status: 5xx stays at error, 4xx moves to
  warn. The status is already on the exception.

The three 4xx handlers also passed the exception in as a second argument, so
every rejected request printed a full stack trace. A stack trace for "the
caller sent a malformed date" is noise. Dropped on those three; kept
everywhere the exception is genuinely unexpected.

handleServiceException, handleDefaultException and handleAccessDeniedException
are unchanged.

Not fixable here: 282 of this service's weekly error entries are the Datadog
Java tracer's own output. The tracer writes to System.err, the log pipeline
maps stderr to error, and so a line the tracer itself labels WARN
("[dd-remote-config] WARN ... empty targets meta in director local store")
arrives in Datadog as an error from this service. That is a Remote
Configuration failure and a pipeline classification problem, not an
application defect.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* What was checked: brace and paren balance on every touched file, line lengths against the prettier-java `printWidth` of 120, and imports placed in sorted order. That is not a build — please treat the CI result as the first real check.

---

## Implementation status

**Pull request: [bravo-insurance-service#820](https://github.com/bfi-finance/bravo-insurance-service/pull/820)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-insurance-service/tree/fix/logging), head `5e917468`, branched from `master` at `242768ce`.

[Files changed](https://github.com/bfi-finance/bravo-insurance-service/pull/820/files) · [Commits](https://github.com/bfi-finance/bravo-insurance-service/pull/820/commits) · [Compare against master](https://github.com/bfi-finance/bravo-insurance-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): log rejected requests at warn, not error

Files:

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`

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

- `src/main/java/com/bfi/bravo/config/ErrorAdvice.java`

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
