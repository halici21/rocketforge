# Solid Propellant Thermochemistry R1 — architecture

Phase D. Written before production code, as section 61 requires.

**Scope, after the Phase-A gate decision:** formulation → NASA CEA HP chamber
equilibrium → chamber thermochemistry → gas and condensed products →
provenance. Solid reference rocket performance is **deferred to R1.1** and is
not implemented, exposed, or stubbed here.

## The constraint that shapes everything: two enforced freeze manifests

`tests/acceptance/test_propulsion_freeze.py` enforces
`freeze_thermochemistry_api_v1` (13 files) and `freeze_cea_provider_v1_1`
(12 files). Both currently match with zero mismatches. **Any byte changed in
those 25 files fails the suite** — including
`rocketforge/physics/thermochemistry/__init__.py` and
`rocketforge/providers/cea/{__init__,mapping,provider,species}.py`.

The freeze is checked **two independent ways**, and the second one is easy to
miss:

1. `test_the_recorded_digest_is_independently_reproducible` walks the
   manifest's own file list and re-hashes each path. It never enumerates a
   directory.
2. `test_each_manifest_covers_its_whole_package` does the opposite: it
   `rglob`s each package root and asserts the manifest's file set **equals**
   what is on disk. `freeze_thermochemistry_api_v1` is pinned to
   `rocketforge/physics/thermochemistry`, `freeze_cea_provider_v1_1` to
   `rocketforge/providers/cea`.

So the boundary is stricter than the first test alone implies:

| Action | Allowed? |
| --- | --- |
| Modify any of the 25 listed files | **No** — breaks the recorded digest |
| Add a new module *inside* either package root | **No** — breaks package coverage |
| Re-export new names from a frozen `__init__.py` | **No** |
| Add a module in a *sibling* package | **Yes** |
| Import frozen symbols from anywhere | **Yes** — reading changes no bytes |

### How this was established

An earlier reading of this constraint consulted only the first test and
concluded that new modules inside the frozen packages were permitted. Acting on
that, `solid.py` was written into `rocketforge/physics/thermochemistry/`. The
suite rejected it:

```
test_each_manifest_covers_its_whole_package
AssertionError: {'missing_from_manifest':
    ['rocketforge/physics/thermochemistry/solid.py'], 'not_on_disk': []}
```

Only the thermochemistry violation is named there, because the assertion fires
on the first failing manifest; the two modules added under
`rocketforge/providers/cea/` were the same violation, unreported only because
the test had already stopped. Both were moved out.

The resulting layout puts each new module in a sibling package:

| Concern | Package |
| --- | --- |
| Solid domain model | `rocketforge/physics/solid_propellant/` |
| Solid CEA provider path | `rocketforge/providers/cea_solid/` |

This is better than the submodule layout it replaced, not merely legal. Each
package gets a real `__init__.py` that re-exports its public names, so callers
write `from rocketforge.physics.solid_propellant import SolidFormulation`
rather than reaching into a submodule — the awkwardness the earlier design had
accepted as a cost of the freeze turned out not to be necessary at all.

Section 36 rules that the frozen contract wins, and it does here.

## What is reusable — verified by execution, not by reading

| Symbol | Coupling | Verdict |
| --- | --- | --- |
| `mapping.condensed_mass_fraction(raw, species)` | no request at all | **Reused unmodified** |
| `mapping.CEARawChamberResult` | plain dataclass | **Reused unmodified** |
| `mapping.assigned_enthalpy_temperature` | takes a cea module and a name | **Reused unmodified** |
| `errors.translate_cea_exception` | none | **Reused unmodified** |
| `cea/units.py` conversion helpers | pure functions | **Reused unmodified** |
| `ChamberGas`, `Species`, `Composition`, `Phase` | frozen domain | **Reused unmodified** |
| `mapping.to_chamber_gas` | reads `request.chamber_pressure`, **and stores `request=request`** | **Not reusable** — see below |
| `mapping.select_product_species(request)` | reads `request.fuel` / `.oxidiser` | **Not reusable** — a formulation has neither |
| `mapping.solve_chamber_raw(input)` | calls `of_ratio_to_weights` inline; `CEAChamberInput` enforces `of_ratio > 0` (`mapping.py:116`) | **Not reusable** |

### Correcting an earlier reading of `to_chamber_gas`

