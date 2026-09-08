import QtQuick
import "../theme"

/*
 * RFPlotSurface - the frame every chart in the application is drawn on.
 *
 * It owns the axes, the grid, the tick labels and the data-to-pixel mapping;
 * it owns no data. Children are placed inside the plot area and position
 * themselves with mapX()/mapY(), so a series never has to know about gutters.
 *
 * Deliberately frameless: two hairline axes, a grid one step quieter than the
 * dividers, and nothing else. No boxed border, no filled plot background beyond
 * the surface it sits on.
 */
Item {
    id: root

    property real xMin: 0
    property real xMax: 1
    property real yMin: 0
    property real yMax: 1

    property int xTickCount: 6
    property int yTickCount: 5

    property string xTitle: ""
    property string yTitle: ""

    // Tick formatting is a presentation choice, so it lives with the plot.
    property var xFormat: function (v) { return v.toFixed(1) }
    property var yFormat: function (v) { return v.toFixed(1) }

    // The rotated axis title needs its own column to the left of the ticks.
    property real leftGutter: yTitle !== "" ? 60 : 46
    // The axis title gets its own line under the tick labels.
    property real bottomGutter: xTitle !== "" ? 44 : 30
    property real topPadding: 12
    property real rightPadding: 16

    // [{ name: "p/p0", color: <color>, dashed: bool }]
    property var legend: []

    readonly property alias plotArea: area
    default property alias content: area.data

    function tickValue(i, count, lo, hi) {
        return lo + (hi - lo) * i / Math.max(1, count - 1)
    }
    function mapX(v) {
        return (v - xMin) / (xMax - xMin) * area.width
    }
    function mapY(v) {
        return area.height - (v - yMin) / (yMax - yMin) * area.height
    }
    function unmapX(px) {
        return xMin + (px / Math.max(1, area.width)) * (xMax - xMin)
    }

    // ---- y axis ----------------------------------------------------------

    Text {
        id: yTitleText
        visible: root.yTitle !== ""
        text: root.yTitle
        rotation: -90
        transformOrigin: Item.Center
        // Rotating about the centre swaps the visual extents, so the left edge
        // of the painted glyphs is x + width/2 - height/2.
        x: 2 - width / 2 + height / 2
        y: area.y + area.height / 2 - height / 2
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.4
    }

    Repeater {
        model: root.yTickCount
        delegate: Text {
            required property int index
            readonly property real value: root.tickValue(index, root.yTickCount, root.yMin, root.yMax)

            x: root.leftGutter - width - 10
            y: area.y + root.mapY(value) - height / 2
            text: root.yFormat(value)
            color: Theme.textMuted
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }
    }

    // ---- x axis ----------------------------------------------------------

    Repeater {
        model: root.xTickCount
        delegate: Text {
            required property int index
            readonly property real value: root.tickValue(index, root.xTickCount, root.xMin, root.xMax)

            x: area.x + root.mapX(value) - width / 2
            y: area.y + area.height + 9
            text: root.xFormat(value)
            color: Theme.textMuted
            font.family: Typography.mono
            font.pixelSize: Typography.meta
        }
    }

    Text {
        visible: root.xTitle !== ""
        text: root.xTitle
        x: area.x + (area.width - width) / 2
        y: area.y + area.height + 25
        color: Theme.textMuted
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.4
    }

    // ---- plot area -------------------------------------------------------

    Item {
        id: area
        x: root.leftGutter
        y: root.topPadding
        width: Math.max(1, root.width - root.leftGutter - root.rightPadding)
        height: Math.max(1, root.height - root.topPadding - root.bottomGutter)

        // Grid and axes, painted below any series added by the caller.
        Canvas {
            id: grid
            anchors.fill: parent
            z: -1
            antialiasing: false

            readonly property color gridColor: Theme.gridLine
            readonly property color axisColor: Theme.axisLine

            onGridColorChanged: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.lineWidth = 1
                ctx.strokeStyle = gridColor
                ctx.beginPath()
                var i
                for (i = 0; i < root.yTickCount; ++i) {
                    var gy = Math.round(root.mapY(root.tickValue(i, root.yTickCount, root.yMin, root.yMax))) + 0.5
                    ctx.moveTo(0, gy)
                    ctx.lineTo(width, gy)
                }
                for (i = 0; i < root.xTickCount; ++i) {
                    var gx = Math.round(root.mapX(root.tickValue(i, root.xTickCount, root.xMin, root.xMax))) + 0.5
                    ctx.moveTo(gx, 0)
                    ctx.lineTo(gx, height)
                }
                ctx.stroke()

                // Axes sit one step stronger than the grid.
                ctx.strokeStyle = axisColor
                ctx.beginPath()
                ctx.moveTo(0.5, 0)
                ctx.lineTo(0.5, height)
                ctx.moveTo(0, height - 0.5)
                ctx.lineTo(width, height - 0.5)
                ctx.stroke()
            }
        }

        // ---- legend ------------------------------------------------------
        Row {
            visible: root.legend.length > 0
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 2
            spacing: Metrics.spacing.l

            Repeater {
                model: root.legend

                delegate: Row {
                    required property var modelData
                    spacing: Metrics.spacing.xs + 2

                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 14
                        height: 2
                        radius: 1
                        color: modelData.color
                        opacity: modelData.dashed !== undefined && modelData.dashed ? 0.55 : 1
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.name
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }
    }
}
