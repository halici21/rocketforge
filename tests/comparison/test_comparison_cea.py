"""RocketForge against its references, through the comparison layer.

Needs NASA CEA; skips with a reason when it is absent.
"""

from __future__ import annotations

import math
import pathlib
import subprocess
import sys

import numpy as np
import pytest

from rocketforge.comparison import (
    AGREES,
    DIFFERS,
    ReferenceCase,
    ReferenceQuantity,
    SourceKind,
    compare,
    observed_from_chamber,
)
from rocketforge.comparison.rp1311 import (
    RP1311_EXAMPLE5_PUBLISHED,
    RP1311_EXAMPLE12_PUBLISHED,
    RP1311_EXAMPLE13_PUBLISHED,
)
from rocketforge.physics.solid_propellant import (
    SolidFormulation,
    SolidFormulationEquilibriumRequest,
    SolidIngredient,
)
from rocketforge.physics.thermochemistry import (
    ChemistryMode,
    EquilibriumConstraint,
    ThermochemistryProvenance,
)
from rocketforge.providers.cea import check_availability
from rocketforge.providers.cea.units import pressure_from_bar
from rocketforge.providers.cea_solid import (
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    solve_solid_chamber,
    solve_solid_equilibrium_cstar,
)

_AVAILABILITY = check_availability()
requires_cea = pytest.mark.skipif(
    not _AVAILABILITY.is_usable,
    reason=f"NASA CEA provider unavailable ({_AVAILABILITY.status.value})")

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROVENANCE = ThermochemistryProvenance(
    provider_id="nasa-cea", database="thermo.lib",
    chemistry_mode=ChemistryMode.EQUILIBRIUM,
    equilibrium_constraint=EquilibriumConstraint.HP)


@pytest.fixture(scope="module")
def cea_module():
    if not _AVAILABILITY.is_usable:
        pytest.skip("NASA CEA is not installed")
    import cea
    return cea


def solve(cea, formulation, pc_bar, products=None, omit=()):
    request = SolidFormulationEquilibriumRequest(
        formulation=formulation, chamber_pressure=pressure_from_bar(pc_bar),
        product_species=products, omit_species=omit)
    chamber = solve_solid_chamber(cea, request, provenance=PROVENANCE)
    cstar = solve_solid_equilibrium_cstar(cea, request, chamber)
    return chamber, cstar


def by_weights(names, weights):
    total = math.fsum(float(w) for w in weights)
    fractions = [float(w) / total for w in weights]
    fractions[-1] = 1.0 - math.fsum(fractions[:-1])
    return SolidFormulation(name="mechanism", ingredients=tuple(
        SolidIngredient(n, f) for n, f in zip(names, fractions)))


@requires_cea
def test_example5_agrees_with_every_quantity_nasa_prints(cea_module):
    """Class A. Fifty quantities -- ten scalars and all forty printed species --
    each within half of NASA's last printed digit."""
    chamber, _ = solve(cea_module, RP1311_EXAMPLE5, RP1311_EXAMPLE5_PRESSURES_BAR[0],
                       omit=RP1311_EXAMPLE5_OMIT)
    result = compare(RP1311_EXAMPLE5_PUBLISHED, observed_from_chamber(chamber))
    assert result.verdict == AGREES
    assert len(result.rows) == 50
    assert not result.not_observed


@requires_cea
def test_example12_chamber_and_cstar_agree_with_the_printout(cea_module):
    """Class B mechanism check, not a solid propellant."""
    names = ["CH6N2(L)", "N2O4(L)"]
    weights = cea_module.Mixture(names).of_ratio_to_weights(
        np.array([0.0, 1.0]), np.array([1.0, 0.0]), 2.5)
    products = ("CO", "CO2", "H", "HNO", "HNO2", "HO2", "H2", "H2O", "H2O2",
                "N", "NO", "NO2", "N2", "N2O", "O", "OH", "O2", "HCO", "NH",
                "CH4", "NH2", "NH3", "H2O(L)", "C(gr)")
    chamber, cstar = solve(cea_module, by_weights(names, weights),
                           cea_module.units.psi_to_bar(1000), products=products)
    observed = observed_from_chamber(chamber, characteristic_velocity=cstar.value)
    assert compare(RP1311_EXAMPLE12_PUBLISHED, observed).verdict == AGREES


