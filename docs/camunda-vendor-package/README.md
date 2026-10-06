# Information package for Camunda: BFI Finance `ms-bpm`

**Prepared by:** PT BFI Finance Indonesia, Engineering
**Date:** 2026-09-28
**Purpose:** give Camunda what it needs to assess the effort, risk and fit of moving our loan-origination workflow service from **Camunda 7.23 Community Edition** to either **Camunda 7 Enterprise Edition** or **Camunda 8 Enterprise**.

We are not asking for a proposal yet. We are asking for an assessment. The two paths are different in kind, and we want Camunda's view of each before we choose.

## What is in the package

| File | What it answers |
|---|---|
| [01-system-overview.md](01-system-overview.md) | What the service is, the stack it runs on, how it is deployed, and what sits around it |
| [02-process-model-inventory.md](02-process-model-inventory.md) | Every BPMN and DMN element we use, counted, with the patterns that matter for a migration |
| [03-engine-integration.md](03-engine-integration.md) | How our Java code touches the engine: delegates, engine services, plugins, webapps, REST, identity, transactions |
| [04-production-footprint.md](04-production-footprint.md) | Real production volumes, in-flight state, database size, history settings, throughput peaks |
| [05-scope-and-questions.md](05-scope-and-questions.md) | What we ask Camunda to assess for each path, our constraints, and our open questions |

A companion slide deck, `bravo-camunda-assessment.pdf`, summarises the package for a first meeting.

## Camunda's response

| File | What it is |
|---|---|
| [Camunda_estimates.pdf](Camunda_estimates.pdf) | Camunda's ballpark licence quote, by email on 2026-09-30 after the 2026-09-29 call: USD 148,400 a year for 1.6M process instances a year on the Essential Success Plan, flat for three years. Used in [option-1.md §3a](../option-1.md) as sub-option **1a** |

## How the numbers were obtained

Every figure comes from one of three places. Each file says which.

1. **The source repository** `bravo-bpm-service`, tag `v2.94.11` (commit `c47f1cb`, 2026-09-17). BPMN and DMN files were parsed with a script. Java usage was counted with text search over the main source tree.
2. **The production PostgreSQL database**, queried read-only on 2026-09-28. Camunda's own `ACT_*` tables were used for instance counts, table sizes, variable types and the schema log.
3. **The production Kubernetes cluster**, read through our observability platform on 2026-09-28, for replica counts, resource limits and JVM flags.

Counts from the repository describe the code as it is now. Counts from the database describe production, which runs the slightly older tag `v2.93.57`. The difference is a few days of ordinary feature work and does not change any figure that matters here.

## What is deliberately left out

- **Credentials, hostnames, connection strings, and internal IP ranges.** None are included. Please ask if a specific environment detail is needed for sizing.
- **Internal cost figures and vendor comparisons.** This package is about the technical facts of our system. Commercial questions will be handled separately.
- **Customer data.** No process variables, business keys or record contents are reproduced. Only counts and Java type names.

## Who to contact

Engineering contact: the sender of this package. Please route technical questions to the same address.
