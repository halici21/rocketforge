# Phase 4E — Fanno Flow and Rayleigh Flow

# Verdict

**READY FOR PHASE 4F**

Physics → application → interface → packaged executable, for two modules.
Everything below was implemented against Phase 3, verified, and rebuilt.

    3892 passed, 1 skipped        (2756 at the start of the phase)
    1136 of those are Phase 4E
    41 architecture tests green, unchanged
    0 QML warnings across twelve pages, three sections each, two themes, plus Engine Design
    2 published reference tables located, 90 printed values compared, 90 PASS

The one thing worth reading first: **the supplied Anderson volume has no Fanno
appendix and no Rayleigh appendix.** None was invented. Section 5 says what was
found instead and why it is enough.

---

## Baseline

    2756 passed, 1 skipped
    41 architecture tests green
    Isentropic, Mass Flow, Normal Shock, Oblique Shock and Prandtl–Meyer
    open with 0 QML warnings

---

## 1. Files created

**Physics** (`rocketforge/physics/compressible/`)

    fanno.py       649 lines   five ratios, 4 f_F L*/D, both inverses, duct solve
    rayleigh.py    584 lines   five ratios, both critical points, heat solve

**Application** (`rocketforge/application/analysis/`)

    fanno_service.py          530 lines   rows, groups, table blocks, status prose
    rayleigh_service.py       546 lines   the same for heat exchange
    fanno_controller.py       673 lines   the QML-facing adapter
    rayleigh_controller.py    666 lines   the QML-facing adapter
    reference_validation.py   219 lines   what backs the numbers, when no table exists

**Interface** (`ui/`)

    pages/FannoPage.qml                80 lines
    pages/RayleighPage.qml             81 lines
    pages/fanno/FannoCalculator.qml   524 lines
    pages/fanno/FannoTable.qml        324 lines
    pages/fanno/FannoCharts.qml       189 lines
    pages/rayleigh/RayleighCalculator.qml   498 lines
    pages/rayleigh/RayleighTable.qml        333 lines
    pages/rayleigh/RayleighCharts.qml       219 lines

**Reference data** (`rocketforge/data/reference/`)

    fanno_nasa_tm_2006_214086.json
    rayleigh_nasa_tm_2006_214086.json

**Tests**

    test_fanno.py, test_fanno_inverse.py
    test_rayleigh.py, test_rayleigh_inverse.py
    test_phase_4e_reference_cases.py
    test_phase_4e_reuse.py
    test_phase_4e_controllers.py

---

## 2. Files modified

    rocketforge/physics/compressible/types.py   + FannoState, FannoDuctResult,
                                                  RayleighState, RayleighDuctResult
    rocketforge/core/tolerances.py              + fanno_tol, rayleigh_tol (1e-12)
    rocketforge/application/analysis/
        reference_comparison.py                 _reference_root() made public as
                                                reference_root(), and shared
    main.py                                     Fanno and Rayleigh registered;
                                                eight singletons reach QML
    ui/data/Navigation.qml                      two entries, computed: true
    ui/components/RFEngineeringTable.qml        second marked row; marker gutter
    ui/components/RFLineChart.qml               reports whether a log axis applied
    tests/core/test_tolerances.py               field-set gate widened

No production module outside this list was touched. Engine Design was not
opened. The frozen physics — Brent, PerfectGas, Isentropic, Area–Mach, Mass
Flow, Normal Shock, Prandtl–Meyer, Oblique Shock — was not edited, and no
erratum against it was needed this phase.

---

## 3. Fanno physics

Adiabatic, constant area, wall friction. `T₀` is constant along the duct and
the entropy rise shows up entirely as stagnation-pressure loss.

    T/T*    = (γ+1) / (2 + (γ-1)M²)
    p/p*    = (1/M) sqrt(T/T*)
    ρ/ρ*    = (1/M) sqrt(T*/T)
    V/V*    = M sqrt(T/T*)
    p₀/p₀*  = (1/M) [ (2 + (γ-1)M²) / (γ+1) ] ^ ((γ+1)/(2(γ-1)))
    4f_F L*/D = (1-M²)/(γM²) + (γ+1)/(2γ) ln[ (γ+1)M² / (2 + (γ-1)M²) ]

