# Notation navigation crash — root cause and closure

**Verdict: CLOSED.** Switching from Nozzle Lab to Thermochemistry crashed the
application in `Qt6Qml.dll` in most runs from commit `0ac8b5e` (ISO 80000-2
notation) onward. The cause is a defect in the incremental garbage collector of
the QML engine in Qt 6.10.2. The notation helper's allocation per label
binding set it off. Two changes close it, each verified on its own:

1. `ui/theme/Notation.qml` compiles its rewrite rules once and memoises its
   results, so a label binding no longer allocates about forty `RegExp`
   objects on every evaluation. This removes the trigger.
2. `main.configure_application()` sets `QV4_GC_TIMELIMIT=0` unless the
   environment already sets it. The QML heap is then collected in one pass,
   as every Qt release before 6.8 did. This removes the defect class, which
   a long mixed session could still reach after change 1.

No physics, controller or scientific result changed.

## Correction to the dependency audit

The audit (2026-09-23) named the failing route "Nozzle Lab → Regimes →
Thermochemistry". That was wrong. The capture script that found it labelled
Nozzle Lab's section 1 "regimes"; section 1 is **Operating point**. Section 0
is Regime map, and the Regime map → Thermochemistry route never crashed:
0 of 10 runs at HEAD.

## Symptom

- Route: Isentropic → Oblique Shock (both sections) → Nozzle Lab
  (Regime map, then Operating point) → Thermochemistry, with Thermochemistry
  and Rocket Performance solved first. The short route
  Nozzle Lab (Operating point) → Thermochemistry alone did not crash: 0 of 18
  runs at HEAD. The crash needs the heap history of the earlier pages.
- Exit code `0xC0000005`, an access violation. Windows Error Reporting kept
  8 records. Every one names `Qt6Qml.dll` 6.10.2.0 at offset `0x413b3`, an
  accessor on a JavaScript function object.
- Bisection over the audit's commits: 0 of 5 runs crashed at `02c9172`.
  8 of 9 crashed from `0ac8b5e` onward.
- Every crashing run printed the same warnings first. Every uninstrumented
  run that survived printed none:
  - `RFBoundNumberField.qml:44: TypeError: Property '_show' … is not a
    function` (×3). A component's own function had gone missing.
  - `RFIconButton.qml:50:5: QML RFIcon: Cannot find member data` (×6). A
    type's own default property had gone missing.
  - In the capture matrix also `RFSegmentedControl.qml:25/29: Value is
    undefined` (×2).

  These are the 11 warnings the audit counted. They are symptoms of the same
  freed memory, not separate defects: all 11 vanish with either change above.

## Evidence

Each row is the full route above, 1.5 s per step, driven by a real event loop
in a separate process. The scratch driver used here works the same way as
`tests/application/shell_navigation_driver.py`. Collector settings are Qt's
defaults unless the row says otherwise.

| Variant | Change against HEAD `9e59d6a` | Crashed |
| --- | --- | --- |
| HEAD | — | 4 of 6 |
| HEAD, controller signals logged from Python | — | 3 of 4 |
| HEAD, `decimals` redeclaration removed | the first suspect, a shadowed property | 4 of 4 |
| B1 | the RFNumberField and RFBoundNumberField notation changes reverted | 0 of 10 |
| B2 | the RFNumberField label as plain text | 0 of 10 |
| B3 | the `textFormat` binding removed; `text` still `Notation.rich()` | 0 of 10 |
| B4 | `clip: true` removed | 10 of 10 |
| B5 | `textFormat: Text.RichText`, static | 0 of 10 |
| B6 | `elide` removed | 9 of 10 |
| B7 | `textFormat: Notation.isRich(label) ? …`, one singleton call | 9 of 10 |
| B8 | `textFormat` decided inline with `indexOf`, no singleton call | 0 of 10 |
| T1 | HEAD, `QV4_GC_TIMELIMIT=0`, one-pass collection | **0 of 10** |
| T2 | `02c9172`, `QV4_MM_AGGRESSIVE_GC` | 0 of 2 |
| GC-in | HEAD, `QV4_GC_TIMELIMIT=0` set from `configure_application()` | **0 of 10**, 0 warnings |
| GC-ctl | HEAD, unchanged, run side by side with GC-in | 9 of 10, 81 warnings |

Reading the table:

- Neither the rich-text format nor the switch between formats is the trigger.
  A static `RichText` survives (B5), and so does a dynamic switch computed
  inline (B8).
- What crashes is a second call into the notation singleton inside the
  `textFormat` binding (B7), on top of the one in `text`. Before the fix,
  each `Notation.rich()` call built 42 `RegExp` objects and about as many
  intermediate strings. The `textFormat` binding doubled that for every
  label on the page being built.
- Clipping and eliding are irrelevant (B4, B6).
- With one-pass collection (T1), the unmodified HEAD survives. This decides
  it. The engine's incremental collector (the default since Qt 6.8,
  `(1000/60)/3` = 5 ms steps) freed objects that were still reachable when
  a collection cycle spanned the page switch. Enough allocation during the
  switch made that likely. A freed function object read later is the crash.
  The same read before the crash is the warnings.
- JavaScript cannot free an object that is still referenced. A collector
  that does is at fault, whatever provoked it. A short search found no
  matching Qt bug report. The 6.10.2 release notes do carry a collector fix,
  QTBUG-142097, but it is a different defect, an infinite loop.

## The fix

### 1. `ui/theme/Notation.qml` — remove the trigger

