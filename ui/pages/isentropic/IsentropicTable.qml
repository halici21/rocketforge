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
 *
 * The table is an interactive data surface (RFEngineeringTable's shared
 * contract): a row selects the chart's exact sample and the inspector; a
 * range draws a quiet interval on the chart (it never zooms it) and can be
 * opened as a lens or pinned as a table snapshot in the one AnalysisSession.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 1.0

    // The settings start closed on a short page (the 1366 x 768 floor), once:
    // after that the drawer is the reader's.
    property bool sized: false
    onHeightChanged: {
        if (!page.sized && page.height > 0) {
            page.sized = true
            if (page.height < 700)
                settings.open = false
        }
    }

    // Numeric navigation rather than a text search: nobody looks for a string
    // in a table of numbers, they look for a Mach number.
    function jumpTo(mach) {
        var row = Isentropic.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        Isentropic.selectRow(row)
        Isentropic.selectTableRow(row)
        table.scrollToRow(row)
    }

    // Each column with the backend's own word for its quantity, from the
    // solve-mode registry keyed by the same column key ("Density ratio" for
    // rho0_over_rho). Presentation only: the column model is unchanged.
    function captionFor(key) {
        var modes = Isentropic.solveModes
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return modes[i].label
        return ""
    }
    readonly property var captionedColumns: Isentropic.tableColumns.map(function (c) {
        return { key: c.key, label: c.label, unit: c.unit,
                 decimals_hint: c.decimals_hint, caption: page.captionFor(c.key) }
    })

    function applySettings() {
        Isentropic.regenerateTable()
        page.selectedRow = -1
    }

    // The rows a Pin or Copy means: the range, else the lens, else the row.
    function activeBlock() {
        if (table.hasRange)
            return [table.rangeFirst, table.rangeLast]
        if (table.lensActive)
            return [table.lensFirst, table.lensLast]
        if (page.selectedRow >= 0)
            return [page.selectedRow, page.selectedRow]
        return null
    }
    function pinBlock() {
        var block = page.activeBlock()
        if (block === null)
            return
        var snap = Isentropic.tableSnapshot(block[0], block[1])
        if (snap.kind === undefined)
            return
        var id = AnalysisSession.pin(snap)
        page.snapMessage = id !== "" ? "Pinned " + id + " · " + snap.rangeLabel
                                     : "Not pinned: " + AnalysisSession.lastError
    }
    function copyBlock() {
        var block = page.activeBlock()
        if (block === null)
            Isentropic.copyTable()
        else
            Isentropic.copyTableRows(block[0], block[1])
    }

    // ---- pinned table snapshots (RFTableSnapshotStrip) ----------------------
    property string snapMessage: ""

    // Restore: the same rows of the current table, as a range and a lens. A
    // snapshot from a table generated with other settings is not forced onto
    // this one -- its rows stay in the snapshot, and the reason is said.
    function restoreSnap(s) {
        var a = s.identity === Isentropic.tableIdentity ? s.firstRow : Isentropic.rowExactly(s.rowKeys[0])
        var b = s.identity === Isentropic.tableIdentity ? s.lastRow
                                                         : Isentropic.rowExactly(s.rowKeys[s.rowKeys.length - 1])
        if (a < 0 || b < 0 || b - a + 1 !== s.rowKeys.length) {
            page.snapMessage = s.id + " comes from another table (γ " + s.gamma
                               + "); generate that table to restore it. Its rows are kept in the snapshot."
            return
        }
        table.selectRange(a, b)
        table.enterLens(a, b)
        page.snapMessage = "Restored " + s.id + " · " + s.rangeLabel
    }

    // The shared selection drives the table too: a point picked on the chart
    // selects its row here; a range restored elsewhere shows as a range.
    Connections {
        target: Isentropic.selection
        function onChanged() {
            var sel = Isentropic.selection
            if (sel.kind === "plotPoint" || sel.kind === "tableRow") {
                var row = Isentropic.rowExactly(sel.x)
                if (row >= 0 && row !== page.selectedRow) {
                    page.selectedRow = row
                    table.clearRange()
                }
            } else if (sel.kind === "") {
                page.selectedRow = -1
                table.clearRange()
            }
        }
    }
    Connections {
        target: Isentropic
        function onTableChanged() {
            table.clearRange()
            table.exitLens()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        // ---- controls -------------------------------------------------------
        // The generation settings, collapsible to one line that still names
        // the table on screen, so on a short window the rows get the room.
        // Open by default; closed from the start below 700 px of page height.
        RFBottomDrawer {
            id: settings
            objectName: "isentropicTableSettings"
            Layout.fillWidth: true
            Layout.preferredHeight: settings.implicitHeight
            title: "Table settings"
            summary: "γ " + (+Number(Isentropic.plottedGamma).toPrecision(4)) + "  ·  "
                     + Isentropic.tableRowCount + " rows  ·  "
                     + (Isentropic.tableConvention === "anderson" ? "Anderson" : "Standard")
                     + " format  ·  " + Isentropic.tablePrecision + " digits"
            open: true
            drawerHeight: settings.handleHeight + Metrics.spacing.s + controls.implicitHeight

        // Sized to its two rows of controls (a fixed height clipped the
        // Jump to M field at the foot of the panel).
        RFPanel {
            id: controls
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
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

                Item { Layout.fillWidth: true }

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

                RFTableToolbar {
                    Layout.fillWidth: true
                    visible: Isentropic.tableRowCount > 0
                    table: table
                    canPin: true
                    canCopy: true
                    onPinRequested: page.pinBlock()
                    onCopyRequested: page.copyBlock()
                }

                RFEngineeringTable {
                    id: table
                    objectName: "isentropicTable"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: Isentropic.tableRowCount > 0
                    interactive: true

                    model: Isentropic.tableModel
                    columns: page.captionedColumns
                    markedRow: Isentropic.sonicRow
                    selectedRow: page.selectedRow
                    firstColumnWidth: 104
                    // The floor for a value column. RFEngineeringTable shares
                    // any width beyond it across the value columns, so the
                    // table always spans the panel; the first column stays
                    // narrow because it holds only M.
                    columnWidth: Math.min(190, Math.max(126,
                                 (width - 104) / Math.max(1, columns.length - 1)))

                    onRowClicked: function (row) {
                        page.selectedRow = row
                        Isentropic.selectRow(row)
                        Isentropic.selectTableRow(row)
                    }
                    onRangeSelected: function (first, last) {
                        page.selectedRow = -1
                        Isentropic.selectTableRange(first, last)
                    }
                    onEscapePressed: Isentropic.selection.clear()
                    onRowActivated: function (row) {
                        Isentropic.setMachAndSolve(Isentropic.tableModel.machAt(row))
                        Isentropic.requestTab(0)
                    }
                }

                // Pinned table snapshots: A/B picks a pair to difference
                // (row-aligned by M); Restore reopens the rows as a lens.
                RFTableSnapshotStrip {
                    objectName: "isentropicTableSnapshots"
                    Layout.fillWidth: true
                    source: "isentropic.table"
                    columns: page.captionedColumns
                    message: page.snapMessage
                    onRestoreRequested: function (snapshot) { page.restoreSnap(snapshot) }
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
                    readonly property string plainText: Isentropic.tableFooter
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
                visible: Isentropic.compareEnabled && Isentropic.referenceAvailable
                contentSpacing: Metrics.spacing.s

                readonly property var summary: Isentropic.comparisonSummary
                // Only while the comparison is showing: it is made with the
                // table then, and selecting a row just reads it.
                readonly property var rowDetail: comparison.visible && page.selectedRow >= 0
                                                 ? Isentropic.comparisonForRow(page.selectedRow) : []

                trailing: Component {
                    RFStatusChip {
                        text: comparison.summary.status !== undefined ? comparison.summary.status : "—"
                        tone: comparison.summary.status === "PASS" ? "success" : "warning"
                        showDot: false
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Isentropic.referenceAvailable ? Isentropic.referenceCitation : Isentropic.referenceMessage
                    wrapMode: Text.WordWrap
                    color: Isentropic.referenceAvailable ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
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
                    readonly property string plainText: page.selectedRow >= 0
                          ? "Row · M = " + Isentropic.tableModel.machAt(page.selectedRow).toFixed(4)
                          : "Select a row"
                    text: Notation.sectionRich(plainText)
                    textFormat: Notation.textFormat(plainText)
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
