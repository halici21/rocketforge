# Design Skill Live Eval R1 — Results

Raw data: `acceptance/design_skill_live_eval_r1/aggregate_scores.json` and
`blocking_gates.json`. This document is the human-readable walk-through.
Where a skill fix was applied mid-run (evals 06 and 07), the numbers below
are the **post-fix** state — see `DESIGN_SKILL_LIVE_EVAL_R1_FAILURES.md` for
the before/after.

## Aggregate

| Metric | Value |
| --- | --- |
| Evals scored | 11 |
| **Routed overall mean** | **4.77 / 5** |
| **Control overall mean** | **3.34 / 5** |
| **Improvement** | **+1.43** |
| Pre-registered target | >= +0.75 |
| Target met | **Yes**, by a wide margin |
| Routed wins | 9 / 11 |
| Control wins | 1 / 11 (eval 08, narrow, both passed the blocking gate) |
| Ties | 1 / 11 (eval 10) |
| Blocking evals, all pass (routed) | **Yes**, 5 / 5, after two skill fixes |
| Blocking dimension score < 4 anywhere (routed) | **None** — every scored blocking dimension is 5/5 |

This is not a landslide manufactured by one or two extreme scores: 9 of 11
individual evals independently favor the routed condition, the two
exceptions are a narrow loss and a tie rather than a loss, and the mean
improvement is nearly double the pre-registered target.

## Per-eval

| # | Eval | Routed mean | Control mean | Winner | Blocking |
| --- | --- | --- | --- | --- | --- |
| 01 | Home | 4.80 | 1.80 | routed | — |
| 02 | Fluid Properties | 5.00 | 3.40 | routed | — |
| 03 | Trade Study axes | 5.00 | 4.67 | routed | PASS |
| 04 | Nozzle realism | 4.67 | 2.33 (blocking-fail) | routed | PASS |
| 05 | QML animation | 5.00 | 4.33 | routed | PASS |
| 06 | Technical visual language | 5.00\* | 3.00 | routed | — |
| 07 | Engine Design 3D | 4.33\* | 1.67 (blocking-fail) | routed | PASS\* |
| 08 | Stale snapshot QA | 4.67 | 5.00 | control | PASS |
| 09 | Chart/table proportion | 4.50 | 4.00 | routed | — |
| 10 | Responsive 1366x768 | 4.50 | 4.50 | tie | — |
| 11 | Qt Quick 3D decision | 5.00 | 2.00 | routed | — |

\* post-fix rerun value; see below and `_FAILURES.md`.

### 01 — Home

Routed (`rf-engineering-workbench` -> `qt-ui-design`) scored 4.8 vs control's
1.8 — the largest gap of any eval that wasn't a blocking-fail case. Control
produced exactly the SaaS-dashboard pattern the skill exists to prevent;
routed placed a dimmed last-solved schematic as the dominant element,
demoted navigation to a secondary rail, and explicitly named and rejected
KPI tiles and activity feeds.

### 02 — Fluid Properties

Routed committed to a single fluid/state centerpiece and banned both the
per-property card grid and a default sweep chart by name, with a fail-closed
honesty rule. 5.00 vs 3.40.

### 03 — Trade Study axes (blocking)

Both PASS. Both explicitly state zero physics/Pareto/score change from an
axis switch and both address the 2D-projection distinction. Routed edges
ahead (5.00 vs 4.67) on RocketForge-specific semantic precision (density
impulse "unavailable" vs. zero, unit-mislabeling risk).

### 04 — Nozzle realism (blocking)

**Control blocking-failed.** It proposed an "exit-plane plume cue" — a
decorative glow past the exit plane, gated on `hasResult && !stale` (i.e.
presented as tied to a real result) — a direct match to the "fake CFD
plume" trigger, and then contradicted its own honesty section two
paragraphs later. Routed (`rf-propulsion-visual-grammar`) proposed only
rendering/annotation upgrades over the already-solved area ratio and
explicitly deferred any bell-contour feature as out of scope. 4.67 vs 2.33.
Rerun after the (unrelated, eval-07-driven) skill fix confirms no
regression: still 5/5, no blocking fail.