- The rewrite rules are compiled once, in the original order, into
  `readonly property var rules`: pairs of `RegExp` and replacement.
- `rich()`, `species()`, `sectionRich()` and `runs()` are memoised in
  bounded maps. Each map holds at most 4096 entries and is cleared when full.
- Equivalence: 11 302 distinct strings from every label, unit and species
  name in the interface produce identical output before and after: 0
  differences. A mutant with one rule changed shows 96 differences, so the
  comparison can see a change.

### 2. `main.configure_application()` — remove the defect class

`os.environ.setdefault("QV4_GC_TIMELIMIT", "0")`, before any engine exists.
The notation fix alone passed every navigation route: 0 crashes in 90 runs,
covering 235 switches into Thermochemistry (below). It did not pass
everything. A 40-round mixed session soak (every workspace; bipropellant and
solid chemistry; Engine Design) still logged `'_show' … is not a function` in
2 of 8 runs under the incremental collector. In the instrumented run, the
field was no longer in the window's item tree. Under one-pass collection the
session soak logged nothing in 13 of 13 runs. A warning signature that
preceded every crash is not acceptable in a shipped build, even when rare.

Cost, from Qt's own statistics (`QV4_MM_STATS`, 5 session rounds): a
one-pass cycle takes 12.8 ms at the median and 21 ms at most, over a heap of
about 10 MB. The incremental collector spent 16.8 ms per cycle at the median,
in 5 ms steps. It also logged "Tried to force the GC to complete a run but
failed due to being in a critical section" 25 times; one-pass mode never
does. A pause of that size is one or two frames at 60 Hz.

An explicit `QV4_GC_TIMELIMIT` in the environment still wins. Revisit this
setting only on a Qt upgrade. Remove it only after the navigation smoke test
and the session soak both pass with the incremental collector on the new
version.

## Verification

With the notation fix only, under Qt's default incremental collector:

| Route | Runs | Crashed | Warnings |
| --- | --- | --- | --- |
| Full audit route | 50 | 0 | 0 |
| Nozzle Lab (Operating point) → Thermochemistry, 10 cycles per run | 5 (50 transitions) | 0 | 0 |
| Nozzle Lab (Regime map) → Thermochemistry, 5 cycles | 5 | 0 | 0 |
| Isentropic → Thermochemistry, 5 cycles | 5 | 0 | 0 |
| Rocket Performance → Thermochemistry, 5 cycles | 5 | 0 | 0 |
| Thermochemistry (solid, RP-1311 example 5) → Nozzle Lab → bipropellant, 5 cycles | 5 | 0 | 0 |
| Trade Study (Pareto) → Thermochemistry, 5 cycles | 5 | 0 | 0 |
| Full route, 1 ms collector steps (stress) | 10 | 0 | 0 |
| UI capture matrix, 54 screens, 3 modes, churn | 1 | 0 | **0** (HEAD: 11) |

With the final code (both changes, no environment variables). The first three
rows are 80 runs and 225 switches into Thermochemistry, 125 of them from
Nozzle Lab:

| Route | Runs | Crashed | Warnings |
| --- | --- | --- | --- |
| Full audit route | 50 | 0 | 0 |
| Nozzle Lab (Operating point) → Thermochemistry, 10 cycles per run | 5 (50 transitions) | 0 | 0 |
| Alternates, 5 cycles each: Regime map, Isentropic, Rocket Performance, solid, Trade Study | 25 (125 transitions) | 0 | 0 |
| Session soak, 40 rounds, four at once under contention | 4 | 0 | 0 |
| Session soak, 40 and 100 rounds, recorded evidence | 2 | 0 | 0 |
| Lifecycle soak, 40 and 100 rounds, recorded evidence | 2 | 0 | 0 |
| UI capture matrix, 54 screens | 1 | 0 | 0 |

## Regression test

`tests/application/test_shell_navigation_smoke.py` runs in every CI job.
Each route is a separate process with a hard timeout, and the process tree is
killed on timeout. A crash, a hang or any Qt/QML warning fails the test. The
tests:

- seven routes into and out of Thermochemistry, including real solid mode and
  Engine Design;
- the audit route again with Qt's own 5 ms incremental steps. The one-pass
  setting would otherwise hide a return of the allocation pattern. On the
  unfixed HEAD this route crashed in 5 of 5 runs, at the switch into
  Thermochemistry;
- a unit test that `configure_application()` sets one-pass collection and
  respects an explicit value;
- three negative controls: an injected QML error, a genuine native access
  violation (`faulthandler._read_null()`; `ctypes.string_at(0)` does not
  work, because ctypes turns the fault into an `OSError`), and an injected
  hang. Each must be reported as what it is.

A `solid:` step in the driver once loaded the solid formulation without
switching the workspace to solid mode, so it solved the bipropellant case.
The step now sets the mode and fails the run unless it ends in the mode it
names, with a result whenever a provider is present.

## Found on the way, not the cause

- Five QML properties redeclare a property of their base type: `decimals`
  (from `0ac8b5e`), plus `scale` in `RFReadoutStrip` and `RFResultValue`,
  `palette` in `ThermoSweepSpeciesChart`, and `state` in `SideNav`, which
  predate it. Removing `decimals` changed nothing (4 of 4 still crashed).
  The other four predate the crash. They are latent, not causal, and are
  left for a UI change of their own.
- The capture harness's "solid" screen had the same missing-mode fault as the
  driver. Its captures before this closure show the bipropellant case.
