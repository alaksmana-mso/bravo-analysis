# Information package for CIB seven: BFI Finance `ms-bpm`

**Prepared by:** PT BFI Finance Indonesia, Engineering
**Date:** 2026-10-09
**Purpose:** give CIB software what it needs to assess the effort, risk and fit of moving our loan-origination workflow service from **Camunda 7 Community Edition** to **CIB seven**, and to propose a support arrangement.

We are assessing more than one route out of Camunda 7 Community Edition. This package asks for CIB seven's view of its own route. It is not a request for a proposal yet. We would like an assessment first, and a support offer with it.

## What is in the package

| File | What it answers |
|---|---|
| [01-system-overview.md](01-system-overview.md) | What the service is, the stack it runs on, how it is deployed, and what sits around it. Includes the older Sharia release line |
| [02-process-model-inventory.md](02-process-model-inventory.md) | Every BPMN and DMN element we use, counted, and the behaviours a fork must reproduce exactly |
| [03-engine-integration.md](03-engine-integration.md) | How our Java code touches the engine: delegates, engine services, internals, plugins, webapps, REST, identity, transactions |
| [04-production-footprint.md](04-production-footprint.md) | Real production volumes, in-flight state, database size, history settings, throughput peaks |
| [05-scope-and-questions.md](05-scope-and-questions.md) | What we understand of CIB seven from public sources, the migration we expect, and our questions |

A companion slide deck, `bravo-cibseven-assessment.pdf`, summarises the package for a first meeting.

## How the numbers were obtained

Every figure comes from one of four places. Each file says which.

1. **The source repository** `bravo-bpm-service`, tag `v2.94.11` (commit `c47f1cb`, 2026-09-17), for the main line. Tag `v2.53.108` on the `release-sharia` branch (2026-02-09) for the Sharia line. BPMN and DMN files were parsed with a script. Java usage was counted with text search over the main source tree.
2. **The production PostgreSQL databases**, queried read-only. Volumes and sizes on 2026-09-28. The Sharia schema state and the table-name checks on 2026-10-09.
3. **The production Kubernetes cluster**, read through our observability platform, for replica counts, image tags, resource limits and JVM flags.
4. **CIB seven's public sources** on 2026-10-09: Maven Central metadata, the `cibseven` GitHub organisation (releases, the `v2.2.0` tag, its PostgreSQL upgrade scripts, the `cibseven-migration` OpenRewrite recipe), and cibseven.org (editions, FAQ, roadmap). Where we quote these, please correct us.

The production volumes are the same figures we have given other parties. Counts from the repository describe the code as it is now. Production runs the slightly older tag `v2.93.57`; the difference does not change any figure that matters here.

## What is deliberately left out

- **Credentials, hostnames, connection strings and internal IP ranges.** None are included.
- **Internal cost figures and any comparison between vendors.** This package is about the technical facts of our system. Commercial questions will be handled separately.
- **Customer data.** No process variables, business keys or record contents are reproduced. Only counts and Java type names.

## Who to contact

Engineering contact: the sender of this package. Please route technical questions to the same address.
