# Information package for Temporal: BFI Finance `ms-bpm`

**Prepared by:** PT BFI Finance Indonesia, Engineering
**Date:** 2026-10-02
**Purpose:** give Temporal what it needs to assess the effort, risk and fit of moving our loan-origination workflow service from **Camunda 7.23 Community Edition** (embedded, Java) to **Temporal**, on the Java SDK, on the Temporal Cloud account BFI already holds.

We are not asking for a proposal yet. We are asking for an assessment. This is a re-platforming of the orchestration tier of a regulated lending system, and we want Temporal's view of the mapping, the sequencing and the in-flight strategy before we decide.

## What is in the package

| File | What it answers |
|---|---|
| [01-system-overview.md](01-system-overview.md) | What the service is, the stack it runs on, how it is deployed, and what sits around it |
| [02-process-model-inventory.md](02-process-model-inventory.md) | Every BPMN and DMN element we use, counted, and our first mapping of each to a Temporal construct |
| [03-engine-integration.md](03-engine-integration.md) | How our Java code touches the engine: delegates, engine services, plugins, identity, transactions |
| [04-production-footprint.md](04-production-footprint.md) | Real production volumes, in-flight state, history size and a rough Actions estimate |
| [05-temporal-at-bfi-today.md](05-temporal-at-bfi-today.md) | What BFI already runs on Temporal, and what we learned doing it |
| [06-scope-and-questions.md](06-scope-and-questions.md) | What we ask Temporal to assess, our constraints, the sequencing options, and our open questions |

A companion slide deck, `bravo-temporal-assessment.pdf`, summarises the package for a first meeting.

## Status

| Date | Event |
|---|---|
| 2026-10-02 | Package sent to Temporal. Written assessment expected in about four weeks. |

Files 01 to 04 share their facts with the package we prepared for our current engine vendor. The system is the same; only the vendor-specific reading of each fact differs.

## How the numbers were obtained

Every figure comes from one of four places. Each file says which.

1. **The source repository** `bravo-bpm-service`, tag `v2.94.11` (commit `c47f1cb`, 2026-09-17). BPMN and DMN files were parsed with a script. Java usage was counted with text search over the main source tree.
2. **The production PostgreSQL database**, queried read-only on 2026-09-28. Camunda's own `ACT_*` tables were used for instance counts, table sizes, variable types and the schema log.
3. **The production Kubernetes cluster**, read through our observability platform on 2026-09-28, for replica counts, resource limits and JVM flags.
4. **Our Temporal Cloud namespaces**, read through the Temporal CLI on 2026-09-23, for the figures in [05](05-temporal-at-bfi-today.md).

Counts from the repository describe the code as it is now. Counts from the database describe production, which runs the slightly older tag `v2.93.57`. The difference is a few days of ordinary feature work and does not change any figure that matters here.

## What is deliberately left out

- **Credentials, API keys, connection strings, hostnames and internal IP ranges.** None are included. Namespace names appear because Temporal already holds them.
- **Internal cost figures, our contract terms, and comparisons with other vendors.** This package is about the technical facts of our system. Commercial questions, including commitment headroom, will be handled separately.
- **Customer data.** No process variables, business keys or record contents are reproduced. Only counts and Java type names.

## Who to contact

Engineering contact: the sender of this package. Please route technical questions to the same address.
