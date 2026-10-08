# DB-0 — Anchor engine corpus

> **DB-0.5 update (2026-10-08).** The anchors below are the DB-0 search-summary record and are kept unchanged.
> Opened-source evidence now exists for RS-25 (Block II and Block IIA), J-2, J-2S, F-1, H-1 (188K), RL10A-3-3A,
> RL10A-4-2, RL10B-2, Apollo SPS, LMDE, OMS, IPD and RD-170: 250 assertions with page locators in
> [db05/assertions.json](db05/assertions.json), and the disposition of 172 DB-0 anchor assertions (confirmed,
> corrected, unsupported, blocked) in [db05/db0_dispositions.json](db05/db0_dispositions.json). Several DB-0
> values belong to a different configuration than the anchor (see [db05/STATUS.md](db05/STATUS.md)).

The anchor corpus is the set of engine variants audited **deeply** — every
field group of the brief's Phase 4, a topology graph, operating points, and the
features that break a simple schema. Anchors were chosen for architectural
diversity, not fame, and to cover every taxonomy category that has hardware.

**Evidence limit.** Every assertion below was read from a web-search summary.
No PDF, datasheet or figure was opened, so no anchor reaches
"regression-grade". Where a summary attributed a number to a named Tier A/B
document (an NTRS report, a manufacturer datasheet, an agency page), the
assertion is `REPORTED` with that source; otherwise it is `SECONDARY_CLAIM`.
Topology nodes and edges carry their own evidence status; almost all are
`REPORTED_IN_TEXT` or `INFERRED`, because no schematic was viewed.

## Selection against the brief's architecture checklist

| Brief category | Anchors |
| --- | --- |
| Pressure-fed, storable spacecraft engine | AJ10-190 (Shuttle OMS), R-4D-11 |
| Pressure-fed launch / lander engine; regulated system | AJ10-137 (Apollo SPS, redundant regulators), LMDE (deep throttling) |
| Blowdown | **no engine-level anchor** — blowdown is a spacecraft-system mode (taxonomy §A.2) |
| Gas generator, LOX/RP-1 | F-1 (exhaust into nozzle extension), H-1 (geared turbopump), Merlin 1D, KRE-075 |
| Gas generator, LOX/LH2 | J-2 (turbines in series, start tank), RS-68A, Vulcain 2 (exhaust re-injected into nozzle), YF-77, CE-20 (turbines in series), HM7B |
| Gas generator, storable | LR87-AJ-5 (two chambers, two turbopumps, solid start cartridge, autogenous/GG-gas pressurization), Viking 5C, Vikas |
| Expander (closed) | RL10A-4-2, RL10B-2 (extendible carbon-carbon nozzle), Vinci |
| Expander bleed | LE-5B, LE-5B-2, LE-9 (first large expander-bleed booster engine) |
| Fuel-rich staged combustion | RS-25D (two preburners, four turbopumps, hydraulic LPOTP turbine), RD-0120, LE-7A, CE-7.5 |
| Oxidizer-rich staged combustion | RD-170 (two preburners → one turbine → four chambers), RD-171M, RD-180, NK-33, RD-0124 (four chambers), YF-100, BE-4 |
| Full-flow staged combustion | RD-270 (historical, ground test), IPD (powerhead demonstrator), Raptor 2, Raptor 3 |
| Electric pump | Rutherford, Rutherford Vacuum |
| Tap-off | J-2S, BE-3PM |
| Open expander (manufacturer wording) | BE-3U |
| Historical / third-fluid turbine drive | A4 (H2O2 + Z-Stoff steam generator, 18 pots), RD-107A and RD-108A (H2O2 drive, verniers, nitrogen pressurization hardware on the engine) |
| Modern methane, several independent families | Raptor 2/3, BE-4 (YF-209, TQ-12, Aeon, Prometheus/MR10 are in the master list but not anchored) |
| Multi-chamber on one turbopump | RD-170, RD-171M, RD-180, RD-0124, RD-107A, RD-108A; LR87 (two chambers but two turbopumps — a deliberate counter-example) |

## Strongest sources found per anchor family (all seen in search summaries only)

- **RS-25D:** Hopson STS-104 flight readiness review (2001) Block I/IIA/II
  table; L3Harris RS-25 sheet (2,994 psia, MR 6.03, ε 69, 512,300 lbf at
  109 %); 1986 NASA "large throat" study (ε 77.5 → 69.5); NTRS 20030005845.
- **J-2 / J-2S:** NTRS 20100027318 (MR 5.5 / 4.5, GG with turbines in series,
  start tank with internal He tank, ε 27.5, "a little over 700 psia"); AEDC
  test reports TR-70-150, -204, -38 and study D5-15772-2 for J-2S.
- **F-1:** MSFC material (5,500 rpm, 55,000 bhp; exhaust heat exchanger →
  manifold → extension film cooling from ε 10 to 16; TEB/TEA hypergol
  cartridge); Rocketdyne R-3896-1 is the Engine Data volume.
- **H-1:** NTRS 19650013470 (188 k rating; ~32,000 rpm turbine, gear reduction
  to ~6,537 rpm pumps). OCR-garbled; identity medium.
- **RL10:** L3Harris sheets; National Academies report (B-2 Pc disagreeing
  within one report); NTRS 19910018888 (RL10A-3-3A — a different variant, kept
  separate).
- **RD-170:** NTRS 19910018906 (1989 Paris Air Show slides): "1 turbopump
  assembly driven by 2 preburners which feed 4 thrust chamber assemblies",
  740 / 806 t, 308 / 336 s, 250 kgf/cm², MR 2.58. This settles the
  one-vs-two preburner question that round 1 left open.
- **RD-0120:** JAXA summary of an AIAA paper (210 kgf/cm² at 100 %, MR 6,
  preburner 398 kgf/cm² and MR 0.8, 190 t / 200 t at 100 / 106 %).
- **NK-33 / AJ26:** Aerojet deck hosted by the National Academies (2,109 psi,
  338 / 377 klbf, 297 / 331 s, chamber MR 2.6); NASA Orb-3 review (AJ26 E15 LOX
  turbopump).
- **RD-180:** ULA-hosted paper "RD-180 Engine: An Established Record of
  Performance and Reliability on Atlas Launch Vehicles" (seen as a URL);
  Glavkosmos export data.
- **LE-7A:** 1997 MEXT/NASDA committee material (LE-7A vs LE-7 turbopump
  speeds and preburner gas temperature).
- **LE-9:** IHI Technical Review 57(3); IAC-16/17/18/19 papers; MHI TR 55-2.
- **Vulcain 2:** ESA "Ariane 5 ECA – new elements"; ESA V157 inquiry; CNES
  (1,390 kN vacuum); LOX turbopump 13,000 rpm / 161 bar (Vulcain 2-specific).
- **RS-68A:** L3Harris datasheet (705 / 800 klbf, 1,580 psia, 411 / 362 s, MR
  5.97, ε 21.5); NASA presentation on the helium spin-start duct redesign.
- **KRE-075:** KARI 2009 design targets; impulse turbine with 12 nozzles; GG
  ~4 % of flow, exhaust through a heat exchanger and a duct giving ~1 % thrust.
- **IPD:** DTIC / USAF releases (1,112,000 N; one turbopump per preburner;
  hydrostatic bearings; full power July 2006).
- **Rutherford:** Rocket Lab pages and payload user's guide (electric pumps,
  brushless DC motors, Li-polymer batteries, printed primary components).
- **Raptor / BE-4 / BE-3 / Merlin:** company pages and user's guides only;
  internal operating data are proprietary and genuinely not public.

## Coverage matrix (as judged by the auditing branch)

W = well documented, P = partial, w = weak, – = not found in the summaries searched (not a claim that it is unpublished), · = not audited. All judgements rest on search summaries.

| Anchor | Assertions | Nodes/edges | id | prop | perf | tca | noz | inj | cool | feed | pump | turb | gg/pb | press | start | ctrl | mech | mat | hist |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-100 | 20 | 8/9 | W | P | P | – | – | – | – | P | w | – | w | – | w | – | – | – | P |
| ENG-CN-YF-77 | 22 | 4/4 | W | P | P | – | – | – | – | – | w | – | w | – | – | w | – | – | P |
| ENG-DE-A4-ENGINE | 18 | 10/10 | P | P | w | – | – | P | P | – | w | w | P | – | – | w | – | – | w |
| ENG-FR-HM7B | 12 | 3/0 | W | – | P | – | – | – | w | – | – | – | w | – | – | – | – | – | – |
| ENG-FR-VIKING-5C | 11 | 6/4 | W | W | w | – | – | – | – | – | w | – | w | – | – | – | – | – | w |
| ENG-FR-VINCI | 10 | 4/3 | W | P | P | – | w | – | – | – | w | – | – | – | – | – | w | – | w |
| ENG-FR-VULCAIN-2 | 34 | 7/6 | W | P | P | – | P | – | w | – | P | – | w | – | – | – | – | w | P |
| ENG-IN-CE-20 | 13 | 7/7 | W | P | P | – | – | – | – | – | w | w | P | – | – | – | w | – | – |
| ENG-IN-CE-7-5 | 12 | 6/1 | W | w | P | – | – | – | – | – | – | – | w | – | – | P | – | – | – |
| ENG-IN-VIKAS | 18 | 4/4 | W | W | P | – | – | – | – | – | w | – | w | – | – | – | – | – | P |
| ENG-JP-LE-5B | 16 | 7/6 | W | P | P | – | – | – | w | – | P | – | – | – | – | P | P | – | – |
| ENG-JP-LE-5B-2 | 13 | 7/5 | W | – | P | – | – | P | w | w | – | – | – | – | – | P | w | – | w |
| ENG-JP-LE-7A | 25 | 7/9 | W | W | P | – | – | – | – | – | P | – | P | – | – | w | – | – | w |
| ENG-JP-LE-9 | 23 | 8/6 | W | P | P | w | – | – | – | – | w | – | – | – | – | w | w | w | P |
| ENG-KR-KRE-075 | 24 | 8/8 | W | W | P | – | – | w | – | – | – | w | w | – | – | w | – | – | w |
| ENG-NZ-RUTHERFORD | 14 | 6/4 | – | – | w | – | – | – | – | P | w | – | – | – | – | – | w | P | – |
| ENG-NZ-RUTHERFORD-VACUUM | 6 | 0/0 | – | – | w | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| ENG-RU-RD-0124 | 13 | 6/5 | P | – | P | w | – | – | w | – | – | – | w | – | – | w | – | – | w |
| ENG-RU-RD-171M | 15 | 0/0 | P | – | W | w | – | – | – | – | – | – | – | – | – | – | P | – | – |
| ENG-RU-RD-180 | 29 | 3/2 | P | P | P | w | w | – | – | – | – | – | – | – | – | w | P | – | – |
| ENG-SU-NK-33 | 17 | 5/3 | P | – | P | – | – | – | w | – | w | – | w | – | – | – | – | – | w |
| ENG-SU-RD-0120 | 14 | 7/5 | P | P | P | – | – | w | – | – | w | – | P | – | – | – | – | – | w |
| ENG-SU-RD-107A | 17 | 13/12 | P | P | P | w | – | – | – | w | – | w | w | w | w | w | – | – | – |
| ENG-SU-RD-108A | 14 | 15/14 | P | P | P | w | – | – | – | w | – | w | w | w | w | w | – | – | – |
| ENG-SU-RD-170 | 26 | 13/16 | P | P | P | w | – | – | w | P | P | w | P | – | w | – | – | – | w |
| ENG-SU-RD-270 | 12 | 7/8 | P | P | P | – | – | – | – | – | – | – | P | – | – | – | – | – | w |
| ENG-US-AJ10-137 | 5 | 7/7 | P | – | – | – | – | – | – | – | – | – | – | w | – | w | – | – | – |
| ENG-US-AJ10-190 | 2 | 7/7 | w | – | – | – | – | – | – | – | – | – | – | w | – | w | – | – | – |
| ENG-US-BE-3PM | 4 | 0/0 | – | – | w | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| ENG-US-BE-3U | 6 | 0/0 | – | – | w | – | – | – | – | – | – | – | – | – | – | – | – | – | – |
| ENG-US-BE-4 | 17 | 5/4 | P | P | w | – | – | – | – | – | – | w | w | w | – | – | – | – | – |
| ENG-US-F-1 | 34 | 10/13 | W | P | P | P | P | – | P | P | P | P | w | w | P | – | P | w | – |
| ENG-US-H-1 | 29 | 10/12 | P | w | P | – | w | – | – | w | P | P | w | – | P | – | P | w | – |
| ENG-US-IPD | 13 | 5/4 | P | – | w | – | – | – | – | – | w | – | P | – | – | – | – | – | P |
| ENG-US-J-2 | 50 | 16/16 | W | W | P | w | P | w | – | P | P | P | w | – | P | P | P | – | w |
| ENG-US-J-2S | 16 | 6/5 | P | w | P | – | – | w | – | w | w | w | – | – | – | w | w | – | P |
| ENG-US-LMDE | 5 | 5/5 | P | – | w | – | – | – | – | – | – | – | – | w | – | – | – | – | w |
| ENG-US-LR87-AJ-5 | 23 | 15/17 | P | P | P | w | w | – | w | P | w | w | w | P | P | – | w | – | – |
| ENG-US-MERLIN-1D | 17 | 6/3 | P | P | w | – | – | w | – | – | w | – | w | – | w | – | – | – | – |
| ENG-US-R-4D-11 | 10 | 2/0 | P | – | P | – | – | – | – | – | – | – | – | – | – | – | w | – | – |
| ENG-US-RAPTOR-2 | 8 | 0/0 | – | – | w | – | – | – | – | – | – | – | – | – | – | – | w | – | – |
| ENG-US-RAPTOR-3 | 9 | 0/0 | P | w | w | – | – | – | – | – | – | – | w | – | – | – | P | – | – |
| ENG-US-RL10A-4-2 | 17 | 11/12 | W | P | P | – | P | – | – | w | w | w | – | – | – | w | – | – | – |
| ENG-US-RL10B-2 | 22 | 4/1 | W | P | P | – | P | – | – | – | – | – | – | – | – | – | P | P | – |
| ENG-US-RS-68A | 23 | 9/4 | P | – | P | – | P | – | – | – | – | w | w | – | w | w | – | – | – |
| ENG-US-SSME-BLOCK-II | 62 | 25/32 | P | P | P | w | P | w | P | P | P | P | w | w | w | P | P | w | – |

## YF-100 — `ENG-CN-YF-100`

**Scope.** Original YF-100 (LM-5 boosters, LM-6/7/8 first stages). Excludes YF-100K/L/M (separate records). Some Chinese summaries may describe later production standards.

**Architecture (master list).** LOX / kerosene (RP-type); pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` rated, vacuum; `OP-2` rated, sea level

**Assertions:** 20 (SECONDARY_CLAIM 20). Full list in [data/anchors/ENG-CN-YF-100.json](data/anchors/ENG-CN-YF-100.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.pc | OP-1 | 18 | MPa | SECONDARY_CLAIM | SRC-WIKI-YF100 | 2,600 psi |
| performance.pc | OP-1 | 18 | MPa | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| performance.thrust_vac | OP-1 | 1340 | kN | SECONDARY_CLAIM | SRC-WIKI-YF100 |  |
| performance.thrust_vac | OP-1 | 1340.5 | kN | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| performance.thrust_sl | OP-2 | 1200 | kN | SECONDARY_CLAIM | SRC-WIKI-YF100 |  |
| performance.thrust_sl | OP-2 | 1188 | kN | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| performance.thrust_sl | OP-2 | 1000 kN design raised to 1200 kN | kN | SECONDARY_CLAIM | SRC-HUXIU-YF100 |  |
| performance.isp_sl | OP-2 | 299.9 | s | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| performance.isp_vac | OP-1 | 335.0 | s | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| propellants.mixture_ratio |  | 2.6 | - | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| nozzle.area_ratio |  | 35 | - | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |
| performance.throttle |  | 65%-105% | % | SECONDARY_CLAIM | SRC-WIKI-YF100 |  |
| performance.throttle |  | 65%-100% | % | SECONDARY_CLAIM | SRC-BILI-CV15113396 |  |

**Topology:** 8 nodes, 9 edges; evidence: REPORTED_IN_TEXT 10, INFERRED 7. Completeness: Partial; regen jacket, LOX booster drive, igniter, valves, gimbal position missing.

**Schema breakers:**
- All oxidizer passes through preburner: flow-fraction attribute on preburner feed edge (100%).
- Booster pump driven by a tapped kerosene stream - a hydraulic drive edge type distinct from turbine_drive by hot gas.
- Throttle range disagrees (65-100 vs 65-105%).
- Gimbal location (pump-before vs pump-after) differs across YF-100 derivatives - mechanical configuration per variant.

**Missing:** 5 field groups (NOT_REPORTED 4, UNKNOWN 1): pumps.*, preburners.pb1.temperature, preburners.pb1.mr, mechanical.gimbal_position, pumps.lox_booster.drive

## YF-77 — `ENG-CN-YF-77`

**Scope.** YF-77 LOX/LH2 core-stage engine of Long March 5/5B (two per stage). SL figures disagree between Wikipedia revisions.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (REPORTED); chambers: 1

**Operating points.** `OP-1` vacuum; `OP-2` sea level

**Assertions:** 22 (SECONDARY_CLAIM 17, REPORTED 5). Full list in [data/anchors/ENG-CN-YF-77.json](data/anchors/ENG-CN-YF-77.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.mixture_ratio | OP-1 | 5.5 | - | REPORTED | SRC-IAC13-17679 |  |
| propellants.mixture_ratio |  | 5.5 (adjustable) | - | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.thrust_vac | OP-1 | 700 | kN | REPORTED | SRC-IAC13-17679 |  |
| performance.thrust_vac | OP-1 | 700 | kN | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.thrust_sl | OP-2 | 518 | kN | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.thrust_sl | OP-2 | 510 | kN | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.pc |  | 10.1 | MPa | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.pc |  | 10.2 | MPa | SECONDARY_CLAIM | SRC-WIKI-YF77 | 1,480 psi |
| performance.isp_vac | OP-1 | 428.0 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.isp_vac | OP-1 | 430 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.isp_sl | OP-2 | 316.7 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.isp_sl | OP-2 | 310.2 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.burn_time |  | 525 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| performance.burn_time |  | 520 | s | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |
| turbines.arrangement |  | two separate turbopumps driven by one central gas generator | - | SECONDARY_CLAIM | SRC-WIKI-YF77 |  |

**Topology:** 4 nodes, 4 edges; evidence: REPORTED_IN_TEXT 6, INFERRED 2. Completeness: Skeleton. Missing: GG feed taps, exhaust, regen, valves.

**Schema breakers:**
- Two engines per stage with independent two-plane gimbal: TVC is per-engine.
- Adjustable mixture ratio: MR is a range/set-point, not a scalar.
- Wikipedia revisions disagree on SL thrust/Isp/pc/burn time - per-source assertions required.

**Missing:** 5 field groups (NOT_REPORTED 3, NOT_AUDITED 2): pumps.*.speed_rpm, gas_generator.*, nozzle.area_ratio, turbines.exhaust_destination, cooling.*

## A-4 (V-2) main engine — `ENG-DE-A4-ENGINE`

**Scope.** Production A-4/V-2 propulsion unit (1944-45). Thiel's 1.5 t development motor values are excluded except where marked.

**Architecture (master list).** LOX / ethanol-water (75% alcohol); pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 18 (SECONDARY_CLAIM 18). Full list in [data/anchors/ENG-DE-A4-ENGINE.json](data/anchors/ENG-DE-A4-ENGINE.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-NOM | 25 | metric tons (~56,000 lb) | SECONDARY_CLAIM | SRC-NASM-A19600013000 |  |
| propellants.oxidizer |  | LOX |  | SECONDARY_CLAIM | SRC-NASM-A19600013000 |  |
| propellants.fuel |  | 75% alcohol |  | SECONDARY_CLAIM | SRC-NASM-A19600013000 |  |
| turbines.T1.working_fluid |  | steam from H2O2 (T-Stoff) + Z-Stoff catalyst (27% sodium permanganate solution) |  | SECONDARY_CLAIM | SRC-NASM-A19600013000 |  |
| gg_preburner.SG1.h2o2_concentration |  | 85 | % | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE02-2 |  |
| gg_preburner.SG1.h2o2_concentration |  | 80 | % (test strength) | SECONDARY_CLAIM | SRC-V2ROCKETHISTORY |  |
| turbines.T1.power | OP-NOM | 580 | hp | SECONDARY_CLAIM | SRC-NMUSAF-V2 |  |
| pumps.shaft.speed | OP-NOM | 3800 | rpm (about) | SECONDARY_CLAIM | SRC-NMUSAF-V2 |  |
| performance.mdot_fuel | OP-NOM | 128 | lb/s | SECONDARY_CLAIM | SRC-NMUSAF-V2 |  |
| performance.mdot_ox | OP-NOM | 159 | lb/s | SECONDARY_CLAIM | SRC-NMUSAF-V2 |  |
| performance.propellant_consumed |  | 9,700 kg over 62 s |  | SECONDARY_CLAIM | SRC-NASM-A19600013000 |  |
| performance.propellant_consumed |  | 9,000 kg over 60 s |  | SECONDARY_CLAIM | SRC-NASM-A19790951000 |  |
| injector.prechambers |  | 18 | count ('pots', each ~1.5 t, feeding common mixing chamber) | SECONDARY_CLAIM | SRC-WIKI-THIEL |  |
| injector.prechambers_function |  | components swirled in 18 pre-chambers |  | SECONDARY_CLAIM | SRC-DEUTSCHESMUSEUM-A4 |  |
| cooling.method |  | regenerative (alcohol enters double wall at lower end, flows to injection head) + film co… |  | SECONDARY_CLAIM | SRC-DEUTSCHESMUSEUM-A4 |  |
| performance.pc_dev_motor |  | 15 | bar (1.5 t development motor; 50 bar desired) | SECONDARY_CLAIM | SRC-WIKI-THIEL | development motor, not production engine |

**Topology:** 10 nodes, 10 edges; evidence: REPORTED_IN_TEXT 12, INFERRED 8. Completeness: Missing: pressurization of T/Z-Stoff tanks, turbine exhaust, film-cooling ring, igniter, preliminary stage.

**Schema breakers:**
- Turbine working fluid generated from two separate consumables (H2O2 + liquid permanganate catalyst).
- Fuel composition is a concentration (75% alcohol); H2O2 concentration disputed (80/85%).
- Injector-level sub-chambers ('pots') each with a thrust rating, feeding one chamber.
- Development-motor Pc easily mistaken for production Pc.

**Missing:** 6 field groups (NOT_REPORTED 6): performance.pc, nozzle.*, pumps.discharge_p.*, pressurization.*, ignition_start.*, materials.*

## HM7B — `ENG-FR-HM7B`

**Scope.** HM7B; sources mix Ariane 1-4 third stage (H10) and Ariane 5 ESC-A applications - not separated.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (REPORTED); chambers: 1

**Operating points.** `OP-1` nominal vacuum (application unclear)

**Assertions:** 12 (SECONDARY_CLAIM 10, REPORTED 2). Full list in [data/anchors/ENG-FR-HM7B.json](data/anchors/ENG-FR-HM7B.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 67 | kN | REPORTED | SRC-CNES-A5-TECH |  |
| performance.thrust_vac | OP-1 | 62.2 | kN | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| performance.thrust_vac | OP-1 | 64.8 | kN | SECONDARY_CLAIM | SRC-SATNOW-HM7B |  |
| performance.isp_vac | OP-1 | 446 | s | SECONDARY_CLAIM | SRC-SATNOW-HM7B |  |
| performance.pc | OP-1 | 3.7 | MPa | SECONDARY_CLAIM | SRC-WIKI-HM7B |  |
| performance.pc_history |  | raised from 30 to 35 bar | bar | SECONDARY_CLAIM | SRC-WIKI-HM7B | which transition (HM7->HM7B?) not clear in snippet |
| performance.burn_time | OP-1 | 950 | s | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE | Ariane 5 ECA |
| performance.burn_time | OP-1 | up to 15 min 45 s | - | REPORTED | SRC-CNES-A5-TECH |  |
| performance.restarts |  | no restart capability | - | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| mechanical.mass_dry |  | 165 | kg | SECONDARY_CLAIM | SRC-SATNOW-HM7B |  |

**Topology:** 3 nodes, 0 edges; evidence: REPORTED_IN_TEXT 2, INFERRED 1. Completeness: Minimal; no turbopump evidence.

**Schema breakers:**
- Same designation flown on different stages with different burn times / possibly thrust values.

**Missing:** 13 field groups (NOT_AUDITED 13): pumps.*, thrust_chamber.*, injector.*, cooling.*, pumps.*, turbines.*, gas_generators.*, pressurization.*, ignition_start.*, control.*, mechanical.*, materials.*, history.*

## Viking 5C — `ENG-FR-VIKING-5C`

**Scope.** Viking 5C as used on Ariane 4 first stage (1990-2003). Same engine as europe branch record ENG-FR-VIKING-5C (ID convention conflict EU vs FR). Family-level values flagged.

**Architecture (master list).** N2O4 / UH 25; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` nominal (SL/vac not stated)

