**A guide, not a work item.** This page teaches what a design system is and how it will change the way designers and engineers work together on the BFI app. The work itself is in Mobile plan 13: Design system.

## Who this is for

UI/UX designers working on the BFI customer app. No code knowledge needed. After reading, you should be able to:

- Explain what a design system is, in one sentence, and name its three parts.
- Read a token name and know what it controls.
- Set up a Figma file so the app can use your colours, spacing and type directly.
- Review a component in Widgetbook instead of waiting for a test build.
- Know what to ask engineers for, and what they will ask you for.

## What a design system is

One sentence: **a design system is the set of shared decisions, written down once, that every screen is built from.**

It has three parts. Each one builds on the one before.

| Part | What it is | BFI example |
|---|---|---|
| **Tokens** | The smallest decisions: one colour, one spacing step, one font size, one corner radius. Each has a name. | `color.brand.primary`, `spacing.16`, `radius.md` |
| **Components** | Reusable building blocks made from tokens: a button, a text field, a dialog. Each has states and variants. | `DigitalButton`, `DigitalTextField`, `DigitalBottomSheet` |
| **Rules and docs** | How to use the parts: when to use a primary vs a secondary button, how much space between fields, what an error looks like. | The AGENTS.md rules today; Widgetbook and this page tomorrow |

A design system is not a Figma library on its own, and not a code library on its own. It is both, kept in step. The problem today is that they drift apart.

## Where BFI is today

From the app code (`bravo-customer-app`, `master`, 9 Oct 2026):

- There are 32 `Digital*` components (buttons, text fields, dialogs, bottom sheets, chips, search bar, tooltip and more). Engineers use them well: 0 raw Material buttons in feature screens, and 1,040 lines use the shared colours.
- Colours are typed by hand from Figma into one file: 44 named colours, each as a hex code. If a colour changes in Figma, an engineer has to notice and retype it.
- 49 places still use a one-off hex colour instead of a named one. 108 places use a one-off text style.
- There is no Widgetbook. To see a component, you need a test build on a phone.
- There is no link between Figma variables and the code. The "source of truth" is whichever side was updated last.

So the components exist and are used. What is missing is the token layer and the catalogue. That is what Mobile plan 13 builds.

## Tokens, explained

A token is a named decision. Instead of writing `#FF6B00` in ten places, we write `color.brand.primary` once and point at it everywhere. Change the value, and every use changes.

Tokens come in tiers. Material Design 3 uses three. We use the same idea.

| Tier | Question it answers | Example |
|---|---|---|
| **Reference** | What colours and sizes exist at all? The raw palette. | `orange.500 = #FF6B00`, `space.4 = 16` |
| **System** | What do we use them for? The meaning. | `color.brand.primary = orange.500`, `spacing.md = space.4` |
| **Component** | What does this part of this component use? | `button.primary.background = color.brand.primary` |

Why tiers matter to you:

- A rebrand changes **reference** tokens. Nothing else moves.
- A dark mode or a second theme changes **system** tokens. Components do not change.
- A button redesign changes **component** tokens. Screens do not change.

In Figma, tokens are **variables**. A **collection** groups them (colours, spacing). A **mode** gives one variable a different value per context (light and dark, or two brands). Figma can export variables as a file, and a script turns that file into code. That is the link that does not exist today.

## Components, explained

Brad Frost's "atomic design" gives us the words. It is a way of thinking, not a rule book.

| Level | What it is | BFI example |
|---|---|---|
| **Atom** | One thing that cannot be split further | A `DigitalButton`, an icon, a text style |
| **Molecule** | A few atoms that work together | A text field with its label, hint and error message |
| **Organism** | A section of a screen | A loan agreement card, the bottom navigation bar |
| **Template** | A screen layout with placeholder content | The "list with empty state" layout |
| **Page** | A real screen with real content | The loan detail screen |

The design system owns atoms, molecules and some organisms. Features own templates and pages.

Two words engineers will use:

- **Variant**: a different look for the same component, chosen on purpose. Primary vs secondary button. Small vs large.
- **State**: what the component is doing right now. Default, pressed, focused, disabled, loading, error. Every component needs a design for every state it can be in. Missing states are the most common gap between Figma and code.

## What changes when plan 13 lands

| Today | After |
|---|---|
| An engineer reads a hex code off your Figma file and types it in | Figma variables are exported; a script writes the code. No retyping |
| To see a component you need a test build on a phone | You open Widgetbook in a browser and click through every component, variant and state |
| A visual change can slip into a release unnoticed | Golden tests compare a screenshot of each component against a saved reference. A change fails the build until someone approves it |
| Components live inside the app code | Components live in their own package. Another BFI app could use the same kit |
| Rules live in one engineering file | Rules live next to the components, where both designers and engineers read them |

