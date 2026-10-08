"""The propulsion system around the engine: stage-level records (SYS gates).

The liquid-engine records (LIQ-2 .. LIQ-6) describe one engine at one design
point. These describe what the stage must carry and deliver to it -- the
propellant inventory, the tanks, how the propellant is kept at the outlets,
how the tanks are pressurized, and the feed lines to the injector. They read
the engine records as upstream truth and never change them.

* :mod:`.records` -- the result, branch and ledger shapes the gates share.
* :mod:`.inventory` -- SYS-1, propellant inventory.
* :mod:`.tanks` -- SYS-2, tank geometry and packaging.
* :mod:`.management` -- SYS-3, propellant management.
* :mod:`.pressurization` -- SYS-4, tank pressurization.
* :mod:`.feed_network` -- SYS-5, liquid feed network.

Each module is data. The relations are in
:mod:`rocketforge.engineering.propulsion_system`; resolving and computing is
the application layer's.
"""

from __future__ import annotations

__all__: list[str] = []
