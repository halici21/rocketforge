# Phase 4F — Quasi-1D C-D Nozzle, Back-Pressure Regimes and the Internal Shock

# Verdict

**READY FOR PHASE 4G**

Physics → application → interface → packaged executable, for the module that
integrates every previous one.

    4494 passed, 1 skipped        (3892 at the start of the phase)
    602 of those are Phase 4F (606 nozzle tests run, 4 shared with earlier phases)
    41 architecture tests green, unchanged and not weakened
    0 QML warnings — 12 pages x 3 sections x 2 themes, plus Engine Design
    7 of 7 regimes implemented, tested and reachable in the interface

**Read this first: `PHASE_3_SPEC_CONFLICT`.** Phase 3 §10.6's worked
internal-shock example contradicts §12.4's mandatory pseudocode, and the
example is the one that is wrong — its numbers lose 38% of the mass flow across
the exit plane. Raised before the affected code was written, proved with an
independent oracle, recorded in
`docs/engineering/ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md`, and section 4 below
gives the whole argument.

---

## Baseline

    3892 passed, 1 skipped
    41 architecture tests green
    Isentropic, Mass Flow, Normal Shock, Oblique Shock, Prandtl–Meyer, Fanno
    and Rayleigh open with 0 QML warnings

---

## 1. Files created

**Physics** (`rocketforge/physics/compressible/`)

    geometry.py    398 lines   AreaDistribution, monotone cubic interpolation
    nozzle.py      686 lines   criticals, classify, shock location, distributed solve

**Application** (`rocketforge/application/analysis/`)

    nozzle_service.py     520 lines   input modes, rows, bands, sweeps, table
    nozzle_controller.py  660 lines   the QML-facing adapter

**Interface** (`ui/pages/nozzle/`)

    NozzleCalculator.qml    390 lines
    NozzleRegimes.qml       250 lines
    NozzleDistribution.qml  290 lines
    NozzleCharts.qml        200 lines

**Reference data**

    rocketforge/data/reference/nozzle_anderson6_constructed.json

**Documentation**

    docs/engineering/ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md

**Tests**

    test_nozzle_geometry.py         27
    test_nozzle_thresholds.py      134
    test_nozzle_regimes.py          71
    test_nozzle_internal_shock.py   56
    test_nozzle_distribution.py     96
    test_nozzle_properties.py      124
    test_nozzle_reference_cases.py  24
    test_nozzle_reuse.py            30
    test_phase_4f_controllers.py    42

---

## 2. Files modified

    rocketforge/core/errors.py                  + GeometryError, InconsistentStateError
    rocketforge/core/tolerances.py              + pressure_tol; the set is now complete
    rocketforge/physics/compressible/types.py   + NozzleRegime, FlowState,
                                                  StagnationState, NozzleOperating,
                                                  CriticalPressureRatios, ShockLocation,
                                                  NozzleRegimeResult, NozzleSolution
    rocketforge/application/analysis/
        reference_validation.py                 + nozzle_validation()
    main.py                                     Nozzle registered; nine singletons
    ui/data/Navigation.qml                      nozzlelab marked computed
    ui/pages/NozzleLabPage.qml                  rebuilt: four sections, real physics
    tests/core/test_tolerances.py               field-set gate: pressure_tol arrives

No previous physics module was edited. Engine Design was not opened, and no
fundamental nozzle result is wired into it — that is a later phase.

---

## 3. The model, stated exactly

Steady · quasi-one-dimensional · inviscid · adiabatic · calorically perfect ·
isentropic everywhere except across an infinitely thin normal shock · area
varying slowly enough that the flow is locally one-dimensional.

Absent by design, and named on the page so nobody has to guess: thrust, Cf,
c\*, Isp, nozzle efficiency, discharge coefficient, boundary layers, viscous
losses, flow separation, shock–boundary-layer interaction, the external plume,
variable γ and any chemistry.

**Separation specifically.** The module classifies `OVEREXPANDED` from
p_e < p_b and does nothing else with it. When p_e/p_b < 0.4 it emits
`MODEL_LIMIT_SEPARATION`, whose message says the threshold is a rule of thumb
for flagging and that quasi-1D theory contains no separation criterion. A test
asserts the words "does not predict" survive in that message.

---

## 4. PHASE_3_SPEC_CONFLICT — §10.6's example versus §12.4's pseudocode

