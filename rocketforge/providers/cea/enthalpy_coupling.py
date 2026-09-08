"""Correcting an assigned-enthalpy reactant with a real sensible increment.

The limitation this closes, stated plainly: several of NASA CEA's reactant
entries -- the cryogenic liquids among them -- carry a single **assigned
enthalpy** at one reference condition instead of a temperature-dependent fit.
CEA accepts a different temperature for those and then ignores it, so liquid
oxygen requested at 95 K is solved with the enthalpy CEA assigns at 90.17 K.

The fix is *not* to hand CEA an enthalpy from a fluid library. A property
library's enthalpy zero is its own convention -- CoolProp's oxygen is
-133398 J/kg at the normal boiling point, CEA's is -405609 J/kg, and the
difference is a datum, not physics. Injecting one into the other would
silently redefine the formation enthalpy of oxygen.

What is transferable between two enthalpy conventions is a **difference**:

    h_corrected(T, p) = h_CEA,assigned(T_ref, p_ref)
                        + [ h_fluid(T, p) - h_fluid(T_ref, p_ref) ]

CEA keeps ownership of the chemical/formation reference. The fluid provider
contributes only the sensible increment, evaluated between two states of the
*same fluid* from the *same provider*, so both conventions cancel exactly.

**Where the reference state comes from.** ``T_ref`` is not guessed from a
docstring: it is what
:func:`~rocketforge.providers.cea.mapping.assigned_enthalpy_temperature`
measures, by evaluating the reactant at two temperatures and finding the answer
does not move. ``p_ref`` is 1 atm, the condition CEA's liquid reactant entries
are stated at -- each of the three is a saturated or slightly subcooled liquid
there, which is what makes the reference state a real state rather than a
label. The convention is declared here, in one place, rather than assumed at a
call site.

**Why the correction is applied to the mixture and not to each reactant.**
``Mixture.calc_property(ENTHALPY, weights, temperatures)`` returns the
mass-fraction-weighted specific enthalpy in J/kg -- verified against CEA's own
published assigned values, which it reproduces exactly: O2(L) -12979 J/mol,
CH4(L) -89233 J/mol, H2(L) -9012 J/mol. Because that combination is linear in
the mass fractions, adding the mass-weighted sum of the per-reactant increments
to the mixture enthalpy is algebraically identical to correcting each reactant
and re-mixing, and it uses CEA's own weights rather than recomputing them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.physics.fluids import (
    FluidDefinition,
    FluidPhase,
    FluidProperty,
    FluidPropertyProvider,
    FluidStateRequest,
)

from .errors import CEAMappingError

__all__ = [
    "ReactantEnthalpyPolicy",
    "ReactantFluidBinding",
    "ReactantEnthalpyCorrection",
    "CEA_REFERENCE_PRESSURE",
    "sensible_enthalpy_increment",
]

#: The pressure CEA's liquid reactant entries are stated at, Pa. One standard
#: atmosphere. Declared as a named constant because a reference state with an
#: unstated pressure is not a state, and because every consumer must use the
#: same one for the two conventions to cancel.
CEA_REFERENCE_PRESSURE = 101325.0


class ReactantEnthalpyPolicy(StrEnum):
    """How a reactant's enthalpy reaches the chamber solve.

    There is **no default anywhere in the domain**. The caller states which
    model it wants, and the choice is recorded in provenance, because the two
    policies give different chamber temperatures and a result that did not say
    which one produced it would be unreproducible.
    """

    PROVIDER_NATIVE = "provider_native"
    """Exactly what NASA CEA does on its own -- including ignoring the
    temperature of an assigned-enthalpy reactant, and including the warning
    that says so. Reproduces every accepted Phase 5 result bit for bit."""

    FLUID_SENSIBLE_CORRECTION = "fluid_sensible_correction"
    """CEA's assigned enthalpy plus a sensible increment from a validated
    fluid-property provider, for those reactants whose enthalpy CEA does not
    vary with temperature. Reactants CEA already handles as
    temperature-dependent are left alone, so nothing is counted twice."""


@dataclass(frozen=True, slots=True)
class ReactantFluidBinding:
    """Which fluid model stands behind one reactant, and at what pressure.

    Attributes:
        fluid: The canonical fluid whose properties describe this reactant.
        pressure: Pa. The **stream's own** pressure, which is a feed-system
            state and is emphatically not the chamber pressure. Required: there
            is no default, because at 95 K oxygen is a liquid at 3 bar and a
            gas at 1 atm, and a package that supplied a pressure would be
            choosing the answer.
        required_phase: The phase the correction is defined for. LIQUID for the
            cryogens, because that is what CEA's assigned entries describe.
    """

    fluid: FluidDefinition
    pressure: float
    required_phase: FluidPhase = FluidPhase.LIQUID

    def __post_init__(self) -> None:
        if not isinstance(self.fluid, FluidDefinition):
            raise CEAMappingError(
                f"binding fluid must be a FluidDefinition, got "
                f"{type(self.fluid).__name__}")
        pressure = float(self.pressure)
        if not math.isfinite(pressure) or pressure <= 0.0:
            raise CEAMappingError(
                f"the stream pressure for {self.fluid.name!r} must be finite "
                f"and above zero, got {self.pressure!r}. The correction has no "
                "default pressure: the phase, and therefore the enthalpy, "
                "depends on it, and the chamber pressure is a different state.")
        if not isinstance(self.required_phase, FluidPhase):
            raise CEAMappingError(
                f"required_phase must be a FluidPhase member, got "
                f"{self.required_phase!r}")


@dataclass(frozen=True, slots=True)
class ReactantEnthalpyCorrection:
    """The full record of one reactant's sensible correction.

    Everything needed to recompute it independently, which is the test a
    provenance record has to pass.
    """

    reactant_name: str
    fluid_name: str
    requested_temperature: float
    requested_pressure: float
    reference_temperature: float
    reference_pressure: float
    fluid_enthalpy_at_request: float
    fluid_enthalpy_at_reference: float
    delta_h: float
    provider_id: str
    provider_label: str
    library_version: str
    backend: str

    @property
    def is_zero(self) -> bool:
        """Whether this correction changes nothing, to the bit."""
        return self.delta_h == 0.0

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        return {
            "reactant": self.reactant_name,
            "fluid": self.fluid_name,
            "requested_temperature_K": self.requested_temperature,
            "requested_pressure_Pa": self.requested_pressure,
            "cea_reference_temperature_K": self.reference_temperature,
            "cea_reference_pressure_Pa": self.reference_pressure,
            "fluid_h_at_request_J_per_kg": self.fluid_enthalpy_at_request,
            "fluid_h_at_reference_J_per_kg": self.fluid_enthalpy_at_reference,
            "delta_h_sensible_J_per_kg": self.delta_h,
            "fluid_provider": self.provider_id,
            "fluid_provider_label": self.provider_label,
            "fluid_library_version": self.library_version,
            "fluid_backend": self.backend,
        }


def _fluid_enthalpy(provider: FluidPropertyProvider, fluid: FluidDefinition,
                    temperature: float, pressure: float,
                    required_phase: FluidPhase, what: str) -> tuple[float, object]:
    """One enthalpy from the fluid provider, or a refusal that says why."""
    solution = provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=float(temperature), pressure=float(pressure),
        properties=(FluidProperty.SPECIFIC_ENTHALPY,),
        required_phase=required_phase))
    if solution.value is None:
        reasons = "; ".join(d.message for d in solution.diagnostics) or "no reason given"
        raise CEAMappingError(
            f"the fluid-property provider could not evaluate {fluid.name!r} at "
            f"the {what} ({temperature} K, {pressure} Pa): {reasons}")
    state = solution.value
    return state.specific_enthalpy, state


def sensible_enthalpy_increment(
    provider: FluidPropertyProvider,
    binding: ReactantFluidBinding,
    reactant_name: str,
    requested_temperature: float,
    reference_temperature: float,
    *,
    reference_pressure: float = CEA_REFERENCE_PRESSURE,
) -> ReactantEnthalpyCorrection:
    """``h_fluid(T, p) - h_fluid(T_ref, p_ref)``, from one provider.

    Both evaluations come from the same provider and the same fluid, so both
    carry the same arbitrary enthalpy datum and it cancels in the difference.
    That cancellation is the entire reason this function returns a difference
    and never an absolute value, and a test asserts that no absolute fluid
    enthalpy reaches CEA.

    The provider must declare temperature dependence. A constant-property model
    would return a difference of exactly zero and look like a correct
    reference-state result, which is the most dangerous possible failure: it is
    refused by name instead.
    """
    capabilities = provider.capabilities
    from rocketforge.physics.fluids import FluidPropertyCapability

    if not capabilities.supports(FluidPropertyCapability.TEMPERATURE_DEPENDENCE):
        raise CEAMappingError(
            f"fluid provider {getattr(provider, 'provider_id', '?')!r} does not "
            "declare temperature dependence, so it cannot supply a sensible "
            "enthalpy increment. A constant-property model would return a "
            "difference of zero and be indistinguishable from a correct "
            "reference-state answer, which is why this is refused rather than "
            "allowed to look right.")

    at_request, request_state = _fluid_enthalpy(
        provider, binding.fluid, requested_temperature, binding.pressure,
        binding.required_phase, "requested state")
    at_reference, _ = _fluid_enthalpy(
        provider, binding.fluid, reference_temperature, reference_pressure,
        binding.required_phase, "CEA reference state")

    provenance = request_state.provenance
    return ReactantEnthalpyCorrection(
        reactant_name=str(reactant_name),
        fluid_name=binding.fluid.name,
        requested_temperature=float(requested_temperature),
        requested_pressure=float(binding.pressure),
        reference_temperature=float(reference_temperature),
        reference_pressure=float(reference_pressure),
        fluid_enthalpy_at_request=float(at_request),
        fluid_enthalpy_at_reference=float(at_reference),
        delta_h=float(at_request) - float(at_reference),
        provider_id=provenance.provider_id,
        provider_label=provenance.provider_label,
        library_version=provenance.library_version,
        backend=provenance.backend)


def reactant_mass_fractions(
    fuel_weights: tuple[float, ...],
    oxidiser_weights: tuple[float, ...],
    of_ratio: float,
) -> tuple[float, ...]:
    """Each reactant slot's share of the total propellant mass.

    ``w_ox_total = OF/(1+OF)``, ``w_fuel_total = 1/(1+OF)``, each split among
    that side's slots in proportion to its relative weights. The result sums to
    one.

    This reproduces the mass basis ``Mixture.calc_property`` uses. It is
    computed here in double precision rather than read back from CEA, which
    differs in the eighth significant figure because CEA's weight vector passes
    through float32 -- an O/F of 3.4 comes back as 3.400000095367432. That
    difference is irrelevant to the correction and *cannot* affect the
    reference-state identity, because at the reference state every increment is
    exactly zero and zero times any weight is zero.
    """
    of = float(of_ratio)
    if not math.isfinite(of) or of <= 0.0:
        raise CEAMappingError(f"O/F must be positive and finite, got {of_ratio!r}")
    fuel_total = math.fsum(fuel_weights)
    ox_total = math.fsum(oxidiser_weights)
    if fuel_total <= 0.0 or ox_total <= 0.0:
        raise CEAMappingError(
            "both the fuel and the oxidiser side must carry weight")
    fuel_share = 1.0 / (1.0 + of)
    ox_share = of / (1.0 + of)
    return tuple(
        fuel_share * (f / fuel_total) + ox_share * (o / ox_total)
        for f, o in zip(fuel_weights, oxidiser_weights))


def mixture_enthalpy_correction(
    mass_fractions: tuple[float, ...],
    increments: tuple[float, ...],
) -> float:
    """``sum(w_i * delta_h_i)`` in J/kg of mixture.

    Linear, because ``Mixture.calc_property(ENTHALPY, ...)`` is linear in the
    mass fractions -- verified directly against CEA, which reproduces the
    mass-weighted sum of its own single-reactant enthalpies to 0.025 J/kg in
    1.58e6, the residue of that float32 weight vector.

    So adding this one number to the mixture enthalpy is the same operation as
    correcting each reactant and re-mixing, and it has the advantage of leaving
    CEA's own weights untouched.
    """
    if len(mass_fractions) != len(increments):
        raise CEAMappingError(
            f"{len(mass_fractions)} mass fractions for {len(increments)} "
            "increments")
    return math.fsum(w * d for w, d in zip(mass_fractions, increments))
