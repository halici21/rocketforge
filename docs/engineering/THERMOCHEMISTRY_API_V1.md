# Thermochemistry API v1.0 — FROZEN

**Frozen by Phase 5G on the integrated propulsion-analysis acceptance.**

| | |
| --- | --- |
| Contract | THERMOCHEMISTRY API |
| Version | 1.0 |
| Scope | `rocketforge.physics.thermochemistry` — the provider-independent domain: the chamber state record, the provider protocol, composition and species semantics, propellant records, requests, provenance, validation and tolerances. |
| Files | 13 |
| Manifest | `tests/acceptance/freeze/phase_5g/freeze_thermochemistry_api_v1.json` |
| Digest | `aa7857573f3e6fb04f77e56aed3cd2c55f1ede047cd80bcc8b04d586fb90f184` |
| Algorithm | `rocketforge-freeze-manifest/2` |

The digest is reproducible without this project's code: sort the relative
POSIX paths, SHA-256 each file's canonical text (its bytes with every CRLF
replaced by LF, nothing else changed), write one
`"<hex><two spaces><path>\n"` line per file, encode as UTF-8, and take the
SHA-256 of those bytes. `tests/acceptance/freeze/phase_5g/freeze_thermochemistry_api_v1.sha256` is
that text, and `sha256sum -c` checks it in a fresh clone, which holds the
canonical LF text.

The digest protects the source text, not a working copy's line endings. The
contract was frozen under algorithm 1, which hashed raw bytes, at digest
`44312c23c71cfd52…`; those bytes carried a Windows working copy's CRLF line
endings, so no fresh clone could reproduce it. Algorithm 2 records the same
content again, every file proven identical to its committed blob
(`tests/acceptance/freeze/MIGRATION_V1_TO_V2.json`). The contract did not
change.

## What freezing means here

The **public surface** of this contract is its packages' `__all__`. Submodules
are reachable, as they are in any Python package, but they are implementation:
depending on one is depending on something nobody promised.

Changes after this point:

* **Additive** — a new function, a new enum member, a new optional field with a
  default — may be made within v1, and the manifest is regenerated.
* **Breaking** — a removed or renamed symbol, a reordered dataclass field, a
  changed unit, a changed default, or a changed scientific meaning — requires
  an explicit version bump and a re-run of the validation that supports it.

A defect fix that changes a number is a scientific change, not a cosmetic one:
it requires the validation evidence to be regenerated and the change recorded,
even when no signature moves.

---

`rocketforge.physics.thermochemistry`

> **This API is NOT frozen.** It is a Phase 5B surface, expected to change when
> the first provider adapter is written in Phase 5C. Compare
> `COMPRESSIBLE_FLOW_API_V1.md`, which *is* frozen and carries a manifest
> digest. This document has neither, deliberately.

Phase 5B builds the domain language through which every future thermochemistry
provider talks to RocketForge. It **solves no chemistry** and computes **no
performance**.

---

## 1. Units, without exception

| Quantity | Unit |
| --- | --- |
| temperature | K |
| pressure | Pa |
| density | kg/m³ |
| **molar mass** | **kg/mol** |
| specific gas constant | J/(kg·K) |
| cp, cv | J/(kg·K) |
| specific enthalpy | J/kg |
| molar enthalpy (on `Species`, `ThermoPolynomial`) | J/mol |
| specific entropy | J/(kg·K) |
| velocity, speed of sound | m/s |
| mass flow | kg/s |
| mixture ratio, fractions, area ratio, γ | dimensionless |

Every state property is **specific** (per kilogram) except molar mass itself.
There is no field named `enthalpy` with an unstated basis.

**Molar mass is kg/mol.** Both candidate providers report kg/kmol; the factor of
1000 is applied once, visibly, in the adapter. `Species` refuses a molar mass
outside `[1e-6, 1.0]` kg/mol, which catches the kg/kmol mistake by three orders
of magnitude.

