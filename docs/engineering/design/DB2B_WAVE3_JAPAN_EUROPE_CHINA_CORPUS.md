# DB-2B Wave 3 — Japan / Europe / China reference-engine expansion

Status: PARTIAL. Every target was evaluated honestly. One configuration ships; everything else is research
evidence withheld by the frozen gates. The owner's decisions of 2026-10-12 (below) keep it withheld.
Baseline: `1265486` (DB-3A). Branch `claude/sweet-volta-55s7ii`.

Frozen and unchanged: the DB-1 schema; source, rights and conflict admission; value-kind and Missing
semantics; the text-basis, excerpt and mixture-ratio gates; the owner mechanisms; topology provenance; the
number matcher; and the DB-3A presentation contract. No gate was added or loosened. Wave 3 itself made
no owner decision. The owner's decisions of 2026-10-12 are recorded literally in `OWNER_REVIEWS`; none
releases a value, `OWNER_DECISIONS` is empty, and no conflict carries `owner_accepted` or `owner_released`.

Two instruction files named by the task are not in the repository and were not fabricated:
`CLAUDE_OPUS_5_5_REPO_INSTRUCTIONS_v4` and `grafify_rocket_forge_prompt.txt`.

## Outcome per target

| Target | DB-0 engine | Outcome | Why |
|---|---|---|---|
| LE-7 | ENG-JP-LE-7 | PROMOTED_PARTIAL | Architecture only (cycle, propellants) from a US 1990 review, NTRS public use. |
| LE-7A | ENG-JP-LE-7A | RIGHTS_BLOCKED (owner decision Q1) | NASDA's 1997 table needs a rights review; JAXA and MHI are restricted. |
| LE-9 | ENG-JP-LE-9 | RIGHTS_BLOCKED | Restricted: JAXA terms, IAF ©, AIREX ©, MHI ©. |
| Vulcain | ENG-FR-VULCAIN | WITHHELD (owner decision Q2) | The 1990 NTRS briefing table sits in an open epoch conflict; ESA is restricted. |
| Vulcain 2 | ENG-FR-VULCAIN-2 | RIGHTS_BLOCKED | Only ESA pages state it (non-commercial terms). |
| Vinci | ENG-FR-VINCI | RIGHTS_BLOCKED | ESA and IAF; EUCASS and Safran returned 403. |
| YF-75 | ENG-CN-YF-75 | RIGHTS_BLOCKED | IAF © abstract only. |
| YF-75D | ENG-CN-YF-75D | RIGHTS_BLOCKED | IAF © abstract only. |
| YF-100 | ENG-CN-YF-100 | RIGHTS_BLOCKED | IAF © abstracts; BIT Press © journal. |
| Target 7: YF-77 | ENG-CN-YF-77 | RIGHTS_BLOCKED | IAF © abstracts (BAPI authors). |

## Target 7 selection

Only engines already in the DB-0 registry with at least one Tier A/B source were considered:

- YF-77 (IAC-13 abstract by BAPI);
- YF-115 (IAC-16, XAPI);
- the Chang'e-3 7500 N variable-thrust engine (a SCIENTIA SINICA paper with no URL in the registry);
- the FY-25, TQS492-2 and third-generation 490 N apogee engines (IAF);
- the commercial TH-12, TH-12V and Welkin engines (company pages).

**YF-77 was chosen.** It is the CZ-5 core-stage LOX/LH2 gas-generator engine, a 50-ton-class core engine
where every other Chinese target is either an upper-stage engine (YF-75, YF-75D) or a LOX/kerosene engine
(YF-100). DB-0 also records YF-75 as a gas-generator engine, so YF-77 adds the core/booster scale of that
cycle, not a new cycle. Its abstract by the developing institute was reachable, and it is not a derivative.

The others were not chosen for these reasons:

- YF-115 duplicates YF-100's cycle (an upper-stage LOX/kerosene staged-combustion engine).
- The apogee engines are pressure-fed, so they add little architecture.
- The 7500 N paper was not reachable.
- The company pages (TH-12, TH-12V, Welkin) carry no technical document.

The choice did not change the outcome: YF-77 is RIGHTS_BLOCKED.

## Source ecosystems, languages and translation

- **Japan.** NASDA material hosted by MEXT, JAXA committee material and press pages, the JAXA repositories
  (AIREX, jaxa.repo), MHI product pages and Technical Review, IAF abstracts, and one US NTRS review (1990).
  Language: Japanese and English.
- **Europe.** ESA pages (2004, 2005, 2024 and an undated retrospective), CNES (French), IAF abstracts by
  ArianeGroup and Snecma, a DLR news item, a US patent, and one US NTRS briefing (1990).
- **China.** IAF abstracts by the Beijing (BAPI) and Xi'an (XAPI) propulsion institutes, and one
  peer-reviewed paper in 深空探测学报 (in Chinese). DB-0's Chinese secondary sources are encyclopaedic
  (Baidu, Bilibili and others) and stayed discovery-only.

Translation method:

- Japanese and Chinese statements are recorded as printed, in the original language. Each research note
  carries a gloss that is labelled "RocketForge reading gloss, not a translation source".