### 05 — QML animation (blocking)

Both PASS cleanly — neither proposes per-solve object creation, growing
signal connections, a permanent repaint loop, or physics in QML. Routed
edges ahead (5.00 vs 4.33) with more explicit lifecycle and lifecycle-test
language.

### 06 — Technical visual language

**Genuine weakness found and fixed.** Pre-fix, routed scored 5/5/1 on
hierarchy/typography/accessibility — strong on restraint, silent on
accessibility, while the naive control scored 3/2/4, catching a contrast
risk routed missed. Post-fix, routed scores 5/5/5, sweeping all three
against an unchanged control's 3/2/4. See `_FAILURES.md` for the full
before/after and the successful generalization test.

### 07 — Engine Design 3D (blocking)

**Genuine weakness found and fixed, and the more serious of the two —
this is a blocking eval.** Pre-fix, both conditions blocking-failed:
control over-claimed chamber/nozzle sizing, and routed (despite invoking
`rf-propulsion-visual-grammar` + `rf-qtquick3d-viewport` and doing real
codebase research) misclassified `injector` as having "real solver code"
because the name appeared inside another module's own disclaimer about
what is *not* built. Post-fix, an independent reviewer re-derived ground
truth directly from the source (not trusting either candidate's
self-report) and confirmed: routed now scores 5/5 on both honesty and
fictional-capability avoidance, renders nothing as solved geometry it does
not have, and explicitly declines the literal "3D CAD engine" framing in
favor of an honest schematic extension. Control (unchanged) still
blocking-fails, as expected. See `_FAILURES.md` for full detail.

### 08 — Stale snapshot QA (blocking)

Both PASS cleanly — both explicitly name the header-vs-schematic mismatch,
correctly diagnose it as a data-binding defect, and correctly prescribe
rebinding the header to the same result snapshot as the schematic. Control
edges ahead narrowly (5.00 vs 4.67) on richness of the proposed remedy
(specific affordance copy, a suggestion to audit for the same pattern
elsewhere). **Honest caveat:** the fixture stated the mismatch explicitly
in the prompt, so this measures whether the pattern is catchable once
named, not whether the routed skill specifically surfaces it unprompted
from a raw screenshot — see the Recommendations document for a stronger
future version of this test.

### 09 — Chart/table proportion

Both avoid the universal-50/50 failure and reason per-workspace. Routed
(4.50 vs 4.00) more precisely separates Thermochemistry's Calculator (no
chart, primary) from its Sweep tab (chart-dominant only when active) —
control leaves that distinction implicit.

### 10 — Responsive 1366x768

A genuine tie (4.50 each), strong in complementary ways — routed is more
explicit about the no-scrolling guarantee for the primary action; control
does sharper resolution-specific vertical-budget arithmetic. Recorded
honestly as a tie rather than forced to a winner.

### 11 — Qt Quick 3D decision

Routed (`rf-qtquick3d-viewport`) scored 5/5 vs control's 2/2 — the second-
largest gap in the run. Both avoided the "yes, 3D looks more professional"
FAIL pattern outright and gave qualified recommendations, but routed's
judgement was grounded in an actual inspection of `EngineCanvas.qml` and
the component registry, naming concrete Qt Quick 3D lifecycle objects,
where control reasoned in the abstract.

## Live vs. structural

Every result above is a **live** result: a real subagent invoked the real
`Skill` tool against the real installed skill files and produced a real,
independently-reviewed response — not a re-read of the skill text asserting
what it would do. Two of the eleven evals surfaced a real gap between
"the rule exists in the text" (which Foundation R1's structural walkthrough
had already confirmed for both fixed skills) and "the rule actually
changes the live output" (which this run tests) before either fix was
applied — proof that the structural/live distinction this run exists to
close is a real one, not a formality.
