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
| Access records (every source attempted) | 109 | `documents_opened.json` |
| Documents read and mined (page-level locators) | 41 (Tier A 36, Tier B 5) | `documents_opened.json`, `read_level = READ_AND_MINED` |
| Documents whose identity was verified but not mined | 19 | `IDENTITY_VERIFIED_ONLY` |
| Downloaded, not read this session | 17 | `FETCHED_NOT_READ` (not evidence) |
| Reached, but no evidence on the page | 3 | `FETCHED_NOT_EVIDENCE` |
| Access blocked | 29 | `ACCESS_BLOCKED`, reason per record |
| Assertion records | 452 | `assertions.json` (250 from the 2026-10-08 pass + 11 DB-2A, 13 DB-2B Wave 1, 11 review supplement, 56 DB-2B Wave 2 and 111 DB-2B Wave 3 transcriptions, below) |
| Assertions promoted (value as printed + locator) | 339 | 310 REPORTED, 28 DIGITISED from viewed schematics, 1 INFERRED |
| Assertions rejected / not promoted | 2 (both REPORTED) | stale-text value; model-tuning parameter |
| DB-0 anchor assertions re-checked | 172 | `db0_dispositions.json` |
| Schematics actually viewed | 16 | `schematics_viewed.json` |
| Verified topology graphs | 10 | `topology/*.json` |
| Conflict outcomes | 32 records: 30 DB-0 conflict ids addressed (25 of the 36 P0), 8 new conflicts | `conflicts.json` |
| Regression candidates | 5 | `regression_candidates.json` |

Four new sources were added to `data/sources.json` (`SRC-DB05-*`): the Saturn V
Flight Manual SA-503 (MSFC-MAN-503), the Rocketdyne F-1 history chapter and
viewgraphs (NTRS 20100027316), the 1993 J-2S Restart Study (NTRS 19940016798)
and the 1985 OMS design-evolution paper (NTRS 19850008634). Sources that were
read now carry `access = fetched`; sources that could not be reached carry
`access = not_retrieved`.

**DB-2A supplement (2026-10-09).** Preparing the verified seed corpus
(`docs/engineering/design/DB2A_VERIFIED_REFERENCE_ENGINE_SEED_CORPUS.md`)
re-opened four documents already read here and transcribed eleven statements
this pass had left out: the "Description" block of the J-2 slide that carries
the 230,000 lb table (feed, propellants, turbine drive, chamber cooling,
turbopumps; NTRS 20100027318 PDF p.14), the cycle and propellants named in the
abstract of NASA CR-195478 (RL10A-3-3A), the 475 psia chamber pressure printed
in the same Pratt & Whitney "RL10A-3-3A ENGINE" table as the thrust and Isp
(NTRS 19910018888 PDF p.3), and the "pressure-fed" engine assembly sentence of
TN D-7375 (Block I). They are ordinary ledger entries
(`ledger_j2.py`, `ledger_rl10.py`, `ledger_sps.py`), REPORTED, with locators.
DB-0.5 stays PARTIAL.

**DB-2B Wave 1 supplement (2026-10-09).** Expanding the production corpus
(`docs/engineering/design/DB2B_WAVE1_VERIFIED_HISTORICAL_CORPUS.md`) re-read four
documents already opened here and transcribed thirteen statements: the
'Description' block of the J-2S viewgraph (feed, propellants, chamber cooling;
NTRS 19940016798 PDF p.9), the 'F-1 Engine Basic Features' viewgraph (feed,
propellants, gas-generator turbine drive; NTRS 20100027316 PDF p.16), the
propellants and liquid gas generator of the SA-10 H-1 (SDES-64-415 Vol. VIII
PDF pp.5-6), and the propellants of the current OMS (abstract of NTRS
19850008634). They are ordinary ledger entries (`ledger_j2.py`, `ledger_f1.py`,
`ledger_h1.py`, `ledger_oms.py`), REPORTED, with locators. DB-0.5 stays PARTIAL.

**Review supplement (2026-10-09).** The independent review of DB-2B Wave 1 found
that production graphs cited text passages no ledger entry recorded. Ten
passages, all from documents already read, were transcribed so that every
cited text basis is a ledger entry: five from Coffman (the J-2 start tank,
the heat exchanger for oxygen tank pressurization, the augmented spark igniter,
the gas generator driving the turbomachinery, the turbine exhaust dumped at the
2:1 tube split),
four from Biggs (the single turbine driving both pumps, the fuel path through
the chamber tubes, the hypergol cartridge, the igniter fuel valve) and the
'bolt-on aluminum injector' of the TN D-7375 Block I engine assembly. DB-0.5
stays PARTIAL.

**Owner-gate review supplement (2026-10-10).** The post-change review of the
owner-decision gates found that the SPS Block I 2:1 ratio's direction
(oxidizer-to-fuel) rested on a reading quoting a TN D-7375 p.3 sentence no
ledger entry held. That sentence was transcribed (AS-DB05-US-AJ10-137-025,
from the page already read). DB-0.5 stays PARTIAL.

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
| RS-25 SLS at 109% | vacuum thrust, Isp, Pc, MR, ε | sea-level thrust excluded (unresolved; owner kept it withheld 2026-10-30) |
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
and are not registered. (Both were read and registered on
2026-10-28; see the J-2 AS-501 and RL10A-3-3 supplements below.) On 2026-10-28 every remaining
`FETCHED_NOT_READ` download was read, so the count is now 0; see the
"Unread downloads closed" supplement below.

**DB-2B Wave 2 supplement (2026-10-10).** A narrow source-completion pass for the
seven Wave 2 targets only (RL10A-4-2, RL10B-2, RD-170, IPD, RS-68A, LR87,
Rutherford), in `tools/ledger_wave2.py`. Already-downloaded documents were read
first (the four Rocket Lab sources), then registered leads, then targeted
NTRS and web discovery; every new document was fetched by `fetch.py` (hash,
NTRS rights metadata) before it was read. 55 assertions were transcribed:

- RS-68A: NASA MSFC, Ares V and RS-68B (NTRS 20090014109) for the changes
  from the RS-68, and a NASA launch-day blog for identity and a 702,000 lb
  thrust with no environment; the manufacturer data sheet is still HTTP 404
  (new conflict CF-DB05-RS68A-THRUST against its DB-0 search excerpt).
- LR87AJ-11: the General Dynamics Convair Titan IIIE/Centaur D-1T systems
  summary (NTRS 19750004937): rated thrust, vacuum Isp, propellants, flows,
  expansion ratio, cycle and feed; Figure 6-20 viewed and transcribed as a
  graph of one subassembly (16 nodes, 18 edges). No other LR87 variant was
  supported by an opened document.
- IPD: the NGLT programme paper (NTRS 20050243602) and an IPD model paper
  (NTRS 20060004818); the DTIC and AFRL papers stay blocked, and two NTRS
  records are abstracts only.
- RD-170: a NASA MSFC CFD paper (NTRS 19950002748) describing the engine
  (four nozzles, regeneratively cooled, kerosene and liquid oxygen); no
  manufacturer document was reached.
- RL10B-2 and RL10A-4-2: the AIAA inaugural-launch paper (RL10B-2 propellants
  and nozzle) and a Lockheed Martin conference paper (RL10A-4 variant map;
  printed copyright). NASA's RL10 transition paper covers only the RL10A-3-3A/B.
- Rutherford: the four Rocket Lab sources (press kit 2017, releases of 2018
  and 2020, Electron page), all carrying a Rocket Lab copyright; two
  epoch conflicts recorded (CF-DB05-RUTHERFORD-SL-THRUST, -VAC-THRUST).

The rights wording of SRC-ULA-DIV-INAUGURAL was re-checked (all 9 pages) and
restated as a finding of no notice; the finding itself is unchanged.

The Wave 2 independent review corrected transcriptions: the RD-170
reconstruction graph (2026-10-08) was re-read against its figure (fuel line
labelled "FUEL", not RP-1; the LP fuel pump's return line rises from the kick
pump; no line joins the HP fuel pump and the kick pump, now an omission;
"turbine drive" not printed); the LR87AJ-11 turbine-to-pump edges are geared
drives (report p.6-23 'through a gear train'); the IPD contractor statement
keeps its printed "Currently,"; and the NGLT paper's 250k-lb-thrust goal was
added (AS-DB05-US-IPD-013). DB-0.5 stays PARTIAL.

**DB-2B Wave 3 supplement (2026-10-11).** A targeted pass for the Wave 3
targets only: LE-7, LE-7A, LE-9, Vulcain, Vulcain 2, Vinci, YF-75, YF-75D,
YF-100 and the conditional seventh target YF-77 (chosen from the DB-0
registry). Every document was downloaded and read; Japanese and Chinese
statements are recorded as printed, with a RocketForge reading gloss that is
not a translation source. Scanned or font-mangled pages were read from
rendered images (the NASDA 1997 scan, the IHI paper). 111 assertions
(`ledger_wave3.py`), 6 conflicts (LE-7 and LE-7A epochs, LE-9 thrust level,
Vulcain thrust and turbopumps, Vinci epoch), 1 schematic viewed (LE-9 cycle,
IHI技報 Fig. 2; not transcribed: restricted), 4 access blocks (EUCASS 403,
Safran 403, an ESA page 404, IAF 429). Two new sources: NTRS 19910018905
(a US panel's 1990 review of Japanese programmes) and the 2021 YF-100 paper
in 深空探测学报. Every Japanese, European and Chinese primary document opened
carries a copyright notice or restrictive host terms; the NASDA 1997 table on
mext.go.jp needs a rights review. After this pass the research files hold
61 documents read and mined, 30 identity-verified, 33 access-blocked,
4 fetched without evidence,
17 schematics viewed and 38 conflict outcomes. See
`docs/engineering/design/DB2B_WAVE3_JAPAN_EUROPE_CHINA_CORPUS.md`. DB-0.5
stays PARTIAL.

**F-1 rating-epoch supplement (2026-10-28).** A narrow pass on DB-0 conflict
CF-ORCH_VERIFY-1 (was the F-1 uprated between SA-503 and SA-504?), in
`tools/ledger_f1_rating.py`. The SA-503 manual was re-downloaded (same SHA-256)
and its "ENGINE DATA" table (p.1-6) viewed; the Apollo-9 (AS-504) Technical
Information Summary (MSFC R-ASTR-S-69-7, 3 Feb 1969; NTRS 19700009516) was
opened for the first time and its S-IC section viewed as images.

- The SA-503 manual already tabulates F-1 "NOMINAL THRUST EACH 1,522,000,
  TOTAL 7,610,000" (and J-2 228,000 for S-II, 203,000 for S-IVB). The AS-504
  summary's stage text gives the same 7,610,000 for five engines, while its
  Figure 19 keeps "1,500,000 lbs Thrust". The opened documents therefore do not
  support an uprate between SA-503 and SA-504 (CF-DB05-F1-RATING-EPOCH,
  PARTIALLY_RESOLVED): AS-501 and AS-502 are still not covered.
- Figure 19 prints "Mixture Ratio - LOX : RP-1 2.27:1", the direction the
  Rocketdyne slide's "Engine mixture ratio 2.27" lacked (CF-DB05-F1-MR-DIRECTION,
  RESOLVED). Shipping it for CFG-F1 is an owner decision; it is withheld.
