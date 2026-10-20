# How we collect logs: Datadog, Cloud Logging and Coralogix

Written 20 October 2026. Scope: the Bravo GCP estate, which means the projects `bravo-project-331802` (production) and `bravo-project-nonprod` (dev, SIT and UAT), and the organisation-level log sinks. The CONFINS `core-system-prod` cluster is out of scope. Sources and queries are in [How this was measured](#how-this-was-measured).

## Summary

- **Three platforms, three different jobs.** Datadog is where squads read production application logs. Cloud Logging is the default store for every GCP log, and it is the only log tool for SIT and UAT. Coralogix is the Security team's SIEM (security information and event management system). It receives the GCP logs that are *not* application logs, and Snowbit runs managed detection on it.
- **Coralogix is not an application log platform.** An organisation-level sink sends every GCP log to Coralogix *except* container, Kubernetes-cluster and Cloud SQL logs. This answers the question in [SRE-1826](https://bfifinance.atlassian.net/browse/SRE-1826), which was closed as "Drop" without an answer.
- **Production application logs are paid for twice.** The same container lines go to Cloud Logging (about Rp 3M a day) and to Datadog. Squads use Datadog for production. Excluding most production container lines from Cloud Logging could save up to about Rp 75M a month. It needs one check first: some busy services send no logs to Datadog at all.
- **Datadog reads log files, not stdout.** This file setup caused the NUL padding that was 89% of our Datadog log bytes. Moving every service to stdout collection removes the cause and the nightly cleanup jobs.
- **One quick win is ready.** The pull request [bravo-terraform#367](https://github.com/bfi-finance/bravo-terraform/pull/367) adds production's own exclusion filters to non-production, and it waits for review. Cloud SQL logs alone cost about Rp 20M a month there.

## What each platform receives today

| Source | Collector | Cloud Logging | Datadog | Coralogix | Who reads it |
|---|---|---|---|---|---|
| Application containers, production | GKE logging agent (`fluentbit-gke`) reads stdout. The Datadog Agent tails `/tmp/log/<pod>.json`, which `tee` writes. | Yes | Yes | No (excluded) | Squads, in Datadog |
| Application containers, SIT and UAT | `fluentbit-gke` reads stdout | Yes | No: log collection is off in the non-production Agent | No (excluded) | Squads, in Cloud Logging |
| Cloud SQL | GCP | Yes. Production excludes INFO and below. Non-production excludes nothing. | No | No (excluded) | SRE, squads |
| VPC flow logs, load balancer, Cloud Armor | GCP | Yes | No | Yes | Security |
| Admin activity audit logs | GCP | Yes (`_Required` bucket) | No | Yes | Security, and CrowdStrike |
| Cloudflare, Palo Alto, Google Workspace, vCenter, AliCloud | Security's own integrations | No | No | Yes | Security (SOC) |
| Tyk Pump analytics, PAM bot and VPN scheduler audit events | Direct API calls | No | No | Yes | Security, Platform |

The rows for Cloudflare, Palo Alto and the other security sources come from two places. These are Security's Jira tickets (DKBFI-661 to DKBFI-666, DKBFI-105, DKBFI-171, DKBFI-248) and the Tyk revamp notes. I did not read the Coralogix account itself.

### The routing in GCP

The Log Router sends every log entry to every sink that matches. Each sink has its own exclusions, so excluding a log from one sink does not remove it from another.

| Sink | Level | Destination | Filter and exclusions |
|---|---|---|---|
| `_Default` | Each project | Cloud Logging `_Default` bucket, 30 days | Production excludes container lines at DEBUG or NOTICE, Cloud SQL at INFO or below, and one gRPC request-log pattern for partnership, rule-engine and scheduling. Non-production excludes nothing. |
| `_Required` | Each project | Cloud Logging `_Required` bucket | Admin activity and system-event audit logs. Not chargeable, cannot be changed. |
| `coralogix-synk` | Organisation, all child projects | Pub/Sub `bfi-host-project/topics/coralogix` | Everything except `k8s_container`, `k8s_cluster` and `cloudsql_database`. Created 21 February 2025. About 226 GiB a day on weekdays. |
| `crowdstrike-CrowdStrikeLogSink` | Organisation, all child projects | Pub/Sub in `bfi-devsecops` | Admin activity, system-event and policy audit logs, except projects named `sys-*` |
| `pam-request` | Production project | Pub/Sub in `bfi-devsecops` | Privileged Access Manager grant requests |

## What it costs

| Platform | Monthly cost | How it is billed | Trend |
|---|---|---|---|
| Cloud Logging, production | About Rp 112M at the 12 to 18 October rate (about Rp 155M from 15 September to 8 October) | Per GB written to the `_Default` bucket | Fell when the duplicate collector was removed ([SRE-1813](https://bfifinance.atlassian.net/browse/SRE-1813), [bravo-terraform#365](https://github.com/bfi-finance/bravo-terraform/pull/365), 9 October). Every container line is now stored once. |
| Cloud Logging, non-production | About Rp 59M at the 12 to 18 October rate | Per GB written | Cloud SQL logs are a third of it: 92 GB a day, about Rp 20M a month |
| Datadog logs | Rp 110.6M in September | The contract covers 256 GB a month. We pay overage for the rest. | Falling as the 19 `tee -a` fixes are released. customer-bff fell by more than 99% after its release. |
| Coralogix | About Rp 253M, flat since February | Fixed contract with Snowbit managed detection. The renewal ticket ITVM-194 describes the period 1 November 2026 to 31 October 2027. | Not a cost lever before the 2027 renewal |

Production Cloud Logging by resource type, average per day over 12 to 18 October (weekends are lower):

| Resource type | Cost per day | Share |
|---|---:|---:|
| `k8s_container` (application logs) | about Rp 3.03M | 81% |
| `gce_subnetwork` (VPC flow logs) | about Rp 0.27M | 7% |
| `http_load_balancer` | about Rp 0.22M | 6% |
| `k8s_cluster`, `gcs_bucket`, `service_account` and the rest | about Rp 0.22M | 6% |

## Problems, in order of cost

### 1. Production application logs are stored in Cloud Logging and in Datadog

Squads read production logs in Datadog. Cloud Logging still stores every production container line at INFO and above, which was about 480 GB on a weekday in mid-October. INFO is about 84% of those bytes. Cloud Logging keeps them for 30 days, and we pay for every byte when it arrives.

Container logs cost about Rp 91M a month. Excluding production container lines below WARNING from the `_Default` sink would save up to about Rp 75M a month. ERROR and WARNING lines would stay, so GCP Error Reporting keeps working. The Coralogix sink is not affected, because it already excludes container logs.

Check this before excluding anything. Eleven busy production services send no logs to Datadog (see the problem statement on [the parent page](README.md#problem-statement)). For those services, Cloud Logging is the only copy. Exclude by container name, not for the whole namespace. Add a service to the list only after you check that its logs are in Datadog.

### 2. Datadog reads log files that `tee` writes, not stdout

Each service's entrypoint pipes its output through `tee` into `/tmp/log/<pod>.json` on the node. The Datadog Agent tails that file. Nightly cron jobs in `bravo-terraform/product/helm-apps/datadog.tf` truncate the files at 19:00 UTC, and weekly jobs delete small ones. Without append mode, `tee` kept its old offset after each truncation, and the Agent shipped the gap as NUL bytes. That was 89% of our Datadog log bytes. The 19 `tee -a` pull requests stop the padding, but the file setup stays.

Stdout collection is simpler and removes the cause:

1. In each service's `app-deployment` values, remove `"type": "file"` and `"path"` from the `ad.datadoghq.com/<container>.logs` annotation. Keep `source`, `service` and the processing rules. The Agent then reads the container's stdout. This step is safe on its own, because `tee` already prints everything to stdout.
2. In a second deploy, remove the `/tmp/log` hostPath volume, its mount and the init container. The images do not create `/tmp/log`, so the entrypoint's `[ -d "$SERVICE_LOG_DIR" ]` check fails and the service runs without `tee`.
3. Later, change the entrypoint to `exec $SERVICE_EXECUTABLE`, as in the closed bravo-user-iam-service#521. The service then runs as PID 1, receives SIGTERM on shutdown, and reports its real exit code. Leave the variable unquoted in Java repos, because their command includes `$JAVA_OPTS`.
4. When no service uses `/tmp/log`, remove the truncation and delete cron jobs and the Agent's `/tmp/log` mount.

Scale on 20 October: 36 repositories still have a `tee` entrypoint, and 59 production values files still use a `"type": "file"` annotation.

**Risk to fix first.** The Agent values file `product/helm-apps/datadog.yaml` is shared by the `dev` and `prod` workspaces. Commit `13f0b83` ("disable log for nonprod", 12 February 2026) set `logs.enabled: false` and `containerCollectUsingFiles: false` in that shared file. Production logs still arrive, so the production Agent was probably not applied after that commit. I could not confirm this, because my account cannot read the Terraform state. If it is right, the next `atlantis apply -p prod-product-helm-apps` stops all production log collection. Split the values per workspace before anyone applies.

### 3. Non-production has no exclusion filters

Production has three exclusions on its `_Default` sink. Non-production has none. Cloud SQL logs at INFO and below cost about Rp 20M a month there. Production drops the same logs. [bravo-terraform#367](https://github.com/bfi-finance/bravo-terraform/pull/367) adds four exclusions: the same two as production, plus Chaos Mesh and the Envoy Gateway access log below WARNING. It is open and waits for review ([SRE-1823](https://bfifinance.atlassian.net/browse/SRE-1823)).

### 4. Coralogix: what Security has and what it asks for

Coralogix receives the network, edge, identity and audit logs that Security needs. It does not receive application logs. Security's own ticket [DKBFI-881](https://bfifinance.atlassian.net/browse/DKBFI-881) asks to review the exclusion of container and Cloud SQL logs, because it may leave a gap in monitoring.

Sending all container logs to Coralogix would add about 480 GB a day in production, about three times its current input. Before that, agree on what Security needs from applications. Login failures, permission changes and admin actions are a small set. The logging libraries can tag those events, and one sink filter on that tag can send only them to Coralogix.

VPC flow logs and load balancer logs are stored in Cloud Logging and in Coralogix. Together they cost about Rp 15M a month in Cloud Logging. If Security confirms that Coralogix is their copy, the `_Default` sink can exclude them.

### 5. The ingestion metric under-reports before 24 September

The Cloud Monitoring metric `logging.googleapis.com/billing/bytes_ingested` shows 10 to 20 GiB a day of production container logs until 23 September, then about 700 GiB from 25 September. The billing export shows about 650 to 800 GB a day for the whole period. No exclusion, sink or cluster setting changed on those days. Use the billing export (FinOps) for cost, and use the metric only for trends after 25 September.

## Target design

- **Applications write one JSON line per event to stdout.** Lines stay under 16 KB. The shared logging libraries already mask and cap messages.
- **Every environment sends stdout to Cloud Logging** through the GKE logging agent. This is the only copy for SIT and UAT.
- **Production also sends stdout to Datadog.** The Datadog Agent reads container stdout, with no log files and no cron jobs.
- **Production Cloud Logging keeps only WARNING and above** for services that Datadog covers.
- **Coralogix receives security sources.** It gets the organisation sink without application logs, plus a tagged stream of security events from applications when Security asks for it.
- **Each platform has one owner.** SRE owns Datadog and Cloud Logging. Security owns Coralogix.

## Steps

| # | Step | Owner | Saving per month | Ticket or PR |
|---|---|---|---|---|
| 1 | Split the Datadog Agent values per workspace, with log collection on in production | SRE | Prevents an outage of all production logs | New ticket |
| 2 | Merge the non-production exclusion filters | SRE | About Rp 20M for Cloud SQL, plus Chaos Mesh and Envoy | [bravo-terraform#367](https://github.com/bfi-finance/bravo-terraform/pull/367), [SRE-1823](https://bfifinance.atlassian.net/browse/SRE-1823) |
| 3 | Move production services to Datadog stdout collection, one pilot first | SRE + squads | Removes the cause of NUL padding and the cron jobs | New ticket, then one `app-deployment` pull request per service |
| 4 | Exclude production container lines below WARNING from Cloud Logging, for services with confirmed Datadog logs | SRE + squads | Up to about Rp 75M | New ticket |
| 5 | Agree with Security which application events Coralogix needs, then tag them in the libraries | Security + Platform | None. It closes the gap in DKBFI-881. | [DKBFI-881](https://bfifinance.atlassian.net/browse/DKBFI-881) |
| 6 | Decide whether VPC flow and load balancer logs stay in Cloud Logging | Security + SRE | About Rp 15M | New ticket |
| 7 | Record the answer to SRE-1826 on that ticket | Architecture | None | [SRE-1826](https://bfifinance.atlassian.net/browse/SRE-1826) |

## Decisions needed

- **SRE and squads:** do squads still read production logs in Cloud Logging? If not, step 4 can go ahead service by service.
- **Security:** is Coralogix the copy of record for VPC flow and load balancer logs? Which application events do you need?
- **Architecture:** confirm that Coralogix stays as the SIEM until the 2027 renewal, so the logging programme stops treating it as a cost to remove.

## How this was measured

- **Log routing:** Cloud Logging API, `sinks` and `exclusions` on both projects, their folders and the organisation, read on 20 October 2026.
- **Cloud Logging cost:** GCP billing export through FinOps, service "Cloud Logging", by `goog-resource-type`. Production 15 September to 18 October, non-production 12 to 18 October. The tool returns at most 200 rows, ordered by cost. The smallest row included is about Rp 28,000, so missing rows change no total here. The billing data prices about Rp 7,350 per GB.
- **Volumes:** Cloud Monitoring `logging.googleapis.com/byte_count` and `billing/bytes_ingested`. The Coralogix topic uses `pubsub.googleapis.com/topic/byte_cost` on `bfi-host-project`.
- **Duplicates:** a two-minute sample of `prod-ms-branch` and `prod-ms-agent` on 19 October had 1,000 lines, each stored once. On 6 October every line was stored twice.
- **Coralogix use:** Jira tickets in DKBFI (Security) and ITVM-194 (the contract), and `sre/TYK Revamp.md`.
- **Datadog figures:** from [Datadog log cost by service](README.md#datadog-log-cost-by-service-8-october-2026), measured 8 to 16 October. The Datadog tools were not available on 20 October, so those figures were not refreshed.
- **Not checked:** the Coralogix account itself, the live Datadog Agent configuration, and the Terraform state.
