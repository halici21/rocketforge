"""Combustion chamber engineering.

Phase 5E populates one part of this package: the handshake that reduces a
chemically computed :class:`ChamberGas` to the single-gamma perfect gas the
frozen compressible module consumes (``12`` section 8).

Chamber sizing -- L*, contraction ratio, residence time, chamber volume -- is
this package's other responsibility (``06`` section 2) and is not implemented.
"""

from __future__ import annotations

from .handshake import (
    GAS_CONSTANT_IDENTITY_TOLERANCE,
    ChamberGammaBasis,
    SINGLE_PHASE_CONDENSED_LIMIT,
    ReducedChamberGas,
    gamma_for_strategy,
    reduce_chamber_gas,
)

__all__ = [
    "ChamberGammaBasis",
    "ReducedChamberGas",
    "reduce_chamber_gas",
    "gamma_for_strategy",
    "SINGLE_PHASE_CONDENSED_LIMIT",
    "GAS_CONSTANT_IDENTITY_TOLERANCE",
]
