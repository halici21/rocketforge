# asia_other branch — NOTES

## Session constraints (read first)
- **WebFetch failed for every host** (DNS `ENOTFOUND`), and `curl` through the agent proxy got `403 CONNECT` from wikipedia.org, jaxa.jp, isro.gov.in, astronautix.com, b14643.de, kari.re.kr, ntrs.nasa.gov, mhi.com, arc.aiaa.org.
- So **every source here has `access: search_result_only`**. Values come from search-engine result summaries of the cited pages. The pages themselves were never opened.
  Treat all `REPORTED` values as "reported by that page according to the search summary". Confirm them against the page before using them in production.
- **The shared WebSearch budget (200 per turn, across all agents) ran out after 18 queries in this branch.** Research stopped partway, after Japan (major LH2 engines) and China (state engines plus LandSpace, Space Pioneer and iSpace).
- 40 records are **NOT_AUDITED identity stubs**. Their notes start with "NOT_AUDITED…". They cover India, Korea, Iran, DPRK, Brazil, Argentina, Egypt, Galactic Energy, Deep Blue, Jiuzhou Yunjian and the minor Japanese engines.
  Their designation, family and hints come **only from the orchestrator's scope list** and are explicitly marked unverified. They have no key_values and no source_ids.
  Re-run this branch for those countries in a later turn.

## Coverage
- Researched with sources: Japan, 8 records (LE-5, LE-5A, LE-5B, LE-5B-2, LE-5B-3, LE-7, LE-7A, LE-9).
- Researched with sources: China, 41 records:
  - State: YF-1, YF-1B, YF-2, YF-3, YF-3A, YF-20, YF-20B, YF-21, YF-21B, YF-22, YF-22B, YF-23, YF-24, YF-24C, YF-25, YF-40, YF-40A, YF-50D, YF-73, YF-75, YF-75D, YF-77, YF-100, YF-100K, YF-100L, YF-100M, YF-115, YF-130, YF-209, YF-215.
  - Commercial: TQ-11, TQ-12, TQ-12A, TQ-12B, TQ-15A, TQ-15B, TH-11, TH-12, TH-12V, JD-1, JD-2.
- Primary-tier (A) sources actually seen in results:
  - MHI product pages for LE-5B, LE-7A and LE-9.
  - JAXA's H-II page.
  - Space Pioneer's TH-12 and TH-12V pages.
- Tier B (IAC abstracts, metadata only):
  - IAC-17 LE-9 status paper.
  - IAC-13 papers on Chinese LOX/LH2 engines.
  - IAC-15 review of Chinese LOX/kerosene staged-combustion engines.
  - IAC-16 paper on the 180 kN LOX/kerosene upper-stage engine (YF-115).

## Family lineages (as sourced)
- **LE-5 line:**
  - LE-5 is a gas-generator engine (H-I).
  - LE-5A is expander bleed, cooling both chamber and nozzle (H-II). It is called the first operational expander-bleed engine.
  - LE-5B is expander bleed with chamber-only cooling, with 180 injector elements.
  - LE-5B-2 has 306 elements, laminarizing plates and a new GH2/LH2 mixer (H-IIB, 2009).
  - LE-5B-3 is used on H3.
- **LE-7 line:** LE-7 is a fuel-rich staged-combustion engine at 12.7 MPa. LE-7A runs at a reduced preburner temperature, has short- and long-nozzle versions, and runs at about 12 MPa.
  LE-9 breaks this line: it is a new expander-bleed first-stage engine, not an LE-7 derivative.
- **YF-1 / YF-2 / YF-3:** YF-2 is a 4×YF-1 module and YF-3 is the upper-stage version (DF-4). The YF-1 oxidizer is inconsistent inside the Wikipedia article: AK27S originally, N2O4 for YF-1B.
- **YF-20 family:**
  - YF-20 is the single-chamber base engine.
  - YF-21 is a 4×YF-20 module; YF-21B is a 4×YF-20B module.
  - YF-22 is the vacuum version; YF-22B is also indexed DaFY20-1.
  - YF-23 is the vernier, and YF-24 is the YF-22 + YF-23 module.
  - YF-25 is the single booster version.
  - The orchestrator hint that "YF-21 has 4 chambers sharing one turbopump" was **not confirmed**. No source seen says whether the turbopumps are shared, so `chambers_note` flags it.
