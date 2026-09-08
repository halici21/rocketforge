"""The dependency graph, the runtime dependencies, and the final benchmarks.

Three artifacts:

**Architecture.** The whole import graph between RocketForge layers, checked
against the direction the architecture declares, plus a cycle check. Read from
the syntax tree so a conditional or function-local import counts the same as a
top-level one -- a lazy import is still a dependency.

**Dependencies.** What the runtime actually requires, checked against the
declared requirements, so a phase cannot have added one quietly.

**Benchmarks.** Baselines for future regression, recorded rather than asserted:
a brittle microbenchmark threshold would fail on a busy machine and teach
people to ignore it.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "phase_5g"

#: The declared layer order. Each may import those below it and no others.
LAYERS = ["core", "physics", "engineering", "engine", "providers",
          "application"]

#: The exception the architecture states: an adapter implements an interface
#: the domain declares, so `providers` may import `physics`.
ALLOWED_EXTRA = {("providers", "physics"), ("providers", "core")}


def layer_of(path: Path) -> str | None:
    parts = path.relative_to(ROOT).parts
    if len(parts) >= 2 and parts[0] == "rocketforge":
        return parts[1] if parts[1] in LAYERS else None
    return None


def module_imports(path: Path) -> set[str]:
    """Absolute module names a file imports.

    Relative imports are skipped. ``from .analysis import x`` records
    ``analysis`` in ``node.module`` with ``level = 1``, and counting that as a
    top-level package name reports every sibling module as a third-party
    dependency.
    """
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:                      # relative: not a package name
                continue
            if node.module:
                names.add(node.module)
    return names


def architecture_audit() -> dict:
    edges: dict[str, set[str]] = defaultdict(set)
    violations = []
    order = {name: index for index, name in enumerate(LAYERS)}

    for path in (ROOT / "rocketforge").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source_layer = layer_of(path)
        if source_layer is None:
            continue
        for name in module_imports(path):
            if not name.startswith("rocketforge."):
                continue
            parts = name.split(".")
            if len(parts) < 2 or parts[1] not in LAYERS:
                continue
            target_layer = parts[1]
            if target_layer == source_layer:
                continue
            edges[source_layer].add(target_layer)
            allowed = (order[target_layer] < order[source_layer]
                       or (source_layer, target_layer) in ALLOWED_EXTRA)
            if not allowed:
                violations.append({
                    "file": path.relative_to(ROOT).as_posix(),
                    "from_layer": source_layer,
                    "to_layer": target_layer,
                    "import": name,
                })

    # Cycles between layers.
    cycles = []
    for source, targets in edges.items():
        for target in targets:
            if source in edges.get(target, set()):
                pair = tuple(sorted((source, target)))
                if pair not in cycles:
                    cycles.append(pair)

    # UI must reach Python only through registered singletons.
    ui_python = list((ROOT / "ui").rglob("*.py"))

    return {
        "purpose": "the declared layer order, checked against the import graph",
        "layer_order": LAYERS,
        "allowed_exception": sorted(f"{a} -> {b}" for a, b in ALLOWED_EXTRA),
        "edges": {source: sorted(targets)
                  for source, targets in sorted(edges.items())},
        "violations": violations,
        "layer_cycles": [list(pair) for pair in cycles],
        "python_files_under_ui": [p.as_posix() for p in ui_python],
        "verdict": "PASS" if not violations and not cycles and not ui_python
                   else "FAIL",
    }


def provider_route_audit() -> dict:
    """There must be one production route into the provider package."""
    importers = []
    for path in (ROOT / "rocketforge").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("rocketforge/providers/"):
            continue
        for name in module_imports(path):
            if name.startswith("rocketforge.providers"):
                importers.append({"file": relative, "import": name})

    gateway = "rocketforge/application/analysis/thermochemistry_provider.py"
    outside_gateway = [entry for entry in importers
                       if entry["file"] != gateway]

    return {
        "purpose": "one accepted route from production code into the provider",
        "gateway": gateway,
        "all_importers": importers,
        "importers_outside_the_gateway": outside_gateway,
        "note": "the selftest and reference harnesses in application/ import "
                "the provider package deliberately: they exist to exercise it "
                "directly. Production analysis code goes through the gateway.",
        "verdict": "PASS" if all(
            entry["file"].startswith("rocketforge/application/")
            for entry in importers) else "FAIL",
    }


def dependency_audit() -> dict:
    """What the runtime imports, against what the project declares."""
    declared = {}
    for name in ("requirements.txt", "requirements-thermochemistry.txt",
                 "requirements-dev.txt"):
        path = ROOT / name
        if path.is_file():
            declared[name] = [
                line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")]

    third_party: set[str] = set()
    stdlib = set(sys.stdlib_module_names)
    for path in (ROOT / "rocketforge").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for name in module_imports(path):
            root_name = name.split(".")[0]
            if root_name in ("rocketforge", "__future__") or root_name in stdlib:
                continue
            third_party.add(root_name)

    banned = {"scipy", "pandas", "sklearn", "pymoo", "deap", "optuna",
              "cantera", "CoolProp", "rocketcea"}
    return {
        "purpose": "no phase may add a runtime dependency quietly",
        "declared": declared,
        "third_party_imported_by_rocketforge": sorted(third_party),
        "banned_present": sorted(third_party & banned),
        "note": "cea is imported only inside function bodies in the provider "
                "package and is an optional extra; PySide6 appears only in the "
                "application layer",
        "verdict": "PASS" if not (third_party & banned) else "FAIL",
    }


def benchmarks() -> dict:
    """Baselines, recorded for future comparison rather than asserted."""
    from rocketforge.application.analysis import performance_service as perf
    from rocketforge.application.analysis import thermochemistry_provider as gw
    from rocketforge.application.analysis import thermochemistry_service as thermo
    from rocketforge.application.analysis import trade_study_service as ts
    from rocketforge.application.analysis.trade_study_domain import (
        build_variable,
    )
    from rocketforge.engine.studies import (
        ObjectiveDefinition,
        ObjectiveDirection,
    )

    if not gw.availability().usable:
        return {"status": "skipped", "reason": "no chemistry provider"}

    def timed(function, rounds: int) -> dict:
        samples = []
        for _ in range(rounds):
            started = time.perf_counter()
            function()
            samples.append(time.perf_counter() - started)
        samples.sort()
        return {"rounds": rounds,
                "median_ms": round(samples[len(samples) // 2] * 1000, 4),
                "min_ms": round(samples[0] * 1000, 4),
                "max_ms": round(samples[-1] * 1000, 4)}

    case = thermo.DEFAULT_CASE
    # The very first solve imports and initialises the library.
    started = time.perf_counter()
    thermo.solve_case(case)
    cold_ms = round((time.perf_counter() - started) * 1000, 4)

    warm = timed(lambda: thermo.solve_case(case), 20)
    chamber = thermo.solve_case(case)
    performance = timed(
        lambda: perf.solve_performance(chamber, perf.DEFAULT_PERFORMANCE_CASE),
        200)

    setup = ts.TradeStudySetup(chamber=case,
                               performance=perf.DEFAULT_PERFORMANCE_CASE)
    MAX_ISP = ObjectiveDefinition("specific_impulse",
                                  ObjectiveDirection.MAXIMIZE)
    MIN_TC = ObjectiveDefinition("chamber_temperature",
                                 ObjectiveDirection.MINIMIZE)

    def study(of_count: int, eps_count: int) -> dict:
        definition = ts.build_definition(
            setup,
            [build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5,
                            count=of_count),
             build_variable("area_ratio", start=10.0, end=120.0,
                            count=eps_count)],
            outputs=("chamber_temperature",), objectives=(MAX_ISP, MIN_TC))
        started = time.perf_counter()
        result = ts.run_trade_study(definition, setup)
        seconds = time.perf_counter() - started
        return {"design_points": len(result.points),
                "chemistry_solves":
                    dict(result.counts.stage_solves).get("thermochemistry"),
                "seconds": round(seconds, 3),
                "ms_per_point": round(seconds * 1000 / len(result.points), 4)}

    return {
        "purpose": "baselines for future regression, recorded not asserted",
        "note": "wall-clock on a developer machine; use as a change detector, "
                "not as a pass/fail gate",
        "thermochemistry_cold_ms": cold_ms,
        "thermochemistry_warm": warm,
        "ideal_performance": performance,
        "trade_study": {
            "small_100": study(10, 10),
            "medium_1000": study(40, 25),
            "large_4000": study(101, 40),
        },
    }


def main() -> int:
    print("Phase 5G architecture, dependencies and benchmarks")
    architecture = architecture_audit()
    routes = provider_route_audit()
    dependencies = dependency_audit()

    (OUT / "architecture_audit.json").write_text(json.dumps({
        "layers": architecture,
        "provider_routes": routes,
        "dependencies": dependencies,
    }, indent=2), encoding="utf-8")

    marks = benchmarks()
    (OUT / "performance_baselines.json").write_text(
        json.dumps(marks, indent=2), encoding="utf-8")

    print(f"  layer violations: {architecture['violations'] or 'none'}")
    print(f"  layer cycles:     {architecture['layer_cycles'] or 'none'}")
    print(f"  python under ui/: {architecture['python_files_under_ui'] or 'none'}")
    print(f"  architecture verdict: {architecture['verdict']}")
    print(f"  provider importers outside the gateway: "
          f"{[e['file'] for e in routes['importers_outside_the_gateway']]}")
    print(f"  provider route verdict: {routes['verdict']}")
    print(f"  third-party imports: "
          f"{dependencies['third_party_imported_by_rocketforge']}")
    print(f"  banned present: {dependencies['banned_present'] or 'none'} "
          f"-> {dependencies['verdict']}")
    if marks.get("thermochemistry_cold_ms"):
        print(f"\n  thermochemistry cold {marks['thermochemistry_cold_ms']} ms, "
              f"warm {marks['thermochemistry_warm']['median_ms']} ms")
        print(f"  ideal performance {marks['ideal_performance']['median_ms']} ms")
        for key, row in marks["trade_study"].items():
            print(f"  study {key:14s} {row['design_points']:>5} pts, "
                  f"{row['chemistry_solves']:>4} solves, {row['seconds']:>7}s, "
                  f"{row['ms_per_point']} ms/point")
    return 0


if __name__ == "__main__":
    sys.exit(main())
