import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Normal shock calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and lays
 * out what comes back. There is no arithmetic in it - not a jump relation, not
 * a Rayleigh pitot formula, not an entropy expression.
 *
 * Five ways in, because an engineer rarely knows M1 directly: they know what a
 * probe read. Four of the five are closed form and one iterates, and the page
 * says which, since that is a real and useful distinction.
 */
Item {
    id: page

    readonly property var modes: NormalShock.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    // Two columns, so the whole shock is visible at once rather than its last
    // rows falling off the bottom of the panel.
    readonly property var columns: [
        ["Flow", "Static jump"],
        ["Stagnation", "Downstream state"]
    ]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < NormalShock.results.length; ++i)
            if (NormalShock.results[i].group === group)
                out.push(NormalShock.results[i])
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
                currentIndex: page.indexOfMode(NormalShock.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    NormalShock.mode = page.modes[currentIndex].key
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: NormalShock.inputSymbol
                value: NormalShock.inputValue
                digits: 6
                decimals: 6
                step: 0.01
                onValueEdited: function (v) { NormalShock.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: "Valid range: " + NormalShock.inputHint
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: NormalShock.modeIsIterative
                text: "This one has no closed-form inverse, so it is solved with RocketForge's "
                      + "own bracketed root finder. The other four are exact rearrangements."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: NormalShock.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { NormalShock.gamma = v }
            }

            RFDivider {}

            RFSectionLabel { text: "Upstream conditions" }

            Text {
                Layout.fillWidth: true
                text: "Optional. Supplying them turns every ratio into a downstream value "
                      + "in Pa and K; the ratios above do not need them."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Static pressure  p₁   [Pa]"
                value: NormalShock.upstreamPressure
                digits: 0
                decimals: 0
                step: 1000
                onValueEdited: function (v) { NormalShock.upstreamPressure = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Static temperature  T₁   [K]"
                value: NormalShock.upstreamTemperature
                digits: 2
                decimals: 2
                step: 5
                onValueEdited: function (v) { NormalShock.upstreamTemperature = v }
            }

            RFDivider {}

            RFSectionLabel { text: "Presets" }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                Repeater {
                    model: [1.5, 2.0, 3.0]

                    delegate: RFButton {
                        required property var modelData
                        Layout.fillWidth: true
                        text: "M₁ " + modelData
                        variant: "quiet"
                        compact: true
                        onClicked: {
                            modeControl.currentIndex = 0
                            NormalShock.setMachAndSolve(modelData)
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                text: NormalShock.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: NormalShock.assumptions.join(" · ")
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
                        text: NormalShock.statusLabel
                        tone: NormalShock.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: NormalShock.statusMessage !== ""
                    readonly property string plainText: NormalShock.statusMessage
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: NormalShock.valid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
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
                                    readonly property bool downstream: modelData === "Downstream state"

                                    Layout.fillWidth: true
                                    spacing: Metrics.spacing.xs
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: Notation.sectionRich(group.modelData); textFormat: Notation.textFormat(group.modelData) }

                                    Text {
                                        Layout.fillWidth: true
                                        visible: group.downstream && !NormalShock.dimensionalAvailable
                                        readonly property string plainText: NormalShock.dimensionalMessage
                                        text: Notation.rich(plainText)
                                        textFormat: Notation.textFormat(plainText)
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
                                                Layout.preferredWidth: 164
                                                text: Notation.rich(modelData.label)
                                                textFormat: Notation.textFormat(modelData.label)
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
                                                    onSingleTapped: NormalShock.copyText(modelData.value)
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
                    readonly property string plainText: NormalShock.strongShockLimits.caption !== undefined
                          ? NormalShock.strongShockLimits.caption : ""
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
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
                    visible: !NormalShock.valid
                    tag: "Input"
                    title: "No shock for this input"
                    body: NormalShock.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- reference check ------------------------------------------
            RFPanel {
                title: "Reference check"
                Layout.fillWidth: true
                Layout.preferredHeight: 246
                contentSpacing: Metrics.spacing.xs

                trailing: Component {
                    RFStatusChip {
                        text: check.rows.length > 0 ? "Published row available"
                                                    : "No exact reference row"
                        tone: check.rows.length > 0 ? "success" : "neutral"
                        showDot: false
                    }
                }

                Item {
                    id: check
                    // Reading NormalShock.results is what makes this re-evaluate
                    // when a new result arrives. Without that dependency the
                    // panel keeps the previous Mach number's comparison and
                    // quietly shows it next to a different result.
                    readonly property var rows: NormalShock.results.length >= 0
                                                ? NormalShock.comparisonForCurrentMach() : []
                    Layout.fillWidth: true
                    Layout.preferredHeight: 0
                }

                Text {
                    Layout.fillWidth: true
                    visible: check.rows.length === 0
                    text: "Anderson Appendix B tabulates γ = 1.4 at discrete Mach numbers. "
                          + "This M₁ is not one of them, and no value is interpolated."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: check.rows.length > 0
                    spacing: Metrics.spacing.m

                    Text {
                        Layout.preferredWidth: 70
                        text: "Quantity"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 120
                        text: "RocketForge"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.preferredWidth: 120
                        text: "Anderson"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Difference"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                    Item { Layout.preferredWidth: 52 }
                }

                Repeater {
                    model: check.rows

                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 22
                        spacing: Metrics.spacing.m

                        Text {
                            Layout.preferredWidth: 70
                            text: Notation.rich(modelData.label)
                            textFormat: Notation.textFormat(modelData.label)
                            color: Theme.textSecondary
                            font.family: Typography.sans
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 120
                            text: modelData.computed
                            color: Theme.text
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.preferredWidth: 120
                            text: modelData.reference
                            color: Theme.textSecondary
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.difference
                            color: Theme.textMuted
                            font.family: Typography.mono
                            font.pixelSize: Typography.bodySmall
                        }
                        RFStatusChip {
                            Layout.preferredWidth: 52
                            text: modelData.status
                            tone: modelData.status === "PASS" ? "success" : "warning"
                            showDot: false
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    text: NormalShock.referenceCitation + " — published reference, not an exact value."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
