# bravo-robot-scrape — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-robot-scrape`  
**Stack:** Python, standard logging with a JSON formatter, Selenium  
**Production volume:** 26,166 info, 300 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-robot-scrape` writes **26,166 info and 300 error** entries a week. Measured in Datadog over the 7 days to 13 September 2026.

## The problem

`account_statement/bficlient/DMSService.py` reported both success and failure with `print()`:

```python
print("✗ Upload client not initialized")
print(f"✗ Upload failed: {e}")
print(f"✓ Upload successful: {result.get('message', 'File uploaded')}")
```

`print()` writes to stdout with no level, so **a failed document upload arrives in Datadog at the same severity as a successful one**. Neither a severity filter nor a monitor can tell them apart. The exception was also reduced to its `str()` with no traceback.

## What this PR changes

The five call sites now use the module logger already declared at the top of the file:

- failures at **error**, with `exc_info=True` so the traceback survives
- the upload attempt and its result at **info**
- the full response body at **debug** rather than info — a diagnostic detail, not something worth a line on every upload

## What is already good and is left alone

`app/utils/logging_config.py` sets up JSON logging for Datadog, takes its level from settings, and quiets `pika`, `urllib3` and `selenium`. That part of the service is in better shape than most of the estate.

## Verification

No Python environment is available here to run the service, but the changed file was **parsed with `ast.parse` and is syntactically valid**. That is more than could be checked on the Go and Java repositories in this programme, and it is still not a test run.

---

## In the production deployment

Read from `app-deployment/robot-scrape/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `DEBUG`  ← **debug in production** |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.
**`LOGGER_LEVEL` is `debug` in production.** Every debug statement in the service ships to Cloud Logging and Datadog. This is the single cheapest change available for this service.

**Proposed change to this file:** section §1 of [deployment-proposal.md](deployment-proposal.md) — raised as [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820) on 14 September 2026 (branch `fix/logging`), awaiting SRE review.

---

## Implementation status

**Pull request: [bravo-robot-scrape#114](https://github.com/bfi-finance/bravo-robot-scrape/pull/114)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-robot-scrape/tree/fix/logging), head `e5be58c`, branched from `master` at `dae730a`.

[Files changed](https://github.com/bfi-finance/bravo-robot-scrape/pull/114/files) · [Commits](https://github.com/bfi-finance/bravo-robot-scrape/pull/114/commits) · [Compare against master](https://github.com/bfi-finance/bravo-robot-scrape/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java or Go wrapper side changes this pull request; it stands as written.

Its production manifest is one of the 19 changed by [app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820), which SRE approved on 15 September with one condition: the service's SA confirms the rollout restart before merge.

CI on the current head is **fully green**.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): report DMS upload failures as errors, not as stdout text

Files:

- `account_statement/bficlient/DMSService.py`

**Not run and not tested; parsed.** Python is available; the changed file parses with `ast.parse`. That is a syntax check, not a test — the scraper itself was not run. CI on the pull request is the first real check.

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
