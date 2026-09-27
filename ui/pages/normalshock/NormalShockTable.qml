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
 *
 * The table is an interactive data surface (RFEngineeringTable's shared
 * contract, as on Isentropic): a row selects the relation chart's exact
 * sample and the inspector; a range draws a quiet interval on the chart (it
 * never zooms it) and can be opened as a lens or pinned as a table snapshot
 * in the one AnalysisSession. Every row keeps M1 and all the jumps across
 * that shock together; nothing here is recomputed or re-solved.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpMach: 2.0

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
        var row = NormalShock.rowNearest(mach)
        if (row < 0)
            return
        page.selectedRow = row
        NormalShock.selectRow(row)
        NormalShock.selectTableRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        NormalShock.regenerateTable()
        page.selectedRow = -1
    }

    // What names the table on screen: the settings it was generated with,
    // not the fields above it, which may have been edited since.
    readonly property var generated: NormalShock.tableGenerated
    readonly property string generatedSummary: page.generated.gamma === undefined
        ? "no table generated"
        : "γ " + (+Number(page.generated.gamma).toPrecision(4)) + "  ·  "
          + NormalShock.tableRowCount + " rows  ·  "
          + (page.generated.convention === "anderson" ? "Anderson" : "Extended") + " columns  ·  "
          + NormalShock.tablePrecision + " digits"

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
        var snap = NormalShock.tableSnapshot(block[0], block[1])
        if (snap.kind === undefined)
            return
        var id = AnalysisSession.pin(snap)
        page.snapMessage = id !== "" ? "Pinned " + id + " · " + snap.rangeLabel
                                     : "Not pinned: " + AnalysisSession.lastError
    }
    function copyBlock() {
        var block = page.activeBlock()
        if (block === null)
            NormalShock.copyTable()
        else
            NormalShock.copyTableRows(block[0], block[1])
    }

    // ---- pinned table snapshots (RFTableSnapshotStrip) ----------------------
    property string snapMessage: ""

    // Restore: the same rows of the table on screen, as a range and a lens --
    // only when that table was generated with the snapshot's gamma and
    // columns (NormalShock.restorableRange). Otherwise its rows stay in the
    // snapshot, and the reason is said.
    function restoreSnap(s) {
        var span = NormalShock.restorableRange(s)
        if (span.length !== 2) {
            page.snapMessage = s.id + " comes from another table (γ " + s.gamma + ", "
                               + s.convention + " columns); generate that table to restore it. "
                               + "Its rows are kept in the snapshot."
            return
        }
        table.selectRange(span[0], span[1])
        table.enterLens(span[0], span[1])
        page.snapMessage = "Restored " + s.id + " · " + s.rangeLabel
    }

    // The shared selection drives the table too: a point picked on the chart
    // selects its row here, a range is shown as a range, a cleared selection
    // clears it -- and a page opened again shows the selection the workspace
    // still holds. Presentation only: rows at exactly the selected keys.
    function syncFromSelection() {
        var sel = NormalShock.selection
        if (sel.kind === "plotPoint" || sel.kind === "tableRow") {
            var row = NormalShock.rowExactly(sel.x)
            if (row >= 0 && row !== page.selectedRow) {
                page.selectedRow = row
                table.clearRange()
            }
        } else if (sel.kind === "tableRange") {
            var a = NormalShock.rowExactly(sel.x), b = NormalShock.rowExactly(sel.x1)
            if (a >= 0 && b >= a && (table.rangeFirst !== a || table.rangeLast !== b)) {
                page.selectedRow = -1
                table.rangeFirst = a
                table.rangeLast = b
            }
        } else if (sel.kind === "") {
            page.selectedRow = -1
            table.clearRange()
        }
    }
    Component.onCompleted: page.syncFromSelection()
    Connections {
        target: NormalShock.selection
        function onChanged() { page.syncFromSelection() }
    }
    Connections {
        target: NormalShock
        function onTableChanged() {
            page.selectedRow = -1
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
        RFBottomDrawer {
            id: settings
            objectName: "normalShockTableSettings"
            Layout.fillWidth: true
            Layout.preferredHeight: settings.implicitHeight
            title: "Table settings"
            summary: page.generatedSummary
                     + (NormalShock.tableStale ? "  ·  settings edited, not generated" : "")
            open: true
            drawerHeight: settings.handleHeight + Metrics.spacing.s + controls.implicitHeight

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
                        objectName: "normalShockGenerate"
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

                // What the rows on screen are: calculated, calculated under
                // settings since edited, or not generated at all.
                trailing: Component {
                    RFStatusChip {
                        objectName: "normalShockTableStatus"
                        text: NormalShock.tableRowCount === 0 ? "Not generated"
                            : NormalShock.tableStale ? "Settings edited · Generate"
                            : "Calculated"
                        tone: NormalShock.tableRowCount > 0 && !NormalShock.tableStale ? "success" : "warning"
                        showDot: false
                    }
                }

                RFTableToolbar {
                    Layout.fillWidth: true
                    visible: NormalShock.tableRowCount > 0
                    table: table
                    canPin: true
                    canCopy: true
                    onPinRequested: page.pinBlock()
                    onCopyRequested: page.copyBlock()
                }

                RFEngineeringTable {
                    id: table
                    objectName: "normalShockTable"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: NormalShock.tableRowCount > 0
                    interactive: true

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
                        NormalShock.selectTableRow(row)
                    }
                    onRangeSelected: function (first, last) {
                        page.selectedRow = -1
                        NormalShock.selectTableRange(first, last)
                    }
                    onEscapePressed: NormalShock.selection.clear()
                    // An explicit request: the calculator solves that M₁ and
                    // the relation shows it.
                    onRowActivated: function (row) {
                        NormalShock.setMachAndSolve(NormalShock.tableModel.machAt(row))
                        NormalShock.requestTab(0)
                    }
                }

                // Pinned table snapshots: A/B picks a pair to difference
                // (row-aligned by M₁); Restore reopens the rows as a lens.
                RFTableSnapshotStrip {
                    objectName: "normalShockTableSnapshots"
                    Layout.fillWidth: true
                    source: "normal_shock.table"
                    columns: NormalShock.tableColumns
                    message: page.snapMessage
                    onRestoreRequested: function (snapshot) { page.restoreSnap(snapshot) }
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
                    objectName: "normalShockTableCaption"
                    // Names the table on screen from the settings it was generated with.
                    readonly property string plainText: NormalShock.generatedCaption
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
                objectName: "normalShockComparison"
                title: "Reference comparison"
                Layout.preferredWidth: 372
                Layout.fillHeight: true
                visible: NormalShock.compareEnabled && NormalShock.referenceAvailable
                contentSpacing: Metrics.spacing.s

                readonly property var summary: NormalShock.comparisonSummary
                // Only while the comparison is showing: it is made with the
                // table then, and selecting a row just reads it.
                readonly property var rowDetail: comparison.visible && page.selectedRow >= 0
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
