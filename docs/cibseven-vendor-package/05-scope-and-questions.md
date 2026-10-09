# 05. What we ask CIB seven to assess, and our questions

## 1. The situation in one paragraph

We run Camunda 7 Community Edition, embedded in Spring Boot, in production for a regulated lender. The main line is on **Camunda 7.23.0 and Spring Boot 3.5.16**. The Sharia line is on **Camunda 7.17.0 and Spring Boot 2.7.18**. Neither engine nor framework receives patches any more. We carry about 135,000 new loan applications a month and half a million open applications at any time. We want a supported engine on a supported Spring Boot line, with as little change to our models, code and data as possible. CIB seven is one of the routes we are assessing.

## 2. What we understand from your public sources

Please correct anything here that is wrong or out of date.

| Topic | Our reading, 2026-10-09 |
|---|---|
| Latest public release | **2.2.0**, on Maven Central since 31 May 2026. Previous public releases: 2.1.0 (November 2025), 2.0.0 (May 2025) |
| Spring Boot | 2.2.0 ships two starter lines. The unsuffixed starters build on **Spring Boot 3.5.14**. The `-4` starters (`cibseven-bpm-spring-boot-starter-4`, `-rest-4`, `-webapp-4`) build on **Spring Boot 4.0.6 and Spring Framework 7.0.6**. The `main` branch moved to Spring Boot 4.1.1 on 8 October 2026 |
| Editions | Community (free, Apache 2.0, six-month release cycle, no support); Community+ (security patches and bug fixes, six-month maintenance); LTS (18 months, hotfixes, SLA options, off-site support); Enterprise (LTS plus all Camunda 7 Enterprise features, batch operations, OpenTelemetry, personal support); OEM. No prices are published |
| Patch delivery | Your FAQ says security patches and hotfixes ship every 4 to 8 weeks for paid editions, and critical vulnerabilities immediately. Your roadmap lists 2.1.2 (December 2025) and 2.1.3 (January 2026). **Neither is on Maven Central**, so we assume patch releases reach paying customers through a separate repository |
| Support for Camunda 7 CE as-is | Your site says that since October 2025 you offer support and maintenance for Camunda 7 Community Edition |
| Code migration | The OpenRewrite recipe `org.cibseven.ReplaceCamundaWithCIBSeven` renames `org.camunda` to `org.cibseven` in Java, XML, YAML and service files, and maps about 190 artifacts. It defaults to the `-4` starters and Spring Framework 7.0.6. It maps the Keycloak plugin, `camunda-bpm-assert`, `camunda-bpm-mockito` and `camunda-process-test-coverage` to CIB seven equivalents |
| Database migration | From a 7.23 schema, the `v2.2.0` PostgreSQL upgrade scripts are 7.23→7.24, 7.24→2.1 and 2.1→2.2. **None changes an `ACT_*` table.** They add three schema-log rows, and 2.1→2.2 creates eight `MOD_*` tables for the modeler and one `CHAT_MESSAGES` table. None of those names exists in either of our databases today. Scripts for 7.17→7.18 onwards are also in the tree |
| Keycloak plugin | `cibseven-keycloak` is on Maven Central at 2.0.0 and 2.1.0. We did not find a 2.2.0 |
| Activity | 147 stars; 26 commits to `cibseven/cibseven` since 1 September 2026; companion repositories for the web client, modeler, migration and an MCP server, all active this month |

## 3. The migration we expect

**Main line, Camunda 7.23 on Spring Boot 3.5:**

1. Run your recipe; move to the `-4` starters and Spring Boot 4.0.x in the same change. We cannot stay on Spring Boot 3.5, because its open-source support has ended.
2. Fix what the recipe does not: our 9 files that import engine internals, our seven Cockpit plugin bundles, our custom identity provider, the Spring Boot 4 changes in our own code (for example 308 `@MockBean` sites).
3. Run the upgrade scripts 7.23→7.24→2.1→2.2 on each database.
4. Rehearse on a copy of production. Then a rolling deployment with the job executor paused.

**Sharia line, Camunda 7.17 on Spring Boot 2.7:** either run the full upgrade chain 7.17→2.2 and the `javax`→`jakarta` move on that branch, or retire the branch and run Sharia on the main line first. We have not decided. We would like your view on which carries less risk.

## 4. Questions

### 4a. Support and commercial

1. **Which edition fits us**, given a regulated lender, two production deployments, and the volumes in [04](04-production-footprint.md)? What is the pricing basis: per deployment, per core, per process instance, flat?
2. **What do we get without a paid edition?** Concretely: between the six-monthly public releases, do security fixes reach the public repository at all? If a critical engine vulnerability is published, when would a Community user get a fixed artifact?
3. **How are patches delivered** to paying customers: a private Maven repository, signed artifacts, release notes with CVE references? How long is a patch line maintained after the next minor release?
4. **Support hours and response times** for a customer in Indonesia (UTC+7). Language. Severity definitions. Is there a partner in South-East Asia?
5. **Contracting.** Can CIB software GmbH contract directly with an Indonesian company? What continuity commitments exist if the commercial relationship ends: source availability, escrow, continued access to patch releases already shipped?
6. **Interim support for Camunda 7 CE.** You offer support for Camunda 7 Community Edition as it is. Would that cover our 7.23 main line and our 7.17 Sharia line while we migrate? On what terms?
7. **Licensing scope.** Two production deployments, four environments each, and an unrelated Camunda 7.17 service in another team ([01](01-system-overview.md)). What would be counted?

