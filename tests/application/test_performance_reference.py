"""The external NASA performance reference, and what it is allowed to claim.

The dataset carries c* and Isp -- the two quantities Phase 5D deliberately
refused to load, because RocketForge did not own them then. It is a **separate**
file, so the Phase 5D contract that its thermochemistry reference is
thermochemistry-only is untouched, and a test here asserts that.

The distinction this module exists to keep is between a **validation** and a
**model comparison**. The same published number is both, depending on what it
is compared against, and the verdict wording follows the role rather than the
size of the residual.
"""

from __future__ import annotations

import copy
import json

import pytest

from rocketforge.application.analysis import performance_reference as ref
from rocketforge.application.analysis import thermochemistry_provider as gateway

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture()
def payload():
    return copy.deepcopy(ref.load_performance_reference())


# ===========================================================================
# the dataset
# ===========================================================================


def test_the_dataset_ships_with_the_application():
    from rocketforge.application.analysis.reference_comparison import reference_root

    path = reference_root() / ref.PERFORMANCE_REFERENCE
    assert path.exists(), path
    assert json.loads(path.read_text(encoding="utf-8"))["kind"] == "rocket_performance"


def test_a_dataset_of_the_wrong_kind_is_refused(tmp_path, monkeypatch):
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"kind": "thermochemistry_chamber"}),
                     encoding="utf-8")
    monkeypatch.setattr(ref, "reference_root", lambda: tmp_path)
    ref.load_performance_reference.cache_clear()
    try:
        with pytest.raises(ValueError, match="not a rocket performance"):
            ref.load_performance_reference("wrong.json")
    finally:
        ref.load_performance_reference.cache_clear()


def test_the_phase_5d_thermochemistry_dataset_is_untouched():
    """Phase 5D's contract was that it carries no performance value. It still does."""
    from rocketforge.application.analysis.thermochemistry_reference import (
        load_reference,
    )

    thermochemistry = load_reference()
    assert [entry["key"] for entry in thermochemistry["published"]] == [
        "chamber_temperature", "chamber_molar_mass"]
    for entry in thermochemistry["not_compared"]:
        assert "value" not in entry, entry
    assert len(thermochemistry["not_compared"]) == 3


def test_the_two_datasets_are_separate_files():
    assert ref.PERFORMANCE_REFERENCE != "thermochemistry_nasa_cea_2002_lox_lh2.json"


def test_the_published_case_is_the_one_the_source_states(payload):
    case = ref.performance_reference_case(payload)
    assert case.case["oxidiser"] == "LOX"
    assert case.case["fuel"] == "LH2"
    assert case.case["oxidiser_fuel_ratio"] == pytest.approx(6.0)
    assert case.case["area_ratio"] == pytest.approx(40.0)
    assert case.case["chamber_pressure_Pa"] == pytest.approx(
        1000.0 * 6894.757293168361)


def test_the_reference_condition_is_recorded_not_assumed(payload):
    """CEA's printed Cf and Isp are optimum-expansion values, and it says so."""
    case = ref.performance_reference_case(payload)
    assert case.conditions["reference_condition"] == "optimum expansion, pe = pa"
    note = case.reference_condition_note
    assert "optimum-expansion" in note
    assert "Cf_printed" in note or "Cf_reported" in note or "printed" in note
    assert "5.6" in note, "the size of the error this avoids should be stated"


def test_the_source_is_identified_and_its_independence_stated(payload):
    case = ref.performance_reference_case(payload)
    assert "NASA" in case.citation and "2002" in case.citation
    assert "2002 Fortran" in case.source["independence"]


def test_what_the_source_validates_is_stated(payload):
    """It validates the oracle. It does not validate RocketForge's own model."""
    case = ref.performance_reference_case(payload)
    assert case.validates["directly"] == "the NASA CEA oracle path"
    assert "RocketForge" in case.validates["not_directly"]
    reason = case.validates["reason"]
    assert "calorically perfect" in reason
    assert "model difference" in reason


# ===========================================================================
# tolerance and units
# ===========================================================================


def test_the_tolerance_is_the_sources_printed_precision(payload):
    case = ref.performance_reference_case(payload)
    c_star = next(q for q in case.published if q.key == "characteristic_velocity")
    assert c_star.significant_figures == 5
    # 7560.0 printed to five significant figures: the last digit is the
    # tenths place, so the box is half a tenth wide.
    assert c_star.tolerance == pytest.approx(0.05 / 7560.0, rel=1e-9)
    isp = next(q for q in case.published if q.key == "specific_impulse")
    assert isp.significant_figures == 4
    assert isp.tolerance == pytest.approx(0.05 / 431.2, rel=1e-9)


