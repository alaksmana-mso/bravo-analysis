**What this page is.** An inventory of every BFI mobile app and web application we could find, with its GitHub repository, stack, where it runs, and who it is for. Built on 20 October 2026 from four sources, cross-checked against each other. Each row says how sure we are.

## Summary

- **Mobile apps in the stores: 7.** Six are Flutter apps built from three repositories in `bfi-finance`. One (M-Beat, employee learning) has no repository in the org and is probably a vendor product.
- **Web applications: about 60 runnable, not archived**, from 280 repositories in the org. 43 are React single-page apps. The rest: the Next.js corporate site, a Strapi CMS, two PHP public sites, two HTMX back offices for LORA, and 17 small PHP tools for the PMO.
- **Two deployment worlds.** The legacy `ms-bfi-*` web UIs each have a Helm chart in `bfi-app-deployment` with a hostname we can read. The Bravo and LORA frontends are static builds pushed to Google Cloud Storage by their own GitHub workflows; the only place they appear in the manifests is as allowed origins on the API gateway.
- **One framework family.** React everywhere on the web (versions 17, 18 and 19 side by side), Flutter everywhere on mobile. No Vue, Angular, React Native or native Kotlin/Swift apps.
- **Ownership is concentrated.** The GitHub team `tribe-bravo-leads` holds about 45 of the frontend repositories, including both main Flutter apps.

## How we built the list

| Source | What it gives | What it misses |
|---|---|---|
| GitHub org `bfi-finance` (280 repos, by language and `package.json`/`pubspec.yaml`) | Every repository and its stack | Whether the app is deployed or used |
| Helm manifests (`bfi-app-deployment`, `app-deployment`, `origin/master` 20 Oct) | Hostnames, environments, public or private, image names | Static frontends deployed to GCS |
| Gateway CORS lists (`krakend-gateway` values) | Hostnames of web apps that call the API | Which repo builds each hostname |
| App Store lookup, Google Play search, Datadog RUM application list (60 apps) | What is live in users' hands and being monitored | RUM IDs are injected at build time, so the mapping to a repo is by name |

Repository URLs all follow `https://github.com/bfi-finance/<repo>`. "Last push" is the last commit date on GitHub as of 20 October 2026.

## Mobile apps

### In the stores

| Store name | Package / bundle id | Repo (app folder) | Audience | iOS | Android | RUM app | Last push |
|---|---|---|---|---|---|---|---|
| **BFI Mobile - Pinjaman Dana** | `id.co.bfi.customer` | `bravo-customer-app` (`digital/`) | Customers | id6472141180, v2.26.0, 12 Oct 2026 | Yes | BFI Mobile Prod `e438ff99…` | 20 Oct 2026 |
| **GENFI** | `id.co.bfi.agenttools` | `bravo-agency-app` (`agent_tools`, GENFI flavour) | Business agents (Agen Bisnis) | id6502278644, v1.16.0, 18 Sep 2026 | Yes | Agent Tools GENFI App `46eaa599…` | 20 Oct 2026 |
| **My Shaf** | `id.co.bfi.sharia.myshaf` | `bravo-agency-app` (`agent_tools`, Sharia flavour) | Sharia partners and agents | id6479341998, v1.3.1, 19 Jun 2026 | Yes | MyShaf `9a3558ab…` | 20 Oct 2026 |
| **SQUARE** (Super Quick Utility ARE) | `id.co.bfi.aretracker` | `bravo-agency-app` (`are_tracker`) | Agency relations staff and supervisors | id6451481748, v1.37.0, 18 Sep 2026 | Yes | SQUARE (ARE Tracker) `46561ada…`, events **not processed** | 20 Oct 2026 |
| **MY BISPRO** | `id.co.bfi.sharia.mybispro` | `bravo-agency-app` (`mybispro`) | Sharia credit marketing staff | id6469687433, v1.8.0, 19 Jun 2026 | Yes | None (Datadog initialised in code, no RUM app) | 20 Oct 2026 |
| **myBRO** (RO Tools) | `id.co.bfi.ro.rotools` | `bravo-ro-tools-apps` (`ro_tools`, v3.50.3) | Internal staff, repeat-order submissions | Not in the iOS catalogue | Yes | RO Tools-Prod `943c4ae2…` | 19 Oct 2026 |
| **BFI New M-Beat** | iOS `com.bfi.mbeatlms`, Play `com.bficompany.mbeatlms` | **No repo found in `bfi-finance`** | Employee learning | id1495767928, v3.0.6, 1 Jul 2026 | Yes | None | n/a |

