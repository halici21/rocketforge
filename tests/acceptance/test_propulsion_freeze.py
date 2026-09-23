"""Phase 5G freeze rules: the public contracts, and the manifests over them.

Three groups of test:

**Manifest reproducibility.** The algorithm is reimplemented here from the
docstring in ``rocketforge.core.freeze`` alone, without calling that module's
helpers, and the two must agree. That is what makes the digest independently
reconstructible -- the property the Phase 4G manifest lacked, where per-file
hashes could be checked but the summary could not.

**Public contract.** Every symbol a downstream consumer is promised: its
existence, its kind, enum members, dataclass field names and order, immutability,
and the absence of accidental exports.

**Freeze boundary.** What is inside each manifest and what is deliberately
outside it.
"""

from __future__ import annotations

import ast
import getpass
import hashlib
import importlib
import inspect
import json
import pathlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from enum import Enum

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
#: The manifests are tracked here, beside the tests that check them: a fresh
#: clone and CI verify exactly what a developer's machine verifies. They used
#: to live in the untracked ``acceptance/`` evidence, where a missing manifest
#: silently skipped these tests everywhere but one machine.
FREEZE = ROOT / "tests" / "acceptance" / "freeze"
ACCEPTANCE = FREEZE / "phase_5g"
FLUIDS_ACCEPTANCE = FREEZE / "fluids_foundation"
LINE_ACCEPTANCE = FREEZE / "transport_line"
COMPRESSIBLE_ACCEPTANCE = FREEZE / "phase_4g"
MANIFEST_DIRECTORIES = (ACCEPTANCE, FLUIDS_ACCEPTANCE, LINE_ACCEPTANCE, COMPRESSIBLE_ACCEPTANCE)

#: Manifests that must still describe what is on disk.
#:
#: ``freeze_cea_provider_v1`` is deliberately absent. The fluids foundation
#: extended the CEA provider additively, so its source changed and its v1.0
#: digest no longer describes the source -- which is the freeze machinery
#: working. The v1.0 manifest is kept unmodified as the record of what Phase 5G
#: accepted, and is checked below as *history*; v1.1 is what must match now.
MANIFEST_STEMS = [
    "freeze_thermochemistry_api_v1",
    "freeze_rocket_performance_api_v1",
    "freeze_trade_study_api_v1",
    "freeze_cea_provider_v1_1",
    "freeze_fluid_properties_api_v1",
    "freeze_coolprop_provider_v1",
    "freeze_propellant_metrics_api_v1",
    "freeze_line_api_v1",
    "freeze_compressible_api_v1",
]

#: Superseded manifests: internally consistent, publicly recorded, and no
#: longer expected to match the working tree.
HISTORICAL_MANIFESTS = {
    "freeze_cea_provider_v1": "freeze_cea_provider_v1_1",
}


def load_manifest(stem: str) -> dict:
    for directory in MANIFEST_DIRECTORIES:
        path = directory / f"{stem}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    pytest.fail(f"{stem}.json is missing from {FREEZE.relative_to(ROOT).as_posix()}")


# ===========================================================================
# the manifest algorithm, reimplemented independently
# ===========================================================================