def test_the_foot_conversion_is_exact(payload):
    case = ref.performance_reference_case(payload)
    c_star = next(q for q in case.published if q.key == "characteristic_velocity")
    assert c_star.unit == "ft/s"
    assert c_star.si_unit == "m/s"
    assert c_star.to_si == 0.3048
    assert c_star.si_value == pytest.approx(7560.0 * 0.3048)


def test_isp_is_published_in_seconds_and_stays_in_seconds(payload):
    """RocketForge never labels a value in m/s as an Isp."""
    case = ref.performance_reference_case(payload)
    isp = next(q for q in case.published if q.key == "specific_impulse")
    assert isp.unit == "s" and isp.si_unit == "s"
    assert "m/s" in isp.conversion_note
    assert "never labels" in isp.conversion_note


# ===========================================================================
# the comparison, and its role
# ===========================================================================


def test_a_comparison_without_a_stated_role_is_refused(payload):
    case = ref.performance_reference_case(payload)
    with pytest.raises(ValueError, match="role must be"):
        ref.compare_published(case, {}, role="whatever",
                              source_of_computed="x")


def test_the_verdict_wording_follows_the_role(payload):
    """The same residual is a failure for one role and a difference for the other."""
    case = ref.performance_reference_case(payload)
    far = {"characteristic_velocity": 2000.0, "specific_impulse": 400.0}

    validation = ref.compare_published(case, far, role="validation",
                                       source_of_computed="oracle")
    model = ref.compare_published(case, far, role="model comparison",
                                  source_of_computed="RocketForge")
    assert [row.verdict for row in validation] == ["FAIL", "FAIL"]
    assert [row.verdict for row in model] == ["MODEL DIFFERENCE",
                                              "MODEL DIFFERENCE"]
    assert ref.overall_verdict(validation) == "FAIL"
    assert ref.overall_verdict(model) == "MODEL DIFFERENCE"


def test_a_missing_computed_value_fails_rather_than_disappearing(payload):
    case = ref.performance_reference_case(payload)
    rows = ref.compare_published(case, {}, role="validation",
                                 source_of_computed="nothing")
    assert len(rows) == len(case.published)
    assert all(row.computed is None and not row.passed for row in rows)
    assert ref.overall_verdict(rows) == "FAIL"


def test_the_source_rows_carry_the_conditions_not_just_a_verdict(payload):
    rows = {row["label"]: row["value"]
            for row in ref.source_rows(ref.performance_reference_case(payload))}
    assert rows["Propellants"] == "O2(L) / H2(L)"
    assert rows["Chamber Pressure"] == "1000.0 psia"
    assert "equilibrium" in rows["Chemistry"]


# ===========================================================================
# live: the oracle against the source, then RocketForge against the source
# ===========================================================================


@requires_cea
def test_the_cea_oracle_reproduces_the_published_case(payload):
    """A genuine external validation: two implementations, one published case."""
    from rocketforge.core.constants import STANDARD_GRAVITY
    from rocketforge.physics.thermochemistry import ExpansionMode
    from rocketforge.providers.cea import CEAThermochemistryProvider
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import HO_PRODUCT_SPECIES

    case = ref.performance_reference_case(payload)
    spec = case.case
    provider = CEAThermochemistryProvider()
    oracle = run_rocket_oracle(
        provider._cea(), fuel_names=("H2(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(spec["fuel_temperature_K"],
                               spec["oxidiser_temperature_K"]),
        of_ratio=spec["oxidiser_fuel_ratio"],
        chamber_pressure=spec["chamber_pressure_Pa"],
        area_ratio=spec["area_ratio"], product_species=HO_PRODUCT_SPECIES,
        expansion_mode=ExpansionMode.EQUILIBRIUM)

    rows = ref.compare_published(
        case,
        {"characteristic_velocity": oracle.c_star,
         "specific_impulse": oracle.specific_impulse / STANDARD_GRAVITY},
        role="validation", source_of_computed="NASA CEA 3.3.4")
    assert ref.overall_verdict(rows) == "PASS"
    for row in rows:
        assert row.relative_difference <= row.tolerance, row


