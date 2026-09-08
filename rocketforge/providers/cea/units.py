"""The unit boundary between RocketForge and NASA CEA.

**One owner per conversion.** Every transformation between RocketForge's SI and
CEA's native units happens in exactly one function here, and nowhere else in
the adapter. A quantity converted in two places is a quantity that will one day
be converted twice (5C brief §178).

CEA's native units, measured in Phase 5B-0 by identity checks rather than read
off a label:

===============  ==================  ===================  ==================
quantity         CEA native          RocketForge          conversion
===============  ==================  ===================  ==================
pressure         bar                 Pa                   Pa = bar x 1e5
temperature      K                   K                    none
molar mass       kg/kmol             kg/mol               kg/mol = kg/kmol / 1e3
cp, cv           kJ/(kg K)           J/(kg K)             x 1e3
enthalpy         kJ/kg               J/kg                 x 1e3
entropy          kJ/(kg K)           J/(kg K)             x 1e3
density          kg/m3               kg/m3                none
gamma            dimensionless       dimensionless        none
mole fraction    dimensionless       dimensionless        none
===============  ==================  ===================  ==================

How the non-obvious ones were established, not assumed:

* **pressure** -- a solve given 100.0 returned ``P = 100.0`` while the
  ideal-gas identity closed only against 1e7 Pa.
* **cp** -- ``cp_fr - cv_fr = 0.38736`` against a specific gas constant of
  387.36 J/(kg K), i.e. a factor of exactly 1000.
* **molar mass** -- ``M = 21.4644`` with ``p = rho R T`` closing for
  ``R = Ru/M`` only when M is read as kg/kmol.
* **density** -- the same identity closes with density taken as-is, so it is
  already kg/m3. (The sample shipped with CEA prints ``density * 1e-3`` under a
  ``kg/m^3`` label; the identity says the raw value is the one in kg/m3.)

The enthalpy the HP solve is *given* is a further case: CEA wants
``H/R``, a quantity with units of K, not an enthalpy. :func:`enthalpy_argument`
owns that and explains it.
"""

from __future__ import annotations

__all__ = [
    "PA_PER_BAR",
    "KJ_PER_J",
    "KMOL_PER_MOL",
    "pressure_to_bar",
    "pressure_from_bar",
    "molar_mass_to_si",
    "specific_energy_to_si",
    "specific_heat_to_si",
    "specific_entropy_to_si",
    "density_to_si",
    "enthalpy_argument",
]

#: Pa in one bar. Exact by definition.
PA_PER_BAR: float = 1.0e5
#: J in one kJ.
KJ_PER_J: float = 1.0e3
#: mol in one kmol.
KMOL_PER_MOL: float = 1.0e3


def pressure_to_bar(pressure_pa: float) -> float:
    """RocketForge Pa -> CEA bar. The only place this direction happens."""
    return float(pressure_pa) / PA_PER_BAR


def pressure_from_bar(pressure_bar: float) -> float:
    """CEA bar -> RocketForge Pa. The only place this direction happens."""
    return float(pressure_bar) * PA_PER_BAR


def molar_mass_to_si(molar_mass_kg_per_kmol: float) -> float:
    """CEA kg/kmol -> RocketForge kg/mol.

    The conversion most likely to be forgotten, and the one Phase 5B's
    ``Species`` molar-mass ceiling exists to catch when it is.
    """
    return float(molar_mass_kg_per_kmol) / KMOL_PER_MOL


def specific_energy_to_si(value_kj_per_kg: float) -> float:
    """CEA kJ/kg -> RocketForge J/kg."""
    return float(value_kj_per_kg) * KJ_PER_J


def specific_heat_to_si(value_kj_per_kg_k: float) -> float:
    """CEA kJ/(kg K) -> RocketForge J/(kg K)."""
    return float(value_kj_per_kg_k) * KJ_PER_J


def specific_entropy_to_si(value_kj_per_kg_k: float) -> float:
    """CEA kJ/(kg K) -> RocketForge J/(kg K)."""
    return float(value_kj_per_kg_k) * KJ_PER_J


def density_to_si(value: float) -> float:
    """CEA density -> RocketForge kg/m3. Already SI; present for symmetry.

    Exists so that every mapped quantity goes through this module, and so that
    the claim "density needs no conversion" is stated once, with its evidence,
    rather than being an unremarked absence.
    """
    return float(value)


def enthalpy_argument(mixture_enthalpy: float, cea_gas_constant: float) -> float:
    """The value CEA's HP solve expects for the fixed enthalpy.

    CEA takes the constraint as ``H / R``, not as an enthalpy: dividing the
    mixture enthalpy by the universal gas constant leaves a quantity in kelvin,
    which is the form its equilibrium solver is posed in. Both operands come
    from CEA itself -- ``Mixture.calc_property(ENTHALPY, ...)`` and ``cea.R`` --
    so the pair is self-consistent and **RocketForge's CODATA constant must not
    be substituted here**. Using ours would introduce a 5.7e-06 inconsistency
    into the solver's own input, which is a different and worse thing than the
    known 5.7e-06 difference in the *reported* properties.
    """
    return float(mixture_enthalpy) / float(cea_gas_constant)
