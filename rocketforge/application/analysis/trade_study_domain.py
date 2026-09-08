"""What RocketForge offers a trade study: its stages, variables and metrics.

The generic engine in ``engine.studies`` knows nothing about rockets. This
module is where the domain is supplied -- which quantities can be varied, which
can be reported, and which evaluation stage each belongs to. Everything here is
data; the evaluation itself is in ``trade_study_service``.

The stage assignment is the important part. It is not documentation: the
planner reads it, and a variable placed in the wrong stage would either cost
hundreds of unnecessary chemistry solves or reuse a chamber state that should
have been re-solved. So each entry says *why* it is where it is.

Three things are deliberately **not** design variables:

**Gamma strategy and basis.** They change the model, not the design. One study
uses one reduction, so that every point on a front was computed the same way;
comparing reductions is two studies, not one front.

**Provider, chemistry mode and database.** Study provenance. Mixing two
providers into one ranking would rank the providers, not the designs.

**Liquid reactant temperature.** Deferred, and for a specific reason recorded
below rather than left as an omission.
"""

from __future__ import annotations

from typing import Any

from rocketforge.engine.studies import (
    LinearRangeVariable,
    MetricDefinition,
    MetricRegistry,
    VariableDomain,
)

__all__ = [
    "STAGE_THERMOCHEMISTRY",
    "STAGE_PERFORMANCE",
    "STAGE_DECISION",
    "STAGE_ORDER",
    "STAGE_LABELS",
    "VARIABLE_SPECS",
    "METRICS",
    "variable_spec",
    "metric_registry",
    "DEFERRED_VARIABLES",
]

#: The chemistry solve. The expensive stage, and the one solve reuse exists for.
STAGE_THERMOCHEMISTRY = "thermochemistry"

#: RocketForge's own performance algebra. Microseconds per point.
STAGE_PERFORMANCE = "performance"

#: Constraints, feasibility, objectives, Pareto, score. No physics at all.
STAGE_DECISION = "decision"

STAGE_ORDER = (STAGE_THERMOCHEMISTRY, STAGE_PERFORMANCE, STAGE_DECISION)

STAGE_LABELS = {
    STAGE_THERMOCHEMISTRY: "Chamber equilibrium",
    STAGE_PERFORMANCE: "Ideal performance",
    STAGE_DECISION: "Decision analysis",
}


#: Every variable a Phase 5F study may vary, with its stage and why.
#:
#: ``effect`` is shown in the interface. It is not decoration: a user who does
#: not know that an area ratio cannot change a chamber temperature will build
#: the study that produces 100 identical rows, and the definition validator
#: will refuse it. Saying so on the control is cheaper than refusing later.
VARIABLE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "oxidiser_fuel_ratio",
        "label": "Mixture ratio  O/F",
        "unit": "",
        "stage": STAGE_THERMOCHEMISTRY,
        "dimensionless": True,
        "minimum": 0.0,
        "exclusive_minimum": True,
        "default": {"start": 2.5, "end": 4.5, "count": 41},
        "effect": "Changes the chamber equilibrium, and everything downstream "
                  "of it. Each value is a separate chemistry solve.",
        "note": "Oxidiser mass divided by fuel mass — RocketForge's "
                "orientation throughout, and CEA's.",
        "display_units": (),
    },
    {
        "key": "chamber_pressure",
        "label": "Chamber pressure  p_c",
        "unit": "Pa",
        "stage": STAGE_THERMOCHEMISTRY,
        "dimensionless": False,
        "minimum": 0.0,
        "exclusive_minimum": True,
        "default": {"start": 5.0e6, "end": 20.0e6, "count": 4},
        "effect": "Changes the chamber equilibrium. Each value multiplies the "
                  "chemistry solve count.",
        "note": "",
        "display_units": (("Pa", 1.0), ("bar", 1.0e5), ("MPa", 1.0e6)),
    },
    {
        "key": "area_ratio",
        "label": "Area ratio  Ae/At",
        "unit": "",
        "stage": STAGE_PERFORMANCE,
        "dimensionless": True,
        "minimum": 1.0,
        "exclusive_minimum": True,
        "default": {"start": 10.0, "end": 80.0, "count": 8},
        "effect": "Changes the expansion only. Costs no additional chemistry "
                  "solves, however many values are chosen.",
        "note": "Exit area over throat area, above 1.",
        "display_units": (),
    },
    {
        "key": "ambient_pressure",
        "label": "Ambient pressure  p_a",
        "unit": "Pa",
        "stage": STAGE_PERFORMANCE,
        "dimensionless": False,
        "minimum": 0.0,
        "exclusive_minimum": False,
        "default": {"start": 0.0, "end": 101325.0, "count": 3},
        "effect": "An operating condition, not engine hardware. Changes the "
                  "pressure-thrust term only, and costs no chemistry solves.",
        "note": "Zero is vacuum, and is a value rather than a missing one.",
        "display_units": (("Pa", 1.0), ("kPa", 1.0e3), ("bar", 1.0e5)),
    },
    {
        "key": "throat_area",
        "label": "Throat area  A_t",
        "unit": "m²",
        "stage": STAGE_PERFORMANCE,
        "dimensionless": False,
        "minimum": 0.0,
        "exclusive_minimum": True,
        "default": {"start": 0.005, "end": 0.05, "count": 4},
        "effect": "Sizes the engine. Scales thrust and mass flow; changes no "
                  "scale-free quantity and costs no chemistry solves.",
        "note": "",
        "display_units": (("m²", 1.0), ("cm²", 1.0e-4)),
    },
)