**Universal gas constant:** `rocketforge.core.constants.UNIVERSAL_GAS_CONSTANT`
= 8.31446261815324 J/(mol·K), CODATA, exact since the 2019 SI redefinition. It
is reused, not redefined, and **not** adjusted to match a provider (§4).

---

## 2. Canonical conventions

| Convention | Value |
| --- | --- |
| Stored composition basis | **mole fraction** |
| Basis on any fraction set | **always explicit**, never inferred |
| Mixture ratio | **O/F = oxidiser mass ÷ fuel mass**, always |
| Enthalpy datum | elements in their reference states at **298.15 K, 1 bar** |
| Phase | part of species **identity**, never a flag |
| Unknown phase | `None`, and never read as `GAS` |
| Unknown condensed fraction | `None`, and never read as zero |

---

## 3. Public surface

70 exported names. `from rocketforge.physics.thermochemistry import ...`

### 3.1 Enumerations — `types.py`

| Name | Members | Notes |
| --- | --- | --- |
| `Phase` | GAS, LIQUID, SOLID, SUPERCRITICAL | `.is_condensed` covers LIQUID and SOLID only |
| `CompositionBasis` | MOLE_FRACTION, MASS_FRACTION | mole is canonical |
| `PropellantRole` | FUEL, OXIDISER, MONOPROPELLANT | Phase 5A spelling |
| `MixtureRatioBasis` | MASS, MOLAR | mass is canonical |
| `ChemistryMode` | EQUILIBRIUM | one member, deliberately |
| `ExpansionMode` | EQUILIBRIUM, FROZEN, FROZEN_AT_THROAT | `.freeze_location` derives the station |
| `FreezeLocation` | CHAMBER, THROAT | explicit, never a boolean |
| `EquilibriumConstraint` | HP, SP | only the two Phase 5A uses |
| `GammaStrategy` | CHAMBER, THROAT, EXIT, CHAMBER_EXIT_MEAN, EFFECTIVE_ISENTROPIC | **no default; data contract only** |

`Phase` has no `UNKNOWN` member. Where a phase may be unknown the field is
`Phase | None`, and nothing defaults it to `GAS`.

### 3.2 Species — `species.py`

```python
ElementalComposition.from_mapping({"C": 1.0, "H": 4.0})
Species(name, phase, molar_mass, formula=..., enthalpy_of_formation=None,
        thermo=None, reference_temperature=298.15, display_name=None,
        is_surrogate=False, source="")
ThermoPolynomial(form, temperature_ranges, coefficients)   # NASA7 / NASA9
```

* `Species.canonical_id` → `"H2O:gas"`. `Species.label` → the display name.
* Atom counts are `float`: an empirical surrogate formula is fractional.
* Element symbols are unrestricted — F, Cl, metals, ionic labels all work with
  no change to the balance algorithm.
* **Molar mass is stored, never recomputed.** `formula_molar_mass(weights)`
  cross-checks it against *caller-supplied* atomic weights; this package ships
  no periodic table, because whose periodic table is exactly the question.
* A surrogate must name its `source`: two RP-1 fits are two species.
* Polynomial evaluation **refuses** temperatures outside its declared range.
  Range joins are matched in value, and slope continuity is deliberately not
  required or tested.
* Species names are **not** length-limited. NASA CEA's 15-character cap is a
  provider constraint and lives in the adapter's name mapping.

### 3.3 Composition — `composition.py`

```python
Composition.from_fractions(mapping, basis, ...)   # must sum to 1
Composition.from_weights(mapping, basis, ...)     # explicit normalisation
Composition.pure(name, basis=MOLE_FRACTION)
comp.to_basis(other_basis, species) -> Composition
comp.mean_molar_mass(species)        # kg/mol
comp.specific_gas_constant(species)  # J/(kg K)
comp.condensed_mass_fraction(species)
comp.elemental(species, basis) -> ElementalInventory
```

Free functions: `mole_to_mass_fractions`, `mass_to_mole_fractions`,
`mean_molar_mass`, `specific_gas_constant`, `elemental_inventory`,
`compare_elemental_inventories`.

