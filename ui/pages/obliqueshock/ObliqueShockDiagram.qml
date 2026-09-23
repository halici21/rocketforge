import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The θ–β–M diagram.
 *
 * A real engineering chart, not a sketch: every point comes from
 * `ObliqueShock.curve()`, which is the same service call the calculator makes.
 * The two therefore cannot disagree about what the physics said, and clicking
 * the chart is deliberately *not* a way to solve anything — a chart that
 * answered questions by interpolating its own pixels would be a second,
 * unvalidated solver.
 *
 * What it shows, for the selected M₁:
 *
 *   the weak branch, from the Mach angle up to the angle of maximum deflection
 *   the strong branch, from there to a right angle, drawn dashed
 *   θ_max, and the wave angle at which it occurs
 *   the wave angle at which the flow behind turns sonic
 *   the solved operating point, on whichever branch was solved
 *
 * When the requested deflection exceeds θ_max the operating point disappears
 * and a marker shows where the request fell, rather than a fabricated β.
 */
Item {
    id: root

    property bool compact: false
    property bool showComparison: false
    property bool showSonicGuide: true

    // `curve()` is a slot, so reading it alone creates no dependency and the
    // diagram would keep drawing the last Mach number's curve under a header
    // showing a new one. Naming mach1 and gamma in the binding is what makes
    // the curve follow them.
    readonly property var curve: (ObliqueShock.mach1 > 0 && ObliqueShock.gamma > 0)
                                 ? ObliqueShock.curve() : ({})
    readonly property var point: ObliqueShock.operatingPoint

    readonly property var comparisonSeries: {
        if (!showComparison)
            return []
        var out = []
        var machs = ObliqueShock.comparisonMachs
        var current = ObliqueShock.mach1        // a real dependency, as above
        for (var i = 0; i < machs.length; ++i) {
            if (Math.abs(machs[i] - current) < 1e-9)
                continue
            var other = ObliqueShock.curveFor(machs[i])
            if (!other || !other.weak)
                continue
            out.push({ points: other.weak.concat(other.strong),
                       color: Theme.textDisabled, dashed: false, width: 1.0 })
        }
        return out
    }

    readonly property var branchSeries: {
        if (!curve || !curve.weak)
            return []
        return [
            { points: curve.weak, color: Theme.accent, dashed: false, width: 2.0 },
            { points: curve.strong, color: Theme.textSecondary, dashed: true, width: 1.6 }
        ]
    }

    readonly property var markers: {
        if (!point || point.both === undefined)
            return []
        if (point.both === true) {
            return [
                { x: point.theta, y: point.betaWeak, label: "weak" },
                { x: point.theta, y: point.betaStrong, label: "strong" }
            ]
        }
        if (point.theta === undefined || point.beta === undefined)
            return []
        return [{ x: point.theta, y: point.beta, label: point.branch }]
    }

    readonly property var guides: {
        if (!curve || curve.thetaMax === undefined)
            return []
        var out = [
            { value: curve.thetaMax, axis: "x", label: "θ_max " + curve.thetaMax.toFixed(2) + "°" },
            { value: curve.betaAtThetaMax, axis: "y",
              label: "β at θ_max " + curve.betaAtThetaMax.toFixed(2) + "°" },
            { value: curve.machAngle, axis: "y", label: "μ " + curve.machAngle.toFixed(2) + "°" }
        ]
        if (root.showSonicGuide)
            out.push({ value: curve.betaSonic, axis: "y",
                       label: "M₂ = 1 at β " + curve.betaSonic.toFixed(2) + "°" })
        // A detached request has no wave angle to mark, so the requested
        // deflection is shown against the limit instead of being drawn as a
        // point that does not exist.
        if (ObliqueShock.detached)
            out.push({ value: ObliqueShock.inputValue, axis: "x",
                       label: "requested θ " + ObliqueShock.inputValue.toFixed(2) + "° — detached" })
        return out
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.xs

        RFLineChart {
            id: chart
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: root.compact ? 150 : 300

            series: root.comparisonSeries.concat(root.branchSeries)
            markers: root.markers
            guides: root.guides
            logScale: false
            xLabel: "Flow deflection  θ  [deg]"
            yLabel: "Shock angle  β  [deg]"
            xMin: 0
            yMin: 0
            yMax: 90

            Connections {
                target: ObliqueShock
                function onCurveChanged() { chart.repaint() }
                function onResultsChanged() { chart.repaint() }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: !root.compact
            spacing: Metrics.spacing.l

            Repeater {
                model: [
                    { swatch: Theme.accent, dashed: false, text: "weak branch" },
                    { swatch: Theme.textSecondary, dashed: true, text: "strong branch" },
                    { swatch: Theme.textDisabled, dashed: false, text: "other Mach numbers" }
                ]

                delegate: RowLayout {
                    required property var modelData
                    required property int index
                    spacing: Metrics.spacing.xs
                    visible: index < 2 || root.showComparison

                    Rectangle {
                        Layout.alignment: Qt.AlignVCenter
                        width: 18
                        height: 2
                        color: modelData.swatch
                        opacity: modelData.dashed ? 0.65 : 1.0
                    }
                    Text {
                        text: modelData.text
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Text {
                readonly property string plainText: "M₁ = " + ObliqueShock.mach1.toFixed(2) + " · γ = "
                      + ObliqueShock.gamma.toFixed(3)
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }
    }
}
