"""Engine Requirement: the catalogue check, the vocabulary and the display rows.

Qt-free and provider-free. The requirement itself lives in
:mod:`rocketforge.engine.requirement`; this module is the part only the
application layer can do -- check a propellant key against the LIQ-1 preset
catalogue, name every option for the interface, and convert the display units
the form uses into the SI the requirement stores.

Nothing here solves, ranks or recommends. Resolving the pair a requirement
names returns the catalogue's own :class:`BipropellantPreset`, never a copy of
its chemistry; resolving a ``PAIR_REFERENCE`` O/F returns the catalogue's
number at the moment it is asked for.
"""

from __future__ import annotations

import math

from rocketforge.engine.requirement import (
    DEFAULT_ATMOSPHERE_MODEL,
    STANDARD_SEA_LEVEL_PRESSURE,
    AmbientMode,
    ChamberPressureMode,
    CyclePreference,
    DesignPriority,
    EngineRequirement,
    FeedArchitecture,
    MixtureRatioMode,
    PropellantMode,
    RequirementIssue,
    validate_requirement,
)

from . import environment_service
from . import thermochemistry_presets as presets

__all__ = [
    "AMBIENT_OPTIONS",
    "CHAMBER_PRESSURE_OPTIONS",
    "CYCLE_OPTIONS",
    "DEFAULT_REQUIREMENT",
    "FEED_OPTIONS",
    "MIXTURE_RATIO_OPTIONS",
    "PRIORITY_OPTIONS",
    "PROPELLANT_OPTIONS",
    "SCOPE_NOTE",
    "UNITS",
    "from_display",
    "open_decision_labels",
    "pair_options",
    "reference_mixture_ratio",
    "requirement_issues",
    "resolved_pair",
    "summary_rows",
    "to_display",
]

#: The form starts here: nothing stated, every preference open. The design
#: environment shows sea level as a visible, editable starting value -- the
#: same convention Rocket Performance uses for its ambient pressure.
DEFAULT_REQUIREMENT = EngineRequirement()

#: Display units of the form. The requirement stores SI; the conversion is
#: here and nowhere else, at the application boundary (``01`` section 7).
UNITS: dict[str, dict] = {
    "thrust": {"unit": "kN", "to_si": 1.0e3},
    "burn_time": {"unit": "s", "to_si": 1.0},
    "ambient_pressure": {"unit": "kPa", "to_si": 1.0e3},
    "altitude": {"unit": "km", "to_si": 1.0e3},
    "chamber_pressure": {"unit": "MPa", "to_si": 1.0e6},
}

SCOPE_NOTE = (
    "Design intent only. Nothing on this page sizes the engine, trades "
    "propellants, selects a cycle or runs a calculation; Auto leaves a "
    "decision open for later design. A stated altitude is resolved to its "
    "standard-atmosphere state, which is closed-form and solves nothing.")


def _option(key: str, label: str, note: str = "", **extra) -> dict:
    return {"key": str(key), "label": label, "note": note, **extra}


#: The model an altitude is read in, with its supported range (from the
#: atmosphere package, not restated here).
_USSA1976 = next(m for m in environment_service.model_options()
                 if m["key"] == DEFAULT_ATMOSPHERE_MODEL)


AMBIENT_OPTIONS: tuple[dict, ...] = (
    _option(AmbientMode.SEA_LEVEL, "Sea level",
            f"Standard atmosphere, p_a = {STANDARD_SEA_LEVEL_PRESSURE:g} Pa"),
    _option(AmbientMode.VACUUM, "Vacuum", "p_a = 0"),
    _option(AmbientMode.CUSTOM, "Custom ambient pressure",
            "An explicit ambient pressure. No altitude model is used."),
    _option(AmbientMode.STANDARD_ATMOSPHERE, "Altitude (USSA 1976)",
            f"A geometric altitude from {_USSA1976['minimum'] / 1e3:g} km to "
            f"{_USSA1976['maximum'] / 1e3:g} km, resolved to pressure by the "
            f"{_USSA1976['label']}. Not a weather or flight condition."),
)

PROPELLANT_OPTIONS: tuple[dict, ...] = (
    _option(PropellantMode.AUTO, "Auto",
            "Pair left open. LIQ-2 does not choose or rank propellants."),
    _option(PropellantMode.EXPLICIT, "Explicit pair",
            "One combination from the liquid propellant catalogue."),
)

CHAMBER_PRESSURE_OPTIONS: tuple[dict, ...] = (
    _option(ChamberPressureMode.AUTO, "Auto", "Chamber pressure left open."),
    _option(ChamberPressureMode.TARGET, "Target", "Design at this chamber pressure."),
    _option(ChamberPressureMode.UPPER_LIMIT, "Upper limit",
            "Any chamber pressure up to this one."),
)

