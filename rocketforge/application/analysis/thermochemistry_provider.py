"""The application's only door to a thermochemistry provider.

Two responsibilities, and deliberately no third:

1. **Availability.** Answer whether a provider can be used, without crashing
   and without pretending. The base environment ships no chemistry library at
   all, and that is a supported configuration, not an error state.
2. **Ownership of the provider instance.** One provider, constructed once,
   reused. Nothing above this module constructs one, and nothing above it
   imports :mod:`rocketforge.providers.cea`.

**Every provider import in this file is function-local, on purpose.** ``main.py``
constructs the thermochemistry controller at start-up so QML has a singleton to
bind to, and the controller imports this module. If that chain pulled in the
provider package, a normal launch would pay for a workspace the user has not
opened -- 181 ms of package import, and, on first use, the native CEA library
and its thermodynamic database. Phase 5C kept provider loading lazy; Phase 5D
keeps it lazy. An architecture test holds the line.

The gateway is Qt-free, so the whole availability/catalogue story is testable
headlessly, including the "nothing installed" branch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "ProviderAvailability",
    "PropellantOption",
    "availability",
    "chamber_provider",
    "propellant_options",
    "propellant_named",
    "provider_temperature_range",
    "reset_provider_state",
    "PROVIDER_LABEL",
    "MODEL_SUMMARY",
    "CHEMISTRY_MODE_LABEL",
    "CONSTRAINT_LABEL",
    "NOT_INSTALLED_REMEDY",
    "solid_formulation_templates",
    "solid_omit_species",
    "solid_species_table",
    "solve_solid_chamber_state",
    "provider_provenance",
    "solid_ingredient_catalogue",
    "solid_phase_label",
    "solid_validated_pressures",
    "solve_solid_equilibrium_cstar",
    "solid_assigned_enthalpy_diagnostics",
]

#: What the interface calls the provider. The machine id stays ``"cea"``.
PROVIDER_LABEL = "NASA CEA"

#: The one-line model statement shown beside every chamber result.
MODEL_SUMMARY = "HP Equilibrium · Adiabatic"

CHEMISTRY_MODE_LABEL = "Equilibrium"
CONSTRAINT_LABEL = "HP — constant enthalpy and pressure"

#: Said on the unavailable screen. Names the profile rather than a bare package
#: so the instruction is actually followable.
NOT_INSTALLED_REMEDY = (
    "Install the thermochemistry dependency profile "
    "(requirements-thermochemistry.txt) into this environment, or use the "
    "packaged RocketForge application, which ships the provider."
)


@dataclass(frozen=True, slots=True)
class ProviderAvailability:
    """Whether a thermochemistry provider can be used, and why not.

    A view model, not a re-implementation: ``status`` is the provider's own
    status value, carried through rather than reinterpreted, so the interface
    can never disagree with the library about what is installed.
    """

    status: str
    usable: bool
    label: str = PROVIDER_LABEL
    version: str = ""
    library_version: str = ""
    detail: str = ""
    remedy: str = ""

    @property
    def headline(self) -> str:
        """One line naming the provider and its state."""
        if self.usable:
            version = self.library_version or self.version
            return f"{self.label} {version}".strip()
        return f"{self.label} unavailable"


@dataclass(frozen=True, slots=True)
class PropellantOption:
    """One selectable reactant, as the interface needs to describe it.

    ``provider_name`` and ``temperature_range`` are the provider's own facts and
    belong in a details area, not in the primary workflow (Phase 5D §17): the
    user picks "LOX", and can find out that CEA calls it ``O2(L)``.
    """

    key: str
    label: str
    role: str
    phase: str
    reference_temperature: float
    provider_name: str = ""
    temperature_range: tuple[float, float] | None = None
    density_hint: float | None = None
    source: str = ""
    definition: Any = field(default=None, repr=False, compare=False)

    @property
    def is_fuel(self) -> bool:
        return self.role == "fuel"

    @property
    def is_oxidiser(self) -> bool:
        return self.role == "oxidiser"

    @property
    def range_text(self) -> str:
        """The provider's declared valid stream-temperature range, or empty."""
        if self.temperature_range is None:
            return ""
        low, high = self.temperature_range
        return f"{low:g} – {high:g} K"


# ---------------------------------------------------------------------------
# lazily resolved state
# ---------------------------------------------------------------------------

_availability: ProviderAvailability | None = None
_provider: Any = None
_options: tuple[PropellantOption, ...] | None = None


def reset_provider_state() -> None:
    """Drop everything cached here.

    Exists for tests, which need to simulate a machine with and without the
    library inside one process. Nothing in the application calls it.
    """
    global _availability, _provider, _options, _solid_catalogue
    _availability = None
    _provider = None
    _options = None
    _solid_catalogue = None


