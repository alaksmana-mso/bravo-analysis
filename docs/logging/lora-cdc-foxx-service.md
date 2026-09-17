# lora-cdc-foxx-service — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-lora-cdc-foxx-service`  
**Stack:** JavaScript, ArangoDB Foxx microservice  
**Production volume:** 17,259 info, 1 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## The whole Datadog configuration was hardcoded in a committed file

`logger/index.js`:

```js
const config = {
    apiKey: 'your_api_key_here',
    endpoint: 'https://http-intake.logs.us5.datadoghq.com/api/v2/logs',
    service: 'sit-lora-cdc-foxx-service',
    env: 'sit',
    ...
```

The checked-in API key is a placeholder, so **nothing is leaked today**.

But the deployed copy reports itself to Datadog as `prod-lora-cdc-foxx-service` and writes **17,259 entries a week** — so what is in this file is already not what runs. The real values are being patched in somewhere this repository cannot see. An `apiKey` field in committed source is a loaded gun whether or not today's value is real.

## What this PR changes

All of it now comes from the Foxx service configuration declared in `manifest.json`:

| Setting | Type | Default |
|---|---|---|
| `apiKey` | password | **none — must be set per deployment** |
| `endpoint` | string | the us5 intake URL |
| `service` | string | `lora-cdc-foxx-service` |
| `env` | string | `sit` |
| `host`, `logLevel`, `enabled`, `logConsoleEnabled` | | as before |

**`shouldLog` also silently dropped unknown levels.** `config.logLevels[level]` is `undefined` for anything outside the four known names, and `undefined <= n` is `false` — so a caller with a typo lost the log line entirely, with no indication. An unrecognised level is now treated as info: the label is lost, the line is not.

## Needing an owner, and not changed here

```js
router.post('/log', function (req, res) { ... sendToDatadog(level, message, metadata); ... });
```

This endpoint accepts a level, a message and arbitrary metadata **from anyone who can reach this Foxx service, with no authentication**, and forwards it to Datadog under this service's identity and API key. That is both a log-injection path and a log-spend path.

Adding authentication is a deployment decision — who is allowed to call it, and with what credential — and not something to guess at from outside the squad.

## Please run this before merging

**This was not run.** No Node or ArangoDB is available on the machine it was written on. `manifest.json` was checked as valid JSON and `index.js` for balanced brackets. That is not a test.

---

## In the production deployment

**No deployment directory was found for this repository** in `bfi-finance/app-deployment` or `bfi-finance/bfi-app-deployment` (searched 14 September 2026; `confins-app-deployment` was not reachable). Either it deploys from somewhere else or under a name this review did not match. Whoever owns the deployment should confirm where its log level and masking are set.

---

## Implementation status

**Pull request: [lora-cdc-foxx-service#3](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/lora-cdc-foxx-service/tree/fix/logging), head `04c85da`, branched from `master` at `e4eda87`.

[Files changed](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3/files) · [Commits](https://github.com/bfi-finance/lora-cdc-foxx-service/pull/3/commits) · [Compare against master](https://github.com/bfi-finance/lora-cdc-foxx-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java or Go wrapper side changes this pull request; it stands as written.

CI on the current head is **fully green**.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(logging): move the Datadog credentials and tags out of source

Files:

- `logger/index.js`
- `logger/manifest.json`

**Not built and not tested; parsed.** Node is available through `mise`; `node --check` parses `logger/index.js` and `manifest.json` is valid JSON. Those are syntax checks, not tests. CI on the pull request is the first real check.

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