def independent_file_digest(data: bytes) -> str:
    """A file's digest, written from the stated algorithm alone: SHA-256 of the
    bytes with every CRLF replaced by LF, and nothing else changed."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def independent_digest(entries: list[tuple[str, str]]) -> str:
    """The overall digest, written from the stated algorithm alone.

    Deliberately does not import anything from ``rocketforge.core.freeze``.
    A test that called the implementation to compute its own expectation would
    check only that the code agrees with itself.

    From the docstring: sort relative POSIX paths lexicographically; one line
    per file as ``"<hex><two spaces><path>\\n"``; UTF-8; SHA-256 of those bytes.
    """
    text = "".join(f"{digest}  {path}\n"
                   for path, digest in sorted(entries, key=lambda e: e[0]))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("stem", MANIFEST_STEMS)
def test_the_recorded_digest_is_independently_reproducible(stem):
    """Re-hash every file and rebuild the digest without the freeze module."""
    manifest = load_manifest(stem)
    entries = []
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        assert path.is_file(), f"{entry['path']} is missing"
        actual = independent_file_digest(path.read_bytes())
        assert actual == entry["sha256"], (
            f"{entry['path']} changed since it was frozen")
        entries.append((entry["path"], actual))
    assert independent_digest(entries) == manifest["digest"]


@pytest.mark.parametrize("stem", MANIFEST_STEMS)
def test_the_sha256sum_text_matches_the_json_record(stem):
    """The checkable text and the JSON must describe the same thing."""
    manifest = load_manifest(stem)
    for directory in MANIFEST_DIRECTORIES:
        text_path = directory / f"{stem}.sha256"
        if text_path.is_file():
            break
    assert text_path.is_file()
    text = text_path.read_text(encoding="utf-8")
    expected = "".join(f"{e['sha256']}  {e['path']}\n"
                       for e in sorted(manifest["files"],
                                       key=lambda e: e["path"]))
    assert text == expected
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == manifest["digest"]


@pytest.mark.parametrize("stem", MANIFEST_STEMS)
def test_the_implementation_agrees_with_the_independent_reimplementation(stem):
    """Both routes to the digest, compared."""
    from rocketforge.core.freeze import FreezeManifest

    manifest = load_manifest(stem)
    rebuilt = FreezeManifest.from_dict(manifest)
    entries = [(e["path"], e["sha256"]) for e in manifest["files"]]
    assert rebuilt.digest == independent_digest(entries) == manifest["digest"]


def test_a_single_changed_byte_changes_both_hashes():
    """The mutation proof. Performed on a copy; production source is untouched.

    A manifest that could not detect a one-byte edit would be decoration.
    """
    import tempfile

    from rocketforge.core.freeze import build_manifest

    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        (root / "pkg").mkdir()
        target = root / "pkg" / "module.py"
        target.write_text("VALUE = 1.0\n", encoding="utf-8")
        other = root / "pkg" / "other.py"
        other.write_text("OTHER = 2.0\n", encoding="utf-8")

        before = build_manifest("demo", "1.0", root, [target, other])
        target.write_text("VALUE = 2.0\n", encoding="utf-8")
        after = build_manifest("demo", "1.0", root, [target, other])

        changed = {e.path: e.sha256 for e in after.files}
        original = {e.path: e.sha256 for e in before.files}
        assert changed["pkg/module.py"] != original["pkg/module.py"]
        assert changed["pkg/other.py"] == original["pkg/other.py"]
        assert after.digest != before.digest


def test_the_manifest_carries_no_machine_specific_text():
    """No absolute path, no timestamp, no user name."""
    user = getpass.getuser()
    for stem in MANIFEST_STEMS:
        manifest = load_manifest(stem)
        blob = json.dumps(manifest)
        assert "C:\\" not in blob and "/home/" not in blob and "/Users/" not in blob
        if len(user) >= 3:          # whoever runs this, on whatever machine
            assert user.lower() not in blob.lower(), "the manifest names a user"
        for entry in manifest["files"]:
            assert not entry["path"].startswith("/")
            assert "\\" not in entry["path"]
        assert "generated" not in manifest
        assert "timestamp" not in blob


def test_the_algorithm_is_versioned():
    from rocketforge.core.freeze import MANIFEST_ALGORITHM

    for directory in (ACCEPTANCE, FLUIDS_ACCEPTANCE, LINE_ACCEPTANCE):
        payload = json.loads((directory / "freeze_manifest.json").read_text(encoding="utf-8"))
        assert payload["algorithm"] == MANIFEST_ALGORITHM
    payload = json.loads((ACCEPTANCE / "freeze_manifest.json").read_text(encoding="utf-8"))
    assert len(payload["algorithm_description"]) >= 7
    assert "CRLF" in payload["algorithm_description"][3]


# ===========================================================================
# the freeze boundary
# ===========================================================================


def test_no_manifest_freezes_a_test_a_harness_or_an_interface_file():
    """Freezing those would make an ordinary improvement a contract break."""
    for stem in MANIFEST_STEMS:
        for entry in load_manifest(stem)["files"]:
            path = entry["path"]
            assert not path.startswith("tests/"), path
            assert not path.startswith("experiments/"), path
            assert not path.startswith("ui/"), path
            assert not path.startswith("acceptance/"), path
            assert path.endswith(".py"), path
            assert "__pycache__" not in path, path


def test_each_manifest_covers_its_whole_package():
    """A manifest that silently omitted a module would be worth little."""
    expected_roots = {
        "freeze_thermochemistry_api_v1": ["rocketforge/physics/thermochemistry"],
        "freeze_rocket_performance_api_v1": ["rocketforge/engineering/chamber",
                                             "rocketforge/engineering/nozzle"],
        "freeze_trade_study_api_v1": ["rocketforge/engine/studies"],
        "freeze_cea_provider_v1_1": ["rocketforge/providers/cea"],
        "freeze_fluid_properties_api_v1": ["rocketforge/physics/fluids"],
        "freeze_coolprop_provider_v1": ["rocketforge/providers/fluid_properties"],
        "freeze_propellant_metrics_api_v1": ["rocketforge/engineering/propellants"],
        "freeze_line_api_v1": ["rocketforge/engineering/line"],
    }
    for stem, roots in expected_roots.items():
        recorded = {e["path"] for e in load_manifest(stem)["files"]}
        on_disk = set()
        for root in roots:
            for path in (ROOT / root).rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                on_disk.add(path.relative_to(ROOT).as_posix())
        assert recorded == on_disk, {
            "missing_from_manifest": sorted(on_disk - recorded),
            "not_on_disk": sorted(recorded - on_disk)}


def test_the_frozen_compressible_manifest_is_still_valid():
    """Phase 5 must not have touched Compressible v1.

    Phase 4G recorded it as 16-hex prefixes in a Markdown table under the
    untracked ``acceptance/``; it is now a full manifest, verified like the
    others by the reproducibility tests above, and still the same 22 files.
    """
    manifest = load_manifest("freeze_compressible_api_v1")
    paths = [entry["path"] for entry in manifest["files"]]
    assert len(paths) == 22
    assert all(path.startswith(("rocketforge/physics/compressible/", "rocketforge/core/"))
               for path in paths)
    assert "rocketforge/core/freeze.py" not in paths
    assert manifest["migrated_from"]["record"].endswith("phase_4g/ACCEPTANCE_MANIFEST.md")


# ===========================================================================
# public contracts
# ===========================================================================


CONTRACT_MODULES = {
    "line": "rocketforge.engineering.line",
    "thermochemistry": "rocketforge.physics.thermochemistry",
    "chamber": "rocketforge.engineering.chamber",
    "nozzle": "rocketforge.engineering.nozzle",
    "studies": "rocketforge.engine.studies",
    "fluids": "rocketforge.physics.fluids",
    "propellants": "rocketforge.engineering.propellants",
}


@pytest.mark.parametrize("label,module_name", sorted(CONTRACT_MODULES.items()))
def test_every_declared_export_exists(label, module_name):
    module = importlib.import_module(module_name)
    missing = [name for name in module.__all__ if not hasattr(module, name)]
    assert not missing, missing


@pytest.mark.parametrize("label,module_name", sorted(CONTRACT_MODULES.items()))
def test_every_declared_export_is_documented(label, module_name):
    """A frozen symbol nobody can interpret is not a contract."""
    module = importlib.import_module(module_name)
    undocumented = []
    for name in module.__all__:
        value = getattr(module, name)
        if isinstance(value, (int, float, str, bool, tuple, frozenset)):
            continue                       # constants are documented by ``#:``
        if not inspect.getdoc(value):
            undocumented.append(name)
    assert not undocumented, undocumented


@pytest.mark.parametrize("label,module_name", sorted(CONTRACT_MODULES.items()))
def test_no_declared_export_is_defined_outside_rocketforge(label, module_name):
    """A re-exported third-party symbol would freeze someone else's contract."""
    module = importlib.import_module(module_name)
    foreign = []
    for name in module.__all__:
        value = getattr(module, name)
        origin = getattr(value, "__module__", "")
        if origin and not origin.startswith("rocketforge."):
            foreign.append((name, origin))
    assert not foreign, foreign


