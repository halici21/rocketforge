import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Nozzle calculator.
 *
 * Every number here is computed by the verified backend and handed over
 * already formatted; this file collects inputs, sends them, and lays out what
 * comes back. There is no arithmetic in it — no area-Mach relation, no
 * threshold, no shock search, not even a pressure ratio: the two input modes
 * are converted by the controller, one layer down, where they are tested
 * without Qt.
 *
 * The regime is the headline, because on this page the regime *is* the answer.
 * The shock block exists only while a shock does, so moving the back pressure
 * out of that interval removes it rather than leaving it stranded on screen.
 */
Item {
    id: page

    readonly property var columns: [["Regime", "Flow"], ["Exit state", "Thresholds"]]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < Nozzle.results.length; ++i)
            if (Nozzle.results[i].group === group)
                out.push(Nozzle.results[i])
        return out
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input rail ---------------------------------------------------
        RFPanel {
            title: "Operating point"
            Layout.preferredWidth: Metrics.railWidth - 10
            Layout.minimumWidth: 260
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m

            RFSectionLabel { text: "Gas" }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: Nozzle.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { Nozzle.gamma = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Gas constant  R   [J/(kg K)]"
                value: Nozzle.gasConstant
                digits: 5
                decimals: 2
                step: 1.0
                onValueEdited: function (v) { Nozzle.gasConstant = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Reservoir" }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation pressure  p₀   [Pa]"
                value: Nozzle.stagnationPressure
                digits: 9
                decimals: 0
                step: 50000
                onValueEdited: function (v) { Nozzle.stagnationPressure = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation temperature  T₀   [K]"
                value: Nozzle.stagnationTemperature
                digits: 6
                decimals: 1
                step: 25
                onValueEdited: function (v) { Nozzle.stagnationTemperature = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Nozzle given as" }

            RFSegmentedControl {
                Layout.fillWidth: true
                model: ["A_t and A_e/A_t", "A_t and A_e"]
                currentIndex: Nozzle.areaMode === "ratio" ? 0 : 1
                onSelected: function (index) {
                    Nozzle.areaMode = index === 0 ? "ratio" : "areas"
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Throat area  A_t   [m²]"
                value: Nozzle.throatArea
                digits: 8
                decimals: 5
                step: 0.001
                onValueEdited: function (v) { Nozzle.throatArea = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.areaMode === "ratio"
                label: "Area ratio  A_e/A_t"
                value: Nozzle.areaRatio
                digits: 6
                decimals: 4
                step: 0.1
                onValueEdited: function (v) { Nozzle.areaRatio = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.areaMode === "areas"
                label: "Exit area  A_e   [m²]"
                value: Nozzle.exitArea
                digits: 8
                decimals: 5
                step: 0.001
                onValueEdited: function (v) { Nozzle.exitArea = v }
            }

            RFDivider {}
            RFSectionLabel { text: "Back pressure given as" }

            RFSegmentedControl {
                Layout.fillWidth: true
                model: ["p_b/p₀", "p_b   [Pa]"]
                currentIndex: Nozzle.pressureMode === "ratio" ? 0 : 1
                onSelected: function (index) {
                    Nozzle.pressureMode = index === 0 ? "ratio" : "absolute"
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.pressureMode === "ratio"
                label: "Back pressure  p_b/p₀"
                value: Nozzle.backPressureRatio
                digits: 6
                decimals: 6
                step: 0.01
                onValueEdited: function (v) { Nozzle.backPressureRatio = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Nozzle.pressureMode === "absolute"
                label: "Back pressure  p_b   [Pa]"
                value: Nozzle.backPressure
                digits: 9
                decimals: 0
                step: 10000
                onValueEdited: function (v) { Nozzle.backPressure = v }
            }

            Text {
                Layout.fillWidth: true
                text: "Switching how the pressure is stated does not move it: the "
                      + "controller converts once, and the nozzle sees the same "
                      + "operating point either way."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                text: "Steady · Quasi-one-dimensional · Inviscid · Adiabatic · "
                      + "Isentropic except across an infinitely thin normal shock · "
                      + "Calorically perfect gas: constant γ, constant R. No thrust, "
                      + "no performance coefficients, no plume."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }
        }

        // ---- results ------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.spacing.l

            RFPanel {
                title: "Flow regime"
                Layout.fillWidth: true
                contentSpacing: Metrics.spacing.s

                trailing: Component {
                    RFStatusChip {
                        text: Nozzle.regimeLabel
                        tone: Nozzle.regimeTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Nozzle.regimeNote
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Nozzle.valid ? Theme.textSecondary : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                // Only where a jet actually needs adjusting outside the exit.
                Text {
                    Layout.fillWidth: true
                    visible: Nozzle.externalContext !== ""
                    text: Nozzle.externalContext
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                Text {
                    Layout.fillWidth: true
                    visible: !Nozzle.valid
                    text: Nozzle.statusMessage
                    wrapMode: Text.WordWrap
                    color: Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }
            }

            RFPanel {
                title: "Solution"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Nozzle.valid

                RowLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    spacing: Metrics.spacing.xl

                    Repeater {
                        model: page.columns

                        delegate: ColumnLayout {
                            id: column
                            required property var modelData

                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.spacing.m

                            Repeater {
                                model: column.modelData

                                delegate: ColumnLayout {
                                    id: group
                                    required property var modelData
                                    readonly property var groupRows: page.rowsIn(modelData)

                                    Layout.fillWidth: true
                                    spacing: Metrics.spacing.xs
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: group.modelData }

                                    Repeater {
                                        model: group.groupRows

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 24
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 190
                                                text: modelData.label
                                                elide: Text.ElideRight
                                                color: Theme.textSecondary
                                                font.family: Typography.sans
                                                font.pixelSize: Typography.body
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: modelData.value
                                                      + (modelData.unit ? " " + modelData.unit : "")
                                                color: modelData.available ? Theme.text
                                                                           : Theme.textMuted
                                                font.family: Typography.mono
                                                font.pixelSize: modelData.emphasis
                                                    ? Typography.readoutMedium
                                                    : Typography.readoutSmall
                                                font.weight: modelData.emphasis
                                                    ? Typography.medium : Typography.regular

                                                TapHandler {
                                                    onSingleTapped: Nozzle.copyText(modelData.value)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // The shock card exists only while a shock does.
            RFPanel {
                title: "Internal normal shock"
                Layout.fillWidth: true
                visible: Nozzle.hasShock

                trailing: Component {
                    RFStatusChip {
                        text: "Solved"
                        tone: "warning"
                        showDot: false
                    }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 4
                    columnSpacing: Metrics.spacing.xl
                    rowSpacing: Metrics.spacing.xs

                    Repeater {
                        model: page.rowsIn("Shock")

                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: Metrics.spacing.s

                            Text {
                                Layout.preferredWidth: 160
                                text: modelData.label
                                elide: Text.ElideRight
                                color: Theme.textSecondary
                                font.family: Typography.sans
                                font.pixelSize: Typography.bodySmall
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.value
                                      + (modelData.unit ? " " + modelData.unit : "")
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutSmall
                                font.weight: modelData.emphasis ? Typography.medium
                                                                : Typography.regular
                            }
                        }
                    }
                }
            }
        }
    }
}