An initial audit counted `request.` attribute accesses inside
`to_chamber_gas`, found exactly one (`request.chamber_pressure`), and
concluded the function was reusable by structural typing. **That conclusion
was wrong**, and the way it was wrong is worth recording.

`to_chamber_gas` also passes `request=request` straight into `ChamberGas`,
and `ChamberGas.__post_init__` (`states.py:281`) runtime-validates that field:

```
request=<duck-typed solid request> -> StateConsistencyError:
    request must be a ChamberEquilibriumRequest or None
request=None                       -> OK
```

That is executed output, not a reading of the source. The attribute-access
count missed it because the coupling is not an attribute read at all — it is
an `isinstance` check one call deeper, in a different frozen file.

`ChamberEquilibriumRequest` cannot be satisfied honestly: it requires a
`PropellantStream` with `role is FUEL`, a `PropellantStream` with
`role is OXIDISER`, and a `MixtureRatio` (`requests.py:83-112`). A solid
formulation has no fuel stream, no oxidiser stream, and no O/F. Manufacturing
them is exactly what section 10 forbids.

## Two unavoidable parallels, and how each is bounded

Because `mapping.py` is frozen and section 10 forbids fabricating a
bipropellant request, the solid path carries two small parallel pieces:

1. **The solver invocation** (~18 lines). `solve_chamber_raw` hard-codes
   `of_ratio_to_weights`; the solid path supplies `weights` directly.
2. **The raw→`ChamberGas` assembly** (~20 lines), passing `request=None`.

Neither duplicates any *logic*: every unit conversion still goes through the
frozen `cea/units.py` helpers, and `condensed_mass_fraction` is called, not
reimplemented. What is duplicated is field assembly and argument marshalling —
the irreducible remainder once the frozen entry points are unreachable.

Both are bounded by tests rather than by good intentions: an equivalence test
asserts the two solver paths return identical `CEARawChamberResult` values for
a case expressible both ways, so the parallel cannot silently drift from the
original.

### Traceability with `request=None`

Dropping the request would normally lose input traceability. It does not here,
because `ThermochemistryProvenance` already owns that job and its fields fit
the solid case natively (`provenance.py:77-78`):

- `reactant_conditions: Mapping[str, float]` — documented as "temperatures and
  any other reactant state the calculation used". It accepts any non-empty
  string key with a finite float value, so it carries each ingredient's mass
  fraction plus the initial temperature directly.
- `options: Mapping[str, str]` — carries the formulation name and its
  published reference.
- `species_set: tuple[str, ...]` — the product species actually considered.

So the solid result is fully reproducible from its own provenance. This is the
mechanism the frozen design already provided for provider-specific input state;
the solid path uses it as intended rather than working around it.

## Proposed public API

Two new modules. Nothing else in the repository changes shape.

### `rocketforge/physics/solid_propellant/` — the domain

A package with a real `__init__.py` re-exporting every name below, so callers
write `from rocketforge.physics.solid_propellant import SolidFormulation`.
The dataclasses live in `formulation.py`.

```python
@dataclass(frozen=True)
class CustomReactant:
    """A NASA-style ingredient defined by formula + assigned enthalpy."""
    formula: Mapping[str, float]      # element -> atoms per formula unit
    molecular_weight: float           # g/mol, of that formula unit
    enthalpy: float                   # assigned enthalpy, as given
    enthalpy_units: str               # "cal/mol" | "kJ/mol" | "J/mol"
    temperature: float                # K, the assigned-enthalpy temperature
    source: str                       # required: where the data comes from

@dataclass(frozen=True)
class SolidIngredient:
    name: str                         # CEA library name, or a custom label
    mass_fraction: float              # [0, 1]; zero is a real editing state
    custom: CustomReactant | None = None   # None => a CEA library species

@dataclass(frozen=True)
class SolidFormulation:
    name: str
    ingredients: tuple[SolidIngredient, ...]
    initial_temperature: float = 298.15    # K
    reference: str | None = None           # e.g. "NASA RP-1311 Example 5"
```

```python
@dataclass(frozen=True)
class SolidFormulationEquilibriumRequest:
    formulation: SolidFormulation
    chamber_pressure: float                # Pa
    product_species: tuple[str, ...] | None = None
    omit_species: tuple[str, ...] = ()
    include_ions: bool = False
```

