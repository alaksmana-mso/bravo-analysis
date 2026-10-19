# notification-service — logging findings and fixes

> **Superseded on 14 September 2026.** The code change this file describes — a default masked-field list in the config struct — was reverted and its pull request closed on SRE's guidance: masked fields are set **per service and per environment in `app-deployment`**, not defaulted in code. The finding stands; the fix moves. See *In the production deployment* below for what the manifest actually sets, and [deployment-proposal.md](deployment-proposal.md) for the diff if one is needed.

**Squad:** Internal Service  
**Production service:** `prod-ms-notification`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** not production-active under this name — prod-ms-notification is bravo-notification-service

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---


> **Mapping correction.** `coverage.md` listed this repository against `prod-ms-notification`. Datadog's `git.repository_url` tag on that service says it is built from **`bravo-notification-service`**, which is covered separately. The change in this pull request is still correct hygiene — the masked-field lists here default to empty — but this repository is not the one behind that production volume.

## What production shows

`prod-ms-notification` writes 9,499 error, 63 warn, 8 info over the 7 days to 13 September 2026.

This PR is about what those entries can contain, not how many there are.

## What this PR changes

**The masked-field lists defaulted to empty**, so an unset deployment masked nothing. They now default to a list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords. `.env.example` matches where present.

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

Read from `app-deployment/notification/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `true` |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service serves gRPC behind the wrapper's REST proxy. Today the proxy drops the gateway's `x-bfi-req-id` (the service does not whitelist it, and none does), so `loggerinterceptor` mints a second id and the id a client holds is not the id in these logs. bfi-go-pkg#185, merged on 19 October 2026, fixes that inside the proxy; the service only bumps. After the bump the id is on the span as `request_id`, and outgoing HTTP calls through `httpclient` forward it automatically. On 12 October its `master` used bfi-go-pkg `2c9abfad290e` (8 June 2026); all of this arrives when it bumps bfi-go-pkg to `3026177` or later, the `main` commit that includes [bfi-go-pkg#185](https://github.com/bfi-finance/bfi-go-pkg/pull/185) (merged 19 October 2026): `go get github.com/bfi-finance/bfi-go-pkg@3026177`.

**Masking on by default (20 October 2026).** The same bump turns on default body masking ([bfi-go-pkg#186](https://github.com/bfi-finance/bfi-go-pkg/pull/186), merged 19 October). Any body or query string this service logs through the wrapper's middleware, interceptor or `LoggedTransport` is masked with the baseline `DEFAULT_LOG_SENSITIVE_KEYS` plus this service's own `LOG_SENSITIVE_KEYS` and `*_BODY_JSON_MASKED_FIELDS` lists. The baseline applies once the service's manifest carries `DEFAULT_LOG_SENSITIVE_KEYS`; the pull requests that add it are still open. Details: [Masking on by default in the libraries](README.md#masking-on-by-default-in-the-libraries).

What is left for the squad after the bump:

- **gRPC dials** (1 file): add `grpc.WithChainUnaryInterceptor(loggerinterceptor.UnaryClient())` to the dial options; the wrapper cannot do this for a `grpc.NewClient` call.
- **Error bodies:** opt in with `errorinterceptor.WithRequestInfoDetail()` and `panicinterceptor.WithRequestInfoDetail()` once the squad has checked that no caller rejects an unknown `@type` in the error details. The REST proxy renders the same detail for REST callers.

## Implementation status

**Pull request [#122](https://github.com/bfi-finance/notification-service/pull/122) was closed on 14 September 2026, on SRE's guidance.** Its only change gave the `*_JSON_MASKED_FIELDS` config fields a default list in the struct tag. Masked fields are a per-service, per-environment setting made in `app-deployment`, not a default in every service's code — not every service handles PII, and each needs its own field list. The default was reverted on the branch, which left it identical to the base branch, so the pull request was closed rather than left open with no diff. What production actually sets is in **In the production deployment** below; the wrapper-side change, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175), merged on 8 October 2026. On 12 October this service's `master` used bfi-go-pkg `2c9abfad290e` (8 June 2026), which masks string values only. Numbers such as a NIK or an amount stay in clear until the service bumps bfi-go-pkg to `d7d3ca2a00f8` or later.

**Pull request: [notification-service#122](https://github.com/bfi-finance/notification-service/pull/122)** — closed 14 September 2026 (see above).  
Branch: [`fix/logging`](https://github.com/bfi-finance/notification-service/tree/fix/logging), head `fbf34eb`, branched from `master` at `0343458`.

[Files changed](https://github.com/bfi-finance/notification-service/pull/122/files) · [Commits](https://github.com/bfi-finance/notification-service/pull/122/commits) · [Compare against master](https://github.com/bfi-finance/notification-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 1 |

Commits:

- fix(logging): mask request and response bodies by default
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance; branch now identical to base, pull request closed)*

Files:

- `.env.example`

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