@requires_cea
def test_a_mutated_published_value_changes_the_verdict(payload):
    """The mutation proof, with the fixture asserted changed first."""
    from rocketforge.core.constants import STANDARD_GRAVITY
    from rocketforge.physics.thermochemistry import ExpansionMode
    from rocketforge.providers.cea import CEAThermochemistryProvider
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import HO_PRODUCT_SPECIES

    case = ref.performance_reference_case(payload)
    spec = case.case
    provider = CEAThermochemistryProvider()
    oracle = run_rocket_oracle(
        provider._cea(), fuel_names=("H2(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(spec["fuel_temperature_K"],
                               spec["oxidiser_temperature_K"]),
        of_ratio=spec["oxidiser_fuel_ratio"],
        chamber_pressure=spec["chamber_pressure_Pa"],
        area_ratio=spec["area_ratio"], product_species=HO_PRODUCT_SPECIES,
        expansion_mode=ExpansionMode.EQUILIBRIUM)
    computed = {"characteristic_velocity": oracle.c_star,
                "specific_impulse": oracle.specific_impulse / STANDARD_GRAVITY}
    assert ref.overall_verdict(ref.compare_published(
        case, computed, role="validation", source_of_computed="x")) == "PASS"

    for key in ("characteristic_velocity", "specific_impulse"):
        mutated = copy.deepcopy(payload)
        entry = next(e for e in mutated["published"] if e["key"] == key)
        original = entry["value"]
        entry["value"] = original * 1.01
        assert entry["value"] != original, "the fixture did not change"

        mutated_case = ref.performance_reference_case(mutated)
        changed = next(q for q in mutated_case.published if q.key == key)
        assert changed.value != next(
            q for q in case.published if q.key == key).value

        rows = ref.compare_published(mutated_case, computed, role="validation",
                                     source_of_computed="x")
        assert ref.overall_verdict(rows) == "FAIL"
        failed = next(row for row in rows if row.key == key)
        assert failed.relative_difference > failed.tolerance


@requires_cea
def test_rocketforge_is_compared_as_a_model_difference_not_an_error(payload):
    """RocketForge is a different model, and the comparison says so.

    The equilibrium basis lands c* inside the source's own rounding box, which
    is what a constant-gamma_s reduction is *designed* to do near the throat.
    That is still recorded as a model comparison: close agreement between
    different models is not validation.
    """
    from rocketforge.engineering.chamber import ChamberGammaBasis, reduce_chamber_gas
    from rocketforge.engineering.nozzle import (
        IdealPerformanceRequest,
        PerformanceScale,
        PerformanceScaleMode,
        solve_ideal_performance,
    )
    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest,
        GammaStrategy,
        MixtureRatio,
        Phase,
        PropellantStream,
    )
    from rocketforge.providers.cea import (
        LIQUID_HYDROGEN,
        LOX,
        CEAThermochemistryProvider,
    )

    case = ref.performance_reference_case(payload)
    spec = case.case
    provider = CEAThermochemistryProvider()
    chamber = provider.solve_chamber(ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_HYDROGEN, spec["fuel_temperature_K"],
                              phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, spec["oxidiser_temperature_K"],
                                  phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(spec["oxidiser_fuel_ratio"]),
        chamber_pressure=spec["chamber_pressure_Pa"])).unwrap()

    reduced = reduce_chamber_gas(chamber, GammaStrategy.CHAMBER,
                                 ChamberGammaBasis.EQUILIBRIUM).value
    scale = PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01)
    vacuum = solve_ideal_performance(IdealPerformanceRequest(
        reduced=reduced, chamber_pressure=spec["chamber_pressure_Pa"],
        area_ratio=spec["area_ratio"], ambient_pressure=0.0,
        scale=scale)).unwrap()
    optimum = solve_ideal_performance(IdealPerformanceRequest(
        reduced=reduced, chamber_pressure=spec["chamber_pressure_Pa"],
        area_ratio=spec["area_ratio"],
        ambient_pressure=vacuum.exit.pressure, scale=scale)).unwrap()

    rows = ref.compare_published(
        case,
        {"characteristic_velocity": optimum.characteristic_velocity,
         "specific_impulse": optimum.specific_impulse},
        role="model comparison",
        source_of_computed="RocketForge ideal, equilibrium basis")

    assert all(row.role == "model comparison" for row in rows)
    assert all(row.verdict in ("WITHIN BOX", "MODEL DIFFERENCE") for row in rows)
    assert "PASS" not in [row.verdict for row in rows], (
        "a model comparison must never report PASS: that word belongs to a "
        "like-for-like validation")
    # And it is genuinely in the right neighbourhood, which is the useful part.
    for row in rows:
        assert row.relative_difference < 0.05
