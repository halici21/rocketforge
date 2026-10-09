# DB-2A — Verified reference engine seed corpus

DB-2A ships the **initial verified seed corpus** of the reference engine
database: three engine configurations, recorded in the DB-1 schema
(`DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md`) from documents that were opened and
read. It is the first production data for that schema, and it is
deliberately small. It is not a complete engine database, it does not claim
any engine's record is complete, and nothing in it designs an engine.

**Status: COMPLETE** for its scope: the three seed configurations ship,
verified. Two of their performance value sets are in research conflicts that
are only partially resolved and ship by recorded owner decision, for their own
configuration only (see "Owner decisions"). What each record can and cannot
support is stated per capability below; not every seed is a regression
candidate.

## Purpose

DB-1 defined how reference-engine evidence is held. DB-2A puts real records
into it, so that the schema, the shipping rules and the capability questions
are exercised by data rather than by fixtures. It does this for three
configurations whose sources were already read in DB-0.5, and promotes only
what those sources state about those configurations.

## Research and production are separate

| | Research (DB-0, DB-0.5) | Production (DB-2A) |
| --- | --- | --- |
| Where | `docs/research/engine_database/` | `rocketforge/data/evidence/engines/reference_engines.json` |
| Holds | everything found, labelled: search results, blocked sources, inferred values, open conflicts, unsettled rights | only what passed the promotion gates |
| Read by | people, the research tests, and the promotion tool at build time | the application (`reference_engine_catalog`) and the package verifier |
| Packaged | no | yes, with the rest of `rocketforge/data/evidence` |

The application never reads research files. The catalog loads one file by
its data path; a test checks that no string in `rocketforge/` code names
`docs/research`, `engine_database` or `db05`, and that the corpus loads from a
copy placed anywhere. The promotion tool (`tools/reference_engines/`) is a
build-time script; RocketForge never imports or runs it.

## Promotion policy

There is no bulk rule. Nothing is promoted because it is "source verified" in
DB-0.5. The manifest, `tools/reference_engines/db2a_manifest.py`, names:

* every source, with its rights reading (repository statement, printed-notice
  check, policy per content kind, review);
* every promoted assertion: its DB-0.5 id, the subject it is about, its
  production field path, its typed value, value kind, operating point and
  conditions;
* every DB-0.5 assertion of the three engines that is **not** promoted, with
  the reason (all 69 are accounted for: 43 promoted, 26 not);
* every DB-0.5 conflict on the three engines, with a decision;
* every topology element that differs from its DB-0.5 graph, with the reason.

`promote_db2a.py` checks each entry against the DB-0.5 records and refuses the
whole build, naming every failure, if any entry fails a gate:

| Gate | Refuses |
| --- | --- |
| Source opened | a source not READ_AND_MINED in DB-0.5 (search results, blocked, fetched-not-read), or without a recorded download hash |
| Rights | a rights review other than CONSISTENT (NOT_REVIEWED ships nothing); DB-0.5 values rights other than public-domain-government or values-with-attribution; a host statement that is not what NTRS returned; a recorded restrictive printed notice; a withheld source anywhere, including a locator |
| Status | INFERRED (never promoted, and never as REPORTED); DIGITISED without the original drawing it was read from |
| Value kind | a kind the printed words do not give (MAXIMUM, AVERAGE, RATED, ...) without a written `reading`; NOMINAL for a value printed as an average, maximum or approximation |
| Value | a number that is not the DB-0.5 value; a number read out of printed text without saying how (`reading`) or that is not in the printed text; an enumeration token that is not the DB-0.5 value |
| Scope | a subject that is not an identity of that engine; a value printed for another configuration (Block II as Block I) or another operating point; an operating point the record does not state, placed without an `op_basis` citing an assertion that DB-0.5 places at that point, or a sibling from the same source and table promoted there |
| Conditions | a chamber-pressure station other than the one printed (an unstated station stays UNKNOWN); a pressure basis the printed unit does not give; an environment the source does not state; any Isp basis; a mixture-ratio basis not printed; a mixture-ratio direction whose mark (O/F, F/O, or the words) is neither printed nor quoted in the `reading`; a mixture-ratio setting added as a condition |
| Limit | a value printed as a limit promoted as an operating value |
| Conflicts | a DB-0.5 conflict with no decision. Each conflict's claims are matched to DB-0.5 assertions (same source, a printed number in common), and the decision is checked against them: WITHHOLD must list every matched assertion and none may be promoted; not carrying a conflict needs every promoted match listed, is refused for UNRESOLVED, and for PARTIALLY_RESOLVED needs the owner's recorded decision (`owner_accepted`); a RESOLVED conflict may ship claims from one side only |
| Topology | an edge whose endpoint is not a node or was withheld; a node or edge without an evidence status or locator; a schematic DB-0.5 records as a third-party reconstruction promoted as anything else; a schematic or text source that is not a manifest source, or is withheld. A restatement may only keep or lower evidence (never INFERRED to evidenced); cite only whole locator parts the DB-0.5 graph already uses, or locators of DB-0.5 assertions from the graph's own text sources; cut a label to the words before its parenthesis; generalise a carrier by a listed rule (A-50 to "fuel"); and change a role only by deleting the withheld wording it names |
| Leaks | a shipped locator citing a withheld source (by id, report number or title); withheld wording (what only MSFC-MAN-503 says about the J-2) in the J-2 record's labels, roles, omissions or notes. The wording check is a word list and therefore best effort; a test pins the exact free text of the J-2 graph, so any change to it needs review |
| Admission | anything `admission_violations` reports in the built corpus |

