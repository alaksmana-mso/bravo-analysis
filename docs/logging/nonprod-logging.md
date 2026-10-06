# Logging in SIT and UAT — what reasonable means

Written 6 October 2026. Evidence: every `values-sit*.yaml` and `values-uat*.yaml` in
`app-deployment` and `bfi-app-deployment` at `origin/master` on 6 October; GCP billing through
FinOps for September 2026; Datadog log indexes for the last seven days.

The rest of this folder is about production. SIT and UAT serve no customer, but they log
into the same bill, they hold copies of customer records more often than anyone admits, and
their manifests are where debug levels and body logging are switched on and then forgotten.
This page says what "reasonable" looks like there and how far the estate is from it.

## 1. Where SIT and UAT logs go, and what they cost

**No SIT or UAT log reaches Datadog.** Seven days of indexes carry `prod`, `prod-sharia`,
`digital-prod` and an empty `env`; nothing else. Non-production logs go to Cloud Logging only,
in the project that hosts the cluster.

| Project | What runs there | Cloud Logging, September 2026 |
|---|---|---:|
| `bravo-project-nonprod` | Bravo dev, SIT, UAT | **Rp 79.0M** |
| `bfi-devsecops` | CI runners, the image and Maven registries | **Rp 78.5M** |
| `bravo-project-331802` | Bravo **production** | Rp 147.6M |

Read that twice. The two non-production projects spent **Rp 157.5M on logs in September**,
more than production did. `logging-cost.md` §1 put non-production at Rp 93.1M a month when it
was written in August; the September bill is higher, and half of it is `bfi-devsecops`, which
runs no application at all — its Cloud Logging line is as large as the whole Bravo
non-production project's. What in a CI project writes Rp 78M of logs a month is the first
question for Platform.

Two things could not be verified from this machine: the retention of the `_Default` log bucket
in those projects and whether any exclusion filter exists. `gcloud` needs a fresh login
(`gcloud auth login`); the commands are at the end of this page. The recommendation in the
README (item 3, 7-day retention and an exclusion filter on non-prod) stands until someone reads
those two settings.

## 2. What the manifests say today

Of the services with logging settings in their SIT or UAT values file:

| | SIT | UAT |
|---|---:|---:|
| Services with logging settings | 106 | 104 |
| Root logger at `debug` or `trace` | 56 | 57 |
| Body logging switched on | 39 | 42 |
| Body logging on **with an empty masked-field list** | 17 | 20 |
| Feign at `full` or the custom Feign body logger on | 4 | 3 |
| A Java package pinned at `DEBUG` | 6 | 5 |

Half the estate runs non-production at `debug`. Forty services write request and response
bodies there, and for seventeen to twenty of them every `*_JSON_MASKED_FIELDS` is `""`, so a
NIK, a phone number or a bank account in a SIT payload is written in full. The Go wrapper does
exactly what the manifest says; the manifest says mask nothing.

## 3. The baseline: what reasonable means in SIT and UAT

SIT and UAT exist so that engineers can see what a request did. Body logging is **allowed**
there. Everything else follows from five rules, each one a manifest value:

| # | Rule | Why |
|---|---|---|
| 1 | Root logger at `info`. `debug` is switched on for one service, for one investigation, and switched back. | At `debug` every framework line ships. Half the SIT estate has run that way for a year; nobody is reading it. |
| 2 | No Java package pinned at `DEBUG` in a values file; the Commons request-logging filter at `OFF`, as in production. | A package at `DEBUG` is a body logger by another name (`com.bfi.bravo.client.confins`, `bravo.adapter`). |
| 3 | Feign at `basic`, never `full`. | `full` writes every outbound body, unmasked, with no cap. The bodies that matter are the ones the service receives, and those have a masked logger. |
| 4 | Body logging may stay on, but **every `*_JSON_MASKED_FIELDS` carries the standard list**; `""` is not a value. On-error-only where the wrapper supports it. | Test data is not always fake. UAT is loaded from production copies for regression runs; SIT gets real NIKs pasted from tickets. |
| 5 | Java lib body logging (`REQUEST_BODY_LOGGING`, `RESPONSE_BODY_LOGGING`) only with a written `SENSITIVE_KEYS`. | Same reason. The lib's default list is four words. |

