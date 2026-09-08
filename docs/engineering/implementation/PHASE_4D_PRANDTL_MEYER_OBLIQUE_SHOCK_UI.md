# Phase 4D — Prandtl–Meyer Expansion and Oblique Shock

# Verdict

**READY FOR PHASE 4E**

Physics → application → interface → packaged executable, for two modules.
Everything below was implemented against Phase 3, verified, and rebuilt.

    2756 passed, 1 skipped        (1589 at the start of the phase)
    0 QML warnings across five analysis pages, fifteen sections, and Engine Design
    336 Appendix C values compared: 336 PASS, 0 REVIEW

---

## Baseline

    1589 passed, 1 skipped
    41 architecture tests green
    rocketforge imports and runs with PySide6 blocked from the process
    Isentropic, Mass Flow and Normal Shock open with 0 QML warnings

---

## 1. Files created

**Physics** (`rocketforge/physics/compressible/`)

    prandtl_meyer.py       510 lines   nu, nu_max, the inverse, expand/compress
    oblique_shock.py       686 lines   theta-beta-M, the closed forms, both branches

**Application** (`rocketforge/application/analysis/`)

    prandtl_meyer_service.py       Qt-free: solve, expansion turn, tables
    oblique_shock_service.py       Qt-free: solve, limits, study, diagram data
    prandtl_meyer_controller.py    the Qt surface for the Prandtl–Meyer page
    oblique_shock_controller.py    the Qt surface for the Oblique Shock page

**Interface** (`ui/`)

    pages/prandtlmeyer/{Calculator,Table,Charts}.qml
    pages/obliqueshock/{Calculator,Study,Charts,Diagram}.qml

**Reference data**

    rocketforge/data/reference/anderson6_appendix_c_prandtl_meyer.json

**Tests**

    tests/physics/compressible/test_prandtl_meyer.py                62
    tests/physics/compressible/test_prandtl_meyer_inverse.py       160
    tests/physics/compressible/test_oblique_shock.py               406
    tests/physics/compressible/test_oblique_shock_branches.py      352
    tests/physics/compressible/test_phase_4d_reuse.py               41
    tests/physics/compressible/test_phase_4d_reference_cases.py     33
    tests/application/test_phase_4d_services.py                     68
    tests/application/test_phase_4d_controllers.py                  45
    -------------------------------------------------------------------
    added                                                        1 167

## 2. Files modified

    rocketforge/core/errors.py                 + SubsonicExpansionError
    rocketforge/core/tolerances.py             + angle_abs_tol, angle_tol,
                                                 angle_margin, nu_tol, near_theta_max
    rocketforge/physics/compressible/equations.py   + 3 relation records
    rocketforge/physics/compressible/types.py       + ShockBranch and four records
    rocketforge/physics/compressible/__init__.py    exports
    rocketforge/application/analysis/reference_comparison.py  + Appendix C, one fix
    rocketforge/data/reference/anderson6_appendix_a_isentropic.json  metadata only
    ui/components/RFLineChart.qml              generalised to multiple series
    ui/pages/{PrandtlMeyer,ObliqueShock}Page.qml    were placeholders
    ui/data/Navigation.qml                     `computed: true` on two entries
    main.py                                    two more singletons
    tests/core/test_tolerances.py              the deliberate field-set gate

---

## 3. Prandtl–Meyer physics

**Public API** — angles in radians, as everywhere below the application layer:

    nu(mach, gas)                     -> float | ndarray      rad
    nu_max(gas)                       -> float                rad
    mach_angle(mach)                  re-exported from isentropic, not redefined
    mach_from_nu(nu, gas, tolerances) -> Solution[float]
    mach_from_nu_array(nu, gas)       -> ndarray               NaN where unsolvable
    expand(M1, turn, gas)             -> Solution[PrandtlMeyerResult]
    compress(M1, turn, gas)           -> Solution[PrandtlMeyerResult]

**ν∞** = (π/2)(√((γ+1)/(γ−1)) − 1) — 130.4540768505° for air, and reproduced to
every digit the specification prints at γ = 1.2, 1.3, 1.4 and 1.66. It is a hard
ceiling on the inverse: a turn asking for more of it returns `NO_SOLUTION` with
`NU_EXCEEDS_MAX`, not a capped Mach number.

