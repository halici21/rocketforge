# 02 — Data Model and API Contracts

**Specification only. Every code block below is a contract to be implemented in
Phase 4, not implementation.** Bodies are `...` deliberately.

Conventions used throughout: SI units, radians for angles, `float` means
`float | np.floating` on input and `float` on scalar output, `ArrayLike` means
`float | Sequence[float] | np.ndarray`.

---

## 1. State objects

### 1.1 Design rules

* **Frozen dataclasses.** `@dataclass(frozen=True, slots=True)`. Mutation is
  `dataclasses.replace`.
* **No god state (task §18).** A state object owns one *physical concept*. A
  `FlowState` never learns about pump efficiency, chamber geometry, injector
  orifice diameter or material strength. If a field would only make sense for
  one device, it belongs to that device's result type in `engineering/`.
* **Mandatory fields are required; derived fields are computed properties;
  unknown fields are `None`.** A state never invents a number to fill a slot.
* **Composition over accumulation.** A nozzle station is a `FlowState` plus a
  station label plus an area, not a 30-field record.

### 1.2 `PerfectGas`

The only gas model in v1.

```python
@dataclass(frozen=True, slots=True)
class PerfectGas:
    """Calorically perfect gas: constant gamma, constant R."""

    gamma: float                      # ratio of specific heats [-], > 1
    gas_constant: float | None = None # specific R [J/(kg K)], > 0; None = dimensionless-only

    # derived, computed on access - not stored
    @property
    def cp(self) -> float: ...        # gamma * R / (gamma - 1)   [J/(kg K)]
    @property
    def cv(self) -> float: ...        # R / (gamma - 1)           [J/(kg K)]

    @classmethod
    def air(cls) -> "PerfectGas": ...          # gamma 1.4,  R 287.0528
    @classmethod
    def from_molar_mass(cls, gamma: float, molar_mass: float) -> "PerfectGas": ...
```

`gas_constant` is **optional by design**: the dimensionless half of the module
(task §31) needs only γ, and forcing a fabricated R on a user who asked for
p/p₀ at M = 2 would be a lie dressed as an API. Any function that needs R raises
`MissingGasConstantError` when it is `None`, naming the field.

Validation (`PerfectGas.__post_init__`): `gamma > 1 + GAMMA_MIN_MARGIN` and
`gamma <= GAMMA_MAX`; `gas_constant > 0` when given. Values and rationale in
`04` §7.

### 1.3 `FlowState`

One station of a one-dimensional flow.

```python
@dataclass(frozen=True, slots=True)
class FlowState:
    mach: float                                # [-]  MANDATORY
    gas: PerfectGas                            #      MANDATORY

    # dimensional, all-or-nothing: either the static set is known or it is None
    pressure: float | None = None              # p   [Pa]
    temperature: float | None = None           # T   [K]
    density: float | None = None               # rho [kg/m3]

    @property
    def is_dimensional(self) -> bool: ...      # pressure and temperature both present
    @property
    def speed_of_sound(self) -> float | None: ...   # sqrt(gamma R T)   [m/s]
    @property
    def velocity(self) -> float | None: ...         # M * a             [m/s]
    @property
    def stagnation(self) -> "StagnationState | None": ...
```

Why `mach` and `gas` are the only mandatory fields: Mach number plus γ fixes
every *ratio* in the module, and that is the level at which the physics is
actually defined. Pressure and temperature are the extra information needed to
turn ratios into numbers, and they travel together — a state with p but not T
cannot give density, speed of sound or velocity, so allowing it would only
produce a half-usable object. Density is stored rather than always derived so a
provider-supplied state can be represented without back-computation, but for a
perfect gas it is required to satisfy ρ = p/(RT) to within `REL_TOL`; the
constructor checks this and raises `InconsistentStateError` if not.

### 1.4 `StagnationState`

```python
@dataclass(frozen=True, slots=True)
class StagnationState:
    stagnation_pressure: float | None = None      # p0 [Pa]
    stagnation_temperature: float | None = None   # T0 [K]
    stagnation_density: float | None = None       # rho0 [kg/m3]
```

Kept separate from `FlowState` rather than folded in, because stagnation
conditions are the quantity that is *conserved or lost* across the module's
processes: constant through an isentropic passage, T₀ constant but p₀ dropping
across a shock, both changing in Rayleigh flow. Making it its own object is what
lets the nozzle solution say "p₀ is this upstream of the shock and that
downstream" without two half-filled `FlowState`s.

### 1.5 Other states (specified now, implemented later)

