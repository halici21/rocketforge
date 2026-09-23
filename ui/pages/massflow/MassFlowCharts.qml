import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Mass-flow charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. RFLineChart draws points it is given
 * and evaluates nothing.
 *
 * The mass-flow parameter is the one curve worth arriving at this page for: it
 * rises from zero at rest, peaks at Mach 1, and falls away again. That single
 * hump is what choking *is*, and seeing it settles the question far faster than
 * a paragraph does.
 */
Item {
    id: page

    readonly property var quantities: MassFlow.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? MassFlow.chartSeries(active.key) : []
    property bool logScale: false

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
                    Layout.preferredWidth: 460
                    spacing: 3
                    RFSectionLabel { text: "Quantity" }
                    RFSegmentedControl {
                        Layout.fillWidth: true
                        model: page.quantities.map(function (q) { return q.label })
                        currentIndex: page.quantityIndex
                        useMonoFont: true
                        onSelected: function (index) { page.quantityIndex = index }
                    }
                }

                RFToggle {
                    text: "Logarithmic vertical axis"
                    checked: page.logScale
                    onToggled: page.logScale = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: page.points.length + " points · γ = " + MassFlow.tableGamma.toFixed(3)
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.active ? page.active.label + "  versus  M" : "Chart"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                Text {
                    text: "computed by RocketForge"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFLineChart {
                id: chart
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                points: page.points
                logScale: page.logScale
                markerX: 1.0
                markerLabel: "M = 1  (choked)"

                Connections {
                    target: MassFlow
                    function onTableChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: page.active !== null && page.active.key === "mass_flow_parameter"
                text: "The peak at M = 1 is the whole of choking: no combination of "
                      + "downstream conditions moves the flow past it, because for this "
                      + "stagnation state and area there is no higher value to reach."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