- No machine translation was used as a source or as corroboration. No translated document exists among the
  sources.
- Scanned or font-mangled pages (the NASDA 1997 scan, the IHI paper) were read from rendered page images
  and noted per record. One reading was corrected from the image: the preburner gas temperature is 810 K,
  not the OCR's 840 K.
- Qualifiers the original does not print stay missing. 混合比 (mixture ratio) without a direction, an Isp
  row without an environment, and 燃焼圧力 (combustion pressure) without a station are recorded as UNSTATED.
  A test proves the direction gate refuses an "O/F" a translator might add.

## Rights

The frozen rights gate admits a value only from a source whose host statement permits public use (the NTRS
determinations) or which has no host statement, and which carries no restrictive printed notice. Results:

| Source | Host / notice | Outcome |
|---|---|---|
| NTRS 19910018905 (Merkle, Penn State, 1990) | NTRS GOV_PUBLIC_USE_PERMITTED; no notice | Ships (B, SECONDARY); rights reading owner-reviewed 2026-10-12 (Q4) |
| NTRS 19910018907 (Rice, Orbital Technologies, 1990) | NTRS GOV_PUBLIC_USE_PERMITTED; no notice | Shippable source; its Vulcain table is held by a conflict |
| NASDA 委12-6 (1997) on mext.go.jp | MEXT terms (CC BY 4.0-compatible) exclude third-party content; NASDA is a third party | Not cleared for shipping (owner, Q1) |
| JAXA 資料37-3 (2017), JAXA H-II page | JAXA Terms of Use: press, research, education or private use only | Restricted |
| IHI技報 57(3) in AIREX | "items protected by copyright unless otherwise indicated" | Restricted |
| MHI product pages and Technical Review | © MHI | Restricted |
| ESA pages | personal non-commercial use; no redistribution | Restricted |
| IAF abstracts | © IAF, all rights reserved | Restricted |
| 深空探测学报 2021 | © Beijing Institute of Technology Press | Restricted |

