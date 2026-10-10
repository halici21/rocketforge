# DB-2B Wave 2 — Difficult and international reference engine expansion

Wave 2 takes the reference corpus into seven targets whose evidence is
incomplete, variant-sensitive, access-limited, international or partly
proprietary: RL10A-4-2, RL10B-2, RD-170, IPD, RS-68A, LR87 and Rutherford.
Its point is to show that the frozen DB-1 and DB-2 admission rules hold
when sources are hard to find, so most records are sparse and two targets
ship nothing.

It is a curated, verified reference corpus, not a complete or worldwide
engine database.

**Status: see the final report of the Wave 2 change.** No owner decision
is recorded by Wave 2; the decisions it needs are listed below.

## Preflight: the text-excerpt rule

Before any Wave 2 work, the text-value excerpt rule introduced for the F-1
qualification life (607230d) was reviewed adversarially. It accepted any
substring of the printed text, so an excerpt could drop a negation,
"maximum", a configuration name, a value kind, "approximately", a ratio
direction or a parenthetical limit (7 of 8 cases shipped). It was fixed in
cc5c3dd: an excerpt is whole `;`-separated statements in printed order,
never drops a heading or a statement without its own value, applies to text
values only, and needs a recorded owner decision. No shipped value changed.
`cc5c3dd` is the frozen admission baseline for Wave 2. The independent review
later showed that a dropped statement which carries its own number but also
scopes the others ("Design limit 900 psia; Pc 800 psia") still passes the
mechanical checks; the recorded owner decision an excerpt requires is the
control for that case. Wave 2 uses no excerpt.

## Two phases

**Phase A — targeted evidence completion** (`db05/tools/ledger_wave2.py`).
Already-downloaded documents were read first, then registered leads, then a
narrow NTRS and web search. Every new document was downloaded through
`fetch.py` (hash, NTRS rights metadata) before it was read; search snippets
were used only to find documents. 55 assertions were transcribed with
locators (56 after the review supplement); one schematic was viewed and
transcribed (LR87AJ-11 Figure 6-20).

**Phase B — production promotion** (`tools/reference_engines/db2b_wave2_manifest.py`).
The frozen gates, merged with the DB-2A and Wave 1 manifests. Every DB-0.5
assertion of the eight Wave 2 engine ids (Rutherford has a sea-level and a
vacuum id) is promoted or given a disposition.

## What changed in the machinery

Nothing in the admission semantics. The promotion tool gained:

| Change | Why |
| --- | --- |
| The Wave 2 manifest joins the merged manifests | one corpus |
| Three component words mapped (`booster_pump`, `preburner_ox_rich`, `thrust_chamber`) | the RD-170 graph's vocabulary |
| Three dispositions (`SECONDHAND_MANUFACTURER_VALUE`, `INFERRED_ONLY`, `DISCOVERY_ONLY_SOURCE`) | reasons to withhold that the vocabulary had no word for; all three only withhold. No gate checks that they are used for what they name: a wrong one changes the accounting, never what ships |

One DB-0.5 record was restated: the rights wording of
`SRC-ULA-DIV-INAUGURAL` was re-checked on all 9 pages and written as a
finding of no notice ("copyright notice not printed" reads as a notice to the
frozen reader). The finding itself is unchanged.

The independent review corrected two research transcriptions: the RD-170
reconstruction (DB-0.5, 2026-10-08) was re-read against its figure — the fuel
line is labelled "FUEL", not RP-1; the LP fuel pump's return line rises from
the kick pump; no line joins the HP fuel pump and the kick pump (now an
omission); "turbine drive" is not printed — and the LR87AJ-11 turbine drives
its pumps through a gear train (report p.6-23), so those two edges are geared
drives.

## Targets

Capabilities are evaluated by `capabilities.py`, not set by hand.

