# Brief for writing the mobile improvement plans

Parent page: Confluence "Mobile development assessment" (EA/2831057205). Its markdown source is
/Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/mobile-assessment.md — READ IT FIRST.
Each row of its "Side-by-side comparison" table gets one plan page.

Repos (read-only, do not modify, no git writes):
- BFI app: "/Users/mac-6000202/Documents/BFI_GITHUB/squads/Customer Mobile Apps/bravo-customer-app" (master @ 190e1d20). Flutter, Riverpod 2.6, melos workspace: digital/, data/customer/, shared_lib/core/.
- Jago reference (DK, another company): /Users/mac-6000202/Documents/DK_GITLAB/digital_banking_app. Cite paths and describe the pattern in your own words. Do NOT paste DK code longer than a few lines, and NEVER copy DK config values, keys, tokens, app IDs or certificates.

Decisions already made: keep Riverpod (migrate StateNotifier -> Notifier/AsyncNotifier). Do not propose bloc.

Writing style (mandatory): plain English, short sentences, plain words. One idea per sentence. Bullets and tables over long paragraphs. No jargon without a one-line explanation. No secret values anywhere.

Markdown limits (Confluence converter): NO nested lists (a sub-bullet gets flattened into its parent). Use ### headings, flat bullets, numbered lists, and tables instead. Code blocks are fine (keep them short; BFI-side Dart sketches are welcome).

Each plan file uses exactly this structure:

## Goal
1–3 sentences. What good looks like.

## Where we are today
Facts from the BFI repo with file paths and counts. Verify each number yourself with grep/find (quote globs: --include='*.dart').

## Target (what Jago does, adapted for BFI)
The Jago pattern with paths, then how it maps to Riverpod/BFI. Say what NOT to copy from Jago.

## Plan
Numbered steps. Each step is one PR or a small set of PRs. Per step: what changes, which files/packages, and how to check it. Order so the app keeps shipping every sprint (no big-bang rewrite).

## Done when
Measurable checks (e.g. "0 direct FirebaseAnalytics calls outside app/analytics/", "CI job X fails a PR that ...").

## Effort and owner
T-shirt size from the parent table, a rough sprint count, and suggested owner (Customer Mobile Apps squad unless clearly SRE/Security).

## Depends on / related plans
Links by title to other plans in this set.

## Risks
Short table: risk | mitigation.

Plan titles (use these exact titles; the file name is given in your task):
01 Repo layout · 02 Layering · 03 State management · 04 Dependency injection · 05 Analytics wrapper ·
06 Logging and crashes · 07 Feature flags · 08 Networking · 09 Security · 10 Design system · 11 Testing ·
12 Lint and guardrails · 13 CI/CD
Page titles on Confluence will be "Mobile plan NN: <title>". Refer to other plans by that page title.

Length: 120–250 lines of markdown per plan. Concrete beats long.