And two rules for the platform, not the manifests: **7-day retention and an exclusion filter**
on the non-production log buckets (health checks, readiness probes, Hibernate SQL), and **Cloud
SQL audit and slow-query logs off** in non-production (`logging-cost.md` §4, item 3). None of
this changes what an engineer can see while debugging; it changes what sits in a bucket for
thirty days afterwards.

The standard lists are the ones SRE already uses: the Go `GENERIC_JSON_MASKED_FIELDS` and
`PHONE_JSON_MASKED_FIELDS` from `backoffice/values-prod.yaml`, and the Java `SENSITIVE_KEYS`
from `onboarding/values-prod.yaml`.

## 4. The twenty services of this programme, SIT and UAT

| Service | SIT today | UAT today | Against the baseline |
|---|---|---|---|
| bravo-bpm-service | `INFO`; lib request and response bodies on with `SENSITIVE_KEYS`; custom Feign logger on, headers off | `INFO`; custom Feign logger on, headers off | Reasonable. Bodies masked by the lib; the Feign logger becomes masked and capped when #10463 merges |
| bravo-cnv-service | **`debug`**; server and client bodies on, two masked lists written | same | Rule 1: `debug` → `info` |
| bravo-onboarding-service | `INFO`; `ENABLEBFILOGGER=true` with `SENSITIVE_KEYS`; **Feign `full`**; two packages at `DEBUG` | `INFO`; lib response bodies on with keys | Rules 2 and 3 on SIT (Feign `basic`, `oauth` and `aspect` packages to `INFO`); the sharia files pin `aspect` at `DEBUG` too |
| bfi-insurance-api | no settings | no settings | Nothing to change in the manifest |
| bravo-lms-gateway | no settings | no settings | Nothing to change |
| bfi-digital-web-api | separate `digital-*` manifests, no logging settings | — | Nothing to change |
| lora-task-service | **`debug`**; server and client bodies on, on-error-only, **all four masked lists empty** | same | Rules 1 and 4: `info`, and the standard lists in all four fields |
| bravo-agency-service | `INFO`; `BRAVO_ADAPTER=DEBUG`, Commons filter `DEBUG`; Feign `BASIC` | same | Rule 2: adapter to `INFO`, filter to `OFF` (production already has both) |
| bravo-approval-engine-service | `INFO`, packages at `INFO` | same | Reasonable |
| bravo-core-proxy-service | `INFO`, packages at `INFO` | same | Reasonable |
| bravo-agreement-service | CONFINS client package at **`DEBUG`** | same | Rule 2 (production has it at `INFO`) |
| bravo-customer-service | **Feign `full`**, CONFINS client at **`DEBUG`** | same | Rules 2 and 3 |
| bravo-edoc-service | `INFO`; lib response bodies on, **no `SENSITIVE_KEYS`** | same | Rule 5 |
| bravo-branch-service | `INFO`; lib response bodies on, **no `SENSITIVE_KEYS`** | same | Rule 5 |
| bfi-payment-api | profile-gated in code; no manifest logging settings | — | Nothing to change |
| bravo-payment-service | no settings | no settings | Nothing to change |
| bravo-inventory-management-service | `INFO`; `ENABLEBFILOGGER=true`, request and response bodies on, **no `SENSITIVE_KEYS`** | same | Rule 5 |
| bravo-surveyor-console | browser application | — | n/a |
| bravo-user-iam-service | **`debug`**; client bodies on, no masked lists written (the wrapper logs nothing for the server side) | same | Rule 1 |

## 5. The change, written out

Applying the five rules to the twenty services' SIT and UAT files (including the `-sharia`
variants) changes **29 files** in `app-deployment`. Body logging is switched off nowhere; every
edit is a level, a Feign mode, or a masked-field list. The list of edits:

```
cnv/values-sit.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
cnv/values-uat.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
onboarding/values-sit-sharia.yaml
    LOGGING_LEVEL_ID_CO_BFI_BRAVO_ASPECT: DEBUG -> INFO (rule 2)
onboarding/values-sit.yaml
    SPRING_CLOUD_OPENFEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    LOGGING_LEVEL_ID_CO_BFI_BRAVO_ADAPTER_HTTP_OAUTH: DEBUG -> INFO (rule 2)
    LOGGING_LEVEL_ID_CO_BFI_BRAVO_ASPECT: DEBUG -> INFO (rule 2)
onboarding/values-uat-sharia.yaml
    LOGGING_LEVEL_ID_CO_BFI_BRAVO_ASPECT: DEBUG -> INFO (rule 2)
lora-task/values-sit.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
    HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
lora-task/values-uat.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
    HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
    HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: "" -> "<standard list>" (rule 4)
agency/values-sit-sharia.yaml
    LOGGING_LEVEL_BRAVO_ADAPTER: DEBUG -> INFO (rule 2)
    LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER: DEBUG -> OFF (rule 2)
agency/values-sit.yaml
    LOGGING_LEVEL_BRAVO_ADAPTER: DEBUG -> INFO (rule 2)
    LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER: DEBUG -> OFF (rule 2)
agency/values-uat-sharia.yaml
    LOGGING_LEVEL_BRAVO_ADAPTER: DEBUG -> INFO (rule 2)
    LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER: DEBUG -> OFF (rule 2)
agency/values-uat.yaml
    LOGGING_LEVEL_BRAVO_ADAPTER: DEBUG -> INFO (rule 2)
    LOGGING_LEVEL_COMMONSREQUESTLOGGINGFILTER: DEBUG -> OFF (rule 2)
agreement/values-sit-sharia.yaml
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
agreement/values-sit.yaml
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
agreement/values-uat-sharia.yaml
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
agreement/values-uat.yaml
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
customer/values-sit-sharia.yaml
    FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
customer/values-sit.yaml
    FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
customer/values-uat-sharia.yaml
    FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
customer/values-uat.yaml
    FEIGN_CLIENT_CONFIG_DEFAULT_LOGGERLEVEL: full -> basic (rule 3)
    LOGGING_LEVEL_COM_BFI_BRAVO_CLIENT_CONFINS: DEBUG -> INFO (rule 2)
edoc/values-sit.yaml
    SENSITIVE_KEYS: added (rule 5)
edoc/values-uat.yaml
    SENSITIVE_KEYS: added (rule 5)
branch/values-sit.yaml
    SENSITIVE_KEYS: added (rule 5)
branch/values-uat.yaml
    SENSITIVE_KEYS: added (rule 5)
inventory-management/values-sit.yaml
    SENSITIVE_KEYS: added (rule 5)
inventory-management/values-uat.yaml
    SENSITIVE_KEYS: added (rule 5)
user-iam/values-sit-sharia.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
user-iam/values-sit.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
user-iam/values-uat-sharia.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
user-iam/values-uat.yaml
    LOGGER_LEVEL: "debug" -> "info" (rule 1)
```

The full unified diff is [nonprod-logging-proposal.diff](nonprod-logging-proposal.diff). It was
generated by a script that applies the five rules to copies of the files, so SRE can run the
same script over the rest of the estate: across all SIT and UAT files it would touch **137**
(68 SIT, 69 UAT), and 188 with dev and test included.

**This is a proposal, not a pull request.** The production manifest change
([app-deployment#13820](https://github.com/bfi-finance/app-deployment/pull/13820)) has waited
three weeks for the SAs' confirmation; a second pull request on the same repository was not
raised from here. SRE can apply the diff as it stands, or run the generator over every
environment; either way the SIT and UAT change needs no rollout window, because nothing a
tester sees changes.

## 6. Order of work

1. Platform reads the two settings this page could not: `_Default` bucket retention and
   exclusion filters in `bravo-project-nonprod` and `bfi-devsecops`, and finds what in
   `bfi-devsecops` writes Rp 78M of logs a month.
2. 7-day retention and an exclusion filter on both projects; Cloud SQL audit and slow-query
   logs off in non-production. Together these are the Rp 60–80M a month in `logging-cost.md`
   §4 items 2 and 3, and nothing a squad does changes them.
3. SRE applies the 29-file diff, then the generator over the remaining SIT and UAT files.
4. From then on: a `debug` level or a `full` Feign client in a `values-sit` or `values-uat`
   file is a review comment, the same as in production.

## Appendix — the two checks that need a login

```bash
gcloud auth login
for p in bravo-project-nonprod bfi-devsecops; do
  gcloud logging buckets list --project "$p" --format='table(name,retentionDays,locked)'
  gcloud logging sinks describe _Default --project "$p" --format='yaml(exclusions)'
done
```
