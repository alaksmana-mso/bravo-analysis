# Brief: Mermaid diagrams for the mobile plan pages

Each Confluence plan page gets ONE Mermaid diagram per `## ` section (8 per plan). The diagram goes directly
under the section heading, as an overview picture of that section's content.

Source of truth for content: /Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/plans/ordered/NN-*.md
(read the whole plan first). Diagrams must reflect what the plan actually says: same numbers, same file
names, same step numbers. Do not invent facts. You may look at the BFI repo
"/Users/mac-6000202/Documents/BFI_GITHUB/squads/Customer Mobile Apps/bravo-customer-app" read-only if needed.

Sections (exact h2 text) in every plan:
Goal · Where we are today · Target (what Jago does, adapted for BFI) · Plan · Done when · Effort and owner ·
Depends on / related plans · Risks

Good diagram types per section (pick what fits, vary them):
- Goal: before -> after flowchart (today vs target), 6–10 nodes.
- Where we are today: flowchart of the current structure/data flow with counts in node labels, or a pie of a real breakdown.
- Target: flowchart or classDiagram of the target design (ports/adapters, layers), or a sequenceDiagram of the new flow.
- Plan: flowchart TD of the numbered steps with dependencies (step -> step), grouped in subgraphs by sprint/phase if the plan says so.
- Done when: flowchart of checks as gates (e.g. "CI fails if X") or a stateDiagram-v2 of the done states.
- Effort and owner: flowchart showing owners -> work items with sizes (S/M/L, sprints).
- Depends on / related plans: flowchart LR with THIS plan highlighted and the related plans as "Mobile plan NN: Title" nodes, edges labelled with what flows.
- Risks: flowchart LR risk -> mitigation pairs (one subgraph or pair per row of the risk table).

Allowed diagram types ONLY: flowchart, sequenceDiagram, stateDiagram-v2, classDiagram, pie.
No gantt, mindmap, timeline, quadrantChart, journey, C4, block, xychart.

Mermaid rules (to render in the Confluence add-on and in mermaid-cli 12):
- Quote any label containing ( ) [ ] { } : ; / , # & or quotes: A["text (like this)"]. Use <br/> for line breaks.
- No `call`, `end`, `class`, `style`, `default` as node IDs or classDef names. Use IDs like s1, g2, r3.
- No HTML other than <br/>. No emojis. Keep each label short (max ~6 words per line).
- Max ~18 nodes per diagram. Readable at page width. Prefer flowchart LR for pipelines, TD for step lists.
- Optional emphasis: `classDef hot fill:#ffe1e1,stroke:#c00` / `classDef good fill:#e3f5e1,stroke:#2a7` / `classDef now fill:#fff4cc,stroke:#b80`.
- Plain English, matching the page's plain-language style.
- No secret values. No DK config values.

Files: write to /Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams/NN/ :
- 01-goal.mmd, 02-today.mmd, 03-target.mmd, 04-plan.mmd, 05-done.mmd, 06-effort.mmd, 07-related.mmd, 08-risks.mmd
- manifest.json: [{"file":"01-goal.mmd","heading":"Goal"}, {"file":"02-today.mmd","heading":"Where we are today"}, ... ] using the exact headings above, in order. Check each heading really exists as an h2 (`## `) line in the plan file; if a plan's heading differs, use the plan's exact text.

Render EVERY file to check it is valid (this also makes the PNG we upload):
  cd /Users/mac-6000202/Documents/BFI_GITHUB/bravo-analysis/docs/mobile-assessment/diagrams
  mise x node@22 -- npx -y @mermaid-js/mermaid-cli -p puppeteer.json -b white -s 2 -i NN/01-goal.mmd -o NN/01-goal.png
A file that fails to render must be fixed. Then LOOK at 2–3 of the PNGs per plan (Read tool on the png) to check they are readable and not cramped; fix if not.

Do NOT publish to Confluence. Do NOT edit the plan markdown files.
