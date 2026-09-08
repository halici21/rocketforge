import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RocketForge 1.0
import "../../theme"
import "../../components"

/*
 * Oblique shock calculator.
 *
 * Every number shown here is computed by the verified backend and handed over
 * already formatted; this file selects a solve mode, sends the inputs, and
 * lays out what comes back. There is no arithmetic in it — no θ–β–M relation,
 * no wave-angle root, no shock ratio, and no degree conversion.
 *
 * Two things this page is careful about, because both are ways of being
 * quietly dishonest:
 *
 *   a deflection past the attachment limit clears the result rather than
 *   leaving the last wave angle on screen looking current;
 *
 *   the branch control appears only in the mode that has a branch to choose.
 *   Given a wave angle, which branch it is on is a fact, not a choice.
 */
Item {
    id: page

    readonly property var modes: ObliqueShock.solveModes

    function indexOfMode(key) {
        for (var i = 0; i < modes.length; ++i)
            if (modes[i].key === key)
                return i
        return 0
    }

    function rowsIn(group) {
        var out = []
        for (var i = 0; i < ObliqueShock.results.length; ++i)
            if (ObliqueShock.results[i].group === group)
                out.push(ObliqueShock.results[i])
        return out
    }

    // The groups come from the controller, because they differ between the
    // single-branch and both-branches results. A fixed list here would show
    // nothing at all when the other one arrived.
    readonly property var groups: ObliqueShock.resultGroups
    readonly property var leftGroups: groups.slice(0, Math.ceil(groups.length / 2))
    readonly property var rightGroups: groups.slice(Math.ceil(groups.length / 2))

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

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Upstream Mach  M₁"
                value: ObliqueShock.mach1
                digits: 6
                decimals: 6
                step: 0.1
                onValueEdited: function (v) { ObliqueShock.mach1 = v }
            }

            RFComboBox {
                id: modeControl
                Layout.fillWidth: true
                label: "Known quantity"
                model: page.modes.map(function (m) { return m.label + "   " + m.symbol })
                currentIndex: page.indexOfMode(ObliqueShock.mode)
                onCurrentIndexChanged: {
                    if (currentIndex < 0 || currentIndex >= page.modes.length)
                        return
                    ObliqueShock.mode = page.modes[currentIndex].key
                }
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: ObliqueShock.inputSymbol + "   [°]"
                value: ObliqueShock.inputValue
                digits: 6
                decimals: 6
                step: 1
                onValueEdited: function (v) { ObliqueShock.inputValue = v }
            }

            Text {
                Layout.fillWidth: true
                text: "Valid range: " + ObliqueShock.inputHint
                wrapMode: Text.WordWrap
                color: Theme.textMuted
                font.family: Typography.sans
                font.pixelSize: Typography.meta
            }

            RFBoundNumberField {
                Layout.fillWidth: true
                label: "Specific heat ratio  γ"
                value: ObliqueShock.gamma
                digits: 4
                decimals: 4
                step: 0.005
                onValueEdited: function (v) { ObliqueShock.gamma = v }
            }

            // Only the deflection mode has two roots. Given a wave angle, the
            // branch is a consequence rather than a choice, and offering a
            // control would imply otherwise.
            ColumnLayout {
                Layout.fillWidth: true
                visible: ObliqueShock.branchRequired
                spacing: Metrics.spacing.xs

                RFSectionLabel { text: "Branch" }

                RFSegmentedControl {
                    Layout.fillWidth: true
                    model: ["Weak", "Strong", "Both"]
                    currentIndex: ObliqueShock.branch === "weak" ? 0
                                : ObliqueShock.branch === "strong" ? 1 : 2
                    onSelected: function (index) {
                        ObliqueShock.branch = ["weak", "strong", "both"][index]
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Every attainable deflection has a weak and a strong wave angle. An "
                          + "unconstrained external flow takes the weak one."
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: Theme.textMuted
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }
            }

            RFDivider {}

            RFSectionLabel { text: "Limits at this Mach number" }

            Repeater {
                model: [
                    { k: "Mach angle  μ", v: "machAngle" },
                    { k: "Maximum deflection  θ_max", v: "thetaMax" },
                    { k: "β at θ_max", v: "betaAtThetaMax" },
                    { k: "β for sonic M₂", v: "betaSonic" }
                ]

                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: Metrics.spacing.s

                    Text {
                        Layout.fillWidth: true
                        text: modelData.k
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.bodySmall
                    }
                    Text {
                        text: ObliqueShock.limits[modelData.v] !== undefined
                              ? ObliqueShock.limits[modelData.v].toFixed(4) + "°" : "—"
                        color: Theme.text
                        font.family: Typography.mono
                        font.pixelSize: Typography.bodySmall
                    }
                }
            }

            RFDivider {}

            RFSectionLabel { text: "Presets" }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.spacing.xs

                Repeater {
                    model: [5, 10, 20]

                    delegate: RFButton {
                        required property var modelData
                        Layout.fillWidth: true
                        text: "θ " + modelData + "°"
                        variant: "quiet"
                        compact: true
                        onClicked: {
                            modeControl.currentIndex = 0
                            ObliqueShock.setDeflectionAndSolve(modelData)
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }

            RFSectionLabel { text: "Model" }

            Text {
                Layout.fillWidth: true
                text: ObliqueShock.modelName
                color: Theme.textSecondary
                font.family: Typography.sans
                font.pixelSize: Typography.bodySmall
            }

            Text {
                Layout.fillWidth: true
                text: ObliqueShock.assumptions.join(" · ")
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
                        text: ObliqueShock.statusLabel
                        tone: ObliqueShock.statusTone
                    }
                }

                Text {
                    Layout.fillWidth: true
                    // The detached block below states the same thing at length,
                    // so saying it twice here would just be noise.
                    visible: ObliqueShock.statusMessage !== "" && !ObliqueShock.detached
                    text: ObliqueShock.statusMessage
                    wrapMode: Text.WordWrap
                    lineHeight: Typography.proseLineHeight
                    lineHeightMode: Text.ProportionalHeight
                    color: ObliqueShock.valid ? Theme.textMuted : Theme.warning
                    font.family: Typography.sans
                    font.pixelSize: Typography.meta
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.s
                    spacing: Metrics.spacing.xl
                    visible: ObliqueShock.valid

                    Repeater {
                        model: [page.leftGroups, page.rightGroups]

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
                                                    onSingleTapped: ObliqueShock.copyText(modelData.value)
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

                // ---- the detached state --------------------------------------
                //
                // No wave angle, no ratios, and nothing left over from the last
                // valid answer: the request has no attached solution and the
                // page says only that.
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.l
                    spacing: Metrics.spacing.m
                    visible: ObliqueShock.detached

                    RFStatusChip {
                        text: "DETACHED SHOCK REQUIRED"
                        tone: "warning"
                        showDot: false
                    }

                    Text {
                        Layout.fillWidth: true
                        text: ObliqueShock.statusMessage
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textSecondary
                        font.family: Typography.sans
                        font.pixelSize: Typography.body
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.spacing.xl

                        ColumnLayout {
                            spacing: 2
                            RFSectionLabel { text: "Requested θ" }
                            Text {
                                text: ObliqueShock.inputValue.toFixed(4) + "°"
                                color: Theme.warning
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutMedium
                            }
                        }

                        ColumnLayout {
                            spacing: 2
                            RFSectionLabel { text: "Maximum attached θ_max" }
                            Text {
                                text: ObliqueShock.limits.thetaMax !== undefined
                                      ? ObliqueShock.limits.thetaMax.toFixed(4) + "°" : "—"
                                color: Theme.text
                                font.family: Typography.mono
                                font.pixelSize: Typography.readoutMedium
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "RocketForge does not solve the detached bow shock: its shape needs "
                              + "a numerical field solution, and substituting a normal shock or "
                              + "the θ_max solution here would be a different answer to a "
                              + "different question."
                        wrapMode: Text.WordWrap
                        lineHeight: Typography.proseLineHeight
                        lineHeightMode: Text.ProportionalHeight
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                RFEmptyState {
                    Layout.fillWidth: true
                    Layout.topMargin: Metrics.spacing.xl
                    visible: !ObliqueShock.valid && !ObliqueShock.detached
                    tag: "Input"
                    title: "No shock for this input"
                    body: ObliqueShock.statusMessage
                }

                Item { Layout.fillHeight: true }
            }

            // ---- the diagram, alongside the numbers -----------------------
            RFPanel {
                title: "θ–β–M"
                Layout.fillWidth: true
                Layout.preferredHeight: 236
                contentSpacing: Metrics.spacing.xs

                trailing: Component {
                    Text {
                        text: "the same solver that produced the numbers"
                        color: Theme.textMuted
                        font.family: Typography.sans
                        font.pixelSize: Typography.meta
                    }
                }

                ObliqueShockDiagram {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    compact: true
                }
            }
        }
    }
}
