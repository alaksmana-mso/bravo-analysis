# bfi-incentive-api — logging findings and fixes

**Squad:** Agency  
**Production service:** `prod-ms-bfi-incentive-api`  
**Stack:** Java, Spring Boot, RabbitMQ, bravo-lib-logging  
**Production volume:** 281,659 info, 40,514 error, 28,909 warn a week

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## What production shows

`prod-ms-bfi-incentive-api` writes **281,659 info, 40,514 error and 28,909 warn** a week. Measured in Datadog over the 7 days to 13 September 2026.

The largest single error pattern — **653 a week** — is `AgreementStatusUpdateDailyConsumer` reporting a failed message, with the whole DTO interpolated into the message text:

```
[AgreementStatusUpdateDailyConsumer]Agreement status update daily consumer failed to
process message for: AgreementStatusUpdateResponse(status=LIVE, agreementNumber=…,
goLiveDate=…, firstInstallmentDate=…)
```

## Why that matters beyond tidiness

Because the message text differs on every occurrence, **these cannot be grouped into one pattern** and **no log query can match on the message**. You cannot count them, alert on them, or exclude them. The agreement number identifies the failure; the rest is already on the message that caused it.

```java
var agreementNumber = agreementStatusUpdate == null ? "unknown" : agreementStatusUpdate.getAgreementNumber();
LoggerUtil.logError(
  this.getClass(),
  "[AgreementStatusUpdateDailyConsumer] failed to process agreement " + agreementNumber,
  e
);
```

## CI caught a real defect in the first version of this change, and it is fixed

The first commit read the agreement number as `agreementStatusUpdate.getAgreementNumber()`
with no null check. `agreementStatusUpdate` is initialised to `null` and is **still null
whenever the failure was the deserialisation itself** — which is one of the main reasons
this catch block runs at all. The call threw a `NullPointerException` from inside the
catch, and that NPE escaped in place of the `AmqpRejectAndDontRequeueException` the
listener contract depends on. That changes what RabbitMQ does with the message, so it was
a behaviour regression, not only a test failure.

The repository's own test suite caught it:

```
AgreementStatusUpdateDailyConsumerTest.test_Receive_WhenException:197
  Unexpected exception type thrown
  ==> expected: <org.springframework.amqp.AmqpRejectAndDontRequeueException>
   but was: <java.lang.NullPointerException>
```

The first parameter case of that test is a null response. Fixed in commit
`2a738ed6` by reading the number null-safely, as shown above. This is the one defect
in the second pack that was mine and reached CI as a **test** failure rather than a
compile or lint failure.

## Not fixable here

The **second**-largest pattern, `Exception delivering confirm` at 542 a week, comes from Spring AMQP's own publisher-confirm machinery, not from this repository's code. It needs whoever owns the confirm callback.

## What I checked and left alone

`application-prod.yaml` sets `root: INFO` and `RestTemplate: INFO`. The `SQL: debug` and `RestTemplate: DEBUG` entries in this repo are all in `application-dev`, `-uat`, `-test` and `-local` profiles, which prod does not use. Nothing to change there — this repo's profile hygiene is good.

## What was and was not checked locally

**Compiled locally on 14 September 2026** (`mvn compile`, Temurin 17 via `mise`); the suite that caught the null dereference ran in CI — 1,806 tests, 0 failures on `2a738ed6`. Earlier versions of this paragraph said Java could not be built here; that was wrong.

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) Unit tests were not run for this repository locally; CI remains the authority for behaviour. Every changed file is also `prettier-java` clean at the repository's pinned settings.

**What could be checked, and now is:** `prettier-plugin-java` runs on Node, which *is*
available through `mise`. Every Java file this programme changed is now parsed and
format-checked with the same `prettier-java` version and `printWidth` the repositories
pin. This file parses and is prettier-clean. A parse check would not have caught the
null dereference — only the test suite could — but it does retire the hand-counting of
braces that earlier versions of these documents described.

---

## In the production deployment

Read from `bfi-app-deployment/bfi-incentive-api/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| Log level | `INFO` |
| `SENSITIVE_KEYS` | `password,secret,authorization,api-secret,nik,Set-Cookie` |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | `true` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It wires the library's `RequestLoggingFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.

---

## Implementation status

**Pull request: [bfi-incentive-api#1698](https://github.com/bfi-finance/bfi-incentive-api/pull/1698)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-incentive-api/tree/fix/logging), head `2a738ed6`, branched from `master` at `554a48b7`.

[Files changed](https://github.com/bfi-finance/bfi-incentive-api/pull/1698/files) · [Commits](https://github.com/bfi-finance/bfi-incentive-api/pull/1698/commits) · [Compare against master](https://github.com/bfi-finance/bfi-incentive-api/compare/master...fix/logging)

| | |
|---|---|
| Commits | 2 |
| Files changed | 1 |

Commits:

- fix(logging): give the consumer failure a stable message
- fix(logging): read the agreement number null-safely

Files:

- `src/main/java/id/co/bfi/bfiincentiveapi/messaging/consumer/AgreementStatusUpdateDailyConsumer.java`

**Compiled locally on 14 September 2026; CI ran the suite** — 1,806 tests, 0 failures on `2a738ed6`, after the null-dereference fix described above. The changed file is also `prettier-java` clean.

---

## Checklist

- [ ] Run CI on the pull request — the change is parsed and prettier-clean, but it was not compiled or unit-tested here
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
