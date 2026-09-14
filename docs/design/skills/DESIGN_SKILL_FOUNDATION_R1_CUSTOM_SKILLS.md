# Design Skill Foundation R1 — Custom RocketForge skills

Seven custom skills, all narrow, all with an explicit non-ownership
section in their own `SKILL.md`. Each is justified by a gap real research
(see `DESIGN_SKILL_FOUNDATION_R1_RESEARCH.md`) confirmed no adequate
external skill fills, or by RocketForge-specific evidence no general skill
could contain (the memory investigation's findings, the accepted pilot's
exact grammar).

## `rf-engineering-workbench`

**Purpose:** the application-level design authority — composition, card and
chrome discipline, progressive disclosure, the CAD/CAE shell target.
**Trigger:** any page/workspace/shell redesign, "make this feel more like
an engineering tool," a panel/dock decision, the home page.
**Owns:** object-first grammar, chrome discipline, responsive layout
behaviour, soft-industrial visual language as applied to layout.
**Explicitly does not own:** scientific honesty (`rf-scientific-ui-contract`),
schematic drawing rules (`rf-propulsion-visual-grammar`), QML mechanics
(`rf-qml-architecture`/`qt-qml`), plot/table internals
(`rf-scientific-visualization`).
**Grounded in:** the accepted Rocket Performance pilot's full report and
audit — the pinned-rail rationale, the overflow-cue rule, the card-count
reduction (2 → 0), the exact `RESPONSIVE_LAYOUT_BLOCKER` history.

## `rf-propulsion-visual-grammar`

**Purpose:** what each workspace's engineering schematic may draw and
claim, per domain, with the current per-workspace object table.
**Trigger:** drawing, redesigning, or reviewing any workspace's central
schematic.
**Owns:** the schematic-vs-solved distinction, the honesty-label rule, the
placeholder/unsolved-state drawing rule, the "no fictional Engine Design
component" rule.
**Explicitly does not own:** where the schematic sits on the page
(`rf-engineering-workbench`), whether a number beside it is honest
(`rf-scientific-ui-contract`), chart/table visualization
(`rf-scientific-visualization`).
**Grounded in:** the Rocket Performance canvas's actual honesty-label
history (including its placeholder-mode correction), and this repository's
real per-workspace physics scope (equilibrium chemistry, ideal expansion,
distributed pipe friction — explicitly not CFD, not a solved contour, not a
phase diagram) as read from the engineering architecture docs.

## `rf-scientific-ui-contract`

**Purpose:** protects meaning at the UI boundary — state semantics
(stale/superseded/warning/refused/unavailable), commonly-mislabeled
quantities, the header-vs-drawing failure pattern.
**Trigger:** any UI change touching how a result, status, or warning is
displayed, renamed, hidden, defaulted, or reformatted.
**Owns:** the governing field-level-parity test, the state-collapse table,
the quantity-meaning glossary (c*, Isp, Cf sign convention, density
impulse, Darcy vs Fanning, CEA-as-oracle, condensed-phase semantics), the
generalized header-vs-drawing rule.
**Explicitly does not own:** layout, schematic drawing, or the physics
itself (frozen, out of scope for any UI skill).
**Grounded in:** a real defect from this project's history (a header bound
to a live input rather than the solved result it sat beside) and the
Rocket Performance pilot's field-by-field parity methodology (5688 fields,
zero differences, under a negative control proving the comparison could
detect a real change).

## `rf-qml-architecture`

**Purpose:** RocketForge-specific QML/Python architecture rules the
general Qt authority does not and should not cover.
**Trigger:** writing/reviewing QML or controller code in this repository,
publishing a new result to a view, adding an animation or Canvas,
investigating a performance/memory complaint.
**Owns:** the no-physics-in-QML boundary as enforced here, the stable
row-model publication pattern (with the measured evidence behind it), this
app's singleton/controller ownership shape, and — via its
`RF_QML_LIFECYCLE_RULES.md` reference — the correct protocol for measuring
memory in a Qt application, including the `DeferredDelete` trap this
project's own investigation fell into.
**Explicitly does not own:** general Qt6 correctness (`qt-qml`,
`qt-qml-review`), broader UX principles (`qt-ui-design`), schematic content
(`rf-propulsion-visual-grammar`), composition (`rf-engineering-workbench`).
**Grounded in:** `docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md`
and `rocketforge/application/rowmodel.py` directly — every rule in this
skill traces to a specific measured finding from that investigation, not
to general best-practice assumption.