| Target / configuration | Disposition | Considered | Promoted | IDENTITY | ARCHITECTURE | PERFORMANCE | TOPOLOGY | REGRESSION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RL10A-4-2 | RESEARCH_VERIFIED_BUT_NOT_SHIPPABLE | 10 | 0 | — | — | — | — | — |
| RL10B-2 (`CFG-RL10B-2-DIV`) | PROMOTED_PARTIAL | 14 | 5 | SUPPORTED | PARTIAL | PARTIAL | NOT_SUPPORTED | NOT_SUPPORTED |
| RD-170 (`CFG-RD-170`) | PROMOTED_PARTIAL | 12 | 3 | SUPPORTED | PARTIAL | NOT_SUPPORTED | PARTIAL (9 / 12, reconstruction) | NOT_SUPPORTED |
| IPD (`CFG-IPD`) | PROMOTED_PARTIAL (ACCESS_BLOCKED for the key papers) | 13 | 8 | SUPPORTED | SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED |
| RS-68A (`CFG-RS-68A`) | PROMOTED_PARTIAL | 6 | 3 | SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED |
| LR87AJ-11 (`CFG-LR87-AJ-11-T3E`) | PROMOTED_PARTIAL | 19 | 15 | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED (16 / 18) | NOT_SUPPORTED |
| Rutherford (sea level, vacuum) | RESEARCH_VERIFIED_BUT_NOT_SHIPPABLE | 14 | 0 | — | — | — | — | — |

The IPD count includes variant-level statements (`VAR-IPD`). Totals: 88
research assertions considered, 34 promoted; not promoted: 33 WITHHELD_RIGHTS,
5 WITHHELD_CONFLICT, 4 SECONDHAND_MANUFACTURER_VALUE, 4
MISSING_REQUIRED_SEMANTICS, 3 DUPLICATE, 2 WRONG_CONFIGURATION, 1
INFERRED_ONLY, 1 NOT_NEEDED, 1 DISCOVERY_ONLY_SOURCE. A test recomputes these.

Production after Wave 2: 16 configurations (3 DB-2A + 8 Wave 1 + 5 Wave 2),
152 assertions, 21 sources, 9 schematics, 8 topology graphs, no conflicts.
Every DB-2A and Wave 1 record is unchanged.

### RL10A-4-2

Every document that states it is copyrighted: the NRC 2006 compilation
(NAP 11780, "(c) National Academy of Sciences", the only source of its
values) and a Lockheed Martin conference paper (2002), which names the
variants by vehicle — RL10A-4-1A on Titan Centaur, RL10A-4-1B on Atlas
IIIA/IIIB, RL10A-4-2 on Atlas V (the –1B features plus Dual Direct Spark
Ignition) — but prints no RL10A-4-2 value. The L3Harris data sheet and the
AIAA vehicle guide are HTTP 404. NASA's RL10 transition paper covers only the
RL10A-3-3A/B, and the 1991 Pratt & Whitney viewgraphs the RL10A-4 (20,800 lb),
a different variant. The A-4-1/A-4-2 column ambiguity (CF-DB05-RL10A42-THRUST-ISP)
stays open. Nothing ships; no RL10A-3-3A value is filed under it.

### RL10B-2

The Boeing inaugural-launch paper (no notice): 24,750 lb thrust with no
environment printed, liquid oxygen and liquid hydrogen, an extendible
nozzle, used on every Delta IV. The NAP compilation is copyrighted, and its
unresolved 644/633 psia and 466.5/465.5 s pair (CF-DB05-RL10B2-PC-ISP) would
be withheld even if it were not. No cycle statement is in a shippable
source, so ARCHITECTURE is PARTIAL.

### RD-170

