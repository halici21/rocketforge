# Phase 5B-0 — NASA CEA v3 vs Cantera: Provider Feasibility Spike

Empirical evidence for the thermochemistry provider decision Phase 5A left
open. Both providers were installed in isolated environments, driven through
their real APIs, measured, and frozen with PyInstaller.

**Type:** experimental / decision phase. No RocketForge production
implementation.
**Dates:** 2026-09-03 to 2026-09-04.

---

## 1. Verdict summary

| Question | Answer |
| --- | --- |
| Does the official NASA CEA Python route exist and work on this machine? | **Yes** — `cea` 3.3.4, CPython 3.13.2, Windows, structured API, no text parsing |
| Does Cantera work? | **Yes** — 3.2.0, same interpreter, structured API |
| Can either be frozen with PyInstaller? | **Both, with explicit flags**; both reproduce source values exactly |
| Which should be primary? | **NASA CEA** — see §17 |
| Is the Phase 5A Cantera-first recommendation confirmed? | **No — REVISED.** See §16 |

---

## 2. RocketForge regression

| Gate | Result |
| --- | --- |
| Opening | `5285 passed, 1 skipped`, pytest exit 0 |
| Closing | `5285 passed, 1 skipped`, pytest exit 0 |
| Frozen compressible manifest (22 files) | **byte-identical**, opening and closing |
| Manifest digest | `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` — unchanged |

Run directly as `.venv\Scripts\python.exe -m pytest -q`, no pipeline, exit code
recorded.

---

## 3. Environment

| Item | Value |
| --- | --- |
| OS | Windows 11 Pro 10.0.26200, x64 |
| RocketForge interpreter | `.venv\Scripts\python.exe` — CPython **3.13.2** (python.org), PySide6 6.10.2, numpy 2.5.2 |
| CEA test environment | `%TEMP%\rocketforge_phase5b0_cea` — CPython 3.13.2, `cea` 3.3.4, numpy 2.5.2 |
| Cantera test environment | `%TEMP%\rocketforge_phase5b0_cantera` — CPython 3.13.2, `cantera` 3.2.0, numpy 2.5.2, ruamel.yaml 0.19.1 |
| PyInstaller | 6.22.2 (in both isolated environments) |
| Build scratch | `%TEMP%\rf5b0_build_cea`, `%TEMP%\rf5b0_build_ct` |

Both isolated environments were created from the **same** base interpreter as
RocketForge's own `.venv`
(`C:\Users\erayh\AppData\Local\Programs\Python\Python313\python.exe`), so the
compatibility result is for the interpreter RocketForge actually uses. No
fallback to Python 3.12 was needed.

---

## 4. Package identity — verified, not assumed

The spike spec warned against assuming `package name = cea`. It was checked.

| Candidate | Reality |
| --- | --- |
| **`cea` 3.3.4** | **The official NASA package.** Summary "Chemical Equilibrium with Applications", `requires_python >=3.11`, licence **Apache-2.0**, repository `github.com/nasa/cea`, docs `nasa.github.io/cea` |
| `pycea` / `pyCEA` 0.1.0 | PyPI summary reads: *"DEPRECATED — replaced by the official nasa/cea package."* |
| `CEApy` 1.0.5 | Third-party automation wrapper, "under development" — not the official route |
| `rocketcea` 1.2.3 | The historical f2py wrapper around legacy CEA2. **Not installed**, per §8 of the spec |
| `nasa-cea`, `cea-py`, `cearun` | Do not exist on PyPI |

CEA v3 is a re-implementation of the legacy CEA2 Fortran code as
object-oriented Fortran 2008 with first-class Fortran/C/Python/MATLAB
interfaces, produced under NASA Engineering & Safety Center sponsorship.

**RocketCEA was not needed and was not investigated further.** The condition in
§65 of the spec — that RocketCEA only enters if the official interface cannot
meet the integration requirements — was not met: the official interface met
them.

---

## 5. Installation

| | NASA CEA | Cantera |
| --- | --- | --- |
| Command | `pip install cea` | `pip install cantera` |
| Result | **PASS** | **PASS** |
| Wall time | 17.5 s | 19.4 s |
| Wheel | `cea-3.3.4-cp313-cp313-win_amd64.whl`, 4.4 MB | `cantera-3.2.0-cp313-cp313-win_amd64.whl`, 5.3 MB |
| Dependencies pulled | numpy only | numpy, ruamel.yaml, typing_extensions |
| Python 3.13 | **PASS** | **PASS** (`requires_python <3.15,>=3.10`) |
| Windows | **PASS** | **PASS** |
| Licence | **Apache-2.0** | **BSD-3-Clause** |
| Compiler/toolchain needed | none | none |

Neither required a Fortran toolchain. Both ship prebuilt cp313 Windows wheels.

**This is the single most consequential finding of the spike.** Phase 5A's
ADR-21 rested on the premise that CEA is only reachable through a
Fortran-compiled wrapper of uncertain cp313 availability. That premise is
false for CEA v3.

---

## 6. Real API — NASA CEA

Structured, typed, Cython-backed. `py.typed` plus `.pyi` stubs are shipped.

```python
import numpy as np, cea

reac   = cea.Mixture(["CH4(L)", "O2(L)"])
prod   = cea.Mixture(["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4","C(gr)"])
solver = cea.RocketSolver(prod, reactants=reac)
soln   = cea.RocketSolution(solver)

w  = reac.of_ratio_to_weights(np.array([0.,100.]), np.array([100.,0.]), 3.4)
hc = reac.calc_property(cea.ENTHALPY, w, [111.643, 90.170]) / cea.R   # per-reactant T

solver.solve(soln, w, 100.0, supar=40.0, hc=hc)      # pc in bar

soln.T          # ndarray over stations [chamber, throat, exit]
soln.c_star     # ndarray, m/s
soln.Isp        # ndarray, m/s  (effective exhaust velocity)
soln.gamma_s    # ndarray, equilibrium isentropic exponent
soln.mole_fractions   # dict[str, ndarray]
```

| Element | Detail |
| --- | --- |
| Solvers | `EqSolver`, `RocketSolver`, `ShockSolver`, `DetonationSolver` |
| Results | `EqSolution`, `RocketSolution`, `ShockSolution`, `DetonationSolution`, `EqDerivatives` |
| Problem types | `HP`, `SP`, `TP`, `TV`, `UV`, `SV` |
| Inputs | `Mixture`, `Reactant`, weights, `of_ratio`, `phi`, `r_eq`, `pct_fuel` |
| Rocket controls | `pi_p` (pressure ratios), `subar`, `supar` (area ratios), `n_frz` (freeze station), `iac`, `ac_at`, `mdot`, `hc`, `tc` |
| Species control | `only`, `omit`, `insert`, `trace`, `products_from_reactants=True` |
| Extras | `transport=True`, `ions=True`, analytic + finite-difference derivatives |
| Return types | Python floats and `numpy.float64` arrays; compositions as `dict[str, …]` |
| Convenience | `cea.eq_solve(...)` one-shot function returning `EqSolution` |

