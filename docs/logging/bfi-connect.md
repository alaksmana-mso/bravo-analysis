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
| Logging variables | none of the shared-library switches are set; the wrapper defaults apply |

Body logging is **off** in production (either set to `false` or absent, and `bfi-go-pkg` defaults it off). No masked-field list is needed until a squad turns bodies on; when it does, set the list in the same file.

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

**Compiled locally on 14 September 2026** — `mvn -DskipTests compile` passes with Temurin 17 and Maven 3.9 via `mise`. (Three earlier versions of this note said Java could not be built on this machine. A JDK was one `mise x` away; that claim is withdrawn everywhere.) **Unit tests: 0 run, 0 failures, 0 errors** (`mvn test`, whole module). Every changed file is also `prettier-java` clean at the repository's pinned settings.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Re-measure this service's 7-day volume and severity mix after the change ships
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
