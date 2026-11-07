# Ideal-value sources for a reference-engine comparison (search of 2026-11-07)

Status: **research findings only**. Nothing was promoted. No ledger, manifest, catalog, evidence record,
gate, test or comparison case was changed. No RocketForge or CEA value was computed against any source value
below: the comparison rules come first (DB-4A §5, DB-4B §6), so this page records what the sources print and
what each value could and could not be used for.

## 1. What was looked for

DB-4A §2 and §6 leave one path to a reference that is not a delivered-against-ideal efficiency: a source
that prints an **ideal** thrust-chamber specific impulse for a catalog configuration, together with

- (a) the expansion model (shifting equilibrium, frozen, ...);
- (b) the inlet state of the cryogenic reactants (temperature or assigned enthalpy);
- (c) the chamber pressure, mixture ratio and area ratio the value was computed at.

Separately, a verdict is drawn only against `CEA_DIRECT` or `NASA_PUBLISHED` sources
(`rocketforge/comparison/cases.py`, `VERDICT_KINDS`).

## 2. Result

One source meets (a), (b) and (c) for a catalog configuration: **NTRS 19860012108**, the 1985 TDK performance
prediction for the SSME, whose "current design" is already this repository's `CFG-RS25-SMALL-THROAT`.

It cannot become a regression reference under the current rules. Its ideal values come from the 1985 TDK
program's one-dimensional modules, with the thermodynamic data of that time. The repository already holds a
NASA printout of that kind as `INDEPENDENT_CODE`: `rocketforge/comparison/rp1311_historical.py` keeps the 1996
RP-1311 Example 5 table without a verdict, because older code and data "differ" from a correct current result
without that being a RocketForge defect. The same reasoning applies here, more strongly (a different program).
`INDEPENDENT_CODE` draws no verdict, so the DB-4A gate result does not change and **regression references stay
0**.

No other source found prints (a), (b) and (c) for a catalog configuration (§5).

## 3. The SSME record: NTRS 19860012108

### 3.1 Identity and rights

| Item | Value |
|---|---|
| Title | Performance Predictions for an SSME Configuration with an Enlarged Throat |
| Authors, organization | G. R. Nickerson, L. D. Dang; Software and Engineering Associates, Inc. |
| Sponsor, contract | NASA MSFC, NAS8-35931 |
| Report numbers | NASA-CR-178740 (title-page stamp; the OCR text layer misreads it as 178743), SN 63, N86-21579 |
| Date | November 1985 |
| NTRS rights | GOV_PUBLIC_USE_PERMITTED, not export controlled |
| Already in the corpus | `SRC-NTRS-19860012108` (`tools/reference_engines/db2b_wave1_manifest.py`), shipping printed p.8 values on `CFG-RS25-SMALL-THROAT`: area ratio 77.5 (`AS-DB05-US-SSME-BLOCK-I-001`) and chamber pressure 3285 psia, station UNKNOWN (`-002`) |

### 3.2 Definitions printed

- PDF p.6 (abbreviations): "ODE One-Dimensional Equilibrium Expansion", "ODF One-Dimensional Frozen
  Expansion", "ODK One-Dimensional Kinetics Expansion". Where the frozen composition is fixed is not stated
  on the page.
- PDF p.5 (nomenclature): the theoretical specific impulse is the one "for an isentropic equilibrium expansion".
- The TDK engineering manual (NTRS 19860007470, NASA-CR-178628, April 1985, PDF pp.334-335) states that for a rocket problem the input
  `P` is the stagnation pressure, with printout "for the chamber pressure condition (i.e. stagnation)".

### 3.3 Inputs: Figure 3, "TDK Input for SSME Current Design Analysis" (printed p.17, PDF p.23)

Read from the rendered page image.

