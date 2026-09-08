import QtQuick
import QtQuick.Layouts
import "../../theme"
import "../../components"
import "../model"
import "../visuals"

/*
 * The injector design workspace, overview section.
 *
 * Configuration on the left, the element drawn on the right, and a summary
 * band underneath whose values are the ones that will need the solver. Those
 * rows stay as em dashes rather than being filled with plausible numbers.
 *
 * The proportions are the argument: the inputs are bounded to a rail and the
 * drawing takes everything left over, so the element section holds roughly two
 * thirds of the page at any width worth working at. A form that grows to fill
 * the screen is a form the reader has to search; the geometry is the thing
 * being designed here, and it is what should be large.
 */
ComponentWorkspaceFrame {
    id: root

    tabs: MockEngineData.injectorTabs
    note: MockEngineData.injectorNote

    // A quiet property line for the rail: the workspace shows a couple of
    // derived quantities beside its inputs without pulling in the inspector.
    component DerivedRow: Item {
        id: row
        property string label: ""
        property string value: ""

        implicitHeight: 22

        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: row.label
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.bodySmall
        }
        Text {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: row.value
            color: row.value === "—" ? Theme.textDisabled : Theme.text
            font.family: Typography.mono
            font.pixelSize: Typography.readoutSmall
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        RFPanel {
            title: "Configuration"
            // The configuration rail is support, not the subject: it is given a
            // working width and no more, so the drawing keeps the rest.
            Layout.preferredWidth: Metrics.configRailWidth
            Layout.minimumWidth: Metrics.configRailMin
            Layout.maximumWidth: Metrics.configRailWidth
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m

            Repeater {
                model: MockEngineData.injectorInputs

                delegate: ConfigField {
                    required property var modelData
                    Layout.fillWidth: true
                    spec: modelData
                }
            }

            Item { Layout.fillHeight: true }

            RFDivider {}

            DerivedRow { Layout.fillWidth: true; label: "Feed pressure"; value: "—" }
            DerivedRow { Layout.fillWidth: true; label: "Mixture ratio"; value: "—" }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            RFPanel {
                title: "Element section"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                trailing: Component {
                    RFStatusChip {
                        text: "Schematic"
                        showDot: false
                    }
                }

                InjectorSchematic {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }

            RFReadoutStrip {
                Layout.fillWidth: true
                title: "Design summary"
                model: MockEngineData.injectorSummary
            }
        }
    }
}
