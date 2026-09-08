# Phase 5D — Thermochemistry Analysis Workspace

The first user-facing thermochemistry surface: a Calculator, a Composition
explorer, an O/F sweep and a reference comparison, over the NASA CEA provider
Phase 5C shipped.

**Verdict: READY FOR PHASE 5E.**

> **Amended 2026-09-04** by a corrective patch. See the
> [Phase 5D corrective addendum](#phase-5d-corrective-addendum) at the end of
> this report. The body below is the original accepted text; the addendum says
> what changed and what did not.

---

## 1. Baseline

| Gate | Opening | Closing |
| --- | --- | --- |
| Base (`.venv`, no CEA) | 5609 passed, 79 skipped, exit 0 | **5785 passed, 106 skipped**, exit 0, 41.19 s |
| CEA-enabled (`.venv-cea`) | 5690 passed, 1 skipped, exit 0 | **5893 passed, 1 skipped**, exit 0, 45.93 s |
| CEA-enabled repeat | — | 5893 passed, 1 skipped, 43.07 s |
| Frozen Compressible | 22/22 byte-identical | 22/22 byte-identical |

**203 new tests**, of which 27 require the provider and skip in the base
environment with a stated reason.

The Phase 4G manifest records `sha256(file)[:16]` per frozen file. All 22
recomputed digests match, so the manifest content is unchanged and the recorded
digest `8f0d1cf5…` still stands. The exact byte layout the digest was taken over
was not recorded in Phase 4G and is not re-derivable; the per-file comparison is
the substantive check.

---

## 2. What was built

### Application, Qt-free

| Module | Responsibility |
| --- | --- |
| `thermochemistry_provider.py` | the **one door** to a provider: availability, the shared instance, the reactant catalogue. Every provider import is function-local. |
| `thermochemistry_service.py` | `ChamberCase` → `ChamberEquilibriumRequest` → `Solution[ChamberGas]` → `ChamberOutcome`; readout rows, species rows, diagnostics, provenance, the condensed verdict |
| `thermochemistry_sweep.py` | range validation, scalar request generation, segmented series, warning aggregation, sampled maxima |
| `thermochemistry_reference.py` | the Level-B dataset, its rounding-box tolerances, and the comparison |

### Application, Qt

| Module | Responsibility |
| --- | --- |
| `thermochemistry_controller.py` | the `Thermochemistry` QML singleton — one controller, four views, one result |
| `thermochemistry_table_model.py` | `ThermoTableModel`, for the two tables whose columns are not all numbers |
| `uismoke.py` | a non-interactive tour of the workspace, runnable **frozen** |

### Data

`rocketforge/data/reference/thermochemistry_nasa_cea_2002_lox_lh2.json` — the
published NASA CEA case, its conditions, its source, and an explicit record of
what it publishes that this phase does not compare.

### Interface

`ui/pages/ThermochemistryPage.qml` plus thirteen files in
`ui/pages/thermochemistry/`: the four views, the provider-unavailable screen,
the result header, the warning block, the diagnostics and provenance panels,
the composition bars, and three sweep components.

### Modified

| File | Change |
| --- | --- |
| `main.py` | registers the `Thermochemistry` singleton; dispatches the new UI diagnostic |
| `ui/data/Navigation.qml` | the page, the `THERMOCHEMISTRY` domain, the page's own status wording |
| `ui/shell/SideNav.qml` | renders the new domain section |
| `ui/shell/StatusBar.qml` | `computedNote` → an overridable `originNote` |
| `ui/Main.qml` | honours the page's solver and origin wording, including the no-provider case |
| `ui/components/RFEngineeringTable.qml` | optional per-column `align: "left"` |
| `ui/components/RFLineChart.qml` | optional `showPoints`; tick decimals from the axis span; marker labels flip at the right edge |
| `rocketforge/providers/cea/provider.py` | public `species_table()` |

---

## 3. Decisions, and what forced them

### The gateway exists so that a launch stays cheap

`main.py` builds the controller at start-up so QML has a singleton to bind to.
If that chain imported the provider package, every launch would pay 181 ms for
a workspace the user has not opened, and on first use the native CEA library
and its 613 kB database. So every provider import in the gateway is
function-local, no other application module may name the provider package, and
a test builds the QML singletons **in a fresh interpreter** and asserts `cea` is
absent from `sys.modules`.

Measured: controller construction 0.12 ms. The first availability check — which
is what opening the workspace triggers — costs 56 ms, once.

### The provider gained one public method

`ChamberGas` carries a composition, not a species table, and converting mole
fractions to mass fractions needs molar masses and phases. Taking them from
anywhere but the provider that solved the case would introduce a second
atomic-weight table into an element balance Phase 5C spent effort removing one
from. So `CEAThermochemistryProvider.species_table()` was made public: three
lines, domain records only, sharing the cache the solve already filled.

### Two tables needed a second model

`EngineeringTableModel` holds a float64 block, which is exactly right for the
compressible tables. A composition table has a species name and a phase; a
sweep table has a per-point status. Encoding text as a float code so it could
live in a numeric block would have been worse than a second model, so
`ThermoTableModel` handles mixed columns and both tables use it.

### The pressure unit is the only unit selector

The rest of the workspace is SI throughout, including molar mass in kg/mol.
Chamber pressure is the one quantity a rocket engineer will not enter in
pascals, so it has a Pa/bar/MPa selector whose conversion lives in the
application layer. Changing it re-renders and does **not** mark the result
stale, because nothing scientific moved.

### Two components gained an option each

Both were forced by the data, and both default to the previous behaviour:

* **Column alignment.** Right-aligning `H2O` against `CO2` in a species column
  reads as a numeric column that has lost its digits.
* **Sampled points, and tick decimals from the axis span.** A molar-mass axis
  running 0.0185 to 0.0242 rendered five identical `0.02` tick labels under the
  old magnitude-based rule. Deriving the decimal count from the span fixes that
  and cannot change an axis whose ticks already differed. Drawing the sampled
  points is what stops a 41-point sweep from reading as a continuous curve.

---

## 4. Scientific labelling

Every chamber result carries provider, chemistry mode, constraint and the
adiabatic assumption — in the page header, the result header and the provenance
summary. The chamber temperature carries `Adiabatic · HP equilibrium` on its
own line and its help text says what it is not: not a wall temperature, not a
finite-rate prediction.

**The two-gamma trap is closed by naming.** The primary readout is
`Isentropic exponent γ_s`, qualified `equilibrium`; the frozen ratio is a
separate advanced row qualified `c_p,fr / c_v,fr`. `c_p` and `c_v` are both
qualified `frozen` — the pair that satisfies `cp − cv = R` — and the equilibrium
heat capacity is a separate advanced row qualified *does not satisfy
c_p − c_v = R*. The sweep charts the same `gamma` field under the same
qualifier, and a test asserts the two agree.

Measured on the canonical case: γ_s = 1.13259 against γ_fr = 1.19557, 5.6 %
apart. One field could not carry both, and one label could not either.

---

## 5. The assigned-enthalpy warning

Phase 5C's central finding reaches the user. When a stream temperature cannot
enter the calculation, the workspace shows the reactant by the provider's own
name, the temperature **requested**, the temperature **used by the model**, and
one sentence saying the result is still usable because the limitation belongs to
the provider's reactant data.

The input is never disabled and the requested value is never displayed as
though it had been used. The status stays `Solved with warnings` and the result
stays on screen — it is a caveat on a valid answer, styled as one.

Verified live: LOX at 95 K → `PROVIDER_ASSIGNED_ENTHALPY_REACTANT`, `O2(L)`,
requested 95 K, used 90.17 K, chamber state retained.
Negative control: GOX/GCH₄ at 320 K → no warning, and a chamber temperature
measurably different from the same case at 298.15 K, so the control is a
control rather than an accident.

---

## 6. Composition, and the two things it must not do

**It must not delete anything.** The display threshold is applied to a *view*
computed from the complete species tuple; the tuple is never filtered. A test
hides a trace species, asserts the row is gone, lowers the threshold and asserts
the row returns with its original value — the mutation proof. The hidden count
and the fraction they account for are stated, and Σ is reported over every
species, not the visible ones. The labels read `≥ 1e-6` because a row exactly at
the threshold is kept.

**It must not confuse a candidate with a presence.** The condensed verdict reads
the state's `condensed_mass_fraction`, which the provider computes from the
returned composition, and never a count of candidate condensed species. Both
halves are covered live: the canonical case reports `None detected` at 6.24e-08
with `C(gr)` genuinely in the composition, and the fuel-rich case at O/F 0.5
reports `Present`, names `C(gr)` and annotates its row.

---

## 7. The sweep, and what it refuses to say

41 points over O/F 2.5–4.5, one scalar solve each, in order, in this process.
No batch API and no threads: Phase 5B-0 measured four threads at ~0.85× of
serial for CEA. The point guard is 1000, derived from Phase 5C's measured
0.568 ms per point rather than chosen for caution.

**Failed points stay.** A point that did not solve keeps its row, its place and
its message; its numbers are em dashes; the chart line **breaks** across it and
a dashed guide marks the mixture ratio. Tested by injecting a failure at one
ratio and asserting the series splits into two segments — with the control that
a clean sweep produces exactly one.

**Repeated warnings are aggregated** into one row naming the code, the count and
the range, with the per-point diagnostics untouched.

**Nothing is called optimal.** Measured on this sweep, three responses peak in
three different places — T₀ at O/F 3.75, γ_s at 2.5, M̄ at 4.5 — so there is no
single peak to recommend. Markers read `Maximum … in sweep`, and a test asserts
no public name in the sweep module promises a decision.

---

## 8. Reference comparison

The published NASA CEA (2002 Fortran) LOX/LH₂ case at O/F 6.0 and 1000 psia,
reproduced through the whole application pipeline:

| Quantity | Published | RocketForge | Difference | Source box | Verdict |
| --- | --- | --- | --- | --- | --- |
| Chamber temperature T₀ | 3483.35 K | 3483.35 K | 6.001e-07 | 1.435e-06 | PASS |
| Mean molar mass M̄ | 0.0134580 kg/mol | 0.0134581 kg/mol | 1.034e-05 | 3.715e-05 | PASS |

The tolerance is the source's own rounding box, computed from the significant
figures the dataset declares. Widening it means editing that declaration, which
is a visible change to a shipped file — and a test asserts it moves the
tolerance when it does.

**The mutation proof.** A copy of the dataset with the published temperature
moved by 1 % is asserted to have actually changed, then asserted to flip the
verdict to FAIL. Without it the comparison could be reading nothing.

**The performance boundary is structural, not cosmetic.** The source publishes
c\*, Isp and an exit gamma. The dataset carries **no value** for any of them —
only their names and the reason they are not compared. A quantity whose value is
never loaded cannot leak into a display.

---

## 9. Architecture

48 additive rules. The ones that matter most:

| Rule | How it is checked |
| --- | --- |
| QML imports only Qt, this repo and the app singletons | the allowed set is enumerated, not the banned one |
| QML names no chemistry library as code | string literals blanked first, so `"NASA CEA 3.3.4"` stays a label |
| QML does only layout arithmetic | `Math.*` restricted to max/min/floor/ceil/round/abs |
| QML carries no physical constant and no unit conversion | scanned with a negative control that proves the scan works |
| No performance quantity is named in QML code | matched on **camelCase words**, never substrings |
| No provider import at module level anywhere in the chain | AST, top-level statements only |
| Only the gateway names the provider package | AST, all imports |
| The service layer imports no Qt | so its logic is testable headlessly |
| `physics` does not import `application`; `providers` imports neither `application` nor Qt | AST |
| A normal launch does not import CEA | a **fresh interpreter** builds the singletons and inspects `sys.modules` |
| `ChamberGas` still carries no performance field | on the real dataclass |
| The compressible and Engine Design QML never mentions the chemistry controller | content, not timestamps |

Two of those scans were written twice. The first version of the performance
audit flagged `chamberPressureDisplay` because `display` contains `isp` — the
same false positive that flagged RocketForge's own `MixtureRatio` for containing
`Mixture` in Phase 5C. Both now tokenise camelCase and both carry a negative
control asserting the matcher would catch a real leak.

---

## 10. Performance

Measured through the controller, because that is the wait a user experiences.

| | |
| --- | --- |
| Warm calculation, end to end | **0.63 ms** median, 0.75 ms worst of 50 |
| First calculation, cold provider | 3.42 ms |
| First availability check | 56.0 ms, once |
| **41-point sweep** | **22.7 ms** — 21.9 ms solver, 0.8 ms interface |
| 101-point sweep | 55.6 ms |
| 1000-point sweep, the guard | 558 ms — 535 ms solver, 23 ms interface |
| Reference case | 1.42 ms |

The interface is 3.5 % of a 41-point sweep and 4 % of a 1000-point one, so
there was nothing to fix in the interface and no reason to thread the solver. A
1000-point sweep retains 8.73 MB against an 8.92 MB peak, and a second one
costs the same.

---

## 11. Packaging and parity

Clean rebuild from `.venv-cea`: **203.9 MB, 2106 files**, +0.2 MB and +15 files
over Phase 5C. The bundled `thermo.lib` hash matches the build input. Cantera,
RocketCEA, CoolProp, the tests and the experiment scripts are absent. The
executable launches with the window titled "RocketForge" and closes with exit 0,
and Phase 5C's provider self-test still passes unchanged.

The packaged application ran the **same tour** as the source build, through a
second, separate diagnostic flag — `--selftest-thermochemistry-ui` — added
rather than repurposing Phase 5C's. "Can the bundled provider solve?" and "does
the bundled interface show the right numbers?" are different questions.

**3909 scalar fields compared across 35 captures. Zero differences.** Every
readout, raw value, provenance string, species-set entry, condensed verdict,
sweep count and reference comparison is identical between source and bundle.

---

## 12. Known limitations

* **One provider, so no provider selector.** The architecture supports a change
  of provider — the gateway is the single door and a change clears every result
  — but there is nothing to switch to, and a selector with one entry would
  suggest otherwise.
* **Five propellants.** The catalogue is the provider's production set, because
  offering a sixth would be offering something with no provider name behind it.
  Widening it is a data-curation task with its own provenance requirements.
* **The sweep varies O/F only.** A pressure sweep would need a second axis and
  a second chart family; the brief scopes this phase to O/F.
* **No export.** Copy-to-clipboard exists for both tables. A file-export
  subsystem does not exist in RocketForge yet and Phase 5D does not start one.
* **The 1e-6 condensed display floor** is a presentation choice, stated as one:
  the exact fraction is always shown beside the verdict.

---

## 13. Reported spec discrepancy — `PHASE_5D_CHART_ARCHITECTURE_NOTE`

Brief §70 states that the project uses **Qt Graphs 2D** for interactive
application charts. It does not: there is no `QtGraphs` or `QtCharts` import
anywhere in `ui/`, `rocketforge/` or the requirements files. Every chart in
RocketForge is drawn by `RFLineChart` on `RFPlotSurface`, a Canvas painter the
project owns.

The binding instruction in the same section — *"Use existing RocketForge chart
architecture"* — is followed: Phase 5D uses `RFLineChart` / `RFPlotSurface` and
introduces no chart library. Recorded rather than silently resolved, because the
brief names a specific technology.

---

## 14. Deliberately not implemented

RocketForge c\*, Cf, Isp, thrust, effective exhaust velocity, combustion
efficiency, density impulse, optimum O/F, Pareto fronts, objectives,
constraints, scoring, a generic trade-study engine, chamber geometry, L\*,
injector sizing, cooling, nozzle performance, engine cycles, finite-rate
chemistry, a Cantera provider selector, CoolProp, transport-property display.

---

## 15. Recommended Phase 5E — Ideal Rocket Performance

Characteristic velocity c\*, thrust coefficient Cf, momentum and pressure
thrust, total thrust, effective exhaust velocity and specific impulse, with
**RocketForge-owned equations**, using NASA CEA's native c\*, Cf and Isp as
independent provider oracle values — which `oracle.py` already records with the
full conditions each was produced under.

Phase 5E must keep four things apart that Phase 5D deliberately kept apart too:
chamber thermochemistry, combustion performance, nozzle performance and total
engine performance. And it must not modify frozen Compressible v1 casually.


---

# Phase 5D corrective addendum

**Date: 2026-09-04.** Applied after the report above was accepted, and recorded
here rather than edited into it.

## What was wrong

The Composition tab reported a condensed mass fraction below its display
threshold as:

    None detected — condensed mass fraction 6.242e-08.

**6.24e-08 is not zero.** "None detected" claims the mixture contains no
condensed material, which is a stronger statement than the number supports. The
number was shown beside it, so nothing was hidden — but the headline said
something the measurement does not.

## What changed

The two "not present" cases became two states instead of one:

| Fraction | Before | After |
| --- | --- | --- |
| exactly 0 | *None detected* | **No condensed product reported** |
| `0 < f < 1e-6` | *None detected* | **No condensed phase above reporting threshold** |
| `f >= 1e-6` | Condensed products present | Condensed products present *(unchanged)* |
| not reported | Unknown is not the same as none | *(unchanged)* |

Every known state now shows the **exact condensed mass fraction** and the
**reporting threshold** it was judged against, so the verdict is never the only
number on screen. A condensed species below the threshold is named as *"in the
composition, below it"* rather than as present.

`_CONDENSED_DISPLAY_FLOOR` became the public
`CONDENSED_REPORTING_THRESHOLD`, and a test asserts that neither the constant
nor the phrase "reporting threshold" appears anywhere in `physics`,
`providers`, `core` or `engineering` — it decides a sentence, not a number.

## What did **not** change

| | |
| --- | --- |
| Provider physics | **NO** |
| `condensed_mass_fraction` computation | **NO** |
| Composition, species mapping, element balance | **NO** |
| Candidate-vs-presence rule | **NO** — presence is still read from the returned composition, never from `num_condensed` |
| Assigned-enthalpy behaviour | **NO** — same diagnostic, same warning, same `Solved with warnings`, input still enabled |
| O/F sweep semantics, failed-point segmentation, optimiser boundary | **NO** |
| Frozen Compressible v1 | **NO** — 22/22 byte-identical |
| Engine Design, compressible workspaces | **NO** |
| Any calculated output | **NO** — source ↔ packaged parity re-run: 4110 fields, 0 differences |

## Two defects found while applying it

Both were introduced by the patch and fixed within it.

1. **The verdict fell off the bottom at 1366×768.** Two extra rows pushed the
   condensed block out of the control rail. It now lives with the composition
   it describes, in the result panel, where it is visible without scrolling —
   and the rail holds only display controls, which is where it belonged.

2. **`CONDENSED` printed on top of `C(gr)`.** `RFEngineeringTable`'s marker
   gutter assumed a right-aligned first column, whose text parks at the
   column's right edge and leaves the left padding free for a label. Phase 5D's
   left-aligned species column starts its text exactly where the label is
   drawn. The gutter now asks for the full label width when the first column is
   left aligned — a Phase 4G gate 9.6 violation, caught by looking at the
   screenshot rather than by a test, and now covered by one.

A third, in the tests: the readout audit still matched banned words as
substrings and flagged the new help text for containing "isp" inside
*display*. That is the **third** occurrence of this false positive in the
project. It now tokenises words, with a negative control.

## Gates after the patch

| Gate | Result |
| --- | --- |
| Base | **5799 passed, 106 skipped**, exit 0 |
| CEA-enabled | **5907 passed, 1 skipped**, exit 0; repeat identical |
| New Phase 5D tests | **217** (was 203) |
| Architecture | 41 + 18 + 18 + **50**, all green |
| QML warnings | **0** — source, base and packaged |
| Source ↔ packaged parity | 35 captures, **4110 fields, 0 differences** |
| Frozen Compressible | **22/22 byte-identical** |
| Packaged | clean rebuild, launches, closes with exit 0; provider self-test unchanged |

## Also recorded

**Reactant enthalpy / fluid-property coupling** is now listed as a deferred,
non-blocking task in the UI contract. Phase 5D reports the CEA
assigned-enthalpy limitation correctly; it does not solve it, and this patch
does not either.
