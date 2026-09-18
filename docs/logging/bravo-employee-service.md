# bravo-employee-service — logging findings and fixes

**Squad:** Internal Service  
**Production service:** `prod-ms-employee`  
**Stack:** Java, Spring Boot, RabbitMQ  
**Production volume:** 897,309 info, 10,202 error a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-employee` writes **897,309 info entries a week** — the second-largest info producer in the estate. Measured in Datadog over the 7 days to 13 September 2026.

Two log lines account for almost all of it, and **both print a complete employee record**.

`HCEmployeeListener@71`, on every inbound HC message:

```
Processing RabbitMQ Message from HC , Message : {"emp_no":…,"emp_name":…,
"dt_birthday":…,"religion":…,"marital_status":…,"place_of_birth":…,
"corporate_email":…,"personal_email":…,"mobile_phone_no":…,
"account_number":…,"account_name":…,"bank_name":…,"education":…,
"resign_reason":…,"leave_balance":…}
```

`RabbitMQPublisherServiceImpl@32` does the same on every outbound message. `GoogleChatCommandListener` does it a third time.

**Religion, marital status, date and place of birth, bank account number and holder name, personal email and mobile number** — at info level, roughly 900,000 times a week, retained for as long as the log index holds.

## What this PR changes

**New `JsonLogMaskUtil`.** Masks the personal fields of a payload, truncates to 2 KiB, and refuses to copy anything it cannot parse as JSON — it cannot tell which parts of such a payload are personal.

**All three call sites now log the size at info and the masked payload only under debug:**

```java
log.info("Processing RabbitMQ message from HC, {} chars", messageJson.length());
if (log.isDebugEnabled()) {
  log.debug("HC message payload: {}", JsonLogMaskUtil.mask(messageJson));
}
```

The identifiers a reader actually needs — message ID, exchange, size — stay at info. The record does not.

## Scope

This is a logging change only. No message handling, no business logic, no schema.

## Please build before merging

**Compiled and, where a suite exists, tested locally on 14 September 2026** — see the verification note under *Implementation status* below. Earlier versions of this paragraph said Java could not be built on this machine; a JDK and Maven were one `mise x` away, and that claim is withdrawn.

---

## In the production deployment

Read from `app-deployment/employee/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `LOGGING_LEVEL_ROOT` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE` | `INFO` |
| `LOGGING_LEVEL_ORG_HIBERNATE_SQL` | `info` |
| `LOGGING_LEVEL_ORG_HIBERNATE_TYPE_DESCRIPTOR_SQL` | `info` |
| `LOGGING_LEVEL_ORG_SPRINGFRAMEWORK_WEB_CLIENT_RESTTEMPLATE` | `INFO` |

This is a Java service that does **not** depend on `bravo-lib-logging`, so the library's `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` / `SENSITIVE_KEYS` switches do not apply here. The body logging this service does comes from its own filters and Feign loggers, described above, and the production levers in this file are the `LOGGING_LEVEL_*` variables in the table — Spring Boot reads each one as `logging.level.<package>`. Where the table is empty, the service's own `application*.yaml` decides. *(An earlier version of this paragraph described `bfi-go-pkg` defaults; that text was generated for Go services and never applied to this one.)*


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.14, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Adopting it means deleting `logback*.xml` and any hand-written `feign.Logger` bean, and telling SRE the manifest reads `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bravo-employee-service#172](https://github.com/bfi-finance/bravo-employee-service/pull/172)** — open, not merged.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-employee-service/tree/fix/logging), head `db62ca7`, branched from `master` at `99feb11`.

[Files changed](https://github.com/bfi-finance/bravo-employee-service/pull/172/files) · [Commits](https://github.com/bfi-finance/bravo-employee-service/pull/172/commits) · [Compare against master](https://github.com/bfi-finance/bravo-employee-service/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.14. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `logback*.xml` and any hand-written `feign.Logger` bean in the same change).

CI on the current head is red only on **`Codacy Coverage Variation`, `Codacy Diff Coverage`, `Security Container Scan`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 4 Codacy thread(s); 4 fixed in `b855c5d` (fix(logging): mask the payload in rejection messages; guard blank input; test the masker). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 4 |

Commits:

- fix(logging): stop writing whole HR records to the log stream

Files:

- `src/main/java/com/bfi/bravo/connector/GoogleChatCommandListener.java`
- `src/main/java/com/bfi/bravo/connector/HCEmployeeListener.java`
- `src/main/java/com/bfi/bravo/service/rabbitmq/publisher/impl/RabbitMQPublisherServiceImpl.java`
- `src/main/java/com/bfi/bravo/util/JsonLogMaskUtil.java`

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 176 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Run CI on the pull request — see the verification note above for what was and was not checked locally
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
