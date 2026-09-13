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
"[AgreementStatusUpdateDailyConsumer] failed to process agreement " +
agreementStatusUpdate.getAgreementNumber(),
```

## Not fixable here

The **second**-largest pattern, `Exception delivering confirm` at 542 a week, comes from Spring AMQP's own publisher-confirm machinery, not from this repository's code. It needs whoever owns the confirm callback.

## What I checked and left alone

`application-prod.yaml` sets `root: INFO` and `RestTemplate: INFO`. The `SQL: debug` and `RestTemplate: DEBUG` entries in this repo are all in `application-dev`, `-uat`, `-test` and `-local` profiles, which prod does not use. Nothing to change there — this repo's profile hygiene is good.

## Please build before merging

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* The concatenation was pre-wrapped by hand to stay inside the prettier-java `printWidth` of 120.

---

## Implementation status

**Pull request: [bfi-incentive-api#1698](https://github.com/bfi-finance/bfi-incentive-api/pull/1698)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-incentive-api/tree/fix/logging), head `888bd196`, branched from `master` at `554a48b7`.

[Files changed](https://github.com/bfi-finance/bfi-incentive-api/pull/1698/files) · [Commits](https://github.com/bfi-finance/bfi-incentive-api/pull/1698/commits) · [Compare against master](https://github.com/bfi-finance/bfi-incentive-api/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): give the consumer failure a stable message

Files:

- `src/main/java/id/co/bfi/bfiincentiveapi/messaging/consumer/AgreementStatusUpdateDailyConsumer.java`

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): give the consumer failure a stable message

Files:

- `src/main/java/id/co/bfi/bfiincentiveapi/messaging/consumer/AgreementStatusUpdateDailyConsumer.java`

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---

## Checklist

- [ ] Run CI on the pull request — nothing here was compiled or tested
- [ ] Review the change with the squad that owns this service
- [ ] Confirm the deployment manifest does not override the defaults this change sets
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
