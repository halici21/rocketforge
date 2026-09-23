import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "theme"
import "components"
import "shell"
import "engine"
import "engine/model"
import "data"
import "pages/tradestudy"

/*
 * RocketForge - application shell.
 *
 * Two working modes share one shell: Analysis, where each module is a page,
 * and Engine Design, where the workspace is a canvas of physical components.
 * The application bar, the status line and the theme are common to both; the
 * region between them is swapped as a unit.
 *
 * Mode, theme and current page live here because they are the only pieces of
 * state the whole application shares.
 */
ApplicationWindow {
    id: window

    width: 1560
    height: 940
    minimumWidth: 1120
    minimumHeight: 700
    visible: true
    // A production package is titled with the product name alone; a source run
    // or any other build says which one it is (build_identity.window_title).
    title: App.windowTitle
    color: Theme.background

    // Shell state. Kept as plain root properties so it stays inspectable,
    // and so it stays the stable, script-settable surface the packaged
    // headless diagnostics under rocketforge/application/ already depend on
    // (several call window.setProperty on these two by name) -- renaming or
    // relocating them would break that production infrastructure, so they
    // stay exactly where and what they were.
    // ShellContext (ui/data/) mirrors both one-way (see the Binding elements
    // below) so shell primitives defined in their own files (AnalysisDock,
    // InspectorDrawer, and anything added later) have one shared,
    // semantically-named place to read current selection/panel state from,
    // without every one of them needing this property prop-drilled in --
    // the same role EngineModel already plays for Engine Design mode.
    // `window` stays the sole place that WRITES it.
    property string appMode: "analysis"   // analysis | engine
    property int currentPageIndex: 0
    property string themeMode: "dark"     // light | dark | system
    property bool navCollapsed: false

    readonly property bool isTradeStudyPage:
        currentPageIndex === Navigation.indexOfKey("tradestudy")

    readonly property var themeModes: ["light", "dark", "system"]

    function cycleTheme() {
        var next = (themeModes.indexOf(themeMode) + 1) % themeModes.length
        themeMode = themeModes[next]
    }

    function showAnalysis(pageIndex) {
        if (pageIndex >= 0)
            currentPageIndex = pageIndex
        appMode = "analysis"
    }

    Binding {
        target: Theme
        property: "mode"
        value: window.themeMode
        restoreMode: Binding.RestoreNone
    }

    Binding {
        target: Theme
        property: "systemPrefersDark"
        value: App.systemDark
        restoreMode: Binding.RestoreNone
    }

    Binding {
        target: ShellContext
        property: "currentPageIndex"
        value: window.currentPageIndex
        restoreMode: Binding.RestoreNone
    }

    Binding {
        target: ShellContext
        property: "browserCollapsed"
        value: window.navCollapsed
        restoreMode: Binding.RestoreNone
    }

    // Keep the native window frame in step with the in-app theme.
    onThemeModeChanged: App.applyColorScheme(themeMode)
    Component.onCompleted: App.applyColorScheme(themeMode)

    Shortcut {
        sequence: "Ctrl+B"
        onActivated: window.navCollapsed = !window.navCollapsed
    }
    Shortcut {
        sequence: "Ctrl+Shift+T"
        onActivated: window.cycleTheme()
    }
    Shortcut {
        sequence: "Ctrl+E"
        onActivated: window.appMode = window.appMode === "engine" ? "analysis" : "engine"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TopBar {
            Layout.fillWidth: true
            navCollapsed: window.navCollapsed
            themeMode: window.themeMode
            appMode: window.appMode
            breadcrumb: engineWorkspace.breadcrumbParts
            onToggleNav: window.navCollapsed = !window.navCollapsed
            onThemeModeRequested: function (mode) { window.themeMode = mode }
            onModeRequested: function (mode) { window.appMode = mode }
            onHomeRequested: window.showAnalysis(Navigation.indexOfKey("home"))
        }

        RFDivider {}

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: window.appMode === "engine" ? 1 : 0

            // ---- analysis mode ----
            // Model Browser (collapsible + resizable) | Engineering Viewport,
            // an on-demand Inspector drawer overlaying the viewport, and a
            // collapsible + resizable Analysis Dock along the bottom -- the
            // shell grammar accepted in the CAD/CAE Workbench R1 shell
            // prototype decision (docs/design/CAD_WORKBENCH_R1_DESIGN_DECISION.md).
            // `ShellContext` (ui/data/) carries the state shared across these
            // pieces, mirroring EngineModel's role for Engine Design mode.
            ColumnLayout {
                spacing: 0

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    RowLayout {
                        anchors.fill: parent
                        spacing: 0

                        PanelRail {
                            Layout.fillHeight: true
                            Layout.preferredWidth: Metrics.collapsedRailWidth
                            visible: window.navCollapsed && !browserPanel.transitioning
                            side: "left"
                            label: "Browser"
                            onRestore: window.navCollapsed = false
                        }

                        SplitView {
                            id: analysisSplit
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            orientation: Qt.Horizontal

                            handle: Rectangle {
                                implicitWidth: 5
                                color: "transparent"

                                Rectangle {
                                    anchors.centerIn: parent
                                    width: Metrics.hairline
                                    height: parent.height
                                    color: SplitHandle.pressed ? Theme.accent
                                         : SplitHandle.hovered ? Theme.borderStrong
                                         : Theme.divider
                                    Behavior on color { ColorAnimation { duration: Motion.fast } }
                                }
                            }

                            CollapsiblePanel {
                                id: browserPanel
                                collapsed: window.navCollapsed
                                expandedWidth: Metrics.browserPanelWidth
                                minimumWidth: Metrics.browserPanelMin
                                maximumWidth: Metrics.browserPanelMax

                                SideNav {
                                    id: nav
                                    anchors.fill: parent
                                    currentIndex: window.currentPageIndex
                                    engineModeActive: window.appMode === "engine"
                                    onSelected: function (index) {
                                        window.currentPageIndex = index
                                        nav.forceActiveFocus()
                                    }
                                    onEngineModeRequested: window.appMode = "engine"
                                }
                            }

                            WorkspaceHost {
                                SplitView.fillWidth: true
                                SplitView.minimumWidth: 480
                                currentIndex: window.currentPageIndex
                                onWorkspaceRequested: function (index) { window.showAnalysis(index) }
                                onEngineRequested: window.appMode = "engine"
                            }
                        }
                    }

                    InspectorDrawer {
                        anchors.fill: parent
                        open: ShellContext.inspectorOpen && window.isTradeStudyPage
                        onCloseRequested: ShellContext.inspectorOpen = false

                        // The only current consumer. Loader-instantiated by
                        // InspectorDrawer itself, so no other workspace pays
                        // for this tree.
                        StudyInspector {}
                    }
                }

                RFDivider {}

                AnalysisDock {
                    id: analysisDock
                    objectName: "analysisDock"
                    Layout.fillWidth: true
                    // Never more than half the window's vertical space, so
                    // the engineering object above it always "stays
                    // meaningful" (RF_WORKBENCH_GRAMMAR.md's responsive
                    // rule) even at the 1366x768 floor with the dock
                    // dragged open -- see the comment on
                    // AnalysisDock.maxExpandedHeight for the capture that
                    // found this needed a cap.
                    maxExpandedHeight: Math.min(420, window.height * 0.5)
                    // A fixed tab count keeps `currentTab` meaningful across
                    // navigation; the Diagnostics tab is simply disabled
                    // outside Trade Study rather than removed, so switching
                    // workspaces can never leave `currentTab` pointing at a
                    // tab that no longer exists.
                    tabs: [
                        { label: "Messages", available: true },
                        { label: "Diagnostics", available: window.isTradeStudyPage }
                    ]

                    // Leaving Trade Study while the dock sits on its
                    // (now-disabled) Diagnostics tab would otherwise show an
                    // empty pane -- return to Messages instead.
                    Connections {
                        target: window
                        function onIsTradeStudyPageChanged() {
                            if (!window.isTradeStudyPage && analysisDock.currentTab !== 0)
                                analysisDock.currentTab = 0
                        }
                    }

                    StackLayout {
                        anchors.fill: parent
                        currentIndex: analysisDock.currentTab

                        Item {
                            Text {
                                anchors.centerIn: parent
                                text: "No messages"
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                        }

                        StudyDockDiagnostics {}
                    }
                }
            }

            // ---- engine design mode ----
            EngineWorkspace {
                id: engineWorkspace
                onAnalysisModeRequested: function (pageIndex) { window.showAnalysis(pageIndex) }
            }
        }

        RFDivider {}

        StatusBar {
            Layout.fillWidth: true
            // On a computed page the mock flow chips are dropped rather than
            // shown: "Supersonic · Case 01" beside a subsonic computed result
            // is the status bar asserting something false. The trailing text
            // still says where the numbers came from. Home is neither a
            // compressible-flow calculator nor a computed workspace -- it
            // reports on other workspaces' own state rather than solving
            // anything itself, so it gets neither the mock chips nor a
            // solver sentence, both of which would misdescribe it.
            items: window.appMode === "engine" ? engineStatus
                 : isHomePage ? []
                 : (computed ? [] : MockData.statusChips)
            trailing: window.appMode === "engine" ? "No solver in this build"
                    : isHomePage ? "Workbench overview"
                    : (computed ? solverNote : MockData.solverStatus)
            computed: window.appMode === "analysis"
                      && Navigation.items[window.currentPageIndex] !== undefined
                      && Navigation.items[window.currentPageIndex].computed === true

            // A page may say what computed its numbers. Only the chemistry
            // workspace does today, because its solver is not the perfect-gas
            // model every other computed page shares -- and because on a
            // machine with no chemistry provider that page shows nothing at
            // all, which neither default sentence describes.
            readonly property var currentItem: Navigation.items[window.currentPageIndex]
            readonly property bool isHomePage: window.appMode === "analysis"
                                               && currentItem !== undefined
                                               && currentItem.key === "home"
            readonly property bool chemistryPage: window.appMode === "analysis"
                                                  && currentItem !== undefined
                                                  && currentItem.key === "thermochem"
            readonly property bool chemistryReady: chemistryPage
                                                   && Thermochemistry.providerAvailable

            readonly property string solverNote: {
                if (chemistryPage && !chemistryReady)
                    return "No thermochemistry provider installed"
                return (currentItem !== undefined && currentItem.solverNote !== undefined)
                        ? currentItem.solverNote : "Verified perfect-gas model"
            }

            originNote: {
                if (window.appMode === "engine")
                    return "Topology and structural state only, not a solve"
                if (isHomePage)
                    return "Each row reports that workspace's own state"
                if (chemistryPage && !chemistryReady)
                    return "No values are shown"
                if (currentItem !== undefined && currentItem.computedNote !== undefined)
                    return currentItem.computedNote
                return computed ? "Values computed by RocketForge"
                                : "All values are mock data"
            }

            readonly property var engineStatus: [
                { label: "Design mode", tone: "accent" },
                { label: EngineModel.nodes.count + " components", tone: "neutral" },
                { label: EngineModel.connections.count + " connections", tone: "neutral" },
                { label: "SI", tone: "neutral" }
            ]
        }
    }
}
