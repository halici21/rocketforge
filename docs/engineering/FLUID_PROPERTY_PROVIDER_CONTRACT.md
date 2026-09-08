# Fluid-property provider contract

What a provider of `rocketforge.physics.fluids` must do, what it may refuse,
and what the two shipped implementations actually are.

`physics.fluids` declares the boundary; `rocketforge.providers.fluid_properties`
implements it. Nothing in `physics` imports a provider, and no provider imports
`application`.

---

## The protocol

```python
class FluidPropertyProvider(Protocol):
    provider_id: str
    @property
    def capabilities(self) -> FluidPropertyCapabilities: ...
    def provenance(self) -> FluidPropertyProvenance: ...
    def evaluate(self, request: FluidStateRequest) -> Solution[FluidState]: ...
```

### Raise or report

Unchanged from Phase 4A's standing policy, and the same split the
thermochemistry provider uses:

| Situation | Behaviour |
| --- | --- |
| malformed argument | **raises** |
| unmapped fluid | **raises** — a caller error, true whether or not the library is installed |
| library not installed | **raises** `FluidProviderUnavailableError` — a deployment fact, named so the interface can act on it |
| state outside the model's range | **reports** — `Solution` with `NO_SOLUTION` and a diagnostic naming the range |
| phase mismatch | **reports**, and the message says how to fix it |
| two-phase state | **reports** ambiguity, and withholds every property |

The mapping check runs **before** the library check, deliberately: telling a
caller to install a library that would not have helped is worse than useless.

### Capabilities are declared, never discovered

A caller must be able to ask before calling, so the interface can present an
honest option rather than discovering a limitation mid-calculation.

| Capability | Meaning |
| --- | --- |
| `DENSITY` … `THERMAL_CONDUCTIVITY` | one per property in the vocabulary |
| `PHASE_IDENTIFICATION` | can say which phase a state is in, not only return numbers |
| `SATURATION_STATE` | can locate the saturation boundary, and so refuse a two-phase state rather than silently returning one branch |
| `TEMPERATURE_DEPENDENCE` | properties actually change with temperature |
| `PRESSURE_DEPENDENCE` | properties actually change with pressure |

The last two exist so that a constant-property model cannot be mistaken for a
real one. The reactant-enthalpy coupling **refuses** a provider that does not
declare `TEMPERATURE_DEPENDENCE`, because such a model would return an
increment of exactly zero and be indistinguishable from a correct
reference-state result — the most dangerous failure available in that coupling.

`require_property` raises for a declared-absent property. It never returns a
default: an unavailable viscosity is not 0 Pa s.

---

## Units

Canonical SI, and **no conversion anywhere in a provider**. CoolProp's `PropsSI`
interface already returns exactly these units, so the adapter performs none —
which is the safest possible answer to the unit question, and is checked by a
mutation test that requires a ×1000 or ÷1000 slip to leave the physical band
for liquid oxygen immediately.

| Quantity | Unit |
| --- | --- |
| temperature | K |
| pressure | Pa |
| density | kg/m³ |
| specific enthalpy | J/kg |
| specific heat | J/(kg K) |
| dynamic viscosity | Pa s |
| thermal conductivity | W/(m K) |

---

## Provenance

Every state carries: provider id and label, provider version, library version,
**backend**, the provider's native name for the fluid, model notes, and any
named approximations. The backend is load-bearing — two backends of one library
are two models.

The native name lives here and nowhere else, which is what keeps
`"HEOS::Oxygen"` out of the domain.

---

## The two shipped providers

### `ConstantPropertyProvider` — in-tree, dependency-free

Purpose: prove the boundary without a library, give the tests a deterministic
fixture, and give the hydraulic components in the next roadmap step something
to run against.

**It is not a cryogenic property model.** It declares neither
`TEMPERATURE_DEPENDENCE` nor `PRESSURE_DEPENDENCE`; every state it returns
carries `CONSTANT_PROPERTY_APPROXIMATION` in its provenance and a warning
diagnostic saying the requested state did not change the numbers; and the
reactant coupling refuses it outright.

