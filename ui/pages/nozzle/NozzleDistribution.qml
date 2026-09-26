import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * The distributed solution, station by station.
 *
 * The two shock stations are two rows sharing an x, marked PRE SHOCK and POST
 * SHOCK. They are never merged and never interpolated between: the jump is the
 * physics, and a table that smoothed it would be reporting something that does
 * not happen. They stay two rows in a selection, in a range, in a pinned
 * snapshot and in a comparison.
 *
 * The throat marker says SONIC only when the throat actually is sonic. An
 * unchoked nozzle has a throat, not a sonic point, and saying otherwise on a
 * page about choking would be a poor joke.
 *
 * The table is the view: a strip of the marked stations above it (each a
 * jump that selects the station everywhere -- drawing, 3D, charts, the
 * Inspector -- then scrolls to it) and the shared table tools. The selected
 * station reads in the Inspector.
 */
Item {
    id: page

    property int selectedRow: -1
    property string snapMessage: ""

    NozzleLinks { id: links }

    // Every Nozzle Lab view selects through the one selection: a station
    // picked on the drawing, in 3D or on a chart selects its row here.
    Connections {
        target: Nozzle.selection
        function onChanged() {
            var row = links.rowOfSelection()
            if (Nozzle.selection.kind !== "tableRange")
                table.clearRange()
            page.selectedRow = row
        }
    }
    Connections {
        target: Nozzle
        function onTableChanged() {
            table.clearRange()
            table.exitLens()
            page.selectedRow = links.rowOfSelection()
        }
    }

    function jumpTo(row) {
        if (row < 0)
            return
        table.clearRange()
        links.selectRow(row, "table")
        page.selectedRow = row
        table.scrollToRow(row)
    }

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
        var snap = Nozzle.tableSnapshot(block[0], block[1])
        if (snap.kind === undefined)
            return
        var id = AnalysisSession.pin(snap)
        page.snapMessage = id !== "" ? "Pinned " + id + " · " + snap.rangeLabel
                                     : "Not pinned: " + AnalysisSession.lastError
    }
    function copyBlock() {
        var block = page.activeBlock()
        if (block === null) {
            Nozzle.copyTable()
            return
        }
        var lines = [table.columns.map(function (c) { return c.label }).join("\t")]
        for (var r = block[0]; r <= block[1]; ++r) {
            var cells = []
            for (var c = 0; c < table.columns.length; ++c)
                cells.push(table.cellText(r, c))
            lines.push(cells.join("\t"))
        }
        AnalysisSession.copyText(lines.join("\n"))
    }
    // Restore: the same solved state only -- a block of another solution is
    // kept in its snapshot, not forced onto these rows.
    function restoreSnap(s) {
        if (s.identity !== Nozzle.resultIdentity || s.lastRow >= Nozzle.rowCount) {
            page.snapMessage = s.id + " belongs to another solution (" + (s.regime || "earlier state")
                               + "); its rows are kept in the snapshot."
            return
        }
        table.selectRange(s.firstRow, s.lastRow)
        table.enterLens(s.firstRow, s.lastRow)
        page.snapMessage = "Restored " + s.id + " · " + s.rangeLabel
    }

    readonly property var markedStations: [
        { key: "throat", label: Nozzle.choked ? "Throat · sonic" : "Throat",
          row: Nozzle.throatRow, shown: true },
        { key: "pre", label: "Pre-shock", row: Nozzle.preShockRow, shown: Nozzle.hasShock },
        { key: "post", label: "Post-shock", row: Nozzle.postShockRow, shown: Nozzle.hasShock },
        { key: "exit", label: "Exit", row: Nozzle.exitRow, shown: true }
    ]

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        // ---- what the table holds: one line of settings --------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.spacing.l

            ColumnLayout {
                Layout.preferredWidth: 240
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
                Layout.preferredWidth: 120
                label: "Stations"
                value: Nozzle.resolution
                digits: 0
                step: 20
                onValueEdited: function (v) { Nozzle.resolution = v }
            }

            ColumnLayout {
                Layout.preferredWidth: 180
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
                text: "Copy table"
                variant: "quiet"
                compact: true
                onClicked: Nozzle.copyTable()
            }
        }

        RFPanel {
            title: "Stations"
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.s

            trailing: Component {
                RFStatusChip {
                    text: "RocketForge computed"
                    showDot: false
                }
            }

            // ---- marked stations: jumps, not a side panel ------------------
            Flow {
                objectName: "nozzleMarkedStations"
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                Text {
                    height: Metrics.controlHeightSmall
                    verticalAlignment: Text.AlignVCenter
                    rightPadding: Metrics.spacing.xs
                    text: "Marked stations"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
                Repeater {
                    model: page.markedStations
                    delegate: RFToolButton {
                        required property var modelData
                        objectName: "nozzleJump_" + modelData.key
                        visible: modelData.shown && modelData.row >= 0
                        text: modelData.label + "  ·  row " + (modelData.row + 1)
                        tooltip: "Select this station everywhere (drawing, 3D, charts, Inspector) and scroll to it"
                        checked: page.selectedRow === modelData.row
                        onClicked: page.jumpTo(modelData.row)
                    }
                }
            }

            RFTableToolbar {
                Layout.fillWidth: true
                table: table
                canPin: true
                canCopy: true
                onPinRequested: page.pinBlock()
                onCopyRequested: page.copyBlock()
            }

            RFEngineeringTable {
                id: table
                objectName: "nozzleDistributionTable"
                Layout.fillWidth: true
                Layout.fillHeight: true
                interactive: true

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
                    links.selectRow(row, "table")
                }
                onRangeSelected: function (first, last) {
                    page.selectedRow = -1
                    Nozzle.selectTableRange(first, last)
                }
                onEscapePressed: links.clear()
            }

            RFTableSnapshotStrip {
                objectName: "nozzleTableSnapshots"
                Layout.fillWidth: true
                source: "nozzle.distribution"
                columns: Nozzle.tableColumns
                message: page.snapMessage
                onRestoreRequested: function (snapshot) { page.restoreSnap(snapshot) }
            }

            Text {
                Layout.fillWidth: true
                text: [Nozzle.tableCaption,
                       Nozzle.hasShock ? "the shock occupies two rows at the same x: the state "
                                         + "before it and the state after it, kept apart because the "
                                         + "jump between them is the result" : ""]
                      .filter(function (s) { return s !== "" }).join("  ·  ")
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
