"""Phase 5F architecture rules.

The layering this phase has to protect is the one it introduced: a generic
decision engine that must not know what a rocket is, above physics that must
not know a study exists.

    ui  ->  TradeStudyController  ->  trade_study_service
                                          |         |
                            engine.studies          thermochemistry + performance

Every arrow is one way. The generic core cannot reach a provider, Qt, or the
application; QML cannot reach a decision algorithm; and nothing in this phase
re-implements a quantity Phase 5E already owns.

Checked statically on the source, so the rules hold regardless of what a test
session happens to have imported, and they run with no chemistry library
installed.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

QML_STRING = r'"(?:[^"\\]|\\.)*"'

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = PROJECT_ROOT / "rocketforge"
UI = PROJECT_ROOT / "ui"
STUDIES = PACKAGE / "engine" / "studies"
ANALYSIS = PACKAGE / "application" / "analysis"

WORKSPACE_QML = sorted(
    [UI / "pages" / "TradeStudyPage.qml"]
    + list((UI / "pages" / "tradestudy").glob("*.qml")))

APPLICATION_MODULES = [
    ANALYSIS / "trade_study_domain.py",
    ANALYSIS / "trade_study_service.py",
    ANALYSIS / "trade_study_controller.py",
]


def _imports(path: pathlib.Path) -> set[str]:
    """Every module name a file imports, relative forms included.

    ``from . import performance_service`` records the name in ``node.names``
    and leaves ``node.module`` empty, so reading only ``module`` reports a file
    that imports six siblings as importing nothing.
    """
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.update(f"{node.module}.{alias.name}"
                             for alias in node.names)
            else:
                names.update(alias.name for alias in node.names)
    return names


def _strip_qml_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", " ", text)


def _qml_strings(text: str) -> list[str]:
    return re.findall(r'"((?:[^"\\]|\\.)*)"', _strip_qml_comments(text))


def _prose(path: pathlib.Path) -> str:
    """Literals joined as a reader sees them, whitespace collapsed.

    QML wraps a sentence by concatenating literals, so a wording audit that
    matched line by line would miss any phrase that spans a break.
    """
    return re.sub(r"\s+", " ",
                  " ".join(_qml_strings(path.read_text(encoding="utf-8")))).lower()


# ===========================================================================
# the generic core is generic
# ===========================================================================


def test_the_studies_package_exists_where_the_architecture_puts_it():
    """Doc 06 assigns parametric studies and trades to ``engine.studies``."""
    assert STUDIES.is_dir()
    assert (STUDIES / "__init__.py").exists()
    assert len(list(STUDIES.glob("*.py"))) >= 8


@pytest.mark.parametrize("path", sorted(STUDIES.glob("*.py")),
                         ids=lambda p: p.name)
def test_no_studies_module_imports_qt_a_provider_or_the_application(path):
    """The whole basis for testing the decision algorithms without physics."""
    for name in _imports(path):
        assert not name.startswith("PySide6"), f"{path.name} imports {name}"
        assert "providers" not in name, f"{path.name} imports {name}"
        assert "application" not in name, f"{path.name} imports {name}"
        assert not name.startswith("cea"), f"{path.name} imports {name}"
        assert "cantera" not in name.lower(), f"{path.name} imports {name}"


@pytest.mark.parametrize("path", sorted(STUDIES.glob("*.py")),
                         ids=lambda p: p.name)
def test_no_studies_module_imports_physics_or_engineering(path):
    """It could -- L3 permits it -- and it does not.

    A design-space engine that reached into ``engineering.nozzle`` would stop
    being a design-space engine and become a rocket one.
    """
    for name in _imports(path):
        assert not name.startswith("rocketforge.physics"), path.name
        assert not name.startswith("rocketforge.engineering"), path.name


def test_the_studies_package_imports_nothing_from_rocketforge_but_core():
    """Measured, not asserted: the only permitted couplings are stdlib-shaped."""
    external = set()
    for path in STUDIES.glob("*.py"):
        external |= {name for name in _imports(path)
                     if name.startswith("rocketforge")}
    assert all(name.startswith("rocketforge.engine.studies")
               or name.startswith("rocketforge.core")
               for name in external), sorted(external)


def test_the_generic_core_runs_with_no_chemistry_library_loaded():
    """The absolute claim, in a process nothing else has touched."""
    import subprocess
    import sys

    program = (
        "import sys\n"
        "from rocketforge.engine.studies import (\n"
        "    ExplicitNumericVariable, MetricDefinition, MetricRegistry,\n"
        "    ObjectiveDefinition, ObjectiveDirection, StageOutcome,\n"
        "    StudyBaseline, StudyDefinition, run_study)\n"
        "registry = MetricRegistry([MetricDefinition('m', 'M', 'a')])\n"
        "class E:\n"
        "    def evaluate(self, stage, point, upstream):\n"
        "        return StageOutcome(ok=True, metrics={'m': point.values['x']})\n"
        "definition = StudyDefinition(\n"
        "    baseline=StudyBaseline(), stage_order=('a', 'b'),\n"
        "    variables=(ExplicitNumericVariable(\n"
        "        key='x', label='X', stage='a', entries=(1.0, 2.0, 3.0)),),\n"
        "    outputs=('m',),\n"
        "    objectives=(ObjectiveDefinition('m', ObjectiveDirection.MAXIMIZE),))\n"
        "result = run_study(definition, registry, E())\n"
        "assert len(result.points) == 3 and result.ranking[0] == 2\n"
        "loaded = sorted(n for n in sys.modules\n"
        "                if n.split('.')[0] in ('cea', 'cantera', 'PySide6'))\n"
        "assert loaded == [], loaded\n"
        "print('OK')\n"
    )
    completed = subprocess.run([sys.executable, "-c", program],
                               cwd=str(PROJECT_ROOT), capture_output=True,
                               text=True, timeout=120)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("OK")


# ===========================================================================
# the application layer is the only orchestrator
# ===========================================================================


def test_only_the_controller_imports_qt():
    for path in APPLICATION_MODULES[:2]:
        for name in _imports(path):
            assert not name.startswith("PySide6"), f"{path.name} imports {name}"
    controller = ANALYSIS / "trade_study_controller.py"
    assert any(name.startswith("PySide6") for name in _imports(controller))


def test_the_service_reaches_the_provider_only_through_the_gateway():
    """One route into ``rocketforge.providers``, and it is the accepted one."""
    for path in APPLICATION_MODULES:
        for name in _imports(path):
            assert not name.startswith("rocketforge.providers"), path.name


def test_the_service_reuses_the_canonical_thermochemistry_and_performance():
    names = _imports(ANALYSIS / "trade_study_service.py")
    assert any("thermochemistry_service" in name for name in names)
    assert any("performance_service" in name for name in names)


def test_no_second_performance_implementation_exists():
    """Phase 5E owns c*, Cf and Isp. This phase reads them."""
    for path in APPLICATION_MODULES + sorted(STUDIES.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defined = {node.name for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for banned in ("characteristic_velocity", "thrust_coefficient",
                       "specific_impulse", "solve_ideal_performance"):
            assert banned not in defined, f"{path.name} defines {banned}"


def test_physics_and_engineering_never_import_the_decision_layer():
    """The arrow runs one way. A nozzle must not know a study exists."""
    for folder in ("physics", "engineering"):
        for path in (PACKAGE / folder).rglob("*.py"):
            for name in _imports(path):
                assert "studies" not in name, f"{path} imports {name}"
                assert "trade_study" not in name, f"{path} imports {name}"


def test_the_providers_package_owns_no_trade_study_logic():
    for path in (PACKAGE / "providers").rglob("*.py"):
        for name in _imports(path):
            assert "studies" not in name, f"{path} imports {name}"
            assert "trade_study" not in name, f"{path} imports {name}"


# ===========================================================================
# QML
# ===========================================================================


def test_the_workspace_qml_exists_and_is_registered():
    assert (UI / "pages" / "TradeStudyPage.qml").exists()
    assert len(WORKSPACE_QML) >= 5, [p.name for p in WORKSPACE_QML]
    navigation = (UI / "data" / "Navigation.qml").read_text(encoding="utf-8")
    assert '"TradeStudyPage.qml"' in navigation
    assert 'key: "tradestudy"' in navigation
    sidenav = (UI / "shell" / "SideNav.qml").read_text(encoding="utf-8")
    assert "Navigation.studyRows" in sidenav
    main = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert '"TradeStudy"' in main


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_no_qml_imports_a_provider_or_a_physics_module(path):
    allowed = ("QtQuick", "QtQuick.Controls", "QtQuick.Layouts",
               "QtQuick.Shapes", "QtQuick.Window", "RocketForge")
    for line in _strip_qml_comments(path.read_text(encoding="utf-8")).splitlines():
        line = line.strip()
        if not line.startswith("import "):
            continue
        target = line[len("import "):].strip()
        if target.startswith('"'):
            continue
        assert target.startswith(allowed), f"{path.name}: {line}"


ALLOWED_MATH = {"max", "min", "floor", "ceil", "round", "abs"}


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_qml_uses_only_layout_arithmetic(path):
    code = _strip_qml_comments(path.read_text(encoding="utf-8"))
    used = set(re.findall(r"Math\.([a-zA-Z]+)", code))
    assert used <= ALLOWED_MATH, f"{path.name} uses Math.{used - ALLOWED_MATH}"


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_qml_carries_no_physical_constant(path):
    code = re.sub(QML_STRING, '""',
                  _strip_qml_comments(path.read_text(encoding="utf-8")))
    for constant in ("8314", "8.3144", "9.80665", "6894", "101325", "273.15"):
        assert constant not in code, f"{path.name} contains {constant}"


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_qml_implements_no_decision_algorithm(path):
    """Pareto, normalisation and constraint checking are not view logic.

    A dominance loop in JavaScript would be a second implementation of the
    thing this phase exists to get right, in the one layer with no tests.

    String literals are blanked first. "Feasible, dominated" is a legend entry
    -- naming a verdict the engine reached is the opposite of computing one --
    and a scan that could not tell them apart would force the labels off the
    chart.
    """
    code = re.sub(QML_STRING, '""',
                  _strip_qml_comments(path.read_text(encoding="utf-8"))).lower()
    for banned in ("dominat", "normaliz", "normalis", "weightedsum",
                   "issatisfied", "computescore"):
        assert banned not in code, f"{path.name} appears to implement {banned}"


def test_the_decision_algorithm_audit_would_catch_a_real_leak():
    """The negative control, in both directions."""
    offending = 'Item { function dominates(a, b) { return a > b } }'
    label_only = 'Text { text: "Feasible, dominated" }'
    assert "dominat" in re.sub(QML_STRING, '""',
                               _strip_qml_comments(offending)).lower()
    assert "dominat" not in re.sub(QML_STRING, '""',
                                   _strip_qml_comments(label_only)).lower()


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_qml_computes_no_score_and_no_constraint_verdict(path):
    code = _strip_qml_comments(path.read_text(encoding="utf-8"))
    # A weighted sum or a limit comparison would look like these.
    assert not re.search(r"weight\s*\*", code), path.name
    assert not re.search(r"<=\s*limit|>=\s*limit", code), path.name


def test_the_qml_audits_would_catch_a_real_leak():
    """The negative control, so the three scans above cannot be vacuous."""
    offending = ('Item { property real s: weight * value / 9.80665\n'
                 '       property bool d: Math.pow(a, 2) > b }\n')
    code = _strip_qml_comments(offending)
    assert set(re.findall(r"Math\.([a-zA-Z]+)", code)) - ALLOWED_MATH
    assert "9.80665" in code
    assert re.search(r"weight\s*\*", code)


# ===========================================================================
# wording
# ===========================================================================


#: Phrases that would claim more than a sampled grid can support.
OPTIMUM_CLAIMS = ("global optimum", "globally optimal", "the optimal design",
                  "optimum design", "guaranteed optimum")

#: Words that turn such a claim into its opposite when they precede it.
#:
#: This workspace's honest wording contains the banned phrases *inside* the
#: sentences that rule them out -- "cannot establish a global optimum". The
#: same class of false positive as Phase 5E's "not a recommended design", and
#: flagging it would push the disclaimer out of the interface.
OPTIMUM_NEGATORS = ("cannot establish", "does not establish", "not a",
                    "never a", "no ", "rather than a", "is not")


def _optimum_claims(prose: str) -> list[str]:
    found = []
    for phrase in OPTIMUM_CLAIMS:
        for match in re.finditer(re.escape(phrase), prose):
            before = prose[max(0, match.start() - 40):match.start()]
            if not any(word in before for word in OPTIMUM_NEGATORS):
                found.append(f"{before!r} -> {phrase!r}")
    return found


@pytest.mark.parametrize("path", WORKSPACE_QML, ids=lambda p: p.name)
def test_no_string_claims_a_global_optimum(path):
    """A finite sampled grid cannot establish one, and nothing here searches."""
    claims = _optimum_claims(_prose(path))
    assert not claims, f"{path.name}: {claims}"


def test_the_optimum_audit_fires_on_a_claim_and_not_on_a_disclaimer():
    """The negative control, in both directions."""
    assert _optimum_claims("this is the global optimum for the mission")
    assert _optimum_claims("we found the optimal design")
    assert not _optimum_claims(
        "a finite sampled grid cannot establish a global optimum")
    assert not _optimum_claims("this is not a globally optimal answer")


def test_the_workspace_uses_the_evaluated_wording():
    prose = _prose(UI / "pages" / "tradestudy" / "StudyPareto.qml")
    assert "best evaluated feasible points" in prose
    assert "cannot establish a global optimum" in prose


def test_the_prose_helper_rejoins_a_wrapped_sentence():
    """The helper every wording audit depends on, checked directly."""
    text = ('Text { text: "a finite sampled grid cannot " '
            '+ "establish a global optimum" }')
    joined = re.sub(r"\s+", " ", " ".join(_qml_strings(text))).lower()
    assert "cannot establish a global optimum" in joined


def test_the_setup_states_that_scoring_is_optional_and_off():
    prose = _prose(UI / "pages" / "tradestudy" / "StudySetup.qml")
    assert "optional" in prose
    assert "scoring starts off" in prose or "combine the objectives" in prose


def test_the_pareto_note_says_the_markers_are_samples():
    """The wording lives in the controller, because it counts the objectives.

    It has to say how many objectives decided membership when a two-axis plot
    shows only some of them, and a static string in the view cannot do that.
    """
    import inspect

    from rocketforge.application.analysis.trade_study_controller import (
        TradeStudyController,
    )

    note = inspect.getsource(TradeStudyController.paretoNote.fget)
    assert "not a point on a" in note
    assert "sample of the grid" in note
    assert "objectives" in note


# ===========================================================================
# the diagnostic
# ===========================================================================


def test_the_packaged_diagnostic_exists_and_is_dispatched():
    from rocketforge.application.studysmoke import STUDY_SMOKE_FLAG

    main = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert "STUDY_SMOKE_FLAG" in main
    assert "run_study_smoke" in main
    assert STUDY_SMOKE_FLAG == "--selftest-trade-study"


def test_the_earlier_self_tests_are_still_dispatched():
    """Phase 5F adds a diagnostic; it does not repurpose the other three."""
    main = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    for flag in ("SELFTEST_FLAG", "UI_SMOKE_FLAG", "PERF_SMOKE_FLAG",
                 "STUDY_SMOKE_FLAG"):
        assert flag in main, flag


def test_the_diagnostic_sends_no_synthetic_input():
    source = (PACKAGE / "application" / "studysmoke.py").read_text(
        encoding="utf-8")
    for banned in ("QTest", "sendEvent", "postEvent", "QCursor", "keyClick",
                   "mouseClick", "pyautogui", "SendInput"):
        assert banned not in source, banned


def test_the_diagnostic_counts_provider_calls():
    source = (PACKAGE / "application" / "studysmoke.py").read_text(
        encoding="utf-8")
    assert "solve_chamber" in source
    assert "actualChemistrySolves" in source
    assert "addedByObjective" in source


def test_execution_is_serial_with_no_worker_pool():
    """Phase 5B-0 measured CEA threading and found no gain."""
    source = (ANALYSIS / "trade_study_controller.py").read_text(encoding="utf-8")
    for banned in ("QThreadPool", "QThread", "ThreadPoolExecutor",
                   "ProcessPoolExecutor", "multiprocessing", "QRunnable"):
        assert banned not in source, banned
    assert "QTimer" in source          # chunking, not threading


# ===========================================================================
# the existing interface is untouched
# ===========================================================================


ANALYSIS_DOMAIN_PAGES = ("thermochemistry", "rocketperformance", "tradestudy")


def test_no_other_page_mentions_the_trade_study_workspace():
    pages = [path for path in (UI / "pages").rglob("*.qml")
             if not any(name in str(path).lower()
                        for name in ANALYSIS_DOMAIN_PAGES)]
    assert len(pages) >= 30, "the protected set must not be hollowed out"
    for path in pages:
        assert "TradeStudy" not in path.read_text(encoding="utf-8"), path


def test_the_upstream_workspaces_do_not_reach_into_this_one():
    """A study reads a chamber case; a chamber knows no study exists."""
    for folder in ("thermochemistry", "rocketperformance"):
        for path in (UI / "pages" / folder).glob("*.qml"):
            assert "TradeStudy" not in path.read_text(encoding="utf-8"), path


def test_the_only_shared_component_change_is_an_added_signal():
    """RFComboBox gained ``activated``; nothing else in the kit moved.

    Additive: no property, default or painted part changed, and every existing
    caller keeps working. It was needed because a selector bound to a backend
    property cannot write back from ``onCurrentIndexChanged`` without looping.
    """
    combo = (UI / "components" / "RFComboBox.qml").read_text(encoding="utf-8")
    assert "signal activated(int index)" in combo
    for path in (UI / "components").glob("*.qml"):
        text = path.read_text(encoding="utf-8")
        assert "TradeStudy" not in text, path
        assert "Study" not in text, path
