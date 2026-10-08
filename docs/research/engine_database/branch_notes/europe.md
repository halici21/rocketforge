# DB-0 branch "europe": notes

## Access conditions (read first)
- **WebFetch could not reach any host** (`getaddrinfo ENOTFOUND` for wikipedia, esa.int, eoportal, iafastro and the rest), and the agent proxy refused direct `curl` with 403 for every host tried (ESA, NTRS, Astronautix, DLR elib, CNES, Ariane/Safran, Isar, RFA, PLD, Avio, AIAA, web.archive.org).
- **The only tool that worked was WebSearch.** It returns result URLs plus a summary of snippets written by a model. About 45 searches ran before the **shared 200-search budget for the turn ran out**, and every later search was refused.
- So **every source is marked `access: search_result_only`** and every value is marked `SECONDARY_CLAIM`, even when the source is Tier A or B (ESA, NTRS, IAC and EUCASS papers). Nothing was read in full. Treat each value as a pointer to check, not a verified figure.
- The searches that were refused covered: SEPR aircraft rockets, OTRAG, Isar Aquila, RFA Helix, PLD TEPREL, Orbex, Skyrora, MIRA, AVUM RD-843, Viking 5B, Themis, LM10, ILR-33, Nammo, Mirak/Repulsor. For these (14 records) I created **identity-only placeholder records** with empty `source_ids`, `confidence_identity: low/medium` and a `NOT_AUDITED` note. Their identity comes from the brief plus background knowledge. They have no key values.

## Counts
69 engine records (FR 26, DE 23, GB 15, IT 2, ES 2, UA 1), 96 sources, 29 conflicts, 5 schematic leads (none viewed). 43 records have key values (142 values in all).

## Lineage and alias findings
- **Viking → Vikas.** Vikas is India's licence-built derivative (ISRO–SEP agreement). It is a lineage link only, not the same engine, and no Indian record was created here. Viking variants recorded: 2, 2B, 4, 4B, 5 (DLR naming), 5B (placeholder), 5C, 6. Fuel went from UDMH to UH 25. GG cycle, with the GG burning the main propellants (IAF-81-362 abstract). **Water injection into the GG was NOT confirmed** by any source, including the French-language searches. MAN built the turbopumps. DLR's "Viking 5" (675/758 kN) may simply be loose naming for 5C.
- **HM4 → HM7 → HM7A/HM7B.** HM7 vs HM7A may be one engine: the Ariane 1 infobox calls it "HM7-A" (see CF-28). HM7B came from raising Pc from 30 to 35 bar and lengthening the nozzle (qualified 1983).
- **Vulcain.** The "HM60" alias was **not found** in any result and is kept with empty source_ids. Vulcain 2.1 = AM gas generator (GKN) plus a simplified nozzle; its thrust is in conflict (1371 / 1340 / ~1324 kN).
- **Vinci** is a closed expander. "Up to 3 restarts" (Wikipedia) and "4 ignitions" (Safran/ESA) are consistent. Early ESA text said 5.
- **Aestus (DE)** is pressure-fed MMH/N2O4. **Aestus II = RS-72**: Rocketdyne powerpack (turbopump plus **gas generator**) and an Astrium thrust chamber. Pathfinder tests at White Sands ended 3 May 2000. It never flew.
- **M10 → MR10** (renamed Sep 2024). It is a closed (full) expander running LOX/CH4, and a **derivative of the Russian RD-0146** via the KBKhA collaboration (ended 2014). This is a cross-branch link to the RU branch. The 362 s Isp is a *minimum requirement*.
- **RZ.1/RZ.2 ← Rocketdyne S-3/S-3D** (1955 R-R/Rocketdyne technical assistance agreement). This is a cross-branch link to the US branch. An uprated 150,000 lbf RZ.2 variant exists but its designation is unknown.
- **LRBA family: Véronique → Vexin → Coralie engines → Valois.**
  - Diamant A's Vexin B was **pressure-fed with no turbopump**. Tanks were pressurised by a **slow-burning solid-propellant gas generator quenched with water** (Rothmund IAC-09). This may be where the brief's "water injection" idea comes from: it belongs to Vexin pressurisation, not to Viking.
  - Rothmund calls Valois "the most powerful pressure-fed engine to have flown in space" and says it shares Coralie's propulsion system.
  - The Coralie engines' designation ("Vexin-A"?) is unverified. The stage used 4 separate LRBA engines.