**The friction convention is stated everywhere it appears.** The duct group is
the Fanning form `4 f_F L*/D`; `f_D = 4 f_F`, so `f_D L*/D` is the identical
number. Both are printed side by side in the calculator, the second labelled
*identical group*, because an engineer holding a Moody-chart `f_D` should not
have to divide by four on trust. `darcy_to_fanning` and `fanning_to_darcy` are
the only conversion path, and no label anywhere in the interface reads a bare
`fL/D`.

Two coincidences are real, and both are asserted rather than assumed:

    fanno.temperature_ratio(M)             == isentropic.temperature_ratio_star(M)
    fanno.stagnation_pressure_ratio(M)     == isentropic.area_ratio(M)

The second is not a numerical accident: `p₀A*` is fixed for a given mass flow
and `T₀`, so the Fanno stagnation-pressure ratio *is* the isentropic area
ratio. That is what lets a Fanno column be checked against a published table
this application already holds — see section 5.

**The supersonic ceiling.** `4f_F L*/D` falls to zero at `M = 1` from both
sides, and on the supersonic branch it is bounded above:

    limit as M → ∞ = 0.8215081165        (γ = 1.4, recomputed: diff 1.9e-11)

No supersonic Fanno duct longer than that can be run without a shock, and the
chart says so under the curve.

---

## 4. Rayleigh physics

Frictionless, constant area, heat exchange through the state relation only.

    p/p*    = (1+γ) / (1 + γM²)
    T/T*    = M² (1+γ)² / (1 + γM²)²
    ρ/ρ*    = (1 + γM²) / ((1+γ)M²)
    T₀/T₀*  = ((1+γ)M²  (2 + (γ-1)M²)) / (1 + γM²)²
    p₀/p₀*  = ((1+γ)/(1+γM²)) [ (2 + (γ-1)M²)/(γ+1) ] ^ (γ/(γ-1))

**The two maxima are different things and are never labelled alike.** This is
the single most misleading mistake the module could make, so it is guarded in
four places — the physics, the controller, the table and the chart:

    static temperature maximum   M = 1/sqrt(γ) = 0.8451542547
                                 value (γ+1)²/(4γ) = 1.0285714286
    stagnation temperature max   M = 1 exactly, value exactly 1
    supersonic T₀/T₀* floor      (γ²-1)/γ² = 0.4897959184

All three recompute to a difference of exactly 0.0 against their closed forms.
Between `M = 1/√γ` and `M = 1` the static temperature *falls* while heat is
still being added: the flow accelerates fast enough that the kinetic-energy
rise outruns the heat put in. The chart in
`10_rayleigh_temperature_chart_dark.png` is that sentence as a picture, with
the two critical Mach numbers drawn as separately labelled guides — `T max`
and `Sonic`.

**One inverse is deliberately absent.** `T/T*` is not monotone on the subsonic
branch — it rises to the maximum at `1/√γ` and falls again — so a `T/T*`
inverse has two subsonic roots *and* the branch flag cannot separate them. The
module does not offer that inversion rather than offer an ambiguous one.
`T₀/T₀*` is monotone on each branch and is inverted, branch required.

---

## 5. Reference confirmation — no invented tables

The supplied Anderson volume, *Fundamentals of Aerodynamics*, 6th edition, has
appendices A (isentropic), B (normal shock), C (Prandtl–Meyer) and D/E
(standard atmospheres). **It has no Fanno table and no Rayleigh table.** Phase
4E section 7 forbids inventing one for visual symmetry, and none was invented.
The table pages say this in plain words where a comparison panel would be, and
then say what does back the numbers.

Section 99 makes external confirmation blocking, so one was found:

> NASA/TM-2006-214086, *User Guide for Compressible Flow Toolbox Version 2.1
> for Use With MATLAB Version 7*, Kevin J. Melcher, NASA Glenn Research Center,
> January 2006.

It tabulates both families, and both are now shipped as data:

    Fanno      Example 4.11, Table 4.3    30 printed values,  6 Mach numbers
    Rayleigh   Example 4.24, Table 4.7    60 printed values, 12 Mach numbers

Each printed value is compared at half a unit in its own last printed figure —
the published digits are the tolerance, not a hand-picked epsilon. All 90 pass.

Six named checks back each module, and the interface shows them rather than a
bare PASS:

**Fanno** — the published table value by value · the friction convention itself
(a Darcy reading would be four times smaller, so agreement confirms the
convention and not only the algebra) · `p₀/p₀*` against Anderson Appendix A ·
`T/T*` against Anderson Appendix A · the Fanno–Rayleigh intersection theorem ·
γ-general identities at γ = 1.2, 1.3, 1.4, 1.66.

**Rayleigh** — the published table value by value · the report's worked inverse
roots on both branches · the Fanno–Rayleigh intersection theorem · both
critical points in closed form · every starred ratio asserted *different* from
its isentropic counterpart, which is what a copy-paste between modules would
break · the same four γ.

### The intersection theorem

The two states either side of a normal shock lie on a common Fanno line **and**
a common Rayleigh line. So the ratios between them, computed from the new
modules, must equal the shock's own — which are already checked against
published Appendix B. Recomputed now:

    M₁ = 1.5   M₂ = 0.7010887   largest disagreement 4.4e-16
    M₁ = 2.0   M₂ = 0.5773503   largest disagreement 2.2e-16
    M₁ = 3.0   M₂ = 0.4751910   largest disagreement 4.4e-16
    M₁ = 5.0   M₂ = 0.4152274   largest disagreement 3.6e-15

That ties both new modules to a published table at machine precision, without
either module ever reading one.

---

## 6. Tables are never the solver

Every number on both pages is computed from the relations above. The shipped
JSON files are read in exactly one place — the validation panel and its tests —
and never on the path from a user's input to an answer. There is no
interpolation of a published row anywhere in the phase.

---

## 7. Nothing is silently clamped

Section 129 is explicit, and it is honoured on both pages: a requested duct
longer than the length available to sonic is **not** turned into the sonic
length, and heat beyond the maximum is **not** turned into the choking heat.

    fanno.downstream_mach(0.3, 10.0, air)     → no_solution, FRICTION_CHOKED, value None
    rayleigh.heat_addition(0.3, 10.0, air)    → no_solution, THERMALLY_CHOKED, value None

The interface reports the limit *and* preserves the request, with no downstream
state at all — `03_fanno_choked_dark.png` and `08_rayleigh_choked_dark.png`:

    Requested 4f_F L/D        10.0000        Requested T₀₂/T₀₁      10.0000
    Available before M = 1     5.29925       Maximum before M = 1    2.88300
    Excess length              4.70075       Excess                  7.11700
    Requested / available      1.88706       Requested / maximum     3.46860

There is no `M₂` row in either choked block. Not a blank one — none. A stale
outlet Mach number left on screen next to a choking warning is exactly the
failure the specification names, and the block is built without that row rather
than built with it and cleared.

---

## 8. Branch discipline

Both inverses require a branch and fail closed without one:

    ValueError: branch must be a FlowBranch, got 'subsonic'. The friction
    parameter falls to zero from both sides of the sonic point, so the caller
    must state which duct is meant.

The branch control appears in the calculator only when the selected mode
actually needs one (`Fanno.modeNeedsBranch`), so it is never a decoration.
Recomputed inverses, against Phase 3 section 11.7/11.8:

    4 f_F L*/D at M = 0.5      1.0690603127   diff 1.8e-11
    inverse, subsonic          0.5000000000   diff 2.2e-12
    inverse, supersonic        1.9999999997   diff 2.7e-10
    T₀/T₀* at M = 0.5          0.6913580247   diff 8.6e-12
    inverse, subsonic          0.5000000000   diff 3.3e-13

