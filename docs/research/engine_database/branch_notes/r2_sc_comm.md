# DB-0 round 2, branch "r2_sc_comm" (spacecraft and commercial gaps), as of 2026-10-08

## Access conditions
- **Only WebSearch was used.** WebFetch and curl were not attempted again, because the round-2 addendum says they are blocked. I made 37 of the 38 allowed searches.
  - Every source has `access: search_result_only`.
  - Every value comes from a summary written by the search tool. Before using any value, re-open the cited document and pin the locator.
- **How statuses were assigned:**
  - `REPORTED` is used only when the summary tied the number to a named Tier A or B document (manufacturer page or release, agency page, IAC paper, NTRS).
  - Values seen only in Wikipedia, trade press, blogs or aggregators are `SECONDARY_CLAIM`.
  - Result: 207 key values, of which 60 are REPORTED and 147 are SECONDARY_CLAIM.
- **No schematics were viewed,** so `schematics.json` is empty.
- **Raw log:** `_research_log.txt` holds the per-search notes, numbered 1 to 30. Searches 31 to 37 are reflected only in the JSON files.

## Counts
- 95 engine records; 84 of them have at least one key value.
- 139 sources: tier A 25, B 16, D 80, E 18. 4 sources are deliberately left unlinked (see below).
- 21 conflicts.

## ID conventions and merge flags
- **Round-1 IDs reused** wherever a round-1 placeholder existed: ENG-US-DRACO, -SUPERDRACO, -VR900, -VR3500, -SPECTRE, -AEON-*, -DELPHIN, -AETHER, -E2, -E-2, -NEWTONTHREE/FOUR, -HADLEY, -DRAPER, -RIPLEY, -ARROWAY, -ANDROMEDA, -ZENITH, -BROADSWORD, -MACHETE, -CYCLOPS, -XR-5K18, -XR-4A3, -5M15, -TR-106/107, -AR1, -AR22, -RS-25E, -BE-1/2, ENG-NZ-CURIE/HYPERCURIE.
  - The round-2 records should supersede those placeholders.
- **ENG-US-E2 (ABL) and ENG-US-E-2 (Launcher) are different engines** whose IDs differ only by a hyphen. This is risky for normalization. Consider renaming them ENG-US-ABL-E2 and ENG-US-LAUNCHER-E-2.
- **ENG-RU-S5-98M and ENG-US-AJ26-58/59/62** also exist in the ussr and anchor_ussr branches. Merge with them.
- **Prefix choice:** I used ENG-RU- for Soviet-era S5.60, S5.35, 11D426 and 11D428 (country field "SU") to match the ussr branch, which mixes ENG-RU- and ENG-SU-. The taxonomy branch should settle this.
- **Cycle mapping:** Broadsword's "dual-expander" is mapped to `expander_closed`, as round 1 did for BE-7. Open versus closed was not stated.

## Key findings (sourced)
- **Starliner (Aerojet Rocketdyne, 2016 releases, Tier A):**
  - Per shipset: 4 × 40,000 lbf launch abort engines (LAE), 24 × 1,500 lbf-class OMAC and 28 × 100 lbf-class RCS.
  - The LAE is a hypergolic (MMH/NTO) derivative of the LOX/ethanol RS-88 (Wikipedia). I created a separate ENG-US-RS-88 record as its parent.
  - The CFT 2024 thruster failures were Teflon poppet swelling in the oxidizer line and NTO two-phase flow from doghouse heating. This comes from secondary sources, including a relay of the February 2026 NASA Class A mishap report.
  - A Mercury-lander concept study gives OMAC 7000 N at 277 s and RCS 375 N at 286 s. Its counts conflict with Aerojet's (CF-R2-3).
- **SuperDraco:** SpaceX states 16,000 lbf, a regeneratively cooled 3D-printed Inconel chamber, restartable and deep-throttling.
  - The 235 s Isp in Wikipedia is disputed on its own talk page (CF-R2-1).
  - No primary Isp exists for Draco or SuperDraco.
- **CLPS landers:**
  - **VR900:** LOX/LCH4 and printed in-house (Intuitive Machines). Its thrust is unresolved: "900 lbf class" (Spaceflight Now), about 3,100 N (a database), or 4,900 lbf (Tier E) (CF-R2-5).
  - **Peregrine main engine:** Frontier Aerospace's Deep Space Engine (DSE), developed under NASA TALOS on MON-25/MMH. It is 150 lbf, five per lander. Trade press says "hydrazine" instead (CF-R2-6).
  - **Blue Ghost:** the main engine is a LEROS 4-ET (>1,000 N, MON/hydrazine). It also carries 8 Firefly-built hypergolic Spectre RCS thrusters, with no thrust published.
  - **ispace HAKUTO-R M1:** ArianeGroup supplied two independent propulsion systems: main (apogee engine plus biprop thrusters) and a hydrazine RCS. No engine designations or thrusts were found, so no record was created. The two ispace sources are left unlinked.
