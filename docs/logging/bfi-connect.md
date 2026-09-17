# bfi-connect — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-ms-bfi-connect`  
**Stack:** Java, Spring Boot, Feign, RabbitMQ  
**Production volume:** 6,608 warn, 5 info, 4 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-bfi-connect` writes **6,608 warn entries a week** (against 5 info and 4 error), and almost all of them are one line from `DuplicateCheckServiceImpl`:

```
Duplicate check asset salestrax for mobile phone 628…, customerId …,
productCategory …, licensePlate …, statusData … : 400
{"header":{"errors":[{"message":"Data Not Found","cause":"Data Not Found","code":"400"}]},"data":null}
```

Measured in Datadog over the 7 days to 13 September 2026.

## Two things are wrong with it

**The level.** A 400 from salestrax means "Data Not Found" — the expected answer to a duplicate check that finds nothing. The very next line in the method already treats a 400 as the normal path:

```java
if (errorStatus != HttpStatus.BAD_REQUEST.value()) {
    // only now build an error response
```

The log statement simply ran *before* that distinction was made. It is now made first: **400 at debug, anything else at warn.**

**The content.** It carried the customer's **mobile phone number, customer ID and licence plate** in the message, 6,608 times a week. Those identifiers are gone from both the warn and the debug line. `productCategory` and `statusData` are enough to say which check it was.

The success-path `log.debug` in the same method printed the same identifiers plus the whole response. Same treatment — debug is off in production, but the default should be right on its own.

## What I checked and deliberately left alone

Nothing else in this repository needed changing, and that is worth saying plainly:

- `RequestLoggingFilterConfig` is **correctly profile-gated** — `setIncludePayload(true)` for dev, sit and uat; `false` for prod. Most of the estate does not do this.
- `application-prod.yaml` sets Feign to `basic` and `RestTemplate` to `WARN`.
- `loggerLevel: full` appears only in `application-test.yaml` and `application-unit-test.yaml`.

This is the pattern the rest of the estate should copy.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/bfi-connect/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_ID_CO_BFI_BFICONNECT_API_CLIENT` | `INFO` |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.9, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bfi-connect#788](https://github.com/bfi-finance/bfi-connect/pull/788)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-connect/tree/fix/logging), head `691f3dff`, branched from `master` at `9d4c47ea`.

[Files changed](https://github.com/bfi-finance/bfi-connect/pull/788/files) · [Commits](https://github.com/bfi-finance/bfi-connect/pull/788/commits) · [Compare against master](https://github.com/bfi-finance/bfi-connect/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.9. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

CI on the current head is red only on **`Lint and Style Check Code - Maven/Prettier`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): stop logging customer phone numbers on every duplicate-check miss

Files:

- `src/main/java/id/co/bfi/bficonnect/service/impl/DuplicateCheckServiceImpl.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 0 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
