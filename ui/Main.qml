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
    title: App.name
    color: Theme.background

    // Shell state. Kept as plain root properties so it stays inspectable.
    property string appMode: "analysis"   // analysis | engine
    property int currentPageIndex: 0
    property string themeMode: "dark"     // light | dark | system
    property bool navCollapsed: false

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
        }

        RFDivider {}

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: window.appMode === "engine" ? 1 : 0

            // ---- analysis mode ----
            RowLayout {
                spacing: 0

                SideNav {
                    id: nav
                    Layout.preferredWidth: window.navCollapsed ? 0 : Metrics.navWidth
                    Layout.fillHeight: true
                    currentIndex: window.currentPageIndex
                    engineModeActive: window.appMode === "engine"
                    onSelected: function (index) {
                        window.currentPageIndex = index
                        nav.forceActiveFocus()
                    }
                    onEngineModeRequested: window.appMode = "engine"

                    Behavior on Layout.preferredWidth {
                        NumberAnimation { duration: Motion.base; easing.type: Motion.emphasized }
                    }
                }

                RFDivider { vertical: true }

                WorkspaceHost {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: window.currentPageIndex
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
            // still says where the numbers came from.
            items: window.appMode === "engine" ? engineStatus
                                               : (computed ? [] : MockData.statusChips)
            trailing: window.appMode === "engine" ? "No solver in this build"
                                                  : (computed ? solverNote
                                                              : MockData.solverStatus)
            computed: window.appMode === "analysis"
                      && Navigation.items[window.currentPageIndex] !== undefined
                      && Navigation.items[window.currentPageIndex].computed === true

            // A page may say what computed its numbers. Only the chemistry
            // workspace does today, because its solver is not the perfect-gas
            // model every other computed page shares -- and because on a
            // machine with no chemistry provider that page shows nothing at
            // all, which neither default sentence describes.
            readonly property var currentItem: Navigation.items[window.currentPageIndex]
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
