import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"
import "../components"

/*
 * The settings surface for this phase: appearance, and an honest statement of
 * what is not configurable yet.
 */
RFMenu {
    id: root

    property string themeMode: "dark"
    signal themeModeRequested(string mode)

    readonly property var modes: ["light", "dark", "system"]

    width: 300
    padding: Metrics.spacing.m

    ColumnLayout {
        width: parent.width
        spacing: Metrics.spacing.m

        RFSectionLabel { text: "Appearance" }

        RFSegmentedControl {
            Layout.fillWidth: true
            model: ["Light", "Dark", "System"]
            currentIndex: Math.max(0, root.modes.indexOf(root.themeMode))
            onSelected: function (index) { root.themeModeRequested(root.modes[index]) }
        }

        RFDivider {}

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.s

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1

                Text {
                    text: "Unit system"
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.body
                }
                Text {
                    text: "Conversion arrives with the solver modules"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFStatusChip {
                Layout.alignment: Qt.AlignVCenter
                text: "SI"
                showDot: false
            }
        }

        RFDivider {}

        RowLayout {
            Layout.fillWidth: true

            Text {
                Layout.fillWidth: true
                text: App.name + " " + App.version
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                text: App.stage
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 0.4
            }
        }
    }
}
