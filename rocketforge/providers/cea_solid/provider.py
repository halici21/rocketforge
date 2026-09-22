"""NASA CEA: chamber equilibrium for a solid propellant formulation.

The solid counterpart to :mod:`rocketforge.providers.cea.mapping`'s
bipropellant chamber path, and a separate *package* because it could not be
folded into that one. ``freeze_cea_provider_v1_1`` byte-freezes every module in
``rocketforge/providers/cea`` and separately requires its manifest to cover
that directory exactly, so neither editing ``mapping.py`` to extract a shared
core nor adding a new module beside it is possible.

**What is reused, and what is not.** Every unit conversion goes through the
frozen :mod:`rocketforge.providers.cea.units` helpers, the raw snapshot is the frozen
:class:`rocketforge.providers.cea.mapping.CEARawChamberResult`, condensed mass is the frozen
:func:`rocketforge.providers.cea.mapping.condensed_mass_fraction`, and every CEA call is wrapped by the
frozen :func:`.errors.translate_cea_exception`. Two pieces could not be reused:

* :func:`rocketforge.providers.cea.mapping.solve_chamber_raw` derives its weight vector with
  ``of_ratio_to_weights``. A solid grain has no O/F to derive one from, and
  inventing an O/F to reach that entry point is precisely the fabrication this
  work is not allowed to perform.
* :func:`rocketforge.providers.cea.mapping.to_chamber_gas` stores ``request=request`` on the
  ``ChamberGas`` it returns, and ``ChamberGas.__post_init__`` validates that
  field with ``isinstance(..., ChamberEquilibriumRequest)``. A solid request is
  not one and cannot honestly be made into one, so the assembly happens here
  with ``request=None``.

Dropping the request does not lose traceability. ``ThermochemistryProvenance``
is the field the frozen design designates for reactant input state, and it
carries the formulation: each ingredient's mass fraction and the grain
temperature in ``reactant_conditions``, the formulation name and its published
reference in ``options``, and the product set in ``species_set``.

Deferred to R1.1 and deliberately absent: ``cea.RocketSolver`` is not called
anywhere in this module. No c*, no Cf, no Isp, no expansion of any kind. This
module answers what is in the chamber, not what a nozzle does with it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import ModuleType

import numpy as np

from rocketforge.physics.thermochemistry import (
    ChamberGas,
    Composition,
    CompositionBasis,
    ElementalComposition,
    Phase,
    Species,
    ThermochemistryProvenance,
    specific_gas_constant,
)
from rocketforge.core.result import Diagnostic, Severity
from rocketforge.physics.solid_propellant import (
    SolidFormulation,
    SolidFormulationEquilibriumRequest,
)

from rocketforge.providers.cea.errors import (
    CEAMappingError,
    translate_cea_exception,
)
from rocketforge.providers.cea.mapping import (
    CEARawChamberResult,
    assigned_enthalpy_temperature,
    condensed_mass_fraction,
)
from rocketforge.providers.cea.species import (
    CEA_FORMULAS,
    cea_molar_masses,
    phase_of_cea_name,
)
from rocketforge.providers.cea.units import (
    density_to_si,
    enthalpy_argument,
    molar_mass_to_si,
    pressure_to_bar,
    specific_energy_to_si,
    specific_entropy_to_si,
    specific_heat_to_si,
)

__all__ = [
    "SolidChamberInput",
    "solid_phase_of_cea_name",
    "build_solid_species_table",
    "build_solid_chamber_input",
    "solve_solid_chamber_raw",
    "to_solid_chamber_gas",
    "solve_solid_chamber",
    "solid_reactant_conditions",
    "solid_assigned_enthalpy_diagnostics",
    "check_condensed_count",
    "library_species_available",
]


# ---------------------------------------------------------------------------
# phase, for names the frozen classifier does not cover
# ---------------------------------------------------------------------------

#: Condensed-phase suffixes the solid product set needs and
#: :func:`rocketforge.providers.cea.species.phase_of_cea_name` does not carry.
#:
#: ``rocketforge/providers/cea/species.py`` is frozen, so this cannot be added there. The gap is real and
#: narrow: that table already maps ``(II)`` and ``(III)`` to solid, but not
#: ``(I)``. CEA uses those roman numerals for crystalline polymorphs of one
#: substance, so a database holding ``MgSO4(I)``, ``MgSO4(II)`` and
#: ``MgSO4(L)`` is naming two solid phases and a liquid. Classifying ``(I)`` as
#: anything but solid would put a crystalline polymorph in the gas phase.
#:
#: Evidence, from the RP-1311 Example 5 product set: ``MgSO4(I)`` is returned
#: alongside ``MgSO4(II)`` and ``MgSO4(L)``, and ``NH4CL(II)``/``NH4CL(III)``
#: appear with no ``(I)`` sibling. The reactant ``NH4CLO4(I)`` is likewise a
#: crystalline perchlorate.
_EXTRA_CONDENSED_SUFFIXES = {"(I)": Phase.SOLID}


def solid_phase_of_cea_name(name: str) -> Phase:
    """The phase a CEA name declares, covering the solid product set.

    Defers to the frozen :func:`rocketforge.providers.cea.species.phase_of_cea_name` for everything it
    knows, and only then consults :data:`_EXTRA_CONDENSED_SUFFIXES`. The frozen
    classifier's refusal behaviour is preserved: an unrecognised phase marker
    that is in neither table still raises, rather than defaulting to gas.
    """
    for suffix, phase in _EXTRA_CONDENSED_SUFFIXES.items():
        if name.endswith(suffix):
            return phase
    return phase_of_cea_name(name)


def build_solid_species_table(cea_module: ModuleType,
                              names: Sequence[str],
                              *,
                              database: str = "",
                              database_version: str = "") -> dict[str, Species]:
    """:class:`Species` records for a solid case's product set.

    Not :func:`rocketforge.providers.cea.species.build_species_table`, which refuses any name without a
    curated elemental formula. That table holds 33 C/H/O species; an aluminised
    ammonium-perchlorate grain returns 205 products spanning Al, Cl, N, Mg and
    S, so the curated set covers 23 of them and the frozen builder would refuse
    the case outright.

    Molar mass and phase are real: molar mass comes from CEA itself via the
    frozen :func:`rocketforge.providers.cea.species.cea_molar_masses`, and phase from the name's own
    suffix. The elemental formula is supplied only where curated data exists,
    and is left **empty** otherwise.

    An empty formula is the contract's own way of saying the elemental content
    is not available -- and it genuinely is not. CEA's Python API exposes
    ``num_elements`` as a count and offers no per-species element composition,
    so the alternative would be parsing formulas out of names like
    ``AL(OH)2CL`` and ``CHCO,ketyl``, which is guessing. The documented
    consequence is that these species cannot take part in an element balance;
    R1 performs none, because a chamber equilibrium state is reported, not
    re-derived.
    """
    names = tuple(names)
    masses = cea_molar_masses(cea_module, names)
    table: dict[str, Species] = {}
    for name in names:
        mass_kg_per_kmol = masses.get(name)
        if mass_kg_per_kmol is None:
            raise CEAMappingError(
                f"CEA returned no molar mass for product {name!r}; it is not "
                "dropped, because a missing product would leave the composition "
                "summing to less than one without saying so")
        curated = CEA_FORMULAS.get(name)
        table[name] = Species(
            name=name,
            phase=solid_phase_of_cea_name(name),
            molar_mass=molar_mass_to_si(mass_kg_per_kmol),
            formula=(ElementalComposition.from_mapping(curated)
                     if curated is not None
                     else ElementalComposition(entries=())),
            source=(f"NASA CEA {database or 'thermo.lib'}"
                    f"{(' ' + database_version) if database_version else ''}; "
                    "molar mass and phase from the provider"
                    + ("; formula curated in rocketforge.providers.cea.species"
                       if curated is not None else
                       "; elemental formula not exposed by the provider API")),
        )
    return table


# ---------------------------------------------------------------------------
# request -> CEA input
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SolidChamberInput:
    """Everything CEA needs for one solid chamber solve, in CEA's own terms.

    The solid analogue of :class:`rocketforge.providers.cea.mapping.CEAChamberInput`, and separate from
    it because that one carries ``of_ratio`` and validates it as strictly
    positive. A frozen, inspectable description for the same reason: a test can
    assert what the provider *would* send without CEA being installed.

    Attributes:
        formulation: The grain this input was built from, kept so the solve can
            materialise its custom reactants and so provenance can record it.
        weights: The mass-fraction vector, in ingredient order. Handed to CEA
            directly -- there is no O/F to derive it from.
        reactant_temperatures: K, one per ingredient, in the same order.
        pressure_bar: Chamber pressure in CEA's native unit.
        product_species: An explicit product set, or ``None`` to derive the
            products from the reactants. ``None`` is what NASA's own solid
            examples do and is a real capability, not a fallback.
        omit_species: Products excluded from the solve.
        include_ions: Whether ionised products are considered.
    """

    formulation: SolidFormulation
    weights: tuple[float, ...]
    reactant_temperatures: tuple[float, ...]
    pressure_bar: float
    product_species: tuple[str, ...] | None = None
    omit_species: tuple[str, ...] = ()
    include_ions: bool = False

    def __post_init__(self) -> None:
        n = len(self.formulation.ingredients)
        for label, seq in (("weights", self.weights),
                           ("reactant_temperatures", self.reactant_temperatures)):
            if len(seq) != n:
                raise CEAMappingError(
                    f"{label} has {len(seq)} entries for {n} ingredients")
        total = math.fsum(self.weights)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise CEAMappingError(
                f"weights must sum to 1.0, got {total!r}")
        if not self.pressure_bar > 0.0 or not math.isfinite(self.pressure_bar):
            raise CEAMappingError(
                f"chamber pressure must be positive and finite, got "
                f"{self.pressure_bar!r} bar")


def build_solid_chamber_input(
        request: SolidFormulationEquilibriumRequest) -> SolidChamberInput:
    """Translate a solid request into CEA's terms. No solving happens here."""
    if not isinstance(request, SolidFormulationEquilibriumRequest):
        raise CEAMappingError(
            f"expected a SolidFormulationEquilibriumRequest, got "
            f"{type(request).__name__}")
    formulation = request.formulation
    return SolidChamberInput(
        formulation=formulation,
        weights=formulation.mass_fractions,
        reactant_temperatures=tuple(
            formulation.initial_temperature for _ in formulation.ingredients),
        pressure_bar=pressure_to_bar(request.chamber_pressure),
        product_species=request.product_species,
        omit_species=tuple(request.omit_species),
        include_ions=request.include_ions,
    )


