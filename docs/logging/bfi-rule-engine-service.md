# bfi-rule-engine-service — logging findings and fixes

**Squad:** Digital Partnership  
**Production service:** `prod-ms-rule-engine`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** 76,590 info, 4 warn, 1 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-rule-engine` is one of the quietest and best-behaved log producers in the estate: **76,590 info, 4 warn, 1 error** over the 7 days to 13 September 2026, and **zero** entries carrying an HTTP body.

This PR is not about volume. It closes a gap.

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

Body logging is on, with a 32 KiB limit on each side and **no masking function**. Because `WithBodyLoggingOnErrorOnly` is true, bodies are only written when a downstream call returns 4xx or 5xx. That is why nothing is leaking today — this service's downstream calls are succeeding.

On a bad week, every failing outbound call would write up to 64 KiB of unmasked request and response body into the log stream.

## What this PR changes

`WithRequestBodyLoggingFunc` and `WithResponseBodyLoggingFunc` already exist in `bfi-go-pkg`, and `logger.JSONScrubberFunc` is the masking function the other Go services use — `bravo-kyc-proxy` wires exactly this pattern. They were simply never wired up here.

```go
httpclient.WithRequestBodyLoggingFunc(logger.JSONScrubberFunc(httpBodyMaskedFields)),
httpclient.WithRequestBodyLoggingLimit(4096),   // was 32768
```

Plus a `httpBodyMaskedFields` list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords.

Nothing else in this service needs changing.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `app-deployment/rule-engine/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `info` |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service serves gRPC behind the wrapper's REST proxy. Today the proxy drops the gateway's `x-bfi-req-id` (the service does not whitelist it, and none does), so `loggerinterceptor` mints a second id and the id a client holds is not the id in these logs. The bfi-go-pkg release with #185 fixes that inside the proxy; the service only bumps. After the bump the id is on the span as `request_id`, and outgoing HTTP calls through `httpclient` forward it automatically. On 12 October its `master` used bfi-go-pkg `003983f388a6` (28 September 2026); all of this arrives with the bump to the release that includes [bfi-go-pkg#185](https://github.com/bfi-finance/bfi-go-pkg/pull/185).

What is left for the squad after the bump:

- **gRPC dials** (1 file): add `grpc.WithChainUnaryInterceptor(loggerinterceptor.UnaryClient())` to the dial options; the wrapper cannot do this for a `grpc.NewClient` call.
- **Error bodies:** opt in with `errorinterceptor.WithRequestInfoDetail()` and `panicinterceptor.WithRequestInfoDetail()` once the squad has checked that no caller rejects an unknown `@type` in the error details. The REST proxy renders the same detail for REST callers.

## Implementation status

**Update, 14 September 2026 — on SRE's guidance, the field list now comes from the environment.** The first version of this branch hardcoded the masked-field list in `main.go`. Masked fields are a per-service, per-environment setting made in `app-deployment`, so the list is now read from `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` and `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` — the names every other Go service uses — and the body limits go back to the 32 KiB master already had. The scrubber stays wired, which is the part master lacked: outbound bodies logged on a failed call went through no scrubber at all. Until `app-deployment` sets those two variables for this service the list is empty and the behaviour is master's; the proposed values are in [deployment-proposal.md](deployment-proposal.md).

Side finding from reading the manifest: this service reads its HTTP client timeouts from `HTTPCLIENT_*` while production sets `HTTP_CLIENT_*`, so those timeouts have never been applied. Not changed here — it is a behaviour change the squad should make knowingly.

Wrapper-side counterpart: https://github.com/bfi-finance/bfi-go-pkg/pull/175, merged on 8 October 2026. The non-string masking itself came with bfi-go-pkg#182 on 30 September.

**Pull request: [bfi-rule-engine-service#67](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67)** — **merged 17 September 2026** by the squad. In production since 1 October (`v1.1.0`).
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-rule-engine-service/tree/fix/logging), head `ae5ae3c`, branched from `master` at `00ef5f8`.

[Files changed](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67/files) · [Commits](https://github.com/bfi-finance/bfi-rule-engine-service/pull/67/commits) · [Compare against master](https://github.com/bfi-finance/bfi-rule-engine-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request. The Go wrapper fix, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175), merged on 8 October 2026. Together with bfi-go-pkg#182 (30 September), `JSONScrubber` now masks every value under a masked key, including numbers. On 12 October this service's `master` used bfi-go-pkg `003983f388a6` (28 September 2026), which masks string values only. Numbers such as a NIK or an amount stay in clear until the service bumps bfi-go-pkg to `d7d3ca2a00f8` or later. The masked-field lists stay a per-service, per-environment setting in `app-deployment`, as SRE asked on 14 September.

CI on the current head is **fully green**.

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
