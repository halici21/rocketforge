# 07 — UI Integration Contracts

Which backend service feeds which existing page, what each page's inputs and
outputs are, and — critically — **which of those the frozen QML can already
render without modification.**

**No QML is modified by this phase, and none should be modified by Phase 4 until
a page genuinely cannot express a result.** Everything in §9 is a *recorded
future requirement*, not a change request.

---

## 1. Module → page mapping

The twelve navigation entries in `ui/data/Navigation.qml`, verified by
inspection:

| `key` | Page file | State today | Backend service | Phase 4? |
| --- | --- | --- | --- | --- |
| `isentropic` | `IsentropicPage.qml` | **built** | `physics.compressible.isentropic` | **yes — first** |
| `massflow` | `MassFlowPage.qml` | placeholder | `physics.compressible.mass_flow` | yes |
| `normalshock` | `NormalShockPage.qml` | placeholder | `physics.compressible.normal_shock` | yes |
| `obliqueshock` | `ObliqueShockPage.qml` | placeholder | `physics.compressible.oblique_shock` | yes |
| `prandtlmeyer` | `PrandtlMeyerPage.qml` | placeholder | `physics.compressible.prandtl_meyer` | yes |
| `fanno` | `FannoPage.qml` | placeholder | `physics.compressible.fanno` | yes |
| `rayleigh` | `RayleighPage.qml` | placeholder | `physics.compressible.rayleigh` | yes |
| `nozzlelab` | `NozzleLabPage.qml` | **built** | `physics.compressible.nozzle` | yes — last |
| `compare` | `ComparePage.qml` | placeholder | `Case` / `SweepResult` (`02` §6) | after the modules |
| `charts` | `ChartsPage.qml` | placeholder | sweep APIs across all modules | after the modules |
| `equations` | `EquationLibraryPage.qml` | **built** (10 mock entries) | the equation registry (`02` §9) | yes — cheap and high value |
| `gases` | `GasPropertiesPage.qml` | placeholder | `PerfectGas` + a gas library | yes |

The two built analysis pages bracket the work: Isentropic proves the whole chain
(service → controller → view model → existing widgets) on the simplest module,
and Nozzle Lab is the integration test of everything.

---

## 2. The general page contract

Every analysis controller exposes the same shape, so twelve pages need one
pattern rather than twelve:

```python
class AnalysisController(QObject):
    # inputs (QML writes these)
    #   ... page-specific properties ...

    # outputs (QML reads these)
    readouts   : list[dict]   # [{label, value, unit, tone}]  -> RFReadoutStrip
    series     : list[dict]   # [{name, values}] or {x, y}    -> plot surfaces
    status     : dict         # {label, tone}                 -> RFStatusChip
    problems   : list[dict]   # [{severity, message}]         -> inline notes
    equation   : str          # HTML                          -> RFEquationBlock
    assumptions: list[str]                                    -> assumption list
    interpretation: str                                       -> interpretation panel
    busy       : bool
    @Slot() def solve(self): ...
```

`readouts`, `assumptions`, `equation` and `interpretation` deliberately match the
shapes `MockData.qml` already provides (`flowState`, `isentropicAssumptions`,
`isentropicEquation`, `isentropicInterpretation`), so binding a page to a
controller is a change of *source*, not of structure.

**Formatting is the controller's job, not QML's** (`01` §6):

| Case | Rendered as |
| --- | --- |
| a number | fixed decimals per quantity, e.g. Mach 3 dp, ratios 4 dp, angles 2 dp |
| very small / very large | scientific with 4 significant figures, e.g. `1.890e-3` |
| not computed (no solver input) | **em dash** `—`, matching the existing convention |
| not applicable to this state (e.g. ν at M < 1) | em dash, with a tooltip reason |
| failed | em dash, and the reason appears in `problems` |

---

## 3. Input validation split

| Layer | Responsibility |
| --- | --- |
| QML | numeric fields, step, min/max where the existing `RFNumberField` supports it |
| Controller | domain pre-check before calling the service; sets `problems` and refuses to call rather than catching an exception in the UI |
| Service | full validation regardless (`04` §8) — because notebooks and scripts call it too |