**Inverse strategy** — Brent from the exact bracket `[1, M_seed]`, where the
seed is the closed form from the large-M asymptote, `M = 2/((γ−1)(ν∞ − ν))`. A
test asserts the seed always overestimates, so the bracket is valid before Brent
starts; the expansion loop that follows is a safety net that never runs. `ν = 0`
returns M = 1 exactly with no iteration at all.

Newton is not used, and a test enforces that: `dν/dM` is zero at M = 1, which is
exactly where a user starts, so the first Newton step from the sonic point is
undefined.

**Near-sonic policy.** ν ≈ [4√2/(3(γ+1))]·(M−1)^{3/2} — asserted directly rather
than quoted — so a relative error ε in ν becomes ε^{2/3} in (M−1). That is better
conditioned than the area-Mach inverse but still a loss, and a `NEAR_SONIC`
advisory says so rather than implying six good figures from a tiny angle.

---

## 4. Expansion turn

    nu1 = nu(M1);  nu2 = nu1 + turn;  M2 = mach_from_nu(nu2)

**Reuse.** The expansion is isentropic, so p₀ and T₀ are unchanged and every
static ratio is the quotient of two isentropic values:

    p2/p1 = pressure_ratio(M2) / pressure_ratio(M1)      (and likewise T, rho)

`prandtl_meyer.py` contains **no** static-ratio formula. The reuse audit asserts
the quotients to `rtol = 1e-15` — machine precision, not 1e-10, because a
carefully re-derived duplicate would agree to about 1e-12 and must fail. A
runtime spy additionally proves `isentropic.pressure_ratio` is called at both
stations, and a static AST check proves no γ-dependent exponent appears in the
file at all.

`compress()` is the same machinery with `nu2 = nu1 − turn`, and it carries a
standing `ISENTROPIC_COMPRESSION` advisory: a real concave turn coalesces into a
shock, and the isentropic result is a bound rather than a description of a wedge.

---

## 5. Anderson Appendix C

    gamma        1.4
    units        degrees
    columns      M, nu, mu
    rows         168
    Mach range   1.00 to 50.00
    pages        1089–1091
    extraction   PDF text layer, whitespace-tolerant tokenising, screened
                 against equation-independent constraints, five rows read
                 visually off the rendered pages

**γ was established, not assumed.** Evaluating ν at each of the 167 supersonic
rows gives a maximum deviation of **0.049°** at γ = 1.4 — within the printed
precision at high Mach — against 26.9° at γ = 1.3, 37.5° at γ = 1.66 and 72.4° at
γ = 1.2. The largest printed ν, 124.7 at M = 50, also sits below ν∞ = 130.454 for
γ = 1.4 and *above* ν∞ = 90.68 for γ = 1.66, which alone excludes the latter.

**The units were established too.** The μ column matches `asin(1/M)` in degrees
at printed precision on all 168 rows — a check involving no gas dynamics and no
choice of γ, which makes it an independent witness for two of the three columns.

**Comparison result: 336 values, 336 PASS, 0 REVIEW.** No extraction correction
was needed and no rounding tie was found. That is worth stating explicitly,
because Appendices A and B each carry one.

**The detector was tested.** Perturbing one ν in a *copy* is caught; swapping ν
and μ on one row is caught on both quantities; a perturbation of a third of the
last printed digit is correctly **not** flagged. The real dataset is
byte-identical before and after.

---

## 6. An erratum in Appendix A, found in passing

Comparing Appendix A over its **whole** range — which nothing did before this
phase, the Isentropic page's default table stopping at M = 5 — surfaced two rows.
Both are in the source, not in RocketForge, and both are now recorded in the
dataset under `source_anomalies` with their evidence.

**M = 16, T₀/T: printed 52.29, exact 52.20 — a typographical error.**
T₀/T = 1 + (γ−1)/2·M² is exactly linear in M², so at M = 16 and γ = 1.4 it is
exactly 52.2 with no rounding involved at all: 1 + 0.2 × 256. All 216 other rows
satisfy that identity at printed precision; this one is out by **18 half-units**,
and its neighbours at M = 15 (46.00) and M = 17 (58.80) are exact. The digits
appear transposed, 5220 printed as 5229. Confirmed against the rendered page.

**M = 7.8, p₀/p: printed 8285, exact 8285.512 — a rounding edge.** Correctly
rounded to four significant figures the value is 8286; the difference is 1.02
half-units, the same class as the two ties in Appendix B.