- Figure 19 also prints "Thrust Chamber Pressure 1105 psia" against the shipped
  1,125 psia (owner decision of 2026-10-09, station UNKNOWN). It is recorded as
  a competing primary claim in CF-DB05-F1-PC (still PARTIALLY_RESOLVED); by the
  owner's decision of 2026-10-28 the shipped 1,125 psia stays and 1105 psia is
  withheld.
- Eight assertions (6 F-1, 2 J-2); none promoted. The DB-2A and DB-2B Wave 1
  manifests account for each.

## J-2 AS-501 flight supplement (2026-10-28)

Rocketdyne R-7450-1, J-2 performance analysis of flight AS-501 (NTRS
19680026222, 320 pp., 17 May 1968), read from rendered pages (Tables 10, 11,
16, 28; the OCR is unusable for tables):

- S-II, five-engine average, high mixture ratio region (156-426 s): 225,362.8
  lb, MR 5.45114, Isp 424.46 s; after the mixture ratio cutback: 187,236 lb,
  MR 4.67886, Isp 429.17 s (Table 16). S-IVB engine J2031, first burn: 223,278
  lb, MR 5.5231, Isp 423.28 s (Table 28). These are flight reconstructions;
  the report names no rating.
- CF-DB05-J2-THRUST stays PARTIALLY_RESOLVED: the first Saturn V's J-2 engines
  flew at about 223,000-225,000 lb, consistent with the 225,000 lb version,
  but no opened document states which rating each flight used.
- Engine J2026's acceptance 'Thrust Chamber Pressure' is 776.3 psia (Table 11,
  station unstated; the figures plot injector-end pressure). Added to
  CF-DB05-J2-PC as context for the unsupported 763 psi; the conflict stays
  RESOLVED at 717 psia nozzle stagnation.
- Ten J-2 assertions (037-046); none promoted. The DB-2A manifest accounts
  for each. DB-0.5 stays PARTIAL.

## RL10A-3-3 design report supplement (2026-10-28)

Pratt & Whitney PWA FR-1769, Design Report for RL10A-3-3 Rocket Engine (NTRS
19670005471, NASA-CR-80920, 28 Feb 1966), read from text with the tables
checked as images. DB-0 held ENG-US-RL10A-3-3 as an unsourced placeholder;
it now has 22 Tier A assertions (contractor design estimates):

- Rated thrust 15,000 lb at 200,000 ft, nominal Isp 444 s, O/F 5.0:1, area
  ratio 57:1 (57.1 effective), at least three starts and 450 s per firing,
  4,000 s service life (Introduction).
- Basic engine weight 289.79 lb (3-sigma maximum; specification 290.00 lb),
  total 301.19 lb (Table IV-1).
- At 5.0:1: throat-total pc 385.2 psia, injector-face static 394.6 psia,
  fuel 5.63 and oxidizer 28.16 lb/s, fuel pump 30,250 rpm, oxidizer pump
  12,100 rpm, c* 7,626 ft/s, throat 5.14 in, L* 38.7 in (Table V-1).
- Cycle: the chamber jacket supplies turbine power and the turbine discharge
  runs to the main fuel shutoff valve, i.e. a closed expander (INFERRED; the
  report never prints 'expander').
- New CF-DB05-RL10A33-PC (PARTIALLY_RESOLVED, intra-document): the
  introduction's 400 psia 'nominal design chamber pressure' has no station
  and differs from the table's 385.2 / 394.6 psia.
- CF-DB05-RL10A33A-MR-ISP stays EXPLAINED for the seeded RL10A-3-3A, but the
  design report estimates 444 s for the A-3-3 too, so NAP's 442 s for the
  A-3-3 is not its design estimate; its origin is not established.
- RL10A-3-3 is not a seed engine; nothing promoted.

## H-1 200K supplement (2026-10-28)

Two Chrysler Space Division reports on Saturn IB stage S-IB-4 (flown on
AS-204), found by NTRS search for the 200K/205K ratings CF-DB05-H1-THRUST
held as secondary-only:

- Final Static Test Report, Stage S-IB-4 (NTRS 19660014225, 25 Feb 1966):
  "All engines produced thrust values within the specified limits of 200K±3
  percent" (Section 2, p.5). The measured thrust is in a Confidential
  Supplement that is not part of the document.
- Final Flight Performance Prediction for AS-204, S-IB-4 (NTRS 19680003903,
  20 Nov 1967), Table 5: average engine at sea level from Rocketdyne engine
  logs 200.53 kips, Isp 262.60 s, MR 2.2168 (static tests SA-32/SA-33:
  201.57 / 201.36 kips).
- Four assertions on ENG-US-H-1-200K (not a seed engine; nothing promoted).
  CF-DB05-H1-THRUST stays PARTIALLY_RESOLVED: 200K is now primary, 205K is
  still secondary-only.
- 'Description and status of the Saturn IB program' (NTRS 19660063404) was
  tried and returned HTTP 404 (citation without PDF); it stays a lead.

## Apollo 9 SPS supplement (2026-10-28)

SRC-APOLLO9-SPS-FFE was the first of the 17 `FETCHED_NOT_READ` downloads to
be read: TRW 11176-H311-R0-00 (NASA-TM-X-62907, 4 Aug 1969), the final
flight evaluation of the CSM 104 service propulsion system. NTRS 19700019020
marks it GOV_PUBLIC_USE_PERMITTED and not export controlled. CSM 104 is a
Block II spacecraft (engine S/N 62, injector S/N 120).

- Flight performance at standard inlet conditions (burns 2 and 3, p.25):
  20,728 lb vacuum thrust, 313.9 s, MR 1.587. That is 0.9% above the preflight
  model built from acceptance data, which is outside its ±0.73% 3-sigma band.
  It is also just above the upper acceptance specification limit of 20,705 lb.
- Predicted Isp 313.0 s ±1.59 s (3-sigma). Table 2 engine constants:
  c\* 5934.3 ft/s, initial throat area 121.6021 in². Standard inlet conditions
  are 162 / 169 psia (oxidizer / fuel) at 70 °F.
- Tables 5 and 6 (calculated): chamber pressure 100 and 102 psia.
- Tank pressures were 180 / 178 psia at liftoff. The report prints no helium
  regulator set point. It notes that the regulator stems were replaced before
  flight (p.22).
- Eleven assertions on ENG-US-AJ10-137 (026-036); none promoted. The DB-2A
  manifest lists them as Block II (not seeded) and withholds -036 under
  CF-DB05-SPS-REG.
- CF-DB05-SPS-THRUST stays PARTIALLY_RESOLVED. These are flight and acceptance
  values for one Block II engine; the report gives no nominal Block II rating.
- CF-DB05-SPS-REG stays UNRESOLVED. The flight tank pressures are consistent
  with 180 psia but do not settle 186 / 191 psig.
- Figures 1-24 are time-history plots. The DB-0 schematic lead
  SCH-AJ10-137-R2-2 ("Apollo 9 SPS pressurization system") has no drawing in
  this document.

## Unread downloads closed (2026-10-28)

The 16 downloads still marked `FETCHED_NOT_READ` were read, which brings that
count to 0. One lead DB-0 cited but never fetched was added: AEHS RPE09.31, the
SPS page. Each document is now READ_AND_MINED, IDENTITY_VERIFIED_ONLY or
FETCHED_NOT_EVIDENCE. Nothing was promoted, and the shipped reference-engine
files rebuild byte for byte.

- **SSME / RS-25** (`ledger_ssme_unread.py`):
  - AIAA 97-2685 (Bradley 1997), Figure 2: RPL 470,000 lb, 3006 psia, Isp 453.5 s
    at altitude, throttle 65-109%, weight 7000 lb, design life 27,000 s / 55
    starts. These are filed on Block I, the pre-large-throat engine; the
    configuration is unstated. Withheld for rights: the cover carries an AIAA
    reprint notice.
  - KSC fact sheet FS-2005-09-030-KSC: about 7,000 lb (3,150 kg).
  - Biggs, "SSME - The First Ten Years" (AAS 1992, Tier B), for the original
    engine: HPFTP 35,000 rpm, HPOTP almost 30,000 rpm, LPFTP 15,000 rpm and
    LPOTP 5,000 rpm. Filed on ENG-US-SSME-FPL-PHASE-I.
  - CF-DB05-RS25-MASS stays UNRESOLVED. The Shuttle-era figures now run from
    7,000 to 7,400 lb with no definition. L3Harris's web page prints 7,775 lb,
    against its own spec sheet's 7,774 lb.
  - The HPFTP and HPOTP speed conflicts gain claims for the original engine.
  - Identity only, because their values repeat records already made: the HAER
    3HO chapter, NASA's RS-25 page and L3Harris's RS-25 page.
- **LMDE**, Apollo 15 DPS evaluation (`ledger_lmde_a15.py`):
  - LM-10, engine S/N 1046, at standard inlet conditions: 9807 lbf, 305.8 s, MR
    1.594. The specification ranges are 9712-10027 lbf, more than 305.0 s and
    MR 1.586-1.614.
  - Table 1 gives a throat area of 53.495 in² and an approximate expansion
    ratio of 54.0. TN D-7143 ends the design's columbium skirt at 47.5:1, and
    no opened document says why LM-10 differs.
  - **Owner decision open:** this discrepancy is not filed as a `C()` conflict.
    Under the DB-2B rule it would withhold the shipped LMDE cooling-zones text
    (AS-DB05-US-LMDE-010). It is recorded in the assertion note instead.