def _materialise_reactants(cea_module: ModuleType,
                           formulation: SolidFormulation) -> list[object]:
    """Build CEA's reactant list, creating custom reactants fresh each time.

    Fresh on every call, never cached at module scope. The ``cea`` library
    holds process-global state, and a ``Reactant`` object carried across two
    solves is exactly the kind of leakage that makes a second run disagree with
    the first for no visible reason.
    """
    out: list[object] = []
    for item in formulation.ingredients:
        if item.custom is None:
            out.append(item.name)
            continue
        custom = item.custom
        kwargs = dict(
            name=item.name,
            formula=dict(custom.formula),
            enthalpy=custom.heat_of_formation,
            enthalpy_units=custom.heat_of_formation_units,
            temperature=custom.reference_temperature,
        )
        # Passed only when the source states it. Absent, CEA derives it from
        # the formula -- and provenance records which of the two happened.
        if custom.molecular_weight is not None:
            kwargs["molecular_weight"] = custom.molecular_weight
        out.append(cea_module.Reactant(**kwargs))
    return out


def solve_solid_chamber_raw(cea_module: ModuleType,
                            chamber_input: SolidChamberInput,
                            ) -> CEARawChamberResult:
    """Run one solid chamber equilibrium and snapshot the answer.

    Mirrors :func:`rocketforge.providers.cea.mapping.solve_chamber_raw` -- same ``EqSolver``, same ``HP``
    constraint, same frozen :func:`.units.enthalpy_argument`, same immediate
    snapshot into :class:`rocketforge.providers.cea.mapping.CEARawChamberResult`. The one difference is
    the weight vector: it is handed over directly instead of being derived from
    an O/F, because a solid grain has no O/F to derive it from.

    ``RocketSolver`` is not used. Chamber properties are the question; an
    expansion nobody asked for is not.
    """
    try:
        reactant_specs = _materialise_reactants(cea_module, chamber_input.formulation)
        reactants = cea_module.Mixture(reactant_specs, ions=chamber_input.include_ions)
        if chamber_input.product_species is None:
            products = cea_module.Mixture(
                reactant_specs,
                products_from_reactants=True,
                omit=list(chamber_input.omit_species),
                ions=chamber_input.include_ions)
        else:
            products = cea_module.Mixture(
                list(chamber_input.product_species),
                omit=list(chamber_input.omit_species),
                ions=chamber_input.include_ions)
        solver = cea_module.EqSolver(products, reactants=reactants)
        solution = cea_module.EqSolution(solver)
    except Exception as exc:  # noqa: BLE001
        raise translate_cea_exception(
            exc, "preparing the solid chamber mixtures") from exc

    try:
        weights = np.asarray(chamber_input.weights, dtype=float)
        mixture_enthalpy = reactants.calc_property(
            cea_module.ENTHALPY, weights,
            list(chamber_input.reactant_temperatures))
        constraint = enthalpy_argument(float(mixture_enthalpy), cea_module.R)
        solver.solve(solution, cea_module.HP, constraint,
                     float(chamber_input.pressure_bar), weights)
    except Exception as exc:  # noqa: BLE001
        raise translate_cea_exception(
            exc, "solving the solid chamber equilibrium") from exc

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


