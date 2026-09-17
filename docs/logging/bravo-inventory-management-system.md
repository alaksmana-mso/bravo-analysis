# bravo-inventory-management-system — logging findings and fixes

**Squad:** Asset Management  
**Production service:** `bravo-inventory-management-system`  
**Stack:** TypeScript, React, Vite, Datadog Browser RUM  
**Production volume:** 485,992 info, 9,416 error, 7,934 warn a week on prod-inventory-management

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## The request body and the Authorization header were going into RUM

`src/libs/datadog.ts`:

```ts
sendAxiosError: (axiosError: AxiosError) => {
  log.sendError(axiosError.message, axiosError);   // the whole error object
},
```

`AxiosError.config` carries `data` — the request body — and `headers`, including `Authorization`. Every failed call from this console sent both to Datadog RUM, where they sit in the error context for the retention period. `services/interceptors.ts` calls this on **every non-401 failure**.

It now sends method, URL, status and error code. That is what a reader needs to find the failure in APM; the payload is already on the backend span.

## A parsing bug that silently turns RUM off

```ts
sessionSampleRate: Number(import.meta.env.VITE_DATADOG_SESSION_SAMPLE_RATE ?? 100),
```

`??` only falls back on `null` or `undefined`. **`.env.dev` defines these variables and leaves them empty**, so the expression evaluates `Number('')` — which is **0**, and RUM records nothing. An *unset* variable gives 100.

Neither is what the code intends. A small `sampleRate()` helper now treats empty and unparseable the same as unset.

## Worth a decision, and left alone

Both rates default to **100**, so an unset deployment records every session *and* every session replay. Session Replay at 100% is the most expensive RUM setting there is. I cannot see the production values from here, so this is flagged rather than changed — it is a cost decision for this squad.

## What is already right

This file is in better shape than most of the estate:

- `allowedTracingUrls` **is** set, so RUM sessions join backend traces. (`bravo-surveyor-console` was missing exactly this.)
- `defaultPrivacyLevel: 'mask-user-input'`
- the user is set by `id` alone

## Tests

The existing unit test is updated, and now also asserts that **neither the bearer token nor a request-body identifier appears in what is sent**.

**The test has not been run** — no Node toolchain is available on the machine this was written on. Please treat CI as the first real check.

---

## In the production deployment

**No deployment directory was found for this repository** in `bfi-finance/app-deployment` or `bfi-finance/bfi-app-deployment` (searched 14 September 2026; `confins-app-deployment` was not reachable). Either it deploys from somewhere else or under a name this review did not match. Whoever owns the deployment should confirm where its log level and masking are set.

---

## Implementation status

**Pull request: [bravo-inventory-management-system#232](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-inventory-management-system/tree/fix/logging), head `3c75205`, branched from `master` at `99425aa`.

[Files changed](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232/files) · [Commits](https://github.com/bfi-finance/bravo-inventory-management-system/pull/232/commits) · [Compare against master](https://github.com/bfi-finance/bravo-inventory-management-system/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request; it stands as written.

CI on the current head is **fully green**.

| | |
|---|---|
| Commits | 1 |
| Files changed | 2 |

Commits:

- fix(rum): stop putting the request body and Authorization header in RUM errors

Files:

- `src/libs/__tests__/datadog.test.ts`
- `src/libs/datadog.ts`

**Not compiled and not tested; parsed.** Node is available through `mise`, but this repository's `node_modules` is not installed here, so the changed TypeScript was **not type-checked** and no test suite was run. The TypeScript compiler's own parser reports no syntax errors in the changed files — a syntax check, not a type check. CI on the pull request is the first real check.

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
