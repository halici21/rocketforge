import QtQuick
import "../theme"

/*
 * RFLineChart - a physics-agnostic engineering plot.
 *
 * It draws points it is given and nothing else. There is no equation here, no
 * gamma, no Mach relation, no theta-beta-M: the caller hands over arrays of
 * {x, y} computed by the backend, and this decides only where pixels go. That
 * separation is the whole reason the component exists as a component.
 *
 * Two ways to supply data, and they compose:
 *
 *   points            one series, the simple case (Mass Flow, Normal Shock)
 *   series            a list of { points, color, dashed, width, label },
 *                     for a curve with more than one branch
 *
 * Plus three kinds of annotation, all optional:
 *
 *   referencePoints   published values, drawn as discrete dots and never
 *                     joined - a printed table is a set of values, not a
 *                     continuous function
 *   guides            { value, axis: "x"|"y", label } dashed reference lines
 *   markers           { x, y, label } a solved operating point
 *
 * Axis ranges are taken from the data unless xMin/xMax/yMin/yMax are set, so a
 * caller that knows the physical range (0 to 90 degrees, say) can say so and
 * stop the axes breathing as the curve changes.
 */
Item {
    id: root

    property var points: []
    property var series: []
    property var referencePoints: []
    property var guides: []
    property var markers: []

    // Draw a dot at every supplied point as well as the line through them.
    // A sweep is a set of discrete solves, and the user has to be able to see
    // which mixture ratios were actually computed rather than reading a
    // continuous curve into a sampled one.
    property bool showPoints: false
    property real pointRadius: 2.0

    property bool logScale: true
    // Whether the log axis actually applied. It cannot when the data touches
    // or crosses zero - the Fanno friction parameter reaches exactly 0 at the
    // sonic point - and a toggle that silently does nothing is worse than one
    // that says why. Set by the paint pass, read by the pages.
    property bool logScaleActive: false
    property real markerX: NaN
    property string markerLabel: ""
    property string xLabel: "Mach number"
    property string yLabel: ""
    property color curveColor: Theme.accent

    // Optional explicit axis limits; NaN means "take it from the data".
    property real xMin: NaN
    property real xMax: NaN
    property real yMin: NaN
    property real yMax: NaN

    readonly property real padLeft: 74
    readonly property real padRight: 18
    readonly property real padTop: 14
    readonly property real padBottom: 34

    onShowPointsChanged: plot.requestPaint()
    onPointsChanged: plot.requestPaint()
    onSeriesChanged: plot.requestPaint()
    onReferencePointsChanged: plot.requestPaint()
    onGuidesChanged: plot.requestPaint()
    onMarkersChanged: plot.requestPaint()
    onLogScaleChanged: plot.requestPaint()
    onMarkerXChanged: plot.requestPaint()

    // The single-series form is expressed as a one-element series list, so the
    // drawing code below has exactly one path through it.
    readonly property var allSeries: {
        var out = []
        if (root.points && root.points.length > 0)
            out.push({ points: root.points, color: root.curveColor, dashed: false, width: 1.6 })
        for (var i = 0; root.series && i < root.series.length; ++i) {
            var s = root.series[i]
            if (s && s.points && s.points.length > 0)
                out.push({
                    points: s.points,
                    color: s.color !== undefined ? s.color : root.curveColor,
                    dashed: s.dashed === true,
                    width: s.width !== undefined ? s.width : 1.6
                })
        }
        return out
    }

    Canvas {
        id: plot
        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)

            var all = root.allSeries
            var total = 0
            for (var s = 0; s < all.length; ++s)
                total += all[s].points.length
            if (total < 2)
                return

            var x0 = root.padLeft, x1 = width - root.padRight
            var y0 = root.padTop, y1 = height - root.padBottom

            // Extents of the supplied points. No physics: this is the range of
            // numbers handed to the canvas, nothing more.
            var xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity
            function widen(list) {
                for (var k = 0; list && k < list.length; ++k) {
                    var p = list[k]
                    if (p.x < xmin) xmin = p.x
                    if (p.x > xmax) xmax = p.x
                    if (p.y < ymin) ymin = p.y
                    if (p.y > ymax) ymax = p.y
                }
            }
            for (var q = 0; q < all.length; ++q)
                widen(all[q].points)
            widen(root.referencePoints)
            for (var g = 0; root.markers && g < root.markers.length; ++g) {
                var m = root.markers[g]
                if (m.x < xmin) xmin = m.x
                if (m.x > xmax) xmax = m.x
                if (m.y < ymin) ymin = m.y
                if (m.y > ymax) ymax = m.y
            }

            if (!isNaN(root.xMin)) xmin = root.xMin
            if (!isNaN(root.xMax)) xmax = root.xMax
            if (!isNaN(root.yMin)) ymin = root.yMin
            if (!isNaN(root.yMax)) ymax = root.yMax

            var useLog = root.logScale && ymin > 0 && (ymax / ymin) > 20
            root.logScaleActive = useLog
            function ty(v) {
                if (useLog) {
                    var lo = Math.log(ymin), hi = Math.log(ymax)
                    return y1 - (Math.log(v) - lo) / (hi - lo) * (y1 - y0)
                }
                return y1 - (v - ymin) / (ymax - ymin || 1) * (y1 - y0)
            }
            function tx(v) {
                return x0 + (v - xmin) / (xmax - xmin || 1) * (x1 - x0)
            }
            // Tick labels are formatted from the axis SPAN, not from the
            // magnitude alone. A molar-mass axis running 0.0185 to 0.0242 has
            // every value rounding to "0.02", and five identical tick labels
            // are worse than none: the reader cannot tell the axis apart from
            // a flat line. So the decimal count is whatever it takes for
            // adjacent ticks to differ, capped so a label stays readable.
            function decimalsFor(span) {
                if (!(span > 0))
                    return 2
                var d = Math.max(0, Math.ceil(-Math.log(span / 4) / Math.LN10) + 1)
                return Math.min(6, d)
            }
            function label(v, span) {
                if (Math.abs(v) >= 1000 || (v !== 0 && Math.abs(v) < 0.01))
                    return v.toExponential(1)
                return v.toFixed(Math.max(2, decimalsFor(span)))
            }

            // grid
            ctx.strokeStyle = Theme.gridLine
            ctx.lineWidth = 1
            // The family must be quoted: an unquoted "Segoe UI" is parsed as
            // two tokens and the whole font string is rejected.
            ctx.font = '10px "' + Typography.sans + '"'
            ctx.fillStyle = Theme.textMuted
            for (var gy = 0; gy <= 4; ++gy) {
                var py = y0 + (y1 - y0) * gy / 4
                ctx.beginPath(); ctx.moveTo(x0, py); ctx.lineTo(x1, py); ctx.stroke()
                var val = useLog
                    ? Math.exp(Math.log(ymax) - (Math.log(ymax) - Math.log(ymin)) * gy / 4)
                    : ymax - (ymax - ymin) * gy / 4
                ctx.textAlign = "right"
                ctx.fillText(label(val, useLog ? val : ymax - ymin), x0 - 8, py + 3)
            }
            for (var gx = 0; gx <= 5; ++gx) {
                var px = x0 + (x1 - x0) * gx / 5
                ctx.beginPath(); ctx.moveTo(px, y0); ctx.lineTo(px, y1); ctx.stroke()
                ctx.textAlign = "center"
                ctx.fillText(label(xmin + (xmax - xmin) * gx / 5, xmax - xmin), px, y1 + 16)
            }

            // axes
            ctx.strokeStyle = Theme.axisLine
            ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0, y1); ctx.lineTo(x1, y1); ctx.stroke()

            // the simple vertical reference (M = 1, usually)
            if (!isNaN(root.markerX) && xmin < root.markerX && xmax > root.markerX) {
                ctx.strokeStyle = Theme.accent
                ctx.globalAlpha = 0.45
                ctx.setLineDash([3, 3])
                ctx.beginPath()
                ctx.moveTo(tx(root.markerX), y0); ctx.lineTo(tx(root.markerX), y1)
                ctx.stroke()
                ctx.setLineDash([]); ctx.globalAlpha = 1
                ctx.fillStyle = Theme.accent
                ctx.textAlign = "left"
                ctx.fillText(root.markerLabel, tx(root.markerX) + 4, y0 + 11)
            }

            // named guide lines
            for (var gi = 0; root.guides && gi < root.guides.length; ++gi) {
                var guide = root.guides[gi]
                var horizontal = guide.axis === "y"
                var at = horizontal ? ty(guide.value) : tx(guide.value)
                if (horizontal ? (guide.value < ymin || guide.value > ymax)
                               : (guide.value < xmin || guide.value > xmax))
                    continue
                ctx.strokeStyle = Theme.textMuted
                ctx.globalAlpha = 0.55
                ctx.setLineDash([4, 4])
                ctx.beginPath()
                if (horizontal) { ctx.moveTo(x0, at); ctx.lineTo(x1, at) }
                else            { ctx.moveTo(at, y0); ctx.lineTo(at, y1) }
                ctx.stroke()
                ctx.setLineDash([]); ctx.globalAlpha = 1
                if (guide.label) {
                    ctx.fillStyle = Theme.textMuted
                    ctx.textAlign = horizontal ? "right" : "center"
                    if (horizontal) ctx.fillText(guide.label, x1 - 4, at - 4)
                    else            ctx.fillText(guide.label, at, y0 + 11)
                }
            }

            // the curves
            for (var si = 0; si < all.length; ++si) {
                var line = all[si]
                ctx.strokeStyle = line.color
                ctx.lineWidth = line.width
                if (line.dashed) ctx.setLineDash([6, 4])
                ctx.beginPath()
                ctx.moveTo(tx(line.points[0].x), ty(line.points[0].y))
                for (var pi = 1; pi < line.points.length; ++pi)
                    ctx.lineTo(tx(line.points[pi].x), ty(line.points[pi].y))
                ctx.stroke()
                ctx.setLineDash([])
            }

            // the sampled points themselves, so a discrete sweep never reads
            // as a continuous function
            if (root.showPoints) {
                for (var ps = 0; ps < all.length; ++ps) {
                    ctx.fillStyle = all[ps].color
                    var pts = all[ps].points
                    for (var pp = 0; pp < pts.length; ++pp) {
                        ctx.beginPath()
                        ctx.arc(tx(pts[pp].x), ty(pts[pp].y),
                                root.pointRadius, 0, 2 * Math.PI)
                        ctx.fill()
                    }
                }
            }

            // published values, as discrete points and never joined
            if (root.referencePoints && root.referencePoints.length > 0) {
                ctx.fillStyle = Theme.textSecondary
                for (var ri = 0; ri < root.referencePoints.length; ++ri) {
                    var rp = root.referencePoints[ri]
                    var rx = tx(rp.x), ry = ty(rp.y)
                    if (rx < x0 || rx > x1 || ry < y0 || ry > y1)
                        continue
                    ctx.beginPath(); ctx.arc(rx, ry, 2.2, 0, 2 * Math.PI); ctx.fill()
                }
            }

            // the solved operating point
            for (var mi = 0; root.markers && mi < root.markers.length; ++mi) {
                var mk = root.markers[mi]
                if (isNaN(mk.x) || isNaN(mk.y))
                    continue
                var mx = tx(mk.x), my = ty(mk.y)
                ctx.strokeStyle = Theme.accent
                ctx.fillStyle = Theme.surface
                ctx.lineWidth = 2
                ctx.beginPath(); ctx.arc(mx, my, 4.5, 0, 2 * Math.PI)
                ctx.fill(); ctx.stroke()
                if (mk.label) {
                    // Near the right edge the label would run off the plot, so
                    // it flips to the other side of the marker rather than
                    // being clipped.
                    ctx.fillStyle = Theme.accent
                    var flip = mx > x1 - 90
                    ctx.textAlign = flip ? "right" : "left"
                    ctx.fillText(mk.label, mx + (flip ? -8 : 8), my - 6)
                }
            }

            ctx.fillStyle = Theme.textMuted
            ctx.textAlign = "center"
            ctx.fillText(root.xLabel, (x0 + x1) / 2, height - 6)
            if (root.yLabel) {
                ctx.save()
                ctx.translate(14, (y0 + y1) / 2)
                ctx.rotate(-Math.PI / 2)
                ctx.textAlign = "center"
                ctx.fillText(root.yLabel, 0, 0)
                ctx.restore()
            }
        }
    }

    function repaint() { plot.requestPaint() }
}
