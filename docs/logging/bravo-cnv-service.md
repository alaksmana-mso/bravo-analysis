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

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This repo already solves the problem the
way the rest of the estate should, and it is the design to copy.**

| | Seven days, production |
|---|---:|
| Spans | 12,523,665 |
| Log entries | 3,621,224 |
| Entries carrying a captured body | 0 |

### Why it is right

`cmd/grpc/main.go:100` wires `httpclient.NewLoggedTransport` with four things that none of
the Java repos have all of at once:

- **A switch per direction** — `WithRequestBodyLogging` and `WithResponseBodyLogging`, off
  or on independently.
- **A size limit per direction** — `HTTP_CLIENT_REQUEST_BODY_LIMIT` and
  `HTTP_CLIENT_RESPONSE_BODY_LIMIT`, 32,768 bytes in `.env.example`.
- **Field masking** — `logger.JSONScrubberFunc` over about thirty field names, including
  `nik`, `ktp`, `ktp_number`, `npwp_number`, `selfie`, `selfie_photo`, `password`,
  `old_password`, `token`, `signature`, `mother_maiden_name`, `birth_date` and `email`, on
  request and response separately.
- **An explicit statement of intent** — the comment above both blocks reads
  `NON PRODUCTION ENVIRONMENT ONLY`.

And it holds in production: a search for body attributes on `prod-ms-cnv` over seven days
returns nothing. The flags are off where they should be off.

**So bodies are not this service's problem.** The 20,000 failed HCIS messages a day are, and
that is item 1 above.

### What the replacement would be, and the catch

Datadog's Live Debugger needs the Datadog tracer library. This service is instrumented with
**OpenTelemetry** — `go.opentelemetry.io/otel v1.45.0` and the `otelhttp` and `otelgrpc`
contrib packages are the direct dependencies; `github.com/DataDog/dd-trace-go/v2 v2.8.1` is
present only as an indirect dependency pulled in by the Agent packages.

That matters. dd-trace-go does subscribe to Datadog's `LIVE_DEBUGGING` remote-config product
at the versions in use, but you only get that by instrumenting with dd-trace-go. Under OTel
there is no probe mechanism. **Live Debugger is not available to this service as it stands**,
and nobody should promise it to this squad until the tracing-stack decision in
[sre-datadog-recommendations.md §7](sre-datadog-recommendations.md) is made.

### What to do

1. Keep the logged transport exactly as it is, and keep the flags off in production.
2. Offer `JSONScrubberFunc` and its field list to the `bravo-lib-logging` maintainers, and
   to the `bravo-bpm-service` squad — their `CustomFeignLogger` writes bodies to production
   logs with no masking at all.
3. Put identifiers on the OTel span instead of expecting bodies: application id, HCIS
   message id, Temporal workflow and run id.
4. Feed this repo into the tracing-stack decision. It is the clearest example of what the
   OTel choice costs: no Live Debugger, whatever SRE enables for the Java estate.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-cnv` | 12,455,513 spans |
| Logs | `prod-ms-cnv` | 3,658,319 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-cnv`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-cnv"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-cnv
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-cnv` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-cnv env:prod

# APM Traces
service:prod-ms-cnv env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-cnv` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `app-deployment/cnv/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `warn` |
| `HTTP_SERVER_BODY_LOGGING` | `true` |
| `HTTP_SERVER_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_SERVER_RESPONSE_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_REQUEST_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_RESPONSE_BODY_LOGGING` | `true` |
| `HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS` | `phone,nik,account_number,selfie_photo,name,birth_date,dob…` (30 fields) |
| `HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS` | `password,signature,api_key,token` |

Bodies are logged in production **with a masked-field list set here** — the pattern SRE asks for. The list is the squad's to keep current.

---

## Implementation status

**Pull request: [bravo-cnv-service#726](https://github.com/bfi-finance/bravo-cnv-service/pull/726)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-cnv-service/tree/fix/logging), head `3b4ccd4d`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bravo-cnv-service/pull/726/files) · [Commits](https://github.com/bfi-finance/bravo-cnv-service/pull/726/commits) · [Compare against master](https://github.com/bfi-finance/bravo-cnv-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

Nothing on the Java side changes this pull request. The Go wrapper fix, [bfi-go-pkg#175](https://github.com/bfi-finance/bfi-go-pkg/pull/175) (`JSONScrubber` masks non-string values), is still open; the masked-field lists stay a per-service, per-environment setting in `app-deployment`, as SRE asked on 14 September.

CI on the current head is **fully green**.

**Codacy review, answered 18 September 2026.** 2 Codacy thread(s); 2 fixed in `eade5f79` (fix(logging): warn when an IAM role revocation fails; trim a comment). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commit:

- fix(logging): stop logging every HCIS attempt twice

Files:

- `internal/rabbitmq/employeemq/employee_hcis_consumer.go`

**Compiled and formatted; not unit-tested.** Go is available through `mise`: `go build ./...` passes and `gofmt` is clean on the changed file. `golangci-lint` could **not** run here — this repository vendors its dependencies and `vendor/modules.txt` is out of step with `go.mod`, which `golangci-lint` refuses to load; running `go mod vendor` would rewrite the vendor tree, so it was left alone. Lint therefore remains unverified locally for this repository. CI on the pull request is the authority.

---

## Checklist

- [ ] Query the error text on `prod-ms-cnv` to classify why `UpdateMetadataConsumer` fails
- [ ] Fix the underlying failure
- [ ] Add a `failure` classification field to the error log
- [ ] Move the pre-attempt info line at `employee_hcis_consumer.go:132` to debug
- [ ] Split expected failures out to debug, leave genuine errors at error
- [ ] Confirm whether discarded messages mean IAM role revocations were missed
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Keep the logged transport as it is, and keep both body-logging flags off in production
- [ ] Offer `JSONScrubberFunc` and its field list to the `bravo-lib-logging` maintainers and the bpm squad
- [ ] Feed this repo into the tracing-stack decision — on OpenTelemetry there is no Live Debugger
