# RF workbench grammar

The composition rules behind `rf-engineering-workbench`, with the evidence
that produced them.

---

## 1. The proven pattern: Rocket Performance

The accepted pilot (`docs/design/ROCKET_PERFORMANCE_VISUAL_PILOT.md`,
`docs/engineering/implementation/ROCKET_PERFORMANCE_VISUAL_ARCHITECTURE_PILOT.md`)
rebuilt one workspace from a 15-row uniform readout list into:

| Zone | Contents | Width behaviour |
| --- | --- | --- |
| **Input rail** | chamber source, gas model, nozzle, ambient, engine size | pinned (236-268 px), not proportional |
| **Engineering canvas** | the schematic gas path, its stations, the exit relation | fills remaining width |
| **Result rail** | Isp first (largest), then Cf/c*/c_eff/thrust, then term breakdowns | pinned (250-320 px) |
| **Model trace** | model, gamma, ambient, regime, scale, warnings | one line, full width, quietest text in the view |

Read this as a template to adapt, not to clone. The next workspace's object
is not a nozzle -- see `rf-propulsion-visual-grammar` for what it actually is.

### Why the rails are pinned, not proportional

A result rail that grows with the window produces a 2560 px layout where the
numbers drift apart with nothing filling the gap meaningfully, and a
1366 px layout where they collide. Pinning the rails and giving all spare
width to the one element that benefits from it -- the engineering object --
fixes both ends at once.

### Why Calculate must sit outside the scrolling body

At 1366x768 the input rail does not fit its own content. The pre-pilot
design simply clipped the overflow -- recorded as `RESPONSIVE_LAYOUT_BLOCKER`,
because it made the expansion ratio and engine size unreachable and buried
Isp below the fold. Scrolling fixes reach, but the one control that produces
a result must never scroll out of view: pin it below a divider, and scroll
the body behind it.

### Why an overflowing rail must say so

The application's own scrollbar (`ui/components/RFScrollBar.qml`) is quiet
by design -- invisible until touched. That is correct for a rail whose
content fits, and wrong for one whose content does not: at 1366x768 nothing
signalled that Ambient and Engine Size existed below the fold until the user
scrolled by accident. The fix is a property override on the instance
(`policy: ScrollBar.AlwaysOn` while `contentHeight > height`), never a
change to the shared component -- a scrollbar that is always visible
everywhere is chrome, not a cue.

---

## 2. Hierarchy: four levels, not fifteen rows

The pre-pilot Rocket Performance page put fifteen numbers at one type size
and carried the only hierarchy in colour (amber for "important," white for
everything else) -- a colour-only signal, which is both weak and an
accessibility failure. The fix was typographic hierarchy, not more colour:

| Level | Role | Approx. treatment |
| --- | --- | --- |
| 1 | The one number the workspace exists to produce | largest mono, medium weight, first in the result rail |
| 2 | Secondary primary results | one clear step down, regular weight |
| 3 | Symbols, labels, units | small, `textSecondary` |
| 4 | Model trace / provenance | smallest, quietest token, one line |

Never more than four active levels on one screen -- a fifth reads as noise
regardless of how carefully it is chosen. Exact numeric tokens live in
`ui/theme/Typography.qml`; this skill governs how they are assigned to
roles, not their pixel values. Consult `qt-ui-design`'s modular-scale
guidance (its section 1.2) when a workspace's existing scale needs
revisiting -- that is general Qt6 authority this skill defers to rather
than duplicates.

## 3. Card and chrome discipline

`RFPanel` in the Performance tab went from 2 to 0 in the pilot: hairline
dividers (`RFDivider`) and section labels (`RFSectionLabel`) did the same
grouping work without a second border around content that already has one
(the workspace edge). This is not a zero-cards ideology -- the task is
**low chrome, not no structure**. Use a surface only where it serves
interaction, selection, or a genuine visual boundary between unrelated
content; never as decoration around content that is already grouped by
proximity or a divider.

Before adding a panel border, ask what it is doing that spacing and a
divider could not. If the honest answer is "make this feel like a card,"
that is the tell to remove it, not add it.

## 4. Progressive disclosure and the empty state

A refusal is not a dead page. When a workspace has nothing to show -- no
chamber solved yet, no design points run -- the empty state must still read
as an instrument waiting for an input, not a blank page with a paragraph at
the top and a void beneath it. The Rocket Performance empty state was
rewritten from a top-clustered text block into a centred column at a
readable measure, with a dimmed, unsolved outline of the object behind it --
carrying no numbers, because there is nothing solved to annotate, and
labelled so it can never be mistaken for a result (`rf-propulsion-visual-grammar`
owns the exact wording rules for that label).