## `rf-scientific-visualization`

**Purpose:** when and how RocketForge shows quantitative evidence — chart
vs. table proportion by task, chart-type selection, data-ink discipline,
the existing plotting component vocabulary.
**Trigger:** adding, resizing, or reviewing a chart/plot/scatter/sweep or
dense numeric table.
**Owns:** the proportion rule (task-driven, never a default split), the
`RFPlotSurface`/`RFLineChart`/`RFEngineeringTable` usage vocabulary, units/
uncertainty/semantic-colour representation on a plot, and the Trade Study
multi-objective Pareto-projection rule.
**Explicitly does not own:** page placement (`rf-engineering-workbench`),
schematic drawing (a schematic and a chart are never the same visual —
`rf-propulsion-visual-grammar`), quantity labeling correctness
(`rf-scientific-ui-contract`).
**Grounded in:** `RFPlotSurface.qml`'s and `RFEngineeringTable.qml`'s actual
doc comments (frameless axis discipline, right-aligned tabular figures, the
sonic-line accent-edge convention) and `StudyPareto.qml`'s existing,
already-correct Pareto-projection discipline — read directly, not assumed.
Tufte's chart-selection/kill-list principles cited by name, not copied
wholesale, since their native output format does not apply here.

## `rf-visual-qa`

**Purpose:** RocketForge's own screenshot-based QA discipline — the
per-workspace canonical state matrix, and the rule that a passing test
suite is not a visual PASS.
**Trigger:** before declaring any workspace redesign finished, after
generating capture screenshots, whenever asked to verify a UI change
actually looks right.
**Owns:** the state matrix per workspace, the discipline of actually
inspecting images rather than inferring their content from code, and the
specific failure modes (stale-vs-solved mismatch, silently empty content)
a field-level parity check structurally cannot see.
**Explicitly does not own:** general craft scoring (`design-review`, used
as the second-opinion layer on top of this skill's checks), what a
schematic may draw (enforces `rf-propulsion-visual-grammar`'s rule, does
not define it), memory/performance (`rf-qml-architecture`).
**Grounded in:** the actual capture tooling already built
(`experiments/ui_visual_pilot/capture_matrix.py`, `visual_parity.py`,
`accessibility_audit.py`) and a real documented case in this project where
a field-level parity check reported zero differences while a rendered
region of the page had silently failed to bind.

## `rf-qtquick3d-viewport` (conditional custom skill)

**Purpose:** evaluation and implementation rules for a Qt Quick 3D
engineering viewport, written from scratch because research confirmed no
comparable skill exists anywhere, including from the Qt Company itself.
**Trigger:** only when a genuine 3D or 2.5D viewport is under discussion —
explicitly not for ordinary 2D QML work.
**Owns:** the evaluate-before-adopting decision, Qt Quick 3D scene/camera/
material/lighting/picking discipline, and the scientific-honesty rule
extended into three dimensions.
**Explicitly does not own:** 2D QML architecture (defers directly to
`rf-qml-architecture`'s lifecycle rules for scene/resource disposal), what
any schematic (2D or 3D) may claim about unsolved geometry (defers directly
to `rf-propulsion-visual-grammar`, extending rather than restating it),
general composition (`rf-engineering-workbench`).
**Grounded in:** Qt's own public Qt Quick 3D module API shape (not copied
from any third party — none exists), and this project's Engine Design
workspace as the concrete case the skill's evaluation questions are framed
against. Its own `SKILL.md` documents its provenance and states plainly
that the "no comparable skill exists" research finding should be re-checked
before treating the skill as complete, should a real 3D viewport project
begin.

## What was considered and not created

A eighth candidate — a narrow "RF theme/token" skill duplicating what
`ui/theme/Theme.qml`'s own doc comments and `qt-ui-design`'s token-role
guidance already state — was considered and dropped: nothing about
RocketForge's actual token *values* needs skill-level guidance beyond
reading the singleton itself, and a skill whose entire content is "read
this file" is not pulling its weight as a skill.