- **Walter / HTP lineage into Britain.** JBIS 1990 (Andrews & Sunley) says the Walter ATO unit and the 109-509 most influenced British HTP engines (Sprite, Spectre, Gamma, Stentor). The Stentor cruise chamber was derived from Gamma.
- **A4 / V-2.** I used cycle `separate_turbine_working_fluid` (an H2O2/permanganate steam generator with overboard exhaust). The HWK 109-509 is the same, except its steam came from T-Stoff over a catalyst; the two sources disagree on which catalyst (CF-21). The **"Triebwerk 39 / 39a" naming was NOT confirmed** and the alias is kept with empty sources.

## Architecture surprises worth anchoring
1. Vexin B / Valois: large pressure-fed first stages, with tank pressurisation by a water-quenched solid gas generator.
2. A4: turbopump driven by a separate working fluid (H2O2 steam). It is the canonical example of a cycle that is not a combustion tap.
3. BMW 109-718: pumps probably driven from the jet engine shaft. This is background knowledge, unverified, so its cycle is left UNKNOWN.
4. Stentor: two chambers with different jobs (boost, then cruise).
5. Aestus II/RS-72: a binational engine (DE thrust chamber, US powerpack).

## Recommended anchor engines (when sources can be fetched)
- **Vulcain (1)**: NTRS 19910018907 (Tier B) gives thrust, Isp, Pc, mass and turbopump layout. Re-read the PDF and check its NTRS rights field.
- **Vinci**: several IAC papers (IAC-15/18/19/21) plus a Safran press release.
- **A4 engine**: NASM objects plus the enginehistory.org flow data (128+159 lb/s and 25 t gives a DERIVED ~195 s, consistent with ~203 s SL Isp).
- **Vexin B / Valois**: Rothmund IAC-09 and IAC-10 history papers (Tier B; they should have system diagrams).
- **Aestus**: Mechanics & Industry 2020 Table 1 (open access; licence to be confirmed) plus ESA EPS.
- **Gamma family**: the JBIS 1990 paper (Tier B, copyrighted).

## Weak areas and unresolved questions
- No Tier A datasheet was read in full. ArianeGroup/Safran datasheets are copyrighted and none was fetched.
- Variants not separated: Véronique engine per vehicle version; HWK 109-509 A-1/A-2/B/C; Isar Aquila SL vs vacuum; RFA Helix; Viking 5 vs 5B vs 5C.
- Not covered at all (search budget): SEPR 25/66/84/841/844 details, OTRAG CRPU, Skyrora engines, Orbex Prime engine name, Polish ILR-33 (hybrid, excluded anyway), Nammo (mostly hybrid or monoprop), ESA Themis (vehicle; uses Prometheus), Avio LM10/MIRA, DLR test engines, Bölkow/MBB 1960s experimental engines, ERNO.
- HyImpulse (hybrid), Rheintochter R1/R2 (solid), Taifun P (solid) and SABRE (air-breathing) were **excluded**.
- The Wasserfall thrust (~8 t per the brief) was not found.
- Some values came out of search summaries where the attribution to a specific page was unclear: RS-72 at 12,500 lbf, and Vulcain 2 at 1340 kN. These are flagged in the key_value notes.
- Dates in notes marked "background" (Ariane 5 retirement 2023, Vulcain 2 first flight 2002, Aestus first flight 1997, Spectrum first flight 2025) were not checked this session.
