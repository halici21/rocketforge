"""The RocketForge trade-study evaluator: solve counts, and parity with the
canonical services.

Two claims are checked here that the generic tests cannot make, because they
are claims about the physics this evaluator is wired to:

**Caching changes the call count, never the science.** Every cached point is
compared against the result of invoking the canonical services directly for
that exact point. If reuse ever returned a chamber state belonging to a
different O/F, this is where it would show.

**The trade study computes nothing of its own.** Its Isp is the Rocket
Performance workspace's Isp for the same case, to the last bit, because there
is one implementation and the study reads it.

The stub provider from the application conftest is used wherever the claim is
about counting rather than about chemistry, so these run in the base
environment. The live CEA studies are separate and marked.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import performance_service as perf
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis import thermochemistry_service as thermo
from rocketforge.application.analysis import trade_study_service as ts
from rocketforge.application.analysis.trade_study_domain import (
    DEFERRED_VARIABLES,
    METRICS,
    STAGE_ORDER,
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    VARIABLE_SPECS,
    build_variable,
    metric_registry,
)
from rocketforge.engine.studies import (
    ComparisonOperator,
    ConstraintDefinition,
    EvaluationStatus,
    ExplicitNumericVariable,
    Feasibility,
    ObjectiveDefinition,
    ObjectiveDirection,
    StudyValidationError,
    WeightedScoreDefinition,
)
from rocketforge.engineering.nozzle import PerformanceScale, PerformanceScaleMode

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")

MAX_ISP = ObjectiveDefinition("specific_impulse", ObjectiveDirection.MAXIMIZE)
MIN_TC = ObjectiveDefinition("chamber_temperature", ObjectiveDirection.MINIMIZE)


@pytest.fixture()
def setup() -> ts.TradeStudySetup:
    """The demonstration case, unscaled, on the frozen gamma basis."""
    return ts.TradeStudySetup(chamber=thermo.DEFAULT_CASE,
                              performance=perf.DEFAULT_PERFORMANCE_CASE)


@pytest.fixture()
def sized_setup() -> ts.TradeStudySetup:
    return ts.TradeStudySetup(
        chamber=thermo.DEFAULT_CASE,
        performance=perf.DEFAULT_PERFORMANCE_CASE.replace(
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01)))


@pytest.fixture()
def of_variable():
    return build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)


@pytest.fixture()
def epsilon_variable():
    return ExplicitNumericVariable(
        key="area_ratio", label="Area ratio  Ae/At", stage=STAGE_PERFORMANCE,
        entries=(10.0, 20.0, 40.0, 80.0))


# ===========================================================================
# the domain registry
# ===========================================================================


def test_every_variable_declares_a_known_stage():
    for spec in VARIABLE_SPECS:
        assert spec["stage"] in STAGE_ORDER, spec["key"]


def test_the_chemistry_affecting_variables_are_at_the_chemistry_stage():
    """Getting this wrong costs hundreds of unnecessary solves, or worse."""
    stages = {spec["key"]: spec["stage"] for spec in VARIABLE_SPECS}
    assert stages["oxidiser_fuel_ratio"] == STAGE_THERMOCHEMISTRY
    assert stages["chamber_pressure"] == STAGE_THERMOCHEMISTRY


def test_the_nozzle_variables_are_at_the_performance_stage():
    stages = {spec["key"]: spec["stage"] for spec in VARIABLE_SPECS}
    assert stages["area_ratio"] == STAGE_PERFORMANCE
    assert stages["ambient_pressure"] == STAGE_PERFORMANCE
    assert stages["throat_area"] == STAGE_PERFORMANCE


def test_no_metric_is_called_plain_gamma():
    """Two exponents several per cent apart; one column named 'gamma' is a trap."""
    keys = {metric.key for metric in METRICS}
    assert "gamma" not in keys
    assert {"gamma_equilibrium", "gamma_frozen"} <= keys


def test_every_metric_declares_a_stage_and_a_help_line():
    for metric in METRICS:
        assert metric.stage in STAGE_ORDER, metric.key
        assert metric.help, metric.key


def test_the_scaled_metrics_are_marked_as_needing_a_size():
    registry = metric_registry()
    for key in ("total_thrust", "mass_flow", "momentum_thrust",
                "pressure_thrust"):
        assert registry[key].requires_scale, key
    for key in ("specific_impulse", "characteristic_velocity",
                "thrust_coefficient"):
        assert not registry[key].requires_scale, key


def test_the_deferred_variables_are_recorded_with_reasons():
    """An omission with a reason is a decision; without one it is an oversight."""
    keys = {entry["key"] for entry in DEFERRED_VARIABLES}
    assert {"reactant_temperature", "gamma_strategy", "provider"} <= keys
    for entry in DEFERRED_VARIABLES:
        assert len(entry["reason"]) > 60, entry["key"]


def test_gamma_strategy_is_not_offered_as_a_design_variable():
    """It changes the model. Two reductions in one front compare models."""
    assert "gamma_strategy" not in {spec["key"] for spec in VARIABLE_SPECS}


def test_reactant_temperature_is_not_offered_as_a_design_variable():
    assert "fuel_temperature" not in {spec["key"] for spec in VARIABLE_SPECS}
    assert "oxidiser_temperature" not in {spec["key"] for spec in VARIABLE_SPECS}


def test_a_variable_domain_refuses_an_impossible_range():
    with pytest.raises(ValueError):
        build_variable("oxidiser_fuel_ratio", start=0.0, end=4.0, count=5)
    with pytest.raises(ValueError):
        build_variable("area_ratio", start=0.5, end=40.0, count=5)


# ===========================================================================
# solve counts through the real evaluator
# ===========================================================================


def test_the_canonical_grid_costs_one_solve_per_chemistry_state(
        stub_gateway, setup, of_variable, epsilon_variable):
    """164 design points, 41 chamber solves. The blocking claim."""
    definition = ts.build_definition(setup, [of_variable, epsilon_variable],
                                     objectives=(MAX_ISP,))
    assert definition.point_count == 164
    assert definition.unique_solves(STAGE_THERMOCHEMISTRY) == 41

    evaluator = ts.RocketForgeEvaluator(setup)
    result = ts.run_trade_study(definition, setup, evaluator=evaluator)

    assert evaluator.calls[STAGE_THERMOCHEMISTRY] == 41
    assert evaluator.calls[STAGE_PERFORMANCE] == 164
    assert len(stub_gateway.calls) == 41         # the provider itself


def test_the_provider_call_count_matches_the_evaluator_count(
        stub_gateway, setup, of_variable, epsilon_variable):
    """Counted at the provider, not only at the service that wraps it."""
    definition = ts.build_definition(setup, [of_variable, epsilon_variable],
                                     objectives=(MAX_ISP,))
    ts.run_trade_study(definition, setup)
    assert len(stub_gateway.calls) == 41


def test_varying_only_the_area_ratio_costs_one_chamber_solve(
        stub_gateway, setup, epsilon_variable):
    definition = ts.build_definition(setup, [epsilon_variable],
                                     objectives=(MAX_ISP,))
    ts.run_trade_study(definition, setup)
    assert len(stub_gateway.calls) == 1


def test_varying_only_the_ambient_pressure_costs_one_chamber_solve(
        stub_gateway, setup):
    ambient = build_variable("ambient_pressure", start=0.0, end=101325.0,
                             count=12)
    definition = ts.build_definition(setup, [ambient], objectives=(MAX_ISP,))
    ts.run_trade_study(definition, setup)
    assert len(stub_gateway.calls) == 1


def test_varying_only_the_throat_area_costs_one_chamber_solve(
        stub_gateway, sized_setup):
    area = build_variable("throat_area", start=0.005, end=0.05, count=10)
    definition = ts.build_definition(sized_setup, [area],
                                     outputs=("total_thrust",))
    ts.run_trade_study(definition, sized_setup)
    assert len(stub_gateway.calls) == 1


def test_chamber_pressure_does_multiply_the_chemistry_solves(
        stub_gateway, setup, epsilon_variable):
    """The negative control: an upstream variable really is upstream."""
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=5)
    pc = build_variable("chamber_pressure", start=5.0e6, end=20.0e6, count=4)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 40.0, 80.0))
    definition = ts.build_definition(setup, [of, pc, eps], objectives=(MAX_ISP,))

    assert definition.point_count == 60
    assert definition.unique_solves(STAGE_THERMOCHEMISTRY) == 20

    ts.run_trade_study(definition, setup)
    assert len(stub_gateway.calls) == 20


def test_a_chamber_temperature_study_never_runs_the_performance_stage(
        stub_gateway, setup, of_variable):
    """No c*, no Cf, no Isp computed for a study that asked for none."""
    definition = ts.build_definition(setup, [of_variable],
                                     outputs=("chamber_temperature",))
    assert definition.required_stages(metric_registry()) == (
        STAGE_THERMOCHEMISTRY,)

    evaluator = ts.RocketForgeEvaluator(setup)
    ts.run_trade_study(definition, setup, evaluator=evaluator)
    assert evaluator.calls[STAGE_THERMOCHEMISTRY] == 41
    assert evaluator.calls[STAGE_PERFORMANCE] == 0


# ===========================================================================
# direct-solve parity — caching changes the count, not the science
# ===========================================================================


def test_every_cached_point_matches_a_direct_canonical_solve(
        stub_gateway, setup, of_variable, epsilon_variable):
    """The one test that would catch a chamber state reused for the wrong O/F."""
    definition = ts.build_definition(
        setup, [of_variable, epsilon_variable],
        outputs=("chamber_temperature", "characteristic_velocity",
                 "thrust_coefficient", "specific_impulse"))
    result = ts.run_trade_study(definition, setup)

    evaluator = ts.RocketForgeEvaluator(setup)
    compared = 0
    for point in result.points:
        chamber = thermo.solve_case(evaluator.chamber_case(point.values))
        direct = perf.solve_performance(
            chamber, evaluator.performance_case(point.values))
        assert direct.result is not None

        assert point.metrics["chamber_temperature"] == chamber.state.temperature
        for key, value in (
            ("characteristic_velocity", direct.result.characteristic_velocity),
            ("thrust_coefficient", direct.result.thrust_coefficient),
            ("specific_impulse", direct.result.specific_impulse),
        ):
            assert point.metrics[key] == value, (point.index, key)
            compared += 1
    assert compared == 164 * 3


def test_the_direct_solve_costs_the_naive_number_of_provider_calls(
        stub_gateway, setup, of_variable, epsilon_variable):
    """What the cache is saving, measured rather than asserted."""
    definition = ts.build_definition(setup, [of_variable, epsilon_variable],
                                     objectives=(MAX_ISP,))
    ts.run_trade_study(definition, setup)
    cached = len(stub_gateway.calls)

    evaluator = ts.RocketForgeEvaluator(setup)
    for point in definition.enumerate():
        thermo.solve_case(evaluator.chamber_case(point.values))
    naive = len(stub_gateway.calls) - cached

    assert cached == 41
    assert naive == 164
    assert naive / cached == pytest.approx(4.0)


# ===========================================================================
# statuses through the real chain
# ===========================================================================


def test_a_condensed_chamber_refuses_performance_but_keeps_chemistry(
        condensed_gateway, setup):
    """Stage-aware failure: Tc exists, Isp does not."""
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=3)
    definition = ts.build_definition(setup, [of],
                                     outputs=("chamber_temperature",))
    result = ts.run_trade_study(definition, setup)
    assert all(p.ok for p in result.points)
    assert all(p.metrics["chamber_temperature"] is not None
               for p in result.points)


def test_the_same_chamber_fails_a_study_that_requires_isp(
        condensed_gateway, setup):
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=3)
    definition = ts.build_definition(setup, [of], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    assert all(p.status is EvaluationStatus.FAILED for p in result.points)
    assert all(p.feasibility is Feasibility.NOT_EVALUATED for p in result.points)


def test_an_assigned_enthalpy_warning_reaches_the_study_summary(
        warning_gateway, setup, of_variable):
    definition = ts.build_definition(setup, [of_variable], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)

    codes = {d.code: d for d in result.diagnostics}
    assert "PROVIDER_ASSIGNED_ENTHALPY_REACTANT" in codes
    row = codes["PROVIDER_ASSIGNED_ENTHALPY_REACTANT"]
    assert row.count == 41 and row.total == 41
    assert row.origin == STAGE_THERMOCHEMISTRY


def test_a_warning_point_is_still_feasible_and_still_ranks(
        warning_gateway, setup, of_variable):
    """A caveat is not a penalty."""
    definition = ts.build_definition(setup, [of_variable], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    assert all(p.status is EvaluationStatus.WARNING for p in result.points)
    assert result.feasible_count == 41
    assert len(result.ranking) == 41


def test_a_missing_provider_fails_every_point_without_crashing(
        absent_gateway, setup, of_variable):
    """No fake gas, no perfect-gas substitute, no reference values."""
    definition = ts.build_definition(setup, [of_variable], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    assert all(p.status is EvaluationStatus.FAILED for p in result.points)
    assert all(p.metrics.get("specific_impulse") is None for p in result.points)


# ===========================================================================
# re-analysis through the service
# ===========================================================================


def test_changing_an_objective_costs_no_provider_call(
        stub_gateway, setup, of_variable, epsilon_variable):
    definition = ts.build_definition(setup, [of_variable, epsilon_variable],
                                     outputs=("chamber_temperature",),
                                     objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    before = len(stub_gateway.calls)

    flipped = definition.replace(objectives=(MIN_TC,))
    again = ts.reanalyse(result, flipped)

    assert len(stub_gateway.calls) == before
    assert [dict(p.metrics) for p in again.points] == [dict(p.metrics)
                                                       for p in result.points]
    assert again.ranking != result.ranking


def test_changing_a_constraint_costs_no_provider_call(
        stub_gateway, setup, of_variable):
    definition = ts.build_definition(setup, [of_variable],
                                     outputs=("chamber_temperature",))
    result = ts.run_trade_study(definition, setup)
    before = len(stub_gateway.calls)

    loose = ts.reanalyse(result, definition.replace(constraints=(
        ConstraintDefinition("chamber_temperature", ComparisonOperator.LE,
                             4000.0),)))
    tight = ts.reanalyse(result, definition.replace(constraints=(
        ConstraintDefinition("chamber_temperature", ComparisonOperator.LE,
                             3300.0),)))

    assert len(stub_gateway.calls) == before
    assert loose.feasible_count > tight.feasible_count


def test_changing_weights_costs_no_provider_call_and_moves_no_front(
        stub_gateway, setup, of_variable, epsilon_variable):
    definition = ts.build_definition(
        setup, [of_variable, epsilon_variable],
        outputs=("chamber_temperature",),
        objectives=(MAX_ISP, MIN_TC),
        scoring=WeightedScoreDefinition(
            weights={"specific_impulse": 1.0, "chamber_temperature": 1.0}))
    result = ts.run_trade_study(definition, setup)
    before = len(stub_gateway.calls)

    again = ts.reanalyse(result, definition.replace(
        scoring=WeightedScoreDefinition(
            weights={"specific_impulse": 500.0,
                     "chamber_temperature": 0.001})))

    assert len(stub_gateway.calls) == before
    assert again.pareto_indices == result.pareto_indices
    assert again.scored and result.scored


# ===========================================================================
# provenance and exclusions
# ===========================================================================


def test_the_provenance_names_both_owners_and_the_fingerprint(
        stub_gateway, setup, of_variable):
    definition = ts.build_definition(setup, [of_variable], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    record = result.provenance

    assert record["performance_model"]["owner"] == "RocketForge"
    assert record["provider"]["label"]
    assert record["definition_fingerprint"] == definition.fingerprint
    assert record["baseline"]["gamma_basis"]


def test_the_provenance_says_the_oracle_was_not_used(
        stub_gateway, setup, of_variable):
    """CEA's own c*, Cf and Isp are a validation tool, not study physics."""
    definition = ts.build_definition(setup, [of_variable], objectives=(MAX_ISP,))
    result = ts.run_trade_study(definition, setup)
    assert result.provenance["oracle_used"] is False
    assert "validation" in result.provenance["oracle_note"].lower()