### 4b. Engine behaviour

8. **Lineage.** The fork point in your repository is Camunda 7.22. Does CIB seven 2.2 contain every engine fix in Camunda 7.23 and 7.24 Community Edition? Is there a list of behavioural differences from Camunda 7.23?
9. **The five behaviours in [02 §10](02-process-model-inventory.md)**: job retries and incidents, error and escalation propagation, JUEL resolution including Spring bean calls, call activities with `latest` binding, inclusive joins and link events. Anything different?
10. **Expressions.** Your `main` branch enabled a task-filter expression whitelist by default on 8 October 2026. Does that, or anything planned, restrict bean method calls in BPMN expressions? We rely on 78 such calls.
11. **Serialised variables.** 3.0M `serializable` variables are in flight ([03 §3](03-engine-integration.md)). Confirm that existing values deserialise unchanged and that no Java-serialisation default is stricter than in Camunda 7.23.
12. **Transactions.** Confirm that delegate execution, flush order and `asyncAfter` behaviour are unchanged ([03 §8](03-engine-integration.md)).

### 4c. Migration and cutover

13. **Recipe coverage for our code.** Our 9 files using `org.camunda.bpm.engine.impl` classes (`Context`, `BpmnExecutionContext`, `ProcessEnginePlugin`, `ProcessEngineConfigurationImpl`, `ReadOnlyIdentityProvider`, `GroupQueryImpl`, `Page`, `CommandContext`, `CollectionUtil`): are all present under `org.cibseven` with the same signatures?
14. **Configuration.** Does CIB seven keep the `camunda.bpm.*` property prefix in Spring Boot, or move to a new one? Does the web application stay at `/camunda/*`?
15. **Cockpit plugins.** Seven custom plugin bundles are served from `webjars/camunda/app/cockpit/scripts` ([03 §6](03-engine-integration.md)). Do they load unchanged in your classic web application? Does your newer web client support plugins?
16. **Identity.** We run our own `ReadOnlyIdentityProvider` plugin. The Sharia line uses the community Keycloak plugin 2.2.3. Is a `cibseven-keycloak` release planned for 2.2, and is our custom provider supported as-is?
17. **Database.** Can the `MOD_*` and `CHAT_MESSAGES` tables be left out if we do not use the modeler or chat features? They would sit in the same schema as our 271 application tables.
18. **In-flight instances.** Confirm that 1.1M engine instances, 1.0M open user tasks, timers, jobs and 4,433 open incidents resume on CIB seven from the same tables, with no data migration.
19. **Rolling deployment.** During a rolling update, a Camunda 7.23 pod and a CIB seven pod may briefly share one `ACT_RU_JOB` table. Is that safe, or must the job executor be paused across the switch?
20. **Rollback.** After the 7.24, 2.1 and 2.2 schema-log rows are written, can a Camunda 7.23 pod start against the database again if we need to roll back?
21. **Spring Boot line.** Which Spring Boot version will your next public and next patch releases target? Our Spring Cloud release train currently constrains us to Spring Boot 4.0.x.
22. **Sharia path.** 7.17→2.2 in one step, or through intermediate versions? Any known issues on PostgreSQL 16 with that chain?

### 4d. Delivery

23. **Effort.** Your estimate of the migration effort for each line, and which parts you would do.
24. **Services.** Your professional-services model for migration support, rehearsal and cutover. Remote is fine.
25. **References.** Any bank, lender or insurer running CIB seven at 100,000 or more long-running instances a month.

## 5. Our constraints

| Constraint | Detail |
|---|---|
| Regulated workload | Loan origination records; auditability; 90-day process history is a floor |
| No drain window | 540,000 open applications, tail up to one year |
| Shared transaction | Engine and application share one PostgreSQL database and one transaction per delegate; we want to keep this |
| Google Cloud | GKE, Cloud SQL PostgreSQL 16, Java 17 |
| Identity | Keycloak OIDC; no engine-native users |
| Human work is ours | Three in-house consoles; we do not use Tasklist or Camunda Forms |
| Two deployments, two release lines | Conventional on 7.23, Sharia on 7.17; separate databases and pipelines |
| Test coverage | 4 engine tests at the process layer; we would build a parity check with your help |

## 6. How we would like to work

- One technical contact on each side.
- A first call to walk through this package, and an NDA for the model files.
- A written answer to section 4 and an indicative support offer, in about four weeks.
- If useful, a short joint spike: run your recipe on our main line in a sandbox and start it against a copy of a non-production database.