The new loop, in order: you change a variable or a component in Figma; the export runs; the generated code changes; Widgetbook and the golden tests show exactly what moved; an engineer or you approves it; the app picks it up.

## How to work with engineers

### Before a feature

- Use components from the library in Figma. Do not detach instances to tweak them. If a component needs a new variant or state, ask for it to be added to the library first.
- Use variables for every colour, spacing and radius. A detached hex colour cannot be exported.
- Design every state the component can reach: empty, loading, error, disabled, and the longest realistic text (Indonesian strings run long).

### Naming variables

- Name by **meaning**, not by value: `color.text.error`, not `red.600`. The red may change; the meaning will not.
- Use one pattern and stick to it: `category.role.property.state`, for example `color.button.primary.background.pressed`.
- Keep modes only for things that really vary (light and dark). Do not use modes as a way to store alternatives.
- Do not rename a variable that is already in use without telling the engineers. The export maps on names.

### During review

- Review in Widgetbook, not only in Figma. It shows the component as the app will draw it, on the real font and spacing.
- When a golden test fails, someone must look at the before and after image and say "intended" or "bug". Designers are the right people to answer that.

### What engineers will ask you

- "Which token is this?" If the answer is a hex code, it needs a token.
- "What does this look like when it is disabled, loading, or the text is three lines?"
- "Is this a new component, or a variant of an existing one?" Prefer a variant.

## How DK does it with the Jago design system

This is how DK's mobile chapter works with its design library today (from the "Mobile development with DK" session, Aug 2026, and the Jago repository, Oct 2026). It is the clearest picture of where BFI is heading.

### The weekly loop

| Step | Who | What happens |
|---|---|---|
| 1. Refinement | Designers and engineers, weekly | Components are detailed together: design guidelines and technical feasibility in the same discussion. An item moves to "ready for development" only when both sides agree |
| 2. Build | Engineer, with an AI tool | The engineer picks the component in Figma, passes its link to the AI through Figma's MCP connection, and the AI drafts the code. Rules and skills in the repository steer it. Merge-ready code typically takes about four prompts; the remaining effort is testing |
| 3. Missing pieces | AI asks, designer answers | If the Figma component lacks a building block, the AI stops and asks. It does not guess. The designer fills the gap in Figma |
| 4. Review | Designer and engineer | The component appears in Widgetbook with every variant and state. The designer checks it there, not on a phone build |
| 5. Accept | The chapter | Lifecycle: community discussion, refine, develop, review, accept, production |

### What a designer must bring

DK's "add a component" guide lists four inputs. The AI will not start without the first one, and asks for the others rather than inventing them.

| Input | What it is | Why it matters |
|---|---|---|
| The component's Figma link | The main component node: the full matrix of type × state × variant | Always required. This is what gets built |
| The building-block links | The small `_Atom` parts the component is made of (a leading icon, a subline, a trailing button) | They pin down the exact structure. Without them, a composite screenshot gets misread |
| The "explore behaviour" playground | The Figma playground that shows every property, including ones that only appear under a selection | This is the only place conditional properties are visible. One instance never shows them all |
| Usage and accessibility notes | Placement rules that live in annotations, not on the node: "input fields sit on the secondary background" | They drive how the component is shown and constrained |

Lessons DK wrote down after real mistakes: decompose from the atoms, never from a composite image; a sub-part named like an existing component is that component, reuse it; icons are SVG assets from Figma, never a Material stand-in; a showcase background is never invented.

### Figma and code stay linked by name

- Every component in the Jago library records which Figma node it was built from, with a date on which its token bindings were last checked against Figma. Anything the bindings could not settle is written down as "unconfirmed", not guessed.
- The variable bound on a Figma node is the source of truth for which token the code reads. Not a hex match, not an old name.
- Legacy variables are marked "to sunset" on the Figma side and listed, so design knows what to rebind.
- Names are 1:1: a Figma component called `MainButton` is a class called `MainButton` in code.

### Widgetbook with a token inspector

- Widgetbook is built from the repository and published to a web page on every merge. Anyone can open it in a browser. DK's is public: [Jago Widgetbook](https://dk-digital-bank.gitlab.io/clients/digital_banking_app/storybook/web/).
- A **token inspector** lets a designer hover any part of a component and see which tokens it uses: colour, typography, padding, radius, shadow. It works like Figma's inspect mode, but on the real rendered component.
- Designers use it to explore states and themes before anything reaches production.

### What BFI takes from this, and what it does not

