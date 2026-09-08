"""CoolProp-backed fluid properties.

The real temperature- and pressure-dependent path. CoolProp implements the
reference multiparameter Helmholtz equations of state for the three cryogens
this project ships -- Schmidt and Wagner for oxygen, Setzmann and Wagner for
methane, Leachman and co-workers for normal hydrogen -- through its ``HEOS``
backend, which is the backend this adapter pins.

**Optional at import time.** ``import CoolProp`` happens inside
:meth:`CoolPropFluidProvider._backend`, never at module scope, so the base
environment imports this module without the library present and gets a named
:class:`~rocketforge.physics.fluids.FluidProviderUnavailableError` only if it
actually asks for a property.

**No CoolProp name, constant or exception escapes this module.** The domain
says ``OXYGEN``; the string ``"Oxygen"`` lives in the table below and in the
provenance, and nowhere else.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from types import MappingProxyType

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.fluids import (
    FluidError,
    FluidPhase,
    FluidProperty,
    FluidPropertyCapabilities,
    FluidPropertyCapability,
    FluidPropertyProvenance,
    FluidProviderUnavailableError,
    FluidState,
    FluidStateRequest,
    PropertyStatus,
)

__all__ = [
    "CoolPropFluidProvider",
    "coolprop_is_available",
    "COOLPROP_FLUID_NAMES",
    "COOLPROP_BACKEND",
    "SATURATION_RELATIVE_BAND",
]

COOLPROP_BACKEND = "HEOS"

#: Canonical RocketForge fluid name -> CoolProp's name for the same substance.
#: The whole reason this table exists: ``"Oxygen"``, ``"O2"`` and
#: ``"HEOS::Oxygen"`` are three spellings a provider answers to, and none of
#: them is a domain identity.
COOLPROP_FLUID_NAMES: Mapping[str, str] = MappingProxyType({
    "OXYGEN": "Oxygen",
    "METHANE": "Methane",
    "HYDROGEN": "Hydrogen",
})

#: CoolProp's ``PropsSI`` key for each property, with its canonical SI unit.
#: CoolProp's SI interface already returns exactly these units, so this adapter
#: performs **no unit conversion at all** -- which is the safest possible answer
#: to the unit question, and is asserted by a mutation test.
_PROPS_KEY: Mapping[FluidProperty, str] = MappingProxyType({
    FluidProperty.DENSITY: "D",
    FluidProperty.SPECIFIC_ENTHALPY: "H",
    FluidProperty.SPECIFIC_HEAT_CP: "C",
    FluidProperty.DYNAMIC_VISCOSITY: "V",
    FluidProperty.THERMAL_CONDUCTIVITY: "L",
})

#: How close to the saturation pressure counts as *on* the saturation line.
#: Not a tolerance of RocketForge's choosing: it is CoolProp's own. Asked for
#: the phase of a fluid at a (T, p) pair within 1e-4 % of p_sat(T), CoolProp
#: declines to answer and says so, because a (T, p) pair there does not
#: determine the state -- the vapour quality does, and nobody supplied one.
#: That band is exactly the two-phase-ambiguous region, so it is the band used.
SATURATION_RELATIVE_BAND = 1.0e-6

_PHASE_NAMES: Mapping[str, FluidPhase | None] = MappingProxyType({
    "liquid": FluidPhase.LIQUID,
    "gas": FluidPhase.GAS,
    "supercritical": FluidPhase.SUPERCRITICAL,
    "supercritical_gas": FluidPhase.SUPERCRITICAL,
    "supercritical_liquid": FluidPhase.SUPERCRITICAL,
    "twophase": FluidPhase.TWO_PHASE,
    # The critical point itself is neither, and calling it either would be a
    # claim. Unknown, and therefore refused by anything that requires a phase.
    "critical_point": None,
    "unknown": None,
    "not_imposed": None,
})


def coolprop_is_available() -> bool:
    """Whether CoolProp can be imported here. A question, not an attempt."""
    try:
        import CoolProp  # noqa: F401
    except Exception:  # noqa: BLE001 - any import failure means unavailable
        return False
    return True


class CoolPropFluidProvider:
    """Fluid properties from CoolProp's reference equations of state."""

    provider_id = "coolprop"

    def __init__(self, *, version: str = "1.0",
                 label: str = "CoolProp (HEOS)") -> None:
        self._version = str(version)
        self._label = str(label)
        self._module = None
        self._props = None
        self._phase = None
        self._capabilities: FluidPropertyCapabilities | None = None
        self._limits: dict[str, tuple[float, float, float]] = {}

    # -- library access ----------------------------------------------------

    def _backend(self):
        """Import CoolProp on first use, and name the failure if it is absent."""
        if self._props is None:
            try:
                import CoolProp
                from CoolProp.CoolProp import PhaseSI, PropsSI
            except Exception as exc:  # noqa: BLE001
                raise FluidProviderUnavailableError(
                    "CoolProp is not installed in this environment, so "
                    "high-fidelity fluid properties are unavailable. This is a "
                    "deployment fact, not a calculation failure: RocketForge "
                    "runs without it, and the constant-property provider "
                    "remains available where a caller explicitly chooses an "
                    "approximation.") from exc
            self._module = CoolProp
            self._props = PropsSI
            self._phase = PhaseSI
        return self._props, self._phase

    def _native(self, name: str) -> str:
        try:
            return COOLPROP_FLUID_NAMES[name]
        except KeyError:
            raise FluidError(
                f"no CoolProp mapping for fluid {name!r}. This adapter maps "
                f"only the fluids it validates: "
                f"{', '.join(sorted(COOLPROP_FLUID_NAMES))}. A fluid without a "
                "validated mapping is unsupported, not guessed at.") from None

    def _fluid_limits(self, native: str) -> tuple[float, float, float]:
        """``(Tmin, Tmax, pmax)`` as CoolProp declares them for this fluid."""
        if native not in self._limits:
            props, _ = self._backend()
            self._limits[native] = (
                float(props("Tmin", "", 0, "", 0, native)),
                float(props("Tmax", "", 0, "", 0, native)),
                float(props("pmax", "", 0, "", 0, native)))
        return self._limits[native]

    # -- declared contract -------------------------------------------------

    @property
    def capabilities(self) -> FluidPropertyCapabilities:
        """Everything this adapter declares, including that it varies with state.

        The declared ranges are the *intersection* of the three fluids' own
        declared ranges, so a range this provider advertises is one every fluid
        it serves actually covers. Per-fluid limits are still checked at
        evaluation, because the intersection is necessarily the loosest honest
        summary and the tighter answer belongs to the fluid.
        """
        if self._capabilities is None:
            self._capabilities = FluidPropertyCapabilities(
                supported=frozenset({
                    FluidPropertyCapability.DENSITY,
                    FluidPropertyCapability.SPECIFIC_ENTHALPY,
                    FluidPropertyCapability.SPECIFIC_HEAT_CP,
                    FluidPropertyCapability.DYNAMIC_VISCOSITY,
                    FluidPropertyCapability.THERMAL_CONDUCTIVITY,
                    FluidPropertyCapability.PHASE_IDENTIFICATION,
                    FluidPropertyCapability.SATURATION_STATE,
                    FluidPropertyCapability.TEMPERATURE_DEPENDENCE,
                    FluidPropertyCapability.PRESSURE_DEPENDENCE,
                }),
                fluids=frozenset(COOLPROP_FLUID_NAMES),
                phases=frozenset({FluidPhase.LIQUID, FluidPhase.GAS,
                                  FluidPhase.SUPERCRITICAL,
                                  FluidPhase.TWO_PHASE}))
        return self._capabilities

    def provenance(self, native_name: str = "") -> FluidPropertyProvenance:
        """This provider's identity, including the exact library version."""
        library_version = ""
        if self._module is not None:
            library_version = str(getattr(self._module, "__version__", ""))
        return FluidPropertyProvenance(
            provider_id=self.provider_id,
            provider_label=self._label,
            provider_version=self._version,
            library_version=library_version,
            backend=COOLPROP_BACKEND,
            native_fluid_name=native_name,
            model_notes=("reference multiparameter Helmholtz equation of "
                         "state; properties vary with temperature and pressure"),
            approximations=())

    # -- helpers -----------------------------------------------------------

    def saturation_pressure(self, fluid_name: str,
                            temperature: float) -> float | None:
        """Saturation pressure in Pa, or ``None`` outside the two-phase region.

        Not part of the provider protocol. It exists so that a phase refusal
        can say *how* to fix itself -- "your oxygen is a gas at 1 atm and 95 K;
        it is a liquid above 1.66 bar" is an actionable message and "wrong
        phase" is not.
        """
        props, _ = self._backend()
        native = self._native(fluid_name)
        try:
            return float(props("P", "T", float(temperature), "Q", 0.0, native))
        except Exception:  # noqa: BLE001 - outside the saturation line
            return None

    # -- the production operation -----------------------------------------

    def evaluate(self, request: FluidStateRequest) -> Solution[FluidState]:
        """Evaluate one fluid at one temperature and one pressure."""
        if not isinstance(request, FluidStateRequest):
            raise FluidError(
                f"expected a FluidStateRequest, got {type(request).__name__}")

        # The mapping is checked first, and deliberately: "this adapter has no
        # model for argon" is the caller's error and is true whether or not the
        # library happens to be installed, while "CoolProp is missing" is a
        # deployment fact. Reporting them in the other order would tell a
        # caller to install a library that would not have helped.
        native = self._native(request.fluid.name)
        props, phase_of = self._backend()
        provenance = self.provenance(native_name=native)
        temperature = float(request.temperature)
        pressure = float(request.pressure)

        t_min, t_max, p_max = self._fluid_limits(native)
        if not t_min <= temperature <= t_max or pressure > p_max:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="FLUID_STATE_OUTSIDE_EQUATION_OF_STATE",
                    severity=Severity.ERROR,
                    message=(f"{request.fluid.name!r} at {temperature} K and "
                             f"{pressure} Pa is outside the range CoolProp "
                             f"states for {native!r}: T in [{t_min}, {t_max}] K, "
                             f"p up to {p_max} Pa. The provider refuses rather "
                             "than extrapolating its equation of state."),
                    field="state",
                    detail={"temperature": temperature, "pressure": pressure,
                            "t_min": t_min, "t_max": t_max, "p_max": p_max}),),
                provenance=(provenance,))

        try:
            phase_name = str(phase_of("T", temperature, "P", pressure, native))
        except Exception as exc:  # noqa: BLE001
            phase_name = f"unknown: {exc}"
        phase = _PHASE_NAMES.get(phase_name)

        if phase is None and phase_name not in _PHASE_NAMES:
            # CoolProp answered with something outside its own phase
            # vocabulary. The overwhelmingly common cause is a (T, p) pair on
            # the saturation line, which it declines to resolve because the
            # pair does not determine the state. Check that directly rather
            # than reading its message: a state within CoolProp's own band of
            # p_sat(T) *is* two-phase, and saying so is more useful than
            # "unknown".
            saturation = self.saturation_pressure(request.fluid.name,
                                                  temperature)
            if saturation is not None and abs(pressure - saturation)                     <= SATURATION_RELATIVE_BAND * saturation:
                phase = FluidPhase.TWO_PHASE
                phase_name = "twophase (on the saturation line)"

        if request.required_phase is not None and phase is not request.required_phase:
            detail: dict[str, object] = {
                "found": phase.value if phase is not None else None,
                "required": request.required_phase.value,
                "coolprop_phase": phase_name}
            saturation = self.saturation_pressure(request.fluid.name, temperature)
            hint = ""
            if saturation is not None:
                detail["saturation_pressure_Pa"] = saturation
                hint = (f" At {temperature} K this fluid is a liquid above "
                        f"{saturation:.0f} Pa.")
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="FLUID_PHASE_MISMATCH", severity=Severity.ERROR,
                    message=(f"{request.fluid.name!r} at {temperature} K and "
                             f"{pressure} Pa is "
                             f"{phase.value if phase else 'of undetermined phase'}"
                             f", and the caller requires "
                             f"{request.required_phase.value}.{hint}"),
                    field="phase", detail=detail),),
                provenance=(provenance,))

        values: dict[FluidProperty, float] = {}
        statuses: dict[FluidProperty, PropertyStatus] = {}
        diagnostics: list[Diagnostic] = []

        for prop in FluidProperty:
            if not request.wants(prop):
                statuses[prop] = PropertyStatus.NOT_REQUESTED
                continue
            if phase is FluidPhase.TWO_PHASE:
                # A saturated state has two values of every property and no
                # single correct one. Reported as ambiguity, never as one branch.
                statuses[prop] = PropertyStatus.TWO_PHASE_AMBIGUOUS
                continue
            try:
                number = float(props(_PROPS_KEY[prop], "T", temperature,
                                     "P", pressure, native))
            except Exception as exc:  # noqa: BLE001
                statuses[prop] = PropertyStatus.PROVIDER_FAILED
                diagnostics.append(Diagnostic(
                    code="FLUID_PROPERTY_UNAVAILABLE", severity=Severity.WARNING,
                    message=(f"CoolProp could not evaluate {prop.value} of "
                             f"{request.fluid.name!r} at {temperature} K and "
                             f"{pressure} Pa: {exc}"),
                    field=prop.value))
                continue
            if not math.isfinite(number):
                statuses[prop] = PropertyStatus.PROVIDER_FAILED
                diagnostics.append(Diagnostic(
                    code="FLUID_PROPERTY_NOT_FINITE", severity=Severity.WARNING,
                    message=(f"{prop.value} of {request.fluid.name!r} came back "
                             f"as {number!r}; reported as unavailable rather "
                             "than stored."),
                    field=prop.value))
                continue
            values[prop] = number
            statuses[prop] = PropertyStatus.AVAILABLE

        if phase is FluidPhase.TWO_PHASE:
            diagnostics.append(Diagnostic(
                code="FLUID_STATE_IS_TWO_PHASE", severity=Severity.WARNING,
                message=(f"{request.fluid.name!r} at {temperature} K and "
                         f"{pressure} Pa is on the saturation boundary. Every "
                         "property there has a liquid value and a vapour value; "
                         "no single one is reported, because choosing a branch "
                         "would be inventing a vapour quality nobody supplied."),
                field="phase"))
        if phase is None:
            diagnostics.append(Diagnostic(
                code="FLUID_PHASE_UNDETERMINED", severity=Severity.WARNING,
                message=(f"CoolProp reports the phase of {request.fluid.name!r} "
                         f"at this state as {phase_name!r}, which this adapter "
                         "does not map to a single phase. The phase is recorded "
                         "as unknown, and unknown is never read as gas."),
                field="phase"))

        state = FluidState(
            fluid=request.fluid, temperature=temperature, pressure=pressure,
            phase=phase, provenance=provenance, values=values,
            statuses=statuses)
        status = Status.OK_WITH_WARNINGS if diagnostics else Status.OK
        return Solution(value=state, status=status,
                        diagnostics=tuple(diagnostics),
                        provenance=(provenance,))
