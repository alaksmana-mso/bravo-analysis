# 03. How the application integrates with the engine

Counts are from text search over `src/main/java` at tag `v2.94.11` (499,237 lines, 5,083 files). Where a count is "files", it is the number of source files that mention the symbol at least once.

## 1. The shape of the coupling

The engine is embedded. Business logic runs **inside** the engine's threads as `JavaDelegate` implementations, and it reads and writes the application's own JPA entities in the **same database transaction** as the engine's `ACT_*` writes. There are no external task workers, no message correlation, and no separate worker processes.

| Coupling surface | Size |
|---|---|
| Files importing anything from `org.camunda` | about 690 (main + test) |
| Delegate classes | **272**: 225 implement `JavaDelegate` directly, 47 extend our `BaseActivity` |
| Distinct Spring beans referenced by `camunda:delegateExpression` | 274 |
| Files touching `DelegateExecution` | 300 |
| `setVariable(...)` call sites | 1,917 |
| `getVariable(...)` call sites | 995 |
| `BpmnError` thrown | 88 sites in 28 files |
| Engine-internal (`org.camunda.bpm.engine.impl`) imports | 23 occurrences in 9 files (see §5) |
| Lines that touch an engine API at all | about 2,000 of 499,000 (0.4%) |

The last row is the useful one. The engine is touched from a thin layer. The delegates themselves are ordinary Spring services that happen to receive a `DelegateExecution`. Their bodies call Feign clients, repositories and domain services that know nothing about Camunda.

## 2. Engine services used, method by method

| Service | Calls | Methods |
|---|---:|---|
| `RuntimeService` | 61 | `startProcessInstanceByKey` 14, `createProcessInstanceQuery` 14, `getVariable` 11, `setVariable` 10, `createProcessInstanceModification` 5, `deleteProcessInstance` 4, `createIncidentQuery` 3 |
| `TaskService` | 96 | `complete` 48, `claim` 24, `createTaskQuery` 23, `setVariables` 1 |
| `ManagementService` | 1 | `setJobRetries` (our own "retry from the API" endpoint) |
| `RepositoryService` | 2 | `getBpmnModelInstance` (reads the deployed model to find element names) |
| `IdentityService` | 3 | `createUserQuery` 2, `checkPassword` 1 |
| `AuthorizationService` | 1 file | Cockpit access set-up |
| `DecisionService` | 0 | DMN is reached only through business rule tasks |
| `HistoryService` | **0** | no history queries from application code |
| `ExternalTaskService`, `FormService`, `FilterService` | 0 | |

Notable:

- **Process instance modification** is used in 5 places. These are our "reprocess" and "revive" operations that move a stuck application to a chosen activity.
- **No history queries.** Our reporting reads our own application tables. Camunda history is kept for Cockpit and audit, not for the application.
- **No business keys.** Applications are found by process variables (`applicationId`) through `createProcessInstanceQuery().variableValueEquals(...)`.

## 3. Variables

- Variables are set with plain `setVariable(name, value)`; there is no use of the typed `Variables.objectValue(...)` API and no Spin.
- Serialisation is the engine default (Java serialisation for non-primitive values).
- Production runtime variable table, by type: string 22.1M, boolean 20.6M, **serializable 3.0M**, integer 0.7M, null 0.05M, long <0.001M.
- Sampled serializable classes: `java.util.UUID` (most), `java.util.ArrayList`, our own `enum` types from `ApplicationConstants` and `UnderwritingConstants`, `java.math.BigDecimal`, `java.util.HashMap`, `java.util.LinkedHashMap`, `java.lang.Float`.

For a Camunda 8 assessment: every variable would become JSON, and the 3.0M Java-serialised values in flight are enums, UUIDs, lists and maps, all of which have obvious JSON forms. There are no engine-specific classes in variables.

## 4. Error handling and retries

- A delegate signals a business outcome by throwing `BpmnError(code)`; the model catches it on an error boundary event. 88 throw sites, 114 error codes.
- A technical failure (exception) is left to the engine's job retry, configured per activity by `failedJobRetryTimeCycle` (186 declarations). When retries are exhausted an incident is raised. There are 4,433 open incidents in production at the time of writing, all of type `failedJob`; operations staff retry them from Cockpit.
- One aspect, `FailingOnLastRetryAspect`, reads the engine's internal `Context.getBpmnExecutionContext()` to detect the last retry of a job so that the delegate can record a definitive failure on the application instead of leaving only an incident.
- Activities also have an application-level "skip" mechanism. `BaseActivity.isNeedToProceed()` reads our own configuration tables (`workflow_master_config` and related) and silently no-ops a service task if it is not enabled for the product and risk tier. This is how one model serves several products. A Camunda 8 worker would carry the same check.

## 5. Engine internals we reach into

