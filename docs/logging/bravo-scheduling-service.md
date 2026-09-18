# bravo-scheduling-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-scheduling`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** 46,924 info, 5,996 warn, 1,759 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-scheduling` writes 46,924 info, 5,996 warn and 1,759 error entries a week. Volume is not this service's problem.

**391 of those entries carry a full HTTP request or response body, unmasked.** Measured in Datadog over the 7 days to 13 September 2026.

## The gap

`cmd/grpc/main.go` builds the shared logged transport like this:

```go
httpclient.WithBodyLogging(true),
httpclient.WithBodyLoggingOnErrorOnly(true),
httpclient.WithRequestBodyLogging(true),
httpclient.WithRequestBodyLoggingLimit(32768),
httpclient.WithResponseBodyLogging(true),
httpclient.WithResponseBodyLoggingLimit(32768),
```

Body logging is on, with a 32 KiB limit on each side and **no masking function**. Bodies are written whenever a downstream call returns 4xx or 5xx — which is what those 391 entries are.

## What this PR changes

`WithRequestBodyLoggingFunc` and `WithResponseBodyLoggingFunc` already exist in `bfi-go-pkg`, and `logger.JSONScrubberFunc` is the masking function the other Go services use — `bravo-kyc-proxy` wires exactly this pattern. They were never wired up here.

```go
httpclient.WithRequestBodyLoggingFunc(logger.JSONScrubberFunc(httpBodyMaskedFields)),
httpclient.WithRequestBodyLoggingLimit(4096),   // was 32768
```

Plus a `httpBodyMaskedFields` list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `app-deployment/scheduling/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `info` |
| Postgres log level | `warn` |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## Implementation status

**Update, 14 September 2026 — on SRE's guidance, the field list now comes from the environment.** The first version of this branch hardcoded the masked-field list in `main.go`. Masked fields are a per-service, per-environment setting made in `app-deployment`, so the list is now read from `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` and `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` — the names every other Go service uses — and the body limits go back to the 32 KiB master already had. The scrubber stays wired, which is the part master lacked: outbound bodies logged on a failed call went through no scrubber at all. Until `app-deployment` sets those two variables for this service the list is empty and the behaviour is master's; the proposed values are in [deployment-proposal.md](deployment-proposal.md).

Side finding from reading the manifest: this service reads its HTTP client timeouts from `HTTPCLIENT_*` while production sets `HTTP_CLIENT_*`, so those timeouts have never been applied. Not changed here — it is a behaviour change the squad should make knowingly.

Wrapper-side counterpart: https://github.com/bfi-finance/bfi-go-pkg/pull/175 (masks non-string values).

**Pull request: [bravo-scheduling-service#300](https://github.com/bfi-finance/bravo-scheduling-service/pull/300)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-scheduling-service/tree/fix/logging), head `f8dfc27`, branched from `master` at `2f839d8`.

[Files changed](https://github.com/bfi-finance/bravo-scheduling-service/pull/300/files) · [Commits](https://github.com/bfi-finance/bravo-scheduling-service/pull/300/commits) · [Compare against master](https://github.com/bfi-finance/bravo-scheduling-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request. The Go wrapper fix, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) (`JSONScrubber` masks non-string values), is still open; the masked-field lists stay a per-service, per-environment setting in `app-deployment`, as SRE asked on 14 September.

CI on the current head is **fully green**.

**Codacy review, answered 18 September 2026.** 2 Codacy thread(s); 2 declined with the reason in the thread. Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): mask outbound HTTP bodies before they reach the log stream

Files:

- `cmd/grpc/main.go`

**Compiled, formatted and linted locally.** An earlier version of this file said no
Go toolchain was available on the machine this analysis ran on. That was wrong — Go is
installed via `mise`. What has been run on this branch:

- `go build ./...` — passes
- `gofmt` — clean on every file this branch touches
- `golangci-lint` against this repository's own `.golangci.yml` — clean on the files
this branch touches

It found a real defect in this change: `gochecknoglobals` on the masked-field list. Fixed on the branch.

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
