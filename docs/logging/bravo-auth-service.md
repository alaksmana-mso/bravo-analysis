# bravo-auth-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-auth`  
**Stack:** Go, zap, gRPC, ent  
**Production volume:** 16,934 error, 837 warn, 3 info a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-auth` writes 17,192 log entries a week. **16,934 of them are error — 98.5%.** There are **3** info entries in seven days. Measured in Datadog over the 7 days to 13 September 2026.

Sampled error messages:

| Message | Real meaning |
|---|---|
| `could not authorized application_id with refresh token` | 401 |
| `wrong OTP` | 400 |
| `refresh token is already expired` | 401 |
| `too many request` | 429 |
| `unauthorized to perform the action` | 403 |

A wrong OTP is the system working.

## The cause is one function

`Error.Write` in `app/auth/pkg/error.go` takes an HTTP status code and then logs at error whatever that code is:

```go
func (e *Error) Write(ctx context.Context, code int, message error, details interface{}) Error {
    ...
    log.ErrorX(ctx, e.Message.Error(), tag.Any("code", code), tag.Any("details", details))
```

Every 4xx in the service goes through it.

## What this PR changes

`Write` now picks its level from the code — **4xx at warn, 5xx still at error**:

```go
logAt := log.ErrorX
if code >= http.StatusBadRequest && code < http.StatusInternalServerError {
    logAt = log.WarnX
}
```

That is the whole change to error handling. The response, the status and the body are untouched.

**`internal/lib/log` gains `WarnX`**, mirroring `ErrorX`. This matters: `ErrorX` attaches `dd.trace_id`, `dd.span_id` and the correlation ID, and plain `Warn` does not. Moving these lines to `Warn` would have silently dropped their trace correlation.

## Two stray prints

`internal/lib/server/http/server.go` printed `fmt.Println("Path log => ", p)` on every swagger file request — one line above a `log.Info` that says the same thing properly. Removed.

`internal/pkg/errors/errors.go` used `fmt.Print(e)` to report a failure to attach bad-request details: an unlabelled, unlevelled line on stdout that no log query could find. It now logs at error with the error attached.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `bfi-app-deployment/auth/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Logging variables | none of the shared-library switches are set; the wrapper defaults apply |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## Implementation status

**Pull request: [bravo-auth-service#258](https://github.com/bfi-finance/bravo-auth-service/pull/258)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-auth-service/tree/fix/logging), head `c8fe6fa`, branched from `master` at `6dc643b`.

[Files changed](https://github.com/bfi-finance/bravo-auth-service/pull/258/files) · [Commits](https://github.com/bfi-finance/bravo-auth-service/pull/258/commits) · [Compare against master](https://github.com/bfi-finance/bravo-auth-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 4 |

Commits:

- fix(logging): pick the log level from the status code

Files:

- `app/auth/pkg/error.go`
- `internal/lib/log/log.go`
- `internal/lib/server/http/server.go`
- `internal/pkg/errors/errors.go`

**CI caught a real defect in this change and it has been fixed:** removing `fmt.Print(e)` left the `fmt` import unused. My own check for remaining uses matched the word inside the comment I had just written. Full list in [README.md](README.md#what-ci-said-about-pack-two).

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

- [ ] Run CI on the pull request — see the verification note above for what was and was not checked locally
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
