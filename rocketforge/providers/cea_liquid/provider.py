"""The NASA CEA provider, widened to the LIQ-1 liquid reactants.

**The same pipeline, not a second one.** :class:`CEALiquidProvider` is the
frozen ``CEAThermochemistryProvider`` with three things added in front of it:

1. **Product species for nitrogen and fluorine.** The frozen selection only
   knows C/H/O; asked about an N-bearing reactant it would choose the H/O set
   and the products could not conserve nitrogen. Here the request is given an
   explicit product set -- the frozen request already carries a field for one
   -- from :data:`~.species.PRODUCT_SPECIES_BY_ELEMENTS`, before the frozen
   provider sees it. A pair with no N or F is passed through **untouched**, so
   LOX/CH4, LOX/LH2 and every other accepted case still runs the frozen code
   on the frozen request, bit for bit.
2. **Species records** for those products and reactants, over the combined
   formula table. Again only when a name lies outside the frozen table; a
   C/H/O species set is built by the frozen code exactly as before.
3. **Range checks** for the new reactants, refused with the range named, as
   the frozen provider does for its own cryogens.

Everything else -- the request-to-CEA mapping, the HP solve, unit conversion,
element conservation, state identities, assigned-enthalpy warnings,
provenance -- is the frozen provider's, inherited unchanged. It overrides one
private method, ``_species_for``, and that is stated rather than hidden: the
frozen class builds its species table through it and offers no other seam.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    PropellantDefinition,
    Species,
)
from rocketforge.providers.cea import CEAThermochemistryProvider
from rocketforge.providers.cea.errors import CEAMappingError
from rocketforge.providers.cea.naming import cea_name_for
from rocketforge.providers.cea.species import CEA_FORMULAS

from .propellants import LIQUID_REACTANT_TEMPERATURE_RANGES
from .species import (
    FORMULAS,
    PRODUCT_SPECIES_BY_ELEMENTS,
    build_liquid_species_table,
)

__all__ = [
    "CEALiquidProvider",
    "reactant_cea_names",
    "liquid_product_species",
    "check_liquid_reactant_temperatures",
    "check_product_coverage",
]


def reactant_cea_names(propellant: PropellantDefinition) -> tuple[str, ...]:
    """The CEA reactant names a propellant reaches CEA as.

    A pure propellant through its required ``provider_names['cea']`` entry; a
    blend through its component keys, which are CEA names. The same rule the
    frozen mapping applies.
    """
    entries = propellant.composition.entries
    if len(entries) == 1:
        return (cea_name_for(propellant),)
    return tuple(name for name, _ in entries)


def _elements(request: ChamberEquilibriumRequest) -> set[str]:
    elements: set[str] = set()
    for stream in (request.fuel, request.oxidiser):
        for name in reactant_cea_names(stream.propellant):
            elements.update(FORMULAS.get(name, {}))
    return elements


def _frozen_selection_applies(request: ChamberEquilibriumRequest) -> bool:
    """Whether the frozen product selection sees every reactant correctly.

    The frozen selection reads elements from the *composition keys* through
    the frozen formula table, and a key it does not know contributes nothing.
    Measured consequence: RP-1 (key ``RP-1``, no frozen formula) with LOX was
    read as oxygen-only, given the H/O product set, and CEA aborted the whole
    process on the missing carbon. So the frozen selection is trusted only
    when every composition key and every CEA reactant name is in its own
    table -- which is exactly the accepted Phase 5C set.
    """
    for stream in (request.fuel, request.oxidiser):
        names = [name for name, _ in stream.propellant.composition.entries]
        names.extend(reactant_cea_names(stream.propellant))
        if any(name not in CEA_FORMULAS for name in names):
            return False
    return True


def liquid_product_species(
        request: ChamberEquilibriumRequest) -> tuple[str, ...] | None:
    """The product set this package supplies for a request, or ``None``.

    ``None`` means "not this package's case": the request already names its
    products, or every reactant is one the frozen selection knows, and that
    selection applies exactly as accepted. Otherwise the set is the curated one
    for the reactants' element system, and a system with none is refused.
    """
    if request.product_species is not None or _frozen_selection_applies(request):
        return None
    elements = _elements(request)
    species = PRODUCT_SPECIES_BY_ELEMENTS.get(frozenset(elements))
    if species is None:
        raise CEAMappingError(
            f"no curated product species set covers the elements "
            f"{sorted(elements)} of this propellant pair. It is refused rather "
            "than solved against a set that cannot hold every element.")
    return species


def check_product_coverage(request: ChamberEquilibriumRequest,
                           product_species: tuple[str, ...]) -> None:
    """Refuse a product set missing an element the reactants contain.

    NASA CEA does not return an error for this: it aborts the process
    ("Element lists for products and reactants must match"), taking the
    application with it. A known reactant element absent from every product
    is therefore caught here, as a mapping refusal, before CEA is called.
    """
    reactant_elements = _elements(request)
    product_elements: set[str] = set()
    for name in product_species:
        product_elements.update(FORMULAS.get(name, {}))
    missing = reactant_elements - product_elements
    if missing:
        raise CEAMappingError(
            f"the product species set holds no {sorted(missing)}, which the "
            "reactants contain; NASA CEA cannot conserve them and aborts on "
            "such a request, so it is refused here.")


def check_liquid_reactant_temperatures(request: ChamberEquilibriumRequest) -> None:
    """Refuse a stream outside the range CEA declares for one of its reactants."""
    for role, stream in (("fuel", request.fuel), ("oxidiser", request.oxidiser)):
        temperature = float(stream.temperature)
        for name in reactant_cea_names(stream.propellant):
            bounds = LIQUID_REACTANT_TEMPERATURE_RANGES.get(name)
            if bounds is None:
                continue
            low, high = bounds
            if not low <= temperature <= high:
                raise CEAMappingError(
                    f"the {role} stream {stream.propellant.name!r} is at "
                    f"{temperature} K, outside the range NASA CEA states for "
                    f"reactant {name!r}, [{low}, {high}] K. The provider "
                    "refuses rather than extrapolating its reactant data.")


class CEALiquidProvider(CEAThermochemistryProvider):
    """``CEAThermochemistryProvider`` plus the LIQ-1 reactants. See the module."""

    def _prepare(self, request: ChamberEquilibriumRequest) -> ChamberEquilibriumRequest:
        if not isinstance(request, ChamberEquilibriumRequest):
            return request          # the frozen provider refuses it, by name
        check_liquid_reactant_temperatures(request)
        species = liquid_product_species(request)
        if species is None:
            if request.product_species is not None:
                check_product_coverage(request, request.product_species)
            return request
        check_product_coverage(request, species)
        return replace(request, product_species=species)

    def solve_chamber(self, request, **options):  # type: ignore[override]
        return super().solve_chamber(self._prepare(request), **options)

    def rocket_oracle(self, request, **options):  # type: ignore[override]
        return super().rocket_oracle(self._prepare(request), **options)

    def _species_for(self, product_species: tuple[str, ...],
                     extra: tuple[str, ...] = ()) -> dict[str, Species]:
        names = set(product_species) | set(extra)
        if names <= set(CEA_FORMULAS):
            return super()._species_for(product_species, extra)
        key = tuple(sorted(names))
        cached = self._species_cache.get(key)
        if cached is None:
            resources = self.resources()
            cached = build_liquid_species_table(
                self._cea(), key, database="thermo.lib",
                database_version=resources.thermo_short)
            self._species_cache[key] = cached
        return cached
