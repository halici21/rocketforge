# DB-0 — Global liquid rocket engine family master list

A **best-effort, publicly documented** inventory of liquid-propellant rocket
engines, grouped by country, then family, then variant. It is a research map,
not a production database and not a claim of completeness. The machine-readable
form is [data/engines.json](data/engines.json) (with
[data/engine_inventory.csv](data/engine_inventory.csv),
[data/families.json](data/families.json) and
[data/aliases.json](data/aliases.json)); this page is generated from it.

**How to read a row.**
- **ID** is the stable DB-0 candidate id (`ENG-<country>-<designation>`). The
  country prefix is the one the discovering branch used. Soviet-era engines
  appear as `ENG-SU-…` or `ENG-RU-…`; this inconsistency is cosmetic, it is
  recorded, and DB-1 should decide the convention (see COVERAGE_GAPS.md). Merged
  duplicate ids are kept in each record's `former_ids`.
- **Feed; cycle (evidence)** uses the DB-0 vocabulary
  ([ENGINE_ARCHITECTURE_TAXONOMY.md](ENGINE_ARCHITECTURE_TAXONOMY.md)). The
  evidence status says how the cycle got there: `REPORTED` (a named source
  states it), `SECONDARY_CLAIM` (only a Tier D/E source states it), `INFERRED`
  (reasoned by the analyst, for example from the propellant pair or era), or
  `UNKNOWN`. **An inferred cycle is a hypothesis, not data.**
- **Evidence** gives the record's state. `placeholder` means the identity came
  from the research brief or analyst background knowledge and no source was
  found in DB-0 — it is a checklist entry to verify, not a confirmed engine
  record. `n values (k REPORTED)` counts the sourced key values; every value was
  read from a search-result summary, never from the document itself.
- **Key sources** lists up to three source ids, best tier first (registry:
  [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md)).
- `?` in a propellant column means the propellant was not recorded for that
  record. It does not mean unknown to the world.

Family ≠ variant: every row is a variant (or a configuration where the source
draws that line). Family-level values are never copied down to variants.
Engine modules (several engines sold under one designation, e.g. YF-21) and
propulsion systems (e.g. RD-0212 = RD-0213 + RD-0214) are recorded as such in
their notes and are flagged in COVERAGE_GAPS.md for DB-1 to model as their own
entity type.

## Counts

| Primary country code | Variant records |
|---|---|
| US | 246 |
| SU | 114 |
| CN | 52 |
| DE | 33 |
| FR | 26 |
| GB | 22 |
| IN | 19 |
| JP | 19 |
| RU | 8 |
| UA | 7 |
| IR | 5 |
| AR | 4 |
| KP | 4 |
| KR | 4 |
| BR | 3 |
| ES | 3 |
| SE | 3 |
| IT | 2 |
| EG | 1 |
| EU | 1 |

| Status | Records |
|---|---|
| retired | 285 |
| operational | 129 |
| development | 66 |
| cancelled | 61 |
| unknown | 25 |
| experimental | 5 |
| proposed | 5 |

| Cycle value (as recorded) | Records |
|---|---|
| gas_generator | 149 |
| none_pressure_fed | 133 |
| UNKNOWN | 126 |
| staged_combustion_ox_rich | 70 |
| separate_turbine_working_fluid | 26 |
| expander_closed | 23 |
| staged_combustion_fuel_rich | 16 |
| full_flow_staged_combustion | 11 |
| expander_bleed | 7 |
| other | 5 |
| electric_pump | 5 |
| tap_off | 5 |

| Cycle evidence status | Records |
|---|---|
| INFERRED | 227 |
| SECONDARY_CLAIM | 149 |
| UNKNOWN | 138 |
| REPORTED | 62 |

## Americas

### United States (US) — 246 variant records

#### FAM-ABL-E2 — ABL Space Systems, ABL Space Systems (now Long Wall)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-E2 | E2 | — / — | ? / retired | booster, upper_stage | LOX / RP-1 / Jet-A | pump_fed_turbopump; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-SFN-RS1-2023, SRC-WIKI-RS1 |
| ENG-US-E2-VACUUM | E2 Vacuum | E2 / vacuum_variant | ? / retired | upper_stage | LOX / RP-1 / Jet-A | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-WIKI-RS1 |

#### FAM-AEON — Relativity Space

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AEON-1 | Aeon 1 | — / — | ? / retired | booster, upper_stage | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 5 values (0 REPORTED) | SRC-AIRPORTTECH-TERRAN1, SRC-SFN-TERRAN1-2023, SRC-WIKI-AEONR |
| ENG-US-AEON-R | Aeon R | — / — | ? / development | booster | LOX / LCH4 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (2 REPORTED) | SRC-RELATIVITY-PR-2023-04-12, SRC-RELATIVITY-PR-2025-03-07, SRC-WIKI-AEONR |
| ENG-US-AEON-VAC | Aeon Vac | Aeon 1 / vacuum_variant | ? / retired | upper_stage | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-AIRPORTTECH-TERRAN1, SRC-SPACEBUCKET-AEON |
| ENG-US-AEON-VAC-TERRAN-R | Aeon Vac (Terran R second stage) | Aeon R / vacuum_variant | ? / development | upper_stage | LOX / LCH4 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-RELATIVITY-PR-2023-04-12, SRC-RELATIVITY-PR-2025-03-07, SRC-WIKI-AEONR |

#### FAM-AETHER — Astra

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AETHER | Aether | — / — | flown 2020-2022 / retired | upper_stage | LOX / RP-1 (not confirmed) | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-ASTRA-ROCKET |

#### FAM-AGILE — Agile Space Industries

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-A110 | A110 | — / — | ? / operational | rcs | NOT_REPORTED / NOT_REPORTED | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-3DADEPT-AGILE |
| ENG-US-A2200 | A2200 | — / — | ? / development | lander_descent, spacecraft_main | NOT_REPORTED / NOT_REPORTED | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-3DADEPT-AGILE, SRC-DEFENSEDAILY-AGILE |
| ENG-US-DS250 | DS250 | — / — | ? / development | orbital_maneuver | NOT_REPORTED / NOT_REPORTED | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-METALAM-AGILE-NYX |

#### FAM-AJ10 — Aerojet, Aerojet (Aerojet-General), Aerojet Rocketdyne (refurbished at NASA WSTF), Aerojet-General

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AJ10-101 | AJ10-101 | AJ10-37 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-104 | AJ10-104 | AJ10-101 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-104D | AJ10-104D | AJ10-104 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-118 | AJ10-118 | AJ10-101 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-118A | AJ10-118A | AJ10-118 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-118D | AJ10-118D | AJ10-118 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-118E | AJ10-118E | AJ10-118 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-118F | AJ10-118F | AJ10-118 / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-AJ10-118K | AJ10-118K | AJ10-118F / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-SPACENEWS-AJ10118K, SRC-WIKI-DELTAK |
| ENG-US-AJ10-137 | AJ10-137 | — / derivative | dev 1962-; flown 1966-1975 / retired | orbital_maneuver, spacecraft_main | N2O4 / Aerozine-50 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-APOLLO9-SPS-FFE, SRC-DTIC-AD0368743, SRC-JAXA-TND7375 |
| ENG-US-AJ10-138 | AJ10-138 | AJ10-118 / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-AJ10-190 | AJ10-190 | — / derivative | flown 1981-2011 / retired | orbital_maneuver | N2O4 (MON-3 per some sources) / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 8 values (0 REPORTED) | SRC-NTRS-19740026212, SRC-WIKI-OMS |
| ENG-US-AJ10-37 | AJ10-37 | — / baseline | ? / retired | upper_stage | HNO3 (WIFNA per background) / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-AJ10-42 | AJ10-42 | AJ10-37 / derivative | ? / retired | upper_stage | HNO3 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AJ10 |
| ENG-US-OMS-E-ORION-ESM | OMS-E (Orion ESM) | AJ10-190 / derivative | Artemis I 2022; Artemis II- / operational | spacecraft_main | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-DLA-ORION, SRC-ESA-BLOG-ART2ENG, SRC-ESA-ESMPROP |

#### FAM-ANDROMEDA — Stoke Space

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-ANDROMEDA | Andromeda | — / — | ? / development | upper_stage | LOX / LH2 | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-SPACECOM-STOKE-2026, SRC-SACRA-STOKE |

#### FAM-AR1 — Aerojet Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AR1 | AR1 | — / — | 2015 CDR milestone; qualification targeted 2019 / cancelled | booster | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-AR-AR1-CDR-2015, SRC-IAC17-AR1 |

