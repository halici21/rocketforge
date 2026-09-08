"""Layer 2 -- component design.

Design and sizing of one physical component: injector, chamber, rocket nozzle,
cooling jacket, pump, turbine, valve, line, tank.

Import rule: ``engineering`` may import ``physics`` and ``core``. It must never
import ``engine`` or ``application``, and it must never restate a fundamental
relation -- a component calls the physics layer rather than carrying its own
copy of an equation.

Empty in Phase 4A.
"""

from __future__ import annotations

__all__: list[str] = []
