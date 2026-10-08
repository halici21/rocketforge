# us_hist branch notes: US liquid rocket engines, early history to about 2010

## Read this first: access limits on this branch

- **No document was opened.** Direct fetching (WebFetch and curl) to en.wikipedia.org, ntrs.nasa.gov,
  nasa.gov, astronautix.com, purdue.edu, apps.dtic.mil, archive.org, nationalacademies.org and others
  was refused by the session egress proxy (CONNECT 403 or DNS failure).
  All evidence comes from **WebSearch result excerpts and summaries**. Every source has
  `access: search_result_only` (or `not_retrieved`), and every key value says "value seen in
  search-result excerpt only".
- **The shared WebSearch budget ran out** after about 40 searches on this branch (200 per turn across
  all agents). Families that were planned but never searched: IPD, RS-84, TR-107, RS-83, COBRA, RS-18,
  J-2T, SSME block history, SP-8107 contents, F-1/J-2/H-1 manuals, Lance, Hustler, AJ10-138/-118F,
  RL10 sub-variants (A-3-1, A-3-3, CECE, C-series).
- **Background stubs.** 38 of the 121 engine records carry the tag
  `IDENTITY_FROM_ANALYST_BACKGROUND`. Their designation, lineage, vehicle and cycle come from my general
  knowledge and are not backed by a source from this session. They have no key values, and their
  `cycle_status` is INFERRED or UNKNOWN. Treat them as a checklist for verification, not as data.
- **Cycle labels are often INFERRED.** Many cycles (RL10 closed expander, SSME fuel-rich staged
  combustion, F-1/H-1/LR87 gas generator) are textbook facts that did not appear in any excerpt. They
  are marked INFERRED, not REPORTED. Cycles REPORTED from a Tier A source: J-2 (gas generator, NTRS
  20100027318), J-2X (gas generator, NTRS) and XRS-2200 (gas generator with linear aerospike, NTRS
  19980174934).
- **Attribution caveat.** Several search summaries merged multiple pages. Where I could not tell which
  page a sentence came from, the key value's note says "attribution inferred".

## Counts

121 engine records in 39 families, 174 key values, 132 sources, 25 conflicts and 7 schematic
pointers. No schematic was viewed; all 7 are `cited_by_other_source` or have an inferred existence.

## Family lineages (as represented)

- **Navaho, Redstone, Jupiter/Thor, H-1, RS-27.** The chain runs XLR43-NA-1 (75K, LOX/alcohol,
  H2O2 steam turbopump) → NAA 75-110 A-1…A-7 (Redstone) and → XLR71-NA-1 (120K) → XLR83-NA-1
  (3×135K, JP-4, "G38"). Next is S-3D/LR79 (Jupiter, Thor), then MB-3 (Delta), then H-1 (Saturn
  I/IB), then RS-27 → RS-27A (Delta II).
  - The S-3D → H-1 and H-1 → RS-27 links are background knowledge. Wikipedia's claim that S-3D was
    "based on the Redstone engine" is loose.
- **Atlas.**
  - MA-1/2/3/5/5A are *propulsion-system* names, not engines. They are not recorded as engines; they
    appear only in aliases and notes.
  - The engines are LR89 (booster), LR105 (sustainer), LR101 (vernier) and RS-56-OBA/OSA (Atlas II).
  - Dash-number mapping is the weakest area: LR89-5 vs LR89-7 for MA-5 (CF-15). LR89-NA-3, LR89-NA-6
    and LR105-NA-3 are background stubs.
- **Titan.**
  - LR87-AJ-3 (LOX/RP-1) → -5 (N2O4/A-50) → -7 (Gemini) → -9 → -11 → -11A.
  - LR91 mirrors the LR87 sequence. LR91-AJ-11 is "similar to one chamber of LR87-AJ-11" (Purdue).
  - The LR87 LH2 variant is a placeholder designation (`LR87-LH2`); it needs a real designation.
- **J-2.** J-2 (gas generator) → J-2S (tap-off, idle modes; AEDC test reports AD0874400 and AD0867628)
  → J-2T-200K/250K (aerospike; unsourced stubs) → J-2X (gas generator, 294 klbf, 448 s).
  - The NTRS comparison table (230/265/294 klbf; 425/436/448 s) is a good Tier A anchor for J-2,
    J-2S and J-2X at once.
- **RL10.**
  - A-1 → A-3 → A-3-1 → A-3-3 → A-3-3A → A-4 → A-4-1 → A-4-2; A-5 (DC-X sea-level version); B-2 (Delta
    III/IV, extendible nozzle); C-series after 2010.
  - NASA TM-107318 states that A-3-3A, A-4 and A-4-1 keep the A-1 basic configuration.
- **AJ10 (launch-vehicle upper-stage variants only).**
  - -37 (Vanguard) → -42 / -101 (Able) → -104/-104D (Ablestar) → -118 / -118A / D / E / F → -118K
    (Delta-K, 1989), plus -138 (Transtage).
  - Spacecraft AJ10s (AJ10-137 for the Apollo SPS, the OMS engine) are left to the spacecraft branch.
- **Agena (Bell Model 8000).**
  - Model numbers: 117 (Hustler pod; stub) → 8001 (BA-3) → 8048 (BA-5) → 8081 (BA-7) → 8096 (BA-11 or
    BA-9: conflict CF-06) → 8247 (BA-13, Gemini Agena Target Vehicle).
  - Records use the Bell model number as the designation and the XLR81 number as a military alias,
    because the military dash numbers are disputed.
- **TR-201** derives from the LMDE (a spacecraft engine). Its parent designation "LMDE (Apollo LM
  Descent Engine)" is outside this branch, so it should be cross-linked with the spacecraft branch.

