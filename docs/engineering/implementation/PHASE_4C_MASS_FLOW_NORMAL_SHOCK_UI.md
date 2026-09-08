# Phase 4C — Mass Flow, Choking and Normal Shock

Physics → application → interface → packaged executable, for two modules.
Everything below was implemented against Phase 3, verified, and rebuilt.

    1589 passed, 1 skipped        (1049 at the start of the phase)
    0 QML warnings across all three analysis pages and all nine sections
    1008 Appendix B values compared: 1006 PASS, 2 REVIEW, both explained

---

## 1. What was built

**Physics** (`rocketforge/physics/compressible/`)

    mass_flow.py        311 lines   the mass-flow parameter, choking, the critical condition
    normal_shock.py     515 lines   the jump relations, four inverses, the strong-shock limits
    equations.py        +4 records  mass_flow.parameter.v1, mass_flow.choked.v1,
                                    normal_shock.jump.v1, normal_shock.pitot.v1

**Application** (`rocketforge/application/analysis/`)

    presentation.py            101   shapes shared by all three analysis services
    analysis_behaviour.py      275   shared controller behaviour (not a QObject — see §6)
    mass_flow_service.py       467   Qt-free: solve, choking report, tables
    normal_shock_service.py    385   Qt-free: solve, limits, tables
    mass_flow_controller.py    545   the Qt surface for the Mass Flow page
    normal_shock_controller.py 580   the Qt surface for the Normal Shock page
    reference_comparison.py    generalised from one hard-wired table to a dataset registry

**Interface** (`ui/`)

    components/RFLineChart.qml           159   physics-agnostic single-series plot
    pages/MassFlowPage.qml                     host: header, sections, workspace
    pages/massflow/*.qml                 793   Calculator, Table, Charts
    pages/NormalShockPage.qml                  host
    pages/normalshock/*.qml            1 029   Calculator, Table, Charts
    Main.qml                             one binding (see §7)
    data/Navigation.qml                  `computed: true` on two entries

**Reference data**

    rocketforge/data/reference/anderson6_appendix_b_normal_shock.json
    168 rows, M₁ = 1.00 … 50.00, γ = 1.4, seven columns, pp. 1085–1088

---

## 2. The canonical normalisation, stated once

Textbooks normalise mass flow half a dozen ways. RocketForge uses one, declared
in the module docstring and nowhere else:

    MFP(M, γ) = ṁ √(R T₀) / (A p₀)
              = √γ · M · [1 + (γ−1)/2 · M²] ^ −(γ+1)/(2(γ−1))

Every dimensional quantity in the module is that group rearranged. `mass_flow`,
`mass_flux`, `choked_mass_flow` and `choked_mass_flux` are the same relation
evaluated or divided, never a second formula, and the tests assert exactly that
rather than checking each against a number typed into a test file.

Two relations in `normal_shock.py` are likewise composed rather than restated:

* `T₂/T₁` is `(p₂/p₁) / (ρ₂/ρ₁)`, so the ideal gas law holds across the shock to
  machine precision instead of only to round-off;
* `p₀₂/p₁` — the Rayleigh pitot ratio — is `(p₀₂/p₀₁) × (p₀₁/p₁)`, reusing two
  verified relations instead of introducing a third.

`T₀₂/T₀₁` is a literal `1.0`, not a computed ratio, because the shock is
adiabatic and a computed value could only drift away from the truth.

---

## 3. The inverse that is not a second solve

For a fixed area and stagnation state,

    ṁ / ṁ_choked  =  MFP(M)/Γ  =  A*/A  =  1 / (A/A*)

because the same mass flow passes both the station and its own sonic throat.
`mach_from_mass_flow_ratio` therefore **calls** `isentropic.mach_from_area_ratio`
and inherits every bracket, tolerance and near-sonic diagnostic verified in
Phase 4B, rather than conditioning a second solve of the same curve. The
identity is asserted directly on a 600-point grid, and a spy test fails if a
bespoke solve is ever introduced in its place.

The normal shock needed four inverses; three are closed form and one iterates:

    p₂/p₁   → M₁   closed form
    ρ₂/ρ₁   → M₁   closed form
    M₂      → M₁   closed form — the relation is an involution, so it is
                   `mach_downstream` evaluated at M₂, not a second formula
    p₀₂/p₀₁ → M₁   the only iteration in this phase; Brent on a monotone curve

