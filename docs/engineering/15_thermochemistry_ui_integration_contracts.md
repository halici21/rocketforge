# 15 — Thermochemistry UI Integration Contracts

What the interface shows for chemistry, what it must never imply, and how it
behaves when the numbers cannot be computed.

**Status:** specification. No QML is written in Phase 5A.

---

## 1. The standing rules, still binding

Nothing here relaxes what the interface already obeys:

| Rule | Source |
| --- | --- |
| **No equations in QML** — layout math only | Phase 3 onward, enforced by review |
| **Never leave stale calculation state on screen** | standing project rule |
| A refused calculation shows **no** numbers, and says why | Phase 4G blocking checks 4.4, 5.4, 6.3, 7.3, 8.6 |
| Zero QML warnings | Phase 4G gate 9.5 |
| Both themes legible at 1366×768 and 1920×1080 | Phase 4G gates 9.1–9.4 |
| Markers never overlap the numbers beside them | Phase 4G gate 9.6, learned the hard way in Fanno |
| Unavailable performance shows an em dash, not a fabricated number | Phase 4G gate 9.8 |

Chemistry raises the stakes on the third and last of these, because a chemistry
result is harder for a user to sanity-check by eye than a Mach number.

---

## 2. Reusing what exists

The component library already carries what this needs. Phase 5B adds pages, not
a new visual language:

| Need | Existing component |
| --- | --- |
| Composition and station tables | `RFEngineeringTable` — with its measured marker gutter |
| Provider / mode status | `RFStatusChip` |
| Propellant and mode selection | `RFComboBox`, `RFSegmentedControl` |
| Chamber summary readouts | `RFReadoutStrip`, `RFResultValue` |
| Property-vs-pressure plots | `RFLineChart`, `RFPlotSurface` |
| "No provider installed" | `RFEmptyState` |
| Provenance detail | `RFTooltip`, `RFPanel` |

`RFEmptyState` matters more here than anywhere so far: with no chemistry library
installed — the current state of this machine — it is what the user sees
(§7).

---

## 3. Every result is labelled with its assumptions

A chamber temperature or an Isp means nothing without the assumptions behind it.
Four labels are **mandatory** wherever a chemistry-derived number appears,
including in any export:

| Label | Values | Why it cannot be omitted |
| --- | --- | --- |
| **Chemistry mode** | equilibrium / frozen / frozen-at-throat | the modes differ by percent-level amounts (`11` §5) |
| **Provider** | Cantera x.y / RocketCEA x.y / tabulated:… | providers legitimately disagree (`13` §4) |
| **Adiabatic** | on every flame temperature | a real chamber loses heat (`11` §3.4) |
| **Ideal** | on every Isp, c\*, Cf | no efficiency, no divergence, no two-phase loss (`13` §10) |

**"Ideal" is the label that prevents the most likely real-world harm.** An ideal
vacuum Isp read as a predicted one is optimistic by several per cent, and it is
exactly the number a user will copy into a spreadsheet. The interface states it
every time, not once in a help page.

### 3.1 Show both bounds

Where both are available, equilibrium and frozen are shown **together**, with
the gap between them presented as its own quantity (`11` §5.5). Neither is
styled as the primary answer and the other as a footnote.

The gap is the honest headline: a narrow gap means the chemistry assumption does
not matter for this design; a wide one means it does. That is more useful than
either number alone, and it is not a number a user can easily get elsewhere.

No interpolation between them is offered anywhere in the interface.

### 3.2 The single-γ discrepancy is displayed

`12` §6 requires the handshake to *measure* what the single-γ reduction costs.
The interface shows it: the `GammaStrategy` chosen, and the resulting difference
in exit conditions against the equilibrium expansion.

A disclaimer that a single γ is approximate is worth much less than a number
saying by how much, for this case.

---

## 4. Selection, invalidation and staleness

### 4.1 Changing anything chemical clears everything chemical

Changing the propellants, the O/F, the chamber pressure, the reactant
temperatures, the chemistry mode, the γ strategy or **the provider** invalidates
every displayed chemistry result immediately.

The provider case is the dangerous one and is called out separately: two
providers can produce numbers differing by a per cent or two — small enough to
look like a valid refresh, large enough to be a wrong answer. Results are
cleared on provider change, not recomputed in place.

This is the "never leave stale calculation state on screen" rule, and the Phase
4E lesson that pages must not display pre-Generate data applies unchanged.

### 4.2 Capabilities drive the controls

A mode a provider cannot do is **disabled with a stated reason**, never offered
and then failed (`10` §4). A pressure or O/F outside the provider's validated
range is flagged before the calculation runs, naming the range.

