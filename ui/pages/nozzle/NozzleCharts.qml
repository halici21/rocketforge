import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Distributed quantities along the nozzle.
 *
 * The chart draws points it is given and evaluates nothing. What matters here
 * is what it is given: when a shock exists the backend returns *two* series,
 * cut at the shock station, so the renderer draws a genuine break rather than
 * a line sloping across the discontinuity. Switch to an overexpanded back
 * pressure and one series comes back instead — and the shock marker goes with
 * it.
 *
 * The stagnation-pressure chart is the one worth arriving at: flat, one step,
 * flat. That picture is the model's whole statement about irreversibility —
 * it happens at the shock and nowhere else.
 */
Item {
    id: page

    readonly property var quantities: Nozzle.chartQuantities
    property int quantityIndex: 0
    property bool logScale: false

    // The shared station selection: the Regime map's drawing, these charts
    // and the inspector read and write the same one.
    NozzleLinks { id: links }

    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)]
                                  : null

    // Read from the distribution property, not the series() slot: a binding
    // re-reads a property when the result changes and never re-calls a slot,
    // so the slot form kept drawing the previous operating point.
    readonly property var series: {
        if (!active)
            return []
        var parts = Nozzle.distribution[active.key] || []
        var out = []
        for (var i = 0; i < parts.length; ++i)
            out.push({
                points: parts[i].points,
                color: parts[i].label === "downstream" ? Theme.textSecondary : Theme.accent,
                dashed: parts[i].label === "downstream",
                width: 1.8
            })
        return out
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            Layout.fillWidth: true
            Layout.preferredHeight: 78

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                ColumnLayout {
                    Layout.preferredWidth: 620
                    spacing: 3
                    RFSectionLabel { text: "Quantity" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: page.quantities.map(function (q) { return q.label })
                        currentIndex: page.quantityIndex
                        onSelected: function (index) { page.quantityIndex = index }
                    }
                }

                ColumnLayout {
                    spacing: 1
                    RFToggle {
                        text: "Logarithmic vertical axis"
                        checked: page.logScale
                        onToggled: page.logScale = checked
                    }
                    Text {
                        visible: page.logScale && !chart.logScaleActive
                        text: "not applied — the data reaches zero"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: Nozzle.regimeLabel + "  ·  p_b/p₀ = "
                          + Nozzle.backPressureRatio.toFixed(5)
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.active ? page.active.label + "  along the nozzle" : "Chart"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                RowLayout {
                    spacing: Metrics.spacing.l

                    Repeater {
                        model: Nozzle.hasShock
                               ? [{ swatch: Theme.accent, text: "upstream of the shock" },
                                  { swatch: Theme.textSecondary, text: "downstream" }]
                               : [{ swatch: Theme.accent, text: "shock-free" }]

                        delegate: RowLayout {
                            required property var modelData
                            spacing: Metrics.spacing.xs
                            Rectangle {
                                Layout.alignment: Qt.AlignVCenter
                                width: 18; height: 2
                                color: modelData.swatch
                            }
                            Text {
                                text: modelData.text
                                color: Theme.textMuted
                                font.family: Typography.sans
                                font.pixelSize: Typography.meta
                            }
                        }
                    }
                }
            }

            RFPlotToolbar {
                interaction: interact
            }

            RFLineChart {
                id: chart
                objectName: "nozzleDistributionChart"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240
                builtInHover: false
                dataKey: page.active ? page.active.key : ""

                series: page.series
                // Throat always; shock only while there is one to mark.
                guides: Nozzle.stationMarkers
                logScale: page.logScale
                xLabel: "axial position  x   [m]"
                yLabel: page.active ? page.active.label : ""

                Connections {
                    target: Nozzle
                    function onResultsChanged() { chart.repaint() }
                    function onInputsChanged() { chart.repaint() }
                }

                // Linked: a click near a station selects the station (and the
                // drawing highlights it); the selection draws here as a
                // crosshair with a ring on each series' real sample.
                RFPlotInteraction {
                    id: interact
                    chart: chart
                    selectionX: Nozzle.selection.kind === "tableRange" ? NaN : links.selectedX
                    selectionLabel: Nozzle.selection.kind === "station" ? "" : Nozzle.selection.label
                    highlightX0: Nozzle.selection.kind === "tableRange" ? Nozzle.selection.x : NaN
                    highlightX1: Nozzle.selection.kind === "tableRange" ? Nozzle.selection.x1 : NaN
                    xSymbol: "x"
                    quantity: page.active ? page.active.key : ""
                    unit: page.active ? page.active.unit : ""
                    seriesLabels: Nozzle.hasShock ? ["upstream", "downstream"] : [""]
                    onPointSelected: function (x, y, s, label) {
                        links.selectNear(x, y, page.active ? page.active.label : "", "chart")
                    }
                    onSelectionCleared: links.clear()
                }
            }
        }

        RFPanel {
            title: "Nozzle contour"
            Layout.fillWidth: true
            Layout.preferredHeight: 180

            trailing: Component {
                Text {
                    text: "straight-walled cone · schematic, not a designed contour"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFLineChart {
                id: contour
                Layout.fillWidth: true
                Layout.fillHeight: true
                builtInHover: false

                series: Nozzle.contour.map(function (part) {
                    return { points: part.points, color: Theme.textSecondary, width: 1.4 }
                })
                guides: Nozzle.stationMarkers
                logScale: false
                xLabel: "axial position  x   [m]"
                yLabel: "wall radius  [m]"

                Connections {
                    target: Nozzle
                    function onInputsChanged() { contour.repaint() }
                    function onResultsChanged() { contour.repaint() }
                }

                RFPlotInteraction {
                    chart: contour
                    selectionX: Nozzle.selection.kind === "tableRange" ? NaN : links.selectedX
                    selectionLabel: Nozzle.selection.kind === "station" ? "" : Nozzle.selection.label
                    highlightX0: Nozzle.selection.kind === "tableRange" ? Nozzle.selection.x : NaN
                    highlightX1: Nozzle.selection.kind === "tableRange" ? Nozzle.selection.x1 : NaN
                    xSymbol: "x"
                    quantity: "wall_radius"
                    unit: "m"
                    seriesLabels: ["wall", ""]
                    onPointSelected: function (x, y, s, label) { links.selectAxial(x, "chart") }
                    onSelectionCleared: links.clear()
                }
            }
        }
    }
}
