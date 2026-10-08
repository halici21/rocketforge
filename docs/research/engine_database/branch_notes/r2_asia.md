# r2_asia — Round 2 notes (anchors EU/Asia + Asia/Europe identity gaps)

## Conditions
- I used exactly 38 WebSearch calls: 20 for anchors and 18 for identity gaps. WebFetch and curl were not used (blocked by policy).
- Every source has `access: search_result_only`. A value is marked `REPORTED` only when the search summary tied it to a named Tier A or B document. Everything else is `SECONDARY_CLAIM`.
- The model that wrote the summaries sometimes merged several result pages. When I could not tell which page a value came from, the source note says "attribution uncertain".
- Round-1 values are carried forward with their round-1 source IDs. Round-1 Tier D values that were marked REPORTED are downgraded to SECONDARY_CLAIM in the anchors. The AIAA Vehicle Guide is rated D here; asia_other had rated it B.
- Build scripts are in `../../r2_asia_build/` (srcs.py, anchors.py, build.py). They are not part of the deliverable.

## Counts
- 75 engine records: 17 anchor or anchor-adjacent records, plus Part 2 records that upgrade round-1 stubs or are new.
- 176 sources. 5 Vulcain sources are carried from round 1.
- 34 conflicts.
- 4 schematic entries. None was viewed; they are text descriptions or leads.
- 12 anchor files with 231 assertions.
- 226 key_values in engines.json: 41 REPORTED and 185 SECONDARY_CLAIM.

## ID / merge issues (action for merger)
- **Vulcain 2 and Viking 5C:** the anchor files use `ENG-EU-VULCAIN-2` and `ENG-EU-VIKING-5C`, following the round-1 anchor_eu_asia convention. The europe branch uses `ENG-FR-VULCAIN-2` and `ENG-FR-VIKING-5C`. Each pair is the same engine. Pick one convention; FR fits ISO-2.
- **`ENG-CN-CANGQIONG` duplicates `ENG-CN-WELKIN`.** Galactic Energy uses 苍穹-50 / CQ-50 / Welkin for one engine. The round-1 hint of a "15 tf Cangqiong second-stage engine" is not supported. Merge the two.
- **`ENG-CN-THUNDER-R2`:** no evidence it exists. The real successor is 雷霆-RS (`ENG-CN-THUNDER-RS`, new). Candidate for deletion.
- **`ENG-CN-LEIYU-THUNDER-R1`:** the correct pinyin is Leiting (雷霆). I kept the ID so the merge still matches.
- **`ENG-AR-TRONADOR-II-ENGINES`:** split into `ENG-AR-RS-2` (30 tf LOX/RP-1 first-stage engine, named in an Argentine government release) and `ENG-AR-MT-B`, plus the `ENG-AR-VEX-1A-ENGINE` test article. Keep the old ID only as a pointer.
- **`ENG-KP-HWASONG-14-15-MAIN-ENGINE-PAEKTUSAN`:** split into two new records:
  - `ENG-KP-HWASONG-14-MAIN-ENGINE`: single chamber, per CSIS.
  - `ENG-KP-HWASONG-15-FIRST-STAGE-ENGINE`: two combustors on a common turbopump, per Brügge as quoted.
- **`ENG-IR-SIMORGH-FIRST-STAGE-ENGINE-CLUSTER`** describes a stage cluster, not an engine. It should become an installation of `ENG-IR-SHAHAB-3-ENGINE`.
- **`ENG-IN-SCE-200`:** I kept the ID, but the current designation is SE-2000 (renamed).
- **Interstellar records:** I kept the long round-1 IDs. Suggest renaming to `ENG-JP-COSMOS` and `ENG-JP-MOMO`.
- **`ENG-RU-RD-151-NARO-1-FIRST-STAGE`:** I kept the ID. Its round-1 family "RD-191" is now "RD-170/RD-191 lineage". See the RD-151 vs RD-191 conflict.

## Anchor findings
- **LE-7A.** The best new source is MEXT-hosted 1997 Space Activities Commission material, Tier A from NASDA. It has an LE-7A vs LE-7 comparison table:

  | Parameter | LE-7A | LE-7 |
  |---|---|---|
  | Mixture ratio | 5.9 | 6.0 |
  | LH2 turbopump speed | 41,200 rpm | 42,200 rpm |
  | LOX turbopump speed | 18,050 rpm | 18,100 rpm |
  | Preburner gas temperature | 740 K | 840 K |
  | Isp | 441 s | — |
  | Throttle | possible, but no mixture-ratio control | — |

  - The LE-7 column agrees with Wikipedia's LE-7 block (42,200 / 18,100 rpm), so the LE-7 values have two independent sources.
  - The OCR is garbled. The thrust unit reads "1.10 Ionf" and was not converted.
  - I am not sure which of the three 1997 PDFs holds the table.
  - No Tier A chamber pressure for LE-7A was found.
