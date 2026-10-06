> **Status:** version 1, 2 October 2026. Written from code (150+ repositories, Helm values, Terraform), Confluence (30+ pages) and Datadog production data. Author: Andre Laksmana. Secret values are never reproduced here, only their names and locations.

# 1. Summary

BFI does not have one place where a person's access starts, changes and ends. Access is granted and removed by hand, by at least seven teams, in at least nine stores. The leaver path is the weakest part. There is no access review anywhere except a written GCP policy. Keycloak is the authentication layer, but it is four deployments, nine realms, and most of the realm configuration is not in git.

**Six facts that matter most**

1. **Four Keycloak deployments, about 15 environment instances, nine realms.** In production: one modern operator-managed cluster (Keycloak 26.7, 3 replicas, `auth.bfi.co.id`, realm `google-workspace`) and three single-pod instances on **Keycloak 21.1.1** (released April 2023, unsupported): `sso.bfi.co.id` (realm `IAM_BFI`), `microservices.prod.bravo.bfi.co.id` (realms `bravo`, `bpm`, `spvcockpit`, `lms-gateway`) and a Sharia copy. The "Keycloak deprecated December 2025" deadline has passed. The legacy `bravo` realm still served about 197,000 token and userinfo calls in the last 7 days. Only two realms (`bpm`, `spvcockpit`) have configuration in git, and the import scripts probably never run.
2. **HCIS is the only real source of truth for employees, and the link from HCIS to access is unreliable and one-directional.** Resignations arrive D+2 over RabbitMQ. The user-iam sync creates Keycloak users with `Enabled=true` and a **predictable temporary password** built from the name and employee number. It never disables anyone. In CNV, about 212,000 HCIS messages a day are discarded as "record not found", so a real revoke failure would be invisible.
3. **Roles live in nine stores and are edited by hand.** 104 roles, 311 permissions, 2,112 job-title rows and 1,424 direct grants in user-iam (SQL in prod, CSV baked into the image for Sharia and BAU, so a role change there is a deploy); a JSON document per person written by curl with a shared secret (LORA); per-app tables (CNV, OTRS dashboard, digital-web-api, FinOps, Pimcore, Strapi); Keycloak groups (`bpm`, `IAM_BFI`); a 116-revision Confluence table for surveyors. No approval step exists outside CNV. user-iam's internal grant API needs only the shared api-secret and a self-asserted actor header.
4. **Offboarding is scattered and partly wrong.** A leaver must be removed from four Keycloaks, Active Directory, Google Workspace and each app table. No code disables a Keycloak user on resignation. The BPM nightly job treats a past resign date as a new employee and **adds** roles. LORA has no leaver path at all. Keycloak realm exports show refresh tokens never revoked, 30-day offline sessions, brute-force protection off, no password policy.
5. **No audit and no review.** Keycloak ships no logs or traces to Datadog. user-iam never calls the audit-trail service, which has no role-change event type. No access certification exists. One shared secret (`prod-internal-service-key-secret`) is mounted into 52 production deployments and is referenced 214 times.
6. **Immediate security items.** The production diff-inspector chart sets `AUTH_MODE=development`, so every request passes its auth check on the public `/diff-inspector` path. BPM gives **every user token** the same `ROLE_SYSTEM_SERVICE` authority that service callers get, has method security disabled, and ships a default `GWS_MOCK_USERS` mapping that prod does not override. Committed secrets: Salesforce RSA keys (pbf-live), a Keycloak client secret in nine files (`platform-dev`), Apigee OAuth keys in application yaml, a Terraform state file with tokens, seven plaintext values in the e2e cypress config, a UAT LORA api-secret on a Confluence page.

**Recommendation in one line.** Fix eight prerequisites first (one realm, HCIS sync in production, CNV discard, Keycloak audit to Datadog, an API in front of every role store, per-service secrets, the BPM authority bug, the diff-inspector flag). Then adopt **midPoint** as the identity governance core, self-hosted on GKE, with n8n only as glue. Do not try to make n8n the IGA. Re-evaluate a SaaS IGA only if the team cannot staff two engineers. Details in sections 7 and 8.

# 2. What this assessment is based on

| Source | What was read |
| --- | --- |
| Code | 150+ repositories under `squads/`, `lora-workspace/`, `sre/` (app-deployment and bfi-app-deployment Helm values, bravo-terraform, Keycloak charts and realm exports). Five scans: Keycloak and IdP inventory, Bravo lifecycle, LORA permissions, SRE and infrastructure identity, long-tail applications. |
| Confluence | 30+ pages on Keycloak, SSO, user management, HCIS sync, GCP access policy, 2022 to October 2026. Listed in section 11. |
| Datadog (us5) | 7 days of production spans for every call to a `realms/` URL; Kubernetes inventory of Keycloak statefulsets, pods, ingresses and image tags; CNV and employee-service logs. |
| Jira | 2026 tickets mentioning Keycloak, GWS SSO or user access. |

**Not read, so not verified:** Google Workspace Admin (groups, suspensions), Active Directory and ADManagerPlus, HCIS itself, Keycloak admin consoles for the `google-workspace`, `bravo`, `IAM_BFI` and `qa` realms (no exports in git), GitHub organisation settings, Temporal Cloud, Datadog and Atlassian user lists, the live GKE cluster.

# 3. The identity landscape today

## 3.1 Identity stores