`--check` rebuilds and compares with the committed file; a test does the same,
so the shipped file is always exactly what the manifest produces.

DB-2A transcribed eleven statements DB-0.5 had left out of documents it had
already read (feed, propellants, turbine drive, cooling and turbopumps from the
J-2 slide that carries the 230,000 lb table; cycle and propellants from the
CR-195478 abstract; the 475 psia in the same Pratt & Whitney table as the
RL10A-3-3A thrust and Isp; "pressure-fed" from the TN D-7375 Block I engine
paragraph). They are ordinary DB-0.5 ledger entries with locators, re-read
from the opened PDFs, and are recorded in `db05/STATUS.md`. DB-0.5 stays
PARTIAL.

## Shipping rules beyond the schema

`rocketforge/evidence/engines/admission.py` states what a shipped corpus must
satisfy that the schema alone does not require. Every source is opened, its
values may ship with attribution, and its rights reading is settled. Every
assertion is admitted and REPORTED or DIGITISED from an original drawing; a
Missing value only says the source does not give it. No shipped assertion is
in an UNRESOLVED or PARTIALLY_RESOLVED conflict. No graph claims completeness.
The catalog and the package verifier refuse a file that breaks any of these.

## The three seeds

### J-2, 230,000 lb rating, MR 5.5 (`CFG-J2-230K`)

Source: Paul Coffman, *Rocketdyne – J-2 Saturn V 2nd & 3rd Stage Engine*, NTRS
20100027318 (Rocketdyne viewgraphs and text). The configuration is defined by
the "J-2 Basic Engine Features" viewgraph (PDF p.14): nominal vacuum thrust
230,000 lb, nominal vacuum specific impulse 425 s, chamber pressure 717 psia
at nozzle stagnation, engine mixture ratio calibration 5.5:1 (O/F), all at
operating point `OP-J2-230K-MR55`; area ratio 27.5:1; dry weights 2,754 lb
(basic) and 3,492 lb (with accessories); pump-fed, liquid oxygen and liquid
hydrogen, gas-generator turbine drive, regeneratively cooled tubular chamber.
Coffman's narrative about "the J-2" (pump types, series turbines, tube
pattern) is recorded for the variant, not this configuration. The 230,000 lb
thrust is a claim in research conflict CF-DB05-J2-THRUST (PARTIALLY_RESOLVED);
it ships for this configuration only, by owner decision. The configuration's
name, after that rating, is a descriptive production label, not a new
historical engine designation.

When the 230,000 lb rating applied is not established (`effective` is Missing,
UNKNOWN): Coffman also names a 225,000 lb qualification version, and the AEDC
test reports could not be opened. The 225,000 lb version is not part of DB-2A.

MSFC-MAN-503 (the Saturn V flight manual DB-0.5 also used) carries a printed
restriction on non-government reproduction that conflicts with its NTRS
public-use flag. That rights conflict is unresolved, so none of its content is
shipped: its six assertions are not promoted, its start-sequence figure is not
recorded, and the J-2 graph rests on the Rocketdyne schematic and Coffman's
text alone. Elements DB-0.5 knew only from the manual are left out and listed
as omissions, worded so that they do not restate the manual: one component
and one drive relation "known only from a rights-withheld source", the
mixture ratio control valve's flow connections, and both turbine-to-pump
drives (Coffman names turbopumps but neither a shaft nor a gear). The control
valve's label is cut to the slide's own words.
Elements that rested on the manual and on the slide keep the slide, and keep
DERIVED_FROM_BOTH only where a quoted Coffman sentence supports them; each such
restatement is in the manifest with its quotation.

### RL10A-3-3A, 475 psia, O/F 5.0 (`CFG-RL10A-3-3A`)