**Text parsing required: NO.** Everything above is returned as Python objects.
A `bin/cea.exe` is shipped for legacy decks but is not on the integration path.

## 7. Real API — Cantera

```python
import cantera as ct

allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
gas = ct.Solution(thermo="ideal-gas",
                  species=[allsp[n] for n in ["CO","CO2","H","H2","H2O","O","O2","OH","CH4"]])
gas.TPY = 298.15, 10.0e6, "CH4:0.2273, O2:0.7727"
gas.equilibrate("HP")

gas.T, gas.P, gas.density, gas.mean_molecular_weight
gas.cp_mass, gas.cv_mass, gas.sound_speed
gas.X, gas.Y                       # numpy arrays, parallel to gas.species_names
```

Databases shipped: `gri30.yaml` (53 species), **`nasa_gas.yaml` (748)**,
**`nasa_condensed.yaml` (382)**, plus `liquidvapor.yaml`, `airNASA9.yaml` and
others — 23 YAML files in total. Text parsing: **NO**.

---

## 8. Capability matrix

`NATIVE` = directly exposed. `DERIVABLE` = the caller can compute it from
exposed primitives. `UNSUPPORTED` = not obtainable in the requested model.

| Capability | NASA CEA v3.3.4 | Cantera 3.2.0 |
| --- | --- | --- |
| HP equilibrium (chamber) | **NATIVE** (`cea.HP`) | **NATIVE** (`equilibrate('HP')`) |
| SP equilibrium (expansion) | **NATIVE** (`cea.SP`) | **NATIVE** (`equilibrate('SP')`) |
| TP / UV / TV / SV equilibrium | **NATIVE** | NATIVE (`TP`, `UV`, `TV`, `SV`) |
| Mole fractions | **NATIVE** `dict[str,float]` | **NATIVE** array + `species_names` |
| Mass fractions | **NATIVE** `dict[str,float]` | **NATIVE** array |
| Chamber temperature | **NATIVE** | **NATIVE** |
| Density, volume | **NATIVE** | **NATIVE** |
| Mean molar mass | **NATIVE** (`M` and `MW`) | **NATIVE** (`mean_molecular_weight`) |
| Specific gas constant R | DERIVABLE (`Ru/M`) | DERIVABLE (`ct.gas_constant/M`) |
| cp, cv — **frozen** | **NATIVE** (`cp_fr`, `cv_fr`) | **NATIVE** (`cp_mass`, `cv_mass`) |
| cp, cv — **equilibrium** | **NATIVE** (`cp_eq`, `cv_eq`) | **UNSUPPORTED** — not exposed |
| **Equilibrium isentropic exponent γ_s** | **NATIVE** (`gamma_s`) | **DERIVABLE** — finite difference along an SP path (§11) |
| Specific enthalpy, entropy, Gibbs | **NATIVE** | **NATIVE** |
| Speed of sound | **NATIVE** (`sonic_velocity`) | **NATIVE** (frozen; `sound_speed`) |
| Transport (viscosity, conductivity, Pr) | **NATIVE**, frozen *and* equilibrium | NATIVE (separate transport model) |
| Condensed species | **NATIVE** (in the product set; `num_condensed`) | NATIVE via `nasa_condensed.yaml` (separate phase objects) |
| Ionised species | **NATIVE** (`ions=True`) | NATIVE (`gri30_ion.yaml`) |
| **Cryogenic liquid reactants** | **NATIVE** — `O2(L)`, `CH4(L)`, `H2(L)`, `RP-1`, `N2H4(L)`, `N2O4(L)`, `H2O2(L)`, `Jet-A(L)`, `JP-10(L)` with valid-T ranges | **UNSUPPORTED** — no liquid reactants in either database (§12) |
| Per-reactant temperatures | **NATIVE** (vector `T_reac` / `calc_property(..., [T1,T2])`) | DERIVABLE by the caller, but see §12 |
| Custom / surrogate reactants | **NATIVE** (`cea.Reactant(formula=, enthalpy=, …)`) | NATIVE (`ct.Species` from YAML) |
| Chamber state | **NATIVE** | **NATIVE** |
| Throat state | **NATIVE** (station 2) | DERIVABLE — caller must find the sonic point |
| Exit state | **NATIVE** | DERIVABLE (SP to a pressure) |
| **Area-ratio-driven expansion** | **NATIVE** (`supar`, `subar`) | **UNSUPPORTED** — no area-ratio solver |
| Pressure-ratio-driven expansion | **NATIVE** (`pi_p`) | **NATIVE** (SP) |
| Equilibrium (shifting) expansion | **NATIVE** | **NATIVE** |
| Frozen expansion | **NATIVE** (`n_frz`) | DERIVABLE (`SPX` at fixed X) |
| Frozen-at-throat | **NATIVE** (`n_frz=2`) | DERIVABLE, caller-implemented |
| **c\*** | **NATIVE** | **UNSUPPORTED** |
| **Cf** | **NATIVE** | **UNSUPPORTED** |
| **Isp / Isp_vacuum** | **NATIVE** | **UNSUPPORTED** |
| Exit Mach | **NATIVE** | DERIVABLE |
| Finite-area combustor (FAC) | **NATIVE** (`iac=False`, `ac_at`, `mdot`) | UNSUPPORTED |
| Detonation, shock tube | **NATIVE** | NATIVE (via other Cantera facilities) |
| **Chemical kinetics** | **UNSUPPORTED** | **NATIVE** — 325 reactions in gri30 |
| Reactor networks, 1-D flames | UNSUPPORTED | **NATIVE** |
| Provider version | **NATIVE** (`__version__`, `lib_version()`) | **NATIVE** (`__version__`, `__git_commit__`) |
| Database identity | **NATIVE** (files on disk, hashable) | **NATIVE** (YAML files, hashable) |

**Not tested:** Cantera's multi-phase `MixturePhase` equilibrium with
`nasa_condensed.yaml` for a full two-phase rocket case; CEA's `ShockSolver` and
`DetonationSolver` beyond confirming the shipped examples run.

---

## 9. Units audit

Measured by identity checks, not read off documentation.