No manufacturer document was reached. The record rests on two secondary
sources (authority B, primacy SECONDARY): NASA MSFC's 1994 CFD analysis of
an RD-170 test ("a regeneratively cooled four-nozzle clustered engine which
burns Kerosene fuel with liquid oxygen") and the 1991 Rockwell briefing. The
display-placard values (740 t, 806 t, 308 s, 336 s, 250 kgf/cm²) are a
manufacturer's statement known only through Rockwell's transcription, so they
are withheld (SECONDHAND_MANUFACTURER_VALUE, and the chamber pressure is in a
conflict). Both mixture ratios stay withheld (UNRESOLVED CF-DB05-RD170-MR).
Rockwell's layout sentence ("1 turbopump assembly driven by 2 preburners
which feed 4 thrust chamber assemblies") is withheld because the frozen
conflict matcher reads the "2" of "kgs/cm2" as a number it shares with
CF-DB05-RD170-PC; the gate was not changed for it. The graph is Rockwell's
reconstruction from display photographs, kept as THIRD_PARTY_RECONSTRUCTION,
so TOPOLOGY is PARTIAL; its fuel line is "fuel", as drawn. The fuel is filed
as printed, "Kerosene", not RP-1.

### IPD

The NASA Stennis facility paper (2004) and the NGLT programme paper (2005):
a full-flow staged-combustion LOX/hydrogen demonstrator (AFRL, 1994; "currently"
Pratt & Whitney Rocketdyne and Aerojet, in 2005), with oxygen and hydrogen
turbopumps and preburners tested as components, installed at SSC E-1 in
October 2004, six start-sequence tests by 2005 reaching about 90% power at
the peak of a transient. The 250k-lb-thrust figure ships at variant level as
a design value from the NGLT paper, which prints it as the programme's goal;
the Stennis paper's "a 250K lbf ... thrust ... technology demonstrator" has no
design or goal word and is withheld. The workhorse
test articles' data (preburner, igniter) is not the engine and is not filed
under it. The DTIC and AFRL papers stay blocked (HTTP 403) and two NTRS
records are abstracts only. No schematic was reachable, so there is no graph:
the cycle name does not make one.

### RS-68A

NASA MSFC's Ares V paper describes the RS-68A against the RS-68: 39,000 lbf
more thrust from three-dimensional turbine nozzles, more main-injector
elements for specific impulse, and reliability changes. The configuration is
the RS-68A as that paper describes it, and these ship as its text, never as
RS-68A values. A NASA launch-day blog gives identity (three common booster
cores on the Delta IV Heavy) and "702,000 pounds of thrust" with no
environment; a blog is authority E under DB-1, discovery only, so nothing
ships from it, and its thrust is also in a conflict with a manufacturer figure
seen only in a search excerpt (705,000 lbf sea level, data sheet HTTP 404). No RS-68 value is carried. No
shippable source states the RS-68A's propellants or cycle for the A model,
so ARCHITECTURE is NOT_SUPPORTED.

`CFG-RS-68A` is IDENTITY SUPPORTED on what NASA MSFC printed about it: here
IDENTITY means "described by an opened source", not "built or flown in this
configuration" (its effectivity is not audited).

### LR87

Only the LR87AJ-11 is supported by an opened document: General Dynamics
Convair's Titan IIIE/Centaur D-1T systems summary (1973). Rated thrust
520,000 lb (environment not printed), rated vacuum Isp 301.1 s, Aerozine 50
and nitrogen tetroxide, regeneratively cooled and turbopump fed, gas
generators fed from the pump discharge, a pair of identical subassemblies,
flows 1,727 / 1,135 / 592 lb/s, a 165 s operating cycle (the engine's
rating; the Titan IIIE burn is about 146 s) and a 15:1 expansion ratio. The
turbine drives the pumps through a gear train. Its "Mixture Ratio 1.915" prints no direction and is withheld; "over
800 psia" is a bound and is withheld. The fill-and-bleed schematic (Figure
6-20) is the graph of one subassembly, with the other listed as an omission.
No other LR87 variant is carried, and no value crosses between variants or
to the family.

### Rutherford

Rocket Lab's press kit (2017), two releases (2018, 2020) and the Electron
page were read: liquid oxygen and kerosene, electric pumps (brushless DC
motors and lithium polymer batteries), 3D-printed primary components, nine
sea-level engines and one vacuum engine; thrust changed between the 2018
and 2020 statements (two epoch conflicts recorded). Every one of these
documents carries a Rocket Lab copyright, so nothing ships, and no topology
is drawn from "electric-pump-fed".

## Rights limitations

Records poorer than the research because of rights: RL10A-4-2 (NAP, Lockheed
Martin), RL10B-2 performance (NAP, ULA booklet), RS-68A (ULA and L3Harris
material not opened), Rutherford (Rocket Lab). Rights readings for the seven
Wave 2 sources that ship are the author's (checked 2026-10-10, recorded per
source); none is owner-reviewed.

