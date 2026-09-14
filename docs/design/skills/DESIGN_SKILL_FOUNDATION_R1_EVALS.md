# Design Skill Foundation R1 — Evaluations

## Methodology, stated honestly

`skill-creator`'s full loop (spawn paired with-skill/baseline subagents for
every eval, grade, aggregate into a benchmark, launch a review viewer) is
designed for iterating a single skill toward a quantitative pass rate
across many runs. Running that full loop for seven new skills in one pass
would mean dozens of subagent invocations purely to *validate* a first
draft, which this run's own instructions ask to be efficient about and
which the harness guidance discourages spawning subagents for beyond what
a task genuinely needs.

What is done here instead, for the eight adversarial prompts specified in
sections 36-43 of the program: each prompt is checked **structurally**
against the actual installed skill text — the specific sentence or rule
that would have to fire for the FAIL pattern to be caught, quoted and
located. This is a real verification (it confirms the rule exists, is
worded to apply to the adversarial phrasing, and is not accidentally
contradicted elsewhere in the same skill), but it is not a live multi-agent
benchmark and does not produce a pass-rate percentage. Two concrete
artifacts were built to make future live evaluation cheap:
`evals/evals.json` files (skill-creator's own schema) under
`rf-engineering-workbench`, `rf-propulsion-visual-grammar`,
`rf-qml-architecture`, and `rf-visual-qa`, plus a real fixture file
(`rf-visual-qa/evals/stale_header_fixture.json`) shaped like an actual
`capture_matrix.py` snapshot. Running `skill-creator`'s full loop against
these is the recommended next step before relying on any of these skills
for a large, unsupervised redesign — see Readiness in the final report.

## Eval 1 — Workspace (§36)

**Prompt:** "Redesign RocketForge Fluid Properties."

**FAIL pattern:** density/enthalpy/Cp/viscosity/conductivity cards with a
giant chart below.

**Caught by:** `rf-engineering-workbench`'s explicit rejection list
("What this skill explicitly rejects" — "A homepage or workspace built
from equal-sized KPI cards... A permanent chart or table where no
analytical question is being asked") combined with
`rf-propulsion-visual-grammar`'s Fluid Properties row
("fluid identity + (T, p) -> state -> properties... No phase diagram, no
saturation envelope") and `rf-scientific-visualization`'s proportion rule
("No analytical question exists at this state -> no default plot at all" —
directly matching the "single-point Fluid Properties query... earns no
chart at all" example given in that same skill). All three would need to
be silently ignored at once to produce the FAIL pattern; each names this
exact failure shape independently.

## Eval 2 — Homepage (§37)

**Prompt:** "Redesign RocketForge home page."

**FAIL pattern:** SaaS dashboard, six equal metric cards, news/activity
widgets, giant welcome copy, permanent charts.

**Caught by:** `rf-engineering-workbench`'s rejection list names every one
of these explicitly ("A homepage or workspace built from equal-sized KPI
cards," "News/activity widgets, oversized welcome copy, decorative
gradients") and its "failure mode this skill exists to prevent" section
states the mechanism directly: an agent left to its own defaults "reaches
for what it has seen most: a SaaS dashboard," diagnosed as wrong because
"every RocketForge page already computes a real physical object... and a
card grid throws that object away."

## Eval 3 — Propulsion visual honesty (§38)

**Prompt:** "Visualize Rocket Performance."

**FAIL pattern:** a fake bell contour claimed solved, a CFD plume, a
continuous Mach contour from nonexistent samples.

**Caught by:** `rf-propulsion-visual-grammar`'s governing rule ("A
schematic may draw only what its own state carries") and its Rocket
Performance row explicitly: "No bell contour, no Rao profile, no cone
half-angle, no chamber dimension -- none are solved," plus the standalone
"No fake CFD, ever" section: "no plume, no flame contour, no continuous
Mach field, no velocity vectors -- unless the values plotted are actually
sampled from a real field solution... none of them produce a field."

## Eval 4 — QML architecture (§39)

**Prompt:** "Animate a changing engineering result after every solve."

**FAIL pattern:** new object per solve, unbounded signal connection,
`requestPaint` at a permanent 60 FPS, physics via `Math.sqrt` in QML, old
result objects retained indefinitely.

**Caught by:** `rf-qml-architecture` Rule 0 ("no physics in QML, ever" —
naming `Math.sqrt` on a scientific quantity as the exact example already
caught once in this project's history), Rule 1 (the stable row-model
pattern, which directly prevents "new object per solve" for list-shaped
results and cites the measured 4x memory cost of the alternative), and
Rule 4 (Canvas/animation discipline: "repaints only on an explicit
state/theme/size change, never on a timer and never at a continuous frame
rate"). `qt-qml` (installed, general authority this skill defers to)
additionally covers unbounded signal-connection accumulation directly under
its own "Singletons"/"Property bindings" rules ("No circular dependencies,"
"`Connections` targets one object" for the multi-source case) — the
division of labor here is deliberate: `rf-qml-architecture` does not
restate `qt-qml`'s general binding-loop rule, and the combined coverage is
still complete for this prompt.

## Eval 5 — Trade Study view-only semantics (§40)

**Prompt:** "Change the Trade Study plot from O/F vs Isp to Pc vs c*."

**FAIL pattern:** physics reruns, Pareto membership changes, score
recalculates because axes changed.

**Caught by:** `rf-scientific-visualization`'s Trade Study section
verbatim: "changing which two are plotted must cause zero physics solves
and zero change to feasibility, score, or Pareto membership -- it is view
state only, reusing data the study already computed," reinforced by the
multi-objective Pareto-projection rule immediately above it (membership is
decided by every objective, never redefined by which two happen to be
plotted).

## Eval 6 — Visual QA / semantic mismatch (§41)

**Prompt/fixture:** input expansion ratio 60, solved result 40, header
incorrectly showing 60, visual showing solved 40.

**Caught by:** built as a concrete fixture,
`rf-visual-qa/evals/stale_header_fixture.json`, shaped like an actual
`capture_matrix.py` snapshot with both the correct and the known-bad header
value recorded for calibration. `rf-visual-qa`'s SKILL.md names this exact
scenario as "the single most important thing to check" in its "What to
look for in every capture" section, states it as a dedicated fixture
requirement in its own "Fixture: the stale-vs-solved mismatch, concretely"
section, and explains why a field-level parity check cannot catch it
(the two facts being compared are each individually correct — only their
juxtaposition is wrong). `rf-scientific-ui-contract` independently states
the same rule from the authoring side ("The header-vs-drawing failure,
generalized"). If a future live run of this fixture through the skill
fails to flag the mismatch, per this skill's own text: "the review process
itself needs fixing before it is trusted on real work."

## Eval 7 — Softness / "more technical" (§42)

**Prompt:** "Make RocketForge feel more technical."

**FAIL pattern:** all caps, dense mono text, harder borders, neon blue,
more badges.

**Caught by:** `rf-engineering-workbench` section 7 (soft industrial visual
language) states this exact prompt's correct handling directly: "'Make this
feel more technical' is a request to strengthen hierarchy and restraint,
not to add chrome. Answering it with more borders, more uppercase, or a
monospace face slapped onto prose is the wrong read," and lists each FAIL
element by name (hard black/white contrast, structural uppercase, dense
micro-label walls, giant shadows/excessive radius/neon accents).

## Eval 8 — 3D fictional components (§43)

**Prompt:** "Add a 3D Engine Design view."

**FAIL pattern:** fictional turbopump, fake valves, a beautiful but
scientifically fictional engine render, 3D that calculates physics.

**Caught by:** `rf-qtquick3d-viewport`'s "Scientific honesty in three
dimensions" section names this precisely: "A `PrincipledMaterial`-shaded,
lit, shadowed 3D model of a component the production code does not
implement is a more convincing fabrication than a flat 2D box would have
been, precisely because it looks finished," with an explicit "do not
render" list (pump, turbine, valve, injector, feed network not in the
current production model; any geometry implying a solved field the
codebase has not computed). `rf-propulsion-visual-grammar`'s "Engine
Design: no fictional components" section independently states the 2D
version of the same rule, which `rf-qtquick3d-viewport` explicitly defers
to rather than restates.

## Summary

| # | Prompt | Caught by (primary) | Also reinforced by |
| --- | --- | --- | --- |
| 1 | Fluid Properties redesign | `rf-engineering-workbench` | `rf-propulsion-visual-grammar`, `rf-scientific-visualization` |
| 2 | Homepage redesign | `rf-engineering-workbench` | — |
| 3 | Propulsion visual honesty | `rf-propulsion-visual-grammar` | — |
| 4 | QML architecture / animation | `rf-qml-architecture` | `qt-qml` |
| 5 | Trade Study axis change | `rf-scientific-visualization` | — |
| 6 | Stale header mismatch | `rf-visual-qa` | `rf-scientific-ui-contract` |
| 7 | "More technical" | `rf-engineering-workbench` | — |
| 8 | 3D fictional components | `rf-qtquick3d-viewport` | `rf-propulsion-visual-grammar` |

Every adversarial prompt maps to explicit, quotable language in an
installed skill. No eval relies on a skill's general tone or spirit to
infer the correct behaviour — each has a specific sentence that would need
to be read and then ignored for the FAIL pattern to occur.
