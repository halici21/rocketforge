"""RocketForge - application bootstrap.

This module is deliberately thin. It starts Qt, publishes the objects QML
cannot construct for itself, and loads the interface from ``ui/``.

Ten singletons reach QML:

* ``App`` -- product name, version, stage, platform colour scheme;
* ``Isentropic``, ``MassFlow``, ``NormalShock``, ``PrandtlMeyer``,
  ``ObliqueShock``, ``Fanno``, ``Rayleigh``, ``Nozzle`` -- the analysis
  controllers, which adapt the verified physics in
  ``rocketforge.physics.compressible`` into display-ready state;
* ``Thermochemistry`` -- the chamber-equilibrium workspace, which adapts a
  thermochemistry **provider**'s results into display-ready state.

``Thermochemistry`` is constructed like the others, but constructing it costs
nothing: its provider gateway defers every provider import to first use, so a
launch that never opens that workspace never loads NASA CEA and never reads a
thermodynamic database.

No engineering equation lives here or in QML. Every fundamental compressible
page now shows computed results, the Nozzle Lab included; the remaining analysis
pages still show the placeholder values in ``ui/data/MockData.qml`` until their
own modules are built.
"""

from __future__ import annotations

import functools
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from PySide6.QtQuickControls2 import QQuickStyle

from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.application.analysis.mass_flow_controller import MassFlowController
from rocketforge.application.analysis.normal_shock_controller import NormalShockController
from rocketforge.application.analysis.oblique_shock_controller import ObliqueShockController
from rocketforge.application.analysis.fanno_controller import FannoController
from rocketforge.application.analysis.prandtl_meyer_controller import PrandtlMeyerController
from rocketforge.application.analysis.nozzle_controller import NozzleController
from rocketforge.application.analysis.rayleigh_controller import RayleighController
from rocketforge.application.analysis.performance_controller import (
    RocketPerformanceController,
)
from rocketforge.application.analysis.fluid_property_controller import (
    FluidPropertyController,
)
from rocketforge.application.analysis.line_controller import LineController
from rocketforge.application.analysis.trade_study_controller import (
    TradeStudyController,
)
from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)
from rocketforge.application.visualization.session import AnalysisSession
from rocketforge.application.visualization.viewport_support import (
    Viewport3DSupport,
    register_viewport_types,
)
from rocketforge.application import build_identity

# The product name is provisional; it is referenced from QML through the App
# singleton so that renaming it is a one-line change.
APP_NAME = "RocketForge"
APP_VERSION = "0.1.0"
APP_STAGE = "UI preview"
ORG_NAME = "RocketForge"
QML_URI = "RocketForge"

def resource_root() -> Path:
    """The directory the interface and its assets are read from.

    Running from source, that is simply the folder holding this file. A frozen
    build unpacks its data somewhere else entirely and sets ``sys._MEIPASS`` to
    say where, so the two cases are asked separately rather than assuming the
    source layout survives packaging. Neither branch consults the working
    directory: the executable has to work when launched from a shortcut, from
    another drive, or from a path with a space in it.
    """
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled)
    return Path(__file__).resolve().parent


UI_DIR = resource_root() / "ui"
# The product mark, resolved the same way as ui/ so the window, the task
# switcher and the taskbar all get it in both a source run and a frozen
# one (packaging/RocketForge.spec carries it into the bundle's datas).
BRAND_ICON = resource_root() / "assets" / "branding" / "rocketforge.ico"

#: Diagnostic: write this process's build identity as JSON and exit.
BUILD_INFO_FLAG = "--build-info"


@functools.lru_cache(maxsize=1)
def current_build() -> build_identity.BuildIdentity:
    """Which RocketForge this process is, established once.

    A packaged build reads the manifest beside its executable and never looks
    for a repository; a source run asks git. See
    rocketforge/application/build_identity.py and
    docs/engineering/release/BUILD_AND_LAUNCH.md.
    """
    frozen = bool(getattr(sys, "frozen", False))
    return build_identity.identity_for_process(
        product=APP_NAME, version=APP_VERSION, frozen=frozen,
        executable_dir=Path(sys.executable).resolve().parent,
        source_root=Path(__file__).resolve().parent)


