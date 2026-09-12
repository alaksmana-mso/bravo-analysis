# lms-calculation-service — logging fixes

**Squad:** Contract Collateral & Loan Calculation
**Production service:** `prod-ms-calculation`
**Stack:** Node.js / TypeScript (`ts-calculation-engine`), Axios

**This is the most urgent item in the logging pack. It is a credential exposure, not a cost
line.** Do item 1 today. The cost work can wait.

This service is also the one squads name when they say they cannot see request and response
bodies in Datadog. **That complaint is correct** — see
[body-visibility.md](body-visibility.md) for the investigation and what SRE should enable.
Item 4a below covers what this repo should do about it.

---

## 1. A live API secret is being written to production logs

`src/helpers/HttpHelper.ts:27`

```ts
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    logger.error(`Unexpected error at client response interceptor: ${JSON.stringify(error)}`);
    return Promise.reject(error);
  }
);
```

`JSON.stringify` on an `AxiosError` serialises `error.config`. That object holds the
request headers and the request body. The constructor two lines above sets an `api-secret`
header on every call:

```ts
constructor(apiSecret?: string) {
  this.headers = new AxiosHeaders({ "Content-Type": "application/json" });
  if (apiSecret) this.headers.set("api-secret", apiSecret);
}
```

Production logs confirm it. Every entry contains:

- the **`api-secret` header value in plaintext** — a live credential, in full, on every
  4xx or 5xx
- the full request body, including customer `birth_date`
- the full Axios stack trace
- ANSI colour escape codes, because the logger writes terminal formatting to stdout

Measured volume: **437 entries in 51 minutes**, about 12,000 a day, 1.5–2 KB each.

The secret has been in production logs for as long as this code has shipped. Anyone with
log read access in `bravo-project-331802` has it.

### Fix

```ts
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    logger.error({
      msg: "upstream call failed",
      method: error.config?.method,
      url: error.config?.url,
      status: error.response?.status,
      code: error.code,
    });
    return Promise.reject(error);
  }
);
```

Log the four fields that help you debug. Never the config object.

### Then

1. **Rotate the `api-secret`.** Treat it as leaked. It is shared with `prod-ms-insurance`,
   so coordinate with Insurance.
2. **Purge or shorten retention** on the log entries that carry it, if your retention
   policy allows.
3. Raise it with whoever owns security review. It is a finding in its own right.

---

## 2. The same errors are logged at the wrong level

These entries arrive at `status: info` even though they say `error:` in the text. The
`[31m…[39m` colour codes are the giveaway — the logger is formatting for a terminal, and
the real level never reaches the log platform.

Two consequences: real failures do not appear in error dashboards, and every one of these
is indexed as routine traffic.

### Fix

In `src/connections/connection.logger.ts`, configure the logger for JSON output with no
colour when not attached to a TTY. Most Node loggers do this with a single option — for
pino, `transport` only in development; for winston, drop `format.colorize()` outside local.

That change alone makes `status` correct across every log this service emits, which makes
the rest of the estate's dashboards more useful too.

---

## 3. `logger.error(err)` on whole error objects

`src/helpers/HttpHelper.ts`, in `get()` and the methods below it:

```ts
} catch (err) {
  logger.error(err);
  ...
}
```

Same problem, smaller blast radius — it serialises whatever the error carries. Replace with
the structured form from item 1.

---

## 4. Body logging in the service layer

21 occurrences of logging a serialised body or payload, concentrated in:

- `src/services/ProductService.ts` — 8
- `src/services/service.calculation.bfi.ts` — 4
- `src/client/client.insurance.bfi.ts` — 2 exception logs

Calculation requests carry customer income, asset and tenor data. Log the identifiers you
need to trace a call — application id, product id, correlation id — not the body.

---

## 4a. The interceptor does not capture what the team thinks it does

This matters because it changes the argument for keeping it.

The interceptor exists so developers can see what was sent and what came back when a
downstream call fails. It does the first. **It has never done the second.**

`JSON.stringify(error)` on an `AxiosError` calls that error's own `toJSON()`. That method
returns `message`, `name`, `stack`, `config`, `code` and `status`. Axios **deliberately
leaves out `response`**. So the request body is captured, inside `config.data`. The response
body is not, and no amount of keeping this code will produce it.

You can see it in production. Every one of these entries ends the same way:

```
"code":"ERR_BAD_REQUEST","status":400}
```

A status code, and nothing about what `prod-ms-insurance` or `prod-ms-asset-pricing`
actually said.

It also only fires on non-2xx. A call that returns HTTP 200 with the wrong number in it
produces no record at all — which for a calculation engine is the failure that matters most.

So the trade is worse than it looks: the interceptor leaks a live credential 1,700 times a
day, costs money on every occurrence, and delivers half of what it was written for.

### What to do instead

Put the identifiers and the outcome on the span. That is enough to find the call, group the
failures and reproduce it:

```ts
import tracer from "dd-trace";

const span = tracer.scope().active();
span?.setTag("http.downstream_service", "prod-ms-insurance");
span?.setTag("http.downstream_status", err.response?.status);
span?.setTag("calc.agreement_no", agreementNo);
```

Then log one line with the same identifiers, at `error`, with no serialised transport object.

For the times you genuinely need to see the payload, the answer is Datadog's Live Debugger —
a probe set from the UI on a running pod, captured once, then removed. SRE is confirming
whether it can be enabled; the prerequisites and limits are in
[body-visibility.md §5.3](body-visibility.md). **Nobody is asking this squad to give up
payload visibility with nothing in return.** The credential line is the exception: that goes
now.

---

## 5. What this is worth

| Item | Saving / month | Priority |
|---|---:|---|
| 1 — secret in logs | Rp 2–4M | **today, it is a security fix** |
| 2 — log levels and colour codes | small, but fixes alerting | this sprint |
| 3 — whole error objects | included in 1 | with 1 |
| 4a — interceptor never captured responses | Rp 0 | changes the argument, not the bill |
| 4 — body logging | Rp 1–2M | next sprint |

Total about Rp 3–6M a month. The money is not the reason to do this.

---

## Request and response bodies in Datadog

The numbered findings above are the detail. This is the summary, in the same shape as every
other file in this pack.

| | Seven days, production |
|---|---:|
| Spans | 5,430,270 |
| Log entries | 2,397,823 |
| of which tagged `status:error` | **1,325** |
| Entries carrying a captured request body | the Axios error dumps — see item 4a |
| Entries carrying a captured response body | **none, ever** |

Three things, all covered above:

- **The complaint is right.** No Datadog tracer, in any language, has a supported setting
  that puts an HTTP body on a span. This service is instrumented and healthy — 5.4 million
  spans a week — and none of them carries content.
- **The workaround captures half of what the team thinks.** `AxiosError.toJSON()` omits
  `response`. Item 4a has the evidence.
- **It leaks a live credential doing it.** Item 1. That one goes now, on its own schedule,
  not behind the SRE programme.

### What you get back, and the Node.js limit

`package.json` has `dd-trace ^5.81.0` and the lockfile pins 5.109.0, so Datadog's Live
Debugger is available in principle. **Node.js gets line probes only.** Method probes —
"capture the arguments and the return value of this function" — are a Java and .NET feature.
Here you pick a *line* and get the variables in scope at it, so probe the line immediately
before `res.json(result)` or immediately after the `await` that produced the value. Do not
probe a line where you would have to walk in through `req`.

Remote Configuration has to work first, and it does not — thirteen production services are
failing to poll it with `empty targets meta in director local store`. The estate-level
picture and what SRE should enable are in [body-visibility.md](body-visibility.md).

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-calculation` | 5,408,124 spans |
| Logs | `prod-ms-calculation` | 2,387,623 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-calculation`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-calculation"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-calculation
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-calculation` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-calculation env:prod

# APM Traces
service:prod-ms-calculation env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-calculation` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Replace the response interceptor in `HttpHelper.ts:27` with structured fields
- [ ] Rotate the `api-secret` shared with `prod-ms-insurance`
- [ ] Tell security the credential was exposed in logs
- [ ] Turn off colour output and emit JSON when not on a TTY
- [ ] Replace `logger.error(err)` with structured logging in `get`, `post`, `put`, `delete`
- [ ] Remove body logging from `ProductService.ts` and `service.calculation.bfi.ts`
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Note that the interceptor never captured response bodies — do not keep it for that reason
- [ ] Put downstream service, status and agreement number on the span with `setTag`
- [ ] Do not wait for Live Debugger to fix item 1 — the credential goes now
- [ ] Note the Node.js limit: line probes only, no method probes
