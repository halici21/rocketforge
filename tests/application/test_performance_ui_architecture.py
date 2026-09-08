"""Phase 5E architecture rules for the Rocket Performance workspace.

The Phase 5D boundary applies unchanged -- QML asks, the application layer
orchestrates, nothing skips a step -- and is re-checked here on the new files
rather than assumed to have been inherited.

What this phase adds is a second boundary, and it runs the other way. Phase 5D
had to keep performance quantities *out* of the chemistry workspace. This one
has to keep the provider's performance quantities from being presented as
RocketForge's, in a workspace where both appear on the same screen.

Everything is checked statically on the source, so it holds regardless of what
a test session has loaded, and it runs in the base environment with no
chemistry library installed.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

#: A double-quoted QML string literal. Named once so every scan that blanks out
#: labels uses the same definition.
QML_STRING = r'"(?:[^"\\]|\\.)*"'

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = PROJECT_ROOT / "rocketforge"
UI = PROJECT_ROOT / "ui"
ANALYSIS = PACKAGE / "application" / "analysis"

#: The QML this phase added.
WORKSPACE_QML = sorted(
    [UI / "pages" / "RocketPerformancePage.qml"]
    + list((UI / "pages" / "rocketperformance").glob("*.qml")))

#: The application modules this phase added.
PERFORMANCE_MODULES = sorted(
    [ANALYSIS / "performance_service.py",
     ANALYSIS / "performance_oracle.py",
     ANALYSIS / "performance_controller.py",
     ANALYSIS / "performance_reference.py"])

#: The Qt-free ones. Everything except the controller.
QT_FREE_MODULES = [path for path in PERFORMANCE_MODULES
                   if path.name != "performance_controller.py"]


def _strip_qml_comments(text: str) -> str:
    """Remove block and line comments so a scan reads code, not prose.

    The distinction matters here more than anywhere: this workspace's comments
    exist to explain what must not happen, and a scan that could not tell a
    warning from a violation would force the explanations out of the source.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def _qml_strings(text: str) -> list[str]:
    """Every double-quoted literal in a QML file, comments removed first."""
    return re.findall(r'"((?:[^"\\]|\\.)*)"', _strip_qml_comments(text))