class AppEnvironment(QObject):
    """Application-level facts exposed to QML as the ``App`` singleton."""

    systemDarkChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._following_system = True
        self._system_dark = self._read_system_dark()

        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._on_system_scheme_changed)

    # ---- product identity ------------------------------------------------

    @Property(str, constant=True)
    def name(self) -> str:
        return APP_NAME

    @Property(str, constant=True)
    def version(self) -> str:
        return APP_VERSION

    @Property(str, constant=True)
    def stage(self) -> str:
        return APP_STAGE

    # ---- build identity: which RocketForge this is ------------------------

    @Property(str, constant=True)
    def buildId(self) -> str:
        return current_build().build_id

    @Property(str, constant=True)
    def buildChannel(self) -> str:
        return current_build().channel

    @Property(str, constant=True)
    def buildMode(self) -> str:
        return current_build().mode

    @Property(str, constant=True)
    def buildCommit(self) -> str:
        return current_build().commit

    @Property(str, constant=True)
    def buildTimestamp(self) -> str:
        return current_build().build_timestamp_utc

    @Property(str, constant=True)
    def runtimeVersions(self) -> str:
        build = current_build()
        return f"Qt {build.qt} · PySide6 {build.pyside6} · Python {build.python}"

    @Property(str, constant=True)
    def buildSummary(self) -> str:
        return current_build().summary()

    @Property(str, constant=True)
    def windowTitle(self) -> str:
        return current_build().window_title(APP_NAME)

    @Slot()
    def copyBuildInfo(self) -> None:
        """Put the build summary on the clipboard, for a bug report."""
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(current_build().summary())

    # ---- platform colour scheme -----------------------------------------

    @Property(bool, notify=systemDarkChanged)
    def systemDark(self) -> bool:
        return self._system_dark

    @Slot(str)
    def applyColorScheme(self, mode: str) -> None:
        """Keep the native window frame in step with the in-app theme.

        Qt paints the title bar from the style hint, so setting it here is what
        stops a light frame from sitting on top of a dark workspace.
        """
        hints = QGuiApplication.styleHints()
        if not hasattr(hints, "setColorScheme"):
            return
        try:
            if mode == "dark":
                scheme = Qt.ColorScheme.Dark
            elif mode == "light":
                scheme = Qt.ColorScheme.Light
            else:
                scheme = Qt.ColorScheme.Unknown
            self._following_system = mode == "system"
            hints.setColorScheme(scheme)
            if self._following_system:
                self._set_system_dark(hints.colorScheme() == Qt.ColorScheme.Dark)
        except (AttributeError, TypeError):
            pass

    def _on_system_scheme_changed(self, *_args) -> None:
        if self._following_system:
            self._set_system_dark(self._read_system_dark())

    def _set_system_dark(self, value: bool) -> None:
        if value != self._system_dark:
            self._system_dark = value
            self.systemDarkChanged.emit()

    @staticmethod
    def _read_system_dark() -> bool:
        try:
            return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        except (AttributeError, TypeError):
            return True


def configure_application() -> None:
    """Global Qt settings that must be applied before the application exists."""
    # The design system styles every control itself, so pin the neutral style
    # rather than inheriting whatever QT_QUICK_CONTROLS_STYLE happens to be.
    QQuickStyle.setStyle("Basic")

    # Collect the QML heap in one pass rather than incrementally. The
    # incremental collector Qt 6.8 made the default freed objects that were
    # still in use under Qt 6.10.2: switching Nozzle Lab to Thermochemistry
    # crashed in Qt6Qml, and a long mixed session still showed the same
    # warning signature after the allocation that provoked the crash was
    # removed. Neither happens in one-pass mode, which is how Qt 6.7 and
    # earlier always collected; a full cycle here takes about 13 ms, 21 ms at
    # most. An explicit QV4_GC_TIMELIMIT in the environment still wins, so
    # the incremental collector can be tested on a newer Qt. Read by the QML
    # engine when it is created, so this must run first. See
    # docs/engineering/implementation/NOTATION_NAVIGATION_CRASH.md.
    os.environ.setdefault("QV4_GC_TIMELIMIT", "0")


