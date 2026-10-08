# DB-0 rights map: source classes and cross-cutting collections

Branch: `rights`. Companion file: `sources.json` (55 entries: about 25 policy/legal-basis sources and about 30 collections/classes).

**This is not legal advice.** It is a research map for engineering triage. Every "PUBLIC_DOMAIN_GOV" or "VALUES_WITH_ATTRIBUTION" call below is a working default, not a clearance. Section 7 lists the questions that need legal review.

---

## 0. Evidence quality: read this first

The session's network access was badly constrained:

- `WebFetch` failed with `getaddrinfo ENOTFOUND` for **every** host tried (ntrs.nasa.gov, sti.nasa.gov, nasa.gov, esa.int, en.wikipedia.org).
- `curl` through the egress proxy was refused with **CONNECT 403** (policy) for ntrs.nasa.gov, and for www.l3harris.com and www.spacelaunchreport.com (the proxy status log shows these). Every other probe also failed: astronautix, skyrocket.de, b14643.de, russianspaceweb, dtic, esa, jaxa, isro, eur-lex, copyright.gov, google and others.
- **WebSearch** worked for about 22 queries. After that, the shared per-turn search budget (200 calls across all agents) ran out.

What that means for the evidence:

- **No policy page was opened directly.** Every "quote" below comes from a search-engine result summary. These are marked *(search summary)*, and their exact wording must be re-verified before anyone relies on it.
- Statements marked **[BK]** come from my background knowledge and were **not verified** in this session.
- NTRS IDs: I record only the two I actually saw. They are **SP-8107 → 19750012398** and **SP-125 (2nd ed.) → 19710019929**. For the other SP-8000 monographs, the NTRS IDs and copyright-field values are **NOT_RETRIEVED**. I did not see the NTRS *copyright field* for SP-125, SP-8107 or SP-8089, or for any contractor report.

Access statuses in `sources.json` use `search_result_only`, `not_retrieved`, `paywalled` and `dead_link`. `dead_link` is used here only for hosts the egress policy blocked. It does **not** mean the site is down.

---

## 1. The two vocabularies

### RocketForge `ShippingPolicy`

Defined in `rocketforge/evidence/values.py:116`. Only `VALUES_WITH_ATTRIBUTION` lets a shipped record carry values. This is enforced by `SourceRecord.values_may_ship` in `rocketforge/evidence/records.py`.