Published values preserved, equations untouched, tolerance untouched. The
comparison reports REVIEW for both, which is the correct outcome, and the counts
are now pinned per appendix so a *new* disagreement fails rather than joining an
approved total.

One reporting defect was fixed while doing this: a printed **zero** — ν at Mach 1
is the first legitimate one in any dataset here — produced an infinite "maximum
relative difference" in the summary. A zero difference from a printed zero is
exact agreement, and now reports as such.

---

## 7. Oblique shock physics

**Public API** — radians throughout:

    theta_from_beta(beta, mach1, gas)              -> float | ndarray   closed form
    theta_max(mach1, gas)                          -> Solution[ThetaMaxResult]
    beta_sonic(mach1, gas)                         -> Solution[float]
    beta_from_theta(mach1, theta, gas, branch)     -> Solution[float]
    solve(mach1, theta, gas, branch=WEAK)          -> Solution[ObliqueShockResult]
    solve_both(mach1, theta, gas)                  -> Solution[ObliqueShockPair]
    solve_from_beta(mach1, beta, gas)              -> Solution[ObliqueShockResult]
    theta_beta_curve(mach1, gas, n=400)            -> Solution[ThetaBetaCurve]

**Branches.** `ShockBranch.WEAK | STRONG | BOTH`, `BOTH` a request and never a
result. `WEAK` is the default because it is what physically occurs, and the
result says which branch it is; `STRONG` carries `STRONG_BRANCH_UNSTABLE`.

**θ_max is closed form** — the analytic stationary point of §6.3, one square root
rather than a maximisation. A golden-section search over 400 iterations exists
**only in the tests**, as the oracle, and agrees at every Mach number and γ. All
six published θ_max / β-at-θ_max values reproduce to 8 digits, as do the three
γ-dependent values at M₁ = 2. β_sonic is likewise closed form, and putting it
through the whole solution chain gives M₂ = 1.00000000.

**Detached behaviour.** θ > θ_max + `angle_tol` returns `Status.NO_SOLUTION` with
a `DETACHED_SHOCK` diagnostic naming the requested deflection and the limit. It
is never a `BracketError`, never `NOT_CONVERGED`, never a NaN, and above all
never a fabricated attached solution or the θ_max solution silently substituted.
At exactly θ_max the two roots have merged and a single β is returned with a
`BRANCH_ASSUMED` note; approaching it raises `NEAR_THETA_MAX`.

---

## 8. Normal Shock reuse — how it is enforced

    Mn1 = M1 sin(beta)
       -> normal_shock.solve(Mn1, gas)          <- every property ratio
    M2  = Mn2 / sin(beta - theta)

`oblique_shock.py` contains **no** pressure, density, temperature or
stagnation-pressure formula. Four independent tests enforce that, and each would
fail for a different kind of mistake:

1. **Numerical, at machine precision.** For M₁ ∈ {1.5, 2, 3, 5} and 60 wave
   angles spanning [μ, π/2] at four γ values, every oblique ratio equals the
   normal-shock relation at `M₁ sin β` to `rtol = 1e-15`.
2. **Runtime spy.** `normal_shock.solve` is patched; the oblique solver must
   call it, and with exactly `M₁ sin β`. Coupled to one public name and nothing
   finer, so an internal refactor does not make it brittle.
3. **Structural AST check.** Every ratio in the result builder is asserted to be
   assigned directly from `shock.<field>` — if one were ever computed instead,
   the right-hand side would stop starting with `shock.` and the test fails.
4. **Static exponent check.** No `**` with a γ-dependent exponent appears
   anywhere in the file; a re-derived shock or isentropic formula needs one.

**The physical consequence, checked end to end:** at β = 90° the oblique result
is bit-identical to `normal_shock.solve(M₁)` — M₂, all three static ratios, the
stagnation-pressure ratio and the entropy rise — and the same M₁ = 2 case passes
the *published* Appendix B comparison. The Oblique page says this about itself,
and a controller test asserts the claim.

---

## 9. Oblique reference validation

The Anderson volume publishes no oblique-shock table, so nothing was invented.
Validation comes from three independent directions:

* **The worked cases in the project specification (§11.5)**, externally
  confirmed there: four solved cases at M₁ = 2, 3 and 5, checked on *both*
  branches against β, M₂ and p₂/p₁ — all to 8 printed digits. Plus the six
  θ_max / β / θ-at-M₂=1 / β_sonic / μ rows, and the three γ-dependent θ_max
  values at M₁ = 2.