Section 10.6 gives six numbers for γ = 1.4, Ae/A\* = 2, shock at A_s/A\* = 1.5.
Section 12.4 gives the pseudocode for the same calculation. **They disagree on
the last two**, and §10.6's own prose sides with the pseudocode:

> "A₂\* is larger, A_e/A₂\* is smaller, M_e is larger and p_e is lower."

| Quantity | §10.6 example | Independent oracle | Verdict |
| --- | --- | --- | --- |
| M_s1 | 1.8541235267 | 1.8541235267 | agrees |
| M_s2 | 0.6048430465 | 0.6048430465 | agrees |
| p₀₂/p₀₁ | 0.7883594291 | 0.7883594291 | agrees |
| A₂\*/A₁\* | 1.2684569539 | 1.2684569539 | agrees |
| **M_e** | **0.2358088692** | **0.4041969520** | example wrong |
| **p_b/p₀** | **0.7584257377** | **0.7044519779** | example wrong |

The decisive test is mass conservation, which is not a matter of convention:

| Path | A/A\* used at the exit | ṁ_exit / ṁ_throat |
| --- | --- | --- |
| §12.4 pseudocode (divide by A₂\*/A₁\*) | 1.5767188582 | **1.000000000000** |
| §10.6 example (multiply) | 2.5369139078 | 0.621510589416 |

The example's numbers lose 38% of the mass flow across the exit plane, so they
cannot describe a steady nozzle. The oracle is a standalone stdlib script — a
plain bisection on the textbook relations, no RocketForge module involved — and
it reproduces the four numbers the example got right, which is what makes the
disagreement on the other two meaningful rather than a difference of method.

**Nothing was tuned.** The example was wrong; the relations were not touched.
The implementation follows §12.4, the corrected values are pinned as tests, and
a second test asserts the *old* values are not reproduced, so this cannot drift
back silently.

One smaller documentation ambiguity, resolved rather than raised as a conflict:
`05` says that as Ae/A\* → 1 "all three criticals → 1". They converge on one
another, at the sonic pressure ratio p\*/p₀ = 0.5283 for γ = 1.4, never on
unity. The test asserts the physical statement and explains the reading.

---

## 5. Geometry

`AreaDistribution(x, area)` — the contour is *supplied*, never generated.
Validation is split deliberately in two:

* the **constructor** accepts any physically meaningful duct, monotone ones
  included, because a converging nozzle is a real device;
* `require_converging_diverging()` adds what the *C-D solver* needs: an
  interior throat, exactly one minimum, monotone on each side, and Ae > At.
  Two throats are refused rather than one of them chosen — a quasi-1D solver
  with two candidate sonic points has no principled way to pick.

Interpolation is Fritsch–Carlson monotone cubic, written out in
`geometry.py` rather than imported: a natural spline overshoots near a throat
and can manufacture a second, spurious minimum between two supplied stations,
which would silently break the classifier. A test drives 2 001 query points
through a 21-station profile and asserts no new minimum appears.

`conical()` exists only so an area-ratio study has something to place a shock
on. It is a straight-walled cone and the page labels it "schematic, not a
designed contour"; a bell contour is `engineering/nozzle/contour.py`, which
this phase does not write. Its wall angles are in **radians**, like every angle
below the application layer — the architecture test caught the `_deg` names in
the first draft and the parameters were renamed rather than the test weakened.

---

## 6. Public API

```python
critical_pressure_ratios(area_ratio_exit, gas, tolerances) -> Solution[CriticalPressureRatios]
classify(area_ratio_exit, pressure_ratio_back, gas, tolerances) -> Solution[NozzleRegimeResult]
shock_area_ratio(area_ratio_exit, pressure_ratio_back, gas, tolerances) -> Solution[ShockLocation]
solve(geometry, operating, gas, tolerances) -> Solution[NozzleSolution]
```

The first three need only Ae/A\*, pb/p₀ and γ — no contour at all. Only
`solve` needs a profile, and only `solve` returns a physical shock position: an
area ratio fixes the shock's *area* and says nothing about where that area
occurs. `ShockLocation.x` is `None` from the dimensionless path, which is the
type saying so.

---

## 7. The three critical pressure ratios

