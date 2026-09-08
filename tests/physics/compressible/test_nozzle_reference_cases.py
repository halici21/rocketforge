"""End-to-end nozzle cases built entirely from published table rows.

The supplied Anderson volume has appendices for isentropic flow, normal shocks
and the Prandtl-Meyer function, and **no nozzle appendix**. None is invented.
What is done instead is stated plainly in the dataset and repeated here: each
case is *constructed* from printed rows -- the geometry and the back pressure
are built out of published values, and the expected answers are themselves
published values from other printed rows. RocketForge is then asked to
rediscover stations it was never given.

For the internal-shock case that means: given only an area ratio and a back
pressure assembled from four printed numbers, the solver must place the shock
at the published M = 2.00 area ratio, reproduce the published jump, and land
the exit on the published M = 0.40 row.

The limitation is equally plain, and ``170`` asks for it to be stated: these
are published *station* values composed by RocketForge, not a transcription of
a published worked nozzle example. The composition is ours; every number in it
is the book's.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from rocketforge.application.analysis.reference_comparison import reference_root
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.types import NozzleRegime

DATASET = "nozzle_anderson6_constructed.json"


def load() -> dict:
    path = reference_root() / DATASET
    return json.loads(path.read_text(encoding="utf-8"))


DATA = load()
CASES = DATA["cases"]


def gas() -> PerfectGas:
    return PerfectGas(gamma=DATA["gamma"], gas_constant=287.05)


def case_ids() -> list[str]:
    return [case["regime"] for case in CASES]


# ---------------------------------------------------------------------------
# the dataset itself
# ---------------------------------------------------------------------------


def test_the_dataset_ships_inside_the_package():
    assert (reference_root() / DATASET).is_file()


def test_the_dataset_names_its_source_and_its_limitation():
    assert DATA["source"]["title"] == "Fundamentals of Aerodynamics"
    assert "1079" in DATA["source"]["appendices"]
    assert "no nozzle appendix" in DATA["construction"]
    assert "not transcriptions" in DATA["limitation"]
    assert "Derived, not chosen" in DATA["tolerance_rule"]
    assert "measure-zero" in DATA["boundary_note"]


def test_every_regime_that_can_be_reached_from_a_published_row_is_covered():
    covered = {case["regime"] for case in CASES}
    assert covered == {r.value for r in NozzleRegime}


def test_every_expected_value_names_the_printed_row_it_came_from():
    for case in CASES:
        for name, expectation in case["expected"].items():
            assert expectation["from"], f"{case['name']}/{name} has no provenance"
            assert "atol" in expectation


# ---------------------------------------------------------------------------
# the cases
# ---------------------------------------------------------------------------


INTERVAL_CASES = [c for c in CASES if c.get("check") == "regime"]
BOUNDARY_CASES = [c for c in CASES if c.get("check") == "threshold"]


@pytest.mark.parametrize("case", INTERVAL_CASES,
                         ids=[c["regime"] for c in INTERVAL_CASES])
def test_a_published_operating_point_is_classified_as_published(case):
    result = nozzle.classify(case["inputs"]["area_ratio_exit"]["value"],
                             case["inputs"]["pressure_ratio_back"]["value"],
                             gas()).unwrap()
    assert result.regime.value == case["regime"]


@pytest.mark.parametrize("case", BOUNDARY_CASES,
                         ids=[c["regime"] for c in BOUNDARY_CASES])
def test_a_published_threshold_matches_the_computed_threshold(case):
    """The measure-zero regimes are checked on the threshold, not on a label.

    A back pressure assembled from four-figure published values misses an
    exact threshold by the rounding of those values -- 1/1.117 sits 3.4e-4
    above the first critical because 1.117 is itself a rounding of 1.116552.
    Widening ``pressure_tol`` to absorb that would collapse genuinely
    different operating points into boundary regimes, so the published number
    is compared against the computed threshold instead.
    """
    critical = nozzle.critical_pressure_ratios(
        case["inputs"]["area_ratio_exit"]["value"], gas()).unwrap()
    published = case["inputs"]["pressure_ratio_back"]["value"]
    computed = getattr(critical, case["threshold"])
    assert computed == pytest.approx(published, rel=1e-3)


@pytest.mark.parametrize("case", BOUNDARY_CASES,
                         ids=[c["regime"] for c in BOUNDARY_CASES])
def test_the_computed_threshold_reaches_its_own_boundary_regime(case):
    """What the interface's preset buttons do, and it must land exactly."""
    area_ratio = case["inputs"]["area_ratio_exit"]["value"]
    critical = nozzle.critical_pressure_ratios(area_ratio, gas()).unwrap()
    threshold = getattr(critical, case["threshold"])
    result = nozzle.classify(area_ratio, threshold, gas()).unwrap()
    assert result.regime.value == case["regime"]


