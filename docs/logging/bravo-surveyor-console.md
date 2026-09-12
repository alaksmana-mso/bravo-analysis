# bravo-surveyor-console — logging fixes

**Squad:** Survey and Verification
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

## Checklist

- [ ] Add `drop: ["console", "debugger"]` to the production build config
- [ ] Verify the production bundle contains no `console.` calls
- [ ] Hand-review `useCustomerValidation.js` and `InputSurveyPage/hooks.js`
- [ ] Remove `console.*` from source over time, as files are touched
