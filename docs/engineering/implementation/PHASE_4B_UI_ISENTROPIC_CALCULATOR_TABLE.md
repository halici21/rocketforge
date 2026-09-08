# Phase 4B-UI — Isentropic Calculator, Generated Table and Reference Comparison

The first complete engineering workflow in RocketForge: verified physics →
application adapter → calculator → generated table → published-reference
comparison → packaged executable.

Date: 2026-08-30

---

# Verdict

**PASS**

---

## Existing backend used

No new physics. Every number originates in one of these Phase 4B calls:

    isentropic.ratios_from_mach(mach, gas) -> IsentropicRatios
    isentropic.temperature_ratio(mach, gas)          # T/T0
    isentropic.pressure_ratio(mach, gas)             # p/p0
    isentropic.density_ratio(mach, gas)              # rho/rho0
    isentropic.area_ratio(mach, gas)                 # A/A*
    isentropic.temperature_ratio_star / pressure_ratio_star / density_ratio_star
    isentropic.mach_angle(mach)
    isentropic.mach_from_temperature_ratio(ratio, gas)
    isentropic.mach_from_pressure_ratio(ratio, gas)
    isentropic.mach_from_density_ratio(ratio, gas)
    isentropic.mach_from_area_ratio(area_ratio, gas, branch) -> Solution[float]
    isentropic.mach_from_area_ratio_both(area_ratio, gas) -> Solution[AreaMachSolutions]
    PerfectGas(gamma) / PerfectGas.diagnostics
    equations.record("isentropic.pressure_ratio.v1")  # assumptions for display

## Files created

**Application layer**

    rocketforge/application/formatting.py                       engineering number formatter
    rocketforge/application/analysis/isentropic_service.py      calculator + table, Qt-free
    rocketforge/application/analysis/reference_comparison.py    published-table comparison, Qt-free
    rocketforge/application/analysis/engineering_table_model.py generic QAbstractTableModel
    rocketforge/application/analysis/isentropic_controller.py   the QObject QML binds to
    rocketforge/application/analysis/__init__.py

**Reference data**

    rocketforge/data/reference/anderson6_appendix_a_isentropic.json   217 rows

**Interface**

    ui/components/RFEngineeringTable.qml        reusable numeric table
    ui/components/RFBoundNumberField.qml        loop-free two-way number field
    ui/pages/isentropic/IsentropicCalculator.qml
    ui/pages/isentropic/IsentropicTable.qml
    ui/pages/isentropic/IsentropicCharts.qml

**Tests**

    tests/application/test_isentropic_service.py       59
    tests/application/test_reference_comparison.py     28
    tests/application/test_controller_and_model.py     30

**Documentation**

    docs/engineering/implementation/PHASE_4B_UI_ISENTROPIC_CALCULATOR_TABLE.md

## Files modified

    ui/pages/IsentropicPage.qml         rewritten as a three-section host; mock values removed
    ui/Main.qml                          registers the Isentropic singleton path; status-bar flag
    ui/shell/StatusBar.qml               `computed` property (see "Shared component changes")
    ui/data/Navigation.qml               `computed: true` on the isentropic entry
    main.py                              registers the IsentropicController singleton
    packaging/RocketForge.spec           bundles rocketforge/data/reference
    rocketforge/application/__init__.py  docstring only

**No physics file was modified.** Verified by modification time: nothing under
`rocketforge/physics/`, and neither `core/numerics/roots.py` nor the frozen
Phase 4A test files, changed during this phase.

---

## Calculator modes

Eight, each mapping to a relation Phase 4B implemented and verified:

| Mode | Symbol | Route |
| --- | --- | --- |
| Mach number | M | direct |
| Pressure ratio | p/p₀ | `mach_from_pressure_ratio` |
| Pressure ratio | p₀/p | reciprocal in the adapter, then `mach_from_pressure_ratio` |
| Temperature ratio | T/T₀ | `mach_from_temperature_ratio` |
| Temperature ratio | T₀/T | reciprocal, then the same call |
| Density ratio | ρ/ρ₀ | `mach_from_density_ratio` |
| Density ratio | ρ₀/ρ | reciprocal, then the same call |
| Area ratio | A/A* | `mach_from_area_ratio`, branch required |

