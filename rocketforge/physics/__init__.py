"""Layer 1 -- fundamental physics.

Relations that are true independently of any device: compressible flow,
fluid-property and thermochemical *interfaces*, transport correlations.

Import rule: ``physics`` may import ``core`` and the standard library. It must
never import ``engineering``, ``engine``, ``providers``, ``application`` or
PySide6. External property libraries (CoolProp, RocketCEA, Cantera) are barred
here too: this layer declares the protocol, ``providers`` implements it.

Empty in Phase 4A. The compressible-flow module specified in
``docs/engineering/03_compressible_flow_specification.md`` is Phase 4B; no
placeholder relations are stubbed out here in the meantime.
"""

from __future__ import annotations

__all__: list[str] = []
