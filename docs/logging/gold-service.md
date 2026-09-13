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

## Implementation status

**Pull request: [gold-service#190](https://github.com/bfi-finance/gold-service/pull/190)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/gold-service/tree/fix/logging), head `79cbef4`, branched from `master` at `0a816c1`.

[Files changed](https://github.com/bfi-finance/gold-service/pull/190/files) · [Commits](https://github.com/bfi-finance/gold-service/pull/190/commits) · [Compare against master](https://github.com/bfi-finance/gold-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 2 |

Commits:

- fix(logging): an agreement that is not a gold loan is not a warning
- fix(logging): mask request and response bodies by default

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

---|---|
| Commits | 2 |
| Files changed | 2 |

Commits:

- fix(logging): an agreement that is not a gold loan is not a warning
- fix(logging): mask request and response bodies by default

Files:

- `internal/config/http.go`
- `internal/event/subscriber/handler/agreementstatusupdate.go`

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
