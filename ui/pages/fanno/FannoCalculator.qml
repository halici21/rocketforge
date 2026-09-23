import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Fanno calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it — no Fanno relation,
 * no friction-factor conversion, no root logic.
 *
 * The friction convention is never left implicit. The control names it, the
 * field label carries the matching symbol, and the relation f_D = 4 f_F is
 * printed beside it. A bare "friction factor f" is banned by the interface
 * contract, and it is banned because the factor of four between the two
 * conventions is the single most expensive mistake this page could invite.
 */
Item {
    id: page

    readonly property var modes: Fanno.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].mode === key)
                return i
        return 0
    }

    readonly property var columns: [["Flow", "Starred state"], ["Choking limit"]]

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < Fanno.results.length; ++i)
            if (Fanno.results[i].group === group)
                out.push(Fanno.results[i])
        return out
    }

    function segmentRowsIn(group) {
        var out = []
        for (var i = 0; i < Fanno.segmentResults.length; ++i)
            if (Fanno.segmentResults[i].group === group)
                out.push(Fanno.segmentResults[i])
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
                currentIndex: page.indexOfMode(Fanno.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    Fanno.mode = page.modes[currentIndex].mode
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: Fanno.inputSymbol
                value: Fanno.inputValue
                digits: 6
                decimals: 6
                step: 0.05
                onValueEdited: function (v) { Fanno.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: "Valid range: " + Fanno.inputHint
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: Fanno.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { Fanno.gamma = v }
            }

            // Friction drives both branches towards sonic, so the parameter
            // falls to zero from both sides and the branch is a real question
            // rather than a preference.
            ColumnLayout {
                Layout.fillWidth: true
                visible: Fanno.modeNeedsBranch
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Branch" }

                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["Subsonic", "Supersonic"]
                    currentIndex: Fanno.branch === "subsonic" ? 0 : 1
                    onSelected: function (index) {
                        Fanno.branch = index === 0 ? "subsonic" : "supersonic"
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "The available duct length falls to zero from both sides of the "
                          + "sonic point, so a length alone does not say which duct is meant."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFDivider {}

            RFSectionLabel { text: "Duct segment" }

            RFToggle {
                text: "Solve a length of duct"
                checked: Fanno.segmentEnabled
                onToggled: Fanno.segmentEnabled = checked
            }

            Text {
                Layout.fillWidth: true
                text: "A separate question: what a real duct does to the flow entering it. "
                      + "It has its own inlet Mach number."
                wrapMode: Text.WordWrap
                lineHeight: Typography.proseLineHeight
                lineHeightMode: Text.ProportionalHeight
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                enabled: Fanno.segmentEnabled
                label: "Inlet Mach  M₁"
                value: Fanno.segmentMach
                digits: 6
                decimals: 6
                step: 0.05
                onValueEdited: function (v) { Fanno.segmentMach = v }
            }

            ColumnLayout {
                Layout.fillWidth: true
                enabled: Fanno.segmentEnabled
                spacing: 3
                RFSectionLabel { text: "Duct given as" }
                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["4 f_F L/D", "f, L, D_h"]
                    currentIndex: Fanno.ductSource === "parameter" ? 0 : 1
                    onSelected: function (index) {
                        Fanno.ductSource = index === 0 ? "parameter" : "geometry"
                    }
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "parameter"
                enabled: Fanno.segmentEnabled
                label: "Duct parameter  4 f_F L/D"
                value: Fanno.ductParameter
                digits: 6
                decimals: 6
                step: 0.1
                onValueEdited: function (v) { Fanno.ductParameter = v }
            }

            ColumnLayout {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "geometry"
                enabled: Fanno.segmentEnabled
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Friction convention" }

                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: Fanno.frictionConventions.map(function (c) { return c.label })
                    currentIndex: Fanno.frictionConvention === "fanning" ? 0 : 1
                    onSelected: function (index) {
                        Fanno.frictionConvention = index === 0 ? "fanning" : "darcy"
                    }
                }

                Text {
                    Layout.fillWidth: true
                    readonly property string plainText: Fanno.frictionRelation
                          + " — switching convention keeps the same physical duct, so the "
                          + "number in the field changes and the answer does not."
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

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "geometry"
                enabled: Fanno.segmentEnabled
                label: Fanno.frictionLabel
                value: Fanno.frictionFactor
                digits: 6
                decimals: 6
                step: 0.001
                onValueEdited: function (v) { Fanno.frictionFactor = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "geometry"
                enabled: Fanno.segmentEnabled
                label: "Length  L   [m]"
                value: Fanno.ductLength
                digits: 4
                decimals: 4
                step: 0.1
                onValueEdited: function (v) { Fanno.ductLength = v }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "geometry"
                enabled: Fanno.segmentEnabled
                label: "Hydraulic diameter  D_h   [m]"
                value: Fanno.hydraulicDiameter
                digits: 5
                decimals: 5
                step: 0.01
                onValueEdited: function (v) { Fanno.hydraulicDiameter = v }
            }

            Text {
                Layout.fillWidth: true
                visible: Fanno.ductSource === "geometry" && Fanno.segmentEnabled
                readonly property string plainText: "4 f_F L/D = " + Fanno.effectiveDuctParameter.toFixed(6)
                      + "   ·   the friction factor is supplied, not correlated: no "
                      + "Colebrook, no Moody chart, no Reynolds number."
                text: Notation.rich(plainText)
                textFormat: Notation.textFormat(plainText)
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
                text: Fanno.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                readonly property string plainText: Fanno.assumptions.join(" · ")
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
                        text: Fanno.statusLabel
                        tone: Fanno.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: Fanno.statusMessage !== ""
                    readonly property string plainText: Fanno.statusMessage
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Fanno.valid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.xl
                    visible: Fanno.valid

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
                                            Layout.preferredHeight: 25
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 210
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
                                                    onSingleTapped: Fanno.copyText(modelData.value)
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
                    visible: !Fanno.valid
                    tag: "Input"
                    title: "No result for this input"
                    body: Fanno.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- the duct segment ------------------------------------------
            RFPanel {
                title: "Duct segment"
                Layout.fillWidth: true
                Layout.preferredHeight: 232
                visible: Fanno.segmentEnabled
                contentSpacing: Metrics.spacing.s

                trailing: Component {
                    RFStatusChip {
                        text: Fanno.segmentStatus
                        tone: Fanno.segmentTone
                        showDot: false
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: Fanno.segmentMessage !== ""
                    readonly property string plainText: Fanno.segmentMessage
                    text: Notation.rich(plainText)
                    textFormat: Notation.textFormat(plainText)
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Fanno.segmentValid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.bodySmall
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.xl
                    // Shown for a choked duct too: the controller then publishes
                    // the requested and available lengths and no outlet Mach at
                    // all, which is the honest answer rather than a blank panel.
                    visible: Fanno.segmentResults.length > 0

                    Repeater {
                        model: [["Flow", "Change across the duct"], ["Choking limit"]]

                        delegate: ColumnLayout {
                            id: segmentColumn
                            required property var modelData

                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.spacing.m

                            Repeater {
                                model: segmentColumn.modelData

                                delegate: ColumnLayout {
                                    id: segmentGroup
                                    required property var modelData
                                    readonly property var groupRows: page.segmentRowsIn(modelData)

                                    Layout.fillWidth: true
                                    spacing: 2
                                    visible: groupRows.length > 0

                                    RFSectionLabel { text: Notation.sectionRich(segmentGroup.modelData); textFormat: Notation.textFormat(segmentGroup.modelData) }

                                    Repeater {
                                        model: segmentGroup.groupRows

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 23
                                            spacing: Metrics.spacing.m

                                            Text {
                                                Layout.preferredWidth: 205
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

                Item { Layout.fillHeight: true }
            }
        }
    }
}
