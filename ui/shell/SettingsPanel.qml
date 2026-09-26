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

        // One motion preference for the whole interface: section and drawer
        // transitions, the analysis lens, camera presets and the flow cues.
        // It changes how a state change looks, never what state results.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.xs

            Text {
                text: "Motion"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.body
            }

            RFSegmentedControl {
                objectName: "motionControl"
                Layout.fillWidth: true
                model: ["Full", "Reduced", "Off"]
                currentIndex: Math.max(0, ["full", "reduced", "off"].indexOf(Motion.mode))
                onSelected: function (index) { Motion.mode = ["full", "reduced", "off"][index] }
            }
        }

        // Whether resting the pointer on a small-multiple plot previews it.
        // Focus by click works either way.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.xs

            Text {
                text: "Plot hover preview"
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.body
            }

            RFSegmentedControl {
                objectName: "hoverPreviewControl"
                Layout.fillWidth: true
                model: ["On", "Off"]
                currentIndex: Motion.hoverPreview ? 0 : 1
                onSelected: function (index) { Motion.hoverPreview = index === 0 }
            }
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

        // Which build this is: the token a bug report quotes, whether it is a
        // packaged build or a source run, and what it runs on. Read from the
        // build identity (main.current_build), never composed here.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Text {
                Layout.fillWidth: true
                text: "Build " + App.buildId
                color: Theme.textSecondary
                font.family: Typography.mono
                font.pixelSize: Typography.meta
                elide: Text.ElideRight
            }
            Text {
                Layout.fillWidth: true
                text: App.buildChannel + " · " + App.buildMode
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                elide: Text.ElideRight
            }
            Text {
                Layout.fillWidth: true
                text: App.runtimeVersions
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                elide: Text.ElideRight
            }
        }

        RFButton {
            Layout.alignment: Qt.AlignLeft
            text: "Copy build info"
            variant: "quiet"
            compact: true
            onClicked: App.copyBuildInfo()
        }
    }
}