* **The published Appendix B**, through the β = 90° limit described above. This
  is the strongest check available: it ties the oblique module to a printed
  table without an oblique table existing.
* **An independent maximisation** for θ_max, and the M₂ = 1 substitution for
  β_sonic, both computed by code that exists only in the tests.

---

## 10. The θ–β–M diagram

Generated by `oblique_shock_service.curve_data`, which calls
`oblique_shock.theta_beta_curve` — **the same service the calculator calls**. A
test samples the drawn weak branch and re-solves each point through the
calculator's own path, requiring agreement to 1e-9: the chart cannot become a
second answer. Clicking it is deliberately not a way to solve anything.

    weak branch      solid, from beta = mu up to beta at theta_max
    strong branch    dashed, from there to a right angle
    markers          theta_max, beta at theta_max, mu, and beta for sonic M2
    operating point  the solved (theta, beta), on whichever branch was solved;
                     two points when Both is selected
    detached         the operating point disappears and the requested theta is
                     drawn against the limit -- no fabricated beta

The wave-angle grid is cosine-clustered towards both ends, where the curve turns
sharply; a uniform grid facets the nose and wastes points on the straight middle.

Optional overlay curves at M = 1.5, 2, 3 and 5 are available and off by default.

---

## 11. Physical invariants

**Prandtl–Meyer.** ν(1) = 0 exactly; ν strictly increasing on a 20 001-point
grid; ν bounded by ν∞ and reaching it in the limit; μ = 90° at Mach 1 and
strictly decreasing; ν larger at lower γ; the 3/2-power near-sonic law.

**Expansion.** M₂ > M₁, p₂ < p₁, T₂ < T₁, ρ₂ < ρ₁, μ₂ < μ₁ for every positive
turn at four γ and four upstream Mach numbers; ν₂ − ν₁ = θ exactly; p₀ and T₀
recovered from the isentropic relations and shown unchanged to 1e-13; the ideal
gas law across the fan; the fan angle equal to μ₁ − μ₂ + θ; a turn past ν∞
refused; a negative turn refused rather than routed into a compression.

**Oblique.** θ = 0 at both ends of the wave-angle range; θ rising to exactly one
maximum, checked by a single sign change of the derivative on a 4 001-point grid;
Mn₁ > 1 and Mn₂ < 1; all three static ratios above 1; 0 < p₀₂/p₀₁ < 1; T₀₂/T₀₁
exactly 1; Δs > 0; M₂ = Mn₂/sin(β − θ); the branch ordering
μ < β_weak < β_θmax < β_strong < π/2 on nine interior deflections at five Mach
numbers and four γ; the strong branch always costing more stagnation pressure.

**The trap this module refuses to fall into:** "weak" is not reported as
"supersonic behind". β_sonic sits *below* β at θ_max, so a narrow band of weak
solutions is already subsonic — a thousandth of a degree wide at M₁ = 10. A test
locates that band by its own two boundaries and asserts the flag is computed
rather than inferred from the branch name.

---

## 12. Numerical behaviour

**PM inverse.** Round-trips at nine Mach numbers × four γ to `rel = 1e-9`; the
published inversions ν = 30° → M = 2.1339050332 and ν = 45° → M = 2.7644521940 to
5e-10. Convergence recorded: bracket, residual ≤ 1e-9, iterations 6–9 typical.

**β weak and β strong.** Each root is asserted to land inside *its own* bracket,
with the residual θ(β) − θ_requested checked below 1e-9 on both branches — not
merely that β looks about right.

**Near θ_max.** For ε ∈ {1e-2, 1e-4, 1e-6, 1e-8}, θ = θ_max(1 − ε) is required to
give β_weak ≤ β_θmax ≤ β_strong with the two never crossing, and the gap between
them is required to shrink monotonically. Detachment at θ_max(1 + ε) for four ε
values returns the physical classification and never a numerical failure.

---

## 13. State regressions tested

    switching from deflection to wave angle removes the branch control
    switching mode replaces the input rather than reinterpreting it
    a detached request clears the rows, the readout and the diagram marker
    ...and a legal deflection brings the solution back, changed
    switching Both -> Weak drops the strong solution's rows entirely
    changing M1 moves the limits, the hint and the curve together
    changing gamma recomputes the whole result
    a refused study range clears the table, its marker and its chart series
    regenerating the study drops the previous row selection
    an invalid PM input keeps the reading, marks it stale, publishes no rows
    the PM reference panel follows the current Mach and clears off-table
    the PM expansion turn follows the shared gamma
    a turn past nu_max clears the expansion readout

