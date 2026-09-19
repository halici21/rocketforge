"""Additive Phase 5D architecture rules, and the static audits of the workspace.

The Phase 5D boundary in one sentence: **QML asks, the application layer
orchestrates, the provider computes, and nothing skips a step.** These rules
are what stop that from decaying into "QML does a quick conversion here" --
the failure mode every other phase of this project has also had to design
against.

Everything here is checked statically on the source, so it holds regardless of
what else a test session happens to have loaded or installed, and it runs in
the base environment where no chemistry library exists.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys

import pytest

#: A double-quoted QML string literal. Named once so every scan that
#: blanks out labels uses the same definition.
QML_STRING = r'"(?:[^"\\]|\\.)*"'

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = PROJECT_ROOT / "rocketforge"
UI = PROJECT_ROOT / "ui"
ANALYSIS = PACKAGE / "application" / "analysis"

#: The QML this phase added.
WORKSPACE_QML = sorted(
    [UI / "pages" / "ThermochemistryPage.qml"]
    + list((UI / "pages" / "thermochemistry").glob("*.qml")))

#: The application modules this phase added.
THERMO_MODULES = sorted((ANALYSIS).glob("thermochemistry_*.py"))


def _strip_qml_comments(text: str) -> str:
    """Remove block and line comments so a scan reads code, not prose.

    The distinction matters: a comment explaining why there is no Isp here is
    the opposite of an Isp leaking into the interface, and a scan that cannot
    tell them apart would force the explanations out of the source.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def _qml_strings(text: str) -> list[str]:
    """Every double-quoted literal in a QML file, comments removed first."""
    return re.findall(r'"((?:[^"\\]|\\.)*)"', _strip_qml_comments(text))


def test_the_workspace_qml_exists_and_is_reachable():
    """A page nobody can navigate to is not a workspace."""
    assert len(WORKSPACE_QML) >= 10, [p.name for p in WORKSPACE_QML]
    navigation = (UI / "data" / "Navigation.qml").read_text(encoding="utf-8")
    assert "ThermochemistryPage.qml" in navigation
    # Analysis Experience R2 replaced the flat per-domain row arrays with
    # progressive-disclosure families. The guard is unchanged in intent --
    # a page nobody can navigate to is not a workspace -- but the
    # mechanism it checks is the families array the rail actually renders.
    families = navigation[navigation.index("readonly property var families:"):]
    assert 'key: "thermochem"' in families
    sidenav = (UI / "shell" / "SideNav.qml").read_text(encoding="utf-8")
    assert "Navigation.families" in sidenav


def test_the_workspace_has_its_four_views():
    names = {path.stem for path in WORKSPACE_QML}
    assert {"ThermoCalculator", "ThermoComposition", "ThermoSweep",
            "ThermoReferences"} <= names
    assert "ThermoProviderUnavailable" in names
    assert "ThermoCondensedSummary" in names


# ===========================================================================
# no provider, no chemistry library, anywhere in QML
# ===========================================================================


def test_qml_imports_only_qt_the_design_system_and_the_app_singletons():
    """The strongest form of "QML does not import a provider".

    Rather than banning particular names, the allowed set is enumerated: any
    import that is not Qt, a relative directory of this project, or the
    ``RocketForge`` singleton module is refused.
    """
    allowed_prefixes = ("QtQuick", "QtQml", "RocketForge 1.0")
    for path in WORKSPACE_QML:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("import "):
                continue
            target = line[len("import "):].strip()
            if target.startswith('"'):
                continue                      # a relative directory of this repo
            assert target.startswith(allowed_prefixes), f"{path.name}: {line}"


def test_no_qml_names_a_chemistry_library_as_code():
    """``cea`` may appear as a display label; never as an identifier."""
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        # Blank out string literals: "NASA CEA 3.3.4" is a label.
        code = re.sub(QML_STRING, '""', code)
        for banned in ("cea", "cantera", "rocketcea", "coolprop"):
            assert not re.search(rf"\b{banned}\b", code, re.IGNORECASE), (
                f"{path.name} uses {banned!r} as code")


def test_no_ui_python_helper_imports_a_provider():
    """There is no UI-side Python at all, and this keeps it that way."""
    assert list(UI.rglob("*.py")) == []


# ===========================================================================
# no physics in QML
# ===========================================================================

