# lora-gateway-service — logging findings and fixes

**Squad:** LORA Core  
**Production service:** `prod-lora-gateway`  
**Stack:** Go, zerolog, HTTP proxy, bfi-go-pkg  
**Production volume:** 65,646 warn, 17,265 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-lora-gateway` writes **69,433 log entries a week carrying a full HTTP request or response body** — the second highest in the estate, behind only `prod-ms-partnership`. Measured in Datadog over the 7 days to 13 September 2026.

Total volume: 65,646 warn and 17,265 error.

## Two causes, both in `internal/config/http.go`

### 1. The masking function was commented out

```go
httpclient.WithRequestBodyLogging(e.HTTPClientRequestBodyLogging),
httpclient.WithRequestBodyLoggingLimit(e.HTTPClientRequestBodyLogLimit),
// httpclient.WithRequestBodyLoggingFunc(),          <-- never wired
// HTTP client response body logger (NON PRODUCTION ENVIRONMENT ONLY)
httpclient.WithResponseBodyLogging(e.HTTPClientResponseBodyLogging),
httpclient.WithResponseBodyLoggingLimit(e.HTTPClientResponseBodyLogLimit),
// httpclient.WithResponseBodyLoggingFunc(),         <-- never wired
```

`HTTPClientRequestBodyJSONMaskedFields` is parsed from the environment and then **never used**. Configuring it had no effect at all.

The server side of this same service wires it correctly — `internal/httpserver/server.go:45` calls `logger.JSONScrubberFunc(cfg.HTTPServerRequestBodyJSONMaskedFields)`. Only the client side was left commented. Both are now wired the same way.

### 2. Bodies were logged on every call, not just failures

```go
HTTPClientBodyLoggingOnErrorOnly bool `env:"HTTP_CLIENT_BODY_LOGGING_ON_ERROR_ONLY" envDefault:"false"`
```

The server-side equivalent defaults to `true`. The client now matches it. This is the volume lever.

### The comment was wrong

`// HTTP client request body logger (NON PRODUCTION ENVIRONMENT ONLY)` — it is running in production, 69,433 times a week. The comment is corrected rather than left to mislead the next reader.

## Also: empty masking defaults

All four `*_BODY_JSON_MASKED_FIELDS` variables had empty defaults, so an unset deployment masked nothing. They now default to a list covering account numbers and names, identity numbers, NIK, NPWP, dates and places of birth, email, phone, salary, tokens and passwords. `.env.example` matches.

## For whoever deploys this

`envDefault` only applies when the variable is **unset**. If the production manifest sets `HTTP_CLIENT_BODY_LOGGING_ON_ERROR_ONLY` or the masked-field lists explicitly, those values still win and need changing there too. I cannot see the deployment manifests from here.

## Please build before merging

**Compiled, formatted and linted locally.** Go is available on this machine through `mise`; an
earlier version of this file said otherwise, which was wrong. On this branch: `go build ./...`
passes, `gofmt` is clean on every changed file, and `golangci-lint` against this repository's own `.golangci.yml` — clean on the files this
branch touches. Unit tests beyond any shipped with
this change have not been run — CI remains the authority.

---

## In the production deployment

Read from `app-deployment/lora-gateway/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `info` |
| `HTTP_SERVER_BODY_LOGGING` | `true` |
| `HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY` | `true` |
| `HTTP_SERVER_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_SERVER_RESPONSE_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `true` |
| `HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |
| `HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |
| `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |
| `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` | `""` (empty)  ← **set, but empty** |

**Bodies are logged in production and nothing is masked.** The switch is on and every masked-field list is set to an empty string, so `bfi-go-pkg`'s scrubber runs with nothing to scrub. That is a deployment setting, not a code defect — the fix is a field list in this file.

**Proposed change to this file:** section §2 of [deployment-proposal.md](deployment-proposal.md) — raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on 14 September 2026 (branch `fix/logging`), awaiting SRE review.

---

## Implementation status

**Scope of [#1263](https://github.com/bfi-finance/lora-gateway-service/pull/1263) was reduced on 14 September 2026, on SRE's guidance.** The commit that gave the `*_JSON_MASKED_FIELDS` config fields a default list was reverted; masked fields are set per environment in `app-deployment`, not defaulted in code. What remains is the code the deployment setting depends on — the scrubber actually wired to the field list the environment provides — and any log-level fixes.

**Pull request: [lora-gateway-service#1263](https://github.com/bfi-finance/lora-gateway-service/pull/1263)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/lora-gateway-service/tree/fix/logging), head `ac494eac`, branched from `master` at `75eeab15`.

[Files changed](https://github.com/bfi-finance/lora-gateway-service/pull/1263/files) · [Commits](https://github.com/bfi-finance/lora-gateway-service/pull/1263/commits) · [Compare against master](https://github.com/bfi-finance/lora-gateway-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request. The Go wrapper fix, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) (`JSONScrubber` masks non-string values), is still open; the masked-field lists stay a per-service, per-environment setting in `app-deployment`, as SRE asked on 14 September.

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is red only on **`SYNK Security Analysis`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

| | |
|---|---|
| Commits | 2 |
| Files changed | 2 |

Commits:

- fix(logging): actually mask outbound bodies, and log them on failure only
- fix(logging): drop the masked-field defaults from the config struct *(14 Sep, reverts the default above on SRE's guidance)*

Files:

- `.env.example`
- `internal/config/http.go`

**CI caught a real defect in this change and it has been fixed:** the shared logger import had to be aliased (`bfilogger`) because the `HTTPClient(logger zerolog.Logger)` parameter shadows the package. Full list in [README.md](README.md#what-ci-said-about-pack-two).

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
