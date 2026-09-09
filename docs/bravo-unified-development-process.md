# How fast does the Bravo unified workflow let a new product ship?

A read on the unified workflow's quality through the lens of delivery speed: comparing DF4W (the product that built the spine) with DF2W (the product that reused it). Evidence from git history of `bravo-bpm-service`, the D2W and DF Jira projects, and the production `ms-bpm` database, read 2026-09-09.

Jira boards: DF2W timeline `D2W` board 2877, DF4W timeline `DF` board 2099. Cycle-time and volume figures below are from a 200-issue sample per program (the most recent pages of each project's child issues) plus full production counts from the application table.

## 1. Verdict

**The unified workflow's central claim — that the second product onto the spine is far cheaper than the first — holds in the data.** DF4W was the pathfinder: it effectively built the unified generation (the `refactor-workflow` work of 2024) and took about seven months from workflow setup to first production loan. DF2W came a year later, reused the same spine and most of the same domain children, and its workflow layer was a small database-config delta plus a handful of new activities; its build effort went almost entirely into product-specific concerns (2-wheel insurance, calculation, the Sharia variant), not workflow plumbing.

The caveat: DF2W is **not yet in production** (zero applications in the database as of 2026-09-09), so the comparison is "time to build" not "time to a proven live product". And DF4W itself, at ~6,500 applications a month, is still only 5.5% of Bravo's volume, so neither DF product has yet been stress-tested at the scale of the legacy monoliths.

## 2. DF4W — the pathfinder that built the spine

| Milestone | Date | Source |
|---|---|---|
| `refactor-workflow` / unified prefix introduced | 2024-03-05 | git `chore(refactor): add prefix unified` |
| DF4W workflow config set up | 2024-07-12 | git `feat(df4w): setup workflow` |
| Heavy build phase | 2024-09 to 2024-12 | 154 DF4W-tagged commits; BLOSCS build issues median cycle 11 days |
| First production application | 2025-02-07 | application table, product_id 4 |
| Ramp to 1,000/month | 2025-10 | 1,101 applications |
| Ramp to steady state | 2026-07 | 6,546 applications/month |

DF4W's build issues were small and fast (median 11 days, p75 18, p90 26), which is the signature of a team building many small activities and config rows rather than wrestling one large workflow. But the elapsed calendar cost was real: **about 7 months from workflow setup to first production loan, and ~11 months to reach 1,000 loans a month.** That time bought the platform: the orchestration spine, the config-driven `BaseActivity` mechanism, and the shared domain children that every later product reuses.

The DF Jira project (`DF-*`) tells the after-story: its epics are all dated 2025-12 onward and are enhancements (calculator redesign, PD model, tax calc, supplier management, insurance expansion), i.e. continuous product iteration once the spine was live, not workflow construction.

## 3. DF2W — the product that reused the spine

| Milestone | Date | Source |
|---|---|---|
| D2W epics created (16 in one batch) | 2026-06-02 | Jira D2W project |
| DF2W workflow config set up | 2026-07-07 | git `feat(df2w): setup workflow config df2w` |
| Build burst | 2026-07 to 2026-09 | 309 df2w-tagged commits (179 in July alone) |
| Production go-live | not yet | zero applications for product_id 11 |

DF2W's workflow footprint on the spine is deliberately small. From the database configuration, the entire DF2W-versus-NDF2W scoring difference is **two config-gated activities** (`SurveyRACUnifiedActivity`, `PDModelAlternativeOverlayUnifiedActivity`) plus a few gateway flags; DF2W reuses the same Check, Initial Scoring, Survey, Underwriting and Operation orchestrators and the same KYC, Pefindo, RAC and PD-model children as every other product. The git history confirms where the effort actually went: the 2026 DF2W commits are dominated by 2-wheel calculation, insurance (the INS issues under epic D2W-9), and the Sharia variant — product economics, not workflow structure.

DF2W's child-issue cycle time is much longer than DF4W's build issues (median 56 days, p75 73, p90 87), and about half the sampled issues are still open. That is consistent with a program still mid-flight and working through business-logic breadth, not with workflow-plumbing difficulty.

## 4. Reading the two together

```mermaid
flowchart LR
  classDef plat fill:#DDEBF1,stroke:#1F6F8B,color:#12252D
  classDef df4 fill:#FBEDD4,stroke:#B8741A,color:#3A2A0E
  classDef df2 fill:#E4E9F4,stroke:#4B5D8A,color:#1A2238
  R["2024-03 unified spine begins<br/>(refactor-workflow)"]:::plat
  A["2024-07 DF4W config"]:::df4 --> B["2025-02 DF4W first prod<br/>~7 months"]:::df4 --> C["2026-07 DF4W 6,546/mo"]:::df4
  R --> A
  D["2026-07 DF2W config<br/>(reuses spine)"]:::df2 --> E["2026-09 still pre-prod<br/>small workflow delta"]:::df2
  R -. "spine + children reused" .-> D
```

- **What speed says about the design.** The unified workflow front-loads cost into the first product and makes later products a configuration exercise. DF2W adding a full loan product by seeding config rows and two activities, against DF4W needing seven months to stand the platform up, is the intended payoff and it is visible in both git and the database.
- **The unproven half.** "Cheap to add" is demonstrated; "cheap to run at scale and safe to change" is not yet, because DF2W is pre-production and DF4W is still a small fraction of volume. The config-skip mechanism that makes products cheap also hides what each product runs (see `workflow-gap.md`), so the maintenance cost of many products on one spine is still ahead of the team.
- **Fair comparison.** DF4W's 7-month clock included building the spine; a third product today would look like DF2W, not DF4W. The right expectation for the next product on Bravo unified is "a quarter of config and product-specific activities", provided its shape fits the existing five-stage spine.

## 5. What could not be measured

- **True DF2W time-to-market**, because it has not gone live; only time-to-build is known.
- **Defect and rework rates** per product, which would require the bug/incident projects, not the feature issues sampled here.
- **Effort in person-days**: Jira issue counts and cycle times are proxies; the `Estimated Effort` and story-point fields were empty on the issues sampled.
