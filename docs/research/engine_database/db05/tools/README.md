# DB-0.5 tools

Research tooling, not part of RocketForge. These scripts produced every JSON
file in `..` (the `db05` folder).

| File | Role |
| --- | --- |
| `fetch.py` | Downloads the P0 queue documents and `extra_urls.json`; records HTTP status, size, SHA-256, page count and the NTRS copyright/export metadata in `access_log.json`. Documents go to `$DB05_CACHE` (default `./cache`) and are **not committed**. |
| `render.py`, `sheet.py` | Render a page (or a crop) and page contact sheets from a cached PDF, for viewing figures. |
| `ledger.py` | The record types: `D` (document identity and rights as checked), `A` (assertion: value as printed, unit, conditions, locator), `S` (schematic viewed), `T` (topology graph), `C` (conflict outcome), `X` (DB-0 assertion disposition), `BLOCK` (access blocked). |
| `ledger_*.py` | One file per anchor group, typed while reading the documents. These are the evidence; the JSON is generated from them. |
| `build.py` | Validates every reference (opened source, locator, node ids, DB-0 indices), writes `documents_opened.json`, `assertions.json`, `schematics_viewed.json`, `topology/`, `conflicts.json`, `db0_dispositions.json`, and updates `../../data/sources.json` and `source_registry.csv` (access state, new `SRC-DB05-*` sources). |
| `candidates.py` | Applies the SCHEMA_PROPOSAL §6 regression-candidate rule and writes `regression_candidates.json`. |

Run from the repository root with an interpreter that has PyMuPDF for the
render step: `python docs/research/engine_database/db05/tools/build.py`, then
`.../candidates.py`. `build.py` is idempotent.
