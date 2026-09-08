"""Verification against printed reference tables.

``docs/engineering/05_verification_and_validation_plan.md`` section 7 makes
this blocking: a value RocketForge generated is not a reference, and no module
is accepted while any of its reference cases is still unconfirmed. The
expectations here were read from the printed tables of NACA Report 1135 and are
recorded with their provenance in ``tests/reference_data/``.

Tolerances come from the source, not from convenience: each is half a unit in
the last digit the table prints. Nothing is asserted more tightly than the
authority states it.
"""

from __future__ import annotations

import json
import pathlib
from fractions import Fraction

import pytest

from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import isentropic as iso

REFERENCE_DIR = pathlib.Path(__file__).resolve().parents[2] / "reference_data"

RELATIONS = {
    "temperature_ratio": iso.temperature_ratio,
    "pressure_ratio": iso.pressure_ratio,
    "density_ratio": iso.density_ratio,
    "area_ratio": iso.area_ratio,
}


def load(name: str) -> dict:
    with (REFERENCE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


ISENTROPIC = load("isentropic_naca1135.json")
AREA_MACH = load("area_mach_naca1135.json")


def isentropic_cases():
    for case in ISENTROPIC["cases"]:
        for quantity, expected in case["values"].items():
            yield pytest.param(
                case["mach"], quantity, expected["printed"], expected["atol"], case["confirmed"],
                id=f"M={case['mach']}-{quantity}",
            )


# ---------------------------------------------------------------------------
# the data itself must be confirmed, not merely present
# ---------------------------------------------------------------------------


def test_reference_files_name_their_source():
    for data in (ISENTROPIC, AREA_MACH):
        assert data["source"]
        assert data["source_url"]
        assert data["accessed"]
        assert data["gamma"] == 1.4


def test_no_isentropic_case_is_left_unconfirmed():
    """The gate: an unconfirmed expectation blocks acceptance of the module."""
    unconfirmed = [
        case["mach"] for case in ISENTROPIC["cases"]
        if not case.get("confirmed") or case["confirmed"] == "pending"
    ]
    assert not unconfirmed, f"reference cases still pending confirmation: {unconfirmed}"


def test_no_area_mach_case_is_left_unconfirmed():
    pending = []
    for pair in AREA_MACH["branch_pairs"]:
        for side in ("subsonic", "supersonic"):
            entry = pair[side]
            if not entry.get("confirmed") or entry["confirmed"] == "pending":
                pending.append((pair["area_ratio"], side))
    assert not pending, f"branch expectations still pending confirmation: {pending}"


def test_every_case_carries_a_tolerance_traceable_to_the_printed_precision():
    for case in ISENTROPIC["cases"]:
        for quantity, expected in case["values"].items():
            printed = expected["printed"]
            atol = expected["atol"]
            # The number of decimals the source prints is recorded in the data,
            # not inferred: JSON parses 0.8430 as 0.843 and drops the trailing
            # zero that states how precisely the table gives the value.
            decimals = expected["printed_decimals"]
            assert atol == pytest.approx(0.5 * 10 ** (-decimals), rel=1e-9), (
                f"M={case['mach']} {quantity}: tolerance {atol} is not half a unit "
                f"in the last of {decimals} printed decimals of {printed}"
            )


# ---------------------------------------------------------------------------
# isentropic ratios against NACA 1135
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mach,quantity,printed,atol,confirmed", list(isentropic_cases()))
def test_matches_naca_1135(mach, quantity, printed, atol, confirmed):
    air = PerfectGas(gamma=ISENTROPIC["gamma"])
    computed = float(RELATIONS[quantity](mach, air))
    assert computed == pytest.approx(printed, abs=atol), (
        f"\n  quantity : {quantity}"
        f"\n  Mach     : {mach}"
        f"\n  computed : {computed!r}"
        f"\n  printed  : {printed!r}"
        f"\n  tolerance: {atol!r} (half a unit in the last printed digit)"
        f"\n  source   : {confirmed}"
    )


@pytest.mark.parametrize("case", ISENTROPIC["exact_rational_cases"],
                         ids=[f"{c['quantity']}@M={c['mach']}" for c in ISENTROPIC["exact_rational_cases"]])
def test_exact_rational_values(case):
    """Cases that are exactly rational at gamma = 1.4, checkable by hand.

    A third kind of confirmation, independent of both the table and the
    implementation: T/T0 at M = 2 is exactly 5/9 and A/A* is exactly 27/16, and
    those can be verified with a pencil.
    """
    air = PerfectGas(gamma=1.4)
    expected = float(Fraction(case["exact"]))
    computed = float(RELATIONS[case["quantity"]](case["mach"], air))
    assert computed == pytest.approx(expected, rel=case["rtol"])


# ---------------------------------------------------------------------------
# area-Mach, both branches, against NACA 1135
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spot", AREA_MACH["forward_spot_checks"],
                         ids=[f"M={s['mach']}" for s in AREA_MACH["forward_spot_checks"]])
def test_area_ratio_forward_spot_checks(spot):
    air = PerfectGas(gamma=1.4)
    computed = float(iso.area_ratio(spot["mach"], air))
    assert computed == pytest.approx(spot["area_ratio"], abs=spot["atol"]), (
        f"M={spot['mach']}: computed {computed!r} against printed "
        f"{spot['area_ratio']!r} from {spot['confirmed']}"
    )


def test_sonic_area_ratio_inverts_to_mach_one():
    """NACA prints A/A* = 1.00000 at M = 1.00 in both tables."""
    air = PerfectGas(gamma=1.4)
    sonic = AREA_MACH["sonic"]
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        solution = iso.mach_from_area_ratio(sonic["area_ratio"], air, branch)
        assert solution.value == sonic["expected_mach"]


@pytest.mark.parametrize("pair", AREA_MACH["branch_pairs"],
                         ids=[f"AR={p['area_ratio']}" for p in AREA_MACH["branch_pairs"]])
def test_branch_pair_against_the_printed_tables(pair):
    """Both roots of one area ratio, each anchored to printed data.

    One side is checked against an exact tabulated Mach number; the other
    against the interval given by two adjacent printed rows, using the fact
    that the tabulated column is monotone. Neither expectation comes from
    RocketForge.
    """
    air = PerfectGas(gamma=1.4)
    both = iso.mach_from_area_ratio_both(pair["area_ratio"], air).unwrap()
    roots = {"subsonic": both.subsonic, "supersonic": both.supersonic}

    for side, entry in (("subsonic", pair["subsonic"]), ("supersonic", pair["supersonic"])):
        value = roots[side]
        if "expected" in entry:
            assert value == pytest.approx(entry["expected"], abs=entry["atol"]), (
                f"{side} root of A/A* = {pair['area_ratio']}: got {value!r}, "
                f"expected {entry['expected']!r} from {entry['confirmed']}"
            )
        else:
            low, high = entry["bracket"]
            assert low < value < high, (
                f"{side} root of A/A* = {pair['area_ratio']}: got {value!r}, which is "
                f"outside the interval [{low}, {high}] implied by {entry['bracket_source']}"
            )


def test_branch_pair_roots_reproduce_the_area_ratio():
    """Whatever the tables say, both roots must satisfy the forward relation."""
    air = PerfectGas(gamma=1.4)
    for pair in AREA_MACH["branch_pairs"]:
        both = iso.mach_from_area_ratio_both(pair["area_ratio"], air).unwrap()
        for mach in (both.subsonic, both.supersonic):
            assert float(iso.area_ratio(mach, air)) == pytest.approx(
                pair["area_ratio"], rel=1e-8
            )
