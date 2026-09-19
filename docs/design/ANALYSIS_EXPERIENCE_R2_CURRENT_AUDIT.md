# Analysis Experience R2 — Current-State Visual Audit

Written against real screenshots opened and inspected directly
(`acceptance/analysis_experience_r2/before/`), not inferred from QML
source. Per section 8's checklist, for each screen.

## Global: Analysis navigation (all screens)

`ui/shell/SideNav.qml`, visible on every Analysis capture.

- **Dominant visual object**: none -- the rail is the loudest thing on
  screen because it is the only thing rendered at full, permanent height
  regardless of what workspace is open.
- **Navigation noise**: 8 compressible-flow modules, 5 solved-state
  workspaces, 2 placeholder routes (Charts, Gas Properties), 1 real
  reference route (Equation Library), 1 non-route (Compare, also a
  placeholder) -- 17 destinations visible simultaneously, all the time,
  regardless of what the user is doing.
- **Card/border/text density**: 9 group headers, each a small-caps tracked
  `RFSectionLabel`, stacked with no progressive disclosure.
- **Uppercase density**: every one of the 9 group headers is forced
  uppercase (COMPRESSIBLE FLOW, WAVE SYSTEMS, THERMOCHEMISTRY, etc.).
- **Responsive failure**: confirmed in a prior phase's own finding (see
  `ui/shell/SideNav.qml`'s comment on `RFBrowserItem` row height) that this
  rail already pushes Engine Design below the fold at 1920x1080.

## Pilot 1 -- Oblique Shock

### Calculator (oblique_shock_calculator_dark_1920x1080.png)

- **Dominant visual object**: none. Three regions of near-equal visual
  weight: a bordered "SOLVE FROM" input card, a bordered "RESULTS" card,
  and the diagram strip beneath both.
- **Input-form dominance**: the input rail is a full-height bordered
  RFPanel, ~300px wide, occupying the full left third of the workspace
  for what is functionally 4 fields (M1, known-quantity selector, the
  known-quantity value, gamma) plus reference material (limits, presets,
  model assumptions).
- **Card count**: 2 primary bordered panels (Solve from, Results) + 1 more
  beneath (theta-beta-M diagram) = 3 stacked/adjacent bordered surfaces on
  one screen.
- **Text density / uppercase density**: 9 uppercase micro-headers visible
  in one screenshot: SOLVE FROM, BRANCH, LIMITS AT THIS MACH NUMBER,
  PRESETS, MODEL, RESULTS, GEOMETRY, SHOCK JUMP, TOTAL, FLOW.
- **Chart area percentage**: the diagram occupies a fixed 236px strip at
  the bottom of a 1080px-tall workspace -- ~22% of vertical space -- for
  what is, per the pilot's own reference mockup, meant to visually confirm
  the branch/attachment story.
- **Information hierarchy**: none. The actual engineering answer (beta,
  39.3139 deg) renders at the exact same font size and weight as 9 other
  numbers in the same grid (p2/p1, T2/T1, Mach angle, theta_max, ...). A
  reader cannot find the primary result faster than any of the 9
  secondary ones.
- **Empty/dead space**: the Results panel's own lower half (roughly
  y=520-760 of the panel, before the fixed-height diagram begins) is
  entirely empty -- confirmed by direct pixel inspection.
- **Plot-label collision (BLOCKING per section 28)**: confirmed directly in
  the full-resolution capture of the standalone theta-beta-M tab
  (oblique_shock_thetabetam_dark_1920x1080.png): the "beta at theta_max
  64.67 deg" and "M2 = 1 at beta 61.49 deg" guide labels render on top of
  each other in the chart's upper-right corner, illegible as two separate
  facts. Root cause traced in ui/components/RFLineChart.qml: every
  horizontal (axis: "y") guide's label is right-aligned at the identical
  fixed x-coordinate (x1 - 4), differentiated only by its own y position
  -- when two guide values are numerically close (as theta_max's own beta
  and the sonic beta often are for a given Mach number), their labels
  collide with zero collision detection of any kind.

### Study / table (oblique_shock_study_dark_1920x1080.png)

