# backend-dashboard-otrs — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `bau-prod-ms-otrs-report`  
**Stack:** Go, standard library log, Echo, ArangoDB, Google Chat webhooks  
**Production volume:** 11,846 info a week, and no other level at all

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Working credentials are in the log index

`helper/googlechat.go` logs the full webhook URL on every message sent and every failure:

```go
log.Printf("✅ Sent ticket %s %s (%s) to channel %s", categoryhdescription, otrsno, categoryd, webhookURL)
log.Printf("❌ Failed sending message for %s to channel %s: %v", otrsno, webhookURL, err)
```

A Google Chat webhook URL carries its credentials in the query string:

```
https://chat.googleapis.com/v1/spaces/<space-id>/messages?key=<API key>&token=<webhook token>
```

Those entries are in `bau-prod-ms-otrs-report` in Datadog now, with the key and token values intact. Anyone with log read access can use them to post into those spaces.

**Please rotate the affected webhooks.** Redacting them going forward does not undo the exposure — the URLs stay in the log index for as long as the retention window covers.

## What this PR changes

**New `helper.RedactURL`.** Keeps scheme, host and path; drops the query string, fragment and userinfo. The space ID in the path still identifies the channel, which is all the log line ever needed. Unit tests included.

Both call sites go through it.

**`main.go` printed the OIDC provider's own endpoint configuration on every rejected token:**

```go
if err != nil {
    fmt.Println(oidcProvider.Endpoint())   // says nothing about why the token failed
    return echo.NewHTTPError(http.StatusUnauthorized, ...)
}
```

It now logs the verification error instead. That is the line a reader needs when someone cannot sign in.

## Not addressed here

**This service has no log levels at all.** It uses the standard library `log` package throughout — 113 `log.Print*` calls and 48 `fmt.Print*` calls. So `❌ Failed sending message` and `✅ Sent ticket` arrive in Datadog at exactly the same severity: all **11,846 weekly entries are `info`**, including the failures.

Fixing that means adopting a levelled logger and a new dependency, which needs a working Go toolchain to tidy the module. It is worth doing and it is not in this PR.

## Please build before merging

**Compiled and tested locally.** An earlier version of this file said no Go toolchain was available. That was wrong — Go is installed via `mise`. On this branch: `go build ./...` passes, `gofmt` is clean on every file touched, and `go test ./helper/... -run TestRedactURL` passes both tests — so the redaction shipped with this change has actually been exercised.

`golangci-lint` **could not run**: this repository's `.golangci.yml` is a v1 config and does not load with golangci-lint 2.11.4, so the branch has had no local lint check. There is also no pull request, because there is no write access to this repository — see below.

---

## Implementation status

**No pull request.** The GitHub API reports `permissions.push: false` for this
repository, so the branch could not be pushed.

The work exists on a local `fix/logging` branch at `ce326fc`, branched from `master`
at `544cddd`, one commit across 4 files:

- `helper/googlechat.go`
- `helper/redact.go`
- `helper/redact_test.go`
- `main.go`

Someone with write access needs to push it. **The credential exposure should not
wait for that** — rotate the affected Google Chat webhooks now.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
