# 09 — Thermochemistry Data Model and API Contracts

**Specification only. Every code block below is a contract to be implemented in
Phase 5B, not implementation.** Bodies are `...` deliberately, exactly as `02`
did for the compressible layer.

Conventions, inherited from `02` without change: SI units throughout, radians
for angles, frozen slotted dataclasses, mandatory fields required, derived
fields as properties, unknown fields `None` and never a guessed number.

Two conventions are added by this layer and are absolute:

* **Amount of substance is moles; mixture composition is stored as mole
  fractions.** Mass fractions are a derived view (§5.3).
* **Every enthalpy in this layer sits on one datum:** elements in their
  reference state at 298.15 K, 1 bar. See §3.4.

---

## 1. The types, at a glance

| Type | Answers | Mandatory | Never carries |
| --- | --- | --- | --- |
| `Species` | what is this chemical substance | `name`, `formula`, `molar_mass` | anything about a flow |
| `ElementalComposition` | which atoms, how many | element→count map | phase, state |
| `PropellantDefinition` | what can be burned | `name`, `species`, `role` | flow rate, pressure |
| `PropellantBlend` | a mixture used as one propellant | components, fractions, basis | flow rate |
| `PropellantStream` | how much is flowing, in what condition | `propellant`, `mass_flow`, `temperature`, `phase` | mixture ratio |
| `MixtureRatio` | the O/F number and what it means | `value`, `basis` | propellant identity |
| `Mixture` | composition of a reacting or product mixture | `mole_fractions` | pressure, temperature |
| `ChamberGas` | the equilibrium product gas (Phase 3) | `temperature`, `gamma`, `gas_constant`, `molar_mass`, `composition` | chamber dimensions |
| `GasStation` | a thermochemical state at an expansion station | `pressure`, `temperature`, `gamma` | nozzle geometry |
| `ThermochemistryProvenance` | who computed it and how | `provider_name`, `provider_version`, `mode` | display formatting |

`ChamberGas` and `GasStation` are Phase 3 names with Phase 3 mandatory fields
(`02` §1.5, `01` §5). They are reproduced here with their optional fields filled
in; the mandatory sets are **not** altered.

---

## 2. `Species`

### 2.1 The contract

```python
@dataclass(frozen=True, slots=True)
class Species:
    """One chemical species and the thermodynamic data needed to burn it."""

    name: str                         # "H2O", "CO2", "Al2O3(L)" - the database key
    formula: ElementalComposition     # atoms per mole of species
    molar_mass: float                 # [kg/mol], > 0
    phase: Phase                      # GAS, LIQUID, SOLID
    enthalpy_of_formation: float      # [J/mol] at 298.15 K, standard state
    thermo: ThermoPolynomial | None = None   # cp/h/s vs T; None = provider-supplied
    reference_temperature: float = 298.15    # [K]
    source: str = ""                  # "NASA Glenn 2002", "Burcat 2005", ...
```

### 2.2 Design notes, each with a reason

**`molar_mass` is stored, not derived from `formula`.** Deriving it would bind
every species to one atomic-weight table, and published thermodynamic data sets
carry their own — CEA's Glenn coefficients were fitted with the atomic weights
of their day. A species is trusted to state its own molar mass, and `13` §4
cross-checks it against the formula to a stated tolerance instead of silently
overriding either.

**Phase is part of identity, not a flag.** `H2O` and `H2O(L)` are two `Species`
with different formation enthalpies. Condensed products are the reason (`11` §7);
folding them into one object with a phase switch is how the latent heat gets
lost.

**`thermo` is optional.** When a provider owns the thermodynamic data — Cantera
holds its own NASA polynomials — RocketForge does not duplicate it. The field
exists for the in-tree species set used by verification (`13` §3), so an oracle
can be built without any external library installed.

### 2.3 `ThermoPolynomial`

```python
@dataclass(frozen=True, slots=True)
class ThermoPolynomial:
    """NASA 7- or 9-term polynomial fit, with its validity range."""

    form: PolynomialForm              # NASA7 or NASA9
    temperature_ranges: tuple[tuple[float, float], ...]   # [K], contiguous, ascending
    coefficients: tuple[tuple[float, ...], ...]           # one tuple per range

    def cp_molar(self, temperature: float) -> float: ...  # [J/(mol K)]
    def enthalpy_molar(self, temperature: float) -> float: ...   # [J/mol], abs datum
    def entropy_molar(self, temperature: float, pressure: float) -> float: ...
```

