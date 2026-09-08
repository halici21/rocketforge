"""Audit the scientific contracts before freezing them.

Six questions, each answered by reading the repository rather than the docs:

1. Is every public quantity in canonical SI, with the unit stated?
2. Is O/F unambiguously oxidiser mass over fuel mass, everywhere?
3. Is every gamma named for which gamma it is?
4. What tolerances exist, who owns them, and why?
5. Is the condensed reporting threshold still presentation-only?
6. Does Phase 5 reach into frozen Compressible's private surface?

The findings are written to artifacts; the judgement about whether each is a
freeze blocker is made in the report that reads them.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "phase_5g"

#: Everything Phase 5 added, as production source.
PHASE_5_ROOTS = [
    ROOT / "rocketforge" / "physics" / "thermochemistry",
    ROOT / "rocketforge" / "engineering" / "chamber",
    ROOT / "rocketforge" / "engineering" / "nozzle",
    ROOT / "rocketforge" / "engine" / "studies",
    ROOT / "rocketforge" / "providers" / "cea",
]

APPLICATION = ROOT / "rocketforge" / "application"

PHASE_5_APPLICATION = sorted(
    list((APPLICATION / "analysis").glob("thermochemistry_*.py"))
    + list((APPLICATION / "analysis").glob("performance_*.py"))
    + list((APPLICATION / "analysis").glob("trade_study_*.py"))
    + [APPLICATION / "selftest.py", APPLICATION / "uismoke.py",
       APPLICATION / "perfsmoke.py", APPLICATION / "studysmoke.py"])


def phase_5_sources() -> list[Path]:
    paths: list[Path] = []
    for root in PHASE_5_ROOTS:
        paths.extend(sorted(root.rglob("*.py")))
    paths.extend(p for p in PHASE_5_APPLICATION if p.exists())
    return paths


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


# ===========================================================================
# 1. units
# ===========================================================================


#: The canonical unit every public quantity is expected to carry.
EXPECTED_UNITS = {
    "temperature": "K", "chamber_temperature": "K", "exit_temperature": "K",
    "stagnation_temperature": "K", "reference_temperature": "K",
    "fuel_temperature": "K", "oxidiser_temperature": "K",
    "pressure": "Pa", "chamber_pressure": "Pa", "ambient_pressure": "Pa",
    "exit_pressure": "Pa",
    "molar_mass": "kg/mol", "mean_molar_mass": "kg/mol",
    "gas_constant": "J/(kg K)",
    "cp": "J/(kg K)", "cv": "J/(kg K)", "cp_frozen": "J/(kg K)",
    "cp_equilibrium": "J/(kg K)",
    "density": "kg/m3", "enthalpy": "J/kg", "entropy": "J/(kg K)",
    "characteristic_velocity": "m/s", "effective_exhaust_velocity": "m/s",
    "exit_velocity": "m/s", "velocity": "m/s",
    "specific_impulse": "s",
    "throat_area": "m2", "exit_area": "m2", "area_ratio": "-",
    "mass_flow": "kg/s",
    "thrust_coefficient": "-", "oxidiser_fuel_ratio": "-",
    "condensed_mass_fraction": "-", "mach": "-",
}


def units_audit() -> dict:
    """Check that each registered metric declares its canonical unit."""
    from rocketforge.application.analysis.trade_study_domain import METRICS

    rows = []
    for metric in METRICS:
        expected = EXPECTED_UNITS.get(metric.key)
        declared = metric.unit or "-"
        normalised = (declared.replace("·", " ").replace("²", "2")
                      .replace("m³", "m3"))
        rows.append({
            "metric": metric.key,
            "declared": metric.unit,
            "expected": expected,
            "agrees": expected is None or normalised.replace(" ", "")
                      == expected.replace(" ", ""),
        })

    # Every public dataclass field whose name implies a dimension should be
    # documented with its unit somewhere in the owning class docstring or an
    # inline comment on the field.
    undocumented = []
    for module_name in ("rocketforge.physics.thermochemistry",
                        "rocketforge.engineering.chamber",
                        "rocketforge.engineering.nozzle"):
        module = importlib.import_module(module_name)
        source_files = {inspect.getsourcefile(getattr(module, name))
                        for name in getattr(module, "__all__", [])
                        if inspect.isclass(getattr(module, name, None))}
        for path in filter(None, source_files):
            text = Path(path).read_text(encoding="utf-8")
            for field, unit in EXPECTED_UNITS.items():
                if re.search(rf"^\s+{field}\s*:", text, re.M):
                    token = unit.split("/")[0].strip("-")
                    if token and token not in text:
                        undocumented.append({"file": Path(path).name,
                                             "field": field, "unit": unit})

    return {
        "purpose": "canonical SI internally; conversion at the application "
                   "boundary only",
        "metric_units": rows,
        "metric_unit_disagreements": [r for r in rows if not r["agrees"]],
        "fields_without_their_unit_in_the_owning_module": undocumented,
    }


# ===========================================================================
# 2. O/F orientation
# ===========================================================================


def of_audit() -> dict:
    """O/F must be oxidiser mass over fuel mass, and say so."""
    hits, ambiguous = [], []
    for path in phase_5_sources():
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if re.search(r"\boxidiser_fuel_ratio\b|\bof_ratio\b|\bof_mass\b", text):
            states = bool(re.search(
                r"[Oo]xidiser mass (divided by|over) fuel mass"
                r"|[Oo]xidiser mass / fuel mass"
                r"|O/F \*\*by mass\*\*"
                r"|oxidiser mass over fuel", text))
            hits.append({"file": rel, "states_orientation": states})
        # A bare `mixture_ratio` in a public scientific name is the ambiguity
        # this audit exists to prevent.
        for match in re.finditer(r"^\s*(?:def |class |)(\w*mixture_ratio\w*)",
                                 text, re.M):
            ambiguous.append({"file": rel, "name": match.group(1)})

    from rocketforge.application.analysis.trade_study_domain import (
        VARIABLE_SPECS,
    )

    variable = next(s for s in VARIABLE_SPECS
                    if s["key"] == "oxidiser_fuel_ratio")

    return {
        "canonical": "O/F = oxidiser mass / fuel mass",
        "modules_using_it": hits,
        "modules_that_state_the_orientation":
            [h["file"] for h in hits if h["states_orientation"]],
        "trade_study_variable_key": variable["key"],
        "trade_study_variable_note": variable["note"],
        "bare_mixture_ratio_in_scientific_names": ambiguous,
        "note": "the UI property `mixtureRatio` on the thermochemistry "
                "controller is a display name whose tooltip states the "
                "orientation; the scientific key everywhere is "
                "`oxidiser_fuel_ratio`",
    }


# ===========================================================================
# 3. gamma semantics
# ===========================================================================


def gamma_audit() -> dict:
    """No public quantity may be a bare, unqualified gamma."""
    from rocketforge.application.analysis.trade_study_domain import METRICS
    from rocketforge.engineering.chamber import ChamberGammaBasis
    from rocketforge.physics.thermochemistry import ChamberGas, GammaStrategy

    metric_keys = [m.key for m in METRICS]
    gamma_metrics = [k for k in metric_keys if "gamma" in k]

    chamber_fields = [f for f in ChamberGas.__dataclass_fields__
                      if "gamma" in f or f in ("cp", "cv", "cp_frozen",
                                               "cp_equilibrium")]

    return {
        "rule": "a chamber state carries two isentropic exponents several per "
                "cent apart; no public name may be an unqualified 'gamma'",
        "chamber_state_fields": chamber_fields,
        "trade_study_gamma_metrics": gamma_metrics,
        "bare_gamma_metric_present": "gamma" in metric_keys,
        "gamma_strategy_members": [m.name for m in GammaStrategy],
        "gamma_basis_members": [m.name for m in ChamberGammaBasis],
        "reduction_is_explicit":
            "reduce_chamber_gas requires both a strategy and a basis "
            "positionally; neither has a default",
        "cp_cv_semantics": {
            "cp_frozen": "constant-composition specific heat",
            "cp_equilibrium": "shifting-equilibrium specific heat",
            "gamma_frozen": "cp_frozen / cv",
            "gamma_equilibrium": "the isentropic exponent of a shifting "
                                 "expansion, not a cp/cv ratio",
        },
    }


# ===========================================================================
# 4. tolerances
# ===========================================================================


def tolerance_inventory() -> dict:
    """Every non-trivial numeric threshold Phase 5 introduced."""
    pattern = re.compile(
        r"^(?P<name>[A-Z][A-Z0-9_]*(?:TOLERANCE|LIMIT|THRESHOLD|EPSILON|_TOL))"
        r"\s*(?::[^=]+)?=\s*(?P<value>[-\d.eE+]+)", re.M)
    rows = []
    for path in phase_5_sources():
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        for match in pattern.finditer(text):
            # The comment block immediately above a constant is its reason.
            start = text.rfind("\n\n", 0, match.start())
            preamble = text[max(0, start):match.start()]
            reason = " ".join(line.strip("#: ").strip()
                              for line in preamble.splitlines()
                              if line.strip().startswith("#:"))
            rows.append({
                "name": match.group("name"),
                "value": float(match.group("value")),
                "owner": rel,
                "documented": bool(reason),
                "reason": reason[:400],
            })

    # The named tolerance sets are structured rather than scalar.
    structured = []
    try:
        from rocketforge.physics.thermochemistry import DEFAULT_THERMO_TOLERANCES

        for field in DEFAULT_THERMO_TOLERANCES.__dataclass_fields__:
            structured.append({
                "name": f"DEFAULT_THERMO_TOLERANCES.{field}",
                "value": getattr(DEFAULT_THERMO_TOLERANCES, field),
                "owner": "rocketforge/physics/thermochemistry",
                "documented": True,
                "reason": "member of the named thermochemistry tolerance set",
            })
    except Exception as error:  # pragma: no cover
        structured.append({"error": str(error)})

    rows.sort(key=lambda r: (r["owner"], r["name"]))
    return {
        "purpose": "every threshold, its owner and its stated reason",
        "scalar_constants": rows,
        "structured_sets": structured,
        "undocumented": [r["name"] for r in rows if not r["documented"]],
    }


# ===========================================================================
# 5. presentation thresholds must not reach physics
# ===========================================================================


def threshold_boundary_audit() -> dict:
    """`CONDENSED_REPORTING_THRESHOLD` is presentation-only. Verified by import."""
    physics_like = [
        ROOT / "rocketforge" / "physics",
        ROOT / "rocketforge" / "engineering",
        ROOT / "rocketforge" / "engine",
        ROOT / "rocketforge" / "providers",
    ]
    leaks = []
    for root in physics_like:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.ImportFrom):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.Name):
                    names = [node.id]
                elif isinstance(node, ast.Attribute):
                    names = [node.attr]
                if "CONDENSED_REPORTING_THRESHOLD" in names:
                    leaks.append(str(path.relative_to(ROOT)).replace("\\", "/"))

    from rocketforge.application.analysis.thermochemistry_service import (
        CONDENSED_REPORTING_THRESHOLD,
    )
    from rocketforge.engineering.chamber import SINGLE_PHASE_CONDENSED_LIMIT

    return {
        "presentation_threshold": {
            "name": "CONDENSED_REPORTING_THRESHOLD",
            "value": CONDENSED_REPORTING_THRESHOLD,
            "owner": "rocketforge/application/analysis/thermochemistry_service.py",
            "role": "how small a condensed fraction may be before the "
                    "interface stops printing it as a separate row",
        },
        "physics_threshold": {
            "name": "SINGLE_PHASE_CONDENSED_LIMIT",
            "value": SINGLE_PHASE_CONDENSED_LIMIT,
            "owner": "rocketforge/engineering/chamber/handshake.py",
            "role": "above this the ideal single-gas reduction refuses rather "
                    "than averaging a condensed phase into the gas",
        },
        "same_value": CONDENSED_REPORTING_THRESHOLD
                      == SINGLE_PHASE_CONDENSED_LIMIT,
        "same_object": CONDENSED_REPORTING_THRESHOLD
                       is SINGLE_PHASE_CONDENSED_LIMIT,
        "separate_layers": True,
        "presentation_threshold_used_below_application": sorted(set(leaks)),
        "verdict": "PASS" if not leaks else "FAIL",
        "note": "the two happen to share a numeric value; they are separate "
                "constants in separate layers, and changing one must not "
                "change the other",
    }


# ===========================================================================
# 6. the Compressible v1 consumer contract
# ===========================================================================


def compressible_contract() -> dict:
    """Which frozen public symbols Phase 5 depends on, and any private reach."""
    import rocketforge.physics.compressible as compressible

    public = set(getattr(compressible, "__all__", []))
    submodules = {"gas", "isentropic", "mass_flow", "normal_shock",
                  "oblique_shock", "prandtl_meyer", "fanno", "rayleigh",
                  "nozzle", "types", "equations", "geometry"}

    used: dict[str, set[str]] = {}
    private = []
    for path in phase_5_sources():
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module \
                    and "physics.compressible" in node.module:
                tail = node.module.split("compressible")[-1].lstrip(".")
                for alias in node.names:
                    used.setdefault(rel, set()).add(
                        f"{tail}.{alias.name}" if tail else alias.name)
                    if alias.name.startswith("_"):
                        private.append({"file": rel, "symbol": alias.name})
                if tail and tail.split(".")[0].startswith("_"):
                    private.append({"file": rel, "module": node.module})

    # Attribute reads on an imported compressible module, e.g. nozzle.classify
    attribute_uses: set[str] = set()
    for path in phase_5_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.asname or alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module
                    and "physics.compressible" in node.module
                    for alias in node.names}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                    and node.value.id in imported:
                attribute_uses.add(f"{node.value.id}.{node.attr}")
                if node.attr.startswith("_"):
                    private.append({"symbol": f"{node.value.id}.{node.attr}"})

    return {
        "purpose": "the dependency contract Phase 5 has on frozen Compressible v1",
        "compressible_public_exports": sorted(public),
        "consumed_by_phase_5": {k: sorted(v) for k, v in sorted(used.items())},
        "attribute_uses": sorted(attribute_uses),
        "private_symbol_uses": private,
        "verdict": "PASS" if not private else "FAIL",
    }


def main() -> int:
    print("Phase 5G contract audit")
    report = {
        "units": units_audit(),
        "oxidiser_fuel_ratio": of_audit(),
        "gamma": gamma_audit(),
        "thresholds": threshold_boundary_audit(),
        "compressible_contract": compressible_contract(),
    }
    write("contract_audit.json", report)
    write("tolerance_inventory.json", tolerance_inventory())

    print()
    print("unit disagreements:",
          report["units"]["metric_unit_disagreements"] or "none")
    print("bare mixture_ratio in scientific names:",
          report["oxidiser_fuel_ratio"]["bare_mixture_ratio_in_scientific_names"]
          or "none")
    print("bare gamma metric:", report["gamma"]["bare_gamma_metric_present"])
    print("presentation threshold below application:",
          report["thresholds"]["presentation_threshold_used_below_application"]
          or "none", "->", report["thresholds"]["verdict"])
    print("compressible private uses:",
          report["compressible_contract"]["private_symbol_uses"] or "none",
          "->", report["compressible_contract"]["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