**Assertions:** 11 (SECONDARY_CLAIM 10, REPORTED 1). Full list in [data/anchors/ENG-FR-VIKING-5C.json](data/anchors/ENG-FR-VIKING-5C.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | N2O4 | - | SECONDARY_CLAIM | SRC-FRWIKI-VIKING |  |
| propellants.fuel |  | UH 25 (75% UDMH + 25% hydrazine); family also used UDMH | - | SECONDARY_CLAIM | SRC-WIKI-VIKING |  |
| propellants.fuel_change |  | UDMH -> UH 25 from Ariane 2 onward after combustion instability / explosion on Ariane 1 f… | - | SECONDARY_CLAIM | SRC-WIKI-UH25 |  |
| performance.pc | OP-1 | 58.5 | bar | SECONDARY_CLAIM | SRC-FRWIKI-VIKING |  |
| performance.pc | OP-1 | 5.5 | MPa | SECONDARY_CLAIM | SRC-WIKI-VIKING | not 5C-specific |
| performance.thrust | OP-1 | 760.7 | kN | SECONDARY_CLAIM | SRC-WIKI-VIKING | SL/vac unstated |
| nozzle.area_ratio |  | 10 | - | SECONDARY_CLAIM | SRC-WIKI-VIKING |  |

**Topology:** 6 nodes, 4 edges; evidence: INFERRED 6, REPORTED_IN_TEXT 4. Completeness: Very weak; destination and fluid of third pump unknown.

**Schema breakers:**
- Three pumps on one shaft, one of which carries a fluid that is neither main propellant (if water, a third working fluid) - schema needs >2 propellant/working-fluid roles.
- Fuel changed mid-life of the family (UDMH -> UH 25) under the same variant names.

**Missing:** 5 field groups (NOT_REPORTED 3, NOT_AUDITED 2): gas_generator.water_injection, pumps.third_pump.fluid, pumps.*.speed_rpm, propellants.mixture_ratio, performance.isp_*

## Vinci — `ENG-FR-VINCI`

**Scope.** Vinci as qualified for Ariane 6 ULPM (search sources did not distinguish development configurations).

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_closed (REPORTED); chambers: 1

**Operating points.** `OP-1` nominal vacuum (undefined by source)

**Assertions:** 10 (SECONDARY_CLAIM 6, REPORTED 4). Full list in [data/anchors/ENG-FR-VINCI.json](data/anchors/ENG-FR-VINCI.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.mixture_ratio | OP-1 | 6.1 | - | SECONDARY_CLAIM | SRC-WIKI-VINCI |  |
| performance.thrust_vac | OP-1 | 180 | kN | SECONDARY_CLAIM | SRC-WIKI-VINCI |  |
| performance.pc | OP-1 | 60 | bar | SECONDARY_CLAIM | SRC-WIKI-VINCI |  |
| performance.isp_vac | OP-1 | 457.2 | s | SECONDARY_CLAIM | SRC-WIKI-VINCI |  |
| nozzle.area_ratio |  | 240 | - | SECONDARY_CLAIM | SRC-WIKI-VINCI | deployed/stowed not stated |
| mechanical.mass_dry |  | ~550 | kg | SECONDARY_CLAIM | SRC-WIKI-VINCI | ~160 kg excluding nozzle |
| pumps.lh2_tp.discharge_p | OP-1 | >300 | bar | REPORTED | SRC-IAC-18-45921 | 'up to more than 300 bar' for hydrogen |

**Topology:** 4 nodes, 3 edges; evidence: INFERRED 4, REPORTED_IN_TEXT 3. Completeness: Skeleton; turbine arrangement, bypass/regulating valves, nozzle-extension cooling, igniter, pressurization tap-offs all missing.

**Schema breakers:**
- Extendable nozzle (per task prompt, unverified): area ratio depends on deployment state.
- Turbopump discharge pressure (>300 bar) is a per-pump value far above pc (60 bar).

**Missing:** 16 field groups (NOT_AUDITED 16): nozzle.extension_deployment, performance.restarts, ignition_start.*, identity.expander_closed_vs_bleed, thrust_chamber.*, injector.*, cooling.*, pumps.*, turbines.*, gas_generators.*, pressurization.*, ignition_start.*, control.*, mechanical.*, materials.*, history.*

## Vulcain 2 — `ENG-FR-VULCAIN-2`

**Scope.** Vulcain 2 as flown on Ariane 5 ECA/ES (2002-2023), incl. post-2002 redesigned nozzle. Excludes Vulcain (1) and Vulcain 2.1 (Ariane 6). Values from the Wikipedia/ESA 'Vulcain' pages whose variant is unclear (13,600/34,000 rpm, 235 kg/s) are NOT attached here (see CF-R2-VUL-1).

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` nominal, vacuum (as quoted by sources; not defined); `OP-2` nominal, sea level; `OP-3` LOX turbopump design point (press release)

**Assertions:** 34 (SECONDARY_CLAIM 26, REPORTED 8). Full list in [data/anchors/ENG-FR-VULCAIN-2.json](data/anchors/ENG-FR-VULCAIN-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX | - | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| propellants.fuel |  | LH2 | - | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| propellants.mixture_ratio | OP-1 | 6.1 | - | SECONDARY_CLAIM | SRC-WIKI-VULCAIN | engine vs chamber O/F convention not stated |
| propellants.mixture_ratio | OP-1 | 6.1 | - | SECONDARY_CLAIM | SRC-MECAIND-2020-T1 |  |
| performance.thrust_vac | OP-1 | 1390 | kN | REPORTED | SRC-CNES-A5-TECH | '1,390 kN (139 tonnes) ... in vacuum'; 20% gain over Vulcain |
| performance.thrust_vac | OP-1 | 1359 | kN | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| performance.thrust_vac | OP-1 | 1359 | kN | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| performance.thrust_vac | OP-1 | 1340 | kN | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| performance.thrust_sl | OP-2 | 960 | kN | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| performance.pc | OP-1 | 117.3 | bar | SECONDARY_CLAIM | SRC-WIKI-VULCAIN | abs/gauge, station not stated |
| performance.pc | OP-1 | 117.3 | bar | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| performance.pc | OP-1 | 115 | bar | SECONDARY_CLAIM | SRC-MECAIND-2020-T1 |  |
| performance.isp_vac | OP-1 | 429 | s | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| performance.isp_vac | OP-1 | 429 | s | SECONDARY_CLAIM | SRC-AIAA-VG-ARIANE |  |
| nozzle.area_ratio |  | 58.2 | - | SECONDARY_CLAIM | SRC-WIKI-VULCAIN |  |
| nozzle.area_ratio |  | 58.5 | - | SECONDARY_CLAIM | SRC-MECAIND-2020-T1 |  |
| nozzle.turbine_exhaust_reinjection |  | new nozzle allows exhaust from the turbopumps to be reinjected into the main system, impr… | - | REPORTED | SRC-ESA-A5ECA-NEWELEM | number of injection points / ducts not stated in seen text |
| pumps.lox_tp.manufacturer |  | Avio (Italy) | - | SECONDARY_CLAIM | SRC-CLASSICISTRANIERI-VULCAIN |  |
| pumps.lh2_tp.manufacturer |  | Snecma | - | SECONDARY_CLAIM | SRC-CLASSICISTRANIERI-VULCAIN |  |
| pumps.lox_tp.redesign |  | new oxygen turbopump vs Vulcain | - | REPORTED | SRC-ESA-A5ECA-NEWELEM | paraphrase |
| pumps.lox_tp.speed_rpm | OP-3 | 13000 | rpm | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD | explicitly the NEW (Vulcain 2) oxygen TP; originator of release not identified |
| pumps.lox_tp.discharge_p | OP-3 | 161 | bar | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD | 'to deliver a pressure of 161 bar' |
| pumps.lox_tp.manufacturer |  | Avio | - | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD |  |
| pumps.lh2_tp.manufacturer |  | Snecma (also prime contractor) | - | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD |  |
| turbines.manufacturer |  | Volvo Aero (later GKN): gas turbines powering the turbopumps, and the nozzle | - | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD | Wikipedia names GKN for the same scope |
| propellants.mixture_ratio_change |  | about 20% more LOX in the mixture than Vulcain (1); slightly higher pressure | - | SECONDARY_CLAIM | SRC-INNOV-VULCAIN2-PROD |  |
| nozzle.film_cooling |  | film cooling of lower part of nozzle by re-injected turbine exhaust gas | - | SECONDARY_CLAIM | SRC-WIKI-VULCAIN | consistent with ESA 'turbopump exhaust re-injected' (round-1); number of injection points not stated |
| cooling.nozzle_circuit |  | tube-wall nozzle with hydrogen cooling circuit (cooling tubes) | - | REPORTED | SRC-ESA-V157-INQUIRY |  |

**Topology:** 7 nodes, 6 edges; evidence: REPORTED_IN_TEXT 10, INFERRED 3. Completeness: Skeleton plus nozzle cooling circuit and film-injection node. Missing: tanks/feed lines, valves, GG feeds, chamber regen path, igniters/start, turbine series/parallel arrangement, which turbine exhausts are reinjected.

**Schema breakers:**
- Turbine exhaust is reinjected into the nozzle rather than dumped overboard: a flat 'cycle=GG' field hides where GG gas ends up (affects Isp accounting).
- Two separate turbopumps from different suppliers: per-pump manufacturer and data need a pump child table.
- Same family name 'Vulcain' spans Vulcain, Vulcain 2, Vulcain 2.1 with agency pages not always variant-labelled.
- Nozzle failure mode and redesign changed the flown hardware under the same designation (pre/post-2003 nozzle) - configuration revision needed.
- Nozzle-extension demonstrator hardware tested on the engine (Vulcain 2+ NE) - test-article configurations must not pollute flight values.

**Missing:** 19 field groups (NOT_AUDITED 14, NOT_REPORTED 3, UNKNOWN 2): pumps.lh2_tp.speed_rpm, performance.mdot_total, nozzle.extension_cooling, gas_generators.gg.*, thrust_chamber.*, injector.*, cooling.*, pumps.*, turbines.*, gas_generators.*, pressurization.*, ignition_start.*, control.*, mechanical.*, materials.*, history.*, pumps.lh2_tp.speed_rpm, gas_generator.gg1.mr, nozzle.extension_cooling_flight

## CE-20 — `ENG-IN-CE-20`

**Scope.** CE-20 LVM3 upper-stage engine (C25 and uprated C32). Thrust ratings 19 t / 20 t (Gaganyaan) / 22 t are qualified set-points of one design; not separate records.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` spec-table vacuum (186.36 kN); `OP-2` nominal 200 kN; `OP-3` uprated 22 t

**Assertions:** 13 (SECONDARY_CLAIM 13). Full list in [data/anchors/ENG-IN-CE-20.json](data/anchors/ENG-IN-CE-20.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| gas_generator.gg1.propellant_source |  | LOX and LH2 tapped from the respective pump outlets | - | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| turbines.arrangement |  | independent LH2 and LOX turbopumps operating in series mode | - | SECONDARY_CLAIM | SRC-WIKI-CE20 | interpreted as turbines in series on the GG gas path; order not stated |
| performance.thrust_vac | OP-1 | 186.36 | kN | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| performance.thrust_vac | OP-2 | 200 | kN | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| performance.throttle |  | 180-220 kN; can be set to any fixed value within range | kN | SECONDARY_CLAIM | SRC-WIKI-CE20 | set-point, not in-flight throttling |
| performance.thrust_vac | OP-3 | 19 t / 20 t / 22 t qualified levels | t | SECONDARY_CLAIM | SRC-IASGYAN-CE20 |  |
| performance.pc | OP-2 | 6 | MPa | SECONDARY_CLAIM | SRC-WIKI-CE20 | 870 psi |
| propellants.mixture_ratio | OP-2 | 5.05 | - | SECONDARY_CLAIM | SRC-WIKI-CE20 | convention not stated |
| performance.isp_vac |  | 442 | s | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| performance.thrust_to_weight |  | 34.7 | - | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| performance.burn_time |  | 640-800 | s | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |
| mechanical.mass_dry |  | 588 | kg | SECONDARY_CLAIM | SRC-WIKI-CE20 |  |

**Topology:** 7 nodes, 7 edges; evidence: REPORTED_IN_TEXT 9, INFERRED 5. Completeness: Series-turbine skeleton; order and exhaust handling unknown.

**Schema breakers:**
- Series turbine drive with independent turbopumps: edge order matters.
- Multiple qualified thrust set-points (19/20/22 t) for one designation; 'nominal' differs by mission.
- GG fed from pump outlets (bootstrap) vs from tanks - needs explicit tap-point.

**Missing:** 6 field groups (NOT_REPORTED 3, NOT_AUDITED 3): pumps.*.speed_rpm, gas_generator.gg1.mr, turbines.exhaust_destination, nozzle.area_ratio, cooling.*, ignition_start.*

## CE-7.5 — `ENG-IN-CE-7-5`

**Scope.** CE-7.5 main engine of the GSLV Mk II indigenous cryogenic upper stage (CUS). Two steering engines belong to the engine assembly per sources; recorded as nodes, not as separate performance.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` nominal, vacuum; `OP-2` GSLV D5 flight-demonstrated range

**Assertions:** 12 (SECONDARY_CLAIM 12). Full list in [data/anchors/ENG-IN-CE-7-5.json](data/anchors/ENG-IN-CE-7-5.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 73.55 | kN | SECONDARY_CLAIM | SRC-WIKI-CE75 | also given as 73.5 kN |
| performance.thrust_vac | OP-1 | 75 | kN | SECONDARY_CLAIM | SRC-WIKI-CE75 |  |
| performance.throttle | OP-2 | 73.55 to 82 kN demonstrated on GSLV Mk2 D5 | kN | SECONDARY_CLAIM | SRC-WIKI-CE75 |  |
| performance.pc | OP-1 | 5.8 / 7.5 | MPa | SECONDARY_CLAIM | SRC-WIKI-CE75 | two values without explanation (main chamber vs preburner? unknown) |
| performance.pc | OP-1 | 58 | bar | SECONDARY_CLAIM | SRC-SLIDESHARE-CRYO | 'nominal chamber pressure' |
| performance.isp_vac | OP-1 | 454 +/- 3 | s | SECONDARY_CLAIM | SRC-WIKI-CE75 | 4.452 +/- 0.029 km/s |
| performance.burn_time |  | 720 | s | SECONDARY_CLAIM | SRC-WIKI-CE75 | nominal |

**Topology:** 6 nodes, 1 edges; evidence: REPORTED_IN_TEXT 5, INFERRED 2. Completeness: Very incomplete: turbopumps, turbine arrangement, steering-engine feed and cooling all unknown.

**Schema breakers:**
- Main engine plus two gimballed steering engines delivered as one engine assembly: engine-vs-auxiliary thrust chamber relationship.
- Separate thrust and MR regulators: closed-loop control attributes.
- Two chamber-pressure figures in one infobox with no label.

**Missing:** 5 field groups (NOT_REPORTED 4, NOT_AUDITED 1): preburners.*, pumps.*, propellants.mixture_ratio, nozzle.area_ratio, steering_engines.feed_source

## Vikas — `ENG-IN-VIKAS`

**Scope.** Vikas family baseline as described by sources that do NOT separate Vikas-2 / -4 / -4B / -X / high-thrust (HTVE) / human-rated. Each assertion names its era/variant where the source does. Variant records exist separately in engines.json.

**Architecture (master list).** N2O4 / UDMH / UH25; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` pre-2001 standard (52.5 bar); `OP-2` 2001 uprated (58.5 bar); `OP-3` high-thrust version (62 bar); `OP-4` unspecified (infobox)

**Assertions:** 18 (SECONDARY_CLAIM 17, REPORTED 1). Full list in [data/anchors/ENG-IN-VIKAS.json](data/anchors/ENG-IN-VIKAS.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | N2O4 | - | SECONDARY_CLAIM | SRC-WIKI-VIKAS |  |
| propellants.fuel |  | UDMH (earlier) / UH25 (75% UDMH + 25% hydrazine hydrate, later variants) | - | SECONDARY_CLAIM | SRC-WIKI-VIKAS | one source says 'hydrazine hydrate', another 'N2H4' for the 25% |
| performance.pc | OP-1 | 52.5 | bar | SECONDARY_CLAIM | SRC-SPACENEWS-33640 | 'current version' as of 2001 |
| performance.pc | OP-2 | 58.5 | bar | SECONDARY_CLAIM | SRC-SPACENEWS-33640 | uprated version tested 2001 |
| performance.pc | OP-3 | 6.2 | MPa | SECONDARY_CLAIM | SRC-WIKI-VIKAS | 62 bar = high-thrust version per other text |
| performance.thrust | OP-1 | 725 | kN | SECONDARY_CLAIM | SRC-WIKI-VIKAS | 'original engine' maximum; SL/vac not stated |
| performance.thrust | OP-2 | 799 | kN | SECONDARY_CLAIM | SRC-VAJIRAM-VIKAS | PSLV version; SL/vac not stated |
| performance.thrust | OP-3 | 846 | kN | SECONDARY_CLAIM | SRC-VAJIRAM-VIKAS | GSLV GS2 high-thrust version |
| performance.thrust | OP-4 | 821 | kN | SECONDARY_CLAIM | SRC-WIKI-VIKAS | another revision gives 850 kN |
| performance.thrust | OP-4 | 850 | kN | SECONDARY_CLAIM | SRC-WIKI-VIKAS |  |
| performance.isp_vac | OP-4 | 293 | s | SECONDARY_CLAIM | SRC-WIKI-VIKAS | baseline per summary |
| performance.isp_sl | OP-4 | 262 | s | SECONDARY_CLAIM | SRC-WIKI-VIKAS |  |
| performance.restarts |  | restart demonstrated on ground (Propulsion Complex, Mahendragiri, reported Jan 2025) | - | SECONDARY_CLAIM | SRC-VISIONIAS-VIKAS-RESTART |  |

**Topology:** 4 nodes, 4 edges; evidence: REPORTED_IN_TEXT 6, INFERRED 2. Completeness: Generic GG skeleton only. Missing: third pump/water circuit (if any), exhaust duct, valves, cooling.

**Schema breakers:**
- Same designation spans several chamber-pressure eras (52.5 / 58.5 / 62 bar) and fuels (UDMH / UH25): variant-by-epoch keys needed.
- Engine is cross-vehicle (PSLV PS2, GSLV GS2, GSLV boosters, LVM3 L110) with different thrust ratings per vehicle.
- Human-rating is a qualification attribute of a variant, not a separate design necessarily.

**Missing:** 6 field groups (NOT_REPORTED 3, NOT_AUDITED 3): pumps.*, gas_generator.coolant_water, nozzle.area_ratio, propellants.mixture_ratio, cooling.*, mechanical.*

## LE-5B — `ENG-JP-LE-5B`

**Scope.** LE-5B as introduced on H-II F8 / H-IIA second stage. Excludes LE-5B-2 (H-IIB/H-IIA later) and LE-5B-3 (H3). Weblio (ja.wikipedia) comparison table values are assumed to be the LE-5B column but the exact page was not identified.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` 100% rated, vacuum; `OP-2` 60% throttle; `OP-3` 30% throttle; `OP-4` idle / tank-head (3% or 5%)

**Assertions:** 16 (SECONDARY_CLAIM 16). Full list in [data/anchors/ENG-JP-LE-5B.json](data/anchors/ENG-JP-LE-5B.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| cooling.design_change |  | combustion chamber cooling passages and materials altered for effective heat transfer to … | - | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| performance.thrust_vac | OP-1 | 137.2 | kN | SECONDARY_CLAIM | SRC-WEBLIO-LE5 | 14 tf |
| propellants.mixture_ratio | OP-1 | 5 | - | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| nozzle.area_ratio |  | 110 | - | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| performance.isp_vac | OP-1 | 447 | s | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| performance.isp_vac | OP-1 | 447 | s | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| performance.pc | OP-1 | 3.58 | MPa | SECONDARY_CLAIM | SRC-WEBLIO-LE5 | abs/gauge not stated |
| pumps.lh2_tp.speed_rpm | OP-1 | 52000 | min-1 | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| pumps.lox_tp.speed_rpm | OP-1 | 18000 | min-1 | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| mechanical.length |  | 2.79 | m | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| mechanical.mass_dry |  | 285 | kg | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| performance.restarts |  | re-re-ignition possible (再々着火まで可能; i.e. up to 3 ignitions) | - | SECONDARY_CLAIM | SRC-WEBLIO-LE5 | interpretation of 再々着火 = third ignition |
| performance.throttle |  | 60%, 30%, and 3% without driving the turbine (from LE-5B onward) | % | SECONDARY_CLAIM | SRC-WEBLIO-LE5 |  |
| performance.throttle | OP-4 | idle mode 5% | % | SECONDARY_CLAIM | SRC-WIKI-LE5 | conflicts with 3% (see conflicts) |

**Topology:** 7 nodes, 6 edges; evidence: INFERRED 7, REPORTED_IN_TEXT 6. Completeness: Skeleton. Missing: valves, LE-5 heritage start sequence, turbine count, bleed dump location.

**Schema breakers:**
- Tank-head idle mode where turbopumps are not driven: one engine operates in two feed modes (pump-fed and effectively pressure-fed).
- Bleed-heat source location (chamber-only vs chamber+nozzle) differentiates LE-5A from LE-5B though both are 'expander bleed'.
- Discrete throttle levels (60/30/3%) rather than a continuous range.

**Missing:** 6 field groups (NOT_REPORTED 5, NOT_AUDITED 1): injector.element_count, turbines.*, cooling.channel_count, turbines.exhaust_destination, ignition_start.*, pumps.*.discharge_p

## LE-5B-2 — `ENG-JP-LE-5B-2`

**Scope.** LE-5B-2 (H-IIB second stage from 2009; later H-IIA). Excludes LE-5B and LE-5B-3.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` 100%, vacuum; `OP-2` 3% tank-head idle

**Assertions:** 13 (SECONDARY_CLAIM 12, REPORTED 1). Full list in [data/anchors/ENG-JP-LE-5B-2.json](data/anchors/ENG-JP-LE-5B-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 144.9 | kN | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| performance.isp_vac | OP-1 | 447 | s | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| performance.pc | OP-1 | 3.78 | MPa | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| nozzle.area_ratio |  | 110 | - | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| propellants.mixture_ratio | OP-1 | 5 | - | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| mechanical.mass_dry |  | 290 | kg | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| performance.throttle |  | 60%, 30%, 3%* (*tank head pressure only) | % | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| injector.element_count |  | 306 | - | SECONDARY_CLAIM | SRC-WIKI-LE5 | smaller coaxial elements |
| injector.element_type |  | coaxial | - | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |
| cooling.manifold |  | flow-laminarizing plates in expander manifold | - | SECONDARY_CLAIM | SRC-WIKI-LE5 |  |

**Topology:** 7 nodes, 5 edges; evidence: INFERRED 9, REPORTED_IN_TEXT 3. Completeness: Mostly inferred; included because the GH2/LH2 mixer is a topology element a flat schema cannot hold.

**Schema breakers:**
- GH2/LH2 mixer in the fuel feed line: a mixing node merging two hydrogen states before injection.
- Upgrade motivated by vehicle vibration (a stage/vehicle requirement) - change rationale belongs to a lineage edge.

**Missing:** 3 field groups (NOT_REPORTED 3): pumps.*, turbines.*, feed.mixer.gh2_source

## LE-7A — `ENG-JP-LE-7A`

**Scope.** LE-7A first-stage engine of H-IIA / H-IIB (2001-2025). Short- and long-nozzle configurations are mixed in sources and labelled where known. MEXT/NASDA 1997 values are development-phase design specifications, not flight-acceptance data. Excludes LE-7 (H-II) except where explicitly contrasted.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; staged_combustion_fuel_rich (REPORTED); chambers: 1

**Operating points.** `OP-1` rated (design spec, 1997 SAC material); `OP-2` short nozzle, vacuum; `OP-3` long nozzle, vacuum; `OP-4` sea level, short nozzle; `OP-5` throttled 72 +/- 5 %

**Assertions:** 25 (SECONDARY_CLAIM 14, REPORTED 11). Full list in [data/anchors/ENG-JP-LE-7A.json](data/anchors/ENG-JP-LE-7A.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX | - | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| propellants.fuel |  | LH2 | - | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| propellants.mixture_ratio | OP-1 | 5.9 | - | REPORTED | SRC-MEXT-SAC-1997 | engine vs chamber convention not stated; LE-7 column gives 6.0 |
| propellants.mixture_ratio | OP-1 | 5.9 | - | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| performance.isp_vac | OP-1 | 441 | s | REPORTED | SRC-MEXT-SAC-1997 | design value 1997; nozzle not stated |
| performance.thrust_vac | OP-1 | 1.10 (unit illegible in OCR: '1.10 Ionf') | unknown (OCR) | REPORTED | SRC-MEXT-SAC-1997 | Unit garbled; plausibly ~110 tonf but NOT converted. Do not use as a number without reading the PDF. |
| performance.throttle |  | throttling capability yes; no mixture-ratio control (推力可変機能あり（混合比制御なし）) | - | REPORTED | SRC-MEXT-SAC-1997 |  |
| performance.throttle | OP-5 | 100% or 72 +/- 5% | % | SECONDARY_CLAIM | SRC-AIAA-VG-H2A |  |
| performance.thrust_vac | OP-2 | 1074 | kN | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| performance.isp_vac | OP-2 | 429 | s | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| performance.thrust_vac | OP-3 | 1098 | kN | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| performance.isp_vac | OP-3 | 442 | s | SECONDARY_CLAIM | SRC-WIKI-LE7 |  |
| performance.thrust_vac |  | 112 | ton (tf) | REPORTED | SRC-MHI-LE7A | nozzle version not stated |
| performance.isp_vac |  | 440 | s | REPORTED | SRC-MHI-LE7A | nozzle version not stated |
| performance.thrust_sl | OP-4 | 843 | kN | SECONDARY_CLAIM | SRC-AIAA-VG-H2A | short nozzle |
| performance.pc |  | 121 | bar | SECONDARY_CLAIM | SRC-AIAA-VG-H2A | abs/gauge and station not stated |
| performance.pc |  | 12.0 | MPa | SECONDARY_CLAIM | SRC-WIKI-LE7 | No Tier A LE-7A pc found in round 2; the 12.7 MPa figure in mirrors belongs to LE-7 |
| pumps.lh2_tp.speed_rpm | OP-1 | 41200 | rpm | REPORTED | SRC-MEXT-SAC-1997 | LE-7 column: 42,200 rpm |
| pumps.lox_tp.speed_rpm | OP-1 | 18050 | rpm | REPORTED | SRC-MEXT-SAC-1997 | LE-7 column: 18,100 rpm |
| preburners.pb1.gas_temperature | OP-1 | 740 | K | REPORTED | SRC-MEXT-SAC-1997 | LE-7 column 840 K. Agrees qualitatively with round-1 Wikipedia note that LE-7A runs a reduced preburner temperature. |
| preburners.pb1.rich_side |  | fuel (hydrogen)-rich | - | SECONDARY_CLAIM | SRC-WEBLIO-LE7 |  |
| pumps.lh2_tp.internal_line_condition |  | about 28 MPa, about 46 K (rated operation), piping inside LH2 turbopump | MPa, K | REPORTED | SRC-MEXT-SAC-1997 | Piping condition, not a pump discharge spec. Which 1997 PDF and whether it concerns LE-7A or LE-7 is uncertain. |

**Topology:** 7 nodes, 9 edges; evidence: REPORTED_IN_TEXT 12, INFERRED 4. Completeness: Skeleton. Missing: regen jacket/nozzle cooling path, fuel split between MCC and preburner, valves (MFV/MOV/PBOV...), igniters, booster pumps (if any), turbine series/parallel arrangement, tanks.

**Schema breakers:**
- Design-spec (1997) vs flight values for the same designation: needs a value-provenance/epoch attribute, not just a number.
- Two nozzle configurations (short/long) share one designation and produce different thrust/Isp: configuration must be a sub-key of operating point.
- Preburner gas temperature is a variant-distinguishing parameter (LE-7 840 K vs LE-7A 740 K) - needs a preburner child table.
- Throttle capability WITHOUT mixture-ratio control - control capability needs separate booleans for thrust and MR.
- Turbine drive split (series vs parallel) is a topology fact absent from a flat 'cycle' column.

**Missing:** 11 field groups (NOT_AUDITED 6, NOT_REPORTED 5): performance.pc, thrust_chamber.*, nozzle.area_ratio, injector.*, cooling.*, preburners.pb1.pressure, preburners.pb1.mr, turbines.*, pumps.*.discharge_p, ignition_start.*, mechanical.mass_dry

## LE-9 — `ENG-JP-LE-9`

**Scope.** LE-9 first-stage engine of H3 (flown from 2023). Type 1 / Type 1A / Type 2 build standards reported in Japanese press were NOT separated here. Dev-era archived values (1,448 kN / 12.4 MPa / 432 s) are recorded only as superseded.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` rated, vacuum

**Assertions:** 23 (SECONDARY_CLAIM 14, REPORTED 9). Full list in [data/anchors/ENG-JP-LE-9.json](data/anchors/ENG-JP-LE-9.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.mixture_ratio | OP-1 | 5.9 | - | SECONDARY_CLAIM | SRC-WIKI-LE9 | convention not stated |
| performance.thrust_vac | OP-1 | 1471 | kN | SECONDARY_CLAIM | SRC-WIKI-LE9 |  |
| performance.thrust_vac | OP-1 | 150 | ton (tf) | REPORTED | SRC-MHI-LE9 |  |
| performance.thrust_vac | OP-1 | 150 | t | REPORTED | SRC-JAXA-PRESS-LE9-2017 | attribution of the summary sentence to this PDF uncertain; 2- or 3-engine vehicle configs |
| performance.thrust_vac | OP-1 | ~1500 kN level, just under 1.4x LE-7A | kN | REPORTED | SRC-IHI-GIHO-LE9-TP |  |
| performance.pc | OP-1 | 10.0 | MPa | SECONDARY_CLAIM | SRC-WIKI-LE9 | abs/gauge, station not stated |
| performance.pc | OP-1 | 12.4 | MPa | SECONDARY_CLAIM | SRC-WIKI-LE9 | superseded development target |
| performance.isp_vac | OP-1 | 425 | s | REPORTED | SRC-MHI-LE9 |  |
| performance.isp_vac | OP-1 | 426 | s | SECONDARY_CLAIM | SRC-WIKI-LE9 |  |
| nozzle.area_ratio |  | 37 | - | SECONDARY_CLAIM | SRC-WIKI-LE9 |  |
| mechanical.mass_dry |  | 2400 | kg | SECONDARY_CLAIM | SRC-WIKI-LE9 |  |
| pumps.unidentified_tp.speed_rpm |  | 41600 | rpm | REPORTED | SRC-IHI-GIHO-LE9-TP | 'nominal speed 41 600 rpm', lower than LE-7A; WHICH pump is not legible in the garbled text |
| pumps.lh2_tp.speed_rpm |  | 41600 | rpm | SECONDARY_CLAIM | SRC-IHIFAN-LE9 | Tier E site states LH2 TP explicitly; consistent with IHI value |
| pumps.design.impeller |  | open impellers (cost reduction) | - | REPORTED | SRC-IAC-LE9-2017 |  |
| thrust_chamber.manufacturing |  | HIP brazing for main combustion chamber | - | REPORTED | SRC-IAC-LE9-2017 |  |
| injector.issue |  | low fuel injection temperature can cause combustion vibration | - | SECONDARY_CLAIM | SRC-TEIKYO-LAB001 |  |

**Topology:** 8 nodes, 6 edges; evidence: INFERRED 9, REPORTED_IN_TEXT 5. Completeness: Skeleton mostly INFERRED from the cycle label. Missing: bleed split ratio, turbine arrangement, valve list, igniter, any chamber/nozzle cooling partition.

**Schema breakers:**
- Open expander bleed: turbine drive fluid is coolant-heated H2 that is dumped, so 'cycle' needs an exhaust-destination attribute.
- Vehicle uses 2 or 3 engines (H3-22/-30): installation count is a vehicle property, not engine.
- Operating point adjustable at acceptance test by electric valves: per-serial-number trim point.
- A pump speed reported without pump identity (IHI) - schema must allow 'unidentified component' assertions rather than forcing assignment.

**Missing:** 7 field groups (NOT_REPORTED 4, NOT_AUDITED 3): pumps.lox_tp.speed_rpm, pumps.*.power, turbines.*, cooling.*, turbines.exhaust_destination, injector.element_count, variants.type1_type2

## KRE-075 — `ENG-KR-KRE-075`

**Scope.** KRE-075 (Nuri/KSLV-II). Stage-1 sea-level version is the baseline; stage-2 altitude-nozzle version values are tagged OP-3 and also kept in a separate engines.json record ENG-KR-KRE-075-2ND-STAGE. 2009 KARI values are design-stage targets.

**Architecture (master list).** LOX / Jet A-1; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` stage-1 version, vacuum; `OP-2` stage-1 version, sea level; `OP-3` stage-2 (altitude nozzle) version, vacuum; `OP-4` 2009 design target, vacuum

**Assertions:** 24 (SECONDARY_CLAIM 19, REPORTED 5). Full list in [data/anchors/ENG-KR-KRE-075.json](data/anchors/ENG-KR-KRE-075.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX | - | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| propellants.fuel |  | Jet A-1 | - | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| propellants.mixture_ratio |  | 2.45 | - | SECONDARY_CLAIM | SRC-WIKI-KRE075 | convention not stated |
| performance.pc | OP-1 | 7.0 | MPa | SECONDARY_CLAIM | SRC-WIKI-KRE075 | 1,020 psi |
| performance.pc | OP-1 | 60 | bar | SECONDARY_CLAIM | SRC-FRWIKI-KRE075 |  |
| performance.pc | OP-4 | 60 | bar | REPORTED | SRC-KSCI-KARI-2009-KRE75 | design-stage combustion chamber |
| performance.thrust_vac | OP-4 | 74.8 | ton | REPORTED | SRC-KSCI-KARI-2009-KRE75 | design stage |
| performance.isp_vac | OP-4 | 306.9 | s | REPORTED | SRC-KSCI-KARI-2009-KRE75 | design stage |
| performance.thrust_vac | OP-1 | 735.5 | kN | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| performance.thrust_vac | OP-3 | 788 | kN | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| performance.thrust_vac | OP-1 | 75.8 | tonf | SECONDARY_CLAIM | SRC-NAMU-KRE075 | summary says 'sea-level type' vacuum thrust |
| performance.thrust_vac | OP-3 | 81.1 | tonf | SECONDARY_CLAIM | SRC-NAMU-KRE075 |  |
| performance.isp_vac | OP-1 | 298.6 | s | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| performance.isp_vac | OP-3 | 315.4 | s | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| performance.isp_sl | OP-2 | 261.7 | s | SECONDARY_CLAIM | SRC-WIKI-KRE075 |  |
| performance.burn_time | OP-1 | 127 | s | SECONDARY_CLAIM | SRC-WIKI-KRE075 | stage 1 |
| performance.burn_time | OP-3 | 148 | s | SECONDARY_CLAIM | SRC-WIKI-KRE075 | stage 2 |
| gas_generator.gg1.flow_fraction |  | ~4% of engine propellant flow | % | SECONDARY_CLAIM | SRC-NAMU-KRE075 | host page uncertain (Namu/Wikipedia) |
| turbines.exhaust_destination |  | GG gas passes heat exchanger and exhaust duct; exhaust produces ~1% of thrust | - | SECONDARY_CLAIM | SRC-NAMU-KRE075 |  |
| turbines.tt1.type |  | impulse turbine, 12 nozzles, single rotor | - | REPORTED | SRC-KSCI-KARI-2016-TP | 2016 development TP |

**Topology:** 8 nodes, 8 edges; evidence: INFERRED 8, REPORTED_IN_TEXT 8. Completeness: Skeleton with notable heat exchanger; valve placement, regen cooling and pressurant paths unknown.

**Schema breakers:**
- Two stage-specific variants (stage-1 SL nozzle, stage-2 altitude nozzle) share the designation.
- Turbine exhaust passes a heat exchanger then a thrust-producing exhaust duct: exhaust has both thermal duty and thrust contribution.
- Design-stage (2009) vs flight values for the same designation.
- Chamber pressure 7.0 MPa vs 60 bar across sources.

**Missing:** 5 field groups (NOT_REPORTED 5): pumps.*.speed_rpm, gas_generator.gg1.mr, turbines.tt1.inlet_t, pumps.*.discharge_p, heat_exchanger.function

## Rutherford — `ENG-NZ-RUTHERFORD`

**Scope.** Rutherford sea-level engine (Electron first stage, 9 per stage). Rutherford Vacuum in its own record. Ratings changed over time.

**Architecture (master list).** LOX / NOT_AUDITED; pump_fed_electric; electric_pump (REPORTED); chambers: 1

**Operating points.** `OP-1` rated, sea level (later rating); `OP-2` rated, sea level (earlier rating)

**Assertions:** 14 (REPORTED 9, SECONDARY_CLAIM 5). Full list in [data/anchors/ENG-NZ-RUTHERFORD.json](data/anchors/ENG-NZ-RUTHERFORD.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 5600 | lbf | REPORTED | SRC-ROCKETLAB-UPDATES | 'up from 5,500'; relayed via sibling log |
| performance.thrust_sl | OP-2 | 5500 | lbf | REPORTED | SRC-ROCKETLAB-UPDATES | relayed via sibling log |
| performance.isp_sl | OP-1 | 311 | s | REPORTED | SRC-ROCKETLAB-UPDATES | relayed via sibling log |
| mechanical.mass_dry |  | 35 | kg | REPORTED | SRC-RKLB-SEC-FILING | 'about 35 kg'; attribution uncertain |
| pumps.motor.power |  | 50 | hp | SECONDARY_CLAIM | SRC-POPSCI-RUTHERFORD-2015 | ~37 kW DERIVED; per motor; 2015 press |
| propellants.pair |  | LOX / RP-1 |  | SECONDARY_CLAIM | SRC-WIKI-RUTHERFORD |  |

**Topology:** 6 nodes, 4 edges; evidence: REPORTED_IN_TEXT 5, INFERRED 5. Completeness: Partial. Missing: separate LOX/fuel pumps, inverters/controllers, cooling path, injector, valves.

**Schema breakers:**
- Power source is electrical (battery) — topology needs non-fluid energy edges and battery mass/energy fields.
- Batteries may be jettisoned/managed at stage level (unverified) — subsystem boundary ambiguous.
- Battery packs jettisoned mid-burn (stage 2): energy source mass changes discretely during operation.
- Pump motor power (hp/kW) is an electrical-machine property, not a turbine property.

**Missing:** 17 field groups (ACCESS_BLOCKED 17): performance.thrust_vac, performance.pc, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.gimbal, history.first_flight

## Rutherford Vacuum — `ENG-NZ-RUTHERFORD-VACUUM`

**Scope.** Rutherford Vacuum (Electron second stage, 1 engine).

**Architecture (master list).** LOX / NOT_AUDITED; pump_fed_electric; electric_pump (REPORTED); chambers: 1

**Operating points.** `OP-1` rated, vacuum (later); `OP-2` rated, vacuum (2022 page)

**Assertions:** 6 (REPORTED 5, SECONDARY_CLAIM 1). Full list in [data/anchors/ENG-NZ-RUTHERFORD-VACUUM.json](data/anchors/ENG-NZ-RUTHERFORD-VACUUM.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 5800 | lbf | REPORTED | SRC-ROCKETLAB-UPDATES | relayed via sibling log |
| performance.isp_vac | OP-1 | 343 | s | REPORTED | SRC-ROCKETLAB-UPDATES | relayed via sibling log |
| performance.thrust_vac | OP-2 | 24 | kN | REPORTED | SRC-ROCKETLAB-UPDATES | 2022 page, also stated as 5,500 lbf; relayed via sibling log |
| performance.thrust_vac | OP-2 | 5500 | lbf | REPORTED | SRC-ROCKETLAB-UPDATES | relayed via sibling log |
| performance.thrust_vac | OP-1 | 26 | kN | SECONDARY_CLAIM | SRC-WIKI-RUTHERFORD | updated; CF-R2-11 |

**Topology:** none extracted.

**Schema breakers:**
- 24 kN vs 5,500 lbf (24.47 kN) rounding mismatch inside one page — unit conversion provenance matters.

**Missing:** 18 field groups (ACCESS_BLOCKED 18): performance.thrust_sl, performance.pc, performance.isp_sl, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight

## RD-0124 (14D23) — `ENG-RU-RD-0124`

**Scope.** RD-0124 Soyuz-2.1b/2.1v Block I. Excludes RD-0124A (Angara) and RD-0124MS (Soyuz-5).

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 4

**Operating points.** `OP-NOM` nominal; `OP-THR` reduced-Pc (throttled) mode

**Assertions:** 13 (SECONDARY_CLAIM 13). Full list in [data/anchors/ENG-RU-RD-0124.json](data/anchors/ENG-RU-RD-0124.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| thrust_chamber.count |  | 4 | count | SECONDARY_CLAIM | SRC-RSW-RD0124 |  |
| gg_preburner.type |  | preburner (ox-rich staged combustion) |  | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| cooling.coolant |  | kerosene (regenerative) |  | SECONDARY_CLAIM | SRC-RSW-RD0124 |  |
| performance.pc | OP-NOM | 15.7 | MPa | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| performance.thrust_vac | OP-NOM | 294.3 | kN | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| performance.isp_vac | OP-NOM | 359 | s | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| performance.pc | OP-THR | 9.5 | MPa (1,380 psi) | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| performance.isp_vac | OP-THR | 347 | s | SECONDARY_CLAIM | SRC-WIKI-RD0124 |  |
| mechanical.dimensions_design_intent |  | height 2,327 mm, diameter 1,470 mm 'roughly same as RD-0110' (early 30-t design statement) |  | SECONDARY_CLAIM | SRC-RSW-RD0124 | NOT a measured RD-0124 dimension |

**Topology:** 6 nodes, 5 edges; evidence: REPORTED_IN_TEXT 7, INFERRED 4. Completeness: Skeletal; pumps, boost pumps, cooling path, valves missing.

**Schema breakers:**
- Gimbal: engine-level 2-plane vs per-chamber single-axis description - schema must allow either.
- Two published operating points (nominal / reduced Pc).

**Missing:** 7 field groups (NOT_REPORTED 7): nozzle.*, injector.*, pumps.*, turbines.*, pressurization.*, materials.*, ignition_start.*

## RD-171M — `ENG-RU-RD-171M`

**Scope.** RD-171M (Zenit-3SL/-3SLB/-2SB, 2000s production). Excludes RD-171 (1985 Zenit) and RD-171MV (Soyuz-5).

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 4

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 15 (REPORTED 14, SECONDARY_CLAIM 1). Full list in [data/anchors/ENG-RU-RD-171M.json](data/anchors/ENG-RU-RD-171M.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-NOM | 740 | tf | REPORTED | SRC-GLAVKOSMOS-RD171M | [carried from round-1 ussr engines.json] |
| performance.thrust_vac | OP-NOM | 806 | tf | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| performance.isp_sl | OP-NOM | 309 | s | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| performance.isp_vac | OP-NOM | 337 | s | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| performance.pc | OP-NOM | 250 | kgf/cm2 | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| mechanical.mass_dry |  | 9300 | kg | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| mechanical.mass_filled |  | 10300 | kg | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| mechanical.length |  | 4150 | mm | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| mechanical.diameter |  | 3565 | mm | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| performance.throttle_range |  | 105-49 | % | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| mechanical.gimbal |  | 6 | deg | REPORTED | SRC-GLAVKOSMOS-RD171M |  |
| performance.thrust_vac |  | 7.8 | MN | REPORTED | SRC-IAC13-20083 |  |
| performance.isp_vac |  | 3273.2 | m/s | REPORTED | SRC-IAC13-20083 |  |
| performance.pc_max_production |  | 25.9 | MPa | REPORTED | SRC-IAC13-20083 | maximum reached by production engine (value kind != rated) |
| thrust_chamber.count |  | 4 | count | SECONDARY_CLAIM | SRC-GLAVKOSMOS-RD171M | 'one TPA feeds four chambers and nozzles' per R2 search summary (source attribution in summary loose) |

**Topology:** none extracted.

**Schema breakers:**
- Pc given as rated (250 kgf/cm2) and as 'maximum reached by production engine' (25.9 MPa) - value kind needed.
- Isp given in s and m/s by different sources.
- Mass given dry and filled.

**Missing:** 9 field groups (NOT_REPORTED 9): pumps.boost_pumps.drive, ignition_start.start_fuel, preburners.count, nozzle.*, injector.*, cooling.*, turbines.*, materials.*, control.*

## RD-180 — `ENG-RU-RD-180`

**Scope.** RD-180 as flown on Atlas III/V (single published nominal rating). Excludes RD-180V and any RD-181/RD-191 data. Values from US (P&W-derived) and Russian sources are NOT confirmed to describe the same production standard.

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 2

**Operating points.** `OP-NOM` nominal (100%) rated, as published

**Assertions:** 29 (SECONDARY_CLAIM 25, REPORTED 4). Full list in [data/anchors/ENG-RU-RD-180.json](data/anchors/ENG-RU-RD-180.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX |  | SECONDARY_CLAIM | SRC-SFN-RD180-2002 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| propellants.fuel |  | kerosene (RP-1) |  | SECONDARY_CLAIM | SRC-SFN-RD180-2002 | Search summary wording 'liquid oxygen and kerosene (RP-1)'. [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| thrust_chamber.count |  | 2 | chambers | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_sl | OP-NOM | 860200 | lb | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | lbf presumably. [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_vac | OP-NOM | 933400 | lb | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_sl | OP-NOM | 860400 | lb | SECONDARY_CLAIM | SRC-PURDUE-RD180 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_vac | OP-NOM | 933000 | lb | SECONDARY_CLAIM | SRC-PURDUE-RD180 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.isp_sl | OP-NOM | 311.3 | s | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.isp_vac | OP-NOM | 337.8 | s | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.isp_sl | OP-NOM | 311 | s | SECONDARY_CLAIM | SRC-PURDUE-RD180 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.pc | OP-NOM | 3722 | psia | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | Location (injector face vs nozzle stagnation) not stated in excerpt. 3722 psia = 25.66 MPa (DERIVED). [merge: status RE… |
| performance.pc | OP-NOM | 3734 | psia | SECONDARY_CLAIM | SRC-PURDUE-RD180 | = 25.75 MPa (DERIVED). [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.pc | OP-NOM | 261 | kgf/cm2 | SECONDARY_CLAIM | SRC-SNOB-172276 | = 25.6 MPa = 3712 psi (DERIVED). Gauge/abs not stated. [merge: status REPORTED -> SECONDARY_CLAIM, source tier E] |
| performance.throttle_range | OP-NOM | 47-100 | % power level | SECONDARY_CLAIM | SRC-SFN-RD180-2002 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.throttle_range | OP-NOM | 40-100 | % ('Forty to 100 percent continuous throttling') | SECONDARY_CLAIM | SRC-SFN-RD180-2002 | Same search result set; may be from SFN 2000 page or Space Foundation sheet. Conflicts with 47%: see CF-3. [merge: stat… |
| performance.throttle_range | OP-NOM | 100-47 | % | REPORTED | SRC-GLAVKOSMOS-RD180 |  |
| nozzle.area_ratio |  | 36.87 | - | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | Value-to-source pairing ambiguous; other value 36.4 (CF-4). [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| propellants.mixture_ratio |  | 2.72 | O/F | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | Engine vs chamber O/F not stated; pairing ambiguous (CF-5). [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| mechanical.length |  | 140 | in | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| mechanical.mass |  | 11675 | lb | SECONDARY_CLAIM | SRC-PURDUE-RD180 | Dry vs wet not stated. [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| mechanical.mass_dry |  | 5480 | kg | REPORTED | SRC-GLAVKOSMOS-RD180 | 5480 kg = 12,081 lb (DERIVED); differs from Purdue 11,675 lb (CF-6). |
| mechanical.height |  | 3.6 | m | REPORTED | SRC-GLAVKOSMOS-RD180 | 3.6 m = 141.7 in, vs 140 in length (SFN) - consistent within rounding. |
| mechanical.diameter |  | 3.2 | m | REPORTED | SRC-GLAVKOSMOS-RD180 | Envelope width presumably. |
| mechanical.gimbal |  | +-8 | deg (each of the two thrust chambers) | SECONDARY_CLAIM | SRC-SFN-RD180-2000 | [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |

**Topology:** 3 nodes, 2 edges; evidence: INFERRED 3, REPORTED_IN_TEXT 2. Completeness: Almost everything: main TPA (pumps, turbine, shaft), boost pumps and their drives, preburner count, fuel cooling paths, igniter/start system, valves, actuators. Graph holds only what search excerpts reported plus 2 INFERRED closed-cycle edges.

**Schema breakers:**
- Two chambers fed by one turbomachinery set: per-chamber vs per-engine values (gimbal is per chamber; thrust/Pc per engine).
- Throttle range stated three ways (47-100%, 40-100%, 100-47%) - needs range + source + context fields, not one number.
- Mass reported as 'weight' (lb) and 'dry mass' (kg) with ~400 lb gap - need mass type qualifier.
- Pc given in psia and kgf/cm2 from different-country sources; abs/gauge unknown.

**Missing:** 16 field groups (ACCESS_BLOCKED 15, NOT_AUDITED 1): turbines.main.*, pumps.fuel_boost.*, pumps.lox_boost.*, history.co_production, thrust_chamber.*, nozzle.*, injector.*, cooling.*, pumps.*, turbines.*, preburners.*, pressurization.*, ignition_start.*, control.*, materials.*, history.*

## NK-33 — `ENG-SU-NK-33`

**Scope.** NK-33 (N1F stock) as characterised in Aerojet AJ26 material. Values in SRC-NAS-DEPS-068011 may describe AJ26 configuration; excludes NK-33A (Soyuz-2.1v) and NK-43.

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-100` 100% throttle

**Assertions:** 17 (SECONDARY_CLAIM 10, REPORTED 7). Full list in [data/anchors/ENG-SU-NK-33.json](data/anchors/ENG-SU-NK-33.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.pc | OP-100 | 2109 | psi | REPORTED | SRC-NAS-DEPS-068011 | main chamber; abs/gauge not stated |
| performance.pc | OP-100 | 2109 | psia | SECONDARY_CLAIM | SRC-PURDUE-AJ26 |  |
| performance.pc | OP-100 | 14.83 | MPa | SECONDARY_CLAIM | SRC-WIKI-NK33 | = 2,151 psi; conflicts with 2,109 psi (CF-R2-4) |
| performance.thrust_vac | OP-100 | 377 | klbf | REPORTED | SRC-NAS-DEPS-068011 |  |
| performance.thrust_sl | OP-100 | 338 | klbf | REPORTED | SRC-NAS-DEPS-068011 |  |
| performance.isp_vac | OP-100 | 331 | s | REPORTED | SRC-NAS-DEPS-068011 |  |
| performance.isp_sl | OP-100 | 297 | s | REPORTED | SRC-NAS-DEPS-068011 |  |
| propellants.mixture_ratio | OP-100 | 2.6 | - (main chamber) | REPORTED | SRC-NAS-DEPS-068011 | chamber MR, not engine MR |
| gg_preburner.type |  | oxygen-rich preburner driving turbopumps |  | SECONDARY_CLAIM | SRC-WIKI-AJ26 |  |
| cooling.method |  | regenerative |  | SECONDARY_CLAIM | SRC-WIKI-AJ26 |  |
| performance.thrust_sl | OP-100 | 1510 | kN | SECONDARY_CLAIM | SRC-WIKI-NK33 |  |
| performance.thrust_vac | OP-100 | 1680 | kN | SECONDARY_CLAIM | SRC-WIKI-NK33 |  |
| performance.throttle_range |  | 50-105 | % | SECONDARY_CLAIM | SRC-WIKI-NK33 |  |
| mechanical.mass_dry |  | 1240 | kg | SECONDARY_CLAIM | SRC-WIKI-NK33 |  |
| pumps.LOX_TP.features |  | Hydraulic Balance Assembly seal package; turbine-end bearing |  | REPORTED | SRC-NASA-ORB3-IRT | named in Orb-3 IRT root-cause candidates for AJ26 LOX TP |

**Topology:** 5 nodes, 3 edges; evidence: REPORTED_IN_TEXT 4, INFERRED 4. Completeness: Skeletal. Missing: shaft arrangement, boost pumps, fuel flows to preburner, valves, ignition.

**Schema breakers:**
- Same hardware carries two designations (NK-33 / AJ26-xx) with modifications; data from Aerojet material may not apply to stock NK-33.
- Field-failure evidence (Orb-3) attaches to a sub-component (LOX TP HBA) of a specific serial engine (E15).

**Missing:** 7 field groups (NOT_REPORTED 7): preburners.count, nozzle.area_ratio, injector.*, turbines.*, pressurization.*, control.*, materials.*

## RD-0120 (11D122) — `ENG-SU-RD-0120`

**Scope.** RD-0120 Energia core-stage engine (nominal 100% and 106% modes).

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-100` 100% power; `OP-106` 106% power

**Assertions:** 14 (REPORTED 8, SECONDARY_CLAIM 5, DERIVED 1). Full list in [data/anchors/ENG-SU-RD-0120.json](data/anchors/ENG-SU-RD-0120.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.pc | OP-100 | 210 | kgf/cm2 | REPORTED | SRC-JAXA-61856043 | from CADB data via AIAA paper (JAXA summary) |
| performance.pc | OP-100 | 20.59 | MPa | DERIVED | SRC-JAXA-61856043 | 210 x 0.0980665 |
| propellants.mixture_ratio | OP-100 | 6 | - | REPORTED | SRC-JAXA-61856043 | convention not stated |
| preburners.PB1.pressure | OP-100 | 398 | kgf/cm2 | REPORTED | SRC-JAXA-61856043 |  |
| preburners.PB1.mixture_ratio | OP-100 | 0.8 | - (fuel-rich) | REPORTED | SRC-JAXA-61856043 |  |
| performance.thrust_vac | OP-100 | 190 | t | REPORTED | SRC-JAXA-61856043 |  |
| performance.thrust_vac | OP-106 | 200 | t | REPORTED | SRC-JAXA-61856043 |  |
| performance.thrust_vac | OP-106 | 1961.3 | kN | SECONDARY_CLAIM | SRC-WIKI-RD0120 |  |
| performance.pc |  | 21.9 | MPa | SECONDARY_CLAIM | SRC-WIKI-RD0120 | operating point not stated; conflicts CF-R2-6 |
| performance.isp_vac |  | 455 | s | SECONDARY_CLAIM | SRC-WIKI-RD0120 |  |
| injector.acoustic_cavities |  | not required (stable without resonators, unlike SSME) |  | SECONDARY_CLAIM | SRC-WIKI-RD0120 |  |
| pumps.inlet_pressure_requirement |  | 2.0-3.0 | MPa (minimum for cavitation-free operation) | REPORTED | SRC-LPRE-NPOEM-RD0120UP | context: feed-unit modernisation; which pump(s) not explicit |

**Topology:** 7 nodes, 5 edges; evidence: REPORTED_IN_TEXT 8, INFERRED 4. Completeness: Skeletal; missing boost pumps, cooling path, preburner feeds, valves, GH2 pressurization tap point.

**Schema breakers:**
- Preburner has its own Pc and MR operating values - preburner must be a first-class entity with operating points.
- Thrust at 100% and 106% both published; unit 't' vs kN.

**Missing:** 7 field groups (NOT_REPORTED 7): preburners.count, pumps.boost_pumps.*, nozzle.*, cooling.*, turbines.*, control.*, materials.*

## RD-107A (14D22) — `ENG-SU-RD-107A`

**Scope.** RD-107A (14D22) on Soyuz-2/Soyuz-FG. Family-level statements from the Wiki RD-107 page (H2O2 drive, start sequence) are attributed to this variant only by family inheritance.

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; separate_turbine_working_fluid (INFERRED); chambers: 4

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 17 (SECONDARY_CLAIM 17). Full list in [data/anchors/ENG-SU-RD-107A.json](data/anchors/ENG-SU-RD-107A.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-NOM | 838.5 | kN | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.thrust_vac | OP-NOM | 1021.3 | kN | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.thrust_vac | OP-NOM | 1019.93 | kN | SECONDARY_CLAIM | SRC-WIKI-SOYUZ-CSG |  |
| performance.thrust_sl | OP-NOM | 85.6 | tf | SECONDARY_CLAIM | SRC-WWW1-RD107A |  |
| performance.thrust_sl | OP-NOM | 839 | kN | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| performance.thrust_vac | OP-NOM | 1020 | kN | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| performance.isp_sl | OP-NOM | 263.3 | s | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| performance.isp_vac | OP-NOM | 320.2 | s | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| thrust_chamber.count_main |  | 4 | count | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| turbines.T1.working_fluid |  | steam/gas from catalytic decomposition of H2O2 |  | SECONDARY_CLAIM | SRC-WIKI-RD107 | family-level statement (RD-107 page) |
| gg_preburner.GG1.catalyst |  | solid catalyst F-30-P-G |  | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |

**Topology:** 13 nodes, 12 edges; evidence: REPORTED_IN_TEXT 16, INFERRED 9. Completeness: Missing: fuel edges, turbine exhaust, pressurant routing, valves, vernier gimbal actuators, N2 source tank.

**Schema breakers:**
- Third, turbine-only working fluid (H2O2) with its own tank, pumps and solid catalyst.
- Chambers by role: 4 main + 2 verniers; verniers have separate gimbal semantics (single-plane vs full).
- Stage-serving hardware (N2 pressurization generator) mounted on the engine TPA.
- Start sequence includes a gravity-fed 'intermediate thrust' stage - a pre-mainstage operating point.

**Missing:** 7 field groups (NOT_REPORTED 7): performance.pc, turbines.T1.exhaust_destination, nozzle.*, injector.*, cooling.*, materials.*, mechanical.*

## RD-108A (14D21) — `ENG-SU-RD-108A`

**Scope.** RD-108A (14D21) on Soyuz-2/Soyuz-FG. Family-level statements from the Wiki RD-107 page (H2O2 drive, start sequence) are attributed to this variant only by family inheritance.

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; separate_turbine_working_fluid (INFERRED); chambers: 4

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 14 (SECONDARY_CLAIM 14). Full list in [data/anchors/ENG-SU-RD-108A.json](data/anchors/ENG-SU-RD-108A.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-NOM | 792.41 | kN | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.thrust_vac | OP-NOM | 921.86 | kN | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.isp_sl | OP-NOM | 257.7 | s | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.isp_vac | OP-NOM | 320.6 | s | SECONDARY_CLAIM | SRC-WIKI-SOYUZFG |  |
| performance.thrust_sl | OP-NOM | 80.8 | tf | SECONDARY_CLAIM | SRC-WWW1-RD107A |  |
| thrust_chamber.count_main |  | 4 | count | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |
| turbines.T1.working_fluid |  | steam/gas from catalytic decomposition of H2O2 |  | SECONDARY_CLAIM | SRC-WIKI-RD107 | family-level statement (RD-107 page) |
| gg_preburner.GG1.catalyst |  | solid catalyst F-30-P-G |  | SECONDARY_CLAIM | SRC-WIKI-RD107 |  |

**Topology:** 15 nodes, 14 edges; evidence: REPORTED_IN_TEXT 18, INFERRED 11. Completeness: Missing: fuel edges, turbine exhaust, pressurant routing, valves, vernier gimbal actuators, N2 source tank.

**Schema breakers:**
- Third, turbine-only working fluid (H2O2) with its own tank, pumps and solid catalyst.
- Chambers by role: 4 main + 4 verniers; verniers have separate gimbal semantics (single-plane vs full).
- Stage-serving hardware (N2 pressurization generator) mounted on the engine TPA.
- Start sequence includes a gravity-fed 'intermediate thrust' stage - a pre-mainstage operating point.

**Missing:** 7 field groups (NOT_REPORTED 7): performance.pc, turbines.T1.exhaust_destination, nozzle.*, injector.*, cooling.*, materials.*, mechanical.*

## RD-170 (11D521) — `ENG-SU-RD-170`

**Scope.** RD-170 Energia strap-on engine. NTRS slides describe 'Energia booster engine' and count Zenit (SL-16) flights under the same label, so some values may be RD-171-common. RD-171/171M excluded (separate records).

**Architecture (master list).** LOX / kerosene; pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM); chambers: 4

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 26 (REPORTED 13, SECONDARY_CLAIM 12, DERIVED 1). Full list in [data/anchors/ENG-SU-RD-170.json](data/anchors/ENG-SU-RD-170.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.pc | OP-NOM | 266.7 | bar | SECONDARY_CLAIM | SRC-NAKEDSCI-RAPTOR | [carried from round 1] Journalism quoting manufacturer. 266.7 bar = 26.67 MPa = 272 kgf/cm2 (DERIVED). Abs/gauge and lo… |
| performance.pc_margin_claim | OP-NOM | >280 | bar (claimed ~10% margin) | SECONDARY_CLAIM | SRC-SNOB-172276 | [carried from round 1] Capability/margin claim, not a rated operating point. Do not merge with rated Pc. |
| preburners.count |  | 2 | count | REPORTED | SRC-NTRS-19910018906 | RESOLVES round-1 1-vs-2 question in favour of 2 (Tier A, but seen only via search summary). Both drive the single turbi… |
| thrust_chamber.count |  | 4 | count | REPORTED | SRC-NTRS-19910018906 |  |
| cooling.method |  | regenerative (fuel) |  | REPORTED | SRC-NTRS-19910018906 | 'four regeneratively cooled (fuel) TCAs' |
| pumps.layout |  | single shaft: fuel pump bottom, oxygen pump middle, turbine top |  | REPORTED | SRC-NTRS-19910018906 |  |
| performance.thrust_sl | OP-NOM | 740 | metric tons | REPORTED | SRC-NTRS-19910018906 |  |
| performance.thrust_vac | OP-NOM | 806 | metric tons | REPORTED | SRC-NTRS-19910018906 |  |
| performance.isp_sl | OP-NOM | 308 | s | REPORTED | SRC-NTRS-19910018906 |  |
| performance.isp_vac | OP-NOM | 336 | s | REPORTED | SRC-NTRS-19910018906 |  |
| performance.pc | OP-NOM | 250 | kgf/cm2 | REPORTED | SRC-NTRS-19910018906 | abs/gauge, station not stated. 250 kgf/cm2 = 24.52 MPa (DERIVED) |
| performance.pc | OP-NOM | 24.52 | MPa | DERIVED | SRC-NTRS-19910018906 | arithmetic 250 x 0.0980665 |
| propellants.mixture_ratio | OP-NOM | 2.58 | - | REPORTED | SRC-NTRS-19910018906 | convention not stated |
| propellants.mixture_ratio | OP-NOM | 2.63 | - | SECONDARY_CLAIM | SRC-WIKI-RD170 |  |
| performance.thrust_sl | OP-NOM | 7250 | kN | SECONDARY_CLAIM | SRC-WIKI-RD170 |  |
| performance.thrust_vac | OP-NOM | 7900 | kN | SECONDARY_CLAIM | SRC-WIKI-RD170 |  |
| turbines.T1.power |  | 170 | MW (230,000 hp) | SECONDARY_CLAIM | SRC-WIKI-RD170 |  |
| performance.life_design |  | 10 | firings (reusable design goal) | SECONDARY_CLAIM | SRC-RSW-RD170 |  |

**Topology:** 13 nodes, 16 edges; evidence: REPORTED_IN_TEXT 17, INFERRED 12. Completeness: Missing: boost pump drives (and their turbine flows), fuel kick pump if any, valves/control, gimbal actuators, coolant edges to TCA2-4 (same as E-11), igniter path, start sequence.

**Schema breakers:**
- 2 preburners -> 1 turbine -> 4 chambers: merge (2->1) then split (1->4) in hot-gas path; preburner and chamber counts differ.
- Rated Pc vs design-margin claim (round-1 >280 bar) vs 266.7 bar journalism vs 250 kgf/cm2 slides: value-kind and source-tier qualifiers needed.
- Flight counts reported under one label for two variants (RD-170 Energia, RD-171 Zenit).
- Low-pressure inlet ports are reported without the boost-pump hardware or drive being described: need 'port' vs 'component' distinction.

**Missing:** 8 field groups (NOT_REPORTED 8): pumps.boost_pumps.drive, preburners.P1.mr, preburners.P1.temperature, nozzle.*, injector.*, materials.*, control.*, mechanical.*

## RD-270 (8D420) — `ENG-SU-RD-270`

**Scope.** RD-270 test-stand engine (never flew).

**Architecture (master list).** N2O4 / UDMH; pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-NOM` nominal 100% rated, as published

**Assertions:** 12 (SECONDARY_CLAIM 12). Full list in [data/anchors/ENG-SU-RD-270.json](data/anchors/ENG-SU-RD-270.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| thrust_chamber.count |  | 1 | count | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| performance.pc | OP-NOM | 26.1 | MPa (3790 psi) | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| performance.isp_sl | OP-NOM | 301 | s | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| performance.isp_vac | OP-NOM | 322 | s | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| performance.thrust_sl | OP-NOM | 6270 | kN | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| performance.thrust_vac | OP-NOM | 6713 | kN | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| propellants.mixture_ratio | OP-NOM | 2.67 | - (variable ~+-7%) | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| propellants.oxidizer |  | N2O4 |  | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| propellants.fuel |  | UDMH |  | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |
| gg_preburner.arrangement |  | two preburners: fuel-rich drives fuel-pump turbine, ox-rich drives ox-pump turbine; main … |  | SECONDARY_CLAIM | SRC-WIKI-RD270 |  |

**Topology:** 7 nodes, 8 edges; evidence: REPORTED_IN_TEXT 13, INFERRED 2. Completeness: Missing: cross-feeds (ox to FPB, fuel to OPB), cooling path, boost pumps, valves. Only Tier D evidence.

**Schema breakers:**
- Two independent turbopump shafts with different hot-gas sides; main chamber is gas-gas.
- Programme end date disputed between language editions.

**Missing:** 9 field groups (NOT_REPORTED 9): nozzle.*, injector.*, cooling.*, pumps.*, turbines.*, materials.*, mechanical.*, control.*, ignition_start.*

## AJ10-137 — `ENG-US-AJ10-137`

**Scope.** Apollo CSM Service Propulsion System engine (AJ10-137, Aerojet). SPS helium/propellant tanks belong to the Service Module (vehicle/stage).

**Architecture (master list).** N2O4 / Aerozine-50; pressure_fed_regulated; none_pressure_fed (INFERRED); chambers: 1

**Assertions:** 5 (SECONDARY_CLAIM 3, REPORTED 2). Full list in [data/anchors/ENG-US-AJ10-137.json](data/anchors/ENG-US-AJ10-137.json).


**Topology:** 7 nodes, 7 edges; evidence: INFERRED 10, REPORTED_IN_TEXT 4. Completeness: Skeleton. Missing: check valves, storage/sump tank pairs, propellant utilization/gauging, valve actuation (GN2), injector, ablative chamber, nozzle extension.

**Schema breakers:**
- Redundant pressurization regulators with distinct setpoints — single 'tank pressure' field insufficient.
- Redundant bipropellant valve banks (expected; unverified) need series/parallel topology semantics.

**Missing:** 22 field groups (ACCESS_BLOCKED 22): performance.thrust_sl, performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, propellants.fuel, nozzle.extension_material

## AJ10-190 — `ENG-US-AJ10-190`

**Scope.** Space Shuttle Orbital Maneuvering System engine (two per Orbiter, in OMS pods). The OMS pod helium/propellant tanks belong to the Orbiter (vehicle). Orion ESM OMS-E reuse noted but NOT included in this record.

**Architecture (master list).** N2O4 (MON-3 per some sources) / MMH; pressure_fed_regulated; none_pressure_fed (INFERRED); chambers: 1

**Assertions:** 2 (SECONDARY_CLAIM 2). Full list in [data/anchors/ENG-US-AJ10-190.json](data/anchors/ENG-US-AJ10-190.json).


**Topology:** 7 nodes, 7 edges; evidence: INFERRED 11, REPORTED_IN_TEXT 3. Completeness: Skeleton only. Missing: check valves, isolation valves, crossfeed to aft RCS, propellant gauging, fuel coolant path, injector, nozzle extension; every node except regulator/He/GN2 valve is inferred.

**Schema breakers:**
- Engine shared across two programmes (Shuttle OMS and Orion ESM) with different vehicle-side pressurization — engine record must not inherit vehicle feed topology.
- OMS propellant crossfeed with Orbiter aft RCS (vehicle-level; expected, unverified) makes tank->engine mapping many-to-many.

**Missing:** 22 field groups (ACCESS_BLOCKED 22): performance.thrust_sl, performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, cooling.method, identity.orion_esm_reuse

## BE-3PM — `ENG-US-BE-3PM`

**Scope.** BE-3PM (New Shepard propulsion module). Separate variant from BE-3U.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; tap_off (REPORTED); chambers: 1

**Operating points.** `OP-1` rated; `OP-2` minimum throttle

**Assertions:** 4 (REPORTED 4). Full list in [data/anchors/ENG-US-BE-3PM.json](data/anchors/ENG-US-BE-3PM.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_rated | OP-1 | 110000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.throttle_min_thrust | OP-2 | 20000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |

**Topology:** none extracted.

**Schema breakers:**
- Deep throttle on a landing booster (~5.5:1 from relayed values, DERIVED) — needs operating points.

**Missing:** 20 field groups (ACCESS_BLOCKED 20): performance.thrust_sl, performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight

## BE-3U — `ENG-US-BE-3U`

**Scope.** BE-3U upper-stage variant (New Glenn GS2). Distinct from BE-3PM (New Shepard) which has its own record.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_bleed (REPORTED); chambers: 1

**Operating points.** `OP-1` rated, vacuum; `OP-2` minimum throttle

**Assertions:** 6 (REPORTED 6). Full list in [data/anchors/ENG-US-BE-3U.json](data/anchors/ENG-US-BE-3U.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 200000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.throttle_min_thrust | OP-2 | 100000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.thrust_vac |  | 173000 | lbf | REPORTED | SRC-BLUE-PRESS-BE3U-UPDATES | earlier rating (CF-2); relayed via sibling log |
| performance.thrust_vac |  | 160000 | lbf | REPORTED | SRC-BLUE-PRESS-BE3U-UPDATES | '160,000 lbf each' in another release (CF-2); relayed via sibling log |

**Topology:** none extracted.

**Schema breakers:**
- Manufacturer cycle wording ('open expander') vs encyclopedic ('expander bleed') — cycle enum needs a source-wording field plus normalized value.
- Same family has a tap-off variant (BE-3PM) and an expander variant (BE-3U): cycle is a variant property, not a family property.

**Missing:** 19 field groups (ACCESS_BLOCKED 19): performance.thrust_sl, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight

## BE-4 — `ENG-US-BE-4`

**Scope.** BE-4 as described on Blue Origin's engines page (current rating). Earlier press-release rating kept as conflict. Covers both Vulcan (2/vehicle) and New Glenn (7/vehicle) uses.

**Architecture (master list).** LOX / LNG; pump_fed_turbopump; staged_combustion_ox_rich (REPORTED); chambers: 1

**Operating points.** `OP-1` rated (as on engines page; SL implied); `OP-2` minimum throttle

**Assertions:** 17 (REPORTED 13, SECONDARY_CLAIM 4). Full list in [data/anchors/ENG-US-BE-4.json](data/anchors/ENG-US-BE-4.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 640000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | also 2,846 kN; SL vs vac not explicit in relay; relayed via sibling log |
| performance.thrust_sl | OP-1 | 2846 | kN | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.throttle_min_thrust | OP-2 | 220000 | lbf | REPORTED | SRC-BLUE-ENGINES-PAGE | 'throttle to 220,000 lbf (978 kN)'; relayed via sibling log |
| performance.throttle_min_thrust | OP-2 | 978 | kN | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.thrust_sl |  | 550000 | lbf | REPORTED | SRC-BLUE-PRESS-BE4-EARLY | earlier press-release rating; see CF-1; relayed via sibling log |
| propellants.pair |  | LOX/LNG |  | REPORTED | SRC-BLUE-ENGINES-PAGE | relayed via sibling log |
| performance.thrust_sl | OP-1 | 550000 | lbf | REPORTED | SRC-ULA-BE4-FACTSHEET | earlier rating; CF-R2-5 |
| performance.thrust_sl | OP-1 | 640000 | lbf | REPORTED | SRC-BLUE-NEWGLENN-PAGE | 2,846 kN; 'deep-throttle capability' |
| preburners.count |  | 1 |  | SECONDARY_CLAIM | SRC-WIKI-BE4 | single oxygen-rich preburner |
| turbines.count |  | 1 |  | SECONDARY_CLAIM | SRC-WIKI-BE4 | single turbine drives fuel and oxygen pumps |
| performance.pc | OP-1 | 134 | bar | SECONDARY_CLAIM | SRC-WIKI-BE4 | CF-R2-6 |
| performance.pc | OP-1 | 140 | bar | SECONDARY_CLAIM | SRC-WIKI-BE4 | CF-R2-6 |

**Topology:** 5 nodes, 4 edges; evidence: REPORTED_IN_TEXT 7, INFERRED 2. Completeness: Boost pumps, regen path, igniters, valves unknown. Preburner/turbine counts SECONDARY_CLAIM.

**Schema breakers:**
- Fuel is 'LNG' (a mixture) rather than pure methane — propellant field cannot be a fixed species.
- Same engine on two vehicles from two companies; vehicle-specific ratings possible.
- Propellant choice justified by vehicle tank-pressurization (autogenous) - a vehicle attribute recorded in engine docs.

**Missing:** 21 field groups (ACCESS_BLOCKED 21): performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, gg_preburner.preburner_count, pumps.boost_pumps

## F-1 — `ENG-US-F-1`

**Scope.** Rocketdyne F-1 as flown on Saturn V S-IC (initial 1.5 Mlbf rating and uprated 1.522 Mlbf). Excludes F-1A and F-1B.

**Architecture (master list).** LOX / RP-1; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1500K` Initial rating, sea level; `OP-1522K` Uprated, sea level (from SA-504 per round-1 caption)

**Assertions:** 34 (SECONDARY_CLAIM 32, DERIVED 2). Full list in [data/anchors/ENG-US-F-1.json](data/anchors/ENG-US-F-1.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1500K | 1500000 | lbf | SECONDARY_CLAIM | SRC-WIKIARCHIVES-MSFC-F1 | Carried from round 1 (NASA caption). [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_sl | OP-1500K | 1.5 million | lb | SECONDARY_CLAIM | SRC-NASM-F1 |  |
| performance.thrust_sl | OP-1522K | 1522000 | lbf | SECONDARY_CLAIM | SRC-WIKIARCHIVES-MSFC-F1 | Carried from round 1. [merge: status REPORTED -> SECONDARY_CLAIM, source tier D] |
| performance.thrust_sl | OP-1522K | 1522000 | lb | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE0812 | 'calibrated to develop a sea-level-rated thrust'. |
| performance.thrust_vac | OP-1522K | 1746000 | lbf | SECONDARY_CLAIM | SRC-WIKI-F1 | 7,770 kN; rating association inferred. |
| performance.pc |  | 70 bar (1,015 psi) | bar | SECONDARY_CLAIM | SRC-WIKI-F1 |  |
| performance.pc |  | 982 | psi | SECONDARY_CLAIM | SRC-PURDUE-F1 |  |
| propellants.mixture_ratio |  | 2.27 | O/F | SECONDARY_CLAIM | SRC-WIKI-F1 | '69% LOX, 31% RP-1'. |
| propellants.mixture_ratio |  | 2.2674 | O/F | SECONDARY_CLAIM | SRC-WIKIDERIV-F1 |  |
| performance.isp_sl |  | 265 | s | SECONDARY_CLAIM | SRC-PURDUE-F1 | Round 1. |
| performance.isp |  | 264.72 | s | SECONDARY_CLAIM | SRC-WIKIDERIV-F1 | Condition not stated. |
| performance.mdot_total_5_engines |  | 28415 | lb/s | SECONDARY_CLAIM | SRC-WIKIDERIV-F1 | Five-engine combined (3,357 US gal/s). |
| performance.mdot_total |  | 5683 | lb/s | DERIVED | SRC-WIKIDERIV-F1 | 28,415 / 5; derived from a secondary claim. |
| pumps.TP.configuration |  | single-shaft turbopump with separate fuel and LOX pumps (MK-10) |  | SECONDARY_CLAIM | SRC-AWESOMESTORIES-F1NASA | NASA text reproduction; MK-10 name from enginehistory. |
| pumps.TP.mass |  | 2500 | lb | SECONDARY_CLAIM | SRC-NASM-F1 | Also enginehistory. |
| pumps.TP.flow_total |  | 42500 | US gal/min | SECONDARY_CLAIM | SRC-NASM-F1 |  |
| pumps.FP.flow |  | 15471 | US gal/min | SECONDARY_CLAIM | SRC-WIKI-F1 | RP-1. |
| pumps.OP.flow |  | 24811 | US gal/min | SECONDARY_CLAIM | SRC-WIKI-F1 | LOX; sum 40,282 gpm vs NASM 42,500 gpm (CF-F1-4). |
| turbines.T.speed_rpm |  | 5500 | rpm | SECONDARY_CLAIM | SRC-WIKI-F1 |  |
| turbines.T.speed_rpm |  | 5490 | rpm | DERIVED | SRC-ENGINEHISTORY-F1 | From '91.5 revolutions in one second' x 60. |
| turbines.T.power |  | 55000 | bhp | SECONDARY_CLAIM | SRC-WIKI-F1 | 41 MW; enginehistory also 55,000 hp. |
| turbines.T.stages |  | 2 (impulse) |  | SECONDARY_CLAIM | SRC-ENGINEHISTORY-F1 |  |
| turbines.T.blade_counts |  | 109 blades (33-in 1st stage), 119 blades (35-in 2nd stage) |  | SECONDARY_CLAIM | SRC-ENGINEHISTORY-F1 |  |
| turbines.T.inlet_temperature |  | 1500 | degF | SECONDARY_CLAIM | SRC-WIKI-F1 | 'input gas at 1,500 F'; Wikipedia cites Saturn V News Reference F-1 Fact Sheet (not retrieved). |
| turbines.T.exhaust_destination |  | heat exchanger, then wrap-around exhaust manifold feeding the periphery of the engine bel… |  | SECONDARY_CLAIM | SRC-AWESOMESTORIES-F1NASA | NASA text reproduction; Wikipedia: tapered manifold, film protects NE from ~3,200 C gas. |
| gas_generators.GG.rich_side |  | fuel-rich LOX/RP-1 |  | SECONDARY_CLAIM | SRC-AWESOMESTORIES-F1NASA |  |
| mechanical.bearing_lubrication |  | fuel (RP-1) lubricates and cools turbopump bearings |  | SECONDARY_CLAIM | SRC-STEVEBLOG-F1GG | Blog quoting NASA; also Wikipedia. |
| thrust_chamber.construction |  | two-piece: tubular-wall regeneratively cooled chamber to 10:1 plane; double-walled turbin… |  | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE0812 |  |
| nozzle.area_ratio |  | 16 | :1 | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE0812 | Also Purdue, Wikipedia. |
| nozzle.area_ratio_regen_section |  | 10 | :1 | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE0812 | Attachment plane of extension. |
| mechanical.mass_dry |  | 18500 | lb | SECONDARY_CLAIM | SRC-ENGINEHISTORY-RPE0812 | 'approximately'; source attribution partly inferred. |
| mechanical.mass |  | 18616 | lb | SECONDARY_CLAIM | SRC-PURDUE-F1 |  |

**Topology:** 10 nodes, 13 edges; evidence: REPORTED_IN_TEXT 22, INFERRED 1. Completeness: Missing main valves, HX working fluids and outputs (stage pressurization), GG valve, hydraulic control using fuel [BG], checkout/purge lines, injector.

**Schema breakers:**
- Turbine exhaust is a coolant: one flow is both 'turbine_exhaust' and 'nozzle_extension_cooling', after passing a heat exchanger used for vehicle functions.
- Two area ratios within one nozzle (regen chamber to 10:1, TEG-cooled extension to 16:1) with different cooling methods.
- Consumable ignition element (hypergol cartridge) inserted into the propellant circuit.
- Re-rating (1.500 -> 1.522 Mlbf) under the same designation.
- Propellant used as bearing lubricant/coolant (fuel), a non-combustion use of the fuel stream.

**Missing:** 5 field groups (NOT_REPORTED 5): pumps.*.discharge_pressure, gas_generators.GG.flow / mr / pressure, pressurization.heat_exchanger_fluids, performance.pc (1,125 psia query hint), injector.*

## H-1 — `ENG-US-H-1`

**Scope.** Umbrella anchor for the H-1 as used in Saturn I S-I and Saturn IB S-IB clusters, kept at the round-1 id for merge continuity. Values are tagged to rating operating points (188k / 200k / 205k lb) because sources disagree; the merge SHOULD split them into ENG-US-H-1-188K / -200K / -205K (us_hist ids). Turbopump numbers come from a 1965 NASA report tied to the 188k rating.

**Architecture (master list).** LOX / RP-1; pump_fed_turbopump; gas_generator (REPORTED); chambers: 1

**Operating points.** `OP-188K` 188,000 lb SL rating (1965 NASA report); `OP-200K` 200,000 lb SL rating (Saturn IB); `OP-205K` 205,000 lb SL rating (final)

**Assertions:** 29 (SECONDARY_CLAIM 17, REPORTED 11, DERIVED 1). Full list in [data/anchors/ENG-US-H-1.json](data/anchors/ENG-US-H-1.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-188K | 188000 | lb | REPORTED | SRC-NTRS-19650013470 | 'nominal sea-level thrust rating'. |
| performance.thrust_sl | OP-188K | 188000 | lb | SECONDARY_CLAIM | SRC-NASM-H1 | Displayed engine 'may be the second variation'. |
| performance.thrust_sl | OP-200K | 200000 | lbf | SECONDARY_CLAIM | SRC-WIKI-H1 | Infobox; summary says adopted on Saturn IB. |
| performance.thrust_sl | OP-205K | 205000 | lbf | SECONDARY_CLAIM | SRC-WIKI-H1 | Text value. |
| performance.thrust_sl | OP-205K | 205000 | lb | SECONDARY_CLAIM | SRC-PURDUE-H1 | Round 1. |
| performance.pc |  | 700 | psia | SECONDARY_CLAIM | SRC-PURDUE-H1 | Rating not stated. |
| performance.pc |  | 700 | psi | SECONDARY_CLAIM | SRC-WIKI-H1 |  |
| propellants.mixture_ratio |  | 2.23 | O/F | SECONDARY_CLAIM | SRC-PURDUE-H1 |  |
| performance.isp_vac |  | 289 | s | SECONDARY_CLAIM | SRC-WIKI-H1 |  |
| performance.isp_sl |  | 255 | s | SECONDARY_CLAIM | SRC-WIKI-H1 |  |
| performance.isp_sl |  | 263 | s | SECONDARY_CLAIM | SRC-PURDUE-H1 |  |
| performance.burn_time |  | 155 | s | SECONDARY_CLAIM | SRC-WIKI-H1 |  |
| nozzle.area_ratio |  | 8 | :1 | SECONDARY_CLAIM | SRC-PURDUE-H1 |  |
| mechanical.mass_dry |  | 2200 | lb | SECONDARY_CLAIM | SRC-WIKI-H1 |  |
| mechanical.mass |  | 2009 | lb | SECONDARY_CLAIM | SRC-PURDUE-H1 |  |
| turbines.T.stages | OP-188K | 2 | stages | REPORTED | SRC-NTRS-19650013470 | OCR-garbled text; engine identity of this passage medium. |
| turbines.T.power | OP-188K | 3793 | hp | REPORTED | SRC-NTRS-19650013470 | 'about'. |
| turbines.T.speed_rpm | OP-188K | 32000 | rpm | REPORTED | SRC-NTRS-19650013470 | 'roughly'. |
| mechanical.gearbox | OP-188K | gear reductions drive LOX and fuel pumps from the turbine shaft |  | REPORTED | SRC-NTRS-19650013470 |  |
| pumps.LOX.speed_rpm | OP-188K | 6537 | rpm | REPORTED | SRC-NTRS-19650013470 | Both pumps quoted at ~6,537 rpm. |
| pumps.FUEL.speed_rpm | OP-188K | 6537 | rpm | REPORTED | SRC-NTRS-19650013470 |  |
| mechanical.gear_ratio | OP-188K | 4.9 | :1 | DERIVED | SRC-NTRS-19650013470 | 32,000 / 6,537 = 4.9 (DERIVED from approximate values). |
| mechanical.accessory_drive | OP-188K | dual accessory drive pads ~4,000 rpm; electric heater keeps accessory-drive bearings from… |  | REPORTED | SRC-NTRS-19650013470 |  |
| mechanical.lubrication |  | additive blended into RP-1 by FABU; fuel/additive mix fed under pressure to turbopump bea… |  | SECONDARY_CLAIM | SRC-WIKI-H1 | FABU existence REPORTED in NTRS 19650013470. |

**Topology:** 10 nodes, 12 edges; evidence: REPORTED_IN_TEXT 18, INFERRED 4. Completeness: Missing valves, turbine exhaust path, heat exchanger (if any), regen path, igniter/hypergol location, LOX dome.

**Schema breakers:**
- Gearbox with three output speeds (turbine ~32,000; pumps ~6,537; accessory ~4,000 rpm) - one turbine, many shafts.
- Two different turbine start sources (solid SPGG) vs run source (LPGG) - start-only working fluid.
- Fuel-additive lubrication system (FABU) - a third 'propellant-derived' fluid circuit.
- Installation-dependent variants (inboard fixed vs outboard gimbaled; outboard carries hydraulic system) under one designation.
- Three successive thrust ratings under one designation.

**Missing:** 5 field groups (NOT_REPORTED 5): turbopump data at 200K/205K, gearbox lube reservoir (query hint), pumps.*.discharge_pressure, cooling.*, injector.*

## Integrated Powerhead Demonstrator — `ENG-US-IPD`

**Scope.** IPD full-flow staged-combustion LOX/LH2 powerhead demonstrator (Rocketdyne + Aerojet; NASA/AFRL IHPRPT). Powerhead test article, not a flight engine.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; full_flow_staged_combustion (REPORTED); chambers: 1

**Assertions:** 13 (REPORTED 9, SECONDARY_CLAIM 4). Full list in [data/anchors/ENG-US-IPD.json](data/anchors/ENG-US-IPD.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_class |  | 250 | klbf | SECONDARY_CLAIM | SRC-SFN-IPD-2006 | '250 klbf' class; SL/vac not stated; relayed via sibling log |
| propellants.pair |  | LOX/LH2 |  | SECONDARY_CLAIM | SRC-SFN-IPD-2006 | relayed via sibling log |
| performance.thrust_sl | OP-1 | 1112000 | N | REPORTED | SRC-DTIC-ADA397910 | '(250,000 lbf) thrust (at sea level)' design class |
| performance.thrust_sl | OP-1 | 250000 | lbf | REPORTED | SRC-DTIC-ADA397910 |  |
| preburners.FPB.drives |  | fuel turbopump |  | REPORTED | SRC-AF-IPD-2006 |  |
| preburners.OPB.drives |  | oxygen turbopump |  | REPORTED | SRC-AF-IPD-2006 |  |
| pumps.OTP.bearings |  | hydrostatic bearings |  | REPORTED | SRC-DTIC-ADA430218 |  |

**Topology:** 5 nodes, 4 edges; evidence: REPORTED_IN_TEXT 6, INFERRED 3. Completeness: Preburner->turbopump pairing REPORTED (USAF). Pump feed of preburners, cooling, valves, Pc missing.

**Schema breakers:**
- Demonstrator 'engine' that is a powerhead (no flight nozzle) — chamber/nozzle fields may legitimately be N/A, not missing.

**Missing:** 20 field groups (ACCESS_BLOCKED 19, NOT_AUDITED 1): performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, documents.ntrs

## J-2 — `ENG-US-J-2`

**Scope.** Rocketdyne J-2 as flown on S-II and S-IVB (Saturn IB/V). Thrust ratings evolved (200k/225k/230k lb per various sources) - rating-specific values flagged in notes. Excludes J-2S, J-2T, J-2X.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (REPORTED); chambers: 1

**Operating points.** `OP-MR5.5` Main stage, engine MR 5.5 (vacuum); `OP-MR4.5` Main stage, engine MR 4.5 (PU shift, vacuum)

**Assertions:** 50 (SECONDARY_CLAIM 33, REPORTED 17). Full list in [data/anchors/ENG-US-J-2.json](data/anchors/ENG-US-J-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX |  | REPORTED | SRC-NTRS-20100027318 |  |
| propellants.fuel |  | LH2 |  | REPORTED | SRC-NTRS-20100027318 |  |
| propellants.mixture_ratio | OP-MR5.5 | 5.5 | O/F | REPORTED | SRC-NTRS-20100027318 | '5.5:1 at that chamber pressure'; engine MR. |
| propellants.mixture_ratio | OP-MR4.5 | 4.5 | O/F | REPORTED | SRC-NTRS-20100027318 | 'capability of operating at a mixture ratio 4.5:1'. Thrust at 4.5 not found. |
| performance.thrust_vac | OP-MR5.5 | 230000 | lb | REPORTED | SRC-NTRS-20100027318 | 'up to 230,000 pounds of thrust'; rating/flight not specified. |
| performance.thrust_vac | OP-MR5.5 | 230000 | lbf | REPORTED | SRC-NTRS-20120016414 | J-2X requirements table heritage column. |
| performance.thrust_vac | OP-MR5.5 | 225000 | lb | SECONDARY_CLAIM | SRC-DTIC-AEDC-J2-SET | 'a rating of 225,000 lb at a mixture ratio of 5.5' (which AEDC report not named). |
| performance.thrust_vac |  | up to 225,000 lb at high altitude | lb | SECONDARY_CLAIM | SRC-NASA-ALSJ-CSM02 | 'A NASA overview'; attribution to ALSJ CSM02 inferred. |
| performance.thrust_vac |  | 232250 | lbf | SECONDARY_CLAIM | SRC-WIKI-J2 | SA-208/SA-504 configuration; 1,033.1 kN. |
| performance.thrust |  | 200,000-230,000 | lb | SECONDARY_CLAIM | SRC-NASM-J2 | Range over ratings. |
| performance.isp_vac |  | 425 | s | REPORTED | SRC-NTRS-20120016414 |  |
| performance.isp_vac |  | 425 | s | SECONDARY_CLAIM | SRC-PURDUE-J2 |  |
| performance.isp_vac |  | 421 | s | SECONDARY_CLAIM | SRC-WIKI-J2 | SA-208/SA-504. |
| performance.pc | OP-MR5.5 | a little over 700 | psia | REPORTED | SRC-NTRS-20100027318 |  |
| performance.pc |  | 763 | psi | SECONDARY_CLAIM | SRC-WIKI-J2 | 5,260 kPa; abs/gauge not stated. |
| performance.restarts |  | one restart in S-IVB application (parking-orbit insertion ~2 min, TLI ~6.5 min) |  | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| nozzle.area_ratio |  | 27.5 | :1 | REPORTED | SRC-NTRS-20100027318 |  |
| nozzle.area_ratio |  | 27.5 | :1 | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| nozzle.area_ratio |  | 28 | :1 | SECONDARY_CLAIM | SRC-PURDUE-J2 | rounded |
| mechanical.mass_dry |  | 3942 | lb | SECONDARY_CLAIM | SRC-WIKI-J2 | 1,788.1 kg; SA-208/SA-504. |
| mechanical.mass |  | 3480 | lb | SECONDARY_CLAIM | SRC-PURDUE-J2 |  |
| mechanical.mass_unfuelled |  | 3170 | lb | SECONDARY_CLAIM | SRC-ASTRONAUTIX-J2 | 1,438 kg. |
| turbines.arrangement |  | gas generator supplies hot gas to two turbines running in series |  | REPORTED | SRC-NTRS-20100027318 |  |
| turbines.arrangement_detail |  | exhaust from fuel turbopump turbine ducted to inlet of oxidizer turbopump turbine manifol… |  | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| turbines.crossover_duct_diameter |  | 8 | in | SECONDARY_CLAIM | SRC-WIKI-J2 | '8-inch diameter crossover duct' - which source said it is not identified. |
| turbines.ox_turbine_bypass |  | during start a percentage of fuel-turbine exhaust is routed directly to the thrust chambe… |  | SECONDARY_CLAIM | SRC-WIKI-J2 | Source among Wikipedia/RPE08.22 not distinguished. |
| pumps.FTP.type |  | axial flow: inducer + seven-stage rotor + stator |  | SECONDARY_CLAIM | SRC-WIKI-J2 | Also described in NTRS 20080036837 (heritage J-2). |
| pumps.FTP.speed_rpm |  | 27000 | rpm | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| pumps.FTP.pressure_rise |  | 30 -> 1,225 | psi (abs) | SECONDARY_CLAIM | SRC-WIKI-J2 | 210 -> 8,450 kPa. |
| pumps.FTP.heritage |  | axial fuel turbopump derived from nuclear-rocket-programme machines; caused a start-sensi… |  | SECONDARY_CLAIM | SRC-NTRS-20100027318 | Attribution inferred. |
| turbines.FT.stages |  | 2 | stages | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| pumps.OTP.type |  | single-stage centrifugal, direct turbine drive |  | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| pumps.OTP.speed_rpm |  | 8600 | rpm | SECONDARY_CLAIM | SRC-WIKI-J2 |  |
| pumps.OTP.discharge_pressure |  | 1080 | psi (abs) | SECONDARY_CLAIM | SRC-WIKI-J2 | 7,400 kPa. |
| pumps.OTP.power |  | 2200 | bhp | SECONDARY_CLAIM | SRC-WIKI-J2 | 1,600 kW. |
| injector.lox_path |  | LOX enters via dome manifold and is injected through oxidizer posts |  | SECONDARY_CLAIM | SRC-WIKI-J2 |  |

**Topology:** 16 nodes, 16 edges; evidence: REPORTED_IN_TEXT 30, INFERRED 2. Completeness: Missing GG propellant feed lines and valves, main fuel valve, turbine exhaust destination after ox turbine (nozzle-wall manifold [BG]), stage tank pressurization taps, thrust chamber cooling details, bleed/chilldown.

**Schema breakers:**
- Two operating points selected in flight by a PU valve (MR 5.5 vs 4.5) - engine-level MR is a controlled variable, not a constant.
- Turbines in series across two separate shafts (fuel turbine exhaust drives ox turbine) plus a start-only bypass path.
- Start tank is refilled by the engine during operation for restart - a state-dependent flow path.
- Thrust rating varied by vehicle/flight (200k-232k lb) under one designation.
- Helium for valve actuation stored inside the hydrogen start tank (nested tank).

**Missing:** 7 field groups (NOT_REPORTED 7): performance.thrust_vac@OP-MR4.5, control.pu_valve_positions, gg.mixture_ratio / temperature, turbines.OT.stages, pressurization.*, cooling.*, thrust_chamber.*

## J-2S — `ENG-US-J-2S`

**Scope.** J-2S ('J-2 Simplified' [BG]) development engine with combustion tap-off turbine drive, 1965-1972 testing. Excludes J-2, J-2T, J-2X (J-2X took J-2S as point of departure).

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; tap_off (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-MAIN` Main stage, vacuum; `OP-IDLE-LOW` Idle mode (low); `OP-IDLE-HIGH` Idle mode (high)

**Assertions:** 16 (SECONDARY_CLAIM 8, REPORTED 8). Full list in [data/anchors/ENG-US-J-2S.json](data/anchors/ENG-US-J-2S.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-MAIN | 265000 | lbf | REPORTED | SRC-NTRS-20120016414 | Round 1, comparison table; ID attribution inferred. |
| performance.thrust_vac | OP-MAIN | 265000 | lbf | SECONDARY_CLAIM | SRC-WIKI2007-J2 |  |
| performance.isp_vac | OP-MAIN | 436 | s | REPORTED | SRC-NTRS-20120016414 |  |
| performance.isp_vac | OP-MAIN | 436 | s | SECONDARY_CLAIM | SRC-WIKI2007-J2 |  |
| propellants.mixture_ratio | OP-MAIN | 5.5 | O/F | SECONDARY_CLAIM | SRC-WIKI2007-J2 |  |
| mechanical.mass_dry |  | 3235 | lb | SECONDARY_CLAIM | SRC-WIKI2007-J2 | Round 1; 3,800 lb with accessories. |
| performance.thrust | OP-IDLE-LOW | 4000 | lbf | REPORTED | SRC-DTIC-AEDC-J2S-SET | Round 1 (AD0867628), approximate. |
| performance.thrust | OP-IDLE-HIGH | 50000 | lbf | REPORTED | SRC-DTIC-AEDC-J2S-SET | Round 1, approximate. |
| injector.idle_mode |  | noncompartmented injector (TR-70-150); full-face oxidizer injector for idle (TR-70-204) |  | REPORTED | SRC-DTIC-AEDC-J2S-SET | Configurations changed during development. |
| pumps.heritage |  | J-2S Mk.29 oxidizer and fuel turbopump designs used as J-2X point of departure |  | REPORTED | SRC-NTRS-20080036837 |  |

**Topology:** 6 nodes, 5 edges; evidence: INFERRED 6, REPORTED_IN_TEXT 5. Completeness: Turbine arrangement, exhaust destination, start system, idle-mode flow paths (tank-head idle) all undocumented.

**Schema breakers:**
- Turbine drive gas source is the main chamber itself (tap-off): no gas generator node, and a feedback loop chamber -> turbine -> pumps -> chamber.
- Multiple discrete operating modes (main stage, high idle, low idle) with very different thrust (~4k to 265k lbf).
- Injector configuration changed between test series - a development engine without a single frozen configuration.

**Missing:** 4 field groups (NOT_REPORTED 4): performance.pc, nozzle.area_ratio, turbines.inlet_temperature / tap-off location, pumps.* values

## LMDE — `ENG-US-LMDE`

**Scope.** Lunar Module Descent Engine (TRW) as the engine of the Apollo LM Descent Propulsion System (DPS). Stage-level DPS items (tanks, supercritical helium) are recorded with subsystem=stage. Excludes TR-201 derivative.

**Architecture (master list).** N2O4 / Aerozine-50; pressure_fed_regulated; none_pressure_fed (INFERRED); chambers: 1

**Assertions:** 5 (REPORTED 5). Full list in [data/anchors/ENG-US-LMDE.json](data/anchors/ENG-US-LMDE.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.throttle_capability |  | deep throttling capability (highlighted as distinctive feature) |  | REPORTED | SRC-NASA-TND7143 | No ratio given in the snippet; the orchestrator's 10:1 is unverified; from search summary, document not opened |

**Topology:** 5 nodes, 5 edges; evidence: INFERRED 8, REPORTED_IN_TEXT 2. Completeness: Skeleton. Missing: supercritical-He heat exchanger(s) (expected, unverified), ambient He start bottle, regulators, burst discs/relief, injector, ablative chamber, radiation-cooled extension, shutoff valves.

**Schema breakers:**
- Throttleable engine: a single thrust/Isp/Pc row is insufficient; needs operating points over the throttle range.
- Pressurization is a stage-level cryogenic helium system distinct from the engine — engine record must point to a stage subsystem.
- Variable-geometry injector (if confirmed) is a geometry that changes with operating point.

**Missing:** 22 field groups (ACCESS_BLOCKED 22): performance.thrust_sl, performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, injector.type, control.throttle_mechanism

## LR87-AJ-5 — `ENG-US-LR87-AJ-5`

**Scope.** Titan II ICBM Stage I engine (N2O4 / Aerozine 50). Excludes LR87-AJ-7 (Gemini GLV), -9, -11 and LOX/RP-1 LR87-AJ-3.

**Architecture (master list).** N2O4 / Aerozine-50; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 2

**Operating points.** `OP-1` Nominal Stage I, sea level

**Assertions:** 23 (SECONDARY_CLAIM 23). Full list in [data/anchors/ENG-US-LR87-AJ-5.json](data/anchors/ENG-US-LR87-AJ-5.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| thrust_chamber.count |  | 2 |  | SECONDARY_CLAIM | SRC-TMS-TITAN2 |  |
| pumps.TPA.configuration |  | each TPA: fuel pump + oxidizer pump + gearbox + two balanced turbine wheels |  | SECONDARY_CLAIM | SRC-TMS-TITAN2 |  |
| turbines.TPA.stages |  | 2 (each stage has nozzle diaphragm directing GG exhaust onto rotor) |  | SECONDARY_CLAIM | SRC-TMS-TITAN2 |  |
| propellants.oxidizer |  | N2O4 |  | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| propellants.fuel |  | Aerozine 50 |  | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| propellants.mixture_ratio |  | 1.93 | O/F | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| performance.thrust_sl | OP-1 | 430000 | lb | SECONDARY_CLAIM | SRC-TMS-TITAN2 | Stage I total (both chambers). |
| performance.pc | OP-1 | 5.4 | MPa | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| performance.pc | OP-1 | 54.0 bar (53.3 atm) | bar | SECONDARY_CLAIM | SRC-ASTRONAUTIX-LR87 | Round 1. |
| performance.isp_vac |  | 297 | s | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| performance.isp_sl |  | 259 | s | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| nozzle.area_ratio |  | 8 | :1 | SECONDARY_CLAIM | SRC-WIKI-LR87 |  |
| mechanical.gimbal_range |  | 5 deg any direction (one page) / 4 deg (another page) | deg | SECONDARY_CLAIM | SRC-TMS-TITAN2 | Internal inconsistency. |
| mechanical.lube_oil_reservoir |  | present (capacities quoted differ between Stage I and II) |  | SECONDARY_CLAIM | SRC-TMS-TITAN2 | Gearbox lubrication by separate oil [INFERRED]. |

**Topology:** 15 nodes, 17 edges; evidence: REPORTED_IN_TEXT 28, INFERRED 4. Completeness: GG count and propellant supply, valves, pressurization tap points, injector and regen paths, cross-connections between sub-assemblies all missing.

**Schema breakers:**
- Two chambers + two turbopumps + (possibly) shared components, fired as one unit: neither 'one engine' nor 'two engines' cleanly.
- Asymmetric sub-assemblies (only sub-assembly 2 carries the oxidizer super-heater).
- Engine produces both tanks' pressurant by different mechanisms (GG gas vs evaporated oxidizer).
- Start by consumable solid cartridge.

**Missing:** 5 field groups (NOT_REPORTED 3, UNKNOWN 1, NOT_AUDITED 1): gas_generators.count, pumps.*.speed / pressures, injector.*, mechanical.mass, HAER engine record

## Merlin 1D — `ENG-US-MERLIN-1D`

**Scope.** Merlin 1D sea-level engine as described in the 2025-05-09 Falcon User's Guide (implicitly Falcon 9 Block 5 configuration). Earlier v1.1/FT ratings are NOT captured. Merlin 1D Vacuum noted only in engines.json/notes.

**Architecture (master list).** LOX / RP-1; pump_fed_turbopump; gas_generator (REPORTED); chambers: 1

**Operating points.** `OP-1` nominal, sea level (as stated in 2025 user guide)

**Assertions:** 17 (SECONDARY_CLAIM 9, REPORTED 8). Full list in [data/anchors/ENG-US-MERLIN-1D.json](data/anchors/ENG-US-MERLIN-1D.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 845 | kN | REPORTED | SRC-SPACEX-FUG-2025 | per engine; also given as 190,000 lbf; relayed via sibling log |
| performance.thrust_sl | OP-1 | 190000 | lbf | REPORTED | SRC-SPACEX-FUG-2025 | per engine; relayed via sibling log |
| propellants.pair |  | RP-1 / LOX |  | REPORTED | SRC-SPACEX-F9-PAGE |  |
| performance.pc | OP-1 | 9.7 | MPa | SECONDARY_CLAIM | SRC-WIKI-MERLIN | 1,410 psi; CF-R2-8 |
| performance.thrust_vac | OP-1 | 981 | kN | SECONDARY_CLAIM | SRC-WIKI-MERLIN | sea-level engine in vacuum; 221,000 lbf |
| nozzle.area_ratio |  | 16 | :1 | SECONDARY_CLAIM | SRC-WIKI-MERLIN |  |
| injector.type |  | pintle (LMDE heritage) |  | SECONDARY_CLAIM | SRC-WIKI-MERLIN |  |
| pumps.TPA.arrangement |  | single-shaft, dual-impeller turbopump |  | SECONDARY_CLAIM | SRC-UC-OLLI-SPACEX |  |
| pumps.TPA.speed_rpm | OP-1 | 36000 | rpm | SECONDARY_CLAIM | SRC-UC-OLLI-SPACEX |  |
| turbines.TPA.power | OP-1 | 10000 | hp | SECONDARY_CLAIM | SRC-UC-OLLI-SPACEX | 'about' |
| performance.throttle_range | OP-1 | 100%-57% | % (SL) | SECONDARY_CLAIM | SRC-WEVOLVER-MERLIN | CF-R2-9 |

**Topology:** 6 nodes, 3 edges; evidence: REPORTED_IN_TEXT 5, INFERRED 4. Completeness: GG cycle REPORTED by FUG; everything else secondary. Turbine exhaust destination, regen cooling path, valves missing.

**Schema breakers:**
- Rating drifts by date/block with the same designation (Merlin 1D thrust uprates); engine record needs dated ratings.
- Stage thrust (7,605 kN) is commonly quoted alongside engine thrust — must not be stored as engine thrust.
- Unofficial sub-variant labels (1D+, 1D++) used by secondary sources for uprated values.

**Missing:** 14 field groups (ACCESS_BLOCKED 13, NOT_REPORTED 1): performance.isp_vac, propellants.mixture_ratio, performance.mdot_total, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.extension_material, cooling.method, control.valves, mechanical.mass_dry, mechanical.gimbal, history.first_flight, performance.isp_sl, gas_generators.GG.*

## R-4D-11 — `ENG-US-R-4D-11`

**Scope.** R-4D-11 490 N-class NTO/MMH apogee/spacecraft engine; two nozzle configurations (164:1 and 300:1) per L3Harris spec sheet. Excludes R-4D-15 (HiPAT) and Orion ESM auxiliary use.

**Architecture (master list).** N2O4/MON-3 / MMH; pressure_fed_regulated; none_pressure_fed (INFERRED); chambers: 1

**Operating points.** `OP-1` 300:1 nozzle configuration; `OP-2` 164:1 nozzle configuration

**Assertions:** 10 (REPORTED 5, SECONDARY_CLAIM 3, INFERRED 2). Full list in [data/anchors/ENG-US-R-4D-11.json](data/anchors/ENG-US-R-4D-11.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_range |  | 378-511 | N | REPORTED | SRC-L3H-LHX-SPECSHEET-2024 |  |
| performance.isp_vac | OP-1 | 315.5 | s (lbf-s/lbm) | REPORTED | SRC-L3H-LHX-SPECSHEET-2024 |  |
| performance.isp_vac | OP-2 | 311 | s (lbf-s/lbm) | REPORTED | SRC-L3H-LHX-SPECSHEET-2024 |  |
| mechanical.mass_dry | OP-1 | 4.31 | kg | REPORTED | SRC-L3H-LHX-SPECSHEET-2024 |  |
| nozzle.area_ratio | OP-1 | 300 | :1 | INFERRED | SRC-L3H-LHX-SPECSHEET-2024 | label read as area ratio; not defined in summary |
| nozzle.area_ratio | OP-2 | 164 | :1 | INFERRED | SRC-L3H-LHX-SPECSHEET-2024 |  |
| performance.thrust_vac |  | 490 | N | REPORTED | SRC-IAC10-AJHIPAT | 'nominal thrust of 490-Newtons' |
| mechanical.mass_dry | OP-1 | 4.31 | kg | SECONDARY_CLAIM | SRC-SATCATALOG-R4D11 |  |
| performance.pc |  | 100.5 | psi | SECONDARY_CLAIM | SRC-WIKI-R4D | R-4D family, not -11 specific |
| propellants.pair |  | NTO/MMH |  | SECONDARY_CLAIM | SRC-WIKI-R4D | family |

**Topology:** 2 nodes, 0 edges; evidence: INFERRED 2. Completeness: Pressure-fed spacecraft engine; feed/pressurization belong to spacecraft. No schematic sourced.

**Schema breakers:**
- Thrust class name (490 N) vs dash-number variants with differing thrust/Isp; propellant MON-3 vs N2O4 variants (expected; unverified).
- Same designation with alternative nozzle area ratios (164:1 vs 300:1) giving different Isp and mass - nozzle configuration must be a variant dimension or operating point.
- Thrust given as a range (378-511 N) rather than a point.

**Missing:** 18 field groups (ACCESS_BLOCKED 18): performance.thrust_sl, performance.pc, performance.isp_sl, propellants.mixture_ratio, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.gimbal, history.first_flight, identity.manufacturer_current, materials.chamber

## Raptor 2 — `ENG-US-RAPTOR-2`

**Scope.** Raptor 2 sea-level engine (Super Heavy / Starship). Raptor Vacuum 2 values recorded only as ambiguous notes. Excludes Raptor 1 and Raptor 3.

**Architecture (master list).** LOX / LCH4; pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` rated, sea level (as quoted in SpaceX R2->R3 comparison)

**Assertions:** 8 (REPORTED 4, SECONDARY_CLAIM 4). Full list in [data/anchors/ENG-US-RAPTOR-2.json](data/anchors/ENG-US-RAPTOR-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 230 | tf | REPORTED | SRC-SPACEX-UPDATES | 'from 230 tf (507,000 lbf)' baseline in a Raptor 3 comparison; sibling flagged summary ambiguity; relayed via sibling l… |
| performance.thrust_sl | OP-1 | 507000 | lbf | REPORTED | SRC-SPACEX-UPDATES | relayed via sibling log |
| mechanical.mass_dry |  | 1630 | kg | REPORTED | SRC-SPACEX-UPDATES | 'SL mass 1,525 kg from 1,630 kg' -- 1,630 kg read as Raptor 2; dry vs wet not stated; relayed via sibling log |
| propellants.mixture_ratio | OP-1 | 3.6 | O/F | SECONDARY_CLAIM | SRC-WIKI-RAPTOR | family-level |
| performance.pc | OP-1 | 330 | bar | SECONDARY_CLAIM | SRC-WIKI-RAPTOR | family-level; CF-R2-4 |
| performance.thrust_sl | OP-1 | 2256 | kN | SECONDARY_CLAIM | SRC-WIKI-RAPTOR | = 230 tf |

**Topology:** none extracted.

**Schema breakers:**
- Rating quoted in metric tonnes-force (tf) by manufacturer; unit system must preserve it.
- Values often published only as deltas in a successor comparison (R2 -> R3), so provenance attaches to the successor's announcement.
- Rapid block evolution under one name (Raptor 1/2/3) with incompatible values.

**Missing:** 19 field groups (ACCESS_BLOCKED 19): performance.thrust_vac, performance.pc, performance.isp_sl, performance.isp_vac, performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.area_ratio, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.gimbal, history.first_flight, gg_preburner.fuel_rich_preburner, gg_preburner.ox_rich_preburner

## Raptor 3 — `ENG-US-RAPTOR-3`

**Scope.** Raptor 3 sea-level engine as announced on spacex.com updates and Starship specs page. Raptor 3 Vacuum (ENG-US-RAPTOR-3-VACUUM) values noted only in notes.

**Architecture (master list).** LOX / LCH4; pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` rated, sea level (manufacturer announcement)

**Assertions:** 9 (REPORTED 6, SECONDARY_CLAIM 3). Full list in [data/anchors/ENG-US-RAPTOR-3.json](data/anchors/ENG-US-RAPTOR-3.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 250 | tf | REPORTED | SRC-SPACEX-UPDATES |  |
| performance.thrust_sl | OP-1 | 551000 | lbf | REPORTED | SRC-SPACEX-UPDATES |  |
| performance.thrust_sl | OP-1 | 250 | tf | REPORTED | SRC-SPACEX-STARSHIP-SPECS | 551 klbf |
| mechanical.mass_dry |  | 1525 | kg | REPORTED | SRC-SPACEX-UPDATES | 'engine mass'; dry vs wet not stated |
| mechanical.diameter |  | 1.3 | m | REPORTED | SRC-SPACEX-STARSHIP-SPECS | variant implied |
| mechanical.length |  | 2.9 | m | REPORTED | SRC-SPACEX-STARSHIP-SPECS | 'height' |
| performance.thrust_sl | OP-1 | 2452 | kN | SECONDARY_CLAIM | SRC-WIKI-RAPTOR |  |
| propellants.mixture_ratio | OP-1 | 3.6 | O/F | SECONDARY_CLAIM | SRC-WIKI-RAPTOR | family-level |

**Topology:** none extracted.

**Schema breakers:**
- Ratings in tf; mass reduction quoted with vehicle-level savings (~1 t per engine incl. vehicle-side commodities) that must not be booked to the engine.
- Conflicting secondary 280 tf figure (CF-R2-3).

**Missing:** 9 field groups (NOT_REPORTED 8, UNKNOWN 1): performance.pc, performance.isp_sl, performance.isp_vac, performance.throttle_range, nozzle.area_ratio, pumps.*, turbines.*, preburners.*, performance.pc

## RL10A-4-2 — `ENG-US-RL10A-4-2`

**Scope.** RL10A-4-2 as flown on Atlas V Centaur (single- and dual-engine Centaur). Excludes RL10A-4 / A-4-1 (recorded only as table neighbours), RL10A-3-3A (family turbomachinery context only), RL10B-2 and RL10C.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_closed (INFERRED); chambers: 1

**Operating points.** `OP-1` Nominal full thrust, vacuum

**Assertions:** 17 (SECONDARY_CLAIM 12, REPORTED 4, INFERRED 1). Full list in [data/anchors/ENG-US-RL10A-4-2.json](data/anchors/ENG-US-RL10A-4-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-1 | 22300 | lbf | REPORTED | SRC-L3HARRIS-RL10-SPEC | RL10A-4-2 column of model table. |
| performance.thrust_vac | OP-1 | 99.1 | kN | SECONDARY_CLAIM | SRC-WIKI-RL10 | Variant table (row truncated in summary). |
| performance.thrust_vac | OP-1 | 10.115 | tonnes (force) | SECONDARY_CLAIM | SRC-NASA-SMA-SLR-DATASHEET | Third-party datasheet. |
| performance.thrust_vac_vehicle_avg_single | OP-1 | 22.9 | klbf | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS | Single-engine Centaur 'average thrust' - differs from 22.3 klbf; may be a different rating or averaging (CF-A42-2). |
| performance.thrust_vac_vehicle_total_dual | OP-1 | 44.6 | klbf | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS | Dual-engine Centaur total = 2 x 22.3 klbf (DERIVED consistency). |
| performance.isp_vac | OP-1 | 451.0 | s | REPORTED | SRC-L3HARRIS-RL10-SPEC |  |
| performance.isp_vac | OP-1 | 450.5 | s | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS |  |
| propellants.mixture_ratio | OP-1 | 5.5 | O/F | REPORTED | SRC-L3HARRIS-RL10-SPEC | Engine O/F. |
| propellants.mixture_ratio | OP-1 | 5.5 | O/F | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS |  |
| performance.pc | OP-1 | 32.1 bar (465 psi) | bar / psi | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS | abs/gauge not stated. Same value printed for RL10B-2 on the AIAA Delta page (suspicious). |
| nozzle.area_ratio |  | 85 | :1 | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-ATLAS |  |
| nozzle.area_ratio |  | 84:1 (A-4, A-4-1 rows); family infobox '84:1 or 280:1' | :1 | SECONDARY_CLAIM | SRC-WIKI-RL10 | A-4-2 row truncated - 84 not shown for A-4-2 itself. |
| nozzle.exit_diameter |  | 46 | in | REPORTED | SRC-L3HARRIS-RL10-SPEC | '46-inch nozzle diameter for the Atlas V version'. |
| pumps.family_context |  | RL10A-3-3A: two-stage fuel pump on turbine shaft; single-stage LOX pump gear-driven; desi… |  | INFERRED | SRC-NTRS-RL10A33A-MODEL | INFERRED applicability: values are for RL10A-3-3A, not A-4-2. Recorded only so the merge does not lose the lead; do not… |

**Topology:** 11 nodes, 12 edges; evidence: INFERRED 22, REPORTED_IN_TEXT 1. Completeness: Entire graph is INFERRED from RL10A-3-3A family sources; no A-4-2-specific flow source seen. Inlet/shutoff valves, igniter, interstage cooldown flows missing.

**Schema breakers:**
- Geared shaft: one turbine drives two pumps at different speeds (gear ratio a design parameter changed between family members, e.g. 2.5 -> 2.13 in throttling studies).
- Vehicle-level counts (single vs dual engine Centaur) quoted as engine 'thrust' in some sources (44.6 klbf).
- Family table values (A-4, A-4-1, A-4-2) share thrust (99.1 kN) and area ratio with truncation - easy to misassign.

**Missing:** 7 field groups (NOT_REPORTED 6, NOT_AUDITED 1): pumps.*, turbines.*, cooling.*, ignition_start.*, mechanical.mass_dry, nozzle.extension_material, performance.burn_time / restarts

## RL10B-2 — `ENG-US-RL10B-2`

**Scope.** RL10B-2 on the Delta IV (and Delta III) Delta Cryogenic Second Stage, with deployable carbon-carbon nozzle extension. Excludes RL10C-2/C-3 and modified 'B-2 without extension' builds.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; expander_closed (INFERRED); chambers: 1

**Operating points.** `OP-DEP` Nominal, vacuum, extension deployed

**Assertions:** 22 (SECONDARY_CLAIM 19, REPORTED 3). Full list in [data/anchors/ENG-US-RL10B-2.json](data/anchors/ENG-US-RL10B-2.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_vac | OP-DEP | 24750 | lb | REPORTED | SRC-ULA-DIV-INAUGURAL | Delta IV inaugural-launch paper. |
| performance.thrust_vac | OP-DEP | 24750 | lbf | REPORTED | SRC-ULA-DIV-GPSIIISV02 | Independent ULA booklet. |
| performance.thrust_vac | OP-DEP | 24740 | lb | SECONDARY_CLAIM | SRC-SPACELINE-DIV |  |
| performance.thrust_vac | OP-DEP | 110.1 kN (24,800 lbf) | kN | SECONDARY_CLAIM | SRC-WIKI-RL10 |  |
| performance.isp_vac | OP-DEP | 465.5 | s | SECONDARY_CLAIM | SRC-NAP-11780 | NAP report text (Tier B, values SECONDARY because NAP is not the originator). |
| performance.isp_vac | OP-DEP | 466.5 | s | SECONDARY_CLAIM | SRC-NAP-11780 | NAP comparison table. |
| performance.isp_vac | OP-DEP | 465.5 | s | SECONDARY_CLAIM | SRC-WIKI-RL10 |  |
| performance.isp_vac_stage_DCSS_DeltaIII |  | 462 | s | SECONDARY_CLAIM | SRC-WIKI-DCSS | Delta III DCSS listing - stage/engine ambiguity. |
| performance.pc | OP-DEP | 633 | psi | SECONDARY_CLAIM | SRC-NAP-11780 | NAP text 'nominally'. |
| performance.pc | OP-DEP | 644 | psia | SECONDARY_CLAIM | SRC-NAP-11780 | NAP comparison table. |
| performance.pc | OP-DEP | 32.1 bar (465 psi) | bar | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-DELTA | Identical to AIAA's RL10A-4-2 value - likely copy error. |
| propellants.mixture_ratio | OP-DEP | 5.88 | O/F | SECONDARY_CLAIM | SRC-WIKI-RL10 |  |
| nozzle.area_ratio | OP-DEP | 285 | :1 | SECONDARY_CLAIM | SRC-AIAA-VEHGUIDE-DELTA |  |
| nozzle.area_ratio | OP-DEP | 285 | :1 | SECONDARY_CLAIM | SRC-NAP-11780 | Two independent secondary sources agree. |
| nozzle.extension_type |  | translating (extendible) carbon-carbon nozzle extension |  | REPORTED | SRC-ULA-DIV-INAUGURAL | 'extendible nozzle designed for boost-phase environments and longer burns'; C-C per Wikipedia DCSS. |
| nozzle.extension_construction |  | three cones, Novoltex / Sepcarb carbon-carbon |  | SECONDARY_CLAIM | SRC-IAC-2018-43630 | Attribution between IAC metadata and Wikipedia 'Nozzle extension' inferred. |
| nozzle.extension_supplier |  | Airbus Safran Launchers (extension); Aerojet Rocketdyne retained Nozzle Extension Deploym… |  | SECONDARY_CLAIM | SRC-IAC-2018-43630 | Era of this supplier arrangement (2018 paper) may post-date early B-2 production; unverified. |
| nozzle.extension_length |  | nearly 100 | in | SECONDARY_CLAIM | SRC-IAC-2018-43630 |  |
| nozzle.exit_diameter | OP-DEP | just over 84 | in | SECONDARY_CLAIM | SRC-IAC-2018-43630 |  |
| mechanical.mass_dry |  | 301 kg (664 lb) | kg | SECONDARY_CLAIM | SRC-WIKI-RL10 |  |
| mechanical.mass_dry |  | 277 | kg | SECONDARY_CLAIM | SRC-WIKI-RL10 | Older Wikipedia revision (mirror). |
| mechanical.gimbal_actuation |  | electro-mechanical gimbaling |  | SECONDARY_CLAIM | SRC-WIKI-RL10 | AIAA Delta page lists 'hydraulic nozzle gimbal' at stage level (CF-B2-4). |

**Topology:** 4 nodes, 1 edges; evidence: INFERRED 3, REPORTED_IN_TEXT 2. Completeness: Feed/turbomachinery not documented in summaries; RL10 family expander topology (see RL10A-4-2 anchor) presumably applies [BG].

**Schema breakers:**
- Deployable nozzle extension: geometry (area ratio, length, exit diameter) differs between stowed and deployed states within one flight.
- Extension and its deployment system have different suppliers than the engine core.
- Same designation later modified (extension removed, new igniter) for other uses - configuration not captured by designation.

**Missing:** 5 field groups (NOT_REPORTED 4, NOT_AUDITED 1): pumps.* / turbines.*, cooling.*, ignition_start.*, nozzle.area_ratio_stowed, performance.restarts / burn_time

## RS-68A — `ENG-US-RS-68A`

**Scope.** RS-68A as described on the Aerojet Rocketdyne/L3Harris RS-68A data sheet (Delta IV / Delta IV Heavy). Excludes baseline RS-68 and RS-68B (Ares V study). OP-1 = 100%/full power level as tabulated; the sheet's second, unlabelled column is NOT interpreted.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; gas_generator (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-1` data-sheet primary column (full power; label not seen); `OP-2` data-sheet second column (unlabelled; likely minimum power level - INFERRED)

**Assertions:** 23 (REPORTED 17, SECONDARY_CLAIM 6). Full list in [data/anchors/ENG-US-RS-68A.json](data/anchors/ENG-US-RS-68A.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| performance.thrust_sl | OP-1 | 705000 | lbf | REPORTED | SRC-L3H-RS68A-DS | '705K lbf' as printed |
| performance.thrust_vac | OP-1 | 800000 | lbf | REPORTED | SRC-L3H-RS68A-DS | '800K lbf' |
| performance.pc | OP-1 | 1580 | psia | REPORTED | SRC-L3H-RS68A-DS | location (injector face vs stagnation) not stated; see CF-R2-1 |
| performance.isp_vac | OP-1 | 411 | s | REPORTED | SRC-L3H-RS68A-DS |  |
| performance.isp_sl | OP-1 | 362 | s | REPORTED | SRC-L3H-RS68A-DS |  |
| propellants.mixture_ratio | OP-1 | 5.97 | O/F | REPORTED | SRC-L3H-RS68A-DS | engine vs chamber convention not stated |
| nozzle.area_ratio | OP-1 | 21.5 | :1 | REPORTED | SRC-L3H-RS68A-DS |  |
| nozzle.area_ratio | OP-1 | 21.5 | :1 | SECONDARY_CLAIM | SRC-WIKI-RS68 |  |
| performance.thrust_sl | OP-1 | 3137 | kN | SECONDARY_CLAIM | SRC-WIKI-RS68 | = 705,000 lbf |
| performance.pc | OP-1 | 1488 | psi | SECONDARY_CLAIM | SRC-WIKI-RS68 | 10.26 MPa; conflicts with data sheet (CF-R2-1) |
| performance.thrust_vac | OP-2 | 412000 | lbf | REPORTED | SRC-L3H-RS68A-DS | column meaning not seen |
| performance.thrust_sl | OP-2 | 318000 | lbf | REPORTED | SRC-L3H-RS68A-DS |  |
| performance.pc | OP-2 | 820 | psia | REPORTED | SRC-L3H-RS68A-DS |  |
| propellants.mixture_ratio | OP-2 | 5.99 | O/F | REPORTED | SRC-L3H-RS68A-DS |  |
| nozzle.ablative_construction |  | ablative nozzle with increased-duration capability (RS-68A upgrade item) |  | REPORTED | SRC-NTRS-20090028723 | liner material not stated; chamber is regen-cooled per NAS (baseline) |
| turbines.seals |  | redesigned turbine seals reduce helium usage pre-launch and in flight |  | REPORTED | SRC-NTRS-20090028723 |  |

**Topology:** 9 nodes, 4 edges; evidence: REPORTED_IN_TEXT 9, INFERRED 4. Completeness: Component list from NAS (baseline RS-68) + RS-68A upgrade slide; no schematic seen. Turbine series/parallel, valves, regen path, HEX function all missing.

**Schema breakers:**
- Delta IV Heavy RS-68A vs single-stick Delta IV RS-68 vs RS-68 throttle-setting conventions (expected; unverified).
- Data sheet tabulates two operating columns; one unlabelled - operating points must be first-class.
- Helium spin-start and helium usage are engine-plus-ground/vehicle features (subsystem ambiguous).
- Roll control via vectored GG exhaust: turbine exhaust has a control function, not just disposal.

**Missing:** 17 field groups (ACCESS_BLOCKED 17): performance.mdot_total, performance.throttle_range, performance.burn_time, thrust_chamber.material, thrust_chamber.throat_diameter, nozzle.extension_material, injector.type, cooling.method, ignition_start.method, control.valves, mechanical.mass_dry, mechanical.gimbal, identity.parent_designation, pumps.LOX_TPA.*, pumps.LH2_TPA.*, turbines.*, gas_generators.GG.*

## RS-25D — `ENG-US-SSME-BLOCK-II`

**Scope.** SSME Block II (Block IIA + Pratt & Whitney HPFTP), final Shuttle flight configuration; the 'RS-25D' label for it is [BG] except that Wikipedia uses RS-25D for the dry-mass value. Includes the 14+ RS-25D engines adapted for SLS only where a source (L3Harris sheet, NASA SLS fact sheets) gives values for that adaptation: flagged in notes. Excludes Phase I/II, Block I, Block IIA-only rows (recorded only as comparison notes) and RS-25E.

**Architecture (master list).** LOX / LH2; pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM); chambers: 1

**Operating points.** `OP-RPL` 100% RPL (rated power level, original design reference); `OP-104.5` 104.5% RPL ('NPL' nominal power level for Shuttle); `OP-109` 109% RPL (FPL on Shuttle; nominal on SLS)

**Assertions:** 62 (SECONDARY_CLAIM 35, REPORTED 27). Full list in [data/anchors/ENG-US-SSME-BLOCK-II.json](data/anchors/ENG-US-SSME-BLOCK-II.json).

| Field | OP | Value | Unit | Status | Source | Note |
|---|---|---|---|---|---|---|
| propellants.oxidizer |  | LOX |  | REPORTED | SRC-L3HARRIS-RS25-SPEC | Sheet lists 'Oxygen pump discharge'. |
| propellants.fuel |  | LH2 |  | REPORTED | SRC-L3HARRIS-RS25-SPEC | Sheet lists 'Hydrogen pump discharge'. |
| propellants.mixture_ratio |  | 6.03 | O/F | REPORTED | SRC-L3HARRIS-RS25-SPEC | Engine O/F per sheet; SLS-supplied configuration; power level not stated. |
| propellants.mixture_ratio |  | 6.0 | O/F | REPORTED | SRC-L3HARRIS-RS25-WEB | Rounded web value. |
| propellants.mixture_ratio_main_chamber |  | 6 lb oxidizer to 1 lb fuel in main combustion chamber | lb/lb | SECONDARY_CLAIM | SRC-IBIBLIO-SSMEOVERVIEW | Summary text from an SSME overview; attribution among co-listed docs inferred. Main-chamber vs engine O/F convention no… |
| performance.thrust_vac | OP-109 | 512300 | lbf | REPORTED | SRC-L3HARRIS-RS25-SPEC | In vacuum at 109% (SLS-supplied configuration). |
| performance.thrust | OP-109 | 512000 | lbf | REPORTED | SRC-NASA-RS25-FS2015 | Carried from round 1; condition not shown in excerpt. |
| performance.thrust | OP-104.5 | 491000 | lbf | REPORTED | SRC-NASA-RS25-WEB | Carried from round 1; reference condition not stated (analyst [BG]: vacuum). |
| performance.thrust_sl | OP-104.5 | 390000 | lb | REPORTED | SRC-NASA-SSME-NPL-DOC | '390,000 pounds nominal power level (NPL) or 104.5 percent RPL' at sea level; which NASA doc among co-listed hits is in… |
| performance.pc | OP-RPL | 2747 | psia | REPORTED | SRC-IBIBLIO-SSMEOVERVIEW | 'approximately'; main combustion chamber; injector-face vs stagnation not stated. |
| performance.pc | OP-104.5 | 2870 | psia | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Block II row of block-comparison table; also ~2,870 psia in SSME overview. |
| performance.pc | OP-104.5 | 2870 | psia | REPORTED | SRC-IBIBLIO-SSMEOVERVIEW | 'approximately 2,870 psia' (independent second source). |
| performance.pc | OP-109 | 2994 | psia | REPORTED | SRC-L3HARRIS-RS25-SPEC | Spec-sheet chamber pressure (SLS configuration). |
| performance.pc | OP-109 | 2994 | psia | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Table row labelled Block IIA at 109% (Block II 109% Pc not given in summary). |
| performance.throttle_range |  | 67-109 | % RPL | REPORTED | SRC-L3HARRIS-RS25-SPEC | SLS-supplied configuration. |
| turbines.HPFT.discharge_temperature | OP-104.5 | 1615 | degR | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Block II row; summary warns of jumbled extraction (a 1601 R value also appears, labelled Block I or IIA). |
| turbines.HPFT.discharge_temperature | OP-109 | 1638 | degR | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Block II at 109%. |
| turbines.HPOT.discharge_temperature | OP-104.5 | 1223 | degR | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Block II at 104.5%. |
| turbines.HPOT.discharge_temperature | OP-109 | 1246 | degR | REPORTED | SRC-NASA-HOPSON-STS104-FRR-2001 | Block II at 109%. |
| pumps.HPFTP.discharge_pressure |  | 6276 | psia | REPORTED | SRC-L3HARRIS-RS25-SPEC | 'Hydrogen Pump Discharge'; power level not stated (probably 109%). |
| pumps.HPOTP.discharge_pressure |  | 7268 | psia | REPORTED | SRC-L3HARRIS-RS25-SPEC | 'Oxygen Pump Discharge'; which HPOTP stage (main pump vs preburner boost pump) not stated; magnitude suggests the prebu… |
| pumps.HPFTP.vendor |  | Pratt & Whitney (Block II) |  | SECONDARY_CLAIM | SRC-SFN-SSMEBLOCK2-2001 |  |
| pumps.HPFTP.construction |  | cast housing (weld elimination), integral shaft/disk, thin-wall blades, ceramic bearings |  | SECONDARY_CLAIM | SRC-SFN-SSMEBLOCK2-2001 |  |
| pumps.HPFTP.mass_delta |  | +300 lb (135 kg) vs previous pump | lb | SECONDARY_CLAIM | SRC-SFN-SSMEBLOCK2-2001 |  |
| pumps.HPFTP.speed_rpm |  | 36200 | rpm | SECONDARY_CLAIM | SRC-FORUM-BITOG-PWHPFTP | Forum quoting P&W website; operating point not stated. |
| pumps.HPFTP.power |  | 76000 | hp | SECONDARY_CLAIM | SRC-SFN-SSMEBLOCK2-2001 | 'turbopumps each transmit 76,000 horsepower to deliver liquid hydrogen'; news source among co-listed hits not distingui… |
| pumps.HPOTP.power |  | 26800 | hp | SECONDARY_CLAIM | SRC-SFN-SSMEBLOCK2-2001 | Same sentence as HPFTP power. |
| pumps.HPOTP.configuration |  | two single-stage centrifugal pumps (main pump + preburner pump) on a common shaft, two-st… |  | SECONDARY_CLAIM | SRC-WIKI-RS25 | Generic SSME description; Block II uses the P&W ATD HPOTP whose detail may differ. |
| pumps.HPOTP_main.discharge_pressure |  | 4350 | psi | SECONDARY_CLAIM | SRC-WIKI-RS25 | 420 -> 4,350 psi; operating point/block not stated. |
| pumps.HPOTP.speed_rpm |  | 28120 | rpm | SECONDARY_CLAIM | SRC-WIKI-RS25 | 'approximately'; block not stated. |
| pumps.HPOTP.power |  | 23260 | hp | SECONDARY_CLAIM | SRC-WIKI-RS25 | 17.34 MW; conflicts with 26,800 hp news figure (CF-RS-5). |
| pumps.LPOTP.type |  | axial-flow pump driven by six-stage turbine powered by high-pressure LOX from the HPOTP |  | SECONDARY_CLAIM | SRC-WIKI-RS25 | Hydraulic (liquid) turbine drive. |
| pumps.LPOTP.speed_rpm |  | 5150 | rpm | SECONDARY_CLAIM | SRC-WIKI-RS25 | approximately |
| pumps.LPOTP.pressure_rise |  | 100 -> 420 | psi | SECONDARY_CLAIM | SRC-WIKI-RS25 | 0.7 -> 2.9 MPa |
| pumps.LPFTP.type |  | axial-flow pump driven by two-stage turbine powered by gaseous hydrogen |  | SECONDARY_CLAIM | SRC-WIKI-RS25 |  |
| pumps.LPFTP.speed_rpm |  | 16185 | rpm | SECONDARY_CLAIM | SRC-WIKI-RS25 | approximately |
| pumps.LPFTP.pressure_rise |  | 30 -> 276 | psia | SECONDARY_CLAIM | SRC-WIKI-RS25 |  |
| preburners.count |  | 2 |  | SECONDARY_CLAIM | SRC-IBIBLIO-SSMEOVERVIEW | 'Two preburners burn a fuel rich mixture to power the HPFTP and HPOTP turbines'. |
| preburners.FPB.rich_side |  | fuel-rich |  | SECONDARY_CLAIM | SRC-IBIBLIO-SSMEOVERVIEW |  |
| preburners.OPB.rich_side |  | fuel-rich |  | SECONDARY_CLAIM | SRC-IBIBLIO-SSMEOVERVIEW |  |

(14 more technical assertions in the JSON.)

**Topology:** 25 nodes, 32 edges; evidence: REPORTED_IN_TEXT 50, INFERRED 7. Completeness: Missing: main fuel valve, chamber coolant valve, fuel/oxidizer bleed and purge circuits, ASIs, heat-exchanger supply source and GOX tank-pressurization line, HGM fuel/ox side split, nozzle-coolant return path into MCC/HGM, LPOTP turbine discharge return, recirculation/start lines. No schematic was viewed; graph is from text summaries only.

**Schema breakers:**
- Three operating points (100/104.5/109% RPL) with different Pc/temperatures; the % scale is relative to a historic rating, not to the variant's own nominal.
- Four turbopumps with different drive media: two hot-gas turbines (fuel-rich preburner gas), one GH2 turbine (LPFTP, driven by regen-heated hydrogen) and one liquid-LOX hydraulic turbine (LPOTP).
- HPOTP has two pumps on one shaft (main + preburner boost pump) with different discharge pressures; a single 'ox pump discharge pressure' field is ambiguous (7,268 vs 4,350 psi).
- Two preburners, both fuel-rich, each tied to one turbopump; preburner LOX flow controlled by two separate valves with distinct control roles (MR vs power level).
- Hot gas manifold is both a structural member and a flow element; turbine exhaust becomes the main injector's fuel feed (closed cycle).
- Block-level change of a single component vendor (P&W HPFTP) creates a new variant without changing designation in many sources (Block II vs RS-25D naming).
- Same physical engines later re-rated (SLS 109% nominal) - operating envelope depends on vehicle.
- Engine-supplied vehicle functions: fuel-tank pressurization gas tap from LPFTP turbine discharge; GOX heat exchanger feeding pogo accumulator / tank.

**Missing:** 10 field groups (NOT_REPORTED 9, NOT_AUDITED 1): pumps.HPFTP.speed_rpm (Tier A), preburners.*.temperature, preburners.*.mixture_ratio, injector.main.element_count, nozzle.exit_diameter / thrust_chamber.throat_diameter, nozzle.tube_count / steerhorn, performance.isp_vac / isp_sl, history.block_II_first_flight, ignition_start.ASI, pressurization.*