A test asserts that all four recover the same M₁ from one shock: four
measurements of one flow must name one flow.

---

## 4. Reference verification against Appendix B

168 rows extracted from the user-supplied PDF, screened before use against
constraints that depend on none of our equations (p₂/p₁ ≥ 1, 0 < p₀₂/p₀₁ ≤ 1,
M₂ ≤ 1, and the ideal gas law at printed precision), and checked visually
against the rendered pages at four Mach numbers.

γ was **established, not assumed**, from three independent asymptotes of the
table's own values: ρ₂/ρ₁ → 5.988 at M₁ = 50 against the limit (γ+1)/(γ−1) = 6;
M₂ → 0.3784 against √((γ−1)/2γ) = 0.37796; and p₀₂/p₁ = 1.893 at M₁ = 1, which
is the isentropic p₀/p at Mach 1.

**One extraction defect, corrected against the page.** The PDF text layer gave
p₀₂/p₀₁ = 9.994 at M₁ = 1.08; the rendered page prints `0.9994 + 00`. A
stagnation-pressure ratio above 1 across a shock is thermodynamically
impossible, so the structural screen caught it. It is recorded in the dataset
under `extraction_corrections` with the evidence.

**Comparison result: 1008 values, 1006 PASS, 2 REVIEW.**

The two are p₀₂/p₀₁ at M₁ = 5.9 and 6.9. They were investigated before anything
was touched:

| | M₁ = 5.9 | M₁ = 6.9 |
|---|---|---|
| printed | `0.3180 − 01` | `0.1635 − 01` |
| exact (40 digits, exact rationals) | 0.031794993234822601 | 0.016344974693931645 |
| correctly rounded | `0.3179 − 01` | `0.1634 − 01` |
| short of the rounding boundary by | 6.8 × 10⁻⁹ | 2.5 × 10⁻⁸ |
| …as a fraction of a half-unit | 0.0014 | 0.0051 |

Both printed values were confirmed by rendering book page 1087 and reading the
glyphs. An independent 40-digit `Decimal` evaluation from exact `Fraction(7,5)`
arithmetic — sharing no code with `rocketforge` — reproduces the RocketForge
value to every digit RocketForge carries. So these are rounding-boundary ties:
the exact values sit a thousandth of a rounding unit below the point where the
last digit rounds up, and the source rounded up where round-to-nearest does not.

**Nothing was adjusted.** Not the equations, not the tolerance. The two rows are
recorded in the dataset under `print_rounding_ties` with their evidence, and the
expected outcome — 1006 PASS, 2 REVIEW, at exactly those two Mach numbers — is
pinned in `expected_comparison_outcome` and asserted by the test suite, so a
*new* disagreement anywhere in the table fails rather than blending into an
approved count. A further test asserts that each REVIEW misses by between 1.000
and 1.01 half-units: a real defect would not land there, it would land somewhere
arbitrary.

The Normal Shock page states this in its own words when a comparison reports a
review, rather than leaving it buried in a test.

**The detector was tested.** Perturbing one value in a *copy* of the fixture is
detected as REVIEW; shifting a whole row's columns left is detected on five of
six quantities; a perturbation of a third of the last printed digit is correctly
**not** flagged, because a detector that cries wolf makes every REVIEW
meaningless. The real dataset is byte-identical before and after.

**Mass flow has no published appendix, and none was invented.** Anderson
publishes no mass-flow table. The Mass Flow page says so on the page itself and
explains what stands in its place: the identity ṁ/ṁ* = A*/A, whose area ratio
*is* checked value-by-value against Appendix A, plus dimensional scaling tests
(ṁ ∝ A, ∝ p₀, ∝ 1/√T₀, ∝ 1/√R) and a hand-worked dimensional case.

---

## 5. Three defects found, and what was done

**5.1 `SubsonicShockError` was never raised.** The taxonomy declared it; the
module raised a plain `DomainError` because a re-raise wrapper matched on the
wrong substring. Fixed by wrapping only the bound check — the one call that can
fail that way — so no string sniffing is involved. `SubsonicShockError`
subclasses `DomainError`, so every existing handler still catches it.