The controller pre-check exists so the common case never raises: a user typing
`M = -1` sees an inline message, not a stack trace, and the service's exception
remains the safety net rather than the user experience.

---

## 4. Isentropic page contract (task §108)

The one page whose layout already exists, so the contract is written against
what is actually on screen.

**Inputs — already present in `IsentropicPage.qml`:**

| Control | Existing binding | Backend meaning |
| --- | --- | --- |
| `RFSegmentedControl` "Given" | `MockData.givenOptions` = `["Mach", "p/p₀", "T/T₀", "A/A*"]` | which inverse to run |
| `RFNumberField` (given value) | `MockData.givenFields[i]` | the value |
| `RFNumberField` "Specific heat ratio γ" | `MockData.gammaInput` | `PerfectGas.gamma` |
| `RFComboBox` "Gas" | `MockData.gases` | selects γ and R from a gas library |
| `RFComboBox` "Gas model" | `MockData.gasModels` | v1: only "Calorically perfect" is enabled |
| `RFButton` "Solve" | currently `enabled: false` | becomes enabled |

**Inputs not yet present** (needed, and the reason each is deferred to §9):

* a **branch selector** for the `A/A*` given mode — mandatory, since the API
  refuses to guess (`03` §3.4);
* optional dimensional inputs p₀, T₀, R, A.

**Outputs — into the existing `RFReadoutStrip`,** whose model shape is
`{label, value, unit}` and which currently shows exactly the right seven rows:

| Row | Source | Notes |
| --- | --- | --- |
| Mach | solved or given | 3 dp |
| p/p₀ | `isentropic.pressure_ratio` | 4 dp, or scientific below 1e-3 |
| T/T₀ | `isentropic.temperature_ratio` | 4 dp |
| ρ/ρ₀ | `isentropic.density_ratio` | 4 dp |
| A/A* | `isentropic.area_ratio` | 3 dp; em dash at M = 0 |
| μ | `isentropic.mach_angle`, converted to degrees | em dash for M < 1 |
| ν | `prandtl_meyer.nu`, converted to degrees | em dash for M < 1 |

The existing mock rows are already exactly these seven, in this order, with these
units — so this readout needs **no QML change at all**.

**Plot:** the existing `MockScientificPlot` consumes
`MockData.isentropicSeries` as `[{name, values}]` sampled at a fixed
`curveMachStep` from M = 0. The controller can produce the identical structure
from `sweep_isentropic`, so the chart also needs no QML change. Default series:
p/p₀, T/T₀, ρ/ρ₀ over M ∈ [0, 4]; the operating point marker uses the existing
`markerMach`/`markerSeriesIndex` properties.

**Reference panels:** `equation`, `assumptions` and `interpretation` come from the
equation registry record for the relation currently being solved, replacing the
three hand-written `MockData` strings.

**Diagnostics:** `NEAR_SONIC` and `EXTRAPOLATED_GAMMA` map to `problems`.

---

## 5. Contracts for the placeholder pages

Each placeholder already declares its intent through
`ModulePlaceholderPage.planned`. Those declared bullets are treated as the
requirement, so the built page matches what the frozen skeleton promises.

### 5.1 Mass Flow — declared: Stagnation state, Throat area, Discharge coefficient, Flow chart

| | |
| --- | --- |
| Inputs | γ, R (or gas), M **or** p/p₀; optional p₀, T₀, A |
| Outputs | MFP, ṁ (if dimensional), mass flux ρV, p\*/p₀, Γ(γ), choked yes/no, ṁ_max |
| Plot | normalised ṁ vs M, **with the maximum at M = 1 explicitly marked** (task §36) |
| Status chip | "Choked" / "Unchoked" — `tone: "accent"` / `"neutral"` |
| Note | the declared "Discharge coefficient" is a **device** correction (`03` §4.3). It is shown on this page as an optional multiplier with a label stating it is empirical and not part of the ideal relation — or deferred to the injector workspace. Recommended: defer, and remove nothing from the UI |

