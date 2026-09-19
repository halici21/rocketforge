import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Isentropic charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. The canvas draws points it is given;
 * it evaluates nothing.
 *
 * One quantity at a time by default: p0/p spans four decades over this Mach
 * range while T0/T spans one, and overlaying them on a shared linear axis
 * would flatten the smaller curve into the baseline.
 */
Item {
    id: page

    readonly property var quantities: Isentropic.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0 ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? Isentropic.chartSeries(active.key) : []
    property bool logScale: true

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
                    Layout.preferredWidth: 420
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

                Text {
                    // A toggle that silently does nothing is worse than one
                    // that says why: the log axis cannot apply to a quantity
                    // whose range is too narrow for it to mean anything.
                    visible: page.logScale && !plot.logScaleActive
                    text: "range too narrow for a log axis"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: page.points.length + " points · γ = " + Isentropic.tableGamma.toFixed(3)
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

            // Was a private Canvas reimplementation of the shared chart:
            // the same grid, the same log mapping, the same sonic marker,
            // written a second time. It drifted, as a duplicate does --
            // it had no y-axis title at all, no hover readout, and it kept
            // the old fractional tick positions after RFLineChart moved to
            // nice numbers, so this one page showed a different axis
            // grammar from every other relation in the application.
            // rf-scientific-visualization: a chart belongs on the shared
            // surface, not as an independent visual language.
            RFLineChart {
                id: plot
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 240

                points: page.points
                logScale: page.logScale
                // The one Mach number every reader looks for. RFLineChart
                // draws it only when it falls inside the plotted range.
                markerX: 1
                markerLabel: "M = 1"
                xLabel: "Mach number"
                yLabel: page.active ? page.active.label : ""

                Connections {
                    target: Isentropic
                    function onTableChanged() { plot.repaint() }
                }
            }
        }
    }
}
