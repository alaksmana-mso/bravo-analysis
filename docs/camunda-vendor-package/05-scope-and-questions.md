# 05. What we ask Camunda to assess, and our questions

## 1. The situation in one paragraph

We run Camunda 7.23.0 Community Edition, embedded in Spring Boot 3.5.16 on Java 17, in production for a regulated lender, with about 135,000 new loan applications a month and half a million applications open at any time. Camunda 7 Community Edition reached end of life in October 2025 and Spring Boot 3.5 open-source support ended in June 2026. We need a supported engine. We want Camunda's assessment of two routes: **stay on Camunda 7 with an Enterprise subscription**, or **move to Camunda 8 Enterprise**. We have not decided, and we want the assessment before we do.

## 2. Our constraints

| Constraint | Detail |
|---|---|
| Regulated workload | Loan origination records; auditability of decisions; 90-day process history is a floor, not a ceiling |
| No drain window | 540,000 open applications, tail up to one year; any migration must handle in-flight instances |
| Shared transaction today | Engine and application share one PostgreSQL database and one transaction per delegate |
| Google Cloud | GKE, Cloud SQL PostgreSQL 16; data residency in Indonesia matters for a SaaS option |
| Identity | Keycloak OIDC for users; no engine-native users |
| Human work is ours | Three in-house operator consoles; we do not use Tasklist or Camunda Forms |
| Two deployments | Conventional and Sharia, same code, separate databases and pipelines |
| Team | Java/Spring squads; no Camunda 8 or Zeebe experience yet |
| Test coverage at the process layer | 4 engine tests; a migration needs a parity approach we would build with your help |

## 3. Path A: Camunda 7 Enterprise Edition

What we expect this to be: replace the Community artifacts with Enterprise artifacts, move from 7.23 to 7.24, add a licence, and gain a patch channel and support. The models, delegates, database and consoles stay as they are.

**Please assess and confirm:**

1. **Support horizon.** For how long will Camunda 7.24 Enterprise receive security and bug patches? What is the published end date, and what happens after it?
2. **Spring Boot.** Which Spring Boot lines does the 7.24 Enterprise starter support, and is a Spring Boot 4 compatible starter on the Camunda 7 Enterprise roadmap? Our binding constraint is that Spring Boot 3.5 is out of open-source support; we need to know whether Camunda 7 EE lets us move to Spring Boot 4, or keeps us on a Spring Boot line that is itself only supported commercially.
3. **Upgrade path 7.23 → 7.24 EE.** Any database upgrade steps beyond the one schema-log row? Any change of behaviour we should test given the model patterns in [02](02-process-model-inventory.md)?
4. **Our custom identity provider plugin** (`ReadOnlyIdentityProvider` implementation in [03 §6](03-engine-integration.md)) and our seven Cockpit plugin bundles: any Enterprise Cockpit changes that affect them?
5. **Enterprise features we would actually use.** Cockpit history views and heatmaps, batch operations for the 4,433 open incidents, process instance migration tooling, and anything that reduces the 490 GB of history load on Cloud SQL (for example history-level guidance or Optimize offload).
6. **Licensing scope.** Two production deployments (conventional and Sharia), four environments each, plus the unrelated 7.17 installation in another squad. How is that counted?
7. **Effort estimate** from your side for A, assuming we do the Spring Boot work ourselves.

## 4. Path B: Camunda 8 Enterprise

What we expect this to be: a re-platforming. The engine leaves the JVM; 272 delegates become job workers; models are converted; in-flight instances and history need a plan; Cockpit becomes Operate; identity is integrated with Keycloak; the shared-transaction assumption is replaced with idempotent workers.

**Please assess, ideally by running the Camunda Migration Analyzer against our models (we will supply them under NDA):**

1. **Model conversion.** Of the element census in [02](02-process-model-inventory.md), what does the Diagram Converter handle automatically and what needs manual work? We are specifically asking about: 659 JUEL conditions (78 reading Spring configuration through `environment.getProperty`), 239 input/output mappings, 108 escalation end events with 82 escalation boundary events, 194 link events, 4 inclusive gateways with joins, 56 call activities with propagate-all variables, 186 retry-cycle declarations with custom back-off lists, and 3 DMN tables with FIRST hit policy.
2. **Delegate conversion.** 272 `JavaDelegate` classes, 483 bindings, all Spring beans. What is Camunda's recommended path: the Camunda 7 adapter, the Spring SDK job workers, or a generated worker per delegate? What does the adapter *not* cover that we have (`BpmnError` from 88 sites, `execution.hasVariable`, process instance modification from 5 places)?
3. **Transactions and idempotency.** Today a delegate's application write and the engine's state change commit together. What is the recommended pattern for our 483 service tasks, and how much of it can be done generically in a base worker class rather than per task?
4. **In-flight instances.** 540,824 open top-level instances, 1.1 million engine instances, 1.0 million open user tasks, tail to one year. What does the Data Migrator support for runtime state in our version (7.23 or 7.24) and for user-task state? Is the practical plan "migrate runtime" or "run both engines and route new applications to Camunda 8"?
5. **History.** 490 GB of 90-day full-level history, about 1.4 million activity-instance rows a day. Is history migration in scope or do we accept a cut-over point? What is the Camunda 8 storage sizing for this rate, and does the 8.8 architecture change the answer?
6. **Hosting.** SaaS with an Indonesian data-residency answer, or Self-Managed on GKE? For Self-Managed, sizing for the throughput in [04 §1](04-production-footprint.md): about 24,000 process instances on a peak day, about 1.4 million activity instances a day at full history (service tasks are the largest share), and peaks of 1,300 applications an hour.
7. **Human tasks.** We need the wait state, assignment from a variable, and a search/claim/complete API our consoles can call. We do not need Forms or Tasklist. Which API surface should we build against so that our consoles keep working unchanged?
8. **Identity and operations.** Keycloak OIDC integration for Operate; role mapping for our operations staff; what replaces our seven Cockpit plugins (route history, historic activities, auto-refresh, audit-log tab) in Operate; incident retry at the scale of 4,433 open incidents.
9. **Process instance modification.** Our reprocess and revive operations depend on it. What is the Camunda 8 equivalent and its limits?
10. **Feature flags in expressions.** The 78 `environment.getProperty` conditions switch flow on deployment configuration. What pattern does Camunda recommend so we do not have to write a variable per flag into every instance?
11. **Two deployments.** Would conventional and Sharia become two clusters, two tenants, or one cluster with a tenant id? Any regulatory-separation guidance from other customers?
12. **Team enablement and effort.** A phased effort estimate from Camunda's side, the professional-services or partner model you recommend, and the training you would expect for squads that know Camunda 7 well and Camunda 8 not at all.

## 5. Questions that apply to both paths

1. **Timeline.** We would like an assessment within about four weeks of receiving this package, and a first workshop sooner. What do you need from us to hit that?
2. **Access.** We can provide the 53 BPMN and 3 DMN files, anonymised database statistics beyond those in [04](04-production-footprint.md), and a read-only walk-through of the code with an engineer. We cannot provide production data or credentials.
3. **Reference customers.** Any lender or insurer at a similar scale (100,000+ long-running instances a month) who has taken each path.
4. **Coexistence.** If we take Path A now and Path B later, what does the Camunda 7 Enterprise subscription contribute to the Camunda 8 move, contractually and technically?

## 6. How we would like to work

- One technical contact on each side.
- A first call to walk through this package and agree the model hand-over.
- Camunda runs its analyzer and returns a written assessment per path, with effort ranges and the risks it sees.
- A second call to go through the assessment with our engineers and the people who operate the system.
