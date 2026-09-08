# Rocket Performance — visual pilot

The workspace was a competent calculator. This is what it became, why each
decision was made, and what it is still not allowed to claim.

Read `ROCKET_PERFORMANCE_VISUAL_AUDIT.md` first: it was written before any code
changed, from the 27 baseline captures, and it is what this document answers.

---

## The thesis

**A propulsion workspace should show the propulsion object.**

The audit's largest finding was that the page computed a nozzle and never
depicted one. Everything else — the flat fifteen-row list, the colour-only
hierarchy, the absent centre — followed from that absence: with no object to
compose around, the page could only be a form beside a table.

So the redesign puts the gas path in the middle, gives the numbers a real
hierarchy around it, and deletes the containers that typography can replace.

---

## Composition

Three zones and a trace, at every supported size.

| Zone | Contents | Width |
| --- | --- | --- |
| **Input rail** | chamber source, gas model, nozzle, ambient, engine size | 236 px compact, 268 px otherwise — pinned |
| **Propulsion canvas** | the schematic gas path, its stations, the exit relation | everything left over |
| **Readout rail** | Isp, then Cf, c\*, c_eff, thrust; then the Cf and thrust terms | 250 / 290 / 320 px |
| **Model trace** | model, gamma, ambient, regime, scale, warnings | full width, one line |

The rails are pinned rather than proportional. A readout rail that grows with
the window makes a 2560 layout where the numbers drift apart and a 1366 layout
where they collide; fixing the rails puts every size's spare width into the one
element that benefits from it, which is the drawing.

**Calculate and Reset sit outside the scrolling body.** At 1366×768 the input
rail does not fit its own content. The old design clipped it, which is the
`RESPONSIVE_LAYOUT_BLOCKER` the audit recorded. Scrolling fixes the reach, but
the one control that must never scroll out of view is the one that produces a
result, so it is pinned beneath a divider and the body scrolls behind it.

**A rail that overflows says so.** The application's scrollbar is quiet by
design — invisible until touched — which is right for a rail whose content
fits and wrong for one whose content does not. While, and only while, there is
more than fits, the bar stays visible and its thumb says how much more.

---

## Hierarchy

The audit's complaint was that Isp — the quantity the workspace exists to
produce — was the thirteenth row of fifteen identical rows, distinguished only
by being amber.

Now:

| Level | Treatment |
| --- | --- |
| **Isp** | 30 px mono, medium weight, first in the rail |
| Cf, c\*, c_eff, thrust | 20 px mono, regular |
| symbols, labels, units | 10.5–12 px, `textSecondary` |
| Cf and thrust terms | a labelled breakdown, values right-aligned |
| model trace | one quiet line beneath everything |

Four typographic levels where there was one, and no meaning carried by hue.

`thrust` is appended to the headline list only when an engine size makes it
real. Nothing is shown as zero in its place.

---

## The canvas, and what it refuses to claim

`PerfNozzleCanvas.qml` draws chamber → convergent → throat → divergent → exit
plane, with the centre line, the throat station and a flow arrow.

**It is driven by the solved area ratio, never by the input field.** The
controller publishes `solvedRadiusRatio`; the view divides by it and derives
nothing. Binding the drawing to the live input would animate the nozzle to a
shape nobody has solved while the numbers still showed the previous result.

**The exit radius is fixed and the throat is derived**, so a larger expansion
ratio visibly narrows the throat against a constant exit. That is what an
expansion ratio means, and it is the one physical fact the drawing carries.

**It is not a contour.** RocketForge has not solved a bell, a Rao profile, a
cone half-angle or any chamber dimension. The wall is a plain schematic curve,
the axial scale is arbitrary, and the drawing says so on itself, permanently:

> SCHEMATIC — AREA EXPANSION ONLY, NOT A SOLVED CONTOUR

A test asserts that label is present, and a second test — reading the code with
comments stripped — asserts that no pilot component ever renders the words
"Rao", "bell contour", "half-angle", "Mach distribution" or "pressure field".

### The unsolved state

With no chamber, the workspace refuses. It does not estimate, and it does not
show a dead grid: the refusal is a centred column at a readable measure, and
beneath it a dimmed unsolved outline so the page reads as an instrument waiting
for an input.

That outline's proportion is invented, so it is kept **inside** the canvas as
`placeholderRatio` and cannot be supplied by a caller. A placeholder can never
occupy `radiusRatio`, the property that otherwise only ever carries a solved
result, and it carries its own weaker label:

> UNSOLVED OUTLINE — ILLUSTRATIVE, NOT AN AREA RATIO

---

## Motion

One animation: `drawnRatio`, so a changed expansion ratio reads as a change to
the same object rather than as a different picture. Nothing else moves.

There is no timer, no `running: true`, no infinite loop, and the canvas
repaints only when something it draws has actually changed — state, theme or
size. Measured idle cost is **10.4 ms of CPU per second** with a result on
screen.

---

## Cards removed

`RFPanel` in the Performance tab: **2 → 0**. Hairline dividers and section
labels do the same work without a second border around content that already has
one. The Model and Provider-comparison tabs were left alone; they are not part
of this pilot.

---

## Accessibility

Measured, not assumed — `experiments/ui_visual_pilot/accessibility_audit.py`.

* **Contrast.** Every pair the workspace actually draws, in both themes, against
  WCAG 2.1 AA. Everything the pilot owns passes. Several values moved to get
  there: the honesty label, the station labels and the exit-state symbols were
  drawn in `textDisabled`, which measures **2.43:1** — the label that stops the
  drawing being misread was among the least readable text on the page. Stale
  values were dimmed to the same token; they are now dimmed to a readable one,
  because a stale number is still the last one that was actually solved.
* **Keyboard.** Driven by real Tab events: **33 distinct stops**, reaching both
  gamma selectors, the expansion ratio field, ambient, scale, Calculate and
  Reset.
* **Not colour-only.** Stale, superseded chamber, regime, the exit/ambient
  relation, the sign of the pressure term and the warning count are all carried
  in words. The status chips state their condition and use the tone only for a
  dot beside the text.

**One finding is not fixed and is not the pilot's to fix.** `Theme.textMuted`
measures 4.21:1 (dark) and 4.33:1 (light) against the page, just under the
4.5:1 AA asks of body text. It is a shared token used by every workspace, so
raising it is a theme change. Recorded as a rollout item; nothing in this
workspace depends on it alone.

---

## What was preserved, deliberately

The audit said these were already right, and they are unchanged:

* **Refusal semantics.** No chamber → no numbers. No engine size → thrust,
  mass flow and areas withheld entirely, never shown as 0.
* **Qualifier text** beside the quantities that get misread.
* **Monospace numerics** with aligned decimals.
* **The model/provenance separation**, so the oracle cannot be mistaken for a
  RocketForge result.
* **Zero chemistry re-solve** on any nozzle, ambient, scale, view, theme or
  resize interaction. Measured again after the redesign: still **0**.

---

## What this pilot did not do

No 3D. No stock imagery, NASA photography or downloaded renders — the
centrepiece is native vector geometry and the directory contains no image or
font asset at all. No other workspace was restyled, and no shared component was
changed: the overflow cue is a property override on an instance.
