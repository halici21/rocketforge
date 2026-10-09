# DB-1 — Reference engine evidence schema

DB-1 is the production data model for what sources say about liquid rocket
engines: identity, technical assertions, sources and rights, conflicts,
hardware and topology. It is a schema and its validators. It ships no engine
records (that is DB-2), adds nothing to the UI, and solves nothing. It is
internal infrastructure, not a reference engine database a user can open.

The design comes from the DB-0 research package and from DB-0.5, which read
the sources themselves (`docs/research/engine_database/`, especially
`SCHEMA_PROPOSAL.md` §8 and `db05/`). Every structure below exists because a
real document needed it.

## Where it lives

| Part | Location |
| --- | --- |
| Vocabularies | `rocketforge/evidence/engines/vocabulary.py` |
| Sources, rights | `rocketforge/evidence/engines/sources.py` |
| Identity: family, variant, configuration, operating point, units, aliases, lineage | `rocketforge/evidence/engines/identity.py` |
| Assertions, values, conditions | `rocketforge/evidence/engines/assertions.py` |
| Conflicts | `rocketforge/evidence/engines/conflicts.py` |
| Components, schematics, topology | `rocketforge/evidence/engines/topology.py` |
| Corpus, cross-checks, capability checks | `rocketforge/evidence/engines/corpus.py` |
| JSON schema version 1 | `rocketforge/evidence/engines/load.py` |
| Tests | `tests/evidence/test_engine_evidence_{model,schema,stress}.py`, fixtures `tests/evidence/engine_fixtures.py` |

The package is part of the `evidence` layer (`01_engineering_architecture.md`
§2): it imports only `core` and the rest of `evidence`, so browsing it can
never reach physics, a provider, a solver or Qt. `tests/test_architecture.py`
enforces that without change, because `rocketforge.evidence.engines` is inside
the `evidence` package.

## What it reuses, and the one change to shared code

| Existing type | Used for |
| --- | --- |
| `Missing`, `MissingReason` | every explicit absence: values, unstated configuration dates, unit-member counts, absent rights statements |
| `ValueStatus` (REPORTED, DERIVED, DIGITISED, INFERRED) | how an assertion entered the record |
| `SourceReference` | wrapped by `EngineSource`: bibliographic identity, access class, the values shipping decision, tier 1-3 |
| `ShippingPolicy` | each of the four rights policies (values, figures, tables, text) |
| `EvidenceError`, `EvidenceSchemaError` | every refusal |
| `rocketforge.evidence.load` parser helpers | strict parsing: duplicate keys, NaN, unknown and missing fields, wrong types, unknown enum values |
| fingerprint convention (`rocketforge.engine.chamber_sizing`) | `corpus_fingerprint`: SHA-256 of the compact sorted-key JSON |