**5.2 The strong-shock limit let its own round-off through.** `ρ₂/ρ₁ = 6.0` —
the number every textbook prints for air — passed a `>= limit` guard, because
`(γ+1)/(γ−1)` evaluates to 6.000000000000001 in float64. The inverse then
returned **M₁ = 1.6 × 10⁸** as a valid answer. An exact comparison cannot be made
robust here: the limit inherits the rounding of `γ − 1`. The guard now tests the
condition that actually fails — the denominator standing clear of its own
cancellation — which catches the exact-limit case and refuses nothing whose
answer was worth reporting (a shock at M₁ = 1000 still solves). Both inverses
carry it, and a regression test types the textbook value in.

**5.3 A subclass property with an inherited notify signal corrupts the
metaobject.** The two controllers first shared a `QObject` base class. PySide6
builds a **corrupt metaobject** when a subclass declares
`Property(..., notify=Base.someSignal)`: the notify index points into the base's
metaobject, and the first QML access segfaults the process — no exception, no
warning, no output. Diagnosed by walking the metaobject in Python, which faults
in the same place.

The base class is now `AnalysisBehaviour`, a plain mixin holding the behaviour,
and each controller declares its own signals and properties. That leaves a
visible block of property boilerplate in each controller; it is the honest cost
of the constraint, and preferable to a base class that crashes when someone adds
one more property. Two tests guard it: one walks every property of all three
controllers and asserts its notify signal resolves inside its own metaobject;
the other asserts structurally that each controller declares its signals itself.

---

## 6. A stated numerical limit, not a defect

The stagnation-pressure loss of a weak shock goes as (M₁²−1)³:

    1 − p₀₂/p₀₁  →  [2γ / (3(γ+1)²)] · (M₁² − 1)³

For M₁ − 1 below roughly 10⁻⁵ that is smaller than the spacing of doubles near
1, so `p₀₂/p₀₁` rounds to 1 give or take an ulp — occasionally an ulp *above* 1
— and the entropy rise rounds to zero. **Nothing is clamped to hide this.** The
loss really is unresolvable there, and a shock that weak is a Mach wave.

The module docstring states it, and the tests assert both halves: from
M₁ − 1 = 10⁻⁴ upward the computed loss follows the cubic law above and every
invariant holds strictly; below it, the relations are asserted to be
indistinguishable from no shock within 8 ulp. A clamp would have made the test
green while making the statement false.

---

## 7. Verification

    tests/physics/compressible/test_mass_flow.py                82
    tests/physics/compressible/test_normal_shock.py            138
    tests/physics/compressible/test_phase_4c_inverses.py       173
    tests/physics/compressible/test_phase_4c_reference_cases.py 26
    tests/application/test_mass_flow_service.py                 48
    tests/application/test_normal_shock_service.py              40
    tests/application/test_phase_4c_controllers.py              33
    ------------------------------------------------------------
    added                                                      540
    whole suite                                    1589 passed, 1 skipped

Every physics test runs at γ ∈ {1.2, 1.3, 1.4, 1.66}, so no relation can quietly
assume air. Beyond the reference comparison, the physics is held to what the
equations *mean*: the mass flow has a unique maximum at Mach 1 with a single
sign change in its derivative; the downstream flow is always subsonic; entropy
increases monotonically for every real shock; the density ratio stays below
(γ+1)/(γ−1) with a shortfall matching 2/(2 + (γ−1)M₁²) exactly; M₂ approaches
its limit as O(1/M₁²), checked by requiring each tenfold rise in M₁ to cut the
excess by a hundred.

**Cross-module.** p₀₂/p₀₁ is reconstructed by a different route —
(p₀₂/p₂)·(p₂/p₁)·(p₁/p₀₁), with the outer terms from the isentropic module —
and required to agree to 10⁻¹². If the two modules ever disagreed, that is where
it would show.

**State regression.** Mode changes replace the input rather than reinterpreting
it; a refused range clears the table, its marker, its selection and its
comparison instead of leaving the previous one on screen under new settings; an
invalid input keeps the previous reading visible but marks it stale and
publishes no readout rows; the chart and the table are asserted to read the same
computed block.

**The Isentropic page, unregressed.** The §8 case is a test and a screenshot:
after solving A/A* = 2 on both branches, switching to Mach 2 leaves
`branchRequired` false, `bothBranches` empty and A/A* = 1.68750, and its own
Appendix A comparison still reports 0 review.

---

## 8. Interface

Both pages follow the Isentropic page exactly: a host with a header, an internal
section selector, and one of three workspaces. **No equation is in any QML
file** — the only `Math.*` calls are `min`/`max` for column widths and the
log-axis pixel mapping in `RFLineChart`, which is the same pattern the accepted
Isentropic charts already use.