| Type | Owns | Layer | Mandatory | Never owns |
| --- | --- | --- | --- | --- |
| `FluidState` | single-species thermophysical state (see `01` §5) | `physics/fluids` | `pressure`, `temperature`, `density` | anything about a device |
| `ThermalState` | wall/coolant thermal condition: `temperature`, `heat_flux`, `conductance` | `physics/heat_transfer` | `temperature` | fluid composition |
| `GeometryState` | see `AreaDistribution`, §1.6 | `physics/compressible` | `x`, `area` | material, contour design intent |
| `ChamberGas` | equilibrium combustion product gas: `temperature`, `gamma`, `gas_constant`, `molar_mass`, composition | `physics/thermochemistry` | all of those | chamber dimensions |
| `GasStation` | a thermochemical state at an expansion station | `physics/thermochemistry` | `pressure`, `temperature`, `gamma` | nozzle geometry |

### 1.6 `AreaDistribution` — the nozzle geometry contract

```python
@dataclass(frozen=True, slots=True)
class AreaDistribution:
    """Quasi-1D duct area as a function of axial position. Geometry only."""

    x: np.ndarray            # [m], strictly increasing, shape (n,), n >= 3
    area: np.ndarray         # [m2], strictly positive, shape (n,)

    throat_index: int        # index of the minimum-area station
    # derived
    @property
    def throat_area(self) -> float: ...
    @property
    def exit_area(self) -> float: ...
    @property
    def inlet_area(self) -> float: ...
    @property
    def area_ratio_exit(self) -> float: ...      # exit_area / throat_area

    def area_at(self, x: ArrayLike) -> np.ndarray: ...   # monotone PCHIP interpolation

    @classmethod
    def from_area_ratios(cls, x: ArrayLike, area_ratio: ArrayLike) -> "AreaDistribution": ...
    @classmethod
    def conical(cls, throat_area: float, area_ratio: float,
                converging_ratio: float, half_angle: float,
                converging_half_angle: float, n: int = 201) -> "AreaDistribution": ...
```

Rules that make this the boundary demanded by task §61:

* The distribution is **supplied to** the compressible solver. The solver never
  generates a contour. `conical` exists only so the Nozzle Lab has something to
  analyse from an area ratio alone, and it is explicitly a *plain cone*, not a
  designed bell — a bell contour generator is `engineering/nozzle/contour.py`.
* `throat_index` is validated, not assumed: exactly one interior minimum is
  required for the C-D solver. A monotone duct is accepted by the constructor
  (it is a valid area distribution) but rejected by the C-D solver with
  `GeometryError`.
* Interpolation is **shape-preserving monotone cubic (PCHIP)**, chosen because a
  natural cubic spline overshoots near the throat and can produce a spurious
  second minimum, which would silently break the regime classifier.
* Units are metres and square metres. A dimensionless variant is expressed by
  setting `throat_area = 1.0`, which the classifier tolerates because it only
  ever uses ratios.

---

## 2. Result model

### 2.1 Why not a bare dict

A dictionary cannot be typed, cannot be documented at the field level, cannot
carry a branch identity that the caller must not ignore, and makes a typo a
silent `KeyError` at the UI boundary rather than an error at the call site. The
module returns typed objects.

### 2.2 `Solution[T]`

```python
T = TypeVar("T")

class Status(StrEnum):
    OK = "ok"                       # converged / exact, result is usable
    OK_WITH_WARNINGS = "warning"    # usable, but read the diagnostics
    NOT_CONVERGED = "not_converged" # numerical failure; value is the best iterate
    NO_SOLUTION = "no_solution"     # physically no solution exists (e.g. detached shock)

@dataclass(frozen=True, slots=True)
class Solution(Generic[T]):
    value: T | None
    status: Status
    diagnostics: tuple[Diagnostic, ...] = ()
    provenance: tuple[RelationRef, ...] = ()
    convergence: Convergence | None = None
    inputs: Mapping[str, float] | None = None   # echoed inputs, for reports

    @property
    def ok(self) -> bool: ...                   # status in {OK, OK_WITH_WARNINGS}
    def unwrap(self) -> T: ...                  # returns value, raises if not ok
```

Naming: `Solution` rather than `SolveResult` because the module also returns
non-solver results (a classification, a table of ratios) and "solve" would
overpromise; and because `Result` alone collides with the many `Result` types in
Python codebases. `unwrap()` gives the notebook user a one-liner that fails loud.

Alternatives considered: `(value, status)` tuples — untyped, positional,
unextendable; exceptions only — cannot express "usable but near-singular", which
is the most common real case; `Either`/`Maybe` — no room for warnings alongside
a good value.

### 2.3 `Diagnostic` and `Convergence`

