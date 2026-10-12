"""Pressure display units for input fields.

Display only: every case, request and stored result stays in pascals, and
changing the unit re-renders a field without changing what it holds. One table
for every page that offers a choice, so a "bar" means the same thing on each.
"""

from __future__ import annotations

__all__ = ["PRESSURE_UNITS", "DEFAULT_UNIT", "unit_info", "to_pa"]

#: Pressure units an input accepts: the key the controller stores, the label
#: shown, the factor to pascals, and the field's decimals and step.
PRESSURE_UNITS: tuple[dict, ...] = (
    {"key": "Pa", "label": "Pa", "to_pa": 1.0, "decimals": 0, "step": 1.0e5},
    {"key": "bar", "label": "bar", "to_pa": 1.0e5, "decimals": 3, "step": 1.0},
    {"key": "MPa", "label": "MPa", "to_pa": 1.0e6, "decimals": 4, "step": 0.1},
)

DEFAULT_UNIT = "Pa"


def unit_info(key: str) -> dict:
    """The unit named ``key``, or pascals for a key that names none."""
    for unit in PRESSURE_UNITS:
        if unit["key"] == key:
            return dict(unit)
    return dict(PRESSURE_UNITS[0])


def to_pa(key: str) -> float:
    """The factor from the unit named ``key`` to pascals."""
    return float(unit_info(key)["to_pa"])
