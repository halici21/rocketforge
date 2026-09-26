import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The primary Trade Study grammar: one swept design variable plotted
 * against one or more response curves. Answers "how does the system
 * respond as this design variable changes" directly, rather than routing
 * every study through a 2D scatter/Pareto projection meant for a
 * genuinely multidimensional design space (that case is StudyPareto.qml).
 *
 * Each response metric gets its own aligned RFLineChart rather than a
 * shared Y axis or an invented dual-axis mechanism: response metrics
 * commonly differ by orders of magnitude (specific impulse in seconds,
 * density impulse in very different units), and forcing them onto one
 * axis would flatten one curve or misrepresent scale. Every chart shares
 * the same X domain (the swept variable's own evaluated range) so they
 * stay visually aligned -- reading down a vertical line at one X value
 * reads the same design across every curve.
 *
 * Each marker is one evaluated design, not a point on a continuous
 * function -- RFLineChart's own showPoints dots every sample for exactly
 * this reason, matching StudyPareto.qml's own discipline for the same
 * underlying data.
 */
Item {
    id: view

    readonly property var allSeries: TradeStudy.sweepSeries
    readonly property var options: TradeStudy.responseMetricOptions
    readonly property var activeMetrics: TradeStudy.sweepMetrics
    readonly property int selectedIndex: TradeStudy.selectedIndices.length > 0
        ? TradeStudy.selectedIndices[TradeStudy.selectedIndices.length - 1] : -1

    readonly property var xBounds: {
        var lo = Number.POSITIVE_INFINITY
        var hi = Number.NEGATIVE_INFINITY
        for (var s = 0; s < view.allSeries.length; ++s) {
            var points = view.allSeries[s].points
            for (var i = 0; i < points.length; ++i) {
                if (points[i].x < lo) lo = points[i].x
                if (points[i].x > hi) hi = points[i].x
            }
        }
        if (lo > hi) return { lo: 0, hi: 1 }
        if (lo === hi) return { lo: lo - 1, hi: hi + 1 }
        var pad = (hi - lo) * 0.04
        return { lo: lo - pad, hi: hi + pad }
    }

    // A gap in the data (a metric a point could not produce) must show as
    // a break in the line, never a bridge across the missing value -- the
    // same honesty rule the results table already applies to a failed
    // row. RFLineChart draws one continuous polyline per series entry, so
    // a series with a gap is split into contiguous valid runs here, all
    // sharing one colour/label so it still reads as one curve.
    function segmentsFor(points) {
        var segments = []
        var current = []
        for (var i = 0; i < points.length; ++i) {
            if (points[i].hasValue) {
                current.push(points[i])
            } else if (current.length > 0) {
                segments.push(current)
                current = []
            }
        }
        if (current.length > 0)
            segments.push(current)
        return segments
    }

    function pointInSeries(series, index) {
        for (var i = 0; i < series.points.length; ++i) {
            if (series.points[i].index === index && series.points[i].hasValue)
                return series.points[i]
        }
        return null
    }

    // Mirrors RFLineChart's own internal pixel<->data mapping (padLeft/
    // padRight, linear in x) so a tap here finds the same point a hover
    // over the same pixel would -- kept here rather than reading it back
    // out of RFLineChart, which does not expose write access to another
    // series' worth of points for a nearest-point search across a
    // segmented (gap-broken) curve.
    // Small-multiple peek/focus (the shared RFPlotPeek contract): which
    // response curve is peeking, and the curve opened in focus.
    QtObject { id: peekGroup; property Item current: null }

    function nearestByX(series, dataX) {
        var best = null, bestDist = Infinity
        for (var i = 0; i < series.points.length; ++i) {
            if (!series.points[i].hasValue) continue
            var dist = Math.abs(series.points[i].x - dataX)
            if (dist < bestDist) { bestDist = dist; best = series.points[i] }
        }
        return best
    }

    function nearestInSeries(series, chart, pixelX) {
        var x0 = chart.padLeft, x1 = chart.width - chart.padRight
        var dataX = view.xBounds.lo + (pixelX - x0) / Math.max(1, x1 - x0)
                    * (view.xBounds.hi - view.xBounds.lo)
        var best = null, bestDist = Infinity
        for (var i = 0; i < series.points.length; ++i) {
            if (!series.points[i].hasValue) continue
            var dist = Math.abs(series.points[i].x - dataX)
            if (dist < bestDist) { bestDist = dist; best = series.points[i] }
        }
        return best
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: !TradeStudy.hasResult
            tag: "NO STUDY"
            title: "No study has been run"
            body: "Sweep exactly one design variable on the Setup tab and "
                  + "run the study to see how the system responds as it "
                  + "changes."
        }

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: TradeStudy.hasResult && !TradeStudy.isParametricSweep
            tag: "NOT A SINGLE SWEEP"
            title: "More than one design variable varies in this study"
            body: "This view answers \"how does the system respond as one "
                  + "variable changes.\" With more than one varying, use "
                  + "Design space instead, or fix all but one variable on "
                  + "the Setup tab."
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.isParametricSweep
            spacing: Metrics.spacing.m

            Text {
                text: TradeStudy.sweepVariableTitle
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
            Item { Layout.fillWidth: true }
            RFToggle {
                text: "Normalized"
                checked: TradeStudy.sweepScaledToPeak
                onToggled: TradeStudy.sweepScaledToPeak = checked
            }
        }

        Flow {
            Layout.fillWidth: true
            visible: TradeStudy.isParametricSweep
            spacing: Metrics.spacing.s

            Repeater {
                model: view.options

                delegate: RFToggle {
                    required property var modelData
                    text: modelData.label
                    checked: view.activeMetrics.indexOf(modelData.key) !== -1
                    onToggled: TradeStudy.setSweepMetricEnabled(modelData.key, checked)
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: TradeStudy.sweepScalingNote !== ""
            text: TradeStudy.sweepScalingNote
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: TradeStudy.isParametricSweep && view.allSeries.length === 0
            tag: "NO RESPONSE CHOSEN"
            title: "No response metric selected"
            body: "Choose at least one response metric above to plot it "
                  + "against " + TradeStudy.sweepVariableTitle + "."
        }

        // Analysis Experience R2, section 26/42: the chart IS the analysis
        // surface here, not a 200px card stacked under the controls. Each
        // response curve takes an equal share of the real workspace height
        // instead of a fixed 200px, so a single-metric sweep fills the
        // view and three metrics still each get a readable plot. The
        // Flickable stays for the case where enough metrics are enabled
        // that equal shares would fall below a legible floor.
        Flickable {
            id: chartScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: TradeStudy.isParametricSweep && view.allSeries.length > 0
            contentWidth: width
            contentHeight: Math.max(height, charts.implicitHeight)
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: RFScrollBar {}

            readonly property real perChartHeight: {
                var n = Math.max(1, view.allSeries.length)
                var gaps = Metrics.spacing.m * (n - 1)
                return Math.max(220, (height - gaps) / n)
            }

            ColumnLayout {
                id: charts
                width: parent.width
                spacing: Metrics.spacing.m

                Repeater {
                    model: view.allSeries

                    // The slot in the column (it never changes size) and, in
                    // it, the curve's panel -- the item a peek lifts.
                    delegate: Item {
                        id: curveCell
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: chartScroll.perChartHeight

                        opacity: curvePeek.receded ? 0.45 : 1
                        Behavior on opacity { NumberAnimation { duration: Motion.fast } }

                    RFPanel {
                        id: chartPanel
                        readonly property var modelData: curveCell.modelData
                        readonly property int index: curveCell.index
                        anchors.fill: parent
                        chromeless: true
                        title: modelData.label
                              + (TradeStudy.sweepScaledToPeak
                                 ? " (normalized)" : "")
                        contentSpacing: 0

                        readonly property var selectedPoint:
                            view.pointInSeries(modelData, view.selectedIndex)
                        readonly property color curveColor:
                            Theme.series[index % Theme.series.length]


                        RFLineChart {
                            id: chart
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            xLabel: TradeStudy.sweepVariableTitle
                            yLabel: chartPanel.modelData.unit
                            xMin: view.xBounds.lo
                            xMax: view.xBounds.hi
                            curveColor: chartPanel.curveColor
                            showPoints: true
                            logScale: false
                            series: {
                                var segments = view.segmentsFor(chartPanel.modelData.points)
                                var out = []
                                for (var i = 0; i < segments.length; ++i)
                                    out.push({ points: segments[i],
                                              color: chartPanel.curveColor })
                                return out
                            }
                            // a design-variable axis: a reference line, no Mach regions
                            markerRegions: false
                            markerX: chartPanel.selectedPoint ? chartPanel.selectedPoint.x : NaN
                            markerLabel: chartPanel.selectedPoint ? "Selected" : ""
                            markers: chartPanel.selectedPoint
                                     ? [{ x: chartPanel.selectedPoint.x,
                                          y: chartPanel.selectedPoint.y, label: "" }]
                                     : []

                            TapHandler {
                                onTapped: {
                                    var found = view.nearestInSeries(
                                        chartPanel.modelData, chart, point.position.x)
                                    if (found)
                                        TradeStudy.toggleSelection(found.index)
                                }
                            }
                        }
                    }

                        // Over the whole slot: peek (the panel lifted, taller;
                        // the column is full width, so it grows in height) and
                        // focus.
                        RFPlotPeek {
                            id: curvePeek
                            group: peekGroup
                            content: chartPanel
                            stage: view
                            area: chartScroll
                            onFocusRequested: focusOverlay.show(
                                chartPanel.title, "Same evaluated study, full size · the chosen design is the crosshair",
                                focusCurve, { series: chartPanel.modelData, color: chartPanel.curveColor })
                        }
                    }
                }
            }
        }
    }

    // ---- focus: one response curve at full size ---------------------------
    Component {
        id: focusCurve
        Item {
            readonly property var series: focusOverlay.context.series
            // kept between opens by the overlay: each open starts whole
            function reopened() {
                interact.clearProbes()
                interact.resetView(false)
            }
            onSeriesChanged: reopened()
            function handleEscape() {
                if (interact.lensActive || plot.zoomed) {
                    interact.resetView(true)
                    return true
                }
                return false
            }
            ColumnLayout {
                anchors.fill: parent
                spacing: Metrics.spacing.s
                RFPlotToolbar { interaction: interact }
                RFLineChart {
                    id: plot
                    objectName: "tradeFocusChart"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    xLabel: TradeStudy.sweepVariableTitle
                    yLabel: parent.parent.series ? parent.parent.series.unit : ""
                    xMin: view.xBounds.lo
                    xMax: view.xBounds.hi
                    showPoints: true
                    logScale: false
                    series: {
                        var s = parent.parent.series
                        if (!s) return []
                        var segments = view.segmentsFor(s.points)
                        var out = []
                        for (var i = 0; i < segments.length; ++i)
                            out.push({ points: segments[i], color: focusOverlay.context.color, width: 1.8 })
                        return out
                    }
                    RFPlotInteraction {
                        id: interact
                        chart: plot
                        readonly property var chosen: plot.parent.parent.series
                                                      ? view.pointInSeries(plot.parent.parent.series, view.selectedIndex) : null
                        selectionX: chosen ? chosen.x : NaN
                        selectionLabel: chosen ? "#" + chosen.index : ""
                        xSymbol: TradeStudy.sweepVariableTitle
                        onPointSelected: function (x, y, s, label) {
                            var found = view.nearestByX(plot.parent.parent.series, x)
                            if (found)
                                TradeStudy.toggleSelection(found.index)
                        }
                    }
                }
            }
        }
    }

    RFFocusOverlay {
        id: focusOverlay
        objectName: "tradeFocusOverlay"
        anchors.fill: parent
    }
}
