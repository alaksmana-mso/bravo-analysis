# bravo-surveyor-console — logging fixes

**Squad:** Survey and Verification
**Production service:** none — browser application
**Stack:** React, browser front-end

**This repo costs nothing in Cloud Logging.** `console.log` runs on the surveyor's device
and never reaches GCP. It is listed here so nobody spends a sprint on it expecting a saving.

The reason to act is data exposure, and it is a smaller job than the raw count suggests.

---

## 1. 939 `console.log` calls, browser-side

Spread across `src/`, with the densest in:

- `src/pages/Conventional/Surveyor/NDF2W/common/InputSurveyPage/hooks.js` — 14
- `src/pages/Conventional/Surveyor/NDFMultiAsset/SurveyFormMediumRisk/SimpleSurveyCustomerValidation/useCustomerValidation.js` — 13

### Why it still matters

The surveyor console handles customer validation and survey input. Files named
`useCustomerValidation` and `InputSurveyPage` are exactly where customer records live.
Anything logged there is readable in the browser console by whoever is holding the device —
including on a shared or personal phone in the field.

There is no Cloud Logging cost, no indexing cost, and no retention question. Only the
console.

### Fix

1. **Strip `console.*` from production builds.** One build setting, no code changes:

   ```js
   // vite.config.js
   export default defineConfig({
     esbuild: { drop: ["console", "debugger"] },
   });
   ```

   or for webpack/terser, `compress: { drop_console: true }`.

   That closes the exposure across all 939 sites in one change.

2. **Then**, at leisure, remove the calls from source so developers stop adding more. This
   is tidying, not risk work — item 1 already fixed the risk.

3. **Hand-check the two files above** before shipping, in case anything is logged that
   should not exist even in development.

---

## 2. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — drop console in production builds | **Rp 0** | it is not a cost line |

Effort: about an hour for item 1. Do it because it is an hour, not because it saves money.

---

## Request and response bodies in Datadog

No Datadog tracer has a supported setting that puts an HTTP body on a span, and squads work
around that by logging bodies. **This repo is a browser application, so the answer is
different from every other file in this pack — and most of it is already built.**

| | Production |
|---|---:|
| Backend spans | none — this is a front end |
| Server log entries | none |
| `console.log` calls in the repo | 939 |
| of those that serialise a response, payload or data object | 18 |

### Live Debugger does not apply here

Datadog's Live Debugger runs inside a server-side tracer. There is no browser
implementation. So the answer SRE is preparing for the Java and Node.js services does not
reach this repo at all. **Do not let this squad be told to wait for it.**

The Datadog product that answers "what did this request send and what came back" in a
browser is **RUM**, and this repo already has it: `@datadog/browser-rum` 5.5.0,
`src/datadog/index.ts`, initialised from `src/setup.js` and `src/sharia-setup.js`, with
`trackResources: true`, `trackLongTasks: true` and `defaultPrivacyLevel: 'mask-user-input'`.

### The one setting that is missing

Compare `src/datadog/index.ts` with `bravo-inventory-management-system`'s
`src/libs/datadog.ts`. They are almost the same file. The difference is one line:

```ts
allowedTracingUrls: [(url) => url?.startsWith(`${import.meta.env.VITE_BASE_URL}`)],
```

That setting is what makes the browser attach trace headers to its API calls, so a RUM
resource joins the backend trace and a developer can click from a slow screen straight into
the server span that caused it. `bravo-inventory-management-system` has it and is the only
working front-to-back linkage in the estate. This repo does not have it.

Without it, RUM here records what the browser did and the backend records what the server
did, and nothing connects the two — which is exactly the "I can't see what was sent"
complaint, arriving from the other end.

### What to do

1. Add `allowedTracingUrls` to `datadogRum.init`, scoped to the surveyor console's own API
   host. Copy the shape from `bravo-inventory-management-system/src/libs/datadog.ts`.
2. Check the sample rates. This repo defaults `sessionSampleRate` and
   `sessionReplaySampleRate` to **1** when the environment variable is unset;
   `bravo-inventory-management-system` defaults both to 100. Find out which values production
   actually runs with — a 1% sample will make the linkage look broken when it is not.
3. For the 18 `console.log` calls that serialise a response or payload: these are visible to
   anyone with devtools open on a surveyor's laptop. Replace them with `datadogRum.addError`
   where they matter, and delete the rest. This is an exposure item, not a cost item — see
   item 1 above.
4. Confirm `defaultPrivacyLevel: 'mask-user-input'` is what Compliance expects for session
   replay on a screen that shows customer documents.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Datadog |
|---|---|
| Logs | none — browser code, nothing reaches Datadog |
| Traces | none |
| RUM | not registered for this console |

This is a browser application. It has no server-side identity to get wrong, and the
`console.log` findings in this file carry no Cloud Logging cost.

What is missing is different: there is no **RUM** application for the surveyor console, so
nothing in Datadog shows what surveyors actually experience — load times, JavaScript errors,
failed API calls from the field. That is a gap worth naming, but it is a new cost and it
belongs behind the gate in
[sre-datadog-recommendations.md](sre-datadog-recommendations.md), not in this file.

### If a RUM application is added later

Register it as `surveyor-console-prod`, matching the `<product>-<env>` convention, and set
`service` in the RUM init to the same string. Point `allowedTracingUrls` at the Bravo
microservices host so browser spans join the backend trace, the way
`bravo-inventory-management-system` already does.

---

## Checklist

- [ ] Add `drop: ["console", "debugger"]` to the production build config
- [ ] Verify the production bundle contains no `console.` calls
- [ ] Hand-review `useCustomerValidation.js` and `InputSurveyPage/hooks.js`
- [ ] Remove `console.*` from source over time, as files are touched
- [ ] Raise a RUM application for the surveyor console as a Phase 4 item, not now
- [ ] Add `allowedTracingUrls` to `datadogRum.init`, copying `bravo-inventory-management-system`
- [ ] Confirm the production RUM sample rates — the code defaults to 1, not 100
- [ ] Do not wait for Live Debugger; it has no browser implementation
