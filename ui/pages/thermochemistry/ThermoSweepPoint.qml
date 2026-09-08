import QtQuick
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * One sweep point, inspected.
 *
 * Selected from the table. Shows the O/F that was solved, the state that came
 * back, and any warnings that point carried - the per-point detail the
 * aggregated warning summary above deliberately collapses.
 *
 * It carries no performance quantity. There is no c*, no Cf and no Isp on a
 * Phase 5D sweep point, because RocketForge owns none of them.
 */
ColumnLayout {
    id: inspector

    property int row: -1
    property var point: ({})

    function refresh() {
        point = row >= 0 ? Thermochemistry.sweepPoint(row) : ({})
    }

    onRowChanged: refresh()

    Connections {
        target: Thermochemistry
        function onSweepChanged() {
            // A new sweep invalidates the selection: point 12 of the old sweep
            // is not point 12 of the new one.
            inspector.row = -1
            inspector.refresh()
        }
    }

    spacing: Metrics.spacing.s
    visible: point.of !== undefined

    RFPanel {
        Layout.fillWidth: true
        title: "Selected point"
        contentSpacing: Metrics.spacing.s

        trailing: Component {
            RFStatusChip {
                text: inspector.point.status !== undefined ? inspector.point.status : ""
                tone: inspector.point.tone !== undefined ? inspector.point.tone : "neutral"
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: Metrics.spacing.xl

            RFResultValue {
                label: "O/F"
                value: inspector.point.of !== undefined
                       ? inspector.point.of.toFixed(4) : "—"
                scale: "small"
            }
            RFResultValue {
                label: "Chamber temperature  T₀"
                value: inspector.point.temperature !== undefined
                       && !isNaN(inspector.point.temperature)
                       ? inspector.point.temperature.toFixed(2) : "—"
                unit: "K"
                scale: "small"
            }
            RFResultValue {
                label: "Mean molar mass  M̄"
                value: inspector.point.molarMass !== undefined
                       && !isNaN(inspector.point.molarMass)
                       ? inspector.point.molarMass.toFixed(6) : "—"
                unit: "kg/mol"
                scale: "small"
            }
            RFResultValue {
                label: "Isentropic exponent  γ_s"
                value: inspector.point.gamma !== undefined
                       && !isNaN(inspector.point.gamma)
                       ? inspector.point.gamma.toFixed(5) : "—"
                scale: "small"
            }
            RFResultValue {
                label: "Density  ρ"
                value: inspector.point.density !== undefined
                       && !isNaN(inspector.point.density)
                       ? inspector.point.density.toFixed(4) : "—"
                unit: "kg/m³"
                scale: "small"
            }
        }

        Text {
            Layout.fillWidth: true
            // `text` is evaluated even while invisible, so the guard has to be
            // in the expression rather than only in `visible`.
            text: inspector.point.message !== undefined ? inspector.point.message : ""
            visible: text !== ""
            wrapMode: Text.WordWrap
            lineHeight: Typography.proseLineHeight
            lineHeightMode: Text.ProportionalHeight
            color: Theme.warning
            font.family: Typography.sans
            font.pixelSize: Typography.meta
        }

        Repeater {
            model: inspector.point.diagnostics !== undefined
                   ? inspector.point.diagnostics : []

            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: Metrics.spacing.s

                Text {
                    Layout.preferredWidth: 54
                    Layout.alignment: Qt.AlignTop
                    text: modelData.severity.toUpperCase()
                    color: modelData.severity === "error" ? Theme.error : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                    font.letterSpacing: 0.6
                }
                Text {
                    Layout.fillWidth: true
                    text: modelData.message
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