- **SPS regulator** (`ledger_unread_misc.py`):
  - AEHS RPE09.31 (Tier D) prints "186 ± 4 psig" primary and "191 ± 4 psig"
    secondary. It also says the set points are referenced to a bellows vented
    to ambient, so in vacuum they act as absolute pressures.
  - CF-DB05-SPS-REG moves from UNRESOLVED to PARTIALLY_RESOLVED. The psig/psia
    difference is a reference definition, but a gap of about 6 psi to TN
    D-7375's 180 psia remains.
  - The two DB-0 dispositions for the set points move from UNSUPPORTED to
    CONFIRMED_OTHER_SOURCE.
- **Identity only, no values used:**
  - the AEHS series record (its URL is the RPE08.12 page) and the RPE08.12
    (F-1) and RPE08.22 (J-2) chapters;
  - SAE 730941, real title "Flight Experience with Apollo Spacecraft
    Propulsion Systems" (Thibodaux 1973);
  - the Titan II start-sequence page (Tier E, no originating source);
  - patent US 8,250,853, whose RL10 background names no variant;
  - Rocket Lab patent US 11,408,373, which does not name Rutherford.
- **Fetched, not evidence:**
  - Wikipedia F-1, a tertiary source.
  - JSC-11174 Rev E Volume I: sections 1-9 only. The OMS and MPS drawings DB-0
    cited are in later sections.

## F-1 "Waking a Giant" supplement (2026-10-28)

An NTRS title search on the F-1 mass and chamber-pressure conflicts found
Betts (NASA MSFC), "Waking a Giant: Bringing the Saturn F-1 Engine Back to
Life" (NTRS 20140011656, 2013, GOV_PUBLIC_USE_PERMITTED). Its slides 8 and 13
were viewed as images.

- **Chamber pressure.** Slide 13's F-1 / F-1A comparison prints "Chamber
  Pressure, ns (psia) 982" (F-1A: 1,161). The slide does not define "ns".
  Reading it as nozzle stagnation is INFERRED.
  - This is the first opened agency document to attach any station to the
    lower F-1 value. CF-DB05-F1-PC stays PARTIALLY_RESOLVED.
  - The owner's 1,125 psia decision is unchanged, and 982 is a withheld
    competing claim.
- **Mass.**
  - The deck repeats 18,616 lb without a definition.
  - The AEHS F-1 page (Tier D) says "approximately 18,500 lb dry". It is the
    only opened source that names a definition.
  - CF-DB05-F1-MASS stays UNRESOLVED.
- **Assertions.** Four F-1 assertions (039-042) and one F-1A, none promoted.
  The total propellant flow of 5,737 lb/s is NOT_NEEDED: CFG-F1 has no such
  field.

**NTRS searches without a usable result (2026-10-28).** These documents were
downloaded and scanned, but none settles its conflict, so none is registered:

| Conflict | Document | Why it does not settle the conflict |
| --- | --- | --- |
| CF-DB05-RS25-PUMPPOWER | NTRS 19890016656 (SSME power-specific redlines) | Prints no pump power. |
| CF-DB05-RS25-PUMPPOWER | NTRS 19930065949 (alternate turbopump integration) | Citation only; no PDF. |
| CF-DB05-RL10B2-PC-ISP | NTRS 19970026009 (RL10B-2 densified-LH2 ignition) | Ignition transients only. |
| CF-DB05-RD170-MR | NTRS 19950002748 and 19950025328 (RD-170 pollutant CFD) | Analysis inputs (241.96 atm); no mixture ratio from a test. |

The LE-7, LE-7A, Vulcain and Vinci epoch conflicts need agency or
manufacturer documents that NTRS does not hold.

**Web search outside NTRS (2026-10-28).** The same open conflicts were searched
on the open web. Nothing new became evidence:

- **CF-DB05-RL10B2-PC-ISP:** the three L3Harris RL10 spec-sheet URLs and the
  RL10 product page all return HTTP 404, so the manufacturer sheet is still
  unreachable. (A retry with a browser user agent was refused and not
  pursued.)
- **CF-DB05-VINCI-EPOCH:** ESA's "All engines for Ariane 6 complete
  qualification tests" (15 Oct 2020) dates qualification to October 2018 and
  counts more than 140 tests, but prints no thrust. The IAC-18 ArianeGroup
  abstract (Haeseler) prints no thrust or Isp either.
- **CF-DB05-VULCAIN-TURBOPUMPS:** only encyclopedia pages and datasets were
  found, and these are not evidence.
- **CF-DB05-RS25-PUMPPOWER:** search only re-finds the L3Harris RS-25 sheet
  already opened, which prints 71,140 / 23,260 hp without a power level.
- **CF-DB05-LE7-EPOCH:** the 1998 J-STAGE LE-7 LH2 turbopump paper
  (JJSASS 46(539)) is free to read, but its PDF never downloaded completely.
  It stays a lead and is not registered, because the registry takes only
  sources DB-0 listed or documents that were opened. Its abstract has no
  numbers.

**Decision on the LM-10 area ratio (2026-10-28, taken under the owner's
standing instruction to decide without asking).** LM-10's approximate 54.0:1 is
kept as a note on AS-DB05-US-LMDE-021 and is not filed as a `C()` conflict:

- The shipped LMDE cooling-zones text (AS-DB05-US-LMDE-010) describes the
  design in TN D-7143, and nothing in it is shown wrong for that design.
- The Apollo 15 value is for one flight engine, carries an "approximate" flag,
  and no opened document gives a reason for the difference.
- Withholding shipped data on that basis would change production without
  evidence.

The owner can reverse this; filing the conflict would require withholding -010.

**DB-0 conflict backlog, US engines (2026-10-28), `tools/ledger_db0_backlog.py`.**
Seven DB-0 conflicts on US engines that DB-0.5 had not reviewed were checked
against documents already opened and the secondary pages DB-0 cited. Those
pages were fetched now: AEHS 'One Second' (F-1), Purdue H-1 and LR91-AJ-11,
Astronautix LR87-5 and LR87-7, and the TMS Titan II page. The Smithsonian F-1
record returned HTTP 403 and was not retried.

| DB-0 conflict | DB-0.5 conflict | Result |
|---|---|---|
| CF-R2_US_CLASSIC-J2-4 | CF-DB05-J2-ISP | RESOLVED: both opened NASA documents print 425 s. The 421 s is an unopened flight value; AS-501 shows Isp moving with the mixture-ratio region. |
| CF-R2_US_CLASSIC-F1-4 | CF-DB05-F1-PUMPFLOW | PARTIALLY_RESOLVED: the AEHS flows (413.5 + 258 gal/s) and the encyclopedia gpm are one figure; the Smithsonian 42,500 gpm is unreachable. |
| CF-R2_US_CLASSIC-F1-3 | CF-DB05-F1-TURBSPEED | EXPLAINED: 91.5 rev/s = 5,490 rpm, i.e. 5,500 rpm rounded. |
| CF-R2_US_CLASSIC-H1-2 | CF-DB05-H1-ISP-MASS | PARTIALLY_RESOLVED: Purdue's 263 s / 2,009 lb sit beside a 205,000 lb rating; the S-IB-4 primary average is 262.60 s; no primary H-1 mass has been opened. |
| CF-R2_US_CLASSIC-LR-1 | CF-DB05-LR87-GIMBAL | EXPLAINED: 5° is for the Stage I chambers, 4° for the Stage II LR91-AJ-5. |
| CF-US_HIST-19 | CF-DB05-LR87-7-PC | UNRESOLVED: Astronautix prints 47.00 bar (LR87-7) against 54.00 bar (LR87-5) as DB-0 said. It also prints a different area ratio (9 against 8), so the difference may be a real design difference rather than a typing error. |
| CF-US_HIST-05 | CF-DB05-LR91-AJ11-MR | RESOLVED: the Titan IIIE/Centaur summary (NTRS 19750004937, p.6-27) prints 1.79, and its flows (203 / 114 lb/s) give Purdue's 1.78. The 1.86 was never opened. |

The AEHS page also prints the F-1 chamber pressure as "1,125 psig"; this was
added to CF-DB05-F1-PC as a withheld competing claim.

Promotion:
- DB-2A: CF-DB05-J2-ISP is CARRIED_NOT, touching the shipped 425 s.
- Wave 1: the four AEHS F-1 values are WITHHELD_RIGHTS (pinned total 53 → 57), and the pump-flow conflict withholds its claims.
- No shipped value changed, and the shipped files rebuild byte for byte.

**Second step, Wave 2/3 engines (same day).**

Several DB-0.5 conflicts filed in the wave passes already covered DB-0
conflicts but did not link them. They are now linked:

| DB-0.5 conflict | Now linked to DB-0 conflicts |
|---|---|
| CF-DB05-RUTHERFORD-SL-THRUST | COM-12, ANCHOR_US_MODERN-5 |
| CF-DB05-RUTHERFORD-VAC-THRUST | COM-11, ANCHOR_US_MODERN-4, R2_SCHEM-R2-11 |
| CF-DB05-LE7A-EPOCH | R2A-1, ASIA_OTHER-2 (Isp) |
| CF-DB05-VULCAIN-THRUST | EUROPE-1 |
| CF-DB05-VULCAIN-TURBOPUMPS | R2A-19 |

On R2A-19: the 1990 NASA briefing prints 13,000 rpm for the Vulcain 1, so that
number does not identify Vulcain 2's new LOX pump.

New conflicts:

| DB-0.5 conflict | DB-0 conflicts | Result |
|---|---|---|
| CF-DB05-LE9-ISP | R2A-4, ASIA_OTHER-4, TAX-2 | RESOLVED: JAXA, MHI and IAC all print 425 s. |
| CF-DB05-VULCAIN-MASS | EUROPE-2, EUROPE-5 | UNRESOLVED: both opened masses (1300 kg in 1990; ESA 1686 kg) are for the first Vulcain. EUROPE-5's Vulcain 2 attribution is not supported. |
| CF-DB05-VINCI-IGNITIONS | EUROPE-7 | PARTIALLY_RESOLVED: ESA 2024 gives four ignitions, which equals three restarts. The earlier "five" was not transcribed. |

Wave 3 withholds their claims; nothing of these engines shipped before.

CF-DB05-IPD-THRUST (DB-0 R2-14): EXPLAINED. Every value is the same 250,000
lbf design class, rounded differently. It is carried as not affecting the
promoted IPD statements that print it.

Rutherford's "311 s" sea-level Isp (COM-13) stays open; see the web pass below
(the release had been read in the Wave 2 pass, so no new download was needed).

