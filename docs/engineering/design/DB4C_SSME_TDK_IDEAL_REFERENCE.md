# DB-4C — SSME ideal reference case from the 1985 TDK printout: compared, never judged

Status: IMPLEMENTED (2026-11-07). The owner accepted the six decisions in §1 as recommended. The rules in §8 were
fixed, and the tests written, before any RocketForge or CEA value was computed for this case. §11 records the first
run as readings only. §12 adds a second point from the same report, the enlarged throat of Figure 7, under the same
decisions and rules, and §13 records its first run. §14 adds a third point, the RL-10 OTV test engine from the TDK
manual's own sample, likewise, and §15 records its first run.

The source and its reading are in `docs/research/engine_database/db05/IDEAL_VALUE_SOURCES.md`. This document answers
that page's §7.

What this does not do: it creates no regression reference, and the hard and validation totals stay 0. It changes no
engine evidence, catalog entry or DB-4A gate rule. No result here can pass, fail or lock anything.

## 1. Decisions

| # | Decision | Recommended |
|---|---|---|
| 1 | Classify the printout as `INDEPENDENT_CODE`, imported: differences reported, no verdict | Yes (§3) |
| 2 | Keep it in the comparison layer, with a report-only runner. No engine evidence, catalog or gate change | Yes (§7) |
| 3 | Record three quantities of the first solution: chamber temperature, ISP (ODE), ISP (ODF). Nothing else | Yes (§4) |
| 4 | Report two separate steps: A, the source against the same model class in CEA; B, RocketForge's constant-gamma reduction against CEA. Print no combined source-to-RocketForge row | Yes (§5) |
| 5 | The case carries its own chamber pressure: the stagnation pressure of TDK's rocket problem. The engine assertion `AS-DB05-US-SSME-BLOCK-I-002` (3285 psia, station UNKNOWN) is not reinterpreted | Yes (§4) |
| 6 | Report only, with no workspace display, as DB-4B | Yes (§8) |

All six were accepted by the owner on 2026-11-07, as recommended.

With decision 1 refused (held as `NASA_PUBLISHED`), every row would carry a verdict at half the last printed digit,
0.00005 s. The source cannot meet that against itself: two of its figures print -422.3787 and -422.3749 BTU/lb for the
same inputs (research page §3.7). A "differs" would then describe 1985 data, not RocketForge.

## 2. What the source settles, and how it was settled

Three readings were open after the search. Each is now settled from TDK's own printed output. No RocketForge or CEA
value was used.

**ISP (ODE) and ISP (ODF) are vacuum values.** The TDK engineering manual (NTRS 19860007470, NASA-CR-178628,
April 1985) prints a complete sample run: three zones of equal mass flow at area ratio 2.0. Its summary table (printed
p.7-41, PDF p.433) gives ISP (ODE) 335.4859 and ISP (ODF) 326.8484. The same run's ODE output gives each zone both
CEA-style columns, IVAC and I (exit pressure equal to ambient):

| Zone | Equilibrium IVAC | Equilibrium I | Frozen IVAC | Frozen I | Pages (printed / PDF) |
|---|---|---|---|---|---|
| 1 (O/F 6.5, 300 psia) | 336.17 | 275.41 | 326.89 | 273.89 | 7-8, 7-10 / 400, 402 |
| 2 (O/F 8.0, 285 psia) | 317.95 | 259.81 | 308.75 | 258.51 | 7-15, 7-16 / 407, 408 |
| 3 (O/F 5.0, 270 psia) | 352.34 | 291.87 | 344.92 | 289.76 | 7-21, 7-23 / 413, 415 |

Weighted by the printed zone mass flows (0.33330, 0.33340, 0.33330), the IVAC columns give 335.4849 and 326.8515. These
match the summary to within the rounding of two-decimal zone values. The I columns give 275.70 and 274.05. The kinetics module
agrees: on PDF p.419 it prints zone 3's "VACUUM SPECIFIC IMPULSE (SEC)" as 0.35186014E+03. Its ODK ISP summary on
the same page lists that value as 351.860, with a mass average of 335.221, which the summary prints as
ISP (ODK) 335.2208.