| Take | Leave for now |
|---|---|
| The weekly refinement with both sides in the room | The multi-brand matrix. BFI ships one brand |
| The four inputs a designer brings | The token inspector, until a designer asks for it |
| "Ask, do not guess" as a rule for AI and people | The Figma token pipeline, until BFI's Figma file uses variables consistently |
| Widgetbook published on every merge | Any of DK's token values, names or Figma files |
| A Figma-to-code index with verified dates | |

### An open decision: build our own, or adopt DK's library

The DK session floated a third option: BFI adopts the Jago library and joins a shared design community that maintains it together. Mobile plan 13 assumes BFI builds its own package. These are different paths:

| | Build our own (plan 13) | Adopt DK's library |
|---|---|---|
| Look and feel | BFI's own tokens and components | DK's components, themed with BFI tokens |
| Speed | Slower to start; the 32 existing `Digital*` components move into a package | Faster if the components fit; slower if BFI needs many that DK lacks |
| Control | Full | Shared. Changes go through the joint community |
| Risk | Two libraries drift apart | Dependency on another company's roadmap and release cadence |

This is a product and management decision, not a design-system one. It is listed under Open questions on the parent page.

## Glossary

| Word | Meaning |
|---|---|
| Token | One named design decision: a colour, a size, a radius, a font style |
| Variable | Figma's name for a token |
| Collection | A group of variables in Figma, for example all colours |
| Mode | A different value for the same variable per context, for example light and dark |
| Component | A reusable building block made from tokens, with variants and states |
| Variant | A chosen look for a component (primary, secondary, small, large) |
| State | What a component is doing now (pressed, disabled, loading, error) |
| Widgetbook | A small web app that shows every component with controls to switch its variants and states |
| Golden test | A test that compares a screenshot of a component against a saved reference image |
| Theme extension | The Flutter way to hand tokens to components at runtime |
| Code Connect | Figma's feature that links a design component to its code. It does not support Flutter today, so BFI will rely on Widgetbook and naming instead |

## Reading list

Links were checked on 14 Oct 2026. Start with the first group; it takes about an hour.

### Start here (about an hour)

- [Atomic Design, by Brad Frost](https://atomicdesign.bradfrost.com/table-of-contents/) — the free online book. Read chapter 1 ("Designing Systems") and chapter 2 ("Atomic Design Methodology"). Everything else on this page uses its words.
- [Material Design 3: design tokens overview](https://m3.material.io/foundations/design-tokens/overview) — the clearest short explanation of reference, system and component tokens.
- [Figma: guide to variables](https://help.figma.com/hc/en-us/articles/15339657135383-Guide-to-variables-in-Figma) — Figma's own guide to variables, collections and modes.

### Go deeper (half a day)

- [Atomic Design, chapters 3 to 5](https://atomicdesign.bradfrost.com/table-of-contents/) — tools, workflow, and keeping a design system alive.
- [Nathan Curtis at EightShapes](https://eightshapes.com/nathan-curtis/) — his articles on planning and running a design system. Start with "Defining Design Systems".
- [Design Tokens Community Group](https://www.designtokens.org/) — the W3C group that owns the token file format (first stable version 2025.10, backed by Figma, Adobe, Google and others). Skim the technical report; you do not need to read the spec.
- [Tokens Studio: token format](https://docs.tokens.studio/manage-settings/token-format) — how a Figma plugin exports tokens in the standard format. Useful if BFI chooses this plugin for the export.

### For curiosity: the engineering side

- [Widgetbook documentation](https://docs.widgetbook.io/) — what the component catalogue is and how it works.
- [Flutter: golden file tests](https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html) — the mechanism behind "a visual change fails the build".
- [Flutter: ThemeExtension](https://api.flutter.dev/flutter/material/ThemeExtension-class.html) — how tokens reach components at runtime.
- [Figma Code Connect](https://developers.figma.com/docs/code-connect/) — read only to know why we are not using it: it supports React, web components, SwiftUI and Jetpack Compose, not Flutter.

### BFI pages

- [Mobile development with DK](https://bfifinance.atlassian.net/wiki/spaces/EA/pages/2644082973) — the Aug 2026 session notes: DK's design-system workflow with AI, the component lifecycle, Widgetbook and the token inspector, with screenshots.
- [Jago Widgetbook](https://dk-digital-bank.gitlab.io/clients/digital_banking_app/storybook/web/) — DK's live component catalogue. Open it to see what BFI's will look like.
- Mobile plan 13: Design system — the work plan: the package, Widgetbook, golden tests, the optional Figma token pipeline.
- BFI Mobile App Assessment — the parent page with all 13 plans and the overall roadmap.
