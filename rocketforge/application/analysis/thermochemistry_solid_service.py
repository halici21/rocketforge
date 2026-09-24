"""Solid formulations, for the Thermochemistry workspace.

The solid sibling of :mod:`.thermochemistry_service`, and deliberately a thin
one: it produces the **same** :class:`~.thermochemistry_service.ChamberOutcome`
the bipropellant path produces, carrying the same ``ChamberGas``. Everything
downstream -- the readout rows, the species table, the condensed summary, the
diagnostics -- therefore works on a solid result without knowing it is one.

What could not be shared is the input. A solid grain has no fuel stream, no
oxidiser stream and no O/F, so :class:`SolidCase` is its own type rather than a
``ChamberCase`` with three fields left blank.

**R1 scope.** Chamber equilibrium only. No c*, no Cf, no Isp, no expansion --
solid reference performance is deferred to R1.1, and there is no dormant panel
or disabled control standing in for it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, ClassVar

from ..species_notation import species_label
from .thermochemistry_provider import (
    availability,
    chamber_provider,
    provider_provenance,
    solid_assigned_enthalpy_diagnostics,
    solid_formulation_templates,
    solid_ingredient_catalogue,
    solid_omit_species,
    solid_validated_pressures,
    solve_solid_chamber_state,
    solve_solid_equilibrium_cstar,
)
from .thermochemistry_service import (
    OUTCOME_INVALID_INPUT,
    OUTCOME_OK,
    OUTCOME_PROVIDER_ERROR,
    OUTCOME_UNAVAILABLE,
    OUTCOME_WARNING,
    ChamberOutcome,
)

__all__ = [
    "SolidFormulationOption",
    "SolidIngredientOption",
    "SolidCase",
    "is_solid_case",
    "default_solid_case",
    "solid_formulation_options",
    "solid_formulation_named",
    "solid_ingredient_options",
    "solid_ingredient_named",
    "build_solid_formulation",
    "build_solid_request",
    "solve_solid_case",
    "solid_case_headline",
    "solid_conditions",
    "MODEL_BOUNDARY_NOTE",
    "CSTAR_LIMITATIONS",
]

#: The boundary every solid result carries (section 26). Stated as a boundary,
#: not a disclaimer: a chamber equilibrium is a real and complete answer to a
#: real question. What it is not is a motor.
MODEL_BOUNDARY_NOTE = (
    "Chamber thermochemistry only. Motor/internal-ballistics and delivered "
    "performance are not modelled."
)

#: What the CEA equilibrium c* is not, shown every time it is (decision D2).
CSTAR_LIMITATIONS = (
    "Not a motor specific impulse.",
    "No nozzle expansion is modelled.",
    "No internal-ballistic effects: burn rate, grain geometry and erosive "
    "burning are not part of it.",
)


# ---------------------------------------------------------------------------
# what can go into a grain
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SolidIngredientOption:
    """One ingredient the editor offers.

    Attributes:
        key: Stable identifier. A library species is keyed by its CEA name; a
            custom reactant by ``custom:<name>``.
        name: What CEA is given and what the editor shows. Phase suffix kept.
        representation: ``"library"`` (a ``thermo.lib`` record) or ``"custom"``
            (an assigned-enthalpy definition RocketForge carries verbatim).
        phase: The phase the name declares, for a library species. Empty for a
            custom reactant: its source does not state one, and a phase is not
            supplied in its place.
        source: Where the thermochemical data comes from.
        assigned_temperature: K, when the ingredient's enthalpy is fixed at one
            temperature; ``None`` when it follows the requested temperature.
    """

    key: str
    name: str
    representation: str
    phase: str
    source: str
    assigned_temperature: float | None


def solid_ingredient_options() -> tuple[SolidIngredientOption, ...]:
    """Every ingredient this build can put into a grain, in a stable order.

    Library species are offered only when the installed ``thermo.lib`` actually
    holds them -- probed, not assumed. Custom reactants are offered only when a
    sourced definition exists; R1 carries one, NASA's RP-1311 Example 5 binder,
    and deliberately no generic HTPB or PBAN, because no exact CEA
    representation of either has been independently sourced.
    """
    out = []
    for key, template in solid_ingredient_catalogue().items():
        custom = template.custom
        out.append(SolidIngredientOption(
            key=key,
            name=template.name,
            representation="custom" if custom is not None else "library",
            phase=template_phase(template),
            source=(custom.source if custom is not None
                    else "NASA CEA thermo.lib"),
            assigned_temperature=(custom.reference_temperature
                                  if custom is not None else None),
        ))
    return tuple(out)


def template_phase(template: Any) -> str:
    if template.custom is not None:
        return ""
    from .thermochemistry_provider import solid_phase_label

    return solid_phase_label(template.name)


def solid_ingredient_named(key: str) -> SolidIngredientOption | None:
    for option in solid_ingredient_options():
        if option.key == key:
            return option
    return None


# ---------------------------------------------------------------------------
# reference formulations
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SolidFormulationOption:
    """A published formulation the workspace can load.

    Attributes:
        is_reference_case: True when this exists to reproduce a published
            result. Shown as such: a validation case and a design starting
            point are different things, and someone who mistakes one for the
            other will draw the wrong conclusion from editing it.
    """

    key: str
    label: str
    reference: str
    is_reference_case: bool
    ingredients: tuple[tuple[str, float], ...]
    initial_temperature: float
    chamber_pressure: float


def _ingredient_key(ingredient: Any) -> str:
    return (f"custom:{ingredient.name}" if ingredient.custom is not None
            else ingredient.name)


#: The pressure each reference formulation opens at. Example 5's first column,
#: 34.473652 bar (500 psia; the source prints 34.023 atm).
_REFERENCE_PRESSURE_PA = {"rp1311-example5": 3447365.2}


def solid_formulation_options() -> tuple[SolidFormulationOption, ...]:
    out = []
    for key, formulation in solid_formulation_templates().items():
        out.append(SolidFormulationOption(
            key=key,
            label=formulation.name,
            reference=formulation.reference or "",
            is_reference_case=bool(formulation.reference),
            ingredients=tuple((_ingredient_key(item), item.mass_fraction)
                              for item in formulation.ingredients),
            initial_temperature=formulation.initial_temperature,
            chamber_pressure=_REFERENCE_PRESSURE_PA.get(key, 1.0e6),
        ))
    return tuple(out)


def solid_formulation_named(key: str | None) -> SolidFormulationOption | None:
    for option in solid_formulation_options():
        if option.key == key:
            return option
    return None


# ---------------------------------------------------------------------------
# the case
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SolidCase:
    """One solid operating point, in SI, independent of any provider.

    Ingredients are named by catalogue key with a mass fraction each, matching
    how :class:`~.thermochemistry_service.ChamberCase` names its propellants:
    nothing above the service layer holds a domain object, so a case stays
    trivially comparable, storable and printable -- and a solved result keeps
    the exact case that produced it, however the form is edited afterwards.

    Attributes:
        ingredients: ``(ingredient key, mass fraction)`` pairs, in the order CEA
            is given them.
        chamber_pressure: Pa.
        initial_temperature: K, the grain's bulk temperature before ignition.
        reference_key: The published formulation this case started from, or
            ``None``. It decides whether the published omit list applies --
            only while the ingredient identities are still the published ones.
    """

    #: How every consumer tells a solid case from a bipropellant one -- the
    #: result headline, the condition rail, and the Rocket Performance gate
    #: that refuses a solid chamber. One explicit marker, not a field probe.
    propellant_kind: ClassVar[str] = "solid"

    ingredients: tuple[tuple[str, float], ...]
    chamber_pressure: float
    initial_temperature: float
    reference_key: str | None = None

    def replace(self, **changes: Any) -> "SolidCase":
        from dataclasses import replace as _replace

        return _replace(self, **changes)

    @property
    def mass_fractions(self) -> tuple[float, ...]:
        return tuple(fraction for _, fraction in self.ingredients)

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(key for key, _ in self.ingredients)

    @property
    def mass_fraction_sum(self) -> float:
        return math.fsum(self.mass_fractions)

    @property
    def is_balanced(self) -> bool:
        """Closes at 100 %, within the domain's own tolerance."""
        from rocketforge.physics.solid_propellant import MASS_FRACTION_SUM_TOL

        return abs(self.mass_fraction_sum - 1.0) <= MASS_FRACTION_SUM_TOL

    def reference(self) -> SolidFormulationOption | None:
        return solid_formulation_named(self.reference_key)

    @property
    def is_published_composition(self) -> bool:
        """Exactly the published grain: same ingredients, same fractions."""
        option = self.reference()
        return option is not None and self.ingredients == option.ingredients

    @property
    def is_validated_operating_point(self) -> bool:
        """The published grain, at a temperature and pressure the source solved.

        Only this is labelled a reference / validation case. The published
        composition at another grain temperature or pressure is a real
        calculation, but not one anyone published a result for.
        """
        option = self.reference()
        if not self.is_published_composition or option is None:
            return False
        if abs(self.initial_temperature - option.initial_temperature) > 1e-9:
            return False
        return any(math.isclose(self.chamber_pressure, p, rel_tol=1e-9)
                   for p in solid_validated_pressures(self.reference_key))

    @property
    def has_published_ingredients(self) -> bool:
        """The published ingredient list, whatever the fractions."""
        option = self.reference()
        return (option is not None
                and self.keys == tuple(key for key, _ in option.ingredients))