- **YF-100:** YF-100K/L (CZ-10 stage 1 and boosters, ~1250 kN SL) and YF-100M (high-altitude, 1450 kN vac). These figures are from The Paper, a news source tier D, which probably quotes AALPT. English press says YF-100 derives from RD-120 technology (unverified).
- **YF-75 → YF-75D:** the cycle changed from gas generator to closed expander. YF-75D has a lengthened chamber and a two-stage axial turbine at 65,000 rpm.

## Architecture surprises / flags
- TH-12 is described on Wikipedia as "oxidizer-rich gas-generator", which is unusual wording for kerolox. The manufacturer page says only gas generator (TH-12V). Logged as conflict CF-15.
- TQ-15A has 836 kN vacuum thrust, 334.5 s, O/F 2.9 and ε 50 (popular-science govt page). That Isp is low for a vacuum methalox engine. This may mix generations of data; check against LandSpace releases.
- The YF-40 "2 chambers" and "~100 kN" figures do not say whether they are per unit or per stage (CF-12).
- LE-5B-3 is listed at 137 kN, which is *lower* than LE-5B-2's 144.9 kN in the same Wikipedia table. This looks like possible table mixing; verify against MHI or JAXA.
- YF-130 is a dual-nozzle engine per SpaceNews. Chamber count is set to 2 on that single tier-D source.

## Weak-source areas
- China: nearly all numbers are tier D (Wikipedia and mirrors, GlobalSecurity, news) or tier E (Bilibili compilation).
  - The YF-100 Pc of 18 MPa, Isp of 335 s and other performance values come only from Bilibili and are marked SECONDARY_CLAIM.
  - Developer-institute attribution (Beijing 11th Institute vs Xi'an 11th Institute) is unverified except "Xi'an Aerospace Propulsion Institute" for YF-115, which is from the Wikipedia summary.
- Weblio pages are ja.wikipedia mirrors, often older versions.

## Leads not followed (search results seen but not used)
- jaxa.repo.nii.ac.jp/records/45156 (appeared for LE-7A; content unknown).
- karya.brin.go.id/10497/1/Jurnal TD_Bagus_Pustekroket_2007.pdf: an Indonesian LAPAN/Pustekroket propulsion paper, content unknown. This is a possible Indonesian liquid-engine lead.
- Yuzhnoye RD861K page (test5.yuzhnoye.com): out of scope (UA).
- orbitcodex.com and spaceodysseyhub: they claim Tianlong-3 failed its 3 Apr 2026 maiden flight and that JD-2 was qualified in Apr 2026. These are low-reliability aggregators and are not recorded as sources.
- spacecraft engines: none came up.

## Israel / Turkey / Taiwan / Australia / Pakistan
No records were created. No research was possible, and the orchestrator itself notes these may have no credible liquid launch engines:
- Shavit is solid.
- TiSpace and Gilmour are hybrids, so they are excluded.

## Recommended anchor engines from this branch
- **LE-7A**: has a manufacturer page (MHI), the AIAA guide and Wikipedia; fuel-rich staged combustion; short/long-nozzle variants are a good variant test.
- **LE-5A / LE-5B / LE-5B-2**: the clearest documented expander-bleed lineage, with a chamber+nozzle vs chamber-only bleed distinction.
- **LE-9**: first-stage expander bleed, with an MHI page and an IAC paper.
- **YF-77 / YF-75D**: LH2 gas generator vs closed expander, with IAC abstracts.
- **YF-20 family**: the best test of the module-vs-engine naming discipline (YF-21 / YF-24 are modules).
