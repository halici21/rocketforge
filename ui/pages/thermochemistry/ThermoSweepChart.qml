import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * One quantity against O/F.
 *
 * The series arrives as SEGMENTS, not as one list of points. A point the
 * provider could not solve ends a segment and the next one starts after it, so
 * the line breaks across a failure instead of joining the values on either
 * side - which would draw a straight run of physics nobody computed.
 *
 * The sampled points are drawn as dots on top of the line, because a sweep is
 * a set of discrete solves and the user has to be able to see which mixture
 * ratios were actually computed.
 *
 * No smoothing, no spline, no fit. RFLineChart joins consecutive points with
 * straight segments and does nothing else, which is the honest rendering of
 * sampled data.
 */
Item {
    id: chart

    property string quantity: "temperature"

    // Series and axis labels come from the controller as method calls rather
    // than properties, so they are pulled once when the sweep changes rather
    // than re-derived on every repaint. Both are computed in Python when the
    // sweep completes; nothing here recomputes anything.
    property var axisValue: ({ label: "", raw: "", unit: "", qualifier: "" })
    property var seriesValue: []
    property var peakValue: ({})

    function refresh() {
        axisValue = Thermochemistry.sweepAxis(quantity)
        seriesValue = Thermochemistry.sweepSeries(quantity)
        peakValue = Thermochemistry.sweepMaximum(quantity)
    }

    Component.onCompleted: refresh()
    onQuantityChanged: refresh()

    Connections {
        target: Thermochemistry
        function onSweepChanged() { chart.refresh() }
    }

    RFPanel {
        anchors.fill: parent
        title: chart.axisValue.raw + " vs O/F"
        contentSpacing: Metrics.spacing.xs

        trailing: Component {
            Row {
                spacing: Metrics.spacing.s

                RFStatusChip {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: chart.axisValue.qualifier !== ""
                    text: chart.axisValue.qualifier
                    showDot: false
                }
            }
        }

        RFLineChart {
            Layout.fillWidth: true
            Layout.fillHeight: true
            logScale: false
            showPoints: true
            xLabel: "Mixture ratio  O/F   (oxidiser mass / fuel mass)"
            yLabel: chart.axisValue.label
            guides: Thermochemistry.sweepFailedRatios
            series: {
                var out = []
                for (var i = 0; i < chart.seriesValue.length; ++i)
                    out.push({ points: chart.seriesValue[i],
                               color: Theme.accent, width: 1.6 })
                return out
            }
            markers: chart.peakValue.of !== undefined
                     ? [{ x: chart.peakValue.of, y: chart.peakValue.value,
                          label: "max in sweep" }]
                     : []
        }

        Text {
            Layout.fillWidth: true
            text: chart.peakValue.text !== undefined ? chart.peakValue.text : ""
            visible: text !== ""
            wrapMode: Text.WordWrap
            color: Theme.textMuted
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }
    }
}