def build_engine(parent: QObject | None = None) -> tuple[QQmlApplicationEngine, AppEnvironment]:
    """Create the QML engine with the application's import paths and singletons."""
    environment = AppEnvironment(parent)
    qmlRegisterSingletonInstance(AppEnvironment, QML_URI, 1, 0, "App", environment)

    # The analysis controllers are constructed here rather than in QML so that
    # the interface never owns a physics object, and so a headless test can
    # drive exactly the controllers the interface uses.
    isentropic = IsentropicController(parent)
    qmlRegisterSingletonInstance(IsentropicController, QML_URI, 1, 0, "Isentropic", isentropic)

    mass_flow = MassFlowController(parent)
    qmlRegisterSingletonInstance(MassFlowController, QML_URI, 1, 0, "MassFlow", mass_flow)

    normal_shock = NormalShockController(parent)
    qmlRegisterSingletonInstance(NormalShockController, QML_URI, 1, 0, "NormalShock", normal_shock)

    prandtl_meyer = PrandtlMeyerController(parent)
    qmlRegisterSingletonInstance(PrandtlMeyerController, QML_URI, 1, 0,
                                 "PrandtlMeyer", prandtl_meyer)

    oblique_shock = ObliqueShockController(parent)
    qmlRegisterSingletonInstance(ObliqueShockController, QML_URI, 1, 0,
                                 "ObliqueShock", oblique_shock)

    fanno = FannoController(parent)
    qmlRegisterSingletonInstance(FannoController, QML_URI, 1, 0, "Fanno", fanno)

    rayleigh = RayleighController(parent)
    qmlRegisterSingletonInstance(RayleighController, QML_URI, 1, 0, "Rayleigh", rayleigh)

    nozzle = NozzleController(parent)
    qmlRegisterSingletonInstance(NozzleController, QML_URI, 1, 0, "Nozzle", nozzle)

    # The chemistry workspace. Its provider is resolved lazily, so this line
    # does not import NASA CEA and a normal launch pays nothing for it.
    thermochemistry = ThermochemistryController(parent)
    qmlRegisterSingletonInstance(ThermochemistryController, QML_URI, 1, 0,
                                 "Thermochemistry", thermochemistry)

    # The performance workspace, wired to the chemistry workspace it starts
    # from. The dependency is one-way and explicit: performance reads a chamber
    # state, chemistry knows nothing about performance. Constructed here rather
    # than found through a lookup so the wiring is visible in one place, and so
    # a headless test can build the same pair.
    rocket_performance = RocketPerformanceController(thermochemistry, parent)
    qmlRegisterSingletonInstance(RocketPerformanceController, QML_URI, 1, 0,
                                 "RocketPerformance", rocket_performance)

    # The trade-study workspace, wired to the two workspaces a study's baseline
    # is snapshotted from. The dependencies run one way -- a study reads a
    # chamber case and a nozzle configuration, and neither of those knows a
    # study exists.
    trade_study = TradeStudyController(thermochemistry, rocket_performance,
                                       parent)
    qmlRegisterSingletonInstance(TradeStudyController, QML_URI, 1, 0,
                                 "TradeStudy", trade_study)

    # The fluid-property workspace. It depends on nothing else in the
    # application: a property inspection needs no chamber and no nozzle, which
    # is exactly what makes physics.fluids the fundamental layer it is.
    fluid_properties = FluidPropertyController(parent)
    qmlRegisterSingletonInstance(FluidPropertyController, QML_URI, 1, 0,
                                 "FluidProperties", fluid_properties)

    # The line workspace. It depends on the fluid-property gateway and on
    # nothing else in the application: a line needs a fluid state, not a
    # chamber and not a nozzle.
    line = LineController(parent)
    qmlRegisterSingletonInstance(LineController, QML_URI, 1, 0, "Line", line)

    # Interactive views. Viewport3D says whether Qt Quick 3D is installed (the
    # optional requirements-3d.txt profile); the QML host adds the second
    # condition, a 3D-capable renderer, and without both the 2D engineering
    # view stays the view. AnalysisSession keeps the session's pinned plot
    # snapshots. Neither holds or solves physics.
    available_3d, reason_3d = register_viewport_types()
    viewport_3d = Viewport3DSupport(available_3d, reason_3d, parent)
    qmlRegisterSingletonInstance(Viewport3DSupport, QML_URI, 1, 0, "Viewport3D", viewport_3d)
    analysis_session = AnalysisSession(parent)
    qmlRegisterSingletonInstance(AnalysisSession, QML_URI, 1, 0, "AnalysisSession",
                                 analysis_session)

    # The application icon is global rather than per-window, so one call
    # covers the QML window, the Alt-Tab entry and the taskbar button. It
    # must happen after the QGuiApplication exists -- setWindowIcon is a
    # static on the instance, and calling it from configure_application()
    # (which by contract runs before the application is constructed)
    # aborts the process rather than failing softly. A missing file is not
    # an error: the interface still runs, just without a custom icon.
    if QGuiApplication.instance() is not None and BRAND_ICON.exists():
        QGuiApplication.setWindowIcon(QIcon(str(BRAND_ICON)))

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(UI_DIR))
    return engine, environment


