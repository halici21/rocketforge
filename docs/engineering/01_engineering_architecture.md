# 01 — Engineering Architecture

**Phase 3 — architecture only. No production physics code exists or is created
by this document.**

Status of the interface: **ROCKETFORGE UI FOUNDATION v1.0 — ACCEPTED / FROZEN.**
Nothing in `ui/` is modified by this phase, and nothing in this document asks
for a QML change. Where the backend eventually needs something the interface
cannot yet express, that is recorded here as a future UI requirement, not as a
change request.

---

## 1. What exists today

Verified by direct inspection of `C:\Users\erayh\Documents\Python\rocket` on
2026-08-30. Read-only; no file was edited.

| Area | State |
| --- | --- |
| Python source | `main.py` only (bootstrap, ~160 lines) plus `packaging/make_icon.py`. **There is no Python package in the project yet.** |
| Interface | `ui/` — 102 files, 98 `.qml`, organised as `theme/`, `components/`, `visuals/`, `pages/`, `shell/`, `data/`, `engine/{model,inspector,workspaces,visuals,dialogs}` |
| Python→QML surface | Exactly one singleton: `AppEnvironment` registered as `App` under URI `RocketForge` (product name, version, stage, system colour scheme, `applyColorScheme`) |
| Analysis pages | 12 navigation entries in `ui/data/Navigation.qml`. Two are built (`IsentropicPage.qml`, `NozzleLabPage.qml`); ten use the shared `ModulePlaceholderPage.qml` skeleton |
| Numbers on screen | All hand-authored constants in `ui/data/MockData.qml`, one singleton, no literals in pages |
| Engine mode | `EngineModel.qml` (graph state, selection, structural `problems`), `ComponentRegistry.qml` (16 component types, port topology, node geometry), `MockEngineData.qml` (demo architecture) |
| Component workspaces | `InjectorWorkspace.qml`, `NozzleWorkspace.qml` built; all others fall back to `PlaceholderComponentWorkspace.qml` |
| Dependencies | `PySide6-Essentials==6.10.2` only. No NumPy, no SciPy, no property libraries |
| Packaging | `packaging/RocketForge.spec`, directory build, Qt modules deliberately **not** pruned |

Three properties of the existing code make the backend easy to attach and must
be preserved:

1. **`MockData.qml` is the single sink for displayed numbers.** A page reads
   `MockData.flowState`, never a literal. Replacing the mock with a view model
   that exposes the same shape (`{label, value, unit}` rows) is a
   property-source swap, not a page rewrite.
2. **`ComponentRegistry.qml` is editor metadata only** — display name, glyph,
   node geometry, port topology, placeholder readout. It contains no behaviour,
   so the engineering component layer can be attached to component *types*
   without competing with it.
