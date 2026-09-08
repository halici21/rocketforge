import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Generated mass-flow table.
 *
 * Every row is computed by RocketForge for the chosen gamma and Mach range.
 *
 * There is no reference-comparison panel here, and that absence is deliberate
 * and stated on the page: Anderson publishes no mass-flow appendix, so there
 * is no printed table to compare against. Inventing one, or quietly comparing
 * against something else and calling it Anderson, would be worse than saying
 * so plainly.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 1.0

    function jumpTo(mach) {
        var row = MassFlow.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        MassFlow.selectRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        MassFlow.regenerateTable()
        page.selectedRow = -1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        // ---- controls -------------------------------------------------------
        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 108
            contentSpacing: Metrics.spacing.s

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "γ"
                    value: MassFlow.tableGamma
                    digits: 4
                    decimals: 4
                    step: 0.005
                    onValueEdited: function (v) { MassFlow.tableGamma = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Start M"
                    value: MassFlow.tableStart
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { MassFlow.tableStart = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "End M"
                    value: MassFlow.tableEnd
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { MassFlow.tableEnd = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Step"
                    value: MassFlow.tableStep
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { MassFlow.tableStep = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 220
                    spacing: 3
                    RFSectionLabel { text: "Columns" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Dimensionless", "kg/s"]
                        currentIndex: MassFlow.tableConvention === "dimensionless" ? 0 : 1
                        onSelected: function (index) {
                            MassFlow.tableConvention = index === 0 ? "dimensionless" : "dimensional"
                            page.applySettings()
                        }
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: 150
                    spacing: 3
                    RFSectionLabel { text: "Precision" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["4", "6", "8"]
                        currentIndex: MassFlow.tablePrecision === 4 ? 0
                                    : MassFlow.tablePrecision === 6 ? 1 : 2
                        useMonoFont: true
                        onSelected: function (index) {
                            MassFlow.tablePrecision = [4, 6, 8][index]
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                RFButton {
                    text: "Generate"
                    variant: "primary"
                    onClicked: page.applySettings()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                RFToggle {
                    text: "Insert the sonic row"
                    checked: MassFlow.includeSonic
                    onToggled: MassFlow.includeSonic = checked
                }

                Text {
                    Layout.fillWidth: true
                    text: MassFlow.referenceMessage
                    elide: Text.ElideRight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 132
                    label: "Jump to M"
                    value: page.jumpMach
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { page.jumpMach = v }
                }

                RFButton {
                    text: "Go"
                    variant: "quiet"
                    compact: true
                    onClicked: page.jumpTo(page.jumpMach)
                }

                RFButton {
                    text: "Copy table"
                    variant: "quiet"
                    compact: true
                    onClicked: MassFlow.copyTable()
                }
            }
        }

        // ---- table ----------------------------------------------------------
        RFPanel {
            title: "Mass flow properties"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                RFStatusChip {
                    text: "Calculated"
                    tone: "success"
                    showDot: false
                }
            }

            RFEngineeringTable {
                id: table
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: MassFlow.tableRowCount > 0

                model: MassFlow.tableModel
                columns: MassFlow.tableColumns
                markedRow: MassFlow.sonicRow
                markedLabel: "CHOKED"
                selectedRow: page.selectedRow
                firstColumnWidth: 104
                columnWidth: Math.min(190, Math.max(126,
                             (width - 104) / Math.max(1, columns.length - 1)))

                onRowClicked: function (row) {
                    page.selectedRow = row
                    MassFlow.selectRow(row)
                }
                onRowActivated: function (row) {
                    MassFlow.setMachAndSolve(MassFlow.tableModel.machAt(row))
                    MassFlow.requestTab(0)
                }
            }

            RFEmptyState {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: MassFlow.tableRowCount === 0
                tag: "Table"
                title: MassFlow.tableMessage !== "" ? "Table not generated" : "No rows"
                body: MassFlow.tableMessage !== "" ? MassFlow.tableMessage
                                                   : "Adjust the range and press Generate."
            }

            Text {
                Layout.fillWidth: true
                text: MassFlow.tableFooter
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