- **LE-9.**
  - IHI Technical Review Vol.57 No.3 (2017), "LE-9 turbopump development" (Tier A, copyrighted) says "nominal speed 41,600 rpm". The garbled text does not show which pump.
  - A Tier E site says it is the LH2 turbopump.
  - Also from IHI: MHI owns the system and IHI the turbopumps; thrust is about 1,500 kN, roughly 1.4 times LE-7A.
  - The IAC-17 abstract gives electric valves, a HIP-brazed main combustion chamber and open impellers.
- **LE-5B and LE-5B-2.**
  - The Weblio (ja.wikipedia) table gives LE-5B: 137.2 kN, 3.58 MPa, MR 5, ε 110, 447 s, LH2 turbopump 52,000 min⁻¹, LOX turbopump 18,000 min⁻¹, 285 kg, 2.79 m. It also gives discrete throttling at 60%, 30% and 3%, with no turbine drive in the 3% tank-head mode.
  - For LE-5B-2: a GH2/LH2 mixer in the fuel line, laminarizing plates in the expander manifold, and a 306-element injector. The IAC-08 MHI abstract confirms it was a vibration fix.
- **Vikas.**
  - Chamber pressure rose over time: 52.5 bar, then 58.5 bar (2001), then 62 bar (high-thrust version, qualified 2018).
  - Reported thrust ranges from 725 to 850 kN, with SL/vacuum and variant almost never stated.
  - ISRO's own page confirms only the human-rated L110-G 240 s test (6 Apr 2023).
  - No result confirmed water injection or coaxial pumps.
- **CE-7.5.**
  - Fuel-rich staged combustion, two gimballed steering engines, and separate thrust and mixture-ratio regulators.
  - Chamber pressure is given as both 5.8 MPa and 7.5 MPa without labels.
  - Preburner and turbopump data were not found.
- **CE-20.**
  - The gas generator is fed from the pump outlets.
  - Independent LH2 and LOX turbopumps run "in series mode", i.e. series turbines.
  - Thrust is quoted at several qualified set-points: 186 kN, 200 kN, and 19 / 20 / 22 t.
- **YF-77.**
  - The IAC-13 abstract (Tier B) gives 700 kN, O/F 5.5, gas-generator cycle, about 9× YF-75's thrust and about 2.7× its pressure. Development problems were fuel turbopump rotor cracking and combustion instability.
  - Chinese-language searches found no turbopump speeds.
- **YF-100.**
  - Chinese sources say all the oxidizer goes through the ox-rich preburner.
  - A kerosene tap drives the fuel pre-pump (booster). This is a hydraulic drive edge in the topology.
  - Throttle range conflicts: 65–100% vs 65–105%.
  - Two sources give 18 MPa, but both are Tier D/E.
- **KRE-075.**
  - The 2009 KARI design paper (Tier B) gives 60 bar, 74.8 t and 306.9 s as design targets. Wikipedia gives 7.0 MPa, which conflicts.
  - Turbine: impulse type, 12 nozzles, single rotor (2016 KARI paper).
  - The gas generator takes about 4% of propellant flow. Its exhaust passes a heat exchanger and then an exhaust duct that produces about 1% of thrust (Korean summary; host page uncertain).
  - The EUCASS-2019 paper says three control valves set the operating point in ground tests.
  - Stage-2 altitude version split into `ENG-KR-KRE-075-2ND-STAGE`.
- **Viking 5C.**
  - Chamber pressure 58.5 bar (fr.wiki) vs 5.5 MPa (family-level).
  - Gas-generator cycle with "3 coaxial pumps". The third pump's fluid is unknown.
  - Water in the gas generator was searched for explicitly and is NOT_REPORTED. [BG] Viking and Vikas use a water circuit for gas-generator gas cooling. This is a verification target, not recorded data.
- **Vulcain 2.**
  - A press-release reprint gives the "new oxygen turbopump" as 13,000 rpm delivering 161 bar. This is Vulcain 2-specific, unlike the 13,600 / 34,000 rpm values, which are probably Vulcain 1 and are still unattached.
  - The ESA V157 inquiry (Tier A): a leak in the nozzle cooling circuit and fissured tubes. The Vulcain 1 and 2 nozzles differ in tube shape and stiffeners.
  - The 2003 fix: reinforced nozzle extension, more H2 coolant flow and a thermal barrier coating.
  - Wikipedia describes the lower nozzle as film-cooled by re-injected turbine exhaust.
  - Volvo's Vulcain 2+ dump-cooled nozzle-extension demonstrator was test hardware only and is not flight configuration.