**RD-180 and NK-33 (same day), `tools/ledger_rd180_nk33.py`.** Neither engine is
seeded. An NTRS search for "RD-180" found two NASA documents:
- NASA-TM-108475 (MSFC, Jan 1995), a pre-design vehicle study. Its Figure 40 gives proposed engine data derived from the RD-170: 827,000 / 900,000 lb, 309 / 337 s, 3,560 psia, MR 2.6, 50 %, 11,675 lb dry.
- Ross (NTRS 20010067310, 2001), which describes the engine tested at MSFC: 3,734 psia, 50–100 %, 11,675 lb dry.

The Aerojet 2012 ASEB slides give the NK-33 at 100 %: 377 / 338 klbf, 331 / 297 s, 2,109 psi, MR 2.6, 27.7:1 and 2,985 lbm.

Findings:
- Purdue's RD-180 11,675 lb, 3,734 psia and 2.6 trace to these two NASA documents.
- Purdue's NK-33 "339,000 lbf vacuum" is the sea-level figure, mislabelled.

New conflicts:

| DB-0.5 conflict | DB-0 conflicts | Result |
|---|---|---|
| CF-DB05-RD180-PC | ANCHOR_USSR-1, USSR-4 | PARTIALLY_RESOLVED |
| CF-DB05-RD180-MASS | ANCHOR_USSR-6 | PARTIALLY_RESOLVED |
| CF-DB05-RD180-MR | ANCHOR_USSR-5 | PARTIALLY_RESOLVED |
| CF-DB05-RD180-THROTTLE | ANCHOR_USSR-3 | UNRESOLVED |
| CF-DB05-RD180-THRUST | ANCHOR_USSR-7 | UNRESOLVED |
| CF-DB05-NK33-PC-THRUST | R2_USSR-R2-4 | PARTIALLY_RESOLVED |

**Manufacturer pages for the Russian engines (same day).** The registry already had
URLs for these pages, but they had never been fetched. They are now fetched and read:
- Spaceflight Now's RD-180 fact sheets, credited Pratt & Whitney/NPO Energomash: 860,200 / 933,400 lb, 311.3 / 337.8 s, 3,722 psia, 36.87:1, MR 2.72, 40–100 %, total system dry weight 11,889 lb.
- Glavkosmos RD-180: 390 / 423 tf, 311 / 339 s, 261.7 kgf/cm², 5,480 kg dry, 100–47 %.
- Glavkosmos RD-171M: 250 kgf/cm², 9,300 kg dry.
- The pnp.ru article: 261.7 kgf/cm² per the manufacturer, and a "> 280 atm" certification margin.
- The IAC-13 abstract: 25.9 MPa as the RD-171M's "maximum reached".
- Buran-Energia (RD-0120: 190 / 147.6 tf).
- RussianSpaceWeb (RD-0120: 11° gimbal).

The JAXA RD-0120 PDF returned HTTP 503.

Results:

| DB-0.5 conflict | Result |
|---|---|
| CF-DB05-RD180-THRUST | EXPLAINED (the 1995 figures are an estimate; the manufacturer figures agree) |
| CF-DB05-RD180-MR | EXPLAINED (2.72 is the built engine; 2.6 is the 1995 estimate) |
| CF-DB05-RD180-PC | PARTIALLY_RESOLVED (261.7 kgf/cm² = 3,722 psia; the 2001 NASA 3,734 is unexplained) |
| CF-DB05-RD180-MASS | UNRESOLVED (three masses: 11,675 / 11,889 lb and 5,480 kg) |
| CF-DB05-RD180-THROTTLE | UNRESOLVED (floors of 50 / 40 / 47 %) |
| CF-DB05-RD180-AREA-RATIO | UNRESOLVED (36.87 against 36.4) |
| CF-DB05-RD170-THRUST | EXPLAINED (every figure is the placard's 740 / 806 t). Wave 2 records it as CARRIED_NOT; no thrust ships. |
| CF-DB05-RD171M-PC | EXPLAINED (rated against maximum reached) |
| CF-DB05-RD171M-MASS | PARTIALLY_RESOLVED |
| CF-DB05-RD0120-THRUST-GIMBAL | UNRESOLVED |

DB-0 had reported a 47 % floor for the 2002 Spaceflight Now page, but that page prints 40–100 %.

65 of the 261 DB-0 conflict records had a DB-0.5 counterpart after this pass.

**DB-0 conflict web pass (same day), `tools/ledger_db0_web.py`.** All 162
secondary pages that DB-0 cites in its open conflicts and that have a URL were
fetched with `fetch.py`; 121 downloaded. Each claim was searched for in
the extracted text, and a value counts as seen only where the number stands
there in the sense DB-0 gave it. 104 pages were read (`IDENTITY_VERIFIED_ONLY`:
no assertion is filed from news, museum, catalogue or encyclopedia-mirror
pages) and 17 were reached without the claimed value or without usable text
(`FETCHED_NOT_EVIDENCE`, reason per record). `FETCHED_NOT_READ` is 0 again.

110 conflict records were filed (`CF-DB05-W-*`, one per DB-0 conflict):
61 UNRESOLVED (only one side read, or nothing settles it), 29 EXPLAINED,
13 PARTIALLY_RESOLVED, 5 RESOLVED and 2 CONFIRMED_SECONDARY. What the
pages changed:

- DB-0 misread sources in several places: the ESA blog says the Artemis II
  OMS-E flew six times "between 2000 and 2002", not in 2011 (SPACECRAFT-4,
  RESOLVED against STS-112); the Jiemian article gives "45%-111%" for an
  improved TQ-12, not 55–110 % for the TQ-15A; Encyclopedia Astronautica's
  Agena B page prints 71.17 kN and 285 s, not 70.7 kN or 71.2 kN / 291 s.
- 854 kN for the Merlin 1D is a transposition: SpaceX's 2025 user's guide
  prints 845 kN (190,000 lbf), which is what 190,000 lbf converts to.
- Merlin 1D and MVac thrust are time series (147,000 → 170,000 → 190,000 lbf;
  210,000 → 220,500 lbf), not conflicts.
- LAM 440 N propellant roles (ISRO's IAC abstract: MON-3 and MMH), Valois
  (one engine, 35 t, Diamant B) and Broadsword (25,000 lbf at sea level, maker's
  page) are RESOLVED from the authors' or maker's own text.
- The RS-25 mixture ratio (6.03:1 sheet, 6.0 web, both L3Harris) is EXPLAINED.
  Rutherford's 311 s (COM-13) stays UNRESOLVED: Rocket Lab prints it beside the
  sea-level engine twice, and DB-0's doubt is a plausibility judgement, not a
  second source.

Twelve of these sit on seed engines and have Wave 1–3 manifest decisions. Ten
change nothing that ships. COM-13 withholds the two Rutherford statements that
print 311 s (Rutherford values were not carried anyway, for rights reasons).
RS-3 is CARRIED_NOT.

175 of the 261 DB-0 conflict records had a DB-0.5 counterpart after the web pass.

**DB-0 conflict encyclopedia pass (same day), `tools/ledger_db0_wiki.py`.** The
last 86 DB-0 conflicts cite only encyclopedia pages, URL-less search summaries,
or sources that had failed. 58 English Wikipedia articles (current revision, CC
BY-SA) and one machine-generated encyclopedia page were fetched and read. They
are encyclopedia pages, so they settle what the cited page says, not what an
engine does. The 7 sources that had failed with a connection error were retried
once and failed again; a French encyclopedia page and a mirror refused (403, 401). Blue Origin pages answer 429 and
the L3Harris datasheets and AIAA vehicle guides 404.

81 records were filed (`CF-DB05-E-*`): 25 EXPLAINED, 3 PARTIALLY_RESOLVED, 53
UNRESOLVED. Most of the explained ones were never engine conflicts:

- Two revisions of one article: LE-9 10.0 against 12.4 MPa, BE-4 134 against 140
  bar, TEPREL-C 50 against 75 kN, BE-3U open expander against expander bleed.
- DB-0 misreadings: CE-7.5 "75 kN max" is the 75 bar chamber pressure; TR-107
  "half the thrust" is said of the TR-106; the NK-15 page's 1,753 kN / 14.50 MPa
  / 331 s set is NK-33 data; BMW 109-558 3.7 / 0.588 kN and 375 / 60 kgf are one
  thrust profile in two units.
- Variants or operating points on one page: SEPR 841 TX2 against SEPR 844
  kerosene; SuperDraco 71 kN per engine, 32,000 lbf per pod, 68.17 kN as
  throttled in tests; Raptor 1 185 tf nominal against ~225 t demonstrated;
  Merlin 1D 282 / 311 s flagged by the article itself as outdated.

Five DB-0 conflicts were not filed, because a ledger claim must cite a source:
RD-170 turbine power, the A-4 propellant load, the Arroway cycle and the RD-253
index carry no source id, and the H-1 188K '188,00' is a single truncated figure
on a 404 page. Filing that last one would withhold the promoted primary H-1
thrust. The skipped five are listed in `NOT_FILED` in the module.

Fourteen of the new records sit on seed engines and have manifest decisions;
none withholds or touches a shipped value.

256 of the 261 DB-0 conflict records now have a DB-0.5 counterpart; the other
five are the `NOT_FILED` set. Every DB-0 conflict has now been reviewed. 
Closing the 132 UNRESOLVED records in the ledger needs primary
documents. The ones blocking seed engines are LE-7A pc, Vulcain 2 pc and area
ratio, RS-68A pc, the RL10A-4-2 area ratio, RL10B-2 mass and YF-77 performance.

**RS-68 baseline (2026-10-29), `tools/ledger_rs68.py`.** An NTRS search for the
seed-engine gaps found Rocketdyne's 1999 IAF Congress slides (NTRS 20000025317,
scanned). The "RS-68 Engine Performance Baseline" slide gives 745 / 650 klbf
vac / sea level, 1,410 psia (836 throttled), MR 6.0, 410 s average vacuum Isp,
expansion ratio 21.5 and under 15,000 lb. That is a pre-flight rating, so
CF-DB05-E-US_HIST-04 is PARTIALLY_RESOLVED: the encyclopedia's 663,000 lbf and
1,488 psi are a later rating with no primary. NASA's 2009 Ares V paper (already
in the ledger) gives the RS-68A as 39,000 lbf above the RS-68, and
663,000 + 39,000 = 702,000 lbf matches NASA's RS-68A figure. Still no primary
for the RS-68A chamber pressure or Isp; the paper prints only RS-68B values
(414.2 s, 797 klbf vac). Nothing changes on the shipped RS-68A.

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

