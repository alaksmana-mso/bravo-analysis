# bravo-gen-ai — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-gen-ai`  
**Stack:** Go, zerolog, gRPC, bfi-go-pkg  
**Production volume:** 31,714 info, 837 error, 569 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-gen-ai` writes 31,714 info, 837 error and 569 warn over the 7 days to 13 September 2026.

This PR is about what those entries can contain, not how many there are.

## The gap

The `*_JSON_MASKED_FIELDS` variables are read from the environment and handed to the JSON scrubber — the wiring is correct — but **they had no default**. An unset deployment therefore masked nothing at all: the scrubber ran with an empty field list.

```go
HTTPClientRequestBodyJSONMaskedField string `env:"HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS"`
```

They now default to a list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords.

## For whoever deploys this

`envDefault` only applies when the variable is **unset**. If the production manifest sets these explicitly, those values still win and need changing there too. I cannot see the deployment manifests from here.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## Implementation status

**Pull request: [bravo-gen-ai#359](https://github.com/bfi-finance/bravo-gen-ai/pull/359)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-gen-ai/tree/fix/logging), head `4a7fb8a`, branched from `master` at `59986b9`.

[Files changed](https://github.com/bfi-finance/bravo-gen-ai/pull/359/files) · [Commits](https://github.com/bfi-finance/bravo-gen-ai/pull/359/commits) · [Compare against master](https://github.com/bfi-finance/bravo-gen-ai/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): give the masked-field lists a default

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

---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): give the masked-field lists a default

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

- [ ] Run CI on the pull request — nothing here was compiled or tested
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
