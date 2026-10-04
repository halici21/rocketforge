"""LIQ-1: the Sutton Table 5-5 bipropellant presets.

A preset is a convenience over the real model: it sets the pair, the O/F and
the reference temperatures, and nothing else. These tests pin that it solves
nothing, names its source, refuses the two combinations the source does not
define, and -- with NASA CEA installed -- that every executable combination
completes the existing chamber and performance solves.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import thermochemistry_presets as presets
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")

#: Table 5-5, in the source's own order and words.
SUTTON_PAIRS = [
    ("Oxygen", "Methane"), ("Oxygen", "Hydrazine"), ("Oxygen", "Hydrogen"),
    ("Oxygen", "RP-1"), ("Oxygen", "UDMH"),
    ("Fluorine", "Hydrazine"), ("Fluorine", "Hydrogen"),
    ("Nitrogen tetroxide", "Hydrazine"),
    ("Nitrogen tetroxide", "50 % UDMH + 50 % hydrazine"),
    ("Nitrogen tetroxide", "RP-1"), ("Nitrogen tetroxide", "MMH"),
    ("Red fuming nitric acid", "RP-1"),
    ("Red fuming nitric acid", "50 % UDMH + 50 % hydrazine"),
    ("Hydrogen peroxide (90 %)", "RP-1"),
]


# ---------------------------------------------------------------------------
# the catalogue
# ---------------------------------------------------------------------------


def test_the_catalogue_is_exactly_table_5_5_in_order():
    catalogue = presets.preset_catalogue()
    assert [(p.oxidiser_label, p.fuel_label) for p in catalogue] == SUTTON_PAIRS
    assert len({p.key for p in catalogue}) == 14
    assert all("Table 5-5" in p.source for p in catalogue)


def test_only_the_two_rfna_pairs_are_blocked():
    blocked = [p for p in presets.preset_catalogue() if not p.executable]
    assert [p.label for p in blocked] == [
        "Red fuming nitric acid / RP-1",
        "Red fuming nitric acid / 50 % UDMH + 50 % hydrazine"]
    for preset in blocked:
        assert preset.oxidiser == "" and preset.fuel == ""
        assert preset.oxidiser_fuel_ratio is None
        assert "IRFNA" in preset.blocker and "not substituted" in preset.blocker
    assert len(presets.executable_presets()) == 12


def test_every_executable_preset_names_real_catalogue_reactants_in_their_roles():
    for preset in presets.executable_presets():
        oxidiser = gateway.propellant_named(preset.oxidiser)
        fuel = gateway.propellant_named(preset.fuel)
        assert oxidiser is not None and oxidiser.is_oxidiser, preset.key
        assert fuel is not None and fuel.is_fuel, preset.key
        assert preset.oxidiser_fuel_ratio > 0.0


def test_the_mixture_presets_use_the_mixture_definitions():
    assert presets.preset_named("sutton-nto-a50").fuel == "A-50"
    assert presets.preset_named("sutton-htp90-rp1").oxidiser == "HTP-90"


def test_lf2_n2h4_uses_the_shifting_optimum_ratio():
    """Table 5-5 prints this pair's Isp values in swapped columns; the
    shifting optimum is the 2.30 row (checked in test_sutton_table_5_5)."""
    assert presets.preset_named("sutton-f2-n2h4").oxidiser_fuel_ratio == 2.30


def test_matching_is_exact():
    preset = presets.preset_named("sutton-nto-mmh")
    assert presets.preset_matching("NTO", "MMH", 2.15) is preset
    assert presets.preset_matching("NTO", "MMH", 2.16) is None
    assert presets.preset_matching("LOX", "MMH", 2.15) is None


def test_a_blend_is_described_by_its_components_and_basis():
    """Display identity stays the engineering name; the provider identity is
    the exact CEA components with their fractions and basis."""
    htp = gateway.propellant_named("HTP-90")
    assert htp.label.startswith("HTP-90")
    assert htp.provider_name == "90 % H2O2(L) + 10 % H2O(L) by mass"
    assert htp.temperature_range is None          # H2O(L) declares no range
    a50 = gateway.propellant_named("A-50")
    assert a50.provider_name == "50 % C2H8N2(L),UDMH + 50 % N2H4(L) by mass"
    assert a50.temperature_range == (288.15, 308.15)
    assert gateway.propellant_named("MMH").provider_name == "CH6N2(L)"


# ---------------------------------------------------------------------------
# the controller
# ---------------------------------------------------------------------------


@pytest.fixture()
def controller(qt_app, stub_gateway):
    return ThermochemistryController()


def test_applying_a_preset_sets_the_pair_ratio_and_reference_temperatures(
        controller, stub_gateway):
    controller.applyPreset("sutton-htp90-rp1")
    assert (controller.oxidiser, controller.fuel) == ("HTP-90", "RP-1")
    assert controller.mixtureRatio == 7.0
    assert controller.oxidiserTemperature == 298.15
    assert controller.fuelTemperature == 298.15
    assert controller.currentPreset == "sutton-htp90-rp1"
    assert stub_gateway.calls == []                   # selection never solves


def test_a_cryogenic_preset_moves_to_cryogenic_reference_temperatures(controller):
    controller.applyPreset("sutton-f2-h2")
    assert controller.oxidiserTemperature == 85.02
    assert controller.fuelTemperature == 20.27


def test_editing_the_ratio_turns_the_form_into_a_custom_case(controller):
    controller.applyPreset("sutton-nto-n2h4")
    controller.mixtureRatio = 1.5
    assert controller.currentPreset == ""


def test_a_blocked_or_unknown_preset_changes_nothing(controller):
    before = (controller.oxidiser, controller.fuel, controller.mixtureRatio)
    controller.applyPreset("sutton-rfna-rp1")
    controller.applyPreset("no-such-preset")
    assert (controller.oxidiser, controller.fuel, controller.mixtureRatio) == before


def test_applying_a_preset_marks_an_existing_result_stale(controller):
    controller.calculate()
    headline = controller.resultHeadline
    controller.applyPreset("sutton-o2-rp1")
    assert controller.resultStale is True
    assert controller.resultHeadline == headline       # never relabelled


def test_the_selector_offers_only_executable_presets_and_says_what_is_withheld(controller):
    keys = [option["key"] for option in controller.presetOptions]
    assert keys == [p.key for p in presets.executable_presets()]
    assert [p["key"] for p in controller.blockedPresets] == [
        "sutton-rfna-rp1", "sutton-rfna-a50"]
    assert "RFNA" in controller.presetNote and "Table 5-5" in controller.presetNote


def test_the_default_case_is_still_the_accepted_lox_methane_case(controller):
    assert (controller.oxidiser, controller.fuel, controller.mixtureRatio) == (
        "LOX", "LCH4", 3.4)
    assert controller.currentPreset == ""


# ---------------------------------------------------------------------------
# end to end, with the real provider
# ---------------------------------------------------------------------------

PSIA = 6894.757293168


@requires_cea
@pytest.mark.parametrize("key", [p.key for p in presets.executable_presets()])
def test_every_executable_preset_completes_chamber_and_performance(gateway, key):
    """Through the production chain the workspace uses: the service, the
    gateway's provider, then RocketForge's own ideal performance."""
    from rocketforge.application.analysis import performance_service as perf
    from rocketforge.application.analysis.thermochemistry_service import (
        ChamberCase, solve_case)
    from rocketforge.engineering.chamber import ChamberGammaBasis
    from rocketforge.physics.compressible import isentropic
    from rocketforge.physics.compressible.gas import PerfectGas
    from rocketforge.physics.thermochemistry import GammaStrategy

    preset = presets.preset_named(key)
    oxidiser = gateway.propellant_named(preset.oxidiser)
    fuel = gateway.propellant_named(preset.fuel)
    chamber = solve_case(ChamberCase(
        fuel=fuel.key, oxidiser=oxidiser.key,
        oxidiser_fuel_ratio=preset.oxidiser_fuel_ratio,
        chamber_pressure=1000 * PSIA,
        fuel_temperature=fuel.reference_temperature,
        oxidiser_temperature=oxidiser.reference_temperature))
    assert chamber.kind in ("ok", "warning"), chamber.message
    state = chamber.state
    assert 2500.0 < state.temperature < 5000.0
    assert not any(str(d.severity) == "error" for d in chamber.diagnostics)

    exit_pressure = 14.7 * PSIA
    for basis, gamma in ((ChamberGammaBasis.FROZEN, state.gamma_frozen),
                         (ChamberGammaBasis.EQUILIBRIUM, state.gamma)):
        gas = PerfectGas(gamma=gamma)
        area_ratio = float(isentropic.area_ratio(
            isentropic.mach_from_pressure_ratio(exit_pressure / state.pressure, gas),
            gas))
        outcome = perf.solve_performance(chamber, perf.PerformanceCase(
            gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=basis,
            area_ratio=area_ratio,
            ambient=perf.AmbientCondition(perf.AmbientMode.CUSTOM, exit_pressure)))
        assert outcome.result is not None, outcome.message
        result = outcome.result
        for value in (result.characteristic_velocity, result.thrust_coefficient,
                      result.specific_impulse):
            assert math.isfinite(value) and value > 0.0
        assert 1200.0 < result.characteristic_velocity < 2700.0
        assert 200.0 < result.specific_impulse < 450.0