| Store | What it holds | Owner | Fed from | Fed to |
| --- | --- | --- | --- | --- |
| **HCIS** (MSSQL; vendor name does not appear in code) | Employee master: NIK, name, job title, work location, status, resign date | Human Capital | HR process | RabbitMQ `human-capital` exchange on `mq.bfi.co.id`; Airflow DAG `hcis_employee_full_sync` (daily 03:00 WIB, in four `bravo-airflow` copies; which copy runs in prod is unknown) |
| **Google Workspace** | Corporate email identity, MFA | Enterprise System | Manual (assumed; not verified) | Keycloak `google-workspace` realm by SAML brokering (configuration not in git); GCP IAM through Google Groups; FinOps dashboard; LORA login |
| **Active Directory** (`dc.bfi.co.id`) + ADManagerPlus / ADSelfServicePlus | Windows, VPN, e-self | Enterprise System | Manual | Keycloak `bpm` and `spvcockpit` realms by **plain LDAP** (`ldap://`, port 389, read-only, full sync weekly). `IAM_BFI` has an LDAP URL set but no federation config in git |
| **Keycloak `auth.bfi.co.id`**, realm `google-workspace` | Brokered GWS users, created on first login | SRE / Platform | Google Workspace | 30+ production services (3.2) |
| **Keycloak `sso.bfi.co.id`**, realm `IAM_BFI` | BAU users: OTRS, Operation Excellence, MySIS, treasury, ARES, AMS, PCMS, Argo CD | SRE | `prod-ms-bau-user-iam` writes attributes (14,460 PUT/week); nightly `keycloak-user-mapper` cron maps job-title codes to groups (source not in repo) | BAU applications |
| **Keycloak `microservices.prod.bravo.bfi.co.id`**, realms `bravo`, `bpm`, `spvcockpit`, `lms-gateway` | Legacy Bravo users with `iam:*` attributes; BPM realm roles and groups; AD-federated cockpit users | SRE | `prod-ms-user-iam` creates users and writes attributes (14,460 PUT, 9 POST per week); BPM admin APIs create and delete users; repeat-order resets agent passwords | repeat-order, lms-ops, collateral, inventory, agent-marketing, agency, BPM, edoc, lms-gateway |
| **Keycloak Sharia** (`prod-sharia-keycloak`) | Realm `Bravo` for Sharia services | SRE | user-iam sharia (CSV mode) | Sharia services |
| **bravo-employee-service** (Postgres `employee`) | Copy of the HCIS record | Internal Service | MQ listener (active in prod) and Airflow | user-iam, CNV, scheduling, collection, BPM, agency, LORA BPP, every GWS-realm service (job title lookup) |
| **bravo-user-iam-service** | `domain`, `role`, `permission`, `role_has_permission`, `employee_has_role`, `job_title_has_role`, `web_menu` tables (prod); the same as CSV files for Sharia and BAU | Internal Service | platform-fe admin pages (needs `platform.iam.*`); internal gRPC behind api-secret; pull requests for CSV | Every Bravo service that calls `CheckPermission`; also pushes attributes and OIDC mappers into Keycloak |
| **LORA LTS `people`** (ArangoDB) | One JSON document per NIK with `partnership`, `ssf`, `corporate` role blocks and branch lists | LORA Core | `POST /mgmt/people` behind a shared api-secret; BPP CSV upload (partnership only, uploader unknown) | lora-task-service permissions |
| **CNV `user_access`** (Postgres) | Branch access, roles, TOTP MFA, checker-maker approvals, deactivation requests | Internal Service | CNV UI, then IAM revoke on approval | CNV only |
| **bravo-auth-service** | Agents, marketing tools users, customers, supplier platform: phone, OTP, per-app roles, refresh tokens | Internal Service | OTP registration; agent-marketing | Agent Tools app, customer BFF, supplier platform |
| Per-app tables | OTRS dashboard users by NIK; digital-web-api (three bcrypt user tables); FinOps dashboard; Pimcore admin; Strapi admin; call and conversation gateway `application` tables (plaintext secrets); Salesforce pbf-live (167 permission sets, 90 roles) | Each squad | Each app's own UI or API | That app only |
| Confins | Agents and marketing staff | Agency | Manual | agent-service, employee-service sync for LORA users |

## 3.2 Keycloak inventory (production, from Datadog and git, 2 October 2026)

| Host | Cluster / namespace | Chart | Image | Pods | Realms | Calls in last 7 days (token, userinfo, certs) | Admin API callers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `auth.bfi.co.id` | bfi-project-prod / prod, `keycloak` | Keycloak Operator CR (`bfi-app-deployment/auth`) | 26.7.x | 3 | `google-workspace` | ~1,040,000 from 30+ services (repeat-order 603k, user-iam 105k, bpm 78k, lms-gateway 77k, otrs-ui 48k, payment 33k, agency 17k, cnv 17k, lora-task 3k) | none seen |
| `sso.bfi.co.id` | bfi-project-prod / prod, `prod-keycloak` | codecentric 16.0.6 (`bfi-app-deployment/keycloak`) | **21.1.1** + Cloud SQL proxy 1.28.1, Postgres 14 | 1 | `IAM_BFI` | ~120 | `prod-ms-bau-user-iam`: 27,093 GET, 14,460 PUT, 9 POST users; nightly mapper cron |
| `microservices.prod.bravo.bfi.co.id` (+ `-private`) | prod-bravo-cluster / prod, `prod-keycloak` | codecentric 16.0.6 (`app-deployment/keycloak`) | **21.1.1** + Cloud SQL proxy 1.28.1 | 1, HPA disabled | `bravo`, `bpm`, `spvcockpit`, `lms-gateway`, `master` | ~197,000 (repeat-order 189k, lms-ops 5.8k, user-iam 1.2k, collateral, agent-marketing, inventory, agreement) | `prod-ms-user-iam`: 27,106 GET, 14,460 PUT, 9 POST users, 248 PUT clients; `prod-ms-bpm`: 149 DELETE sessions, 94 GET users, 21 GET groups; a RabbitMQ consumer: 71 PUT users, 8 reset-password |
| Sharia | prod-bravo-cluster / prod-sharia, `prod-sharia-keycloak` | same chart | **21.1.1** + Cloud SQL proxy | 1 | `Bravo` | 0 seen | none seen |
| `sso.nonprod.bravo.bfi.co.id` | non-production | Keycloak Operator CR (`app-deployment/sso`) | 26.7.3 | 3 | `google-workspace`, `qa` | not in this Datadog org | `impersonation` and `token-exchange` enabled |
| `sso.prod.bravo.bfi.co.id` | no chart in git serves this host | | | | | | referenced only by the diff-inspector prod values |

