"""U.S. Standard Atmosphere, 1976, from 86 km to 1000 km (geometric).

Above 86 km the Standard is no longer a mixed, hydrostatic gas. Each species
diffuses on its own, and the profile is defined in geometric altitude Z by the
equations of section 1.2.6 and 1.3 of NOAA-S/T 76-1562. Those equations are
implemented here, with the Standard's constants and no approximation.

**Temperature** (eqs. 25-32): isothermal 86-91 km at T7 = 186.8673 K; a
segment of an ellipse 91-110 km; linear 110-120 km at 12 K/km; then
``T = T_inf - (T_inf - T10) exp(-lambda xi)`` to 1000 km.

**Number densities** (eqs. 35-38), integrated upward from the Table 9 values at
86 km, in the Standard's order N2, O, O2, Ar, He:

    d ln(n_i T)/dZ = -[ f_i(Z) + v_i/(D_i + K) ]
    f_i = g/(R* T) D_i/(D_i + K) [M_i + M K/D_i + alpha_i R*/g dT/dZ]   (36)
    D_i = a_i / (sum n) (T/273.15)^b_i                                  (8)
    K   = 120 m^2/s to 95 km, eq. 7b to 115 km, 0 above                 (7)

* N2 (eq. 38) has no flux term and its D/K split is replaced by M: M0 up to
  100 km, M(N2) above.
* O and O2 diffuse through N2 as the stationary background gas (p. 14), so
  their D_i uses n(N2).
* Ar and He diffuse through N2 + O + O2, and M is that mixture's mean
  molecular weight.
* For all four, M is M0 below 100 km, for consistency with N2 (p. 14).
* The flux terms are eq. 37 with Table 7. The second term applies to O only,
  and only from 86 to 97 km.

**Hydrogen** (eqs. 39, 40) is defined from 150 to 1000 km only. It is
referenced to n(H) = 8.0e10 m^-3 at 500 km with the escape flux
phi = 7.2e11 m^-2 s^-1. Its D(H) uses the sum of the other five species. Above
500 km the flux integral is neglected, as the Standard states and as its
tables are computed. Below 150 km the Standard neglects H, so H is absent
there. Its appearance at 150 km adds n(H)/N ~ 7e-6 to the total number
density, a step the Standard's own definition makes.

**Totals** (eqs. 20, 33c, 42): N = sum n_i, P = N k T, rho = sum n_i M_i/N_A,
M = sum n_i M_i / N, and TM = T M0/M.

**Not defined above 86 km:** speed of sound and dynamic viscosity. The
Standard terminates both at 86 km (sections 1.3.10 and 1.3.11): eq. 50 holds
only while sound is a small perturbation of a continuum, and eq. 51 "fails for
conditions of very high and very low temperatures".

The integration runs once, lazily, to nodes every 1 km from 86 to 1000 km (all
of the Standard's breakpoints are whole kilometres). A query between nodes
integrates the same equations onward from the node below. Nothing is
interpolated.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Final

from ._dopri5 import integrate
from ._ussa1976_constants import AVOGADRO, BOLTZMANN, G0, M0, R0, R_STAR

__all__ = [
    "AVOGADRO",
    "BOLTZMANN",
    "MOLAR_MASS",
    "N_7",
    "UPPER_RANGE_KM",
    "dtemperature_dz",
    "species",
    "temperature",
]

R0_KM: Final = R0 / 1000.0

#: Molecular weights, kg/kmol: Table 3, with O and H as half of O2 and H2.
MOLAR_MASS: Final = {"N2": 28.0134, "O": 15.9994, "O2": 31.9988, "Ar": 39.948,
                     "He": 4.0026, "H": 1.00797}

#: Table 9: number densities at Z7 = 86 km, m^-3.
N_7: Final = {"N2": 1.129794e20, "O": 8.6e16, "O2": 3.030898e19, "Ar": 1.351400e18,
              "He": 7.5817e14}

#: Table 6: alpha_i, a_i (m^-1 s^-1), b_i.
ALPHA: Final = {"N2": 0.0, "O": 0.0, "O2": 0.0, "Ar": 0.0, "He": -0.40, "H": -0.25}
A_COEF: Final = {"O": 6.986e20, "O2": 4.863e20, "Ar": 4.487e20, "He": 1.700e21,
                 "H": 3.305e21}
B_COEF: Final = {"O": 0.750, "O2": 0.750, "Ar": 0.870, "He": 0.691, "H": 0.500}

#: Table 7: Q (km^-3), q (km^-3), U (km), u (km), W (km^-3), w (km^-3).
FLUX: Final = {
    "O": (-5.809644e-4, -3.416248e-3, 56.90311, 97.0, 2.706240e-5, 5.008765e-4),
    "O2": (1.366212e-4, 0.0, 86.000, 0.0, 8.333333e-5, 0.0),
    "Ar": (9.434079e-5, 0.0, 86.000, 0.0, 8.333333e-5, 0.0),
    "He": (-2.457369e-4, 0.0, 86.000, 0.0, 6.666667e-4, 0.0),
}

#: Temperature segments (Tables 2 and 5, eqs. 25-32).
Z7, Z8, Z9, Z10, Z11, Z12 = 86.0, 91.0, 110.0, 120.0, 500.0, 1000.0   # km
T7: Final = 186.8673
T9, LK9, T10, T_INF = 240.0, 12.0, 360.0, 1000.0
#: The ellipse of eq. 27, from its defining conditions (Appendix B, eqs. B-5,
#: B-8, B-9): T = T8 with zero slope at 91 km and T = T9 with slope LK9 at
#: 110 km. The printed constants (263.1905 K, -76.3232 K, -19.9429 km) are
#: these rounded to four decimals; used rounded, the ellipse would end
#: 2.7e-4 K short of T9 and step at 110 km.
TC: Final = ((LK9 * (Z9 - Z8) * T9 + T7 ** 2 - T9 ** 2)
             / (LK9 * (Z9 - Z8) + 2.0 * T7 - 2.0 * T9))                  # B-8
A_ELLIPSE: Final = T7 - TC                                               # B-5
A_AXIS: Final = (Z9 - Z8) * A_ELLIPSE / math.sqrt(A_ELLIPSE ** 2 - (T9 - TC) ** 2)    # B-9
LAMBDA: Final = LK9 / (T_INF - T10)                 # 0.01875 per km
K7, K10 = 1.2e2, 0.0

#: n(H) at Z11 = 500 km (m^-3) and the hydrogen flux phi (m^-2 s^-1).
N_H_11: Final = 8.0e10
PHI: Final = 7.2e11

UPPER_RANGE_KM: Final = (Z7, Z12)
_ORDER = ("N2", "O", "O2", "Ar", "He")
#: Integration tolerance on ln(n T) (magnitude ~40): well below the tables'
#: four figures and above double-precision noise.
_TOL: Final = 1e-14


def temperature(z: float) -> float:
    """Kinetic temperature, K, at geometric altitude ``z`` km (86-1000)."""
    if z < Z8:
        return T7
    if z < Z9:
        x = (z - Z8) / A_AXIS
        return TC + A_ELLIPSE * math.sqrt(1.0 - x * x)
    if z < Z10:
        return T9 + LK9 * (z - Z9)
    xi = (z - Z10) * (R0_KM + Z10) / (R0_KM + z)
    return T_INF - (T_INF - T10) * math.exp(-LAMBDA * xi)


def dtemperature_dz(z: float) -> float:
    """dT/dZ, K/km (eqs. 26, 28, 30, 32)."""
    if z < Z8:
        return 0.0
    if z < Z9:
        x = (z - Z8) / A_AXIS
        return -A_ELLIPSE / A_AXIS * x / math.sqrt(1.0 - x * x)
    if z < Z10:
        return LK9
    xi = (z - Z10) * (R0_KM + Z10) / (R0_KM + z)
    return (LAMBDA * (T_INF - T10) * ((R0_KM + Z10) / (R0_KM + z)) ** 2
            * math.exp(-LAMBDA * xi))


def _gravity(z: float) -> float:
    return G0 * (R0_KM / (R0_KM + z)) ** 2                        # eq. 17


def _eddy(z: float) -> float:
    if z < 95.0:
        return K7
    if z < 115.0:
        return K7 * math.exp(1.0 - 400.0 / (400.0 - (z - 95.0) ** 2))
    return K10


def _flux(name: str, z: float) -> float:
    q_big, q_small, u_big, u_small, w_big, w_small = FLUX[name]
    term = q_big * (z - u_big) ** 2 * math.exp(-w_big * (z - u_big) ** 3)
    if q_small and z <= u_small:
        term += q_small * (u_small - z) ** 2 * math.exp(-w_small * (u_small - z) ** 3)
    return term                                                  # per km


def _rates(z: float, y: list[float]) -> list[float]:
    """d/dZ (per km) of ln(n_i T) for N2, O, O2, Ar, He."""
    t, dt = temperature(z), dtemperature_dz(z)
    g = _gravity(z)
    n = [math.exp(v) / t for v in y]
    n_n2, n_o, n_o2 = n[0], n[1], n[2]
    per_km = 1000.0 * g / (R_STAR * t)                           # (g/R*T) per km, x M
    out = [-(per_km * (M0 if z <= 100.0 else MOLAR_MASS["N2"]))]   # eq. 38
    k = _eddy(z)
    background_light = n_n2
    background_heavy = n_n2 + n_o + n_o2
    for index, name in enumerate(_ORDER[1:], start=1):
        if name in ("O", "O2"):
            background, m_mix = background_light, MOLAR_MASS["N2"]
        else:
            background = background_heavy
            m_mix = (n_n2 * MOLAR_MASS["N2"] + n_o * MOLAR_MASS["O"]
                     + n_o2 * MOLAR_MASS["O2"]) / background_heavy
        if z <= 100.0:
            m_mix = M0
        d = A_COEF[name] / background * (t / 273.15) ** B_COEF[name]
        f = (per_km * (d * MOLAR_MASS[name] + k * m_mix) / (d + k)
             + d / (d + k) * ALPHA[name] * dt / t)
        out.append(-(f + _flux(name, z)))
    return out


def _rates_with_hydrogen(z: float, y: list[float]) -> list[float]:
    """The five species, plus tau and G for hydrogen (eqs. 39, 40), from 150 km.

    tau(Z) = int_150^Z g M_H/(R* T) dZ and G(Z) = int_150^Z phi/D_H
    (T/T11)^(1+alpha) e^tau dZ, both in metres, measured from 150 km. Eq. 39's
    integrals from 500 km follow from these by subtraction.
    """
    out = _rates(z, y[:5])
    t = temperature(z)
    total = sum(math.exp(v) / t for v in y[:5])
    d_h = A_COEF["H"] / total * (t / 273.15) ** B_COEF["H"]
    out.append(1000.0 * _gravity(z) * MOLAR_MASS["H"] / (R_STAR * t))
    out.append(1000.0 * PHI / d_h * (t / _T11) ** (1.0 + ALPHA["H"]) * math.exp(y[5]))
    return out


_T11: Final = temperature(Z11)


@lru_cache(maxsize=1)
def _nodes() -> dict[int, tuple[float, ...]]:
    """Solution at every whole kilometre 86..1000: ln(n_i T) x5, then tau, G from 150."""
    y = [math.log(N_7[name] * T7) for name in _ORDER]
    nodes = {86: tuple(y)}
    for z in range(87, 151):
        y = integrate(_rates, z - 1, y, z, rtol=_TOL, atol=_TOL)
        nodes[z] = tuple(y)
    y = list(nodes[150]) + [0.0, 0.0]
    nodes[150] = tuple(y)
    for z in range(151, 1001):
        y = integrate(_rates_with_hydrogen, z - 1, y, z, rtol=_TOL, atol=_TOL)
        nodes[z] = tuple(y)
    return nodes


def species(z: float) -> dict[str, float]:
    """Number densities, m^-3, at geometric altitude ``z`` km, 86 <= z <= 1000."""
    if not Z7 <= z <= Z12:
        raise ValueError(f"the upper Standard covers 86-1000 km, not {z!r}")
    nodes = _nodes()
    base = min(int(math.floor(z)), 999) if z < Z12 else 1000
    if base < 150:
        y = list(nodes[base][:5])
        y = y if z == base else integrate(_rates, float(base), y, z, rtol=_TOL, atol=_TOL)
    else:
        y = list(nodes[base])
        y = y if z == base else integrate(_rates_with_hydrogen, float(base), y, z,
                                          rtol=_TOL, atol=_TOL)
    t = temperature(z)
    result = {name: math.exp(y[i]) / t for i, name in enumerate(_ORDER)}
    if z >= 150.0:
        tau_500, g_500 = nodes[500][5], nodes[500][6]
        tau, g = y[5], y[6]
        # Eq. 39. Above Z11 = 500 km the Standard neglects the flux integral
        # ("D(H) becomes very large compared with phi ... the integral term
        # can be neglected at these heights", p. 14) and its tables are
        # computed that way: kept, the term lowers n(H) by 0.25 % at 750 km
        # and 0.30 % at 1000 km against Table VIII; neglected, both agree to
        # the printed digits. At 500 km both forms give n(H)11.
        flux = 0.0 if z > Z11 else math.exp(-tau_500) * (g - g_500)
        result["H"] = ((N_H_11 - flux)
                       * (_T11 / t) ** (1.0 + ALPHA["H"]) * math.exp(-(tau - tau_500)))
    return result