#: Variables this phase deliberately does not offer, and why.
#:
#: Recorded here rather than omitted silently, so the reason survives into the
#: interface and into the next phase that might be tempted to add them.
DEFERRED_VARIABLES: tuple[dict[str, str], ...] = (
    {
        "key": "reactant_temperature",
        "label": "Liquid reactant temperature",
        "reason": "NASA CEA models the shipped liquid reactants with an "
                  "assigned enthalpy, so the requested stream temperature does "
                  "not enter the chamber solve. A temperature trade study "
                  "would draw a sensitivity curve for something the provider "
                  "is not modelling — a flat line read as 'temperature barely "
                  "matters'. Deferred until reactant enthalpy / fluid-property "
                  "coupling exists.",
    },
    {
        "key": "gamma_strategy",
        "label": "Gamma strategy and basis",
        "reason": "A model assumption, not a design. Two reductions in one "
                  "Pareto front would compare models rather than designs. One "
                  "study, one reduction; comparing them is two studies.",
    },
    {
        "key": "provider",
        "label": "Provider, chemistry mode and database",
        "reason": "Study provenance. Ranking designs computed by different "
                  "providers ranks the providers.",
    },
    {
        "key": "propellant_pair",
        "label": "Propellant pair",
        "reason": "The registry supports a categorical variable and the "
                  "production catalogue is provenance-bearing, but a pair "
                  "study also changes which element set the products are "
                  "solved over. Left for a later phase rather than fabricated "
                  "from display strings.",
    },
)