Notes.

- The same 14,460 PUT-user calls a week appear on both `bravo` and `IAM_BFI`. This is the user-iam "Keycloak sync" writing employee attributes into two legacy realms. It becomes redundant once those realms are gone.
- Realm configuration in git: only `bpm` and `spvcockpit` exports under `app-deployment/keycloak/realms/`, with `identityProviders: []`. The import script is mounted at a JBoss startup path, but the container command is overridden to `kc.sh start`, and prod sets `KEYCLOAK_IMPORT` while the script reads `KEYCLOAK_IMPORT_BPM`. So the exports are documentation, not the running state. The `google-workspace`, `bravo`, `IAM_BFI` and `qa` realms, including the Google SAML broker and all clients, exist only in the Keycloak databases.
- The Confluence consolidation page (August 2025) counted 9 instances. Git shows 4 charts across about 15 environment instances. Keycloak itself emits **no logs and no traces** to Datadog; the Terraform Datadog agent chart has `logs.enabled: false`. Login and admin events for the realms that matter are only in Keycloak's database, and only the `bpm` realm has admin events on.
- Known config defects: `setLDAPConnection.sh` writes the `bpm` LDAP settings into the `spvcockpit` realm; assistance prod points its `bpm` realm variable at `auth.bfi.co.id`; rule-engine prod lists two different issuer hosts for the same realm; SPV cockpit falls back to realm `master` if its variable is unset.
- Realm sprawl is still growing: a new realm decision in September 2026 (RI-118, Risk Innovation), GitLab SSO planned (RI-104), realm `qa` in SIT, `IAM_BFI_DEV/TEST/UAT` in non-prod.

## 3.3 Who authenticates where

| Population | Identity provider | Notes |
| --- | --- | --- |
| Head office and branch employees on Bravo | Keycloak `google-workspace` for migrated apps; Keycloak `bravo` for repeat-order, lms-ops, SPV cockpit, RMS, AQM, DMS data admin (prod), LMS password login (`lms-ui` client) | Several front ends keep a dual-login or feature-flag fallback to the `bravo` realm (LMS FE DMS-5743, e-line UI, platform-fe); inventory-service and BPM accept both JWKS |
| Surveyors, CRE, underwriting, branch ops (LOS) | Keycloak `bpm` realm (AD-federated) and GWS realm clients `los-*` | BPM admin APIs create users with a default password from a secret and assign realm roles; nightly job syncs roles from job title |
| BAU employees (OTRS, Operation Excellence, MySIS, treasury, ARES, AMS, PCMS) | Keycloak `IAM_BFI` on `sso.bfi.co.id` | Also "Keycloak BAU (SSO)" in the August 2025 incident; Argo CD and Grafana use GitHub org login, Argo CD also `IAM_BFI` |
| LORA back office (VD, admin, credit chain, SSF, corporate) | Keycloak `google-workspace`, then LTS issues its own ES256 cookie | Only `preferred_username` (NIK) is read; no Keycloak roles; SIT uses realm `qa`; dev/SIT/UAT allow remapping any Keycloak user to any LTS user id |
| ARE, SPV, BM field staff (Square, SPV Cockpit) | Keycloak `google-workspace` (verified in spans) with password fallback on `bravo` or `spvcockpit` | Duplicate-user SOP: delete the user by hand at `auth.bfi.co.id`; mobile apps use the password grant (ROPC) |
| Agents, sub-agents (Agent Tools, onboarding FE) | bravo-auth-service OTP, own RS512 JWT; repeat-order also manages agent users in Keycloak `bravo` with a **predictable reset password** (`Bfi` + NIK + join year + `!`) | Not GWS |
| Customers | bravo-auth-service OTP; customer-BFF ECDSA request tokens; digital-web-api; gold-service HMAC JWT; LORA session guard | Out of IGA scope; no deactivate endpoint found in auth-service |
| Partners, insurers, banks | HMAC JWT, API keys, SNAP-BI RSA, ES256 partner JWT, Apigee OAuth | Out of IGA scope except key rotation |
| Engineers on GCP and GKE | IAP member lists are per-user in Terraform; GKE RBAC binds Google Groups but the cluster setting that resolves Google Groups is not set; no `container.*` IAM roles for humans in code; external contractor identities (fsoft) and a personal Gmail appear in RBAC and bucket ACLs | Policy page (July 2025) describes group-based access and quarterly review; the code does not match it |
| Engineers on GitHub, Argo CD, Grafana | GitHub org `bfi-finance`; two teams in Terraform; no SSO enforcement in code; GitHub Actions use a long-lived GCP service-account key rotated weekly, not Workload Identity Federation | |
| Engineers on databases | Jira tickets to DOE (DOE-640, DOE-669); MSSQL via a PAM (DKBFI-264/265) | Manual |
| Services to services | Static `api-secret` headers compared with plain equality. Bravo: `prod-internal-service-key-secret` in **52 production deployments, 214 references**, plus about 20 per-service secrets. LORA: one `<env>-lora-internal-service-key-secret` for every link | See F7 |

# 4. How access is granted and removed today

## 4.1 Bravo employee (joiner, mover, leaver)