#: Layout arithmetic only. Everything else -- logs, powers, roots, trig -- is
#: how a relation would be written, and none belongs here.
ALLOWED_MATH = {"max", "min", "floor", "ceil", "round", "abs"}


def test_qml_uses_only_layout_arithmetic():
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        used = set(re.findall(r"Math\.([a-zA-Z]+)", code))
        assert used <= ALLOWED_MATH, f"{path.name} uses Math.{used - ALLOWED_MATH}"


def test_qml_carries_no_physical_constant():
    """A universal gas constant in QML would mean a relation is in QML."""
    banned = ("8314", "8.3144", "9.80665", "6894", "101325", "273.15",
              "1.986", "0.0821")
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        code = re.sub(QML_STRING, '""', code)
        for constant in banned:
            assert constant not in code, f"{path.name} contains {constant}"


def test_qml_does_no_unit_conversion():
    """The application layer owns the unit boundary, including pressure."""
    scale_factors = re.compile(r"[*/]\s*1\.?0?e[+-]?\d|[*/]\s*1000\b|[*/]\s*100000\b")
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        assert not scale_factors.search(code), f"{path.name} scales a value"


def test_the_audit_would_catch_physics_in_qml():
    """The negative control, so the three scans above cannot be vacuous."""
    offending = (
        'Item { property real r: 8314.46 / molarMass\n'
        '       property real g: Math.pow(t, 2)\n'
        '       property real p: value / 1000 }\n')
    code = _strip_qml_comments(offending)
    assert set(re.findall(r"Math\.([a-zA-Z]+)", code)) - ALLOWED_MATH
    assert "8314" in code
    assert re.search(r"[*/]\s*1000\b", code)


# ===========================================================================
# the performance boundary, in the interface
# ===========================================================================

#: Whole words that would name a rocket-performance quantity. Matched as
#: camelCase words, never as substrings: ``chamberPressureDisplay`` contains
#: "isp", which is the same false positive that flagged RocketForge's own
#: ``MixtureRatio`` for containing "Mixture" in Phase 5C.
PERFORMANCE_WORDS = {"isp", "cstar", "cf", "thrust", "impulse", "star",
                     "characteristic", "velocity"}


def _identifier_words(code: str) -> set[str]:
    """Every camelCase word of every identifier in a fragment of code."""
    words: set[str] = set()
    for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code):
        for part in re.findall(r"[A-Z]?[a-z]+|[A-Z]+|[0-9]+", identifier):
            words.add(part.lower())
    return words


def test_no_workspace_qml_names_a_performance_quantity_in_code():
    """Comments may explain the absence; code may not create the presence."""
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        code = re.sub(QML_STRING, '""', code)
        leaked = _identifier_words(code) & PERFORMANCE_WORDS
        assert not leaked, f"{path.name} references {leaked}"


def test_the_identifier_audit_would_catch_a_real_leak():
    """The negative control, so the scan above cannot be vacuous."""
    for leaked in ("specificImpulse", "cStar", "thrustCoefficient",
                   "characteristicVelocity", "isp"):
        assert _identifier_words(leaked) & PERFORMANCE_WORDS, leaked
    assert not (_identifier_words("chamberPressureDisplay") & PERFORMANCE_WORDS)


def test_no_workspace_string_promises_engine_performance():
    """A wording audit of every user-facing literal in the workspace.

    ``c*`` and ``Isp`` do appear on the References page, but only as the names
    of quantities the page says it is **not** comparing, and those strings come
    from the shipped dataset rather than from QML.
    """
    banned = ("optimal", "optimum", "best o/f", "recommended o/f",
              "real flame temperature", "actual engine performance",
              "combustion efficiency", "guaranteed", "exact result")
    for path in WORKSPACE_QML:
        for literal in _qml_strings(path.read_text(encoding="utf-8")):
            lowered = literal.lower()
            for phrase in banned:
                assert phrase not in lowered, f"{path.name}: {literal!r}"


def test_the_wording_audit_would_catch_a_real_claim():
    text = 'Text { text: "The optimal O/F for this engine" }'
    assert any("optimal" in literal.lower() for literal in _qml_strings(text))


def test_no_qml_names_isp_or_cstar_even_in_a_string():
    """The only permitted occurrences come from the reference dataset."""
    for path in WORKSPACE_QML:
        for literal in _qml_strings(path.read_text(encoding="utf-8")):
            lowered = literal.lower()
            assert "isp" not in lowered.split(), f"{path.name}: {literal!r}"
            assert "c*" not in lowered, f"{path.name}: {literal!r}"