@pytest.mark.parametrize("case", CASES, ids=case_ids())
def test_the_published_values_are_reproduced(case):
    air = gas()
    area_ratio = case["inputs"]["area_ratio_exit"]["value"]
    back = case["inputs"]["pressure_ratio_back"]["value"]
    if case.get("check") == "threshold":
        # Solve at the threshold itself, so the case describes the state the
        # published numbers describe rather than one a rounding away from it.
        critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
        back = getattr(critical, case["threshold"])
    result = nozzle.classify(area_ratio, back, air).unwrap()

    computed = {
        "mach_exit": result.mach_exit,
        "pressure_ratio_exit": result.pressure_ratio_exit,
        "mach_exit_supersonic": result.critical.mach_exit_supersonic,
        "mach_throat": None if result.regime is NozzleRegime.UNCHOKED_SUBSONIC else 1.0,
    }
    if result.shock is not None:
        computed.update({
            "shock_area_ratio": result.shock.area_ratio_shock,
            "mach_upstream": result.shock.mach_upstream,
            "mach_downstream": result.shock.mach_downstream,
            "shock_pressure_ratio": result.shock.pressure_ratio,
            "shock_mach_upstream": result.shock.mach_upstream,
            "shock_mach_downstream": result.shock.mach_downstream,
        })

    for name, expectation in case["expected"].items():
        got = computed[name]
        assert got is not None, f"{case['name']} has no value for {name}"
        assert got == pytest.approx(expectation["published"],
                                    abs=expectation["atol"]), (
            f"{case['name']}: {name} = {got!r}, published "
            f"{expectation['published']!r} ({expectation['from']})")


def test_the_internal_shock_case_rediscovers_four_published_numbers():
    """The strongest single check in the phase, spelled out.

    The solver is handed an area ratio and a back pressure and nothing else.
    It must place the shock where Appendix A puts M = 2.00, reproduce Appendix
    B's M = 2.00 row, and land the exit on Appendix A's M = 0.40 row.
    """
    case = next(c for c in CASES if c["regime"] == "internal_normal_shock")
    result = nozzle.classify(case["inputs"]["area_ratio_exit"]["value"],
                             case["inputs"]["pressure_ratio_back"]["value"],
                             gas()).unwrap()
    assert result.shock.area_ratio_shock == pytest.approx(1.687, abs=2e-3)
    assert result.shock.mach_upstream == pytest.approx(2.00, abs=2e-3)
    assert result.shock.mach_downstream == pytest.approx(0.5774, abs=2e-4)
    assert result.mach_exit == pytest.approx(0.40, abs=4e-4)


def test_no_reference_value_is_interpolated():
    """``145``: published rows are exact checkpoints, never a lookup table."""
    for case in CASES:
        for expectation in case["expected"].values():
            provenance = expectation["from"].lower()
            assert "interpolat" not in provenance
            assert "between" not in provenance
    # The dataset says so of itself, in the sentence that describes it.
    assert "Nothing is interpolated" in DATA["construction"]
