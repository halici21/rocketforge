"""Layer 0 -- core.

Everything here is free of physics content: units, universal constants, the
error hierarchy, the result and diagnostic types, tolerance definitions,
numerical utilities and provenance records.

Import rule: ``core`` may import the standard library and NumPy, and nothing
else from ``rocketforge``. It is the bottom of the stack, so a ``core`` module
importing ``physics`` (or anything above it) is an architecture violation and
fails ``tests/test_architecture.py``.

Domain-specific relations never belong here. A gamma-based compressible
relation lives in ``rocketforge.physics``; the root finder it calls lives here.
"""

from __future__ import annotations

__all__: list[str] = []