def test_the_chamber_state_still_carries_no_performance_field():
    """Re-asserted at the UI boundary, on the real dataclass."""
    from rocketforge.physics.thermochemistry import ChamberGas

    fields = set(ChamberGas.__dataclass_fields__)
    assert fields.isdisjoint({
        "c_star", "cstar", "cf", "thrust_coefficient", "isp",
        "specific_impulse", "thrust", "characteristic_velocity"})


# ===========================================================================
# layering
# ===========================================================================


def _module_level_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def _all_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_the_new_modules_exist():
    names = {path.name for path in THERMO_MODULES}
    assert names == {
        "thermochemistry_provider.py",
        "thermochemistry_service.py",
        "thermochemistry_sweep.py",
        "thermochemistry_reference.py",
        "thermochemistry_controller.py",
        "thermochemistry_table_model.py",
    }, sorted(names)


def test_no_thermochemistry_module_imports_a_provider_at_module_level():
    """The lazy-loading rule, checked where it is easy to break.

    ``main.py`` builds the controller at start-up, so a module-level provider
    import anywhere in this chain would make every launch pay for a workspace
    the user has not opened -- 181 ms of package import, and on first use the
    native CEA library and its thermodynamic database.
    """
    for path in THERMO_MODULES:
        imports = _module_level_imports(path)
        offenders = {name for name in imports
                     if name.startswith("rocketforge.providers")
                     or name.split(".")[0] in ("cea", "cantera")}
        assert not offenders, f"{path.name} imports {offenders} at module level"


def test_the_gateway_is_the_only_module_that_names_the_provider_package():
    """One door to the provider, so there is one place to change it."""
    for path in THERMO_MODULES:
        if path.name == "thermochemistry_provider.py":
            continue
        for name in _all_imports(path):
            assert not name.startswith("rocketforge.providers"), (
                f"{path.name} reaches past the gateway to {name}")


def test_no_thermochemistry_module_imports_qt_below_the_controller():
    """The service layer stays headless, so its logic is testable without Qt."""
    for path in THERMO_MODULES:
        if path.name in ("thermochemistry_controller.py",
                         "thermochemistry_table_model.py"):
            continue
        for name in _all_imports(path):
            assert not name.startswith("PySide6"), f"{path.name} imports {name}"


def test_the_physics_layer_does_not_import_the_application_layer():
    for path in (PACKAGE / "physics").rglob("*.py"):
        for name in _all_imports(path):
            assert "application" not in name, f"{path} imports {name}"


def test_the_provider_layer_does_not_import_the_application_layer_or_the_ui():
    for path in (PACKAGE / "providers").rglob("*.py"):
        for name in _all_imports(path):
            assert "application" not in name, f"{path} imports {name}"
            assert not name.startswith("PySide6"), f"{path} imports {name}"


def test_no_application_module_reimplements_a_provider_conversion():
    """Phase 5C put every CEA unit conversion in one file. It stays there.

    The kJ-to-J and kg/kmol-to-kg/mol factors are the ones that would be
    retyped, so their appearance in application code is what this looks for.
    A pressure *display* factor is different and is declared in
    ``PRESSURE_UNITS``, where the whole set is visible at once.
    """
    banned = re.compile(r"(kmol|kJ|calc_property|moles_to_weights|"
                        r"num_condensed|mole_fractions\s*\[)")
    for path in THERMO_MODULES:
        source = path.read_text(encoding="utf-8")
        source = re.sub(r'"""(?:.|\n)*?"""', "", source)      # drop docstrings
        source = re.sub(r"#[^\n]*", "", source)               # and comments
        found = banned.findall(source)
        assert not found, f"{path.name} reimplements provider handling: {found}"


def test_the_application_layer_handles_no_raw_provider_object():
    """Nothing here touches a CEA type, a solver object or a raw array."""
    banned = ("EqSolver", "RocketSolver", "Mixture(", "Reactant(",
              "EqSolution", "RocketSolution", "n_frz", "libcea")
    for path in THERMO_MODULES:
        source = path.read_text(encoding="utf-8")
        for name in banned:
            assert name not in source, f"{path.name} handles {name}"


