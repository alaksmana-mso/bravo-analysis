# bfi-payment-api — logging fixes

**Squad:** Payment
**Production service:** `prod-ms-bfi-payment-api`
**Stack:** Java, Spring Boot

Nothing in this repo is misconfigured for production. Everything found is in non-production
profiles — which still costs **Rp 56.4M a month** estate-wide, so it is worth a pass.

---

## 1. Non-production profiles carry debug settings

| Setting | File | Value |
|---|---|---|
| `loggerLevel: FULL` ×2 | `application-dev.yaml` | full request/response bodies |
| `loggerLevel: FULL` ×3 | `application-local-standalone.yaml` | full request/response bodies |
| `show-sql: true` ×2 | `application-local-standalone.yaml` | every SQL statement |
| DEBUG/TRACE ×6 | `application-dev.yaml` | |
| DEBUG/TRACE ×4 | `application-local-standalone.yaml` | |

`application-prod.yaml` is clean. `application-local-standalone.yaml` runs on a developer's
machine and costs nothing.

**`application-dev.yaml` is the one that matters.** The dev environment runs in
`bravo-project-nonprod`, which bills Rp 56.4M a month for Cloud Logging — 21% of the whole
logging line. Full Feign bodies plus six debug levels on a payment service is a meaningful
share of that.

### Fix

In `application-dev.yaml`:

```yaml
feign:
  client:
    config:
      default:
        loggerLevel: basic
logging:
  level:
    root: INFO
```

Developers who need full bodies in dev can set an environment variable for the afternoon.
It should not be the committed default for a shared environment.

Leave `application-local-standalone.yaml` alone. It never leaves a laptop.

---

## 2. `CommonsRequestLoggingFilter` — dormant in prod

`src/main/java/id/co/bfi/bfipaymentapi/config/RequestLoggingFilterConfig.java` registers
the filter with payload logging and a 10 KB limit. Its logger sits at INFO in production,
so it emits nothing.

One more entry sits in `logback-backup.xml`, which is not loaded.

### Fix

Same as elsewhere: `setIncludePayload(false)`, or `@Profile("local")` on the bean, and pin
the level in `application-prod.yaml`. Payment request bodies carry account and amount data.

---

## 3. 27 `System.out.print` — all in tests

`src/test/java/id/co/bfi/bfipaymentapi/utils/PaymentPointGroupBillingUtilsUserScenarioTest.java`
has all 27.

They do not ship. Worth replacing with assertions on principle — a test that prints instead
of asserting is not testing much — but this is not a logging cost item.

---

## 4. What this is worth

| Item | Saving / month | Confidence |
|---|---:|---|
| 1 — dev profile debug and Feign full | Rp 2–5M | medium, part of the non-prod line |
| 2 — dormant payload filter | Rp 0 today | risk removal |

---

## Request and response bodies in Datadog

No Datadog tracer, in any language, has a supported setting that puts an HTTP body on a
span. Squads work around that by logging bodies. **This repo is the one that handles it
correctly, and it should be cited as the pattern when other squads are asked to change.**

| | Seven days, production |
|---|---:|
| Spans | 669,038 |
| Log entries | 70,880 |
| Entries carrying a captured body | 0 |

### Why it is right

`RequestLoggingFilterConfig` declares two beans, not one:

```java
@Bean @Profile("!prod")   // payload and headers included
@Bean @Profile({ "prod" }) // setIncludePayload(false), setIncludeHeaders(false)
```

and `FeignLoggingInterceptor`, which sets `Logger.Level.FULL`, is `@Profile("!prod")`
throughout. Developers get full bodies where they need them and production gets none. That
is the shape every other Java repo in this pack should end up in.

### The consequence, which is the point

Because it is right, this squad has **no body visibility in production at all**. When a
BCA VA or SNAP-BI call misbehaves in prod, there is nothing to look at beyond status and
duration. That is exactly the gap the other squads filled with always-on logging — so this
squad has the strongest claim on the replacement, not the weakest.

### What the replacement is

Java services can use **method probes** in Datadog's Live Debugger: name a method, capture
its arguments and return value from the running pod, then remove the probe. No redeploy, no
always-on logging, nothing left running.

It needs Remote Configuration, and Remote Configuration is failing on this service more than
on any other: **679 failed polls in two days**, `unexpected response code Internal Server
Error 500 ... empty targets meta in director local store`. Thirteen production services
report the same error.

### What to do

1. Nothing to remove. Do not "tidy up" the two-bean arrangement — it is the fix, not a
   leftover.
