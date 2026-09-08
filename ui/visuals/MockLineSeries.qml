import QtQuick
import "../theme"

/*
 * One polyline drawn inside an RFPlotSurface.
 *
 * The component knows how to draw a sequence of points; it never produces
 * them. Points arrive either as [x, y] pairs or as a y-value array with a
 * uniform x step, and are hand-authored constants in this phase.
 */
Canvas {
    id: root

    property Item plot: null
    property var points: []          // [[x, y], ...]
    property var values: []          // alternative: y only
    property real xStart: 0
    property real xStep: 1

    property color color: Theme.textSecondary
    property real thickness: 1.6
    property bool dashed: false

    anchors.fill: parent
    antialiasing: true

    onPointsChanged: requestPaint()
    onValuesChanged: requestPaint()
    onColorChanged: requestPaint()
    onOpacityChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    function samples() {
        if (points.length > 0)
            return points
        var out = []
        for (var i = 0; i < values.length; ++i)
            out.push([xStart + i * xStep, values[i]])
        return out
    }

    onPaint: {
        if (!plot)
            return
        var data = samples()
        if (data.length < 2)
            return

        var ctx = getContext("2d")
        ctx.reset()
        ctx.lineWidth = thickness
        ctx.lineJoin = "round"
        ctx.lineCap = "round"
        ctx.strokeStyle = root.color
        if (dashed)
            ctx.setLineDash([4, 4])

        ctx.beginPath()
        for (var i = 0; i < data.length; ++i) {
            var px = plot.mapX(data[i][0])
            var py = plot.mapY(data[i][1])
            if (i === 0)
                ctx.moveTo(px, py)
            else
                ctx.lineTo(px, py)
        }
        ctx.stroke()
    }
}
