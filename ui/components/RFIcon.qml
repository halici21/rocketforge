import QtQuick
import "../theme"

/*
 * RFIcon - the complete icon set, drawn as strokes on a 16x16 grid.
 *
 * Icons are drawn rather than shipped as assets for one reason: they have to
 * recolour with the theme, and a stroked path does that for free. The set is
 * deliberately tiny; the interface navigates by typography, not by pictograms.
 */
Canvas {
    id: root

    property string name: ""
    property color color: Theme.textSecondary
    property real strokeWidth: 1.4

    implicitWidth: 16
    implicitHeight: 16
    antialiasing: true

    onNameChanged: requestPaint()
    onColorChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.save()
        ctx.scale(width / 16, height / 16)
        ctx.strokeStyle = root.color
        ctx.fillStyle = root.color
        ctx.lineWidth = root.strokeWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.beginPath()

        switch (root.name) {
        case "chevron-down":
            ctx.moveTo(4, 6.5); ctx.lineTo(8, 10.5); ctx.lineTo(12, 6.5)
            break
        case "chevron-right":
            ctx.moveTo(6.5, 4); ctx.lineTo(10.5, 8); ctx.lineTo(6.5, 12)
            break
        case "chevron-left":
            ctx.moveTo(9.5, 4); ctx.lineTo(5.5, 8); ctx.lineTo(9.5, 12)
            break
        case "caret-up":
            ctx.moveTo(4.5, 9.5); ctx.lineTo(8, 6); ctx.lineTo(11.5, 9.5)
            break
        case "caret-down":
            ctx.moveTo(4.5, 6.5); ctx.lineTo(8, 10); ctx.lineTo(11.5, 6.5)
            break
        case "sun":
            ctx.arc(8, 8, 3, 0, Math.PI * 2)
            ctx.stroke()
            ctx.beginPath()
            for (var i = 0; i < 8; ++i) {
                var a = i * Math.PI / 4
                ctx.moveTo(8 + Math.cos(a) * 5.1, 8 + Math.sin(a) * 5.1)
                ctx.lineTo(8 + Math.cos(a) * 6.6, 8 + Math.sin(a) * 6.6)
            }
            break
        case "moon":
            // Crescent: an arc closed by a shallower return arc.
            ctx.arc(8, 8, 5.2, Math.PI * 0.35, Math.PI * 1.55)
            ctx.arc(5.6, 6.2, 5.2, Math.PI * 1.62, Math.PI * 0.28, true)
            break
        case "monitor":
            ctx.moveTo(2.5, 3.5); ctx.lineTo(13.5, 3.5); ctx.lineTo(13.5, 10.5)
            ctx.lineTo(2.5, 10.5); ctx.closePath()
            ctx.moveTo(6, 13); ctx.lineTo(10, 13)
            ctx.moveTo(8, 10.5); ctx.lineTo(8, 13)
            break
        case "settings":
            // Two parameter tracks with a setting mark on each: reads more
            // clearly at 16 px than a toothed gear.
            ctx.moveTo(2.5, 5.5); ctx.lineTo(13.5, 5.5)
            ctx.moveTo(2.5, 10.5); ctx.lineTo(13.5, 10.5)
            ctx.moveTo(10.5, 3.4); ctx.lineTo(10.5, 7.6)
            ctx.moveTo(5.5, 8.4); ctx.lineTo(5.5, 12.6)
            break
        case "panel-left":
            ctx.moveTo(2.5, 3.5); ctx.lineTo(13.5, 3.5); ctx.lineTo(13.5, 12.5)
            ctx.lineTo(2.5, 12.5); ctx.closePath()
            ctx.moveTo(6.5, 3.5); ctx.lineTo(6.5, 12.5)
            break
        case "export":
            ctx.moveTo(8, 10.5); ctx.lineTo(8, 2.8)
            ctx.moveTo(5.2, 5.6); ctx.lineTo(8, 2.8); ctx.lineTo(10.8, 5.6)
            ctx.moveTo(3, 9.5); ctx.lineTo(3, 13); ctx.lineTo(13, 13); ctx.lineTo(13, 9.5)
            break
        case "plus":
            ctx.moveTo(8, 3.5); ctx.lineTo(8, 12.5)
            ctx.moveTo(3.5, 8); ctx.lineTo(12.5, 8)
            break
        case "minus":
            ctx.moveTo(3.5, 8); ctx.lineTo(12.5, 8)
            break
        case "close":
            ctx.moveTo(4.4, 4.4); ctx.lineTo(11.6, 11.6)
            ctx.moveTo(11.6, 4.4); ctx.lineTo(4.4, 11.6)
            break
        case "check":
            ctx.moveTo(3.5, 8.4); ctx.lineTo(6.6, 11.5); ctx.lineTo(12.5, 4.8)
            break
        case "nozzle":
            // Product mark: a converging-diverging silhouette.
            ctx.moveTo(2, 2.6); ctx.lineTo(6.4, 8); ctx.lineTo(2, 13.4)
            ctx.moveTo(14, 3.4); ctx.lineTo(9.6, 8); ctx.lineTo(14, 12.6)
            break
        default:
            ctx.restore()
            return
        }

        ctx.stroke()
        ctx.restore()
    }
}