```python
class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str            # stable, greppable: "NEAR_SONIC", "DETACHED_SHOCK", ...
    severity: Severity
    message: str         # one sentence, user-facing, no jargon beyond the domain
    field: str | None = None      # the input this concerns, if any
    detail: Mapping[str, float] | None = None

@dataclass(frozen=True, slots=True)
class Convergence:
    converged: bool
    iterations: int
    residual: float          # |f(x)| at the returned root
    tolerance: float         # the tolerance actually applied
    bracket: tuple[float, float] | None
    method: str              # "brent", "analytic", "bisection"
```

`Convergence` is `None` for closed-form results and populated for every
iterative one. A test asserts that: any function documented as iterative that
returns `convergence=None` is a bug.

### 2.4 Stable diagnostic codes (v1)

| Code | Severity | Raised by | Meaning |
| --- | --- | --- | --- |
| `NEAR_SONIC` | warning | area-Mach inverse, Fanno, Rayleigh inverses | input within the sonic tolerance of the choked state; Mach resolution is limited (`04` §4) |
| `SONIC_EXACT` | info | same | input inside the sonic tolerance; M = 1 returned exactly |
| `BRANCH_ASSUMED` | info | any branched relation called with a default branch | records which branch was returned |
| `DETACHED_SHOCK` | error | oblique shock | θ > θ_max; no attached solution exists |
| `STRONG_BRANCH_UNSTABLE` | info | oblique shock, strong branch | the strong solution is returned but is rarely realised without downstream back-pressure support |
| `THERMALLY_CHOKED` | error | Rayleigh inverse | requested heat addition exceeds that which drives the flow to M = 1 |
| `FRICTION_CHOKED` | error | Fanno inverse | requested duct length exceeds L_max |
| `EXTRAPOLATED_GAMMA` | warning | any | γ outside [1.05, 1.9], where the perfect-gas idealisation is rarely meaningful |
| `MODEL_LIMIT_SEPARATION` | warning | nozzle | overexpanded beyond roughly p_e/p_b < 0.4; real nozzles may separate, which this model does not predict (`03` §10.9) |
| `SHOCK_IN_NOZZLE` | info | nozzle | a normal shock was located inside the diverging section |
| `NOT_CHOKED` | info | nozzle, mass flow | throat is not sonic; mass flow is set by the pressure ratio, not by A* |

---

## 3. Two-tier API (ADR-07)

**Tier 1 — bare pure functions.** Algebraic, total on their documented domain,
scalar-or-array, no branch, no iteration.

```python
isentropic.temperature_ratio(mach, gas)   -> float | np.ndarray     # T/T0
normal_shock.pressure_ratio(mach1, gas)   -> float | np.ndarray     # p2/p1
prandtl_meyer.nu(mach, gas)               -> float | np.ndarray     # rad
```

They raise `DomainError` on invalid input and return the number. They are what a
notebook, a sweep and a plot call.

**Tier 2 — `Solution`-returning functions.** Anything with a branch, an
iteration, or a classification.

```python
isentropic.mach_from_area_ratio(area_ratio, gas, branch)  -> Solution[float]
oblique_shock.solve(mach1, theta, gas, branch)            -> Solution[ObliqueShockResult]
nozzle.solve(geometry, operating, gas)                    -> Solution[NozzleSolution]
```

The rule is mechanical enough to review in a pull request: *if a caller could be
wrong about which answer they got, or if the answer required iteration, it
returns a `Solution`.*

---

## 4. Branch types

Free-form strings are banned here (task §82).

```python
class FlowBranch(StrEnum):
    SUBSONIC = "subsonic"
    SUPERSONIC = "supersonic"
    BOTH = "both"          # request only; a result is never "both"

class ShockBranch(StrEnum):
    WEAK = "weak"
    STRONG = "strong"
    BOTH = "both"          # request only

class NozzleRegime(StrEnum):
    UNCHOKED_SUBSONIC = "unchoked_subsonic"
    CHOKED_SUBSONIC_EXIT = "choked_subsonic_exit"   # choked, shock-free, subsonic diverging section
    INTERNAL_NORMAL_SHOCK = "internal_normal_shock"
    SHOCK_AT_EXIT = "shock_at_exit"
    OVEREXPANDED = "overexpanded"
    IDEALLY_EXPANDED = "ideally_expanded"
    UNDEREXPANDED = "underexpanded"
```

When `BOTH` is requested the return type is a paired result
(`AreaMachSolutions`, `ObliqueShockPair`), never a list whose order the caller
has to guess.

---

## 5. Error taxonomy

