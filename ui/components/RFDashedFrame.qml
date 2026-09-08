import QtQuick
import "../theme"

/*
 * A dashed outline with an optional label. Reserved space, drawn so that it
 * cannot be mistaken for a surface that failed to load.
 */
Item {
    id: root

    property string label: ""
    property color strokeColor: Theme.border
    property real radius: Metrics.radius.l

    implicitWidth: 120
    implicitHeight: 44

    Canvas {
        id: frame
        anchors.fill: parent
        antialiasing: true

        readonly property color stroke: root.strokeColor
        onStrokeChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = stroke
            ctx.lineWidth = 1
            ctx.setLineDash([5, 5])

            var r = Math.min(root.radius, width / 2, height / 2)
            var w = width - 0.5
            var h = height - 0.5
            ctx.beginPath()
            ctx.moveTo(0.5 + r, 0.5)
            ctx.lineTo(w - r, 0.5)
            ctx.quadraticCurveTo(w, 0.5, w, 0.5 + r)
            ctx.lineTo(w, h - r)
            ctx.quadraticCurveTo(w, h, w - r, h)
            ctx.lineTo(0.5 + r, h)
            ctx.quadraticCurveTo(0.5, h, 0.5, h - r)
            ctx.lineTo(0.5, 0.5 + r)
            ctx.quadraticCurveTo(0.5, 0.5, 0.5 + r, 0.5)
            ctx.stroke()
        }
    }

    Text {
        anchors.centerIn: parent
        visible: root.label !== ""
        text: root.label
        color: Theme.textDisabled
        font.family: Typography.sans
        font.pixelSize: Typography.meta
        font.letterSpacing: 0.6
        font.capitalization: Font.AllUppercase
    }
}
