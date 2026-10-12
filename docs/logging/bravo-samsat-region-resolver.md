# bravo-samsat-region-resolver — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-ms-rule-engine`  
**Stack:** Go, zerolog, bfi-go-pkg  
**Production volume:** not production-active under this name

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**Not production-active, and my earlier mapping of it was wrong.**

`coverage.md` listed this repository against `prod-ms-rule-engine`. Datadog's `git.repository_url` tag on that service says it is built from **`bfi-rule-engine-service`**, which is covered separately in this pack.

This repository does not correspond to any service emitting telemetry in production. No change, and no pull request.

---

## One request id across services

**Decided 12 October 2026.** Every request keeps one id, the gateway's `x-bfi-req-id`, from the client through every service it touches, in logs, on the span (`request_id`) and in the error body. The strategy, the three pull requests and the team-by-team list are on the main page: [One request id across services](README.md#one-request-id-across-services-x-bfi-req-id). This is what it means for this repository.

This service serves gRPC behind the wrapper's REST proxy. Today the proxy drops the gateway's `x-bfi-req-id` (the service does not whitelist it, and none does), so `loggerinterceptor` mints a second id and the id a client holds is not the id in these logs. The bfi-go-pkg release with #185 fixes that inside the proxy; the service only bumps. After the bump the id is on the span as `request_id`, and outgoing HTTP calls through `httpclient` forward it automatically.

What is left for the squad after the bump:

- **gRPC dials** (1 file): add `grpc.WithChainUnaryInterceptor(loggerinterceptor.UnaryClient())` to the dial options; the wrapper cannot do this for a `grpc.NewClient` call.
- **Error bodies:** opt in with `errorinterceptor.WithRequestInfoDetail()` and `panicinterceptor.WithRequestInfoDetail()` once the squad has checked that no caller rejects an unknown `@type` in the error details. The REST proxy renders the same detail for REST callers.

## Implementation status

**No pull request, and none needed.** No branch was created for this repository.
See the findings above for why.

---

## Checklist

- [ ] Confirm the conclusion above with the squad that owns this service
- [ ] Correct any other document that maps this repository to a production service
- [ ] Move service identity to `tags.datadoghq.com/*` labels on the pod template so logs and traces cannot drift apart
- [ ] Fix Remote Configuration before expecting Live Debugger or any UI-driven tracer change to work — see [sre-datadog-recommendations.md](sre-datadog-recommendations.md) §2.5b

---

Part of the logging and Datadog cost review. Index: [README.md](README.md) · Coverage: [coverage.md](coverage.md) · Estate-level body visibility: [body-visibility.md](body-visibility.md)
