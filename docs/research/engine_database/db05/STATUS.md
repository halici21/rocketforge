# DB-0.5 — status: PARTIAL (opened-source pass, session 2026-10-08)

The previous session was blocked by network policy. In this session the NTRS
citation API answered (HTTP 200 for `ntrs.nasa.gov/api/citations/19950022693`),
so the P0 queue in `work_queue.json` was worked from the top. Every record in
this folder comes from a document that was downloaded and read page by page,
with figures rendered and viewed. Search summaries were used only to find
documents, never as evidence.

DB-0.5 is **PARTIAL**, not complete: every priority anchor has opened-source
evidence, but DTIC (all AEDC J-2/J-2S test reports and the IPD engine papers)
refused access, no manufacturer RD-170 document was available, and the P0
queue still holds unread items (Rutherford, LR87, RS-68A were not started).

## What was done

| Measure | Count | Where |
| --- | --- | --- |
| Access records (every source attempted) | 94 | `documents_opened.json` |
| Documents read and mined (page-level locators) | 30 (Tier A 27, Tier B 3) | `documents_opened.json`, `read_level = READ_AND_MINED` |
| Documents whose identity was verified but not mined | 11 | `IDENTITY_VERIFIED_ONLY` |
| Downloaded, not read this session | 21 | `FETCHED_NOT_READ` (not evidence) |
| Reached, but no evidence on the page | 3 | `FETCHED_NOT_EVIDENCE` |
| Access blocked | 29 | `ACCESS_BLOCKED`, reason per record |
| Assertion records | 250 | `assertions.json` |
| Assertions promoted (value as printed + locator) | 248 | 219 REPORTED, 28 DIGITISED from viewed schematics, 1 INFERRED |
| Assertions rejected / not promoted | 2 (both REPORTED) | stale-text value; model-tuning parameter |
| DB-0 anchor assertions re-checked | 172 | `db0_dispositions.json` |
| Schematics actually viewed | 15 | `schematics_viewed.json` |
| Verified topology graphs | 9 | `topology/*.json` |
| Conflict outcomes | 29 records: 30 DB-0 conflict ids addressed (25 of the 36 P0), 5 new conflicts | `conflicts.json` |
| Regression candidates | 5 | `regression_candidates.json` |

Four new sources were added to `data/sources.json` (`SRC-DB05-*`): the Saturn V
Flight Manual SA-503 (MSFC-MAN-503), the Rocketdyne F-1 history chapter and
viewgraphs (NTRS 20100027316), the 1993 J-2S Restart Study (NTRS 19940016798)
and the 1985 OMS design-evolution paper (NTRS 19850008634). Sources that were
read now carry `access = fetched`; sources that could not be reached carry
`access = not_retrieved`.

## Anchors

| Anchor (engine id used) | Key opened sources | Schematic viewed | Topology |
| --- | --- | --- | --- |
| RS-25 Block II (`ENG-US-SSME-BLOCK-II`) and Block IIA (`…-BLOCK-IIA`) | L3Harris L26301; NASA FS-2015/FS-2025; JSC-19041 Rev F; Rocketdyne BC98-04; AIAA 2002-3581; NTRS 19860012108, 20180006338; HAER TX-116 | JSC-19041 Fig. 1.1-II; AIAA 97-2687 Fig. 1; BC98-04 slide 19 | Block IIA, 31 nodes / 42 edges |
| J-2 (`ENG-US-J-2`) | NTRS 20100027318 (Coffman + viewgraphs); MSFC-MAN-503; NTRS 20120016414 | Coffman slide J2-4; MSFC-MAN-503 Fig. 5-7 | 22 / 28 |
| J-2S (`ENG-US-J-2S`) | J-2S Restart Study (NAS8-39210, 1993); NTRS 20120016414, 20080036837 | — (timeline slide only) | — |
| F-1 (`ENG-US-F-1`) | NTRS 20100027316 (Biggs + viewgraphs); MSFC-MAN-503 | Biggs slide 'F-1 Engine Schematic' | 16 / 22 |
| H-1 (`ENG-US-H-1-188K`) | SDES-64-415 Vol. VIII (SA-10, July 1964) | Fig. 3-1 mechanical schematic | 19 / 25 |
| RL10 (`…-RL10A-3-3A`, `…-RL10A-4-2`, `…-RL10B-2`) | NASA CR-195478; NTRS 19910018888; NRC 2006 (NAP 11780); ULA documents | CR-195478 Fig. 1 | RL10A-3-3A, 19 / 23 |
| AJ10-137 / Apollo SPS (`ENG-US-AJ10-137`) | NASA TN D-7375; NTRS 20100027319 | TN D-7375 Fig. 2 | 16 / 16 (stage + engine) |
| LM Descent Engine (`ENG-US-LMDE`) | NASA TN D-7143 | TN D-7143 Figs. 3, 6, 7 | 17 / 21 |
| AJ10-190 / Shuttle OMS (`ENG-US-AJ10-190`) | USA006500 (OMS 21002); JSC-19950; NTRS 19850008634 | USA006500 Figs. 2-1, 2-10 | 16 / 20 |
| IPD (`ENG-US-IPD`) | NTRS 20040084662 (Stennis facility paper) | none reachable (DTIC 403) | — |
| RD-170 (`ENG-SU-RD-170`) | NTRS 19910018906 (Rockwell 1990 briefing, re-graded Tier B) | Rockwell reconstruction p.569 | 9 / 13, **third-party reconstruction** |