## 9. Finite segments

    M₁ = 0.3, 4fL/D = 3.0   →  M₂ = 0.4005096605   remaining 2.2992531049
    M₁ = 0.2, T₀₂/T₀₁ = 2   →  M₂ = 0.300134555

Both match Phase 3. The Fanno remainder is exact arithmetic on the friction
length — `5.2992531051 - 3.0` — which is the additive property of the group
made visible rather than a second solve.

The friction convention switch implements Policy A: switching a duct given as
`f_D = 0.02, L = 5 m, D_h = 0.1 m` to the Fanning convention changes the field
to `0.005` and leaves `4fL/D = 0.2` untouched. The same physical duct, stated
two ways; the answer does not move. `02_fanno_segment_dark.png` shows it, with
the explanation under the control.

---

## 10. Interface

Three sections per page, matching every earlier analysis module: Calculator,
Table, Charts.

**No equations in QML.** The new QML contains no gamma exponent, no root
finding, no friction-factor conversion and no gas-dynamic algebra of any kind —
verified by grep over the eight new files plus the two shared components. Layout
arithmetic only.

**Two shared components were generalised rather than forked**, as sections
77/83 require:

*RFEngineeringTable* gained a second marked row, because Rayleigh has two
critical rows that mean different things. It also gained a measured marker
gutter: the label used to be drawn in the first column's padding, which was
fine for `SONIC` and `CHOKED` but printed `SONIC · CHOKING` straight through a
Mach number. The gutter is now computed from the actual label and the actual
marked cell, so it is zero for every table that already fitted — Normal Shock's
layout is unchanged, photographed in `14_shared_table_component_regression.png`
— and just wide enough where it is not. Pages size their columns from the new
`valueAreaWidth`, so a gutter can never push the last column out of view.

*RFLineChart* now reports whether a requested log axis actually applied. It
cannot apply when the data touches zero, and the Fanno friction parameter is
*exactly* zero at the sonic point, so the toggle appeared to do nothing. It now
says `not applied — the data reaches zero` beside the switch
(`05b_fanno_chart_log_declined_dark.png`). The refusal itself was already
correct; only the silence was wrong.

Both branches are delivered to every chart as separate series, never one array
containing `M = 1`.

---

## 11. Numerical behaviour

    fanno_tol      1e-12
    rayleigh_tol   1e-12

Both inverses use the frozen Phase 4A Brent solver with its two-tier halving
safeguard; no new root finder was written, and there is still exactly one in
the codebase. The sonic point is returned exactly rather than converged to:
`4f_F L*/D(1) = 0`, `T₀/T₀*(1) = 1`, `T/T*(1) = 1` are literals, because a
printed `0.9999999997` invites a reader to wonder what was lost.

---

## 12. Performance

    Fanno forward sweep, 100 000 Mach samples      1.92 ms
    Fanno full state, 5 000 rows                   0.16 ms
    Rayleigh forward sweep, 100 000 Mach samples   1.02 ms
    Rayleigh full state, 5 000 rows                0.12 ms
    one Fanno inverse (subsonic / supersonic)      0.130 / 0.125 ms
    one Fanno duct solve                           0.210 ms
    one Rayleigh inverse (subsonic / supersonic)   0.062 / 0.081 ms
    one Rayleigh heat solve                        0.121 ms

Tables are vectorised — a 5 000-row table costs a tenth of a millisecond
because it is six array evaluations, not 5 000 solves. No threading was added
and none is warranted.

---

## 13. Architecture, isolation and audit

    architecture test     PASS, 41 tests, unchanged and not weakened
    Qt isolation          PASS — both modules import and run their forward
                          relations, both inverses, the duct solve and the heat
                          solve with PySide6 blocked from the process
    scipy / pandas / numba in production      0 imports
    PySide6 under physics / core / engineering  0 imports (one docstring mention)
    duplicate root solvers                      0
    gas-dynamic equations in QML                0
    bare `fL/D` labels                          0

