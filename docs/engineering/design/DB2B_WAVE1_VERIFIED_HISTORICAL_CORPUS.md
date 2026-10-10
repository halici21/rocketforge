# DB-2B Wave 1 — Verified historical corpus expansion

Wave 1 extends the DB-2A seed corpus with six historical engines, using the
DB-1 schema and the DB-2A promotion machinery unchanged in meaning. Its point
is to show that the strict promotion process scales to a mixed set of
historical records without loosening provenance, configuration scope, conflict
handling, rights, topology provenance or honesty about missing data.

It is a curated, verified reference corpus, not a complete historical engine
database. Several records ship sparse on purpose.

**Status: COMPLETE.** Every target was evaluated and every research assertion
of the six was given a disposition. No evidence rule was weakened; the
independent review's findings were fixed and each confirmed bypass has a
regression test. The owner's decisions of 2026-10-09 (below) are recorded and
applied.

## Research and production

Unchanged from DB-2A: research lives in `docs/research/engine_database/`,
production in one file, `rocketforge/data/evidence/engines/reference_engines.json`,
read by the existing catalog (`rocketforge/application/analysis/reference_engine_catalog.py`)
and nothing else. There is no second corpus file and no second catalog.

The file is built by `tools/reference_engines/promote_db2a.py` from two
manifests merged into one: `db2a_manifest.py` (the seeds) and
`db2b_wave1_manifest.py` (Wave 1). A key defined in both must be identical.
`--check` fails if the shipped file differs from what the manifests produce.
The DB-2A records come out of the merged build identical, item for item.

DB-0.5 gained thirteen supplementary transcriptions from documents it had
already opened (J-2S and F-1 viewgraph description blocks, the SA-10 H-1
propellants and gas generator, the OMS propellants), and ten more after the
review so that every passage a graph cites as its text basis is a ledger entry
(J-2, F-1 and SPS passages), all recorded in `db05/STATUS.md`. No new outside
source was used. DB-0.5 stays PARTIAL.

## Promotion: what changed in the machinery

DB-1 is unchanged. `admission.py`, `capabilities.py` and the catalog are
unchanged. The promotion tool gained these gates and capabilities, all
additive (the DB-2A part of the build is unchanged):

