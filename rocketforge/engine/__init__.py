"""Layer 3 -- engine system.

Assembly of components into a cycle: network topology, mass and pressure
balances, shaft power balance, cycle iteration, parametric studies.

Import rule: ``engine`` may import ``engineering``, ``physics`` and ``core``.
It must never import ``application``, and it must never reimplement a component
equation.

Empty in Phase 4A.
"""

from __future__ import annotations

__all__: list[str] = []
