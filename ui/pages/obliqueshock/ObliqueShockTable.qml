import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The deflection sweep, as an engineering table.
 *
 * A sweep of the flow deflection θ at one upstream Mach number, every row
 * computed by RocketForge on the branch it names: "One branch" reports the
 * full downstream state on the weak or the strong branch; "Weak vs strong"
 * puts the two branches side by side in their own labelled columns. The two
 * are never merged into one row, and a row is never read back without the
 * M₁, γ and branch it was generated with.
 *
 * The sweep is capped at the attachment limit rather than filled with
 * substituted rows. Past θ_max there is no attached shock, and a table that
 * kept going would be the worst possible way to say so — so the range is cut,
 * the last row is the merged solution at θ_max, and the footer says the cap
 * happened. A deflection the service could not solve is left out, not
 * filled in.
 *
 * The table is an interactive data surface (RFEngineeringTable's shared
 * contract, as on Isentropic): a row selects the Study's sweep curve at that
 * exact θ and the inspector; a range draws a quiet interval on the curve (it
 * never zooms it) and can be opened as a lens or pinned as a table snapshot
 * in the one AnalysisSession. Nothing here is recomputed or re-solved.
 */
Item {
    id: page

    property int selectedRow: -1
    property real jumpTheta: 10.0

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

    // Numeric navigation: a reader looks for a deflection, not a string.
    function jumpTo(theta) {
        var row = ObliqueShock.rowNearest(theta)
        if (row < 0)
            return
        page.selectedRow = row
        ObliqueShock.selectRow(row)
        ObliqueShock.selectTableRow(row)
        table.scrollToRow(row)
    }

    function applySettings() {
        ObliqueShock.regenerateTable()
        page.selectedRow = -1
    }

    // What names the table on screen: the settings it was generated with,
    // not the fields above it, which may have been edited since.
    readonly property var generated: ObliqueShock.tableGenerated
    readonly property string branchWords: page.generated.convention === "comparison"
                                          ? "weak and strong side by side"
                                          : (page.generated.branch || "") + " branch"
    readonly property string generatedSummary: page.generated.mach1 === undefined
        ? "no sweep generated"
        : "M₁ " + (+Number(page.generated.mach1).toPrecision(6))
          + "  ·  γ " + (+Number(page.generated.gamma).toPrecision(4))
          + "  ·  " + page.branchWords
          + "  ·  " + ObliqueShock.tableRowCount + " rows"
          + (page.generated.capped ? "  ·  capped at the attachment limit, "
                                     + Number(page.generated.thetaMax).toFixed(4) + "°" : "")
          + "  ·  " + ObliqueShock.tablePrecision + " digits"

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
        var snap = ObliqueShock.tableSnapshot(block[0], block[1])
        if (snap.kind === undefined)
            return
        var id = AnalysisSession.pin(snap)
        page.snapMessage = id !== "" ? "Pinned " + id + " · " + snap.rangeLabel + " · " + snap.regime
                                     : "Not pinned: " + AnalysisSession.lastError
    }
    function copyBlock() {
        var block = page.activeBlock()
        if (block === null)
            ObliqueShock.copyTable()
        else
            ObliqueShock.copyTableRows(block[0], block[1])
    }

    // ---- pinned table snapshots (RFTableSnapshotStrip) ----------------------
    property string snapMessage: ""

    // Restore: the same rows of the sweep on screen, as a range and a lens --
    // only when that sweep was generated at the snapshot's M₁, γ, columns and
    // branch (ObliqueShock.restorableRange). The same θ on another branch or
    // another Mach number is a different shock, so it is not restored onto it.
    function restoreSnap(s) {
        var span = ObliqueShock.restorableRange(s)
        if (span.length !== 2) {
            page.snapMessage = s.id + " comes from another sweep (" + s.regime + ", γ " + s.gamma
                               + "); generate that sweep to restore it. Its rows are kept in the snapshot."
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
        var sel = ObliqueShock.selection
        if (sel.kind === "plotPoint" || sel.kind === "tableRow") {
            var row = ObliqueShock.rowExactly(sel.x)
            if (row >= 0 && row !== page.selectedRow) {
                page.selectedRow = row
                table.clearRange()
            }
        } else if (sel.kind === "tableRange") {
            var a = ObliqueShock.rowExactly(sel.x), b = ObliqueShock.rowExactly(sel.x1)
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
        target: ObliqueShock.selection
        function onChanged() { page.syncFromSelection() }
    }
    Connections {
        target: ObliqueShock
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
        RFBottomDrawer {
            id: settings
            objectName: "obliqueShockTableSettings"
            Layout.fillWidth: true
            Layout.preferredHeight: settings.implicitHeight
            title: "Sweep settings"
            summary: page.generatedSummary
                     + (ObliqueShock.tableStale ? "  ·  settings edited, not generated" : "")
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
                        Layout.preferredWidth: 150
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
                        objectName: "obliqueShockGenerate"
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

                    // The branch is a choice only for the one-branch sweep;
                    // side by side, both are printed, each in its own column.
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

                    Text {
                        Layout.fillWidth: true
                        visible: ObliqueShock.tableCapped
                        text: "Range capped at the attachment limit — no attached shock exists above it."
                        elide: Text.ElideRight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.fillWidth: true; visible: !ObliqueShock.tableCapped }

                    RFBoundNumberField {
                        Layout.preferredWidth: 132
                        label: "Jump to θ  [°]"
                        value: page.jumpTheta
                        digits: 3
                        decimals: 3
                        step: 0.5
                        onValueEdited: function (v) { page.jumpTheta = v }
                    }

                    RFButton {
                        text: "Go"
                        variant: "quiet"
                        compact: true
                        onClicked: page.jumpTo(page.jumpTheta)
                    }

                    RFButton {
                        text: "Copy table"
                        variant: "quiet"
                        compact: true
                        onClicked: ObliqueShock.copyTable()
                    }
                }
            }
        }

        // ---- table ----------------------------------------------------------
        RFPanel {
            title: "Deflection sweep"
            Layout.fillWidth: true
            Layout.fillHeight: true

            // What the rows on screen are: calculated, calculated under
            // settings since edited, or not generated at all.
            trailing: Component {
                RFStatusChip {
                    objectName: "obliqueShockTableStatus"
                    text: ObliqueShock.tableRowCount === 0 ? "Not generated"
                        : ObliqueShock.tableStale ? "Settings edited · Generate"
                        : "Calculated"
                    tone: ObliqueShock.tableRowCount > 0 && !ObliqueShock.tableStale ? "success" : "warning"
                    showDot: false
                }
            }

            RFTableToolbar {
                Layout.fillWidth: true
                visible: ObliqueShock.tableRowCount > 0
                table: table
                canPin: true
                canCopy: true
                onPinRequested: page.pinBlock()
                onCopyRequested: page.copyBlock()
            }

            RFEngineeringTable {
                id: table
                objectName: "obliqueShockTable"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ObliqueShock.tableRowCount > 0
                interactive: true

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
                    ObliqueShock.selectTableRow(row)
                }
                onRangeSelected: function (first, last) {
                    page.selectedRow = -1
                    ObliqueShock.selectTableRange(first, last)
                }
                onEscapePressed: ObliqueShock.selection.clear()
                // An explicit request, unchanged: the Calculator solves that
                // deflection at its own M₁, γ and branch (said in the footer).
                onRowActivated: function (row) {
                    ObliqueShock.setDeflectionAndSolve(ObliqueShock.tableModel.machAt(row))
                    ObliqueShock.requestTab(0)
                }
            }

            // Pinned table snapshots: A/B picks a pair to difference (rows
            // aligned by θ, each chip naming its M₁ and branch); Restore
            // reopens the rows as a lens on the sweep they came from.
            RFTableSnapshotStrip {
                objectName: "obliqueShockTableSnapshots"
                Layout.fillWidth: true
                source: "oblique_shock.table"
                columns: ObliqueShock.tableColumns
                message: page.snapMessage
                onRestoreRequested: function (snapshot) { page.restoreSnap(snapshot) }
            }

            RFEmptyState {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ObliqueShock.tableRowCount === 0
                tag: "Table"
                title: ObliqueShock.tableMessage !== "" ? "Sweep not generated" : "No rows"
                body: ObliqueShock.tableMessage !== "" ? ObliqueShock.tableMessage
                                                       : "Adjust the range and press Generate."
            }

            Text {
                Layout.fillWidth: true
                objectName: "obliqueShockTableCaption"
                // Names the sweep on screen from the settings it was generated with.
                readonly property string plainText: ObliqueShock.generatedCaption
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: ObliqueShock.tableRowCount > 0
                readonly property string plainText: "The final row is the maximum deflection this Mach number can turn: the "
                      + "weak and strong solutions merge there into one wave angle. Double-click a row "
                      + "to solve that θ on the Calculator, at the Calculator's own M₁, γ and branch."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
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