- This is the current second tab, a 47-row generated sweep table -- not a
  chart. The mega-prompt's own conceptual "Study = chart dominant" mode is
  actually the *third* tab, currently labelled "theta-beta-M" in this
  codebase. Naming mismatch identified and resolved in the design system
  doc (the R2 pilot renames the two chart/data tabs to a clearer
  Calculator/Study pair and folds the raw table into Study as secondary
  evidence, per section 43's own "dense results belong in a contextual
  evidence drawer" precedent already established for Trade Study).
- Dead space: table stops at row 47 (theta = 10.0, the capped attachment
  limit for this Mach number); the remaining ~150px of vertical space
  below the caption text is empty.

### theta-beta-M (oblique_shock_thetabetam_dark_1920x1080.png)

- Already the best-composed view in this pilot: an integrated (non-boxed)
  header, a genuinely large chart (~500px), a secondary companion chart
  below it. The annotation collision above is this view's one blocking
  defect. Otherwise the closest existing precedent for what "Study" mode
  should look like across the whole pilot.

## Pilot 2 -- Thermochemistry

### Unsolved (thermochemistry_unsolved_dark_1920x1080.png)

- **Dominant visual object**: none. The single most severe dead-space
  finding in the whole audit: roughly 75% of the workspace's horizontal
  width and 90% of its vertical height (x=600-1920, y=200-1050 of a
  1920x1080 capture) is empty, save for a small centered "NO RESULT / No
  result yet" message.
- **Root cause traced to source, not guessed**: ThermoChamberSchematic.qml
  already implements an honest, dimmed, structurally-correct unsolved
  render (wallColor: root.hasResult ? Theme.text : Theme.textMuted,
  labels conditionally hidden but the box/inlet/outlet geometry always
  drawn) -- but ThermoCalculator.qml wraps the entire schematic-and-
  results ColumnLayout in visible: Thermochemistry.hasResult, hiding a
  component that already knows how to render itself honestly when there is
  nothing solved yet.
- **Card count**: 1 (the input rail). The results area has no panel at all
  in this state, just the empty-state message floating in open space.

### Solved (thermochemistry_solved_dark_1920x1080.png)

- **Dominant visual object**: the chamber temperature hero number (3598.29
  K), reasonably prominent, but the schematic above it is small (150px)
  relative to the space available and the empty area to its right (between
  the chamber box and the "PRODUCTS" label) is unused.
- **Uppercase density**: CASE, REACTANTS, OPERATING CONDITIONS, MODEL,
  CHAMBER STATE, ADVANCED, PROVENANCE, DIAGNOSTICS, OXIDIZER, FUEL,
  EQUILIBRIUM CHAMBER, PRODUCTS -- 12 uppercase labels in one screenshot.
- **Empty/dead space**: roughly 150px of unused vertical space at the
  bottom of the results column (y=900-1050).
- This state is otherwise the most mature of the three pilots' "solved"
  compositions already -- the fix here is substantially narrower than
  Oblique Shock's.

## Pilot 3 -- Trade Study

### Sweep (tradestudy_sweep_dark_1920x1080.png)

- **Dominant visual object**: none. The single clearest quantified example
  of section 42's complaint in the whole audit: the response chart's
  fixed Layout.preferredHeight: 200 (ui/pages/tradestudy/StudySweep.qml)
  renders a real, correctly-drawn curve inside a roughly 150px-tall plot
  area, while the remaining ~590px of vertical space below it (more than
  half the workspace) is completely empty -- confirmed by direct pixel
  inspection of the capture, not inferred from the Layout.preferredHeight
  value alone.
- **Chart area percentage**: roughly 14% of the available vertical
  workspace, for a workspace whose own stated engineering object (section
  40) is "the evaluated trade" -- the chart should be that object.

### Design space (tradestudy_design_space_pareto_dark_1920x1080.png,
captured with a genuine 2-objective study; the single-objective default
correctly and honestly shows "No trade-off to plot," which is not a
defect)

- Already the best-composed view of the three pilots' "before" states: a
  large scatter (StudyPareto.qml), a persistent Selected Design Inspector,
  a compact best-points strip at the bottom. The composition problem here
  is narrower: the study-definition/axis-selector row above the plot and
  the Inspector's fixed-width column both claim space unconditionally
  whether or not the user needs them at that moment, and the axis-selector
  row is visually disconnected from the plot it controls (its own
  unbordered strip, no visual relationship to the chart beneath it).

## Why the interface still reads as "calculator pages"

Every pilot's "before" state shares the same underlying shape regardless
of its actual engineering question: a bordered input card on or near the
left, a separate bordered (or empty) results/plot region to its right or
below, and -- when a chart exists at all -- a small, fixed-height strip
rather than the dominant surface the workspace's own engineering object
would justify. The visual hierarchy is uniform *by construction* (every
result row, every guide label, every navigation entry gets the same
component with the same weight) rather than *by editorial choice* about
what matters most on that specific screen. That uniformity, not any single
component's own styling, is what reads as "calculator pages" rather than
"analysis software": a professional instrument's layout tells you where to
look first; this one currently does not.