| Quantity | CEA native | Cantera native | RocketForge SI | Conversion |
| --- | --- | --- | --- | --- |
| Pressure | **bar** | **Pa** | Pa | CEA: ×1e5 |
| Temperature | K | K | K | none |
| Density | **kg/m³** | kg/m³ | kg/m³ | none |
| Specific volume | m³/kg | m³/kg | m³/kg | none |
| **Molar mass** | **kg/kmol** (= g/mol) | **kg/kmol** | **kg/mol** | both: ÷1000 |
| cp, cv | **kJ/(kg·K)** | **J/(kg·K)** | J/(kg·K) | CEA: ×1000 |
| Enthalpy | **kJ/kg** | **J/kg** | J/kg | CEA: ×1000 |
| Entropy | **kJ/(kg·K)** | **J/(kg·K)** | J/(kg·K) | CEA: ×1000 |
| Speed of sound | m/s | m/s | m/s | none |
| c\* | **m/s** | — | m/s | none |
| **Isp** | **m/s** (effective exhaust velocity) | — | m/s | ÷ g₀ for seconds |
| Cf | dimensionless | — | — | none |
| Universal gas constant | **8314.51** J/(kmol·K) | **8314.46261815324** J/(kmol·K) | 8.31446261815324 J/(mol·K) | see below |

**Molar-mass trap resolved by identity, not by magnitude.** For CEA,
`cp_fr − cv_fr = 387.362 J/(kg·K)` against `Ru·1000/M = 387.360`, ratio
1.0000057 — so M is kg/kmol and cp is kJ/(kg·K). For Cantera the same identity
gives ratio 0.9999999999999994.

**Isp confirmed as a velocity by identity:** `Cf × c* = 3434.5992` and
`Isp = 3434.5992`, relative difference **0.000e+00**. Dividing by g₀ gives
350.23 s.

**CEA uses the pre-2019 universal gas constant** (8314.51 vs CODATA-2019
8314.46261815324), a relative difference of **5.699e-06**. Phase 5A doc `09`
§7.2 anticipated this but proposed a ~1e-8 tolerance for the `R = Ru/M̄`
consistency check. **That tolerance is too tight by three orders of magnitude
and must be ≥1e-5.** This is the clearest concrete correction the spike makes
to Phase 5A.

---

## 10. Provenance available

| Item | CEA | Cantera |
| --- | --- | --- |
| Package version | `cea.__version__` = 3.3.4 | `ct.__version__` = 3.2.0 |
| Native library version | `cea.lib_version()` = 3.3.4 (+ major/minor/patch) | `ct.__git_commit__` = `4a8358e` |
| Database file | `data/thermo.lib`, 612 751 B | `nasa_gas.yaml`, 276 140 B |
| Database SHA-256 | `8e5df1cca92d4a48…3ec52a` | `4de6199d65d2d3db…67e4db` |
| Transport data | `data/trans.lib`, 35 108 B, `c203d93307464…834111` | separate transport model |
| Species list | `Mixture.species_names`, `num_gas`, `num_condensed`, `num_elements` | `gas.species_names`, `n_species` |
| Chemistry mode | caller-supplied constant, echoed in the call | caller-supplied string |
| Data search path | fixed package-relative | `ct.get_data_directories()` |

**Phase 5A's provenance concept is implementable for both.** SHA-256 hashing of
the on-disk database files worked without touching them. What RocketForge must
add itself for both: the chemistry-mode label, the reactant conditions, and the
O/F basis — none of which the providers record.

---

## 11. The two-gamma question, settled empirically

At the common case (§13) the three quantities all called "gamma" are:

| Quantity | CEA | Cantera |
| --- | --- | --- |
| γ_s, equilibrium isentropic exponent | **1.133592** (native) | 1.133473 (finite difference) |
| cp/cv, **frozen** | 1.198530 | 1.198324 |
| cp/cv, **equilibrium** | 1.180800 | not available |

γ_s and the frozen cp/cv differ by **5.7 %** at this state. Phase 5A ADR-26
asserted this distinction on physical grounds; it is now measured.

**Cantera does not expose γ_s.** Obtaining it requires a finite-difference
derivative along an SP path — two extra equilibrium solves per point, plus a
step-size choice that is a numerical-accuracy decision RocketForge would own.
CEA returns it directly.

---

## 12. Cryogenic reactants and the fluid-property boundary

This is the sharpest capability split found.

**CEA: native.** The thermo database carries liquid reactants with valid
temperature ranges:

| Reactant | Valid T range [K] |
| --- | --- |
| `O2(L)` | 80.17 – 100.17 |
| `CH4(L)` | 101.643 – 121.643 |
| `H2(L)` | 10.27 – 30.27 |
| `RP-1` | 288.15 – 308.15 |
| `N2H4(L)` | 100.0 – 800.0 |
| `H2O2(L)` | 272.74 – 6000.0 |
| `Jet-A(L)` | 220.0 – 550.0 |
| `N2O4(L)`, `JP-10(L)`, `CH6N2(L)` (MMH), `C2H5OH(L)` | present |

Per-reactant temperatures are accepted as a vector. The phase enthalpy is
demonstrably applied:

| LOX/CH₄, O/F 3.4, Pc 100 bar, Ae/At 40 | Tc [K] | c\* [m/s] | Isp exit [m/s] |
| --- | --- | --- | --- |
| gaseous reactants at 298.15 K | 3673.27 | 1878.90 | 3500.76 |
| **liquid reactants at NBP** (CH₄ 111.643 K, O₂ 90.17 K) | **3598.33** | **1846.90** | **3434.60** |
| difference | **−74.94** | −32.00 | **−66.17** |

A 74.9 K shift in flame temperature is exactly the effect Phase 5A doc `11`
§3.3 warned would be silently lost.

**Cantera: unsupported.** `O2(L)` and `CH4(L)` are in neither `nasa_gas.yaml`
nor `nasa_condensed.yaml`. Two failure modes were demonstrated:

* forcing the ideal-gas phase to 111.643 K returns `phase_of_matter='gas'` and
  `h = −5.0457e6 J/kg` — **a silently wrong liquid-reactant enthalpy**;
* `ct.Methane()` (PureFluid) gives a real fluid enthalpy, `−5.0480e6 J/kg`, but
  **on its own datum**, which cannot be added to the reacting-mixture datum.

**Phase 5A §21's question is answered, and the answer is provider-dependent:**

> The `ThermochemistryProvider` / `FluidPropertyProvider` separation is
> **necessary for Cantera** and **not necessary for CEA**.

With CEA as the chemistry provider, no fluid-property provider is needed to get
the reactant enthalpy right — CEA owns that data. The separation should still
be kept (ADR-23 stands), because `physics.fluids` answers a different question
(injector densities, coolant properties), but it is no longer load-bearing for
chamber energetics.

---

## 13. Common case — Tier A comparison

Deliberately chosen so both providers can represent it without inventing
liquid support, with a **matched species set**.

```
CH4 + O2, GASEOUS reactants at 298.15 K
O/F = 3.4 by mass,  P = 10 MPa,  HP equilibrium
species: CO CO2 H H2 H2O O O2 OH CH4   (9, gas only)
```

