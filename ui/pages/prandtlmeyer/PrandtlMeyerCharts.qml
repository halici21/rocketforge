import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Prandtl–Meyer charts.
 *
 * Plotted from the same computed block the table renders, so the two can never
 * disagree about what the physics said. RFLineChart draws points it is given
 * and evaluates nothing.
 *
 * ν and μ are shown one at a time rather than overlaid. They share an axis
 * label — degrees — but not a shape: ν climbs from zero towards its finite
 * ceiling while μ falls from a right angle towards zero, and putting them on
 * one linear axis makes both harder to read rather than easier.
 */
Item {
    id: page

    readonly property var quantities: PrandtlMeyer.tableColumns.filter(function (c) {
        return c.key !== "mach"
    })
    property int quantityIndex: 0
    readonly property var active: quantities.length > 0
                                  ? quantities[Math.min(quantityIndex, quantities.length - 1)] : null
    readonly property var points: active ? PrandtlMeyer.chartSeries(active.key) : []
    property bool logScale: false
    property bool showReference: false
    readonly property var referencePoints: (showReference && active)
                                           ? PrandtlMeyer.referenceSeries(active.key) : []

    readonly property bool isNu: active !== null && active.key === "nu"
    readonly property bool isMu: active !== null && active.key === "mach_angle"

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
                    text: "Overlay Appendix C"
                    checked: page.showReference
                    enabled: PrandtlMeyer.referenceAvailable
                    onToggled: page.showReference = checked
                }

                Item { Layout.fillWidth: true }

                Text {
                    readonly property string plainText: page.points.length + " points · γ = " + PrandtlMeyer.tableGamma.toFixed(3)
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
                    text: page.showReference ? "line: RocketForge · dots: Anderson Appendix C"
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
                xLabel: "Mach number  M"
                yLabel: page.active ? page.active.label + "  [°]" : ""

                // The asymptote a reader looks for on the nu curve, and the
                // right angle the Mach angle starts from. Both are supplied by
                // the controller; nothing is computed here.
                guides: page.isNu
                        ? [{ value: PrandtlMeyer.nuMax, axis: "y",
                             label: "ν_max = " + PrandtlMeyer.nuMax.toFixed(3) + "°" }]
                        : (page.isMu
                           ? [{ value: 90, axis: "y", label: "μ = 90° at M = 1" }]
                           : [])

                Connections {
                    target: PrandtlMeyer
                    function onTableChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: page.isNu
                readonly property string plainText: "ν rises from zero at Mach 1 towards a finite ceiling: for γ = 1.4 no "
                      + "expansion can turn a flow further than "
                      + PrandtlMeyer.nuMax.toFixed(4) + "°, however fast it ends up going."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: page.isMu
                readonly property string plainText: "μ falls from a right angle at Mach 1: the faster the flow, the further "
                      + "back its Mach lines sweep. This curve is pure geometry — arcsin(1/M) "
                      + "— and does not depend on γ at all."
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
    }
}
