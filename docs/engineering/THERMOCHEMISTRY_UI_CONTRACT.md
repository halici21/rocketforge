# Thermochemistry UI Contract

What the Thermochemistry workspace shows, what it must never imply, and how it
behaves when the numbers cannot be computed.

**Status:** production, Phase 5D. Implements the specification in
`15_thermochemistry_ui_integration_contracts.md` for the chamber state; the
expansion half of that document remains unimplemented because there is no
expansion yet.

---

## 1. What this workspace answers

> At this operating point, what ideal HP-equilibrium chamber state does the
> selected thermochemistry provider predict?

It does **not** answer "how good is this engine". There is no characteristic
velocity, no thrust coefficient, no specific impulse and no thrust anywhere in
it, because RocketForge owns none of those yet (ADR-15). NASA CEA returns them
natively; that is a reason to keep them reachable as provider oracle values for
Phase 5E, not a reason to display them as RocketForge's answer.

---

## 2. The chain, and the direction of every arrow

```
    QML                                   asks, and renders
     |
     v
    ThermochemistryController             validates, orchestrates, formats
     |
     v
    thermochemistry_provider (gateway)    the one door to a provider
     |
     v
    CEAThermochemistryProvider            solves
     |
     v
    ChamberGas + diagnostics + provenance the answer
```

No step is skipped and no arrow points back. QML holds no provider, no domain
object and no equation; the application layer holds no chemistry; the provider
holds no Qt.

**One shared result.** Calculator, Composition and the provenance panel read the
same immutable `ChamberOutcome`. Switching view never re-solves and two views
can never show states from different calculations.

---

## 3. Every result is labelled with its assumptions

Four labels accompany every chamber result, in the page header, the result
header and the provenance summary:

| Label | Value | Why it cannot be omitted |
| --- | --- | --- |
| Provider | NASA CEA 3.3.4 | providers legitimately disagree |
| Chemistry mode | Equilibrium | the modes differ by percent-level amounts |
| Constraint | HP — constant enthalpy and pressure | a UV calculation would give a noticeably higher temperature |
| Heat loss | Adiabatic | a real chamber loses heat |

The chamber temperature carries `Adiabatic · HP equilibrium` on its own line,
never the bare phrase "flame temperature". Its help text says what it is not:
*not a wall temperature and not a finite-rate combustion prediction.*

---

## 4. Which gamma, which cp

Phase 5C's state carries **two** gammas and **two** heat capacities. The
interface names which is which, everywhere, because one displayed under the
other's label is a silent error.

| Displayed as | State field | Qualifier shown |
| --- | --- | --- |
| Isentropic exponent γ_s | `gamma` (= `gamma_equilibrium`) | equilibrium |
| Frozen specific-heat ratio γ_fr | `gamma_frozen` | c_p,fr / c_v,fr |
| Specific heat c_p | `cp` | frozen |
| Specific heat c_v | `cv` | frozen |
| Equilibrium specific heat c_p,eq | `cp_equilibrium` | does not satisfy c_p − c_v = R |

The frozen pair is the one that satisfies `cp − cv = R`; the equilibrium heat
capacity does not, and is not meant to. The sweep charts the **same** `gamma`
field under the **same** qualifier, so the two views cannot disagree.

Measured on the canonical case: γ_s = 1.13259 against γ_fr = 1.19557 — 5.6 %
apart. One field could not carry both.

---

## 5. Units and precision

Every dimensional value shows its unit. Molar mass is displayed in **kg/mol**,
the canonical SI unit, in the readout, the sweep table and the sweep chart —
one unit everywhere rather than a per-view choice.

Chamber pressure has a **display unit** (Pa / bar / MPa). It is the only unit
selector in the workspace, the conversion lives in the application layer, and
the case, the request and every stored result stay in pascals. Changing it
re-renders and does **not** mark the result stale.

Rounding happens on the way to the screen and never replaces a stored value.
A quantity a result genuinely does not carry is an em dash, never a zero.

---

## 6. Assigned-enthalpy reactants — the blocking caveat

Several of NASA CEA's reactant entries, the cryogenic liquids among them, carry
a single **assigned enthalpy** at one reference condition instead of a
temperature-dependent fit. CEA accepts a different temperature and then ignores
it.

The stream-temperature input is **never disabled** for those reactants, and the
requested temperature is never displayed as though it had been used. When the
provider reports `PROVIDER_ASSIGNED_ENTHALPY_REACTANT` the workspace shows,
beside the result:

* the affected reactant, by the provider's own name for it;
* the temperature that was **requested**;
* the temperature the model actually **used**;
* one sentence saying the requested value did not enter the calculation, and
  one saying the result is still usable.

