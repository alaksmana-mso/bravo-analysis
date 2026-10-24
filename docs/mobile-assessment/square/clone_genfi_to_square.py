#!/usr/bin/env python3
"""Create the missing SQUARE plan pages from their GENFI twins (shared monorepo plans).
Rewrites titles, priorities, cross-references and app-specific 'today' facts; strips the
mermaid-cloud macros because the GENFI/SQUARE pages have no diagram attachments.
Usage: clone_genfi_to_square.py  (idempotent: skips a title that already exists)."""
import sys, re, json, html
sys.path.insert(0, "/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams")
import publish
SQUARE_PARENT = "2875260970"; SPACE = "EA"
TITLE_MAP = {  # GENFI title -> SQUARE title
 "GENFI plan 01: Security": "SQUARE plan 01: Security", "GENFI plan 02: CI/CD": "SQUARE plan 02: CI/CD",
 "GENFI plan 03: Logging and crashes": "SQUARE plan 03: Logging and crashes", "GENFI plan 04: Testing": "SQUARE plan 05: Testing",
 "GENFI plan 05: Networking": "SQUARE plan 06: Networking", "GENFI plan 06: Lint and guardrails": "SQUARE plan 07: Lint and guardrails",
 "GENFI plan 07: Layering": "SQUARE plan 08: Layering", "GENFI plan 08: State management": "SQUARE plan 09: State management",
 "GENFI plan 09: Repo layout": "SQUARE plan 10: Repo layout", "GENFI plan 10: Feature flags": "SQUARE plan 11: Feature flags",
 "GENFI plan 11: Analytics wrapper": "SQUARE plan 04: Analytics wrapper", "GENFI plan 12: Design system": "SQUARE plan 12: Design system",
 "GENFI plan 13: Dependency injection": "SQUARE plan 13: Dependency injection"}
JOBS = [
 ("2875392203", "SQUARE plan 06: Networking", [
   ("Priority 5 of 13.", "Priority 6 of 13."),
   ("The same page exists under the SQUARE assessment", "The same page exists under the GENFI assessment"),
   ("adapted for GENFI", "adapted for SQUARE"),
   ("Owner: GENFI squad", "Owner: Agency squad (one change for GENFI and SQUARE)"),
   ("GENFI has one HttpClient provider override.", "GENFI has one HttpClient provider override. SQUARE (are_tracker/lib/main.dart lines 211-238) overrides three: HttpClient.provider, HttpClient.authProvider and HttpClient.krakendHttpClientProvider, and signs in through Keycloak (KeycloakConfig and SsoConfig are overridden there too)."),
 ]),
 ("2875392224", "SQUARE plan 07: Lint and guardrails", [
   ("Priority 6 of 13.", "Priority 7 of 13."),
   ("The same page exists under the SQUARE assessment", "The same page exists under the GENFI assessment"),
   ("adapted for GENFI", "adapted for SQUARE"),
   ("Owner: GENFI squad", "Owner: Agency squad (one change for GENFI and SQUARE)"),
 ]),
 ("2874998913", "SQUARE plan 13: Dependency injection", [
   ("adapted for GENFI", "adapted for SQUARE"),
   ("104 static final provider in agent_tools; 96 StateNotifierProvider.", "103 static final provider in are_tracker; 88 StateNotifierProvider (82 StateNotifier classes)."),
   ("main.dart overrides five HttpClient variants (default, auth, Krakend, chat gateway, non-auth Krakend), NetworkConfig, the remote-config Notifier instance and CrashReporter.instance (a static, replaced at main.dart:32).",
    "are_tracker/lib/main.dart overrides nine providers (lines 211-238): AppConfig, three HttpClient variants (default, auth, Krakend), KeycloakConfig, SsoConfig, NetworkConfig, PlacesConfig and secure storage. No static is replaced there, but CrashReporter.instance (3 uses) and NavigationService.instance (5 uses) are read as singletons."),
   ("Static singletons exist beside Riverpod: CrashReporter.instance, the remote-config service instance (GENFI), AliceInspector.", "Static singletons exist beside Riverpod: CrashReporter.instance, NavigationService.instance, DatadogSdk.instance and FirebaseCrashlytics.instance read directly."),
   ("Owner: GENFI squad", "Owner: Agency squad (steps 1, 2 and 4 are one change for GENFI and SQUARE; step 3 is per app)"),
 ]),
]
def main():
    existing = {p["title"] for p in publish.req("GET", f"/rest/api/content/{SQUARE_PARENT}/child/page?limit=50")["results"]}
    for src, title, edits in JOBS:
        if title in existing: print("skip, exists:", title); continue
        s = publish.req("GET", f"/rest/api/content/{src}?expand=body.storage")["body"]["storage"]["value"]
        n_macros = len(re.findall(r'<ac:structured-macro[^>]*ac:name="mermaid-cloud".*?</ac:structured-macro>', s, re.S))
        s = re.sub(r'<ac:structured-macro[^>]*ac:name="mermaid-cloud".*?</ac:structured-macro>', "", s, flags=re.S)
        for old, new in edits:
            for cand in (old, html.escape(old, quote=False), old.replace("'", "&rsquo;")):
                if s.count(cand) == 1: s = s.replace(cand, html.escape(new, quote=False) if cand != old else new); break
            else:
                if old.startswith("Owner:"): print("  optional edit skipped:", old[:40]); continue
                raise SystemExit(f"{title}: edit not found exactly once: {old[:60]}")
        for g, q in TITLE_MAP.items():
            s = s.replace(f'ri:content-title="{g}"', f'ri:content-title="{q}"').replace(g, q)
        s = s.replace("Genfi mobile app assessment", "Square mobile app assessment")
        body = {"type": "page", "title": title, "space": {"key": SPACE}, "ancestors": [{"id": SQUARE_PARENT}],
                "body": {"storage": {"value": s, "representation": "storage"}}}
        r = publish.req("POST", "/rest/api/content", json.dumps(body).encode(), {"Content-Type": "application/json"})
        print(f"created {r['id']} {title} (stripped {n_macros} diagram macros, {len(s)} chars)")
if __name__ == "__main__": main()
