# bravo-bpm-service — logging fixes

**Squad:** Scoring and Underwriting (also checked out under Survey and Verification)
**Production service:** `prod-ms-bpm`
**Stack:** Java, Spring Boot, Camunda 7

This repo carries the largest logging configuration risk in the estate. Whether it is
currently costing money is **unconfirmed** — see item 1.

---

## 1. Feign full-body logging — check the manifest before doing anything else

### What the code says

`src/main/resources/application.yaml`:

- **129** entries set `loggerLevel: full`, including `feign.client.config.default`
- the same file sets:

```yaml
logging:
  level:
    com:
      bfi:
        bravo:
          adapter: DEBUG
```

- all **57** Feign client interfaces live under `com.bfi.bravo.adapter.http.*`

`src/main/resources/application-prod.yaml`:

```yaml
logging:
  level:
    root: INFO
    org:
      hibernate: WARN
```

It sets `root`. It does **not** set `com.bfi.bravo.adapter`. Those are different keys in
Spring Boot, so the DEBUG level survives into production.

Feign writes bodies when the client's logger is at DEBUG. On this reading, every upstream
call — PEFINDO, SLIK, Dukcapil, CONFINS, Ali Cloud — logs its complete request and response
body.

### What production says

Nothing matching. Across two days, all production services:

| Check | Result |
|---|---|
| `status:debug` | 0 |
| `END HTTP` (Feign's full-logging terminator) | 0 |

### So do this first

Somebody needs to read the deployment manifest, which is not in this repo:

```bash
kubectl -n prod set env deploy/prod-ms-bpm --list | grep -i logging
```

If it shows `LOGGING_LEVEL_COM_BFI_BRAVO_ADAPTER=INFO` or similar, the body logging is
already off and there is **no cost saving here at all**. If it shows nothing, the logs are
being written and Datadog is dropping them before indexing — in which case Cloud Logging is
paying for all of it.

**One hour of work decides whether this repo is worth Rp 0 or Rp 40M a month.** Do not
quote a saving until it is done.

### Fix the configuration either way

Regardless of the answer, this is wrong:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: full
```

A default of `full` means one environment variable — or one merge into
`application-prod.yaml` — starts writing customer credit-bureau payloads into Cloud
Logging. That should not be one line away.

Change the default to `basic`, which logs method, URL, status and timing:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
```

Then set `full` on individual clients only where somebody can say why, and only for
non-production profiles.

Also pin the level explicitly in `application-prod.yaml` so it cannot drift:

```yaml
logging:
  level:
    root: INFO
    com.bfi.bravo.adapter: INFO
```

---

## 2. Stack traces, one log entry per frame

The three highest-volume log patterns in this service are all single stack frames:

| Pattern | Count, 2 days |
|---|---:|
| `at <pkg>.<class>.<method>(File.java:NN)` | 1,441 |
| `at org.springframework.…` | 844 |
| `at <pkg>.…` (deeper nesting) | 378 |

Multi-line aggregation is not configured anywhere in the cluster. A 50-frame Java trace
becomes 50 log entries. The text is about 3 KB; the 50 metadata envelopes add roughly 35 KB
on top of it.

Two of these are not faults at all:

- **`TokenExpiredException`** — 172 in two days, each with a ~50-frame trace, logged at
  SEVERE by Tomcat's `StandardWrapperValve`. An expired token is a normal condition. It
  should be a 401 and one line.
- **`FeignException$Unauthorized` on `IAMApiClient#getAssignedPermission`** — 106 in two
  days, same shape.

### Fix

1. Catch `TokenExpiredException` in `InternalAuthenticationFilter` (`doFilterInternal`,
   line 52) and return 401 without letting it reach Tomcat. One warn line with the token
   subject, no trace.
2. Same for the `IAMApiClient` 401 path.
3. Ask Platform to enable multi-line log aggregation cluster-wide. That is one Fluent Bit
   setting and it helps every Java service at once — it belongs in the platform work, not
   this backlog.

---

## 3. ENGINE-09004 BPMN parse warnings

432 occurrences in two days across four variants. Each message is long — one exceeds 1,500
characters listing every gateway and link event in the diagram.

Affected models:

- `ndf2w.bpmn` — exclusive gateways with an unconditional outgoing flow that is not marked
  as the default
- `ndf4w.bpmn` — link events whose catch and throw names do not match
- `unified-main-workflow.bpmn` — five mismatched link event names

These are model quality warnings. They re-emit every time the engine parses the definition.
None is a runtime error.

### Fix

In the BPMN files:

- set the default flow explicitly on each exclusive gateway the warning names
- make each link event's name match its link definition name

This is diagram editing, not code. It also removes a recurring warning that makes real
`ENGINE-*` problems harder to spot. `ENGINE-14006 Exception while executing job` — 41 in
two days — is a real one currently buried in the noise.

---

## 4. 694 exception logs passing the throwable

694 occurrences of `log.error(msg, exception)` across the repo. Highest concentration:

- `src/main/java/com/bfi/bravo/activity/multiasset/CalculateIncomePerMonthV2Activity.java` — 15

Each one can emit a full trace. Most do not need to: if the error is handled and the flow
continues, the trace adds nothing a message and a correlation id would not.

### Fix

Use the trace where the error is genuinely unexpected. Where it is an expected upstream
failure, log one structured line:

```java
log.warn("PD model check failed, falling back: loanId={} status={} reason={}",
         loanId, status, ex.getMessage());
```

Two error messages worth attention on their own, both currently logged with full traces:

- `Error while invoking Ali Cloud for PD Model Check Response` — 35 in two days, plus 31
  `ENGINE-16004 Exception while closing command context` for the same cause
- `Error when processing scheduling appointment event : 404 NOT_FOUND "Lead does NOT exist!"`
  — 169 in two days. A missing lead is a data condition, not an exception.

---

## 5. Smaller items

| Item | Count | Note |
|---|---:|---|
| Logging a serialised body | 46 | `RecalculateLoanStructureLTVOnly2WServiceImpl.java` has 6 |
| `printStackTrace()` | 26 | All in `src/test/` — harmless, but replace with assertions |
| `console.log` | 28 | Camunda Cockpit webjars, vendor code — leave alone |
| `CommonsRequestLoggingFilter` | registered | `setIncludePayload(true)`, 10 KB limit, but its logger sits at INFO in prod, so it is dormant. Remove the bean or leave it — it is not currently emitting |

Two recurring errors point at a caller bug rather than a logging problem:

- `Method parameter 'id': … Invalid UUID string: undefined` — 91 in two days
- `Method parameter '…': … For input string: "undefined"` — 82 in two days

A front-end is sending the literal string `undefined`. Fixing the caller removes 173 error
logs every two days and a real defect. Worth a ticket to whichever console owns it.

---

## 6. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — Feign body logging | **Rp 0 to 40M** | unknown until the manifest is read |
| 2 — stack trace handling | Rp 8–15M | medium; most of it is the cluster-wide setting |
| 3 — ENGINE-09004 | Rp 2–5M | high |
| 4 — exception logs | Rp 3–6M | medium |
| 5 — `undefined` parameter bug | under Rp 1M | high |

---

## Checklist

- [ ] **Read the prod deployment manifest for `LOGGING_LEVEL_*` overrides** — do this first
- [ ] Change `feign.client.config.default.loggerLevel` to `basic`
- [ ] Pin `com.bfi.bravo.adapter: INFO` in `application-prod.yaml`
- [ ] Handle `TokenExpiredException` in `InternalAuthenticationFilter` without a trace
- [ ] Handle the `IAMApiClient` 401 path the same way
- [ ] Ask Platform for cluster-wide multi-line aggregation
- [ ] Set default flows on the gateways named in `ndf2w.bpmn`
- [ ] Match link event names in `ndf4w.bpmn` and `unified-main-workflow.bpmn`
- [ ] Review the 694 `log.error(msg, ex)` sites, starting with the Ali Cloud path
- [ ] Raise a ticket for the front-end sending `undefined` as a path parameter