| Quantity | NASA CEA | Cantera | relative difference |
| --- | --- | --- | --- |
| Chamber temperature [K] | 3673.614577 | 3677.007652 | **9.24e-04** |
| Mean molar mass [kg/kmol] | 21.4644308 | 21.47347618 | 4.21e-04 |
| Density [kg/m³] | 7.027310231 | 7.023824253 | 4.96e-04 |
| γ_s (equilibrium) | 1.133592185 | 1.133472637 | **1.05e-04** |
| Frozen cp/cv | 1.198530038 | 1.198323861 | 1.72e-04 |
| Frozen cp [J/(kg·K)] | 2338.514034 | 2339.543199 | 4.40e-04 |
| Entropy [J/(kg·K)] | 12183.22507 | 12186.20831 | 2.45e-04 |
| Σ mole fractions | 1.0 | 1.0 | 6.66e-16 |
| X(H₂O) | 0.4734548 | 0.4751382 | 3.56e-03 |
| X(CO) | 0.1834638 | 0.1834926 | 1.57e-04 |
| X(CO₂) | 0.1206217 | 0.1207108 | 7.39e-04 |
| X(OH) | 0.0754158 | 0.0718310 | **4.75e-02** |
| X(O₂) | 0.0255665 | 0.0264512 | 3.46e-02 |
| X(O) | 0.0119625 | 0.0123504 | 3.24e-02 |

**Parity tier: Tier 2** (Phase 5A `13` §4) — the species sets were matched but
the thermodynamic databases are independent (`thermo.lib` vs `nasa_gas.yaml`),
and the universal gas constants differ by 5.7e-06.

Bulk thermodynamic properties agree to **better than 1e-3 relative**, which for
two independently maintained codes is a strong mutual corroboration. The
**radical** mole fractions (OH, O, O₂) differ by 3–5 %, which is the expected
signature of different radical thermodynamic data and is exactly why Phase 5A
refused to declare one provider ground truth.

**Neither provider was treated as truth.** The disagreement is reported, not
resolved.

---

## 14. LOX/CH₄ rocket case and O/F trade study

**Case** (one transparent representative condition — **not** claimed as a
design optimum):

```
LOX / CH4, liquid reactants at NBP: O2(L) 90.170 K, CH4(L) 111.643 K
Pc = 100 bar = 10 MPa
Ae/At = 40 (supersonic area ratio)
O/F = 2.5 .. 4.5, step 0.05  ->  41 points
products: CO CO2 H H2 H2O O O2 OH HO2 H2O2 CH4 C(gr)
```

Three chemistry modes per point: equilibrium, frozen-at-throat (`n_frz=2`),
frozen-at-chamber (`n_frz=1`). All 41 points converged; Σ X ∈ [1−2e-16, 1+2e-16].

| O/F | Tc [K] | M̄ | γ_s | c\* [m/s] | Isp_eq [m/s] | Isp_frz-throat | ΔIsp | ΔIsp/Isp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.50 | 3180.44 | 18.497 | 1.1768 | 1853.98 | 3319.40 | 3288.31 | 31.09 | 0.94 % |
| 2.90 | 3464.34 | 20.164 | 1.1475 | 1872.38 | 3409.60 | 3335.32 | 74.28 | 2.18 % |
| 3.30 | 3584.97 | 21.485 | 1.1342 | 1854.50 | **3437.25** | 3310.39 | 126.86 | 3.69 % |
| 3.70 | 3614.79 | 22.537 | 1.1299 | 1821.15 | 3403.04 | 3254.32 | 148.72 | 4.37 % |
| 4.10 | 3603.98 | 23.411 | 1.1286 | 1784.96 | 3336.59 | 3191.06 | 145.54 | 4.36 % |
| 4.50 | 3574.51 | 24.158 | 1.1284 | 1749.93 | 3269.96 | 3128.65 | 141.30 | 4.32 % |

**Three different maxima, at three different mixture ratios:**

| Metric | Peak | at O/F |
| --- | --- | --- |
| Chamber temperature | 3615.01 K | **3.75** |
| Characteristic velocity c\* | 1872.46 m/s | **2.85** |
| Equilibrium Isp | 3437.25 m/s (350.5 s) | **3.30** |

This is the trade-study point made concrete: **"optimum O/F" is undefined
without a stated objective.** Phase 5A doc `14` §4.3 argued this on principle;
the sweep demonstrates it in one table.

The equilibrium–frozen gap grows monotonically from **0.94 % to 4.37 %** across
the range — i.e. the chemistry assumption matters more as the mixture gets
richer in oxygen, and at O/F 3.7 choosing the wrong mode costs 149 m/s.

**Mode ordering verified** (Phase 5A doc `11` §5 invariants I7/I8/I9):
at O/F 3.4, exit Isp is equilibrium **3500.76** > frozen-at-throat **3350.36** >
frozen-at-chamber **3297.38** m/s, and exit temperature is 1940.94 > 1258.40 >
1173.06 K.

**Cantera's sweep is a different physical case** and is recorded as such:
gaseous reactants at 298.15 K, chamber-only equilibrium plus a
pressure-ratio-100 expansion, no c\*/Cf/Isp. It is not compared to CEA's liquid
case as though it were the same problem.

**No equilibrium/frozen average was produced.** The homework heuristic
`(Isp_eq + Isp_frozen)/2` has no physical basis and is not used anywhere in the
spike or in provider scoring.

### Figures

All in `acceptance/phase_5b0/`, raw sweep points drawn as markers, no smoothing:

| File | Content |
| --- | --- |
| `01_tc_vs_of.png` | Tc vs O/F, both providers, with an explicit note that the cases differ |
| `02_molar_mass_vs_of.png` | M̄ vs O/F, both providers |
| `03_gamma_vs_of.png` | γ_s (CEA native, Cantera finite-difference) and Cantera frozen cp/cv |
| `04_species_vs_of.png` | Chamber composition vs O/F, log scale, 8 species |
| `05_cea_cstar_vs_of.png` | c\* vs O/F with its maximum annotated |
| `06_cea_isp_equilibrium_frozen_vs_of.png` | Three chemistry modes, bracketed |
| `07_cea_equilibrium_frozen_gap.png` | ΔIsp and ΔIsp/Isp vs O/F, twin axes |

---

## 15. Published reference reproduction

**The user-supplied propellant-performance table was not available in this
session**, so its source metadata is **INCOMPLETE** and no attempt was made to
reproduce it. Per §27–29 of the spike spec, a screenshot alone is not treated
as an authoritative citation, and the publication was not guessed.

A better reference was found instead: **CEA v3 ships the NASA RP-1311 Part II
worked examples**, which is precisely the published source Phase 5A doc `13` §3
named for Tier-4 validation.

| Result | |
| --- | --- |
| Examples shipped | 14 (`cea/samples/rp1311/example1.py` … `example14.py`) |
| **Executed successfully** | **14 of 14** |

Coverage includes TP, HP, UV, TV equilibrium; IAC and FAC rocket problems;
frozen-from-throat; condensed species; a `BeO(L)` insert; a solid-propellant
blend with a custom reactant; Chapman–Jouguet detonation; and a shock tube.

