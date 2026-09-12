# lms-calculation-service — logging fixes

**Squad:** Contract Collateral & Loan Calculation
**Production service:** `prod-ms-calculation`
**Stack:** Node.js / TypeScript (`ts-calculation-engine`), Axios

**This is the most urgent item in the logging pack. It is a credential exposure, not a cost
line.** Do item 1 today. The cost work can wait.

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

## 5. What this is worth

| Item | Saving / month | Priority |
|---|---:|---|
| 1 — secret in logs | Rp 2–4M | **today, it is a security fix** |
| 2 — log levels and colour codes | small, but fixes alerting | this sprint |
| 3 — whole error objects | included in 1 | with 1 |
| 4 — body logging | Rp 1–2M | next sprint |

Total about Rp 3–6M a month. The money is not the reason to do this.

---

## Checklist

- [ ] Replace the response interceptor in `HttpHelper.ts:27` with structured fields
- [ ] Rotate the `api-secret` shared with `prod-ms-insurance`
- [ ] Tell security the credential was exposed in logs
- [ ] Turn off colour output and emit JSON when not on a TTY
- [ ] Replace `logger.error(err)` with structured logging in `get`, `post`, `put`, `delete`
- [ ] Remove body logging from `ProductService.ts` and `service.calculation.bfi.ts`