**One additive change:** `MissingReason.ACCESS_BLOCKED` ("the source that would
give it could not be opened"). The engine research called rights withholding
`RIGHTS_RESTRICTED`; that is the existing `WITHHELD_RIGHTS` and keeps its one
spelling. Existing solid-propellant records and the CEA bridge are unaffected:
the bridge special-cases only `WITHHELD_RIGHTS`.

`ReportedValue` is not used for engines. It holds a float with a unit, which
cannot carry a range, a categorical claim, a value kind, an operating point or
structured conditions. `Assertion` sits beside it with the same discipline.

## The model

### Identity

```
EngineFamily -> EngineVariant -> EngineConfiguration -> OperatingPoint
PropulsionUnit (ENGINE_MODULE | PROPULSION_SYSTEM | STAGE_PROPULSION) with members
Alias (names an identity, never another alias)
LineageEdge (DERIVED_FROM, UPRATE_OF, RENAMED_FROM, LICENSED_FROM, SUCCESSOR_OF, MODULE_OF)
```

The hierarchy carries no values, and no lookup walks it:
`EngineEvidenceCorpus.assertions_about(subject)` returns exactly what was
recorded for that subject. A value printed for the RL10 family stays a family
statement; Block IIA's state points are not Block II's. A designation that is
really a propulsion system (RD-0212) or a module (YF-21) is a
`PropulsionUnit`, not a variant.

### Assertions

An `Assertion` holds the subject (any identity level, or a component), a dotted
`field_path`, a typed value, the value and unit **as printed**, structured
`Conditions`, an optional operating point and epoch, a `ValueKind`, the
`ValueStatus`, an `Admissibility`, the source, the locator, the source's access
state, an optional first-stated-by source, the schematic a digitised value was
read from, the arithmetic for a derived value, and a note.

| Value type | Example |
| --- | --- |
| `NumberValue` | 2,994 psia |
| `RangeValue` | 67 % - 109 % |
| `EnumValue` | `FUEL_RICH`, `TAP_OFF` |
| `TextValue` | "The modification between the Block IA SSME and the Block IIA was a larger throat MCC" |
| `Missing` | NOT_REPORTED, NOT_AUDITED, UNKNOWN, ACCESS_BLOCKED, WITHHELD_RIGHTS |

A `NormalizedQuantity` (SI value, unit, conversion method) can sit beside a
printed number; it never replaces it.

`ValueKind` keeps a limit apart from an operating value. The RS-25 high-pressure
oxidizer turbine's "maximum allowable ... approximately 30,000 rpm" is
`LIMIT`, and `OPERATING_VALUE_KINDS` excludes `LIMIT`, `PREDICTION`,
`DESIGN_VALUE`, `OTHER` and `UNKNOWN`.

`Conditions` fields: environment, power level and mixture-ratio settings,
mixture-ratio form (O/F or F/O) and basis (engine, thrust chamber, gas
generator, preburner), pressure basis, chamber-pressure station, Isp basis,
named qualifiers. `None` means "not a condition of this value"; `UNKNOWN`
means "the source does not say". Four quantities have one canonical name each
(a suffix after it is allowed, e.g. `thrust_vac`, `chamber_pressure_max`), and
a printed value of them must state:

| Final segment | Must state |
| --- | --- |
| `chamber_pressure`, `chamber_pressure_*` | pressure basis and measurement station |
| `thrust`, `thrust_*` (not `thrust_chamber*`) | environment |
| `specific_impulse`, `specific_impulse_*` | environment and Isp basis |
| `mixture_ratio`, `mixture_ratio_*` | form and basis |

Synonyms that would slip past these checks (`isp`, `pc`, `isp_vac`,
`vacuum_thrust`, `main_chamber_pressure`) are refused. A `Missing` value prints
nothing, so it carries no condition obligations. A mixture-ratio *setting* in
`Conditions` also states its form and basis.

### Sources and rights

`EngineSource` = `SourceReference` + A-E authority (tied to the 1-3 tier:
A, B → 1; C → 2; D, E → 3) + primacy + access state + content SHA-256 +
`same_document_as` + a `RightsRecord`.

Access states are OPENED, IDENTITY_VERIFIED_ONLY, FETCHED_NOT_READ,
SEARCH_RESULT_ONLY and ACCESS_BLOCKED. Only OPENED and SEARCH_RESULT_ONLY
sources can supply a value. Only OPENED sources can supply a schematic, a
topology text basis, an absence statement or a "not reported". A blocked
source can only supply `Missing(ACCESS_BLOCKED)`. The wrapped
`SourceReference.rights_statement` reads `RIGHTS_IN_RECORD`; the statements
themselves live only in the `RightsRecord`, so the two cannot drift apart.
`notices_disagree` is the reviewer's finding, not computed from the text.

`RightsRecord` keeps the host's statement and the printed notice separately,
with a policy for values, figures, tables and text. When the two statements
disagree (NTRS "public use permitted" over a page printing an AIAA copyright),
the record must be `CONFLICT_UNRESOLVED`, and no content kind may ship values
until a review with a written note resolves it. Scientific authority is a
separate field: a Tier A report can be rights-restricted.

### Conflicts

A `Conflict` names two or more assertions, a resolution (UNRESOLVED,
PARTIALLY_RESOLVED, EXPLAINED, RESOLVED), the categories that explain them
(different variant, configuration, operating point, epoch, definition,
measurement station; rounding; unit conversion; printed typo; other) and the
argument. A RESOLVED conflict names the claim that stands; every claim stays
recorded. Nothing is averaged. `EngineEvidenceCorpus.is_intra_document`
reports a conflict inside one document (a table against its own text).

### Hardware and topology

A `Component` is typed (`ComponentType`, 35 members from thrust chamber to
interface port), owned (`ENGINE`, `STAGE`, `VEHICLE`, `AMBIENT`, `EXTERNAL`,
`UNKNOWN`) and scoped (`HARDWARE_SCOPES`) to one engine configuration or to a
propulsion unit, for hardware several engines share (a stage's common tanks).
It carries no attributes: a stage count or a rich side is an assertion whose
subject is the component.

A `TopologyGraph` is scoped the same way. An engine graph uses its
configuration's components. A stage or system graph (a pressure-fed RCS quad on
common tanks) uses the unit's components and those of the engine configurations
the unit contains. Hardware from outside the scope is refused. Its nodes and
edges each carry
evidence (SHOWN_IN_SCHEMATIC, REPORTED_IN_TEXT, DERIVED_FROM_BOTH, INFERRED)
and a locator. Edges are typed:

| `EdgeKind` | Carrier |
| --- | --- |
| `FLUID_FLOW` | required: the fluid |
| `CONTROL_ACTUATION`, `ELECTRICAL_POWER` | optional: the medium (GN2 to valve pistons) |
| `MECHANICAL_SHAFT`, `GEARED_DRIVE`, `MECHANICAL_LINKAGE` | none |

Split and merge groups mark parallel branches. A graph must cite the
schematics and texts its evidence statuses claim.

**Omission is never absence.** `Completeness` holds `declared_complete`
(which forbids listed omissions), `known_omissions`, and `AbsenceStatement`s,
each citing an opened source that says a component is not there.
`TopologyGraph.stated_absent()` is true only from such a statement.

A `Schematic` records who drew it: ORIGINAL_MANUFACTURER, ORIGINAL_AGENCY,
ORIGINAL_CONTRACTOR, THIRD_PARTY_RECONSTRUCTION or UNKNOWN.
`ROCKETFORGE_DERIVED_GRAPH` describes graphs, not printed figures.
`original_topology_blockers()` refuses a reconstruction (the Rockwell RD-170
drawing) or INFERRED elements.

## Capability, not a score

There is no quality score, consistent with `EvidenceStatus`.
`regression_blockers(corpus, assertion_ids)` lists every reason a set of
assertions cannot serve as a regression reference:

- not admitted, or Missing;
- INFERRED;
- not an operating value kind;
- stated above configuration level (a family or a bare variant; a propulsion
  unit counts as scoped);
- source not opened, or not authority A or B;
- first stated by a source of authority C-E;
- digitised from a schematic that is not an original drawing;
- values may not ship, or rights not settled;
- an UNRESOLVED or PARTIALLY_RESOLVED conflict on the assertion, or a
  RESOLVED one that preferred another claim.

An empty answer does not lock a regression; that stays a separate decision
with a comparison case. The five DB-0.5 regression candidates remain
candidates.

## JSON

One document per corpus. It holds `format` `"rocketforge.engine_evidence"`,
`schema_version` 1, and the thirteen collections. Parsing is strict in the
same way as the solid evidence files, and every field is written (`null`
included). A missing optional field is an error, not a default. The canonical
text is two-space indented UTF-8 with a final newline and round-trips byte for
byte. Construction runs every cross-reference check:

- ids are unique;
- every reference resolves;
- an operating point belongs to the subject's configuration;
- unit membership, lineage and derivations have no loops;
- an alias whose name also names another identity (variant designation, unit
  designation, family name, other alias) is marked ambiguous, comparing names
  after NFKC, case folding and dash/space folding;
- sources with one hash name one canonical record;
- assertion access agrees with its source;
- each `Missing` reason fits what was done with the source.

## Decisions

- **Subpackage of `evidence`, not a new layer.** Engine evidence is the same
  kind of thing as solid-propellant evidence: sourced data that computes
  nothing.
- **Facts about hardware are assertions.** A component with typed attributes
  (stages, rich side) would carry unsourced values and grow a field per engine
  family.
- **Per-collection identifiers, references by typed `SubjectRef`.** A family
  and a variant may share an id string without ambiguity.
- **Field paths are open, four endings are checked.** A closed field list would
  need a schema change for every new quantity DB-2 meets. The four checked
  endings are the ones DB-0.5 showed to be ambiguous without their conditions.
- **PARTIALLY_RESOLVED blocks a regression.** That is stricter than the DB-0.5
  research rule, deliberately, for production.
- **Medium on actuation edges.** The Shuttle OMS valve pistons are GN2-driven
  and the F-1 uses RP-1 as hydraulic fluid. Converting the DB-0.5 graphs showed
  that forbidding a carrier on non-flow edges would lose that medium.

## Verified by

- `test_engine_evidence_model.py`: every validator, positive and negative.
- `test_engine_evidence_schema.py`: strict loading, round-trip, fingerprint,
  refusal of solid-evidence files.
- `test_engine_evidence_stress.py`: RS-25, J-2, RL10A-3-3A, LMDE and RD-170
  cases, plus all nine DB-0.5 verified topologies converted into production
  graphs and validated. That conversion is a stress test; the research files
  are not production data.

## Independent review

A separate reviewer checked the schema before acceptance. It found two major
gaps, both fixed:

- the field-path obligations could be dodged by naming (`isp`, `vacuum_thrust`)
  and wrongly applied to `thrust_chamber_count`;
- there was no stage- or system-level topology, so common tanks feeding several
  engines could not be modelled without duplicating hardware.

It also found these minor issues, all fixed:

- the alias clash check missed unit and family names and Unicode dashes;
- rights text was held in two unlinked places;
- the blocked-source rule was not fully enforced;
- a `Missing` value had to state conditions;
- the regression check ignored first-stated-by sources and reconstruction
  schematics, and always refused unit-level values;
- a mixture-ratio setting did not have to state its basis.

The reviewer confirmed the duplicate-document, acyclicity, operating-point
scope and conflict logic.

## Limits

- Field-path vocabularies (which tokens a field accepts, e.g. `TAP_OFF` vs
  `TAPOFF`) are not fixed. DB-2 decides them per field as records arrive; an
  advisory registry is a DB-2 task.
- Printed precision (decimals, significant figures) is kept only in
  `value_as_printed`, not as separate fields as `ReportedValue` does.
- Two variants may share a designation; only aliases are checked for name clashes.
- Rights policies are recorded, not adjudicated; legal review stays outside
  the schema (`RIGHTS_MATRIX.md` §7).
- No engine records ship. DB-2 decides which source-verified records become
  production assets.
