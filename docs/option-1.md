# Option 1 — Land on a supported stack: fork the engine and upgrade Spring Boot

**Companion to** [option-2.md](option-2.md) (Temporal), [option-3.md](option-3.md) (LORA) and [option-summary.md](option-summary.md) (comparison and decision framework).

**Status of the wider decision.** No decision has been taken about Bravo's long-term platform. This document assesses Option 1 on its own merits.

> **Correction, 2026-09-10.** An earlier version of this document said three things. That the free upgrade path ended at Camunda 7.24.0 Community Edition. That Spring Boot 4 therefore needed a Camunda 7 **Enterprise licence**. And that the work was **11–19 engineer-months**. All three were wrong.
>
> The Camunda 7 **community forks**, Operaton and CIB seven, are both Apache 2.0. Both run on Spring Boot 4. Both keep the `ACT_` schema unchanged and ship automated migration recipes. The measured work is **18–33 engineer-days**, and **no licence is required**.
>
> The correction comes from the Bravo team's decision memo, [Camunda 7 Exit Plan](production-findings/Camunda%207%20Exit%20Plan.pdf) (2026-09-09). We re-verified its counts against the tree for this revision (§8).

**Verdict in one line.** Option 1 costs roughly **1–1.5 engineer-months**. It lands Bravo on a fully supported engine *and* a supported Spring Boot. There is no licence to buy, no data migration, and rollback is clean. That makes it the cheapest of the three options by an order of magnitude, and it removes the end-of-support exposure outright rather than postponing it.

---

## 1. The exposure, stated precisely

Bravo's runtime, as pinned in [`pom.xml`](../../squads/Scoring%20and%20Underwriting/bravo-bpm-service/pom.xml) and `Dockerfile`:

| Component | Bravo pin | Status |
|---|---|---|
| **Camunda Platform 7** | **7.23.0**, Community Edition | CE line ended at **7.24.0** (14 Oct 2025); upstream repository **archived**; no security patches |
| **Spring Boot** | **3.5.16** | OSS support ended **30 Jun 2026**; 3.5.16 was the **final** OSS patch (25 Jun 2026) |
| Spring Cloud | 2025.0.1 (Northfields) | Tied to Boot 3.5 |
| Java | 17 (`gcr.io/distroless/java17-debian12`) | **Stays.** Boot 4 supports JDK 17–26 and both forks build against 17 — no JDK change required |

Neither of these was a decision. Camunda 7 went end-of-life underneath the service. Spring Boot 3.5 reached its published cut-off. Bravo gets no security patches for either. It also sits one minor version behind even the final Community Edition release.

This matters more here than it would elsewhere. `bravo-bpm-service` is the system of record for loan applications in flight at a regulated lender. It also orchestrates roughly thirty microservices.

**One thing here is not a version problem, but it shares the blast radius.** [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) records 61 injected remote-code-execution process definitions in the production engine. One of them ran.

**Vector corrected 2026-09-10.** The way in was *not* the `permitAll()` on `/camunda/**`. The deploy path `/engine-rest/**` requires a credential. So **someone held a valid Keycloak token, or the shared `INTERNAL_SERVICE_KEY`**. That shared secret grants full engine rights, because no `ProcessEngineAuthenticationFilter` establishes a Camunda identity on that path.

So this is **a compromised-credential problem with a configuration component**, not a configuration defect on its own. The fix has three parts: rotate the secret and issue per-caller secrets, add the auth filter, and clean up the `permitAll`. It must be done under **every** option in this pack. It is also why an unpatchable engine is not a theoretical concern.

---

## 2. The constraint that shapes everything

> **Camunda 7.23's Spring Boot starter will not run on Spring Boot 4.**

The coupling runs in exactly one direction:

- Moving to Spring Boot 4 **forces** a decision about the engine.
- Swapping the engine does **not** force Spring Boot 4.

That removes the most intuitive plan from the table. **"Do the Spring Boot upgrade first and decide about Camunda later" is not available.** Any Spring Boot 4 work is blocked behind an engine decision.

