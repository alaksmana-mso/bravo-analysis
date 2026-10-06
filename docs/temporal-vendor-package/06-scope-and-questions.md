# 06. What we ask Temporal to assess, and our questions

## 1. The situation in one paragraph

We run Camunda 7.23 Community Edition embedded in Spring Boot 3.5 on Java 17, in production for a regulated lender, with about 135,000 new loan applications a month and half a million applications open at any time. Camunda 7 Community Edition reached end of life in October 2025. We need a supported engine, and we are assessing more than one route. This package asks Temporal to assess one of them: porting the orchestration tier of `ms-bpm` to workflow code on the Temporal Java SDK, running on the Temporal Cloud account BFI already holds, while the rest of the service, its database and its three operator consoles stay as they are.

## 2. What we think the move is

Our own first reading, for Temporal to correct:

- **Keep:** 499,000 lines of Java, 238 JPA entities and 271 tables, 113 Feign clients, the three consoles and their endpoint contracts, the per-product configuration tables, and the 272 delegate bodies.
- **Rewrite:** the 53 BPMN models as about 60 Java workflow classes; the 2,004 lines of code that touch the engine API; the 48 user-task completion sites, which become signals or updates.
- **Design new:** the escalation and link-event idioms (384 elements) as structured control flow; search attributes for operations; the in-flight strategy; worker topology and sizing; the parity harness.
- **Decommission:** the embedded engine, Cockpit and its seven plugins, and about 490 GB of engine history tables.

The engine contact is 0.4% of the code. That is what makes the port bounded. It does not make it small: the 384 control-flow elements with no Temporal equivalent are exactly the part that is not reused.

## 3. Our constraints

| Constraint | Detail |
|---|---|
| Regulated workload | Loan origination records; auditability of decisions; a 90-day process history is a floor, not a ceiling, and it must be queryable after the workflow closes |
| No drain window | 540,000 open applications, tail up to one year; Camunda will run alongside Temporal for at least a year under any plan |
| Data residency | Our Temporal Cloud region is Singapore. We need Temporal's current position on data residency for Indonesian financial-services workloads, and what is held in Temporal (payloads, search attributes, history) versus in our database |
| Shared transaction today | Engine and application share one PostgreSQL transaction per delegate; every activity has to become safe to re-run |
| Human work is ours | Three in-house operator consoles; endpoint contracts must be preserved so 764,000 lines of console code do not change |
| Two deployments | Conventional and Sharia, same code, separate databases, separate regulatory treatment |
| Team | Java and Spring squads with deep Camunda 7 habits; a Go team with a year of Temporal in production; one Java pilot |
| Spring Boot | 3.5 now, moving to 4; the Java SDK and starter must support that line |
| Test coverage at the process layer | 4 engine tests today; replay and time-skipping tests would be new to the team |

## 4. What we ask Temporal to assess

1. **The element mapping.** Correct the table in [02 §10](02-process-model-inventory.md). In particular: the recommended pattern for the 190 escalation and 194 link events; whether call activities become child workflows or in-process calls; and how the 78 configuration-reading conditions should be handled so a flag change does not break determinism for an instance that has been running for days.
2. **The human-task pattern.** 96 wait points, a million open today, tail to a year. Signal, update, or asynchronously completed activity? How do we keep assignment, claim and reassignment, which live in our tables today, consistent with the workflow's view? What does a workflow blocked on a human wait for a year cost in history size, and when does Continue-As-New become necessary?
3. **The in-flight strategy.** There is no tool that moves a Camunda instance into a Temporal execution. Is the recommended shape "route new applications to Temporal and let Camunda run off", or "reconstruct state and start a Temporal execution at the matching step" for the 60,000 applications older than a year? What have other customers done at this scale?
4. **Sequencing.** We see three orderings and want Temporal's view on each:
   - **Direct:** port all four live top-level processes, legacy monoliths included.
   - **Consolidate first:** move the legacy products onto our unified spine (Camunda to Camunda), then port one spine. Removes 78% of the BPMN from the port, but migrates the highest-volume product twice and lengthens time on the unsupported engine.
   - **Spine first:** port the unified spine (one product, about 5% of volume) to Temporal as the pilot, then move each legacy product straight onto the Temporal spine, writing the long-tail activities once.
5. **Idempotency and the database.** The recommended pattern for 483 activities that today rely on a shared transaction, and how much of it can be generic in a base activity class. Whether an outbox or an idempotency key table is the usual answer at this volume.
6. **Operations.** What replaces Cockpit for our operations staff: Temporal UI plus which search attributes, and what we would still build ourselves (today they retry 4,433 open incidents and move stuck applications with process instance modification). What is the Temporal equivalent of modification, and its limits?
7. **Sizing.** Replace our rough 5 to 15 million Actions a month with a proper estimate from the element counts and volumes in [02](02-process-model-inventory.md) and [04](04-production-footprint.md). Worker fleet sizing for a Java worker holding hundreds of thousands of mostly idle workflows, given the sticky-cache lesson in [05 §3](05-temporal-at-bfi-today.md). Whether conventional and Sharia should be two namespaces.
8. **History and audit.** Retention settings, history export to our own store for the 90-day audit floor, and what a regulator-facing audit trail looks like when engine state is no longer in our database.
9. **Versioning.** The recommended deployment-versioning model for workflows that live for a year, given LORA's experience with one task queue per version and the cleanup it needed. Worker Versioning, patching, or both.
10. **Java SDK and Spring Boot 4.** Confirmation of starter support for Spring Boot 3.5 and 4, gRPC and protobuf pinning guidance, and anything we should know about running the worker in-process with the API pods versus separately.
11. **Testing.** How to build the parity harness: replay tests from production histories, time-skipping tests for the long waits, and a dual-run approach where Camunda and Temporal process the same application and the outcomes are diffed in our database.
12. **Effort, enablement and delivery model.** A phased effort estimate from Temporal's side for the sequencing you recommend; what Temporal's solutions or professional-services team would take on versus our squads; and the training path for Java engineers who know Camunda well and have the Go team's Temporal experience next door.

## 5. Questions that apply regardless

1. **Timeline.** We would like an assessment within about four weeks of receiving this package, and a first workshop sooner. What do you need from us to hit that?
2. **Access.** We can provide the 53 BPMN and 3 DMN files, the Java pilot's design notes, anonymised database statistics beyond those in [04](04-production-footprint.md), read access to our Temporal namespaces for LORA, and a read-only walk-through of the code with an engineer. We cannot provide production data or credentials.
3. **Reference customers.** Any lender or insurer who ported a BPMN-based origination system with long-running human waits to Temporal at this scale.
4. **Commitment headroom.** Our Actions commitment and its renewal are a separate commercial conversation. For the assessment we only need the technical Actions estimate in item 7.

## 6. How we would like to work

- One technical contact on each side.
- A first call to walk through this package and agree the model hand-over.
- Temporal returns a written assessment: the corrected mapping, the recommended sequencing and in-flight strategy, effort ranges, sizing, and the risks it sees.
- A second call to go through the assessment with our engineers, the Go team that runs LORA, and the people who operate `ms-bpm`.