### 5.2 Normal Shock — declared: Upstream Mach, Static and stagnation jumps, Shock chart, Total-pressure loss

| | |
| --- | --- |
| Inputs | M₁, γ; optional upstream p₁, T₁ |
| Outputs | M₂, p₂/p₁, T₂/T₁, ρ₂/ρ₁, p₀₂/p₀₁, Δs/R, A₂\*/A₁\*; downstream dimensional state when given |
| Plot | M₂, p₂/p₁, T₂/T₁, ρ₂/ρ₁, p₀₂/p₀₁ vs M₁ over [1, 5], one family per γ |
| Interpretation | the standing text of `03` §5.3 — from the registry, not hand-written |
| Errors | M₁ < 1 → inline message "A normal shock requires supersonic upstream flow", no computation |

### 5.3 Oblique Shock — declared: Deflection angle, Weak and strong branch, Theta-beta-M chart, Detachment limit

| | |
| --- | --- |
| Inputs | M₁, θ (degrees), γ, **branch** (`RFSegmentedControl`: Weak / Strong) |
| Outputs | β, M_n1, M_n2, M₂, p₂/p₁, T₂/T₁, ρ₂/ρ₁, p₀₂/p₀₁, θ_max, downstream flow angle, "downstream supersonic" yes/no |
| Plot | θ-β-M curves for several M₁, with θ_max markers and the β_sonic locus |
| Status chip | "Attached (weak)" / "Attached (strong)" / **"Detached"** with `tone: "warning"` |
| Detached | `NO_SOLUTION` renders every output as an em dash plus one clear message: "No attached shock: θ = 40.0° exceeds θ_max = 22.97° at M₁ = 2.0." **The page must not show a number** |
| Angles | degrees on screen, radians in the service — converted in the controller only (`01` §8) |

### 5.4 Prandtl–Meyer — declared: Turn angle, Expansion fan, Mach wave envelope, Downstream state

| | |
| --- | --- |
| Inputs | M₁, turn angle Δθ (degrees), γ |
| Outputs | ν₁, ν₂, M₂, p₂/p₁, T₂/T₁, ρ₂/ρ₁, μ₁, μ₂, fan angle, ν_max for this γ |
| Visualisation | the fan drawn from μ₁, μ₂ and Δθ — pure geometry from the result, no physics in QML |
| Errors | M₁ < 1 → inline message; ν₁ + Δθ ≥ ν_max → "Turn exceeds the maximum expansion (130.45° at γ = 1.4)" |

### 5.5 Fanno — declared: Friction factor, Duct length, Choking length, Fanno line

| | |
| --- | --- |
| Inputs | M₁, γ, **friction factor with its convention named**, L/D or 4fL/D, branch |
| Outputs | T/T\*, p/p\*, ρ/ρ\*, p₀/p₀\*, 4fL\*/D, M₂, remaining length to choking, choked yes/no |
| Plot | the five ratios vs M, **subsonic and supersonic as separate series** (`03` §8.7) |
| Status chip | "Choked" `tone: "warning"` when the duct reaches L\* |
| **Label rule** | the friction input **must** read "Fanning friction factor f" (or "Darcy f_D" if the user switches convention). A bare "f" is forbidden (task §112, `03` §8.2). The derived parameter is labelled "4fL/D (Fanning)" |
| Over-length duct | `FRICTION_CHOKED` → outputs are em dashes plus "The duct is longer than the choking length (4fL\*/D = 5.299 at M₁ = 0.3); the flow chokes and the inlet condition must change" |

### 5.6 Rayleigh — declared: Heat addition, Thermal choking, Rayleigh line, Stagnation temperature ratio

Task §113 warns against overloading this page. **Recommended primary workflow —
one question, well answered:**

> *Given an inlet Mach number and an amount of heat addition (as T₀₂/T₀₁ or as q),
> what is the exit state, and how close is the flow to thermal choking?*