**ODF is frozen at the chamber composition.** The manual says the ODE module calculates performance "assuming that the
chemical composition is frozen at the chamber (stagnation) conditions" (PDF pp.98, 155). Subroutine FROZEN works with
"Composition frozen at combustion conditions" (PDF p.167). The frozen sample page holds the molecular weight at its
chamber value, 13.966, from chamber to exit (PDF p.402).

**The input `P` is the stagnation pressure** of the rocket problem (PDF pp.334-335), as the research page records.

The SSME report itself does not restate these conventions. They are read from the manual of the same program and year
(SEA, 1985). That the SSME run's summary follows them is an inference from one program generation, recorded as such.
It is not a reading of the SSME pages.

## 3. Classification

`SourceKind.INDEPENDENT_CODE`, `CaseOrigin.IMPORTED`, by the precedent of `rocketforge/comparison/rp1311_historical.py`.
That module holds a NASA printout made with older code and data, and compares it without a verdict. Here the code itself
is a different program:

- code: "TDK (Two-Dimensional Kinetics), ODE module; Software and Engineering Associates";
- code_version: "not stated (the 1985 program with the shock option)";
- database_version: "not stated (the thermodynamic data of that program; the report does not identify them)";
- benchmark_class: `"B"`, a check that is not a solid propellant, as for RP-1311 Example 12 in
  `rocketforge/comparison/rp1311.py`.

## 4. The case

Hand-transcribed from the rendered pages of NTRS 19860012108 (`SRC-NTRS-19860012108`). Figure 3 is printed p.17,
PDF p.23. Figure 6 is printed p.20, PDF p.26, first solution.

Inputs, as the source states them:

| Input | Value | Where |
|---|---|---|
| Chamber pressure | 3285 psia, the stagnation pressure of the rocket problem (`P = 3285.`, `PSIA = T`) | Figure 3 `$ODE`; manual pp.334-335 |
| Mixture ratio | 6.05485, oxidiser to fuel by mass (`OFSKED`); Figure 6 prints 6.054850 | Figure 3 |
| Area ratio | 77.5 (`ASUP` schedule and `$ODK EP`); Figure 6 prints EP (NOZZLE) 77.50022, recorded, not used | Figures 3, 6 |
| Fuel | H2(L), -2154. cal/mol, 20.27 K ("Tank Conditions CPIA 246") | Figure 3 |
| Oxidiser | O2(L), -3102. cal/mol, 90.180 K | Figure 3 |
| Expansion | one-dimensional, isentropic, vacuum; equilibrium (ODE) and frozen at the chamber composition (ODF) | §2 |

Quantities. In `units.py` both new units are exact by definition (§7):

| Key | Value | Unit | Printed decimals |
|---|---|---|---|
| `chamber_temperature` | 6543.192 | R | 3 |
| `vacuum_specific_impulse:equilibrium` | 465.1311 | lbf*s/lbm | 4 |
| `vacuum_specific_impulse:frozen` | 446.7661 | lbf*s/lbm | 4 |

The expansion model is part of the key, as a composition basis is part of a fraction's key. A shifting value can then
never be compared with a frozen one. The suffixes are the values of `ExpansionMode` (`equilibrium`, and `frozen`,
which means composition fixed at the chamber value).

`missing`, recorded and never filled in:

- the program version and the thermodynamic data;
- the ODE product species list;
- whether the summary's ISP (ODE) was evaluated at the scheduled 77.5 or at the nozzle's 77.50022.

Not recorded, with the reason kept in the case notes:

| Printed | Why not |
|---|---|
| ISP (ODK) | kinetics; outside RocketForge's and CEA's models |
| ISP (TDK), ISP (TC), CSTAR (TDK), CF (TDK), CD | two-dimensional flow and boundary layer |
| Every second-solution value | regenerative heat added to the propellant (DELH1 118.7092 BTU/lb); not a tank-condition inlet state |
| HCHAM (ODE) | an input consequence, not a result; its use is the consistency check in the research page §3.7 |
| Figure 7, large throat | not a catalog configuration; a possible second point later (§10) |

## 5. The two steps

One operating point is solved once and used by both steps: LH2 at 20.27 K, LOX at 90.17 K, O/F 6.05485, 3285 psia
(22 649 277.708 Pa by the exact psia factor), area ratio 77.5.

### Step A — the source against the same model class

