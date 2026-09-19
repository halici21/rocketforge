import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * "What design am I looking at?" -- the Selected Design Inspector.
 *
 * The Analysis Dock's Results table answers "what evidence exists across
 * the population"; this answers the single-design question: which design
 * variables produced it, what it evaluated to, whether it is feasible,
 * whether it is Pareto-efficient, its score if the study has one, and
 * whether it failed or carries a warning.
 *
 * Deliberately reuses TradeStudy.compareColumns -- the exact same per-design
 * rows the Compare tab already renders -- rather than a second query path,
 * so the Inspector and Compare can never disagree about one design's own
 * numbers. The inspected design is the most recently selected one (the last
 * entry of TradeStudy.selectedIndices): the same point that carries the
 * gold selection ring on the Pareto plot. Reads only already-computed
 * result data -- selecting or opening this drawer causes zero solves.
 */
Item {
    id: view

    readonly property var columns: TradeStudy.compareColumns
    readonly property var design: columns.length > 0 ? columns[columns.length - 1] : null

    RFPanel {
        anchors.fill: parent
        anchors.margins: Metrics.spacing.m
        title: "Selected design"
        contentSpacing: Metrics.spacing.s

        trailing: Component {
            Row {
                spacing: Metrics.spacing.s

                RFStatusChip {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: TradeStudy.resultStale
                    text: "Setup changed"
                    tone: "warning"
                }
                RFIconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    icon: "close"
                    tooltip: "Close"
                    onClicked: ShellContext.inspectorOpen = false
                }
            }
        }

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: view.design === null
            tag: "NOTHING SELECTED"
            title: "No design selected"
            body: "Tap a point on the design-space plot, or a row in the "
                  + "best-evaluated-points list, to inspect it here."
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: view.design !== null
            spacing: 2

            Text {
                Layout.fillWidth: true
                text: view.design ? view.design.title : ""
                color: Theme.text
                font.family: Typography.sans
                font.pixelSize: Typography.groupLabel
                font.weight: Typography.medium
            }
            Text {
                Layout.fillWidth: true
                text: view.design ? view.design.subtitle : ""
                wrapMode: Text.WordWrap
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                bottomPadding: Metrics.spacing.xs
            }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: view.design !== null
            contentWidth: width
            contentHeight: rows.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {}

            ColumnLayout {
                id: rows
                width: parent.width
                spacing: 1

                Repeater {
                    model: view.design ? view.design.rows : []

                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 1

                        RFSectionLabel {
                            visible: modelData.showGroup
                            text: modelData.group
                            Layout.topMargin: Metrics.spacing.xs
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                wrapMode: Text.WordWrap
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

                // The compromise a sweep asks about: not just this design's
                // raw value (already shown above, under Physics) but how it
                // sits relative to the best this evaluated sweep reached for
                // the same response -- "distance from max" answers "what am
                // I giving up here," in plain numbers rather than a word
                // like "efficiency loss" that would claim a defined
                // quantity this is not.
                RFSectionLabel {
                    visible: TradeStudy.isParametricSweep
                             && TradeStudy.sweepComparisonRows.length > 0
                    text: "Trade-off vs. evaluated maximum"
                    Layout.topMargin: Metrics.spacing.xs
                }

                Repeater {
                    model: TradeStudy.isParametricSweep
                           ? TradeStudy.sweepComparisonRows : []

                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 1

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                wrapMode: Text.WordWrap
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
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: "Evaluated max " + modelData.maxValue
                                color: Theme.textDisabled
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                text: modelData.percentFromMax
                                color: Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }
            }
        }
    }
}