## Schema breakers seen across anchors
1. Operating points that change feed mode: LE-5B's tank-head idle with no turbine drive.
2. The same designation with several epochs or configurations:
   - LE-7A short vs long nozzle and 1997 design vs flight values.
   - Vikas chamber-pressure eras and fuel change.
   - CE-20 thrust set-points.
   - KRE-075 stage-1 vs stage-2 versions.
   - Vulcain 2 nozzle before vs after 2003.
3. Flow-fraction and tap-point attributes: 100% of LOX through the YF-100 preburner; CE-20 gas generator fed from pump outlets; KRE-075 gas generator at about 4%.
4. Non-standard drive edges: YF-100's hydraulic kerosene drive of the booster pump; SEPR 841's turbojet shaft-driven pump through a clutch.
5. Turbine-exhaust destinations with a duty: Vulcain 2 film cooling of the lower nozzle; KRE-075 heat exchanger, then a thrust-producing duct.
6. Values without a component identity: an LE-9 pump speed whose pump is unknown; a third Viking pump of unknown fluid.
7. Auxiliary thrust chambers delivered with an engine: the CE-7.5 steering engines.
8. Chamber vs engine counting: Hwasong-15 has two combustors on one turbopump but is counted as "1 engine".

## Part 2 highlights
- **India**
  - SE-2000 (ISRO, Tier A): 180 bar, feed pressures up to 600 bar, 335 s. Thrust (2,030 kN vacuum / 1,820 kN SL) is Wikipedia only.
  - PS4 L-2-5: MMH/MON-3 confirmed by ISRO. Each engine is about 7.33 kN; two per stage.
  - 440 N LAM (IAC-16): MR 1.6, ε 160, about 315 s, flown on 34 spacecraft.
  - Agnilet: electric pumps confirmed for 2025 tests. Whether the 2024 flight engine used them is not stated.
  - Raman: hypergolic upper-stage and roll-control engines, not cryogenic.
- **Korea**
  - KSR-III: pressure-fed with regulator and venturi (KSME paper).
  - KRE-007: 68.7 kN, 325 s, shut down early after 475 s in 2021.
  - Naro-1 first-stage engine: RD-151 vs RD-191 conflict.
- **Iran / North Korea**
  - All Tier D analyst sources; identities stay low-confidence.
  - Nodong lineage is disputed: Isayev S-2.713M (FAS) vs Scud scale-up (ACW).
- **Brazil:** L75 is a LOX/ethanol open gas-generator engine, 75 ± 5 kN (JATM, Tier B). L5 first fired in 2005. L15 is named only.
- **Japan minor**
  - LE-3: 12,000 lbf, 285 s, 250 s. The "AJ10 licence" hint is not supported.
  - LE-8: LOX/LNG for GX (not J-I), ablative, 11 tests.
  - MB-60: Boeing/MHI open expander, 60,000 lbf. Alias collision with RL60.
  - COSMOS: about 130 kN, gas generator, pintle injector, biomethane.
  - MOMO: 12 kN, pressure-fed, ethanol/LOX.
- **China commercial**
  - Welkin/CQ-50 manufacturer data (Tier A): 50 t SL, 4:1 throttle, open cycle, pintle injector, coaxial dual-suction turbopump.
  - Thunder-RS: 1,297.5 kN measured.
  - Longyun: 676 / 704 kN; cycle not stated.
  - Fengyun: 140 t full-flow staged combustion.
- **Europe**
  - Aquila SL 75 kN and VAC 94 kN (LOX/propane, gas generator).
  - Helix: 100 kN, ORSC since 2020, early turbopumps from Pivdenmash.
  - TEPREL-B: pressure-fed, 30 kN.
  - TEPREL-C: gas generator, 190 kN. The vacuum version is 50 or 75 kN (conflict).
  - Skyrora 70 kN "Skyforce-2". The name comes from the summary; check the spelling.
  - LM10-MIRA: 7.5 t expander demonstrator, Voronezh 2014.
  - SEPR 841: turbojet-shaft-driven turbopump, 93 bhp at 5,070 rpm.
  - OTRAG CRPU: 26.96 kN, N2O4 per Wikipedia. Pressure feed is supported only by a forum post.

## Not reached / gaps
- **Turbopump speeds not found** for LE-9 LOX, CE-7.5, CE-20, YF-77, YF-100, KRE-075, Vikas and Viking.
- **Gas-generator and preburner mixture ratios:** none found for any anchor.
- **Not researched (budget):** Egypt; the Vikas L40 strap-on as a separate variant; Isar and RFA chamber pressures; Orbex engine name; MOMO v1.
- **Tier A/B leads to fetch when network allows:**
  - IHI Technical Review 57(3).
  - MEXT 1997 PDFs (3).
  - JAXA 2010 LNG report.
  - EUCASS2019-0521.
  - KARI koreascience PDFs (2009, 2016).
  - JATM L75 paper (open access).
  - ESA V157 inquiry page.
  - IAC-13-17679 and IAC-16-32550 full texts.
  - ISRO SE-2000 release.
