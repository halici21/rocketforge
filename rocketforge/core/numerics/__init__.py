"""Numerical utilities with no physics content.

Root finding lives here; array helpers and sweep-grid sampling join it when the
physics layer that needs them arrives. Nothing in this package knows what a
Mach number is -- it solves ``f(x) = 0`` and reports how that went.
"""

from __future__ import annotations

from .roots import METHOD_BRENT, RootReport, brent

__all__ = ["brent", "RootReport", "METHOD_BRENT"]
