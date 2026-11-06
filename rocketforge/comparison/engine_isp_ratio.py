"""The engine-level Isp ratio (DB-4B): a printed engine Isp beside an ideal one.

``ratio = printed engine Isp / ideal Isp``, once per gamma basis, always both.

This is not a thrust-chamber efficiency, and nothing here decides anything. The
printed value is an engine rating whose basis may not be stated, the ideal value
is evaluated at the engine's mixture ratio, and the model has no losses and one
constant gamma. A ratio above 1 is possible and is not a defect on either side.

So the record has no verdict, no tolerance, no preferred basis and no average of
the two. Like the rest of this layer it is handed its numbers and cannot reach a
solver, so it can never produce the value it reports.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from rocketforge.core.errors import InputError

__all__ = ["GAMMA_BASES", "EngineIspRatioError", "IspRatioCell", "EngineIspRatio", "engine_isp_ratio"]

#: Neither is printed by any source, so both are always shown.
GAMMA_BASES = ("frozen", "equilibrium")


class EngineIspRatioError(InputError):
    """The values cannot form a ratio record."""


@dataclass(frozen=True, slots=True)
class IspRatioCell:
    """One gamma basis: the ideal Isp under it, in seconds, and the ratio against it."""

    gamma_basis: str
    ideal_isp_s: float
    ratio: float


@dataclass(frozen=True, slots=True)
class EngineIspRatio:
    """A printed Isp, the ideal one under each gamma basis, and what the comparison declared.

    Attributes:
        configuration_id: The configuration the printed value is stated for.
        printed_isp_s: As printed, in seconds.
        cells: One per :data:`GAMMA_BASES`, in that order.
        declarations: The choices and readings the numbers rest on, in words. They belong to the
            result and are not to be dropped from any display of it.
    """

    configuration_id: str
    printed_isp_s: float
    cells: tuple[IspRatioCell, ...]
    declarations: tuple[str, ...]


def _positive(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise EngineIspRatioError(f"{name} must be finite and positive, got {value!r}")
    return number


def engine_isp_ratio(configuration_id: str, printed_isp_s: float, ideal_isp_s: Mapping[str, float],
                     declarations: tuple[str, ...]) -> EngineIspRatio:
    """Form the record, or refuse. Both gamma bases are required, and only those."""
    if set(ideal_isp_s) != set(GAMMA_BASES):
        raise EngineIspRatioError(f"need an ideal Isp for exactly {GAMMA_BASES}, got {sorted(ideal_isp_s)}")
    if not declarations:
        raise EngineIspRatioError("a ratio with nothing declared cannot be read")
    printed = _positive(printed_isp_s, "the printed Isp")
    cells = []
    for basis in GAMMA_BASES:
        ideal = _positive(ideal_isp_s[basis], f"the {basis} ideal Isp")
        cells.append(IspRatioCell(basis, ideal, printed / ideal))
    return EngineIspRatio(configuration_id, printed, tuple(cells), tuple(declarations))
