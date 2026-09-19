import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"

/*
 * The nozzle itself: the engineering object this workspace analyses.
 *
 * WHAT THIS IS. The wall drawn from the SOLVED station distribution --
 * r(x) = sqrt(A(x)/pi) over the controller's own axial coordinate, straight
 * from Nozzle.contourSeries(). Both the radius and the axial position are
 * solver output, not presentation geometry, so unlike the Rocket Performance
 * canvas (which has no solved axial scale and says so) this drawing is to
 * scale in both directions and the aspect ratio is held at 1:1 deliberately:
 * a nozzle plotted on unequal axes reads as a flat tube, which is what the
 * audit capture of the "Nozzle contour" chart showed.
 *
 * WHAT THIS IS NOT. Not a designed contour. The area distribution analysed
 * here is a straight-walled cone supplied to the module, not a bell, a Rao
 * profile or an optimised wall -- the module analyses a distribution, it does
 * not design one. The label on the drawing says exactly that.
 *
 * NO FABRICATED FIELD. The interior carries a flat fill and nothing else: no
 * gradient, no Mach shading, no plume, no streamlines. RocketForge solves a
 * quasi-1D station distribution, not a field, and a gradient across this
 * shape would claim a field solution that does not exist
 * (rf-propulsion-visual-grammar: no fake CFD, ever).
 *
 * The throat and, when one exists, the normal shock are marked at their own
 * SOLVED axial stations -- the shock line is not placed by eye.
 */
Item {
    id: root

    // Solved geometry, supplied by the caller from the controller.
    property var wall: []          // [{x, y}] upper wall
    property var stations: []      // [{value, axis, label}] throat / shock
    property bool hasResult: false

    implicitHeight: 190

    onWallChanged: shape.requestPaint()
    onStationsChanged: shape.requestPaint()

    Canvas {
        id: shape
        anchors.fill: parent

        readonly property color wallColor: Theme.textSecondary
        readonly property color fillColor: Theme.surfaceElevated
        readonly property color markColor: Theme.textMuted
        readonly property color axisColor: Theme.divider

        onWallColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)

            var pts = root.wall
            if (!root.hasResult || !pts || pts.length < 2)
                return

            var padX = 18, padTop = 40, padBottom = 42
            var xmin = pts[0].x, xmax = pts[0].x, rmax = 0
            for (var i = 0; i < pts.length; ++i) {
                if (pts[i].x < xmin) xmin = pts[i].x
                if (pts[i].x > xmax) xmax = pts[i].x
                if (Math.abs(pts[i].y) > rmax) rmax = Math.abs(pts[i].y)
            }
            var spanX = (xmax - xmin) || 1
            var spanY = (2 * rmax) || 1

            // One scale for both directions. The drawing is to scale or it
            // is not a drawing of this nozzle.
            var availW = width - 2 * padX
            var availH = height - padTop - padBottom
            var scale = Math.min(availW / spanX, availH / spanY)
            var originX = (width - spanX * scale) / 2
            var axisY = padTop + availH / 2

            function px(v) { return originX + (v - xmin) * scale }
            function py(r) { return axisY - r * scale }

            // The body: upper wall, across the exit plane, back along the
            // mirrored wall. One closed path, flat fill.
            ctx.beginPath()
            ctx.moveTo(px(pts[0].x), py(pts[0].y))
            var k
            for (k = 1; k < pts.length; ++k)
                ctx.lineTo(px(pts[k].x), py(pts[k].y))
            for (k = pts.length - 1; k >= 0; --k)
                ctx.lineTo(px(pts[k].x), py(-pts[k].y))
            ctx.closePath()
            ctx.fillStyle = fillColor
            ctx.fill()
            ctx.strokeStyle = wallColor
            ctx.lineWidth = 1.4
            ctx.stroke()

            // The centreline, one step quieter than the wall.
            ctx.strokeStyle = axisColor
            ctx.lineWidth = 1
            ctx.setLineDash([4, 4])
            ctx.beginPath()
            ctx.moveTo(px(xmin), axisY)
            ctx.lineTo(px(xmax), axisY)
            ctx.stroke()
            ctx.setLineDash([])

            // Throat and shock, each at its own solved axial station.
            //
            // At a low area ratio the shock stands close behind the throat,
            // so the two labels land on top of each other -- the capture
            // read "throaishock". Track what has been written and lift a
            // colliding label onto its own line rather than overprinting;
            // the LINES stay exactly where the solver put them, only the
            // text moves.
            ctx.font = Typography.chartAnnotation + 'px "' + Typography.sans + '"'
            var writtenSpans = []
            function labelRow(centre, halfWidth) {
                for (var row = 0; row < 3; ++row) {
                    var clash = false
                    for (var w = 0; w < writtenSpans.length; ++w) {
                        var span = writtenSpans[w]
                        if (span.row === row
                                && centre - halfWidth < span.right
                                && centre + halfWidth > span.left) {
                            clash = true
                            break
                        }
                    }
                    if (!clash) {
                        writtenSpans.push({ row: row, left: centre - halfWidth,
                                            right: centre + halfWidth })
                        return row
                    }
                }
                return 0
            }
            for (var s = 0; root.stations && s < root.stations.length; ++s) {
                var mark = root.stations[s]
                if (mark.axis !== "x" || mark.value < xmin || mark.value > xmax)
                    continue
                var mx = px(mark.value)
                var isShock = String(mark.label).indexOf("shock") !== -1
                ctx.strokeStyle = isShock ? Theme.accent : markColor
                ctx.globalAlpha = isShock ? 0.9 : 0.55
                ctx.lineWidth = isShock ? 1.6 : 1
                if (!isShock)
                    ctx.setLineDash([3, 3])
                ctx.beginPath()
                ctx.moveTo(mx, py(rmax) - 4)
                ctx.lineTo(mx, py(-rmax) + 4)
                ctx.stroke()
                ctx.setLineDash([])
                ctx.globalAlpha = 1
                ctx.fillStyle = isShock ? Theme.accent : markColor
                ctx.textAlign = "center"
                var halfW = ctx.measureText(mark.label).width / 2 + 3
                ctx.fillText(mark.label, mx,
                             py(rmax) - 9 - labelRow(mx, halfW) * 13)
            }

            // The honesty label, in the page's own muted text rather than
            // its dimmest token -- this is a statement about what the
            // drawing claims, not a footnote. Two lines, because as one it
            // ran off the panel and the capture showed it cut at "NOT A [",
            // which is worse than not labelling the drawing at all: a
            // truncated qualifier still reads as a claim.
            ctx.fillStyle = markColor
            ctx.textAlign = "center"
            var mid = width / 2
            ctx.fillText("SOLVED AREA DISTRIBUTION, DRAWN TO SCALE", mid, height - 22)
            ctx.fillText("SUPPLIED CONE, NOT A DESIGNED CONTOUR", mid, height - 9)
        }

        Connections {
            target: Theme
            function onModeChanged() { shape.requestPaint() }
        }
    }
}
