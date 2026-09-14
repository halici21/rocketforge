# RF screenshot matrix -- detail and template

## The pattern the pilot established

The accepted Rocket Performance pilot captured 27 states: 3 resolutions
(2560x1440, 1920x1080, 1366x768) x roughly 9 canonical scientific/theme
combinations, run identically before and after the redesign so the two sets
could be compared field-by-field and, separately, actually looked at. That
27-state matrix is the concrete precedent for the per-workspace tables in
`SKILL.md` -- when adding a new workspace's matrix, size it similarly:
enough states to cover every materially different thing the page can show,
not an exhaustive cross-product of every input combination.

## Template for a new workspace

When a workspace does not yet have a captured state matrix, derive one by
answering:

1. What does the empty/unconfigured state look like? (always capture this)
2. What is the single most common "everything worked" state?
3. What states does the *engineering model itself* refuse or warn on? (a
   validity-envelope refusal, a provider warning, a numerically borderline
   case) -- these are exactly the states most likely to be visually
   neglected because they are rare in normal use.
4. What does a stale/superseded/pending state look like?
5. Does this workspace have a sign convention or a term that can go
   negative without being an error? (Rocket Performance's pressure-thrust
   term is the existing example) -- capture that state explicitly, since a
   negative value styled like an error is a real defect this project has
   made before.
6. Any workspace-specific edge the model has: for Trade Study, an
   infeasible design and a large study; for Line, the transitional-Reynolds
   refusal; for Thermochemistry, a condensed-phase result versus one with
   no condensed species.

## Reusing the pilot's capture tooling

`experiments/ui_visual_pilot/capture_matrix.py` drives the application
offscreen (`QT_QPA_PLATFORM=offscreen`), walks a defined list of states,
and saves one PNG per (state, resolution) pair plus a JSON snapshot of every
relevant controller property at that moment -- the JSON is what a
field-level parity check (`rf-scientific-ui-contract`'s governing test)
diffs; the PNGs are what a human, or `design-review`, actually looks at.
Both must be produced together -- a JSON-only capture cannot catch a
rendering defect, and a screenshot-only capture cannot catch a subtle
numeric regression at scale.

`experiments/ui_visual_pilot/visual_parity.py` is the concrete
implementation of "compare against a prior accepted baseline without
requiring pixel-identical output" -- it measures ink ratio (did the page
render materially less content than before) and changed-pixel fraction,
with thresholds tuned so that anti-aliasing and minor text reflow do not
trip it, but a silently emptied region does. Reuse or adapt this rather
than building bespoke pixel-diffing per workspace.

## What "actually inspect" means in practice

Load each capture with an image-reading tool and look at it -- do not read
the QML that produced it and reason about what it must look like. This
project has a documented case where doing the latter produced a report of
"27 captures, 0 differences, PASS" while the rendered image showed an
entire section of the page missing. The parity check was correct about
every field it checked; it was never capable of checking whether the field
was actually painted to the screen.
