# Fluid Properties API v1.0 — FROZEN

**Frozen on the fluids-foundation acceptance.**

| | |
| --- | --- |
| Package | `rocketforge.physics.fluids` |
| Layer | L1, fundamental. Depends on `rocketforge.core` and nothing else in the project |
| Files | 8 |
| Digest | `306ec275df25f850…` — full value in `acceptance/fluids_foundation/freeze_manifest.json` |
| Roadmap | `06_future_module_dependency_map.md` §8 **step 1** |

---

## What it owns

The fluid-property *domain*: a fluid's identity, a state request, a state, the
phase vocabulary, the property vocabulary with its canonical SI units, the
capability model, provenance, and the provider protocol.

## What it must never own

No equation of state. No property correlation. No device equation — no line,
valve, orifice, injector, pump or cooling channel. No provider. No Qt. No
chemistry. It imports `rocketforge.core` and nothing else in the project, and a
per-module test asserts that.

---

## The four decisions worth reading

### 1. Temperature and pressure are both required

```python
FluidStateRequest(fluid=OXYGEN, temperature=95.0, pressure=300_000.0)
```

There is **no default pressure**, and none may be added. The reason is
measurable rather than stylistic: at 95 K oxygen's saturation pressure is
1.657 bar, so the same fluid at the same temperature is a **liquid at 3 bar and
a gas at 1 atm**. A package that supplied a pressure would be choosing which,
and the caller would never see the choice.

`FluidStateRequest(fluid=OXYGEN, temperature=95.0)` is a `TypeError`.

### 2. Unknown is `None`, and `None` is never GAS

`FluidPhase` has five members — `LIQUID`, `GAS`, `SUPERCRITICAL`, `SOLID`,
`TWO_PHASE` — and deliberately **no `UNKNOWN`**. That is a documented departure
from the original brief's suggested member list, and a deliberate match to the
rule `physics.thermochemistry.Phase` already applies: an enum member meaning
"unknown" is a value that silently satisfies a required field.

Where the phase may genuinely be unknown the field is `FluidPhase | None`, and
`require_phase` refuses on `None` rather than proceeding.

`TWO_PHASE` *is* a member, because a saturated state is an answer, not an
absence. Every property there has a liquid value and a vapour value, and
reporting one branch would be inventing a vapour quality nobody supplied.

### 3. An unavailable property is a reason, never a zero

Every property in the vocabulary carries a `PropertyStatus` on every state,
whether or not it has a value:

| Status | Meaning |
| --- | --- |
| `AVAILABLE` | there is a value |
| `NOT_REQUESTED` | the provider has it; this request did not ask |
| `NOT_SUPPORTED` | the provider does not declare it at all |
| `OUT_OF_RANGE` | declared, but not valid at this state |
| `PHASE_UNSUPPORTED` | declared, but not defined for the phase found |
| `TWO_PHASE_AMBIGUOUS` | on the saturation line, where it has two values |
| `PROVIDER_FAILED` | the provider raised, or returned a non-finite number |

`state.density` raises with the status in the message when it is unavailable.
`state.optional(prop)` returns `None` for a caller that genuinely handles
absence. Neither ever returns zero, and a state that tried to store a zero
density is refused at construction.

### 4. Enthalpy is only ever a difference

`specific_enthalpy` is on the provider's own datum. CoolProp's liquid oxygen is
−133 398 J/kg at the normal boiling point; NASA CEA's is −405 609 J/kg. Both
are correct and they are 272 kJ/kg apart, because a datum is a convention.

So enthalpy is consumed only as a difference between two states of the **same
fluid** from the **same provider**, where the convention cancels exactly. See
[REACTANT_ENTHALPY_COUPLING_CONTRACT.md](REACTANT_ENTHALPY_COUPLING_CONTRACT.md).

`specific_enthalpy` is also the one property excluded from the strictly-positive
check, because its zero is a convention rather than a floor.

---

## The vocabulary

| `FluidProperty` | Canonical SI unit |
| --- | --- |
| `DENSITY` | kg/m³ |
| `SPECIFIC_ENTHALPY` | J/kg |
| `SPECIFIC_HEAT_CP` | J/(kg K) |
| `DYNAMIC_VISCOSITY` | Pa s |
| `THERMAL_CONDUCTIVITY` | W/(m K) |

Five, and not an encyclopedia. Density and viscosity are what the hydraulic
components in the next roadmap step need; enthalpy and cp are what reactant
energy needs; thermal conductivity is what the thermal work after that needs.
Every additional property is another thing to validate, and an unvalidated
property inside a frozen contract is worse than an absent one.

---

## Fluid identity

```python
OXYGEN = FluidDefinition(name="OXYGEN", formula="O2", molar_mass=0.0319988, ...)
```

The domain says `OXYGEN`. CoolProp says `"Oxygen"` and would also answer to
`"O2"` and `"HEOS::Oxygen"`; NASA CEA says `"O2(L)"` and means something
different by `"O2"`. If any of those strings were the identity, changing
provider would change the substance — so the mapping lives inside the provider
and the native name appears only in provenance.

A definition carries a name, a formula, a molar mass and a source, and
**nothing else**. No density, no boiling point, no critical point: those are
properties *at a state*, and a definition that carried one would be a second
source of truth competing with the provider. A test pins the field set.

Molar mass is kg/mol. A value above 1 kg/mol is refused by name, because
`31.9988` is g/mol and would be wrong by a thousand.

---

## The provider boundary

```python
class FluidPropertyProvider(Protocol):
    provider_id: str
    @property
    def capabilities(self) -> FluidPropertyCapabilities: ...
    def provenance(self) -> FluidPropertyProvenance: ...
    def evaluate(self, request: FluidStateRequest) -> Solution[FluidState]: ...
```

`evaluate` returns a `Solution`. A state the provider has no data for is an
answer — "outside this equation of state's range" — not a bug, and it arrives
with a diagnostic naming what was missing. Malformed input still raises, and a
broken provider still raises. The same split as
`physics.thermochemistry.protocols`, deliberately: a second provider boundary
that worked differently would be a second thing to learn for no gain.

**Capabilities are declared, never discovered.** `TEMPERATURE_DEPENDENCE` and
`PRESSURE_DEPENDENCE` are separate capabilities precisely so a caller can ask,
before calling, whether the numbers it is about to get respond to state at all.
The constant-property provider declares neither, which is what stops it being
mistaken for a real cryogenic model — and the reactant coupling refuses a
provider that does not declare temperature dependence, by name.

`require_property` raises for a declared-absent property rather than falling
back. An unavailable viscosity is not 0 Pa s.

---

## Changing this contract

* **Additive** within v1: a new function, a new enum member, a new optional
  field with a default. Regenerate the manifest.
* **Breaking**: a removed or renamed symbol, a reordered dataclass field, a
  changed unit, a changed default, a changed meaning. Version bump, with the
  previous manifest kept as history.
* **A defect fix that changes a number** is a scientific change even when no
  signature moves: regenerate the evidence and record it.

The providers are versioned separately from the domain they implement, so a
provider fix does not reopen this API.

---

## Known limitations

See [PROPULSION_ANALYSIS_LIMITATIONS.md](PROPULSION_ANALYSIS_LIMITATIONS.md).
The ones belonging to this package: three fluids, five properties, no mixture
model, single-phase evaluation only, and methane viscosity not validated
against an independent source.
