---
name: rf-visual-qa
description: RocketForge's own screenshot-based visual QA -- the per-workspace canonical state matrix (empty/stale/warning/refused/etc, at 2560/1920/1366 in light and dark), and the discipline that a build/test PASS is not a visual PASS. Use before declaring any workspace redesign finished, after generating capture screenshots, or whenever asked to verify a UI change actually looks right rather than just runs without error. Complements design-review (general craft/hierarchy critique) and interface-review's independent-reviewer role -- this skill owns RocketForge-specific state truthfulness, they own general polish.
---

# RocketForge visual QA

**A passing test suite is not a visual PASS.** Field-by-field scientific
parity, source/packaged parity, and a green pytest run all check that a
number is correct -- none of them look at the rendered page. This project
has already shipped, and caught after the fact by looking, a completely
empty result rail that a 5688-field parity check reported as zero
differences, because the check reads controller properties and the
component that rendered them had silently failed to bind. **Actually
inspect the images.** Do not infer their content from the code that
produced them.

## The canonical state matrix

Before signing off a redesigned or reviewed workspace, capture and inspect
it across the states in the table below (extend the table when a workspace
gains a state not listed), at 2560x1440, 1920x1080, and 1366x768, in both
light and dark:

| Workspace | States to capture |
| --- | --- |
| Rocket Performance | no chamber, normal, vacuum, scaled, stale, warning, positive pressure thrust, negative pressure thrust |
| Thermochemistry | native assigned enthalpy, corrected enthalpy, no condensed species, below reporting threshold, condensed present |
| Fluid Properties | representative fluid (e.g. LOX/LCH4), phase refusal, out-of-envelope state |
| Line | laminar, turbulent, transitional refusal, outside transport envelope |
| Trade Study | empty/configure, feasible, infeasible, Pareto, large study, arbitrary X/Y axes (if supported) |
| Engine Design | a supported topology, stale, a selected component, an unavailable component |

This project's existing capture tooling
(`experiments/ui_visual_pilot/capture_matrix.py`,
`experiments/ui_visual_pilot/visual_parity.py`,
`experiments/ui_visual_pilot/accessibility_audit.py`) is the reference
implementation of how to drive these states non-interactively and how to
compare captures against a prior accepted baseline. Extend that pattern for
a new workspace rather than inventing a new capture mechanism.

## What to look for in every capture

- **Stale-vs-solved mismatch.** A header, label, or annotation sourced from
  a live input rather than the result it sits beside -- see
  `rf-scientific-ui-contract`'s header-vs-drawing rule. This is the single
  most important thing to check and the one a field-level parity diff
  structurally cannot catch, because the mismatch is between two things
  that are each individually correct.
- **Silently empty content.** A list, breakdown, or readout that rendered
  nothing where a solved state should show something -- check this
  especially after any change to how results are published to QML (see
  `rf-qml-architecture`'s row-model rule; a role-name collision produces
  exactly this failure with a clean parity diff alongside it).
- Clipping, overlap, dead empty regions, over-dense rails.
- Weak hierarchy -- can the primary result be found in under two seconds?
- Wrong or missing units.
- A warning or stale indicator that is visually present but easy to miss.
- Fabricated physical implication in a schematic (`rf-propulsion-visual-grammar`
  owns the rule; this skill is where a violation actually gets caught).
- Accidental generic-SaaS drift: card grids, gradient washes, uppercase
  labels used structurally rather than selectively, badges added without a
  reason (`rf-engineering-workbench` owns the rule).
- Accessibility floor: keyboard focus visible, contrast adequate, no state
  distinction that relies on colour alone.

## Fixture: the stale-vs-solved mismatch, concretely

Before trusting this skill's own judgement on a redesign, build (or reuse)
a fixture like this and confirm it is caught:

- Set a live input (e.g. an expansion ratio field) to one value.
- Solve/calculate so the result reflects an *earlier* input value.
- Edit the input again without recalculating.
- Capture the screen.

A passing review must flag that the header text and the drawn/solved
content disagree. If it does not, the review process itself needs fixing
before it is trusted on real work -- do not proceed to sign off other
screens until this fixture passes.

## One workspace at a time

Do not batch a redesign across every workspace and review at the end. For
each workspace: audit the existing state from real captures, design,
implement, capture, **manually inspect**, fix, memory-check
(`rf-qml-architecture`), verify scientific parity
(`rf-scientific-ui-contract`), check for unexplained Qt/QML warnings,
accept, only then move to the next workspace. A defect caught early in one
workspace is cheap; the same defect copied into five workspaces before
anyone looks is expensive.

## Relationship to `design-review` and `interface-review`

`design-review` (installed, project-local) gives a scored, cited critique
of a screenshot -- hierarchy, craft, typography, general UX heuristics. Use
it as the independent, second-opinion layer after this skill's
RocketForge-specific truthfulness checks pass, not instead of them: it has
no way to know that a Rocket Performance header must be sourced from a
result object rather than a live input, or that an expansion ratio of 60
next to a drawn nozzle at 40 is a defect rather than a matter of taste. Run
this skill's checks first; bring in `design-review` for the craft pass on
top.

## Ownership

**This skill owns:** the per-workspace canonical capture-state matrix,
the discipline that screenshots are actually inspected rather than
inferred, and the specific failure modes (stale-vs-solved mismatch,
silently empty content) that field-level parity checks cannot see.

**This skill explicitly does not own:**
- General craft/hierarchy scoring of a screenshot -- `design-review`.
- What a schematic may draw -- `rf-propulsion-visual-grammar` (this skill
  enforces that rule at review time; it does not define it).
- Scientific state semantics -- `rf-scientific-ui-contract` (same
  relationship: enforcement here, definition there).
- Memory/performance measurement -- `rf-qml-architecture`.