3. **`EngineModel.problems` is explicitly structural** ("Nothing here inspects
   pressures, flows or temperatures — that is solver work"). It already has the
   record shape `{problemId, severity, message, targetKind, targetId}`, which is
   the natural channel for solver diagnostics later.

---

## 2. Layer model

Eight layers. Each has one sentence of responsibility and an explicit list of
what it is allowed to import. `comparison` sits beside `providers`: both build
on `physics` and `core`, and only `application` may use either.

```
  L6  ui/                QML. No Python. No arithmetic beyond layout.
       ^ (properties, signals, slots on registered QObjects)
  L5  application/       Composition root, controllers, view models, formatting.
       ^
  L4  providers/         Adapters onto external libraries (CoolProp, CEA, ...).
      comparison/        Reference-case comparison. Never runs a solver.
       ^            (implements interfaces declared in L1 - see section 5)
  L3  engine/            Whole-engine assembly, balances, cycle iteration.
       ^
  L2  engineering/       Component design: injector, chamber, nozzle, pump, ...
       ^
  L1  physics/           Fundamental relations. Compressible flow lives here.
       ^
  L0  core/              Units, constants, errors, results, numerics, provenance.
```

| Layer | Responsibility | May import |
| --- | --- | --- |
| `core` | Things with no physics content: unit conversion, universal constants, the result/error types, tolerance definitions, root finders, array helpers, provenance records | stdlib, NumPy |
| `physics` | Fundamental relations that are true independently of any device: γ-based compressible relations, fluid property *interfaces*, thermochemical *interfaces*, transport correlations | `core` |
| `engineering` | Design and sizing of one physical component, using L1 relations | `physics`, `core` |
| `engine` | Assembly of components into a cycle: mass balance, pressure network, shaft power balance, iteration | `engineering`, `physics`, `core` |
| `providers` | Concrete adapters that satisfy L1 interfaces using external libraries | `physics`, `core`, external libs |
| `comparison` | Compares RocketForge results with reference cases (direct CEA, NASA printouts, independent codes, experiments) and reports the differences; draws a verdict only where the source kind permits one | `physics`, `core` |
| `application` | The only place that wires providers to services and exposes QObjects to QML | everything below |
| `ui` | Presentation | nothing Python |

**Hard rules.**

* `physics` must never import `engineering`, `engine`, `providers`,
  `application`, or PySide6.
* `engineering` must never import `engine` or `application`.
* Nothing below `application` may import PySide6, and nothing below
  `application` may require a `QApplication`/`QGuiApplication`/`QQmlEngine` to
  import or to run. This is an acceptance criterion, not a preference (task §89).
* External engineering libraries (CoolProp, RocketCEA, Cantera) are imported in
  `providers/` **and nowhere else**.
* `comparison` must never import `providers` or `application`. It compares
  values it is handed; if it could run a solver, a comparison could produce
  the very number it is checking. Added with Solid Propellant Thermochemistry
  Phase 1.

---

## 3. Package layout

```
rocket/
  main.py                      # unchanged: Qt bootstrap only
  ui/                          # unchanged: frozen QML
  rocketforge/                 # NEW in Phase 4 - the engineering package
    __init__.py
    core/
      __init__.py
      constants.py             # universal constants, standard gravity
      units.py                 # boundary conversion, no runtime unit algebra
      errors.py                # exception hierarchy
      result.py                # Solution[T], Status, Diagnostic
      provenance.py            # RelationRef, EquationRecord, registry loader
      tolerances.py            # named tolerance categories, ToleranceSet
      validation.py            # domain guards used by public relations
      numerics/
        __init__.py
        roots.py               # brent(), bracket helpers, RootReport
        arrays.py              # scalar/array normalisation, broadcasting
        sampling.py            # sweep grids (linear, log, Mach-clustered)
    physics/
      __init__.py
      compressible/            # THE PHASE 4 MODULE - see 03_...
        __init__.py
        gas.py
        isentropic.py
        mass_flow.py
        normal_shock.py
        oblique_shock.py
        prandtl_meyer.py
        fanno.py
        rayleigh.py
        nozzle.py
        types.py               # branch enums, shared result dataclasses
        equations.py           # relation metadata for this module
      fluids/
        interfaces.py          # FluidPropertyProvider protocol + FluidState
        constant.py            # trivial constant-property provider (in-tree)
      thermochemistry/
        interfaces.py          # ThermochemistryProvider protocol + ChamberGas
      heat_transfer/           # (later)
      combustion/              # (later)
    engineering/               # (later) injector/ chamber/ nozzle/ cooling/ ...
    engine/                    # (later) network/ cycles/ balances/ solver/
    providers/                 # (later) coolprop/ rocketcea/ cantera/ tabulated/
    application/
      __init__.py
      controllers/             # QObject facades per analysis page
      viewmodels/              # plain data shaped for the QML it feeds
      adapters/                # Solution -> readout rows, series -> plot model
      formatting.py            # display units, significant figures, em dash
  tests/
    core/ physics/compressible/ reference_data/
  docs/engineering/            # this specification set
```

`rocketforge/` sits beside `ui/` rather than inside it so that
`import rocketforge` works from a notebook, a script or a test with the project
root on `sys.path`, with Qt absent from the process entirely (task §88).

**Packaging consequence.** `packaging/RocketForge.spec` will need
`rocketforge/` on the analysis path in Phase 4. That is a one-line addition to
an existing list; the `excludes` list must not grow (the QtNetwork lesson
stands).

---

## 4. Dependency direction and how it is enforced

```
             external libs
                   |
                   v
   ui --> application --> providers --+
                |                     |
                +--> engine --> engineering --> physics --> core
                |                                  ^
                +----------------------------------+
                     (providers implement physics-declared interfaces)
```

Direction is enforced by a test, not by convention:

* `tests/test_architecture.py` walks the AST of every module under
  `rocketforge/` and asserts the imports of each file against the allow-list in
  §2. A `physics` module importing `engineering`, `providers`, `PySide6` or
  `CoolProp` fails the suite.
* A second assertion imports `rocketforge.physics.compressible` in a
  subprocess with `PySide6` blocked by a meta path finder, proving task §89.

This is cheap to write, runs in milliseconds, and is the only thing that keeps
the boundary real once several people are adding modules.

---

## 5. Provider architecture (external property libraries)

The naive arrangement — every component importing CoolProp — is forbidden by
task §15, and the fix is dependency inversion:

* **`physics/fluids/interfaces.py` declares the protocol** and the state type
  it returns. It imports nothing but `core`.
* **`providers/coolprop/provider.py` implements the protocol** and is the only
  module allowed to `import CoolProp`.
* **`application/` chooses and injects the implementation.** A service is
  constructed with a provider; it never reaches for a global.

```python
# physics/fluids/interfaces.py   (SPECIFICATION - not implementation)

class FluidPropertyProvider(Protocol):
    """Thermophysical properties of a single-species fluid, SI units."""

    name: str        # "CoolProp", "constant-property", "table:LOX-v2"
    version: str     # provider version, recorded in provenance

    def state_pt(self, fluid: str, pressure: float, temperature: float) -> FluidState: ...
    def state_ph(self, fluid: str, pressure: float, enthalpy: float) -> FluidState: ...
    def saturation_pressure(self, fluid: str, temperature: float) -> float: ...
    def supports(self, fluid: str) -> bool: ...
```

`FluidState` returns SI floats: `pressure` [Pa], `temperature` [K], `density`
[kg/m³], `specific_enthalpy` [J/kg], `specific_entropy` [J/(kg·K)], `cp`, `cv`
[J/(kg·K)], `viscosity` [Pa·s], `thermal_conductivity` [W/(m·K)],
`speed_of_sound` [m/s], `phase` (enum), plus a `source` provenance record.
Every field the provider cannot supply is `None`, never a guessed number.

```python
# physics/thermochemistry/interfaces.py   (SPECIFICATION)

class ThermochemistryProvider(Protocol):
    name: str
    version: str

    def equilibrium_chamber(
        self, fuel: str, oxidiser: str, mixture_ratio: float,
        chamber_pressure: float,
    ) -> ChamberGas: ...

    def expand(
        self, chamber: ChamberGas, area_ratio: float, mode: ExpansionMode,
    ) -> GasStation: ...
```

`ChamberGas` carries `temperature` [K], `gamma` [-], `gas_constant` [J/(kg·K)],
`molar_mass` [kg/mol], `cp`, composition, and provenance. **This is exactly the
handshake into the compressible module**: `ChamberGas` → `PerfectGas(gamma, R)`
plus `p0`, `T0`. See the §117 boundary in `06_future_module_dependency_map.md`.

**Error model for providers.** A provider raises `ProviderUnavailableError`
(library not installed), `ProviderDomainError` (state outside the library's
range, e.g. below the triple point), or `ProviderFluidUnknownError`. It never
returns a substitute value. Callers translate these into `Diagnostic` entries
on the `Solution`.

**v1 ships zero providers.** Compressible v1 is given γ, R, p₀, T₀ as inputs and
computes chemistry-free. The interfaces are written now only so that the later
modules have somewhere to attach.

---

## 6. UI adapter layer

QML receives prepared state. It never computes.

```
Solution[IsentropicRatios]        (physics, SI floats, radians)
        |
        v  application/adapters
ReadoutRows: [{label, value, unit, tone}]   <- already formatted strings
PlotSeries:  {x: [...], y: [...], label, ...}
Diagnostics: [{severity, message, code}]
        |
        v  application/controllers  (QObject: Property / Signal / Slot)
QML property binding
```

Rules, to be treated as architectural, not stylistic:

* **QML must not calculate** pressure ratios, Mach numbers, mass flow, thrust,
  heat flux, pump power, or unit conversions. Existing QML does not: the only
  arithmetic in `ui/` is layout, colour, and one array-index lookup
  (`MockData.nearestSampleIndex`), which is a lookup, not an evaluation.
* Rounding, significant figures, unit symbols and the em dash for
  "no value yet" are decided in `application/formatting.py`, so the same rule
  applies everywhere and the frozen UI keeps rendering plain strings.
* Controllers are thin: validate → call service → adapt → set properties →
  emit. No relation is ever written in a controller.
* Controllers are **per page**, mirroring `ui/data/Navigation.qml`, so one
  page's failure cannot blank another.

---

## 7. Units policy

**Decision: SI floats internally, units converted at the boundary. No Pint in
the physics core.**

Internal SI base for every quantity crossing a `physics` or `engineering`
function boundary:

| Quantity | Unit | Quantity | Unit |
| --- | --- | --- | --- |
| pressure | Pa | length | m |
| temperature | K | area | m² |
| density | kg/m³ | velocity | m/s |
| mass flow | kg/s | specific gas constant | J/(kg·K) |
| specific heat | J/(kg·K) | angle | **rad** |
| force | N | heat flux | W/m² |

Options weighed:

| | A — Pint everywhere | B — SI floats + boundary conversion (**chosen**) | C — no unit handling at all |
| --- | --- | --- | --- |
| Correctness | Highest; dimensional errors caught by the library | Guarded by naming, typing and tests | Nothing catches a mistake |
| Sweep cost | `Quantity` arithmetic is roughly 10–100× a float op; a 2000-point sweep with six outputs becomes noticeable in an interactive UI | Native NumPy | Native |
| Vectorisation | Works, but wraps arrays and complicates NumPy idioms | Direct | Direct |
| Interop | Every provider and every test must speak Pint | Providers already speak SI floats | — |
| Failure mode | A stripped magnitude silently reintroduces the very bug Pint was bought to prevent | A wrong unit is a wrong number at exactly one place: the boundary converter, which is unit-tested | Wrong numbers anywhere |

**Recommendation: B.** Pint is not a dependency of `rocketforge.physics`.
`core/units.py` holds an explicit table (`dimension → {symbol: (factor, offset)}`)
covering the display units the UI offers, with `to_si(value, unit)` and
`from_si(value, unit)`, plus a test that every registered unit round-trips.
Temperature and gauge pressure are the only offset conversions and are handled
explicitly.

Consequences: function names and docstrings must state units (`pressure: float
— static pressure [Pa]`); a public function never accepts "a pressure in
whatever unit"; the UI's SI/US switch is a formatting concern in
`application/`. If user-typed unit *expressions* ("lbf/in²·s") are ever
required, Pint may be adopted **in `application/` only**, never below it.

---

## 8. Angle policy

**Internal: radians, always. Display: degrees.**

* Every angle argument and every angle field in a `physics` result is in
  radians.
* Conversion happens in `application/`, at the same boundary as units.
* Naming enforces it: a field carrying degrees must be named with a `_deg`
  suffix and may only exist in `application/` or in a view model. A `physics`
  module may not define a name ending in `_deg`; the architecture test asserts
  this.

This is the most common source of silent error in oblique-shock and
Prandtl–Meyer code, and it is cheap to make structurally impossible.

---

## 9. Determinism

Identical inputs plus an identical model version produce a bit-identical result.

* No randomness anywhere in `physics` or `engineering`.
* No hidden global mutable state, and no module-level caches for cheap
  relations. Configuration (tolerances) is passed in, defaulting to a frozen
  `DEFAULT_TOLERANCES` instance.
* Iteration counts and bracket choices are fixed by the algorithm, never by
  wall-clock time or dictionary ordering.
* Sweep results depend only on the requested grid, never on the order in which
  the UI happened to ask.

Consequence: this is what makes regression reference data meaningful, and what
allows a study to be re-run and compared months later.

---

## 10. Provenance and model versioning

Every public relation family carries a `RelationRef`:

```python
@dataclass(frozen=True)
class RelationRef:
    identifier: str        # "isentropic.area_ratio.v1"
    name: str              # "Isentropic area-Mach relation"
    model: str             # "perfect_gas_isentropic_v1"
    source: str            # "Anderson, Modern Compressible Flow, ch. 5"
    assumptions: tuple[str, ...]
    domain: str            # human-readable domain statement
```

`Solution.provenance` is a tuple of the `RelationRef`s actually used, so a
nozzle solution that crossed a shock lists both the isentropic and the normal
shock relation. Results carry references, **not** copies of the assumption
prose: the text lives once in the equation registry
(`02_data_model_and_api_contracts.md` §9) and is looked up by identifier.

**Model versioning: adopt it now.** The identifier suffix (`_v1`) and the
`model` string cost nothing today and are the only way a stored study can later
be told apart from the same study re-run against variable-γ chemistry. The rule:
a change that alters a returned number for unchanged inputs requires a new model
identifier; a bug fix that makes a wrong number right is a version bump recorded
in the changelog and in `reference_data`.

---

## 11. Naming conventions

**Static vs stagnation.** Static is bare, stagnation takes a `0`, the sonic
reference takes `_star`:

| Symbol | Code name | Symbol | Code name |
| --- | --- | --- | --- |
| p | `pressure` | p₀ | `stagnation_pressure` |
| T | `temperature` | T₀ | `stagnation_temperature` |
| ρ | `density` | ρ₀ | `stagnation_density` |
| a | `speed_of_sound` | p* | `pressure_star` |
| V | `velocity` | A* | `area_star` |
| M | `mach` | ṁ | `mass_flow` |
| γ | `gamma` | R | `gas_constant` |
| θ | `theta` (rad) | β | `beta` (rad) |
| ν | `nu` (rad) | μ | `mach_angle` (rad) |
| A/A* | `area_ratio` | p/p₀ | `pressure_ratio` |

Banned as identifiers: `Pt`, `P0`, `PT`, `Tt`; mixing `stagnation_pressure` and
`p0` in the same module; `P` for pressure alongside `p` for something else.

**Pressure disambiguation (task §126).** The generic compressible module uses
physical names only:

| Name | Meaning | Where it is legal |
| --- | --- | --- |
| `stagnation_pressure` | p₀ at the station in question | everywhere |
| `back_pressure` | ambient pressure imposed downstream of a nozzle exit | `compressible.nozzle` |
| `exit_pressure` | static pressure at the exit plane | `compressible.nozzle` |
| `chamber_pressure` | p₀ of the combustion chamber | `engineering.chamber`, **not** in `physics` |
| `ambient_pressure` | atmosphere around a vehicle | `engineering.nozzle` (thrust), **not** in `physics.compressible` |

`chamber_pressure` deliberately does not appear in the fundamental module: the
compressible nozzle receives a stagnation pressure, and whether it came from a
combustion chamber is not its business.

---

## 12. Architecture Decisions

Format: Decision / Alternatives / Reason / Consequence.

**ADR-01 — A pure-Python engineering package, `rocketforge/`, beside `ui/`.**
*Alternatives:* physics inside `ui/`; a separate repository; physics in QML/JS.
*Reason:* task §88/§89 require the physics to run without Qt; a sibling package
makes that structurally true and keeps one repository, one version, one test
suite.
*Consequence:* `main.py` gains one import in Phase 4; the PyInstaller spec gains
the package; nothing else in the app changes.

**ADR-02 — Seven layers with a tested import allow-list.**
*Alternatives:* a flat `rocketforge/` module set; convention-only boundaries.
*Reason:* the coupling this phase exists to prevent does not appear on day one —
it appears on month nine, when the cooling module "just needs" the nozzle's
contour helper. Only an executable rule survives that.
*Consequence:* one extra test file; occasional friction when a shortcut is
tempting, which is the point.

**ADR-03 — SI floats internally; unit conversion at the application boundary;
no Pint in the core.**
*Alternatives:* Pint everywhere; unit-tagged DTOs down to the kernels.
*Reason:* see §7 — interactive sweeps make per-element unit algebra a real cost,
and the boundary is a single testable place.
*Consequence:* unit correctness rests on naming discipline and tests; the
converter table must be exhaustively tested; Pint remains available above L5 if
free-form unit input is ever demanded.

**ADR-04 — Radians internally; `_deg` names forbidden below `application/`.**
*Alternatives:* degrees internally because the UI shows degrees.
*Reason:* every trigonometric relation in the module is written in radians;
converting at the boundary means exactly one conversion per value.
*Consequence:* oblique-shock and PM view models must convert; the architecture
test enforces the naming rule.

**ADR-05 — Dependency inversion for external property libraries: interfaces in
`physics`, implementations in `providers`, wiring in `application`.**
*Alternatives:* direct imports at each call site; a global singleton registry.
*Reason:* task §15 forbids library leakage; a protocol keeps `physics`
importable with CoolProp absent, which also keeps the frozen build small until a
provider is actually shipped.
*Consequence:* providers must be constructed and passed; a small amount of
wiring code in `application/`.

**ADR-06 — A typed result wrapper, `Solution[T]`, rather than bare values or
dictionaries.**
*Alternatives:* return floats and raise on everything; return dicts.
*Reason:* the module must carry warnings ("near-sonic, Mach resolution
limited"), convergence data, branch identity and provenance — none of which fits
in a float, and all of which is unreadable and untypeable in a dict.
*Consequence:* two call styles (see ADR-07); slightly more code per relation.

**ADR-07 — Two-tier API: bare pure functions for algebraic relations,
`Solution`-returning services for anything with branches, iteration or
classification.**
*Alternatives:* wrap everything; wrap nothing.
*Reason:* `p_over_p0(mach, gamma)` returning `Solution[float]` would make the
package tiresome from a notebook and would wrap the vectorised path in
per-element objects. Iterative and branched relations genuinely need the extra
information.
*Consequence:* documented in `02` §3; the rule is "algebraic and total → bare
float/array; inverse, branched or classified → `Solution`".

**ADR-08 — Immutable, frozen dataclasses for all state and result types.**
*Alternatives:* mutable dataclasses; plain dicts.
*Reason:* reproducibility, safe hand-off to a worker thread, safe caching, and
safe storage in a QML view model that may outlive the call.
*Consequence:* "modify" means "construct a new one"; `dataclasses.replace` is
the idiom.

**ADR-09 — NumPy is a dependency; SciPy is not, for v1.**
*Alternatives:* SciPy for `brentq`; pure-Python loops.
*Reason:* every v1 inverse is a scalar, bracketed, monotone 1-D root — about
sixty lines of Brent that we must test anyway. SciPy would add a large binary
wheel to a frozen build whose packaging is only just proven stable, and it
returns less diagnostic detail than `Solution` needs. NumPy is unavoidable for
sweeps and array outputs.
*Consequence:* `core/numerics/roots.py` must be first-class code with its own
test suite against analytic roots, including pathological brackets. SciPy is
reconsidered — and probably adopted — when `engine/solver` needs multivariate
cycle balancing, which is a different layer and a different phase.

**ADR-10 — Pandas is not a dependency of `physics`.**
*Alternatives:* DataFrame outputs from sweeps.
*Reason:* NumPy arrays carry everything the plots and tables need; Pandas would
add weight to the frozen build and an idiom the UI cannot consume directly.
*Consequence:* tabular export lives in `application/`, where Pandas may be used
if it ever earns its place.

**ADR-11 — `float64` throughout; no extended precision.**
*Alternatives:* `decimal`/`mpmath` for near-sonic inversion.
*Reason:* the ill-conditioning near M = 1 is algebraic — the area relation is
quadratically flat at the sonic point (see `04` §4) — so extra precision buys
only a square root's worth of improvement at a large cost. Every reference case
in this specification is stated to a precision `float64` reaches comfortably.
*Consequence:* documented Mach resolution limits near sonic, and a sonic
tolerance rather than a pretence of exactness.

**ADR-12 — Relation metadata lives in one registry, referenced by identifier.**
*Alternatives:* assumption strings duplicated in every result.
*Reason:* the Equation Library page already exists in the navigation and will
want the same records; duplication guarantees drift.
*Consequence:* results carry `RelationRef` tuples; the registry is the single
source, loadable without Qt.

**ADR-13 — Model identifiers are versioned from the first release
(`perfect_gas_isentropic_v1`).**
*Alternatives:* add versioning when a second model appears.
*Reason:* retrofitting a version onto stored results is impossible; the cost now
is a string.
*Consequence:* a numeric-behaviour change requires a new identifier and a
reference-data update.

**ADR-14 — Compressible v1 is calorically perfect, constant γ, constant R —
with no back door.**
*Alternatives:* a γ(T) hook "for later".
*Reason:* task §28 and §71; a half-wired variable-γ path is how a validated
module silently becomes unvalidated.
*Consequence:* variable-γ arrives as a *separate* model namespace
(`physics/compressible/real/`, or an `equilibrium` nozzle model) that reuses the
numerics but is validated on its own terms.

**ADR-15 — Fundamental nozzle gas dynamics and rocket nozzle design are
different layers.**
*Alternatives:* one nozzle module that also computes thrust and Cf.
*Reason:* task §116. Quasi-1D area/Mach/shock behaviour is gas dynamics and
belongs in `physics`; thrust, Cf, c*, Isp, contour generation, divergence and
boundary-layer corrections are device design and belong in
`engineering/nozzle/`.
*Consequence:* `engineering.nozzle` imports `physics.compressible.nozzle` and
never restates a relation.

**ADR-16 — Solver diagnostics reuse the existing `problems` record shape.**
*Alternatives:* a parallel diagnostics channel in the UI.
*Reason:* `EngineModel.problems` already carries
`{problemId, severity, message, targetKind, targetId}`, and the Problems panel
already focuses a component when a row is clicked. Matching that shape means the
first engine solver needs **no** QML change to report a warning.
*Consequence:* `application/adapters` maps `Diagnostic` → that record.
Severities map onto the existing `info | warning`; a third `error` tone is
recorded in `07` §9 as a future UI requirement, not a change request — until
then an error renders with the warning treatment.

---

## 13. Open questions

Genuine, and none of them blocks Phase 4.

1. **Sweep transport to QML.** A 2000-point series crossing the QML boundary as
   a `QVariantList` of floats is measurably slower than a buffer or a custom
   `QQuickItem` reading a NumPy array. The existing plots (`MockLineSeries`,
   `MockScientificPlot`) consume plain JS arrays. *Proposal:* start with lists,
   measure at 2000 points, and optimise only if a frame budget is actually
   missed. Decide during Phase 4 UI integration, not now.
2. **Rayleigh inverse scope.** Which inverse pairs earn a place in v1 is argued
   in `03` §9.5; the recommendation there is one inverse (T₀ ratio → M) with the
   rest marked FUTURE. Worth a second opinion from whoever teaches with it.
3. **Nozzle geometry supplied by the UI.** The frozen Nozzle Lab page exposes an
   area ratio and a hand-authored contour, not an arbitrary A(x). The v1 solver
   contract accepts both (`03` §10.2). Whether the page eventually gains an A(x)
   import is a UI question for a later phase.