`compare(case, observed)` over the three quantities. For an `INDEPENDENT_CODE` case every row is `compared`, and so is
the case. No bound is formed.

| Row | Source | Computed by | Same model class because |
|---|---|---|---|
| Chamber temperature | 6543.192 R | RocketForge's chamber result (`thermochemistry_service.solve_case`, read by `observed_from_chamber`) | HP equilibrium at the same pressure, ratio and reactants |
| Vacuum Isp, equilibrium | 465.1311 s | `performance_oracle.run_oracle(case, 77.5, "equilibrium").specific_impulse_vacuum` | shifting equilibrium, vacuum |
| Vacuum Isp, frozen | 446.7661 s | `run_oracle(case, 77.5, "frozen").specific_impulse_vacuum` | frozen at the chamber composition, vacuum |

A difference here contains the code (TDK's 1985 ODE module against CEA 3.3.4), the thermodynamic data, and the
declared input differences in §6. It is never a RocketForge defect. RocketForge's chamber is a CEA solve, so the
temperature row is CEA against TDK as well. It is labelled as RocketForge's chamber result because that is the value
RocketForge reports.

### Step B — RocketForge's reduction against CEA, at the same point

`performance_oracle.oracle_comparison_rows`, the existing "model difference" table, uses only its `isp_vacuum` row, one
pairing per gamma basis:

| RocketForge (`performance_service.solve_performance`, gamma strategy chamber, vacuum) | CEA (`run_oracle`, vacuum) |
|---|---|
| frozen gamma basis | `"frozen"` |
| equilibrium gamma basis | `"equilibrium"` |

The source takes no part in step B. A difference here is the constant-gamma, calorically perfect reduction alone, with
the same code, data and inputs on both sides. It is labelled "model difference", never error. Both bases are always
shown, as in DB-4B.

### No combined row

The report never prints RocketForge minus TDK. That one number would mix code, data and the reduction. It would also
read as RocketForge's error against a NASA source, the same trap DB-4B avoided by not calling its ratio an efficiency. A
reader who wants the total can add the two steps and keep the attribution.

## 6. Declared input differences

Each is put on the result verbatim as a declaration. None is corrected or estimated away.

| Input | Source | Run | Note |
|---|---|---|---|
| O2(L) | -3102.000 cal/mol, 90.180 K | CEA's assigned -12979 J/mol (-3102.055 cal/mol) at 90.17 K | 90.17 K is CEA's reference temperature, where RocketForge's enthalpy coupling adds no increment |
| H2(L) | -2154.000 cal/mol | CEA's assigned -9012 J/mol (-2153.920 cal/mol) at 20.27 K | also CEA's reference temperature (`tests/providers/cea/test_cea_provider_live.py`), so no increment |
| Area ratio | 77.5 scheduled; 77.50022 printed for the nozzle | 77.5 | |
| Product species | not printed | the provider's H/O set (`HO_PRODUCT_SPECIES`) | |

From those reactant enthalpies alone, the chamber enthalpy at O/F 6.05485 moves by 0.0075 BTU/lb, 1.8e-5 of the
printed -422.3787. That is arithmetic on the printed and CEA constants, not a computed result. It is smaller than the
0.0038 BTU/lb by which the source's two figures disagree with each other.

## 7. Where the code goes

| File | Change |
|---|---|
| `rocketforge/comparison/units.py` | add `"R"` (temperature, 5/9 exactly) and `"lbf*s/lbm"` (velocity, 9.80665 m/s exactly: a pound-force is a pound-mass times standard gravity) |
| `rocketforge/comparison/ssme_tdk_1985.py` | new: the `ReferenceCase` above, with page citations and the source id. Imported by its module path and not re-exported from `comparison/__init__.py`, as the `rp1311` modules are |
| `rocketforge/application/analysis/reference_ideal_case.py` | new: `run_ideal_case(*, solve_chamber=None, solve_expansion=None, oracle=None)`. It never raises and returns kind ok, unavailable or refused, with step A, step B, the declarations and the provider warnings. The solvers are injectable, as in DB-4B, so the rules are tested without a provider. All or nothing: if any of the five computations fails, nothing is reported but the reason |
| `tools/reference_engines/report_ideal_case.py` | new: the hand-run report, run in `.venv-cea` |
| `tests/comparison/test_ssme_tdk_1985.py` | the transcription (source values, which are data), the kind, no verdict, the keys, and the two unit factors |
| `tests/application/test_reference_ideal_case.py` | the pairings, the vacuum reference, no combined row, no verdict or tolerance field, and the refusal and unavailable paths with injected solvers. One CEA-gated run asserts structure and finiteness only |

§12 extends the case module and the runner to a second point, and §14 to a third from a second document.

`units.py` is a shared contract. When it changes, both full suites and `tests/test_architecture.py` run. The layering
is DB-4B's: the case sits in `comparison` and imports nothing from `providers`. The runner sits in
`application/analysis` and reaches CEA only through `performance_oracle` and `thermochemistry_service`.

## 8. Rules fixed now

- No verdict, tolerance, pass or fail. Step A rows say `compared`, step B rows say `model difference`.
- No test pins a computed difference, and no rule, input, pairing or declaration may change in response to one. A change
  needs its own reason, stated without reference to the result.
- Report only. A workspace display is a separate decision, taken after reading the first run, and needs a
  scientific-UI review.
- Engine evidence, the catalog, the DB-4A gate and the regression totals are untouched. Regression references stay 0.

## 9. Limits

- Three operating points from two 1985 documents of one program (§12, §14), vacuum only.
- It does not validate CEA: it is no verdict. The Phase 5E printout (`rocketforge/data/reference/performance_nasa_cea_2002_lox_lh2.json`)
  stays the oracle's validation.
- It says nothing about delivered SSME performance. The measured 452.6 s and the report's own efficiencies are not part
  of it.
- The vacuum and freezing conventions rest on the manual of the same program generation (§2), not on the SSME pages.

## 10. Possible later additions (not decided)

- The large-throat first solution (Figure 7) as a second point under the same rules. Taken up in §12.
- The manual's RL-10 OTV sample (Table 7-3), likewise; not a catalog configuration. Taken up in §14.
- The manual's next sample, §7.3 (printed p.7-59, PDF p.451): Rocketdyne's prototype Advanced Space Engine for
  OTV propulsion, 2300 psia and 400:1, input in Table 7-4 and summary in Table 7-5. Found while reading §7.2 and
  not read yet.
- A display, after a scientific-UI review.

## 11. First run (2026-11-07)

Run by hand: `.venv-cea\Scripts\python.exe tools\reference_engines\report_ideal_case.py`, NASA CEA through the
provider, at one point: LH2 20.27 K, LOX 90.17 K, O/F 6.05485, 22 649 277.708 Pa, area ratio 77.5. All five
computations succeeded and the provider raised no warning. These are readings. No test pins them, and no rule, input,
pairing or declaration was changed after seeing them (§8).

Step A, the 1985 TDK printout against the same model class in CEA. Every row is `compared`; none is judged:

| Quantity | TDK 1985 | Computed | Difference |
|---|---|---|---|
| Chamber temperature | 3635.107 K (6543.192 R) | 3617.574 K, RocketForge's chamber (a CEA HP solve) | -17.533 K (-0.48 %) |
| Vacuum Isp, equilibrium | 465.1311 s | 464.6838 s, CEA | -0.447 s (-0.096 %) |
| Vacuum Isp, frozen at the chamber | 446.7661 s | 447.0315 s, CEA | +0.265 s (+0.059 %) |

Step B, RocketForge's constant-gamma reduction against CEA at the same point. The printout takes no part. Both rows are
a model difference, both in vacuum:

| Gamma basis | RocketForge | CEA, matching expansion | Difference |
|---|---|---|---|
| frozen | 454.4515 s | 447.0315 s (frozen) | +1.660 % |
| equilibrium | 475.2373 s | 464.6838 s (equilibrium) | +2.271 % |

What these readings do not say:

- The step A differences are not attributed. They contain the two codes, their thermodynamic data and the §6 input
  differences together. The reactant enthalpies alone move the chamber enthalpy by 1.8e-5 (§6), so they are not what
  separates the chamber temperatures, but nothing here separates code from data. The species list TDK used is not
  printed. This was not investigated further, and the case does not ask for it.
- The chamber temperature row differs by more, relatively, than either Isp row. That is recorded, not explained.
- Step B is the reduction alone. It is not an error against TDK, and the two steps are not added in this record.
- The first run changes no engine evidence, catalog entry, DB-4A gate rule or regression total. Regression references
  stay 0.

## 12. A second point: the enlarged throat, Figure 7 (2026-11-07)

Taken up from §10, which listed it before the first run, after the owner's go-ahead to continue. It adds no decision:
the six in §1 and the rules in §8 apply unchanged. Its transcription, rules and tests are fixed here before any value is
computed for it.

The same report runs TDK on a "Large Throat" design: the main combustion chamber is modified for a larger throat and
the nozzle assembly is unchanged. In the report's words, this "reduces the nozzle expansion ratio from 77.5 to 69.5:1",
and the chamber pressure falls "from 3285 (109% power level) to 3010 psia" (printed p.2, PDF p.8). Figure 4 (printed
p.18, PDF p.24) is the TDK input for this design. Figure 7 (printed p.21, PDF p.27) is its summary.

It is a 1985 design study, not a catalog configuration. The catalog records `CFG-RS25-SMALL-THROAT` as the baseline this
study starts from, "Not Block IIA or Block II". This case is linked to no configuration, `CFG-RS25-BLOCK-II` included.

Inputs, as Figure 4 states them:

| Input | Value | Current design |
|---|---|---|
| Chamber pressure | 3010 psia, the stagnation pressure of the rocket problem (`P = 3010.`, `PSIA = T`, `DELH = 0`) | 3285 psia |
| Mixture ratio | 6.05485 (`OFSKED`); Figure 7 prints 6.054850 | same |
| Area ratio | 69.5 (`ASUP` schedule and `$ODK EP`); Figure 7 prints EP (NOZZLE) 69.48698, recorded, not used | 77.5 |
| Fuel | H2(L), -2154. cal/mol, 20.27 K | same card |
| Oxidiser | O2(L), -3102. cal/mol, 90.180 K | same card |
| Expansion | one-dimensional, isentropic, vacuum; as §2 | same |

Quantities, from Figure 7's first TDK/BLM solution:

| Key | Value | Unit | Printed decimals |
|---|---|---|---|
| `chamber_temperature` | 6526.882 | R | 3 |
| `vacuum_specific_impulse:equilibrium` | 463.2604 | lbf*s/lbm | 4 |
| `vacuum_specific_impulse:frozen` | 444.7228 | lbf*s/lbm | 4 |

Not recorded, for the reasons in §4: ISP (ODK) 463.0793; the two-dimensional and boundary-layer values; the whole
second solution (DELH1 116.6856 BTU/lb); and HCHAM (ODE) -422.3749, one side of the research page's §3.7 inconsistency.

`missing` is as in §4, with 69.5 against the printed 69.48698. That gap is 1.9e-4 of the area ratio, against 2.8e-6 for
the current design, and it is declared on the result like every other input difference. It is not estimated: an
estimate would need the expansion model, which is a computed result.

Declarations: §6's reactant and species lines apply unchanged. The area ratio line reads 69.5 against 69.48698. The
chamber pressure line says the design is a 1985 study linked to no catalog configuration, in place of the engine
assertion the current design names.

Code. The case is `SSME_TDK_1985_LARGE_THROAT` in `ssme_tdk_1985.py`. A `TdkPoint` pairs each case with its numeric
inputs, and `POINTS` holds the current design first and the enlarged throat second. `run_ideal_case(point)` runs one
point; without a point it runs the current design, as before. `run_ideal_cases()` runs each point on its own. Each
point is all or nothing by itself, and one point's failure does not hide the other's result. The hand-run report prints
both.

No row compares the two points. Their difference is a design change inside one program; each point is set beside CEA,
never beside the other.

## 13. Second point, first run (2026-11-07)

Run by hand with the same report, which now prints both points. The enlarged throat ran at LH2 20.27 K, LOX 90.17 K,
O/F 6.05485, 20 753 219.452 Pa (3010 psia) and area ratio 69.5. All five computations succeeded and the provider raised
no warning. The current design's rows were identical to §11. These are readings: no test pins them, and nothing in §12
was changed after seeing them.

Step A, the 1985 TDK printout against the same model class in CEA. Every row is `compared`; none is judged:

| Quantity | TDK 1985 | Computed | Difference |
|---|---|---|---|
| Chamber temperature | 3626.046 K (6526.882 R) | 3608.797 K, RocketForge's chamber (a CEA HP solve) | -17.249 K (-0.48 %) |
| Vacuum Isp, equilibrium | 463.2604 s | 462.7992 s, CEA | -0.461 s (-0.100 %) |
| Vacuum Isp, frozen at the chamber | 444.7228 s | 444.9810 s, CEA | +0.258 s (+0.058 %) |

Step B, RocketForge's constant-gamma reduction against CEA at the same point. The printout takes no part. Both rows are
a model difference, both in vacuum:

| Gamma basis | RocketForge | CEA, matching expansion | Difference |
|---|---|---|---|
| frozen | 452.0964 s | 444.9810 s (frozen) | +1.599 % |
| equilibrium | 472.8420 s | 462.7992 s (equilibrium) | +2.170 % |

What these readings do not say:

- At both points, each step A difference has the same sign and nearly the same size: -17.5 and -17.2 K, -0.096 and
  -0.100 %, +0.059 and +0.058 %. That is recorded, not explained. It does not separate code from data, and it is not a
  row between the points.
- Everything §11 says it does not say holds here too. Step B is the reduction alone, and the two steps are not added.
- Engine evidence, the catalog, the DB-4A gate and the regression totals are unchanged. Regression references stay 0.

## 14. A third point: the RL-10 OTV test engine, TDK manual Table 7-3 (2026-11-07)

Taken up from §10, which listed it before the first run, after the owner's next go-ahead to continue. It adds no
decision: the six in §1 and the rules in §8 apply unchanged. Its transcription, rules and tests are fixed here before
any value is computed for it.

The source is the TDK engineering manual itself (NASA-CR-178628, NTRS 19860007470; G. R. Nickerson, L. D. Dang and
D. E. Coats, Software and Engineering Associates, April 1985), the manual §2 reads the conventions from. NTRS lists it
as public, `GOV_PUBLIC_USE_PERMITTED`, and not export controlled. Its §7.2 (printed p.7-53, PDF p.445) runs TDK on the
"Pratt and Whitney test engine for RL-10 OTV propulsion", an expander cycle "sized to produce a nominal vacuum thrust
of 15,500 pounds when operated at a chamber pressure of 394 psia and an expansion ratio of 205:1". The input was
"prepared by SEA, Inc. from data provided by NASA MSFC". The first ODE calculation is made "with the system enthalpy
set at the propellant tank values, i.e., liquid oxygen and liquid hydrogen at their normal boiling points". Table 7-2
(printed p.7-56, PDF p.448) is the input and Table 7-3 (printed p.7-58, PDF p.450) the summary. Both are printed
sideways and were read from pages rendered upright.

It is an RL10 test engine at area ratio 205, not a catalog configuration, and is linked to none.

Inputs, as Table 7-2 states them:

| Input | Value |
|---|---|
| Chamber pressure | 394.3 psia: `RKT=.TRUE.`, `P(1)=394.3`, `PSIA=.TRUE.` in `$ODE`, the stagnation pressure of the rocket problem as in §2 |
| Mixture ratio | 5.035244 (`OFSKED(1)`); Table 7-3 prints 5.035244 |
| Area ratio | 205.03, the last `ASUP` entry. `EPS=205.03376` sets the contour's exit, and Table 7-3 prints EP (NOZZLE) 205.0338, recorded, not used. The `$ODK` card is too faded to read beyond "205," |
| Fuel | H2(L), -2154. cal/mol, printed at 20.56 K (the SSME cards print 20.27 K) |
| Oxidiser | O2(L), -3102. cal/mol, printed at 90.110 K (the SSME cards print 90.180 K) |
| Expansion | as §2. Here the conventions come from the same manual's three-zone sample (§7.1), not from Table 7-3 |

Quantities, from Table 7-3's first TDK/BLM solution, where DELH and DELH1 are both 0:

| Key | Value | Unit | Printed decimals |
|---|---|---|---|
| `chamber_temperature` | 5815.918 | R | 3 |
| `vacuum_specific_impulse:equilibrium` | 477.5184 | lbf*s/lbm | 4 |
| `vacuum_specific_impulse:frozen` | 456.1371 | lbf*s/lbm | 4 |

Not recorded, for the reasons in §4: ISP (ODK) 474.4465; ISP (TDK) 469.6459 and every other two-dimensional and
boundary-layer value; the whole second solution (DELH1 156.3460 BTU/lb, EP (NOZZLE) 194.0614); and HCHAM (ODE)
-464.2563, which the printed inputs put at -464.264 (research page).

The inlet state is the SSME points'. A card's temperature is not what sets it: Table 7-3 prints H (FUEL) -2154.000 and
H (OXID) -3102.000 cal/mol, exactly what the SSME figures print for cards at 20.27 K and 90.180 K. So this point runs,
like the others, with CEA's assigned enthalpies at 20.27 K and 90.17 K, where RocketForge's enthalpy coupling adds no
increment. The card temperatures are declared, not used.

Thermodynamic data. The manual's §6.1 (printed pp.6-4 and 6-5, PDF pp.304-305) gives the data format, "identical to
the THERMO DATA described in Appendix D of NASA SP-273", and says coefficients "for many chemical species are supplied
with the computer program". It does not say which data file the sample used, so the case's database version stays not
stated, with that context.

Declarations differ from the SSME points' in five lines: both reactant lines (the card temperatures), the area ratio
(205.03 against 205.0338), the chamber pressure (394.3 psia, linked to no catalog configuration), and the conventions
line (the same manual's sample, not Table 7-3).

Code. A new module `rocketforge/comparison/tdk_1985.py` holds what every TDK case shares: the three keys, `TdkPoint`,
the code description and the quantity layout. `ssme_tdk_1985.py` keeps the report's two points. The new
`tdk_manual_1985.py` holds the manual's case, `TDK_MANUAL_1985_RL10_OTV`. `TdkPoint` gains the two printed card
temperatures and the conventions source. The runner's `POINTS` lists the SSME points, then this one. No row compares
any two points.

## 15. Third point, first run (2026-11-07)

Run by hand with the same report, which now prints three points. The RL-10 OTV point ran at LH2 20.27 K, LOX 90.17 K,
O/F 5.035244, 2 718 602.801 Pa (394.3 psia) and area ratio 205.03. All five computations succeeded and the provider
raised no warning. Both SSME points' rows were identical to §11 and §13. These are readings: no test pins them, and
nothing in §14 was changed after seeing them. One fault in the report's printout was fixed after this run: it printed
the mixture ratio to six significant figures, so 5.035244 showed as 5.03524. The run itself used 5.035244, which a test
pins, and no rule, input, pairing or declaration changed.

Step A, the TDK manual's printout against the same model class in CEA. Every row is `compared`; none is judged:

| Quantity | TDK 1985 | Computed | Difference |
|---|---|---|---|
| Chamber temperature | 3231.066 K (5815.918 R) | 3218.049 K, RocketForge's chamber (a CEA HP solve) | -13.016 K (-0.40 %) |
| Vacuum Isp, equilibrium | 477.5184 s | 477.3326 s, CEA | -0.186 s (-0.039 %) |
| Vacuum Isp, frozen at the chamber | 456.1371 s | 456.4435 s, CEA | +0.306 s (+0.067 %) |

Step B, RocketForge's constant-gamma reduction against CEA at the same point. The printout takes no part. Both rows are
a model difference, both in vacuum:

| Gamma basis | RocketForge | CEA, matching expansion | Difference |
|---|---|---|---|
| frozen | 469.6190 s | 456.4435 s (frozen) | +2.887 % |
| equilibrium | 501.2026 s | 477.3326 s (equilibrium) | +5.001 % |

What these readings do not say:

- At all three points, each step A difference has the same sign: CEA's chamber temperature is lower by 13.0 to 17.5 K,
  its equilibrium Isp lower by 0.04 to 0.10 %, its frozen Isp higher by 0.06 to 0.07 %. That is recorded, not
  explained, and it does not separate code from data.
- Step B is larger here than at either SSME point: +2.9 and +5.0 %, against +1.6 to 1.7 and +2.2 to 2.3 %. This point
  differs from those in chamber pressure, area ratio and mixture ratio at once, and the record does not separate them.
  It is the reduction's difference alone, never an error against the manual.
- Everything §11 says it does not say holds here too, and no row compares any two points.
- Engine evidence, the catalog, the DB-4A gate and the regression totals are unchanged. Regression references stay 0.
