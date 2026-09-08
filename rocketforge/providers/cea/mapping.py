"""Request -> CEA, and CEA -> RocketForge.

The adapter proper. Split so that the parts which need no chemistry library are
pure functions: :func:`build_chamber_input` turns a validated RocketForge
request into a description of what CEA will be asked, and can be tested --
including its O/F orientation and its temperature sourcing -- in the base
environment with no provider installed at all.

Ordering discipline, from the 5C brief §29: the request validates itself, then
this module validates what is provider-specific, and only then is CEA called.
Nothing reaches the solver unchecked. That is not tidiness: Phase 5B-0 measured
NASA CEA accepting a negative temperature and a negative pressure without
complaint and returning a plausible-looking number.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import ModuleType

import numpy as np

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    Phase,
    PropellantDefinition,
    Species,
    ThermochemistryProvenance,
    specific_gas_constant,
)

from .errors import CEAMappingError, translate_cea_exception
from .naming import PROVIDER_ID, cea_name_for, check_name
from .propellants import CEA_REACTANT_TEMPERATURE_RANGES
from .species import (
    CHO_PRODUCT_SPECIES,
    HO_PRODUCT_SPECIES,
    build_species_table,
)
from .units import (
    density_to_si,
    enthalpy_argument,
    molar_mass_to_si,
    pressure_to_bar,
    specific_energy_to_si,
    specific_entropy_to_si,
    specific_heat_to_si,
)

__all__ = [
    "CEAChamberInput",
    "CEARawChamberResult",
    "build_chamber_input",
    "select_product_species",
    "solve_chamber_raw",
    "to_chamber_gas",
    "assigned_enthalpy_temperature",
]


# ---------------------------------------------------------------------------
# request -> CEA input
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CEAChamberInput:
    """Everything CEA needs for one chamber solve, in CEA's own terms.

    A frozen, inspectable description rather than a set of positional
    arguments, so a test can assert what the provider *would* send without a
    provider being installed.

    Attributes:
        reactant_names: CEA reactant identifiers, fuel components first.
        fuel_weights: Relative mass of each reactant slot on the fuel side.
        oxidiser_weights: The same on the oxidiser side. The two are disjoint.
        reactant_temperatures: K, one per reactant slot, in the same order.
        of_ratio: Oxidiser mass over fuel mass. RocketForge's orientation,
            which is also CEA's.
        pressure_bar: Chamber pressure in CEA's native unit.
        product_species: The product set the solve is restricted to.
        enthalpy_correction: J/kg of propellant mixture, added to the enthalpy
            CEA computes for the reactants before it becomes the HP constraint.
            **Added in NASA CEA Provider v1.1**, defaulted to 0.0 so that every
            v1.0 caller and every v1.0 result is unchanged. Non-zero only under
            ``ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION``; see
            ``enthalpy_coupling.py`` for what the number means and why it is a
            difference rather than an absolute enthalpy.
    """

    reactant_names: tuple[str, ...]
    fuel_weights: tuple[float, ...]
    oxidiser_weights: tuple[float, ...]
    reactant_temperatures: tuple[float, ...]
    of_ratio: float
    pressure_bar: float
    product_species: tuple[str, ...]
    enthalpy_correction: float = 0.0

    def __post_init__(self) -> None:
        n = len(self.reactant_names)
        for name, seq in (("fuel_weights", self.fuel_weights),
                          ("oxidiser_weights", self.oxidiser_weights),
                          ("reactant_temperatures", self.reactant_temperatures)):
            if len(seq) != n:
                raise CEAMappingError(
                    f"{name} has {len(seq)} entries for {n} reactants")
        if not self.of_ratio > 0.0 or not math.isfinite(self.of_ratio):
            raise CEAMappingError(f"O/F must be positive and finite, got {self.of_ratio!r}")
        if not self.pressure_bar > 0.0 or not math.isfinite(self.pressure_bar):
            raise CEAMappingError(
                f"chamber pressure must be positive and finite, got {self.pressure_bar!r} bar")
        if not math.isfinite(self.enthalpy_correction):
            raise CEAMappingError(
                f"enthalpy correction must be finite, got "
                f"{self.enthalpy_correction!r} J/kg")

    @property
    def fuel_names(self) -> tuple[str, ...]:
        return tuple(n for n, w in zip(self.reactant_names, self.fuel_weights) if w > 0.0)

    @property
    def oxidiser_names(self) -> tuple[str, ...]:
        return tuple(n for n, w in zip(self.reactant_names, self.oxidiser_weights) if w > 0.0)


def _component_cea_names(propellant: PropellantDefinition) -> tuple[str, ...]:
    """CEA names for a propellant's component species.

    A single-species propellant uses its ``provider_names['cea']`` entry, which
    is required: RocketForge calls it ``LOX`` and CEA calls it ``O2(L)``.

    A **blend** uses its component species keys directly as CEA names. That is a
    Phase 5C limitation, stated rather than hidden: ``PropellantDefinition``
    carries one provider name for the substance, not one per component, and
    adding a per-component mapping would be a domain change made for an
    adapter's convenience. Blends whose component keys are already valid CEA
    species names work today; anything else needs the domain extension, and
    will say so through :class:`CEAMappingError` rather than guessing.
    """
    entries = propellant.composition.entries
    if len(entries) == 1:
        return (cea_name_for(propellant),)
    names = []
    for species_name, _ in entries:
        names.append(check_name(
            species_name,
            f"blend component {species_name!r} of {propellant.name!r}"))
    return tuple(names)


def _component_mass_weights(
    propellant: PropellantDefinition,
    molar_masses: Mapping[str, float] | None,
) -> tuple[float, ...]:
    """Relative masses of a propellant's components, on a mass basis.

    CEA reactant weights are masses. A mass-basis blend passes straight
    through; a mole-basis blend is converted using the domain's own conversion,
    which needs molar masses -- supplied by the caller, from CEA, so the
    numbers are the provider's own.
    """
    composition = propellant.composition
    if len(composition.entries) == 1:
        return (1.0,)
    if composition.basis is CompositionBasis.MASS_FRACTION:
        return tuple(value for _, value in composition.entries)
    if molar_masses is None:
        raise CEAMappingError(
            f"blend {propellant.name!r} is stated on a mole basis, so mapping "
            "it to CEA mass weights needs molar masses; none were supplied")
    missing = [n for n, _ in composition.entries if n not in molar_masses]
    if missing:
        raise CEAMappingError(
            f"no molar mass available for blend components {missing!r} of "
            f"{propellant.name!r}")
    table = {
        name: Species(name=name, phase=propellant.reference_phase,
                      molar_mass=molar_masses[name])
        for name, _ in composition.entries
    }
    converted = composition.to_basis(CompositionBasis.MASS_FRACTION, table)
    return tuple(value for _, value in converted.entries)


def assigned_enthalpy_temperature(cea_module: ModuleType, cea_name: str
                                  ) -> float | None:
    """The temperature a reactant's enthalpy is fixed at, or ``None``.

    A genuine and easily-missed property of NASA CEA's reactant library: some
    entries -- the cryogenic liquids among them -- carry a single **assigned
    enthalpy** at one reference condition rather than a temperature-dependent
    fit. For those, the temperature handed to ``calc_property`` is accepted and
    then **ignored**, so a caller who sets liquid oxygen to 95 K silently gets
    the 90.17 K answer.

    RocketForge refuses to pass that silence on. This function determines the
    behaviour **empirically**, by evaluating the reactant's enthalpy at two
    temperatures inside its declared range and seeing whether the answer moves.
    Probing beats pattern-matching on the range width: it cannot be wrong about
    a reactant it has actually measured.

    Returns the assigned temperature when the enthalpy is fixed, and ``None``
    when the reactant genuinely responds to temperature.
    """
    try:
        low, high = cea_module.Reactant(cea_name).get_valid_temperature_range()
    except Exception:  # noqa: BLE001 - not every name is a library reactant
        return None
    low, high = float(low), float(high)
    if not high > low:
        return None

    mixture = cea_module.Mixture([cea_name])
    weights = np.array([1.0], dtype=float)
    lower = low + 0.25 * (high - low)
    upper = low + 0.75 * (high - low)
    try:
        at_lower = float(mixture.calc_property(cea_module.ENTHALPY, weights, [lower]))
        at_upper = float(mixture.calc_property(cea_module.ENTHALPY, weights, [upper]))
    except Exception:  # noqa: BLE001
        return None
    if at_lower == at_upper:
        # Fixed. The assigned condition is the midpoint of the declared range:
        # every assigned-enthalpy reactant in the library declares its range as
        # the assigned temperature plus and minus 10 K.
        return 0.5 * (low + high)
    return None


def _check_reactant_temperature(cea_name: str, temperature: float,
                                label: str) -> None:
    """Refuse a stream outside the range CEA states for that reactant.

    A refusal that names the range. CEA's liquid reactant entries are fits over
    a narrow band around the normal boiling point; asking for liquid oxygen at
    300 K is not a small extrapolation, it is a different substance.
    """
    bounds = CEA_REACTANT_TEMPERATURE_RANGES.get(cea_name)
    if bounds is None:
        return
    low, high = bounds
    if not low <= temperature <= high:
        raise CEAMappingError(
            f"{label} is at {temperature} K, outside the range NASA CEA states "
            f"for reactant {cea_name!r}, [{low}, {high}] K. The provider "
            "refuses rather than extrapolating its reactant data.")


def select_product_species(request: ChamberEquilibriumRequest) -> tuple[str, ...]:
    """The product set for a request.

    An explicit ``request.product_species`` wins. Otherwise the set is chosen
    from the elements present in the reactants: a carbon-free system gets the
    hydrogen/oxygen set, because including carbon species where there is no
    carbon adds nothing but zeros.

    The set actually used is recorded in provenance, so a result always says
    which species it was solved with (see ``species.py`` for the measured cost
    of this curated set versus CEA's full automatic selection).
    """
    if request.product_species is not None:
        return tuple(request.product_species)
    elements: set[str] = set()
    for stream in (request.fuel, request.oxidiser):
        for name, _ in stream.propellant.composition.entries:
            from .species import CEA_FORMULAS
            elements.update(CEA_FORMULAS.get(name, {}))
    if "C" in elements:
        return CHO_PRODUCT_SPECIES
    return HO_PRODUCT_SPECIES


def build_chamber_input(
    request: ChamberEquilibriumRequest,
    *,
    molar_masses: Mapping[str, float] | None = None,
    enthalpy_correction: float = 0.0,
) -> CEAChamberInput:
    """Turn a validated RocketForge request into a CEA chamber description.

    Pure: no chemistry library is imported or called. Everything a test needs
    in order to check the O/F orientation, the temperature sourcing, the phase
    mapping and the unit conversion is decided here.

    The request has already validated itself -- positive temperature, positive
    pressure, positive O/F, roles checked. What this adds is provider-specific:
    CEA names exist, names fit CEA's field width, reactant temperatures lie in
    the ranges CEA states.
    """
    if request.equilibrium_constraint is not EquilibriumConstraint.HP:
        raise CEAMappingError(
            f"this provider solves the chamber at constant enthalpy and "
            f"pressure; {request.equilibrium_constraint.value} was requested. "
            "The constraint is not silently substituted.")
    if request.chemistry_mode is not ChemistryMode.EQUILIBRIUM:
        raise CEAMappingError(
            f"chamber chemistry mode {request.chemistry_mode.value} is not "
            "supported by this provider")

    fuel_names = _component_cea_names(request.fuel.propellant)
    oxidiser_names = _component_cea_names(request.oxidiser.propellant)
    fuel_masses = _component_mass_weights(request.fuel.propellant, molar_masses)
    oxidiser_masses = _component_mass_weights(request.oxidiser.propellant, molar_masses)

    overlap = set(fuel_names) & set(oxidiser_names)
    if overlap:
        raise CEAMappingError(
            f"the same CEA reactant {sorted(overlap)!r} appears on both the "
            "fuel and the oxidiser side; CEA cannot distinguish them, so the "
            "mixture ratio would be meaningless")

    names = fuel_names + oxidiser_names
    n_fuel = len(fuel_names)
    fuel_weights = tuple(fuel_masses) + (0.0,) * len(oxidiser_names)
    oxidiser_weights = (0.0,) * n_fuel + tuple(oxidiser_masses)

    # The actual stream temperatures, never the definitions' reference values.
    # Phase 5B-0 measured that substitution as 74.9 K of chamber temperature.
    temperatures = ((float(request.fuel.temperature),) * n_fuel
                    + (float(request.oxidiser.temperature),) * len(oxidiser_names))

    for name in fuel_names:
        _check_reactant_temperature(name, float(request.fuel.temperature),
                                    f"the fuel stream {request.fuel.propellant.name!r}")
    for name in oxidiser_names:
        _check_reactant_temperature(name, float(request.oxidiser.temperature),
                                    f"the oxidiser stream {request.oxidiser.propellant.name!r}")

    return CEAChamberInput(
        reactant_names=names,
        fuel_weights=fuel_weights,
        oxidiser_weights=oxidiser_weights,
        reactant_temperatures=temperatures,
        # RocketForge's O/F is oxidiser mass over fuel mass, and so is CEA's.
        of_ratio=request.of_mass,
        pressure_bar=pressure_to_bar(request.chamber_pressure),
        product_species=select_product_species(request),
        # v1.1, defaulted to zero: a caller that says nothing gets exactly the
        # v1.0 description, byte for byte.
        enthalpy_correction=float(enthalpy_correction),
    )


# ---------------------------------------------------------------------------
# CEA -> raw snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CEARawChamberResult:
    """CEA's answer, copied out into plain Python in CEA's native units.

    A snapshot, taken immediately. CEA's solution object is a reused mutable
    carrier, so nothing beyond this boundary ever holds a reference to it --
    the values are read once, converted to ``float``/``dict``, and the provider
    object is free to be reused for the next solve.

    Units here are **CEA's**: bar, kJ/(kg K), kg/kmol. Conversion happens in
    :func:`to_chamber_gas`, once.
    """

    converged: bool
    temperature_k: float
    pressure_bar: float
    density: float
    molar_mass_kg_per_kmol: float
    molar_mass_1_over_n: float
    enthalpy_kj_per_kg: float
    entropy_kj_per_kg_k: float
    gamma_s: float
    cp_frozen_kj: float
    cv_frozen_kj: float
    cp_equilibrium_kj: float
    cv_equilibrium_kj: float
    mole_fractions: Mapping[str, float]
    mass_fractions: Mapping[str, float]
    num_condensed_candidates: int
    num_gas: int
    num_products: int
    cea_gas_constant: float
    raw_mole_fraction_sum: float = 0.0


def solve_chamber_raw(cea_module: ModuleType,
                      chamber_input: CEAChamberInput) -> CEARawChamberResult:
    """Run one chamber equilibrium and snapshot the answer.

    Uses ``EqSolver`` with the ``HP`` constraint directly -- the most direct
    official API for a chamber equilibrium. The full rocket solver is *not*
    used merely to obtain chamber properties: it would solve an expansion
    nobody asked for and would make the chamber state a by-product of a nozzle
    calculation that Phase 5C does not own.
    """
    names = list(chamber_input.reactant_names)
    try:
        reactants = cea_module.Mixture(names)
        products = cea_module.Mixture(list(chamber_input.product_species))
        solver = cea_module.EqSolver(products, reactants=reactants)
        solution = cea_module.EqSolution(solver)
    except Exception as exc:  # noqa: BLE001
        raise translate_cea_exception(exc, "preparing the chamber mixtures") from exc

    try:
        weights = reactants.of_ratio_to_weights(
            np.asarray(chamber_input.oxidiser_weights, dtype=float),
            np.asarray(chamber_input.fuel_weights, dtype=float),
            float(chamber_input.of_ratio))
        mixture_enthalpy = reactants.calc_property(
            cea_module.ENTHALPY, weights,
            list(chamber_input.reactant_temperatures))
        # v1.1: a sensible-enthalpy increment, in J/kg of mixture, on CEA's own
        # mass basis. Zero under the v1.0 native policy, which is why every
        # accepted Phase 5 number is reproduced bit for bit. The addition
        # happens here, before the division by CEA's own R, so the corrected
        # constraint stays in the units CEA posed its solver in.
        corrected = float(mixture_enthalpy) + float(
            chamber_input.enthalpy_correction)
        constraint = enthalpy_argument(corrected, cea_module.R)
        solver.solve(solution, cea_module.HP, constraint,
                     float(chamber_input.pressure_bar), weights)
    except Exception as exc:  # noqa: BLE001
        raise translate_cea_exception(exc, "solving the chamber equilibrium") from exc

    mole = {str(k): float(v) for k, v in solution.mole_fractions.items()}
    mass = {str(k): float(v) for k, v in solution.mass_fractions.items()}

    return CEARawChamberResult(
        converged=bool(solution.converged),
        temperature_k=float(solution.T),
        pressure_bar=float(solution.P),
        density=float(solution.density),
        molar_mass_kg_per_kmol=float(solution.MW),
        molar_mass_1_over_n=float(solution.M),
        enthalpy_kj_per_kg=float(solution.enthalpy),
        entropy_kj_per_kg_k=float(solution.entropy),
        gamma_s=float(solution.gamma_s),
        cp_frozen_kj=float(solution.cp_fr),
        cv_frozen_kj=float(solution.cv_fr),
        cp_equilibrium_kj=float(solution.cp_eq),
        cv_equilibrium_kj=float(solution.cv_eq),
        mole_fractions=mole,
        mass_fractions=mass,
        num_condensed_candidates=int(solver.num_condensed),
        num_gas=int(solver.num_gas),
        num_products=int(solver.num_products),
        cea_gas_constant=float(cea_module.R),
        raw_mole_fraction_sum=math.fsum(mole.values()),
    )


# ---------------------------------------------------------------------------
# raw -> ChamberGas
# ---------------------------------------------------------------------------


def condensed_mass_fraction(raw: CEARawChamberResult,
                            species: Mapping[str, Species]) -> float:
    """How much condensed material is actually present, by mass.

    Computed from the **returned composition**, never from
    ``num_condensed``. Phase 5B-0 found that counter reporting three condensed
    candidates while all three were present at exactly zero -- and the same
    thing happens in Phase 5C's own production case, where ``C(gr)``,
    ``H2O(L)`` and ``H2O(cr)`` are candidates and none is present (ADR-28).
    """
    total = 0.0
    for name, value in raw.mass_fractions.items():
        record = species.get(name)
        if record is not None and record.phase.is_condensed:
            total += value
    return total


def to_chamber_gas(
    raw: CEARawChamberResult,
    species: Mapping[str, Species],
    request: ChamberEquilibriumRequest,
    provenance: ThermochemistryProvenance,
) -> ChamberGas:
    """Map a raw CEA answer onto RocketForge's chamber state.

    Every unit conversion goes through :mod:`.units`. Every field CEA does not
    supply is left ``None`` rather than invented.

    Two mapping decisions worth stating:

    * **cp and cv carry the frozen pair.** Only the frozen pair satisfies
      ``cp - cv = R``; the equilibrium pair does not and is not meant to.
      Both are preserved, in ``cp_frozen`` and ``cp_equilibrium``.
    * **R is derived from RocketForge's CODATA constant**, not from CEA's.
      CEA returns a molar mass, not a gas constant, so R has to be derived, and
      deriving it with our constant is what makes ``R = Ru/M`` close exactly.
      The consequence -- CEA's own ``cp - cv`` and ``p = rho R T`` then miss ours
      by 5.7e-06 -- is absorbed by ``provider_identity_rel_tol``, which exists
      for precisely this and is tested against it.
    """
    molar_mass = molar_mass_to_si(raw.molar_mass_kg_per_kmol)
    composition = Composition.from_fractions(
        raw.mole_fractions,
        CompositionBasis.MOLE_FRACTION,
        database=provenance.database,
        database_version=provenance.database_version or provenance.database_sha256[:16],
    )
    cp = specific_heat_to_si(raw.cp_frozen_kj)
    cv = specific_heat_to_si(raw.cv_frozen_kj)

    return ChamberGas(
        temperature=raw.temperature_k,
        gamma=raw.gamma_s,
        gas_constant=specific_gas_constant(molar_mass),
        molar_mass=molar_mass,
        composition=composition,
        pressure=request.chamber_pressure,
        density=density_to_si(raw.density),
        enthalpy=specific_energy_to_si(raw.enthalpy_kj_per_kg),
        entropy=specific_entropy_to_si(raw.entropy_kj_per_kg_k),
        cp=cp,
        cv=cv,
        cp_frozen=cp,
        cp_equilibrium=specific_heat_to_si(raw.cp_equilibrium_kj),
        gamma_frozen=raw.cp_frozen_kj / raw.cv_frozen_kj,
        gamma_equilibrium=raw.gamma_s,
        condensed_mass_fraction=condensed_mass_fraction(raw, species),
        request=request,
        provenance=provenance,
    )
