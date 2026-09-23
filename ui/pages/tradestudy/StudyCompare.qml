import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * A small number of designs, side by side.
 *
 * Four at most. A comparison a person can hold in their head is worth more
 * than one they have to scroll, and beyond four the columns are too narrow to
 * read a number in.
 *
 * The raw physics comes first and the score - if there is one - is the last
 * row of the last group. That ordering is the argument: a score is a summary
 * of the numbers above it, and a reader must always be able to see what
 * produced it rather than being asked to trust it.
 *
 * Violated constraints are listed with the value that violated them. "3610 K
 * violates <= 3500 K" is something a person can act on; "infeasible" is not.
 */
Item {
    id: view

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: TradeStudy.compareColumns.length === 0
            tag: "NOTHING SELECTED"
            title: "No designs selected"
            body: "Select up to " + TradeStudy.maximumComparisons
                  + " evaluated designs from the Pareto plot or the best-point "
                  + "list, and they will be compared here."
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.compareColumns.length > 0
            spacing: Metrics.spacing.m

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: TradeStudy.compareColumns.length + " of "
                      + TradeStudy.maximumComparisons + " selected"
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Item { Layout.fillWidth: true }

            RFButton {
                text: "Clear selection"
                variant: "quiet"
                onClicked: TradeStudy.clearSelection()
            }
        }

        Text {
            Layout.fillWidth: true
            visible: TradeStudy.selectedViolations.length > 0
            text: "Violated constraints among the selected designs:"
            color: Theme.warning
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        Repeater {
            model: TradeStudy.selectedViolations

            delegate: Text {
                required property var modelData
                Layout.fillWidth: true
                Layout.fillHeight: false
                text: "Point " + modelData.index + " — " + modelData.text
                wrapMode: Text.WordWrap
                color: Theme.warning
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: TradeStudy.compareColumns.length > 0
            contentWidth: width
            contentHeight: columns.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {}

            RowLayout {
                id: columns
                width: parent.width
                spacing: Metrics.spacing.m

                Repeater {
                    model: TradeStudy.compareColumns

                    delegate: RFPanel {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        title: modelData.title
                        contentSpacing: 2

                        trailing: Component {
                            RFIconButton {
                                icon: "close"
                                tooltip: "Remove from comparison"
                                onClicked: TradeStudy.toggleSelection(
                                               modelData.index)
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: modelData.subtitle
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                            bottomPadding: Metrics.spacing.xs
                        }

                        Repeater {
                            model: modelData.rows

                            delegate: ColumnLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
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
                                        text: Notation.rich(modelData.label)
                                        textFormat: Notation.textFormat(modelData.label)
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
                    }
                }

                Item { Layout.fillWidth: true }
            }
        }
    }
}
