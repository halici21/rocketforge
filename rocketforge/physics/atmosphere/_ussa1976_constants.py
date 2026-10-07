"""The U.S. Standard Atmosphere, 1976 constants, defined once (Table 2 and text).

The printed Table 2 has known typographical errors (NASA STI errata for
19770009539.pdf: R*, r0, S and sigma). The values here are those of the
defining text: R* (p. 3), r0 (p. 8, eq. 17), beta and S (p. 19, eq. 51), k and
N_A (p. 2), and they reproduce the Standard's tables. R*, k and N_A are the
Standard's, not CODATA's.
"""

from __future__ import annotations

from typing import Final

from rocketforge.core.constants import STANDARD_GRAVITY

#: g0, m/s^2, and g0', m^2/(s^2 m'): numerically equal, Gamma = 1 m'/m (eq. 18).
G0: Final = STANDARD_GRAVITY
G0_PRIME: Final = STANDARD_GRAVITY
#: R*, N m/(kmol K) (p. 3); k, N m/K, and N_A, 1/kmol (p. 2).
R_STAR: Final = 8.31432e3
BOLTZMANN: Final = 1.380622e-23
AVOGADRO: Final = 6.022169e26
#: M0, kg/kmol (section 1.2.4); r0, m (p. 8).
M0: Final = 28.9644
R0: Final = 6.356766e6
#: P0, Pa, and T0, K (pp. 3-4).
P0: Final = 101325.0
T0: Final = 288.15
#: gamma, beta (kg/(s m K^1/2)) and S (K) for eqs. (50) and (51) (pp. 4, 19).
GAMMA: Final = 1.40
BETA: Final = 1.458e-6
SUTHERLAND_S: Final = 110.4
