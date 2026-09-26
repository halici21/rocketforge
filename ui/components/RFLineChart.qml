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
 *   markers           { x, y, label } a solved operating point; an optional
 *                     slope (+1 rising, -1 falling, the curve's direction
 *                     through the point) puts the label on the side of the
 *                     ring the curve does not run through
 *
 * Axis ranges are taken from the data unless xMin/xMax/yMin/yMax are set, so a
 * caller that knows the physical range (0 to 90 degrees, say) can say so and
 * stop the axes breathing as the curve changes.
 *
 * Interaction is a separate layer (RFPlotInteraction) that sets the view
 * range below: zoom, pan and the analysis lens move the axes over the same
 * data and never change a value. The log/linear decision is made on the full
 * data range, so zooming in never switches the axis mode under the reader.
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
    // The marker is M = 1 on a Mach axis, and the plot is tinted subsonic /
    // supersonic either side of it. On any other axis (O/F, a design
    // variable) the marker is only a reference line: set this false, or a
    // selected O/F would be labelled as a sonic boundary.
    property bool markerRegions: true
    property string xLabel: "Mach number"
    property string yLabel: ""
    property color curveColor: Theme.accent

    // Optional explicit axis limits; NaN means "take it from the data".
    property real xMin: NaN
    property real xMax: NaN
    property real yMin: NaN
    property real yMax: NaN

    // The range being looked at, set by an interaction layer (zoom, pan, the
    // analysis lens). NaN = the full range. Presentation only.
    property real viewXMin: NaN
    property real viewXMax: NaN
    property real viewYMin: NaN
    property real viewYMax: NaN
    readonly property bool zoomed: !isNaN(root.viewXMin) || !isNaN(root.viewYMin)

    // What is plotted (a quantity key). A new solve of the same quantity on
    // the same x grid may ease from the previous curve to the new one; the
    // in-between frames are drawn only -- never read by a hover, an
    // inspector or a copy, which always see the final data.
    property string dataKey: ""
    // The built-in hover readout. An interaction layer replaces it.
    property bool builtInHover: true

    onViewXMinChanged: plot.requestPaint()
    onViewXMaxChanged: plot.requestPaint()
    onViewYMinChanged: plot.requestPaint()
    onViewYMaxChanged: plot.requestPaint()

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

    // ---- notation on a Canvas ----------------------------------------------
    // A Canvas cannot render markup, so a label with notation ("Isp",
    // "p_b/p0") is drawn one run at a time: italic for a quantity symbol, a
    // smaller font lowered by a fixed share of the size for a subscript. The
    // runs come from Notation, the same rules every Text label uses.
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
        ctx.font = size + 'px "' + family + '"'
        return width
    }

    function drawNotation(ctx, text, x, y, align, size, family) {
        var runs = Notation.runs(text)
        var width = root.measureNotation(ctx, text, size, family)
        var left = align === "center" ? x - width / 2
                 : align === "right" ? x - width : x
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
        ctx.font = size + 'px "' + family + '"'
        return width
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
    onPointsChanged: { plot.seriesArrived(); plot.requestPaint() }
    onSeriesChanged: { plot.seriesArrived(); plot.requestPaint() }
    onReferencePointsChanged: plot.requestPaint()
    onGuidesChanged: plot.requestPaint()
    onMarkersChanged: { plot.markersArrived(); plot.requestPaint() }
    onLogScaleChanged: plot.requestPaint()
    onMarkerXChanged: plot.requestPaint()
    onCurveColorChanged: plot.requestPaint()

    // A theme change recolours every stroke and fill this canvas paints while
    // its data stays exactly the same, so no data signal arrives to repaint
    // it: a chart whose inputs do not mention a colour kept the previous
    // theme's plot on screen after the toggle. Repaint on the theme itself.
    Connections {
        target: Theme
        function onModeChanged() { plot.requestPaint() }
    }

    // ---- hover inspection --------------------------------------------
    // The data extent and axis mapping a hover readout needs, kept in one
    // place so the crosshair overlay agrees exactly with what onPaint drew
    // -- duplicated from onPaint's own extent/log-scale logic rather than
    // refactored out of it, so the existing, already-visually-verified
    // paint path is untouched by this addition.
    // (The function that stood here, `dataExtent()`, returned `extent()`.
    // The full-range binding below took its name and shadowed it, so every
    // call of it threw; the one caller, nearestPoint(), reads extent().)

    // The data plus the caller's explicit limits: the "full range". Held as a
    // binding -- rescanned only when the data, the markers or the limits
    // change -- so the pixel mapping below, which a paint pass calls once per
    // sample, costs a lookup and not a pass over every series.
    readonly property var dataExtent: root.scanExtent()
    function fullExtent() {
        var d = root.dataExtent
        return { xmin: d.xmin, xmax: d.xmax, ymin: d.ymin, ymax: d.ymax }
    }
    function scanExtent() {
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

    // What the axes show: the full range, narrowed by the view range.
    function extent() {
        var e = root.fullExtent()
        if (!isNaN(root.viewXMin)) e.xmin = root.viewXMin
        if (!isNaN(root.viewXMax)) e.xmax = root.viewXMax
        if (!isNaN(root.viewYMin)) e.ymin = root.viewYMin
        if (!isNaN(root.viewYMax)) e.ymax = root.viewYMax
        return e
    }

    // Log applies when the whole data range spans more than a factor of 20
    // above zero -- decided on the full range, so a zoom never flips it.
    function useLogScale() {
        var f = root.fullExtent()
        var v = root.extent()
        return root.logScale && f.ymin > 0 && (f.ymax / f.ymin) > 20 && v.ymin > 0
    }

    // Data <-> pixel, exactly as the paint pass maps it.
    function toPixelX(v) {
        var e = root.extent()
        var x0 = root.padLeft, x1 = root.width - root.padRight
        return x0 + (v - e.xmin) / ((e.xmax - e.xmin) || 1) * (x1 - x0)
    }
    function toPixelY(v) {
        var e = root.extent()
        var y0 = root.padTop, y1 = root.height - root.padBottom
        if (root.useLogScale()) {
            var lo = Math.log(e.ymin), hi = Math.log(e.ymax)
            return y1 - (Math.log(v) - lo) / ((hi - lo) || 1) * (y1 - y0)
        }
        return y1 - (v - e.ymin) / ((e.ymax - e.ymin) || 1) * (y1 - y0)
    }
    function toDataX(px) {
        var e = root.extent()
        var x0 = root.padLeft, x1 = root.width - root.padRight
        return e.xmin + (px - x0) / Math.max(1, x1 - x0) * (e.xmax - e.xmin)
    }
    function toDataY(py) {
        var e = root.extent()
        var y0 = root.padTop, y1 = root.height - root.padBottom
        var f = (y1 - py) / Math.max(1, y1 - y0)
        if (root.useLogScale())
            return Math.exp(Math.log(e.ymin) + f * (Math.log(e.ymax) - Math.log(e.ymin)))
        return e.ymin + f * (e.ymax - e.ymin)
    }

    // The point on the primary series nearest a plot-area pixel x, for the
    // hover readout. Null when there is nothing to find one in.
    function nearestPoint(pixelX) {
        var all = root.allSeries
        if (all.length === 0)
            return null
        var extent = root.extent()
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
        visible: root.builtInHover
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

        // Solve-to-solve continuity, presentation only.
        property real morphT: 1
        property var morphFrom: null
        property var lastSeries: null
        property string lastKey: ""
        property real markerT: 1
        property var markerFrom: null
        property var lastMarkers: null
        onMorphTChanged: requestPaint()
        onMarkerTChanged: requestPaint()
        NumberAnimation { id: morphAnim; target: plot; property: "morphT"; from: 0; to: 1
                          duration: Motion.data; easing.type: Motion.standard }
        NumberAnimation { id: markerAnim; target: plot; property: "markerT"; from: 0; to: 1
                          duration: Motion.data; easing.type: Motion.standard }

        // Ease only between compatible curves: the same quantity, the same
        // number of series, the same x grid point for point. Anything else
        // (a new quantity, a shock station inserted into the grid, a
        // different range) replaces immediately.
        function compatible(a, b) {
            if (!a || !b || a.length !== b.length || a.length === 0)
                return false
            for (var s = 0; s < a.length; ++s) {
                var pa = a[s].points, pb = b[s].points
                if (!pa || !pb || pa.length !== pb.length)
                    return false
                for (var k = 0; k < pa.length; ++k)
                    if (pa[k].x !== pb[k].x || !isFinite(pa[k].y) || !isFinite(pb[k].y))
                        return false
            }
            return true
        }
        function seriesArrived() {
            var now = root.allSeries
            if (Motion.animated && root.dataKey !== "" && root.dataKey === plot.lastKey
                    && plot.compatible(plot.lastSeries, now)) {
                var from = []
                for (var s = 0; s < plot.lastSeries.length; ++s)
                    from.push(plot.lastSeries[s].points)
                plot.morphFrom = from
                morphAnim.restart()
            } else {
                morphAnim.stop()
                plot.morphT = 1
                plot.morphFrom = null
            }
            plot.lastSeries = now
            plot.lastKey = root.dataKey
        }
        function markersArrived() {
            var now = root.markers || []
            var before = plot.lastMarkers
            var same = !!before && before.length === now.length && now.length > 0
            for (var m = 0; same && m < now.length; ++m)
                same = (before[m].label || "") === (now[m].label || "")
            if (Motion.animated && same) {
                plot.markerFrom = before
                markerAnim.restart()
            } else {
                markerAnim.stop()
                plot.markerT = 1
                plot.markerFrom = null
            }
            plot.lastMarkers = now.map(function (m) { return { x: m.x, y: m.y, label: m.label } })
        }

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

            // Extents of the supplied points, narrowed by the view range. No
            // physics: this is the range of numbers handed to the canvas.
            var e = root.extent()
            var xmin = e.xmin, xmax = e.xmax, ymin = e.ymin, ymax = e.ymax

            var useLog = root.useLogScale()
            root.logScaleActive = useLog

            // The previous curve, eased towards the new one: drawn, never read.
            var morphing = plot.morphT < 1 && plot.morphFrom !== null
                           && plot.morphFrom.length === all.length
            function drawnPoints(si) {
                var pts = all[si].points
                if (!morphing)
                    return pts
                var from = plot.morphFrom[si]
                var out = []
                for (var k = 0; k < pts.length; ++k)
                    out.push({ x: pts[k].x, y: from[k].y + (pts[k].y - from[k].y) * plot.morphT })
                return out
            }
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

            // Does any curve pass through this pixel box? Labels use it to
            // find clear space instead of being drawn under the data.
            function segmentHits(box) {
                for (var si = 0; si < all.length; ++si) {
                    var pts = all[si].points
                    for (var pi = 1; pts && pi < pts.length; ++pi) {
                        var ax = tx(pts[pi - 1].x), ay = ty(pts[pi - 1].y)
                        var bx = tx(pts[pi].x), by = ty(pts[pi].y)
                        var lo = Math.max(Math.min(ax, bx), box.x0)
                        var hi = Math.min(Math.max(ax, bx), box.x1)
                        if (lo > hi || !isFinite(ay) || !isFinite(by))
                            continue
                        // A straight segment's y over [lo, hi] spans the
                        // values at its two ends.
                        var span = bx - ax
                        var ya = span === 0 ? ay : ay + (by - ay) * (lo - ax) / span
                        var yb = span === 0 ? by : ay + (by - ay) * (hi - ax) / span
                        if (Math.max(ya, yb) >= box.y0 && Math.min(ya, yb) <= box.y1)
                            return true
                    }
                }
                return false
            }

            // Plot area background
            ctx.fillStyle = Theme.surfaceSubtle
            ctx.fillRect(x0, y0, x1 - x0, y1 - y0)

            // Flow regime background shading when M=1 falls within range
            if (root.markerRegions && !isNaN(root.markerX) && xmin < root.markerX && xmax > root.markerX) {
                var smx = tx(root.markerX)
                // Subsonic zone tint
                ctx.fillStyle = "rgba(56, 139, 253, 0.035)"
                ctx.fillRect(x0, y0, smx - x0, y1 - y0)
                // Supersonic zone tint
                ctx.fillStyle = "rgba(240, 136, 62, 0.035)"
                ctx.fillRect(smx, y0, x1 - smx, y1 - y0)

                // Zone labels. Each goes where no curve passes -- the top of
                // its zone, else the bottom -- and is left out rather than
                // drawn under a curve: a label the data runs through is noise.
                var zoneSize = 9
                var markerBox = null
                if (root.markerLabel !== "") {
                    var mlx = smx + 4
                    markerBox = { x0: mlx - 2,
                                  x1: mlx + root.measureNotation(ctx, root.markerLabel,
                                                                 Typography.chartAnnotation,
                                                                 Typography.sans) + 2,
                                  y0: y0, y1: y0 + 16 }
                }
                function overlaps(a, b) {
                    return b !== null && a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1
                }
                function placeZoneLabel(label, left, right, alignLeft) {
                    var w = root.measureNotation(ctx, label, zoneSize, Typography.sans)
                    if (w + 20 > right - left)
                        return
                    var lx = alignLeft ? left + 10 : right - 10 - w
                    var baselines = [y0 + 14, y1 - 8]
                    for (var bi = 0; bi < baselines.length; ++bi) {
                        var box = { x0: lx - 4, x1: lx + w + 4,
                                    y0: baselines[bi] - zoneSize - 3, y1: baselines[bi] + 4 }
                        if (segmentHits(box) || overlaps(box, markerBox))
                            continue
                        ctx.fillStyle = Theme.textMuted
                        root.drawNotation(ctx, label, lx, baselines[bi], "left",
                                          zoneSize, Typography.sans)
                        return
                    }
                }
                placeZoneLabel("SUBSONIC (<i>M</i> &lt; 1)", x0, smx, true)
                placeZoneLabel("SUPERSONIC (<i>M</i> &gt; 1)", smx, x1, false)
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
                root.drawNotation(ctx, root.markerLabel, tx(root.markerX) + 4, y0 + 11,
                                  "left", Typography.chartAnnotation, Typography.sans)
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
                            // The right end, else the left end if a curve runs
                            // through the right. A guide label carries a value,
                            // so it is kept even when neither end is clear.
                            var gw = root.measureNotation(ctx, guide.label,
                                                          Typography.chartAnnotation,
                                                          Typography.sans)
                            var gbox = { x0: x1 - 8 - gw, x1: x1 - 2,
                                         y0: placedY - 6, y1: placedY + 8 }
                            var onLeft = segmentHits(gbox)
                                         && !segmentHits({ x0: x0 + 2, x1: x0 + 8 + gw,
                                                           y0: gbox.y0, y1: gbox.y1 })
                            root.drawNotation(ctx, guide.label,
                                              onLeft ? x0 + 6 : x1 - 4, placedY + 4,
                                              onLeft ? "left" : "right",
                                              Typography.chartAnnotation, Typography.sans)
                        }
                    } else {
                        root.drawNotation(ctx, guide.label, at, y0 + 11,
                                          "center", Typography.chartAnnotation, Typography.sans)
                    }
                }
            }

            // Everything drawn from data stays inside the plot rectangle, so a
            // zoomed view never paints a curve across the axes.
            ctx.save()
            ctx.beginPath()
            ctx.rect(x0, y0, x1 - x0, y1 - y0)
            ctx.clip()

            // the curves
            for (var si = 0; si < all.length; ++si) {
                var line = { points: drawnPoints(si), color: all[si].color,
                             dashed: all[si].dashed, width: all[si].width }
                if (line.points.length > 1 && !line.dashed) {
                    // Soft gradient fill under curve
                    ctx.save()
                    ctx.beginPath()
                    ctx.moveTo(tx(line.points[0].x), y1)
                    for (var gpi = 0; gpi < line.points.length; ++gpi) {
                        ctx.lineTo(tx(line.points[gpi].x), ty(line.points[gpi].y))
                    }
                    ctx.lineTo(tx(line.points[line.points.length - 1].x), y1)
                    ctx.closePath()
                    var grad = ctx.createLinearGradient(0, y0, 0, y1)
                    grad.addColorStop(0, Qt.rgba(line.color.r, line.color.g, line.color.b, 0.14))
                    grad.addColorStop(1, Qt.rgba(line.color.r, line.color.g, line.color.b, 0.0))
                    ctx.fillStyle = grad
                    ctx.fill()
                    ctx.restore()
                }

                ctx.strokeStyle = line.color
                ctx.lineWidth = Math.max(line.width, 2.0)
                ctx.lineJoin = "round"
                ctx.lineCap = "round"
                if (line.dashed) ctx.setLineDash([6, 4])
                ctx.beginPath()
                ctx.moveTo(tx(line.points[0].x), ty(line.points[0].y))
                for (var pi = 1; pi < line.points.length; ++pi)
                    ctx.lineTo(tx(line.points[pi].x), ty(line.points[pi].y))
                ctx.stroke()
                ctx.setLineDash([])
            }

            // Crisp plot frame border
            ctx.restore()
            ctx.save()
            ctx.beginPath()
            ctx.rect(x0, y0, x1 - x0, y1 - y0)
            ctx.clip()
            ctx.strokeStyle = Theme.border
            ctx.lineWidth = 1
            ctx.strokeRect(x0, y0, x1 - x0, y1 - y0)

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

            // the solved operating point -- between two solves it travels
            // from the previous point to the new one, in pixels: continuity
            // for the eye, not a trajectory
            for (var mi = 0; root.markers && mi < root.markers.length; ++mi) {
                var mk = root.markers[mi]
                if (isNaN(mk.x) || isNaN(mk.y))
                    continue
                var mx = tx(mk.x), my = ty(mk.y)
                var prev = plot.markerFrom !== null && plot.markerFrom.length === root.markers.length
                           ? plot.markerFrom[mi] : null
                if (prev !== null && plot.markerT < 1 && !isNaN(prev.x) && !isNaN(prev.y)) {
                    var pxp = tx(prev.x), pyp = ty(prev.y)
                    if (isFinite(pxp) && isFinite(pyp)) {
                        mx = pxp + (mx - pxp) * plot.markerT
                        my = pyp + (my - pyp) * plot.markerT
                    }
                }
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
                    // To the right of a rising curve the clear side is below
                    // it, to the left it is above; the reverse for a falling
                    // one. With no slope given the label sits above, as ever.
                    var below = mk.slope !== undefined
                                && ((mk.slope > 0) !== flip)
                    var markerY = below ? my + 16 : my - 6
                    if (flip) {
                        var claimed = claimBand(below ? my + 10 : my - 6, 12, y0 + 2, y1 - 2)
                        if (isNaN(claimed))
                            continue
                        markerY = claimed + 4
                    }
                    root.drawNotation(ctx, mk.label, mx + (flip ? -8 : 8), markerY,
                                      flip ? "right" : "left", Typography.chartAnnotation, Typography.sans)
                }
            }

            ctx.restore()

            // The axis titles name the whole axis and carry its unit, so
            // they sit one step above the in-plot annotations.
            ctx.font = Typography.axisTitle + 'px "' + Typography.sans + '"'
            ctx.fillStyle = Theme.textMuted
            root.drawNotation(ctx, root.xLabel, (x0 + x1) / 2, height - 8, "center",
                              Typography.axisTitle, Typography.sans)
            if (root.yLabel) {
                ctx.save()
                ctx.translate(14, (y0 + y1) / 2)
                ctx.rotate(-Math.PI / 2)
                root.drawNotation(ctx, root.yLabel, 0, 0, "center",
                                  Typography.axisTitle, Typography.sans)
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
            if (!root.builtInHover || !root.hoverActive || root.hoverPoint === null)
                return

            var x0 = root.padLeft, x1 = width - root.padRight
            var y0 = root.padTop, y1 = height - root.padBottom
            var px = root.toPixelX(root.hoverPoint.x)
            var py = root.toPixelY(root.hoverPoint.y)

            // Crosshair lines
            ctx.strokeStyle = Theme.borderStrong
            ctx.lineWidth = 1
            ctx.setLineDash([3, 3])
            ctx.beginPath()
            ctx.moveTo(px, y0); ctx.lineTo(px, y1)
            ctx.moveTo(x0, py); ctx.lineTo(x1, py)
            ctx.stroke()
            ctx.setLineDash([])

            // Target marker on curve
            ctx.beginPath()
            ctx.arc(px, py, 6, 0, 2 * Math.PI)
            ctx.fillStyle = Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
            ctx.fill()
            ctx.beginPath()
            ctx.arc(px, py, 3.5, 0, 2 * Math.PI)
            ctx.fillStyle = Theme.accent
            ctx.fill()
            ctx.strokeStyle = "#FFFFFF"
            ctx.lineWidth = 1.2
            ctx.stroke()

            // Fixed in the plot's own top-right corner rather than
            // following the cursor: a box that tracks the mouse can drift
            // over a guide line's own label (found by hovering directly on
            // the M=1 choking guide and opening the capture -- the two
            // overlapped exactly there, which is also the single most
            // likely place to hover). A fixed corner never competes with
            // cursor-adjacent, data-driven annotations.
            var text = root.xLabel + " " + root.hoverPoint.x.toPrecision(4)
                     + (root.yLabel ? "   " + root.yLabel + " " + root.hoverPoint.y.toPrecision(4) : "")
            // Measured with the same runs it is drawn with, so the box fits.
            var textW = root.measureNotation(ctx, text, Typography.axisTick, Typography.mono)
            var boxW = textW + 12, boxH = 18
            var boxX = x1 - boxW
            var boxY = y0 + 4

            ctx.fillStyle = Theme.surfaceElevated
            ctx.strokeStyle = Theme.borderStrong
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.rect(boxX, boxY, boxW, boxH)
            ctx.fill(); ctx.stroke()

            ctx.fillStyle = Theme.text
            ctx.textBaseline = "middle"
            root.drawNotation(ctx, text, boxX + boxW / 2, boxY + boxH / 2 + 1, "center",
                              Typography.axisTick, Typography.mono)
        }
    }

    function repaint() { plot.requestPaint() }
}