`chamber_pressure` is named identically to the bipropellant request so the
two request objects read the same way at a call site, even though they are
unrelated types and neither is substitutable for the other.

### `rocketforge/providers/cea_solid/` — the provider path

`provider.py` holds the solve path, `formulations.py` the RP-1311 Example 5
reference case, and `__init__.py` re-exports both.

```python
def build_solid_chamber_input(request) -> SolidChamberInput
def select_solid_product_species(request) -> tuple[str, ...]
def solve_solid_chamber_raw(cea_module, chamber_input) -> CEARawChamberResult
def solve_solid_chamber(cea_module, request, *, provenance) -> ChamberGas
```

`solve_solid_chamber` is the only entry point a caller needs. Internally it
calls `select_solid_product_species`, `build_solid_chamber_input` and
`solve_solid_chamber_raw`, then assembles the `ChamberGas` with
`request=None`, calling the **frozen** `mapping.condensed_mass_fraction`
and the **frozen** `cea/units.py` converters for every field.
`errors.translate_cea_exception` wraps every CEA call.

## Fraction semantics

**Mass fractions, normalised to 1.0, never weight percent inside the API.**

- CEA's `weights` argument is a mass-fraction vector; RP-1311 Example 5 passes
  `[0.7206, 0.1858, 0.09, 0.002, 0.0016]`, which sums to exactly 1.0.
- The domain object stores fractions in [0, 1], and validation rejects a sum
  outside `1.0 ± 1e-9`. Zero is allowed: dialling an ingredient out is a real
  intermediate state in the editor, and the sum check still refuses a grain
  that does not close. No silent renormalisation: a formulation that does not
  sum to one is a user error the caller must see, not something the provider
  quietly repairs.
- Percent is a **UI-layer presentation** only. The formulation editor shows
  `Total mass = 100.000%` because that is what a propellant chemist writes; it
  divides by 100 at the boundary. The physics layer never sees a percent.
- Fractions pair positionally with the reactant list, as CEA requires.
  `SolidFormulation.ingredients` is a tuple so that ordering is part of the
  value and the two vectors cannot drift apart.

## Custom ingredient semantics

NASA RP-1311 Example 5 defines its binder as a *custom reactant*: an element
formula, a molecular weight, and an assigned enthalpy at a stated temperature.
It is not a library species, and no library species is equivalent to it.

Per section 16, R1 represents it **exactly as the official example does**:

| Field | Value from RP-1311 Example 5 |
| --- | --- |
| name | `CHOS-Binder` |
| formula | C 1.0, H 1.86955, O 0.031256, S 0.008415 |
| molecular_weight | 14.6652984484 |
| enthalpy | -2999.082 |
| enthalpy_units | `cal/mol` |
| temperature | 298.15 K |

It is **not** relabelled HTPB, PBAN, or any other real binder. The name in the
UI is the name in the source document, so a reader comparing RocketForge's
output against the published table sees the same identifiers.

`cea.Reactant` objects are **materialised inside each solve**, never cached at
module scope. The `cea` library holds process-global state, and section 38
requires case-local isolation: a stale `Reactant` reused across two solves is
exactly the class of bug the A/solid/A determinism test exists to catch.

## Result reuse

The solid path produces a `ChamberGas` — the **same type** the bipropellant
path produces. It cannot be built by the same *function*, for the reason
recorded above, but it is the same type built from the same converters.
Consequences:

- No `SolidChamberResult` type is introduced. A second result type would fork
  every downstream consumer, which is precisely what section 11 forbids.
- Temperature, molecular weight, gamma, and composition carry identical units,
  tolerances, and rounding, because every conversion goes through the same
  frozen `cea/units.py` helpers the bipropellant path uses.
- `ChamberGas.request` is `None`; the formulation lives in provenance, which
  is the field the frozen design designates for reactant input state.

The one field a solid chamber genuinely does not have is O/F. CEA itself
reports `o/f = 0.000` for Example 5 — the correct representation is the
absence of a ratio, not a fabricated one (section 10). The UI omits the row
rather than printing a zero a reader could mistake for a measured value.

## Condensed reporting

