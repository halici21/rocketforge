import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Oblique shock parameter study.
 *
 * Called a Study rather than a Table because that is what it is: a sweep of
 * the flow deflection at one upstream Mach number, not a tabulation of a
 * single relation. Every row is computed by RocketForge.
 *
 * The sweep is capped at the attachment limit rather than filled with
 * substituted rows. Past θ_max there is no attached shock, and a table that
 * kept going would be the worst possible way to say so — so the range is cut,
 * the last row is the merged solution at θ_max, and the footer says the cap
 * happened.
 */
Item {
    id: page

    property int selectedRow: -1

    function applySettings() {
        ObliqueShock.regenerateTable()
        page.selectedRow = -1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 108
            contentSpacing: Metrics.spacing.s

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.m

                RFBoundNumberField {
                    Layout.preferredWidth: 112
                    label: "M₁"
                    value: ObliqueShock.tableMach1
                    digits: 4
                    decimals: 4
                    step: 0.1
                    onValueEdited: function (v) { ObliqueShock.tableMach1 = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 112
                    label: "γ"
                    value: ObliqueShock.tableGamma
                    digits: 4
                    decimals: 4
                    step: 0.005
                    onValueEdited: function (v) { ObliqueShock.tableGamma = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 112
                    label: "Start θ  [°]"
                    value: ObliqueShock.tableStart
                    digits: 3
                    decimals: 3
                    step: 1
                    onValueEdited: function (v) { ObliqueShock.tableStart = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 112
                    label: "End θ  [°]"
                    value: ObliqueShock.tableEnd
                    digits: 3
                    decimals: 3
                    step: 1
                    onValueEdited: function (v) { ObliqueShock.tableEnd = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 112
                    label: "Step  [°]"
                    value: ObliqueShock.tableStep
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { ObliqueShock.tableStep = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 180
                    spacing: 3
                    RFSectionLabel { text: "Precision" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["4", "6", "8"]
                        currentIndex: ObliqueShock.tablePrecision === 4 ? 0
                                    : ObliqueShock.tablePrecision === 6 ? 1 : 2
                        useMonoFont: true
                        onSelected: function (index) {
                            ObliqueShock.tablePrecision = [4, 6, 8][index]
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

                ColumnLayout {
                    Layout.preferredWidth: 240
                    spacing: 3
                    RFSectionLabel { text: "Columns" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["One branch", "Weak vs strong"]
                        currentIndex: ObliqueShock.tableConvention === "branch" ? 0 : 1
                        onSelected: function (index) {
                            ObliqueShock.tableConvention = index === 0 ? "branch" : "comparison"
                            page.applySettings()
                        }
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: 200
                    spacing: 3
                    visible: ObliqueShock.tableConvention === "branch"
                    RFSectionLabel { text: "Branch" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Weak", "Strong"]
                        currentIndex: ObliqueShock.tableBranch === "weak" ? 0 : 1
                        onSelected: function (index) {
                            ObliqueShock.tableBranch = index === 0 ? "weak" : "strong"
                            page.applySettings()
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    visible: ObliqueShock.tableCapped
                    text: "Range capped at the attachment limit — no attached shock exists above it."
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFButton {
                    text: "Copy table"
                    variant: "quiet"
                    compact: true
                    onClicked: ObliqueShock.copyTable()
                }
            }
        }

        RFPanel {
            title: "Deflection sweep"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                RFStatusChip { text: "Calculated"; tone: "success"; showDot: false }
            }

            RFEngineeringTable {
                id: table
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ObliqueShock.tableRowCount > 0

                model: ObliqueShock.tableModel
                columns: ObliqueShock.tableColumns
                markedRow: ObliqueShock.sonicRow
                markedLabel: "θ_max"
                selectedRow: page.selectedRow
                firstColumnWidth: 104
                showRegionEdge: false
                columnWidth: Math.min(190, Math.max(120,
                             (width - 104) / Math.max(1, columns.length - 1)))

                onRowClicked: function (row) {
                    page.selectedRow = row
                    ObliqueShock.selectRow(row)
                }
                onRowActivated: function (row) {
                    ObliqueShock.setDeflectionAndSolve(ObliqueShock.tableModel.machAt(row))
                    ObliqueShock.requestTab(0)
                }
            }

            RFEmptyState {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ObliqueShock.tableRowCount === 0
                tag: "Study"
                title: ObliqueShock.tableMessage !== "" ? "Study not generated" : "No rows"
                body: ObliqueShock.tableMessage !== "" ? ObliqueShock.tableMessage
                                                       : "Adjust the range and press Generate."
            }

            Text {
                Layout.fillWidth: true
                text: ObliqueShock.tableFooter
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                text: "The final row is the maximum deflection this Mach number can turn: the "
                      + "weak and strong solutions merge there into one wave angle."
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
