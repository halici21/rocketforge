"""Propulsion-system relations: inventory, tanks, management, pressurization, feed.

Stage-level bookkeeping and first-order relations around a liquid engine, kept
apart from the engine's own components:

* :mod:`.inventory` (SYS-1) -- usable, loaded, residual and reserved
  propellant per branch (Sutton 9th ed. §6.2, §11.1);
* :mod:`.tank_geometry` (SYS-2) -- liquid and ullage volume, and sphere or
  cylinder-with-domes internal geometry;
* :mod:`.propellant_management` (SYS-3) -- how the outlet is kept covered,
  stated as intent and checked for consistency, not proved;
* :mod:`.pressurization` (SYS-4) -- regulated stored gas and blowdown with a
  perfect gas (Sutton §6.4, §6.5, Eqs. 6-5 to 6-7);
* :mod:`.feed_network` (SYS-5) -- a series line from tank outlet to injector
  inlet: pipes with the Darcy friction factor of ``engineering.line``, local
  losses K ρv²/2, stated losses and static head.

Nothing here has a default for a physical input, and an unknown term is never
zero. None of it sizes a tank wall, a pump or a turbine.
"""

from __future__ import annotations

__all__: list[str] = []