Apple developer account: "BFI FINANCE INDONESIA, PT TBK" (id 1495767927). Google Play developer contact on the SQUARE listing: `playstore.developer@bfi.co.id`.

Notes on the mobile list:

- `bravo-agency-app` is one Melos monorepo holding four apps and a `ui_catalog`. It is checked out three times locally (Customer Platform, Agency, Tele Marketing squads), all at the same commit.
- A RUM app named **BFI PAS!** exists in Datadog, inactive, with events not processed. The App Store URL slug for BFI Mobile is still `bfi-pas`, so this is most likely the old name of the customer app. Not confirmed.
- A RUM app named **SMART Mobile - Collection** exists (browser type, events not processed). We found no store app or repo for it.
- SQUARE's two RUM apps have event processing set to **NONE**, so SQUARE is effectively unmonitored today.

### Not in the stores

| Repo | What it is | Status | Last push |
|---|---|---|---|
| `bravo-unsecured-apps` | Flutter customer app for unsecured loans, Dart 2.18 | **Archived** | 17 Jul 2023 |
| `bravo-supplier-web-ui` | React web app with an Android wrapper (`com.bfi.supplierapp`) | Not found in either store | 1 Oct 2026 |
| `bravo-mobile-playground` | Flutter sandbox for the Play Console internal track | Internal | 9 Sep 2024 |
| `flutter-boiler-plate-v2` | Flutter template | Template, not an app | 25 Aug 2022 |

### Mobile libraries and tooling (not apps)

| Repo | What it is | Last push |
|---|---|---|
| `bravo-image-validation-mobile-sdk` | Flutter plugin `bfi_document_detection` (KTP capture) | 19 Oct 2026 |
| `bfi-anti-kernel-su` | Flutter plugin, root and KernelSU detection | 3 Dec 2025 |
| `bfi-flutter-device-integrity` | Flutter plugin, Play Integrity and App Attest | 25 Mar 2026 |
| `bfi-flutter-packages` | Forked and patched packages: jailbreak detection, PDF view, certificate pinning, HTTP proxy, Mixpanel replay | 24 Aug 2026 |
| `frontend-mobile-ui` | Mobile design system (Melos, `ds_1/2/3`) | 6 Apr 2026 |
| `wdio-test-automation` | WebdriverIO mobile test automation | 5 Mar 2026 |

## Web applications