No figure ships. The one schematic viewed (LE-9 engine cycle, IHI技報 Fig. 2, a reproduction credited to
the paper's reference) was not transcribed. Its rights are restricted, and it is a 2017 development-era
figure.

## Conflicts (none averaged, chosen or resolved by translation)

| Conflict | Resolution | Decision |
|---|---|---|
| CF-DB05-LE7-EPOCH (1990 development 265,000 lbf / 451 s vs NASDA 1997 110 tonf / 445.6 s) | UNRESOLVED | Withhold; the table-mates wait for the owner |
| CF-DB05-LE7A-EPOCH (1997 development spec vs 2017 / MHI figures) | UNRESOLVED | Withhold (all restricted) |
| CF-DB05-LE9-THRUST-LEVEL ("1 500 kN level" vs 1 471 kN in the same paper) | EXPLAINED | Nothing ships |
| CF-DB05-VULCAIN-THRUST (1025 kN, June 1990 pre-growth, vs ESA's "115 tonnes ... initial version") | PARTIALLY_RESOLVED | Withhold; the table-mates wait for the owner |
| CF-DB05-VULCAIN-TURBOPUMPS (speeds and powers, 1990 vs ESA) | UNRESOLVED | Withhold |
| CF-DB05-VINCI-EPOCH (2005 target "18 tonnes ... 465 sec" vs 2024 "180 Kn") | UNRESOLVED | Withhold |

## Production dispositions

The 111 Wave 3 research assertions break down as follows:

| Disposition | Count | What it covers |
|---|---|---|
| Promoted | 3 | LE-7 oxidizer, fuel and cycle (NTRS 19910018905 p.16) |
| WITHHELD_RIGHTS | 82 | |
| WITHHELD_CONFLICT | 7 | LE-7 thrust and Isp; Vulcain thrust and turbines |
| OWNER_DECISION_REQUIRED | 14 | The LE-7 p.18 table-mates and the Vulcain p.10 table-mates |
| DUPLICATE | 3 | LE-7 p.18 cycle and propellants (p.16 carries them) |
| MISSING_REQUIRED_SEMANTICS | 1 | The 1990 Vulcain "first firing" dates, a schedule at the time of writing |
| NOT_NEEDED | 1 | |

Only existing dispositions are used. Numeric figures in the two 1990 US reviews are a third party's summary
of the developer's numbers. They are not carried, as Rockwell's RD-170 transcriptions were not (the Wave 2
owner decision).

## Capabilities of what ships

`CFG-LE7-H2-1990-REVIEW`, "LE-7, H-II first-stage engine as a US panel described it in June 1990":

| Capability | Status |
|---|---|
| IDENTITY | SUPPORTED (effectivity NOT_AUDITED) |
| ARCHITECTURE | SUPPORTED (LOX/LH2, STAGED_COMBUSTION with no rich side) |
| PERFORMANCE_REFERENCE | NOT_SUPPORTED |
| TOPOLOGY | NOT_SUPPORTED |
| REGRESSION_CANDIDATE | NOT_SUPPORTED |

Intentionally missing: every LE-7 performance value, its mixture-ratio direction, its Pc station and its Isp
environment.

## Owner decisions (2026-10-12)

Recorded word for word in `tools/reference_engines/db2b_wave3_manifest.py`, `OWNER_REVIEWS`. They release
nothing, and the DB-0.5 conflict history is not rewritten.

| Question | Key | Decision |
|---|---|---|
| Q1 | `WAVE3-MEXT-NASDA-1997` | DO NOT CLEAR FOR SHIPPING. MEXT hosting is not sufficient evidence of redistribution permission; values, tables and figures stay withheld without explicit rights evidence. |
| Q2 | `WAVE3-1990-TABLE-MATES` | KEEP WITHHELD. No `owner_released`; the 1990 review sources remain secondary evidence. |
| Q3 | `WAVE3-1990-SECONDARY-VALUES` | KEEP WITHHELD FROM PRODUCTION PERFORMANCE; preserved in research with provenance and conflicts (the RD-170 precedent). |
| Q4 | `WAVE3-NTRS-RIGHTS` | ACCEPT the rights reading of `SRC-DB05-NTRS-19910018905` as Owner-reviewed 2026-10-12: a RocketForge shipping-policy review, not a legal determination. Tier (B), authority and primacy (SECONDARY) and every per-content policy are preserved. |

`SRC-NTRS-19910018907` ships nothing, so the Q4 review names only the shipped source.

## Owner questions as asked (before the decisions)

**Q1 — NASDA 1997 table on mext.go.jp** (`SRC-MEXT-SAC-1997`, AS-DB05-JP-LE-7-015…022 and
AS-DB05-JP-LE-7A-001…011).

- The MEXT terms declare numeric data not subject to copyright, and are CC BY 4.0-compatible for the
  State's content. NASDA's paper is third-party content under those terms.
- Choices: (a) keep withheld; or (b) accept a values-only reading.
- If (b): the rights block lifts, but that alone releases nothing that is also held by a conflict. The
  LE-7 1997 thrust, mixture ratio and Isp (LE-7-015…017) are claims of CF-DB05-LE7-EPOCH. The LE-7A 1997
  thrust, Isp and length are claims of CF-DB05-LE7A-EPOCH. Those need the owner's conflict decision as well.
  The rest of each table (turbopump speeds, preburner temperature, dimensions) is printed with those
  withheld claims, so it ships only with an `owner_released` under the matching conflict decision (the same
  mechanism as Q2), not from the rights decision alone. The LE-7A values
  would be DESIGN_VALUE for a development configuration. The mixture ratios stay withheld (no direction
  printed), and Isp stays environment-UNKNOWN.

**Q2 — 1990 US briefing tables held by open epoch conflicts.**

- Vulcain (CF-DB05-VULCAIN-THRUST): AS-DB05-FR-VULCAIN-001…004 and 006…009.
- LE-7 (CF-DB05-LE7-EPOCH): AS-DB05-JP-LE-7-008 and 010…014.
- Choices: (a) keep withheld; or (b) release named table-mates for a configuration the owner names.
- If (b): the Vulcain June 1990 development configuration could ship "System Uses Gas Generator; Separate
  LH2 and LOX Turbopumps" and LH2/LOX. The numeric figures would still be secondhand and withheld.

**Q3 (optional) — secondhand figures in the 1990 reviews.** These are kept withheld by the RD-170
precedent. The owner may confirm or revisit that precedent for these two documents.

**Q4 — rights reading of the newly shipped source.** The rights reading of `SRC-DB05-NTRS-19910018905` is
the author's: NTRS government public use and no printed notice, recorded as CONSISTENT. It is not
owner-reviewed. Every source shipped before Wave 3 carries an owner review (DB-2A, Wave 1, Wave 2).

- Choices: (a) accept the reading as owner-reviewed (recorded later as an `OWNER_REVIEWS` entry); or
  (b) withhold the source, and with it the LE-7 configuration.
- The same reading applies to `SRC-NTRS-19910018907`, which ships nothing now but would carry Vulcain's
  architecture under Q2(b).

## DB-3A consumer check

- The new configuration lists under family "LE-7" and is found by the search "le-7".
- It shows two supported and three not-supported capability cells, the five missing performance quantities,
  and an honest no-topology state.
- Its source is shown as "Authority B · Secondary".
- No European or Chinese record ships, so none appears; there is no original-language metadata in
  production.
- Visual check: 1920 light and 1366 dark, captures inspected, no warnings.
- The DB-3A zero-solve runtime test visits all 17 configurations with zero solves, zero probes, no file
  reads and no network.

## Research evidence (DB-0.5)

- Ledger: `docs/research/engine_database/db05/tools/ledger_wave3.py`.
- Totals: 111 assertions, 6 conflicts, 1 schematic viewed, 4 access blocks, and 1 page fetched without
  evidence (JAXA repository record 44968 renders only through scripts).
- New sources: `SRC-DB05-NTRS-19910018905` and `SRC-DB05-JDSE-2021-YF100`.
- Exploratory NTRS downloads that were never read (20090022131, 19920004056, 20080007517, 20160008869,
  20080008340, 20110015783) are leads only and are not evidence.