**Sum policy**

| Input | Behaviour |
| --- | --- |
| sums to exactly 1 | accepted, `canonicalised_from_sum is None` |
| within `composition_sum_tol` (1e-9) | canonicalised to 1, **and the original sum recorded** |
| outside that | `CompositionSumError` — **never rescaled** |
| relative amounts (20/30/50) | use `from_weights`, which normalises because the caller said so |

Negative fractions are refused; `fraction_negative_tol` is 0 by default, so
nothing is clamped. Zero components and trace species are preserved — there is
no storage cutoff.

Entries are stored sorted, so equality, hashing and serialisation never depend
on insertion order.

**Naming deviation from Phase 5A:** `09` §5.1 sketched this as `Mixture` with
an implicit mole basis. It is `Composition` with an explicit `basis` field —
strictly stronger, and consistent with the ban on implicit bases elsewhere.

**Elemental inventory** carries an explicit `ElementalInventoryBasis`:
`PER_MOLE_OF_MIXTURE` or `PER_KILOGRAM_OF_MIXTURE`. Inventories on different
bases refuse to be compared. `compare_elemental_inventories` returns an
`ElementBalanceReport` with a **scale-aware** residual that cannot divide by
zero for an element absent from both sides.

### 3.4 Propellants — `propellants.py`

```python
PropellantDefinition(name, role, composition, reference_temperature,
                     reference_phase, reference_pressure=None,
                     enthalpy_of_formation=None, density_hint=None,
                     provider_names={}, is_surrogate=False, source="")
PropellantStream(propellant, temperature, pressure=None, phase=None,
                 mass_flow=None)
MixtureRatio(value, basis=MASS)
PropellantPair(oxidiser, fuel, name="", stoichiometric_of_mass=None)
PropellantPairReferenceCase(pair, source, ...)
mixture_ratio_from_streams(fuel, oxidiser) -> MixtureRatio
```

* **Definition ≠ stream.** The definition holds the *reference* condition its
  published data is stated at; the stream holds the *actual* condition. LOX at
  90.17 K versus notional LOX at 298 K is worth 74.9 K of chamber temperature.
* `density_hint` is **display-only**. A test greps the package to prove no code
  path reads it.
* `provider_names` is a generic `{provider_id: name}` mapping, replacing Phase
  5A's `cea_name` so that no public field is named after one vendor.
* `mixture_ratio_from_streams` takes fuel first and returns oxidiser-over-fuel,
  and **checks the roles**: swapped arguments raise rather than inverting.
* `MixtureRatio` refuses 0, negatives, NaN and infinity, and does not clamp
  large or small values. A molar-basis ratio refuses `.of_mass` until converted
  through `to_mass_basis(...)`, which needs data the record does not carry.
* `equivalence_ratio(stoich)` requires the stoichiometric ratio explicitly.
  There is no hidden constant.
* **`PropellantPair` stores no performance and no `optimal_of`.** Phase 5B-0
  measured c\*, Tc and Isp peaking at three different mixture ratios for
  LOX/CH₄ (2.85, 3.75, 3.30), so "optimum O/F" is undefined without an
  objective.
* `PropellantPairReferenceCase` binds every observation to its conditions, and
  each observation must state its unit. Observations live in a mapping, not as
  typed attributes, so the record cannot be mistaken for a computed result.

### 3.5 Requests — `requests.py`

```python
ChamberEquilibriumRequest(fuel, oxidiser, oxidiser_fuel_ratio,
                          chamber_pressure, chemistry_mode=EQUILIBRIUM,
                          equilibrium_constraint=HP,
                          product_species=None, trace_threshold=None)
ExpansionRequest(mode, pressure=None, area_ratio=None)
```

Requests validate on construction, so malformed input is refused **before a
provider is consulted** — Phase 5B-0 measured NASA CEA silently accepting a
negative temperature and a negative pressure.

Absent by design: total mass flow, nozzle geometry, chamber dimensions, and
every provider-specific flag (`n_frz`, `iac`, `ac_at`, `**kwargs`).

