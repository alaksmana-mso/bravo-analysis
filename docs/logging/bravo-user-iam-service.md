# bravo-user-iam-service — logging fixes

**Squad:** Internal Service
**Production services:** `prod-ms-user-iam`, plus a BAU deployment of the same image
**Stack:** Go, zerolog, dd-trace-go v2.7.1

This file exists for one reason: this repo is the only one in `squads/` whose production
workload is **split across more than one Datadog identity**. Seven other services have the
same defect, but they belong to the CONFINS vendor estate and have no repo here.

The logging itself is in good shape. That is worth saying first, because it is rare.

---

## 1. What this service already does right

Over seven days, `prod-ms-user-iam` sent 153,506 log entries, and Datadog resolved the
severity on every one of them:

| Level | Entries |
|---|---:|
| `error` | 77,159 |
| `info` | 74,472 |
| `warn` | 1,875 |

Compare `prod-ms-calculation`, which sent 2,387,623 entries and got `status:error` on 1,325
of them because its level is rendered inside the message string. zerolog emits JSON, Datadog
parses it, and severity survives. This is the pattern
[squads-guide.md Rule 4](squads-guide.md#rule-4-emit-json-and-let-the-framework-do-it) asks
every squad to follow, and this repo is already there.

One thing to look at, though it is not a cost item: **half of everything this service logs is
an error.** 77,159 errors in a week either means something is genuinely wrong at that rate,
or `error` is being used for conditions that are expected — failed logins, expired tokens.
If it is the second, those belong at `warn` or `info`, and the level stops meaning anything
when it is used this way. Worth 30 minutes with the top few messages.

---

## 2. The BAU deployment is split across three names

The same image runs twice in production. The second deployment is the problem.

| | Name in Datadog | Volume, 7 days |
|---|---|---:|
| Main — traces | `prod-ms-user-iam` | 4,960,106 spans |
| Main — logs | `prod-ms-user-iam` | 153,506 entries |
| **BAU — traces** | `prod-ms-bau-user-iam` | **1,939,316 spans** |
| **BAU — logs** | `bau-prod-ms-user-iam` | **36 entries** |
| **BAU — logs** | `prod-ms-bau-user-iam` | **15 entries** |

Two things are wrong.

**The BAU deployment's log name and trace name do not match.** The trace name is
`prod-ms-bau-user-iam`. The log name is `bau-prod-ms-user-iam`. Same words, different order.
Datadog has no way to know these are one workload, so it builds two Service Catalog entries,
and any dashboard or monitor written against one covers half the picture.

You can see the collision directly on the log events. A single BAU log line carries **two
`service` tags**:

```
service:bau-prod-ms-user-iam     <- from the Kubernetes container and deployment name
service:prod-ms-user-iam         <- from the kube_app_instance label
```

Datadog picks one. Neither is the name the traces use.

**The BAU deployment barely logs at all.** 51 log entries against 1,939,316 spans. That is
one log line per 38,000 requests. The main deployment's ratio is one per 32. Something is
stopping BAU's logs from reaching Datadog — most likely that the split identity is sending
them somewhere nobody is looking.

The practical effect is that a service handling nearly two million requests a week is,
for operational purposes, dark.

---

## 3. How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name. The
service name on a **trace** comes from `DD_SERVICE`. Nothing makes those agree, and here
they do not.

Stop setting the name in two places. Put the Datadog unified tagging labels on the pod
template, and the Agent gives logs, traces, metrics and profiles the same identity:

```yaml
# BAU deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bau-user-iam"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then source the environment variables from those same labels, so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_SERVICE
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

**Pick `prod-ms-bau-user-iam` and keep it.** It matches the `prod-ms-*` convention the rest
of the estate uses, and it is already the name on 1.9 million spans, so choosing it means no
trace history is orphaned.

These files are in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template/.github/workflows/go-deploy-prod.yaml` with `service: user-iam`
— a template **104 of the 152 repos share**. Raise it with Platform as one change to the
shared template rather than as a change to this repo.

### Then find the missing logs

Renaming will not by itself produce the logs that are not arriving. Once the identity is
single, check:

1. Whether the Agent is collecting this pod at all — search `kube_deployment:bau-prod-ms-user-iam`
   in Logs, not `service:`.
2. `docker-entrypoint.sh` pipes output through `tee` into
   `${SERVICE_LOG_DIR}/${SERVICE_NAME}.json` when that directory exists. stdout still flows,
   so this should not break collection, but it does write every line twice and fills
   container storage with a file nobody reads. Confirm `SERVICE_LOG_DIR` is unset in the BAU
   deployment.
3. Whether `LOG_LEVEL` is set higher on BAU than on the main deployment.

---

## 4. How to check your own service

Two searches, one minute, in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bau-user-iam env:prod

# APM Traces
service:prod-ms-bau-user-iam env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to
`kube_deployment:bau-prod-ms-user-iam` to tell them apart: results there mean the logs are
arriving under a different service name.

---

## 5. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — error level used for expected conditions | Rp 0–1M | low, needs the message breakdown first |
| 2 — split identity | **Rp 0** | this is a correctness fix, not a cost fix |

Nothing here saves money. It is on the list because a service running 1.9 million requests a
week with 51 log lines and two names is not observable, and because this repo is the one
place a squad can fix the pattern that also affects seven CONFINS services.

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service does not, and for the BAU
deployment the question is academic: almost nothing it writes arrives.**

| | Seven days, production |
|---|---:|
| `prod-ms-user-iam` spans | 4,977,454 |
| `prod-ms-user-iam` log entries | 155,234 |
| `prod-ms-bau-user-iam` spans | 1,943,069 |
| `prod-ms-bau-user-iam` log entries | **51**, across three names |
| Entries carrying a captured body, either deployment | 0 |

### What exists, and why it is off

`cmd/grpc/main.go:78` wires the same logged HTTP transport that `bravo-cnv-service` uses,
with `HTTP_CLIENT_REQUEST_BODY_LOGGING` and `HTTP_CLIENT_RESPONSE_BODY_LOGGING` switches and
per-direction size limits. A search for body attributes on either deployment over seven days
returns nothing, so both flags are false in production. That is correct — this is the
identity service, and its request bodies carry credentials by definition.

Keep them off. There is no debugging argument strong enough to justify capturing IAM
payloads into a system with broad read access.

### What the replacement would be, and the catch

Datadog's Live Debugger needs the Datadog tracer library. This service is instrumented with
**OpenTelemetry** — `go.opentelemetry.io/otel v1.43.0` with the `otelhttp` and `otelgrpc`
contrib packages as the direct dependencies. `github.com/DataDog/dd-trace-go/v2 v2.7.1` is
present only as an indirect dependency.

Under OpenTelemetry there is no probe mechanism, so **Live Debugger is not available to this
service as it stands** — and for an IAM service, that is arguably the right outcome. The
tracing-stack decision is in
[sre-datadog-recommendations.md §7](sre-datadog-recommendations.md).

### What to do

1. Nothing to remove. Confirm both body-logging flags are false in both deployment manifests
   and record the answer.
2. Fix the BAU deployment's log delivery first. 51 log entries against 1.9 million spans is
   the real observability problem here, and it is covered above.
3. Put identifiers on the OTel span — realm, client id, user id — never the token or the
   credential.

---

## Checklist

- [ ] Choose `prod-ms-bau-user-iam` as the single name for the BAU deployment
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the BAU pod template
- [ ] Source `DD_ENV` / `DD_SERVICE` / `DD_VERSION` from those labels
- [ ] Raise the unified tagging change against `bfi-base-template`, not just this repo
- [ ] Find why the BAU deployment sends 51 log entries against 1.9M spans
- [ ] Confirm `SERVICE_LOG_DIR` is unset so `docker-entrypoint.sh` does not `tee` to a file
- [ ] Review the top error messages — 77,159 errors a week suggests `error` is doing `warn`'s job
- [ ] Confirm both `HTTP_CLIENT_*_BODY_LOGGING` flags are false in both deployment manifests
- [ ] Do not enable IAM body logging in production under any circumstances
- [ ] Feed this repo into the tracing-stack decision — on OpenTelemetry there is no Live Debugger
