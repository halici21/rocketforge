"""Universal physical constants.

Only constants that are true independently of any gas, device or application
belong here. A gas-specific value such as the specific gas constant of air is
a property of a gas model, not a universal constant, and lives with
``PerfectGas``.

Every value is SI and carries its source, because an unattributed constant is
the hardest kind of error to find later.
"""

from __future__ import annotations

from typing import Final

__all__ = ["UNIVERSAL_GAS_CONSTANT", "STANDARD_GRAVITY"]

#: Molar gas constant R, in J/(mol K).
#:
#: Exact by definition since the 2019 SI redefinition fixed the Boltzmann and
#: Avogadro constants: R = N_A * k_B. Source: CODATA / SI Brochure, 9th ed.
UNIVERSAL_GAS_CONSTANT: Final = 8.31446261815324

#: Standard acceleration of gravity g_0, in m/s^2.
#:
#: Exact by definition (CGPM, 3rd conference, 1901). Used for the Isp
#: convention in later phases; no relation in Phase 4B needs it.
STANDARD_GRAVITY: Final = 9.80665