| | Definition | Reuse path |
| --- | --- | --- |
| first | throat exactly sonic, subsonic diverging section | `pressure_ratio(mach_from_area_ratio(AR, SUBSONIC))` |
| second | normal shock standing in the exit plane | `third x normal_shock.pressure_ratio(Me_sup)` |
| third | ideal expansion, p_e = p_b | `pressure_ratio(mach_from_area_ratio(AR, SUPERSONIC))` |

Recomputed now, γ = 1.4, Ae/A\* = 2:

    Me subsonic     0.3059038342   spec 0.3059038342
    Me supersonic   2.1971981216   spec 2.1971981217
    first           0.9371625024   spec 0.9371625024
    second          0.5134007280   spec 0.5134007280
    third           0.0939326457   spec 0.0939326457

Ordering `third < second < first < 1` is asserted at four γ and six area
ratios, and a violation returns `NO_SOLUTION` with a `CRITICAL_ORDER`
diagnostic rather than an assertion that could be switched off — a violation
would mean one of the three had been computed on the wrong branch, and every
regime built on them would be wrong in a way no downstream test would localise.

`05` §10's identity holds to machine precision: second = third × p₂/p₁ at
M = 2.1971981217, giving 0.0939326457 × 5.4656261834 = 0.5134007280.

---

## 8. Regime classification

Threshold-first, always. The classifier never runs a shock solve to find out
which regime it is in — it decides from the criticals, and only then invokes
the shock locator if the answer was `INTERNAL_NORMAL_SHOCK`.

    r >= 1            InputError -- no flow, or flow backwards through the nozzle
    first < r < 1     UNCHOKED_SUBSONIC
    |r - first|<=tol  CHOKED_SUBSONIC_EXIT   (choking onset)
    second < r        INTERNAL_NORMAL_SHOCK
    |r - second|      SHOCK_AT_EXIT
    third < r         OVEREXPANDED
    |r - third|       IDEALLY_EXPANDED
    r < third         UNDEREXPANDED

`pressure_tol = 1e-9` is applied **relatively**, as `04` §5 specifies — each
threshold carries its own window, so the tolerance is not generous at the first
critical and tight at the third. The requested back pressure is carried through
untouched: a value near a boundary is classified by the documented tolerance
and never clamped onto it, and a test asserts the stored value is the value
supplied.

Classification is deterministic and independent of sampling: the same float64
inputs give the same regime, and a 200-point sweep gives identical results on
two consecutive runs.

---

## 9. The unchoked solution

`03` §10.10, including the step implementations usually get wrong:

1. `Me = mach_from_pressure_ratio(pb/p0)` — a subsonic exit communicates with
   the downstream reservoir, so p_e = p_b;
2. `A* = Ae / area_ratio(Me)` — a **virtual** sonic area, smaller than the
   throat, never physically reached;
3. every station subsonic on `A(x)/A*`;
4. `choked = False`, mass flow from the *actual* throat Mach number, diagnostic
   `NOT_CHOKED`.

Continuing to use the throat as A\* here is the classic error, and it produces
a throat Mach number of exactly 1 in a regime where the throat is not sonic. A
test asserts the virtual A\* is below the throat area and the throat Mach is
below 1.

Limits, both tested: as pb → p₀ the mass flow falls a decade per decade of
approach (7.4 → 0.03 kg/s at pb/p₀ = 0.999999) and the throat Mach → 0; as
pb → first critical the throat Mach → 1 and the mass flow → the choked value.

---

## 10. The internal shock

Residual, in area rather than in x:

    F(As/A1*) = pe(As)/p01 - pb/p01

with the chain naming the module that owns each step: supersonic area–Mach to
the shock, `normal_shock.solve`, a **new sonic area** A₂\* = A₁\*·p₀₁/p₀₂
downstream, subsonic area–Mach from there to the exit, and the isentropic
pressure ratio on the reduced stagnation pressure.

F is strictly decreasing, so the root is unique, and the bracket needs no
search because its ends evaluate to the two criticals. That is asserted where
it lives rather than inferred: at the throat end the predicted exit pressure is
the first critical, at the exit end it is the second, and the residual
therefore changes sign for every back pressure strictly between them.

    solver        the frozen Phase 4A Brent, xtol = area_abs_tol, rtol = area_rel_tol
    iterations    6 for a mid-interval case
    residual      8.9e-16
    boundaries    answered exactly, never by a degenerate root solve