@pytest.mark.parametrize("label,module_name", sorted(CONTRACT_MODULES.items()))
def test_every_public_dataclass_is_frozen(label, module_name):
    """A result a consumer can edit is not a result."""
    module = importlib.import_module(module_name)
    mutable = []
    for name in module.__all__:
        value = getattr(module, name)
        if inspect.isclass(value) and is_dataclass(value):
            if not value.__dataclass_params__.frozen:
                mutable.append(name)
    assert not mutable, mutable


def test_a_frozen_result_really_refuses_assignment():
    """The negative control for the check above."""
    from rocketforge.engineering.nozzle import PerformanceScale

    scale = PerformanceScale()
    with pytest.raises(FrozenInstanceError):
        scale.value = 1.0            # type: ignore[misc]


#: Field names and order for the records a downstream consumer destructures.
#: Frozen because a reordered or renamed field is a silent breakage for anyone
#: constructing one positionally.
EXPECTED_FIELDS = {
    "rocketforge.engineering.nozzle:NozzleExitState": [
        "mach", "pressure", "temperature", "velocity", "pressure_ratio",
        "area_ratio", "regime", "ambient_pressure"],
    "rocketforge.engineering.nozzle:ThrustBreakdown": [
        "momentum", "pressure", "total"],
    "rocketforge.engineering.nozzle:PerformanceScale": ["mode", "value"],
    "rocketforge.engine.studies:ObjectiveDefinition": ["metric", "direction"],
    "rocketforge.engine.studies:ConstraintDefinition": [
        "metric", "operator", "limit"],
    "rocketforge.engine.studies:MetricDefinition": [
        "key", "label", "stage", "unit", "requires_scale", "help",
        "decimals_hint"],
    "rocketforge.physics.fluids:FluidDefinition": [
        "name", "formula", "molar_mass", "source"],
    "rocketforge.physics.fluids:FluidStateRequest": [
        "fluid", "temperature", "pressure", "properties", "required_phase"],
    "rocketforge.physics.fluids:FluidState": [
        "fluid", "temperature", "pressure", "phase", "provenance", "values",
        "statuses"],
    "rocketforge.physics.fluids:FluidPropertyProvenance": [
        "provider_id", "provider_label", "provider_version", "library_version",
        "backend", "native_fluid_name", "model_notes", "approximations"],
    "rocketforge.engineering.propellants:StreamDensity": [
        "propellant_name", "fluid_name", "temperature", "pressure", "phase",
        "density", "provider_id", "provider_label", "library_version",
        "backend"],
    "rocketforge.engineering.propellants:BulkPropellantDensity": [
        "oxidiser_fuel_ratio", "fuel", "oxidiser", "fuel_mass_fraction",
        "oxidiser_mass_fraction", "density", "assumptions"],
    "rocketforge.engineering.propellants:DensityImpulse": [
        "bulk_density", "effective_exhaust_velocity", "specific_impulse",
        "value", "residual", "unit", "unit_alias"],
}


