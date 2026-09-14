---
name: rf-propulsion-visual-grammar
description: Rules for what each RocketForge workspace's engineering schematic is allowed to draw and claim -- chamber/nozzle for Rocket Performance, reactants-to-products for Thermochemistry, inlet-to-outlet for Line, state for Fluid Properties, design space for Trade Study, real component topology for Engine Design. Use whenever you are drawing, redesigning, or reviewing a workspace's central schematic or deciding what geometry, annotation, or honesty label it needs. Does not own layout/chrome (rf-engineering-workbench), plot/table choices (rf-scientific-visualization), or whether a displayed number is honest (rf-scientific-ui-contract, though the two work together closely).
---

# RocketForge propulsion visual grammar

A schematic earns trust by never claiming more than the model behind it
solved. This skill exists because that boundary is easy to cross by accident
-- a nicer-looking nozzle curve, a smoother flame, a filled-in phase diagram
-- and once crossed, the picture is lying about the physics even though every
number next to it is still correct.

## The one rule under everything

**A schematic may draw only what its own state carries.** Not what would be
plausible. Not what a real engine of that kind usually looks like. If the
production model has not solved a bell contour, a residence time, a
saturation curve, or a component that does not exist in the codebase, the
drawing must not imply one exists -- geometry, colour gradient, particle
effect, or label.

This is not an aesthetic constraint to work around with a clever rendering.
It is the same constraint the Rocket Performance canvas
(`ui/pages/rocketperformance/PerfNozzleCanvas.qml`) already lives inside, and
it produced a stronger design, not a weaker one: fixing the exit radius and
deriving the throat from the solved area ratio, so a larger expansion ratio
visibly narrows the throat against a constant exit, *is* the physical fact
the drawing is allowed to carry -- and it is the only one.

## Per-workspace object, as of this repository

| Workspace | The object | What it may draw |
| --- | --- | --- |
| **Rocket Performance** | chamber -> throat -> nozzle -> exit | Schematic area expansion from the solved area ratio only. No bell contour, no Rao profile, no cone half-angle, no chamber dimension -- none are solved. |
| **Thermochemistry** | oxidizer + fuel -> equilibrium chamber -> products | The chamber as an equilibrium state, not a combustion process. No flame structure, no reaction-zone geometry, no residence time -- CEA solves an equilibrium state, not a flow field. |
| **Line** | inlet -> straight pipe -> outlet | A straight schematic with solved flow direction, Re, Darcy `f`, and delta-p annotated. No bends, valves, fittings, pumps, injectors, or turbulent eddies -- `engineering.line` v1.0 solves distributed friction in a straight pipe and nothing else. |
| **Fluid Properties** | fluid identity + (T, p) -> state -> properties | The state as reported by the provider (phase, density, enthalpy, transport properties). No phase diagram, no saturation envelope -- unless the provider returns actual sampled boundary data, in which case cite the source explicitly. |
| **Trade Study** | the design space itself | The design space is the object; it does not get a fabricated physical illustration. See `rf-scientific-visualization` for how the space itself is drawn. |
| **Engine Design** | the real, implemented component topology | Only components that exist in the production model. See section "Engine Design: no fictional components" below -- this is the highest-risk workspace for silent invention. |

When a new workspace is added, extend this table before drawing anything for
it -- do not improvise an object for a domain not yet listed here.

## Schematic vs solved, and how to say which

Two different claims, and a drawing must never blur them:

- **Solved geometry**: derived directly from a value the production model
  actually computed (an area ratio, a flow direction, a Reynolds regime).
  Annotate it with the real number.
- **Schematic geometry**: chosen for legibility, not physics (an arbitrary
  axial scale, a fixed exit radius, a straight-pipe aspect ratio picked to
  fit the canvas). It carries no claim to correctness beyond "this is the
  right *kind* of shape."

Every centerpiece needs a permanent, honestly worded label that states which
one the viewer is looking at. Follow the Rocket Performance precedent
exactly in form (not wording -- adapt the words to the domain):

```
SCHEMATIC -- AREA EXPANSION ONLY, NOT A SOLVED CONTOUR
```

Suggested wording per domain (adapt to the actual model, verify against the
current implementation before using verbatim -- these are starting points,
not a fixed catalogue):

- Line: `SCHEMATIC -- STRAIGHT LINE, NOT DRAWN TO SCALE`
- Thermochemistry: `EQUILIBRIUM STATE SCHEMATIC, NOT A REACTION-FLOW SOLUTION`
- Fluid Properties: `STATE REPRESENTATION, NOT A COMPUTED PHASE DIAGRAM`
- Engine Design: `SYSTEM SCHEMATIC -- IMPLEMENTED COMPONENTS ONLY`