```
RocketForgeError                      (base; never raised directly)
├── InputError                        caller supplied something meaningless
│   ├── DomainError                   outside a relation's physical domain
│   │   ├── SubsonicShockError        normal/oblique shock with M1 <= 1
│   │   ├── SubsonicExpansionError    Prandtl-Meyer with M < 1
│   │   └── AreaRatioError            A/A* < 1
│   ├── GasModelError
│   │   ├── InvalidGammaError         gamma <= 1 (or outside the hard limits)
│   │   └── MissingGasConstantError   dimensional call without R
│   ├── GeometryError                 non-monotone x, non-positive area, no throat
│   └── InconsistentStateError        p, T, rho supplied and mutually inconsistent
├── NumericalError
│   ├── BracketError                  no sign change in the supplied bracket
│   └── ConvergenceError              raised only by *_strict() variants
└── ProviderError                     (later layers)
    ├── ProviderUnavailableError
    ├── ProviderDomainError
    └── ProviderFluidUnknownError
```

**Policy: raise for invalid input, report for unattainable physics.**

* A caller asking for `nu(0.5)` made a programming error → `raise`.
* A caller asking for an attached oblique shock at θ = 40° with M₁ = 2 asked a
  meaningful engineering question whose answer is "no such shock" →
  `Solution(value=None, status=NO_SOLUTION, diagnostics=[DETACHED_SHOCK])`.

That line is the one thing a reviewer should check in every new relation, and it
is what keeps the UI from having to wrap every call in `try`.

**Non-convergence** returns `Status.NOT_CONVERGED` with the best iterate and a
populated `Convergence`, rather than raising, so the UI can show the near-answer
and say it did not converge. A `*_strict()` variant that raises is provided for
scripting, where failing loud is preferable.

---

## 6. Sweeps, cases and series

The Analysis UI needs comparison plots (task §73/§74) without a Python-level
loop per point.

```python
@dataclass(frozen=True, slots=True)
class Series:
    """One curve. Plain arrays - no plotting library types."""
    x: np.ndarray
    y: np.ndarray
    label: str                       # "p/p0, gamma = 1.40"
    quantity: str                    # "pressure_ratio"     - machine key
    unit: str = ""                   # "" for dimensionless, else SI symbol
    metadata: Mapping[str, float] = field(default_factory=dict)   # {"gamma": 1.4}

@dataclass(frozen=True, slots=True)
class SweepResult:
    series: tuple[Series, ...]
    independent: str                 # "mach"
    diagnostics: tuple[Diagnostic, ...] = ()
    provenance: tuple[RelationRef, ...] = ()

@dataclass(frozen=True, slots=True)
class Case:
    """A named set of inputs, reusable across modules."""
    name: str                        # "gamma = 1.30"
    gas: PerfectGas
    parameters: Mapping[str, float] = field(default_factory=dict)
```

```python
# proposed sweep API (SPECIFICATION)
def sweep_isentropic(
    mach: np.ndarray,
    cases: Sequence[Case],
    quantities: Sequence[str] = ("pressure_ratio", "temperature_ratio",
                                 "density_ratio", "area_ratio"),
) -> SweepResult: ...
```

Design notes:

* One vectorised call per (case × quantity), never per point. A 2000-point,
  4-γ, 4-quantity sweep is 16 NumPy expressions.
* `Series` is deliberately dumb: `x`, `y`, a label, a machine-readable
  `quantity`, and metadata. No colours, no axes, no Qt. The renderer decides
  presentation. This is the answer to task §72 — the physics package must not
  know that Qt Graphs exists.
* `SweepResult` carries diagnostics *for the sweep as a whole* (for example
  `NEAR_SONIC` when the grid steps across M = 1), not one per point, which would
  produce thousands of duplicates.
* Sampling helpers live in `core/numerics/sampling.py`:
  `mach_grid(lo, hi, n, cluster="sonic")` clusters points near M = 1 where every
  curve has its structure, which matters more for plot quality than raw count.

---

## 7. Immutability and serialisation

**Immutable: yes, for every state and result type (ADR-08).** Reproducibility,
thread hand-off, safe caching, and the fact that a view model may hold a result
long after the call.

**Serialisation: designed for, not implemented.** Project persistence is out of
scope, but a result that cannot be written to JSON cannot be regression-recorded
or exported, so the constraint is adopted now:

* Every field of every result type is a float, int, str, bool, enum, `None`,
  tuple of those, or NumPy array of floats.
* No lambdas, no open file handles, no live provider references (a provider is
  represented by its `name` + `version` string, never by the object).
* `core/result.py` supplies `to_jsonable(obj)` / `from_jsonable(data, cls)` with
  arrays becoming lists and enums becoming their values. Round-trip is tested.
* Every serialised record carries `schema_version` and the `model` identifier,
  so a stored study can be read back after a model change with a clear error
  rather than a silent misinterpretation.

---

## 8. Threading readiness

Not implemented in Phase 4, but the contract is fixed now (task §90):

