# gold-service — logging findings and fixes

**Squad:** Irvan Setiawan  
**Production service:** `prod-ms-gold-service`  
**Stack:** Go, zerolog, HTTP, RabbitMQ, bfi-go-pkg  
**Production volume:** 9,387 warn, 8,087 info, 34 error, 1 emergency a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-gold-service` writes 9,387 warn, 8,087 info, 34 error over the 7 days to 13 September 2026.

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

Read from `app-deployment/gold-service/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `debug`  ← **debug in production** |
| Postgres log level | `debug`  ← **debug in production** |
| `HTTP_SERVER_BODY_LOGGING` | `TRUE` |
| `HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY` | `TRUE` |
| `HTTP_SERVER_REQUEST_BODY_LOGGING` | `TRUE` |
| `HTTP_SERVER_RESPONSE_BODY_LOGGING` | `TRUE` |
| `HTTP_CLIENT_BODY_LOGGING` | `TRUE` |
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `TRUE` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `TRUE` |
| `HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS` | `password,ktp_number,phone_number,account_number,mothers_m…` (5 fields) |
| `HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS` | `ktp_number,phone_number,account_number,mothers_maiden_name` |
| `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` | `password,secret,token` |
| `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` | `password,secret,token` |

Bodies are logged in production **with a masked-field list set here** — the pattern SRE asks for. The list is the squad's to keep current.
**`LOGGER_LEVEL` is `debug` in production.** Every debug statement in the service ships to Cloud Logging and Datadog. This is the single cheapest change available for this service.

**Proposed change to this file:** section §1 of [deployment-proposal.md](deployment-proposal.md) — raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on 14 September 2026 (branch `fix/logging`), awaiting SRE review.

---

## Implementation status

**Scope of [#190](https://github.com/bfi-finance/gold-service/pull/190) was reduced on 14 September 2026, on SRE's guidance.** The commit that gave the `*_JSON_MASKED_FIELDS` config fields a default list was reverted; masked fields are set per environment in `app-deployment`, not defaulted in code. What remains is the code the deployment setting depends on — the scrubber actually wired to the field list the environment provides — and any log-level fixes.

**Pull request: [gold-service#190](https://github.com/bfi-finance/gold-service/pull/190)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/gold-service/tree/fix/logging), head `79cbef4`, branched from `master` at `0a816c1`.

[Files changed](https://github.com/bfi-finance/gold-service/pull/190/files) · [Commits](https://github.com/bfi-finance/gold-service/pull/190/commits) · [Compare against master](https://github.com/bfi-finance/gold-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 3 |
| Files changed | 2 |

Commits:

- fix(logging): an agreement that is not a gold loan is not a warning
- fix(logging): mask request and response bodies by default
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance)*

Files:

- `internal/config/http.go`
- `internal/event/subscriber/handler/agreementstatusupdate.go`

**CI caught a real defect in this change and it has been fixed:** gofmt rejected the `//nolint:lll` directive placed directly under a doc comment; since Go 1.19 it needs a blank `//` line before it. **Now green.** Full list in [README.md](README.md#what-ci-said-about-pack-two).

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
