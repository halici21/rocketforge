"""Presentation geometry for the Rocket Performance canvas.

One function. It exists because the schematic needs to turn a solved *area*
ratio into a *radius* ratio in order to draw, and three accepted rules all say
that derivation may not live where it would otherwise have gone:

* the interface performs only layout arithmetic, so not in QML;
* the controller holds no equation and no constant, so not there either;
* and the frozen ``engineering.nozzle`` owns rocket performance, so a drawing
  helper has no business being added to it.

So it lives here, in a module whose whole subject is drawing, where it can be
tested on its own and where its name says what it is for.

**This is not physics.** ``r ∝ sqrt(A)`` is the definition of a circle's area,
used to size a picture. Nothing computed here reaches a result, a provenance
record or a published quantity.
"""

from __future__ import annotations

import math

__all__ = ["radius_ratio_for_drawing"]


def radius_ratio_for_drawing(area_ratio: float) -> float:
    """``r_e / r_t`` for a schematic drawn from an area ratio.

    Returns 0.0 for a non-positive or non-finite input rather than raising:
    the caller is a paint routine, and a drawing that cannot be sized should
    draw nothing rather than interrupt a render.
    """
    try:
        value = float(area_ratio)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value) or value <= 0.0:
        return 0.0
    return math.sqrt(value)
