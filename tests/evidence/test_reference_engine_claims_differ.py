"""A vacuum and a sea-level thrust or Isp are two statements, not a disagreement.

The rule is narrow. It applies only to thrust and specific impulse, and only when both environments are recorded. Any
other or unknown environment is still compared with every claim. It decides no regression: it only stops one false reason.
"""

from __future__ import annotations

import pathlib

import pytest

from rocketforge.evidence.engines import corpus_from_dict, corpus_from_json, corpus_to_dict
from rocketforge.evidence.engines.capabilities import Capability, CapabilityStatus, evaluate_capability

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"

RS68, F1 = "CFG-RS68-1999-BASELINE", "CFG-F1"
RS68_SL = "AS-DB05-US-RS-68-002"
DIFFER = "thrust: the claims differ"


@pytest.fixture(scope="module")
def corpus():
    return corpus_from_json(SHIPPED.read_text(encoding="utf-8"))


def regression(corpus, cfg):
    return evaluate_capability(corpus, cfg, Capability.REGRESSION_CANDIDATE)


def with_rs68_sea_level_environment(corpus, environment):
    payload = corpus_to_dict(corpus)
    record = next(a for a in payload["assertions"] if a["assertion_id"] == RS68_SL)
    assert record["conditions"]["environment"] == "SEA_LEVEL"
    record["conditions"]["environment"] = environment
    return corpus_from_dict(payload)


def test_vacuum_and_sea_level_thrust_are_not_a_disagreement(corpus):
    assert not [g for g in regression(corpus, RS68).gaps if "claims differ" in g]
    performance = evaluate_capability(corpus, RS68, Capability.PERFORMANCE_REFERENCE)
    assert not [c for c in performance.caveats if "claims differ" in c]


def test_vacuum_and_sea_level_isp_are_not_a_disagreement(corpus):
    assert not [g for g in regression(corpus, F1).gaps if "claims differ" in g]


def test_the_rule_makes_no_new_candidate(corpus):
    candidates = {c.configuration_id for c in corpus.configurations
                  if regression(corpus, c.configuration_id).status is CapabilityStatus.SUPPORTED}
    assert candidates == {"CFG-J2-230K", "CFG-J2S"}
    assert regression(corpus, RS68).status is CapabilityStatus.NOT_SUPPORTED
    assert regression(corpus, F1).status is CapabilityStatus.NOT_SUPPORTED


@pytest.mark.parametrize("environment", ["VACUUM", "ALTITUDE", "UNKNOWN"])
def test_two_thrusts_differ_unless_both_environments_are_recorded(corpus, environment):
    changed = with_rs68_sea_level_environment(corpus, environment)
    assert any(g.startswith(DIFFER) for g in regression(changed, RS68).gaps)


def test_chamber_pressure_claims_still_differ(corpus):
    assert any(g.startswith("chamber_pressure: the claims differ") for g in regression(corpus, "CFG-RS25-BLOCK-II").gaps)


def test_no_shipped_value_contradicts_its_field_about_the_environment(corpus):
    """The rule reads the recorded environment, so the field and the record must not say opposite things."""
    opposite = {"_vac": "SEA_LEVEL", "_sl": "VACUUM"}
    for a in corpus.assertions:
        for suffix, wrong in opposite.items():
            if a.field_path in (f"performance.thrust{suffix}", f"performance.specific_impulse{suffix}"):
                assert getattr(a.conditions.environment, "value", None) != wrong, a.assertion_id
