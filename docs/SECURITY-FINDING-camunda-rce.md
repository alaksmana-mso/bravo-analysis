# SECURITY FINDING — Camunda RCE executed on prod BPM via an authenticated deploy path

**Severity: Critical.** Found incidentally on 2026-09-09 while querying the production `ms-bpm` PostgreSQL database for the workflow analysis.

> ## Correction, 2026-09-10 — the Bravo team is right, and this document's mechanism claim is withdrawn
>
> This finding was published as **"Unauthenticated Camunda RCE exposure"**. The Bravo team responded that a caller must be registered in Keycloak. **Checked against the code: they are correct, and the original headline was wrong.**
>
> | | Original claim | Verified 2026-09-10 |
> |---|---|---|
> | Deploy vector | `/camunda/**` is `permitAll()`, so anyone reachable can `POST` a BPMN and start it | **The deploy vector is the REST API at `/engine-rest/`, which does *not* match `/camunda/**`.** It falls through to `.requestMatchers("/**").authenticated()`, so it **requires a credential** — a Keycloak JWT (`Authorization: Bearer …`) or the shared `api-secret` header |
> | `permitAll()` on `/camunda/**` | The hole | Real, but it exposes the **Cockpit webapp**, which has its own login. Camunda CE Cockpit has **no deployment upload**, so it is not the exploit path. Hardening, not the breach |
> | Null `start_user_id_` ⇒ unauthenticated | Asserted | **Withdrawn — the inference has no force.** The `api-secret` path sets a Spring `RunAsUserToken`, not a Camunda identity, so `start_user_id_` is null for *ordinary application traffic too* |
>
> **What is unchanged is all of the empirical evidence.** 61 injected process definitions still exist and are still active; one of them ran and captured the production pod hostname. Code execution on the prod JVM is confirmed by data, not inferred from configuration.
>
> **And the corrected finding is worse in one specific way.** If the deploy path required a credential, then **whoever deployed those definitions held a valid BFI credential** — a Keycloak account or the shared internal service secret. This is no longer "the door was open"; it is either an insider, an authorized tester, or a **leaked secret**. See [§ How it was possible](#how-it-was-possible-corrected) and the revised actions, where credential rotation moves to number one.
>
> *Why the original was wrong:* the Spring config makes `/camunda/**` public and the injected artifacts were real, so "public Camunda ⇒ unauthenticated deploy" looked like one step. It is two, and the second one does not hold — `/engine-rest` is a different path. The commented-out `OldSecurityConfig.java`, a genuine Keycloak adapter chain, is probably also why both sides had different mental models of what protects this service.

**This is not a workflow-design issue; it is a live security exposure**, written up separately so it can be routed to whoever owns Bravo security. If this was an authorized penetration test, treat it as confirmation that the finding is real and the artifacts are **still in production**; if it was not, treat it as an incident. Either way the credential question in the correction above has to be answered, because an authorized test would not explain a shared secret that grants production code execution.

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

## How it was possible (corrected)

`SecurityConfig.java:65` does make the Camunda **webapp** surface public:

```java
.requestMatchers("/camunda/**", "/camunda**").permitAll()
.requestMatchers("/**").authenticated()
```

But the deploy endpoint is `POST /engine-rest/deployment/create`, and `/engine-rest/**` matches neither `permitAll` pattern. It falls to `authenticated()`. The REST base path is confirmed twice in the repo: `pom.xml:350` (*"access the api at http://localhost:8080/engine-rest/"*) and `.github/knowledge/references/camunda-activities.md:232`. `server.servlet.context-path` is `/`, so there is no prefix that would pull it under `/camunda`.

**So a credential was required. There are exactly two that satisfy it**, both via `InternalAuthenticationFilter`:

| Credential | Header | What it becomes |
|---|---|---|
| A Keycloak user token | `Authorization: Bearer …` | Whatever the JWT grants, via `KeycloakJWTService` |
| **The shared internal service secret** | `api-secret: <INTERNAL_SERVICE_KEY>` | A `RunAsUserToken` with `ROLE_SYSTEM_SERVICE` |

Note what `InternalAuthenticationFilter` does *not* do: it never rejects. It reads the headers, populates the security context if they are valid, and calls `filterChain.doFilter(...)` unconditionally. It is a *populating* filter, not an *enforcing* one — all enforcement is the `authorizeHttpRequests()` block. That is why `permitAll()` on `/camunda/**` really is public, and why everything else really does require a credential.

**Two aggravating facts about the secret path.**

1. **`INTERNAL_SERVICE_KEY` is a single static shared value**, compared with `.equals()` (`application.yaml:1489`, `setting.service.internal.key`). It is not per-caller, not rotated per request, and not scoped — any holder gets `ROLE_SYSTEM_SERVICE`.
2. **Once past Spring, the caller has full engine rights.** `camunda.bpm.authorization.enabled: true` governs in-engine authorization *for an authenticated Camunda identity*. No `ProcessEngineAuthenticationFilter` is registered on the REST API (verified: no such bean anywhere in `src/main/java`), so the REST caller establishes **no Camunda identity** — and Camunda skips authorization checks when no identity is set. So the engine's own authorization layer is inert on this path.

**Therefore `INTERNAL_SERVICE_KEY` is an RCE-equivalent credential**: whoever holds it can deploy and start a process definition, and a process definition can contain an arbitrary expression. That is the actual finding, and it is a design issue independent of this intrusion.

**A plausible source for the credential, connecting this to a separate finding.** `bravo-e2e-test/cypress.config.js` carries committed plaintext credentials — including an agreement `apiSecret`, an LMS username and password with no expiry, a Jira token and a Zephyr key — in a repository with **46 contributors and two squad checkouts**, exposed through 600 commits of git history ([bravo-testing.md recommendation 14](bravo-testing.md#recommended-actions)). Whether that specific secret is the one that opened this path is **not established**, but it is the first place to look, and it makes the two findings one problem rather than two.

**Attribution is still absent, and this part is unchanged.** `act_hi_op_log` has no entries for these deployments and `start_user_id_` is null. As the correction above states, that no longer supports "unauthenticated" — but it does mean **the engine recorded nothing about who did this**, so attribution has to come from HTTP access logs, not from the database.

**What remains genuinely unverified: external reachability.** Whether `/engine-rest/**` is exposed at the ingress or is cluster-internal only cannot be determined from this repository — it holds no Ingress manifest. Datadog confirms the *webapp* paths are reachable in prod (`GET /bpm/camunda/app/cockpit/…`, `GET /camunda/app/**` → 200); it does not establish the same for `/engine-rest`. **This materially changes the exposure** — an internet-reachable `/engine-rest` plus a leaked shared secret is a very different picture from a cluster-internal one — and it is the first thing the platform owner should check.

## Blast radius

- **Confirmed:** arbitrary OS command execution as the `ms-bpm` process user inside the prod pod. **Precondition, corrected 2026-09-10:** possession of a Keycloak token or the shared `api-secret` — not open to the anonymous internet, and not therefore less serious, because the secret is static, shared and grants full engine rights.
- **Reachable from that position:** the `SPRING_DATASOURCE_*` credentials in the pod environment (full read/write to this database — application, loan, customer PII, Camunda history), the `dd-java-agent`, the GKE pod's service-account token and metadata endpoint, and any internal service the pod can call (`gateway.bfi.co.id`, scoring/approval engines).
- **Scope of injected artifacts:** BPM production only. The **Sharia** BPM engine (`:15455`) was checked explicitly and is **clean** — zero non-application definitions, zero probe instances.

## Immediate actions (for the security/platform owner) — reprioritised 2026-09-10

The order changed with the mechanism. Closing `permitAll` was previously item 1 as "the single fix that stops re-exploitation"; **it is not, because it was not the way in.** Credential rotation is.

1. **Rotate `INTERNAL_SERVICE_KEY` — and treat it as an RCE-equivalent secret from now on.** A single static shared value that grants `ROLE_SYSTEM_SERVICE`, and thereby the whole Camunda REST API on a path where the engine's own authorization is inert. Rotate it, then move to per-caller credentials with scoped authorities so that "can call an internal endpoint" stops implying "can deploy and run arbitrary code in production".
2. **Rotate the credentials committed in `bravo-e2e-test/cypress.config.js`** and assume full-history exposure — 46 contributors, 600 commits, plaintext values with no expiry. Independently justified, and the most plausible source for the credential used here.
3. **Determine which credential was used, which is now answerable.** The engine recorded nothing, but the deploys were HTTP requests. Pull ingress / load-balancer / APM access logs for `POST /engine-rest/deployment/create` (and `/process-definition/*/start`) across **2026-05-23 02:50 → 2026-06-30 13:08, 7 distinct sessions**, and read the source IPs and whether the caller presented `api-secret` or `Authorization`. That distinguishes an insider, an authorized tester and a leaked secret — three very different incidents.
4. **Establish whether `/engine-rest/**` is reachable from outside the cluster.** Not determinable from this repository. If it is internet-facing, restrict it to cluster-internal or an authenticated admin ingress immediately; if it is already internal-only, the exposure is materially smaller and the intrusion is much more likely to be internal.
5. **Register a `ProcessEngineAuthenticationFilter` on the REST API**, so a REST caller establishes a Camunda identity and `camunda.bpm.authorization.enabled: true` — already switched on, and currently doing nothing on this path — actually applies.
6. **Purge the injected definitions** after preserving evidence: the 61 non-application `act_re_procdef` rows with their deployments and bytearrays, and the `x1_1781161729` history instance. Suspend first if immediate deletion is not possible. All 61 are still `suspension_state_ = 1`.
7. **Rotate everything else reachable from the pod**, on the assumption that code execution means the pod's environment is compromised: the `ms-bpm` database credentials, the GKE workload service-account, and any internal API keys mounted into the deployment.
8. **Scope the intrusion.** The window is 2026-05-23 to 2026-06-30. Review egress, database audit and GKE audit logs in and after that window for lateral movement or data access originating from the `ms-bpm` pod. One captured hostname proves execution; it does not prove the actor stopped there.
9. **Close the Cockpit exposure anyway (hardening, not the breach).** Remove `/camunda/**` from `permitAll` or restrict it to an authenticated admin ingress. Camunda's own login and `authorization.enabled: true` stand behind it and CE Cockpit cannot deploy, so this is not how the definitions arrived — but an unauthenticated login page on a production engine is still needless attack surface.
10. **Confirm authorization.** Determine whether this was a sanctioned penetration test. Note the timing: an **LOS penetration test was active in September 2026** (`ADI-1312` firewall access for the Sibertahan VPN, Done 2026-09-09; `BLCS-4799` sample-data support, Done 2026-09-07) — that is *three months after* this window closed, so it does not explain these artifacts, but the same programme may have earlier engagements worth checking. If it was sanctioned, the artifacts should still be removed and the credential still rotated. If not, open an incident.

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

-- the 7 deployment sessions, to correlate against HTTP access logs (action 3)
SELECT date_trunc('minute', d.deploy_time_) AS session_minute,
       count(*) AS definitions, min(d.name_) AS sample_name
FROM act_re_procdef pd JOIN act_re_deployment d ON d.id_ = pd.deployment_id_
WHERE pd.key_ !~ '^(NDF|OPERATION|Process_|Unified_|Ro_|Sharia_|UNSECURED|unsecured|preApproval|multiAsset)'
GROUP BY 1 ORDER BY 1;

-- the payload of any probe (read the BPMN bytes)
SELECT d.name_, convert_from(b.bytes_, 'UTF8')
FROM act_re_deployment d JOIN act_ge_bytearray b ON b.deployment_id_ = d.id_
WHERE d.name_ = 'prod_rce_bypass';
```

I did not modify anything; every database session was set `default_transaction_read_only = on`.