**RP-1311 example 8 re-run** (LOX/LH₂, O/F 5.55157, Pc 53.3172 bar, IAC,
subar 1.58, supar 25/50/75, pi_p 10/100/1000):

```
converged, 9 stations, 11 products auto-selected
Tc = 3383.84 K,  c* = 2332.34 m/s
Isp at Ae/At = 75:  4399.12 m/s  (448.6 s)
```

**Status: the shipped examples execute and produce physically coherent
results. They were NOT numerically diffed against the printed RP-1311 tables**,
because the shipped scripts print rather than assert, and transcribing the
published tables is Phase 5B work under the rounding-box discipline of
Phase 5A doc `13` §4. Classified: **approximately reproduced, not yet verified
digit-by-digit.**

---

## 16. Conservation and identity checks

| Check | Result |
| --- | --- |
| Σ mole fractions (CEA) | 1.000000000000000 |
| Σ mass fractions (CEA) | 1.000000000000000 |
| Σ mole fractions (Cantera) | 1.000000000000000 |
| **Element balance, independent** | **max relative imbalance 1.037e-09** |
| cp − cv = R (CEA) | ratio 1.0000057 (pre-2019 Ru) |
| cp − cv = R (Cantera) | ratio 0.9999999999999994 |
| γ = cp/cv | consistent, both |
| R = Ru/M̄ | consistent, both, within the Ru discrepancy |
| Ideal gas p = ρRT (CEA) | 9 999 943 Pa vs 10 000 000 input — 5.7e-06, the Ru difference |
| Ideal gas p = ρRT (Cantera) | relative error **0.0** |
| Sound speed vs √(γRT) (Cantera) | relative difference **0.0** |
| Enthalpy conserved across HP (Cantera) | \|Δh\| = 5.36e-05 J/kg on −1.057e+06 |

The element balance was computed **independently** — my own atom and
molar-mass bookkeeping over the returned mass fractions, not the provider's
internal residual. Phase 5A doc `13` §4 proposed ~1e-10 for this tolerance;
the measured value is **1.04e-09**, so the tolerance should be ~1e-8.

---

## 17. Provider state behaviour

| Property | CEA | Cantera |
| --- | --- | --- |
| Repeatability, 10 identical solves | **bitwise identical** | **bitwise identical**, spread 0.0 |
| A/B/A/B/A state leakage | **none** | **none** (even with a shared object) |
| Result object mutability | `EqSolution.T` is **read-only** (`AttributeError` on assignment); the solution object is the mutated carrier the solver writes into | `Solution` is a **fully mutable state container**; `T`, `P`, `X` are all settable |
| Raw objects may escape an adapter? | **No** — the solution is rebound by the next `solve()` | **No** — the object *is* the state |
| Threading, 4 workers vs serial | **0.85× — slower than serial**, no corruption | not tested |
| Import side effects | **`import cea` initialises the native library and loads `thermo.lib`** — `is_initialized()` is True immediately | import is cheap; databases load on first use |

Two consequences for Phase 5B:

**Neither provider's objects may cross the adapter boundary.** Cantera's for the
obvious reason; CEA's because the result object is reused by the next solve.
Phase 5A's immutable-snapshot contract is confirmed as necessary for both.

**Threading buys nothing.** CEA gives 0.85× at four workers — measurably worse
than serial. (An earlier measurement suggesting a 10× slowdown was warm-up
contamination inside the pool and is withdrawn.) Recommendation: **serial
in-process**, with a separate process only if isolation from a native crash is
wanted later. No thread pool.

**CEA's import is not free and can fail on missing data**, which is how the
first frozen-executable attempt failed (§19). Availability detection must
therefore wrap the import itself:

```python
try:
    import cea
    AVAILABLE, VERSION = True, cea.__version__
except (ImportError, ValueError) as exc:      # ValueError: thermo.lib not found
    AVAILABLE, VERSION = False, None
```

---

## 18. Performance

Matched workload — **chamber-only HP equilibrium, 11 gas species**, so the two
columns are comparable. Medians.

| Measurement | NASA CEA | Cantera | ratio |
| --- | --- | --- | --- |
| Cold import (fresh subprocess, median of 5) | 321.8 ms | 358.5 ms | 1.11× |
| First solve after setup | 0.228 ms | 1.037 ms | 4.5× |
| **Warm solve** | **44.2 µs** | **839.3 µs** | **19.0×** |
| Cold setup + solve | 0.216 ms | 0.945 ms | 4.4× |
| **100-point sweep** | **5.52 ms** (0.055 ms/pt) | **51.87 ms** (0.519 ms/pt) | **9.4×** |
| **1000-point sweep** | **58.01 ms** (0.058 ms/pt) | **517.61 ms** (0.518 ms/pt) | **8.9×** |

**CEA-only workload, labelled separately** — full rocket solve (3 stations plus
c\*, Cf, Isp), *more* work than either column above:

| Measurement | NASA CEA |
| --- | --- |
| Warm full rocket solve | 271.0 µs |
| 100-point rocket sweep | 31.64 ms (0.316 ms/pt) |
| 1000-point rocket sweep | 337.02 ms (0.337 ms/pt) |

CEA's **full rocket** solve (271 µs) is still faster than Cantera's
**chamber-only** solve (839 µs).

Memory (working set):

| | baseline | after import | after setup | after 1000-point sweep |
| --- | --- | --- | --- | --- |
| CEA | 28.2 MB | 34.1 MB | 34.3 MB | **34.8 MB** |
| Cantera | 28.4 MB | 35.7 MB | 50.3 MB | **50.7 MB** |

Neither leaks. Cantera's setup step costs ~14.6 MB, from parsing the
748-species YAML.

**Batch API:** neither provides a vectorised multi-case call; both are repeated
scalar solves. Reusing an initialised solver/mixture matters for CEA
(0.216 ms cold-setup vs 44 µs warm — a ~5× penalty for rebuilding per request),
which is a direct input to Phase 5B's adapter design.

---

## 19. PyInstaller feasibility

Minimal console scripts, `--onedir`, built in the isolated environments. The
RocketForge spec file was **not** touched.

