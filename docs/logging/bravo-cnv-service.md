# bravo-cnv-service — logging fixes

**Squad:** Internal Service
**Production service:** `prod-ms-cnv`
**Stack:** Go, zerolog, RabbitMQ, Temporal

The logging in this repo is fine. The problem is that something is failing 20,000 times a
day and the logging is doing its job.

---

## 1. 20,000 HCIS messages fail every day

`internal/rabbitmq/employeemq/employee_hcis_consumer.go:147`

```go
if err != nil {
    ctxLogger.Error().Any("employeeID", body.EmpNo).Err(err).Msg("Failed to update user access metadata")
    return rabbitmq.NackDiscard
}
```

Production, measured:

| Window | `Failed to update user access metadata` |
|---|---:|
| 6 hours | **4,995** |
| 1 day | about 20,000 |
| 7 days | 1.59 million errors on this service, nearly all of them this one |

This service produces more error logs than any other in the estate, and it is one message.

### It is not a retry loop

The handler returns `NackDiscard`, so failed messages are thrown away rather than requeued.
That means these are **20,000 distinct HCIS employee messages failing every day** and being
discarded.

Employee work location, job title and IAM role revocation are not being applied. That is a
correctness problem and possibly an access-control one — `UpdateMetadataConsumer` is what
sets `IAMRoleRevoked`.

### It also logs twice per failure

Lines 132–137 log an info line before every attempt:

```go
ctxLogger.Info().
    Str("emp_no", body.EmpNo).
    Str("incoming_worklocation_code", metadata.WorkLocationCode).
    Str("incoming_job_title_code", metadata.JobTitleCode).
    Str("incoming_job_title_name", metadata.JobTitleName).
    Msg("Updating user access metadata from HCIS message")
```

So each failure costs two entries. About 40,000 lines a day from one consumer.

### Fix, in order

1. **Find out why `UpdateMetadataConsumer` fails.** The error is currently attached with
   `.Err(err)` but nobody has read it. Start there — one query on the error text will
   classify it. This is the actual work.
2. **Log the reason, not just the message.** Add the failure class so the next person can
   triage without reading code:

   ```go
   ctxLogger.Error().
       Str("employee_id", body.EmpNo).
       Str("failure", classify(err)).
       Err(err).
       Msg("Failed to update user access metadata")
   ```

3. **Drop the pre-attempt info line to debug.** It duplicates fields the error line already
   carries, and on the success path it tells you nothing the success line does not.
4. **If some failures are expected** — for example an employee number that does not exist
   yet — split those out and log them at debug. Only log an error when something is wrong.

Fixing the root cause removes about 40,000 log lines a day and restores employee metadata
sync. The logging change alone would hide the problem, so do them in this order.

---

## 2. Everything else in this repo is small

| Item | Count | Location |
|---|---:|---|
| `log.Error().Err(err)` with a message | 6 | `internal/service/pefindo/process_event_publisher.go` (2), `internal/temporal/activity/generic/process_activity.go` (1) |

Six sites, all reasonable. No body logging, no `printStackTrace` equivalent, no debug
levels left on. zerolog is already structured and JSON by default.

**This repo is a good template for the Go services.** `bravo-partnership-service`,
`bravo-backoffice-service` and `lora-task-service` could copy its logger setup.

---

## 3. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — fix the HCIS failure | Rp 3–8M | medium |

The saving is a side effect. The reason to do this is that 20,000 employee access updates a
day are being discarded.

---

## Checklist

- [ ] Query the error text on `prod-ms-cnv` to classify why `UpdateMetadataConsumer` fails
- [ ] Fix the underlying failure
- [ ] Add a `failure` classification field to the error log
- [ ] Move the pre-attempt info line at `employee_hcis_consumer.go:132` to debug
- [ ] Split expected failures out to debug, leave genuine errors at error
- [ ] Confirm whether discarded messages mean IAM role revocations were missed
