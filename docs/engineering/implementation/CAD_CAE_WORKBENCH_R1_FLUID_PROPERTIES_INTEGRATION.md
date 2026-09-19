# CAD/CAE Workbench R1 — Fluid Properties integration (full redesign)

Fourth workspace through the audit → design → implement → gate cycle.
Explicit instruction for this phase: do not copy Thermochemistry's chamber
composition or Line's pipe schematic — the shell grammar is shared, the
workspace object is different. This workspace's object is not hardware at
all: it is a thermodynamic state.

## Before-state audit

Read before writing anything: `ui/pages/FluidPropertiesPage.qml`
(pre-redesign — a flat `State` input panel above a flat, unweighted
5-row `Repeater`, two status chips silently rendering as neutral dots
because `FluidOutcome.status_tone`'s `positive`/`caution`/`negative`/
`neutral` vocabulary doesn't match `RFStatusChip`'s recognized tones — the
same bug class Line had), `fluid_property_controller.py` (zero
stale-detection, like Line before its own fix), `fluid_property_service.py`
(the exact `PROPERTY_ORDER` — density, specific_enthalpy,
specific_heat_cp, dynamic_viscosity, thermal_conductivity — and the
`FluidOutcome`/`PropertyRow` shapes), `docs/engineering/
FLUID_PROPERTIES_API_V1.md` (the frozen v1.0 contract), `rocketforge/
physics/fluids/types.py` and `states.py` (`FluidPhase`'s five members
with deliberately no `UNKNOWN`; `PropertyStatus`'s seven members, each a
distinct reason a property may have no value), and `docs/engineering/
REACTANT_ENTHALPY_COUPLING_CONTRACT.md` (why this page's `specific_enthalpy`
is not interchangeable with NASA CEA's assigned reactant enthalpy).

Went one level further than the frozen domain docs, into the actual
provider adapter (`rocketforge/providers/fluid_properties/coolprop.py`),
to find which of `PropertyStatus`'s seven members this build's provider
can actually produce, rather than designing for all seven and guessing at
captures: **only `AVAILABLE`, `NOT_REQUESTED`, `TWO_PHASE_AMBIGUOUS` and
`PROVIDER_FAILED` are ever assigned by `CoolPropFluidProvider.evaluate()`.**
`NOT_SUPPORTED`, `OUT_OF_RANGE` and `PHASE_UNSUPPORTED` are real, valid
vocabulary members — declared for other providers or a future one — but
this adapter never assigns them. A live evaluation of every reachable
branch (below) confirmed this before any capture was attempted, instead of
fabricating a state to match an assumed-complete list.

## Engineering-object definition

Per the brief and confirmed live via `rf-engineering-workbench`: "object-first"
does not require a hardware drawing. A thermodynamic state can itself be
the central engineering object — fluid identity, phase, temperature,
pressure. `rf-propulsion-visual-grammar` was deliberately **not** invoked
to justify a schematic, because this workspace's final visual
representation contains no physical propulsion-domain drawing; forcing
that skill onto a non-pictorial state block would be routing to the wrong
owner.

## Design thesis and centerpiece decision

**`ui/pages/fluidproperties/FluidStateBlock.qml`** (new) — the object. Not
a `Canvas`: there is no geometry to draw for a state, so none is invented.
A plain `ColumnLayout` of styled text: fluid identity, phase, then `T`/`p`
as a compact two-column mono readout. Every field is sourced from the
solved `FluidOutcome` (`resultChanged`) — `fluidLabel`/`temperatureText`/
`pressureText` are pulled from `FluidProperties.provenanceRows` by label
(mirroring Line's `rowByLabel` helper), never from the live
`fluidName`/`temperature`/`pressure` input properties, so editing the form
without evaluating can never move this block.

**Phase is deliberately never colour-coded as validity.** `TWO_PHASE` is a
real, valid answer per `rocketforge/physics/fluids/types.py` ("`TWO_PHASE`
is a real answer and not an absence"), not a warning state — so the phase
line always renders in the same neutral secondary-text tone regardless of
which of the five `FluidPhase` members it is. `Theme.success`/`warning`/
`error` are reserved for the one place validity is actually being claimed:
the `RESULT` status chip (`Evaluated` / `Evaluated with warnings` /
`Refused`). Verified live with `rf-visual-qa`: the two-phase capture pairs
a warning-toned status chip with a neutral "TWO-PHASE" state line and
explicit "two phase ambiguous" text on every withheld row — the chip
carries "pay attention here," the state block states the (valid) fact,
and the per-row text carries the specific reason. No layer overloads
another layer's meaning.

**Hierarchy**, confirmed live via `rf-scientific-visualization` (no chart,
no `RFEngineeringTable` — a single-point evaluation has no sweep, and five
heterogeneous physical quantities of one state are not comparable
entities): a 3-tier plain-row hierarchy over the same `PROPERTY_ORDER` the
frozen service always published — `Primary` (density, specific enthalpy,
`Typography.readoutLarge`), `Thermodynamic` (cp, `readoutMedium`),
`Transport` (viscosity, conductivity, `readoutSmall`, grouped). Built as a
new reusable `ui/pages/fluidproperties/PropertyRow.qml` rather than
extending `RFResultValue` or duplicating the row markup three times:
`RFResultValue` has no slot for the per-row reason text every one of the
four reachable `PropertyStatus` values needs, and duplicating a
4-column row layout three times for one font-size difference was worse
than one small parametrized component.

**Enthalpy provenance caveat.** Added a persistent (not hover-only) row to
the Provenance panel — "Enthalpy datum: This provider's own reference
state, not NASA CEA's assigned reactant enthalpy..." — the same
always-visible treatment Line gives its Darcy/Fanning distinction, per
`rf-scientific-ui-contract`'s commonly-mislabeled-quantities discipline.
This page is the only place a reader ever sees this raw number; the
injection-prevention logic lives in the CEA coupling layer, but the
honesty obligation about what the number *is* belongs here.

## Pre-existing bug fixed while wiring the redesign

Both `RFStatusChip` tones on this page (`providerAvailable ? "positive" :
"neutral"` on the header; `FluidProperties.statusTone` bound raw to
`tone` on the result chip) used the service layer's own vocabulary
(`positive`/`caution`/`negative`/`neutral`) directly, which
`RFStatusChip` does not recognize (`success`/`warning`/`error`/`accent`/
`neutral`) — both silently rendered as neutral/muted dots regardless of
actual state, the identical bug Line had before its own fix. Fixed with
the same presentation-only `chipTone()` mapping function in QML, no
Python touched for this part.

## `resultStale` added to `FluidPropertyController`

The one Python change beyond the mapping bug: Fluid Properties had zero
stale-detection, unlike the three already-accepted workspaces. Added
`_stale`/`_mark_dirty()` mirroring `LineController`/
`ThermochemistryController` exactly — every input setter now calls
`_mark_dirty()`; `calculate()`/`clear()` clear it. This is necessary
presentation plumbing, not scope creep: item 15 of the brief requires the
same solved-snapshot contract every other accepted workspace already has,
and item 20 explicitly says not to avoid necessary Python changes merely
to preserve a "zero files touched" figure.

## Gates run

| Gate | Result |
| --- | --- |
| Science files touched | `fluid_property_controller.py` only, staleness only — `fluid_property_service.py`, `rocketforge/physics/fluids/`, `rocketforge/providers/fluid_properties/` all untouched |
| Solve-call parity | evaluate: **1**. Dock expand/collapse, page navigate-away-and-back, theme toggle, resize, stale-edit (`setTemperature` without recalculating): all **0** additional evaluations |
| Stale-vs-solved mismatch fixture (rf-visual-qa's required check) | **PASS** — evaluated at T=90.17 K (liquid), edited T to 150 K without recalculating: input field correctly shows 150.000, `FluidStateBlock` and every property row still correctly show the OLD T=90.17 K solve (density 1,141.7, enthalpy −133,292, phase LIQUID), "Stale — recalculate" chip visible |
| States captured and manually inspected | nominal liquid (OXYGEN, default), a materially different valid state (true GAS phase, OXYGEN 100 K/50000 Pa — all five properties available with materially different values), two-phase ambiguity (OXYGEN at its own saturation pressure — all five properties simultaneously withheld with "two phase ambiguous" reason text, `kind=warning`), a hard refusal outside CoolProp's own declared EOS range (OXYGEN 40 K, below its `Tmin=54.36 K`), the stale fixture, a METHANE state exercised through the actual combo-box/controller path (not just the service layer) to confirm fluid-switching renders correctly, dark 2560×1440/1920×1080/1366×768, light 1920×1080/1366×768 |
| Categories confirmed unreachable and not fabricated | `NOT_SUPPORTED`/`OUT_OF_RANGE`/`PHASE_UNSUPPORTED` (this adapter never assigns them — see audit above); `PROVIDER_FAILED` (searched near `Tmax`, near `Tmin`, and near the critical point for a viscosity/conductivity correlation failure; none found for these three well-supported fluids in this build — documented honestly rather than chased further); `FLUID_PHASE_MISMATCH` (this workspace's service never passes `required_phase`, unlike Line's liquid-only request, so this refusal path is structurally unreachable here) |
| Memory (session soak, 100 rounds, whole-app sweep, `QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:/Windows/Fonts`) | 171.92 MB private, second half (38.48) << first half (133.44) — decelerating, PASS; page instances +0, canonical result unchanged, **0 Qt warnings** |
| Full regression | base 6931 passed/154 skipped, production 7086 passed/2 skipped — unchanged from historical baseline |
| Lint (`qt_qml_lint.py`) | clean against genuinely new code; remaining findings (`var`, loose equality, font dot-notation, `ORD-1` ordering, `required property var`) all match this codebase's own established convention, cross-checked against `LinePage.qml`/`LineSchematic.qml` |
| `rf-engineering-workbench` (live) | confirmed the object-first grammar applies to a non-pictorial state block; confirmed a 3-tier weighted plain hierarchy (not RFResultValue cards) stays inside the "never more than four active levels" rule and reads as grouping, not a KPI-card grid |
| `rf-scientific-ui-contract` (live) | confirmed the per-property-status visual treatment (uniform dim + full reason text, not seven separate tones) and the enthalpy-caveat placement (persistent Provenance row, not hover-only) |
| `rf-scientific-visualization` (live) | confirmed no chart/table earns its place at this row count, no sweep exists |
| `rf-qml-architecture` (live) | cross-workspace audit of the `QVariantList`-vs-`RowListModel` carry-forward — see below |
| `rf-visual-qa` (live) | confirmed the phase-neutral-colour design decision holds against the failure-mode checklist; flagged the canonical table's "phase refusal" entry needed reinterpreting against what this adapter can actually produce (see audit) |
| `qt-qml-review` (lint + hand-applied checklist) | no new findings beyond lint; delegate/binding/layout patterns all match established precedent |

### The `QVariantList`-vs-`RowListModel` cross-workspace audit (carried forward from Line, not fixed)

Per the explicit instruction not to "fix Line only": audited whether
Fluid Properties shares Line's publication pattern before touching
anything. It does — `resultRows`/`provenanceRows`/`diagnosticRows` are
all plain re-read `@Property("QVariantList")`, identical to Line's and
Thermochemistry's own already-accepted pattern, with no `RowListModel`
import anywhere in `fluid_property_controller.py`. That makes **three**
of the four full-redesign workspaces (Thermochemistry, Line, Fluid
Properties — all 5–20 row, single-solve-event result surfaces) on the
plain pattern, against **one** (Rocket Performance, ~11 named row-groups,
a materially larger and more frequently-republished multi-panel surface)
on `RowListModel`. Consulted live with `rf-qml-architecture`: this reads
as the small-workspace pattern sitting genuinely within the "bounded,
decelerating" envelope this project's own soak harness treats as safe at
this row count and update frequency — not a theoretical exemption, each
workspace's own soak evidence is the actual proof (Fluid Properties:
171.92 MB decelerating this phase; Line: 171.31 MB; Thermochemistry:
172.44 MB at its own acceptance) — rather than undiscovered risk quietly
accumulating. It is still real, documented technical debt against Rule
1's stated "never," not a discovered non-issue. **Not migrated this
phase**, per the explicit instruction: a correction here is a
cross-workspace change (Thermochemistry + Line + Fluid Properties
together) needing its own regression gate, not a decision to make inside
a single-workspace redesign. Recorded here and in the checkpoint for
whoever picks up that gate.

## Carried-forward non-blocking items (unchanged by this phase)

- Thermochemistry's native-vs-corrected assigned-enthalpy capture gap.
- The previously-documented mixed-session memory tail (~0.78 MB/round,
  brief-unrelated).
- The `QVariantList`-vs-`RowListModel` cross-workspace investigation above.

## Not done / explicitly out of scope this phase

- Migrating any workspace's result-row publication to `RowListModel`.
- Any change to `fluid_property_service.py`'s evaluation logic, the
  `CoolPropFluidProvider` adapter, or the `PropertyStatus`/`FluidPhase`
  vocabulary — all frozen and untouched.
- Chasing a `PROVIDER_FAILED` capture further than the three edge
  conditions tried (none reachable for these three fluids in this build).
