import QtQuick
import RocketForge 1.0
import "../theme"

/*
 * RFPlotInteraction — the analysis layer over an RFLineChart.
 *
 * View -> inspect -> focus -> pin -> compare. Everything here is view state
 * over data the chart already holds: zooming, panning and the analysis lens
 * move the chart's view range; probes and the selection read real samples of
 * the supplied series and never interpolate a value into existence. Nothing
 * here solves, and no animated frame is ever read back as data.
 *
 *   wheel            zoom about the cursor (log axes zoom in log space)
 *   middle drag      pan              (or left drag with the Pan tool)
 *   Shift + drag     select a region  (or left drag with the ROI tool); on
 *                    release the region becomes the analysis lens
 *   click            select the nearest sample   (Probe tool: pin a probe)
 *   double-click     back to the full range
 *   Esc              leave the lens, else clear probes and selection
 *
 * The lens: the selected range eases in over Motion.focus and becomes the
 * plot; a breadcrumb names the range ("Full range > M 1.600 - 2.400") and an
 * overview inset keeps the whole curve in view with the lens drawn on it, so
 * the axis context is never lost. Data inside stays sharp and full contrast.
 */
Item {
    // The root id is not `layer`: inside a component (a Loader's) that name
    // resolves to an Item's own `layer` property before it reaches an id.
    id: plotLayer

    required property Item chart
    property string tool: "select"          // select | pan | roi | probe
    property int maxProbes: 3
    property var probes: []                  // [{x, y, series, label, unit, quantity}]
    property real selectionX: NaN            // linked selection (engineering x)
    property string selectionLabel: ""
    property string xSymbol: "x"             // short symbol for the breadcrumb
    property string quantity: ""             // quantity key, for probe deltas
    property string unit: ""
    property var seriesLabels: []            // label per series, for readouts

    readonly property bool lensActive: plotLayer.lens !== null
    property var lens: null                  // {x0, x1, y0, y1} in data units

    signal pointSelected(real x, real y, int seriesIndex, string label)
    signal selectionCleared()
    signal lensEntered(real x0, real x1, real y0, real y1)
    signal lensExited()

    anchors.fill: parent

    // ---- the view range ----------------------------------------------------
    // Held here and pushed to the chart. Animated only when a lens is entered
    // or left, so the reader sees where the new range came from; wheel and
    // drag are immediate. NaN means the chart's own full range.
    property real vx0: NaN
    property real vx1: NaN
    property real vy0: NaN
    property real vy1: NaN
    property bool easing: false
    Binding { target: plotLayer.chart; property: "viewXMin"; value: plotLayer.vx0 }
    Binding { target: plotLayer.chart; property: "viewXMax"; value: plotLayer.vx1 }
    Binding { target: plotLayer.chart; property: "viewYMin"; value: plotLayer.vy0 }
    Binding { target: plotLayer.chart; property: "viewYMax"; value: plotLayer.vy1 }
    Behavior on vx0 { enabled: plotLayer.easing; NumberAnimation { duration: Motion.focus; easing.type: Motion.standard } }
    Behavior on vx1 { enabled: plotLayer.easing; NumberAnimation { duration: Motion.focus; easing.type: Motion.standard } }
    Behavior on vy0 { enabled: plotLayer.easing; NumberAnimation { duration: Motion.focus; easing.type: Motion.standard } }
    Behavior on vy1 { enabled: plotLayer.easing; NumberAnimation { duration: Motion.focus; easing.type: Motion.standard } }
    Timer { id: easeEnd; interval: Motion.focus + 30; onTriggered: plotLayer.easing = false }

    function setView(x0, x1, y0, y1, animated) {
        if (animated && Motion.animated && isNaN(plotLayer.vx0)) {
            // an animation needs a numeric start: the range on screen now
            var e = plotLayer.chart.extent()
            plotLayer.easing = false
            plotLayer.vx0 = e.xmin; plotLayer.vx1 = e.xmax; plotLayer.vy0 = e.ymin; plotLayer.vy1 = e.ymax
        }
        plotLayer.easing = animated && Motion.animated
        plotLayer.vx0 = x0; plotLayer.vx1 = x1; plotLayer.vy0 = y0; plotLayer.vy1 = y1
        if (plotLayer.easing)
            easeEnd.restart()
    }

    function clearToFull() {
        plotLayer.easing = false
        plotLayer.vx0 = NaN; plotLayer.vx1 = NaN; plotLayer.vy0 = NaN; plotLayer.vy1 = NaN
    }

    function resetView(animated) {
        if (plotLayer.lens !== null) {
            plotLayer.lens = null
            plotLayer.lensExited()
        }
        if (!plotLayer.chart.zoomed)
            return
        if (animated && Motion.animated) {
            // ease to the explicit full range, then hand back to auto (NaN)
            var f = plotLayer.chart.fullExtent()
            plotLayer.setView(f.xmin, f.xmax, f.ymin, f.ymax, true)
            clearView.restart()
        } else {
            plotLayer.clearToFull()
        }
    }
    Timer {
        id: clearView
        interval: Motion.focus + 40
        onTriggered: if (plotLayer.lens === null) plotLayer.clearToFull()
    }

    function enterLens(x0, x1, y0, y1) {
        if (!(x1 > x0) || !(y1 > y0))
            return
        plotLayer.lens = { x0: x0, x1: x1, y0: y0, y1: y1 }
        plotLayer.setView(x0, x1, y0, y1, true)
        plotLayer.lensEntered(x0, x1, y0, y1)
    }

    function zoomAt(px, py, factor) {
        var e = plotLayer.chart.extent()
        var cx = plotLayer.chart.toDataX(px)
        var nx0 = cx - (cx - e.xmin) * factor
        var nx1 = cx + (e.xmax - cx) * factor
        var ny0, ny1
        if (plotLayer.chart.useLogScale()) {
            var ly = Math.log(plotLayer.chart.toDataY(py))
            ny0 = Math.exp(ly - (ly - Math.log(e.ymin)) * factor)
            ny1 = Math.exp(ly + (Math.log(e.ymax) - ly) * factor)
        } else {
            var cy = plotLayer.chart.toDataY(py)
            ny0 = cy - (cy - e.ymin) * factor
            ny1 = cy + (e.ymax - cy) * factor
        }
        plotLayer.setView(nx0, nx1, ny0, ny1, false)
    }

    function panBy(dxPx, dyPx) {
        var e = plotLayer.chart.extent()
        var w = Math.max(1, plotLayer.chart.width - plotLayer.chart.padLeft - plotLayer.chart.padRight)
        var h = Math.max(1, plotLayer.chart.height - plotLayer.chart.padTop - plotLayer.chart.padBottom)
        var dx = dxPx / w * (e.xmax - e.xmin)
        var ny0, ny1
        if (plotLayer.chart.useLogScale()) {
            var dl = dyPx / h * (Math.log(e.ymax) - Math.log(e.ymin))
            ny0 = Math.exp(Math.log(e.ymin) + dl); ny1 = Math.exp(Math.log(e.ymax) + dl)
        } else {
            var dy = dyPx / h * (e.ymax - e.ymin)
            ny0 = e.ymin + dy; ny1 = e.ymax + dy
        }
        plotLayer.setView(e.xmin - dx, e.xmax - dx, ny0, ny1, false)
    }

    // ---- reading samples -----------------------------------------------------
    // The supplied sample nearest x on each series: a value the backend
    // computed, never an interpolation.
    // A series that does not reach x (the downstream branch before the
    // shock, say) has no sample there, and none is borrowed from elsewhere.
    function samplesAt(x) {
        var out = []
        var all = plotLayer.chart.allSeries
        var f = plotLayer.chart.fullExtent()
        var tol = 0.004 * Math.abs(f.xmax - f.xmin)
        for (var s = 0; s < all.length; ++s) {
            var pts = all[s].points, best = null, bd = Infinity
            var lo = Infinity, hi = -Infinity
            for (var k = 0; k < pts.length; ++k) {
                var d = Math.abs(pts[k].x - x)
                if (d < bd) { bd = d; best = pts[k] }
                if (pts[k].x < lo) lo = pts[k].x
                if (pts[k].x > hi) hi = pts[k].x
            }
            if (x < lo - tol || x > hi + tol)
                continue
            if (best !== null)
                out.push({ series: s, x: best.x, y: best.y, color: all[s].color,
                           label: s < plotLayer.seriesLabels.length ? plotLayer.seriesLabels[s] : "" })
        }
        return out
    }

    // Nearest sample to a pixel, over every series (by pixel distance).
    function nearestSample(px, py) {
        var best = null, bd = Infinity
        var cand = plotLayer.samplesAt(plotLayer.chart.toDataX(px))
        for (var i = 0; i < cand.length; ++i) {
            var d = Math.abs(plotLayer.chart.toPixelY(cand[i].y) - py) + Math.abs(plotLayer.chart.toPixelX(cand[i].x) - px)
            if (d < bd) { bd = d; best = cand[i] }
        }
        return best
    }

    // Digits a reading deserves at this zoom: more as the range narrows,
    // never past seven significant figures (the display policy).
    function digits() {
        var e = plotLayer.chart.extent()
        var span = Math.abs(e.xmax - e.xmin)
        var d = span > 0 ? Math.ceil(-Math.log(span) / Math.LN10) + 4 : 4
        return Math.max(4, Math.min(7, d))
    }
    function fmt(v) { return isFinite(v) ? Number(v).toPrecision(plotLayer.digits()) : "—" }

    // A corner of the plot area (bottom-left, bottom-right, top-left below the
    // breadcrumb, top-right) where a w x h box covers no visible sample and no
    // segment between two samples; null when there is none.
    function freeCorner(x0, y0, x1, y1, w, h) {
        var m = 8
        var cx = [x0 + m, x1 - w - m, x0 + m, x1 - w - m]
        var cy = [y1 - h - m, y1 - h - m, y0 + 34, y0 + 34]
        var hit = [false, false, false, false]
        var all = plotLayer.chart.allSeries
        // One pass over the samples in pixel space, no allocation per sample:
        // a corner is taken when a sample lies in it or a segment between two
        // samples crosses it (an exact segment/rectangle clip test).
        function crosses(ax, ay, bx, by, l, t, r, b) {
            if (Math.max(ax, bx) < l || Math.min(ax, bx) > r || Math.max(ay, by) < t || Math.min(ay, by) > b)
                return false
            var dx = bx - ax, dy = by - ay, u0 = 0, u1 = 1
            var ps = [-dx, dx, -dy, dy], qs = [ax - l, r - ax, ay - t, b - ay]
            for (var i = 0; i < 4; ++i) {
                if (ps[i] === 0) {
                    if (qs[i] < 0)
                        return false
                } else {
                    var u = qs[i] / ps[i]
                    if (ps[i] < 0) { if (u > u1) return false; if (u > u0) u0 = u }
                    else { if (u < u0) return false; if (u < u1) u1 = u }
                }
            }
            return true
        }
        for (var s = 0; s < all.length; ++s) {
            var pts = all[s].points || []
            var px0 = NaN, py0 = NaN
            for (var k = 0; k < pts.length; ++k) {
                var px = plotLayer.chart.toPixelX(pts[k].x), py = plotLayer.chart.toPixelY(pts[k].y)
                if (isFinite(px) && isFinite(py)) {
                    for (var c = 0; c < 4; ++c) {
                        if (hit[c])
                            continue
                        var l = cx[c] - 4, tt = cy[c] - 4, r = cx[c] + w + 4, b = cy[c] + h + 4
                        if ((px >= l && px <= r && py >= tt && py <= b)
                                || (isFinite(px0) && crosses(px0, py0, px, py, l, tt, r, b)))
                            hit[c] = true
                    }
                }
                px0 = px; py0 = py
            }
            if (hit[0] && hit[1] && hit[2] && hit[3])
                return null
        }
        for (var q = 0; q < 4; ++q)
            if (!hit[q])
                return { x: cx[q], y: cy[q] }
        return null
    }

    function addProbe(sample) {
        var list = plotLayer.probes.slice()
        list.push({ x: sample.x, y: sample.y, series: sample.series, label: sample.label,
                    quantity: plotLayer.quantity, unit: plotLayer.unit })
        while (list.length > plotLayer.maxProbes)
            list.shift()
        plotLayer.probes = list
    }
    function clearProbes() { plotLayer.probes = [] }

    readonly property var probeDelta: plotLayer.probes.length >= 2
        ? AnalysisSession.probeDelta(plotLayer.probes[plotLayer.probes.length - 2],
                                     plotLayer.probes[plotLayer.probes.length - 1])
        : ({})

    // ---- pointer ---------------------------------------------------------------
    property bool hovering: false
    property point hoverAt: Qt.point(0, 0)
    property bool banding: false
    property point bandFrom: Qt.point(0, 0)
    property point bandTo: Qt.point(0, 0)

    MouseArea {
        id: pointer
        x: plotLayer.chart.padLeft
        y: plotLayer.chart.padTop
        width: Math.max(0, plotLayer.chart.width - plotLayer.chart.padLeft - plotLayer.chart.padRight)
        height: Math.max(0, plotLayer.chart.height - plotLayer.chart.padTop - plotLayer.chart.padBottom)
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        cursorShape: plotLayer.tool === "pan" ? Qt.OpenHandCursor
                   : plotLayer.tool === "roi" ? Qt.CrossCursor : Qt.ArrowCursor
        property point last
        property bool moved: false
        property int mode: 0                  // 0 none, 1 pan, 2 band

        function plotPoint(m) { return Qt.point(m.x + plotLayer.chart.padLeft, m.y + plotLayer.chart.padTop) }

        onPressed: function (m) {
            plotLayer.forceActiveFocus()
            last = Qt.point(m.x, m.y)
            moved = false
            var band = (m.button === Qt.LeftButton)
                       && (plotLayer.tool === "roi" || (m.modifiers & Qt.ShiftModifier))
            var pan = m.button === Qt.MiddleButton
                      || (m.button === Qt.LeftButton && plotLayer.tool === "pan")
            mode = band ? 2 : pan ? 1 : 0
            if (band) {
                plotLayer.banding = true
                plotLayer.bandFrom = plotPoint(m)
                plotLayer.bandTo = plotLayer.bandFrom
            }
        }
        onPositionChanged: function (m) {
            plotLayer.hovering = true
            plotLayer.hoverAt = plotPoint(m)
            if (Math.abs(m.x - last.x) + Math.abs(m.y - last.y) > 2 && pressed)
                moved = true
            if (mode === 1 && pressed) {
                plotLayer.panBy(m.x - last.x, m.y - last.y)
                last = Qt.point(m.x, m.y)
            } else if (mode === 2 && pressed) {
                plotLayer.bandTo = plotPoint(m)
            }
            overlay.requestPaint()
        }
        onExited: { plotLayer.hovering = false; overlay.requestPaint() }
        onReleased: function (m) {
            if (mode === 2) {
                plotLayer.banding = false
                var a = plotLayer.bandFrom, b = plotLayer.bandTo
                if (Math.abs(b.x - a.x) > 8 && Math.abs(b.y - a.y) > 8) {
                    var x0 = plotLayer.chart.toDataX(Math.min(a.x, b.x)), x1 = plotLayer.chart.toDataX(Math.max(a.x, b.x))
                    var y0 = plotLayer.chart.toDataY(Math.max(a.y, b.y)), y1 = plotLayer.chart.toDataY(Math.min(a.y, b.y))
                    plotLayer.enterLens(x0, x1, y0, y1)
                }
            } else if (mode === 0 && !moved && m.button === Qt.LeftButton) {
                var p = plotPoint(m)
                var s = plotLayer.nearestSample(p.x, p.y)
                if (s !== null) {
                    if (plotLayer.tool === "probe" || (m.modifiers & Qt.ControlModifier))
                        plotLayer.addProbe(s)
                    else
                        plotLayer.pointSelected(s.x, s.y, s.series, s.label)
                }
            }
            mode = 0
            overlay.requestPaint()
        }
        onDoubleClicked: plotLayer.resetView(true)
        onWheel: function (w) {
            var p = Qt.point(w.x + plotLayer.chart.padLeft, w.y + plotLayer.chart.padTop)
            plotLayer.zoomAt(p.x, p.y, w.angleDelta.y > 0 ? 0.85 : 1.0 / 0.85)
            overlay.requestPaint()
        }
    }

    Keys.onPressed: function (event) {
        if (event.key === Qt.Key_Escape) {
            if (plotLayer.lensActive || plotLayer.chart.zoomed)
                plotLayer.resetView(true)
            else {
                plotLayer.clearProbes()
                plotLayer.selectionCleared()
            }
            event.accepted = true
        }
    }

    // ---- the overlay ---------------------------------------------------------
    // Crosshair and multi-series readout, the region being selected, probes,
    // the linked selection and the overview inset. Its own Canvas, repainted
    // on pointer moves; the chart's grid and curves are never repainted for a
    // hover.
    Connections {
        target: chart
        function onViewXMinChanged() { overlay.requestPaint() }
        function onViewYMinChanged() { overlay.requestPaint() }
        function onWidthChanged() { overlay.requestPaint() }
        function onHeightChanged() { overlay.requestPaint() }
        function onSeriesChanged() { overlay.requestPaint() }
        function onPointsChanged() { overlay.requestPaint() }
    }
    Connections { target: Theme; function onModeChanged() { overlay.requestPaint() } }
    onProbesChanged: overlay.requestPaint()
    onSelectionXChanged: overlay.requestPaint()
    onLensChanged: overlay.requestPaint()

    Canvas {
        id: overlay
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)
            var x0 = plotLayer.chart.padLeft, x1 = width - plotLayer.chart.padRight
            var y0 = plotLayer.chart.padTop, y1 = height - plotLayer.chart.padBottom
            if (x1 <= x0 || y1 <= y0)
                return
            ctx.save()
            ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip()

            // the region being selected: everything outside it recedes
            if (plotLayer.banding) {
                var ax = Math.min(plotLayer.bandFrom.x, plotLayer.bandTo.x), bx = Math.max(plotLayer.bandFrom.x, plotLayer.bandTo.x)
                var ay = Math.min(plotLayer.bandFrom.y, plotLayer.bandTo.y), by = Math.max(plotLayer.bandFrom.y, plotLayer.bandTo.y)
                ctx.fillStyle = Qt.rgba(Theme.background.r, Theme.background.g, Theme.background.b, 0.55)
                ctx.fillRect(x0, y0, x1 - x0, ay - y0)
                ctx.fillRect(x0, by, x1 - x0, y1 - by)
                ctx.fillRect(x0, ay, ax - x0, by - ay)
                ctx.fillRect(bx, ay, x1 - bx, by - ay)
                ctx.strokeStyle = Theme.accent
                ctx.lineWidth = 1
                ctx.strokeRect(ax + 0.5, ay + 0.5, bx - ax, by - ay)
            }

            // the linked selection: an accent crosshair at the selected x and
            // a ring on every series at its real sample there
            if (!isNaN(plotLayer.selectionX)) {
                var sx = plotLayer.chart.toPixelX(plotLayer.selectionX)
                if (sx >= x0 && sx <= x1) {
                    ctx.strokeStyle = Theme.accent
                    ctx.lineWidth = 1.5
                    ctx.beginPath(); ctx.moveTo(sx, y0); ctx.lineTo(sx, y1); ctx.stroke()
                    var sel = plotLayer.samplesAt(plotLayer.selectionX)
                    for (var q = 0; q < sel.length; ++q) {
                        var sy = plotLayer.chart.toPixelY(sel[q].y)
                        ctx.beginPath(); ctx.arc(plotLayer.chart.toPixelX(sel[q].x), sy, 5, 0, 2 * Math.PI)
                        ctx.fillStyle = Theme.surface; ctx.fill()
                        ctx.lineWidth = 2; ctx.strokeStyle = Theme.accent; ctx.stroke()
                    }
                    if (plotLayer.selectionLabel !== "") {
                        ctx.fillStyle = Theme.accent
                        ctx.font = Typography.chartAnnotation + 'px "' + Typography.sans + '"'
                        ctx.textAlign = sx > x1 - 120 ? "right" : "left"
                        plotLayer.chart.drawNotation(ctx, plotLayer.selectionLabel, sx + (sx > x1 - 120 ? -6 : 6),
                                           y0 + 26, sx > x1 - 120 ? "right" : "left",
                                           Typography.chartAnnotation, Typography.sans)
                    }
                }
            }

            // pinned probes
            for (var p = 0; p < plotLayer.probes.length; ++p) {
                var pr = plotLayer.probes[p]
                var ppx = plotLayer.chart.toPixelX(pr.x), ppy = plotLayer.chart.toPixelY(pr.y)
                ctx.fillStyle = Theme.text
                ctx.beginPath(); ctx.moveTo(ppx, ppy - 6); ctx.lineTo(ppx + 5, ppy); ctx.lineTo(ppx, ppy + 6)
                ctx.lineTo(ppx - 5, ppy); ctx.closePath(); ctx.fill()
                ctx.font = Typography.chartAnnotation + 'px "' + Typography.sans + '"'
                ctx.textAlign = "left"
                ctx.fillText("P" + (p + 1), ppx + 8, ppy - 8)
            }

            // hover: crosshair and every series' sample at this x
            if (plotLayer.hovering && !plotLayer.banding) {
                var hx = plotLayer.hoverAt.x
                if (hx >= x0 && hx <= x1) {
                    var samples = plotLayer.samplesAt(plotLayer.chart.toDataX(hx))
                    if (samples.length > 0) {
                        var cx = plotLayer.chart.toPixelX(samples[0].x)
                        ctx.strokeStyle = Theme.borderStrong
                        ctx.lineWidth = 1
                        ctx.setLineDash([3, 3])
                        ctx.beginPath(); ctx.moveTo(cx, y0); ctx.lineTo(cx, y1); ctx.stroke()
                        ctx.setLineDash([])
                        for (var h = 0; h < samples.length; ++h) {
                            var hy = plotLayer.chart.toPixelY(samples[h].y)
                            ctx.beginPath(); ctx.arc(plotLayer.chart.toPixelX(samples[h].x), hy, 3.5, 0, 2 * Math.PI)
                            ctx.fillStyle = samples[h].color; ctx.fill()
                        }
                        // readout, in the plot's top-right corner
                        var lines = [plotLayer.chart.xLabel + " " + plotLayer.fmt(samples[0].x)]
                        for (var r = 0; r < samples.length; ++r)
                            lines.push((samples[r].label || plotLayer.chart.yLabel) + " " + plotLayer.fmt(samples[r].y))
                        ctx.font = Typography.axisTick + 'px "' + Typography.mono + '"'
                        var bw = 0
                        for (var l = 0; l < lines.length; ++l)
                            bw = Math.max(bw, plotLayer.chart.measureNotation(ctx, lines[l], Typography.axisTick, Typography.mono))
                        bw += 14
                        var bh = 6 + 16 * lines.length
                        var bxp = x1 - bw - 4, byp = y0 + 4
                        ctx.fillStyle = Theme.surfaceElevated
                        ctx.strokeStyle = Theme.borderStrong
                        ctx.fillRect(bxp, byp, bw, bh); ctx.strokeRect(bxp + 0.5, byp + 0.5, bw, bh)
                        for (var li = 0; li < lines.length; ++li) {
                            ctx.fillStyle = li === 0 ? Theme.textSecondary
                                          : samples[li - 1].color
                            plotLayer.chart.drawNotation(ctx, lines[li], bxp + 7, byp + 16 + 16 * li, "left",
                                               Typography.axisTick, Typography.mono)
                        }
                    }
                }
            }
            ctx.restore()

            // the overview: the whole curve, with the lens (or zoom) drawn on it.
            // It takes the first corner where it covers no visible data --
            // never on top of the curve being analysed -- and when every
            // corner holds data it is not drawn: the breadcrumb still names
            // the range.
            var ow = Math.min(180, (x1 - x0) * 0.3), oh = 64
            var corner = plotLayer.chart.zoomed ? plotLayer.freeCorner(x0, y0, x1, y1, ow, oh) : null
            if (corner !== null) {
                var ox = corner.x, oy = corner.y
                var f = plotLayer.chart.fullExtent(), all = plotLayer.chart.allSeries
                ctx.fillStyle = Theme.plotBackground
                ctx.strokeStyle = Theme.borderStrong
                ctx.fillRect(ox, oy, ow, oh); ctx.strokeRect(ox + 0.5, oy + 0.5, ow, oh)
                var logF = plotLayer.chart.logScale && f.ymin > 0 && f.ymax / f.ymin > 20
                function mx(v) { return ox + 4 + (v - f.xmin) / ((f.xmax - f.xmin) || 1) * (ow - 8) }
                function my(v) {
                    if (logF)
                        return oy + oh - 4 - (Math.log(v) - Math.log(f.ymin)) / ((Math.log(f.ymax) - Math.log(f.ymin)) || 1) * (oh - 8)
                    return oy + oh - 4 - (v - f.ymin) / ((f.ymax - f.ymin) || 1) * (oh - 8)
                }
                for (var si = 0; si < all.length; ++si) {
                    var pts = all[si].points
                    ctx.strokeStyle = Theme.textMuted
                    ctx.lineWidth = 1
                    ctx.beginPath()
                    for (var k = 0; k < pts.length; ++k) {
                        if (k === 0) ctx.moveTo(mx(pts[k].x), my(pts[k].y))
                        else ctx.lineTo(mx(pts[k].x), my(pts[k].y))
                    }
                    ctx.stroke()
                }
                var v = plotLayer.chart.extent()
                var rx0 = Math.max(ox, mx(v.xmin)), rx1 = Math.min(ox + ow, mx(v.xmax))
                var ry0 = Math.max(oy, my(v.ymax)), ry1 = Math.min(oy + oh, my(v.ymin))
                ctx.strokeStyle = Theme.accent
                ctx.lineWidth = 1.5
                ctx.strokeRect(rx0, ry0, Math.max(2, rx1 - rx0), Math.max(2, ry1 - ry0))
            }
        }
    }

    // ---- the breadcrumb ---------------------------------------------------
    // Built only while the chart is zoomed; the full-range view has no
    // breadcrumb to show.
    Loader {
        x: plotLayer.chart.padLeft + 8
        y: plotLayer.chart.padTop + 6
        active: plotLayer.chart.zoomed
        sourceComponent: Row {
            id: crumb
            objectName: "lensBreadcrumb"
            spacing: 6

            Text {
                text: "Full range"
                color: crumbMouse.containsMouse ? Theme.accent : Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                font.underline: crumbMouse.containsMouse
                MouseArea { id: crumbMouse; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor; onClicked: plotLayer.resetView(true) }
            }
            Text { text: "›"; color: Theme.textMuted; font.pixelSize: Typography.meta }
            Text {
                readonly property var e: { plotLayer.chart.viewXMin; plotLayer.chart.viewXMax; return plotLayer.chart.extent() }
                text: Notation.rich(plotLayer.xSymbol + " " + plotLayer.fmt(e.xmin) + " – " + plotLayer.fmt(e.xmax)
                                    + (plotLayer.lensActive ? "   (lens)" : ""))
                textFormat: Text.RichText
                color: Theme.accent
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