1. HR creates the employee in HCIS.
2. HCIS publishes to RabbitMQ; `HCEmployeeListener` in bravo-employee-service upserts the `employee` table and republishes to `x.employee.data-acknowledgement-fo.work`. The listener is active in prod (`AIRFLOW_SYNC_ENABLED` is not set there). A daily Airflow DAG also writes the same table directly and POSTs `/employees/sync`. The April 2026 proposal records lost messages, D+2 resign delay and no single source of truth; the May 2026 TRD designed 15-minute and 5-minute DAGs, but the code in the repositories is a daily job. Which runs in prod is unknown.
3. user-iam consumes the fan-out, creates the Keycloak user if missing (username = NIK, `Enabled=true`, temporary password derived from name and NIK), and writes `iam:*` attributes into realms `bravo` and `IAM_BFI`. Users with `iam:manual_update_at` are skipped. The user's `emp_status` is stored as an attribute and claim but never enforced by user-iam.
4. Roles: an engineer uses the platform-fe IAM pages (prod, SQL) or opens a pull request to the CSV files (Sharia, BAU) and `webmenu/data.json`. There is no approval. Services can also grant roles through the internal gRPC API with only the shared api-secret and a self-asserted `x-internal-actor` header.
5. CNV is the exception: checker-maker tables (November 2025) and a deactivation request flow (February 2026) that revokes `cnv.*` IAM roles and terminates sessions on approval.
6. Leaver: CNV listens on the fan-out and, if `dt_resign` is today or earlier, deactivates the user and deletes CNV roles only. In the last 24 hours CNV logged **212,064** "Failed to update user access metadata" errors, all `record not found` (employee numbers in the 700xxxx range with no CNV access). The handler discards the message. Any other failure class is buried.
7. BPM runs a nightly job that removes the job title's Keycloak roles when `resignDate` is today or later. A record with a past resign date falls through to `processNewEmployee`, which **adds** roles. No code disables or deletes a Keycloak user on resignation in any realm. Google Workspace suspension on resignation is assumed to be manual; not verified.
8. Realm settings in the `bpm` and `spvcockpit` exports: `revokeRefreshToken: false`, offline session idle 30 days, `bruteForceProtected: false`, no password policy.

## 4.2 LORA user

1. The employee must exist in Confins and be synced to agent-service and employee-service.
2. An engineer adds the NIK and email to the application deployment repo (a pull request).
3. Someone runs `POST /mgmt/people` on lora-task-service with a JSON body (branches, role, supervisor) and the environment's shared api-secret. Partnership users can also be uploaded as a CSV to BPP, which maps "LORA Role ID" to role, menu and tasks from a static `role_employee_v2.json` (23 roles); who uploads it in prod is unknown. SSF and corporate users have no tool outside local dev.
4. The UAT how-to page prints the UAT api-secret value in plain text (page 2515107911). Rotate it and edit the page.
5. Leaver: re-upload the CSV with `Active=false` (partnership only). The person cache is per pod with a 1-hour TTL, the LTS session cookie is not revoked (an empty "VALIDATE USER HERE" placeholder), there is no delete endpoint, direct assignment does not check `active`, and tasks already assigned stay with the departed user. SSF and corporate users have no leaver path.
6. Branch scoping is enforced only where a worker adds it to a task filter; survey permissions are not branch-scoped; `ssf.branches` and `corporate.branches` are never used in a filter; `/users/query` lets any active user query the whole `people` collection.
7. Committed test material: Keycloak session cookies and test passwords in automation-monorepo fixtures; a Playwright helper writes the password into the test-step title.

## 4.3 Everything else

- OTRS dashboard, digital-web-api, FinOps dashboard, Pimcore, Strapi, call and conversation gateways each keep their own user table with their own admin UI or API. None is tied to HCIS.
- bravo-auth-service (agents, customers, suppliers) has no deactivate endpoint; agency deactivation updates Confins but not the credential.
- pbf-live (Salesforce) has 167 permission sets and 90 roles managed in Salesforce Setup.
- GCP, GitHub, Datadog, Temporal Cloud, Atlassian: group or invitation based, by request to SRE. No automated deprovisioning found in code.