| ShippingPolicy | Meaning in the code | Use in DB-0 |
|---|---|---|
| VALUES_WITH_ATTRIBUTION | A shipped record may carry values from the source, with a citation. | Gov public-domain sources; factual values from manufacturer pages; agencies that grant reproduction with attribution (ISRO). |
| METADATA_ONLY | Only the bibliographic record ships. | Commercial databases (Jane's, Forecast International); sources whose rights are still unknown. |
| RESTRICTED_REFERENCE | The source is cited, but none of its content ships. | Copyrighted books and papers, personal encyclopedic sites. |
| LICENSED_PROVIDER | Content arrives through a licensed provider at runtime (for example CEA or CoolProp). | Not applicable to engine-data sources. Reserve it. |
| RIGHTS_REVIEW_REQUIRED | Blocked until a human decides. | Contractor reports, JAXA-RR, archive.org scans, theses, ESA/DLR mixed regimes. |

### DB-0 rights classes (from the BRIEF)

The classes are: PUBLIC_DOMAIN_GOV, OPEN_LICENSE (with the licence named), VALUES_WITH_ATTRIBUTION, METADATA_ONLY, RESTRICTED_REFERENCE, RIGHTS_REVIEW_REQUIRED and UNKNOWN.

**Key point:** the code makes a single decision per source, through one `shipping` field. Rights differ by **content kind**, though. A Huzel & Huang 1992 thrust *value* is a fact. Its Fig. 4-3 schematic is a copyrighted image. A whole engine table may be a protected compilation. Its prose is plainly protected.

**Recommendation for the data model (proposal only; no code was changed):** carry a per-content-kind rights tuple at DB-0 research level, `{values, figures, tables, text}`. Then derive the single `ShippingPolicy` for the shipped evidence record from the **values** column only, because values are all that RocketForge ships today. Figures should never ship from DB-0 at all. A "topology" record that RocketForge draws itself is a new derived work. Section 6 covers it.

---

## 2. Legal principles (background; flagged for review)

1. **US: facts are not copyrightable.** *Feist v. Rural Telephone*, 499 U.S. 340 (1991) [BK]. A compilation is protected only in its original *selection, coordination or arrangement*; "sweat of the brow" gives no protection. 17 USC 102(b) excludes "any idea, procedure, process, system, method of operation" [BK].
   - Consequence: a thrust, chamber pressure or O/F value, or the *fact* that the fuel cools the nozzle before driving the turbine, can be stated with a citation even when it comes from a copyrighted book.
   - Copying a whole table, keeping its column choice and order, can copy protected selection and arrangement.
2. **US Government works.** 17 USC 105 says "Copyright protection under this title is not available for any work of the United States Government" (search summary of law.cornell.edu / govinfo).
   - This covers work by **officers and employees in the scope of their duties**. It does *not* automatically cover contractor or grantee work.
   - The protection is **US-only**. Other countries may still recognise US-Government copyright abroad [BK]. That matters if RocketForge is distributed outside the US.
3. **Contractor reports.**
   - Under FAR 52.227-14, a contractor may assert copyright in scientific and technical articles based on contract data without approval. Other data need Contracting Officer approval; Alternate IV grants blanket permission.
   - The Government receives a "paid-up, nonexclusive, irrevocable, worldwide license to reproduce, prepare derivative works, distribute to the public, and perform publicly and display publicly" (search summary of FAR 52.227-14 / 27.404-3).
   - Under 27.404-3, approval is normally *withheld* for "official agency or statutorily required reports" (search summary).
   - **Implication:** NASA CRs and Air Force/Army contractor reports may carry contractor copyright. The Government licence lets the Government distribute them. It does not obviously let RocketForge redistribute *figures or text*. Factual values are still facts.
4. **EU sui generis database right** (Directive 96/9/EC, Art. 7) [BK, eur-lex not reachable].
   - It protects the maker of a database who made a *substantial investment in obtaining, verification or presentation* of the contents.
   - It forbids extracting or re-using the whole or a *substantial part* of the contents, and Art. 7(5) adds *repeated and systematic* extraction of insubstantial parts.
   - The term is 15 years and renews with substantial new investment. The right exists only for makers who are EU nationals, residents or EU companies (Art. 11).
   - The CJEU (*BHB v William Hill*, C-203/02) held that investment in *creating* data does not count; investment in *collecting* existing data does.
   - **Implication:** Gunter's Space Page (Germany), Norbert Brügge (Germany) and Bernd Leitenberger (Germany) are plausibly protected databases even where each fact is free. **Do not systematically harvest them.** Use them to discover a lead, then source the value from a Tier A document. The UK has an equivalent right; the US has none.
5. **Japan:** Copyright Act exceptions for research and personal use exist. Art. 30-4 (data analysis) [BK] covers *analysis*, not redistribution.
6. **Russia:** Civil Code Part IV. Art. 1229, "absence of a prohibition shall not be deemed consent" (search summary via a ROSPHOTO secondary page). There is no fair-use doctrine; there are quotation exceptions [BK].
7. **Trademarks and insignia are separate from copyright.**
   - NASA Insignia ("meatball"), Logotype ("worm") and Seal: "may not be used for any purpose without explicit permission" and may not imply endorsement (search summary of the NASA logo-use page).
   - Crop or omit insignia from any image. Manufacturer engine names are trademarks: use them nominatively only.

---

## 3. Per-source-class findings with policy text

### 3.1 NASA NTRS / STI: PUBLIC_DOMAIN_GOV by default, with caveats

- **NTRS copyright field is structured.** The NASA STI OpenAPI Data Dictionary (06/2021, `https://sti.nasa.gov/docs/OpenAPI-Data-Dictionary-062021.pdf`; search summary) gives these enums:
  - `copyright.determinationType` ∈ {`NO_PERMISSION`, `MAY_INCLUDE_COPYRIGHT_MATERIAL`, `GOV_PERMITTED`, `GOV_PUBLIC_USE_PERMITTED`, `PUBLIC_USE_PERMITTED`, `OTHER`}
  - `copyright.licenseType` ∈ {`NO`, `OPEN_ACCESS`, `CCBY`, `CCBYSA`, `CCBYND`, `CCBYNC`, `CCBYNCSA`, `CCBYNCND`}
  - `copyright.thirdPartyContentCondition`: the example value is `NOT_SET`, and the full enum was not seen.
  - There is also a boolean `thirdPartyPermissionsProduced`.
  - The example record in the 2021/2022 OpenAPI docs reads `licenseType: "NO", determinationType: "PUBLIC_USE_PERMITTED", thirdPartyContentCondition: "NOT_SET"`.
- **UI label.** On the NASA Publications Guide record (NTRS 20150013303 / 20050189209), the Copyright row reads **"Work of the US Gov. Public Use Permitted."** and Distribution Limits reads "Public" (search summary).
  - The same label reportedly appears on a 1992 CR (contract NASW-4070) and on a 1964 University of Maryland grant paper.
  - So the label reflects NTRS's catalogue determination, **not** proof of Government authorship.
  - The labels "Public Use Permitted" (without "Work of the US Gov"), "Copyright" and "No copyright determination" were **not observed**. Their mapping below is inferred from the enum.
- **STI disclaimer** (`https://sti.nasa.gov/disclaimers/`; search summary): federal-employee works lack US copyright, and NASA does not require permission to use them. **But** government works can contain privately created copyrighted material, such as a quote, photo, chart or drawing, used under licence. An archived older notice said documents "may include portions contributed by private companies… other parties may retain all rights".
- **Media guidelines** (`https://nasa.gov/nasa-brand-center/images-and-media`; search summary):
  - NASA content is "generally not subject to copyright in the U.S." and may be used for educational and informational purposes without explicit permission.
  - It must not imply endorsement.
  - Identifiable people raise publicity-right issues.
  - Third-party imagery on NASA sites may be copyrighted.

**Mapping NTRS `determinationType` to DB-0 rights (proposed, per document):**

| determinationType (UI label) | values | figures | tables | text |
|---|---|---|---|---|
| GOV_PUBLIC_USE_PERMITTED ("Work of the US Gov. Public Use Permitted") | PUBLIC_DOMAIN_GOV → VALUES_WITH_ATTRIBUTION | PUBLIC_DOMAIN_GOV unless the caption credits a third party / contractor → RIGHTS_REVIEW_REQUIRED for that figure | PUBLIC_DOMAIN_GOV | PUBLIC_DOMAIN_GOV |
| PUBLIC_USE_PERMITTED (not Gov work, but public use permitted) | VALUES_WITH_ATTRIBUTION | RIGHTS_REVIEW_REQUIRED (the scope of "public use" is undefined) | VALUES_WITH_ATTRIBUTION | RIGHTS_REVIEW_REQUIRED |
| GOV_PERMITTED (Government use only) | VALUES_WITH_ATTRIBUTION (facts) | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| MAY_INCLUDE_COPYRIGHT_MATERIAL | VALUES_WITH_ATTRIBUTION | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED |
| NO_PERMISSION ("Copyright") | VALUES_WITH_ATTRIBUTION (facts only; bulk → review) | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| OTHER / field absent ("no determination") | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED |
| licenseType = CC* | OPEN_LICENSE (that licence) for all four columns, and the licence terms govern | | | |

**Action for whoever has NTRS access:** record `copyright.determinationType`, `licenseType` and `thirdPartyContentCondition` *verbatim* into `rights_statement` for each NTRS source. `SourceRecord.rights_statement` is documented as "Rights as the source or its repository states them. Not inferred". Do not record a guess there.

**SP-8000 monographs, SP-125, CRs.**
- Many SP-8000 liquid monographs were *written by contractor engineers* (Rocketdyne, Aerojet, Pratt & Whitney) under NASA contract and published by NASA as SPs [BK].
- SP-125 (1967 / 1971) is credited on NTRS to Dieter K. Huzel of North American Aviation, Los Angeles, and David H. Huang (search summary).
- As NASA-published SPs they are very likely catalogued GOV_PUBLIC_USE_PERMITTED. That is **unverified**: the copyright field was not seen.
- Contractor authorship is the reason to keep **figures** at RIGHTS_REVIEW_REQUIRED until the per-record field is checked. Values ship freely.
- The 1992 AIAA edition, *Modern Engineering for Design of Liquid-Propellant Rocket Engines* (PAA v.147, rev. Arbit), is a **separate AIAA-copyright work**: RESTRICTED_REFERENCE. Some library catalogues also file it under "SP-125". Do not conflate the two.
- NATO RTO-EN-AVT-150-05 reproduces an SP-8107 cycle diagram (search summary). SP-8000 figures circulate widely, which is not itself a rights clearance.

### 3.2 DTIC and US Air Force/Army reports

- DoDI 5230.24, reissued 10 Jan 2023. DTIC *Guide to Marking Documents 2023* (search summary):
  - **A** "Approved for public release: distribution is unlimited"
  - **B** US Gov agencies only
  - **C** US Gov agencies and their contractors
  - **D** DoD and US DoD contractors only
  - **E** DoD components only (1987 wording)
  - **F** further dissemination only as directed by the controlling office (1987 wording)
- Statement A may be used only on unclassified documents cleared by competent authority. The export-control warning is a separate marking (para 4.3.e).
- **Distribution A is a *release* decision, not a copyright decision.** An Air Force Rocket Propulsion Laboratory report written by Aerojet or Rocketdyne staff can be Dist A *and* contractor-copyrighted. DFARS 252.227-7013 governs [BK].

Mapping:

| Case | Rights class |
|---|---|
| Dist A + Gov-employee author | PUBLIC_DOMAIN_GOV in all columns |
| Dist A + contractor author | values VALUES_WITH_ATTRIBUTION; figures, tables and text RIGHTS_REVIEW_REQUIRED |
| Dist B–F, or any export-control warning | **Do not ingest**: METADATA_ONLY at most. Even holding the content may raise ITAR/EAR issues; that is a legal question. |

### 3.3 Patents

- **US patents.** The text and drawings are generally treated as free of copyright. The exception is when the specification carries the 37 CFR 1.71(e) authorisation language and the drawing carries a notice under 1.84(s) (search summary).
  - Check each patent for that language.
  - Cite the USPTO document number, not the Google Patents rendering.
  - Default mapping: PUBLIC_DOMAIN_GOV-like (strictly, "no copyright asserted"). Values, figures, tables and text: VALUES_WITH_ATTRIBUTION; figures are fine after the check.
- **Foreign patents (EPO, WIPO, JPO, CNIPA):** not verified this session.
  - [BK] EPO publications are generally reusable, and EPO data terms allow reproduction with attribution. WIPO PATENTSCOPE content is reusable, but WIPO site terms apply. JPO / J-PlatPat and CNIPA terms are unknown.
  - Several national laws (Germany §5 UrhG "amtliche Werke" is debated for patent specifications) do not clearly place the *applicant's* drawings in the public domain.
  - Mapping: values VALUES_WITH_ATTRIBUTION; figures RIGHTS_REVIEW_REQUIRED.

### 3.4 Other agencies

| Agency | What was found (search summary unless marked) | Values | Figures/images | Tables | Text |
|---|---|---|---|---|---|
| **ESA** | Images and videos are for education/editorial/information use; commercial use needs written authorisation. Ownership may be ESA, joint or third-party as credited. *Some* items are expressly CC BY-SA 3.0 IGO (credit e.g. "ESA/DLR/FU Berlin, CC BY-SA 3.0 IGO"), and CC applies only where expressly stated. The "ESA Standard Licence" phrase was **not found** in results. | VALUES_WITH_ATTRIBUTION | OPEN_LICENSE (CC BY-SA 3.0 IGO) **only if the item is labelled**; else RESTRICTED_REFERENCE | RIGHTS_REVIEW_REQUIRED | RESTRICTED_REFERENCE |
| **DLR** | Main imprint: where expressly stated, CC **BY-NC-ND 3.0 DE**. Some subportals (geoservice, AI-core, atmos) use CC BY 3.0. Material credited only "Source: DLR" is **not** CC-licensed. The task premise "CC BY 3.0" is only partly right. | VALUES_WITH_ATTRIBUTION | per label: BY-NC-ND → RESTRICTED_REFERENCE (no derivatives/commercial use); BY → OPEN_LICENSE; unlabelled → RESTRICTED_REFERENCE | RIGHTS_REVIEW_REQUIRED | RESTRICTED_REFERENCE |
| **CNES** | "Tous droits de propriété intellectuelle … sont la propriété du CNES ou d'un tiers"; the only right granted is "un droit personnel, gratuit, non exclusif et non transférable d'accès et d'utilisation… Tout autre droit est expressément exclu." | VALUES_WITH_ATTRIBUTION | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| **JAXA / ISAS** | Copyrights belong to JAXA unless otherwise stated. Research, education and personal use fall under Japanese law exceptions; commercial use needs prior approval via JAXA Digital Archives. Attribution "Courtesy of JAXA". | VALUES_WITH_ATTRIBUTION | RESTRICTED_REFERENCE (RocketForge's commercial status, see Q7) | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| **JAXA Repository (JAXA-RR etc.)** | Deposit doesn't change copyright; the author keeps it, and JAXA receives public-transmission and e-reproduction rights. Record pages have a "ライセンス" field whose **values were not seen**. No CC BY confirmed. | VALUES_WITH_ATTRIBUTION | RIGHTS_REVIEW_REQUIRED (check the per-record licence field) | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED |
| **ISRO** | "Material featured on this site … may be reproduced free of charge without specific permission", subject to accurate reproduction, no derogatory or misleading context, and prominent acknowledgement of the source. Third-party material is excluded; no framing. | VALUES_WITH_ATTRIBUTION | VALUES_WITH_ATTRIBUTION (verbatim reproduction with acknowledgement; *modification* unclear → review if redrawn) | VALUES_WITH_ATTRIBUTION | VALUES_WITH_ATTRIBUTION |
| **KARI** | No policy page found. Korean public bodies use KOGL (공공누리) types 1–4 under Copyright Act Art. 24-2; KARI's own label was not seen. | VALUES_WITH_ATTRIBUTION | UNKNOWN | UNKNOWN | UNKNOWN |
| **CNSA / CASC** | Not found. Other PRC government sites require a source citation (注明来源) on reprint. | VALUES_WITH_ATTRIBUTION | UNKNOWN → treat RESTRICTED_REFERENCE | UNKNOWN | UNKNOWN |
| **Roscosmos** | No terms page found. Indirect evidence: a 2010 MK.ru report of Roscosmos objecting to copying without a link. Civil Code Art. 1229. | VALUES_WITH_ATTRIBUTION | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| **NPO Energomash** (engine.space) | No terms found. Gazeta.ru reported the company's own 2017 annual report had copied text from an amateur site, so provenance of the company's web text is itself uncertain. | VALUES_WITH_ATTRIBUTION | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| **Yuzhnoye** | Footer: "© Yuzhnoye State Design Office. 1995–2026. All rights reserved." and "When citing materials, link to the site is required." Seen on the test5 staging subdomain. | VALUES_WITH_ATTRIBUTION (with link) | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |

### 3.5 Manufacturer datasheets

This row covers L3Harris (ex-Aerojet Rocketdyne), ArianeGroup, MHI, IHI, Moog, Northrop Grumman, SpaceX, Rocket Lab and Blue Origin.

None of their terms pages were retrieved; l3harris.com was proxy-denied. [BK] All carry "all rights reserved" footers.

- **Published performance numbers are facts.** Ship them as VALUES_WITH_ATTRIBUTION with the URL, retrieval date and a Wayback snapshot, because datasheets move. Aerojet Rocketdyne's datasheets moved after the L3Harris acquisition [BK].
- Photos, renders, cutaways and datasheet layout: RESTRICTED_REFERENCE.
- Tables: cite individual values; don't mirror the layout.
- Text: RESTRICTED_REFERENCE.

### 3.6 Encyclopedic / web (Tier D–E)

| Source | Basis | Values | Figures | Tables | Text |
|---|---|---|---|---|---|
| Wikipedia | Text CC BY-SA 4.0 (+GFDL legacy) [BK, not re-verified]. Images are licensed individually; en.wiki hosts *non-free fair-use* images. | Facts free, **but Tier D**: re-source before shipping. Rights-wise VALUES_WITH_ATTRIBUTION. | OPEN_LICENSE only per-file, verified on Commons; non-free → RESTRICTED_REFERENCE | OPEN_LICENSE (CC BY-SA 4.0; a copied table is a derivative → share-alike) | OPEN_LICENSE (CC BY-SA 4.0) |
| Wikimedia Commons | Per-file licence [BK]. Uploader claims can be wrong; trace to the original (e.g. a NASA source). | n/a | OPEN_LICENSE (named per file) / PUBLIC_DOMAIN_GOV for verified PD-USGov | n/a | n/a |
| Wikidata | CC0 [BK] | OPEN_LICENSE (CC0), Tier D | n/a | OPEN_LICENSE | n/a |
| Astronautix (Mark Wade) | Personal site, no open licence known [BK]; host unreachable. Hosts many third-party images. | discovery only → RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| Gunter's Space Page (G. D. Krebs, DE) | © author [BK]; **EU database right plausible** | discovery only; no systematic extraction | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| Norbert Brügge (DE) | © author [BK]; **EU database right plausible**; drawings are the author's own | discovery only; no systematic extraction | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| RussianSpaceWeb (A. Zak) | © author; a site_info page exists (URL seen, not read); partly subscriber-only [BK] | facts citable | RESTRICTED_REFERENCE (original artwork) | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| Space Launch Report (E. Kyle) | © author [BK]; proxy-denied | discovery | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| Spaceflight101 | Commercial news site; intermittently offline [BK] | discovery | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE | RESTRICTED_REFERENCE |
| NASASpaceflight forum | User copyright; attachments are often third-party (some leaked or limited-distribution) | leads only | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED | RESTRICTED_REFERENCE |
| epizodyspace.ru | Hosts scans of Russian books and journals with unknown authorisation (seen in results) | cite the *original* publication | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED | RIGHTS_REVIEW_REQUIRED |
| Forecast International, Jane's | Commercial subscription. **Contract terms override the fact/copyright analysis.** | METADATA_ONLY | METADATA_ONLY | METADATA_ONLY | METADATA_ONLY |

### 3.7 Books, papers, theses

- **Sutton & Biblarz, *Rocket Propulsion Elements* 9th ed. (Wiley 2017); Sutton, *History of Liquid Propellant Rocket Engines* (AIAA 2006); Huzel & Huang 1992 (AIAA).** All three are RESTRICTED_REFERENCE.
  - Individual values with a citation are VALUES_WITH_ATTRIBUTION (Feist), provided we extract **non-substantial, non-systematic** subsets and do not mirror table structure.
  - Figures are never reproduced. Many figures in Sutton's History are themselves manufacturer-supplied by permission [BK].
- **AIAA papers.** AIAA copyright by default. [BK] Papers by US Government employees carry a statement that the work is a US Government work not subject to US copyright; those are PUBLIC_DOMAIN_GOV in the US.
  - AIAA's typography and layout of the PDF are still AIAA's, so redraw rather than crop.
  - Many such papers are also on NTRS with their own determination; prefer the NTRS copy.
- **Stanford AA284a notes, other course notes.** Author copyright, and they reproduce textbook figures. RESTRICTED_REFERENCE; discovery only.
- **University theses.** Author copyright by default; some carry CC licences per item. A thesis's own reuse of third-party figures under fair use or quotation **does not pass through** to us. RIGHTS_REVIEW_REQUIRED, and values VALUES_WITH_ATTRIBUTION.
- **CPIA/JANNAF Liquid Propellant Manual and JANNAF proceedings.** Distribution-limited or export-controlled [BK]. RESTRICTED_REFERENCE; do not ingest unless an item carries Dist A.

---

## 4. Master matrix: source class × content kind

Each cell reads `DB-0 class → ShippingPolicy`. VWA = VALUES_WITH_ATTRIBUTION, RR = RESTRICTED_REFERENCE, RRR = RIGHTS_REVIEW_REQUIRED, MO = METADATA_ONLY, PDG = PUBLIC_DOMAIN_GOV, OL = OPEN_LICENSE.

| Source class | (a) factual values | (b) figures / schematics images | (c) tables (as tables) | (d) text |
|---|---|---|---|---|
| NTRS, GOV_PUBLIC_USE_PERMITTED, NASA-employee author | PDG → VWA | PDG → (n/a: RF ships no images) PDG; drop insignia; third-party-credited figure → RRR | PDG → VWA | PDG |
| NTRS SP/CR, contractor author (SP-8000, SP-125, CRs) | PDG/VWA → VWA | RRR until the NTRS field is checked; then PDG if GOV_PUBLIC_USE_PERMITTED | VWA | RRR |
| NTRS, NO_PERMISSION / MAY_INCLUDE_COPYRIGHT / OTHER / blank | VWA (non-bulk) / RRR (bulk) | RR | RR | RR |
| NASA History SPs (SP-4206, SP-4221) | PDG → VWA | PDG for NASA photos; contractor-credited photos → RRR | PDG → VWA | PDG |
| NASA web images | PDG → VWA | PDG, minus insignia, people, third-party credits | n/a | PDG |
| DTIC Dist A, Gov author | PDG → VWA | PDG | PDG → VWA | PDG |
| DTIC Dist A, contractor author | VWA | RRR | VWA (values) / RRR (layout) | RRR |
| DTIC Dist B–F / export-controlled | MO | MO | MO | MO |
| US patent (no 1.71(e) notice) | PDG-like → VWA | VWA (figure reuse OK) | VWA | VWA |
| Foreign patent | VWA | RRR | VWA | RRR |
| ESA | VWA | OL (CC BY-SA 3.0 IGO) if labelled; else RR | RRR | RR |
| DLR | VWA | OL (CC BY 3.0) / RR (BY-NC-ND, or unlabelled) | RRR | RR |
| CNES | VWA | RR | RR | RR |
| JAXA web | VWA | RR | RR | RR |
| JAXA Repository | VWA | RRR | RRR | RRR |
| ISRO | VWA | VWA (verbatim + acknowledgement) / RRR (modified) | VWA | VWA |
| KARI, CNSA/CASC | VWA | UNKNOWN → RR | UNKNOWN | UNKNOWN |
| Roscosmos, Energomash, Yuzhnoye | VWA | RR | RR | RR |
| Manufacturer datasheet | VWA | RR | VWA (values) / RR (layout) | RR |
| Wikipedia | OL CC BY-SA 4.0, Tier D → do not ship unless re-sourced | per file (OL / RR) | OL (share-alike) | OL CC BY-SA 4.0 |
| Wikimedia Commons | n/a | OL (per file) | n/a | n/a |
| Wikidata | OL CC0 (Tier D) | n/a | OL | n/a |
| Astronautix, Space Launch Report, Spaceflight101 | RR (discovery; re-source values) | RR | RR | RR |
| Gunter, Brügge (EU makers) | RR + **EU DB right: no systematic extraction** | RR | RR | RR |
| RussianSpaceWeb | VWA (isolated facts) / RR | RR | RR | RR |
| Forums, scan-hosting sites | RRR (leads only) | RRR | RRR | RR |
| Textbooks (Sutton, Huzel & Huang 1992, Sutton History) | VWA for isolated facts; RRR for bulk | RR | RR (compilation) | RR |
| AIAA papers, non-Gov author | VWA (isolated) | RR | RR | RR |
| AIAA papers, US-Gov author | PDG → VWA | PDG (redraw; avoid AIAA layout) | PDG → VWA | PDG (US only) |
| Theses | VWA | RRR | RRR | RRR |
| Course notes (Stanford AA284a) | RR (discovery) | RR | RR | RR |
| Jane's, Forecast International | MO | MO | MO | MO |
| CPIA/JANNAF LPM | MO (unless Dist A) | MO | MO | MO |
| CEA / CoolProp provider data | LICENSED_PROVIDER (existing use; out of DB-0 scope) | — | — | — |

**One-line rule set for DB-0 ingestion:**
1. Ship **values** only from Tier A/B sources whose values column is PDG or VWA.
2. Never ship third-party **figures**.
3. Never mirror **tables** wholesale from RR sources.
4. Never copy **prose** except from PDG/OL sources (and for OL, honour attribution and share-alike).

---

## 5. Cross-cutting collections registry (summary; details in `sources.json`)

| source_id | Collection | Rights | Access this session |
|---|---|---|---|
| SRC-NASA-SP8000-LRE | NASA SP-8000 liquid-rocket monographs (23 members listed) | PDG (provisional) | search_result_only. **Only SP-8107 = NTRS 19750012398 seen**; SP-8109 and SP-8121 mentioned as on NTRS (no ID); the other 20 numbers/titles are [BK], unverified |
| SRC-NASA-SP8107 | Turbopump systems for liquid rocket engines (1974) | PDG (field not seen) | search_result_only |
| SRC-NASA-SP125 | Huzel & Huang, Design of LPRE, 2nd ed. 1971 (1st 1967) | PDG (contractor authors; field not seen) | search_result_only (NTRS 19710019929) |
| SRC-AIAA-HUZELHUANG-1992 | AIAA PAA v.147 | RR | search_result_only |
| SRC-AIAA-SUTTON-HISTORY | Sutton, History of LPRE (2006) | RR | not_retrieved |
| SRC-WILEY-SUTTON-9ED | Rocket Propulsion Elements 9e | RR | not_retrieved |
| SRC-NASA-SP4206 | Stages to Saturn (Bilstein 1980) | PDG | not_retrieved |
| SRC-NASA-SP4221 | The Space Shuttle Decision (Heppenheimer 1999) | PDG | not_retrieved |
| SRC-NASA-APOLLO-EXP-REPORTS | Apollo Experience Reports (TN D series) | PDG | not_retrieved |
| SRC-ROCKETDYNE-MANUALS-DIGITIZED | F-1/J-2/H-1 manuals, digitized copies | RRR | not_retrieved |
| SRC-DTIC-COLLECTION | DTIC technical reports | per document | blocked by egress policy |
| SRC-JAXA-REPOSITORY | JAXA-RR/AIREX | RRR | search_result_only |
| SRC-WIKIPEDIA / -COMMONS / -WIKIDATA | Wikimedia | OL | not_retrieved |
| SRC-ASTRONAUTIX, SRC-GUNTER, SRC-BRUEGGE, SRC-SPACELAUNCHREPORT | personal encyclopedias | RR | blocked |
| SRC-RUSSIANSPACEWEB | Zak | RR | search_result_only |
| SRC-SPACEFLIGHT101, SRC-NSF-FORUM, SRC-EPIZODYSPACE | web | RR / RRR | not_retrieved / search_result_only |
| SRC-FORECAST-INTL, SRC-JANES | commercial | RR → MO | paywalled |
| SRC-CPIA-JANNAF-LPM | restricted handbook | RR → MO | not_retrieved |
| SRC-NATO-RTO-EN-AVT-150-05 | NATO lecture (reuses an SP-8107 figure) | RRR | search_result_only |
| SRC-PATENT-US5197851 | example US patent citing SP-8107 pp. 53–55 | PDG-like | search_result_only |
| SRC-MFR-DATASHEETS, SRC-AIAA-PAPERS, SRC-UNIV-THESES, SRC-STANFORD-AA284A, SRC-PURDUE-ZUCROW | classes | see matrix | not_retrieved |

Not covered at all (budget exhausted): Kuznetsov / ODK-Kuznetsov site, NASA "Liquid Rocket Engine Data" compendia, the Rocketdyne "Engine Data Book", "Encyclopedia of propellants", third-party "LRE database" compilations, and Bernd Leitenberger. These need a follow-up pass.

---

## 6. Schematics and "original machine-readable topology"

- **Figure redistribution.** A flow schematic in a copyrighted book or contractor report is a protected pictorial work. Copying, cropping or tracing it closely reproduces protected expression. Simplified cycle diagrams in NASA-employee works are PDG.
- **Topology extraction.** This means recording, as data, that the fuel pump outlet feeds the regenerative jacket, which feeds the turbine inlet, then the injector. It is most plausibly the extraction of **facts / a system or method of operation** (17 USC 102(b); Feist), not of expression. RocketForge then renders the topology with *its own* drawing grammar. Per the `rf-propulsion-visual-grammar` skill, schematics show "real component topology for Engine Design".
- **Residual risks, which need legal review:**
  1. Reproducing a *distinctive layout* (component placement, line routing, symbol choices) gives a derivative image even if the data are re-entered. So generate the layout algorithmically and never place nodes from the source coordinates.
  2. Systematic extraction of topologies from an EU-maker database (Brügge's schematics) may engage the sui generis right even though each topology is a fact.
  3. Topology from export-controlled or Dist B–F documents. The facts may themselves be controlled technical data (ITAR/EAR), so copyright is not the only issue.
  4. Contractual terms (Jane's, Forecast International, subscriber-only RussianSpaceWeb) can forbid extraction regardless of copyright.
- **Recommended labelling:** a topology record should carry `derived_from: [source_id + figure locator]` and `rights: "ORIGINAL_DERIVED_TOPOLOGY (facts extracted; rendering original)"`. It should keep a `review_flag: true` until the questions in section 7 are answered.

---

## 7. Rights questions requiring legal review

1. **NASA contractor-authored SPs and CRs** (SP-8000 series, SP-125, NASA CRs). With NTRS GOV_PUBLIC_USE_PERMITTED, may a third party redistribute their *figures* and *text*, or only the Government? Does FAR 52.227-14's licence "to distribute to the public" extend to downstream redistributors?
2. **Meaning of NTRS `PUBLIC_USE_PERMITTED` versus `GOV_PUBLIC_USE_PERMITTED`.** Is commercial redistribution included? NASA has published no definition that we found.
3. **Non-US distribution of US-Government works.** RocketForge may ship outside the US.
4. **DTIC Dist A contractor reports.** Is there contractor copyright in practice? Separately, is ingesting any export-controlled technical data (even "public" engine details) an ITAR/EAR issue? This applies especially to Dist B–F and to Russian/Chinese military engine data.
5. **Bulk extraction of values from copyrighted textbooks.** Where is the threshold between "isolated facts" and copying a protected compilation (Sutton tables, Huzel & Huang tables)?
6. **EU sui generis database right.** Does it apply to Gunter's Space Page, Norbert Brügge and Leitenberger? Is "discovery then re-source from Tier A" sufficient mitigation?
7. **RocketForge's commercial status.** Is RocketForge distribution "commercial" under the ESA, JAXA, CNES and DLR (BY-NC-ND) terms? If yes, nearly all agency images are excluded.
8. **ESA CC BY-SA 3.0 IGO items.** Does share-alike contaminate a RocketForge-rendered derivative? (It should not if we do not ship the image.)
9. **Algorithmically re-rendered topology** from copyrighted schematics: is it non-infringing (section 6)?
10. **Wikipedia-derived data.** If any CC BY-SA text or tables are shipped, share-alike obligations apply to that part.
11. **Archive.org / epizodyspace / forum-hosted scans** of manuals of unclear provenance. Can a value cite such a scan, or must we cite the original document and record the scan only as an access route?
12. **Trademarks.** NASA insignia, and engine names that are registered marks: confirm that nominative use in the UI and data is acceptable.

---

## 8. Recommended next steps (for an orchestrator with network access)

1. With NTRS reachable, call `GET https://ntrs.nasa.gov/api/citations/search?q=...` for each SP-8000 number. Record `id`, `reportNumber` and the full `copyright` object verbatim, and fill `members[].verification` in `SRC-NASA-SP8000-LRE`.
2. Fetch and quote: `sti.nasa.gov/disclaimers`, `nasa.gov/nasa-brand-center/images-and-media`, the ESA Terms_and_Conditions page, the DLR imprint, `global.jaxa.jp/policy.html`, `isro.gov.in/Copyright_Policy.html`, `cnes.fr/mentions-legales`, the Wikipedia:Copyrights page, astronautix/skyrocket/b14643 footers, and `russianspaceweb.com/site_info.html`. Replace every *(search summary)* above with verbatim text.
3. Add per-content-kind rights fields to DB-0 source records (section 1 proposal). Keep the shipped `ShippingPolicy` derived from the values column.
