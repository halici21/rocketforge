"""What RocketForge reported, as comparable quantities.

Reads a :class:`~rocketforge.physics.thermochemistry.ChamberGas` -- the result
both the bipropellant and the solid path produce -- and names each value the
way reference cases name theirs. Nothing is recomputed: every number here is a
field the result already carries, in the unit it carries it in.
"""

from __future__ import annotations

from collections.abc import Mapping

from rocketforge.physics.thermochemistry import ChamberGas, CompositionBasis

from .compare import ObservedQuantity

__all__ = ["observed_from_chamber"]


def observed_from_chamber(
        chamber: ChamberGas,
        *,
        mass_fractions: Mapping[str, float] | None = None,
        characteristic_velocity: float | None = None,
) -> dict[str, ObservedQuantity]:
    """Every comparable quantity a chamber result carries.

    ``mass_fractions`` is optional because the composition is held on a mole
    basis and converting needs each species' molar mass, which a caller has
    from its provider and this layer deliberately does not. Mole fractions are
    always available. ``characteristic_velocity`` is passed in, not derived:
    it comes from a separate CEA solve with its own validity checks, and is
    only given when those passed.
    """
    out: dict[str, ObservedQuantity] = {}

    def put(key: str, value: float | None, unit: str) -> None:
        if value is not None:
            out[key] = ObservedQuantity(key, float(value), unit)

    put("chamber_temperature", chamber.temperature, "K")
    put("chamber_pressure", chamber.pressure, "Pa")
    put("molar_mass", chamber.molar_mass, "kg/mol")
    put("gamma_s", chamber.gamma_equilibrium, "1")
    put("gamma_frozen", chamber.gamma_frozen, "1")
    put("density", chamber.density, "kg/m^3")
    put("enthalpy", chamber.enthalpy, "J/kg")
    put("entropy", chamber.entropy, "J/(kg*K)")
    put("cp_equilibrium", chamber.cp_equilibrium, "J/(kg*K)")
    put("cp_frozen", chamber.cp_frozen, "J/(kg*K)")
    put("cv_frozen", chamber.cv, "J/(kg*K)")
    put("condensed_mass_fraction", chamber.condensed_mass_fraction, "1")
    put("characteristic_velocity", characteristic_velocity, "m/s")

    # The basis is read from the composition, never assumed: a mass-basis
    # composition keyed as mole fractions would compare the wrong quantity
    # with perfect-looking precision.
    composition = chamber.composition
    prefix = {CompositionBasis.MOLE_FRACTION: "mole_fraction",
              CompositionBasis.MASS_FRACTION: "mass_fraction"}.get(composition.basis)
    if prefix is None:
        raise ValueError(f"unsupported composition basis {composition.basis!r}")
    for name in composition.species_names:
        put(f"{prefix}:{name}", composition.fraction_of(name), "1")
    for name, value in (mass_fractions or {}).items():
        put(f"mass_fraction:{name}", value, "1")
    return out