## LE-7A and RL10A-4-2 primaries (2026-10-29)

- NASDA 委16-4 (1997-05-14, MEXT archive) opened as SRC-DB05-NASDA-LE7A-FT6-1997: LE-7A development firing test 6
  printed main combustion pressure about 120 kgf/cm2a (11.77 MPa DERIVED). It was added as a claim to
  CF-DB05-E-R2_ASIA-R2A-2 and CF-DB05-E-ASIA_OTHER-1. These stay UNRESOLVED because a development-test reading is not
  the flight rating.
- CF-DB05-E-R2_US_CLASSIC-A42-1 is now PARTIALLY_RESOLVED: NRC Table D-4 prints 84:1 for the RL10A-4-2 against
  AIAA's 85:1. The NRC area ratio is withheld in the wave-2 manifest.
- Still open with no primary reached: Vulcain 2 pc and area ratio, RS-68A pc, RL10B-2 mass, YF-77.

## YF-77, Vulcain 2 and RL10B-2 searches (2026-10-29)

- YF-77: opened the developer's IAC-17 keynote abstract, SRC-IAC17-41861 (BAPI). It prints "700-kN in vacuum" at O/F 5.5
  and "a factor of 2.7 on pressure" over the YF-75, which gives the environment the IAC-13 abstract left unstated. The
  three assertions are NOT_PROMOTED (IAF rights), and the wave-3 count test went from 111 to 114. No absolute chamber
  pressure, sea-level thrust or Isp is printed, so CF-DB05-E-R2_ASIA-R2A-13 stays UNRESOLVED. No full paper and no
  CNKI or CALT document was reached.
- Vulcain 2 area ratio: an ESA patent, US 6,996,973 B2 (priority 1999), states "an area ratio R equal to 60 for a
  specific impulse of 433 seconds". That is a round design-era figure, not precise enough to choose between 58.2 and
  58.5. It is added as a claim to CF-DB05-E-ANCHOR_EU_ASIA-3, which stays UNRESOLVED. The patent gives no chamber
  pressure.
- RL10B-2 mass: NTRS 20170008949, a 2017 paper on carbon-carbon nozzle extensions, was opened and prints no engine
  mass. No value was taken.
- RS-68A pc: the L3Harris RS-68A product page also returns 404, like its data sheet.

## ULA Delta IV user's guide (2026-10-29)

- Opened the ULA Delta IV Launch Services User's Guide (June 2013), SRC-DB05-ULA-DELTA4-UG-2013. Its pp. 1-5 and 1-6 give
  the RS-68A as 3137 kN (705,250 lbf) at sea level, 411.9 s vacuum and 21.5:1, and the RL10B-2 as 110 kN (24,750 lb),
  465 s, with electromechanical gimbal actuators. It prints no chamber pressure and no engine mass. It is used for
  conflict claims only; no assertion was taken from it.
- CF-DB05-E-R2_SCHEM-R2-2 (RS-68A Isp, 411 vs 411.9 s) is now EXPLAINED.
- CF-DB05-E-R2_US_CLASSIC-B2-4 is now PARTIALLY_RESOLVED: the gimbal half is settled, the RL10B-2 mass half is still open.
- CF-DB05-RS68A-THRUST stays PARTIALLY_RESOLVED. The guide supports 705,000 lbf at sea level. The owner decision
  WAVE2-RS68A-THRUST, which keeps the NASA-blog 702,000 lb withheld, is unchanged.
  - For the owner: that decision's premise was that the manufacturer value existed only as unopened evidence. That
    premise is weaker now, but nothing was promoted.
- Totals: 129 UNRESOLVED, 39 PARTIALLY_RESOLVED, 69 EXPLAINED.

## Ariane 5 user's manual (2026-10-29)

- Opened the Arianespace Ariane 5 User's Manual, Issue 5 Revision 2 (October 2016), as SRC-DB05-ARIANESPACE-A5UM-I5R2.
  The copy is an edX (DelftX) course asset, not one taken from arianespace.com.
- For the Vulcain 2 it prints 960 kN at sea level and 1390 kN in vacuum ("maximum thrust in vacuum"), and an Isp of
  about 310 s at sea level and 432 s in vacuum. It gives no chamber pressure, area ratio or flow rates.
- CF-DB05-W-ANCHOR_EU_ASIA-1 (Vulcain 2 vacuum thrust) is now PARTIALLY_RESOLVED: the operator's 1390 kN matches CNES,
  while 1359 kN appears only in secondary pages.
- Also tried, no usable copy: the Ariane 5 User's Manual Issue 4 at the ENSTA mirror (404), and the Airbus VA219 flight
  dossier (no engine figures).

## LE-7A chamber pressure resolved (2026-10-29)

- Opened four sources:
  - JAXA's LE-7A engine page (12.3 MPa).
  - MHI's 2016 technical review, 三菱重工技報 Vol.53 No.4, Table 1 (12.3 MPa, main chamber).
  - The H-II F8 investigation report in the MEXT archive, 別添表8-2 (design-era 12.2 MPa at MR 6.2).
  - A JAXA page on a 2010 H-IIB F3 LE-7A firing (about 12.3 MPa measured, planned range 11.7-13.2).
- With JAXA's 2017 LE-9 briefing (AS-DB05-JP-LE-7A-018, 12.3 MPa), CF-DB05-E-R2_ASIA-R2A-2 and CF-DB05-E-ASIA_OTHER-1
  are RESOLVED. No primary prints 12.0 MPa or 121 bar.
- Correction to the earlier "LE-7A and RL10A-4-2 primaries" entry: a rating document had already been filed. The JAXA
  2017 briefing was recorded in wave 3, and the earlier explanation missed it.
- The LE-7A is still not carried, so nothing new ships (wave-3 manifest CARRIED_NOT, AS-018 listed as competing).
- Totals: 126 UNRESOLVED, 16 RESOLVED.
- HM7B, from the same Arianespace manual (ESC-A table and p.A4-3): 67 kN maximum vacuum thrust, 446 s, 945 s burn.
  - CF-DB05-W-ANCHOR_EU_ASIA-7 (burn time, 945 vs 950 s) is EXPLAINED.
  - CF-DB05-W-EUROPE-9 and CF-DB05-W-ANCHOR_EU_ASIA-5 (thrust, 62.2 / 64.8 / 67 kN) are PARTIALLY_RESOLVED.
- The open conflicts were checked against the assertions already filed. Only CF-DB05-RS25-SLTHRUST has a primary
  assertion outside its claims, and that is a known power-level definition question.
- Totals: 123 UNRESOLVED, 42 PARTIALLY_RESOLVED, 70 EXPLAINED.
- CNES Ariane 5 page (cnes.fr/projets/ariane-5/lanceur), opened as SRC-DB05-CNES-A5-LANCEUR. The old CNES URL, which
  gave no text, now redirects here. It prints:
  - Vulcain: 1 650 kg. This is a third mass beside 1300 and 1686 kg, so CF-DB05-VULCAIN-MASS stays UNRESOLVED.
  - Vulcain 2: 1 390 kN in vacuum.
  - HM-7B: 67 kN, burning up to 15 min 45 s.
  - Aestus: 29 kN in vacuum, added to CF-DB05-E-EUROPE-10, which stays UNRESOLVED.
  These were added as claims to the Vulcain 2 and HM7B records above.
- BE-4: the ULA Vulcan Launch Systems User's Guide (October 2023), SRC-DB05-ULA-VULCAN-UG-2023, prints 2446.5 kN
  (550k lbf) at sea level for each engine. It was added as a claim to CF-DB05-W-R2_SCHEM-R2-5, which stays UNRESOLVED:
  the 640,000 lbf uprate sits on Blue Origin pages that return HTTP 429.

### What the 123 UNRESOLVED records still need

- Blue Origin pages, all rate-limited: BE-4, BE-3U.
- Full IAC papers or Chinese journals: YF-77, YF-100, YF-75D, YF-115.
- Manufacturer datasheets:
  - Safran/ArianeGroup: Vulcain 2 pc and area ratio, HM7B pc.
  - Airbus: Aestus pc and mixture ratio.
  - L3Harris: RS-68A pc. The L3Harris pages return 404.
- Owner definition decisions between opened primaries: RS-25 mass and pump power, F-1 rating epoch and mass, RD-180
  mass and throttle range.
- Many single-record historical and small engines with no primary reachable from here.

## ESA Bulletin 102: Vulcain 2 (2026-10-29)

- Opened ESA Bulletin 102 (May 2000), D. Coulon, as SRC-DB05-ESA-BULLETIN-102-VULCAIN2. Table 1 gives development-era
  values: 1 350 kN vacuum, 433 s, 115 bar, mixture ratio 6.10, section ratio 58.5, 320 kg/s, 1935 kg. The text gives
  44.9 kg/s of hydrogen at the nominal point.
- Now PARTIALLY_RESOLVED:
  - Chamber pressure: CF-DB05-E-EUROPE-4 and CF-DB05-E-ANCHOR_EU_ASIA-2. 115 bar is supported; 117.3 bar has no
    primary.
  - Area ratio: CF-DB05-E-ANCHOR_EU_ASIA-3. 58.5 is supported.
  - Flows: CF-DB05-W-R2_ASIA-R2A-20 and CF-DB05-W-ANCHOR_EU_ASIA-4. Neither claim is the Vulcain 2 value; the 41.2 kg/s
    fits the first Vulcain.
- The thrust record now shows growth from 1350 kN in 2000 to 1390 kN on the flown engine.
- Aestus mixture ratio: CF-DB05-E-EUROPE-12 is PARTIALLY_RESOLVED as two epochs (2.05 changed to 1.90, first flown in
  2004), from the encyclopedia's history section only.
- Tried without result: Airbus space-propulsion.com (pages now 404) and core.ac.uk DLR copy (HTTP 403).
- Totals: 117 UNRESOLVED, 48 PARTIALLY_RESOLVED.
- RL10B-2: opened NASA TM-107470 (1997), NTRS 19970026009. It uses "a delivered Isp of 466.5 sec at a mixture ratio of
  6.0", so CF-DB05-RL10B2-PC-ISP is now PARTIALLY_RESOLVED: the Isp half leans to 466.5 s, and the chamber pressure
  half (644 vs 633 psia) is still open. It prints no engine mass.
