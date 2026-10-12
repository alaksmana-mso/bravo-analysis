# bravo-backoffice-service — logging findings and fixes

> **Superseded on 14 September 2026.** The code change this file describes — a default masked-field list in the config struct — was reverted and its pull request closed on SRE's guidance: masked fields are set **per service and per environment in `app-deployment`**, not defaulted in code. The finding stands; the fix moves. See *In the production deployment* below for what the manifest actually sets, and [deployment-proposal.md](deployment-proposal.md) for the diff if one is needed.

**Squad:** Direct Marketing  
**Production service:** `prod-ms-backoffice`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** 9,158 warn, 1,311 info, 87 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-backoffice` writes 9,158 warn, 1,311 info, 87 error over the 7 days to 13 September 2026.

This PR is about what those entries can contain, not how many there are.

## What this PR changes

**`BODY_LOGGING_ON_ERROR_ONLY` was false**, so bodies were written on every call rather than only on failures. It is now true, matching the other services.

## For whoever deploys this

`envDefault` only applies when the variable is **unset**. If the production manifest sets these variables explicitly, those values still win and need changing there too. I cannot see the deployment manifests from here.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `app-deployment/backoffice/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `warn` |
| Postgres log level | `info` |
| `HTTP_SERVER_BODY_LOGGING` | `true` |
| `HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY` | `false` |
| `HTTP_SERVER_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_SERVER_RESPONSE_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `true` |
| `GENERIC_JSON_MASKED_FIELDS` | `access_token,accessKey,account_number,address,address_det…` (44 fields) |
| `PHONE_JSON_MASKED_FIELDS` | `alternate_phone,customer_phone,phone,phone_number,additio…` (10 fields) |

Bodies are logged in production **with a masked-field list set here** — the pattern SRE asks for. The list is the squad's to keep current.
`*_BODY_LOGGING_ON_ERROR_ONLY` is `false`: **every** request and response body is written, not only those of failed calls.

---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service serves gRPC behind the wrapper's REST proxy. Today the proxy drops the gateway's `x-bfi-req-id` (the service does not whitelist it, and none does), so `loggerinterceptor` mints a second id and the id a client holds is not the id in these logs. The bfi-go-pkg release with #185 fixes that inside the proxy; the service only bumps. After the bump the id is on the span as `request_id`, and outgoing HTTP calls through `httpclient` forward it automatically. On 12 October its `master` used bfi-go-pkg `27dfd20afa55` (24 August 2026); all of this arrives with the bump to the release that includes [bfi-go-pkg#185](https://github.com/bfi-finance/bfi-go-pkg/pull/185).

What is left for the squad after the bump:

- **gRPC dials** (2 files): add `grpc.WithChainUnaryInterceptor(loggerinterceptor.UnaryClient())` to the dial options; the wrapper cannot do this for a `grpc.NewClient` call.
- **Error bodies:** opt in with `errorinterceptor.WithRequestInfoDetail()` and `panicinterceptor.WithRequestInfoDetail()` once the squad has checked that no caller rejects an unknown `@type` in the error details. The REST proxy renders the same detail for REST callers.
- **Already forwarding:** this service sets `x-bfi-req-id` on outgoing calls in its own code. That code can go once the wrapper does it; until then it is harmless.

## Implementation status

**Pull request [#2781](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781) was closed on 14 September 2026, on SRE's guidance.** Its only change gave the `*_JSON_MASKED_FIELDS` config fields a default list in the struct tag. Masked fields are a per-service, per-environment setting made in `app-deployment`, not a default in every service's code — not every service handles PII, and each needs its own field list. The default was reverted on the branch, which left it identical to the base branch, so the pull request was closed rather than left open with no diff. What production actually sets is in **In the production deployment** below; the wrapper-side change, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175), merged on 8 October 2026. On 12 October this service's `master` used bfi-go-pkg `27dfd20afa55` (24 August 2026), which masks string values only. Numbers such as a NIK or an amount stay in clear until the service bumps bfi-go-pkg to `d7d3ca2a00f8` or later.

**Pull request: [bravo-backoffice-service#2781](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781)** — closed 14 September 2026 (see above).  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-backoffice-service/tree/fix/logging), head `a1536ee64`, branched from `master` at `36e171f19`.

[Files changed](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781/files) · [Commits](https://github.com/bfi-finance/bravo-backoffice-service/pull/2781/commits) · [Compare against master](https://github.com/bfi-finance/bravo-backoffice-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 2 |

Commits:

- fix(logging): mask request and response bodies by default
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance; branch now identical to base, pull request closed)*

Files:

- `.env.example`
- `CHANGELOG.md`

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