| File | Internal symbol | Why |
|---|---|---|
| `FailingOnLastRetryAspect` | `impl.context.Context`, `BpmnExecutionContext` | detect the last retry (see §4) |
| `IAMIdentityProviderPlugin`, `IAMIdentityProviderFactory`, `IAMIdentityProviderSession`, `IAMUserQuery`, `IAMGroupQuery`, `IAMTenantQuery` | `impl.cfg.ProcessEnginePlugin`, `ProcessEngineConfigurationImpl`, `impl.identity.ReadOnlyIdentityProvider`, `GroupQueryImpl`, `Page`, `impl.interceptor.CommandContext` | a custom read-only identity provider that answers Cockpit's user and group queries from our IAM (Keycloak) instead of `ACT_ID_*` (see §6) |
| `SurveyorCoverageProduct`, `SurveyorCoverageProductDto` | `impl.util.CollectionUtil` | incidental; trivially replaceable |

That is the whole list. There are no custom command interceptors, no custom job handlers, no custom history event handlers, no custom `ProcessEngineConfiguration` subclass, and no engine plugin other than the identity provider.

## 6. Identity, authorisation and the webapps

- `camunda.bpm.authorization.enabled: true`.
- The engine's own identity tables are empty: 0 users, 0 groups, 0 tenants in `ACT_ID_*`.
- When `CAMUNDA_SSO_ENABLED` is on, a conditional `ProcessEnginePlugin` installs a custom `ReadOnlyIdentityProvider` backed by our IAM, and Spring Security's OAuth2 client handles Cockpit login through Keycloak OIDC. Admin rights are granted by IAM role.
- `camunda-platform-7-keycloak` is on the classpath but our custom provider is what runs.
- Cockpit, Tasklist and Admin are embedded (`camunda-bpm-spring-boot-starter-webapp`). Cockpit is used by operations for job retries: in the last 30 days the operation log shows 151 `SetJobRetries` by 6 users, and a handful of task claims and completions. Tasklist is not used as an operator tool.
- Seven custom Cockpit/Tasklist plugin scripts ship with the application (about 4.9 MB of built JavaScript): instance route history, definition and instance historic-activity views, instance auto-refresh, a Tasklist audit-log tab, and a "robot" module. Their TypeScript sources are not in this repository; only the built bundles are. One further bundle (`instance-tab-modify.js`) is present but not loaded.

## 7. Database and schema

- One PostgreSQL database holds both the engine schema (`ACT_*`) and the application schema (271 tables) in the same `public` schema.
- Schema changes to the engine tables have been applied by our Flyway rather than by the engine's upgrade scripts on two occasions (December 2024): the four columns and two indexes that Camunda's 7.20→7.22 upgrade adds (`ACT_RU_JOB.BATCH_ID_`, `ACT_RU_JOB.ROOT_PROC_INST_ID_`, `ACT_HI_JOB_LOG.BATCH_ID_`, `ACT_HI_PROCINST.RESTARTED_PROC_INST_ID_`, plus `ACT_IDX_JOB_ROOT_PROCINST` and `ACT_IDX_HI_PRO_RST_PRO_INST_ID`), all with `IF NOT EXISTS`.
- **The engine schema log is consistent.** `ACT_GE_SCHEMA_LOG` in production reads `7.23.0` at id `1200`, with the 7.19→7.23 rows present. `ACT_GE_PROPERTY.schema.version` carries the legacy value `fox`, which is expected for a database first created by an older engine.
- Application code never selects from `ACT_*` tables directly and no JPA entity maps to them.

## 8. Transactions

Delegates run inside the engine's command transaction. Because the application's JPA entities live in the same database, a delegate that updates an application record and then throws rolls back both the engine state and the application change together. The team relies on this, mostly implicitly. It is the single most important behavioural difference to assess for Camunda 8, where a worker's database write and the engine's job completion are separate operations and must be made idempotent.

Related: 134 files carry `@Transactional`, and 260 `asyncAfter` continuations were placed to make external calls retryable. So the transaction boundaries are already thought about, activity by activity; they would need re-checking rather than inventing.

## 9. REST API and external callers

- The Camunda REST API is embedded at `/engine-rest` behind our authentication filter. Internal tooling and end-to-end tests call it. The operator consoles do not.
- Application-to-application calls into `ms-bpm` go through our own REST endpoints, which then call the engine services in §2.
- No other production service calls the Camunda REST API of `ms-bpm` as part of a business flow.

## 10. Tests

- 1,469 test files. **4** run the engine (`AntiFraudEngineCheckpointFunctionalTest`, `DMNFunctionalTest`, `UnsecuredLMSIntegrationFunctionalTest`, `AdvanceAIKYCActivityFunctionalTest`) using `camunda-bpm-process-test-coverage` and `camunda-bpm-assert`.
- The other tests mock the delegate's collaborators; `@MockBean` appears at 308 sites in 186 files.
- The consoles carry 829 tests that exercise `ms-bpm`'s domain endpoints and gate every console pull request. They do not touch the engine but they do assert the API contract that sits in front of it.

We say this plainly because it affects any migration plan: automated coverage of the process layer is thin, and a migration would need a parity harness we do not have today.