def availability(*, refresh: bool = False) -> ProviderAvailability:
    """Whether a thermochemistry provider is usable in this environment.

    Never raises. An import failure of the *adapter* -- not of the chemistry
    library, which the adapter already handles -- is reported as an unusable
    provider carrying the exception text, because a workspace that cannot say
    why it is empty is worse than one that can.
    """
    global _availability
    if _availability is not None and not refresh:
        return _availability

    try:
        from rocketforge.providers.cea import PROVIDER_VERSION, check_availability
    except Exception as exc:  # noqa: BLE001 - the adapter itself failed to load
        _availability = ProviderAvailability(
            status="adapter_load_failed", usable=False,
            detail=f"{type(exc).__name__}: {exc}",
            remedy="This is a RocketForge defect rather than a missing "
                   "dependency; the provider adapter could not be imported.")
        return _availability

    status = check_availability()
    _availability = ProviderAvailability(
        status=status.status.value,
        usable=bool(status.is_usable),
        version=PROVIDER_VERSION,
        library_version=status.library_version or status.version or "",
        detail=status.detail or "",
        remedy=NOT_INSTALLED_REMEDY if not status.is_usable else "",
    )
    return _availability


def chamber_provider() -> Any:
    """The shared provider instance, or ``None`` when none is usable.

    Returns ``None`` rather than raising: "no provider installed" is a
    first-class screen in this workspace, not an exception path.
    """
    global _provider
    if _provider is not None:
        return _provider
    if not availability().usable:
        return None
    from rocketforge.providers.cea import CEAThermochemistryProvider

    _provider = CEAThermochemistryProvider()
    return _provider


# ---------------------------------------------------------------------------
# the reactant catalogue
# ---------------------------------------------------------------------------


def propellant_options() -> tuple[PropellantOption, ...]:
    """The reactants this build can actually map, in a stable order.

    Read from the provider package's production set rather than restated here.
    Phase 5C validated exactly five definitions end to end, and a selector
    offering a sixth would be offering something the backend cannot map -- the
    failure mode Phase 5D §15 rules out.

    Importing the *adapter package* works with no chemistry library installed,
    so the catalogue is available even on the unavailable screen, where it is
    used to describe what the workspace would be able to do.
    """
    global _options
    if _options is not None:
        return _options

    try:
        from rocketforge.providers.cea.naming import PROVIDER_ID
        from rocketforge.providers.cea.propellants import (
            CEA_REACTANT_TEMPERATURE_RANGES,
            PRODUCTION_PROPELLANTS,
        )
    except Exception:  # noqa: BLE001 - no catalogue is a usable state here
        _options = ()
        return _options

    options: list[PropellantOption] = []
    for definition in PRODUCTION_PROPELLANTS.values():
        provider_name = definition.provider_names.get(PROVIDER_ID, "")
        options.append(PropellantOption(
            key=definition.name,
            label=_display_label(definition.name),
            role=str(definition.role.value),
            phase=str(definition.reference_phase.value),
            reference_temperature=float(definition.reference_temperature),
            provider_name=provider_name,
            temperature_range=CEA_REACTANT_TEMPERATURE_RANGES.get(provider_name),
            density_hint=(None if definition.density_hint is None
                          else float(definition.density_hint)),
            source=definition.source,
            definition=definition,
        ))
    _options = tuple(options)
    return _options


#: Display names for the shipped set. The canonical name stays the identifier;
#: this is presentation only, and an unlisted name falls through unchanged
#: rather than being invented.
_DISPLAY_LABELS = {
    "LOX": "LOX — liquid oxygen",
    "LCH4": "LCH4 — liquid methane",
    "LH2": "LH2 — liquid hydrogen",
    "GOX": "GOX — gaseous oxygen",
    "GCH4": "GCH4 — gaseous methane",
}


def _display_label(name: str) -> str:
    return _DISPLAY_LABELS.get(name, name)


def propellant_named(key: str) -> PropellantOption | None:
    """One catalogue entry by its canonical name, or ``None``."""
    for option in propellant_options():
        if option.key == key:
            return option
    return None


def provider_temperature_range(key: str) -> tuple[float, float] | None:
    """The provider's declared stream-temperature range for a reactant."""
    option = propellant_named(key)
    return None if option is None else option.temperature_range


# ---------------------------------------------------------------------------
# the solid path
# ---------------------------------------------------------------------------
#
# These sit here, in the gateway, for the same reason everything else provider-
# shaped does: this module is the one door to ``rocketforge.providers``, so
# there is one place to change when the provider changes. The solid service
# above calls these and never names the provider package itself.


def solid_formulation_templates() -> dict[str, Any]:
    """The reference solid formulations this build offers, by key.

    R1 ships exactly one, and it is a published validation case rather than a
    design starting point. Imported lazily, like every other provider import in
    this module.
    """
    from rocketforge.providers.cea_solid import RP1311_EXAMPLE5

    return {"rp1311-example5": RP1311_EXAMPLE5}


def solid_omit_species(formulation_key: str | None) -> tuple[str, ...]:
    """Products a reference case excludes, verbatim from its published input.

    Reproducing a published number requires reproducing its omissions. A
    formulation that is not a published case carries none.
    """
    if formulation_key != "rp1311-example5":
        return ()
    from rocketforge.providers.cea_solid import RP1311_EXAMPLE5_OMIT

    return RP1311_EXAMPLE5_OMIT


