# Analysis R2 — Nozzle Lab 1366x768 Solution clip closure

**Verdict: CLIP CLOSED.** Fixed by restructuring the Solution's information
layout at compact height. No Flickable, no font below the accepted scale, no
quantity hidden, no scrollbar.

## The defect, measured

At 1366x768 the Operating point workspace has **508px** of content height for
three stacked panels:

| Panel | Height |
| --- | --- |
| Flow regime | 113px |
| **Solution** | **241px** (209px inside its chrome) |
| Internal normal shock | 122px |

The Solution's content column asked for **252px**. The 43px shortfall clipped
seven quantities: Mass flow, Throat Mach, Exit Mach, Choking onset, Shock at
exit, Ideal expansion, Design exit Mach.

## Why not a Flickable

Tried in an earlier pass and rejected twice over. Mechanically it collapsed
every group to a single row — a `Layout` inside a `Flickable` is not laid out
by a parent `Layout`, so it needs both dimensions set explicitly — and that
attempt was reverted rather than shipped.

The deeper reason is that scrolling is the wrong model here. These fourteen
quantities describe **one state of one nozzle** and are read together. Putting
half of them below a fold converts a glance into a scroll. The panel was not
too long; it was the wrong shape.

## What changed, gated entirely on `page.compact`

`readonly property bool compact: page.height < 620` already existed — it is
what already decided whether the nozzle object yields. No new width or height
constant was introduced.

| Aspect | Roomy | Compact |
| --- | --- | --- |
| group arrangement | 2 columns x 2 groups | **4 groups abreast** |
| result cell | label and value on one line | **label above value** |
| hero | two lines, `readoutHero` 32 | **one line, `readoutLarge` 20** |
| group row spacing | `spacing.xs` | 0 |
| column gutter | `spacing.xl` | `spacing.m` |

### Why each step was necessary

Four abreast is the **only** arrangement that fits vertically: four rows plus
a group label is ~112px against 209px available, while 2x2 needs ~248px.

Four abreast then does not fit *horizontally* with the existing side-by-side
cell — each group gets ~222px and a label plus a value needs ~247px. That
intermediate state was captured and inspected: values ran into the next
column (`7.37872 kg/s` into "Exit pressure") and labels elided to `p_b…`.
Stacking the cell drops the requirement to ~145px because the label and the
value stop competing for one line.

That left 223px against 209px. Inlining the hero and pinning the compact row
height closed the last 14px. Final: **194px into 209px**, with slack.

## Worst case, established from the source

`nozzle_service._rows_for` emits a fixed **3/3/4/4** across Regime / Flow /
Exit state / Thresholds **regardless of regime**. The shock's eight rows go to
a separate panel. So the tallest group is always four rows, and the
internal-shock regime is the worst case on both axes simultaneously: it keeps
all fourteen Solution rows (its hero comes from the shock group) *and* it is
the only regime that adds a panel taking height from the Solution. Every other
regime has more room and one row fewer.

No row in this service is ever emitted with `available=False`, so no long
"unavailable" status string can appear and overflow.

## Evidence

| Size | Theme | States | Result |
| --- | --- | --- | --- |
| 1366x768 | dark | operating point, regime map, 4 regimes | pass |
| 1366x768 | light | operating point, regime map, 4 regimes | pass |
| 1920x1080 | dark | operating point | **0 differing pixels vs approved** |
| 2560x1440 | dark | operating point | roomy composition retained |

Regimes: internal normal shock (p_b/p0 0.70), overexpanded (0.30),
underexpanded (0.05), unchoked subsonic (0.98). The regime-dependent hero
follows correctly and carries its label inline in every case, which is what
keeps a changing hero honest.

## The hero at compact

`readoutLarge` is inside the accepted type scale, and at 20px against
12.5–15px for every other value the hero is still unmistakably the largest
number in the panel. It is still sourced from the result object
(`page.heroRow`), never a live input, so nothing about the stale-vs-solved
boundary moves.

## Verification

- 60 resize cycles plus 18 single-pixel steps straddling the 620px breakpoint:
  **0 Qt warnings, 0 binding loops**.
- Field-level scientific parity across the resize: **0 differences** in all six
  workspaces, roomy vs compact and roomy vs restored, with a live negative
  control.
- Solve-call parity including the responsive transition: **0 solves** across 46
  interactions.
