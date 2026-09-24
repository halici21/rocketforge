import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"

/*
 * The nozzle itself: the engineering object this workspace analyses.
 *
 * WHAT THIS IS. The wall drawn from the SOLVED station distribution --
 * r(x) = sqrt(A(x)/pi) over the controller's own axial coordinate, straight
 * from Nozzle.contour. Both the radius and the axial position are solver
 * output, not presentation geometry, so unlike the Rocket Performance canvas
 * (which has no solved axial scale and says so) this drawing is to scale in
 * both directions and the aspect ratio is held at 1:1 deliberately: a nozzle
 * plotted on unequal axes reads as a flat tube, which is what the audit
 * capture of the "Nozzle contour" chart showed.
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
 * SOLVED axial stations -- the shock line is not placed by eye. The shock is
 * drawn across the section at that station and no further: in a quasi-1D
 * model it is a plane discontinuity at one area, not a resolved structure,
 * and the caption says so for as long as a shock is on the drawing.
 */
Item {
    id: root

    // Solved geometry, supplied by the caller from the controller.
    property var wall: []          // [{x, y}] upper wall
    property var stations: []      // [{value, axis, label}] throat / shock
    property bool hasResult: false
    // Optional second line per station, keyed by the station's label and
    // already formatted by the backend (e.g. { shock: "A_s/A_t 1.51009" }).
    // Text only; nothing here is evaluated.
    property var annotations: ({})
    // The drawing's own type size: the annotation token by default, the
    // axis-title step where the nozzle is the page's dominant object.
    property real labelSize: Typography.chartAnnotation

    implicitHeight: 190

    onWallChanged: shape.requestPaint()
    onStationsChanged: shape.requestPaint()
    onAnnotationsChanged: shape.requestPaint()
    onLabelSizeChanged: shape.requestPaint()

    // A Canvas cannot render markup, so an annotation carrying notation
    // ("A_s/A_t") is drawn one run at a time from Notation.runs -- the same
    // rules and the same run drawing RFLineChart uses for its labels.
    function notationFont(size, family, run) {
        var px = (run.sub || run.sup) ? Math.round(size * 0.72) : size
        return (run.italic ? "italic " : "") + px + 'px "' + family + '"'
    }

    function measureNotation(ctx, text, size, family) {
        var runs = Notation.runs(text)
        var width = 0
        for (var i = 0; i < runs.length; ++i) {
            ctx.font = root.notationFont(size, family, runs[i])
            width += ctx.measureText(runs[i].text).width
        }
        return width
    }

    function drawNotation(ctx, text, x, y, size, family, align) {
        var runs = Notation.runs(text)
        var width = root.measureNotation(ctx, text, size, family)
        var left = align === "right" ? x - width
                 : align === "left" ? x : x - width / 2
        var saved = ctx.textAlign
        ctx.textAlign = "left"
        for (var i = 0; i < runs.length; ++i) {
            var run = runs[i]
            ctx.font = root.notationFont(size, family, run)
            var dy = run.sub ? Math.round(size * 0.28)
                   : run.sup ? -Math.round(size * 0.38) : 0
            ctx.fillText(run.text, left, y + dy)
            left += ctx.measureText(run.text).width
        }
        ctx.textAlign = saved
    }

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

            var size = root.labelSize
            var lineStep = Math.round(size * 1.3)
            var sansFont = size + 'px "' + Typography.sans + '"'

            var xmin = pts[0].x, xmax = pts[0].x, rmax = 0
            for (var i = 0; i < pts.length; ++i) {
                if (pts[i].x < xmin) xmin = pts[i].x
                if (pts[i].x > xmax) xmax = pts[i].x
                if (Math.abs(pts[i].y) > rmax) rmax = Math.abs(pts[i].y)
            }
            var spanX = (xmax - xmin) || 1
            var spanY = (2 * rmax) || 1

            // The stations on the drawing, each at its own solved axial
            // position. The shock exists only while the solve has one.
            var marks = []
            var shockOnDrawing = false
            for (var s = 0; root.stations && s < root.stations.length; ++s) {
                var st = root.stations[s]
                if (st.axis !== "x" || st.value < xmin || st.value > xmax)
                    continue
                var shock = String(st.label).indexOf("shock") !== -1
                shockOnDrawing = shockOnDrawing || shock
                marks.push({ value: st.value, label: String(st.label), isShock: shock,
                             second: root.annotations && root.annotations[st.label]
                                     ? String(root.annotations[st.label]) : "" })
            }

            // The honesty label, in the page's own muted text rather than
            // its dimmest token -- this is a statement about what the
            // drawing claims, not a footnote. One clause per line, because
            // as one line it ran off the panel and the capture showed it cut
            // at "NOT A [", which is worse than not labelling the drawing at
            // all: a truncated qualifier still reads as a claim.
            var lines = ["SOLVED AREA DISTRIBUTION, DRAWN TO SCALE",
                         "SUPPLIED CONE, NOT A DESIGNED CONTOUR"]
            if (shockOnDrawing)
                lines.push("QUASI-1-D NORMAL SHOCK STATION, NOT A RESOLVED SHOCK")
            ctx.font = sansFont
            var captionW = 0
            for (var c = 0; c < lines.length; ++c)
                captionW = Math.max(captionW, ctx.measureText(lines[c]).width)

            var padX = 18, margin = 14

            // One scale for both directions. The drawing is to scale or it
            // is not a drawing of this nozzle.
            function fit(padTop, padBottom) {
                var availW = width - 2 * padX
                var availH = height - padTop - padBottom
                if (availW <= 0 || availH <= 0)
                    return null
                var k = Math.min(availW / spanX, availH / spanY)
                return { scale: k, drawnW: spanX * k,
                         originX: (width - spanX * k) / 2,
                         axisY: padTop + availH / 2 }
            }

            function labelWidth(mark) {
                ctx.font = sansFont
                var w = ctx.measureText(mark.label).width
                if (mark.second !== "")
                    w = Math.max(w, root.measureNotation(ctx, mark.second, size,
                                                         Typography.mono))
                return w
            }

            // Station labels are flags on a leader: the throat's to its
            // left, over the converging section, anything downstream to its
            // right. At a low area ratio the shock stands close behind the
            // throat and the capture once read "throaishock"; flags pointing
            // away from each other cannot collide. A label with no room on
            // its side turns round, and one that would still overprint
            // another is lifted a row. The LINES stay exactly where the
            // solver put them -- only the text moves.
            function place(g, rows) {
                var written = []
                var out = []
                var maxRow = 0
                for (var m = 0; m < marks.length; ++m) {
                    var mx = g.originX + (marks[m].value - xmin) * g.scale
                    var w = labelWidth(marks[m])
                    var sides = marks[m].label === "throat" ? ["left", "right"]
                                                            : ["right", "left"]
                    var chosen = null
                    for (var row = 0; row < rows && chosen === null; ++row) {
                        for (var q = 0; q < sides.length && chosen === null; ++q) {
                            var left = sides[q] === "right" ? mx + 6 : mx - 6 - w
                            if (left < 2 || left + w > width - 2)
                                continue
                            var clash = false
                            for (var n = 0; n < written.length; ++n)
                                if (written[n].row === row && left < written[n].right + 8
                                        && left + w + 8 > written[n].left)
                                    clash = true
                            if (!clash)
                                chosen = { row: row, side: sides[q], left: left }
                        }
                    }
                    if (chosen === null)
                        chosen = { row: 0, side: sides[0],
                                   left: sides[0] === "right" ? mx + 6 : mx - 6 - w }
                    written.push({ row: chosen.row, left: chosen.left,
                                   right: chosen.left + w })
                    maxRow = Math.max(maxRow, chosen.row)
                    out.push({ mark: marks[m], x: mx, side: chosen.side, row: chosen.row })
                }
                return { labels: out, rowsUsed: maxRow + 1 }
            }

            // Room above the wall for the labels, and the caption beside the
            // drawing where the drawing leaves room for it -- a to-scale
            // nozzle is often much narrower than its panel -- or beneath it
            // where it does not.
            var g = null, placed = null, captionBelow = false
            for (var rows = 1; rows <= 2; ++rows) {
                var padTop = margin + rows * 2 * lineStep
                captionBelow = false
                g = fit(padTop, margin)
                if (g !== null && (width - g.drawnW) / 2 < captionW + 24) {
                    captionBelow = true
                    g = fit(padTop, margin + lines.length * lineStep)
                }
                if (g === null)
                    return
                placed = place(g, 2)
                if (placed.rowsUsed <= rows)
                    break
            }

            function px(v) { return g.originX + (v - xmin) * g.scale }
            function py(r) { return g.axisY - r * g.scale }

            // The drawn wall's own radius at x: the same straight segments
            // the outline below is stroked with, read back so that a station
            // line meets the wall it is drawn on. Drawing, not physics.
            function wallAt(v) {
                for (var j = 1; j < pts.length; ++j) {
                    var a = pts[j - 1], b = pts[j]
                    if ((v >= a.x && v <= b.x) || (v <= a.x && v >= b.x)) {
                        var f = b.x === a.x ? 0 : (v - a.x) / (b.x - a.x)
                        return Math.abs(a.y + f * (b.y - a.y))
                    }
                }
                return rmax
            }

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
            ctx.moveTo(px(xmin), g.axisY)
            ctx.lineTo(px(xmax), g.axisY)
            ctx.stroke()
            ctx.setLineDash([])

            // Throat and shock. Each is drawn across the section at its own
            // station, wall to wall, and no further.
            var labelFloor = py(rmax) - 8
            for (var p = 0; p < placed.labels.length; ++p) {
                var item = placed.labels[p]
                var mark = item.mark
                var local = wallAt(mark.value)
                var lastY = labelFloor - item.row * 2 * lineStep
                var firstY = mark.second !== "" ? lastY - lineStep : lastY
                var topY = firstY - size

                ctx.strokeStyle = mark.isShock ? Theme.accent : markColor
                ctx.globalAlpha = mark.isShock ? 0.95 : 0.6
                ctx.lineWidth = mark.isShock ? 2 : 1
                if (!mark.isShock)
                    ctx.setLineDash([3, 3])
                ctx.beginPath()
                ctx.moveTo(item.x, py(local))
                ctx.lineTo(item.x, py(-local))
                ctx.stroke()
                ctx.setLineDash([])

                // The leader, from the wall up alongside the label.
                ctx.strokeStyle = markColor
                ctx.globalAlpha = 0.45
                ctx.lineWidth = 1
                ctx.beginPath()
                ctx.moveTo(item.x, py(local) - 3)
                ctx.lineTo(item.x, topY)
                ctx.stroke()
                ctx.globalAlpha = 1

                var anchorX = item.side === "right" ? item.x + 6 : item.x - 6
                ctx.font = sansFont
                ctx.textAlign = item.side === "right" ? "left" : "right"
                ctx.fillStyle = mark.isShock ? Theme.accent : markColor
                ctx.fillText(mark.label, anchorX, firstY)
                if (mark.second !== "") {
                    ctx.fillStyle = mark.isShock ? Theme.accent : Theme.textSecondary
                    root.drawNotation(ctx, mark.second, anchorX, lastY, size,
                                      Typography.mono, ctx.textAlign)
                }
            }

            ctx.font = sansFont
            ctx.fillStyle = markColor
            ctx.textAlign = captionBelow ? "center" : "right"
            var captionX = captionBelow ? width / 2 : width - 2
            for (c = 0; c < lines.length; ++c)
                ctx.fillText(lines[c], captionX,
                             height - 9 - (lines.length - 1 - c) * lineStep)
        }

        Connections {
            target: Theme
            function onModeChanged() { shape.requestPaint() }
        }
    }
}