## 5. Chart/table proportion -- the rule, not the split

**Never default to a 50/50 chart-and-table split.** The proportion is a
consequence of the analytical task, decided per workspace:

- The visualization answers the page's main question -> it dominates.
- A table supports inspection of a visualization already answering the
  question -> it is secondary, and may collapse.
- No analytical question exists at this state -> no default plot at all.

This is `rf-scientific-visualization`'s full territory (chart selection,
Tufte-style data-ink discipline, when a table beats a chart); this skill
only states that proportion follows task, never habit.

## 6. The future CAD/CAE shell target

The application shell (`ui/shell/`, `ui/Main.qml`) already has the bones of
this -- `SideNav`, `WorkspaceHost`, `EngineWorkspace` with its
`EngineSidebar`/`EngineInspector`/`BottomPanel`. The target grammar for a
mature workbench extends that pattern to every workspace, not only Engine
Design:

```
MODEL / MODULE BROWSER
        <->
ENGINEERING VIEWPORT   (the object -- commands ~55-65%+ of attention)
        <->
INSPECTOR

  +  a collapsible, resizable ANALYSIS DOCK along the bottom
```

This is a direction, not a mandate to rebuild every page's shell in one
pass -- see `rf-visual-qa`'s one-workspace-at-a-time discipline. `Engine
Design` already has a real inspector and dock; treat it as the existing
reference implementation to extend, not a separate concern to redesign from
scratch.

## 7. Soft industrial visual language

Target character: CAD precision, scientific calm, aerospace
instrumentation, editorial spacing, soft technical surfaces.

Avoid, specifically because each one is a generic-AI-tell as much as it is a
style mistake (see also `frontend-design`'s calibration notes, reference-only
in this project since it targets web/CSS output -- the *tells* it names are
real regardless of platform):

- Hard black/white contrast everywhere, in place of the graduated surface
  tokens `ui/theme/Theme.qml` already defines (`surface`, `surfaceElevated`,
  `surfaceSubtle`, `surfaceSunken`).
- Uppercase used as a default rather than a deliberate choice for a short
  section label. `qt-ui-design` and this project's own accepted pilot both
  treat it as selective, not structural.
- Dense micro-label walls -- every value does not need a label at the same
  weight as the value itself.
- Giant shadows, excessive corner radius, neon accent colours. RocketForge's
  accent (`Theme.accent`) is a restrained warm tone used for exactly one
  focal signal per view (the solved flow direction, the primary metric) --
  never scattered across multiple elements at once.

"Make this feel more technical" is a request to strengthen hierarchy and
restraint, not to add chrome. Answering it with more borders, more
uppercase, or a monospace face slapped onto prose is the wrong read -- see
the eval in `rf-visual-qa`'s reference doc for the concrete failure case.

### Restraint is not the only thing at stake

Every change in this section -- tightening contrast, reducing colour
saturation, thinning hairlines, narrowing a type scale -- moves the same
pixels that WCAG contrast and legibility rules measure. A live evaluation
of this skill found a real gap here: a proposal that got the hierarchy and
typographic restraint exactly right went to press without checking
contrast at all, while a naive comparison response (with no RocketForge
skill routing) thought to flag it unprompted. Restraint and legibility are
not in tension -- a quieter palette can fail contrast just as easily as a
loud one -- so a *quieter* proposal is not automatically a *safer* one.

Detailed contrast/keyboard/focus mechanics belong to `qt-ui-design`
(design-time rules) and `design-review` (independent audit) per
`DESIGN_SKILL_FOUNDATION_R1_OWNERSHIP.md` -- this skill does not restate
their rules. But whenever a change here touches colour, contrast, or type
size, say so and route to them before calling the composition finished,
the same way a scientific-content change routes to
`rf-scientific-ui-contract`: naming the need for the check is this skill's
job even though performing it is not.

## 8. What "responsive" means here

Every workspace is checked at 2560x1440, 1920x1080, and 1366x768, in both
themes. The floor is 1366x768 because that is where the pre-pilot design
broke (`RESPONSIVE_LAYOUT_BLOCKER`). At the floor:

- Every primary input must be reachable.
- Calculate/Run must be reachable and must never scroll away.
- The primary result must be visible without scrolling.
- The engineering object stays meaningful -- shrink it, do not hide it.
- No text becomes illegibly small; reflow before you shrink type.

Use reflow (rails collapse, dock hides, secondary breakdowns wrap), never
uniform scaling of the whole page.
