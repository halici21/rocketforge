import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Oblique shock charts.
 *
 * The θ–β–M diagram is the reason this section exists, so it gets the room.
 * The secondary curves below it — how the downstream Mach number and the
 * stagnation-pressure loss vary with deflection — are read from the same
 * generated study the table renders, so the three views cannot disagree.
 */
Item {
    id: page

    readonly property var quantities: ObliqueShock.tableColumns.filter(function (c) {
        return c.key !== "theta"
    })
    property int quantityIndex: 1
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? ObliqueShock.chartSeries(active.key) : []

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
                    text: ObliqueShock.limits.thetaMax !== undefined
                          ? "θ_max = " + ObliqueShock.limits.thetaMax.toFixed(4) + "°"
                          : ""
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: "Shock angle β versus flow deflection θ"
            Layout.fillWidth: true
            Layout.fillHeight: true

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
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            Text {
                Layout.fillWidth: true
                text: "The curve rises from a Mach wave at β = μ to the maximum deflection and "
                      + "falls back to a normal shock at β = 90°, which is why every attainable "
                      + "deflection has two wave angles. Past θ_max the body cannot turn the "
                      + "flow at all and the shock detaches."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        RFPanel {
            title: (page.active ? page.active.label + "  versus  θ" : "Secondary")
                   + "   ·   M₁ = " + ObliqueShock.tableMach1.toFixed(2)
                   + " (" + ObliqueShock.tableBranch + " branch)"
            Layout.fillWidth: true
            Layout.preferredHeight: 250

            trailing: Component {
                RFSegmentedControl {
                    width: 320
                    model: page.quantities.map(function (q) { return q.label })
                    currentIndex: page.quantityIndex
                    useMonoFont: true
                    onSelected: function (index) { page.quantityIndex = index }
                }
            }

            RFLineChart {
                id: secondary
                Layout.fillWidth: true
                Layout.fillHeight: true

                points: page.points
                logScale: false
                xLabel: "Flow deflection  θ  [deg]"
                yLabel: page.active ? page.active.label : ""

                Connections {
                    target: ObliqueShock
                    function onTableChanged() { secondary.repaint() }
                }
            }
        }
    }
}
