import QtQuick
import "../theme"

/*
 * A dashed guide line. Guides are dashed everywhere in the application so that
 * a reference level can never be mistaken for a data curve.
 */
Canvas {
    id: root

    property bool vertical: false
    property color color: Theme.textMuted
    property real thickness: Metrics.hairline
    property var pattern: [4, 4]

    implicitWidth: vertical ? 1 : 100
    implicitHeight: vertical ? 100 : 1
    height: vertical ? implicitHeight : Math.max(1, thickness)
    width: vertical ? Math.max(1, thickness) : implicitWidth

    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.strokeStyle = root.color
        ctx.lineWidth = root.thickness
        ctx.setLineDash(root.pattern)
        ctx.beginPath()
        if (vertical) {
            ctx.moveTo(width / 2, 0)
            ctx.lineTo(width / 2, height)
        } else {
            ctx.moveTo(0, height / 2)
            ctx.lineTo(width, height / 2)
        }
        ctx.stroke()
    }
}