Both endpoints are special-cased on purpose. At the second critical the shock
*is* the exit and the state is `normal_shock.solve(Me_sup)` directly, returned
with `convergence = None` because an exact boundary is not an iteration. At the
first critical there is no shock to place — the supersonic pocket has zero
extent — and the module says `NO_INTERNAL_SHOCK` rather than putting a
zero-strength shock at the throat and calling it a result.

Behaviour across the interval, tested at four γ:

    pb falls  ->  As/At rises, xs moves downstream, M1 rises, p02/p01 falls
    pb -> first critical:   As/At -> 1.000067, M1 -> 1.009, p02/p01 -> 0.999999
    pb -> second critical:  As/At -> 1.999997, M1 -> Me_sup to 1e-6

---

## 11. The distributed solution

The output grid is the caller's own x grid — no resampling, no smoothing —
plus one duplicated station when a shock exists: `x[i] == x[i+1] == x_s`, the
pre-shock state first, `shock_index = i`.

Branch assignment is explicit at every station and never guessed:

    unchoked            subsonic throughout, on the virtual A*
    choked, shock-free  subsonic | M = 1 exactly at the throat | supersonic
    internal shock      subsonic | sonic | supersonic to the shock |
                        subsonic on A/A2* to the exit

The throat is set to exactly 1.0 when choked rather than inverted from an area
ratio of 1 ± round-off, which is where a naive implementation produces `nan`.

Critical stations are guaranteed present regardless of the sampling grid:
throat, exit, and both shock stations. A test asserts every one of them exists
at 11, 51, 201 and 1001 stations, and that the regime does not depend on the
count.

**Conservation, swept over four γ, four area ratios and every regime:**

    mass          rho A V equals the mass flow at every station, rtol 1e-7
    energy        T + V^2/(2 cp) equals T0 everywhere, rtol 1e-10, shock included
    p0            exactly one level without a shock, exactly two with one,
                  and never rising

---

## 12. Reuse — audited three ways

The module's whole claim is that it composes rather than restates, so the claim
is checked by reading the source, by spying at runtime, and by comparing
results against the modules they came from.

    static     every call the nozzle must make is present in its AST:
               isentropic.mach_from_area_ratio / pressure_ratio /
               temperature_ratio / area_ratio / mach_from_pressure_ratio,
               normal_shock.solve / pressure_ratio,
               mass_flow.choked_mass_flow / mass_flow, and brent
    runtime    monkeypatched spies confirm normal_shock.solve, the two
               area-Mach branches and the mass-flow module are really called
    results    the shock-at-exit state is bit-identical to normal_shock.solve;
               every distributed p and T is the isentropic relation to 1e-12;
               density is p/(RT) to 1e-15; a is the gas model's own

