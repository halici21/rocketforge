# Analysis Experience R2 — Design System Changes

Additive and surgical. The accepted Obsidian/Champagne identity, the
spacing scale, the radius scale and the control heights are unchanged;
this phase added one token, one component scale, and one surface rule.

## Typography

One addition:

```
readoutHero: 32   // mono -- hierarchy Level 1
```

A golden-ratio step above the existing `readoutLarge: 20`. The existing
13 / 15 / 20 / 21 values were left alone rather than retrofitted to a
ratio: they are shipped and widely consumed, and `qt-ui-design`'s own
guidance for an established scale is a surgical addition over a rebuild.

`RFResultValue` gained a matching `scale: "hero"`.

Used by exactly two things so far — the Oblique Shock shock angle and the
Thermochemistry chamber temperature — because each is the one number its
workspace exists to produce. A third hero on a screen would mean there is
no hero.

## Uppercase

`RFSectionLabel` is unchanged, but it is used less. The reduction came
from removing bordered panels rather than restyling the label: every
`RFPanel` header forces one, so dropping a panel drops its uppercase
header with it. Oblique Shock's Calculator went from ten uppercase labels
in one screen to six.

Short uppercase identifiers survive in one place by intent: the 64 px
family rail, where they function as compact glyphs in an icon-width
column rather than as section headings.

## Surfaces

`RFPanel`'s existing `chromeless` property (added in the structural
recovery phase) is now the default choice for an analysis region rather
than an exception. Applied to the Oblique Shock input rail, results region
and chart panel, and to the Trade Study sweep chart cards.

The test before adding a border is unchanged and was applied
case-by-case: what is this border doing that spacing, alignment and a
divider could not?

## Navigation metrics

```
browserPanelWidth: 240 -> 64
browserPanelMin:   200 -> 64
browserPanelMax:   320 -> 200
```

## What did not change

Theme tokens, the spacing scale, radii, motion durations and easing,
control heights, the series palette, the accent's meaning (selection and
focus only), and every scientific-honesty rule — stale, unavailable,
refused, provenance, and the schematic-versus-solved distinction.