| | |
| --- | --- |
| Inputs | M₁, γ, T₀₂/T₀₁ **or** q with cp (mode switch), branch implied by M₁ |
| Outputs | M₂, T/T\*, p/p\*, T₀/T₀\*, p₀/p₀\* at both stations; p₂/p₁; p₀₂/p₀₁; margin to choking as (1 − T₀₂/T₀\*) |
| Plot | the Rayleigh line, T₀/T₀\* and T/T\* vs M, with **the T/T\* maximum at M = 1/√γ marked** (`03` §9.2) — the single most instructive feature of the page |
| Status chip | "Thermally choked" `tone: "warning"` |
| Interpretation | must state the counter-intuitive result explicitly: between M = 1/√γ and M = 1, static temperature *falls* while heat is added |
| Not on this page | the T/T\* inverse (non-monotone, `03` §9.5) and the p/p\* inverse — both marked FUTURE |

### 5.7 Gas Properties — declared: Gas library, Model selection, Constants table, Source and validity

| | |
| --- | --- |
| Inputs | gas selection |
| Outputs | γ, R, M̄, cp, cv, and the validity note for each |
| Source | a small in-tree gas library (air, N₂, He, CO₂, and a representative combustion-products entry), each entry carrying its own provenance record |
| Rule | the combustion-products entry must be labelled as a **representative constant-γ approximation**, not a computed chemistry result, until a thermochemistry provider exists |

### 5.8 Equation Library

Already built against ten hand-written entries with `{group, name, body}` where
`body` is HTML. The registry's `EquationRecord` (`02` §9) provides
`group`, `name` and `html` with exactly that meaning, so this page can be
switched to the real registry with **no QML change** — the cheapest genuine win
in Phase 4, and it makes every relation self-documenting from day one.

### 5.9 Compare and Charts

Both consume `SweepResult` (`02` §6) directly: Compare aligns readouts across
`Case`s and shows difference columns; Charts is a catalogue of standing sweeps
with a γ family selector. Neither needs new physics — only the sweep APIs — and
both are scheduled after the individual modules are accepted.

---

## 6. Nozzle Lab contract (task §114)

The most integrated page, and the one whose existing structure most constrains
the contract. Verified against `NozzleLabPage.qml` and `MockData.qml`.

**Inputs already on the page:** p₀ (MPa), T₀ (K), γ, Aₑ/A\*, and a back-pressure
`RFSlider` from 0 to 1 in units of p₀.

That set is *exactly* the input list the dimensionless solver needs — the page
was built to the right shape before the physics existed.

**Outputs into the existing `RFReadoutStrip` ("Stations"),** whose current mock
rows are Chamber M, Throat M, Exit M, Aₑ/A\*, pₑ/p₀, Tₑ/T₀ — again already the
right rows.

**The regime scale.** `RFBandScale` consumes `MockData.nozzleRegimes`, each band
being `{key, label, short, tone, from, to, shockX, sonic, plume, note, trace}`
where `from`/`to` are positions on the back-pressure axis. The backend maps onto
this **without any QML change**:

| Band field | Backend source |
| --- | --- |
| `from`, `to` | computed from `CriticalPressureRatios` — the band edges become the real first/second/third criticals instead of authored numbers |
| `key`, `label`, `short` | the `NozzleRegime` enum |
| `tone` | `success` for ideal, `warning` for internal shock, `neutral` otherwise — the existing convention |
| `shockX` | the solved shock position as an axial fraction, or `-1` when there is no shock (the existing sentinel) |
| `sonic` | `NozzleSolution.choked` |
| `note` | the regime's interpretation text from the registry |
| `trace` | the solved p(x)/p₀ profile, resampled to the drawing's point list |

One consequence worth stating: with real criticals the bands are **not** evenly
spaced the way the authored ones are. For γ = 1.4 and Aₑ/A\* = 2, the internal
shock band spans p_b/p₀ ∈ (0.513, 0.937) — 42% of the axis — while ideal
expansion is a single point at 0.094. The existing scale renders arbitrary band
widths already, so this is a data change, not a UI change; but the *ideal* band
being a point rather than a range is a genuine presentation question, recorded in
§9.

**Distributed output.** `NozzleVisualization` draws a contour and a `trace` as a
point list. The solved `p(x)/p₀` maps onto `trace` directly, including the
duplicated abscissa at a shock (`03` §10.8), which renders as the vertical jump
the mock currently fakes with two authored points at `x = 0.62`.