def is_solid_case(case: Any) -> bool:
    return getattr(case, "propellant_kind", "") == "solid"


def default_solid_case() -> SolidCase:
    """The workspace's opening case: the published validation case, unedited."""
    option = solid_formulation_options()[0]
    return SolidCase(
        ingredients=option.ingredients,
        chamber_pressure=option.chamber_pressure,
        initial_temperature=option.initial_temperature,
        reference_key=option.key,
    )


# ---------------------------------------------------------------------------
# case -> request -> outcome
# ---------------------------------------------------------------------------


def build_solid_formulation(case: SolidCase):
    """Rebuild a domain formulation from a case.

    Every ingredient's identity -- including a custom reactant's formula,
    molecular weight, assigned enthalpy and source -- comes from the catalogue.
    Only the mass fractions come from the case. Raises the domain's own errors
    for a grain that does not close, so the 100 % rule lives in one place.
    """
    from dataclasses import replace

    from rocketforge.physics.solid_propellant import SolidFormulation

    catalogue = solid_ingredient_catalogue()
    if not case.ingredients:
        raise LookupError("a formulation needs at least one ingredient")
    ingredients = []
    for key, fraction in case.ingredients:
        template = catalogue.get(key)
        if template is None:
            raise LookupError(f"no solid ingredient named {key!r} in this build")
        ingredients.append(replace(template, mass_fraction=fraction))

    option = case.reference()
    if case.is_published_composition:
        name = option.label
        reference = option.reference or None
    elif option is not None:
        name = f"Edited from {option.label}"
        reference = None
    else:
        name = "Custom formulation"
        reference = None
    return SolidFormulation(name=name, ingredients=tuple(ingredients),
                            initial_temperature=case.initial_temperature,
                            reference=reference)


