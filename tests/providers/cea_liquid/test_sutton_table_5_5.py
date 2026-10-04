"""Sutton & Biblarz Table 5-5 against RocketForge's NASA CEA path.

**An external comparison, not an oracle.** Table 5-5 states no reactant
temperatures, predates the shipped ``thermo.lib`` and prints three or four
significant figures; RocketForge is never tuned toward it. Every compared cell
must do one of two things:

* agree within the source-condition band recorded in the fixture, or
* be listed in the fixture's ``anomalies`` with a classification -- and that
  classification is itself checked here, so "the source is wrong" is a tested
  claim and not a shrug. If a later change moved RocketForge onto an anomalous
  printed value, the anomaly test would fail too.

Semantics are matched, not assumed: chamber temperature, molar mass and k come
from the HP chamber equilibrium; shifting Isp from CEA's equilibrium expansion
and frozen Isp from its expansion frozen at the chamber, both to an exit
pressure of 14.7 psia (the "optimum expansion" of the table), found by solving
for the area ratio; c* from the equilibrium expansion. Sutton's k is compared
with the frozen ratio cp/cv, and a separate test shows it is that ratio and
not the isentropic exponent gamma_s.
"""

from __future__ import annotations

import json
import math
import pathlib
from functools import lru_cache

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ExpansionMode,
    MixtureRatio,
    PropellantStream,
)
from rocketforge.providers.cea import PRODUCTION_PROPELLANTS, check_availability
from rocketforge.providers.cea_liquid import LIQUID_PROPELLANTS, CEALiquidProvider

CEA_PRESENT = check_availability().is_usable
pytestmark = pytest.mark.skipif(not CEA_PRESENT,
                                reason="NASA CEA provider unavailable")

FIXTURE = json.loads((pathlib.Path(__file__).with_name("sutton_table_5_5.json"))
                     .read_text(encoding="utf-8"))
PSIA = 6894.757293168
PC = FIXTURE["conditions"]["chamber_pressure_psia"] * PSIA
PE = FIXTURE["conditions"]["exit_pressure_psia"] * PSIA
BANDS = {k: v for k, v in FIXTURE["bands"].items() if k != "rationale"}
QUANTITIES = ("tc", "cstar", "molar_mass", "isp_shifting", "isp_frozen", "k")
DEFINITIONS = {**PRODUCTION_PROPELLANTS, **LIQUID_PROPELLANTS}


def _key(row) -> tuple[str, str, float]:
    return (row["oxidiser"], row["fuel"], float(row["of"]))


ROWS = {_key(row): row for row in FIXTURE["rows"]}


def _anomaly_cells() -> dict[tuple[tuple[str, str, float], str], str]:
    cells = {}
    for anomaly in FIXTURE["anomalies"]:
        quantities = (("isp_shifting", "isp_frozen") if anomaly["quantity"] == "isp"
                      else (anomaly["quantity"],))
        for ox, fuel, of in anomaly["rows"]:
            for quantity in quantities:
                if quantity in ROWS[(ox, fuel, float(of))]:
                    cells[((ox, fuel, float(of)), quantity)] = anomaly["id"]
    return cells


ANOMALIES = _anomaly_cells()


@lru_cache(maxsize=1)
def _provider() -> CEALiquidProvider:
    return CEALiquidProvider()


def _request(key) -> ChamberEquilibriumRequest:
    ox, fuel, of = key
    oxidiser, fuel_def = DEFINITIONS[ox], DEFINITIONS[fuel]
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(fuel_def, fuel_def.reference_temperature),
        oxidiser=PropellantStream(oxidiser, oxidiser.reference_temperature),
        oxidiser_fuel_ratio=MixtureRatio(of), chamber_pressure=PC)


def _optimum_expansion(request, mode):
    """CEA's rocket solution at the area ratio whose exit pressure is 1 atm.

    Bisection in log(area ratio) on the frozen provider's own area-ratio
    oracle: exit pressure falls monotonically with area ratio. 50 halvings of
    [2, 60] leave the area ratio to 1e-14 relative.
    """
    low, high = math.log(2.0), math.log(60.0)
    oracle = None
    for _ in range(50):
        middle = 0.5 * (low + high)
        oracle = _provider().rocket_oracle(request, area_ratio=math.exp(middle),
                                           expansion_mode=mode)
        if oracle.exit.pressure > PE:
            low = middle
        else:
            high = middle
    assert oracle.exit.pressure == pytest.approx(PE, rel=1e-9)
    return oracle


@lru_cache(maxsize=None)
def computed(key) -> dict[str, float]:
    request = _request(key)
    solution = _provider().solve_chamber(request)
    assert solution.value is not None, key
    state = solution.value
    shifting = _optimum_expansion(request, ExpansionMode.EQUILIBRIUM)
    frozen = _optimum_expansion(request, ExpansionMode.FROZEN)
    return {
        "tc": state.temperature,
        "molar_mass": state.molar_mass * 1.0e3,
        "k": state.gamma_frozen,
        "gamma_s": state.gamma,
        "cstar": shifting.c_star,
        "cstar_frozen": frozen.c_star,
        "isp_shifting": shifting.specific_impulse_seconds,
        "isp_frozen": frozen.specific_impulse_seconds,
    }


def deviation(key, quantity, printed=None) -> float:
    value = ROWS[key][quantity] if printed is None else printed
    return computed(key)[quantity] / value - 1.0