@pytest.mark.parametrize("target,expected", sorted(EXPECTED_FIELDS.items()))
def test_public_record_fields_are_stable(target, expected):
    module_name, class_name = target.split(":")
    cls = getattr(importlib.import_module(module_name), class_name)
    assert [f.name for f in fields(cls)] == expected


#: Enum members that are part of the contract. A removed member breaks a
#: consumer's match; a renamed one breaks a stored study.
EXPECTED_ENUMS = {
    "rocketforge.engineering.line:FlowRegime":
        ["LAMINAR", "TRANSITIONAL", "TURBULENT"],
    "rocketforge.physics.fluids:FluidPhase":
        ["LIQUID", "GAS", "SUPERCRITICAL", "SOLID", "TWO_PHASE"],
    "rocketforge.physics.fluids:FluidProperty":
        ["DENSITY", "SPECIFIC_ENTHALPY", "SPECIFIC_HEAT_CP",
         "DYNAMIC_VISCOSITY", "THERMAL_CONDUCTIVITY"],
    "rocketforge.physics.fluids:PropertyStatus":
        ["AVAILABLE", "NOT_REQUESTED", "NOT_SUPPORTED", "OUT_OF_RANGE",
         "PHASE_UNSUPPORTED", "TWO_PHASE_AMBIGUOUS", "PROVIDER_FAILED"],
    "rocketforge.physics.fluids:FluidPropertyCapability":
        ["DENSITY", "SPECIFIC_ENTHALPY", "SPECIFIC_HEAT_CP",
         "DYNAMIC_VISCOSITY", "THERMAL_CONDUCTIVITY", "PHASE_IDENTIFICATION",
         "SATURATION_STATE", "TEMPERATURE_DEPENDENCE", "PRESSURE_DEPENDENCE"],
    "rocketforge.engineering.chamber:ChamberGammaBasis":
        ["EQUILIBRIUM", "FROZEN"],
    "rocketforge.engineering.nozzle:PerformanceScaleMode":
        ["NORMALIZED", "THROAT_AREA", "MASS_FLOW"],
    "rocketforge.engine.studies:ObjectiveDirection": ["MAXIMIZE", "MINIMIZE"],
    "rocketforge.engine.studies:ComparisonOperator":
        ["LE", "LT", "GE", "GT", "EQ"],
    "rocketforge.engine.studies:EvaluationStatus":
        ["SUCCESS", "WARNING", "FAILED", "NOT_EVALUABLE"],
    "rocketforge.engine.studies:Feasibility":
        ["FEASIBLE", "INFEASIBLE", "NOT_EVALUATED"],
    "rocketforge.engine.studies:StudyStatus":
        ["COMPLETE", "CANCELLED", "FAILED"],
    "rocketforge.engine.studies:NormalizationMethod":
        ["MIN_MAX_OVER_FEASIBLE"],
}