* Every `physics` function is pure: output depends only on arguments.
* No module-level mutable state; no lazy singletons that mutate on first use.
* Results are immutable and picklable, so they can cross a thread or a process.
* The eventual `QThread`/`QRunnable` wrapper lives in `application/`, and it is
  the only place that knows a UI thread exists.

Consequence: the compressible module needs no change when background solving
arrives — which is the whole point of specifying it before writing it.

---

## 9. Equation registry

Powers `EquationLibraryPage.qml` (which today reads ten hand-written entries
from `MockData.equationEntries`) and the per-page assumption lists.

```python
@dataclass(frozen=True, slots=True)
class EquationRecord:
    identifier: str                  # "isentropic.area_ratio.v1"
    name: str                        # "Area-Mach relation"
    group: str                       # "Isentropic"  - matches the UI grouping
    latex: str                       # r"\frac{A}{A^*} = \frac{1}{M}\left[...\right]"
    html: str                        # entity-based fallback for QML Text
    description: str                 # 1-3 sentences
    variables: tuple[VariableRef, ...]
    assumptions: tuple[str, ...]
    domain: str                      # "M > 0, gamma > 1"
    source: str                      # "Anderson, Modern Compressible Flow, ch. 5"
    related: tuple[str, ...] = ()    # identifiers of related records

@dataclass(frozen=True, slots=True)
class VariableRef:
    symbol: str        # "A/A*"
    name: str          # "area ratio"
    unit: str          # "" | "Pa" | "K" | "rad"
    code_name: str     # "area_ratio"
```

* The registry is a module-level immutable mapping in
  `physics/compressible/equations.py`, built from literal records — not a
  database, not a file to parse at start-up.
* `RelationRef` (`01` §10) carries only the identifier and the short fields;
  the full record is looked up when the UI wants to display it. Results never
  embed the prose.
* The existing QML entries use HTML entities (`<i>p</i><sub>0</sub>`), so `html`
  is the field the frozen Equation Library can consume with no QML change;
  `latex` is for future export and documentation.

---

## 10. Public API catalogue

Every public function of the compressible module. Physics, domains and
algorithms are specified in `03`; this is the signature contract.

### 10.1 `physics.compressible.gas`

```python
def speed_of_sound(temperature: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
def gamma_from_cp_cv(cp: float, cv: float) -> float: ...
def gas_constant_from_molar_mass(molar_mass: float) -> float: ...
```

### 10.2 `physics.compressible.isentropic`

Forward, dimensionless (Tier 1):

```python
def temperature_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...   # T/T0
def pressure_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...      # p/p0
def density_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...       # rho/rho0
def area_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...          # A/A*
def temperature_ratio_star(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...   # T/T*
def pressure_ratio_star(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...      # p/p*
def density_ratio_star(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...       # rho/rho*
def mach_angle(mach: ArrayLike) -> float | np.ndarray: ...                           # rad, M >= 1
def ratios_from_mach(mach: float, gas: PerfectGas) -> IsentropicRatios: ...
```

Inverse (Tier 2 where iterative, Tier 1 where analytic):

```python
def mach_from_pressure_ratio(pressure_ratio: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
def mach_from_temperature_ratio(temperature_ratio: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
def mach_from_density_ratio(density_ratio: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...

def mach_from_area_ratio(
    area_ratio: float, gas: PerfectGas, branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]: ...

def mach_from_area_ratio_both(
    area_ratio: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[AreaMachSolutions]: ...

def mach_from_area_ratio_array(
    area_ratio: np.ndarray, gas: PerfectGas, branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> np.ndarray: ...     # vectorised; raises on any invalid element
```

Dimensional:

```python
def state_from_stagnation(
    mach: float, gas: PerfectGas,
    stagnation_pressure: float, stagnation_temperature: float,
) -> FlowState: ...
```

### 10.3 `physics.compressible.mass_flow`

```python
def mass_flow_parameter(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
    # mdot * sqrt(R T0) / (A p0)   [-]

def choked_mass_flow_coefficient(gas: PerfectGas) -> float: ...
    # Gamma(gamma) = sqrt(gamma) (2/(gamma+1))^((gamma+1)/(2(gamma-1)))   [-]

def mass_flow(
    mach: float, gas: PerfectGas, area: float,
    stagnation_pressure: float, stagnation_temperature: float,
) -> float: ...                                     # [kg/s]

def choked_mass_flow(
    gas: PerfectGas, throat_area: float,
    stagnation_pressure: float, stagnation_temperature: float,
) -> float: ...                                     # [kg/s]

def mass_flux(mach: float, gas: PerfectGas,
              stagnation_pressure: float, stagnation_temperature: float) -> float: ...
    # rho V   [kg/(s m2)]

def critical_pressure_ratio(gas: PerfectGas) -> float: ...      # p*/p0
def is_choked(pressure_ratio: float, gas: PerfectGas) -> bool: ...
```