MIXTURE_RATIO_OPTIONS: tuple[dict, ...] = (
    _option(MixtureRatioMode.AUTO, "Auto", "O/F left open."),
    _option(MixtureRatioMode.PAIR_REFERENCE, "Pair reference",
            "The selected pair's catalogue O/F, read from the catalogue."),
    _option(MixtureRatioMode.EXPLICIT, "Explicit", "This O/F, by mass."),
)

FEED_OPTIONS: tuple[dict, ...] = (
    _option(FeedArchitecture.AUTO, "Auto", "Feed architecture left open."),
    _option(FeedArchitecture.PRESSURE_FED, "Pressure-fed",
            "Tank pressure delivers the propellants. No pumps, so no power cycle."),
    _option(FeedArchitecture.PUMP_FED, "Pump-fed",
            "Pumps deliver the propellants; the power cycle is a separate choice."),
)

#: Every cycle is recorded intent in LIQ-2. ``modelled`` is False for all of
#: them and says so; full-flow staged combustion carries its own note because
#: it is the one a reader is most likely to expect a model behind.
CYCLE_OPTIONS: tuple[dict, ...] = (
    _option(CyclePreference.AUTO, "Auto", "Cycle left open.", modelled=False),
    _option(CyclePreference.GAS_GENERATOR, "Gas generator",
            "Recorded intent. No cycle model in this build.", modelled=False),
    _option(CyclePreference.EXPANDER, "Expander",
            "Recorded intent. No cycle model in this build.", modelled=False),
    _option(CyclePreference.STAGED_COMBUSTION, "Staged combustion",
            "Recorded intent. No cycle model in this build.", modelled=False),
    _option(CyclePreference.FULL_FLOW_STAGED_COMBUSTION, "Full-flow staged combustion",
            "Recorded as future-modelled intent. RocketForge has no full-flow "
            "staged-combustion model; no preburner or power balance is computed.",
            modelled=False),
)

PRIORITY_OPTIONS: tuple[dict, ...] = (
    _option(DesignPriority.UNSTATED, "Not stated"),
    _option(DesignPriority.SPECIFIC_IMPULSE, "Specific impulse",
            "Recorded for a later trade study. Nothing is ranked by it here."),
    _option(DesignPriority.DENSITY_IMPULSE, "Density impulse",
            "Recorded for a later trade study. Nothing is ranked by it here."),
    _option(DesignPriority.STORABILITY, "Storable propellants",
            "Recorded for a later trade study. Nothing is ranked by it here."),
    _option(DesignPriority.SIMPLICITY, "Simplicity",
            "Recorded for a later trade study. Nothing is ranked by it here."),
)

_OPEN_LABELS = {
    "propellant": "Propellant pair",
    "chamber_pressure": "Chamber pressure",
    "mixture_ratio": "O/F",
    "feed": "Feed architecture",
    "cycle": "Power cycle",
}


def _label(options: tuple[dict, ...], key: str) -> str:
    for option in options:
        if option["key"] == key:
            return option["label"]
    return key


# ---------------------------------------------------------------------------
# the catalogue reference
# ---------------------------------------------------------------------------


def pair_options() -> list[dict]:
    """Every LIQ-1 catalogue combination, executable or not, in source order.

    Blocked pairs are listed with their reason so the form can show why they
    cannot be chosen, rather than leaving them out silently.
    """
    return [{"key": preset.key, "label": preset.label,
             "executable": preset.executable, "blocker": preset.blocker,
             "mixtureRatio": preset.oxidiser_fuel_ratio, "source": preset.source}
            for preset in presets.preset_catalogue()]


def resolved_pair(requirement: EngineRequirement) -> presets.BipropellantPreset | None:
    """The catalogue entry an explicit pair names, or ``None``."""
    if not requirement.propellant.is_explicit:
        return None
    return presets.preset_named(requirement.propellant.pair_key)


def reference_mixture_ratio(requirement: EngineRequirement) -> float | None:
    """The catalogue O/F a ``PAIR_REFERENCE`` preference points to, if any."""
    if requirement.mixture_ratio.mode is not MixtureRatioMode.PAIR_REFERENCE:
        return None
    preset = resolved_pair(requirement)
    if preset is None or not preset.executable:
        return None
    return preset.oxidiser_fuel_ratio


