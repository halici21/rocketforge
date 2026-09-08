"""RocketForge engineering backend.

A pure-Python package: no Qt, no QML, no GUI. It must remain importable and
usable from a plain interpreter, a notebook, a test runner or a future engine
solver, with PySide6 absent from the process entirely. That property is an
acceptance criterion of the architecture, not a convenience -- see
``docs/engineering/01_engineering_architecture.md`` section 2.

The package is deliberately empty at import time. Nothing is pulled in eagerly,
so ``import rocketforge`` stays cheap however large the physics layer grows;
callers import the module they need:

    from rocketforge.core.numerics.roots import brent

Layers, lowest first (a layer may import only itself and the layers below it):

    core          units, constants, errors, results, numerics, provenance
    physics       fundamental relations, true independently of any device
    engineering   design and sizing of one physical component
    engine        assembly of components into a cycle
    providers     adapters onto external libraries; implement physics protocols
    application   the composition root; the only layer allowed to touch Qt

``tests/test_architecture.py`` enforces that direction.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Tracks the engineering backend, not the application version in main.py. The
# two are deliberately independent: the UI can ship without the backend moving,
# and the backend is usable without the UI at all.
__version__ = "0.1.0"
