# r2_schem — Round 2: flow-schematic index + modern anchors

## Access and budget
- WebSearch only (WebFetch/curl blocked per ROUND2.md, not retried). **34 of 38** searches used.
- Every source has `access: search_result_only`. No figure was viewed. A schematic is `described_in_text` only when the search summary quotes a caption, legend or figure reference; otherwise it is `cited_by_other_source`.
- Raw per-search notes: `searchlog.txt` (S1–S34; S33–S34 logged below).
- Builder scripts: `scratchpad/r2_schem_scripts/*.py`.

## Part 1 — Flow-schematic index (schematics.json, 42 entries)

### Best-located figures (document + figure number known)
| Engine | Source | Locator | Notes |
|---|---|---|---|
| RS-25 / SSME | AIAA 97-2687, Bradley 1997 (NTRS 19970028362) | **Fig. 1**, legend 97PD-038-001 | Legend names OPOV, FPOV, MFV, MOV, CCV. The companion AIAA 97-2685 (NTRS 19970028361) reuses the figure. |
| RS-25 | enginehistory "SSME Part 1" | **Fig. 3**, Photo No. **LC86C-4-1315** | The photo number lets the original be traced. |
| RS-25 | JSC-19041 SSME Overview (2003, ibiblio) | **Fig. 1.1-II** (flow schematic), **Fig. 1.1-III** (components) | Best government-origin candidate. |
| RL10 (all models / A-3-3A) | NTRS 19950022693 | **Figure 1** (full expander cycle) | Points to an RL10A-3-3A Modeling Project Final Report (not found). |
| RD-170 | Lioi, Ku & Yang, JPP 2018, DOI 10.2514/1.B36878 | **Fig. 1** | RESTRICTED_REFERENCE. |
| Apollo SPS (AJ10-137) | NASA Apollo liquid-propulsion overview | **Fig. 22, p. 31** (pressurization and propellant system) | The document's NTRS id is unresolved. |

### Documents that probably contain a schematic (figure number not seen)
- **H-1:** Chrysler SDES-64-414, Saturn I FSD Vol. VIII (NTRS 19650013471). The title includes "mechanical schematics". This is the strongest H-1 lead; it covers Saturn I, not IB.
- **F-1 / J-2:** Saturn V Flight Manual SA-507 (history.nasa.gov). Text-only flow descriptions are on enginehistory RPE08.12 (F-1) and RPE08.22 (J-2):
  - J-2 has series turbines: GG → fuel turbine → LOX turbine → nozzle.
  - F-1 routes turbine exhaust → heat exchanger → manifold → double-wall extension to 16:1.
  - The F-1 Familiarization manual R-3896 was not found.
- **LMDE / APS:** Apollo Experience Reports (NTRS 19730011150 and 19730010173), plus the Apollo 10 APS (TRW) and DPS flight evaluations.
- **Shuttle OMS:** OMS Workbook 21002 Rev A (2006), JSC-19950 OMS 2102 (1995), JSC 10588, JSC-11174 Systems Handbook, and the JSC-CN-7650 presentation. All are on ibiblio.
- **IPD:** DTIC ADA397910 ("IPD: Full Flow Cycle Development") and ADA430218 (briefing).
- **J-2S:** AEDC DTIC AD0867628 and AD0874400 (marked ITAR), and NTRS 19940016798 (1994 restart study). No CR schematic was found.
- **LE-9 / LE-7A / LE-X:**
  - JAXA repository AA1740298002.
  - IAC-16-C4.1 #35064 (manuscript restricted).
  - MHI Technical Review "Development of the LE-X Engine" (cited by Wikipedia).
  - A Teikyo page carries a JAXA-credited comparison figure.
- **A4:** the v2rocket.com engine-systems diagram (Tier E, provenance unknown). NASM text describes the steam-generator drive path.

### Searched, nothing locatable
- RS-68 / RS-68A: no flow schematic. The NAS 2006 Appendix D gives only an 11-component list.
- LR87/LR91: no HAER drawing found. The Library of Congress HAER collection is the lead.
- NK-33/AJ26, Vulcain 2 and RD-0120: Wikipedia-level text only. For Vulcain, the Winterfeldt/Laumert paper is cited.
- Merlin, Raptor and BE-4: no schematic from any manufacturer. [BG] None is expected to exist publicly.
- Rutherford: only the Rocket Lab battery-jettison patent (US 11,408,373 / 12,006,894) has figures.

### US patents (PUBLIC_DOMAIN_GOV class, figures not viewed)
- US 6,832,471 (Aerojet, staged expander)
- US 7,900,436 (GG-augmented expander)
- US 4,589,253 (pre-regenerated staged combustion)
- US 11,149,691 family (integrated TPU/preburner)
- US 8,250,853: its background text describes the RL10's gear-driven LOX pump and bootstrap start.

**No Rockwell, Rocketdyne or P&W SSME/RL10 patent was found.** A targeted assignee search in USPTO is still needed.