| | NASA CEA | Cantera |
| --- | --- | --- |
| Build with no extra flags | builds, **fails at runtime** | builds, **fails at runtime** |
| Failure without flags | `ValueError: thermo.lib not found` — data files not collected | `ImportError: dynamic module does not define module export function (PyInit_drawnetwork)` |
| **Working incantation** | `--collect-data cea --collect-binaries cea` | `--collect-all cantera` |
| **Result with flags** | **PASS**, exit 0 | **PASS**, exit 0 |
| **Frozen vs source parity** | **exact, every digit** | **exact, every digit** |
| Bundle size | **60 MB**, 121 files | **63 MB**, 216 files |
| Provider native artifacts | `cea/lib/cea_bindc.dll`, `libcea.cp313-win_amd64.pyd`, `cea.libs/cea_bindc-*.dll` | `cantera/_cantera.cp313-win_amd64.pyd` (6 MB), `hdf5-*.dll`, `sundials_core/cvodes/idas/nvecserial-*.dll`, `yaml-cpp-*.dll` |
| Data files needing collection | `data/thermo.lib`, `data/trans.lib` (also duplicated to `share/cea/`) | `cantera/data/*.yaml` (23 files) |
| Resource path after freezing | resolves under `_MEIPASS/cea/data` | `get_data_directories()` correctly reports `_MEIPASS/cantera/data` |
| VC++ runtime | `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `msvcp140-*.dll` bundled | same, plus its own `msvcp140-*` |
| Hooks needed | none beyond the flags | none beyond the flag |

Frozen CEA output, identical to the source run:

```
Tc_K=3598.3332   cstar_m_per_s=1846.9047   gamma_s=1.132650
M_kg_per_kmol=21.769469   Isp_exit_m_per_s=3434.5992
```

**Marginal size.** Both bundles are dominated by numpy's 20 MB OpenBLAS DLL,
which RocketForge already ships. The provider-specific additions are roughly
**5 MB for CEA** and **~12 MB for Cantera** (its 6 MB extension plus HDF5,
three SUNDIALS libraries and yaml-cpp).

**Clean-machine risk: LOW for both.** Both bundle their VC++ runtime, neither
needs a PATH entry, an environment variable, an external executable or a global
data directory. CEA's data files resolve package-relative; Cantera's resolve via
its own data-directory API. Cantera carries a wider native surface (HDF5,
SUNDIALS), which is more that can go wrong but nothing that failed here.

---

## 20. Risks

**NASA CEA**

| Risk | Assessment |
| --- | --- |
| Import initialises the native library and reads `thermo.lib` | **Real.** A packaging mistake fails at import, not at first use. Mitigated by the flags in §19 and a guarded import. |
| Invalid inputs are silently accepted | **Real.** Negative temperature and negative pressure raised **no error**; negative pressure produced a `CEA_NOT_CONVERGED` RuntimeWarning and returned. **RocketForge must validate inputs itself** rather than relying on the provider. |
| 15-character name limit | **Real, discovered here.** A reactant/species name of 16+ characters raises `CEA_INVALID_SIZE`. Makes Phase 5A's `cea_name` mapping field load-bearing. |
| `num_condensed` is a *product-list* count, not a presence count | **Real trap.** At O/F 3.4 `num_condensed == 1` while `X[C(gr)] == 0`. ADR-28 must key on the actual condensed **mass fraction**, never on this counter. |
| `M` vs `MW` are distinct properties | Both equal here; they diverge when condensed species are present. Must not be used interchangeably. |
| Pre-2019 universal gas constant | Known, 5.7e-06, accommodated by tolerance. |
| Younger codebase than CEA2 | v3 is a re-implementation; less field time than the legacy Fortran. Mitigated by the RP-1311 examples and by cross-checking against Cantera. |
| Shipped sample's density conversion | `samples/h2_o2.py` prints `density*1e-3` under a "kg/m³" label while the identity check shows the native value is already kg/m³. A sample-script discrepancy, not a library defect — but a reason to trust identities over sample code. |
| No kinetics | Out of Phase 5 scope anyway. |

**Cantera**

| Risk | Assessment |
| --- | --- |
| **No liquid reactants** | **Blocking for rocket chamber work.** §12. Would require a separate fluid-property path and a datum reconciliation that Phase 5A doc `09` §3.4 explicitly forbids doing casually. |
| **No rocket performance** | c\*, Cf, Isp, area-ratio expansion all absent; RocketForge would implement and validate them itself. |
| γ_s not exposed | Requires finite differencing, with a step-size choice RocketForge would own and have to justify. |
| Mutable `Solution` objects | Standard for Cantera; handled by the adapter boundary. |
| Wider native surface when frozen | HDF5 + SUNDIALS + yaml-cpp; more to break on another machine, though nothing broke here. |
| ~19× slower on the matched workload | Matters for sweeps; irrelevant for single points. |
| Setup memory | +14.6 MB per Solution family from YAML parsing. |

---

## 21. Phase 5A assumptions — confirmed, revised, unresolved

**CONFIRMED**

| Assumption | Evidence |
| --- | --- |
| ADR-26 — γ is mode-dependent; γ_s ≠ cp/cv | Measured: 1.1336 vs 1.1985, a 5.7 % difference (§11) |
| ADR-25 — enthalpy datums must never be mixed | Cantera's PureFluid and ideal-gas enthalpies differ and are not interchangeable (§12) |
| ADR-28 — condensed phases need explicit handling | Al/O₂ produced a **13.0 %** condensed mass fraction; `num_condensed` is a misleading counter (§20) |
| Immutable snapshot at the adapter boundary | Both providers' result objects are unsafe to let escape (§17) |
| Doc `11` §5 mode ordering (I7/I8/I9) | equilibrium > frozen-at-throat > frozen-at-chamber, in both Isp and exit T (§14) |
| Doc `09` §3.2 element balance as the key invariant | Independently verified to 1.04e-09 (§16) |
| Provenance is implementable | Versions and database SHA-256 obtainable for both (§10) |
| Providers are optional and detectable | Guarded import works; must catch `ValueError` too for CEA (§17) |
| ADR-23 — keep the two provider protocols separate | Still right, but no longer load-bearing for chamber energetics under CEA (§12) |
| ADR-19 — do not write an in-house equilibrium solver | Reinforced: both providers are free, fast, permissively licensed and better validated than anything in-house would be |

**REVISED**

| Assumption | Correction |
| --- | --- |
| **ADR-20/21 — Cantera primary, CEA developer-side** | **Reversed.** See §22. CEA v3 installs cleanly on cp313/Windows with no toolchain, is Apache-2.0, has a structured API, and is the only one of the two that can do the job at all (liquid reactants, rocket performance). |
| CEA "carries a Fortran extension whose cp313 Windows wheel availability is unconfirmed" | **False for CEA v3.** A cp313 win_amd64 wheel exists and installs in 17.5 s. |
| CEA licensing is an open legal question (OQ-3) | **Largely resolved:** the PyPI distribution declares **Apache-2.0**. Redistribution inside a bundled application looks unproblematic. Still `NEEDS_REVIEW` by the owner for the bundled `thermo.lib`/`trans.lib` data files specifically. |
| Doc `09` §7.2 — `R = Ru/M̄` tolerance ~1e-8 | **Too tight.** CEA's pre-2019 Ru forces **≥1e-5**. |
| Doc `13` §4 — element-balance tolerance ~1e-10 | **Too tight.** Measured 1.04e-09; use ~1e-8. |
| Doc `10` §5.2 — CEA "wrong shape for a shipped dependency" | **False.** It packages more cleanly than Cantera: fewer files, smaller marginal size, narrower native surface. |
| Doc `10` §5.1 — Cantera "fits RocketForge specifically" | Overstated. It fits *general chemistry*; it does not fit *rocket* chemistry without RocketForge supplying liquid reactants, the sonic search, γ_s, and all performance metrics. |

**UNRESOLVED**

| Question | Status |
| --- | --- |
| Digit-level agreement with printed RP-1311 tables | Examples run; numerical diff is Phase 5B work (§15) |
| The user-supplied propellant table | Source metadata **INCOMPLETE** — not supplied this session, not guessed (§15) |
| Cantera multi-phase condensed equilibrium | **NOT TESTED** |
| Two-phase rocket performance in either provider | Out of scope; Phase 5A refuses these states anyway |
| Whether a chemistry dependency is acceptable in `requirements.txt` at all | **Owner's call** — this is the real remaining question (§22) |

---

## 22. OQ-2 recommendation

Phase 5A recorded a `PHASE_3_SPEC_CONFLICT`: Phase 3 `06` §8 step 3 says
"thermochemistry interfaces **+ a CEA provider**", while Phase 5A proposed
building Cantera first.

**The evidence resolves this in Phase 3's favour.** Phase 3 was right, and
Phase 5A's reasoning was based on a factual premise about CEA's packaging that
CEA v3 has made obsolete.

The decisive points, in order of weight:

1. **Cantera cannot do the job for a rocket chamber.** It has no liquid
   reactants. LOX/CH₄ at their boiling points is not an exotic case; it is *the*
   case, and getting it wrong costs 74.9 K of flame temperature and 66 m/s of
   Isp. Everything else is secondary to this.
2. **CEA gives natively what RocketForge would otherwise have to build and
   validate**: c\*, Cf, Isp, area-ratio expansion, throat state, freeze-point
   control, γ_s, equilibrium cp.
3. **The packaging objection was wrong.** cp313 wheel, no toolchain, Apache-2.0,
   17.5 s install, ~5 MB marginal bundle, exact frozen parity.
4. **CEA is 9–19× faster** on the matched workload.
5. **CEA ships the RP-1311 published examples**, i.e. the validation corpus
   Phase 5A's V&V plan already named.

**No owner decision is strictly required to proceed**, because the recommended
Phase 5B scope (§24) is provider-independent. One decision *is* still the
owner's: **whether a compiled chemistry dependency may enter
`requirements.txt` at all**, given the project's deliberately minimal runtime
(PySide6 + numpy) and the architecture test that fails the build on a SciPy
import. That is a policy question the spike cannot answer, only inform.

---

## 23. Recommended provider architecture

**Option A** from the spike spec, with one adjustment.

| Role | Provider | Why |
| --- | --- | --- |
| **Primary** | **NASA CEA v3** (`cea`) | The only candidate that covers liquid reactants and rocket performance; fastest; permissively licensed; packages cleanly; ships the reference corpus |
| **Secondary / independent oracle** | **Cantera** | Independent database and solver — genuine cross-validation value, demonstrated at 1e-4 to 1e-3 on bulk properties. Dev-only (`requirements-dev.txt`), skipped when absent |
| **Future optional** | Cantera again, promoted | If kinetics, reactor networks or 1-D flames ever enter scope. Not now (Phase 5A ADR-29) |
| **Not pursued** | RocketCEA | The condition for considering it (§65 of the spec) was never met |

**CEA must not become a god solver.** It returns c\*, Cf and Isp natively, and
RocketForge should consume them — but *architectural ownership* of rocket
performance stays in `engineering.nozzle` per ADR-15. Concretely: the provider
supplies them as **provider outputs with provenance**, and `engineering.nozzle`
remains the module that owns performance semantics, applies efficiencies, and
decides what is reported. A CEA-returned Isp is a value, not a licence to
relocate the physics boundary.

---

## 24. Phase 5B impact

Contract changes the real APIs suggest, to be made **in Phase 5B, not now**:

| Change | Reason |
| --- | --- |
| `R = Ru/M̄` tolerance → **≥1e-5** | CEA's pre-2019 Ru (§9) |
| Element-balance tolerance → **~1e-8** | Measured 1.04e-09 (§16) |
| `ChamberGas.molar_mass` — providers report **kg/kmol** | Conversion belongs in the adapter; the trap is real |
| Add `gamma_frozen` **and** `gamma_equilibrium` to the state | CEA gives both natively; one field cannot carry both (§11) |
| Add `cp_frozen` / `cp_equilibrium` | Same reason |
| `condensed_mass_fraction` must be **computed from the composition**, never from a provider counter | `num_condensed` counts the product list (§20) |
| `PropellantDefinition.cea_name` — enforce **≤15 characters** | `CEA_INVALID_SIZE` (§20) |
| `ProviderCapabilities` — add `liquid_reactants`, `rocket_performance`, `area_ratio_expansion`, `native_gamma_s` | The capability split found here is sharper than Phase 5A anticipated |
| Provider protocol — allow a **station array** return | CEA returns all stations from one call; forcing per-station calls would waste ~5× |
| Adapter must **cache the initialised solver** | 0.216 ms cold-setup vs 44 µs warm (§18) |
| Availability detection must catch `ValueError` as well as `ImportError` | CEA raises `ValueError` when `thermo.lib` is missing (§17) |
| Input validation is **RocketForge's job** | CEA silently accepts negative T and P (§20) |
| Execution model: **serial in-process**, no thread pool | 0.85× at four threads (§17) |

**Phase 5B scope stays provider-independent.** Regardless of §23, Phase 5B
should still build `Species`, `Phase`, `Composition`, `PropellantDefinition`,
`PropellantStream`, the thermodynamic-state DTOs, the provider protocol,
provenance, the capability model, and the conservation/identity tests — with a
stub provider — before any adapter is written. Phase 5B must not become "wrap
CEA everywhere".

---

## 24b. Common adapter sketch — documentation only

Built from the **real** APIs above, but shaped by Phase 5A's
provider-independent contract, not by either library's vocabulary. Not
implemented.

```python
# SPECIFICATION SKETCH - Phase 5B, not production code.

