# bravo-inventory-management-service — logging fixes

**Squad:** Asset Management
**Production service:** `prod-inventory-management`
**Stack:** Java, Spring Boot

This is the only repo in the estate with `loggerLevel: full` written directly into
`application-prod.yaml`. It happens to be harmless today. It is one line from not being.

---

## 1. `loggerLevel: full` in the production profile

`src/main/resources/application-prod.yaml`, lines 1–7:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: full
        connectTimeout: 30000
        readTimeout: 30000

logging:
  level:
    root: WARN
```

18 Feign client interfaces are covered by that `default`.

**It emits nothing.** Feign writes bodies at DEBUG, and `root: WARN` puts every logger two
levels above that. No package-specific override raises them.

So the current cost is zero. But this configuration says "log every upstream request and
response body in production" and is relying on a separate setting, in the same file, to
contradict it. Anyone who later adds a package-level debug entry to chase a bug turns on
full body logging for 18 clients without realising.

Of the six repos carrying `loggerLevel: full`, this is the one most likely to surprise
someone, because the other five at least keep it out of the production profile.

### Fix

Delete the `loggerLevel: full` line. Keep the timeouts:

```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 30000
        readTimeout: 30000
```

Two minutes of work. No behaviour change.

---

## 2. Five DEBUG entries in the SIT profile

`src/main/resources/application-sit.yaml` carries five DEBUG/TRACE levels and a
`loggerLevel: full`, plus a payload-logging filter entry.

SIT runs in `bravo-project-nonprod`, which costs **Rp 56.4M a month** in Cloud Logging. Non-
production debug settings are not free — they are a third of the logging bill estate-wide.

### Fix

Lower SIT to INFO. If a developer needs debug in SIT, they can set it for an afternoon and
put it back. It should not be the committed default.

---

## 3. Smaller items

| Item | Count | Note |
|---|---:|---|
| Payload-logging filter entries | 3 | In `application-sit.yaml`, `application-local.yaml` and one more — not prod |
| `show-sql: true` | 1 | `application-local.yaml` only — fine |
| Exception logs with throwable | 5 | `AgreementServiceImpl.java` (2) and others — low |

This repo is in good shape apart from item 1. Five exception-logging sites is the lowest
count of any Java service reviewed.

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — remove `loggerLevel: full` from prod | Rp 0 today | removes a risk, not a cost |
| 2 — lower SIT debug levels | Rp 1–3M | medium |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This service is one of only two in the
pack where that workaround is switched on in production.**

| | Seven days, production |
|---|---:|
| Spans | 77,840 |
| Log entries | 492,884 |
| of which `info` | 475,591 |
| Log entries already carrying `dd.trace_id` in their text | **5,819** |

Note the ratio: this service writes six log lines for every span it records. That is the
wrong way round, and it is the signature of always-on request logging.

### Why it is on

Two settings line up:

- `application.yaml:110` — `enableBfiLogger: ${SETTING_FEATURES_ENABLEBFILOGGER:true}`. The
  default is **true**, so `config/LoggerConfiguration.java` registers `bravo-lib-logging`'s
  `RequestLoggingFilter` and its `FeignClientFilter` as the `@Primary` Feign logger.
- `application-prod.yaml:5` — `loggerLevel: full`, which is item 1 above.

Together those mean the shared library's request logger and full Feign logging are both live
in production. Every other repo in this pack either gates the library behind a flag that is
false, or sits above DEBUG so the code is a no-op.

The masking and truncation behaviour lives inside `com.bfi.bravo:bravo-lib-logging`, which is
not in `squads/`. **Nobody on this analysis could read it.** Before defending this setup,
someone has to open that library and confirm what it does with a payload.

### The good news, which is specific to this service

5,819 of its log entries already carry `dd.trace_id` in the message text — the second
highest count in the estate. The tracer's log injection is working here. What is missing is
that Datadog does not parse it: a search for `@dd.trace_id` across **all** of production
returns zero results, because the field sits inside a text message rather than in a JSON
attribute.

That makes this service the shortest path to proving log-to-trace correlation. The fields
are already being written.

### What you get back

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe.

Remote Configuration has to work first, and it is failing here: 302 failed polls in two
days, `unexpected response code Internal Server Error 500 ... empty targets meta in director
local store`. Thirteen production services report the same error.

### What to do

1. Set `SETTING_FEATURES_ENABLEBFILOGGER=false` in the production manifest, or change the
   YAML default from `true` to `false`. This is a bigger lever than item 1.
2. Remove `loggerLevel: full` from `application-prod.yaml` (item 1).
3. Read `bravo-lib-logging` and write down what `RequestLoggingFilter` actually captures.
   Fifteen repos depend on it; this is the only one running it in production.
4. Volunteer this service as SRE's pilot for log-to-trace correlation. It is already most of
   the way there.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces (backend) | `prod-inventory-management` | 78,780 spans |
| Logs | `prod-inventory-management` | 494,533 entries |
| Traces (browser) | `bravo-inventory-management-system` | 4,333 spans |

**Names match, and the split is correct.** This is worth stating plainly, because it looks
like a duplicate and is not.

`bravo-inventory-management-system` is the **RUM application** for the browser front end at
`ims.bfi.co.id`. Its spans are `type: browser`, and they carry
`peer.service: prod-inventory-management` — meaning browser requests are already joining the
backend trace. Session Replay is on.

This is the only service in the estate with working front-end to back-end trace linkage. It
is the pattern the other consoles should copy, not a defect to clean up. Leave both
identities alone.

One thing to keep an eye on: logs (494,533) outnumber backend spans (78,780) by more
than six to one. That ratio is unusual and suggests logging on paths that are not traced —
batch jobs or consumers. Worth a look when the squad works through the items above.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-inventory-management`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-inventory-management"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-inventory-management
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in the GitOps repo, not here. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-inventory-management` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-inventory-management env:prod

# APM Traces
service:prod-inventory-management env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-inventory-management` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## Checklist

- [ ] Delete `loggerLevel: full` from `application-prod.yaml`
- [ ] Lower the five DEBUG/TRACE entries in `application-sit.yaml` to INFO
- [ ] Remove `loggerLevel: full` from `application-sit.yaml`
- [ ] Leave the RUM application `bravo-inventory-management-system` as it is — it is correct
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template
- [ ] Check why log volume is six times backend span volume
- [ ] Set `SETTING_FEATURES_ENABLEBFILOGGER=false` in production, or flip the YAML default
- [ ] Read `bravo-lib-logging` and record what `RequestLoggingFilter` actually captures
- [ ] Volunteer this service as SRE's log-to-trace correlation pilot — 5,819 entries already carry `dd.trace_id`
