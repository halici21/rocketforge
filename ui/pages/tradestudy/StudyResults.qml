import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Every evaluated point, with its raw physics intact.
 *
 * The table contains successful, infeasible and failed points by default. A
 * filter hides rows; it never removes them, and the underlying study result
 * keeps all of them however the view is set. A design space with holes in it
 * is information: the holes are where the model stops working, and a table
 * that quietly dropped those rows would imply the space is continuous.
 *
 * A failed row shows an em dash for the metrics it could not produce - never a
 * zero, which would be a physical claim about an engine rather than the
 * absence of one.
 *
 * Status and feasibility are separate columns because they answer different
 * questions: whether the model produced an answer, and whether that answer is
 * a design anyone may choose.
 */
Item {
    id: view

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: !TradeStudy.hasResult
            tag: "NO STUDY"
            title: "No study has been run"
            body: "Define the variables, objectives and constraints on the "
                  + "Setup tab, then press Run Study. Nothing is shown here "
                  + "until a design space has actually been evaluated."
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.hasResult
            spacing: Metrics.spacing.m

            RFComboBox {
                Layout.preferredWidth: 190
                label: "Show"
                model: TradeStudy.filterOptions.map(function (o) { return o.label })
                onActivated: function (index) {
                    var options = TradeStudy.filterOptions
                    if (index >= 0 && index < options.length)
                        TradeStudy.filterMode = options[index].key
                }
            }

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: TradeStudy.visibleRowCount + " rows shown · "
                      + TradeStudy.solveReuseNote
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Item { Layout.fillWidth: true }

            RFStatusChip {
                Layout.alignment: Qt.AlignVCenter
                visible: TradeStudy.resultStale
                text: "Setup changed"
                tone: "warning"
            }
        }

        Text {
            Layout.fillWidth: true
            visible: TradeStudy.hasResult && TradeStudy.message !== ""
            text: TradeStudy.message
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.warning
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        RFEngineeringTable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: TradeStudy.hasResult
            model: TradeStudy.resultsModel
            columns: TradeStudy.resultColumns
            firstColumnWidth: 56
            columnWidth: 142
        }

        // ---- summary, provenance and aggregated diagnostics -------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: 168
            visible: TradeStudy.hasResult
            spacing: Metrics.spacing.m

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "Study summary"
                contentSpacing: Metrics.spacing.xs

                Flow {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.l

                    Repeater {
                        model: TradeStudy.summaryRows

                        delegate: Row {
                            required property var modelData
                            spacing: Metrics.spacing.xs

                            Text {
                                text: modelData.label
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                text: modelData.value
                                color: Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xs
                    text: "Design points and chamber solves are different "
                          + "numbers. The nozzle-stage variables cost no "
                          + "chemistry, which is why the second is usually the "
                          + "smaller."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFPanel {
                Layout.preferredWidth: 440
                Layout.fillHeight: true
                title: "Diagnostics and provenance"
                contentSpacing: Metrics.spacing.xs

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: notes.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: notes
                        width: parent.width
                        spacing: 2

                        Repeater {
                            model: TradeStudy.diagnosticRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.code
                                    elide: Text.ElideRight
                                    color: modelData.severity === "warning"
                                           ? Theme.warning : Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    text: modelData.summary
                                    color: Theme.textDisabled
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }

                        RFDivider { Layout.fillWidth: true }

                        Repeater {
                            model: TradeStudy.provenanceRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.preferredWidth: 152
                                    text: modelData.label
                                    wrapMode: Text.WordWrap
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.value
                                    wrapMode: Text.WordWrap
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
