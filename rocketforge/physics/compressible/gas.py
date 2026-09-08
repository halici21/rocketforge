"""The calorically perfect gas model.

The only gas model in this release, specified in
``docs/engineering/03_compressible_flow_specification.md`` section 2 and
``02`` section 1.2: constant ratio of specific heats, constant specific gas
constant, ideal equation of state. No chemistry, no temperature dependence, no
real-gas behaviour. Variable-gamma models arrive in a separate namespace with
their own validation rather than as a switch inside this one.

Units are SI throughout, as everywhere below the application layer:
temperature in kelvin, gas constant and specific heats in J/(kg K), speed of
sound in m/s. Nothing here converts units; that happens at the application
boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.constants import UNIVERSAL_GAS_CONSTANT
from ...core.errors import InvalidGammaError, InvalidGasConstantError, MissingGasConstantError
from ...core.numerics.arrays import (
    as_float_array,
    require_above,
    require_finite,
    restore_scalar,
)
from ...core.result import Diagnostic, Severity
from ...core.tolerances import DEFAULT_TOLERANCES

__all__ = ["PerfectGas", "speed_of_sound", "MODEL_PERFECT_GAS"]

#: Model identifier carried into result provenance. A change that alters a
#: returned number for unchanged inputs requires a new identifier (ADR-13).
MODEL_PERFECT_GAS = "perfect_gas_v1"


@dataclass(frozen=True, slots=True)
class PerfectGas:
    """A calorically perfect gas: constant gamma, constant R.

    Immutable. "Changing" a gas means constructing another one, which is what
    keeps a result reproducible: a stored analysis can name the gas it used and
    that gas cannot have been altered since.

    Attributes:
        gamma: Ratio of specific heats [-]. Hard domain
            ``1.001 <= gamma <= 3.0``; outside it, construction raises.
        gas_constant: Specific gas constant R [J/(kg K)], or None.

    ``gas_constant`` is optional by design. The dimensionless half of the
    compressible module -- every ratio, and the whole area-Mach relation --
    needs nothing but gamma, and forcing a made-up R on a user who asked for
    p/p0 at Mach 2 would be a fiction dressed as an API. Anything genuinely
    dimensional raises :class:`MissingGasConstantError` instead, naming the
    property it could not compute.

    Example:
        >>> air = PerfectGas.air()
        >>> round(air.gamma, 3), round(air.gas_constant, 2)
        (1.4, 287.05)
        >>> combustion_products = PerfectGas(gamma=1.22, gas_constant=320.0)
        >>> round(combustion_products.cp, 1)
        1774.5
    """

    gamma: float
    gas_constant: float | None = None

    def __post_init__(self) -> None:
        gamma = self.gamma
        if isinstance(gamma, bool) or not isinstance(gamma, (int, float, np.floating)):
            raise InvalidGammaError(f"gamma must be a real number, got {gamma!r}")
        gamma = float(gamma)
        if not np.isfinite(gamma):
            raise InvalidGammaError(f"gamma must be finite, got {gamma!r}")
        low, high = DEFAULT_TOLERANCES.gamma_min, DEFAULT_TOLERANCES.gamma_max
        if not low <= gamma <= high:
            raise InvalidGammaError(
                f"gamma must satisfy {low} <= gamma <= {high}, got {gamma!r}. "
                "Below the lower limit the exponents gamma/(gamma-1) exceed 1000 "
                "and overflow double precision for modest Mach numbers; a "
                "calorically perfect gas with gamma approaching 1 has unbounded "
                "specific heat and is not a meaningful model."
            )
        object.__setattr__(self, "gamma", gamma)

        if self.gas_constant is not None:
            r = self.gas_constant
            if isinstance(r, bool) or not isinstance(r, (int, float, np.floating)):
                raise InvalidGasConstantError(f"gas_constant must be a real number, got {r!r}")
            r = float(r)
            if not np.isfinite(r):
                raise InvalidGasConstantError(f"gas_constant must be finite, got {r!r}")
            if r <= 0.0:
                raise InvalidGasConstantError(
                    f"gas_constant must be strictly positive [J/(kg K)], got {r!r}"
                )
            object.__setattr__(self, "gas_constant", r)

    # -- derived properties, computed rather than stored ------------------
    #
    # Storing cp and cv alongside gamma and R would allow the four to drift
    # apart; deriving them makes cp/cv = gamma and cp - cv = R true by
    # construction rather than by discipline.

    @property
    def cp(self) -> float:
        """Specific heat at constant pressure [J/(kg K)]: ``gamma R / (gamma - 1)``."""
        return self.gamma * self._require_gas_constant("cp") / (self.gamma - 1.0)

    @property
    def cv(self) -> float:
        """Specific heat at constant volume [J/(kg K)]: ``R / (gamma - 1)``."""
        return self._require_gas_constant("cv") / (self.gamma - 1.0)

    @property
    def is_dimensional(self) -> bool:
        """Whether this gas can answer dimensional questions."""
        return self.gas_constant is not None

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        """Advisories about the model itself.

        A gamma outside the recommended band is *computable but questionable*,
        which is a warning rather than an error: the arithmetic is sound, the
        idealisation is stretched. Solution-returning relations merge these
        into their own diagnostics so the advisory reaches the caller wherever
        the gas is used, without any relation having to print anything.
        """
        low = DEFAULT_TOLERANCES.gamma_advisory_min
        high = DEFAULT_TOLERANCES.gamma_advisory_max
        if low <= self.gamma <= high:
            return ()
        return (
            Diagnostic(
                code="EXTRAPOLATED_GAMMA",
                severity=Severity.WARNING,
                message=(
                    f"gamma = {self.gamma:g} lies outside the range {low} to {high} "
                    "where the calorically perfect gas idealisation is normally "
                    "meaningful; the relations are still evaluated exactly."
                ),
                field="gamma",
                detail={"gamma": self.gamma, "advisory_min": low, "advisory_max": high},
            ),
        )

    def speed_of_sound(self, temperature: object) -> float | np.ndarray:
        """Speed of sound at a static temperature. See :func:`speed_of_sound`."""
        return speed_of_sound(temperature, self)

    def _require_gas_constant(self, wanted: str) -> float:
        if self.gas_constant is None:
            raise MissingGasConstantError(
                f"{wanted} is a dimensional property and needs a gas constant, but this "
                "gas was constructed without one. Supply gas_constant [J/(kg K)], or "
                "use the dimensionless relations, which need only gamma."
            )
        return self.gas_constant

    # -- named constructors ------------------------------------------------
    #
    # Explicit, never implicit. No relation in this package defaults to air:
    # rocket combustion products commonly sit near gamma = 1.2 with a gas
    # constant twice that of air, and a hidden air default would silently make
    # every such analysis wrong.

    @classmethod
    def air(cls) -> "PerfectGas":
        """Dry air as a calorically perfect gas.

        gamma = 1.4 and R = 287.0528 J/(kg K), the latter being
        ``8314.32 / 28.9644`` from the US Standard Atmosphere, 1976.
        """
        return cls(gamma=1.4, gas_constant=287.0528)

    @classmethod
    def from_molar_mass(cls, gamma: float, molar_mass: float) -> "PerfectGas":
        """Build a gas from gamma and a molar mass.

        Args:
            gamma: Ratio of specific heats [-].
            molar_mass: Molar mass [kg/mol] -- kilograms, not grams. This is
                the form a thermochemistry provider will return.
        """
        if not isinstance(molar_mass, (int, float, np.floating)) or isinstance(molar_mass, bool):
            raise InvalidGasConstantError(f"molar_mass must be a real number, got {molar_mass!r}")
        molar_mass = float(molar_mass)
        if not np.isfinite(molar_mass) or molar_mass <= 0.0:
            raise InvalidGasConstantError(
                f"molar_mass must be finite and strictly positive [kg/mol], got {molar_mass!r}"
            )
        return cls(gamma=gamma, gas_constant=UNIVERSAL_GAS_CONSTANT / molar_mass)


def speed_of_sound(temperature: object, gas: PerfectGas) -> float | np.ndarray:
    """Speed of sound in a perfect gas.

    ``a = sqrt(gamma R T)``.

    Args:
        temperature: Static temperature [K], strictly positive. Scalar or
            array; the return type mirrors it.
        gas: The gas model. Must carry a gas constant.

    Returns:
        Speed of sound [m/s].

    Raises:
        DomainError: Temperature is not finite or not strictly positive.
        MissingGasConstantError: The gas has no gas constant.

    Kelvin, always. Nothing here recognises Celsius, and a temperature of 20
    would be interpreted as 20 K rather than as room temperature -- which is
    why the domain check rejects non-positive values loudly instead of
    guessing. Unit conversion belongs at the application boundary.
    """
    r = gas._require_gas_constant("speed of sound")
    array, was_scalar = as_float_array(temperature, "temperature")
    require_finite(array, "temperature [K]")
    require_above(array, 0.0, "temperature [K]")
    return restore_scalar(np.sqrt(gas.gamma * r * array), was_scalar)