Sources: Pratt & Whitney viewgraphs, NTRS 19910018888 ("RL10A-3-3A ENGINE"
table, p.3: vacuum thrust 16,500 lb, specific impulse 444.4 s, mixture ratio
5:1, chamber pressure 475 psia, area ratio 61:1, weight 305 lb), and NASA
CR-195478 (NTRS 19950022693: "hydrogen/oxygen expander cycle engine", pump
configuration and the "normal operating point of 475 psia and O/F = 5.0" with
pump flows and speeds). Both documents give the same point, `OP-RL10A-3-3A-475-OF5`; each value DB-0.5
recorded without an operating point is placed there with a written basis.
Neither says where the chamber pressure is measured (UNKNOWN), and the table
does not say vacuum or sea level for the specific impulse (UNKNOWN). The
feed system is not stated as such; the architecture rests on the stated
cycle. The graph is CR-195478 Figure 1, unchanged except one edge: the igniter
to chamber line is drawn, but DB-1 has no edge kind for ignition energy, so it
is listed as an omission rather than forced into a fluid edge.

### Apollo SPS engine, Block I (`CFG-SPS-BLOCK-I`)

Source: NASA TN D-7375, *Apollo Experience Report – Service Propulsion
Subsystem* (NTRS 19730023031), Block I section: chamber pressure 102 psia,
vacuum thrust 21 500 lb, average specific impulse 309 s (environment not
stated), O/F 2:1, radiation-cooled nozzle to area ratio 62.5:1, pressure-fed,
hypergolic ignition, life, valve and cooling statements. The first three are
one claim in research conflict CF-DB05-SPS-THRUST (PARTIALLY_RESOLVED) against
Aerojet's configuration-unstated 20,000 lb, 100 psi and 314.5 s; they ship for
Block I only, by owner decision, and never for Block II or the SPS family.
Aerojet's values are not shipped. The graph (TN D-7375 Fig. 2 and the engine-assembly text)
is scoped to a propulsion unit, `UNIT-SPS-BLOCK-I`, because the tanks,
pressurization and feed belong to the service module; the engine owns the
bipropellant valve, injector, chamber and nozzle. The 4400 psia in the DB-0.5
helium-tank label is the value of a claim withheld by the UNRESOLVED
regulator conflict, so the label is cut before it.

TN D-7375 names the oxidizer (N2O4) but never the fuel. "A-50" in the DB-0.5
graph came from the Aerojet chapter (NTRS 20100027319), which states no
configuration, so the fuel lines carry "fuel". The Aerojet propellant
statement is recorded for the AJ10-137 variant; it is not applied to Block I,
so the Block I configuration's ARCHITECTURE answer is PARTIAL. No Block II
value is shipped.

### Owner decisions

The contract allows no UNRESOLVED or PARTIALLY_RESOLVED conflict on a shipped
value unless resolved. The author's arguments were put to the owner, who
decided on 2026-10-09:

* **CF-DB05-J2-THRUST: accepted** for the DB-2A 230,000 lbf / MR 5.5
  configuration only. The open research question is flight effectivity of the
  225,000 and 230,000 lb ratings and a 232,250 lbf figure seen only in a search
  result; no opened source gives another value for this configuration.
* **CF-DB05-SPS-THRUST: accepted** for Block I only: 21,500 lbf vacuum thrust,
  102 psia and 309 s. The open research question is the Block II rating;
  Aerojet states no configuration.
* **J-2 name kept**: "J-2, 230,000 lb nominal vacuum thrust rating" is a
  descriptive production configuration label, not a new historical engine
  designation.
* **Rights readings accepted** as owner-reviewed for all five sources
  ("consistent", checked 2026-10-09). Host metadata, the printed-notice check
  and every per-content policy are kept as recorded; acceptance upgrades
  nothing (values ship with attribution, not as public domain).
* **CR-195478 Figure 1 accepted as ORIGINAL_CONTRACTOR**: an original drawing
  in a NASA contractor report. It is not ORIGINAL_MANUFACTURER; the schematic
  record says so.

In the manifest the two conflicts are CARRIED_NOT with `owner_accepted`
recording the decision; the build still checks every gate (every promoted
claim listed in `touches`, competing claims unpromoted). A test pins exactly
these two owner entries, so any other change to them changes that test in the
same commit. The DB-0.5 conflicts are unchanged and stay PARTIALLY_RESOLVED in
the research record. The UNRESOLVED regulator-setpoint conflict
(CF-DB05-SPS-REG) withholds its claim. The seed corpus itself carries no
conflict.

## Capabilities

`rocketforge/evidence/engines/capabilities.py` answers five questions for one
configuration, each with a status (SUPPORTED, PARTIAL, NOT_SUPPORTED), the
assertions and graphs it rests on, `gaps` and `caveats`. They are never
combined into a score or a rank.

