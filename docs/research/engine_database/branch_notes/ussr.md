# Branch "ussr": Soviet / Russian / Ukrainian liquid engines, notes

## Session limits (read this first)
- **WebFetch failed on every domain** with `getaddrinfo ENOTFOUND`. That included wikipedia, npoenergomash, astronautix, russianspaceweb, ntrs and kiwix mirrors. Direct curl was also blocked (proxy CONNECT 403).
  As a result, **no page was opened directly.** Every value came from WebSearch result summaries, which quote the page text.
  Every key_value carries the note "seen in WebSearch result summary ... re-verify".
  Every source has `access: search_result_only`, except the not-consulted book, which is `not_retrieved`.
- **The WebSearch budget (200 per turn, shared across all branches) ran out after 20 searches on this branch.**
  The planned Russian-language sweep didn't run: Энергомаш/КБХА/Кузнецов/Южное official pages, 11Д58М, С5.92, Блок Л, РД-56, 11Д57, missile engines.
- Values: a figure that only Wikipedia, RSW or another Tier D/E source reports has status `SECONDARY_CLAIM`. Figures from the Glavkosmos export catalogue (Tier A) and from the Energomash IAC-13 paper (Tier B) are `REPORTED`.
- **Identity-only records are 72 of the 107 engines.** The model filled them in from memory. Each one's `notes` starts with "NOT_VERIFIED" and has no key_values.
  Aliases with empty `source_ids` are unverified recall. That includes many GRAU indices: 8D51, 8D52, 8D75, 8D716, 11D43, 8D412K, 11D111..114, 14D30, 17D61, 15D117 and others.

## Counts
107 engine records. 35 have values, 183 key_values in total. 59 sources, 19 conflicts. 0 schematics: none were viewed, and no schematic was cited in a retrieved summary.

## Alias resolution (core value): what was actually supported
- **RD-107 family:** RD-107 = 8D74 (Wiki). 8D74K appears only as a reference point.
  RD-107MM = 8D728 = 8D74M, and RD-108MM = 8D727 = 8D75M (Molniya-M, Soyuz 11A511).
  RD-117 = 11D511 and RD-118 = 11D512 (Soyuz-U/U2). RD-107A = 14D22 and RD-108A = 14D21 (from 2001).
  GlobalSecurity labels 11D511/11D512 with the generic names "RD-107/RD-108". The index mapping agrees; only the naming differs (CF-7).
- **RD-170 = 11D521 and RD-171 = 11D520.** This rests only on a reference title seen in a Russian search summary.
  RD-171M → RD-171MV (Soyuz-5, first flight 30 Apr 2026 per Wikipedia).
- **RD-191 family:** RD-191 (Angara) → RD-151 (Naro-1, 170 t, fired 30 Jul 2009) → RD-181 (Antares, export) → RD-193 (Soyuz-2.1v replacement for NK-33, no gimbal).
- **RD-0124 family:** RD-0124 = 14D23. RD-0124A (Angara URM-2) burns 424 s and weighs 548 kg.
  RD-0124MS (Soyuz-5) has 2 blocks of 2 chambers and 60 t. "RD-124MV" in Tier E press is very likely a garbling of RD-0124MS.
- **Proton family:** RD-0210 = 8D411K. RD-0212 = 8D49 is a propulsion system, made of RD-0213 = 8D48 plus the RD-0214 four-nozzle steering engine.
  All derive from RD-0205 (UR-200). RD-275 = 14D14 per one summary.
  **11D43 for RD-253 is NOT confirmed** (CF-19). **8D412K for RD-0211 is not confirmed.**
- **NK line:** the GRAU index of NK-33 is unresolved (CF-12). The summary gave 14D15. My recollection is NK-33 = 11D111 and NK-33A = 14D15.
  NK-21 = 11D59 (RSW Block G page). NK-31 replaced it from vehicle 5L.
  The AJ26 mapping conflicts: NK-43 is given as AJ26-59 on one page and AJ26-60 on another (CF-13). Sources also disagree on whether Antares flew AJ26-58 or AJ26-62.

