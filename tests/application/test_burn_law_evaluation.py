"""EV-5: evaluating a published burn law inside its domain only, and showing it.

The law is synthetic and test-only: three regimes, one with a negative exponent,
chosen so the rate is not monotonic across regimes. No published coefficient
appears here.
"""
from __future__ import annotations

import math
import pathlib
import sys

import pytest

from rocketforge.application.analysis import burn_law_evaluation as burn
from rocketforge.application.analysis import evidence_cea_bridge as bridge
from rocketforge.application.analysis import propulsion_evidence_service as service
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.evidence import record_to_json, sources_to_json

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "evidence"))
from test_evidence_burn_law import SOURCES, law, record, regime  # noqa: E402

LAW = law()                                  # [0.1, 1.0) [1.0, 2.0) [2.0, 4.0] MPa


def rate(regime_index, p):
    r = LAW.regimes[regime_index]
    return r.a.value * p ** r.n.value


@pytest.mark.parametrize("p, index", [(0.1, 0), (0.5, 0), (1.0, 1), (1.5, 1), (2.0, 2), (3.9, 2),
                                      (4.0, 2)])
def test_a_pressure_is_evaluated_with_its_own_regime_only(p, index):
    result = burn.evaluate(LAW, p)
    assert result.regime_index == index
    assert result.rate == rate(index, p)
    assert (result.rate_unit, result.pressure_unit, result.law_id) == ("mm/s", "MPa", "L-TEST")


def test_a_shared_endpoint_belongs_to_the_upper_regime_and_the_top_to_the_last():
    assert burn.owning_regime(LAW, 1.0) == 1 and burn.owning_regime(LAW, 2.0) == 2
    assert burn.owning_regime(LAW, 4.0) == 2
    # the published endpoints themselves are untouched
    assert [(r.pressure_min.value, r.pressure_max.value) for r in LAW.regimes] == [
        (0.1, 1.0), (1.0, 2.0), (2.0, 4.0)]


@pytest.mark.parametrize("p", [0.0, 0.0999, 4.0001, 50.0, -1.0, math.inf, math.nan])
def test_outside_the_published_domain_is_refused_not_extended(p):
    with pytest.raises(burn.BurnLawDomainError):
        burn.evaluate(LAW, p)


def test_a_gap_is_refused_and_its_edges_belong_to_their_own_regimes():
    gapped = law(regimes=(regime(0.1, 1.0, 5.0, 0.4), regime(2.0, 3.0, 4.0, 0.5)))
    assert burn.owning_regime(gapped, 1.0) == 0          # unshared p_max: its own
    assert burn.owning_regime(gapped, 2.0) == 1
    with pytest.raises(burn.BurnLawDomainError, match="outside the published domain"):
        burn.evaluate(gapped, 1.5)


def test_a_negative_exponent_is_used_as_printed_and_the_rate_need_not_rise():
    low, high = burn.evaluate(LAW, 1.0), burn.evaluate(LAW, 1.9)
    assert LAW.regimes[1].n.value < 0 and high.rate < low.rate
    assert burn.evaluate(LAW, 0.99).rate != low.rate   # a discontinuity stays one


def test_zero_pressure_with_a_non_positive_exponent_is_refused():
    at_zero = law(regimes=(regime(0.0, 1.0, 5.0, -0.2),))
    with pytest.raises(burn.BurnLawDomainError, match="no finite rate"):
        burn.evaluate(at_zero, 0.0)
    assert burn.evaluate(law(regimes=(regime(0.0, 1.0, 5.0, 0.3),)), 0.0).rate == 0.0


# ---------------------------------------------------------------- presentation


def test_the_workspace_shows_a_law_generically_as_stored(tmp_path):
    folder = tmp_path / "evidence"
    (folder / "records").mkdir(parents=True)
    (folder / "sources.json").write_text(sources_to_json(SOURCES.values()), encoding="utf-8")
    (folder / "records" / "DS-TEST-LAW.json").write_text(record_to_json(record()), encoding="utf-8")
    corpus = service.load_corpus(folder)
    rec = corpus.record("DS-TEST-LAW")
    assert service.library_rows(corpus.records)[0]["section"] == "Burn Laws"
    keys, rows = service.table_rows(rec)
    assert len(rows) == 3 * 4 + 2
    assert rows[1][:3] == ("Regime 1 · p max", service.stored_text(1.0), "MPa")
    assert rows[7][:3] == ("Regime 2 · n", service.stored_text(-0.25), "1")
    assert rows[-2] == ("Burn law · test temperature", "Missing", "", "NOT_REPORTED", "", "")
    missing = service.missing_rows(rec)
    assert [m["key"] for m in missing] == ["burn_law.temperature", "burn_law.uncertainty"]
    assert "ambient" in missing[0]["note"]
    readout = service.datum_readout(rec, corpus.sources, "burn_law.regimes[1].n")
    values = [row["value"] for section in readout["sections"] for row in section["rows"]]
    assert "Table 9 (test)" in values and "REPORTED" in values


def test_a_burn_law_is_not_a_cea_target_and_asks_no_provider(monkeypatch):
    def refuse(*_a, **_k):
        raise AssertionError("no provider may be asked about a burn law")
    for name in ("probe_solid_library_species", "solve_solid_chamber_state",
                 "solve_solid_equilibrium_cstar", "availability"):
        monkeypatch.setattr(gateway, name, refuse)
    result = bridge.assess(record(), SOURCES)
    assert result.state is bridge.CompatibilityState.NOT_A_CEA_TARGET and result.probe is None
