"""What a thermochemistry provider must look like, and what it may be asked.

This module declares the abstraction. It implements no provider, imports no
chemistry library, and never will: ``providers`` implements what ``physics``
declares, and the arrow points that way and not back
(``06`` section 3, ``08`` section 8).

**Two documented refinements of Phase 5A**, both driven by Phase 5B-0 evidence
rather than by preference:

1. ``09`` section 9.1 shaped the protocol around propellant *names* and scalar
   arguments. This module takes a
   :class:`~rocketforge.physics.thermochemistry.requests.ChamberEquilibriumRequest`
   instead. Phase 5B-0 established that reactant **temperature and phase** are
   first-class inputs -- LOX at 90.17 K versus notional LOX at 298 K is worth
   74.9 K of flame temperature -- and a name plus a scalar cannot carry a
   stream's actual condition without an ever-growing keyword list.

2. ``09`` section 9.4 and ADR-30 had providers return a bare value and raise on
   failure. This protocol returns ``Solution[ChamberGas]``. The reason is the
   project's own policy, quoted from :mod:`rocketforge.core.errors`: *"A root
   solver that merely ran out of iterations has not failed in that sense: it
   returns its best estimate with converged=False and never raises."* Phase
   5B-0 found NASA CEA exposing exactly such a flag (``solution.converged``),
   and a bare return has nowhere to put it. Malformed input still raises, and
   provider breakage still raises; non-convergence is reported.

Neither change weakens ADR-30's intent -- adapters stay thin, and no provider
type crosses the boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from rocketforge.core.result import Solution

from .errors import ThermochemistryError, UnsupportedCapabilityError
from .provenance import ThermochemistryProvenance
from .requests import ChamberEquilibriumRequest
from .states import ChamberGas
from .types import ExpansionMode
from enum import StrEnum

__all__ = [
    "ProviderCapability",
    "ProviderCapabilities",
    "ThermochemistryProvider",
]


class ProviderCapability(StrEnum):
    """One thing a provider can do.

    An enumerated set rather than several dozen boolean fields: the set is
    introspectable, extends without changing a dataclass signature, and cannot
    drift out of sync with itself (Phase 5B spec section 106).

    The membership is shaped by what Phase 5B-0 actually found the two candidate
    providers doing, so that neither has to lie: NASA CEA declares
    ``ROCKET_PERFORMANCE`` and ``LIQUID_REACTANTS``, Cantera does not, and
    Cantera declares ``KINETICS``, which CEA does not.
    """

    HP_EQUILIBRIUM = "hp_equilibrium"
    SP_EQUILIBRIUM = "sp_equilibrium"
    COMPOSITION = "composition"
    """Returns the product composition, not only bulk properties."""
    CONDENSED_PHASES = "condensed_phases"
    """Can include condensed species in the equilibrium at all."""
    CONDENSED_PHASE_REPORTING = "condensed_phase_reporting"
    """Can report how much condensed material is actually present. Distinct from
    CONDENSED_PHASES because Phase 5B-0 found a provider counter that reports
    candidate condensed species rather than present ones."""
    LIQUID_REACTANTS = "liquid_reactants"
    """Has thermodynamic data for reactants in the liquid phase."""
    CUSTOM_REACTANT_TEMPERATURE = "custom_reactant_temperature"
    """Accepts a reactant temperature other than its own reference."""
    CUSTOM_REACTANTS = "custom_reactants"
    """Accepts a caller-defined species or surrogate."""
    CUSTOM_SPECIES_SET = "custom_species_set"
    """Accepts an explicit product species list."""
    EQUILIBRIUM_EXPANSION = "equilibrium_expansion"
    FROZEN_EXPANSION = "frozen_expansion"
    FREEZE_LOCATION_CONTROL = "freeze_location_control"
    """Can freeze composition at a chosen station rather than only at one."""
    PRESSURE_RATIO_EXPANSION = "pressure_ratio_expansion"
    AREA_RATIO_EXPANSION = "area_ratio_expansion"
    NATIVE_EQUILIBRIUM_GAMMA = "native_equilibrium_gamma"
    """Reports the equilibrium isentropic exponent directly, rather than
    leaving the caller to finite-difference it."""
    ROCKET_PERFORMANCE = "rocket_performance"
    """Returns c*, Cf or Isp natively. Declaring this does **not** move
    ownership of rocket performance out of ``engineering.nozzle``; it says the
    provider can supply oracle values (Phase 5B spec section 16, 181)."""
    MONOPROPELLANTS = "monopropellants"
    TRANSPORT_PROPERTIES = "transport_properties"
    KINETICS = "kinetics"
    IONISED_SPECIES = "ionised_species"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """What a provider declares it can do, and over what range.

    **Declared, never discovered.** A caller must be able to ask before calling,
    so the interface can present honest options instead of finding a limitation
    through an exception mid-calculation (``10`` section 4).

    A capability that is absent means the corresponding call raises
    :class:`~rocketforge.physics.thermochemistry.errors.UnsupportedCapabilityError`
    immediately and always. It must never partially work, and it must never
    quietly substitute a capability the provider does have.

    Attributes:
        supported: The set of capabilities this provider declares.
        pressure_range: ``(min, max)`` in Pa. The provider's **validated**
            range, not its tolerated range: a call outside it is refused with a
            diagnostic naming the range, never silently extrapolated.
        mixture_ratio_range: ``(min, max)`` O/F by mass, validated range.
        temperature_ceiling: K above which the provider's data runs out, or
            ``None`` when it declares none.
    """

    supported: frozenset[ProviderCapability] = field(default_factory=frozenset)
    pressure_range: tuple[float, float] | None = None
    mixture_ratio_range: tuple[float, float] | None = None
    temperature_ceiling: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.supported, frozenset):
            raise ThermochemistryError(
                f"supported must be a frozenset of ProviderCapability, got "
                f"{type(self.supported).__name__}")
        for item in self.supported:
            if not isinstance(item, ProviderCapability):
                raise ThermochemistryError(
                    f"{item!r} is not a ProviderCapability member")
        for name in ("pressure_range", "mixture_ratio_range"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, tuple) or len(value) != 2:
                raise ThermochemistryError(f"{name} must be a (min, max) tuple")
            low, high = (float(value[0]), float(value[1]))
            if not (math.isfinite(low) and math.isfinite(high)):
                raise ThermochemistryError(f"{name} bounds must be finite")
            if low <= 0.0 or high <= low:
                raise ThermochemistryError(
                    f"{name} must be a positive ascending range, got {value!r}")
        if self.temperature_ceiling is not None:
            ceiling = float(self.temperature_ceiling)
            if not math.isfinite(ceiling) or ceiling <= 0.0:
                raise ThermochemistryError(
                    f"temperature_ceiling must be positive and finite, "
                    f"got {self.temperature_ceiling!r}")

    def supports(self, capability: ProviderCapability) -> bool:
        """Whether this provider declares ``capability``."""
        if not isinstance(capability, ProviderCapability):
            raise ThermochemistryError(
                f"{capability!r} is not a ProviderCapability member")
        return capability in self.supported

    def require(self, capability: ProviderCapability, provider_id: str = "") -> None:
        """Raise unless ``capability`` is declared.

        The refusal names what was missing, so a caller never has to infer a
        capability gap from a numerical oddity.
        """
        if not self.supports(capability):
            who = f"{provider_id!r} " if provider_id else ""
            raise UnsupportedCapabilityError(
                f"provider {who}does not declare {capability.value}. A declared-absent "
                "capability raises rather than falling back: silently returning "
                "frozen results when equilibrium was requested would look right and "
                "be systematically wrong.")

    def supports_expansion_mode(self, mode: ExpansionMode) -> bool:
        """Whether an expansion mode is available on this provider."""
        if mode is ExpansionMode.EQUILIBRIUM:
            return self.supports(ProviderCapability.EQUILIBRIUM_EXPANSION)
        if mode is ExpansionMode.FROZEN:
            return self.supports(ProviderCapability.FROZEN_EXPANSION)
        return (self.supports(ProviderCapability.FROZEN_EXPANSION)
                and self.supports(ProviderCapability.FREEZE_LOCATION_CONTROL))

    def pressure_is_in_range(self, pressure: float) -> bool:
        """Whether a chamber pressure lies in the declared validated range.

        ``True`` when no range is declared: an undeclared range is not a claim
        that everything is valid, it is an absence of information, and refusing
        on that basis would block a provider that simply did not state one.
        """
        if self.pressure_range is None:
            return True
        low, high = self.pressure_range
        return low <= float(pressure) <= high

    def mixture_ratio_is_in_range(self, of_mass: float) -> bool:
        """Whether an O/F lies in the declared validated range."""
        if self.mixture_ratio_range is None:
            return True
        low, high = self.mixture_ratio_range
        return low <= float(of_mass) <= high


@runtime_checkable
class ThermochemistryProvider(Protocol):
    """The contract every thermochemistry provider implements.

    A ``Protocol`` rather than a base class, following the precedent set for
    ``FluidPropertyProvider`` (``01`` section 5): a provider can be a CEA
    adapter, a Cantera adapter, a lookup table or a test stub without inheriting
    from a physics type, and this package stays importable with none of them
    installed -- which is the property that makes ``pytest`` run on a clean
    checkout.

    **Nothing provider-specific crosses this boundary.** No ``cantera.Solution``,
    no CEA solver object, no ``n_frz``, no ``iac``, no ``**kwargs``. Inputs and
    outputs are RocketForge domain records only. Phase 5B-0 confirmed both
    candidates hand out mutable or reused state objects, so an adapter must copy
    values out and build an immutable snapshot rather than passing anything
    through.

    Error policy, three outcomes that are never conflated:

    * **malformed input** -- an ``InputError`` subclass, raised. Requests
      validate themselves on construction, so this normally happens before a
      provider is reached at all.
    * **no solution / not converged** -- a ``Solution`` whose status says so.
      Not an exception: "this mixture does not converge" is a meaningful answer.
    * **provider failure** -- a ``ProviderError`` subclass, raised. The library
      is missing, its data file is absent, or a declared capability was not
      honoured.
    """

    provider_id: str
    """Stable machine identifier, e.g. ``"cea"``. Matches the provenance id."""

    version: str
    """The adapter's version."""

    capabilities: ProviderCapabilities
    """What this provider declares it can do."""

    def provenance(self) -> ThermochemistryProvenance:
        """A provenance record describing this provider and its data.

        Called without a result so that an interface can show what is installed
        before anything is computed.
        """
        ...

    def solve_chamber(
        self, request: ChamberEquilibriumRequest
    ) -> Solution[ChamberGas]:
        """Solve the chamber equilibrium described by ``request``.

        The returned :class:`~rocketforge.physics.thermochemistry.states.ChamberGas`
        must carry provenance stating the chemistry mode, or it cannot be used
        by the downstream single-gamma handshake (``12`` section 4).
        """
        ...
