# Rocket Performance visual pilot — Checkpoint

A visual-architecture pilot for **one** workspace. Not a physics phase, not a
backend refactor, not a global UI rewrite.

**Status:** **COMPLETE**

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | **closed** |
| LAST_COMPLETED_STEP | the verdict |
| NEXT_STEP | — the pilot is complete |
| NEXT_ACTION | Owner decision on the rollout candidates in section 10 of the implementation report |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6831 passed, 154 skipped**, exit 0 | 6831 / 154 | ✅ |
| Production (`.venv-cea`) | **6986 passed, 2 skipped**, exit 0 | 6986 / 2 | ✅ |

Freeze verification and the before-capture matrix are recorded below.

## Baseline capture matrix

`acceptance/ui_visual_pilot/before/` — **27 captures**, 0 Qt warnings.

Chemistry solves per interaction, measured at the gateway's own provider:

| Interaction | Solves |
| --- | --- |
| ε edit + calculate | **0** |
| ambient edit + calculate | **0** |
| scale edit + calculate | **0** |
| view / theme / resize | **0** |

This is the property the redesign must not break.

## Visual audit

`docs/design/ROCKET_PERFORMANCE_VISUAL_AUDIT.md`.

| Dimension | Finding |
| --- | --- |
| Hierarchy | colour-only; **Isp is the 13th row** of a 15-row uniform list |
| Composition | form-left / list-right; no visual centre |
| Cards | **9 `RFPanel`** across three tabs, several redundant |
| Typography | effectively one numeric level |
| Engineering object | **absent** — a nozzle tool that never shows a nozzle |
| Motion | none |
| **1366×768** | **`RESPONSIVE_LAYOUT_BLOCKER`** — left rail clipped mid-section (ε, ambient, scale unreachable); c_eff, Isp and all scaled results below the fold |

Preserved deliberately: refusal semantics, qualifier text, monospace aligned
numerics, the model/oracle separation, zero chemistry re-solve.

## State by area

| Area | Status |
| --- | --- |
| Opening regressions | ✅ both match |
| Before captures | ✅ 27, 0 warnings |
| Visual audit | ✅ written |
| Composition design | ✅ three zones + trace |
| Local primitives | ✅ 5 added, 2 superseded and removed |
| Hero visualization | ✅ schematic gas path, solved-snapshot driven |
| Rails and trace | ✅ pinned rails, one model-trace line |
| States and motion | ✅ 10 canonical states; one animation, no idle motion |
| Responsive | ✅ blocker closed at 1366×768 |
| Scientific parity | ✅ 5688 fields, 0 differences |
| Accessibility | ✅ pilot-owned PASS; one shared-token finding open |
| Runtime cost | ✅ inside budget; memory halved vs the previous design |
| Package | ✅ clean build, 8/8 packaged self-tests, source ↔ packaged 0 differences |

## Blockers

**None open against this pilot.**

`RESPONSIVE_LAYOUT_BLOCKER`, raised by the audit against the *previous* design
at 1366×768, is **CLOSED** — see Closure below.

Two findings are recorded and deliberately left to the owner, neither of them
a defect this pilot introduced: the shared `Theme.textMuted` token sits just
below WCAG AA, and the QML layer retains memory under repeated recalculation.


---

## Closure

| Deliverable | Where |
| --- | --- |
| Design rationale | `docs/design/ROCKET_PERFORMANCE_VISUAL_PILOT.md` |
| Implementation report | `docs/engineering/implementation/ROCKET_PERFORMANCE_VISUAL_ARCHITECTURE_PILOT.md` |
| Acceptance manifest | `acceptance/ui_visual_pilot/ACCEPTANCE_MANIFEST.md` |
| Rules | `tests/test_performance_visual_architecture.py` — 62 tests |

### The governing rule, answered

**27 captures, 5688 leaf fields, 0 differences.** Chemistry solves per
interaction unchanged at 0 for ε, ambient, scale and every view, theme and
resize. Total provider solves 1 → 1. Qt warnings 0 → 0.

### The audit's blocker, answered

`RESPONSIVE_LAYOUT_BLOCKER` is closed. At 1366×768 the expansion ratio,
ambient and engine size are all reachable, the rail says when it continues,
Calculate is pinned and never scrolls away, and Isp, Cf, c\*, c_eff and thrust
are all visible without scrolling.

### Closing gates

| Gate | Result |
| --- | --- |
| Base (`.venv`) | 6893 passed, 154 skipped, exit 0 |
| Production (`.venv-cea`) | 7048 passed, 2 skipped, exit 0 |
| Production, repeated | 7045 passed, 2 skipped, exit 0 (mid-run) |
| Frozen contracts | 102 passed, all nine verify |
| Source self-tests | 8 of 8 |
| Clean build + packaged self-tests | exit 0; 8 of 8 |
| Source ↔ packaged | 5189 fields, 0 differences |

### Open, and deliberately not fixed here

1. `Theme.textMuted` at 4.21:1 / 4.33:1 — a shared token, below WCAG AA.
   Raising it is a theme change affecting every workspace.
2. QML-layer memory retention under repeated recalculation — pre-existing,
   halved by this pilot, not eliminated.
3. `performance_before.json` cannot be regenerated: its UI tree was destroyed
   by the clean rebuild. The scientific baseline is unaffected.
