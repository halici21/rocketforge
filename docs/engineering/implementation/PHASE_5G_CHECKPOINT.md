# Phase 5G — Checkpoint

Integrated propulsion analysis acceptance and freeze: Thermochemistry, Ideal
Rocket Performance, Trade Study, over frozen Compressible v1.

**Status:** ✅ **COMPLETE — PROPULSION ANALYSIS v1.0 ACCEPTED / FROZEN**

Not a feature phase. No new physics, no new design variables, no new
optimisers, no UI redesign.

Report: [PHASE_5G_INTEGRATED_PROPULSION_ACCEPTANCE.md](PHASE_5G_INTEGRATED_PROPULSION_ACCEPTANCE.md).
Evidence: `acceptance/phase_5g/ACCEPTANCE_MANIFEST.md`.

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | — closed |
| LAST_COMPLETED_STEP | STEP 104 — final verdict returned |
| NEXT_STEP | — Phase 5G is closed |
| NEXT_ACTION | Next module per `06` §8 step 1: `physics.fluids` (recommendation only; numbering is the owner's call) |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6390 passed, 118 skipped**, exit 0, 58.99 s | 6390 / 118 | ✅ |
| CEA-enabled (`.venv-cea`) | **6510 passed, 1 skipped**, exit 0, 59.26 s | 6510 / 1 | ✅ |
| Frozen Compressible | **22 / 22 byte-identical** | 22/22 | ✅ |

Digest `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502`,
verified by recomputing each file's recorded `sha256[:16]` against the Phase 4G
manifest. The baseline was clean before any freeze work began.

## Closing gates

| Gate | Result |
| --- | --- |
| Base (`.venv`) | **6451 passed, 118 skipped**, exit 0 |
| CEA (`.venv-cea`) | **6571 passed, 1 skipped**, exit 0 |
| CEA, repeat run | **6571 / 1 — identical** |
| Frozen Compressible | **22 / 22 byte-identical**, digest unchanged |
| Freeze suite | **61 passed** |
| Architecture + freeze rules | **305 passed** |

+61 tests. No tolerance widened, no test removed, no case skipped, no provider
substituted.

---

## Files created

**Production (2)**

| File | Purpose |
| --- | --- |
| `rocketforge/core/freeze.py` | manifest algorithm `rocketforge-freeze-manifest/1` |
| `rocketforge/application/shellsmoke.py` | `--selftest-workspaces` |

**Tests (1)** — `tests/acceptance/test_propulsion_freeze.py` (61)

**Harnesses (7)** — `experiments/phase_5g/`: `api_surface_audit.py`,
`contract_audit.py`, `integrated_acceptance.py`, `determinism_and_soak.py`,
`generate_freeze_manifests.py`, `package_audit.py`,
`architecture_and_benchmarks.py`

**Documents (7)** — `THERMOCHEMISTRY_API_V1.md`,
`ROCKET_PERFORMANCE_API_V1.md`, `TRADE_STUDY_API_V1.md`,
`PROPULSION_ANALYSIS_API_V1.md`, `PROPULSION_ANALYSIS_LIMITATIONS.md`, this
checkpoint, and the implementation report

**Artifacts** — 26 JSON files and 8 capture directories under
`acceptance/phase_5g/`, plus `ACCEPTANCE_MANIFEST.md`

## Files modified

| File | Change |
| --- | --- |
| `rocketforge/providers/cea/propellants.py` | two public tables → `MappingProxyType` |
| `rocketforge/providers/cea/species.py` | `CEA_FORMULAS` → `MappingProxyType` |
| `ui/components/RFEngineeringTable.qml` | header anchored both sides + elide + alignment |
| `main.py` | `--selftest-workspaces` dispatch |
| three API drafts | superseded banners |

---

## Status by area

| Area | Status |
| --- | --- |
| Baseline tests | ✅ opening matched, closing green |
| Focused validation | ✅ |
| Integrated validation | ✅ 7 canonical artifacts, worst identity residual 0.0 |
| API audit | ✅ 160 exports, 0 accidental, 0 mutable, 0 unfrozen |
| Architecture audit | ✅ no violation, no cycle, deps `PySide6` + `numpy` |
| Provenance audit | ✅ one point rebuilt from its record, exact |
| Determinism | ✅ exact float64 equality, A/B/A clean |
| Soak | ✅ 14 865 points, 405 solves, no leak (+0.030 MB / 10 rounds) |
| UI regression | ✅ 134 captures, 0 Qt messages; one header defect found and fixed |
| Package | ✅ clean rebuild, 2117 files, 192.9 MB, nothing forbidden |
| Source/package parity | ✅ 16 650 fields, 0 differences |
| Freeze manifest | ✅ 4 manifests, digests reproducible from the prose alone |

## Current test result

Base 6451 / 118, CEA 6571 / 1, both exit 0, CEA repeat identical.

## Current manifest state

| Contract | Files | Digest |
| --- | --- | --- |
| THERMOCHEMISTRY API v1.0 | 13 | `44312c23c71cfd52…` |
| IDEAL ROCKET PERFORMANCE API v1.0 | 6 | `d07f4ff9017efdfe…` |
| TRADE STUDY API v1.0 | 12 | `912065266fccc6d5…` |
| NASA CEA PROVIDER v1.0 | 11 | `0a46b5f089a9cc7a…` |
| COMPRESSIBLE FLOW v1.0 (4G) | 22 | `8f0d1cf5685e0c52…` |

Full digests in `acceptance/phase_5g/freeze_manifest.json`.

## Current blockers

None. Two product defects were found during the phase and both were fixed:
the three public mutable CEA reference tables, and the `RFEngineeringTable`
header that could overprint its neighbour. Three defects in the phase's own
audit code were corrected without relaxing a tolerance.