2. Ask SRE for the Remote Configuration fix. This service is the best pilot candidate:
   highest failure count, cleanest logging, and a real unmet need.
3. Ask SRE for `DD_TRACE_HEADER_TAGS` so correlation ids land on spans. For a payment
   gateway that answers a large share of "which call was this" questions on its own.
4. Where a field is needed on every request rather than during a debugging session, put it
   on the span:

   ```java
   final Span span = GlobalTracer.get().activeSpan();
   if (span != null) {
     span.setTag("payment.partner_ref", partnerReference);
     span.setTag("payment.va_number_masked", maskedVa);
   }
   ```

---

## Why did validation fail? Answering the customer without logging the payload

The same question the Scoring and Underwriting reviewer asked on `bravo-bpm-service#10463` applies
here: when a request is rejected and the customer asks why, the engineer reads the payload in the
log because nothing else says. The estate-level answer is in
[bravo-bpm-service.md](bravo-bpm-service.md#why-did-validation-fail-answering-the-customer-without-logging-the-payload):
**log the decision, return the reference, keep the data in the database.** This section is what
that means for this service, read from the code on `fix/logging` and seven days of production
logs on 23 September 2026.

### What happens today when a request is rejected

| How the request fails | Caller gets | Log says |
|---|---|---|
| Bean validation (`@Valid` on 27 of 156 request bodies) | Boot's default body, no field list — no handler exists in any of the eight advice classes | Spring's own WARN `Resolved [… rejected value [...]]` |
| Unreadable body | 400 with the message; the enum case echoes the invalid value; the BRI partner handler answers **500** `UNEXPECTED_ERROR` | nothing |
| Business rule via `BusinessException` (about 80 partner-specific classes: `TransferErrorException` 34 sites, `AccountInquiryErrorException` 32, `BillNotFoundBriException` 19, `TokopediaException` 15, `GotoException` 14, …) | the exception's status with `cause`, `message`, `code`, `reason` | **nothing** in `GlobalExceptionHandler`; only the CentralPaymentPoint handler (WARN) and the Jago handler (ERROR) log |
| `PaymentPointException`, `BillNotFoundException`, `OnlinePaymentTransactionException` (20 sites, no handler, no `@ResponseStatus`) | **500** | Spring's WARN |
| `AccessDeniedException` (payment-point handler) | **401**, should be 403 | nothing |

Production, seven days: 73,520 warn, 16,986 error. Among the warn lines: the BCA account-inquiry
400s, logged with the **raw partner response including the beneficiary account number**.

### The gaps

1. No decision line, and eight handler classes that each do a little of the job.
2. The reference never returns: `CorrelationIdFilter` reads `X-Correlation-Id` into the MDC and
   sets no header; `BaseJsonErrorResponseDto` has no id field. For the BCA virtual-account flow
   the service *does* create a reference — the `HostToHostVaNotificationLog` row id, saved in the
   auth filter before processing, kept as `X-Internal-Log-Id` on the request — and never returns it.
3. Two handler bugs seen in passing: `@ExceptionHandler(ParsingException.class)` on a method
   whose parameter is `HandleDatabaseErrorException` (never matches, falls to 500), and
   `AccessDeniedException` mapped to 401.
4. `application-prod.yaml` is an empty file, so every production level and switch comes from
   the manifest.

### The best practice for this service

1. **One decision line in `GlobalExceptionHandler`**, WARN, for every `BusinessException` and a
   new `MethodArgumentNotValidException` handler with the field list: route, status, `code`,
   the partner (`bca`, `bri`, `doku`, `goto`, `tokopedia`, `jago`), the partner reference number
   and the virtual-account or bill id — never the account number. Keep ERROR and the stack for
   the true 500 branch. Give the twenty unhandled rule sites a status.
2. **Return the reference.** `setHeader` in `CorrelationIdFilter` plus a field on
   `BaseJsonErrorResponseDto`. For the virtual-account flow, return the existing internal log id
   as well; it already points at the stored request.
3. **The input is already persisted before processing** for the flows that matter:
   `HostToHostVaNotificationLog` (saved in the auth filter), `PaymentPointLogTransaction` and
   its Goto and Tokopedia variants, `HostToHostJagoCallbackTransactionLog`,
   `AutoDebitTransactionLog`, `AccountValidationLog`. That is the pattern this write-up asks
   for; the rows hold reference numbers and response codes, not raw payloads, which is right.
4. **Take the account number out of the partner-error lines.** The BCA `Invalid Field Format
   beneficiaryAccountNo` line prints the raw response twice; log the response code and the
   partner reference only.
5. **Fix the two handler bugs** and the BRI 500-for-bad-input while there.

### Runbook: a customer asks why a payment was refused

1. Get the reference (once step 2 ships) or the partner reference number and time.
2. `service:prod-ms-bfi-payment-api @event:request_rejected @partner_reference:<n>`.
3. For the data, the transaction log row for that partner and reference.

---

## Service identity in Datadog

Measured over seven days to 12 September 2026, production.

| | Name | Volume |
|---|---|---:|
| Traces | `prod-ms-bfi-payment-api` | 663,598 spans |
| Logs | `prod-ms-bfi-payment-api` | 70,100 entries |

**The names match.** Nothing to fix here today.

Keep it that way. The mismatch happens when someone changes the Kubernetes deployment name
without changing `DD_SERVICE`, or the other way round. Eight production services are split
across two identities right now for exactly that reason. The unified tagging block below
removes the possibility.

### How to fix it

The service name on a **log** comes from the Kubernetes container and deployment name, or
from a Datadog Agent annotation. The service name on a **trace** comes from `DD_prod-ms-bfi-payment-api`, or
from whatever the tracer was initialised with in code. Nothing makes those two agree. When
they differ, Datadog builds two entities from one workload, and every dashboard, monitor and
Service Catalog entry silently covers half of it.

The fix is to stop setting the name in two places. Put the Datadog unified tagging labels on
the **pod template**, and the Agent applies the same identity to logs, traces, metrics and
profiles together:

```yaml
# deployment.yaml -> spec.template.metadata.labels
tags.datadoghq.com/env: "prod"
tags.datadoghq.com/service: "prod-ms-bfi-payment-api"
tags.datadoghq.com/version: "{{ .Values.image.tag }}"
```

Then set the matching environment variables on the container, sourced from those same
labels so they cannot drift:

```yaml
env:
  - name: DD_ENV
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/env'] } }
  - name: DD_prod-ms-bfi-payment-api
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/service'] } }
  - name: DD_VERSION
    valueFrom: { fieldRef: { fieldPath: metadata.labels['tags.datadoghq.com/version'] } }
```

These files live in `bfi-finance/app-deployment` (`bfi-app-deployment` for the `bfi-*-api` services), not here — SRE-owned, and read for this service on 14 September 2026; what they set is under *In the production deployment* below. This repo deploys through
`bfi-finance/bfi-base-template`, which **104 of the 152 repos share** — so this is worth
raising as one change to the shared template rather than 104 separate pull requests. Ask the
Platform team before opening anything.

If the tracer is initialised in code, remove the hardcoded name so `DD_prod-ms-bfi-payment-api` is the only
source. In Node.js that means `tracer.init({})` rather than
`tracer.init({ service: "..." })`; in Spring Boot, drop `dd.service` from `JAVA_OPTS`.

### How to check your own service

Two searches, one minute. Run both in the Datadog **us5** org.

```
# Logs Explorer
service:prod-ms-bfi-payment-api env:prod

# APM Traces
service:prod-ms-bfi-payment-api env:prod
```

If one returns nothing and the other returns plenty, you have either a name mismatch or a
collection gap — not an empty service. Widen the log search to `kube_deployment:prod-ms-bfi-payment-api` to
tell the two apart: results there mean the logs are arriving under a different service name.

---

## In the production deployment

Read from `bfi-app-deployment/bfi-payment-api/values-prod.yaml` on 14 September 2026. **This is what the running service actually uses** — a struct default in the code only applies when the variable is absent here, and where a variable is set to `""` the default never applies at all.

| Setting | Production value |
|---|---|
| `SENSITIVE_KEYS` | not set  ← library default (6 keys) |
| `REQUEST_BODY_LOGGING` | not set  ← library default `true` |
| `RESPONSE_BODY_LOGGING` | not set  ← library default `true` |
| `BODY_LOG_MAX_LENGTH` | not set  ← new in bfi-java-pkg#123, default 16384 |

This is a Java service on `bravo-lib-logging` (`bfi-java-pkg`). It does not wire the library's `RequestLoggingFilter`, and `REQUEST_BODY_LOGGING` / `RESPONSE_BODY_LOGGING` default to **`true`** in the library — so where they are not set here, every request and response body is logged at INFO. `SENSITIVE_KEYS` defaults to six keys (`password`, `token`, `secret`, `key`, `authorization`, `api-secret`); until [bfi-java-pkg#123](https://github.com/bfi-finance/bfi-java-pkg/pull/123) ships, the match is case-sensitive and `FeignClientFilter` masks nothing.


**Which Java wrapper applies here (17 September 2026).** This repository is on Spring Boot 3.5.15, so its target is `bfi-logging-spring-boot-starter` ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122), **merged 16 September 2026**): single-line JSON, an 8 KB message cap, request logging off by default, Feign bodies opt-in and never headers. It is not published yet — Platform must run `bfi-java-pkg`'s manual *Deploy Package* workflow for `logging-core` and then `logging-starter` before any `pom.xml` can name it. Migrating off `bravo-lib-logging` means deleting the `logback*.xml` files and the manual filter beans, and telling SRE that the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`.
---