The branch control appears only for A/A*, offering Subsonic, Supersonic and
Both. It is never defaulted away: the backend refuses to guess and so does the
interface.

## Table columns

**Anderson (default)** — M, p₀/p, ρ₀/ρ, T₀/T, A/A*
**Standard** — M, p/p₀, ρ/ρ₀, T/T₀, A/A*

Both are the same computation; only the printed orientation differs. A test
asserts that the three ratio columns of one are exactly the reciprocals of the
other, and that A/A* is *not* inverted between them.

## Anderson convention

The published appendix prints **stagnation over static**:

    M    p0/p    rho0/rho    T0/T    A/A*

RocketForge computes **static over stagnation**. The mapping, which lives in
the adapter and nowhere else:

    p0_over_p      = 1 / isentropic.pressure_ratio(M, gas)
    rho0_over_rho  = 1 / isentropic.density_ratio(M, gas)
    T0_over_T      = 1 / isentropic.temperature_ratio(M, gas)
    area_ratio     =     isentropic.area_ratio(M, gas)        # same way up in both

That reciprocal is a representation transform of a verified value, not a second
implementation: there is no alternative formula anywhere in the application
layer. `test_book_convention_is_the_reciprocal_of_the_rocketforge_convention`
exists specifically to catch an orientation slip, and checks at four Mach
numbers that the published column equals the reciprocal of the computed one to
the source's own precision — plus that the two sit on opposite sides of 1 in
supersonic flow, so an accidental double inversion could not pass.

## Reference source

* **Author** John D. Anderson, Jr.
* **Title** *Fundamentals of Aerodynamics*, 6th Edition
* **Publisher** McGraw-Hill · ISBN 9781259129919
* **Appendix** A — Isentropic Flow Properties
* **Printed pages** 1079–1083
* **Copy used** the PDF supplied in the working environment
* **Extracted** 2026-08-30

Only numeric values and citation metadata are stored. No explanatory text from
the source is reproduced.

## Extracted reference data

    rows      217
    range     M = 0.02 to M = 50.0
    columns   M, p0/p, rho0/rho, T0/T, A/A*
    gamma     1.4

**Gamma was determined, not assumed.** For a calorically perfect gas
`T0/T = (gamma+1)/2` at M = 1; the sonic row prints 1.200, giving gamma = 1.4
exactly, and the other three sonic values agree to the printed precision. A
test re-derives this from the dataset rather than trusting the metadata.

**Extraction verification.** The notation is `0.5229 + 02`, a normalised
mantissa with a signed exponent. Text extraction emits some values as
`0 . 1893 + 01`, with spaces around the decimal point, and a regex without
whitespace allowances silently *drops* those values — which would shift every
remaining number in the row one column to the left. The M = 1.0 and M = 2.0
rows are among the affected ones, so the corruption would have landed exactly
on the checkpoints. It was caught by a guard requiring the token count on each
page to be a multiple of five.

Manual checkpoints, read visually from the rendered pages and asserted in
`test_manual_extraction_checkpoints`:

| M | p₀/p | ρ₀/ρ | T₀/T | A/A* |
| --- | --- | --- | --- | --- |
| 0.50 | 1.186 | 1.130 | 1.050 | 1.340 |
| 1.00 | 1.893 | 1.577 | 1.200 | 1.000 |
| 2.00 | 7.824 | 4.347 | 1.800 | 1.687 |
| 3.00 | 36.73 | 13.12 | 2.800 | 4.235 |
| 5.00 | 529.1 | 88.18 | 6.000 | 25.00 |

Two of those were initially wrong in my own checkpoint list because they were
written from memory rather than read off the page — M = 3.0 prints ρ₀/ρ = 13.12
(not 19.09) and M = 5.0 prints 88.18 (not 113.6). The parser was right both
times; the expectation was corrected against the page, never the reverse.

