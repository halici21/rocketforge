# QML memory retention closure + visual system rollout — Checkpoint

Two gates, strictly ordered. Gate B does not begin until Gate A passes.

---

## Program state

| Field | Value |
| --- | --- |
| PROGRAM_STATE | **GATE_A_MEMORY** |
| CURRENT_GATE | A — QML rendered-layer memory retention |
| CURRENT_WORKSPACE | Rocket Performance (accepted pilot, under diagnosis) |
| LAST_COMPLETED_STEP | STEP 9 — checkpoint created |
| NEXT_STEP | STEP 10–14 — memory harness self-tests, noise floor, pre-registered criterion |
| NEXT_ACTION | Build the calibrated harness and prove it detects memory before measuring anything |

---

## Opening gates — STEP 4–8

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6893 passed, 154 skipped**, exit 0 | 6893 / 154 | ✅ |
| Production (`.venv-cea`) | **7048 passed, 2 skipped**, exit 0 | 7048 / 2 | ✅ |
| Production, repeated | **7048 passed, 2 skipped**, exit 0 | identical | ✅ |
| Freeze / acceptance suite | **102 passed**, exit 0 | 102 | ✅ |
| Self-tests | **8 of 8**, exit 0 | 8 / 8 | ✅ |

No unexplained baseline mismatch. Cleared to proceed.

## Baseline snapshot — STEP 3

`acceptance/ui_rollout/baseline_snapshot/`

| Item | Value |
| --- | --- |
| Source files | **110** (`ui/pages`, `ui/components`, `ui/theme`, `ui/data`, `ui/Main.qml`) |
| Manifest digest | `d422a863753fe1b0…` (`rocketforge-freeze-manifest/1`) |
| Frozen contract identities | **9** recorded |
| Pilot captures preserved | **54** |
| Pilot acceptance artifacts | parity, accessibility, performance, source↔packaged |

Created **before** any destructive operation. `dist/` is not acceptance
evidence and is not relied on.

---

## GATE A — memory

| Step | State |
| --- | --- |
| Measurement harness | — |
| Harness calibration (40 MB / leak / no-op) | — |
| Pre-registered acceptance criterion | — |
| Baseline reproduction | — |
| Ablation matrix | — |
| Object-retention analysis | — |
| Python-wrapper analysis | — |
| JS-engine analysis | — |
| Scenegraph analysis | — |
| Root cause | — |
| Fix | — |
| 100-cycle | — |
| 500-cycle | — |
| 1000-cycle | — |
| Mixed interaction soak | — |
| Page destroy/recreate | — |
| Package verification | — |

### Symptom under investigation

From the accepted pilot, decomposed:

| Path | Retention |
| --- | --- |
| solver, no UI | ~0.08 MB, flat |
| controller, page never shown | ~0.19 MB, plateaus |
| controller + reading every list property from Python | ~0.02 MB |
| tab switching | **0** |
| resize | **0** |
| idle | **0** |
| **rendered page, 100 recalculations** | **~451 MB** |

Previous design: ~896 MB / 100. The pilot halved it and did not close it.

---

## GATE B — visual rollout

**NOT STARTED.** Blocked on Gate A.

| Step | State |
| --- | --- |
| Visual-system extraction | — |
| Accessibility tokens | — |
| Thermochemistry rollout | — |
| Line rollout | — |
| Fluid Properties rollout | — |
| Trade Study rollout | — |
| Engine Design rollout | — |
| Full app regression | — |
| Package acceptance | — |

---

## Files created

| File | Purpose |
| --- | --- |
| `experiments/ui_visual_pilot/baseline_snapshot.py` | the pre-rollout source snapshot |
| `acceptance/ui_rollout/baseline_snapshot/` | the snapshot itself |
| `docs/engineering/implementation/QML_MEMORY_AND_VISUAL_ROLLOUT_CHECKPOINT.md` | this file |

## Files modified

None yet.

## Current state

| Field | Value |
| --- | --- |
| CURRENT_MEMORY_RESULT | not yet measured this program |
| CURRENT_ROOT_CAUSE_HYPOTHESIS | none — evidence not yet collected |
| CURRENT_ABLATION_STATE | not started |
| CURRENT_SCIENTIFIC_PARITY | pilot: 5688 fields, 0 differences (inherited) |
| CURRENT_VISUAL_STATE | accepted pilot, unmodified |
| CURRENT_TEST_RESULT | base 6893/154, production 7048/2 |
| CURRENT_QML_MESSAGES | 0 |
| CURRENT_FREEZE_STATE | 9 contracts, all verify |
| CURRENT_BLOCKERS | none open; Gate A in progress |
