# bravo-supplier-service — logging findings and fixes

> **Superseded on 14 September 2026.** The code change this file describes — a default masked-field list in the config struct — was reverted and its pull request closed on SRE's guidance: masked fields are set **per service and per environment in `app-deployment`**, not defaulted in code. The finding stands; the fix moves. See *In the production deployment* below for what the manifest actually sets, and [deployment-proposal.md](deployment-proposal.md) for the diff if one is needed.

**Squad:** Supplier Platform  
**Production service:** `prod-ms-supplier`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** 126,795 info, 1,591 warn, 8 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-supplier` writes 126,795 info, 1,591 warn, 8 error over the 7 days to 13 September 2026.

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

Read from `app-deployment/supplier/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `debug`  ← **debug in production** |
| Postgres log level | `info` |
| `GRPC_SERVER_REQUEST_BODY_LOGGING` | `true` |
| `GRPC_SERVER_RESPONSE_BODY_LOGGING` | `true` |
| `GRPC_SERVER_BODY_LOGGING_ON_ERROR_ONLY` | `false` |

Bodies are logged in production and **no masked-field variable is set at all**, so the scrubber list is whatever the code defaults to — which is empty.
`*_BODY_LOGGING_ON_ERROR_ONLY` is `false`: **every** request and response body is written, not only those of failed calls.
**`LOGGER_LEVEL` is `debug` in production.** Every debug statement in the service ships to Cloud Logging and Datadog. This is the single cheapest change available for this service.

**Proposed change to this file:** section §1 of [deployment-proposal.md](deployment-proposal.md) — raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on 14 September 2026 (branch `fix/logging`), awaiting SRE review.

---

## Implementation status

**Pull request [#181](https://github.com/bfi-finance/bravo-supplier-service/pull/181) was closed on 14 September 2026, on SRE's guidance.** Its only change gave the `*_JSON_MASKED_FIELDS` config fields a default list in the struct tag. Masked fields are a per-service, per-environment setting made in `app-deployment`, not a default in every service's code — not every service handles PII, and each needs its own field list. The default was reverted on the branch, which left it identical to the base branch, so the pull request was closed rather than left open with no diff. What production actually sets is in **In the production deployment** below; the wrapper-side change is [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175).

**Pull request: [bravo-supplier-service#181](https://github.com/bfi-finance/bravo-supplier-service/pull/181)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-supplier-service/tree/fix/logging), head `b36e1f4`, branched from `master` at `77d44a8`.

[Files changed](https://github.com/bfi-finance/bravo-supplier-service/pull/181/files) · [Commits](https://github.com/bfi-finance/bravo-supplier-service/pull/181/commits) · [Compare against master](https://github.com/bfi-finance/bravo-supplier-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 1 |

Commits:

- fix(logging): mask request and response bodies by default
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance; branch now identical to base, pull request closed)*

Files:

- `internal/config/config.go`

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