@pytest.mark.parametrize("target,expected", sorted(EXPECTED_ENUMS.items()))
def test_public_enum_members_are_stable(target, expected):
    module_name, class_name = target.split(":")
    cls = getattr(importlib.import_module(module_name), class_name)
    assert issubclass(cls, Enum)
    assert [member.name for member in cls] == expected


def test_the_public_reference_tables_are_read_only():
    """Scientific reference data a consumer could edit is a mutation point."""
    from types import MappingProxyType

    from rocketforge.providers.cea.propellants import (
        CEA_REACTANT_TEMPERATURE_RANGES,
        PRODUCTION_PROPELLANTS,
    )
    from rocketforge.providers.cea.species import CEA_FORMULAS

    for table in (PRODUCTION_PROPELLANTS, CEA_REACTANT_TEMPERATURE_RANGES,
                  CEA_FORMULAS):
        assert isinstance(table, MappingProxyType)
        with pytest.raises(TypeError):
            table["injected"] = None     # type: ignore[index]


def test_no_public_export_is_a_mutable_container():
    """The general form of the rule above, across every contract package."""
    from types import MappingProxyType

    offenders = []
    for module_name in list(CONTRACT_MODULES.values()) + [
            "rocketforge.providers.cea"]:
        module = importlib.import_module(module_name)
        for name in getattr(module, "__all__", []):
            value = getattr(module, name)
            if isinstance(value, (dict, list, set)) \
                    and not isinstance(value, MappingProxyType):
                offenders.append(f"{module_name}.{name}")
    assert not offenders, offenders


def test_the_mutable_container_audit_would_catch_a_real_case():
    """The negative control."""
    from types import MappingProxyType

    assert isinstance({}, dict) and not isinstance({}, MappingProxyType)
    assert isinstance(MappingProxyType({}), MappingProxyType)


# ===========================================================================
# the Compressible v1 consumer contract
# ===========================================================================


PHASE_5_PACKAGES = [
    "rocketforge/physics/thermochemistry",
    "rocketforge/engineering/chamber",
    "rocketforge/engineering/nozzle",
    "rocketforge/engine/studies",
    "rocketforge/providers/cea",
]