- NTRS searches for "HM7", "RS-68A" and "Vulcain" found nothing relevant.
- Totals: 116 UNRESOLVED, 49 PARTIALLY_RESOLVED.
- Opened ESA Bulletin 123 (August 2005, Ariane-5 ECA), SRC-DB05-ESA-BULLETIN-123-A5ECA:
  - Vulcain-2: 1350 kN, against 1100 kN for Vulcain-1. Bulletin 102 gave the Vulcain-1 figure as 1145 kN.
  - HM-7B: 65 kN in vacuum, 447 s.
  - ESC-A: up to 970 s of propelled flight.
- These were added to CF-DB05-VULCAIN-THRUST, CF-DB05-W-ANCHOR_EU_ASIA-1, -5 and -7, and CF-DB05-W-EUROPE-9. They
  narrow the epochs; no resolution changed.
- Tried, not reachable: the 推进技术 (Journal of Propulsion Technology) 2021 YF-77 design paper by BAPI, whose PDF link
  answers with a slider bot check (not attempted further), and SciEngine (empty page).
- Aestus thrust: opened ESA Press Release N° 35-1994 (development test campaign), which gives 27.5 kN, 1130 s and a
  nominal of about 1100 s. It was added to CF-DB05-E-EUROPE-10, which stays UNRESOLVED as a likely epoch difference
  (27.5 kN in 1994 against 29 or 29.6 kN later). No document records the change.
- YF-100: the 深空探测学报 (Journal of Deep Space Exploration) 2021 paper (SRC-DB05-JDSE-2021-YF100) serves only its
  abstract. The PDF preview URL returns an HTML stub, so its four tables (thrust, throttle range) were not reached.
  CF-DB05-W-R2_ASIA-R2A-14 and -15 stay UNRESOLVED.

## Pass 2026-10-29: XLR99 mass, R-4D thrust (NTRS)

- CF-DB05-E-US_HIST-09 (XLR99 mass) RESOLVED: NTRS 19710070145 (*XLR99 engine operating
  experience*, 1961) prints dry weight 910 lb; Table I gives 540 → 856 → 910 lb dry (1,025 lb wet)
  across specifications. 915 lb has no document.
- CF-DB05-W-SPACECRAFT-2 (R-4D thrust) PARTIALLY_RESOLVED: NTRS 19690029231 (Marquardt Apollo
  SM/LM RCS summary, 1969) gives a nominal 100 lb, raised from 95 lb at PFRT. The 110 lbf figure
  belongs to a later variant and has no opened document.
- UNRESOLVED: 116 → 114.
- CF-DB05-W-R2_SC_COMM-R2-9 (GR-22 flown) RESOLVED: NTRS 20170001286 p.2, re-read, states that
  only the GR-1 is in GPIM's on-orbit phase (GR-22 cracked in 2014 ground test; redesign tested in
  2015). Shipped data already lists the GR-22 as "GPIM (planned)". UNRESOLVED: 114 → 113.
- Searched NTRS for M-1 termination and later R-4D (110 lbf) documents: nothing usable.

## Pass 2026-10-29: Redstone A-7, Atlas verniers, RS-56-OSA (NASA SP-45)

- NASA SP-45 *Mercury Project Summary* (1963, NTRS 19630012071, 454 pp.) gives the Mercury-Redstone
  "Model A-7 engine, Thrust 78,000 lb" and the Mercury-Atlas sustainer 57,000 lb with two verniers
  of 1,000 lb each.
  - CF-DB05-W-US_HIST-13 (NAA 75-110 A-6) PARTIALLY_RESOLVED: 78,000 lb is the A-7 rating; the A-6's
    91,350 lbf still has no document.
  - CF-DB05-W-US_HIST-24 (LR101) PARTIALLY_RESOLVED: 1,000 lb on Atlas D, consistent with 1,017 lbf
    tank-fed; 830/525 lb and 1,060 lbf still unopened.
- CF-DB05-E-US_HIST-16 (RS-56-OSA) EXPLAINED: 60,500 lbf × 316/220 s = 86,900 lbf (386.5 kN),
  so the two figures are sea-level and vacuum thrust of one engine.
- `fetch.py` fix: downloads were capped at 180 s and a timed-out, truncated PDF was logged as
  HTTP 200. The cap is now `DB05_CURL_MAX_SECONDS` (default 180), and a curl failure is written
  into the status. SP-45 was the only truncated file; it was refetched in full.
- Searched without result: L3Harris/Aerojet spacecraft-thruster spec sheets (every URL 404,
  Wayback 429), so R-42, R-40B, MR-103J, MR-111G and R-4D-11 stay open.
- UNRESOLVED: 113 → 110.
- CF-DB05-E-US_HIST-12 (S-3D thrust) PARTIALLY_RESOLVED: MSFC's 1962 *From Peenemuende to Outer
  Space* (NTRS 19630006100, tier B) says the Jupiter S-3D "produced a thrust of 150,000 lb"; the
  134,908 lbf sea-level figure still has no document.
- CF-DB05-E-US_HIST-23 (M-1 cancellation) PARTIALLY_RESOLVED: Aerojet's 1968 M-1 thrust-chamber
  report (NTRS 19680014530) records uncooled-chamber firings in July–August 1966 before the
  programme's "phaseout", so a 1965 cancellation is wrong for hardware testing; the phase-out date
  is not printed.
- UNRESOLVED: 110 → 108. Not on NTRS: Stages to Saturn PDF (404), Juno II volume I.
- ESA's EPS page (SRC-ESA-EPS), never opened by DB-0 because m.esa.int gave no response, was
  fetched from www.esa.int: Aestus vacuum thrust 2.7 t, engine weight 115 kg.
  CF-DB05-W-EUROPE-13 (Aestus mass) is PARTIALLY_RESOLVED (agency 115 kg against a catalogue's
  111 kg of unstated scope). EUROPE-10 now cites the page as opened, and stays UNRESOLVED
  (ESA 2.7 t / 27.5 kN against CNES 29 kN). UNRESOLVED: 108 → 107.

## Pass 2026-10-29: retry of failed DB-0 fetches; NASA HAT 2011 engine table

- Retried 15 DB-0 sources that failed on 2026-10-28. Newly reachable: IAC-18 LE-9 abstract (no
  values), the Vikas exam-prep page (does not print 799/846 kN; locator set to NF) and NTRS
  20110015783. The others are still 000/429/500/503.
- NTRS 20110015783 (NASA Human Spaceflight Architecture Team, *Cryogenic Propulsion Stage*, Aug
  2011, tier B) slide 10 tabulates engine options:
  - CF-DB05-E-R2_US_CLASSIC-B2-4 (RL10B-2 mass/gimbal) RESOLVED: 668 lbm (303 kg) against the
    current 301 kg rules out 277 kg; manifest now CARRIED_NOT with nothing shipped.
  - CF-DB05-E-EUROPE-3 (Vulcain 2 vacuum thrust) PARTIALLY_RESOLVED: 301,243 lbf = 1,340.0 kN.
  - CF-DB05-VINCI-EPOCH PARTIALLY_RESOLVED: 40,500 lbf (180.2 kN) in vacuum by 2011. The 2005
    18 t stays unexplained; both ESA values stay withheld, and the epoch test now accepts
    PARTIALLY_RESOLVED.
  - RL10B2-PC-ISP and RL10A42-THRUST-ISP gain the 2011 values (633 psia / 465.5 s;
    22,300 lbf / 450.5 s) and stay PARTIALLY_RESOLVED.
- UNRESOLVED: 107 → 105.

## Pass 2026-10-29: KBKhA manufacturer pages (RD-0120, RD-0124, RD-0124MS, RD-0210)

- The design bureau's own site (kbkha.ru) has a specification block per engine; four registered
  as tier-A manufacturer sources by hand.
  - CF-DB05-W-USSR-6 (RD-0124MS Isp) RESOLVED: 361 s for the RD0124MS, 359 s for the parent RD0124.
  - CF-DB05-W-USSR-16 (RD-0210) PARTIALLY_RESOLVED: 59.36 tf (582.1 kN) and 150 kgf/cm2 (14.7 MPa);
    burn time not printed.
  - CF-DB05-E-R2_USSR-R2-6 (RD-0120 pc) PARTIALLY_RESOLVED: 223 kgf/cm2 (21.9 MPa) beside 200 tf.
  - CF-DB05-RD0120-THRUST-GIMBAL PARTIALLY_RESOLVED: 200 tf = 1,961 kN; the gimbal angle is open.
- The 11D58M page carries history but no figures.
- UNRESOLVED: 105 → 101.
- CF-DB05-W-R2_ASIA-R2A-15 (YF-100 sea-level thrust) RESOLVED: the developing institute's 2021
  *Journal of Deep Space Exploration* paper, previously abstract-only, has a static PDF at the
  journal's preview link (`/sktcxb/cn/article/pdf/preview/<DOI>.pdf`). Its Table 3 prints
  地面推力 1 200 kN. The manifest is now CARRIED_NOT with nothing shipped. R2A-14 (throttle) stays
  open: the paper gives no range. UNRESOLVED: 101 → 100.
- After five requests, jdse.bit.edu.cn began serving a "访问频率较高，请完成安全验证" (rate-limit
  verification) page. That is a bot check, so it was not pursued. The issue-8(4) papers likely to
  hold YF-77/YF-75D tables (DOIs ...2021.20210009, 20210012, 20210021, 20210040) are for a later
  pass at low request rate.
- Remaining blockers after this session: Blue Origin (429), L3Harris/Aerojet datasheets (404),
  NPO Energomash (403), ArianeGroup/Safran datasheets, the jdse rate limit, DTIC PDFs (bot page),
  and the owner definition decisions (RS-25 mass/pump power, F-1 rating/mass, RD-180
  mass/throttle). UNRESOLVED stands at 100.
- Later single retry of jdse succeeded: the CZ-5 general-scheme paper (DOI ...20210009) gives only
  thrust classes (YF-77 50 t级 sea level, YF-100 120 t级, YF-75D 10 t级 vacuum); no conflict moves.
- The remaining definition conflicts (RS-25 mass/pump power/HPFT speed/SL thrust, F-1
  rating/mass, RD-170 MR, RD-180 mass/throttle/area ratio) were re-read. Each is a genuine
  disagreement between documents that no opened document explains. Reclassifying them would either
  misstate the evidence or, for RS-25 SL thrust, release withheld assertions into production. Both
  need the owner, not a research pass.

