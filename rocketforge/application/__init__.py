"""Layer 5 -- application.

The composition root: it adapts verified physics into the shapes the interface
consumes, owns display formatting, and is the only layer permitted to import
Qt. Nothing imports this package.

It owns no engineering equations. Where a display convention differs from the
physics convention -- a table printing p0/p where the physics computes p/p0 --
the adapter takes a reciprocal of the computed value. That is a representation
transform, never a second implementation.
"""

from __future__ import annotations

__all__: list[str] = []
