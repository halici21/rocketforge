# r2_ussr: round-2 notes (USSR/Russia/Ukraine deep anchors + identity gaps)

## Method and limits
- WebFetch/curl blocked (per ROUND2.md, not retried). **33 of 38 WebSearch calls used.** Every source is `search_result_only`
  (Arianespace Soyuz manual: `not_retrieved`). See `raw_log.md` for what each search returned.
- A value is REPORTED only when the summary tied it to a named Tier A/B document. These are NTRS 19910018906, the Aerojet/NAS deck
  deps_068011, the JAXA 61856043 summary of an AIAA paper, Yuzhnoye official RD-861K data, the Starsem sheet, the Vestnik SSAU 2014 paper
  and the NASA Orb-3 IRT. Everything else is SECONDARY_CLAIM.
- The search engine's summarizer often offered numbers from its "own knowledge" (e.g. RD-0120 ~21-22 MPa, NK-33 ~146 atm). **None were recorded.**
  One summarizer statement was wrong: "RD-107 uses a GG on main propellants, H2O2 only for verniers". It was contradicted by the next search and not recorded.
- ID convention: the round-1 `ussr` branch uses ENG-SU-* for RD-170, NK-33, RD-0120, RD-107A, RD-108A and RD-270. The round-1 `anchor_ussr` branch used ENG-RU-* for the same engines.
  engines.json here uses the `ussr` ids. Anchor files keep the `anchor_ussr` file ids so the merge overrides them, and each anchor carries an `equivalent_ids` list. **The merge must unify these.**
- engines.json holds only new or updated records (55: 16 new, 39 updated from round 1, with round-1 key_values carried). Each record has `r2_record`.

## Part 1: anchors
- **RD-170: preburner count resolved to 2.** NASA NTRS 19910018906 is a set of Energia booster engine slides from the 1989 Paris Air Show displays.
  It says "1 turbopump assembly driven by 2 preburners which feed 4 thrust chamber assemblies". The same slides give the shaft order (fuel pump bottom, LOX pump middle,
  turbine top), regeneratively cooled (fuel) chambers, 740/806 t, 308/336 s, 250 kgf/cm2 and MR 2.58. Wiki's "single turbine" is consistent with this.
  Caveat: only the search summary was seen. **The boost-pump drive is still unresolved.** Three searches found nothing, and the "hydraulic turbine on kerosene /
  gas turbine on ox-rich gas" idea stays a [BG] verification target. Patent RU2544684C1 shows a booster turbine fed by turbine exhaust, but it is generic and not attached to any engine.
- **RD-171M**: no new data. The anchor is rebuilt from the round-1 Glavkosmos (Tier A) and IAC-13 (Tier B) values. It now separates the "max Pc reached in production" value kind from the rated Pc.
- **NK-33 / AJ26-62**: Tier B Aerojet deck: 2,109 psi main chamber Pc, 338/377 klbf, 297/331 s, chamber MR 2.6. NASA Orb-3 IRT (Tier A): the explosion was in the LOX turbopump of AJ26 engine E15.
  The candidate causes are the Hydraulic Balance Assembly and the turbine-end bearing. The IRT gives no AJ26-62-specific performance. The index conflict (14D15 vs 11D111) is still open.
- **RD-0120**: JAXA document (Tier B, summarizing CADB data from an AIAA paper): Pc 210 kgf/cm2 at 100%, MR 6. **Preburner 398 kgf/cm2 at MR 0.8 (fuel-rich).**
  Thrust is 190 t at 100% and 200 t at 106%. Wiki's 21.9 MPa conflicts with this (CF-R2-6). A KBKhA-author PDF (Ivanov & Dmitrenko) gives pump inlet pressures of 2-3 MPa for cavitation-free operation.
- **RD-107A / RD-108A**: the H2O2 steam drive and solid catalyst F-30-P-G are Wiki only. Wiki describes a "nitrogen gas generator for tank pressurization" on the TPA; the "LN2 evaporator" wording was **not** found.
  Other Wiki details: a gravity-fed "intermediate thrust" start stage, and two small pumps feeding H2O2. The Arianespace Soyuz User's Manual 2012 URL was found, but its tables were not seen. It is the top Tier A target.
- **RD-270**: Tier D only. FFSC with 2 preburners and 2 turbines (fuel-rich drives the fuel pump, ox-rich drives the ox pump). MR 2.67 can vary by about 7%. The end date is disputed: 1968 vs 1970.
- **RD-0124**: 4 chambers and 1 multi-stage TP with an ox-rich preburner, kerosene regen. Wiki gives a nominal 15.7 MPa / 359 s and a reduced-Pc mode of 9.5 MPa / 347 s. **Gimbal semantics conflict** (CF-R2-7).
  Round-1's "2327x1470 mm contamination" turns out to be an RSW design-intent sentence comparing the engine to RD-0110. It is still not a measured value.