### 10.4 `physics.compressible.normal_shock`

```python
def mach_downstream(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
def pressure_ratio(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...        # p2/p1
def density_ratio(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...         # rho2/rho1
def temperature_ratio(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...     # T2/T1
def stagnation_pressure_ratio(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...  # p02/p01
def entropy_change(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...        # (s2-s1)/R
def area_star_ratio(mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...       # A2*/A1* = p01/p02

def solve(mach1: float, gas: PerfectGas) -> NormalShockResult: ...
def solve_from_state(upstream: FlowState) -> NormalShockResult: ...
def mach_upstream_from_pressure_ratio(pressure_ratio: float, gas: PerfectGas) -> float: ...
```

### 10.5 `physics.compressible.oblique_shock`

```python
def theta_from_beta(beta: ArrayLike, mach1: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...
def theta_max(mach1: float, gas: PerfectGas,
              tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[ThetaMaxResult]: ...
def beta_sonic(mach1: float, gas: PerfectGas) -> Solution[float]: ...   # beta at which M2 = 1

def beta_from_theta(
    mach1: float, theta: float, gas: PerfectGas, branch: ShockBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]: ...                       # rad

def solve(
    mach1: float, theta: float, gas: PerfectGas,
    branch: ShockBranch = ShockBranch.WEAK,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[ObliqueShockResult]: ...

def solve_from_beta(mach1: float, beta: float, gas: PerfectGas) -> Solution[ObliqueShockResult]: ...

def theta_beta_curve(
    mach1: float, gas: PerfectGas, n: int = 400,
) -> Solution[ThetaBetaCurve]: ...              # data for the theta-beta-M diagram
```

### 10.6 `physics.compressible.prandtl_meyer`

```python
def nu(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...        # rad, M >= 1
def nu_max(gas: PerfectGas) -> float: ...                                  # rad
def mach_from_nu(nu_value: float, gas: PerfectGas,
                 tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[float]: ...
def mach_from_nu_array(nu_value: np.ndarray, gas: PerfectGas) -> np.ndarray: ...

def expand(mach1: float, turn_angle: float, gas: PerfectGas,
           tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[PrandtlMeyerResult]: ...
def compress(mach1: float, turn_angle: float, gas: PerfectGas,
             tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[PrandtlMeyerResult]: ...
```

### 10.7 `physics.compressible.fanno`

Friction convention is fixed in `03` §8.2: **Fanning**, parameter `4 f L*/D`.

```python
def temperature_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...            # T/T*
def pressure_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...               # p/p*
def density_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...                # rho/rho*
def stagnation_pressure_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...    # p0/p0*
def velocity_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...               # V/V*
def friction_parameter(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...           # 4 f L*/D

def state(mach: float, gas: PerfectGas) -> FannoState: ...
def mach_from_friction_parameter(
    friction_parameter: float, gas: PerfectGas, branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]: ...

def downstream_mach(
    mach1: float, duct_parameter: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[FannoDuctResult]: ...      # duct_parameter = 4 f L / D of the actual duct

def darcy_to_fanning(darcy: float) -> float: ...     # f_F = f_D / 4
def fanning_to_darcy(fanning: float) -> float: ...   # f_D = 4 f_F
```

### 10.8 `physics.compressible.rayleigh`

```python
def temperature_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...              # T/T*
def pressure_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...                 # p/p*
def density_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...                  # rho/rho*
def stagnation_temperature_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...   # T0/T0*
def stagnation_pressure_ratio(mach: ArrayLike, gas: PerfectGas) -> float | np.ndarray: ...      # p0/p0*

def state(mach: float, gas: PerfectGas) -> RayleighState: ...
def mach_from_stagnation_temperature_ratio(
    ratio: float, gas: PerfectGas, branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]: ...

def heat_addition(
    mach1: float, stagnation_temperature_ratio_12: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[RayleighDuctResult]: ...

def specific_heat_addition(
    mach1: float, mach2: float, gas: PerfectGas, stagnation_temperature_1: float,
) -> float: ...       # q = cp (T02 - T01)   [J/kg]
```

### 10.9 `physics.compressible.nozzle`

```python
@dataclass(frozen=True, slots=True)
class NozzleOperating:
    stagnation_pressure: float                     # p0 [Pa]
    back_pressure: float                           # pb [Pa]
    stagnation_temperature: float | None = None    # T0 [K]; required for T, rho, V, mdot

def critical_pressure_ratios(
    area_ratio_exit: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[CriticalPressureRatios]: ...

def classify(
    area_ratio_exit: float, pressure_ratio_back: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[NozzleRegimeResult]: ...       # pressure_ratio_back = pb/p0

def shock_area_ratio(
    area_ratio_exit: float, pressure_ratio_back: float, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[ShockLocation]: ...            # As/A* of the internal normal shock

def solve(
    geometry: AreaDistribution, operating: NozzleOperating, gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[NozzleSolution]: ...           # full distributed solution
```