def phase_5_sources():
    for relative in PHASE_5_PACKAGES:
        for path in sorted((ROOT / relative).rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path


def test_phase_5_uses_only_the_public_compressible_surface():
    """No reach into a private module or a private symbol of frozen v1."""
    private = []
    for path in phase_5_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module \
                    and "physics.compressible" in node.module:
                tail = node.module.split("compressible", 1)[1].lstrip(".")
                if tail and any(part.startswith("_")
                                for part in tail.split(".")):
                    private.append((path.name, node.module))
                for alias in node.names:
                    if alias.name.startswith("_"):
                        private.append((path.name, alias.name))
    assert not private, private


def test_the_private_access_audit_would_catch_a_real_case():
    """The negative control."""
    tree = ast.parse("from rocketforge.physics.compressible import _helper\n")
    found = [alias.name for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom)
             for alias in node.names if alias.name.startswith("_")]
    assert found == ["_helper"]


def test_the_compressible_dependency_is_recorded():
    """The contract document must say what Phase 5 depends on."""
    audit = ACCEPTANCE / "contract_audit.json"
    assert audit.is_file(), "the Phase 5G contract audit record is missing"
    payload = json.loads(audit.read_text(encoding="utf-8"))
    contract = payload["compressible_contract"]
    assert contract["verdict"] == "PASS"
    assert contract["consumed_by_phase_5"]
    assert not contract["private_symbol_uses"]


# ===========================================================================
# what "public" means
# ===========================================================================


def test_only_all_is_public_and_the_rest_is_a_submodule_or_a_future_flag():
    """The policy, stated as a test rather than left to convention.

    ``from pkg import submodule`` works for every package in Python, and
    ``from __future__ import annotations`` leaves ``pkg.annotations`` bound.
    Neither is an export anyone chose, and neither may become a frozen
    contract by accident. The rule is therefore: ``__all__`` is the public
    surface, and everything else reachable must be one of those two artifacts.
    """
    import types

    for module_name in list(CONTRACT_MODULES.values()) + [
            "rocketforge.providers.cea"]:
        module = importlib.import_module(module_name)
        declared = set(getattr(module, "__all__", []))
        unexpected = []
        for name, value in vars(module).items():
            if name.startswith("_") or name in declared:
                continue
            is_submodule = isinstance(value, types.ModuleType) and \
                getattr(value, "__name__", "").startswith(module_name)
            is_future_flag = name == "annotations"
            if not (is_submodule or is_future_flag):
                unexpected.append(name)
        assert not unexpected, f"{module_name}: {unexpected}"


def test_the_accidental_export_audit_would_catch_a_real_case():
    """The negative control: a stray helper is not a submodule or a flag."""
    import types

    fake = types.ModuleType("fake")
    fake.__all__ = ["Wanted"]
    fake.Wanted = object()
    fake.leaked_helper = lambda: None
    declared = set(fake.__all__)
    unexpected = [n for n, v in vars(fake).items()
                  if not n.startswith("_") and n not in declared
                  and not isinstance(v, types.ModuleType)
                  and n != "annotations"]
    assert "leaked_helper" in unexpected


def test_the_provider_is_optional_and_imported_lazily():
    """A fresh interpreter builds the app singletons without loading CEA.

    The base environment ships no chemistry library, so this is not a
    performance nicety: an unconditional import would make the whole
    application refuse to start there.
    """
    import subprocess
    import sys

    program = (
        "import sys\n"
        "from rocketforge.application.analysis.thermochemistry_controller "
        "import ThermochemistryController\n"
        "from rocketforge.application.analysis.performance_controller "
        "import RocketPerformanceController\n"
        "from rocketforge.application.analysis.trade_study_controller "
        "import TradeStudyController\n"
        "loaded = sorted(n for n in sys.modules "
        "if n.split('.')[0] in ('cea', 'cantera', 'CoolProp'))\n"
        "assert loaded == [], loaded\n"
        "print('OK')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program], cwd=str(ROOT),
        capture_output=True, text=True, timeout=180,
        env={**__import__("os").environ, "QT_QPA_PLATFORM": "offscreen"})
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("OK")


