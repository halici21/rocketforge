import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Generated isentropic table.
 *
 * Every row here is computed by RocketForge for the chosen gamma and Mach
 * range. The published table is never read to produce a value - it is only
 * ever compared against, and only at Mach numbers it actually prints.
 *
 * The default column set deliberately matches the classical appendix
 * orientation (p0/p, rho0/rho, T0/T) because that is what a reader has in
 * front of them; the backend computes its canonical ratios and the adapter
 * takes the reciprocal.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 1.0

    // Numeric navigation rather than a text search: nobody looks for a string
    // in a table of numbers, they look for a Mach number.
    function jumpTo(mach) {
        var row = Isentropic.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        Isentropic.selectRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        Isentropic.regenerateTable()
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
                    value: Isentropic.tableGamma
                    digits: 4
                    decimals: 4
                    step: 0.005
                    onValueEdited: function (v) { Isentropic.tableGamma = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Start M"
                    value: Isentropic.tableStart
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { Isentropic.tableStart = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "End M"
                    value: Isentropic.tableEnd
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { Isentropic.tableEnd = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Step"
                    value: Isentropic.tableStep
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { Isentropic.tableStep = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 190
                    spacing: 3
                    RFSectionLabel { text: "Format" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Anderson", "Standard"]
                        currentIndex: Isentropic.tableConvention === "anderson" ? 0 : 1
                        onSelected: function (index) {
                            Isentropic.tableConvention = index === 0 ? "anderson" : "standard"
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
                        currentIndex: Isentropic.tablePrecision === 4 ? 0
                                    : Isentropic.tablePrecision === 6 ? 1 : 2
                        useMonoFont: true
                        onSelected: function (index) {
                            Isentropic.tablePrecision = [4, 6, 8][index]
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
                    text: "Compare with Anderson Appendix A"
                    checked: Isentropic.compareEnabled
                    enabled: Isentropic.referenceAvailable
                    onToggled: Isentropic.compareEnabled = checked
                }

                Text {
                    Layout.fillWidth: true
                    text: Isentropic.referenceAvailable ? Isentropic.referenceCitation
                                                        : Isentropic.referenceMessage
                    elide: Text.ElideRight
                    color: Isentropic.referenceAvailable ? Theme.textMuted : Theme.warning
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
                    onClicked: Isentropic.copyTable()
                }
            }
        }

        // ---- table + comparison --------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFPanel {
                title: "Isentropic properties"
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
                    visible: Isentropic.tableRowCount > 0

                    model: Isentropic.tableModel
                    columns: Isentropic.tableColumns
                    markedRow: Isentropic.sonicRow
                    selectedRow: page.selectedRow
                    firstColumnWidth: 104
                    // Capped: a numeric column wider than about 190 px pushes
                    // the figures too far apart to scan across a row.
                    columnWidth: Math.min(190, Math.max(126,
                                 (width - 104) / Math.max(1, columns.length - 1)))

                    onRowClicked: function (row) {
                        page.selectedRow = row
                        Isentropic.selectRow(row)
                    }
                    onRowActivated: function (row) {
                        Isentropic.setMachAndSolve(Isentropic.tableModel.machAt(row))
                        Isentropic.requestTab(0)
                    }
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Isentropic.tableRowCount === 0
                    tag: "Table"
                    title: Isentropic.tableMessage !== "" ? "Table not generated"
                                                          : "No rows"
                    body: Isentropic.tableMessage !== "" ? Isentropic.tableMessage
                                                         : "Adjust the range and press Generate."
                }

                Text {
                    Layout.fillWidth: true
                    text: Isentropic.tableFooter
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            // ---- reference detail ------------------------------------------
            RFPanel {
                id: comparison
                title: "Reference comparison"
                Layout.preferredWidth: 372
                Layout.fillHeight: true
                visible: Isentropic.compareEnabled && Isentropic.referenceAvailable
                contentSpacing: Metrics.spacing.s

                readonly property var summary: Isentropic.comparisonSummary
                readonly property var rowDetail: page.selectedRow >= 0
                                                 ? Isentropic.comparisonForRow(page.selectedRow) : []

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
                          ? "Row · M = " + Isentropic.tableModel.machAt(page.selectedRow).toFixed(4)
                          : "Select a row"
                }

                Text {
                    Layout.fillWidth: true
                    visible: page.selectedRow >= 0 && comparison.rowDetail.length === 0
                    text: "No reference row at this Mach number. Appendix A prints discrete "
                          + "values and nothing is interpolated between them."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: comparison.rowDetail.length > 0
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.preferredWidth: 52
                        text: "Qty"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "RocketForge"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 84
                        text: "Anderson"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 44
                        text: ""
                    }
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
