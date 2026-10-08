# DB-0 — Global liquid rocket engine discovery and architecture research

**Status: DB-0 = PARTIAL.** A broad, best-effort global map of publicly
documented liquid-propellant rocket engines, their families and variants,
architectures, schematics, sources, conflicts and rights, built to let DB-1
design a reference engine database without rediscovering the field. It is
**not** a production database and **not** a complete inventory, and none of its
values is regression-grade: no source document could be opened during the
research (see §3).

| Milestone | State |
| --- | --- |
| DB-0 Global Liquid Engine Research Map | **PARTIAL** — identity and architecture map broad; values from search summaries only |
| DB-1 Production Reference Engine Schema | NOT STARTED (proposal in [SCHEMA_PROPOSAL.md](SCHEMA_PROPOSAL.md)) |
| DB-2 Production Engine Corpus | NOT STARTED |
| LIQ-7 Pump Foundation | PAUSED FOR DATABASE RESEARCH |

## 1. Package contents

| Document | What it holds |
| --- | --- |
| this file | goal, method, findings, limitations, DB-1 recommendation |
| [ENGINE_ARCHITECTURE_TAXONOMY.md](ENGINE_ARCHITECTURE_TAXONOMY.md) | feed, cycle, pressurization, cooling, injector, turbomachinery, start/control taxonomy; aliases and look-alike categories; hardware evidence per category |
| [ENGINE_FAMILY_MASTER_LIST.md](ENGINE_FAMILY_MASTER_LIST.md) | 576 variant records in 227 families, by country and family (generated) |
| [ANCHOR_ENGINE_CORPUS.md](ANCHOR_ENGINE_CORPUS.md) | 46 deeply audited anchor variants: coverage matrix, assertions, topology, schema breakers (generated + narrative) |
| [FLOW_SCHEMATIC_INDEX.md](FLOW_SCHEMATIC_INDEX.md) | 71 schematic entries with locators, rights and verification state |
| [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md) | 1,057 sources: tier, rights, access |
| [CONFLICT_LEDGER.md](CONFLICT_LEDGER.md) | 261 recorded conflicts, never averaged |
| [RIGHTS_MATRIX.md](RIGHTS_MATRIX.md) | rights by source class and content kind; legal-review questions |
| [SCHEMA_PROPOSAL.md](SCHEMA_PROPOSAL.md) | DB-1 entities and relations, stress-tested against real engines |
| [COVERAGE_GAPS.md](COVERAGE_GAPS.md) | what is missing, by region, engine, subsystem and rights |
| [data/](data/README.md) | machine-readable research artifacts (JSON + CSV) |
| [branch_notes/](branch_notes/README.md) | raw per-branch working notes, incl. each branch's priority documents to open |

## 2. Goal and scope

**Goal.** Discover the real information landscape for liquid rocket engines
before a database is designed: which engines and variants exist or existed,
how they group into families, which feed and cycle architectures occur in
hardware, what flow schematics and subsystem data are public, which sources are
authoritative, where they disagree, where information is missing, what rights
restrictions apply, and what schema RocketForge will need.

**Scope.** Liquid-propellant chemical rocket engines and thrusters of every
role — booster, sustainer, core, upper stage, kick stage, spacecraft main,
orbital manoeuvring, lander descent/ascent, RCS, missile, aircraft rocket,
demonstrator, experimental — from the 1920s to October 2026. Bipropellants
first; monopropellant, tripropellant, HTP and green-propellant thrusters where
technically relevant. Solid and hybrid motors are excluded except where they
explain a shared subsystem (solid start cartridges, the Vexin B solid gas
generator). Nuclear engines are excluded.

## 3. How the research was actually done

### 3.1 Method
1. Repository inspection: `rocketforge/evidence` (`ReportedValue`, `Missing`,
   `ValueStatus`, `MissingReason`, `ShippingPolicy`, `SourceReference`),
   LIQ-1…LIQ-6 and SYS-1…SYS-5 design documents, the LIQ-2 feed/cycle rule.
2. A shared research brief fixing the record formats, evidence statuses,
   missing-value reasons, source tiers and rights classes.
