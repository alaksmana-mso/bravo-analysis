# 01. System overview

## What `ms-bpm` is

`ms-bpm` (repository `bravo-bpm-service`) is the loan origination workflow service of BFI Finance's retail lending platform, internally called **Bravo**. It takes a loan application from lead intake through survey, credit scoring, underwriting, approval, document signing and go-live. It is a single Spring Boot application with an **embedded Camunda 7 engine**. The business logic and the workflow engine run in the same JVM and write to the same PostgreSQL database.

It is a system of record for loan applications in flight at a regulated consumer-finance lender. Around thirty other microservices are called from inside its workflows: credit bureau, KYC, scoring models, customer master, calculation, agreement, document management and others.

## Products it serves

One codebase runs several loan products. Each product is routed to a top-level process definition by a product-id map in application configuration.

| Product | Meaning | Top-level process key | Generation |
|---|---|---|---|
| NDF4W | New financing, four-wheel vehicle collateral | `NDF4W` | legacy, per-product process |
| NDF2W | New financing, two-wheel vehicle collateral | `NDF2W` | legacy, per-product process |
| NDF4W RO | Repeat-order variant of NDF4W | `NDF4W_RO` | legacy |
| NDF4W Sharia | Sharia-compliant NDF4W | `NDF4W_Sharia` | legacy, separate deployment (see below) |
| Unsecured, pre-approval | Smaller channels | `UNSECURED`, `preApprovalScoring` | legacy |
| DF4W | Dealer-financed four-wheel | `Unified_Process_Main_Workflow` | unified, one shared spine plus 32 child processes |
| DF2W | Dealer-financed two-wheel | `Unified_Process_Main_Workflow` | unified, configured, not yet in production |

The two generations coexist. The legacy processes carry about 94% of production volume today. The unified generation is where new products land. Both are part of the migration scope.

## Runtime stack

| Component | Version | Notes |
|---|---|---|
| Java | 17 | `gcr.io/distroless/java17-debian12` base image |
| Spring Boot | 3.5.16 | `spring-boot-starter-parent`; Spring Framework 6.2.19 pinned |
| Spring Cloud | 2025.0.x | OpenFeign clients to the other services (113 `@FeignClient`) |
| **Camunda Platform 7** | **7.23.0 Community Edition** | starters: `camunda-bpm-spring-boot-starter`, `-webapp`, `-rest` |
| Camunda DMN engine | 7.23.0 | `camunda-engine-dmn` |
| Camunda Spin plugin | 7.23.0 | `camunda-engine-plugin-spin` and `camunda-spin-dataformat-all` are declared; no Java code imports Spin |
| Camunda Keycloak identity plugin | `camunda-platform-7-keycloak` 7.23.0 | declared; a custom read-only identity provider is what actually runs (see [03](03-engine-integration.md)) |
| JUEL | 2.2.7 | explicit dependency |
| Persistence | Spring Data JPA, Hibernate 6.x | 238 `@Entity` classes, 271 application tables, in the **same database and schema** as the Camunda tables |
| Database | PostgreSQL 16.14 | Google Cloud SQL, reached through a Cloud SQL proxy sidecar |
| Messaging | RabbitMQ | application events; the engine does not use it |
| Cache / session | Redis | application use only |
| Identity | Keycloak (OIDC) | user authentication for the API and for Cockpit SSO |
| Observability | Datadog APM (Java tracer as agent), logs, Kubernetes metrics | |
| Schema migrations | Flyway, 1,350 migrations | 2 of them touch `ACT_*` tables (see [03 §7](03-engine-integration.md)) |
| Tests | 1,469 test files | 4 start the Camunda engine, using `camunda-bpm-process-test-coverage` and `camunda-bpm-assert` |
| Temporal | none in this service yet | a sibling Java service has a pilot on `temporal-spring-boot-starter` 1.39; see [05](05-temporal-at-bfi-today.md) |

Source size: about **499,000 lines of main Java in 5,083 files**. The workflow engine is a small part of that by line count, but it is the spine everything hangs from.

## Deployment

Two production deployments run the same codebase against two separate databases.

| Deployment | Purpose | Replicas | Per-pod resources (application container) | JVM |
|---|---|---|---|---|
| `prod-ms-bpm` | conventional products | 2, managed by a vertical pod autoscaler recommender | request 4 CPU / 8 GiB, limit 8 CPU / 16 GiB | `-XX:MaxRAMPercentage=80` |
| `prod-sharia-bpm-sharia` | Sharia products | 4 | same chart | same |

- Platform: Google Kubernetes Engine, Helm chart `microservices-http`, deployed by ArgoCD from GitHub Actions. Istio sidecar and Cloud SQL proxy sidecar in each pod.
- Rolling updates. Because 96 user tasks park instances on human action, there is never a moment with zero in-flight instances. Every deployment is a hot deployment against live engine state.
- A scheduled Kubernetes job restarts the conventional deployment once a day.
- Camunda process definitions are deployed by the Spring Boot auto-deployment from the classpath at start-up. There is no separate deployment pipeline for BPMN. 203 engine deployments have been recorded since May 2022; 7 in the last 90 days.

## Environments

Four environments: development, SIT, UAT and production, each with its own database. The Sharia variant has its own promotion pipeline. The counts in [04](04-production-footprint.md) are from production only.

## What surrounds the engine

- **Three operator consoles** (React/TypeScript, about 764,000 lines): surveyor, underwriting and operation. They call domain endpoints on `ms-bpm` (for example "complete survey", "branch manager decision"). They contain **no reference to Camunda**, never see a task id, and do not use Tasklist. This matters for a Temporal assessment: the human-task user interface is ours and stays. The engine only has to expose the wait state and let our service complete it.
- **Cockpit** is used by operations staff, mainly to retry failed jobs. Tasklist and Admin are effectively unused.
- **The Camunda REST API** (`/engine-rest`) is embedded and reachable to authenticated internal callers. Its regular consumers are internal tooling and end-to-end tests, not the consoles.

## A second, unrelated Camunda installation

A separate service in another squad, `bfi-incentive-api`, embeds **Camunda 7.17** with 6 BPMN files. It is a different codebase with a different owner and is **not** in the scope of this package. It is listed for completeness.