- **LEROS:**
  - Nammo page for the 1b: 635 N, 317 s, 12.965 MN·s total impulse, 19-year life. Juno flew a 640 N configuration on N2H4/MON-3.
  - Wikipedia table: 1c 460 N/325 s; 2b 407 N/318 s (MMH); 4 1100 N/323 s; 4-ET 1310 N.
  - Ownership chain: BAe → AMPAC → Moog (2012) → Nammo (2017). "Moog LEROS" is a 2012–2017 label.
- **Moog DST (manufacturer page, all REPORTED):**
  - DST-12: MMH/MON, 22 N, ε 300, MR 1.61, Isp ≥297 s, 0.64 kg.
  - DST-11H: N2H4/MON, ≥307 s, MR 0.85.
  - DST-13: 22/27.5 N.
  - All have Pt/Rh chambers.
- **TRW:**
  - TR-312: Ir/Re made by powder metallurgy, about 110 lbf, 325 s demonstrated on MMH/NTO, 330 s planned on N2H4.
  - TR-308: identity only.
  - TR-201: a Purdue table gives 9,900 lb and 303 s. It is a Delta stage engine, not an apogee engine.
- **Planetary:**
  - Cassini: two 445 N R-4D-class main engines, run in blowdown or He-pressurized mode (NASA).
  - Galileo: RPM with a 400 N main engine and 12 × 10 N thrusters, NTO/MMH. The main engine was first used at JOI, with more than 1 hour total firing (EADS).
  - Rosetta: 24 × 10 N biprop thrusters and no main engine. The thruster model was not named, so no record was created.
- **Green monopropellants:**
  - HPGP 1 N: roughly 204–235 s; first flew on PRISMA in 2010.
  - HPGP 5 N: 1–5.5 N, 239–253 s.
  - HPGP 22 N: 5.5–22 N, 243–255 s, 1.1 kg; NTRS 2021 qualification to about 150 kg throughput.
  - Aerojet GR-1 and GR-22: thrust class only. No Isp was found, and the GR-22 flight status on GPIM conflicts (CF-R2-9).
- **Japan:**
  - BT-4: 450 N vs 500 N; Cygnus main engine; originally for LUNAR-A.
  - HBT-5 (500 N class) replaced the R-4D on HTV from flight 3. MMH/MON-3.
  - Akatsuki OME: 500 N Si3N4 ceramic engine (JAXA). It failed at VOI in 2010 and gave only 10% thrust in 2011.
- **China:**
  - The Chang'e 7500 N engine throttles continuously from 1500 to 7500 N with a pintle injector. Isp is 308 s on Chang'e-3 and 310 s on Chang'e-4.
  - The brief's "490 N" lower limit is wrong; that figure belongs to the separate SISP 490 N apogee engine series.
  - SISP 490 N series: generation 1 (FY-25?) about 305 s, ε 154, Pc 0.68 MPa, NbHf10-1M chamber. Generation 2 (TQS492-2) 315 s. Generation 3 323 s, with a target above 325 s.
- **India:**
  - Chandrayaan-3 Vikram: 4 × 800 N throttleable engines plus 8 × 58 N, MMH/MON-3 (ISRO page, REPORTED). Chandrayaan-2 had a fifth central engine.
  - The 440 N LAM is on the propulsion module, not the lander.
- **Russia:**
  - S5.80 (KTDU-80 main engine): 2.95 kN, 302 s, ε 153.8, 30 starts / 890 s. Predecessor 11D426: 3.09 kN, 292 s.
  - DPO-B 11D428A then 11D428A-16: 500k ignitions, 2,000 s. DPO-M S5.142: 25 N, 285 s.
  - KTDU-35: S5.60 is the primary (4.09 kN, 278 s) and S5.35 the backup (4.03 kN, 270 s). The brief had these reversed.
  - S5.98M (14D30): 19.62 kN, 328.6 s.
