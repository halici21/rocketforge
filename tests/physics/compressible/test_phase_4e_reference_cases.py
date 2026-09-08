"""Fanno and Rayleigh against published values.

``docs/engineering/05_verification_and_validation_plan.md`` section 7 makes
this blocking: a number RocketForge produced is not a reference, and no module
is accepted while its reference cases are unconfirmed.

**Where the values come from, and why not NACA 1135.** The isentropic,
normal-shock and Prandtl-Meyer modules were confirmed against NACA Report 1135.
That report has no Fanno or Rayleigh tables. Rather than present a table as
though 1135 carried one, Phase 4E used NASA/TM-2006-214086 -- Melcher, *User
Guide for Compressible Flow Toolbox*, NASA Glenn, January 2006 -- which
tabulates both families and is equally in the public domain. Provenance for
every value is in ``tests/reference_data/SOURCES.md``.

Tolerances come from the source: half a unit in the last significant figure
each value is printed to, taken per value because Table 4.3 prints six figures
and the worked examples print four or five. Nothing is asserted more tightly
than the authority states it.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import fanno, rayleigh

# The shipped copy, not a test-only one: the Fanno and Rayleigh pages read
# these files at run time to show what backs their numbers, so the packaged
# application and this test must be looking at the same bytes. The resolver
# is shared for the same reason -- a second copy of the frozen-path logic is
# exactly what fails only inside the executable.
from rocketforge.application.analysis.reference_comparison import reference_root

REFERENCE_DIR = reference_root()


def load(name: str) -> dict:
    with (REFERENCE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


FANNO = load("fanno_nasa_tm_2006_214086.json")
RAYLEIGH = load("rayleigh_nasa_tm_2006_214086.json")

FANNO_RELATIONS = {
    "temperature_ratio": fanno.temperature_ratio,
    "pressure_ratio": fanno.pressure_ratio,
    "density_ratio": fanno.density_ratio,
    "stagnation_pressure_ratio": fanno.stagnation_pressure_ratio,
    "velocity_ratio": fanno.velocity_ratio,
    "friction_parameter": fanno.friction_parameter,
}

RAYLEIGH_RELATIONS = {
    "temperature_ratio": rayleigh.temperature_ratio,
    "pressure_ratio": rayleigh.pressure_ratio,
    "stagnation_temperature_ratio": rayleigh.stagnation_temperature_ratio,
    "stagnation_pressure_ratio": rayleigh.stagnation_pressure_ratio,
    # The report tabulates V/V*, which for a constant-area duct is the
    # reciprocal of rho/rho* by continuity. Comparing against it therefore
    # tests the density relation through an identity the source does not share.
    "velocity_ratio": lambda m, g: 1.0 / float(rayleigh.density_ratio(m, g)),
}


# ---------------------------------------------------------------------------
# the data must be confirmed, not merely present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("data", [FANNO, RAYLEIGH], ids=["fanno", "rayleigh"])
def test_reference_files_name_their_source(data):
    assert data["source"]
    assert data["source_url"].startswith("https://")
    assert data["accessed"]
    assert data["gamma"] == 1.4
    for case in data["cases"]:
        assert case["confirmed"], "a reference case without a confirmation is not a reference"
        assert case["page"]


def test_no_reference_case_is_still_pending():
    """The gate from ``05`` section 7, made mechanical.

    A case whose ``confirmed`` field is a placeholder is not confirmation, and
    Phase 4E is not complete while one exists.
    """
    for data in (FANNO, RAYLEIGH):
        for case in data["cases"]:
            text = case["confirmed"].lower()
            assert "pending" not in text
            assert "todo" not in text
            assert "unconfirmed" not in text


# ---------------------------------------------------------------------------
# Fanno
# ---------------------------------------------------------------------------


def fanno_cases():
    for case in FANNO["cases"]:
        for quantity, expected in case["values"].items():
            yield pytest.param(
                case["mach"], quantity, expected["printed"], expected["atol"],
                id=f"M={case['mach']}-{quantity}",
            )


@pytest.mark.parametrize("mach,quantity,printed,atol", list(fanno_cases()))
def test_fanno_matches_the_published_table(mach, quantity, printed, atol):
    air = PerfectGas(gamma=FANNO["gamma"], gas_constant=287.0528)
    computed = float(FANNO_RELATIONS[quantity](mach, air))
    assert computed == pytest.approx(printed, abs=atol)


def test_the_published_friction_column_is_the_fanning_group():
    """The factor-of-four check, against an authority rather than ourselves.

    NASA/TM-2006-214086 heads the column ``4fL*/D``. If RocketForge were
    computing the Darcy group the same duct would read four times smaller, and
    the published value would be missed by a factor of four rather than by a
    rounding. Asserting the mismatch as well as the match is what makes this a
    test of the convention and not just of the algebra.
    """
    air = PerfectGas(gamma=1.4, gas_constant=287.0528)
    published = 1.06906                       # Table 4.3, report p.38, M = 0.50
    computed = float(fanno.friction_parameter(0.5, air))
    assert computed == pytest.approx(published, abs=5e-6)
    assert computed / 4.0 != pytest.approx(published, abs=5e-6)


# ---------------------------------------------------------------------------
# Rayleigh
# ---------------------------------------------------------------------------


def rayleigh_cases():
    for case in RAYLEIGH["cases"]:
        for quantity, expected in case["values"].items():
            yield pytest.param(
                case["mach"], quantity, expected["printed"], expected["atol"],
                id=f"M={case['mach']}-{quantity}",
            )


@pytest.mark.parametrize("mach,quantity,printed,atol", list(rayleigh_cases()))
def test_rayleigh_matches_the_published_table(mach, quantity, printed, atol):
    air = PerfectGas(gamma=RAYLEIGH["gamma"], gas_constant=287.0528)
    computed = float(RAYLEIGH_RELATIONS[quantity](mach, air))
    assert computed == pytest.approx(printed, abs=atol)


def rayleigh_inverse_cases():
    for case in RAYLEIGH["inverse_cases"]:
        for branch in ("subsonic", "supersonic"):
            yield pytest.param(
                case["stagnation_temperature_ratio"], branch,
                case[branch]["printed"], case[branch]["atol"],
                id=f"T0ratio={case['stagnation_temperature_ratio']}-{branch}",
            )


@pytest.mark.parametrize("ratio,branch,printed,atol", list(rayleigh_inverse_cases()))
def test_the_rayleigh_inverse_matches_the_published_roots(ratio, branch, printed, atol):
    """Example 4.25, report p.55 -- both roots of the same T0/T0*.

    The most valuable case in the file: it confirms the branch-aware inverse
    against a published answer on both sides of sonic, which is the one inverse
    Phase 3 puts in v1 and the one the heat-addition problem is built on.
    """
    air = PerfectGas(gamma=RAYLEIGH["gamma"], gas_constant=287.0528)
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        ratio, air,
        FlowBranch.SUBSONIC if branch == "subsonic" else FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(printed, abs=atol)


def test_the_published_inverse_roots_really_are_two_different_ducts():
    """Both roots of one ratio, from the published pair, are far apart."""
    air = PerfectGas(gamma=1.4, gas_constant=287.0528)
    for case in RAYLEIGH["inverse_cases"]:
        sub = case["subsonic"]["printed"]
        sup = case["supersonic"]["printed"]
        assert sub < 1.0 < sup
        for mach in (sub, sup):
            assert float(rayleigh.stagnation_temperature_ratio(mach, air)) == \
                pytest.approx(case["stagnation_temperature_ratio"], abs=1e-4)