## Part 2 — Modern anchors (anchors/, 9 files)
| Anchor | New in round 2 | Status |
|---|---|---|
| RS-68A | L3Harris data sheet: 705K lbf SL / 800K vac, 1580 psia, 411/362 s, MR 5.97, ε 21.5, first test Sep 2008, certification Apr 2011, first flight Jun 2012 | REPORTED, medium |
| RS-68A | NASA presentation (NTRS 20090028723, identity uncertain): helium spin-start duct redesigned; ablative nozzle given increased duration; turbine seals cut helium use | REPORTED, low–medium |
| RS-68A | Roll control by vectored turbine exhaust | SECONDARY_CLAIM (NAS, baseline RS-68) |
| R-4D-11 | L3Harris 2024 spec sheet: 378–511 N; 315.5 s at 300:1 and 311 s at 164:1; 4.31 kg | REPORTED |
| R-4D-11 | 490 N nominal (IAC-10) | REPORTED |
| Merlin 1D | FUG 2025: GG cycle, 845 kN / 190,000 lbf, 9 / 27 engines | REPORTED |
| Merlin 1D | Pintle, TEA-TEB, 36,000 rpm, 9.7 MPa | SECONDARY_CLAIM only |
| Raptor 3 (new anchor) | spacex.com: 250 tf / 551 klbf, 1,525 kg (from 1,630 kg), RVac 275 tf; 1.3 m × 2.9 m | REPORTED |
| Raptor 3 | Pc, preburners | SECONDARY_CLAIM only |
| Raptor 2 | Wikipedia-level FFSC, MR 3.6, 330 bar added | SECONDARY_CLAIM |
| BE-4 | ULA fact sheet: 550,000 lbf, ORSC, LNG lets autogenous pressurization | REPORTED |
| BE-4 | Blue Origin: 640,000 lbf | REPORTED |
| BE-4 | Single preburner and single turbine | SECONDARY_CLAIM |
| BE-4 | Boost pumps | NOT found |
| Rutherford | Rocket Lab: BLDC + LiPo; all primary parts 3D printed; ~35 kg | REPORTED (attribution caveats) |
| Rutherford | ~50 hp per motor | SECONDARY_CLAIM (2015 press) |
| Rutherford | rpm, Pc, cooling | NOT found |
| IPD | DTIC: 1,112,000 N (250,000 lbf) SL, full-flow | REPORTED |
| IPD | USAF: FPB → fuel TP, OPB → ox TP; mainstage July 2006; 21/26 tests, 300 s | REPORTED |
| IPD | DTIC: hydrostatic bearings in the ox TP | REPORTED |
| IPD | Pc | NOT found |

## Conflicts (conflicts.json, 15)
**Unresolved:**
- RS-68A Pc: 1580 psia on the data sheet vs 1,488 psi on Wikipedia.
- Raptor 3 thrust: SpaceX gives 250 tf; secondary sources claim 280 tf.
- Raptor and BE-4 Pc drift.
- Merlin Pc and throttle range.
- A4 propellant masses.
- RD-170 turbine power (secondary).

**Resolved as dated uprates or rounding:** BE-4 550→640 klbf, Rutherford Vacuum 24→26 kN, Merlin 854 kN vs 845 kN (typo), IPD N/lbf.

## Schema breakers found this round
- A data sheet with an **unlabelled second operating column** (RS-68A).
- **Nozzle configuration as a variant dimension** under one designation (R-4D-11 at 164:1 vs 300:1).
- **Thrust given as a range** (R-4D-11).
- **Turbine exhaust with a control function** (RS-68 roll control).
- **Helium spin-start / helium budget** that spans engine, vehicle and ground.
- **Jettisoned battery packs** change the energy-source mass during a burn.
- **Vehicle-level mass savings** quoted together with engine mass (Raptor 3).
- Manufacturer **engine docs that justify propellants by vehicle pressurization** (BE-4 LNG autogenous).

## ID / merge issues
- Rutherford appears as both `ENG-US-RUTHERFORD` and `ENG-NZ-RUTHERFORD` across round-1 branches.
- RD-170, NK-33 and RD-0120 have both `ENG-SU-*` and `ENG-RU-*` ids. Schematic entries list both where relevant.
- Vulcain 2 has both `ENG-EU-` and `ENG-FR-` ids.

## Extra searches logged
- S33 (IPD): DTIC ADA430218 hydrostatic bearings; Flightglobal 1,110 kN.
- S34 (AIAA 97-2687): title and authors confirmed; Fig. 1 legend; inlet ranges.

## Priority fetches for a session with document access
1. NTRS 19970028362, Fig. 1.
2. ibiblio JSC-19041, Fig. 1.1-II.
3. NTRS 19650013471, H-1 schematics.
4. SA-507 flight manual, F-1/J-2 figures.
5. NTRS 19950022693, Fig. 1.
6. OMS 21002.
7. DTIC ADA397910.
8. L3Harris RS-68A sheet: interpret its second column.
9. NTRS 20090028723: confirm its identity.