**One defect this found.** The θ–β–M diagram bound `curve` to a *slot*, so QML
had no dependency on it: changing M₁ updated the header, the limits and the
operating point, but the diagram kept drawing the previous Mach number's curve.
Caught by reading the first screenshot — the axis ran to 22.97° (M = 2's θ_max)
under a header saying M₁ = 3.00. Fixed by naming `mach1` and `gamma` in the
binding. A second, related inconsistency was fixed at the same time: the Charts
section drew the diagram at `mach1` and the secondary curve at the study's
`tableMach1`, so one page could show two different Mach numbers, neither
labelled. The M₁ field now drives both, and the secondary panel states its own.

---

## 14. Performance

    PM table, 250 / 1 000 / 5 000 rows        0.07 / 0.06 / 0.14 ms   (vectorised)
    PM forward sweep, 100 000 Mach samples    1.60 ms
    PM inverse sweep, 2 000 angles            131 ms
    one PM inverse                            0.064 ms
    theta-beta-M curve, 400 / 4 000 points    0.16 / 0.87 ms
    four overlay curves, 400 points each      0.60 ms
    one weak oblique solve                    0.304 ms
    oblique study at the default step         46 rows, 13.8 ms
    oblique study, 250 / 1 000 / 5 000 rows   81 / 314 / 1 578 ms

Reported honestly: the oblique study costs one Brent solve per row, so a
5 000-row sweep takes about 1.6 s. The default sweep is 46 rows and imperceptible;
5 000 rows means a 0.005° step across a 23° range, which is a deliberate stress
rather than a use. No threading was added — the guidance is explicit that these
are inexpensive relations and worker pools are not warranted, and the one genuine
waste found (θ_max being computed twice per `solve`) was removed instead.

---

## 15. Architecture, isolation and audit

    architecture test        PASS, 41 tests, unchanged
    Qt isolation             PASS -- PM forward, PM inverse, expansion turn,
                             theta-beta-M, weak, strong and detached all execute
                             with PySide6 blocked from the process
    scipy / pandas           absent from production source and from the bundle
    PySide6 under physics    absent (the two grep hits are prose stating the rule)
    _deg below application   absent (likewise prose stating the ban)
    gas dynamics in QML      absent -- the only Math.* in the new QML is min/max
                             for column widths and the log-axis pixel mapping

The degree/radian boundary is in the services and nowhere else. Tests assert both
halves: the readouts are the familiar degrees (ν = 26.3798°, μ = 30.0000°) *and*
they equal `math.degrees` of the radian physics to 1e-14.

---

## 16. Previous-phase regression

    4A     PASS -- Brent, tolerances, architecture all green
    4B     PASS -- isentropic and area-Mach unchanged
    4B-UI  PASS -- the Isentropic page's own Appendix A comparison still 0 review
                   over its default range; the A/A* "Both" transition still clean
    4C     PASS -- Mass Flow and Normal Shock controllers, tables and comparisons
                   unchanged; RFLineChart was generalised and both pages that use
                   it were re-validated

Engine Design opens with no warnings and is untouched.

---

## 17. Executable

    C:\Users\erayh\Documents\Python\rocket\dist\RocketForge\RocketForge.exe
    192 MB directory build, clean rebuild via the project's own build_exe.bat

The spec needed **no change**: it already bundles the whole of `ui/` and the
whole reference directory. Verified in the bundle: `numpy` present; `scipy`,
`pandas`, `tests/` and any PDF **absent**; all seven new QML files present; all
three appendices present.

The frozen reference path was tested against the real bundle by resolving
`sys._MEIPASS` to `dist/RocketForge/_internal`: all three datasets load from
there and their comparisons run — A 866/2, B 1006/2, C 336/0, the same numbers as
from source. That is the failure that would otherwise pass every test and show up
only in the shipped build.

### EXE interaction verification

**Automated.** Launch and stay-alive; bundle content; frozen-path resolution of
all three appendices with their full comparisons; window enumeration and a
`PrintWindow` capture of the running executable.

**Not automated.** Navigating the packaged process to a specific page needs
synthetic desktop input, which the harness refuses unless RocketForge owns the
foreground. Screenshot 16 therefore shows the executable's landing page and is
named for what it shows.

**Manual release checklist** — the states to confirm by hand in the shipped
build, each already verified in the source runtime and captured:

    Prandtl-Meyer
      1. open the page; M = 2, gamma = 1.4
      2. nu = 26.3798 deg, mu = 30.0000 deg, nu_max = 130.454 deg
      3. Reference check shows two PASS rows against Anderson
      4. switch to "Prandtl-Meyer angle", enter 49.7573467443 -> M = 3
      5. Table -> Compare with Appendix C -> 0 needing review
      6. Charts -> Overlay Appendix C -> dots sit on the line

    Oblique Shock
      1. M1 = 2, theta = 10 deg, Weak -> beta = 39.3139 deg, M2 = 1.64052
      2. Strong -> beta = 83.7001 deg, M2 = 0.603698
      3. Both -> two solutions, two markers on the diagram
      4. theta-beta-M -> weak solid, strong dashed, theta_max marked
      5. theta = 30 deg -> DETACHED SHOCK REQUIRED, no beta, no marker
      6. Given beta = 90 deg -> theta = 0 and the Normal Shock values

---

## 18. Screenshots

    C:\Users\erayh\Documents\Python\rocket\acceptance\phase_4d\

    01_pm_calculator_dark.png              source runtime
    02_pm_inverse_dark.png                 source runtime
    03_pm_expansion_dark.png               source runtime
    04_pm_table_reference_dark.png         source runtime
    05_pm_chart_dark.png                   source runtime
    06_oblique_calculator_weak_dark.png    source runtime
    07_oblique_calculator_both_dark.png    source runtime
    08_oblique_theta_beta_mach_dark.png    source runtime
    09_oblique_detached_dark.png           source runtime
    10_oblique_table_dark.png              source runtime
    11_pm_light.png                        source runtime
    12_oblique_light.png                   source runtime
    13_previous_modules_regression.png     source runtime (Isentropic)
    14_mass_flow_regression.png            source runtime
    15_normal_shock_regression.png         source runtime
    16_executable_landing_dark.png         packaged executable

**Provenance, stated plainly.** 01–15 were rendered from the source runtime with
`QQuickWindow.grabWindow`, which draws the live scene offscreen; the QML and the
backend are the same files the executable bundles. 16 is the packaged
executable, captured with `PrintWindow`, and shows its landing page for the
reason given in §17.

---

## 19. Runtime dependencies added

**None.** NumPy and PySide6, as before.

---

## 20. Errata

1. **Anderson Appendix A, M = 16, T₀/T** — printed 52.29 where the exact value is
   52.20. A typographical error in the source, established by an identity that
   needs no solver. Recorded, preserved, reported as REVIEW. §6.
2. **Anderson Appendix A, M = 7.8, p₀/p** — printed 8285 where round-to-nearest
   gives 8286. A rounding edge, 1.02 half-units. Recorded, preserved. §6.
3. **`reference_comparison`, relative difference against a printed zero** — a
   zero difference from a printed zero reported as infinite. Fixed; ν at Mach 1
   is the first legitimate printed zero in any dataset here.
4. **θ–β–M diagram, stale curve** — a QML binding to a slot created no
   dependency, so the diagram kept the previous Mach number's curve. Fixed. §13.
5. **Oblique Charts, two Mach numbers on one page** — the diagram used `mach1`
   and the secondary curve used the study's `tableMach1`. Fixed. §13.

Nothing in Phase 4A–4C physics needed changing.

---

## 21. Scope

Built: the Prandtl–Meyer function and its inverse, the Mach angle by reuse, ν∞,
the expansion turn, the isentropic compression turn, the θ–β–M relation, θ_max
and β_sonic in closed form, both wave-angle branches, detachment classification,
the downstream state by reuse of Normal Shock, both pages with Calculator, Table
or Study and Charts, the θ–β–M diagram, the Appendix C comparison, and the
rebuilt executable.

Not built, and deliberately not started: Fanno, Rayleigh, the C-D nozzle regime
solver, internal shock location, thrust, Cf, c*, Isp, thermochemistry, CEA,
Cantera, CoolProp, injector, chamber, cooling, pump, turbine, engine-cycle
solver. Conical (Taylor–Maccoll) shocks and the detached bow-shock shape remain
out of scope by specification, and the module says so where a user would ask.

Stopping here, as instructed.
