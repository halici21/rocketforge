"""Flow regimes and the model's declared domain.

Every boundary here is sourced. None of them is a number chosen because a test
passed with it.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

__all__ = [
    "FlowRegime",
    "REYNOLDS_LAMINAR_LIMIT",
    "REYNOLDS_TURBULENT_ONSET",
    "MAX_RELATIVE_ROUGHNESS",
    "COLEBROOK_REYNOLDS_MAX",
    "FRICTION_FACTOR_CONVENTION",
]

#: Above this Reynolds number fully developed laminar pipe flow is no longer
#: reliable. The classical critical value for flow in a circular pipe; below it
#: the Hagen-Poiseuille solution holds and ``f_D = 64/Re`` is exact.
REYNOLDS_LAMINAR_LIMIT: Final = 2300.0

#: Below this Reynolds number the Colebrook-White correlation is not applicable.
#: It is the lower edge of the turbulent zone on the Moody chart, and Colebrook
#: fitted his equation to turbulent commercial-pipe data above it.
REYNOLDS_TURBULENT_ONSET: Final = 4000.0

#: The upper edge of the Moody chart's turbulent zone.
COLEBROOK_REYNOLDS_MAX: Final = 1.0e8

#: The largest relative roughness the Moody chart covers. Beyond it the pipe is
#: no longer a rough pipe in the sense the correlation was fitted for.
MAX_RELATIVE_ROUGHNESS: Final = 0.05

#: Stated wherever a friction factor appears, because the two conventions
#: differ by exactly four and both are called "the friction factor".
FRICTION_FACTOR_CONVENTION: Final = (
    "Darcy friction factor f_D. The Fanning friction factor f_F is a different "
    "quantity: f_D = 4 f_F. Darcy-Weisbach uses f_D, and using f_F in it "
    "underpredicts the pressure drop by exactly a factor of four.")


class FlowRegime(StrEnum):
    """Which regime a line's Reynolds number puts it in.

    ``TRANSITIONAL`` is a real answer and not a failure: between the laminar
    limit and the turbulent onset there is no correlation this model is willing
    to stand behind, and saying so is the honest result. Nothing interpolates
    between ``64/Re`` and Colebrook across that band, because an interpolation
    would be a fabricated friction factor wearing the authority of the two
    models it sits between.
    """

    LAMINAR = "laminar"
    TRANSITIONAL = "transitional"
    TURBULENT = "turbulent"

    @property
    def has_friction_factor(self) -> bool:
        """Whether this model reports a friction factor for the regime."""
        return self is not FlowRegime.TRANSITIONAL


def classify(reynolds_number: float) -> FlowRegime:
    """The regime for a Reynolds number, by the declared boundaries."""
    value = float(reynolds_number)
    if value < REYNOLDS_LAMINAR_LIMIT:
        return FlowRegime.LAMINAR
    if value >= REYNOLDS_TURBULENT_ONSET:
        return FlowRegime.TURBULENT
    return FlowRegime.TRANSITIONAL
