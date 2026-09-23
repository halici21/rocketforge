import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * The back-pressure regime map.
 *
 * The signature view of this page: every band edge is a computed critical, so
 * the map is a picture of *this* nozzle rather than an authored illustration.
 * Change the area ratio and the bands move, because the thresholds do.
 *
 * Ideal expansion is a single point on the axis, not a range, and it is drawn
 * as a point. Widening it to something clickable would be the one dishonest
 * thing this map could do, so the three exact conditions are reachable by the
 * preset buttons instead — each of which sets the back pressure to the
 * threshold the backend computed.
 */
Item {
    id: page

    readonly property var bands: Nozzle.regimeBands
    readonly property real current: Nozzle.backPressureRatio

    // The band the current operating point falls in, so the map can highlight
    // it. Comparison only; the regime itself is decided by the physics layer.
    readonly property int activeIndex: {
        for (var i = 0; i < bands.length; ++i)
            if (bands[i].key === Nozzle.regime)
                return i
        return -1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.m

        RFPanel {
            title: "Back pressure"
            Layout.fillWidth: true
            contentSpacing: Metrics.spacing.s

            trailing: Component {
                Row {
                    spacing: 5
                    Text {
                        id: value
                        text: Nozzle.backPressureRatio.toFixed(6)
                        color: Theme.text
                        font.family: Typography.mono
                        font.pixelSize: Typography.readoutMedium
                        font.weight: Typography.medium
                    }
                    Text {
                        anchors.baseline: value.baseline
                        readonly property string plainText: "p₀"
                        text: Notation.rich(plainText)
                        textFormat: Notation.textFormat(plainText)
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.l

                RFBoundNumberField {
                    Layout.preferredWidth: 200
                    label: "p_b/p₀"
                    value: Nozzle.backPressureRatio
                    digits: 8
                    decimals: 8
                    step: 0.005
                    onValueEdited: function (v) { Nozzle.backPressureRatio = v }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    RFSlider {
                        Layout.fillWidth: true
                        from: 0.001
                        to: 0.999
                        value: Nozzle.backPressureRatio
                        stepSize: 0.001
                        tickCount: 11
                        onMoved: Nozzle.backPressureRatio = value
                    }

                    Text {
                        text: "The field is authoritative — a slider cannot land on an "
                              + "exact threshold, and the presets below can."
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                RowLayout {
                    spacing: Metrics.spacing.xs

                    RFButton {
                        text: "Choking onset"
                        variant: "quiet"
                        compact: true
                        onClicked: Nozzle.applyPreset("choking")
                    }
                    RFButton {
                        text: "Shock at exit"
                        variant: "quiet"
                        compact: true
                        onClicked: Nozzle.applyPreset("shock_exit")
                    }
                    RFButton {
                        text: "Ideal expansion"
                        variant: "quiet"
                        compact: true
                        onClicked: Nozzle.applyPreset("ideal")
                    }
                }
            }
        }

        RFPanel {
            title: "Regime map"
            Layout.fillWidth: true
            contentSpacing: Metrics.spacing.s

            trailing: Component {
                RFStatusChip {
                    text: Nozzle.regimeLabel
                    tone: Nozzle.regimeTone
                }
            }

            RFBandScale {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.xs
                bands: page.bands
                from: 0
                to: 1
                value: page.current
            }

            // The three thresholds, printed as numbers as well as drawn.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.s
                spacing: Metrics.spacing.xl

                Repeater {
                    model: [
                        { label: "Choking onset   p_b/p₀", value: Nozzle.firstCritical,
                          hint: "throat reaches M = 1" },
                        { label: "Shock at exit   p_b/p₀", value: Nozzle.secondCritical,
                          hint: "the shock stands in the exit plane" },
                        { label: "Ideal expansion  p_b/p₀", value: Nozzle.thirdCritical,
                          hint: "p_e = p_b, no external adjustment" }
                    ]

                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 1

                        Text {
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            text: modelData.value.toFixed(8)
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutMedium
                            font.weight: Typography.medium
                        }
                        Text {
                            readonly property string plainText: modelData.hint
                            text: Notation.rich(plainText)
                            textFormat: Notation.textFormat(plainText)
                            color: Theme.textMuted
                            font.family: Typography.sans
                            font.pixelSize: Typography.meta
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.spacing.xs
                readonly property string plainText: "Every edge above is computed from A_e/A_t and γ — there is no "
                      + "hard-coded pressure anywhere in the classifier. Ideal expansion "
                      + "is a single point rather than a band, which is why the presets "
                      + "exist."
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
            title: "Shock station against back pressure"
            Layout.fillWidth: true
            Layout.fillHeight: true

            trailing: Component {
                Text {
                    text: "solved with the same shock solver the calculator uses"
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFLineChart {
                id: chart
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 200

                series: [{ points: Nozzle.shockPositionSeries(),
                           color: Theme.accent, width: 1.8 }]
                guides: Nozzle.hasShock
                        ? [{ value: Nozzle.backPressureRatio, axis: "x",
                             label: "current" }]
                        : []
                logScale: false
                xLabel: "back pressure  p_b/p₀"
                yLabel: "shock station  A_s/A_t"

                Connections {
                    target: Nozzle
                    function onInputsChanged() { chart.repaint() }
                }
            }

            Text {
                Layout.fillWidth: true
                text: "Inside the internal-shock interval only. Lower the back pressure "
                      + "and the shock moves downstream to a larger area, where it is "
                      + "stronger and costs more stagnation pressure — which is why the "
                      + "curve rises to the left."
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
