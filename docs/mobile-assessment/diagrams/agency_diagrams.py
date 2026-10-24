#!/usr/bin/env python3
"""Mermaid sources for the 39 diagrams on each agency assessment page (GENFI 2874998826,
SQUARE 2875260970). The pages already hold mermaid-cloud macros named a01-today ... a22 with
revision 1, but no attachments were ever uploaded. This script writes the .mmd files into
diagrams/<app>-parent/, renders them to PNG, uploads both as attachments (version 1 on a
fresh page, matching the macro revision) and verifies the result.

Usage: agency_diagrams.py genfi|square [--upload]
"""
import os, sys, json, subprocess, re
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)

HOT = 'classDef hot fill:#ffe1e1,stroke:#c00'
GOOD = 'classDef good fill:#e3f5e1,stroke:#2a7'
NOW = 'classDef now fill:#fff4cc,stroke:#b80'

APPS = {
 "genfi": dict(page="2874998826", name="GENFI", folder="agent_tools", feat="lib/feature", nfeat="34", edges="129", edge_note="76 not into feature/common",
   ctrls="96", providers="104", ctrl_note="ref.watch in callbacks: 3", pilot="prospect + calculator", pilot_a="prospect", pilot_b="calculator",
   files="486 files, 103,625 lines", routes="router.dart 1,564 lines, 75 routes",
   analytics_today='ConventAnalyticsService<br/>5-value enum, 4 call sites<br/>key typo: proudct', analytics_sinks="Firebase only<br/>RUM screen names separate",
   log_today='DatadogLog.e creates a logger<br/>and never writes to it', log_crash="Crashlytics only<br/>off for MyShaf and web", log_keys="crash key nik_marketing",
   flags_today='ConventFeatureFlag (20 keys)<br/>+ app config (10) + Sharia model (1)', flags_raw="raw getBool in main.dart<br/>compile-time FEATURE_* defines",
   net_today='OtpHttpClient (264 lines)<br/>checks token before every call<br/>refresh single-flight, retry once', net_variants="5 client variants in main.dart<br/>default, auth, Krakend,<br/>chat gateway, non-auth Krakend",
   sec_today='Pinning: prod only<br/>Play Integrity: MyShaf only<br/>proguard-rules.pro missing', sec_extra="proxy switch reaches prod<br/>Alice in release builds",
   ds_today='ds_2 (154 files) + ds_3 (199)<br/>110 files import both<br/>local ds3 shim', ds_raw="92 raw Colors, 17 TextStyle(", ds_target="ds_3 only<br/>delete ds_2 and the shim",
   test_today='149 test files<br/>665 widget, 823 unit<br/>33 controller tests', test_e2e="register, prospect input,<br/>calculator, reserve lead",
   deps=["Riverpod 2.6 (StateNotifier)", "freezed 2.5", "flutter_markdown 0.6 (discontinued)", "flutter_html 3.0.0-beta", "intl pinned 0.20.2 + override", "git deps: ds_2, ds_3, device_integrity,<br/>jailbreak fork (SHA)", "alice in release builds"],
   bigfiles=[("loan_info_screen.dart", "2,429"), ("calculator_controller.dart", "2,290"), ("collateral_screen.dart", "2,160"), ("calculation_result_screen.dart", "2,038"), ("loan_info_screen_controller.dart", "1,901"), ("calculator_screen.dart", "1,862")],
   leak_main='convent SIT pipeline<br/>Reveal-secret step prints FIREBASE_API_KEY<br/>162 runs, latest 22 Oct 2026', leak_main_fix="delete the step<br/>rotate FIREBASE_API_KEY",
   plans={"01": "Security (shared)", "02": "CI/CD (shared)", "03": "Logging and crashes", "04": "Testing", "05": "Networking (shared)", "06": "Lint + guardrails (shared)", "07": "Layering<br/>(prospect + calculator first)", "08": "State management", "09": "Repo layout (shared)", "10": "Feature flags", "11": "Analytics wrapper", "12": "Design system (shared)", "13": "Dependency injection"},
   stageA=["01", "02"], stageB=["03", "04", "05", "06"], stageC=["07", "08", "09", "13"], stageD=["10", "11", "12"],
   q_extra=[("Is the GENFI web build<br/>a supported target?", "changes what pinning<br/>and Alice can do"), ("MyShaf: flavour of agent_tools<br/>or its own app?", "own pipelines, environments<br/>and integrity check already")]),
 "square": dict(page="2875260970", name="SQUARE", folder="are_tracker", feat="lib/features", nfeat="21", edges="89", edge_note="profile imported by 35 files",
   ctrls="82", providers="103", ctrl_note="ref.watch in callbacks: 0", pilot="lead + company_submission", pilot_a="lead", pilot_b="company_submission",
   files="394 files, 69,799 lines", routes="router.dart 628 lines, 32 routes",
   analytics_today='37-line Analytics wrapper<br/>27 logEvent calls in 25 files<br/>string names, some interpolated', analytics_sinks="Firebase only<br/>user id = employee NIK<br/>RUM events not processed",
   log_today='Log.e logs at debug level<br/>under a warning threshold', log_crash="Crashlytics only<br/>skips session, socket, timeout", log_keys="crash user id = NIK",
   flags_today='freezed RemoteConfig (23 fields)<br/>hand-mapped, 140-line repository<br/>no setDefaults', flags_raw="FEATURE_FLAG_NON_REGISTERED_MAINTAIN<br/>is a compile-time define",
   net_today='SquareHttpClient (288 lines)<br/>refreshes Keycloak token<br/>BEFORE every request<br/>401: SessionExpired, no retry', net_variants="3 client variants in main.dart<br/>Keycloak: password grant with<br/>client secret, or WebView<br/>code flow without PKCE",
   sec_today='Pinning: prod only<br/>no Play Integrity / App Attest<br/>proguard-rules.pro missing', sec_extra="CLIENT_SECRET + GOOGLE_API_KEY<br/>compiled into the app",
   ds_today='ds_1 in 195 files<br/>BfiColors 746, BfiText 536', ds_raw="46 TextStyle(, 10 TextButton(,<br/>20 raw Colors", ds_target="ds_3 (with GENFI)<br/>delete ds_1",
   test_today='135 test files<br/>854 widget, 394 unit<br/>71 screen, 9 controller tests', test_e2e="visit report, lead submission,<br/>company submission",
   deps=["Riverpod 2.6 (StateNotifier)<br/>only in dependency_overrides", "freezed 2.5", "flutter_markdown 0.6 (discontinued)", "flutter_secure_storage 8", "dio, equatable undeclared", "git deps: ds_1, flutter_contacts fork,<br/>jailbreak fork (SHA)", "4 unused dart-defines<br/>alice in release builds"],
   bigfiles=[("company_submission_prospect_step.dart", "1,195"), ("no_deal_recalculation_screen.dart", "1,071"), ("collateral_asset_info_screen.dart", "1,057"), ("visit_report_form_screen.dart", "1,056"), ("loan_controller.dart", "1,029"), ("company_submission_collateral_step.dart", "944")],
   leak_main='ARE tracker SIT/UAT pipeline<br/>uploads keystore.jks + properties<br/>as an artifact, 156 runs', leak_main_fix="delete the upload step<br/>reset the upload key (Play App Signing)",
   plans={"01": "Security (shared)", "02": "CI/CD (shared)", "03": "Logging and crashes", "04": "Analytics wrapper", "05": "Testing", "06": "Networking (shared)", "07": "Lint + guardrails (shared)", "08": "Layering<br/>(lead + company_submission first)", "09": "State management", "10": "Repo layout (shared)", "11": "Feature flags", "12": "Design system (shared)", "13": "Dependency injection"},
   stageA=["01", "02"], stageB=["03", "04", "05", "06", "07"], stageC=["08", "09", "10", "13"], stageD=["11", "12"],
   q_extra=[("Keycloak: code flow with PKCE<br/>for the SQUARE client?", "so the secret leaves the app"), ("Who owns Datadog for SQUARE?", "RUM wired but not processed")]),
}

