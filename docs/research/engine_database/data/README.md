# DB-0 research data

> **DB-0.5 (2026-10-08).** Sources with `access = fetched` were opened in DB-0.5; their evidence lives in
> [../db05/](../db05/) (documents, assertions, schematics, topology, conflicts, dispositions, regression
> candidates), checked by `tests/research/test_db05_research_artifacts.py`. Values in this folder are still
> the DB-0 search-summary record.

Machine-readable research artifacts for the DB-0 package. **Research data, not
a runtime asset:** nothing under `rocketforge/` reads these files, nothing here
is shipped in `dist/`, and no value here is regression-grade. Every value was
read from a web-search result summary; no source document was opened
([../DB0_RESEARCH_OVERVIEW.md §3](../DB0_RESEARCH_OVERVIEW.md#3-how-the-research-was-actually-done)).

Consistency is checked by `tests/research/test_db0_research_artifacts.py`.

## Files

| File | Contents |
| --- | --- |
| `engines.json` | 576 engine variant/configuration candidates (`engines`) and excluded candidates |
| `engine_inventory.csv` | flat view of `engines.json` identity and architecture fields |
| `key_values.csv` | every key value on every engine record, with status, source and locator |
| `families.json`, `family_registry.csv` | 227 families with member variant ids |
| `aliases.json`, `alias_registry.csv` | aliases (native, transliteration, index, military, former name …), with `ambiguous` and dropped-alias flags |
| `sources.json`, `source_registry.csv` | 1,057 sources with tier, rights class, access state; `source_id_aliases` maps ids merged by identical URL |
| `schematics.json`, `schematic_registry.csv` | flow/cycle schematic entries; `family_ids` where a schematic is family-level |
| `conflicts.json`, `conflict_ledger.csv` | conflicts as sets of claims; `origin` replaces `source_id` for unregistered origins |
| `anchors/<ENGINE_ID>.json` | deep anchor audits: operating points, assertions, missing fields, topology graph, coverage, schema breakers |
| `anchor_coverage_matrix.csv` | coverage judgement per anchor and field group |

## Record conventions

- **Ids.** `ENG-<country>-<designation>`, `FAM-<family>`, `SRC-<org>-<short>`,
  `SCH-…`, `CF-<branch>-<n>`. Ids are opaque and stable; merged ids are kept in
  `former_ids`. Soviet/Russian ids use `SU` or `RU` inconsistently; the
  `country` / `country_codes` fields carry the meaning.
- **Value status** (`key_values[].status`, anchor `assertions[].status`):
  `REPORTED` (a named Tier A–C source states it), `DERIVED` (arithmetic from
  reported values), `DIGITISED`, `INFERRED`, `SECONDARY_CLAIM` (only a Tier D/E
  source states it). A merge rule enforces that `REPORTED` never rests on a
  Tier D/E source.
- **Missing reasons** (anchor `missing[].reason`): `NOT_REPORTED`,
  `NOT_AUDITED`, `UNKNOWN`, `ACCESS_BLOCKED`, `RIGHTS_RESTRICTED`.
- **Topology evidence** (anchor `topology.nodes[]/edges[].evidence_status`):
  `SHOWN_IN_SCHEMATIC`, `REPORTED_IN_TEXT`, `DERIVED_FROM_BOTH`, `INFERRED`,
  `UNKNOWN`. A component absent from a graph is not shown, never absent; each
  graph's `topology_completeness` names known omissions.
- **identity_evidence**: `SOURCED` or `UNSOURCED_PLACEHOLDER` (identity from
  the research brief or background knowledge only — a verification checklist,
  not data).
- **Units are stored as printed** (RocketForge evidence rule: convert at the
  point of use). The vocabulary includes `kN`, `N`, `MN`, `lbf`, `klbf`, `lb`
  (thrust as printed), `tf` / `tonf` / `t` / `tonne-force` / `metric tons`,
  `kgf` and `kg` (German WWII sources print thrust in "kg", meaning kgf), `s`,
  `kgf.s/kg`, `N.s/kg`, `m/s`, `MPa`, `bar`, `psia`, `psi` (basis often
  unstated), `kgf/cm2`, `kg`, `mm`, `m`, `rpm`, `min-1`, `K`, `hp`, `%`, `:1`,
  `-`. Some values are printed strings carrying two units (`"845 kN (190,000
  lbf)"`, unit `kN/lbf`). Field names such as `thrust_vac` / `thrust_sl` record
  what the source labelled; an unlabelled `thrust` is ambiguous by definition.
- `branch_disagreements` on an engine lists fields where research branches
  recorded different values; the record shows the higher-precedence one.
