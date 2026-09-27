import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * Oblique shock study.
 *
 * The θ–β–M diagram is the reason this section exists, so it gets the room.
 * The secondary curve below it — how the downstream Mach number, the shock
 * angle or the stagnation-pressure loss varies with deflection — is read from
 * the same generated sweep the Table section renders (ObliqueShock.chartData),
 * so the views cannot disagree, and it is labelled with the M₁ and branch that
 * sweep was *generated* with, not with a setting edited since.
 *
 * The sweep itself is an engineering table on the Table section (it used to be
 * a drawer here); a row or a range selected there is this curve's crosshair or
 * quiet band, and a click here selects the exact generated sample. Nothing on
 * this page solves: the diagram reads the curve the controller holds for the
 * current M₁ and γ.
 */
Item {
    id: page

    // At the 1366x768 floor there is not enough height for a full-size
    // primary plot, an explanatory paragraph AND the secondary plot. Reflow
    // rather than shrink: the paragraph and the secondary curve go, and the
    // primary plot -- the reason this view exists -- keeps a floor it cannot
    // fall below. The same quantities remain on the Table section.
    readonly property bool compact: page.height < 720

    readonly property var quantities: ObliqueShock.tableColumns.filter(function (c) {
        return c.key !== "theta"
    })
    property int quantityIndex: 1
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    // A property of the controller, so a regenerated sweep redraws the curve.
    readonly property var points: active ? (ObliqueShock.chartData[active.key] || []) : []

    // What the plotted sweep is: the settings it was generated with.
    readonly property var generated: ObliqueShock.tableGenerated
    readonly property string sweepWords: page.generated.mach1 === undefined ? "no sweep generated"
        : "M₁ = " + (+Number(page.generated.mach1).toPrecision(6)) + " · "
          + (page.generated.convention === "comparison" ? "weak and strong"
                                                          : page.generated.branch + " branch")

    function copyValues() {
        if (!page.active)
            return
        var e = secondary.extent()
        var lines = ["theta\t" + page.active.key]
        for (var i = 0; i < page.points.length; ++i) {
            var p = page.points[i]
            if (p.x >= e.xmin && p.x <= e.xmax)
                lines.push(p.x + "\t" + p.y)
        }
        ObliqueShock.copyText(lines.join("\n"))
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

                RFBoundNumberField {
                    Layout.preferredWidth: 140
                    label: "Upstream Mach  M₁"
                    value: ObliqueShock.mach1
                    digits: 4
                    decimals: 4
                    step: 0.1
                    // Drives the sweep as well as the diagram: two charts on
                    // one page showing two different Mach numbers, neither of
                    // them labelled, is how a reader is misled.
                    onValueEdited: function (v) {
                        ObliqueShock.mach1 = v
                        ObliqueShock.tableMach1 = v
                        ObliqueShock.regenerateTable()
                    }
                }

                RFToggle {
                    text: "Overlay other Mach numbers"
                    checked: diagram.showComparison
                    onToggled: diagram.showComparison = checked
                }

                RFToggle {
                    text: "Mark the sonic wave angle"
                    checked: diagram.showSonicGuide
                    onToggled: diagram.showSonicGuide = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: ObliqueShock.limits.thetaMax !== undefined
                          ? "θ_max = " + ObliqueShock.limits.thetaMax.toFixed(4) + "°"
                          : ""
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                // The sweep's rows are on the Table section.
                RFToolButton {
                    objectName: "obliqueShockOpenTable"
                    text: "Sweep table · " + ObliqueShock.tableRowCount + " rows  ›"
                    tooltip: "Open the generated deflection sweep on the Table section"
                    onClicked: ObliqueShock.requestTab(2)
                }
            }
        }

        RFPanel {
            title: "Shock angle β versus flow deflection θ"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 280

            trailing: Component {
                Text {
                    text: "computed by RocketForge · the same solver as the Calculator"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            ObliqueShockDiagram {
                id: diagram
                chartName: "obliqueShockStudyDiagram"
                Layout.fillWidth: true
                Layout.fillHeight: true
                compact: page.compact
            }

            Text {
                Layout.fillWidth: true
                visible: !page.compact
                readonly property string plainText: "The curve rises from a Mach wave at β = μ to the maximum deflection and "
                      + "falls back to a normal shock at β = 90°, which is why every attainable "
                      + "deflection has two wave angles. Past θ_max the body cannot turn the "
                      + "flow at all and the shock detaches."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        RFPanel {
            objectName: "obliqueShockSweepPanel"
            title: (page.active ? page.active.label + "  versus  θ" : "Secondary")
                   + "   ·   " + page.sweepWords
            Layout.fillWidth: true
            // At the floor this secondary curve yields entirely rather than
            // showing half of itself; the same quantities remain on Table.
            visible: !page.compact
            Layout.preferredHeight: visible ? 300 : 0

            trailing: Component {
                RFSegmentedControl {
                    width: 360
                    model: page.quantities.map(function (q) { return q.label })
                    currentIndex: page.quantityIndex
                    useMonoFont: true
                    onSelected: function (index) { page.quantityIndex = index }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                RFPlotToolbar {
                    interaction: interact
                    canCopy: true
                    onCopyRequested: page.copyValues()
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: ObliqueShock.tableStale
                    text: "sweep settings edited since this sweep was generated"
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFLineChart {
                id: secondary
                objectName: "obliqueShockSweepChart"
                Layout.fillWidth: true
                Layout.fillHeight: true
                builtInHover: false
                dataKey: page.active ? page.active.key : ""

                points: page.points
                logScale: false
                xLabel: "Flow deflection  θ  [deg]"
                yLabel: page.active ? page.active.label : ""

                // A row selected on the Table section is this crosshair; a
                // range is a quiet band. A click reads a real generated
                // sample into the shared selection. Nothing is solved.
                RFPlotInteraction {
                    id: interact
                    chart: secondary
                    readonly property bool rangeSelected: ObliqueShock.selection.kind === "tableRange"
                    selectionX: ObliqueShock.selection.active && !rangeSelected ? ObliqueShock.selection.x : NaN
                    selectionLabel: ObliqueShock.selection.kind === "tableRow" ? ObliqueShock.selection.label : ""
                    highlightX0: rangeSelected ? ObliqueShock.selection.x : NaN
                    highlightX1: rangeSelected ? ObliqueShock.selection.x1 : NaN
                    xSymbol: "θ"
                    quantity: page.active ? page.active.key : ""
                    unit: ""
                    seriesLabels: [page.active ? page.active.label : ""]
                    onPointSelected: function (x, y, s, label) {
                        if (s === 0 && page.active) {
                            ObliqueShock.selection.selectPoint("plotPoint", page.active.key, x, y,
                                                               page.active.label, "chart")
                            ShellContext.inspectorOpen = true
                        }
                    }
                    onSelectionCleared: ObliqueShock.selection.clear()
                }
            }
        }
    }
}