## Findings that change DB-0

- **Variant scoping matters more than DB-0 assumed.** The Rocketdyne flow
  schematic with pump speeds and state points is Block IIA, not Block II; the
  Apollo SPS 21,500 lb / 102 psia / 309 s values sit under TN D-7375's
  *Block I* heading; the H-1 values are the SA-10 188K engine. All are
  attached to the matching configuration, not the anchor.
- **Corrected DB-0 values:** HPFTP power is printed 71,140 hp (L3Harris) and
  69,000 hp (NTRS 20180006338), not 76,000 hp; FPOV/OPOV roles: the OPOV is
  driven *with* the FPOV to change thrust, not alone; the "≈30,000 rpm HPOT"
  figure is the maximum allowable shutdown speed, not an operating speed;
  F-1 sea-level Isp is printed 265.4 s; J-2 Pc is 717 psia at nozzle
  stagnation (763 psi is unsupported); OMS Isp is 313 s (316 s unsupported).
- **Upgraded evidence:** J-2S tap-off cycle (now Tier A), RL10 full expander
  and LOX-pump gearbox, H-1 gearbox (both previously "to verify").
- **Identity fixes:** JSC-19041, BC98-04, TN D-7143 and HAER TX-116 verified on
  the page; two DB-0 source pairs are the same file (TN D-7143 / AER-DPS,
  IPD-WPB / 20040084662); the SA-8/SA-10 SDES numbers are set numbers shared
  by all volumes.
- **Rights conflicts:** NTRS marks MSFC-MAN-503 and AIAA 97-2687 public use,
  but the pages print a restrictive notice and an AIAA copyright respectively;
  BC98-04 is stamped "BOEING PROPRIETARY" on every page. Rights are recorded
  per document as *checked statement*, not inferred.

## Regression candidates (`regression_candidates.json`)

Rule from SCHEMA_PROPOSAL §6: fetched, values usable with attribution, defined
operating point, no UNRESOLVED conflict on the fields used.

| Candidate | Fields | Note |
| --- | --- | --- |
| RL10A-3-3A nominal | thrust, Isp, Pc, O/F, ε | Pc station unstated |
| J-2S nominal | thrust, Isp, Pc (nozzle stagnation), MR, ε | |
| J-2 230K | thrust, Isp, Pc (nozzle stagnation), MR, ε | 225K rating also primary |
| RS-25 SLS at 109% | vacuum thrust, Isp, Pc, MR, ε | sea-level thrust excluded (unresolved) |
| Apollo SPS Block I | thrust, Isp (average), Pc, O/F, ε | Block I only |

Not candidates: F-1 (rating epoch unresolved), RL10B-2 (Pc/Isp conflict),
RL10A-4-2 (Tier B only), OMS and LMDE (MR/Pc not found), H-1 (no Pc/Isp/MR),
IPD (blocked), RD-170 (second-hand).

## Remaining access blockers

- `apps.dtic.mil` — HTTP 403 to every request: AEDC J-2 and J-2S altitude
  test reports, Apollo SPS altitude test, IPD papers (ADA397910, ADA430218).
- `wpafb.af.mil`, `generalstaff.org`, `mocat.library.unt.edu` — HTTP 403.
- `l3harris.com` RL10 and RS-68A data sheets and `aiaa.org` vehicle guides —
  HTTP 404 at every URL tried.
- `corpora.tika.apache.org` (Hopson STS-104 FRR) — connection failed.
- No URL in the registry for the F-1 and J-2 Rocketdyne manuals or the
  unidentified SSME preburner patent.

## Not done

Rutherford, LR87 and RS-68A anchors; 21 downloaded documents not read (Rocket
Lab pages, patents, enginehistory.org chapters, Apollo flight evaluations);
176 of the 206 DB-0 conflicts (11 of them P0). Two exploratory downloads (RL10A-3-3 design
report NTRS 19670005471; J-2 AS-501 flight analysis NTRS 19680026222) are leads
and are not registered.

## Reproducing

`tools/` holds the scripts that produced every file here: `fetch.py`
downloads and hashes (documents are **not** committed; set `DB05_CACHE`),
`ledger_*.py` hold each assertion with its locator as typed while reading,
`build.py` validates and emits the JSON and updates `data/sources.json`,
`candidates.py` applies the regression-candidate rule. Consistency is checked
by `tests/research/test_db05_research_artifacts.py`.

DB-1 Production Reference Engine Schema: implemented after this pass, see
`docs/engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md`. DB-1 uses
these files as design evidence and stress-test input only; they are not
production data.
DB-2 Production Engine Corpus: NOT STARTED.
LIQ-7 Pump Foundation: PAUSED.
