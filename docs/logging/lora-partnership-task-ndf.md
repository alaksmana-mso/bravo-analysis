# lora-partnership-task-ndf — logging findings and fixes

**Squad:** LORA Core  
**Production service:** `prod-lora-partnership-task-ndf`  
**Stack:** Go, zerolog, Temporal, bfi-go-pkg  
**Production volume:** 32,640 warn, 3,512 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-lora-partnership-task-ndf` writes 32,640 warn, 3,512 error over the 7 days to 13 September 2026.

This PR is about what those entries can contain, not how many there are.

## What this PR changes

**The masking function was commented out.** The client body logger was built like this:

```go
httpclient.WithRequestBodyLoggingLimit(e.HTTPClientRequestBodyLogLimit),
// httpclient.WithRequestBodyLoggingFunc(),
```

`HTTPClientRequestBodyJSONMaskedFields` is parsed from the environment and then never used, so configuring it had no effect at all. Both hooks are now wired to `logger.JSONScrubberFunc`, the same helper the rest of the Go estate uses.

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

Read from `app-deployment/lora-partnership-task-ndf/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `info` |
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `false` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `false` |
| `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |
| `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

---

## Implementation status

**Scope of [#2126](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126) was reduced on 14 September 2026, on SRE's guidance.** The commit that gave the `*_JSON_MASKED_FIELDS` config fields a default list was reverted; masked fields are set per environment in `app-deployment`, not defaulted in code. What remains is the code the deployment setting depends on — the scrubber actually wired to the field list the environment provides — and any log-level fixes.

**Pull request: [lora-partnership-task-ndf#2126](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/lora-partnership-task-ndf/tree/fix/logging), head `503128e3`, branched from `master` at `f969f899`.

[Files changed](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126/files) · [Commits](https://github.com/bfi-finance/lora-partnership-task-ndf/pull/2126/commits) · [Compare against master](https://github.com/bfi-finance/lora-partnership-task-ndf/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 1 |

Commits:

- fix(logging): mask request and response bodies by default
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance)*

Files:

- `internal/config/config.go`

**CI caught a real defect in this change and it has been fixed:** the shared logger import had to be aliased (`bfilogger`), and then `Env.Logger()` in the same file needed the alias too. Full list in [README.md](README.md#what-ci-said-about-pack-two).

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
