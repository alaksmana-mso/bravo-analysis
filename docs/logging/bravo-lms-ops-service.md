# bravo-lms-ops-service — logging findings and fixes

**Squad:** Operation Post-Go Live  
**Production service:** `prod-ms-lms-ops`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** 464,045 info, 67,867 error, 255 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What this PR changes

RequestLoggingFilterConfig built the filter with setIncludePayload(true) and a
10 KB cap. AbstractRequestLoggingFilter.shouldLog() returns
logger.isDebugEnabled(), and application-prod.yaml sets root: INFO with
nothing overriding the filter, so this never fired in production. It was still
a full request body one level change away from the log stream, and raising the
level is exactly what someone does when they are debugging an incident.
Payload capture is now off and the cap drops to 2 KB.

Not addressed here, and needing this squad. prod-bravo-lms-ops writes 67,867
error entries a week. The largest pattern, 1,264 of them, is a log line whose
entire message is the single word:

    Exception

That is not something a logging pass can repair from the outside — it needs
whoever wrote the call site to say what happened. The second largest, 446 a
week, is "Error decrypting bbn customer data", which looks like the same class
of problem as the decrypt failure on prod-ms-partnership and deserves an owner
rather than a level change.

No JDK or Maven is available on the machine this was written on, so this has
not been compiled or tested locally.

## Please build before merging

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* What was checked: brace and paren balance on every touched file, line lengths against the prettier-java `printWidth` of 120, and imports placed in sorted order. That is not a build — please treat the CI result as the first real check.

---

## Implementation status

**Pull request: [bravo-lms-ops-service#1856](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-lms-ops-service/tree/fix/logging), head `af3f466a`, branched from `master` at `057f3826`.

[Files changed](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856/files) · [Commits](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1856/commits) · [Compare against master](https://github.com/bfi-finance/bravo-lms-ops-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): close the request payload trap

Files:

- `src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java`

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

- fix(logging): close the request payload trap

Files:

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
