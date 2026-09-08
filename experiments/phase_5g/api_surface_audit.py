"""Inventory every public symbol of the Phase 5 propulsion-analysis packages.

The freeze boundary cannot be drawn from a prompt; it has to be read off the
repository. This walks each candidate package, records what it exports, what
kind of object each export is, and where it was defined -- so that an export
which arrived by accident (a re-exported stdlib name, a helper that leaked
through a star import) is visible as such rather than frozen forever by
inheritance.

Classification is deliberately mechanical here. The judgement calls live in the
report that consumes this, not in the collector.
"""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: The packages whose public surface is a freeze candidate.
#:
#: The application and UI layers are deliberately absent: they are the
#: composition root and the presentation, and freezing a controller property
#: would freeze a view decision as though it were a scientific contract.
CANDIDATES = [
    ("thermochemistry", "rocketforge.physics.thermochemistry"),
    ("performance.chamber", "rocketforge.engineering.chamber"),
    ("performance.nozzle", "rocketforge.engineering.nozzle"),
    ("trade_study", "rocketforge.engine.studies"),
    ("provider.cea", "rocketforge.providers.cea"),
]

#: Modules whose symbols are legitimately re-exported by a candidate.
OWN_PREFIXES = ("rocketforge.",)


def kind_of(value) -> str:
    if inspect.isclass(value):
        if issubclass(value, Enum):
            return "enum"
        if is_dataclass(value):
            return "dataclass"
        if issubclass(value, BaseException):
            return "exception"
        return "class"
    if inspect.isfunction(value) or inspect.isbuiltin(value):
        return "function"
    if isinstance(value, (int, float, str, bool, tuple, frozenset)):
        return "constant"
    if isinstance(value, (dict, list, set)):
        return "mutable-constant"
    return type(value).__name__


def describe(name: str, value) -> dict:
    entry: dict = {"name": name, "kind": kind_of(value)}
    module = getattr(value, "__module__", None)
    if module:
        entry["defined_in"] = module
        entry["foreign"] = not module.startswith(OWN_PREFIXES)
    else:
        entry["defined_in"] = None
        entry["foreign"] = False

    if entry["kind"] == "enum":
        entry["members"] = [member.name for member in value]
        entry["values"] = [getattr(member, "value", None) for member in value]
    elif entry["kind"] == "dataclass":
        entry["frozen"] = bool(getattr(value, "__dataclass_params__").frozen)
        entry["slots"] = "__slots__" in vars(value)
        entry["fields"] = [{"name": f.name,
                            "type": str(f.type),
                            "has_default": (f.default is not f.default_factory
                                            or f.default_factory is not None)
                            if False else
                            (repr(f.default) != "<dataclasses._MISSING_TYPE>"
                             or repr(f.default_factory)
                             != "<class 'dataclasses._MISSING_TYPE'>")}
                           for f in fields(value)]
    elif entry["kind"] == "function":
        try:
            entry["signature"] = str(inspect.signature(value))
        except (TypeError, ValueError):  # pragma: no cover - builtins
            entry["signature"] = None
    elif entry["kind"] == "constant":
        entry["value"] = (list(value) if isinstance(value, (tuple, frozenset))
                          else value)

    doc = inspect.getdoc(value)
    entry["documented"] = bool(doc)
    entry["summary"] = doc.splitlines()[0] if doc else ""
    return entry


def audit(label: str, module_name: str) -> dict:
    module = importlib.import_module(module_name)
    declared = list(getattr(module, "__all__", []))

    # Everything importable that is not private, whether or not __all__ lists
    # it. An export reachable by `from x import y` is part of the surface a
    # consumer can depend on, and pretending otherwise is how a helper becomes
    # permanent by accident.
    reachable = sorted(name for name in vars(module)
                       if not name.startswith("_"))

    entries = []
    for name in sorted(set(declared) | set(reachable)):
        value = getattr(module, name, None)
        if value is None and name not in vars(module):
            entries.append({"name": name, "kind": "MISSING",
                            "in_all": name in declared, "reachable": False})
            continue
        entry = describe(name, value)
        entry["in_all"] = name in declared
        entry["reachable"] = name in reachable
        entries.append(entry)

    undeclared = [e["name"] for e in entries
                  if e["reachable"] and not e["in_all"]]
    foreign = [e["name"] for e in entries if e.get("foreign")]
    undocumented = [e["name"] for e in entries
                    if e.get("kind") not in ("constant", "MISSING")
                    and not e.get("documented")]
    mutable = [e["name"] for e in entries
               if e.get("kind") == "mutable-constant"]
    unfrozen = [e["name"] for e in entries
                if e.get("kind") == "dataclass" and not e.get("frozen")]

    return {
        "label": label,
        "module": module_name,
        "declared_in_all": len(declared),
        "reachable_public": len(reachable),
        "entries": entries,
        "findings": {
            "reachable_but_not_in_all": undeclared,
            "defined_outside_rocketforge": foreign,
            "undocumented": undocumented,
            "mutable_module_level_containers": mutable,
            "unfrozen_dataclasses": unfrozen,
        },
    }


def main() -> int:
    report = {
        "purpose": "the public surface of every Phase 5 freeze candidate",
        "python": sys.version.split()[0],
        "packages": [audit(label, module) for label, module in CANDIDATES],
    }

    totals = {
        "packages": len(report["packages"]),
        "declared": sum(p["declared_in_all"] for p in report["packages"]),
        "reachable": sum(p["reachable_public"] for p in report["packages"]),
    }
    for key in ("reachable_but_not_in_all", "defined_outside_rocketforge",
                "undocumented", "mutable_module_level_containers",
                "unfrozen_dataclasses"):
        totals[key] = sum(len(p["findings"][key]) for p in report["packages"])
    report["totals"] = totals

    out = ROOT / "acceptance" / "phase_5g" / "api_surface_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"{'package':22s} {'__all__':>8} {'reachable':>10} {'extra':>6} "
          f"{'foreign':>8} {'undoc':>6} {'mutable':>8} {'unfrozen':>9}")
    for p in report["packages"]:
        f = p["findings"]
        print(f"{p['label']:22s} {p['declared_in_all']:>8} "
              f"{p['reachable_public']:>10} "
              f"{len(f['reachable_but_not_in_all']):>6} "
              f"{len(f['defined_outside_rocketforge']):>8} "
              f"{len(f['undocumented']):>6} "
              f"{len(f['mutable_module_level_containers']):>8} "
              f"{len(f['unfrozen_dataclasses']):>9}")
    print()
    for p in report["packages"]:
        f = p["findings"]
        for key, values in f.items():
            if values:
                print(f"{p['label']} — {key}: {values}")
    print(f"\n-> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
