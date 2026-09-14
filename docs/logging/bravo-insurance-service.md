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

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/insurance/values-prod-sharia.yaml`, `app-deployment/insurance/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Logging variables | none of the shared-library switches are set; the wrapper defaults apply |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

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

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 947 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

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