3. **Round 1** — twelve parallel research branches: US historical, US/NZ
   commercial, USSR/Russia/Ukraine, Europe, Asia and other countries,
   spacecraft/RCS/lander, architecture taxonomy and schematics, rights, and four
   anchor deep-dives (US classic, US modern/spacecraft, Soviet/Russian + A4,
   Europe/Asia).
4. **Round 2** — five gap-filling branches with an explicit per-branch search
   budget: US classic anchors, Soviet anchors and identity gaps, Asia/Europe
   anchors and gaps, spacecraft and commercial gaps, schematics and modern
   anchors.
5. Merge: designation-key deduplication across branches with manual id merges
   (e.g. `ENG-EU-VULCAIN-2` → `ENG-FR-VULCAIN-2`, `ENG-CN-CANGQIONG` →
   `ENG-CN-WELKIN`, `ENG-US-SSME-BLOCK-II` → `ENG-US-RS-25D`), family
   consolidation, source-id collision splitting, and source-tier enforcement
   (§5.5).
6. Independent orchestrator cross-checks (§7).

### 3.2 The constraint that shapes every number here

**No source document was opened.** The session's egress policy refused
connections to every documentation host tried — `ntrs.nasa.gov`,
`apps.dtic.mil`, `web.archive.org`, `www.astronautix.com`, Wikipedia, agency
and manufacturer sites — and the web-fetch tool could not resolve any host.
Only web **search** worked, and it returns a summary of each result page, not
the page. The search budget (200 calls per turn, shared by all agents) was
exhausted in round 1; round 2 rationed it explicitly (≤ 38 calls per branch).

Consequences, applied throughout the package:
- Every source carries `access: search_result_only` (or `not_retrieved` /
  `dead_link`, where `dead_link` means policy-refused, not offline).
- A value is `REPORTED` only when the summary attributed it to a named
  Tier A–C document; otherwise it is `SECONDARY_CLAIM`. A merge rule then
  downgraded 154 values and assertions that a branch had marked `REPORTED` but
  whose source is Tier D/E.
- No page, table or figure locator was verified. Locators read "search summary
  only" unless the summary itself named a figure (e.g. "Fig. 1" of AIAA
  97-2687).
- No schematic was viewed. No NTRS copyright field was read. No terms page was
  read.
- Identity records that rest only on the research brief or analyst background
  knowledge are marked `UNSOURCED_PLACEHOLDER` (82 of 576) and kept as a
  verification checklist, not as data.

This is why DB-0 is **PARTIAL**, not COMPLETE: the identity and architecture
map is broad, but the deep, page-located, regression-grade evidence the brief
asks for requires document access. The registry, ledgers and anchor files are
built so that DB-1 can open each document and promote evidence without
re-doing discovery.

## 4. Source hierarchy

| Tier | Class | Count | Use |
| --- | --- | --- | --- |
| A | NASA NTRS / SP / TM / TN / CR, DTIC, agencies (ESA, JAXA, ISRO, KARI, CNES), manufacturer datasheets and pages, export catalogues (Glavkosmos), patents | 290 | primary evidence once opened |
| B | AIAA, IAC/IAF, EUCASS, JPP, journals, theses, contractor reports | 112 | primary or strong secondary |
| C | Sutton & Biblarz 9th ed., Huzel & Huang (NASA SP-125; AIAA 1992), Sutton *History of LPRE* | 8 | definitions; isolated facts with citation |
| D | Wikipedia (all languages), Astronautix, Gunter, Brügge, RussianSpaceWeb, Space Launch Report, museum pages, university data pages | 537 | discovery; values only as secondary claims |
| E | forums, blogs, news aggregators, unsourced compilations | 110 | leads only |

Tier D dominates the count because it is where search lands first. The
registry deliberately keeps those records so a reader can see what each value
rests on.

## 5. Major findings

### 5.1 Coverage (best-effort, not complete)

- **576 engine variant / configuration records in 227 families**; 494 rest on
  at least one source, 82 are unsourced placeholders.