## Cycle notes
- R-7 RD-107/108 and derivatives are coded `separate_turbine_working_fluid`. The H2O2 steam generator is well established in the literature, but the retrieved summaries said only "gas generator". cycle_status is therefore SECONDARY_CLAIM or INFERRED, and the H2O2 detail is flagged as not re-confirmed.
- Ox-rich staged combustion is supported (Tier D) for RD-170/171/180/191, RD-253/275/275M, RD-0124, RD-0210/0211, NK-9, NK-15 and NK-33.
- RD-0120 is fuel-rich staged combustion with a single shaft. RD-270 is full-flow staged combustion (Wiki).
- RD-0110 and RD-0105/0109 are gas-generator.
- Unverified: 11D33 and 11D58 ox-rich staged combustion, RD-56/KVD-1 fuel-rich staged combustion, and the S5.92 and RD-8 cycles.

## Multi-chamber engines
RD-170/171 (4), RD-180 (2), RD-107 (4 main + 2 verniers), RD-108 (4 + 4), RD-0110 (4 + steering nozzles), RD-0124 (4), RD-0124MS (2x2), RD-0214 (4 nozzles), RD-8 (4, unverified), RD-264 (4 × RD-263, unverified), RD-218 (6, unverified).

## Suspicious data caught
- A summary gave RD-0124 dimensions as 2327 x 1470 mm. Those are identical to the RD-0210 figures, so I treated them as contamination and did not record them.
- The NK-15 Wikipedia revisions carry two incompatible spec sets; version B copies NK-33 (CF-11).
- LLMpedia (an AI-generated encyclopedia) gives RD-171 SL thrust as 7900 kN and calls RD-253 gas-generator. I excluded it.
- The RD-170 summary offered a chamber pressure of about 24.5 MPa from the summarizer's "own knowledge". I did not record it.
- FAS says the R-2 used methyl alcohol (CF-10). This is flagged as doubtful.

## Excluded
RD-0410 nuclear thermal engine (KBKhA) is excluded per scope. Copies of Soviet engines made in other countries (e.g. Scud/Hwasong lineage) are left to other branches.

## Highest-value next fetches (once fetch/search is available)
1. Glavkosmos catalogue pages: trade.glavkosmos.com/rd-171-m/, /rd-181/ and /500/, /502/. These are Tier A tables with units as printed. Check for RD-191, RD-180, RD-0124 and 14D22 pages too.
2. ILS Proton Mission Planner's Guide Section A (Tier A) for RD-275M, RD-0210, RD-0212 and 11D58M on Block DM-03.
3. The 'Dvigatel' journal scans on epizodyspace: 1999/1 pp.30-31 (NK-33/43) and 2000/2 pp.14-15 (Proton second/third-stage engines).
4. IAC-13 C4.P.20083 and IAC-15 E4.2.27909 (Energomash).
5. The Hindley Glasgow table. Its content was not returned.
6. Official sites: npoenergomash.ru / engine.space, kbkha.ru, kbhmisaeva.ru, uecrus.com (Kuznetsov), yuzhnoye.com.
7. Sutton, *History of Liquid Propellant Rocket Engines*, Ch. 8, as the Tier C cross-check for all identity-only records.

## Recommended anchor engines
- **RD-171M:** Tier A Glavkosmos values plus a Tier B IAC paper, with full SL/vac, pc, mass, throttle and gimbal data.
- **RD-181:** Tier A Glavkosmos values. It is the export twin of RD-191.
- **RD-0120:** the richest Tier D set, a fuel-rich staged-combustion reference, and the comparison point to the SSME.
- **RD-253 / RD-275 / RD-275M:** a clean uprate series with consistent Wiki/RSW values. Good for uprate lineage modelling.
- **RD-107A / RD-108A:** the canonical multi-chamber plus vernier, H2O2-drive architecture.