**Regime-specific messaging.** `MODEL_LIMIT_SEPARATION` must be surfaced on this
page — it is where a user is most likely to over-read the result. The message
states that the model classifies overexpansion but does not predict separation
(`03` §10.9).

---

## 7. Engine Design mode

Out of scope for Phase 4 physics, but the attachment plan is recorded so that
nothing here forces a UI change later:

* `EngineModel.problems` already carries
  `{problemId, severity, message, targetKind, targetId}` with `severity` in
  `{info, warning}`. Solver `Diagnostic`s map onto that record exactly
  (ADR-16), and the Problems panel already focuses the offending component.
* Component readout rows in `ComponentRegistry` are `{label, value, unit}` with
  em dashes for solver-dependent quantities — the same shape a view model
  produces.
* The Injector and Nozzle workspaces show em dashes for pc, L\*, Δp, exit Mach,
  exit pressure, Cf and thrust. Those are precisely the outputs
  `engineering.injector` / `engineering.nozzle` will produce — after the
  compressible module is accepted, and in a later phase.

No engine-mode QML change is implied by anything in this specification.

---

## 8. Educational and engineering use in one backend (task §115)

There is **one** solver. There is no "teaching mode" with different equations.

The dual use is served entirely by metadata:

| Need | Served by |
| --- | --- |
| the number | the service result |
| the equation behind it | `EquationRecord.html` / `.latex` |
| why it is allowed to be used | `EquationRecord.assumptions` |
| what the number means physically | `EquationRecord.description` + the interpretation text |
| where it came from | `EquationRecord.source` and `Solution.provenance` |
| where it stops being valid | `EquationRecord.domain` + diagnostics |

A student and an engineer therefore see the same number, and the student sees
more context around it. Duplicating solvers "one simple, one real" would
guarantee that the two eventually disagree — which is the worst possible outcome
for a tool people learn from.

---

## 9. Recorded future UI requirements

Things the backend will eventually need that the frozen UI cannot express today.
**None of these is a change request, and none is actioned in Phase 4 without its
own UI phase.** They are recorded here so the need is documented at the moment
it was discovered.

| # | Requirement | Driven by | Severity |
| --- | --- | --- | --- |
| U-1 | A **branch selector** on the Isentropic page when "Given" is `A/A*` | `03` §3.4 — the API refuses to guess | **blocking** for that one input mode; the other three modes work without it |
| U-2 | Optional dimensional inputs (p₀, T₀, R, A) on Isentropic, Mass Flow, Normal Shock | the dimensional half of the module (`03` §31) | non-blocking; the dimensionless half is fully usable |
| U-3 | A third diagnostic tone for `error` alongside `info`/`warning` in the Problems panel | ADR-16 | non-blocking; errors render with the warning treatment until then |
| U-4 | A friction-convention label/switch on the Fanno page | `03` §8.2, task §112 | **blocking** for Fanno — an unlabelled `f` is exactly the ambiguity the spec forbids |
| U-5 | A visible marker for a zero-width regime band (ideal expansion is a point, not a range) on the Nozzle Lab scale | §6 above | cosmetic; the band renders, it is just very narrow |
| U-6 | Somewhere to show `Solution.provenance` and the assumption list per result | `01` §10 | non-blocking; the Isentropic page already has an assumptions panel that can carry it |
| U-7 | A mode switch on the Rayleigh page between "heat as T₀ ratio" and "heat as q" | §5.6 | non-blocking; ship the T₀-ratio mode first |

U-1 and U-4 are the only two that block a *specific* capability, and both are
single controls on pages that are currently placeholders anyway — so both will
be built as part of building those pages, not as modifications to accepted UI.
The Isentropic page is the exception: it is built, and U-1 touches it. The
recommendation is to ship Isentropic in Phase 4 with the three inverse modes that
need no branch, leaving the `A/A*` mode disabled with a note, until a UI phase
adds the selector. That keeps the frozen-UI promise intact.
