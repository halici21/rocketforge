import QtQuick
import QtQuick.Layouts
import "../theme"
import "../components"

/*
 * The shared skeleton for modules that are navigable but not yet built.
 *
 * Rather than an empty surface, the page shows the anatomy every analysis
 * module will be built to: the same rail, visualisation, readout and reference
 * regions as the Isentropic Flow page, drawn as reserved space. It states what
 * is missing and what will occupy the room.
 */
Item {
    id: root

    property string title: ""
    property string subtitle: ""
    property var planned: []
    property string note: "Module UI will be implemented in a later phase."

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.pagePadding
        spacing: Metrics.spacing.l

        RFPageHeader {
            Layout.fillWidth: true
            title: root.title
            subtitle: root.subtitle

            trailing: Component {
                RFStatusChip {
                    text: "Planned"
                    tone: "neutral"
                }
            }
        }

        RFPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.xxl

                Item { Layout.fillHeight: true }

                RFEmptyState {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: Math.min(root.width - Metrics.spacing.h2 * 4, 520)
                    tag: "Later phase"
                    title: root.note
                    body: "The navigation entry, the page frame and the design system are in "
                          + "place. The regions below are reserved for this module and follow "
                          + "the same layout language as the Isentropic Flow page."
                    bullets: root.planned
                }

                // Reserved anatomy: the shape every analysis module will fill.
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: Math.min(root.width - Metrics.spacing.h2 * 4, 760)
                    Layout.preferredHeight: Math.min(300, root.height * 0.36)

                    RowLayout {
                        anchors.fill: parent
                        spacing: Metrics.spacing.s

                        RFDashedFrame {
                            Layout.preferredWidth: 170
                            Layout.fillHeight: true
                            label: "Inputs"
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: Metrics.spacing.s

                            RFDashedFrame {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                label: "Visualisation"
                            }

                            RFDashedFrame {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                label: "Readout"
                            }

                            RowLayout {
                                // Nested layouts fill by default; this row is
                                // a fixed band under the readout.
                                Layout.fillHeight: false
                                Layout.fillWidth: true
                                Layout.preferredHeight: 64
                                spacing: Metrics.spacing.s

                                RFDashedFrame {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    label: "Equation"
                                }
                                RFDashedFrame {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    label: "Assumptions"
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