## Alias and identity problems

- **Ratings vs variants.**
  - H-1 165K/188K/200K/205K and F-1 1.500/1.522 Mlbf are ratings of the same designation.
  - H-1 was split into four records because the brief asked for it.
  - F-1 is kept as one record with two dated values, plus F-1A. Taxonomy should decide which approach
    to use.
- **"FPL" for SSME.** Full Power Level (109% RPL) is a power level, not a configuration. The record
  "SSME (FPL / Phase I)" stands for the first-flight configuration and needs renaming.
- **RS-25 thrust reference condition.**
  - A search summary called 491,000 lbf (104.5%) "sea level". By arithmetic it is the vacuum value:
    491,000 / 1.045 ≈ 470k at 100% RPL.
  - Always store RS-25 thrust with both %RPL and condition (CF-18).
- **XLR11 family.** 6000C4 = XLR11 = XLR8 (Navy, D-558-2).
  - The brief's suggested "LR-8 (Viking)" alias is not supported: the Viking engine is XLR10-RM-2.
  - The X-1 engine is RM-5 per Wikipedia and RM-3 per a Tier E source.
- **AJ26 / NK-33** belongs to the USSR branch. AJ26-58/-59/-62 are Aerojet's US designations for
  modified NK-33s (Kistler, Antares). That is background knowledge, not sourced here.
- **XF30L20000** is the 1944 Corporal *concept* designation. Production Corporal engine designations
  were not found.
- **MB-3 = LR79-NA-9.** This equivalence comes only from a Pima museum placard, which also wrongly puts
  it on Atlas E/F (CF-11).
- **Out of scope or excluded.**
  - P&W 304 (Suntan) is a hydrogen jet engine, so it is excluded.
  - The Bomarc booster (Aerojet LR59) and LR62 were not researched.
  - AJ-260 is a solid motor, so it is excluded.
  - F-1B (2012) and RS-68B are after 2010 and commercial or proposal-stage.

## Weak-source areas

The following rest on Tier D/E sources only:

- Atlas engine dash numbers
- Agena designations
- Redstone A-x details (heroicrelics, enginehistory)
- LR87 chamber pressures (Astronautix; LR87-7 < LR87-5 looks wrong, CF-19)
- Corporal and WAC Corporal propellants
- XLR25 and XLR99 details (USAF museum fact sheets and This Day in Aviation)

Tier A values from excerpts:

- J-2 and J-2X (NTRS)
- RL10A-3-3A (NTRS 19910018888)
- RS-68A (L3Harris datasheet)
- RS-25 RPL convention (NTRS 20180006338, 20170008958)
- Redstone A-7 at 78,000 lbf (NASA MSFC)
- F-1 re-rating (NASA-credited MSFC caption)
- M-1 at 1.5 Mlbf (NASA GRC)
- XRS-2200 cycle (NTRS 19980174934)

## Tier A references still to retrieve

None of these were retrieved. Document numbers marked unverified come from the brief or from memory.

- NASA SP-8107, *Turbopump Systems for Liquid Rocket Engines*. The list of engines it tabulates was not
  audited.
- Other SP-8xxx monographs.
- Rocketdyne *SSME Orientation* (BC98-04, unverified).
- F-1 Engine Familiarization manual (R-3896-1, from the brief, unverified).
- J-2 and H-1 engine manuals.
- Saturn V Flight Manual (MSFC-MAN-50x, unverified).
- AEDC J-2S reports (AD0874400, AD0867628): DTIC PDFs, direct URLs seen.
- NTIS AD508757 (XLR129-P-1 demonstrator design, 1970).
- DTIC AD0423340 (1963 Rocketdyne vernier report).
- Sutton, *History of Liquid Propellant Rocket Engines* (AIAA 2006): Tier C, restricted, not consulted.

## Dead or blocked links

All URLs in `sources.json` appeared in search results but could not be fetched from this sandbox. They
are not known to be dead.

## Recommended anchor engines from this branch

1. **J-2 / J-2S / J-2X.** One NTRS table gives thrust and Isp for all three, and the cycles differ
   (gas generator, tap-off, gas generator). That makes the family a good test of cycle taxonomy and
   variant lineage.
2. **RL10A-3-3A.** NASA TM-107318 is a full engine modeling report (Tier A, public domain) with
   P&W-reported Pc 475 psia, ε 61 and 16,500 lbf. It is the best open closed-expander reference.
3. **RS-68A.** A manufacturer datasheet gives SL and vacuum thrust, Isp and Pc. It is a clean
   gas-generator LOX/LH2 anchor.
4. **F-1.** The rating history is documented by NASA, and the engine is an iconic gas-generator
   LOX/RP-1 reference. Pair it with the F-1 familiarization manual once retrieved.
5. **RS-25 (Block II / RS-25D).** It is the staged-combustion anchor and the reference for the RPL
   convention. Values must carry %RPL and condition.
6. **NAA 75-110 A-7 (Redstone).** NASA MSFC gives 78,000 lbf, and the engine is the canonical H2O2
   steam-turbine (separate working fluid) case.

## Unresolved questions

- J-2 rating history (200K/225K/230K) was not confirmed.
- Was the XLR129 actually staged combustion? This is believed but was not confirmed in the excerpts.
- XLR99-RM-1 vs RM-2 distinction.
- Which Delta models used AJ10-118A/D/E/F.
- RS-27C identity.
- Feed system of each XLR11 sub-variant.
- Whether the X-405 turbine used H2O2 or a gas generator (Wikipedia excerpt says gas generator).