Hostnames are production unless marked. "Deployed how" is one of: **Helm** (a chart in `bfi-app-deployment` or `app-deployment`), **GCS** (static build pushed to a bucket by the repo's own workflow), or **unknown**. Where the repo-to-hostname link is a name match and not read from any manifest, the hostname is marked *(inferred)*.

### Customer-facing

| App | Repo | Stack | Hostname | Deployed how | RUM | Last push |
|---|---|---|---|---|---|---|
| BFI public website | `bfi-digital-web-ui-v3` | PHP | www.bfi.co.id | Helm (`bfi-digital-ui-x`, public) | None | 19 Oct 2026 |
| BFI public website, older line | `bfi-digital-web-ui` | PHP | www.bfi-2.co.id | Helm (`bfi-digital-ui`, public) | None | 26 Aug 2026 |
| Corporate website | `bfi-corporate-website` | Next.js 16, React 19 | bfi-website.bfi.co.id (origin, private; likely behind the public site) | Helm | None | 20 Oct 2026 |
| Customer platform (4W, 2W, DF, Sharia) | `bravo-customer-platform-web` | React 17, Nx, Vite | platform.bravo.bfi.co.id *(inferred)*, pinjaman.bfi.co.id and digital-customer.bfi.co.id *(inferred)* | GCS | Customer Platform 4W, 2W, DF, Sharia; customer-platform-unified | 20 Oct 2026 |
| Gold customer mini-app | `gold-customer-web` | React 18 | gold-customer.*.bravo *(inferred)* | Unknown | None | 25 Jun 2026 |
| Lead portal | `bravo-web-lead-portal` | React 18 | Unknown | Unknown | None | 15 Dec 2025 |
| e-Doc download | `bravo-edoc-download` | React 18, Vite 6 | e-doc.bfi.co.id *(inferred)* | Unknown | prod-bravo-edoc-download | 19 Oct 2026 |
| E-Line feedback | `bravo-e-line-feedback-ui` | React 18 | Unknown | Unknown | sit/prod-eline-portal (name match) | 19 Oct 2026 |
| Whistleblower | `ms-whistleblower-ui` (chart name; repo not matched) | Unknown | wbs.bfi.co.id | Helm, public | None | n/a |

### Partner, agent and dealer facing

| App | Repo | Stack | Hostname | Deployed how | RUM | Last push |
|---|---|---|---|---|---|---|
| Agent Tools web (GENFI web) | `useragent-onboarding-fe` | React 18, Vite 4 | Unknown | GCS | agent-tools | 19 Oct 2026 |
| Agency supervisor cockpit | `agency-spv-cockpit` | React 18, Vite 4 | agencycockpit.bfi.co.id, spvcockpit.* | GCS | Agency Cockpit (ID found in repo) | 19 Oct 2026 |
| Supplier web | `bravo-supplier-web-ui` | React 18 | Unknown | Unknown | Supplier Web App | 1 Oct 2026 |
| Notary | `bravo-notary-ui` | React 18 | notary.*.bravo *(inferred)* | GCS (shared `js-deploy-prod` workflow) | sit/prod-notary-ui | 19 Oct 2026 |
| Unsecured merchant web | `bravo-unsecuredv2-merchant-web-ui` | React 18 | n/a | n/a | None | **Archived**, 21 Jun 2025 |
| Panel dashboard | `bfi-panel-dashboard-ui` (chart; repo not matched) | Unknown | dashboardconnect.bfi.co.id | Helm, public | None | n/a |
| Agency business | `bfi-agency-ui` (chart; repo not matched) | Unknown | agencybusiness.bfi.co.id | Helm, private | None | n/a |

### Internal: Bravo platform consoles (loan origination and servicing)

| App | Repo | Stack | Hostname | Deployed how | RUM | Last push |
|---|---|---|---|---|---|---|
| Employee Get Customer | `bravo-egc-fe` | React 18, Vite 6 | egc-fe.*.bravo *(inferred)* | GCS | EGC Platform | 19 Oct 2026 |
| Surveyor console | `bravo-surveyor-console` | React 18, Vite 7 | surveyor.bfi.co.id, surveyor-syariah.bfi.co.id | Unknown | Surveyor Platform Prod/Test | 19 Oct 2026 |
| Underwriting console | `bravo-underwriting-console` | React 17, Vite 4 | Unknown | Unknown | Underwriting Platform Prod/Test | 15 Oct 2026 |
| Operation console | `bravo-operation-console` | React 18, Vite 7 | operation.bfi.co.id *(inferred)* | GCS (public bucket) | Operation Platform Prod/Test | 16 Oct 2026 |
| Back office | `bravo-backoffice-web-ui` | React 18 | backoffice-web-ui.*.bravo | Unknown | Backoffice Web App | 20 Oct 2026 |
| Assistance apps (micro-frontend) | `bravo-assistance-service-web` | React 18, Nx, Module Federation, Vite 7 | new-asisten.bfi.co.id, asisten.* | Unknown | new-assistance-apps, Assistance App | 20 Oct 2026 |
| Lead assistance (CAS) | `lead-assistance-fe` | React 18 | Unknown | Unknown | None found | 2 Oct 2026 |
| Platform FE (IS Platform) | `bravo-platform-fe` | React 18, Vite 7 | platform.* *(inferred)* | Unknown | sit-platform-fe | 19 Oct 2026 |
| Product and pricing admin | `bravo-product-web` | React 18 | Unknown | Unknown | None | 19 Oct 2026 |
| Repeat-order telesales | `bravo-repeat-order-web-tele` | React 18, Vite 3 | Unknown | Unknown | RO Web Tele Prod/UAT/SIT | 20 Oct 2026 |
| Repeat-order campaign CMS | `bravo-repeat-order-web-cms` | React 18 | Unknown | Unknown | None | 19 May 2025 |
| POS tools | `pos-tools-web` | React 18, Vite 7 | Unknown | Unknown | None | 19 Oct 2026 |
| Gold back office | `gold-backoffice-web` | React 18 | Unknown | Unknown | None | 25 Jun 2026 |
| Digital dashboard | `bfi-dashboard-digital-fe` | React 18 | digital-business.bfi.co.id *(inferred)* | Unknown | prod-bfi-dashboard-digital-fe | 20 Oct 2026 |
| Mobile internal dashboard | `bfi-mobile-internal-dashboard` | React 18, Vite 8 | Unknown | Unknown | None | 13 Oct 2026 |
| NDF 4W onboarding | `ndf4w-onboarding-fe` | React 17 | dm-fe-ndf4w.bfi.co.id *(inferred, internal gateway)* | Unknown | None | 21 Jun 2025 |
| NDF 2W | `ndf2w-fe` | React 17, CRA | dm-fe-ndf2w.bfi.co.id *(inferred, internal gateway)* | Unknown | None | 21 Jun 2025 |
| 4W/2W monorepo | `monorepo-frontend` | React 18, Nx 16 | Unknown | Unknown | None | 21 Jun 2025 |

### Internal: loan management, documents and collection

| App | Repo | Stack | Hostname | Deployed how | RUM | Last push |
|---|---|---|---|---|---|---|
| LMS back office | `bravo-lms-fe` | React 17, Vite 6 | lms.bfi.co.id *(inferred)* | GCS | prod-bravo-lms-fe | 19 Oct 2026 |
| LMS core | `bravo-lms-core-fe` | React 17 | Unknown | Unknown | Prod LMS Core FE | 20 Oct 2026 |
| LMS funding | `bravo-lms-fund-fe` | React 17 | lms-fund.bfi.co.id *(inferred)* | Unknown | prod-bravo-lms-fund-fe | 20 Oct 2026 |
| LMS insurance | `bravo-lms-insurance-fe` | React 17 | Unknown | Unknown | Prod LMS Insurance FE (inactive) | 19 Oct 2026 |
| LMS operation | `bravo-lms-operation-fe` | React 17 | Unknown | Unknown | Prod LMS Operation FE (inactive) | 17 Oct 2025 |
| Document management (DMS) | `bravo-dms-fe` | React 18, Vite 6 | document.bfi.co.id *(inferred)* | GCS | PROD-DMS-FE | 20 Oct 2026 |
| DMS data admin | `dms-data-admin-fe` | React 18, Vite 6 | Unknown | Unknown | prod-dms-data-admin-fe (inactive) | 19 Oct 2026 |
| Dominic | `bravo-dominic-fe` | React 18 | Unknown | Unknown | None | 19 May 2025 |
| E-Line | `bravo-e-line-ui` | React 18 | Unknown | Unknown | prod-bravo-e-line-ui | 19 Oct 2026 |
| E-Line portal | `bravo-eline-portal-fe` | React 18 | n/a | n/a | sit/prod-eline-portal | **Archived**, 31 Oct 2025 |
| Collection automated QA | `bravo-aqm-collection-fe` | React 18 | aqm-collection.*.bravo *(inferred)* | Unknown | Automated Quality Management | 19 Oct 2026 |
| Recovery management | `bfi-rms-fe` | React 18 | rms-fe.*.bravo *(inferred)* | GCS (shared `js-deploy-prod` workflow) | None found | 20 Oct 2026 |
| Inventory management | `bravo-inventory-management-system` | React 18 | Unknown | Unknown | Inventory Management System | 20 Oct 2026 |

### Internal: LORA

| App | Repo | Stack | Hostname | Deployed how | RUM | Last push |
|---|---|---|---|---|---|---|
| LORA back office | `lora-backoffice-fe` | HTMX 2 + Solid, Vite 6 | lora-backoffice.*.bravo (SIT/UAT); lora-backoffice-corporate and -ssf hosts in UAT CORS | GCS | LORA Back Office FE SIT/UAT/PROD | 20 Oct 2026 |
| LORA back office, SSF | `lora-backoffice-ssf-fe` | HTMX + Solid, Vite 6 | lora-backoffice-ssf.* *(inferred)* | Unknown | None found | 26 Jan 2026 |
| LORA customer FE | Repo not matched | Unknown | Unknown | Unknown | LORA Customer FE SIT/UAT/PROD | n/a |
| Rule editor | `gorules-editor` image (no repo matched) | GoRules | gorules-editor.uat.bravo (UAT only) | Helm, private | None | n/a |

### Internal: legacy `ms-bfi-*` estate (Helm charts in `bfi-app-deployment`)

These have a chart and a hostname, but in most cases we could not match the chart to a frontend repo in the org. The image name is the chart name.

| Hostname | Chart | Exposure | Audience | Repo |
|---|---|---|---|---|
| otrs.bfi.co.id | `bfi-otrs-ui` | Public and private | Customer care | Not matched (`new-otrs-ui` and `dashboard-otrs` exist for the newer OTRS) |
| new-otrs.bfi.co.id | `ms-new-otrs-ui` | Private | Customer care | `new-otrs-ui` (React 18) |
| incentive.bfi.co.id | `bfi-incentive-ui` | Private | Sales incentive admins | `bfi-incentive-ui` (React 17, Vite 4; RUM test-ms-bfi-incentive-ui) |
| operation-excellent.bfi.co.id | `bfi-operation-ui` | Private | Ops excellence | `bfi-operation-ui` (React 18; RUM prod-ms-bfi-operation-ui) |
| website-cms.bfi.co.id | `bfi-website-cms` | Private | Marketing | `bfi-website-cms` (Strapi 5) |
| pcms.bfi.co.id | `pcms` | Public and private | Finance | `finance-pcms-findigitalization` (PHP) |
| ams.bfi.co.id | `iad-ams` | Public | Internal audit | Not matched |
| ares.bfi.co.id | `ares` | Public | Finance | Not matched |
| microservices.prod.bfi.co.id/bfi-treasury-web-ui | `bfi-treasury-web-ui` | Public, path on API host | Treasury | Not matched |
| audit.bfi.co.id | `bfi-audit-ui` | Private | Internal audit | Not matched |
| new-insurance.bfi.co.id | `bfi-insurance-ui` | Private | Insurance ops | Not matched |
| omni-middleware.bfi.co.id | `bfi-omni-middleware-ui` | Private | Ops and IT | Not matched |
| branch-score.bfi.co.id | `ms-score-branch-ui` | Private | Branch management | Not matched |
| sa-tools.bfi.co.id | `ms-sa-tools` | Private | Internal tools | Not matched |
| formio-attachment.bfi.co.id | `bfi-formio-ui` | Both ingresses disabled in prod | Forms | Not matched |
| iad-sandbox-army.prod.bfi.co.id | `army` | Private | Internal audit | Not matched |
| s1.bfi.co.id | `strategyone-*` | Private, internal gateway | Risk decisioning (StrategyOne, vendor) | Vendor product |
| e-pmo.prod.bfi.co.id/pmotools, /pmotools2 | `pmotools`, `pmotools2` | Private | PMO | `pmo-pmotools`, `pmo-pmotools2` |
| Non-prod only: frp, dga, ticketing, engineering-report, redash, autiq, pmo-omega, promesys | various | Private | Internal | Partly matched (`pmo-promesys`) |

### Internal: decision management and other hosts behind the internal gateway

Seen as allowed origins on `krakend-gateway-internal` (SSO through the google-workspace realm). No chart or repo was matched for these: `da-obligor`, `dm-afrules`, `dm-aggregation`, `dm-mdata`, `dm-rules`, `webcore5`, `webcore6` (all `.bfi.co.id`, mostly plain HTTP). Likely legacy decision-management and core web apps. Also seen in service config, unmatched: `xportal-app.bfi.co.id`, `ca.bfi.co.id`, `orientasi.*`, `genfi.*.bravo`.

### PMO tools (17 small PHP apps)

Repos `pmo-absen`, `pmo-actionlog`, `pmo-boarding`, `pmo-briliance`, `pmo-core`, `pmo-dfr`, `pmo-kboard`, `pmo-momo`, `pmo-pdc`, `pmo-pmotools`, `pmo-pmotools2`, `pmo-projo`, `pmo-promesys`, `pmo-rapi`, `pmo-resep`, `pmo-room`, `pmo-vms`. Plain PHP (no `composer.json`), last pushes between Aug 2024 and Feb 2026. Only `pmotools`, `pmotools2` (prod) and `promesys`, `pmo-omega` (dev) have charts. Whether the others are live is not known.

### Web libraries, templates and login themes (not apps)

| Repo | What it is |
|---|---|
| `frontend-ui` | `@bfi-finance/frontend-ui`, web design system |
| `frontend-kit` | Shared config |
| `bravo-voyagers` | Unified navigation shell component |
| `bfi-ai-chat-sdk` | `@bfi-finance/chat-sdk` |
| `bravo-image-validation-web-sdk` | Web image validation SDK |
| `bravo-eslint-config`, `bravo-prettier-config` | Lint and format config |
| `bravo-react-ts-boilerplate` | React template. At least 12 apps still carry its default package name |
| `agency-spvcockpit-login`, `bravo-ims-login`, `bravo-repeat-order-web-tele-login`, `bravo-surveyor-console-login`, `dms-edoc-login` | Keycloak login themes |
| `bravo-unsecuredv2-web-lib` | Archived |
| `bravo-monorepo-egc-fe`, `bravo-repeat-order-cre-tool-app` | Empty repos |
| `lora-template-builder-poc`, `doc-renderer-builder`, `dashboard-otrs` | Proof of concept and internal tools (React 19 / Astro) |

## Observations

- **The mobile estate is 3 repos and 6 apps.** The agency monorepo alone ships four store apps. Any mobile platform decision (RASP, design system, CI) should be made for all three repos, not only `bravo-customer-app`.
- **Three React majors in production.** React 17 lives in the LMS apps, the underwriting console, the NDF apps and the customer platform. React 18 is the default. React 19 is only in the corporate site. Vite ranges from 3 to 8. The web estate has no shared upgrade cadence.
- **Monitoring gaps.** SQUARE's RUM events are not processed. MY BISPRO and M-Beat have no RUM app. Five web RUM apps are inactive. About 12 web repos have no Datadog package at all.
- **Deployment is not visible for most Bravo frontends.** They go to GCS buckets through per-repo workflows and a shared `bfi-base-template` workflow. There is no single place that lists which bucket serves which hostname. That is why about 20 hostnames on this page have no confirmed repo and about 25 repos have no confirmed hostname.
- **Legacy charts without repos.** About 12 `ms-bfi-*` charts in `bfi-app-deployment` have no matching frontend repo in the org. Either the source is in another org or forge (two repos mention a GitLab migration), or the image is built from a repo with a different name.
- **Archived but still referenced.** `bravo-eline-portal-fe` is archived, yet `prod-eline-portal` is an active RUM app. Worth checking what still serves it.

## What we could not verify

- Google Play update dates and install counts. Play pages did not return content to our tools.
- Which hostnames are truly internet-reachable. "Public" and "private" above come from the ingress class, not from a network test.
- The repo behind each GCS-hosted hostname. The bucket names live in each repo's workflow and in Terraform, which we did not read.
- The second Datadog server was not queried. RUM apps that exist only there are missing.
- Whether "BFI PAS!" is the old customer app, and what "SMART Mobile - Collection" is.
- Whether any BFI apps still live only in GitLab.

## How to keep this page current

- A new frontend repo in `bfi-finance` should be added here with its hostname and RUM app on the day it first deploys.
- The repo listing can be regenerated with `gh repo list bfi-finance --limit 1000 --json name,description,primaryLanguage,isArchived,pushedAt`. The store list comes from the iTunes lookup API for developer id 1495767927. The RUM list comes from Datadog.
