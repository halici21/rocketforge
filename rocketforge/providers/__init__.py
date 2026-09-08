"""Layer 4 -- external property providers.

Adapters that satisfy the protocols declared in ``physics`` using external
libraries. This is the only layer permitted to import CoolProp, RocketCEA or
Cantera, which is what keeps the physics layer importable when none of them is
installed.

Note the direction: providers depend on ``physics`` (for the protocol and the
state types it returns), not the other way round. ``application`` chooses an
implementation and injects it; nothing below ``application`` may import this
package.

Empty in Phase 4A.
"""

from __future__ import annotations

__all__: list[str] = []