def solid_reactant_conditions(formulation: SolidFormulation) -> dict[str, float]:
    """The formulation, in the shape provenance records reactant state in.

    ``ThermochemistryProvenance.reactant_conditions`` is documented as
    "temperatures and any other reactant state the calculation used", and takes
    any string key with a finite float value. That is where the grain lives,
    because :attr:`ChamberGas.request` cannot hold a solid request.

    Keys are prefixed so an ingredient named ``"temperature"`` could never
    collide with the grain temperature.
    """
    out: dict[str, float] = {
        "initial_temperature_k": formulation.initial_temperature,
    }
    for item in formulation.ingredients:
        out[f"mass_fraction:{item.name}"] = item.mass_fraction
    return out


def to_solid_chamber_gas(raw: CEARawChamberResult,
                         species: Mapping[str, Species],
                         request: SolidFormulationEquilibriumRequest,
                         provenance: ThermochemistryProvenance) -> ChamberGas:
    """Map a raw solid CEA answer onto RocketForge's chamber state.

    Field for field the same mapping :func:`rocketforge.providers.cea.mapping.to_chamber_gas` performs,
    through the same frozen :mod:`rocketforge.providers.cea.units` converters, with one difference that
    could not be avoided: ``request`` is ``None``.

    That frozen function stores ``request=request``, and
    ``ChamberGas.__post_init__`` validates the field with
    ``isinstance(..., ChamberEquilibriumRequest)``. A solid request is not one,
    and making it one would mean inventing a fuel stream, an oxidiser stream
    and an O/F that no solid grain has. The formulation is carried in
    ``provenance`` instead, which is the field the domain designates for
    reactant input state -- see :func:`solid_reactant_conditions`.

    An equivalence test pins this function against the frozen one so the two
    cannot drift apart.
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
        request=None,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def solve_solid_chamber(cea_module: ModuleType,
                        request: SolidFormulationEquilibriumRequest,
                        *,
                        provenance: ThermochemistryProvenance) -> ChamberGas:
    """Solve one solid formulation's chamber equilibrium, end to end.

    The only entry point a caller needs. ``provenance`` is the provider's own
    base record -- who solved this, with which library and database -- and this
    function returns it enriched with what the solid case adds: the product set
    actually considered, the grain's ingredient fractions and temperature, and
    the formulation's name and published reference.

    That enrichment is not decoration. ``ChamberGas.request`` is ``None`` for a
    solid result, so provenance is the *only* record of what went in, and a
    result that cannot say what it was made from is not reproducible.
    """
    chamber_input = build_solid_chamber_input(request)
    raw = solve_solid_chamber_raw(cea_module, chamber_input)

    names = tuple(sorted(raw.mass_fractions))
    species = build_solid_species_table(
        cea_module, names,
        database=provenance.database,
        database_version=provenance.database_version)
    check_condensed_count(species, raw)

    formulation = request.formulation
    options = dict(provenance.options)
    options["solid_formulation"] = formulation.name
    if formulation.reference:
        options["solid_formulation_reference"] = formulation.reference
    options["solid_custom_reactants"] = repr(
        [item.name for item in formulation.custom_ingredients])
    # Ingredient thermochemical provenance: the complete definition of every
    # custom reactant, and where it came from. These are the numbers the
    # chamber state rests on that RocketForge did not compute.
    for item in formulation.custom_ingredients:
        custom = item.custom
        options[f"solid_custom_reactant:{item.name}"] = repr({
            "formula": dict(custom.formula),
            "heat_of_formation": custom.heat_of_formation,
            "heat_of_formation_units": custom.heat_of_formation_units,
            "reference_temperature": custom.reference_temperature,
            "molecular_weight": custom.molecular_weight,
            "molecular_weight_origin": custom.molecular_weight_origin,
        })
        options[f"solid_custom_reactant_source:{item.name}"] = custom.source
    options["solid_omit_species_count"] = str(len(chamber_input.omit_species))
    options["solid_products_from_reactants"] = str(
        chamber_input.product_species is None)

    enriched = replace(
        provenance,
        species_set=names,
        reactant_conditions={
            **dict(provenance.reactant_conditions),
            **solid_reactant_conditions(formulation),
        },
        options=options,
    )
    return to_solid_chamber_gas(raw, species, request, enriched)


# ---------------------------------------------------------------------------
# checks the solid path adds
# ---------------------------------------------------------------------------


def check_condensed_count(species: Mapping[str, Species],
                          raw: CEARawChamberResult) -> None:
    """Require the phase classification to agree with CEA's own count.

    CEA returns gas and condensed products in **one** mapping, not two output
    channels. Measured for Example 5: the 161 gases come first and the 44
    condensed candidates follow as a block. That ordering is an observation
    about one case, not a documented guarantee, so nothing here relies on it --
    which is which is decided from each name's phase suffix, and a test
    shuffles the mapping to prove the answer does not change.
    ``num_condensed`` is CEA's independent statement of how many condensed
    *candidates* the product set holds. The two must agree.

    This is a check on the classification, not on the physics: the counter
    says nothing about how much of each candidate is present (44 candidates,
    one present, in Example 5), which is why condensed *mass* is still read
    from the composition. A disagreement means a product has been put in the
    wrong phase, and the result is refused rather than reported with a phase
    it does not have.
    """
    classified = sum(1 for record in species.values() if record.phase.is_condensed)
    if classified != raw.num_condensed_candidates:
        raise CEAMappingError(
            f"phase classification found {classified} condensed products but "
            f"NASA CEA reports {raw.num_condensed_candidates} condensed "
            "candidates. A product is in the wrong phase; the result is "
            "refused rather than reported with a phase it does not have.")


def solid_assigned_enthalpy_diagnostics(
        cea_module: ModuleType,
        chamber_input: SolidChamberInput) -> tuple[Diagnostic, ...]:
    """Warn when an ingredient's temperature cannot affect the answer.

    The same rule, code and message shape the bipropellant provider uses, so
    the interface shows it with no solid-specific handling. Two sources of an
    assigned enthalpy:

    * a **custom reactant**, whose enthalpy is fixed at the temperature its
      source assigns it. Measured, not assumed: a binder-only CEA mixture
      returns the same enthalpy at 250, 298.15 and 320 K.
    * a **library** entry CEA models the same way, found with the frozen
      :func:`rocketforge.providers.cea.mapping.assigned_enthalpy_temperature`.

    Reported as a warning rather than a refusal, exactly as for a bipropellant:
    the answer is correct for the reactant CEA modelled, but the caller must be
    told the temperature they set did not enter it.
    """
    found: list[Diagnostic] = []
    for item, temperature in zip(chamber_input.formulation.ingredients,
                                 chamber_input.reactant_temperatures):
        if item.custom is not None:
            assigned = item.custom.reference_temperature
            origin = "its source assigns its enthalpy"
        else:
            assigned = assigned_enthalpy_temperature(cea_module, item.name)
            origin = "NASA CEA models it with an assigned enthalpy"
        if assigned is None or abs(temperature - assigned) <= 1.0e-9:
            continue
        found.append(Diagnostic(
            code="PROVIDER_ASSIGNED_ENTHALPY_REACTANT",
            severity=Severity.WARNING,
            message=(
                f"Reactant {item.name!r} carries an assigned enthalpy at "
                f"{assigned} K ({origin}), not a temperature-dependent fit. "
                f"The grain temperature of {temperature} K was accepted and "
                f"did not affect it; the chamber state is the one for "
                f"{item.name!r} at {assigned} K."),
            field="reactant_temperature",
            detail={"requested": float(temperature),
                    "assigned": float(assigned)}))
    return tuple(found)


def library_species_available(cea_module: ModuleType,
                              names: Sequence[str]) -> tuple[str, ...]:
    """The subset of ``names`` the installed ``thermo.lib`` actually holds.

    Probed by building a one-species ``Mixture``, which is the reliable test:
    ``cea.Reactant`` reports some present species -- ``AL(cr)`` among them --
    as absent. Order is preserved. Measured on this build: ``KNO3(cr)`` and
    ``KCLO4(cr)`` are absent.
    """
    present = []
    for name in names:
        try:
            cea_module.Mixture([name])
        except Exception:  # noqa: BLE001 -- absent from this thermo.lib
            continue
        present.append(name)
    return tuple(present)
