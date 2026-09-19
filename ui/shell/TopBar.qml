import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"
import "../data"

/*
 * The application bar: identity on the left, workspace in the middle, global
 * state on the right. Deliberately one row tall - vertical space belongs to
 * the workspace, not to chrome.
 */
Item {
    id: root

    property bool navCollapsed: false
    property string themeMode: "dark"
    property string appMode: "analysis"
    property var breadcrumb: []

    readonly property var modes: ["analysis", "engine"]

    signal toggleNav()
    signal themeModeRequested(string mode)
    signal modeRequested(string mode)
    signal homeRequested()

    implicitHeight: Metrics.topBarHeight

    // Shell chrome sits one step off the workspace so the two read as
    // different layers without a border between them.
    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceSubtle
        Behavior on color { ColorAnimation { duration: Motion.fast } }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Metrics.spacing.m
        anchors.rightMargin: Metrics.spacing.m
        spacing: Metrics.spacing.m

        RFIconButton {
            icon: "panel-left"
            tooltip: root.navCollapsed ? "Show navigation  (Ctrl+B)" : "Hide navigation  (Ctrl+B)"
            active: !root.navCollapsed
            onClicked: root.toggleNav()
        }

        // ---- product mark --------------------------------------------------
        // Clickable: the one affordance that returns to the workbench
        // overview from anywhere, the same convention as returning to a
        // desktop application's own home view.
        RowLayout {
            id: productMark
            spacing: Metrics.spacing.s

            RFIcon {
                name: "nozzle"
                width: 17
                height: 17
                strokeWidth: 1.6
                color: Theme.accent
            }

            Text {
                text: App.name
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.body + 1
                font.weight: Typography.semibold
                font.letterSpacing: 0.2
            }

            // The stage badge ("UI PREVIEW") sat beside the product name on
            // every screen in every capture. It belongs with the version in
            // the settings panel, which is where a reader goes to ask what
            // build this is -- not stamped across a workspace computing
            // verified physics. App.stage is unchanged and still shown there.

            HoverHandler { id: markHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: root.homeRequested() }
        }

        Rectangle {
            Layout.preferredWidth: Metrics.hairline
            Layout.preferredHeight: 18
            Layout.leftMargin: Metrics.spacing.xs
            color: Theme.divider
        }

        // ---- working mode -------------------------------------------------
        RFSegmentedControl {
            Layout.preferredWidth: 216
            Layout.preferredHeight: Metrics.controlHeightSmall
            model: ["Analysis", "Engine Design"]
            currentIndex: root.appMode === "engine" ? 1 : 0
            onSelected: function (index) { root.modeRequested(root.modes[index]) }
        }

        // ---- context: file menu in analysis, breadcrumb in engine design ---
        Row {
            visible: root.appMode === "engine"
            Layout.preferredWidth: visible ? implicitWidth : 0
            Layout.alignment: Qt.AlignVCenter
            spacing: Metrics.spacing.s

            Repeater {
                model: root.breadcrumb

                delegate: Row {
                    required property var modelData
                    required property int index
                    spacing: Metrics.spacing.s

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: index > 0
                        text: "›"
                        color: Theme.textDisabled
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData
                        color: index === root.breadcrumb.length - 1 ? Theme.text
                                                                    : Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                        font.weight: index === root.breadcrumb.length - 1 ? Typography.medium
                                                                          : Typography.regular
                    }
                }
            }
        }

        // The workspace name and its file menu are gone until there is a
        // workspace to name. Every item in that menu was available: false
        // with the note "later phase", so the centre of the application bar
        // carried a control that did nothing on every screen, under the
        // label "Untitled workspace" -- a promise rather than a feature
        // (rf-engineering-workbench: no chrome without a reason). It comes
        // back with project handling, which is what it was waiting for.

        Item { Layout.fillWidth: true }

        // ---- global state -------------------------------------------------
        RFStatusChip {
            text: "SI"
            showDot: false

            HoverHandler { id: unitsHover }
            RFTooltip {
                text: "Unit system is fixed to SI in this build"
                visible: unitsHover.hovered
                x: -width + parent.width
                y: parent.height + 6
            }
        }

        RFIconButton {
            id: themeButton
            icon: root.themeMode === "light" ? "sun"
                : root.themeMode === "dark" ? "moon" : "monitor"
            tooltip: "Appearance  (Ctrl+Shift+T)"
            active: settingsMenu.opened
            onClicked: settingsMenu.open()
        }

        RFIconButton {
            icon: "settings"
            tooltip: "Settings"
            active: settingsMenu.opened
            onClicked: settingsMenu.open()

            SettingsPanel {
                id: settingsMenu
                x: -width + parent.width
                y: parent.height + 8
                themeMode: root.themeMode
                onThemeModeRequested: function (mode) { root.themeModeRequested(mode) }
            }
        }
    }
}