def diagrams(a):
    N = a["name"]; d = {}
    d["a01-today"] = f'''flowchart TD
  sc["Screens"]
  fb["Firebase"]
  sc -->|"{'5 enum events, 4 sites' if N=='GENFI' else '27 logEvent calls (strings)'}"| fb
  ct["StateNotifier controllers<br/>({a['ctrls']})"]
  rp["shared_data repositories<br/>(API models reach the UI)"]
  hc["HttpClient + auth decorator<br/>(auth outside the client)"]
  sc --> ct --> rp --> hc
  subgraph bt["Build and tests"]
    pb["Prod build: obfuscate + R8<br/>pinning prod only, no RASP"]
    ts["Tests: screens + controllers<br/>no coverage gate, no E2E"]
  end
  hc ~~~ bt
  class ct,rp,hc,pb,ts hot
  {HOT}'''
    d["a01-target"] = f'''flowchart TD
  sc["Screens"]
  ap["Analytics port"]
  sc -->|"typed events"| ap
  ap --> fb["Firebase"]
  ap --> dd["Datadog RUM"]
  nt["Notifier / AsyncNotifier"]
  uc["Domain use cases<br/>(pure Dart)"]
  rp["Ports over shared_data<br/>(DTO -> entity)"]
  dio["core HttpClient<br/>+ interceptor chain"]
  sc --> nt --> uc --> rp --> dio
  subgraph bt["Build and tests"]
    pb["Prod build: obfuscate + R8 + RASP<br/>pinning everywhere"]
    ts["Tests: domain + notifier + screen<br/>coverage gate + E2E"]
  end
  dio ~~~ bt
  class ap,nt,uc,rp,dio,pb,ts good
  {GOOD}'''
    d["a02"] = f'''flowchart TD
  repo["bravo-agency-app<br/>one monorepo, one CI"]
  repo --> at["agent_tools/<br/>GENFI + MyShaf flavour"]
  repo --> ar["are_tracker/<br/>SQUARE"]
  repo --> mb["mybispro/<br/>MY BISPRO"]
  repo --> sd["shared_data/ (9)<br/>agency, agent_marketing,<br/>onboarding, keycloak, sso ..."]
  repo --> sl["shared_lib/<br/>core, crash_reporting, places"]
  repo --> sf["shared_features/<br/>collab_form"]
  at --> sd
  ar --> sd
  mb --> sd
  at --> sl
  ar --> sl
  at --> sf
  ar --> sf
  class {'at' if N=='GENFI' else 'ar'} now
  {NOW}'''
    d["a03-today"] = f'''flowchart TD
  mw["melos workspace<br/>15 shared packages"]
  ap["{a['folder']}/<br/>app + ALL {a['nfeat']} features<br/>({a['feat']})"]
  mw --> ap
  mw --> sd["shared_data/*<br/>DTOs + repositories<br/>291k generated lines"]
  mw --> co["shared_lib/core/"]
  ap --> f1["{a['pilot_a']}"]
  ap --> f2["{a['pilot_b']}"]
  ap --> f3["{'common ...' if N=='GENFI' else 'profile, maintain ...'}"]
  f1 <-.->|"{a['edges']} free imports<br/>{a['edge_note']}"| f3
  f2 <-.-> f1
  class ap,f1,f2,f3,sd hot
  {HOT}'''
    d["a03-target"] = f'''flowchart TD
  mw["melos workspace"]
  ft["features/{a['folder']}/"]
  mw --> ap["{a['folder']}/<br/>app shell: router + composition root"]
  mw --> ft
  mw --> sd["shared_data/*<br/>plain Dart, generated in CI"]
  mw --> co["shared_lib/core/<br/>+ pure barrel"]
  ft --> f1["{a['pilot_a']}/<br/>small public API"]
  ft --> f1a["{a['pilot_a']}_api/<br/>entities others import"]
  ft --> f2["{a['pilot_b']}/ ..."]
  f2 -.->|"imports"| f1a
  rule["Rule: feature -> *_api<br/>never feature -> feature"]
  f2 ~~~ rule
  class ap,ft,f1,f1a,rule,sd,co good
  {GOOD}'''
    d["a04-today"] = f'''flowchart LR
  sc["Screen"] --> ct["StateNotifier controller<br/>rules live here"]
  ct --> rp["shared_data repository<br/>(concrete class, static provider)"]
  rp --> hc["HttpClient"]
  sc -.->|"reads repositories<br/>directly"| rp
  rp -.->|"*Response DTOs<br/>reach screens"| sc
  note["No domain layer<br/>{'0 domain folders' if N=='GENFI' else 'only lead/cancellation_review<br/>has the shape'}"]
  class ct,rp,note hot
  {HOT}'''
    d["a04-target"] = f'''flowchart LR
  sc["Screen"] --> nt["Notifier<br/>UI state only"]
  nt --> uc["Use case<br/>(pure Dart, unit-tested)"]
  uc --> pt["Port<br/>(interface in domain)"]
  pt --> im["Port impl in data/<br/>wraps shared_data, maps DTO -> entity"]
  im --> rp["shared_data repository"]
  rule["domain-purity: strict<br/>dto-in-presentation: ratchet"]
  pt ~~~ rule
  class nt,uc,pt,im,rule good
  {GOOD}'''
    d["a05-today"] = f'''flowchart TD
  sc["Screens"] --> ct["{a['ctrls']} StateNotifier controllers<br/>{a['ctrl_note']}"]
  ct --> pv["{a['providers']} static final provider"]
  md["main.dart: ProviderScope.overrides<br/>HttpClient variants, NetworkConfig,<br/>auth client"]
  md --> pv
  sg["Static singletons beside Riverpod:<br/>CrashReporter.instance,<br/>NavigationService.instance{', remote-config instance' if N=='GENFI' else ''}"]
  pv -.-> sg
  rp["shared_data: concrete repositories<br/>nothing below HttpClient can be faked"]
  pv --> rp
  class ct,sg,rp hot
  {HOT}'''
    d["a05-target"] = f'''flowchart TD
  sc["Screens"] --> nt["Notifier / AsyncNotifier<br/>(Riverpod 3)"]
  nt --> uc["Use cases"]
  uc --> pt["Ports (providers that throw<br/>until overridden)"]
  cr["app/di/app_overrides.dart<br/>one composition root per app"]
  cr -->|"overrides"| pt
  tv["test/helpers/test_overrides.dart<br/>fakes per port"]
  tv -->|"overrides"| pt
  wt["wiring test reads every port"]
  cr ~~~ wt
  class nt,uc,pt,cr,tv,wt good
  {GOOD}'''
    d["a06-today"] = f'''flowchart TD
  sc["Screens"]
  wr["{a['analytics_today']}"]
  sc --> wr
  wr --> fb["{a['analytics_sinks']}"]
  nv["Navigation observer<br/>sends screen names to RUM<br/>(separate path)"]
  sc --> nv
  class wr,fb hot
  {HOT}'''
    d["a06-target"] = f'''flowchart TD
  sc["Screens"] -->|"typed events<br/>from one catalogue"| ap["shared_lib/analytics<br/>Analytics port + PII denylist"]
  ap --> fa["FirebaseAdapter"]
  ap --> da["DatadogRumAdapter"]
  ro["Router observer<br/>screen() to all adapters"] --> ap
  gf["event-names.golden.txt<br/>parity oracle"]
  ap ~~~ gf
  class ap,fa,da,ro,gf good
  {GOOD}'''
    d["a07-today"] = f'''flowchart TD
  err["Handled error<br/>(guardLog, provider observer)"]
  lg["{a['log_today']}"]
  err --> lg
  lg -.->|"nothing arrives"| dd["Datadog logs"]
  lg --> cr["{a['log_crash']}"]
  pii["No PII cleaner<br/>{a['log_keys']}<br/>consent hard-coded granted"]
  cr ~~~ pii
  class lg,pii hot
  {HOT}'''
    d["a07-target"] = f'''flowchart TD
  err["Handled error / crash"] --> al["shared_lib/observability<br/>AppLogger + LogEvent"]
  al --> sn["Sanitiser<br/>denied keys dropped,<br/>NIK / phone / email masked"]
  sn --> s1["Datadog logs sink<br/>(error level, stack, trace id)"]
  sn --> s2["Crashlytics sink<br/>(opaque agent id)"]
  cs["ConsentState provider"] --> al
  class al,sn,s1,s2,cs good
  {GOOD}'''
    d["a08-today"] = f'''flowchart TD
  rc["Firebase Remote Config"] --> md["{a['flags_today']}"]
  md --> sc["Screens and controllers"]
  df["{a['flags_raw']}"]
  df --> sc
  own["No owner, no removal date,<br/>no switch-flag kind"]
  md ~~~ own
  class md,df,own hot
  {HOT}'''
    d["a08-target"] = f'''flowchart TD
  cat["Typed flag catalogue per app<br/>key, default, owner, removal date"]
  gen["Generator: setDefaults + key map"]
  cat --> gen
  pl["FeatureFlagPlatform<br/>(Remote Config adapter, FakeFlags)"]
  gen --> pl
  pl --> sc["Screens read flagProvider(...)"]
  sw["SwitchFlag kind<br/>default = old path, read at journey start"]
  cat --> sw
  ci["CI fails on an overdue flag"]
  cat ~~~ ci
  class cat,gen,pl,sw,ci good
  {GOOD}'''
    d["a09-today"] = f'''flowchart TD
  rp["Repositories"] --> dc["{a['net_today']}"]
  dc --> hc["core HttpClient (395 lines)<br/>no auth, no retry, no trace id<br/>pinning only if fingerprint set"]
  hc --> net["Backend / Krakend / Keycloak"]
  six["(shared) six near-identical<br/>auth decorators, 1,508 lines<br/>only one retries after refresh"]
  dc ~~~ six
  va["{a['net_variants']}"]
  dc ~~~ va
  class dc,six,va hot
  {HOT}'''
    d["a09-target"] = f'''flowchart LR
  rp["Repositories<br/>(unchanged call sites)"] --> hc["core HttpClient"]
  hc --> i1["headers"] --> i2["auth strategy<br/>({'OtpAuthStrategy' if N=='GENFI' else 'KeycloakAuthStrategy + PKCE'})"] --> i3["single-flight refresh<br/>retry once on 401"] --> i4["retry (GET only)"] --> i5["trace id"] --> i6["error mapping"] --> i7["pinning (every build)"]
  i7 --> net["Backend"]
  fl["useInterceptorClient flag<br/>default old, per app"]
  hc ~~~ fl
  class hc,i1,i2,i3,i4,i5,i6,i7,fl good
  {GOOD}'''
    d["a10-today"] = f'''flowchart TD
  wf["4 workflows print or export secrets<br/>debugger.yaml: 52 echoes<br/>{a['leak_main']}"]
  env["Prod approval = workflow step<br/>_build variants: no approval<br/>environment rules: not verified"]
  app["{a['sec_today']}<br/>{a['sec_extra']}"]
  wf ~~~ env ~~~ app
  class wf,env,app hot
  {HOT}'''
    d["a10-target"] = f'''flowchart TD
  wf["No secret in any log or artifact<br/>workflow-lint + Codacy on every PR<br/>secrets rotated, upload key reset"]
  env["Prod environments: release refs only<br/>every prod-signed build behind<br/>the 2-approval step"]
  app["Pinning in every build<br/>integrity verdicts enforced server-side<br/>reviewed proguard-rules.pro<br/>RASP: one vendor, three repos"]
  pii["Consent provider, PII sanitiser,<br/>screen-capture guard on sensitive routes"]
  wf ~~~ env ~~~ app ~~~ pii
  class wf,env,app,pii good
  {GOOD}'''
    d["a11-today"] = f'''flowchart TD
  app["{N} screens"] --> ds["{a['ds_today']}"]
  app --> raw["Raw styling:<br/>{a['ds_raw']}"]
  four["(shared) four design systems<br/>ds_1, ds_2, ds_3, ui_theme<br/>no Widgetbook, no tokens"]
  ds ~~~ four
  class ds,raw,four hot
  {HOT}'''
    d["a11-target"] = f'''flowchart TD
  app["{N} screens"] --> ds["{a['ds_target']}"]
  ds --> wb["Widgetbook for ds_3<br/>(frontend-mobile-ui, GitHub Pages)"]
  ds --> tk["Tokens from Figma variables<br/>(optional)"]
  rt["no-raw-style ratchet<br/>baselines only go down"]
  app ~~~ rt
  class ds,wb,tk,rt good
  {GOOD}'''
    d["a12-today"] = f'''flowchart TD
  t["{a['test_today']}<br/>controllers tested directly (good)"]
  g["No coverage threshold<br/>report posted with continue-on-error<br/>--fail-fast hides failures<br/>no random order"]
  e["No integration or E2E tests<br/>sso, integrity, pinning fork: 0 tests"]
  t ~~~ g ~~~ e
  class g,e hot
  {HOT}'''
    d["a12-target"] = f'''flowchart TD
  g["Coverage gate on changed files<br/>start 70%, ratchet up"]
  h["Random order, full failure list<br/>every shared package has tests"]
  p["Parity net: goldens, recorded fixtures,<br/>both-paths tests, golden names file"]
  e["E2E on real devices:<br/>{a['test_e2e']}<br/>nightly on SIT, gate on release candidates"]
  g ~~~ h ~~~ p ~~~ e
  class g,h,p,e good
  {GOOD}'''
    d["a13-today"] = f'''flowchart TD
  l["Three lint sets:<br/>strict_lint.yaml (1,176 lines),<br/>very_good_analysis, flutter_lints"]
  c["CI: format, analyze --fatal-infos,<br/>pubghost (dead code allowed)"]
  r["No dependency rules:<br/>{a['edges']} cross-feature imports allowed<br/>shared_data imports flutter/material"]
  b["Review: Copilot + Atlas webhook<br/>copilot-instructions.md only<br/>no .claude/rules, no CODEOWNERS"]
  l ~~~ c ~~~ r ~~~ b
  class l,r hot
  {HOT}'''
    d["a13-target"] = f'''flowchart TD
  l["One lint set for every package"]
  c["tool/arch_check.dart with a ratchet:<br/>feature-boundary, domain-purity,<br/>dto-in-presentation, flutter-in-shared_data"]
  b["AGENTS.md + .claude/rules<br/>mr-review skill, CODEOWNERS"]
  ci["Checks run on every PR,<br/>not only *.dart changes"]
  l ~~~ c ~~~ b ~~~ ci
  class l,c,b,ci good
  {GOOD}'''
    d["a14-today"] = f'''flowchart TD
  s1["manual dispatch<br/>(tag, version typed by hand)"]
  s2["approval = job step<br/>2 of {'8' if N=='GENFI' else '9'} people, GH_PAT"]
  s3["Flutter 3.35.0<br/>copied into 37 places"]
  s4["{'21' if N=='GENFI' else '31'} --dart-define per platform"]
  s5["build --obfuscate + R8<br/>proguard-rules.pro missing"]
  s6["sign (base64 keystore secret)"]
  s7["Play internal + TestFlight{'<br/>Android Firebase path is dead' if N=='GENFI' else ''}"]
  s8["symbols -> Crashlytics, Datadog<br/>{'iOS dSYM path wrong' if N=='GENFI' else 'no --version on the Datadog upload'}"]
  s1 --> s2 --> s3 --> s4 --> s5 --> s6 --> s7 --> s8
  sd["Side door:<br/>{'agent_tools_prod_release_build.yaml' if N=='GENFI' else 'are-tracker-prod-deployment-build.yml'}"] -->|"no approval"| sa["prod-signed APK + IPA"]
  class s2,s3,s5,s8,sd,sa hot
  {HOT}'''
    d["a14-target"] = f'''flowchart TD
  s1["dispatch from master or release-*<br/>version from the tag"]
  s2["prod environment: release refs only<br/>+ 2-approval step (App token)"]
  s3["one toolchain (mise.toml)"]
  s4["defines from one file<br/>no secret the backend relies on"]
  s5["build + R8 explicit<br/>reviewed keep rules"]
  s6["protect + register (RASP slot)"]
  s7["sign; fail without mapping.txt"]
  s8["Play staged rollout<br/>iOS phased release"]
  s9["symbols with --version<br/>to Crashlytics and Datadog"]
  s1 --> s2 --> s3 --> s4 --> s5 --> s6 --> s7 --> s8 --> s9
  rw["reusable workflows:<br/>checks, build-android, build-ios, distribute"]
  s9 ~~~ rw
  class s1,s2,s3,s4,s5,s6,s7,s8,s9,rw good
  {GOOD}'''
    d["a15-today"] = f'''flowchart TD
  pr["PR"]
  c0["runs only when *.dart changes<br/>(.github, pubspec, Gradle, iOS: no checks)"]
  c1["format"]
  c2["analyze --fatal-infos"]
  c3["pubghost (dead code allowed)"]
  c4["tests --fail-fast<br/>(whole package coverage)"]
  c5["coverage comment<br/>continue-on-error, no minimum"]
  pr --> c0 --> c1 --> c2 --> c3 --> c4 --> c5
  nt["ui_catalog, crash_reporting, myshaf:<br/>no paths-filter key, never tested"]
  class c0,c3,c4,c5,nt hot
  {HOT}'''
    d["a15-target"] = f'''flowchart TD
  pr["PR"]
  c0["workflow-lint + Codacy<br/>(every PR, no path filter)"]
  c1["format + one lint set"]
  c2["arch_check ratchet"]
  c3["generated files fresh"]
  c4["tests, random order,<br/>full failure list"]
  c5["coverage gate on changed files<br/>(required check)"]
  c6["review: Copilot + mr-review skill<br/>CODEOWNERS on guardrail files"]
  pr --> c0 --> c1 --> c2 --> c3 --> c4 --> c5 --> c6
  class c0,c1,c2,c3,c4,c5,c6 good
  {GOOD}'''
    deps_nodes = "\n".join(f'  t{i}["{t}"]:::hot' for i, t in enumerate(a["deps"]))
    d["a16-today"] = f'''flowchart TD
  subgraph T["Today"]
    direction TB
{deps_nodes}
  end
  {HOT}'''
    d["a16-target"] = f'''flowchart TD
  subgraph G["Target"]
    direction TB
    g1["Riverpod 3 + Notifier<br/>(upgrade alone, then convert)"]:::good
    g2["freezed 3; current firebase,<br/>markdown and storage packages"]:::good
    g3["every git dependency has an owner<br/>and an upgrade path"]:::good
    g4["pubghost strict: no undeclared imports"]:::good
    g5["alice in dev_dependencies only"]:::good
  end
  {GOOD}'''
    bf = "\n".join(f'  f{i}["{n}<br/>{l} lines"]:::hot' for i, (n, l) in enumerate(a["bigfiles"]))
    d["a17-today"] = f'''flowchart TD
  subgraph T["Six largest files ({a['pilot']})"]
    direction TB
{bf}
  end
  r["{a['routes']}<br/>every route in one file"]:::hot
  {HOT}'''
    d["a17-target"] = f'''flowchart TD
  subgraph G["Target"]
    direction TB
    g1["rules in domain use cases<br/>(pure Dart, unit-tested)"]:::good
    g2["screens under 500 lines:<br/>widgets per section"]:::good
    g3["notifiers hold UI state only"]:::good
    g4["one <feature>_routes.dart per feature<br/>composed in router.dart"]:::good
  end
  {GOOD}'''
    d["a18-today"] = f'''flowchart TD
  six["Six auth clients implement HttpClient<br/>1,508 lines, only OtpHttpClient retries"]:::hot
  kc["Two KeycloakRepository classes<br/>one with the client secret"]:::hot
  ts["Five token stores, one secure storage<br/>colliding keys (mkt, atk, rtk ...)"]:::hot
  cf["collab_form 18,595 lines<br/>CollabFormAppId branches, 1 empty test<br/>imports core undeclared"]:::hot
  dd["Dead: shared_data/document,<br/>onboarding_collab_form"]:::hot
  gen["Generated code 291,420 lines<br/>vs 33,497 hand-written (8.7x), committed<br/>largest file 8,238 lines"]:::hot
  co["core contains Flutter UI;<br/>stream and plain map to json"]:::hot
  six ~~~ kc ~~~ ts
  cf ~~~ dd ~~~ gen ~~~ co
  {HOT}'''
    d["a18-target"] = f'''flowchart TD
  one["One interceptor chain in core<br/>auth strategies per app"]:::good
  kc["One KeycloakRepository<br/>code flow with PKCE, no secret in the app"]:::good
  ts["One TokenStore with namespaced keys"]:::good
  cf["collab_form split by screen<br/>policies injected per app"]:::good
  dd["Dead packages deleted,<br/>undeclared imports declared"]:::good
  gen["Generated code: built in CI<br/>or committed with a freshness check"]:::good
  co["core: pure barrel, no UI"]:::good
  one ~~~ kc ~~~ ts
  cf ~~~ dd ~~~ gen ~~~ co
  {GOOD}'''
    d["a19-today"] = f'''flowchart TD
  w1["test.yaml 'Reveal Secret'<br/>SSH_PRIVATE_KEY, KNOWN_HOSTS<br/>0 runs, disabled by hand"]:::hot
  w2["debugger.yaml<br/>52 secret echoes in 4 jobs<br/>ro_tools environments, still active"]:::hot
  w3["{a['leak_main']}"]:::hot
  w4["{'ARE tracker pipeline: keystore + properties<br/>uploaded as artifact, 156 runs' if N=='GENFI' else 'convent SIT pipeline prints<br/>FIREBASE_API_KEY, 162 runs'}"]:::hot
  how["sed 's/./& /g' puts a space between<br/>characters, so log masking fails"]:::now
  w1 ~~~ w2 ~~~ w3 ~~~ w4
  w4 ~~~ how
  {HOT}
  {NOW}'''
    d["a19-target"] = f'''flowchart TD
  d1["Delete test.yaml, debugger.yaml,<br/>the Reveal-secret step and the keystore upload"]:::good
  d2["{a['leak_main_fix']}"]:::good
  d3["Rotate SSH_PRIVATE_KEY, BRAVO_GCP_SA_KEY,<br/>KEYCLOAK_CLIENT_SECRET, keystore passwords"]:::good
  d4["Prod environments: release refs only<br/>workflow-lint on every PR<br/>(no echo of secrets.*, no keystore artifact)"]:::good
  d5["Retire the ro_tools environments<br/>check bravo-ro-tools-apps too"]:::good
  d1 --> d2 --> d3 --> d4 --> d5
  {GOOD}'''
    P = a["plans"]
    def stage(sid, label, ids, cls):
        nodes = "\n".join(f'    p{i}["{i} {P[i]}"]' for i in ids)
        chain = " ~~~ ".join(f"p{i}" for i in ids)
        return f'  subgraph {sid}["{label}"]\n    direction TB\n{nodes}\n    {chain}\n  end'
    d["a20"] = f'''flowchart LR
{stage("sa", "Stage A: stop the leaks", a["stageA"], "hot")}
{stage("sb", "Stage B: safety net", a["stageB"], "now")}
{stage("sc", "Stage C: architecture", a["stageC"], "good")}
{stage("sd", "Stage D: platform", a["stageD"], "good")}
  sa --> sb
  sb -->|"refactors are<br/>now protected"| sc
  sc --> sd
  class {",".join("p"+i for i in a["stageA"])} hot
  class {",".join("p"+i for i in a["stageB"])} now
  class {",".join("p"+i for i in a["stageC"]+a["stageD"])} good
  {HOT}
  {NOW}
  {GOOD}'''
    qx = a["q_extra"]
    d["a22"] = f'''flowchart LR
  q1["Who owns the plan?"] --> a1["{a['folder']} squad (Agency)<br/>+ one owner for the shared plans<br/>across the four apps"]
  q2["RASP vendor and budget?"] --> a2["one decision for customer-app,<br/>agency-app and ro-tools-apps"]
  q3["Coverage threshold?"] --> a3["start 70% on changed files,<br/>raise over time"]
  q4["Generated code?"] --> a4["291,420 lines committed:<br/>generate in CI, or split the models"]
  q5["{qx[0][0]}"] --> a5["{qx[0][1]}"]
  q6["{qx[1][0]}"] --> a6["{qx[1][1]}"]
  class q1,q2,q3,q4,q5,q6 now
  {NOW}'''
    return d

