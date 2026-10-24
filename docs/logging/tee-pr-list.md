# tee -a PR list

**tee -a pull requests — status 24 Oct, 02:00 UTC**

Fix: one flag in `docker-entrypoint.sh` (`tee` → `tee -a`) so SRE's nightly 19:00 UTC log truncation (the `clear-log-*` CronJobs in bravo-terraform) stops sending NUL padding to Datadog. The file is still emptied every night; `-a` just makes `tee` write from the top of the empty file instead of from its old offset, so there is no gap of zero bytes for the Agent to ship.

Proof it works: every service that has shipped it stopped producing padding at the release minute. 23 Oct was the first full day with fifteen services live: **about 1,740 GB a day before → 5.6 GB a day**, line counts unchanged, about **$5,200 a month**. Datadog's estate-wide ingestion went from about 2.0 TB a day (week to 20 Oct) to 0.65 TB on 23 Oct.

**Score, first pack (8 Oct): 19 of 19 merged, 15 live.** Second pack (24 Oct): 19 new pull requests, 0 merged.

✅ **Live in production with the fix (15)**
- customer-bff [#1297](https://github.com/bfi-finance/bravo-customer-bff-service/pull/1297) — v1.27.0 since 13 Oct (now v1.27.1). 73 GB/day → 0.1.
- partnership [#2400](https://github.com/bfi-finance/bravo-partnership-service/pull/2400) — v3.7.2 since 15 Oct (now v3.7.4). Never padded much.
- cnv [#777](https://github.com/bfi-finance/bravo-cnv-service/pull/777) — v1.66.1 since 15 Oct. 95 GB/day → 0.004.
- kyc-proxy [#740](https://github.com/bfi-finance/bravo-kyc-proxy/pull/740) — v1.47.0 since 15 Oct. 9 GB/day → 0.01.
- collection-consumer [#152](https://github.com/bfi-finance/collection-consumer-service/pull/152) — v1.10.2-rc1 since 16 Oct (now v1.10.3-rc1). 20 GB/day → 0.5.
- integrity [#30](https://github.com/bfi-finance/bravo-integrity-service/pull/30) — v1.1.5 since 21 Oct 02:50 UTC. 10 GB/day → 0.001.
- audit-trail [#38](https://github.com/bfi-finance/bravo-audit-trail-service/pull/38) — v1.1.12 since 21 Oct 03:12 UTC. **555 GB/day → 0.004.** The single biggest saving.
- gen-ai [#362](https://github.com/bfi-finance/bravo-gen-ai/pull/362) — v1.4.20 since 21 Oct 03:52 UTC. 14 GB/day → 0.001.
- user-iam [#525](https://github.com/bfi-finance/bravo-user-iam-service/pull/525) — v1.0.17 since 21 Oct 04:12 UTC. 72 GB/day → 0.001. Main deployment only; the sharia deployment did not move (see below).
- assistance [#207](https://github.com/bfi-finance/bravo-assistance-service/pull/207) — v1.13.4 since 21 Oct 09:39 UTC. 127 GB/day → 0.35. About 1,000 padding chunks a day remain from pods that report no `version` tag, so one assistance workload has not rolled yet.
- lms-ops [#1874](https://github.com/bfi-finance/bravo-lms-ops-service/pull/1874) — v3.24.1 since 21 Oct 10:31 UTC (now v3.24.2). **425 GB/day → 3.9**; what is left is real lines.
- rule-engine [#84](https://github.com/bfi-finance/bfi-rule-engine-service/pull/84) — v1.1.1 since 22 Oct 04:17 UTC. 6 GB/day → 0.001.
- agent-marketing [#840](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/840) — v1.24.0 since 22 Oct 09:41 UTC. 185 GB/day → 0.01. Main deployment only; the sharia deployment did not move.
- agency [#1175](https://github.com/bfi-finance/bravo-agency-service/pull/1175) — v2.28.1 since 22 Oct 09:56 UTC. 35 GB/day → 0.05.
- supplier [#204](https://github.com/bfi-finance/bravo-supplier-service/pull/204) — v1.9.4 since 22 Oct 11:09 UTC, also moved supplier-worker. 113 (+22) GB/day → 0.001.

🟠 **Merged, waiting for a release (3)**
- scheduling [#305](https://github.com/bfi-finance/bravo-scheduling-service/pull/305) — prod v2.2.18, no tag since 21 Sep. **42 GB/day.** The biggest of the three.
- gold-service [#191](https://github.com/bfi-finance/gold-service/pull/191) — prod v0.0.154, last tag is from June. 4 GB/day.
- robot-controller [#92](https://github.com/bfi-finance/bravo-robot-controller/pull/92) — prod v1.3.4. 0.9 GB/day.

🔴 **Merged to master, but production is built from another branch (1)**
- backoffice [#2982](https://github.com/bfi-finance/bravo-backoffice-service/pull/2982) — merged 16 Oct, but v1.26.0 (20 Oct) and v1.26.1 (22 Oct) were both cut from `release-v1.26.x` before the merge and still have plain `tee`. Under 1 GB/day. New pull request [#3108](https://github.com/bfi-finance/bravo-backoffice-service/pull/3108) on `release-v1.26.x`.

**What still pads on 23 Oct: about 580 GB a day, about $1,750 a month. 84% of it is one service.**

| Service | Production build | GB on 23 Oct | What fixes it |
|---|---|---:|---|
| repeat-order | v3.52.3 from `hotfix/v3.52.3-offering-life-insurance`, plain `tee`; `master` has no `tee` at all | **489** (up from 242 two weeks ago) | merge [#3551](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3551) on the hotfix branch and release, or ship v3.54.0 |
| scheduling | v2.2.18 | 42 | release `master` (#305 merged) |
| user-iam, sharia deployment | v0.1.24-sharia.2 from branch `v0.1.24-sharia.1` | 28 | [#532](https://github.com/bfi-finance/bravo-user-iam-service/pull/532) on that branch, then release |
| agent-marketing, sharia deployment | v1.8.5 from `release-1.8.0` | 12 | [#846](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/846) on that branch, then release |
| unsecured-v2 | v1.8.1, repository archived | 7 | owner to unarchive or retire |
| gold-service | v0.0.154 | 4 | release `master` (#191 merged) |
| robot-controller | v1.3.4 | 0.9 | release `master` (#92 merged) |
| backoffice | v1.26.1 from `release-v1.26.x` | 0.14 | [#3108](https://github.com/bfi-finance/bravo-backoffice-service/pull/3108), then release |

Outside the twenty: bpm sends 29 GB a day of padding; its `master` has no `tee` any more, so its next release fixes it. incentive-api (2.6 GB a day) has a pull request below.

**Second pack, 24 Oct: 19 new pull requests (0 merged).** A search of every `docker-entrypoint.sh` in the organisation found 18 more repositories whose default branch still pipes through plain `tee`. Each pull request is the same one-flag change with the same comment, and has reviewers from the repository's earlier pull requests.

Four on the branches production is really built from:
- repeat-order [#3551](https://github.com/bfi-finance/bravo-repeat-order-service/pull/3551) on `hotfix/v3.52.3-offering-life-insurance` — subhanbfi, khalidalhabibiebfi, yusuf-pangaribuan-bfi, bfi-yoanihsan, rudihermanto-bfi
- backoffice [#3108](https://github.com/bfi-finance/bravo-backoffice-service/pull/3108) on `release-v1.26.x` — okky-bfi, ekosilviawan, rudihermanto-bfi
- user-iam [#532](https://github.com/bfi-finance/bravo-user-iam-service/pull/532) on `v0.1.24-sharia.1` — bagus-bfi, bayubfi, debam-bfi
- agent-marketing [#846](https://github.com/bfi-finance/bravo-agent-marketing-service/pull/846) on `release-1.8.0` — subhanbfi, christianwijasabfi, ariesatya

Fifteen on `master`:
- bfi-incentive-api [#1738](https://github.com/bfi-finance/bfi-incentive-api/pull/1738) — 15,083 padding chunks in 7 days — christianwijasabfi, ariesatya, raymond-bfi
- bfi-insurance-api [#3391](https://github.com/bfi-finance/bfi-insurance-api/pull/3391) — ra-putranto, hendri-bfi, bfi-richardk, okky-bfi
- bfi-operation-ui [#996](https://github.com/bfi-finance/bfi-operation-ui/pull/996) — domisiriusbfi, rjiandybfi, bfisreadmin
- bravo-calculation-service [#15](https://github.com/bfi-finance/bravo-calculation-service/pull/15) — dave-bfi, jaka-utama, yuliusardy
- bravo-document-service [#316](https://github.com/bfi-finance/bravo-document-service/pull/316) — arirasmana0104, BFI-Ahmad-Akbar, luthfihm-bfi
- bravo-dominic-service [#19](https://github.com/bfi-finance/bravo-dominic-service/pull/19) — arirasmana0104, radifan-bfi, luthfihm-bfi
- bravo-employee-marketing-service [#14](https://github.com/bfi-finance/bravo-employee-marketing-service/pull/14) — samuel-bfi, okky-bfi, GibranLubis
- bravo-kyc-sign-service [#123](https://github.com/bfi-finance/bravo-kyc-sign-service/pull/123) — simukti, BFI-Yohanes, bagus-bfi, ariesatya, bayubfi, debam-bfi, rudihermanto-bfi
- bravo-master-service [#509](https://github.com/bfi-finance/bravo-master-service/pull/509) — bayubfi, debam-bfi, fairuzyassar85
- bravo-partnership-provisioning-service [#122](https://github.com/bfi-finance/bravo-partnership-provisioning-service/pull/122) — simukti, hendry-bfi, bfi-niel
- bravo-pbf-service [#126](https://github.com/bfi-finance/bravo-pbf-service/pull/126) — 095268, bfi-atria-tya, bfi-anggayuhindra
- bravo-samsat-region-resolver [#1](https://github.com/bfi-finance/bravo-samsat-region-resolver/pull/1) — no reviewer could be requested
- lora-cdc-bridge-service [#3](https://github.com/bfi-finance/lora-cdc-bridge-service/pull/3) — okky-bfi, andreas-wicaksana-s
- bravo-java-example [#46](https://github.com/bfi-finance/bravo-java-example/pull/46), the Java service template — bfi-atria-tya, okky-bfi, bfi-yoanihsan
- lora-example [#19](https://github.com/bfi-finance/lora-example/pull/19), the LORA service template — simukti, bfi-niel, yuliusardy

Could not be raised: `backend-dashboard-otrs` and `go-example-service` give no push access; `bravo-unsecuredv2-service` is archived. Seen with padding but without a `tee` line on `master` (old builds in production, a release fixes them): payment, bfi-digital-web-api, bfi-payment-api.

**Two asks that pay most:** release **repeat-order** (merge #3551 and cut a hotfix, or ship v3.54.0) and release **scheduling**. Together that is about 530 GB a day, over 90% of the padding left.

How this was checked: production versions from the `version` tag on each service's logs; padding = indexed lines starting with `...TRUNCATED...`; bytes = `datadog.estimated_usage.logs.ingested_bytes` by service, daily sums; whether a tag carries the fix = the `tee` line in `docker-entrypoint.sh` at that tag (tags cut from release branches do not list the merge commit, so ancestry is not reliable). The dashboard *Logging — log ingestion by service (tee -a watch)* (import file on the programme page) shows all of this per service.

Details and evidence: [Logging Improvement](README.md)