---

## 11. Result dataclasses

Fields, units, and meaning. All frozen.

```python
@dataclass(frozen=True, slots=True)
class IsentropicRatios:
    mach: float
    temperature_ratio: float        # T/T0   [-]
    pressure_ratio: float           # p/p0   [-]
    density_ratio: float            # rho/rho0 [-]
    area_ratio: float | None        # A/A*   [-]; None at M = 0 (infinite)
    temperature_ratio_star: float   # T/T*   [-]
    pressure_ratio_star: float      # p/p*   [-]
    density_ratio_star: float       # rho/rho* [-]
    mach_angle: float | None        # mu [rad]; None for M < 1
    prandtl_meyer_angle: float | None   # nu [rad]; None for M < 1

@dataclass(frozen=True, slots=True)
class AreaMachSolutions:
    area_ratio: float
    subsonic: float                 # M < 1 root
    supersonic: float               # M > 1 root
    sonic: bool                     # True when the input was within the sonic tolerance

@dataclass(frozen=True, slots=True)
class NormalShockResult:
    mach1: float
    mach2: float
    pressure_ratio: float                  # p2/p1
    temperature_ratio: float               # T2/T1
    density_ratio: float                   # rho2/rho1
    stagnation_pressure_ratio: float       # p02/p01
    stagnation_temperature_ratio: float    # T02/T01 == 1.0 for this model
    entropy_change: float                  # (s2 - s1)/R   [-]
    area_star_ratio: float                 # A2*/A1*
    downstream: FlowState | None = None    # populated when the upstream state was dimensional

@dataclass(frozen=True, slots=True)
class ThetaMaxResult:
    mach1: float
    theta_max: float          # rad
    beta_at_theta_max: float  # rad
    mach_angle: float         # rad, asin(1/M1)

@dataclass(frozen=True, slots=True)
class ObliqueShockResult:
    mach1: float
    theta: float                  # rad, flow deflection
    beta: float                   # rad, wave angle
    branch: ShockBranch           # WEAK or STRONG - never BOTH
    mach_normal1: float           # M1 sin(beta)
    mach_normal2: float
    mach2: float                  # Mn2 / sin(beta - theta)
    pressure_ratio: float
    temperature_ratio: float
    density_ratio: float
    stagnation_pressure_ratio: float
    downstream_flow_angle: float  # rad, relative to the upstream direction (== theta)
    theta_max: float              # rad, the attachment limit for this M1
    downstream_supersonic: bool

@dataclass(frozen=True, slots=True)
class ObliqueShockPair:
    weak: ObliqueShockResult
    strong: ObliqueShockResult

@dataclass(frozen=True, slots=True)
class ThetaBetaCurve:
    mach1: float
    beta: np.ndarray              # rad, from the Mach angle to pi/2
    theta: np.ndarray             # rad
    theta_max: float              # rad
    beta_at_theta_max: float      # rad
    beta_sonic: float             # rad, boundary between supersonic and subsonic M2

@dataclass(frozen=True, slots=True)
class PrandtlMeyerResult:
    mach1: float
    mach2: float
    nu1: float                    # rad
    nu2: float                    # rad
    turn_angle: float             # rad, positive for expansion
    pressure_ratio: float         # p2/p1
    temperature_ratio: float      # T2/T1
    density_ratio: float          # rho2/rho1
    mach_angle1: float            # rad
    mach_angle2: float            # rad
    fan_angle: float              # rad, angular width of the centred fan

@dataclass(frozen=True, slots=True)
class FannoState:
    mach: float
    temperature_ratio: float             # T/T*
    pressure_ratio: float                # p/p*
    density_ratio: float                 # rho/rho*
    stagnation_pressure_ratio: float     # p0/p0*
    velocity_ratio: float                # V/V*
    friction_parameter: float            # 4 f_Fanning L*/D  [-]

@dataclass(frozen=True, slots=True)
class FannoDuctResult:
    upstream: FannoState
    downstream: FannoState
    duct_parameter: float          # 4 f L/D supplied
    remaining_to_choking: float    # 4 f L*/D at the downstream station
    choked: bool                   # True when the duct exactly reaches M = 1
    pressure_ratio_12: float       # p2/p1
    temperature_ratio_12: float
    stagnation_pressure_ratio_12: float

@dataclass(frozen=True, slots=True)
class RayleighState:
    mach: float
    temperature_ratio: float               # T/T*
    pressure_ratio: float                  # p/p*
    density_ratio: float                   # rho/rho*
    stagnation_temperature_ratio: float    # T0/T0*
    stagnation_pressure_ratio: float       # p0/p0*

@dataclass(frozen=True, slots=True)
class RayleighDuctResult:
    upstream: RayleighState
    downstream: RayleighState
    stagnation_temperature_ratio_12: float  # T02/T01
    pressure_ratio_12: float
    temperature_ratio_12: float
    stagnation_pressure_ratio_12: float     # always < 1 for heat addition
    thermally_choked: bool

@dataclass(frozen=True, slots=True)
class CriticalPressureRatios:
    """The three back-pressure thresholds of a C-D nozzle, as pb/p0."""
    area_ratio_exit: float
    first_critical: float       # choking onset: subsonic branch exit pressure
    second_critical: float      # normal shock standing exactly at the exit plane
    third_critical: float       # ideal expansion: supersonic branch exit pressure
    mach_exit_subsonic: float
    mach_exit_supersonic: float

@dataclass(frozen=True, slots=True)
class ShockLocation:
    area_ratio_shock: float        # As/A*  (A* of the upstream, choked throat)
    x: float | None                # [m], present when geometry was supplied
    mach_upstream: float
    mach_downstream: float
    stagnation_pressure_ratio: float   # p02/p01 across the shock
    area_star_downstream_ratio: float  # A2*/A1*

@dataclass(frozen=True, slots=True)
class NozzleRegimeResult:
    regime: NozzleRegime
    critical: CriticalPressureRatios
    pressure_ratio_back: float        # pb/p0 as supplied
    mach_exit: float
    pressure_ratio_exit: float        # pe/p0
    shock: ShockLocation | None       # only for INTERNAL_NORMAL_SHOCK / SHOCK_AT_EXIT

@dataclass(frozen=True, slots=True)
class NozzleSolution:
    regime: NozzleRegime
    critical: CriticalPressureRatios
    shock: ShockLocation | None
    choked: bool
    mass_flow: float | None            # [kg/s]; None without T0 or a dimensional area

    throat: FlowState
    exit: FlowState

    # distributed solution - all the same length, see 03 section 10.7
    x: np.ndarray                      # [m]
    area: np.ndarray                   # [m2]
    mach: np.ndarray                   # [-]
    pressure: np.ndarray               # [Pa]
    temperature: np.ndarray            # [K]
    density: np.ndarray                # [kg/m3]
    speed_of_sound: np.ndarray         # [m/s]
    velocity: np.ndarray               # [m/s]
    stagnation_pressure: np.ndarray    # [Pa]  - steps down across a shock
    stagnation_temperature: np.ndarray # [K]   - constant for this model
    shock_index: int | None            # index of the last pre-shock sample; the
                                       # shock sits between shock_index and +1,
                                       # which share the same x  (03 section 10.8)
```