## Owner decisions required

Wave 2 records none. These are withheld until the owner decides:

1. **RS-68A thrust** (CF-DB05-RS68A-THRUST; AS-DB05-US-RS-68A-002): NASA blog
   "Each engine produces 702,000 pounds of thrust" (no environment) against
   705,000 lbf sea level from a DB-0 search excerpt of the manufacturer data
   sheet (never opened). Choices: keep withheld (the blog is discovery only);
   or rule that this NASA blog may speak for the RS-68A as an agency source,
   which would admit 702,000 lb with environment UNKNOWN (PERFORMANCE becomes
   PARTIAL; regression stays NOT_SUPPORTED).
2. **RD-170 placard values** (AS-DB05-SU-RD-170-001..004): 740 t sea level,
   806 t vacuum, 308 s and 336 s, as Rockwell transcribed the 1989 display.
   Choices: keep withheld; or admit them as secondary values attributed to
   the placard (their DB-0.5 records carry no environment condition, so they
   would ship with environment UNKNOWN unless the transcription is
   corrected).
3. **Wave 2 rights readings** for the seven shipped sources (as given for
   Wave 1).
4. **Machinery additions and research corrections**: the three dispositions,
   the three component words, the restated rights wording of
   `SRC-ULA-DIV-INAUGURAL`, and the re-transcribed RD-170 reconstruction.
5. **The conflict matcher's unit-digit match** ("kgs/cm2"), which withholds
   Rockwell's RD-170 layout sentence: keep, or change the frozen matcher in a
   separate, reviewed change.

## Independent review

The final independent review ran after the last material change. The first
review found five material issues, all fixed with a regression test: the
RD-170 graph shipped an "RP-1" carrier no source prints; two RD-170 edges were
not as drawn; the LR87AJ-11 pumps were shown on a direct shaft where the
report prints a gear train; a NASA blog shipped with authority A; and the IPD
design value took its value from one document and its kind from another.
Minor items fixed: unsupported family notes (Energomash, LR87 propellants), the
dropped "Currently," of the IPD contractors, the RD-170 preburner argument, the
LR87 operating-cycle note, and tests pinning graph carriers and edge kinds.
The second review found no material issue; its minor items were fixed (the IPD
contractor note's 2005 epoch, the blog graded E in the research record, the
RD-170 feed arrow's ambiguity stated in its role, a test that the IPD goal
cannot become a tested-engine value) or documented (the kind gate does not
read "designing"; the new dispositions are not themselves checked; IDENTITY for
`CFG-RS-68A`).

## Not done, by design

No other engine was migrated (Merlin, Raptor, BE-3, BE-4, Vinci, Vulcain,
LE-7/LE-7A, LE-9, YF engines, RD-180/RD-191, the rest of DB-0). No regression
is accepted, no UI exists for the corpus, nothing is solved, and no record
designs an engine.

## Verified by

| Test file | What it holds |
| --- | --- |
| `tests/research/test_text_excerpt_gate.py` | the preflight: an excerpt cannot change meaning |
| `tests/research/test_db2b_wave2_promotion.py` | accounting and totals; no owner decision; RL10A-4-2 cannot pick a side of the A-4-1/A-4-2 columns and takes no RL10A-3-3A value; the RL10B-2 Pc/Isp pair cannot ship; the RD-170 reconstruction cannot be relabelled original and its mixture-ratio conflict cannot be normalised away; a cycle name cannot make a graph; a blocked source is not evidence; RS-68 wording and relative changes cannot become RS-68A values; LR87 values cannot cross variants or reach the family, and its ratio direction is not guessed; Rutherford values cannot cross sea level and vacuum and are refused for rights; the build is deterministic; Wave 2 adds only its targets; production code never names the research tree |
| `tests/evidence/test_reference_engine_wave2.py` | the shipped records: capabilities as evaluated, what each target carries and must not carry, the RD-170 and LR87AJ-11 graph carriers and edge kinds |
| Wave 1 and DB-2A tests | rescoped from "nothing else ships" to "their records are present and unchanged" |
