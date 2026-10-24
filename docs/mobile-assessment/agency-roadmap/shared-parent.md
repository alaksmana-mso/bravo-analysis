## What this page is

The four agency apps (GENFI, SQUARE, MyShaf, MY BISPRO) live in one monorepo, `bfi-finance/bravo-agency-app`, with one CI setup and 15 shared packages. Most of the improvement work is therefore done once for all of them. This page holds the phase pages that are shared: each child page below lists the steps of one phase, with a column that says which app or package each step touches.

The two app roadmaps, GENFI roadmap: step by step and SQUARE roadmap: step by step, link to these shared phase pages and hold their own pages only for the phases that differ per app (approved deltas, the pilot feature, and the other features).

The method is the same as the BFI customer app's roadmap (Mobile roadmap: step by step under BFI Mobile App Assessment): steps ordered by risk to users, one class per step (A no app change, B same behaviour, C behind a switch flag, D approved delta, E backend-coupled), one risky change per release, and a parity net that must stay green.

## Shared phases

| Phase | Page | Classes | Jira epic |
| --- | --- | --- | --- |
| 0 | Agency phase 0: Close the leak | A | |
| 1 | Agency phase 1: Safety net first | A | |
| 2 | Agency phase 2: Seams with the same behaviour | B | |
| 4 | Agency phase 4: Network chain behind a switch flag | C, E | |
| 5 | Agency phase 5: Move call sites, per app | B | |
| 6 | Agency phase 6: Riverpod 3 upgrade on its own | B | |
| 8 | Agency phase 8: Packages, move only | B | |
| 10 | Agency phase 10: Platform | C, D | |

Phases 3, 7 and 9 are per app and sit under each app's roadmap page.

## Apps in the monorepo

| App | Folder | Store name | Users | Assessment |
| --- | --- | --- | --- | --- |
| GENFI | `agent_tools/` (convent flavour) | Agent Tools GENFI App | external agents | Genfi mobile app assessment |
| MyShaf | `agent_tools/` (Sharia flavour) | MyShaf | external agents (Sharia) | covered by the GENFI pages |
| SQUARE | `are_tracker/` | SQUARE (ARE Tracker) | BFI field staff | Square mobile app assessment |
| MY BISPRO | `mybispro/` | MY BISPRO | BFI staff (Sharia) | no assessment yet; shared steps apply |

Facts on this page and its children were checked on 24 Oct 2026 against `bravo-agency-app` `master` @ `1e50b819` (22 Oct 2026), the revision the plan pages used.