def build_solid_request(case: SolidCase):
    """Turn a case into a validated solid equilibrium request."""
    from rocketforge.physics.solid_propellant import (
        SolidFormulationEquilibriumRequest,
    )

    # A published case's omissions are part of that case, so they apply while
    # its ingredient list is intact -- fractions may be edited. Once an
    # ingredient is added or removed the grain is a different chemical system
    # and nothing is omitted on its behalf.
    omit = (solid_omit_species(case.reference_key)
            if case.has_published_ingredients else ())
    return SolidFormulationEquilibriumRequest(
        formulation=build_solid_formulation(case),
        chamber_pressure=case.chamber_pressure,
        product_species=None,
        omit_species=omit,
    )


def solve_solid_case(case: SolidCase) -> ChamberOutcome:
    """Run one solid chamber equilibrium and package the answer for display.

    Never raises, mirroring :func:`~.thermochemistry_service.solve_case`, and
    returns the same outcome type. An ingredient whose temperature the model
    could not honour -- a custom reactant fixed at its assigned temperature --
    makes the outcome a *warning*, with the same diagnostic the bipropellant
    path raises for a cryogen, so the interface shows it the same way.
    """
    from rocketforge.core.errors import DomainError, InputError
    from rocketforge.physics.thermochemistry import ProviderError

    provider = chamber_provider()
    if provider is None:
        state = availability()
        return ChamberOutcome(
            kind=OUTCOME_UNAVAILABLE, case=case,
            message=state.detail or "No thermochemistry provider is installed "
                                    "in this environment.")

    try:
        request = build_solid_request(case)
    except LookupError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field="formulation")
    except InputError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field="mass_fraction")

    base = provider_provenance()
    try:
        state = solve_solid_chamber_state(request, base)
        diagnostics = solid_assigned_enthalpy_diagnostics(request)
    except ProviderError as exc:
        return ChamberOutcome(kind=OUTCOME_PROVIDER_ERROR, case=case,
                              message=str(exc), field="formulation")
    except DomainError as exc:
        return ChamberOutcome(kind=OUTCOME_PROVIDER_ERROR, case=case,
                              message=str(exc), field="formulation")
    except InputError as exc:
        return ChamberOutcome(kind=OUTCOME_INVALID_INPUT, case=case,
                              message=str(exc), field="mass_fraction")

    # c* is a second CEA solve with its own validity checks. It never fails
    # the chamber result: a refused c* is reported as refused, beside a
    # chamber state that is still valid.
    cstar = solve_solid_equilibrium_cstar(request, state)

    kind = OUTCOME_WARNING if diagnostics else OUTCOME_OK
    return ChamberOutcome(kind=kind, case=case, state=state,
                          diagnostics=tuple(diagnostics),
                          provenance=state.provenance or base,
                          characteristic_velocity=cstar)


