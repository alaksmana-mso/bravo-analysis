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

**This was not compiled and not tested, and for a Java repository that is still true.** There is no Maven and no JVM on the machine it was written on — `/usr/bin/java` is the macOS stub with no runtime. *(An earlier version of this file also claimed no Go or Node toolchain; both turned out to be available through `mise`, and the Go changes in this programme have since been compiled and linted.)* Brace balance was checked and no line over the prettier-java `printWidth` of 120 was added.

---

## Implementation status

**Pull request: [bfi-connect#788](https://github.com/bfi-finance/bfi-connect/pull/788)** — open.  
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-connect/tree/fix/logging), head `691f3dff`, branched from `master` at `9d4c47ea`.

[Files changed](https://github.com/bfi-finance/bfi-connect/pull/788/files) · [Commits](https://github.com/bfi-finance/bfi-connect/pull/788/commits) · [Compare against master](https://github.com/bfi-finance/bfi-connect/compare/master...fix/logging)

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commits:

- fix(logging): stop logging customer phone numbers on every duplicate-check miss

Files:

- `src/main/java/id/co/bfi/bficonnect/service/impl/DuplicateCheckServiceImpl.java`

**Nothing in this pull request was compiled or tested.** There is no Maven and no JVM on the machine this analysis ran on — `/usr/bin/java` is the
macOS stub with no runtime — so this Java change was reviewed by reading only. (Go and
Node turned out to be available through `mise`, and the Go changes in this programme have
since been compiled and linted; Java cannot be built here.) CI on the pull
request is the first real check — do not merge on the strength of this
document.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