**Out of range is refused, never extrapolated.** A NASA fit is a
least-squares approximation valid over a stated band; evaluated 500 K past its
top range it can return a negative cp. `cp_molar(6000.0)` on a fit that stops at
5000 K raises `ProviderDomainError`. This is the same rule the compressible
module applies to ν beyond ν_max, and it exists for the same reason: a number
that is outside the model's domain is not a number the model may return.

**Range joins are continuous but not smooth.** NASA fits are matched in value at
the join and generally *not* in slope. `13` §4 tests continuity at the join to
a stated tolerance and explicitly does **not** test derivative continuity,
because demanding it would be testing a property the data does not have.

### 2.4 `SpeciesDatabase`

```python
class SpeciesDatabase(Protocol):
    """A named, versioned collection of Species."""

    name: str
    version: str

    def get(self, name: str) -> Species: ...          # raises SpeciesUnknownError
    def has(self, name: str) -> bool: ...
    def names(self) -> tuple[str, ...]: ...
```

A protocol, not a dict, so that Cantera's mechanism and the in-tree set are
interchangeable, and so a species set is always *named and versioned* in
provenance. Two databases disagreeing about `Al2O3(L)` must be distinguishable
after the fact.

---

## 3. Elements, atoms and the energy datum

### 3.1 `ElementalComposition`

```python
@dataclass(frozen=True, slots=True)
class ElementalComposition:
    """Atoms per mole of a species or per unit of a mixture."""

    atoms: Mapping[str, float]        # {"C": 1.0, "H": 4.0}, counts >= 0

    def __add__(self, other: ElementalComposition) -> ElementalComposition: ...
    def scaled(self, factor: float) -> ElementalComposition: ...
```

Counts are `float`, not `int`, because a *mixture's* elemental content per
kilogram is not integral, and because a blend such as RP-1 is defined by an
empirical formula with fractional subscripts.

### 3.2 Element conservation is the layer's one hard invariant

Chemistry rearranges atoms; it never creates them. Every equilibrium result
must satisfy, per element:

```
    sum over products of (moles_i * atoms_of_element_in_i)
        == sum over reactants of (moles_j * atoms_of_element_in_j)
```

This is the single most valuable test available to this layer, because it is
**provider-independent, propellant-independent and reference-free**: it needs no
published table and no oracle, and it catches the largest class of real defects
— a mis-parsed formula, a dropped species, a mixture-ratio inversion, a units
slip in the mass basis. `13` §5 makes it a universal property test over every
case the suite runs, and it is the compressible suite's cross-module identity
tests in a new domain.

Mass conservation follows from element conservation plus molar masses, and is
tested alongside it. Notably, mass conservation is what settled the Phase 3
§10.6 nozzle erratum; the same instrument works here.

### 3.3 `Phase`

```python
class Phase(Enum):
    GAS = "gas"
    LIQUID = "liquid"
    SOLID = "solid"
    SUPERCRITICAL = "supercritical"
```

`SUPERCRITICAL` exists because it is a real and common *reactant* condition —
LOX above 5.04 MPa in a regeneratively cooled feed system — and stating it is
better than misfiling it as a liquid. For product species only `GAS`, `LIQUID`
and `SOLID` occur.

### 3.4 The energy datum, stated once

> **All enthalpies in `physics.thermochemistry` are absolute, referenced to the
> elements in their reference states at 298.15 K and 1 bar.**

Consequences that Phase 5B must honour:

* `Species.enthalpy_of_formation` is on this datum by definition.
* `ThermoPolynomial.enthalpy_molar(T)` returns **formation plus sensible**, not
  sensible alone. A NASA polynomial already does this; the contract records it
  so nobody "fixes" it later.
* A `FluidState.specific_enthalpy` from `physics.fluids` or CoolProp is on a
  *different, arbitrary* datum and **must never be added to a value from this
  layer**. Where a reactant's enthalpy at injection temperature is needed, it is
  computed here, from this layer's data (§4.4).
* A reactant enthalpy handed in by a caller must arrive with its datum declared;
  if it cannot be, it is refused.

This paragraph exists because mixing enthalpy datums produces a flame
temperature that is wrong by hundreds of kelvin while looking entirely
plausible, and no downstream test would catch it. `13` §5 adds a datum-sanity
check: the computed heat of a known reaction against its published value.