- **Commercial highlights:**
  - **Relativity Aeon R:** high-pressure gas generator (Relativity 2023, REPORTED). 258 klbf in 2023, raised to 269 klbf in March 2025. The upper-stage Aeon Vac went from 279 to 323 klbf.
  - **Aeon 1:** 23 klbf SL, consistent with 207 klbf for 9 engines at the Terran 1 liftoff. Its cycle is disputed (GG vs open expander).
  - **Ursa Major (press):** Hadley 5 klbf ORSC LOX/RP-1 (has flown on Talon-A), Draper 4 klbf closed-cycle H2O2/kerosene, Ripley 50 klbf, Arroway 200 klbf LOX/CH4. Arroway's cycle is disputed.
  - **Launcher E-2:** about 22 klbf, LOX/RP-1, closed staged combustion, MR 2.62, 100 bar, 288/326 s (company claim via trade press).
  - **Stoke Zenith:** 100 klbf FFSC methalox, 7 per Nova. Andromeda is the LH2/LOX upper-stage system: 24 ring thrusters on the earlier concept, 12 dual-thrust chambers on Nova.
  - **Masten Broadsword:** 25 klbf SL, dual-expander, AFRL test 2019-12-10. Machete: 225 lbf on MXP-351. Cyclops-AL-3: 1,150 lbf. Scimitar: 1,200 lbf.
  - **XCOR:**
    - XR-5K18: 2,900 lbf, piston pumps. This is a rare `pump_fed_positive_displacement` engine.
    - XR-4A3: 400 lbf IPA/LOX.
    - XR-5M15: 7,500 lbf LOX/CH4 for ATK/NASA.
  - **Aerojet Rocketdyne:**
    - AR1: 500 klbf-class ORSC.
    - RS-25 restart: 521,000 lb at 111% (L3Harris 2022). The brief's 418,000 lbf is the RS-25D SL figure.
    - AR-22: 10 × 100 s firings in 240 h, completed 2018-07-06.
  - **Rocket Lab:**
    - Curie: 120 N, about 320 s. The propellant is disputed: bipropellant vs green monopropellant.
    - HyperCurie: electric-pump-fed hypergolic, 0.4 kN, 310 s, more than 3 km/s on CAPSTONE (Rocket Lab doc).
  - **Blue Origin BE-1 and BE-2** (Blue Origin page, REPORTED): BE-1 is 2,000 lbf on peroxide. BE-2 is 31,000 lbf on kerosene/peroxide. The brief's 2,200 lbf is not supported.
  - **Kistler K-1:** AJ26-58/59 on the first stage, plus the AJ26-60 (reworked NK-43) on the second stage, at 1,769 kN vac and 348 s at stage level.
  - **Roton:** rotating annular aerospike at 720 rpm with LOX cooling. It was dropped for a Fastrac derivative in June 1999. The brief's "96 chambers" was not found.
  - **TR-106:** 650 klbf LOX/LH2 pintle, ablative, Stennis 2000 test at 65% throttle. TR-107: 1.1 Mlbf LOX/RP-1, 17.7 MPa.
  - **Vector:** LP-2 upper-stage engine, LOX/propylene, 1,000 lbf vs 3.5 kN.
  - **Phantom:** buys Hadley and Ripley engines from Ursa Major and has no in-house engine, so no record was created.
  - **Agile:** A110, A2200 (500 lbf) and DS250 (250 N, for Nyx). The brief's "A3200" was not found.

## Brief claims corrected or not supported
- Chang'e "490 N" throttle lower limit: the actual lower limit is 1500 N.
- "S5.35 main engine": S5.35 is the backup.
- BE-1 "2,200 lbf": the source gives 2,000 lbf.
- RS-25E "418,000 lbf": that is the RS-25D SL figure.
- GR-22 "26.9 N" and GR-1 "231 s": not found.
- "Roton 96 chambers": not found.
- TR-308 Chandra use: not found.
- "Spectre = Frontier/MON-25": not supported.
- XR-5M15 ULA link: not found.

## Weak areas and open questions
- **No Tier A Isp exists** for Draco, SuperDraco, VR900, Spectre, HBT-5, GR-1/GR-22, Curie or most of the commercial engines.
- **Dream Chaser:**
  - VR35K-A (35 klbf LOX/LH2 with AFRL) and the VORTEX 1,500 lbf hypergolic engine were found.
  - The engines actually installed on Tenacity, and its RCS propellant (H2O2?), are NOT confirmed.
- **Not searched this round:**
  - MAVEN, Shenzhou propulsion-module engines (one search found none), and KTDU-417/425.
  - Mercury/X-15 HTP RCS, and the IHI 1700 N LAE (seen only as a mention).
  - Frontier M-Series 25 lbf (source captured but unlinked), Firefly Spectre thrust, Astra Rocket 4 engine identity ("Chiron" = Reaver?, Tier E only), and Vector's first-stage engine name.
- **Dates for Masten, Launcher and XCOR status:** the "cancelled" status on these records is inferred from company closures or acquisitions ([BG]) and is not sourced.

## Recommended next steps / anchors from this branch
1. **Moog DST-12 / DST-11H:** a clean manufacturer table with ε, MR, Isp and mass. A good monoprop/biprop RCS anchor.
2. **S5.80 / KTDU-80:** a full parameter set, though Tier D only. Confirm against a KB KhimMash or NIIMash document.
3. **Chandrayaan-3 800 N:** an ISRO Tier A page, and an example of a throttleable storable lander engine.
4. **SISP 490 N series:** three IAC papers give a generational Isp lineage.
5. **Starliner LAE ← RS-88:** a clear cross-propellant derivative lineage (LOX/ethanol → MMH/NTO).
- **Documents to open when fetch is available:**
  - NTRS 20170001286 (GR-1/GR-22 Isp).
  - Sci Sin Tech 2014 44(6):569 (Chang'e 7500 N).
  - IAC-11/12/18 SISP papers.
  - Nammo LEROS datasheets.
  - IM-1 press kit (VR900).
  - The Starliner NASA mishap report (Feb 2026).
  - L3Harris RS-25 brochure (vac vs SL).