- **By country of origin (primary code):** US 247 · USSR/Russia 122 (SU 114,
  RU 8) · China 52 · Germany 33 · France 26 · UK 22 · India 19 · Japan 19 ·
  Ukraine 7 · Iran 5 · Argentina 4 · North Korea 4 · South Korea 4 · Brazil 3 ·
  Spain 3 · Sweden 3 · Italy 2 · Egypt 1 · multinational Europe 1. New Zealand
  appears through Rocket Lab (recorded `US/NZ`).
- **By role:** upper stage 174, booster 167, missile 84, core 53, RCS 51,
  spacecraft main 40, demonstrator 27, aircraft rocket 27, orbital manoeuvring
  25, experimental 22, lander descent 16, sustainer 12, lander ascent 1 (more
  ascent engines exist as spacecraft-main records).
- **By era** (first dated year in the record): 1920s–1940s 32, 1950s 44,
  1960s 73, 1970s 28, 1980s 14, 1990s 35, 2000s 37, 2010s 52, 2020s 44; 217
  undated.
- **By status:** retired 286, operational 129, development 66, cancelled 61,
  unknown 25, experimental 5, proposed 5.
- **Values:** 1,471 key values on the inventory (354 REPORTED, 1,114
  SECONDARY_CLAIM, 3 DERIVED) plus 820 anchor assertions. 195 records have
  no value at all; 119 have at least one REPORTED value.
- **Anchors:** 46 variant-level anchor files covering every hardware
  architecture category (see ANCHOR_ENGINE_CORPUS.md).
- **Schematics:** 71 entries; a handful with real figure numbers (SSME AIAA
  97-2687 Fig. 1; JSC-19041 Figs. 1.1-II/-III; RL10 NTRS 19950022693 Fig. 1;
  RD-170 JPP 2018 Fig. 1); none viewed.

### 5.2 Architecture findings

1. **Feed and cycle are separate, and "cycle" must itself be split.** The
   LIQ-2 rule is upheld. Named cycles mix three independent facts: turbine drive
   source, turbine exhaust destination, and turbine flow fraction. Gas-generator
   engines alone dump turbine gas overboard, into the nozzle extension (F-1,
   Vulcain 2), through steering nozzles (RD-0110) or via a pressurization heat
   exchanger (LR87, KRE-075). See taxonomy §1.