| Card | Printed |
|---|---|
| Title | SSME - COOLED WALL, CURRENT DESIGN, 109% |
| Modules | ODE = 1, ODK = 1, TDK = 1, BLM = 1 |
| Reactant H2 | 100., -2154., L, 20.27F (annotated "Tank Conditions CPIA 246") |
| Reactant O2 | 100., -3102., L, 90.180 |
| `$ODE` | RKT = T, P = 3285., XP = 1, PSIA = T, DELH = 0, OFSKED = 6.05485 |
| `$ODK` | EP = 77.5 |
| `$DATA` | ECRAT = 3 (TDK geometry) |

The enthalpies are cal/mol (Figure 6 units). They equal, to their printed digits, the CEA assigned enthalpies
RocketForge already uses (`rocketforge/providers/cea/enthalpy_coupling.py`: O2(L) -12979 J/mol = -3102.1
cal/mol, H2(L) -9012 J/mol = -2153.9 cal/mol, thermochemical calorie). The printed O2 temperature is 90.180 K;
DB-4B uses 90.17 K for LOX.

### 3.4 Outputs: Figure 6, "TDK Performance Summary for SSME Current Configuration" (printed p.20, PDF p.26)

Read from the rendered page image. The first solution uses the tank-condition enthalpies unchanged (DELH = 0,
DELH1 = 0). The second adds the
regenerative-cooling heat pickup to the propellant (DELH1 118.7092 BTU/lb) and is **not** a tank-condition
case.

| Quantity | Units | First solution | Second solution |
|---|---|---|---|
| CHAMBER PRESS | psia | 3285.000 | 3285.000 |
| CHAMBER TEMP | R | 6543.192 | 6609.458 |
| MIXTURE RATIO | - | 6.054850 | 6.054850 |
| H (OXID) | cal/mole | -3102.000 | -3102.000 |
| H (FUEL) | cal/mole | -2154.000 | -2154.000 |
| HCHAM (ODE) | BTU/lb | -422.3787 | -303.6657 |
| DELH1 (AVE) | BTU/lb | 0 | 118.7092 |
| EP (NOZZLE) | - | 77.50022 | 76.50255 |
| ISP (ODE) | s | 465.1311 | 469.2740 |
| ISP (ODK) | s | 464.9658 | 469.0910 |
| ISP (ODF) | s | 446.7661 | 449.4862 |
| CSTAR (TDK) | ft/s | 7713.456 | 7768.724 |
| CF (TDK) | - | 1.921868 | 1.928235 |
| ISP (TDK) | s | 460.7523 | 464.9368 |
| ISP (TC) | s | 453.8121 | 458.0472 |

6543.192 R is 3635.107 K; 3285 psia is 22.649 MPa (unit conversions only).

### 3.5 Large-throat design: Figure 7 (printed p.21, PDF p.27)

Not a catalog configuration (the enlarged-throat main combustion chamber), recorded for completeness. First
solution: Pc 3010.000 psia, Tc 6526.882 R, MR 6.054850, same reactant enthalpies, HCHAM -422.3749 BTU/lb,
EP 69.48698, ISP (ODE) 463.2604, ISP (ODK) 463.0793, ISP (ODF) 444.7228, ISP (TDK) 457.2597, ISP (TC) 450.4516 s.

### 3.6 What the report itself derives (printed p.4, PDF p.10)

Measured specific impulse of the current design "452.6±1 seconds"; I(TDK,BLM) = 458.0 s and
458.0/465.1 = .9847. The 458.0 s is the second solution's ISP (TC) and the 465.1 s the first solution's
ISP (ODE): the report's own efficiency mixes the two columns. This is a delivered-against-ideal efficiency,
the class DB-4B already handles as non-locking.

### 3.7 Checks of the source against itself (no RocketForge value involved)

- The printed reactant enthalpies at MR 6.05485 give a chamber enthalpy of -422.385 BTU/lb (molar masses
  31.9988 and 2.01588). Figure 6 prints -422.3787 and Figure 7 prints -422.3749 for the same printed inputs.
  The inputs are consistent with the printout to four figures, but the last printed digits are not
  reproducible from the printed inputs. Printed precision is therefore not an agreement scale for this
  source, as DB-4A §5 already says for tolerances in general.
