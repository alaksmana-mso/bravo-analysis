# 04. Production footprint

All figures are from the production databases and cluster on **2026-09-28**, read-only. "Root instance" means a process instance with no super process instance, that is, one loan application's top-level process. Child instances started by call activities are counted separately where stated.

## 1. Throughput

| Measure | Conventional (`prod-ms-bpm`) | Sharia (`prod-sharia-bpm-sharia`) |
|---|---:|---:|
| Root process instances started, last 90 days | **399,942** | 86 |
| Root process instances started, last 30 days | **135,745** | 26 |
| All process instances started incl. call-activity children, last 90 days | **1,278,214** | — |
| Busiest day, last 30 days (root / all) | **7,943 / 23,865** (15 Sep) | — |
| Busiest hour, last 14 days (root) | **1,347** | — |
| Typical weekday, root | 5,500–6,100 | — |

So: about 4,400 loan applications a day on average, 8,000 on the busiest day, with the unified generation multiplying each application into several engine process instances.

## 2. By process definition, last 90 days (conventional)

| Process key | Root instances | Still open | Mean duration |
|---|---:|---:|---:|
| `NDF2W` | 253,728 | 100,633 | 54 h |
| `NDF4W` | 61,930 | 17,298 | 99 h |
| `multiAssetSurveyScoring` | 27,611 | 0 | minutes |
| `OPERATION` | 21,999 | 2,395 | 25 h |
| `Unified_Process_Main_Workflow` | 20,092 | 9,079 | 142 h |
| `NDF4W_RO` | 11,713 | 2,592 | 43 h |
| `Unified_Process_Operation_Workflow` | 2,874 | 189 | 20 h |

Sharia, last 90 days: `NDF4W_Sharia` 43, `multiAssetSurveyScoring` 25, `Sharia_NDF4W_Operation_Process` 18.

Instances are **long-lived**: days, not seconds. A loan application waits for a surveyor visit, a customer decision, a branch manager, a document. That shapes the in-flight state below.

## 3. In-flight state (conventional)

| Runtime table | Rows |
|---|---:|
| Process instances, top level and called children (`ACT_RU_EXECUTION`, no parent) | **1,097,108** |
| Executions in total | 2,123,056 |
| **Open user tasks** (`ACT_RU_TASK`) | **1,036,845** |
| Runtime variables (`ACT_RU_VARIABLE`) | **46,469,953** |
| Jobs (`ACT_RU_JOB`) | 3,905, of which 38 timers |
| Open incidents (`ACT_RU_INCIDENT`), all `failedJob` | 4,433 |
| External tasks, event subscriptions | 0, 0 |

Open **top-level** instances by age, from history:

| | Count |
|---|---:|
| Open root instances | **540,824** |
| … started more than 90 days ago | 408,638 |
| … started more than 1 year ago | 59,710 |
| … started more than 2 years ago | 0 |
| Oldest open root instance | 2025-09-01 |

An application-level expiry job closes instances after about a year, which is why nothing is older than that. Most open instances are parked on a user task. The largest single wait state is the NDF2W "User Survey Task", with **695,734** open tasks, all assigned. The next are the high-risk survey task (81,819), two "system trigger follow-up" wait states (50,486 and 30,031), and the low-risk survey task (26,066).

By definition, open instances (top level and children): `NDF2W` 770,674; `NDF4W` 209,426; `OPERATION` 21,754; `Unified_Process_Main_Workflow` 19,019; unified survey and assignment children 12,000–16,000 each; `NDF4W_RO` 12,185.

**This is the number that shapes a Temporal plan.** Half a million top-level applications, 1.1 million engine instances, and a million user tasks are open at any moment, and the tail runs to a year. A migration cannot wait for the engine to drain. There is no tool that moves a Camunda process instance into a Temporal workflow execution, so the realistic shapes are: route new applications to Temporal and let Camunda run off over a year, or reconstruct in-flight state into new workflow executions at a chosen point. We want Temporal's view on both.

## 4. History configuration and database size

| Setting | Value |
|---|---|
| History level | `full` (level 3) |
| `historyTimeToLive` | 90 days, set on every process definition |
| History cleanup | batch window 00:00–01:00 daily |
| `historyCleanupJobLogTimeToLive` | 365 days |
| Camunda telemetry flag in `ACT_GE_PROPERTY` | enabled |

Database size, conventional: **914 GB** in total. Engine tables account for roughly **490 GB** of that:

| Table | Total size (with indexes) | Estimated rows |
|---|---:|---:|
| `ACT_HI_ACTINST` | 203 GB | 127 M |
| `ACT_HI_DETAIL` | 105 GB | 121 M |
| `ACT_HI_VARINST` | 85 GB | 81 M |
| `ACT_HI_JOB_LOG` | 49 GB | 56 M |
| `ACT_RU_VARIABLE` | 31 GB | 46 M |
| `ACT_GE_BYTEARRAY` | 16 GB | 22 M |
| `ACT_RU_METER_LOG` | 3.9 GB | 8.9 M |

The rest is application data (for example the credit-bureau response store at 181 GB and amortisation tables at 53 GB).

Sharia database: 2.9 GB in total.

So the engine writes roughly **1.4 M activity-instance history rows a day** at full history level, and keeps 90 days of them. For a Temporal assessment this is the input for three things: the Actions a month we would consume, the event-history size of a long-running workflow with 96 possible wait points, and the retention and export we need to keep a 90-day audit trail outside Temporal's own history retention.

**Our rough Actions estimate, for Temporal to replace with a proper one.** About 1.28 M process instances start per 90 days including children, and about 1.4 M activity-instance history rows are written a day across all element types. If roughly a third of those rows are service tasks, that is about 450 k activity executions a day, each counting as an activity start plus a completion, before signals, timers and child-workflow starts. That lands in the range of **5 to 15 million Actions a month**. It is a rough figure and we would rather Temporal derive it from the element counts in [02](02-process-model-inventory.md) and the volumes above.

## 5. Definitions and deployments

| | Conventional | Sharia |
|---|---:|---:|
| Distinct process keys deployed | 90 | 42 |
| Process definition versions | 3,750 | 161 |
| Decision definitions | 3 | — |
| Engine deployments since first deployment (May 2022) | 203 | — |
| Deployments in the last 90 days | 7 (371 new versions, all 53 keys) | — |

Because auto-deployment redeploys every changed file, each release creates a new version of most definitions. All 56 call activities bind `latest`, so a child process change takes effect for parents already in flight the next time they reach that call activity.

## 6. Compute

| | Conventional | Sharia |
|---|---|---|
| Replicas | 2 | 4 |
| Application container | request 4 CPU / 8 GiB, limit 8 CPU / 16 GiB | same chart |
| JVM | `-XX:+UseContainerSupport -XX:MaxRAMPercentage=80.0`, Datadog Java agent, profiling off | same |
| Sidecars | Cloud SQL proxy, Istio | same |
| Job executor | Spring Boot starter defaults (no `job-execution` overrides in configuration) | same |
| Engine cache | `cacheCapacity` 1000 | same |

## 7. Operations pattern

- Failed jobs become incidents; operations staff retry from Cockpit (151 retries by 6 users in the last 30 days) or through our own retry endpoint.
- Stuck applications are moved with process instance modification through our own "reprocess" endpoints.
- A daily scheduled restart of the conventional deployment exists.
- Monitoring is through Datadog APM on the HTTP, JPA and outbound-call layer. There are no engine-level metrics exported today (job executor, incidents, instance counts).