The result stays on screen and the status stays `Solved with warnings`. This is
a caveat on a valid answer, not a refusal, and it is styled as one.

**This reports an upstream limitation; it does not remove it.** RocketForge
cannot make CEA use a temperature its reactant data does not carry. Closing the
gap needs a **reactant enthalpy / fluid-property coupling** — a stream's
`(T, p, phase)` resolved to an actual `h(T, p, phase)` by a property model, and
that enthalpy handed to the provider instead of a reactant name. That is a
future phase, listed in §16, and nothing in this workspace pretends it is done.

---

## 7. Composition

| Requirement | How |
| --- | --- |
| Sorted descending on the displayed basis | the significant species first |
| Mole and mass fraction both present, each labelled | both are carried on every row, so switching basis recalculates nothing |
| Condensed species visually distinguished | the phase column says `solid`/`liquid`, and the row is annotated in the gutter, the same way the compressible tables annotate the sonic line |
| Trace species collapsible | a **display threshold**, applied to the view |
| Truncation declared | the hidden count and the fraction they account for are stated |
| Σ shown over every species | not over the visible ones |

**The display threshold is a display threshold.** It hides rows. The underlying
result keeps every species the provider returned, and lowering the threshold
brings a row back with its original value unchanged — proved by a test that
hides a trace species and recovers it exactly.

The labels read `≥ 1e-6`, not `> 1e-6`, because a row at exactly the threshold
is kept.

---

## 8. Condensed products

Presence is read from the **returned composition**, never from a count of
candidate condensed species. Phase 5C established that the canonical production
case carries solid carbon among its candidates while the amount present is
6.24e-08; announcing condensed material there would be false.

**Four states, not two.** The two "not present" ones are genuinely different
and are never merged:

| State | Condition | Headline |
| --- | --- | --- |
| `unknown` | the provider reported no fraction | `Condensed fraction not reported` — *unknown is not the same as none* |
| `none_reported` | fraction is exactly 0 | `No condensed product reported` |
| `below_threshold` | `0 < fraction <` the reporting threshold | `No condensed phase above reporting threshold` |
| `present` | `fraction >=` the reporting threshold | `Condensed products present` |

The middle two used to be one, reported as *"None detected"*. A measured
6.24e-08 is not zero, and claiming the mixture contains no condensed material
is a stronger statement than that number supports. The state between them says
what it is.

**In every known state the interface shows both numbers the verdict is about:**
the exact condensed mass fraction and the reporting threshold it was judged
against. A sentence about a measurement is never the only thing on screen.

A condensed species below the threshold still appears in the composition table
under the normal display-threshold policy, and the summary names it — as
*"in the composition, below it"*, never as present.

### The reporting threshold is not a physical cutoff

`CONDENSED_REPORTING_THRESHOLD = 1e-6` decides **one thing**: which sentence
the interface says. It changes no composition, deletes no species, alters no
`ChamberGas` field, touches no element balance, never reaches the provider and
plays no part in any future nozzle or performance handshake. It is named
`reporting threshold` for that reason, and a test asserts the constant and the
phrase appear nowhere in `physics`, `providers`, `core` or `engineering`.

The value is chosen from measurement: the canonical Phase 5C case sits at
6.24e-08 with condensed candidates in the product set, and the genuine
solid-carbon case at O/F 0.5 is four orders of magnitude above it.

---

## 9. Diagnostics and refusals

Seven outcomes, never collapsed into "calculation failed":

| Outcome | Meaning |
| --- | --- |
| `empty` | nothing calculated yet — an intentional empty state, no zeros |
| `ok` | solved |
| `warning` | solved, with a scientific caveat |
| `no_solution` | the provider did not converge, **or** it converged and RocketForge rejected the result |
| `unavailable` | no provider installed |
| `invalid_input` | the domain refused the request |
| `provider_error` | outside the provider's validated range, or unmappable |

A refusal shows **no numbers** and says what was asked, why it cannot be
answered, and which field it concerns. A provider range refusal names the
range.

"Converged but rejected" keeps its own wording — *"The provider converged, but
RocketForge rejected the result: …"* — because it is a scientifically different
event from non-convergence.

Diagnostics are keyed by their stable code, never by matching English. A code
this build does not recognise is shown with a neutral title and its own name
attached rather than being dropped. Severity is carried through unchanged.

---

## 10. Provenance

Read from the **result's own** provenance record, never from what happens to be
installed now. A result keeps the identity of the provider that made it.

Summary, always visible: provider and version, model, database and short SHA.
Expanded: provider id, adapter version, library version, chemistry mode,
equilibrium constraint, heat-loss assumption, full database SHA-256, the
product species set, and the provider's own name for each reactant.

