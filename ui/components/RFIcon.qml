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

        // ---- navigation families ------------------------------------
        // One mark per family, each drawn from that domain's own subject
        // rather than from a generic pictogram set: the rail used to be
        // seven uppercase words (FLOW / CHEM / PROP / TRADE / FLUID / REF)
        // which carry no recognition at a glance. The label stays under
        // each mark -- an icon alone would be a guessing game, and this
        // interface still navigates by typography first.

        case "home":
            // Workbench overview: four workspace tiles. Rounded corners
            // implied by the stroke radius rather than fill, so the grid
            // reads as a dashboard rather than a window manager.
            ctx.rect(2.2, 2.2, 5.2, 5.2)
            ctx.rect(8.6, 2.2, 5.2, 5.2)
            ctx.rect(2.2, 8.6, 5.2, 5.2)
            ctx.rect(8.6, 8.6, 5.2, 5.2)
            break

        case "flow":
            // Converging-diverging nozzle walls with a centre streamline
            // and arrowhead. The walls converge to a throat at x=8, then
            // diverge -- the defining shape of compressible flow analysis.
            ctx.moveTo(2, 2.4)
            ctx.bezierCurveTo(5.5, 2.4, 6.5, 6, 8, 6.4)
            ctx.bezierCurveTo(9.5, 6.8, 11, 4.4, 14, 3.6)
            ctx.moveTo(2, 13.6)
            ctx.bezierCurveTo(5.5, 13.6, 6.5, 10, 8, 9.6)
            ctx.bezierCurveTo(9.5, 9.2, 11, 11.6, 14, 12.4)
            ctx.moveTo(3, 8); ctx.lineTo(11, 8)
            ctx.moveTo(9.2, 6.4); ctx.lineTo(11.4, 8); ctx.lineTo(9.2, 9.6)
            break

        case "chem":
            // Combustion chamber cross-section with injector dome and a
            // flame tongue inside. Chemistry in this product is combustion
            // chemistry, not bench chemistry -- the flask confused both
            // contact-sheet reviewers because it sat next to a rocket motor.
            // Outer chamber walls:
            ctx.moveTo(4.4, 2.2); ctx.lineTo(11.6, 2.2)  // injector plate
            ctx.lineTo(11.6, 10.6); ctx.lineTo(10, 12.8)  // converging wall R
            ctx.lineTo(6, 12.8); ctx.lineTo(4.4, 10.6)    // converging wall L
            ctx.closePath()
            ctx.stroke()
            // Flame tongue (drawn separately so it does not close into walls):
            ctx.beginPath()
            ctx.moveTo(8, 10.8)
            ctx.bezierCurveTo(6.6, 8.2, 6.8, 6.6, 8, 4.6)
            ctx.bezierCurveTo(9.2, 6.6, 9.4, 8.2, 8, 10.8)
            break

        case "prop":
            // Rocket motor cross-section: injector dome, cylindrical
            // chamber, converging throat and a bell-curve diverging nozzle.
            // The bell curve is what distinguishes this from "chem" at 20px.
            // Injector dome (arc at top):
            ctx.moveTo(5.6, 4)
            ctx.bezierCurveTo(5.6, 2.2, 10.4, 2.2, 10.4, 4)
            // Chamber walls:
            ctx.lineTo(10.4, 6.8)
            // Diverging bell (right wall):
            ctx.bezierCurveTo(10.4, 9.6, 11.6, 11.8, 13.6, 13.8)
            // Exit plane:
            ctx.lineTo(2.4, 13.8)
            // Diverging bell (left wall):
            ctx.bezierCurveTo(4.4, 11.8, 5.6, 9.6, 5.6, 6.8)
            ctx.closePath()
            break

        case "trade":
            // Design-space scatter with a Pareto front curve. Axes frame
            // the data; three filled dots are dominated points, and the
            // curve through two front points is what makes this "trade
            // study" rather than a generic chart.
            // Axes:
            ctx.moveTo(2.8, 2.2); ctx.lineTo(2.8, 13.4); ctx.lineTo(13.8, 13.4)
            ctx.stroke()
            // Pareto front curve (the distinctive mark):
            ctx.beginPath()
            ctx.moveTo(4.8, 4.4)
            ctx.bezierCurveTo(6.4, 4.6, 9.2, 7.2, 12.2, 11.2)
            ctx.stroke()
            // Front points (filled):
            ctx.beginPath()
            ctx.arc(4.8, 4.4, 1.2, 0, 2 * Math.PI)
            ctx.arc(12.2, 11.2, 1.2, 0, 2 * Math.PI)
            ctx.fill()
            // Dominated points (stroked):
            ctx.beginPath()
            ctx.arc(7.4, 10, 1.0, 0, 2 * Math.PI)
            ctx.arc(10.4, 6.6, 1.0, 0, 2 * Math.PI)
            break

        case "fluid":
            // A cryogenic droplet with a small feed-line stub above it,
            // grounding this in propellant delivery rather than weather.
            // Feed-line stub:
            ctx.moveTo(8, 1.4); ctx.lineTo(8, 3.6)
            ctx.stroke()
            // Droplet body:
            ctx.beginPath()
            ctx.moveTo(8, 3.6)
            ctx.bezierCurveTo(11.4, 6.8, 12.8, 8.6, 12.8, 10.4)
            ctx.bezierCurveTo(12.8, 12.8, 10.6, 14.2, 8, 14.2)
            ctx.bezierCurveTo(5.4, 14.2, 3.2, 12.8, 3.2, 10.4)
            ctx.bezierCurveTo(3.2, 8.6, 4.6, 6.8, 8, 3.6)
            break

        case "reference":
            // An open reference book with a bookmark tab on the right
            // page -- the tab distinguishes this from a generic book at
            // rail size, and reads as "look something up".
            ctx.moveTo(8, 4.4); ctx.lineTo(8, 13)
            ctx.moveTo(8, 4.4)
            ctx.lineTo(3.6, 3); ctx.lineTo(2.2, 3.4); ctx.lineTo(2.2, 11.6)
            ctx.lineTo(3.6, 11.2); ctx.lineTo(8, 13)
            ctx.moveTo(8, 4.4)
            ctx.lineTo(12.4, 3); ctx.lineTo(13.8, 3.4); ctx.lineTo(13.8, 11.6)
            ctx.lineTo(12.4, 11.2); ctx.lineTo(8, 13)
            ctx.stroke()
            // Bookmark tab:
            ctx.beginPath()
            ctx.moveTo(11.4, 3.4); ctx.lineTo(11.4, 6.6)
            ctx.lineTo(10.6, 5.8); ctx.lineTo(9.8, 6.6); ctx.lineTo(9.8, 3.4)
            break
        default:
            ctx.restore()
            return
        }

        ctx.stroke()
        ctx.restore()
    }
}