The reverse is available: swap the engine and stay on Spring Boot 3. But as §3 shows, that leaves Bravo on an end-of-life Spring Boot whichever fork it picks.

---

## 3. The options

Camunda 7 has several community forks. Two are credible for a service this critical: **Operaton** and **CIB seven**. Both are **Apache 2.0**. Both keep the `ACT_` database schema. Both accept the legacy `camunda:` BPMN namespace. And both publish an automated OpenRewrite migration recipe.

Both are published on Maven Central, and we confirmed both for this revision. `org.operaton.bpm:operaton-engine` is at **2.1.4** — 2.2.0-M1 through M3 are milestones. `org.cibseven.bpm:cibseven-engine` is at **2.2.0**, released 31 May 2026. Each ships a Spring Boot starter.

**Camunda 8 is not an upgrade path, and it is out of scope here.** It removes the embedded engine. It replaces all 272 `JavaDelegate` classes with external job workers. It drops the `ACT_` tables from the database. And it requires a paid licence for self-managed production use. That is a multi-quarter rewrite programme with its own budget line, not a version bump. It is comparable in size to [option-2.md](option-2.md), and it should be evaluated there.

| | **A — Sequenced** | **B1 — Combined, Operaton** | **B2 — Combined, CIB seven** |
|---|---|---|---|
| Engine | CIB seven 2.2.0 | Operaton 2.1.4 | CIB seven 2.2.0 (`-4`) |
| Spring Boot | **3.5.14 — backwards** | **4.0.8** | **4.0.6** |
| Camunda 7.24 hop first | not needed | **required** | not needed |
| Regression cycles | **two** | one | one |
| Ends on a supported stack | **No** — engine yes, Spring Boot no | **Yes** | **Yes** |
| Effort | **25–40 days** | **20–33 days** | **18–30 days** |

**Approach A** is the only way to separate the two migrations in time. CIB seven is the only fork that allows it, because it is the only one still shipping a Spring Boot 3 line. Its honest value is that it spreads risk across two smaller changes.

Its cost is real. It pays the full regression bill twice. It moves Spring Boot *backwards*, from 3.5.16 to 3.5.14. It leaves Bravo on an end-of-life Spring Boot for as long as the second step takes. And it commits to CIB seven before anyone has weighed the fork question, because no other fork offers this route. It is a way-station, not a destination.

**Approaches B1 and B2** are the same shape and differ only in which fork is adopted. Both land on a supported engine and a supported Spring Boot in a single regression cycle.

**Target Spring Boot 4.0.x, not 4.1.x.** `spring-cloud` Oakwood (2025.1.x) is the only GA release train, and it pins `spring-boot.version` to 4.0.8. So Boot 4.1 waits until a `spring-cloud` train targets it. *(This corrects the earlier version of this document, which proposed 4.1.x.)*

---

## 4. Which fork — the question this document does not answer

The Bravo team's memo deliberately declines to pick, and the reasoning holds up. The measured evidence says two different things at once.

| | **Operaton 2.1.4** | **CIB seven 2.2.0** |
|---|---|---|
| Commits, last 52 weeks | **2,310** | 258 |
| Distinct authors, 12 months | **52** | 31 |
| Top-contributor concentration | ~80% of non-bot commits | **25%** |
| Ex-Camunda core engineers active | none | **two** |
| Long-term support | **none** — 6-month lines | **paid**, terms undisclosed |
| Legal entity | none yet; non-profit planned | CIB software GmbH (Munich) |
| Requires 7.24 hop first | **yes** | no |
| Ships process-test-coverage | **no** — 4 tests affected | yes |
| Keycloak identity provider | 2.1.0 — lags the engine | 2.2.0 |
| `engine.impl.util.CollectionUtil` | **absent** — breaks 2 files | present |
| Cockpit webjar path | moves to `webjars/operaton/` | **unchanged** |