# 5. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **No identity lifecycle owner.** HCIS is the source, but nothing turns a resignation into removal from Keycloak (4 instances), Google Workspace, AD, LORA and app tables. user-iam only ever enables. | Sections 3.1, 4.1, 4.2; Confluence "Unifying SSO" problem 6 (2024), still open | High |
| F2 | **Three of four production Keycloaks are unsupported** (21.1.1, single pod, HPA off, Cloud SQL proxy 1.28). The GWS migration PRD set a hard deadline of December 2025. Legacy `bravo` still serves 197k calls/week. Realm config for the realms that matter is not in git, and the import scripts for the two that are cannot run. | Datadog manifests; `app-deployment/keycloak`; PRD 2471920352 | High |
| F3 | **Leaver signal is late and lossy.** D+2 over MQ; the daily Airflow DAG and the MQ listener both write the same table; CNV discards 212k messages/day; BPM's nightly job adds roles for past resign dates. | Confluence 2361262191, 2420506705; Datadog `prod-ms-cnv`; `EmployeeDataUpdateServiceImpl.java:266-339` | High |
| F4 | **LORA has no leaver path.** No delete, no session revocation, per-pod cache, tasks stay assigned, SSF and corporate users cannot be provisioned or deactivated by any tool. | lora-task-service `store.go`, `cookie_middleware.go`, `assignment.go`; BPP `to_lts_v2.go` | High |
| F5 | **Roles are hand-edited data in nine stores with no approval.** user-iam internal grant API is api-secret only with a self-asserted actor; CSV mode needs a deploy; LORA JSON by curl; Confluence tables; Keycloak groups by cron with source outside git. | Confluence 505709679, 436535330, 2515107911; `employee_has_role_internal.go` | High |
| F6 | **No audit, no review.** Keycloak sends nothing to Datadog; only `bpm` has admin events on. user-iam never calls audit-trail; audit-trail has no role event type and its read APIs need only a valid token. No certification campaign. GCP policy says quarterly review; code shows per-user lists. | Datadog service search; `app_logger.go`; SREW 1197277243; `settings/variables.tf` | Medium |
| F7 | **Service-to-service trust is one static secret.** `prod-internal-service-key-secret` in 52 deployments; one key for all LORA links; plain string compare; employee-service reuses it as its Basic-auth password. Holding it equals `ROLE_SYSTEM_SERVICE` on BPM, the credential in the Camunda RCE. | app-deployment values; `InternalAuthenticationFilter.java`; APPSEC-5 | High |
| F8 | **BPM authorization is effectively off for employees.** Method security disabled, 0 `@PreAuthorize`; every user token gets `ROLE_SYSTEM_SERVICE`; default `GWS_MOCK_USERS` maps one GWS username to a fixed employee's permissions and prod does not override it. bfi-incentive-api similarly gives every token `INCENTIVE_SERVICE`, which guards 127 endpoints, and exposes Camunda with authorization disabled. | `KeycloakJWTServiceImpl.java:142-170`; `application.yaml:3276`; incentive `SecurityContextServiceImpl.java:74` | High |
| F9 | **diff-inspector production auth is bypassed.** `AUTH_MODE=development` makes `authorized()` return true. Its OIDC issuer points at `sso.prod.bravo.bfi.co.id`, a host no chart serves, so OIDC mode would not work either. Public path `/diff-inspector` on `microservices.prod.bravo.bfi.co.id` through `nginx-ingress-protected` (a ClusterIP behind a Google NEG; no load balancer or Cloud Armor policy found in Terraform). | `lora-diff-inspector/values-prod.yaml:98-99,135`; `diff-inspector/auth.ts:94-96` | High until reachability is confirmed |
| F10 | **Predictable passwords.** user-iam temporary password from name and NIK; repeat-order agent reset password `Bfi{NIK}{JoinYear}!`; BPM default user password shared across all created users; no password policy in the realm exports; brute-force protection off. | `keycloak_syncer.go:279-287`; `AgentUtil.java:44-49`; realm exports | High |
| F11 | **Credentials in repositories and pages.** Keycloak client secret `platform-dev` in nine files; Apigee OAuth key and secret in `application-prod.yaml` of agreement, collateral and customer; `errored.tfstate` with tokens committed; seven plaintext values in `bravo-e2e-test/cypress.config.js`; Salesforce RSA keys in pbf-live; shared vendor login in backend-dashboard-otrs; `REACT_APP_API_SECRET` bundled into the notary UI; Keycloak cookies and passwords in automation-monorepo; UAT LORA api-secret on Confluence; local `admin/admin` compose files. | Keycloak, SRE and long-tail scans | High |
| F12 | **AD federation over plain LDAP**, read-only, weekly full sync, in `bpm` and `spvcockpit`. Whether an AD-disabled account is blocked at Keycloak login was not verified. | `bpm-realm-prod.json:2142-2334` | Medium |
| F13 | **Platform access is per-user and partly outside BFI.** IAP and bastion access from individual lists in Terraform; contractor and personal-Gmail identities in GKE RBAC and bucket ACLs; GitHub Actions on a long-lived service-account key; GKE Google Groups for RBAC not enabled; no GitHub SSO enforcement in code. | `settings/variables.tf`, `product/rbac/main.tf`, `k6-reporter/variables.tf`, `github_actions.tf` | Medium |
| F14 | **Non-person identities are ungoverned.** Bank portal logins used by bravo-robot-scrape, SLIK OJK login, Vonage, FINOPS_SERVICE_TOKEN, gateway app secrets stored in plaintext. No inventory, no rotation schedule. | Long-tail scan | Medium |
| F15 | **Authorization gaps in specific apps.** gold-service backoffice checks only token validity; OTRS scheduler endpoints have no auth and its hash middleware is computable from the request; digital-web-api lets any API-key holder create a dashboard user with any role; Spring APIs ending in `permitAll` relying on aspects. | Long-tail scan | Medium to High per app |
| F16 | **Realm and client sprawl continues.** New realm decision September 2026 (RI-118); `qa`, `Bravo`, `IAM_BFI_*`, `master` fallback; dual-realm JWKS in several services; most GWS clients are public (no secret) which is fine for SPAs but also used by backends. | Jira RI-118, RI-104; values files | Medium |

# 6. What good looks like

One system owns the lifecycle. Everything else is a target it provisions to.

