# confins-prod-ms-lms-ar-be — what the "blank log lines" really are

Written 14 September 2026. Evidence is Datadog production: logs, unsampled trace metrics,
usage metrics and the Bravo source under `squads/`. The CONFINS cluster itself
(`core-system-prod`) could not be read: `gcloud` on the analysis machine needs an
interactive login, and the CONFINS Helm charts are not in the four repositories SRE shared.
Every claim below is marked with where it came from.

This file corrects [logging-cost.md](logging-cost.md) §4.1 and item 6,
[squads-guide.md](squads-guide.md), [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §3,
[README.md](README.md) and [coverage.md](coverage.md). Each of those now carries a marker
pointing here.

---

## 1. What the pack said, and how it was found

The logging pack ranked production services by Datadog log entry count over two days,
then clustered each top service by its `message` field. For this service every entry
clustered as an empty string. The pack called them "genuinely blank log lines", costed them
as a metadata envelope of 500–1,000 bytes each, said they carried no information, put the
count at 9.25 million a week, and assigned the fix to "a CONFINS owner".

Nobody opened the attributes on one of those entries. That was the mistake.

## 2. The lines are not blank

The vendor's C# logger (application name `AdIns.AR.API.X`, source `csharp`) writes one JSON
object per line with no `message` or `msg` key. Datadog's csharp pipeline therefore leaves
the message column empty. The information is in custom attributes:

| Attribute | What it holds |
|---|---|
| `action` | `Request` or `Response`, or `Request-HttpHelper` / `Response-HttpHelper` for outbound calls |
| `req_method`, `req_host`, `req_path` | The HTTP call |
| `log_id` | One id shared by a request and its response |
| `payload` | **The full HTTP body** |
| `level`, `time`, `app` | Vendor's own level, timestamp and app name |

Every inbound call produces two entries, request and response, each with the body attached.
Payload sizes over 24 hours to 14 September, from `analyze_datadog_logs`:

| Action | Entries | Payload bytes | Average payload |
|---|---:|---:|---:|
| Response | 99,176 | 259.6 MB | 2.6 KB |
| Request | 99,034 | 6.3 MB | 63 B |
| Response-HttpHelper (outbound to foundation-be) | 6,373 | 10.4 MB | 1.6 KB |
| Request-HttpHelper | 6,373 | 1.0 MB | 158 B |

The largest bodies are amortisation schedules from `GetListAmrtzByAgrmntCodeX`, 13 KB on
average and 25.6 KB at most, which is why a handful of entries a day arrive as unparsed text
fragments: the 16 KB container-runtime split cuts them.

**What is in the bodies.** Agreement numbers, customer numbers (`CustNo`), office codes,
outstanding principal and interest, instalment amounts, overdue buckets, product and scheme
codes, prepaid balances. No names or national ids were seen in the endpoints sampled, but
`GetAgrmntByAgrmntNo` returns the whole agreement object. This is a body-logging finding of
the same class as §5a of logging-cost.md, and a data-handling question in its own right.

**The error entries** (237 in the hour sampled) are all the same shape: a 406
"Agreement Not Found" response from `CalculatePrepaidSettlement`, logged at the vendor's
`Error` level.

## 3. Ninety per cent of the volume is re-ingestion, not traffic

### 3.1 Real traffic

Datadog's trace metrics are computed before sampling, so they count every request.
`sum:trace.aspnet_core.request.hits{service:prod-ms-lms-ar-be}` by day:

| Day (UTC) | 7 Sep | 8 Sep | 9 Sep | 10 Sep | 11 Sep | 12 Sep | 13 Sep | 14 Sep |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Requests | 367,761 | 341,710 | 300,561 | 372,356 | 335,081 | 228,265 | 122,777 | 333,683 |

A flat 300–370k requests a day on weekdays. Two log entries per request would be
600–750k lines a day written by the application.

### 3.2 What Datadog indexed

| Day (UTC) | Indexed entries |
|---|---:|
| 7 Sep | 7,499 (retention edge) |
| **8 Sep** | **2,196,031** |
| 9 Sep | 201,240 |
| **10 Sep** | **2,446,990** |
| 11 Sep | 194,456 |
| 12 Sep | 131,766 |
| 13 Sep | 78,622 |
| 14 Sep (partial) | 197,808 |

Steady state is about 200k a day, a third of what the application writes, because the
Agent only tails the files it sees. The two big days are each **one hour**:

| Burst hour | Entries in the hour | Real requests in the hour (trace hits) | Amplification |
|---|---:|---:|---:|
| 8 Sep 09:00–10:00 UTC (16:00 WIB) | 2,169,813 | ~50,000 | ~40× |
| 10 Sep 04:00–05:00 UTC (11:00 WIB) | 2,262,084 | ~50,000 | ~45× |

### 3.3 What the burst hours contain

The application stamps every entry with its own `time`. In the 10 September burst hour:

| Application timestamp on the line | Entries |
|---|---:|
| August (12–30 Aug) | 2,172,013 |
| 10 Sep, earlier that day | 2 |
| Within the hour | 90,069 |

Ninety-six per cent of the lines ingested in that hour were written in August. Grouping the
same hour by the pod that emitted them and the **file** the Agent read them from:

| Node | Pod | Files tailed | Entries | Application time range of the files |
|---|---|---:|---:|---|
| `…-5fb158cb-zs2g` | `prod-ms-lms-ar-be-7587fdcdb-s56wk` (new) | **16** | **2,172,710** | 12 Aug – 30 Aug |
| `…-0e9bdb50-2627` | `…-6dskg` (new) | 4 | 20,315 | within the hour |
| `…-0e9bdb50-2627` | `…-r6xd4` (new) | 4 | 17,914 | within the hour |
| `…-0e9bdb50-2627` | `…-w5tj6` (new) | 4 | 16,586 | within the hour |
| `…-0e9bdb50-2627` | `…-f2952` (new) | 4 | 13,537 | within the hour |
| `…-5fb158cb-v684` | `…-vpfk6` | 1 | 19,265 | within the hour |

The sixteen files read by pod `s56wk` are named after **dead pods from three older
ReplicaSets** (`b64df665f`, `69984dc877`, `7587fdcdb`): `prod-ms-lms-ar-be-b64df665f-64gk4.json`
(652,730 entries, 16–21 Aug), `…-rql5j.json` (601,305, 21–26 Aug), `…-7587fdcdb-8v4q7.json`
(458,616, 26–29 Aug) and thirteen more. The four new pods on node `2627` each tailed the
same four files, their own and each other's, so every live line on that node was indexed
four times.

The 8 September burst is the same event on the same node (`zs2g`): two new pods, `2v4xd` and
`ftj8h`, read the same August files again. Those files had already been indexed once on
8 September and were indexed again on 10 September.

### 3.4 The mechanism

From the tags on every entry (`dirname:/var/log`, `filename:<pod-name>.json`), the
application writes its log to `/var/log/<pod-name>.json`, and the Datadog Agent collects it
with a `type: file` log configuration rather than from container stdout. Files from dead pods
are still present on the node a month later, and a new pod can see them, so the path is
shared across pods: a hostPath or an equivalent node-level mount. The Agent's file config
uses a wildcard (`prod-ms-lms-ar-be-*.json` or similar). When a rollout schedules a new pod,
the Agent creates a new tailer for that pod's configuration and reads **every file matching
the wildcard on that node from the beginning**, attributing all of it to the new pod.

Two consequences follow, both visible in the data:

- Every rollout re-ingests every historical file left on the nodes. The August files have
  been ingested at least three times (8 Sep, 10 Sep, and originally).
- Pods co-located on a node index each other's live lines, once per pod.

This is not vendor application behaviour. It is how the log collection was wired.

### 3.5 Duplicates across the week

Requests only, 7–14 September: 2,455,294 request entries against 1,887,631 distinct
`log_id` values. The window does not include August, so the true duplication is higher.

## 4. Blast radius: the CONFINS family

Seven days to 14 September, indexed entries, distinct pods and distinct file names:

| Service | Entries | Pods | Files | Shape |
|---|---:|---:|---:|---|
| `confins-prod-ms-lms-ar-be` | 5,449,533 | 103 | 114 | this file |
| `confins-prod-ms-ce-camunda-external-task-client` | 4,340,442 | 3 | 3 | 4.08M of it on 12 Sep alone; polls `ExternalTask/FetchAndLock` and logs both bodies each time |
| `confins-prod-ms-foundation-be` | 2,003,457 | 81 | 130 | 1.55M on 8 Sep, 444k on 9 Sep, then under 300 a day |
| `confins-prod-ms-lms-amendment-be` | 381,778 | 2 | 2 | 809k ingested on 12 Sep |
| `confins-prod-ms-ce-batch-worker-ar` | 234,496 | 33 | **253** | files far outnumber pods |
| `…-batch-worker-armnt` / `-amendment` / `-payment` / `-fou` / `-asset` / `-govreg` / `-cashbank` | 1,190 – 58,818 each | 21–34 | 87–230 | same |

Files outnumbering pods is the signature. Datadog's own usage metric
(`datadog.estimated_usage.logs.ingested_events`) for the family, 7–14 September:

| Service | Ingested events, 8 days | Of which the burst days |
|---|---:|---:|
| `confins-prod-ms-lms-ar-be` | 19.3M | 17.7M (7, 8, 10 Sep) |
| `confins-prod-ms-ce-camunda-external-task-client` | 8.65M | 8.1M (12 Sep) |
| `confins-prod-ms-foundation-be` | 7.0M | 6.1M (7, 8 Sep) |
| `confins-prod-ms-lms-amendment-be` | 0.81M | 0.81M (12 Sep) |
| `ce-batch-worker-*` (nine) | ~0.7M | — |
| **Family** | **~36.5M** | **~32.7M, about 90%** |

For scale: all of production indexed 33.4M log entries in the same seven days. The
CONFINS family indexed about 12.2M of them. **Roughly a third of indexed production log
events last week were CONFINS re-ingestion.**

Ingested bytes for `lms-ar-be` alone were 69.5 GB in eight days, 64 GB of it on the three
burst days.

## 5. Cost, corrected

- **Cloud Logging: nil.** The application writes files, not stdout, so nothing reaches
  Cloud Logging. `core-system-prod` does not appear in the Cloud Logging line items in
  logging-cost.md §2 at all. The "Rp 5–15M a month" saving in item 6 of that document did not
  exist.
- **Datadog log ingestion:** 64 GB a week of re-ingestion at $0.10/GB is about $28 a
  month. Small.
- **Datadog log events:** this is where it bites. The contract (§1a of logging-cost.md)
  commits 150M indexed events a month across the 3-day and 7-day lines and the estate used
  240M in the last 30 days. CONFINS re-ingestion at ~12M indexed a week is ~52M a month —
  most of the overage, at $1.59–1.91 per million.
- **Index headroom:** a 2.2M-entry hour is the kind of burst that exhausts a daily index
  quota and drops every other service's logs for the rest of the day. No quota event was
  found in the last 14 days, so it has not happened yet.

## 6. Who owns what

| Question | Answer | Source |
|---|---|---|
| Where does it run | project `core-system-prod`, cluster `prod-core-system-cluster`, namespace `prod`, deployment `prod-ms-lms-ar-be`, 3–7 pods, `v3.1.12` | log tags |
| Who builds the image | BFI's own registry: `asia-southeast2-docker.pkg.dev/bfi-devsecops/ms-lms-ar-be/ms-lms-ar-be` | `image_name` tag |
| Vendor | AdIns (app name `AdIns.AR.API.X`, runtime .NET / ASP.NET Core) | `app` attribute, span `language:dotnet` |
| Datadog catalog owner | none | `search_datadog_entities` |
| Who generates the traffic | `prod-ms-bravo-core-proxy` (user-agent `Java/17.0.12`), called by `prod-ms-agreement` for `GET /v1/agreement/{no}` and `GET /v1/agreements/{no}/fees`; upstream of that, `prod-ms-partnership`, `prod-ms-collection-consumer`, `prod-ms-repeat-order`, RabbitMQ consumers | span aggregation, `bravo-core-proxy-service` `ApiPath.java` and `NewCoreAPIClient.java`, `bravo-agreement-service` `LoanAgreementV2ServiceImpl.java:1398` |
| Who owns the fix | **SRE.** The defect is in how the Agent collects the file, not in the vendor's code | §3.4 |

The pack's "needs a CONFINS owner" was the wrong framing. The log *content* is the vendor's
and the Contract Collateral squad's business. The log *volume* is a collection defect that
SRE can fix without touching either.

## 7. What SRE should do

1. **Stop tailing a shared file path.** Either switch the CONFINS containers to log to
   stdout and remove the `type: file` annotation, so the Agent collects container logs the
   standard way, or keep files but point the annotation at the pod's own file using the
   autodiscovery variable `%%kube_pod_name%%` in the path, so a pod can never see another
   pod's file. Verify the variable is supported by the Agent version on that cluster before
   relying on it.
2. **Purge the stale files** from `/var/log` on the `pool-01` nodes of
   `prod-core-system-cluster`. The August files are still there and will be re-read at the
   next rollout of any CONFINS service.
3. **Add an index exclusion filter** on the production index for
   `service:confins-* @action:(Request OR Response) status:info` until 1 and 2 are done.
   Keep `status:error`. This stops the indexing cost. It does not stop ingestion cost;
   only 1 and 2 do that.
4. **Give the entries a message.** A string builder processor on the csharp pipeline setting
   `message` from `action`, `req_method` and `req_path` makes these lines readable and would
   have prevented the misreading in the pack.
5. **Ask AdIns whether request/response body logging has a switch**, and set it to
   failure-only. That is the data-handling half, and it is independent of 1–4.
6. **Fix the dual service name** while in the manifest, per
   [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §3: every entry carries both
   `service:confins-prod-ms-lms-ar-be` and `service:prod-ms-lms-ar-be`.

## 8. How to reproduce

Log analytics, DDSQL, filter `service:confins-prod-ms-lms-ar-be`, with `@payload`, `@action`,
`@req_path`, `@log_id`, `@time`, `pod_name`, `filename`, `kube_node` declared as columns:

```sql
-- Bodies per endpoint
SELECT "@req_path", "@action", count(*), avg(length("@payload")), max(length("@payload"))
FROM logs GROUP BY "@req_path", "@action" ORDER BY count(*) DESC;

-- A burst hour: who read which file, and how old the lines were
SELECT kube_node, pod_name, filename, count(*), min("@time"), max("@time")
FROM logs GROUP BY kube_node, pod_name, filename ORDER BY count(*) DESC;

-- Files versus pods across the family (filter service:confins-*)
SELECT service, count(*), count(distinct pod_name), count(distinct filename)
FROM logs GROUP BY service ORDER BY count(*) DESC;
```

Metrics explorer, to compare against real traffic:

```
sum:trace.aspnet_core.request.hits{service:prod-ms-lms-ar-be}.as_count()
sum:datadog.estimated_usage.logs.ingested_events{service:confins-*} by {service}.as_count()
```

## 9. Two lessons for the pack

- An empty `message` column is a pipeline artefact until the attributes have been opened.
- An indexed log count is not a traffic count. Check it against a trace hit metric and
  against the application's own timestamp before calling it volume.
