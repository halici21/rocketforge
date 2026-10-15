# RocketForge R3 simplification — program status

The canonical continuity record for the R3 program. Read this first when resuming. The gate list and
the per-gate scope come from the "Proposed phases" section of
[ROCKETFORGE_R3_SIMPLIFICATION_AUDIT.md](ROCKETFORGE_R3_SIMPLIFICATION_AUDIT.md), and the evidence
for each closed gate is in its "R3-x — done" section there. No R4 is defined.

Branch: `claude/r3-simplification`, fast-forward pushes only. Master is not merged into.

| Gate | Scope (audit) | State | Commit |
|---|---|---|---|
| Phase 0 | audit | done | `c27e3c8` |
| R3-A | U1, C4, U2(a), U8 (+U6 by owner decision) | accepted | `2f09a10` |
| R3-B | U3, U4, U5 | accepted | `3ec5f0f` |
| R3-C | C1 property helper + frozen surface test | accepted | `9982243` |
| R3-D | C2/C3 shared table, readout, inspector components, per-page parity | accepted | `ea01220` |
| R3-E | P1–P3 performance, before/after numbers | P2, P3 closed by measurement (no code change); **P1 held for an owner decision** | this commit (see git log) |
| R3-F | U2(b) chain strip (marked optional in the audit) | **current** | — |

## Frozen decisions and invariants

- Owner decisions of 2026-10-12 (audit, "Owner decisions"): placeholder pages deleted; every
  compressible page opens on its visual relation; one empty-state sentence per card, scientific scope
  chips and caveats stay.
- No change to solved numbers, tolerances, frozen baselines, providers or CEA behaviour.
- The QML-visible surface of the seven compressible controllers is pinned by
  `tests/application/test_compressible_property_surface.py` (captured at 3ec5f0f).
- R3-B's field fixes are pinned by `tests/application/test_pressure_units.py` (unit switch and step
  precision; 0.35 MPa + one step = 450 000 Pa).
- Each gate closes with: focused tests, Base suite green, `git diff --check`, independent review with
  zero unresolved material findings, then one forward commit and a normal push.

## Blockers

- R3-E P1 (background provider pre-import) contradicts the documented lazy-provider contract
  (`main.py`, CLAUDE.md). It saves at most ≈ 0.85 s once. The owner must choose; see the audit's R3-E section.

## Last verification

R3-D: Base 9531 passed, 448 skipped; 28 capture scenarios against a pristine 9982243 tree, texts
identical, pixels within the 2/255 run-to-run noise, 0 QML warnings; first review 1 material (fixed),
confirmation review 0 material.
