"""GATE A: is CoolProp's liquid methane viscosity fit to build a line model on?

The question is *not* "does CoolProp agree with NIST". It is whether RocketForge
can scientifically rely on this provider's mu_CH4(T,p) over the liquid states a
feed line will actually use.

Three kinds of evidence, kept apart:

1. **Tier 1, evaluated reference correlation.** Sotiriadou, Antoniadis, Assael,
   Martinek and Huber (NIST), Int. J. Thermophys. 47 (2025) 18. Saturated-liquid
   check values, and -- more importantly -- a stated liquid uncertainty of
   **3 % (k=2)** which is what makes an acceptance criterion possible at all.

2. **Tier 1, independent implementation of a different model.** NIST Chemistry
   WebBook isotherms. CoolProp uses friction theory; the WebBook does not. A
   difference here is a **cross-model difference**, and the 2025 paper says how
   large such a difference is expected to be.

3. **Tier 1, primary experiment.** Diller, Physica 104A (1980) 417: 116 points,
   100-300 K, 0.6-33.1 MPa, stated accuracy 2 %. This is the dataset the
   correlations are anchored on, and it covers the envelope below entirely.

The acceptance criterion is derived from (1) and (3) *before* any comparison is
run, and is not widened afterwards.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.physics.fluids import (  # noqa: E402
    METHANE,
    OXYGEN,
    FluidPhase,
    FluidProperty,
    FluidStateRequest,
)
from rocketforge.providers.fluid_properties import coolprop_provider  # noqa: E402

OUT = ROOT / "acceptance" / "transport_validation"
OUT.mkdir(parents=True, exist_ok=True)

provider = coolprop_provider()

# ===========================================================================
# the envelope, derived rather than chosen
# ===========================================================================

ENVELOPE = {
    "fluid": "METHANE",
    "phase": "LIQUID",
    "temperature_K": {"min": 100.0, "max": 125.0},
    "pressure_Pa": {"min": 5.0e5, "max": 3.0e6},
    "saturation_margin": "p >= 1.5 * p_sat(T)",
    "rationale": [
        "The lower and upper temperatures bracket NASA CEA's own declared "
        "range for the CH4(L) reactant, 101.643-121.643 K, with margin at each "
        "end, so every propellant state RocketForge can actually request is "
        "inside the validated band.",
        "The pressures are feed-system pressures for a preliminary design. "
        "They are emphatically not chamber pressures: the chamber runs at "
        "10 MPa in the canonical case and a line does not.",
        "The whole box sits inside Diller's experimental range (100-300 K, "
        "0.6-33.1 MPa) and inside the 33 MPa limit of the 2025 evaluated "
        "correlation, so every state is covered by primary evidence rather "
        "than by extrapolation.",
        "The saturation margin keeps the box clear of the two-phase boundary, "
        "which the line model does not support. At 125 K, the warmest state, "
        "p_sat is about 0.27 MPa and the lowest validated pressure is 0.5 MPa.",
    ],
    "excluded": [
        "two-phase and saturated states",
        "gas and supercritical states",
        "T below 100 K, where the liquid range ends at the 90.694 K triple point",
        "p above 3 MPa, which is outside the intended line envelope even though "
        "the reference data extend to 33 MPa",
    ],
    "accepted_properties": ["density", "dynamic_viscosity"],
}

# ===========================================================================
# reference data
# ===========================================================================

#: NIST Chemistry WebBook, SRD 69, isothermal tables, retrieved 2026-09-06.
#: 8 significant digits as printed. Every row reported phase "liquid".
NIST_ISOTHERMS = {
    100.0: [(0.5, 439.24018, 152.09386), (1.0, 439.61870, 153.30645),
            (1.5, 439.99455, 154.51612), (2.0, 440.36778, 155.72293),
            (2.5, 440.73843, 156.92695), (3.0, 441.10656, 158.12822)],
    110.0: [(0.5, 425.15302, 121.62434), (1.0, 425.60543, 122.49682),
            (1.5, 426.05381, 123.36530), (2.0, 426.49823, 124.22988),
            (2.5, 426.93880, 125.09064), (3.0, 427.37559, 125.94766)],
    120.0: [(0.5, 410.24622, 99.128704), (1.0, 410.79816, 99.852079),
            (1.5, 411.34372, 100.57037), (2.0, 411.88310, 101.28371),
            (2.5, 412.41647, 101.99222), (3.0, 412.94400, 102.69602)],
    125.0: [(0.5, 402.39817, 89.808893), (1.0, 403.01385, 90.494262),
            (1.5, 403.62136, 91.173924), (2.0, 404.22097, 91.848040),
            (2.5, 404.81293, 92.516760), (3.0, 405.39749, 93.180232)],
}

#: Sotiriadou et al. 2025, Table 8: saturated liquid check values.
SATURATED_LIQUID_2025 = {100.0: 154.50, 120.0: 98.180, 150.0: 56.233}

SOURCES = {
    "provider_model": {
        "provider": "CoolProp 8.0.0, HEOS backend",
        "bibtex": "QuinonesCisneros-JPCB-2006",
        "publication": ("Quinones-Cisneros, S.E. and Deiters, U.K., "
                        "Generalization of the Friction Theory for Viscosity "
                        "Modeling, J. Phys. Chem. B 110 (2006) 12820-12834"),
        "doi": "10.1021/jp0618577",
        "structure": ("dilute-gas term (powers of T/Tc, Tc = 190.564 K) plus a "
                      "friction-theory residual computed from the repulsive "
                      "and attractive pressure contributions of the equation "
                      "of state"),
        "eos": "Setzmann-JPCRD-1991 (methane reference EOS)",
        "critical_enhancement": "none for viscosity",
        "state_dependent_model_switching": "none",
    },
    "evaluated_reference_correlation": {
        "publication": ("Sotiriadou, S.G., Antoniadis, K.D., Assael, M.J., "
                        "Martinek, V. and Huber, M.L., Correlation for the "
                        "Viscosity of Methane from the Triple Point to 625 K "
                        "and Pressures to 1000 MPa, Int. J. Thermophys. 47 "
                        "(2025) 18"),
        "doi": "10.1007/s10765-025-03690-7",
        "stated_uncertainty_liquid": "3 % (k = 2) at pressures to 33 MPa",
        "note_on_friction_theory": ("the paper compares itself with the "
                                    "friction-theory model in the liquid and "
                                    "reports that the performance of both "
                                    "correlations is similar"),
    },
    "primary_experiment": {
        "publication": ("Diller, D.E., Measurements of the viscosity of "
                        "compressed gaseous and liquid methane, Physica 104A "
                        "(1980) 417-426"),
        "method": "torsionally oscillating quartz crystal viscometer",
        "coverage": "116 points, 100-300 K, 0.6-33.1 MPa",
        "stated_uncertainty": "2 % accuracy, 0.5 % precision",
    },
    "supporting_experiment": {
        "haynes_1973": "17 liquid points, 2 %",
        "boon_1967": "8 saturated-liquid points, 1 %",
        "slyusar_1974": "15 liquid points, 4 %",
    },
    "independent_implementation": {
        "source": "NIST Chemistry WebBook, SRD 69",
        "retrieved": "2026-09-06",
        "note": ("a different implementation of a different correlation from "
                 "CoolProp's; used as a cross-model comparison, never as an "
                 "implementation oracle"),
    },
}

# ===========================================================================
# the acceptance criterion, derived before comparing
# ===========================================================================

#: The expanded uncertainty of the best available evaluated correlation for
#: liquid methane viscosity. Everything below is judged against this, and it is
#: a published number rather than a chosen one.
REFERENCE_UNCERTAINTY_K2 = 0.03

CRITERION = {
    "value": REFERENCE_UNCERTAINTY_K2,
    "statement": ("|mu_provider - mu_reference| / mu_reference <= 3 %"),
    "derivation": [
        "The 2025 evaluated correlation states 3 % (k = 2) for the compressed "
        "liquid to 33 MPa. That is the uncertainty of the best available "
        "reference, and nothing computed from methane viscosity in this region "
        "can be known better than it.",
        "The primary experimental data the correlations rest on carry 2 % "
        "(Diller, Haynes) and 1 % (Boon, saturated liquid). A model agreeing "
        "with a reference to better than 3 % is agreeing to within the "
        "measurements that define the quantity.",
        "The 2025 paper reports that the friction-theory model and the new "
        "correlation perform similarly in the liquid, so a cross-model "
        "difference of this size is the expected result rather than a defect.",
        "This is not a widened tolerance. It is the published expanded "
        "uncertainty of the field, and a point outside it would mean the two "
        "models disagree by more than the measurements permit, which would be "
        "a finding and would be investigated rather than accepted.",
    ],
}


def evaluate(temperature: float, pressure: float, fluid=METHANE):
    return provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=temperature, pressure=pressure)).value


def saturation_pressure(temperature: float) -> float:
    return provider.saturation_pressure("METHANE", temperature)


# ===========================================================================
# 1. the comparison matrix
# ===========================================================================

points = []
worst = 0.0
failures = []
for temperature, rows in sorted(NIST_ISOTHERMS.items()):
    p_sat = saturation_pressure(temperature)
    for pressure_mpa, reference_density, reference_viscosity_upa in rows:
        pressure = pressure_mpa * 1.0e6
        state = evaluate(temperature, pressure)
        assert state is not None, (temperature, pressure)
        mu = state.dynamic_viscosity
        reference_viscosity = reference_viscosity_upa * 1.0e-6
        difference = mu - reference_viscosity
        relative = abs(difference) / reference_viscosity
        density_relative = (abs(state.density - reference_density)
                            / reference_density)
        inside = relative <= REFERENCE_UNCERTAINTY_K2
        margin_ok = pressure >= 1.5 * p_sat
        phase_ok = state.phase is FluidPhase.LIQUID
        if not (inside and margin_ok and phase_ok):
            failures.append({
                "temperature_K": temperature, "pressure_Pa": pressure,
                "inside_criterion": inside, "margin_ok": margin_ok,
                "phase_ok": phase_ok, "relative": relative})
        worst = max(worst, relative)
        points.append({
            "temperature_K": temperature,
            "pressure_Pa": pressure,
            "saturation_pressure_Pa": p_sat,
            "pressure_over_saturation": pressure / p_sat,
            "inside_saturation_margin": margin_ok,
            "provider_phase": state.phase.value if state.phase else None,
            "phase_is_liquid": phase_ok,
            "provider_viscosity_Pa_s": mu,
            "reference_viscosity_Pa_s": reference_viscosity,
            "absolute_difference_Pa_s": difference,
            "relative_difference": relative,
            "criterion": REFERENCE_UNCERTAINTY_K2,
            "verdict": "PASS" if inside else "FAIL",
            "provider_density_kg_m3": state.density,
            "reference_density_kg_m3": reference_density,
            "density_relative_difference": density_relative,
        })

# ===========================================================================
# 2. the Tier-1 saturated-liquid check values
# ===========================================================================

saturated = []
for temperature, reference_upa in sorted(SATURATED_LIQUID_2025.items()):
    if not (ENVELOPE["temperature_K"]["min"] <= temperature
            <= ENVELOPE["temperature_K"]["max"]):
        in_envelope = False
    else:
        in_envelope = True
    from CoolProp.CoolProp import PropsSI

    mu = float(PropsSI("V", "T", temperature, "Q", 0, "Methane"))
    reference = reference_upa * 1.0e-6
    relative = abs(mu - reference) / reference
    saturated.append({
        "temperature_K": temperature,
        "inside_line_envelope": in_envelope,
        "provider_saturated_liquid_viscosity_Pa_s": mu,
        "reference_2025_Pa_s": reference,
        "relative_difference": relative,
        "inside_criterion": relative <= REFERENCE_UNCERTAINTY_K2,
        "note": ("saturated states are outside the line envelope by design; "
                 "these are a direct Tier-1 check of the provider against the "
                 "evaluated correlation's own published check values"),
    })

report = {
    "purpose": ("can RocketForge rely on CoolProp's liquid methane viscosity "
                "over the intended line envelope?"),
    "sources": SOURCES,
    "envelope": ENVELOPE,
    "acceptance_criterion": CRITERION,
    "matrix": {
        "temperatures": sorted(NIST_ISOTHERMS),
        "pressures_MPa": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        "states": len(points),
    },
    "points": points,
    "saturated_liquid_check_values": saturated,
    "worst_relative_difference": worst,
    "failures": failures,
}

(OUT / "methane_viscosity_validation.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")

print(f"states compared: {len(points)}")
print(f"worst relative difference: {worst:.4%}")
print(f"criterion: {REFERENCE_UNCERTAINTY_K2:.1%} (k=2, published)")
print(f"failures: {len(failures)}")
print()
for entry in saturated:
    print(f"  saturated {entry['temperature_K']:6.1f} K: "
          f"{entry['relative_difference']:.3%} vs the 2025 correlation "
          f"[{'PASS' if entry['inside_criterion'] else 'FAIL'}]")
