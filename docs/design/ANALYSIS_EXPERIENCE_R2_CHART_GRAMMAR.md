# Analysis Experience R2 — Scientific Chart Grammar

## The blocking defect, and its cause

The brief named chart annotation collision as a blocking condition. It was
real and reproducible: in the θ–β–M view, "β at θ_max 64.67°" and
"M₂ = 1 at β 61.49°" printed on top of each other.

The cause was structural, not cosmetic. `RFLineChart` drew every
horizontal (`axis: "y"`) guide label right-aligned at one fixed
x-coordinate (`x1 - 4`), separated only by each guide's own y position.
Two guides at nearby values therefore drew their labels in the same place,
with no collision detection of any kind.

## The fix

Label placement is now band-aware. Each label claims a vertical band; a
label whose preferred band is already occupied is pushed clear in
alternating directions until it finds free space, and a label with nowhere
legible to go is dropped rather than overdrawn — the guide line itself
still draws, so no information is silently invented or lost.

Marker labels in the right-hand zone (where they share the column with
guide labels) claim from the same set of bands.

## Chart proportion

Proportion follows the analytical task:

| State | Treatment |
| --- | --- |
| The chart answers the page's question | It dominates: Trade Study sweeps take an equal share of real workspace height with a 220 px floor; θ–β–M owns its view. |
| The chart supports numbers that answer it | It is secondary but real: the Calculator's θ–β–M panel is 320 px, up from 236, not a strip. |
| Space is tight (1366×768) | Reflow, never shrink. The primary plot keeps a 280 px floor, its explanatory paragraph is dropped, and the secondary curve yields entirely rather than rendering with a clipped axis. |

## Visual weight

Unchanged from the accepted system, and restated because the redesign had
opportunity to break it: data is the strongest layer, the grid is
significantly weaker than the data, axes are readable without dominating,
reference lines stay subdued and dashed, and the champagne accent marks
selection only. No glow, no neon, no gradient fills.

## Light theme

Both themes were captured and inspected for every pilot. The light
register is the same system, not an inversion: the same guide/grid/data
hierarchy holds, and the collision fix is theme-independent because it is
geometric.

## What was deliberately not done

`RFLineChart` (Canvas-based, owns guides/markers/series) and
`RFPlotSurface` (frame-only, children position themselves) remain two
components. Unifying them would mean rewriting every consumer of both in
a phase whose brief explicitly forbids broad refactors; the collision fix,
the proportion rules and the responsive floors were applied to each in
place instead. Recorded here as a known, deliberate boundary rather than
an oversight.
