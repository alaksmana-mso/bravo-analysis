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
> **All of the empirical evidence is unchanged.** 61 injected process definitions still exist, and they are still active. One of them ran and captured the production pod hostname. So code execution on the production JVM is confirmed by data. It is not inferred from configuration.
>
> **And the corrected finding is worse in one specific way.** The deploy path required a credential. So **whoever deployed those definitions held a valid BFI credential** — a Keycloak account, or the shared internal service secret.
>
> This is no longer "the door was open". It is an insider, an authorised tester, or a **leaked secret**. See [§ How it was possible](#how-it-was-possible-corrected) and the revised actions, where credential rotation moves to number one.
>
> *Why the original was wrong.* The Spring config makes `/camunda/**` public, and the injected artifacts were real. So "public Camunda means unauthenticated deploy" looked like a single step. It is two steps, and the second one does not hold: `/engine-rest` is a different path.
>
> There is probably a second reason both sides held different mental models of what protects this service — the commented-out `OldSecurityConfig.java`, which is a genuine Keycloak adapter chain.

**This is not a workflow-design issue. It is a live security exposure.** It is written up separately so it can be routed to whoever owns Bravo security.

If this was an authorised penetration test, treat it as confirmation that the finding is real and the artifacts are **still in production**. If it was not, treat it as an incident.

Either way, the credential question in the correction above has to be answered. An authorised test would not explain a shared secret that grants production code execution.

## What was found

The Camunda engine behind `prod-ms-bpm` contains **61 process definitions that are not part of the application**. (We reached it through the proxy `sqlproxy.prod.bravo.bfi.co.id:15434`, database `postgres`.) They were deployed between **2026-05-23 02:50 and 2026-06-30 13:08, across 7 distinct sessions**.

They are textbook Camunda expression-injection probes for remote code execution (RCE). Here are examples, by deployment name and by the `camunda:expression` on their single service task:

| Deployment name | What the service-task expression does |
|---|---|
| `prod_rce_bypass` | Builds `java.lang.Runtime` by reflection through string `concat()` (to dodge keyword filters) and runs `Runtime.getRuntime().exec('hostname')`, capturing stdout into a process variable |
| `cmd_sh_c` | Same reflection chain, runs `sh -c uname` |
| `cmd_id`, `cmd_uname`, `direct_ls`, `direct_cat`, `direct_ps`, `ifs_tab` | OS command probes (`id`, `uname`, `ls`, `cat`, `ps`) |
| `kw_getRuntime`, `kw_newInstance`, `kw_invoke`, `fn_getMethod`, `meta_forName`, `getclass_getmethod` | Reflection-primitive probes mapping which JUEL/SpEL building blocks the engine allows |
| `x1_1779505439` … `x1_1782824884` (≈9) | Full RCE payloads (reflection → `Runtime.exec` → `readAllBytes()` of stdout) |

All 61 are **active** (`suspension_state_ = 1`), i.e. still deployable/startable today.

## Proof the RCE executed (not just deployed)

Deploying a definition does not run its expression. **Starting an instance does.** History shows that exactly one probe instance was ever started:

- Process `x1_1781161729`, started **2026-06-11 07:08:51**, completed 14 ms later.
- Its captured result variable `o` (the `camunda:resultVariable` on the exec task) holds: `prod-ms-bpm-75765895b4-dxbq4` — the Kubernetes **pod hostname**.

That is command output from inside the production pod, written into the Camunda history tables. So code execution on the production JVM is confirmed, not theoretical. The other 60 definitions were deployed but never instantiated. That fits either a tester confirming the deploy path is open, or automated fuzzing that stopped at deploy.

## How it was possible (corrected)

`SecurityConfig.java:65` does make the Camunda **webapp** surface public:

```java
.requestMatchers("/camunda/**", "/camunda**").permitAll()
.requestMatchers("/**").authenticated()
```

But the deploy endpoint is `POST /engine-rest/deployment/create`, and `/engine-rest/**` matches neither `permitAll` pattern. It falls through to `authenticated()`.

The repository confirms the REST base path twice: `pom.xml:350`, which says *"access the api at http://localhost:8080/engine-rest/"*, and `.github/knowledge/references/camunda-activities.md:232`. And `server.servlet.context-path` is `/`, so no prefix pulls it under `/camunda`.

**So a credential was required. There are exactly two that satisfy it**, both via `InternalAuthenticationFilter`:

| Credential | Header | What it becomes |
|---|---|---|
| A Keycloak user token | `Authorization: Bearer …` | Whatever the JWT grants, via `KeycloakJWTService` |
| **The shared internal service secret** | `api-secret: <INTERNAL_SERVICE_KEY>` | A `RunAsUserToken` with `ROLE_SYSTEM_SERVICE` |

Note what `InternalAuthenticationFilter` does *not* do. It never rejects anything. It reads the headers, populates the security context if they are valid, and then calls `filterChain.doFilter(...)` unconditionally.

So it is a *populating* filter, not an *enforcing* one. All enforcement happens in the `authorizeHttpRequests()` block. That is why `permitAll()` on `/camunda/**` really is public, and why everything else really does require a credential.

**Two aggravating facts about the secret path.**

1. **`INTERNAL_SERVICE_KEY` is a single static shared value.** It is compared with `.equals()` — see `application.yaml:1489`, `setting.service.internal.key`. It is not per caller. It is not rotated per request. And it is not scoped. Any holder gets `ROLE_SYSTEM_SERVICE`.
2. **Once past Spring, the caller has full engine rights.** `camunda.bpm.authorization.enabled: true` governs in-engine authorization, but only *for an authenticated Camunda identity*. No `ProcessEngineAuthenticationFilter` is registered on the REST API — we verified there is no such bean anywhere in `src/main/java`. So the REST caller establishes **no Camunda identity**. And Camunda skips authorization checks when no identity is set. So the engine's own authorization layer is inert on this path.

**So `INTERNAL_SERVICE_KEY` is an RCE-equivalent credential.** Whoever holds it can deploy and start a process definition. And a process definition can contain an arbitrary expression. That is the actual finding. It is a design issue, and it stands independently of this intrusion.

**There is a plausible source for the credential, and it connects this to a separate finding.** `bravo-e2e-test/cypress.config.js` carries committed plaintext credentials. Those include an agreement `apiSecret`, an LMS username and password with no expiry, a Jira token and a Zephyr key. The repository has **46 contributors and two squad checkouts**, and the values are exposed through 600 commits of git history ([bravo-testing.md recommendation 14](bravo-testing.md#recommended-actions)).

Whether one of those secrets is the one that opened this path is **not established**. But it is the first place to look. And it makes the two findings one problem rather than two.

**Attribution is still absent, and that part is unchanged.** `act_hi_op_log` has no entries for these deployments, and `start_user_id_` is null. As the correction above says, that no longer supports "unauthenticated". But it does mean **the engine recorded nothing about who did this**. So attribution has to come from HTTP access logs, not from the database.

**One thing remains genuinely unverified: external reachability.** We cannot determine from this repository whether `/engine-rest/**` is exposed at the ingress or is cluster-internal only. The repository holds no Ingress manifest.

Datadog confirms the *webapp* paths are reachable in production — `GET /bpm/camunda/app/cockpit/…` and `GET /camunda/app/**` both return 200. It does not establish the same for `/engine-rest`.

**This materially changes the exposure.** An internet-reachable `/engine-rest` plus a leaked shared secret is a very different picture from a cluster-internal one. So it is the first thing the platform owner should check.

## Blast radius

- **Confirmed:** arbitrary OS command execution, as the `ms-bpm` process user, inside the production pod. **Precondition, corrected 2026-09-10:** the attacker needed a Keycloak token or the shared `api-secret`. So it was not open to the anonymous internet. That does not make it less serious. The secret is static, it is shared, and it grants full engine rights.
- **Reachable from that position:** the `SPRING_DATASOURCE_*` credentials in the pod environment, which give full read and write access to this database — application data, loan data, customer personal data, and Camunda history. Also the `dd-java-agent`. Also the GKE pod's service-account token and metadata endpoint. And any internal service the pod can call, such as `gateway.bfi.co.id` and the scoring and approval engines.
- **Scope of injected artifacts:** BPM production only. The **Sharia** BPM engine (`:15455`) was checked explicitly and is **clean** — zero non-application definitions, zero probe instances.

## Immediate actions (for the security/platform owner) — reprioritised 2026-09-10

The order changed when the mechanism changed. Closing `permitAll` used to be item 1, described as "the single fix that stops re-exploitation". **It is not that, because it was not the way in.** Credential rotation is.

1. **Rotate `INTERNAL_SERVICE_KEY`, and treat it as an RCE-equivalent secret from now on.** It is a single static shared value. It grants `ROLE_SYSTEM_SERVICE`, and through that the whole Camunda REST API, on a path where the engine's own authorization is inert.

    Rotate it. Then move to per-caller credentials with scoped authorities, so that "can call an internal endpoint" stops meaning "can deploy and run arbitrary code in production".
2. **Rotate the credentials committed in `bravo-e2e-test/cypress.config.js`.** Assume the full history is exposed: 46 contributors, 600 commits, and plaintext values with no expiry. This is justified on its own merits. It is also the most plausible source for the credential used here.
3. **Work out which credential was used. This is now answerable.** The engine recorded nothing, but the deploys were HTTP requests.

    Pull the ingress, load-balancer and APM access logs for `POST /engine-rest/deployment/create`, and for `/process-definition/*/start`, across **2026-05-23 02:50 to 2026-06-30 13:08, over 7 distinct sessions**. Read the source IPs, and read whether the caller presented `api-secret` or `Authorization`.

    That distinguishes an insider from an authorised tester from a leaked secret. Those are three very different incidents.
4. **Establish whether `/engine-rest/**` is reachable from outside the cluster.** This repository cannot tell us. If it is internet-facing, restrict it immediately to cluster-internal, or to an authenticated admin ingress. If it is already internal-only, the exposure is much smaller, and the intrusion is much more likely to be internal.
5. **Register a `ProcessEngineAuthenticationFilter` on the REST API.** Then a REST caller establishes a Camunda identity, and `camunda.bpm.authorization.enabled: true` actually applies. That setting is already switched on, and today it does nothing on this path.
6. **Purge the injected definitions, after preserving the evidence.** That evidence is the 61 non-application `act_re_procdef` rows with their deployments and bytearrays, plus the `x1_1781161729` history instance. If you cannot delete them immediately, suspend them first. All 61 are still `suspension_state_ = 1`.
7. **Rotate everything else reachable from the pod**, on the assumption that code execution means the pod's environment is compromised: the `ms-bpm` database credentials, the GKE workload service-account, and any internal API keys mounted into the deployment.
8. **Scope the intrusion.** The window is 2026-05-23 to 2026-06-30. Review the egress, database audit and GKE audit logs, both inside and after that window, for lateral movement or data access originating from the `ms-bpm` pod. One captured hostname proves execution. It does not prove the actor stopped there.
9. **Close the Cockpit exposure anyway. This is hardening, not the breach.** Remove `/camunda/**` from `permitAll`, or restrict it to an authenticated admin ingress. Camunda's own login and `authorization.enabled: true` stand behind it, and CE Cockpit cannot deploy, so this is not how the definitions arrived. But an unauthenticated login page on a production engine is still needless attack surface.
10. **Confirm authorisation.** Work out whether this was a sanctioned penetration test.

    Note the timing. An **LOS penetration test was active in September 2026** — `ADI-1312` gave firewall access for the Sibertahan VPN, Done 2026-09-09, and `BLCS-4799` supported it with sample data, Done 2026-09-07. That is *three months after* this window closed, so it does not explain these artifacts. But the same programme may have earlier engagements worth checking.

    If it was sanctioned, still remove the artifacts and still rotate the credential. If it was not, open an incident.

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

We modified nothing. Every database session was set `default_transaction_read_only = on`.