def test_the_presentation_threshold_never_reaches_a_lower_layer():
    """Blocking. A display rule must not become a physical one."""
    for folder in ("physics", "engineering", "engine", "providers"):
        for path in (ROOT / "rocketforge" / folder).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.ImportFrom):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.Name):
                    names = [node.id]
                elif isinstance(node, ast.Attribute):
                    names = [node.attr]
                assert "CONDENSED_REPORTING_THRESHOLD" not in names, path


def test_the_two_condensed_thresholds_are_separate_constants():
    """They share a value today; they must never share an identity."""
    from rocketforge.application.analysis.thermochemistry_service import (
        CONDENSED_REPORTING_THRESHOLD,
    )
    from rocketforge.engineering.chamber import SINGLE_PHASE_CONDENSED_LIMIT

    assert CONDENSED_REPORTING_THRESHOLD is not SINGLE_PHASE_CONDENSED_LIMIT \
        or isinstance(CONDENSED_REPORTING_THRESHOLD, float)
    presentation = inspect.getsourcefile(
        importlib.import_module(
            "rocketforge.application.analysis.thermochemistry_service"))
    physics = inspect.getsourcefile(
        importlib.import_module("rocketforge.engineering.chamber.handshake"))
    assert presentation != physics


def test_no_phase_5_module_reimplements_a_performance_quantity():
    """One owner per equation, across every frozen package."""
    banned = {"characteristic_velocity", "thrust_coefficient",
              "specific_impulse", "effective_exhaust_velocity"}
    owner = ROOT / "rocketforge" / "engineering" / "nozzle" / "performance.py"
    for path in phase_5_sources():
        if path == owner:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defined = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert not (defined & banned), (path.name, defined & banned)


# ===========================================================================
# versioned supersession
# ===========================================================================


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_a_superseded_manifest_is_kept_and_still_internally_consistent(
        old_stem, new_stem):
    """History is preserved, not rewritten.

    The superseded manifest must still reproduce its own recorded digest from
    its own recorded hashes. That is what makes it evidence: it says what the
    package looked like when it was accepted, and it keeps saying it after the
    package moves on.
    """
    manifest = load_manifest(old_stem)
    entries = [(e["path"], e["sha256"]) for e in manifest["files"]]
    assert independent_digest(entries) == manifest["digest"]


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_the_successor_names_what_it_supersedes(old_stem, new_stem):
    successor = load_manifest(new_stem)
    assert successor["supersedes"] == old_stem
    assert successor["change"], "a version bump must say what changed"


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_a_version_bump_is_additive_and_removes_no_file(old_stem, new_stem):
    """v1.1 must still contain everything v1.0 froze.

    A removed module would be a breaking change wearing a minor version
    number, which is the thing this test exists to prevent.
    """
    before = {e["path"] for e in load_manifest(old_stem)["files"]}
    after = {e["path"] for e in load_manifest(new_stem)["files"]}
    assert not (before - after), {"removed": sorted(before - after)}


@pytest.mark.parametrize("old_stem,new_stem", sorted(HISTORICAL_MANIFESTS.items()))
def test_the_two_versions_actually_differ(old_stem, new_stem):
    """A version bump that changed nothing would be noise in the record."""
    assert load_manifest(old_stem)["digest"] != load_manifest(new_stem)["digest"]


def test_the_superseded_manifest_file_was_not_modified():
    """The historical record still describes the version it was written for.

    Checked by content rather than by mtime: the v1.0 manifest must still name
    v1.0 and must not have acquired the successor's files.
    """
    manifest = load_manifest("freeze_cea_provider_v1")
    assert manifest["version"] == "1.0"
    paths = {e["path"] for e in manifest["files"]}
    assert "rocketforge/providers/cea/enthalpy_coupling.py" not in paths, (
        "regenerating the v1.0 manifest would erase what Phase 5G accepted")


# ===========================================================================
# canonical text: the same source freezes the same way on every checkout
# ===========================================================================


def _freeze_copy(folder: pathlib.Path, name: str, data: bytes):
    from rocketforge.core.freeze import build_manifest, file_digest

    path = folder / name
    path.write_bytes(data)
    return file_digest(path), build_manifest("demo", "1.0", folder, [path]).digest