And what must **not** appear, scanned over code with docstrings stripped —
necessary because the module's docstring names every forbidden thing in order
to say it is out of scope:

    no gamma expression        no `**` anywhere
    no sqrt                    no newton/secant/bisect/scipy
    exactly one brent( call    no fanno, no rayleigh
    no thrust / Cf / c* / Isp  no scipy, pandas or PySide6 imports

---

## 13. Reference validation

The supplied Anderson volume has **no nozzle appendix** and no printed
back-pressure regime table. None was invented.

What replaces it is stronger than a lookup: seven complete nozzle cases are
*constructed from printed rows*, and RocketForge must then rediscover published
stations it was never given. The internal-shock case is the one worth stating
in full — given only an area ratio and a back pressure assembled from four
printed values, the solver must land on four other printed values:

    geometry   Ae/At = 1.590 / 0.7209      (Appendix A M=0.40 A/A*, Appendix B M1=2.00 p02/p01)
    back       pb/p0 = 0.7209 / 1.117      (Appendix B p02/p01, Appendix A M=0.40 p0/p)

    recovered  As/At  1.688068   published 1.687    (Appendix A, M = 2.00)
               M1     2.000404   published 2.000
               M2     0.577281   published 0.5774   (Appendix B, M1 = 2.00)
               p2/p1  4.501885   published 4.500
               Me     0.400190   published 0.400    (Appendix A, M = 0.40)

Tolerances are **derived, not chosen**: each published value stands for a
rounding interval of half a unit in its last printed figure, and each case was
re-solved at every corner of that interval box with an independent
implementation of the relations. The tolerance is the widest departure that
rounding alone can produce, plus half a unit in the expected value's own last
figure.

**The limitation is stated rather than blurred.** These are end-to-end cases
assembled from published *station* values, not transcriptions of a published
worked nozzle example: the composition is RocketForge's, the numbers are the
book's. `170` asks for exactly that distinction and the dataset carries it.

**The measure-zero regimes are handled honestly.** A back pressure built from
four-figure values cannot land on an exact threshold — 1/1.117 misses the first
critical by 3.4e-4, because 1.117 is itself a rounding of 1.116552. Widening
`pressure_tol` to absorb that would collapse genuinely different operating
points into boundary regimes, so it was not widened. Those three cases compare
the published number against the *computed threshold*, and the regime label is
checked by setting the back pressure to that threshold — which is exactly what
the interface's preset buttons do.

    7 cases, all seven regimes covered, 19 published values, 19 PASS
    1 NOTE: the Phase 3 erratum, reported on the page rather than hidden

---

## 14. The interface

Four sections, because this page has more to say than three would hold.

**Calculator** — gas, reservoir, geometry and back pressure on the rail; the
regime as the headline; solution rows in four groups; and a shock card that
exists only while a shock does. Two input modes per quantity (p_b or p_b/p₀;
A_e or A_e/A_t), converted once by the controller so the physics never sees a
mode flag, and switching mode provably does not move the operating point.

**Regimes** — the signature view. Band edges are the computed criticals, so the
map is a picture of this nozzle; change the area ratio and the bands move.
Ideal expansion is a zero-width band and is drawn as one rather than widened
into something clickable, which is why the three preset buttons exist — each
sets the back pressure to a computed threshold, and each lands exactly on its
boundary regime. Below it, As/At against pb/p₀, solved with the same shock
solver the calculator uses.

**Distribution** — the station table, with PRE SHOCK and POST SHOCK as two rows
sharing an x, a station inspector, and jump buttons for the marked stations.
The throat marker reads "THROAT · SONIC" only when the throat actually is
sonic.

**Charts** — Mach, p, T, ρ, V and p₀ along x, plus the contour. When a shock
exists the backend returns two series cut at the shock, so the renderer draws a
genuine break rather than a line sloping across it. The stagnation-pressure
chart is the one worth arriving at: flat, one step, flat.

**No physics in QML.** No area–Mach relation, no threshold, no root logic, not
even a pressure ratio — the audit greps for it and the sweep confirms zero
warnings.

**State discipline**, tested rather than asserted: leaving the shock regime
clears the shock rows, the shock marker, the pre/post row indices and the table
markers together; going from a shock to an unchoked nozzle also drops the
choked mass flow; and crossing the ideal point changes only the label, with the
internal arrays asserted identical either side.

---

## 15. Performance

    one threshold set                                  0.005 ms
    one classification                                 0.014 ms
    100 000 classifications                            766 ms
    1 000 back pressures across every regime           1.11 s
    one shock location                                 2.4 ms   (6 iterations)
    distribution, 100 / 500 / 1000 / 5000 stations     11 / 48 / 93 / 772 ms

The first draft classified in 0.216 ms and took 38.5 s for 100 000 — not what
`147` means by cheap. The cause was that every point of a sweep recomputed the
same two bracketed inversions for the same nozzle, so the criticals are now
memoised on `(area ratio, gas, tolerances)`. That is a pure function of its
arguments, so the cache changes no answer, and a test proves a different area
ratio or a different γ cannot receive another nozzle's thresholds.

The remaining cost is honest and irreducible at this design: a sweep that
crosses the shock interval pays one Brent solve per point in it, each with two
nested area–Mach inversions. The UI's shock curve uses 80 points, about 200 ms
on a tab switch. No threading was added; `150` asks for measurement first, and
the measurement says the default resolutions are comfortable.

---

## 16. Architecture, isolation and audit

    architecture test     PASS, 41 tests, unchanged and not weakened
    Qt isolation          PASS — thresholds, classification, the shock solve and
                          all seven regimes' distributed solutions run with
                          PySide6 blocked from the process
    scipy / pandas / numba in production      0
    PySide6 under physics / core              0
    QML gas dynamics                          0
    duplicated relation families              0
    Fanno or Rayleigh inside the nozzle       0
    thrust / Cf / c* / Isp anywhere in code   0

---

## 17. Regression

    4494 passed, 1 skipped, run twice with identical results
    0 QML warnings across every page in both themes, plus Engine Design

`15_previous_modules_regression.png` shows Isentropic at M = 2 with all four
Appendix A checks still PASS. The Fanno, Rayleigh, Prandtl–Meyer, Oblique
Shock, Normal Shock and Mass Flow suites are unchanged and green; no shared
component was modified this phase, so no earlier page could have moved.

---

## 18. Executable

    build              clean rebuild, exit 0
    size               191.9 MB across 2 072 files
    launch             starts and stays alive
    numpy              present
    scipy / pandas     absent
    tests              not bundled
    textbook PDF       not bundled
    nozzle + geometry + service + controller   present in the build graph
    all four nozzle QML files                  present
    nozzle reference JSON                      present and loading

The frozen path was exercised by pointing `sys._MEIPASS` at the real bundle and
running the packaged modules from there: the validation panel returned PASS
from the shipped data, and the packaged backend solved all seven regimes with
the mass flow constant at 7.37872 kg/s across every choked one.

### EXE interaction verification

**Automated, source runtime:** every regime, the three presets, the regime map,
the distribution table with all four marked stations, all six charts, both
themes. 15 screenshots, each asserting its own regime before the shutter.

**Automated, packaged:** backend and resources only — all seven regimes solved
from inside the bundle, reference data loaded through `sys._MEIPASS`, launch
and stay-alive, plus a PrintWindow capture of the running window.

**Not automated:** navigating the packaged application's interface. Driving a
packaged Qt process needs synthetic desktop input, and the harness refuses to
send it. `16_packaged_exe.png` is therefore the exe's landing page — the
sidebar shows Nozzle Lab, but the nozzle views in this set come from the source
runtime.

**Manual:** none performed. Stated plainly rather than implied.

---

## 19. Screenshots

`acceptance/phase_4f/`

    01_nozzle_unchoked_dark.png              throat M = 0.361, mdot below critical
    02_nozzle_choking_onset_dark.png         first-critical preset
    03_nozzle_internal_shock_dark.png        As/At 1.51009, M1 1.86271, M2 0.603072
    04_nozzle_shock_exit_dark.png            second-critical preset
    05_nozzle_overexpanded_dark.png          pe < pb, no shock card at all
    06_nozzle_ideal_dark.png                 third-critical preset, pe = pb
    07_nozzle_underexpanded_dark.png         pe > pb
    08_nozzle_regime_map_dark.png            bands from the computed criticals
    09_nozzle_distribution_shock_dark.png    THROAT · SONIC, PRE/POST SHOCK, EXIT
    10_nozzle_mach_chart_dark.png            supersonic, jump, subsonic
    11_nozzle_pressure_chart_dark.png        the pressure jump, unsmoothed
    12_nozzle_total_pressure_chart_dark.png  flat, one step, flat
    12b_nozzle_total_pressure_no_shock_dark.png   the marker gone with the shock
    13_nozzle_calculator_light.png
    14_nozzle_distribution_light.png
    15_previous_modules_regression.png
    16_packaged_exe.png

Provenance: 01–15 are `QQuickWindow.grabWindow` renders of the live scene graph
from the source runtime, driven through the controller's own properties and
slots. They are offscreen renders, so nothing on the desktop can disturb them,
and no synthetic input was used. 16 is the packaged executable via PrintWindow.

---

## 20. Runtime dependencies

None. PySide6 and numpy, as before. The monotone cubic interpolation was
written rather than imported, which is why SciPy is still absent.

---

## 21. Errata and source anomalies

**New this phase:** the Phase 3 §10.6 internal-shock example, section 4 above
and `ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md`. Two published numbers are wrong
and the specification's own pseudocode gives the right ones.

**Standing, unchanged:** the Anderson Appendix A M = 16 misprint
(T₀/T printed 52.29, exactly 52.20) and the M = 7.8 rounding edge, both
recorded in Phase 4C/4D and both still reported as REVIEW with the published
values preserved.

---

## 22. Deliberately not implemented

thrust · thrust coefficient · characteristic velocity · specific impulse ·
nozzle efficiency · discharge coefficient · divergence loss · flow separation ·
shock–boundary-layer interaction · the external plume, its shocks, fans and
diamonds · contour optimisation · Rao bells · method of characteristics ·
boundary layers · thermal or structural analysis · thermochemistry, CEA,
Cantera, CoolProp · variable γ.

Stopped after the quasi-1D nozzle, as instructed.