---

## 4. Propellants

### 4.1 `PropellantRole`

```python
class PropellantRole(Enum):
    FUEL = "fuel"
    OXIDISER = "oxidiser"
    MONOPROPELLANT = "monopropellant"
```

`MONOPROPELLANT` is in the enum from the start because hydrazine and hydrogen
peroxide are the cases where "O/F" is undefined, and a type that cannot express
them invites a fake mixture ratio to be invented. §6.5 states what happens.

### 4.2 `PropellantDefinition`

```python
@dataclass(frozen=True, slots=True)
class PropellantDefinition:
    """A substance usable as a reactant, with its reference condition."""

    name: str                          # "LOX", "RP-1", "CH4", "N2O4", "MMH"
    role: PropellantRole
    species: tuple[SpeciesAmount, ...] # one entry for a pure substance
    reference_temperature: float       # [K] the temperature the data is stated at
    reference_phase: Phase
    enthalpy_of_formation: float | None = None  # [J/mol] at reference condition
    density_hint: float | None = None  # [kg/m3], DISPLAY AND SIZING ONLY - see below
    cea_name: str | None = None        # the name CEA knows it by, if different
    source: str = ""
```

**`density_hint` is deliberately named a hint, and is deliberately not a
property this layer computes.** Bulk density belongs to `physics.fluids`
(`08` §6). The field exists so a propellant card can show a nominal value
without a fluid provider installed, it is labelled as a nominal at its reference
condition wherever it is displayed (`15` §6), and **no calculation in
`physics.thermochemistry` may read it**. Phase 5B enforces that with a test, not
a comment: the field is unused by every code path in the layer.

**`cea_name` acknowledges reality.** CEA's reactant library uses its own names
(`RP-1`, `Jet-A(L)`, `H2(L)`). Carrying the mapping in the definition keeps the
translation in one place instead of scattered through the CEA provider.

### 4.3 `SpeciesAmount` and blends

```python
@dataclass(frozen=True, slots=True)
class SpeciesAmount:
    species: str                       # key into a SpeciesDatabase
    amount: float                      # > 0, interpreted per `basis`
    basis: CompositionBasis
```

```python
class CompositionBasis(Enum):
    MOLE_FRACTION = "mole_fraction"
    MASS_FRACTION = "mass_fraction"
```

**The basis is stored on the data, never assumed by the reader.** This is the
same discipline that keeps Darcy and Fanning friction factors apart in the Fanno
module: the ambiguity is real, the failure is silent, so the units travel with
the number. A `SpeciesAmount` whose basis is unknown does not exist.

Blends are `PropellantDefinition`s with more than one `SpeciesAmount`:

| Blend | Convention |
| --- | --- |
| MON-3 (N₂O₄ + 3 % NO) | mass fraction — that is how the specification states it |
| Aerozine-50 (50/50 UDMH/N₂H₄) | mass fraction — likewise |
| Air as a diluent | mole fraction — likewise |
| RP-1 | **not** a blend: one pseudo-species with an empirical formula, §4.5 |

Fractions must sum to 1 within a stated tolerance, on their declared basis. A
blend mixing bases across its components is a construction error and raises.

### 4.4 Reactant temperature and phase

A propellant enters the chamber at a temperature that is generally **not** its
reference temperature: LOX at 90 K, RP-1 at 298 K, methane at 111 K, a
regeneratively heated fuel at 400 K. That difference is real energy, and at
cryogenic temperatures it is worth tens of kelvin of flame temperature.

The contract:

* `PropellantDefinition` carries the **reference** condition — the condition its
  published data is stated at.
* `PropellantStream` carries the **actual** condition — what is really flowing.
* The reactant enthalpy at the actual condition is
  `h_f(reference) + ∫cp dT (+ latent heat if the phase differs)`, computed by
  this layer on the datum of §3.4.
* **A phase change between reference and actual condition that the layer cannot
  quantify is refused, not ignored.** If a definition gives liquid data and the
  stream is gaseous with no enthalpy of vaporisation available, the request
  fails with a diagnostic naming the missing quantity. Silently reusing the
  liquid value would understate the energy by the latent heat.
* Whether the provider is *told* the reactant temperature or the reactant
  *enthalpy* is a provider-interface matter, settled in §9.3.

### 4.5 Ill-defined propellants are named as such