### 4.3 Long calculations

An equilibrium solve is far slower than any compressible relation, and a sweep
is slower still. The interface must not freeze, must not appear to have
finished before it has, and must not show a partially updated result set.

The precedent is Phase 4F's memoised nozzle criticals (0.216 ms → 0.014 ms):
measure first, cache the pure function on its exact inputs, and prove with a
test that no result leaks between cases.

---

## 5. Composition display

| Requirement | Reason |
| --- | --- |
| Sorted by mole fraction, descending | the significant species first |
| Trace species collapsed, with the collapsed count **and** the fraction they account for | truncation is declared, never silent (`09` §5.2) |
| Mole and mass fraction both available, each labelled | the basis ambiguity is real (`09` §4.3) |
| Condensed species **visually distinguished** | they change what the result means (`11` §7) |
| The species database and version shown | species keys are meaningless without it (`09` §5.1) |
| Frozen expansion shows the chamber composition, **not** an em dash | `composition is None` means "the chamber's", not "unknown" (`09` §8) |

That last row is a specific instruction to Phase 5B, because rendering `None` as
missing data is the natural thing to do and would be wrong here.

---

## 6. Propellant presentation

* **`density_hint` is labelled a nominal value at its reference condition**, or
  it is not shown at all. It is never presented as a computed property, and no
  calculation reads it (`09` §4.2).
* **Ill-defined propellants say so.** RP-1 is displayed with its specification
  and fit provenance, not as though it were a pure compound (`09` §4.5). Two
  different RP-1 fits are visibly different entries.
* **Blends show their components and the basis** the fractions are stated on.
* **Reactant temperature and phase are visible inputs**, defaulting to the
  reference condition and labelled as such — because they change the answer
  (`11` §3.3) and a user who does not know they exist cannot know that.

---

## 7. No provider installed

The default state today. It is a first-class screen, not an error.

**What the user sees:** a clear statement that no thermochemistry provider is
available, which packages would provide one, and what remains usable without
one.

**What the user does not see:** any number. No defaults, no placeholders shaped
like results, no values quietly drawn from a table they did not select
(`10` §7.2).

**What still works:** every compressible page, unchanged. The Analysis pages
have no chemistry dependency and must never acquire one — if installing a
chemistry library becomes a prerequisite for the Isentropic page, something has
been wired wrongly.

**Choosing the tabulated provider is a deliberate user action**, and once chosen
every result it produces is labelled interpolated, with its dataset and version
(`10` §5.3).

---

## 8. Refusals

Chemistry adds refusal cases; they behave like the ones the manual gate already
checks.

| Case | Display |
| --- | --- |
| Condensed phases present | refusal for the single-phase handshake, naming the fraction and why; the chemistry result itself is still shown (`11` §7.3) |
| Provider cannot report condensed fraction | refused as **unknown**, not assumed absent — and the wording says which |
| O/F, pressure or temperature outside the provider's range | refusal naming the range |
| Reactant phase change the layer cannot quantify | refusal naming the missing quantity (`09` §4.4) |
| Provider raises | the exception becomes a diagnostic; **no partial result is left on screen** |
| Monopropellant with an O/F entered | the O/F control is absent, not zeroed (`09` §6.5) |

Every one of these follows the same shape the compressible pages already use for
ν beyond ν_max and for a detached oblique shock: **say what was asked, say why
it cannot be answered, show nothing that looks like an answer.**

---

## 9. What a chemistry acceptance gate would check

Not run in Phase 5A. Listed so Phase 5B has the shape, in the style of the
56-item Phase 4G checklist:

* every displayed number carries mode, provider and ideal/adiabatic labelling;
* switching provider clears results rather than updating them in place;
* switching mode clears results;
* a condensed-phase case refuses the handshake and says why;
* a case outside the provider's range refuses and names the range;
* with no provider installed: the empty state appears, no numbers anywhere, and
  every compressible page still works;
* the tabulated provider is visibly labelled interpolated on every result;
* frozen expansion shows the chamber composition, not em dashes;
* trace-species collapse states the count and the fraction collapsed;
* equilibrium and frozen appear together with their gap;
* the single-γ discrepancy is displayed with its strategy;
* zero QML warnings, both themes, both window sizes.

The honesty items — the refusals, the labelling, the empty state, the
provider-switch invalidation — are the **blocking** ones, on the same reasoning
as the seven blocking checks in the Phase 4G manual gate: a stale or invented
value reaching a user is the one class of defect this project treats as
unshippable.