`ExpansionRequest` takes exactly one of `pressure` or `area_ratio`. An area
ratio is a dimensionless boundary condition, not geometry.

### 3.6 States — `states.py`

```python
ChamberGas(temperature, gamma, gas_constant, molar_mass, composition, ...)
GasStation(pressure, temperature, gamma, ...)
```

Phase 5A's canonical names, with Phase 5A's mandatory field sets unchanged.

| Field | Meaning |
| --- | --- |
| `ChamberGas.temperature` | **T0**, a stagnation temperature |
| `gamma` | the exponent appropriate to the mode that produced the state |
| `gamma_equilibrium` | the equilibrium isentropic exponent, when supplied |
| `gamma_frozen` | cp/cv at fixed composition, when supplied |
| `cp_equilibrium` / `cp_frozen` | likewise |
| `condensed_mass_fraction` | `None` means **unknown**, not zero |
| `request` | full input traceability |
| `provenance` | provider, database, mode |

The two-gamma split is an addition Phase 5B-0 forced: it measured γ_s = 1.1336
against a frozen cp/cv of 1.1985 on the same real state, 5.7 % apart. One field
could not carry both.

`GasStation.composition is None` **means the chamber's composition, unchanged**
(frozen flow). It is a documented convention, not missing data, and a renderer
must not show it as an em dash.

Neither record carries `c_star`, `cf`, `isp`, `thrust`, `l_star`, `throat_area`
or any chamber dimension, and an architecture test enforces it.

### 3.7 Provider contract — `protocols.py`, `provenance.py`

```python
class ThermochemistryProvider(Protocol):
    provider_id: str
    version: str
    capabilities: ProviderCapabilities
    def provenance(self) -> ThermochemistryProvenance: ...
    def solve_chamber(self, request) -> Solution[ChamberGas]: ...
```

`ProviderCapability` is a 21-member enum; `ProviderCapabilities` holds a
`frozenset` of them plus validated `pressure_range`, `mixture_ratio_range` and
`temperature_ceiling`. Capabilities are **declared, never discovered**;
`require()` raises `UnsupportedCapabilityError` naming what was missing.

The set is shaped so CEA and Cantera can both be honest: CEA declares
`LIQUID_REACTANTS`, `ROCKET_PERFORMANCE`, `AREA_RATIO_EXPANSION` and
`NATIVE_EQUILIBRIUM_GAMMA`; Cantera declares `KINETICS` and none of those.

**Two documented refinements of Phase 5A**, both from 5B-0 evidence:

1. the protocol takes a **request object**, not names plus scalars, because
   reactant temperature and phase are first-class inputs;
2. it returns **`Solution[ChamberGas]`**, not a bare value, because this
   project's own policy (`core/errors.py`) reports non-convergence rather than
   raising it — and CEA exposes exactly such a `converged` flag.

`ThermochemistryProvenance` records provider id, versions, database name,
version and SHA-256, chemistry mode, constraint, species set, reactant
conditions, options and warnings. It carries **no timestamp**, so two identical
calculations produce equal provenance.

### 3.8 Validation — `validation.py`

```python
check_composition_sum, check_composition_round_trip,
check_mean_molar_mass_paths, check_gas_constant, check_cp_cv_relation,
check_gamma_definition, check_ideal_gas, check_element_balance,
check_provenance_completeness
validate_chamber_gas(state, species=None, *, tolerances, require_provenance)
validate_gas_station(state, species=None, *, tolerances)
```

Validators **report**, never raise, and never repair. Each returns an
`IdentityCheck` with `identity`, `passed`, `residual`, `tolerance`, `left`,
`right` and `applicable`. A check that could not run is `applicable=False` and
is **never counted as a pass**. `ValidationReport.to_diagnostics()` bridges to
`rocketforge.core.result.Diagnostic` with INFO / ERROR severities.

`check_gamma_definition` applies to the **frozen** gamma only. The equilibrium
exponent is a different quantity and does not equal cp/cv; applying the identity
to it would fail a correct provider.

