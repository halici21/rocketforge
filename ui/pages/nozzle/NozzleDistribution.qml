import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The distributed solution, station by station.
 *
 * The two shock stations are two rows sharing an x, marked PRE SHOCK and POST
 * SHOCK. They are never merged and never interpolated between: the jump is the
 * physics, and a table that smoothed it would be reporting something that does
 * not happen.
 *
 * The throat marker says SONIC only when the throat actually is sonic. An
 * unchoked nozzle has a throat, not a sonic point, and saying otherwise on a
 * page about choking would be a poor joke.
 */
Item {
    id: page

    property int selectedRow: -1

    readonly property var station: selectedRow >= 0 ? Nozzle.stationAt(selectedRow) : []

    function markerFor(row) {
        var markers = Nozzle.rowMarkers
        var key = String(row)
        return markers[key] !== undefined ? markers[key] : ""
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 96
            contentSpacing: Metrics.spacing.s

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                ColumnLayout {
                    Layout.preferredWidth: 260
                    spacing: 3
                    RFSectionLabel { text: "Columns" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Dimensional", "Normalized"]
                        currentIndex: Nozzle.normalized ? 1 : 0
                        onSelected: function (index) { Nozzle.normalized = index === 1 }
                    }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 130
                    label: "Stations"
                    value: Nozzle.resolution
                    digits: 0
                    step: 20
                    onValueEdited: function (v) { Nozzle.resolution = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 220
                    spacing: 3
                    RFSectionLabel { text: "Precision" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["4", "6", "8"]
                        currentIndex: Nozzle.tablePrecision === 4 ? 0
                                    : (Nozzle.tablePrecision === 6 ? 1 : 2)
                        onSelected: function (index) {
                            Nozzle.tablePrecision = [4, 6, 8][index]
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                RFButton {
                    text: "Jump to throat"
                    variant: "quiet"
                    compact: true
                    onClicked: page.jumpTo(Nozzle.throatRow)
                }
                RFButton {
                    text: "Jump to shock"
                    variant: "quiet"
                    compact: true
                    enabled: Nozzle.hasShock
                    onClicked: page.jumpTo(Nozzle.preShockRow)
                }
                RFButton {
                    text: "Copy table"
                    variant: "quiet"
                    compact: true
                    onClicked: Nozzle.copyTable()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFPanel {
                title: "Stations"
                Layout.fillWidth: true
                Layout.fillHeight: true

                trailing: Component {
                    RFStatusChip {
                        text: "RocketForge computed"
                        showDot: false
                    }
                }

                RFEngineeringTable {
                    id: table
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    model: Nozzle.tableModel
                    columns: Nozzle.tableColumns
                    markedRow: Nozzle.preShockRow
                    markedLabel: "PRE SHOCK"
                    secondaryRow: Nozzle.postShockRow
                    secondaryLabel: "POST SHOCK"
                    selectedRow: page.selectedRow
                    firstColumnWidth: 96
                    columnWidth: Math.min(170, Math.max(86,
                                 valueAreaWidth / Math.max(1, columns.length - 1)))

                    onRowClicked: function (row) {
                        page.selectedRow = row
                        Nozzle.selectRow(row)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Nozzle.tableCaption
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 250
                Layout.fillHeight: true
                spacing: Metrics.spacing.m

                RFPanel {
                    title: "Station"
                    Layout.fillWidth: true
                    contentSpacing: Metrics.spacing.xs

                    trailing: Component {
                        RFStatusChip {
                            text: page.selectedRow >= 0
                                  ? page.markerFor(page.selectedRow) || ("row "
                                    + (page.selectedRow + 1))
                                  : "none"
                            showDot: false
                        }
                    }

                    RFEmptyState {
                        Layout.fillWidth: true
                        visible: page.selectedRow < 0
                        title: "No station selected"
                        body: "Click a row in the table to inspect it."
                    }

                    Repeater {
                        model: page.station

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 22
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 92
                                text: modelData.label
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.text
                                      + (modelData.unit ? " " + modelData.unit : "")
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutSmall
                            }
                        }
                    }
                }

                RFPanel {
                    title: "Marked stations"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentSpacing: Metrics.spacing.xs

                    Repeater {
                        model: [
                            { label: Nozzle.choked ? "Throat · sonic" : "Throat",
                              row: Nozzle.throatRow, shown: true },
                            { label: "Pre-shock", row: Nozzle.preShockRow,
                              shown: Nozzle.hasShock },
                            { label: "Post-shock", row: Nozzle.postShockRow,
                              shown: Nozzle.hasShock },
                            { label: "Exit", row: Nozzle.exitRow, shown: true }
                        ]

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            visible: modelData.shown && modelData.row >= 0
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            RFButton {
                                text: "row " + (modelData.row + 1)
                                variant: "quiet"
                                compact: true
                                onClicked: page.jumpTo(modelData.row)
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    Text {
                        Layout.fillWidth: true
                        text: "The shock occupies two rows at the same x: the state "
                              + "before it and the state after it. They are kept apart "
                              + "because the jump between them is the result."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }
    }

    function jumpTo(row) {
        if (row < 0)
            return
        page.selectedRow = row
        Nozzle.selectRow(row)
        table.scrollToRow(row)
    }
}