def _imported_modules(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


# ===========================================================================
# the workspace exists and is reachable
# ===========================================================================


def test_the_workspace_qml_exists():
    assert (UI / "pages" / "RocketPerformancePage.qml").exists()
    assert len(WORKSPACE_QML) >= 5, [p.name for p in WORKSPACE_QML]


def test_the_page_is_registered_in_the_navigation_model():
    """A page nobody can navigate to is not a workspace."""
    navigation = (UI / "data" / "Navigation.qml").read_text(encoding="utf-8")
    assert '"RocketPerformancePage.qml"' in navigation
    assert 'key: "performance"' in navigation


def test_the_navigation_no_longer_advertises_performance_as_planned():
    """It exists now, so listing it under "planned" would be false."""
    navigation = _strip_qml_comments(
        (UI / "data" / "Navigation.qml").read_text(encoding="utf-8"))
    planned = re.search(r"engineItems:\s*\[(.*?)\]", navigation, re.DOTALL)
    assert planned is not None
    assert '"Performance"' not in planned.group(1)


def test_the_sidebar_renders_the_performance_domain():
    sidenav = (UI / "shell" / "SideNav.qml").read_text(encoding="utf-8")
    assert "Navigation.performanceRows" in sidenav
    assert "Navigation.performanceDomain" in sidenav


def test_the_controller_is_registered_as_a_singleton():
    main = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert "RocketPerformanceController" in main
    assert '"RocketPerformance"' in main


# ===========================================================================
# the layer boundary
# ===========================================================================


def test_only_the_controller_imports_qt():
    """Every other module in this feature must run headless."""
    for path in QT_FREE_MODULES:
        for name in _imported_modules(path):
            assert not name.startswith("PySide6"), f"{path.name} imports {name}"
    controller = ANALYSIS / "performance_controller.py"
    assert any(name.startswith("PySide6")
               for name in _imported_modules(controller))


def test_no_qml_imports_a_provider_or_a_physics_module():
    allowed = ("QtQuick", "QtQuick.Controls", "QtQuick.Layouts",
               "QtQuick.Shapes", "QtQuick.Window", "QtCharts", "RocketForge")
    for path in WORKSPACE_QML:
        for line in _strip_qml_comments(
                path.read_text(encoding="utf-8")).splitlines():
            line = line.strip()
            if not line.startswith("import "):
                continue
            target = line[len("import "):].strip()
            if target.startswith('"'):
                continue                      # a relative directory of this repo
            assert target.startswith(allowed), f"{path.name}: {line}"


def test_no_qml_names_a_chemistry_library_as_code():
    """``NASA CEA`` may appear as a display label; never as an identifier."""
    for path in WORKSPACE_QML:
        code = re.sub(QML_STRING, '""',
                      _strip_qml_comments(path.read_text(encoding="utf-8")))
        for banned in ("cea", "cantera", "rocketcea", "coolprop"):
            assert not re.search(rf"\b{banned}\b", code, re.IGNORECASE), (
                f"{path.name} uses {banned!r} as code")


def test_no_qml_names_a_provider_even_as_a_label():
    """The provider's name is data, read from the result that carries it.

    Hard-coding "NASA CEA" in the interface would survive a provider change
    and start lying on the day one happens.
    """
    for path in WORKSPACE_QML:
        for literal in _qml_strings(path.read_text(encoding="utf-8")):
            assert "nasa" not in literal.lower(), f"{path.name}: {literal!r}"
            assert "cea" not in literal.lower().split(), f"{path.name}: {literal!r}"


def test_there_is_still_no_ui_side_python():
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
    """A standard gravity in QML would mean Isp is computed in QML."""
    banned = ("8314", "8.3144", "9.80665", "6894", "101325", "273.15",
              "1.986", "0.0821")
    for path in WORKSPACE_QML:
        code = re.sub(QML_STRING, '""',
                      _strip_qml_comments(path.read_text(encoding="utf-8")))
        for constant in banned:
            assert constant not in code, f"{path.name} contains {constant}"


def test_qml_does_no_unit_conversion():
    scale_factors = re.compile(r"[*/]\s*1\.?0?e[+-]?\d|[*/]\s*1000\b|[*/]\s*100000\b")
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        assert not scale_factors.search(code), f"{path.name} scales a value"


def test_the_audit_would_catch_physics_in_qml():
    """The negative control, so the three scans above cannot be vacuous."""
    offending = ('Item { property real isp: ceff / 9.80665\n'
                 '       property real m: Math.pow(t, 2)\n'
                 '       property real p: value / 1000 }\n')
    code = _strip_qml_comments(offending)
    assert set(re.findall(r"Math\.([a-zA-Z]+)", code)) - ALLOWED_MATH
    assert "9.80665" in code
    assert re.search(r"[*/]\s*1000\b", code)


# ===========================================================================
# the oracle boundary, in the interface
# ===========================================================================


def test_the_oracle_panel_is_a_separate_file():
    """A panel boundary is part of the argument that these are separate."""
    assert (UI / "pages" / "rocketperformance" / "PerfOracle.qml").exists()


def test_the_calculator_view_never_reads_an_oracle_property():
    """The provider's numbers must not appear beside RocketForge's own.

    Not a style preference. A reader who sees an Isp on the Performance tab
    must be able to say without checking that RocketForge computed it.
    """
    code = _strip_qml_comments(
        (UI / "pages" / "rocketperformance" / "PerfCalculator.qml")
        .read_text(encoding="utf-8"))
    assert "oracle" not in code.lower(), "the calculator reads the oracle"


def _prose(path: pathlib.Path) -> str:
    """Every literal in a file, joined as the reader sees it.

    QML wraps long sentences by concatenating adjacent literals, so a phrase a
    user reads as one line is several strings in the source. Joining and then
    collapsing whitespace is what makes a wording audit read the sentence
    rather than the line breaks.
    """
    return re.sub(r"\s+", " ",
                  " ".join(_qml_strings(path.read_text(encoding="utf-8")))).lower()


def test_the_oracle_panel_states_that_it_runs_on_request():
    """An automatic provider call is the failure mode; the wording rules it out."""
    prose = _prose(UI / "pages" / "rocketperformance" / "PerfOracle.qml")
    assert "run provider" in prose
    assert "only when you press run provider" in prose


def test_the_prose_helper_rejoins_a_wrapped_sentence():
    """The negative control for the helper the wording audits depend on."""
    assert "only when you press" in re.sub(
        r"\s+", " ", " ".join(["it happens only ", "when you press Run"])).lower()


def test_no_qml_computes_a_difference_between_two_answers():
    """The comparison arithmetic lives where it can be tested."""
    for path in WORKSPACE_QML:
        code = _strip_qml_comments(path.read_text(encoding="utf-8"))
        # A subtraction or ratio between two model values would look like this.
        assert not re.search(r"rocketforge\s*[-/]\s*", code, re.IGNORECASE), path.name
        assert not re.search(r"\.value\s*[-/]\s*\w+\.value", code), path.name


# ===========================================================================
# wording
# ===========================================================================


#: Phrases that would be a claim about a real engine.
CLAIM_PHRASES = ("actual engine performance", "real engine performance",
                 "predicted performance", "guaranteed", "exact result",
                 "optimal design", "recommended design",
                 "combustion efficiency", "expected thrust", "delivered isp",
                 "delivered specific impulse")

#: Words that turn a claim into its opposite when they precede it.
#:
#: Needed because this workspace's honest wording contains the very phrases the
#: audit bans: "an example, not a recommended design" is a disclaimer, and
#: flagging it would push the disclaimer out of the interface. The same class
#: of false positive as reading "isp" out of ``chamberPressureDisplay``.
NEGATORS = ("not a", "not an", "not the", "never a", "never the", "no ",
            "rather than a", "rather than an", "instead of a")


def _claims(prose: str) -> list[str]:
    """Occurrences of a banned phrase that are not preceded by a negation."""
    found = []
    for phrase in CLAIM_PHRASES:
        for match in re.finditer(re.escape(phrase), prose):
            before = prose[max(0, match.start() - 24):match.start()]
            if not any(before.rstrip().endswith(word.strip())
                       or word in before[-len(word) - 2:]
                       for word in NEGATORS):
                found.append(f"{before!r} -> {phrase!r}")
    return found


def test_no_string_promises_real_engine_performance():
    """An ideal figure is an upper bound, and no label may imply otherwise."""
    for path in WORKSPACE_QML:
        claims = _claims(_prose(path))
        assert not claims, f"{path.name}: {claims}"


def test_the_wording_audit_would_catch_a_real_claim():
    """The negative control, in both directions.

    It must fire on the claim and stay silent on the disclaimer, or it would
    be enforcing the opposite of what it is for.
    """
    assert _claims("this is the predicted performance of the engine")
    assert _claims("a recommended design for this mission")
    assert not _claims("an example, not a recommended design.")
    assert not _claims("an upper bound, never a predicted performance")


def test_the_workspace_says_ideal_where_a_reader_will_see_it():
    """The framing is on the page header, not only in a details panel."""
    page = (UI / "pages" / "RocketPerformancePage.qml").read_text(encoding="utf-8")
    literals = " ".join(_qml_strings(page)).lower()
    assert "ideal" in literals


def test_the_comparison_never_calls_a_residual_an_error():
    """Two models disagreeing is a model difference. The word matters."""
    oracle = (UI / "pages" / "rocketperformance" / "PerfOracle.qml").read_text(
        encoding="utf-8")
    for literal in _qml_strings(oracle):
        lowered = literal.lower()
        if "%" in lowered or "difference" in lowered:
            assert "error in" not in lowered or "rather than an error" in lowered


def test_no_qml_hardcodes_a_reference_condition():
    """It is measured from the provider and carried on the result.

    Phase 5E established by measurement that a provider's Cf and Isp columns
    are the optimum-expansion values. Restating that as a literal in the
    interface would make it a claim the interface cannot check.
    """
    for path in WORKSPACE_QML:
        for literal in _qml_strings(path.read_text(encoding="utf-8")):
            lowered = literal.lower()
            assert "p_e = p_a" not in lowered, f"{path.name}: {literal!r}"


# ===========================================================================
# the diagnostic
# ===========================================================================


def test_the_packaged_diagnostic_exists_and_is_dispatched():
    from rocketforge.application.perfsmoke import PERF_SMOKE_FLAG

    main = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert "PERF_SMOKE_FLAG" in main
    assert "run_performance_smoke" in main
    assert PERF_SMOKE_FLAG.startswith("--selftest-")


def test_the_diagnostic_takes_its_bootstrap_as_arguments():
    """A frozen build runs main.py as __main__, so it cannot import it."""
    source = (PACKAGE / "application" / "perfsmoke.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "run_performance_smoke")
    names = [argument.arg for argument in function.args.args]
    assert names == ["argv", "configure", "build_engine", "ui_dir"]
    assert "import main" not in source


def test_the_diagnostic_sends_no_synthetic_input():
    """It drives controllers, never the desktop."""
    source = (PACKAGE / "application" / "perfsmoke.py").read_text(encoding="utf-8")
    for banned in ("QTest", "sendEvent", "postEvent", "QCursor", "keyClick",
                   "mouseClick", "pyautogui", "SendInput"):
        assert banned not in source, banned


def test_the_diagnostic_counts_provider_calls():
    """The one thing a screenshot cannot show is a hidden chemistry re-solve."""
    source = (PACKAGE / "application" / "perfsmoke.py").read_text(encoding="utf-8")
    assert "solve_chamber" in source
    assert "causedByInputChanges" in source


# ===========================================================================
# the existing interface is untouched
# ===========================================================================


def test_no_compressible_page_mentions_the_performance_workspace():
    """Phase 5E adds a domain; it does not reach into the existing ones.

    The mirror of the Phase 5D rule, and the reason that rule had to be
    rescoped: the dependency between these two workspaces runs one way, from
    performance to chemistry, and it must not start running back.
    """
    domains = ("thermochemistry", "rocketperformance", "tradestudy")
    pages = [path for path in (UI / "pages").rglob("*.qml")
             if not any(name in str(path).lower() for name in domains)]
    assert len(pages) >= 30, "the protected set must not be hollowed out"
    for path in pages:
        assert "RocketPerformance" not in path.read_text(encoding="utf-8"), path


def test_the_chemistry_workspace_does_not_reach_into_this_one():
    """Chemistry knows nothing about performance, in the interface too."""
    for path in (UI / "pages" / "thermochemistry").glob("*.qml"):
        assert "RocketPerformance" not in path.read_text(encoding="utf-8"), path
    page = (UI / "pages" / "ThermochemistryPage.qml").read_text(encoding="utf-8")
    assert "RocketPerformance" not in page


def test_the_engine_design_workspace_is_untouched():
    for path in (UI / "engine").rglob("*.qml"):
        assert "RocketPerformance" not in path.read_text(encoding="utf-8"), path


def test_no_shared_component_was_changed_for_this_phase():
    """The workspace is built from the existing kit, unmodified.

    A new page that needs a component changed is a page that has drifted from
    the design system; this one needed none.
    """
    for path in (UI / "components").glob("*.qml"):
        text = path.read_text(encoding="utf-8")
        assert "RocketPerformance" not in text, path
        assert "Perf" not in text, path