---

## 14. Regression

    3892 passed, 1 skipped
    0 QML warnings — twelve pages × three sections × two themes, plus Engine Design

`13_previous_modules_regression.png` shows Isentropic at M = 2 with all four
Appendix A checks still PASS. `14_shared_table_component_regression.png` shows
the Normal Shock table after the shared-component change: same columns, same
widths, marker still where Phase 4C put it.

---

## 15. Executable

    build              clean rebuild, exit 0
    size               191.8 MB across 2 067 files, dist/RocketForge/
    launch             starts and stays alive
    numpy              present
    scipy / pandas     absent
    tests              not bundled
    textbook PDF       not bundled
    Appendices A/B/C   present and loading
    Fanno + Rayleigh reference JSON   present and loading
    Fanno + Rayleigh QML              present
    shared components  the shipped copies carry both fixes

The frozen reference path was exercised by pointing `sys._MEIPASS` at the real
bundle and running the validation panel from there: both modules returned PASS
from the shipped data, not from the source tree. That check exists because the
first version of the reference lookup had a second copy of the path logic,
which would have failed only inside the executable.

`15_packaged_executable_dark.png` is the built exe itself, captured with
PrintWindow — no synthetic input was sent to it.

---

## 16. Screenshots

`acceptance/phase_4e/`

    01_fanno_state_subsonic_dark.png          M = 0.5, full starred state
    02_fanno_segment_dark.png                 a duct that fits, Darcy convention
    03_fanno_choked_dark.png                  requested > available, no M₂
    04_fanno_table_dark.png                   generated table + validation panel
    05_fanno_chart_dark.png                   4f_F L*/D → 0 at sonic, both sides
    05b_fanno_chart_log_declined_dark.png     log axis requested, and why it cannot
    06_rayleigh_state_dark.png                M = 0.5, both critical points
    07_rayleigh_heat_transition_dark.png      T₀₂/T₀₁ = 1.5, margin still available
    08_rayleigh_choked_dark.png               requested > maximum, no M₂
    09_rayleigh_table_dark.png                both marked rows, labelled apart
    10_rayleigh_temperature_chart_dark.png    the two maxima, in one frame
    11_fanno_light.png                        light theme
    12_rayleigh_light.png                     light theme
    13_previous_modules_regression.png        Isentropic unchanged
    14_shared_table_component_regression.png  Normal Shock table unchanged
    15_packaged_executable_dark.png           the built exe

Provenance: 01–14 are `QQuickWindow.grabWindow` renders of the live scene graph
from the source runtime, driven through the same controller properties the
interface binds to. They are offscreen renders, so they cannot be disturbed by
anything else on the desktop, and no synthetic input was used. 15 is the
packaged executable.

---

## 17. Runtime dependencies added

None. PySide6 and numpy, as before.

---

## 18. Errata

None against RocketForge this phase.

Two source anomalies were recorded rather than smoothed over, both in earlier
phases and both still standing: the Anderson Appendix A `M = 16` row prints
`T₀/T = 52.29` where the exactly-linear relation gives `52.20` (216 of 217 rows
satisfy it), and the Appendix B pair reported in Phase 4C. Published values are
preserved as printed and reported as REVIEW; nothing was tuned to match them.

---

## 19. Scope

Implemented: Fanno flow, Rayleigh flow, their inverses, finite duct segments,
heat transitions, choking limits, tables, charts, reference validation.

Not implemented, and deliberately: converging–diverging nozzle flow, back-pressure
regimes, shock location in a nozzle, thrust, `C_f`, `c*`, `I_sp`, thermochemistry,
CEA/Cantera/CoolProp, injectors, chambers, cooling, pumps, turbines, engine-cycle
solving. Stopped after Fanno and Rayleigh, as instructed.