def within(key, quantity, printed=None) -> bool:
    return abs(deviation(key, quantity, printed)) <= BANDS[quantity]


CELLS = [(key, quantity) for key, row in ROWS.items()
         for quantity in QUANTITIES if quantity in row]


def test_the_fixture_covers_every_executable_sutton_pair():
    from rocketforge.application.analysis.thermochemistry_presets import executable_presets

    pairs = {(key[0], key[1]) for key in ROWS}
    assert pairs == {(p.oxidiser, p.fuel) for p in executable_presets()}
    assert len(pairs) == 12


@pytest.mark.parametrize("key,quantity",
                         [c for c in CELLS if c not in ANOMALIES],
                         ids=[f"{k[0]}-{k[1]}-{k[2]}-{q}" for k, q in CELLS
                              if (k, q) not in ANOMALIES])
def test_unclassified_cells_agree_within_the_source_band(key, quantity):
    assert within(key, quantity), (
        f"{key} {quantity}: computed {computed(key)[quantity]:.4g} vs Sutton "
        f"{ROWS[key][quantity]} ({100 * deviation(key, quantity):+.2f} %), outside "
        f"the {100 * BANDS[quantity]:.0f} % band and not a classified anomaly")


@pytest.mark.parametrize("cell", sorted(ANOMALIES), ids=lambda c: f"{c[0]}-{c[1]}")
def test_every_classified_anomaly_really_is_outside_the_band(cell):
    key, quantity = cell
    assert not within(key, quantity)


def test_lox_lh2_chamber_temperature_contradicts_its_own_row():
    key = ("LOX", "LH2", 3.40)
    assert deviation(key, "tc") < -BANDS["tc"]
    for quantity in ("cstar", "molar_mass", "isp_frozen"):
        assert within(key, quantity), quantity


def test_lf2_n2h4_isp_values_sit_in_swapped_columns():
    low, high = ("LF2", "N2H4", 1.83), ("LF2", "N2H4", 2.30)
    # As printed, both disagree...
    assert not within(low, "isp_shifting") and not within(high, "isp_frozen")
    # ...and both agree once each is read as the other mode.
    assert within(low, "isp_frozen", printed=ROWS[low]["isp_shifting"])
    assert within(high, "isp_shifting", printed=ROWS[high]["isp_frozen"])


def test_nto_n2h4_chamber_temperatures_sit_in_swapped_rows():
    a, b = ("NTO", "N2H4", 1.08), ("NTO", "N2H4", 1.34)
    assert not within(a, "tc") and not within(b, "tc")
    assert within(b, "tc", printed=ROWS[a]["tc"])
    assert within(a, "tc", printed=ROWS[b]["tc"])
    for key in (a, b):
        for quantity in ("cstar", "molar_mass"):
            assert within(key, quantity), (key, quantity)


def _ideal_cstar(row) -> float:
    """c* of a calorically perfect gas at the row's own printed T, M and k."""
    k = row["k"]
    gas_constant = 8314.462618 / row["molar_mass"]
    throat = (2.0 / (k + 1.0)) ** ((k + 1.0) / (2.0 * (k - 1.0)))
    return math.sqrt(gas_constant * row["tc"] / k) / throat


@pytest.mark.parametrize("key", [("NTO", "A-50", 1.62), ("NTO", "MMH", 1.65)])
def test_low_printed_cstar_contradicts_the_rows_own_isp(key):
    assert deviation(key, "cstar") > BANDS["cstar"]
    # Low on the frozen basis too, and against the row's own T, M and k.
    assert computed(key)["cstar_frozen"] / ROWS[key]["cstar"] - 1.0 > BANDS["cstar"]
    assert _ideal_cstar(ROWS[key]) / ROWS[key]["cstar"] - 1.0 > BANDS["cstar"]
    printed_isp = [ROWS[key][q] for q in ("isp_shifting", "isp_frozen") if q in ROWS[key]]
    modes = ("isp_shifting", "isp_frozen")
    assert any(within(key, mode, printed=isp) for isp in printed_isp for mode in modes)


def test_lf2_n2h4_printed_cstar_is_the_frozen_throat_value():
    """Not a source error: the row is self-consistent on the frozen basis."""
    key = ("LF2", "N2H4", 1.83)
    row = ROWS[key]
    assert deviation(key, "cstar") > BANDS["cstar"]          # vs equilibrium c*
    assert abs(computed(key)["cstar_frozen"] / row["cstar"] - 1.0) <= BANDS["cstar"]
    assert _ideal_cstar(row) == pytest.approx(row["cstar"], rel=0.005)


@pytest.mark.parametrize("key", [("NTO", "RP-1", 3.4), ("HTP-90", "RP-1", 7.0)])
def test_printed_frozen_isp_297_contradicts_the_rows_own_chamber(key):
    assert deviation(key, "isp_frozen") < -BANDS["isp_frozen"]
    for quantity in ("tc", "molar_mass", "k"):
        assert within(key, quantity), quantity


def test_suttons_k_is_the_frozen_ratio_not_the_isentropic_exponent():
    """Semantics, not tolerance: every printed k is nearer cp/cv than gamma_s."""
    for key, row in ROWS.items():
        if "k" not in row:
            continue
        values = computed(key)
        assert abs(values["k"] - row["k"]) < abs(values["gamma_s"] - row["k"]), key
