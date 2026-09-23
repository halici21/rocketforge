"""Level C -- the Cantera cross-provider oracle.

Reads the comparison recorded by ``experiments/phase_5c/cantera_oracle.py``,
which runs Cantera in a **separate** environment, and is tracked in
``tests/acceptance/records/phase_5c/`` so it is checked in every checkout.
Cantera is deliberately not installed in ``.venv-cea``: the official
executable is built from that environment, and an oracle must not be bundled
into the product.

The interpretation matters as much as the numbers. Two providers with
independent thermodynamic databases are expected to agree closely on bulk
properties and to differ more on trace radicals. That signature is evidence
that both are working, not evidence that either is broken -- and neither is
treated as ground truth (Phase 5C brief sections 96-98).
"""

from __future__ import annotations

import json
import pathlib

import pytest

ARTIFACTS = (pathlib.Path(__file__).resolve().parents[3]
             / "tests" / "acceptance" / "records" / "phase_5c")
COMPARISON = ARTIFACTS / "cantera_oracle_comparison.json"


def load() -> dict:
    if not COMPARISON.exists():
        pytest.fail(
            f"the recorded Cantera comparison {COMPARISON.name} is missing; it is "
            "tracked, and regenerated with experiments/phase_5c/cantera_oracle.py "
            "in a Cantera environment")
    return json.loads(COMPARISON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def comparison() -> dict:
    return load()


def test_the_comparison_is_classified_as_tier_two(comparison):
    """Honesty about what this evidence is worth.

    Independent databases, so exact agreement is neither expected nor required.
    Recording the tier prevents the comparison being read later as a
    like-for-like validation.
    """
    assert comparison["parity_tier"] == 2
    assert "INDEPENDENT" in comparison["parity_tier_note"]
    assert "ground truth" in comparison["parity_tier_note"]


def test_the_two_providers_are_genuinely_different(comparison):
    assert comparison["cea_version"].startswith("3.")
    assert comparison["cantera_version"].startswith("3.")
    assert comparison["cantera_mechanism"] == "nasa_gas.yaml"
    assert comparison["cea_thermo_sha256"]


def test_bulk_properties_agree_closely(comparison):
    """Chamber temperature, molar mass and gamma to within 1e-3.

    Measured 9.2e-04 on chamber temperature -- the same order Phase 5B-0 found
    for the direct-library comparison, which is what says the RocketForge
    pipeline has not introduced anything of its own.
    """
    assert comparison["max_bulk_relative_difference"] < 1.0e-3
    bulk = comparison["bulk_properties"]
    assert bulk["Tc_K"]["relative_difference"] < 1.0e-3
    assert bulk["M_kg_per_mol"]["relative_difference"] < 1.0e-3
    assert bulk["gamma_s"]["relative_difference"] < 1.0e-3


def test_major_species_agree_and_radicals_diverge(comparison):
    """The expected signature of independent thermodynamic data.

    Stable majors -- H2O, CO, CO2 -- agree to better than a percent. Radicals
    such as OH, O and H2O2 differ by a few percent, because their equilibrium
    amounts are exponentially sensitive to formation enthalpies that the two
    databases transcribe independently.

    This is asserted rather than merely tolerated, because a run in which the
    radicals *also* matched to 1e-4 would suggest the two sides were not
    actually independent.
    """
    species = comparison["major_species"]
    for name in ("H2O", "CO", "CO2"):
        assert species[name]["relative_difference"] < 1.0e-2, name
    radicals = [species[n]["relative_difference"]
                for n in ("OH", "O", "O2") if n in species]
    assert radicals, "expected radical species in the comparison"
    assert max(radicals) > 1.0e-2, (
        "radical species agreeing as closely as the majors would suggest the "
        "two providers are not independent")
    assert max(radicals) < 1.0e-1, (
        "a radical difference above 10 % would be worth investigating rather "
        "than attributing to database differences")


def test_a_species_absent_from_one_provider_is_recorded_not_hidden(comparison):
    """``HCCO`` is in CEA's product set and not in Cantera's nasa_gas.yaml.

    Recorded explicitly, because silently dropping it would make the two
    species sets look identical when they are not.
    """
    assert "species_missing_from_cantera" in comparison
    assert isinstance(comparison["species_missing_from_cantera"], list)


def test_the_comparison_records_no_verdict_against_either_provider(comparison):
    """A cross-provider difference is data, not a judgement.

    The artifact carries measured differences and a parity tier, and no
    pass/fail field for either side. Asserting the *absence of a verdict field*
    is the meaningful check; searching the text for the word "defect" would
    only trip on the note explaining that a difference is not one.
    """
    verdict_fields = {"pass", "passed", "fail", "failed", "verdict",
                      "cea_correct", "cantera_correct", "winner", "reference"}
    assert not verdict_fields & set(comparison)
    for row in comparison["bulk_properties"].values():
        assert set(row) == {"cea", "cantera", "relative_difference"}
    assert "ground truth" in comparison["parity_tier_note"].lower()
