import QtQuick
import QtQuick.Layouts
import "../../theme"
import "../../components"
import "../model"
import "../visuals"

/*
 * The nozzle design workspace, overview section.
 *
 * Same anatomy as the injector workspace, and the same contour the Nozzle Lab
 * draws in analysis mode - one component, two contexts, one drawing.
 */
ComponentWorkspaceFrame {
    id: root

    tabs: MockEngineData.nozzleTabs
    note: MockEngineData.nozzleNote

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        RFPanel {
            title: "Geometry"
            // The configuration rail is support, not the subject: it is given a
            // working width and no more, so the drawing keeps the rest.
            Layout.preferredWidth: Metrics.configRailWidth
            Layout.minimumWidth: Metrics.configRailMin
            Layout.maximumWidth: Metrics.configRailWidth
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m

            Repeater {
                model: MockEngineData.nozzleInputs

                delegate: ConfigField {
                    required property var modelData
                    Layout.fillWidth: true
                    spec: modelData
                }
            }

            Item { Layout.fillHeight: true }

            RFDivider {}

            Text {
                Layout.fillWidth: true
                text: "Contour points are the hand-authored profile shared with the Nozzle Lab."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            RFPanel {
                title: "Contour"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                trailing: Component {
                    RFStatusChip {
                        text: "Schematic"
                        showDot: false
                    }
                }

                NozzleSchematic {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }

            RFReadoutStrip {
                Layout.fillWidth: true
                title: "Design summary"
                model: MockEngineData.nozzleSummary
            }
        }
    }
}
