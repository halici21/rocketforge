import QtQuick
import QtQuick.Layouts
import "../../theme"
import "../../components"
import "../model"

/*
 * The workspace for a component whose design module does not exist yet.
 *
 * It uses the real frame and shows the anatomy the module will fill, so that
 * opening a pump reads as "not built yet" rather than "broken".
 */
ComponentWorkspaceFrame {
    id: root

    tabs: ["Overview"]

    RFPanel {
        anchors.fill: parent

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.xxl

            Item { Layout.fillHeight: true }

            RFEmptyState {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(root.width - Metrics.spacing.h2 * 4, 520)
                tag: "Later phase"
                title: (root.definition ? root.definition.displayName : "Component")
                       + " design will be implemented in a later phase."
                body: "The component exists in the architecture and can be connected, named "
                      + "and inspected. Its design workspace will follow the same layout as "
                      + "the injector and nozzle workspaces."
                bullets: ["Configuration", "Schematic", "Summary"]
            }

            Item {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(root.width - Metrics.spacing.h2 * 4, 700)
                Layout.preferredHeight: Math.min(240, root.height * 0.32)

                RowLayout {
                    anchors.fill: parent
                    spacing: Metrics.spacing.s

                    RFDashedFrame {
                        Layout.preferredWidth: 168
                        Layout.fillHeight: true
                        label: "Configuration"
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: Metrics.spacing.s

                        RFDashedFrame {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            label: "Schematic"
                        }
                        RFDashedFrame {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 46
                            label: "Summary"
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
