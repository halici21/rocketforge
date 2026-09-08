"""Thermodynamic states produced by a thermochemistry provider.

Two records, both immutable, both Phase 5A's canonical names (``09`` sections
7 and 8):

* :class:`ChamberGas` -- the **stagnation** state of the combustion products at
  the nozzle entrance.
* :class:`GasStation` -- a **static** state at one station of an expansion.

Units, without exception:

====================  ==================
temperature           K
pressure              Pa
density               kg/m3
molar mass            kg/mol
specific gas constant J/(kg K)
cp, cv                J/(kg K)
enthalpy              J/kg
entropy               J/(kg K)
velocity, sound speed m/s
====================  ==================

Every property is **specific** (per kilogram), not molar, except molar mass
itself. There is no field called simply ``enthalpy`` with an unstated basis.

**No performance quantities live here.** There is no ``c_star``, no ``cf``, no
``isp`` and no ``thrust``, and none may be added. Those depend on a nozzle and
belong to ``engineering.nozzle`` (ADR-15). NASA CEA returns c*, Cf and Isp
natively, and that is a reason to consume them in a provider *extension* later,
not a reason to relocate the physics boundary (Phase 5B spec section 181).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .composition import Composition
from .errors import StateConsistencyError
from .provenance import ThermochemistryProvenance
from .requests import ChamberEquilibriumRequest
from .types import CompositionBasis

__all__ = ["GasStation", "ChamberGas"]


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise StateConsistencyError(
            f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise StateConsistencyError(f"{what} must be finite, got {number!r}")
    return number


def _positive(value: object, what: str) -> float:
    number = _finite(value, what)
    if number <= 0.0:
        raise StateConsistencyError(f"{what} must be strictly positive, got {number!r}")
    return number


def _check_optional_positive(value: float | None, what: str) -> None:
    if value is not None:
        _positive(value, what)


def _check_gamma(value: float, what: str) -> float:
    number = _finite(value, what)
    if number <= 1.0:
        raise StateConsistencyError(
            f"{what} must exceed 1, got {number!r}. A ratio of specific heats at or "
            "below 1 is not physical for a gas.")
    return number


def _check_condensed(value: float | None) -> None:
    if value is None:
        return
    number = _finite(value, "condensed mass fraction")
    if not 0.0 <= number <= 1.0:
        raise StateConsistencyError(
            f"condensed mass fraction must lie in [0, 1], got {number!r}")


# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GasStation:
    """A thermochemical state at one station of an expansion. No geometry.

    Mandatory fields are exactly Phase 5A's (``09`` section 8): pressure,
    temperature, gamma. Everything else is optional and is ``None`` when the
    provider did not supply it -- never a guessed number.

    Attributes:
        pressure: Pa. Static pressure at this station.
        temperature: K. **Static** temperature, unlike :class:`ChamberGas`.
        gamma: The exponent appropriate to the mode that produced this state.
            See :attr:`gamma_equilibrium` and :attr:`gamma_frozen` for the
            distinction, and the provenance for which mode this was.
        composition: ``None`` on a frozen station **means the chamber's
            composition, unchanged** -- a documented convention, not missing
            data. A renderer must not show it as an em dash
            (``09`` section 8, ``15`` section 5).
        area_ratio: The dimensionless boundary condition this station was solved
            at, recorded so a result can say what was asked of it. It is not
            geometry: there is no area, no axial position and no contour here.
        velocity: m/s, from the energy equation on this package's enthalpy
            datum. Provider-supplied; nothing here computes it.
        condensed_mass_fraction: ``None`` means **unknown**, not zero. "The
            provider did not say" is not "there is none" (ADR-28).
    """

    pressure: float
    temperature: float
    gamma: float
    composition: Composition | None = None
    molar_mass: float | None = None
    gas_constant: float | None = None
    density: float | None = None
    enthalpy: float | None = None
    entropy: float | None = None
    cp: float | None = None
    cv: float | None = None
    cp_frozen: float | None = None
    cp_equilibrium: float | None = None
    gamma_frozen: float | None = None
    gamma_equilibrium: float | None = None
    speed_of_sound: float | None = None
    velocity: float | None = None
    mach: float | None = None
    area_ratio: float | None = None
    condensed_mass_fraction: float | None = None
    provenance: ThermochemistryProvenance | None = None

    def __post_init__(self) -> None:
        _positive(self.pressure, "station pressure")
        _positive(self.temperature, "station temperature")
        _check_gamma(self.gamma, "station gamma")
        for name in ("molar_mass", "gas_constant", "density", "cp", "cv",
                     "cp_frozen", "cp_equilibrium", "speed_of_sound"):
            _check_optional_positive(getattr(self, name), f"station {name}")
        for name in ("gamma_frozen", "gamma_equilibrium"):
            value = getattr(self, name)
            if value is not None:
                _check_gamma(value, f"station {name}")
        for name in ("enthalpy", "entropy", "velocity", "mach"):
            value = getattr(self, name)
            if value is not None:
                _finite(value, f"station {name}")
        if self.mach is not None and self.mach < 0.0:
            raise StateConsistencyError(
                f"station Mach number must be non-negative, got {self.mach!r}")
        if self.velocity is not None and self.velocity < 0.0:
            raise StateConsistencyError(
                f"station velocity must be non-negative, got {self.velocity!r}")
        if self.area_ratio is not None:
            ratio = _finite(self.area_ratio, "station area ratio")
            if ratio < 1.0:
                raise StateConsistencyError(
                    f"station area ratio must be at least 1, got {ratio!r}")
        _check_condensed(self.condensed_mass_fraction)
        if self.composition is not None and not isinstance(self.composition, Composition):
            raise StateConsistencyError(
                f"composition must be a Composition or None, got "
                f"{type(self.composition).__name__}")
        if self.provenance is not None and not isinstance(
                self.provenance, ThermochemistryProvenance):
            raise StateConsistencyError(
                "provenance must be a ThermochemistryProvenance or None")

    @property
    def composition_is_inherited(self) -> bool:
        """True when :attr:`composition` is ``None`` by the frozen convention.

        Named so that calling code reads as intent rather than as a null check.
        """
        return self.composition is None

    @property
    def has_condensed_phase(self) -> bool | None:
        """Whether condensed species are present: True, False, or ``None``.

        ``None`` is a real answer and means the provider did not report. A
        caller deciding whether a single-phase model applies must treat ``None``
        as disqualifying, not as "no" (ADR-28).
        """
        if self.condensed_mass_fraction is None:
            return None
        return self.condensed_mass_fraction > 0.0


# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChamberGas:
    """Equilibrium combustion products at the chamber stagnation condition.

    Mandatory fields are exactly Phase 5A's (``09`` section 7): temperature,
    gamma, gas_constant, molar_mass, composition.

    :attr:`temperature` is **T0**, a stagnation temperature. It comes out of a
    constant-enthalpy problem solved from the reactants' *stagnation* enthalpy,
    so it is the stagnation temperature for the nozzle flow that follows. One
    letter's confusion between T and T0 would propagate through an entire
    expansion, which is why this is stated on the field rather than assumed
    (``11`` section 3.5).

    Attributes:
        gamma: The exponent appropriate to the mode that produced this state.
            A ``ChamberGas`` whose provenance does not state its mode is not
            valid input to a single-gamma handshake, because the handshake's
            correctness depends on knowing which gamma this is
            (``12`` section 4, precondition P1).
        gamma_equilibrium: The equilibrium isentropic exponent
            ``-(d ln p / d ln v)_s``, when the provider supplies it. Phase 5B-0
            measured this differing from the frozen ratio by **5.7 %** on a real
            LOX/CH4 chamber, so one field cannot carry both.
        gamma_frozen: ``cp/cv`` at fixed composition, when supplied.
        cp_equilibrium / cp_frozen: The corresponding heat capacities. NASA CEA
            supplies both natively; Cantera exposes only the frozen one.
        condensed_mass_fraction: ``None`` means **unknown**, not zero.
        request: The request this state answers, when the adapter recorded it.
            Gives full input traceability -- streams, their actual temperatures,
            O/F, chamber pressure and constraint -- without duplicating those
            fields onto the state (Phase 5B spec section 88).
        provenance: Which provider, which database, which mode.

    Deliberately absent: chamber dimensions, L*, contraction ratio, residence
    time, throat area, injector geometry (``08`` section 4), and every
    performance quantity (module docstring).
    """

    temperature: float
    gamma: float
    gas_constant: float
    molar_mass: float
    composition: Composition
    pressure: float | None = None
    density: float | None = None
    enthalpy: float | None = None
    entropy: float | None = None
    cp: float | None = None
    cv: float | None = None
    cp_frozen: float | None = None
    cp_equilibrium: float | None = None
    gamma_frozen: float | None = None
    gamma_equilibrium: float | None = None
    speed_of_sound: float | None = None
    condensed_mass_fraction: float | None = None
    request: ChamberEquilibriumRequest | None = None
    provenance: ThermochemistryProvenance | None = None

    def __post_init__(self) -> None:
        _positive(self.temperature, "chamber stagnation temperature")
        _check_gamma(self.gamma, "chamber gamma")
        _positive(self.gas_constant, "chamber specific gas constant")
        _positive(self.molar_mass, "chamber mean molar mass")
        if not isinstance(self.composition, Composition):
            raise StateConsistencyError(
                f"composition must be a Composition, got "
                f"{type(self.composition).__name__}")
        for name in ("pressure", "density", "cp", "cv", "cp_frozen",
                     "cp_equilibrium", "speed_of_sound"):
            _check_optional_positive(getattr(self, name), f"chamber {name}")
        for name in ("gamma_frozen", "gamma_equilibrium"):
            value = getattr(self, name)
            if value is not None:
                _check_gamma(value, f"chamber {name}")
        for name in ("enthalpy", "entropy"):
            value = getattr(self, name)
            if value is not None:
                _finite(value, f"chamber {name}")
        _check_condensed(self.condensed_mass_fraction)
        if self.request is not None and not isinstance(
                self.request, ChamberEquilibriumRequest):
            raise StateConsistencyError(
                "request must be a ChamberEquilibriumRequest or None")
        if self.provenance is not None and not isinstance(
                self.provenance, ThermochemistryProvenance):
            raise StateConsistencyError(
                "provenance must be a ThermochemistryProvenance or None")

    @property
    def stagnation_temperature(self) -> float:
        """T0 in K. An explicit alias, because :attr:`temperature` is T0."""
        return self.temperature

    @property
    def has_condensed_phase(self) -> bool | None:
        """True, False, or ``None`` for "the provider did not report"."""
        if self.condensed_mass_fraction is None:
            return None
        return self.condensed_mass_fraction > 0.0

    @property
    def mode_is_recorded(self) -> bool:
        """Whether provenance states the chemistry mode behind :attr:`gamma`.

        Precondition P1 of the compressible handshake (``12`` section 4). A
        state that cannot say which gamma it carries may not be reduced to a
        single-gamma perfect gas.
        """
        return (self.provenance is not None
                and self.provenance.chemistry_mode is not None)

    def mole_fractions(self, species) -> "dict[str, float]":
        """Product composition as mole fractions."""
        return dict(self.composition.to_basis(
            CompositionBasis.MOLE_FRACTION, species).fractions)
