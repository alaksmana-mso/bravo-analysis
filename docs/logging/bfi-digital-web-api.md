# bfi-digital-web-api — logging fixes

**Squad:** Digital Web
**Production service:** `digital-prod-ms-bfi-digital-web-api` (note: `env:digital-prod`, not `prod`)
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

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service is not logging bodies — it is
logging error objects, which is the same mistake at smaller scale, and it is invisible for a
different reason.**

| | Seven days, `env:digital-prod` |
|---|---:|
| Spans | 2,101,579 |
| Log entries | **3,369** |
| of which `error` | 2,841 |
| of which `info` | 515 |

Two million spans and three thousand log lines. Whatever those 679 `console.log` calls are
producing, almost none of it is reaching Datadog.

### What the serialising calls actually do

92 of the `console.log` calls wrap `JSON.stringify`. They are not request or response
bodies — they are driver errors:

- `src/v1/handler/handleError.js:4` — `console.log("mssql-error-code:" + JSON.stringify(error.code))`
- `src/v1/models/service/carCalculatorModel.js:235` — `console.log("getSumInsuranceYearly: ", JSON.stringify(err))`
- `src/v1/service/submission/submissionService.js:144`, `:154`, `:162`, `:186`, `:197` — the same pattern across five sites

Serialising a whole error object is the pattern that put a live API secret into
`lms-calculation-service`'s logs. This repo calls MSSQL and RabbitMQ, so the risk here is
connection strings and credentials in driver error objects. **Check what
`JSON.stringify(err)` produces for a failed MSSQL connection before deciding this is
harmless.**

### The env tag is the bigger problem

This service reports as `env:digital-prod`, not `env:prod`. That means it is excluded from
every `env:prod` dashboard, monitor and search in this analysis — and it will be excluded
from any Live Debugger or correlation rollout that SRE scopes to production, unless someone
remembers this service by name.

The fix is in the service identity section below.

### What you get back, and the Node.js limit

`package.json` has `dd-trace: ^6.1.0`, so the tracer is present. Datadog's Live Debugger
supports Node.js, but **with line probes only.** Method probes — "capture the arguments and
the return value of this function" — are a Java and .NET feature. In Node.js you pick a
*line* and get the variables in scope at that line.

In practice that means probing the line immediately before a `res.json(...)` or immediately
after an `await` that returns a result, where a plain local variable holds the value. Do not
probe a line where you would have to walk in through `req` — the default capture depth is 3
levels and 20 fields per object, and an Express `req` blows past both.

Remote Configuration is required, and it is failing across the estate —
`unexpected response code Internal Server Error 500 ... empty targets meta in director local
store`.

### What to do

1. Fix the env tag first. Nothing else SRE enables will reach this service until it does.
2. Replace `JSON.stringify(err)` with `err.message` and `err.code`, and check what a failed
   MSSQL connection error contains before you assume the old form was safe.
3. Find out why 679 `console.log` calls produce 3,369 log entries a week. Either the calls
   are on cold paths, or stdout is not being collected from this deployment. Both are worth
   knowing.
4. Put identifiers on the span rather than expecting a body:

   ```js
   const tracer = require('dd-trace');
   tracer.scope().active()?.setTag('submission.id', submissionId);
   tracer.scope().active()?.setTag('product.id', productId);
   ```

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `digital-prod-ms-bfi-digital-web-api` | 2,078,441 spans |
| Logs | `digital-prod-ms-bfi-digital-web-api` | 3,406 entries |
| `env` tag | `digital-prod` | — |

The names match, which is right. Two other things are wrong.

**The `env` tag is `digital-prod`, not `prod`.** Every estate-wide query, dashboard and
monitor written against `env:prod` excludes this service completely. It is invisible in any
production view that does not name it explicitly. `env` is meant to be a small closed set —
`prod`, `uat`, `sit`, `dev` — with the product expressed in the service name, which it
already is.

**Log coverage is thin.** 3,406 log entries against 2,078,441 spans is roughly one log
line per 600 requests. Either most logging is not reaching Datadog, or this service barely
logs. Worth confirming which before the `console.log` cleanup in this file is scheduled —
if the logs are not arriving, that cleanup saves nothing here.

### What to do

1. **Change the `env` tag to `prod`** in the GitOps values file, via the unified tagging
   labels below. Do this as a deliberate cutover: for a short window the service will appear
   under both values, and any monitor scoped to `env:digital-prod` needs repointing first.
2. **Find out where the logs are going.** Compare Cloud Logging volume for this deployment
   against the 3,406 entries Datadog received.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_digital-prod-ms-bfi-digital-web-api`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "digital-prod-ms-bfi-digital-web-api"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_digital-prod-ms-bfi-digital-web-api
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_digital-prod-ms-bfi-digital-web-api` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:digital-prod-ms-bfi-digital-web-api env:digital-prod

# APM Traces
service:digital-prod-ms-bfi-digital-web-api env:digital-prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:digital-prod-ms-bfi-digital-web-api` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Add pino or winston with the level driven by `LOG_LEVEL`
- [ ] Codemod `console.log` to `logger.debug` across `src/`
- [ ] Hand-review `leads.js`, `cars.leads.js`, `pbf.leads.js` for logged customer payloads
- [ ] Promote genuine errors to `logger.error` with structured fields
- [ ] Confirm the production config carries no debug level
- [ ] Change the `env` tag from `digital-prod` to `prod`, repointing monitors first
- [ ] Find out why only 3,406 log entries reached Datadog against 2.08M spans
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Fix the env tag first — nothing SRE enables for `env:prod` reaches this service
- [ ] Check what `JSON.stringify(err)` produces for a failed MSSQL connection before calling it harmless
- [ ] Find out why 679 `console.log` calls produce only 3,369 log entries a week
