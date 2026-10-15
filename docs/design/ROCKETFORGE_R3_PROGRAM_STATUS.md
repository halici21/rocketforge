# RocketForge R3 simplification — program status

**Program status: CLOSED (2026-10-15).** Every gate of the audit's "Proposed phases" is closed.

The canonical continuity record for the R3 program. Read this first when resuming. The gate list and
the per-gate scope come from the "Proposed phases" section of
[ROCKETFORGE_R3_SIMPLIFICATION_AUDIT.md](ROCKETFORGE_R3_SIMPLIFICATION_AUDIT.md), and the evidence
for each closed gate is in its "R3-x — done" section there.

Branch: `claude/r3-simplification` (kept; fast-forward pushes only while the program ran).

**Integrated into master (2026-10-15).** PR #8 (`9e0f260`) had squash-merged Phase 0, R3-A and R3-B;
its tree equals `3ec5f0f`. Merge `9bb649c` brought R3-C to the closure `77ee4ff` into master with
their history. Every conflict came from that squash and resolved to the branch side, and the merged
tree is identical to `77ee4ff`'s.

## Next program

None is defined. A search of `docs/`, CHANGELOG and the history after the closure found no R4 or other
open program:
- the engine-database line ends at DB-4A. Any further reference-engine case needs the owner decisions
  in its §7, and the model capabilities in its §9 are deferred;
- LIQ-7 Pump Foundation is PAUSED (DB-4A §9, `docs/research/engine_database/DB0_RESEARCH_OVERVIEW.md`)
  and has no written definition.

Starting a next program is the owner's call.

| Gate | Scope (audit) | State | Commit |
|---|---|---|---|
| Phase 0 | audit | done | `c27e3c8` |
| R3-A | U1, C4, U2(a), U8 (+U6 by owner decision) | accepted | `2f09a10` |
| R3-B | U3, U4, U5 | accepted | `3ec5f0f` |
| R3-C | C1 property helper + frozen surface test | accepted | `9982243` |
| R3-D | C2/C3 shared table, readout, inspector components, per-page parity | accepted | `ea01220` |
| R3-E | P1–P3 performance, before/after numbers | closed: P2, P3 by measurement (no code change); P1 NOT ADOPTED by owner decision | `6d8e374`, closure in the R3 closure commit |
| R3-F | U2(b) chain strip (marked optional in the audit) | accepted | `f5e5d0f` |

## Frozen decisions and invariants

- Owner decisions of 2026-10-12 (audit, "Owner decisions"): placeholder pages deleted; every
  compressible page opens on its visual relation; one empty-state sentence per card, scientific scope
  chips and caveats stay.
- No change to solved numbers, tolerances, frozen baselines, providers or CEA behaviour.
- The QML-visible surface of the seven compressible controllers is pinned by
  `tests/application/test_compressible_property_surface.py` (captured at 3ec5f0f).
- R3-B's field fixes are pinned by `tests/application/test_pressure_units.py` (unit switch and step
  precision; 0.35 MPa + one step = 450 000 Pa).
- Lazy provider loading (owner decision, 2026-10-15, R3-E P1): NASA CEA and CoolProp are loaded
  only on first use; a provider or workspace the user never opens incurs no provider-loading cost.
  Pinned by `tests/application/test_thermochemistry_ui_architecture.py`
  (`test_building_the_qml_singletons_does_not_import_cea`).
- Each gate closes with: focused tests, Base suite green, `git diff --check`, independent review with
  zero unresolved material findings, then one forward commit and a normal push.

## Blockers

None. R3-E P1 was closed by the owner's decision to preserve lazy loading (not adopted).

## Last verification

- R3-F (`f5e5d0f`): Base 9545 passed, 452 skipped; `test_chain_strip.py` 18 passed with NASA CEA,
  14 + 4 skipped without; final review 0 material.
- R3 closure: documentation only (this record, the audit's R3-E section, CHANGELOG); the lazy-provider
  and architecture tests re-run green. Program closed.
- Master integration (`9bb649c`): the R3 invariant tests (architecture, frozen surface, stored
  property, chain strip, issue links, pressure units) gave 127 passed, 4 skipped; the lazy-provider
  file gave 52 passed; full Base suite 9565 passed, 432 skipped, 0 failed (20 more run than on the branch worktree because this checkout has the untracked `acceptance/` evidence).