def test_the_service_never_imports_the_performance_oracle():
    """Structural: a CEA Isp cannot reach a study metric even by accident."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(ts))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not any("performance_oracle" in name for name in names), names
    assert not any(name.startswith("rocketforge.providers") for name in names)


def _phase_5f_modules():
    """Every production module this phase added."""
    import pathlib

    root = pathlib.Path(ts.__file__).resolve().parents[3]
    paths = [
        root / "rocketforge" / "application" / "analysis" / "trade_study_service.py",
        root / "rocketforge" / "application" / "analysis" / "trade_study_domain.py",
    ]
    paths.extend(sorted((root / "rocketforge" / "engine" / "studies").glob("*.py")))
    return paths


def _identifiers(path) -> set[str]:
    """Every name, attribute and string literal a module uses, prose excluded.

    Read from the syntax tree rather than by scanning text. These modules
    explain at length *why* ``density_hint`` must not enter a calculation, and
    a substring scan reports exactly those sentences -- the same false positive
    that read "isp" out of ``chamberPressureDisplay`` three separate times in
    Phase 5D, and that flagged this phase's own disclaimer on the first two
    attempts at this test.

    Docstring nodes are skipped **by identity**. Subtracting the text that
    ``ast.get_docstring`` returns does not work: that value is cleaned of
    indentation while the ``Constant`` node holds the raw string, so the two
    never match and the prose survives the subtraction.

    String literals that are not docstrings are kept, because a metric key is
    a string: a study reaching for ``"density_impulse"`` would do it by name.
    """
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))

    docstring_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = getattr(node, "body", None)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docstring_nodes.add(id(body[0].value))

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstring_nodes:
                names.add(node.value)
    return names


def test_no_trade_study_code_touches_density_hint():
    """Blocking. ``density_hint`` is display-only metadata by 5A/5B contract.

    A density impulse computed from it would be a physical claim resting on a
    number never validated as a physical property, at a temperature, pressure
    and phase it does not record.

    **Scope changed, invariant unchanged.** Phase 5F banned every identifier
    containing "density" from these modules, because at that time density had
    no validated source in this program and so any density here could only have
    come from the hint. The fluids foundation gives density a validated source,
    so the blanket form would now forbid correct work. What it was protecting
    is asserted directly instead, and the negative control below is stronger
    for it: it must fire on a ``density_hint`` read *inside* a module full of
    legitimate density code, which the blanket rule could not distinguish.
    """
    for path in _phase_5f_modules():
        assert "density_hint" not in _identifiers(path), path.name


def test_trade_study_density_comes_from_the_propellant_metrics_layer():
    """The positive half: density must arrive by the validated route.

    The ban alone is satisfiable by having no density at all. This says where
    density is allowed to come from, so a future edit cannot reintroduce the
    hint by another name and still pass.
    """
    source = (_phase_5f_modules()[0]).read_text(encoding="utf-8")
    assert "rocketforge.engineering.propellants" in source
    assert "stream_density" in source
    assert "mixture_bulk_density" in source


def test_the_density_audit_would_catch_a_real_use():
    """The negative control, in both directions.

    It must fire on the use and stay silent on the explanation, or it would be
    enforcing the opposite of what it is for.
    """
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        offending = pathlib.Path(folder) / "offending.py"
        offending.write_text(
            "def f(p):\n"
            '    """Never mention the forbidden field."""\n'
            "    return p.density_hint * 9.0\n", encoding="utf-8")
        assert "density_hint" in _identifiers(offending)

        # The case the old blanket rule could not tell apart: a module doing
        # legitimate density work *and* reading the hint. The rule must fire.
        mixed = pathlib.Path(folder) / "mixed.py"
        mixed.write_text(
            "from rocketforge.engineering.propellants import stream_density\n"
            "def f(provider, binding, p):\n"
            "    good = stream_density(provider, binding, 90.0, 3e5).density\n"
            "    return good + p.density_hint\n", encoding="utf-8")
        assert "density_hint" in _identifiers(mixed)

        innocent = pathlib.Path(folder) / "innocent.py"
        innocent.write_text(
            '"""density_hint is deliberately unused here."""\n'
            "def f():\n"
            '    """It is display-only metadata."""\n'
            "    return 1.0\n", encoding="utf-8")
        assert "density_hint" not in _identifiers(innocent)

        # And legitimate density work alone must NOT trip it, or the rule
        # would be forbidding the thing it was never about.
        legitimate = pathlib.Path(folder) / "legitimate.py"
        legitimate.write_text(
            "def f(bulk, c_eff):\n"
            "    return bulk.density * c_eff\n", encoding="utf-8")
        assert "density_hint" not in _identifiers(legitimate)


def test_no_trade_study_code_reimplements_a_performance_formula():
    """The study reads Phase 5E's numbers; it does not recompute them."""
    banned = {"STANDARD_GRAVITY", "vandenkerckhove", "sqrt", "pow", "g0",
              "choked_mass_flow_coefficient", "characteristic_velocity_of"}
    for path in _phase_5f_modules():
        leaked = _identifiers(path) & banned
        assert not leaked, f"{path.name} uses {leaked}"