Structural checks: 217 rows, Mach strictly increasing and unique, every value
finite and positive, A/A* ≥ 1 throughout, exactly one sonic row and its
A/A* = 1.000.

## Comparison methodology

For every reference row:

    published Mach  ->  RocketForge recomputes all four quantities  ->  compare

The published value is **never** an input to the calculation it checks, and
rows are matched by Mach number, not by index, so a user's grid need not align
with the book's. A Mach number the source does not print has no reference value
and says so; nothing is interpolated.

**Tolerance** is half a unit in the last printed digit, scaled by the printed
exponent: `atol = 0.5 × 10^(exponent − 4)`. So 1.687 is stated to ±0.0005 while
8285 is stated only to ±0.5. A hair of relative slack absorbs the binary
representation of a decimal, so a value sitting exactly on the half-unit
boundary — A/A* = 1.6875 against a printed 1.687 — is not failed by float
noise.

Full-precision values are compared; only the display is rounded.

## Comparison result

    rows compared        217
    values compared      868
    PASS                 866
    REVIEW                 2
    max absolute diff    0.0900
    max relative diff    1.721e-3

**The two REVIEW cases are source artefacts, investigated before anything was
touched, and RocketForge's physics was left alone in both.**

1. **M = 16, T₀/T** — the book prints 52.29. The relation gives
   `1 + 0.2 × 16² = 52.2` exactly, which anyone can check by hand, and the
   neighbouring rows at M = 15, 17 and 18 are all exact (46.0, 58.8, 65.8).
   This is a misprint in the source.
2. **M = 7.8, p₀/p** — computed 8285.512 against a printed 8285, a difference
   of 0.512 units where the four-figure mantissa implies half a unit. A
   rounding artefact 0.012 units past the boundary.

Before concluding that, the source's rounding convention was characterised
rather than guessed: of 868 printed values, **856 are reproduced exactly by
round-half-up to four mantissa digits**, and only the M = 16 value matches no
convention at all. So the table rounds (with exact halves resolved downward),
and the M = 7.8 case is a marginal rounding decision rather than evidence
against the relation.

Both surface as REVIEW in the interface, which is what that status is for.

## Table generation

* Range and step are user-controlled and validated: start > 0 (A/A* is
  unbounded at rest), end > start, step > 0.
* **Row limit 20,000**, reported as a readable message rather than a freeze:
  *"That range and step would produce 4,999,001 rows, above the 20,000 row
  limit. Increase the step or narrow the range."*
* **M = 1 is inserted** when it falls inside the range but the step would step
  over it — the one row every reader looks for. The insertion is explicit,
  switchable, and recorded in the table metadata.
* One vectorised call per quantity, never a loop per row.
* Deterministic: the same settings produce a bit-identical block.

## Performance

    250 rows      0.4 ms
    1,000 rows    0.2 ms
    5,000 rows    0.5 ms
    868 reference values compared   9.3 ms

Comfortably interactive; no threading was introduced, and none is warranted.

## QML warnings

**0.** A 56-step sweep covering both themes, all three sections, all eight
solve modes, all three branches, gamma changes, table regeneration at two step
sizes and the comparison toggle produces no Qt messages.

Four defects were found and fixed during that sweep rather than shipped:

1. A two-way binding loop on every number field — fixed by
   `RFBoundNumberField`, which makes the flow one-way in each direction.
2. `undefined` assigned to a string while the table model reset, once per
   visible cell.
3. An unquoted font family in the chart's canvas context.
4. A `TypeError` from a handler that ran before the component it referenced
   existed.

Two more were found by looking at the rendered result:

5. The Presets segmented control drew its selection indicator outside itself
   when it had no current index, painting over the navigation rail. Replaced
   with buttons, since presets are actions rather than a persistent selection.
6. **The Reference check panel did not re-evaluate**, so it could show the
   comparison for one Mach number beside the result for another. Fixed by
   giving the binding a real dependency on the result.

## Architecture regression

**PASS** — 41 tests, unchanged and not weakened. `application` may import
`physics` and Qt; `physics` imports neither Qt nor `application`. No SciPy
anywhere.

