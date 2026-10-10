"""The conflict-number matcher (owner decision 2026-10-10): a unit's exponent is not a claim value.

The matcher links a DB-0.5 conflict claim to the assertions that print the same numbers. It read the
"2" of "kgs/cm2" as a number, which tied Rockwell's RD-170 layout sentence ("... 2 preburners ...")
to the chamber-pressure conflict. A unit exponent must not count; real values must still count.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import promote_db2a  # noqa: E402


@pytest.mark.parametrize("text,expected", [
    ("250 kgs/cm2", {250.0}),
    ("250 kg/cm2", {250.0}),
    ("250 kgf/cm²", {250.0}),
    ("3,556 lb/in2", {3556.0}),
    ("9.81 m/s^2", {9.81}),
    ("12 ft**2", {12.0}),
    ("Pression dans la chambre de combustion - 250 kgs/cm2", {250.0}),
])
def test_a_unit_exponent_is_not_a_claim_value(text, expected):
    assert promote_db2a._whole_numbers(text) == expected


@pytest.mark.parametrize("text,expected", [
    # values glued to a slash label are values (final review finding)
    ("O/F2.27", {2.27}),
    ("MR O/F2.27", {2.27}),
    ("O/F6", {6.0}),
    ("T/W73", {73.0}),
    ("thrust/weight73", {73.0}),
    ("Isp/s300", {300.0}),
    ("kg/s1727", {1727.0}),
    ("lb/sec1,727", {1727.0}),
    ("ox/fuel2.6 ratio", {2.6}),
    ("RL10A-4/A42", {4.0, 10.0, 42.0}),
    ("250 kgs/cm2, 3,556 psi", {250.0, 3556.0}),
    ("2.27 O/F", {2.27}),
    ("Engine mixture ratio O/F 2.27", {2.27}),
    ("20 starts", {20.0}),
    ("2250 seconds", {2250.0}),
    ("Duration 2,250 seconds", {2250.0}),
    ("21 500 pounds vacuum, 102 psia, 309 s", {21500.0, 102.0, 309.0}),
    ("1 turbopump assembly driven by 2 preburners which feed 4 thrust chamber assemblies", {2.0, 4.0}),
])
def test_real_values_are_still_found(text, expected):
    assert promote_db2a._whole_numbers(text) == expected


@pytest.mark.parametrize("text,expected", [("250 kgs/cm 2", {250.0, 2.0}), ("250 per cm2", {250.0, 2.0})])
def test_a_spaced_or_slashless_exponent_is_still_read_conservatively(text, expected):
    """Documented: these still count the exponent, which can only link more claims and withhold more."""
    assert promote_db2a._whole_numbers(text) == expected


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


def test_the_rd170_layout_sentence_is_no_longer_a_chamber_pressure_claim(research):
    claims = promote_db2a.claim_matches(research.conflicts["CF-DB05-RD170-PC"], research)
    matched = set().union(*claims)
    assert "AS-DB05-SU-RD-170-006" not in matched
    assert "AS-DB05-SU-RD-170-005" in matched  # the placard's 250 kgs/cm2 is still its claim


def test_real_claims_still_match_their_assertions(research):
    matched = set().union(*promote_db2a.claim_matches(research.conflicts["CF-DB05-RL10B2-PC-ISP"], research))
    assert {"AS-DB05-US-RL10B-2-002", "AS-DB05-US-RL10B-2-003", "AS-DB05-US-RL10B-2-004",
            "AS-DB05-US-RL10B-2-005"} <= matched
    matched = set().union(*promote_db2a.claim_matches(research.conflicts["CF-DB05-RD170-MR"], research))
    assert {"AS-DB05-SU-RD-170-008", "AS-DB05-SU-RD-170-009"} <= matched
