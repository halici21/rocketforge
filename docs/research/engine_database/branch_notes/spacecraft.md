# DB-0 branch "spacecraft" — notes

## Access conditions (read first)
- **This branch ran with no direct document access.** WebFetch failed with DNS errors (ENOTFOUND) for every domain I tried: ntrs.nasa.gov, l3harris.com, space-propulsion.com, en.wikipedia.org and esa.int. Bash `curl` also failed: the egress proxy refused the connection with a 403.
- **The shared WebSearch budget ran out after 13 searches.** The limit is 200 searches per turn, and parallel branches used up the rest. The sweep therefore stopped at about a third of the scope.
- **Every value comes from a WebSearch result summary.** The search tool's model wrote each summary from search snippets; no source document itself was opened. Every such source has `access: "search_result_only"`, and every key_value note carries the "seen only via WebSearch result summary" caveat.
- **"REPORTED" status means the summary attributed the number to that specific URL.** These values still need checking against the document itself. I used SECONDARY_CLAIM where the attribution was unclear or the source is Tier D/E.
- **No schematics are recorded** (`schematics.json` is empty), because I viewed none. Sources likely to contain flow schematics are listed under "Next steps".

## Counts
- 39 engine variant records, 56 sources and 9 conflicts. The target was 80+ records; this sweep did not reach it.

## Family lineage findings
- **AJ10 (spacecraft branch).** AJ10-137 (Apollo SPS) → AJ10-190 (Shuttle OMS) → the refurbished OMS-E flown on the Orion ESM for Artemis I and II.
  - The Artemis I OMS-E flew 19 Shuttle missions, STS-41G to STS-112 (NTRS 20240003648).
  - An ESA blog says the engine last flew in 2011 on Atlantis. That conflicts with the NASA paper (CF-6). The blog may be describing the Artemis II engine, which ESA says came from Atlantis and flew six times between 2000 and 2002.
  - AJ10-118K/Delta and the other upper-stage AJ10s belong to the upper-stage branch.
- **R-4D.**
  - R-4D (Apollo, 100 lbf) → R-4D-11 (490 N / 110 lbf; area-ratio 164 and 300 versions) → R-4D-15 HiPAT (Ir/Re chamber, 322 s nominal) → R-4D-15DM (dual-mode NTO/N2H4, 328 s, 100 lbf) → AMBR (333–333.5 s, development).
  - The Orion ESM auxiliary engines are "modified R-4D-11 produced specifically for Orion" (NASA). I kept them as a separate stage_specific record.
  - The 100 lbf versus 110 lbf/490 N thrust conflict comes from mixing variants (CF-2, resolved).
- **R-40.** The R-40A Shuttle Primary RCS (870 lbf, Pc 152 psia, Isp 280 s, ε 22, columbium) comes from a Marquardt NTRS table. The lineage to the commercial R-40B (about 4,000 N) is inferred from the designation only.
- **MR-80.**
  - Viking MR-80 had 18 nozzles and throttled 10:1, from 276 to 2,667 N.
  - MR-80B (MSL and Mars 2020) has a single nozzle, throttles more than 100:1, and is rated 800 lbf.
  - The brief's "3,100 N" figure is not supported by anything I saw: 800 lbf is about 3,560 N.
- **MR-107.** The family dates from the early 1990s (Peace Courage program).
  - Variants T, V, S and U are on the L3Harris sheets.
  - MR-107N flew on Phoenix. Sources disagree on how many: 12 versus 8 (CF-9).
  - MR-107U is the 68 lbf thruster on the MSL descent stage.
- **ArianeGroup.**
  - S400-12 (318 s) and S400-15 (321 s, larger nozzle).
  - 10 N thruster: Pt/Rh chamber, 292 s. Catalogue sub-variants S10-18 and S10-26 are unresolved.
  - The 200 N thruster was developed for ATV; a 220 N version is on the Orion ESM RCS (24 units).
  - A 22 N thruster is in ESA GSTP development.
- **Gemini.** The OAMS used 100, 85 and 25 lbf thrusters, and the separate re-entry RCS used 25 lbf units, all Rocketdyne with MMH/N2O4.
  - The SE-6 designation for the RCS thruster comes only from a Tier E auction listing.
  - "SE-7" for the 100 lbf OAMS unit is unverified and recorded only as an alias with that caveat.
  - Ablative chambers are commonly claimed but were not confirmed.

## Feed / pressurization boundary (key theme)
- **Pressurization belongs to the spacecraft propulsion system, not the engine,** in every case seen here.
  - The LM Descent Propulsion System used supercritical cryogenic helium pressurization (AER-DPS abstract).
  - The Orion CM RCS is helium-pressurized hydrazine with full redundancy (NTRS 20140006053).
  - The feed field on engine records is therefore a vehicle-installation attribute. It is INFERRED unless a note says otherwise.
