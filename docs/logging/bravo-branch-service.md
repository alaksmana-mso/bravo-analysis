# bravo-branch-service — logging fixes

**Squad:** Internal Service
**Production service:** `prod-ms-branch`
**Stack:** Java, Spring Boot

Moderate findings. The logs-inside-loops item is the one worth attention, because branch
and survey group data is processed in batches.

---

## 1. Six logs inside loops

| File | Count |
|---|---:|
| `src/main/java/com/bfi/bravo/service/impl/BravoBranchTransactionalServiceImpl.java` | 1 |
| `src/main/java/com/bfi/bravo/service/impl/SurveyGroupTransactionalServiceImpl.java` | 1 |

Branch and survey group syncs run over the full branch list. One log line per branch means
the output scales with the estate, and it grows every time BFI opens a branch.

### Fix

Log once before the loop with the count, once after with the outcome, and inside only on
failure:

```java
log.info("branch upsert starting: count={}", branches.size());
// loop, log failures only
log.info("branch upsert done: ok={} failed={}", ok, failed);
```

---

## 2. 66 exception logs passing the throwable

Densest file: `src/main/java/com/bfi/bravo/service/impl/BranchUpsertServiceImpl.java` with 4.

Combined with item 1, a failing branch sync produces a stack trace per branch. With
multi-line aggregation off cluster-wide, each trace is one entry per frame.

That combination is how a routine upstream outage turns into a large log bill for an hour.

### Fix

Structured warn lines for expected failures. Traces only where diagnosis needs one.

---

## 3. `CommonsRequestLoggingFilter` — dormant

`src/main/java/com/bfi/bravo/config/RequestLoggingFilterConfig.java` registers it with
payload logging on. The logger sits at INFO in production, so it emits nothing.

Set `setIncludePayload(false)` or move the bean behind `@Profile("local")`, and pin the
level in `application-prod.yaml`.

---

## 4. Smaller items

| Item | Count | Note |
|---|---:|---|
| DEBUG/TRACE in YAML | 8 | `application-unit-test.yaml` and local profiles — no production impact |
| `System.out.print` | 2 | `src/test/` only |

---

## 5. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — logs in loops | Rp 1–3M | medium, spikes during syncs |
| 2 — exception logs | Rp 1–2M | medium |
| 3 — dormant payload filter | Rp 0 today | risk removal |

---

## Checklist

- [ ] Move loop logging out of the loop in `BravoBranchTransactionalServiceImpl`
- [ ] Same in `SurveyGroupTransactionalServiceImpl`
- [ ] Review the exception logs in `BranchUpsertServiceImpl.java`
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
