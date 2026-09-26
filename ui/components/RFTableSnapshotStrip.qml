import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../theme"

/*
 * RFTableSnapshotStrip — the pinned table blocks of one table, in the one
 * AnalysisSession.
 *
 * One chip per pinned block (id, range, rows, what it was generated with).
 * Picking two -- A, then B -- differences them row by row, aligned by the
 * rows' engineering key (never by position), and names the largest
 * difference per column; blocks that cannot be compared say why. Restore is
 * the owner's (it knows how to find those rows in the table on screen); the
 * strip only asks. Hidden when nothing is pinned and nothing needs saying.
 */
ColumnLayout {
    id: strip

    property string source: ""
    // The owner's current column labels, for the difference line.
    property var columns: []
    property string message: ""

    signal restoreRequested(var snapshot)

    readonly property var snaps: AnalysisSession.snapshots.filter(function (s) {
        return s.kind === "table" && s.source === strip.source
    })
    property string snapA: ""
    property string snapB: ""

    function byId(id) {
        for (var i = 0; i < strip.snaps.length; ++i)
            if (strip.snaps[i].id === id)
                return strip.snaps[i]
        return null
    }
    function pick(id) {
        if (strip.snapA === id) { strip.snapA = ""; return }
        if (strip.snapB === id) { strip.snapB = ""; return }
        if (strip.snapA === "") strip.snapA = id
        else strip.snapB = id
    }
    function describe(s) {
        var parts = [s.id + "  " + s.rangeLabel, s.rowKeys.length + (s.rowKeys.length === 1 ? " row" : " rows")]
        if (s.gamma !== undefined) parts.push("γ " + s.gamma)
        if (s.regime !== undefined && s.regime !== "") parts.push(s.regime)
        if (s.stale) parts.push("stale")
        return parts.join("  ·  ")
    }

    readonly property var delta: strip.byId(strip.snapA) !== null && strip.byId(strip.snapB) !== null
                                 ? AnalysisSession.tableDelta(strip.snapA, strip.snapB) : ({})
    readonly property string deltaText: {
        var d = strip.delta
        if (d.compatible === undefined)
            return ""
        if (!d.compatible)
            return strip.snapB + " − " + strip.snapA + ": not comparable (" + d.reason + ")"
        var parts = []
        for (var c = 1; c < d.columns.length; ++c) {
            var col = strip.columns[c]
            if (d.maxAbs[c] !== null && col)
                parts.push(col.label + " " + Number(d.maxAbs[c]).toPrecision(3))
        }
        return strip.snapB + " − " + strip.snapA + ": " + d.matched + " rows matched by key"
               + (d.unmatchedA + d.unmatchedB > 0 ? " (" + d.unmatchedA + " only in " + strip.snapA
                  + ", " + d.unmatchedB + " only in " + strip.snapB + ")" : "")
               + (parts.length > 0 ? "  ·  max |Δ|  " + parts.join("   ") : "")
    }

    visible: strip.snaps.length > 0 || strip.message !== ""
    spacing: Metrics.spacing.xs

    Flow {
        Layout.fillWidth: true
        spacing: Metrics.spacing.s
        visible: strip.snaps.length > 0

        Repeater {
            model: strip.snaps
            delegate: Row {
                required property var modelData
                spacing: 2
                RFToolButton {
                    text: (strip.snapA === modelData.id ? "A · " : strip.snapB === modelData.id ? "B · " : "")
                          + strip.describe(modelData)
                    tooltip: "Pick as A, then B, to difference two pinned blocks"
                    checked: strip.snapA === modelData.id || strip.snapB === modelData.id
                    onClicked: strip.pick(modelData.id)
                }
                RFToolButton {
                    text: "Restore"
                    tooltip: "Reopen these rows of the table on screen as a range and a lens"
                    onClicked: strip.restoreRequested(modelData)
                }
                RFToolButton {
                    text: "×"
                    tooltip: "Remove this snapshot"
                    onClicked: {
                        if (strip.snapA === modelData.id) strip.snapA = ""
                        if (strip.snapB === modelData.id) strip.snapB = ""
                        AnalysisSession.remove(modelData.id)
                    }
                }
            }
        }
    }

    Text {
        Layout.fillWidth: true
        visible: text !== ""
        text: Notation.rich(strip.deltaText !== "" ? strip.deltaText : strip.message)
        textFormat: Text.RichText
        wrapMode: Text.WordWrap
        color: Theme.textSecondary
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }
}
