import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Generated normal-shock table.
 *
 * Every row here is computed by RocketForge for the chosen gamma and range of
 * upstream Mach numbers. Anderson's Appendix B is never read to produce a
 * value - it is only ever compared against, and only at Mach numbers it
 * actually prints.
 *
 * The default column set matches the published appendix column for column, so
 * a reader can set the two side by side; the Extended set adds the entropy
 * rise and the sonic-area growth, which the appendix omits and a nozzle
 * calculation needs.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 2.0

    function jumpTo(mach) {
        var row = NormalShock.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        NormalShock.selectRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        NormalShock.regenerateTable()
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
                    value: NormalShock.tableGamma
                    digits: 4
                    decimals: 4
                    step: 0.005
                    onValueEdited: function (v) { NormalShock.tableGamma = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Start M₁"
                    value: NormalShock.tableStart
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { NormalShock.tableStart = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "End M₁"
                    value: NormalShock.tableEnd
                    digits: 3
                    decimals: 3
                    step: 0.1
                    onValueEdited: function (v) { NormalShock.tableEnd = v }
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 118
                    label: "Step"
                    value: NormalShock.tableStep
                    digits: 3
                    decimals: 3
                    step: 0.01
                    onValueEdited: function (v) { NormalShock.tableStep = v }
                }

                ColumnLayout {
                    Layout.preferredWidth: 200
                    spacing: 3
                    RFSectionLabel { text: "Columns" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: ["Anderson", "Extended"]
                        currentIndex: NormalShock.tableConvention === "anderson" ? 0 : 1
                        onSelected: function (index) {
                            NormalShock.tableConvention = index === 0 ? "anderson" : "extended"
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
                        currentIndex: NormalShock.tablePrecision === 4 ? 0
                                    : NormalShock.tablePrecision === 6 ? 1 : 2
                        useMonoFont: true
                        onSelected: function (index) {
                            NormalShock.tablePrecision = [4, 6, 8][index]
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
                    text: "Compare with Anderson Appendix B"
                    checked: NormalShock.compareEnabled
                    enabled: NormalShock.referenceAvailable
                    onToggled: NormalShock.compareEnabled = checked
                }

                Text {
                    Layout.fillWidth: true
                    text: NormalShock.referenceAvailable ? NormalShock.referenceCitation
                                                         : NormalShock.referenceMessage
                    elide: Text.ElideRight
                    color: NormalShock.referenceAvailable ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFBoundNumberField {
                    Layout.preferredWidth: 132
                    label: "Jump to M₁"
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
                    onClicked: NormalShock.copyTable()
                }
            }
        }

        // ---- table + comparison --------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.m

            RFPanel {
                title: "Normal shock properties"
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
                    visible: NormalShock.tableRowCount > 0

                    model: NormalShock.tableModel
                    columns: NormalShock.tableColumns
                    markedRow: NormalShock.sonicRow
                    markedLabel: "M₁ = 1"
                    selectedRow: page.selectedRow
                    firstColumnWidth: 104
                    // The whole table is supersonic, so the shaded region edge
                    // the isentropic table uses would mark nothing here.
                    showRegionEdge: false
                    columnWidth: Math.min(190, Math.max(120,
                                 (width - 104) / Math.max(1, columns.length - 1)))

                    onRowClicked: function (row) {
                        page.selectedRow = row
                        NormalShock.selectRow(row)
                    }
                    onRowActivated: function (row) {
                        NormalShock.setMachAndSolve(NormalShock.tableModel.machAt(row))
                        NormalShock.requestTab(0)
                    }
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: NormalShock.tableRowCount === 0
                    tag: "Table"
                    title: NormalShock.tableMessage !== "" ? "Table not generated" : "No rows"
                    body: NormalShock.tableMessage !== "" ? NormalShock.tableMessage
                                                          : "Adjust the range and press Generate."
                }

                Text {
                    Layout.fillWidth: true
                    readonly property string plainText: NormalShock.tableFooter
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
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
                visible: NormalShock.compareEnabled && NormalShock.referenceAvailable
                contentSpacing: Metrics.spacing.s

                readonly property var summary: NormalShock.comparisonSummary
                readonly property var rowDetail: page.selectedRow >= 0
                                                 ? NormalShock.comparisonForRow(page.selectedRow) : []

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

                Text {
                    Layout.fillWidth: true
                    visible: comparison.summary.review !== undefined && comparison.summary.review > 0
                    text: NormalShock.referenceNote
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFDivider {}

                RFSectionLabel {
                    readonly property string plainText: page.selectedRow >= 0
                          ? "Row · M₁ = " + NormalShock.tableModel.machAt(page.selectedRow).toFixed(4)
                          : "Select a row"
                    text: Notation.sectionRich(plainText)
                    textFormat: Notation.textFormat(plainText)
                }

                Text {
                    Layout.fillWidth: true
                    visible: page.selectedRow >= 0 && comparison.rowDetail.length === 0
                    text: "No reference row at this Mach number. Appendix B prints discrete "
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
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
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
