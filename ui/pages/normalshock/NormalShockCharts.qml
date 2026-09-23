import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Normal-shock charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. RFLineChart draws points it is given
 * and evaluates nothing.
 *
 * The published values can be overlaid as discrete dots. They are a *check*
 * drawn on top of the computed curve, never the curve itself, and they are
 * never joined into a line - Appendix B prints values at particular Mach
 * numbers and says nothing about what lies between them.
 */
Item {
    id: page

    readonly property var quantities: NormalShock.tableColumns.filter(function (c) {
        return c.key !== "mach1"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? NormalShock.chartSeries(active.key) : []
    property bool logScale: true
    property bool showReference: false
    readonly property var referencePoints: (showReference && active)
                                           ? NormalShock.referenceSeries(active.key) : []

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
                    Layout.preferredWidth: 440
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

                RFToggle {
                    text: "Overlay Appendix B"
                    checked: page.showReference
                    enabled: NormalShock.referenceAvailable
                    onToggled: page.showReference = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: page.points.length + " points · γ = " + NormalShock.tableGamma.toFixed(3)
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }

        RFPanel {
            title: page.active ? page.active.label + "  versus  M₁" : "Chart"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                Text {
                    text: page.showReference ? "line: RocketForge · dots: Anderson Appendix B"
                                             : "computed by RocketForge"
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
                referencePoints: page.referencePoints
                logScale: page.logScale
                xLabel: "Upstream Mach number  M₁"

                Connections {
                    target: NormalShock
                    function onTableChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: page.showReference && page.referencePoints.length > 0
                text: "The dots are printed values, plotted where they are printed and nowhere "
                      + "between. They check the curve; they never produce it."
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