def solid_validated_pressures(formulation_key: str | None) -> tuple[float, ...]:
    """Pa. The chamber pressures a reference case publishes results at."""
    if formulation_key != "rp1311-example5":
        return ()
    from rocketforge.providers.cea.units import pressure_from_bar
    from rocketforge.providers.cea_solid import RP1311_EXAMPLE5_PRESSURES_BAR

    return tuple(pressure_from_bar(p) for p in RP1311_EXAMPLE5_PRESSURES_BAR)


def provider_provenance() -> Any:
    """The provider's own base provenance record, or ``None``.

    Who solved this, with which library and database -- available before
    anything is solved. The solid path enriches it with the formulation.
    """
    provider = chamber_provider()
    return provider.provenance() if provider is not None else None


def _cea_module() -> Any:
    """The imported CEA module the provider is actually using, or ``None``.

    Taken from the live provider rather than imported afresh, so the solid path
    and the bipropellant path are demonstrably driving the same library
    instance -- which is the premise the A/solid/A determinism check rests on.
    """
    provider = chamber_provider()
    if provider is None:
        return None
    # The provider imports CEA lazily, on its first solve. ``load_cea`` is the
    # frozen adapter's own single import point, and a module is a singleton,
    # so this is the same object the provider solves with -- loaded now rather
    # than left as ``None`` until something happens to have solved first.
    from rocketforge.providers.cea.availability import load_cea

    return load_cea()


def solve_solid_chamber_state(request: Any, provenance: Any) -> Any:
    """Run one solid chamber equilibrium. Raises; the service packages errors."""
    module = _cea_module()
    if module is None:
        raise RuntimeError("no NASA CEA module is loaded")
    from rocketforge.providers.cea_solid import solve_solid_chamber

    return solve_solid_chamber(module, request, provenance=provenance)


def solve_solid_equilibrium_cstar(request: Any, chamber: Any) -> Any:
    """CEA equilibrium c* for a solved solid chamber, or its refusal.

    Never raises for a solve that fails; the result says why there is no value.
    """
    module = _cea_module()
    from rocketforge.providers.cea_solid import (
        solve_solid_equilibrium_cstar as _solve,
    )

    return _solve(module, request, chamber)


def solid_species_table(names: tuple[str, ...], *, database: str = "",
                        database_version: str = "") -> dict[str, Any]:
    """``Species`` records for a solid result's product set.

    Not the provider's own table, which refuses any species without a curated
    elemental formula and curates 33 C/H/O species. An aluminised perchlorate
    grain returns around 205 products spanning Al, Cl, N, Mg and S, so that
    table would refuse the entire result.
    """
    module = _cea_module()
    if module is None:
        return {}
    from rocketforge.providers.cea_solid import build_solid_species_table

    return build_solid_species_table(module, names, database=database,
                                     database_version=database_version)


#: Library ingredients the solid editor may offer, in display order. Each is
#: offered only if the installed ``thermo.lib`` actually holds it; the provider
#: package does the probing, because this layer touches no CEA object.
_SOLID_LIBRARY_CANDIDATES = (
    "NH4CLO4(I)", "NH4NO3(I)", "AL(cr)", "Mg(cr)", "MgO(cr)",
    "B(b)", "C(gr)", "H2O(L)",
)

_solid_catalogue: dict[str, Any] | None = None


def solid_ingredient_catalogue() -> dict[str, Any]:
    """Every ingredient a grain may contain, keyed as a ``SolidCase`` keys them.

    Library species by CEA name; custom reactants as ``custom:<name>``, taken
    only from sourced reference formulations. Cached: the probe is a CEA call
    per species and the answer cannot change within a process.
    """
    global _solid_catalogue
    if _solid_catalogue is not None:
        return _solid_catalogue
    from rocketforge.physics.solid_propellant import SolidIngredient

    catalogue: dict[str, Any] = {}
    module = _cea_module()
    if module is not None:
        from rocketforge.providers.cea_solid import library_species_available

        for name in library_species_available(module, _SOLID_LIBRARY_CANDIDATES):
            catalogue[name] = SolidIngredient(name, 0.0)
    for formulation in solid_formulation_templates().values():
        for item in formulation.ingredients:
            if item.custom is not None:
                catalogue.setdefault(
                    f"custom:{item.name}",
                    SolidIngredient(item.name, 0.0, custom=item.custom))
            elif module is None:
                catalogue.setdefault(item.name, SolidIngredient(item.name, 0.0))
    _solid_catalogue = catalogue
    return catalogue


def solid_phase_label(name: str) -> str:
    """The phase a CEA name declares, as a word, or empty if unrecognised."""
    from rocketforge.providers.cea_solid import solid_phase_of_cea_name

    try:
        return solid_phase_of_cea_name(name).value
    except Exception:  # noqa: BLE001
        return ""


def solid_assigned_enthalpy_diagnostics(request: Any) -> tuple[Any, ...]:
    """Ingredients whose temperature could not enter the solve."""
    module = _cea_module()
    if module is None:
        return ()
    from rocketforge.providers.cea_solid import (
        build_solid_chamber_input,
        solid_assigned_enthalpy_diagnostics as _diagnostics,
    )

    return _diagnostics(module, build_solid_chamber_input(request))