def test_mole_to_mass_conversion_is_not_reimplemented():
    """The application calls the domain's ``to_basis`` and nothing else."""
    service = (ANALYSIS / "thermochemistry_service.py").read_text(encoding="utf-8")
    assert "to_basis(" in service
    # The algebra itself -- sum(x_i M_i) -- must not appear.
    assert "molar_mass *" not in service
    assert "* species[" not in service


# ===========================================================================
# start-up cost
# ===========================================================================


def test_building_the_qml_singletons_does_not_import_cea(tmp_path):
    """A normal launch must not load the chemistry library.

    Run in a fresh interpreter and checked on ``sys.modules``, because the
    claim is about what a launch costs, not about what this test session
    happens to have imported already.
    """
    script = tmp_path / "startup.py"
    script.write_text(
        "import os, sys\n"
        "os.environ['QT_QPA_PLATFORM'] = 'offscreen'\n"
        f"sys.path.insert(0, {str(PROJECT_ROOT)!r})\n"
        "import main\n"
        "from PySide6.QtGui import QGuiApplication\n"
        "main.configure_application()\n"
        "app = QGuiApplication(sys.argv[:1])\n"
        "engine, env = main.build_engine(app)\n"
        "loaded = [n for n in sys.modules if n == 'cea' or n.startswith('cea.')]\n"
        "print('CEA_MODULES=' + repr(loaded))\n",
        encoding="utf-8")
    result = subprocess.run([sys.executable, str(script)],
                            capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    assert "CEA_MODULES=[]" in result.stdout, result.stdout


def test_the_selftest_entry_point_is_untouched():
    """Phase 5C's packaged-provider diagnostic is not repurposed by this phase.

    Phase 5D adds a **second**, separate flag rather than changing this one:
    "can the bundled provider solve?" and "does the bundled interface show the
    right numbers?" are different questions and stay so.
    """
    from rocketforge.application.selftest import SELFTEST_FLAG
    from rocketforge.application.uismoke import UI_SMOKE_FLAG

    assert SELFTEST_FLAG == "--selftest-thermochemistry"
    assert UI_SMOKE_FLAG == "--selftest-thermochemistry-ui"
    assert UI_SMOKE_FLAG != SELFTEST_FLAG

    main_source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert "run_thermochemistry_selftest" in main_source
    assert "run_ui_smoke" in main_source
    for path in WORKSPACE_QML:
        assert "selftest" not in path.read_text(encoding="utf-8").lower()


def test_the_ui_smoke_module_costs_a_normal_launch_nothing():
    """Same rule as the provider self-test, for the same reason.

    ``main.py`` imports it unconditionally to dispatch on the flag, so a
    module-level RocketForge or Qt import here would be paid for on every
    launch.
    """
    path = PACKAGE / "application" / "uismoke.py"
    imports = _module_level_imports(path)
    for name in imports:
        head = name.split(".")[0]
        assert head not in ("rocketforge", "PySide6", "cea", "cantera"), name


def test_the_ui_smoke_module_is_not_a_user_facing_surface():
    """A diagnostic: no QML entry, no menu, no window that outlives it."""
    source = (PACKAGE / "application" / "uismoke.py").read_text(encoding="utf-8")
    assert "qmlRegister" not in source
    assert "app.exec" not in source
    for qml in (PROJECT_ROOT / "ui").rglob("*.qml"):
        assert "uismoke" not in qml.read_text(encoding="utf-8").lower(), qml.name
        assert "selftest" not in qml.read_text(encoding="utf-8").lower(), qml.name


def test_the_ui_smoke_module_sends_no_synthetic_input():
    """The standing rule: never drive the desktop, drive the controller.

    A harness that synthesised key or mouse events could type into whatever
    window happened to be in front. This one calls the same slots the
    interface's own controls call, so there is nothing to guard against.
    """
    source = (PACKAGE / "application" / "uismoke.py").read_text(encoding="utf-8")
    for banned in ("QTest", "sendEvent", "postEvent", "keyClick", "mouseClick",
                   "SendInput", "pyautogui", "keyboard.", "mouse."):
        assert banned not in source, f"uismoke.py uses {banned}"


# ===========================================================================
# the existing interface is untouched
# ===========================================================================


#: The workspaces that are their own analysis domain rather than compressible
#: pages. Named explicitly so the rule below states what it means.
#:
#: The exclusion used to be "anything not called thermochemistry", which was
#: the same claim only for as long as this was the last workspace in the
#: product. Phase 5E added another one, and a rule phrased as an exclusion
#: silently began asserting that the *new* workspace may not mention this one
#: -- which it must, because that is where a user goes to get a chamber state.
#:
#: Phase 5F added the third, for the same reason: a trade study tells a user
#: which tab to visit to set its baseline. Adding a domain here is a deliberate
#: one-line change, and the test below refuses any widening beyond named
#: domains.
ANALYSIS_DOMAIN_PAGES = ("thermochemistry", "rocketperformance", "tradestudy")


def _compressible_pages() -> list:
    return [path for path in (UI / "pages").rglob("*.qml")
            if not any(name in str(path).lower()
                       for name in ANALYSIS_DOMAIN_PAGES)]


def test_no_compressible_page_was_modified_by_this_phase():
    """Phase 5D adds a workspace; it does not redesign the product.

    Checked by content rather than by timestamp: every compressible page must
    still bind to its own controller and must not mention the chemistry one.
    """
    pages = _compressible_pages()
    assert len(pages) >= 30, "the protected set must not be hollowed out"
    for path in pages:
        assert "Thermochemistry" not in path.read_text(encoding="utf-8"), path


def test_the_exclusion_covers_only_the_analysis_domains():
    """The rule above must keep protecting every compressible page.

    A scope this test does not check is a scope that can be widened later to
    make a failure go away, which is how a rule stops being one.
    """
    excluded = set((UI / "pages").rglob("*.qml")) - set(_compressible_pages())
    for path in excluded:
        assert any(name in str(path).lower() for name in ANALYSIS_DOMAIN_PAGES)
    assert {"ThermochemistryPage.qml", "RocketPerformancePage.qml",
            "TradeStudyPage.qml"} <= {
        path.name for path in excluded}


def test_the_engine_design_workspace_is_untouched():
    for path in (UI / "engine").rglob("*.qml"):
        assert "Thermochemistry" not in path.read_text(encoding="utf-8"), path


def test_the_shared_components_kept_their_defaults():
    """Two components gained an option each; neither changed by default."""
    table = (UI / "components" / "RFEngineeringTable.qml").read_text(encoding="utf-8")
    assert 'columns[column].align === "left"' in table, (
        "column alignment should be opt-in per column")
    chart = (UI / "components" / "RFLineChart.qml").read_text(encoding="utf-8")
    assert "property bool showPoints: false" in chart, (
        "drawing the sampled points should be opt-in")


def test_a_left_aligned_first_column_gets_a_full_marker_gutter():
    """Phase 4G gate 9.6, extended to the column alignment Phase 5D added.

    A right-aligned first column parks its text at the column's right edge, so
    a gutter label can borrow the padding already there. A left-aligned one
    starts at the left edge -- where the label is drawn -- and the two printed
    on top of each other: "CONDENSED" over "C(gr)". The gutter now asks for the
    whole label width when the first column is left aligned.
    """
    table = (UI / "components" / "RFEngineeringTable.qml").read_text(encoding="utf-8")
    assert "if (alignsLeft(0))" in table
    assert "markerLabelWidth + Metrics.spacing.m" in table
    # And the right-aligned branch is still the one that subtracts the column.
    assert "- firstColumnWidth" in table


def test_the_composition_table_marks_condensed_rows_in_the_gutter():
    """The annotation exists, and the column it sits beside is left aligned."""
    from rocketforge.application.analysis.thermochemistry_controller import (
        _COMPOSITION_COLUMNS,
    )

    assert _COMPOSITION_COLUMNS[0]["align"] == "left"
    composition = (UI / "pages" / "thermochemistry"
                   / "ThermoComposition.qml").read_text(encoding="utf-8")
    assert 'markedLabel: "CONDENSED"' in composition
    assert "Thermochemistry.condensedRows" in composition


@pytest.mark.parametrize("name", [
    "RFPanel", "RFButton", "RFComboBox", "RFSegmentedControl", "RFStatusChip",
    "RFEmptyState", "RFEngineeringTable", "RFLineChart", "RFResultValue",
    "RFTooltip", "RFBoundNumberField", "RFTextField", "RFSectionLabel",
    "RFDivider", "RFScrollBar", "RFDashedFrame",
])
def test_the_workspace_reuses_the_existing_component_library(name):
    """No second visual language: every control used already existed."""
    assert (UI / "components" / f"{name}.qml").exists()
    used = any(name in path.read_text(encoding="utf-8") for path in WORKSPACE_QML)
    assert used, f"{name} is claimed as reused but never used"