class ThermochemistryProvider(Protocol):
    name: str
    version: str
    capabilities: ProviderCapabilities

    def solve_chamber(self, request: ChamberRequest) -> ChamberGas: ...
```

`ChamberRequest` is RocketForge's vocabulary — propellant names, an O/F on the
canonical mass basis, reactant temperatures and phases, chamber pressure in
**Pa**, a chemistry mode. Neither provider's spelling leaks into it.

**CEA adapter** — the mapping is direct:

```python
def solve_chamber(self, req):
    reac = cea.Mixture([req.fuel.cea_name, req.oxidiser.cea_name])   # <=15 chars each
    prod = cea.Mixture(req.product_species or [], products_from_reactants=not req.product_species)
    solver = self._cached_rocket_solver(reac, prod)         # 5x penalty if rebuilt
    soln = cea.RocketSolution(solver)
    w  = reac.of_ratio_to_weights(OXID, FUEL, req.of_mass)
    hc = reac.calc_property(cea.ENTHALPY, w,
                            [req.fuel_temperature, req.oxidiser_temperature]) / cea.R
    solver.solve(soln, w, req.chamber_pressure / 1e5,       # Pa -> bar
                 supar=req.area_ratio, hc=hc,
                 n_frz=FREEZE_STATION[req.mode])

    return ChamberGas(                                     # immutable snapshot
        temperature      = float(soln.T[0]),               # K
        pressure         = float(soln.P[0]) * 1e5,         # bar -> Pa
        gamma_equilibrium= float(soln.gamma_s[0]),         # native
        gamma_frozen     = float(soln.cp_fr[0] / soln.cv_fr[0]),
        molar_mass       = float(soln.M[0]) / 1000.0,      # kg/kmol -> kg/mol
        gas_constant     = R_UNIVERSAL / (float(soln.M[0]) / 1000.0),
        cp_frozen        = float(soln.cp_fr[0]) * 1000.0,  # kJ -> J
        cp_equilibrium   = float(soln.cp_eq[0]) * 1000.0,
        composition      = Mixture({k: float(v[0]) for k, v in soln.mole_fractions.items()},
                                   database="cea:thermo.lib", database_version=SHA256[:16]),
        condensed_mass_fraction = _condensed_from_composition(soln),  # NOT num_condensed
        provenance = ThermochemistryProvenance(
            provider_name="NASA CEA", provider_version=cea.__version__,
            mode=req.mode.value, species_database="thermo.lib",
            species_database_version=SHA256, reactant_conditions={...}),
    )
