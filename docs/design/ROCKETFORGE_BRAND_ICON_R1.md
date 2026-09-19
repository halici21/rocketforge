# RocketForge Brand Icon R1

## The mark

A converging–diverging bell nozzle in cross-section: a short chamber, a
pinched throat, a long flaring bell. One closed filled silhouette in
champagne (`#D3B26A`) on an obsidian (`#0F1013`) rounded tile.

No text. No flame. No gradient. No cartoon rocket. No agency logo
resemblance. The geometry alone carries propulsion; the restraint carries
engineering.

## The design that was rejected, and why

The first pass drew the nozzle as two mirrored contour strokes plus a
centre axis line with a throat station tick — the engineering-drawing
reading. Rendered to a contact sheet and actually inspected, it failed
twice: at full size the axis line through the middle made the whole mark
read as a letterform rather than a nozzle, and below 32 px the thin
strokes dissolved into grey mush.

The response was to simplify the geometry, not to downscale the
illustration harder: axis removed, ticks removed, open strokes replaced by
a single filled silhouette. The second pass survives to 16 px as a
recognisable chamber-throat-bell shape.

A third adjustment raised the throat from the vertical midpoint to ~41%,
so the diverging bell is visibly longer than the converging section —
without it the silhouette read as an hourglass.

## Assets

| File | Role |
| --- | --- |
| `assets/branding/rocketforge_mark.svg` | Vector master, same geometry |
| `assets/branding/rocketforge_icon_1024.png` | Large raster |
| `assets/branding/rocketforge.ico` | Multi-size Windows icon (16/24/32/48/64/128/256) |
| `assets/branding/contact_sheet_dark.png` | Small-size review, dark ground |
| `assets/branding/contact_sheet_light.png` | Small-size review, light ground |
| `packaging/RocketForge.ico` | Build copy, written by the same generator so it cannot drift |

All of them are emitted by `packaging/make_brand_icon.py` from one
geometry definition, so the SVG, the PNG, both ICOs and both contact
sheets can never disagree.

## Integration

**Application / window icon.** `QGuiApplication.setWindowIcon` in
`build_engine()`. It is deliberately *not* in `configure_application()`:
that function runs before the `QGuiApplication` exists by contract, and
calling `setWindowIcon` there aborts the process — found by running it,
not by reasoning about it. Verified live: the icon loads with all seven
sizes present.

**Executable icon.** `packaging/RocketForge.spec` already pointed at
`packaging/RocketForge.ico`; the generator now writes that file, so the
shell icon and the in-app icon are the same mark.

**Bundle.** The spec's `datas` now carries `assets/branding`, so the
frozen application resolves the same icon at runtime through
`resource_root()`.

## Desktop shortcut

Deferred, per the brief's own staging rule: `RocketForge.lnk` is created
only after user visual approval and a final approved package build. Not
created in Stage A.
