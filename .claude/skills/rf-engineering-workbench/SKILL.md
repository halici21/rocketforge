---
name: rf-engineering-workbench
description: RocketForge's application-level design authority — the CAD/CAE-style shell grammar (model browser / engineering viewport / inspector / analysis dock), workspace composition, card-chrome discipline, and progressive disclosure. Use when designing or redesigning any RocketForge page, workspace, or the application shell itself — the home page, a workspace layout, a panel/dock decision, or "make this feel more like an engineering tool." Does not own scientific semantics, QML implementation, plot/table internals, or screenshot QA — see below.
---

# RocketForge engineering workbench

This is the design authority for **composition**: what goes where, how much
chrome surrounds it, and what commands the reader's attention first. It does
not decide whether a number is correct, how QML is written, or how a chart is
drawn — those are `rf-scientific-ui-contract`, `rf-qml-architecture`, and
`rf-scientific-visualization`. Read [Ownership](#ownership) before you start.

RocketForge's target character is instrumentation, not a website. Ground every
decision in that: this is a tool an engineer looks at for hours a day while
solving a real chamber, not a page a visitor scans for thirty seconds.

## The one page you must read first

`references/RF_WORKBENCH_GRAMMAR.md` has the accepted composition grammar, the
proven Rocket Performance pilot pattern in full, the reasons the previous
generation of pages read as forms, and the exact rules that catch a regression
back into a dashboard. It is not optional background — the rules in it are
what actually gets enforced.

## Why this skill exists

Rocket Performance went through a full pilot: an audit of 27 real captures
before any code changed, a redesign to a three-zone composition (input rail /
engineering canvas / result rail, plus a quiet model trace), and a
field-by-field proof that not one scientific result moved. That pilot is
accepted and its report is the primary source for the grammar in this skill.
Every other workspace in RocketForge — Thermochemistry, Line, Fluid
Properties, Trade Study, Engine Design — still reads as a form beside a
result table, which is the exact defect the pilot fixed once already. This
skill exists so the next redesign starts from what was learned, instead of
re-deriving it from a blank page and drifting toward a generic dashboard on
the way.

## The failure mode this skill exists to prevent

Left to its own defaults, an agent asked to "redesign" a RocketForge page
reaches for what it has seen most: a SaaS dashboard. Equal-sized metric
cards, a permanent chart, a welcome banner, a card grid. That is wrong here
for a specific reason, not a stylistic one — every RocketForge page already
computes a real physical object (a chamber, a nozzle, a pipe, a design
space), and a card grid throws that object away and replaces it with a
list of its outputs. The audit that started the Rocket Performance pilot
named this precisely: *"the workspace computes a nozzle and never shows
one."* Read the failure mode as a diagnosis, not a taste preference, and the
fix follows: put the object back.

## Composition, in one line

```
ENGINEERING OBJECT  →  PRIMARY RESULTS  →  CONTEXTUAL CONTROLS  →  SECONDARY STATE  →  TRACE / PROVENANCE
```

Every workspace has its own object (see `rf-propulsion-visual-grammar` for
what each domain's object actually is and what it may truthfully show).
Inputs are quieter than the object; the object is quieter than the primary
result; provenance is quietest of all and lives in one line, not a wall of
text. The full reasoning, the pixel-adjacent guidance (not hard formulas),
and the responsive rule for the 1366×768 floor are in the reference doc.

## What this skill explicitly rejects

State these plainly when a request drifts toward them, and route to the
grammar instead of complying by default:

- A homepage or workspace built from equal-sized KPI cards.
- A permanent chart or table where no analytical question is being asked
  (`rf-scientific-visualization` owns exactly when a plot earns its place).
- News/activity widgets, oversized welcome copy, decorative gradients.
- Restyling every page to look identical regardless of what it computes —
  each workspace's centerpiece is specific to its own physics.
- Chasing "more technical" by adding chrome: more borders, more uppercase,
  more badges, harder shadows. Technical character comes from restraint and
  hierarchy, not decoration — see the soft-industrial language section of
  the reference doc.

Any of the above being avoided is not, by itself, evidence the result is
finished. A typography/colour/contrast change made in the name of
restraint still needs an accessibility pass (`qt-ui-design`, `design-review`)
before it ships — say so explicitly rather than treating "it looks quieter
now" as the same claim as "it still passes contrast." See "Restraint is not
the only thing at stake" in the reference doc.

## Ownership

**This skill owns:** page/workspace/shell composition, the object-first
grammar, card and chrome discipline, progressive disclosure, responsive
behaviour of the *layout* (not of any one chart), and the soft-industrial
visual language (spacing, radius, motion restraint, typography scale as
applied to layout — token *values* live in `ui/theme/`, this skill only says
how to use them).

**This skill explicitly does not own:**
- Whether a displayed number, label, or state is scientifically honest —
  that is `rf-scientific-ui-contract`.
- What a workspace's schematic centerpiece is allowed to draw and claim —
  that is `rf-propulsion-visual-grammar`.
- How QML is written, component lifecycle, memory, or performance — that is
  `rf-qml-architecture` (RocketForge-specific) and `qt-qml` /
  `qt-ui-design` / `qt-qml-review` (general Qt6 authority).
- Plot and table internals, when a chart earns its place, chart-type
  selection — that is `rf-scientific-visualization`.
- Verifying a finished screen against captures — that is `rf-visual-qa` and
  `design-review`.

When a request needs more than one of these, say so and pull in the other
skill rather than improvising its territory.