RP-1 is not a compound; it is a specification-controlled kerosene cut. CEA
models it as a pseudo-species with an empirical formula and a fitted heat of
formation. RocketForge does the same, and says so:

* the `Species` is explicitly a pseudo-species with a fractional formula;
* its `source` names the specification and fit it came from;
* `15` §6 requires the UI to show that provenance rather than implying a pure
  substance;
* two different RP-1 fits are two different named species, never silently
  interchanged.

The general rule: **where the substance itself is a convention, the convention
is part of the data, visible and versioned.**

---

## 5. Mixtures

### 5.1 `Mixture`

```python
@dataclass(frozen=True, slots=True)
class Mixture:
    """Composition of a reacting or product mixture. Composition only."""

    mole_fractions: Mapping[str, float]     # species name -> x_i, sums to 1
    database: str                            # which SpeciesDatabase these keys are in
    database_version: str

    @property
    def molar_mass(self) -> float: ...       # [kg/mol], sum(x_i * M_i)
    def mass_fractions(self) -> Mapping[str, float]: ...
    def elemental(self) -> ElementalComposition: ...
    def condensed_fraction(self) -> float: ...   # mass fraction in LIQUID or SOLID
```

**Mole fractions are the stored form** (§0), because equilibrium is computed in
moles, element balances are in moles, and the mean molar mass is a mole-weighted
sum. Mass fractions are derived on request. Storing both invites them to
disagree.

**A `Mixture` has no pressure and no temperature.** It is a composition. Putting
it in a state object is what `GasStation` is for. This is `02` §1.1's no-god-state
rule applied to chemistry.

**The species keys are meaningless without their database**, so the database
name and version travel inside the mixture. A `Mixture` from Cantera's
`gri30.yaml` and one from a CEA run are not interchangeable just because both
contain the string `"OH"`.

### 5.2 Truncation is declared, never silent

An equilibrium result may contain fifty species, most in trace amounts. A UI or
report will show a handful. The rule:

* the stored `Mixture` is **complete** as the provider returned it;
* any truncation for display happens above the physics boundary and is labelled
  with what was dropped and how much it accounted for (`15` §5);
* `mole_fractions` on a truncated mixture would no longer sum to 1, so a
  truncated mixture is never a `Mixture` — it is a display view.

### 5.3 Conversions

Provided as pure functions, tested against each other in both directions:

```python
def mole_to_mass_fractions(x: Mapping[str, float], molar_masses: Mapping[str, float]) -> Mapping[str, float]: ...
def mass_to_mole_fractions(y: Mapping[str, float], molar_masses: Mapping[str, float]) -> Mapping[str, float]: ...
```

Round-tripping either direction must return the input to floating-point
tolerance; `13` §5 makes that a property test across every mixture the suite
produces. This is cheap and it catches the single most common chemistry bug in
engineering software.

---

## 6. The canonical mixture ratio

### 6.1 The definition

> **O/F is the ratio of oxidiser mass flow to fuel mass flow.**
>
>     MR = m_dot_oxidiser / m_dot_fuel        [dimensionless, > 0]
>
> **Mass basis. Oxidiser over fuel. Always.**

This is the aerospace convention, it is what CEA's `o/f` means, and it is what
Phase 3 already assumed in `01` §5 (`mixture_ratio: float` alongside a fuel and
an oxidiser) and `06` §4.1. Phase 5A fixes it in one place so that no module
ever has to guess.

### 6.2 `MixtureRatio`

```python
@dataclass(frozen=True, slots=True)
class MixtureRatio:
    """An oxidiser-to-fuel ratio, with the basis it was stated on."""

    value: float                       # > 0
    basis: MixtureRatioBasis = MixtureRatioBasis.MASS

    @property
    def of_mass(self) -> float: ...    # canonical O/F by mass
    def stoichiometric_fraction(self, stoich: float) -> float: ...   # phi-related
```

```python
class MixtureRatioBasis(Enum):
    MASS = "mass"                      # canonical
    MOLAR = "molar"                    # accepted on input, converted immediately
```

A `MixtureRatio` constructed on a molar basis converts to mass on construction
and remembers that it did, so provenance can say so. Internally, only
`of_mass` is ever consumed.

### 6.3 What is *not* the mixture ratio

Three neighbouring quantities exist, are useful, and are **not** interchangeable
with O/F. Each gets its own name, and none is called `mixture_ratio`:

| Quantity | Meaning | Relation |
| --- | --- | --- |
| **equivalence ratio** φ | fuel-richness relative to stoichiometric | φ = MR_stoich / MR |
| **stoichiometric ratio** MR_stoich | O/F at complete combustion | property of the propellant pair |
| **F/O** | fuel over oxidiser | 1 / MR — appears in some literature |

The inversion trap is the reason this section exists. Rocket engines run
fuel-rich, so a typical LOX/LH₂ engine runs at MR ≈ 6 where stoichiometric is
7.94, giving φ ≈ 1.32. A code that confuses O/F with F/O gets 0.167 instead of 6
and produces a temperature that is wrong but not absurd. `13` §5 therefore
requires every mixture-ratio-taking entry point to be tested with an asymmetric
pair where the inversion is unmistakable, and requires the known
stoichiometric ratios of the reference propellant pairs to be reproduced.

### 6.4 Range

`MixtureRatio` accepts any positive finite value. It does **not** clamp to a
"sensible" band, because sweeps legitimately run from very fuel-rich to very
oxidiser-rich, and because clamping is the behaviour this project forbids
everywhere else. Providers may refuse a ratio outside their own validated range;
that refusal is a diagnostic naming the range, not a silent substitution.

Zero and infinity are not mixture ratios: `MR = 0` means no oxidiser, which is a
monopropellant or a decomposition problem, and is rejected with a diagnostic
saying so rather than being computed as a limit.

### 6.5 Monopropellants

A monopropellant has no O/F. The API expresses that by **absence**, not by a
sentinel:

```python
def equilibrium_chamber_monopropellant(
    self, propellant: str, chamber_pressure: float, *,
    reactant_temperature: float | None = None,
) -> ChamberGas: ...
```

There is no `mixture_ratio=None` overload of the bipropellant call and no
`MR = 0` convention, because both would let a monopropellant flow through code
paths that assume two streams. Phase 5B may defer implementing this method
entirely (`14` §3 puts it after the bipropellant path); what it may not do is
fake it.

---

## 7. `ChamberGas` — the Phase 3 contract, filled in

```python
@dataclass(frozen=True, slots=True)
class ChamberGas:
    """Equilibrium combustion product gas at the chamber stagnation condition."""

    # --- mandatory, exactly as 02 section 1.5 fixes them ---
    temperature: float                 # T0 [K], the equilibrium flame temperature
    gamma: float                       # [-], > 1, see the warning below
    gas_constant: float                # specific R [J/(kg K)], > 0
    molar_mass: float                  # M_bar [kg/mol], > 0
    composition: Mixture

    # --- optional, None when the provider does not supply them ---
    pressure: float | None = None      # p0 [Pa] the state was computed at
    cp: float | None = None            # [J/(kg K)]
    enthalpy: float | None = None      # [J/kg], datum of section 3.4
    entropy: float | None = None       # [J/(kg K)]
    density: float | None = None       # [kg/m3]
    speed_of_sound: float | None = None    # [m/s]
    condensed_mass_fraction: float | None = None
    provenance: ThermochemistryProvenance | None = None
```

### 7.1 Which γ this is

**`gamma` is the isentropic exponent, not necessarily cp/cv.** For a reacting
mixture these differ, and the difference is not small.

* The **frozen** γ is cp/cv at fixed composition.
* The **equilibrium** isentropic exponent is
  γ_s = −(∂ln p / ∂ln v)_s , which accounts for composition shifting as the gas
  expands. CEA reports both, printing the equilibrium one as `GAMMAs`.

For a hot LOX/LH₂ chamber these can differ by several per cent, which moves
computed exit conditions by more than any tolerance in this project. So:

* `ChamberGas.gamma` **means the exponent appropriate to the mode that produced
  it**, and the mode is recorded in `provenance.mode`;
* a `ChamberGas` without provenance stating its mode is not a valid input to the
  compressible handshake (`12` §4 makes this a precondition);
* `11` §4 defines the modes, and `13` §5 tests that the two exponents are
  *distinguishable* for a case where they should differ — a test that fails if a
  provider adapter quietly reports cp/cv for both.

### 7.2 R, M̄ and the consistency invariant

```
    gas_constant == R_universal / molar_mass
```

must hold to floating-point tolerance for every `ChamberGas`, with
R_universal = 8.31446261815324 J/(mol·K) (CODATA, exact by the 2019 SI
redefinition). Storing both is redundant, and the redundancy is the point: a
provider adapter that scales one and not the other is caught immediately.
`13` §5 checks it on every state the suite produces.

