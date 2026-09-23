import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Prandtl–Meyer calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it — no turning
 * function, no Mach angle, and no degree conversion: the service converts at
 * the boundary and this displays what it is given.
 *
 * Two workflows rather than three modes. "Solve from" answers what the state
 * *is*; the expansion turn answers what a corner *does*. Forcing both into one
 * form would make the reader guess which question was being answered.
 */
Item {
    id: page

    readonly property var modes: PrandtlMeyer.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    readonly property var columns: [["Flow"], ["Stagnation state"]]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < PrandtlMeyer.results.length; ++i)
            if (PrandtlMeyer.results[i].group === group)
                out.push(PrandtlMeyer.results[i])
        return out
    }

    function expansionRowsIn(group) {
        var out = []
        for (var i = 0; i < PrandtlMeyer.expansionResults.length; ++i)
            if (PrandtlMeyer.expansionResults[i].group === group)
                out.push(PrandtlMeyer.expansionResults[i])
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
                currentIndex: page.indexOfMode(PrandtlMeyer.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    PrandtlMeyer.mode = page.modes[currentIndex].key
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: PrandtlMeyer.inputSymbol
                       + (PrandtlMeyer.inputUnit ? "   [" + PrandtlMeyer.inputUnit + "]" : "")
                value: PrandtlMeyer.inputValue
                digits: 6
                decimals: 6
                step: 0.1
                onValueEdited: function (v) { PrandtlMeyer.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: "Valid range: " + PrandtlMeyer.inputHint
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            Text {
                Layout.fillWidth: true
                visible: PrandtlMeyer.modeIsIterative
                text: "The turning function has no closed-form inverse, so this one is "
                      + "solved with RocketForge's own bracketed root finder. Solving from "
                      + "Mach is an exact evaluation."
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
                value: PrandtlMeyer.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { PrandtlMeyer.gamma = v }
            }

            RFDivider {}

            RFSectionLabel { text: "Expansion turn" }

            RFToggle {
                text: "Solve a corner"
                checked: PrandtlMeyer.expansionEnabled
                onToggled: PrandtlMeyer.expansionEnabled = checked
            }

            Text {
                Layout.fillWidth: true
                text: "A separate question: what a convex corner does to a supersonic "
                      + "stream. It has its own upstream Mach number and its own turn."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                enabled: PrandtlMeyer.expansionEnabled
                label: "Upstream Mach  M₁"
                value: PrandtlMeyer.expansionMach
                digits: 6
                decimals: 6
                step: 0.1
                onValueEdited: function (v) { PrandtlMeyer.expansionMach = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                enabled: PrandtlMeyer.expansionEnabled
                label: "Turn  θ   [°]"
                value: PrandtlMeyer.expansionTurn
                digits: 4
                decimals: 4
                step: 1
                onValueEdited: function (v) { PrandtlMeyer.expansionTurn = v }
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
                        text: "M " + modelData
                        variant: "quiet"
                        compact: true
                        onClicked: {
                            modeControl.currentIndex = 0
                            PrandtlMeyer.setMachAndSolve(modelData)
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                text: PrandtlMeyer.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: PrandtlMeyer.assumptions.join(" · ")
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
                title: "State"
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentSpacing: Metrics.spacing.m

                trailing: Component {
                    RFStatusChip {
                        text: PrandtlMeyer.statusLabel
                        tone: PrandtlMeyer.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: PrandtlMeyer.statusMessage !== ""
                    readonly property string plainText: PrandtlMeyer.statusMessage
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: PrandtlMeyer.valid ? Theme.textMuted : Theme.warning
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

                                    Layout.fillWidth: true
                                    spacing: Metrics.spacing.xs
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: Notation.sectionRich(group.modelData); textFormat: Notation.textFormat(group.modelData) }

                                    Repeater {
                                        model: group.groupRows

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 26
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 186
                                                text: Notation.rich(modelData.label)
                                                textFormat: Notation.textFormat(modelData.label)
                                                elide: Text.ElideRight
                                                clip: true              // RichText does not elide
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
                                                    onSingleTapped: PrandtlMeyer.copyText(modelData.value)
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

                // ---- the expansion turn, when asked for ---------------------
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.m
                    spacing: Metrics.spacing.xs
                    visible: PrandtlMeyer.expansionEnabled

                    RFDivider {}

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.s

                        RFSectionLabel {
                            Layout.fillWidth: true
                            text: "Expansion turn"
                        }
                        RFStatusChip {
                            text: PrandtlMeyer.expansionStatus
                            tone: PrandtlMeyer.expansionValid ? "success" : "warning"
                            showDot: false
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: PrandtlMeyer.expansionMessage
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: PrandtlMeyer.expansionValid ? Theme.textMuted : Theme.warning
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xl
                        visible: PrandtlMeyer.expansionValid

                        Repeater {
                            model: [["Flow", "Turning"], ["Static ratios", "Stagnation"]]

                            delegate: ColumnLayout {
                                id: expansionColumn
                                required property var modelData

                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignTop
                                spacing: Metrics.spacing.m

                                Repeater {
                                    model: expansionColumn.modelData

                                    delegate: ColumnLayout {
                                        id: expansionGroup
                                        required property var modelData
                                        readonly property var groupRows: page.expansionRowsIn(modelData)

                                        Layout.fillWidth: true
                                        spacing: 2
                                        visible: groupRows.length > 0

                                        RFSectionLabel { text: Notation.sectionRich(expansionGroup.modelData); textFormat: Notation.textFormat(expansionGroup.modelData) }

                                        Repeater {
                                            model: expansionGroup.groupRows

                                            delegate: RowLayout {
                                                required property var modelData
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 24
                                                spacing: Metrics.spacing.m

                                                Text {
                                                    Layout.preferredWidth: 150
                                                    text: Notation.rich(modelData.label)
                                                    textFormat: Notation.textFormat(modelData.label)
                                                    elide: Text.ElideRight
                                                    clip: true              // RichText does not elide
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
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xl
                    visible: !PrandtlMeyer.valid
                    tag: "Input"
                    title: "No result for this input"
                    body: PrandtlMeyer.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- reference check ------------------------------------------
            RFPanel {
                title: "Reference check"
                Layout.fillWidth: true
                Layout.preferredHeight: 152
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
                    // Reading PrandtlMeyer.results is what makes this re-evaluate
                    // when a new result arrives. Without that dependency the
                    // panel keeps the previous Mach number's comparison and
                    // quietly shows it next to a different result.
                    readonly property var rows: PrandtlMeyer.results.length >= 0
                                                ? PrandtlMeyer.comparisonForCurrentMach() : []
                    Layout.fillWidth: true
                    Layout.preferredHeight: 0
                }

                Text {
                    Layout.fillWidth: true
                    visible: check.rows.length === 0
                    text: "Anderson Appendix C tabulates γ = 1.4 at discrete Mach numbers. "
                          + "This Mach number is not one of them, and no value is interpolated."
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
                    text: PrandtlMeyer.referenceCitation + " — published reference, not an exact value."
                    wrapMode: Text.WordWrap
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }
        }
    }
}