None of it is editable. A database hash is a fact about a result, not a setting.

---

## 11. The O/F sweep

An analysis visualisation. **Not an optimiser.**

* Runs on an explicit press, never on a keystroke.
* One scalar solve per point, in order, in this process. No batch API, no
  threads — Phase 5B-0 measured four threads at ~0.85× of serial for CEA.
* Points are ascending in O/F, endpoints exact.
* A range that cannot mean anything is refused with the reason named, and
  reversed endpoints are **not** silently reordered.
* The point guard is 1000, derived from Phase 5C's measured 0.568 ms per point.
* Every fixed condition stays on screen, taken from the sweep's own case.

**Failed points.** A point that did not solve keeps its row, its place and its
message. Its numbers are em dashes. The chart line **breaks** across it and a
dashed guide marks the mixture ratio, because a straight segment joining the
neighbours would draw physics nobody solved.

**No smoothing.** Consecutive points are joined by straight segments and the
sampled points are drawn, so a discrete sweep never reads as a continuous
function.

**No optimum.** A peak is labelled `Maximum <quantity> in sweep`, and nothing
is called optimal, best or recommended. Measured on LOX/CH₄ over O/F 2.5–4.5:
the chamber temperature peaks at 3.75 while the isentropic exponent peaks at
2.5. There is no single peak to recommend, and choosing between them is a
decision layer this phase does not build.

**Repeated warnings are aggregated** into one row naming the diagnostic, how
many points carried it and over what range. The per-point diagnostics are
untouched and reachable through point inspection.

---

## 12. Reference comparison

    published value  --compare-->  RocketForge + provider value

never a lookup. Nothing in RocketForge reads a published number to produce a
result, and none of them is editable.

The tolerance is the **source's own rounding box**, computed from the
significant figures the dataset records, before the comparison runs. Widening
it means editing the declared precision of the published value, which is a
visible change to the shipped dataset.

The reference case runs its **stored** conditions. The Calculator form is not
consulted.

**The source publishes c\*, Isp and an exit gamma. This workspace loads no
value for any of them.** The dataset records their names and the reason they
are not compared; a quantity whose value is never read cannot leak into a
display.

---

## 13. No provider installed

A first-class screen, not an error. The base RocketForge environment ships
without a chemistry library and that is supported.

**What the user sees:** the provider's status, what it reported, and what would
enable it — naming the dependency profile, and noting that the packaged
application already ships one.

**What the user does not see:** any number. The status bar says
`No thermochemistry provider installed · No values are shown`.

**What still works:** every compressible workspace, unchanged. Those pages have
no chemistry dependency and must never acquire one.

---

## 14. Staleness and traceability

Every result view can recover the conditions that produced it — reactants,
their actual stream temperatures, O/F, chamber pressure, provider and model —
from the result's own snapshot, never from the input form.

Editing an input after solving marks the result **stale**: the header keeps
saying what the result is for, a chip says the inputs have changed, and one
sentence explains the difference. The labels are never updated from unsolved
input fields.

Changing anything that defines the sweep marks the sweep stale in the same way.
Re-checking the provider clears the result and the sweep outright, because two
providers can differ by a per cent — small enough to look like a refresh, large
enough to be a wrong answer.

---

## 15. Deferred, and recorded rather than forgotten

### Reactant enthalpy / fluid-property coupling

**Status:** deferred, non-blocking. Reported correctly today.

CEA models several reactants — `O2(L)`, `CH4(L)`, `H2(L)`, `RP-1` — with a
single assigned enthalpy at one reference condition, and ignores any other
temperature. A subcooled or pressurised liquid therefore cannot be expressed
through a reactant name alone.

A future phase may investigate coupling an explicit reactant property model:

```
PropellantStream(T, p, phase)
        |
        v
fluid / reactant property model
        |
        v
actual h(T, p, phase)
        |
        v
thermochemistry provider
```

None of that architecture exists. Phase 5D's contribution is that the
limitation is **visible** rather than silent: the requested temperature, the
temperature the model used, and the reactant it applies to are all on screen.

---

## 16. Deliberately not implemented

RocketForge c\*, Cf, Isp, thrust, effective exhaust velocity, combustion
efficiency, density impulse, optimum O/F, Pareto fronts, objectives,
constraints, scoring, a generic trade-study engine, chamber geometry, L\*,
injector sizing, cooling, nozzle performance, engine cycles, finite-rate
chemistry, a Cantera provider selector, CoolProp, transport-property display.

Rocket performance is Phase 5E. The generic decision layer is Phase 5F.