#: What a study may report on, constrain or optimise.
#:
#: No metric is named plain ``gamma``. A chamber state carries two isentropic
#: exponents several per cent apart, and a column headed "gamma" would be a
#: number nobody could interpret.
METRICS: tuple[MetricDefinition, ...] = (
    # ---- chamber equilibrium ------------------------------------------
    MetricDefinition(
        key="chamber_temperature", label="Chamber temperature  T₀",
        stage=STAGE_THERMOCHEMISTRY, unit="K", decimals_hint=5,
        help="Adiabatic flame temperature at constant enthalpy and pressure. "
             "An ideal equilibrium value with no heat loss of any kind."),
    MetricDefinition(
        key="mean_molar_mass", label="Mean molar mass  M", unit="kg/mol",
        stage=STAGE_THERMOCHEMISTRY, decimals_hint=6,
        help="Mass-weighted mean over the product composition."),
    MetricDefinition(
        key="gas_constant", label="Specific gas constant  R", unit="J/(kg·K)",
        stage=STAGE_THERMOCHEMISTRY, decimals_hint=6,
        help="R_universal divided by the mean molar mass."),
    MetricDefinition(
        key="gamma_equilibrium", label="Equilibrium exponent  γ_s", unit="",
        stage=STAGE_THERMOCHEMISTRY, decimals_hint=6,
        help="The isentropic exponent of a shifting-equilibrium expansion. "
             "Distinct from cp/cv, and several per cent from it."),
    MetricDefinition(
        key="gamma_frozen", label="Frozen exponent  cp/cv", unit="",
        stage=STAGE_THERMOCHEMISTRY, decimals_hint=6,
        help="The ratio of specific heats at fixed composition."),
    MetricDefinition(
        key="condensed_mass_fraction", label="Condensed mass fraction", unit="",
        stage=STAGE_THERMOCHEMISTRY, decimals_hint=3,
        help="Mass fraction of condensed products in the chamber. The ideal "
             "performance model refuses a materially mixed-phase state rather "
             "than averaging it into the gas."),

    # ---- ideal performance, scale-free ---------------------------------
    MetricDefinition(
        key="characteristic_velocity", label="Characteristic velocity  c*",
        stage=STAGE_PERFORMANCE, unit="m/s", decimals_hint=6,
        help="p_c·A_t/ṁ. A chamber and choked-throat quantity: not the exhaust "
             "velocity, and independent of area ratio and ambient pressure."),
    MetricDefinition(
        key="thrust_coefficient", label="Thrust coefficient  Cf", unit="",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="F/(p_c·A_t). How much the nozzle amplifies the thrust a bare "
             "throat would produce."),
    MetricDefinition(
        key="effective_exhaust_velocity", label="Effective exhaust velocity  c_eff",
        stage=STAGE_PERFORMANCE, unit="m/s", decimals_hint=6,
        help="F/ṁ = Cf·c*. Equal to the exit velocity only at ideal expansion."),
    MetricDefinition(
        key="specific_impulse", label="Specific impulse  Isp", unit="s",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="c_eff/g₀, in seconds. Ideal: no efficiency factor of any kind."),
    MetricDefinition(
        key="fuel_density", label="Fuel density  ρ_f", unit="kg/m^3",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="At the fuel stream's own temperature and feed pressure, from "
             "the fluid-property provider. Not density_hint."),
    MetricDefinition(
        key="oxidiser_density", label="Oxidiser density  ρ_ox", unit="kg/m^3",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="At the oxidiser stream's own temperature and feed pressure, "
             "from the fluid-property provider. Not density_hint."),
    MetricDefinition(
        key="bulk_propellant_density", label="Bulk propellant density  ρ_mix",
        unit="kg/m^3", stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="(1 + O/F) / (1/ρ_f + (O/F)/ρ_ox). The additive-volume tank "
             "density, not the density of a mixture: separate volumes, no "
             "ullage, no structure."),
    MetricDefinition(
        key="density_impulse", label="Density impulse  I_d",
        unit="kg/(m^2 s)", stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="ρ_mix·c_eff, equivalently ρ_mix·Isp·g₀, in N·s/m³. Impulse per "
             "unit propellant volume — the metric for a volume-limited "
             "stage. Available only when both propellants have a validated "
             "fluid model and a feed pressure was stated."),
    MetricDefinition(
        key="exit_mach", label="Exit Mach number  M_e", unit="",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="Fixed by the area ratio and gamma alone."),
    MetricDefinition(
        key="exit_pressure", label="Exit pressure  p_e", unit="Pa",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="Static pressure at the exit plane."),
    MetricDefinition(
        key="exit_temperature", label="Exit temperature  T_e", unit="K",
        stage=STAGE_PERFORMANCE, decimals_hint=5,
        help="Static temperature at the exit plane."),
    MetricDefinition(
        key="exit_velocity", label="Exit velocity  V_e", unit="m/s",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="The physical gas velocity at the exit. Distinct from c_eff."),

    # ---- scaled engine --------------------------------------------------
    MetricDefinition(
        key="total_thrust", label="Total thrust  F", unit="N",
        stage=STAGE_PERFORMANCE, requires_scale=True, decimals_hint=6,
        help="Momentum plus pressure thrust. Needs an engine size."),
    MetricDefinition(
        key="momentum_thrust", label="Momentum thrust  ṁ·V_e", unit="N",
        stage=STAGE_PERFORMANCE, requires_scale=True, decimals_hint=6,
        help="Needs an engine size."),
    MetricDefinition(
        key="pressure_thrust", label="Pressure thrust  (p_e−p_a)·A_e", unit="N",
        stage=STAGE_PERFORMANCE, requires_scale=True, decimals_hint=6,
        help="Signed: negative for an overexpanded nozzle, and not clamped."),
    MetricDefinition(
        key="mass_flow", label="Mass flow  ṁ", unit="kg/s",
        stage=STAGE_PERFORMANCE, requires_scale=True, decimals_hint=6,
        help="p_c·A_t/c*. Needs an engine size."),
)


def metric_registry() -> MetricRegistry:
    """The registry a RocketForge study is validated and planned against."""
    return MetricRegistry(METRICS)


def variable_spec(key: str) -> dict[str, Any] | None:
    for spec in VARIABLE_SPECS:
        if spec["key"] == key:
            return spec
    return None


def build_variable(key: str, *, start: float, end: float,
                   count: int) -> LinearRangeVariable:
    """A linear-range variable from the registry entry for ``key``.

    The domain comes from the registry rather than from the caller, so an O/F
    of zero is refused the same way wherever the study was built.
    """
    spec = variable_spec(key)
    if spec is None:
        raise KeyError(
            f"no design variable named {key!r}. Available: "
            f"{', '.join(entry['key'] for entry in VARIABLE_SPECS)}")
    return LinearRangeVariable(
        key=spec["key"], label=spec["label"], stage=spec["stage"],
        unit=spec["unit"],
        domain=VariableDomain(minimum=spec.get("minimum"),
                              exclusive_minimum=spec.get("exclusive_minimum",
                                                         False)),
        start=start, end=end, count=count)