## Pass 2026-10-29: manufacturer pages for LEROS 4 and Firefly Alpha

- Nammo LEROS 4 product page (tier A): its prose says "MON/ Hydrazine" and its specification table
  says MON-3/MMH. CF-DB05-E-R2_SC_COMM-R2-8 (LEROS 4-ET fuel) is PARTIALLY_RESOLVED: "hydrazine" is
  the maker's loose family wording, and the 4-ET fuel is inferred from the parent.
- Firefly Alpha PUG 5.3 (2026-09; the 5.2 that DB-0 cited returns 404): Lightning 73.0 kN (vac) at
  322 s, Reaver ×4 836.3 kN (vac), with no "maximum" qualifier. CF-DB05-W-COMMERCIAL-COM-16 is
  PARTIALLY_RESOLVED (two maker figures, likely an uprate). COM-15 cites the guide and stays EXPLAINED.
- UNRESOLVED: 100 → 98.
- Rocket Lab: the Neutron PUG (rocketlabusa.com/assets/Uploads/Rocket-Lab-Neutron-PUG-Reduced.pdf) and the
  Electron payload user's guides return 404, so COM-13/COM-14 stay open. IHI publishes no BT-4 page
  that a search reaches.
- KARI 2011 test-range paper (한국추진공학회지 15(6):91-97): main specification 75 tf vacuum, 297 s,
  60 bar. CF-DB05-W-R2_ASIA-R2A-17 (KRE-075 vacuum thrust) is PARTIALLY_RESOLVED: 735.5 kN is
  exactly 75 tf. R2A-16 (pc) gains the 2011 60 bar. UNRESOLVED: 98 → 97.
- Dead ends: ESA Bulletin 94 (Ariane qualification, bullet94/GON.pdf) has no Viking or HM7 values;
  no primary was found for the HM7B chamber pressure (37 vs 35 vs 35.3 bar) or the Viking 5C pc.

### Pass: Chinese commercial makers (2026-10-29)

- CF-DB05-W-R2_ASIA-R2A-28 (Welkin SL thrust) RESOLVED and CF-DB05-E-R2_ASIA-R2A-29 (Welkin-Vac) RESOLVED. The Galactic
  Energy engine page DB-0 had cited as '50 t' (SRC-GE-WELKIN-EN, already fetched 2026-10-28) prints CQ-50 500 kN at
  sea level / 265 s and 600 kN / 330 s for the vacuum version; the Chinese page (List/cid/5, 苍穹50) agrees. The
  encyclopedia's 400 kN and 500 kN 'vacuum' are not the maker's figures. Unresolved: 97 → 95.
- Dead ends: Space Pioneer /tianhuo/TH11, TH12, TH12V pages repeat the TH-12 figures already recorded (TH-11 30 t vac,
  345 s). LandSpace /product/engine gives only TQ-12A (84.6 t SL, 293 s SL, MR 2.9; '+40 m/s Isp over TQ-12'); no TQ-12
  vacuum Isp, so CF-ASIA_OTHER-13 stays UNRESOLVED.

### Pass: Phoenix descent engines and Juno main engine (2026-10-29)

- CF-DB05-W-SPACECRAFT-9 (MR-107N count) RESOLVED: JPL's 2008 AIAA paper (NTRS 20080034655, Grover and Cichy) p.2 prints
  "a system of 12 pulsed thrusters" for the powered descent; the 2004 IPPW presentation (NTRS 20070014659) slide 10
  gives "12 descent engines, ~300N each". 'Eight' has no opened document.
- CF-DB05-W-R2_SC_COMM-R2-7 (LEROS 1b thrust) PARTIALLY_RESOLVED: NASA's 2011 Juno launch press kit p.15 gives the
  flown engine as 645 N against Nammo's catalogue 635 N; DB-0's 640 N is still unopened. Unresolved: 95 → 93.
- Dead ends: L3Harris re-hosted datasheets (2023-07, 2024-02, 2024-07, 2024-10, 2025-05 biprop; 2023-07, 2025-10 mono)
  all return 404 to curl and WebFetch on 2026-10-29, so SPACECRAFT-5..8 stay open (search snippets are not evidence).
  NTRS has no AJ26/NK-33, VR900, SuperDraco, Delphin or LEROS documents by title; no IM-1 press kit or ELDO history
  PDF was found; the IHI satellite-propulsion page returns 404.

### Pass: Goddard date and YF-23 verniers (2026-10-29)

- CF-DB05-W-US_HIST-21 (Goddard first flight) CONFIRMED_SECONDARY: NASA's history article (2021-03-17) prints
  16 March 1926; DB-0's 18 March had no recorded source.
- CF-DB05-W-ASIA_OTHER-7 (YF-23 thrust) PARTIALLY_RESOLVED, different_variant: CALT's LM-3C (1998) and LM-2E (1999)
  user's manuals (GlobalSecurity mirror, Table 2-1 p.2-2) give the four DaFY21-1 verniers 11.8 kN each (47.2 kN
  DERIVED) at 2910.5 / 2834.11 N.s/kg, while the CZ-2D table gives 46.1 kN at 2762 N.s/kg. Not a transcription slip.
  Unresolved: 93 → 91.
- Dead ends: the STS-104 FRR chart mirror (corpora.tika.apache.org) no longer resolves; NTRS 20030005845 (STS-104
  shutdown surge, AIAA 2002-3581) has no HPFT discharge temperatures. Isaev (kbhmisaeva.ru) and Energia sites give no
  connection. NASA's own Goddard biography URLs return 404. GlobalSecurity mirrors no LM-2C/2D/4 manuals; LM-3A/3B
  chapters add nothing for an open conflict. One jdse request (DOI ...20210012, CZ-5 booster) gives 2 400 kN for two
  YF-100, consistent with R2A-15.

### Pass: AJ26-62 and Vulcain 2.1 (2026-10-29)

- CF-DB05-W-R2_SC_COMM-R2-18 (AJ26-62 vacuum thrust) PARTIALLY_RESOLVED, different_operating_point: Orbital's Antares
  OSP-3 User's Guide Release 1.1 (July 2013, approved for public release; read from the manualsdir.com mirror,
  section 2.2.1) gives about 3,630 kN total vacuum thrust for two engines (1,815 kN each DERIVED) and a 58-108 %
  throttle range; 1,815 / 1,680 = 1.080 DERIVED, consistent with the Korean 1,680 kN being the 100 % rating, but not
  printed as such.
- CF-DB05-W-EUROPE-6 (Vulcain 2.1 thrust) RESOLVED: ESA's 'The engines of Ariane 6' page (05/06/2024) prints 1371 kN.
  The 1,340 kN and 135 t are not on their fetched pages. Unresolved: 91 → 89.
- Looked at, no change: a 2015 Via Satellite report gives NewtonFour 'capable of 5,000 lbf' (news, not the maker), so
  R2-20 stays open; the Ariane 6 User's Manual Issue 2 (2021) and ESA's 2023 Ariane 5 media kit print no Vulcain 2.1
  thrust, Aestus or HM7B chamber pressure.

### Pass: Gemini launch vehicle chamber pressure (2026-10-29)

- CF-DB05-LR87-7-PC PARTIALLY_RESOLVED: Martin's 1964 Gemini Launch Vehicle paper (LaFrance, NTRS 19720063749) p.10
  sets the chamber-pressure switches at 68 % of Stage I rated thrust, 'equivalent to 550 psia'; the Stage I rated
  chamber pressure is therefore about 809 psia (55.8 bar) DERIVED if pressure scales with thrust, which does not
  support the 47 bar LR87-7 entry. The paper names no engine model. Unresolved: 89 → 88.
- Dead ends: jdse CZ-5 papers DOI ...20210021 (Φ5 m structure; needed a 500 s download, first try truncated) and
  ...20210012 (boosters) give no YF-77/YF-75D data; jdse requests stopped for this session. NTRS 20090014109 (Ares V and
  RS-68B, JANNAF 2008) gives RS-68B 797 klbf vac / 414.2 s but no RS-68A chamber pressure.

### Pass: BT-4, Longyun and Agnilet (2026-10-29)

- CF-DB05-W-R2_SC_COMM-R2-4 (BT-4 thrust) PARTIALLY_RESOLVED, different_variant: the encyclopedia article, now read
  (current revision), lists BT-4 (450N), BT-4 (500N) and a 450 N Cygnus unit; its infobox shows the 500 N variant.
- CF-DB05-W-R2_ASIA-R2A-30 (Longyun thrust) EXPLAINED: Jiuzhou Yunjian's product page prints 海平面推力70吨 and
  真空版推力80吨, so the news pages' 70 t and 80 t are the maker's sea-level and vacuum-version figures.
- CF-DB05-W-R2_ASIA-R2A-22 (Agnilet thrust) PARTIALLY_RESOLVED: Agnikul's Agnibaan page gives Agnilet '6.2kN thrust
  capacity'; the 2024 '~3 kN at sea level' has no maker document. Unresolved: 88 → 85.
- Dead ends: Blue Origin engine pages still 429 (one retry); Skyroot's site has no Dhawan page (/dhawan 404); NTRS has
  no V-2/A-4 engine documents by title.
- Further dead ends (2026-10-29): Intuitive Machines site redirects with no body (VR900); astra.com covers Rocket 4
  only (no Delphin data); launcherspace.com (now Vast) prints no E-2 figures; rocketlabcorp.com engine pages now
  return 403 (Archimedes, Rutherford); no primary YF-115 document found. Remaining UNRESOLVED (85) are blocked on
  these hosts, on Russian bureau sites (no connection), Blue Origin (429), L3Harris (404), SpaceX (script-only), or
  are definition conflicts awaiting the owner (RS-25, F-1, RD-170, RD-180).

### Pass: Tronador II (2026-10-29)

- CF-DB05-E-R2_ASIA-R2A-26 (MT-B propellants) EXPLAINED, different_epoch: the Argentine government's Tronador II
  programme page gives a pressure-fed MMH / N2O4-nitric acid upper stage, and its 1 August 2023 release tests a
  LOX / kerosene prototype of the final second-stage engine.
- CF-DB05-E-R2_ASIA-R2A-27 (VEx-1A date) PARTIALLY_RESOLVED: iProfesional's report of 5 March 2014 dates the failed
  launch to Wednesday 26 February 2014; the government programme page says 'marzo del 2014'. Unresolved: 85 → 83.
