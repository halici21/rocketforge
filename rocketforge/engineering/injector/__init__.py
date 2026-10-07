"""Injector hydraulics and the branch feed pressure budget (LIQ-6).

``hydraulics`` sizes each propellant branch's total injector orifice from its
mass flow (Sutton 9th ed. §8.1, Eqs. 8-1, 8-2, 8-5); ``pressure_budget`` adds
the branch's pressure terms (§10.4 Eq. 10-7, §11.5 Eqs. 11-6, 11-7) without
turning an unknown into zero. Neither designs an injector element, a feed
system or a cycle, and neither evaluates atomization, combustion efficiency or
combustion stability.
"""

from __future__ import annotations

from .hydraulics import (
    WHOLE_COUNT_TOLERANCE,
    DynamicHead,
    HoleSplit,
    OrificeSizing,
    dynamic_head,
    holes_from_count,
    holes_from_diameter,
    orifice_sizing,
)
from .pressure_budget import BranchBudget, BudgetTerm, TermStatus, branch_budget

__all__ = [
    "WHOLE_COUNT_TOLERANCE",
    "BranchBudget",
    "BudgetTerm",
    "DynamicHead",
    "HoleSplit",
    "OrificeSizing",
    "TermStatus",
    "branch_budget",
    "dynamic_head",
    "holes_from_count",
    "holes_from_diameter",
    "orifice_sizing",
]
