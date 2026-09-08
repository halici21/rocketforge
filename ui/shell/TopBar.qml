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

        // ---- product mark ------------------------------------------------
        RowLayout {
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

            Text {
                text: App.stage
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.letterSpacing: 0.4
                font.capitalization: Font.AllUppercase
                Layout.topMargin: 1
            }
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

        Item {
            visible: root.appMode === "analysis"
            Layout.preferredWidth: visible ? workspaceRow.implicitWidth + Metrics.spacing.m : 0
            Layout.preferredHeight: Metrics.controlHeightSmall

            Rectangle {
                anchors.fill: parent
                radius: Metrics.radius.m
                color: fileMenu.opened || workspaceHover.hovered ? Theme.surfaceHover : "transparent"
                Behavior on color { ColorAnimation { duration: Motion.fast } }
            }

            RowLayout {
                id: workspaceRow
                anchors.centerIn: parent
                spacing: Metrics.spacing.s

                Text {
                    text: MockData.workspaceName
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                RFIcon {
                    name: "chevron-down"
                    width: 12
                    height: 12
                    color: Theme.textMuted
                }
            }

            HoverHandler { id: workspaceHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: fileMenu.open() }

            RFMenu {
                id: fileMenu
                y: parent.height + 6
                width: 260

                Column {
                    width: parent.width

                    RFMenuItem {
                        width: parent.width
                        label: "New case"
                        available: false
                        note: "later phase"
                    }
                    RFMenuItem {
                        width: parent.width
                        label: "Open…"
                        available: false
                        note: "later phase"
                    }
                    RFMenuItem {
                        width: parent.width
                        label: "Save"
                        available: false
                        note: "later phase"
                    }
                    RFMenuItem {
                        width: parent.width
                        label: "Export results…"
                        available: false
                        note: "later phase"
                    }

                    Rectangle {
                        width: parent.width
                        height: Metrics.hairline
                        color: Theme.divider
                    }

                    Text {
                        width: parent.width - Metrics.spacing.m
                        x: Metrics.spacing.s
                        topPadding: Metrics.spacing.s
                        bottomPadding: Metrics.spacing.xs
                        text: "Project handling arrives with the first solver module."
                        wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }

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