## Phase 4A regression

**PASS** — 203 root-solver tests green, the frozen files untouched.

## Phase 4B regression

**PASS** — 658 physics tests green, including every NACA reference case. No
physics output changed; the Anderson table was made to fit the physics, never
the reverse.

## Executable

    C:\Users\erayh\Documents\Python\rocket\dist\RocketForge\RocketForge.exe

Rebuilt with the project's own `build_exe.bat`. Bundle checks: `numpy` present,
`scipy` **absent**, `ui/` present, and the reference dataset present at
`_internal/rocketforge/data/reference/`. 185 MB directory build.

The reference path resolves through `sys._MEIPASS` when frozen, the same way
`main.py` finds `ui/`. Deriving it from `__file__` alone would have passed every
test and failed only in the shipped build, with the comparison silently dead.

Verified in the packaged application: it launches; the Isentropic page opens on
the Calculator; γ = 1.4 and M = 2 produce T/T₀ = 0.555556, p₀/p = 7.82445,
ρ₀/ρ = 4.34692 and A/A* = 1.68750; and the reference check shows four PASS rows
against Anderson with the citation. That single state exercises the bundled
backend, NumPy and the bundled reference dataset together.

## Screenshots

    C:\Users\erayh\Documents\Python\rocket\acceptance\phase_4b_ui\

    01_isentropic_calculator_dark.png        source runtime
    02_isentropic_area_inverse_dark.png      source runtime
    03_isentropic_table_dark.png             source runtime
    04_isentropic_reference_compare_dark.png source runtime
    05_isentropic_calculator_light.png       source runtime
    06_isentropic_table_light.png            source runtime
    07_isentropic_charts_dark.png            source runtime
    08_executable_calculator_dark.png        packaged executable

**Provenance, stated plainly.** 01–07 were rendered from the source runtime
with `QQuickWindow.grabWindow`, which draws the live scene offscreen; the QML
and the backend are the same files the executable bundles. 08 is the packaged
executable, captured with `PrintWindow`.

The split is not a preference. Capturing further executable states needs
synthetic input, and there are only two ways to deliver it: real desktop input,
which the harness **refuses** unless RocketForge owns the foreground — it
aborted correctly when a browser window held focus — or window-targeted posted
messages, which reach a Qt `TapHandler` only intermittently and leave
`PrintWindow` returning a blank surface. Rendering the scene directly avoids
both problems and produces a deterministic picture of the same code.

## UI files changed

    ui/pages/IsentropicPage.qml                    rewritten (this page's own workspace)
    ui/pages/isentropic/*.qml                      new
    ui/components/RFEngineeringTable.qml           new, reusable
    ui/components/RFBoundNumberField.qml           new, reusable
    ui/Main.qml                                    status-bar flag only
    ui/shell/StatusBar.qml                         `computed` property
    ui/data/Navigation.qml                         `computed: true` on one entry

**Shared component changes, declared.** Two files outside the Isentropic
workspace were touched, both for the same reason: the status bar stated
flatly *"All values are mock data"* and *"No solver in this build"*. Those
became false the moment a page started computing. A status bar that misreports
the trustworthiness of what is on screen is worse than none, so it now takes a
`computed` flag, derived from a `computed: true` marker on the navigation
entry — no page index is hard-coded, and every other module is unaffected
because the key is absent there. Nothing visual changed on any other page.

## Physics files changed

    None.

## New physics added

    None.

## Reusability

`RFEngineeringTable` and `EngineeringTableModel` contain no compressible-flow
knowledge: the model holds column definitions and a float64 block, and the view
renders whatever it is given. A test populates the model with normal-shock
column headings to demonstrate it. The same pair will serve the Normal Shock,
Prandtl-Meyer, Fanno and Rayleigh tables without modification, and
`reference_comparison` is structured so a second published dataset only needs
its own recipe map.

## Ready for Phase 4C

**YES.** The vertical slice works end to end and the pattern is reusable:
verified physics → Qt-free service → controller → generic table model → QML.
Nothing of Phase 4C was started.