# ---------------------------------------------------------------------------
# labels, from the case a result carries -- never from the live form
# ---------------------------------------------------------------------------


def _formulation_label(case: SolidCase) -> str:
    option = case.reference()
    if case.is_published_composition:
        return option.label
    if option is not None:
        return f"Edited from {option.label}"
    return "Custom formulation"


def solid_case_headline(case: SolidCase | None) -> str:
    """The one-line statement of what a solid result is for.

    No O/F term: CEA reports ``o/f = 0.000`` for a solid case, and the absence
    of a ratio is the honest representation -- a printed zero invites being
    read as a measured value.
    """
    if case is None:
        return ""
    return (f"{_formulation_label(case)} · "
            f"p_c {case.chamber_pressure / 1.0e5:g} bar · "
            f"T_grain {case.initial_temperature:g} K")


def solid_conditions(case: SolidCase | None) -> tuple[dict[str, str], ...]:
    """The full condition snapshot behind a displayed solid result."""
    if case is None:
        return ()
    option = case.reference()
    rows: list[dict[str, str]] = [{
        "label": "Formulation",
        "value": _formulation_label(case),
        "note": (option.reference if option and case.is_published_composition
                 else ""),
    }]
    for key, fraction in case.ingredients:
        ingredient = solid_ingredient_named(key)
        name = ingredient.name if ingredient else key
        note = ""
        if ingredient is not None and ingredient.representation == "custom":
            note = "custom · assigned enthalpy"
        rows.append({"label": species_label(name), "value": f"{fraction * 100.0:.3f} %",
                     "note": note})
    rows.append({"label": "Total mass",
                 "value": f"{case.mass_fraction_sum * 100.0:.3f} %", "note": ""})
    rows.append({"label": "Chamber pressure",
                 "value": f"{case.chamber_pressure / 1.0e5:g} bar",
                 "note": f"{case.chamber_pressure:g} Pa"})
    rows.append({"label": "Grain temperature",
                 "value": f"{case.initial_temperature:g} K", "note": ""})
    rows.append({"label": "Model", "value": "HP Equilibrium · Adiabatic",
                 "note": MODEL_BOUNDARY_NOTE})
    return tuple(rows)
