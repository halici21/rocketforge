"""Register density impulse as a Trade Study metric, outside the frozen core.

**No frozen file is touched.** ``engine.studies`` is a generic engine: it takes
metrics from whatever the evaluator returns and a metric *table* from the
application. Both live in ``application/analysis``, which no freeze manifest
covers, so density impulse needs no TRADE STUDY API v1.1.

The stream states are fixed for a whole study -- a study varies O/F, chamber
pressure, area ratio and ambient pressure, none of which change a propellant's
tank temperature or feed pressure -- so the two fluid evaluations happen once
per study, whatever the point count.
"""
from __future__ import annotations

import pathlib

# --- 1. the metric table -------------------------------------------------
domain = pathlib.Path("rocketforge/application/analysis/trade_study_domain.py")
t = domain.read_text(encoding="utf-8")

old = '''    MetricDefinition(
        key="exit_mach", label="Exit Mach number  M_e", unit="",
        stage=STAGE_PERFORMANCE, decimals_hint=6,
        help="Fixed by the area ratio and gamma alone."),'''
new = '''    MetricDefinition(
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
        help="Fixed by the area ratio and gamma alone."),'''
assert old in t
domain.write_text(t.replace(old, new, 1), encoding="utf-8")
print("metric table extended by 4")

# --- 2. the setup carries a feed pressure --------------------------------
service = pathlib.Path("rocketforge/application/analysis/trade_study_service.py")
s = service.read_text(encoding="utf-8")

old_setup = '''    chamber: thermo.ChamberCase
    performance: perf.PerformanceCase

    @property
    def scale_available(self) -> bool:
        return self.performance.scale.is_scaled'''
new_setup = '''    chamber: thermo.ChamberCase
    performance: perf.PerformanceCase
    feed_pressure: float | None = None
    """Pa. The pressure the propellants are *stored and fed at*, which is a
    feed-system state and emphatically not the chamber pressure. ``None``
    means the user did not state one, and then the density metrics are simply
    absent -- never computed at a pressure nobody supplied."""

    @property
    def scale_available(self) -> bool:
        return self.performance.scale.is_scaled

    @property
    def density_metrics_available(self) -> bool:
        """Whether this setup can produce a density impulse at all."""
        if self.feed_pressure is None:
            return False
        from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING

        return (PRODUCTION_FLUID_MAPPING.has(self.chamber.fuel)
                and PRODUCTION_FLUID_MAPPING.has(self.chamber.oxidiser))'''
assert old_setup in s
s = s.replace(old_setup, new_setup, 1)

old_canonical = '''            "scale_value": (None if self.performance.scale.value is None
                            else float(self.performance.scale.value)),
        }'''
new_canonical = '''            "scale_value": (None if self.performance.scale.value is None
                            else float(self.performance.scale.value)),
            "feed_pressure": (None if self.feed_pressure is None
                              else float(self.feed_pressure)),
        }'''
assert old_canonical in s
s = s.replace(old_canonical, new_canonical, 1)

# --- 3. the evaluator computes the stream densities once ------------------
old_slots = '''    __slots__ = ("_setup", "_solve_case", "_solve_performance", "_calls")'''
new_slots = '''    __slots__ = ("_setup", "_solve_case", "_solve_performance", "_calls",
                 "_densities", "_density_calls")'''
assert old_slots in s
s = s.replace(old_slots, new_slots, 1)

old_init = '''        self._calls: dict[str, int] = {STAGE_THERMOCHEMISTRY: 0,
                                       STAGE_PERFORMANCE: 0}'''
new_init = '''        self._calls: dict[str, int] = {STAGE_THERMOCHEMISTRY: 0,
                                       STAGE_PERFORMANCE: 0}
        # Stream states are fixed for a whole study: nothing a study varies
        # changes a propellant's tank temperature or its feed pressure. So the
        # densities are evaluated at most once each, whatever the point count,
        # and the counter below is what a test asserts that against.
        self._densities: tuple[Any, Any] | None = None
        self._density_calls = 0'''
assert old_init in s
s = s.replace(old_init, new_init, 1)

old_calls = '''    @property
    def calls(self) -> dict[str, int]:
        return dict(self._calls)'''
new_calls = '''    @property
    def calls(self) -> dict[str, int]:
        return dict(self._calls)

    @property
    def fluid_calls(self) -> int:
        """How many times a fluid property was actually evaluated."""
        return self._density_calls

    def stream_densities(self):
        """The two stream densities, evaluated once per study or not at all."""
        if self._densities is not None:
            return self._densities
        if not self._setup.density_metrics_available:
            self._densities = (None, None)
            return self._densities
        from rocketforge.application.analysis.fluid_property_provider import (
            availability,
            property_provider,
        )
        from rocketforge.engineering.propellants import (
            PRODUCTION_FLUID_MAPPING,
            stream_density,
        )

        if not availability().is_usable:
            self._densities = (None, None)
            return self._densities
        case = self._setup.chamber
        pressure = float(self._setup.feed_pressure)
        provider = property_provider()
        try:
            fuel = stream_density(provider,
                                  PRODUCTION_FLUID_MAPPING.require(case.fuel),
                                  float(case.fuel_temperature), pressure)
            oxidiser = stream_density(
                provider, PRODUCTION_FLUID_MAPPING.require(case.oxidiser),
                float(case.oxidiser_temperature), pressure)
        except Exception:  # noqa: BLE001 - an unusable state is an absent metric
            self._densities = (None, None)
            return self._densities
        self._density_calls += 2
        self._densities = (fuel, oxidiser)
        return self._densities'''
assert old_calls in s
s = s.replace(old_calls, new_calls, 1)

old_perf = '''        return StageOutcome(
            ok=True, value=outcome, metrics=performance_metrics(outcome),
            diagnostics=diagnostics,
            warning=outcome.kind == perf.OUTCOME_WARNING)'''
new_perf = '''        metrics = performance_metrics(outcome)
        metrics.update(self._density_metrics(point, outcome))
        return StageOutcome(
            ok=True, value=outcome, metrics=metrics,
            diagnostics=diagnostics,
            warning=outcome.kind == perf.OUTCOME_WARNING)

    def _density_metrics(self, point, outcome) -> dict[str, float | None]:
        """Validated densities and density impulse, or nothing at all.

        Nothing, rather than a fallback: a point with no validated density has
        no density impulse, and a study that *requires* it will mark that point
        NOT_EVALUABLE -- which is the honest verdict and is different from
        infeasible.
        """
        fuel, oxidiser = self.stream_densities()
        if fuel is None or oxidiser is None:
            return {}
        result = outcome.result
        if result is None:
            return {}
        from rocketforge.engineering.propellants import (
            density_impulse,
            mixture_bulk_density,
        )

        of = float(self.chamber_case(point.values).oxidiser_fuel_ratio)
        bulk = mixture_bulk_density(of, fuel, oxidiser)
        c_eff = _finite(result.effective_exhaust_velocity)
        isp = _finite(result.specific_impulse)
        metrics: dict[str, float | None] = {
            "fuel_density": fuel.density,
            "oxidiser_density": oxidiser.density,
            "bulk_propellant_density": bulk.density,
            "density_impulse": None,
        }
        if c_eff is not None and isp is not None:
            metrics["density_impulse"] = density_impulse(bulk, c_eff, isp).value
        return metrics'''
assert old_perf in s
s = s.replace(old_perf, new_perf, 1)

service.write_text(s, encoding="utf-8")
print("evaluator and setup extended")
