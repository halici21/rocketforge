"""What a caller asks a thermochemistry provider for.

A request is validated **before** any provider is consulted. That is not
defensive tidiness: Phase 5B-0 measured NASA CEA silently accepting a negative
temperature and a negative pressure without raising, so a malformed request that
reaches a provider may come back as a plausible-looking number rather than as an
error. RocketForge refuses it first.

Nothing here solves anything. A request is a question.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import PropellantError, PropellantRoleError, ThermochemistryError
from .propellants import MixtureRatio, PropellantStream
from .types import (
    ChemistryMode,
    EquilibriumConstraint,
    ExpansionMode,
    PropellantRole,
)

__all__ = ["ChamberEquilibriumRequest", "ExpansionRequest"]


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ThermochemistryError(
            f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise ThermochemistryError(f"{what} must be finite, got {number!r}")
    return number


@dataclass(frozen=True, slots=True)
class ChamberEquilibriumRequest:
    """A request for the equilibrium state of a combustion chamber.

    Attributes:
        fuel: The fuel stream, in its **actual** condition. Its temperature is
            what the chamber energy balance uses -- not the propellant
            definition's reference temperature.
        oxidiser: The oxidiser stream, likewise.
        oxidiser_fuel_ratio: O/F. Named for its orientation so it cannot be
            read as F/O (Phase 5B spec section 68).
        chamber_pressure: Pa, strictly positive and finite.
        chemistry_mode: How chemistry is treated. Equilibrium is the only
            chamber mode; the field exists so provenance always carries one.
        equilibrium_constraint: Which properties are held fixed. ``HP`` for a
            chamber: a rocket chamber is a steady-flow device at a pressure set
            by the throat, so enthalpy and pressure are what is conserved. A
            ``UV`` calculation would give a noticeably higher temperature --
            correct for a bomb calorimeter, wrong for a rocket
            (``11`` section 3.2).
        product_species: Optional explicit product set. ``None`` means "let the
            provider choose", which is a real capability -- CEA can derive
            products from reactants. When supplied it is recorded in provenance,
            because a 9-species result and a 50-species result are different
            calculations.
        trace_threshold: Optional mole-fraction floor below which a provider may
            drop species. ``None`` means no truncation is requested. This is a
            *provider* setting, not a display setting: a composition this
            package holds is always complete.

    Deliberately absent:

    * **total mass flow.** A chamber equilibrium is set by the *ratio* of
      reactants, not their absolute rate (Phase 5B spec section 192). A stream
      may carry a mass flow, and then ``MixtureRatio`` can be derived from the
      pair, but the request never requires one.
    * **nozzle geometry, area ratios, chamber dimensions.** Those belong to
      ``engineering`` (``08`` section 4).
    * **provider-specific flags.** No ``n_frz``, no ``iac``, no ``**kwargs``.
      A provider's control vocabulary stays in its adapter
      (Phase 5B spec sections 116, 207, 208).
    """

    fuel: PropellantStream
    oxidiser: PropellantStream
    oxidiser_fuel_ratio: MixtureRatio
    chamber_pressure: float
    chemistry_mode: ChemistryMode = ChemistryMode.EQUILIBRIUM
    equilibrium_constraint: EquilibriumConstraint = EquilibriumConstraint.HP
    product_species: tuple[str, ...] | None = None
    trace_threshold: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fuel, PropellantStream):
            raise PropellantError(
                f"fuel must be a PropellantStream, got {type(self.fuel).__name__}")
        if not isinstance(self.oxidiser, PropellantStream):
            raise PropellantError(
                f"oxidiser must be a PropellantStream, got "
                f"{type(self.oxidiser).__name__}")
        if self.fuel.role is not PropellantRole.FUEL:
            raise PropellantRoleError(
                f"the fuel stream carries {self.fuel.propellant.name!r}, whose role "
                f"is {self.fuel.role.value}, not fuel. Arguments may be swapped.")
        if self.oxidiser.role is not PropellantRole.OXIDISER:
            raise PropellantRoleError(
                f"the oxidiser stream carries {self.oxidiser.propellant.name!r}, "
                f"whose role is {self.oxidiser.role.value}, not oxidiser. "
                "Arguments may be swapped.")
        if not isinstance(self.oxidiser_fuel_ratio, MixtureRatio):
            raise PropellantError(
                "oxidiser_fuel_ratio must be a MixtureRatio; a bare float would "
                "carry no basis and no orientation")
        pressure = _finite(self.chamber_pressure, "chamber pressure")
        if pressure <= 0.0:
            raise ThermochemistryError(
                f"chamber pressure must be strictly positive, got {pressure!r} Pa. "
                "This is checked here because a provider may accept a negative "
                "pressure without complaint and return a plausible-looking number.")
        if not isinstance(self.chemistry_mode, ChemistryMode):
            raise ThermochemistryError(
                f"chemistry_mode must be a ChemistryMode member, got "
                f"{self.chemistry_mode!r}")
        if not isinstance(self.equilibrium_constraint, EquilibriumConstraint):
            raise ThermochemistryError(
                f"equilibrium_constraint must be an EquilibriumConstraint member, "
                f"got {self.equilibrium_constraint!r}")
        if self.product_species is not None:
            if not isinstance(self.product_species, tuple) or not self.product_species:
                raise ThermochemistryError(
                    "product_species must be a non-empty tuple of names, or None to "
                    "let the provider choose")
            for name in self.product_species:
                if not isinstance(name, str) or not name:
                    raise ThermochemistryError(
                        f"product species names must be non-empty strings, got {name!r}")
        if self.trace_threshold is not None:
            threshold = _finite(self.trace_threshold, "trace threshold")
            if not 0.0 < threshold < 1.0:
                raise ThermochemistryError(
                    f"trace_threshold must lie strictly between 0 and 1, got "
                    f"{threshold!r}")

    @property
    def of_mass(self) -> float:
        """The canonical oxidiser-over-fuel mass ratio for this request."""
        return self.oxidiser_fuel_ratio.of_mass

    @property
    def reactant_conditions(self) -> dict[str, float]:
        """The reactant state, shaped for a provenance record."""
        conditions = {
            "fuel_temperature": float(self.fuel.temperature),
            "oxidiser_temperature": float(self.oxidiser.temperature),
            "oxidiser_fuel_ratio": self.of_mass,
            "chamber_pressure": float(self.chamber_pressure),
        }
        if self.fuel.pressure is not None:
            conditions["fuel_pressure"] = float(self.fuel.pressure)
        if self.oxidiser.pressure is not None:
            conditions["oxidiser_pressure"] = float(self.oxidiser.pressure)
        return conditions


@dataclass(frozen=True, slots=True)
class ExpansionRequest:
    """A request for a state part-way through an expansion.

    A **data contract only**. Phase 5B computes no expansion; this type exists
    so the provider protocol has something to accept and so the freeze location
    is expressed explicitly rather than as a boolean.

    Exactly one of ``pressure`` and ``area_ratio`` must be given. They are
    genuinely different questions: an expansion is thermodynamically determined
    by entropy and pressure, and an area ratio is a *condition to be solved
    for*, which is why it costs a provider more (``09`` section 9.2).

    ``area_ratio`` is a dimensionless boundary condition, not geometry. This
    layer never sees a contour, an axial station or an area, and stores none
    (``08`` section 5.3).
    """

    mode: ExpansionMode
    pressure: float | None = None
    area_ratio: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ExpansionMode):
            raise ThermochemistryError(
                f"mode must be an ExpansionMode member, got {self.mode!r}")
        given = [name for name, value in (("pressure", self.pressure),
                                          ("area_ratio", self.area_ratio))
                 if value is not None]
        if len(given) != 1:
            raise ThermochemistryError(
                "supply exactly one of pressure or area_ratio, not "
                f"{given or 'neither'}; they are different questions and asking "
                "both would over-determine the station")
        if self.pressure is not None:
            pressure = _finite(self.pressure, "expansion pressure")
            if pressure <= 0.0:
                raise ThermochemistryError(
                    f"expansion pressure must be strictly positive, got {pressure!r} Pa")
        if self.area_ratio is not None:
            ratio = _finite(self.area_ratio, "area ratio")
            if ratio < 1.0:
                raise ThermochemistryError(
                    f"area ratio must be at least 1, got {ratio!r}; Ae/At is the ratio "
                    "of a station's area to the sonic area and cannot be below one")

    @property
    def freeze_location(self):
        """Where this request freezes composition, or ``None``."""
        return self.mode.freeze_location