- **A-4**: 18 pots of about 1.5 t each feed a common chamber. Thiel's design was frozen on 15 Sep 1941. Alcohol cools the double wall, entering at the lower end, and film cooling is used. The steam generator burns H2O2 plus Z-Stoff
  (NASM: 27% sodium permanganate solution). The turbine gives 580 hp at about 3,800 rpm, with flows of 128 lb/s alcohol and 159 lb/s LOX (NMUSAF).
  Production Pc was not found. The only Pc found is 15 bar for the 1.5 t development motor, and it is labelled as such.

## Part 2: identity gaps closed (Tier D unless noted)
- RD-214 = 8D59 (AK-27I/TM-185, 4 chambers, refractory vanes). RD-215 = 8D513 is the unit engine. **RD-216 is 2 x RD-215 (8D514)**, and round-1's 11D614 alias was dropped.
  RD-217 = 8D515. RD-218 = 8D712 = 3 x RD-217. RD-219 = 8D713 (R-16 stage 2, no data).
- RD-250 = 8D518 (2-chamber unit). RD-251 = 8D723 = 3 x RD-250 (6 chambers). RD-252 = 8D724 is the vacuum version. RD-261 = 11D69 = 3 x RD-250PM. RD-262 = 11D26.
- RD-263 = 15D117 (unit). **RD-264 = 15D119** (module); round-1 had given it 15D117. RD-268 = 15D168. RD-0228 is R-36M stage 2. RD-0229 has not been characterised.
- UR-100N/Rokot: RD-0232 unit = 3 x RD-0233 (15D95) + 1 x RD-0234 (15D96, which adds a pressurant heat exchanger). RD-0235 = 15D113 is the stage-2 main engine.
  RD-0236 = 15D114 is a 4-nozzle GG vernier. RD-0237 was not found.
- Isayev: S5.92 (2 modes, 19.61/13.73 kN). **17D61 is NOT S5.92**: it is the Ikar module with S5.144, so round-1's alias was dropped. S5.98M = 14D30.
  KTDU-35 = 11D62 is a *system* of S5.60 (SKD) + S5.35 (DKD). The R-27 4D10 is one ox-rich SC main chamber plus 2 GG steering chambers in one engine, mounted in the fuel tank.
  The R-29 engine designation was not found; "4D75" is unverified. The RD-0243 module (RSM-54) is RD-0244 main + RD-0245 vernier, also mounted in the tank.
  No data was found for S2.253.
- OKB-1: S1.5400 = 11D33 and S1.5400A1 = 11D33M (63.74 to 66.69 kN). 11D58M figures from different sources conflict (79.46 vs 83.4 kN).
  The 11D58MF Tier B paper gives "oxidizer gas generator 170 kgf/cm2".
- RD-56 = 11D56 is the KVD-1 precursor (ESA image, Tier A), with a fuel-rich closed cycle. KVD-1 data is from Wiki. RD-57 (Lyulka-Saturn 1966-1974) is likely 11D57, which is INFERRED.
- Yuzhnoye: RD-8 (4 chambers, ±33° single-plane). **RD-861K Tier A**: 7916 kgf, 330 s, MR 2.41, 207 kg. RD-864 (Dnepr). RD-843 is pressure-fed with 8 starts (Tier A brochure, no thrust given).
  RD-870 is closed-cycle LOX/kerosene. Nothing was found for RD-868P.

## Schema breakers (new evidence)
- The hot-gas path merges 2→1 and then splits 1→4 (RD-170): preburner, turbine and chamber counts are all different.
- Russian "газогенератор" is used for closed-cycle preburners (11D58MF). Never map ГГ to `gas_generator` cycle automatically.
- One engine can have mixed cycles, such as a staged-combustion main chamber with GG-cycle steering chambers (4D10, RD-0243/0244/0245).
- Records can sit at different levels: unit engine, multi-engine propulsion unit (RD-216, 218, 251, 261, 264, 0232, 0243) and multi-engine system (KTDU-35). They need an explicit `assembly_of` relation.
- Gimbal can be engine-level 2-plane or per-chamber single-axis (RD-0124, RD-8 ±33°, RD-0236).
- Value kinds differ: rated, "max reached in production", design margin, and development-motor values (A-4 15 bar).
- A preburner can have its own operating point (RD-0120: 398 kgf/cm2, MR 0.8).
- Stage-serving hardware can be part of the engine: an N2 pressurization generator (RD-107/108), a pressurant heat exchanger (RD-0234 vs RD-0233, the only difference between them) and GH2 pressurization (RD-0120).
- A field failure can be attributed to a sub-component of a serial-numbered engine (Orb-3 E15 LOX TP HBA).

## Highest-value fetch targets (when fetch works)
NTRS 19910018906; Soyuz User's Manual 2012 (edX copy); JAXA 61856043; deps_068011; Yuzhnoye LIQUID-PROPELLANTROCKET-ENGINES-1.pdf; Vestnik SSAU 2587; NPOEM_RD0120_up.pdf;
Orb-3 IRT exec summary; yuzhmash.com RD-8/RD-261/RD-861K pages; Starsem ST07/ST08.
