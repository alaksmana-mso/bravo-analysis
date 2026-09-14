# bravo-notification-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-notification`  
**Stack:** Go, zap, gRPC, RabbitMQ, ent, Vonage, Firebase  
**Production volume:** 9,499 error, 63 warn, 8 info a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Four places write credential material into the log stream

### 1. The JWT signing key, printed in full

`pkg/lib/grpc/grpcmiddleware/jwt.go`, `GenerateTokenWithAcl`:

```go
fmt.Printf("[TokenUtil][GenerateTokenWithAcl] Private key PEM: %s", pemPrivateKey)
```

`fmt.Printf` writes straight to stdout, so **no logger level could ever have suppressed it**. Anyone who could read the container log could forge tokens.

Three sibling debug prints go with it. All four are replaced by one structured line at debug naming the application, the subject and the ACL paths — never the key.

### 2. The Vonage private key, at info

Same file, `GenerateVonageJWT`:

```go
log.Info("generating vonage jwt", ..., tag.Any("private_key", config.Environment.VonagePrivateKey))
log.Info("vonage jwt generated", tag.Any("vonage_jwt", jwtAuth.JWT))
```

The private key, and then the JWT it produced. Both fields removed; `app_id` stays, which is what a reader actually needs.

### 3. Every failed bearer token, at warn

Same file, the `AccessToken` middleware:

```go
l := log.With(tag.Any("event_type", "access_token"), tag.Any("access_token", accessToken))
...
l.Warn("failed to parse access token", tag.Error(err))
```

`l` carries the token, so every malformed or expired bearer token was written out in full. The field is gone.

### 4. `fmt.Printf("Error loading private key: %v", err)`

Now a structured error.

## What I checked before claiming impact

Over the 7 days to 13 September 2026, **none of these lines appears in `prod-ms-notification`**. Nothing is leaking right now — the Vonage ACL path is not being exercised.

The code is still there and would print the signing key the moment it runs. And that window is 7 days, not the life of the code. **Please treat the Vonage credentials as needing review rather than assuming they were never exposed.**

## Two smaller fixes

`app/handler/handler.go` used the standard library `log.Printf` with an `"ERROR:"` prefix for two genuine errors. Everything stdlib `log` writes arrives in Datadog at **info**, so those errors were invisible to any severity filter — which matters, because one of them says Google Chat OIDC verification is disabled. They now use the service's own logger at error, and the stdlib `log` import is gone.

`config/vendors/vendor.go` reported a failed Google Chat adapter initialisation with `fmt.Printf("WARNING: ...")`. Now `log.Warn`.

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

## Implementation status

**Pull request: [bravo-notification-service#446](https://github.com/bfi-finance/bravo-notification-service/pull/446)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-notification-service/tree/fix/logging), head `b077a05`, branched from `master` at `16e64cf`.

[Files changed](https://github.com/bfi-finance/bravo-notification-service/pull/446/files) · [Commits](https://github.com/bfi-finance/bravo-notification-service/pull/446/commits) · [Compare against master](https://github.com/bfi-finance/bravo-notification-service/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 3 |

Commits:

- fix(logging): stop logging signing keys, private keys and bearer tokens

Files:

- `app/handler/handler.go`
- `config/vendors/vendor.go`
- `pkg/lib/grpc/grpcmiddleware/jwt.go`

**CI caught a real defect in this change and it has been fixed:** a comment block I added was missing its `//` on the second line and would not have compiled. Caught by re-reading before the push, not by a build. Full list in [README.md](README.md#what-ci-said-about-pack-two).

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
