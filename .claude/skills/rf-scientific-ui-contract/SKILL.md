---
name: rf-scientific-ui-contract
description: Protects the scientific meaning of a RocketForge result at the UI boundary -- what a stale/warning/refused/unavailable state must never be confused with, which quantities are commonly mislabeled (c*, Isp, Cf, density impulse, Darcy friction factor), and why simplifying a display can silently corrupt what it says. Use whenever a UI change touches how a scientific result, status, or warning is displayed, renamed, hidden, defaulted, or reformatted -- including "simplify this," "make this cleaner," "just show the number," or any redesign that changes what state is visible. Does not own layout (rf-engineering-workbench), schematic drawing rules (rf-propulsion-visual-grammar), or the underlying physics itself (frozen, out of UI scope entirely).
---

# RocketForge scientific UI contract

A visual redesign is allowed to change how a result looks. It is never
allowed to change what a result *means*, and meaning is easiest to lose
exactly where a redesign is trying hardest to simplify. This skill is the
checklist for that boundary.

The scientific computation itself is frozen and out of scope for any UI
work -- multiple frozen API contracts exist precisely so the engineering
layers underneath the UI cannot be touched by a redesign. This skill is
about the much narrower and much easier mistake: relabeling, hiding, or
reformatting a correct number into an incorrect impression.

## The governing test

Before shipping any UI change to a scientific result, ask: **if I ran the
old UI and the new UI side by side on the same solved state, would every
field say the same thing?** The Rocket Performance pilot enforced this
literally -- 5688 leaf fields compared field-by-field between the old and
new interface, zero differences required, with a negative control proving
the comparison could actually detect a changed digit. That is the standard,
not a metaphor for "looks similar."

## States that must never collapse into each other

| State | Must never be shown as | Why |
| --- | --- | --- |
| Stale (input changed since last solve) | The current result | It is answering a question that has since changed. Dim it, label it "Stale -- recalculate," never delete or silently refresh it. |
| Superseded (upstream chamber changed) | The current result relabeled with the new chamber's numbers | The result was computed from a chamber that no longer exists; it is not wrong, it is about a different case. Label it "Superseded chamber," keep showing what it actually used. |
| Unavailable (no provider, no solve yet) | Zero, blank treated as zero, or omitted silently | Zero is a value. Unavailable is the absence of one. A reader must not be able to mistake "0" for "not computed." |
| Warning (provider succeeded with caveats) | Failure | A provider warning is not a failed solve -- it is a solve with something the user should read before trusting it fully. |
| Refused (model outside its validity envelope -- e.g. transitional Reynolds flow, a nozzle regime the ideal model rejects) | An estimate, a best guess, or the nearest valid case silently substituted | RocketForge's `engineering.line` explicitly withholds a friction factor in the transitional regime rather than interpolate one. A UI must preserve that refusal, never paper over it with a number that looks like an answer. |

## Quantities that are commonly mislabeled

Get the exact meaning right in every label, tooltip, and micro-copy -- these
are the specific errors that have actually occurred in this project's
history:

- **c\*** (characteristic velocity) is not exhaust velocity. It characterizes
  the chamber and throat only.
- **Isp** (specific impulse) is not burn duration. It is thrust per unit
  propellant weight flow rate.
- **Cf** (thrust coefficient) decomposes into a momentum term and a pressure
  term -- the pressure term is signed and legitimately negative
  (overexpanded nozzle) or near-zero (nearly ambient-matched exit). A
  negative pressure-thrust term is not an error state and must never be
  styled like one.
- **Density impulse** is a physical metric (propellant density x Isp,
  roughly), not automatically a "score" or a ranking criterion -- do not let
  a Trade Study surface imply it alone should drive a design decision unless
  the study's own objective says so.
- **Darcy friction factor** vs **Fanning friction factor** differ by a
  factor of 4 (`f_Darcy = 4 f_Fanning`). Never show a bare "friction factor"
  without stating which convention -- RocketForge's Line workspace states
  Darcy explicitly for this reason.
- **CEA's own performance numbers** are an oracle/reference, not a
  RocketForge result. Keep the visual and textual separation between "what
  RocketForge's ideal-rocket model computed" and "what the reference
  provider reports for the same case" absolute -- they use different models
  and a residual between them is a modelling difference, not an error in
  either.
- **Condensed-phase species** in a thermochemistry result carry their own
  accepted four-state semantics (see Phase 5D). Do not average a condensed
  species into "the gas" or otherwise flatten states that were deliberately
  kept distinct.

## The header-vs-drawing failure, generalized

A real defect from this project's history: a workspace's schematic header
was bound to the *live input field* rather than to the *result the drawing
actually shows*, so editing an expansion ratio without recalculating
produced a header reading "Ae/At 60" over a drawing still showing the
solved "Ae/At 40." Every scientific redesign must check this specific
failure shape: **any label near a solved visual must be sourced from the
result object, never from a live/pending input control**, or a reader will
believe the picture and the words in front of them are describing the same
thing when they are not. `rf-visual-qa`'s screenshot matrix includes a
fixture built exactly to catch this.

## Meaning must not be colour-only

Every state distinction in this section (stale, superseded, warning,
refused, the sign of a pressure term) must be legible with colour removed --
carried in words, a symbol, or a shape as well as a hue. This is both an
accessibility requirement (WCAG, owned mechanically by `qt-ui-design` and
`design-review`) and a scientific-honesty one: a colour-blind engineer must
be able to tell a stale result from a current one exactly as reliably as
anyone else.

## Simplification is not automatically corruption -- but prove it

"Make this simpler" is a legitimate request and most of the time the right
one. It becomes a scientific-UI defect only when the simplification removes
a *distinction the underlying state still makes*. Before collapsing two
displayed states into one, check whether the controller/service layer still
distinguishes them internally -- if it does, the UI has no license to stop
distinguishing them, no matter how rarely one of the two actually occurs.

## Ownership

**This skill owns:** the boundary between a scientific result and its
displayed representation -- state semantics, quantity meaning, and the
requirement that redesign proves parity rather than assumes it.

**This skill explicitly does not own:**
- Composition, chrome, hierarchy -- `rf-engineering-workbench`.
- What a schematic is allowed to draw -- `rf-propulsion-visual-grammar`
  (though the two must agree on any given screen).
- Verifying parity mechanically (running the comparison, building the
  fixture, checking a real screenshot) -- `rf-visual-qa`.
- The physics itself, which is frozen and never touched by UI work.