- Dead end: ESA's HSR histories cover ELDO's founding, not Coralie/Astris figures.
- Correction: the OTRAG pass (317112a) used NASA TM-75376, a translation of a Der Spiegel article, as a source. The
  research rules forbid translation sources (test_original_language_and_gloss_are_kept_apart), so it was reverted in
  1a1cad2; CF-DB05-E-R2_ASIA-R2A-33 stays UNRESOLVED (83). Lesson: a NASA TM/TT 'translation of ...' cannot be cited.
- Housekeeping: data/source_registry.csv, regenerated by build.py, had not been committed since acabcdf; it now
  carries this session's 15 new sources.
- More dead ends (2026-10-29): khrunichev.ru gives no connection and roscosmos.ru 403 (RD-191); NTRS has no RD-191,
  RD-181, Angara, Merlin 1D, Falcon 9 engine or Raptor documents by title; CNES/ESA history searches gave only
  encyclopedia mirrors for Vexin/Coralie/Astris.

### Pass: archived maker pages (2026-10-29)

Read the current encyclopedia revisions DB-0 knew only from search summaries and followed their citations to maker
material in Internet Archive captures (the live pages are gone or script-rendered).

- CF-DB05-W-R2_SC_COMM-R2-20 (NewtonFour) RESOLVED: Virgin Orbit's LauncherOne Service Guide v2.1 (August 2020) and
  its technology page give 5,000 lbf; the 'about 6,000 lb' news figure has no maker source.
- CF-DB05-W-COMMERCIAL-COM-4 (Merlin Vacuum Isp) RESOLVED: SpaceX's Falcon 9 page (capture of 2018-02-08) gives a
  vacuum Isp of 348 s.
- CF-DB05-W-R2_SCHEM-R2-9 (Merlin 1D throttle) PARTIALLY_RESOLVED, different_epoch: the 2015 Falcon 9 user's guide
  gives 170,000 to 119,000 lbf at sea level (70 % DERIVED); SpaceX's chief executive wrote '~40% of 1 Merlin' in May
  2016. The aggregator's 57 % has no source. Unresolved: 83 → 80.
- No change from the other revisions read: the Rotary Rocket article prints no chamber count (TAX-7); the XLR11
  variant list has no RM-3 (US_HIST-08); the BMW 109-718 article gives 1,250 kg both for the combined 003R unit and
  the rocket (EUROPE-22); YF-115 176.5 kN is marked 'citation needed' (ASIA_OTHER-12); the YF-40 article lists two
  chambers at 103 kN (ASIA_OTHER-8). Encyclopedia text is not evidence, so these stay open.

### Pass: archived datasheets and releases (2026-10-29)

Read Internet Archive captures of maker documents whose live URLs return 404 or 429. blueorigin.com itself was not
contacted again; only web.archive.org captures were read.

- L3Harris sheets: CF-DB05-E-SPACECRAFT-7 (MR-103J) and -8 (MR-111G) EXPLAINED, different_epoch (the 2023 and
  October 2025 editions both read; the ranges changed between them). SPACECRAFT-5 (R-42, 4.53 kg) and -6 (R-40B,
  10.5 kg) PARTIALLY_RESOLVED: the June 2023 and February 2024 sheets agree; the July 2024 sheet with the heavier
  masses has no capture. CF-DB05-E-R2_SCHEM-R2-10 (R-4D-11) PARTIALLY_RESOLVED: 311 s at 164:1, 315.5 s at 300:1.
- CF-DB05-E-TAXONOMY-TAX-6 (Delphin) RESOLVED: Astra's 2020 press kit gives 6,300 lbf SL per engine, 31,500 for five.
- BE-4 (CF-DB05-E-COMMERCIAL-COM-9, CF-DB05-E-ANCHOR_US_MODERN-1, CF-DB05-W-R2_SCHEM-R2-5) EXPLAINED, different_epoch:
  550,000 lbf SL from the 2014 announcement; Blue Origin's 20 November 2025 release calls it the existing capability
  and announces 640,000 lbf with subcooled propellant.
- BE-3U (COM-10, ANCHOR_US_MODERN-2) EXPLAINED, different_epoch: 160,000 lbf design, 173,000 lbf for NG-1 (2024),
  200,000 lbf per engine announced 2025. ANCHOR_US_MODERN-3 (cycle) EXPLAINED, definition: the maker uses both
  'open-expander' and 'expander bleed'.
- Unresolved: 80 → 68. Not captured: L3Harris July 2024 bipropellant sheet, RS-68A data sheet (arsuppliernet).

### Pass: archived museum records and a 1947 thesis (2026-10-29)

- CF-DB05-E-R2_USSR-R2-10 (V-2 propellant consumed) PARTIALLY_RESOLVED, definition: the two Smithsonian records give a
  60 s burn and name different quantities (about 9,700 kg of liquid oxygen alone; nearly 9,000 kg of both
  propellants). Read literally they contradict each other; neither cites a source.
- CF-DB05-E-R2_SCHEM-R2-13 (V-2 load mass) is now filed, UNRESOLVED: it had no source id before; the Smithsonian
  record now supplies one for the 9,700 kg LOX claim. Conflicts filed: 254 → 255.
- CF-DB05-E-US_HIST-14 (WAC Corporal fuel) PARTIALLY_RESOLVED: a 1947 GALCIT engineer's thesis says RFNA and aniline.
- CF-DB05-E-EUROPE-24 (HWK 109-507) PARTIALLY_RESOLVED, different_operating_point: the Smithsonian gives 600 kg at
  ignition falling to 400 kg over the 10 s burn.
- CF-DB05-W-EUROPE-26 (Super Sprite) PARTIALLY_RESOLVED: the Smithsonian gives 4,200 lb maximum for 40 s, adjustable.
- Unresolved: 68 → 65. No archive capture exists for the STS-104 FRR chart mirror (RS-7), the SpaceX Starship
  specification page (R2-3) or the newspacetracker page (VR900).
- 2026-10-29: CF-DB05-W-R2_USSR-R2-9 (V-2 peroxide) stays UNRESOLVED; the Smithsonian V-2 record confirms the 27 %
  sodium permanganate Z-Stoff but no peroxide concentration, and v2rockethistory.com serves a bot check (not
  bypassed). Dead end: the ILS Proton Mission Planner's Guide Rev 7 (July 2009, archive captures of sections 0, 1,
  2, A) gives the Breeze M 14D30 19.62 kN vacuum thrust and the RD-0213 583 kN, but no 14D30 Isp, so the S5.98M Isp
  conflicts (R2_USSR-R2-18, R2_SC_COMM-R2-11) stay open. Sites answering 403 or a bot check were not read through
  the archive either.
- More dead ends (2026-10-29): skyroot.in (current site) prints no Dhawan-1 figures (R2A-23); intuitivemachines.com
  still answers 302 with no body and has no archived propulsion page (VR900, R2-5); energomash.ru is an unrelated
  boiler maker (Belenergomash), and NPO Energomash's own site stays excluded under the 403 rule; jdse was not
  contacted again this session. Unresolved stands at 65 of 255 filed; the rest wait on owner definition decisions
  (RS-25, F-1, RD-170, RD-180, LE-7/LE-7A epochs, Vulcain) or on sites that refuse access.
- Further dead ends (2026-10-29): the Ariane 5 User's Manual Issue 5 Rev 3 (June 2020, archive capture) gives HM7B
  67 kN / 446 s and Vulcain 2 960 / 1390 kN but no chamber pressures (HM7B, Aestus stay open); no archived Ariane 4
  manual was found; NTRS has no HM7, Aestus, Vulcain, ELDO or XLR11 documents by title; energia.ru, khrunichev.ru,
  kbhmisaeva.ru and npoenergomash.ru give no connection, engine.space answers 403, samspace.ru fails TLS
  verification (not bypassed). The HWK 109-509 wire-mesh sentence traces to a 1998 book (Stuewe) not available
  here. A paywalled trade article (Aviation Week 2011, Merlin 1D 1,410 psi) was not read through the archive.
- CF-DB05-W-ASIA_OTHER-12 (YF-115 vacuum thrust) PARTIALLY_RESOLVED, rating_or_rounding (2026-10-29): the IAC-16
  brief from the developing institute now delivers text and calls the YF-115 a '180KN' engine (a class name);
  Spaceflight101's 2015 report (archive capture) gives 17,850 kgf; the encyclopedia's 176.5 kN is marked 'citation
  needed'. Unresolved: 65 → 64. Dead ends: Intuitive Machines' VR900 qualification release (July 2024) is only on
  sites answering 403 (investors site, GlobeNewswire, StreetInsider, SatNow); Rocket Lab's 2024 Archimedes release
  (up to 202,300 lbf) adds nothing beyond the two maker pages already filed (COM-14); Dhawan-1 news pages give no
  figure beyond the 1.5 kN vacuum already filed.
- Dead ends (2026-10-29, late): IAC abstracts from the Chinese developers (IAC-13 x17679 and x18525, IAC-15 x28419,
  IAC-17 x41861) give the YF-77 700 kN vacuum at O/F 5.5 and name the YF-100 a 1200 kN engine, but no YF-77 Isp or
  sea-level thrust, no YF-75D burn time and no YF-100 throttle range; three of the brief PDFs answered 403 (not
  retried). Current encyclopedia revisions of KVD-1, RD-58, RD-191, RD-216, RD-270 and S5.98M add nothing citable;
  the RD-58 article's 11D58MF reference (ecoruspace.me, an enthusiast database, archive capture 2021-12-29) gives
  5000 kgf / 372 s but no cycle wording, so CF-DB05-W-R2_USSR-R2-20 stays open.

## Pass 2026-10-30: owner decision on RS-25 sea-level thrust; Roton maker site

- Owner decision of 2026-10-30: CF-DB05-RS25-SLTHRUST stays withheld. The 418,000 lb at 109% (L3Harris sheet) is
  not released; the RS-25 sea-level thrust stays excluded until a rated-thrust table by block is found. Resolution
  unchanged (UNRESOLVED); recorded in `tools/ledger_rs25b.py`.
- CF-DB05-W-TAXONOMY-TAX-7 (Roton combustor count) still UNRESOLVED: the Rotary Rocket Company's own 1998 site
  (archive captures of 1998-01-26, SRC-DB05-ROTARYROCKET-SITE-1998) describes a December 1997 hot-fire of one
  combustor module and says the final engine 'will have groups of these around a rotating hub', with no count; the
  2000 site says the engine will be derived from Fastrac. The 192 still has no source.
