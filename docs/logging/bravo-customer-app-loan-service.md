# bravo-customer-app-loan-service — logging findings and fixes

**Squad:** not filed under a squad folder — cloned into `squads/others/` by this review  
**Production service:** `prod-ms-kyc-proxy`  
**Stack:** Go, zerolog, bfi-go-pkg  
**Production volume:** not production-active under this name

Measured in Datadog over the 7 days to 13 September 2026, unless stated otherwise.

---

## Findings

**Not production-active, and my earlier mapping of it was wrong.**

`coverage.md` listed this repository against `prod-ms-kyc-proxy`. Datadog's `git.repository_url` tag on that service says it is built from **`bravo-kyc-proxy`**, which is covered separately in this pack.

This repository — ten Go files — does not correspond to any service emitting telemetry in production. No change, and no pull request.

---

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
