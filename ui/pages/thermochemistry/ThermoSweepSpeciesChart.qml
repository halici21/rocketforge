import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"
import "../../data"

/*
 * Selected species against O/F.
 *
 * The basis is stated on the axis and in the legend, because a mole fraction
 * plotted under a mass-fraction label is a wrong chart that looks right. The
 * controller supplies the values already on the requested basis; nothing here
 * converts anything.
 *
 * Like the property charts, the lines break across a point that did not solve
 * rather than joining across it.
 */
Item {
    id: chart

    property var speciesValue: []
    property QtObject peekGroup: null
    signal focusRequested()
    readonly property string title: "Species vs O/F"
    readonly property real selectedOf: Thermochemistry.sweepSelection.active
                                       ? Thermochemistry.sweepSelection.x : NaN

    opacity: peek.receded ? 0.45 : 1
    Behavior on opacity { NumberAnimation { duration: Motion.fast } }

    function refresh() { speciesValue = Thermochemistry.sweepSpeciesSeries }

    Component.onCompleted: refresh()

    Connections {
        target: Thermochemistry
        function onSweepChanged() { chart.refresh() }
    }

    readonly property var palette: Theme.series

    RFPanel {
        anchors.fill: parent
        title: "Species vs O/F"
        contentSpacing: Metrics.spacing.xs

        trailing: Component {
            RFStatusChip {
                text: Thermochemistry.sweepSpeciesBasis === "mole"
                      ? "mole fraction" : "mass fraction"
                showDot: false
            }
        }

        RFLineChart {
            Layout.fillWidth: true
            Layout.fillHeight: true
            logScale: true
            showPoints: true
            xLabel: "Mixture ratio  O/F   (oxidiser mass / fuel mass)"
            yLabel: Thermochemistry.sweepSpeciesAxis
            guides: Thermochemistry.sweepFailedRatios
            series: {
                var out = []
                for (var i = 0; i < chart.speciesValue.length; ++i) {
                    var entry = chart.speciesValue[i]
                    var colour = chart.palette[i % chart.palette.length]
                    for (var s = 0; s < entry.segments.length; ++s)
                        out.push({ points: entry.segments[s],
                                   color: colour, width: 1.5 })
                }
                return out
            }
            markerX: chart.selectedOf
            markerRegions: false
            markerLabel: isNaN(chart.selectedOf) ? "" : Thermochemistry.sweepSelection.label

            TapHandler {
                onTapped: function (point) {
                    Thermochemistry.selectSweepNear(parent.toDataX(point.position.x))
                    ShellContext.inspectorOpen = true
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: Metrics.spacing.m

            Repeater {
                model: chart.speciesValue

                delegate: Row {
                    required property var modelData
                    required property int index
                    spacing: Metrics.spacing.xs

                    Rectangle {
                        width: 10
                        height: 2
                        radius: 1
                        anchors.verticalCenter: parent.verticalCenter
                        color: chart.palette[index % chart.palette.length]
                    }
                    Text {
                        text: Notation.species(modelData.name)
                        textFormat: Notation.speciesFormat(modelData.name)
                        color: Theme.textSecondary
                        font.family: Typography.mono
                        font.pixelSize: Typography.meta
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: chart.speciesValue.length === 0
            text: "Choose species in the setup drawer to plot them."
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }

    RFPlotPeek {
        id: peek
        group: chart.peekGroup
        onFocusRequested: chart.focusRequested()
    }
}