def main() -> int:
    configure_application()

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # The window title is the build-aware title (App.windowTitle). Qt appends the
    # display name to any title that does not already end with it, so the two
    # are the same string: "RocketForge", or "RocketForge [DEV 3f7836c]".
    app.setApplicationDisplayName(current_build().window_title(APP_NAME))
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)

    engine, _environment = build_engine(app)
    engine.quit.connect(app.quit)
    engine.load(QUrl.fromLocalFile(str(UI_DIR / "Main.qml")))

    if not engine.rootObjects():
        print(f"Failed to load {UI_DIR / 'Main.qml'}", file=sys.stderr)
        return 1

    return app.exec()


if __name__ == "__main__":
    # Non-interactive diagnostics, dispatched before the interface starts.
    # They exist so that claims about the *packaged* application are checkable
    # rather than assumed: that the bundled provider can load its native
    # library and find its thermodynamic database, and that the bundled
    # interface loads, navigates and shows the same numbers the source build
    # shows. None has a window that outlives it, a menu entry or any other
    # user-facing surface.
    from rocketforge.application.selftest import (
        SELFTEST_FLAG,
        run_thermochemistry_selftest,
    )
    from rocketforge.application.perfsmoke import (
        PERF_SMOKE_FLAG,
        run_performance_smoke,
    )
    from rocketforge.application.shellsmoke import (
        SHELL_SMOKE_FLAG,
        run_shell_smoke,
    )
    from rocketforge.application.studysmoke import (
        STUDY_SMOKE_FLAG,
        run_study_smoke,
    )
    from rocketforge.application.fluidsmoke import (
        COUPLING_SMOKE_FLAG,
        FLUID_SMOKE_FLAG,
        run_coupling_smoke,
        run_fluid_smoke,
    )
    from rocketforge.application.linesmoke import (
        LINE_SMOKE_FLAG,
        run_line_smoke,
    )
    from rocketforge.application.uismoke import UI_SMOKE_FLAG, run_ui_smoke
    from rocketforge.application.navsmoke import (
        NAVIGATION_SMOKE_FLAG,
        run_navigation_smoke,
    )
    from rocketforge.application.sciencedigest import (
        SCIENCE_DIGEST_FLAG,
        run_science_digest,
    )

    if BUILD_INFO_FLAG in sys.argv:
        # A packaged build has no console, so the answer goes to a file.
        position = sys.argv.index(BUILD_INFO_FLAG)
        target = Path(sys.argv[position + 1]) if len(sys.argv) > position + 1 \
            else Path.cwd() / "rocketforge_build_info.json"
        build = current_build()
        target.write_text(json.dumps({**build.to_dict(),
                                      "window_title": build.window_title(APP_NAME),
                                      "summary": build.summary()}, indent=2),
                          encoding="utf-8")
        sys.exit(0)
    if NAVIGATION_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(NAVIGATION_SMOKE_FLAG)
        sys.exit(run_navigation_smoke(sys.argv[position + 1:],
                                      configure_application, build_engine, UI_DIR))
    if SCIENCE_DIGEST_FLAG in sys.argv:
        position = sys.argv.index(SCIENCE_DIGEST_FLAG)
        configure_application()
        sys.exit(run_science_digest(sys.argv[position + 1:],
                                    current_build().to_dict()))
    if SELFTEST_FLAG in sys.argv:
        sys.exit(run_thermochemistry_selftest())
    if UI_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(UI_SMOKE_FLAG)
        sys.exit(run_ui_smoke(sys.argv[position + 1:],
                              configure_application, build_engine, UI_DIR))
    if PERF_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(PERF_SMOKE_FLAG)
        sys.exit(run_performance_smoke(sys.argv[position + 1:],
                                       configure_application, build_engine, UI_DIR))
    if STUDY_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(STUDY_SMOKE_FLAG)
        sys.exit(run_study_smoke(sys.argv[position + 1:],
                                 configure_application, build_engine, UI_DIR))
    if FLUID_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(FLUID_SMOKE_FLAG)
        sys.exit(run_fluid_smoke(sys.argv[position + 1:],
                                 configure_application, build_engine, UI_DIR))
    if COUPLING_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(COUPLING_SMOKE_FLAG)
        sys.exit(run_coupling_smoke(sys.argv[position + 1:],
                                    configure_application, build_engine, UI_DIR))
    if LINE_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(LINE_SMOKE_FLAG)
        sys.exit(run_line_smoke(sys.argv[position + 1:],
                                configure_application, build_engine, UI_DIR))
    if SHELL_SMOKE_FLAG in sys.argv:
        position = sys.argv.index(SHELL_SMOKE_FLAG)
        sys.exit(run_shell_smoke(sys.argv[position + 1:],
                                 configure_application, build_engine, UI_DIR))

    sys.exit(main())
