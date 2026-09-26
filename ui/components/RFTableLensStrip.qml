import QtQuick
import "../theme"

/*
 * RFTableLensStrip — the context an RFEngineeringTable lens leaves outside.
 *
 * One quiet strip above the lens and one below, each counting the rows it
 * stands for and naming the first of them ("▲ 80 rows above · next M 1.79"),
 * so the lens never pretends the table ends where it does. Clicking a strip
 * is handled by the table (it leaves the lens); the strip itself draws.
 */
Rectangle {
    id: strip

    property Item table: null
    property int count: 0
    property int edgeRow: -1
    property string direction: "above"          // above | below

    color: Theme.surfaceSubtle

    Text {
        anchors.left: parent.left
        anchors.leftMargin: Metrics.spacing.m
        anchors.right: parent.right
        anchors.rightMargin: Metrics.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        elide: Text.ElideRight
        text: {
            if (!strip.table || !strip.visible)
                return ""
            var head = strip.table.columns.length > 0 ? strip.table.columns[0].label : ""
            return (strip.direction === "above" ? "▲  " : "▼  ") + strip.count
                   + (strip.count === 1 ? " row " : " rows ") + strip.direction + " the lens"
                   + "   ·   next " + head + " " + strip.table.cellText(strip.edgeRow, 0)
                   + "   ·   click to show the full table"
        }
        textFormat: Text.PlainText
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
    }

    Rectangle {
        anchors.bottom: strip.direction === "above" ? parent.bottom : undefined
        anchors.top: strip.direction === "below" ? parent.top : undefined
        width: parent.width
        height: Metrics.hairline
        color: Theme.borderStrong
    }
}