def test_the_formula_audit_would_catch_a_real_reimplementation():
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        path = pathlib.Path(folder) / "offending.py"
        path.write_text("import math\n"
                        "def cstar(r, t):\n"
                        "    return math.sqrt(r * t)\n", encoding="utf-8")
        assert _identifiers(path) & {"sqrt"}


# ===========================================================================
# live, against the real provider and the real performance model
# ===========================================================================


@requires_cea
def test_the_live_canonical_study_costs_41_chamber_solves(setup, of_variable,
                                                          epsilon_variable):
    definition = ts.build_definition(setup, [of_variable, epsilon_variable],
                                     objectives=(MAX_ISP,),
                                     title="canonical live study A")
    evaluator = ts.RocketForgeEvaluator(setup)
    result = ts.run_trade_study(definition, setup, evaluator=evaluator)

    assert definition.point_count == 164
    assert evaluator.calls[STAGE_THERMOCHEMISTRY] == 41
    assert evaluator.calls[STAGE_PERFORMANCE] == 164
    assert result.failed_count == 0
    assert result.feasible_count == 164


@requires_cea
def test_the_live_study_matches_direct_canonical_solves(setup, of_variable):
    """Live parity, on a smaller grid so the test stays quick."""
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(20.0, 60.0))
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=5)
    definition = ts.build_definition(
        setup, [of, eps],
        outputs=("chamber_temperature", "characteristic_velocity",
                 "specific_impulse"))
    result = ts.run_trade_study(definition, setup)

    evaluator = ts.RocketForgeEvaluator(setup)
    for point in result.points:
        chamber = thermo.solve_case(evaluator.chamber_case(point.values))
        direct = perf.solve_performance(
            chamber, evaluator.performance_case(point.values))
        assert point.metrics["chamber_temperature"] == chamber.state.temperature
        assert (point.metrics["specific_impulse"]
                == direct.result.specific_impulse)
        assert (point.metrics["characteristic_velocity"]
                == direct.result.characteristic_velocity)


@requires_cea
def test_a_live_two_objective_study_produces_a_front(setup, of_variable):
    """Isp against chamber temperature — a real trade, not a synthetic one."""
    definition = ts.build_definition(
        setup, [of_variable],
        outputs=("chamber_temperature",),
        objectives=(MAX_ISP, MIN_TC))
    result = ts.run_trade_study(definition, setup)

    assert result.complete
    assert 1 < len(result.pareto_indices) < 41       # a real trade-off
    for index in result.pareto_indices:
        assert result.by_index(index).eligible_for_decision


@requires_cea
def test_a_live_constraint_makes_some_points_infeasible(setup, of_variable):
    definition = ts.build_definition(
        setup, [of_variable],
        outputs=("chamber_temperature",),
        objectives=(MAX_ISP,),
        constraints=(ConstraintDefinition(
            "chamber_temperature", ComparisonOperator.LE, 3500.0),))
    result = ts.run_trade_study(definition, setup)

    assert result.feasible_count > 0
    assert result.infeasible_count > 0
    for point in result.points:
        if point.feasibility is Feasibility.INFEASIBLE:
            assert point.metrics["chamber_temperature"] > 3500.0
            assert point.violated