**CIB seven is cheaper to migrate to.** It avoids five concrete frictions: the 7.24 hop, the `CollectionUtil` compile break, relocating seven Cockpit plugin bundles, and two missing test dependencies. It also employs two engineers who wrote large parts of the original engine. And a support contract is at least in principle purchasable.

**Operaton is the healthier project.** It has nine times the commit volume and two-thirds more distinct contributors. It has a broader ecosystem under one organisation. And it commits explicitly to Apache 2.0, with no paid tier and no open core.

> **The question that decides it:** do we require a contractual support agreement for the workflow engine, and can one actually be purchased for a BFI entity?
>
> **If yes → CIB seven.** Company-backed, deep original-engine expertise, cheaper migration, a purchasable relationship.
> **If no → Operaton.** On a core engine over five to ten years, sustained project activity is worth more than a one-off migration saving. Operaton leads on that by a wide margin.

**Unresolved.** CIB seven's actual support terms are **not published**. Length, service levels and pricing are all sales-contact-only. If the decision leans that way, start that enquiry *before* finalising the choice, not after.

**A note on risk posture.** Bravo already runs two end-of-life foundations in production, and no control has stopped it. So there is no hard gate here.

But two situations that look alike are worth separating. What exists **now** is drift: Camunda 7 went end-of-life underneath the team. What would be **chosen** is a project with a six-month support window, a concentrated maintainer base, and — for Operaton — no legal entity yet. Those two things attract different scrutiny. Do not read today's silence as pre-approval for tomorrow's deliberate choice.

The counterweight argues for moving rather than waiting. **Camunda 7 Community Edition had the long support window, and it still ended in an archived repository with no upgrade path.** In practice, a six-month line with monthly patches responds to security issues faster than a multi-year line that stops dead.

---


### 4a. The consoles are insulated from this change

