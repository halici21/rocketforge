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

    // Gutters grew with the chart type scale (Typography.axisTick): the
    // previous 74/34 were sized for 10px labels and clip an 11.5px mono
    // tick carrying four decimals.
    readonly property real padLeft: 82
    readonly property real padRight: 18
    readonly property real padTop: 16
    readonly property real padBottom: 42

    // ---- axis ticks ---------------------------------------------------
    // Ticks are placed at human numbers, not at even fractions of the data
    // range. The audit captures are the argument: dividing the range into
    // five equal parts produced y axes reading 529.09 / 110.33 / 23.01 /
    // 4.80 / 1.00 and x axes reading 0.02 / 1.02 / 2.01 / 3.01 / 4.00 --
    // an axis an engineer cannot read a value off of.
    //
    // The axis EXTENT still comes from the data (a range frame: the axis
    // spans where the data exists, per rf-scientific-visualization), so this
    // only chooses where inside that span a labelled line falls. It never
    // pads the range out to a round number, which would make the plot claim
    // a domain the solver was never asked about.
    function niceStep(raw) {
        if (!(raw > 0))
            return 1
        var exp = Math.floor(Math.log(raw) / Math.LN10)
        var pow = Math.pow(10, exp)
        var frac = raw / pow
        var nice = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 2.5 ? 2.5 : frac <= 5 ? 5 : 10
        return nice * pow
    }

    function niceTicks(lo, hi, target) {
        if (!(hi > lo) || !isFinite(lo) || !isFinite(hi))
            return [lo]
        var step = niceStep((hi - lo) / Math.max(1, target))
        var out = []
        var first = Math.ceil(lo / step - 1e-9) * step
        for (var v = first; v <= hi + step * 1e-9; v += step)
            out.push(Math.abs(v) < step * 1e-9 ? 0 : v)
        // A span narrower than one nice step leaves nothing inside it; fall
        // back to the two ends rather than an unlabelled axis.
        return out.length >= 2 ? out : [lo, hi]
    }

    // On a log axis the readable positions are the decades themselves, with
    // 2 and 5 filled in only when the span is short enough that decades
    // alone would leave two or three labels on a 600px axis.
    function niceLogTicks(lo, hi) {
        if (!(hi > lo) || !(lo > 0))
            return [lo, hi]
        var decLo = Math.floor(Math.log(lo) / Math.LN10)
        var decHi = Math.ceil(Math.log(hi) / Math.LN10)
        var mults = (decHi - decLo) <= 3 ? [1, 2, 5] : [1]
        var out = []
        for (var d = decLo; d <= decHi; ++d) {
            for (var m = 0; m < mults.length; ++m) {
                var v = mults[m] * Math.pow(10, d)
                if (v >= lo * (1 - 1e-9) && v <= hi * (1 + 1e-9))
                    out.push(v)
            }
        }
        return out.length >= 2 ? out : [lo, hi]
    }

    // A tick label, formatted from the STEP between ticks rather than the
    // value magnitude, so adjacent labels always differ and never carry
    // decimals the step cannot justify.
    function tickLabel(v, step) {
        if (v === 0)
            return "0"
        var av = Math.abs(v)
        if (av >= 100000 || av < 0.001)
            return v.toExponential(av >= 100000 ? 0 : 1)
        var dec = Math.max(0, -Math.floor(Math.log(step) / Math.LN10 + 1e-9))
        return v.toFixed(Math.min(6, dec))
    }

    onShowPointsChanged: plot.requestPaint()
    onPointsChanged: plot.requestPaint()
    onSeriesChanged: plot.requestPaint()
    onReferencePointsChanged: plot.requestPaint()
    onGuidesChanged: plot.requestPaint()
    onMarkersChanged: plot.requestPaint()
    onLogScaleChanged: plot.requestPaint()
    onMarkerXChanged: plot.requestPaint()

    // ---- hover inspection --------------------------------------------
    // The data extent and axis mapping a hover readout needs, kept in one
    // place so the crosshair overlay agrees exactly with what onPaint drew
    // -- duplicated from onPaint's own extent/log-scale logic rather than
    // refactored out of it, so the existing, already-visually-verified
    // paint path is untouched by this addition.
    function dataExtent() {
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
        var all = root.allSeries
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
        return { xmin: xmin, xmax: xmax, ymin: ymin, ymax: ymax }
    }

    // The point on the primary series nearest a plot-area pixel x, for the
    // hover readout. Null when there is nothing to find one in.
    function nearestPoint(pixelX) {
        var all = root.allSeries
        if (all.length === 0)
            return null
        var extent = root.dataExtent()
        var x0 = root.padLeft, x1 = root.width - root.padRight
        var dataX = extent.xmin + (pixelX - x0) / Math.max(1, x1 - x0) * (extent.xmax - extent.xmin)
        var pts = all[0].points
        var best = null, bestDist = Infinity
        for (var i = 0; i < pts.length; ++i) {
            var dist = Math.abs(pts[i].x - dataX)
            if (dist < bestDist) { bestDist = dist; best = pts[i] }
        }
        return best
    }

    property bool hoverActive: false
    property var hoverPoint: null

    MouseArea {
        x: root.padLeft
        y: root.padTop
        width: Math.max(0, root.width - root.padLeft - root.padRight)
        height: Math.max(0, root.height - root.padTop - root.padBottom)
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onPositionChanged: function (mouse) {
            root.hoverPoint = root.nearestPoint(root.padLeft + mouse.x)
            root.hoverActive = root.hoverPoint !== null
        }
        onExited: root.hoverActive = false
    }

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
            // grid, at nice-number tick positions inside the data range.
            // More divisions across than down: the plot is wider than it is
            // tall in every consumer, and the eye reads a curve along x.
            var yTicks = useLog ? root.niceLogTicks(ymin, ymax)
                                : root.niceTicks(ymin, ymax, 5)
            var xTicks = root.niceTicks(xmin, xmax, 6)
            var yStep = yTicks.length > 1 ? Math.abs(yTicks[1] - yTicks[0]) : (ymax - ymin)
            var xStep = xTicks.length > 1 ? Math.abs(xTicks[1] - xTicks[0]) : (xmax - xmin)

            ctx.strokeStyle = Theme.gridLine
            ctx.lineWidth = 1
            // The family must be quoted: an unquoted "Segoe UI" is parsed as
            // two tokens and the whole font string is rejected. Numbers are
            // set in the mono face so digits line up down the tick column,
            // matching RFPlotSurface and RFEngineeringTable.
            ctx.font = Typography.axisTick + 'px "' + Typography.mono + '"'
            ctx.fillStyle = Theme.textMuted
            var ti
            for (ti = 0; ti < yTicks.length; ++ti) {
                var py = ty(yTicks[ti])
                if (py < y0 - 0.5 || py > y1 + 0.5)
                    continue
                ctx.beginPath(); ctx.moveTo(x0, py); ctx.lineTo(x1, py); ctx.stroke()
                ctx.textAlign = "right"
                ctx.fillText(root.tickLabel(yTicks[ti], useLog ? yTicks[ti] : yStep),
                             x0 - 10, py + 4)
            }
            for (ti = 0; ti < xTicks.length; ++ti) {
                var px = tx(xTicks[ti])
                if (px < x0 - 0.5 || px > x1 + 0.5)
                    continue
                ctx.beginPath(); ctx.moveTo(px, y0); ctx.lineTo(px, y1); ctx.stroke()
                ctx.textAlign = "center"
                ctx.fillText(root.tickLabel(xTicks[ti], xStep), px, y1 + 18)
            }

            // axes
            ctx.strokeStyle = Theme.axisLine
            ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0, y1); ctx.lineTo(x1, y1); ctx.stroke()

            // Annotations are prose, not figures, so they leave the mono
            // tick face behind here and stay in it for the guide and marker
            // labels below -- all three are the same kind of text.
            ctx.font = Typography.chartAnnotation + 'px "' + Typography.sans + '"'

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
            //
            // Label placement is collision-aware. Every horizontal guide
            // used to right-align its label at the same fixed x (x1 - 4),
            // separated only by its own y -- so two guides at nearby
            // values (theta_max's own beta and the sonic beta, for one
            // real case captured in
            // acceptance/analysis_experience_r2/before/) drew their labels
            // directly on top of each other, illegible as two facts.
            // Occupied label bands are tracked here and a colliding label
            // is pushed clear rather than overdrawn.
            var placedBands = []
            function bandFree(top, bottom) {
                for (var b = 0; b < placedBands.length; ++b) {
                    if (top < placedBands[b].bottom && bottom > placedBands[b].top)
                        return false
                }
                return true
            }
            function claimBand(preferredY, height, lo, hi) {
                var half = height / 2
                var step = height + 2
                for (var attempt = 0; attempt < 12; ++attempt) {
                    var offset = Math.ceil(attempt / 2) * step * (attempt % 2 === 0 ? 1 : -1)
                    var centre = preferredY + offset
                    var top = centre - half, bottom = centre + half
                    if (top < lo || bottom > hi)
                        continue
                    if (bandFree(top, bottom)) {
                        placedBands.push({ top: top, bottom: bottom })
                        return centre
                    }
                }
                return NaN   // nowhere legible to put it: draw the line, drop the label
            }

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
                    if (horizontal) {
                        var placedY = claimBand(at - 6, 12, y0 + 2, y1 - 2)
                        if (!isNaN(placedY)) {
                            ctx.textAlign = "right"
                            ctx.fillText(guide.label, x1 - 4, placedY + 4)
                        }
                    } else {
                        ctx.textAlign = "center"
                        ctx.fillText(guide.label, at, y0 + 11)
                    }
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
                    // being clipped -- and, in that same zone, it shares the
                    // right-hand column with the guide labels above, so it
                    // claims a band there too rather than overdrawing one.
                    ctx.fillStyle = Theme.accent
                    var flip = mx > x1 - 90
                    ctx.textAlign = flip ? "right" : "left"
                    var markerY = my - 6
                    if (flip) {
                        var claimed = claimBand(my - 6, 12, y0 + 2, y1 - 2)
                        if (isNaN(claimed))
                            continue
                        markerY = claimed + 4
                    }
                    ctx.fillText(mk.label, mx + (flip ? -8 : 8), markerY)
                }
            }

            // The axis titles name the whole axis and carry its unit, so
            // they sit one step above the in-plot annotations.
            ctx.font = Typography.axisTitle + 'px "' + Typography.sans + '"'
            ctx.fillStyle = Theme.textMuted
            ctx.textAlign = "center"
            ctx.fillText(root.xLabel, (x0 + x1) / 2, height - 8)
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

    // A separate, lightweight overlay for the hover crosshair and readout,
    // repainted on every mouse move -- kept off the main `plot` Canvas so
    // hovering never re-triggers the full grid/curve/marker paint pass
    // (rf-qml-architecture's Canvas discipline: no frequently-repainted
    // content sharing a Canvas with content that must not be).
    Canvas {
        id: hover
        anchors.fill: parent
        z: 1
        renderStrategy: Canvas.Cooperative

        // Local mirrors of root's hover state, purely so their
        // auto-generated on<Name>Changed handlers can request a repaint --
        // `onHoverPointChanged` directly on this Canvas would refer to a
        // property this item does not have (root's, not its own), which
        // QML refuses to bind at all rather than silently no-op.
        property bool paintHoverActive: root.hoverActive
        property var paintHoverPoint: root.hoverPoint

        onPaintHoverActiveChanged: requestPaint()
        onPaintHoverPointChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)
            if (!root.hoverActive || root.hoverPoint === null)
                return

            var x0 = root.padLeft, x1 = width - root.padRight
            var y0 = root.padTop, y1 = height - root.padBottom
            var extent = root.dataExtent()
            var span = extent.xmax - extent.xmin
            var px = x0 + (root.hoverPoint.x - extent.xmin) / (span || 1) * (x1 - x0)

            ctx.strokeStyle = Theme.textMuted
            ctx.globalAlpha = 0.5
            ctx.setLineDash([3, 3])
            ctx.beginPath()
            ctx.moveTo(px, y0); ctx.lineTo(px, y1)
            ctx.stroke()
            ctx.setLineDash([])
            ctx.globalAlpha = 1

            // Fixed in the plot's own top-right corner rather than
            // following the cursor: a box that tracks the mouse can drift
            // over a guide line's own label (found by hovering directly on
            // the M=1 choking guide and opening the capture -- the two
            // overlapped exactly there, which is also the single most
            // likely place to hover). A fixed corner never competes with
            // cursor-adjacent, data-driven annotations.
            var text = root.xLabel + " " + root.hoverPoint.x.toPrecision(4)
                     + (root.yLabel ? "   " + root.yLabel + " " + root.hoverPoint.y.toPrecision(4) : "")
            ctx.font = Typography.axisTick + 'px "' + Typography.mono + '"'
            var metrics = ctx.measureText(text)
            var boxW = metrics.width + 12, boxH = 18
            var boxX = x1 - boxW
            var boxY = y0 + 4

            ctx.fillStyle = Theme.surfaceElevated
            ctx.strokeStyle = Theme.borderStrong
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.rect(boxX, boxY, boxW, boxH)
            ctx.fill(); ctx.stroke()

            ctx.fillStyle = Theme.text
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            ctx.fillText(text, boxX + boxW / 2, boxY + boxH / 2 + 1)
        }
    }

    function repaint() { plot.requestPaint() }
}