def requirement_issues(requirement: EngineRequirement) -> tuple[RequirementIssue, ...]:
    """The domain's issues, plus the checks only this layer can make: the
    catalogue, and an altitude's resolved atmosphere."""
    issues = list(validate_requirement(requirement))
    issues += environment_service.environment_issues(requirement)
    key = requirement.propellant.pair_key
    if requirement.propellant.is_explicit and key.strip():
        preset = presets.preset_named(key)
        if preset is None:
            issues.append(RequirementIssue(
                "PROPELLANT_PAIR_UNKNOWN", "propellant",
                f"{key!r} is not a pair in the liquid propellant catalogue."))
        elif not preset.executable:
            issues.append(RequirementIssue(
                "PROPELLANT_PAIR_BLOCKED", "propellant",
                f"{preset.label} cannot be represented: {preset.blocker}"))
    return tuple(issues)


def open_decision_labels(requirement: EngineRequirement) -> list[str]:
    return [_OPEN_LABELS[name] for name in requirement.open_decisions()]


# ---------------------------------------------------------------------------
# units
# ---------------------------------------------------------------------------


def to_display(quantity: str, value: float | None) -> float | None:
    if value is None:
        return None
    return value / UNITS[quantity]["to_si"]


def from_display(quantity: str, value: float | None) -> float | None:
    if value is None:
        return None
    return value * UNITS[quantity]["to_si"]


def _format(quantity: str, value: float | None) -> str:
    shown = to_display(quantity, value)
    if shown is None:
        return "Not stated"
    if not math.isfinite(shown):
        return str(shown)
    return f"{shown:g} {UNITS[quantity]['unit']}"


# ---------------------------------------------------------------------------
# the summary
# ---------------------------------------------------------------------------


def summary_rows(requirement: EngineRequirement) -> list[dict]:
    """The requirement as label/value rows, exactly as stored. No derived value."""
    environment = requirement.environment
    env_text = _label(AMBIENT_OPTIONS, environment.mode)
    if environment.mode is AmbientMode.CUSTOM:
        env_text += f", p_a = {_format('ambient_pressure', environment.custom_pressure)}"
    elif environment.mode is AmbientMode.SEA_LEVEL:
        env_text += f", p_a = {_format('ambient_pressure', STANDARD_SEA_LEVEL_PRESSURE)}"
    elif environment.is_altitude:
        env_text += f", Z = {_format('altitude', environment.altitude)}"
        pressure = environment_service.ambient_pressure(environment)
        if math.isfinite(pressure):
            env_text += f", p_a = {_format('ambient_pressure', pressure)}"
    else:
        env_text += ", p_a = 0"

    preset = resolved_pair(requirement)
    if not requirement.propellant.is_explicit:
        pair_text = "Auto · open"
    elif preset is None:
        pair_text = requirement.propellant.pair_key or "Not chosen"
    else:
        pair_text = preset.label

    chamber = requirement.chamber_pressure
    if chamber.mode is ChamberPressureMode.AUTO:
        chamber_text = "Auto · open"
    else:
        chamber_text = (f"{_label(CHAMBER_PRESSURE_OPTIONS, chamber.mode)} "
                        f"{_format('chamber_pressure', chamber.value)}")

    ratio = requirement.mixture_ratio
    if ratio.mode is MixtureRatioMode.AUTO:
        ratio_text = "Auto · open"
    elif ratio.mode is MixtureRatioMode.EXPLICIT:
        ratio_text = "Not stated" if ratio.value is None else f"{ratio.value:g} (explicit)"
    else:
        reference = reference_mixture_ratio(requirement)
        ratio_text = ("Pair reference · no pair" if reference is None
                      else f"{reference:g} (pair reference, catalogue)")

    if requirement.cycle is None:
        cycle_text = "Not applicable" if requirement.feed is not FeedArchitecture.PUMP_FED \
            else "Not stated"
    else:
        cycle_text = _label(CYCLE_OPTIONS, requirement.cycle)
        if requirement.cycle is CyclePreference.AUTO:
            cycle_text += " · open"

    feed_text = _label(FEED_OPTIONS, requirement.feed)
    if requirement.feed is FeedArchitecture.AUTO:
        feed_text += " · open"

    return [
        {"key": "thrust", "label": "Target thrust",
         "value": _format("thrust", requirement.thrust)},
        {"key": "environment", "label": "Design environment", "value": env_text},
        {"key": "burn_time", "label": "Burn time",
         "value": _format("burn_time", requirement.burn_time)},
        {"key": "propellant", "label": "Propellant pair", "value": pair_text},
        {"key": "chamber_pressure", "label": "Chamber pressure", "value": chamber_text},
        {"key": "mixture_ratio", "label": "O/F", "value": ratio_text},
        {"key": "feed", "label": "Feed architecture", "value": feed_text},
        {"key": "cycle", "label": "Power cycle", "value": cycle_text},
        {"key": "priority", "label": "Design priority",
         "value": _label(PRIORITY_OPTIONS, requirement.priority)},
    ]
