# DB-0 — Rights and redistribution matrix

**Not legal advice.** This is an engineering triage map. Every
`PUBLIC_DOMAIN_GOV` or `VALUES_WITH_ATTRIBUTION` call below is a working
default, not a clearance. §7 lists the questions that need legal review before
DB-2 ships any value.

**Evidence quality.** No policy page could be opened during DB-0 (the egress
policy refused every host, see
[DB0_RESEARCH_OVERVIEW.md §3](DB0_RESEARCH_OVERVIEW.md#3-how-the-research-was-actually-done)).
Statements marked *(search summary)* were read in search-engine summaries and
must be re-checked verbatim. Statements marked **[BK]** are background knowledge
and were not verified.

## 1. Two vocabularies, and why one decision per source is not enough

RocketForge already ships evidence under one `ShippingPolicy` per source
(`rocketforge/evidence/values.py`): only `VALUES_WITH_ATTRIBUTION` lets a
shipped record carry values (`SourceReference.values_may_ship`), and
`validate_against_sources` enforces it.

DB-0 uses a finer research vocabulary:

| DB-0 rights class | Meaning | Shipped as `ShippingPolicy` |
| --- | --- | --- |
| `PUBLIC_DOMAIN_GOV` | Work of a government with no copyright in the relevant jurisdiction (US 17 USC 105), or a document the repository marks public use | `VALUES_WITH_ATTRIBUTION` |
| `OPEN_LICENSE` (named) | CC BY, CC BY-SA, CC0, … — the named licence governs | `VALUES_WITH_ATTRIBUTION` for values; the licence decides the rest |
| `VALUES_WITH_ATTRIBUTION` | Facts may be stated with a citation; the expression is protected | `VALUES_WITH_ATTRIBUTION` |
| `METADATA_ONLY` | Only the bibliographic record | `METADATA_ONLY` |
| `RESTRICTED_REFERENCE` | Cite it; ship none of its content | `RESTRICTED_REFERENCE` |
| `RIGHTS_REVIEW_REQUIRED` | Blocked until a human decides | `RIGHTS_REVIEW_REQUIRED` |
| `UNKNOWN` | Not yet classified | `RIGHTS_REVIEW_REQUIRED` |

`LICENSED_PROVIDER` (CEA, CoolProp) has no engine-data use.

**The key finding: rights differ by content kind.** A thrust value in Huzel &
Huang (1992) is a fact; its flow schematic is a copyrighted image; a whole
engine table may be a protected compilation; its prose is plainly protected.
**DB-1 should therefore carry a per-content-kind rights tuple
`{values, figures, tables, text}` on each source**, and derive the single
`ShippingPolicy` of a shipped evidence record from the **values** column, which
is all RocketForge ships today. Figures never ship from DB-0.

## 2. Legal principles relied on (flagged for review)

1. **US: facts are not copyrightable** — *Feist v. Rural Telephone*, 499 U.S.
   340 (1991); 17 USC 102(b) excludes "any idea, procedure, process, system,
   method of operation" [BK]. A compilation is protected only in its original
   selection, coordination or arrangement. Isolated values with citations are
   free; mirroring a whole table's selection and order is not.
2. **US Government works:** "Copyright protection under this title is not
   available for any work of the United States Government" (17 USC 105, search
   summary). Covers officers and employees acting in their duties, **not**
   automatically contractors or grantees, and only in the US [BK].
3. **Contractor reports:** under FAR 52.227-14 a contractor may assert
   copyright in technical articles based on contract data; the Government gets
   a "paid-up, nonexclusive, irrevocable, worldwide license to reproduce,
   prepare derivative works, distribute to the public…" (search summary). NASA
   CRs and many SP-8000 monographs (written by contractor engineers [BK]) may
   therefore carry contractor copyright in figures and text. The facts remain
   facts.
4. **EU sui generis database right** (Directive 96/9/EC, Art. 7) [BK]: protects
   a maker's substantial investment in obtaining, verifying or presenting
   contents, against extraction of a substantial part or repeated systematic
   extraction of insubstantial parts; applies to EU makers. Gunter's Space Page,
   Norbert Brügge and Bernd Leitenberger (all German) are plausibly protected
   databases even where each fact is free. **Discovery only; never harvest.**
5. **Japan:** research exceptions (incl. Art. 30-4 data analysis) cover
   analysis, not redistribution [BK].
6. **Russia:** Civil Code Part IV, Art. 1229 — "absence of a prohibition shall
   not be deemed consent" (search summary). No fair-use doctrine [BK].
7. **Trademarks and insignia are separate.** The NASA insignia, logotype and
   seal "may not be used for any purpose without explicit permission" (search
   summary). Engine names are trademarks: nominative use only.

## 3. Per-source-class findings

### 3.1 NASA NTRS / STI
- NTRS records carry a structured copyright object (NASA STI OpenAPI Data
  Dictionary, 06/2021, search summary):
  `determinationType ∈ {NO_PERMISSION, MAY_INCLUDE_COPYRIGHT_MATERIAL,
  GOV_PERMITTED, GOV_PUBLIC_USE_PERMITTED, PUBLIC_USE_PERMITTED, OTHER}`,
  `licenseType ∈ {NO, OPEN_ACCESS, CCBY, CCBYSA, CCBYND, CCBYNC, CCBYNCSA,
  CCBYNCND}`, plus `thirdPartyContentCondition`.
- The UI label "Work of the US Gov. Public Use Permitted." was seen on a NASA
  Publications Guide record — and reportedly also on a 1992 contractor report
  and a 1964 university grant paper. **The label is NTRS's catalogue
  determination, not proof of Government authorship.**
- STI disclaimer (search summary): Government works may contain private
  copyrighted material (quotes, photos, charts, drawings) used under licence.
- **Action for DB-1:** record `determinationType`, `licenseType` and
  `thirdPartyContentCondition` **verbatim** in `rights_statement` per NTRS
  record. `SourceReference.rights_statement` is documented as "Not inferred".
  **No NTRS copyright field was seen for any engine document in DB-0**, so every
  NTRS engine source in the registry is `RIGHTS_REVIEW_REQUIRED` for figures and
  provisionally `PUBLIC_DOMAIN_GOV` / `VALUES_WITH_ATTRIBUTION` for values.

Proposed mapping, per NTRS record:

| determinationType | values | figures | tables | text |
| --- | --- | --- | --- | --- |
| GOV_PUBLIC_USE_PERMITTED | PDG → VWA | PDG unless the caption credits a third party/contractor → RRR | PDG | PDG |
| PUBLIC_USE_PERMITTED | VWA | RRR | VWA | RRR |
| GOV_PERMITTED | VWA (facts) | RR | RR | RR |
| MAY_INCLUDE_COPYRIGHT_MATERIAL | VWA | RRR | RRR | RRR |
| NO_PERMISSION | VWA (isolated facts; bulk → RRR) | RR | RR | RR |
| OTHER / absent | RRR | RRR | RRR | RRR |
| licenseType = CC* | OPEN_LICENSE, terms govern all four | | | |

(PDG = PUBLIC_DOMAIN_GOV, VWA = VALUES_WITH_ATTRIBUTION, RR =
RESTRICTED_REFERENCE, RRR = RIGHTS_REVIEW_REQUIRED, MO = METADATA_ONLY, OL =
OPEN_LICENSE.)

**SP-125 vs the 1992 AIAA edition.** NASA SP-125 (Huzel & Huang, 1967; 2nd ed.
1971, NTRS 19710019929 seen) is a NASA publication by North American Aviation
authors. *Modern Engineering for Design of Liquid-Propellant Rocket Engines*
(AIAA Progress in Astronautics and Aeronautics v.147, 1992) is a separate
AIAA-copyright work: `RESTRICTED_REFERENCE`. Some catalogues file both under
"SP-125". Do not conflate them.

### 3.2 DTIC and US Air Force / Army reports
DoDI 5230.24 distribution statements (search summary): **A** public release,
unlimited; **B–F** progressively restricted. Statement A is a **release**
decision, not a copyright decision.

| Case | Rights |
| --- | --- |
| Dist A, Government author | PDG in all columns |
| Dist A, contractor author | values VWA; figures/tables/text RRR |
| Dist B–F, or any export-control warning | **Do not ingest.** MO at most; ITAR/EAR is a legal question |

### 3.3 Patents
- **US patents:** text and drawings generally free, unless the specification
  carries the 37 CFR 1.71(e) authorization language and a 1.84(s) drawing
  notice (search summary). Check per patent; cite the USPTO number. Default:
  VWA for values, figures, tables and text.
- **Foreign patents (EPO, WIPO, JPO, CNIPA):** not verified. Values VWA;
  figures RRR.

### 3.4 Other agencies

| Agency | Finding | values | figures | tables | text |
| --- | --- | --- | --- | --- | --- |
| ESA | Commercial use of images needs written authorization; CC BY-SA 3.0 IGO only where expressly labelled (search summary) | VWA | OL if labelled, else RR | RRR | RR |
| DLR | Main imprint: CC **BY-NC-ND 3.0 DE** where stated; some sub-portals CC BY 3.0; "Source: DLR" alone is not CC (search summary) | VWA | per label (BY → OL; BY-NC-ND or unlabelled → RR) | RRR | RR |
| CNES | Only a personal access right; "Tout autre droit est expressément exclu" (search summary) | VWA | RR | RR | RR |
| JAXA / ISAS web | JAXA keeps copyright; commercial use needs prior approval (search summary) | VWA | RR | RR | RR |
| JAXA Repository | Author keeps copyright; per-record licence field not seen | VWA | RRR | RRR | RRR |
| ISRO | Site material "may be reproduced free of charge without specific permission" with prominent acknowledgement (search summary) | VWA | VWA verbatim; RRR if modified | VWA | VWA |
| KARI | No page found; Korean public bodies use KOGL types 1–4 | VWA | UNKNOWN → RR | UNKNOWN | UNKNOWN |
| CNSA / CASC / AALPT | No page found | VWA | UNKNOWN → RR | UNKNOWN | UNKNOWN |
| Roscosmos, NPO Energomash, KBKhA, Kuznetsov | No terms page found; Civil Code Art. 1229 | VWA | RR | RR | RR |
| Yuzhnoye | "All rights reserved"; citing requires a link (seen on a staging subdomain) | VWA with link | RR | RR | RR |

### 3.5 Manufacturer datasheets and pages
L3Harris/Aerojet Rocketdyne, ArianeGroup, Safran, MHI, IHI, Moog, Northrop
Grumman, SpaceX, Rocket Lab, Blue Origin, Firefly: none of their terms pages
was retrieved; all carry "all rights reserved" footers [BK].
- Published performance numbers are facts: VWA, with URL, retrieval date and
  an archived snapshot — datasheets move (Aerojet Rocketdyne's moved to
  L3Harris) and are **re-rated in place** (Merlin 1D, BE-3U, Rutherford; see
  CONFLICT_LEDGER.md), so a value without a retrieval date is ambiguous.
- Photos, renders, cutaways, layout: RR. Tables: cite values, never mirror
  the layout.

### 3.6 Encyclopedic and web sources (Tier D–E)

| Source | values | figures | tables | text |
| --- | --- | --- | --- | --- |
| Wikipedia (text CC BY-SA 4.0 [BK]) | rights OK, **Tier D → re-source before shipping** | per file on Commons; en.wiki also hosts non-free images → RR | OL share-alike | OL CC BY-SA 4.0 |
| Wikimedia Commons | n/a | OL per file (trace to the original; uploader claims can be wrong) | n/a | n/a |
| Wikidata (CC0 [BK]) | OL, Tier D | n/a | OL | n/a |
| Astronautix, Space Launch Report, Spaceflight101 | RR (discovery; re-source values) | RR | RR | RR |
| Gunter's Space Page, Norbert Brügge (EU makers) | RR + **EU database right: no systematic extraction** | RR | RR | RR |
| RussianSpaceWeb | isolated facts VWA | RR | RR | RR |
| Forums (NASASpaceflight), scan hosts (epizodyspace, archive scans) | RRR (leads only; cite the original publication) | RRR | RRR | RR |
| AI-generated encyclopedias (e.g. "LLMpedia", seen in results) | **excluded** — not a source | — | — | — |

### 3.7 Books, papers, theses

| Source | values | figures | tables | text |
| --- | --- | --- | --- | --- |
| Sutton & Biblarz 9th ed. (Wiley 2017); Sutton, *History of LPRE* (AIAA 2006); Huzel & Huang 1992 (AIAA) | VWA for isolated facts; RRR for bulk | RR (many History figures are themselves manufacturer-supplied [BK]) | RR (compilation) | RR |
| AIAA papers, non-Government authors | VWA (isolated) | RR | RR | RR |
| AIAA papers, US-Government authors | PDG → VWA | PDG (redraw; avoid AIAA layout) | PDG | PDG (US only) |
| IAC / IAF papers | VWA (isolated) | RR | RR | RR |
| Theses | VWA | RRR (third-party figures inside them do not pass through) | RRR | RRR |
| Course notes (Stanford AA284a, uploaded lecture material) | RR (discovery) | RR | RR | RR |
| Jane's, Forecast International | MO (**contract terms override** the fact analysis) | MO | MO | MO |
| CPIA/JANNAF Liquid Propellant Manual | MO unless an item carries Dist A | MO | MO | MO |

## 4. Master matrix (source class × content kind)

| Source class | (a) values | (b) figures / schematic images | (c) tables as tables | (d) text |
| --- | --- | --- | --- | --- |
| NTRS, GOV_PUBLIC_USE_PERMITTED, NASA-employee author | PDG → VWA | PDG (drop insignia; third-party-credited → RRR) | PDG → VWA | PDG |
| NTRS SP/CR, contractor author | VWA | RRR until the NTRS field is checked | VWA | RRR |
| NTRS other determinations | VWA (isolated) / RRR (bulk) | RR | RR | RR |
| NASA History SPs (SP-4206 etc.) | PDG → VWA | PDG for NASA photos; contractor credits → RRR | PDG | PDG |
| DTIC Dist A, Government author | PDG → VWA | PDG | PDG | PDG |
| DTIC Dist A, contractor author | VWA | RRR | VWA / RRR (layout) | RRR |
| DTIC Dist B–F / export-controlled | MO | MO | MO | MO |
| US patent (no 1.71(e) notice) | VWA | VWA | VWA | VWA |
| Foreign patent | VWA | RRR | VWA | RRR |
| ESA | VWA | OL if labelled, else RR | RRR | RR |
| DLR | VWA | OL (CC BY) / RR | RRR | RR |
| CNES, JAXA web, Roscosmos, Energomash, KBKhA, Kuznetsov, Yuzhnoye | VWA | RR | RR | RR |
| JAXA Repository | VWA | RRR | RRR | RRR |
| ISRO | VWA | VWA verbatim / RRR modified | VWA | VWA |
| KARI, CNSA/CASC | VWA | UNKNOWN → RR | UNKNOWN | UNKNOWN |
| Manufacturer datasheet / web page | VWA (dated) | RR | VWA (values) / RR (layout) | RR |
| Wikipedia / Wikidata | OL, Tier D → do not ship unless re-sourced | per file | OL | OL |
| Personal encyclopedias (Astronautix, SLR, Gunter, Brügge) | RR; EU DB right for EU makers | RR | RR | RR |
| Textbooks | VWA isolated / RRR bulk | RR | RR | RR |
| AIAA / IAC papers, non-Government | VWA isolated | RR | RR | RR |
| Theses | VWA | RRR | RRR | RRR |
| Commercial databases | MO | MO | MO | MO |

**Ingestion rules for DB-1/DB-2:**
1. Ship **values** only from Tier A/B sources whose values column is PDG or VWA.
2. Never ship third-party **figures**.
3. Never mirror **tables** wholesale from RR sources.
4. Never copy **prose** except from PDG/OL sources (and honour attribution and
   share-alike for OL).
5. Tier D values may be rights-clean (Wikipedia) and still unshippable for
   **quality** reasons. Rights and science are separate gates.

## 5. Schematics and machine-readable topology

- A flow schematic in a copyrighted book or contractor report is a protected
  pictorial work. Copying, cropping or tracing it reproduces protected
  expression. Simplified diagrams in NASA-employee works are PDG.
- **Topology extraction** — recording as data that the fuel pump outlet feeds
  the regenerative jacket, which feeds the turbine inlet, then the injector —
  is most plausibly the extraction of facts and of a "system or method of
  operation" (17 USC 102(b); *Feist*), not of expression. RocketForge would
  render it in its own grammar (the `rf-propulsion-visual-grammar` skill:
  "real component topology for Engine Design").
- **Residual risks (legal review):**
  1. Reproducing a **distinctive layout** gives a derivative image even if the
     data are re-entered. Generate layout algorithmically; never place nodes
     from source coordinates.
  2. Systematic topology extraction from an EU maker's database (Brügge's
     schematics) may engage the sui generis right.
  3. Topology from export-controlled or Dist B–F documents may itself be
     controlled technical data.
  4. Contract terms (Jane's, subscriber-only sites) can forbid extraction.
- **Recommended labelling** for each topology record:
  `derived_from: [source_id + figure locator]`,
  `rights: ORIGINAL_DERIVED_TOPOLOGY`, `review_flag: true` until §7 is answered.

## 6. Rights status of the DB-0 registry itself

The registry in [data/sources.json](data/sources.json) records a `rights` class
per source, as the branch that found it judged it. Because no repository
copyright field or terms page was opened, every class is **provisional**. The
counts are in [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md). DB-0 ships **no
figure, no table and no prose** from any third-party source: the research
package contains only citations, factual extractions with locators, and
original prose.

## 7. Rights questions requiring legal review

1. **Contractor-authored NASA SPs and CRs.** With NTRS GOV_PUBLIC_USE_PERMITTED,
   may a third party redistribute their figures and text, or only the
   Government? Does FAR 52.227-14's licence to "distribute to the public"
   extend to downstream redistributors?
2. **NTRS `PUBLIC_USE_PERMITTED` vs `GOV_PUBLIC_USE_PERMITTED`.** Is commercial
   redistribution included?
3. **Non-US distribution of US-Government works.** RocketForge may ship outside
   the US.
4. **DTIC Dist A contractor reports**, and whether ingesting export-controlled
   technical data (even "public" engine details, especially Russian/Chinese
   military engines) is an ITAR/EAR issue.
5. **Bulk extraction from textbooks.** Where is the line between isolated facts
   and copying a protected compilation (Sutton tables, Huzel & Huang tables)?
6. **EU database right** for Gunter, Brügge, Leitenberger; is "discover, then
   re-source from Tier A" sufficient mitigation?
7. **Is RocketForge distribution "commercial"** under ESA, JAXA, CNES and DLR
   (BY-NC-ND) terms? If yes, nearly every agency image is excluded.
8. **ESA CC BY-SA 3.0 IGO**: does share-alike reach a RocketForge-rendered
   derivative?
9. **Algorithmically re-rendered topology** from copyrighted schematics — is it
   non-infringing?
10. **Wikipedia-derived data**: share-alike obligations if any CC BY-SA text or
    table is shipped.
11. **Scans of unclear provenance** (archive.org, epizodyspace, forums): may a
    value cite the scan, or must it cite the original document, with the scan
    only as an access route?
12. **Trademarks**: nominative use of engine names and agency insignia in UI
    and data.
