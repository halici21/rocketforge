import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Generated Prandtl–Meyer table.
 *
 * Every row is computed by RocketForge for the chosen gamma and Mach range.
 * Anderson's Appendix C is never read to produce a value — it is only ever
 * compared against, and only at Mach numbers it actually prints.
 *
 * The default columns are Appendix C's own: M, ν, μ and nothing else. The
 * appendix leaves the isentropic ratios to Appendix A on purpose, and the
 * default here does the same; the Extended set adds them for a working
 * calculation.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 2.0

    function jumpTo(mach) {
        var row = PrandtlMeyer.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        PrandtlMeyer.selectRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        PrandtlMeyer.regenerateTable()
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
                    Layout.preferredWidth: 118
                    label: "γ"
                    value: PrandtlMeyer.tableGamma
                    digits: 4
                    decimals: 4
                    step: 0.005
                    onValueEdited: function (v) { PrandtlMeyer.tableGamma = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Start M"
                    value: PrandtlMeyer.tableStart
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { PrandtlMeyer.tableStart = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "End M"
                    value: PrandtlMeyer.tableEnd
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { PrandtlMeyer.tableEnd = v }
                }
                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Step"
                    value: PrandtlMeyer.tableStep
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { PrandtlMeyer.tableStep = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 200
                    spacing: 3
                    RFSectionLabel { text: "Columns" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Anderson", "Extended"]
                        currentIndex: PrandtlMeyer.tableConvention === "anderson" ? 0 : 1
                        onSelected: function (index) {
                            PrandtlMeyer.tableConvention = index === 0 ? "anderson" : "extended"
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
                        currentIndex: PrandtlMeyer.tablePrecision === 4 ? 0
                                    : PrandtlMeyer.tablePrecision === 6 ? 1 : 2
                        useMonoFont: true
                        onSelected: function (index) {
                            PrandtlMeyer.tablePrecision = [4, 6, 8][index]
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
                    text: "Compare with Anderson Appendix C"
                    checked: PrandtlMeyer.compareEnabled
                    enabled: PrandtlMeyer.referenceAvailable
                    onToggled: PrandtlMeyer.compareEnabled = checked
                }

                Text {
                    Layout.fillWidth: true
                    text: PrandtlMeyer.referenceAvailable ? PrandtlMeyer.referenceCitation
                                                          : PrandtlMeyer.referenceMessage
                    elide: Text.ElideRight
                    color: PrandtlMeyer.referenceAvailable ? Theme.textMuted : Theme.warning
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
                    onClicked: PrandtlMeyer.copyTable()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFPanel {
                title: "Prandtl–Meyer function and Mach angle"
                Layout.fillWidth: true
                Layout.fillHeight: true

                trailing: Component {
                    RFStatusChip { text: "Calculated"; tone: "success"; showDot: false }
                }

                RFEngineeringTable {
                    id: table
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: PrandtlMeyer.tableRowCount > 0

                    model: PrandtlMeyer.tableModel
                    columns: PrandtlMeyer.tableColumns
                    markedRow: PrandtlMeyer.sonicRow
                    markedLabel: "SONIC"
                    selectedRow: page.selectedRow
                    firstColumnWidth: 104
                    showRegionEdge: false
                    columnWidth: Math.min(200, Math.max(130,
                                 (width - 104) / Math.max(1, columns.length - 1)))

                    onRowClicked: function (row) {
                        page.selectedRow = row
                        PrandtlMeyer.selectRow(row)
                    }
                    onRowActivated: function (row) {
                        PrandtlMeyer.setMachAndSolve(PrandtlMeyer.tableModel.machAt(row))
                        PrandtlMeyer.requestTab(0)
                    }
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: PrandtlMeyer.tableRowCount === 0
                    tag: "Table"
                    title: PrandtlMeyer.tableMessage !== "" ? "Table not generated" : "No rows"
                    body: PrandtlMeyer.tableMessage !== "" ? PrandtlMeyer.tableMessage
                                                           : "Adjust the range and press Generate."
                }

                Text {
                    Layout.fillWidth: true
                    text: PrandtlMeyer.tableFooter
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFPanel {
                id: comparison
                title: "Reference comparison"
                Layout.preferredWidth: 372
                Layout.fillHeight: true
                visible: PrandtlMeyer.compareEnabled && PrandtlMeyer.referenceAvailable
                contentSpacing: Metrics.spacing.s

                readonly property var summary: PrandtlMeyer.comparisonSummary
                readonly property var rowDetail: page.selectedRow >= 0
                                                 ? PrandtlMeyer.comparisonForRow(page.selectedRow) : []

                trailing: Component {
                    RFStatusChip {
                        text: comparison.summary.status !== undefined ? comparison.summary.status : "—"
                        tone: comparison.summary.status === "PASS" ? "success" : "warning"
                        showDot: false
                    }
                }

                RFSectionLabel { text: "Whole table" }

                Repeater {
                    model: [
                        { k: "Rows compared", v: comparison.summary.rows !== undefined ? comparison.summary.rows : 0 },
                        { k: "Values compared", v: comparison.summary.values !== undefined ? comparison.summary.values : 0 },
                        { k: "Within printed precision", v: comparison.summary.pass !== undefined ? comparison.summary.pass : 0 },
                        { k: "Needing review", v: comparison.summary.review !== undefined ? comparison.summary.review : 0 },
                        { k: "Max relative difference", v: comparison.summary.maxRelative !== undefined ? comparison.summary.maxRelative : "—" }
                    ]

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.fillWidth: true
                            text: modelData.k
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            text: String(modelData.v)
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                    }
                }

                RFDivider {}

                RFSectionLabel {
                    text: page.selectedRow >= 0
                          ? "Row · M = " + PrandtlMeyer.tableModel.machAt(page.selectedRow).toFixed(4)
                          : "Select a row"
                }

                Text {
                    Layout.fillWidth: true
                    visible: page.selectedRow >= 0 && comparison.rowDetail.length === 0
                    text: "No reference row at this Mach number. Appendix C prints discrete "
                          + "values and nothing is interpolated between them."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Repeater {
                    model: comparison.rowDetail

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        Text {
                            Layout.preferredWidth: 52
                            text: modelData.label
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.computed
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 84
                            text: modelData.reference
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        RFStatusChip {
                            Layout.preferredWidth: 44
                            text: modelData.status
                            tone: modelData.status === "PASS" ? "success" : "warning"
                            showDot: false
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    text: "Published values are rounded to four significant figures. A difference "
                          + "inside that rounding is agreement, not error."
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