The label is not decoration and not a legal disclaimer to be shrunk into
invisibility. Screenshot review (`rf-visual-qa`) checks it is legible, not
merely present -- an early Rocket Performance draft put this exact label in
the page's dimmest text token and had to be corrected.

## An unsolved state needs its own outline, not a blank canvas

`rf-engineering-workbench` already covers empty-state composition. This
skill covers what the outline drawn in that empty state may claim: nothing
solved, so nothing numeric. Keep any placeholder proportion **internal** to
the drawing component and unreachable from the property that carries a real
result -- the Rocket Performance canvas enforces this by giving the
placeholder its own internal ratio (`placeholderRatio`) that a caller cannot
supply, so an invented shape can never occupy the property a solved result
uses. Give the placeholder its own, weaker label
(`UNSOLVED OUTLINE -- ILLUSTRATIVE, NOT AN AREA RATIO` was the Rocket
Performance wording) rather than reusing the solved-state label.

## Engine Design: no fictional components

This is the workspace where the temptation to invent is strongest, because a
propulsion engine visually "wants" a pump, a turbine, a valve, a feed
network. Render only what the production component model actually
implements today. Read `rocketforge/engineering/` (or the current component
registry) before drawing a single node -- do not draw from general knowledge
of what rocket engines contain.

If a future connection point is worth showing for product-direction reasons,
it must be visually and semantically unmistakable as **not implemented** --
distinct treatment (not just a subdued colour), no numerical state at all,
and ideally no solved-looking annotation near it whatsoever. When in doubt,
omit it rather than gesture at it.

### Verify each component individually, not the workspace as a whole

A live evaluation of this skill found a real failure mode: an agent that
did read `rocketforge/engineering/` first still classified a component as
"real" because its *name* appeared somewhere in the tree -- in a UI
registry's list of node types, or inside another module's docstring -- and
mistook that appearance for confirmation. In one traced case the module
`propellants.py` states outright that injector geometry is "deliberately
absent" and "belong[s] to `engineering.injector`," a module that does not
exist; the agent read that exact sentence, and still went on to call the
injector one of the "grounded" components with "real solver code."

A name appearing in a *disclaimer about what is absent* is negative
evidence, not positive evidence -- the opposite of what it was read as.
Checking "does `rocketforge/engineering/` mention this component" is not
the same question as "does an implementing module or class for this
component exist," and only the second question licenses rendering
something as real. For every component under consideration:

- Confirm there is an actual module, class, or function that computes a
  result for it -- not a registry entry, not a UI placeholder, not a
  mention inside another component's own scope note.
- Treat an explicit "not implemented," "deliberately absent," or
  "placeholder" statement anywhere in the code as authoritative and final
  for that component, even if the same code also contains other language
  that could be read as suggestive of support.
- When a written investigation of the codebase and a later claim about
  what may be rendered disagree with each other, the investigation wins --
  state the contradiction and revise the claim, rather than letting an
  earlier draft's conclusion survive past evidence that undercuts it.

Do not chase the "beautiful 3D reference engine" temptation: a
scientifically fictional turbopump rendered gorgeously is a worse outcome
than a plain 2D box for a component that does not exist, because the
gorgeous rendering is what makes the fiction convincing. See
`rf-qtquick3d-viewport` for the same rule applied to a future 3D viewport,
if one is ever built.

## No fake CFD, ever

Across every workspace: no plume, no flame contour, no continuous Mach
field, no velocity vectors -- unless the values plotted are actually sampled
from a real field solution. RocketForge's solvers are 0-D/1-D (equilibrium
chemistry, ideal-gas expansion, distributed pipe friction); none of them
produce a field. A gradient fill that *looks* like a flow field is exactly
as false as a number that is wrong, even though no number on the page is
wrong.

## Ownership

**This skill owns:** what a schematic may draw, what it must claim in its
honesty label, and the placeholder/unsolved-state drawing rule, for every
propulsion domain in this repository.

**This skill explicitly does not own:**
- Where the schematic sits on the page, how much of the view it commands, or
  chrome around it -- `rf-engineering-workbench`.
- Whether a *number* next to the schematic is stale, superseded, or
  mislabeled -- `rf-scientific-ui-contract` (the two must agree: a stale
  schematic and a stale number are the same failure seen from two sides).
- Chart/table/design-space visualization -- `rf-scientific-visualization`.
- QML implementation of the drawing (Canvas vs Shape, repaint discipline,
  animation) -- `rf-qml-architecture` and `qt-qml`.