2. **Every taxonomy category with a hardware example was found to have one**,
   including the rare ones: full-flow staged combustion (RD-270 ground test,
   IPD powerhead, Raptor flight), tap-off (J-2S ground; BE-3PM and Firefly's
   Reaver/Lightning/Miranda flight — the makers' own wording), expander bleed
   as a large booster cycle (LE-9), electric pump (Rutherford, Delphin; Agnilet
   reported), positive-displacement pump (XCOR, test only), third-fluid H2O2
   turbine drive (A4, R-7, RD-214, HWK 109-509). Categories with **no flight
   hardware** found: rotating centrifugal feed (Roton), Tridyne
   pressurization, main-tank injection, monopropellant GG turbine drive,
   self-pressurized liquid main engine.
3. **"Open expander" ≡ "expander bleed"** (JAXA's own framing); "chamber
   bleed" is a sub-variant attribute.
4. **Russian "газогенератор" is used for closed-cycle preburners too.** Mapping
   it to "gas-generator cycle" automatically would misclassify staged-combustion
   engines.
5. **One engine can mix cycles**: the R-27 4D10 has a staged-combustion main
   chamber plus two gas-generator steering chambers (r2_ussr, secondary).
6. **Multi-chamber topology is real and varied.** RD-170: two preburners → one
   turbine → four chambers (NTRS 19910018906). RD-107/108: four main chambers
   plus two or four verniers on one H2O2-driven turbopump. LR87: two chambers,
   two turbopumps. YF-21/YF-24: modules of complete engines.
7. **Pressurization belongs to the stage, with engine-mounted ports.** S-IVB/J-2
   heat exchanger, SSME GOX heat exchanger, Titan II GG-gas and N2O4
   superheater, R-7 nitrogen system, RD-0234 pressurant heat exchanger, RD-0120
   hydrogen tap. "Autogenous" covers both propellant-vapour and GG-product
   pressurization and should be split.
8. **Corrections to common assumptions:** the water-quenched gas generator is
   Vexin B's (Diamant A), not Viking's; the Soyuz third stage's RD-0110 is a
   LOX/kerosene GG, not H2O2-driven; Raptor is "staged combustion" in SpaceX's
   own words and "full-flow" only in secondary sources; Merlin 1D's GG cycle is
   stated in the 2025 Falcon User's Guide.

### 5.3 Source findings

- **Strongest families:** NASA NTRS (SSME, J-2/J-2X, RL10, H-1, F-1, IPD,
  Apollo Experience Reports, RD-170 1989 slides), L3Harris/Aerojet Rocketdyne
  datasheets, ULA/Arianespace/SpaceX/Rocket Lab user's guides, Glavkosmos export
  data, JAXA/MHI/IHI papers and IAC papers, ESA inquiry and programme pages,
  ISRO pages, KARI EUCASS/IAC papers.
- **Weak-source regions and programmes:** Soviet missile engines, Isayev/KB
  KhimMash and Yuzhnoye engines, Chinese state engines (institute attribution
  mostly unverified), Iranian and North Korean engines (only analyst and press
  sources), Chinese and Western commercial start-ups (company pages and press).
- **Inaccessible / archive gaps:** every primary document (§3.2); DTIC; the
  SP-8000 monographs (only SP-8107 = NTRS 19750012398 and SP-125 2nd ed. = NTRS
  19710019929 seen); Russian journal *Dvigatel* scans; JAXA Repository records;
  Soyuz User's Manual tables.
- **Identity corrections made during DB-0:** R-3896-1 is the F-1 Engine Data
  volume; the LM descent experience report is TN D-7143; "SSME Orientation" is
  two documents (1984 manual; 1998 proprietary-marked handout).

### 5.4 Flow schematics

Engines with **located** public-domain schematic leads: SSME/RS-25, RL10, H-1,
F-1 and J-2 (Saturn V flight manual), LM descent/ascent and Apollo SPS (Apollo
Experience Reports), Shuttle OMS, IPD (DTIC), generic cycles (SP-8107). Engines
with **restricted** schematics only: RD-170 (JPP), LE-9 (JAXA/IAC), Vulcain,
RD-0120. **No schematic located** for RS-68/RS-68A, LR87/LR91 (no HAER drawing
found), NK-33, Merlin, Raptor, BE-4. Topology extraction is feasible: the
anchor files hold text-derived graphs (SSME 25 nodes / 32 edges; J-2 16/16;
LR87 15/17; RD-170 13/16; RD-107A 13/12), each with an explicit
`topology_completeness` statement. The main risk is treating a simplified
diagram as a bill of materials (taxonomy §10; schema §3.3).

### 5.5 Data quality

- **261 conflicts** recorded (CONFLICT_LEDGER.md). Dominant patterns:
  re-rating under one designation, sea-level/vacuum confusion, rated-power
  percentage conventions, chamber-pressure definition and units, variant
  contamination, index/alias disputes, manufacturer page revisions.
- **Alias problems:** GRAU/manufacturer indices disputed (NK-33 11D111 vs
  14D15; 15D117 vs 15D119); generic aliases ("MVac", "Merlin Vacuum") spanning
  generations; module and propulsion-system names (YF-21, RD-0212, Atlas MA-5)
  mistaken for engines; renames (M10 → MR10, SCE-200 → SE-2000); press
  garbling (RD-124MV).
- **Variant contamination risks** found and blocked: Vulcain 1 turbopump speeds
  on Vulcain 2 pages; RD-0210 dimensions attached to RD-0124; NK-33 data in an
  NK-15 spec set; RL10A-3-3A data near RL10A-4-2; J-2X facts in J-2 summaries.
- **Fields almost always missing:** injector Δp, element counts, cooling
  channel data, pump inlet/outlet pressures, turbine inlet states, GG/preburner
  mixture ratio and temperature, start sequences, valve inventories.
- **Tier enforcement:** 154 values and assertions marked `REPORTED` by a
  branch were downgraded to `SECONDARY_CLAIM` at merge because their source is
  Tier D/E.

### 5.6 Rights

- **Open/public:** US-Government works (NTRS public-use records, NASA history
  SPs, US patents) for values, text and most figures (contractor-authored
  figures need review); ISRO site material with acknowledgement; Wikipedia
  text (CC BY-SA, but Tier D).
- **Restricted references:** textbooks, AIAA/IAC/JPP papers by non-Government
  authors, ESA/CNES/JAXA/DLR (unlabelled) figures, manufacturer documents,
  Russian and Chinese agency and company material, personal encyclopedias
  (EU database right for Gunter, Brügge).
- **Unresolved:** twelve legal-review questions (RIGHTS_MATRIX.md §7), led by
  contractor-authored NASA SPs/CRs, RocketForge's commercial status under agency
  terms, export control of military-engine data, and re-rendered topology.

### 5.7 Schema

The existing evidence model is the right foundation (value as printed,
explicit `Missing`, status, per-source shipping), but it breaks on: non-numeric
and range values, missing condition qualifiers (sea level/vacuum, abs/gauge,
Pc station, Isp basis), operating points, rating epochs,
`MissingReason.ACCESS_BLOCKED`, A–E tiers, and per-content-kind rights. DB-1
needs family / variant / configuration / operating point, hardware entities
(chamber assemblies, turbopump → shaft → pump/turbine/gearbox, combustors,
energy stores, effectors), a first-class topology graph with mechanical and
electrical edges and graph-level completeness, and conflicts as sets of
assertions. Twelve concrete cases that broke simpler assumptions are listed in
SCHEMA_PROPOSAL.md §4.

### 5.8 Findings for RocketForge (documented only — nothing changed)

- **LIQ-2's power-cycle enumeration** (gas generator, expander, staged
  combustion, FFSC) has no value for flight cycles DB-0 confirmed: tap-off,
  expander bleed, electric pump, and third-fluid turbine drive. LIQ-2 is
  intent-only and this is not a defect in any computed result; it is input for
  a future LIQ/DB decision. No accepted solver, baseline or LIQ/SYS/ENV file was
  modified.
- **`MissingReason.WITHHELD_RIGHTS`** in the code corresponds to the brief's
  `RIGHTS_RESTRICTED`; there is no `ACCESS_BLOCKED`. Engine evidence needs the
  latter (SCHEMA_PROPOSAL.md G5).
- No RocketForge physics bug was found.

## 6. Limitations

- Values come from search summaries; none is regression-grade (§3.2).
- 82 identity records are unsourced placeholders.
- 126 records have `cycle = UNKNOWN`; 228 have an `INFERRED` cycle (a
  hypothesis from propellants, era or family).
- Some country/organization sweeps were thin (COVERAGE_GAPS.md §1).
- Developer attribution for Chinese institutes, Soviet design bureaus' index
  numbers and many dates are unverified.
- Rights classes are provisional; no repository copyright field was read.
- Id prefixes for Soviet/Russian engines are inconsistent (`ENG-SU-` vs
  `ENG-RU-`); ids are opaque and stable, and the country field carries the
  meaning.

## 7. Verification performed

| Check | Result |
| --- | --- |
| Internal consistency of the master list | merged ids unique; every source id referenced by an engine, key value, schematic or anchor resolves in the registry; conflict claims without a registered source carry `origin` instead (enforced by `tests/research/test_db0_research_artifacts.py`) |
| Duplicates | designation-key dedup across 18 branch outputs (12 round-1, 5 round-2, 1 orchestrator check); manual merges for renamed/duplicated records; remaining alias collisions listed in the master list |
| Stage/system names as engines | flagged: YF-21/24 modules, RD-0212, Atlas MA-x (alias only), Iranian/North Korean stage-level records whose engine designation is unknown |
| Tier vs status | 154 REPORTED → SECONDARY_CLAIM downgrades for Tier D/E sources |
| Feed/cycle consistency | no pressure-fed record carries a cycle; no pump-fed record carries `none_pressure_fed`; electric pump ⇔ `pump_fed_electric` |
| Independent identity cross-checks (orchestrator searches) | **RD-170** four chambers on one single-shaft, single-turbine turbopump, ox-rich SC (Wikipedia) — consistent with the NTRS slide "1 TPA driven by 2 preburners"; **LE-9** expander bleed, 1,471 kN, JAXA IAC-17 (Pc 10.0 MPa vs an older 12.4 MPa); **Vikas** SEP Viking licence, UDMH/N2O4 GG, versioned thrust; **YF-100** ox-rich SC, 1,200 kN SL (IAC-15 review paper exists); **Vexin** pressure-fed, solid GG quenched with water (IAC-09); **Rutherford** brushless DC motors and Li-polymer batteries (Rocket Lab); **KRE-075** fuel-rich GG (KARI EUCASS 2019); **F-1** 1.500 → 1.522 Mlbf (timing conflict added); **SSME** ε 77.5 widely, 69 only in the Wikipedia infobox (conflict added; the "large throat" explanation remains single-source) |
| Every architecture category has an example or is marked theoretical/experimental | taxonomy §11 |
| Schematic registry references actual figures | entries with figure numbers say so; all others are explicitly `described_in_text` or `cited_by_other_source` |
| "Not shown" never converted to "absent" | anchors use `Missing(NOT_REPORTED/NOT_AUDITED/…)`; topology graphs carry completeness statements; no `false` flags for unmentioned hardware |
| Machine-readable artifacts | JSON parses; ids unique; enumerations valid; units stored as printed (unit vocabulary listed in data/README.md) |
| Repository checks | research data test, architecture test, `git diff --check` (see final report) |

## 8. Recommendation for DB-1

**Implementation scope (DB-1):**
1. Evidence extensions (SCHEMA_PROPOSAL.md §7.1): typed assertion values,
   conditions, operating points, epochs, `ACCESS_BLOCKED`, A–E tiers with a
   mapping to the existing 1–3, per-content-kind rights. Keep `ReportedValue`
   unchanged; add engine types beside it.
2. Identity layer with the no-numeric-inheritance validator; module and
   propulsion-system entities; lineage edges.
3. Topology graph (mechanical and electrical edges, graph completeness,
   per-element evidence status).
4. Loader and validator mirroring `rocketforge/evidence/load.py` (strict
   schema version, refusal of unknown fields).
5. **A document-access pass first.** Re-run the anchor audit with network
   access to NTRS, DTIC, agency and manufacturer hosts, opening each Tier A/B
   document and promoting assertions from `search_result_only` to `fetched` with
   page/figure locators and the NTRS copyright field recorded verbatim.

**Recommended first production corpus (DB-2 candidates)** — engines whose
primary documents are US-Government works and which together span the
architectures:
- RS-25 (SSME, Block II / RS-25D) — fuel-rich SC, two preburners, four
  turbopumps;
- J-2 and J-2S — GG with turbines in series; tap-off;
- F-1 — GG with exhaust film-cooling the extension;
- H-1 — geared turbopump GG;
- RL10A-3-3A (the variant NTRS documents best) and then RL10A-4-2 / B-2 —
  closed expander;
- Apollo SPS (AJ10-137) and LMDE — regulated pressure-fed, deep throttling;
- Shuttle OMS (AJ10-190);
- IPD — FFSC (DTIC/AFRL);
- RD-170 — only through NASA-hosted material (NTRS 19910018906).

**Research-only (do not ship values):** everything resting on Tier D/E;
modern proprietary engines (Merlin, Raptor, BE-4, BE-3, Rutherford, Archimedes,
Chinese commercial engines) except dated manufacturer headline values;
Iranian and North Korean engines; anything from DTIC Dist B–F or
export-controlled material; anything from Gunter/Brügge (EU database right).

**Suitable for regression-grade validation, once opened:** NASA NTRS reports
with numerical tables (RL10A-3-3A NTRS 19910018888 and TM-107318; J-2 NTRS
20100027318; SSME Block comparisons in the STS-104 FRR and NTRS 20030005845;
Apollo TN D-7375 and TN D-7143), L3Harris datasheets (values only, dated), and
JAXA/MEXT LE-7A tables (values with attribution).
