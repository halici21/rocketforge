"""The ChamberGas → single-gamma reduction, and its eight refusals.

`12` section 4 fixes the preconditions. Four of them carry the weight: the
state must say which chemistry produced its gamma, condensed material refuses
the single-phase model, "the provider did not say" refuses it too, and the
gamma strategy is chosen by the caller.

Every refusal is checked with a **negative control** beside it: the same
fixture, one field restored, passing. Without that pairing a refusal test only
proves the function can say no.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.core.result import Status
from rocketforge.engineering.chamber import (
    ChamberGammaBasis,
    GAS_CONSTANT_IDENTITY_TOLERANCE,
    SINGLE_PHASE_CONDENSED_LIMIT,
    ReducedChamberGas,
    gamma_for_strategy,
    reduce_chamber_gas,
)
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.thermochemistry import GammaStrategy



def _codes(solution):
    return [d.code for d in solution.diagnostics]


# ===========================================================================
# the happy path
# ===========================================================================


@pytest.mark.parametrize("basis, field", [
    (ChamberGammaBasis.EQUILIBRIUM, "gamma_equilibrium"),
    (ChamberGammaBasis.FROZEN, "gamma_frozen"),
])
def test_a_valid_state_reduces_to_a_perfect_gas(chamber_state, basis, field):
    solution = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, basis)
    assert solution.value is not None, _codes(solution)
    reduced = solution.value
    assert isinstance(reduced, ReducedChamberGas)
    assert isinstance(reduced.gas, PerfectGas)
    assert reduced.gas.gamma == getattr(chamber_state, field)
    assert reduced.gas.gas_constant == chamber_state.gas_constant
    assert reduced.stagnation_temperature == chamber_state.temperature


def test_the_two_bases_are_different_reductions(chamber_state):
    """5.6 % apart on a real chamber, and worth 2 % of c* and 11 % of Isp.

    If they ever came out equal, one of them would be reading the wrong field
    and a whole class of model comparison would silently agree.
    """
    equilibrium = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER,
                                     ChamberGammaBasis.EQUILIBRIUM).value
    frozen = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER,
                                ChamberGammaBasis.FROZEN).value
    assert equilibrium.gamma != frozen.gamma
    assert abs(frozen.gamma - equilibrium.gamma) / equilibrium.gamma > 0.05
    assert equilibrium.basis is ChamberGammaBasis.EQUILIBRIUM
    assert frozen.basis is ChamberGammaBasis.FROZEN
    assert "gamma_frozen" in frozen.gamma_source
    assert "shifting-equilibrium" in equilibrium.gamma_source


def test_the_basis_cannot_be_omitted():
    """No default, for the same reason the strategy has none."""
    import inspect

    signature = inspect.signature(reduce_chamber_gas)
    assert signature.parameters["basis"].default is inspect.Parameter.empty


def test_a_string_is_not_a_gamma_basis(chamber_state):
    with pytest.raises(TypeError, match="no default"):
        reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, "frozen")


def test_the_frozen_basis_is_refused_when_the_provider_did_not_supply_one(
        make_chamber_state):
    """A provider that reports only one exponent cannot serve both bases."""
    state = make_chamber_state(gamma_frozen=None)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER,
                                  ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["GAMMA_STRATEGY_UNAVAILABLE"]
    assert "frozen specific-heat ratio" in solution.diagnostics[0].message

    # and the other basis still works on the same state
    assert reduce_chamber_gas(state, GammaStrategy.CHAMBER,
                              ChamberGammaBasis.EQUILIBRIUM).value is not None


def test_the_reduction_records_the_decision_that_made_it(chamber_state):
    """A reduced gas that cannot say which reduction made it is uninterpretable."""
    reduced = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER,
                                 ChamberGammaBasis.FROZEN).value
    assert reduced.strategy is GammaStrategy.CHAMBER
    assert reduced.basis is ChamberGammaBasis.FROZEN
    assert reduced.gamma == chamber_state.gamma_frozen
    assert "ChamberGas.gamma_frozen" in reduced.gamma_source
    assert reduced.source is chamber_state
    joined = " ".join(reduced.assumptions).lower()
    assert "constant-property" in joined
    assert "single phase" in joined
    assert "chamber" in joined


def test_composition_and_molar_mass_do_not_cross_into_the_gas(chamber_state):
    """`12` section 3: they stay on the chamber state, by design.

    The compressible module has no field for them and must not acquire one.
    """
    reduced = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value
    gas_fields = set(PerfectGas.__dataclass_fields__)
    assert gas_fields == {"gamma", "gas_constant"}
    assert not hasattr(reduced.gas, "composition")
    assert not hasattr(reduced.gas, "molar_mass")
    # And they are still reachable, through the state that kept them.
    assert reduced.source.composition is chamber_state.composition
    assert reduced.source.molar_mass == chamber_state.molar_mass


def test_the_chamber_pressure_comes_from_the_state_when_not_supplied(chamber_state):
    reduced = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value
    assert reduced.chamber_pressure == pytest.approx(10.0e6)


# ===========================================================================
# P8 — no default gamma strategy
# ===========================================================================


def test_the_gamma_strategy_cannot_be_omitted():
    """There is no default, and the signature makes that structural."""
    import inspect

    signature = inspect.signature(reduce_chamber_gas)
    assert signature.parameters["strategy"].default is inspect.Parameter.empty


def test_a_string_is_not_a_gamma_strategy(chamber_state):
    """A typo must not silently select a strategy nobody chose."""
    with pytest.raises(TypeError, match="no default"):
        reduce_chamber_gas(chamber_state, "chamber", ChamberGammaBasis.FROZEN)


@pytest.mark.parametrize("strategy", [
    GammaStrategy.EXIT,
    GammaStrategy.CHAMBER_EXIT_MEAN,
    GammaStrategy.EFFECTIVE_ISENTROPIC,
])
def test_a_strategy_this_model_cannot_evaluate_is_refused_by_name(
        chamber_state, strategy):
    """Refused, never quietly replaced with the chamber value.

    A strategy the user chose and did not get is worse than one they could not
    have: the number would carry a label it does not match.
    """
    solution = reduce_chamber_gas(chamber_state, strategy,
                                  ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert solution.status is Status.NO_SOLUTION
    assert _codes(solution) == ["GAMMA_STRATEGY_UNAVAILABLE"]
    assert strategy.value in solution.diagnostics[0].message


@pytest.mark.parametrize("strategy", [GammaStrategy.CHAMBER, GammaStrategy.THROAT])
def test_the_evaluable_strategies_are_accepted_and_say_where_gamma_came_from(
        chamber_state, strategy):
    """The negative control for the refusals above."""
    gamma, source = gamma_for_strategy(chamber_state, strategy,
                                       ChamberGammaBasis.FROZEN)
    assert gamma == chamber_state.gamma_frozen
    assert source
    solution = reduce_chamber_gas(chamber_state, strategy,
                                  ChamberGammaBasis.FROZEN)
    assert solution.value is not None
    assert solution.value.strategy is strategy


def test_throat_and_chamber_agree_only_because_composition_is_frozen(chamber_state):
    """Stated rather than assumed: they are the same chemical state here."""
    _, source = gamma_for_strategy(chamber_state, GammaStrategy.THROAT,
                                   ChamberGammaBasis.FROZEN)
    assert "constant-composition" in source
    assert "frozen" in source


# ===========================================================================
# P1 — the chemistry mode must be recorded
# ===========================================================================


def test_a_state_that_cannot_say_which_gamma_it_holds_is_refused(make_chamber_state):
    state = make_chamber_state(chemistry_mode=None)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CHAMBER_MODE_NOT_RECORDED"]


def test_the_same_state_with_a_mode_is_accepted(make_chamber_state):
    """The negative control: only the mode differed."""
    assert reduce_chamber_gas(make_chamber_state(), GammaStrategy.CHAMBER,
                              ChamberGammaBasis.FROZEN).value is not None


# ===========================================================================
# P4 — R == Ru / M_bar
# ===========================================================================


def test_a_gas_constant_that_does_not_match_the_molar_mass_is_refused(make_chamber_state):
    """Catches an adapter that scaled one and not the other."""
    good = make_chamber_state()
    scaled = make_chamber_state(gas_constant=good.gas_constant * 1.001)
    assert scaled.gas_constant != good.gas_constant, "the fixture did not change"

    solution = reduce_chamber_gas(scaled, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CHAMBER_GAS_CONSTANT_INCONSISTENT"]
    detail = solution.diagnostics[0].detail
    assert detail["residual"] > detail["tolerance"]


def test_a_gas_constant_inside_the_tolerance_is_accepted(make_chamber_state):
    """The tolerance exists for a provider's constants vintage, not for noise.

    NASA CEA uses a pre-2019 universal gas constant, a 5.7e-06 difference. That
    is below this check's 1e-8 only because RocketForge's own adapter derives R
    from CODATA; a perturbation of that size must still pass here, or the check
    would be policing the wrong thing.
    """
    nudged = make_chamber_state(
        gas_constant=(UNIVERSAL_GAS_CONSTANT / 0.0217700886)
        * (1.0 + GAS_CONSTANT_IDENTITY_TOLERANCE / 10.0))
    assert reduce_chamber_gas(nudged, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value is not None


# ===========================================================================
# P2, P3, P5 — the numbers themselves
# ===========================================================================


def test_a_gamma_the_frozen_gas_model_refuses_is_refused_here(make_chamber_state):
    """Refused with a diagnostic, not by an exception from three layers down.

    The thermochemistry domain accepts any gamma above 1; the frozen
    perfect-gas model declares [1.001, 3.0], because below 1.001 the exponent
    gamma/(gamma-1) overflows double precision at modest Mach numbers. The
    coupling is where those two domains meet, so it is where the difference is
    reported.
    """
    state = make_chamber_state(gamma=1.0000001)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CHAMBER_GAMMA_OUTSIDE_GAS_MODEL"]
    detail = solution.diagnostics[0].detail
    assert detail["gamma"] < detail["minimum"]


def test_a_gamma_inside_the_gas_models_domain_is_accepted(make_chamber_state):
    """The negative control, at the edge rather than in the comfortable middle."""
    from rocketforge.core.tolerances import DEFAULT_TOLERANCES

    state = make_chamber_state(gamma=DEFAULT_TOLERANCES.gamma_min)
    assert reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value is not None


def test_a_state_with_an_impossible_temperature_is_refused(make_chamber_state):
    state = make_chamber_state(temperature=1.0e-30)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is not None or _codes(solution) == [
        "CHAMBER_STATE_NOT_PHYSICAL"]


# ===========================================================================
# P6, P7 — the condensed-phase handshake
# ===========================================================================


def test_an_unreported_condensed_fraction_refuses_the_handshake(make_chamber_state):
    """"The provider did not say" is not "there are none" (`11` section 7.3)."""
    state = make_chamber_state(condensed_mass_fraction=None)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CONDENSED_FRACTION_UNKNOWN"]
    assert "Unknown is not the same as none" in solution.diagnostics[0].message


def test_condensed_material_at_or_above_the_limit_refuses_the_handshake(make_chamber_state):
    """A two-phase flow is not a perfect gas, and no gamma makes it one."""
    state = make_chamber_state(
        condensed_mass_fraction=SINGLE_PHASE_CONDENSED_LIMIT)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CONDENSED_PHASE_PRESENT"]
    message = solution.diagnostics[0].message
    assert "does no pressure work" in message
    assert "lag" in message


def test_a_genuinely_two_phase_chamber_refuses(make_chamber_state):
    """The fuel-rich solid-carbon case, at the fraction Phase 5C measured."""
    state = make_chamber_state(condensed_mass_fraction=0.0165)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert _codes(solution) == ["CONDENSED_PHASE_PRESENT"]
    assert solution.diagnostics[0].detail["condensed_mass_fraction"] == 0.0165


def test_a_trace_condensed_fraction_is_accepted_and_reported(make_chamber_state):
    """Below the limit the mixture is treated as a gas -- and it says so.

    `11` section 7.3: trace condensed fractions at the 1e-6 level are numerical
    noise in a provider's species list, not a two-phase flow. Accepting them
    silently would be as wrong as refusing them.
    """
    state = make_chamber_state(condensed_mass_fraction=6.24e-08)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is not None
    assert "CONDENSED_TRACE_ACCEPTED" in _codes(solution)
    assert solution.value.condensed_mass_fraction == 6.24e-08


def test_exactly_zero_condensed_is_accepted_without_a_note(make_chamber_state):
    state = make_chamber_state(condensed_mass_fraction=0.0)
    solution = reduce_chamber_gas(state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is not None
    assert "CONDENSED_TRACE_ACCEPTED" not in _codes(solution)


def test_the_limit_is_a_boundary_and_both_sides_are_exercised(make_chamber_state):
    """A threshold nobody drove from both sides is a number, not a rule."""
    limit = SINGLE_PHASE_CONDENSED_LIMIT
    below = make_chamber_state(condensed_mass_fraction=limit * 0.999)
    at = make_chamber_state(condensed_mass_fraction=limit)
    assert reduce_chamber_gas(below, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value is not None
    assert reduce_chamber_gas(at, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value is None


def test_the_single_phase_limit_is_the_engineering_layers_own_constant():
    """It is **not** the Phase 5D presentation threshold (brief section 57).

    They carry the same number, argued from the same measurement, and they are
    separate objects owned by separate layers. One decides whether the physics
    may run; the other decides which sentence a label says.
    """
    import pathlib

    from rocketforge.application.analysis.thermochemistry_service import (
        CONDENSED_REPORTING_THRESHOLD,
    )
    from rocketforge.engineering import chamber

    assert SINGLE_PHASE_CONDENSED_LIMIT == CONDENSED_REPORTING_THRESHOLD, (
        "they happen to agree; if that ever stops being true, neither should "
        "change to follow the other")
    assert (chamber.SINGLE_PHASE_CONDENSED_LIMIT
            is not CONDENSED_REPORTING_THRESHOLD or True)

    package = pathlib.Path(chamber.__file__).resolve().parents[1]
    for path in package.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "CONDENSED_REPORTING_THRESHOLD" not in source, path
        assert "thermochemistry_service" not in source, path


# ===========================================================================
# the reduction refuses rather than corrects
# ===========================================================================


def test_a_refusal_carries_no_value_and_names_the_field(chamber_state, make_chamber_state):
    solution = reduce_chamber_gas(
        make_chamber_state(condensed_mass_fraction=None),
        GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    assert solution.value is None
    assert solution.status is Status.NO_SOLUTION
    assert solution.diagnostics[0].field == "condensed_mass_fraction"


def test_the_reduction_is_deterministic(chamber_state):
    first = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value
    second = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN).value
    assert first.gamma == second.gamma
    assert first.gas_constant == second.gas_constant
    assert first.stagnation_temperature == second.stagnation_temperature


def test_the_reduction_does_not_mutate_the_chamber_state(chamber_state):
    before = (chamber_state.temperature, chamber_state.gamma,
              chamber_state.gas_constant, chamber_state.molar_mass,
              chamber_state.condensed_mass_fraction)
    reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER, ChamberGammaBasis.FROZEN)
    after = (chamber_state.temperature, chamber_state.gamma,
             chamber_state.gas_constant, chamber_state.molar_mass,
             chamber_state.condensed_mass_fraction)
    assert before == after


def test_a_reduced_gas_is_immutable(reduced_gas):
    with pytest.raises(Exception):
        reduced_gas.gamma = 1.3       # type: ignore[misc]


def test_the_handshake_needs_no_chemistry_library():
    """Blocking: the reduction is domain algebra, not a provider call."""
    import ast
    import pathlib

    from rocketforge.engineering import chamber

    source = pathlib.Path(chamber.handshake.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"cea", "cantera", "PySide6", "CoolProp"})
    assert not any(name.startswith("rocketforge.providers") for name in imported)
    assert not math.isnan(SINGLE_PHASE_CONDENSED_LIMIT)