### 3.9 Tolerances — `tolerances.py`

Five named categories, each with a justification:

| Field | Value | For |
| --- | --- | --- |
| `identity_rel_tol` | 1e-12 | RocketForge's own arithmetic |
| `state_identity_rel_tol` | 1e-9 | identities on supplied field values |
| `composition_sum_tol` | 1e-9 | how far a fraction set may miss unity |
| `element_balance_rel_tol` | 1e-8 | conservation between two inventories |
| `provider_identity_rel_tol` | **1e-5** | identities on values a provider computed |
| `fraction_negative_tol` | **0.0** | permits no clamping by default |

`provider_identity_rel_tol` exists because of a measurement: NASA CEA uses the
pre-2019 universal gas constant, so its own `cp − cv` and `p = ρRT` close on
*its* R and miss CODATA's by 5.7e-06. That is a fact about CEA, absorbed by a
named category rather than by loosening the strict one.

### 3.10 Serialization — `serialization.py`

`to_jsonable(value)` encodes every public record into JSON-safe primitives.
Encoding only; the backend has no DTO decoding framework yet.

* floats at full precision — display rounding belongs to the interface;
* negative zero normalised, genuine negatives untouched;
* NaN and infinity **refused**;
* `None` encodes as `null`, never replaced by a default;
* sets emitted sorted, so encoding is deterministic;
* an unknown type raises rather than falling back on `repr()`.

### 3.11 Errors — `errors.py`

`ThermochemistryError` derives from `RocketForgeError`. Subclasses:
`SpeciesError`, `UnknownSpeciesError`, `ElementalCompositionError`,
`CompositionError`, `CompositionBasisError`, `CompositionSumError`,
`PropellantError`, `PropellantRoleError`, `MixtureRatioError`,
`StateConsistencyError`, and the provider branch `ProviderError`,
`ProviderUnavailableError`, `ProviderDomainError`,
`UnsupportedCapabilityError`.

Three outcomes are never conflated:

| Outcome | Mechanism |
| --- | --- |
| malformed input | `InputError` subclass, **raised**, before any provider |
| no solution / not converged | a `Solution` whose status says so, **not** an exception |
| provider failure | `ProviderError` subclass, **raised** |

`ProviderUnavailableError` covers `ValueError` as well as `ImportError`: NASA
CEA loads its thermodynamic database at **import** time, so a missing data file
surfaces during import.

---

## 4. Deliberate exclusions

Not implemented, and not by oversight:

| Excluded | Belongs to |
| --- | --- |
| chemical equilibrium solver | a provider (ADR-19) |
| NASA CEA adapter, Cantera adapter | Phase 5C, `providers.*` |
| kinetics, reaction mechanisms | future, Cantera path (ADR-29) |
| transport properties, fluid properties | `physics.fluids`, `providers.*` |
| c\*, Cf, Isp, thrust | `engineering.nozzle` (ADR-15) |
| chamber geometry, L\*, sizing | `engineering.chamber` |
| γ reduction to a single-gamma `PerfectGas` | `engineering.chamber` (`12` §8) |
| trade-study engine, Pareto scoring | `engine.studies` |
| propellant catalogue | a later reference-data task |
| any UI | later |

The `GammaStrategy` enum is present as a **data contract**; no reduction is
implemented and none may be selected implicitly.

---

## 5. Dependencies

Production dependencies added by this package: **none**. It imports the standard
library and `rocketforge.core`, and not even NumPy — composition algebra over a
handful of species is lighter as plain Python.

---

## 6. Status and next steps

Provisional. Phase 5C writes the first provider adapter (NASA CEA v3, per
ADR-31) against this surface. The contract-fitness tests in
`tests/physics/thermochemistry/test_contract_fitness.py` already map **real
recorded CEA and Cantera output** into these records, so the adapter has a
worked example and the surface has evidence behind it rather than a hope.

An API freeze, if one is wanted, belongs after that adapter exists and has
exercised the contract in anger.
