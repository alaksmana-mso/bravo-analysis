# bravo-partnership-service — logging findings and fixes

**Squad:** Digital Partnership  
**Production service:** `prod-ms-partnership`  
**Stack:** Go, zerolog, gRPC, RabbitMQ, NATS, bfi-go-pkg  
**Production volume:** 561,767 warn, 399,780 error, 4,069 info a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-partnership` writes **964,197 log entries a week**: 561,767 warn, 399,780 error, 4,069 info. Measured in Datadog over the 7 days to 13 September 2026.

| Source (`@module`) | Level | Entries/week |
|---|---|---:|
| `requestloggerinterceptor.unary_server` | warn | 202,148 |
| `rabbitmq.loan_application.work.consumer` | error | 159,183 |
| `http.client` | warn | 137,649 |
| `service.agreement_history` | error | 43,431 |
| `cronjob.agreement_scheduler` | error | 22,006 |

**123,503 entries a week carry a full HTTP request or response body.** That is the highest count of any service in the estate.

The largest single error line is `[StatusTrack Listener] Could not finish transaction when updating data` at **76,309 a week** — and it logs the entire raw MQ message body alongside it.

## What this PR changes

Only what is written to logs. No business logic, no message-handling semantics.

**1. New `pkg/logbody`.** Masks sensitive JSON fields, truncates to 2 KiB, and refuses to copy a payload it cannot parse as JSON — it cannot tell what such a payload holds. Unit tests included.

**2. 70 call sites across 13 RabbitMQ consumers** logged the whole raw message body on every failure path:

```go
Str("body", string(mqMessage.Body)).          // before
Str("body", logbody.String(mqMessage.Body)).  // after
```

The statustrack consumer also dumped the decoded payload with `Any("mqData", mqData)`. `conditionalLogger` returns `Info()` for go-live, disbursed and live statuses, so that line ran at **info** level in production. It now goes through `logbody.Any`.

**3. The shared HTTP client had no masking function and a 32 KiB limit** on each body:

```go
httpclient.WithRequestBodyLoggingFunc(logbody.Scrub),   // added
httpclient.WithRequestBodyLoggingLimit(4096),           // was 32768
httpclient.WithResponseBodyLoggingFunc(logbody.Scrub),  // added
httpclient.WithResponseBodyLoggingLimit(4096),          // was 32768
```

`WithRequestBodyLoggingFunc` and `WithResponseBodyLoggingFunc` already exist in `bfi-go-pkg`. They were simply never wired up. A production sample of one of these entries carried a customer's collateral and sub-district data in plaintext.

**One level change.** `[StatusTrack Listener] Status state transition is not valid` moves from error to warn. It is the state machine rejecting a transition — the expected outcome of a rule, not a service fault. The same application group ID appears **183 times** because the message is redelivered.

## What this PR deliberately does not change

**The redelivery loop.** A permanently invalid transition is retried until it ages out; every UUID in that log line repeats exactly 183 times. Fixing it means deciding the message is non-retryable, which is a message-handling change and belongs to this squad, not to a logging pass.

**`failed to decrypt bank_account_name_to, assuming plaintext`** — 639 entries in two days, at warn. The service fails to decrypt a bank account holder's name and carries on with the value as plaintext. This line is left exactly as it is: it is the only signal that this is happening. It needs an owner, and it is not a logging defect.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `app-deployment/partnership/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `info` |
| Postgres log level | `warn` |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## Implementation status

**Wrapper follow-up (14 September 2026).** The `pkg/logbody` package this branch adds is the kind of thing that belongs in the shared library, and [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) adds `logger.Payload(b, scrub, limit)` for exactly this use — a queue consumer that has no HTTP middleware to bound and mask a body for it. Once that ships, the 70 call sites here can move to `logger.Payload(msg.Body, logger.JSONScrubberFunc(cfg.MaskedFields), 2048)` and `pkg/logbody` can go, with the field list coming from the environment as SRE asks. The branch is left as it is so the fix does not wait on a library release.

**Pull request: [bravo-partnership-service#2367](https://github.com/bfi-finance/bravo-partnership-service/pull/2367)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-partnership-service/tree/fix/logging), head `08dc1d0c9`, branched from `master` at `a676689bf`.

[Files changed](https://github.com/bfi-finance/bravo-partnership-service/pull/2367/files) · [Commits](https://github.com/bfi-finance/bravo-partnership-service/pull/2367/commits) · [Compare against master](https://github.com/bfi-finance/bravo-partnership-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request. The Go wrapper fix, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) (`JSONScrubber` masks non-string values), is still open; the masked-field lists stay a per-service, per-environment setting in `app-deployment`, as SRE asked on 14 September.

CI on the current head is red only on **`Security Scan - SNYK`, `Static Analysis - SonarQube`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

| | |
|---|---|
| Commits | 1 |
| Files changed | 16 |

Commits:

- fix(logging): stop copying MQ and HTTP payloads into the log stream

Files:

- `cmd/grpc/main.go`
- `internal/rabbitmq/additionaldocument/webhookposting/work_consumer.go`
- `internal/rabbitmq/agreementhistory/work_consumer.go`
- `internal/rabbitmq/loandocument/cancellation_work_consumer.go`
- `internal/rabbitmq/loandocument/esignviabfi/sign_lender_complete_work_consumer.go`
- `internal/rabbitmq/loandocument/webhookposting/webhook_consumer.go`
- `internal/rabbitmq/loanevent/work_consumer.go`
- `internal/rabbitmq/loanposting/webhookposting/work_consumer.go`
- `internal/rabbitmq/loanposting/work_consumer.go`
- `internal/rabbitmq/repayment/work_consumer.go`
- `internal/rabbitmq/repeatorder/work_consumer.go`
- `internal/rabbitmq/repeatordercdp/work_consumer.go`
- `internal/rabbitmq/statustrack/webhookposting/work_consumer.go`
- `internal/rabbitmq/statustrack/work_consumer.go`
- `pkg/logbody/logbody.go`
- `pkg/logbody/logbody_test.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches
- `go test ./pkg/logbody/...` — 7 tests, all pass

It found a real defect in this change: `gochecknoglobals` on two lookup tables in `pkg/logbody`. Fixed on the branch.

Unit tests beyond those shipped with this change have not been run, and nothing has
been exercised against a running dependency. CI remains the authority.

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