1. **Source of truth:** HCIS for employees, Confins for agents, with a written contract and a pull-based sync that reports its own health.
2. **Governance core (IGA):** one identity record per person; a role catalogue with named owners; birthright roles from job title and branch; request and approval for extra roles; automatic removal on mover and leaver; periodic certification; separation-of-duties rules; a full audit of who granted what, when and why.
3. **Authentication:** one Keycloak cluster (26.x, operator-managed, config in git through the operator's realm import), one employee realm brokered to Google Workspace with Google MFA. Non-employee populations (agents, notaries) in their own realm or IdP. Legacy realms retired. Keycloak events shipped to Datadog.
4. **Targets:** Google Workspace (create, suspend), Keycloak (attributes, groups, disable, logout), Bravo IAM (role rows via API, not CSV), LORA LTS (`people` via API with delete and revoke), CNV, bravo-auth-service, GCP Google Groups, GitHub teams, Datadog, Atlassian, Temporal Cloud, database access (PAM), Salesforce. For data-level authorization (branch, product, task ownership) one Zanzibar-style decision service beside Keycloak, fed by the IGA (see 7.5).
5. **Service identities:** one credential per service, rotated; mTLS or workload identity in-cluster; no environment-wide shared key; Workload Identity Federation for GitHub Actions.
6. **Evidence:** IGA audit and Keycloak events in Datadog with monitors (user created outside the IGA, role change by a human, login by a resigned NIK).

# 7. Options

## 7.1 n8n (already running at BFI)

n8n hosts the LORA workflow-stats job and an SRE pod-scaling webhook today, so the platform and the skills exist.

| Can do | Cannot do |
| --- | --- |
| Call HCIS (read-only SQL), Keycloak Admin API, Google Admin SDK, LTS `/mgmt/people`, user-iam, Jira, Google Chat | Keep an identity record and reconcile it against each target (detect drift, orphan accounts) |
| Run a joiner, mover, leaver flow as a scheduled or triggered workflow | Role catalogue, role ownership, birthright rules as data rather than code |
| Send approval requests to Google Chat and wait for a reply | Access certification campaigns with evidence |
| Internal use is allowed under the Sustainable Use License | Separation-of-duties checks |
| | An audit trail an OJK or internal auditor will accept as the system of record |

n8n is a workflow engine. An IGA built on it is a set of JSON workflows that nobody can review, with credentials for every target held in one n8n credential store. It is a good tool for notifications and one-off glue during migration. It is not the governance system. n8n itself also needs an owner, SSO and backups; the Confluence TRD does not say who runs it.

## 7.2 midPoint (Evolveum, open source)

A full IGA: identity lifecycle, roles and organisations, provisioning, reconciliation, access requests, certification, policy rules (SoD), audit. Java and Spring, runs on Kubernetes with PostgreSQL. midPoint 4.10 was released in November 2025; 4.11 is planned for 15 October 2026.

| Fit for BFI | Watch-outs |
| --- | --- |
| Self-hosted on GKE; identity data stays in Indonesia | Needs 1 to 2 engineers who learn midPoint's model (schema, mappings, roles). Plan 3 months to the first production flow |
| HR-driven lifecycle is its core design; the DatabaseTable connector reads HCIS MSSQL read-only, the same access the Airflow design already asks for | The Keycloak connector is community-maintained (Openstandia); a Google Workspace connector exists; both need testing against our versions |
| REST, SCIM and scripted connectors cover LTS `/mgmt/people`, user-iam, CNV, GitHub, Datadog, Atlassian | Our role stores must first expose an API midPoint can call; CSV in git cannot be a target |
| Role catalogue, certification and SoD out of the box; audit is a first-class table | Commercial support from Evolveum is a per-identity subscription; quote needed |
| Same ecosystem as Keycloak (Java, open source, operator on Kubernetes) | The UI is functional, not polished; business approvers may prefer approvals in Google Chat or Jira (n8n can bridge) |

## 7.3 Commercial IGA

| Product | Fit | Why |
| --- | --- | --- |
| SailPoint Identity Security Cloud | Strong product, weak fit | Built for large enterprises with thousands of apps; expensive; SaaS outside Indonesia; connectors for our custom apps still need SCIM or REST work |
| Saviynt | Similar to SailPoint | Same trade-offs |
| Okta Identity Governance | Poor fit | Needs Okta as the IdP; we are Keycloak plus Google Workspace |
| Microsoft Entra ID Governance | Poor fit | Needs Entra ID; BFI is a Google Workspace company. Listed at about USD 7 per user per month on top of a base licence |
| ConductorOne, Lumos, Zluri, AccessOwl | Possible for SaaS apps | Google-Workspace-first, fast to start, good for GitHub, Datadog, Atlassian, Google Groups. Weak for Bravo and LORA custom role stores unless those expose SCIM. SaaS, data outside Indonesia; check OJK and PDP requirements |
| Google Workspace alone | Not an IGA | Directory and groups only; no lifecycle from HR, no certification |

Whatever is chosen, the prerequisite work in section 8 is the same: every role store needs an API, and the realms must be consolidated. That work is most of the effort.

## 7.4 Comparison

| Capability | n8n | midPoint | SaaS IGA (SailPoint class) | SaaS IGA (ConductorOne class) |
| --- | --- | --- | --- | --- |
| Joiner, mover, leaver from HCIS | Build it | Native | Native | Native (HR connector) |
| Identity record and reconciliation | No | Native | Native | Partial |
| Role catalogue, birthright, SoD | No | Native | Native | Partial |
| Access request and approval | Build it (Chat) | Native | Native | Native |
| Certification campaigns | No | Native | Native | Native |
| Keycloak target | Admin API via HTTP node | Connector (community) | Connector or SCIM | SCIM to Keycloak 26.8 (inbound only) |
| Google Workspace target | HTTP node | Connector | Native | Native |
| Custom Bravo and LORA stores | HTTP node | REST or scripted connector | Needs SCIM | Needs SCIM |
| Audit acceptable to auditors | No | Yes | Yes | Yes |
| Data residency | Self-hosted | Self-hosted | Vendor cloud | Vendor cloud |
| Licence | Free for internal use | Free; optional subscription | High | Medium |
| Team effort | Low to start, high to maintain | Medium | Medium plus vendor | Low to medium |

## 7.5 Keycloak authorization and the Ory stack

Two questions came up after the first version: can Keycloak also manage authorization, and how does it compare to the Ory stack.

**Keycloak does authorization at three levels.**

1. **Roles and groups in the token.** Realm roles, client roles, composite roles, group membership and user attributes become claims. The app enforces. This is what BFI uses today: the `bpm` realm roles, the `iam:*` attributes, and Krakend checking only issuer and signature.
2. **Keycloak Authorization Services.** A resource server per client with resources, scopes, policies (role, group, user, client, time, regex, aggregate; JavaScript policies only with the `scripts` feature) and permissions, UMA 2.0 tickets, a decision endpoint and a policy-enforcer library for Java. BFI already uses this in one place: bfi-incentive-api reads its `incentive.report.*` permissions from Keycloak client resources. New in 26.x: an AuthZEN decision API (26.7, experimental), Fine-Grained Admin Permissions v2 (26.2, delegated admin) and Organizations.
3. **Where it stops.** Policies live in the Keycloak database and admin console, not in git unless exported. Evaluation is per client and per request against that database. There is no relationship model, so "surveyor X may see loan Y because X belongs to the branch that owns Y" has to be encoded as attributes. The old adapters are gone; only the policy-enforcer library remains. The user-iam catalogue (8 domains, 104 roles, 311 permissions, 2,112 job-title rows, 1,424 direct grants) would map to client and composite roles, but branch scoping and LORA's task-level `$.person.*` filters do not fit.

**What Keycloak cannot do:** HR-driven lifecycle, approval workflows, certification, separation of duties. Those stay with the IGA. Keycloak is a target of midPoint, not a replacement for it.

**The Ory stack** is four Go services, API-first, with no UI: Kratos (identities, credentials, self-service flows, MFA; JSON-Schema identity model), Hydra (OAuth2 and OIDC provider, no user store of its own), Keto (Zanzibar-style relationship-based authorization, tuples in Postgres, a check API) and Oathkeeper (identity-aware proxy and decision API). The core is Apache 2.0. SAML, SCIM, organizations and multi-tenancy are behind the Ory Enterprise License. Ory Network is the SaaS.

| | Keycloak (what we run) | Ory stack |
| --- | --- | --- |
| Authentication, brokering to Google Workspace | Built in; SAML broker in use; AD LDAP federation in use | Kratos social sign-in with Google OIDC works; SAML needs the Enterprise License; no LDAP federation |
| Admin console, themes, realms | Built in | None; headless, build your own with Ory Elements |
| Coarse roles in tokens | Yes | Hydra can add claims from Kratos traits |
| Fine-grained, data-level authorization (branch, product, task ownership) | Weak: attributes or Authorization Services policies per client | Strong: Keto relationship tuples, millisecond checks, one service for every app |
| Edge enforcement | Krakend gateway today | Oathkeeper, or keep Krakend and call Keto |
| IGA connector (midPoint) | Community connector exists | None; REST or scripted connector needed |
| Migration cost for BFI | Zero | 60+ integrated apps, the realm model, AD federation and SAML redone, mid-way through the GWS migration |
| Team skills | Java, Keycloak, operator | Go services; new |

**Recommendation.** Do not replace Keycloak with Ory. Keep Keycloak for authentication, brokering and coarse roles in the token, with the role catalogue governed by midPoint and pushed into Keycloak client roles. Use Keycloak Authorization Services only where a single app needs simple resource permissions, as incentive-api does. For data-level authorization across apps (branch, product, task) add one Zanzibar-style decision service next to Keycloak. Evaluate OpenFGA and SpiceDB alongside Ory Keto; OpenFGA and SpiceDB have the wider adoption today. midPoint feeds it organisation and branch membership; the apps write resource ownership. Oathkeeper is not needed while Krakend is the gateway.

# 8. Recommendation

## 8.1 Prerequisites, start now (October to December 2026)

These are needed for any IGA and remove the worst risks on their own.

1. **This week.** Set diff-inspector `AUTH_MODE` to `oidc` in prod, fix its issuer host, confirm the `ALLOWED_USERNAMES` list, and confirm whether `nginx-ingress-protected` is internet-facing. Remove `ROLE_SYSTEM_SERVICE` from user tokens in BPM and override `GWS_MOCK_USERS` to empty in prod. Fix the BPM resign-date condition.
2. **Rotate and remove F11 credentials.** `platform-dev` client secret, Apigee keys, cypress values, pbf-live RSA keys, OTRS vendor login, the UAT LORA api-secret on Confluence, automation-monorepo cookies and passwords; delete `errored.tfstate` from git and purge history.
3. **One HCIS path in production.** Decide between the MQ listener and the Airflow DAG, turn the other off, add the 5-minute resign DAG from the May 2026 TRD, and add a Datadog monitor on DAG failure and on "resigned NIK still enabled in Keycloak".
4. **Stop discarding in CNV.** Treat `record not found` as expected at debug level; alert on any other failure of `UpdateMetadataConsumer`.
5. **One realm.** Finish the GWS migration for repeat-order, lms-ops, collateral, inventory, agent-marketing, SPV cockpit, RMS, AQM, DMS data admin, LMS password login. Then retire the `bravo`, `IAM_BFI` and Sharia Keycloak 21.1.1 instances. Freeze new realms (RI-118) and new clients outside `google-workspace` unless the architecture board approves. Put the `google-workspace` realm definition in git through the operator's realm import.
6. **Keycloak audit to Datadog.** Enable user and admin events on `google-workspace`, ship the logs, add three monitors: user created outside the IGA, role or group change by a human, login by a NIK whose HCIS status is resigned. Enable brute-force protection and a password policy while passwords still exist.
7. **An API in front of every role store.** user-iam: an authenticated grant endpoint with a real actor and an audit-trail event; retire CSV mode for Sharia and BAU. LORA LTS: DELETE, session revocation on deactivation, reassignment of open tasks on leaver, and a provisioning tool for SSF and corporate users. bravo-auth-service: a deactivate endpoint. CNV already has one.
8. **Service identities.** One credential per service, rotated; Istio mTLS or workload identity for in-cluster calls; Workload Identity Federation for GitHub Actions; remove predictable password generation in user-iam, repeat-order and BPM (use required-actions and the GWS login instead).

## 8.2 Adopt midPoint as the governance core (from January 2027)

Why midPoint over the others: it is the only option that is a full IGA, keeps identity data in Indonesia, costs nothing to license, and matches the skills the platform team already has (Java, Keycloak, Kubernetes operators). n8n stays for Google Chat approvals and notifications. A SaaS IGA is the fallback if the team cannot commit two engineers.

| Phase | When | Scope | Done when |
| --- | --- | --- | --- |
| 0. Decision and staffing | October 2026 | Name an identity owner. Assign 2 engineers. Request an Evolveum subscription quote. Name a role-catalogue owner per squad. | Decision recorded |
| 1. Pilot | January to March 2027 | midPoint on GKE. HCIS read-only resource. Targets: Keycloak `google-workspace` (enable, disable, attributes, logout), Google Workspace (suspend on leaver), LORA LTS `people` (create, update, deactivate). Birthright LORA roles from job title and branch. | A resignation in HCIS disables Keycloak, suspends GWS and deactivates LORA within 15 minutes, with an audit record |
| 2. Bravo roles | April to June 2027 | user-iam through its new API; CNV `user_access`; BPM groups; menu access. Access request and approval in midPoint with Google Chat notification by n8n. Retire the CSV flow and the surveyor Confluence table. | All Bravo role grants originate in midPoint |
| 3. Platform access | July to September 2027 | GCP Google Groups, GitHub teams, Datadog, Atlassian, Temporal Cloud, database access requests. Replace Jira tickets to SRE and DOE with midPoint requests. | SRE and DOE no longer edit membership by hand |
| 4. Governance | October to December 2027 | Quarterly certification for privileged roles; SoD rules (maker and checker in CNV, the credit approver chain in LORA); dashboards; an OJK audit pack. | First certification campaign completed with evidence |
| Later | 2028 | Active Directory and VPN, Salesforce (pbf-live), agents in Confins and bravo-auth-service | |

## 8.3 Decisions needed

1. Who owns identity lifecycle end to end (one name, not a committee).
2. Approve retirement of the three Keycloak 21.1.1 instances and the realm freeze.
3. Approve midPoint as the IGA core and the two-engineer allocation, or choose the SaaS fallback and accept data outside Indonesia.
4. Confirm that Google Workspace is the only employee IdP, and that AD remains for VPN and Windows only.

# 9. Open items and unverified claims

- Internet reachability of `microservices.prod.bravo.bfi.co.id` paths (diff-inspector, Camunda). No load balancer or Cloud Armor policy for the protected NEG was found in bravo-terraform.
- Which HCIS path runs in production (MQ listener, which `bravo-airflow` copy), and whether the 5-minute resign DAG exists anywhere.
- Configuration of the `google-workspace`, `bravo`, `IAM_BFI` and `qa` realms: Google broker, clients, roles, events, password policy.
- How Google Workspace accounts are suspended on resignation today.
- Who uploads BPP CSVs in production, and how SSF and corporate LORA users are created.
- Whether the AD `msad-user-account-control-mapper` blocks AD-disabled users at Keycloak login.
- Whether GKE Google Groups for RBAC is enabled on the live cluster, and how engineers get cluster credentials.
- Who installs the Keycloak Operator; the live log pipeline for Keycloak; the source of the `keycloak-user-mapper` image.
- Who issues the HMAC JWTs consumed by bfi-connect and bfi-operation-api.

# 10. Related security findings already open

- APPSEC-5 Camunda BPM RCE via JUEL injection (the shared `INTERNAL_SERVICE_KEY` is the credential at issue).
- Logging security findings (September 2026): Google Chat webhook keys in Datadog, a JWT signing key printed to stdout, full HR records at info in bravo-employee-service (bank account, religion, personal email), still visible in production logs on 1 October 2026.

# 11. Sources

Confluence: Keycloak Consolidation & Modernization (1338212400); Keycloak SSO with Google Workspace as IdP (1171456107); Unifying SSO (700153891); TRD Keycloak migrations to GWS SSO (1646297133); PRD Keycloak to Google Workspace SSO Migration (2471920352); PRD [LORA] User Management (2471002950); User Access (457113988); How to add IAM user access and page access (505709679); TRD User Management Checker Maker (1832386684); Technote Adjustment User Management for Deactivation (2185134282); 04 User Access, CNV (2525233326); Proposal Airflow-Based HCIS Sync (2361262191); TRD HCIS Employee Sync Airflow DAGs (2420506705); Internal Service Platform Building Block (1837465631); Authentication with Keycloak for SPV & ARE (395707061); User Keycloak Surveyor Platform (436535330); How to Add a New LORA User in UAT (2515107911); SOP Duplicate user on keycloak (2417819843); GCP User Access Policy (1197277243); S1 & Keycloak SSL incident (1308557314); LOS Platform GWS SSO IAM (1553301509); TRD LORA Workflow Stats, n8n (2571337736); Sporadic Employee data management (2644181169); bravo-cnv-service logging fixes (2755789028).

Jira: RI-118, RI-104, DMS-5743, DMS-5549, PRD-7427, DOE-565, DOE-640, DOE-669, APPSEC-5, DKBFI-264, DKBFI-265, DPS-2995.

Datadog (us5, production, 7 days to 2 October 2026): `dd.spans` filtered on `@http.url:*realms*` grouped by host, realm and service; `@http.url:*admin/realms*` grouped by method; Kubernetes statefulset, pod and ingress search on `keycloak`, `sso`, `auth`; statefulset manifests for image tags; logs on `prod-ms-cnv` and `prod-ms-employee`.

Code: `sre/app-deployment` (keycloak, sso, user-iam, bpm, cnv, employee, lora-task, lora-diff-inspector, secrets), `sre/bfi-app-deployment` (keycloak, auth, user-iam), `sre/bravo-terraform` (product/helm-apps nginx ingress, product/rbac, product/microservices/keycloak.tf, settings, devops), `squads/Internal Service/bravo-user-iam-service`, `bravo-employee-service`, `bravo-cnv-service`, `bravo-auth-service`, `squads/Scoring and Underwriting/bravo-bpm-service`, `bravo-e2e-test`, `squads/Tele Marketing/bravo-repeat-order-service`, `squads/Agency/*`, `lora-workspace/services/*`, and the long-tail repositories under `squads/others`, `squads/Digital Web`, `squads/Asset Management`, `squads/Irvan Setiawan`, `squads/PBF (SF)`, `bfi-finops-dashboard`.

External: Keycloak 26.7 and 26.8 release notes (SCIM inbound API supported in 26.8; AuthZEN experimental in 26.7); Keycloak Authorization Services guide and the Fine-Grained Admin Permissions v2 announcement (26.2); Ory documentation for Kratos, Hydra, Keto and Oathkeeper and the Ory Enterprise License feature list; Evolveum midPoint release page (4.10 November 2025, 4.11 planned 15 October 2026) and Keycloak connector page; n8n Sustainable Use License.