def main():
    app = sys.argv[1]; a = APPS[app]; out = os.path.join(D, f"{app}-parent"); os.makedirs(out, exist_ok=True)
    d = diagrams(a); assert len(d) == 39, len(d)
    for stem, src in d.items():
        open(os.path.join(out, stem + ".mmd"), "w").write(src.strip() + "\n")
    print(f"{app}: wrote {len(d)} .mmd files to {out}")
    failed = []
    for stem in d:
        r = subprocess.run(["mise", "x", "node@22", "--", "npx", "-y", "@mermaid-js/mermaid-cli", "-p", os.path.join(D, "puppeteer.json"), "-b", "white", "-s", "2",
                            "-i", os.path.join(out, stem + ".mmd"), "-o", os.path.join(out, stem + ".png")], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(os.path.join(out, stem + ".png")): failed.append((stem, r.stderr[-300:]))
    print(f"{app}: rendered {39 - len(failed)}/39", failed)
    if failed or ("--upload" not in sys.argv and "--verify" not in sys.argv): return
    import publish
    page = a["page"]
    if "--verify" not in sys.argv:
        for stem in d:
            v1 = publish.upload(page, stem, open(os.path.join(out, stem + ".mmd"), "rb").read(), "text/plain")
            v2 = publish.upload(page, stem + ".png", open(os.path.join(out, stem + ".png"), "rb").read(), "image/png")
            if v1 != 1: print(f"  WARNING {stem}: attachment version {v1}, macro expects 1")
    s = publish.req("GET", f"/rest/api/content/{page}?expand=body.storage")["body"]["storage"]["value"]
    macros = re.findall(r'<ac:parameter ac:name="filename">([^<]+)</ac:parameter><ac:parameter ac:name="revision">(\d+)', s)
    atts = publish.req("GET", f"/rest/api/content/{page}/child/attachment?limit=200&expand=version")["results"]
    names = {x["title"]: x["version"]["number"] for x in atts}
    bad = [(f, r) for f, r in macros if names.get(f) != int(r) or f + ".png" not in names]
    print(f"{app}: {len(macros)} macros, {len(atts)} attachments, mismatches: {bad}")

if __name__ == "__main__": main()
