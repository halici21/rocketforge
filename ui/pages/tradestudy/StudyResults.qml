import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * Every evaluated point, with its raw physics intact.
 *
 * The table contains successful, infeasible and failed points by default. A
 * filter hides rows; it never removes them, and the underlying study result
 * keeps all of them however the view is set. A design space with holes in it
 * is information: the holes are where the model stops working, and a table
 * that quietly dropped those rows would imply the space is continuous.
 *
 * A failed row shows an em dash for the metrics it could not produce - never a
 * zero, which would be a physical claim about an engine rather than the
 * absence of one.
 *
 * Status and feasibility are separate columns because they answer different
 * questions: whether the model produced an answer, and whether that answer is
 * a design anyone may choose.
 *
 * The filter lives in a drawer whose handle says how much of the study is on
 * screen ("328 / 328 visible"). A row selects its design point for the
 * Inspector -- read from the evaluated result, nothing is evaluated -- and
 * chosen points can be pinned as a subset of this run, with the filter and
 * the columns that framed them. A subset of another run is never compared
 * with one of this run.
 */
Item {
    id: view

    property string subsetMessage: ""

    // The rows a Pin means: the design points chosen for comparison, else
    // the table range, else the lens.
    function blockIndices() {
        if (TradeStudy.selectedIndices.length > 0)
            return TradeStudy.selectedIndices
        var a = resultsTable.hasRange ? resultsTable.rangeFirst
              : resultsTable.lensActive ? resultsTable.lensFirst : -1
        var b = resultsTable.hasRange ? resultsTable.rangeLast
              : resultsTable.lensActive ? resultsTable.lensLast : -1
        var out = []
        for (var r = a; a >= 0 && r <= b; ++r) {
            var index = TradeStudy.pointAtRow(r)
            if (index >= 0)
                out.push(index)
        }
        return out
    }
    function pinSubset() {
        var indices = view.blockIndices()
        if (indices.length === 0) {
            view.subsetMessage = "Select design points (click rows) or a row range to pin a subset."
            return
        }
        var snap = TradeStudy.subsetSnapshot(indices)
        if (snap.kind === undefined)
            return
        var id = AnalysisSession.pin(snap)
        view.subsetMessage = id !== "" ? "Pinned " + id + " · " + snap.label + " · " + snap.runIdentity
                                       : "Not pinned: " + AnalysisSession.lastError
    }
    function copyRows() {
        var a = resultsTable.hasRange ? resultsTable.rangeFirst
              : resultsTable.lensActive ? resultsTable.lensFirst : 0
        var b = resultsTable.hasRange ? resultsTable.rangeLast
              : resultsTable.lensActive ? resultsTable.lensLast : TradeStudy.visibleRowCount - 1
        var lines = [resultsTable.columns.map(function (c) { return c.label }).join("\t")]
        for (var r = a; r <= b; ++r) {
            var cells = []
            for (var c = 0; c < resultsTable.columns.length; ++c)
                cells.push(resultsTable.cellText(r, c))
            lines.push(cells.join("\t"))
        }
        AnalysisSession.copyText(lines.join("\n"))
    }

    // ---- pinned subsets (kind "subset" in the one AnalysisSession) --------
    readonly property var subsets: AnalysisSession.snapshots.filter(function (s) {
        return s.kind === "subset" && s.source === "tradestudy"
    })
    property string subsetA: ""
    property string subsetB: ""
    function subsetById(id) {
        for (var i = 0; i < view.subsets.length; ++i)
            if (view.subsets[i].id === id)
                return view.subsets[i]
        return null
    }
    function pickSubset(id) {
        if (view.subsetA === id) { view.subsetA = ""; return }
        if (view.subsetB === id) { view.subsetB = ""; return }
        if (view.subsetA === "") view.subsetA = id
        else view.subsetB = id
    }
    // Two subsets of one run: which points they share. Of different runs (or
    // analyses): refused, with the reason the session gives.
    readonly property string subsetCompareText: {
        var a = view.subsetById(view.subsetA), b = view.subsetById(view.subsetB)
        if (a === null || b === null)
            return ""
        var verdict = AnalysisSession.compare(view.subsetA, view.subsetB)
        if (!verdict.compatible)
            return view.subsetB + " vs " + view.subsetA + ": not comparable (" + verdict.reason + ")"
        var shared = a.indices.filter(function (i) { return b.indices.indexOf(i) >= 0 })
        return view.subsetB + " vs " + view.subsetA + " (" + a.runIdentity + "): "
               + shared.length + " design points in both, "
               + (a.indices.length - shared.length) + " only in " + view.subsetA + ", "
               + (b.indices.length - shared.length) + " only in " + view.subsetB
               + (shared.length > 0 ? "  ·  shared #" + shared.join(", #") : "")
    }
    // Restore: this run only. The filter it was pinned under, and its points
    // selected again (the comparison holds up to four).
    function restoreSubset(s) {
        if (s.runIdentity !== TradeStudy.runIdentity) {
            view.subsetMessage = s.id + " belongs to " + s.runIdentity + "; the study on screen is "
                                 + TradeStudy.runIdentity + ". It is kept, not applied."
            return
        }
        TradeStudy.filterMode = s.filter.mode
        TradeStudy.setSelection(s.indices)
        view.subsetMessage = "Restored " + s.id + " · " + s.label
                             + (s.indices.length > TradeStudy.maximumComparisons
                                ? " (the first " + TradeStudy.maximumComparisons + " selected for comparison)" : "")
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: !TradeStudy.hasResult
            tag: "NO STUDY"
            title: "No study has been run"
            body: "Define the variables, objectives and constraints on the "
                  + "Setup tab, then press Run Study. Nothing is shown here "
                  + "until a design space has actually been evaluated."
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: TradeStudy.hasResult
            spacing: Metrics.spacing.m

            // ---- filter drawer ----------------------------------------------
            RFWorkspaceDrawer {
                id: filterDrawer
                objectName: "tradeFilterDrawer"
                Layout.preferredWidth: filterDrawer.implicitWidth
                Layout.fillHeight: true
                title: "Filter"
                summary: TradeStudy.visibleRowCount + " / " + TradeStudy.totalPointCount
                         + " visible  ·  " + TradeStudy.filterLabel
                drawerWidth: 250
                open: false

                ColumnLayout {
                    anchors.fill: parent
                    spacing: Metrics.spacing.m

                    RFComboBox {
                        Layout.fillWidth: true
                        label: "Show"
                        model: TradeStudy.filterOptions.map(function (o) { return o.label })
                        currentIndex: {
                            var options = TradeStudy.filterOptions
                            for (var i = 0; i < options.length; ++i)
                                if (options[i].key === TradeStudy.filterMode)
                                    return i
                            return 0
                        }
                        onActivated: function (index) {
                            var options = TradeStudy.filterOptions
                            if (index >= 0 && index < options.length)
                                TradeStudy.filterMode = options[index].key
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: TradeStudy.visibleRowCount + " of " + TradeStudy.totalPointCount
                              + " evaluated points shown. A filter hides rows; it never removes "
                              + "them, and the study keeps every point."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // ---- the table ----------------------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.spacing.s

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.m

                    Text {
                        objectName: "tradeVisibleCount"
                        Layout.alignment: Qt.AlignVCenter
                        text: TradeStudy.visibleRowCount + " / " + TradeStudy.totalPointCount
                              + " visible · " + TradeStudy.solveReuseNote
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    RFStatusChip {
                        Layout.alignment: Qt.AlignVCenter
                        visible: TradeStudy.resultStale
                        text: "Setup changed"
                        tone: "warning"
                    }
                    Item { Layout.fillWidth: true }
                    RFTableToolbar {
                        table: resultsTable
                        canPin: true
                        canCopy: true
                        pinText: "Pin subset"
                        onPinRequested: view.pinSubset()
                        onCopyRequested: view.copyRows()
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: TradeStudy.message !== ""
                    text: TradeStudy.message
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFEngineeringTable {
                    id: resultsTable
                    objectName: "tradeResultsTable"
                    Layout.fillWidth: true
                    // Fills the room up to exactly its rows: a small study
                    // leaves the slack to the spacer below instead of an
                    // empty grid; a large one takes the room and scrolls.
                    // The count is the controller's property (it notifies);
                    // `model.rowCount()` read once in a binding never
                    // re-evaluated, which left the table empty when the page
                    // was built before the study finished.
                    Layout.fillHeight: true
                    Layout.minimumHeight: Math.min(160, Layout.maximumHeight)
                    Layout.maximumHeight: TradeStudy.visibleRowCount * effRowHeight + headerHeight
                    interactive: true
                    model: TradeStudy.resultsModel
                    columns: TradeStudy.resultColumns
                    firstColumnWidth: 56
                    columnWidth: 142
                    // the last design chosen, where the filter shows it
                    selectedRow: {
                        var chosen = TradeStudy.selectedIndices
                        TradeStudy.visibleRowCount
                        return chosen.length > 0 ? TradeStudy.rowOfPoint(chosen[chosen.length - 1]) : -1
                    }
                    onRowClicked: function (row) {
                        var index = TradeStudy.pointAtRow(row)
                        if (index >= 0)
                            TradeStudy.toggleSelection(index)
                    }
                    onEscapePressed: TradeStudy.clearSelection()
                }

                // A filter that matches nothing says so -- an empty grid under
                // a header reads as a table that failed to load.
                Text {
                    objectName: "tradeFilterEmpty"
                    Layout.fillWidth: true
                    visible: TradeStudy.visibleRowCount === 0 && TradeStudy.totalPointCount > 0
                    text: "No evaluated point matches “" + TradeStudy.filterLabel + "”. The filter "
                          + "hides rows; the study still holds all " + TradeStudy.totalPointCount
                          + " points (Filter → All points)."
                    wrapMode: Text.WordWrap
                    color: Theme.textSecondary
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                // Pinned subsets: A/B picks a pair; Restore re-applies one of
                // this run. Built only when something is pinned or said.
                Loader {
                    Layout.fillWidth: true
                    active: view.subsets.length > 0 || view.subsetMessage !== ""
                    visible: active
                    sourceComponent: ColumnLayout {
                        objectName: "tradeSubsets"
                        spacing: Metrics.spacing.xs
                        Flow {
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s
                            Repeater {
                                model: view.subsets
                                delegate: Row {
                                    required property var modelData
                                    spacing: 2
                                    RFToolButton {
                                        text: (view.subsetA === modelData.id ? "A · " : view.subsetB === modelData.id ? "B · " : "")
                                              + modelData.id + "  " + modelData.label + "  ·  " + modelData.runIdentity
                                        tooltip: "Pick as A, then B, to compare two subsets of one run"
                                        checked: view.subsetA === modelData.id || view.subsetB === modelData.id
                                        onClicked: view.pickSubset(modelData.id)
                                    }
                                    RFToolButton {
                                        text: "Restore"
                                        tooltip: "Re-apply its filter and select its design points (this run only)"
                                        onClicked: view.restoreSubset(modelData)
                                    }
                                    RFToolButton {
                                        text: "×"
                                        tooltip: "Remove this subset"
                                        onClicked: {
                                            if (view.subsetA === modelData.id) view.subsetA = ""
                                            if (view.subsetB === modelData.id) view.subsetB = ""
                                            AnalysisSession.remove(modelData.id)
                                        }
                                    }
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: text !== ""
                            text: view.subsetCompareText !== "" ? view.subsetCompareText : view.subsetMessage
                            wrapMode: Text.WordWrap
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }

                // Takes the slack when the table is shorter than the view.
                Item { Layout.fillHeight: true; Layout.preferredHeight: 0 }
            }
        }

        // ---- summary, provenance and aggregated diagnostics -------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: 168
            visible: TradeStudy.hasResult
            spacing: Metrics.spacing.m

            RFPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "Study summary"
                contentSpacing: Metrics.spacing.xs

                Flow {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.l

                    Repeater {
                        model: TradeStudy.summaryRows

                        delegate: Row {
                            required property var modelData
                            spacing: Metrics.spacing.xs

                            Text {
                                text: Notation.rich(modelData.label)
                                textFormat: Notation.textFormat(modelData.label)
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                            Text {
                                text: modelData.value
                                color: Theme.textSecondary
                                font.family: Typography.mono
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xs
                    text: "Design points and chamber solves are different "
                          + "numbers. The nozzle-stage variables cost no "
                          + "chemistry, which is why the second is usually the "
                          + "smaller."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textDisabled
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFPanel {
                Layout.preferredWidth: 440
                Layout.fillHeight: true
                title: "Diagnostics and provenance"
                contentSpacing: Metrics.spacing.xs

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: notes.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: RFScrollBar {}

                    ColumnLayout {
                        id: notes
                        width: parent.width
                        spacing: 2

                        Repeater {
                            model: TradeStudy.diagnosticRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.code
                                    elide: Text.ElideRight
                                    color: modelData.severity === "warning"
                                           ? Theme.warning : Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    text: modelData.summary
                                    color: Theme.textDisabled
                                    font.family: Typography.mono
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }

                        RFDivider { Layout.fillWidth: true }

                        Repeater {
                            model: TradeStudy.provenanceRows

                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: false
                                spacing: Metrics.spacing.s

                                Text {
                                    Layout.preferredWidth: 152
                                    text: Notation.rich(modelData.label)
                                    textFormat: Notation.textFormat(modelData.label)
                                    wrapMode: Text.WordWrap
                                    color: Theme.textMuted
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.value
                                    wrapMode: Text.WordWrap
                                    color: Theme.textSecondary
                                    font.family: Typography.sans
                                    font.pixelSize: Typography.meta
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
