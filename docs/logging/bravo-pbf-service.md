# bravo-pbf-service — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-ms-pbf`  
**Stack:** Go, zerolog, gRPC, RabbitMQ, bfi-go-pkg  
**Production volume:** 40,024 error, 1,042 warn, no info at all

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

**97% of this service's log volume is a single line.**

`prod-ms-pbf` writes 41,065 log entries a week. 40,024 are `error`. Of those, **40,021 are the message `sql: no rows in result set`**, from `@module:agreement.agreement-status-update-fo`. There is no `info` at all — the production logger level is `warn`.

Measured in Datadog over the 7 days to 13 September 2026.

## The cause

`handle()` in `internal/rabbitmq/agreement/work_consumer.go`:

```go
agreementID, err := g.agreementStore.GetAgreementIDByAgreementNumber(ctx, parsedMsg.AgreementNumber)
if err != nil {
    return err          // sql.ErrNoRows goes straight through
}
```

The store returns `sql.ErrNoRows` when this service does not hold the agreement. The error handler discards the message and logs `err.Error()` at error level.

The very next function in the same file already knows better:

```go
if errors.Is(err, sql.ErrNoRows) {
    return nil
}
```

The lookup never learned the same rule. This service holds a subset of agreements; a status update for one it does not hold is the normal case.

## What this PR changes

**`rmqcommon` gains `ErrNotApplicable`.** A message marked with it takes **exactly the same action as before — discard** — but is logged at debug rather than error:

```go
switch {
case errors.Is(err, ErrNotApplicable):
	ctxLogger.Debug().Err(err).Msg(err.Error())
case action == ActionDiscard:
	ctxLogger.Err(err).Msg(err.Error())
default:
	ctxLogger.Warn().Err(err).Msg(err.Error())
}
```

The action is deliberately left alone so this stays a logging change.

**The agreement consumer names the agreement.** `sql: no rows in result set` told a reader nothing — not which agreement, not which queue, not why. It now reads `message not applicable to this service: agreement <number> is not held by this service`.

**The per-message info line stops re-marshalling the payload.** It rebuilt the whole message as JSON and logged it back out with a stray `\n`. It now logs the agreement number and status, at debug.

## What this PR deliberately does not change

Whether these 40,000 messages a week should be **acked rather than dead-lettered**. `ActionDiscard` maps to `NackDiscard`, so every one of them is currently dead-lettered; an ack would also record an idempotency key. Acking is arguably the correct semantics for "understood, nothing to do" — but it is a message-handling decision for this squad, not something a logging pass should slip in.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## Implementation status

**Pull request: [bravo-pbf-service#125](https://github.com/bfi-finance/bravo-pbf-service/pull/125)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-pbf-service/tree/fix/logging), head `4f4c69c`, branched from `master` at `0102be3`.

[Files changed](https://github.com/bfi-finance/bravo-pbf-service/pull/125/files) · [Commits](https://github.com/bfi-finance/bravo-pbf-service/pull/125/commits) · [Compare against master](https://github.com/bfi-finance/bravo-pbf-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 4 |

Commits:

- fix(logging): default the masked-field lists instead of leaving them empty
- fix(logging): stop reporting "agreement not held here" as an error

Files:

- `.env.example`
- `internal/config/config.go`
- `internal/rabbitmq/agreement/work_consumer.go`
- `internal/rabbitmq/rmqcommon/error_handler.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches

Unit tests beyond those shipped with this change have not been run, and nothing has
been exercised against a running dependency. CI remains the authority.

---|---|
| Commits | 2 |
| Files changed | 4 |

Commits:

- fix(logging): default the masked-field lists instead of leaving them empty
- fix(logging): stop reporting "agreement not held here" as an error

Files:

- `.env.example`
- `internal/config/config.go`
- `internal/rabbitmq/agreement/work_consumer.go`
- `internal/rabbitmq/rmqcommon/error_handler.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches

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
