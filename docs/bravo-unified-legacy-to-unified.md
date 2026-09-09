# Moving NDF4W and NDF2W from the legacy monoliths to the unified workflow

High-level, step-by-step of what it takes to migrate Bravo's two legacy per-product monoliths (`NDF4W`, `NDF2W`) onto `Unified_Process_Main_Workflow`. Companion to `workflow-analysis.md` and `workflow-gap.md`. Evidence from `bravo-bpm-service` and the production `ms-bpm` database, 2026-09-09.

## 1. The headline: more of this is already done than it looks

Two facts from the database change the shape of this migration:

- **The unified configuration for both products already exists.** The selector types `OPTION_NDF4W` and `OPTION_NDF2W` are seeded in `workflow_selector_type`, with master configs per customer and risk type (NDF4W 6, NDF2W 16), and NDF2W-specific scoring activities (`CollateralVerification`, `FatalScore`, `SimpleSurvey`) are already active for `OPTION_NDF2W`. NDF4W has even run in production on the spine — 4 "company" applications went through `Unified_Process_Main_Workflow` as `OPTION_NDF4W`.
- **Most domain activities already have unified equivalents.** By name, 31 of 71 NDF4W delegate beans and 25 of 74 NDF2W beans already exist as `*UnifiedActivity` classes (KYC, Pefindo, RAC, PD model, anti-fraud, dedupe, create-CIF, operation). The remainder are the long tail of product-specific variants.

So this is not a green-field rebuild. It is **completing a partial port and then moving live traffic across safely** — and the "safely" is the hard part, because NDF2W alone starts ~248,000 process instances every 90 days.

## 2. What is genuinely missing

The gap is the product-specific long tail, roughly 40 NDF4W and 49 NDF2W delegates with no unified equivalent today. It clusters into:

- **PD-model variants** — NTB/NTC, RO-tele, partnership, pre-overlay (many `PDModel*2wActivity` classes).
- **Legacy scoring and profile activities** — Asliri, iziData, one-obligor, Shopee, income/ATP/WTP calculations, retrieve-Pefindo-profile variants.
- **Channel and RO specifics** — Pallav customer creation, RO same-asset, RO-digital operation assignment, forced-survey and survey-type flags.
- **The human flows** — survey, negotiation, document pickup, and the underwriting/operation user tasks, which in the monoliths are deeply branched by risk tier.

## 3. Step-by-step (high level)

```mermaid
flowchart TB
  classDef s fill:#DDEBF1,stroke:#1F6F8B,color:#12252D
  S1["1. Gap inventory per product<br/>legacy delegates vs unified activities"]:::s --> S2["2. Port the long-tail activities<br/>as config-gated *UnifiedActivity"]:::s
  S2 --> S3["3. Complete DB config per risk/customer tier<br/>OPTION_NDF4W / OPTION_NDF2W"]:::s
  S3 --> S4["4. Shadow / parallel run<br/>unified vs legacy on same inputs"]:::s
  S4 --> S5["5. Cut over by tier, low-risk & low-volume first<br/>feature-flag routing"]:::s
  S5 --> S6["6. Ramp to full volume, watch SLA & rewind"]:::s
  S6 --> S7["7. Decommission NDF4W / NDF2W BPMN + dead map keys"]:::s
```

1. **Gap inventory per product.** Turn the name-match analysis into an exact list: every legacy delegate mapped to an existing unified activity, a required new one, or "drop" (dead/duplicate). This is the backlog.
2. **Port the long-tail activities.** Implement the missing beans as `*UnifiedActivity` classes extending `BaseActivity`, so they participate in the config-skip mechanism. Favour merging near-duplicate legacy variants (for example the many PD-model variants) into fewer parameterised activities rather than porting one-for-one.
3. **Complete the DB configuration.** Fill `workflow_selector_order` and `workflow_master_config_detail` for every NDF4W and NDF2W customer-type and risk-type combination, so the spine reproduces each tier's real path. Start from the seeded configs that already exist.
4. **Shadow / parallel run.** Drive real applications through both the legacy monolith and the unified spine and diff the outcomes (decisions, statuses, assignments, documents). This is the critical safety gate given the volume; the config-skip design means a missing row silently drops a check, so parity must be proven, not assumed.
5. **Cut over by tier.** Route the safest, lowest-volume segment first (for example NDF4W company, already piloted; then low-risk new-customer), behind the existing workflow-routing flags. Keep the legacy process warm for rollback.
6. **Ramp to full volume.** Move risk tiers across one at a time, watching SLA, stuck-instance and human-task-queue metrics. NDF2W's survey and follow-up queues are the highest-volume human work in the estate and the most likely to surface load problems.
7. **Decommission.** Once a product runs entirely on the spine, retire its legacy BPMN, remove the dead `setting.workflow.map` entries, and delete the unreferenced `Process_NDF4W_Scoring_1_Mock_Ro`.

## 4. Effort shape and risks

- **Effort is concentrated in steps 2 and 4**, not the spine. The orchestration is done; the work is the activity long tail and, above all, proving parity at scale.
- **NDF2W is the harder of the two**: more product-specific delegates (49 vs 40), far higher volume (248k vs 60k instances/90d), and more risk tiers (16 master configs vs 6). Do NDF4W first to build confidence, then NDF2W.
- **The config-skip trap.** Because an unconfigured activity no-ops silently, the migration's main risk is a missing config row removing a credit or compliance check without failing. Parallel-run diffing and a "fail loud on missing config" guard are the mitigations.
- **RO and channel variants** (RO same-asset, Pallav, RO-digital) are the messiest legacy corners and the least reusable; scope them as their own workstream, or decide some low-volume variants stay on legacy until last.
- **Do not migrate onto a spine you cannot see per product.** The visibility gap in `workflow-gap.md` (no per-product diagram, product logic split across config, Java `isXxx()` branches, and gateways) should be addressed in parallel, or the migrated products become hard to operate.