- ISP (ODE) > ISP (ODK) > ISP (ODF) in both figures: the kinetic value lies between the equilibrium and
  frozen limits. The report puts the ODE-ODK difference at "only 2/10 seconds" (printed p.12, PDF p.18).

## 4. What a comparison with this record could mean

None of the following was computed.

| Candidate quantity | Same model class as RocketForge? | What a difference would contain |
|---|---|---|
| Chamber temperature, first solution | Yes: HP equilibrium at the same pressure, MR and reactant enthalpies; RocketForge's chamber stage is CEA | thermodynamic data and code (1985 TDK against current CEA) |
| ISP (ODE), ISP (ODF), first solution | No. Both are variable-property expansions. RocketForge's Isp is a constant-gamma reduction (frozen or equilibrium basis) through a frozen ideal nozzle | the constant-gamma reduction, the thermodynamic data and the code, mixed |
| ISP (ODE), ISP (ODF) against CEA's own rocket problem (shifting and frozen, `rocketforge/providers/cea/oracle.py`, not the runtime chain) | Same model class as TDK's ODE/ODF, but this compares CEA with TDK, not RocketForge's model | thermodynamic data and code |
| ISP (ODK), ISP (TDK), ISP (TC), CSTAR (TDK), CF (TDK) | No: kinetics, two-dimensional flow, boundary layer | outside RocketForge's model; not usable |
| Any second-solution value | No: heat added to the propellant, not a tank-condition inlet state | not usable as an ideal case |

Two cautions follow from the table:

- A difference between RocketForge's constant-gamma Isp and ISP (ODE) or ISP (ODF) would mostly measure the
  constant-gamma reduction. That is a property of RocketForge's model choice, not a defect, and DB-4B already
  reports both gamma bases so the reduction is visible.
- The ideal case's chamber pressure is a **model input**, the stagnation pressure of an infinite-area
  rocket problem. The engine assertion `-002` holds the same 3285 psia with station UNKNOWN. Carrying the
  ideal case would need its own pressure meaning, not a reinterpretation of `-002`.

## 5. Other sources found

| Source | What it prints | Why it is secondary |
|---|---|---|
| NTRS 19860007470, TDK engineering manual (NASA-CR-178628, SEA, April 1985), Table 7-3, printed p.7-58, PDF p.450 (rotated) | "Pratt and Whitney test engine for RL-10 OTV propulsion" (PDF p.445), input "from data provided by NASA MSFC": first solution Pc 394.3 psia, Tc 5815.918 R, MR 5.035244, EP 205.0338, same reactant enthalpies, HCHAM -464.2563 BTU/lb (the printed inputs give -464.264), ISP (ODE) 477.5184, ISP (ODF) 456.1371, ISP (ODK) 474.4465, ISP (TDK) 469.6459 s | Not a catalog configuration: an RL10 test engine at area ratio 205, where the catalog's RL10A-3-3 records 57 and RL10A-3-3A 61; same 1980s TDK code class |
| NTRS 19810008621, OTV advanced expander cycle engine point design study vol. 2 (NASA-CR-161638, Dec 1980), Table XXXIV, printed p.239, PDF p.251 | ASE, RL-10 and OTV columns. RL-10: 15K lbf, 400 psia, MR 6.4, area ratio 263, chamber enthalpy -411.5 Btu/lbm, ISP (ODE) 479.3 s, predicted 457.8 s, experimental 459.2 s (footnoted to P&W FR-6011, 1973) | The RL-10 column is a derivative-study engine, not a catalog configuration; the reactant inlet state is not printed, only a chamber enthalpy |
| NTRS 19910014933, Wang, "Prediction of the Thrust Performance and the Flowfield of Liquid Rocket Engines" (1990) | SSME 100% power level inputs, including inlet temperatures 90.56 K and 20.56 K, Pc 2935.7 psia, Tc 3639.0 K, area ratio 77.5 (from the text layer) | Its Isp values are two-dimensional (FDNS, TDK), not one-dimensional ideal values |
| NTRS 19930019839, Nickerson, "Additional support for the TDK/MABL computer program" (SN-130, 1993) | TDK/MABL cases including a 650K STME | Unbuilt engine |
| NTRS 19870010946 (NASA-TM-89814), NTRS 19870015990 (NASA-TP-2725), NTRS 19990051032 (NASA/TP-1999-208522) | Theoretical and analytical Isp for a hypothetical engine and for NASA Lewis high-area-ratio test nozzles | Not catalog engines |
| NTRS 19980228039, Gordon, "Theoretical Performance of Liquid Hydrogen with Liquid Oxygen as a Rocket Propellant" (NASA-MEMO-5-21-59E, 1959) | Shifting and frozen propellant tables | A propellant study, not an engine |
| NTRS 19760007104, Bell Aerospace OME reusable thrust chamber program (1976) | Describes using JANNAF ODE and ODK inside its ADEPT parametric program | No engine-specific ideal value printed |
| NTRS 19740027082, P&W FR-6011 "Design Study of RL10 Derivatives" vol. 2 (1973) | RL10A-3-3 is mentioned as the baseline | The OCR text layer shows no ODE table; a page-image read was not done |

