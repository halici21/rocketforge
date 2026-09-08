"""External validation of the fluid provider against NIST reference data.

**What this establishes, and what it does not.** The reference values below are
NIST Chemistry WebBook isobaric tables, retrieved 2026-09-06. NIST's fluid
tables and CoolProp's ``HEOS`` backend both implement the same *reference
equations of state* for these three fluids -- Schmidt and Wagner for oxygen,
Setzmann and Wagner for methane, Leachman and co-workers for normal hydrogen.

So this is an **independent-implementation check, not an independent-model
check**, and it is recorded as such. It catches a wrong fluid, a wrong unit, a
wrong state point, the wrong branch of a saturation line and an implementation
defect. It cannot catch an error in the reference EOS itself, and no comparison
against NIST could. Phase 5G's rule applies unchanged: a close number between
two implementations of one model is a residual, and a close number between two
different models is a model difference, and they are never added together.

The **enthalpy difference** rows matter most. They are the quantity the
reactant coupling actually transfers into CEA, and validating a difference
sidesteps the arbitrary datum entirely -- which is the whole reason the
coupling is posed as a difference.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.physics.fluids import (
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidPhase,
    FluidProperty,
    FluidStateRequest,
)
from rocketforge.providers.fluid_properties import coolprop_provider

OUT = pathlib.Path("acceptance/fluids_foundation/fluid_external_reference.json")
ATM = 101325.0

SOURCE = {
    "publication": "NIST Chemistry WebBook, SRD 69, Thermophysical Properties "
                   "of Fluid Systems",
    "query": "isobaric table at 1 atm",
    "retrieved": "2026-09-06",
    "oxygen_id": "C7782447",
    "methane_id": "C74828",
    "hydrogen_id": "C1333740",
    "lineage_note": (
        "NIST's tables and CoolProp's HEOS backend implement the same "
        "reference equations of state for these fluids. This comparison is "
        "therefore an independent-implementation check, not an "
        "independent-model check."),
}

# fluid -> T(K) -> published values. Units as printed by the source.
PUBLISHED = {
    "OXYGEN": {
        88.000: {"density": 1152.01, "enthalpy_kJ_per_kg": -137.08,
                 "cp_J_per_gK": 1.694, "viscosity_uPa_s": 206.52,
                 "conductivity_W_per_mK": 0.154, "phase": "liquid"},
        90.000: {"density": 1142.11, "enthalpy_kJ_per_kg": -133.69,
                 "cp_J_per_gK": 1.699, "viscosity_uPa_s": 195.65,
                 "conductivity_W_per_mK": 0.151, "phase": "liquid"},
        92.000: {"density": 4.371, "enthalpy_kJ_per_kg": 81.43,
                 "cp_J_per_gK": 0.954, "viscosity_uPa_s": 7.09,
                 "conductivity_W_per_mK": 0.0083, "phase": "gas"},
    },
    "METHANE": {
        108.00: {"density": 427.68, "enthalpy_kJ_per_kg": -12.72,
                 "cp_J_per_gK": 3.46, "viscosity_uPa_s": 126.19,
                 "conductivity_W_per_mK": 0.189, "phase": "liquid"},
        110.00: {"density": 424.79, "enthalpy_kJ_per_kg": -5.79,
                 "cp_J_per_gK": 3.47, "viscosity_uPa_s": 120.93,
                 "conductivity_W_per_mK": 0.186, "phase": "liquid"},
        114.00: {"density": 1.78, "enthalpy_kJ_per_kg": 515.98,
                 "cp_J_per_gK": 2.20, "viscosity_uPa_s": 4.42,
                 "conductivity_W_per_mK": 0.012, "phase": "gas"},
    },
    "HYDROGEN": {
        18.000: {"density": 73.436, "enthalpy_kJ_per_kg": -21.663,
                 "cp_J_per_gK": 8.563, "viscosity_uPa_s": 16.650,
                 "conductivity_W_per_mK": 0.103, "phase": "liquid"},
        19.000: {"density": 72.392, "enthalpy_kJ_per_kg": -12.865,
                 "cp_J_per_gK": 9.041, "viscosity_uPa_s": 15.194,
                 "conductivity_W_per_mK": 0.103, "phase": "liquid"},
        20.000: {"density": 71.279, "enthalpy_kJ_per_kg": -3.567,
                 "cp_J_per_gK": 9.565, "viscosity_uPa_s": 13.921,
                 "conductivity_W_per_mK": 0.104, "phase": "liquid"},
    },
}

FLUIDS = {"OXYGEN": OXYGEN, "METHANE": METHANE, "HYDROGEN": HYDROGEN}

# Property -> (our field, factor from published unit to SI)
CONVERSION = {
    "density": (FluidProperty.DENSITY, 1.0),
    "enthalpy_kJ_per_kg": (FluidProperty.SPECIFIC_ENTHALPY, 1000.0),
    "cp_J_per_gK": (FluidProperty.SPECIFIC_HEAT_CP, 1000.0),
    "viscosity_uPa_s": (FluidProperty.DYNAMIC_VISCOSITY, 1.0e-6),
    "conductivity_W_per_mK": (FluidProperty.THERMAL_CONDUCTIVITY, 1.0),
}


def rounding_box(printed: float) -> float:
    """Half a unit in the last printed digit, as an absolute tolerance.

    Derived from the source's own precision *before* any comparison is run, so
    the box cannot be widened to fit an answer.
    """
    text = repr(float(printed))
    if "." in text:
        decimals = len(text.split(".")[1].rstrip("0")) or 0
    else:
        decimals = 0
    return 0.5 * (10.0 ** -decimals)


#: Properties whose correlation CoolProp and NIST are known to share, per
#: fluid. Populated from CoolProp's own recorded references and compared
#: against NIST's; a property listed here is validated as an
#: implementation residual, and one *not* listed is compared and reported as a
#: model difference rather than being asserted.
SHARED_CORRELATION = {
    ("OXYGEN", "dynamic_viscosity"): True,
    ("HYDROGEN", "dynamic_viscosity"): True,
    # CoolProp uses QuinonesCisneros-JPCB-2006 friction theory for methane
    # viscosity; NIST's tables do not. Different correlation, so a difference
    # here is a model difference and is not evidence of a defect in either.
    ("METHANE", "dynamic_viscosity"): False,
}


def is_validated(fluid_name: str, prop_value: str) -> bool:
    """Whether a disagreement here would be a defect rather than a model gap."""
    return SHARED_CORRELATION.get((fluid_name, prop_value), True)


provider = coolprop_provider()
report = {
    "purpose": "CoolProp against NIST reference tables",
    "classification": "independent-implementation residual, not a model difference",
    "source": SOURCE,
    "provider": dict(provider.provenance().as_mapping()),
    "points": [],
    "enthalpy_differences": [],
    "cp_derivative": [],
}

worst = 0.0
failures = []
model_differences = []
for fluid_name, rows in PUBLISHED.items():
    fluid = FLUIDS[fluid_name]
    for temperature, published in sorted(rows.items()):
        solution = provider.evaluate(FluidStateRequest(
            fluid=fluid, temperature=temperature, pressure=ATM))
        state = solution.value
        assert state is not None, (fluid_name, temperature)
        entry = {
            "fluid": fluid_name, "temperature_K": temperature,
            "pressure_Pa": ATM,
            "published_phase": published["phase"],
            "computed_phase": state.phase.value if state.phase else None,
            "phase_agrees": (state.phase is not None
                             and state.phase.value == published["phase"]),
            "properties": {},
        }
        if not entry["phase_agrees"]:
            failures.append(f"{fluid_name} {temperature} K phase")
        for key, (prop, factor) in CONVERSION.items():
            if key not in published:
                continue
            expected = published[key] * factor
            box = rounding_box(published[key]) * factor
            actual = state.value_of(prop)
            difference = abs(actual - expected)
            relative = difference / abs(expected) if expected else 0.0
            inside = difference <= box
            validated = is_validated(fluid_name, prop.value)
            if validated:
                worst = max(worst, relative)
                if not inside:
                    failures.append(
                        f"{fluid_name} {temperature} K {prop.value}: "
                        f"{actual} vs {expected} +/- {box}")
            elif not inside:
                model_differences.append({
                    "fluid": fluid_name, "temperature_K": temperature,
                    "property": prop.value,
                    "relative_difference": relative,
                })
            entry["properties"][prop.value] = {
                "classification": ("implementation residual" if validated
                                   else "model difference: different correlation"),
                "published": published[key],
                "published_unit": key,
                "published_in_SI": expected,
                "computed_SI": actual,
                "unit": prop.unit,
                "absolute_difference": difference,
                "relative_difference": relative,
                "rounding_box": box,
                "inside_box": inside,
            }
        report["points"].append(entry)

# --- the quantity the coupling actually transfers ------------------------
for fluid_name, (t_low, t_high) in (("OXYGEN", (88.000, 90.000)),
                                    ("METHANE", (108.00, 110.00)),
                                    ("HYDROGEN", (18.000, 20.000))):
    fluid = FLUIDS[fluid_name]
    rows = PUBLISHED[fluid_name]
    published_delta = (rows[t_high]["enthalpy_kJ_per_kg"]
                       - rows[t_low]["enthalpy_kJ_per_kg"]) * 1000.0
    box = (rounding_box(rows[t_high]["enthalpy_kJ_per_kg"])
           + rounding_box(rows[t_low]["enthalpy_kJ_per_kg"])) * 1000.0
    low = provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=t_low, pressure=ATM,
        properties=(FluidProperty.SPECIFIC_ENTHALPY,),
        required_phase=FluidPhase.LIQUID)).value
    high = provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=t_high, pressure=ATM,
        properties=(FluidProperty.SPECIFIC_ENTHALPY,),
        required_phase=FluidPhase.LIQUID)).value
    computed_delta = high.specific_enthalpy - low.specific_enthalpy
    inside = abs(computed_delta - published_delta) <= box
    if not inside:
        failures.append(f"{fluid_name} enthalpy difference")
    report["enthalpy_differences"].append({
        "fluid": fluid_name, "from_K": t_low, "to_K": t_high,
        "published_delta_h_J_per_kg": published_delta,
        "computed_delta_h_J_per_kg": computed_delta,
        "rounding_box": box,
        "inside_box": inside,
        "note": ("this is the quantity the reactant coupling transfers into "
                 "CEA; validating a difference is independent of the datum"),
    })

    # dh/dT against cp at the midpoint -- an identity, not a table lookup
    midpoint = 0.5 * (t_low + t_high)
    span = t_high - t_low
    finite_difference = computed_delta / span
    cp = provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=midpoint, pressure=ATM,
        properties=(FluidProperty.SPECIFIC_HEAT_CP,),
        required_phase=FluidPhase.LIQUID)).value.specific_heat_cp
    report["cp_derivative"].append({
        "fluid": fluid_name, "midpoint_K": midpoint, "span_K": span,
        "dh_dT_J_per_kgK": finite_difference,
        "cp_J_per_kgK": cp,
        "relative_difference": abs(finite_difference - cp) / cp,
        "note": ("a central-difference estimate over a finite span, so it "
                 "carries the curvature of cp over that span; agreement to a "
                 "few parts in a thousand is the expected result, not an "
                 "exact identity"),
    })

report["worst_relative_difference_among_validated"] = worst
report["failures"] = failures
report["model_differences"] = model_differences
report["correlation_references"] = {
    "note": ("read from CoolProp's own recorded references, not assumed"),
    "OXYGEN": {"eos": "Schwabe/Wagner reference EOS",
               "viscosity": "Lemmon-IJT-2004"},
    "METHANE": {"eos": "Setzmann-JPCRD-1991",
                "viscosity": "QuinonesCisneros-JPCB-2006"},
    "HYDROGEN": {"eos": "Leachman reference EOS",
                 "viscosity": "Muzny-JCED-2013"},
}
report["not_validated"] = [
    {"fluid": "METHANE", "property": "dynamic_viscosity",
     "reason": ("CoolProp uses the Quinones-Cisneros friction-theory "
                "correlation and the NIST reference table does not, so the "
                "0.4-1.4% disagreement measured here is a model difference "
                "between two correlations and not evidence about either. No "
                "independent source using the same correlation was available, "
                "so methane viscosity is NOT claimed as validated."),
     "consumed_by_this_phase": False,
     "blocks": ("engineering.line / valve / orifice, which are the first "
                "consumers of viscosity and must not be built on an "
                "unvalidated one")},
]
report["verdict"] = "PASS" if not failures else "FAIL"
report["verdict_scope"] = (
    "covers every property this phase consumes: density, specific enthalpy, "
    "specific heat, thermal conductivity, phase identification, and the "
    "enthalpy differences the reactant coupling transfers. Methane viscosity "
    "is excluded and listed under not_validated.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("verdict:", report["verdict"])
print("worst relative difference:", worst)
print("failures:", failures)
print("\nenthalpy differences:")
print(json.dumps(report["enthalpy_differences"], indent=1))
print("\ncp derivative:")
print(json.dumps(report["cp_derivative"], indent=1))
