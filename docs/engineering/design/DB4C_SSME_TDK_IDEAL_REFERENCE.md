# DB-4C — SSME ideal reference case from the 1985 TDK printout: compared, never judged

Status: PROPOSED. Nothing is implemented. No RocketForge or CEA value has been computed for this case, so none of
the rules below could be fitted to a result. The owner decides §1 before any code is written.

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

## 7. Where the code would go

| File | Change |
|---|---|
| `rocketforge/comparison/units.py` | add `"R"` (temperature, 5/9 exactly) and `"lbf*s/lbm"` (velocity, 9.80665 m/s exactly: a pound-force is a pound-mass times standard gravity) |
| `rocketforge/comparison/ssme_tdk_1985.py` | new: the `ReferenceCase` above, with page citations and the source id; exported from `comparison/__init__.py` |
| `rocketforge/application/analysis/reference_ideal_case.py` | new: `run_ideal_case(*, solve_chamber=None, solve_expansion=None, oracle=None)`. It never raises and returns kind ok, unavailable or refused, with step A, step B, the declarations and the provider warnings. The solvers are injectable, as in DB-4B, so the rules are tested without a provider. All or nothing: if any of the five computations fails, nothing is reported but the reason |
| `tools/reference_engines/report_ideal_case.py` | new: the hand-run report, run in `.venv-cea` |
| `tests/comparison/test_ssme_tdk_1985.py` | the transcription (source values, which are data), the kind, no verdict, the keys, and the two unit factors |
| `tests/application/test_reference_ideal_case.py` | the pairings, the vacuum reference, no combined row, no verdict or tolerance field, and the refusal and unavailable paths with injected solvers. One CEA-gated run asserts structure and finiteness only |

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

- One operating point, one 1985 program, vacuum only.
- It does not validate CEA: it is no verdict. The Phase 5E printout (`rocketforge/data/reference/performance_nasa_cea_2002_lox_lh2.json`)
  stays the oracle's validation.
- It says nothing about delivered SSME performance. The measured 452.6 s and the report's own efficiencies are not part
  of it.
- The vacuum and freezing conventions rest on the manual of the same program generation (§2), not on the SSME pages.

## 10. Possible later additions (not decided)

- The large-throat first solution (Figure 7) as a second point under the same rules.
- The manual's RL-10 OTV sample (Table 7-3), likewise; not a catalog configuration.
- A display, after a scientific-UI review.