@requires_cea
def test_example13_reports_its_explained_difference_rather_than_hiding_it(cea_module):
    """Class B. Chamber agrees; c* prints one digit lower (6386.74 against
    6386.75 ft/s) because NASA's run uses a BeO(L) insert at a throat sitting
    on beryllium oxide's melting point. The comparison says ``differs`` --
    which is true -- and the case notes say why."""
    names = ["N2H4(L)", "Be(a)", "H2O2(L)"]
    weights = cea_module.Mixture(names).of_ratio_to_weights(
        np.array([0.0, 0.0, 1.0]), np.array([0.8, 0.2, 0.0]), 33.0 / 67.0)
    chamber, cstar = solve(cea_module, by_weights(names, weights),
                           cea_module.units.psi_to_bar(3000))
    result = compare(RP1311_EXAMPLE13_PUBLISHED, observed_from_chamber(
        chamber, characteristic_velocity=cstar.value))
    verdicts = {row.key: row.verdict for row in result.rows}
    assert verdicts == {"chamber_pressure": AGREES,
                        "chamber_temperature": AGREES,
                        "characteristic_velocity": DIFFERS}
    assert result.verdict == DIFFERS
    assert "insert" in RP1311_EXAMPLE13_PUBLISHED.notes
    c_star = next(r for r in result.rows if r.key == "characteristic_velocity")
    assert abs(c_star.rel_diff) < 1e-5


@requires_cea
def test_example5_against_direct_cea_is_identical(cea_module):
    """A direct-CEA case at zero tolerance: every value bit for bit."""
    direct = _direct_example5(cea_module)
    case = ReferenceCase(
        case_id="rp1311-example5-direct", title="Example 5, direct CEA",
        source_kind=SourceKind.CEA_DIRECT, benchmark_class="A",
        source="cea.EqSolver and cea.RocketSolver, run directly",
        code="NASA CEA", code_version="as installed", inputs={},
        tolerance_rel=0.0, quantities=(
            ReferenceQuantity("chamber_temperature", direct["T"], "K"),
            ReferenceQuantity("molar_mass", direct["MW"], "kg/kmol"),
            ReferenceQuantity("gamma_s", direct["gamma_s"], "1"),
            ReferenceQuantity("characteristic_velocity", direct["c_star"], "m/s"),
            ReferenceQuantity("mole_fraction:AL2O3(L)", direct["x_al2o3"], "1")))
    chamber, cstar = solve(cea_module, RP1311_EXAMPLE5,
                           RP1311_EXAMPLE5_PRESSURES_BAR[0], omit=RP1311_EXAMPLE5_OMIT)
    result = compare(case, observed_from_chamber(
        chamber, characteristic_velocity=cstar.value))
    assert result.verdict == AGREES, result.as_records()


def _direct_example5(cea) -> dict:
    """Example 5 solved with CEA alone -- no RocketForge code in the solve."""
    reactants = []
    for item in RP1311_EXAMPLE5.ingredients:
        custom = item.custom
        reactants.append(item.name if custom is None else cea.Reactant(
            name=item.name, formula=dict(custom.formula),
            molecular_weight=custom.molecular_weight,
            enthalpy=custom.heat_of_formation,
            enthalpy_units=custom.heat_of_formation_units,
            temperature=custom.reference_temperature))
    weights = np.asarray(RP1311_EXAMPLE5.mass_fractions)
    pc = RP1311_EXAMPLE5_PRESSURES_BAR[0]
    reac = cea.Mixture(reactants)
    prod = cea.Mixture(reactants, products_from_reactants=True,
                       omit=list(RP1311_EXAMPLE5_OMIT))
    h0 = reac.calc_property(cea.ENTHALPY, weights, [298.15] * 5)
    eq = cea.EqSolver(prod, reactants=reac)
    sol = cea.EqSolution(eq)
    eq.solve(sol, cea.HP, h0 / cea.R, pc, weights)
    rocket = cea.RocketSolver(prod, reactants=reac)
    rsol = cea.RocketSolution(rocket)
    rocket.solve(rsol, weights, pc, [10.0], iac=True, hc=h0 / cea.R)
    return {"T": float(sol.T), "MW": float(sol.MW), "gamma_s": float(sol.gamma_s),
            "c_star": float(rsol.c_star[0]),
            "x_al2o3": float(sol.mole_fractions["AL2O3(L)"])}


@requires_cea
def test_the_committed_reference_module_is_reproduced_byte_for_byte(tmp_path):
    """Generated from NASA's shipped scripts, never typed. Re-running the
    generator must give the committed file exactly."""
    out = tmp_path / "rp1311.py"
    subprocess.run([sys.executable, str(ROOT / "experiments" / "solid_propellant_r1"
                                        / "generate_rp1311_reference_cases.py"),
                    str(out)], check=True, capture_output=True)
    committed = ROOT / "rocketforge" / "comparison" / "rp1311.py"
    assert out.read_bytes() == committed.read_bytes()


@requires_cea
def test_extraction_reads_the_basis_and_adds_cstar_only_when_given(cea_module):
    chamber, cstar = solve(cea_module, RP1311_EXAMPLE5,
                           RP1311_EXAMPLE5_PRESSURES_BAR[0], omit=RP1311_EXAMPLE5_OMIT)
    plain = observed_from_chamber(chamber)
    assert "mole_fraction:AL2O3(L)" in plain
    assert not any(k.startswith("mass_fraction:") for k in plain)
    assert "characteristic_velocity" not in plain
    with_cstar = observed_from_chamber(chamber, characteristic_velocity=cstar.value)
    assert with_cstar["characteristic_velocity"].value == cstar.value