It is constructed with an explicit table, never a hidden built-in catalogue. A
**production** definition must state its source *and* the envelope its values
are claimed over — a constant that claims validity everywhere is claiming to be
an equation of state. A synthetic **test model** may declare no envelope, and
must say `is_test_model=True`.

### `CoolPropFluidProvider` — the real path

| | |
| --- | --- |
| Library | CoolProp **8.0.0**, MIT, pinned in `requirements-fluids.txt` |
| Backend | `HEOS` |
| Wheel | `cp312-abi3`, runs on CPython 3.13 |
| Fluids | `OXYGEN`, `METHANE`, `HYDROGEN` |
| Import | **lazy**, inside `_backend()`. Never at module scope |

The lazy import is asserted twice: a static test walks the module body and
fails on a top-level `import CoolProp`, and a subprocess test confirms that
importing `rocketforge.physics.fluids` leaves `CoolProp` out of `sys.modules`.

Ranges are the fluid's own `Tmin`, `Tmax` and `pmax`, read from CoolProp, and a
state outside them is refused with the range in the message.

**Saturation.** Asked for the phase at a `(T, p)` pair within 1 × 10⁻⁴ % of
`p_sat(T)`, CoolProp declines to answer, because such a pair does not determine
the state — the vapour quality does, and nobody supplied one. That band is
exactly the two-phase-ambiguous region, so it is the band the adapter uses:
`SATURATION_RELATIVE_BAND = 1e-6`, CoolProp's own tolerance rather than one of
RocketForge's choosing. Inside it the phase is reported `TWO_PHASE`, every
property is `TWO_PHASE_AMBIGUOUS`, and no value is stored.

---

## Optionality

The base environment ships **no** property library, and that is a supported
configuration rather than an error state. Without CoolProp:

* `rocketforge.physics.fluids` imports and its whole test suite passes;
* `rocketforge.providers.fluid_properties` imports, and
  `ConstantPropertyProvider` works;
* the CoolProp adapter module imports, and raises a named error only if asked
  to evaluate;
* the Fluid Properties workspace renders an unavailable state naming the
  dependency profile to install;
* the CoolProp-requiring tests skip with an explicit reason, and the
  fluid-enabled suite is a separate gate that runs them.

The official desktop build has both provider profiles installed, and the
PyInstaller spec collects each one **conditionally**, so a build environment
without either still produces a working executable.

---

## External validation

`acceptance/fluids_foundation/fluid_external_reference.json`, against NIST
Chemistry WebBook isobaric tables retrieved 2026-09-06.

**Classified honestly.** NIST's tables and CoolProp's `HEOS` backend implement
the same *reference equations of state* for these three fluids, so this is an
**independent-implementation check, not an independent-model check**. It catches
a wrong fluid, a wrong unit, a wrong state point, the wrong branch of a
saturation line and an implementation defect. It cannot catch an error in the
reference EOS itself, and no comparison against NIST could.

Tolerance boxes are half a unit in the source's last printed digit, derived
before any comparison ran.

| | |
| --- | --- |
| Validated comparisons | **42**, all inside their boxes |
| Phase agreement | every point, including the liquid/vapour transition |
| Enthalpy **differences** — the quantity the coupling transfers | O₂ 3392.5 vs 3390 J/kg; CH₄ 6924.4 vs 6930; H₂ 18096.8 vs 18096 — all inside box |
| dh/dT against cp | 2.1e-05, 9.2e-06 and 8.4e-04 relative |

### Not validated: methane viscosity

CoolProp uses the **Quiñones-Cisneros (2006)** friction-theory correlation for
methane viscosity; the NIST reference table does not. The measured 0.4–1.4 %
disagreement is therefore a **model difference between two correlations**, not
evidence about either, and no independent source using the same correlation was
available.

So methane viscosity is **not claimed as validated**. Oxygen
(Lemmon 2004) and hydrogen (Muzny 2013) match NIST's choices and do pass.
Nothing in this phase consumes viscosity; `engineering.line`, `valve` and
`orifice` will be its first consumers, and they must not be built on it until
this is resolved.