`condensed_mass_fraction(raw, species)` already computes from the returned
composition rather than CEA's `num_condensed` counter, with an ADR recording
why. R1 inherits that unchanged — which matters more for solids than for
bipropellants, because an aluminised formulation's headline condensed product,
AL2O3(L) at 0.036724 mass fraction in Example 5, is a first-class result
rather than a trace.

Reporting rules, carried over from the accepted condensed-phase semantics:

- Gas and condensed products are listed in **separate groups**, never averaged
  or flattened together.
- A condensed species keeps the phase suffix CEA reports — `AL2O3(L)` is
  liquid alumina, and dropping the `(L)` would discard the state.
- "No condensed species present" and "condensed species below the reporting
  threshold" stay distinct states, as `rf-scientific-ui-contract` requires.

## CEA reference performance — explicitly out of scope

`cea.RocketSolver` is **not called anywhere in R1**. No c\*, Cf, ceff, Isp,
equilibrium expansion, or frozen expansion is computed, stored, serialised, or
displayed for a solid formulation. Per section 7 there is also **no dormant UI**
— no disabled panel, no "Reference performance — coming soon" placeholder, and
no Solid Motor or Solid Performance navigation entry (section 21).

The boundary is preserved architecturally rather than by a stub: because the
solid path yields a standard `ChamberGas`, R1.1 can add a performance module
that consumes it without revisiting anything built here. That is the whole
point of the result-reuse decision above, and it is the honest way to leave
the door open — a working joint rather than a painted-on one.

## Compatibility strategy

| Risk | Control |
| --- | --- |
| Frozen digests break | No frozen file is edited; `test_propulsion_freeze.py` runs in the gate |
| Bipropellant numerics drift | `acceptance/solid_propellant_r1/opening_baseline.json` pins the canonical LOX/LCH4 case (Tc 3598.2854205339845 K, digest `2ae9f38f36292b4a`); re-checked after implementation |
| CEA global state leaks between cases | A/solid/A determinism test: bipropellant, solid, bipropellant — first and third must be bit-identical |
| The parallel solver path drifts from `solve_chamber_raw` | Equivalence test on a case expressible both ways |
| `cea` absent from the base `.venv` | Every CEA test carries `pytest.mark.skipif` on a live `import cea` probe, matching existing practice |

## Verification gate before any UI work (section 28)

All seven must pass:

1. The Example 5 request is constructed correctly from the published data.
2. Direct CEA reproduces the published Example 5 chamber values.
3. The RocketForge provider reproduces the direct CEA result.
4. The custom binder is handled correctly (formula, MW, assigned enthalpy).
5. Condensed species are parsed correctly, AL2O3(L) included.
6. Bipropellant A / solid / bipropellant A is deterministic.
7. The canonical bipropellant results are unchanged from the opening baseline.

## What implementation added to this design

Recorded here so the design and the code do not drift apart.

- **`SolidCase` carries ingredient identities**, not just fractions, because the
  editor adds and removes ingredients. Identities come from a catalogue; only
  the fractions come from the case.
- **The catalogue is probed, not declared.** A library species is offered only
  if the installed `thermo.lib` holds it (`library_species_available`, in the
  provider package — the application layer touches no CEA object). Custom
  reactants are offered only with a sourced definition.
- **`CustomReactant.source` is required.** A custom reactant is thermochemical
  data RocketForge did not compute; a result built on it is only as traceable
  as that string. Provenance carries the full definition and its source.
- **`SolidCase.propellant_kind`** is the one marker every consumer reads to
  tell a solid case from a bipropellant one — the result headline, the
  condition rail, the species table, and the performance refusal. A field probe
  (`hasattr(case, ...)`) was used first and broke silently when the case shape
  changed.
- **`check_condensed_count`** cross-checks the phase classification against
  CEA's own `num_condensed` on every solve, and refuses a mismatch rather than
  reporting a product in the wrong phase.
- **Assigned-enthalpy diagnostics.** Measured, not assumed: CEA returns the
  same enthalpy for the custom binder at 250, 298.15 and 320 K. A grain
  temperature that cannot reach a reactant is reported with the frozen
  provider's own diagnostic code, so the existing interface renders it.
- **A performance refusal.** `solve_performance` refuses a solid chamber before
  the reduction runs. The reduction's condensed gate is not enough: a
  non-metalised grain has no condensed mass and would otherwise publish an
  ideal-rocket result for a solid propellant.