```

**Cantera adapter** — same return type, materially more work, and it must
refuse what it cannot do:

```python
def solve_chamber(self, req):
    if req.fuel.phase is not Phase.GAS or req.oxidiser.phase is not Phase.GAS:
        raise ProviderDomainError(
            "Cantera has no liquid reactant data; a gaseous substitute would "
            "misstate the reactant enthalpy")            # refuse, never approximate

    gas = self._cached_solution(req.product_species)
    gas.TPY = req.fuel_temperature, req.chamber_pressure, _mass_string(req.of_mass)
    gas.equilibrate("HP")

    return ChamberGas(
        temperature       = gas.T,                        # already SI
        pressure          = gas.P,
        gamma_frozen      = gas.cp_mass / gas.cv_mass,
        gamma_equilibrium = self._gamma_s_finite_difference(gas),   # NOT native
        molar_mass        = gas.mean_molecular_weight / 1000.0,
        gas_constant      = ct.gas_constant / gas.mean_molecular_weight,
        cp_frozen         = gas.cp_mass,
        cp_equilibrium    = None,                          # not exposed
        composition       = Mixture(dict(zip(gas.species_names, map(float, gas.X))),
                                    database="cantera:nasa_gas.yaml",
                                    database_version=SHA256[:16]),
        provenance = ThermochemistryProvenance(
            provider_name="Cantera", provider_version=ct.__version__,
            mode=req.mode.value, species_database="nasa_gas.yaml",
            warnings=("gamma_equilibrium is a finite-difference estimate",)),
    )
```

Three properties the sketch is built to preserve:

* **No provider object escapes.** Both adapters read scalars out and construct a
  frozen `ChamberGas`. CEA's solution is rebound by the next `solve()`;
  Cantera's `Solution` is mutable. Neither can be handed upward.
* **Unit conversion happens once, at the boundary**, and is visible in the code
  rather than assumed.
* **A capability gap is a refusal with a reason**, never a substitution — which
  is why the Cantera adapter raises on liquid reactants instead of quietly using
  a gaseous enthalpy.

---

## 25. Isolation compliance

| Check | Result |
| --- | --- |
| Main `.venv` gained `cea` | **No** |
| Main `.venv` gained `cantera` | **No** |
| Main `.venv` gained `rocketcea` | **No** |
| Main `.venv` gained `matplotlib` | **No** |
| `PyInstaller` in main `.venv` | Present, **pre-existing** from the Phase 4G packaging step; not installed by this phase |
| `requirements.txt` modified | **No** (mtime 2026-08-30) |
| `requirements-dev.txt` modified | **No** (mtime 2026-08-30) |
| `build_exe.bat` modified | **No** (mtime 2026-08-29) |
| RocketForge `.spec` modified | **No** |
| `rocketforge/physics/compressible/` modified | **No** — manifest byte-identical |
| `rocketforge/core/` modified | **No** — manifest byte-identical |
| Production Python changed | **None** |
| QML changed | **None** |
| Experimental scripts outside the production package | Yes — `experiments/phase_5b0/`, imported by nothing under `rocketforge/` |
| Provider environments | Isolated under `%TEMP%`, not inside the project |

---

## 26. Durable artifacts

`acceptance/phase_5b0/`

| File | Content |
| --- | --- |
| `cea_probe.json` | CEA provenance, species availability, units, composition, rocket modes, errors, state |
| `cea_cryo_condensed.json` | Cryogenic reactants, Isp units, condensed phases, aluminised case, RP-1, element balance |
| `cea_final_tests.json` | RP-1311 example 8, custom reactants, H₂O₂ blend, concurrency, availability |
| `cea_followup.json` | Custom reactant with a legal name, threading isolation |
| `cantera_probe.json` | Cantera provenance, databases, HP equilibrium, identities, gammas, SP expansion, cryogenic limits, errors, state |
| `cea_of_sweep.csv` | 41 points × 37 columns, LOX/CH₄ liquid, 3 chemistry modes |
| `cantera_of_sweep.csv` | 41 points × 35 columns, CH₄/O₂ gaseous, chamber + PR-100 expansion |
| `provider_common_case_comparison.csv` | Matched-species Tier-A comparison with relative differences |
| `common_case_cea.json`, `common_case_cantera.json` | Raw common-case results |
| `cea_benchmark.json`, `cantera_benchmark.json` | Timing |
| `cea_memory.json`, `cantera_memory.json` | Working-set measurements |
| `01`–`07` `*.png` | Seven experimental figures |

`experiments/phase_5b0/` — 11 scripts, none imported by `rocketforge/`.

Not stored in the project: provider environments, wheel caches, build trees.

---

## 27. Verdict

**PROVIDER SPIKE COMPLETE — READY FOR PHASE 5B**

Both providers install and work on the actual RocketForge interpreter, both
expose structured APIs needing no text parsing, both freeze with PyInstaller
and reproduce source values exactly, and both are permissively licensed. The
capability split is decisive rather than marginal: only NASA CEA v3 can
represent cryogenic liquid reactants and rocket performance, and it is also the
faster and smaller of the two.

Phase 5A's provider recommendation is **revised**; Phase 3's expectation of a
CEA provider is **vindicated**. Nothing in RocketForge production was changed,
and the frozen Compressible v1.0 manifest is byte-identical.
