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

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* What was checked: brace and paren balance on every touched file, line lengths against the prettier-java `printWidth` of 120, and imports placed in sorted order. That is not a build — please treat the CI result as the first real check.

---

## Implementation status

**Pull request: [bravo-employee-service#172](https://github.com/bfi-finance/bravo-employee-service/pull/172)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bravo-employee-service/tree/fix/logging), head `db62ca7`, branched from `master` at `99feb11`.

[Files changed](https://github.com/bfi-finance/bravo-employee-service/pull/172/files) · [Commits](https://github.com/bfi-finance/bravo-employee-service/pull/172/commits) · [Compare against master](https://github.com/bfi-finance/bravo-employee-service/compare/master...fix/logging)

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

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---|---|
| Commits | 1 |
| Files changed | 4 |

Commits:

- fix(logging): stop writing whole HR records to the log stream

Files:

- `src/main/java/com/bfi/bravo/connector/GoogleChatCommandListener.java`
- `src/main/java/com/bfi/bravo/connector/HCEmployeeListener.java`
- `src/main/java/com/bfi/bravo/service/rabbitmq/publisher/impl/RabbitMQPublisherServiceImpl.java`
- `src/main/java/com/bfi/bravo/util/JsonLogMaskUtil.java`

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
