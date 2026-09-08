import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Rayleigh calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it — no Rayleigh
 * relation, no cp, no root logic.
 *
 * The Critical points group is not decoration. Rayleigh flow has two different
 * maxima at two different Mach numbers — the static temperature at M = 1/√γ
 * and the stagnation temperature at M = 1 — and between them the static
 * temperature *falls while heat is being added*. Showing them side by side,
 * labelled differently, is the one thing this page most has to get right.
 */
Item {
    id: page

    readonly property var modes: Rayleigh.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].mode === key)
                return i
        return 0
    }

    readonly property var columns: [["Flow", "Starred state"],
                                    ["Critical points", "Heat / choking"]]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < Rayleigh.results.length; ++i)
            if (Rayleigh.results[i].group === group)
                out.push(Rayleigh.results[i])
        return out
    }

    function heatRowsIn(group) {
        var out = []
        for (var i = 0; i < Rayleigh.heatResults.length; ++i)
            if (Rayleigh.heatResults[i].group === group)
                out.push(Rayleigh.heatResults[i])
        return out
    }

    RowLayout {
        anchors.fill: parent
        spacing: Metrics.spacing.l

        // ---- input rail ---------------------------------------------------
        RFPanel {
            title: "Solve from"
            Layout.preferredWidth: Metrics.railWidth - 20
            Layout.minimumWidth: 250
            Layout.fillHeight: true
            contentSpacing: Metrics.spacing.m

            RFComboBox {
                id: modeControl
                Layout.fillWidth: true
                label: "Known quantity"
                model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                currentIndex: page.indexOfMode(Rayleigh.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    Rayleigh.mode = page.modes[currentIndex].mode
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: Rayleigh.inputSymbol
                value: Rayleigh.inputValue
                digits: 6
                decimals: 6
                step: 0.05
                onValueEdited: function (v) { Rayleigh.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                text: "Valid range: " + Rayleigh.inputHint
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: Rayleigh.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { Rayleigh.gamma = v }
            }

            // T0/T0* rises to 1 from both sides, so every attainable value has
            // two roots and the branch is a real question.
            ColumnLayout {
                Layout.fillWidth: true
                visible: Rayleigh.modeNeedsBranch
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Branch" }

                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["Subsonic", "Supersonic"]
                    currentIndex: Rayleigh.branch === "subsonic" ? 0 : 1
                    onSelected: function (index) {
                        Rayleigh.branch = index === 0 ? "subsonic" : "supersonic"
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "T₀/T₀* rises to 1 from both sides of the sonic point, so a value "
                          + "alone does not say which duct is meant."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFDivider {}

            RFSectionLabel { text: "Heat transition" }

            RFToggle {
                text: "Add or remove heat"
                checked: Rayleigh.heatEnabled
                onToggled: Rayleigh.heatEnabled = checked
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                enabled: Rayleigh.heatEnabled
                label: "Inlet Mach  M₁"
                value: Rayleigh.heatMach
                digits: 6
                decimals: 6
                step: 0.05
                onValueEdited: function (v) { Rayleigh.heatMach = v }
            }

            ColumnLayout {
                Layout.fillWidth: true
                enabled: Rayleigh.heatEnabled
                spacing: 3
                RFSectionLabel { text: "Heat given as" }
                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["T₀₂/T₀₁", "q  [J/kg]"]
                    currentIndex: Rayleigh.heatInput === "ratio" ? 0 : 1
                    onSelected: function (index) {
                        Rayleigh.heatInput = index === 0 ? "ratio" : "heat"
                    }
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Rayleigh.heatInput === "ratio"
                enabled: Rayleigh.heatEnabled
                label: "Stagnation temperature ratio  T₀₂/T₀₁"
                value: Rayleigh.temperatureRatio
                digits: 6
                decimals: 6
                step: 0.05
                onValueEdited: function (v) { Rayleigh.temperatureRatio = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Rayleigh.heatInput === "heat"
                enabled: Rayleigh.heatEnabled
                label: "Heat per unit mass  q   [J/kg]"
                value: Rayleigh.heat
                digits: 1
                decimals: 1
                step: 10000
                onValueEdited: function (v) { Rayleigh.heat = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Rayleigh.heatInput === "heat"
                enabled: Rayleigh.heatEnabled
                label: "Gas constant  R   [J/(kg·K)]"
                value: Rayleigh.gasConstant
                digits: 4
                decimals: 4
                step: 1
                onValueEdited: function (v) { Rayleigh.gasConstant = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Rayleigh.heatInput === "heat"
                enabled: Rayleigh.heatEnabled
                label: "Inlet stagnation temperature  T₀₁   [K]"
                value: Rayleigh.inletStagnationTemperature
                digits: 2
                decimals: 2
                step: 10
                onValueEdited: function (v) { Rayleigh.inletStagnationTemperature = v }
            }

            Text {
                Layout.fillWidth: true
                visible: Rayleigh.heatInput === "heat" && Rayleigh.heatEnabled
                text: "q = cp (T₀₂ − T₀₁), with cp taken from the gas model. Imposed heat "
                      + "transfer only: no combustion, no chemistry, no species."
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
                text: Rayleigh.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                text: Rayleigh.assumptions.join(" · ")
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
                title: "State"
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    RFStatusChip {
                        text: Rayleigh.statusLabel
                        tone: Rayleigh.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: Rayleigh.statusMessage !== ""
                    text: Rayleigh.statusMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Rayleigh.valid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.xl
                    visible: Rayleigh.valid

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
                                            Layout.preferredHeight: 25
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 226
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
                                                    onSingleTapped: Rayleigh.copyText(modelData.value)
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    visible: Rayleigh.valid
                    text: "Two different maxima at two different Mach numbers: the static "
                          + "temperature peaks at M = 1/√γ = "
                          + Rayleigh.staticTemperatureMaxMach.toFixed(6)
                          + " and the stagnation temperature at M = 1. Between them the static "
                          + "temperature falls while heat is still being added — the flow is "
                          + "accelerating fast enough that the kinetic-energy rise outruns it."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xl
                    visible: !Rayleigh.valid
                    tag: "Input"
                    title: "No result for this input"
                    body: Rayleigh.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- the heat transition ---------------------------------------
            RFPanel {
                title: "Heat transition"
                Layout.fillWidth: true
                Layout.preferredHeight: 232
                visible: Rayleigh.heatEnabled
                contentSpacing: Metrics.spacing.s

                trailing: Component {
                    RFStatusChip {
                        text: Rayleigh.heatStatus
                        tone: Rayleigh.heatTone
                        showDot: false
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: Rayleigh.heatMessage !== ""
                    text: Rayleigh.heatMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Rayleigh.heatValid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.xl
                    // Shown for a choked duct too: the controller then publishes
                    // the requested and maximum heat and no outlet Mach at all,
                    // which is the honest answer rather than a blank panel.
                    visible: Rayleigh.heatResults.length > 0

                    Repeater {
                        model: [["Flow", "Change across the duct"], ["Heat / choking"]]

                        delegate: ColumnLayout {
                            id: heatColumn
                            required property var modelData

                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.spacing.m

                            Repeater {
                                model: heatColumn.modelData

                                delegate: ColumnLayout {
                                    id: heatGroup
                                    required property var modelData
                                    readonly property var groupRows: page.heatRowsIn(modelData)

                                    Layout.fillWidth: true
                                    spacing: 2
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: heatGroup.modelData }

                                    Repeater {
                                        model: heatGroup.groupRows

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 23
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 214
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
                                                font.pixelSize: modelData.emphasis
                                                    ? Typography.readoutSmall
                                                    : Typography.bodySmall
                                            }
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
