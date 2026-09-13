# bravo-audit-trail-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-audit-trail`  
**Stack:** Go, zerolog, gRPC, RabbitMQ, bfi-go-pkg  
**Production volume:** 291,538 info, 567 error, 4 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-audit-trail` writes **291,538 info, 567 error and 4 warn** a week. Measured in Datadog over the 7 days to 13 September 2026.

Volume is not this service's problem. Two smaller things are.

## 1. Outbound bodies were logged with no masking at all

`cmd/grpc/main.go` builds the shared logged transport with request and response body logging on and **no masking function** — this service had no `*_JSON_MASKED_FIELDS` configuration to wire up in the first place.

Two config fields are added, defaulting to a list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords, and both hooks now use `logger.JSONScrubberFunc`.

The comment claiming this is `NON PRODUCTION ENVIRONMENT ONLY` is corrected — this is the transport the production binary uses.

## 2. The error was written twice in the same entry

```go
ctxLogger.Error().Err(err).Msgf("error create event: %v", err)
```

`Err(err)` already attaches the error as a structured field. Interpolating it into the message as well means the message text differs on every occurrence, so Datadog cannot group these into one pattern and a log query cannot match on the message.

It now reads `could not create audit event` with the error in its own field.

## Left alone deliberately

**`signature verification failed`** — 25 entries a week, at error. An audit event arriving with a signature that does not verify is exactly what this service exists to notice. It belongs at error, and it needs someone to look at who is sending them. It is not a logging defect and I have not touched it.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## Implementation status

**Pull request: [bravo-audit-trail-service#36](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-audit-trail-service/tree/fix/logging), head `810a394`, branched from `master` at `043f1b8`.

[Files changed](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36/files) · [Commits](https://github.com/bfi-finance/bravo-audit-trail-service/pull/36/commits) · [Compare against master](https://github.com/bfi-finance/bravo-audit-trail-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 3 |

Commits:

- fix(logging): mask outbound bodies, and say what the error was

Files:

- `cmd/grpc/main.go`
- `internal/config/config.go`
- `internal/rabbitmq/event/event_consumer.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches

It found a real defect in this change: a `gofmt` comment-alignment miss in `internal/config/config.go`. Fixed on the branch.

Unit tests beyond those shipped with this change have not been run, and nothing has
been exercised against a running dependency. CI remains the authority.

---|---|
| Commits | 1 |
| Files changed | 3 |

Commits:

- fix(logging): mask outbound bodies, and say what the error was

Files:

- `cmd/grpc/main.go`
- `internal/config/config.go`
- `internal/rabbitmq/event/event_consumer.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches

It found a real defect in this change: a `gofmt` comment-alignment miss in `internal/config/config.go`. Fixed on the branch.

Unit tests beyond those shipped with this change have not been run, and nothing has
been exercised against a running dependency. CI remains the authority.

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