#### FAM-ARCHIMEDES — Rocket Lab

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-NZ-ARCHIMEDES | Archimedes | — / baseline | first hot fire 2024-08-08; Neutron debut slipped to 2026 an… | booster | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 3 values (3 REPORTED) | SRC-RL-ARCH-BUILD, SRC-RL-ARCH-HOTFIRE-2024, SRC-RL-NEUTRON-PAGE |
| ENG-NZ-ARCHIMEDES-VACUUM | Archimedes Vacuum | Archimedes / vacuum_variant | stage-2 full-duration static fire reported (date not captur… | upper_stage | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 2 values (2 REPORTED) | SRC-RL-ARCH-BUILD, SRC-RL-NEUTRON-PAGE, SRC-SPACECOM-NEUTRON-2026 |

#### FAM-ARROWAY — Ursa Major

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-ARROWAY | Arroway | — / — | ? / development | booster | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-SATTODAY-ARROWAY-2022 |

#### FAM-BE-1 — Blue Origin

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BE-1 | BE-1 | — / baseline | ? / retired | experimental, test_bed | none(mono) / HTP | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-BLUE-ENGINES, SRC-WIKI-BE3 |

#### FAM-BE-2 — Blue Origin

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BE-2 | BE-2 | — / baseline | ? / retired | experimental, test_bed | HTP / kerosene | UNKNOWN; UNKNOWN | sourced; 1 values (1 REPORTED) | SRC-BLUE-ENGINES, SRC-WIKI-BE3 |

#### FAM-BE-3 — Blue Origin

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BE-3PM | BE-3PM | BE-3 / baseline | New Shepard; operational 2026-10 (status of New Shepard fli… | booster | LOX / LH2 | pump_fed_turbopump; tap_off (REPORTED) | sourced; 4 values (4 REPORTED) | SRC-BLUE-2013-BE3-RELEASE, SRC-BLUE-BE3-ACCEPT, SRC-BLUE-BE3-DEBUT |
| ENG-US-BE-3U | BE-3U | BE-3PM / vacuum_variant | New Glenn GS2; first flight 2025 (NG-1, analyst knowledge) … | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (REPORTED) | sourced; 9 values (9 REPORTED) | SRC-BLUE-ENGINES, SRC-BLUE-ENGINES-PAGE, SRC-BLUE-NEWGLENN-PAGE |

#### FAM-BE-4 — Blue Origin

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BE-4 | BE-4 | — / baseline | development from 2012; flown on Vulcan and New Glenn (first… | booster | LOX / LNG | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 9 values (9 REPORTED) | SRC-BLUE-ENGINES, SRC-BLUE-ENGINES-PAGE, SRC-BLUE-NEWGLENN-PAGE |

#### FAM-BE-7 — Blue Origin

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BE-7 | BE-7 | — / baseline | in test (Blue Moon MK1/MK2 lander) / development | lander_descent | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; expander_closed (REPORTED) | sourced; 2 values (2 REPORTED) | SRC-BLUE-BE7-TEST, SRC-BLUE-ENGINES |

#### FAM-COBRA — Pratt & Whitney / Aerojet

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-COBRA | COBRA | — / — | 2000-2002 / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-CORPORAL — JPL / Firestone (Ryan built engines later) - manufacturer UNKNOWN in sources seen

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XF30L20000 | XF30L20000 | — / — | concept 1944; missile deployed 1950s / retired | missile | RFNA / aniline | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-CALTECH-THESIS310, SRC-FAS-CORPORAL, SRC-WIKI-CORPORALE |

#### FAM-CURIE — Rocket Lab

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-NZ-CURIE | Curie | — / baseline | ? / operational | kick_stage | NOT_REPORTED / NOT_REPORTED | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-CURIE, SRC-WIKI-ELECTRON |
| ENG-NZ-HYPERCURIE | HyperCurie | Curie / derivative | ? / operational | kick_stage, spacecraft_main | NOT_REPORTED / NOT_REPORTED | pump_fed_electric; electric_pump (REPORTED) | sourced; 3 values (1 REPORTED) | SRC-RL-PHOTON-DOC, SRC-WIKI-CURIE, SRC-WIKI-ELECTRON |

#### FAM-DELPHIN — Astra

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-DELPHIN | Delphin | — / — | 2012- (SALVO origin); flown 2020-2022 / retired | booster | LOX / RP-1 (kerosene; propellant not confirmed this session) | pump_fed_electric; electric_pump (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-ASTRA-R31-PRESSKIT, SRC-SFN-ASTRA-2021-08, SRC-SKYROCKET-ASTRA-R3 |

#### FAM-DRACO — SpaceX

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-DRACO | Draco | — / baseline | ? / operational | orbital_maneuver, rcs, spacecraft_main | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-WIKI-DRACO, SRC-WIKI-DRAGON2, SRC-UC-OLLI-DRAGON |
| ENG-US-SUPERDRACO | SuperDraco | Draco / derivative | ? / operational | other | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (1 REPORTED) | SRC-SPACEX-SUPERDRACO-QUAL-2014, SRC-WIKI-DRAGON2, SRC-WIKI-SUPERDRACO |

#### FAM-F-1 — Rocketdyne, Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-F-1 | F-1 | — / baseline | 1957 dev start; flown 1967-1973 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 15 values (0 REPORTED) | SRC-MSFC-SATURNV-FLIGHTMANUAL, SRC-AWESOMESTORIES-F1NASA, SRC-ENGINEHISTORY-F1 |
| ENG-US-F-1A | F-1A | F-1 / uprate | 1960s dev; never flown / cancelled | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-F1, SRC-WIKI2007-F1 |

#### FAM-FRONTIER-DSE — Frontier Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-FRONTIER-DSE | Frontier Deep Space Engine (DSE) / Peregrine main engine | — / — | ? / retired | lander_descent, spacecraft_main | MON-25 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-NASA-TALOS, SRC-AIRPORTTECH-PEREGRINE, SRC-SATNEWS-FRONTIER-2018 |

#### FAM-GEMINI-OAMS — Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-GEMINI-OAMS-100-LBF-THRUSTER | Gemini OAMS 100 lbf thruster | — / — | contract 1962; flown 1965-1966 / retired | orbital_maneuver, rcs | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NASM-OAMS, SRC-WIKI-OAMS |
| ENG-US-SE-6 | SE-6 | — / — | flown 1965-1966 / retired | rcs | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NASM-GEMRCS, SRC-NASM-OAMS, SRC-HA-SE6 |

#### FAM-GODDARD — Robert H. Goddard, Robert H. Goddard (Roswell, NM)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-GODDARD-1926-LIQUID-ROCKET-MOTOR | Goddard 1926 liquid rocket motor | — / — | 1921-1926 dev; flown 16 Mar 1926 / retired | experimental | LOX / gasoline | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-APS-GODDARD, SRC-NPS-GODDARD |
| ENG-US-GODDARD-P-SERIES-PUMP-FED-ENGINE | Goddard P-series pump-fed engine | — / — | Jan 1939 - Oct 1941 tests / retired | experimental | LOX / gasoline | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-CLARK-GODDARD, SRC-NASM-GODDARD-PUMP |

#### FAM-GR-AF-M315E — Aerojet Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-GR-1 | GR-1 | — / — | ? / experimental | rcs | none(mono) / AF-M315E (ASCENT, HAN-based) | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-NASA-GPIM-FACTSHEET, SRC-IAC15-31185, SRC-NTRS-20140016838 |
| ENG-US-GR-22 | GR-22 | — / — | ? / experimental | orbital_maneuver, rcs | none(mono) / AF-M315E (ASCENT, HAN-based) | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-NASA-GPIM-FACTSHEET, SRC-NTRS-20140016838, SRC-NTRS-20170001286 |

#### FAM-H-1 — Rocketdyne, Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-H-1 | H-1 | — / — | NOT_AUDITED / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 15 values (1 REPORTED) | SRC-NTRS-19650013470, SRC-NASM-H1, SRC-PURDUE-H1 |
| ENG-US-H-1-165K | H-1 (165K) | S-3D / baseline | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-GLOBALSEC-SATURNIB, SRC-WIKI-H1 |
| ENG-US-H-1-188K | H-1 (188,000 lbf rating) | H-1 / baseline | NOT_AUDITED / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 3 values (1 REPORTED) | SRC-NASA-ALSJ-CSM02, SRC-NTRS-19650013470, SRC-NASM-H1 |
| ENG-US-H-1-200K | H-1 (200,000 lbf rating) | H-1 / uprate | NOT_AUDITED / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-NTRS-19650013470, SRC-GLOBALSEC-SATURNIB, SRC-NASM-H1 |
| ENG-US-H-1-205K | H-1 (205,000 lbf rating) | H-1 / uprate | NOT_AUDITED / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 4 values (0 REPORTED) | SRC-NTRS-19650013470, SRC-GLOBALSEC-SATURNIB, SRC-NASM-H1 |

#### FAM-HADLEY — Ursa Major

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-DRAPER | Draper | Hadley / derivative | ? / development | missile, other | HTP / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-TECTONIC-DRAPER |
| ENG-US-HADLEY | Hadley | — / — | ? / operational | booster, experimental, other, upper_sta… | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-PAYLOAD-URSA-TACFI, SRC-SATTODAY-PHANTOM-URSA-2022 |
| ENG-US-HADLEY-VACUUM | Hadley (vacuum variant) | Hadley / vacuum_variant | ? / development | upper_stage | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-SPACENEWS-152328, SRC-ORBITCODEX-ROCKET4 |

#### FAM-IPD — Rocketdyne + Aerojet (USAF/NASA IHPRPT)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-IPD | IPD | — / test_article | 1990s-2006 / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; full_flow_staged_combustion (REPORTED) | sourced; 3 values (0 REPORTED) | SRC-AF-IPD-2006, SRC-NTRS-IPD-OTPCF, SRC-NTRS-IPD-WPB |

#### FAM-J-2 — Pratt & Whitney Rocketdyne (for NASA), Rocketdyne, Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-J-2 | J-2 | — / baseline | 1960 dev; flown 1966-1975 / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 21 values (8 REPORTED) | SRC-DTIC-AEDC-J2-SET, SRC-NASA-ALSJ-CSM02, SRC-NTRS-20100027318 |
| ENG-US-J-2S | J-2S | J-2 / development_config | 1965-1972 test / cancelled | development_config, experimental, upper… | LOX / LH2 | pump_fed_turbopump; tap_off (SECONDARY_CLAIM) | sourced; 10 values (5 REPORTED) | SRC-DTIC-AD0867628, SRC-DTIC-AD0874400, SRC-DTIC-AEDC-J2S-SET |
| ENG-US-J-2T-200K | J-2T-200K | J-2 / derivative | late 1960s test / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-J-2T-250K | J-2T-250K | J-2T-200K / uprate | ? / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-J-2X | J-2X | J-2 / derivative | 2006-2014 dev/test / cancelled | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 5 values (4 REPORTED) | SRC-NTRS-20080036837, SRC-NTRS-20090009149, SRC-NTRS-20120016414 |

#### FAM-KESTREL — SpaceX

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-KESTREL | Kestrel | — / baseline | flown 2006-2009 on Falcon 1 (flight dates per Falcon 1 hist… | upper_stage | LOX / RP-1 | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-KESTREL |
| ENG-US-KESTREL-2 | Kestrel 2 | Kestrel / derivative | ? / cancelled | upper_stage | LOX / RP-1 | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-KESTREL |

#### FAM-LANCE-PROPULSION — Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-P8E-9 | P8E-9 | — / — | 1960s-1992 / retired | missile | IRFNA / UDMH | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-LAUNCHER-E-2 — Launcher (acquired by Vast [BG])

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-E-2 | E-2 | — / — | ? / development | booster | LOX / RP-1 | pump_fed_turbopump; UNKNOWN (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-3DNATIVES-E2, SRC-CONTROL-E2-TEST, SRC-SPACENEWS-128063 |

#### FAM-LIGHTNING — Firefly Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LIGHTNING | Lightning | — / baseline | ? / operational | upper_stage | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; tap_off (REPORTED) | sourced; 3 values (3 REPORTED) | SRC-FIREFLY-ALPHA-PAGE, SRC-FIREFLY-FLTA004, SRC-FIREFLY-FLTA006 |

#### FAM-LINEAR-AEROSPIKE — Boeing Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-2200 | RS-2200 | XRS-2200 / derivative | 1990s / cancelled | booster, core | LOX / LH2 | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-RS2200 |
| ENG-US-XRS-2200 | XRS-2200 | — / — | 1996-2001 / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 9 values (1 REPORTED) | SRC-NTRS-19980174934, SRC-PURDUE-XRS2200, SRC-SFN-AEROSPIKE-1999 |

#### FAM-LM-APS — Bell Aerosystems (injector later by Rocketdyne)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LM-ASCENT-ENGINE | LM Ascent Engine | — / — | dev 1963-; flown 1969-1972 / retired | lander_ascent | N2O4 / Aerozine-50 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-NTRS-19730010173, SRC-NTRS-19740005391 |

#### FAM-LMDE — TRW (Space Technology Laboratories)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LMDE | LMDE | — / baseline | dev 1963-; flown 1969-1972 / retired | lander_descent | N2O4 / Aerozine-50 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 3 values (1 REPORTED) | SRC-MSC-05161-A15S4, SRC-NASA-A14DPSPERF, SRC-NASA-AER-DPS |

#### FAM-LR101 — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR101 | LR101 | — / — | 1957-2004 / retired | other | LOX / RP-1 | UNKNOWN; UNKNOWN | sourced; 3 values (1 REPORTED) | SRC-DTIC-AD0423340, SRC-ENGINEHISTORY-USSRC-ATLAS, SRC-NASM-ATLASVERNIER |

#### FAM-LR105 — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR105-NA-3 | LR105-NA-3 | — / baseline | ? / retired | missile, sustainer | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR105-NA-5 | LR105-NA-5 | LR105-NA-3 / derivative | ? / retired | missile, sustainer | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-ENGINEHISTORY-RPE05, SRC-RRS-LR105NA5 |
| ENG-US-LR105-NA-7 | LR105-NA-7 | LR105-NA-5 / derivative | ? / retired | sustainer | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-ASTRONAUTIX-LR105-7, SRC-WIKI-MA5 |

#### FAM-LR79-S-3 — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR79-NA-11 | LR79-NA-11 | LR79-NA-9 / derivative | ? / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR79-NA-13 | LR79-NA-13 | LR79-NA-11 / uprate | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR79-NA-9 | LR79-NA-9 | S-3D / stage_specific | ? / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-FLICKR-MB3, SRC-THISDAY-LR79NA9 |
| ENG-US-S-3D | S-3D | NAA 75-110 A-7 / derivative | 1955-1961 / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-NMUSAF-LR79, SRC-WIKI-PGM19, SRC-WIKI-S3D |

#### FAM-LR87 — Aerojet, Aerojet (Aerojet-General)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR87-AJ-11 | LR87-AJ-11 | LR87-AJ-9 / derivative | 1970s-2005 / retired | booster, core | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-ASTRONAUTIX-LR87 |
| ENG-US-LR87-AJ-11A | LR87-AJ-11A | LR87-AJ-11 / derivative | ? / retired | core | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR87-AJ-3 | LR87-AJ-3 | — / baseline | 1955-1965 / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-ASTRONAUTIX-LR87, SRC-ENGINEHISTORY-RPE06, SRC-HEROICRELICS-TITANI |
| ENG-US-LR87-AJ-5 | LR87-AJ-5 | LR87-AJ-3 / derivative | 1960s / retired | booster, missile | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 8 values (0 REPORTED) | SRC-ASTRONAUTIX-LR87, SRC-ENGINEHISTORY-RPE06, SRC-TMS-TITAN2 |
| ENG-US-LR87-AJ-7 | LR87-AJ-7 | LR87-AJ-5 / stage_specific | 1964-1966 / retired | booster | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-ASTRONAUTIX-LR87, SRC-ENGINEHISTORY-RPE06 |
| ENG-US-LR87-AJ-9 | LR87-AJ-9 | LR87-AJ-5 / derivative | 1960s / retired | booster | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR87-LH2 | LR87-LH2 | LR87-AJ-3 / test_article | late 1950s-1960 test / experimental | experimental | LOX / LH2 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-LR89 — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR89-NA-3 | LR89-NA-3 | — / baseline | ? / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR89-NA-5 | LR89-NA-5 | LR89-NA-3 / derivative | ? / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-ENGINEHISTORY-RPE05 |
| ENG-US-LR89-NA-6 | LR89-NA-6 | LR89-NA-5 / derivative | ? / retired | booster, missile | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR89-NA-7 | LR89-NA-7 | LR89-NA-6 / derivative | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 6 values (0 REPORTED) | SRC-ASTRONAUTIX-LR89-7, SRC-WIKI-ATLASG, SRC-WIKI-MA5 |

#### FAM-LR91 — Aerojet (Aerojet-General)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LR91-AJ-11 | LR91-AJ-11 | LR91-AJ-9 / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 7 values (0 REPORTED) | SRC-PURDUE-LR91AJ11, SRC-WIKI-LR91 |
| ENG-US-LR91-AJ-11A | LR91-AJ-11A | LR91-AJ-11 / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-LR91-AJ-3 | LR91-AJ-3 | — / baseline | 1959-1965 / retired | missile, upper_stage | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-WIKI-LR91, SRC-HMDB-LR91AJ3 |
| ENG-US-LR91-AJ-5 | LR91-AJ-5 | LR91-AJ-3 / derivative | ? / retired | missile, upper_stage | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-LR91 |
| ENG-US-LR91-AJ-7 | LR91-AJ-7 | LR91-AJ-5 / stage_specific | ? / retired | upper_stage | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-LR91 |
| ENG-US-LR91-AJ-9 | LR91-AJ-9 | LR91-AJ-5 / derivative | ? / retired | upper_stage | N2O4 / Aerozine-50 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-M-1 — Aerojet (Aerojet-General) / NASA Lewis

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-M-1 | M-1 | — / — | 1961-1965/66 / cancelled | booster, upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 3 values (1 REPORTED) | SRC-NASA-GRC-1966-C-03899, SRC-NASM-M1, SRC-WIKI-M1 |

#### FAM-MASTEN — Masten Space Systems

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BROADSWORD | Broadsword 25K | — / — | dev from Aug 2015; AFRL tests to 2019-12 / cancelled | booster, demonstrator, experimental | LOX / LCH4 | pump_fed_turbopump; expander_closed (REPORTED) | sourced; 3 values (2 REPORTED) | SRC-AFRL-BROADSWORD-2019, SRC-MASTEN-ENGINES, SRC-MECO-BROADSWORD-2017 |
| ENG-US-CYCLOPS | Cyclops-AL-3 | — / — | ? / retired | experimental, test_bed | LOX / isopropyl alcohol | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-WIKI-MASTEN |
| ENG-US-MACHETE | Machete | — / — | ? / cancelled | experimental, lander_descent, test_bed | NOT_REPORTED / MXP-351 | pressure_fed_unspecified; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-MECO-MXP351-2017 |
| ENG-US-SCIMITAR | Scimitar | — / — | ? / retired | test_bed | NOT_REPORTED / NOT_REPORTED | UNKNOWN; UNKNOWN | sourced; 1 values (1 REPORTED) | SRC-MASTEN-ENGINES |

#### FAM-MB-3 — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MB-3-1 | MB-3-1 | LR79-NA-9 / derivative | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-ASTRONAUTIX-LR79 |
| ENG-US-MB-3-2 | MB-3-2 | MB-3-1 / block_upgrade | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-MB-3-3 | MB-3-3 | MB-3-2 / block_upgrade | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-MERLIN — SpaceX

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MERLIN-1A | Merlin 1A | — / baseline | flown 2006-03-24 (failure) and 2007-03-21 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-SLR-F9-SMA, SRC-WIKI-MERLIN |
| ENG-US-MERLIN-1B | Merlin 1B | Merlin 1A / uprate | development c.2006-2007; not flown / cancelled | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-MERLIN |
| ENG-US-MERLIN-1C | Merlin 1C | Merlin 1A / derivative | regen version announced 2006; development complete 2007-11-… | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 6 values (3 REPORTED) | SRC-SPACEX-PR-M1C-2007, SRC-SLR-F9-SMA, SRC-SPACENEWS-2008-F1 |
| ENG-US-MERLIN-1C-FALCON-9-CONFIGURATION | Merlin 1C (Falcon 9 configuration) | Merlin 1C / stage_specific | Falcon 9 v1.0 flights 2010-2013 (dates not individually sou… | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 6 values (3 REPORTED) | SRC-SPACEX-PR-M1C-2007, SRC-SLR-F9-SMA |
| ENG-US-MERLIN-1C-VACUUM | Merlin 1C Vacuum | Merlin 1C / vacuum_variant | tested 2009 (PR 2009-03-10); first flight 2010-06-04 / reti… | upper_stage | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-SATTODAY-2009-MVAC, SRC-SLR-F9-SMA, SRC-WIKI-MERLIN |
| ENG-US-MERLIN-1D | Merlin 1D | Merlin 1C / derivative | announced c.2011 (JPC 2011 data); Falcon 9 v1.1 2013-2015 (… | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 10 values (2 REPORTED) | SRC-SPACEX-FUG-2025, SRC-SFN-2015-FT, SRC-SLR-F9-SMA |
| ENG-US-MERLIN-1D-BLOCK-5 | Merlin 1D Block 5 | Merlin 1D Full Thrust / block_upgrade | Block 5 from 2018 (analyst knowledge); operational 2026-10 … | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (1 REPORTED) | SRC-SPACEX-F9-PAGE, SRC-SPACEX-FUG-2025, SRC-WIKI-F9FT |
| ENG-US-MERLIN-1D-FULL-THRUST | Merlin 1D Full Thrust | Merlin 1D / block_upgrade | Falcon 9 FT (v1.2) from 2015 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-SF101-F9FT, SRC-SFN-2015-FT |
| ENG-US-MERLIN-1D-VACUUM | Merlin 1D Vacuum | Merlin 1D / vacuum_variant | Falcon 9 v1.1 onward; operational 2026-10 / operational | upper_stage | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 7 values (3 REPORTED) | SRC-SPACEX-F9-PAGE, SRC-SPACEX-FUG-2025, SRC-SFN-2015-FT |
| ENG-US-MERLIN-1D-VACUUM-SHORT-NOZZLE | Merlin 1D Vacuum (short nozzle) | Merlin 1D Vacuum / derivative | ? / operational | upper_stage | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-MERLIN |

#### FAM-MIRANDA — Firefly Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MIRANDA | Miranda | Reaver / derivative | component risk-reduction testing (date not captured) / deve… | booster | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; tap_off (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-FIREFLY-ECLIPSE-NG, SRC-FIREFLY-MIRANDA-RR |

#### FAM-MOOG-DST — Moog

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-DST-11H | DST-11H | — / — | ? / operational | rcs | MON / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (4 REPORTED) | SRC-MOOG-BIPROP-PAGE |
| ENG-US-DST-12 | DST-12 | — / — | ? / operational | rcs | MON / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 7 values (6 REPORTED) | SRC-MOOG-BIPROP-PAGE, SRC-SATNOW-DST12 |
| ENG-US-DST-13 | DST-13 | — / — | ? / operational | rcs | MON / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 6 values (6 REPORTED) | SRC-MOOG-BIPROP-PAGE |

#### FAM-MR-103 — Aerojet (Rocket Research Co. heritage, Redmond WA)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-103G | MR-103G | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-L3H-MONO-2023, SRC-SATCAT-MR103G |
| ENG-US-MR-103J | MR-103J | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-L3H-MONO-2023, SRC-L3H-MONO-2025 |

#### FAM-MR-104 — Aerojet (Rocket Research Co. heritage, Redmond WA), Aerojet Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-104 | MR-104 | — / — | ? / operational | orbital_maneuver, rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-L3H-MONO-2023 |
| ENG-US-MR-104G | MR-104G | MR-104 / derivative | qual 2018; flown 2014 (EFT-1, earlier config?)/2022 / opera… | rcs | none(mono) / N2H4 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-AJRD-PR-MR104G, SRC-DLA-ORION, SRC-NTRS-20140006053 |

#### FAM-MR-106 — Aerojet (Rocket Research Co. heritage, Redmond WA)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-106L | MR-106L | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-L3H-MONO-2025 |
| ENG-US-MR-106M | MR-106M | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-L3H-MONO-2025 |

#### FAM-MR-107 — Aerojet (Rocket Research Co. heritage, Redmond WA)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-107N | MR-107N | — / — | ? / retired | lander_descent | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-SDU-PHXPLUME, SRC-UA-PHXSPEC, SRC-PLANETARY-1034 |
| ENG-US-MR-107S | MR-107S | — / — | ? / operational | orbital_maneuver, rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-L3H-MONO-2025, SRC-SATCAT-MR107 |
| ENG-US-MR-107T | MR-107T | — / — | ? / operational | orbital_maneuver, rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-L3H-MONO-2025, SRC-SATCAT-MR107 |
| ENG-US-MR-107U | MR-107U | — / — | ? / operational | lander_descent, rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-L3H-MONO-2025, SRC-SPACEFDN-MSL |
| ENG-US-MR-107V | MR-107V | — / — | ? / operational | orbital_maneuver, rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-L3H-MONO-2025, SRC-SATCAT-MR107 |

#### FAM-MR-111 — Aerojet (Rocket Research Co. heritage, Redmond WA)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-111C | MR-111C | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-SPACEFDN-MSL |
| ENG-US-MR-111G | MR-111G | — / — | ? / operational | rcs | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-L3H-MONO-2023, SRC-L3H-MONO-2025, SRC-SATCAT-MR111G |

#### FAM-MR-80 — Aerojet (Rocket Research Co. heritage, Redmond WA), Rocket Research Company

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-MR-80 | MR-80 | — / baseline | 1970s; launched 1975, landed 1976 / retired | lander_descent | none(mono) / N2H4 | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-L3H-VIKING, SRC-IAC10-MR80B, SRC-WIKI-VIKING-PROGRAM |
| ENG-US-MR-80B | MR-80B | MR-80 / derivative | ? / operational | lander_descent | none(mono) / N2H4 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-L3H-MONO-2023, SRC-L3H-VIKING, SRC-IAC10-MR80B |

#### FAM-NAA-120K-135K — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR71-NA-1 | XLR71-NA-1 | XLR43-NA-1 / derivative | 1950-1955 / cancelled | booster, missile | LOX / ethyl alcohol | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-ASTRONAUTIX-XLR71, SRC-ENGINEHISTORY-RPE03, SRC-HEROICRELICS-RKDTREE |
| ENG-US-XLR83-NA-1 | XLR83-NA-1 | XLR71-NA-1 / uprate | 1955-1958 / cancelled | booster, missile | LOX / JP-4 | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-ASTRONAUTIX-XLR71, SRC-ENGINEHISTORY-RPE03, SRC-HEROICRELICS-RKDTREE |

#### FAM-NAA-75-110-REDSTONE — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-NAA-75-110-A-1 | NAA 75-110 A-1 | XLR43-NA-1 / derivative | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |
| ENG-US-NAA-75-110-A-2 | NAA 75-110 A-2 | NAA 75-110 A-1 / development_config | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |
| ENG-US-NAA-75-110-A-3 | NAA 75-110 A-3 | NAA 75-110 A-2 / development_config | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |
| ENG-US-NAA-75-110-A-4 | NAA 75-110 A-4 | NAA 75-110 A-3 / development_config | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |
| ENG-US-NAA-75-110-A-5 | NAA 75-110 A-5 | NAA 75-110 A-4 / development_config | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |
| ENG-US-NAA-75-110-A-6 | NAA 75-110 A-6 | NAA 75-110 A-5 / derivative | ? / retired | booster, missile | LOX / ethyl alcohol-water; hydyne (UDMH/DETA) in some applications | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-A6 |
| ENG-US-NAA-75-110-A-7 | NAA 75-110 A-7 | NAA 75-110 A-6 / derivative | ? / retired | booster, missile | LOX / ethyl alcohol 75% / water 25% | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 6 values (1 REPORTED) | SRC-NASA-MSFC-MERCREDSTONE, SRC-ENGINEHISTORY-RPE04-2, SRC-HEROICRELICS-REDSTONE |

#### FAM-NAA-75K — Rocketdyne (North American Aviation)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR43-NA-1 | XLR43-NA-1 | — / baseline | 1947-1951 dev / retired | missile, test_bed | LOX / ethyl alcohol | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-ASTRONAUTIX-XLR43, SRC-ENGINEHISTORY-RPE03, SRC-ENGINEHISTORY-RPE04-2 |

#### FAM-NEWTON — Virgin Orbit

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-NEWTONFOUR | NewtonFour | — / — | ? / retired | upper_stage | LOX / RP-1 | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-NSF-LAUNCHERONE-2020, SRC-WIKI-LAUNCHERONE, SRC-AVIATIONIST-L1-2020 |
| ENG-US-NEWTONTHREE | NewtonThree | — / — | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-NSF-LAUNCHERONE-2020, SRC-WIKI-LAUNCHERONE |

#### FAM-NK — Aerojet, Aerojet (from NK-43)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AJ26-58 | AJ26-58 | NK-33 / derivative | 1990s-2014 / cancelled | booster | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-SKYROCKET-K1, SRC-WIKI-AJ26, SRC-WIKI-ANTARES |
| ENG-US-AJ26-59 | AJ26-59 | NK-33 / derivative | 1990s-2000s / cancelled | booster, upper_stage | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-SKYROCKET-K1, SRC-WIKI-AJ26 |
| ENG-US-AJ26-60 | AJ26-60 | NK-43 / derivative | ? / cancelled | upper_stage | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-SKYROCKET-K1, SRC-WIKI-K1 |
| ENG-US-AJ26-62 | AJ26-62 | NK-33 / export | 2000s-2014 / retired | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 7 values (1 REPORTED) | SRC-NASA-ORB3-IRT, SRC-KOREASCI-AJ26, SRC-NAS-DEPS-068011 |

#### FAM-R-1E — The Marquardt Company

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-R-1E | R-1E | — / — | flown 1981-2011 / retired | rcs | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 5 values (5 REPORTED) | SRC-NTRS-19910018886 |

#### FAM-R-40 — Aerojet (ex-Marquardt), The Marquardt Company

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-R-40A | R-40A | — / — | flown 1981-2011 / retired | rcs | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 6 values (6 REPORTED) | SRC-NTRS-19910018886 |
| ENG-US-R-40B | R-40B | R-40A / derivative | ? / operational | rcs, spacecraft_main | N2O4/MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (4 REPORTED) | SRC-L3H-BIPROP-2023, SRC-L3H-BIPROP-2024 |

#### FAM-R-42 — Marquardt / Aerojet

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-R-42 | R-42 | — / — | ? / operational | spacecraft_main | N2O4/MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (4 REPORTED) | SRC-L3H-BIPROP-2023, SRC-L3H-BIPROP-2024 |

#### FAM-R-4D — Aerojet, Aerojet (NASA ISPT funded), Aerojet (formerly Marquardt), Aerojet Rocketdyne, Marquardt / Kaiser Marquardt (la…

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AMBR | AMBR | R-4D-15DM / development_config | dev ~2006-2010 / development | demonstrator, spacecraft_main | N2O4 / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-NASA-AMBR-DISC, SRC-NASA-AMBR-NF3 |
| ENG-US-R-4D-CASSINI-MAIN-ENGINE | Cassini main engine (R-4D) | R-4D / stage_specific | ? / retired | spacecraft_main | NTO / MMH | other; none_pressure_fed (REPORTED) | sourced; 2 values (1 REPORTED) | SRC-NASA-CASSINI-ENGINE, SRC-IAC10-AJHIPAT, SRC-WIKI-R4D |
| ENG-US-R-4D | R-4D | — / baseline | dev 1962-; flown 1966- / retired | rcs | N2O4 / MMH / Aerozine-50 (Apollo LM used A-50) | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NASA-TND7151, SRC-NTRS-19690029231, SRC-WIKI-R4D |
| ENG-US-R-4D-11 | R-4D-11 | R-4D / uprate | 1980s-present / operational | orbital_maneuver, rcs, spacecraft_main | N2O4/MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 6 values (6 REPORTED) | SRC-L3H-BIPROP-2024, SRC-IAC10-AJHIPAT, SRC-SATCATALOG-R4D11 |
| ENG-US-R-4D-11-ORION-ESM-AUXILIARY | R-4D-11 (Orion ESM auxiliary) | R-4D-11 / stage_specific | 2022- / operational | orbital_maneuver | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-ESA-ESMPROP, SRC-NTRS-20240003648 |
| ENG-US-R-4D-15 | R-4D-15 | R-4D-11 / uprate | 2000s-present / operational | spacecraft_main | N2O4/MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-IAC10-AJHIPAT, SRC-SPACEFDN-HIPAT100 |
| ENG-US-R-4D-15DM | R-4D-15DM | R-4D-15 / derivative | ? / operational | spacecraft_main | N2O4 / N2H4 | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-NASA-AMBR-NF3 |

#### FAM-RAPTOR — SpaceX

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RAPTOR-DEVELOPMENT | Raptor (development) | — / development_config | development engines c.2016-2019 (dates unsourced) / retired | test_bed | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-UT-2019-RAPTOR, SRC-WIKI-RAPTOR |
| ENG-US-RAPTOR-1 | Raptor 1 | Raptor (development) / baseline | first flight Starhopper July 2019 (secondary); Starship SN-… | booster, test_bed, upper_stage | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-WIKI-RAPTOR, SRC-WCCF-RAPTOR-330 |
| ENG-US-RAPTOR-2 | Raptor 2 | Raptor 1 / block_upgrade | static fires from c.2021-2022; flew Starship IFT-1..IFT-11 … | booster, upper_stage | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 7 values (5 REPORTED) | SRC-SPACEX-STARSHIP-PAGE, SRC-SPACEX-UPDATES, SRC-EDA-RAPTOR-COMPARE |
| ENG-US-RAPTOR-3 | Raptor 3 | Raptor 2 / block_upgrade | first flight 2026-05-22 (Starship Flight 12); Flight 13 202… | booster, upper_stage | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 4 values (4 REPORTED) | SRC-SPACEX-FLT12, SRC-SPACEX-FLT13, SRC-SPACEX-STARSHIP-PAGE |
| ENG-US-RAPTOR-3-VACUUM | Raptor 3 Vacuum | Raptor 3 / vacuum_variant | first flight 2026-05-22 / operational | upper_stage | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 1 values (1 REPORTED) | SRC-SPACEX-FLT12, SRC-SPACEX-UPDATES |
| ENG-US-RAPTOR-VACUUM | Raptor Vacuum | Raptor 2 / vacuum_variant | R2-era RVac flown on Starship V1/V2 2023-2025 (analyst know… | upper_stage | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 1 values (1 REPORTED) | SRC-SPACEX-UPDATES |

#### FAM-REAVER — Firefly Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-REAVER | Reaver | — / baseline | Alpha flights 2021-2025 (FLTA006 2025); return-to-flight st… | booster | NOT_AUDITED / NOT_AUDITED | pump_fed_turbopump; tap_off (REPORTED) | sourced; 6 values (5 REPORTED) | SRC-FIREFLY-ALPHA-PAGE, SRC-FIREFLY-MIRANDA-RR, SRC-FIREFLY-PUG-5.2 |

#### FAM-RIPLEY — Ursa Major

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RIPLEY | Ripley | — / — | ? / development | booster | LOX / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-SATTODAY-ARROWAY-2022, SRC-SATTODAY-PHANTOM-URSA-2022 |

#### FAM-RL10 — Pratt & Whitney

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RL10-CECE | RL10 CECE | RL10A-4 / test_article | ? / experimental | demonstrator | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10A-1 | RL10A-1 | — / baseline | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NTRS-TM107318, SRC-ASME-RL10, SRC-ASTRONAUTIX-RL10 |
| ENG-US-RL10A-3 | RL10A-3 | RL10A-1 / derivative | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-ASTRONAUTIX-RL10 |
| ENG-US-RL10A-3-1 | RL10A-3-1 | RL10A-3 / derivative | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10A-3-3 | RL10A-3-3 | RL10A-3-1 / derivative | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10A-3-3A | RL10A-3-3A | RL10A-3-3 / uprate | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 7 values (5 REPORTED) | SRC-NTRS-19910018888, SRC-NTRS-TM107318, SRC-PURDUE-RL10 |
| ENG-US-RL10A-4 | RL10A-4 | RL10A-3-3A / uprate | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-NTRS-TM107318, SRC-NAP-11780 |
| ENG-US-RL10A-4-1 | RL10A-4-1 | RL10A-4 / derivative | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-NTRS-TM107318, SRC-WIKI-ATLASIII |
| ENG-US-RL10A-4-2 | RL10A-4-2 | RL10A-4-1 / derivative | NOT_AUDITED / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 10 values (3 REPORTED) | SRC-L3HARRIS-RL10-SPEC, SRC-NTRS-RL10A33A-MODEL, SRC-AIAA-VEHGUIDE-ATLAS |
| ENG-US-RL10A-5 | RL10A-5 | RL10A-4 / sea_level_variant | ? / retired | demonstrator | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-YARCHIVE-RL10 |
| ENG-US-RL10B-2 | RL10B-2 | RL10A-4 / derivative | NOT_AUDITED / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | sourced; 17 values (2 REPORTED) | SRC-ULA-DIV-GPSIIISV02, SRC-AIAA-VEHGUIDE-DELTA, SRC-IAC-2018-43630 |
| ENG-US-RL10C-1 | RL10C-1 | RL10A-4-2 / derivative | ? / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10C-1-1 | RL10C-1-1 | RL10C-1 / derivative | ? / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10C-2 | RL10C-2 | RL10B-2 / derivative | ? / unknown | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10C-3 | RL10C-3 | RL10B-2 / derivative | ? / development | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-RL10C-X | RL10C-X | RL10C-1-1 / derivative | ? / development | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-ROTON — Rotary Rocket Company

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-ROTON-ROTARY-ENGINE | Roton rotating annular aerospike (unnamed) | — / — | 1996-1999 design; abandoned for Fastrac derivative June 199… | booster, experimental | LOX / kerosene | other; other (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-FLIGHTGLOBAL-ROTON, SRC-GLOBALSEC-ROTON, SRC-WIKI-ROTARYROCKET |

#### FAM-RS-18 — Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-18 | RS-18 | — / — | 2000s / cancelled | demonstrator | N2O4 / Aerozine-50 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RS-25 — Aerojet Rocketdyne, Aerojet Rocketdyne (L3Harris), Rocketdyne (Rockwell / Boeing / PWR / Aerojet Rocketdyne), Rocketdyn…

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-AR22 | AR-22 | RS-25D / derivative | ? / retired | booster, demonstrator | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-DARPA-XS1-2017, SRC-SPACECOM-AR22-2018 |
| ENG-US-SSME-BLOCK-II | RS-25D | RS-25 / block_upgrade | NOT_REPORTED (Block II first flight not found in round 2); … | booster, core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM) | sourced; 18 values (17 REPORTED) | SRC-ENGINEHISTORY-SSMEORIENT-1998, SRC-IBIBLIO-SSMEOVERVIEW, SRC-L3HARRIS-RS25-SPEC |
| ENG-US-RS-25E | RS-25E (RS-25 restart production) | RS-25D / block_upgrade | 2010s-2020s dev / development | core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | sourced; 5 values (5 REPORTED) | SRC-L3H-SLS-BROCHURE-2022, SRC-NASA-RS25-WEB, SRC-NTRS-20170008958 |
| ENG-US-SSME-FPL-PHASE-I | SSME (FPL / Phase I) | — / baseline | 1972 dev; flown 1981- / retired | booster, core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-NASA-RS25-WEB |
| ENG-US-SSME-BLOCK-I | SSME Block I | SSME Phase II / block_upgrade | 1995 (background) / retired | booster, core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-SSME-BLOCK-IIA | SSME Block IIA | SSME Block I / block_upgrade | 1998 (background) / retired | booster, core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-SSME-PHASE-II | SSME Phase II | SSME (FPL / Phase I) / block_upgrade | 1983-1988 (background) / retired | booster, core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RS-27 — Rocketdyne, Rocketdyne (Boeing / PWR / Aerojet Rocketdyne), Rocketdyne (Rockwell International)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-27 | RS-27 | H-1 (205K) / derivative | 1974-1992 (Delta 2000/3000/Delta II 6925) / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-ASTRONAUTIX-LR79, SRC-WIKI-RS27 |
| ENG-US-RS-27A | RS-27A | RS-27 / derivative | 1990-2018 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 6 values (0 REPORTED) | SRC-PURDUE-RS27A, SRC-WIKI-RS27, SRC-WIKI-RS27A |
| ENG-US-RS-27C | RS-27C | RS-27 / derivative | ? / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RS-56 — Rocketdyne (Rockwell)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-56-OBA | RS-56-OBA | LR89-NA-7 / derivative | 1991-2004 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-WIKI-ATLASII, SRC-WIKI-MA5A, SRC-WIKI-RS56 |
| ENG-US-RS-56-OSA | RS-56-OSA | LR105-NA-7 / derivative | 1991-2004 / retired | sustainer | LOX / RP-1 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-WIKI-ATLASII, SRC-WIKI-RS56 |

#### FAM-RS-68 — Boeing Rocketdyne, Pratt & Whitney Rocketdyne / Aerojet Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-68 | RS-68 | — / baseline | 1990s dev; flown 2002-2012? / retired | booster, core | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-NAP-11780, SRC-WIKI-RS68 |
| ENG-US-RS-68A | RS-68A | RS-68 / uprate | 2008 dev; flown 2012-2024 / retired | booster, core | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 6 values (5 REPORTED) | SRC-L3H-RS68A-DS, SRC-WIKI-RS68 |

#### FAM-RS-83 — Rocketdyne (Boeing)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-83 | RS-83 | — / — | 2000-2002 / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RS-84 — Rocketdyne (Boeing)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-84 | RS-84 | — / — | 2000-2004 / cancelled | demonstrator | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RS-88 — Aerojet Rocketdyne, Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-RS-88 | RS-88 | — / — | 1997 Bantam System Technology; NASA tests Nov-Dec 2003 (14 … | demonstrator | LOX / ethanol | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-RS88 |
| ENG-US-STARLINER-LAE | Starliner Launch Abort Engine (LAE) | RS-88 / derivative | ? / operational | other | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (1 REPORTED) | SRC-AR-STARLINER-2016, SRC-MILAERO-STARLINER, SRC-WIKI-RS88 |

#### FAM-RUTHERFORD — Rocket Lab

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-NZ-RUTHERFORD | Rutherford | — / baseline | first flight 2017 ('It's a Test', analyst knowledge); opera… | booster | LOX / NOT_AUDITED | pump_fed_electric; electric_pump (REPORTED) | sourced; 8 values (7 REPORTED) | SRC-RKLB-PAYLOAD-INCREASE, SRC-RL-500-TESTS, SRC-RL-ELECTRON-PAGE |
| ENG-NZ-RUTHERFORD-VACUUM | Rutherford Vacuum | Rutherford / vacuum_variant | ? / operational | upper_stage | LOX / NOT_AUDITED | pump_fed_electric; electric_pump (REPORTED) | sourced; 8 values (8 REPORTED) | SRC-RKLB-PAYLOAD-INCREASE, SRC-RL-100TH-RUTHERFORD, SRC-RL-ELECTRON-PAGE |

#### FAM-SE-8 — Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-SE-8 | SE-8 | — / — | flown 1966-1975 / retired | rcs | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-NASA-TND7151, SRC-STEVEBLOG-SE6SE8 |

#### FAM-SPECTRE — Firefly Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-SPECTRE | Spectre | — / — | ? / operational | lander_descent, rcs, spacecraft_main | UNKNOWN / UNKNOWN | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-BLUEGHOST |

#### FAM-STARLINER-SM-PROPULSION — Aerojet Rocketdyne

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-STARLINER-OMAC | Starliner OMAC thruster | — / — | ? / operational | orbital_maneuver, rcs | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 3 values (1 REPORTED) | SRC-AR-STARLINER-2016, SRC-ARXIV-2107-06795, SRC-MILAERO-STARLINER |
| ENG-US-STARLINER-RCS | Starliner service module RCS thruster | — / — | ? / operational | rcs | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 3 values (1 REPORTED) | SRC-AR-STARLINER-2016, SRC-ARXIV-2107-06795, SRC-SPACEREVIEW-4842 |

#### FAM-TR-202 — Northrop Grumman

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-TR-202 | TR-202 | — / — | ? / unknown | lander_descent | NOT_AUDITED / NOT_AUDITED | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-TRW-LAE — TRW (now Northrop Grumman)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-TR-308 | TR-308 | — / — | ? / unknown | spacecraft_main | NTO / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-SATSEARCH-TR308 |
| ENG-US-TR-312 | TR-312 | — / — | qualification MMH/NTO targeted early 2000 / unknown | orbital_maneuver, spacecraft_main | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-SPACEDAILY-TR312 |

#### FAM-TRW-PINTLE — TRW, TRW / Northrop Grumman

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-TR-106 | TR-106 | — / — | ? / cancelled | demonstrator | LOX / LH2 | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-TR106 |
| ENG-US-TR-107 | TR-107 | — / — | 2000-2004 / cancelled | demonstrator | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-TR107 |
| ENG-US-TR-201 | TR-201 | LMDE (Apollo LM Descent Engine) / derivative | early 1970s dev; flown 1972/1974-1988 / retired | upper_stage | N2O4 / Aerozine-50 | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-PURDUE-LIQUIDS, SRC-WIKI-TR201 |

#### FAM-VECTOR — Vector Launch

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-LP-2 | LP-2 | — / — | ? / cancelled | upper_stage | LOX / propylene | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-AMD-VECTOR-2017, SRC-SKYROCKET-VECTOR, SRC-WIKI-VECTORR |

#### FAM-VORTEX — Sierra Space

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-VORTEX-1500-LBF-HYPERGOLIC | VORTEX 1,500 lbf hypergolic engine | — / — | ? / development | orbital_maneuver, spacecraft_main | NOT_REPORTED / NOT_REPORTED | UNKNOWN; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-BW-SIERRA-VORTEX-1500-2023, SRC-SPACEBUCKET-DC-ENGINES |
| ENG-US-VR35K-A | VR35K-A | — / — | ? / development | upper_stage | LOX / LH2 | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-SPACEBUCKET-DC-ENGINES |

#### FAM-VR — Intuitive Machines

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-VR3500 | VR3500 | — / — | ? / development | lander_descent | LOX / LCH4 | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-IM-VR900-QUAL-2024 |
| ENG-US-VR900 | VR900 | — / — | ? / operational | lander_descent, spacecraft_main | LOX / LCH4 | UNKNOWN; UNKNOWN | sourced; 4 values (0 REPORTED) | SRC-IM-NOVAC-PAGE, SRC-IM-VR900-QUAL-2024, SRC-SFN-IM1-2024 |

#### FAM-WAC-CORPORAL — Aerojet (with JPL)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-38ALDW-1500 | 38ALDW-1500 | — / — | 1945-1947 / retired | other | RFNA / furfuryl alcohol / aniline (conflict) | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-CALTECH-THESIS310, SRC-WIKI-WACCORPORAL |

#### FAM-X-405 — General Electric

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-X-405 | X-405 | — / — | 1955-1959 / retired | booster | LOX / RP-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-VANGUARD, SRC-WIKI-X405 |

#### FAM-XCOR — XCOR Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XCOR-LYNX-MAIN | XCOR Lynx main engine (piston-pump fed) - designation NOT confirmed this session | — / — | ~2008-2017 development / cancelled | aircraft_rocket, experimental | LOX / kerosene | pump_fed_positive_displacement; other (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-SPACENEWS-XCOR-ULA, SRC-SPACEREF-XCOR-LOXPUMP |
| ENG-US-XR-4A3 | XR-4A3 | — / — | ? / retired | aircraft_rocket | LOX / isopropyl alcohol | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-MOJAVE-EZROCKET, SRC-WIKI-EZROCKET |
| ENG-US-XR-5K18 | XR-5K18 | — / — | ? / cancelled | aircraft_rocket | LOX / kerosene | pump_fed_positive_displacement; other (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-SATNEWS-XCOR-2008, SRC-WIKI-LYNX |
| ENG-US-5M15 | XR-5M15 | — / — | first firings announced 2007-01-16 / cancelled | demonstrator, experimental | LOX / LCH4 | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-ENGINEER-5M15, SRC-FLIGHTGLOBAL-5M15 |

#### FAM-XLR10 — Reaction Motors Inc.

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR10-RM-2 | XLR10-RM-2 | — / — | 1949-1957 (Viking flights) / retired | other | LOX / ethyl alcohol (95:5 ethanol-water per one source) | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-WIKI-VIKING-SOUNDING-ROCKET, SRC-DARLING-VIKING, SRC-THISDAY-XLR10 |

#### FAM-XLR11 — Reaction Motors Inc., Reaction Motors Inc. (RMI)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR11 | XLR11 | — / baseline | 1940s-1975 / retired | aircraft_rocket | LOX / ethyl alcohol (diluted with water) | UNKNOWN; UNKNOWN (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-NASM-XLR11, SRC-NMUSAF-XLR11, SRC-WIKI-XLR11 |
| ENG-US-XLR11-RM-5 | XLR11-RM-5 | XLR11 / stage_specific | ? / retired | aircraft_rocket | LOX / ethyl alcohol | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-XLR11, SRC-HISTORYOFWAR-X1 |
| ENG-US-XLR8-RM-5 | XLR8-RM-5 | XLR11 / renamed | ? / retired | aircraft_rocket | LOX / ethyl alcohol | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-XLR11 |

#### FAM-XLR129 — Pratt & Whitney (Florida R&D Center)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR129-P-1 | XLR129-P-1 | — / — | 1967-1971 / cancelled | demonstrator | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NTRL-AD508757, SRC-WIKI-XLR129 |

#### FAM-XLR25 — Curtiss-Wright

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR25-CW-1 | XLR25-CW-1 | — / — | 1950s / retired | aircraft_rocket | LOX / alcohol | UNKNOWN; UNKNOWN | sourced; 2 values (1 REPORTED) | SRC-NASA-DFRC-FS079, SRC-WIKI-BELLX2, SRC-THISDAY-XLR25 |

#### FAM-XLR81 — Bell Aerosystems (Bell Aircraft)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-BELL-117 | Bell 117 | — / baseline | 1950s / cancelled | other | IRFNA / UDMH | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-US-BELL-8001 | Bell 8001 | Bell 117 / derivative | ? / retired | upper_stage | IRFNA / UDMH | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-BELL8000 |
| ENG-US-BELL-8048 | Bell 8048 | Bell 8001 / derivative | ? / retired | upper_stage | IRFNA / UDMH | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-WIKI-BELL8000, SRC-THISDAY-BELL8048 |
| ENG-US-BELL-8081 | Bell 8081 | Bell 8048 / derivative | ? / retired | upper_stage | IRFNA / UDMH | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-ASTRONAUTIX-AGENAB, SRC-WIKI-BELL8000 |
| ENG-US-BELL-8096 | Bell 8096 | Bell 8081 / derivative | ? / retired | upper_stage | IRFNA / UDMH | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-ASTRONAUTIX-AGENAB, SRC-DESIGNSYS-RM81, SRC-WIKI-BELL8000 |
| ENG-US-BELL-8247 | Bell 8247 | Bell 8096 / stage_specific | ? / retired | upper_stage | IRFNA / UDMH | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-ASTRONAUTIX-BELL8247, SRC-WIKI-BELL8000 |

#### FAM-XLR99 — Reaction Motors Division of Thiokol

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-XLR99-RM-1 | XLR99-RM-1 | — / baseline | 1950s dev; flown Nov 1960-1968 / retired | aircraft_rocket | LOX / anhydrous ammonia | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 6 values (0 REPORTED) | SRC-NASM-XLR99, SRC-NMUSAF-XLR99, SRC-NMUSAF-YLR99 |
| ENG-US-XLR99-RM-2 | XLR99-RM-2 | XLR99-RM-1 / derivative | ? / retired | aircraft_rocket | LOX / anhydrous ammonia | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-ZENITH — Stoke Space

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-US-ZENITH | Zenith | — / — | ? / development | booster | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-SPACECOM-STOKE-2026, SRC-SPACENEWS-442279, SRC-SACRA-STOKE |

### Brazil (BR) — 3 variant records

#### FAM-L-SERIES-IAE — IAE/DCTA, IAE/DCTA (with DLR)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-BR-L15 | L15 | — / — | ? / unknown |  | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-JATM-IAE-2009 |
| ENG-BR-L5 | L5 | — / baseline | first firing 2005 / unknown | demonstrator, upper_stage | LOX / ethanol (tests/flight); designed for kerosene | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-COBEM09-0532, SRC-JATM-IAE-2009, SRC-FAPESP-GRAVIDADE-ZERO |
| ENG-BR-L75 | L75 | — / baseline | dev 2008- / development | upper_stage | LOX / ethanol | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-JATM-L75-386, SRC-REDALYC-L75-2011, SRC-FAPESP-PROPULSAO-VERDE |

### Argentina (AR) — 4 variant records

#### FAM-TRONADOR — CONAE, CONAE (UNVERIFIED), CONAE / VENG S.A.

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-AR-MT-B | MT-B | — / baseline | ? / development | upper_stage | LOX (current) / N2O4 (older design) / RP-1 (current) / MMH (older design) | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-WIKI-TRONADOR |
| ENG-AR-RS-2 | RS-2 (30 tf) | — / baseline | ? / development | booster | LOX / kerosene (RP-1) | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-ARG-GOB-390734, SRC-SKYROCKET-VEX5, SRC-WIKI-TRONADOR |
| ENG-AR-TRONADOR-II-ENGINES | Tronador II engines (bundled round-1 placeholder) | — / — | ? / unknown |  | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-TRONADOR |
| ENG-AR-VEX-1A-ENGINE | VEx-1A engine (4 t, designation unknown) | — / test_article | test flight attempt 2014 / retired | demonstrator | ? / ? | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-IPROFESIONAL-VEX1A, SRC-WIKI-TRONADOR |

## USSR / Russia / Ukraine

### Soviet Union and Russia (SU+RU) — 122 variant records

#### FAM-DPO-THRUSTERS — KB KhimMash (Isayev) [developer not in summary], NIIMash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-11D428 | 11D428 | — / — | ? / retired | rcs | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-11D428 |
| ENG-RU-11D428A | 11D428A | 11D428 / derivative | ? / operational | rcs | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-11D428, SRC-WIKI-KTDU80 |
| ENG-RU-11D428A-16 | 11D428A-16 | 11D428A / block_upgrade | ? / operational | rcs | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-11D428 |
| ENG-RU-S5-142 | S5.142 | — / — | ? / operational | rcs | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-WIKI-S5142 |

#### FAM-ISAYEV-MISSILE-ENGINES — OKB-2 / KB KhimMash (A. M. Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-4D10 | 4D10 | — / — | 1960s / retired | missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | placeholder; 0 values (0 REPORTED) | SRC-GLOBALSEC-R27K, SRC-WIKI-R27 |
| ENG-SU-9D21 | 9D21 | S2.253 / derivative | 1960s- / retired | missile | AK-27I / TG-02 (Samin) | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-S2-253 | S2.253 | — / — | 1950s / retired | missile | AK-20 (nitric acid) / TG-02 / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) | SRC-WIKI-KBKHM |
| ENG-SU-S2-711 | S2.711 | — / — | 1950s / retired | missile | AK-20 / TG-02 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-ISAYEV-S5-UPPER-STAGE-ENGINES — KB KhimMash (Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-S5-92 | S5.92 | — / — | 1990s-; flown 2000- / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 9 values (1 REPORTED) | SRC-STARSEM-ST07, SRC-STARSEM-ST08, SRC-RSW-FREGAT |
| ENG-RU-S5-98M | S5.98M | S5.92 (predecessor per Wiki) / — | 1990s-; flown 1999- / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-RSW-BRIZM, SRC-WIKI-S598M, SRC-HABR-212735 |

#### FAM-KTDU — OKB-2 (Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-KTDU-35 | KTDU-35 | — / — | NOT_AUDITED / retired | spacecraft_main | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-KTDU35 |
| ENG-SU-S5-35 | S5.35 (DKD) | — / — | NOT_AUDITED / retired | spacecraft_main | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-KTDU35 |
| ENG-SU-S5-60 | S5.60 (SKD) | — / — | NOT_AUDITED / retired | spacecraft_main | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-KTDU35 |

#### FAM-KTDU-35 — OKB-2 (Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-S5-35 | S5.35 | — / — | ? / retired | spacecraft_main | AK-27I / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-KTDU35 |
| ENG-RU-S5-60 | S5.60 | — / — | ? / retired | spacecraft_main | AK-27I / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-KTDU35 |

#### FAM-KTDU-53 — OKB-2 (Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-S5-53 | S5.53 | — / — | ? / retired | orbital_maneuver | NOT_REPORTED / NOT_REPORTED | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-KTDU35 |

#### FAM-KTDU-80 — KB KhimMash (Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-11D426 | 11D426 | — / — | ? / retired | spacecraft_main | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-S580 |
| ENG-RU-S5-80 | S5.80 | 11D426 / derivative | ? / operational | orbital_maneuver, spacecraft_main | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 7 values (0 REPORTED) | SRC-WIKI-KTDU80, SRC-WIKI-S580 |

#### FAM-LYULKA-LOX-LH2 — OKB-165 (A. M. Lyulka)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-11D57 | 11D57 | — / — | 1960s-1970s / cancelled | upper_stage | LOX / LH2 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) | SRC-LPRE-NPOEM-RD0120UP |

#### FAM-NK — OKB-276 (N. D. Kuznetsov) / SNTK im. Kuznetsova (now UEC-Kuznetsov), SNTK Kuznetsov / Kuznetsov (Samara)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-NK-15 | NK-15 | NK-9 / derivative | 1962-1972; flown 1969-1972 / retired | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 6 values (0 REPORTED) | SRC-WIKI-NK15 |
| ENG-SU-NK-15V | NK-15V | NK-15 / vacuum_variant | 1960s-1972 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-NK15 |
| ENG-SU-NK-19 | NK-19 | NK-15 / stage_specific | 1960s-1972 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-NK-21 | NK-21 | — / — | 1960s-1972 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RSW-N1G |
| ENG-SU-NK-31 | NK-31 | NK-21 / block_upgrade | 1970s / cancelled | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RSW-N1G, SRC-WIKI-NK9 |
| ENG-SU-NK-33 | NK-33 | NK-15 / block_upgrade | 1968-1974 dev; stored; flown 2010s via AJ26 and NK-33A / re… | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 18 values (6 REPORTED) | SRC-DVIGATEL-1999-1, SRC-NAS-DEPS-068011, SRC-PURDUE-AJ26 |
| ENG-RU-NK-33A | NK-33A | NK-33 / block_upgrade | 2000s-2019 / retired | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-NK15 |
| ENG-SU-NK-39 | NK-39 | NK-31 / derivative | 1970s / cancelled | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-NK-43 | NK-43 | NK-33 / vacuum_variant | 1970s / cancelled | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-NK15, SRC-WIKI-NK43 |
| ENG-SU-NK-9 | NK-9 | — / — | 1959-1962 / cancelled | missile | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-NK9 |
| ENG-SU-NK-9V | NK-9V | NK-9 / vacuum_variant | 1962 tests / cancelled | missile | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-NK9 |

#### FAM-OKB-1-UPPER-STAGE-ENGINES — OKB-1 (M. V. Melnikov), OKB-1 (Melnikov)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-11D33 | 11D33 | — / — | dev 1958-1960; flown 1961-2010 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 6 values (0 REPORTED) | SRC-WIKI-S15400 |
| ENG-SU-11D33M | S1.5400A1 (11D33M) | 11D33 / uprate | upgrade 1961-1964 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-S15400 |

#### FAM-ORM — GDL/RNII (V. P. Glushko)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-ORM-65 | ORM-65 | — / — | 1936-1938 / retired | aircraft_rocket, experimental | nitric acid / kerosene | pressure_fed_unspecified; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-0105-0109 — OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0105 | RD-0105 | — / — | 1958 dev (9 months); flown 1959-1960 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-WIKI-RD0109 |
| ENG-SU-RD-0109 | RD-0109 | RD-0105 / block_upgrade | 1959-1960s / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-RSW-VOSTOK-LV, SRC-WIKI-RD0109 |

#### FAM-RD-0106-0107-0108-0110 — KBKhA, OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0106 | RD-0106 | — / — | 1960s / retired | missile, upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RSW-RD0110 |
| ENG-SU-RD-0107 | RD-0107 | RD-0106 / stage_specific | 1963-1976 / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RSW-RD0110 |
| ENG-SU-RD-0108 | RD-0108 | RD-0107 / derivative | 1960s / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-RD-0110 | RD-0110 | RD-0107 / derivative | 1960s-; flown 1967?- / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 11 values (0 REPORTED) | SRC-ESA-RD0110, SRC-RSW-RD0110, SRC-WIKI-RD0110 |
| ENG-RU-RD-0110R | RD-0110R | RD-0110 / derivative | 2000s-2019 / retired | booster, rcs | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-WIKI-RD0110R |

#### FAM-RD-0120 — OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0120 | RD-0120 | — / baseline | 1976-1987 dev; flown 1987-1988 / retired | core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM) | sourced; 19 values (5 REPORTED) | SRC-JAXA-61856043, SRC-LPRE-NPOEM-RD0120UP, SRC-AVWEEK-RD0120-EU |

#### FAM-RD-0124 — KBKhA, KBKhA (now part of NPO Energomash)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-0124 | RD-0124 | — / — | 1990s-2006 dev; flown 2006- / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 7 values (0 REPORTED) | SRC-RSW-RD0124, SRC-WIKI-RD0124, SRC-WWW1-RD0124 |
| ENG-RU-RD-0124A | RD-0124A | RD-0124 / stage_specific | 2000s; flown 2014- / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-RD0124 |
| ENG-RU-RD-0124MS | RD-0124MS | RD-0124 / derivative | 2010s-; flown 2026 / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-RSW-RD0124, SRC-SPACEREF-RD0124MS, SRC-WIKI-SOYUZ5 |

#### FAM-RD-0146 — KBKhA (with Pratt & Whitney cooperation, early)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-0146 | RD-0146 | — / — | 1990s-2010s dev / development | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-0162 — KBKhA

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-0162 | RD-0162 | — / — | 2010s dev (demonstrators) / development | booster | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-0205-0210 — OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0205 | RD-0205 | — / — | 1961-1964 / cancelled | missile, upper_stage | N2O4 / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-RSW-RD0212 |
| ENG-SU-RD-0210 | RD-0210 | RD-0205 / derivative | 1963-; flown 1965- / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 10 values (0 REPORTED) | SRC-ILS-PMPG-A, SRC-DVIGATEL-2000-2, SRC-RSW-RD0210 |
| ENG-SU-RD-0211 | RD-0211 | RD-0210 / stage_specific | 1965- / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-RSW-RD0210, SRC-WIKI-RD0210 |
| ENG-SU-RD-0212 | RD-0212 | RD-0205 / stage_specific | 1960s-; flown 1968- / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RSW-RD0212 |
| ENG-SU-RD-0213 | RD-0213 | RD-0210 / stage_specific | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-RSW-RD0212 |
| ENG-SU-RD-0214 | RD-0214 | — / — | ? / operational | rcs, upper_stage | N2O4 / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-RSW-RD0212 |

#### FAM-RD-0216-0217 — OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0216 | RD-0216 | — / — | 1960s / retired | missile | N2O4 (AT) / UDMH | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-RD-0217 | RD-0217 | — / — | 1960s / retired | missile | N2O4 (AT) / UDMH | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-0228-0229-0255 — KBKhA, KBKhA (OKB-154)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0228 | RD-0228 | — / — | NOT_AUDITED / retired | missile | N2O4 (unverified) / UDMH (unverified) | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-SKYROCKET-R36M, SRC-WIKI-RD0229 |
| ENG-SU-RD-0229 | RD-0229 | — / — | NOT_AUDITED / unknown | missile | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD0229 |

#### FAM-RD-0233-0234-0235 — KBKhA, OKB-154 (S. A. Kosberg) / KBKhA (Chemical Automatics Design Bureau), Voronezh

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0232 | RD-0232 | — / — | NOT_AUDITED / retired | booster, missile | N2O4 / UDMH | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-SF101-ROKOT |
| ENG-SU-RD-0233 | RD-0233 | — / — | 1970s / retired | booster, missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-SF101-ROKOT, SRC-WIKI-RD0233 |
| ENG-SU-RD-0234 | RD-0234 | RD-0233 / stage_specific | NOT_AUDITED / retired | booster, missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-SF101-ROKOT, SRC-WIKI-RD0233 |
| ENG-SU-RD-0235 | RD-0235 | — / — | 1970s / retired | missile | N2O4 / UDMH | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) | SRC-SF101-ROKOT, SRC-WIKI-ROKOT |
| ENG-SU-RD-0236 | RD-0236 | — / — | NOT_AUDITED / retired | missile, rcs | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-SF101-ROKOT, SRC-WIKI-RD0236 |

#### FAM-RD-0243-0244-0245 — KBKhA, KBKhA (OKB-154)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-0243 | RD-0243 | — / — | NOT_AUDITED / operational | missile | N2O4 / UDMH | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD0243 |
| ENG-SU-RD-0244 | RD-0244 | RD-0243 (module) / — | NOT_AUDITED / operational | missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD0243 |
| ENG-SU-RD-0245 | RD-0245 | RD-0243 (module) / — | NOT_AUDITED / operational | missile, rcs | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD0243 |

#### FAM-RD-0750 — KBKhA

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-0750 | RD-0750 | — / — | 1990s study / proposed | booster | LOX / kerosene + LH2 (tripropellant) | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-1-AIRCRAFT-BOOSTER — OKB-SD Kazan (V. P. Glushko)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-1 | RD-1 | — / — | 1943-1946 / retired | aircraft_rocket | nitric acid / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-SU-RD-1KHZ | RD-1KhZ | RD-1 / derivative | 1944-1946 / retired | aircraft_rocket | nitric acid / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-100-V-2-LINEAGE — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-100 | RD-100 | — / — | 1947-1950s / retired | missile | LOX / ethanol-water | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-KPI-GLUSHKO, SRC-PLANETARY-GLUSHKO, SRC-HISTORYRISE-GLUSHKO |
| ENG-SU-RD-101 | RD-101 | RD-100 / uprate | 1949-1950s / retired | missile | LOX / ethanol-water | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 7 values (0 REPORTED) | SRC-FAS-R2, SRC-KPI-GLUSHKO, SRC-PLANETARY-GLUSHKO |
| ENG-SU-RD-103 | RD-103 | RD-101 / uprate | 1953-1955 / retired | missile | LOX / ethanol-water | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-PLANETARY-GLUSHKO |
| ENG-SU-RD-103M | RD-103M | RD-103 / derivative | 1955-1960s / retired | missile | LOX / ethanol-water | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-KPI-GLUSHKO |

#### FAM-RD-107-108 — NPO Energomash, OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-107 | RD-107 | — / baseline | 1954-1957 dev; flown 1957- / retired | booster | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-IAC15-27909, SRC-WIKI-RD107 |
| ENG-SU-RD-107-8D74K | RD-107 (8D74K) | RD-107 / derivative | 1960s / retired | booster | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD107 |
| ENG-SU-RD-107A | RD-107A | RD-117 / block_upgrade | 2001- (in Soyuz service) / operational | booster | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 8 values (0 REPORTED) | SRC-ARIANESPACE-SOYUZ-UM-2012, SRC-WIKI-RD107, SRC-WIKI-SOYUZ-CSG |
| ENG-SU-RD-107MM | RD-107MM | RD-107 / uprate | 1960s-1970s / retired | booster | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD107 |
| ENG-SU-RD-108 | RD-108 | RD-107 / stage_specific | 1954-1957 dev; flown 1957- / retired | core, sustainer | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-SPUTNIK-LV |
| ENG-SU-RD-108A | RD-108A | RD-118 / block_upgrade | 2001- / operational | core, sustainer | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 9 values (0 REPORTED) | SRC-ARIANESPACE-SOYUZ-UM-2012, SRC-WIKI-RD107, SRC-WIKI-SOYUZFG |
| ENG-SU-RD-108MM | RD-108MM | RD-108 / uprate | 1960s-1970s / retired | core, sustainer | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD107 |
| ENG-SU-RD-117 | RD-117 | RD-107 / derivative | 1973-2017 / retired | booster | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-GLOBALSEC-SOYUZU, SRC-SF101-SOYUZU, SRC-SKYROCKET-R7 |
| ENG-SU-RD-118 | RD-118 | RD-108 / derivative | 1973-2017 / retired | core, sustainer | LOX / kerosene | pump_fed_turbopump; separate_turbine_working_fluid (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-GLOBALSEC-SOYUZU, SRC-SKYROCKET-R7, SRC-WIKI-RD107 |

#### FAM-RD-109-BLOCK-E-PROPOSAL — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-109 | RD-109 | — / — | 1958 / cancelled | upper_stage | LOX / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD0109 |

#### FAM-RD-111 — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-111 | RD-111 | — / — | 1959-1960s / retired | booster, missile | LOX / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) | SRC-WIKI-NK9 |

#### FAM-RD-120 — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-120 | RD-120 | — / — | 1976-1985 dev; flown 1985- / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-170 — NPO Energomash, NPO Energomash (INFERRED), OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-151 | RD-151 | RD-191 / derivative | flown 2009-2013 / retired | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-SFN-KSLV-2010, SRC-SPACENEWS-12177, SRC-WIKI-NARO1 |
| ENG-SU-RD-170 | RD-170 | — / baseline | 1976-1985 dev; flown 1987-1988 (Energia) / retired | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 18 values (8 REPORTED) | SRC-NTRS-19910018906, SRC-GUINNESS-RD170, SRC-RSW-RD170 |
| ENG-SU-RD-171 | RD-171 | RD-170 / stage_specific | 1985-2000s / retired | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-RUWIKI-RD191, SRC-WIKI-RD170 |
| ENG-RU-RD-171M | RD-171M | RD-171 / block_upgrade | 2000s-; flown 2006- / retired | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 14 values (14 REPORTED) | SRC-GLAVKOSMOS-RD171M, SRC-PATENT-RU2544684C1, SRC-IAC13-20083 |
| ENG-RU-RD-171MV | RD-171MV | RD-171M / derivative | 2010s-2026; first flight 2026 / operational | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 7 values (0 REPORTED) | SRC-INTERFAX-RD171MV, SRC-WIKI-RD170, SRC-WIKI-SOYUZ5 |
| ENG-RU-RD-180 | RD-180 | RD-170 / derivative | 1994-1999 dev; flown 2000-2024 / retired | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 10 values (1 REPORTED) | SRC-GLAVKOSMOS-RD180, SRC-ULA-RD180-RECORD, SRC-PNP-RD180 |
| ENG-RU-RD-180V | RD-180V | RD-180 / derivative | 2010s (proposed) / proposed | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-RU-RD-181 | RD-181 | RD-191 / export | 2014-; flown 2016-2023 / retired | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 5 values (5 REPORTED) | SRC-GLAVKOSMOS-RD181, SRC-RSW-RD181, SRC-WIKI-ANTARES |
| ENG-RU-RD-191 | RD-191 | RD-170 / derivative | 1998-2014 dev; flown 2014- / operational | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 12 values (0 REPORTED) | SRC-RSW-RD191, SRC-RUWIKI-RD191, SRC-WIKI-RD191 |
| ENG-RU-RD-191M | RD-191M | RD-191 / uprate | 2010s-2020s / development | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-RU-RD-193 | RD-193 | RD-191 / derivative | 2010s (development/tests) / cancelled | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD191 |

#### FAM-RD-21X — OKB-456 (Glushko), OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-214 | RD-214 | — / — | dev 1952-1957; serial Perm Nov 1958 - Jul 1972 (Cyclowiki) … | booster, missile | AK-27I / TM-185 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | placeholder; 0 values (0 REPORTED) | SRC-CYCLOWIKI-RD214, SRC-WIKI-ENERGOMASH, SRC-WIKI-RD214 |
| ENG-SU-RD-215 | RD-215 | — / baseline | NOT_AUDITED / retired | missile | AK-27 / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 4 values (0 REPORTED) | SRC-WIKI-RD215 |
| ENG-SU-RD-216 | RD-216 | RD-215 / stage_specific | 1958-1961 / retired | booster, missile | AK-27I / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD215 |
| ENG-SU-RD-217 | RD-217 | RD-215 / derivative | NOT_AUDITED / retired | missile | AK-27I (per family; unverified) / UDMH | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD215 |
| ENG-SU-RD-218 | RD-218 | RD-217 / stage_specific | 1958-1961 / retired | missile | AK-27I / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD215 |
| ENG-SU-RD-219 | RD-219 | — / — | 1958-1961 / retired | missile | AK-27I / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD215 |

#### FAM-RD-253-275 — NPO Energomash, OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-253 | RD-253 | — / baseline | 1961-1965 dev; flown 1965- / retired | booster | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 11 values (0 REPORTED) | SRC-RSW-RD253, SRC-WIKI-RD253 |
| ENG-RU-RD-275 | RD-275 | RD-253 / uprate | 1987-1993 dev; flown 1995- / retired | booster | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 7 values (0 REPORTED) | SRC-RSW-RD253, SRC-WIKI-RD253 |
| ENG-RU-RD-275M | RD-275M | RD-275 / uprate | 2000s; flown 2007- / operational | booster | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-ILS-PMPG-A, SRC-WIKI-RD253 |

#### FAM-RD-25X — OKB-456 (Glushko), OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-250 | RD-250 | — / baseline | NOT_AUDITED / retired | booster, missile | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-RSW-RD250, SRC-WIKI-RD250, SRC-FAKTY-TURCHYNOV |
| ENG-SU-RD-251 | RD-251 | RD-250 / stage_specific | 1962-1966 / retired | missile | N2O4 / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD250 |
| ENG-SU-RD-252 | RD-252 | RD-250 / vacuum_variant | 1962-1966 / retired | missile | N2O4 / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD250 |
| ENG-SU-RD-261 | RD-261 | RD-250PM / stage_specific | 1960s-2009 / retired | booster | N2O4 / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-YUZHMASH-RD261, SRC-WIKI-RD250 |
| ENG-SU-RD-262 | RD-262 | RD-250 / vacuum_variant | 1960s-2009 / retired | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator | placeholder; 0 values (0 REPORTED) | SRC-WIKI-RD250, SRC-FAKTY-TURCHYNOV |

#### FAM-RD-26X — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-263 | RD-263 | — / baseline | 1969- / retired | missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-RD263 |
| ENG-SU-RD-264 | RD-264 | RD-263 / stage_specific | 1969-1975 / retired | booster, missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | placeholder; 0 values (0 REPORTED) | SRC-SKYROCKET-R36M, SRC-WIKI-RD263 |
| ENG-SU-RD-268 | RD-268 | — / — | 1970s / retired | missile | N2O4 / UDMH | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-RD263 |

#### FAM-RD-270 — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-270 | RD-270 | — / baseline | 1962-1968 (infobox) / 1960-1970 (text) / cancelled | booster | N2O4 / UDMH | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 8 values (0 REPORTED) | SRC-WIKI-RD270 |

#### FAM-RD-301 — OKB-456 (V. P. Glushko) / NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-RD-301 | RD-301 | — / — | 1969-1977 dev / cancelled | upper_stage | LF2 / NH3 | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-RD-56-KVD-1 — KB KhimMash (Isayev), OKB-2 / KB KhimMash (A. M. Isayev)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-KVD-1 | KVD-1 | RD-56 (11D56) / export | 1990s-; flown 2001- / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM) | sourced; 9 values (0 REPORTED) | SRC-ESA-KVD1-11D56, SRC-WIKI-KVD1 |
| ENG-SU-RD-56 | RD-56 | — / — | dev 1965-1972 (Wiki) / 1962-1974 (NPOEM PDF) / cancelled | upper_stage | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM) | placeholder; 0 values (0 REPORTED) | SRC-ESA-KVD1-11D56, SRC-WIKI-KVD1 |

#### FAM-RD-58-11D58 — NPO Energia, OKB-1 / NPO Energia, RSC Energia

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SU-11D58 | 11D58 | — / — | 1960s-; flown 1967- / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich | sourced; 0 values (0 REPORTED) | SRC-WIKI-RD58 |
| ENG-SU-11D58M | 11D58M | 11D58 / block_upgrade | 1970s-; flown 1974- / retired | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich | sourced; 9 values (0 REPORTED) | SRC-SSAU-2587, SRC-ASTRONAUTIX-RD58, SRC-WIKI-RD58 |
| ENG-RU-11D58MF | 11D58MF | 11D58M / derivative | 1990s- / operational | upper_stage | LOX / kerosene / synthin | pump_fed_turbopump; staged_combustion_ox_rich | sourced; 1 values (1 REPORTED) | SRC-SSAU-2587 |

#### FAM-RD-701-704-TRIPROPELLANT — NPO Energomash

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-RU-RD-701 | RD-701 | — / — | 1980s-1990s study / cancelled | booster | LOX / kerosene + LH2 (tripropellant) | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-RU-RD-704 | RD-704 | RD-701 / derivative | 1990s study / proposed | booster | LOX / kerosene + LH2 (tripropellant) | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-YUZHNOYE-RD-8XX — KB Yuzhnoye (Dnipro)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-UA-RD-855 | RD-855 | — / — | 1960s-2009 / retired | booster, rcs | N2O4 / UDMH | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-UA-RD-861 | RD-861 | — / — | 1970s-2009 / retired | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator | sourced; 2 values (0 REPORTED) | SRC-WIKI-RD861 |

### Ukraine (UA) — 7 variant records

#### FAM-RD-8 — KB Yuzhnoye (Dnipro)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-UA-RD-8 | RD-8 | — / — | 1970s-1985 dev; flown 1985- / retired | rcs, upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-YUZHMASH-RD8, SRC-YUZHNOYE-LPRE-BROCHURE, SRC-WIKI-RD8 |

#### FAM-YUZHNOYE-RD-8XX — KB Yuzhnoye (Dnipro), Yuzhnoye

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-UA-RD-801 | RD-801 | — / — | 2010s- / development | booster | LOX / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-UA-RD-810 | RD-810 | — / — | 2010s- / development | booster | LOX / kerosene | pump_fed_turbopump; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-UA-RD-843 | RD-843 | — / — | 2000s-; flown 2012- / operational | upper_stage | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed | sourced; 1 values (1 REPORTED) | SRC-YUZHNOYE-LPRE-BROCHURE |
| ENG-UA-RD-861K | RD-861K | RD-861 / derivative | 2000s-2010s / development | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator | sourced; 6 values (6 REPORTED) | SRC-YUZHMASH-RD861K, SRC-YUZHNOYE-RD861K |
| ENG-UA-RD-864 | RD-864 | — / — | NOT_AUDITED / retired | upper_stage | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 5 values (0 REPORTED) | SRC-WIKI-RD864 |
| ENG-UA-RD-870 | RD-870 | — / — | 2010s- / development | booster | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-RSW-RD870 |

## Europe

### Germany (DE) — 33 variant records

#### FAM-AESTUS — Astrium (Ottobrunn) with Boeing Rocketdyne, DASA / Astrium (Ottobrunn Space Propulsion Centre)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-AESTUS | Aestus | — / baseline | dev 1988-1995; flown 1997-2018 / retired | upper_stage | N2O4 / MMH | pressure_fed_regulated; none_pressure_fed (REPORTED) | sourced; 12 values (0 REPORTED) | SRC-ESA-EPS, SRC-MECAIND-2020-T1, SRC-WIKI-AESTUS |
| ENG-DE-AESTUS-II | Aestus II | Aestus / derivative | Pathfinder tests at White Sands, final (14th) test 3 May 20… | upper_stage | N2O4 / MMH | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-BOEING-RS72-2000, SRC-SFN-RS72-2000, SRC-WIKI-AESTUS |

#### FAM-AGGREGAT — HVA Peenemuende, Heeresversuchsanstalt (Kummersdorf/Peenemuende), Heeresversuchsanstalt Peenemuende (per general knowle…

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-A4-ENGINE | A-4 main engine | — / baseline | dev 1936-1942; flown 1942-1945; postwar captured use / reti… | missile | LOX / ethanol-water (75% alcohol) | pump_fed_turbopump; separate_turbine_working_fluid (SECONDARY_CLAIM) | sourced; 12 values (0 REPORTED) | SRC-DEUTSCHESMUSEUM-A4, SRC-ENGINEHISTORY-RPE02-2, SRC-ENGINEHISTORY-V2 |
| ENG-DE-A1-ENGINE | A1 engine | — / baseline | 1932-1934 / retired | experimental | LOX / alcohol | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-ENGINEHISTORY-V2, SRC-WIKI-AGGREGAT |
| ENG-DE-A3-ENGINE | A3 engine | A1 engine / uprate | 1936-1937; flown Dec 1937 / retired | experimental | LOX / 75% ethanol | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-RUSSIANSPACEWEB-A3, SRC-WIKI-AGGREGAT |
| ENG-DE-A5-ENGINE | A5 engine | A3 engine / derivative | 1938-1942 / retired | experimental | LOX / alcohol | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-AGGREGAT |

#### FAM-AQUILA — Isar Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-AQUILA | Aquila (SL) | — / baseline | flown 2025- / operational | booster, upper_stage | LOX / propane | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-ESF-ISAR, SRC-NSE-ELC-2025, SRC-ORBITCODEX-SPECTRUM |
| ENG-DE-AQUILA-VAC | Aquila VAC | Aquila (SL) / vacuum_variant | ? / operational | upper_stage | LOX / propane | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-NSE-ELC-2025 |

#### FAM-ARIANEGROUP-200N — ArianeGroup (ex-Snecma/Astrium heritage)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EU-ESM-RCS-220-N | ESM RCS 220 N | 200 N bipropellant thruster (ATV) / derivative | 2022- / operational | rcs | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-AG-200N, SRC-ESA-ESMPROP |

#### FAM-ASTRIS — ERNO / MBB (ASAT consortium)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-ASTRIS | Astris | — / — | flown 1966-1971 (Europa) / retired | upper_stage | N2O4 / Aerozine 50 | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 6 values (0 REPORTED) | SRC-DLR-ASTRIS, SRC-DEUTSCHESMUSEUM-EUROPA, SRC-WIKI-ASTRIS-ENGINE |

#### FAM-BMW-109-5XX — BMW (Bruckmuehl / Berlin-Spandau, Helmut von Zborowski group), BMW (Flugmotorenbau, Berlin-Spandau group)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-BMW-109-548 | BMW 109-548 | — / — | 1943-1945 / retired | missile | SV-Stoff (nitric acid) / Tonka 250 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-NASM-X4 |
| ENG-DE-BMW-109-558 | BMW 109-558 | — / — | 1944-1945 / cancelled | missile | nitric acid (Salbei) / Tonka (50% triethylamine / 50% xylidine per Wikipedia) | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-NASM-BMW109558, SRC-WIKI-BMW109558 |

#### FAM-BMW-109-7XX — BMW

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-BMW-109-718 | BMW 109-718 | — / — | 1944-1945 / experimental | aircraft_rocket | nitric acid / hydrocarbon (R-Stoff/Tonka? NOT_AUDITED) | pump_fed_turbopump; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-WIKI-BMW109718, SRC-WARBIRDS-ME262 |

#### FAM-HELIX — Rocket Factory Augsburg

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-HELIX | Helix | — / baseline | dev 2019- / development | booster, upper_stage | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-RFA-GUIDE, SRC-WIKI-RFAONE |
| ENG-DE-HELIX-VAC | Helix (vacuum) | Helix / vacuum_variant | ? / development | upper_stage | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-RFA-GUIDE, SRC-WIKI-RFAONE |
| ENG-DE-HELIX-2-0 | Helix 2.0 | Helix / uprate | ? / proposed | booster | LOX / RP-1 | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-RFA-GUIDE |

#### FAM-HWK-109 — Hellmuth Walter KG, Hellmuth Walter KG (Kiel)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-HWK-109-500 | HWK 109-500 | — / baseline | service 1942-1945 / retired | aircraft_rocket | none(mono) / HTP (T-Stoff) | pressure_fed_unspecified; none_pressure_fed (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-HWK109500 |
| ENG-DE-HWK-109-501 | HWK 109-501 | HWK 109-500 / derivative | WWII / retired | aircraft_rocket | HTP (T-Stoff) / kerosene + hydrazine hydrate | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-MUZEUM-KRAKOW-HWK |
| ENG-DE-HWK-109-507 | HWK 109-507 | HWK 109-500 / derivative | 1943-1944 / retired | missile | none(mono) / HTP (T-Stoff) | pressure_fed_blowdown; none_pressure_fed (REPORTED) | sourced; 3 values (0 REPORTED) | SRC-MUZEUM-KRAKOW-HWK, SRC-NASM-HWK109507, SRC-WIKI-HWK109507 |
| ENG-DE-HWK-109-509 | HWK 109-509 | — / baseline | 1943-1945 / retired | aircraft_rocket | HTP (T-Stoff, ~80%) / C-Stoff (30% hydrazine hydrate, 57% methanol, 13% water) | pump_fed_turbopump; separate_turbine_working_fluid (REPORTED) | sourced; 3 values (0 REPORTED) | SRC-NASM-HWK109509, SRC-WIKI-HWK109509 |
| ENG-DE-HWK-109-739 | HWK 109-739 | — / — | 1944-1945 / cancelled | missile | UNKNOWN / UNKNOWN | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-ENZIAN, SRC-ARMEDCONFLICTS-ENZIAN |

#### FAM-KONRAD — Dr. Konrad (Rheinmetall-Borsig / VfK?), Dr. Konrad (Rheinmetall-Borsig)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-KONRAD-VFK-613-A01 | Konrad VfK 613-A01 | — / — | 1944-1945 / cancelled | missile | nitric acid (likely, via Rheintochter heritage - INFERRED) / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-AWM-ENZIAN, SRC-WIKI-ENZIAN, SRC-ARMEDCONFLICTS-ENZIAN |
| ENG-DE-RHEINTOCHTER-R3-SUSTAINER | Rheintochter R3 sustainer | — / — | 1944-1945 / cancelled | missile | nitric acid / UNKNOWN | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-NASM-RHEINTOCHTER |

#### FAM-MBB-10-N — MBB (later DASA/EADS)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-GALILEO-RPM-10-N | Galileo RPM 10 N thruster | — / — | ? / retired | rcs | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-EADS-GALILEO-2003, SRC-NTRS-19840054177 |

#### FAM-MBB-400-N — MBB (later DASA/EADS)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-GALILEO-RPM-400-N | Galileo RPM 400 N main engine | — / — | ? / retired | spacecraft_main | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-EADS-GALILEO-2003, SRC-NTRS-19840054177 |

#### FAM-OTRAG — OTRAG (Lutz Kayser)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-OTRAG-CRPU-ENGINE | OTRAG CRPU | — / baseline | flights 1977-1983 / retired | booster, experimental | N2O4 (per Wikipedia summary; nitric acid per round-1 hint) / UNKNOWN (kerosene unconfirmed) | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-SPEKTRUM-OTRAG, SRC-WIKI-OTRAG, SRC-KSP-OTRAG |

#### FAM-S10 — ArianeGroup

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EU-S10-10-N-BIPROPELLANT-THRUSTER | S10 (10 N bipropellant thruster) | — / — | ? / operational | rcs | N2O4/MON-1/MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (4 REPORTED) | SRC-AG-10N, SRC-SATCAT-S1026 |

#### FAM-S22 — ArianeGroup

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EU-22-N-THRUSTER-ESA-GSTP-ARIANEGROUP | 22 N thruster (ESA GSTP, ArianeGroup) | — / — | ? / development | rcs | MON / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-ESA-22NASLLAM |

#### FAM-S400 — ArianeGroup, ArianeGroup (MBB/DASA/Astrium heritage)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EU-S400-12 | S400-12 | — / baseline | ? / operational | spacecraft_main | MON-1/MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-AG-APOGEE, SRC-SATCAT-S40012 |
| ENG-EU-S400-15 | S400-15 | S400-12 / derivative | ? / operational | spacecraft_main | MON-1/MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-AG-APOGEE |

#### FAM-TAIFUN — HVA Peenemuende / Elektromechanische Werke Karlshagen

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-TAIFUN-F-ENGINE | Taifun F engine | — / — | 1944-1945 / cancelled | missile | nitric acid (+10% H2SO4 per one source) / Tonka 841 (per one source) / organic fuel mixture | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-IAC-10-8811, SRC-WIKI-TAIFUN |

#### FAM-VFR — Verein fuer Raumschiffahrt (VfR)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-MIRAK-ENGINE | Mirak engine | — / — | 1930-1932 / retired | experimental | LOX / gasoline / alcohol (UNVERIFIED) | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-WASSERFALL — HVA Peenemuende (Walter Thiel)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-DE-WASSERFALL-ENGINE | Wasserfall engine | — / — | 1943-1945; test flights from Feb/Mar 1944 / cancelled | missile | SV-Stoff (RFNA ~94% HNO3/6% N2O4); later Salbei / mixed acid / Visol (vinyl isobutyl ether); later Optoline | pressure_fed_unspecified; none_pressure_fed (REPORTED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-WASSERFALL |

### France (FR) — 26 variant records

#### FAM-HM7 — SEP

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-HM4 | HM4 | — / baseline | 1960s development / cancelled | experimental | LOX / LH2 | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-HM7B |
| ENG-FR-HM7 | HM7 | HM4 / derivative | dev from 1973; flown 1979- / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-NTRS-19910018907, SRC-WIKI-HM7B |
| ENG-FR-HM7A | HM7A | HM7 / renamed | ? / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-ARIANE1 |
| ENG-FR-HM7B | HM7B | HM7 / uprate | qualified 1983; flown Ariane 2/3/4 and Ariane 5 ECA (ESC-A)… | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 16 values (2 REPORTED) | SRC-CNES-A5-TECH, SRC-AIAA-VG-ARIANE, SRC-WIKI-HM7B |

#### FAM-PROMETHEUS — ArianeGroup (ESA)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-PROMETHEUS | Prometheus | — / baseline | hot fire 2023- / development | booster, demonstrator | LOX / LCH4 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-ESA-PROMETHEUS, SRC-ESA-THEMIS, SRC-ESF-PROMETHEUS-2025 |

#### FAM-SEPR — SEPR, SEPR (Societe d'Etude de la Propulsion par Reaction)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-SEPR-25 | SEPR 25 | — / — | ? / retired | aircraft_rocket | nitric acid (UNVERIFIED) / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-FR-SEPR-66 | SEPR 66 | — / — | ? / retired | aircraft_rocket | nitric acid (UNVERIFIED) / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-FR-SEPR-841 | SEPR 841 | — / baseline | service 1961-1970 / retired | aircraft_rocket | nitric acid / kerosene (TX2 for ignition) - conflict: one source says TX2 was the fuel | other; other (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-SEPR84, SRC-POLOT-ROCKET11 |
| ENG-FR-SEPR-844 | SEPR 844 | SEPR 841 / derivative | ? / retired | aircraft_rocket | nitric acid / Jet TR-0 / JP-4 / JP-5 (aircraft fuel) | other; other (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-AAMA-SEPR, SRC-WIKI-SEPR84 |

#### FAM-VERONIQUE — LRBA, LRBA (Laboratoire de recherches balistiques et aerodynamiques)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-VERONIQUE-ENGINE | Veronique engine | — / baseline | work from Mar 1949; N version flown from 1952 / retired | experimental, other | nitric acid / turpentine / kerosene (version-dependent; sources conflict) | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-PLANET4589-CNESSR, SRC-WIKI-VERONIQUE |
| ENG-FR-VESTA-ENGINE | Vesta engine | Veronique engine / uprate | ordered 1962; static tests 1964; flown 1965-1969 / retired | other | nitric acid / turpentine | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-PLANET4589-CNESSR, SRC-UNIVERSALIS-FUSEESSONDES, SRC-WIKI-VESTA |

#### FAM-VEXIN — LRBA

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-CORALIE-ENGINE | Coralie engine | — / — | flown 1966-1971 (Europa) / retired | upper_stage | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 4 values (0 REPORTED) | SRC-IAC-10-6759, SRC-DEUTSCHESMUSEUM-EUROPA, SRC-WIKI-CORA |
| ENG-FR-VALOIS | Valois | Coralie engine / derivative | flown 1970-1975 (Diamant B, BP4) / retired | booster | N2O4 / UDMH | pressure_fed_unspecified; none_pressure_fed (REPORTED) | sourced; 4 values (0 REPORTED) | SRC-IAC-10-6759, SRC-WIKI-DIAMANT, SRC-ORBITCODEX-DIAMANTB |
| ENG-FR-VEXIN-B | Vexin B | — / — | flown 1964-1967 (Emeraude, Diamant A) / retired | booster | nitric acid (HNO3) / turpentine | pressure_fed_regulated; none_pressure_fed (REPORTED) | sourced; 4 values (0 REPORTED) | SRC-IAC-09-3159, SRC-WIKI-DIAMANT, SRC-WIKI-EMERAUDE |

#### FAM-VIKING — SEP, SEP (Societe Europeenne de Propulsion)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-VIKING-2 | Viking 2 | — / baseline | flown 1979- / retired | booster | N2O4 / UDMH | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 1 values (0 REPORTED) | SRC-DLR-VIKING-IMG, SRC-IAF-81-362, SRC-NTRS-19910018907 |
| ENG-FR-VIKING-2B | Viking 2B | Viking 2 / derivative | ? / retired | booster | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-VIKING, SRC-ORBITCODEX-ARIANE2 |
| ENG-FR-VIKING-4 | Viking 4 | Viking 2 / vacuum_variant | ? / retired | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 0 values (0 REPORTED) | SRC-WIKI-VIKING |
| ENG-FR-VIKING-4B | Viking 4B | Viking 4 / derivative | ? / retired | upper_stage | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 3 values (0 REPORTED) | SRC-WIKI-ARIANE3, SRC-WIKI-VIKING, SRC-ORBITCODEX-ARIANE2 |
| ENG-FR-VIKING-5 | Viking 5 | Viking 2 / uprate | ? / retired | booster | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-DLR-VIKING-IMG, SRC-WIKI-VIKING |
| ENG-FR-VIKING-5B | Viking 5B | Viking 5 / development_config | ? / retired | booster | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (REPORTED) | placeholder; 0 values (0 REPORTED) |  |
| ENG-FR-VIKING-5C | Viking 5C | Viking 5 / derivative | flown 1990-2003 (Ariane 4) / retired | booster, core | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-DLR-VIKING-GALLERY, SRC-FLIGHTGLOBAL-1000VIKING, SRC-FRWIKI-VIKING |
| ENG-FR-VIKING-6 | Viking 6 | Viking 5C / stage_specific | ? / retired | booster | N2O4 / UH 25 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-SKYROCKET-ARIANE44L, SRC-WIKI-VIKING |

#### FAM-VINCI — Snecma / ArianeGroup (ESA programme)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-VINCI | Vinci | — / baseline | dev 1998-2018 (qualified 2018); first flight 9 Jul 2024 / o… | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (REPORTED) | sourced; 11 values (1 REPORTED) | SRC-DLR-VINCI-NOZZLE-2010, SRC-ESA-A6ENGINES, SRC-ESA-VINCI-60S |

#### FAM-VULCAIN — SEP (prime) with European partners; later Snecma / ArianeGroup, Snecma (Safran/ArianeGroup)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-FR-VULCAIN | Vulcain | — / baseline | first ignition Jul 1990; flown 1996-2009 / retired | core | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 7 values (0 REPORTED) | SRC-ESA-VULCAIN, SRC-NTRS-19910018907, SRC-HANDWIKI-VULCAIN |
| ENG-FR-VULCAIN-2 | Vulcain 2 | Vulcain / uprate | flown 2002-2023 / retired | core | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 20 values (1 REPORTED) | SRC-CNES-A5-TECH, SRC-ESA-A5ECA-NEWELEM, SRC-ESA-ESAMI-VULCAIN |
| ENG-FR-VULCAIN-2-1 | Vulcain 2.1 | Vulcain 2 / derivative | first flight 9 Jul 2024 (Ariane 6 VA262) / operational | core | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 2 values (0 REPORTED) | SRC-ESA-A6ENGINES, SRC-METALAM-V21, SRC-3DPI-V21 |

### United Kingdom (GB) — 22 variant records

#### FAM-ARMSTRONG-SIDDELEY — Armstrong Siddeley, Armstrong Siddeley (from RAE Westcott work)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-BETA | Beta | — / — | late 1940s / cancelled | aircraft_rocket, experimental | HTP / C-fuel (57% methanol, 30% hydrazine hydrate, 13% water) | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-BETA |
| ENG-GB-SCREAMER | Screamer | — / — | dev 1946-1958; first static test Mar 1954 / cancelled | aircraft_rocket | LOX / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-SCREAMER |
| ENG-GB-SNARLER | Snarler | — / — | early 1950s / cancelled | aircraft_rocket | LOX / methanol/water | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-SCREAMER |

#### FAM-DE-HAVILLAND-HTP — de Havilland Engine Co.

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-DOUBLE-SPECTRE | Double Spectre | Spectre / derivative | late 1950s-1961 / retired | aircraft_rocket, missile | HTP / kerosene | UNKNOWN; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-NASM-DOUBLESPECTRE, SRC-WIKI-SPECTRE |
| ENG-GB-SPECTRE | Spectre | — / baseline | 1950s / cancelled | aircraft_rocket | HTP / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-DHMUSEUM-SPECTRE, SRC-WIKI-SPECTRE |
| ENG-GB-SPRITE | Sprite | — / baseline | Comet RATO trials from May 1951 / cancelled | aircraft_rocket | none(mono) / HTP | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-WIKI-SPRITE |
| ENG-GB-SUPER-SPRITE | Super Sprite | Sprite / derivative | production approved 1955 / retired | aircraft_rocket | HTP / kerosene | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-DHMUSEUM-SPECTRE, SRC-NASM-SUPERSPRITE, SRC-WIKI-SPRITE |

#### FAM-GAMMA — Armstrong Siddeley (Bristol Siddeley from 1959), Armstrong Siddeley / Bristol Siddeley

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-GAMMA-2 | Gamma 2 | Gamma 301 / vacuum_variant | flown 1969-1971 / retired | upper_stage | HTP (85% H2O2) / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-SCIMUS-GAMMA2, SRC-WIGHT-BLACKARROW, SRC-WIKI-GAMMA |
| ENG-GB-GAMMA-201 | Gamma 201 | — / baseline | flown 1958-1960? / retired | booster | HTP (85% H2O2) / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-JBIS-GAMMA-1990, SRC-WIKI-GAMMA |
| ENG-GB-GAMMA-301 | Gamma 301 | Gamma 201 / uprate | ? / retired | booster | HTP (85% H2O2) / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-JBIS-GAMMA-1990, SRC-WIKI-GAMMA |
| ENG-GB-GAMMA-8 | Gamma 8 | Gamma 301 / derivative | flown 1969-1971 / retired | booster | HTP (85% H2O2) / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIGHT-BLACKARROW, SRC-WIKI-GAMMA |
| ENG-GB-STENTOR | Stentor | — / — | service 1962-1970 / retired | missile | HTP / kerosene | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-SCIMUS-GAMMA2, SRC-WIKI-STENTOR, SRC-BCAR-BLUESTEEL |

#### FAM-LEROS — Nammo UK, Nammo UK (formerly BAe / Royal Ordnance / AMPAC-ISP / Moog-ISP)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-LEROS-1B | LEROS 1b | — / — | ? / operational | orbital_maneuver, spacecraft_main | MON-3 / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 8 values (6 REPORTED) | SRC-AMPAC-JUNO-2011, SRC-NAMMO-LEROS1B, SRC-ENGINEER-JUNO |
| ENG-GB-LEROS-1C | LEROS 1c | — / — | ? / operational | orbital_maneuver, spacecraft_main | MON / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-LEROS |
| ENG-GB-LEROS-2B | LEROS 2b | — / — | ? / operational | orbital_maneuver, spacecraft_main | MON / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-LEROS |
| ENG-GB-LEROS-4 | LEROS 4 | — / — | ? / unknown | orbital_maneuver, spacecraft_main | MON / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-LEROS |
| ENG-GB-LEROS-4-ET | LEROS 4-ET | LEROS 4 / uprate | ? / operational | lander_descent, spacecraft_main | MON / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-BLUEGHOST, SRC-WIKI-LEROS |

#### FAM-ORBEX — Orbex

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-ORBEX-PRIME-ENGINE | Orbex Prime engine (name not found) | — / baseline | unveiled 2019 / development | booster, upper_stage | LOX / bio-propane | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-ORBEX-2019-PR, SRC-NEWATLAS-ORBEX |

#### FAM-RZ — Rolls-Royce, Rolls-Royce (from Rocketdyne S-3D)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-RZ-1 | RZ.1 | — / baseline | mid/late 1950s / cancelled | missile | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-GRACES-BLUESTREAK, SRC-WIKI-RZ2 |
| ENG-GB-RZ-2 | RZ.2 | RZ.1 / derivative | 1958-1971; flown on Blue Streak/Europa 1964-1971 / retired | booster | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-ARMAGH-BLUESTREAK, SRC-GRACES-BLUESTREAK, SRC-VERKEHRSHAUS-RZ2 |

#### FAM-SKYRORA — Skyrora

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-GB-SKYFORCE-2 | Skyforce-2 (70 kN; name per search summary) | — / baseline | ? / development | booster, upper_stage | HTP (INFERRED from Skyrora family) / kerosene (INFERRED) | UNKNOWN; UNKNOWN | sourced; 1 values (1 REPORTED) | SRC-SKYRORA-WEB, SRC-3DPI-SKYRORA-70KN |
| ENG-GB-SKYLARK-L-ENGINE | Skylark L engine (30 kN; formerly 'Skyrora 1') | — / baseline | flight attempt Oct 2022 / unknown | booster | HTP / kerosene | pressure_fed_unspecified; none_pressure_fed (REPORTED) | sourced; 1 values (0 REPORTED) | SRC-SKYRORA-WEB, SRC-WIKI-SKYRORA |

### Italy (IT) — 2 variant records

#### FAM-M10 — Avio (with heritage from KBKhA RD-0146 collaboration), Avio + KBKhA (RU)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IT-MIRA | LM10-MIRA | — / development_config | test campaign June 2014 (Voronezh) / retired | demonstrator | LOX / LNG | pump_fed_turbopump; expander_closed (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-IAC07-7632, SRC-IAC15-30730, SRC-WIKI-M10 |
| ENG-IT-M10 | M10 | — / baseline | dev 2014-; TCA hot fire 2020; engine tests from May 2022 / … | upper_stage | LOX / LCH4 | pump_fed_turbopump; expander_closed (REPORTED) | sourced; 4 values (0 REPORTED) | SRC-ESA-VEGAE, SRC-EUCASS2019-0315, SRC-WIKI-M10 |

### Spain (ES) — 3 variant records

#### FAM-TEPREL — PLD Space

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-ES-TEPREL-B | TEPREL-B | — / baseline | flown 2023 / retired | booster | LOX / kerosene | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-NSF-M1SN1, SRC-WIKI-MIURA1, SRC-WIKI-TEPREL |
| ENG-ES-TEPREL-C | TEPREL-C | TEPREL-B / derivative | development / development | booster | LOX / biokerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-ATALAYAR-M5, SRC-WIKI-MIURA5, SRC-SATNOW-TEPRELC |
| ENG-ES-TEPREL-C-VAC | TEPREL-C Vacuum | TEPREL-C / vacuum_variant | ? / development | upper_stage | LOX / biokerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-WIKI-TEPREL, SRC-SATNOW-TEPRELC |

### Sweden (SE) — 3 variant records

#### FAM-HPGP — ECAPS (Bradford ECAPS)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-SE-HPGP-1N | HPGP 1N | — / — | ? / operational | rcs | none(mono) / LMP-103S (ADN-based) | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 5 values (0 REPORTED) | SRC-NDIA-ECAPS-2009, SRC-SATNOW-HPGP1N |
| ENG-SE-HPGP-22N | HPGP 22N | — / — | ? / operational | rcs | none(mono) / LMP-103S (ADN-based) | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 4 values (1 REPORTED) | SRC-NTRS-20210022261, SRC-SATCAT-HPGP22N |
| ENG-SE-HPGP-5N | HPGP 5N | — / — | ? / development | rcs | none(mono) / LMP-103S (ADN-based) | pressure_fed_blowdown; none_pressure_fed (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-SATSEARCH-HPGP5N |

### Europe (multinational) (EU) — 1 variant records

#### FAM-ARIANEGROUP-200N — Snecma (Safran) / ArianeGroup

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EU-200-N-BIPROPELLANT-THRUSTER-ATV | 200 N bipropellant thruster (ATV) | — / — | ? / retired | orbital_maneuver, rcs | MON-3 / MMH | pressure_fed_regulated; none_pressure_fed (INFERRED) | sourced; 0 values (0 REPORTED) | SRC-AG-200N |

## Asia-Pacific

### China (CN) — 52 variant records

#### FAM-CHANG-E-LANDER-ENGINE — CASC (6th Academy) [developer not in summary]

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-7500N-VARIABLE-THRUST-ENGINE | 7500N变推力发动机 (Chang'e-3 7500 N variable-thrust engine) | — / — | ? / operational | lander_descent | NOT_REPORTED / NOT_REPORTED | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-SCISIN-CE3-7500N-2014, SRC-IFENG-CE4-ENGINE, SRC-TSINGHUA-7500N |

#### FAM-FENGYUN — Jiuzhou Yunjian

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-FENGYUN | Fengyun (烽云) | — / baseline | ? / development | booster | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-36KR-JZYJ |

#### FAM-JD-JIAODIAN-FOCUS — iSpace, iSpace (Beijing Interstellar Glory Space Technology)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-JD-1 | JD-1 | — / baseline | ? / development | core, demonstrator | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-IFENG-JD1, SRC-SPACENEWS-105372 |
| ENG-CN-JD-2 | JD-2 | — / baseline | ? / development | core | LOX / LCH4 | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-IFENG-JD1, SRC-ITHOME-638884 |

#### FAM-LONGYUN — Jiuzhou Yunjian (九州云箭)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-LONGYUN | Longyun (龙云) | — / baseline | hot fire 2021- / development | booster | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-36KR-JZYJ, SRC-ITHOME-893006, SRC-JIEMIAN-14422448 |

#### FAM-SISP-490N-LAE — SISP, SISP (上海空间推进研究所)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-FY-25 | FY-25 (first-generation 490N liquid apogee engine) | — / — | developed by April 1990 / operational | spacecraft_main | NTO / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 5 values (5 REPORTED) | SRC-IAC03-LAE-CN, SRC-IAC11-490N-CN, SRC-IAC18-490N-SISP |
| ENG-CN-TQS492-2 | TQS492-2 (second-generation 490N LAE) | FY-25 / derivative | ? / operational | spacecraft_main | MON-1 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-IAC12-490N-GEN2, SRC-IAC18-490N-SISP |
| ENG-CN-490N-LAE-THIRD-GENERATION | Third-generation high-performance 490N LAE (SISP) | TQS492-2 / derivative | ? / development | spacecraft_main | MON-1 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-IAC18-490N-SISP |

#### FAM-THUNDER-LEITING — Deep Blue Aerospace, Deep Blue Aerospace (深蓝航天)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-LEIYU-THUNDER-R1 | Thunder-R1 (雷霆-R1) | — / baseline | tests 2022- / development | booster | LOX / kerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-BJNEWS-THUNDER, SRC-ITHOME-628718 |
| ENG-CN-THUNDER-RS | Thunder-RS (雷霆-RS) | — / baseline | tests 2025-2026 / development | booster | LOX / kerosene | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-STDAILY-2026-THUNDERRS |

#### FAM-TIANHUO — Space Pioneer, Space Pioneer (Beijing Tianbing Technology), UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-TH-11 | TH-11 | — / baseline | ? / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-WIKI-TH11 |
| ENG-CN-TH-12 | TH-12 | — / baseline | ? / operational | core | LOX / kerosene (coal-based aviation kerosene reported) | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 9 values (4 REPORTED) | SRC-SPACEPIONEER-TH12, SRC-ITHOME-655315, SRC-WIKI-TH12 |
| ENG-CN-TH-12V | TH-12V | TH-12 / vacuum_variant | ? / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 3 values (3 REPORTED) | SRC-SPACEPIONEER-TH12V |
| ENG-CN-TH-31 | TH-31 | — / — | ? / unknown |  | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-TQ-11 — LandSpace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-TQ-11 | TQ-11 | — / baseline | ? / retired | upper_stage | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-ITHOME-434823, SRC-WIKI-TQ15 |

#### FAM-TQ-12 — LandSpace, LandSpace (蓝箭航天)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-TQ-12 | TQ-12 | — / baseline | ? / retired | core | LOX / LCH4 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 12 values (5 REPORTED) | SRC-NCSTI-2023-TQ, SRC-NSF-ZQ2Y3, SRC-WIKI-TQ12 |
| ENG-CN-TQ-12A | TQ-12A | TQ-12 / uprate | ? / operational | core | LOX / LCH4 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-WIKI-TQ15, SRC-WIKI-ZQ3 |
| ENG-CN-TQ-12B | TQ-12B | TQ-12A / uprate | ? / development | core | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-ZQ3 |

#### FAM-TQ-15 — LandSpace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-TQ-15A | TQ-15A | TQ-12 (vacuum) / vacuum_variant | ? / operational | upper_stage | LOX / LCH4 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 10 values (4 REPORTED) | SRC-NCSTI-2023-TQ, SRC-BJNEWS-TQ15A, SRC-JIEMIAN-TQ |
| ENG-CN-TQ-15B | TQ-15B | TQ-15A / uprate | ? / development | upper_stage | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-ZQ3 |

#### FAM-WELKIN — Galactic Energy

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-WELKIN | Welkin (CQ-50) | — / baseline | dev 2020s; Pallas-1 maiden flight expected 2026 / developme… | booster | LOX / kerosene (RP-1) | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 7 values (3 REPORTED) | SRC-GE-CQ50-CN, SRC-GE-WELKIN-EN, SRC-10JQKA-CQ50 |
| ENG-CN-WELKIN-VAC | Welkin Vac | Welkin (CQ-50) / vacuum_variant | ? / development | upper_stage | LOX / kerosene | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-WIKI-WELKIN, SRC-ORBITCODEX-PALLAS |

#### FAM-YF-1 — CAS propulsion (later AALPT), CAS/7th Ministry propulsion (later AALPT), UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-1 | YF-1 | — / baseline | 1960s-1970s / retired | booster, missile | AK27S (inhibited RFNA, per WIKI) / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-CZ1, SRC-WIKI-YF1 |
| ENG-CN-YF-1B | YF-1B | YF-1 / derivative | ? / retired | booster | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-CZ1D, SRC-WIKI-YF1 |
| ENG-CN-YF-2 | YF-2 | YF-1 / stage_specific | ? / retired | booster, missile | AK27S / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF1 |
| ENG-CN-YF-3 | YF-3 | YF-1 / vacuum_variant | ? / retired | missile, upper_stage | AK27S (INFERRED from family) / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF3 |
| ENG-CN-YF-3A | YF-3A | YF-3 / derivative | ? / retired | upper_stage | AK27S / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-CZ1, SRC-WIKI-YF3 |

#### FAM-YF-100 — AALPT; Xi'an Aerospace Propulsion Institute (INFERRED), UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-100 | YF-100 | — / baseline | flown 2015- / operational | booster, core | LOX / kerosene (RP-type) | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 15 values (0 REPORTED) | SRC-IAC15-LOXKERO-REVIEW, SRC-WIKI-YF100, SRC-BILI-CV15113396 |
| ENG-CN-YF-100K | YF-100K | YF-100 / uprate | ? / development | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 5 values (0 REPORTED) | SRC-163-CZ10-TEST, SRC-PAPER-YF100K, SRC-BILI-CV15113396 |
| ENG-CN-YF-100L | YF-100L | YF-100 / derivative | ? / development | core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-PAPER-YF100K |
| ENG-CN-YF-100M | YF-100M | YF-100K / vacuum_variant | ? / development | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (INFERRED) | sourced; 2 values (0 REPORTED) | SRC-PAPER-YF100K, SRC-BILI-CV15113396 |

#### FAM-YF-115 — Xi'an Aerospace Propulsion Institute (AALPT)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-115 | YF-115 | — / baseline | ? / operational | upper_stage | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 7 values (0 REPORTED) | SRC-IAC16-YF115, SRC-MYNAVI-CHINA2, SRC-SF101-CZ6 |

#### FAM-YF-130 — AALPT

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-130 | YF-130 | — / baseline | dev 2010s-; full system test Nov 2022 / development | booster, core | LOX / kerosene | pump_fed_turbopump; staged_combustion_ox_rich (REPORTED) | sourced; 1 values (0 REPORTED) | SRC-SPACECOM-YF130, SRC-SPACENEWS-129757, SRC-WIKI-CZ9 |

#### FAM-YF-20 — AALPT (Academy of Aerospace Liquid Propulsion Technology), UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-20 | YF-20 | — / baseline | 1970s- / operational | booster, core, missile | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 5 values (0 REPORTED) | SRC-WIKI-YF20 |
| ENG-CN-YF-20B | YF-20B | YF-20 / uprate | 1990s- / operational | booster, core | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 6 values (0 REPORTED) | SRC-WEBLIO-YF20, SRC-WIKI-CZ2F |
| ENG-CN-YF-21 | YF-21 | YF-20 / stage_specific | ? / retired | core, missile | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF20 |
| ENG-CN-YF-21B | YF-21B | YF-21 / uprate | ? / operational | core | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-GS-CZ2D, SRC-WEBLIO-YF20, SRC-WIKI-YF20 |
| ENG-CN-YF-22 | YF-22 | YF-20 / vacuum_variant | ? / retired | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF20, SRC-WIKI-YF24 |
| ENG-CN-YF-22B | YF-22B | YF-22 / uprate | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF24 |
| ENG-CN-YF-23 | YF-23 | — / stage_specific | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-GS-CZ2D, SRC-WIKI-YF23 |
| ENG-CN-YF-24 | YF-24 | — / stage_specific | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-CZ2F, SRC-WIKI-YF20, SRC-WIKI-YF24 |
| ENG-CN-YF-24C | YF-24C | YF-24 / stage_specific | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-GS-CZ2D |
| ENG-CN-YF-25 | YF-25 | YF-20 / stage_specific | ? / operational | booster | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-WIKI-YF20 |

#### FAM-YF-209 — AALPT (CASC 6th Academy)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-209 | YF-209 | — / baseline | ? / development | core | LOX / LCH4 | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-CHINADAILY-YF209, SRC-STDAILY-2024 |

#### FAM-YF-215 — AALPT

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-215 | YF-215 | — / baseline | ? / development | core | LOX / LCH4 | pump_fed_turbopump; full_flow_staged_combustion (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-WIKI-CZ9, SRC-WIKI-YF215 |

#### FAM-YF-40 — UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-40 | YF-40 | — / baseline | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 8 values (0 REPORTED) | SRC-GS-CZ4, SRC-WIKI-CZ4B, SRC-WIKI-YF40 |
| ENG-CN-YF-40A | YF-40A | YF-40 / derivative | ? / operational | upper_stage | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-EDA-CZ4C |

#### FAM-YF-50 — CALT (stage) / engine developer UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-50D | YF-50D | — / stage_specific | ? / operational | kick_stage, upper_stage | N2O4 / UDMH | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-WIKI-YZ |

#### FAM-YF-73 — UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-73 | YF-73 | — / baseline | dev 1970-; flown 1984-2000 / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-WIKI-CZ3, SRC-WIKI-YF73 |

#### FAM-YF-75 — AALPT (Beijing Aerospace Propulsion Institute — UNVERIFIED), UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-75 | YF-75 | — / baseline | ? / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 3 values (0 REPORTED) | SRC-IAC13-18525, SRC-WIKI-YF75 |
| ENG-CN-YF-75D | YF-75D | YF-75 / derivative | ? / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_closed (SECONDARY_CLAIM) | sourced; 6 values (0 REPORTED) | SRC-WIKI-YF75D |

#### FAM-YF-77 — AALPT (Beijing, INFERRED)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-CN-YF-77 | YF-77 | — / baseline | flown 2016- / operational | core | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 14 values (2 REPORTED) | SRC-IAC13-17679, SRC-GOTAIK-2021, SRC-WIKI-YF77 |

### Japan (JP) — 19 variant records

#### FAM-AKATSUKI-OME — JAXA / IHI Aerospace (manufacturer NOT confirmed)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-AKATSUKI-OME | Akatsuki OME (500 N ceramic thruster) | — / — | ? / retired | spacecraft_main | NTO / N2H4 | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (2 REPORTED) | SRC-JAXA-AKATSUKI-2010, SRC-WIKI-AKATSUKI |

#### FAM-BT-4 — IHI Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-BT-4 | BT-4 | — / — | ? / operational | orbital_maneuver, spacecraft_main | NTO / N2H4 | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 7 values (0 REPORTED) | SRC-WIKI-BT4, SRC-MECO-CYGNUS-REBOOST-2018, SRC-SATCAT-BT4 |

#### FAM-COSMOS — Interstellar Technologies

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-INTERSTELLAR-TECHNOLOGIES-ZERO-FIRST-STAGE-ENGINE-COSMOS | COSMOS | — / baseline | development / development | booster | LOX / liquid biomethane | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 1 values (1 REPORTED) | SRC-IST-LV, SRC-IST-PP-2024, SRC-IST-TP-2024 |

#### FAM-IHI-HBT — IHI Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-HBT-1 | HBT-1 | — / — | ? / unknown | rcs | MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-HANDWIKI-HTV |
| ENG-JP-HBT-5 | HBT-5 | — / — | ? / retired | orbital_maneuver, spacecraft_main | MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (0 REPORTED) | SRC-IAC05-HTVPM, SRC-HANDWIKI-HTV, SRC-WIKI-BT4 |

#### FAM-LE-3 — NASDA / MHI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-3 | LE-3 | — / baseline | flown 1975-1982 (N-I) [background] / retired | upper_stage | N2O4 (background, unverified) / Aerozine-50 (background, unverified) | UNKNOWN; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-FORSYTH-NIPPON, SRC-WIKI-N1 |

#### FAM-LE-5 — JAXA / MHI, NASDA / MHI, NASDA/JAXA, MHI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-5 | LE-5 | — / baseline | flown 1986-1992 / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (REPORTED) | sourced; 4 values (0 REPORTED) | SRC-ASTRONAUTIX-LE5, SRC-WIKI-LE5 |
| ENG-JP-LE-5A | LE-5A | LE-5 / derivative | flown 1994-1999 / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (REPORTED) | sourced; 6 values (0 REPORTED) | SRC-WIKI-LE5 |
| ENG-JP-LE-5B | LE-5B | LE-5A / derivative | flown 1999- (H-II F8), H-IIA / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM) | sourced; 11 values (0 REPORTED) | SRC-WEBLIO-LE5, SRC-WIKI-LE5 |
| ENG-JP-LE-5B-2 | LE-5B-2 | LE-5B / block_upgrade | flown 2009- / retired | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM) | sourced; 8 values (0 REPORTED) | SRC-IAC08-LE5B, SRC-WIKI-LE5 |
| ENG-JP-LE-5B-3 | LE-5B-3 | LE-5B-2 / block_upgrade | flown 2023- / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (REPORTED) | sourced; 5 values (4 REPORTED) | SRC-MHI-LE5B, SRC-WIKI-LE5 |

#### FAM-LE-7 — NASDA / MHI, NASDA/JAXA, MHI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-7 | LE-7 | — / baseline | flown 1994-1999 (H-II) / retired | core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (REPORTED) | sourced; 14 values (5 REPORTED) | SRC-JAXA-H2, SRC-MEXT-SAC-1997, SRC-WIKI-LE7 |
| ENG-JP-LE-7A | LE-7A | LE-7 / derivative | flown 2001-2025 / retired | core | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (REPORTED) | sourced; 19 values (9 REPORTED) | SRC-JAXAREPO-45156, SRC-MEXT-SAC-1997, SRC-MHI-LE7A |

#### FAM-LE-8 — JAXA / IHI (IHI Aerospace)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-8 | LE-8 | — / baseline | dev 2000s; GX cancelled 2009 / cancelled | upper_stage | LOX / LNG | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-JAXA-SAC-2010-LNG, SRC-IAC12-14616, SRC-WEBLIO-LE8 |

#### FAM-LE-9 — JAXA / MHI (system), IHI (turbopumps)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-9 | LE-9 | — / baseline | dev 2015-2023; flown 2023- / operational | core | LOX / LH2 | pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM) | sourced; 12 values (4 REPORTED) | SRC-IHI-GIHO-LE9-TP, SRC-JAXA-PRESS-LE9-2017, SRC-MHI-LE9 |

#### FAM-LE-X — UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-LE-X | LE-X | — / — | ? / proposed |  | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-MB-3 — UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-MB-3-LICENCE-BUILT-N-I-N-II-H-I | MB-3 (licence-built, N-I/N-II/H-I) | — / export | ? / unknown |  | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

#### FAM-MB-60 — Boeing Rocketdyne + MHI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-MB-60 | MB-60 | — / baseline | dev from 2000; halted / cancelled | upper_stage | LOX / LH2 | pump_fed_turbopump; expander_bleed (SECONDARY_CLAIM) | sourced; 2 values (1 REPORTED) | SRC-BOEING-2000-MB60, SRC-WIKI-MARC60, SRC-WIKI-RL60 |

#### FAM-MOMO — Interstellar Technologies

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-JP-INTERSTELLAR-TECHNOLOGIES-MOMO-ENGINE | MOMO engine | — / baseline | flown 2017- / operational | booster | LOX / ethanol | pressure_fed_unspecified; none_pressure_fed (SECONDARY_CLAIM) | sourced; 1 values (0 REPORTED) | SRC-SLN-MOMO |

### India (IN) — 19 variant records

#### FAM-AGNILET — AgniKul Cosmos

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-AGNILET | Agnilet | — / baseline | flown 2024 (Agnibaan SOrTeD) / development | booster, demonstrator | LOX (sub-cooled) / ATF (aviation turbine fuel) | pump_fed_electric; electric_pump (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-IE-AGNIBAAN, SRC-M3D-AGNIKUL-2026, SRC-MACHINIST-AGNIKUL |

#### FAM-CE-20 — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-CE-20 | CE-20 | — / baseline | flown 2017- / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 9 values (0 REPORTED) | SRC-WIKI-CE20, SRC-IASGYAN-CE20 |

#### FAM-CE-7-5 — ISRO LPSC, ISRO LPSC (CUSP)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-CE-7-5 | CE-7.5 | — / baseline | flown 2010- / operational | upper_stage | LOX / LH2 | pump_fed_turbopump; staged_combustion_fuel_rich (SECONDARY_CLAIM) | sourced; 7 values (0 REPORTED) | SRC-WIKI-CE75, SRC-BHARATNOTES-CRYO, SRC-SLIDESHARE-CRYO |
| ENG-IN-CE-7-5-STEERING-ENGINE | CE-7.5 steering engine (designation unknown) | CE-7.5 / other | ? / operational | upper_stage | LOX (INFERRED 'cryogenic') / LH2 (INFERRED) | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-CE75, SRC-BHARATNOTES-CRYO |

#### FAM-DHAWAN — Skyroot Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-DHAWAN-1 | Dhawan-1 | — / baseline | test 2021 / development | demonstrator, upper_stage | LOX / LNG | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-COLDFACTS-DHAWAN1, SRC-CHANAKYA-DHAWAN1 |
| ENG-IN-DHAWAN-2 | Dhawan-2 | Dhawan-1 / derivative | test 2023 / development | demonstrator, upper_stage | LOX / LNG | UNKNOWN; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-M3D-SKYROOT-2026, SRC-WIKI-SKYROOT |

#### FAM-ISRO-800N-THROTTLEABLE — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-800-N-THROTTLEABLE-ENGINE | 800 N throttleable engine (Chandrayaan-3 Vikram) | — / — | ? / operational | lander_descent | MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 2 values (1 REPORTED) | SRC-ISRO-CH3-PAGE, SRC-EOPORTAL-CH3, SRC-THEWEEK-CH3 |

#### FAM-ISRO-LAM-440N — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-LAM-440-N | 440 N Liquid Apogee Motor | — / baseline | ? / operational | orbital_maneuver, spacecraft_main | MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 7 values (4 REPORTED) | SRC-IAC16-32550, SRC-NSF-CH3-2023, SRC-SF101-LAM |

#### FAM-ISRO-THRUSTERS — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-58-N-THRUSTER | 58 N attitude thruster (Chandrayaan-3) | — / — | ? / operational | rcs | MON-3 / MMH | pressure_fed_unspecified; none_pressure_fed (INFERRED) | sourced; 1 values (1 REPORTED) | SRC-ISRO-CH3-PAGE |

#### FAM-PS4 — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-PS4-ENGINE-L-2-5 | L-2-5 (PS4 engine) | — / baseline | ? / operational | upper_stage | MON-3 / MMH | UNKNOWN; UNKNOWN | sourced; 3 values (0 REPORTED) | SRC-ISRO-PSLVC27, SRC-FRANCOWIKI-PSLV, SRC-METALAM-PS4 |

#### FAM-RAMAN — Skyroot Aerospace

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-RAMAN | Raman (engine series) | — / baseline | ? / development | rcs, upper_stage | hypergolic oxidizer (unspecified) / hypergolic fuel (unspecified) | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-WIKI-VIKRAM |

#### FAM-SE-2000 — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-SCE-200 | SE-2000 | — / baseline | development 2010s- / development | core | LOX / kerosene (ISROsene) | pump_fed_turbopump; staged_combustion_ox_rich (SECONDARY_CLAIM) | sourced; 5 values (2 REPORTED) | SRC-ISRO-SEMICRYO-2025, SRC-WIKI-SE2000 |

#### FAM-VIKAS — ISRO LPSC

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IN-VIKAS-HIGH-THRUST | High Thrust Vikas Engine (HTVE) | Vikas-2B? / uprate | qualified 2018 / operational | core, sustainer | N2O4 / UH25 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 2 values (0 REPORTED) | SRC-WIKI-VIKAS, SRC-VAJIRAM-VIKAS |
| ENG-IN-VIKAS-HUMAN-RATED | Human-rated Vikas (L110-G) | Vikas-X? / derivative | qualification 2023 / development | core | N2O4 / UH25 (INFERRED) | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 1 values (1 REPORTED) | SRC-ISRO-VIKAS-TEST |
| ENG-IN-VIKAS | Vikas | — / baseline | dev 1970s-; flown 1993- (PSLV) / operational | booster, core, sustainer, upper_stage | N2O4 / UDMH / UH25 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 10 values (0 REPORTED) | SRC-ISRO-VIKAS-TEST, SRC-SPACENEWS-33640, SRC-WIKI-VIKAS |
| ENG-IN-VIKAS-L40-STRAP-ON | Vikas (L40 strap-on) | Vikas / stage_specific | ? / unknown |  | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |
| ENG-IN-VIKAS-4 | Vikas-4 | Vikas / stage_specific | ? / unknown | sustainer | N2O4 / UDMH | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-ANANTAM-VIKAS |
| ENG-IN-VIKAS-4B | Vikas-4B | Vikas-4 / stage_specific | ? / unknown | sustainer | N2O4 / UH25 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-ANANTAM-VIKAS |
| ENG-IN-VIKAS-X | Vikas-X | Vikas / stage_specific | ? / operational | core | N2O4 / UH25 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 0 values (0 REPORTED) | SRC-ANANTAM-VIKAS |

### South Korea (KR) — 4 variant records

#### FAM-KRE — KARI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-KR-KRE-007 | KRE-007 | — / baseline | dev 2014-2019; flown 2021- / operational | upper_stage | LOX / Jet-A | pump_fed_turbopump; gas_generator (INFERRED) | sourced; 3 values (0 REPORTED) | SRC-SFN-NURI-2021, SRC-WIKI-NURI |
| ENG-KR-KRE-075 | KRE-075 | — / baseline | dev 2010-2021; flown 2018 (TLV), 2021- / operational | booster, core | LOX / Jet A-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 15 values (3 REPORTED) | SRC-EUCASS2019-0521, SRC-KSCI-KARI-2009-KRE75, SRC-KSCI-KARI-2016-TP |
| ENG-KR-KRE-075-2ND-STAGE | KRE-075 (2nd-stage altitude version) | KRE-075 / vacuum_variant | ? / operational | upper_stage | LOX / Jet A-1 | pump_fed_turbopump; gas_generator (SECONDARY_CLAIM) | sourced; 4 values (0 REPORTED) | SRC-WIKI-KRE075, SRC-NAMU-KRE075 |

#### FAM-KSR-III — KARI

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-KR-KSR-III-ENGINE | KSR-III engine (13 tf class) | — / baseline | flown 2002 / retired | booster, demonstrator | LOX / kerosene (Jet A-1 in subscale tests) | pressure_fed_regulated; none_pressure_fed (REPORTED) | sourced; 2 values (1 REPORTED) | SRC-KSCI-KSR3-FPS, SRC-KSCI-KSR3-SUBSCALE, SRC-WIKI-KSR3 |

### North Korea (KP) — 4 variant records

#### FAM-NODONG — developer not recorded

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-KP-NODONG-ENGINE | Nodong engine | — / baseline | ? / unknown | booster, missile | ? / ? | pump_fed_turbopump; UNKNOWN | sourced; 2 values (0 REPORTED) | SRC-ACW-502404, SRC-FAS-ND1, SRC-GS-ND-A-SPECS |

#### FAM-PAEKTUSAN — developer not recorded

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-KP-HWASONG-14-MAIN-ENGINE | Hwasong-14 first-stage engine (single-chamber RD-250 variant) | — / derivative | flown 2017 / unknown | missile | hypergolic (unspecified) / hypergolic (unspecified) | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-CSIS-HS14 |
| ENG-KP-HWASONG-15-FIRST-STAGE-ENGINE | Hwasong-15 first-stage engine (two combustors, common turbopump) | — / derivative | flown 2017 / unknown | missile | ? / ? | pump_fed_turbopump; UNKNOWN | sourced; 1 values (0 REPORTED) | SRC-WIKI-HS15 |
| ENG-KP-HWASONG-14-15-MAIN-ENGINE-PAEKTUSAN | Paektusan engine family (RD-250-derived) | — / — | ? / unknown | missile | N2O4 (INFERRED 'high-energy hypergolic') / UDMH (INFERRED) | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-CSIS-HS14, SRC-WIKI-HS14, SRC-WIKI-HS15 |

## Middle East / Africa

### Iran (IR) — 5 variant records

#### FAM-NODONG — developer not recorded

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IR-SHAHAB-3-ENGINE | Shahab-3 engine | Nodong engine / export | ? / unknown | booster, missile | ? / ? | pump_fed_turbopump; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-GS-ND-A-SPECS, SRC-NTI-SIMORGH |

#### FAM-R-27-VERNIER — developer not recorded

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IR-SAFIR-SECOND-STAGE-ENGINE-PAIR | Safir second-stage engines (pair, designation unknown) | — / stage_specific | ? / unknown | upper_stage | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-ACW-302585, SRC-ARMSCONTROL-2008 |
| ENG-IR-SIMORGH-SECOND-STAGE-ENGINES | Simorgh second-stage engines (4 low-thrust, R-27/SS-N-6 steering-engine heritage) | — / stage_specific | ? / unknown | upper_stage | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-CSIS-SIMORGH, SRC-UCS-SIMORGH |

#### FAM-SHAHAB-NODONG — Iran (unknown entity)

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-IR-SAFIR-FIRST-STAGE-ENGINE | Safir first-stage engine (designation unknown) | — / stage_specific | ? / unknown | booster | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-ACW-302585, SRC-SKYROCKET-SAFIR |
| ENG-IR-SIMORGH-FIRST-STAGE-ENGINE-CLUSTER | Simorgh first-stage cluster (4 x Shahab-3/Nodong + 4 steering engines) | — / stage_specific | ? / unknown | booster | ? / ? | UNKNOWN; UNKNOWN | sourced; 0 values (0 REPORTED) | SRC-CSIS-SIMORGH, SRC-NTI-SIMORGH |

### Egypt (EG) — 1 variant records

#### FAM-AL-ZAFIR — UNKNOWN

| ID | Designation | Parent / relation | Period / status | Role | Propellants | Feed; cycle (evidence) | Evidence | Key sources |
|---|---|---|---|---|---|---|---|---|
| ENG-EG-AL-ZAFIR-AL-KAHIR-ENGINE | Al-Zafir / Al-Kahir engine | — / — | ? / retired |  | UNKNOWN / UNKNOWN | UNKNOWN; UNKNOWN | placeholder; 0 values (0 REPORTED) |  |

## Excluded candidates

| ID | Designation | Reason |
|---|---|---|
| ENG-CN-THUNDER-R2 | Thunder-R2 (existence unconfirmed) | Round-1 placeholder from the orchestrator scope list; round 2 found no source for its existence (closest: Thunder-RS). Excluded, not deleted from history. |

## Alias problems recorded

Aliases that point at more than one record, and aliases dropped during merge:

| Alias | Kind | Engine | Sourced | Note |
|---|---|---|---|---|
| 14D15 | index | ENG-RU-NK-33A | False |  |
| 14D15 | index | ENG-SU-NK-33 | True |  |
| 15D117 | DROPPED | ENG-SU-RD-264 | False | round-1 unsourced; r2_ussr found RD-264 = 15D119 and 15D117 = RD-263 unit |
| H-1 | manufacturer | ENG-US-H-1-165K | True |  |
| MVac | common | ENG-US-MERLIN-1C-VACUUM | False |  |
| MVac | common | ENG-US-MERLIN-1D-VACUUM | True |  |
| Merlin Vacuum | common | ENG-US-MERLIN-1C-VACUUM | True |  |
| Merlin Vacuum | manufacturer | ENG-US-MERLIN-1D-VACUUM | True |  |
| RS-18 | former_name | ENG-US-LM-ASCENT-ENGINE | False |  |