| Change | Why |
| --- | --- |
| Manifests merge; a key may not be redefined differently | one corpus from several reviewed manifests |
| `host = "NONE"` for a source with no repository statement (an ibiblio mirror, a nasa.gov download); then NTRS must have returned nothing | three Wave-1 sources are not NTRS records; their rights record keeps `host_metadata = Missing(NOT_REPORTED)` |
| The restrictive-notice check sets aside only the explicit finding "no copyright notice" (optionally "on the cover" or "on pages read"), and also recognises `(c)`, `©` and "all rights reserved" | DB-0.5 writes "no copyright notice on cover" for clean NASA documents; the old word match refused them, and a following "but … all rights reserved" must still count |
| Field-level conflict coverage: a promoted assertion of the same engine whose field the conflict names must be listed by the decision | a value can be in a conflict without being one of its recorded claims (FS-2025's 418,000 lb sea-level thrust) |
| `CONFIGURATION_SOURCES`: a configuration listed there takes values only from its sources | DB-0.5 files Shuttle Block II, SLS and fleet statements under one engine id |
| `NOT_PROMOTED` for Wave-1 engines is `(disposition, reason)`; each disposition is checked against what it claims | exact accounting; WITHHELD_CONFLICT must be withheld by a conflict decision, WITHHELD_RIGHTS must fail the rights gate |
| A graph's scope must be an identity of its engine; its schematics and text sources must be ones the DB-0.5 graph rests on | no J-2 graph under the J-2S, no development figure in the final LMDE graph |
| A schematic in a source whose figures are RESTRICTED_REFERENCE cannot carry a graph | the Boeing-proprietary SSME schematic |
| Restated omissions: only cut at a word boundary, or replaced by the one neutral wording "an element known only from a rights-withheld source (not recorded)" | DB-0.5 omissions that name what only MSFC-MAN-503 says |
| Withheld wording is checked per configuration, including graphs of units that contain it | LMDE graph is unit-scoped |
| Kind words may come from the locator, but a word inside a compound modifier ("maximum-rated thrust") does not count; a number printed under a design-requirements heading must be DESIGN_VALUE; sea-level environments map; "fuel-to-LOX" counts as a fuel-to-oxidizer mark; a `gg.` field states the gas-generator basis | design-requirement tables, sea-level Isp, the H-1 gas generator ratio, the LMDE fixed throttle point |
| A restatement that keeps a text basis names the DB-0.5 assertions that record that text (`text_basis`), from the graph's own text sources; each basis is from a page the restated locator adds, is not withheld, and holds the passage the reason quotes | review findings: the F-1 graph cited Biggs passages no ledger entry held; a J-2 restatement cited a Coffman sentence that was never transcribed (now J-2-033 and J-2-034); the DB-2A J-2 and SPS restatements name their bases (their shipped data is unchanged) |
| A performance, geometry or mass value, or one printed for a build or point, is not filed on a family or variant (a reading does not excuse it; only a programme requirement, DESIGN_VALUE, sits above the build), nor is a statement printed in the same place as a configuration's; a design requirement is never a configuration value, and a number printed under a requirements heading is DESIGN_VALUE whatever the reading; a propulsion unit carries only pressurization, feed or tank statements | review findings: build values could be filed on a family (J-2S thrust on the J-2 family); a reading escaped the rule; the Block IIA throat statement printed beside the Block II definition was filed on the RS-25 variant (now WRONG_CONFIGURATION) |
| A source withheld for scope (`rights=False`) must carry an unrestricted rights record | review finding: a restricted source could be relabelled as out of scope |
| OWNER_DECISION_REQUIRED, like WITHHELD_CONFLICT, must be withheld by a conflict decision; a value from a source refused for rights must carry WITHHELD_RIGHTS | review finding: the F-1 vacuum thrust could be promoted; a rights-withheld value could be relabelled NOT_NEEDED |
| `owner_accepted` must equal the decision recorded in `OWNER_DECISIONS`, the two DB-2A owner decisions written out as text, not derived from the conflicts it checks | review finding: an invented `owner_accepted` was guarded only by a test |
| "No copyright notice" is set aside only as an exact finding, and not when followed by but, except, although, however or yet | review finding: the earlier rule cut at the next punctuation |
| An open WITHHOLD conflict of DB-0.5 kind `different_epoch` (an unsettled rating epoch) withholds the whole table that prints its claim: every other value printed at the same source and locator ships only if the decision lists it in `owner_released` or another conflict's recorded owner decision carries it. A release needs the recorded owner decision, never covers a claim of the conflict, covers only values printed at the same source and locator as a withheld claim, and covers only values whose printed numbers (or printed text) appear in the owner's recorded words | the owner's F-1 decision admits the table's vacuum thrust and Isp while the sea-level rating stays withheld; post-change review: the release was not mandatory (with every owner record removed the values still shipped), and an id added to the release list shipped without the owner's words naming it |
| A recorded owner decision that names a configuration (`CFG-…`) binds every value it releases or carries to that configuration (`owner_scope`) | post-change review: nothing tied the F-1 values to `CFG-F1` beyond the manifest entry; a later F-1 configuration could have taken them |
| Every `OWNER_DECISIONS` entry must be the `owner_accepted` of its own conflict | post-change review: the same words recorded under an unrelated conflict passed |
| A rights note that claims an owner review ("owner-reviewed", "owner-approved", "approved by the owner" and the like) must belong to a source an `OWNER_REVIEWS` entry lists, every listed source must record the review, and only a shipped source can be listed | an owner review is recorded once, as text, and never upgrades a withheld source; post-change review: other wordings escaped the check |
| A mixture-ratio direction must be printed, or be in a DB-0.5 record the reading cites by id (same engine) or quotes (same source and page); the author's own words are not evidence | post-change review, a DB-2A-era rule: a reading saying "O/F" admitted the F-1 2.27 with a direction nothing prints. The SPS Block I reading's quoted TN D-7375 phrase was transcribed (AJ10-137-025); the RL10 reading cites AS-DB05-US-RL10A-3-3A-006. No shipped value changed |

## Targets

Capabilities are evaluated by `capabilities.py`, not set by hand.

| Configuration | Disposition | Considered | Promoted | IDENTITY | ARCHITECTURE | PERFORMANCE | TOPOLOGY | REGRESSION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J-2S (`CFG-J2S`) | PROMOTED | 24 | 13 | SUPPORTED | SUPPORTED | SUPPORTED | NOT_SUPPORTED | SUPPORTED (eligible only) |
| F-1 (`CFG-F1`) | PROMOTED_PARTIAL | 32 | 15 | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED (15 nodes / 19 edges) | NOT_SUPPORTED |
| H-1 188K, SA-10 (`CFG-H1-188K-SA10`) | PROMOTED_PARTIAL | 28 | 14 | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED (19 / 25) | NOT_SUPPORTED |
| LM descent engine, final (`CFG-LMDE-FINAL`) | PROMOTED_PARTIAL | 14 | 13 | SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | SUPPORTED (17 / 21, unit graph) | NOT_SUPPORTED |
| Shuttle OMS engine (`CFG-OMS`) | PROMOTED_PARTIAL | 14 | 9 | SUPPORTED | PARTIAL | PARTIAL | NOT_SUPPORTED | NOT_SUPPORTED |
| RS-25 original throat (`CFG-RS25-SMALL-THROAT`) | PROMOTED_PARTIAL | 2 | 2 | SUPPORTED | NOT_SUPPORTED | PARTIAL | NOT_SUPPORTED | NOT_SUPPORTED |
| RS-25 Block II, 2003 (`CFG-RS25-BLOCK-II`) | PROMOTED_PARTIAL | 44 (one DB-0.5 id) | 8 (with SLS) | SUPPORTED | NOT_SUPPORTED | PARTIAL | NOT_SUPPORTED | NOT_SUPPORTED |
| RS-25 SLS-adapted (`CFG-RS25-SLS`) | PROMOTED_PARTIAL | (as above) | (as above) | SUPPORTED | NOT_SUPPORTED | PARTIAL | NOT_SUPPORTED | NOT_SUPPORTED |
| RS-25 Block IIA | WITHHELD (rights) | 19 | 0 | — | — | — | — | — |

Totals over the six targets: 177 research assertions considered, 74 promoted;
not promoted: 46 WITHHELD_RIGHTS, 15 WITHHELD_CONFLICT, 14 NOT_NEEDED (four of
them the F-1 graph's recorded text bases), 10 MISSING_REQUIRED_SEMANTICS, 10
SOURCE_SCOPE_TOO_BROAD, 5 WRONG_CONFIGURATION, 1 OWNER_DECISION_REQUIRED, 1
WRONG_OPERATING_POINT, 1 DUPLICATE. A test recomputes these from the manifest.
(Before the owner's decisions: 71 promoted, 16 WITHHELD_CONFLICT, 3
OWNER_DECISION_REQUIRED.)

Production after Wave 1: 11 configurations (3 DB-2A + 8 Wave 1), 117
assertions, 14 sources, 7 schematics, 6 topology graphs, no conflicts.

### J-2S

The Rocketdyne "J-2S Basic Engine Features" viewgraph (NTRS 19940016798, the
1993 restart study): 265,000 lb nominal vacuum thrust, 436 s, 1,200 psia at
nozzle stagnation, engine mixture ratio calibration 5.5:1 (O/F), area ratio
40:1, dry weights, tap-off turbine drive cycle, pump-fed, liquid oxygen and
liquid hydrogen, regeneratively cooled. DB-0.5 has no J-2S graph, so none
ships, and the J-2 graph cannot be filed under the J-2S (a gate refuses it).
Timeline dates are withheld (PARTIALLY_RESOLVED conflict CF-DB05-J2S-DATES).

### F-1

Rocketdyne's "F-1 Engine Characteristics" and "Basic Features" viewgraphs
(Biggs, NTRS 20100027316): area ratio 16:1, pump-fed, LOX and RP-1,
gas-generator turbine drive, the engine graph, and, by the owner's decision of
2026-10-09, the "F-1 Engine Characteristics" table's vacuum thrust
(1,748,200 lb), sea-level and vacuum Isp (265.4 s, 304.1 s, basis unknown)
and chamber pressure (1,125 psia, station UNKNOWN). The owner accepted the
viewgraph as defining this source-scoped configuration; that is not a
canonical flight-rating epoch. The table's sea-level thrust stays withheld in
the UNRESOLVED rating-epoch conflict CF-DB05-F1-RATING, which releases the
other three only through its recorded owner decision; the chamber pressure is
carried in PARTIALLY_RESOLVED CF-DB05-F1-PC for `CFG-F1` only. None of these
values is filed on the F-1 variant or family. The 18,616 lb mass stays in
UNRESOLVED CF-DB05-F1-MASS. The same table's qualification life ("Starts 20;
Duration 2,250 seconds; mission duration 165 seconds", AS-DB05-US-F-1-010)
shipped in `3f8d02a` although that table's values were meant to wait for the
owner; the owner's decision does not name it, so it is now withheld as
OWNER_DECISION_REQUIRED. PERFORMANCE stays PARTIAL: no mixture ratio
with a direction is printed. The printed "Engine mixture ratio 2.27" has no direction
(O/F or F/O), so it is not shipped (MISSING_REQUIRED_SEMANTICS). The 1.8
million lb figure is the F-1A (Biggs's footnote). MSFC-MAN-503's F-1 values are
withheld for rights; the graph rests on the viewgraph and Biggs's text, with
the MSFC-only elements (stage pressurization tap, heat-exchanger order in the
turbine exhaust) left out as omissions. Every text basis it keeps cites a
Biggs passage recorded in the ledger.

### H-1 188K, Saturn I SA-10

SDES-64-415 Vol. VIII only: 188,000 lb nominal sea-level rating, LOX and RP-1,
liquid-propellant gas generator, geared turbopump, the start cartridge, the
gas generator's fuel-to-LOX ratio (2.924, as the gas generator's, not the
engine's), and the inboard-engine graph. No engine chamber pressure, Isp,
mixture ratio or area ratio is printed for this configuration, and none is
filled from the H-1 family (none was transcribed for this configuration in
DB-0.5). The schematic's pressure callouts are withheld:
no operating point is printed for them, and the graph roles that quoted them
had the numbers removed.

### LM descent engine, final design

TN D-7143. The "basic design requirements for the descent engine" (throttling
ratio, maximum-rated thrust, Isp at end of duty cycle, propellants, pressure
feed) are programme requirements: they ship as DESIGN_VALUE statements of the
variant, never as values of the final design. The final design ships its
fixed throttle point (as printed: "optimized at 92.5 percent of
maximum-rated thrust", NOMINAL), minimum throttle point, cooling, shutoff valves and
throttle actuator, and the final DPS graph (Figures 3 and 7) scoped to the
propulsion unit: helium storage, regulation, tanks and plumbing are vehicle-
owned; flow-control valves, actuator, shutoff valves, variable-area injector,
chamber and nozzle extension are engine-owned. The development fixed-area
design (Figure 6) is not in the record; a gate refuses its schematic and the
wording. ARCHITECTURE and PERFORMANCE are NOT_SUPPORTED because TN D-7143
states the propellants and the feed for the programme, not for the final
design.

### Space Shuttle OMS engine

JSC-19950 (6,000 lb thrust and 313 s, environment not printed) and NTRS
19850008634 (N2O4/MMH, 120 coolant channels, 55:1 nozzle, injector, throat
distance). 316 s does not ship (no primary support). No mixture ratio or
chamber pressure ships: DB-0.5 holds no mixture ratio, and its only chamber
pressure assertion is from the rights-withheld workbook (JSC-19950 prints the
same approximate 130 psia, recorded in conflict CF-DB05-OMS-PCBAND, but not
transcribed as an assertion). The OMS
Workbook (OMS 21002) prints "Copyright (c) 2004 by United Space Alliance … All
other rights are reserved", so its values and both its schematics are
withheld, and with them the whole DB-0.5 OMS graph: TOPOLOGY is NOT_SUPPORTED.
The sources name it "OMS engine"; AJ10-190 is not printed in them and is not
used.

### RS-25 / SSME

Three configurations, none of them Block IIA:

- the original-throat MCC baseline of NTRS 19860012108 (77.5:1, 3,285 psia at
  109%);
- Block II as JSC-19041 describes the 2003 fleet (approximately 2,747 and
  2,870 psia at RPL and 104.5%, approximately 470,000 lb vacuum at RPL, gimbal,
  throttle range);
- the SLS-adapted engine of NASA facts FS-2025 (512,300 lb vacuum at 109%).

`CONFIGURATION_SOURCES` keeps each build to its own sources. Every Block IIA
statement in DB-0.5 is from BC98-04, stamped BOEING PROPRIETARY, so Block IIA
ships nothing and no RS-25 graph ships (the only DB-0.5 RS-25 graph is drawn
from that schematic). The L3Harris spec sheet (©, no reuse licence) and AIAA
2002-3581 (© against NTRS public use) are withheld. Mass, pump power, sea-
level thrust and HPOTP speed are in UNRESOLVED or PARTIALLY_RESOLVED conflicts
and withheld; the unaffected vacuum thrust ships. HAER TX-116 and FS-2025's
shuttle-fleet figures (104.5%, 111%) name no block and are not filed under one.
JSC-19041's statement that Block IIA added a larger-throat MCC is the Block IIA
change, printed beside the Block II definition; it is not generalised to the
RS-25 variant (WRONG_CONFIGURATION).

## Rights limitations

Records poorer than DB-0.5 because of rights:

- **RS-25**: all Block IIA data and the only RS-25 topology (Boeing proprietary);
  the L3Harris 109% specification set; AIAA 2002-3581.
- **OMS**: the workbook's values and both schematics (USA copyright), hence no
  OMS graph.
- **F-1**: MSFC-MAN-503's values and the elements of the graph it alone supports.

Rights readings for Wave-1 sources were checked 2026-10-09 and recorded per
source; the owner accepted them as owner-reviewed on 2026-10-09
(`OWNER_REVIEWS["WAVE1-RIGHTS"]`). That is a RocketForge shipping-policy
review, not a legal determination: host metadata, printed notices and every
per-content restriction are kept, and no restrictive or withheld source is
upgraded.

## Owner decisions (2026-10-09)

Recorded as text in `db2b_wave1_manifest.py` (`OWNER_DECISIONS`,
`OWNER_REVIEWS`); the DB-0.5 conflicts are not rewritten.

1. **F-1 "Engine Characteristics" viewgraph** (CF-DB05-F1-RATING): accepted as
   defining the source-scoped `CFG-F1`; 1,748,200 lb vacuum thrust, 265.4 s
   sea-level Isp and 304.1 s vacuum Isp admitted. Not a canonical historical
   flight-rating epoch; the sea-level thrust conflict stays withheld.
2. **F-1 chamber pressure** (CF-DB05-F1-PC): 1,125 psia accepted for `CFG-F1`
   only, station UNKNOWN, no family, variant or general F-1 inheritance; the
   research conflict stays PARTIALLY_RESOLVED.
3. **Wave-1 rights readings**: accepted as owner-reviewed (shipping policy, not
   a legal determination; no restriction lifted).
4. **DB-2A manifest metadata** (text_basis, NOT_PROMOTED metadata, literal
   OWNER_DECISIONS): re-approved; DB-2A shipped data is item-for-item
   unchanged.

The two DB-2A `owner_accepted` decisions remain and apply only to their J-2
and SPS Block I records.

### Owner decision requested (post-change review, 2026-10-10)

5. **F-1 qualification life (AS-DB05-US-F-1-010)**, printed in the same
   "F-1 Engine Characteristics" table: may it ship for `CFG-F1`? Decision 1
   accepts the viewgraph as defining the configuration but names only the
   vacuum thrust and the two Isp values, so it is withheld until decided.

## Not done, by design

No other engine was migrated (RD-170, RL10A-4-2, RL10B-2, IPD, Rutherford,
LR87, RS-68A, LE-7A, LE-9, Vulcain, Vinci, YF engines and the rest of DB-0).
No regression is accepted, no UI exists for the corpus, nothing is solved, and
no record designs an engine.

## Verified by

| Test file | What it holds |
| --- | --- |
| `tests/evidence/test_reference_engine_wave1.py` | the production boundary; capability results per configuration; per target: J-2S architecture without a graph and no J-2 leakage, no F-1 thrust or canonical rating and no guessed mixture-ratio direction, F-1 graph without the withheld manual, H-1 missing values stay missing and callouts do not ship, LMDE final design only with stage equipment outside the engine and requirements at variant level, OMS 313 s kept and 316 s absent with no guessed MR or Pc, RS-25 configurations distinct through a round trip, no Block IIA value or rights-restricted source or figure, open conflicts blocking only their fields |
| `tests/research/test_db2b_wave1_promotion.py` | a regression test for each review finding (unrecorded text basis, compound kind words, F-1 viewgraph values, build values on a family, variant or unit, withheld RS-25 and LMDE wording in notes, rights-withheld value relabelled, invented owner decision, notices qualified by an exception; and from the second review: a text basis from another page, a withheld text basis, a quote not in the basis, a reading excusing a requirement kind or a family build value, a requirement on a configuration, a build statement generalised to its variant, owner decisions as written text, a restricted source withheld as out of scope, L3Harris and Block IIA wording in RS-25 and variant notes; and for the owner decisions: a release without the recorded decision, admitted F-1 values not inherited by variant or family, the sea-level rating never released, a release only for a value printed with a withheld claim, the F-1 chamber pressure station, an unused owner decision, owner reviews tied to their sources and never upgrading a withheld source; and from the post-change review of the owner gates: a table-mate of a withheld rating shipped without any owner record, a release beyond the owner's words, the unadmitted F-1 qualification life, the decision's configuration scope and a later F-1 configuration, another engine's decision, a released value keeping its own conflict, a mixture-ratio direction from the reading alone and the DB-2A readings' records, owner-review wordings, an unknown source in a review); exhaustive accounting and its totals; the recorded Wave-1 owner decisions; disposition checks; manifest merge; a gate refusal for each hazard above (J-2 graph or value under J-2S, F-1 thrust and MR direction, F-1 withheld wording, H-1 callouts, digitised callout as a value, LMDE development schematic and wording, programme requirement as a final value, OMS workbook values and graph, filled OMS environment, false NTRS host, Block IIA value under Block II, cross-build source, Boeing schematic as topology, open-conflict field coverage) and the restrictive-notice reading |
| DB-2A tests | rescoped from "the corpus is the three seeds" to "the three seeds are present, unchanged"; the catalog lists every configuration |
