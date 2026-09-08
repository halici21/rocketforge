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

    function seriesColor(key) {
        if (key === "efficient") return Theme.accent
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
                xFormat: function (v) { return v.toPrecision(5) }
                yFormat: function (v) { return v.toPrecision(5) }

                legend: [
                    { name: "Pareto-efficient ◆", color: Theme.accent },
                    { name: "Feasible, dominated ●", color: Theme.textMuted },
                    { name: "Infeasible or failed ✕", color: Theme.warning }
                ]

                Repeater {
                    model: view.series

                    delegate: Repeater {
                        required property var modelData
                        readonly property string seriesKey: modelData.key
                        model: modelData.points

                        delegate: Item {
                            required property var modelData
                            readonly property bool efficient: seriesKey === "efficient"
                            readonly property bool excluded: seriesKey === "excluded"

                            x: surface.mapX(modelData.x) - width / 2
                            y: surface.mapY(modelData.y) - height / 2
                            width: efficient ? 11 : 8
                            height: width

                            // Shape, not only colour. A reader who cannot rely
                            // on hue still sees three distinct groups.
                            Rectangle {
                                anchors.fill: parent
                                visible: !parent.excluded
                                radius: parent.efficient ? 2 : width / 2
                                rotation: parent.efficient ? 45 : 0
                                color: parent.efficient ? Theme.accent : "transparent"
                                border.width: Metrics.hairline
                                border.color: parent.efficient
                                              ? Theme.accent : Theme.textMuted
                                opacity: parent.efficient ? 1.0 : 0.65
                            }

                            Item {
                                anchors.fill: parent
                                visible: parent.excluded
                                opacity: 0.7

                                Rectangle {
                                    anchors.centerIn: parent
                                    width: parent.width
                                    height: Metrics.hairline * 2
                                    rotation: 45
                                    color: Theme.warning
                                }
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: parent.width
                                    height: Metrics.hairline * 2
                                    rotation: -45
                                    color: Theme.warning
                                }
                            }

                            HoverHandler { id: markerHover }
                            TapHandler {
                                onTapped: TradeStudy.toggleSelection(modelData.index)
                            }
                            RFTooltip {
                                visible: markerHover.hovered
                                text: "Point " + modelData.index
                                      + "\n" + TradeStudy.paretoXTitle + "  "
                                      + modelData.x.toPrecision(6)
                                      + "\n" + TradeStudy.paretoYTitle + "  "
                                      + modelData.y.toPrecision(6)
                                      + "\nTap to add to Compare"
                            }
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
                        text: modelData.objective
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
                        text: modelData.point
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
