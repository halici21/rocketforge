import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Mass flow calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it - not a ratio, not a
 * unit conversion, and certainly not a choking criterion.
 *
 * The layout separates two genuinely different things: the dimensionless
 * results, which need only gamma, and the dimensional ones in kg/s, which need
 * an area, a stagnation state and a gas constant. When those are absent the
 * dimensional rows are shown as unavailable rather than as zero.
 */
Item {
    id: page

    readonly property var modes: MassFlow.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    // Groups in the order an engineer reads them: what the flow is doing, the
    // dimensionless groups, the state it came from, then kilograms per second.
    // Two columns, because fourteen labelled values in one column run off the
    // bottom of the panel, and a result you have to scroll for is a result you
    // read wrong.
    readonly property var columns: [
        ["Flow", "Dimensionless", "Stagnation state"],
        ["Critical condition", "Dimensional"]
    ]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < MassFlow.results.length; ++i)
            if (MassFlow.results[i].group === group)
                out.push(MassFlow.results[i])
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
                currentIndex: page.indexOfMode(MassFlow.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    MassFlow.mode = page.modes[currentIndex].key
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: MassFlow.inputSymbol + (MassFlow.inputUnit ? "  [" + MassFlow.inputUnit + "]" : "")
                value: MassFlow.inputValue
                digits: 6
                decimals: 6
                step: 0.01
                onValueEdited: function (v) { MassFlow.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                text: "Valid range: " + MassFlow.inputHint
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: MassFlow.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { MassFlow.gamma = v }
            }

            // A given fraction of the choked flow is passed by one subsonic and
            // one supersonic state, so the branch must be asked for. The
            // backend refuses to guess, and so does the interface.
            ColumnLayout {
                Layout.fillWidth: true
                visible: MassFlow.branchRequired
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Branch" }

                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["Subsonic", "Supersonic", "Both"]
                    currentIndex: MassFlow.branch === "subsonic" ? 0
                                : MassFlow.branch === "supersonic" ? 1 : 2
                    onSelected: function (index) {
                        MassFlow.branch = ["subsonic", "supersonic", "both"][index]
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Any flow below the choked value is passed by one subsonic and one supersonic Mach number."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFDivider {}

            RFSectionLabel { text: "Stagnation state and geometry" }

            Text {
                Layout.fillWidth: true
                text: "Needed only for a flow in kg/s. The dimensionless results above do not use them."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Area  A   [m²]"
                value: MassFlow.area
                digits: 6
                decimals: 6
                step: 0.001
                onValueEdited: function (v) { MassFlow.area = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation pressure  p₀   [Pa]"
                value: MassFlow.stagnationPressure
                digits: 0
                decimals: 0
                step: 10000
                onValueEdited: function (v) { MassFlow.stagnationPressure = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Stagnation temperature  T₀   [K]"
                value: MassFlow.stagnationTemperature
                digits: 2
                decimals: 2
                step: 10
                onValueEdited: function (v) { MassFlow.stagnationTemperature = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Gas constant  R   [J/(kg·K)]"
                value: MassFlow.gasConstant
                digits: 4
                decimals: 4
                step: 1
                onValueEdited: function (v) { MassFlow.gasConstant = v }
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                text: MassFlow.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                text: MassFlow.assumptions.join(" · ")
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
                title: "Results"
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    RFStatusChip {
                        text: MassFlow.statusLabel
                        tone: MassFlow.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: MassFlow.statusMessage !== ""
                    text: MassFlow.statusMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: MassFlow.valid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                // Both roots, when the user asked for both.
                Repeater {
                    model: MassFlow.bothBranches

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: 176
                            text: modelData.label
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.body
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.value
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.readoutMedium
                            font.weight: Typography.medium
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
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
                                    readonly property bool dimensional: modelData === "Dimensional"

                                    Layout.fillWidth: true
                                    spacing: Metrics.spacing.xs
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: group.modelData }

                                    Text {
                                        Layout.fillWidth: true
                                        visible: group.dimensional && !MassFlow.dimensionalAvailable
                                        text: MassFlow.dimensionalMessage
                                        wrapMode: Text.WordWrap
                                        lineHeight: Typography.proseLineHeight
                                        lineHeightMode: Text.ProportionalHeight
                                        color: Theme.textMuted
                                        font.family: Typography.sans
                                        font.pixelSize: Typography.meta
                                    }

                                    Repeater {
                                        model: group.groupRows

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 26
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 176
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
                                                    onSingleTapped: MassFlow.copyText(modelData.value)
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

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xl
                    visible: !MassFlow.valid
                    tag: "Input"
                    title: "No result for this input"
                    body: MassFlow.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- choking check ---------------------------------------------
            RFPanel {
                id: choke
                title: "Choking check"
                Layout.fillWidth: true
                Layout.preferredHeight: 176
                contentSpacing: Metrics.spacing.s

                readonly property var check: MassFlow.chokingCheck

                trailing: Component {
                    RFStatusChip {
                        text: choke.check.label !== undefined ? choke.check.label : "—"
                        tone: choke.check.tone !== undefined ? choke.check.tone : "neutral"
                        showDot: false
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.l

                    RFBoundNumberField {
                        Layout.preferredWidth: 200
                        label: "Receiver pressure  p_back/p₀"
                        value: MassFlow.receiverPressureRatio
                        digits: 4
                        decimals: 4
                        step: 0.01
                        onValueEdited: function (v) { MassFlow.receiverPressureRatio = v }
                    }

                    Text {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        text: choke.check.message !== undefined ? choke.check.message : ""
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: choke.check.valid ? Theme.textSecondary : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    text: "This question is about a convergent passage discharging to a receiver. "
                          + "A converging–diverging nozzle can be choked at its throat with its exit "
                          + "pressure anywhere across a wide band, and deciding that needs the area "
                          + "ratio and a shock analysis the Nozzle module will provide."
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
}
