# SECURITY FINDING — Unauthenticated Camunda RCE exposure on prod BPM

**Severity: Critical.** Found incidentally on 2026-09-09 while querying the production `ms-bpm` PostgreSQL database for the workflow analysis. This is not a workflow-design issue; it is a live security exposure and is written up separately so it can be routed to whoever owns Bravo security. If this was an authorized penetration test, treat this as confirmation the finding is real and the artifacts are still in production; if it was not, treat it as an incident.

## What was found

The Camunda engine behind `prod-ms-bpm` (proxy `sqlproxy.prod.bravo.bfi.co.id:15434`, database `postgres`) contains **61 process definitions that are not part of the application**, deployed between **2026-05-23 02:50 and 2026-06-30 13:08 (7 distinct sessions)**. They are text-book Camunda expression-injection remote-code-execution (RCE) probes. Examples, by deployment name and the `camunda:expression` on their single service task:

| Deployment name | What the service-task expression does |
|---|---|
| `prod_rce_bypass` | Builds `java.lang.Runtime` by reflection through string `concat()` (to dodge keyword filters) and runs `Runtime.getRuntime().exec('hostname')`, capturing stdout into a process variable |
| `cmd_sh_c` | Same reflection chain, runs `sh -c uname` |
| `cmd_id`, `cmd_uname`, `direct_ls`, `direct_cat`, `direct_ps`, `ifs_tab` | OS command probes (`id`, `uname`, `ls`, `cat`, `ps`) |
| `kw_getRuntime`, `kw_newInstance`, `kw_invoke`, `fn_getMethod`, `meta_forName`, `getclass_getmethod` | Reflection-primitive probes mapping which JUEL/SpEL building blocks the engine allows |
| `x1_1779505439` … `x1_1782824884` (≈9) | Full RCE payloads (reflection → `Runtime.exec` → `readAllBytes()` of stdout) |

All 61 are **active** (`suspension_state_ = 1`), i.e. still deployable/startable today.

## Proof the RCE executed (not just deployed)

Deploying a definition does not run its expression; **starting an instance does**. History shows exactly one probe instance was ever started:

- Process `x1_1781161729`, started **2026-06-11 07:08:51**, completed 14 ms later.
- Its captured result variable `o` (the `camunda:resultVariable` on the exec task) holds: `prod-ms-bpm-75765895b4-dxbq4` — the Kubernetes **pod hostname**.

That is command output from inside the production pod persisted into the Camunda history tables. Code execution on the production JVM is confirmed, not theoretical. The other 60 definitions were deployed but not instantiated (a tester confirming the deploy path is open, or automated fuzzing that stopped at deploy).

## How it was possible

`SecurityConfig.java` (`src/main/java/com/bfi/bravo/config/SecurityConfig.java:65`) makes the whole Camunda surface public:

```java
.requestMatchers("/camunda/**", "/camunda**").permitAll()
```

The service ships `camunda-bpm-spring-boot-starter-rest` and `-webapp` (`pom.xml`). With the REST API reachable and unauthenticated, anyone who can reach `/camunda` or the engine-rest deployment endpoint can `POST` a BPMN file and then start it — no login. `camunda.bpm.authorization.enabled=true` in `application.yaml` governs *in-engine* authorization for logged-in users; it does not help when the HTTP path itself is `permitAll` and the caller never authenticates. Datadog APM confirms the Camunda web paths are reachable in prod (`GET /bpm/camunda/app/cockpit/...`, `GET /camunda/app/**` returning 200).

There is no attribution: `act_hi_op_log` has no entries for these deployments and the process `start_user_id_` is null, consistent with unauthenticated calls. The deploys did **not** come through the app's Git-managed BPMN (those are the `NDF*`, `Unified_*`, `Process_*` keys); they were pushed directly to the engine.

## Blast radius

- **Confirmed:** arbitrary OS command execution as the `ms-bpm` process user inside the prod pod.
- **Reachable from that position:** the `SPRING_DATASOURCE_*` credentials in the pod environment (full read/write to this database — application, loan, customer PII, Camunda history), the `dd-java-agent`, the GKE pod's service-account token and metadata endpoint, and any internal service the pod can call (`gateway.bfi.co.id`, scoring/approval engines).
- **Scope of injected artifacts:** BPM production only. The **Sharia** BPM engine (`:15455`) was checked explicitly and is **clean** — zero non-application definitions, zero probe instances.

## Immediate actions (for the security/platform owner)

1. **Close the hole:** remove `/camunda/**` from `permitAll` (require authentication, or do not expose the Camunda REST/webapp externally at all — restrict to cluster-internal or an authenticated admin ingress). This is the single fix that stops re-exploitation.
2. **Rotate everything reachable from the pod:** the `ms-bpm` database credentials (these proxy logins included if they live in the pod), the GKE workload service-account, and any internal API keys/secrets mounted into the deployment.
3. **Purge the injected definitions** after preserving evidence: the 61 non-application `act_re_procdef` rows and their deployments/bytearrays, and the `x1_1781161729` history instance. Suspend first if immediate deletion is not possible.
4. **Scope the intrusion:** the window is 2026-05-23 to 2026-06-30. Review egress logs, database audit, and GKE audit logs in and after that window for lateral movement or data access originating from the `ms-bpm` pod. One captured hostname proves execution; it does not prove the actor stopped there.
5. **Confirm authorization:** determine whether this was a sanctioned pentest. If yes, the artifacts should still be removed from prod and the auth gap closed. If no, open an incident.

## Evidence queries (read-only, already run)

```sql
-- the 61 injected definitions
SELECT pd.key_, pd.version_, d.name_, d.deploy_time_
FROM act_re_procdef pd JOIN act_re_deployment d ON d.id_ = pd.deployment_id_
WHERE pd.key_ !~ '^(NDF|OPERATION|Process_|Unified_|Ro_|Sharia_|UNSECURED|unsecured|preApproval|multiAsset)'
ORDER BY d.deploy_time_;

-- the one confirmed execution and its captured command output
SELECT p.proc_def_key_, p.start_time_, v.name_, v.text_
FROM act_hi_procinst p JOIN act_hi_varinst v ON v.proc_inst_id_ = p.id_
WHERE p.proc_def_key_ = 'x1_1781161729';

-- the payload of any probe (read the BPMN bytes)
SELECT d.name_, convert_from(b.bytes_, 'UTF8')
FROM act_re_deployment d JOIN act_ge_bytearray b ON b.deployment_id_ = d.id_
WHERE d.name_ = 'prod_rce_bypass';
```

I did not modify anything; every database session was set `default_transaction_read_only = on`.