def test_lf_and_crlf_copies_of_the_same_text_freeze_identically():
    """A Windows working copy (CRLF) and a fresh clone (LF) must agree.

    Algorithm 1 hashed raw bytes, and they did not: seven freeze tests failed
    on a clean checkout of a commit whose working copy passed them.
    """
    import tempfile

    text = "VALUE = 1.0\nOTHER = 2.0\n"
    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        (root / "lf").mkdir()
        (root / "crlf").mkdir()
        lf = _freeze_copy(root / "lf", "module.py", text.encode("utf-8"))
        crlf = _freeze_copy(root / "crlf", "module.py",
                            text.replace("\n", "\r\n").encode("utf-8"))
    assert lf == crlf


def test_a_real_content_change_still_changes_the_digest():
    """The negative control: canonicalising line endings must not blind the freeze."""
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        for name in ("a", "b", "c"):
            (root / name).mkdir()
        original = _freeze_copy(root / "a", "module.py", b"VALUE = 1.0\n")
        edited_lf = _freeze_copy(root / "b", "module.py", b"VALUE = 2.0\n")
        edited_crlf = _freeze_copy(root / "c", "module.py", b"VALUE = 2.0\r\n")
    assert edited_lf[0] != original[0] and edited_lf[1] != original[1]
    assert edited_crlf == edited_lf


@pytest.mark.parametrize("variant", [
    b"VALUE = 1.0\rOTHER = 2.0\n",       # a lone CR is content, not a line ending
    b"VALUE = 1.0 \nOTHER = 2.0\n",      # trailing whitespace
    b"VALUE = 1.0\nOTHER = 2.0",         # no final newline
])
def test_only_crlf_is_canonicalised(variant):
    """Nothing but CRLF -> LF: every other byte difference is a difference."""
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        (root / "base").mkdir()
        (root / "variant").mkdir()
        base = _freeze_copy(root / "base", "module.py", b"VALUE = 1.0\nOTHER = 2.0\n")
        other = _freeze_copy(root / "variant", "module.py", variant)
    assert base[0] != other[0]


@pytest.mark.parametrize("stem", MANIFEST_STEMS)
def test_every_current_manifest_uses_the_current_algorithm(stem):
    from rocketforge.core.freeze import MANIFEST_ALGORITHM

    assert load_manifest(stem)["algorithm"] == MANIFEST_ALGORITHM


def test_a_manifest_is_verified_with_the_algorithm_it_was_made_with():
    """The superseded v1.0 record stays readable as what it was: raw bytes."""
    from rocketforge.core.freeze import (RAW_BYTES_ALGORITHM, FreezeManifest,
                                         file_digest)

    historical = FreezeManifest.from_dict(load_manifest("freeze_cea_provider_v1"))
    assert historical.algorithm == RAW_BYTES_ALGORITHM
    sample = ROOT / "rocketforge" / "core" / "freeze.py"
    assert file_digest(sample, RAW_BYTES_ALGORITHM) == hashlib.sha256(
        sample.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        file_digest(sample, "rocketforge-freeze-manifest/0")


def test_the_implementation_canonicalises_like_the_independent_reading():
    """Both routes to a file digest, compared on every frozen file."""
    from rocketforge.core.freeze import file_digest

    for stem in MANIFEST_STEMS:
        for entry in load_manifest(stem)["files"]:
            path = ROOT / entry["path"]
            assert file_digest(path) == independent_file_digest(path.read_bytes())


def test_the_migration_record_proves_every_migrated_file():
    """Algorithm 2 replaced algorithm 1 without re-freezing anything.

    The record keeps both digests of every file and the proof that the
    canonical text is the committed text; it must cover every file of every
    current manifest, and its digests must be the ones the manifests hold.
    """
    record = json.loads((FREEZE / "MIGRATION_V1_TO_V2.json").read_text(encoding="utf-8"))
    proven = {m["stem"]: {f["path"]: f["algorithm_2"] for f in m.get("files", [])}
              for m in record["manifests"]}
    for stem in MANIFEST_STEMS:
        manifest = load_manifest(stem)
        assert {e["path"]: e["sha256"] for e in manifest["files"]} == proven[stem], stem