## Implementation status

**Pull request: [bfi-payment-api#1650](https://github.com/bfi-finance/bfi-payment-api/pull/1650)** — open, not merged.
Branch: [`fix/logging`](https://github.com/bfi-finance/bfi-payment-api/tree/fix/logging), head `d6defb9c`, branched from `master`.

[Files changed](https://github.com/bfi-finance/bfi-payment-api/pull/1650/files) · [Commits](https://github.com/bfi-finance/bfi-payment-api/pull/1650/commits) · [Compare against master](https://github.com/bfi-finance/bfi-payment-api/compare/master...fix/logging)

**Update, 17 September 2026 — where this pull request fits now.**

This repository is on Spring Boot 3.5.15. The shared Java logging library it should move to, `bfi-logging-spring-boot-starter`, **merged on 16 September** ([bfi-java-pkg#122](https://github.com/bfi-finance/bfi-java-pkg/pull/122)): single-line JSON, an 8 KB message cap, request logging off by default, one masked line per Feign call and never a header. It is not yet published — `bfi-java-pkg` releases a module only through a manual *Deploy Package* run, which has not happened for the new modules — so the dependency cannot be added yet. **This pull request stands as the in-service fix until then**, and nothing in it has to be undone when the starter arrives (delete `bravo-lib-logging`, its filter beans and `logback*.xml` in the same change; the manifest's `LOGGER_LEVEL` / `SENSITIVE_KEYS` become `LOG_LEVEL` / `LOG_SENSITIVE_KEYS`).

CI on the current head is red only on **`Security Container Scan`, `Static Analysis - SonarQube`** — gates that were red on `master` before this branch (dependency and image CVEs, SonarQube new-code baselines, a Codacy token the runner lacks); nothing written here fails.

**Codacy review, answered 18 September 2026.** 2 Codacy thread(s); 2 fixed in `678dd64f` (style(feign): BASIC in the enum casing). Every thread is replied to and resolved on the pull request.

| | |
|---|---|
| Commits | 1 |
| Files changed | 1 |

Commit:

- chore(logging): stop the dev profile defaulting to debug and full Feign bodies

Files:

- `src/main/resources/application-dev.yaml`

**No Java changed on this branch — the change is to `application*.yaml`, which parses as valid YAML.** There is nothing to compile; the file is what Spring reads at start-up. (Earlier versions of this note said Java could not be built here; it can, and every Java branch in this programme now has been.)

---

## Checklist

- [ ] Change `loggerLevel: FULL` to `basic` in `application-dev.yaml`
- [ ] Lower the six DEBUG/TRACE entries in `application-dev.yaml` to INFO
- [ ] Leave `application-local-standalone.yaml` as it is
- [ ] Set `setIncludePayload(false)` or move the filter bean behind `@Profile("local")`
- [ ] Replace the 27 `System.out.print` in the scenario test with assertions
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Leave the two-bean `RequestLoggingFilterConfig` alone — it is the pattern, not a leftover
- [ ] Volunteer this service as the Live Debugger pilot: cleanest logging, highest Remote Configuration failure count
- [ ] Ask SRE for `DD_TRACE_HEADER_TAGS` so partner correlation ids land on spans
- [ ] One WARN `request_rejected` line in `GlobalExceptionHandler` for every `BusinessException`; add a `MethodArgumentNotValidException` handler with the field list; give the 20 unhandled rule sites a status
- [ ] Write `X-Correlation-Id` back and put it (and the VA internal log id) on `BaseJsonErrorResponseDto`
- [ ] Log partner error responses as code and reference, not the raw body with the account number
- [ ] Fix the `ParsingException` handler signature and the 401-for-`AccessDeniedException` mapping
