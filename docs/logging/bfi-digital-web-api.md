# bfi-digital-web-api — logging fixes

**Squad:** Digital Web
**Stack:** Node.js (`compro_backend`)

679 `console.log` calls in a Node backend. Unlike the front-end repos, **these cost money** —
`console.log` writes to stdout, and stdout goes to Cloud Logging.

---

## 1. 679 `console.log` calls in production code

Highest concentration:

| File | Count |
|---|---:|
| `src/v2/services/leads/cars.leads.js` | 24 |
| `src/v2/services/leads/leads.js` | 22 |
| `src/v2/services/leads/pbf.leads.js` | 21 |
| `src/v2/models/submission.app/submission.app.js` | 19 |
| `src/v2/subscribers/centrix.car.js` | 18 |
| `src/v2/services/greeting/greeting.leads.js` | 17 |

Every one of these has three problems:

1. **It is billable.** stdout goes straight to Cloud Logging.
2. **It has no level.** Everything lands as `info`, so none of it can be excluded by a
   filter later, and real errors do not reach error dashboards.
3. **The lead files are the risk.** `leads.js`, `cars.leads.js` and `pbf.leads.js` handle
   customer lead submissions — name, phone, email, vehicle details. `console.log` in a
   lead service usually means logging the payload.

### Fix

1. **Add a real logger.** pino or winston, JSON output, level from an environment variable:

   ```js
   const logger = require("pino")({ level: process.env.LOG_LEVEL || "info" });
   ```

2. **Replace `console.log` with `logger.debug`** as the default. Almost all 679 are
   developer tracing, and debug is off in production.
3. **Promote the few that matter** to `logger.info` or `logger.error` with structured
   fields.
4. **Check the lead files first** for logged payloads and remove customer data from them.

A codemod handles most of this. The judgement calls are which lines deserve `info` and
which files log personal data — do those two by hand.

---

## 2. Root debug levels in config

`docroot/config/config_dev.yaml` and `docroot/config/config_local.yaml` carry four
root-level debug entries. Non-production only, so no production cost — but non-production
Cloud Logging is Rp 56.4M a month estate-wide, so it is not free either.

Confirm `config_prod.yaml` does not carry the same, and lower the dev ones once the logger
in item 1 exists.

---

## 3. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — replace `console.log` with a levelled logger | Rp 3–8M | medium |
| 2 — non-prod debug config | Rp 1–2M | medium |

The stronger argument is item 1 point 3. Customer lead data should not be in logs, and
right now nobody can tell whether it is without reading 679 call sites.

---

## Checklist

- [ ] Add pino or winston with the level driven by `LOG_LEVEL`
- [ ] Codemod `console.log` to `logger.debug` across `src/`
- [ ] Hand-review `leads.js`, `cars.leads.js`, `pbf.leads.js` for logged customer payloads
- [ ] Promote genuine errors to `logger.error` with structured fields
- [ ] Confirm the production config carries no debug level