The consistency check uses **this project's** universal gas constant. A provider
using an older value (CEA's tables predate the 2019 redefinition) will differ in
the eighth significant figure; the tolerance accommodates that and `13` §4
records the expected magnitude rather than pretending the two agree exactly.

---

## 8. `GasStation` — a state during expansion

```python
@dataclass(frozen=True, slots=True)
class GasStation:
    """A thermochemical state at one station of an expansion. No geometry."""

    # --- mandatory, exactly as 02 section 1.5 fixes them ---
    pressure: float                    # [Pa], > 0
    temperature: float                 # [K], > 0
    gamma: float                       # [-], > 1, section 7.1 applies

    # --- optional ---
    composition: Mixture | None = None       # None when frozen: same as chamber
    molar_mass: float | None = None
    gas_constant: float | None = None
    density: float | None = None
    enthalpy: float | None = None            # [J/kg], datum of section 3.4
    entropy: float | None = None
    speed_of_sound: float | None = None
    velocity: float | None = None            # [m/s], from the energy equation
    mach: float | None = None
    area_ratio: float | None = None          # the boundary condition, if one was set
    condensed_mass_fraction: float | None = None
    provenance: ThermochemistryProvenance | None = None
```

Three notes.

**`area_ratio` is recorded, not owned.** It is the scalar boundary condition the
station was solved at (`08` §5.3), stored so a result can say what was asked of
it. It is not geometry: there is no area, no axial position, no contour, and
`engineering.nozzle` remains the only module that knows what the nozzle looks
like.

**`velocity` and `mach` are optional and provider-supplied.** They come from the
energy equation `V = sqrt(2(h0 − h))` on this layer's enthalpy datum, which is
valid for a variable-γ expansion where the frozen module's isentropic relations
are not. They are *not* computed by calling `physics.compressible`.

**`composition is None` means frozen, and that is a documented convention** —
the composition is the chamber's, unchanged. It does not mean "unknown". `11` §5
states it; `15` §5 requires the UI to render it as the chamber composition
rather than as an em dash.

---

## 9. `ThermochemistryProvider` — the protocol

### 9.1 Phase 3's signature, preserved

`01` §5 fixed two methods. They are reproduced verbatim; nothing about them is
changed:

```python
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

### 9.2 The additions

Extension is not contradiction. Phase 5B adds:

```python
    # --- capability declaration, see 10 section 4 ---
    capabilities: ProviderCapabilities

    def supports(self, fuel: str, oxidiser: str) -> bool: ...

    # --- the primitive that expand() is built on ---
    def expand_to_pressure(
        self, chamber: ChamberGas, pressure: float, mode: ExpansionMode,
    ) -> GasStation: ...

    # --- the throat, which is a condition, not an area ---
    def throat(
        self, chamber: ChamberGas, mode: ExpansionMode,
    ) -> GasStation: ...

    # --- monopropellants, see 6.5 ---
    def equilibrium_chamber_monopropellant(
        self, propellant: str, chamber_pressure: float, *,
        reactant_temperature: float | None = None,
    ) -> ChamberGas: ...
```

`expand_to_pressure` is the primitive because an expansion is thermodynamically
determined by entropy and pressure (`11` §5); the area ratio is a *condition to
be solved for*, and solving it is what makes `expand()` the more expensive call.
Exposing the primitive means a pressure-driven analysis never pays for a root
find it does not need.

`throat` is separate because the sonic condition of an equilibrium gas is not at
the frozen module's `p/p0 = (2/(γ+1))^(γ/(γ−1))`; it is where V equals the
equilibrium speed of sound, which must be found by the provider.

### 9.3 Reactant conditions

Phase 3's `equilibrium_chamber` takes propellants by **name**, which implies a
provider-side library and a reference temperature. Real analyses need the actual
injection temperature (§4.4). Phase 5B adds it as keyword-only, preserving the
positional signature exactly:

```python
    def equilibrium_chamber(
        self, fuel: str, oxidiser: str, mixture_ratio: float,
        chamber_pressure: float, *,
        fuel_temperature: float | None = None,
        oxidiser_temperature: float | None = None,
        fuel_phase: Phase | None = None,
        oxidiser_phase: Phase | None = None,
    ) -> ChamberGas: ...
```

`None` means "the provider's reference condition for that reactant", and the
condition actually used is recorded in provenance either way — so a result never
leaves the layer without stating what temperature its reactants were at.

A stream-based convenience wrapper (`PropellantStream` in, `ChamberGas` out)
belongs in `engineering.chamber`, not in the protocol: it is where mass flows
live, and keeping the protocol name-based is what lets a thin CEA adapter
implement it.

### 9.4 Return type and the `Solution` question

Phase 3's protocol returns bare `ChamberGas` / `GasStation` and specifies an
**exception**-based error model (`01` §5: `ProviderUnavailableError`,
`ProviderDomainError`, `ProviderFluidUnknownError`, "It never returns a
substitute value"). Phase 5B keeps that at the provider boundary.

The `Solution[T]` wrapper — with `Status`, `Diagnostic` and provenance — appears
one layer up, in `engineering.chamber`, which translates provider exceptions
into diagnostics. `01` §5 already says callers do exactly this.

The reasons this split is right, rather than merely inherited:

* a provider adapter stays thin, which is what makes a third-party library easy
  to wrap correctly;
* the rich result type stays where the *engineering* question is being asked,
  which is where a partial answer with diagnostics is meaningful;
* it matches `FluidPropertyProvider`, so the two provider families behave alike.

---

## 10. `PropellantStream`

```python
@dataclass(frozen=True, slots=True)
class PropellantStream:
    """A flowing quantity of one propellant in a definite condition."""

    propellant: PropellantDefinition
    mass_flow: float                   # [kg/s], > 0
    temperature: float                 # [K], > 0 - the ACTUAL condition
    pressure: float | None = None      # [Pa], for phase determination
    phase: Phase | None = None         # None = determine from p, T if possible

    @property
    def molar_flow(self) -> float: ...       # [mol/s]
    def specific_enthalpy(self) -> float: ...  # [J/kg] on section 3.4's datum
```

**Mass flow, not volumetric.** Volume needs a density, density is
`physics.fluids`' answer, and this layer does not import it.

**One propellant per stream.** Two streams make a mixture ratio; that is the
composition rule (`02` §1.1) applied here. A stream does not know about the
other side of the injector.

`MixtureRatio` is derived from a pair of streams by a free function, so the
canonical direction is written exactly once:

```python
def mixture_ratio_from_streams(
    fuel: PropellantStream, oxidiser: PropellantStream
) -> MixtureRatio: ...
```

Its parameters are named and its argument order is fuel-first while its result
is oxidiser-over-fuel — deliberately, so that a caller who swaps the arguments
gets a type error on the `role` check rather than a silently inverted ratio.
The function validates `fuel.propellant.role is FUEL` and
`oxidiser.propellant.role is OXIDISER` and raises otherwise.

---

## 11. Provenance

```python
@dataclass(frozen=True, slots=True)
class ThermochemistryProvenance:
    """Who computed this state, how, and against what data."""

    provider_name: str                 # "RocketCEA", "Cantera", "tabulated:LOX-CH4-v1"
    provider_version: str
    mode: str                          # ChemistryMode / ExpansionMode value
    species_database: str = ""
    species_database_version: str = ""
    reactant_conditions: Mapping[str, float] = ...   # {"fuel_T": 111.0, ...}
    options: Mapping[str, str] = ...   # provider-specific knobs actually used
    warnings: tuple[str, ...] = ()     # e.g. "condensed species present"
```

Provenance is **mandatory in practice**: `12` §4 makes a `ChamberGas` without it
an invalid input to the compressible handshake, because the handshake's
correctness depends on knowing which γ it holds (§7.1). The field is typed
`| None` only so an intermediate value can be constructed before it is filled.

This is the same discipline as the compressible module's relation identifiers
(ADR-12, ADR-13): a number without a statement of where it came from is not a
result this project ships.

---

## 12. What this document does not decide

Deferred deliberately, with the deciding document named:

| Question | Decided in |
| --- | --- |
| Which provider is default, and what happens when it is absent | `10` §5, §7 |
| What equilibrium, frozen and frozen-at-throat mean precisely | `11` |
| What happens when condensed species appear | `11` §7 |
| How `ChamberGas` becomes a `PerfectGas` | `12` §5 |
| Tolerances for every check named above | `13` §4 |
| Which propellant pairs ship in v1 | `PHASE_5A_SUMMARY.md`, OQ-1 |