Two things the interface says rather than hides:

* **Dimensionless and dimensional are separated.** MFP needs only γ; kilograms
  per second additionally need R, an area and a stagnation state. When those are
  missing the dimensional rows are shown as *unavailable*, never as zero, and
  the page says what is needed. Same for the shock's optional upstream p₁ and T₁.
* **Which mode iterates.** Four of the five shock inverses are exact
  rearrangements and one is a root solve. The page says so, because a reader
  should be able to tell where an answer came from.

The readouts are laid out in two columns. The first capture showed both results
panels clipping their last rows at 1600×900; a result you have to scroll for is
a result you read wrong, and the panel is wide enough that two columns is the
right answer rather than a scrollbar.

**One shared file changed, declared.** `ui/Main.qml`, one binding: the status bar
drew its chips from `MockData` on every page, so a computed Mass Flow page
reading *Subsonic* sat above a status bar asserting *"Supersonic · Case 01"*. On
a computed page those mock chips are now dropped; the trailing text still says
where the numbers came from. Nothing visual was otherwise touched, and the
Engine Design side is untouched entirely.

---

## 9. Executable

    C:\Users\erayh\Documents\Python\rocket\dist\RocketForge\RocketForge.exe
    185 MB directory build, clean rebuild from packaging/RocketForge.spec

The spec needed **no change**: it already bundles the whole of `ui/` and the
whole reference directory, so the new QML subdirectories, `RFLineChart.qml` and
Appendix B are carried automatically. Verified in the bundle: `numpy` present,
`scipy` **absent**, both appendices present, all six new QML files present.

The frozen reference path was tested against the real bundle by resolving
`sys._MEIPASS` to `dist/RocketForge/_internal`: both datasets load from there and
the whole Appendix B comparison runs — 1008 values, 1006 pass, 2 review, the same
numbers as from source. That is the failure that would otherwise have passed
every test and shown up only in the shipped build.

The executable launches and stays up; its window renders the analysis workspace
with the bundled backend, NumPy and the bundled Appendix A comparison all live.

---

## 10. Screenshots

    C:\Users\erayh\Documents\Python\rocket\acceptance\phase_4c\

    01_mass_flow_calculator_dark.png            source runtime
    02_mass_flow_choked_dark.png                source runtime
    03_mass_flow_branches_dark.png              source runtime
    04_mass_flow_table_dark.png                 source runtime
    05_mass_flow_table_dimensional_dark.png     source runtime
    06_mass_flow_charts_dark.png                source runtime
    07_normal_shock_calculator_dark.png         source runtime
    08_normal_shock_inverse_dark.png            source runtime
    09_normal_shock_reference_compare_dark.png  source runtime
    10_normal_shock_charts_reference_dark.png   source runtime
    11_mass_flow_calculator_light.png           source runtime
    12_normal_shock_table_light.png             source runtime
    13_isentropic_regression_dark.png           source runtime
    14_executable_landing_dark.png              packaged executable

**Provenance, stated plainly.** 01–13 were rendered from the source runtime with
`QQuickWindow.grabWindow`, which draws the live scene offscreen; the QML and the
backend are the same files the executable bundles. 14 is the packaged
executable, captured with `PrintWindow`.

14 shows the executable's **landing page**, not a Phase 4C page, and is named for
what it shows. Reaching Mass Flow inside the packaged process needs synthetic
desktop input, which the harness refuses unless RocketForge owns the foreground.
The packaged build's Phase 4C behaviour is evidenced instead by the frozen-path
check in §9, which runs the Appendix B comparison out of the shipped bundle.

---

## 11. Scope

Built: mass flow, choking, the critical condition, the normal-shock jump
relations, their inverses, both pages with Calculator, Table and Charts, the
Appendix B comparison, and the rebuilt executable.

Not built, and deliberately not started: oblique shock, θ–β–M, Prandtl–Meyer,
Fanno, Rayleigh, nozzle regimes, thrust, Cf, c*, Isp, CEA/Cantera/CoolProp,
injector, chamber, cooling, pump, turbine, engine-cycle solver.

`is_choked` is scoped to a convergent passage discharging to a receiver and is
**not** a nozzle regime classifier — the page says so in as many words, and a
test asserts the word "nozzle" does not appear in its verdict.

Stopping here, as instructed.