---

## 12. Duplication audit

Asserted here and tested in `05` §9. Each row states what a module must
**call** rather than restate.

| Module | Must reuse | Must not restate |
| --- | --- | --- |
| `oblique_shock` | `normal_shock.*` applied to `Mn1 = M1 sin β` | any p, T, ρ, p₀ jump formula |
| `prandtl_meyer.expand` | `isentropic.pressure_ratio` etc. at M₁ and M₂ | any static-ratio formula |
| `nozzle` | `isentropic.mach_from_area_ratio`, `isentropic.*`, `normal_shock.*`, `mass_flow.*` | area-Mach inversion, shock jumps, choked flow |
| `mass_flow` | `isentropic.*` for the stagnation ratios | its own copy of `1 + (γ−1)/2 M²` |
| `fanno`, `rayleigh` | `gas`, `core.numerics.roots` | isentropic relations wholesale — their sonic reference states are *different* states (see `03` §8.1, §8.4 and §9.4) |
| `engineering.nozzle` (later) | `physics.compressible.nozzle` | quasi-1D area-Mach or shock physics |

The one deliberate non-reuse needs care, because it is *partly* a coincidence.
The Fanno and Rayleigh sonic reference states are reached by different processes
than the isentropic one, so in general their starred ratios differ — Fanno
`p/p*` and `ρ/ρ*`, and every Rayleigh ratio, are **not** the isentropic values.
But two Fanno relations do coincide exactly, for a physical reason: Fanno flow is
adiabatic at fixed mass flow, so `fanno.temperature_ratio == isentropic.temperature_ratio_star`
and `fanno.stagnation_pressure_ratio == isentropic.area_ratio`. Those two
equalities and the surrounding inequalities are set out in `03` §8.4 and are
**both** asserted by tests (`05` §9), so a future refactor can neither merge the
families wholesale nor break the genuine identities.