The remaining downloads (NTRS 19680003903, 19700025293, 19710000538, 19720019047, 19740010285, 19770009165,
19770078415, 19800008878, 19810021639, 19840004180, 19840011401, 19850010707, 19850011050, 19860019159,
19890012381, 19890014148, 19940019971, 19940030418, 19950002750, 19950017370) print no engine-specific ideal
value with its inlet state, or describe programs and methods only.

## 6. Search record

- NTRS citation API (`https://ntrs.nasa.gov/api/citations/search`), three query sets: 20 long topic queries,
  then short queries (long ones returned 0 results), then TDK and JANNAF program queries and engine names
  (SSME, RL10, J-2, F-1, H-1, OME/OMS, AJ10/SPS, Titan LR87, RS-27, Atlas MA-5, RS-68, J-2X, RD-180).
  1027 unique records in the two saved result files.
- 31 PDFs downloaded with the client name "RocketForge-research/1.0", text-extracted, and scanned for
  theoretical-performance words. Every value in §3 and in the first two rows of §5 was read from a rendered
  page image; the NTRS 19910014933 values come from the text layer.
- Not found: an ideal Isp with its inlet state for J-2, J-2S, F-1, H-1, RS-68, RL10A-3-3, RL10B-2 or any
  other catalog configuration besides `CFG-RS25-SMALL-THROAT`; and any engine source that prints values from
  current CEA, which is what a `NASA_PUBLISHED` verdict would need. "Not found" means not found by these
  queries, not that no such document exists.

## 7. Owner decisions this would need

None is made here.

1. **Classification.** `INDEPENDENT_CODE` (recommended, by the `rp1311_historical.py` precedent: no verdict)
   or `NASA_PUBLISHED` (a verdict at printed precision, which §3.7 shows the source cannot support).
2. **Whether to record it at all, and where.** A comparison-layer `ReferenceCase`, like
   `rp1311_historical.py`, needs a quantity key for Isp and fields for the expansion model and area ratio:
   today its keys are thermochemistry only (DB-4A §6). Engine evidence would need new qualifiers instead
   (performance basis IDEAL, expansion model, reactant enthalpy or temperature), which is a schema change.
3. **Which quantities.** Chamber temperature only (the one like-for-like quantity), or also ISP (ODE) and
   ISP (ODF).
4. **Which RocketForge path.** The runtime constant-gamma Isp (both gamma bases, as DB-4B reports), CEA's own
   rocket problem through the oracle, or both, shown separately.
5. **The ideal case's chamber pressure.** Its own meaning (stagnation pressure, model input) rather than the
   engine assertion `-002`.

Whatever is decided, the comparison rules and tolerances must be fixed before any RocketForge or CEA value is
computed against these numbers, and none may change in response to a result.