**Added 2026-09-10.** Bravo LOS includes three React/TypeScript operator consoles: `bravo-surveyor-console`, `bravo-operation-console` and `bravo-underwriting-console`. Together they hold **763,861 lines of source and 829 test files**. This document had not counted them ([bravo-people.md §2](bravo-people.md), [bravo-testing.md §1.1](bravo-testing.md#11-the-console-tier-what-actually-gates-a-bravo-front-end-change)). They matter to a fork swap in exactly two ways, and both are favourable:

**They are not in scope.** We searched the console source for engine coupling and found **zero references to Camunda anywhere**. The consoles call domain verbs behind a `/bpm` prefix — `/v1/head-surveyor/assignment-request/reprocess`, `/v1/operation-assignment/release-assignment`, `PATCH /v1/underwritings/{id}/approval/bm-decision` — and never see a Camunda task id. Operaton and CIB seven keep the `ACT_` schema, the engine API and the Spring REST surface. So **the swap itself changes no console line and needs no console redeploy.** The 18–33 engineer-day estimate does not need widening.

**They are a regression net the estimate did not credit.** Those 829 tests run as a blocking job on every console pull request. They assert the response shapes of the `ms-bpm` endpoints the consoles depend on. That is exactly the surface a cutover could break invisibly. So running the three console suites against a staging instance on the forked engine gives you a **cheap, existing, high-coverage smoke test of the API boundary**. It is the closest thing Bravo has to the parity harness this document says it lacks. It does not test the engine's internals. It does test that the application still answers correctly.

**Two caveats.** First, the three consoles are **three toolchains, not one**: React 17 against 18, Vite 4 against 7, Node 18 against 20, ESLint against Biome, and three different versions of the shared `@bfi-finance/frontend-ui` ([bravo-delivery.md §2](bravo-delivery.md#2-custom-front-end-easy-per-page-hard-per-system)). So "run the console suites" means standing up three separate setups.

Second, console coverage is measured and **not enforced**. The thresholds sit at 0% for surveyor and operation, and 1% for underwriting. So the suites prove that *the tests that exist still pass*. They do not prove the boundary is covered. Turn the thresholds on before relying on them as a cutover gate ([bravo-testing.md recommendation 15](bravo-testing.md#recommended-actions)).

## 5. Effort

One engineer, excluding review, deployment soak and any work arising from the open questions in §9.

| Work | Estimate | Confidence |
|---|---|---|
| Pre-decision cleanup (§6) | 1–2 days | High |
| **Spring Boot 4 alone** | **12–20 days** | Medium — variance is Hibernate 7 and test fallout |
| Engine swap, CIB seven | +3–5 days | Medium |
| Engine swap, Operaton | +5–8 days | Medium — adds the 7.24 hop, bundle relocation, test-coverage rework |
| PROD-clone rehearsal | 2–3 days | Medium |

| Path | Total | Cycles |
|---|---|---|
| **B2 — CIB seven combined** | **18–30 days** | one |
| **B1 — Operaton combined** | **20–33 days** | one |
| A — sequenced | 25–40 days | two |

**Note the shape. The engine swap is the small half.** Spring Boot 4 is 12–20 of the 18–33 days. That half is owed whichever engine Bravo ends up on, including under [Option 2](option-2.md). The framework upgrade does not disappear just because Camunda does.

**Reconciled to this pack's units:** roughly **1–1.5 engineer-months** to build, or **1.5–2.5 engineer-months** once you add review, deployment soak and fallout from open questions. Option 2 is 31–57 and Option 3 is 30–57. At an assumed Rp30–50M fully loaded per engineer-month, that is **Rp45M – Rp125M**, with **no licence to buy**.

**Run-rate is unchanged.** The orchestration tier stays at ≈Rp58M a month in production — `ms-bpm` pods at Rp5.3M plus Cloud SQL at Rp52.7M. That is the cheapest of the three options ([compare.md §3.12](compare.md)).

One reduction is available on its own. Camunda history is at `full` level with `historyTimeToLive: P90D`, so every variable write on 483 service tasks lands in `ACT_HI_DETAIL`. That is a material slice of the Rp52.7M database line.

---

## 6. Work that lands now, independent of the decision

Six items. None of them depends on which path or fork you choose, and all of them shrink the eventual migration diff. Four are pure deletion. **This is 1–2 days of work, and it can start immediately.**

| # | Change | Why now | Risk |
|---|---|---|---|
| 1 | Replace `org.camunda.bpm.engine.impl.util.CollectionUtil` with `org.springframework.util.CollectionUtils` in `SurveyorCoverageProduct.java` and `SurveyorCoverageProductDto.java` (6 call sites) | The class is **absent from Operaton entirely**; the recipe would rename the import to a class that does not exist and break the compile. Both files already import Spring's version and use it four lines away for the identical check | None — behaviourally identical |
| 2 | Delete `instance-tab-modify.js` (219 KB) | Commented out in `config.js`, and the commented reference misspells it `.hjs`, so it has never loaded | None — dead code |
| 3 | Remove `camunda-bpm-mockito` from `pom.xml` | Declared; imported by zero test files | None |
| 4 | Remove `com.vladmihalcea:hibernate-types-55` | Declared; imported by zero files | None |
| 5 | Remove the OpenTracing / Jaeger stack and `config/TraceConfig.java` | Both upstream projects are retired; the pinned versions are the last ever published. The sole consumer returns a no-op tracer behind a normally-false condition | Sign-off — removes a dormant tracing hook |
| 6 | Delete `config/OldSecurityConfig.java` | Entirely commented-out `KeycloakWebSecurityConfigurerAdapter` | None |

Items 1 and 2 matter to the migration. Items 3 to 6 are hygiene that happens to reduce the Spring Boot 4 surface.

---

## 7. Pre-flight gates

These run **before** any date is committed. Two of them can change the plan.

### 7.1 Schema-version reconciliation — the one real database risk

This is the most important new finding in the memo, and it was verified for this revision.

Two Flyway migrations add four columns and two indexes to Camunda-owned tables:

```
V2_0_202412300429__alter-camunda-table.sql       -- 4 columns, all "add column if not exists"
V2_0_202412301022__alter-camunda-table-add-index.sql  -- 2 indexes, "create index concurrently if not exists"
```

Confirmed contents: `act_ru_job.batch_id_`, `act_ru_job.root_proc_inst_id_`, `act_hi_job_log.batch_id_`, `act_hi_procinst.restarted_proc_inst_id_`, plus the indexes `act_idx_job_root_procinst` and `act_idx_hi_pro_rst_pro_inst_id`. These are **verbatim replays of Camunda's own upgrade DDL**. The 7.20 → 7.21 and 7.21 → 7.22 scripts shipped inside the engine jar add exactly these four columns and these two indexes, index names included.

> **Inference — strong, not verified.** The database was never engine-upgraded through the 7.21 and 7.22 steps. Someone hand-replayed the official DDL through Flyway instead. The columns arrived; the engine's own record of *what version the schema is at* may not have moved with them.

That matters because engine upgrade scripts use bare `add column`, with **no `IF NOT EXISTS`**. The Flyway copies were defensive; the engine's own scripts are not. So if `ACT_GE_SCHEMA_LOG` reports a version below 7.22 while those columns already exist, the engine will attempt an upgrade that cannot succeed. Startup then fails with `column "batch_id_" of relation "act_ru_job" already exists`.

The `IF NOT EXISTS` guards made the migrations idempotent. That was the right call. It also made the drift **silent**, because nothing ever failed loudly enough to reveal it.

**Run the diagnostics against SIT, UAT and PROD independently. Do not infer PROD from SIT.**

| Result | Meaning | Action |
|---|---|---|
| Top row `1300` / `7.24.0`, all four columns present | Clear — schema and label agree | No DDL runs. Proceed |
| Version below 7.22, columns present | **Drift confirmed** | Insert the missing `ACT_GE_SCHEMA_LOG` rows to reconcile the label **before** cutover |
| Version at or above 7.22, columns missing | Inverse drift | Investigate — not expected, and would invalidate assumptions |

For reference, the entire Camunda 7.23 → 7.24 Postgres upgrade script is one row: `insert into ACT_GE_SCHEMA_LOG values ('1300', CURRENT_TIMESTAMP, '7.24.0');`. **There is no DDL at all.** So the documented 7.24 prerequisite, Path B1, costs nothing at the database layer.

### 7.2 Process-variable census

In-flight variables should be safe. Nothing in `src/main/java` uses Spin or the `ObjectValue` API. Stored values are String, Boolean, Double and `java.util.UUID`, and `UUID` is a JDK class the package rename does not touch. Confirm this against real data with `SELECT type_, COUNT(*) FROM act_ru_variable GROUP BY type_`. Any `serializable` rows carrying an `org.camunda.*` class name would be the one blocker to a hot cutover. We found no code path that creates one.

### 7.3 Production-clone rehearsal

This step is non-negotiable. Restore a PROD clone and run the full cutover against it. Then verify five things:

- the engine starts and applies no unexpected DDL
- in-flight instances resume and advance
- user tasks stay claimable, with their existing assignments
- Cockpit plugins load and render
- pending jobs and timers fire

> **Where to spend the rehearsal budget.** During a rolling deployment, two engine versions run against the same `ACT_RU_JOB` table. That is the one genuinely untested area of this migration.

---

## 8. Blast radius

Every count below was re-measured against the working tree for this revision and matches the memo exactly.

| Surface | Size | Effect |
|---|---|---|
| Files importing `org.camunda` | **687** (351 main + 336 test) | Mechanically renamed by the recipe |
| Delegate classes | **272** (225 + 47) | `JavaDelegate` and `BaseActivity`. Imports change; **logic untouched** |
| BPMN files | 53 | **Unchanged** — legacy `camunda:` namespace accepted |
| DMN files | 3 | Unchanged |
| `camunda:delegateExpression` in BPMN | 483 | Unchanged — resolve as before |
| Flyway migrations touching `ACT_` | 2 | Unchanged |
| Internal `engine.impl` imports | 4 across 3 files | `Context` and `BpmnExecutionContext` resolve as-is; `CollectionUtil` fixed by §6 item 1 |
| Cockpit / Tasklist plugin bundles | 7 (~4.9 MB) | Relocated (Operaton) or untouched (CIB seven) |
| `@MockBean` sites | **308 across 186 files** | Path B only — `@MockBean` → `@MockitoBean` |
| Total test files, `ms-bpm` | 1,457 | Full regression required |
| Test files in the three operator consoles | **829** (188,389 LOC) | **Untouched by the swap** — zero Camunda references in console source; they call domain verbs behind `/bpm`. They gate every console PR, so they are a **free regression net at the API boundary** ([§4a](#4a-the-consoles-are-insulated-from-this-change)) |

**687 files are touched, but the coupling is shallow.** It is almost all public API. `engine.delegate` alone accounts for **531 of the main-source imports**, and 813 across main and test together. That is exactly the profile an automated recipe handles well. [option-2.md §3](option-2.md) reached the same conclusion by a different route: only about 2,004 lines out of 497,970 actually touch an engine API.

**The Spring Boot 4 half, owed regardless of engine:**

| Driver | Detail |
|---|---|
| `@MockBean` → `@MockitoBean` | 308 occurrences across 186 files — the dominant mechanical change |
| Hibernate 6 → 7 | `hypersistence-utils-hibernate-63` → `-70`; 325 `JsonBinaryType` occurrences across 86 files, against 238 `@Entity` classes |
| ShedLock 4.42 → 7.9 | Three majors; 11 `@SchedulerLock` sites |
| **Remove the `spring-framework-bom` pin (6.2.19)** | Would silently fight Boot 4's own BOM — **the single most dangerous pin in `pom.xml`** |
| Spring Security 6 → 7, Spring Data 3 → 4, Tomcat 10.1 → 11 | Remove the explicit pins; let the Boot 4 BOM manage them |
| `springdoc-openapi` 2.8.11 → 3.1.1 | Major bump; its POM targets Boot 4 module names |
| `javax.*` leftovers | 4 files, trivial |

---

## 9. Rollback, and why it is unusually good

It rests on one fact: **both forks keep Camunda 7.24's database schema unchanged**, `ACT_` prefix included. Operaton seeds `ACT_GE_SCHEMA_LOG` with `7.24.0`, and it ends its upgrade chain at the same id, `1300`, that Camunda uses. Neither fork renumbers.

| Stage | Rollback | Notes |
|---|---|---|
| Pre-decision cleanup (§6) | Ordinary revert | No engine involvement |
| 7.24 bump (B1 only) | Redeploy the 7.23 artifact | Schema-log row is additive and harmless |
| Recipe run, pre-deploy | Discard the branch | No production impact |
| SIT / UAT | Redeploy previous artifact | Standard |
| **PROD cutover** | **Redeploy the previous artifact against the same database** | Viable *because no DDL runs*. This is the load-bearing claim and must be proven in the §7.3 rehearsal, not assumed |

**One thing does not roll back cleanly:** the schema-log reconciliation in §7.1, if it turns out to be necessary. Those inserted rows correct a real drift and should stay. Take a database backup immediately before.

**There is no point of no return at the database layer.** That is the unusual and welcome part. The practical point of no return is organisational. Once PROD has run on the new engine long enough to accumulate history, reverting means running an unpatched engine again. It is not a data problem.

### Cutover shape

> **A rolling restart, not a drain.** Draining is not available anyway. **96 `userTask` elements sit across 26 of the 53 BPMN files**, so instances park on human action indefinitely. In-flight instances resume because deployed BPMN re-parses from `ACT_GE_BYTEARRAY`. We verified at bytecode level that both forks register the legacy `camunda:` namespace alongside their own.

Two conditions attach. **Quiesce the job executor during the swap** — two engine versions competing for the same `ACT_RU_JOB` rows is the untested area. And **rehearse on a PROD clone first**.

Standard promotion is SIT → soak → UAT → soak → PROD. Run the §7.1 diagnostics separately against each environment, because their schema-log state may differ.

*(One counting nit, recorded for accuracy. The memo states 192 `userTask` elements. That is the open-plus-close tag count. The element count is **96**, across the 26 files the memo correctly identifies. The conclusion, that draining is unavailable, is unaffected.)*

---

## 10. What this option does and does not solve

**Solves:** the end-of-support finding, outright and cheaply. Bravo lands on a maintained engine and a supported Spring Boot in one change. There is no licence, **no data migration, no paradigm change and no retraining**. It also keeps everything the comparison found Bravo genuinely does better than LORA: bounded, classified failure handling with a designed dead-letter path; relational fleet queries; durable reprocess generations; an analyst-readable BPMN model; cheap version coexistence; commodity skills; and the cheapest orchestration tier of the three ([compare.md §5](compare.md)).

**Does not solve:**

- Five legacy per-product monoliths still carry **about 94% of production volume**. Over 90 days that is NDF2W 248,682, NDF4W 59,909 and NDF4W_RO 11,458 process starts, against the unified spine's 18,809 ([workflow-gap.md §8.1](workflow-gap.md)).
- Product identity is still a magic number in five places. Lifecycle state is still spread across 30 `ApplicationStatus` values, about 105 other status enums, and 197 `setStatus` call sites ([compare.md §3.3](compare.md)).
- There are no process metrics, no saga compensation and no per-product visibility. Only 4 of `ms-bpm`'s 1,457 tests exercise a process. (Bravo's estate has 2,286 test files across four repositories. The other 829 are console tests that never reach the engine.)
- **It does not answer the platform question** — it removes the deadline from it.

### What is lost or deferred

- **On Operaton only:** you lose the BPMN path-coverage HTML reports on four functional tests — `DMNFunctionalTest`, `UnsecuredLMSIntegrationFunctionalTest`, `AdvanceAIKYCActivityFunctionalTest` and `AntiFraudEngineCheckpointFunctionalTest`. Test *correctness* is unaffected. Only the coverage reporting goes. CIB seven ships the library and loses nothing.
- **Latent, on both paths:** the seven Cockpit plugin bundles are committed as **built artefacts whose TypeScript sources are not in this repository**. `rollup.config.mjs` references a `src/` directory that does not exist, and there is no `package.json`. They survive this migration untouched, because both forks preserve the plugin contract. They **cannot** survive a future change that alters it. Finding those sources is worth doing on its own merits.
- **Deferred deliberately:** Operaton's `webapp-neo` and CIB seven's `webclient` both ship *alongside* the classic webapp, so no action is needed now. Camunda 8 is a separate programme. Spring Boot 4.1 waits until a `spring-cloud` train targets it.

**Do not rename the environment variables** as part of this migration. `CAMUNDA_HISTORY_*` are BFI's own placeholders, not engine-defined. What matters is the deployed values. Touching the names multiplies what can go wrong at cutover, for no functional gain.

---

## 11. Risks

| Risk | Severity | Note |
|---|---|---|
| **Schema-log drift** (§7.1) | **High** | Startup failure at cutover if the label is below 7.22 while the columns exist. Strong inference, not yet verified. Diagnose per environment before committing a date |
| Two engine versions on one `ACT_RU_JOB` | High | The genuinely untested area. Quiesce the job executor; rehearse on a PROD clone |
| **Choosing a smaller-support project** | Medium–High | Six-month support lines and, for Operaton, no legal entity yet. This is a deliberate choice rather than drift, and will be scrutinised as such |
| Regression without a test net | Medium–High | 1,457 `ms-bpm` test files, but only 4 deploy and run a process. **Partly mitigated 2026-09-10:** the three consoles' 829 tests gate every PR and exercise the domain endpoints the engine sits behind, so UI-contract regressions at the boundary would be caught even though the engine itself would not be. The recipe is mechanical and the logic is untouched, which bounds this — but the orchestration layer remains unverified by CI |
| CIB seven support terms unknown | Medium | Not published; sales-contact only. Blocks the fork decision if the answer to §4's question is "yes" |
| Cockpit plugin sources missing | Medium | Survives this migration; blocks any future change to the plugin contract |
| Boot 4.1 unavailable | Low | `spring-cloud` Oakwood pins 4.0.8. A known, dated constraint rather than a surprise |
| **Does not remove the platform decision** | — | It removes the deadline, which is the point. See [option-summary.md](option-summary.md) |

---

## 12. Open questions

| # | Question | Blocks | Owner |
|---|---|---|---|
| 1 | Is a support agreement required, and is one purchasable for a BFI entity? | **The fork decision** | Architect / procurement |
| 2 | Are these six Cockpit capabilities in active use — historic activities on definitions and on instances, route history, auto-refresh, the bpmn-js robot module, the Tasklist audit log? | The fallback option of dropping the plugins | Operations |
| 3 | What does `ACT_GE_SCHEMA_LOG` report in SIT, UAT and PROD? | The cutover plan | Engineering — SQL in §7.1 |
| 4 | CIB seven's property prefix and webapp URL path | Accurate B2 estimate | Engineering — spike |
| 5 | What deployment window is actually available? | Cutover design | Release management |

**Question 1 is the critical path. Questions 3 and 4 are answerable in hours.**

---

## 13. When Option 1 is the right answer

Option 1 is now the right answer under a **much wider** set of beliefs than the earlier version of this document implied. It is no longer a licence purchase, and it is no longer 11–19 engineer-months.

- **If Bravo has any future at all beyond the next year** — it lands on a supported stack for ~1–1.5 engineer-months and stops the exposure. Nothing else in the pack does that at that price.
- **If the platform question is still open**, this is the option that buys the *right* to take that decision on its merits rather than under a security deadline. None of the work is wasted under Options 2 or 3. The Spring Boot 4 half, 12–20 of the 18–33 days, is owed under Option 2 as well, because the framework upgrade does not disappear when Camunda does.
- **If Bravo is strategic long-term** — it is the destination, not a way-station, and the fork question in §4 deserves the full weight described there.

There is one belief under which Option 1 is *not* enough: that Bravo's **architecture** is the problem — five monoliths, product identity in five places, four status vocabularies. Option 1 changes the runtime and keeps the architecture exactly as it is. That is a real limitation. It is the argument [option-2.md](option-2.md) and [option-3.md](option-3.md) exist to make.

**Recommended path: B, the combined one, with the fork subject to §4.** Sequencing does not let you defer the hard question. It only delays the benefit while paying the regression cost twice. And Path A still ends on an end-of-life Spring Boot, so it does not resolve the exposure that makes this urgent.

---

## Sources

- **[Camunda 7 Exit Plan](production-findings/Camunda%207%20Exit%20Plan.pdf)** — Bravo team decision memo, 2026-09-09. It is the substance of §2 to §9 above. We verified its version and artefact facts against `repo1.maven.org` directory listings and release-tag POMs. Project health came from the GitHub API. Schema and namespace behaviour came from extracting and inspecting the published engine and webapp jars. Repository counts were measured against the working tree
- Re-verification for this revision, 2026-09-10. We checked: 351 main and 336 test files importing `org.camunda`; 308 `@MockBean` across 186 files; both Flyway migration filenames and their exact DDL; `CollectionUtil` in exactly 2 files; 96 `userTask` elements across 26 of the 53 BPMN files; and Maven Central metadata for `org.operaton.bpm:operaton-engine` (2.1.4 GA), `org.cibseven.bpm:cibseven-engine` (2.2.0 GA) and both Spring Boot starters
- [SECURITY-FINDING-camunda-rce.md](SECURITY-FINDING-camunda-rce.md) — the live RCE exposure
- [compare.md](compare.md) — cost tier, capability comparison, where product and lifecycle logic live
- [workflow-gap.md §8](workflow-gap.md) — production volumes by root definition
- [Camunda 7 Community Edition End of Life](https://forum.camunda.io/t/important-update-camunda-7-community-edition-end-of-life-announced/50921) · [Spring Boot support timeline](https://endoflife.date/spring-boot)
