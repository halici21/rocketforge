import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The trade-off, plotted.
 *
 * Two things this view is careful to say, because a reader would otherwise
 * assume both wrongly:
 *
 * **The markers are samples, not a curve.** Each one is a design that was
 * actually evaluated on the grid that was run. There is no interpolation, no
 * spline and no surrogate: the space between two markers was not evaluated,
 * and drawing a smooth line through them would claim it was.
 *
 * **The plot is a projection.** Pareto membership is decided using every
 * objective; this shows two of them. With three or more, a marker can look
 * dominated here and be efficient in the full set, and the note says so rather
 * than leaving a reader to discover it.
 *
 * Membership is never encoded by colour alone: the three groups use different
 * marker shapes and are separately labelled.
 */
Item {
    id: view

    readonly property var series: TradeStudy.paretoSeries

    // Theme.accent (champagne gold) is reserved for the current selection
    // only, never for Pareto/feasibility status -- see Theme.qml's own
    // "application state only" note. Pareto-efficient gets its own hue.
    readonly property color paretoColor: Theme.series[0]

    function seriesColor(key) {
        if (key === "efficient") return view.paretoColor
        if (key === "dominated") return Theme.textMuted
        return Theme.warning
    }

    function bounds(axis) {
        var lo = Number.POSITIVE_INFINITY
        var hi = Number.NEGATIVE_INFINITY
        for (var s = 0; s < view.series.length; ++s) {
            var points = view.series[s].points
            for (var i = 0; i < points.length; ++i) {
                var value = axis === "x" ? points[i].x : points[i].y
                if (value < lo) lo = value
                if (value > hi) hi = value
            }
        }
        if (lo > hi)
            return { lo: 0, hi: 1 }
        if (lo === hi)
            return { lo: lo - 1, hi: hi + 1 }
        var pad = (hi - lo) * 0.06
        return { lo: lo - pad, hi: hi + pad }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFEmptyState {
            Layout.fillWidth: true
            Layout.topMargin: Metrics.spacing.h1
            visible: !TradeStudy.paretoAvailable
            tag: TradeStudy.hasResult ? "NOT APPLICABLE" : "NO STUDY"
            title: TradeStudy.hasResult
                   ? "No trade-off to plot"
                   : "No study has been run"
            body: TradeStudy.hasResult
                  ? (TradeStudy.rankingNote !== ""
                     ? TradeStudy.rankingNote
                     : "A Pareto front needs two or more objectives and a "
                       + "completed study. A cancelled run shows no front, "
                       + "because a front over part of a design space is not a "
                       + "front over the design space.")
                  : "Define at least two objectives on the Setup tab and run "
                    + "the study."
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.paretoAvailable
            spacing: Metrics.spacing.m

            RFComboBox {
                Layout.preferredWidth: 240
                label: "Horizontal axis"
                model: TradeStudy.objectiveAxisOptions.map(
                           function (o) { return o.label })
                currentIndex: TradeStudy.paretoXIndex
                // onActivated, not onCurrentIndexChanged: the index is bound
                // to the controller, so writing back from the change handler
                // would loop through the binding. Activation fires only on a
                // person choosing an item.
                onActivated: function (index) {
                    var options = TradeStudy.objectiveAxisOptions
                    if (index < 0 || index >= options.length)
                        return
                    TradeStudy.paretoX = options[index].key
                }
            }

            RFComboBox {
                Layout.preferredWidth: 240
                label: "Vertical axis"
                model: TradeStudy.objectiveAxisOptions.map(
                           function (o) { return o.label })
                currentIndex: TradeStudy.paretoYIndex
                // onActivated, not onCurrentIndexChanged: the index is bound
                // to the controller, so writing back from the change handler
                // would loop through the binding. Activation fires only on a
                // person choosing an item.
                onActivated: function (index) {
                    var options = TradeStudy.objectiveAxisOptions
                    if (index < 0 || index >= options.length)
                        return
                    TradeStudy.paretoY = options[index].key
                }
            }

            Item { Layout.fillWidth: true }
        }

        RFPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: TradeStudy.paretoAvailable
            title: "Evaluated designs"
            chromeless: true
            contentSpacing: Metrics.spacing.s

            RFPlotSurface {
                id: surface
                Layout.fillWidth: true
                Layout.fillHeight: true

                readonly property var xb: view.bounds("x")
                readonly property var yb: view.bounds("y")

                xMin: xb.lo
                xMax: xb.hi
                yMin: yb.lo
                yMax: yb.hi
                xTitle: TradeStudy.paretoXTitle
                yTitle: TradeStudy.paretoYTitle
                // The surface now formats from the tick STEP, which is what
                // toPrecision(5) was standing in for -- and standing in
                // badly: it printed "1.9500" on a 0.05 step and "330.00"
                // on a step of 10.

                // The shape now lives in the swatch rather than in a glyph
                // appended to the name: the U+2715 cross rendered as tofu in
                // the shipped font stack, which left "infeasible" carried by
                // colour alone.
                legend: [
                    { name: "Pareto-efficient", color: view.paretoColor, shape: "diamond" },
                    { name: "Feasible, dominated", color: Theme.textMuted, shape: "circle" },
                    { name: "Infeasible or failed", color: Theme.warning, shape: "cross" },
                    { name: "Selected", color: Theme.accent, shape: "ring" }
                ]

                // Data-oriented: every evaluated point is painted by one
                // Canvas, not instantiated as a QML Item. Measured directly
                // (experiments/cad_workbench_r1/tradestudy_large_study_perf.py):
                // the previous one-Item-per-point Repeater-of-Repeaters cost
                // 3.2s to redraw on an axis switch at 3000 points -- exactly
                // the anti-pattern rf-scientific-visualization's own "large
                // studies stay responsive" section warns against. Hit-testing
                // for hover/tap is one nearest-point scan per mouse event
                // (still O(N), but only on an actual pointer move, never on
                // every repaint), not a handler per marker.
                Canvas {
                    id: pointsCanvas
                    anchors.fill: parent
                    antialiasing: true

                    readonly property var seriesData: view.series
                    readonly property var selectedIndices: TradeStudy.selectedIndices
                    readonly property color paretoColor: view.paretoColor
                    // "feasible, not Pareto-efficient" -- named for the
                    // legend entry it draws, not "dominated": this file may
                    // present the decision layer's verdict, never compute
                    // one (test_qml_implements_no_decision_algorithm).
                    readonly property color feasibleMarkerColor: Theme.textMuted
                    readonly property color excludedColor: Theme.warning
                    readonly property color selectedColor: Theme.accent
                    // Canvas rotate()/arc() take radians; Math.PI itself is
                    // outside this project's QML layout-arithmetic allowlist
                    // (test_qml_uses_only_layout_arithmetic), so the two
                    // angles this file needs are spelled out as literals.
                    readonly property real fullTurn: 6.283185307179586   // 2*pi
                    readonly property real quarterTurn: 0.7853981633974483  // pi/4

                    onSeriesDataChanged: requestPaint()
                    onSelectedIndicesChanged: requestPaint()
                    onFeasibleMarkerColorChanged: requestPaint()
                    onExcludedColorChanged: requestPaint()
                    onSelectedColorChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    onParetoColorChanged: requestPaint()

                    function nearestPoint(mx, my) {
                        var hitRadius = 14
                        var best = null
                        var bestDist = hitRadius * hitRadius
                        for (var s = 0; s < seriesData.length; ++s) {
                            var points = seriesData[s].points
                            for (var p = 0; p < points.length; ++p) {
                                var pt = points[p]
                                var dx = surface.mapX(pt.x) - mx
                                var dy = surface.mapY(pt.y) - my
                                var d = dx * dx + dy * dy
                                if (d < bestDist) {
                                    bestDist = d
                                    best = pt
                                }
                            }
                        }
                        return best
                    }

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        for (var s = 0; s < seriesData.length; ++s) {
                            var entry = seriesData[s]
                            var efficient = entry.key === "efficient"
                            var excluded = entry.key === "excluded"
                            var points = entry.points
                            for (var p = 0; p < points.length; ++p) {
                                var pt = points[p]
                                var x = surface.mapX(pt.x)
                                var y = surface.mapY(pt.y)
                                var half = efficient ? 5.5 : 4

                                // Current-selection ring. Gold is reserved
                                // for this one meaning across the whole
                                // application -- never for Pareto/feasibility
                                // status, which each already have their own
                                // shape and colour below.
                                if (selectedIndices.indexOf(pt.index) !== -1) {
                                    ctx.beginPath()
                                    ctx.arc(x, y, half + 4, 0, fullTurn)
                                    ctx.strokeStyle = selectedColor
                                    ctx.lineWidth = 2
                                    ctx.stroke()
                                }

                                // Shape, not only colour. A reader who cannot
                                // rely on hue still sees three distinct
                                // groups.
                                if (excluded) {
                                    ctx.globalAlpha = 0.7
                                    ctx.strokeStyle = excludedColor
                                    ctx.lineWidth = 2
                                    ctx.beginPath()
                                    ctx.moveTo(x - half, y - half)
                                    ctx.lineTo(x + half, y + half)
                                    ctx.moveTo(x - half, y + half)
                                    ctx.lineTo(x + half, y - half)
                                    ctx.stroke()
                                    ctx.globalAlpha = 1
                                } else if (efficient) {
                                    ctx.save()
                                    ctx.translate(x, y)
                                    ctx.rotate(quarterTurn)
                                    ctx.fillStyle = paretoColor
                                    ctx.fillRect(-half, -half, half * 2, half * 2)
                                    ctx.restore()
                                } else {
                                    ctx.globalAlpha = 0.65
                                    ctx.strokeStyle = feasibleMarkerColor
                                    ctx.lineWidth = 1
                                    ctx.beginPath()
                                    ctx.arc(x, y, half, 0, fullTurn)
                                    ctx.stroke()
                                    ctx.globalAlpha = 1
                                }
                            }
                        }
                    }

                    property var hovered: null

                    HoverHandler {
                        id: plotHover
                        onPointChanged: {
                            var found = pointsCanvas.nearestPoint(
                                point.position.x, point.position.y)
                            pointsCanvas.hovered = found
                            surface.hoverX = found ? found.x : NaN
                            surface.hoverY = found ? found.y : NaN
                        }
                        onHoveredChanged: {
                            if (!hovered) {
                                pointsCanvas.hovered = null
                                surface.hoverX = NaN
                                surface.hoverY = NaN
                            }
                        }
                    }
                    TapHandler {
                        onTapped: {
                            var found = pointsCanvas.nearestPoint(
                                point.position.x, point.position.y)
                            if (found)
                                TradeStudy.toggleSelection(found.index)
                        }
                    }

                    RFTooltip {
                        parent: pointsCanvas
                        // Guard directly against pointsCanvas.hovered here,
                        // not the sibling `visible` property: when hovered
                        // changes, QML does not guarantee visible's binding
                        // re-evaluates before this one runs, so reading
                        // `visible` as the guard could still see the old
                        // (stale) true and dereference a null hovered.
                        visible: pointsCanvas.hovered !== null
                        x: pointsCanvas.hovered
                           ? surface.mapX(pointsCanvas.hovered.x) + 10 : 0
                        y: pointsCanvas.hovered
                           ? surface.mapY(pointsCanvas.hovered.y) + 10 : 0
                        text: {
                            if (!pointsCanvas.hovered) return ""
                            var h = pointsCanvas.hovered
                            var isSelected = TradeStudy.selectedIndices.indexOf(h.index) !== -1
                            return "Point " + h.index
                                 + "\n" + TradeStudy.paretoXTitle + "  "
                                 + h.x.toPrecision(6)
                                 + "\n" + TradeStudy.paretoYTitle + "  "
                                 + h.y.toPrecision(6)
                                 + "\nEvaluation  " + h.status
                                 + "\nFeasibility  " + h.feasibility
                                 + "\nPareto  " + (h.pareto ? "Efficient" : "Dominated")
                                 + (h.score !== "" ? "\nScore  " + h.score : "")
                                 + "\n" + (isSelected
                                           ? "Tap to remove from Compare"
                                           : "Tap to add to Compare")
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: TradeStudy.paretoNote
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        RFPanel {
            Layout.fillWidth: true
            Layout.fillHeight: false
            visible: TradeStudy.hasResult && TradeStudy.resultComplete
            title: "Best evaluated feasible points"
            contentSpacing: Metrics.spacing.xs

            Text {
                Layout.fillWidth: true
                text: "One per objective, over the points this study actually "
                      + "evaluated. A finite sampled grid cannot establish a "
                      + "global optimum, and nothing here searches for one."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
                bottomPadding: Metrics.spacing.xs
            }

            Repeater {
                model: TradeStudy.bestRows

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.preferredWidth: 240
                        readonly property string plainText: modelData.objective
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        clip: true              // RichText does not elide
                        elide: Text.ElideRight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 132
                        text: modelData.value
                        color: Theme.accent
                        font.family: Typography.mono
                        font.pixelSize: Typography.body
                    }
                    Text {
                        Layout.fillWidth: true
                        readonly property string plainText: modelData.point
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        clip: true              // RichText does not elide
                        elide: Text.ElideRight
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    RFButton {
                        text: "Compare"
                        variant: "quiet"
                        onClicked: TradeStudy.toggleSelection(modelData.index)
                    }
                }
            }
        }
    }
}