| Capability | SUPPORTED when |
| --- | --- |
| IDENTITY | the configuration is a named build of a named variant and family, and a shipped statement is about it |
| ARCHITECTURE | both propellants, and the cycle or the feed system, are stated for this configuration |
| PERFORMANCE_REFERENCE | thrust, specific impulse, chamber pressure, mixture ratio and area ratio are stated for it as operating values |
| TOPOLOGY | a graph of it (or of a unit containing it) has nothing stopping it counting as an original drawing; every graph's omissions are caveats |
| REGRESSION_CANDIDATE | those five quantities, the running ones at one operating point, agree, have a stated environment for thrust and specific impulse, are not printed as averages or approximations, and pass `regression_blockers` |

Only what is recorded for the configuration, its operating points and its
components counts. A variant or family statement is reported as a caveat
naming it and supports nothing. Only admitted REPORTED or DIGITISED values
count. A LIMIT is not an operating value. Unknown conditions (an unstated
chamber-pressure station, an unstated Isp environment) are caveats, never
filled in.

| | IDENTITY | ARCHITECTURE | PERFORMANCE_REFERENCE | TOPOLOGY | REGRESSION_CANDIDATE |
| --- | --- | --- | --- | --- | --- |
| J-2 230K | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED (eligible only) |
| RL10A-3-3A | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_SUPPORTED (Isp environment not stated) |
| SPS Block I | SUPPORTED | PARTIAL (propellants not stated for Block I) | SUPPORTED | SUPPORTED | NOT_SUPPORTED (Isp printed as an average, environment not stated) |

REGRESSION_CANDIDATE SUPPORTED means *eligible to be proposed*. No regression
is accepted, locked or run from these records; the ideal-performance and CEA
baselines, LIQ-1 to LIQ-6 values, tolerances and regression locks are
unchanged. Accepting a regression is a separate decision with a comparison
case.

## No solver coupling

`rocketforge/application/analysis/reference_engine_catalog.py` loads the
corpus, refuses it if `admission_violations` reports anything, and answers:
the configurations, a name lookup over designations, family names and aliases
(exact, no fuzzy match), a configuration's own assertions, its variant and
family context (kept apart), its graphs, its sources, and its capabilities.
Answers are frozen tuples. It imports `rocketforge.evidence` and
`data_paths` only: no Qt, no provider, no CEA, no network, no physics, no
unit conversion, and no design-recommendation entry point. A test imports it
and evaluates every capability in a fresh interpreter and checks that no
physics, engineering, engine, provider, comparison, UI, CEA, Cantera, CoolProp
or Qt module was loaded. There is no UI for the catalog yet.

`packaging/verify_package.py` already compares every file under the packaged
evidence folder with the source tree; it now also loads the packaged
reference-engine corpus through the catalog and fails if it does not load.

## DB-1 changes

None to the schema. DB-2A adds two modules beside it (`admission.py`,
`capabilities.py`) and changes no existing type, validator or JSON field.

## Verified by

| Test file | What it holds |
| --- | --- |
| `tests/evidence/test_reference_engine_seed_corpus.py` | the boundary (exactly three seeds, no other engine), canonical JSON and stable fingerprint, every assertion verbatim against DB-0.5, source rights and hashes, the three records, graph ids, types, ownership, edges, carriers and omissions against DB-0.5, capability results, and negatives on the shipped record (limit, inferred, open conflicts, unreviewed rights, family statement, Block I value moved to another configuration, edge endpoints and locators, third-party drawing) |
| `tests/research/test_db2a_promotion_gates.py` | the manifest rebuilds the shipped file byte for byte; every gate refuses: search result, access blocked, unreviewed rights, printed notice, withheld manual, inferred, changed value, filled-in station, environment, Isp basis, mixture-ratio basis or direction, unprinted value kind, unexplained operating point, limit, Block II as Block I, another engine's subject, unresolved and partially resolved conflicts (and the owner-accepted path), incomplete conflict decisions, withheld or competing claims, edge endpoints, edge provenance, withheld locator and wording, every widening restatement, inferred upgrade, third-party reclassification, omission never absence |
| `tests/application/test_reference_engine_catalog.py` | the catalog: entries, lookup, own versus context, sources, frozen answers, determinism, one file and never research, frozen-build path, no network, refusal of a broken file, no solver import (static and in a fresh interpreter), no design entry point |
| `tests/test_evidence_packaging.py` | the packaged corpus must match the source and load |

## Limits

* Three configurations. DB-2B (a broad corpus) has not started; no other DB-0
  or DB-0.5 engine (RS-25, F-1, H-1, J-2S, OMS, LMDE, RD-170, RL10A-4-2,
  RL10B-2, Rutherford, LR87, RS-68A or any other) is migrated.
* No record is complete. Every graph lists what it leaves out; nothing is
  recorded as absent.
* Two performance value sets rest on owner decisions scoped to one
  configuration each; the research conflicts behind them stay open in DB-0.5.
* No UI. The catalog is a backend only.