- **Monoprop records default to `pressure_fed_blowdown`.** That is the typical satellite installation, not a property of the thruster, and is marked INFERRED. MR-80B and MR-104G are set to regulated because their landers and capsules are known to be regulated systems; even that is INFERRED, apart from Orion's helium system.
- **Dual-mode systems:** in the R-4D-15DM, hydrazine fuel is shared with the monoprop thrusters. This is an architecture choice at the system level.

## Cooling and injector claims not confirmed this session
- **Cooling:**
  - SPS: ablative chamber with radiation-cooled extension.
  - LMDE and LM ascent engine: ablative.
  - Apollo R-4D: molybdenum, radiation cooled.
  - OMS: fuel-regenerative.
  - These are widely stated but none was seen in a source this session, so they are notes only.
- **Confirmed by summaries:** columbium construction on the Shuttle PRCS (NTRS table), the Ir/Re chamber on HiPAT and AMBR, and Pt/Rh on the ArianeGroup 10 N thruster.
- **LMDE pintle:** the pintle and its credit to TRW (Staudhammer) come from a secondary source only.

## Alias problems
- **LM ascent engine:** "Bell 8258" (Bell model), a Rocketdyne replacement injector, and "RS-18" (Rocketdyne's later LOX/methane test conversion) are three different things. RS-18 should become a separate test_article record.
- **LMDE "TR-200":** a common alias, not seen in a Tier A source.
- **R-42 versus R-42DM:** the search engine conflated R-42DM with R-4D-15DM. R-42DM was not confirmed, so I recorded no R-42DM.
- **"Primary RCS" figure:** the NTRS OCR text reads 970 lbf while the table reads 870 lbf.

## Weak-source areas, and scope not swept (budget exhausted)
**Not researched at all (no records created; no source checked):**
- **US commercial and crew vehicles:**
  - Starliner: OMAC (1,500 lbf), RCS (100 lbf) and launch abort engines (4 × ~40 klbf).
  - SpaceX Draco and SuperDraco.
  - Cygnus BT-4 and the Cygnus RCS.
  - Dream Chaser VORTEX.
- **CLPS landers:**
  - Intuitive Machines VR900 (LOX/LCH4).
  - Astrobotic Peregrine (Frontier Aerospace thrusters).
  - ispace Hakuto-R.
  - Firefly Blue Ghost (Spectre).
- **Northrop Grumman / TRW:** TR-308, TR-312 and TR-201.
- **Moog / Nammo / AMPAC:** LEROS 1b, 1c, 2b and 4; Moog DST-11H and DST-12.
- **Planetary missions:** Juno, MAVEN, Cassini main engine (445 N), Galileo (MBB 400 N) and Rosetta.
- **Green propellants:** ECAPS HPGP (LMP-103S) at 1, 5 and 22 N; Aerojet GR-1 and GR-22 (AF-M315E/ASCENT, GPIM).
- **HTP:** Mercury and X-15 RCS, and the Soyuz descent-module thrusters.
- **Japan:** IHI BT-4, HTV thrusters and the Akatsuki ceramic OME.
- **China:** Chang'e 7,500 N variable-thrust engine, Shenzhou/Tiangong engines and the 490 N engine.
- **India:** 440 N LAM, 22 N thruster, and the Chandrayaan-2/3 800 N throttleable engine.
- **Russia/USSR:** KTDU-35, KTDU-80 (S5.80, DPO-B 11D428A, DPO-M), KTDU-417, KTDU-425 and the Luna/Mars/Zond engines. S5.92/Fregat is cross-reference only.

**Tier A documents identified but not read** (fetch them when access is available):
- TN D-7375 (SPS, NTRS 19730023031).
- AER Descent Propulsion System (NTRS 19730011150) and AER Ascent Propulsion System (NTRS 19730010173).
- TN D-7151 (CSM RCS).
- NTRS 19690029231 (Marquardt R-4D improvement report).
- NTRS 19910018886 (Shuttle RCS table).
- NTRS 20240003648 and 20240005874 (Orion engines).
- The L3Harris biprop/monoprop sheets (2023, 2024, 2025).
- The ArianeGroup apogee and 10 N pages.

## Recommended anchor engines from this branch
1. **AJ10-190 / OMS-E.** A long-lived pressure-fed storable engine with clear lineage and Tier A Artemis papers.
2. **R-4D family.** The richest variant lineage (R-4D → -11 → -15 → -15DM → AMBR) with manufacturer sheets. A good test of family versus variant handling.
3. **LMDE.** The canonical deep-throttling pintle engine with Tier A AERs, and a good test of the feed boundary with its supercritical helium system.
4. **MR-80 → MR-80B.** A monoprop throttling lineage with a documented architecture change (18 nozzles → 1; 10:1 → 100:1).
5. **R-40A.** A clean NTRS table with Pc, Isp, ε and mass.

## Next steps
- Rerun with WebFetch access, or once the search budget resets.
- For schematics, pull the AER PDFs. They normally include subsystem flow schematics, but I did not verify that here.
